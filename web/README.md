# Cashflow Scheduler Web UI

Browser interface for configuring monthly cashflow plans, running the dynamic programming solver, and reviewing results without the CLI.

## Quick Start

```bash
cd web
npm install        # already run via create-next-app, repeat when dependencies change
npm run dev        # starts Next.js on http://localhost:3000
```

Set the solver API base URL with `.env.local`:

```ini
NEXT_PUBLIC_SOLVER_API_URL=http://localhost:8000
```

Run the FastAPI server locally via `uvicorn api.index:app --reload` (served on port 8000 by default), then visit `http://localhost:3000`.

## Features

- Guided form to edit balances, deposits, and bills
- JSON import/export helpers for advanced edits
- Solve button calls the Python DP solver and renders the ledger, objective vector, and validation checks
- Download schedule as Markdown, CSV, or JSON using existing renderer endpoints

## Scripts

| Command         | Description                         |
| --------------- | ----------------------------------- |
| `npm run dev`   | Start development server            |
| `npm run build` | Production build with Turbopack     |
| `npm run start` | Run built app (`npm run build` first)|
| `npm run lint`  | ESLint check                        |

## Next Steps

- Add automated component tests (RTL + Jest/Vitest) and happy-path Playwright E2E.
- Expose solver flags (e.g., `forbid_large_after_day1`) as advanced toggles.
- Implement Next.js route handlers as a proxy to the Python API for same-origin deployments.
