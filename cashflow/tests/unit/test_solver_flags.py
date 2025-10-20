from __future__ import annotations

import pytest

from cashflow.io.store import load_plan
from cashflow.engines import cpsat
from cashflow.engines.cpsat import solve_with_diagnostics
from cashflow.engines.dp import solve as dp_solve


@pytest.fixture(scope="module")
def sample_plan():
    return load_plan("plan.json")


def test_cpsat_matches_dp_objective(sample_plan):
    result = solve_with_diagnostics(sample_plan)
    dp_schedule = dp_solve(sample_plan)

    assert result.schedule.objective == dp_schedule.objective
    assert result.schedule.final_closing_cents == dp_schedule.final_closing_cents
    # 2 statuses for 2-part lexicographic objective (workdays, |Δ|)
    assert len(result.statuses) == 2


def test_cpsat_fallback_to_dp(monkeypatch, sample_plan):
    monkeypatch.setattr(cpsat, "cp_model", None)
    result = solve_with_diagnostics(sample_plan)
    assert result.solver == "dp"
    assert result.fallback_reason is not None
