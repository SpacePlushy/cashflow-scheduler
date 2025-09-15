from __future__ import annotations

from dataclasses import dataclass
from typing import List, Tuple

from .model import (
    Plan,
    Schedule,
    SHIFT_NET_CENTS,
    build_prefix_arrays,
    pre_rent_base_on_day30,
)


@dataclass
class ValidationReport:
    ok: bool
    checks: List[Tuple[str, bool, str]]  # (name, pass, detail)


def _has_off_off_last7(off_flags_7: List[int]) -> bool:
    for i in range(6):
        if off_flags_7[i] == 1 and off_flags_7[i + 1] == 1:
            return True
    return False


def validate(plan: Plan, schedule: Schedule) -> ValidationReport:
    dep, bills, base = build_prefix_arrays(plan)
    checks: List[Tuple[str, bool, str]] = []

    # Ensure every action is a known Spark code (O or SP)
    valid_actions = all(a in SHIFT_NET_CENTS for a in schedule.actions)
    detail = "{" + ",".join(sorted(set(schedule.actions))) + "}"
    checks.append(("Actions valid", valid_actions, detail))

    # Non-negativity & bills paid by construction
    nonneg_ok = True
    for t, ledger_row in enumerate(schedule.ledger, start=1):
        if ledger_row.closing_cents < 0:
            nonneg_ok = False
            break
    checks.append(("Non-negative balances", nonneg_ok, "closing>=0 for all t"))

    # Final day within band
    final = schedule.final_closing_cents
    lo = plan.target_end_cents - plan.band_cents
    hi = plan.target_end_cents + plan.band_cents
    band_ok = lo <= final <= hi
    checks.append(("Final within band", band_ok, f"{final} in [{lo},{hi}]"))

    # Day-30 pre-rent guard
    pre30 = pre_rent_base_on_day30(plan, dep, bills)
    net_total = sum(SHIFT_NET_CENTS[a] for a in schedule.actions)
    pre_rent_balance = pre30 + net_total
    rent_ok = pre_rent_balance >= plan.rent_guard_cents
    checks.append(
        (
            "Day-30 pre-rent guard",
            rent_ok,
            f"{pre_rent_balance}>= {plan.rent_guard_cents}",
        )
    )

    # Off-Off in each rolling 7-day window
    off = [1 if a == "O" else 0 for a in schedule.actions]
    off_ok = True
    for s in range(0, 24):
        window7 = off[s : s + 7]
        if not _has_off_off_last7(window7):
            off_ok = False
            break
    checks.append(("7-day Off,Off present", off_ok, "every 7-day window"))

    ok = all(p for _, p, _ in checks)
    return ValidationReport(ok=ok, checks=checks)
