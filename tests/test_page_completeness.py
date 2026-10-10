from beacon_merchant_intelligence.analyzers import analyze_thin_page
from beacon_merchant_intelligence.models import EvidenceSufficiency
from fixtures import product


def test_missing_description_and_low_image_count_produce_finding():
    result = analyze_thin_page(product(description_present=False, image_count=1, review_count=None))
    assert len(result) == 1
    assert result[0].evidence_sufficiency is EvidenceSufficiency.LIMITED
    assert "No product description" in " ".join(result[0].evidence)
    assert "Observed image count: 1" in " ".join(result[0].evidence)


def test_zero_reviews_alone_is_not_a_defect_or_finding():
    assert analyze_thin_page(product(review_count=0)) == ()


def test_unknown_reviews_are_not_treated_as_zero():
    assert analyze_thin_page(product(review_count=None)) == ()


def test_missing_fields_remain_explicitly_unknown_if_other_gap_triggers_finding():
    result = analyze_thin_page(product(description_present=None, image_count=0, review_count=None))
    assert len(result) == 1
    joined = " ".join(result[0].evidence)
    assert "Description presence was not observed" in joined
    assert "Image count was not observed" not in joined
    assert "Review count was not observed" in joined


def test_negative_image_and_review_counts_are_not_used_as_observations():
    assert analyze_thin_page(product(image_count=-1, review_count=-1)) == ()


def test_invalid_counts_are_reported_as_excluded_when_another_gap_triggers_finding():
    finding = analyze_thin_page(product(
        description_present=False, image_count=-1, review_count=-2,
    ))[0]
    joined = " ".join(finding.evidence)
    assert "Invalid image count" in joined
    assert "excluded from assessment" in joined
    assert "not interpreted as zero reviews" in joined
    assert finding.evidence_sufficiency is EvidenceSufficiency.LIMITED
