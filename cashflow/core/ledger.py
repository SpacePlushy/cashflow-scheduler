from __future__ import annotations

from typing import List

from .model import DayLedger, Plan, SHIFT_NET_CENTS, build_prefix_arrays


def build_ledger(plan: Plan, actions: List[str]) -> List[DayLedger]:
    dep, bills, base = build_prefix_arrays(plan)
    ledger: List[DayLedger] = []

    # opening for day t = base[t-1] + net_so_far
    net_so_far = 0
    for t in range(1, 31):
        opening = (plan.start_balance_cents + sum(dep[1:t]) - sum(bills[1:t])) + net_so_far
        a = actions[t - 1]
        net_today = SHIFT_NET_CENTS[a]
        closing = base[t] + net_so_far + net_today
        ledger.append(
            DayLedger(
                day=t,
                opening_cents=opening,
                deposit_cents=dep[t],
                action=a,
                net_cents=net_today,
                bills_cents=bills[t],
                closing_cents=closing,
            )
        )
        net_so_far += net_today
    return ledger

