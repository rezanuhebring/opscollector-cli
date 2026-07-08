"""Change & Maintenance service: business logic for change/maintenance logs."""

from __future__ import annotations

from typing import Any

from sqlalchemy import select

from app.core.exceptions import ValidationError
from app.database.db import get_session
from app.models import ChangeLog


class ChangeService:
    """Business operations for Change & Maintenance records."""

    def _next_change_no(self) -> str:
        from datetime import datetime

        year = datetime.now().year
        return f"CHG-{year}-{{seq:04d}}"

    def create(
        self,
        *,
        date: str,
        title: str,
        change_category_id: int | None = None,
        change_type: str = "Change",
        description: str | None = None,
        status_id: int | None = None,
        pic_id: int | None = None,
        department_id: int | None = None,
        scheduled_start: str | None = None,
        scheduled_end: str | None = None,
        result: str | None = None,
        change_no: str | None = None,
    ) -> dict[str, Any]:
        if not date or not title:
            raise ValidationError("date and title are required")
        with get_session() as session:
            obj = ChangeLog(
                date=date,
                title=title,
                change_category_id=change_category_id,
                change_type=change_type,
                description=description,
                status_id=status_id,
                pic_id=pic_id,
                department_id=department_id,
                scheduled_start=scheduled_start,
                scheduled_end=scheduled_end,
                result=result,
                change_no=change_no,
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
        change_type: str | None = None,
        status_id: int | None = None,
        limit: int | None = 50,
    ) -> list[dict[str, Any]]:
        with get_session() as session:
            stmt = select(ChangeLog)
            if date_from:
                stmt = stmt.where(ChangeLog.date >= date_from)
            if date_to:
                stmt = stmt.where(ChangeLog.date <= date_to)
            if change_type:
                stmt = stmt.where(ChangeLog.change_type == change_type)
            if status_id is not None:
                stmt = stmt.where(ChangeLog.status_id == status_id)
            stmt = stmt.order_by(ChangeLog.date.desc())
            if limit:
                stmt = stmt.limit(limit)
            rows = session.scalars(stmt).all()
            return [_to_dict(r) for r in rows]

    def get(self, change_id: int) -> dict[str, Any]:
        with get_session() as session:
            obj = session.get(ChangeLog, change_id)
            if obj is None:
                raise ValidationError(f"Change log id={change_id} not found")
            return _to_dict(obj)

    def update(self, change_id: int, **fields: Any) -> dict[str, Any]:
        allowed = {
            "date", "title", "change_category_id", "change_type", "description",
            "status_id", "pic_id", "department_id", "scheduled_start",
            "scheduled_end", "result", "change_no",
        }
        cleaned = {k: v for k, v in fields.items() if k in allowed and v is not None}
        with get_session() as session:
            obj = session.get(ChangeLog, change_id)
            if obj is None:
                raise ValidationError(f"Change log id={change_id} not found")
            for k, v in cleaned.items():
                setattr(obj, k, v)
            session.commit()
            session.refresh(obj)
            return _to_dict(obj)

    def delete(self, change_id: int) -> None:
        with get_session() as session:
            obj = session.get(ChangeLog, change_id)
            if obj is None:
                raise ValidationError(f"Change log id={change_id} not found")
            session.delete(obj)
            session.commit()


def _to_dict(obj: Any) -> dict[str, Any]:
    return {c.name: getattr(obj, c.name) for c in obj.__table__.columns}  # type: ignore[attr-defined]
