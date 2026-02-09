#!/usr/bin/env python3
"""Create Default Schedule - Quick Start Example

This script demonstrates the complete workflow:
1. Create a default plan (always works)
2. Solve and display the schedule
3. Show how to make common adjustments

Usage:
    python examples/create_default.py
"""

import sys
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


def create_default_plan():
    """Create the default plan from plan.json (real-world example)

    This plan represents a realistic monthly budget:
    - Starting with $90.50
    - Two paycheck deposits (days 10 and 24)
    - All monthly bills: groceries, subscriptions, utilities, rent, etc.
    - Target: maintain starting balance by month end
    - Wide band for flexibility ([$0, $190.50])

    This is the ACTUAL plan from plan.json in the repository.
    """
    return Plan(
        start_balance_cents=to_cents(90.50),
        target_end_cents=to_cents(90.50),
        band_cents=to_cents(100.0),  # Wide band: [$0, $190.50]
        rent_guard_cents=to_cents(1636.0),
        deposits=[
            Deposit(day=10, amount_cents=to_cents(1021.0)),
            Deposit(day=24, amount_cents=to_cents(1021.0))
        ],
        bills=[
            Bill(day=1, name="Auto Insurance", amount_cents=to_cents(108.0)),
            Bill(day=2, name="YouTube Premium", amount_cents=to_cents(8.0)),
            Bill(day=5, name="Groceries", amount_cents=to_cents(112.5)),
            Bill(day=5, name="Weed", amount_cents=to_cents(20.0)),
            Bill(day=6, name="Electric", amount_cents=to_cents(139.0)),
            Bill(day=8, name="Paramount Plus", amount_cents=to_cents(12.0)),
            Bill(day=8, name="iPad AppleCare", amount_cents=to_cents(8.49)),
            Bill(day=10, name="Streaming Svcs", amount_cents=to_cents(230.0)),
            Bill(day=10, name="AI Subscription", amount_cents=to_cents(220.0)),
            Bill(day=11, name="Cat Food", amount_cents=to_cents(40.0)),
            Bill(day=12, name="Groceries", amount_cents=to_cents(112.5)),
            Bill(day=12, name="Weed", amount_cents=to_cents(20.0)),
            Bill(day=14, name="iPad AppleCare", amount_cents=to_cents(8.49)),
            Bill(day=16, name="Cat Food", amount_cents=to_cents(40.0)),
            Bill(day=19, name="Groceries", amount_cents=to_cents(112.5)),
            Bill(day=19, name="Weed", amount_cents=to_cents(20.0)),
            Bill(day=22, name="Cell Phone", amount_cents=to_cents(177.0)),
            Bill(day=23, name="Cat Food", amount_cents=to_cents(40.0)),
            Bill(day=25, name="Ring Subscription", amount_cents=to_cents(10.0)),
            Bill(day=26, name="Groceries", amount_cents=to_cents(112.5)),
            Bill(day=26, name="Weed", amount_cents=to_cents(20.0)),
            Bill(day=28, name="iPhone AppleCare", amount_cents=to_cents(13.49)),
            Bill(day=29, name="Internet", amount_cents=to_cents(30.0)),
            Bill(day=29, name="Cat Food", amount_cents=to_cents(40.0)),
            Bill(day=30, name="Rent", amount_cents=to_cents(1636.0))
        ],
        actions=[None] * 30,  # Let solver decide all days
        manual_adjustments=[],
        locks=[],
        metadata={"template": "default", "source": "plan.json"}
    )


def display_schedule(schedule, title="Schedule"):
    """Display schedule in a nice format"""
    w, b2b, diff = schedule.objective

    print(f"\n{'=' * 60}")
    print(f"{title}")
    print('=' * 60)
    print(f"Objective:")
    print(f"  Workdays: {w}")
    print(f"  Back-to-back pairs: {b2b}")
    print(f"  Distance from target: ${cents_to_str(diff)}")
    print(f"  Final balance: ${cents_to_str(schedule.final_closing_cents)}")
    print()

    # Display calendar view
    print("30-Day Calendar:")
    for i in range(0, 30, 10):
        days = ' '.join(f"Day {j+1:2d}" for j in range(i, min(i+10, 30)))
        actions = '  '.join(f"{schedule.actions[j]:5s}" for j in range(i, min(i+10, 30)))
        print(f"  {days}")
        print(f"  {actions}")
        print()

    # Show work days
    work_days = [i+1 for i, a in enumerate(schedule.actions) if a == "Spark"]
    print(f"Work days: {work_days}")
    print(f"Summary: {w} work days, {30-w} off days")


def show_adjustment_examples(base_plan):
    """Show common adjustment patterns"""
    print("\n" + "=" * 60)
    print("COMMON ADJUSTMENTS (Examples)")
    print("=" * 60)

    print("\n1️⃣  Want to work LESS? Increase the band tolerance:")
    print("   plan.band_cents = to_cents(150.0)  # Was 100.0")

    print("\n2️⃣  Want to work MORE (save more)? Increase target:")
    print("   plan.target_end_cents = to_cents(300.0)  # Was 100.0")

    print("\n3️⃣  Need specific days OFF? Lock them:")
    print("   plan.actions[5:8] = ['O', 'O', 'O']  # Days 6-8 off")

    print("\n4️⃣  Add a new bill? Append it:")
    print("   plan.bills.append(Bill(day=15, name='Utilities', amount_cents=to_cents(120.0)))")

    print("\n5️⃣  One-time expense? Use adjustment:")
    print("   plan.manual_adjustments.append(Adjustment(day=12, amount_cents=to_cents(-75.0), note='Car repair'))")

    print("\n" + "=" * 60)


def main():
    print("=" * 60)
    print("CASHFLOW SCHEDULER - DEFAULT SCHEDULE")
    print("=" * 60)

    # Create default plan
    print("\n📋 Creating default plan...")
    plan = create_default_plan()

    print(f"  Start Balance: ${cents_to_str(plan.start_balance_cents)}")
    print(f"  Target End: ${cents_to_str(plan.target_end_cents)} ± ${cents_to_str(plan.band_cents)}")
    print(f"  Rent Guard: ${cents_to_str(plan.rent_guard_cents)}")
    print(f"  Deposits: {len(plan.deposits)} scheduled")
    print(f"  Bills: {len(plan.bills)} scheduled")

    # Solve
    print("\n🔍 Solving schedule...")
    schedule = solve(plan)

    # Validate
    report = validate(plan, schedule)
    if report.ok:
        print("✅ Schedule is valid and meets all constraints!")
    else:
        print("⚠️  Schedule has validation issues:")
        for name, ok, detail in report.checks:
            if not ok:
                print(f"  ✗ {name}: {detail}")

    # Display
    display_schedule(schedule, "✅ DEFAULT SCHEDULE CREATED")

    # Show sample ledger
    print("\n💰 Sample Daily Ledger (first 5 days):")
    print("-" * 60)
    for entry in schedule.ledger[:5]:
        print(
            f"  Day {entry.day:2d}: {entry.action:5s} | "
            f"Open: ${cents_to_str(entry.opening_cents):>8s} | "
            f"Close: ${cents_to_str(entry.closing_cents):>8s}"
        )
    print("  ...")
    last = schedule.ledger[-1]
    print(
        f"  Day {last.day:2d}: {last.action:5s} | "
        f"Open: ${cents_to_str(last.opening_cents):>8s} | "
        f"Close: ${cents_to_str(last.closing_cents):>8s}"
    )

    # Show how to make adjustments
    show_adjustment_examples(plan)

    print("\n💡 TIP: Copy the code from this script to make your own custom plan!")
    print("     Or load from JSON: see examples/solve_from_json.py")
    print("\n" + "=" * 60)


if __name__ == "__main__":
    main()
