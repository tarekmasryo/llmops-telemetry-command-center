from __future__ import annotations

import pandas as pd
import streamlit as st

from src.ui import dataframe


class DataExplorerViewMixin:
    """Render helpers for one focused dashboard surface."""

    def _render_data_explorer_tab(self) -> None:
        st.subheader("Data explorer")
        st.caption(
            "Use this for inspection. Text columns are masked by default so exported views avoid exposing request or response text."
        )
        mask_text = st.toggle("Mask request/response text", value=True)
        search = st.text_input("Search interaction/use case/model/provider", "")
        explorer = self._search_filtered_rows(search)
        selected_cols = self._column_picker(explorer)
        display_df = explorer[selected_cols].copy() if selected_cols else explorer.copy()
        if mask_text:
            self._mask_text_columns(display_df)
        dataframe(display_df.head(1000), height=430)
        st.download_button(
            "Download filtered rows CSV",
            display_df.to_csv(index=False).encode("utf-8"),
            "filtered_interactions.csv",
            "text/csv",
        )
        self._render_instruction_template_analysis()
        self._render_user_cohort_analysis()
        self._render_row_detail(explorer, mask_text)

    def _search_filtered_rows(self, search: str) -> pd.DataFrame:
        explorer = self.filtered.copy()
        if not search:
            return explorer
        text_cols = [
            c
            for c in [
                "interaction_id",
                "session_id",
                "user_id",
                "use_case",
                "model_provider",
                "model_name",
                "failure_type",
            ]
            if c in explorer.columns
        ]
        haystack = explorer[text_cols].astype(str).agg(" ".join, axis=1).str.lower()
        return explorer[haystack.str.contains(search.lower(), na=False, regex=False)]

    @staticmethod
    def _column_picker(explorer: pd.DataFrame) -> list[str]:
        default_cols = [
            "interaction_id",
            "timestamp_utc",
            "use_case",
            "model_provider",
            "model_name",
            "is_failure",
            "failure_type",
            "latency_ms",
            "cost_usd",
            "total_tokens",
            "response_quality_score",
            "final_resolution_state",
            "business_impact_tag",
        ]
        available = explorer.columns.tolist()
        return st.multiselect("Columns", available, default=[c for c in default_cols if c in available])

    @staticmethod
    def _mask_text_columns(df: pd.DataFrame) -> None:
        for col in ["request_text", "response_text_snippet", "instruction_text"]:
            if col in df.columns:
                df[col] = "[masked in dashboard]"

    def _render_instruction_template_analysis(self) -> None:
        st.markdown("#### Instruction template analysis")
        template_col = (
            "instruction_template"
            if "instruction_template" in self.filtered.columns
            else "request_text_template"
        )
        if template_col not in self.filtered.columns:
            st.info("No instruction template column was found in the filtered telemetry.")
            return
        tmp_template = self.filtered.copy()
        tmp_template["sla_breach"] = (
            pd.to_numeric(tmp_template["latency_ms"], errors="coerce") > self.settings.sla_ms
        )
        template_view = (
            tmp_template.groupby(template_col, dropna=False)
            .agg(
                requests=("interaction_id", "count"),
                failure_rate=("is_failure", "mean"),
                sla_breach_rate=("sla_breach", "mean"),
                p95_latency=("latency_ms", lambda x: pd.to_numeric(x, errors="coerce").quantile(0.95)),
                avg_cost=("cost_usd", "mean"),
            )
            .reset_index()
            .sort_values(["failure_rate", "requests"], ascending=[False, False])
            .head(30)
        )
        template_view["failure_rate"] = template_view["failure_rate"].map(lambda x: f"{float(x):.1%}")
        template_view["sla_breach_rate"] = template_view["sla_breach_rate"].map(lambda x: f"{float(x):.1%}")
        template_view["p95_latency"] = template_view["p95_latency"].map(lambda x: f"{float(x):.0f}ms")
        template_view["avg_cost"] = template_view["avg_cost"].map(lambda x: f"${float(x):.4f}")
        dataframe(template_view, height=280)

    def _render_user_cohort_analysis(self) -> None:
        st.markdown("#### User cohort analysis")
        user_group = st.radio(
            "Group users by",
            ["dominant_account_tier", "primary_use_case", "dominant_region", "high_risk_user_flag"],
            horizontal=True,
        )
        if user_group not in self.bundle.users.columns:
            st.info("Selected user cohort column was not found.")
            return
        users_view = (
            self.bundle.users.groupby(user_group, dropna=False)
            .agg(
                users=("user_id", "count"),
                total_requests=("total_requests", "sum"),
                avg_failure_rate=("overall_failure_rate", "mean"),
                avg_requests_per_user=("total_requests", "mean"),
                total_cost=("total_cost_usd", "sum"),
            )
            .reset_index()
            .sort_values("total_requests", ascending=False)
        )
        users_view["avg_failure_rate"] = users_view["avg_failure_rate"].map(lambda x: f"{float(x):.1%}")
        users_view["avg_requests_per_user"] = users_view["avg_requests_per_user"].map(
            lambda x: f"{float(x):.1f}"
        )
        users_view["total_cost"] = users_view["total_cost"].map(lambda x: f"${float(x):,.0f}")
        dataframe(users_view, height=260)

    def _render_row_detail(self, explorer: pd.DataFrame, mask_text: bool) -> None:
        st.markdown("#### Row detail")
        if explorer.empty or "interaction_id" not in explorer.columns:
            return
        selected_id = st.selectbox(
            "Select interaction", explorer["interaction_id"].astype(str).head(1000).tolist()
        )
        row = explorer[explorer["interaction_id"].astype(str).eq(selected_id)].head(1)
        if row.empty:
            return
        record = row.iloc[0].to_dict()
        if mask_text:
            for col in ["request_text", "response_text_snippet", "instruction_text"]:
                if col in record:
                    record[col] = "[masked in dashboard]"
        with st.expander("View selected row JSON", expanded=False):
            st.json(record, expanded=False)
