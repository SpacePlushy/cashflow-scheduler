---
name: cashflow-scheduler
description: Plan optimal work schedules around bills and cashflow constraints while minimizing workdays
---

# Cashflow Scheduler

## Overview

This skill optimizes 30-day work schedules for cashflow management. It solves: *"Given my bills, deposits, and target balance, what's the optimal work schedule that minimizes workdays while maintaining positive daily balances?"*

**Key Features:**
- Dual solvers: CP-SAT (OR-Tools) primary with automatic DP fallback
- Lexicographic optimization: Minimize workdays → back-to-back work → distance from target
- Constraint validation: Ensures non-negative balances, rent guard, and final band requirements
- Self-contained: Works immediately, no installation required

**When to use this skill:**
- User needs to plan gig work schedule (DoorDash, Uber, freelance)
- Optimizing work-life balance while meeting financial obligations
- Ensuring enough cash for rent while saving towards target
- Comparing different financial scenarios
- Mid-month adjustments based on actual balance

## Quick Start

### Generate Default Schedule (Fastest)

```python
from core import solve, Plan, Bill, Deposit, to_cents

# Create plan with bills and deposits
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
        Bill(day=30, name="Rent", amount_cents=to_cents(1636.0))
        # ... add more bills
    ],
    actions=[None] * 30
)

# Solve and get optimal schedule
schedule = solve(plan)

# Display results
print(f"Workdays: {schedule.objective[0]}")
print(f"Schedule: {' '.join(schedule.actions)}")
print(f"Work on days: {[i+1 for i, a in enumerate(schedule.actions) if a == 'Spark']}")
```

**Or use:** `python examples/create_default.py` for a complete working example.

### Mid-Month Adjustment (Primary Use Case)

**Scenario:** You're on day 20 with $230 actual balance. What should you do for the rest of the month?

```python
from core import adjust_from_day

# Adjust from current day with actual balance
new_schedule = adjust_from_day(
    original_plan=plan,
    current_day=20,
    current_eod_balance=230.00
)

# See what to do for days 21-30
print(f"Days 21-30: {' '.join(new_schedule.actions[20:])}")
work_days = [i+1 for i, a in enumerate(new_schedule.actions[20:], start=20) if a == 'Spark']
print(f"Work on days: {work_days}")
```

## Common Workflows

### 1. Basic Schedule Optimization
**User:** "Plan my October work schedule. I have rent on the 30th and want to save $500."
1. Create Plan with bills, deposits, targets
2. Call `solve(plan)`
3. Validate with `validate(plan, schedule)`
4. Display work schedule

**See:** `examples/solve_basic.py`

### 2. Load and Solve from JSON
**User:** "Here's my plan.json file, can you optimize it?"
1. Load JSON into Plan object
2. Call `solve(plan)`
3. Show ledger with daily balances

**See:** `examples/solve_from_json.py`

### 3. Iterative Adjustments
**User:** "Can you make me work less?" or "What if I move my internet bill to the 15th?"

```python
# Fewer workdays? Increase band tolerance
plan.band_cents = to_cents(150.0)  # Was 100.0
schedule = solve(plan)

# Lock specific days off
plan.actions[5:8] = ["O", "O", "O"]  # Days 6-8 off
schedule = solve(plan)

# Move a bill
for bill in plan.bills:
    if bill.name == "Internet":
        plan.bills.remove(bill)
        plan.bills.append(Bill(day=15, name="Internet", amount_cents=bill.amount_cents))
        break
schedule = solve(plan)
```

### 4. Compare Scenarios
**User:** "What if I delay my internet bill to the 15th instead of the 5th?"
1. Create two Plan variants
2. Solve both with `solve()`
3. Compare objectives and schedules

**See:** `examples/compare_solvers.py`

## Core Concepts

### Plan Object
Defines the problem:
- `start_balance_cents`: Starting cash on Day 1
- `target_end_cents`: Desired ending balance on Day 30
- `band_cents`: Tolerance around target (±)
- `rent_guard_cents`: Minimum balance before paying rent
- `deposits`: List of cash inflows (paychecks)
- `bills`: List of cash outflows (rent, utilities)
- `actions`: Pre-filled days (None = solver decides)

### Schedule Object
Contains the solution:
- `actions`: 30-element list of "O" (off) or "Spark" (work)
- `objective`: (workdays, back_to_back_pairs, abs_diff_from_target)
- `final_closing_cents`: Final balance on Day 30
- `ledger`: Daily ledger entries

### Constraints
**Hard (must satisfy):**
- Day 1 must be "Spark" (work day)
- Daily closing balances ≥ 0
- Day 30 pre-rent balance ≥ rent_guard
- Final balance in [target - band, target + band]

**Soft (optimized lexicographically):**
1. Minimize total workdays
2. Minimize back-to-back work pairs
3. Minimize distance from exact target

## Troubleshooting

### "No feasible schedule found"
**Causes:** Bills exceed income, target too high, band too tight

**Solutions:**
```python
plan.band_cents = to_cents(150.0)  # Increase tolerance
plan.target_end_cents = to_cents(400.0)  # Lower target
plan.deposits.append(Deposit(day=15, amount_cents=to_cents(200.0)))  # Add income
```

### "OR-Tools CP-SAT not installed"
**Solution:** `pip install ortools` or use auto-fallback: `solve(plan)`

## Available Resources

### Example Scripts (`examples/`)
- `create_default.py` - Quick start with real-world data
- `solve_basic.py` - Basic solve workflow
- `solve_from_json.py` - Load and solve JSON plans
- `compare_solvers.py` - Benchmark DP vs CP-SAT
- `interactive_create.py` - Interactive plan builder

### Reference Documentation (`references/`)
- `api.md` - Complete API reference
- `advanced.md` - Advanced usage patterns
- `plan_schema.md` - JSON schema documentation
- `constraints.md` - Constraint system details
- `troubleshooting.md` - Common issues and solutions

### Example Plans (`assets/example_plans/`)
- `default_plan.json` - Real-world monthly budget
- `simple_plan.json` - Basic example with minimal bills

## Tips for Success

1. **Start simple:** Use `examples/create_default.py` as a template
2. **Validate always:** Check `validate(plan, schedule).ok` before trusting results
3. **Use auto-fallback:** Default `solve(plan)` ensures robustness
4. **Increase band if infeasible:** Try $50-150 instead of $25
5. **Check total funds:** Ensure start + deposits ≥ bills + target
6. **Prefer fewer locks:** Only lock days if absolutely necessary

## See Also

- [API Reference](references/api.md) - Complete function documentation
- [Advanced Usage](references/advanced.md) - Solver options, manual adjustments, locking
- [JSON Schema](references/plan_schema.md) - Complete JSON format
- [Constraints](references/constraints.md) - Constraint system deep dive
- [Troubleshooting](references/troubleshooting.md) - Debugging guide
