#!/usr/bin/env python3
"""Compare Solvers: Benchmark DP vs CP-SAT solvers

This example demonstrates:
1. Running both DP and CP-SAT solvers on the same plan
2. Comparing their results and performance
3. Verifying they produce equivalent solutions

Usage:
    python examples/compare_solvers.py
"""

import sys
import time
from pathlib import Path

# Add skill root to Python path
skill_root = Path(__file__).parent.parent
sys.path.insert(0, str(skill_root))

from core import (
    solve,
    Plan,
    Bill,
    Deposit,
    to_cents,
    cents_to_str,
    dp_solver,
    cpsat_solver,
)


def create_test_plan() -> Plan:
    """Create a moderately complex test plan"""
    return Plan(
        start_balance_cents=to_cents(90.50),
        target_end_cents=to_cents(490.50),
        band_cents=to_cents(25.0),
        rent_guard_cents=to_cents(1636.0),
        deposits=[
            Deposit(day=11, amount_cents=to_cents(1021.0)),
            Deposit(day=25, amount_cents=to_cents(1021.0)),
        ],
        bills=[
            Bill(day=1, name="Auto Insurance", amount_cents=to_cents(177.0)),
            Bill(day=3, name="Internet", amount_cents=to_cents(75.0)),
            Bill(day=7, name="Streaming Services", amount_cents=to_cents(50.0)),
            Bill(day=15, name="Utilities", amount_cents=to_cents(120.0)),
            Bill(day=20, name="Phone", amount_cents=to_cents(85.0)),
            Bill(day=30, name="Rent", amount_cents=to_cents(1636.0)),
        ],
        actions=[None] * 30,
        manual_adjustments=[],
        locks=[],
        metadata={}
    )


def main():
    print("=== Solver Comparison: DP vs CP-SAT ===\n")

    plan = create_test_plan()

    print("Test Plan:")
    print(f"  Start Balance: ${cents_to_str(plan.start_balance_cents)}")
    print(f"  Target End: ${cents_to_str(plan.target_end_cents)} ± ${cents_to_str(plan.band_cents)}")
    print(f"  Bills: {len(plan.bills)} (total ${cents_to_str(sum(b.amount_cents for b in plan.bills))})")
    print(f"  Deposits: {len(plan.deposits)} (total ${cents_to_str(sum(d.amount_cents for d in plan.deposits))})")
    print()

    # Solve with DP
    print("Running DP solver...")
    start = time.time()
    try:
        dp_schedule = dp_solver.solve(plan)
        dp_time = time.time() - start
        dp_available = True
    except Exception as e:
        print(f"  DP solver failed: {e}")
        dp_available = False
        dp_time = 0
        dp_schedule = None

    # Solve with CP-SAT
    print("Running CP-SAT solver...")
    start = time.time()
    try:
        cpsat_result = cpsat_solver.solve_with_diagnostics(plan, dp_fallback=False)
        cpsat_time = time.time() - start
        cpsat_schedule = cpsat_result.schedule
        cpsat_available = True
    except Exception as e:
        print(f"  CP-SAT solver failed (likely OR-Tools not installed): {e}")
        cpsat_available = False
        cpsat_time = 0
        cpsat_schedule = None

    print()

    # Compare results
    if dp_available and cpsat_available:
        print("=== Comparison Results ===\n")

        print(f"{'Metric':<30} {'DP':<20} {'CP-SAT':<20} {'Match':<10}")
        print("-" * 80)

        # Objective comparison
        dp_w, dp_b2b, dp_delta = dp_schedule.objective
        cp_w, cp_b2b, cp_delta = cpsat_schedule.objective

        print(f"{'Workdays':<30} {dp_w:<20} {cp_w:<20} {'✓' if dp_w == cp_w else '✗':<10}")
        print(f"{'Back-to-back pairs':<30} {dp_b2b:<20} {cp_b2b:<20} {'✓' if dp_b2b == cp_b2b else '✗':<10}")
        print(f"{'Abs diff from target':<30} {dp_delta:<20} {cp_delta:<20} {'✓' if dp_delta == cp_delta else '✗':<10}")
        print(f"{'Final balance':<30} ${cents_to_str(dp_schedule.final_closing_cents):<19} ${cents_to_str(cpsat_schedule.final_closing_cents):<19} {'✓' if dp_schedule.final_closing_cents == cpsat_schedule.final_closing_cents else '✗':<10}")
        print()

        # Performance comparison
        print(f"{'Solve time (seconds)':<30} {dp_time:.4f}{'s':<15} {cpsat_time:.4f}{'s':<15}")
        speedup = cpsat_time / dp_time if dp_time > 0 else 0
        print(f"{'Speed comparison':<30} {'Baseline':<20} {f'{speedup:.2f}x vs DP' if speedup > 0 else 'N/A':<20}")
        print()

        # Schedule comparison
        same_schedule = dp_schedule.actions == cpsat_schedule.actions
        print(f"Schedules identical: {'✓ Yes' if same_schedule else '✗ No (but may be equivalent)'}")

        if not same_schedule:
            print("\nNote: Different schedules with same objective are both optimal (ties).")
            print("DP schedule:", ' '.join(dp_schedule.actions[:10]), "...")
            print("CP schedule:", ' '.join(cpsat_schedule.actions[:10]), "...")

    elif dp_available:
        print("✅ DP solver works")
        print("❌ CP-SAT solver unavailable (install OR-Tools: pip install ortools)")
        print(f"\nDP Result: {dp_schedule.objective}")
        print(f"DP Time: {dp_time:.4f}s")

    elif cpsat_available:
        print("❌ DP solver failed")
        print("✅ CP-SAT solver works")
        print(f"\nCP-SAT Result: {cpsat_schedule.objective}")
        print(f"CP-SAT Time: {cpsat_time:.4f}s")

    else:
        print("❌ Both solvers failed!")

    print()


if __name__ == "__main__":
    main()
