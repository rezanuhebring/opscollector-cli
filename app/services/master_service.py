"""Master / reference data service.

Thin business layer over the master repositories. All reference entities share
a common shape, so we expose generic create/list/update/delete helpers keyed by
model. This keeps the CLI command layer small and consistent.
"""

from __future__ import annotations

from typing import Any

from sqlalchemy import select

from app.core.exceptions import DuplicateError, ValidationError
from app.database.db import get_session
from app.models import (
    BAUActivity,
    BAUCategory,
    ChangeCategory,
    Department,
    EvidenceCategory,
    IncidentCategory,
    KeyResult,
    Objective,
    PIC,
    Priority,
    Status,
)
from app.sync.capture import record_change

PILOT_ENTITIES = {"pic", "department", "status"}

# Master entity -> model mapping used by generic operations.
MASTER_MODELS: dict[str, type] = {
    "objective": Objective,
    "key_result": KeyResult,
    "bau_category": BAUCategory,
    "bau_activity": BAUActivity,
    "incident_category": IncidentCategory,
    "change_category": ChangeCategory,
    "evidence_category": EvidenceCategory,
    "department": Department,
    "pic": PIC,
    "priority": Priority,
    "status": Status,
}

# Fields that belong to each master model (for safe creation/update).
_MODEL_FIELDS: dict[type, list[str]] = {
    Objective: ["name", "title", "owner_id", "status_id", "start_date", "end_date", "progress", "description"],
    KeyResult: ["name", "objective_id", "target_value", "current_value", "unit", "status_id", "progress", "description"],
    BAUCategory: ["name", "description"],
    BAUActivity: ["name", "bau_category_id", "description"],
    IncidentCategory: ["name", "description"],
    ChangeCategory: ["name", "description"],
    EvidenceCategory: ["name", "description"],
    Department: ["name", "description"],
    PIC: ["name", "department_id", "email", "description"],
    Priority: ["name", "level", "description"],
    Status: ["name", "description"],
}


class MasterService:
    """Business operations for reference/master data."""

    def list_types(self) -> list[str]:
        return sorted(MASTER_MODELS.keys())

    def list(
        self,
        entity: str,
        *,
        active_only: bool = False,
        limit: int = 50,
        offset: int = 0,
    ) -> list[dict[str, Any]]:
        model = self._resolve(entity)
        with get_session() as session:
            stmt = select(model)
            if active_only:
                stmt = stmt.where(model.is_active == True)  # noqa: E712
            stmt = stmt.limit(limit).offset(offset)
            rows = session.scalars(stmt).all()
            return [_to_dict(r) for r in rows]

    def get(self, entity: str, entity_id: int) -> dict[str, Any]:
        model = self._resolve(entity)
        with get_session() as session:
            obj = session.get(model, entity_id)
            if obj is None:
                raise ValidationError(f"{entity} id={entity_id} not found")
            return _to_dict(obj)

    def create(self, entity: str, **fields: Any) -> dict[str, Any]:
        model = self._resolve(entity)
        allowed = set(_MODEL_FIELDS.get(model, ["name", "description"]))
        cleaned = {k: v for k, v in fields.items() if k in allowed and v is not None}
        if "name" in allowed and not cleaned.get("name"):
            raise ValidationError(f"{entity} requires a 'name'")
        with get_session() as session:
            # Duplicate guard on name for reference entities.
            existing = session.scalars(
                select(model).where(model.name == cleaned.get("name"))
            ).first() if "name" in cleaned else None
            if existing is not None:
                raise DuplicateError(f"{entity} '{cleaned.get('name')}' already exists")
            obj = model(**cleaned)  # type: ignore[call-arg]
            session.add(obj)
            session.commit()
            session.refresh(obj)
            data = _to_dict(obj)
        self._maybe_capture(entity, "create", data)
        return data

    def update(self, entity: str, entity_id: int, **fields: Any) -> dict[str, Any]:
        model = self._resolve(entity)
        allowed = set(_MODEL_FIELDS.get(model, ["name", "description"]))
        cleaned = {k: v for k, v in fields.items() if k in allowed and v is not None}
        with get_session() as session:
            obj = session.get(model, entity_id)
            if obj is None:
                raise ValidationError(f"{entity} id={entity_id} not found")
            for key, value in cleaned.items():
                setattr(obj, key, value)
            session.commit()
            session.refresh(obj)
            data = _to_dict(obj)
        self._maybe_capture(entity, "update", data)
        return data

    def delete(self, entity: str, entity_id: int) -> None:
        model = self._resolve(entity)
        with get_session() as session:
            obj = session.get(model, entity_id)
            if obj is None:
                raise ValidationError(f"{entity} id={entity_id} not found")
            session.delete(obj)
            session.commit()
        self._maybe_capture(entity, "delete", {"id": entity_id})

    def _maybe_capture(self, entity: str, op: str, data: dict[str, Any]) -> None:
        try:
            row_id = int(data.get("id") or data.get("row_id") or 0)
            record_change(entity, row_id, op, data)
        except Exception:
            pass

    # --- helpers ---
    def _resolve(self, entity: str) -> type:
        key = entity.lower()
        if key not in MASTER_MODELS:
            raise ValidationError(
                f"Unknown master entity '{entity}'. Valid: {', '.join(sorted(MASTER_MODELS))}"
            )
        return MASTER_MODELS[key]


def _to_dict(obj: Any) -> dict[str, Any]:
    """Convert an ORM row to a plain dict (safe for JSON/CLI output)."""
    data: dict[str, Any] = {}
    for col in obj.__table__.columns:  # type: ignore[attr-defined]
        data[col.name] = getattr(obj, col.name)
    return data
