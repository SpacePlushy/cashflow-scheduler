import pytest

from cashflow.io.store import load_plan
from cashflow.engines.dp import solve
from cashflow.core.ledger import build_ledger
from cashflow.core.model import Adjustment, SHIFT_NET_CENTS, SPARK_ACTION
from cashflow.core.validate import validate


SPARK_PAYOUT = SHIFT_NET_CENTS[SPARK_ACTION]


def test_large_positive_adjustments_multiple_days():
    plan = load_plan("plan.json")
    base_sched = solve(plan)
    base_ledg = build_ledger(plan, base_sched.actions)

    cases = {
        4: SPARK_PAYOUT,  # +$100
        10: 2 * SPARK_PAYOUT,  # +$200
        17: 3 * SPARK_PAYOUT,  # +$300
        24: 2 * SPARK_PAYOUT,  # +$200
    }

    for day, delta in cases.items():
        plan2 = load_plan("plan.json")
        prefix = base_sched.actions[: day - 1]
        plan2.actions = prefix + [None] * (31 - day)
        plan2.manual_adjustments = plan2.manual_adjustments + [
            Adjustment(day=day, amount_cents=delta, note="large+")
        ]
        sched2 = solve(plan2)
        rep2 = validate(plan2, sched2)
        assert rep2.ok, rep2.checks
        ledg2 = build_ledger(plan2, sched2.actions)
        # prefix unchanged
        for t in range(1, day):
            assert ledg2[t - 1].closing_cents == base_ledg[t - 1].closing_cents
            assert sched2.actions[t - 1] == base_sched.actions[t - 1]
        # manual adjustment applied as a deposit on the edited day
        assert (
            ledg2[day - 1].deposit_cents
            == base_ledg[day - 1].deposit_cents + delta
        )
        # schedule should differ to stay within the tight target band
        assert sched2.actions != base_sched.actions


def test_large_negative_adjustments_raise_without_capacity():
    plan = load_plan("plan.json")
    base_sched = solve(plan)
    base_ledg = build_ledger(plan, base_sched.actions)

    for day in [10, 20]:
        if base_ledg[day - 1].closing_cents <= SPARK_PAYOUT:
            pytest.skip(f"insufficient balance slack on day {day}")
        delta = -SPARK_PAYOUT

        plan2 = load_plan("plan.json")
        prefix = base_sched.actions[: day - 1]
        plan2.actions = prefix + [None] * (31 - day)
        plan2.manual_adjustments = plan2.manual_adjustments + [
            Adjustment(day=day, amount_cents=delta, note="large-")
        ]
        with pytest.raises(RuntimeError):
            solve(plan2)


def test_day30_large_positive_adjustment_with_flexible_action():
    plan = load_plan("plan.json")
    base_sched = solve(plan)
    base_ledg = build_ledger(plan, base_sched.actions)

    day = 30
    delta = 2 * SPARK_PAYOUT  # +$200

    plan2 = load_plan("plan.json")
    # lock only up to day 27; allow days 28-30 to adjust to absorb +$250
    plan2.actions = base_sched.actions[:27] + [None, None, None]
    plan2.manual_adjustments = plan2.manual_adjustments + [
        Adjustment(day=day, amount_cents=delta, note="d30 large+")
    ]
    sched2 = solve(plan2)
    rep2 = validate(plan2, sched2)
    assert rep2.ok, rep2.checks
    ledg2 = build_ledger(plan2, sched2.actions)
    # Days 1..27 unchanged (we allowed 28-30 to flex)
    for t in range(1, 28):
        assert ledg2[t - 1].closing_cents == base_ledg[t - 1].closing_cents
        assert sched2.actions[t - 1] == base_sched.actions[t - 1]
    # Day 30 tail should adjust to stay within band after the manual deposit
    assert sched2.actions[27:] != base_sched.actions[27:]
