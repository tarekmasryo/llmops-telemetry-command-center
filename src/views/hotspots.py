from __future__ import annotations

import pandas as pd
import streamlit as st

from src.charts import cost_by_dimension, hotspot_scatter
from src.metrics import compute_kpis, model_hotspots, safe_money
from src.ui import metric_card, plotly


class HotspotsViewMixin:
    """Render helpers for one focused dashboard surface."""

    def _render_hotspots_tab(self) -> None:
        st.subheader("Provider / model hotspot drilldown")
        hotspots = model_hotspots(
            self.filtered,
            sla_ms=self.settings.sla_ms,
            failure_cost=self.settings.failure_cost,
            sla_penalty=self.settings.sla_penalty,
        )
        plotly(
            hotspot_scatter(hotspots, sla_ms=self.settings.sla_ms, fail_budget=self.settings.fail_budget),
            key="hotspots_scatter",
        )
        if not hotspots.empty:
            models = (hotspots["model_provider"] + " / " + hotspots["model_name"]).tolist()
            selected = st.selectbox("Select a provider/model slice", models)
            provider, model = [part.strip() for part in selected.split(" / ", 1)]
            slice_df = self.filtered[
                (self.filtered["model_provider"].astype(str) == provider)
                & (self.filtered["model_name"].astype(str) == model)
            ]
            self._render_slice_metrics(selected, slice_df)
            self._render_slice_reasons(slice_df)
        st.subheader("Cost concentration")
        cost_dim = st.radio(
            "Group cost by", ["model_provider", "model_name", "use_case", "account_tier"], horizontal=True
        )
        plotly(cost_by_dimension(self.filtered, cost_dim), key=f"hotspots_cost_{cost_dim}")

    def _render_slice_metrics(self, selected: str, slice_df: pd.DataFrame) -> None:
        sk = compute_kpis(slice_df, sla_ms=self.settings.sla_ms, fail_budget=self.settings.fail_budget)
        a, b, c, d = st.columns(4)
        with a:
            metric_card("Slice requests", f"{sk['requests']:,}", selected, "#38bdf8")
        with b:
            metric_card(
                "Slice failure",
                self.pct_text(sk["failure_rate"]),
                f"vs budget {self.pct_text(self.settings.fail_budget)}",
                "#fb7185",
            )
        with c:
            metric_card("Slice p95", f"{sk['p95_latency']:.0f}ms", f"SLA {self.settings.sla_ms}ms", "#fbbf24")
        with d:
            metric_card(
                "Slice cost",
                safe_money(sk["total_cost"], 0),
                f"avg {safe_money(sk['avg_cost'], 3)}",
                "#34d399",
            )

    def _render_slice_reasons(self, slice_df: pd.DataFrame) -> None:
        sk = compute_kpis(slice_df, sla_ms=self.settings.sla_ms, fail_budget=self.settings.fail_budget)
        st.markdown("#### Why this slice matters")
        reasons = []
        if sk["failure_rate"] > self.settings.fail_budget:
            reasons.append(
                f"Failure rate is {self.pct_text(sk['failure_rate'])}, above the configured budget of {self.pct_text(self.settings.fail_budget)}."
            )
        if sk["p95_latency"] > self.settings.sla_ms:
            reasons.append(
                f"p95 latency is {sk['p95_latency']:.0f}ms, above SLA target {self.settings.sla_ms}ms."
            )
        if not reasons:
            reasons.append("This slice is currently within the configured failure and latency guardrails.")
        for reason in reasons:
            st.write("- " + reason)
