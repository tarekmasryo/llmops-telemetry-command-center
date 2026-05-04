import pandas as pd

from src.metrics import build_triage_queue, compute_kpis, risk_slices
from src.policy import simulate_routing_policy


def sample_df():
    return pd.DataFrame(
        {
            "interaction_id": ["a", "b", "c", "d"],
            "use_case": ["support", "support", "coding", "coding"],
            "model_provider": ["p1", "p1", "p2", "p2"],
            "model_name": ["m1", "m1", "m2", "m2"],
            "is_failure": [True, False, False, False],
            "latency_ms": [3000, 1200, 900, 1000],
            "cost_usd": [0.3, 0.2, 0.1, 0.1],
            "tool_calls_count": [1, 0, 0, 0],
            "response_quality_score": [0.2, 0.8, 0.9, 0.85],
        }
    )


def test_compute_kpis_returns_expected_shape():
    kpis = compute_kpis(sample_df(), sla_ms=2200, fail_budget=0.02)
    assert kpis["requests"] == 4
    assert round(kpis["failure_rate"], 2) == 0.25
    assert round(kpis["sla_breach_rate"], 2) == 0.25
    assert 0 <= kpis["health_score"] <= 100


def test_policy_simulator_returns_summary():
    policy, summary = simulate_routing_policy(sample_df(), min_requests=1)
    assert not policy.empty
    assert summary["requests"] == 4
    assert "baseline_expected_unit_cost" in summary


def test_risk_slices_has_severity():
    slices = risk_slices(sample_df(), min_requests=1)
    assert "severity" in slices.columns


def test_compute_kpis_empty_frame_is_safe():
    kpis = compute_kpis(pd.DataFrame(), sla_ms=2200, fail_budget=0.02)
    assert kpis["requests"] == 0
    assert kpis["health_score"] == 0


def test_filter_interactions_by_provider_and_date():
    df = sample_df().copy()
    df["timestamp_utc"] = pd.to_datetime(["2025-01-01", "2025-01-02", "2025-02-01", "2025-02-02"], utc=True)
    from src.metrics import filter_interactions

    out = filter_interactions(
        df,
        providers=["p1"],
        models=[],
        use_cases=[],
        channels=[],
        tiers=[],
        regions=[],
        date_range=(pd.Timestamp("2025-01-01", tz="UTC"), pd.Timestamp("2025-01-31", tz="UTC")),
    )
    assert len(out) == 2
    assert set(out["model_provider"]) == {"p1"}


def test_build_triage_queue_prioritizes_rows():
    actions = pd.DataFrame(
        {
            "interaction_id": ["low", "high"],
            "proba_failure": [0.12, 0.80],
            "latency_ms": [900, 3500],
            "cost_usd": [0.01, 0.50],
            "action_review": [True, True],
        }
    )
    queue = build_triage_queue(actions)
    assert queue.iloc[0]["interaction_id"] == "high"
    assert "reason" in queue.columns


def test_build_triage_queue_respects_filtered_interactions():
    actions = pd.DataFrame(
        {
            "interaction_id": ["keep", "drop"],
            "proba_failure": [0.70, 0.90],
            "latency_ms": [2400, 3600],
            "cost_usd": [0.20, 0.80],
            "action_review": [True, True],
        }
    )
    filtered = pd.DataFrame({"interaction_id": ["keep"]})
    queue = build_triage_queue(actions, filtered)
    assert queue["interaction_id"].tolist() == ["keep"]


def test_build_triage_queue_uses_configured_sla_for_reason():
    actions = pd.DataFrame(
        {
            "interaction_id": ["near_sla"],
            "proba_failure": [0.10],
            "latency_ms": [2500],
            "cost_usd": [0.01],
            "action_review": [True],
        }
    )

    default_sla_queue = build_triage_queue(actions, sla_ms=2200)
    relaxed_sla_queue = build_triage_queue(actions, sla_ms=4000)

    assert default_sla_queue.iloc[0]["reason"] == "Latency/SLA pressure"
    assert relaxed_sla_queue.iloc[0]["reason"] != "Latency/SLA pressure"
