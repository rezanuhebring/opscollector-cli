from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import select

from server.db import SessionLocal
from server.models import ChangeFeed, ConflictEvent, model_for
from server.config import settings


def _now() -> datetime:
    return datetime.now(timezone.utc)


def apply_change(change: dict, client) -> tuple[dict | None, dict | None]:
    """Apply a single change dict.

    Returns (accepted_change, rejected_or_conflict_payload_or_None).
    """
    entity = change.get("entity")
    row_id = change.get("row_id")
    op = change.get("op")
    payload = change.get("payload") or {}
    base_schema_version = change.get("base_schema_version")

    if entity not in model_for:
        return None, {"entity": entity, "row_id": row_id, "reason": f"unsupported entity {entity}"}
    model = model_for[entity]

    with SessionLocal() as db:
        incoming_updated = payload.get("updated_at") or _now().isoformat()

        dup = db.scalar(
            select(ChangeFeed).where(
                ChangeFeed.client_id == client.client_id,
                ChangeFeed.entity == entity,
                ChangeFeed.row_id == str(row_id),
                ChangeFeed.version == change.get("version"),
                ChangeFeed.op == op,
            )
        )
        if dup:
            return None, {"entity": entity, "row_id": row_id, "reason": "duplicate"}

        pk = int(row_id) if str(row_id).isdigit() else row_id
        existing = db.get(model, pk)

        if existing is None:
            row = model(
                id=pk,
                name=payload.get("name", ""),
                description=payload.get("description"),
                is_active=payload.get("is_active", True),
                updated_at=_now(),
                version=change.get("version", 1),
                schema_version=settings.SERVER_SCHEMA_VERSION,
                payload=payload,
            )
            db.add(row)
            event = _make_event(change, client, base_schema_version, db)
            db.add(event)
            db.commit()
            change["id"] = f"{entity}:{row_id}"
            return change, None

        if op == "delete":
            db.delete(existing)
            event = _make_event(change, client, base_schema_version, db)
            db.add(event)
            db.commit()
            change["id"] = f"{entity}:{row_id}"
            return change, None

        try:
            incoming_dt = datetime.fromisoformat(incoming_updated)
        except Exception:
            incoming_dt = _now()
        if incoming_dt.tzinfo is None:
            incoming_dt = incoming_dt.replace(tzinfo=timezone.utc)
        existing_dt = existing.updated_at
        if existing_dt is None:
            existing_dt = datetime.min.replace(tzinfo=timezone.utc)
        if existing_dt.tzinfo is None:
            existing_dt = existing_dt.replace(tzinfo=timezone.utc)

        incoming_version = change.get("version", existing.version)
        existing_version = existing.version

        if incoming_version > existing_version:
            existing.name = payload.get("name", existing.name)
            existing.description = payload.get("description", existing.description)
            existing.is_active = payload.get("is_active", existing.is_active)
            existing.updated_at = _now()
            existing.version = incoming_version
            existing.schema_version = settings.SERVER_SCHEMA_VERSION
            existing.payload = payload
            event = _make_event(change, client, base_schema_version, db)
            db.add(event)
            db.commit()
            change["id"] = f"{entity}:{row_id}"
            return change, None

        if incoming_version == existing_version:
            if payload != existing.payload:
                conflict = ConflictEvent(
                    entity=entity,
                    row_id=str(row_id),
                    winning_payload={
                        "id": existing.id,
                        "name": existing.name,
                        "description": existing.description,
                        "is_active": existing.is_active,
                        "version": existing.version,
                        "schema_version": existing.schema_version,
                    },
                    losing_payload=payload,
                    status="open",
                )
                db.add(conflict)
                event = _make_event(change, client, base_schema_version, db)
                db.add(event)
                db.commit()
                change["id"] = f"{entity}:{row_id}"
                comp = {
                    "entity": entity,
                    "row_id": row_id,
                    "conflict_id": conflict.id,
                    "reason": "diverged",
                    "status": "open",
                }
                return change, comp

            event = _make_event(change, client, base_schema_version, db)
            db.add(event)
            db.commit()
            change["id"] = f"{entity}:{row_id}"
            return change, None

        if incoming_version < existing_version:
            incoming_version = change.get("version", existing.version)
            existing_version = existing.version

            if incoming_version > existing_version:
                existing.name = payload.get("name", existing.name)
                existing.description = payload.get("description", existing.description)
                existing.is_active = payload.get("is_active", existing.is_active)
                existing.updated_at = _now()
                existing.version = incoming_version
                existing.schema_version = settings.SERVER_SCHEMA_VERSION
                existing.payload = payload
                event = _make_event(change, client, base_schema_version, db)
                db.add(event)
                db.commit()
                change["id"] = f"{entity}:{row_id}"
                return change, None

            if incoming_version < existing_version:
                rejected = {
                    "entity": entity,
                    "row_id": row_id,
                    "reason": "stale_version",
                    "existing_version": existing_version,
                    "incoming_version": incoming_version,
                }
                event = _make_event(change, client, base_schema_version, db)
                db.add(event)
                db.commit()
                return None, rejected

            if payload != existing.payload:
                conflict = ConflictEvent(
                    entity=entity,
                    row_id=str(row_id),
                    winning_payload={
                        "id": existing.id,
                        "name": existing.name,
                        "description": existing.description,
                        "is_active": existing.is_active,
                        "version": existing.version,
                        "schema_version": existing.schema_version,
                    },
                    losing_payload=payload,
                    status="open",
                )
                db.add(conflict)
                event = _make_event(change, client, base_schema_version, db)
                db.add(event)
                db.commit()
                change["id"] = f"{entity}:{row_id}"
                comp = {
                    "entity": entity,
                    "row_id": row_id,
                    "conflict_id": conflict.id,
                    "reason": "diverged",
                    "status": "open",
                }
                return change, comp

            event = _make_event(change, client, base_schema_version, db)
            db.add(event)
            db.commit()
            change["id"] = f"{entity}:{row_id}"
            return change, None

        event = _make_event(change, client, base_schema_version, db)
        db.add(event)
        db.commit()
        change["id"] = f"{entity}:{row_id}"
        return change, None


def _make_event(change, client, base_schema_version, db):
    return ChangeFeed(
        entity=change.get("entity"),
        row_id=str(change.get("row_id")),
        op=change.get("op"),
        client_id=client.client_id,
        version=change.get("version", 1),
        payload=change.get("payload") or {},
        base_schema_version=base_schema_version,
        updated_at=_now(),
        schema_version=settings.SERVER_SCHEMA_VERSION,
    )
