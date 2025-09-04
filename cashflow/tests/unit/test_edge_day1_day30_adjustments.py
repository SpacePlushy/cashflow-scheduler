from cashflow.io.store import load_plan
from cashflow.engines.dp import solve
from cashflow.core.ledger import build_ledger
from cashflow.core.model import Adjustment
from cashflow.core.validate import validate


def test_day1_and_day30_small_adjustments():
    plan = load_plan("plan.json")
    base_sched = solve(plan)
    base_ledg = build_ledger(plan, base_sched.actions)

    # Day 1 +$1.00
    plan1 = load_plan("plan.json")
    plan1.actions = base_sched.actions[:1] + [None] * 29
    plan1.manual_adjustments = plan1.manual_adjustments + [
        Adjustment(day=1, amount_cents=100, note="d1+")
    ]
    s1 = solve(plan1)
    r1 = validate(plan1, s1)
    assert r1.ok
    l1 = build_ledger(plan1, s1.actions)
    assert l1[0].closing_cents == base_ledg[0].closing_cents + 100

    # Day 30 -$1.00 (should still satisfy rent guard since slack is large)
    plan2 = load_plan("plan.json")
    plan2.actions = base_sched.actions[:30]
    plan2.manual_adjustments = plan2.manual_adjustments + [
        Adjustment(day=30, amount_cents=-100, note="d30-")
    ]
    s2 = solve(plan2)
    r2 = validate(plan2, s2)
    assert r2.ok
    l2 = build_ledger(plan2, s2.actions)
    assert l2[29].closing_cents == base_ledg[29].closing_cents - 100
