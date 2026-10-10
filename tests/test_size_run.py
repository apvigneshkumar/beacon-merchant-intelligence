from beacon_merchant_intelligence.analyzers import analyze_broken_size_run
from beacon_merchant_intelligence.models import Assessment, EvidenceSufficiency, ProductVariant, VariantAvailability as A
from fixtures import edge_sizes, product


def test_only_edge_sizes_remaining_is_flagged():
    result = analyze_broken_size_run(product(variants=edge_sizes()))
    assert len(result) == 1
    assert result[0].evidence_sufficiency is EvidenceSufficiency.LIMITED
    assert "5, 11" in result[0].evidence[0]
    assert "does not establish" in result[0].rationale


def test_unknown_sizes_reduce_evidence_sufficiency():
    result = analyze_broken_size_run(product(variants=edge_sizes(unknown_middle=True)))
    assert len(result) == 1
    assert result[0].evidence_sufficiency is EvidenceSufficiency.LIMITED
    assert "unknown" in result[0].evidence[-1]


def test_size_run_requires_enough_numeric_variants():
    variants = tuple(ProductVariant(str(size), A.UNAVAILABLE) for size in (6, 7, 8, 9))
    finding = analyze_broken_size_run(product(variants=variants))[0]
    assert finding.assessment is Assessment.INSUFFICIENT_EVIDENCE
    assert "only 4 distinct numeric sizes" in finding.evidence[0]


def test_middle_size_availability_is_not_misclassified_as_edge_only():
    variants = tuple(ProductVariant(str(size), A.AVAILABLE if size in (7, 8) else A.UNAVAILABLE)
                     for size in range(5, 12))
    assert analyze_broken_size_run(product(variants=variants)) == ()


def test_numeric_variants_without_identified_size_option_are_not_assumed_to_be_sizes():
    assert analyze_broken_size_run(product(size_option=None, variants=edge_sizes())) == ()


def test_named_size_option_with_non_numeric_labels_is_insufficient():
    variants = tuple(ProductVariant(name, A.AVAILABLE) for name in ("Small", "Medium", "Large"))
    finding = analyze_broken_size_run(product(size_option="Size", variants=variants))[0]
    assert finding.assessment is Assessment.INSUFFICIENT_EVIDENCE
    assert "only 0 distinct numeric sizes were parsed" in finding.evidence[0]


def test_unknown_availability_is_not_counted_as_sold_out():
    variants = tuple(ProductVariant(str(size), A.UNKNOWN) for size in range(5, 12))
    finding = analyze_broken_size_run(product(variants=variants))[0]
    assert finding.assessment is Assessment.INSUFFICIENT_EVIDENCE
    assert "unknown for all 7" in finding.evidence[0]


def test_unknown_availability_is_not_reported_as_a_stockout():
    variants = tuple(
        ProductVariant(str(size), A.AVAILABLE if size in (5, 6, 7, 8) else A.UNKNOWN)
        for size in range(5, 12)
    )
    finding = analyze_broken_size_run(product(variants=variants))[0]
    assert finding.assessment is Assessment.INSUFFICIENT_EVIDENCE
    assert "No unavailable numeric size option was observed" in finding.evidence[0]


def test_size_analysis_sorts_sizes_independent_of_variant_order():
    variants = tuple(reversed(edge_sizes()))
    result = analyze_broken_size_run(product(variants=variants))
    assert len(result) == 1
    assert "5, 11" in result[0].evidence[0]


def test_duplicate_color_variants_do_not_inflate_size_run():
    variants = list(edge_sizes())
    variants.extend((ProductVariant("5 / Navy", A.UNAVAILABLE), ProductVariant("11 / Navy", A.UNAVAILABLE)))
    result = analyze_broken_size_run(product(variants=tuple(variants)))
    # Size 5 and 11 remain available in one color. Counting duplicate color
    # variants as separate sizes would distort the 2-of-7 size-run ratio.
    assert len(result) == 1
    assert "2 of 7 numeric sizes" in result[0].evidence[1]


def test_non_numeric_variant_labels_are_disclosed_and_excluded():
    variants = list(edge_sizes()) + [ProductVariant("Tall", A.UNAVAILABLE)]
    finding = analyze_broken_size_run(product(variants=tuple(variants)))[0]
    assert "Non-numeric variant labels excluded from the size comparison: Tall." in finding.evidence
