from __future__ import annotations

import os
import logging
import secrets

from fastapi import FastAPI, Request, HTTPException, Header, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from cashflow.engines.dp import solve as dp_solve
from cashflow.engines.cpsat import verify_lex_optimal
from cashflow.io.store import load_plan
from cashflow.core.model import Plan, Bill, Deposit, Adjustment, to_cents

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


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


# Configure CORS origins from environment (more restrictive default)
CORS_ORIGINS_RAW = os.getenv("CORS_ORIGINS", "")
if CORS_ORIGINS_RAW:
    CORS_ORIGINS = [origin.strip() for origin in CORS_ORIGINS_RAW.split(",")]
else:
    # Default to localhost for development
    CORS_ORIGINS = ["http://localhost:3000", "http://localhost:3001"]
    logger.warning("CORS_ORIGINS not set, using development defaults. Set CORS_ORIGINS env var for production.")

# API key authentication (optional)
API_KEY = os.getenv("API_KEY")
REQUIRE_API_KEY = os.getenv("REQUIRE_API_KEY", "false").lower() == "true"

# Rate limiting
limiter = Limiter(key_func=get_remote_address, default_limits=["60/hour"])

app = FastAPI(title="Cashflow Verify Service")
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS middleware with secure defaults
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type", "X-API-Key"],
    allow_credentials=False,
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
    if request.url.scheme == "https":
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    return response


# Optional API key authentication
async def verify_api_key(x_api_key: str = Header(None, alias="X-API-Key")):
    """Verify API key if authentication is required."""
    if not REQUIRE_API_KEY:
        return None

    if not API_KEY:
        logger.error("REQUIRE_API_KEY is true but API_KEY is not set")
        raise HTTPException(status_code=500, detail="Server configuration error")

    if not x_api_key:
        logger.warning("API key missing from request")
        raise HTTPException(status_code=401, detail="API key required")

    # Use constant-time comparison to prevent timing attacks
    if not secrets.compare_digest(x_api_key, API_KEY):
        logger.warning("Invalid API key attempt")
        raise HTTPException(status_code=403, detail="Invalid API key")

    return x_api_key


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/")
def root():
    return {"service": "cashflow-verify", "status": "ok"}


@app.post("/verify", response_model=VerifyOut, dependencies=[Depends(verify_api_key)])
@limiter.limit("30/hour")
def verify(request: Request):
    """Verify DP solution against CP-SAT solver."""
    try:
        plan = load_default_plan()
        schedule = dp_solve(plan)
        report = verify_lex_optimal(plan, schedule)
        return VerifyOut(
            ok=report.ok,
            dp_obj=list(report.dp_obj),
            cp_obj=list(report.cp_obj),
            detail=report.detail,
        )
    except Exception as e:
        logger.error(f"Error in verify endpoint: {e}")
        raise HTTPException(status_code=500, detail="Verification failed")
