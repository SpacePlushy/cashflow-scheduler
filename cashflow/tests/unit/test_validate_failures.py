from cashflow.core.model import Plan, Schedule, DayLedger
from cashflow.core.validate import validate


def test_validate_detects_rule_failures():
    plan = Plan(
        start_balance_cents=0,
        target_end_cents=10_000,
        band_cents=500,
        rent_guard_cents=200_000,
        deposits=[],
        bills=[],
        actions=[None] * 30,
        manual_adjustments=[],
        locks=[],
        metadata={"case": "invalid"},
    )

    actions = ["S"] * 30  # Violates Day-1 Large requirement and Off-Off rule
    ledger = []
    balance = 0
    for day in range(1, 31):
        opening = balance
        net = 0
        closing = opening
        if day == 5:
            closing = -100  # violates non-negative balances
        if day == 30:
            closing = 500  # outside target band
        ledger.append(
            DayLedger(
                day=day,
                opening_cents=opening,
                deposit_cents=0,
                action=actions[day - 1],
                net_cents=net,
                bills_cents=0,
                closing_cents=closing,
            )
        )
        balance = closing

    schedule = Schedule(
        actions=actions,
        objective=(0, 0, 0, 0, 0),
        final_closing_cents=ledger[-1].closing_cents,
        ledger=ledger,
    )

    report = validate(plan, schedule)
    assert not report.ok
    results = {name: (ok, detail) for name, ok, detail in report.checks}

    assert results["Day 1 Large"] == (False, "S")
    assert results["Non-negative balances"][0] is False
    assert results["Final within band"][0] is False
    assert results["Day-30 pre-rent guard"][0] is False
    assert results["7-day Off,Off present"][0] is False
