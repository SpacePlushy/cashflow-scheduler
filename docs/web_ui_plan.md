# Cashflow Scheduler Web UI Plan

## Objectives
- Deliver a browser-based experience that mirrors the CLI solver flow while remaining approachable for non-technical users.
- Let users generate a personal 30-day cashflow schedule by configuring income, bills, and guard rails without hand-editing `plan.json`.
- Provide immediate visual feedback (calendar and tables) and access to solver diagnostics/validation results.

## Guiding Principles
- **Accuracy first**: the UI should never diverge from solver truth; all calculations come from the Python backend.
- **Fast iteration**: Lean architecture that encourages small, testable increments. Avoid bespoke state machines when React Query + server actions suffice.
- **User empathy**: default copy and flows for people with limited financial jargon familiarity; progressive disclosure for advanced options.
- **Device reach**: responsive layout that renders well on desktop and tablet; mobile support is a stretch goal.

## Technical Architecture
- **Framework**: Next.js 14 (App Router, TypeScript, React Server Components where helpful).
- **UI Toolkit**: Tailwind CSS + Headless UI (or Radix + custom) for accessible primitives; add domain-specific components gradually.
- **State/Data**:
  - Client uses React Query or Server Actions to call backend `/api/solve`, `/api/set_eod`, `/api/export` endpoints.
  - Shared TypeScript types generated from Pydantic schemas via `datamodel-code-generator` or manual mirrors in `cashflow/api/schemas.py` → `web/src/lib/types.ts`.
- **Backend integration**: Prefer Next.js route handlers that proxy to existing FastAPI service (running locally via `uvicorn`). For production, deploy both Next.js (Vercel) and the Python API (Fly.io/Render) with CORS allowed.
- **Auth**: none for MVP; treat as single-user tool.

## MVP Scope (Milestone M1)
1. **Plan Builder Form**
   - Inputs for pay periods, bills, starting balance, target bands.
   - Ability to upload existing `plan.json` and edit it inline.
2. **Solve Trigger**
   - Calls `/api/solve` with current plan; surface validation errors in context.
3. **Results View**
   - Tabbed layout: table view (day-by-day cashflow) and calendar visualization.
   - Download options for CSV/Markdown (reuse CLI renderers via API endpoints).
4. **Validation Banner**
   - Snapshot of key constraints (non-negative, shift guards) with success/error states.
5. **Session Persistence**
   - Persist last plan in `localStorage` (no server persistence initially).

## Post-MVP Enhancements
- **M2 – Personalization**: named scenarios, saved presets, dark mode toggle.
- **M3 – Collaboration**: shareable links (signed URLs) and read-only embeds.
- **M4 – Insights**: charts for cash-on-hand, warnings for tight days, recommendation hints from solver diffs.

## Implementation Phases
1. **Scaffold**: `npx create-next-app web --ts --eslint --tailwind`; wire lint/test scripts into root `Makefile`.
2. **API Contracts**: confirm request/response schema with backend; add integration tests hitting local FastAPI during `npm run test:api`.
3. **Data Layer**: set up React Query provider and typed client.
4. **Core UI Shell**: global layout, navigation tabs, toast system for alerts.
5. **Plan Builder**: build form with Zod validation mirroring Pydantic rules; provide import/export to JSON.
6. **Solve Flow**: hook form submission to API, display loading/progress, render results components.
7. **Calendar View**: reuse existing rendering logic via SVG/Canvas or build React calendar using solver output; ensure parity with CLI images.
8. **QA & Polish**: add Jest + React Testing Library smoke tests, Playwright happy-path E2E, accessibility checks (axe).

## Tooling & Developer Experience
- Add scripts: `npm run dev`, `npm run lint`, `npm run test`, `npm run build`.
- Configure CI job (`.github/workflows/web.yml`) running lint/test/build.
- Storybook optional for component isolation; defer until calendar view stabilizes.

## Risks & Mitigations
- **Schema drift**: Mitigate with shared schema generation and contract tests.
- **Solver latency**: Provide optimistic UI skeletons; consider streaming progress if API gains long-running tasks.
- **Calendar parity**: Validate layout against CLI snapshots (golden image tests) or share renderer logic by exposing an API endpoint that returns SVG/PNG.

## Open Questions
- Do we retire the FastAPI server in favor of Next.js API routes wrapping the Python solver via Pyodide or serverless? (Default: keep FastAPI.)
- Will production hosting co-locate frontend and backend, or require CORS + separate deployment pipelines?
- Should we expose solver flags (e.g., `forbid_large_after_day1`) in the UI or keep them hidden?

## Definition of Done for MVP
- Deployed Next.js app accessible at staging URL, running against staging solver API.
- User can create/edit plan, run solve, view calendar/table, and download outputs without CLI involvement.
- Automated tests cover API contract (schema match) and happy-path E2E.
- Documentation updated: `README.md` (web section), `docs/web_ui_plan.md`, and onboarding notes in `AGENTS.md`.
