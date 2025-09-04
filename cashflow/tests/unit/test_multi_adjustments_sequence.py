from cashflow.io.store import load_plan
from cashflow.engines.dp import solve
from cashflow.core.ledger import build_ledger
from cashflow.core.model import Adjustment
from cashflow.core.validate import validate


def test_three_sequential_adjustments_with_locks():
    plan = load_plan("plan.json")
    sched0 = solve(plan)
    ledg0 = build_ledger(plan, sched0.actions)

    # 1) Adjust day 6 by +$3.00
    plan1 = load_plan("plan.json")
    plan1.actions = sched0.actions[:6] + [None] * (30 - 6)
    plan1.manual_adjustments = plan1.manual_adjustments + [Adjustment(day=6, amount_cents=300, note="adj1")]
    sched1 = solve(plan1)
    ledg1 = build_ledger(plan1, sched1.actions)
    assert ledg1[5].closing_cents == ledg0[5].closing_cents + 300
    for t in range(1, 6):
        assert ledg1[t - 1].closing_cents == ledg0[t - 1].closing_cents

    # 2) Adjust day 14 by -$5.00
    plan2 = load_plan("plan.json")
    plan2.actions = sched1.actions[:14] + [None] * (30 - 14)
    # carry prior adjustments
    plan2.manual_adjustments = [Adjustment(day=6, amount_cents=300, note="adj1")]
    plan2.manual_adjustments.append(Adjustment(day=14, amount_cents=-500, note="adj2"))
    sched2 = solve(plan2)
    ledg2 = build_ledger(plan2, sched2.actions)
    assert ledg2[13].closing_cents == ledg1[13].closing_cents - 500
    for t in range(1, 14):
        assert ledg2[t - 1].closing_cents == ledg1[t - 1].closing_cents

    # 3) Adjust day 25 by +$2.00
    plan3 = load_plan("plan.json")
    plan3.actions = sched2.actions[:25] + [None] * (30 - 25)
    plan3.manual_adjustments = [
        Adjustment(day=6, amount_cents=300, note="adj1"),
        Adjustment(day=14, amount_cents=-500, note="adj2"),
        Adjustment(day=25, amount_cents=200, note="adj3"),
    ]
    sched3 = solve(plan3)
    rep3 = validate(plan3, sched3)
    assert rep3.ok
    ledg3 = build_ledger(plan3, sched3.actions)
    assert ledg3[24].closing_cents == ledg2[24].closing_cents + 200
    for t in range(1, 25):
        assert ledg3[t - 1].closing_cents == ledg2[t - 1].closing_cents
