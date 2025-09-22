import json

from cashflow.io.store import load_plan
from cashflow.engines.cpsat import solve_with_diagnostics
from cashflow.io.render import render_markdown, render_csv, render_json


def test_render_helpers_cover_formats():
    plan = load_plan("plan.json")
    result = solve_with_diagnostics(plan)
    schedule = result.schedule

    markdown = render_markdown(schedule)
    assert "| Day | Opening | Action | Payout | Deposits | Bills | Closing |" in markdown
    assert "Objective: workdays=" in markdown
    assert "Final closing:" in markdown

    csv_text = render_csv(schedule)
    lines = csv_text.splitlines()
    assert lines[0] == "Day,Opening,Deposits,Action,Net,Bills,Closing"
    assert lines[1].startswith("1,")

    data = json.loads(render_json(schedule))
    assert data["actions"] == schedule.actions
    assert data["objective"] == list(schedule.objective)
    assert data["ledger"][0]["day"] == 1
