# Project Progress

This document tracks implementation status against the plan in `instructions.md` (§9 Project Plan) and the Web UI plan in `docs/web_ui_plan.md`.

## Summary

- Core engine and CLI through Day 4 are complete. Day 2 “resume” flows are exposed via `set-eod` and `solve --from`.
- Advanced extras: Pareto ties and “why” explanations implemented; additional export formats (CSV/JSON) added.
- Tests (unit, property, regression) and CI are set up and green locally.
- Web UI work has not started.

## Detailed Checklist (Core, §9)

Day 1 (repo + DP + validator + basic CLI + initial tests)

- [x] Create repo structure (cashflow/{core,engines,io}, tests, Makefile)
- [x] DP solver (`cashflow/engines/dp.py`)
- [x] Validator (`cashflow/core/validate.py`)
- [x] CLI commands: `solve`, `show`, `export` (`cashflow/cli.py`)
- [x] Tests: basic unit + one regression (`cashflow/tests/`)

Day 2 (resume semantics)

- [x] Manual adjustment + recompute prefix supported in data model and solver (`Plan.manual_adjustments` used in prefix; tests cover resume)
- [x] Seeded DP API `solve_from()` (locks prefix and re-solves tail; convenience)
- [x] CLI: `set-eod` and `solve --from` (implemented in `cashflow/cli.py`)
- [x] Tests: resume scenarios and Off‑Off across boundary (`test_resume_manual_adjustment.py`, property tests)

Day 3 (CP‑SAT cross‑verification)

- [x] CP‑SAT model and sequential lex optimization (`cashflow/engines/cpsat.py`)
- [x] `verify` CLI command (`python -m cashflow.cli verify`)

Day 4 (extras)

- [x] Pareto (`pareto`) frontier of lex‑ties (CP‑SAT enumeration; requires OR‑Tools)
- [x] “Why” local counterfactual/explanations (`cash why <day>`)

Day 5 (polish & exports & options)

- [x] Exports: Markdown, CSV, and JSON supported via `cash export --format`
- [~] Error messages/guardrails: added friendly failure hints on `solve`; richer certificates TBD
- [x] CLI options: `--forbid-large-after-day1`, `--target`, `--band` (solve-time overrides)

Day 6–7 (tests, CI, docs)

- [x] Property tests (Hypothesis) and regression tests
- [x] CI workflow (lint, type, test) under GitHub Actions
- [x] Documentation: README and spec (`instructions.md`)

## Web UI Plan (docs/web_ui_plan.md)

- [x] Backend FastAPI app under `cashflow/api/` (MVP endpoints implemented)
- [x] SPA scaffold under `ui/` (Vite React/TS) with basic Schedule screen and API wiring
- [x] API endpoints: `/health`, `/plan`, `/solve`, `/set-eod`, `/verify`, `/export`, `/ties`
- [x] UI: table render, EOD edit + re‑solve, validation panel
- [ ] UI: diff view, verify panel polish, settings page

## Artifacts and References

- CLI entry: `cashflow/cli.py:20`
- DP engine: `cashflow/engines/dp.py:43`
- Validator: `cashflow/core/validate.py:28`
- Ledger: `cashflow/core/ledger.py:8`
- Model/types: `cashflow/core/model.py:31`
- Plan loader: `cashflow/io/store.py:9`
- Markdown renderer: `cashflow/io/render.py:8`
- CP‑SAT verify: `cashflow/engines/cpsat.py:171`
- DP solve_from: `cashflow/engines/dp.py:140`
- Tests: `cashflow/tests/unit/test_cli.py:9`, `cashflow/tests/unit/test_resume_manual_adjustment.py:19`, `cashflow/tests/property/test_resume_random_single_adjustment.py:28`, `cashflow/tests/regression/test_regression_objective.py:5`
- CI: `.github/workflows/ci.yml:1`

## Next Steps

1) Improve infeasibility certificates (“what to relax”) and guardrail messages.
2) Add unit tests for new CLI commands (`why`, `pareto`, `set-eod`, exports CSV/JSON).
3) If desired, start Web UI scaffolding per `docs/web_ui_plan.md`.
