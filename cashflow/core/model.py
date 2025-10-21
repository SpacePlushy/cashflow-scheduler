from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP, InvalidOperation
from typing import Dict, List, Optional, Tuple

# Maximum monetary value: $10 million in cents (reasonable upper bound)
MAX_AMOUNT_CENTS = 1_000_000_000  # $10,000,000


# Money utils (integer cents only)
def to_cents(amount: float | int | str | Decimal) -> int:
    """Convert monetary amount to integer cents with overflow protection.

    Args:
        amount: Monetary value as float, int, string, or Decimal

    Returns:
        Integer cents value

    Raises:
        ValueError: If amount exceeds MAX_AMOUNT_CENTS or is invalid
    """
    try:
        d = Decimal(str(amount)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    except (InvalidOperation, ValueError) as e:
        raise ValueError(f"Invalid monetary amount: {amount}") from e

    cents = int(d * 100)

    # Check for overflow
    if abs(cents) > MAX_AMOUNT_CENTS:
        raise ValueError(
            f"Amount {amount} exceeds maximum allowed value "
            f"(${MAX_AMOUNT_CENTS / 100:,.2f})"
        )

    return cents


def cents_to_str(cents: int) -> str:
    sign = "-" if cents < 0 else ""
    cents_abs = abs(cents)
    return f"{sign}{cents_abs // 100}.{cents_abs % 100:02d}"


# Spark shift payouts (integer cents). Off days net to 0; each Spark workday
# deposits $100 with no deductions.
SHIFT_NET_CENTS: Dict[str, int] = {
    "O": 0,
    "Spark": 10_000,
}


@dataclass(frozen=True)
class Bill:
    day: int
    name: str
    amount_cents: int


@dataclass(frozen=True)
class Deposit:
    day: int
    amount_cents: int


@dataclass(frozen=True)
class Adjustment:
    day: int
    amount_cents: int
    note: str = ""


@dataclass
class Plan:
    start_balance_cents: int
    target_end_cents: int
    band_cents: int
    rent_guard_cents: int
    deposits: List[Deposit]
    bills: List[Bill]
    actions: List[Optional[str]]  # length 30, optional prefilled/locks
    manual_adjustments: List[Adjustment]
    locks: List[Tuple[int, int]]
    metadata: Dict[str, str]


@dataclass
class DayLedger:
    day: int
    opening_cents: int
    deposit_cents: int
    action: str
    net_cents: int
    bills_cents: int
    closing_cents: int


@dataclass
class Schedule:
    actions: List[str]  # 30 entries from {O,Spark}
    objective: Tuple[int, int, int]
    final_closing_cents: int
    ledger: List[DayLedger]


def build_prefix_arrays(plan: Plan) -> Tuple[List[int], List[int], List[int]]:
    """Return (deposit_by_day, bills_by_day, base_prefix)
    deposit_by_day[t]: total deposits on day t (1..30)
    bills_by_day[t]: total bills on day t (1..30)
    base_prefix[t]: start_balance + sum(deposits[1..t]) - sum(bills[1..t])
    """
    dep = [0] * 31
    bills = [0] * 31
    for d in plan.deposits:
        if 1 <= d.day <= 30:
            dep[d.day] += d.amount_cents
    # manual adjustments behave like deposits (can be negative)
    for adj in plan.manual_adjustments:
        if 1 <= adj.day <= 30:
            dep[adj.day] += adj.amount_cents
    for b in plan.bills:
        if 1 <= b.day <= 30:
            bills[b.day] += b.amount_cents
    base = [0] * 31
    running = plan.start_balance_cents
    for t in range(1, 31):
        running += dep[t]
        running -= bills[t]
        base[t] = running
    return dep, bills, base


def pre_rent_base_on_day30(
    plan: Plan, deposit_by_day: List[int], bills_by_day: List[int]
) -> int:
    # Pre-rent balance after deposits and shifts on Day 30 (before paying rent)
    # = start + sum(deposits[1..30]) - sum(bills[1..29])
    pre = plan.start_balance_cents + sum(deposit_by_day[1:31]) - sum(bills_by_day[1:30])
    return pre
