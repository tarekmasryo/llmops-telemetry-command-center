import pytest

from src.data import load_bundle, validate_bundle_integrity


def test_load_bundle_validates_complete_release_contract():
    bundle = load_bundle()
    assert len(bundle.interactions) == 9000
    assert bundle.interactions["interaction_id"].is_unique
    assert not bundle.sessions.empty
    assert not bundle.users.empty
    assert not bundle.prompts_lookup.empty
    assert not bundle.instruction_samples.empty
    assert bundle.prompts_lookup["prompt_id"].is_unique
    assert bundle.instruction_samples["sample_id"].is_unique
    assert not bundle.routing_summary.empty
    assert not bundle.triage_curve.empty


def test_bundle_integrity_rejects_orphaned_triage_actions():
    bundle = load_bundle()
    broken_actions = bundle.triage_actions.copy()
    broken_actions.loc[broken_actions.index[0], "interaction_id"] = "missing_interaction"
    broken_bundle = bundle.__class__(
        interactions=bundle.interactions,
        sessions=bundle.sessions,
        users=bundle.users,
        prompts_lookup=bundle.prompts_lookup,
        instruction_samples=bundle.instruction_samples,
        routing_summary=bundle.routing_summary,
        routing_policy=bundle.routing_policy,
        drift_report=bundle.drift_report,
        triage_actions=broken_actions,
        triage_baselines=bundle.triage_baselines,
        triage_curve=bundle.triage_curve,
        triage_policy=bundle.triage_policy,
        decision_artifact=bundle.decision_artifact,
    )
    with pytest.raises(ValueError, match="triage_actions_preview"):
        validate_bundle_integrity(broken_bundle)


def test_bundle_integrity_rejects_orphaned_prompt_references():
    bundle = load_bundle()
    broken_interactions = bundle.interactions.copy()
    broken_interactions.loc[broken_interactions.index[0], "prompt_id"] = "missing_prompt"
    broken_bundle = bundle.__class__(
        interactions=broken_interactions,
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
    with pytest.raises(ValueError, match="prompts_lookup"):
        validate_bundle_integrity(broken_bundle)


def test_bundle_integrity_rejects_orphaned_instruction_samples():
    bundle = load_bundle()
    broken_samples = bundle.instruction_samples.copy()
    broken_samples.loc[broken_samples.index[0], "interaction_id"] = "missing_interaction"
    broken_bundle = bundle.__class__(
        interactions=bundle.interactions,
        sessions=bundle.sessions,
        users=bundle.users,
        prompts_lookup=bundle.prompts_lookup,
        instruction_samples=broken_samples,
        routing_summary=bundle.routing_summary,
        routing_policy=bundle.routing_policy,
        drift_report=bundle.drift_report,
        triage_actions=bundle.triage_actions,
        triage_baselines=bundle.triage_baselines,
        triage_curve=bundle.triage_curve,
        triage_policy=bundle.triage_policy,
        decision_artifact=bundle.decision_artifact,
    )
    with pytest.raises(ValueError, match="instruction_tuning_samples"):
        validate_bundle_integrity(broken_bundle)
