"""CLI: OKR progress commands."""

from __future__ import annotations

import typer

from app.cli._console import console, render_dict, render_table, success
from app.services.okr_service import OKRService

app = typer.Typer(help="OKR progress tracking", no_args_is_help=True)
svc = OKRService()


@app.command("add")
def add(
    key_result_id: int = typer.Option(..., "--kr"),
    date: str = typer.Option(..., "--date"),
    current_value: float = typer.Option(0.0, "--value"),
    gap: float = typer.Option(0.0, "--gap"),
    progress: float = typer.Option(0.0, "--progress"),
    achievement: str = typer.Option(None, "--achievement"),
    risk: str = typer.Option(None, "--risk"),
    issue: str = typer.Option(None, "--issue"),
    action_plan: str = typer.Option(None, "--action"),
) -> None:
    """Record OKR progress for a Key Result."""
    data = svc.create(
        key_result_id=key_result_id, date=date, current_value=current_value,
        gap=gap, progress=progress, achievement=achievement, risk=risk,
        issue=issue, action_plan=action_plan,
    )
    success(f"OKR progress recorded (id={data['id']})")


@app.command("list")
def list_cmd(key_result_id: int = typer.Option(None, "--kr"), limit: int = typer.Option(50, "--limit")) -> None:
    """List OKR progress records."""
    rows = svc.list(key_result_id=key_result_id, limit=limit)
    if not rows:
        console.print("[yellow]No OKR progress records found.[/yellow]")
        return
    render_table("OKR Progress", ["id", "kr_id", "date", "current_value", "gap", "progress"],
                 [[r["id"], r["key_result_id"], r["date"], r["current_value"], r["gap"], r["progress"]] for r in rows])


@app.command("show")
def show(progress_id: int = typer.Argument(...)) -> None:
    render_dict(f"OKR Progress #{progress_id}", svc.get(progress_id))


@app.command("rm")
def remove(progress_id: int = typer.Argument(...)) -> None:
    svc.delete(progress_id)
    success(f"OKR progress id={progress_id} removed")
