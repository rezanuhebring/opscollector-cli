"""Centralised logging configuration.

Logging is initialised once from ``config.json``. All modules should call
:func:`get_logger` rather than creating their own handlers.
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path

from app.core.config import get_settings

_CONFIGURED = False


def _configure() -> None:
    global _CONFIGURED
    if _CONFIGURED:
        return

    settings = get_settings()
    level_name = settings.logging.level.upper()
    level = getattr(logging, level_name, logging.INFO)
    fmt = settings.logging.format

    # Ensure log directory exists.
    log_dir = settings.logs_dir
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / "opscollector.log"

    root = logging.getLogger("opscollector")
    root.setLevel(level)
    root.handlers.clear()

    formatter = logging.Formatter(fmt)

    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setFormatter(formatter)
    root.addHandler(file_handler)

    stream_handler = logging.StreamHandler(sys.stderr)
    stream_handler.setFormatter(formatter)
    # Keep stderr quiet by default; the CLI controls user-facing output via Rich.
    stream_handler.setLevel(logging.WARNING)
    root.addHandler(stream_handler)

    _CONFIGURED = True


def get_logger(name: str) -> logging.Logger:
    """Return a configured logger under the ``opscollector`` namespace."""
    _configure()
    if not name.startswith("opscollector"):
        name = f"opscollector.{name}"
    return logging.getLogger(name)
