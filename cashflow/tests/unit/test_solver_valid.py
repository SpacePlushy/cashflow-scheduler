from pathlib import Path

from cashflow.io.store import load_plan
from cashflow.engines.dp import solve
from cashflow.core.validate import validate


def test_dp_produces_valid_schedule(tmp_path: Path):
    plan_path = Path.cwd() / "plan.json"
    plan = load_plan(plan_path)
    schedule = solve(plan)
    report = validate(plan, schedule)
    assert report.ok, report.checks

