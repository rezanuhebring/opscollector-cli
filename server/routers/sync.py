from __future__ import annotations

import secrets
import hashlib
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from server.auth import validate_token
from server.conflict import apply_change
from server.config import settings
from server.db import SessionLocal
from server.models import ChangeFeed, SettingsKV, ConflictEvent

router = APIRouter()


class RegisterIn(BaseModel):
    client_name: Optional[str] = None


class ChangeIn(BaseModel):
    entity: str
    row_id: int
    op: str = Field(pattern="^(create|update|delete)$")
    client_id: str
    version: int
    payload: dict
    base_schema_version: int


class PushIn(BaseModel):
    changes: list[ChangeIn]


class ChangeOut(BaseModel):
    id: Optional[str] = None
    entity: str
    row_id: str
    op: str
    payload: dict
    received_at: Optional[str] = None


@router.post("/api/v1/push")
def push(request: Request, body: PushIn):
    auth = request.headers.get("authorization") or request.headers.get("Authorization")
    client = validate_token(auth)
    if client is None:
        raise HTTPException(status_code=401, detail="Unauthorized")

    if client.revoked:
        raise HTTPException(status_code=401, detail="Revoked")

    accepted = []
    rejected = []
    conflicts = []

    raw_changes = [c.model_dump() for c in body.changes]
    for ch in raw_changes:
        ch["row_id"] = str(ch.get("row_id"))
        if ch.get("base_schema_version", 0) < settings.SERVER_SCHEMA_VERSION - settings.ALLOWED_DRIFT:
            rejected.append({"entity": ch.get("entity"), "row_id": ch.get("row_id"), "reason": "schema_version too old"})
            continue
        applied, comp = apply_change(ch, client)
        if comp and isinstance(comp, dict) and comp.get("reason") == "diverged":
            conflicts.append(comp)
            # still count as accepted per minimal contract? keep accepted
            if applied:
                accepted.append(applied)
        elif comp and isinstance(comp, dict) and comp.get("reason"):
            rejected.append(comp)
        elif applied:
            accepted.append(applied)

    if conflicts:
        return JSONResponse(
            status_code=409,
            content={
                "accepted": accepted,
                "rejected": rejected,
                "conflicts": conflicts,
            },
        )

    return {"accepted": accepted, "rejected": rejected}


@router.get("/api/v1/pull")
def pull(request: Request, since: Optional[str] = None, schema_version: int | None = None):
    auth = request.headers.get("authorization") or request.headers.get("Authorization")
    client = validate_token(auth)
    if client is None:
        raise HTTPException(status_code=401, detail="Unauthorized")

    with SessionLocal() as db:
        sv_row = db.get(SettingsKV, "server_schema_version")
        required = int((sv_row.value if sv_row else str(settings.SERVER_SCHEMA_VERSION)))
        if schema_version is not None and schema_version < required - settings.ALLOWED_DRIFT:
            raise HTTPException(status_code=426, detail={"error": "schema_too_old", "min_required_schema_version": required})

        q = db.query(ChangeFeed)
        if since:
            try:
                t = datetime.fromisoformat(since)
                q = q.filter(ChangeFeed.updated_at > t)
            except Exception:
                q = q.filter(False)
        rows = q.order_by(ChangeFeed.updated_at.asc()).all()
        changes = []
        for r in rows:
            changes.append({
                "id": f"{r.entity}:{r.row_id}",
                "entity": r.entity,
                "row_id": r.row_id,
                "op": r.op,
                "payload": r.payload,
                "received_at": (r.updated_at.isoformat() if hasattr(r.updated_at, "isoformat") else str(r.updated_at)),
            })
        return {"schema_version": required, "changes": changes}


@router.get("/api/v1/entities/{entity}")
def list_entities(entity: str):
    from server.models import model_for
    try:
        m = model_for[entity]
    except KeyError:
        raise HTTPException(status_code=404, detail="unknown entity")
    with SessionLocal() as db:
        rows = db.query(m).all()
        data = []
        for row in rows:
            data.append({
                "id": row.id,
                "name": row.name,
                "description": row.description,
                "is_active": row.is_active,
                "updated_at": (row.updated_at.isoformat() if hasattr(row.updated_at, "isoformat") else str(row.updated_at)),
                "version": row.version,
                "schema_version": row.schema_version,
            })
        return data


@router.get("/api/v1/entities/{entity}/{row_id}")
def get_entity(entity: str, row_id: str):
    from server.models import model_for
    try:
        m = model_for[entity]
    except KeyError:
        raise HTTPException(status_code=404, detail="unknown entity")
    with SessionLocal() as db:
        row = db.get(m, row_id)
        if not row:
            raise HTTPException(status_code=404, detail="not found")
        return {
            "id": row.id,
            "name": row.name,
            "description": row.description,
            "is_active": row.is_active,
            "updated_at": (row.updated_at.isoformat() if hasattr(row.updated_at, "isoformat") else str(row.updated_at)),
            "version": row.version,
            "schema_version": row.schema_version,
        }
