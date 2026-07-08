"""CLI: Backup & Restore commands."""

from __future__ import annotations

import typer

from app.cli._console import console, render_table, success
from app.services.backup_service import BackupService

app = typer.Typer(help="Backup & Restore", no_args_is_help=True)
svc = BackupService()


@app.command("create")
def create(label: str = typer.Option(None, "--label")) -> None:
    """Create a full backup."""
    path = svc.backup(label=label)
    success(f"Backup created at {path}")


@app.command("list")
def list_() -> None:
    """List existing backups."""
    backups = svc.list_backups()
    if not backups:
        console.print("[yellow]No backups found.[/yellow]")
        return
    render_table("Backups", ["name", "created_at", "label"],
                 [[b.get("name"), b.get("created_at"), b.get("label")] for b in backups])


@app.command("restore")
def restore(
    name: str = typer.Argument(..., help="Backup folder name"),
    selective: list[str] = typer.Option(None, "--only", help="database|config|export"),
) -> None:
    """Restore a backup (full, or selective via --only)."""
    svc.restore(backup_name=name, selective=selective or None)
    success(f"Restored backup '{name}'")
