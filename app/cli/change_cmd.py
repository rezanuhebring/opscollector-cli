"""CLI: Change & Maintenance commands."""

from __future__ import annotations

import typer

from app.cli._console import console, render_dict, render_table, success
from app.services.change_service import ChangeService

app = typer.Typer(help="Change & Maintenance logging", no_args_is_help=True)
svc = ChangeService()


@app.command("add")
def add(
    date: str = typer.Option(..., "--date"),
    title: str = typer.Option(..., "--title"),
    change_category_id: int = typer.Option(None, "--cat"),
    change_type: str = typer.Option("Change", "--type"),
    description: str = typer.Option(None, "--desc"),
    status_id: int = typer.Option(None, "--status"),
    pic_id: int = typer.Option(None, "--pic"),
    department_id: int = typer.Option(None, "--dept"),
    scheduled_start: str = typer.Option(None, "--start"),
    scheduled_end: str = typer.Option(None, "--end"),
    result: str = typer.Option(None, "--result"),
) -> None:
    data = svc.create(
        date=date, title=title, change_category_id=change_category_id,
        change_type=change_type, description=description, status_id=status_id,
        pic_id=pic_id, department_id=department_id, scheduled_start=scheduled_start,
        scheduled_end=scheduled_end, result=result,
    )
    success(f"Change logged (id={data['id']}, no={data['change_no']})")


@app.command("list")
def list_cmd(
    date_from: str = typer.Option(None, "--from"),
    date_to: str = typer.Option(None, "--to"),
    change_type: str = typer.Option(None, "--type"),
    status_id: int = typer.Option(None, "--status"),
    limit: int = typer.Option(50, "--limit"),
) -> None:
    rows = svc.list(date_from=date_from, date_to=date_to, change_type=change_type, status_id=status_id, limit=limit)
    if not rows:
        console.print("[yellow]No change records found.[/yellow]")
        return
    render_table("Change & Maintenance", ["id", "no", "date", "title", "type", "status_id"],
                 [[r["id"], r["change_no"], r["date"], r["title"], r["change_type"], r["status_id"]] for r in rows])


@app.command("show")
def show(change_id: int = typer.Argument(...)) -> None:
    render_dict(f"Change #{change_id}", svc.get(change_id))


@app.command("rm")
def remove(change_id: int = typer.Argument(...)) -> None:
    svc.delete(change_id)
    success(f"Change id={change_id} removed")
