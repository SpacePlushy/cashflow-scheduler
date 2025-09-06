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
