"""Command-line entry point for the bounded public mock.shop collector."""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import fields
from datetime import datetime
from decimal import Decimal
from pathlib import Path

from .collector import DEFAULT_PRODUCTS, MAX_PRODUCTS, CollectionError, collect_storefront
from .models import Product
from .reporting import render_collected_markdown


def _product_dict(product: Product, currency_codes: tuple[str, ...]) -> dict[str, object]:
    result: dict[str, object] = {}
    for item in fields(Product):
        value = getattr(product, item.name)
        if isinstance(value, Decimal):
            value = str(value)
        elif isinstance(value, datetime):
            value = value.isoformat()
        elif item.name == "variants":
            value = [
                {"name": variant.name, "availability": variant.availability.value}
                for variant in product.variants
            ]
        result[item.name] = value
    result["currency_codes_observed"] = list(currency_codes)
    return result


def serialize_dataset(dataset: dict[str, object]) -> str:
    products = dataset["products"]
    currencies = dataset["currency_codes_by_product"]
    if not isinstance(products, list) or not isinstance(currencies, list):
        raise ValueError("invalid collector dataset")
    output = {key: value for key, value in dataset.items() if key not in {"products", "currency_codes_by_product"}}
    output["products"] = [
        _product_dict(product, tuple(currency_codes))
        for product, currency_codes in zip(products, currencies, strict=True)
    ]
    return json.dumps(output, indent=2, ensure_ascii=False) + "\n"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="beacon-collect",
        description="Collect a bounded product sample from a public Shopify mock.shop storefront.",
    )
    parser.add_argument("url", help="https://mock.shop/ or https://{store}.mock.shop/collections/{handle}")
    parser.add_argument("--max-products", type=int, default=DEFAULT_PRODUCTS, help=f"products to collect (1-{MAX_PRODUCTS}; default {DEFAULT_PRODUCTS})")
    parser.add_argument("--json-out", type=Path, default=Path("artifacts/collection.json"), help="normalized JSON dataset path")
    parser.add_argument("--report-out", type=Path, default=Path("artifacts/report.md"), help="Markdown analyzer report path")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        dataset = collect_storefront(args.url, max_products=args.max_products)
        report = render_collected_markdown(dataset)
        json_text = serialize_dataset(dataset)
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.report_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(json_text, encoding="utf-8")
        args.report_out.write_text(report, encoding="utf-8")
    except (CollectionError, OSError, ValueError) as exc:
        print(f"beacon-collect: {exc}", file=sys.stderr)
        return 2
    print(f"Collected {dataset['returned_products']} fictional demo product(s).")
    print(f"JSON: {args.json_out}")
    print(f"Report: {args.report_out}")
    for warning in dataset["warnings"]:
        print(f"Warning: {warning}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
