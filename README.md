# Cashflow Scheduler (CP-SAT)

[![CI](https://github.com/SpacePlushy/cashflow-scheduler/actions/workflows/ci.yml/badge.svg)](https://github.com/SpacePlushy/cashflow-scheduler/actions)

30‑day cash‑flow scheduler backed by Google OR-Tools CP-SAT for lexicographic optimality, with the original Dynamic Programming (DP) engine retained as a fast fallback.

Highlights

- Integer‑cents math for correctness and determinism
- Primary solver: OR-Tools CP-SAT sequential lexicographic optimization with surfaced solver diagnostics
- DP engine still available for lightning-fast fallback or local experimentation (`--solver dp`)
- Hard constraints: non‑negative daily closings, Day‑1 Large, 7‑day Off‑Off window, Day‑30 pre‑rent guard, final balance band
- Lexicographic objective: `(workdays, b2b, |final−target|, large_days, single_pen)`
- Optional tie enumeration and DP ↔ CP-SAT comparison tools

Quick Start

- Ensure Python 3.11+ and install `ortools>=9.8` (`python -m pip install --user ortools>=9.8`)
- Place a `plan.json` in the project root (see example)
- Solve: `python -m cashflow.cli solve` (CP-SAT by default; add `--solver dp` to force DP)
- Launch the web UI + API: `./scripts/dev_run_all.sh`
- Verify DP vs CP-SAT: `python -m cashflow.cli verify`

How It Works

- Model and money
  - All amounts are integer cents; `to_cents()`/`cents_to_str()` in `cashflow/core/model.py`.
  - `Plan` holds inputs; `DayLedger`/`Schedule` capture the solved plan.
- Ledger and validation
  - `build_ledger(plan, actions)` constructs daily rows (opening → deposits → action net → bills → closing).
  - `validate(plan, schedule)` checks: Day‑1 Large, non‑negativity, final band, Day‑30 pre‑rent guard, and Off‑Off in every 7‑day window.
- CP‑SAT solver (`cashflow/engines/cpsat.py`)
  - Builds a one-hot action model and solves a five-part lexicographic objective `(workdays, b2b, |Δ|, large_days, single_pen)` sequentially.
  - Exposes `solve_with_diagnostics(plan)` returning the schedule plus statuses, wall time, and fallback metadata.
  - Supports tie enumeration and DP schedule verification utilities.
- DP engine (`cashflow/engines/dp.py`)
  - Still available for fast experimentation or when OR-Tools is unavailable (`--solver dp`).
  - Provides helpers like `solve_from(plan, start_day)` for prefix locking scenarios.

CLI

- Show: `python -m cashflow.cli show`
- Solve + validate: `python -m cashflow.cli solve` (CP-SAT by default; add `--solver dp` to force DP)
- Set EOD and re-solve: `python -m cashflow.cli set-eod <day> <amount>`
  - Add `--calendar` to overwrite the wallpaper PNG (~/Downloads/cashflow_calendar.png).
- Calendar wallpaper (PNG): `python -m cashflow.cli calendar --width 3840 --height 2160 --theme dark`
- Export: `python -m cashflow.cli export --format md --out schedule.md`
- Verify DP vs CP‑SAT: `python -m cashflow.cli verify`
- All commands default to `./plan.json`; pass a custom path as an argument.

EOD Override Example

- Set Day‑6 to end at $167.00 and re‑solve the remainder:
  - `python -m cashflow.cli set-eod 6 167`
- Optionally persist a derived plan with the locked prefix and adjustment:
  - `python -m cashflow.cli set-eod 6 167 --save-plan plan_eod6_167.json`
 - Also refresh the wallpaper in one step (overwrites ~/Downloads/cashflow_calendar.png):
   - `python -m cashflow.cli set-eod 6 167 --calendar`

Troubleshooting

- `python` vs `python3`: these may be different interpreters with different site‑packages. If `python -m pytest` fails but `python3 -m pytest` works, install missing deps for your `python` (e.g., `python -m pip install --user --break-system-packages pytest ortools`) or use the repo venv (`.venv/bin/python -m pytest`).
- OR‑Tools required: CP-SAT is the default backend. Install it for your interpreter with `python -m pip install --user 'ortools>=9.8'`. CLI/API will fall back to DP (and warn) if it is missing.

Calendar Export

- Writes a high-resolution PNG to `~/Downloads/cashflow_calendar.png` by default.
- Options:
  - `--width/--height`: set image resolution (e.g., 3840×2160 for 4K).
  - `--theme dark|light`.
  - `--out <path>`: custom output path.

API (local dev)

- Install: `pip install -r api/requirements.txt ortools>=9.8` (use a venv)
- Run: `uvicorn api.index:app --reload`
- Endpoints
  - `GET /health`
  - `POST /solve` — returns actions, objective, ledger, validation checks, and solver diagnostics
  - `POST /set_eod` — resume‑from‑day via end‑of‑day override `{ "day": 12, "eod_amount": 250.00 }`
  - `POST /export` — `{ "format": "md"|"csv"|"json" }` → rendered schedule

Web UI (Next.js)

- Dev: `cd web && npm install && npm run dev` (http://localhost:3000)
- Configure API base: create `web/.env.local` with `NEXT_PUBLIC_SOLVER_API_URL=http://127.0.0.1:8000`
- Build: `npm run build` inside `web/`
- Features: guided plan editor, JSON import/export helpers, solve button with ledger + validation results, CSV/Markdown/JSON downloads via backend renderers

Build, Test, Type, Lint

- Install deps: `make setup`
- Tests: `make test`
- Lint/format: `make lint` / `make format`
- Types: `make type`
- CP‑SAT verify: `make verify`
- E2E (web + API): `cd web && npx playwright test` (run `npx playwright install` once to download browsers)

Plan File

- Example at `./plan.json`. Loader: `cashflow/io/store.py`.
- Important fields: `start_balance`, `target_end`, `band`, `rent_guard`, `deposits[]`, `bills[]`, `actions[30]` (locks/prefills), optional `manual_adjustments[]`.

Changelog Highlights

- CP‑SAT: promoted to primary solver with diagnostics and DP fallback integration; tie enumeration and verification remain available.
- DP: retained as secondary engine (`--solver dp`) for fast experimentation and fallback when CP-SAT is unavailable.
- API/UI: `/solve` now emits solver metadata consumed by the Next.js frontend; CLI exposes backend selection flags.
- Packaging/CI: editable installs fixed; mypy typing tightened; Makefile smoke targets and Vercel/Fly helpers added.

See `instructions.md` for a deeper developer guide and algorithmic notes.
