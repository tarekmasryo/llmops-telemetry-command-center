from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
ARTIFACTS_DIR = ROOT / "artifacts"

INTERACTIONS_REQUIRED_COLUMNS = {
    "interaction_id",
    "timestamp_utc",
    "use_case",
    "model_provider",
    "model_name",
    "latency_ms",
    "cost_usd",
    "is_failure",
}
SESSIONS_REQUIRED_COLUMNS = {
    "session_id",
    "user_id",
    "total_requests",
    "failure_rate",
    "total_cost_usd",
}
USERS_REQUIRED_COLUMNS = {
    "user_id",
    "total_sessions",
    "total_requests",
    "overall_failure_rate",
    "total_cost_usd",
}
PROMPTS_REQUIRED_COLUMNS = {
    "prompt_id",
    "instruction_template",
    "use_case",
    "n_interactions",
    "instruction_text",
}
INSTRUCTION_SAMPLES_REQUIRED_COLUMNS = {
    "sample_id",
    "interaction_id",
    "session_id",
    "user_id",
    "split",
    "use_case",
    "prompt_id",
    "sft_user_prompt",
    "sft_assistant_response",
}
ROUTING_SUMMARY_REQUIRED_COLUMNS = {
    "routing_status",
    "routing_recommendation",
    "baseline_expected_unit_cost",
    "policy_expected_unit_cost",
    "unit_cost_delta_vs_baseline",
}
ROUTING_POLICY_REQUIRED_COLUMNS = {
    "use_case",
    "model_provider",
    "model_name",
    "requests",
    "expected_unit_cost",
    "policy_mode",
}
DRIFT_REQUIRED_COLUMNS = {"feature", "type", "severity"}
STRICT_BOOL_COLUMNS = {"is_failure", "action_review"}
TRIAGE_ACTIONS_REQUIRED_COLUMNS = {"interaction_id", "proba_failure", "action_review"}
TRIAGE_BASELINES_REQUIRED_COLUMNS = {"policy", "expected_cost", "review_share", "precision", "recall"}
TRIAGE_CURVE_REQUIRED_COLUMNS = {"threshold", "expected_cost", "review_share", "precision", "recall"}


@dataclass(frozen=True)
class DataBundle:
    interactions: pd.DataFrame
    sessions: pd.DataFrame
    users: pd.DataFrame
    prompts_lookup: pd.DataFrame
    instruction_samples: pd.DataFrame
    routing_summary: pd.DataFrame
    routing_policy: pd.DataFrame
    drift_report: pd.DataFrame
    triage_actions: pd.DataFrame
    triage_baselines: pd.DataFrame
    triage_curve: pd.DataFrame
    triage_policy: dict[str, Any]
    decision_artifact: dict[str, Any]


def read_csv_required(path: Path) -> pd.DataFrame:
    """Read a required CSV and fail loudly when the artifact is invalid."""
    if not path.exists():
        raise FileNotFoundError(f"Required CSV not found: {path}")
    try:
        df = pd.read_csv(path)
    except Exception as exc:  # pragma: no cover - message quality matters more than branch type
        raise RuntimeError(f"Failed to read CSV artifact: {path.name}. Original error: {exc}") from exc
    if df.empty:
        raise ValueError(f"CSV artifact is empty: {path.name}")
    return df


def read_json_required(path: Path) -> dict[str, Any]:
    """Read a required JSON artifact and fail loudly when it is invalid."""
    if not path.exists():
        raise FileNotFoundError(f"Required JSON not found: {path}")
    try:
        with path.open("r", encoding="utf-8") as f:
            payload = json.load(f)
    except Exception as exc:  # pragma: no cover
        raise RuntimeError(f"Failed to read JSON artifact: {path.name}. Original error: {exc}") from exc
    if not isinstance(payload, dict):
        raise ValueError(f"JSON artifact must contain an object: {path.name}")
    return payload


def require_columns(df: pd.DataFrame, required: set[str], source_name: str) -> None:
    """Validate that an input table has the minimum schema needed by the app."""
    missing = sorted(required.difference(df.columns))
    if missing:
        raise ValueError(f"{source_name} is missing required columns: {', '.join(missing)}")


def validate_interactions(df: pd.DataFrame) -> None:
    """Validate core telemetry ranges after type coercion."""
    require_columns(df, INTERACTIONS_REQUIRED_COLUMNS, "llm_system_interactions.csv")
    if df["interaction_id"].isna().any():
        raise ValueError("llm_system_interactions.csv contains missing interaction_id values")
    if "timestamp_utc" in df.columns and df["timestamp_utc"].isna().all():
        raise ValueError("llm_system_interactions.csv has no valid timestamp_utc values after parsing")
    if not pd.api.types.is_bool_dtype(df["is_failure"]):
        raise ValueError("llm_system_interactions.csv is_failure must be boolean-compatible")
    if df["is_failure"].isna().any():
        raise ValueError("llm_system_interactions.csv contains missing is_failure values")
    for col in ["latency_ms", "cost_usd", "prompt_tokens", "completion_tokens", "total_tokens"]:
        if col in df.columns:
            values = pd.to_numeric(df[col], errors="coerce")
            if values.notna().any() and (values.dropna() < 0).any():
                raise ValueError(f"llm_system_interactions.csv contains negative values in {col}")


def validate_triage_policy(payload: dict[str, Any]) -> None:
    required = {"threshold", "operating_mode", "selected_policy_metrics", "economics", "metrics"}
    missing = sorted(required.difference(payload.keys()))
    if missing:
        raise ValueError(f"triage_threshold_policy.json is missing required keys: {', '.join(missing)}")


def validate_decision_artifact(payload: dict[str, Any]) -> None:
    required = {"status", "issues", "scope_note", "generated_outputs", "operator_knobs"}
    missing = sorted(required.difference(payload.keys()))
    if missing:
        raise ValueError(f"decision_artifact.json is missing required keys: {', '.join(missing)}")


def validate_bundle_integrity(bundle: DataBundle) -> None:
    """Validate cross-table and artifact referential integrity for the bundled release."""
    interactions = bundle.interactions
    sessions = bundle.sessions
    users = bundle.users

    if interactions["interaction_id"].duplicated().any():
        raise ValueError("llm_system_interactions.csv contains duplicate interaction_id values")

    if "session_id" in interactions.columns and "session_id" in sessions.columns:
        if sessions["session_id"].duplicated().any():
            raise ValueError("llm_system_sessions_summary.csv contains duplicate session_id values")
        missing_sessions = _missing_references(interactions["session_id"], sessions["session_id"])
        if missing_sessions:
            raise ValueError(
                "llm_system_interactions.csv contains session_id values missing from "
                f"llm_system_sessions_summary.csv: {', '.join(missing_sessions[:5])}"
            )

    if "user_id" in interactions.columns and "user_id" in users.columns:
        if users["user_id"].duplicated().any():
            raise ValueError("llm_system_users_summary.csv contains duplicate user_id values")
        missing_users = _missing_references(interactions["user_id"], users["user_id"])
        if missing_users:
            raise ValueError(
                "llm_system_interactions.csv contains user_id values missing from "
                f"llm_system_users_summary.csv: {', '.join(missing_users[:5])}"
            )

    prompts = bundle.prompts_lookup
    instruction_samples = bundle.instruction_samples

    if "prompt_id" in prompts.columns:
        if prompts["prompt_id"].duplicated().any():
            raise ValueError("llm_system_prompts_lookup.csv contains duplicate prompt_id values")

    if "prompt_id" in interactions.columns and "prompt_id" in prompts.columns:
        missing_prompts = _missing_references(interactions["prompt_id"], prompts["prompt_id"])
        if missing_prompts:
            raise ValueError(
                "llm_system_interactions.csv contains prompt_id values missing from "
                f"llm_system_prompts_lookup.csv: {', '.join(missing_prompts[:5])}"
            )

    if "sample_id" in instruction_samples.columns and instruction_samples["sample_id"].duplicated().any():
        raise ValueError("llm_system_instruction_tuning_samples.csv contains duplicate sample_id values")

    if "interaction_id" in instruction_samples.columns:
        missing_sample_interactions = _missing_references(
            instruction_samples["interaction_id"], interactions["interaction_id"]
        )
        if missing_sample_interactions:
            raise ValueError(
                "llm_system_instruction_tuning_samples.csv contains interaction_id values missing from "
                f"llm_system_interactions.csv: {', '.join(missing_sample_interactions[:5])}"
            )

    if "session_id" in instruction_samples.columns and "session_id" in sessions.columns:
        missing_sample_sessions = _missing_references(
            instruction_samples["session_id"], sessions["session_id"]
        )
        if missing_sample_sessions:
            raise ValueError(
                "llm_system_instruction_tuning_samples.csv contains session_id values missing from "
                f"llm_system_sessions_summary.csv: {', '.join(missing_sample_sessions[:5])}"
            )

    if "user_id" in instruction_samples.columns and "user_id" in users.columns:
        missing_sample_users = _missing_references(instruction_samples["user_id"], users["user_id"])
        if missing_sample_users:
            raise ValueError(
                "llm_system_instruction_tuning_samples.csv contains user_id values missing from "
                f"llm_system_users_summary.csv: {', '.join(missing_sample_users[:5])}"
            )

    if "prompt_id" in instruction_samples.columns and "prompt_id" in prompts.columns:
        missing_sample_prompts = _missing_references(instruction_samples["prompt_id"], prompts["prompt_id"])
        if missing_sample_prompts:
            raise ValueError(
                "llm_system_instruction_tuning_samples.csv contains prompt_id values missing from "
                f"llm_system_prompts_lookup.csv: {', '.join(missing_sample_prompts[:5])}"
            )

    if "interaction_id" in bundle.triage_actions.columns:
        missing_actions = _missing_references(
            bundle.triage_actions["interaction_id"], interactions["interaction_id"]
        )
        if missing_actions:
            raise ValueError(
                "triage_actions_preview.csv contains interaction_id values missing from "
                f"llm_system_interactions.csv: {', '.join(missing_actions[:5])}"
            )


def _missing_references(left: pd.Series, right: pd.Series) -> list[str]:
    left_values = set(left.dropna().astype(str))
    right_values = set(right.dropna().astype(str))
    return sorted(left_values.difference(right_values))


def coerce_interactions(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    for col in ["timestamp_utc", "date_utc"]:
        if col in out.columns:
            out[col] = pd.to_datetime(out[col], errors="coerce", utc=True)
    bool_cols = [
        "is_failure",
        "hallucination_flag",
        "toxicity_flag",
        "safety_block_flag",
        "formatting_error_flag",
        "tool_error_flag",
        "latency_timeout_flag",
        "user_reported_issue",
        "is_weekend",
        "is_peak_hour",
        "user_feedback_observed",
        "action_review",
    ]
    for col in bool_cols:
        if col in out.columns:
            out[col] = _coerce_bool_series(out[col], col)
    numeric_cols = [
        "latency_ms",
        "cost_usd",
        "prompt_tokens",
        "completion_tokens",
        "total_tokens",
        "response_quality_score",
        "tool_calls_count",
        "user_feedback_score",
        "tokens_per_second",
        "prompt_to_completion_ratio",
        "hour_of_day_utc",
    ]
    for col in numeric_cols:
        if col in out.columns:
            out[col] = pd.to_numeric(out[col], errors="coerce")
    if "timestamp_utc" in out.columns:
        out = out.sort_values("timestamp_utc").reset_index(drop=True)
    return out


def _to_bool(value: object) -> bool | None:
    if isinstance(value, bool):
        return value
    if value is None or pd.isna(value):
        return None
    text = str(value).strip().lower()
    if text in {"true", "1", "yes", "y", "t"}:
        return True
    if text in {"false", "0", "no", "n", "f", "none", "nan", ""}:
        return False
    return None


def _coerce_bool_series(series: pd.Series, column_name: str) -> pd.Series:
    converted = series.map(_to_bool)
    if column_name in STRICT_BOOL_COLUMNS and converted.isna().any():
        bad_values = series[converted.isna()].dropna().astype(str).unique().tolist()[:5]
        examples = ", ".join(bad_values) if bad_values else "missing values"
        raise ValueError(f"{column_name} must contain boolean-compatible values; examples: {examples}")
    return converted.fillna(False).astype(bool)


def load_bundle() -> DataBundle:
    interactions = coerce_interactions(read_csv_required(DATA_DIR / "llm_system_interactions.csv"))
    validate_interactions(interactions)

    sessions = read_csv_required(DATA_DIR / "llm_system_sessions_summary.csv")
    require_columns(sessions, SESSIONS_REQUIRED_COLUMNS, "llm_system_sessions_summary.csv")

    users = read_csv_required(DATA_DIR / "llm_system_users_summary.csv")
    require_columns(users, USERS_REQUIRED_COLUMNS, "llm_system_users_summary.csv")

    prompts_lookup = read_csv_required(DATA_DIR / "llm_system_prompts_lookup.csv")
    require_columns(prompts_lookup, PROMPTS_REQUIRED_COLUMNS, "llm_system_prompts_lookup.csv")

    instruction_samples = read_csv_required(DATA_DIR / "llm_system_instruction_tuning_samples.csv")
    require_columns(
        instruction_samples,
        INSTRUCTION_SAMPLES_REQUIRED_COLUMNS,
        "llm_system_instruction_tuning_samples.csv",
    )

    routing_summary = read_csv_required(ARTIFACTS_DIR / "routing_backtest_summary.csv")
    require_columns(routing_summary, ROUTING_SUMMARY_REQUIRED_COLUMNS, "routing_backtest_summary.csv")

    routing_policy = read_csv_required(ARTIFACTS_DIR / "routing_policy_use_case.csv")
    require_columns(routing_policy, ROUTING_POLICY_REQUIRED_COLUMNS, "routing_policy_use_case.csv")

    drift_report = read_csv_required(ARTIFACTS_DIR / "drift_report.csv")
    require_columns(drift_report, DRIFT_REQUIRED_COLUMNS, "drift_report.csv")

    triage_actions = read_csv_required(ARTIFACTS_DIR / "triage_actions_preview.csv")
    require_columns(triage_actions, TRIAGE_ACTIONS_REQUIRED_COLUMNS, "triage_actions_preview.csv")
    triage_actions = coerce_interactions(triage_actions)

    triage_baselines = read_csv_required(ARTIFACTS_DIR / "triage_baseline_comparison.csv")
    require_columns(triage_baselines, TRIAGE_BASELINES_REQUIRED_COLUMNS, "triage_baseline_comparison.csv")

    triage_curve = read_csv_required(ARTIFACTS_DIR / "triage_threshold_curve.csv")
    require_columns(triage_curve, TRIAGE_CURVE_REQUIRED_COLUMNS, "triage_threshold_curve.csv")

    triage_policy = read_json_required(ARTIFACTS_DIR / "triage_threshold_policy.json")
    validate_triage_policy(triage_policy)

    decision_artifact = read_json_required(ARTIFACTS_DIR / "decision_artifact.json")
    validate_decision_artifact(decision_artifact)

    bundle = DataBundle(
        interactions=interactions,
        sessions=sessions,
        users=users,
        prompts_lookup=prompts_lookup,
        instruction_samples=instruction_samples,
        routing_summary=routing_summary,
        routing_policy=routing_policy,
        drift_report=drift_report,
        triage_actions=triage_actions,
        triage_baselines=triage_baselines,
        triage_curve=triage_curve,
        triage_policy=triage_policy,
        decision_artifact=decision_artifact,
    )
    validate_bundle_integrity(bundle)
    return bundle
