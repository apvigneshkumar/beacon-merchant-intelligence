import json
import copy
from pathlib import Path
from urllib.error import HTTPError

import pytest

from beacon_merchant_intelligence import collector
from beacon_merchant_intelligence.collector import CollectionError, collect_storefront, validate_storefront_url
from beacon_merchant_intelligence.models import VariantAvailability as A
from beacon_merchant_intelligence.reporting import render_collected_markdown
from beacon_merchant_intelligence.cli import serialize_dataset


FIXTURE = json.loads((Path(__file__).parent / "data/mock_shop_collection.json").read_text(encoding="utf-8"))


def fake_fetcher(response=FIXTURE, captured=None):
    def fetch(url, payload):
        if captured is not None:
            captured["url"] = url
            captured["payload"] = json.loads(payload)
        return response
    return fetch


def test_normalizes_shopify_storefront_data_without_inventing_unknown_values():
    captured = {}
    dataset = collect_storefront(
        "https://mock.shop/collections/test-boots", max_products=2,
        fetcher=fake_fetcher(captured=captured),
    )

    assert captured["url"] == "https://mock.shop/api"
    assert captured["payload"]["variables"] == {
        "productLimit": 2,
        "collectionQuery": "handle:test-boots",
    }
    first, second = dataset["products"]
    assert first.collection_position == 1
    assert first.url is None  # source explicitly provides no public product page URL
    assert first.current_price == 50
    assert first.original_price == 100
    assert first.description_present is True
    assert first.image_count == 1
    assert first.review_count is None
    assert first.sales_rank is None
    assert first.inventory_age_days is None
    assert [v.availability for v in first.variants] == [
        A.AVAILABLE, A.UNAVAILABLE, A.UNAVAILABLE, A.UNAVAILABLE,
        A.UNAVAILABLE, A.UNAVAILABLE, A.AVAILABLE,
    ]
    assert first.size_option == "Size"

    assert second.collection_position == 2
    assert second.description_present is None
    assert second.image_count == 0
    assert second.review_count is None
    assert second.current_price is None  # invalid range and negative variant price
    assert second.original_price is None
    assert second.variants[0].availability is A.UNKNOWN
    assert "fictional demo data" in " ".join(dataset["warnings"])


def test_store_root_has_no_fabricated_collection_position():
    response = {
        "data": {
            "products": {
                "nodes": [FIXTURE["data"]["collections"]["nodes"][0]["products"]["nodes"][0]],
                "pageInfo": {"hasNextPage": False},
            }
        }
    }
    product = collect_storefront("https://mock.shop", fetcher=fake_fetcher(response))["products"][0]
    assert product.collection_position is None


def test_missing_image_or_variant_pagination_is_unknown_not_zero_or_complete():
    response = copy.deepcopy(FIXTURE)
    raw_product = response["data"]["collections"]["nodes"][0]["products"]["nodes"][0]
    raw_product.pop("images")
    raw_product["variants"].pop("pageInfo")
    product = collect_storefront("https://mock.shop/collections/test-boots", fetcher=fake_fetcher(response))["products"][0]
    assert product.image_count is None
    assert product.current_price == 50  # reported price range is independent of variant pagination
    assert product.original_price is None


@pytest.mark.parametrize("url", [
    "http://mock.shop",
    "https://example.com/collections/test-boots",
    "https://127.0.0.1/collections/test-boots",
    "https://mock.shop:444",
    "https://mock.shop/collections/a?sort=price",
    "https://user:pass@mock.shop",
    "https://mock.shop/products/one",
    "https://mock.shop.evil.example",
])
def test_rejects_unsafe_or_unsupported_urls(url):
    with pytest.raises(CollectionError):
        validate_storefront_url(url)


@pytest.mark.parametrize("limit", [0, -1, 11, True, 1.5])
def test_enforces_explicit_product_limit(limit):
    with pytest.raises(CollectionError, match="max_products"):
        collect_storefront("https://mock.shop", max_products=limit, fetcher=fake_fetcher())


def test_handles_graphql_errors_and_malformed_shapes():
    with pytest.raises(CollectionError, match="GraphQL errors"):
        collect_storefront("https://mock.shop", fetcher=fake_fetcher({"errors": [{"message": "bad query"}]}))
    with pytest.raises(CollectionError, match="No public products"):
        collect_storefront("https://mock.shop", fetcher=fake_fetcher({"data": {"products": {"nodes": []}}}))


@pytest.mark.parametrize(("status", "message"), [(302, "Redirect refused"), (503, "HTTP 503")])
def test_http_failures_and_redirects_are_reported_without_following_them(monkeypatch, status, message):
    class FakeOpener:
        def open(self, request, timeout):
            raise HTTPError(request.full_url, status, "blocked", {}, None)

    monkeypatch.setattr(collector, "build_opener", lambda handler: FakeOpener())
    with pytest.raises(CollectionError, match=message):
        collector._fetch_graphql("https://mock.shop/api", b"{}")


def test_malformed_http_json_is_rejected_without_network(monkeypatch):
    class FakeResponse:
        status = 200
        headers = {"Content-Type": "application/json"}

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return None

        def read(self, limit):
            return b"not-json"

    class FakeOpener:
        def open(self, request, timeout):
            return FakeResponse()

    monkeypatch.setattr(collector, "build_opener", lambda handler: FakeOpener())
    with pytest.raises(CollectionError, match="malformed JSON"):
        collector._fetch_graphql("https://mock.shop/api", b"{}")


def test_reports_incomplete_bounded_collection_and_unknown_analyzer_evidence():
    dataset = collect_storefront("https://mock.shop/collections/test-boots", max_products=2, fetcher=fake_fetcher())
    report = render_collected_markdown(dataset)
    assert "fictional demo data" in report
    assert "Sales rank" in report
    assert "collection position" in report.lower()
    assert "not a probability" in report
    assert "Demo Trail Boot — broken_size_run" in report
    assert "missing data is not interpreted as zero reviews" in report
    assert "0 reviews" not in report
    encoded = json.loads(serialize_dataset(dataset))
    assert encoded["products"][0]["review_count"] is None
    assert encoded["products"][1]["variants"][0]["availability"] == "unknown"
