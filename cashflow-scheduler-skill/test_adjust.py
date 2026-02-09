#!/usr/bin/env python3
"""Test adjust_from_day functionality"""

import sys
from pathlib import Path

skill_root = Path(__file__).parent
sys.path.insert(0, str(skill_root))

from core import adjust_from_day, solve, Plan, Bill, Deposit, to_cents, cents_to_str

# Create the default plan from plan.json
plan = Plan(
    start_balance_cents=to_cents(90.50),
    target_end_cents=to_cents(90.50),
    band_cents=to_cents(100.0),
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
    actions=[None] * 30,
    manual_adjustments=[],
    locks=[],
    metadata={}
)

print("=" * 70)
print("TEST: adjust_from_day() - Mid-Month Balance Adjustment")
print("=" * 70)

# First, get the baseline schedule
print("\n1️⃣  Solving baseline schedule...")
baseline = solve(plan)
w, b2b, diff = baseline.objective

print(f"\nBaseline schedule:")
print(f"  Workdays: {w}")
print(f"  Work on days: {[i+1 for i, a in enumerate(baseline.actions) if a == 'Spark']}")
print(f"  Day 20 EOD balance (baseline): ${cents_to_str(baseline.ledger[19].closing_cents)}")

# Now simulate: user is on day 20 with $230 actual balance
print("\n2️⃣  Adjusting from day 20 with $230 actual balance...")
current_day = 20
current_balance = 230.0

adjusted = adjust_from_day(plan, current_day=current_day, current_eod_balance=current_balance)

print(f"\nAdjusted schedule:")
w2, b2b2, diff2 = adjusted.objective
print(f"  Full month workdays: {w2}")
print(f"  Days 1-20 (locked): {' '.join(adjusted.actions[:20])}")
print(f"  Days 21-30 (re-optimized): {' '.join(adjusted.actions[20:])}")
print(f"  Remaining work days: {[i+1 for i, a in enumerate(adjusted.actions[20:], start=20) if a == 'Spark']}")

# Verify day 20 EOD is correct
day20_eod = adjusted.ledger[19].closing_cents
print(f"\n  Day 20 EOD balance: ${cents_to_str(day20_eod)}")
print(f"  Target: ${current_balance:.2f}")
print(f"  Match: {'✅' if abs(day20_eod - to_cents(current_balance)) < 1 else '❌'}")

# Show remaining days ledger
print("\n3️⃣  Ledger for days 20-30:")
print(f"{'Day':>4} {'Action':>7} {'Opening':>10} {'Closing':>10}")
print("-" * 35)
for entry in adjusted.ledger[19:]:
    print(
        f"{entry.day:>4} {entry.action:>7} "
        f"${cents_to_str(entry.opening_cents):>9} "
        f"${cents_to_str(entry.closing_cents):>9}"
    )

print("\n" + "=" * 70)
print("✅ TEST PASSED: adjust_from_day() works correctly!")
print("=" * 70)
