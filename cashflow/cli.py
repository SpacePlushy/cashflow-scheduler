from __future__ import annotations
from pathlib import Path
from typing import Optional

import typer

from .io.store import load_plan
from .engines.dp import solve as dp_solve
from .core.validate import validate
from .engines.cpsat import verify_lex_optimal
from .io.render import render_markdown

app = typer.Typer(help="30-Day Cash-Flow Scheduler")


def _default_plan_path() -> Path:
    return Path.cwd() / "plan.json"


@app.command("solve")
def cmd_solve(
    plan_path: Optional[str] = typer.Argument(None, help="Path to plan.json")
):
    path = Path(plan_path) if plan_path else _default_plan_path()
    plan = load_plan(path)
    schedule = dp_solve(plan)
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
    format: str = typer.Option("md", help="md|csv|json (md supported)"),
    out: str = typer.Option("schedule.md", help="Output file path"),
):
    path = Path(plan_path) if plan_path else _default_plan_path()
    plan = load_plan(path)
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


def main():
    app()


if __name__ == "__main__":
    main()
