# Cashflow Scheduler (DP)

[![CI](https://github.com/SpacePlushy/cashflow-scheduler/actions/workflows/ci.yml/badge.svg)](https://github.com/SpacePlushy/cashflow-scheduler/actions)

A 30-day cash-flow scheduler that produces feasible, constraint-correct plans using a DP solver over integer cents. CLI provides `solve`, `show`, `export`, and `verify` (CP-SAT cross-check).

Quick start:

- Ensure Python 3.11+
- Place a `plan.json` in the project root (see example).
- Run setup script: `bash scripts/bootstrap_venv.sh` (adds `.venv`, installs deps, runs tests)
- Run: `python3 -m cashflow.cli solve`
- Verify (requires OR-Tools): `python3 -m cashflow.cli verify`
- Edit an end-of-day and re-solve tail:
  - `python3 -m cashflow.cli set-eod 12 1286.01`
  - `python3 -m cashflow.cli solve --from 13`
 - Explain a day’s choice and alternatives:
   - `python3 -m cashflow.cli why 12`
 - Enumerate ties (same objective, different actions) [requires OR-Tools]:
   - `python3 -m cashflow.cli pareto --limit 5`

This repository follows the high-level spec in `instructions.md`. Current scope includes the DP engine, ledger/validator, extensive tests (unit/property/regression), and a CP‑SAT cross‑verifier.

## Project Status

See `PROGRESS.md` for a checked-off view of what’s done and what’s next.

Design docs:
- API/Frontend plan: `docs/web_ui_plan.md`
- Frontend design (Apple‑themed): `docs/web_ui_design.md`

## Local API (FastAPI)

- Install deps and create venv: `bash scripts/bootstrap_venv.sh --no-tests`
- Run API (reload): `make api` (serves at `http://127.0.0.1:8000`)
- Endpoints: `/health`, `/plan` (GET/POST), `/solve`, `/set-eod`, `/export`, `/verify`, `/ties`

## Web UI (Vite + React)

- Install Node dependencies: `make ui-install`
- Run UI dev server: `make ui` (http://localhost:5173)
- Build: `make ui-build`; Preview: `make ui-preview`
- Dev workflow: run `make api` and `make ui` in separate terminals.

## One-Command Dev Runner

- Run everything and get the URL to open:
  - `bash scripts/dev_all.sh` (adds venv, installs, starts API+UI, prints link)
  - Add `--open` to auto-open the browser.

## Deploy to Vercel (Single Project)

This repo includes `vercel.json` to deploy the UI and API together:

- UI: built from `ui/` with Vite. Static assets are served from `ui/dist`.
- API: Python serverless function at `api/index.py` which mounts the FastAPI app at `/api`.

Steps:
- Connect the GitHub repo in Vercel (Pro plan works best).
- Vercel will detect `vercel.json` and:
  - build the UI (`@vercel/static-build`),
  - deploy the API (`@vercel/python`).
- No env vars are required by default; the UI calls same‑origin `/api/*`.

Notes:
- `vercel.json` includes `cashflow/**` and `plan.json` in the API function bundle.
- CP‑SAT (OR‑Tools) is heavy and may not be available in serverless; the Verify feature degrades gracefully (it will show a readable message).
- Add your custom domain and enable Analytics/Speed Insights from the Vercel dashboard.
