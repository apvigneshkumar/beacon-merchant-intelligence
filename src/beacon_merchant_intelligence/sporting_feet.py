"""Bounded read-only Sporting Feet UCP catalog adapter."""

from __future__ import annotations

import json
import re
import threading
import time
from collections.abc import Callable, Mapping
from datetime import datetime, timezone
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener

from .models import Product
from .sporting_feet_normalization import STORE_HOST, normalize_product

MAX_PRODUCTS = 10
DEFAULT_PRODUCTS = 5
REQUEST_TIMEOUT_SECONDS = 15
MAX_RESPONSE_BYTES = 2_000_000
MIN_REQUEST_INTERVAL_SECONDS = 1.0
MCP_ENDPOINT = "https://sporting-feet.myshopify.com/api/ucp/mcp"
AGENT_PROFILE = "https://shopify.dev/ucp/agent-profiles/2026-08-25/valid-with-capabilities.json"
_lock = threading.Lock()
_last_request: float | None = None


class SportingFeetError(ValueError):
    """A safe read-only catalog collection failure."""


class _NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def validate_store_url(url: str) -> str:
    try:
        parsed = urlsplit(url)
        host = (parsed.hostname or "").lower().rstrip(".")
        port = parsed.port
    except ValueError as exc:
        raise SportingFeetError(f"Invalid store URL: {exc}") from exc
    if (parsed.scheme != "https" or host != STORE_HOST or parsed.username or parsed.password
            or port not in (None, 443) or parsed.query or parsed.fragment
            or parsed.path not in ("", "/")):
        raise SportingFeetError("Use the HTTPS Sporting Feet storefront root (https://www.sporting-feet.com/).")
    if not all(re.fullmatch(r"[a-z0-9-]+", label) for label in host.split(".")):
        raise SportingFeetError("Invalid retailer host.")
    return "https://www.sporting-feet.com/"


def _pace() -> None:
    global _last_request
    with _lock:
        now = time.monotonic()
        if _last_request is not None:
            delay = MIN_REQUEST_INTERVAL_SECONDS - (now - _last_request)
            if delay > 0:
                time.sleep(delay)
        _last_request = time.monotonic()


def _post(payload: Mapping[str, object]) -> Mapping[str, object]:
    request = Request(MCP_ENDPOINT, data=json.dumps(payload).encode(), method="POST", headers={
        "Content-Type": "application/json", "Accept": "application/json, text/event-stream",
        "User-Agent": "Beacon-Merchant-Intelligence/0.3 (read-only catalog validation)",
    })
    _pace()
    try:
        with build_opener(_NoRedirect()).open(request, timeout=REQUEST_TIMEOUT_SECONDS) as response:
            if response.status != 200:
                raise SportingFeetError(f"UCP catalog endpoint returned HTTP {response.status}.")
            if "json" not in response.headers.get("Content-Type", "").lower():
                raise SportingFeetError("UCP catalog endpoint returned a non-JSON response.")
            body = response.read(MAX_RESPONSE_BYTES + 1)
    except HTTPError as exc:
        if 300 <= exc.code < 400:
            raise SportingFeetError(f"Redirect refused (HTTP {exc.code}); redirects are not followed.") from exc
        raise SportingFeetError(f"UCP catalog request failed with HTTP {exc.code}.") from exc
    except (URLError, TimeoutError, OSError) as exc:
        raise SportingFeetError(f"UCP catalog request failed: {exc}") from exc
    if len(body) > MAX_RESPONSE_BYTES:
        raise SportingFeetError("UCP response exceeded the 2 MB safety limit.")
    try:
        result = json.loads(body)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise SportingFeetError("UCP catalog endpoint returned malformed JSON.") from exc
    if not isinstance(result, dict):
        raise SportingFeetError("UCP response must be a JSON object.")
    return result


def _unwrap_tool_result(response: Mapping[str, object]) -> Mapping[str, object]:
    result = response.get("result")
    if not isinstance(result, Mapping):
        raise SportingFeetError("UCP response did not contain a tool result.")
    content = result.get("content")
    if isinstance(content, list):
        for item in content:
            block = item if isinstance(item, Mapping) else None
            text = block.get("text") if block else None
            if isinstance(text, str):
                try:
                    value = json.loads(text)
                except json.JSONDecodeError:
                    continue
                if isinstance(value, Mapping):
                    return value
    structured = result.get("structuredContent")
    if isinstance(structured, Mapping):
        return structured
    raise SportingFeetError("UCP tool response did not contain catalog JSON.")


def collect_storefront(
    url: str,
    *,
    query: str = "trainers",
    max_products: int = DEFAULT_PRODUCTS,
    fetcher: Callable[[Mapping[str, object]], Mapping[str, object]] | None = None,
) -> dict[str, object]:
    """Collect one bounded UCP search page; never calls cart or checkout tools."""
    if isinstance(max_products, bool) or not isinstance(max_products, int) or not 1 <= max_products <= MAX_PRODUCTS:
        raise SportingFeetError(f"max_products must be between 1 and {MAX_PRODUCTS}.")
    if not isinstance(query, str) or not query.strip() or len(query) > 120:
        raise SportingFeetError("query must be a non-empty string of at most 120 characters.")
    requested_url = validate_store_url(url)
    now = datetime.now(timezone.utc)
    client = fetcher or _post
    init = client({"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {
        "protocolVersion": "2025-03-26", "capabilities": {},
        "clientInfo": {"name": "beacon-merchant-intelligence", "version": "0.3"},
    }})
    if init.get("error"):
        raise SportingFeetError("UCP protocol initialization failed.")
    client({"jsonrpc": "2.0", "method": "notifications/initialized", "params": {}})
    response = client({"jsonrpc": "2.0", "id": 2, "method": "tools/call", "params": {
        "name": "search_catalog", "arguments": {
            "meta": {"ucp-agent": {"profile": AGENT_PROFILE}},
            "catalog": {"query": query.strip(), "context": {"address_country": "GB", "currency": "GBP", "language": "en-GB"},
                        "pagination": {"limit": max_products}},
        },
    }})
    catalog = _unwrap_tool_result(response)
    raw_products = catalog.get("products")
    if not isinstance(raw_products, list) or not raw_products:
        raise SportingFeetError("No public catalog products were returned for this search.")
    warnings = [
        "Real, public Sporting Feet catalog data; read-only UCP search. No cart or checkout operation was used.",
        "Search result order is not sales rank or collection position; those values remain unknown.",
        "UCP catalog search defaults to sale-ready products and may omit wholly unavailable products.",
        "Review count, inventory history/age, and exact product image count are not exposed by this search response.",
        "Variant availability is the source's sale-ready boolean, not units on hand or guaranteed fulfillment.",
        "The search response does not expose variant pagination completeness; counts and size runs cover returned variants only.",
        "A single observed discount is a review prompt and does not establish overstock.",
    ]
    page = _mapping(catalog.get("pagination"))
    if page and page.get("has_next_page") is True:
        warnings.append(f"More matching products exist; only the first bounded page of {max_products} was collected.")
    elif len(raw_products) < max_products:
        warnings.append(f"Only {len(raw_products)} products were returned for this query; broader catalog completeness is not established.")
    products: list[Product] = []
    currencies: list[tuple[str, ...]] = []
    for index, raw in enumerate(raw_products[:max_products], start=1):
        if not isinstance(raw, Mapping):
            warnings.append(f"Malformed catalog product at result position {index} was skipped.")
            continue
        product, currency_codes = normalize_product(raw, MCP_ENDPOINT, now, warnings)
        if not product.product_id or not product.title:
            warnings.append(f"Catalog record at result position {index} lacked an ID or title and was skipped.")
            continue
        products.append(product)
        currencies.append(currency_codes)
    if not products:
        raise SportingFeetError("No valid catalog products remained after normalization.")
    if len(raw_products) > max_products:
        warnings.append(f"The API exceeded the requested maximum; excess records were discarded.")
    return {
        "schema_version": "1.0",
        "store_name": "Sporting Feet",
        "fictional_demo_data": False,
        "requested_url": requested_url,
        "query": query.strip(),
        "source_endpoint": MCP_ENDPOINT,
        "source_method": "UCP MCP read-only search_catalog",
        "observed_at": now.isoformat(),
        "max_products": max_products,
        "returned_products": len(products),
        "products": products,
        "currency_codes_by_product": currencies,
        "warnings": list(dict.fromkeys(warnings)),
    }


def _mapping(value: object) -> Mapping[str, object] | None:
    return value if isinstance(value, Mapping) else None
