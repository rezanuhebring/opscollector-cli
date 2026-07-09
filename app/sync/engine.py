"""Sync engine: offline-first push/pull orchestration."""

from __future__ import annotations

import json
from collections.abc import Callable

from app.core.config import get_settings
from app.sync.transport import SyncClient

PushPullClient = SyncClient | Callable[..., bool | list[dict] | None]

PILOT_ENTITIES = {"pic", "department", "status"}


def __now_iso__() -> str:
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).isoformat()


def push_pending(client: PushPullClient) -> int:
    """Send unsynced change rows; return count of newly synced rows.

    Offline-safe: returns 0 on network failure or bad response without raising.
    """
    from app.database.db import get_session
    from app.models import SyncLog
    from sqlalchemy import select

    settings = get_settings()
    with get_session() as session:
        rows = session.scalars(
            select(SyncLog).where(SyncLog.synced == 0).order_by(SyncLog.id)
        ).all()
        changes = [_serialize_row(r) for r in rows]

    if not changes:
        return 0

    ok = False
    if callable(getattr(client, "push", None)):
        ok = bool(client.push(changes))
    elif callable(client):
        ok = bool(client(changes))
    if not ok:
        return 0

    with get_session() as session:
        batch = session.query(SyncLog).filter(SyncLog.synced == 0).all()
        for row in batch:
            row.synced = 1
        settings.sync.last_push = __now_iso__()
    return len(batch)


def pull_updates(client: PushPullClient) -> int:
    """Pull server changes since last_pull; upsert reference entities.

    Offline-safe: returns 0 on network failure.
    """
    settings = get_settings()
    result = None
    try:
        if callable(getattr(client, "pull", None)):
            result = client.pull(settings.sync.last_pull, schema_version=1)
        elif callable(client):
            result = client(since=settings.sync.last_pull, schema_version=1)
    except Exception:
        result = None

    if not result:
        return 0

    changes = list(result) if isinstance(result, (list, tuple)) else []
    if not changes:
        with get_session() as session:
            settings.sync.last_pull = __now_iso__()
        return 0

    from app.services.master_service import MasterService

    svc = MasterService()
    upserted = 0
    for change in changes:
        entity = str(change.get("entity") or "").lower()
        if entity not in PILOT_ENTITIES:
            continue
        payload = change.get("payload") or {}
        row_id = _safe_int(change.get("row_id"))
        if row_id is None or payload.get("id") is None:
            continue
        try:
            if _exists(entity, row_id):
                svc.update(entity, row_id, **{k: v for k, v in payload.items() if k in ("name", "description")})
            else:
                svc.create(entity, **{k: v for k, v in payload.items() if k in ("name", "description")})
            upserted += 1
        except Exception:
            pass

    with get_session() as session:
        settings.sync.last_pull = __now_iso__()
    return upserted


def sync_once(client: PushPullClient) -> None:
    """Push pending then pull updates. Never raises on network errors."""
    try:
        push_pending(client)
    except Exception:
        pass

    try:
        pull_updates(client)
    except Exception:
        pass


def _serialize_row(row) -> dict:
    try:
        payload = json.loads(row.payload or "{}")
    except Exception:
        payload = {"_raw": row.payload}
    return {
        "entity": row.entity,
        "row_id": int(row.row_id),
        "op": row.op,
        "client_id": row.client_id,
        "version": int(row.version),
        "payload": payload,
        "base_schema_version": int(row.base_schema_version),
    }


def _safe_int(v):
    try:
        return int(v)
    except Exception:
        return None


def _exists(entity: str, row_id: int) -> bool:
    map_ = {
        "pic": __import__("app.models", fromlist=["PIC"]).PIC,
        "department": __import__("app.models", fromlist=["Department"]).Department,
        "status": __import__("app.models", fromlist=["Status"]).Status,
    }
    model = map_.get(entity)
    if model is None:
        return False
    from app.database.db import get_session
    with get_session() as session:
        return session.get(model, row_id) is not None
