"""Normalize Sporting Feet UCP catalog records into Beacon's existing model."""

from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime
from decimal import Decimal, InvalidOperation
from html.parser import HTMLParser
from urllib.parse import urlsplit

from .models import Product, ProductVariant, VariantAvailability

STORE_HOST = "www.sporting-feet.com"


class _TextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.has_text = False

    def handle_data(self, data: str) -> None:
        if data.strip():
            self.has_text = True


def _mapping(value: object) -> Mapping[str, object] | None:
    return value if isinstance(value, Mapping) else None


def _amount(value: object) -> tuple[Decimal, str] | None:
    money = _mapping(value)
    amount = money.get("amount") if money else None
    currency = money.get("currency") if money else None
    if isinstance(amount, bool) or not isinstance(amount, int) or amount < 0 or not isinstance(currency, str):
        return None
    if currency != "GBP":
        return None
    # UCP represents prices in minor currency units; the request fixes GBP.
    return Decimal(amount) / Decimal(100), currency


def normalize_product(
    raw: Mapping[str, object], source_url: str, observed_at: datetime, warnings: list[str]
) -> tuple[Product, tuple[str, ...]]:
    title = raw.get("title") if isinstance(raw.get("title"), str) else None
    raw_url = raw.get("url")
    product_url = None
    if isinstance(raw_url, str):
        try:
            parsed = urlsplit(raw_url)
            if (parsed.scheme == "https" and parsed.hostname == STORE_HOST
                    and parsed.username is None and parsed.password is None
                    and parsed.port in (None, 443) and not parsed.query and not parsed.fragment):
                product_url = raw_url
        except ValueError:
            pass
    if product_url is None:
        warnings.append(f"{title or 'A product'} has no verified Sporting Feet product URL.")

    options = raw.get("options")
    size_option = None
    if isinstance(options, list):
        for option in options:
            item = _mapping(option)
            name = item.get("name") if item else None
            if isinstance(name, str) and name.strip().casefold() == "size":
                size_option = name.strip()
                break

    raw_variants = raw.get("variants")
    variants: list[ProductVariant] = []
    prices: list[Decimal] = []
    original_prices: list[Decimal] = []
    currencies: set[str] = set()
    if isinstance(raw_variants, list):
        for item in raw_variants:
            variant = _mapping(item)
            if variant is None:
                warnings.append(f"{title or 'A product'} contains a malformed variant; it was skipped.")
                continue
            variant_options = variant.get("options")
            labels: dict[str, str] = {}
            if isinstance(variant_options, list):
                for option in variant_options:
                    option_map = _mapping(option)
                    if option_map and isinstance(option_map.get("name"), str) and isinstance(option_map.get("label"), str):
                        labels[str(option_map["name"]).casefold()] = str(option_map["label"])
            name = labels.get("size") if size_option else variant.get("title")
            if not isinstance(name, str):
                name = None
            availability_map = _mapping(variant.get("availability"))
            available = availability_map.get("available") if availability_map else None
            availability = (VariantAvailability.AVAILABLE if available is True else
                            VariantAvailability.UNAVAILABLE if available is False else
                            VariantAvailability.UNKNOWN)
            variants.append(ProductVariant(name=name, availability=availability))

            price = _amount(variant.get("price"))
            if price:
                prices.append(price[0]); currencies.add(price[1])
            list_price = _amount(variant.get("list_price"))
            if list_price and list_price[0] > 0:
                original_prices.append(list_price[0]); currencies.add(list_price[1])

    # The model supports one product price, not a range. Keep it unknown if the
    # source exposes materially different variant prices.
    price_range = _mapping(raw.get("price_range"))
    price_min = _amount(price_range.get("min")) if price_range else None
    price_max = _amount(price_range.get("max")) if price_range else None
    current_price = None
    if price_min and price_max and price_min[0] == price_max[0]:
        current_price = price_min[0]
        currencies.update((price_min[1], price_max[1]))
    elif prices and len(prices) == len(variants) and len(set(prices)) == 1:
        current_price = prices[0]
    elif price_min or price_max:
        warnings.append(f"{title or 'A product'} has a price range; single current_price remains unknown.")

    list_range = _mapping(raw.get("list_price_range"))
    list_min = _amount(list_range.get("min")) if list_range else None
    list_max = _amount(list_range.get("max")) if list_range else None
    original_price = None
    if (list_min and list_max and list_min[0] > 0 and list_min[0] == list_max[0]
            and current_price is not None and list_min[0] >= current_price):
        original_price = list_min[0]
        currencies.update((list_min[1], list_max[1]))
    elif original_prices and len(original_prices) == len(variants) and len(set(original_prices)) == 1:
        candidate = original_prices[0]
        if current_price is not None and candidate >= current_price:
            original_price = candidate

    description = _mapping(raw.get("description"))
    description_html = description.get("html") if description else None
    description_present: bool | None = None
    if isinstance(description_html, str):
        parser = _TextExtractor()
        try:
            parser.feed(description_html); parser.close()
            description_present = parser.has_text
        except Exception:
            description_present = None
    else:
        warnings.append(f"{title or 'A product'} has no observable description field.")

    # Catalog search media is a card/variant preview, not a complete gallery;
    # review counts and inventory history are not in the returned schema.
    if isinstance(raw.get("media"), list):
        warnings.append(f"{title or 'A product'} media are previews; exact product image count remains unknown.")
    else:
        warnings.append(f"{title or 'A product'} has no observable media list; image count remains unknown.")
    if not variants:
        warnings.append(f"{title or 'A product'} has no usable variant records.")

    product = Product(
        product_id=raw.get("id") if isinstance(raw.get("id"), str) else None,
        title=title,
        url=product_url,
        collection_position=None,
        size_option=size_option,
        current_price=current_price,
        original_price=original_price,
        variants=tuple(variants),
        description_present=description_present,
        image_count=None,
        review_count=None,
        observation_timestamp=observed_at,
        source=source_url,
        sales_rank=None,
        sales_rank_source=None,
        inventory_age_days=None,
        inventory_history_source=None,
    )
    return product, tuple(sorted(currencies))
