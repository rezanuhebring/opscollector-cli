"""Interactive keyboard-driven menu engine (Windows, zero dependencies).

Uses the native ``msvcrt`` console API so it works without extra packages and
matches the offline-first, portable goal of OpsCollector-CLI.

Controls
--------
- ``Up`` / ``Down``  -> move selection vertically
- ``Left`` / ``Right`` -> move selection horizontally (2-column layout)
- ``Enter``          -> select the highlighted item
- ``Esc``            -> go back one level (or exit at the root)

Key decoding is robust to two encodings used by Windows consoles:
* Legacy conhost: arrow keys arrive as ``\\x00`` (or ``\\xe0``) + scan code.
* Windows Terminal / ConPTY (VT mode): arrow keys arrive as ``\\x1b[`` + letter.
Both are normalised to canonical tokens so the menu works in cmd.exe,
PowerShell, and Windows Terminal alike.
"""

from __future__ import annotations

import msvcrt
import sys
from dataclasses import dataclass, field
from typing import Callable, Sequence

# Canonical key tokens returned by _read_key().
UP = "UP"
DOWN = "DOWN"
LEFT = "LEFT"
RIGHT = "RIGHT"
ENTER = "ENTER"
ESC = "ESC"
CTRL_C = "CTRL_C"
# Function keys F1..F12
F1 = "F1"
F2 = "F2"
F3 = "F3"
F4 = "F4"
F5 = "F5"
F6 = "F6"
F7 = "F7"
F8 = "F8"
F9 = "F9"
F10 = "F10"
F11 = "F11"
F12 = "F12"

# Legacy console scan codes (after the 0x00 / 0xe0 prefix).
_LEGACY = {"H": UP, "P": DOWN, "K": LEFT, "M": RIGHT}
# VT sequences (after the ESC [ prefix).
_VT = {"A": UP, "B": DOWN, "C": RIGHT, "D": LEFT}

# Legacy conhost scan codes for the function keys (after 0x00/0xe0).
_LEGACY_F = {
    "\x3b": F1, "\x3c": F2, "\x3d": F3, "\x3e": F4, "\x3f": F5, "\x40": F6,
    "\x41": F7, "\x42": F8, "\x43": F9, "\x44": F10, "\x85": F11, "\x86": F12,
}
# SS3 sequences (after the ESC O prefix): F1..F4.
_SS3_F = {"P": F1, "Q": F2, "R": F3, "S": F4}
# CSI sequences (after the ESC [ prefix) for F5..F12: "<n>~".
_CSI_F = {"15": F5, "17": F6, "18": F7, "19": F8, "20": F9, "21": F10,
          "23": F11, "24": F12}


@dataclass
class MenuItem:
    label: str
    description: str = ""
    on_select: Callable[[], None] = lambda: None
    # Optional sub-menu: list of MenuItems shown when this item is chosen.
    submenu: list["MenuItem"] | None = None


# Box drawing characters for a clean retro-style frame.
_TOP = "\u2554" + "\u2550" * 56 + "\u2557"
_BOT = "\u255a" + "\u2550" * 56 + "\u255d"
_SIDE = "\u2551"
_PTR = "\u25b6"  # ▶
_BLANK_PTR = " "


def _read_key() -> str:
    """Read a single key, normalising extended/VT keys to canonical tokens.

    Returns one of the canonical tokens (UP/DOWN/LEFT/RIGHT/ENTER/ESC/CTRL_C)
    or the literal character typed.
    """
    ch = msvcrt.getwch()
    # Legacy extended key: 0x00 or 0xe0 prefix followed by a scan code.
    if ch in ("\x00", "\xe0"):
        code = msvcrt.getwch()
        if code in _LEGACY_F:
            return _LEGACY_F[code]
        return _LEGACY.get(code, ch + code)
    # VT / ANSI sequence (Windows Terminal, ConPTY): ESC O <code> or ESC [ ...
    if ch == "\x1b":
        nxt = msvcrt.getwch()
        if nxt == "O":  # SS3: function keys F1..F4
            code = msvcrt.getwch()
            return _SS3_F.get(code, ESC)
        if nxt == "[":
            code = msvcrt.getwch()
            if code in _VT:
                return _VT[code]
            # Collect the numeric prefix of a CSI sequence (e.g. "15~").
            digits = code if code.isdigit() else ""
            while True:
                after = msvcrt.getwch()
                if after == "~":
                    return _CSI_F.get(digits, ESC)
                if after.isdigit():
                    digits += after
                else:
                    return ESC
        # Any other ESC sequence (e.g. lone ESC followed by another char).
        return ESC
    if ch == "\r":
        return ENTER
    if ch == "\x03":
        return CTRL_C
    return ch


def _render(title: str, items: list[MenuItem], selected: int) -> None:
    if sys.stdout.isatty():
        sys.stdout.write("\x1b[2J\x1b[H")  # clear screen, home cursor (VT)
    print(_TOP)
    header = f"  {title}"
    print(f"{_SIDE}{header.ljust(56)}{_SIDE}")
    print(_SIDE + "\u2550" * 56 + _SIDE)
    # Two-column layout when there are enough items.
    cols = 2 if len(items) > 6 else 1
    if cols == 1:
        for i, it in enumerate(items):
            ptr = _PTR if i == selected else _BLANK_PTR
            line = f" {ptr} {it.label}"
            print(f"{_SIDE}{line.ljust(56)}{_SIDE}")
    else:
        for row in range(0, len(items), 2):
            left = items[row]
            right = items[row + 1] if row + 1 < len(items) else None
            lp = (_PTR + " " + left.label) if row == selected else ("  " + left.label)
            if right is None:
                cell = lp.ljust(27)
            else:
                rp = (_PTR + " " + right.label) if row + 1 == selected else ("  " + right.label)
                cell = lp.ljust(27) + " " + rp.ljust(27)
            print(f"{_SIDE}{cell.ljust(56)}{_SIDE}")
    print(_BOT)
    hint = "  ↑↓ navigate   ←→ column   Enter open   F1 help   Esc back/exit"
    print(f"{hint}")


def run_menu(title: str, items: list[MenuItem]) -> None:
    """Render a menu and dispatch until the user backs out of the root."""
    _navigate(title, items, top_items=items)


def _navigate(title: str, items: list[MenuItem], *, top_items: list[MenuItem]) -> None:
    selected = 0
    cols = 2 if len(items) > 6 else 1
    while True:
        _render(title, items, selected)
        key = _read_key()
        if key == ESC:
            return  # back to parent (or exit at root)
        if key == F1:
            _show_help_overlay(GLOBAL_SHORTCUTS)
            continue
        if key == ENTER:
            item = items[selected]
            if item.submenu:
                _navigate(item.label, item.submenu, top_items=top_items)
            else:
                try:
                    item.on_select()
                except Exception as exc:  # pragma: no cover - defensive UI guard
                    print(f"\n  [Error] {exc}")
                    _pause()
            # After an action, return to this same menu.
            _pause()
            continue
        # movement
        if key == DOWN:
            selected = (selected + 1) % len(items)
        elif key == UP:
            selected = (selected - 1) % len(items)
        elif key == RIGHT and cols == 2:
            if selected + 1 < len(items) and (selected % 2 == 0):
                selected += 1
        elif key == LEFT and cols == 2:
            if selected - 1 >= 0 and (selected % 2 == 1):
                selected -= 1
        elif key == CTRL_C:
            raise KeyboardInterrupt


def _pause() -> None:
    sys.stdout.write("\n  Press any key to continue (Esc to skip)...")
    sys.stdout.flush()
    try:
        ch = msvcrt.getwch()
        # Drain any extended/VT sequence so it doesn't leak into the next read.
        if ch in ("\x00", "\xe0"):
            msvcrt.getwch()
        elif ch == "\x1b" and msvcrt.kbhit() and msvcrt.getwch() == "[":
            msvcrt.getwch()
    except Exception:
        pass


# Standard function-key shortcuts, reusable across every module.
GLOBAL_SHORTCUTS: list[tuple[str, str]] = [
    ("F1", "Help"),
    ("F2", "Save"),
    ("F3", "New / Add"),
    ("F4", "Edit"),
    ("F8", "Delete"),
    ("F9", "Refresh"),
    ("Enter", "Open / Select"),
    ("Esc", "Back / Cancel / Exit"),
]

# Box used by the help overlay.
_HTOP = "\u2554" + "\u2550" * 56 + "\u2557"
_HBOT = "\u255a" + "\u2550" * 56 + "\u255d"


def _show_help_overlay(shortcuts: Sequence[tuple[str, str]] = GLOBAL_SHORTCUTS) -> None:
    """Render a full-screen keyboard-shortcut help overlay. Any key closes it."""
    if sys.stdout.isatty():
        sys.stdout.write("\x1b[2J\x1b[H")
    print(_HTOP)
    print(f"{_SIDE}  Keyboard Shortcuts{'':<42}{_SIDE}")
    print(_SIDE + "\u2550" * 56 + _SIDE)
    for key, desc in shortcuts:
        print(f"{_SIDE}  {key.ljust(8)}{desc.ljust(45)}{_SIDE}")
    print(_HBOT)
    print("  Press any key to close...")
    sys.stdout.flush()
    try:
        ch = msvcrt.getwch()
        if ch in ("\x00", "\xe0"):
            msvcrt.getwch()
        elif ch == "\x1b" and msvcrt.kbhit() and msvcrt.getwch() == "[":
            msvcrt.getwch()
    except Exception:
        pass



