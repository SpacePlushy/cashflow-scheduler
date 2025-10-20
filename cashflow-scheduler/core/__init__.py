"""Cashflow Scheduler Core Package

This package provides constraint-based work schedule optimization for 30-day
cashflow planning. It includes both CP-SAT (OR-Tools) and DP solvers with
automatic fallback.

Quick Start:
    from core import solve, Plan, Bill, Deposit, to_cents

    plan = Plan(
        start_balance_cents=to_cents(100.00),
        target_end_cents=to_cents(200.00),
        band_cents=to_cents(50.0),
        rent_guard_cents=to_cents(800.0),
        deposits=[Deposit(day=15, amount_cents=to_cents(500.0))],
        bills=[Bill(day=30, name="Rent", amount_cents=to_cents(800.0))],
        actions=[None] * 30,
        manual_adjustments=[],
        locks=[],
        metadata={}
    )

    schedule = solve(plan)  # Auto-selects CP-SAT, falls back to DP
    print(f"Workdays: {schedule.objective[0]}")
    print(f"Schedule: {' '.join(schedule.actions)}")
"""

from __future__ import annotations

from typing import TYPE_CHECKING

# Import core data models
from .model import (
    Plan,
    Schedule,
    Bill,
    Deposit,
    Adjustment,
    DayLedger,
    to_cents,
    cents_to_str,
    SHIFT_NET_CENTS,
    build_prefix_arrays,
    pre_rent_base_on_day30,
)

# Import ledger builder
from .ledger import build_ledger

# Import validation
from .validate import validate, ValidationReport

# Import solvers
from . import dp_solver
from . import cpsat_solver

if TYPE_CHECKING:
    from typing import Optional, Any


def adjust_from_day(
    original_plan: Plan,
    current_day: int,
    current_eod_balance: float,
    solver: str = "auto",
    **kwargs: Any
) -> Schedule:
    """
    Adjust schedule from a specific day with a known end-of-day balance.

    This is the primary function for mid-month adjustments. Use when you know
    your actual balance on a specific day and want to recalculate the rest
    of the month.

    Workflow:
    1. Solve the original plan to get baseline schedule
    2. Lock days 1 through current_day to the baseline
    3. Add manual adjustment to hit the current_eod_balance exactly
    4. Re-solve days current_day+1 through 30

    Args:
        original_plan: The original full-month plan
        current_day: The day you're on (1-30)
        current_eod_balance: Your actual end-of-day balance in dollars
        solver: Solver to use ("auto", "dp", or "cpsat")
        **kwargs: Additional solver options

    Returns:
        Schedule for the full month with days 1-current_day locked and
        days current_day+1 to 30 re-optimized

    Example:
        >>> # You're on day 20 with $230 actual balance
        >>> new_schedule = adjust_from_day(plan, current_day=20, current_eod_balance=230.0)
        >>>
        >>> # Shows what you should do for days 21-30
        >>> print(f"Remaining work: {new_schedule.actions[20:]}")

    Raises:
        ValueError: If current_day not in valid range
        RuntimeError: If no feasible schedule exists for remaining days
    """
    if not (1 <= current_day <= 30):
        raise ValueError(f"current_day must be 1-30, got {current_day}")

    # Step 1: Solve baseline to get optimal schedule
    baseline_schedule = solve(original_plan, solver=solver, **kwargs)

    # Step 2: Create adjusted plan with locked prefix
    from copy import deepcopy
    adjusted_plan = deepcopy(original_plan)

    # Lock days 1 through current_day to baseline
    adjusted_plan.actions = baseline_schedule.actions[:current_day] + [None] * (30 - current_day)

    # Step 3: Calculate adjustment needed
    # What balance would we have on current_day with baseline schedule?
    baseline_eod = baseline_schedule.ledger[current_day - 1].closing_cents
    target_eod = to_cents(current_eod_balance)
    adjustment_needed = target_eod - baseline_eod

    # Add manual adjustment on current_day to hit target EOD exactly
    adjusted_plan.manual_adjustments.append(
        Adjustment(
            day=current_day,
            amount_cents=adjustment_needed,
            note=f"Actual EOD balance on day {current_day}: ${current_eod_balance:.2f}"
        )
    )

    # Step 4: Re-solve with locked prefix and adjustment
    new_schedule = solve(adjusted_plan, solver=solver, **kwargs)

    return new_schedule


def solve(plan: Plan, solver: str = "auto", **kwargs: Any) -> Schedule:
    """
    Unified solve function with automatic solver selection.

    This is the primary entry point for solving cashflow schedules. By default,
    it attempts to use CP-SAT (if OR-Tools is available) and falls back to DP
    if CP-SAT is unavailable or fails.

    Args:
        plan: The cashflow plan to solve
        solver: Solver selection - one of:
            - "auto" (default): Try CP-SAT with DP fallback
            - "dp": Use DP solver only
            - "cpsat": Use CP-SAT only (raises error if unavailable)
        **kwargs: Additional solver-specific options
            - For CP-SAT: options (CPSATSolveOptions), dp_fallback (bool)
            - For DP: forbid_large_after_day1 (bool)

    Returns:
        Schedule object with optimal solution containing:
            - actions: 30-day sequence of "O" (off) or "Spark" (work)
            - objective: (workdays, back_to_back_pairs, abs_diff_from_target)
            - final_closing_cents: Final balance on Day 30
            - ledger: Daily ledger entries

    Raises:
        RuntimeError: If solver fails or no feasible solution exists
        ValueError: If unknown solver specified

    Example:
        >>> schedule = solve(plan)  # Auto-select solver
        >>> schedule = solve(plan, solver="dp")  # Force DP
        >>> schedule = solve(plan, solver="cpsat", dp_fallback=False)  # CP-SAT only
    """
    if solver == "auto":
        # Try CP-SAT first, fall back to DP if OR-Tools unavailable
        return cpsat_solver.solve(plan, dp_fallback=True, **kwargs)
    elif solver == "dp":
        return dp_solver.solve(plan, **kwargs)
    elif solver == "cpsat":
        return cpsat_solver.solve(plan, dp_fallback=False, **kwargs)
    else:
        raise ValueError(
            f"Unknown solver: {solver!r}. "
            f"Must be one of: 'auto', 'dp', 'cpsat'"
        )


__all__ = [
    # Main solve functions
    "solve",
    "adjust_from_day",
    # Data models
    "Plan",
    "Schedule",
    "Bill",
    "Deposit",
    "Adjustment",
    "DayLedger",
    # Utilities
    "to_cents",
    "cents_to_str",
    "build_ledger",
    "validate",
    "ValidationReport",
    # Constants
    "SHIFT_NET_CENTS",
    # Solver modules (for advanced usage)
    "dp_solver",
    "cpsat_solver",
]
