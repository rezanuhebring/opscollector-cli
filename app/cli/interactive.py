"""Interactive keyboard-driven menu engine (Windows, zero dependencies).

Uses the native ``msvcrt`` console API so it works without extra packages and
matches the offline-first, portable goal of OpsCollector-CLI.

Controls
--------
- ``Up`` / ``Down``  -> move selection vertically
- ``Left`` / ``Right`` -> move selection horizontally (2-column layout)
- ``Enter``          -> select the highlighted item
- ``Esc``            -> go back one level (or exit at the root)

The engine is intentionally tiny and generic: it renders a list of
``MenuItem`` and dispatches a callback when an item is chosen.
"""

from __future__ import annotations

import msvcrt
import sys
from dataclasses import dataclass, field
from typing import Callable

# Windows virtual-key codes returned by msvcrt.getwch() in "extended" mode.
# Extended keys arrive as a two-byte sequence: 0x00 (or 0xe0) then the code.
_VK_UP = "\x00H"  # 0x48
_VK_DOWN = "\x00P"  # 0x50
_VK_LEFT = "\x00K"  # 0x4b
_VK_RIGHT = "\x00M"  # 0x4d
_VK_ESC = "\x1b"
_VK_ENTER = "\r"
_VK_CTRL_C = "\x03"


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
    """Read a single key, normalising extended keys into 2-char codes."""
    ch = msvcrt.getwch()
    if ch in ("\x00", "\xe0"):  # prefix for extended keys
        return ch + msvcrt.getwch()
    return ch


def _render(title: str, items: list[MenuItem], selected: int) -> None:
    sys.stdout.write("\x1b[2J\x1b[H")  # clear screen, home cursor
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
        if key == _VK_ESC:
            if items is top_items:
                return  # exit application
            return  # back to parent (caller loop)
        if key == _VK_ENTER:
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
        if key == _VK_DOWN:
            selected = (selected + 1) % len(items)
        elif key == _VK_UP:
            selected = (selected - 1) % len(items)
        elif key == _VK_RIGHT and cols == 2:
            if selected + 1 < len(items) and (selected % 2 == 0):
                selected += 1
        elif key == _VK_LEFT and cols == 2:
            if selected - 1 >= 0 and (selected % 2 == 1):
                selected -= 1
        elif key == _VK_CTRL_C:
            raise KeyboardInterrupt


def _pause() -> None:
    sys.stdout.write("\n  Press any key to continue...")
    sys.stdout.flush()
    msvcrt.getwch()
