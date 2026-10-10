import re

from ..config import AnalyzerConfig, DEFAULT_CONFIG
from ..models import Assessment, EvidenceSufficiency, Finding, Product, VariantAvailability
from .common import finding

SIGNAL = "broken_size_run"
_SIZE = re.compile(r"^\s*(\d+(?:\.\d+)?)\b")


def _numeric_size(name: str | None) -> float | None:
    if name is None:
        return None
    match = _SIZE.match(name)
    return float(match.group(1)) if match else None


def analyze_broken_size_run(
    product: Product, config: AnalyzerConfig = DEFAULT_CONFIG
) -> tuple[Finding, ...]:
    if not product.size_option:
        # Do not infer that numeric options are sizes (they may be volume,
        # pack count, model year, or another product-specific dimension).
        return ()
    # A size/color matrix may have several variants for the same size. Collapse
    # those into one size, treating it as available if any corresponding variant
    # is available, unavailable only if every corresponding variant is so.
    by_size: dict[float, list[VariantAvailability]] = {}
    unparsed_labels: list[str] = []
    for variant in product.variants:
        size = _numeric_size(variant.name)
        if size is not None:
            by_size.setdefault(size, []).append(variant.availability)
        else:
            unparsed_labels.append(variant.name or "unnamed variant")
    sized: list[tuple[float, str, VariantAvailability]] = []
    for size, statuses in sorted(by_size.items()):
        if VariantAvailability.AVAILABLE in statuses:
            availability = VariantAvailability.AVAILABLE
        elif all(status == VariantAvailability.UNAVAILABLE for status in statuses):
            availability = VariantAvailability.UNAVAILABLE
        else:
            availability = VariantAvailability.UNKNOWN
        display = str(int(size)) if size.is_integer() else str(size)
        sized.append((size, display, availability))
    if len(sized) < config.size_run_min_variants:
        return (finding(
            product, signal=SIGNAL, assessment=Assessment.INSUFFICIENT_EVIDENCE,
            evidence=(
                f"Size option '{product.size_option}' was identified, but only {len(sized)} distinct numeric sizes were parsed; at least {config.size_run_min_variants} are required.",
                "The expected size range and category-specific size standards were not provided.",
            ),
            rationale="The size-run heuristic needs enough explicitly identified numeric size options to compare observed availability.",
            sufficiency=EvidenceSufficiency.INSUFFICIENT,
            action="Confirm the size option and expected assortment before evaluating a size-run gap.",
            score=config.score_insufficient_evidence,
        ),)
    available = [i for i, (_, _, status) in enumerate(sized) if status == VariantAvailability.AVAILABLE]
    unavailable = [i for i, (_, _, status) in enumerate(sized) if status == VariantAvailability.UNAVAILABLE]
    unknown_count = sum(status == VariantAvailability.UNKNOWN for _, _, status in sized)
    if not available and not unavailable:
        return (finding(
            product, signal=SIGNAL, assessment=Assessment.INSUFFICIENT_EVIDENCE,
            evidence=(f"Availability is unknown for all {len(sized)} observed numeric size options.",),
            rationale="No size-run pattern can be evaluated without observed available or unavailable status.",
            sufficiency=EvidenceSufficiency.INSUFFICIENT,
            action="Collect variant availability before assessing a size-run pattern.",
            score=config.score_insufficient_evidence,
        ),)
    if not available:
        return ()
    if not unavailable:
        if unknown_count:
            return (finding(
                product, signal=SIGNAL, assessment=Assessment.INSUFFICIENT_EVIDENCE,
                evidence=(
                    "No unavailable numeric size option was observed.",
                    f"Availability is unknown for {unknown_count} of {len(sized)} observed numeric size options.",
                ),
                rationale="Unknown availability cannot be treated as a stockout, so a broken run cannot be confirmed.",
                sufficiency=EvidenceSufficiency.INSUFFICIENT,
                action="Confirm availability for the remaining size options before evaluating the run.",
                score=config.score_insufficient_evidence,
            ),)
        return ()
    ratio = len(available) / len(sized)
    if ratio > config.size_run_max_available_ratio:
        return ()
    edge = max(1, int(len(sized) * config.size_run_edge_fraction))
    edge_indices = set(range(edge)) | set(range(len(sized) - edge, len(sized)))
    if not all(index in edge_indices for index in available):
        return ()
    available_names = [sized[i][1] for i in available]
    evidence = [
        f"Available numeric sizes observed: {', '.join(available_names)}.",
        f"{len(available)} of {len(sized)} numeric sizes are reported available ({ratio:.0%}).",
    ]
    if unknown_count:
        evidence.append(f"Availability is unknown for {unknown_count} numeric size(s); the run is only partially observed.")
    if unparsed_labels:
        evidence.append(
            f"Non-numeric variant labels excluded from the size comparison: {', '.join(unparsed_labels)}."
        )
    return (finding(
        product, signal=SIGNAL, assessment=Assessment.SIGNAL,
        evidence=tuple(evidence),
        rationale=(
            f"Among the product's observed numeric options for '{product.size_option}', available sizes are sparse and occur at the observed endpoints. "
            "This does not establish that unlisted sizes belong in this product's assortment."
        ),
        sufficiency=EvidenceSufficiency.LIMITED,
        action="Compare this observed pattern with the product's intended size range and size-level demand before changing replenishment.",
        score=config.score_broken_size_run,
    ),)
