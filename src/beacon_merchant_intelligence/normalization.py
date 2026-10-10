"""Map extracted Shopify Storefront API records into the domain Product model."""

from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime
from decimal import Decimal, InvalidOperation
from html.parser import HTMLParser
from urllib.parse import urlsplit

from .models import Product, ProductVariant, VariantAvailability

VARIANT_PAGE_SIZE = 50
IMAGE_PAGE_SIZE = 20


class _TextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.has_text = False

    def handle_data(self, data: str) -> None:
        if data.strip():
            self.has_text = True


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


def _connection_complete(value: object) -> bool:
    connection = _mapping(value)
    page = _mapping(connection.get("pageInfo")) if connection else None
    return page is not None and page.get("hasNextPage") is False


def _decimal_money(value: object) -> Decimal | None:
    money = _mapping(value)
    amount = money.get("amount") if money else None
    if not isinstance(amount, (str, int, float)) or isinstance(amount, bool):
        return None
    try:
        parsed = Decimal(str(amount))
    except (InvalidOperation, ValueError):
        return None
    return parsed if parsed.is_finite() and parsed >= 0 else None


def _description_present(value: object) -> bool | None:
    if not isinstance(value, str):
        return None
    parser = _TextExtractor()
    try:
        parser.feed(value)
        parser.close()
    except Exception:
        return None
    return parser.has_text


def normalize_shopify_product(
    raw: Mapping[str, object], host: str, source_url: str, position: int | None,
    observed_at: datetime, warnings: list[str],
) -> tuple[Product, tuple[str, ...]]:
    """Normalize one Shopify product record; absent or malformed data stays unknown."""
    title = raw.get("title") if isinstance(raw.get("title"), str) else None
    raw_product_url = raw.get("onlineStoreUrl")
    product_url = None
    if isinstance(raw_product_url, str):
        try:
            parsed_product_url = urlsplit(raw_product_url)
            if (
                parsed_product_url.scheme == "https"
                and parsed_product_url.hostname == host
                and parsed_product_url.username is None
                and parsed_product_url.password is None
                and parsed_product_url.port in (None, 443)
            ):
                product_url = raw_product_url
        except ValueError:
            pass
    if product_url is None:
        warnings.append(f"{title or 'A product'} has no verified public product-page URL in the source response.")
    variants_connection = raw.get("variants")
    raw_variants = _nodes(variants_connection)
    product_options = raw.get("options")
    size_option = None
    if isinstance(product_options, list):
        for option in product_options:
            option_map = _mapping(option)
            name = option_map.get("name") if option_map else None
            if isinstance(name, str) and name.strip().casefold() == "size":
                size_option = name.strip()
                break

    variants: list[ProductVariant] = []
    prices: list[Decimal] = []
    original_prices: list[Decimal | None] = []
    currencies: set[str] = set()
    for raw_variant in raw_variants:
        variant = _mapping(raw_variant)
        if variant is None:
            warnings.append(f"{title or 'A product'} contained a malformed variant record; it was skipped.")
            continue
        options = variant.get("selectedOptions")
        option_values: dict[str, str] = {}
        if isinstance(options, list):
            for option in options:
                option_map = _mapping(option)
                if option_map and isinstance(option_map.get("name"), str) and isinstance(option_map.get("value"), str):
                    option_values[str(option_map["name"]).casefold()] = str(option_map["value"])
        # Preserve full labels; the existing analyzer recognizes numeric
        # prefixes and collapses repeated sizes across options such as color.
        name = variant.get("title")
        if not isinstance(name, str) and option_values:
            name = " / ".join(option_values.values())
        if not isinstance(name, str):
            name = None
        availability_value = variant.get("availableForSale")
        if availability_value is True:
            availability = VariantAvailability.AVAILABLE
        elif availability_value is False:
            availability = VariantAvailability.UNAVAILABLE
        else:
            availability = VariantAvailability.UNKNOWN
        variants.append(ProductVariant(name=name, availability=availability))

        money = variant.get("price")
        price = _decimal_money(money)
        if price is not None:
            prices.append(price)
        money_map = _mapping(money)
        currency = money_map.get("currencyCode") if money_map else None
        if isinstance(currency, str):
            currencies.add(currency)
        original_value = variant.get("compareAtPrice")
        original = _decimal_money(original_value) if original_value is not None else None
        original_prices.append(original)
        original_map = _mapping(original_value)
        original_currency = original_map.get("currencyCode") if original_map else None
        if isinstance(original_currency, str):
            currencies.add(original_currency)

    price_range = _mapping(raw.get("priceRange"))
    range_min = _decimal_money(price_range.get("minVariantPrice")) if price_range else None
    range_money = _mapping(price_range.get("minVariantPrice")) if price_range else None
    range_currency = range_money.get("currencyCode") if range_money else None
    if isinstance(range_currency, str):
        currencies.add(range_currency)
    variants_complete = _connection_complete(variants_connection)
    current_price = range_min
    if current_price is None and variants_complete and len(prices) == len(raw_variants) == len(variants):
        current_price = min(prices) if prices else None
    original_price = None
    if len(currencies) <= 1 and variants and variants_complete and len(variants) == len(raw_variants) and all(value is not None and value > 0 for value in original_prices):
        observed_originals = {value for value in original_prices if value is not None}
        if len(observed_originals) == 1:
            original_price = next(iter(observed_originals))
    if not variants_complete:
        if _has_next(variants_connection):
            warnings.append(f"{title or 'A product'} has more variants than the {VARIANT_PAGE_SIZE} collected; variant data and original price are incomplete.")
        else:
            warnings.append(f"{title or 'A product'} did not include complete variant pagination metadata; variant coverage and original price remain uncertain.")

    image_connection = raw.get("images")
    image_nodes = _nodes(image_connection)
    image_count = len(image_nodes) if _connection_complete(image_connection) else None
    if not _connection_complete(image_connection):
        if _has_next(image_connection):
            warnings.append(f"{title or 'A product'} has more than {IMAGE_PAGE_SIZE} images; exact image count is unknown.")
        else:
            warnings.append(f"{title or 'A product'} has no complete image connection; image count remains unknown.")
    if not isinstance(raw.get("descriptionHtml"), str):
        warnings.append(f"{title or 'A product'} has no observable description field.")
    if not variants:
        warnings.append(f"{title or 'A product'} had no usable variant records.")
    if len(currencies) > 1:
        warnings.append(f"{title or 'A product'} exposed mixed currency codes; monetary values are retained without a single currency label.")
    currency_codes = tuple(sorted(currencies))

    product = Product(
        product_id=raw.get("id") if isinstance(raw.get("id"), str) else None,
        title=title,
        url=product_url,
        collection_position=position,
        size_option=size_option,
        current_price=current_price,
        original_price=original_price,
        variants=tuple(variants),
        description_present=_description_present(raw.get("descriptionHtml")),
        image_count=image_count,
        review_count=None,
        observation_timestamp=observed_at,
        source=source_url,
        sales_rank=None,
        sales_rank_source=None,
        inventory_age_days=None,
        inventory_history_source=None,
    )
    return product, currency_codes
