# CP-SAT Migration Plan

## Goal
Replace the DP solver as the primary execution engine with the CP-SAT optimizer (Google OR-Tools) across API, CLI, and UI, while retaining DP for validation/fallback.

## Why CP-SAT
- Guarantees lexicographic optimality using a single source of truth (currently only a verifier).
- Supports richer constraints or objectives in the future without DP-state explosion.
- Aligns with the upcoming web UI focus: users trigger solves through the API, so we can afford SAT solve times.

## High-Level Workstream Breakdown
1. **Solver API Surface**
   - Expose `cpsat.solve(plan, *, seed_dp=False)` returning `Schedule` identical to DP.
   - Allow optional DP seeding to warm-start (extract DP objective to prioritize search).
   - Keep a `cpsat.verify_and_enrich(dp_schedule)` helper for customers who still run DP locally.

2. **Backend (API)**
   - `/solve`: call CP-SAT by default, fall back to DP on solver failure/timeouts.
   - `/set_eod`: run DP to generate adjusted plan, then solve with CP-SAT.
   - `/export`: ensure payloads come from CP-SAT schedule.
   - Add startup check for OR-Tools availability; raise descriptive error if missing.
   - Expose metrics (solve time, fail reason) inside response for UI to display.

3. **CLI**
   - Update `python -m cashflow.cli solve` to use CP-SAT, with `--use-dp` override.
   - `verify`: restructure to run DP first (if requested) then CP-SAT, showing comparison.
   - Add flags for solver timeouts, max search nodes, random seed.

4. **UI**
   - Update copy: “Powered by Google OR-Tools (CP-SAT)”
   - Show solver duration / status in ResultsView.
   - Provide advanced toggle to run DP fallback (disambiguate why output differs).

5. **Testing**
   - Expand regression fixtures to validate CP-SAT schedule matches historic DP results.
   - Add unit tests ensuring `/solve` returns expected structure with CP-SAT.
   - Create integration test calling CP-SAT from the API route (guards import errors).
   - Ensure tests handle missing OR-Tools gracefully (skip or clear messaging).

6. **Docs & Tooling**
   - README, instructions, AGENTS: highlight CP-SAT as primary engine, DP as fallback.
   - Note `pip install ortools>=9.8` requirement (and platform wheel caveats).
   - Update `scripts/dev_run_all.sh` to check for OR-Tools and guide installation.
   - Provide a migration FAQ: expected runtime differences, tie behavior, how to re-enable DP.

## Delivery Phases
1. **Phase 1 – Solver Core**
   - Implement `cpsat.solve()` public API, wrap OR-Tools invocation, and validate output.
   - Add solver-level unit tests and docstrings.

2. **Phase 2 – API/CLI Integration**
   - Wire CP-SAT into `/solve`, CLI, and `/set_eod` flows.
   - Add fallback + error handling.

3. **Phase 3 – UI & UX**
   - Update frontend to reflect new solver, surface solve metadata, add advanced toggles.

4. **Phase 4 – Test & Docs**
   - Beef up regression coverage, finalize documentation, and ensure CI includes OR-Tools steps.

## Risks & Mitigations
- **Performance regressions**: large solve times vs DP. Mitigate with DP warm start and sensible timeouts.
- **OR-Tools availability**: wheels missing on some platforms. Provide install and docker guidance.
- **Different tie-break behavior**: document expected differences; consider storing objective metadata in responses.
- **API consumers relying on DP**: keep DP accessible via flag/env var for transitional period.

## Definition of Done
- `/solve` defaults to CP-SAT, CLI/UI reflect change, and DP remains accessible as fallback.
- Automated tests verifying CP-SAT output run in CI (with OR-Tools installed).
- Docs updated; script/tooling warn if OR-Tools missing.
- Web UI shows CP-SAT metadata (solver time/status) and optionally DP toggle.
