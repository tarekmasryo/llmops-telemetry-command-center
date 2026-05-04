from __future__ import annotations

from collections.abc import Sequence

import numpy as np
import pandas as pd


def safe_pct(value: float | int | None, digits: int = 1) -> str:
    if value is None or pd.isna(value):
        return "—"
    return f"{float(value) * 100:.{digits}f}%"


def safe_money(value: float | int | None, digits: int = 0) -> str:
    if value is None or pd.isna(value):
        return "—"
    return f"${float(value):,.{digits}f}"


def filter_interactions(
    df: pd.DataFrame,
    providers: Sequence[str],
    models: Sequence[str],
    use_cases: Sequence[str],
    channels: Sequence[str],
    tiers: Sequence[str],
    regions: Sequence[str],
    date_range: tuple[pd.Timestamp, pd.Timestamp] | None,
) -> pd.DataFrame:
    out = df.copy()
    for col, selected in [
        ("model_provider", providers),
        ("model_name", models),
        ("use_case", use_cases),
        ("channel", channels),
        ("account_tier", tiers),
        ("region", regions),
    ]:
        if selected and col in out.columns:
            out = out[out[col].isin(selected)]
    if date_range and "timestamp_utc" in out.columns:
        start, end = date_range
        start = (
            pd.Timestamp(start).tz_convert("UTC")
            if pd.Timestamp(start).tzinfo
            else pd.Timestamp(start).tz_localize("UTC")
        )
        end = (
            pd.Timestamp(end).tz_convert("UTC")
            if pd.Timestamp(end).tzinfo
            else pd.Timestamp(end).tz_localize("UTC")
        )
        out = out[(out["timestamp_utc"] >= start) & (out["timestamp_utc"] <= end)]
    return out.reset_index(drop=True)


def compute_kpis(df: pd.DataFrame, sla_ms: int = 2200, fail_budget: float = 0.02) -> dict[str, float | int]:
    if df.empty:
        return {
            "requests": 0,
            "failure_rate": np.nan,
            "sla_breach_rate": np.nan,
            "p95_latency": np.nan,
            "avg_latency": np.nan,
            "total_cost": np.nan,
            "avg_cost": np.nan,
            "tool_usage_rate": np.nan,
            "safety_flag_rate": np.nan,
            "quality_mean": np.nan,
            "health_score": 0,
            "fail_budget_multiple": np.nan,
        }
    failures = df.get("is_failure", pd.Series(False, index=df.index)).astype(bool)
    latency = pd.to_numeric(df.get("latency_ms"), errors="coerce")
    cost = pd.to_numeric(df.get("cost_usd"), errors="coerce")
    tool_calls = pd.to_numeric(df.get("tool_calls_count"), errors="coerce").fillna(0)
    safety = df.get("safety_block_flag", pd.Series(False, index=df.index)).astype(bool)
    quality = pd.to_numeric(df.get("response_quality_score"), errors="coerce")

    failure_rate = float(failures.mean())
    sla_breach_rate = float((latency > sla_ms).mean())
    p95_latency = float(latency.quantile(0.95)) if latency.notna().any() else np.nan
    total_cost = float(cost.sum()) if cost.notna().any() else np.nan
    health = operating_health_score(failure_rate, sla_breach_rate, p95_latency, sla_ms, fail_budget)
    return {
        "requests": int(len(df)),
        "failure_rate": failure_rate,
        "sla_breach_rate": sla_breach_rate,
        "p95_latency": p95_latency,
        "avg_latency": float(latency.mean()) if latency.notna().any() else np.nan,
        "total_cost": total_cost,
        "avg_cost": float(cost.mean()) if cost.notna().any() else np.nan,
        "tool_usage_rate": float((tool_calls > 0).mean()),
        "safety_flag_rate": float(safety.mean()),
        "quality_mean": float(quality.mean()) if quality.notna().any() else np.nan,
        "health_score": health,
        "fail_budget_multiple": failure_rate / max(fail_budget, 1e-9),
    }


def operating_health_score(
    failure_rate: float, sla_rate: float, p95_latency: float, sla_ms: int, fail_budget: float
) -> float:
    """Return an operator heuristic score, not a calibrated production risk model.

    Weighting is intentionally transparent: failure-budget pressure carries the
    largest penalty, SLA breach share is second, and p95 latency adds a smaller
    overload penalty once it exceeds the configured SLA. The score is meant for
    dashboard triage and ranking, not automated rollout approval.
    """
    failure_penalty = min(45.0, 45.0 * (failure_rate / max(fail_budget * 8, 1e-9)))
    sla_penalty = min(30.0, 30.0 * (sla_rate / 0.35))
    latency_ratio = (p95_latency / sla_ms) if sla_ms and not pd.isna(p95_latency) else 1.0
    latency_penalty = min(15.0, max(0.0, (latency_ratio - 1.0) * 25.0))
    return round(max(0.0, 100.0 - failure_penalty - sla_penalty - latency_penalty), 1)


def daily_operational_series(df: pd.DataFrame, sla_ms: int = 2200) -> pd.DataFrame:
    if df.empty or "timestamp_utc" not in df.columns:
        return pd.DataFrame(columns=["date", "requests", "failure_rate", "sla_breach_rate", "cost_usd"])
    tmp = df.copy()
    tmp["date"] = pd.to_datetime(tmp["timestamp_utc"], errors="coerce", utc=True).dt.date
    tmp["sla_breach"] = pd.to_numeric(tmp["latency_ms"], errors="coerce") > sla_ms
    g = (
        tmp.dropna(subset=["date"])
        .groupby("date", as_index=False)
        .agg(
            requests=("interaction_id", "count"),
            failure_rate=("is_failure", "mean"),
            sla_breach_rate=("sla_breach", "mean"),
            cost_usd=("cost_usd", "sum"),
            p95_latency=("latency_ms", lambda s: pd.to_numeric(s, errors="coerce").quantile(0.95)),
        )
    )
    return g


def failure_breakdown(df: pd.DataFrame, top_n: int = 8) -> pd.DataFrame:
    if df.empty or "failure_type" not in df.columns:
        return pd.DataFrame(columns=["failure_type", "requests", "share"])
    failures = df[df.get("is_failure", False).astype(bool)].copy()
    if failures.empty:
        return pd.DataFrame(columns=["failure_type", "requests", "share"])
    out = (
        failures["failure_type"]
        .fillna("unknown")
        .value_counts()
        .head(top_n)
        .rename_axis("failure_type")
        .reset_index(name="requests")
    )
    out["share"] = out["requests"] / max(1, len(failures))
    return out


def model_hotspots(
    df: pd.DataFrame, sla_ms: int = 2200, failure_cost: float = 40.0, sla_penalty: float = 5.0
) -> pd.DataFrame:
    """Rank provider/model segments with a transparent operator heuristic.

    The risk score gives most weight to failure rate, then SLA pressure, with
    latency and average cost as secondary tie-breakers. Expected unit cost uses
    sidebar economics, while risk_score is for visual prioritization only.
    """
    if df.empty:
        return pd.DataFrame()
    tmp = df.copy()
    tmp["sla_breach"] = pd.to_numeric(tmp["latency_ms"], errors="coerce") > sla_ms
    group_cols = [c for c in ["model_provider", "model_name"] if c in tmp.columns]
    out = tmp.groupby(group_cols, as_index=False).agg(
        requests=("interaction_id", "count"),
        failure_rate=("is_failure", "mean"),
        sla_breach_rate=("sla_breach", "mean"),
        p95_latency=("latency_ms", lambda s: pd.to_numeric(s, errors="coerce").quantile(0.95)),
        avg_cost=("cost_usd", "mean"),
        total_cost=("cost_usd", "sum"),
        avg_quality=("response_quality_score", "mean"),
    )
    out["expected_unit_cost"] = (
        out["avg_cost"].fillna(0)
        + out["failure_rate"].fillna(0) * failure_cost
        + out["sla_breach_rate"].fillna(0) * sla_penalty
    )
    out["risk_score"] = (
        out["failure_rate"].fillna(0) * 55
        + out["sla_breach_rate"].fillna(0) * 25
        + (out["p95_latency"].fillna(sla_ms) / max(sla_ms, 1)).clip(0, 3) * 10
        + out["avg_cost"].fillna(0) * 10
    )
    return out.sort_values("risk_score", ascending=False).reset_index(drop=True)


def risk_slices(df: pd.DataFrame, sla_ms: int = 2200, min_requests: int = 20) -> pd.DataFrame:
    """Score use-case/provider/model slices for operator review priority.

    Severity is a dashboard heuristic based on failure rate, SLA breach share,
    and p95 latency pressure after applying a minimum traffic floor.
    """
    if df.empty:
        return pd.DataFrame()
    tmp = df.copy()
    tmp["sla_breach"] = pd.to_numeric(tmp["latency_ms"], errors="coerce") > sla_ms
    group_cols = [c for c in ["use_case", "model_provider", "model_name"] if c in tmp.columns]
    out = tmp.groupby(group_cols, as_index=False).agg(
        requests=("interaction_id", "count"),
        failure_rate=("is_failure", "mean"),
        sla_breach_rate=("sla_breach", "mean"),
        p95_latency=("latency_ms", lambda s: pd.to_numeric(s, errors="coerce").quantile(0.95)),
        avg_cost=("cost_usd", "mean"),
        total_cost=("cost_usd", "sum"),
    )
    out = out[out["requests"] >= min_requests].copy()
    out["severity_score"] = (
        out["failure_rate"] * 100 + out["sla_breach_rate"] * 60 + (out["p95_latency"] / max(sla_ms, 1)) * 10
    )
    out["severity"] = pd.cut(
        out["severity_score"],
        bins=[-np.inf, 35, 55, 75, np.inf],
        labels=["watch", "elevated", "high", "critical"],
    ).astype(str)
    return out.sort_values("severity_score", ascending=False).reset_index(drop=True)


def incident_board(df: pd.DataFrame, sla_ms: int, fail_budget: float) -> pd.DataFrame:
    k = compute_kpis(df, sla_ms=sla_ms, fail_budget=fail_budget)
    rows: list[dict[str, object]] = []
    if k["failure_rate"] > fail_budget:
        rows.append(
            {
                "severity": "critical" if k["failure_rate"] > fail_budget * 8 else "high",
                "signal": "Failure budget breach",
                "why": f"Failure rate {safe_pct(k['failure_rate'])} vs budget {safe_pct(fail_budget)}.",
                "recommended_action": "Freeze rollout, inspect top model/use-case hotspots, and run candidate policies in shadow mode only.",
            }
        )
    if k["sla_breach_rate"] > 0.05:
        rows.append(
            {
                "severity": "high" if k["sla_breach_rate"] > 0.2 else "medium",
                "signal": "SLA breach pressure",
                "why": f"SLA breach rate {safe_pct(k['sla_breach_rate'])}; p95 latency {k['p95_latency']:.0f}ms vs SLA {sla_ms}ms.",
                "recommended_action": "Investigate slow providers, large-token requests, and use cases with high p95 latency.",
            }
        )
    if k["tool_usage_rate"] > 0.35:
        rows.append(
            {
                "severity": "medium",
                "signal": "Tool dependency exposure",
                "why": f"Tool usage appears in {safe_pct(k['tool_usage_rate'])} of requests.",
                "recommended_action": "Inspect tool_error slices and add tool-call guardrails/retries.",
            }
        )
    if not rows:
        rows.append(
            {
                "severity": "ok",
                "signal": "No active incident trigger",
                "why": "Filtered window is within configured thresholds.",
                "recommended_action": "Continue monitoring and compare against notebook-level artifacts.",
            }
        )
    return pd.DataFrame(rows)


def build_triage_queue(
    actions: pd.DataFrame, interactions: pd.DataFrame | None = None, sla_ms: int = 2200
) -> pd.DataFrame:
    """Build a review queue from the notebook triage artifact.

    When a filtered interactions table is provided, the queue is restricted to
    matching ``interaction_id`` values so the displayed queue follows the
    Streamlit sidebar filters. The configured ``sla_ms`` is used consistently
    in priority scoring and reason labels. The probabilities and action flags
    still come from the held-out notebook artifact; this function does not
    retrain or recalibrate triage decisions live.
    """
    if actions.empty:
        return pd.DataFrame()

    q = actions.copy()
    if (
        interactions is not None
        and not interactions.empty
        and "interaction_id" in interactions.columns
        and "interaction_id" in q.columns
    ):
        allowed_ids = set(interactions["interaction_id"].dropna().astype(str))
        q = q[q["interaction_id"].astype(str).isin(allowed_ids)].copy()
        if q.empty:
            return pd.DataFrame()

    q["proba_failure"] = pd.to_numeric(q.get("proba_failure"), errors="coerce")
    q["latency_ms"] = pd.to_numeric(q.get("latency_ms"), errors="coerce")
    q["cost_usd"] = pd.to_numeric(q.get("cost_usd"), errors="coerce")
    cost_p95 = q["cost_usd"].quantile(0.95)
    cost_p90 = q["cost_usd"].quantile(0.90)
    q["priority_score"] = (
        q["proba_failure"].fillna(0) * 70
        + (q["latency_ms"].fillna(0) / max(sla_ms, 1)).clip(0, 3) * 15
        + (q["cost_usd"].fillna(0) / max(cost_p95, 1e-6)).clip(0, 2) * 15
    )
    q["priority"] = pd.cut(
        q["priority_score"],
        bins=[-np.inf, 35, 55, 75, np.inf],
        labels=["low", "medium", "high", "critical"],
    ).astype(str)
    q["reason"] = np.select(
        [q["proba_failure"] >= 0.45, q["latency_ms"] >= sla_ms, q["cost_usd"] >= cost_p90],
        ["High predicted failure risk", "Latency/SLA pressure", "High estimated cost"],
        default="Conservative threshold rule",
    )
    keep = [
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
            "action_review",
        ]
        if c in q.columns
    ]
    return q.sort_values("priority_score", ascending=False)[keep].reset_index(drop=True)
