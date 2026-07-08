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


def _read_line(prompt: str, *, default: str = "") -> str | None:
    """Read a line via msvcrt; return None if the user presses Esc to cancel.

    Unlike ``input()``, this lets the keyboard menu honour Esc for cancel at
    any prompt, and still reads arrow-key sequences without echoing garbage.
    """
    console.print(f"[cyan]{prompt}[/cyan]", end="")
    if default:
        console.print(f" [dim]({default})[/dim]", end="")
    console.print(": ", end="")
    buf: list[str] = []
    esc_mode = False
    while True:
        ch = msvcrt.getwch()
        if ch in ("\x00", "\xe0"):  # legacy extended key — discard scan code
            msvcrt.getwch()
            continue
        if ch == "\x1b":  # lone ESC (cancel) or start of a VT sequence
            nxt = msvcrt.getwch() if msvcrt.kbhit() else ""
            if nxt == "[":  # arrow/etc — discard the rest of the sequence
                msvcrt.getwch()
                continue
            console.print()  # user cancelled
            return None
        if ch == "\r":  # Enter
            console.print()
            val = "".join(buf).strip()
            return val or default
        if ch == "\x08":  # Backspace
            if buf:
                buf.pop()
                console.print("\b \b", end="")
        elif ch.isprintable():
            buf.append(ch)
            console.print(ch, end="")
        # ignore other control chars (Ctrl-C handled by runtime)


def _ask(prompt: str, *, default: str = "") -> str:
    """Prompt for a line of text. Returns empty string if cancelled with Esc."""
    val = _read_line(prompt, default=default)
    if val is None:
        console.print("[yellow]! cancelled[/yellow]")
        return ""
    return val


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


def bau_list_flow() -> None:
    rows = BAUService().list(limit=25)
    if not rows:
        console.print("[dim](no BAU records)[/dim]")
        return
    for r in rows:
        console.print(f"  [{r['id']}] {r['date']} — {r['title']} [{r.get('status_id')}]")


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


def incident_list_flow() -> None:
    rows = IncidentService().list(limit=25)
    if not rows:
        console.print("[dim](no incidents)[/dim]")
        return
    for r in rows:
        console.print(f"  [{r['id']}] {r['date']} — {r['title']} ({r['severity']})")


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


def change_list_flow() -> None:
    rows = ChangeService().list(limit=25)
    if not rows:
        console.print("[dim](no changes)[/dim]")
        return
    for r in rows:
        console.print(f"  [{r['id']}] {r['date']} — {r['title']} ({r.get('change_type')})")


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


def evidence_list_flow() -> None:
    rows = EvidenceService().list(limit=25)
    if not rows:
        console.print("[dim](no evidence)[/dim]")
        return
    for r in rows:
        console.print(f"  [{r['id']}] {r.get('title') or r['original_filename']} ({r['extension']})")


# --- CRUD submenu flows --------------------------------------------------
def _pick_id(rows: list[dict], label: str) -> int | None:
    """Let the user choose a record id from a list view; None if cancelled."""
    if not rows:
        console.print("[dim](no records)[/dim]")
        return None
    for r in rows[:25]:
        rid = r.get("id")
        summary = r.get("title") or r.get("date") or r.get("name") or rid
        console.print(f"  [{rid}] {summary}")
    raw = _ask_int(f"{label} ID (Esc to cancel)")
    if raw is None:
        return None
    return raw


def _confirm(prompt: str) -> bool:
    ans = _read_line(prompt + " [y/N]")
    if ans is None:
        return False
    return ans.strip().lower() in ("y", "yes")


def incident_edit_flow() -> None:
    rows = IncidentService().list(limit=50)
    iid = _pick_id(rows, "Incident")
    if iid is None:
        return
    title = _ask("Title")
    severity = _ask("Severity", default="Medium")
    desc = _ask("Description")
    fields = {}
    if title:
        fields["title"] = title
    if severity:
        fields["severity"] = severity
    if desc:
        fields["description"] = desc
    if not fields:
        console.print("[yellow]! nothing to change[/yellow]")
        return
    try:
        rec = IncidentService().update(iid, **fields)
        console.print(f"[green]✓ Incident {rec['incident_no']} updated[/green]")
    except Exception as exc:
        console.print(f"[red]! {exc}[/red]")


def incident_delete_flow() -> None:
    rows = IncidentService().list(limit=50)
    iid = _pick_id(rows, "Incident")
    if iid is None:
        return
    if not _confirm(f"Delete incident #{iid}?"):
        console.print("[dim]cancelled[/dim]")
        return
    try:
        IncidentService().delete(iid)
        console.print(f"[green]✓ Incident #{iid} deleted[/green]")
    except Exception as exc:
        console.print(f"[red]! {exc}[/red]")


def bau_edit_flow() -> None:
    rows = BAUService().list(limit=50)
    bid = _pick_id(rows, "BAU")
    if bid is None:
        return
    title = _ask("Title")
    desc = _ask("Description")
    status_id = _ask_int("Status ID", default=0)
    fields = {}
    if title:
        fields["title"] = title
    if desc:
        fields["description"] = desc
    if status_id:
        fields["status_id"] = status_id
    if not fields:
        console.print("[yellow]! nothing to change[/yellow]")
        return
    try:
        rec = BAUService().update(bid, **fields)
        console.print(f"[green]✓ BAU #{rec['id']} updated[/green]")
    except Exception as exc:
        console.print(f"[red]! {exc}[/red]")


def bau_delete_flow() -> None:
    rows = BAUService().list(limit=50)
    bid = _pick_id(rows, "BAU")
    if bid is None:
        return
    if not _confirm(f"Delete BAU #{bid}?"):
        console.print("[dim]cancelled[/dim]")
        return
    try:
        BAUService().delete(bid)
        console.print(f"[green]✓ BAU #{bid} deleted[/green]")
    except Exception as exc:
        console.print(f"[red]! {exc}[/red]")


def change_edit_flow() -> None:
    rows = ChangeService().list(limit=50)
    cid = _pick_id(rows, "Change")
    if cid is None:
        return
    title = _ask("Title")
    ctype = _ask("Change type", default="Change")
    desc = _ask("Description")
    fields = {}
    if title:
        fields["title"] = title
    if ctype:
        fields["change_type"] = ctype
    if desc:
        fields["description"] = desc
    if not fields:
        console.print("[yellow]! nothing to change[/yellow]")
        return
    try:
        rec = ChangeService().update(cid, **fields)
        console.print(f"[green]✓ Change #{rec['id']} updated[/green]")
    except Exception as exc:
        console.print(f"[red]! {exc}[/red]")


def change_delete_flow() -> None:
    rows = ChangeService().list(limit=50)
    cid = _pick_id(rows, "Change")
    if cid is None:
        return
    if not _confirm(f"Delete change #{cid}?"):
        console.print("[dim]cancelled[/dim]")
        return
    try:
        ChangeService().delete(cid)
        console.print(f"[green]✓ Change #{cid} deleted[/green]")
    except Exception as exc:
        console.print(f"[red]! {exc}[/red]")


def evidence_delete_flow() -> None:
    rows = EvidenceService().list(limit=50)
    eid = _pick_id(rows, "Evidence")
    if eid is None:
        return
    if not _confirm(f"Delete evidence #{eid} (removes file)?"):
        console.print("[dim]cancelled[/dim]")
        return
    try:
        EvidenceService().delete(eid, remove_file=True)
        console.print(f"[green]✓ Evidence #{eid} deleted[/green]")
    except Exception as exc:
        console.print(f"[red]! {exc}[/red]")


def master_edit_flow() -> None:
    types = MasterService().list_types()
    console.print("[bold]Master entities:[/bold] " + ", ".join(types))
    entity = _ask("Entity type")
    if not entity:
        return
    rows = MasterService().list(entity)
    mid = _pick_id(rows, entity)
    if mid is None:
        return
    name = _ask("Name")
    extra: dict = {}
    if entity.lower() in ("objective", "key_result"):
        extra["title"] = _ask("Title")
    fields = {}
    if name:
        fields["name"] = name
    fields.update({k: v for k, v in extra.items() if v})
    if not fields:
        console.print("[yellow]! nothing to change[/yellow]")
        return
    try:
        rec = MasterService().update(entity, mid, **fields)
        console.print(f"[green]✓ {entity} #{rec['id']} updated[/green]")
    except Exception as exc:
        console.print(f"[red]! {exc}[/red]")


def master_delete_flow() -> None:
    types = MasterService().list_types()
    console.print("[bold]Master entities:[/bold] " + ", ".join(types))
    entity = _ask("Entity type")
    if not entity:
        return
    rows = MasterService().list(entity)
    mid = _pick_id(rows, entity)
    if mid is None:
        return
    if not _confirm(f"Delete {entity} #{mid}?"):
        console.print("[dim]cancelled[/dim]")
        return
    try:
        MasterService().delete(entity, mid)
        console.print(f"[green]✓ {entity} #{mid} deleted[/green]")
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


def load_demo_flow() -> None:
    from app.database.seed import force_seed_demo_data, seed_reference_data

    try:
        seed_reference_data()
        added = force_seed_demo_data()
        console.print(f"[green]✓ Demo data loaded ({added} incidents inserted)[/green]")
    except Exception as exc:
        console.print(f"[red]! {exc}[/red]")


def excel_import_flow() -> None:
    console.print("Entities: daily_bau, okr_progress, incident, change, <master type e.g. department>")
    file_path = _ask("Excel/CSV file path")
    if not file_path or not os.path.exists(file_path):
        console.print("[yellow]! file not found[/yellow]")
        return
    entity = _ask("Entity")
    if not entity:
        return
    try:
        res = ExcelService().import_sheet(file_path, entity)
        console.print(
            f"[green]✓ Imported {res['created']} of {res['rows_read']} rows "
            f"({len(res['errors'])} errors)[/green]"
        )
        for err in res["errors"][:10]:
            console.print(f"  [red]row {err['row']}: {err['error']}[/red]")
    except Exception as exc:
        console.print(f"[red]! {exc}[/red]")


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
