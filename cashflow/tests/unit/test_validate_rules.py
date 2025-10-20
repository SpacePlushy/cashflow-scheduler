from cashflow.io.store import load_plan
from cashflow.engines.dp import solve
from cashflow.core.validate import validate


def test_validation_rules_hold():
    plan = load_plan("plan.json")
    schedule = solve(plan)
    report = validate(plan, schedule)

    # Global ok
    assert report.ok, report.checks

    # Day 1 must be Spark
    assert schedule.actions[0] == "Spark"
