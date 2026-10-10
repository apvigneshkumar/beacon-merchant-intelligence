from ..models import Assessment, EvidenceSufficiency, Finding, Product


def finding(
    product: Product,
    *,
    signal: str,
    assessment: Assessment,
    evidence: tuple[str, ...],
    rationale: str,
    sufficiency: EvidenceSufficiency,
    action: str,
    score: int,
) -> Finding:
    return Finding(
        product_id=product.product_id,
        product_title=product.title,
        signal=signal,
        assessment=assessment,
        evidence=evidence,
        rationale=rationale,
        evidence_sufficiency=sufficiency,
        recommended_action=action,
        heuristic_score=score,
    )


def unavailable_variant_names(product: Product) -> tuple[str, ...]:
    return tuple(
        variant.name or "unnamed variant"
        for variant in product.variants
        if variant.availability.value == "unavailable"
    )
