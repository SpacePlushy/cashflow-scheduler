from __future__ import annotations

import json
from ._shared import _load_default_plan, dp_solve, validate, _cors_headers, handle_preflight


def handler(request):
    pf = handle_preflight(request)
    if pf is not None:
        return pf
    plan = _load_default_plan()
    schedule = dp_solve(plan)
    report = validate(plan, schedule)
    body = json.dumps({
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
    })
    origin = None
    try:
        origin = request.headers.get("origin")  # type: ignore[attr-defined]
    except Exception:
        pass
    return body, 200, _cors_headers(origin)
