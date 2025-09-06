"""
CP-SAT verification and tie-enumeration engine.

This module builds a constraint programming model in OR-Tools CP-SAT that
captures the same feasibility rules and objective used by the DP solver. It is
used to:

- Solve a sequential lexicographic objective (workdays, back-to-back work,
  |final diff|, number of large days, and a final single-day penalty) and
  extract an optimal 30-day schedule.
- Cross-check a DP-produced schedule for lexicographic optimality.
- Enumerate alternative schedules ("ties") that achieve the exact same
  lexicographic objective value.

Key ideas:
- One-hot action variable per day over ACTIONS = ("O","S","M","L","SS").
- Derived boolean indicators for off/work, back-to-back work pairs, and
  off-off pairs in adjacent days.
- Integer prefix balance recursion over net cents deltas per action.
- Feasibility constraints mirror validator rules: non-negative daily closings,
  Day-1 Large, Day-30 pre-rent guard, final band, and an Off-Off window rule.
- Sequential lexicographic optimization modeled by solving 5 stages in order
  and fixing the previous objective part to its optimum before proceeding.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Tuple, Optional

try:
    # Optional dependency: the rest of the repo (DP engine, CLI, tests) can run
    # without OR-Tools installed. We guard imports and raise clear errors only
    # when CP-SAT specific functions are invoked.
    from ortools.sat.python import cp_model
except Exception:  # pragma: no cover - optional dependency
    cp_model = None  # type: ignore

from ..core.model import (
    SHIFT_NET_CENTS,
    Plan,
    build_prefix_arrays,
    pre_rent_base_on_day30,
)

# Notes on core.model imports:
# - Plan: input data class describing the month, target band, rent guard, and
#   optional per-day action locks. Only a subset of fields is used here.
# - SHIFT_NET_CENTS: mapping from action symbol (e.g., "M") to integer cents
#   representing the net cash delta contributed by performing that action on a
#   given day.
# - build_prefix_arrays(plan): returns deterministic base arrays (deposit/bill
#   prefixes and a combined base trajectory) against which dynamic action
#   deltas are added to compute daily closings.
# - pre_rent_base_on_day30(...): extracts the deterministic amount relevant to
#   the Day-30 pre-rent guard (i.e., the base part of the balance before
#   applying action deltas on or before Day-30).


ActionList = ["O", "S", "M", "L", "SS"]
# Canonical action order used to index decision variables. This order must
# match how SHIFT_NET_CENTS is accessed below.
ACTIONS = ("O", "S", "M", "L", "SS")
IDX: Dict[str, int] = {a: i for i, a in enumerate(ACTIONS)}


@dataclass
class CPSATSolution:
    """Container for a CP-SAT schedule and its objective components.

    - actions: the chosen action symbol per day (length 30)
    - objective: 5-tuple in lexicographic order
    - final_closing_cents: closing balance on Day-30
    - statuses: per-stage CP-SAT status names during lex solve
    """

    actions: List[str]
    objective: Tuple[int, int, int, int, int]
    final_closing_cents: int
    statuses: List[str]


@dataclass
class VerificationReport:
    """Result of verifying a DP schedule with CP-SAT.

    If OR-Tools is unavailable or CP-SAT fails, `ok` is False and `detail`
    describes the error; otherwise `ok` reflects whether the DP objective
    matches the CP-SAT lexicographic optimum.
    """

    ok: bool
    dp_obj: Tuple[int, int, int, int, int]
    cp_obj: Tuple[int, int, int, int, int]
    dp_actions: List[str]
    cp_actions: List[str]
    detail: str = ""
    statuses: Optional[List[str]] = None


def _build_model(plan: Plan):
    """Construct the CP-SAT model for a given `plan`.

    Returns: (model, x, obj_parts, final_close)
    - model: cp_model.CpModel
    - x: shape (30,5) list of BoolVar (one-hot actions per day)
    - obj_parts: tuple of IntVar/LinearExpr for objective parts
    - final_close: IntVar for final closing balance

    Notes on inputs from core.model:
    - build_prefix_arrays(plan) -> (dep, bills, base): cumulative arrays used to
      express daily closing balances; `base[t+1] + prefix_net[t]` is the closing
      balance on day t.
    - pre_rent_base_on_day30(plan, dep, bills): base amount for the pre-rent
      guard constraint on Day-30.
    """
    assert cp_model is not None, "OR-Tools CP-SAT not available"

    dep, bills, base = build_prefix_arrays(plan)
    # `base` is a length-31 vector of deterministic cents; `dep` and `bills`
    # are cumulative prefixes of deposits and bills. The dynamic part comes
    # from action deltas accumulated into `prefix_net` below.
    pre30 = pre_rent_base_on_day30(plan, dep, bills)

    model = cp_model.CpModel()

    # Decision vars
    # x[t][a] == 1 iff action `ACTIONS[a]` is chosen on day t.
    x = [[model.NewBoolVar(f"x_{t}_{a}") for a in range(5)] for t in range(30)]
    off = [model.NewBoolVar(f"off_{t}") for t in range(30)]
    w = [model.NewBoolVar(f"w_{t}") for t in range(30)]
    # Adjacent-pair indicators for (work,work) and (off,off).
    b2b = [model.NewBoolVar(f"b2b_{t}") for t in range(29)]
    oo = [model.NewBoolVar(f"oo_{t}") for t in range(29)]
    # Cumulative sum of action deltas (in cents) up to day t.
    # Upper bound is a safe coarse cap to keep domains finite.
    prefix_net = [model.NewIntVar(0, 12000 * (t + 1), f"pref_{t}") for t in range(30)]
    final_close = model.NewIntVar(-(10**9), 10**9, "final_close")
    abs_diff = model.NewIntVar(0, 10**9, "abs_diff")

    # Rationale for domains:
    # - prefix_net: coarse upper bounds (12k per day) are conservative but
    #   avoid needless search by preventing unbounded growth; lower bound 0 is
    #   consistent with non-negative or zero net deltas in SHIFT_NET_CENTS.
    # - final_close: wide bounds; we subsequently constrain it to the target
    #   band, which effectively tightens its domain during solving.
    # - abs_diff: non-negative absolute deviation, linked via AddAbsEquality.

    # One-hot and lock handling
    for t in range(30):
        # Exactly one action chosen per day.
        model.Add(sum(x[t]) == 1)
        # Locks via plan.actions: if a day is pre-fixed, force its one-hot.
        # This is how users can "pin" certain days when exploring schedules.
        locked = plan.actions[t]
        if locked is not None:
            for a in range(5):
                model.Add(x[t][a] == (1 if a == IDX[locked] else 0))

    # Day 1 Large
    # Business rule: the first day must be a Large shift. This mirrors the
    # validator and DP solver’s model assumptions.
    model.Add(x[0][IDX["L"]] == 1)

    # off, w
    for t in range(30):
        model.Add(off[t] == x[t][IDX["O"]])
        # w is the boolean negation of off (work if not off).
        model.Add(w[t] + off[t] == 1)

    # b2b linearization
    for t in range(29):
        # b2b[t] = AND(w[t], w[t+1]) using standard linearization:
        # b2b <= w_t, b2b <= w_t+1, b2b >= w_t + w_t+1 - 1
        model.Add(b2b[t] <= w[t])
        model.Add(b2b[t] <= w[t + 1])
        model.Add(b2b[t] >= w[t] + w[t + 1] - 1)

    # oo (off-off) linearization
    for t in range(29):
        # oo[t] = AND(off[t], off[t+1])
        model.Add(oo[t] <= off[t])
        model.Add(oo[t] <= off[t + 1])
        model.Add(oo[t] >= off[t] + off[t + 1] - 1)

    # Prefix net recursion
    # Map actions to per-day net cents deltas.
    net_vec = [SHIFT_NET_CENTS[a] for a in ACTIONS]
    # day 0
    model.Add(prefix_net[0] == sum(net_vec[a] * x[0][a] for a in range(5)))
    for t in range(1, 30):
        # prefix_net[t] = prefix_net[t-1] + net(action_t)
        model.Add(
            prefix_net[t]
            == prefix_net[t - 1] + sum(net_vec[a] * x[t][a] for a in range(5))
        )
    # With base[] provided by build_prefix_arrays, the closing balance on day t
    # is base[t+1] + prefix_net[t]. The constraints below enforce feasibility.

    # Non-negative daily closings
    for t in range(30):
        # Closing balance at day t is base[t+1] + prefix_net[t]; enforce >= 0.
        model.Add(base[t + 1] + prefix_net[t] >= 0)

    # Day 30 pre-rent guard
    # Ensure enough cash prior to rent: base part + dynamic deltas >= guard.
    model.Add(pre30 + prefix_net[29] >= plan.rent_guard_cents)

    # Final closing within band and |diff|
    model.Add(final_close == base[30] + prefix_net[29])
    model.Add(final_close >= plan.target_end_cents - plan.band_cents)
    model.Add(final_close <= plan.target_end_cents + plan.band_cents)
    # abs_diff = |final_close - target|
    model.AddAbsEquality(abs_diff, final_close - plan.target_end_cents)

    # Off-Off window rule: For each 7-day window s..s+6, sum oo[i] >= 1
    for s in range(0, 24):
        # Each 7-day window contains 6 adjacent pairs; require at least one
        # off-off adjacent pair within the window.
        model.Add(sum(oo[i] for i in range(s, s + 6)) >= 1)

    # Objective components
    # We optimize lexicographically over these five parts (in order):
    # 1) Minimize total workdays; 2) minimize back-to-back work pairs;
    # 3) minimize |final diff from target|; 4) minimize number of Large days;
    # 5) minimize a tie-breaker penalizing M and especially L.
    workdays = sum(w)
    b2b_sum = sum(b2b)
    large_days = sum(x[t][IDX["L"]] for t in range(30))
    single_pen = sum(x[t][IDX["M"]] + 2 * x[t][IDX["L"]] for t in range(30))
    # Notes:
    # - workdays: encourages more off days when feasible.
    # - b2b_sum: discourages consecutive working days to spread work out.
    # - abs_diff: centers final balance within the target band with a preference
    #   toward the target itself when multiple values lie within the band.
    # - large_days: prefers fewer Large shifts after satisfying (1)-(3).
    # - single_pen: final tie-breaker to prefer Medium over Large, and avoid
    #   unnecessary Mediums as well.

    return model, x, (workdays, b2b_sum, abs_diff, large_days, single_pen), final_close


def enumerate_ties(plan: Plan, limit: int = 5) -> List[CPSATSolution]:
    """Enumerate alternative schedules with the same optimal objective.

    Procedure:
    1) Run sequential lex optimization to obtain the optimal objective vector.
    2) Re-build the model and fix each objective part to that optimal value.
    3) Drop the objective and enumerate distinct feasible action sequences
       using a `CpSolverSolutionCallback`, stopping after `limit` solutions.

    Returns a list possibly including the baseline schedule; list may be empty
    if no solution is found within the time limit.
    """
    if cp_model is None:  # pragma: no cover - optional dependency
        raise RuntimeError("OR-Tools CP-SAT not installed")

    # First, get the optimal objective via sequential lex optimization
    model_opt, x_opt, obj_parts, final_close_opt = _build_model(plan)
    solver_opt = cp_model.CpSolver()
    w, b2b, absd, large, sp = _solve_sequential_lex(model_opt, obj_parts, solver_opt)

    # Build a fresh model with the same constraints and fix the objective parts to the optimal values
    model, x, obj_parts2, final_close = _build_model(plan)
    workdays, b2b_sum, abs_diff, large_days, single_pen = obj_parts2
    model.Add(workdays == w)
    model.Add(b2b_sum == b2b)
    model.Add(abs_diff == absd)
    model.Add(large_days == large)
    model.Add(single_pen == sp)

    # Enumerate feasible solutions (no objective)
    sols: List[CPSATSolution] = []

    class Collector(cp_model.CpSolverSolutionCallback):  # type: ignore
        def __init__(self):
            super().__init__()
            self._seen = set()

        def on_solution_callback(self):  # type: ignore
            if len(sols) >= limit:
                self.StopSearch()
                return
            actions: List[str] = []
            for t in range(30):
                idx = None
                for a in range(5):
                    if self.Value(x[t][a]) == 1:
                        idx = a
                        break
                assert idx is not None
                actions.append(ACTIONS[idx])
            key = tuple(actions)
            if key in self._seen:
                return
            self._seen.add(key)
            final_cents = self.Value(final_close)
            sols.append(
                CPSATSolution(
                    actions=actions,
                    objective=(w, b2b, absd, large, sp),
                    final_closing_cents=final_cents,
                )
            )
            # Note: We do not record solver status per enumerated solution here;
            # instead, `statuses` are captured during the lex run that fixed the
            # objective parts. Enumeration purely explores equal-optimum ties.

    solver = cp_model.CpSolver()
    # Mild time cap and multi-threading for enumeration.
    # If your ties are numerous, consider raising the time or lowering
    # `num_search_workers` for determinism.
    solver.parameters.max_time_in_seconds = 10.0
    solver.parameters.num_search_workers = 8
    solver.SearchForAllSolutions(model, Collector())
    return sols


def _status_name(code: object) -> str:
    """Map a CP-SAT status code to a human-readable string."""
    try:
        if code == cp_model.OPTIMAL:
            return "OPTIMAL"
        if code == cp_model.FEASIBLE:
            return "FEASIBLE"
        if code == cp_model.INFEASIBLE:
            return "INFEASIBLE"
        if code == cp_model.MODEL_INVALID:
            return "MODEL_INVALID"
        if code == cp_model.UNKNOWN:
            return "UNKNOWN"
    except Exception:
        pass
    return str(code)


def _solve_sequential_lex(model, obj_parts, solver: "cp_model.CpSolver"):
    """Solve a 5-part lexicographic objective sequentially.

    At each stage, minimize the current part, record the optimum, then add an
    equality constraint fixing that part before moving to the next. This is a
    standard technique to emulate lexicographic optimization with CP-SAT.
    Returns the optimal values for each part along with per-stage statuses.
    """
    workdays, b2b_sum, abs_diff, large_days, single_pen = obj_parts

    statuses: List[str] = []

    # 1) Minimize workdays
    model.Minimize(workdays)
    solver.parameters.max_time_in_seconds = 10.0
    solver.parameters.num_search_workers = 8
    r = solver.Solve(model)
    statuses.append(_status_name(r))
    if r not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        raise RuntimeError("CP-SAT failed to find a solution for objective 1")
    best_work = solver.Value(workdays)
    model.Add(workdays == best_work)

    # 2) Minimize b2b
    model.Minimize(b2b_sum)
    r = solver.Solve(model)
    statuses.append(_status_name(r))
    if r not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        raise RuntimeError("CP-SAT failed for objective 2")
    best_b2b = solver.Value(b2b_sum)
    model.Add(b2b_sum == best_b2b)

    # 3) Minimize abs_diff
    model.Minimize(abs_diff)
    r = solver.Solve(model)
    statuses.append(_status_name(r))
    if r not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        raise RuntimeError("CP-SAT failed for objective 3")
    best_abs = solver.Value(abs_diff)
    model.Add(abs_diff == best_abs)

    # 4) Minimize large_days
    model.Minimize(large_days)
    r = solver.Solve(model)
    statuses.append(_status_name(r))
    if r not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        raise RuntimeError("CP-SAT failed for objective 4")
    best_large = solver.Value(large_days)
    model.Add(large_days == best_large)

    # 5) Minimize single_pen (final tie-breaker among Large/Medium usage)
    model.Minimize(single_pen)
    r = solver.Solve(model)
    statuses.append(_status_name(r))
    if r not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        raise RuntimeError("CP-SAT failed for objective 5")

    return best_work, best_b2b, best_abs, best_large, solver.Value(single_pen), statuses


def solve_lex(plan: Plan) -> CPSATSolution:
    """Run CP-SAT sequential lex optimization and extract the schedule."""
    if cp_model is None:
        raise RuntimeError("OR-Tools CP-SAT not installed")

    model, x, obj_parts, final_close = _build_model(plan)
    solver = cp_model.CpSolver()
    w, b2b, absd, large, sp, statuses = _solve_sequential_lex(model, obj_parts, solver)

    # Extract actions from the solved one-hot variables.
    actions: List[str] = []
    for t in range(30):
        idx = None
        for a in range(5):
            if solver.Value(x[t][a]) == 1:
                idx = a
                break
        assert idx is not None
        actions.append(ACTIONS[idx])
    # `final_close` aligns with base[30] + prefix_net[29] due to the equality
    # constraint in _build_model. Reading it from the solver is sufficient.

    final_cents = solver.Value(final_close)
    sol = CPSATSolution(
        actions=actions,
        objective=(w, b2b, absd, large, sp),
        final_closing_cents=final_cents,
        statuses=statuses,
    )
    return sol


def verify_lex_optimal(plan: Plan, schedule_dp) -> VerificationReport:
    """Compare the DP schedule's objective to the CP-SAT optimum.

    Returns a `VerificationReport` with the CP-SAT objective, actions, and
    per-stage statuses. If OR-Tools is not available, the report explains why.
    """
    try:
        sol = solve_lex(plan)
    except Exception as e:  # pragma: no cover - dependent on OR-Tools
        return VerificationReport(
            ok=False,
            dp_obj=schedule_dp.objective,
            cp_obj=(-1, -1, -1, -1, -1),
            dp_actions=schedule_dp.actions,
            cp_actions=[],
            detail=f"CP-SAT error: {e}",
            statuses=[],
        )

    ok = sol.objective == schedule_dp.objective
    detail = "OK" if ok else "Mismatch between DP and CP-SAT objectives"
    return VerificationReport(
        ok=ok,
        dp_obj=schedule_dp.objective,
        cp_obj=sol.objective,
        dp_actions=schedule_dp.actions,
        cp_actions=sol.actions,
        detail=detail,
        statuses=sol.statuses,
    )
