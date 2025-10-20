# Troubleshooting Guide

Common issues and solutions when using the cashflow scheduler.

## Solver Errors

### "No feasible schedule found"

**Symptom:**
```python
RuntimeError: No feasible schedule found under constraints and band
```

**Common Causes:**

1. **Bills exceed available funds**
   ```python
   total_needed = sum(b.amount_cents for b in plan.bills)
   total_available = (plan.start_balance_cents +
                      sum(d.amount_cents for d in plan.deposits) +
                      30 * 10000)  # Max work income

   if total_needed > total_available:
       print("Impossible: Not enough potential income")
   ```

2. **Target end + rent guard too high**
   - Solver needs to save for target_end while maintaining rent_guard
   - Try: Lower target_end or increase band

3. **Too many locked "O" days**
   - Forcing too many off days prevents earning enough
   - Try: Remove locks or reduce to essential ones only

4. **Band too tight**
   - Very small band makes it hard to hit exact target
   - Try: Increase band from $25 to $50+

**Solutions (in order of preference):**

1. Increase band tolerance:
   ```python
   plan.band_cents = to_cents(50.0)  # Was 25.0
   ```

2. Lower target end slightly:
   ```python
   plan.target_end_cents = to_cents(450.0)  # Was 500.0
   ```

3. Reduce rent guard to minimum:
   ```python
   rent_amount = max(b.amount_cents for b in plan.bills if b.day == 30)
   plan.rent_guard_cents = rent_amount  # Just enough for rent
   ```

4. Add deposits or reduce bills:
   ```python
   plan.deposits.append(Deposit(day=15, amount_cents=to_cents(200.0)))
   ```

5. Remove action locks:
   ```python
   plan.actions = [None] * 30  # Let solver decide everything
   ```

### "OR-Tools CP-SAT not installed"

**Symptom:**
```python
RuntimeError: OR-Tools CP-SAT not installed
```

**Cause:** OR-Tools library not available and dp_fallback=False

**Solutions:**

1. **Install OR-Tools:**
   ```bash
   pip install ortools
   ```

2. **Enable DP fallback (recommended):**
   ```python
   from core import solve

   # This automatically falls back to DP if CP-SAT unavailable
   schedule = solve(plan)  # solver="auto" by default
   ```

3. **Use DP solver explicitly:**
   ```python
   schedule = solve(plan, solver="dp")
   ```

## Import Errors

### "ModuleNotFoundError: No module named 'core'"

**Cause:** Python path doesn't include skill directory

**Solutions:**

1. **Run from skill root directory:**
   ```bash
   cd cashflow-scheduler
   python examples/solve_basic.py
   ```

2. **Add skill to Python path:**
   ```python
   import sys
   from pathlib import Path

   skill_root = Path(__file__).parent.parent
   sys.path.insert(0, str(skill_root))

   from core import solve, Plan
   ```

### "ImportError: cannot import name 'solve'"

**Cause:** Circular import or core/__init__.py missing

**Solution:** Ensure core/__init__.py exists and contains solve function

## Validation Errors

### "Day 1 Spark: FAIL"

**Symptom:**
```python
report = validate(plan, schedule)
# Shows: ✗ Day 1 Spark: O
```

**Cause:** Schedule violated Day 1 work rule (should be impossible with correct solvers)

**Solution:** This indicates solver bug - report as issue

### "Non-negative balances: FAIL"

**Symptom:** Some day has negative closing balance

**Cause:** Schedule violated feasibility (should be impossible with correct solvers)

**Solution:** Indicates solver bug or manual schedule edit - recompute schedule

### "Final within band: FAIL"

**Symptom:** Final balance outside [target - band, target + band]

**Example:**
```
Final within band: FAIL - 46050 not in [46500, 51500]
```

**Cause:** Schedule violated band constraint

**Solution:** Indicates solver bug - report as issue

### "Day-30 pre-rent guard: FAIL"

**Symptom:** Not enough cash before rent on Day 30

**Cause:** Rent guard constraint violated

**Solution:** Indicates solver bug - report as issue

## Performance Issues

### "Solver takes too long (>10 seconds)"

**Symptom:** CP-SAT solver runs but doesn't finish

**Causes:**
- Complex plan with many constraints
- Many locked actions
- OR-Tools trying to prove optimality

**Solutions:**

1. **Use DP solver instead:**
   ```python
   schedule = solve(plan, solver="dp")  # Usually faster
   ```

2. **Increase CP-SAT time limit:**
   ```python
   from core.cpsat_solver import CPSATSolveOptions

   options = CPSATSolveOptions(max_time_seconds=30.0)
   schedule = solve(plan, solver="cpsat", options=options)
   ```

3. **Reduce search workers:**
   ```python
   options = CPSATSolveOptions(num_search_workers=4)
   schedule = solve(plan, solver="cpsat", options=options)
   ```

## Data Issues

### "TypeError: to_cents() argument must be str, float, or int"

**Cause:** Passing None or invalid type to to_cents

**Solution:**
```python
# Wrong
amount = to_cents(None)  # ✗

# Right
amount = to_cents(100.0)  # ✓
amount = to_cents("100.50")  # ✓
amount = to_cents(10000)  # ✓ (cents directly)
```

### "IndexError: list index out of range" with actions

**Cause:** actions array not exactly 30 elements

**Solution:**
```python
# Wrong
plan.actions = [None, None, None]  # ✗ Only 3 elements

# Right
plan.actions = [None] * 30  # ✓ Exactly 30
plan.actions = ["Spark"] + [None] * 29  # ✓ Day 1 fixed, rest flexible
```

### "ValueError: day must be in range 1-30"

**Cause:** Bill or Deposit with day outside valid range

**Solution:**
```python
# Wrong
Bill(day=0, name="Early", amount_cents=10000)  # ✗ day 0
Bill(day=31, name="Late", amount_cents=10000)  # ✗ day 31

# Right
Bill(day=1, name="First", amount_cents=10000)  # ✓
Bill(day=30, name="Last", amount_cents=10000)  # ✓
```

## JSON Loading Issues

### "json.JSONDecodeError"

**Cause:** Malformed JSON file

**Common mistakes:**
- Trailing commas
- Missing quotes around keys
- Using single quotes instead of double

**Solution:**
```json
// Wrong
{
  'start_balance': 100,  // Single quotes
  'bills': [
    {'day': 1, 'name': 'Rent', 'amount': 1000},  // Trailing comma
  ]
}

// Right
{
  "start_balance": 100,
  "bills": [
    {"day": 1, "name": "Rent", "amount": 1000}
  ]
}
```

### "KeyError: 'start_balance'"

**Cause:** Missing required field in JSON

**Solution:** Ensure all required fields present:
```json
{
  "start_balance": 100.0,      // Required
  "target_end": 500.0,         // Required
  "band": 25.0,                // Required
  "rent_guard": 1600.0,        // Required
  "deposits": [],              // Required (can be empty)
  "bills": [],                 // Required (can be empty)
  "actions": [null, ...],      // Optional
  "manual_adjustments": [],    // Optional
  "locks": [],                 // Optional
  "metadata": {}               // Optional
}
```

## Getting Help

If issues persist:

1. **Enable DP fallback:** Ensures solver always works
   ```python
   schedule = solve(plan)  # Auto-fallback enabled
   ```

2. **Simplify plan:** Remove manual_adjustments, locks, reduce bills

3. **Check example plans:** Compare against working examples in assets/example_plans/

4. **Validate inputs:** Ensure all amounts are positive, days in 1-30 range

5. **Try DP solver directly:** Bypasses CP-SAT issues
   ```python
   schedule = solve(plan, solver="dp")
   ```

## Debugging Checklist

- [ ] All bills/deposits have days in range 1-30
- [ ] actions array has exactly 30 elements
- [ ] All amounts are positive (except manual_adjustments)
- [ ] Total bills < start_balance + deposits + max_work_income
- [ ] rent_guard <= rent_amount (not excessively high)
- [ ] band is reasonable (>= $25)
- [ ] target_end is achievable given constraints
- [ ] No circular/impossible locks
