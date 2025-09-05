# Cashflow Scheduler (DP)

[![CI](https://github.com/SpacePlushy/cashflow-scheduler/actions/workflows/ci.yml/badge.svg)](https://github.com/SpacePlushy/cashflow-scheduler/actions)

A 30-day cash-flow scheduler that produces feasible, constraint-correct plans using a DP solver over integer cents. CLI provides `solve`, `show`, `export`, and `verify` (CP-SAT cross-check).

Quick start:

- Ensure Python 3.11+
- Place a `plan.json` in the project root (see example).
- Run: `python3 -m cashflow.cli solve`
- Verify (requires OR-Tools): `python3 -m cashflow.cli verify`

This repository follows the high-level spec in `instructions.md`. Current scope includes the DP engine, ledger/validator, extensive tests (unit/property/regression), and a CP‑SAT cross‑verifier.

## Web UI (Next.js)

The repository includes a Next.js app under `web/` designed for Vercel.

- Dev: `cd web && npm install && npm run dev` (http://localhost:3000)
- API base: set `NEXT_PUBLIC_API_BASE` (optional). Defaults to `http://127.0.0.1:8000` on localhost, or `/api/index` in production.
- Build: `npm run build` inside `web/`.

### Vercel Deploy

- Easiest: Create two Vercel projects
  - UI project → Root Directory: `web/` (Next auto-detected)
  - API project → Root Directory: repo root, Python Serverless Functions under `api/` (e.g., `api/health.py`)
  - In the UI project, set `NEXT_PUBLIC_API_BASE` to the API project URL (e.g., `https://<api>.vercel.app/api/index`).
