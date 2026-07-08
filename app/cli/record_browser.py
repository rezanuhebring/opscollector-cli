"""Reusable keyboard-driven record browser (list -> view -> edit -> save).

One small widget powers every entity list in OpsCollector-CLI so the UX is
identical everywhere. It is driven by a declarative spec and talks to the
service layer through two thin callbacks (``load`` and ``save``); it never
imports a concrete service itself.

Lifecycle
---------
1. LIST  : a scrollable, selectable list of records (↑/↓, PgUp/PgDn, Enter).
2. DETAIL: the selected record's fields, read-only, with an action bar.
            Enter / F4 -> EDIT, F8 -> delete (with confirm), F3 -> new.
3. EDIT  : fields become editable, one at a time (or all at once); F2 saves,
            Esc cancels. Changes are sent to ``save`` and the list refreshes.

Function-key shortcuts (consistent across all modules)
------------------------------------------------------
F1 Help | F2 Save | F3 New | F4 Edit | F8 Delete | F9 Refresh | Enter Open | Esc Back
"""

from __future__ import annotations

import msvcrt
import sys

from rich.console import Console

from app.cli.interactive import (
    F1, F2, F3, F4, F8, F9, ESC, ENTER,
    _read_key, _show_help_overlay, GLOBAL_SHORTCUTS,
)

console = Console()

# Box drawing.
_TOP = "\u2554" + "\u2550" * 72 + "\u2557"
_BOT = "\u255a" + "\u2550" * 72 + "\u255d"
_SIDE = "\u2551"
_PTR = "\u25b6"


def _clear_screen() -> None:
    if sys.stdout.isatty():
        sys.stdout.write("\x1b[2J\x1b[H")


def _any_key_close() -> None:
    try:
        ch = msvcrt.getwch()
        if ch in ("\x00", "\xe0"):
            msvcrt.getwch()
        elif ch == "\x1b":
            if msvcrt.kbhit() and msvcrt.getwch() == "[":
                msvcrt.getwch()
    except Exception:
        pass


def _confirm(prompt: str) -> bool:
    console.print(f"\n[bold red]{prompt}[/bold red] [dim](y/N, Esc=no)[/dim]: ", end="")
    while True:
        ch = msvcrt.getwch()
        if ch in ("\x00", "\xe0"):
            msvcrt.getwch()
            continue
        if ch == "\x1b":
            return False
        if ch in ("y", "Y"):
            return True
        if ch in ("\r", "n", "N"):
            return False


def _edit_field(name: str, current: str) -> str | None:
    """Edit a single field; Esc cancels (returns sentinel ''? use None)."""
    from app.cli.menu_actions import _read_line  # local import to avoid cycle
    val = _read_line(f"{name}", default=current)
    return val  # None == cancelled


class BrowserSpec:
    """Declarative description of an entity for the browser."""

    def __init__(
        self,
        *,
        title: str,
        # load(limit, offset) -> list[dict]; each dict MUST contain 'id'.
        load,
        # fields(record) -> list[(label, value_str)] for detail/edit view.
        fields,
        # editable_fields(record) -> list[(field_key, label, current_value_str)].
        editable_fields,
        # save(record_id, {field_key: value}) -> dict (updated record).
        save,
        # optional: create() -> dict (new record) or None if cancelled.
        create=None,
        # optional: delete(record_id) -> None.
        delete=None,
        # optional: summary(record) -> str for the list row.
        summary=None,
        page_size: int = 15,
    ) -> None:
        self.title = title
        self.load = load
        self.fields = fields
        self.editable_fields = editable_fields
        self.save = save
        self.create = create
        self.delete = delete
        self.summary = summary or (lambda r: str(r.get("id")))
        self.page_size = page_size


def _render_list(spec: BrowserSpec, rows: list[dict], selected: int, offset: int, total_hint: str) -> None:
    _clear_screen()
    print(_TOP)
    print(f"{_SIDE}  {spec.title}  ({total_hint}){'':<45}{_SIDE}")
    print(_SIDE + "\u2550" * 72 + _SIDE)
    if not rows:
        print(f"{_SIDE}  [dim](no records — press F3 to add)[/dim]{'':<40}{_SIDE}")
    for i, r in enumerate(rows):
        ptr = _PTR if i == selected else " "
        line = f" {ptr} [{r.get('id')}] {spec.summary(r)}"
        print(f"{_SIDE}{line[:70].ljust(72)}{_SIDE}")
    print(_BOT)
    print("  ↑↓ select   Enter/DblClick open   F1 help  F3 new  F9 refresh  Esc back")


def _render_detail(spec: BrowserSpec, rec: dict, *, editing: bool = False, msg: str = "") -> None:
    _clear_screen()
    print(_TOP)
    print(f"{_SIDE}  {spec.title} #{rec.get('id')}{'':<52}{_SIDE}")
    print(_SIDE + "\u2550" * 72 + _SIDE)
    for label, value in spec.fields(rec):
        print(f"{_SIDE}  {label.ljust(22)}: {str(value)[:48].ljust(46)}{_SIDE}")
    print(_BOT)
    bar = "  F4 Edit" if not editing else "  F2 Save"
    bar += "   F8 Delete   F3 New   F1 Help   Esc " + ("cancel" if editing else "back")
    if msg:
        print(f"  {msg}")
    print(bar)


def browse(spec: BrowserSpec) -> None:
    """Run the browser loop for one entity. Returns when the user presses Esc."""
    offset = 0
    selected = 0
    while True:
        rows = spec.load(limit=spec.page_size, offset=offset) or []
        if not rows:
            selected = 0
        else:
            selected = max(0, min(selected, len(rows) - 1))
        _render_list(spec, rows, selected, offset, f"showing {offset+1}-{offset+len(rows)}")

        key = _read_key()
        if key == ESC:
            return
        if key == F1:
            _show_help_overlay(GLOBAL_SHORTCUTS)
            continue
        if key == F9:
            continue  # reload
        if key == F3 and spec.create:
            _do_create(spec)
            offset = 0
            selected = 0
            continue
        if key in (ENTER, F4) and rows:
            rec = rows[selected]
            if key == F4 and spec.editable_fields:
                _do_edit(spec, rec["id"])
            else:
                _do_detail(spec, rec["id"])
            continue
        if key == F8 and rows and spec.delete:
            rec = rows[selected]
            if _confirm(f"Delete #{rec['id']} {spec.summary(rec)}?"):
                try:
                    spec.delete(rec["id"])
                    console.print(f"[green]✓ deleted #{rec['id']}[/green]")
                except Exception as exc:  # pragma: no cover
                    console.print(f"[red]! {exc}[/red]")
                _any_key_close()
                # adjust paging if we deleted the last item on the page
                if selected >= len(rows) - 1 and offset > 0:
                    offset = max(0, offset - spec.page_size)
            continue
        # movement (list)
        if key in ("UP", "DOWN", "LEFT", "RIGHT"):
            if key == "DOWN":
                if selected + 1 < len(rows):
                    selected += 1
                elif len(rows) == spec.page_size:
                    offset += spec.page_size
                    selected = 0
            elif key == "UP":
                if selected > 0:
                    selected -= 1
                elif offset > 0:
                    offset -= spec.page_size
                    selected = spec.page_size - 1
            elif key in ("LEFT", "RIGHT"):
                pass  # single column list
            continue


def _do_detail(spec: BrowserSpec, rec_id: int) -> None:
    while True:
        rows = spec.load(limit=spec.page_size, offset=0)
        rec = next((r for r in rows if r.get("id") == rec_id), None)
        if rec is None:
            # fall back to a full load to find the record
            rec = next((r for r in (spec.load(limit=10000, offset=0) or []) if r.get("id") == rec_id), None)
        if rec is None:
            return
        _render_detail(spec, rec)
        key = _read_key()
        if key == ESC:
            return
        if key == F1:
            _show_help_overlay(GLOBAL_SHORTCUTS)
            continue
        if key == F4 and spec.editable_fields:
            _do_edit(spec, rec_id)
            continue
        if key == F3 and spec.create:
            _do_create(spec)
            return
        if key == F8 and spec.delete:
            if _confirm(f"Delete #{rec_id}?"):
                try:
                    spec.delete(rec_id)
                    console.print(f"[green]✓ deleted #{rec_id}[/green]")
                except Exception as exc:  # pragma: no cover
                    console.print(f"[red]! {exc}[/red]")
                _any_key_close()
            return


def _do_edit(spec: BrowserSpec, rec_id: int) -> None:
    rows = spec.load(limit=10000, offset=0) or []
    rec = next((r for r in rows if r.get("id") == rec_id), None)
    if rec is None:
        return
    changes: dict = {}
    editable = spec.editable_fields(rec)
    i = 0
    while True:
        _render_detail(spec, rec, editing=True, msg=f"Editing field {i+1}/{len(editable)} — Esc cancels all")
        key = _read_key()
        if key == ESC:
            if _confirm("Discard changes?"):
                return
            continue
        if key == F1:
            _show_help_overlay(GLOBAL_SHORTCUTS)
            continue
        if key == F2:
            if not changes:
                _render_detail(spec, rec, editing=True, msg="Nothing changed")
                _any_key_close()
                continue
            try:
                updated = spec.save(rec_id, changes)
                console.print(f"[green]✓ saved #{rec_id}[/green]")
                _any_key_close()
                return
            except Exception as exc:
                console.print(f"[red]! {exc}[/red]")
                _any_key_close()
                continue
        if key in (ENTER, "DOWN") and i < len(editable) - 1:
            i += 1
        elif key == "UP" and i > 0:
            i -= 1
        elif key in ("UP", "DOWN"):
            pass
        else:
            # edit current field
            key_, label_, current_ = editable[i]
            new_val = _edit_field(label_, str(current_))
            if new_val is None:
                continue
            if new_val != str(current_):
                changes[key_] = new_val


def _do_create(spec: BrowserSpec) -> None:
    if not spec.create:
        return
    try:
        rec = spec.create()
    except Exception as exc:
        console.print(f"[red]! {exc}[/red]")
        _any_key_close()
        return
    if rec:
        console.print(f"[green]✓ created #{rec.get('id')}[/green]")
        _any_key_close()
