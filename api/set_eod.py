from __future__ import annotations

import json
from typing import Any, Dict

from cashflow.core.model import Adjustment
from cashflow.core.ledger import build_ledger
from cashflow.engines.dp import solve as dp_solve
from cashflow.core.validate import validate
from ._shared import _load_default_plan


def handler(request):
    try:
        body = request.get_json() if hasattr(request, "get_json") else json.loads(request.body or "{}")
    except Exception:
        body = {}
    day = int(body.get("day", 0))
    eod_amount = float(body.get("eod_amount", 0))
    if not (1 <= day <= 30):
        return json.dumps({"error": "day must be in 1..30"}), 400, {"Content-Type": "application/json"}

    plan = _load_default_plan()
    # Baseline solve to know current closing and actions
    baseline = dp_solve(plan)
    base_ledger = build_ledger(plan, baseline.actions)
    current_eod = base_ledger[day - 1].closing_cents
    desired_cents = int(round(eod_amount * 100))
    delta = desired_cents - current_eod

    # Lock prefix and add adjustment
    plan.actions = baseline.actions[:day] + [None] * (30 - day)
    plan.manual_adjustments = list(plan.manual_adjustments) + [
        Adjustment(day=day, amount_cents=delta, note="api set-eod"),
    ]

    # Solve again
    schedule = dp_solve(plan)
    report = validate(plan, schedule)

    result: Dict[str, Any] = {
        "actions": schedule.actions,
        "objective": list(schedule.objective),
        "final_closing": f"{schedule.ledger[-1].closing_cents//100}.{schedule.ledger[-1].closing_cents%100:02d}",
        "ledger": [
            {
                "day": r.day,
                "opening": f"{r.opening_cents//100}.{r.opening_cents%100:02d}",
                "deposits": f"{r.deposit_cents//100}.{r.deposit_cents%100:02d}",
                "action": r.action,
                "net": f"{r.net_cents//100}.{r.net_cents%100:02d}",
                "bills": f"{r.bills_cents//100}.{r.bills_cents%100:02d}",
                "closing": f"{r.closing_cents//100}.{r.closing_cents%100:02d}",
            }
            for r in schedule.ledger
        ],
        "checks": report.checks,
    }
    return json.dumps(result), 200, {"Content-Type": "application/json"}

