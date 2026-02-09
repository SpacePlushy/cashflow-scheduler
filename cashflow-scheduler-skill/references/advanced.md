# Advanced Usage

Advanced patterns, solver options, and optimization techniques for the cashflow-scheduler skill.

## Table of Contents

- [CP-SAT Solver Options](#cp-sat-solver-options)
- [Locking Specific Days](#locking-specific-days)
- [Manual Adjustments](#manual-adjustments)
- [Iterative Refinement Workflows](#iterative-refinement-workflows)
- [Solver Selection Strategy](#solver-selection-strategy)
- [Performance Optimization](#performance-optimization)

---

## CP-SAT Solver Options

The CP-SAT solver supports advanced options for fine-tuning search behavior.

### Basic Options

```python
from core import solve
from core.cpsat_solver import CPSATSolveOptions

options = CPSATSolveOptions(
    max_time_seconds=30.0,       # Maximum solve time (default: 60.0)
    num_search_workers=4,        # Parallel workers (default: 8)
    log_search_progress=True     # Print search logs (default: False)
)

schedule = solve(plan, solver="cpsat", options=options)
```

### Option Reference

**`max_time_seconds`** (float, default: 60.0)
- Maximum time to spend searching for solution
- Solver returns best solution found so far if timeout
- Use shorter times for interactive use, longer for batch optimization

**`num_search_workers`** (int, default: 8)
- Number of parallel search threads
- More workers = faster on multi-core systems
- Set to 1 for deterministic results

**`log_search_progress`** (bool, default: False)
- Print search progress to stdout
- Useful for debugging slow solves
- Shows bounds, conflicts, and search tree stats

### Example: Fast Interactive Solve

```python
# For interactive UI: return quickly with good-enough solution
fast_options = CPSATSolveOptions(
    max_time_seconds=5.0,
    num_search_workers=4,
    log_search_progress=False
)

schedule = solve(plan, solver="cpsat", options=fast_options)
```

### Example: Thorough Batch Optimization

```python
# For batch processing: maximize solution quality
thorough_options = CPSATSolveOptions(
    max_time_seconds=120.0,
    num_search_workers=16,
    log_search_progress=True
)

schedule = solve(plan, solver="cpsat", options=thorough_options)
```

---

## Locking Specific Days

Lock days to force specific actions, reducing the search space.

### Basic Locking

```python
from core import Plan, to_cents

plan = Plan(
    # ... other fields ...
    actions=[
        "Spark",  # Day 1: Work (required by constraints anyway)
        "O",      # Day 2: Off (locked)
        None,     # Day 3: Solver decides
        None,     # Day 4: Solver decides
        "O",      # Day 5: Off (locked)
        # ... rest are None
    ] + [None] * 25
)

schedule = solve(plan)
```

### Common Locking Patterns

**Lock a weekend off:**
```python
# Force days 6-7 off (weekend)
plan.actions[5:7] = ["O", "O"]
```

**Lock vacation days:**
```python
# Force days 10-14 off (vacation week)
plan.actions[9:14] = ["O"] * 5
```

**Lock known work days:**
```python
# Force specific days as work (e.g., pre-scheduled shifts)
plan.actions[2] = "Spark"   # Day 3
plan.actions[9] = "Spark"   # Day 10
plan.actions[16] = "Spark"  # Day 17
```

**Lock first half, optimize second:**
```python
# Lock days 1-15 to a known schedule, optimize 16-30
known_schedule = ["Spark", "O", "Spark", "O", ...] * 15
plan.actions[:15] = known_schedule
# Days 16-30 remain None (solver decides)
```

### Advanced: Conditional Locking

```python
def create_plan_with_preferences(base_plan, preferred_off_days):
    """Lock preferred days off if financially feasible"""
    plan = base_plan.copy()

    # Try locking all preferred days
    for day in preferred_off_days:
        plan.actions[day - 1] = "O"

    try:
        schedule = solve(plan)
        return schedule  # Success!
    except RuntimeError:
        # Infeasible - try fewer locks
        plan.actions = [None] * 30
        # Lock only first half of preferred days
        for day in preferred_off_days[:len(preferred_off_days)//2]:
            plan.actions[day - 1] = "O"
        return solve(plan)
```

---

## Manual Adjustments

Use manual adjustments for one-time income or expenses.

### One-Time Expenses

```python
from core import Adjustment, to_cents

# Car repair on Day 15
car_repair = Adjustment(
    day=15,
    amount_cents=to_cents(-250.00),
    note="Emergency car repair"
)

plan.manual_adjustments = [car_repair]
schedule = solve(plan)
```

### One-Time Income

```python
# Tax refund on Day 12
tax_refund = Adjustment(
    day=12,
    amount_cents=to_cents(800.00),
    note="Tax refund"
)

plan.manual_adjustments = [tax_refund]
schedule = solve(plan)
```

### Multiple Adjustments

```python
# Multiple one-time events
plan.manual_adjustments = [
    Adjustment(day=5, amount_cents=to_cents(-75.00), note="Birthday gift"),
    Adjustment(day=12, amount_cents=to_cents(200.00), note="Freelance gig"),
    Adjustment(day=20, amount_cents=to_cents(-120.00), note="Vet visit"),
]

schedule = solve(plan)
```

### Adjustments vs Bills

**Use Bills for:**
- Recurring expenses (rent, utilities, subscriptions)
- Scheduled payments
- Events you want to track by name

**Use Adjustments for:**
- One-time corrections
- Unexpected income/expenses
- Reconciling actual vs planned balance
- Mid-month recalculations

---

## Iterative Refinement Workflows

The skill is designed for interactive, iterative refinement.

### Pattern 1: Reduce Workdays

```python
# Start with tight constraints
plan.band_cents = to_cents(25.0)
schedule = solve(plan)
print(f"Workdays: {schedule.objective[0]}")

# User wants fewer workdays - relax constraints
plan.band_cents = to_cents(100.0)
schedule = solve(plan)
print(f"Workdays (relaxed): {schedule.objective[0]}")

# Try lowering target
plan.target_end_cents = to_cents(400.0)  # Was 500.0
schedule = solve(plan)
print(f"Workdays (lower target): {schedule.objective[0]}")
```

### Pattern 2: Move Bills Around

```python
def move_bill(plan, bill_name, new_day):
    """Move a bill to a different day"""
    for bill in plan.bills:
        if bill.name == bill_name:
            plan.bills.remove(bill)
            plan.bills.append(Bill(
                day=new_day,
                name=bill.name,
                amount_cents=bill.amount_cents
            ))
            break
    return plan

# Try moving internet bill from day 5 to day 15
schedule_before = solve(plan)
plan_after = move_bill(plan, "Internet", 15)
schedule_after = solve(plan_after)

print(f"Before: {schedule_before.objective[0]} workdays")
print(f"After:  {schedule_after.objective[0]} workdays")
```

### Pattern 3: Progressive Constraint Relaxation

```python
def find_minimal_workdays(base_plan):
    """Find minimum workdays by progressively relaxing constraints"""
    best_schedule = None

    # Try increasing band sizes
    for band in [25, 50, 100, 150, 200]:
        plan = base_plan.copy()
        plan.band_cents = to_cents(float(band))

        try:
            schedule = solve(plan)
            if best_schedule is None or schedule.objective[0] < best_schedule.objective[0]:
                best_schedule = schedule
                print(f"Band ${band}: {schedule.objective[0]} workdays")
        except RuntimeError:
            print(f"Band ${band}: Infeasible")
            continue

    return best_schedule
```

### Pattern 4: Scenario Comparison

```python
def compare_scenarios(base_plan, scenario_configs):
    """Compare multiple plan variants"""
    results = []

    for name, config in scenario_configs.items():
        plan = base_plan.copy()

        # Apply scenario-specific changes
        for key, value in config.items():
            setattr(plan, key, value)

        try:
            schedule = solve(plan)
            results.append({
                'scenario': name,
                'workdays': schedule.objective[0],
                'final_balance': schedule.final_closing_cents
            })
        except RuntimeError:
            results.append({'scenario': name, 'workdays': None, 'final_balance': None})

    return results

# Usage
scenarios = {
    'Conservative': {'band_cents': to_cents(25.0), 'target_end_cents': to_cents(500.0)},
    'Moderate': {'band_cents': to_cents(50.0), 'target_end_cents': to_cents(450.0)},
    'Relaxed': {'band_cents': to_cents(100.0), 'target_end_cents': to_cents(400.0)},
}

results = compare_scenarios(plan, scenarios)
for r in results:
    print(f"{r['scenario']:15s}: {r['workdays']} workdays, ${cents_to_str(r['final_balance'])}")
```

---

## Solver Selection Strategy

Choose the right solver for your use case.

### Decision Tree

```
Need to solve?
│
├─ OR-Tools installed?
│  ├─ YES → Use "auto" (tries CP-SAT, falls back to DP)
│  └─ NO → Use "dp"
│
├─ Need reproducible results?
│  └─ Use "cpsat" with num_search_workers=1
│
├─ Need fastest possible solve?
│  └─ Use "cpsat" with max num_search_workers
│
└─ Deployment/distribution concern?
   └─ Use "dp" (no dependencies)
```

### Solver Comparison

| Feature | CP-SAT | DP |
|---------|--------|-----|
| Speed (complex problems) | ⚡⚡⚡ Fast | ⚡⚡ Moderate |
| Speed (simple problems) | ⚡⚡ Moderate | ⚡⚡⚡ Fast |
| Dependencies | OR-Tools (large) | None |
| Parallelism | Yes (8 workers) | No |
| Memory usage | Higher | Lower |
| Optimality | Guaranteed | Guaranteed |

### When to Use Each

**Use CP-SAT when:**
- Solving complex plans with many bills and constraints
- Have OR-Tools installed
- Want parallel search
- Batch optimization (can afford longer solve times)

**Use DP when:**
- Distributing to users (no dependencies)
- Simple plans (< 10 bills)
- Need minimal memory footprint
- Embedded/constrained environments

**Use Auto when:**
- Unsure which is better
- Want robustness (fallback if CP-SAT unavailable)
- General-purpose use (recommended default)

---

## Performance Optimization

Tips for faster solves and better solutions.

### 1. Reduce Problem Size

```python
# Bad: Overly tight constraints (more search)
plan.band_cents = to_cents(1.0)  # Forces exact target

# Good: Reasonable tolerance (less search)
plan.band_cents = to_cents(50.0)  # Flexible band
```

### 2. Lock Obvious Days

```python
# If you know you MUST work certain days, lock them
# Reduces search space significantly

plan.actions[0] = "Spark"  # Day 1 (required anyway)
plan.actions[9] = "Spark"  # Day 10 (paycheck day - likely needed)
plan.actions[23] = "Spark" # Day 24 (paycheck day - likely needed)
```

### 3. Use Realistic Rent Guard

```python
# Bad: Overly conservative rent guard
plan.rent_guard_cents = to_cents(3000.0)  # Way more than rent

# Good: Just enough to cover rent
plan.rent_guard_cents = to_cents(1636.0)  # Exactly rent amount
```

### 4. Batch Solving

```python
# When solving many plans, reuse solver instances
from core.cpsat_solver import solve_cpsat
from core.dp_solver import solve_dp

options = CPSATSolveOptions(max_time_seconds=10.0)

for plan in many_plans:
    schedule = solve_cpsat(plan, options)  # Reuses compiled solver
```

### 5. Caching Results

```python
import hashlib
import json
import pickle

def plan_hash(plan):
    """Create hash of plan for caching"""
    plan_dict = {
        'start': plan.start_balance_cents,
        'target': plan.target_end_cents,
        'band': plan.band_cents,
        'bills': [(b.day, b.amount_cents) for b in plan.bills],
        'deposits': [(d.day, d.amount_cents) for d in plan.deposits],
    }
    return hashlib.sha256(json.dumps(plan_dict, sort_keys=True).encode()).hexdigest()

# Cache schedules
cache = {}

def solve_cached(plan):
    """Solve with caching"""
    h = plan_hash(plan)
    if h in cache:
        return cache[h]

    schedule = solve(plan)
    cache[h] = schedule
    return schedule
```

### 6. Parallel Scenario Evaluation

```python
from concurrent.futures import ProcessPoolExecutor

def solve_scenario(scenario_config):
    """Solve a single scenario (for parallel execution)"""
    plan = create_plan_from_config(scenario_config)
    try:
        schedule = solve(plan)
        return {'config': scenario_config, 'schedule': schedule}
    except RuntimeError:
        return {'config': scenario_config, 'schedule': None}

# Solve 100 scenarios in parallel
scenarios = [generate_scenario_config(i) for i in range(100)]

with ProcessPoolExecutor(max_workers=8) as executor:
    results = list(executor.map(solve_scenario, scenarios))

# Analyze results
feasible = [r for r in results if r['schedule'] is not None]
best = min(feasible, key=lambda r: r['schedule'].objective[0])
```

---

## See Also

- [API Reference](api.md) - Complete function documentation
- [JSON Schema](plan_schema.md) - JSON format
- [Constraints](constraints.md) - Constraint system details
- [Troubleshooting](troubleshooting.md) - Debugging guide
