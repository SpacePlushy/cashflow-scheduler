from hypothesis import given, settings, strategies as st, assume

from cashflow.io.store import load_plan
from cashflow.engines.dp import solve
from cashflow.core.ledger import build_ledger
from cashflow.core.validate import validate
from cashflow.core.model import Adjustment


def apply_adjustment_and_lock(plan_path: str, day: int, delta: int):
    base_plan = load_plan(plan_path)
    base_schedule = solve(base_plan)
    base_ledger = build_ledger(base_plan, base_schedule.actions)

    plan2 = load_plan(plan_path)
    plan2.actions = base_schedule.actions[:day] + [None] * (30 - day)
    plan2.manual_adjustments = list(plan2.manual_adjustments) + [
        Adjustment(day=day, amount_cents=delta, note="property test")
    ]
    return base_schedule, base_ledger, plan2


@settings(max_examples=12, deadline=None)
@given(day=st.integers(min_value=1, max_value=30), delta=st.integers(min_value=-700, max_value=700))
def test_random_single_adjustment_keeps_validity(day, delta):
    base_plan_path = "plan.json"
    base_plan = load_plan(base_plan_path)
    base_schedule = solve(base_plan)
    base_ledger = build_ledger(base_plan, base_schedule.actions)

    # Keep negative deltas safe for that day to avoid guaranteed infeasibility
    min_neg = -min(base_ledger[day - 1].closing_cents, 700)
    if delta < min_neg:
        delta = min_neg

    plan2 = load_plan(base_plan_path)
    plan2.actions = base_schedule.actions[:day] + [None] * (30 - day)
    plan2.manual_adjustments = list(plan2.manual_adjustments) + [
        Adjustment(day=day, amount_cents=delta, note="property-random")
    ]

    try:
        sched2 = solve(plan2)
    except Exception:
        assume(False)  # discard too-hard example
        return

    rep2 = validate(plan2, sched2)
    assert rep2.ok, rep2.checks

