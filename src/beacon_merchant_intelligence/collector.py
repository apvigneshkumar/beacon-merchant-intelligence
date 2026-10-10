"""Bounded Shopify Storefront API collection for Shopify's public mock.shop."""

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
from .normalization import normalize_shopify_product

MAX_PRODUCTS = 10
DEFAULT_PRODUCTS = 5
REQUEST_TIMEOUT_SECONDS = 15
MAX_RESPONSE_BYTES = 2_000_000
MIN_REQUEST_INTERVAL_SECONDS = 1.0
_request_lock = threading.Lock()
_last_request_started: float | None = None

_COLLECTION_QUERY = """query BeaconCollection($productLimit: Int!, $collectionQuery: String!) {
  collections(first: 1, query: $collectionQuery) {
    nodes {
      id title handle
      products(first: $productLimit) {
        nodes {
          id title handle onlineStoreUrl descriptionHtml availableForSale options { name }
          featuredImage { url }
          images(first: 20) { nodes { url } pageInfo { hasNextPage } }
          priceRange { minVariantPrice { amount currencyCode } }
          variants(first: 50) {
            nodes {
              id title availableForSale
              price { amount currencyCode }
              compareAtPrice { amount currencyCode }
              selectedOptions { name value }
            }
            pageInfo { hasNextPage }
          }
        }
        pageInfo { hasNextPage }
      }
    }
  }
}"""

_ROOT_QUERY = """query BeaconProducts($productLimit: Int!) {
  shop { name }
  products(first: $productLimit) {
    nodes {
      id title handle onlineStoreUrl descriptionHtml availableForSale options { name }
      featuredImage { url }
      images(first: 20) { nodes { url } pageInfo { hasNextPage } }
      priceRange { minVariantPrice { amount currencyCode } }
      variants(first: 50) {
        nodes {
          id title availableForSale
          price { amount currencyCode }
          compareAtPrice { amount currencyCode }
          selectedOptions { name value }
        }
        pageInfo { hasNextPage }
      }
      pageInfo { hasNextPage }
    }
    pageInfo { hasNextPage }
  }
}"""


class CollectionError(ValueError):
    """A safe collection failure with a user-readable message."""


class _NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def _validate_host(host: str) -> None:
    if host != "mock.shop" and not host.endswith(".mock.shop"):
        raise CollectionError("Only mock.shop storefront hosts are supported.")
    labels = host.split(".")
    if any(not re.fullmatch(r"[a-z0-9](?:[a-z0-9-]*[a-z0-9])?", label) for label in labels):
        raise CollectionError("Invalid mock.shop host name.")
    # The strict provider-host allowlist is the SSRF boundary: arbitrary hosts,
    # IP literals, local names, and user-supplied API destinations are rejected.


def validate_storefront_url(url: str) -> tuple[str, str | None, str]:
    """Return (host, collection_handle, canonical input URL)."""
    try:
        parsed = urlsplit(url)
        host = (parsed.hostname or "").lower().rstrip(".")
        port = parsed.port
    except ValueError as exc:
        raise CollectionError(f"Invalid storefront URL: {exc}") from exc
    if parsed.scheme != "https" or not host or parsed.username or parsed.password:
        raise CollectionError("Use an https:// mock.shop storefront URL without credentials.")
    if port not in (None, 443) or parsed.query or parsed.fragment:
        raise CollectionError("Ports, query strings, and fragments are not supported in storefront URLs.")
    _validate_host(host)
    path = parsed.path.rstrip("/")
    if path in ("", "/"):
        handle = None
    else:
        match = re.fullmatch(r"/collections/([a-zA-Z0-9][a-zA-Z0-9_-]*)", path)
        if not match:
            raise CollectionError("Use a storefront root URL or a single /collections/{handle} URL.")
        handle = match.group(1)
    return host, handle, f"https://{host}{path or '/'}"


def _fetch_graphql(url: str, payload: bytes) -> Mapping[str, object]:
    request = Request(
        url,
        data=payload,
        method="POST",
        headers={"Content-Type": "application/json", "Accept": "application/json", "User-Agent": "Beacon-Merchant-Intelligence/0.2 (mock.shop demo collector)"},
    )
    opener = build_opener(_NoRedirect())
    try:
        with opener.open(request, timeout=REQUEST_TIMEOUT_SECONDS) as response:
            if response.status != 200:
                raise CollectionError(f"Storefront returned HTTP {response.status}.")
            content_type = response.headers.get("Content-Type", "")
            if "json" not in content_type.lower():
                raise CollectionError("Storefront returned a non-JSON response.")
            body = response.read(MAX_RESPONSE_BYTES + 1)
    except HTTPError as exc:
        if 300 <= exc.code < 400:
            raise CollectionError(f"Redirect refused (HTTP {exc.code}); redirects are not followed.") from exc
        raise CollectionError(f"Storefront request failed with HTTP {exc.code}.") from exc
    except (URLError, TimeoutError, OSError) as exc:
        raise CollectionError(f"Storefront request failed: {exc}") from exc
    if len(body) > MAX_RESPONSE_BYTES:
        raise CollectionError("Storefront response exceeded the 2 MB safety limit.")
    try:
        value = json.loads(body)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise CollectionError("Storefront returned malformed JSON.") from exc
    if not isinstance(value, dict):
        raise CollectionError("Storefront JSON must be an object.")
    return value


def _wait_for_request_slot() -> None:
    """Enforce a one-request-per-second minimum interval in this process."""
    global _last_request_started
    with _request_lock:
        now = time.monotonic()
        if _last_request_started is not None:
            delay = MIN_REQUEST_INTERVAL_SECONDS - (now - _last_request_started)
            if delay > 0:
                time.sleep(delay)
        _last_request_started = time.monotonic()


def _mapping(value: object) -> Mapping[str, object] | None:
    return value if isinstance(value, Mapping) else None


def _nodes(value: object) -> list[object]:
    connection = _mapping(value)
    nodes = connection.get("nodes") if connection else None
    return nodes if isinstance(nodes, list) else []


def _has_next(value: object) -> bool:
    connection = _mapping(value)
    page = _mapping(connection.get("pageInfo")) if connection else None
    return page is not None and page.get("hasNextPage") is True


def collect_storefront(
    url: str,
    *,
    max_products: int = DEFAULT_PRODUCTS,
    fetcher: Callable[[str, bytes], Mapping[str, object]] | None = None,
) -> dict[str, object]:
    """Collect one bounded page from a mock.shop root or collection URL.

    ``fetcher`` is injectable for fixture-based tests. Production requests use
    HTTPS, an allowlisted host, a fixed endpoint, a timeout, response cap, and
    a redirect-blocking opener.
    """
    if isinstance(max_products, bool) or not isinstance(max_products, int) or not 1 <= max_products <= MAX_PRODUCTS:
        raise CollectionError(f"max_products must be between 1 and {MAX_PRODUCTS}.")
    host, collection_handle, canonical_url = validate_storefront_url(url)
    api_url = f"https://{host}/api"
    variables: dict[str, object] = {"productLimit": max_products}
    if collection_handle:
        variables["collectionQuery"] = f"handle:{collection_handle}"
    query = _COLLECTION_QUERY if collection_handle else _ROOT_QUERY
    payload = json.dumps({"query": query, "variables": variables}).encode("utf-8")
    request_fetcher = fetcher or _fetch_graphql
    if fetcher is None:
        _wait_for_request_slot()
    try:
        response = request_fetcher(api_url, payload)
    except CollectionError:
        raise
    except Exception as exc:
        raise CollectionError(f"Storefront request failed: {exc}") from exc
    data = _mapping(response.get("data"))
    if data is None:
        errors = response.get("errors")
        if isinstance(errors, list):
            raise CollectionError("Storefront GraphQL errors: " + "; ".join(str(item) for item in errors[:3]))
        raise CollectionError("Storefront response did not contain GraphQL data.")
    warnings = [
        "mock.shop records are fictional demo data, not observations from a real merchant.",
        "Sales rank, inventory history, and review count are not exposed by this collector; those analyzer inputs remain unknown.",
        "Variant availability means available for sale, not units on hand or guaranteed fulfillment.",
        "One page is collected per run; collection/API ordering is only a visibility proxy and is not demand rank.",
    ]
    graph_errors = response.get("errors")
    if isinstance(graph_errors, list) and graph_errors:
        warnings.append(f"Storefront returned {len(graph_errors)} GraphQL error(s); some fields may be missing.")

    collection_title = None
    position_enabled = collection_handle is not None
    if collection_handle:
        connection = _nodes(data.get("collections"))
        if not connection:
            raise CollectionError(f"Collection '{collection_handle}' was not found or is not public.")
        collection = _mapping(connection[0])
        if collection is None:
            raise CollectionError("Storefront returned a malformed collection record.")
        collection_title = collection.get("title") if isinstance(collection.get("title"), str) else None
        product_connection = collection.get("products")
    else:
        product_connection = data.get("products")
    raw_products = _nodes(product_connection)
    if not raw_products:
        raise CollectionError("No public products were returned for this URL.")
    if len(raw_products) > max_products:
        warnings.append(f"The API returned more than the requested maximum of {max_products}; excess records were discarded.")
    raw_products = raw_products[:max_products]
    if _has_next(product_connection):
        warnings.append(f"The source has more products than this bounded sample (maximum {max_products}); later products were not fetched.")
    elif len(raw_products) < max_products:
        warnings.append(f"The source returned {len(raw_products)} product(s), fewer than the requested maximum {max_products}; full collection completeness is not established.")

    observed_at = datetime.now(timezone.utc)
    products: list[Product] = []
    currencies_by_product: list[tuple[str, ...]] = []
    for index, item in enumerate(raw_products, start=1):
        raw = _mapping(item)
        if raw is None:
            warnings.append(f"Malformed product record at sample position {index} was skipped.")
            continue
        product, currencies = normalize_shopify_product(
            raw, host, api_url, index if position_enabled else None, observed_at, warnings
        )
        if product.product_id is None or product.title is None:
            warnings.append(f"Product record at sample position {index} lacked an ID or title and was skipped.")
            continue
        products.append(product)
        currencies_by_product.append(currencies)
    if not products:
        raise CollectionError("No valid product records remained after normalization.")
    return {
        "schema_version": "1.0",
        "store_name": "mock.shop",
        "fictional_demo_data": True,
        "requested_url": canonical_url,
        "collection_title": collection_title,
        "source_endpoint": api_url,
        "observed_at": observed_at.isoformat(),
        "max_products": max_products,
        "returned_products": len(products),
        "products": products,
        "currency_codes_by_product": currencies_by_product,
        "warnings": list(dict.fromkeys(warnings)),
    }
