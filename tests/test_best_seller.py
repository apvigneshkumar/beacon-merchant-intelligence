from beacon_merchant_intelligence.analyzers import analyze_best_seller_stockouts
from beacon_merchant_intelligence.config import AnalyzerConfig
from beacon_merchant_intelligence.models import Assessment, ProductVariant, VariantAvailability as A
from fixtures import product


def test_sourced_best_seller_with_sold_out_variant_is_flagged():
    result = analyze_best_seller_stockouts(product(
        sales_rank=2, sales_rank_source="synthetic order export",
        variants=(ProductVariant("M", A.UNAVAILABLE),),
    ))
    assert len(result) == 1
    assert result[0].assessment is Assessment.SIGNAL
    assert "M" in " ".join(result[0].evidence)
    assert result[0].recommended_action


def test_missing_sales_rank_is_explicitly_insufficient():
    finding = analyze_best_seller_stockouts(product())[0]
    assert finding.assessment is Assessment.INSUFFICIENT_EVIDENCE
    assert finding.evidence_sufficiency.value == "insufficient"
    assert "Sales rank was not provided" in finding.evidence[0]


def test_unavailable_variants_are_reported_but_not_called_best_sellers_without_rank():
    finding = analyze_best_seller_stockouts(product(
        sales_rank=None,
        variants=(ProductVariant("M", A.UNAVAILABLE), ProductVariant("L", A.AVAILABLE)),
    ))[0]
    assert finding.assessment is Assessment.INSUFFICIENT_EVIDENCE
    assert "Observed unavailable variants: M." in finding.evidence
    assert "best-selling status cannot be established" in finding.evidence[0]


def test_rank_without_source_cannot_support_best_seller_claim():
    finding = analyze_best_seller_stockouts(product(sales_rank=1))[0]
    assert finding.assessment is Assessment.INSUFFICIENT_EVIDENCE
    assert "source is missing" in finding.evidence[0]


def test_rank_outside_configured_top_n_is_not_flagged():
    result = analyze_best_seller_stockouts(
        product(sales_rank=12, sales_rank_source="synthetic"),
        AnalyzerConfig(best_seller_rank_max=10),
    )
    assert result == ()


def test_invalid_nonpositive_rank_is_insufficient_evidence():
    finding = analyze_best_seller_stockouts(product(sales_rank=0, sales_rank_source="synthetic"))[0]
    assert finding.assessment is Assessment.INSUFFICIENT_EVIDENCE
    assert "invalid" in finding.evidence[0]


def test_available_variants_do_not_make_a_stockout_signal():
    assert analyze_best_seller_stockouts(product(sales_rank=1, sales_rank_source="synthetic")) == ()


def test_missing_variant_availability_is_explicitly_insufficient():
    finding = analyze_best_seller_stockouts(product(
        sales_rank=1, sales_rank_source="synthetic",
        variants=(ProductVariant("M", A.UNKNOWN),),
    ))[0]
    assert finding.assessment is Assessment.INSUFFICIENT_EVIDENCE
    assert "No variant availability was observed" in finding.evidence[-1]


def test_partial_variant_availability_reduces_sufficiency():
    finding = analyze_best_seller_stockouts(product(
        sales_rank=1, sales_rank_source="synthetic",
        variants=(ProductVariant("M", A.UNAVAILABLE), ProductVariant("L", A.UNKNOWN)),
    ))[0]
    assert finding.evidence_sufficiency.value == "limited"
    assert "Availability is unknown for 1 additional variant" in finding.evidence[-1]
