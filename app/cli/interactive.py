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
from typing import Callable

# Canonical key tokens returned by _read_key().
UP = "UP"
DOWN = "DOWN"
LEFT = "LEFT"
RIGHT = "RIGHT"
ENTER = "ENTER"
ESC = "ESC"
CTRL_C = "CTRL_C"

# Legacy console scan codes (after the 0x00 / 0xe0 prefix).
_LEGACY = {"H": UP, "P": DOWN, "K": LEFT, "M": RIGHT}
# VT sequences (after the ESC [ prefix).
_VT = {"A": UP, "B": DOWN, "C": RIGHT, "D": LEFT}


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
        return _LEGACY.get(code, ch + code)
    # VT / ANSI sequence (Windows Terminal, ConPTY): ESC [ <letter>
    if ch == "\x1b":
        nxt = msvcrt.getwch()
        if nxt == "[":
            code = msvcrt.getwch()
            return _VT.get(code, ESC)
        # A lone ESC (not the start of a CSI sequence) -> treat as Esc.
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
    hint = "  \u2191\u2193 navigate   \u2190\u2192 column   Enter select   Esc back/exit"
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
    sys.stdout.write("\n  Press any key to continue...")
    sys.stdout.flush()
    msvcrt.getwch()
