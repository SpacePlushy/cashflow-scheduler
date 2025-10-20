# Phase B: Enhanced Automation Scripts - Implementation Plan V2

## Overview

Phase B adds **automation and helper scripts** to the self-contained solver skill. These scripts make common workflows easier and reduce the amount of code Claude needs to write repeatedly.

**Timeline:** Weeks 3-4 (12-16 hours)
**Status:** 🟡 Ready After Phase A Complete

---

## Key Changes from Original Plan

### ❌ Original Approach
- External scripts that call `./cash` CLI
- Separate from skill bundle

### ✅ New Approach
- Scripts bundled in skill's `scripts/` directory
- Import from `core/` modules
- Claude can execute them directly
- Follows PDF skill pattern (scripts for common operations)

---

## Objectives

### Primary Goals
1. ✅ Add interactive plan creation wizard
2. ✅ Add feasibility pre-check tool
3. ✅ Add infeasibility diagnostic tool
4. ✅ Add month-to-month rollover automation
5. ✅ Update SKILL.md with script usage examples

### Non-Goals (Deferred to Phase C)
- ❌ AI-powered budget optimization
- ❌ Financial advice or recommendations
- ❌ Scenario comparison and analysis
- ❌ Work-life balance scoring

---

## Enhanced Structure

```
cashflow-scheduler/
├── SKILL.md                          # Updated with script workflows
├── core/                             # From Phase A (no changes)
│   ├── __init__.py
│   ├── model.py
│   ├── dp_solver.py
│   ├── cpsat_solver.py
│   ├── ledger.py
│   └── validate.py
├── scripts/                          # NEW - Automation tools
│   ├── create_plan.py                # Interactive plan creation
│   ├── analyze_feasibility.py       # Pre-check before solving
│   ├── explain_infeasible.py        # Why plan failed
│   ├── rollover_month.py            # Auto-generate next month
│   └── compare_solvers.py           # DP vs CP-SAT benchmark
├── examples/                         # From Phase A (no changes)
│   ├── solve_basic.py
│   ├── solve_from_json.py
│   ├── compare_solvers.py
│   └── interactive_create.py
├── references/                       # From Phase A (minor updates)
│   ├── plan_schema.md
│   ├── troubleshooting.md
│   ├── dp_algorithm.md
│   ├── cpsat_algorithm.md
│   ├── constraints.md
│   └── automation_guide.md          # NEW - Script usage guide
└── assets/                           # From Phase A (no changes)
    └── example_plans/
```

---

## New Scripts Specification

### 1. scripts/create_plan.py

**Purpose:** Interactive wizard for creating valid plan.json files

**Features:**
- Prompts for all required fields
- Validates inputs in real-time
- Suggests reasonable defaults
- Detects recurring bill/deposit patterns
- Saves to JSON file

**Usage:**
```bash
python scripts/create_plan.py --output my_plan.json
```

**Implementation:** ~200 lines
- Interactive prompts using `input()`
- Validation with `core.model` classes
- Pattern detection for recurring transactions
- JSON export with nice formatting

**Key Functions:**
```python
def prompt_balance(prompt: str, default: float) -> int:
    """Prompt for dollar amount, convert to cents."""

def prompt_bills() -> List[Bill]:
    """Interactively collect bills with pattern detection."""

def prompt_deposits() -> List[Deposit]:
    """Interactively collect deposits with pattern detection."""

def detect_recurring_pattern(items: List) -> Optional[str]:
    """Detect weekly/biweekly patterns."""

def create_plan_interactive() -> Plan:
    """Main interactive flow."""
```

---

### 2. scripts/analyze_feasibility.py

**Purpose:** Pre-check plan feasibility without running full solver

**Features:**
- Quick math checks (bills vs income + work)
- Rent guard achievability check
- Band feasibility check
- Early-day solvency check
- Recommendations for fixes

**Usage:**
```bash
python scripts/analyze_feasibility.py plan.json
```

**Output:**
```
Analyzing plan.json...

✅ Basic Feasibility: LIKELY FEASIBLE
   Total bills: $2,500.00
   Total deposits: $2,000.00
   Max work earnings: $3,000.00
   Available: $5,000.00 >= Required: $2,900.00

✅ Rent Guard: ACHIEVABLE
   Need $1,600 before day 30 bills
   Available: $2,500 (deposits + work)

⚠️  Target Band: TIGHT
   Target: $500 ± $25
   This leaves little room for optimization
   Recommendation: Increase band to $50

Overall: Plan is likely feasible but may require many workdays
```

**Implementation:** ~150 lines
- Load plan from JSON
- Perform quick calculations
- No solver needed
- Generate report with recommendations

---

### 3. scripts/explain_infeasible.py

**Purpose:** Diagnose why a plan is infeasible

**Features:**
- Binary search to find minimal infeasible subset
- Identify which constraints are violated
- Suggest specific fixes
- Show "what-if" scenarios

**Usage:**
```bash
python scripts/explain_infeasible.py plan.json
```

**Output:**
```
Diagnosing infeasible plan...

❌ Plan is INFEASIBLE

Root cause: Insufficient funds
   Total bills: $3,500.00
   Total deposits: $1,000.00
   Max possible work: $3,000.00 (30 days × $100)
   Shortfall: $500.00

Possible fixes:
1. Add $500 to start_balance
2. Add a deposit of $500 (any day)
3. Reduce bills by $500 total
4. Lower target_end by $500

Testing fix #2 (add $500 deposit on day 15)...
✅ With this fix, plan becomes FEASIBLE
```

**Implementation:** ~250 lines
- Try removing constraints one by one
- Binary search for minimal fix
- Generate concrete suggestions
- Test suggestions to verify

---

### 4. scripts/rollover_month.py

**Purpose:** Auto-generate next month's plan from current month's solution

**Features:**
- Use current month's final balance as next month's start
- Copy recurring bills/deposits (with date shift)
- Preserve rent guard and band settings
- Optional manual override for one-time changes

**Usage:**
```bash
python scripts/rollover_month.py \
    --current-plan october.json \
    --current-schedule october_solution.json \
    --output november.json
```

**Output:**
```
Rolling over October → November...

From October solution:
   Final balance: $485.27
   → November start_balance: $485.27

Recurring bills detected (shifted +30 days):
   ✓ Rent: Day 30 → Day 30 (always end of month)
   ✓ Phone: Day 5 → Day 5
   ✓ Groceries: Days 7, 14, 21, 28 → Days 7, 14, 21, 28

Recurring deposits detected (shift pattern):
   ✓ Biweekly paycheck pattern detected
   ✓ Day 10, 24 → Day 9, 23 (adjusted for month length)

Created: november.json
```

**Implementation:** ~180 lines
- Load current plan and solution
- Detect recurring patterns
- Shift dates appropriately
- Handle month-length differences (28/30/31 days)
- Generate new plan JSON

---

### 5. scripts/compare_solvers.py

**Purpose:** Benchmark DP vs CP-SAT on plans

**Features:**
- Run both solvers on same plan
- Compare objectives (should match)
- Show timing difference
- Detailed diagnostics
- Optional: run on all example plans

**Usage:**
```bash
python scripts/compare_solvers.py plan.json
python scripts/compare_solvers.py --all-examples
```

**Output:**
```
Comparing solvers on plan.json...

DP Solver:
   ✅ Objective: (12, 0, 48.47)
   ⏱️  Time: 23ms
   📊 States explored: 15,432

CP-SAT Solver:
   ✅ Objective: (12, 0, 48.47)
   ⏱️  Time: 156ms
   📊 Constraints: 2,847
   📊 Variables: 930

Verification: ✅ Both solvers agree!
Performance: DP is 6.8× faster
```

**Implementation:** ~120 lines
- Import both solvers
- Time execution
- Compare results
- Display diagnostics
- Handle missing OR-Tools gracefully

---

## Updated SKILL.md Sections

### New Section: "Automation Scripts"

```markdown
## Automation Scripts

The skill includes helper scripts for common workflows:

### Create a Plan Interactively

```bash
python scripts/create_plan.py --output my_plan.json
```

Walks you through creating a valid plan with prompts for each field.

### Check Feasibility Before Solving

```bash
python scripts/analyze_feasibility.py my_plan.json
```

Quickly checks if a plan is likely feasible without running the full solver.

### Diagnose Infeasible Plans

```bash
python scripts/explain_infeasible.py my_plan.json
```

Explains why a plan is infeasible and suggests specific fixes.

### Roll Over to Next Month

```bash
python scripts/rollover_month.py \
    --current-plan october.json \
    --current-schedule october_solution.json \
    --output november.json
```

Auto-generates next month's plan from current month's results.

### Compare Solver Performance

```bash
python scripts/compare_solvers.py my_plan.json
```

Benchmarks DP vs CP-SAT solvers and verifies they agree.

For detailed script documentation, see [references/automation_guide.md](references/automation_guide.md).
```

---

## Implementation Checklist

### Script Development (8 hours)

#### create_plan.py (2 hours)
- [ ] Interactive prompts for all fields
- [ ] Real-time validation
- [ ] Pattern detection for recurring items
- [ ] JSON export with formatting
- [ ] Help text and examples

#### analyze_feasibility.py (1.5 hours)
- [ ] Load plan from JSON
- [ ] Basic math checks
- [ ] Rent guard check
- [ ] Band analysis
- [ ] Generate recommendations

#### explain_infeasible.py (2.5 hours)
- [ ] Detect infeasibility
- [ ] Binary search for minimal fix
- [ ] Constraint violation analysis
- [ ] Generate concrete suggestions
- [ ] Test suggestions

#### rollover_month.py (1.5 hours)
- [ ] Extract final balance
- [ ] Detect recurring patterns
- [ ] Shift dates appropriately
- [ ] Handle month-length differences
- [ ] Generate new plan

#### compare_solvers.py (30 minutes)
- [ ] Run both solvers
- [ ] Time execution
- [ ] Compare objectives
- [ ] Display diagnostics
- [ ] Handle OR-Tools absence

### Documentation Updates (2 hours)

#### automation_guide.md (1 hour)
- [ ] Detailed script usage examples
- [ ] Common workflow patterns
- [ ] Troubleshooting script errors
- [ ] Best practices

#### SKILL.md Updates (1 hour)
- [ ] Add "Automation Scripts" section
- [ ] Update "Quick Start" with script examples
- [ ] Add workflow diagrams
- [ ] Link to automation_guide.md

### Testing (2 hours)

#### Script Testing (1.5 hours)
- [ ] Test create_plan.py with various inputs
- [ ] Test analyze_feasibility.py on all example plans
- [ ] Test explain_infeasible.py on intentionally broken plans
- [ ] Test rollover_month.py with October → November
- [ ] Test compare_solvers.py with and without OR-Tools

#### Integration Testing (30 minutes)
- [ ] End-to-end: create → analyze → solve → rollover
- [ ] Verify all scripts work from skill directory
- [ ] Test with example plans
- [ ] Validate package_skill.py still passes

---

## Success Criteria

### Script Functionality
- [ ] create_plan.py creates valid plans that solve
- [ ] analyze_feasibility.py correctly predicts feasibility
- [ ] explain_infeasible.py identifies root causes
- [ ] rollover_month.py preserves patterns correctly
- [ ] compare_solvers.py shows both solvers agree

### Code Quality
- [ ] All scripts have clear help text
- [ ] Error messages are helpful
- [ ] Scripts handle edge cases gracefully
- [ ] No hardcoded paths or assumptions
- [ ] Docstrings on all functions

### Documentation
- [ ] automation_guide.md covers all scripts
- [ ] SKILL.md integrates scripts into workflows
- [ ] Examples show typical usage
- [ ] Troubleshooting section updated

### User Experience
- [ ] Scripts are easy to discover
- [ ] Help text is clear
- [ ] Output is readable and useful
- [ ] Error messages suggest fixes
- [ ] Scripts work together smoothly

---

## Deliverables

1. **Updated cashflow-scheduler.zip** (55-60 KB)
   - All Phase A features
   - 5 automation scripts
   - Updated documentation
   - Integration examples

2. **PHASE_B_COMPLETE.md**
   - Implementation summary
   - Script usage examples
   - Performance metrics

3. **Updated SKILL_ROADMAP.md**
   - Phase B completion
   - Phase C preview

---

## Timeline Breakdown

| Task | Time | Cumulative |
|------|------|------------|
| create_plan.py | 2 hrs | 2 hrs |
| analyze_feasibility.py | 1.5 hrs | 3.5 hrs |
| explain_infeasible.py | 2.5 hrs | 6 hrs |
| rollover_month.py | 1.5 hrs | 7.5 hrs |
| compare_solvers.py | 0.5 hrs | 8 hrs |
| automation_guide.md | 1 hr | 9 hrs |
| SKILL.md updates | 1 hr | 10 hrs |
| Script testing | 1.5 hrs | 11.5 hrs |
| Integration testing | 0.5 hrs | 12 hrs |
| **TOTAL** | **12 hours** | |

---

## Dependencies

### Phase A Must Be Complete
- ✅ Core modules working (DP + CP-SAT)
- ✅ Example plans available
- ✅ Base SKILL.md written

### Optional
- ⚠️ OR-Tools (for compare_solvers.py full functionality)

---

## Next Steps After Phase B

Phase B completes the "power user" features - automation and diagnostics. Phase C will add AI-powered intelligence:

- Budget optimization
- Scenario analysis
- Financial health scoring
- Work-life balance recommendations
- Predictive features

Phase B sets the foundation by providing the tools; Phase C adds the intelligence layer on top.
