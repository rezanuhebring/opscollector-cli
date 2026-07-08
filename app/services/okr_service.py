"""OKR Progress service: business logic for Key Result progress tracking."""

from __future__ import annotations

from typing import Any

from sqlalchemy import select

from app.core.exceptions import ValidationError
from app.database.db import get_session
from app.models import KeyResult, OKRProgress


class OKRService:
    """Business operations for OKR progress records."""

    def create(
        self,
        *,
        key_result_id: int,
        date: str,
        current_value: float = 0.0,
        gap: float = 0.0,
        progress: float = 0.0,
        achievement: str | None = None,
        risk: str | None = None,
        issue: str | None = None,
        action_plan: str | None = None,
    ) -> dict[str, Any]:
        if not key_result_id or not date:
            raise ValidationError("key_result_id and date are required")
        with get_session() as session:
            kr = session.get(KeyResult, key_result_id)
            if kr is None:
                raise ValidationError(f"Key Result id={key_result_id} not found")
            obj = OKRProgress(
                key_result_id=key_result_id,
                date=date,
                current_value=current_value,
                gap=gap,
                progress=progress,
                achievement=achievement,
                risk=risk,
                issue=issue,
                action_plan=action_plan,
            )
            session.add(obj)
            # Keep the KeyResult's current_value/progress in sync.
            kr = session.get(KeyResult, key_result_id)
            if kr is not None:
                kr.current_value = current_value
                kr.progress = progress
            session.commit()
            session.refresh(obj)
            return _to_dict(obj)

    def list(
        self, *, key_result_id: int | None = None, limit: int | None = 50
    ) -> list[dict[str, Any]]:
        with get_session() as session:
            stmt = select(OKRProgress)
            if key_result_id is not None:
                stmt = stmt.where(OKRProgress.key_result_id == key_result_id)
            stmt = stmt.order_by(OKRProgress.date.desc())
            if limit:
                stmt = stmt.limit(limit)
            rows = session.scalars(stmt).all()
            return [_to_dict(r) for r in rows]

    def get(self, progress_id: int) -> dict[str, Any]:
        with get_session() as session:
            obj = session.get(OKRProgress, progress_id)
            if obj is None:
                raise ValidationError(f"OKR progress id={progress_id} not found")
            return _to_dict(obj)

    def update(self, progress_id: int, **fields: Any) -> dict[str, Any]:
        allowed = {
            "key_result_id", "date", "current_value", "gap", "progress",
            "achievement", "risk", "issue", "action_plan",
        }
        cleaned = {k: v for k, v in fields.items() if k in allowed and v is not None}
        with get_session() as session:
            obj = session.get(OKRProgress, progress_id)
            if obj is None:
                raise ValidationError(f"OKR progress id={progress_id} not found")
            for k, v in cleaned.items():
                setattr(obj, k, v)
            session.commit()
            session.refresh(obj)
            return _to_dict(obj)

    def delete(self, progress_id: int) -> None:
        with get_session() as session:
            obj = session.get(OKRProgress, progress_id)
            if obj is None:
                raise ValidationError(f"OKR progress id={progress_id} not found")
            session.delete(obj)
            session.commit()


def _to_dict(obj: Any) -> dict[str, Any]:
    return {c.name: getattr(obj, c.name) for c in obj.__table__.columns}  # type: ignore[attr-defined]
