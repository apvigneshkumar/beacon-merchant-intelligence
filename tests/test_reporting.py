from decimal import Decimal

from beacon_merchant_intelligence.analyzers import analyze_heavy_discount
from beacon_merchant_intelligence.models import Finding, Assessment, EvidenceSufficiency
from beacon_merchant_intelligence.prioritization import prioritize_findings
from beacon_merchant_intelligence.reporting import render_markdown
from fixtures import product


def test_prioritization_is_stable_and_highest_score_first():
    low = Finding("b", "B", "z", Assessment.SIGNAL, ("evidence",), "why", EvidenceSufficiency.LIMITED, "act", 20)
    high = Finding("a", "A", "a", Assessment.SIGNAL, ("evidence",), "why", EvidenceSufficiency.STRONG, "act", 80)
    assert prioritize_findings((low, high)) == (high, low)


def test_report_labels_synthetic_data_and_non_probability_score():
    finding = analyze_heavy_discount(product(current_price=Decimal("50"), original_price=Decimal("100")))[0]
    report = render_markdown((finding,), synthetic=True)
    assert "Synthetic demonstration data only" in report
    assert "not a probability" in report
    assert "Recommended action" in report


def test_empty_report_is_explained():
    assert "No findings" in render_markdown(())
