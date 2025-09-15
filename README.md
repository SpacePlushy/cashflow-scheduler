# Cashflow Scheduler (DP)

[![CI](https://github.com/SpacePlushy/cashflow-scheduler/actions/workflows/ci.yml/badge.svg)](https://github.com/SpacePlushy/cashflow-scheduler/actions)

30‑day cash‑flow scheduler with an exact Dynamic Programming (DP) solver over integer cents. Produces constraint‑correct monthly schedules and cross‑verifies optimality with CP‑SAT (OR‑Tools).

Highlights

- Integer‑cents math for correctness and determinism
- Hard constraints: non‑negative daily closings, 7‑day Off‑Off window, Day‑30 pre‑rent guard, final balance band
- Lexicographic objective: `(workdays, b2b, |final−target|)`
- Spark shifts: a single Spark workday (`SP`) nets $100; off days (`O`) net $0.
- Fast “resume from any day” via manual adjustment (API) or `solve_from()` helper (library)
- Optional CP‑SAT verification and tie enumeration

Quick Start

- Ensure Python 3.11+
- Place a `plan.json` in the project root (see example)
- Solve: `python -m cashflow.cli solve`
- Verify (needs OR‑Tools): `python -m cashflow.cli verify`

How It Works

- Model and money
  - All amounts are integer cents; `to_cents()`/`cents_to_str()` in `cashflow/core/model.py`.
  - `Plan` holds inputs; `DayLedger`/`Schedule` capture the solved plan.
- Ledger and validation
  - `build_ledger(plan, actions)` constructs daily rows (opening → deposits → action net → bills → closing).
  - `validate(plan, schedule)` checks: Spark action validity, non‑negativity, final band, Day‑30 pre‑rent guard, and Off‑Off in every 7‑day window.
- DP solver (`cashflow/engines/dp.py`)
  - State: `(last6_off_bits, prevWorked, workUsed, net)` and additive cost `(b2b)`.
  - Feasibility: rolling Off‑Off, non‑negativity, Day‑30 pre‑rent guard, optional locks.
  - Selection: choose final states within the band minimizing `(workUsed, b2b, |Δ|)`.
  - Helpers: `solve_from(plan, start_day)` re‑solves tail days by locking a prefix.
- CP‑SAT verifier (`cashflow/engines/cpsat.py`)
  - Builds an equivalent model with one‑hot daily actions and sequential lexicographic minimization across three objective parts.
  - `verify_lex_optimal(plan, dp_schedule)` compares DP vs CP‑SAT objectives; CLI shows per‑stage solver statuses.
  - `enumerate_ties(plan, limit)` lists alternate optimal schedules (library API).

CLI

- Show: `python -m cashflow.cli show`
- Solve + validate: `python -m cashflow.cli solve`
- Set EOD and re-solve: `python -m cashflow.cli set-eod <day> <amount>`
  - Add `--calendar` to overwrite the wallpaper PNG (~/Downloads/cashflow_calendar.png).
- Calendar wallpaper (PNG): `python -m cashflow.cli calendar --width 3840 --height 2160 --theme dark`
- Export: `python -m cashflow.cli export --format md --out schedule.md`
- Verify with CP‑SAT: `python -m cashflow.cli verify`
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
- OR‑Tools for verify: the `verify` command requires OR‑Tools. If unavailable, `verify` exits non‑zero. Install it for your interpreter: `python -m pip install --user --break-system-packages 'ortools>=9.8'`.

Calendar Export

- Writes a high-resolution PNG to `~/Downloads/cashflow_calendar.png` by default.
- Options:
  - `--width/--height`: set image resolution (e.g., 3840×2160 for 4K).
  - `--theme dark|light`.
  - `--out <path>`: custom output path.

API (local dev)

- Install: `pip install -r api/requirements.txt` (use a venv)
- Run: `uvicorn api.index:app --reload`
- Endpoints
  - `GET /health`
  - `POST /solve` — returns actions, objective, ledger, validation checks
  - `POST /set_eod` — resume‑from‑day via end‑of‑day override `{ "day": 12, "eod_amount": 250.00 }`
  - `POST /export` — `{ "format": "md"|"csv"|"json" }` → rendered schedule

Web UI (Next.js)

- Dev: `cd web && npm install && npm run dev` (http://localhost:3000)
- API base: `NEXT_PUBLIC_API_BASE` (defaults to `http://127.0.0.1:8000` locally)
- Build: `npm run build` inside `web/`

Build, Test, Type, Lint

- Install deps: `make setup`
- Tests: `make test`
- Lint/format: `make lint` / `make format`
- Types: `make type`
- CP‑SAT verify: `make verify`

Plan File

- Example at `./plan.json`. Loader: `cashflow/io/store.py`.
- Important fields: `start_balance`, `target_end`, `band`, `rent_guard`, `deposits[]`, `bills[]`, `actions[30]` (locks/prefills), optional `manual_adjustments[]`.

Changelog Highlights

- DP: added `solve_from()` and internal `forbid_large_after_day1` flag; refined Off‑Off/window handling and pruning.
- CP‑SAT: sequential lexicographic verify with per‑stage statuses; `enumerate_ties()` for alternate optimal schedules.
- API: `/solve`, `/set_eod`, `/export` with CORS; split serverless `api/` deps from root to slim deploys.
- Packaging/CI: editable installs fixed; mypy typing tightened; Makefile smoke targets and Vercel/Fly helpers added.

See `instructions.md` for a deeper developer guide and algorithmic notes.
