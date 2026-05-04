from __future__ import annotations

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

TEMPLATE = "plotly_dark"
COLORS = {
    "blue": "#38bdf8",
    "purple": "#a78bfa",
    "green": "#34d399",
    "amber": "#fbbf24",
    "red": "#fb7185",
    "slate": "#94a3b8",
}


def _layout(fig: go.Figure, height: int = 360) -> go.Figure:
    fig.update_layout(
        template=TEMPLATE,
        height=height,
        margin=dict(l=16, r=16, t=36, b=16),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(15,23,42,0.35)",
        font=dict(family="Inter, Segoe UI, sans-serif", size=12, color="#cbd5e1"),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    fig.update_xaxes(gridcolor="rgba(148,163,184,0.15)", zerolinecolor="rgba(148,163,184,0.18)")
    fig.update_yaxes(gridcolor="rgba(148,163,184,0.15)", zerolinecolor="rgba(148,163,184,0.18)")
    return fig


def empty_figure(title: str = "No data") -> go.Figure:
    fig = go.Figure()
    fig.add_annotation(text=title, x=0.5, y=0.5, showarrow=False, font=dict(size=16, color="#94a3b8"))
    return _layout(fig, height=260)


def line_operations(daily: pd.DataFrame) -> go.Figure:
    if daily.empty:
        return empty_figure("No daily data for selected filters")
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=daily["date"],
            y=daily["failure_rate"],
            name="failure rate",
            mode="lines",
            line=dict(color=COLORS["red"], width=3),
        )
    )
    fig.add_trace(
        go.Scatter(
            x=daily["date"],
            y=daily["sla_breach_rate"],
            name="SLA breach",
            mode="lines",
            line=dict(color=COLORS["amber"], width=3),
        )
    )
    fig.add_trace(
        go.Bar(
            x=daily["date"],
            y=daily["requests"],
            name="requests",
            yaxis="y2",
            marker_color="rgba(56,189,248,0.25)",
        )
    )
    fig.update_layout(
        title="Daily operating pressure",
        yaxis=dict(title="rate", tickformat=".0%"),
        yaxis2=dict(title="requests", overlaying="y", side="right", showgrid=False),
        barmode="overlay",
    )
    return _layout(fig, height=380)


def failure_type_bar(df: pd.DataFrame) -> go.Figure:
    if df.empty:
        return empty_figure("No failures in selected window")
    fig = px.bar(
        df,
        x="share",
        y="failure_type",
        orientation="h",
        text=df["share"].map(lambda x: f"{x:.1%}"),
        color="share",
        color_continuous_scale=[COLORS["amber"], COLORS["red"]],
    )
    fig.update_layout(
        title="Failure type mix",
        coloraxis_showscale=False,
        xaxis_tickformat=".0%",
        yaxis_title="",
        xaxis_title="share of failures",
    )
    fig.update_traces(textposition="outside", cliponaxis=False)
    return _layout(fig, height=340)


def hotspot_scatter(df: pd.DataFrame, sla_ms: int = 2200, fail_budget: float = 0.02) -> go.Figure:
    if df.empty:
        return empty_figure("No model hotspot data")
    fig = px.scatter(
        df,
        x="p95_latency",
        y="failure_rate",
        size="requests",
        color="expected_unit_cost",
        hover_data=["model_provider", "model_name", "requests", "sla_breach_rate", "avg_cost"],
        text="model_name",
        color_continuous_scale=[COLORS["green"], COLORS["amber"], COLORS["red"]],
        size_max=42,
    )
    fig.add_vline(x=sla_ms, line_dash="dash", line_color=COLORS["amber"], annotation_text="SLA")
    fig.add_hline(y=fail_budget, line_dash="dash", line_color=COLORS["red"], annotation_text="fail budget")
    fig.update_layout(
        title="Provider / model hotspot map",
        xaxis_title="p95 latency (ms)",
        yaxis_title="failure rate",
        yaxis_tickformat=".0%",
        coloraxis_colorbar_title="exp. unit cost",
    )
    fig.update_traces(textposition="top center")
    return _layout(fig, height=470)


def cost_by_dimension(df: pd.DataFrame, dimension: str) -> go.Figure:
    if df.empty or dimension not in df.columns:
        return empty_figure("No cost data")
    g = (
        df.groupby(dimension, as_index=False)
        .agg(total_cost=("cost_usd", "sum"), requests=("interaction_id", "count"))
        .sort_values("total_cost", ascending=True)
        .tail(12)
    )
    fig = px.bar(
        g,
        x="total_cost",
        y=dimension,
        orientation="h",
        text="requests",
        color="total_cost",
        color_continuous_scale=[COLORS["blue"], COLORS["purple"]],
    )
    fig.update_layout(
        title=f"Cost concentration by {dimension}",
        coloraxis_showscale=False,
        xaxis_title="estimated cost",
        yaxis_title="",
    )
    return _layout(fig, height=360)


def triage_curve(curve: pd.DataFrame, selected_threshold: float) -> go.Figure:
    if curve.empty:
        return empty_figure("No triage curve artifact")
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=curve["threshold"],
            y=curve["expected_cost"],
            name="expected cost",
            line=dict(color=COLORS["red"], width=3),
        )
    )
    fig.add_trace(
        go.Scatter(
            x=curve["threshold"],
            y=curve["review_share"],
            name="review share",
            yaxis="y2",
            line=dict(color=COLORS["blue"], width=3),
        )
    )
    fig.add_vline(
        x=selected_threshold, line_dash="dash", line_color=COLORS["amber"], annotation_text="selected"
    )
    fig.update_layout(
        title="Triage threshold simulator",
        xaxis_title="threshold",
        yaxis=dict(title="expected cost"),
        yaxis2=dict(title="review share", tickformat=".0%", overlaying="y", side="right", showgrid=False),
    )
    return _layout(fig, height=380)


def triage_performance_curve(curve: pd.DataFrame, selected_threshold: float) -> go.Figure:
    if curve.empty:
        return empty_figure("No triage curve artifact")
    tmp = curve.copy()
    for col in ["threshold", "precision", "recall", "review_share", "expected_cost"]:
        if col in tmp.columns:
            tmp[col] = pd.to_numeric(tmp[col], errors="coerce")
    tmp["f1"] = (2 * tmp["precision"] * tmp["recall"]) / (tmp["precision"] + tmp["recall"]).replace(0, pd.NA)

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=tmp["threshold"], y=tmp["precision"], name="precision", line=dict(color=COLORS["blue"], width=3)
        )
    )
    fig.add_trace(
        go.Scatter(
            x=tmp["threshold"], y=tmp["recall"], name="recall", line=dict(color=COLORS["green"], width=3)
        )
    )
    fig.add_trace(
        go.Scatter(x=tmp["threshold"], y=tmp["f1"], name="F1", line=dict(color=COLORS["purple"], width=3))
    )
    fig.add_trace(
        go.Scatter(
            x=tmp["threshold"],
            y=tmp["review_share"],
            name="review share",
            line=dict(color=COLORS["amber"], width=3, dash="dot"),
        )
    )
    fig.add_vline(
        x=selected_threshold, line_dash="dash", line_color=COLORS["red"], annotation_text="selected"
    )
    fig.update_layout(
        title="Triage performance trade-off",
        xaxis_title="threshold",
        yaxis=dict(title="rate", tickformat=".0%"),
    )
    return _layout(fig, height=390)


def drift_bars(drift: pd.DataFrame) -> go.Figure:
    if drift.empty:
        return empty_figure("No drift report")
    tmp = drift.copy()
    tmp["score"] = tmp["psi"].fillna(tmp["tv_distance"]).fillna(0)
    tmp["severity"] = tmp["severity"].fillna("low").replace("", "low")
    tmp = tmp.sort_values("score", ascending=True).tail(16)
    fig = px.bar(
        tmp,
        x="score",
        y="feature",
        orientation="h",
        color="type",
        text="severity",
        color_discrete_sequence=[COLORS["green"], COLORS["blue"]],
    )
    fig.update_layout(title="Temporal drift monitor", xaxis_title="PSI / TV distance", yaxis_title="")
    return _layout(fig, height=420)


def baseline_comparison(df: pd.DataFrame) -> go.Figure:
    if df.empty:
        return empty_figure("No baseline comparison")
    fig = px.bar(
        df.sort_values("expected_cost"),
        x="policy",
        y="expected_cost",
        color="review_share",
        text="reviewed_rows",
        color_continuous_scale=[COLORS["green"], COLORS["amber"], COLORS["red"]],
    )
    fig.update_layout(
        title="Triage baseline comparison",
        yaxis_title="expected cost",
        xaxis_title="",
        coloraxis_colorbar_title="review share",
    )
    return _layout(fig, height=340)
