from __future__ import annotations

from typing import List

from ..core.model import Schedule, cents_to_str


def render_markdown(schedule: Schedule) -> str:
    lines: List[str] = []
    lines.append("| Day | Opening | Deposits | Action | Net | Bills | Closing |")
    lines.append("| ---:| -------:| --------:|:------:| ---:| -----:| -------:|")
    for row in schedule.ledger:
        lines.append(
            f"| {row.day:>3} | {cents_to_str(row.opening_cents):>7} | {cents_to_str(row.deposit_cents):>8} | {row.action:^6} | {cents_to_str(row.net_cents):>3} | {cents_to_str(row.bills_cents):>5} | {cents_to_str(row.closing_cents):>7} |"
        )
    lines.append("")
    w, b2b, delta, large, sp = schedule.objective
    lines.append(
        f"Objective: workdays={w}, b2b={b2b}, |Δ|={cents_to_str(delta)}, large_days={large}, single_pen={sp}"
    )
    lines.append(f"Final closing: {cents_to_str(schedule.final_closing_cents)}")
    return "\n".join(lines)


def render_csv(schedule: Schedule) -> str:
    lines: List[str] = []
    lines.append("Day,Opening,Deposits,Action,Net,Bills,Closing")
    for row in schedule.ledger:
        lines.append(
            ",".join(
                [
                    str(row.day),
                    cents_to_str(row.opening_cents),
                    cents_to_str(row.deposit_cents),
                    row.action,
                    cents_to_str(row.net_cents),
                    cents_to_str(row.bills_cents),
                    cents_to_str(row.closing_cents),
                ]
            )
        )
    return "\n".join(lines)


def render_json(schedule: Schedule) -> str:
    import json

    obj = {
        "actions": schedule.actions,
        "objective": list(schedule.objective),
        "final_closing": cents_to_str(schedule.final_closing_cents),
        "ledger": [
            {
                "day": r.day,
                "opening": cents_to_str(r.opening_cents),
                "deposits": cents_to_str(r.deposit_cents),
                "action": r.action,
                "net": cents_to_str(r.net_cents),
                "bills": cents_to_str(r.bills_cents),
                "closing": cents_to_str(r.closing_cents),
            }
            for r in schedule.ledger
        ],
    }
    return json.dumps(obj, separators=(",", ":"))
