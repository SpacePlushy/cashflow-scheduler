# Web UI Plan for Cashflow Scheduler

## Goals

- Provide a local, browser-based interface to generate, inspect, and edit 30‑day schedules.
- Preserve “resume-from-any-day” semantics by recording manual adjustments and re‑solving tails.
- Keep everything offline, deterministic, and consistent with the CLI objectives and validator.

## Approach Overview

- Backend: expose the existing solver via a thin HTTP API served locally (localhost). No external services.
- Frontend: a small SPA for interactive editing (table view, EOD overrides, diffs, export).
- Packaging: one repo with `cashflow` Python package (API server optional) and `ui/` for the SPA; dev runs both concurrently.

## Stack Choices

- Backend: Python FastAPI or Starlette, Pydantic for request/response models, Uvicorn for dev server.
  - Reason: minimal overhead, great typing, easy JSON interop with our existing Pydantic-like models.
- Frontend: React + Vite + TypeScript (or SvelteKit). React is a safe default for table-heavy UI; Svelte is lighter.
  - Use TanStack Table for render/perf; Zustand/Redux for simple local state if needed.

## API Design (HTTP, JSON)

- GET `/health` → `{ status: 'ok', version }`
- GET `/plan` → returns current plan.json content (normalized to cents in backend and money strings in payload).
- POST `/plan` body: Plan payload → saves as working plan (in-memory or writes to `plan.json` if requested).
- POST `/solve` body: `{ plan?: Plan }` → returns `{ schedule, ledger, objective, checks }`.
- POST `/set-eod` body: `{ day: number, eod_amount: number }` → inserts `manual_adjustment`, locks prefix actions, re‑solves tail; returns updated `{ plan, schedule, ledger, checks }`.
- POST `/verify` body: `{ plan?: Plan }` → returns `{ dp_obj, cp_obj, match, notes }` (if OR-Tools available).
- POST `/export` body: `{ format: 'md'|'csv'|'json' }` → returns file content (download) or artifact link.

Notes:
- All amounts transported as numbers in dollars; backend converts to integer cents internally.
- Endpoints accept full plan payloads or operate on the current working plan; keep deterministic.

## Data Contracts

- Reuse `plan.json` schema (instructions.md §4.2). Add optional UI metadata: `{ ui: { lastEdited: ISO, focusDay: number } }`.
- Responses include:
  - `schedule.actions: string[30]`
  - `objective: [workdays, b2b, abs_delta_cents, large_days, single_pen]`
  - `ledger: [{day, opening, deposits, action, net, bills, closing}]` (all as strings like "123.45" for display)
  - `checks: [ { name, ok, detail } ]` from `validate()`

## UX Flows

- Full Solve: Load plan → click “Solve” → render table (days 1..30), objective, validation checklist.
- EOD Edit: Click a day’s closing cell → enter new EOD → UI calls `/set-eod` → updates plan with `manual_adjustment`, locks prefix actions, re‑solves tail; re-renders.
- Diff: Store previous solve in memory; on next solve, show a side-by-side or inline change indicators (actions, balances).
- Export: Click export → `/export` → download Markdown.
- Verify: Optional “Verify with CP-SAT” button → `/verify` and show result.

## Backend Implementation Plan

1) Introduce `cashflow/api/` with a FastAPI app (optional dependency) and Pydantic models mirroring `Plan`, `Schedule`, `DayLedger` in display-friendly types.
2) Adapters:
   - Parse incoming dollars → cents; produce responses in strings (e.g., "489.53").
   - Bridge functions to DP and validator; optionally to CP‑SAT.
3) Session/State: Start with stateless operations; store working plan in memory per process. Optional: read/write `plan.json` when requested.
4) Error handling: return 400 for schema issues; include minimal infeasibility messages from DP if exposed.
5) Security: bind to `127.0.0.1`; CORS allow `http://localhost:<ui-port>`.

## Frontend Implementation Plan

1) Scaffold `ui/` (Vite React + TS).
2) Views:
   - Home: Plan summary (start, target, band), buttons for Solve / Verify / Export.
   - Table: 30-row schedule with editable EOD column and per-day deposits/bills rollup.
   - Checks: validation checklist.
   - Diff: toggle to view last-vs-current schedule differences.
3) State:
   - `plan` (server copy), `schedule`, `ledger`, `checks`, `lastSchedule` for diff.
   - Local component state for edits; persist full plan on apply.
4) API client: small typed client with fetch wrappers and zod validation on the frontend.

## Dev & Build

- Dev: run API on `localhost:8000` (uvicorn); UI on `localhost:5173` (Vite). CORS enabled.
- Build: `ui/` builds to static assets served by the API under `/` in production mode.
- Make targets: `make api`, `make ui`, `make dev` (concurrently), `make build-ui`, `make serve`.
- CI: add Node setup (v20 LTS). Jobs: `lint` (ruff+black), `type` (mypy), `test` (pytest), `ui-build` (pnpm install + build). Optional Playwright e2e later.

## MVP Scope (Phase 1)

- API endpoints: `/health`, `/solve`, `/set-eod`, `/export`, `/verify` (if OR-Tools available).
- UI: Solve screen with table rendering, EOD edit + re-solve, validation checklist, export.

## Phase 2

- Additional features: plan presets, multiple scenarios, pareto alternatives, "why" explanations.
- Diff viewer polish (per-cell highlights; action changes).
- Settings for `--forbid-large-after-day1`, target/band overrides.

## Risks & Mitigations

- OR-Tools optional install: feature-gate `/verify` and show UI notice.
- Large negative EOD edits may become infeasible: show precise error with guidance; propose auto-widen band or added workdays.
- Performance: DP is already sub-second; guard CP-SAT time budget to avoid UI stalls.

## Timeline (Rough)

- Day 1–2: API scaffolding + endpoints; wire DP/validate; manual adjustments; integrate CORS; simple JSON schema.
- Day 3–4: UI table, EOD edit flow, solve/verify/export, validation panel.
- Day 5: Polish, diff view, error UX; docs.
- Day 6–7: Tests (API unit + UI integration), CI updates, README screenshots.

---

See also: `docs/web_ui_design.md` for the detailed Apple‑themed frontend design (IA, layout, components, a11y).
