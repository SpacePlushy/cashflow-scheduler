from cashflow.io.store import load_plan
from cashflow.engines.dp import solve
from cashflow.core.ledger import build_ledger
from cashflow.core.validate import validate
from cashflow.core.model import Adjustment


def make_locked_plan_with_adjustment(orig_plan, schedule, day, delta_cents):
    plan = load_plan("plan.json")  # fresh copy
    # lock prefix actions through day
    plan.actions = schedule.actions[:day] + [None] * (30 - day)
    # append manual adjustment on the specified day
    plan.manual_adjustments = list(plan.manual_adjustments) + [
        Adjustment(day=day, amount_cents=delta_cents, note="test EOD override")
    ]
    return plan


def test_resume_after_positive_adjustment_multiple_days():
    base_plan = load_plan("plan.json")
    base_schedule = solve(base_plan)
    base_ledger = build_ledger(base_plan, base_schedule.actions)

    for day in [5, 12, 20, 29]:
        delta = 500  # +$5.00 adjustment
        new_eod = base_ledger[day - 1].closing_cents + delta

        plan2 = make_locked_plan_with_adjustment(base_plan, base_schedule, day, delta)
        sched2 = solve(plan2)
        rep2 = validate(plan2, sched2)
        assert rep2.ok, rep2.checks

        ledg2 = build_ledger(plan2, sched2.actions)

        # Historical prefix days unchanged
        for t in range(1, day):
            assert ledg2[t - 1].closing_cents == base_ledger[t - 1].closing_cents
            assert sched2.actions[t - 1] == base_schedule.actions[t - 1]

        # Day d closing matches requested new EOD; action is locked
        assert ledg2[day - 1].closing_cents == new_eod
        assert sched2.actions[day - 1] == base_schedule.actions[day - 1]


def test_resume_after_negative_adjustment_safe():
    base_plan = load_plan("plan.json")
    base_schedule = solve(base_plan)
    base_ledger = build_ledger(base_plan, base_schedule.actions)

    day = 25
    # Safe negative adjustment that keeps day closing non-negative
    assert base_ledger[day - 1].closing_cents > 1000
    delta = -500  # -$5.00
    new_eod = base_ledger[day - 1].closing_cents + delta

    plan2 = make_locked_plan_with_adjustment(base_plan, base_schedule, day, delta)
    sched2 = solve(plan2)
    rep2 = validate(plan2, sched2)
    assert rep2.ok, rep2.checks

    ledg2 = build_ledger(plan2, sched2.actions)
    # Days before day unchanged
    for t in range(1, day):
        assert ledg2[t - 1].closing_cents == base_ledger[t - 1].closing_cents
        assert sched2.actions[t - 1] == base_schedule.actions[t - 1]
    # Day closing matches new_eod
    assert ledg2[day - 1].closing_cents == new_eod
    assert sched2.actions[day - 1] == base_schedule.actions[day - 1]
