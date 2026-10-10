from decimal import Decimal, InvalidOperation

from ..config import AnalyzerConfig, DEFAULT_CONFIG
from ..models import Assessment, EvidenceSufficiency, Finding, Product

SIGNAL = "heavy_discount_possible_overstock"


def _inventory_evidence(product: Product) -> tuple[bool, str]:
    if product.inventory_age_days is not None and product.inventory_age_days < 0:
        return False, f"Inventory age is invalid ({product.inventory_age_days} days); it is excluded from assessment."
    if product.inventory_age_days is not None and product.inventory_history_source:
        return True, f"Observed inventory age: {product.inventory_age_days} days (source: {product.inventory_history_source})."
    if product.inventory_age_days is not None:
        return False, "Inventory age is present but has no source; inventory history is not considered verified."
    return False, "Inventory age/history was not provided; discount alone does not establish overstock."


def analyze_heavy_discount(
    product: Product, config: AnalyzerConfig = DEFAULT_CONFIG
) -> tuple[Finding, ...]:
    current, original = product.current_price, product.original_price
    valid = (
        current is not None
        and original is not None
        and current.is_finite()
        and original.is_finite()
        and current >= 0
        and original > 0
        and original >= current
    )
    age_known, inventory_evidence = _inventory_evidence(product)
    if not valid:
        reason = "Valid current and original prices were not both observed; discount level cannot be assessed."
        if current is not None and original is not None:
            reason = f"Prices are invalid for discount calculation (current={current}, original={original}); no discount is inferred."
        return (Finding(
            product_id=product.product_id,
            product_title=product.title,
            signal=SIGNAL,
            assessment=Assessment.INSUFFICIENT_EVIDENCE,
            evidence=(reason, inventory_evidence),
            rationale="A discount requires a non-negative current price and a positive original price at least as high as current price; overstock also requires verified inventory context.",
            evidence_sufficiency=EvidenceSufficiency.INSUFFICIENT,
            recommended_action="Verify price data before evaluating discounting; obtain inventory age/history before making an overstock claim.",
            heuristic_score=config.score_insufficient_evidence,
        ),)
    try:
        discount = (Decimal(1) - current / original) * Decimal(100)
    except (InvalidOperation, ZeroDivisionError):
        return ()
    if float(discount) < config.heavy_discount_percent:
        if not age_known:
            return (Finding(
                product_id=product.product_id,
                product_title=product.title,
                signal=SIGNAL,
                assessment=Assessment.INSUFFICIENT_EVIDENCE,
                evidence=(
                    f"Observed price reduction: {discount:.1f}% (below the configured {config.heavy_discount_percent:.1f}% heavy-discount threshold).",
                    inventory_evidence,
                ),
                rationale="The observed price does not cross the heavy-discount threshold, and overstock cannot be assessed without verified inventory history.",
                evidence_sufficiency=EvidenceSufficiency.INSUFFICIENT,
                recommended_action="Obtain inventory age/history before assessing overstock; do not treat price alone as evidence of excess stock.",
                heuristic_score=config.score_insufficient_evidence,
            ),)
        return ()
    evidence = [f"Observed price reduction: {discount:.1f}% ({current} from {original})."]
    evidence.append(inventory_evidence)
    rationale = "The observed discount crosses the configured review threshold; it is a prompt to investigate, not proof of excess inventory."
    if age_known and product.inventory_age_days >= config.overstock_age_days:
        rationale += " The sourced age also crosses the configured aging threshold, which strengthens the case for review but still does not prove overstock."
    return (Finding(
        product_id=product.product_id,
        product_title=product.title,
        signal=SIGNAL,
        assessment=Assessment.SIGNAL,
        evidence=tuple(evidence),
        rationale=rationale,
        evidence_sufficiency=EvidenceSufficiency.LIMITED if not age_known else EvidenceSufficiency.STRONG,
        recommended_action="Review sell-through, stock on hand, replenishment commitments, and promotion context before labeling this overstock.",
        heuristic_score=config.score_heavy_discount,
    ),)
