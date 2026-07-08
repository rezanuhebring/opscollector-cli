"""CLI: Watch command (auto-ingest evidence from a shared folder)."""

from __future__ import annotations

import typer

from app.cli._console import console, info, success
from app.services.watcher_service import start_watcher

app = typer.Typer(help="File monitoring / auto-ingest", no_args_is_help=True)


@app.command("start")
def start(
    watch_dir: str = typer.Argument(..., help="Directory to watch for new files"),
    category_id: int = typer.Option(None, "--cat"),
    duration: float = typer.Option(0.0, "--duration", help="Seconds to run; 0 = until Ctrl+C"),
) -> None:
    """Watch a folder and auto-ingest new files as evidence."""
    info(f"Watching {watch_dir} (Ctrl+C to stop)...")
    try:
        start_watcher(watch_dir, category_id=category_id, stop_after=duration or None)
        if not duration:
            # Block until keyboard interrupt.
            try:
                import time
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                pass
        success("Watcher stopped")
    except KeyboardInterrupt:
        success("Watcher stopped")
