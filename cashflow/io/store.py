from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Iterable, Mapping, Optional

from ..core.model import Bill, Deposit, Plan, to_cents, Adjustment


def load_plan(path: str | Path, allowed_dir: Optional[Path] = None) -> Plan:
    """Load a plan from a JSON file with optional path validation.

    Args:
        path: Path to the plan JSON file
        allowed_dir: Optional directory to restrict file access to (for security)

    Returns:
        Plan object parsed from JSON

    Raises:
        ValueError: If path is outside allowed directory or contains traversal attempts
        FileNotFoundError: If file doesn't exist
    """
    p = Path(path).resolve()  # Resolve symlinks and relative paths

    # Optional path traversal protection
    if allowed_dir is not None:
        allowed = Path(allowed_dir).resolve()
        try:
            # Check if resolved path is within allowed directory
            p.relative_to(allowed)
        except ValueError:
            raise ValueError(
                f"Path traversal detected: {path} is outside allowed directory {allowed_dir}"
            ) from None

    # Additional check for common path traversal patterns
    path_str = str(path)
    if ".." in path_str or path_str.startswith("/etc") or path_str.startswith("/sys"):
        raise ValueError(f"Potentially unsafe path: {path}")

    data = json.loads(p.read_text())
    return plan_from_dict(data)


def plan_from_dict(data: Mapping[str, Any]) -> Plan:
    try:
        start_balance = to_cents(data["start_balance"])
        target_end = to_cents(data["target_end"])
        band = to_cents(data["band"])
        rent_guard = to_cents(data["rent_guard"])
    except KeyError as exc:  # pragma: no cover - defensive guard
        raise ValueError(f"missing required field: {exc.args[0]}") from exc

    deposits = []
    for entry in _iter_entries(data.get("deposits", [])):
        try:
            day = int(entry["day"])
            amount = to_cents(entry["amount"])
        except KeyError as exc:  # pragma: no cover - defensive guard
            raise ValueError("deposit entries require 'day' and 'amount'") from exc
        deposits.append(Deposit(day=day, amount_cents=amount))

    bills = []
    for entry in _iter_entries(data.get("bills", [])):
        try:
            day = int(entry["day"])
            name = str(entry["name"])
            amount = to_cents(entry["amount"])
        except KeyError as exc:  # pragma: no cover - defensive guard
            raise ValueError("bill entries require 'day', 'name', and 'amount'") from exc
        bills.append(Bill(day=day, name=name, amount_cents=amount))

    raw_actions = list(data.get("actions", [None] * 30))
    if len(raw_actions) != 30:
        raise ValueError("actions must be length 30")
    actions = [
        None if action in (None, "", "null") else str(action)
        for action in raw_actions
    ]

    manual_adjustments = []
    for entry in _iter_entries(data.get("manual_adjustments", [])):
        try:
            day = int(entry["day"])
            amount = to_cents(entry["amount"])
        except KeyError as exc:  # pragma: no cover - defensive guard
            raise ValueError("manual adjustments require 'day' and 'amount'") from exc
        note = str(entry.get("note", ""))
        manual_adjustments.append(
            Adjustment(day=day, amount_cents=amount, note=note)
        )

    locks: list[tuple[int, int]] = []
    for entry in data.get("locks", []):
        if isinstance(entry, (list, tuple)) and len(entry) == 2:
            start, end = int(entry[0]), int(entry[1])
            locks.append((start, end))

    metadata_raw = data.get("metadata", {})
    metadata = dict(metadata_raw) if isinstance(metadata_raw, Mapping) else {}

    return Plan(
        start_balance_cents=start_balance,
        target_end_cents=target_end,
        band_cents=band,
        rent_guard_cents=rent_guard,
        deposits=deposits,
        bills=bills,
        actions=actions,  # type: ignore[arg-type]
        manual_adjustments=manual_adjustments,
        locks=locks,
        metadata=metadata,
    )


def _iter_entries(value: Any) -> Iterable[Mapping[str, Any]]:
    if isinstance(value, Mapping):
        return [value]
    if isinstance(value, (list, tuple)):
        return [entry for entry in value if isinstance(entry, Mapping)]
    return []
