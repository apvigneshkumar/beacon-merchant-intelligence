from ..config import AnalyzerConfig, DEFAULT_CONFIG
from ..models import Assessment, EvidenceSufficiency, Finding, Product
from .common import finding, unavailable_variant_names

SIGNAL = "prominent_collection_item_unavailable"


def analyze_prominent_unavailable(
    product: Product, config: AnalyzerConfig = DEFAULT_CONFIG
) -> tuple[Finding, ...]:
    if product.collection_position is None or product.collection_position < 1:
        return ()
    if product.collection_position > config.prominent_position_max:
        return ()
    unavailable = unavailable_variant_names(product)
    if not unavailable:
        return ()
    unknown_count = sum(variant.availability.value == "unknown" for variant in product.variants)
    evidence = [
        f"Observed collection position: {product.collection_position} (visibility proxy only).",
        "Unavailable variants: " + ", ".join(unavailable) + ".",
    ]
    if unknown_count:
        evidence.append(f"Availability is unknown for {unknown_count} additional variant(s).")
    return (finding(
        product, signal=SIGNAL, assessment=Assessment.SIGNAL,
        evidence=tuple(evidence),
        rationale="A high-visibility collection position co-occurs with unavailable variants; position does not establish demand.",
        sufficiency=EvidenceSufficiency.LIMITED,
        action="Check whether the collection ordering and availability are current, and consider surfacing available alternatives.",
        score=config.score_prominent_unavailable,
    ),)
