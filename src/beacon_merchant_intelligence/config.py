"""Explicit thresholds and ordinal heuristic scores for the prototype."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class AnalyzerConfig:
    best_seller_rank_max: int = 20
    prominent_position_max: int = 5
    size_run_min_variants: int = 5
    size_run_max_available_ratio: float = 0.40
    size_run_edge_fraction: float = 0.25
    thin_image_max_count: int = 2
    heavy_discount_percent: float = 40.0
    overstock_age_days: int = 90
    score_best_seller_stockout: int = 85
    score_broken_size_run: int = 65
    score_prominent_unavailable: int = 70
    score_thin_page: int = 35
    score_heavy_discount: int = 30
    score_insufficient_evidence: int = 0

    def __post_init__(self) -> None:
        if self.best_seller_rank_max < 1 or self.prominent_position_max < 1:
            raise ValueError("rank and position thresholds must be positive")
        if self.size_run_min_variants < 2:
            raise ValueError("size_run_min_variants must be at least 2")
        if not 0 <= self.size_run_max_available_ratio <= 1:
            raise ValueError("size_run_max_available_ratio must be between 0 and 1")
        if not 0 < self.size_run_edge_fraction <= 0.5:
            raise ValueError("size_run_edge_fraction must be in (0, 0.5]")
        if not 0 < self.heavy_discount_percent <= 100:
            raise ValueError("heavy_discount_percent must be in (0, 100]")
        if self.overstock_age_days < 0:
            raise ValueError("overstock_age_days must be non-negative")
        for name in (
            "score_best_seller_stockout", "score_broken_size_run",
            "score_prominent_unavailable", "score_thin_page",
            "score_heavy_discount", "score_insufficient_evidence",
        ):
            if not 0 <= getattr(self, name) <= 100:
                raise ValueError(f"{name} must be between 0 and 100")


DEFAULT_CONFIG = AnalyzerConfig()
