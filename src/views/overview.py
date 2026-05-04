from __future__ import annotations

import streamlit as st

from src.metrics import safe_money
from src.ui import metric_card


class OverviewViewMixin:
    """Render helpers for one focused dashboard surface."""

    def _render_metric_strip(self) -> None:
        c1, c2, c3, c4, c5 = st.columns([1.05, 1, 1, 1, 1])
        score_color = (
            "#34d399"
            if self.kpis["health_score"] >= 75
            else "#fbbf24"
            if self.kpis["health_score"] >= 45
            else "#fb7185"
        )
        with c1:
            metric_card(
                "Operating health",
                f"{self.kpis['health_score']:.1f}/100",
                "Composite score from failure budget, SLA pressure, and p95 latency.",
                score_color,
            )
        with c2:
            metric_card(
                "Requests", f"{int(self.kpis['requests']):,}", "Filtered telemetry volume.", "#38bdf8"
            )
        with c3:
            metric_card(
                "Failure rate",
                self.pct_text(self.kpis["failure_rate"]),
                f"Budget multiple: {self.kpis['fail_budget_multiple']:.1f}×",
                "#fb7185",
            )
        with c4:
            metric_card(
                "p95 latency",
                f"{self.kpis['p95_latency']:.0f}ms",
                f"SLA target: {self.settings.sla_ms}ms",
                "#fbbf24",
            )
        with c5:
            metric_card(
                "Total cost",
                safe_money(self.kpis["total_cost"], 0),
                f"Avg {safe_money(self.kpis['avg_cost'], 3)} / request",
                "#34d399",
            )
