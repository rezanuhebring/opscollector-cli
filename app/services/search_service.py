"""Search service: cross-entity search over operational data.

Supports filtering by date range, PIC, status, keyword, and entity type.
Returns normalised result rows with an ``entity_type`` discriminator so the CLI
can render a unified search view.
"""

from __future__ import annotations

from typing import Any

from sqlalchemy import or_, select

from app.database.db import get_session
from app.models import ChangeLog, DailyBAU, Incident, OKRProgress


class SearchService:
    """Unified search across operational modules."""

    def search(
        self,
        *,
        keyword: str | None = None,
        date_from: str | None = None,
        date_to: str | None = None,
        pic_id: int | None = None,
        status_id: int | None = None,
        entity_types: list[str] | None = None,
        limit: int = 100,
    ) -> dict[str, list[dict[str, Any]]]:
        types = entity_types or ["bau", "okr", "incident", "change"]
        results: dict[str, list[dict[str, Any]]] = {
            "bau": [],
            "okr": [],
            "incident": [],
            "change": [],
        }
        if "bau" in types:
            results["bau"] = self._search_bau(keyword, date_from, date_to, pic_id, status_id, limit)
        if "okr" in types:
            results["okr"] = self._search_okr(keyword, date_from, date_to, limit)
        if "incident" in types:
            results["incident"] = self._search_incident(keyword, date_from, date_to, pic_id, status_id, limit)
        if "change" in types:
            results["change"] = self._search_change(keyword, date_from, date_to, pic_id, status_id, limit)
        return results

    def _kw(self, stmt: Any, *columns: Any, keyword: str | None) -> Any:
        if keyword:
            like = f"%{keyword}%"
            stmt = stmt.where(or_(*[c.like(like) for c in columns if c is not None]))
        return stmt

    def _search_bau(self, keyword, date_from, date_to, pic_id, status_id, limit) -> list[dict]:
        with get_session() as session:
            stmt = select(DailyBAU)
            if date_from:
                stmt = stmt.where(DailyBAU.date >= date_from)
            if date_to:
                stmt = stmt.where(DailyBAU.date <= date_to)
            if pic_id is not None:
                stmt = stmt.where(DailyBAU.pic_id == pic_id)
            if status_id is not None:
                stmt = stmt.where(DailyBAU.status_id == status_id)
            stmt = self._kw(stmt, DailyBAU.title, DailyBAU.description, DailyBAU.notes, keyword=keyword)
            stmt = stmt.limit(limit)
            rows = session.scalars(stmt).all()
            return [{"entity_type": "bau", **_to_dict(r)} for r in rows]

    def _search_okr(self, keyword, date_from, date_to, limit) -> list[dict]:
        with get_session() as session:
            stmt = select(OKRProgress)
            if date_from:
                stmt = stmt.where(OKRProgress.date >= date_from)
            if date_to:
                stmt = stmt.where(OKRProgress.date <= date_to)
            stmt = self._kw(stmt, OKRProgress.achievement, OKRProgress.risk,
                            OKRProgress.issue, OKRProgress.action_plan, keyword=keyword)
            stmt = stmt.limit(limit)
            rows = session.scalars(stmt).all()
            return [{"entity_type": "okr", **_to_dict(r)} for r in rows]

    def _search_incident(self, keyword, date_from, date_to, pic_id, status_id, limit) -> list[dict]:
        with get_session() as session:
            stmt = select(Incident)
            if date_from:
                stmt = stmt.where(Incident.date >= date_from)
            if date_to:
                stmt = stmt.where(Incident.date <= date_to)
            if pic_id is not None:
                stmt = stmt.where(Incident.pic_id == pic_id)
            if status_id is not None:
                stmt = stmt.where(Incident.status_id == status_id)
            stmt = self._kw(stmt, Incident.title, Incident.description,
                            Incident.root_cause, Incident.resolution, keyword=keyword)
            stmt = stmt.limit(limit)
            rows = session.scalars(stmt).all()
            return [{"entity_type": "incident", **_to_dict(r)} for r in rows]

    def _search_change(self, keyword, date_from, date_to, pic_id, status_id, limit) -> list[dict]:
        with get_session() as session:
            stmt = select(ChangeLog)
            if date_from:
                stmt = stmt.where(ChangeLog.date >= date_from)
            if date_to:
                stmt = stmt.where(ChangeLog.date <= date_to)
            if pic_id is not None:
                stmt = stmt.where(ChangeLog.pic_id == pic_id)
            if status_id is not None:
                stmt = stmt.where(ChangeLog.status_id == status_id)
            stmt = self._kw(stmt, ChangeLog.title, ChangeLog.description, ChangeLog.result, keyword=keyword)
            stmt = stmt.limit(limit)
            rows = session.scalars(stmt).all()
            return [{"entity_type": "change", **_to_dict(r)} for r in rows]


def _to_dict(obj: Any) -> dict[str, Any]:
    return {c.name: getattr(obj, c.name) for c in obj.__table__.columns}  # type: ignore[attr-defined]
