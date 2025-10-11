import pytest

from cashflow.io.store import load_plan
from cashflow.engines.dp import solve
from cashflow.core.ledger import build_ledger
from cashflow.core.model import Adjustment, SHIFT_NET_CENTS
from cashflow.core.validate import validate


def _tail_extra_capacity(actions, start_day_exclusive):
    # Optimistic capacity (ignores Off-Off). Not used for final negative bound.
    cap = 0
    for t in range(start_day_exclusive + 1, 31):
        base_net = SHIFT_NET_CENTS[actions[t - 1]]
        cap += 12000 - base_net
    return cap


def test_large_positive_adjustments_multiple_days():
    plan = load_plan("plan.json")
    base_sched = solve(plan)
    base_ledg = build_ledger(plan, base_sched.actions)

    # With Spark-only $100 steps, use multiples of $100 for feasibility
    cases = {
        4: 10000,   # +$100
        10: 10000,  # +$100
        17: 20000,  # +$200
        24: 30000,  # +$300
    }

    for day, delta in cases.items():
        plan2 = load_plan("plan.json")
        plan2.actions = base_sched.actions[:day] + [None] * (30 - day)
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
        # edited day closing increased by delta
        assert ledg2[day - 1].closing_cents == base_ledg[day - 1].closing_cents + delta


def test_day30_large_positive_adjustment_with_flexible_action():
    plan = load_plan("plan.json")
    base_sched = solve(plan)
    base_ledg = build_ledger(plan, base_sched.actions)

    day = 30
    delta = 20000  # +$200 (Spark-compatible step)

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
    # Day 30 closing remains within band (solver can re-balance tail days)
    assert rep2.ok
