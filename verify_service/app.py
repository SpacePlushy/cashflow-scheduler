from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from cashflow.engines.dp import solve as dp_solve
from cashflow.engines.cpsat import verify_lex_optimal
from cashflow.io.store import load_plan
from cashflow.core.model import Plan, Bill, Deposit, Adjustment, to_cents


def _embedded_plan() -> Plan:
    deposits = [
        Deposit(day=11, amount_cents=to_cents(1021.0)),
        Deposit(day=25, amount_cents=to_cents(1021.0)),
    ]
    bills = [
        Bill(1, "Auto Insurance", to_cents(177.0)),
        Bill(2, "YouTube Premium", to_cents(8.0)),
        Bill(5, "Groceries", to_cents(112.5)),
        Bill(5, "Weed", to_cents(20.0)),
        Bill(8, "Paramount Plus", to_cents(12.0)),
        Bill(8, "iPad AppleCare", to_cents(8.49)),
        Bill(10, "Streaming Svcs", to_cents(230.0)),
        Bill(11, "Cat Food", to_cents(40.0)),
        Bill(12, "Groceries", to_cents(112.5)),
        Bill(12, "Weed", to_cents(20.0)),
        Bill(14, "iPad AppleCare", to_cents(8.49)),
        Bill(16, "Cat Food", to_cents(40.0)),
        Bill(17, "Car Payment", to_cents(463.0)),
        Bill(19, "Groceries", to_cents(112.5)),
        Bill(19, "Weed", to_cents(20.0)),
        Bill(22, "Cell Phone", to_cents(177.0)),
        Bill(23, "Cat Food", to_cents(40.0)),
        Bill(24, "AI Subscription", to_cents(220.0)),
        Bill(25, "Electric", to_cents(139.0)),
        Bill(25, "Ring Subscription", to_cents(10.0)),
        Bill(26, "Groceries", to_cents(112.5)),
        Bill(26, "Weed", to_cents(20.0)),
        Bill(28, "iPhone AppleCare", to_cents(13.49)),
        Bill(29, "Internet", to_cents(30.0)),
        Bill(29, "Cat Food", to_cents(40.0)),
        Bill(30, "Rent", to_cents(1636.0)),
    ]
    return Plan(
        start_balance_cents=to_cents(90.5),
        target_end_cents=to_cents(490.5),
        band_cents=to_cents(25.0),
        rent_guard_cents=to_cents(1636.0),
        deposits=deposits,
        bills=bills,
        actions=[None] * 30,
        manual_adjustments=[],
        locks=[],
        metadata={"version": "1.0.0", "source": "embedded"},
    )


def load_default_plan() -> Plan:
    try:
        return load_plan("plan.json")
    except Exception:
        return _embedded_plan()


class VerifyOut(BaseModel):
    ok: bool
    dp_obj: list[int]
    cp_obj: list[int]
    detail: str


app = FastAPI(title="Cashflow Verify Service")

# Allow browser calls from your UI origins (update as needed)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "*",  # TODO: replace with your Vercel UI origin for production
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/")
def root():
    return {"service": "cashflow-verify", "status": "ok"}


@app.post("/verify", response_model=VerifyOut)
def verify():
    plan = load_default_plan()
    schedule = dp_solve(plan)
    report = verify_lex_optimal(plan, schedule)
    return VerifyOut(
        ok=report.ok,
        dp_obj=list(report.dp_obj),
        cp_obj=list(report.cp_obj),
        detail=report.detail,
    )
