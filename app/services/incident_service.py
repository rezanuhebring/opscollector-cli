"""Incident service: business logic for operational incident logging."""

from __future__ import annotations

import re
from typing import Any

from sqlalchemy import select

from app.core.exceptions import ValidationError
from app.database.db import get_session
from app.models import Incident


class IncidentService:
    """Business operations for Incident records."""

    def _next_incident_no(self, session: Any) -> str:
        from sqlalchemy import func

        year = __import__("datetime").datetime.now().year
        # Count existing incidents for this year to derive the next sequence.
        existing = session.scalar(
            select(func.count()).select_from(Incident).where(Incident.incident_no.like(f"INC-{year}-%"))
        ) or 0
        seq = existing + 1
        return f"INC-{year}-{seq:04d}"

    def create(
        self,
        *,
        date: str,
        title: str,
        incident_category_id: int | None = None,
        severity: str = "Medium",
        description: str | None = None,
        root_cause: str | None = None,
        resolution: str | None = None,
        status_id: int | None = None,
        pic_id: int | None = None,
        department_id: int | None = None,
        resolution_time_minutes: int | None = None,
        incident_no: str | None = None,
    ) -> dict[str, Any]:
        if not date or not title:
            raise ValidationError("date and title are required")
        with get_session() as session:
            obj = Incident(
                date=date,
                title=title,
                incident_category_id=incident_category_id,
                severity=severity,
                description=description,
                root_cause=root_cause,
                resolution=resolution,
                status_id=status_id,
                pic_id=pic_id,
                department_id=department_id,
                resolution_time_minutes=resolution_time_minutes,
                incident_no=incident_no or self._next_incident_no(session),
            )
            session.add(obj)
            session.commit()
            session.refresh(obj)
            return _to_dict(obj)

    def list(
        self,
        *,
        date_from: str | None = None,
        date_to: str | None = None,
        severity: str | None = None,
        status_id: int | None = None,
        limit: int | None = 50,
    ) -> list[dict[str, Any]]:
        with get_session() as session:
            stmt = select(Incident)
            if date_from:
                stmt = stmt.where(Incident.date >= date_from)
            if date_to:
                stmt = stmt.where(Incident.date <= date_to)
            if severity:
                stmt = stmt.where(Incident.severity == severity)
            if status_id is not None:
                stmt = stmt.where(Incident.status_id == status_id)
            stmt = stmt.order_by(Incident.date.desc())
            if limit:
                stmt = stmt.limit(limit)
            rows = session.scalars(stmt).all()
            return [_to_dict(r) for r in rows]

    def get(self, incident_id: int) -> dict[str, Any]:
        with get_session() as session:
            obj = session.get(Incident, incident_id)
            if obj is None:
                raise ValidationError(f"Incident id={incident_id} not found")
            return _to_dict(obj)

    def update(self, incident_id: int, **fields: Any) -> dict[str, Any]:
        allowed = {
            "date", "title", "incident_category_id", "severity", "description",
            "root_cause", "resolution", "status_id", "pic_id", "department_id",
            "resolution_time_minutes", "incident_no",
        }
        cleaned = {k: v for k, v in fields.items() if k in allowed and v is not None}
        with get_session() as session:
            obj = session.get(Incident, incident_id)
            if obj is None:
                raise ValidationError(f"Incident id={incident_id} not found")
            for k, v in cleaned.items():
                setattr(obj, k, v)
            session.commit()
            session.refresh(obj)
            return _to_dict(obj)

    def delete(self, incident_id: int) -> None:
        with get_session() as session:
            obj = session.get(Incident, incident_id)
            if obj is None:
                raise ValidationError(f"Incident id={incident_id} not found")
            session.delete(obj)
            session.commit()


def _to_dict(obj: Any) -> dict[str, Any]:
    return {c.name: getattr(obj, c.name) for c in obj.__table__.columns}  # type: ignore[attr-defined]
