"""CLI: Excel import/export commands."""

from __future__ import annotations

from pathlib import Path

import typer

from app.cli._console import console, success
from app.services.excel_service import ExcelService

app = typer.Typer(help="Excel import/export", no_args_is_help=True)
svc = ExcelService()


@app.command("templates")
def templates(target: Path = typer.Option(None, "--out", help="Output directory")) -> None:
    """Generate standard Excel import templates."""
    out = svc.generate_templates(target)
    success(f"Templates written to {out}")


@app.command("preview")
def preview(file: Path = typer.Argument(..., exists=True), sheet: str = typer.Option(None, "--sheet")) -> None:
    """Preview the rows of an Excel file without importing."""
    rows = svc.preview(file, sheet)
    for i, r in enumerate(rows[:20], start=1):
        console.print(f"{i}. {r}")


@app.command("import")
def import_cmd(
    file: Path = typer.Argument(..., exists=True),
    entity: str = typer.Argument(..., help="daily_bau|okr_progress|incident|change|<master type>"),
    sheet: str = typer.Option(None, "--sheet"),
    skip_duplicates: bool = typer.Option(True, "--skip-dup/--no-skip-dup"),
) -> None:
    """Import an Excel sheet into the database."""
    result = svc.import_sheet(file, entity, sheet=sheet, skip_duplicates=skip_duplicates)
    success(
        f"Imported {result['entity']}: {result['created']} created "
        f"of {result['rows_read']} rows ({len(result['errors'])} errors)"
    )
    for err in result["errors"][:10]:
        console.print(f"  [red]row {err['row']}: {err['error']}[/red]")


@app.command("export")
def export(report: str = typer.Argument(..., help="bau|okr|incident|evidence|summary|management"),
           target: Path = typer.Option(None, "--out")) -> None:
    """Export an XLSX report."""
    path = svc.export_report(report, target)
    success(f"Report written to {path}")
