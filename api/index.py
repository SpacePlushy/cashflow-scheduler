from __future__ import annotations

import os
import logging
import json
import secrets
from typing import Any, Mapping, cast

from fastapi import FastAPI, Request, HTTPException, Header, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from ._shared import (
    _load_default_plan,
    dp_solve,
    validate,
)
from cashflow.io.render import render_markdown, render_csv, render_json
from cashflow.core.ledger import build_ledger
from cashflow.core.model import Adjustment, Plan, MAX_AMOUNT_CENTS
from cashflow.io.store import plan_from_dict
from cashflow.engines.cpsat import solve_with_diagnostics

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configure CORS origins from environment (more restrictive default)
CORS_ORIGINS_RAW = os.getenv("CORS_ORIGINS", "")
if CORS_ORIGINS_RAW:
    CORS_ORIGINS = [origin.strip() for origin in CORS_ORIGINS_RAW.split(",")]
else:
    # Default to localhost for development, but require explicit config for production
    CORS_ORIGINS = ["http://localhost:3000", "http://localhost:3001"]
    logger.warning("CORS_ORIGINS not set, using development defaults. Set CORS_ORIGINS env var for production.")

# API key authentication (optional, controlled by env var)
API_KEY = os.getenv("API_KEY")
REQUIRE_API_KEY = os.getenv("REQUIRE_API_KEY", "false").lower() == "true"

# Rate limiting
limiter = Limiter(key_func=get_remote_address, default_limits=["100/hour"])

app = FastAPI(title="Cashflow API (Serverless)")
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS middleware with secure defaults
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type", "X-API-Key"],
    allow_credentials=False,  # Set to False for security unless specific origins are set
    max_age=3600,
)


# Security headers middleware
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Content-Security-Policy"] = "default-src 'self'"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    # Only set HSTS in production with HTTPS
    if request.url.scheme == "https":
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    return response


# Optional API key authentication
async def verify_api_key(x_api_key: str = Header(None, alias="X-API-Key")):
    """Verify API key if authentication is required."""
    if not REQUIRE_API_KEY:
        return None  # Authentication disabled

    if not API_KEY:
        logger.error("REQUIRE_API_KEY is true but API_KEY is not set")
        raise HTTPException(status_code=500, detail="Server configuration error")

    if not x_api_key:
        logger.warning("API key missing from request")
        raise HTTPException(status_code=401, detail="API key required")

    # Use constant-time comparison to prevent timing attacks
    if not secrets.compare_digest(x_api_key, API_KEY):
        logger.warning(f"Invalid API key attempt")
        raise HTTPException(status_code=403, detail="Invalid API key")

    return x_api_key


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/solve", dependencies=[Depends(verify_api_key)])
@limiter.limit("10/minute")
async def solve(req: Request):
    body = await _read_body(req)
    try:
        plan_payload = _extract_plan_payload(body)
        plan = _plan_from_payload(plan_payload)
    except ValueError as exc:
        logger.warning(f"Invalid plan payload: {exc}")
        return JSONResponse({"error": str(exc)}, status_code=400)
    except Exception as exc:
        logger.error(f"Unexpected error parsing plan: {exc}")
        return JSONResponse({"error": "Invalid request"}, status_code=400)

    # Extract and validate solver preference
    solver_preference = body.get("solver", "cpsat")
    if solver_preference not in ("dp", "cpsat"):
        logger.warning(f"Invalid solver preference: {solver_preference}")
        return JSONResponse({"error": "solver must be 'dp' or 'cpsat'"}, status_code=400)

    try:
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
    except Exception as exc:
        logger.error(f"Error solving plan: {exc}")
        return JSONResponse({"error": "Failed to solve schedule"}, status_code=500)


@app.post("/set_eod", dependencies=[Depends(verify_api_key)])
@limiter.limit("10/minute")
async def set_eod(req: Request):
    body = await _read_body(req)

    # Validate input types with proper error handling
    try:
        day = int(body.get("day", 0))
    except (ValueError, TypeError) as e:
        logger.warning(f"Invalid day value: {body.get('day')}")
        return JSONResponse({"error": "day must be an integer"}, status_code=400)

    try:
        eod_amount = float(body.get("eod_amount", 0))
    except (ValueError, TypeError) as e:
        logger.warning(f"Invalid eod_amount value: {body.get('eod_amount')}")
        return JSONResponse({"error": "eod_amount must be a number"}, status_code=400)

    # Validate ranges
    if not (1 <= day <= 30):
        return JSONResponse({"error": "day must be in 1..30"}, status_code=400)

    # Reasonable bounds on EOD amount (consistent with MAX_AMOUNT_CENTS = $10M)
    max_dollars = MAX_AMOUNT_CENTS / 100
    if not (-max_dollars <= eod_amount <= max_dollars):
        return JSONResponse({"error": "eod_amount out of reasonable range"}, status_code=400)

    try:
        plan = _plan_from_payload(body.get("plan"))
    except ValueError as exc:
        logger.warning(f"Invalid plan payload in set_eod: {exc}")
        return JSONResponse({"error": str(exc)}, status_code=400)
    except Exception as exc:
        logger.error(f"Unexpected error parsing plan in set_eod: {exc}")
        return JSONResponse({"error": "Invalid request"}, status_code=400)

    # Extract and validate solver preference
    solver_preference = body.get("solver", "cpsat")
    if solver_preference not in ("dp", "cpsat"):
        logger.warning(f"Invalid solver preference: {solver_preference}")
        return JSONResponse({"error": "solver must be 'dp' or 'cpsat'"}, status_code=400)

    try:
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
    except Exception as exc:
        logger.error(f"Error in set_eod: {exc}")
        return JSONResponse({"error": "Failed to solve schedule"}, status_code=500)


@app.post("/export", dependencies=[Depends(verify_api_key)])
@limiter.limit("20/minute")
async def export(req: Request):
    body = await _read_body(req)
    fmt = str(body.get("format", "md")).lower()
    if fmt not in ("md", "csv", "json"):
        return JSONResponse({"error": "format must be md|csv|json"}, status_code=400)

    try:
        plan = _plan_from_payload(body.get("plan"))
    except ValueError as exc:
        logger.warning(f"Invalid plan payload in export: {exc}")
        return JSONResponse({"error": str(exc)}, status_code=400)
    except Exception as exc:
        logger.error(f"Unexpected error parsing plan in export: {exc}")
        return JSONResponse({"error": "Invalid request"}, status_code=400)

    # Extract and validate solver preference
    solver_preference = body.get("solver", "cpsat")
    if solver_preference not in ("dp", "cpsat"):
        logger.warning(f"Invalid solver preference: {solver_preference}")
        return JSONResponse({"error": "solver must be 'dp' or 'cpsat'"}, status_code=400)

    try:
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
    except Exception as exc:
        logger.error(f"Error in export: {exc}")
        return JSONResponse({"error": "Failed to export schedule"}, status_code=500)


async def _read_body(req: Request) -> Mapping[str, Any]:
    """Read and parse request body with proper error handling."""
    try:
        payload = await req.json()
    except json.JSONDecodeError as e:
        logger.warning(f"Invalid JSON in request: {e}")
        return {}
    except Exception as e:
        logger.error(f"Unexpected error reading request body: {e}")
        return {}

    if isinstance(payload, Mapping):
        return payload

    logger.warning(f"Request payload is not a mapping: {type(payload)}")
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
