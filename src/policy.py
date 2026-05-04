from __future__ import annotations

import numpy as np
import pandas as pd


def simulate_routing_policy(
    df: pd.DataFrame,
    sla_ms: int = 2200,
    failure_cost: float = 40.0,
    sla_penalty: float = 5.0,
    max_fail_rate: float = 0.12,
    min_requests: int = 60,
) -> tuple[pd.DataFrame, dict[str, float | int | str]]:
    """Build a simple use-case routing simulator from the filtered window.

    This is intentionally transparent: it ranks historical
    model/use-case slices by expected unit cost under user-selected economics and marks whether the
    selected row met strict constraints or needed fallback.
    """
    if df.empty:
        return pd.DataFrame(), {"status": "empty", "requests": 0}

    tmp = df.copy()
    tmp["sla_breach"] = pd.to_numeric(tmp["latency_ms"], errors="coerce") > sla_ms
    group_cols = ["use_case", "model_provider", "model_name"]
    available_cols = [c for c in group_cols if c in tmp.columns]
    stats = tmp.groupby(available_cols, as_index=False).agg(
        requests=("interaction_id", "count"),
        fail_rate=("is_failure", "mean"),
        p95_latency=("latency_ms", lambda s: pd.to_numeric(s, errors="coerce").quantile(0.95)),
        sla_breach_rate=("sla_breach", "mean"),
        avg_cost=("cost_usd", "mean"),
    )
    stats["expected_unit_cost"] = (
        stats["avg_cost"].fillna(0)
        + stats["fail_rate"].fillna(0) * failure_cost
        + stats["sla_breach_rate"].fillna(0) * sla_penalty
    )

    selected_rows = []
    for use_case, group in stats.groupby("use_case", dropna=False):
        group = group[group["requests"] >= min_requests].copy()
        if group.empty:
            all_group = stats[stats["use_case"].eq(use_case)].copy()
            if all_group.empty:
                continue
            chosen = all_group.sort_values("expected_unit_cost").iloc[0].copy()
            chosen["policy_mode"] = "low_sample_fallback"
        else:
            strict = group[(group["fail_rate"] <= max_fail_rate) & (group["p95_latency"] <= sla_ms)]
            if not strict.empty:
                chosen = strict.sort_values("expected_unit_cost").iloc[0].copy()
                chosen["policy_mode"] = "strict"
            else:
                relaxed = group[
                    (group["fail_rate"] <= max_fail_rate + 0.05) & (group["p95_latency"] <= sla_ms * 1.15)
                ]
                if not relaxed.empty:
                    chosen = relaxed.sort_values("expected_unit_cost").iloc[0].copy()
                    chosen["policy_mode"] = "relaxed"
                else:
                    chosen = group.sort_values("expected_unit_cost").iloc[0].copy()
                    chosen["policy_mode"] = "fallback_unconstrained"
        selected_rows.append(chosen)

    policy = pd.DataFrame(selected_rows)
    if policy.empty:
        return policy, {"status": "empty", "requests": int(len(df))}

    # Baseline is observed expected unit cost for the current filtered window.
    baseline_fail_rate = float(tmp["is_failure"].mean())
    baseline_sla_rate = float(tmp["sla_breach"].mean())
    baseline_avg_cost = float(pd.to_numeric(tmp["cost_usd"], errors="coerce").mean())
    baseline_expected = (
        baseline_avg_cost + baseline_fail_rate * failure_cost + baseline_sla_rate * sla_penalty
    )

    # Weighted policy expectation across use-case volumes in current window.
    use_case_counts = (
        tmp["use_case"]
        .value_counts(normalize=True)
        .rename("weight")
        .reset_index()
        .rename(columns={"index": "use_case"})
    )
    merged = policy.merge(use_case_counts, on="use_case", how="left")
    merged["weight"] = merged["weight"].fillna(0)
    policy_expected = float((merged["expected_unit_cost"] * merged["weight"]).sum())
    delta = policy_expected - baseline_expected
    status = "candidate_improves_cost" if delta < 0 else "candidate_cost_increase"
    strict_share = float((policy["policy_mode"] == "strict").mean())
    summary: dict[str, float | int | str] = {
        "status": status,
        "requests": int(len(df)),
        "use_cases": int(policy["use_case"].nunique()),
        "baseline_expected_unit_cost": round(baseline_expected, 4),
        "policy_expected_unit_cost": round(policy_expected, 4),
        "unit_cost_delta": round(delta, 4),
        "strict_share": round(strict_share, 4),
    }
    return policy.sort_values("expected_unit_cost"), summary


def simulate_threshold_queue(curve: pd.DataFrame, threshold: float) -> dict[str, float | int | str]:
    if curve.empty or "threshold" not in curve.columns:
        return {"status": "missing_curve"}
    tmp = curve.copy()
    tmp["threshold"] = pd.to_numeric(tmp["threshold"], errors="coerce")
    idx = (tmp["threshold"] - threshold).abs().idxmin()
    row = tmp.loc[idx]
    return {
        k: (
            float(v)
            if isinstance(v, np.floating | float)
            else int(v)
            if isinstance(v, np.integer | int)
            else v
        )
        for k, v in row.to_dict().items()
    }
