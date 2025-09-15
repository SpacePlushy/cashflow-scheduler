from __future__ import annotations
import os
import sys
from pathlib import Path
from typing import Optional

import typer

from .io.store import load_plan
from .engines.dp import solve as dp_solve
from .core.ledger import build_ledger
from .core.validate import validate
from .engines.cpsat import verify_lex_optimal
from .io.render import render_markdown, build_rich_table
from .io.calendar import render_calendar_png
from .core.model import Adjustment, to_cents

app = typer.Typer(help="30-Day Cash-Flow Scheduler")


def _default_plan_path() -> Path:
    return Path.cwd() / "plan.json"


def _load_plan_or_exit(path: Path):
    try:
        return load_plan(path)
    except FileNotFoundError:
        typer.secho(f"Plan file not found: {path}", fg=typer.colors.RED)
        typer.secho(
            "Hint: run from the repo root or pass a path, e.g.\n  python -m cashflow.cli solve path/to/plan.json",
            fg=typer.colors.YELLOW,
        )
        raise typer.Exit(code=2)
    except Exception as e:  # noqa: BLE001
        typer.secho(f"Failed to load plan from {path}: {e}", fg=typer.colors.RED)
        raise typer.Exit(code=2)


@app.command("solve")
def cmd_solve(
    plan_path: Optional[str] = typer.Argument(None, help="Path to plan.json")
):
    path = Path(plan_path) if plan_path else _default_plan_path()
    plan = _load_plan_or_exit(path)
    schedule = dp_solve(plan)
    report = validate(plan, schedule)
    printed = False
    if sys.stdout.isatty() and os.environ.get("CF_FORCE_MARKDOWN") != "1":
        try:
            from rich.console import Console

            console = Console()
            console.print(build_rich_table(schedule))
            printed = True
        except Exception:
            printed = False
    if not printed:
        typer.echo(render_markdown(schedule))
    typer.echo("")
    typer.echo("Validation:")
    for name, ok, detail in report.checks:
        typer.echo(f"- {name}: {'[x]' if ok else '[ ]'} {detail}")
    if not report.ok:
        raise typer.Exit(code=2)


@app.command("show")
def cmd_show(plan_path: Optional[str] = typer.Argument(None, help="Path to plan.json")):
    path = Path(plan_path) if plan_path else _default_plan_path()
    plan = _load_plan_or_exit(path)
    schedule = dp_solve(plan)
    printed = False
    if sys.stdout.isatty() and os.environ.get("CF_FORCE_MARKDOWN") != "1":
        try:
            from rich.console import Console

            Console().print(build_rich_table(schedule))
            printed = True
        except Exception:
            printed = False
    if not printed:
        typer.echo(render_markdown(schedule))


@app.command("export")
def cmd_export(
    plan_path: Optional[str] = typer.Argument(None, help="Path to plan.json"),
    format: str = typer.Option("md", help="md|csv|json (md supported)"),
    out: str = typer.Option("schedule.md", help="Output file path"),
):
    path = Path(plan_path) if plan_path else _default_plan_path()
    plan = _load_plan_or_exit(path)
    schedule = dp_solve(plan)
    if format != "md":
        typer.echo("Only markdown export is implemented at this time", err=True)
        raise typer.Exit(code=2)
    text = render_markdown(schedule)
    Path(out).write_text(text)
    typer.echo(f"Wrote {out}")


@app.command("verify")
def cmd_verify(
    plan_path: Optional[str] = typer.Argument(None, help="Path to plan.json")
):
    """Cross-verify DP solution against CP-SAT sequential-lex optimum."""
    path = Path(plan_path) if plan_path else _default_plan_path()
    plan = _load_plan_or_exit(path)
    schedule = dp_solve(plan)
    report = verify_lex_optimal(plan, schedule)
    typer.echo("DP Objective:   " + str(schedule.objective))
    typer.echo("CP-SAT Objective: " + str(report.cp_obj))
    if getattr(report, "statuses", None):
        names = ["workdays", "b2b", "|Δ|"]
        typer.echo("Solver statuses:")
        for i, s in enumerate(report.statuses or []):
            label = names[i] if i < len(names) else f"part{i+1}"
            typer.echo(f"- {label}: {s}")
    if report.ok:
        if report.dp_obj == report.cp_obj and report.dp_actions != report.cp_actions:
            typer.echo("Objectives match; actions differ (tie)")
        else:
            typer.echo("Match: OK")
    else:
        typer.echo(report.detail)
        raise typer.Exit(code=2)


@app.command("set-eod")
def cmd_set_eod(
    day: int = typer.Argument(..., help="Day index (1..30) to set EOD for"),
    eod_amount: float = typer.Argument(
        ..., help="Desired end-of-day balance (e.g., 167.00)"
    ),
    plan_path: Optional[str] = typer.Argument(
        None, help="Path to plan.json (defaults to CWD)"
    ),
    save_plan: Optional[str] = typer.Option(
        None, help="Optional path to write updated plan JSON"
    ),
    calendar: bool = typer.Option(
        False,
        "--calendar",
        help="Also render calendar PNG to ~/Downloads/cashflow_calendar.png",
    ),
):
    """Adjust the plan so that Day `day` closes at `eod_amount`, lock days 1..day,
    and re-solve the remainder. Prints the new schedule and validation report.

    Mirrors the serverless API's /set_eod endpoint.
    """
    if not (1 <= day <= 30):
        typer.echo("day must be in 1..30", err=True)
        raise typer.Exit(code=2)

    path = Path(plan_path) if plan_path else _default_plan_path()
    plan = load_plan(path)

    baseline = dp_solve(plan)
    base_ledger = build_ledger(plan, baseline.actions)
    current_eod = base_ledger[day - 1].closing_cents
    desired_cents = to_cents(eod_amount)
    delta = desired_cents - current_eod

    # Lock prefix actions and append manual adjustment
    plan.actions = baseline.actions[:day] + [None] * (30 - day)
    plan.manual_adjustments = list(plan.manual_adjustments) + [
        Adjustment(day=day, amount_cents=delta, note="cli set-eod"),
    ]

    schedule = dp_solve(plan)
    report = validate(plan, schedule)
    printed = False
    if sys.stdout.isatty() and os.environ.get("CF_FORCE_MARKDOWN") != "1":
        try:
            from rich.console import Console

            Console().print(build_rich_table(schedule))
            printed = True
        except Exception:
            printed = False
    if not printed:
        typer.echo(render_markdown(schedule))
    typer.echo("")
    typer.echo("Validation:")
    for name, ok, detail in report.checks:
        typer.echo(f"- {name}: {'[x]' if ok else '[ ]'} {detail}")
    if not report.ok:
        raise typer.Exit(code=2)
    if save_plan:
        # Persist an updated plan JSON with merged actions/adjustments
        try:
            import json

            data = json.loads(Path(path).read_text())
            data["actions"] = plan.actions
            madj = list(data.get("manual_adjustments", []))
            # Amount is delta in dollars
            madj.append({"day": day, "amount": delta / 100.0, "note": "cli set-eod"})
            data["manual_adjustments"] = madj
            Path(save_plan).write_text(json.dumps(data, indent=2))
            typer.echo(f"Wrote {save_plan}")
        except Exception as e:
            typer.echo(f"Failed to write updated plan: {e}", err=True)
            raise typer.Exit(code=2)
    if calendar:
        out_path = Path.home() / "Downloads" / "cashflow_calendar.png"
        try:
            bmap: dict[int, list[tuple[str, int]]] = {}
            for b in plan.bills:
                bmap.setdefault(b.day, []).append((b.name, b.amount_cents))
            render_calendar_png(
                schedule,
                out_path,
                size=(3840, 2160),
                theme="dark",
                bills_by_day=bmap,
            )
        except RuntimeError as e:
            typer.echo(str(e), err=True)
            raise typer.Exit(code=2)
        typer.echo(f"Updated {out_path}")


@app.command("calendar")
def cmd_calendar(
    plan_path: Optional[str] = typer.Argument(None, help="Path to plan.json"),
    out: Optional[str] = typer.Option(
        None, help="Output PNG path (default: ~/Downloads/cashflow_calendar.png)"
    ),
    width: int = typer.Option(3840, help="Image width (px)"),
    height: int = typer.Option(2160, help="Image height (px)"),
    theme: str = typer.Option("dark", help="Theme: dark|light"),
    force_4k: bool = typer.Option(
        False, "--4k", help="Force 3840x2160 regardless of width/height"
    ),
):
    """Generate a high-resolution calendar PNG for wallpaper use."""
    path = Path(plan_path) if plan_path else _default_plan_path()
    plan = load_plan(path)
    schedule = dp_solve(plan)
    bmap: dict[int, list[tuple[str, int]]] = {}
    for b in plan.bills:
        bmap.setdefault(b.day, []).append((b.name, b.amount_cents))

    out_path = (
        Path(out).expanduser()
        if out
        else Path.home() / "Downloads" / "cashflow_calendar.png"
    )
    if force_4k:
        width, height = 3840, 2160
    try:
        render_calendar_png(
            schedule, out_path, size=(width, height), theme=theme, bills_by_day=bmap
        )
    except RuntimeError as e:
        typer.echo(str(e), err=True)
        raise typer.Exit(code=2)
    typer.echo(f"Wrote {out_path} ({width}x{height})")


def main():
    app()


if __name__ == "__main__":
    main()
