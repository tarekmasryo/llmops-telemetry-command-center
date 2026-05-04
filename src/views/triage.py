from __future__ import annotations

from typing import Any

import pandas as pd
import streamlit as st

from src.charts import baseline_comparison, triage_curve, triage_performance_curve
from src.metrics import build_triage_queue, safe_money
from src.policy import simulate_threshold_queue
from src.ui import dataframe, metric_card, plotly, section_card


class TriageViewMixin:
    """Render helpers for one focused dashboard surface."""

    def _render_triage_simulator_tab(self) -> None:
        st.subheader("Triage threshold simulator")
        st.caption(
            "Explore the notebook triage curve as an operating trade-off: threshold, review load, cost, precision, recall, and confusion-matrix effects."
        )
        sim_row = simulate_threshold_queue(self.bundle.triage_curve, self.settings.triage_threshold)
        self._render_triage_threshold_metrics(sim_row)
        c1, c2 = st.columns([1.2, 1])
        with c1:
            plotly(
                triage_curve(self.bundle.triage_curve, self.settings.triage_threshold),
                key="triage_threshold_cost_curve",
            )
        with c2:
            plotly(
                triage_performance_curve(self.bundle.triage_curve, self.settings.triage_threshold),
                key="triage_threshold_performance_curve",
            )
        self._render_confusion_metrics(sim_row)
        st.markdown("#### Baseline comparison")
        plotly(baseline_comparison(self.bundle.triage_baselines), key="triage_baseline_comparison")
        dataframe(self._formatted_triage_baselines(), height=220)
        section_card(
            "Interpretation",
            "When the selected threshold behaves like review-all, use the queue for prioritization while validating an independent window before adopting it as a workload-reduction setting.",
        )

    def _render_triage_threshold_metrics(self, sim_row: dict[str, Any]) -> None:
        t1, t2, t3, t4, t5 = st.columns(5)
        with t1:
            metric_card(
                "Threshold",
                f"{float(sim_row.get('threshold', self.settings.triage_threshold)):.2f}",
                "Nearest artifact threshold.",
                "#a78bfa",
            )
        with t2:
            metric_card(
                "Expected cost",
                safe_money(sim_row.get("expected_cost", 0), 0),
                "Review + false-negative cost.",
                "#fb7185",
            )
        with t3:
            metric_card(
                "Review share",
                self.pct_text(sim_row.get("review_share", 0)),
                "Operational review load.",
                "#fbbf24",
            )
        with t4:
            metric_card(
                "Precision", self.pct_text(sim_row.get("precision", 0)), "Reviewed rows that fail.", "#38bdf8"
            )
        with t5:
            metric_card("Recall", self.pct_text(sim_row.get("recall", 0)), "Failure capture rate.", "#34d399")

    @staticmethod
    def _render_confusion_metrics(sim_row: dict[str, Any]) -> None:
        st.markdown("#### Confusion matrix at selected threshold")
        cm1, cm2, cm3, cm4 = st.columns(4)
        with cm1:
            metric_card(
                "TP", f"{int(sim_row.get('tp', 0)):,}", "Failures correctly sent to review.", "#34d399"
            )
        with cm2:
            metric_card(
                "FP", f"{int(sim_row.get('fp', 0)):,}", "Extra reviews created by the threshold.", "#fbbf24"
            )
        with cm3:
            metric_card("FN", f"{int(sim_row.get('fn', 0)):,}", "Failures missed by triage.", "#fb7185")
        with cm4:
            metric_card("TN", f"{int(sim_row.get('tn', 0)):,}", "Rows correctly left unreviewed.", "#38bdf8")

    def _formatted_triage_baselines(self) -> pd.DataFrame:
        baseline_view = self.bundle.triage_baselines.copy()
        for col in ["review_share", "precision", "recall"]:
            if col in baseline_view.columns:
                baseline_view[col] = baseline_view[col].map(lambda x: f"{float(x):.1%}")
        if "expected_cost" in baseline_view.columns:
            baseline_view["expected_cost"] = baseline_view["expected_cost"].map(lambda x: f"${float(x):,.0f}")
        return baseline_view

    def _render_review_queue_tab(self) -> None:
        st.subheader("Triage action queue")
        q = build_triage_queue(self.bundle.triage_actions, self.filtered, sla_ms=self.settings.sla_ms)
        if q.empty:
            st.info("No triage action preview artifact found for the current filters.")
            return
        q = q[q["action_review"].astype(bool)] if "action_review" in q.columns else q
        min_prob = st.slider("Minimum predicted failure probability", 0.0, 1.0, 0.10, 0.01)
        priority_filter = st.multiselect(
            "Priority", sorted(q["priority"].dropna().unique().tolist()), default=[]
        )
        qv = q[q["proba_failure"] >= min_prob].copy()
        if priority_filter:
            qv = qv[qv["priority"].isin(priority_filter)]
        st.caption(
            "Queue probabilities/actions come from the notebook triage artifact and are subset to the current sidebar filters when matching interaction IDs are available. Use it as an artifact-backed review queue for analyst handoff."
        )
        show_cols = [
            c
            for c in [
                "priority",
                "priority_score",
                "reason",
                "interaction_id",
                "timestamp_utc",
                "use_case",
                "model_provider",
                "model_name",
                "proba_failure",
                "latency_ms",
                "cost_usd",
            ]
            if c in qv.columns
        ]
        dataframe(qv[show_cols].head(250), height=420)
        csv = qv[show_cols].to_csv(index=False).encode("utf-8")
        st.download_button("Download filtered queue CSV", csv, "triage_queue_filtered.csv", "text/csv")
        st.markdown("#### Queue explanation")
        st.write(
            "- **Critical/high** rows combine high predicted failure probability with latency or cost pressure."
        )
        st.write(
            "- Current notebook threshold is conservative; this queue prioritizes review rows while an independent validation window confirms workload-reduction impact."
        )
