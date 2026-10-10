from decimal import Decimal

from beacon_merchant_intelligence.models import Product, ProductVariant, VariantAvailability as A


def product(**overrides) -> Product:
    values = {
        "product_id": "fixture-1",
        "title": "Synthetic Everyday Shoe",
        "url": "https://example.invalid/products/shoe",
        "collection_position": 8,
        "size_option": "Size",
        "current_price": Decimal("80"),
        "original_price": Decimal("100"),
        "variants": (
            ProductVariant("5", A.AVAILABLE),
            ProductVariant("6", A.AVAILABLE),
            ProductVariant("7", A.AVAILABLE),
            ProductVariant("8", A.AVAILABLE),
            ProductVariant("9", A.AVAILABLE),
            ProductVariant("10", A.AVAILABLE),
            ProductVariant("11", A.AVAILABLE),
        ),
        "description_present": True,
        "image_count": 5,
        "review_count": 12,
        "source": "synthetic fixture",
    }
    values.update(overrides)
    return Product(**values)


def edge_sizes(*, unknown_middle: bool = False) -> tuple[ProductVariant, ...]:
    sizes = []
    for size in range(5, 12):
        if size in (5, 11):
            availability = A.AVAILABLE
        elif unknown_middle and size == 8:
            availability = A.UNKNOWN
        else:
            availability = A.UNAVAILABLE
        sizes.append(ProductVariant(str(size), availability))
    return tuple(sizes)
