from ..config import AnalyzerConfig, DEFAULT_CONFIG
from ..models import Assessment, EvidenceSufficiency, Finding, Product

SIGNAL = "product_page_completeness"


def analyze_thin_page(
    product: Product, config: AnalyzerConfig = DEFAULT_CONFIG
) -> tuple[Finding, ...]:
    evidence: list[str] = []
    actionable_gaps: list[str] = []
    if product.description_present is False:
        evidence.append("No product description was observed.")
        actionable_gaps.append("description")
    elif product.description_present is None:
        evidence.append("Description presence was not observed.")
    invalid_image_count = product.image_count is not None and product.image_count < 0
    if invalid_image_count:
        evidence.append(f"Invalid image count was observed ({product.image_count}); it is excluded from assessment.")
    elif product.image_count is not None and product.image_count < config.thin_image_max_count:
        evidence.append(f"Observed image count: {product.image_count} (configured thin-page threshold: fewer than {config.thin_image_max_count}).")
        actionable_gaps.append("imagery")
    elif product.image_count is None:
        evidence.append("Image count was not observed.")
    invalid_review_count = product.review_count is not None and product.review_count < 0
    if invalid_review_count:
        evidence.append(f"Invalid review count was observed ({product.review_count}); it is not interpreted as zero reviews.")
    elif product.review_count == 0:
        evidence.append("No review signal was observed (review count is zero); this alone is not treated as a defect.")
    elif product.review_count is None:
        evidence.append("Review count was not observed; missing data is not interpreted as zero reviews.")
    if not actionable_gaps:
        return ()
    unknown = (
        product.description_present is None
        or product.image_count is None
        or invalid_image_count
        or product.review_count is None
        or invalid_review_count
        or product.review_count == 0
    )
    gaps = " and ".join(actionable_gaps)
    return (Finding(
        product_id=product.product_id,
        product_title=product.title,
        signal=SIGNAL,
        assessment=Assessment.SIGNAL,
        evidence=tuple(evidence),
        rationale=f"The observed page has a potential content-completeness gap in {gaps}; review absence is contextual evidence only.",
        evidence_sufficiency=EvidenceSufficiency.LIMITED if unknown else EvidenceSufficiency.STRONG,
        recommended_action="Review the product page with shoppers or merchandising staff and add useful content only where it answers a real purchase question.",
        heuristic_score=config.score_thin_page,
    ),)
