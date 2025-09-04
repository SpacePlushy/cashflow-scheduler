from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..core.model import Bill, Deposit, Plan, to_cents, Adjustment


def load_plan(path: str | Path) -> Plan:
    p = Path(path)
    data = json.loads(p.read_text())

    deposits = [Deposit(day=int(d["day"]), amount_cents=to_cents(d["amount"])) for d in data.get("deposits", [])]
    bills = [
        Bill(day=int(b["day"]), name=str(b["name"]), amount_cents=to_cents(b["amount"]))
        for b in data.get("bills", [])
    ]
    actions = data.get("actions", [None] * 30)
    if len(actions) != 30:
        raise ValueError("actions must be length 30")

    # manual adjustments
    man_adj_data = data.get("manual_adjustments", [])
    manual_adjustments = []
    for a in man_adj_data:
        manual_adjustments.append(
            Adjustment(day=int(a["day"]), amount_cents=to_cents(a["amount"]), note=str(a.get("note", "")))
        )

    plan = Plan(
        start_balance_cents=to_cents(data["start_balance"]),
        target_end_cents=to_cents(data["target_end"]),
        band_cents=to_cents(data["band"]),
        rent_guard_cents=to_cents(data["rent_guard"]),
        deposits=deposits,
        bills=bills,
        actions=actions,  # type: ignore
        manual_adjustments=manual_adjustments,
        locks=[],
        metadata=dict(data.get("metadata", {})),
    )
    return plan
