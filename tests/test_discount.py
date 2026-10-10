from decimal import Decimal

from beacon_merchant_intelligence.analyzers import analyze_heavy_discount
from beacon_merchant_intelligence.config import AnalyzerConfig
from beacon_merchant_intelligence.models import Assessment, EvidenceSufficiency
from fixtures import product


def test_heavy_discount_is_possible_overstock_not_a_claim():
    finding = analyze_heavy_discount(product(current_price=Decimal("50"), original_price=Decimal("100")))[0]
    assert finding.assessment is Assessment.SIGNAL
    assert finding.evidence_sufficiency is EvidenceSufficiency.LIMITED
    assert "does not establish overstock" in finding.evidence[-1]
    assert "not proof" in finding.rationale


def test_sourced_old_inventory_adds_context_but_not_certainty():
    finding = analyze_heavy_discount(product(
        current_price=Decimal("50"), original_price=Decimal("100"),
        inventory_age_days=120, inventory_history_source="synthetic inventory history",
    ))[0]
    assert finding.evidence_sufficiency is EvidenceSufficiency.STRONG
    assert "120 days" in finding.evidence[1]
    assert "does not prove overstock" in finding.rationale


def test_discount_below_configured_threshold_is_not_flagged():
    finding = analyze_heavy_discount(
        product(current_price=Decimal("80"), original_price=Decimal("100")),
        AnalyzerConfig(heavy_discount_percent=25),
    )[0]
    assert finding.assessment is Assessment.INSUFFICIENT_EVIDENCE
    assert "below the configured" in finding.evidence[0]


def test_missing_prices_explicitly_report_insufficient_evidence():
    finding = analyze_heavy_discount(product(current_price=None, original_price=None))[0]
    assert finding.assessment is Assessment.INSUFFICIENT_EVIDENCE
    assert "cannot be assessed" in finding.evidence[0]


def test_invalid_price_order_is_not_interpreted_as_discount():
    finding = analyze_heavy_discount(product(current_price=Decimal("110"), original_price=Decimal("100")))[0]
    assert finding.assessment is Assessment.INSUFFICIENT_EVIDENCE
    assert "Prices are invalid" in finding.evidence[0]


def test_negative_current_price_is_invalid():
    finding = analyze_heavy_discount(product(current_price=Decimal("-1"), original_price=Decimal("100")))[0]
    assert finding.assessment is Assessment.INSUFFICIENT_EVIDENCE


def test_non_finite_price_is_invalid_without_raising():
    finding = analyze_heavy_discount(product(current_price=Decimal("NaN"), original_price=Decimal("100")))[0]
    assert finding.assessment is Assessment.INSUFFICIENT_EVIDENCE


def test_unverified_inventory_age_does_not_increase_evidence_sufficiency():
    finding = analyze_heavy_discount(product(
        current_price=Decimal("50"), original_price=Decimal("100"),
        inventory_age_days=120, inventory_history_source=None,
    ))[0]
    assert finding.evidence_sufficiency is EvidenceSufficiency.LIMITED
    assert "has no source" in finding.evidence[-1]


def test_missing_inventory_history_is_explicit_when_discount_is_heavy():
    finding = analyze_heavy_discount(product(current_price=Decimal("50"), original_price=Decimal("100")))[0]
    assert "Inventory age/history was not provided" in finding.evidence[-1]


def test_missing_inventory_history_is_explicit_even_without_heavy_discount():
    finding = analyze_heavy_discount(product(current_price=Decimal("80"), original_price=Decimal("100")))[0]
    assert finding.assessment is Assessment.INSUFFICIENT_EVIDENCE
    assert "Inventory age/history was not provided" in finding.evidence[-1]
