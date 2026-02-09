# Cashflow Scheduler - CP-SAT Solver (Minimal Package)

This minimal package contains only the files needed to run the CP-SAT constraint programming solver for optimizing 30-day work schedules.

## Quick Start (3 Steps)

### Step 1: Extract the Zip File

```bash
# Extract to a directory of your choice
unzip cashflow-cpsat-minimal.zip
cd cashflow-cpsat-minimal/
```

### Step 2: Install Dependencies

You need Python 3.9+ and OR-Tools. Install OR-Tools:

```bash
pip install ortools
# or if using pip3
pip3 install ortools
```

**Note:** OR-Tools 9.8+ required (9.10+ recommended). If installation fails on your platform, this solver won't work - you'll need the full package with the DP solver instead.

### Step 3: Test It Works

Create a test file `test.py`:

```python
from cashflow.core.model import Plan, Deposit, Bill, to_cents
from cashflow.engines.cpsat import solve_with_diagnostics

# Create a simple plan
plan = Plan(
    start_balance_cents=to_cents(90.50),
    target_end_cents=to_cents(490.50),
    band_cents=to_cents(25.0),
    rent_guard_cents=to_cents(1636.0),
    deposits=[Deposit(day=11, amount_cents=to_cents(1021.0))],
    bills=[
        Bill(day=1, name="Auto Insurance", amount_cents=to_cents(177.0)),
        Bill(day=30, name="Rent", amount_cents=to_cents(1636.0)),
    ],
    actions=[None] * 30,
    manual_adjustments=[],
    locks=[],
    metadata={}
)

# Solve it
result = solve_with_diagnostics(plan)
schedule = result.schedule

print(f"✓ Solver: {result.solver}")
print(f"✓ Actions: {' '.join(schedule.actions)}")
print(f"✓ Workdays: {schedule.objective[0]}")
print(f"✓ Final balance: ${schedule.final_closing_cents / 100:.2f}")
```

Run it:

```bash
python3 test.py
```

You should see output like:
```
✓ Solver: cpsat
✓ Actions: Spark O Spark O Spark O O O Spark...
✓ Workdays: 12
✓ Final balance: $498.50
```

## What's Included

- `cashflow/core/model.py` - Data structures (Plan, Schedule, Bill, Deposit)
- `cashflow/core/ledger.py` - Builds daily ledger from actions
- `cashflow/engines/cpsat.py` - CP-SAT constraint programming solver
- `plan.json` - Example plan you can load
- `CPSAT-README.md` - This file

## Detailed Usage

### Loading from JSON

If you have a `plan.json` file:

```python
import json
from cashflow.core.model import Plan, Deposit, Bill, Adjustment, to_cents
from cashflow.engines.cpsat import solve_with_diagnostics

# Load from JSON
with open('plan.json', 'r') as f:
    data = json.load(f)

plan = Plan(
    start_balance_cents=to_cents(data['start_balance']),
    target_end_cents=to_cents(data['target_end']),
    band_cents=to_cents(data['band']),
    rent_guard_cents=to_cents(data['rent_guard']),
    deposits=[Deposit(day=d['day'], amount_cents=to_cents(d['amount']))
              for d in data.get('deposits', [])],
    bills=[Bill(day=b['day'], name=b['name'], amount_cents=to_cents(b['amount']))
           for b in data.get('bills', [])],
    actions=data.get('actions', [None] * 30),
    manual_adjustments=[Adjustment(day=a['day'], amount_cents=to_cents(a['amount']), note=a.get('note', ''))
                       for a in data.get('manual_adjustments', [])],
    locks=data.get('locks', []),
    metadata=data.get('metadata', {})
)

# Solve
result = solve_with_diagnostics(plan)
schedule = result.schedule

print(f"Workdays needed: {schedule.objective[0]}")
print(f"Schedule: {' '.join(schedule.actions)}")
```

### Viewing Daily Details

```python
# View full daily ledger
for day in schedule.ledger:
    print(f"Day {day.day:2d}: Open ${day.opening_cents/100:7.2f} | "
          f"{day.action:5s} +${day.net_cents/100:6.2f} | "
          f"Bills -${day.bills_cents/100:6.2f} | "
          f"Close ${day.closing_cents/100:7.2f}")
```

### Understanding the Plan Parameters

- **start_balance_cents**: How much money you start with (in cents)
- **target_end_cents**: Goal balance at end of 30 days (in cents)
- **band_cents**: Acceptable deviation from target (± this amount)
- **rent_guard_cents**: Minimum balance needed before paying Day 30 rent
- **deposits**: Money coming in on specific days
- **bills**: Money going out on specific days
- **actions**: Pre-locked work days (use `None` for unsolved days)
- **manual_adjustments**: One-time cash corrections on specific days

## Key Functions

**From `cashflow.engines.cpsat`:**
- `solve_with_diagnostics(plan)` - Main entry point, returns `CPSATSolveResult`
  - Result includes: `schedule`, `solver` (name), `statuses`, `solve_seconds`
- `solve(plan)` - Direct solve, returns `Schedule` object
- `verify_schedule(plan, schedule)` - Check if a schedule is optimal

**From `cashflow.core.model`:**
- `to_cents(amount)` - Convert dollars to cents (e.g., `to_cents(100.50)` → `10050`)
- `cents_to_str(cents)` - Convert cents to dollar string (e.g., `cents_to_str(10050)` → `"100.50"`)

## Troubleshooting

### Import Error: "No module named 'ortools'"

**Solution:** Install OR-Tools:
```bash
pip3 install ortools
```

If that fails, OR-Tools may not be available for your platform. You'll need the full package with the DP solver.

### Import Error: "No module named 'cashflow'"

**Solution:** Make sure you're running Python from the directory where you extracted the zip. The `cashflow/` folder should be in the same directory as your script.

```bash
ls -la
# Should show:
# cashflow/
# plan.json
# CPSAT-README.md
# test.py (your script)
```

### "No feasible schedule found"

This means the constraints are too tight. Try:
- Increasing `band_cents` (allow more deviation from target)
- Lowering `rent_guard_cents` (less strict rent requirement)
- Adjusting your target end balance
- Adding more deposits or reducing bills

### Solver is Very Slow

CP-SAT should solve most problems in under 1 second. If it's taking longer:
- Your problem may be heavily constrained
- Try using the DP solver instead (included in full package)

## System Requirements

- **Python:** 3.9 or higher
- **OR-Tools:** 9.8+ (9.10+ recommended)
- **Platforms:** Linux, macOS (Intel/ARM), Windows
- **Note:** Older macOS ARM64 systems may need OR-Tools 9.10+

## What This Solver Does

The CP-SAT solver finds the optimal 30-day work schedule that:
1. ✓ Minimizes workdays
2. ✓ Minimizes back-to-back work pairs
3. ✓ Gets closest to target end balance
4. ✓ Never goes negative on any day
5. ✓ Maintains required rent guard on Day 30
6. ✓ Enforces "Off-Off Window" rule (at least one consecutive off-off pair in every 7-day window)

**Actions:**
- `"Spark"` = Work day (+$100)
- `"O"` = Off day ($0)
