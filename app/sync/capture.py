"""Sync change-capture helper.

Appends change records to ``sync_log`` using a fresh session so capture
failures cannot break local writes. Service layers should call these inside
``try/except`` blocks as needed.
"""

from __future__ import annotations

import json
from contextlib import contextmanager
from datetime import datetime, timezone
from typing import Any

from app.core.config import get_settings
from app.database.db import get_engine
from app.models import SyncLog


@contextmanager
def _fresh_session():
    from sqlalchemy.orm import sessionmaker

    factory = sessionmaker(bind=get_engine(), expire_on_commit=False, future=True)
    session = factory()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def record_change(
    entity: str,
    row_id: int,
    op: str,
    payload_dict: dict[str, Any],
    *,
    base_schema_version: int = 1,
    version: int = 1,
) -> None:
    settings = get_settings()

    row = SyncLog(
        entity=entity,
        row_id=int(row_id),
        op=op,
        client_id=settings.client_id or "",
        version=version,
        payload=json.dumps(payload_dict, default=str, sort_keys=True),
        base_schema_version=int(base_schema_version),
        created_at=datetime.now(timezone.utc),
        synced=0,
    )

    with _fresh_session() as session:
        session.add(row)
