"""CLI: Search commands."""

from __future__ import annotations

import typer

from app.cli._console import console, render_table
from app.services.search_service import SearchService

app = typer.Typer(help="Search operational data", no_args_is_help=True)
svc = SearchService()


@app.command("run")
def run(
    keyword: str = typer.Option(None, "--kw"),
    date_from: str = typer.Option(None, "--from"),
    date_to: str = typer.Option(None, "--to"),
    pic_id: int = typer.Option(None, "--pic"),
    status_id: int = typer.Option(None, "--status"),
    entity_types: list[str] = typer.Option(None, "--type", help="bau|okr|incident|change"),
) -> None:
    """Search across operational modules."""
    results = svc.search(
        keyword=keyword, date_from=date_from, date_to=date_to,
        pic_id=pic_id, status_id=status_id, entity_types=entity_types,
    )
    total = sum(len(v) for v in results.values())
    if total == 0:
        console.print("[yellow]No matches found.[/yellow]")
        return
    for etype, rows in results.items():
        if not rows:
            continue
        console.print(f"[bold cyan]{etype.upper()}[/bold cyan] ({len(rows)})")
        for r in rows[:10]:
            title = r.get("title") or r.get("achievement") or r.get("incident_no") or r.get("change_no") or "-"
            console.print(f"  [#{r.get('id')}] {r.get('date')} - {title}")
