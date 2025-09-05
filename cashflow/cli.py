from __future__ import annotations
from pathlib import Path
from typing import Optional

import typer

from .io.store import load_plan, save_plan
from .engines.dp import solve as dp_solve
from .engines.dp import solve_from as dp_solve_from
from .core.validate import validate
from .engines.cpsat import verify_lex_optimal, enumerate_ties
from .io.render import render_markdown, render_csv, render_json
from .core.ledger import build_ledger
from .core.model import to_cents, Adjustment, Schedule

app = typer.Typer(help="30-Day Cash-Flow Scheduler")


def _default_plan_path() -> Path:
    return Path.cwd() / "plan.json"


@app.command("solve")
def cmd_solve(
    plan_path: Optional[str] = typer.Argument(None, help="Path to plan.json"),
    from_day: Optional[int] = typer.Option(
        None,
        "--from",
        "--from-day",
        help="Lock prefix and re-solve tail starting from this day",
    ),
    target: Optional[float] = typer.Option(
        None, help="Override target_end (dollars) for this run"
    ),
    band: Optional[float] = typer.Option(
        None, help="Override band (dollars) for this run"
    ),
    forbid_large_after_day1: bool = typer.Option(
        False, help="Disallow Large shifts after day 1 during solve"
    ),
):
    path = Path(plan_path) if plan_path else _default_plan_path()
    plan = load_plan(path)
    if target is not None:
        plan.target_end_cents = to_cents(target)
    if band is not None:
        plan.band_cents = to_cents(band)

    try:
        if from_day is not None:
            schedule = dp_solve_from(
                plan, from_day, forbid_large_after_day1=forbid_large_after_day1
            )
        else:
            schedule = dp_solve(plan, forbid_large_after_day1=forbid_large_after_day1)
    except Exception as e:
        typer.echo(str(e), err=True)
        typer.echo(
            "Hint: try widening --band, adjusting --target, or relaxing constraints (e.g., allow Large after day 1).",
            err=True,
        )
        raise typer.Exit(code=2)
    report = validate(plan, schedule)
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
    plan = load_plan(path)
    schedule = dp_solve(plan)
    typer.echo(render_markdown(schedule))


@app.command("export")
def cmd_export(
    plan_path: Optional[str] = typer.Argument(None, help="Path to plan.json"),
    format: str = typer.Option("md", help="md|csv|json"),
    out: str = typer.Option("schedule.md", help="Output file path"),
):
    path = Path(plan_path) if plan_path else _default_plan_path()
    plan = load_plan(path)
    schedule = dp_solve(plan)
    if format == "md":
        text = render_markdown(schedule)
    elif format == "csv":
        text = render_csv(schedule)
    elif format == "json":
        text = render_json(schedule)
    else:
        typer.echo("Unsupported format (use md|csv|json)", err=True)
        raise typer.Exit(code=2)
    Path(out).write_text(text)
    typer.echo(f"Wrote {out}")


@app.command("verify")
def cmd_verify(
    plan_path: Optional[str] = typer.Argument(None, help="Path to plan.json")
):
    """Cross-verify DP solution against CP-SAT sequential-lex optimum."""
    path = Path(plan_path) if plan_path else _default_plan_path()
    plan = load_plan(path)
    schedule = dp_solve(plan)
    report = verify_lex_optimal(plan, schedule)
    typer.echo("DP Objective:   " + str(schedule.objective))
    typer.echo("CP-SAT Objective: " + str(report.cp_obj))
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
    day: int = typer.Argument(..., help="Day index (1-30)"),
    amount: str = typer.Argument(
        ..., help="Desired end-of-day balance in dollars (e.g., 1286.01)"
    ),
    plan_path: Optional[str] = typer.Option(None, "--plan", help="Path to plan.json"),
    write: bool = typer.Option(True, help="Persist changes to plan.json"),
):
    path = Path(plan_path) if plan_path else _default_plan_path()
    plan = load_plan(path)
    base = dp_solve(plan)
    base_ledger = build_ledger(plan, base.actions)
    if not (1 <= day <= 30):
        typer.echo("day must be in 1..30", err=True)
        raise typer.Exit(code=2)
    desired_cents = to_cents(amount)
    current_eod = base_ledger[day - 1].closing_cents
    delta = desired_cents - current_eod
    # Lock prefix actions through the edited day and append manual adjustment
    plan.actions = base.actions[:day] + [None] * (30 - day)
    plan.manual_adjustments = list(plan.manual_adjustments) + [
        Adjustment(day=day, amount_cents=delta, note="cli set-eod"),
    ]

    # Try solving to sanity-check feasibility now
    try:
        new_sched = dp_solve(plan)
        rep = validate(plan, new_sched)
    except Exception as e:
        typer.echo(f"Set EOD applied, but re-solve failed: {e}", err=True)
        rep = None
        new_sched = None  # type: ignore

    if write:
        save_plan(path, plan)
        typer.echo(f"Updated plan written to {path}")
    else:
        typer.echo(
            "Updated plan in-memory; not written (use --no-write to keep transient)"
        )

    if new_sched is not None and rep is not None:
        final_eod = new_sched.ledger[day - 1].closing_cents
        typer.echo(
            f"Day {day} closing set from {current_eod} to {final_eod} cents; tail is re-solved."
        )
        if not rep.ok:
            typer.echo("Validation has failures for updated plan:")
            for name, ok, detail in rep.checks:
                typer.echo(f"- {name}: {'[x]' if ok else '[ ]'} {detail}")
        typer.echo("Tip: run 'cash solve --from' with the next day to view the tail.")


@app.command("pareto")
def cmd_pareto(
    plan_path: Optional[str] = typer.Argument(None, help="Path to plan.json"),
    limit: int = typer.Option(5, help="Max solutions to enumerate"),
):
    """Enumerate alternative schedules with identical objective (requires OR-Tools)."""
    path = Path(plan_path) if plan_path else _default_plan_path()
    plan = load_plan(path)
    try:
        sols = enumerate_ties(plan, limit=limit)
    except Exception as e:
        typer.echo(f"CP-SAT enumeration failed: {e}", err=True)
        raise typer.Exit(code=2)
    if not sols:
        typer.echo("No solutions found (unexpected).")
        return
    base_obj = sols[0].objective
    typer.echo(f"Found {len(sols)} solution(s) with objective {base_obj}:")
    for i, s in enumerate(sols, start=1):
        typer.echo(f"[{i}] final={s.final_closing_cents}  actions={''.join(s.actions)}")


def _objective_for_actions(plan, actions):
    # workdays
    w = sum(1 for a in actions if a != "O")
    # b2b
    b2b = sum(1 for i in range(29) if actions[i] != "O" and actions[i + 1] != "O")
    # large_days
    large = sum(1 for a in actions if a == "L")
    # single_pen: 1 for M, 2 for L
    sp = sum(1 if a == "M" else 2 if a == "L" else 0 for a in actions)
    # final closing via ledger
    ledger = build_ledger(plan, actions)
    final = ledger[-1].closing_cents
    abs_delta = abs(final - plan.target_end_cents)
    return (w, b2b, abs_delta, large, sp), final, ledger


def _first_failing_check(plan, actions):
    obj, final, ledger = _objective_for_actions(plan, actions)
    sched = Schedule(
        actions=actions, objective=obj, final_closing_cents=final, ledger=ledger
    )
    rep = validate(plan, sched)
    for name, ok, detail in rep.checks:
        if not ok:
            return name, detail
    return None, ""


@app.command("why")
def cmd_why(
    day: int = typer.Argument(..., help="Day index (1-30) to analyze"),
    plan_path: Optional[str] = typer.Option(None, "--plan", help="Path to plan.json"),
    action: Optional[str] = typer.Option(
        None, "--action", help="Test a specific alternative action: O|S|M|L|SS"
    ),
    forbid_large_after_day1: bool = typer.Option(
        False, help="Match solve flag: disallow Large shifts after day 1"
    ),
):
    """Explain why the solver chose a specific shift on a given day.

    Compares feasible alternatives by locking the prefix and forcing the candidate
    action on that day, re-solving the tail. If infeasible, prints the first
    validation check that fails when keeping the baseline tail unchanged.
    """
    if not (1 <= day <= 30):
        typer.echo("day must be in 1..30", err=True)
        raise typer.Exit(code=2)
    path = Path(plan_path) if plan_path else _default_plan_path()
    plan0 = load_plan(path)
    base = dp_solve(plan0, forbid_large_after_day1=forbid_large_after_day1)
    base_obj = base.objective
    chosen = base.actions[day - 1]
    typer.echo(f"Baseline day {day}: {chosen}; objective {base_obj}")

    universe = ["O", "S", "M", "L", "SS"]
    # Day 1 must be L
    if day == 1:
        universe = ["L"]
    if forbid_large_after_day1 and day != 1:
        universe = [a for a in universe if a != "L"]
    alts = [action] if action else [a for a in universe if a != chosen]
    if not alts:
        typer.echo("No alternative actions to evaluate for this day.")
        return

    for alt in alts:
        plan_alt = load_plan(path)
        # Lock prefix to baseline and force alt on the day
        plan_alt.actions = base.actions[: day - 1] + [alt] + [None] * (30 - day)
        try:
            sched_alt = dp_solve(
                plan_alt, forbid_large_after_day1=forbid_large_after_day1
            )
            obj_alt = sched_alt.objective
            # Compare lexicographically
            if obj_alt == base_obj:
                typer.echo(
                    f"- {alt}: Feasible with equal objective {obj_alt} → Tie; baseline preferred."
                )
            else:
                # find first differing component
                labels = [
                    "workdays",
                    "back-to-back",
                    "abs_delta_to_target",
                    "large_days",
                    "single_pen",
                ]
                idx = next(i for i in range(5) if obj_alt[i] != base_obj[i])
                direction = "worse" if obj_alt[idx] > base_obj[idx] else "better"
                typer.echo(
                    f"- {alt}: Feasible but {direction} on {labels[idx]} (alt={obj_alt[idx]} vs base={base_obj[idx]})."
                )
        except Exception:
            # Infeasible with optimal tail. Provide a quick failing check with baseline tail unchanged.
            forced_actions = base.actions[:]
            forced_actions[day - 1] = alt
            fail, detail = _first_failing_check(plan0, forced_actions)
            if fail:
                typer.echo(
                    f"- {alt}: Infeasible — first failing check: {fail} ({detail})"
                )
            else:
                typer.echo(f"- {alt}: Infeasible — could not isolate failing check")


def main():
    app()


if __name__ == "__main__":
    main()
