"""Deterministic ordering for findings; scores are heuristic, not probabilities."""

from collections.abc import Iterable

from .models import Finding


def prioritize_findings(findings: Iterable[Finding]) -> tuple[Finding, ...]:
    """Sort by configured heuristic score, then signal and product for stable output."""
    return tuple(sorted(
        findings,
        key=lambda item: (-item.heuristic_score, item.signal, item.product_title or ""),
    ))
