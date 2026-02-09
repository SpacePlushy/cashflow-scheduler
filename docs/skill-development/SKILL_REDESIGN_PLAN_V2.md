# Cashflow Scheduler Skill - Redesign Plan V2 (WITH CP-SAT)

## Based on Official Claude Skills Documentation + User Request

### Key Change: Include BOTH Solvers

✅ **DP Solver** - Pure Python, no dependencies (always available)
✅ **CP-SAT Solver** - Uses OR-Tools, with automatic fallback to DP if not available

---

## New Architecture

### Directory Structure

```
cashflow-scheduler/
├── SKILL.md                          # Instructions with import examples
├── core/                             # Bundled solver code
│   ├── __init__.py
│   ├── model.py                     # Plan, Schedule, Bill, Deposit classes
│   ├── dp_solver.py                 # DP algorithm (no dependencies)
│   ├── cpsat_solver.py              # CP-SAT algorithm (optional OR-Tools)
│   ├── ledger.py                    # Daily balance calculations
│   └── validate.py                  # Constraint validation
├── examples/                         # Quick-start examples
│   ├── solve_basic_dp.py            # Basic DP example
│   ├── solve_basic_cpsat.py         # Basic CP-SAT example
│   ├── solve_with_fallback.py      # Automatic fallback
│   ├── compare_solvers.py           # Run both and compare
│   └── load_and_solve.py            # Load from JSON
├── references/                       # Detailed documentation
│   ├── plan_schema.md
│   ├── troubleshooting.md
│   ├── dp_algorithm.md              # DP solver explanation
│   ├── cpsat_algorithm.md           # CP-SAT solver explanation
│   └── constraints.md
├── assets/
│   └── example_plans/
│       ├── simple_plan.json
│       ├── complex_plan.json
│       ├── tight_budget.json
│       └── comfortable.json
└── requirements.txt                  # ortools (optional)
```

---

## Core Modules Design

### core/model.py

```python
"""Data models and utilities for cashflow scheduling."""

from dataclasses import dataclass
from typing import List, Optional, Tuple

# Shift types and their net income
SHIFT_NET_CENTS = {
    "O": 0,           # Off day
    "Spark": 10_000,  # Work day ($100)
}

@dataclass
class Bill:
    day: int          # 1-30
    name: str
    amount_cents: int

@dataclass
class Deposit:
    day: int          # 1-30
    amount_cents: int

@dataclass
class Adjustment:
    day: int          # 1-30
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
    actions: List[Optional[str]]  # 30 elements, None = solver decides
    manual_adjustments: List[Adjustment]

@dataclass
class Schedule:
    actions: List[str]                    # 30 elements
    objective: Tuple[int, int, int]       # (workdays, b2b, abs_diff)
    ledger: List[dict]                    # Daily balance info
    solver_used: str = "DP"               # "DP" or "CPSAT"

# Utility functions
def to_cents(dollars: float) -> int:
    """Convert dollars to cents."""
    return int(round(dollars * 100))

def cents_to_str(cents: int) -> str:
    """Convert cents to dollar string."""
    return f"{cents / 100:.2f}"
```

### core/dp_solver.py

```python
"""Dynamic Programming solver - no external dependencies."""

from typing import Optional
from .model import Plan, Schedule

def solve_dp(plan: Plan) -> Optional[Schedule]:
    """
    Solve using dynamic programming.

    Algorithm:
    - State space: (day, balance, workdays, b2b, prev_worked)
    - Pruning: Keep only Pareto-optimal states
    - Objective: Lexicographic (workdays, b2b, abs_diff)

    Returns:
        Schedule if feasible, None if infeasible
    """
    # Full DP implementation from cashflow/engines/dp.py
    # Self-contained, no external dependencies
    pass
```

### core/cpsat_solver.py

```python
"""CP-SAT solver - requires OR-Tools (with fallback to DP)."""

from typing import Optional
from .model import Plan, Schedule

try:
    from ortools.sat.python import cp_model
    ORTOOLS_AVAILABLE = True
except ImportError:
    cp_model = None
    ORTOOLS_AVAILABLE = False

def solve_cpsat(plan: Plan, dp_fallback: bool = True) -> Optional[Schedule]:
    """
    Solve using CP-SAT constraint programming.

    Args:
        plan: Financial plan to solve
        dp_fallback: If True, fall back to DP if OR-Tools not available

    Returns:
        Schedule if feasible, None if infeasible

    Raises:
        ImportError: If OR-Tools not available and dp_fallback=False
    """
    if not ORTOOLS_AVAILABLE:
        if dp_fallback:
            from .dp_solver import solve_dp
            print("⚠️  OR-Tools not available, using DP solver fallback")
            return solve_dp(plan)
        else:
            raise ImportError(
                "OR-Tools not installed. Install with: pip install ortools"
            )

    # Full CP-SAT implementation from cashflow/engines/cpsat.py
    # Uses OR-Tools constraint programming
    pass

def is_ortools_available() -> bool:
    """Check if OR-Tools is available."""
    return ORTOOLS_AVAILABLE
```

### core/__init__.py

```python
"""Cashflow scheduler core modules."""

from .model import (
    Plan,
    Schedule,
    Bill,
    Deposit,
    Adjustment,
    SHIFT_NET_CENTS,
    to_cents,
    cents_to_str,
)
from .dp_solver import solve_dp
from .cpsat_solver import solve_cpsat, is_ortools_available
from .ledger import build_ledger
from .validate import validate

# Convenience function
def solve(plan: Plan, solver: str = "auto") -> Optional[Schedule]:
    """
    Solve a plan using the specified solver.

    Args:
        plan: Financial plan
        solver: "dp", "cpsat", or "auto" (tries CP-SAT, falls back to DP)

    Returns:
        Schedule if feasible, None if infeasible
    """
    if solver == "dp":
        return solve_dp(plan)
    elif solver == "cpsat":
        return solve_cpsat(plan, dp_fallback=False)
    elif solver == "auto":
        return solve_cpsat(plan, dp_fallback=True)
    else:
        raise ValueError(f"Unknown solver: {solver}. Use 'dp', 'cpsat', or 'auto'")

__all__ = [
    "Plan",
    "Schedule",
    "Bill",
    "Deposit",
    "Adjustment",
    "SHIFT_NET_CENTS",
    "to_cents",
    "cents_to_str",
    "solve",
    "solve_dp",
    "solve_cpsat",
    "is_ortools_available",
    "build_ledger",
    "validate",
]
```

---

## Updated SKILL.md Structure

### Quick Start - Auto Solver Selection

```markdown
## Quick Start

The skill includes **two solvers** that find optimal work schedules:

1. **DP (Dynamic Programming)** - Pure Python, no dependencies
2. **CP-SAT (Constraint Programming)** - Uses OR-Tools for verification

The `solve()` function **automatically chooses the best available solver**:

```python
from core import Plan, Bill, Deposit, to_cents, solve

# Create a plan
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
    actions=[None] * 30,  # Let solver decide all days
    manual_adjustments=[]
)

# Solve (tries CP-SAT, falls back to DP if OR-Tools not available)
schedule = solve(plan)

if schedule:
    w, b2b, delta = schedule.objective
    print(f"✅ Solution found using {schedule.solver_used}")
    print(f"Objective: workdays={w}, b2b={b2b}, |Δ|={delta/100:.2f}")
    print(f"Schedule: {' '.join(schedule.actions)}")
else:
    print("❌ No feasible schedule")
```
```

### Explicit Solver Selection

```markdown
## Choosing a Solver

### Use DP Solver (Always Available)

```python
from core import solve_dp

schedule = solve_dp(plan)
# Pure Python, fast (10-100ms), no dependencies
```

**When to use DP:**
- Production environments
- When OR-Tools not installed
- Fast iteration during development
- Resource-constrained systems

### Use CP-SAT Solver (Requires OR-Tools)

```python
from core import solve_cpsat, is_ortools_available

if is_ortools_available():
    schedule = solve_cpsat(plan, dp_fallback=False)
    # OR-Tools constraint programming
else:
    print("Install OR-Tools: pip install ortools")
```

**When to use CP-SAT:**
- Verification of DP results
- Detailed diagnostics
- Finding alternative optimal solutions
- When OR-Tools is already installed

### Compare Both Solvers

```python
from core import solve_dp, solve_cpsat, is_ortools_available

# Solve with DP
dp_schedule = solve_dp(plan)

# Solve with CP-SAT (if available)
if is_ortools_available():
    cpsat_schedule = solve_cpsat(plan, dp_fallback=False)

    # Should have same objective
    assert dp_schedule.objective == cpsat_schedule.objective
    print("✅ Both solvers agree!")
else:
    print("⚠️  CP-SAT not available (OR-Tools not installed)")
```
```

---

## Example Scripts

### examples/solve_basic_dp.py

```python
#!/usr/bin/env python3
"""Basic example using DP solver."""

from core import Plan, Bill, Deposit, to_cents, cents_to_str, solve_dp

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

print("Solving with DP solver...")
schedule = solve_dp(plan)

if schedule:
    w, b2b, delta = schedule.objective
    print(f"\n✅ Solution found!")
    print(f"Objective: workdays={w}, b2b={b2b}, |Δ|={cents_to_str(delta)}")
    print(f"\nSchedule:")
    for i, action in enumerate(schedule.actions, 1):
        print(f"Day {i:2d}: {action}")
else:
    print("\n❌ No feasible schedule (INFEASIBLE)")
```

### examples/solve_basic_cpsat.py

```python
#!/usr/bin/env python3
"""Basic example using CP-SAT solver with fallback."""

from core import Plan, Bill, Deposit, to_cents, cents_to_str
from core import solve_cpsat, is_ortools_available

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

if is_ortools_available():
    print("Solving with CP-SAT solver...")
    schedule = solve_cpsat(plan, dp_fallback=False)
else:
    print("⚠️  OR-Tools not available, falling back to DP...")
    from core import solve_dp
    schedule = solve_dp(plan)

if schedule:
    w, b2b, delta = schedule.objective
    print(f"\n✅ Solution found using {schedule.solver_used}!")
    print(f"Objective: workdays={w}, b2b={b2b}, |Δ|={cents_to_str(delta)}")
else:
    print("\n❌ No feasible schedule (INFEASIBLE)")
```

### examples/compare_solvers.py

```python
#!/usr/bin/env python3
"""Compare DP and CP-SAT solvers on the same plan."""

import time
from core import Plan, Bill, Deposit, to_cents, cents_to_str
from core import solve_dp, solve_cpsat, is_ortools_available

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

# Solve with DP
print("=" * 60)
print("DP SOLVER")
print("=" * 60)
start = time.time()
dp_schedule = solve_dp(plan)
dp_time = time.time() - start

if dp_schedule:
    w, b2b, delta = dp_schedule.objective
    print(f"✅ Objective: ({w}, {b2b}, {cents_to_str(delta)})")
    print(f"⏱️  Time: {dp_time*1000:.1f}ms")
else:
    print("❌ INFEASIBLE")

# Solve with CP-SAT
print("\n" + "=" * 60)
print("CP-SAT SOLVER")
print("=" * 60)

if is_ortools_available():
    start = time.time()
    cpsat_schedule = solve_cpsat(plan, dp_fallback=False)
    cpsat_time = time.time() - start

    if cpsat_schedule:
        w, b2b, delta = cpsat_schedule.objective
        print(f"✅ Objective: ({w}, {b2b}, {cents_to_str(delta)})")
        print(f"⏱️  Time: {cpsat_time*1000:.1f}ms")

        # Compare
        print("\n" + "=" * 60)
        print("COMPARISON")
        print("=" * 60)
        if dp_schedule and cpsat_schedule:
            if dp_schedule.objective == cpsat_schedule.objective:
                print("✅ Both solvers found the same objective!")
            else:
                print("⚠️  Different objectives (this shouldn't happen)")
                print(f"   DP:     {dp_schedule.objective}")
                print(f"   CP-SAT: {cpsat_schedule.objective}")

            print(f"\nSpeed: DP was {cpsat_time/dp_time:.1f}x faster" if dp_time < cpsat_time
                  else f"\nSpeed: CP-SAT was {dp_time/cpsat_time:.1f}x faster")
    else:
        print("❌ INFEASIBLE")
else:
    print("⚠️  OR-Tools not installed")
    print("   Install with: pip install ortools")
```

---

## requirements.txt

```
# Optional: OR-Tools for CP-SAT solver
# The skill works without this (uses DP solver)
ortools>=9.10.4067
```

**Note:** OR-Tools is **optional**. The skill works perfectly fine with just the DP solver if OR-Tools isn't installed.

---

## Installation & Dependencies

### Minimal Install (DP Only)

```bash
# No installation needed! DP solver is pure Python
python examples/solve_basic_dp.py
```

### Full Install (DP + CP-SAT)

```bash
# Install OR-Tools for CP-SAT solver
pip install ortools

# Now both solvers available
python examples/compare_solvers.py
```

---

## Implementation Steps

### Step 1: Copy Core Modules (2 hours)

```bash
# Create directory structure
mkdir -p cashflow-scheduler/core
mkdir -p cashflow-scheduler/examples

# Copy from existing cashflow package
cp cashflow/core/model.py cashflow-scheduler/core/
cp cashflow/engines/dp.py cashflow-scheduler/core/dp_solver.py
cp cashflow/engines/cpsat.py cashflow-scheduler/core/cpsat_solver.py
cp cashflow/core/ledger.py cashflow-scheduler/core/
cp cashflow/core/validate.py cashflow-scheduler/core/

# Create __init__.py with convenience functions
# (as shown above)
```

### Step 2: Adapt for Skill Bundle (1 hour)

**Changes needed:**
- Update import paths (remove `..core` relative imports, use `from .model import ...`)
- Ensure graceful OR-Tools fallback is preserved
- Add `solver_used` field to Schedule dataclass
- Create convenience `solve()` function in `__init__.py`

### Step 3: Create Example Scripts (1 hour)

Create all 4 example scripts:
- `solve_basic_dp.py`
- `solve_basic_cpsat.py`
- `compare_solvers.py`
- `load_and_solve.py` (loads from JSON)

### Step 4: Write New SKILL.md (2 hours)

**Structure:**
1. Overview - What the skill does
2. Quick Start - Auto solver selection
3. Choosing a Solver - DP vs CP-SAT guidance
4. Loading Plans from JSON
5. Core Modules Reference
6. Example Scripts
7. Troubleshooting
8. Constraint System

### Step 5: Test Both Solver Paths (1 hour)

**Test matrix:**
- ✅ DP solver works (no OR-Tools)
- ✅ CP-SAT solver works (with OR-Tools)
- ✅ Automatic fallback works (CP-SAT → DP when OR-Tools missing)
- ✅ Both solvers find same objective
- ✅ All example plans solve

### Step 6: Package and Validate (30 min)

```bash
python3 skills/skill-creator/scripts/package_skill.py cashflow-scheduler
```

---

## Advantages

✅ **Both solvers included** - DP (fast, no deps) and CP-SAT (verification)
✅ **Graceful fallback** - Works without OR-Tools, better with it
✅ **Self-contained** - No CLI dependency
✅ **Follows official pattern** - Matches slack-gif-creator
✅ **Optional dependencies** - OR-Tools improves it but not required
✅ **Cross-validation** - Can verify DP with CP-SAT
✅ **Production ready** - Works in any Python environment

---

## Timeline

**Total: 7-8 hours**

1. Copy and adapt core modules (2 hours)
2. Create example scripts (1 hour)
3. Write new SKILL.md (2 hours)
4. Update reference docs (1 hour)
5. Test both solver paths (1 hour)
6. Package and validate (1 hour)

---

## Next Steps

Ready to implement! This gives you:

- ✅ **DP solver** (pure Python, always works)
- ✅ **CP-SAT solver** (better verification, requires OR-Tools)
- ✅ **Automatic fallback** (tries CP-SAT, uses DP if unavailable)
- ✅ **Self-contained** (no external CLI needed)
- ✅ **Official pattern** (matches Anthropic's skills)

Should I proceed with this implementation?
