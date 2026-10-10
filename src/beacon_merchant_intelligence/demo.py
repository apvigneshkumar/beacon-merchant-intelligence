"""Run the deterministic analyzers against synthetic examples."""

from decimal import Decimal

from .analyzers import (
    analyze_best_seller_stockouts,
    analyze_broken_size_run,
    analyze_heavy_discount,
    analyze_prominent_unavailable,
    analyze_thin_page,
)
from .models import Product, ProductVariant, VariantAvailability as Availability
from .reporting import render_markdown


def synthetic_products() -> tuple[Product, ...]:
    sizes = tuple(ProductVariant(str(size), Availability.AVAILABLE if size in {5, 11} else Availability.UNAVAILABLE)
                  for size in range(5, 12))
    return (
        Product(product_id="synthetic-001", title="Synthetic Trail Shoe", url="https://example.invalid/products/trail-shoe",
                collection_position=2, size_option="Size", variants=sizes, sales_rank=4, sales_rank_source="synthetic fixture",
                description_present=True, image_count=1, review_count=0, source="synthetic fixture"),
        Product(product_id="synthetic-002", title="Synthetic Camp Mug", current_price=Decimal("30"),
                original_price=Decimal("60"), inventory_age_days=None, source="synthetic fixture"),
    )


def main() -> None:
    products = synthetic_products()
    findings = []
    for product in products:
        findings.extend(analyze_best_seller_stockouts(product))
        findings.extend(analyze_broken_size_run(product))
        findings.extend(analyze_prominent_unavailable(product))
        findings.extend(analyze_thin_page(product))
        findings.extend(analyze_heavy_discount(product))
    print(render_markdown(findings, synthetic=True))


if __name__ == "__main__":
    main()
