from ..config import AnalyzerConfig, DEFAULT_CONFIG
from ..models import Assessment, EvidenceSufficiency, Finding, Product
from .common import finding, unavailable_variant_names

SIGNAL = "sales_ranked_unavailable_variants"


def analyze_best_seller_stockouts(
    product: Product, config: AnalyzerConfig = DEFAULT_CONFIG
) -> tuple[Finding, ...]:
    if product.sales_rank is None:
        unavailable = unavailable_variant_names(product)
        evidence = ["Sales rank was not provided; best-selling status cannot be established."]
        if unavailable:
            evidence.append("Observed unavailable variants: " + ", ".join(unavailable) + ".")
        return (finding(
            product, signal=SIGNAL, assessment=Assessment.INSUFFICIENT_EVIDENCE,
            evidence=tuple(evidence),
            rationale="The best-selling status cannot be assessed without an observed, sourced sales ranking.",
            sufficiency=EvidenceSufficiency.INSUFFICIENT,
            action="Connect a verified sales ranking or merchant sales feed before prioritizing restock.",
            score=config.score_insufficient_evidence,
        ),)
    if product.sales_rank < 1:
        return (finding(
            product, signal=SIGNAL, assessment=Assessment.INSUFFICIENT_EVIDENCE,
            evidence=(f"Sales rank {product.sales_rank} is invalid; ranks start at 1.",),
            rationale="Invalid ranking data cannot establish best-selling status.",
            sufficiency=EvidenceSufficiency.INSUFFICIENT,
            action="Correct or discard the ranking value before using it for prioritization.",
            score=config.score_insufficient_evidence,
        ),)
    if product.sales_rank > config.best_seller_rank_max:
        return ()
    if not product.sales_rank_source:
        return (finding(
            product, signal=SIGNAL, assessment=Assessment.INSUFFICIENT_EVIDENCE,
            evidence=(f"Sales rank {product.sales_rank} is present, but its source is missing.",),
            rationale="An unproven ranking cannot support a best-seller claim.",
            sufficiency=EvidenceSufficiency.INSUFFICIENT,
            action="Verify the ranking source and time window before using it for restock decisions.",
            score=config.score_insufficient_evidence,
        ),)
    observed_availability = [variant for variant in product.variants if variant.availability.value != "unknown"]
    if not observed_availability:
        return (finding(
            product, signal=SIGNAL, assessment=Assessment.INSUFFICIENT_EVIDENCE,
            evidence=(
                f"Observed sales rank: {product.sales_rank} (source: {product.sales_rank_source}).",
                "No variant availability was observed; stockout status cannot be assessed.",
            ),
            rationale="A sourced sales ranking is available, but variant availability evidence is missing.",
            sufficiency=EvidenceSufficiency.INSUFFICIENT,
            action="Collect variant-level availability before assessing a best-seller stockout.",
            score=config.score_insufficient_evidence,
        ),)
    unavailable = unavailable_variant_names(product)
    if not unavailable:
        return ()
    unknown_count = sum(variant.availability.value == "unknown" for variant in product.variants)
    evidence = [
        f"Observed sales rank: {product.sales_rank} (source: {product.sales_rank_source}).",
        "Unavailable variants: " + ", ".join(unavailable) + ".",
    ]
    if unknown_count:
        evidence.append(f"Availability is unknown for {unknown_count} additional variant(s).")
    return (finding(
        product, signal=SIGNAL, assessment=Assessment.SIGNAL,
        evidence=tuple(evidence),
        rationale="A sourced high sales ranking and at least one unavailable variant co-occur; this is a restock-priority candidate, not proof of lost sales.",
        sufficiency=(
            EvidenceSufficiency.LIMITED
            if len(observed_availability) < len(product.variants)
            else EvidenceSufficiency.STRONG
        ),
        action="Check recent variant-level sales, inventory, and replenishment lead time before changing the purchase order.",
        score=config.score_best_seller_stockout,
    ),)
