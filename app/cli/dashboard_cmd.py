"""CLI: Dashboard commands."""

from __future__ import annotations

import typer

from app.cli._console import console
from app.services.dashboard_service import DashboardService
from rich.panel import Panel
from rich.table import Table

app = typer.Typer(help="Operational dashboard", no_args_is_help=True)
svc = DashboardService()


@app.command("show")
def show() -> None:
    """Show the operational summary dashboard."""
    s = svc.summary()
    panel = Panel.fit(
        f"[bold]Objectives[/bold]: {s['objectives']['completed']}/{s['objectives']['total']} completed\n"
        f"[bold]Key Results[/bold]: {s['key_results']['total']}\n"
        f"[bold]BAU[/bold]: {s['bau']['completed']}/{s['bau']['total']} ({s['bau']['completion_pct']}%)\n"
        f"[bold]Incidents[/bold]: {s['incidents']['total']} ({s['incidents']['open']} open)\n"
        f"[bold]Changes[/bold]: {s['changes']['total']}\n"
        f"[bold]Evidence[/bold]: {s['evidence']['total']}\n"
        f"[bold]Outstanding[/bold]: {s['outstanding']}",
        title="OpsCollector Dashboard",
        border_style="magenta",
    )
    console.print(panel)


@app.command("weekly")
def weekly(weeks: int = typer.Option(6, "--weeks")) -> None:
    """Show weekly trend for the last N weeks."""
    trend = svc.weekly_trend(weeks=weeks)
    table = Table(title="Weekly Trend")
    table.add_column("Week")
    table.add_column("BAU")
    table.add_column("Incidents")
    table.add_column("Changes")
    for w in trend:
        table.add_row(w["week"], str(w["bau"]), str(w["incidents"]), str(w["changes"]))
    console.print(table)


@app.command("objectives")
def objectives() -> None:
    """Show objective progress."""
    rows = svc.objectives_progress()
    table = Table(title="Objective Progress")
    table.add_column("id")
    table.add_column("name")
    table.add_column("progress")
    table.add_column("KRs")
    table.add_column("KR avg")
    for r in rows:
        table.add_row(str(r["id"]), r["name"], str(r["progress"]), str(r["key_results"]), str(r["kr_avg_progress"]))
    console.print(table)
