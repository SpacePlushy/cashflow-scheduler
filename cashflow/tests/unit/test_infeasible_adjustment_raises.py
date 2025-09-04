import pytest

from cashflow.io.store import load_plan
from cashflow.engines.dp import solve
from cashflow.core.ledger import build_ledger
from cashflow.core.model import Adjustment


def test_too_negative_adjustment_causes_infeasibility_with_locked_day():
    plan = load_plan("plan.json")
    base_sched = solve(plan)
    base_ledg = build_ledger(plan, base_sched.actions)

    day = 10
    closing = base_ledg[day - 1].closing_cents
    # Force negative closing by subtracting closing + 1 cent; lock day action
    delta = -(closing + 1)
    plan2 = load_plan("plan.json")
    plan2.actions = base_sched.actions[:day] + [None] * (30 - day)
    plan2.manual_adjustments = plan2.manual_adjustments + [Adjustment(day=day, amount_cents=delta, note="force infeasible")]

    with pytest.raises(RuntimeError):
        solve(plan2)

