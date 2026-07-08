"""Configuration loading and path management.

All configuration originates from ``config.json`` at the project root, per the
PRD development standards. Paths are resolved relative to the project root so the
application stays portable (just copy the folder).
"""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

# Project root is the directory containing this file's grandparent (app/ -> repo root).
PROJECT_ROOT = Path(__file__).resolve().parents[2]
CONFIG_PATH = PROJECT_ROOT / "config.json"


class DatabaseConfig(BaseModel):
    filename: str = "opscollector.db"
    directory: str = "database"


class PathsConfig(BaseModel):
    evidence_dir: str = "evidence"
    export_dir: str = "export"
    backup_dir: str = "backup"
    logs_dir: str = "logs"
    templates_dir: str = "app/templates"


class EvidenceConfig(BaseModel):
    allowed_extensions: list[str] = Field(
        default_factory=lambda: ["png", "jpg", "jpeg", "pdf", "docx", "xlsx", "txt", "log", "zip"]
    )
    max_size_mb: int = 100


class LoggingConfig(BaseModel):
    level: str = "INFO"
    format: str = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"


class UIConfig(BaseModel):
    date_format: str = "%Y-%m-%d"
    datetime_format: str = "%Y-%m-%d %H:%M:%S"


class AppSettings(BaseModel):
    app_name: str = "OpsCollector-CLI"
    version: str = "1.0.0"
    database: DatabaseConfig = Field(default_factory=DatabaseConfig)
    paths: PathsConfig = Field(default_factory=PathsConfig)
    evidence: EvidenceConfig = Field(default_factory=EvidenceConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)
    ui: UIConfig = Field(default_factory=UIConfig)

    # --- Resolved path helpers (computed, not stored in JSON) ---
    @property
    def db_directory(self) -> Path:
        return PROJECT_ROOT / self.paths.database_directory if hasattr(self.paths, "database_directory") else PROJECT_ROOT / self.database.directory

    @property
    def db_path(self) -> Path:
        return self.db_directory / self.database.filename

    @property
    def evidence_dir(self) -> Path:
        return PROJECT_ROOT / self.paths.evidence_dir

    @property
    def export_dir(self) -> Path:
        return PROJECT_ROOT / self.paths.export_dir

    @property
    def backup_dir(self) -> Path:
        return PROJECT_ROOT / self.paths.backup_dir

    @property
    def logs_dir(self) -> Path:
        return PROJECT_ROOT / self.paths.logs_dir

    @property
    def templates_dir(self) -> Path:
        return PROJECT_ROOT / self.paths.templates_dir

    def ensure_directories(self) -> None:
        """Create all runtime directories if they do not exist."""
        for p in (
            self.db_directory,
            self.evidence_dir,
            self.export_dir,
            self.backup_dir,
            self.logs_dir,
            self.templates_dir,
        ):
            p.mkdir(parents=True, exist_ok=True)


@lru_cache(maxsize=1)
def get_settings() -> AppSettings:
    """Load and cache application settings from ``config.json``."""
    if not CONFIG_PATH.exists():
        # Fall back to defaults so the app can bootstrap itself on first run.
        return AppSettings()
    raw: dict[str, Any] = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    return AppSettings(**raw)


def reload_settings() -> AppSettings:
    """Clear the cache and reload settings from disk."""
    try:
        get_settings.cache_clear()
    except AttributeError:
        # get_settings may be replaced by a plain callable (e.g. in tests).
        pass
    return get_settings()
