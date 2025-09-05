#!/usr/bin/env markdown
# Web UI Design — Cashflow Scheduler (Apple‑Themed)

## Vision

- A crisp, calm financial instrument panel that feels native to macOS.
- One primary surface (the 30‑day table) with minimal chrome; secondary details in panels/sheets.
- Deterministic, reversible actions; every change is inspectable, explainable, and exportable.

## Users & Jobs

- Primary user: individual planner.
- Jobs: solve a plan; tweak a day’s EOD; validate; compare diffs; export; optionally verify with CP‑SAT.

## Information Architecture

- Home (Plan): summary cards + primary actions (Solve, Verify, Export).
- Schedule: 30‑day table, inline EOD edits, validation panel, diff toggle.
- Why: per‑day explanation sheet (alternatives, feasibility, objective deltas).
- Verify: CP‑SAT cross‑check (optional) and tie enumeration.
- Settings: target/band overrides, “forbid large after day 1”, persistence, advanced flags.

## Layout & Navigation

- Top toolbar: subtle title, actions (Solve, Verify, Export, Settings), right‑aligned status and “last updated”.
- Content split: left 2/3 schedule grid; right 1/3 contextual panel (Validation/Why/Diff). Panel collapses on narrow view.
- Sticky footer: objective summary chips and final closing.

## Core Screens

Home

- Plan overview: Start, Target, Band, Rent Guard; upcoming deposits/bills strip.
- Primary buttons: Solve, Verify, Open Schedule.

Schedule

- Table columns: Day | Opening | Deposits | Action | Net | Bills | Closing.
- Edit EOD: click Closing → money input; save triggers `/set-eod` → locks prefix → re‑solves tail.
- Action badges: O/S/M/L/SS; locked days show a small lock dot.
- Diff toggle: per‑cell highlights vs last schedule; subtle green/red halos; “show changed only”.
- Right panel: Validation checklist with concise details; row details on click.

Why

- Open from an Action chip. Shows baseline choice, equal‑objective ties, infeasible alternatives (first failing check), and “worse on …” notes.

Verify

- DP vs CP‑SAT objective; tie note and optional list of N ties; time budget indicator.

Export

- Markdown/CSV/JSON buttons; inline preview with copy/download.

## Interactions & Flows

- Full solve: atomic update of table/objective/checks; toast: “Solved in X ms.”
- EOD edit: apply → table/ledger/objective update; toast with any validation notes.
- Undo/Redo: local session history; undo last EOD edit; revert to baseline.
- Diff view: toggle; highlights actions/balances deltas.
- Verify: if OR‑Tools missing, show install hint; otherwise run and show results.

## Visual Design (Apple‑Themed)

- Typography: SF Pro Text/Display (fallback: Inter, system‑ui). Sizes: 12/14/16/20/28.
- Colors: macOS neutrals; accent from system (CSS `accent-color`); success green, warning amber, error red, info blue — slightly desaturated.
- Surfaces: large white/dark panels, soft elevation; translucent blurred toolbar.
- Components: rounded corners (10–12px), 1px hairline borders, subtle shadows; 150–200ms ease transitions.

## Components

- ScheduleTable: 30 rows, optional column resize.
- MoneyInput: validation on blur; separators; keyboard step (±cents/dollars with modifiers).
- ActionBadge: five variants with tooltips (net cents, constraints hints).
- ValidationList: pass/fail items; clicking highlights offending days.
- ObjectiveBar: pill chips with icons; hover explains objective levels.
- DiffHighlight: computes cell deltas; legend in panel.
- Toasts: bottom‑center, unobtrusive, stackable.

## State & Data

- Slices: `plan`, `schedule`, `ledger`, `checks`, `lastSchedule`, `pending`, `settings`.
- Fetch: small typed client with zod/ts types; retries; request dedupe.
- Persistence: in‑memory by default; optional write/read `plan.json` via `/plan`.
- No optimistic UI for solve; show progress and disable controls during requests.

## Error, Loading, and Empty States

- Loading: skeleton rows, toolbar spinner, status “Solving…”.
- Empty: prompt to Solve; show plan summary.
- Errors: inline cause (e.g., “Day‑30 pre‑rent guard violated”), suggestions (widen band, allow large), link to Settings.
- Network: retry affordance; keep last good schedule visible with a banner.

## Accessibility & Keyboard

- Full keyboard: Tab → Enter to edit EOD; Esc cancels; Cmd/Ctrl+Z undo; Cmd/Ctrl+S solve; Shift+D diff.
- ARIA: grid/list roles, semantic headings, visible focus outlines; WCAG AA contrast.
- Screen‑reader labels on action badges and validation outputs.

## Performance

- DP is sub‑second; cap CP‑SAT at ~10s. Batch DOM updates. Memoize derived data (diffs, aggregates).

## Responsive

- Tablet/Phone: right panel becomes bottom sheet; sticky Solve button. Desktop max content width ~1280px.

## Security & Privacy

- Localhost only; strict validation; no telemetry. No PII beyond amounts/dates; persistence only on user request.

## Implementation Roadmap

Backend (MVP)

- Endpoints: `/health`, `/plan` GET/POST, `/solve`, `/set-eod`, `/export (md|csv|json)`, `/verify` (optional), `/ties` (optional).
- Models: Pydantic DTOs mapping to core types; cents↔dollars adapters.
- CORS: allow `http://localhost:5173`; bind `127.0.0.1`.

Frontend (MVP)

- Scaffold with Vite React + TS; CSS variables for color/radius/shadows; light/dark.
- Pages: Home, Schedule; Panels: Validation, Diff, Why.
- Flows: Solve, EOD edit, Diff, Export; Verify gated by feature flag.

Polish

- Undo/Redo; timeline of changes per cell; Settings overrides & persistence.
- Keyboard shortcuts and a11y pass; screenshots/docs.

Stretch

- Pareto view with multiple tie schedules and side‑by‑side compare.
- “Why” with embedded explanations; richer error guidance.

## References

- API/plan: `docs/web_ui_plan.md` (endpoints, contracts, timeline).
- Core engines and CLI: `cashflow/engines/*`, `cashflow/cli.py`.

