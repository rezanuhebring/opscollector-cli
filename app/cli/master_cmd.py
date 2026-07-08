"""CLI: master data commands."""

from __future__ import annotations

import typer

from app.cli._console import console, handle_error, render_dict, render_table, success
from app.services.master_service import MasterService

app = typer.Typer(help="Manage master / reference data", no_args_is_help=True)
svc = MasterService()


@app.command("types")
def list_types() -> None:
    """List available master entity types."""
    render_table("Master Entity Types", ["type"], [[t] for t in svc.list_types()])


@app.command("list")
def list_entities(entity: str = typer.Argument(..., help="Entity type")) -> None:
    """List all records of a master entity."""
    rows = svc.list(entity)
    if not rows:
        console.print(f"[yellow]No {entity} records found.[/yellow]")
        return
    cols = list(rows[0].keys())
    render_table(entity, cols, [[r.get(c) for c in cols] for r in rows])


@app.command("add")
def add(
    entity: str = typer.Argument(..., help="Entity type"),
    name: str = typer.Option(..., "--name", help="Name"),
    description: str = typer.Option(None, "--desc", help="Description"),
) -> None:
    """Add a master record (name + description only for generic types)."""
    data = svc.create(entity, name=name, description=description)
    success(f"{entity} '{name}' created (id={data['id']})")


@app.command("rm")
def remove(entity: str = typer.Argument(...), id: int = typer.Argument(...)) -> None:
    """Remove a master record by id."""
    svc.delete(entity, id)
    success(f"{entity} id={id} removed")


@handle_error
def _run() -> None:
    app()
