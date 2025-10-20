#!/usr/bin/env python3
"""Test the default snippet from SKILL.md"""

import sys
from pathlib import Path

skill_root = Path(__file__).parent
sys.path.insert(0, str(skill_root))

from core import solve, Plan, Bill, Deposit, to_cents, cents_to_str

# Default plan from plan.json (real-world example)
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

schedule = solve(plan)

# Show results
w, b2b, diff = schedule.objective
print(f"✅ Schedule created!")
print(f"Workdays: {w}")
print(f"Schedule: {' '.join(schedule.actions)}")
print(f"Work on days: {[i+1 for i, a in enumerate(schedule.actions) if a == 'Spark']}")
