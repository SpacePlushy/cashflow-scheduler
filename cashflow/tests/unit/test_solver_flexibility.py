from __future__ import annotations

from dataclasses import replace
from typing import List, Tuple

import pytest

from cashflow.io.store import load_plan
from cashflow.engines.cpsat import solve_with_diagnostics
from cashflow.core import model


def test_bill_amount_change_reflected_in_ledger():
    plan = load_plan("plan.json")
    baseline_schedule = solve_with_diagnostics(plan).schedule
    baseline_bill = baseline_schedule.ledger[0].bills_cents

    new_plan = load_plan("plan.json")
    first_bill = new_plan.bills[0]
    delta = -200
    updated_bill = first_bill.__class__(
        day=first_bill.day,
        name=first_bill.name,
        amount_cents=first_bill.amount_cents + delta,
    )
    new_plan.bills[0] = updated_bill
    new_plan.target_end_cents -= delta

    updated_schedule = solve_with_diagnostics(new_plan).schedule
    assert updated_schedule.ledger[0].bills_cents == baseline_bill + delta
    assert updated_schedule.final_closing_cents == baseline_schedule.final_closing_cents - delta


_BILL_CASES: List[Tuple[str, int, int, int]] = [
    ("auto_insurance_forward", 0, -500, 1),
    ("youtube_forward", 1, 200, 1),
    ("groceries_early", 2, 1000, -1),
    ("paramount_later", 4, -200, 2),
    ("streaming_to_day11", 6, 300, 1),
    ("electric_to_day24", 18, -400, -1),
]


@pytest.mark.parametrize(
    "_case_id, bill_index, amount_delta, day_delta",
    _BILL_CASES,
    ids=[case[0] for case in _BILL_CASES],
)
def test_specific_bill_adjustments(_case_id, bill_index: int, amount_delta: int, day_delta: int):
    plan = load_plan("plan.json")
    original_bill = plan.bills[bill_index]
    assert 1 <= original_bill.day + day_delta <= 30
    assert original_bill.amount_cents + amount_delta > 0

    new_day = original_bill.day + day_delta
    new_amount = original_bill.amount_cents + amount_delta
    plan.bills[bill_index] = replace(original_bill, day=new_day, amount_cents=new_amount)
    if amount_delta > 0:
        plan.target_end_cents -= amount_delta

    schedule = solve_with_diagnostics(plan).schedule

    expected_new_day_total = sum(b.amount_cents for b in plan.bills if b.day == new_day)
    expected_old_day_total = sum(b.amount_cents for b in plan.bills if b.day == original_bill.day)

    assert schedule.ledger[new_day - 1].bills_cents == expected_new_day_total
    assert schedule.ledger[original_bill.day - 1].bills_cents == expected_old_day_total
    assert abs(schedule.final_closing_cents - plan.target_end_cents) <= plan.band_cents


def test_shift_pay_rate_change_adjusts_final_balance(monkeypatch):
    plan = load_plan("plan.json")
    baseline_schedule = solve_with_diagnostics(plan).schedule
    baseline = baseline_schedule.final_closing_cents

    original_large = model.SHIFT_NET_CENTS["L"]
    delta = 500
    monkeypatch.setitem(model.SHIFT_NET_CENTS, "L", original_large + delta)

    adjusted_plan = load_plan("plan.json")
    l_days = baseline_schedule.actions.count("L")
    adjusted_plan.target_end_cents += l_days * delta

    lowered_schedule = solve_with_diagnostics(adjusted_plan).schedule
    l_days = baseline_schedule.actions.count("L")
    assert lowered_schedule.actions.count("L") == l_days
    assert lowered_schedule.final_closing_cents == baseline + l_days * delta


def test_locked_actions_respected():
    plan = load_plan("plan.json")
    plan.actions[5] = "SS"
    schedule = solve_with_diagnostics(plan).schedule
    assert schedule.actions[5] == "SS"
