"""CLI: Evidence repository commands."""

from __future__ import annotations

from pathlib import Path

import typer

from app.cli._console import console, render_dict, render_table, success
from app.services.evidence_service import EvidenceService

app = typer.Typer(help="Evidence repository", no_args_is_help=True)
svc = EvidenceService()


@app.command("add")
def add(
    source: Path = typer.Argument(..., help="Path to the file to store", exists=True, file_okay=True, dir_okay=False),
    title: str = typer.Option(None, "--title"),
    description: str = typer.Option(None, "--desc"),
    evidence_category_id: int = typer.Option(None, "--cat"),
    uploaded_by: str = typer.Option(None, "--by"),
    entity_type: str = typer.Option(None, "--entity", help="bau|okr|incident|change"),
    entity_id: int = typer.Option(None, "--entity-id"),
) -> None:
    """Copy a file into the evidence repository."""
    data = svc.add_file(
        source_path=source, title=title, description=description,
        evidence_category_id=evidence_category_id, uploaded_by=uploaded_by,
        entity_type=entity_type, entity_id=entity_id,
    )
    success(f"Evidence stored (id={data['id']}) -> {data['relative_path']}")


@app.command("list")
def list_cmd(
    entity_type: str = typer.Option(None, "--entity"),
    entity_id: int = typer.Option(None, "--entity-id"),
    evidence_category_id: int = typer.Option(None, "--cat"),
    limit: int = typer.Option(50, "--limit"),
) -> None:
    rows = svc.list(entity_type=entity_type, entity_id=entity_id, evidence_category_id=evidence_category_id, limit=limit)
    if not rows:
        console.print("[yellow]No evidence found.[/yellow]")
        return
    render_table("Evidence", ["id", "title", "original_filename", "ext", "entity_type", "entity_id"],
                 [[r["id"], r["title"], r["original_filename"], r["extension"], r["entity_type"], r["entity_id"]] for r in rows])


@app.command("show")
def show(evidence_id: int = typer.Argument(...)) -> None:
    render_dict(f"Evidence #{evidence_id}", svc.get(evidence_id))


@app.command("path")
def show_path(evidence_id: int = typer.Argument(...)) -> None:
    """Print the absolute path of a stored evidence file."""
    console.print(str(svc.get_path(evidence_id)))


@app.command("rm")
def remove(evidence_id: int = typer.Argument(...), keep_file: bool = typer.Option(False, "--keep-file")) -> None:
    svc.delete(evidence_id, remove_file=not keep_file)
    success(f"Evidence id={evidence_id} removed")
