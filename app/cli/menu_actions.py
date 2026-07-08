"""Interactive menu actions.

Thin adapter between the keyboard menu and the service layer. Keeps all
business logic in ``app.services`` (never re-implements validation here); this
module only collects input and renders results via Rich.
"""

from __future__ import annotations

import msvcrt
import os
from datetime import date

from rich.console import Console

from app.services import (
    BAUService,
    BackupService,
    ChangeService,
    DashboardService,
    EvidenceService,
    ExcelService,
    IncidentService,
    MasterService,
    SearchService,
)

console = Console()


def _ask(prompt: str, *, default: str = "") -> str:
    """Prompt for a line of text (Windows console, no extra deps)."""
    console.print(f"[cyan]{prompt}[/cyan]", end="")
    if default:
        console.print(f" [dim]({default})[/dim]", end="")
    console.print(": ", end="")
    buf = default
    # Use input() — works in the interactive console session.
    try:
        val = input()
    except (EOFError, KeyboardInterrupt):
        return buf
    return val.strip() or default


def _ask_int(prompt: str, *, default: int = 0) -> int | None:
    raw = _ask(prompt, default=str(default))
    if raw == "":
        return None
    try:
        return int(raw)
    except ValueError:
        console.print("[yellow]! must be a number, skipping[/yellow]")
        return None


def _ask_date(prompt: str) -> str:
    default = date.today().isoformat()
    raw = _ask(prompt, default=default)
    return raw or default


def _pause() -> None:
    console.print("\n[dim]Press Enter to continue...[/dim]")
    try:
        input()
    except (EOFError, KeyboardInterrupt):
        pass


# --- Master data ---------------------------------------------------------
def master_add_flow() -> None:
    types = MasterService().list_types()
    console.print("[bold]Master entities:[/bold] " + ", ".join(types))
    entity = _ask("Entity type")
    if not entity:
        return
    name = _ask("Name")
    if not name:
        console.print("[yellow]! name required[/yellow]")
        return
    extra: dict = {}
    if entity.lower() in ("objective", "key_result"):
        extra["title"] = _ask("Title")
    try:
        rec = MasterService().create(entity, name=name, **extra)
        console.print(f"[green]✓ {entity} created (id={rec['id']})[/green]")
    except Exception as exc:
        console.print(f"[red]! {exc}[/red]")


def master_list_flow() -> None:
    types = MasterService().list_types()
    entity = _ask("Entity type", default=types[0] if types else "")
    if not entity:
        return
    rows = MasterService().list(entity)
    if not rows:
        console.print("[dim](no records)[/dim]")
        return
    for r in rows[:25]:
        console.print(f"  [{r['id']}] {r.get('name', '')}")


# --- Operational flows ---------------------------------------------------
def bau_add_flow() -> None:
    date_ = _ask_date("Date")
    title = _ask("Title")
    if not title:
        console.print("[yellow]! title required[/yellow]")
        return
    desc = _ask("Description")
    status_id = _ask_int("Status ID", default=0)
    try:
        rec = BAUService().create(
            date=date_, title=title, description=desc or None,
            status_id=status_id,
        )
        console.print(f"[green]✓ BAU logged (id={rec['id']})[/green]")
    except Exception as exc:
        console.print(f"[red]! {exc}[/red]")


def incident_add_flow() -> None:
    date_ = _ask_date("Date")
    title = _ask("Title")
    if not title:
        console.print("[yellow]! title required[/yellow]")
        return
    severity = _ask("Severity", default="Medium")
    desc = _ask("Description")
    try:
        rec = IncidentService().create(date=date_, title=title, severity=severity, description=desc or None)
        console.print(f"[green]✓ Incident logged ({rec['incident_no']})[/green]")
    except Exception as exc:
        console.print(f"[red]! {exc}[/red]")


def change_add_flow() -> None:
    date_ = _ask_date("Date")
    title = _ask("Title")
    if not title:
        console.print("[yellow]! title required[/yellow]")
        return
    ctype = _ask("Change type", default="Change")
    desc = _ask("Description")
    try:
        rec = ChangeService().create(date=date_, title=title, change_type=ctype, description=desc or None)
        console.print(f"[green]✓ Change logged (id={rec['id']})[/green]")
    except Exception as exc:
        console.print(f"[red]! {exc}[/red]")


def evidence_add_flow() -> None:
    path = _ask("Source file path")
    if not path or not os.path.exists(path):
        console.print("[yellow]! file not found[/yellow]")
        return
    title = _ask("Title", default=os.path.splitext(os.path.basename(path))[0])
    desc = _ask("Description")
    try:
        rec = EvidenceService().add_file(source_path=path, title=title or None, description=desc or None)
        console.print(f"[green]✓ Evidence stored ({rec['relative_path']})[/green]")
    except Exception as exc:
        console.print(f"[red]! {exc}[/red]")


# --- Views ---------------------------------------------------------------
def dashboard_flow() -> None:
    s = DashboardService().summary()
    console.print("\n[bold cyan]Operational Dashboard[/bold cyan]")
    for k, v in s.items():
        if isinstance(v, dict):
            parts = ", ".join(f"{kk}={vv}" for kk, vv in v.items())
            console.print(f"  {k}: {parts}")
        else:
            console.print(f"  {k}: {v}")
    _pause()


def search_flow() -> None:
    kw = _ask("Keyword (blank = all)")
    res = SearchService().search(keyword=kw or None)
    for etype, rows in res.items():
        if not rows:
            continue
        console.print(f"\n[bold]{etype.upper()}[/bold] ({len(rows)})")
        for r in rows[:10]:
            console.print(f"  [{r.get('id')}] {r.get('title') or r.get('date')}")


def excel_export_flow() -> None:
    console.print("Reports: bau, okr, incident, evidence, summary, management")
    report = _ask("Report", default="summary")
    try:
        path = ExcelService().export_report(report)
        console.print(f"[green]✓ Exported: {path}[/green]")
    except Exception as exc:
        console.print(f"[red]! {exc}[/red]")


def backup_flow() -> None:
    try:
        dest = BackupService().backup(label="menu")
        console.print(f"[green]✓ Backup: {dest}[/green]")
    except Exception as exc:
        console.print(f"[red]! {exc}[/red]")


def about_flow() -> None:
    from app import __version__
    console.print(f"\nOpsCollector-CLI v{__version__}")
    console.print("Capture Once. Report Everywhere.")
    console.print("Keyboard menu: Up/Down navigate, Left/Right column, Enter select, Esc back.\n")
    _pause()
