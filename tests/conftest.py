"""Pytest configuration: isolated SQLite database for every test.

Strategy
--------
``app.core.config.get_settings`` is the single configuration seam. Because every
consumer imports it as ``from app.core.config import get_settings`` (a name
binding), patching it on the *source* module is insufficient. Instead we replace
the function object on ``app.core.config`` *and* on every module that has already
bound the name, then point the database engine at a temp SQLite file.

No production code is modified; this file lives only in ``tests/``.
"""

from __future__ import annotations

import types
from pathlib import Path

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import get_settings as _real_get_settings
from app.models import Base


def _make_fake_settings(db_file: Path, tmp: Path) -> types.SimpleNamespace:
    real = _real_get_settings()
    return types.SimpleNamespace(
        app_name=real.app_name,
        version=real.version,
        database=types.SimpleNamespace(filename=db_file.name, directory="database"),
        db_directory=tmp,
        db_path=db_file,
        paths=types.SimpleNamespace(
            evidence_dir="evidence",
            export_dir="export",
            backup_dir="backup",
            logs_dir="logs",
            templates_dir="templates",
        ),
        evidence_dir=tmp / "evidence",
        export_dir=tmp / "export",
        backup_dir=tmp / "backup",
        logs_dir=tmp / "logs",
        templates_dir=tmp / "templates",
        evidence=types.SimpleNamespace(
            allowed_extensions=["png", "jpg", "jpeg", "pdf", "docx", "xlsx", "txt", "log", "zip"],
            max_size_mb=100,
        ),
        logging=types.SimpleNamespace(level="INFO", format="%(message)s"),
        ui=types.SimpleNamespace(date_format="%Y-%m-%d", datetime_format="%Y-%m-%d %H:%M:%S"),
        ensure_directories=lambda: None,
    )


@pytest.fixture(autouse=True)
def _isolated_db(monkeypatch, tmp_path: Path):
    import app.core.config as core_config
    import app.database.db as db_mod
    import app.services.backup_service as backup_mod
    import app.services.evidence_service as evidence_mod
    import app.services.excel_service as excel_mod

    db_file = tmp_path / "opscollector.db"
    engine = create_engine(
        f"sqlite:///{db_file.as_posix()}",
        echo=False,
        future=True,
        connect_args={"check_same_thread": False},
    )
    factory = sessionmaker(bind=engine, expire_on_commit=False, future=True)
    settings = _make_fake_settings(db_file, tmp_path)

    # Point the database layer at the temp engine.
    monkeypatch.setattr(db_mod, "_engine", engine)
    monkeypatch.setattr(db_mod, "_SessionFactory", factory)
    monkeypatch.setattr(db_mod, "get_engine", lambda: engine)
    monkeypatch.setattr(db_mod, "get_session_factory", lambda: factory)

    # Patch the configuration seam for every module that consumes it.
    monkeypatch.setattr(core_config, "get_settings", lambda: settings)
    monkeypatch.setattr(evidence_mod, "get_settings", lambda: settings)
    monkeypatch.setattr(backup_mod, "get_settings", lambda: settings)
    monkeypatch.setattr(excel_mod, "get_settings", lambda: settings)

    Base.metadata.create_all(engine)
    # Seed reference data directly to avoid re-entering init_db's logging path.
    from app.database.seed import seed_reference_data
    from app.models import KeyResult, Objective
    from app.services.master_service import MasterService

    seed_reference_data()
    master = MasterService()
    obj = master.create("objective", name="Test Objective", title="TO")
    master.create(
        "key_result", name="Test KR", objective_id=obj["id"], target_value=100.0
    )
    yield
