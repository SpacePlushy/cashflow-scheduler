# Plan JSON Schema Documentation

This document describes the JSON format for cashflow scheduler plans.

## Schema Overview

```json
{
  "start_balance": <float>,
  "target_end": <float>,
  "band": <float>,
  "rent_guard": <float>,
  "deposits": [<Deposit>, ...],
  "bills": [<Bill>, ...],
  "actions": [<Action|null>, ...],  // 30 elements
  "manual_adjustments": [<Adjustment>, ...],
  "locks": [[<int>, <int>], ...],
  "metadata": {<string>: <string>, ...}
}
```

## Field Descriptions

### Required Fields

#### `start_balance` (float)
Starting balance in dollars at the beginning of Day 1 (before any transactions).

**Example:** `100.50`

**Valid range:** Any number (can be negative, though solver may fail)

#### `target_end` (float)
Target ending balance in dollars at the end of Day 30.

**Example:** `500.00`

**Note:** The actual final balance must be within `[target_end - band, target_end + band]`

#### `band` (float)
Tolerance band in dollars around the target ending balance.

**Example:** `25.00`

**Valid range:** Non-negative

**Effect:** Larger band = more flexibility = easier to find solutions

#### `rent_guard` (float)
Minimum balance required **before** paying rent on Day 30.

**Example:** `1636.00`

**Purpose:** Ensures you have enough cash to pay rent before it's deducted

**Constraint:** `balance_on_day_30_before_rent >= rent_guard`

### Array Fields

#### `deposits` (array of objects)
Scheduled cash inflows on specific days.

**Deposit object:**
```json
{
  "day": <int 1-30>,
  "amount": <float>
}
```

**Example:**
```json
[
  {"day": 11, "amount": 1021.00},
  {"day": 25, "amount": 1021.00}
]
```

**Notes:**
- Deposits are applied in the **morning** before actions
- Multiple deposits on the same day are allowed and summed
- Amount should be positive

#### `bills` (array of objects)
Scheduled cash outflows on specific days.

**Bill object:**
```json
{
  "day": <int 1-30>,
  "name": <string>,
  "amount": <float>
}
```

**Example:**
```json
[
  {"day": 1, "name": "Auto Insurance", "amount": 177.00},
  {"day": 30, "name": "Rent", "amount": 1636.00}
]
```

**Notes:**
- Bills are applied in the **evening** after actions
- Multiple bills on the same day are allowed and summed
- Amount should be positive
- Name is for documentation only (not used in solving)

#### `actions` (array of strings or null)
Pre-filled or locked actions for specific days.

**Format:** Array of exactly 30 elements, one per day

**Valid values:**
- `null`: Let solver decide
- `"O"`: Force off day
- `"Spark"`: Force work day ($100 net)

**Example:**
```json
[
  "Spark",  // Day 1 (always Spark by business rule)
  null,     // Day 2 (solver decides)
  "O",      // Day 3 (forced off)
  null,     // Day 4 (solver decides)
  ...       // 26 more entries
]
```

**Notes:**
- Day 1 is **always** forced to "Spark" regardless of this field
- Locking too many days may make the problem infeasible

#### `manual_adjustments` (array of objects)
One-time cash corrections on specific days (not recurring).

**Adjustment object:**
```json
{
  "day": <int 1-30>,
  "amount": <float>,
  "note": <string>
}
```

**Example:**
```json
[
  {"day": 15, "amount": -50.00, "note": "Venmo refund correction"},
  {"day": 20, "amount": 25.00, "note": "Found cash"}
]
```

**Notes:**
- Positive = cash in, Negative = cash out
- Applied like deposits (in the morning)
- Use sparingly - they complicate the model

### Optional Fields

#### `locks` (array of tuples)
Range-based action locks (currently unused by solvers).

**Format:** Array of `[start_day, end_day]` tuples

**Example:**
```json
[
  [1, 10],   // Days 1-10 locked
  [25, 30]   // Days 25-30 locked
]
```

**Status:** Deprecated - use `actions` array instead

#### `metadata` (object)
Arbitrary key-value pairs for tracking information.

**Example:**
```json
{
  "version": "1.0.0",
  "created_by": "interactive_create.py",
  "notes": "October budget"
}
```

**Notes:**
- Not used by solver
- Useful for documentation and tracking

## Complete Example

```json
{
  "start_balance": 90.50,
  "target_end": 490.50,
  "band": 25.0,
  "rent_guard": 1636.0,
  "deposits": [
    {"day": 11, "amount": 1021.0},
    {"day": 25, "amount": 1021.0}
  ],
  "bills": [
    {"day": 1, "name": "Auto Insurance", "amount": 177.0},
    {"day": 3, "name": "Internet", "amount": 75.0},
    {"day": 7, "name": "Streaming", "amount": 50.0},
    {"day": 15, "name": "Utilities", "amount": 120.0},
    {"day": 20, "name": "Phone", "amount": 85.0},
    {"day": 30, "name": "Rent", "amount": 1636.0}
  ],
  "actions": [null, null, null, null, null, null, null, null, null, null,
              null, null, null, null, null, null, null, null, null, null,
              null, null, null, null, null, null, null, null, null, null],
  "manual_adjustments": [],
  "locks": [],
  "metadata": {
    "version": "1.0.0",
    "month": "October 2024"
  }
}
```

## Loading in Python

```python
import json
from core import Plan, Bill, Deposit, Adjustment, to_cents

with open('plan.json') as f:
    data = json.load(f)

plan = Plan(
    start_balance_cents=to_cents(data['start_balance']),
    target_end_cents=to_cents(data['target_end']),
    band_cents=to_cents(data['band']),
    rent_guard_cents=to_cents(data['rent_guard']),
    deposits=[
        Deposit(day=d['day'], amount_cents=to_cents(d['amount']))
        for d in data['deposits']
    ],
    bills=[
        Bill(day=b['day'], name=b['name'], amount_cents=to_cents(b['amount']))
        for b in data['bills']
    ],
    actions=data.get('actions', [None] * 30),
    manual_adjustments=[
        Adjustment(day=a['day'], amount_cents=to_cents(a['amount']),
                   note=a.get('note', ''))
        for a in data.get('manual_adjustments', [])
    ],
    locks=data.get('locks', []),
    metadata=data.get('metadata', {})
)
```

## Common Mistakes

### Missing Required Fields
**Error:** `KeyError: 'start_balance'`
**Fix:** Ensure all required fields are present

### Wrong Array Length for actions
**Error:** Schedule validation fails
**Fix:** `actions` must have exactly 30 elements

### Negative band
**Error:** Solver may fail or behave unexpectedly
**Fix:** Use non-negative band value

### Bills exceed available funds
**Error:** `RuntimeError: No feasible schedule found`
**Fix:** Increase deposits, reduce bills, or increase band tolerance

## See Also

- [constraints.md](./constraints.md) - Detailed constraint system
- [troubleshooting.md](./troubleshooting.md) - Common solver issues
