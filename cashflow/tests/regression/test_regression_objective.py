from cashflow.io.store import load_plan
from cashflow.engines.dp import solve


def test_regression_objective_and_final():
    plan = load_plan("plan.json")
    s1 = solve(plan)
    s2 = solve(plan)

    # Deterministic
    assert s1.actions == s2.actions
    assert s1.objective == s2.objective
    assert s1.final_closing_cents == s2.final_closing_cents

    # Lock current baseline (update if solver logic changes intentionally)
    # Updated to restore b2b minimization for workday spreading
    assert s1.objective == (12, 0, 4847)
    assert s1.final_closing_cents == 4203
