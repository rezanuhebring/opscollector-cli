"""File monitoring service (watchdog).

Watches a shared folder for new evidence files and automatically ingests them
into the evidence repository. Designed for future SharePoint/auto-upload
integration (Roadmap v2.0). Runs as a standalone observer; the CLI can start it
via a `watch` command if desired.
"""

from __future__ import annotations

import time
from pathlib import Path
from typing import Callable

from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

from app.core.config import get_settings
from app.core.exceptions import EvidenceError
from app.core.logging_config import get_logger
from app.services.evidence_service import EvidenceService

logger = get_logger("watcher")


class EvidenceWatcherHandler(FileSystemEventHandler):
    """Ingests newly created/modified files in the watched directory."""

    def __init__(self, evidence_service: EvidenceService, category_id: int | None = None):
        self.svc = evidence_service
        self.category_id = category_id

    def on_created(self, event) -> None:  # noqa: D401
        if event.is_directory:
            return
        self._ingest(Path(event.src_path))

    def _ingest(self, path: Path) -> None:
        try:
            data = self.svc.add_file(
                source_path=path,
                title=path.stem,
                evidence_category_id=self.category_id,
                uploaded_by="watcher",
            )
            logger.info("Auto-ingested %s -> evidence id=%s", path.name, data["id"])
        except EvidenceError as e:
            logger.warning("Skipped %s: %s", path.name, e)


def start_watcher(
    watch_dir: str | Path,
    *,
    category_id: int | None = None,
    stop_after: float | None = None,
    on_event: Callable[[Path], None] | None = None,
) -> Observer:
    """Start watching ``watch_dir`` and auto-ingest new files.

    If ``stop_after`` is set (seconds), the observer is stopped automatically
    (useful for tests/one-shot runs). Otherwise it runs until the process exits.
    """
    watch_path = Path(watch_dir)
    watch_path.mkdir(parents=True, exist_ok=True)

    handler = EvidenceWatcherHandler(EvidenceService(), category_id)
    if on_event is not None:
        orig = handler._ingest

        def _wrap(p: Path) -> None:
            orig(p)
            on_event(p)

        handler._ingest = _wrap  # type: ignore[method-assign]

    observer = Observer()
    observer.schedule(handler, str(watch_path), recursive=False)
    observer.start()
    logger.info("Watching %s for new evidence", watch_path)

    if stop_after is not None:
        try:
            time.sleep(stop_after)
        finally:
            observer.stop()
            observer.join()
    return observer
