from __future__ import annotations

import streamlit as st

from src.policy import simulate_routing_policy
from src.ui import dataframe, metric_card


class PolicyLabViewMixin:
    """Render helpers for one focused dashboard surface."""

    def _render_policy_tab(self) -> None:
        st.subheader("Routing decision lab")
        st.caption(
            "Held-out notebook artifacts are the audit source of truth. The live simulator below supports filtered operator review and may surface candidates that differ from the held-out verdict."
        )
        self._render_held_out_routing_summary()
        st.warning(
            "Source-of-truth rule: keep `routing_backtest_summary.csv` as the held-out audit artifact. "
            "If filtered scenarios improve cost, treat them as candidates for shadow validation before rollout."
        )
        self._render_live_policy_review()
        st.markdown("#### Held-out routing artifact details")
        dataframe(self.bundle.routing_summary.copy(), height=170)
        st.info(
            "Triage threshold analysis is separated into Tab 04. Routing, triage, and drift artifacts keep their original notebook evaluation scope even when sidebar filters change live dashboard views."
        )

    def _render_held_out_routing_summary(self) -> None:
        h1, h2, h3, h4 = st.columns(4)
        with h1:
            metric_card(
                "Held-out verdict",
                self.truth.status.replace("_", " "),
                self.truth.recommendation,
                "#34d399" if self.truth.status == "approved" else "#fb7185",
            )
        with h2:
            metric_card("Held-out window", self.truth.window, "Notebook evaluation scope.", "#38bdf8")
        with h3:
            metric_card(
                "Baseline unit cost", f"${self.truth.baseline_unit_cost:.2f}", "Held-out artifact.", "#94a3b8"
            )
        with h4:
            metric_card(
                "Policy delta",
                f"${self.truth.delta:.2f}",
                "Positive means worse than baseline.",
                "#34d399" if self.truth.delta < 0 else "#fb7185",
            )

    def _render_live_policy_review(self) -> None:
        st.markdown("#### Live filtered scenario review")
        policy_df, policy_summary = simulate_routing_policy(
            self.filtered,
            sla_ms=self.settings.sla_ms,
            failure_cost=self.settings.failure_cost,
            sla_penalty=self.settings.sla_penalty,
            max_fail_rate=self.settings.max_fail_rate,
            min_requests=self.settings.min_requests,
        )
        p1, p2, p3, p4 = st.columns(4)
        status = str(policy_summary.get("status", "unknown"))
        with p1:
            metric_card(
                "Scenario status",
                status.replace("_", " "),
                "Exploratory scenario based on current filters.",
                "#34d399" if "improves" in status else "#fb7185",
            )
        with p2:
            metric_card(
                "Scenario baseline",
                f"${float(policy_summary.get('baseline_expected_unit_cost', 0)):.2f}",
                "Observed filtered-window cost.",
                "#38bdf8",
            )
        with p3:
            metric_card(
                "Scenario policy",
                f"${float(policy_summary.get('policy_expected_unit_cost', 0)):.2f}",
                "Weighted candidate cost.",
                "#a78bfa",
            )
        with p4:
            metric_card(
                "Scenario delta",
                f"${float(policy_summary.get('unit_cost_delta', 0)):.2f}",
                "Negative is better.",
                "#34d399" if float(policy_summary.get("unit_cost_delta", 0)) < 0 else "#fb7185",
            )
        if policy_df.empty:
            st.info("No policy candidate could be produced with the current filters.")
            return
        show = policy_df[
            [
                "use_case",
                "model_provider",
                "model_name",
                "requests",
                "fail_rate",
                "p95_latency",
                "sla_breach_rate",
                "avg_cost",
                "expected_unit_cost",
                "policy_mode",
            ]
        ].copy()
        show["fail_rate"] = show["fail_rate"].map(lambda x: f"{x:.1%}")
        show["sla_breach_rate"] = show["sla_breach_rate"].map(lambda x: f"{x:.1%}")
        show["p95_latency"] = show["p95_latency"].map(lambda x: f"{x:.0f}ms")
        show["avg_cost"] = show["avg_cost"].map(lambda x: f"${x:.4f}")
        show["expected_unit_cost"] = show["expected_unit_cost"].map(lambda x: f"${x:.2f}")
        dataframe(show, height=320)
