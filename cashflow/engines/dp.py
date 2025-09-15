from __future__ import annotations

from dataclasses import dataclass
from copy import deepcopy
from typing import Dict, List, Optional, Tuple

from ..core.model import (
    Plan,
    Schedule,
    SHIFT_NET_CENTS,
    build_prefix_arrays,
    pre_rent_base_on_day30,
)
from ..core.ledger import build_ledger


Action = str  # 'O' or 'Spark'


@dataclass
class _StateVal:
    # costs that are additive across days
    b2b: int
    back: Optional[Tuple]  # (prev_state_key, action)


def _allowed_actions(
    day: int, locked: Optional[str], forbid_large_after_day1: bool
) -> List[Action]:
    if locked is not None:
        return [locked]
    if day == 1:
        return ["Spark"]
    if forbid_large_after_day1:
        # Legacy flag name; with Spark-only model, interpret as forbidding
        # additional workdays after Day 1.
        return ["O"]
    return ["O", "Spark"]


def _has_off_off(vec: List[int]) -> bool:
    for i in range(len(vec) - 1):
        if vec[i] == 1 and vec[i + 1] == 1:
            return True
    return False


def solve(plan: Plan, *, forbid_large_after_day1: bool = False) -> Schedule:
    dep, bills, base = build_prefix_arrays(plan)

    # Precompute global net bounds for pruning
    base_end = base[30]
    min_net = (plan.target_end_cents - plan.band_cents) - base_end
    max_net = (plan.target_end_cents + plan.band_cents) - base_end
    # Max per remaining day (derived from available actions)
    MAX_DAY_NET = max(SHIFT_NET_CENTS.values())

    pre30 = pre_rent_base_on_day30(plan, dep, bills)

    # DP layers: dict[state_key] = _StateVal
    # State key: (last6_off_tuple, prevWorked:int, workUsed:int, net:int)
    # last6_off_tuple: tuple[int,...] oldest->newest, len<=6
    layers: List[Dict[Tuple, _StateVal]] = []
    s0: Dict[Tuple, _StateVal] = {((), 0, 0, 0): _StateVal(b2b=0, back=None)}
    layers.append(s0)

    for day in range(1, 31):
        prev_layer = layers[-1]
        cur: Dict[Tuple, _StateVal] = {}

        for (last6_off, prevW, workUsed, net), val in prev_layer.items():
            last6_off_tuple: Tuple[int, ...] = last6_off if isinstance(last6_off, tuple) else tuple(last6_off)  # type: ignore

            locked = plan.actions[day - 1] if day - 1 < len(plan.actions) else None
            for a in _allowed_actions(day, locked, forbid_large_after_day1):
                will_work = 1 if a != "O" else 0
                work_used_new = workUsed + will_work

                net_new = net + SHIFT_NET_CENTS[a]

                # Prune by global net bounds and remaining capacity
                days_left = 30 - day
                if net_new > max_net:
                    continue
                if net_new + MAX_DAY_NET * days_left < min_net:
                    continue

                # Off-Off window check
                off_today = 1 if a == "O" else 0
                # Build 7-day window view for feasibility check (keep full 7)
                last7 = list(last6_off_tuple) + [off_today]
                if day >= 7:
                    if not _has_off_off(last7):
                        continue
                # Store last 6 bits for next state's memory (oldest dropped)
                last6_new = tuple(last7[-6:])

                # Balance feasibility for day t
                closing_t = base[day] + net_new
                if closing_t < 0:
                    continue
                # Day 30 pre-rent guard (before paying rent)
                if day == 30:
                    if pre30 + net_new < plan.rent_guard_cents:
                        continue

                # Update costs
                b2b_new = val.b2b + (1 if (prevW == 1 and will_work == 1) else 0)

                state_key = (last6_new, 1 if will_work else 0, work_used_new, net_new)
                new_val = _StateVal(
                    b2b=b2b_new,
                    back=((last6_off_tuple, prevW, workUsed, net), a),
                )

                # Keep lexicographically best by (work_used, b2b)
                existing = cur.get(state_key)
                if existing is None or (work_used_new, b2b_new) < (
                    work_used_new,
                    existing.b2b,
                ):
                    cur[state_key] = new_val

        layers.append(cur)

    # Select best final state within band
    best_tuple: Optional[Tuple[Tuple[int, int, int], Tuple, _StateVal]] = None
    for (last6_off, prevW, workUsed, net), val in layers[-1].items():
        final_closing = base[30] + net
        if not (
            plan.target_end_cents - plan.band_cents
            <= final_closing
            <= plan.target_end_cents + plan.band_cents
        ):
            continue
        abs_delta = abs(final_closing - plan.target_end_cents)
        obj = (workUsed, val.b2b, abs_delta)
        if best_tuple is None or obj < best_tuple[0]:
            best_tuple = (obj, (last6_off, prevW, workUsed, net), val)

    if best_tuple is None:
        raise RuntimeError("No feasible schedule found under constraints and band")

    objective, key, val = best_tuple

    # Reconstruct actions
    actions_rev: List[str] = []
    cur_key = key
    cur_val = val
    for day in range(30, 0, -1):
        prev = cur_val.back
        assert prev is not None
        prev_key, a = prev
        actions_rev.append(a)
        # Move up
        # Find the _StateVal for prev_key on previous layer to continue reconstruction
        # We can reconstruct using stored back-pointer chain only; val.back holds full information
        # Move to previous state's _StateVal by looking it up in the appropriate layer
        # day d corresponds to layer index d; previous is layer d-1
        # However we didn't store layers with mapping from key to val for all days except last.
        # To reconstruct reliably, keep following the stored chain in _StateVal.back which already provides prev_key and action.
        # We need the previous _StateVal to continue the chain; we can retrieve it by looking up in layers[day-1].
        cur_val = layers[day - 1][prev_key]
        cur_key = prev_key  # noqa: F841

    actions = list(reversed(actions_rev))

    ledger = build_ledger(plan, actions)
    final_closing = ledger[-1].closing_cents
    schedule = Schedule(
        actions=actions,
        objective=objective,
        final_closing_cents=final_closing,
        ledger=ledger,
    )
    return schedule


def solve_from(
    plan: Plan, start_day: int, *, forbid_large_after_day1: bool = False
) -> Schedule:
    """Solve with prefix [1..start_day-1] locked to the optimal baseline for `plan`,
    then re-solve the tail [start_day..30]. Convenience wrapper; currently locks
    actions and calls `solve()` rather than seeding state directly.
    """
    if not (1 <= start_day <= 30):
        raise ValueError("start_day must be in 1..30")
    if start_day == 1:
        return solve(plan, forbid_large_after_day1=forbid_large_after_day1)
    base = solve(plan, forbid_large_after_day1=forbid_large_after_day1)
    plan2 = deepcopy(plan)
    lock_upto = start_day - 1
    plan2.actions = base.actions[:lock_upto] + [None] * (30 - lock_upto)
    return solve(plan2, forbid_large_after_day1=forbid_large_after_day1)
