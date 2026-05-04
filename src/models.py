from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import pandas as pd


@dataclass(frozen=True)
class DashboardSettings:
    """User-selected controls that drive live dashboard views."""

    date_range: tuple[pd.Timestamp, pd.Timestamp] | None
    providers: tuple[str, ...]
    models: tuple[str, ...]
    use_cases: tuple[str, ...]
    channels: tuple[str, ...]
    tiers: tuple[str, ...]
    regions: tuple[str, ...]
    sla_ms: int
    fail_budget: float
    failure_cost: float
    sla_penalty: float
    max_fail_rate: float
    min_requests: int
    triage_threshold: float


@dataclass(frozen=True)
class RoutingTruth:
    """Held-out routing verdict loaded from the notebook artifact layer."""

    status: str
    recommendation: str
    delta: float
    window: str
    baseline_unit_cost: float
    policy_unit_cost: float
