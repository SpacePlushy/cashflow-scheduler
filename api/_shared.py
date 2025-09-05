from __future__ import annotations

import json
from typing import Any, Dict

from cashflow.io.store import load_plan
from cashflow.engines.dp import solve as dp_solve
from cashflow.core.ledger import build_ledger
from cashflow.core.validate import validate
"""Shared utilities for serverless API handlers.

Avoid importing optional render helpers here, since not all functions need
them and importing them at module import time can cause ImportError if a
stale deploy is running older code. Handlers that need exports should import
from cashflow.io.render locally in their modules.
"""
from cashflow.engines.cpsat import verify_lex_optimal
from cashflow.core.model import Plan, Bill, Deposit, Adjustment, to_cents


def _embedded_plan() -> Plan:
    # Minimal embedded dataset (mirrors plan.json) to avoid runtime file deps
    deposits = [Deposit(day=11, amount_cents=to_cents(1021.0)), Deposit(day=25, amount_cents=to_cents(1021.0))]
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


def _load_default_plan() -> Plan:
    # Attempt to load plan.json if present; on serverless, use embedded
    try:
        return load_plan("plan.json")
    except Exception:
        return _embedded_plan()


def json_response(obj: Dict[str, Any]) -> tuple[str, int, Dict[str, str]]:
    return json.dumps(obj, separators=(",", ":")), 200, {"Content-Type": "application/json"}


def _cors_headers(origin: str | None = None) -> Dict[str, str]:
    o = origin or "*"
    return {
        "Access-Control-Allow-Origin": o,
        "Access-Control-Allow-Methods": "GET,POST,OPTIONS",
        "Access-Control-Allow-Headers": "Content-Type",
        "Vary": "Origin",
        "Content-Type": "application/json",
    }


def handle_preflight(request) -> tuple[str, int, Dict[str, str]] | None:
    try:
        method = getattr(request, "method", None) or request.method  # type: ignore[attr-defined]
    except Exception:
        method = None
    if (method or "").upper() == "OPTIONS":
        origin = None
        try:
            origin = request.headers.get("origin")  # type: ignore[attr-defined]
        except Exception:
            pass
        return "", 204, _cors_headers(origin)
    return None
