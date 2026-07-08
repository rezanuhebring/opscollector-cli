"""Backup & Restore service.

Produces timestamped backups of the SQLite database, config, and the export
directory. Supports full restore and selective restore of individual artifacts.
"""

from __future__ import annotations

import json
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any

from app.core.config import get_settings
from app.core.exceptions import OpsCollectorError
from app.core.logging_config import get_logger

logger = get_logger("backup")


class BackupService:
    """Create and restore application backups."""

    def backup(self, *, label: str | None = None) -> Path:
        settings = get_settings()
        settings.ensure_directories()
        stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        name = f"backup-{stamp}" + (f"-{label}" if label else "")
        dest = settings.backup_dir / name
        dest.mkdir(parents=True, exist_ok=True)

        # Database
        db_src = settings.db_path
        if db_src.exists():
            shutil.copy2(db_src, dest / db_src.name)

        # Config
        from app.core.config import PROJECT_ROOT
        shutil.copy2(PROJECT_ROOT / "config.json", dest / "config.json")

        # Export dir (copied, not moved)
        if settings.export_dir.exists():
            shutil.copytree(settings.export_dir, dest / "export", dirs_exist_ok=True)

        manifest = {
            "created_at": stamp,
            "label": label,
            "version": settings.version,
            "contents": ["database", "config", "export"],
        }
        (dest / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
        logger.info("Backup created at %s", dest)
        return dest

    def list_backups(self) -> list[dict[str, Any]]:
        settings = get_settings()
        if not settings.backup_dir.exists():
            return []
        out = []
        for d in sorted(settings.backup_dir.iterdir(), reverse=True):
            if d.is_dir():
                manifest = d / "manifest.json"
                info: dict[str, Any] = {"name": d.name, "path": str(d)}
                if manifest.exists():
                    info.update(json.loads(manifest.read_text(encoding="utf-8")))
                out.append(info)
        return out

    def restore(self, *, backup_name: str, selective: list[str] | None = None) -> None:
        from app.core.config import PROJECT_ROOT, reload_settings
        from app.database.db import reset_engine

        settings = get_settings()
        settings.ensure_directories()
        src = settings.backup_dir / backup_name
        if not src.exists() or not src.is_dir():
            raise OpsCollectorError(f"Backup '{backup_name}' not found")

        targets = selective or ["database", "config", "export"]

        if "database" in targets:
            db_file = src / settings.database.filename
            if db_file.exists():
                # Close any open engine first.
                reset_engine()
                shutil.copy2(db_file, settings.db_path)

        if "config" in targets:
            cfg = src / "config.json"
            if cfg.exists():
                shutil.copy2(cfg, PROJECT_ROOT / "config.json")
                reload_settings()

        if "export" in targets:
            export_src = src / "export"
            if export_src.exists():
                shutil.copytree(export_src, settings.export_dir, dirs_exist_ok=True)

        logger.info("Restored backup %s (targets=%s)", backup_name, targets)
