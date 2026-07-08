"""CLI: Incident commands."""

from __future__ import annotations

import typer

from app.cli._console import console, render_dict, render_table, success
from app.services.incident_service import IncidentService

app = typer.Typer(help="Incident logging", no_args_is_help=True)
svc = IncidentService()


@app.command("add")
def add(
    date: str = typer.Option(..., "--date"),
    title: str = typer.Option(..., "--title"),
    incident_category_id: int = typer.Option(None, "--cat"),
    severity: str = typer.Option("Medium", "--severity"),
    description: str = typer.Option(None, "--desc"),
    root_cause: str = typer.Option(None, "--root-cause"),
    resolution: str = typer.Option(None, "--resolution"),
    status_id: int = typer.Option(None, "--status"),
    pic_id: int = typer.Option(None, "--pic"),
    department_id: int = typer.Option(None, "--dept"),
    resolution_time_minutes: int = typer.Option(None, "--res-min"),
) -> None:
    data = svc.create(
        date=date, title=title, incident_category_id=incident_category_id,
        severity=severity, description=description, root_cause=root_cause,
        resolution=resolution, status_id=status_id, pic_id=pic_id,
        department_id=department_id, resolution_time_minutes=resolution_time_minutes,
    )
    success(f"Incident logged (id={data['id']}, no={data['incident_no']})")


@app.command("list")
def list_cmd(
    date_from: str = typer.Option(None, "--from"),
    date_to: str = typer.Option(None, "--to"),
    severity: str = typer.Option(None, "--severity"),
    status_id: int = typer.Option(None, "--status"),
    limit: int = typer.Option(50, "--limit"),
) -> None:
    rows = svc.list(date_from=date_from, date_to=date_to, severity=severity, status_id=status_id, limit=limit)
    if not rows:
        console.print("[yellow]No incidents found.[/yellow]")
        return
    render_table("Incidents", ["id", "no", "date", "title", "severity", "status_id"],
                 [[r["id"], r["incident_no"], r["date"], r["title"], r["severity"], r["status_id"]] for r in rows])


@app.command("show")
def show(incident_id: int = typer.Argument(...)) -> None:
    render_dict(f"Incident #{incident_id}", svc.get(incident_id))


@app.command("rm")
def remove(incident_id: int = typer.Argument(...)) -> None:
    svc.delete(incident_id)
    success(f"Incident id={incident_id} removed")
