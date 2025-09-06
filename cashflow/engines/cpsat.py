from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Tuple

try:
    from ortools.sat.python import cp_model
except Exception:  # pragma: no cover - optional dependency
    cp_model = None  # type: ignore

from ..core.model import (
    SHIFT_NET_CENTS,
    Plan,
    build_prefix_arrays,
    pre_rent_base_on_day30,
)


ActionList = ["O", "S", "M", "L", "SS"]
ACTIONS = ("O", "S", "M", "L", "SS")
IDX: Dict[str, int] = {a: i for i, a in enumerate(ACTIONS)}


@dataclass
class CPSATSolution:
    actions: List[str]
    objective: Tuple[int, int, int, int, int]
    final_closing_cents: int


@dataclass
class VerificationReport:
    ok: bool
    dp_obj: Tuple[int, int, int, int, int]
    cp_obj: Tuple[int, int, int, int, int]
    dp_actions: List[str]
    cp_actions: List[str]
    detail: str = ""


def _build_model(plan: Plan):
    assert cp_model is not None, "OR-Tools CP-SAT not available"

    dep, bills, base = build_prefix_arrays(plan)
    pre30 = pre_rent_base_on_day30(plan, dep, bills)

    model = cp_model.CpModel()

    # Decision vars
    x = [[model.NewBoolVar(f"x_{t}_{a}") for a in range(5)] for t in range(30)]
    off = [model.NewBoolVar(f"off_{t}") for t in range(30)]
    w = [model.NewBoolVar(f"w_{t}") for t in range(30)]
    b2b = [model.NewBoolVar(f"b2b_{t}") for t in range(29)]
    oo = [model.NewBoolVar(f"oo_{t}") for t in range(29)]
    prefix_net = [model.NewIntVar(0, 12000 * (t + 1), f"pref_{t}") for t in range(30)]
    final_close = model.NewIntVar(-(10**9), 10**9, "final_close")
    abs_diff = model.NewIntVar(0, 10**9, "abs_diff")

    # One-hot and lock handling
    for t in range(30):
        model.Add(sum(x[t]) == 1)
        # Locks via plan.actions
        locked = plan.actions[t]
        if locked is not None:
            for a in range(5):
                model.Add(x[t][a] == (1 if a == IDX[locked] else 0))

    # Day 1 Large
    model.Add(x[0][IDX["L"]] == 1)

    # off, w
    for t in range(30):
        model.Add(off[t] == x[t][IDX["O"]])
        # w = 1 - off
        model.Add(w[t] + off[t] == 1)

    # b2b linearization
    for t in range(29):
        model.Add(b2b[t] <= w[t])
        model.Add(b2b[t] <= w[t + 1])
        model.Add(b2b[t] >= w[t] + w[t + 1] - 1)

    # oo (off-off) linearization
    for t in range(29):
        model.Add(oo[t] <= off[t])
        model.Add(oo[t] <= off[t + 1])
        model.Add(oo[t] >= off[t] + off[t + 1] - 1)

    # Prefix net recursion
    net_vec = [SHIFT_NET_CENTS[a] for a in ACTIONS]
    # day 0
    model.Add(prefix_net[0] == sum(net_vec[a] * x[0][a] for a in range(5)))
    for t in range(1, 30):
        model.Add(
            prefix_net[t]
            == prefix_net[t - 1] + sum(net_vec[a] * x[t][a] for a in range(5))
        )

    # Non-negative daily closings
    for t in range(30):
        model.Add(base[t + 1] + prefix_net[t] >= 0)

    # Day 30 pre-rent guard
    model.Add(pre30 + prefix_net[29] >= plan.rent_guard_cents)

    # Final closing within band and |diff|
    model.Add(final_close == base[30] + prefix_net[29])
    model.Add(final_close >= plan.target_end_cents - plan.band_cents)
    model.Add(final_close <= plan.target_end_cents + plan.band_cents)
    model.AddAbsEquality(abs_diff, final_close - plan.target_end_cents)

    # Off-Off window rule: For each 7-day window s..s+6, sum oo[i] >= 1
    for s in range(0, 24):
        model.Add(sum(oo[i] for i in range(s, s + 6)) >= 1)

    # Objective components
    workdays = sum(w)
    b2b_sum = sum(b2b)
    large_days = sum(x[t][IDX["L"]] for t in range(30))
    single_pen = sum(x[t][IDX["M"]] + 2 * x[t][IDX["L"]] for t in range(30))

    return model, x, (workdays, b2b_sum, abs_diff, large_days, single_pen), final_close


def enumerate_ties(plan: Plan, limit: int = 5) -> List[CPSATSolution]:
    """Enumerate up to `limit` alternative action sequences with the same optimal
    lexicographic objective using CP-SAT solution enumeration.

    Requires OR-Tools. Returns a (possibly empty) list including the baseline solution.
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

    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = 10.0
    solver.parameters.num_search_workers = 8
    solver.SearchForAllSolutions(model, Collector())
    return sols


def _solve_sequential_lex(model, obj_parts, solver: "cp_model.CpSolver"):
    workdays, b2b_sum, abs_diff, large_days, single_pen = obj_parts

    # 1) Minimize workdays
    model.Minimize(workdays)
    solver.parameters.max_time_in_seconds = 10.0
    solver.parameters.num_search_workers = 8
    r = solver.Solve(model)
    if r not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        raise RuntimeError("CP-SAT failed to find a solution for objective 1")
    best_work = solver.Value(workdays)
    model.Add(workdays == best_work)

    # 2) Minimize b2b
    model.Minimize(b2b_sum)
    r = solver.Solve(model)
    if r not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        raise RuntimeError("CP-SAT failed for objective 2")
    best_b2b = solver.Value(b2b_sum)
    model.Add(b2b_sum == best_b2b)

    # 3) Minimize abs_diff
    model.Minimize(abs_diff)
    r = solver.Solve(model)
    if r not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        raise RuntimeError("CP-SAT failed for objective 3")
    best_abs = solver.Value(abs_diff)
    model.Add(abs_diff == best_abs)

    # 4) Minimize large_days
    model.Minimize(large_days)
    r = solver.Solve(model)
    if r not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        raise RuntimeError("CP-SAT failed for objective 4")
    best_large = solver.Value(large_days)
    model.Add(large_days == best_large)

    # 5) Minimize single_pen
    model.Minimize(single_pen)
    r = solver.Solve(model)
    if r not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        raise RuntimeError("CP-SAT failed for objective 5")

    return best_work, best_b2b, best_abs, best_large, solver.Value(single_pen)


def solve_lex(plan: Plan) -> CPSATSolution:
    if cp_model is None:
        raise RuntimeError("OR-Tools CP-SAT not installed")

    model, x, obj_parts, final_close = _build_model(plan)
    solver = cp_model.CpSolver()
    w, b2b, absd, large, sp = _solve_sequential_lex(model, obj_parts, solver)

    # Extract actions
    actions: List[str] = []
    for t in range(30):
        idx = None
        for a in range(5):
            if solver.Value(x[t][a]) == 1:
                idx = a
                break
        assert idx is not None
        actions.append(ACTIONS[idx])

    final_cents = solver.Value(final_close)
    sol = CPSATSolution(
        actions=actions,
        objective=(w, b2b, absd, large, sp),
        final_closing_cents=final_cents,
    )
    return sol


def verify_lex_optimal(plan: Plan, schedule_dp) -> VerificationReport:
    """Run CP-SAT sequential lex optimization and compare to DP schedule."""
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
    )
