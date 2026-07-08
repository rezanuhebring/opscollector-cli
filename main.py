"""OpsCollector-CLI entry point.

Wires the Typer command groups together and initialises the database on first
run. Business logic lives in ``app.services``; this module only orchestrates
CLI parsing and startup.
"""

from __future__ import annotations

import typer
from rich.console import Console

from app import __version__
from app.cli import (
    backup_cmd,
    bau_cmd,
    change_cmd,
    dashboard_cmd,
    evidence_cmd,
    excel_cmd,
    incident_cmd,
    master_cmd,
    okr_cmd,
    search_cmd,
    watch_cmd,
)
from app.core.logging_config import get_logger

console = Console()
logger = get_logger("cli")


def _ensure_db() -> None:
    """Create the database and seed reference data if needed."""
    from app.database.db import init_db

    try:
        init_db()
    except Exception as exc:  # pragma: no cover - defensive
        console.print(f"[red]Failed to initialise database:[/red] {exc}")
        raise typer.Exit(code=1)


app = typer.Typer(
    name="opscollector",
    help="OpsCollector-CLI — Capture Once. Report Everywhere.",
    no_args_is_help=True,
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
app.add_typer(backup_cmd.app, name="backup")
app.add_typer(watch_cmd.app, name="watch")


def _version_callback(value: bool) -> None:
    if value:
        console.print(f"OpsCollector-CLI v{__version__}")
        raise typer.Exit()


@app.callback()
def main(
    version: bool = typer.Option(False, "--version", callback=_version_callback, is_eager=True),
) -> None:
    """OpsCollector-CLI main entry point."""
    _ensure_db()


if __name__ == "__main__":
    app()
