from pathlib import Path

import pandas as pd
import pytest

from src.data import (
    _to_bool,
    coerce_interactions,
    read_csv_required,
    read_json_required,
    require_columns,
    validate_bundle_integrity,
    validate_interactions,
    validate_triage_policy,
)


def test_to_bool_handles_common_inputs():
    assert _to_bool(True) is True
    assert _to_bool("YES") is True
    assert _to_bool("0") is False
    assert _to_bool("") is False
    assert _to_bool(None) is None
    assert _to_bool("unexpected") is None


def test_coerce_interactions_converts_types():
    df = pd.DataFrame(
        {
            "timestamp_utc": ["2025-01-01T00:00:00Z", "bad-date"],
            "is_failure": ["true", "no"],
            "latency_ms": ["1200", "bad"],
            "cost_usd": ["0.12", None],
        }
    )
    out = coerce_interactions(df)
    assert out["is_failure"].tolist() == [True, False]
    assert pd.api.types.is_datetime64_any_dtype(out["timestamp_utc"])
    assert out["latency_ms"].notna().sum() == 1


def test_required_readers_fail_loudly(tmp_path: Path):
    with pytest.raises(FileNotFoundError):
        read_csv_required(tmp_path / "missing.csv")
    empty = tmp_path / "empty.csv"
    empty.write_text("a,b\n", encoding="utf-8")
    with pytest.raises(ValueError):
        read_csv_required(empty)
    bad_json = tmp_path / "bad.json"
    bad_json.write_text("[]", encoding="utf-8")
    with pytest.raises(ValueError):
        read_json_required(bad_json)


def test_require_columns_reports_missing_columns():
    df = pd.DataFrame({"a": [1]})
    with pytest.raises(ValueError, match="missing required columns"):
        require_columns(df, {"a", "b"}, "sample.csv")


def test_validate_interactions_rejects_negative_core_values():
    df = pd.DataFrame(
        {
            "interaction_id": ["x"],
            "timestamp_utc": pd.to_datetime(["2025-01-01"], utc=True),
            "use_case": ["support"],
            "model_provider": ["p"],
            "model_name": ["m"],
            "latency_ms": [-1],
            "cost_usd": [0.1],
            "is_failure": [False],
        }
    )
    with pytest.raises(ValueError, match="negative values"):
        validate_interactions(df)


def test_coerce_interactions_rejects_invalid_required_boolean_values():
    df = pd.DataFrame(
        {
            "timestamp_utc": ["2025-01-01T00:00:00Z"],
            "is_failure": ["not-a-bool"],
            "latency_ms": [1200],
            "cost_usd": [0.12],
        }
    )

    with pytest.raises(ValueError, match="is_failure must contain boolean-compatible values"):
        coerce_interactions(df)


def test_validate_interactions_requires_boolean_is_failure():
    df = pd.DataFrame(
        {
            "interaction_id": ["x"],
            "timestamp_utc": pd.to_datetime(["2025-01-01"], utc=True),
            "use_case": ["support"],
            "model_provider": ["p"],
            "model_name": ["m"],
            "latency_ms": [1200],
            "cost_usd": [0.1],
            "is_failure": ["false"],
        }
    )
    with pytest.raises(ValueError, match="is_failure must be boolean-compatible"):
        validate_interactions(df)


def test_validate_triage_policy_requires_core_keys():
    with pytest.raises(ValueError, match="missing required keys"):
        validate_triage_policy({"threshold": 0.1})


def test_validate_bundle_integrity_rejects_duplicate_interaction_ids():
    from src.data import load_bundle

    bundle = load_bundle()
    broken = bundle.interactions.copy()
    broken.loc[broken.index[1], "interaction_id"] = broken.loc[broken.index[0], "interaction_id"]
    broken_bundle = bundle.__class__(
        interactions=broken,
        sessions=bundle.sessions,
        users=bundle.users,
        prompts_lookup=bundle.prompts_lookup,
        instruction_samples=bundle.instruction_samples,
        routing_summary=bundle.routing_summary,
        routing_policy=bundle.routing_policy,
        drift_report=bundle.drift_report,
        triage_actions=bundle.triage_actions,
        triage_baselines=bundle.triage_baselines,
        triage_curve=bundle.triage_curve,
        triage_policy=bundle.triage_policy,
        decision_artifact=bundle.decision_artifact,
    )
    with pytest.raises(ValueError, match="duplicate interaction_id"):
        validate_bundle_integrity(broken_bundle)
