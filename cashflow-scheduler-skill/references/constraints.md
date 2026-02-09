# Constraint System Documentation

This document describes all constraints enforced by the cashflow scheduler solvers.

## Overview

The solver must find a 30-day schedule of actions ("O" for off, "Spark" for work) that satisfies all hard constraints while optimizing the objective function.

## Hard Constraints

These constraints **must** be satisfied for a schedule to be feasible.

### 1. Day 1 Must Be Work Day

**Rule:** Day 1 action must always be "Spark" (work day)

**Rationale:** Business rule to ensure early income

**Violation:** Schedule is invalid if Day 1 is not "Spark"

**Example:**
```python
# Valid
schedule.actions[0] == "Spark"  # ✓

# Invalid
schedule.actions[0] == "O"  # ✗
```

### 2. Non-Negative Daily Closing Balances

**Rule:** Closing balance must be ≥ 0 at end of each day

**Formula:** For each day t (1-30):
```
closing[t] = opening[t] + deposits[t] + action_net[t] - bills[t] >= 0
```

**Rationale:** Cannot have negative bank balance

**Violation:** Schedule is infeasible if any day ends negative

**Example:**
```
Day 5:
  Opening: $50
  Deposits: $0
  Action: O ($0 net)
  Bills: $75
  Closing: $50 + $0 + $0 - $75 = -$25  # ✗ INVALID
```

### 3. Day 30 Pre-Rent Guard

**Rule:** Balance before paying rent on Day 30 must be ≥ rent_guard

**Formula:**
```
balance_before_rent = start_balance + sum(all_deposits) + sum(all_action_nets) - sum(bills[1:29]) >= rent_guard
```

**Rationale:** Ensures rent can be paid

**Violation:** Schedule is infeasible if pre-rent balance < rent_guard

**Example:**
```
Plan: rent_guard = $1636

Day 30 before rent bill:
  Balance: $1650  # ✓ >= $1636

Day 30 before rent bill:
  Balance: $1600  # ✗ < $1636
```

### 4. Final Balance Within Band

**Rule:** Final closing balance on Day 30 must be within target ± band

**Formula:**
```
target_end - band <= final_closing <= target_end + band
```

**Rationale:** Achieve desired ending balance with tolerance

**Violation:** Schedule is infeasible if final balance outside band

**Example:**
```
Plan: target_end = $500, band = $25

Valid range: [$475, $525]

final_closing = $490  # ✓
final_closing = $510  # ✓
final_closing = $530  # ✗
final_closing = $470  # ✗
```

### 5. Locked Actions Must Be Honored

**Rule:** If plan.actions[i] is not None, schedule must use that exact action

**Example:**
```python
plan.actions = [None, "O", None, "Spark", ...]

# Valid schedule
schedule.actions = ["Spark", "O", "Spark", "Spark", ...]  # ✓

# Invalid schedule
schedule.actions = ["Spark", "Spark", "Spark", "Spark", ...]  # ✗ Day 2 must be "O"
```

## Soft Constraints (Objectives)

These are optimized lexicographically in order of priority.

### Priority 1: Minimize Workdays

**Goal:** Minimize total number of "Spark" (work) days

**Formula:**
```
workdays = count(action == "Spark" for action in schedule.actions)
```

**Rationale:** Prefer more rest days

**Example:**
```
Schedule A: 15 workdays
Schedule B: 12 workdays
→ Schedule B is better (all else equal)
```

### Priority 2: Minimize Back-to-Back Work

**Goal:** Minimize number of consecutive work day pairs

**Formula:**
```
b2b = count(actions[i] == "Spark" AND actions[i+1] == "Spark" for i in 0..28)
```

**Rationale:** Spread out work days for better rest distribution

**Example:**
```
Schedule A: [Spark, Spark, O, O, Spark, Spark, ...]
  → b2b = 2 (pair on days 1-2, pair on days 5-6)

Schedule B: [Spark, O, Spark, O, Spark, O, ...]
  → b2b = 0 (no consecutive work days)

→ Schedule B is better (if workdays are equal)
```

### Priority 3: Minimize Distance from Target

**Goal:** Get as close as possible to exact target_end balance

**Formula:**
```
abs_diff = |final_closing - target_end|
```

**Rationale:** Hitting target precisely is ideal

**Example:**
```
target_end = $500

Schedule A: final = $510 → abs_diff = $10
Schedule B: final = $502 → abs_diff = $2

→ Schedule B is better (if workdays and b2b are equal)
```

## Lexicographic Optimization

The solver optimizes objectives in **strict priority order**:

1. First, minimize workdays
2. Then, among all schedules with minimum workdays, minimize b2b
3. Then, among those with minimum workdays and b2b, minimize abs_diff

**Example:**
```
Schedule A: (12 workdays, 0 b2b, $10 diff)
Schedule B: (13 workdays, 0 b2b, $2 diff)

→ Schedule A wins (fewer workdays, even though larger diff)

Schedule C: (12 workdays, 1 b2b, $2 diff)
Schedule D: (12 workdays, 0 b2b, $10 diff)

→ Schedule D wins (same workdays, fewer b2b, even though larger diff)
```

## Constraint Relaxation Strategies

If no feasible solution exists, try these in order:

### 1. Increase Band Tolerance
```python
# Original
plan.band_cents = to_cents(25.0)

# Relaxed
plan.band_cents = to_cents(50.0)  # More flexibility
```

### 2. Reduce Rent Guard
```python
# Original
plan.rent_guard_cents = to_cents(1700.0)

# Relaxed
plan.rent_guard_cents = to_cents(1636.0)  # Just enough for rent
```

### 3. Remove Locked Actions
```python
# Original
plan.actions = ["Spark", "O", "O", None, ...]  # Some days locked

# Relaxed
plan.actions = [None] * 30  # Let solver decide all days
```

### 4. Adjust Target End
```python
# Original (too high)
plan.target_end_cents = to_cents(800.0)

# Relaxed
plan.target_end_cents = to_cents(500.0)  # More achievable
```

### 5. Add Deposits or Reduce Bills
```python
# Add income
plan.deposits.append(Deposit(day=15, amount_cents=to_cents(500.0)))

# Reduce expenses
plan.bills = [b for b in plan.bills if b.amount_cents < to_cents(200.0)]
```

## Validation

After solving, validate the schedule:

```python
from core import validate

report = validate(plan, schedule)

if not report.ok:
    print("Validation failed:")
    for name, ok, detail in report.checks:
        if not ok:
            print(f"  ✗ {name}: {detail}")
```

### Validation Checks

1. **Day 1 Spark:** Ensures first day is work day
2. **Non-negative balances:** Checks all 30 days have closing >= 0
3. **Final within band:** Checks final balance in [target-band, target+band]
4. **Day-30 pre-rent guard:** Checks pre-rent balance >= rent_guard

## Common Infeasibility Patterns

### Pattern 1: Bills Exceed Income Potential

**Symptom:** Solver always fails

**Diagnosis:**
```python
total_bills = sum(b.amount_cents for b in plan.bills)
total_deposits = sum(d.amount_cents for d in plan.deposits)
max_work_income = 30 * 10000  # 30 days * $100/day

if total_bills > plan.start_balance_cents + total_deposits + max_work_income:
    print("Impossible: Bills exceed all possible income")
```

**Fix:** Reduce bills or add deposits

### Pattern 2: Conflicting Constraints

**Symptom:** Solver fails even with high workdays

**Diagnosis:**
- target_end too high AND band too tight
- rent_guard too high for available cash flow
- Too many locked "O" days with high expenses

**Fix:** Relax one constraint at a time to find bottleneck

### Pattern 3: Early Large Bill

**Symptom:** Day 1-5 balance goes negative

**Diagnosis:** Not enough starting balance + early deposits for early bills

**Fix:**
- Increase start_balance
- Move early bills to later days
- Add early deposits

## See Also

- [plan_schema.md](./plan_schema.md) - JSON format specification
- [troubleshooting.md](./troubleshooting.md) - Debugging solver issues
- [dp_algorithm.md](./dp_algorithm.md) - How DP solver works
- [cpsat_algorithm.md](./cpsat_algorithm.md) - How CP-SAT solver works
