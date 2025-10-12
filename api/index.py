from __future__ import annotations

import os
from typing import Any, Mapping, cast

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from ._shared import (
    _load_default_plan,
    dp_solve,
    validate,
)
from cashflow.io.render import render_markdown, render_csv, render_json
from cashflow.core.ledger import build_ledger
from cashflow.core.model import Adjustment, Plan
from cashflow.io.store import plan_from_dict
from cashflow.engines.cpsat import solve_with_diagnostics

# Configure CORS origins from environment or use defaults
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "*").split(",")

app = FastAPI(title="Cashflow API (Serverless)")
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=True,
)


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/solve")
async def solve(req: Request):
    body = await _read_body(req)
    try:
        plan_payload = _extract_plan_payload(body)
        plan = _plan_from_payload(plan_payload)
    except ValueError as exc:
        return JSONResponse({"error": str(exc)}, status_code=400)

    # Extract solver preference from request body
    solver_preference = body.get("solver", "cpsat")  # default to cpsat

    if solver_preference == "dp":
        # Use DP solver directly
        schedule = dp_solve(plan)
        from cashflow.core.ledger import build_ledger
        if not schedule.ledger:
            schedule.ledger = build_ledger(plan, schedule.actions)
        # Create a result-like structure for DP
        class DPResult:
            def __init__(self, schedule):
                self.schedule = schedule
                self.solver = "dp"
                self.statuses = []
                self.solve_seconds = 0.0
                self.fallback_reason = None
        result = DPResult(schedule)
    else:
        # Use CP-SAT with DP fallback
        result = solve_with_diagnostics(plan)
        schedule = result.schedule

    report = validate(plan, schedule)
    return JSONResponse(_schedule_payload(schedule, report, result))


@app.post("/set_eod")
async def set_eod(req: Request):
    body = await _read_body(req)
    day = int(body.get("day", 0))
    eod_amount = float(body.get("eod_amount", 0))
    if not (1 <= day <= 30):
        return JSONResponse({"error": "day must be in 1..30"}, status_code=400)

    try:
        plan = _plan_from_payload(body.get("plan"))
    except ValueError as exc:
        return JSONResponse({"error": str(exc)}, status_code=400)

    # Extract solver preference from request body
    solver_preference = body.get("solver", "cpsat")  # default to cpsat

    baseline = dp_solve(plan)
    base_ledger = build_ledger(plan, baseline.actions)
    current_eod = base_ledger[day - 1].closing_cents
    desired_cents = int(round(eod_amount * 100))
    delta = desired_cents - current_eod

    plan.actions = baseline.actions[:day] + [None] * (30 - day)
    plan.manual_adjustments = list(plan.manual_adjustments) + [
        Adjustment(day=day, amount_cents=delta, note="api set-eod"),
    ]

    if solver_preference == "dp":
        # Use DP solver directly
        schedule = dp_solve(plan)
        if not schedule.ledger:
            schedule.ledger = build_ledger(plan, schedule.actions)
        # Create a result-like structure for DP
        class DPResult:
            def __init__(self, schedule):
                self.schedule = schedule
                self.solver = "dp"
                self.statuses = []
                self.solve_seconds = 0.0
                self.fallback_reason = None
        result = DPResult(schedule)
    else:
        # Use CP-SAT with DP fallback
        result = solve_with_diagnostics(plan)
        schedule = result.schedule

    report = validate(plan, schedule)

    return JSONResponse(_schedule_payload(schedule, report, result))


@app.post("/export")
async def export(req: Request):
    body = await _read_body(req)
    fmt = str(body.get("format", "md")).lower()
    if fmt not in ("md", "csv", "json"):
        return JSONResponse({"error": "format must be md|csv|json"}, status_code=400)

    try:
        plan = _plan_from_payload(body.get("plan"))
    except ValueError as exc:
        return JSONResponse({"error": str(exc)}, status_code=400)

    # Extract solver preference from request body
    solver_preference = body.get("solver", "cpsat")  # default to cpsat

    if solver_preference == "dp":
        # Use DP solver directly
        schedule = dp_solve(plan)
        if not schedule.ledger:
            from cashflow.core.ledger import build_ledger
            schedule.ledger = build_ledger(plan, schedule.actions)
    else:
        # Use CP-SAT with DP fallback
        result = solve_with_diagnostics(plan)
        schedule = result.schedule

    if fmt == "md":
        content = render_markdown(schedule)
    elif fmt == "csv":
        content = render_csv(schedule)
    else:
        content = render_json(schedule)
    return JSONResponse({"format": fmt, "content": content})


async def _read_body(req: Request) -> Mapping[str, Any]:
    try:
        payload = await req.json()
    except Exception:
        return {}
    if isinstance(payload, Mapping):
        return payload
    return {}


def _extract_plan_payload(body: Mapping[str, Any]) -> Mapping[str, Any] | None:
    if "plan" in body and isinstance(body["plan"], Mapping):
        return cast(Mapping[str, Any], body["plan"])
    if _looks_like_plan(body):
        return body
    return None


def _looks_like_plan(obj: Mapping[str, Any]) -> bool:
    required = {"start_balance", "target_end", "band", "rent_guard"}
    return required.issubset(obj.keys())


def _plan_from_payload(payload: Mapping[str, Any] | None) -> Plan:
    if payload is None:
        return _load_default_plan()
    return plan_from_dict(payload)


def _schedule_payload(schedule, report, diagnostics=None):
    payload = {
        "actions": schedule.actions,
        "objective": list(schedule.objective),
        "final_closing": _cents_to_str(schedule.ledger[-1].closing_cents),
        "ledger": [
            {
                "day": row.day,
                "opening": _cents_to_str(row.opening_cents),
                "deposits": _cents_to_str(row.deposit_cents),
                "action": row.action,
                "net": _cents_to_str(row.net_cents),
                "bills": _cents_to_str(row.bills_cents),
                "closing": _cents_to_str(row.closing_cents),
            }
            for row in schedule.ledger
        ],
        "checks": report.checks,
    }
    if diagnostics is not None:
        payload["solver"] = {
            "name": diagnostics.solver,
            "statuses": diagnostics.statuses,
            "seconds": diagnostics.solve_seconds,
        }
        if diagnostics.fallback_reason:
            payload["solver"]["fallback_reason"] = diagnostics.fallback_reason
    return payload


def _cents_to_str(amount: int) -> str:
    return f"{amount // 100}.{amount % 100:02d}"
