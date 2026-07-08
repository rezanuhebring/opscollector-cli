"""Database engine, session management, and initialisation.

The application is SQLite-backed and offline-first. A single engine is created
lazily and shared process-wide. Sessions are produced via
:func:`get_session` (context-managed) or used as a dependency in the service layer.
"""

from __future__ import annotations

from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import get_settings
from app.core.exceptions import ConfigurationError

_engine: Engine | None = None
_SessionFactory: sessionmaker | None = None


def _build_engine() -> Engine:
    settings = get_settings()
    settings.ensure_directories()
    db_path: Path = settings.db_path
    # check_same_thread=False so the CLI (single thread) and any background
    # watcher can share the connection pool safely for our read/write patterns.
    engine = create_engine(
        f"sqlite:///{db_path.as_posix()}",
        echo=False,
        future=True,
        connect_args={"check_same_thread": False},
    )
    return engine


def get_engine() -> Engine:
    """Return the process-wide engine, creating it on first use."""
    global _engine
    if _engine is None:
        _engine = _build_engine()
    return _engine


def get_session_factory() -> sessionmaker:
    """Return a cached sessionmaker bound to the engine."""
    global _SessionFactory
    if _SessionFactory is None:
        _SessionFactory = sessionmaker(bind=get_engine(), expire_on_commit=False, future=True)
    return _SessionFactory


@contextmanager
def get_session() -> Iterator[Session]:
    """Yield a transactional session. Commits on success, rolls back on error."""
    factory = get_session_factory()
    session = factory()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def init_db() -> None:
    """Create all tables (idempotent) and seed mandatory reference data."""
    from app.core.logging_config import get_logger
    from app.database.seed import seed_reference_data
    from app.models import Base

    engine = get_engine()
    Base.metadata.create_all(engine)
    get_logger("database").info("Database initialised at %s", get_settings().db_path)
    seed_reference_data()


def reset_engine() -> None:
    """Drop the cached engine (used in tests after changing the DB file)."""
    global _engine, _SessionFactory
    _engine = None
    _SessionFactory = None
