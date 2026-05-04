import pandas as pd

from src.policy import simulate_routing_policy, simulate_threshold_queue


def test_policy_simulator_handles_empty_frame():
    policy, summary = simulate_routing_policy(pd.DataFrame())
    assert policy.empty
    assert summary["status"] == "empty"


def test_policy_simulator_marks_fallback_when_constraints_fail():
    df = pd.DataFrame(
        {
            "interaction_id": ["a", "b", "c"],
            "use_case": ["support", "support", "support"],
            "model_provider": ["p", "p", "p"],
            "model_name": ["m", "m", "m"],
            "is_failure": [True, True, False],
            "latency_ms": [5000, 5200, 5100],
            "cost_usd": [0.2, 0.2, 0.2],
        }
    )
    policy, summary = simulate_routing_policy(df, sla_ms=2200, max_fail_rate=0.01, min_requests=1)
    assert summary["requests"] == 3
    assert policy.iloc[0]["policy_mode"] == "fallback_unconstrained"


def test_threshold_queue_selects_nearest_threshold():
    curve = pd.DataFrame(
        {
            "threshold": [0.10, 0.20],
            "expected_cost": [100.0, 130.0],
            "review_share": [1.0, 0.5],
            "precision": [0.3, 0.4],
            "recall": [1.0, 0.7],
        }
    )
    row = simulate_threshold_queue(curve, 0.18)
    assert row["threshold"] == 0.2
    assert row["expected_cost"] == 130.0
