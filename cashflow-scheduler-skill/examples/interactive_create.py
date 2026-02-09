#!/usr/bin/env python3
"""Interactive Plan Creator: Build a plan interactively

This example demonstrates:
1. Interactive plan creation with prompts
2. Building a Plan object step-by-step
3. Saving the plan to JSON
4. Solving the created plan

Usage:
    python examples/interactive_create.py
"""

import json
from pathlib import Path
from typing import List

from core import (
    solve,
    Plan,
    Bill,
    Deposit,
    to_cents,
    cents_to_str,
    validate
)


def get_float(prompt: str, default: float = None) -> float:
    """Get a float input from user"""
    if default is not None:
        prompt = f"{prompt} (default: {default}): "
    else:
        prompt = f"{prompt}: "

    while True:
        value = input(prompt).strip()
        if not value and default is not None:
            return default
        try:
            return float(value)
        except ValueError:
            print("  Please enter a valid number")


def get_int(prompt: str, default: int = None) -> int:
    """Get an integer input from user"""
    if default is not None:
        prompt = f"{prompt} (default: {default}): "
    else:
        prompt = f"{prompt}: "

    while True:
        value = input(prompt).strip()
        if not value and default is not None:
            return default
        try:
            return int(value)
        except ValueError:
            print("  Please enter a valid integer")


def create_bills() -> List[Bill]:
    """Interactively create bills"""
    bills = []
    print("\nAdd Bills (press Enter with empty name to finish)")

    while True:
        name = input(f"  Bill #{len(bills) + 1} name: ").strip()
        if not name:
            break

        day = get_int(f"  Day (1-30)")
        if not (1 <= day <= 30):
            print("    Day must be between 1 and 30")
            continue

        amount = get_float(f"  Amount ($)")
        bills.append(Bill(
            day=day,
            name=name,
            amount_cents=to_cents(amount)
        ))

    return bills


def create_deposits() -> List[Deposit]:
    """Interactively create deposits"""
    deposits = []
    print("\nAdd Deposits (press Enter at day prompt to finish)")

    while True:
        day_str = input(f"  Deposit #{len(deposits) + 1} day (1-30): ").strip()
        if not day_str:
            break

        try:
            day = int(day_str)
            if not (1 <= day <= 30):
                print("    Day must be between 1 and 30")
                continue
        except ValueError:
            print("    Please enter a valid day number")
            continue

        amount = get_float(f"  Amount ($)")
        deposits.append(Deposit(
            day=day,
            amount_cents=to_cents(amount)
        ))

    return deposits


def main():
    print("=== Interactive Cashflow Plan Creator ===\n")

    # Basic parameters
    print("Plan Parameters:")
    start_balance = get_float("Starting balance ($)", default=100.0)
    target_end = get_float("Target ending balance ($)", default=500.0)
    band = get_float("Band tolerance ($)", default=25.0)
    rent_guard = get_float("Rent guard threshold ($)", default=1600.0)

    # Bills
    bills = create_bills()
    print(f"  Added {len(bills)} bills")

    # Deposits
    deposits = create_deposits()
    print(f"  Added {len(deposits)} deposits")

    # Create plan
    plan = Plan(
        start_balance_cents=to_cents(start_balance),
        target_end_cents=to_cents(target_end),
        band_cents=to_cents(band),
        rent_guard_cents=to_cents(rent_guard),
        bills=bills,
        deposits=deposits,
        actions=[None] * 30,
        manual_adjustments=[],
        locks=[],
        metadata={"created_by": "interactive_create.py"}
    )

    print("\n=== Plan Summary ===")
    print(f"Start: ${cents_to_str(plan.start_balance_cents)}")
    print(f"Target: ${cents_to_str(plan.target_end_cents)} ± ${cents_to_str(plan.band_cents)}")
    print(f"Bills: {len(bills)} (total: ${cents_to_str(sum(b.amount_cents for b in bills))})")
    print(f"Deposits: {len(deposits)} (total: ${cents_to_str(sum(d.amount_cents for d in deposits))})")
    print()

    # Solve
    print("Solving...")
    try:
        schedule = solve(plan)
        w, b2b, delta = schedule.objective

        print(f"✅ Solution found!\n")
        print(f"Objective:")
        print(f"  Workdays: {w}")
        print(f"  Back-to-back pairs: {b2b}")
        print(f"  Distance from target: ${cents_to_str(delta)}")
        print()

        # Validate
        report = validate(plan, schedule)
        if report.ok:
            print("✅ Validation passed")
        else:
            print("❌ Validation failed:")
            for name, ok, detail in report.checks:
                if not ok:
                    print(f"  ✗ {name}: {detail}")
        print()

        # Save option
        save = input("Save plan to JSON? (y/n): ").strip().lower()
        if save == 'y':
            filename = input("Filename (default: my_plan.json): ").strip() or "my_plan.json"
            output_path = Path(filename)

            # Convert to JSON-serializable format
            plan_dict = {
                "start_balance": start_balance,
                "target_end": target_end,
                "band": band,
                "rent_guard": rent_guard,
                "bills": [
                    {"day": b.day, "name": b.name, "amount": b.amount_cents / 100}
                    for b in bills
                ],
                "deposits": [
                    {"day": d.day, "amount": d.amount_cents / 100}
                    for d in deposits
                ],
                "actions": [None] * 30,
                "manual_adjustments": [],
                "metadata": plan.metadata
            }

            with open(output_path, 'w') as f:
                json.dump(plan_dict, f, indent=2)

            print(f"✅ Plan saved to {output_path}")

    except RuntimeError as e:
        print(f"❌ No feasible solution found: {e}")
        print("\nTry adjusting:")
        print("  - Increase target band tolerance")
        print("  - Add more deposits or reduce bills")
        print("  - Lower rent guard threshold")


if __name__ == "__main__":
    main()
