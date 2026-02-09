# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

A 30-day cash-flow scheduler that optimizes work schedules to meet financial constraints. The project uses constraint programming (CP-SAT via OR-Tools) and dynamic programming (DP) to find optimal schedules that minimize workdays while maintaining positive daily balances and meeting target end balances.

**Key Constraint:** The system enforces an "Off-Off Window" rule requiring at least one consecutive pair of off-days within every rolling 7-day window.

## Repository Structure

```
cashflow/               # Core Python package
├── core/              # Domain models and validation
│   ├── model.py       # Plan, Schedule, Bill, Deposit, Adjustment dataclasses
│   ├── ledger.py      # Build daily ledger from actions
│   └── validate.py    # Validation rules (non-negative closings, rent guard, band)
├── engines/           # Solver implementations
│   ├── dp.py          # Dynamic programming solver (primary)
│   ├── cpsat.py       # CP-SAT solver (verification & tie enumeration)
├── io/                # I/O and rendering
│   ├── store.py       # JSON plan loading/parsing
│   ├── render.py      # Markdown/CSV/JSON output
│   └── calendar.py    # PNG calendar generation
├── cli.py             # Typer-based CLI entry point
└── tests/             # Pytest test suite
    ├── unit/          # Unit tests
    ├── property/      # Property-based tests (Hypothesis)
    └── regression/    # Regression tests

api/                   # FastAPI serverless API
├── index.py           # Endpoints: /solve, /set_eod, /export
└── _shared.py         # Shared utilities

verify_service/        # Standalone verification service
└── app.py            # FastAPI app for /verify endpoint (DP vs CP-SAT)

web/                   # Next.js 15 frontend (shadcn/ui redesign)
├── src/
│   ├── app/          # App router pages
│   ├── components/   # React components (PlanEditor, ResultsView)
│   └── lib/          # Types, API client, default plan

scripts/               # Development utilities
├── dev_run_all.sh    # Run all services locally
├── smoke.mjs         # Smoke test runner
└── vercel_smoke.sh   # Vercel deployment smoke tests
```

## Development Commands

### Python Backend

```bash
# Setup
make setup          # Install dependencies from requirements.txt
make setup-dev      # Install package in editable mode

# Code Quality
make lint           # Run ruff check + black --check
make type           # Run mypy type checking
make format         # Auto-format with black + ruff --fix

# Testing
make test           # Run pytest suite
pytest -v           # Verbose test output
pytest -k test_name # Run specific test
pytest cashflow/tests/unit/test_cli.py  # Run single test file

# CLI Usage
python -m cashflow.cli solve [plan.json]           # Solve and validate
python -m cashflow.cli solve --solver dp           # Use DP solver
python -m cashflow.cli solve --solver cpsat         # Use CP-SAT solver
python -m cashflow.cli show [plan.json]            # Show schedule without validation
python -m cashflow.cli verify [plan.json]          # Cross-verify DP vs CP-SAT
python -m cashflow.cli set-eod DAY AMOUNT          # Lock days 1..DAY and re-solve
python -m cashflow.cli calendar [--4k]             # Generate PNG calendar
python -m cashflow.cli export --format md          # Export to markdown

# Installed command (after setup-dev)
cash solve          # Alias for python -m cashflow.cli solve
```

### Next.js Frontend

```bash
# Setup and Development
make web-install    # Install npm dependencies
make web-dev        # Start dev server (port 3000, Turbopack)
make web-build      # Production build with Turbopack
make web-start      # Start production server
make web-lint       # Run ESLint

# Direct npm commands (from web/)
cd web && npm run dev     # Dev with Turbopack
cd web && npm run build   # Production build
```

### Verification Service

```bash
# Run locally (from verify_service/)
cd verify_service
uvicorn app:app --reload --port 8001
```

## Core Architecture

### Solver Flow

1. **Input:** `Plan` object defines:
   - Start/target balances, band tolerance
   - Bills and deposits by day
   - Optional action locks (pre-filled days)
   - Manual adjustments (one-time cash corrections)
   - Rent guard threshold for Day 30

2. **Solvers:**
   - **DP (dp.py):** Primary solver using dynamic programming with state space pruning. Optimizes lexicographically: (workdays, back-to-back pairs, |final diff from target|)
   - **CP-SAT (cpsat.py):** Constraint programming solver for verification and tie enumeration. Requires OR-Tools (optional dependency)

3. **Output:** `Schedule` with:
   - 30-day action sequence ("O" = off, "Spark" = work/$100)
   - Objective tuple (workdays, b2b, abs_diff)
   - Daily ledger (opening, deposits, action net, bills, closing)

### Key Constraints

- **Day 1:** Always "Spark" (business rule)
- **Off-Off Window:** Every 7-day sliding window must contain at least one consecutive off-off pair
- **Non-negative Closings:** Daily balance ≥ 0 after bills
- **Day 30 Pre-Rent Guard:** Balance before paying rent ≥ `rent_guard_cents`
- **Final Band:** Closing balance within `[target - band, target + band]`

### API Architecture

The system uses a **hybrid FastAPI + serverless** architecture:

- **api/index.py:** Main serverless API (Vercel) with `/solve`, `/set_eod`, `/export`
- **verify_service/app.py:** Standalone verification service (Fly.io) with `/verify`
- Both services use the same `cashflow` package core
- CP-SAT solver auto-falls back to DP if OR-Tools unavailable

### Frontend State Management

The Next.js app (`web/src/`) uses:
- Local state for plan editing (PlanEditor component)
- Fetch-based API calls (no external state library)
- shadcn/ui components with Tailwind CSS v4
- Dark/light theme support via next-themes

## Testing Strategy

### Test Types

1. **Unit Tests (`cashflow/tests/unit/`):**
   - Core solver logic (`test_solver_*.py`)
   - Validation rules (`test_validate_*.py`)
   - Edge cases (adjustments, locks, infeasible plans)

2. **Property Tests (`cashflow/tests/property/`):**
   - Hypothesis-based generative testing
   - Solver invariants across random inputs

3. **Regression Tests (`cashflow/tests/regression/`):**
   - Known-good scenarios

4. **Smoke Tests (`scripts/`):**
   - End-to-end API/UI integration tests
   - `smoke.mjs`: Local smoke test runner
   - `vercel_smoke.sh`: Vercel deployment validation

### Running Tests

```bash
# Python tests
pytest -q                                    # Quiet mode
pytest -v cashflow/tests/unit/              # Unit tests only
pytest --hypothesis-show-statistics         # Show property test stats

# Integration tests
make smoke UI_URL=http://localhost:3000 API_URL=http://localhost:8000
make smoke-vercel UI_PROJECT=my-ui API_PROJECT=my-api
```

## Common Patterns

### Loading a Plan

```python
from cashflow.io.store import load_plan
plan = load_plan("plan.json")  # Parses JSON into Plan dataclass
```

### Solving

```python
from cashflow.engines.dp import solve as dp_solve
from cashflow.engines.cpsat import solve_with_diagnostics

# DP solver (always available)
schedule = dp_solve(plan)

# CP-SAT with fallback
result = solve_with_diagnostics(plan, dp_fallback=True)
schedule = result.schedule
```

### Validation

```python
from cashflow.core.validate import validate
report = validate(plan, schedule)
if not report.ok:
    for name, ok, detail in report.checks:
        print(f"{name}: {'PASS' if ok else 'FAIL'} - {detail}")
```

### Locking Prefix Days (set-eod flow)

```python
# To lock days 1..N and re-solve remainder:
baseline = dp_solve(plan)
plan.actions = baseline.actions[:N] + [None] * (30 - N)
# Optionally add manual adjustment to hit target EOD
plan.manual_adjustments.append(Adjustment(day=N, amount_cents=delta))
new_schedule = dp_solve(plan)
```

## Money Handling

All monetary values are stored as **integer cents** internally:

```python
from cashflow.core.model import to_cents, cents_to_str

# Convert to cents
amount_cents = to_cents(167.50)  # -> 16750

# Convert back to string
cents_to_str(16750)  # -> "167.50"
```

## OR-Tools CP-SAT (Optional)

- **Installation:** `pip install ortools` (may fail on some platforms)
- **Fallback:** System automatically uses DP solver if OR-Tools unavailable
- **Usage:** Primarily for verification (`make verify`) and tie enumeration
- **Note:** OR-Tools 9.8+ for macOS ARM64, 9.10+ elsewhere

## Shift Types

Current model uses a simplified shift system defined in `cashflow/core/model.py`:

```python
SHIFT_NET_CENTS = {
    "O": 0,           # Off day (no income)
    "Spark": 10_000,  # Work day ($100 net)
}
```

Historical note: Previous versions supported multiple shift types (S/M/L). Recent refactor simplified to single work type.

## Plan JSON Schema

```json
{
  "start_balance": 90.50,
  "target_end": 490.50,
  "band": 25.0,
  "rent_guard": 1636.0,
  "deposits": [
    {"day": 11, "amount": 1021.0}
  ],
  "bills": [
    {"day": 1, "name": "Auto Insurance", "amount": 177.0}
  ],
  "actions": [null, null, ...],  // 30 elements, null = not locked
  "manual_adjustments": [
    {"day": 15, "amount": -50.0, "note": "correction"}
  ],
  "locks": [[1, 10]],  // Range tuples (currently unused by solvers)
  "metadata": {"version": "1.0.0"}
}
```

## Deployment

- **Frontend:** Vercel (Next.js)
- **API:** Vercel Serverless Functions (api/)
- **Verify Service:** Fly.io (verify_service/)
- **Config:** `.vercelignore`, `fly.toml`, `Dockerfile.verify`

## Development Workflow

1. Make changes to Python core (`cashflow/`)
2. Run `make format lint type test` before committing
3. Test CLI: `python -m cashflow.cli solve`
4. Test API locally: Run `scripts/dev_run_all.sh` or individually start services
5. Test frontend: `make web-dev` and open http://localhost:3000
6. Run smoke tests before deploying: `make smoke`

## Important Files

- **plan.json** (repo root): Default plan for development/testing
- **requirements.txt**: Python dependencies (shared by all services)
- **pyproject.toml**: Package metadata and build config
- **Makefile**: Common development tasks
- **web/src/lib/defaultPlan.ts**: Default plan for frontend

## Type Checking

The Python codebase uses mypy with strict checking:
- Run `make type` to check types
- `from __future__ import annotations` enables forward references
- Core models use dataclasses with type hints
