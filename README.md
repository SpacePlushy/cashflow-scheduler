# Cashflow Scheduler (DP)

[![CI](https://github.com/SpacePlushy/cashflow-scheduler/actions/workflows/ci.yml/badge.svg)](https://github.com/SpacePlushy/cashflow-scheduler/actions)

A 30-day cash-flow scheduler that produces feasible, constraint-correct plans using a DP solver over integer cents. CLI provides `solve`, `show`, `export`, and `verify` (CP-SAT cross-check).

Quick start:

- Ensure Python 3.11+
- Place a `plan.json` in the project root (see example).
- Run: `python3 -m cashflow.cli solve`
- Verify (requires OR-Tools): `python3 -m cashflow.cli verify`

This repository follows the high-level spec in `instructions.md`. Current scope includes the DP engine, ledger/validator, extensive tests (unit/property/regression), and a CP‑SAT cross‑verifier.
