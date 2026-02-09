# Phase A: Self-Contained Solver Skill - Implementation Plan V2

## Overview

Phase A creates a **fully functional, self-contained skill** that bundles both DP and CP-SAT solvers directly in the skill. No external CLI tools required - Claude can solve schedules immediately upon loading the skill.

**Timeline:** Week 1 (6-8 hours)
**Status:** 🟢 Ready to Implement

---

## Key Change from Original Plan

### ❌ Original Approach (Rejected)
- Documented the `./cash` CLI tool
- Required users to install tool separately
- Skill was just documentation, not functional

### ✅ New Approach (Official Pattern)
- **Bundle solver code directly in the skill**
- Works immediately when loaded
- Follows official Anthropic pattern (slack-gif-creator)
- Includes both CP-SAT (primary) and DP (fallback)

---

## Objectives

### Primary Goals
1. ✅ Bundle working DP and CP-SAT solvers in the skill
2. ✅ Enable Claude to solve plans without external dependencies
3. ✅ Automatic fallback to DP if OR-Tools not available
4. ✅ Provide working example scripts
5. ✅ Maintain comprehensive documentation

### Non-Goals (Deferred to Later Phases)
- ❌ Interactive plan creation wizards
- ❌ Financial planning advice
- ❌ Advanced optimization strategies
- ❌ Web UI or API

---

## Skill Structure

```
cashflow-scheduler/
├── SKILL.md                          # ~300 lines - Instructions with code examples
├── core/                             # Bundled solver code
│   ├── __init__.py                   # Convenience functions
│   ├── model.py                      # Plan, Schedule, Bill, Deposit classes
│   ├── dp_solver.py                  # DP algorithm (pure Python)
│   ├── cpsat_solver.py               # CP-SAT algorithm (with fallback)
│   ├── ledger.py                     # Daily balance calculations
│   └── validate.py                   # Constraint validation
├── examples/                         # Runnable examples
│   ├── solve_basic.py                # Simple solve example
│   ├── solve_from_json.py            # Load and solve JSON plan
│   ├── compare_solvers.py            # DP vs CP-SAT comparison
│   └── interactive_create.py         # Manual plan creation
├── references/
│   ├── plan_schema.md                # ~300 lines - Complete JSON spec
│   ├── troubleshooting.md            # ~200 lines - Common issues & fixes
│   ├── dp_algorithm.md               # ~150 lines - DP solver explanation
│   ├── cpsat_algorithm.md            # ~150 lines - CP-SAT solver explanation
│   └── constraints.md                # ~150 lines - Constraint system
├── assets/
│   └── example_plans/
│       ├── simple_plan.json          # Minimal viable plan
│       ├── complex_plan.json         # With locks & adjustments
│       ├── tight_budget.json         # Barely feasible
│       └── comfortable.json          # Easy scenario
└── requirements.txt                  # ortools (optional)
```

**Total Estimated Size:**
- Python code: ~1,500 lines
- Documentation: ~1,250 lines
- Examples: ~400 lines

---

## Implementation Checklist

### Setup (30 minutes)
- [x] Archive old Phase A skill (cashflow-scheduler.zip → cashflow-scheduler-v1.zip)
- [ ] Remove old cashflow-scheduler directory
- [ ] Run `python skills/skill-creator/scripts/init_skill.py cashflow-scheduler --path .`
- [ ] Review generated template structure
- [ ] Delete unnecessary example files from init

### Core Modules (3 hours)

#### Copy and Adapt Existing Code (1.5 hours)
- [ ] Copy `cashflow/core/model.py` → `core/model.py`
  - Keep: Plan, Schedule, Bill, Deposit, Adjustment dataclasses
  - Keep: SHIFT_NET_CENTS, to_cents(), cents_to_str()
  - Remove: CLI-specific code
- [ ] Copy `cashflow/engines/dp.py` → `core/dp_solver.py`
  - Rename: `solve()` → `solve_dp()`
  - Update: Import paths (remove `..core`)
  - Add: Returns Schedule with `solver_used="DP"`
- [ ] Copy `cashflow/engines/cpsat.py` → `core/cpsat_solver.py`
  - Rename: `solve_with_diagnostics()` → `solve_cpsat()`
  - Keep: OR-Tools try/except fallback
  - Add: Returns Schedule with `solver_used="CPSAT"`
  - Add: `dp_fallback=True` parameter
- [ ] Copy `cashflow/core/ledger.py` → `core/ledger.py`
  - Keep: `build_ledger()` function
  - Update: Import paths
- [ ] Copy `cashflow/core/validate.py` → `core/validate.py`
  - Keep: `validate()` function
  - Update: Import paths

#### Create Convenience Module (30 minutes)
- [ ] Create `core/__init__.py` with:
  - Import all classes and functions
  - Add `solve(plan, solver="auto")` function
  - Add `is_ortools_available()` check
  - Export clean API via `__all__`

#### Test Core Modules (1 hour)
- [ ] Test imports work: `from core import solve, Plan`
- [ ] Test DP solver: `solve_dp(simple_plan)`
- [ ] Test CP-SAT solver: `solve_cpsat(simple_plan)`
- [ ] Test auto fallback: Works with and without OR-Tools
- [ ] Test with all 4 example plans

### Example Scripts (1.5 hours)

#### Basic Examples (45 minutes)
- [ ] Create `examples/solve_basic.py`
  - Import from core
  - Create simple plan programmatically
  - Solve and print results
  - ~50 lines
- [ ] Create `examples/solve_from_json.py`
  - Load plan from JSON file
  - Convert to Plan object
  - Solve and display ledger
  - ~80 lines

#### Advanced Examples (45 minutes)
- [ ] Create `examples/compare_solvers.py`
  - Run both DP and CP-SAT
  - Compare objectives
  - Show timing difference
  - ~100 lines
- [ ] Create `examples/interactive_create.py`
  - Prompt user for plan details
  - Build Plan object
  - Solve and save to JSON
  - ~120 lines

### SKILL.md Content (2 hours)

#### Section 1: Overview & Quick Start (30 min)
- [ ] Write YAML frontmatter
  - name: cashflow-scheduler
  - description: Complete description with triggers
- [ ] Add overview paragraph
- [ ] Show simplest possible example (5 lines of code)
- [ ] Explain what gets returned

#### Section 2: Solver Selection (20 min)
- [ ] Document automatic solver selection
- [ ] Show how to choose DP explicitly
- [ ] Show how to choose CP-SAT explicitly
- [ ] Explain when to use each

#### Section 3: Creating Plans (30 min)
- [ ] Show programmatic plan creation
- [ ] Show loading from JSON
- [ ] Document Plan class fields
- [ ] Point to plan_schema.md for details

#### Section 4: Working with Results (20 min)
- [ ] Explain Schedule object
- [ ] Show how to access objective tuple
- [ ] Show how to get daily ledger
- [ ] Show validation checks

#### Section 5: Example Scripts (10 min)
- [ ] List all examples in examples/
- [ ] Brief description of each
- [ ] How to run them

#### Section 6: Troubleshooting (20 min)
- [ ] Common errors
- [ ] OR-Tools installation
- [ ] Infeasible plans
- [ ] Link to troubleshooting.md

#### Section 7: Constraint System (10 min)
- [ ] List 5 hard constraints
- [ ] Link to constraints.md for details

### References Updates (1 hour)

#### Keep Existing (30 minutes)
- [ ] Copy plan_schema.md (no changes)
- [ ] Copy troubleshooting.md (no changes)
- [ ] Copy constraints.md (no changes)

#### Add New (30 minutes)
- [ ] Create dp_algorithm.md
  - Explain DP state space
  - Show pruning strategy
  - Complexity analysis
  - ~150 lines
- [ ] Create cpsat_algorithm.md
  - Explain CP-SAT model
  - Show constraints encoding
  - Lexicographic optimization
  - ~150 lines

### Assets (10 minutes)
- [ ] Copy all 4 example_plans/*.json (no changes)

### Testing & Validation (1 hour)

#### Functionality Tests (30 minutes)
- [ ] Test: `from core import solve, Plan`
- [ ] Test: Create simple plan, solve with auto
- [ ] Test: Load simple_plan.json and solve
- [ ] Test: Compare DP vs CP-SAT results
- [ ] Test: All 4 example plans solve successfully
- [ ] Test: Graceful fallback when OR-Tools missing

#### Validation (30 minutes)
- [ ] Run: `python3 skills/skill-creator/scripts/package_skill.py cashflow-scheduler`
- [ ] Verify: YAML frontmatter validates
- [ ] Verify: All files included in zip
- [ ] Verify: File structure correct
- [ ] Verify: Import paths work from skill directory

---

## Success Criteria - All Must Pass ✅

### 1. Solver Functionality
- [ ] DP solver works without any dependencies
- [ ] CP-SAT solver works when OR-Tools installed
- [ ] Auto fallback works (CP-SAT → DP when OR-Tools missing)
- [ ] Both solvers find same objective for all test plans
- [ ] Solve time < 1 second for typical plans

### 2. Code Quality
- [ ] No external dependencies except ortools (optional)
- [ ] Clean import structure (`from core import ...`)
- [ ] All modules are self-contained
- [ ] No relative imports outside core/
- [ ] Docstrings on all public functions

### 3. Example Scripts
- [ ] All 4 examples run without errors
- [ ] Examples demonstrate key features
- [ ] Examples include helpful comments
- [ ] Examples work with bundled example plans

### 4. Documentation
- [ ] SKILL.md < 400 lines
- [ ] No duplication with references
- [ ] Code examples are correct and runnable
- [ ] References are comprehensive
- [ ] Links between docs work correctly

### 5. Skill Validation
- [ ] Passes package_skill.py validation
- [ ] YAML frontmatter correct
- [ ] Name matches directory name
- [ ] Description triggers on appropriate queries
- [ ] Total skill size < 50 KB

---

## Key Files to Create

### core/__init__.py (Critical)
```python
"""Cashflow scheduler core modules."""

from .model import (
    Plan, Schedule, Bill, Deposit, Adjustment,
    SHIFT_NET_CENTS, to_cents, cents_to_str
)
from .dp_solver import solve_dp
from .cpsat_solver import solve_cpsat, is_ortools_available
from .ledger import build_ledger
from .validate import validate

def solve(plan: Plan, solver: str = "auto"):
    """
    Solve a plan using specified solver.

    Args:
        plan: Financial plan to solve
        solver: "auto" (tries CP-SAT, falls back to DP),
                "dp" (DP only), or "cpsat" (CP-SAT only)

    Returns:
        Schedule if feasible, None if infeasible
    """
    if solver == "auto":
        return solve_cpsat(plan, dp_fallback=True)
    elif solver == "dp":
        return solve_dp(plan)
    elif solver == "cpsat":
        return solve_cpsat(plan, dp_fallback=False)
    else:
        raise ValueError(f"Unknown solver: {solver}")

__all__ = [
    "Plan", "Schedule", "Bill", "Deposit", "Adjustment",
    "SHIFT_NET_CENTS", "to_cents", "cents_to_str",
    "solve", "solve_dp", "solve_cpsat",
    "is_ortools_available",
    "build_ledger", "validate"
]
```

### requirements.txt
```
# Optional: OR-Tools for CP-SAT solver
# Skill works with DP solver if this is not installed
ortools>=9.10.4067
```

---

## Testing Workflow

### Step 1: Test Without OR-Tools
```bash
# Ensure OR-Tools not in environment
pip uninstall ortools -y

# Test DP solver
python examples/solve_basic.py

# Test auto fallback
python -c "from core import solve, Plan; print('DP fallback works!')"
```

### Step 2: Test With OR-Tools
```bash
# Install OR-Tools
pip install ortools

# Test CP-SAT solver
python examples/compare_solvers.py

# Should show both solvers agree
```

### Step 3: Test All Examples
```bash
python examples/solve_basic.py
python examples/solve_from_json.py assets/example_plans/simple_plan.json
python examples/compare_solvers.py
python examples/interactive_create.py
```

---

## Deliverables

1. **cashflow-scheduler.zip** (45-50 KB)
   - Fully functional skill
   - Both solvers included
   - 4 working examples
   - Comprehensive documentation

2. **PHASE_A_COMPLETE_V2.md**
   - Implementation summary
   - Test results
   - Comparison with v1

3. **Updated SKILL_ROADMAP.md**
   - Reflect new Phase A scope
   - Update Phase B/C plans

---

## Timeline Breakdown

| Task | Time | Cumulative |
|------|------|------------|
| Setup & cleanup | 30 min | 0.5 hrs |
| Copy & adapt core modules | 1.5 hrs | 2 hrs |
| Create __init__.py | 30 min | 2.5 hrs |
| Test core modules | 1 hr | 3.5 hrs |
| Create example scripts | 1.5 hrs | 5 hrs |
| Write SKILL.md | 2 hrs | 7 hrs |
| Update references | 1 hr | 8 hrs |
| Testing & validation | 1 hr | 9 hrs |
| **TOTAL** | **9 hours** | |

**Note:** Reduced from 6-8 hours to 9 hours to account for both solvers and more thorough testing.

---

## Risks & Mitigation

### Risk: OR-Tools Import Issues
**Impact:** CP-SAT solver won't work
**Mitigation:** Graceful fallback to DP already built-in

### Risk: Import Path Issues
**Impact:** Core modules can't find each other
**Mitigation:** Test imports early and often

### Risk: Solver Disagreement
**Impact:** DP and CP-SAT find different objectives
**Mitigation:** Comprehensive test suite, both are battle-tested

### Risk: Skill Too Large
**Impact:** Exceeds size limits for skills
**Mitigation:** Current estimate 45-50KB, well under limits

---

## Next Steps

Once Phase A is complete:

1. **Validation:** Test skill in actual Claude environment
2. **User Testing:** Get feedback on bundled code approach
3. **Phase B Planning:** Update PHASE_B_PLAN.md with automation scripts
4. **Phase C Planning:** Update PHASE_C_PLAN.md with AI features

Phase A establishes the foundation - a working, self-contained solver that Claude can use immediately. All future phases build on this.
