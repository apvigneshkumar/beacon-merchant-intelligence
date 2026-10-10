import json
from copy import deepcopy
from pathlib import Path
from urllib.error import HTTPError

import pytest

import beacon_merchant_intelligence.sporting_feet as collector
from beacon_merchant_intelligence.analyzers import analyze_broken_size_run
from beacon_merchant_intelligence.models import VariantAvailability as A
from beacon_merchant_intelligence.reporting import render_collected_markdown
from beacon_merchant_intelligence.sporting_feet import (
    AGENT_PROFILE, MCP_ENDPOINT, SportingFeetError, collect_storefront, validate_store_url,
)


FIXTURE = json.loads((Path(__file__).parent / "data/sporting_feet_search.json").read_text(encoding="utf-8"))


def fake_fetcher(catalog=FIXTURE, captured=None):
    calls = []
    def fetch(request):
        calls.append(request)
        if captured is not None:
            captured.append(request)
        if request.get("method") == "tools/call":
            return {"result": {"content": [{"type": "text", "text": json.dumps(catalog)}]}}
        return {"result": {}}
    return fetch, calls


def test_collects_and_normalizes_public_ucp_catalog_without_inventing_unknowns():
    captured = []
    fetch, calls = fake_fetcher(captured=captured)
    dataset = collect_storefront("https://www.sporting-feet.com/", query="trainers", max_products=5, fetcher=fetch)
    first, third = dataset["products"][0], dataset["products"][2]

    assert len(calls) == 3
    assert captured[-1]["params"]["name"] == "search_catalog"
    assert captured[-1]["params"]["arguments"]["meta"]["ucp-agent"]["profile"] == AGENT_PROFILE
    assert dataset["source_endpoint"] == MCP_ENDPOINT
    assert dataset["fictional_demo_data"] is False
    assert first.product_id == "gid://shopify/Product/15212963234171"
    assert first.url == "https://www.sporting-feet.com/products/w-divide-6-gtx-120448"
    assert first.current_price == 120
    assert first.original_price is None
    assert first.collection_position is None
    assert first.sales_rank is None and first.inventory_age_days is None
    assert first.review_count is None and first.image_count is None
    assert first.description_present is True and first.size_option == "Size"
    assert first.variants[0].name == "4.5"
    assert first.variants[0].availability is A.UNAVAILABLE
    assert first.variants[2].availability is A.AVAILABLE
    assert third.current_price == 115 and third.original_price == 135
    assert dataset["currency_codes_by_product"][2] == ("GBP",)
    assert "More matching products exist" in " ".join(dataset["warnings"])


def test_existing_analyzers_run_on_real_store_records_with_supported_size_option():
    fetch, _ = fake_fetcher()
    dataset = collect_storefront("https://www.sporting-feet.com", fetcher=fetch)
    findings = [finding for product in dataset["products"] for finding in analyze_broken_size_run(product)]
    # The real Size option and source variant availability are used; this test
    # deliberately does not prescribe that a pattern must be flagged.
    assert all("Size" in " ".join(item.evidence) or item.signal == "broken_size_run" for item in findings)
    report = render_collected_markdown(dataset)
    assert "Real, public Sporting Feet catalog data" in report
    assert "not a probability" in report
    assert "Sales rank" in report
    assert "collection position" in report.lower()


def test_missing_and_invalid_values_stay_unknown():
    catalog = deepcopy(FIXTURE)
    first = catalog["products"][0]
    first["variants"][0]["availability"].pop("available")
    first["variants"][1]["price"]["amount"] = -1
    first["price_range"]["min"]["amount"] = -5
    first["price_range"]["max"]["amount"] = -5
    fetch, _ = fake_fetcher(catalog)
    product = collect_storefront("https://www.sporting-feet.com", fetcher=fetch)["products"][0]
    assert product.variants[0].availability is A.UNKNOWN
    assert product.variants[1].availability is A.UNAVAILABLE
    assert product.current_price is None


@pytest.mark.parametrize("url", [
    "http://www.sporting-feet.com/", "https://sporting-feet.com/", "https://www.sporting-feet.com.evil.test/",
    "https://127.0.0.1/", "https://user:pass@www.sporting-feet.com/", "https://www.sporting-feet.com:444/",
    "https://www.sporting-feet.com/products/a", "https://www.sporting-feet.com/?q=shoes",
])
def test_unsafe_or_unsupported_store_urls_are_rejected(url):
    with pytest.raises(SportingFeetError):
        validate_store_url(url)


@pytest.mark.parametrize("limit", [0, -1, 11, True, 1.5])
def test_enforces_bounded_product_limit(limit):
    fetch, _ = fake_fetcher()
    with pytest.raises(SportingFeetError, match="max_products"):
        collect_storefront("https://www.sporting-feet.com", max_products=limit, fetcher=fetch)


def test_rejects_empty_query_and_malformed_tool_result():
    fetch, _ = fake_fetcher()
    with pytest.raises(SportingFeetError, match="query"):
        collect_storefront("https://www.sporting-feet.com", query=" ", fetcher=fetch)
    def malformed(request):
        if request.get("method") == "tools/call":
            return {"result": {"content": [{"type": "text", "text": "not-json"}]}}
        return {"result": {}}
    with pytest.raises(SportingFeetError, match="catalog JSON"):
        collect_storefront("https://www.sporting-feet.com", fetcher=malformed)


@pytest.mark.parametrize("status, message", [(302, "Redirect refused"), (503, "HTTP 503")])
def test_http_errors_and_redirects_are_rejected(monkeypatch, status, message):
    class FakeOpener:
        def open(self, request, timeout):
            assert request.full_url == MCP_ENDPOINT
            assert request.get_method() == "POST"
            raise HTTPError(request.full_url, status, "blocked", {}, None)
    monkeypatch.setattr(collector, "_pace", lambda: None)
    monkeypatch.setattr(collector, "build_opener", lambda handler: FakeOpener())
    with pytest.raises(SportingFeetError, match=message):
        collector._post({"jsonrpc": "2.0"})


def test_response_size_and_content_type_limits_are_enforced(monkeypatch):
    class FakeResponse:
        status = 200

        def __init__(self, content_type, body):
            self.headers = {"Content-Type": content_type}
            self.body = body

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return None

        def read(self, limit):
            return self.body[:limit]

    class FakeOpener:
        response = None

        def open(self, request, timeout):
            return self.response

    opener = FakeOpener()
    monkeypatch.setattr(collector, "_pace", lambda: None)
    monkeypatch.setattr(collector, "build_opener", lambda handler: opener)
    opener.response = FakeResponse("text/html", b"{}")
    with pytest.raises(SportingFeetError, match="non-JSON"):
        collector._post({"jsonrpc": "2.0"})
    opener.response = FakeResponse("application/json", b"x" * (collector.MAX_RESPONSE_BYTES + 1))
    with pytest.raises(SportingFeetError, match="2 MB"):
        collector._post({"jsonrpc": "2.0"})
