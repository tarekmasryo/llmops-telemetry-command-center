import hashlib
import re
from pathlib import Path

import pandas as pd

from src.data import ARTIFACTS_DIR, DATA_DIR, read_json_required

ROOT = Path(__file__).resolve().parents[1]

REQUIRED_DATA_FILES = {
    "llm_system_interactions.csv",
    "llm_system_sessions_summary.csv",
    "llm_system_users_summary.csv",
    "llm_system_prompts_lookup.csv",
    "llm_system_instruction_tuning_samples.csv",
}

REQUIRED_ARTIFACT_FILES = {
    "decision_artifact.json",
    "routing_backtest_summary.csv",
    "routing_policy_use_case.csv",
    "drift_report.csv",
    "triage_threshold_policy.json",
    "triage_threshold_curve.csv",
    "triage_baseline_comparison.csv",
    "triage_actions_preview.csv",
}


def test_required_data_and_artifact_files_are_present():
    data_files = {p.name for p in DATA_DIR.iterdir() if p.is_file()}
    artifact_files = {p.name for p in ARTIFACTS_DIR.iterdir() if p.is_file()}
    assert REQUIRED_DATA_FILES.issubset(data_files)
    assert REQUIRED_ARTIFACT_FILES.issubset(artifact_files)


def test_decision_artifact_generated_outputs_exist():
    payload = read_json_required(ARTIFACTS_DIR / "decision_artifact.json")
    generated_outputs = payload.get("generated_outputs", {})
    assert generated_outputs
    for relative_path in generated_outputs.values():
        path = ROOT / str(relative_path)
        assert path.exists(), f"Generated output is missing: {relative_path}"


def test_triage_policy_references_existing_curve_and_baseline():
    payload = read_json_required(ARTIFACTS_DIR / "triage_threshold_policy.json")
    for key in ["baseline_comparison_path", "threshold_curve_path"]:
        path = ROOT / str(payload[key])
        assert path.exists(), f"Triage policy reference is missing: {payload[key]}"


def test_routing_backtest_exposes_rollout_verdict():
    summary = pd.read_csv(ARTIFACTS_DIR / "routing_backtest_summary.csv")
    row = summary.iloc[0]
    assert row["routing_status"]
    assert row["routing_recommendation"]
    assert "unit_cost_delta_vs_baseline" in summary.columns


def test_artifact_manifest_matches_bundled_files():
    manifest_path = ROOT / "docs" / "artifact_manifest.md"
    manifest = manifest_path.read_text(encoding="utf-8")
    rows = re.findall(r"\| `([^`]+)` \| ([^|]+) \| ([^|]+) \| `([a-f0-9]{64})` \|", manifest)
    assert rows, "No manifest entries were parsed"

    for relative_path, expected_rows, expected_cols, expected_sha in rows:
        path = ROOT / relative_path
        assert path.exists(), f"Manifest references a missing file: {relative_path}"
        actual_sha = hashlib.sha256(path.read_bytes()).hexdigest()
        assert actual_sha == expected_sha, f"SHA256 mismatch for {relative_path}"

        if expected_rows.strip() != "n/a":
            df = pd.read_csv(path)
            assert len(df) == int(expected_rows.strip()), f"Row-count mismatch for {relative_path}"
            assert len(df.columns) == int(expected_cols.strip()), f"Column-count mismatch for {relative_path}"


def test_drift_report_has_explicit_severity_labels():
    drift = pd.read_csv(ARTIFACTS_DIR / "drift_report.csv")
    assert drift["severity"].notna().all()
    assert set(drift["severity"]).issubset({"low", "medium", "high"})
