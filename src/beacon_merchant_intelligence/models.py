"""Small typed domain models; ``None`` means the value was not observed."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from enum import Enum


class VariantAvailability(str, Enum):
    AVAILABLE = "available"
    UNAVAILABLE = "unavailable"
    UNKNOWN = "unknown"


class Assessment(str, Enum):
    SIGNAL = "signal"
    INSUFFICIENT_EVIDENCE = "insufficient_evidence"


class EvidenceSufficiency(str, Enum):
    STRONG = "strong"
    LIMITED = "limited"
    INSUFFICIENT = "insufficient"


@dataclass(frozen=True, slots=True)
class ProductVariant:
    name: str | None
    availability: VariantAvailability = VariantAvailability.UNKNOWN


@dataclass(frozen=True, slots=True)
class Product:
    product_id: str | None = None
    title: str | None = None
    url: str | None = None
    collection_position: int | None = None
    # Set only when a collector has identified a product option as sizing.
    # Numeric variant labels alone do not establish that they are sizes.
    size_option: str | None = None
    current_price: Decimal | None = None
    original_price: Decimal | None = None
    variants: tuple[ProductVariant, ...] = ()
    description_present: bool | None = None
    image_count: int | None = None
    review_count: int | None = None
    observation_timestamp: datetime | None = None
    source: str | None = None
    # These are optional evidence fields. They must be sourced, never inferred
    # from collection order or a discount.
    sales_rank: int | None = None
    sales_rank_source: str | None = None
    inventory_age_days: int | None = None
    inventory_history_source: str | None = None


@dataclass(frozen=True, slots=True)
class Finding:
    product_id: str | None
    product_title: str | None
    signal: str
    assessment: Assessment
    evidence: tuple[str, ...]
    rationale: str
    evidence_sufficiency: EvidenceSufficiency
    recommended_action: str
    heuristic_score: int

    def __post_init__(self) -> None:
        if not 0 <= self.heuristic_score <= 100:
            raise ValueError("heuristic_score must be between 0 and 100")
        if not self.evidence:
            raise ValueError("every finding must include evidence or a missing-evidence statement")
        if not self.rationale.strip() or not self.recommended_action.strip():
            raise ValueError("every finding must include rationale and a recommended action")
