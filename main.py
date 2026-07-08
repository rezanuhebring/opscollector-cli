"""OpsCollector-CLI entry point.

Wires the Typer command groups together and initialises the database on first
run. Business logic lives in ``app.services``; this module only orchestrates
CLI parsing and startup.
"""

from __future__ import annotations

import os

import typer
from rich.console import Console

from app import __version__
from app.cli import (
    backup_cmd,
    bau_cmd,
    change_cmd,
    dashboard_cmd,
    db_cmd,
    evidence_cmd,
    excel_cmd,
    incident_cmd,
    master_cmd,
    okr_cmd,
    search_cmd,
    watch_cmd,
)
from app.cli import interactive, menu_actions
from app.core.logging_config import get_logger

console = Console()
logger = get_logger("cli")


def _ensure_db() -> None:
    """Create the database and seed reference + demo data if needed."""
    from app.database.db import init_db
    from app.database.seed import seed_demo_data, seed_reference_data

    try:
        init_db()
        seed_reference_data()
        seed_demo_data()
    except Exception as exc:  # pragma: no cover - defensive
        console.print(f"[red]Failed to initialise database:[/red] {exc}")
        raise typer.Exit(code=1)


app = typer.Typer(
    name="opscollector",
    help="OpsCollector-CLI — Capture Once. Report Everywhere.",
    # NOTE: no_args_is_help is intentionally False so that running the app with
    # no arguments reaches this module's callback (which launches the keyboard
    # menu). With it True, Typer would print help and exit before the menu.
    no_args_is_help=False,
)

app.add_typer(master_cmd.app, name="master")
app.add_typer(bau_cmd.app, name="bau")
app.add_typer(okr_cmd.app, name="okr")
app.add_typer(incident_cmd.app, name="incident")
app.add_typer(change_cmd.app, name="change")
app.add_typer(evidence_cmd.app, name="evidence")
app.add_typer(search_cmd.app, name="search")
app.add_typer(dashboard_cmd.app, name="dashboard")
app.add_typer(excel_cmd.app, name="excel")
app.add_typer(db_cmd.app, name="db")
app.add_typer(backup_cmd.app, name="backup")
app.add_typer(watch_cmd.app, name="watch")


def _version_callback(value: bool) -> None:
    if value:
        console.print(f"OpsCollector-CLI v{__version__}")
        raise typer.Exit()


def _build_menu() -> list[interactive.MenuItem]:
    """Top-level keyboard-menu items, mapped to service-backed flows."""
    return [
        interactive.MenuItem("Daily BAU", "Log daily business-as-usual", bau_add_flow),
        interactive.MenuItem("Incident", "Log an operational incident", incident_add_flow),
        interactive.MenuItem("Change / Maint.", "Log a change or maintenance", change_add_flow),
        interactive.MenuItem("Evidence", "Add a file to the evidence repo", evidence_add_flow),
        interactive.MenuItem("Master Data", "Add/list reference data", master_add_flow),
        interactive.MenuItem("List Incidents", "View logged incidents", incident_list_flow),
        interactive.MenuItem("List BAU", "View BAU records", bau_list_flow),
        interactive.MenuItem("List Changes", "View change records", change_list_flow),
        interactive.MenuItem("List Evidence", "View evidence register", evidence_list_flow),
        interactive.MenuItem("Import Excel/CSV", "Bulk import from a file", excel_import_flow),
        interactive.MenuItem("Load Demo Data", "Populate example data", load_demo_flow),
        interactive.MenuItem("Dashboard", "View operational summary", dashboard_flow),
        interactive.MenuItem("Search", "Search operational data", search_flow),
        interactive.MenuItem("Excel Export", "Export a report to Excel", excel_export_flow),
        interactive.MenuItem("Backup", "Create a timestamped backup", backup_flow),
        interactive.MenuItem("About", "Version and help", about_flow),
    ]


@app.callback(invoke_without_command=True)
def main(
    version: bool = typer.Option(False, "--version", callback=_version_callback, is_eager=True),
    cli: bool = typer.Option(False, "--cli", help="Use the typed command-line interface instead of the keyboard menu"),
) -> None:
    """OpsCollector-CLI main entry point.

    By default opens an interactive keyboard-driven menu (Up/Down/Left/Right,
    Enter to select, Esc to go back). Use ``--cli`` for the classic typed
    commands, or set ``OPSC_KEYBOARD=0`` to disable the menu by default.
    """
    _ensure_db()
    if cli or os.environ.get("OPSC_KEYBOARD", "1") == "0":
        return  # fall through to Typer command dispatch
    try:
        interactive.run_menu("OpsCollector-CLI — Capture Once. Report Everywhere.", _build_menu())
    except KeyboardInterrupt:
        console.print("\n[dim]Exited.[/dim]")
    raise typer.Exit()


if __name__ == "__main__":
    app()
