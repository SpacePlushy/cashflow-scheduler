# API Reference

Complete documentation for all functions and data classes in the cashflow-scheduler skill.

## Core Functions

### `solve(plan, solver="auto", **kwargs)`

Main solver entry point for full-month scheduling.

**Args:**
- `plan` (Plan): Problem definition
- `solver` (str): "auto", "dp", or "cpsat"
  - `"auto"`: Try CP-SAT first, fall back to DP if OR-Tools unavailable (recommended)
  - `"dp"`: Force dynamic programming solver (pure Python, always available)
  - `"cpsat"`: Force CP-SAT solver (requires OR-Tools, faster on complex problems)
- `**kwargs`: Solver-specific options (e.g., `options=CPSATSolveOptions(...)`)

**Returns:** Schedule object with optimal work schedule

**Raises:**
- `RuntimeError`: If no feasible solution exists
- `ImportError`: If solver="cpsat" but OR-Tools not installed

**Example:**
```python
from core import solve, Plan

# Auto-select solver (recommended)
schedule = solve(plan)

# Force DP only
schedule = solve(plan, solver="dp")

# Force CP-SAT with options
from core.cpsat_solver import CPSATSolveOptions
options = CPSATSolveOptions(max_time_seconds=30.0, num_search_workers=4)
schedule = solve(plan, solver="cpsat", options=options)
```

---

### `adjust_from_day(original_plan, current_day, current_eod_balance, solver="auto", **kwargs)`

**PRIMARY FUNCTION for mid-month adjustments.** Use when you know your actual balance on a specific day and need to re-optimize the remaining days.

**How it works:**
1. Solves baseline schedule for the full month
2. Locks days 1 through `current_day` to baseline schedule
3. Adds adjustment to match your actual balance on `current_day`
4. Re-solves days `current_day+1` through 30 optimally

**Args:**
- `original_plan` (Plan): The original full-month plan
- `current_day` (int): Current day number (1-30)
- `current_eod_balance` (float): Your actual end-of-day balance in dollars
- `solver` (str): "auto", "dp", or "cpsat" (default: "auto")
- `**kwargs`: Solver-specific options

**Returns:** Schedule object with:
- Days 1 through `current_day`: Locked to baseline schedule
- Days `current_day+1` through 30: Re-optimized based on actual balance

**Raises:**
- `ValueError`: If `current_day` not in range 1-30
- `RuntimeError`: If no feasible schedule exists for remaining days

**Example:**
```python
from core import adjust_from_day

# You're on day 20 with $230 actual balance
new_schedule = adjust_from_day(
    original_plan=plan,
    current_day=20,
    current_eod_balance=230.00
)

# See what to do for days 21-30
print(f"Days 21-30: {' '.join(new_schedule.actions[20:])}")
work_days_remaining = [i+1 for i, a in enumerate(new_schedule.actions[20:], start=20)
                       if a == 'Spark']
print(f"Work on days: {work_days_remaining}")
```

---

### `validate(plan, schedule)`

Validate a schedule against all hard constraints.

**Args:**
- `plan` (Plan): Problem definition
- `schedule` (Schedule): Solution to validate

**Returns:** `ValidationReport` object with:
- `ok` (bool): True if all checks pass
- `checks` (List[Tuple[str, bool, str]]): List of (check_name, passed, detail_message)

**Validation Checks:**
1. Day 1 is "Spark" (work day)
2. All daily closing balances ≥ 0
3. Final balance within [target - band, target + band]
4. Day 30 pre-rent balance ≥ rent_guard

**Example:**
```python
from core import validate

report = validate(plan, schedule)

if report.ok:
    print("✅ Schedule is valid")
else:
    print("❌ Validation failed:")
    for name, ok, detail in report.checks:
        if not ok:
            print(f"  ✗ {name}: {detail}")
```

---

### `to_cents(amount)`

Convert dollars to integer cents for internal representation.

**Args:**
- `amount` (float | int | str | Decimal): Dollar amount

**Returns:** `int` - Amount in cents

**Example:**
```python
from core import to_cents

cents = to_cents(123.45)  # 12345
cents = to_cents("99.99")  # 9999
cents = to_cents(100)      # 10000
```

---

### `cents_to_str(cents)`

Convert integer cents to dollar string for display.

**Args:**
- `cents` (int): Amount in cents

**Returns:** `str` - Dollar amount as string (e.g., "123.45")

**Example:**
```python
from core import cents_to_str

dollars = cents_to_str(12345)  # "123.45"
dollars = cents_to_str(9999)   # "99.99"
dollars = cents_to_str(10000)  # "100.00"
```

---

## Data Classes

### `Plan`

Problem definition for schedule optimization.

**Fields:**
- `start_balance_cents` (int): Starting cash on Day 1 (before any transactions)
- `target_end_cents` (int): Desired ending balance on Day 30
- `band_cents` (int): Tolerance around target (final must be in [target-band, target+band])
- `rent_guard_cents` (int): Minimum balance required before paying rent on Day 30
- `deposits` (List[Deposit]): Scheduled cash inflows (paychecks, deposits)
- `bills` (List[Bill]): Scheduled cash outflows (rent, utilities, etc.)
- `actions` (List[Optional[str]]): 30-element list
  - `None`: Let solver decide
  - `"O"`: Lock as off day
  - `"Spark"`: Lock as work day ($100 income)
- `manual_adjustments` (List[Adjustment]): One-time corrections (refunds, found money)
- `locks` (List[Tuple[int, int]]): Legacy locking mechanism (prefer `actions`)
- `metadata` (Dict[str, Any]): Optional metadata for tracking

**Example:**
```python
from core import Plan, Bill, Deposit, to_cents

plan = Plan(
    start_balance_cents=to_cents(100.00),
    target_end_cents=to_cents(500.00),
    band_cents=to_cents(25.0),
    rent_guard_cents=to_cents(1600.0),
    deposits=[
        Deposit(day=11, amount_cents=to_cents(1021.0)),
        Deposit(day=25, amount_cents=to_cents(1021.0))
    ],
    bills=[
        Bill(day=1, name="Insurance", amount_cents=to_cents(177.0)),
        Bill(day=30, name="Rent", amount_cents=to_cents(1636.0))
    ],
    actions=[None] * 30,  # Let solver decide all days
    manual_adjustments=[],
    locks=[],
    metadata={"created": "2024-01-15"}
)
```

---

### `Schedule`

Solution returned by solver.

**Fields:**
- `actions` (List[str]): 30-element list of "O" (off) or "Spark" (work)
- `objective` (Tuple[int, int, int]):
  - `[0]`: Total workdays
  - `[1]`: Back-to-back work pairs
  - `[2]`: Absolute difference from target (in cents)
- `final_closing_cents` (int): Final balance on Day 30 (after all transactions)
- `ledger` (List[LedgerEntry]): Daily ledger entries with opening/closing balances

**Example:**
```python
schedule = solve(plan)

# Access results
workdays = schedule.objective[0]
b2b_pairs = schedule.objective[1]
target_diff = schedule.objective[2]

# Show schedule
print(f"Schedule: {' '.join(schedule.actions)}")
print(f"Work on days: {[i+1 for i, a in enumerate(schedule.actions) if a == 'Spark']}")

# Show ledger
for entry in schedule.ledger:
    print(f"Day {entry.day}: {entry.action} | "
          f"Opening: ${cents_to_str(entry.opening_cents)} | "
          f"Closing: ${cents_to_str(entry.closing_cents)}")
```

---

### `Bill`

Scheduled cash outflow.

**Fields:**
- `day` (int): Day number (1-30) when bill is due
- `name` (str): Description of bill
- `amount_cents` (int): Bill amount in cents

**Example:**
```python
from core import Bill, to_cents

bill = Bill(
    day=15,
    name="Internet",
    amount_cents=to_cents(79.99)
)
```

---

### `Deposit`

Scheduled cash inflow.

**Fields:**
- `day` (int): Day number (1-30) when deposit arrives
- `amount_cents` (int): Deposit amount in cents

**Example:**
```python
from core import Deposit, to_cents

deposit = Deposit(
    day=10,
    amount_cents=to_cents(1021.00)
)
```

---

### `Adjustment`

One-time balance correction (for manual adjustments).

**Fields:**
- `day` (int): Day number (1-30) when adjustment occurs
- `amount_cents` (int): Adjustment amount in cents (negative for expenses)
- `note` (str): Description of adjustment

**Example:**
```python
from core import Adjustment, to_cents

# One-time expense
car_repair = Adjustment(
    day=15,
    amount_cents=to_cents(-250.00),
    note="Car repair"
)

# One-time income
refund = Adjustment(
    day=20,
    amount_cents=to_cents(50.00),
    note="Venmo refund"
)

# Add to plan
plan.manual_adjustments = [car_repair, refund]
```

---

### `LedgerEntry`

Single day's ledger entry in schedule.

**Fields:**
- `day` (int): Day number (1-30)
- `action` (str): "O" (off) or "Spark" (work)
- `opening_cents` (int): Balance at start of day
- `closing_cents` (int): Balance at end of day (after all transactions)

**Note:** Automatically generated by solver, not created manually.

**Example:**
```python
schedule = solve(plan)

# Access ledger
for entry in schedule.ledger:
    print(f"Day {entry.day:2d}: {entry.action:5s} | "
          f"Open: ${cents_to_str(entry.opening_cents):>8s} | "
          f"Close: ${cents_to_str(entry.closing_cents):>8s}")
```

---

### `ValidationReport`

Result of schedule validation.

**Fields:**
- `ok` (bool): True if all checks passed
- `checks` (List[Tuple[str, bool, str]]): List of (check_name, passed, detail)

**Note:** Automatically generated by `validate()`, not created manually.

**Example:**
```python
report = validate(plan, schedule)

if not report.ok:
    for name, ok, detail in report.checks:
        if not ok:
            print(f"Failed: {name} - {detail}")
```

---

## Loading from JSON

### `load_plan(path: Path) -> Plan`

Helper function to load a plan from JSON file.

**Args:**
- `path` (Path): Path to JSON file

**Returns:** Plan object

**JSON Format:**
```json
{
  "start_balance": 100.00,
  "target_end": 500.00,
  "band": 25.00,
  "rent_guard": 1600.00,
  "deposits": [
    {"day": 11, "amount": 1021.00},
    {"day": 25, "amount": 1021.00}
  ],
  "bills": [
    {"day": 1, "name": "Insurance", "amount": 177.00},
    {"day": 30, "name": "Rent", "amount": 1636.00}
  ],
  "actions": [null, null, ...],
  "metadata": {}
}
```

**Example:**
```python
import json
from pathlib import Path
from core import Plan, Bill, Deposit, to_cents

def load_plan(path: Path) -> Plan:
    with open(path) as f:
        data = json.load(f)

    return Plan(
        start_balance_cents=to_cents(data['start_balance']),
        target_end_cents=to_cents(data['target_end']),
        band_cents=to_cents(data['band']),
        rent_guard_cents=to_cents(data['rent_guard']),
        deposits=[Deposit(day=d['day'], amount_cents=to_cents(d['amount']))
                  for d in data['deposits']],
        bills=[Bill(day=b['day'], name=b['name'],
                    amount_cents=to_cents(b['amount']))
               for b in data['bills']],
        actions=data.get('actions', [None] * 30),
        manual_adjustments=[],
        locks=[],
        metadata=data.get('metadata', {})
    )

# Usage
plan = load_plan(Path('plan.json'))
schedule = solve(plan)
```

See `examples/solve_from_json.py` for a complete working example.

---

## See Also

- [Advanced Usage](advanced.md) - CP-SAT options, locking patterns, iterative workflows
- [JSON Schema](plan_schema.md) - Complete JSON format documentation
- [Constraints](constraints.md) - Constraint system deep dive
- [Troubleshooting](troubleshooting.md) - Common issues and solutions
