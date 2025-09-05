from __future__ import annotations

from decimal import Decimal
from pathlib import Path
from typing import List, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, model_validator

from .. import __version__
from ..core.model import Adjustment as CFAdjustment
from ..core.model import Bill as CFBill
from ..core.model import Deposit as CFDeposit
from ..core.model import Plan as CFPlan
from ..core.ledger import build_ledger
from ..engines.dp import solve as dp_solve
from ..engines.cpsat import verify_lex_optimal, enumerate_ties
from ..io.store import load_plan, save_plan
from ..io.render import render_markdown, render_csv, render_json


# -----------------
# Pydantic DTOs
# -----------------


def to_cents(amount: float | int | str | Decimal) -> int:
    d = Decimal(str(amount)).quantize(Decimal("0.01"))
    return int(d * 100)


def cents_to_str(cents: int) -> str:
    sign = "-" if cents < 0 else ""
    cents_abs = abs(cents)
    return f"{sign}{cents_abs // 100}.{cents_abs % 100:02d}"


class BillIn(BaseModel):
    day: int
    name: str
    amount: float


class DepositIn(BaseModel):
    day: int
    amount: float


class AdjustmentIn(BaseModel):
    day: int
    amount: float
    note: str = ""


def _empty_actions() -> List[Optional[str]]:
    return [None] * 30


class PlanIn(BaseModel):
    start_balance: float
    target_end: float
    band: float
    rent_guard: float
    deposits: List[DepositIn] = Field(default_factory=list)
    bills: List[BillIn] = Field(default_factory=list)
    actions: List[Optional[str]] = Field(default_factory=_empty_actions)
    manual_adjustments: List[AdjustmentIn] = Field(default_factory=list)
    metadata: dict = Field(default_factory=dict)

    @model_validator(mode="after")
    def _check_actions_len(self):  # type: ignore[no-redef]
        if len(self.actions) != 30:
            raise ValueError("actions must be length 30")
        return self


class LedgerRowOut(BaseModel):
    day: int
    opening: str
    deposits: str
    action: str
    net: str
    bills: str
    closing: str


class SolveResultOut(BaseModel):
    actions: List[str]
    objective: List[int]
    final_closing: str
    ledger: List[LedgerRowOut]
    checks: List[tuple[str, bool, str]]


class HealthOut(BaseModel):
    status: str
    version: str


# -----------------
# Working state
# -----------------


WORKING_PLAN: Optional[CFPlan] = None
PLAN_PATH: Path = Path.cwd() / "plan.json"


def _ensure_plan() -> CFPlan:
    global WORKING_PLAN
    if WORKING_PLAN is None:
        try:
            WORKING_PLAN = load_plan(PLAN_PATH)
        except Exception as e:  # pragma: no cover - depends on environment
            raise HTTPException(
                status_code=500, detail=f"Failed to load plan.json: {e}"
            )
    return WORKING_PLAN


def _plan_from_in(p: PlanIn) -> CFPlan:
    deposits = [
        CFDeposit(day=d.day, amount_cents=to_cents(d.amount)) for d in p.deposits
    ]
    bills = [
        CFBill(day=b.day, name=b.name, amount_cents=to_cents(b.amount)) for b in p.bills
    ]
    adjs = [
        CFAdjustment(day=a.day, amount_cents=to_cents(a.amount), note=a.note)
        for a in p.manual_adjustments
    ]
    return CFPlan(
        start_balance_cents=to_cents(p.start_balance),
        target_end_cents=to_cents(p.target_end),
        band_cents=to_cents(p.band),
        rent_guard_cents=to_cents(p.rent_guard),
        deposits=deposits,
        bills=bills,
        actions=p.actions,  # type: ignore
        manual_adjustments=adjs,
        locks=[],
        metadata=dict(p.metadata),
    )


def _plan_to_out(p: CFPlan) -> PlanIn:
    return PlanIn(
        start_balance=float(cents_to_str(p.start_balance_cents)),
        target_end=float(cents_to_str(p.target_end_cents)),
        band=float(cents_to_str(p.band_cents)),
        rent_guard=float(cents_to_str(p.rent_guard_cents)),
        deposits=[
            DepositIn(day=d.day, amount=float(cents_to_str(d.amount_cents)))
            for d in p.deposits
        ],
        bills=[
            BillIn(day=b.day, name=b.name, amount=float(cents_to_str(b.amount_cents)))
            for b in p.bills
        ],
        actions=p.actions,
        manual_adjustments=[
            AdjustmentIn(
                day=a.day, amount=float(cents_to_str(a.amount_cents)), note=a.note
            )
            for a in p.manual_adjustments
        ],
        metadata=p.metadata,
    )


def _solve_and_validate(plan: CFPlan):
    schedule = dp_solve(plan)
    # build checks via validate in CLI style
    from ..core.validate import validate

    report = validate(plan, schedule)
    ledger_rows = []
    for r in schedule.ledger:
        ledger_rows.append(
            LedgerRowOut(
                day=r.day,
                opening=cents_to_str(r.opening_cents),
                deposits=cents_to_str(r.deposit_cents),
                action=r.action,
                net=cents_to_str(r.net_cents),
                bills=cents_to_str(r.bills_cents),
                closing=cents_to_str(r.closing_cents),
            )
        )
    return SolveResultOut(
        actions=schedule.actions,
        objective=list(schedule.objective),
        final_closing=cents_to_str(schedule.final_closing_cents),
        ledger=ledger_rows,
        checks=report.checks,
    )


app = FastAPI(title="Cashflow Scheduler API", version=__version__)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", response_model=HealthOut)
def health():
    return HealthOut(status="ok", version=__version__)


@app.get("/plan", response_model=PlanIn)
def get_plan():
    plan = _ensure_plan()
    return _plan_to_out(plan)


class PlanPostBody(BaseModel):
    plan: PlanIn
    write: bool = False


@app.post("/plan", response_model=PlanIn)
def set_plan(body: PlanPostBody):
    global WORKING_PLAN
    new_plan = _plan_from_in(body.plan)
    WORKING_PLAN = new_plan
    if body.write:
        try:
            save_plan(PLAN_PATH, new_plan)
        except Exception as e:  # pragma: no cover
            raise HTTPException(
                status_code=500, detail=f"Failed to write plan.json: {e}"
            )
    return _plan_to_out(new_plan)


class SolveBody(BaseModel):
    plan: Optional[PlanIn] = None


@app.post("/solve", response_model=SolveResultOut)
def solve_endpoint(body: SolveBody):
    plan = _plan_from_in(body.plan) if body.plan else _ensure_plan()
    return _solve_and_validate(plan)


class SetEODBody(BaseModel):
    day: int
    eod_amount: float


@app.post("/set-eod", response_model=SolveResultOut)
def set_eod(body: SetEODBody):
    if not (1 <= body.day <= 30):
        raise HTTPException(status_code=400, detail="day must be in 1..30")
    plan = _ensure_plan()
    # baseline
    base = dp_solve(plan)
    base_ledger = build_ledger(plan, base.actions)
    desired_cents = to_cents(body.eod_amount)
    current_eod = base_ledger[body.day - 1].closing_cents
    delta = desired_cents - current_eod
    # lock prefix and add adjustment
    plan.actions = base.actions[: body.day] + [None] * (30 - body.day)
    plan.manual_adjustments = list(plan.manual_adjustments) + [
        CFAdjustment(day=body.day, amount_cents=delta, note="api set-eod"),
    ]
    # mutate working plan
    global WORKING_PLAN
    WORKING_PLAN = plan
    return _solve_and_validate(plan)


class ExportBody(BaseModel):
    format: str = Field("md", pattern="^(md|csv|json)$")


class ExportOut(BaseModel):
    format: str
    content: str


@app.post("/export", response_model=ExportOut)
def export_endpoint(body: ExportBody):
    plan = _ensure_plan()
    schedule = dp_solve(plan)
    if body.format == "md":
        text = render_markdown(schedule)
    elif body.format == "csv":
        text = render_csv(schedule)
    else:
        text = render_json(schedule)
    return ExportOut(format=body.format, content=text)


class VerifyOut(BaseModel):
    ok: bool
    dp_obj: List[int]
    cp_obj: List[int]
    detail: str


@app.post("/verify", response_model=VerifyOut)
def verify_endpoint():
    plan = _ensure_plan()
    schedule = dp_solve(plan)
    report = verify_lex_optimal(plan, schedule)
    return VerifyOut(
        ok=report.ok,
        dp_obj=list(report.dp_obj),
        cp_obj=list(report.cp_obj),
        detail=report.detail,
    )


# Allow GET for idempotent verification from the UI
@app.get("/verify", response_model=VerifyOut)
def verify_get():
    return verify_endpoint()  # type: ignore[misc]


class TiesOut(BaseModel):
    objective: List[int]
    solutions: List[str]


@app.get("/ties", response_model=TiesOut)
def ties_endpoint(limit: int = 5):
    plan = _ensure_plan()
    sols = enumerate_ties(plan, limit=limit)
    if not sols:
        return TiesOut(objective=[], solutions=[])
    obj = list(sols[0].objective)
    acts = ["".join(s.actions) for s in sols]
    return TiesOut(objective=obj, solutions=acts)
