"""CLI for Sporting Feet's public read-only UCP catalog search."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .cli import serialize_dataset
from .reporting import render_collected_markdown
from .sporting_feet import DEFAULT_PRODUCTS, MAX_PRODUCTS, SportingFeetError, collect_storefront


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="beacon-collect-sporting-feet",
        description="Collect a bounded read-only product sample from Sporting Feet's public catalog API.",
    )
    parser.add_argument("url", help="https://www.sporting-feet.com/")
    parser.add_argument("--query", default="trainers", help="UCP catalog search query (default: trainers)")
    parser.add_argument("--max-products", type=int, default=DEFAULT_PRODUCTS,
                        help=f"products to collect (1-{MAX_PRODUCTS}; default {DEFAULT_PRODUCTS})")
    parser.add_argument("--json-out", type=Path, default=Path("artifacts/sporting-feet.json"))
    parser.add_argument("--report-out", type=Path, default=Path("artifacts/sporting-feet.md"))
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        dataset = collect_storefront(args.url, query=args.query, max_products=args.max_products)
        json_text = serialize_dataset(dataset)
        report = render_collected_markdown(dataset)
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.report_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(json_text, encoding="utf-8")
        args.report_out.write_text(report, encoding="utf-8")
    except (SportingFeetError, OSError, ValueError) as exc:
        print(f"beacon-collect-sporting-feet: {exc}", file=sys.stderr)
        return 2
    print(f"Collected {dataset['returned_products']} public Sporting Feet product(s).")
    print(f"JSON: {args.json_out}")
    print(f"Report: {args.report_out}")
    for warning in dataset["warnings"]:
        print(f"Warning: {warning}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
