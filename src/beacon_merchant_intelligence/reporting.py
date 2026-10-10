from collections.abc import Iterable

from .analyzers import (
    analyze_best_seller_stockouts,
    analyze_broken_size_run,
    analyze_heavy_discount,
    analyze_prominent_unavailable,
    analyze_thin_page,
)
from .models import Finding, Product
from .prioritization import prioritize_findings


def render_markdown(findings: Iterable[Finding], *, synthetic: bool = False) -> str:
    rows = prioritize_findings(findings)
    title = "# Beacon merchant intelligence report"
    if synthetic:
        title += "\n\n> Synthetic demonstration data only; no real store was analyzed."
    if not rows:
        return title + "\n\nNo findings were produced from the supplied observations."
    sections = [title]
    for item in rows:
        sections.extend([
            "",
            f"## {item.product_title or item.product_id or 'Unknown product'} — {item.signal}",
            f"- Assessment: `{item.assessment.value}`",
            f"- Evidence sufficiency: `{item.evidence_sufficiency.value}`",
            f"- Heuristic priority score: {item.heuristic_score}/100 (not a probability)",
            "- Evidence:",
            *(f"  - {entry}" for entry in item.evidence),
            f"- Rationale: {item.rationale}",
            f"- Recommended action: {item.recommended_action}",
        ])
    return "\n".join(sections)


def render_collected_markdown(dataset: dict[str, object]) -> str:
    """Analyze collected products with the existing deterministic analyzers."""
    products = dataset.get("products", [])
    if not isinstance(products, list) or not all(isinstance(item, Product) for item in products):
        raise ValueError("dataset products must be normalized Product records")
    findings: list[Finding] = []
    analyzers = (
        analyze_best_seller_stockouts,
        analyze_broken_size_run,
        analyze_prominent_unavailable,
        analyze_thin_page,
        analyze_heavy_discount,
    )
    for product in products:
        for analyze in analyzers:
            findings.extend(analyze(product))

    collection_title = dataset.get("collection_title")
    scope = f"Collection: {collection_title}" if collection_title else "Scope: storefront product sample"
    store_name = dataset.get("store_name", "unknown store")
    if dataset.get("fictional_demo_data") is True:
        source_note = f"Source: Shopify {store_name} public demo API. Products are fictional demo data, not real merchant observations."
    else:
        source_note = f"Source: {store_name} public catalog ({dataset.get('source_method', 'read-only API')})."
    header = [
        "# Beacon merchant intelligence report",
        "",
        f"> {source_note}",
        f"> Requested URL: {dataset.get('requested_url')}",
        f"> API endpoint: {dataset.get('source_endpoint')}",
        *( [f"> Search query: {dataset.get('query')} (result order is not sales rank or collection position)."] if dataset.get("query") else [] ),
        f"> {scope}; collected {dataset.get('returned_products')} product(s), maximum {dataset.get('max_products')}.",
        f"> Observed at: {dataset.get('observed_at')}",
        "",
        "## Collection warnings",
    ]
    warnings = dataset.get("warnings", [])
    if isinstance(warnings, list) and warnings:
        header.extend(f"- {warning}" for warning in warnings)
    else:
        header.append("- None reported.")
    header.extend(["", "## Analyzer findings", ""])
    body = render_markdown(findings)
    # Remove the duplicate title emitted by the shared finding renderer.
    body = body.removeprefix("# Beacon merchant intelligence report\n\n")
    return "\n".join(header) + body + "\n"
