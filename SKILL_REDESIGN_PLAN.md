# Cashflow Scheduler Skill - Redesign Plan

## Based on Official Claude Skills Documentation

### Current Problem
- ❌ Phase A skill documents a CLI tool (`./cash`) that users must install separately
- ❌ Skill doesn't work unless `./cash` is available on the system
- ❌ Not following the recommended pattern from Anthropic's official skills

### Official Recommended Pattern

From `anthropics/skills` repository and official docs:

**✅ Bundle the actual Python code in the skill**

Example: `slack-gif-creator` includes `core/` modules that Claude imports directly:

```python
from core.gif_builder import GIFBuilder
builder = GIFBuilder(width=128, height=128)
```

**Key insight:** Skills can contain Python modules that Claude executes directly - no external tools needed!

---

## New Architecture

### Directory Structure

```
cashflow-scheduler/
├── SKILL.md                          # Instructions with import examples
├── core/                             # Bundled solver code
│   ├── __init__.py
│   ├── model.py                     # Plan, Schedule, Bill, Deposit classes
│   ├── solver.py                    # DP solver algorithm
│   ├── ledger.py                    # Daily balance calculations
│   └── validate.py                  # Constraint validation
├── examples/                         # Quick-start examples
│   ├── solve_basic.py               # Basic solve example
│   ├── solve_with_adjustments.py   # Advanced example
│   └── analyze_feasibility.py      # Pre-check example
├── references/                       # Detailed documentation
│   ├── plan_schema.md
│   ├── troubleshooting.md
│   ├── solver_algorithm.md          # NEW - DP algorithm explanation
│   └── constraints.md
├── assets/
│   └── example_plans/
│       ├── simple_plan.json
│       ├── complex_plan.json
│       ├── tight_budget.json
│       └── comfortable.json
└── requirements.txt                  # Empty (no external deps for DP)
```

### What Gets Bundled

From existing `cashflow/` package, copy only what's needed:

#### core/model.py
```python
"""Data models for plans and schedules."""
from dataclasses import dataclass
from typing import List, Optional, Tuple

@dataclass
class Bill:
    day: int
    name: str
    amount_cents: int

@dataclass
class Deposit:
    day: int
    amount_cents: int

@dataclass
class Adjustment:
    day: int
    amount_cents: int
    note: str = ""

@dataclass
class Plan:
    start_balance_cents: int
    target_end_cents: int
    band_cents: int
    rent_guard_cents: int
    bills: List[Bill]
    deposits: List[Deposit]
    actions: List[Optional[str]]  # 30 elements
    manual_adjustments: List[Adjustment]

@dataclass
class Schedule:
    actions: List[str]  # 30 elements
    objective: Tuple[int, int, int]  # (workdays, b2b, abs_diff)
    ledger: List[dict]  # Daily balance info

def to_cents(dollars: float) -> int:
    """Convert dollars to cents."""
    return int(round(dollars * 100))

def cents_to_str(cents: int) -> str:
    """Convert cents to dollar string."""
    return f"{cents / 100:.2f}"
```

#### core/solver.py
```python
"""DP solver for cashflow optimization."""
from typing import Optional, Dict, Tuple, List
from .model import Plan, Schedule

def solve(plan: Plan) -> Optional[Schedule]:
    """
    Solve a cashflow plan using dynamic programming.

    Returns:
        Schedule if feasible, None if infeasible
    """
    # Full DP implementation from cashflow/engines/dp.py
    # (Self-contained, no external dependencies)
    pass
```

#### core/ledger.py
```python
"""Daily ledger calculations."""
from .model import Plan, Schedule

def build_ledger(plan: Plan, schedule: Schedule) -> List[dict]:
    """
    Build daily ledger showing opening/closing balances.

    Returns:
        List of dicts with keys: day, opening, deposits, action_net, bills, closing
    """
    pass
```

#### core/validate.py
```python
"""Constraint validation."""
from .model import Plan, Schedule

def validate(plan: Plan, schedule: Schedule) -> dict:
    """
    Validate schedule against all constraints.

    Returns:
        Dict with keys: ok (bool), checks (list of check results)
    """
    pass
```

---

## New SKILL.md Structure

### Quick Start Example

```markdown
## Quick Start

To create an optimized work schedule:

```python
from core.model import Plan, Bill, Deposit, to_cents
from core.solver import solve
from core.ledger import build_ledger
from core.validate import validate

# Create a plan
plan = Plan(
    start_balance_cents=to_cents(100.00),
    target_end_cents=to_cents(200.00),
    band_cents=to_cents(50.0),
    rent_guard_cents=to_cents(800.0),
    deposits=[
        Deposit(day=15, amount_cents=to_cents(500.0))
    ],
    bills=[
        Bill(day=5, name="Phone", amount_cents=to_cents(75.0)),
        Bill(day=30, name="Rent", amount_cents=to_cents(800.0))
    ],
    actions=[None] * 30,  # Let solver decide
    manual_adjustments=[]
)

# Solve
schedule = solve(plan)

if schedule:
    print(f"Objective: workdays={schedule.objective[0]}, "
          f"b2b={schedule.objective[1]}, "
          f"abs_diff={schedule.objective[2]}")

    # Validate
    report = validate(plan, schedule)
    print(f"Valid: {report['ok']}")

    # Get ledger
    ledger = build_ledger(plan, schedule)
    for entry in ledger:
        print(f"Day {entry['day']}: {entry['action']} -> ${entry['closing']/100:.2f}")
else:
    print("No feasible schedule found")
```
```

### Loading Plans from JSON

```python
import json
from core.model import Plan, Bill, Deposit, Adjustment, to_cents

# Load from JSON file
with open('plan.json') as f:
    data = json.load(f)

plan = Plan(
    start_balance_cents=to_cents(data['start_balance']),
    target_end_cents=to_cents(data['target_end']),
    band_cents=to_cents(data['band']),
    rent_guard_cents=to_cents(data['rent_guard']),
    bills=[Bill(day=b['day'], name=b['name'],
                amount_cents=to_cents(b['amount']))
           for b in data['bills']],
    deposits=[Deposit(day=d['day'],
                      amount_cents=to_cents(d['amount']))
              for d in data['deposits']],
    actions=data.get('actions', [None] * 30),
    manual_adjustments=[Adjustment(day=a['day'],
                                   amount_cents=to_cents(a['amount']),
                                   note=a.get('note', ''))
                       for a in data.get('manual_adjustments', [])]
)

schedule = solve(plan)
```

---

## Implementation Steps

### Step 1: Extract Core Modules
```bash
# Copy from existing cashflow package
cp cashflow/core/model.py cashflow-scheduler/core/
cp cashflow/engines/dp.py cashflow-scheduler/core/solver.py
cp cashflow/core/ledger.py cashflow-scheduler/core/
cp cashflow/core/validate.py cashflow-scheduler/core/
```

### Step 2: Simplify for Skill Bundle
- Remove CLI-specific code
- Remove OR-Tools dependency (DP only)
- Make fully self-contained
- Add `__init__.py` to make importable package

### Step 3: Create Example Scripts

**examples/solve_basic.py:**
```python
#!/usr/bin/env python3
"""Basic example: Create and solve a simple plan."""

from core.model import Plan, Bill, Deposit, to_cents, cents_to_str
from core.solver import solve

# Create plan
plan = Plan(
    start_balance_cents=to_cents(100.00),
    target_end_cents=to_cents(200.00),
    band_cents=to_cents(50.0),
    rent_guard_cents=to_cents(800.0),
    deposits=[Deposit(day=15, amount_cents=to_cents(500.0))],
    bills=[
        Bill(day=5, name="Phone", amount_cents=to_cents(75.0)),
        Bill(day=30, name="Rent", amount_cents=to_cents(800.0))
    ],
    actions=[None] * 30,
    manual_adjustments=[]
)

# Solve
schedule = solve(plan)

if schedule:
    w, b2b, delta = schedule.objective
    print(f"✅ Solution found!")
    print(f"Objective: workdays={w}, b2b={b2b}, |Δ|={cents_to_str(delta)}")
    print(f"\nSchedule: {' '.join(schedule.actions)}")
else:
    print("❌ No feasible schedule")
```

**examples/load_and_solve.py:**
```python
#!/usr/bin/env python3
"""Load a plan.json file and solve it."""

import sys
import json
from pathlib import Path
from core.model import Plan, Bill, Deposit, Adjustment, to_cents, cents_to_str
from core.solver import solve
from core.validate import validate

if len(sys.argv) < 2:
    print("Usage: python examples/load_and_solve.py <plan.json>")
    sys.exit(1)

# Load plan from JSON
plan_path = Path(sys.argv[1])
with open(plan_path) as f:
    data = json.load(f)

# Convert to Plan object
plan = Plan(
    start_balance_cents=to_cents(data['start_balance']),
    target_end_cents=to_cents(data['target_end']),
    band_cents=to_cents(data['band']),
    rent_guard_cents=to_cents(data['rent_guard']),
    bills=[Bill(day=b['day'], name=b['name'], amount_cents=to_cents(b['amount']))
           for b in data['bills']],
    deposits=[Deposit(day=d['day'], amount_cents=to_cents(d['amount']))
              for d in data['deposits']],
    actions=data.get('actions', [None] * 30),
    manual_adjustments=[Adjustment(day=a['day'], amount_cents=to_cents(a['amount']),
                                   note=a.get('note', ''))
                       for a in data.get('manual_adjustments', [])]
)

# Solve
print(f"Solving {plan_path}...")
schedule = solve(plan)

if schedule:
    w, b2b, delta = schedule.objective
    print(f"\n✅ Solution found!")
    print(f"Objective: workdays={w}, b2b={b2b}, |Δ|={cents_to_str(delta)}")

    # Validate
    report = validate(plan, schedule)
    print(f"\nValidation: {'PASS' if report['ok'] else 'FAIL'}")
    for check in report['checks']:
        status = '✓' if check['ok'] else '✗'
        print(f"  {status} {check['name']}")
else:
    print("\n❌ No feasible schedule (INFEASIBLE)")
```

### Step 4: Update SKILL.md

**New structure:**
1. **Overview** - What the skill does
2. **Quick Start** - Simple import example
3. **Loading Plans from JSON** - File-based workflow
4. **Core Modules** - What's available in `core/`
5. **Example Scripts** - Point to `examples/` directory
6. **Troubleshooting** - Reference to references/
7. **Constraint System** - Brief overview

### Step 5: Test

```python
# Test that imports work
from core.model import Plan
from core.solver import solve

# Test with example plan
import json
with open('assets/example_plans/simple_plan.json') as f:
    # ... load and solve
```

---

## Advantages of This Approach

✅ **Self-contained** - No external CLI dependency
✅ **Follows official pattern** - Matches slack-gif-creator approach
✅ **Works everywhere** - Pure Python, no installation needed
✅ **Easy to debug** - Claude can read the bundled source
✅ **Progressive disclosure** - Core code + examples + references
✅ **Future-proof** - Easy to extend with more features

---

## Migration from Phase A

**What stays the same:**
- ✅ references/ docs (no changes needed)
- ✅ assets/example_plans/ (no changes needed)
- ✅ Overall skill structure

**What changes:**
- ❌ Remove CLI tool dependency
- ✅ Add core/ Python modules
- ✅ Add examples/ directory
- ✅ Rewrite SKILL.md to show imports instead of CLI commands

---

## Timeline

**Estimated effort:** 3-4 hours

1. **Copy and adapt code** (1 hour)
   - Extract from cashflow package
   - Make self-contained
   - Add __init__.py

2. **Create examples** (1 hour)
   - solve_basic.py
   - load_and_solve.py
   - analyze_feasibility.py

3. **Rewrite SKILL.md** (1 hour)
   - Import-based examples
   - Point to core modules
   - Update workflows

4. **Test and validate** (1 hour)
   - Test all examples
   - Validate with package_skill.py
   - Test with actual example plans

---

## Next Steps

1. Should I proceed with this redesign?
2. Any specific requirements or constraints?
3. Do you want to keep the CLI tool as an optional addition, or go fully Python-only?

This approach will make the skill **actually work** when Claude loads it, instead of just documenting an external tool.
