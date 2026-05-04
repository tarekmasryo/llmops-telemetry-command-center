from __future__ import annotations

import pandas as pd
import streamlit as st

from src.data import DataBundle
from src.metrics import compute_kpis, filter_interactions, safe_pct
from src.models import DashboardSettings, RoutingTruth
from src.ui import artifact_note, hero
from src.views import (
    CommandViewMixin,
    DataExplorerViewMixin,
    EvidenceViewMixin,
    HotspotsViewMixin,
    OverviewViewMixin,
    PolicyLabViewMixin,
    TriageViewMixin,
)


class DashboardApp(
    OverviewViewMixin,
    CommandViewMixin,
    HotspotsViewMixin,
    PolicyLabViewMixin,
    TriageViewMixin,
    EvidenceViewMixin,
    DataExplorerViewMixin,
):
    """Thin Streamlit coordinator that composes focused view mixins."""

    def __init__(self, bundle: DataBundle) -> None:
        self.bundle = bundle
        self.settings = self._build_sidebar()
        self.filtered = filter_interactions(
            self.bundle.interactions,
            providers=self.settings.providers,
            models=self.settings.models,
            use_cases=self.settings.use_cases,
            channels=self.settings.channels,
            tiers=self.settings.tiers,
            regions=self.settings.regions,
            date_range=self.settings.date_range,
        )
        self.kpis = compute_kpis(
            self.filtered,
            sla_ms=self.settings.sla_ms,
            fail_budget=self.settings.fail_budget,
        )
        self.truth = self._routing_truth(self.bundle.routing_summary)

    def render(self) -> None:
        self._render_header()
        if self.filtered.empty:
            self._render_empty_state()
            return
        artifact_note()
        self._render_metric_strip()
        st.markdown("---")
        self._render_tabs()

    @staticmethod
    def unique_options(df: pd.DataFrame, col: str) -> list[str]:
        if col not in df.columns:
            return []
        return sorted([str(x) for x in df[col].dropna().unique().tolist()])

    @staticmethod
    def pct_text(value: float | int | None) -> str:
        return safe_pct(value, digits=1)

    @staticmethod
    def _routing_truth(summary_df: pd.DataFrame) -> RoutingTruth:
        if summary_df.empty:
            return RoutingTruth(
                status="missing",
                recommendation="review_artifact_missing",
                delta=0.0,
                window="held_out_window",
                baseline_unit_cost=0.0,
                policy_unit_cost=0.0,
            )
        row = summary_df.iloc[0].to_dict()
        return RoutingTruth(
            status=str(row.get("routing_status", row.get("status", "unknown"))),
            recommendation=str(row.get("routing_recommendation", "review_required")),
            delta=float(row.get("unit_cost_delta_vs_baseline", row.get("unit_cost_delta", 0.0)) or 0.0),
            window=str(row.get("evaluation_window", "held_out_window")),
            baseline_unit_cost=float(row.get("baseline_expected_unit_cost", 0.0) or 0.0),
            policy_unit_cost=float(row.get("policy_expected_unit_cost", 0.0) or 0.0),
        )

    def _build_sidebar(self) -> DashboardSettings:
        df = self.bundle.interactions
        triage_policy = self.bundle.triage_policy
        st.sidebar.markdown("### 🛰️ Command Filters")
        st.sidebar.caption(
            "Filters update live views. Notebook artifacts keep their original evaluation scope."
        )
        date_range = self._date_filter(df)
        providers = st.sidebar.multiselect("Providers", self.unique_options(df, "model_provider"), default=[])
        models = st.sidebar.multiselect("Models", self.unique_options(df, "model_name"), default=[])
        use_cases = st.sidebar.multiselect("Use cases", self.unique_options(df, "use_case"), default=[])
        channels = st.sidebar.multiselect("Channels", self.unique_options(df, "channel"), default=[])
        tiers = st.sidebar.multiselect("Account tiers", self.unique_options(df, "account_tier"), default=[])
        regions = st.sidebar.multiselect("Regions", self.unique_options(df, "region"), default=[])
        st.sidebar.markdown("---")
        st.sidebar.markdown("### ⚙️ Operator Knobs")
        economics = triage_policy.get("economics", {}) if isinstance(triage_policy, dict) else {}
        review_cost = float(economics.get("review_cost", 2.0))
        st.sidebar.caption(
            f"Artifact review cost: ${review_cost:.2f}. Triage economics come from notebook-generated artifacts; "
            "sidebar filters do not recompute held-out artifact verdicts."
        )
        return DashboardSettings(
            date_range=date_range,
            providers=tuple(providers),
            models=tuple(models),
            use_cases=tuple(use_cases),
            channels=tuple(channels),
            tiers=tuple(tiers),
            regions=tuple(regions),
            sla_ms=st.sidebar.slider("SLA target (ms)", 800, 6000, 2200, 100),
            fail_budget=st.sidebar.slider("Failure budget", 0.005, 0.30, 0.02, 0.005, format="%.3f"),
            failure_cost=st.sidebar.slider(
                "Failure business cost ($)",
                1.0,
                120.0,
                float(economics.get("fn_cost", 40.0)),
                1.0,
            ),
            sla_penalty=st.sidebar.slider("SLA breach penalty ($)", 0.0, 30.0, 5.0, 0.5),
            max_fail_rate=st.sidebar.slider("Routing max failure rate", 0.01, 0.40, 0.12, 0.01),
            min_requests=st.sidebar.slider("Minimum requests per slice", 10, 300, 60, 10),
            triage_threshold=st.sidebar.slider(
                "Triage threshold",
                0.01,
                0.95,
                float(triage_policy.get("threshold", 0.10)),
                0.01,
            ),
        )

    @staticmethod
    def _date_filter(df: pd.DataFrame) -> tuple[pd.Timestamp, pd.Timestamp] | None:
        if "timestamp_utc" not in df.columns or not df["timestamp_utc"].notna().any():
            return None
        min_date = df["timestamp_utc"].min().date()
        max_date = df["timestamp_utc"].max().date()
        selected_dates = st.sidebar.date_input(
            "Time window",
            value=(min_date, max_date),
            min_value=min_date,
            max_value=max_date,
        )
        if not isinstance(selected_dates, tuple) or len(selected_dates) != 2:
            return None
        return (
            pd.Timestamp(selected_dates[0], tz="UTC"),
            pd.Timestamp(selected_dates[1], tz="UTC") + pd.Timedelta(days=1) - pd.Timedelta(seconds=1),
        )

    def _render_header(self) -> None:
        hero(
            "LLMOps Telemetry Command Center",
            "Operational view for reliability, latency, cost, routing, drift, and review workload across LLM telemetry.",
            status=f"{int(self.kpis['requests']):,} filtered rows · routing: {self.truth.status.replace('_', ' ')}",
        )

    @staticmethod
    def _render_empty_state() -> None:
        st.error("No rows matched the current filters. Clear one or more sidebar filters to continue.")

    def _render_tabs(self) -> None:
        tabs = st.tabs(
            [
                "01 · Command",
                "02 · Hotspots",
                "03 · Policy Lab",
                "04 · Triage Simulator",
                "05 · Review Queue",
                "06 · Evidence",
                "07 · Data Explorer",
            ]
        )
        with tabs[0]:
            self._render_command_tab()
        with tabs[1]:
            self._render_hotspots_tab()
        with tabs[2]:
            self._render_policy_tab()
        with tabs[3]:
            self._render_triage_simulator_tab()
        with tabs[4]:
            self._render_review_queue_tab()
        with tabs[5]:
            self._render_evidence_tab()
        with tabs[6]:
            self._render_data_explorer_tab()
