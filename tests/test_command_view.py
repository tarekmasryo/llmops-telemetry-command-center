from src.models import RoutingTruth
from src.views.command import CommandViewMixin


class CommandHarness(CommandViewMixin):
    pass


def test_operations_checklist_holds_when_routing_artifact_rejects_rollout() -> None:
    harness = CommandHarness()
    harness.truth = RoutingTruth(
        status="candidate_failed_backtest",
        recommendation="do_not_roll_out_keep_baseline",
        delta=0.0,
        window="held_out",
        baseline_unit_cost=1.0,
        policy_unit_cost=1.2,
    )

    checklist = harness._operations_checklist()

    assert checklist.iloc[0]["action"] == "Hold routing rollout"
    assert "does not support rollout" in checklist.iloc[0]["reason"]


def test_operations_checklist_is_not_hardcoded_to_hold() -> None:
    harness = CommandHarness()
    harness.truth = RoutingTruth(
        status="candidate_passed_backtest",
        recommendation="review_rollout_readiness",
        delta=-0.1,
        window="held_out",
        baseline_unit_cost=1.0,
        policy_unit_cost=0.9,
    )

    checklist = harness._operations_checklist()

    assert checklist.iloc[0]["action"] == "Review routing rollout readiness"
    assert "does not explicitly reject rollout" in checklist.iloc[0]["reason"]
