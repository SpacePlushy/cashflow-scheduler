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
    assert s1.objective == (19, 11, 97, 3, 6)
    assert s1.final_closing_cents == 48953
