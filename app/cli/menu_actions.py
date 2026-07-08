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
    from app.cli.record_browser import browse, BrowserSpec

    types = MasterService().list_types()
    entity = _ask("Entity type", default=types[0] if types else "")
    if not entity:
        return

    def load(limit, offset):
        return MasterService().list(entity, limit=limit, offset=offset)

    def summary(r):
        return r.get("name") or str(r.get("id"))

    def fields(r):
        items = [(k, v) for k, v in r.items() if k not in ("id",)]
        return items or [("id", r.get("id"))]

    def editable(r):
        out = [("name", "Name", r.get("name") or "")]
        if entity.lower() in ("objective", "key_result"):
            out.append(("title", "Title", r.get("title") or ""))
        return out

    browse(BrowserSpec(
        title=f"Master: {entity}",
        load=load, fields=fields, editable_fields=editable, summary=summary,
        save=lambda rid, ch: MasterService().update(entity, rid, **ch),
        delete=lambda rid: MasterService().delete(entity, rid),
    ))


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
    from app.cli.record_browser import browse, BrowserSpec

    def summary(r):
        return f"{r['date']} — {r['title']} [{r.get('status_id')}]"

    def fields(r):
        return [
            ("Date", r["date"]),
            ("Title", r["title"]),
            ("Description", r.get("description") or ""),
            ("Status ID", r.get("status_id")),
            ("PIC ID", r.get("pic_id")),
            ("Dept ID", r.get("department_id")),
        ]

    def editable(r):
        return [
            ("title", "Title", r["title"]),
            ("description", "Description", r.get("description") or ""),
            ("status_id", "Status ID", r.get("status_id") or ""),
            ("pic_id", "PIC ID", r.get("pic_id") or ""),
            ("department_id", "Dept ID", r.get("department_id") or ""),
        ]

    browse(BrowserSpec(
        title="Daily BAU",
        load=lambda limit, offset: BAUService().list(limit=limit, offset=offset),
        fields=fields, editable_fields=editable, summary=summary,
        save=lambda rid, ch: BAUService().update(rid, **{k: (int(v) if v.isdigit() else v) for k, v in ch.items()}),
        delete=lambda rid: BAUService().delete(rid),
    ))


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
    from app.cli.record_browser import browse, BrowserSpec

    def summary(r):
        return f"{r['date']} — {r['title']} ({r['severity']})"

    def fields(r):
        return [
            ("No", r.get("incident_no")),
            ("Date", r["date"]),
            ("Title", r["title"]),
            ("Severity", r["severity"]),
            ("Status ID", r.get("status_id")),
            ("PIC ID", r.get("pic_id")),
            ("Dept ID", r.get("department_id")),
        ]

    def editable(r):
        return [
            ("title", "Title", r["title"]),
            ("severity", "Severity", r["severity"]),
            ("description", "Description", r.get("description") or ""),
            ("root_cause", "Root cause", r.get("root_cause") or ""),
            ("resolution", "Resolution", r.get("resolution") or ""),
            ("status_id", "Status ID", r.get("status_id") or ""),
            ("pic_id", "PIC ID", r.get("pic_id") or ""),
            ("department_id", "Dept ID", r.get("department_id") or ""),
        ]

    browse(BrowserSpec(
        title="Incident",
        load=lambda limit, offset: IncidentService().list(limit=limit, offset=offset),
        fields=fields, editable_fields=editable, summary=summary,
        save=lambda rid, ch: IncidentService().update(rid, **{k: (int(v) if v.isdigit() else v) for k, v in ch.items()}),
        delete=lambda rid: IncidentService().delete(rid),
    ))


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
    from app.cli.record_browser import browse, BrowserSpec

    def summary(r):
        return f"{r['date']} — {r['title']} ({r.get('change_type')})"

    def fields(r):
        return [
            ("No", r.get("change_no")),
            ("Date", r["date"]),
            ("Title", r["title"]),
            ("Type", r.get("change_type")),
            ("Status ID", r.get("status_id")),
            ("PIC ID", r.get("pic_id")),
            ("Dept ID", r.get("department_id")),
        ]

    def editable(r):
        return [
            ("title", "Title", r["title"]),
            ("change_type", "Type", r.get("change_type") or ""),
            ("description", "Description", r.get("description") or ""),
            ("result", "Result", r.get("result") or ""),
            ("status_id", "Status ID", r.get("status_id") or ""),
            ("pic_id", "PIC ID", r.get("pic_id") or ""),
            ("department_id", "Dept ID", r.get("department_id") or ""),
        ]

    browse(BrowserSpec(
        title="Change / Maint.",
        load=lambda limit, offset: ChangeService().list(limit=limit, offset=offset),
        fields=fields, editable_fields=editable, summary=summary,
        save=lambda rid, ch: ChangeService().update(rid, **{k: (int(v) if v.isdigit() else v) for k, v in ch.items()}),
        delete=lambda rid: ChangeService().delete(rid),
    ))


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
    from app.cli.record_browser import browse, BrowserSpec

    def summary(r):
        return f"{r.get('title') or r['original_filename']} ({r['extension']})"

    def fields(r):
        return [
            ("Title", r.get("title") or r["original_filename"]),
            ("Original file", r["original_filename"]),
            ("Extension", r["extension"]),
            ("Size (bytes)", r.get("size_bytes")),
            ("Category ID", r.get("evidence_category_id")),
            ("Entity", f"{r.get('entity_type')}#{r.get('entity_id')}"),
            ("Uploaded", str(r.get("uploaded_at"))),
        ]

    def editable(r):
        return [
            ("title", "Title", r.get("title") or ""),
            ("description", "Description", r.get("description") or ""),
        ]

    browse(BrowserSpec(
        title="Evidence",
        load=lambda limit, offset: EvidenceService().list(limit=limit, offset=offset),
        fields=fields, editable_fields=editable, summary=summary,
        save=lambda rid, ch: EvidenceService().update(rid, **ch),
        delete=lambda rid: EvidenceService().delete(rid, remove_file=True),
    ))


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
    console.print("Keyboard menu: ↑↓ select, ←→ column, Enter open, Esc back/exit.")
    console.print("Shortcuts: F1 Help · F2 Save · F3 New · F4 Edit · F8 Delete · F9 Refresh.")
    _pause()
