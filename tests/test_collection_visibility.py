from beacon_merchant_intelligence.analyzers import analyze_prominent_unavailable
from beacon_merchant_intelligence.config import AnalyzerConfig
from beacon_merchant_intelligence.models import EvidenceSufficiency, ProductVariant, VariantAvailability as A
from fixtures import product


def test_prominent_unavailable_item_is_flagged_as_visibility_proxy():
    result = analyze_prominent_unavailable(product(
        collection_position=2, variants=(ProductVariant("Blue", A.UNAVAILABLE),)
    ))
    assert len(result) == 1
    assert result[0].evidence_sufficiency is EvidenceSufficiency.LIMITED
    assert "visibility proxy only" in result[0].evidence[0]
    assert "does not establish demand" in result[0].rationale


def test_position_outside_threshold_is_not_flagged():
    result = analyze_prominent_unavailable(product(
        collection_position=6, variants=(ProductVariant("Blue", A.UNAVAILABLE),)
    ), AnalyzerConfig(prominent_position_max=5))
    assert result == ()


def test_unknown_variant_availability_is_not_assumed_unavailable():
    assert analyze_prominent_unavailable(product(
        collection_position=1, variants=(ProductVariant("Blue", A.UNKNOWN),)
    )) == ()


def test_partial_unknown_availability_is_disclosed_in_evidence():
    result = analyze_prominent_unavailable(product(
        collection_position=1,
        variants=(ProductVariant("Blue", A.UNAVAILABLE), ProductVariant("Green", A.UNKNOWN)),
    ))
    assert "Availability is unknown for 1 additional variant(s)." in result[0].evidence


def test_missing_collection_position_is_not_assumed_prominent():
    assert analyze_prominent_unavailable(product(
        collection_position=None, variants=(ProductVariant("Blue", A.UNAVAILABLE),)
    )) == ()
