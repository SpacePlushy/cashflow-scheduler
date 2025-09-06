# Repository Guidelines

## Project Structure & Module Organization
- `cashflow/`: Python package
  - `core/`: money utils, models, ledger, validation
  - `engines/`: solvers (`dp.py`, `cpsat.py`)
  - `io/`: plan loading and renderers (md/csv/json)
  - `cli.py`: Typer CLI entrypoint
- `cashflow/tests/`: `unit/`, `property/`, `regression/`
- `api/`: FastAPI serverless endpoints (`/solve`, `/set_eod`, `/export`)
- `verify_service/`: containerized CP‑SAT verify API
- `web/`: Next.js UI (optional for local dev)
- Root: `plan.json`, `Makefile`, `pyproject.toml`, `requirements.txt`

## Build, Test, and Development Commands
- `make setup` — install dependencies (Python 3.11+)
- `make test` — run the full pytest suite
- `make lint` — `ruff` + `black --check`
- `make format` — auto-format + fix lints
- `make type` — mypy type checks
- `make verify` — CP‑SAT cross‑check of DP objective
- CLI: `python -m cashflow.cli show|solve|export|verify`
  - After editable install (`pip install -e .`): `cash solve`

## Coding Style & Naming Conventions
- Black formatting (4‑space indent); imports ordered; no unused/broad excepts
- Public functions typed; run `make type` before PRs
- Names: modules/functions `snake_case`, classes `PascalCase`, constants `UPPER_SNAKE_CASE`

## Testing Guidelines
- Frameworks: `pytest` + `hypothesis` (property tests)
- Location: `cashflow/tests/{unit,property,regression}`; files `test_*.py`
- Quick runs: `pytest -q`, or `pytest -q cashflow/tests/unit -k cli`
- Add tests with behavior changes; property tests when applicable (no strict coverage gate)

## Commit & Pull Request Guidelines
- Conventional Commits (e.g., `feat: add dp tie-break`, `fix: guard negative balance`)
- PRs include: description, linked issue, rationale, sample CLI output (e.g., `python -m cashflow.cli verify`), and tests
- Keep changes focused; update docs when user‑facing behavior changes

## Architecture Overview
- DP (`engines/dp.py`) computes feasible 30‑day schedules over integer cents
- Validator enforces non‑negativity, Day‑1 `L`, rolling `O,O` window, end‑band, and Day‑30 pre‑rent guard
- CP‑SAT (`engines/cpsat.py`) verifies lexicographic optimality and can enumerate ties

## Current Surface & Status
- CLI: `python -m cashflow.cli show|solve|set-eod|export|verify` (defaults to `./plan.json`).
- Library: `engines.dp.solve()` and `solve_from()`; internal flag `forbid_large_after_day1` exists (not exposed).
- API (FastAPI in `api/index.py`): `/health`, `/solve`, `/set_eod`, `/export` for EOD override and rendering.
- CP‑SAT: `verify_lex_optimal()` used by CLI `verify`; `enumerate_ties()` is available as a library helper.
- Web UI: `web/` Next.js app for local dev and Vercel.

Note: `instructions.md` includes forward‑looking CLI ideas (e.g., `go`, `set-eod` command, `pareto`, `why`). Only the subset above is implemented today.

## Agent Notes (Contributing)
- Money is integer cents; never introduce floats in computations or IO.
- Shift nets are defined in `core/model.py::SHIFT_NET_CENTS`. Do not change without updating tests and docs.
- Validator is independent of the solver; keep feasibility rules mirrored across DP, validator, and CP‑SAT.
- OR‑Tools is optional; keep imports guarded in `engines/cpsat.py` and surface clear errors only when CP‑SAT paths are used.
- If you modify solver behavior or plan schema, update:
  - `README.md` (How it works, CLI), `instructions.md` (algorithm/PRD), and this `AGENTS.md` (surface & notes)
  - Tests under `cashflow/tests/{unit,property,regression}`
- Commit messages follow Conventional Commits; include sample CLI output for user‑visible changes.

## Recent History (high‑level)
- Added `solve_from()` to DP and optional `forbid_large_after_day1` guard.
- CP‑SAT: sequential lex optimization with per‑stage statuses and tie enumeration.
- Serverless API consolidated under `api/index.py` with CORS; `/set_eod` and `/export` added.
- Packaging/CI: editable installs fixed, mypy tightened, smoke scripts for Vercel/Fly.
