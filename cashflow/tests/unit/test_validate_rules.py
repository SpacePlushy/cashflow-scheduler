from cashflow.io.store import load_plan
from cashflow.engines.dp import solve
from cashflow.core.model import SHIFT_NET_CENTS, SPARK_ACTION
from cashflow.core.validate import validate


def _has_off_off(seq):
    for i in range(len(seq) - 1):
        if seq[i] == "O" and seq[i + 1] == "O":
            return True
    return False


def test_validation_rules_hold():
    plan = load_plan("plan.json")
    schedule = solve(plan)
    report = validate(plan, schedule)

    # Global ok
    assert report.ok, report.checks

    # Spark actions should be limited to Off/Spark and include Spark work
    assert set(schedule.actions) <= set(SHIFT_NET_CENTS.keys())
    assert SPARK_ACTION in schedule.actions

    # Off-Off windows across [1..7] and [24..30]
    actions = schedule.actions
    assert _has_off_off(actions[0:7])
    assert _has_off_off(actions[23:30])
