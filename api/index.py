from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from ._shared import (
    _load_default_plan,
    dp_solve,
    validate,
    render_markdown,
    render_csv,
    render_json,
)
from cashflow.core.ledger import build_ledger
from cashflow.core.model import Adjustment


app = FastAPI(title="Cashflow API (Serverless)")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/solve")
async def solve():
    plan = _load_default_plan()
    schedule = dp_solve(plan)
    report = validate(plan, schedule)

    payload = {
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
    return JSONResponse(payload)


@app.post("/set_eod")
async def set_eod(req: Request):
    body = await req.json()
    day = int(body.get("day", 0))
    eod_amount = float(body.get("eod_amount", 0))
    if not (1 <= day <= 30):
        return JSONResponse({"error": "day must be in 1..30"}, status_code=400)

    plan = _load_default_plan()
    baseline = dp_solve(plan)
    base_ledger = build_ledger(plan, baseline.actions)
    current_eod = base_ledger[day - 1].closing_cents
    desired_cents = int(round(eod_amount * 100))
    delta = desired_cents - current_eod

    plan.actions = baseline.actions[:day] + [None] * (30 - day)
    plan.manual_adjustments = list(plan.manual_adjustments) + [
        Adjustment(day=day, amount_cents=delta, note="api set-eod"),
    ]
    schedule = dp_solve(plan)
    report = validate(plan, schedule)

    payload = {
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
    return JSONResponse(payload)


@app.post("/export")
async def export(req: Request):
    body = await req.json()
    fmt = str(body.get("format", "md")).lower()
    if fmt not in ("md", "csv", "json"):
        return JSONResponse({"error": "format must be md|csv|json"}, status_code=400)
    plan = _load_default_plan()
    schedule = dp_solve(plan)
    if fmt == "md":
        content = render_markdown(schedule)
    elif fmt == "csv":
        content = render_csv(schedule)
    else:
        content = render_json(schedule)
    return JSONResponse({"format": fmt, "content": content})

