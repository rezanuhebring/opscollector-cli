"""Daily BAU service: business logic for daily operational activities."""

from __future__ import annotations

from typing import Any

from sqlalchemy import select

from app.core.exceptions import ValidationError
from app.database.db import get_session
from app.models import DailyBAU, Status


class BAUService:
    """Business operations for Daily BAU records."""

    def create(
        self,
        *,
        date: str,
        title: str,
        bau_activity_id: int | None = None,
        description: str | None = None,
        status_id: int | None = None,
        pic_id: int | None = None,
        department_id: int | None = None,
        duration_minutes: int | None = None,
        notes: str | None = None,
    ) -> dict[str, Any]:
        if not date or not title:
            raise ValidationError("date and title are required")
        with get_session() as session:
            obj = DailyBAU(
                date=date,
                title=title,
                bau_activity_id=bau_activity_id,
                description=description,
                status_id=status_id,
                pic_id=pic_id,
                department_id=department_id,
                duration_minutes=duration_minutes,
                notes=notes,
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
        status_id: int | None = None,
        pic_id: int | None = None,
        limit: int | None = 50,
        offset: int = 0,
    ) -> list[dict[str, Any]]:
        with get_session() as session:
            stmt = select(DailyBAU)
            if date_from:
                stmt = stmt.where(DailyBAU.date >= date_from)
            if date_to:
                stmt = stmt.where(DailyBAU.date <= date_to)
            if status_id is not None:
                stmt = stmt.where(DailyBAU.status_id == status_id)
            if pic_id is not None:
                stmt = stmt.where(DailyBAU.pic_id == pic_id)
            stmt = stmt.order_by(DailyBAU.date.desc())
            stmt = stmt.offset(offset)
            if limit:
                stmt = stmt.limit(limit)
            rows = session.scalars(stmt).all()
            return [_to_dict(r) for r in rows]

    def get(self, bau_id: int) -> dict[str, Any]:
        with get_session() as session:
            obj = session.get(DailyBAU, bau_id)
            if obj is None:
                raise ValidationError(f"BAU id={bau_id} not found")
            return _to_dict(obj)

    def update(self, bau_id: int, **fields: Any) -> dict[str, Any]:
        allowed = {
            "date", "title", "bau_activity_id", "description", "status_id",
            "pic_id", "department_id", "duration_minutes", "notes",
        }
        cleaned = {k: v for k, v in fields.items() if k in allowed and v is not None}
        with get_session() as session:
            obj = session.get(DailyBAU, bau_id)
            if obj is None:
                raise ValidationError(f"BAU id={bau_id} not found")
            for k, v in cleaned.items():
                setattr(obj, k, v)
            session.commit()
            session.refresh(obj)
            return _to_dict(obj)

    def delete(self, bau_id: int) -> None:
        with get_session() as session:
            obj = session.get(DailyBAU, bau_id)
            if obj is None:
                raise ValidationError(f"BAU id={bau_id} not found")
            session.delete(obj)
            session.commit()


def _to_dict(obj: Any) -> dict[str, Any]:
    return {c.name: getattr(obj, c.name) for c in obj.__table__.columns}  # type: ignore[attr-defined]
