# Cashflow Scheduler (DP)

A 30-day cash-flow scheduler that produces feasible, constraint-correct plans using a DP solver over integer cents. CLI provides `solve`, `show`, and `export`.

Quick start:

- Ensure Python 3.11+
- Place a `plan.json` in the project root (see example).
- Run: `python3 -m cashflow.cli solve`

This repository follows the high-level spec in `instructions.md`. Day 1 scope includes the DP engine, ledger/validator, and minimal CLI.

