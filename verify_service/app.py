from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from cashflow.engines.dp import solve as dp_solve
from cashflow.engines.cpsat import verify_lex_optimal
from cashflow.io.store import load_plan
from cashflow.core.model import Plan
from api._shared import _embedded_plan  # reuse embedded default


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
