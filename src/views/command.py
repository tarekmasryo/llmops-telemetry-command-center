from __future__ import annotations

import pandas as pd
import streamlit as st

from src.charts import failure_type_bar, line_operations
from src.metrics import daily_operational_series, failure_breakdown, incident_board, risk_slices
from src.ui import alert_card, dataframe, plotly


class CommandViewMixin:
    """Render helpers for one focused dashboard surface."""

    def _render_command_tab(self) -> None:
        left, right = st.columns([1.25, 1])
        with left:
            st.subheader("Current operating state")
            daily = daily_operational_series(self.filtered, sla_ms=self.settings.sla_ms)
            plotly(line_operations(daily), key="command_daily_operations")
            st.subheader("Failure anatomy")
            plotly(failure_type_bar(failure_breakdown(self.filtered)), key="command_failure_breakdown")
        with right:
            st.subheader("Incident board")
            incidents = incident_board(
                self.filtered,
                sla_ms=self.settings.sla_ms,
                fail_budget=self.settings.fail_budget,
            )
            for _, row in incidents.iterrows():
                alert_card(
                    str(row["severity"]),
                    str(row["signal"]),
                    str(row["why"]),
                    str(row["recommended_action"]),
                )
            st.subheader("Operations checklist")
            dataframe(self._operations_checklist(), height=180)
        st.subheader("Live risk slices")
        slices = risk_slices(
            self.filtered,
            sla_ms=self.settings.sla_ms,
            min_requests=self.settings.min_requests,
        )
        if slices.empty:
            st.info("No risk slices meet the current minimum request threshold.")
            return
        view = (
            slices[
                [
                    "severity",
                    "use_case",
                    "model_provider",
                    "model_name",
                    "requests",
                    "failure_rate",
                    "sla_breach_rate",
                    "p95_latency",
                    "avg_cost",
                    "severity_score",
                ]
            ]
            .head(20)
            .copy()
        )
        view["failure_rate"] = view["failure_rate"].map(lambda x: f"{x:.1%}")
        view["sla_breach_rate"] = view["sla_breach_rate"].map(lambda x: f"{x:.1%}")
        view["p95_latency"] = view["p95_latency"].map(lambda x: f"{x:.0f}ms")
        view["avg_cost"] = view["avg_cost"].map(lambda x: f"${x:.4f}")
        dataframe(view, height=360)

    def _operations_checklist(self) -> pd.DataFrame:
        routing_status = self.truth.status.replace("_", " ").lower()
        routing_recommendation = self.truth.recommendation.replace("_", " ").lower()
        should_hold = any(
            token in f"{routing_status} {routing_recommendation}"
            for token in ["failed", "reject", "do not roll out", "hold"]
        )
        routing_action = "Hold routing rollout" if should_hold else "Review routing rollout readiness"
        routing_reason = (
            "Held-out routing artifact does not support rollout under the current evidence window."
            if should_hold
            else "Held-out routing artifact does not explicitly reject rollout; verify acceptance criteria before release."
        )
        return pd.DataFrame(
            [
                {
                    "priority": 1,
                    "action": routing_action,
                    "reason": routing_reason,
                    "owner": "Platform / ML Ops",
                },
                {
                    "priority": 2,
                    "action": "Investigate highest-risk slice",
                    "reason": "Use Hotspots to isolate provider/model/use-case combinations above failure or SLA budget.",
                    "owner": "Model Ops",
                },
                {
                    "priority": 3,
                    "action": "Review triage threshold",
                    "reason": "Validate review-load reduction on an independent window before changing operating policy.",
                    "owner": "Operations",
                },
            ]
        )
