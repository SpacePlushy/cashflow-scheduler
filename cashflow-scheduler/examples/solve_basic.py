#!/usr/bin/env python3
"""Basic Example: Create and solve a simple cashflow plan

This example demonstrates the core workflow:
1. Create a Plan object with bills, deposits, and constraints
2. Solve using the default solver (CP-SAT with DP fallback)
3. Display the results

Usage:
    python examples/solve_basic.py
"""

import sys
from pathlib import Path

# Add skill root to Python path
skill_root = Path(__file__).parent.parent
sys.path.insert(0, str(skill_root))

from core import solve, Plan, Bill, Deposit, to_cents, cents_to_str, validate


def main():
    print("=== Cashflow Scheduler - Basic Example ===\n")

    # Create a simple plan
    plan = Plan(
        start_balance_cents=to_cents(100.00),
        target_end_cents=to_cents(200.00),
        band_cents=to_cents(50.0),
        rent_guard_cents=to_cents(800.0),
        deposits=[
            Deposit(day=15, amount_cents=to_cents(500.0))
        ],
        bills=[
            Bill(day=5, name="Phone Bill", amount_cents=to_cents(75.0)),
            Bill(day=30, name="Rent", amount_cents=to_cents(800.0))
        ],
        actions=[None] * 30,  # Let solver decide all days
        manual_adjustments=[],
        locks=[],
        metadata={}
    )

    print("Plan Configuration:")
    print(f"  Start Balance: ${cents_to_str(plan.start_balance_cents)}")
    print(f"  Target End: ${cents_to_str(plan.target_end_cents)} ± ${cents_to_str(plan.band_cents)}")
    print(f"  Rent Guard: ${cents_to_str(plan.rent_guard_cents)}")
    print(f"  Bills: {len(plan.bills)} total")
    print(f"  Deposits: {len(plan.deposits)} total")
    print()

    # Solve
    print("Solving...")
    schedule = solve(plan)

    # Display results
    workdays, b2b, abs_diff = schedule.objective
    print(f"✅ Solution found!\n")
    print(f"Objective:")
    print(f"  Workdays: {workdays}")
    print(f"  Back-to-back work pairs: {b2b}")
    print(f"  Distance from target: ${cents_to_str(abs_diff)}")
    print()

    print(f"Schedule: {' '.join(schedule.actions)}")
    print()

    # Validate
    report = validate(plan, schedule)
    print(f"Validation: {'✅ PASS' if report.ok else '❌ FAIL'}")
    for name, ok, detail in report.checks:
        status = '✓' if ok else '✗'
        print(f"  {status} {name}: {detail}")
    print()

    # Show final balance
    print(f"Final Balance: ${cents_to_str(schedule.final_closing_cents)}")


if __name__ == "__main__":
    main()
