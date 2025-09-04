from cashflow.io.store import load_plan
from cashflow.engines.dp import solve
from cashflow.core.ledger import build_ledger
from cashflow.core.model import build_prefix_arrays, SHIFT_NET_CENTS


def test_prefix_and_ledger_consistency():
    plan = load_plan("plan.json")
    schedule = solve(plan)
    dep, bills, base = build_prefix_arrays(plan)
    ledger = build_ledger(plan, schedule.actions)

    # Final closing equals base[30] + sum(net)
    net_total = sum(SHIFT_NET_CENTS[a] for a in schedule.actions)
    assert ledger[-1].closing_cents == base[30] + net_total

    # Opening/closing consistency per day
    net_so_far = 0
    for t, row in enumerate(ledger, start=1):
        # opening_t = start + sum(dep[1..t-1]) - sum(bills[1..t-1]) + net_so_far
        opening_expected = (
            plan.start_balance_cents + sum(dep[1:t]) - sum(bills[1:t])
        ) + net_so_far
        assert row.opening_cents == opening_expected
        net_so_far += row.net_cents
