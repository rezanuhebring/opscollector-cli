"""CLI: Daily BAU commands."""

from __future__ import annotations

import typer

from app.cli._console import console, render_dict, render_table, success
from app.services.bau_service import BAUService

app = typer.Typer(help="Daily BAU (Business As Usual) logging", no_args_is_help=True)
svc = BAUService()


@app.command("add")
def add(
    date: str = typer.Option(..., "--date", help="YYYY-MM-DD"),
    title: str = typer.Option(..., "--title"),
    bau_activity_id: int = typer.Option(None, "--activity"),
    description: str = typer.Option(None, "--desc"),
    status_id: int = typer.Option(None, "--status"),
    pic_id: int = typer.Option(None, "--pic"),
    department_id: int = typer.Option(None, "--dept"),
    duration_minutes: int = typer.Option(None, "--duration"),
    notes: str = typer.Option(None, "--notes"),
) -> None:
    """Record a daily BAU activity."""
    data = svc.create(
        date=date, title=title, bau_activity_id=bau_activity_id,
        description=description, status_id=status_id, pic_id=pic_id,
        department_id=department_id, duration_minutes=duration_minutes, notes=notes,
    )
    success(f"BAU recorded (id={data['id']})")


@app.command("list")
def list_cmd(
    date_from: str = typer.Option(None, "--from"),
    date_to: str = typer.Option(None, "--to"),
    status_id: int = typer.Option(None, "--status"),
    pic_id: int = typer.Option(None, "--pic"),
    limit: int = typer.Option(50, "--limit"),
) -> None:
    """List BAU records with optional filters."""
    rows = svc.list(date_from=date_from, date_to=date_to, status_id=status_id, pic_id=pic_id, limit=limit)
    if not rows:
        console.print("[yellow]No BAU records found.[/yellow]")
        return
    render_table("Daily BAU", ["id", "date", "title", "status_id", "pic_id", "duration_minutes"],
                 [[r["id"], r["date"], r["title"], r["status_id"], r["pic_id"], r["duration_minutes"]] for r in rows])


@app.command("show")
def show(bau_id: int = typer.Argument(...)) -> None:
    """Show a single BAU record."""
    render_dict(f"BAU #{bau_id}", svc.get(bau_id))


@app.command("rm")
def remove(bau_id: int = typer.Argument(...)) -> None:
    """Remove a BAU record."""
    svc.delete(bau_id)
    success(f"BAU id={bau_id} removed")
