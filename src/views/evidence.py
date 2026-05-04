from __future__ import annotations

import pandas as pd
import streamlit as st

from src.charts import drift_bars
from src.metrics import safe_money
from src.ui import dataframe, key_value_grid, plotly


class EvidenceViewMixin:
    """Render helpers for one focused dashboard surface."""

    def _render_evidence_tab(self) -> None:
        st.subheader("Drift and evidence layer")
        d1, d2 = st.columns([1.15, 1])
        with d1:
            plotly(drift_bars(self.bundle.drift_report), key="evidence_drift_bars")
        with d2:
            self._render_decision_artifact_summary()
        self._render_artifact_browser()

    def _render_decision_artifact_summary(self) -> None:
        da = self.bundle.decision_artifact
        status = str(da.get("status", da.get("decision_status", "review_required")))
        issues = da.get("issues", []) or da.get("quality", {}).get("issues", []) or []
        recommendations = (
            da.get("recommendations", []) or da.get("decision", {}).get("recommendations", []) or []
        )
        routing_status = str(
            self.bundle.routing_summary.get("routing_status", pd.Series(["unknown"])).iloc[0]
        )
        triage_mode = str(self.bundle.triage_policy.get("operating_mode", "unknown"))
        st.markdown("#### Decision artifact")
        key_value_grid(
            [
                ("Status", status),
                ("Routing", routing_status),
                ("Triage", triage_mode),
                ("Issues", str(len(issues))),
            ]
        )
        evidence_summary = pd.DataFrame(
            [
                {
                    "check": "Routing",
                    "current_state": routing_status,
                    "operator_note": "Held-out backtest is the rollout source of truth.",
                },
                {
                    "check": "Triage",
                    "current_state": triage_mode,
                    "operator_note": "Review workload remains high if the threshold behaves like review-all.",
                },
                {
                    "check": "Filtered health",
                    "current_state": f"{self.kpis['health_score']:.1f}/100",
                    "operator_note": f"p95 latency {self.kpis['p95_latency']:.0f}ms vs SLA {self.settings.sla_ms}ms; cost {safe_money(self.kpis['total_cost'], 0)}.",
                },
            ]
        )
        dataframe(evidence_summary, height=180)
        with st.expander("View raw decision artifact JSON", expanded=False):
            st.json(
                {
                    "status": status,
                    "issues": issues,
                    "recommendations": recommendations,
                    "routing_status": routing_status,
                    "triage_mode": triage_mode,
                },
                expanded=False,
            )

    def _render_artifact_browser(self) -> None:
        st.markdown("#### Artifact files")
        artifact_name = st.selectbox(
            "Choose artifact",
            [
                "routing_backtest_summary.csv",
                "routing_policy_use_case.csv",
                "drift_report.csv",
                "triage_threshold_policy.json",
                "triage_baseline_comparison.csv",
                "decision_artifact.json",
            ],
        )
        if artifact_name.endswith(".json"):
            self._render_json_artifact(artifact_name)
            return
        artifact_map = {
            "routing_backtest_summary.csv": self.bundle.routing_summary,
            "routing_policy_use_case.csv": self.bundle.routing_policy,
            "drift_report.csv": self.bundle.drift_report,
            "triage_baseline_comparison.csv": self.bundle.triage_baselines,
        }
        dataframe(artifact_map[artifact_name], height=320)

    def _render_json_artifact(self, artifact_name: str) -> None:
        payload = (
            self.bundle.triage_policy
            if artifact_name == "triage_threshold_policy.json"
            else self.bundle.decision_artifact
        )
        if artifact_name == "triage_threshold_policy.json":
            metrics = payload.get("metrics", {}) if isinstance(payload.get("metrics"), dict) else {}
            selected_metrics = (
                payload.get("selected_policy_metrics", {})
                if isinstance(payload.get("selected_policy_metrics"), dict)
                else {}
            )
            summary_rows = [
                {"field": "threshold", "value": payload.get("threshold", "unknown")},
                {"field": "operating_mode", "value": payload.get("operating_mode", "unknown")},
                {"field": "model_auc", "value": metrics.get("roc_auc", "unknown")},
                {"field": "average_precision", "value": metrics.get("avg_precision", "unknown")},
                {"field": "review_share", "value": selected_metrics.get("review_share", "unknown")},
                {"field": "expected_cost", "value": selected_metrics.get("expected_cost", "unknown")},
            ]
        else:
            summary_rows = [
                {
                    "field": "status",
                    "value": payload.get("status", payload.get("decision_status", "unknown")),
                },
                {
                    "field": "issues",
                    "value": len(payload.get("issues", []) or payload.get("quality", {}).get("issues", [])),
                },
                {
                    "field": "recommendations",
                    "value": len(
                        payload.get("recommendations", [])
                        or payload.get("decision", {}).get("recommendations", [])
                    ),
                },
            ]
        dataframe(pd.DataFrame(summary_rows), height=170)
        with st.expander("Raw artifact JSON", expanded=False):
            st.json(payload, expanded=False)
