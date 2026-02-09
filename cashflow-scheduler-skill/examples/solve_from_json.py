#!/usr/bin/env python3
"""Load and Solve: Load a plan from JSON file and solve it

This example shows how to:
1. Load a plan.json file
2. Parse it into a Plan object
3. Solve it
4. Display detailed ledger information

Usage:
    python examples/solve_from_json.py [path/to/plan.json]

If no path is provided, uses assets/example_plans/simple_plan.json
"""

import sys
import json
from pathlib import Path

# Add skill root to Python path
skill_root = Path(__file__).parent.parent
sys.path.insert(0, str(skill_root))

from core import (
    solve,
    Plan,
    Bill,
    Deposit,
    Adjustment,
    to_cents,
    cents_to_str,
    validate
)


def load_plan_from_json(path: Path) -> Plan:
    """Load a Plan from a JSON file"""
    with open(path) as f:
        data = json.load(f)

    return Plan(
        start_balance_cents=to_cents(data['start_balance']),
        target_end_cents=to_cents(data['target_end']),
        band_cents=to_cents(data['band']),
        rent_guard_cents=to_cents(data['rent_guard']),
        deposits=[
            Deposit(day=d['day'], amount_cents=to_cents(d['amount']))
            for d in data.get('deposits', [])
        ],
        bills=[
            Bill(day=b['day'], name=b['name'], amount_cents=to_cents(b['amount']))
            for b in data.get('bills', [])
        ],
        actions=data.get('actions', [None] * 30),
        manual_adjustments=[
            Adjustment(
                day=a['day'],
                amount_cents=to_cents(a['amount']),
                note=a.get('note', '')
            )
            for a in data.get('manual_adjustments', [])
        ],
        locks=data.get('locks', []),
        metadata=data.get('metadata', {})
    )


def main():
    # Determine plan path
    if len(sys.argv) > 1:
        plan_path = Path(sys.argv[1])
    else:
        plan_path = Path(__file__).parent.parent / "assets" / "example_plans" / "simple_plan.json"

    print(f"=== Loading plan from {plan_path} ===\n")

    # Load plan
    plan = load_plan_from_json(plan_path)

    print("Plan loaded successfully!")
    print(f"  Start: ${cents_to_str(plan.start_balance_cents)}")
    print(f"  Target: ${cents_to_str(plan.target_end_cents)} ± ${cents_to_str(plan.band_cents)}")
    print(f"  Bills: {len(plan.bills)}")
    print(f"  Deposits: {len(plan.deposits)}")
    print()

    # Solve
    print("Solving...")
    schedule = solve(plan)

    # Results
    w, b2b, delta = schedule.objective
    print(f"✅ Solution found!\n")
    print(f"Objective: ({w} workdays, {b2b} back-to-back, ${cents_to_str(delta)} from target)\n")

    # Validate
    report = validate(plan, schedule)
    print(f"Validation: {'✅ PASS' if report.ok else '❌ FAIL'}")
    for name, ok, detail in report.checks:
        status = '✓' if ok else '✗'
        print(f"  {status} {name}")
    print()

    # Show first 5 days of ledger
    print("Daily Ledger (first 5 days):")
    print(f"{'Day':>4} {'Opening':>10} {'Deposits':>10} {'Action':>7} {'Bills':>10} {'Closing':>10}")
    print("-" * 61)
    for entry in schedule.ledger[:5]:
        print(
            f"{entry.day:>4} "
            f"${cents_to_str(entry.opening_cents):>9} "
            f"${cents_to_str(entry.deposit_cents):>9} "
            f"{entry.action:>7} "
            f"${cents_to_str(entry.bills_cents):>9} "
            f"${cents_to_str(entry.closing_cents):>9}"
        )
    print("...")
    print()

    # Show work schedule
    print("Work Schedule:")
    work_days = [i + 1 for i, a in enumerate(schedule.actions) if a == "Spark"]
    print(f"Work on days: {', '.join(map(str, work_days))}")
    print(f"Total workdays: {len(work_days)}")


if __name__ == "__main__":
    main()
