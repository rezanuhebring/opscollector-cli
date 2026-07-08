"""Dashboard service: aggregates operational data into summary metrics.

Returns plain dicts so the CLI (Rich) and a future web backend can both consume
the same business logic.
"""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timedelta
from typing import Any

from sqlalchemy import func, select

from app.database.db import get_session
from app.models import (
    ChangeLog,
    DailyBAU,
    Evidence,
    Incident,
    KeyResult,
    Objective,
    Status,
)


class DashboardService:
    """Produces summary metrics for the operational dashboard."""

    def summary(self) -> dict[str, Any]:
        with get_session() as session:
            objectives_total = session.scalar(select(func.count()).select_from(Objective)) or 0
            objectives_done = session.scalar(
                select(func.count()).select_from(Objective).join(Status, Objective.status_id == Status.id).where(Status.name == "Completed")
            ) or 0
            krs_total = session.scalar(select(func.count()).select_from(KeyResult)) or 0

            bau_total = session.scalar(select(func.count()).select_from(DailyBAU)) or 0
            bau_done = session.scalar(
                select(func.count()).select_from(DailyBAU).join(Status, DailyBAU.status_id == Status.id).where(Status.name == "Completed")
            ) or 0

            incidents_total = session.scalar(select(func.count()).select_from(Incident)) or 0
            incidents_open = session.scalar(
                select(func.count()).select_from(Incident).join(Status, Incident.status_id == Status.id).where(Status.name.in_(["Open", "In Progress"]))
            ) or 0
            incidents_resolved = session.scalar(
                select(func.count()).select_from(Incident).join(Status, Incident.status_id == Status.id).where(Status.name.in_(["Resolved", "Closed"]))
            ) or 0

            changes_total = session.scalar(select(func.count()).select_from(ChangeLog)) or 0
            evidence_total = session.scalar(select(func.count()).select_from(Evidence)) or 0

            # Average KR progress across all objectives.
            kr_rows = session.scalars(select(KeyResult.progress)).all()
            kr_avg = round(sum(kr_rows) / len(kr_rows), 1) if kr_rows else 0.0

            bau_completion = round((bau_done / bau_total * 100), 1) if bau_total else 0.0

            return {
                "objectives": {"total": objectives_total, "completed": objectives_done},
                "key_results": {"total": krs_total, "avg_progress": kr_avg},
                "bau": {"total": bau_total, "completed": bau_done, "completion_pct": bau_completion},
                "incidents": {"total": incidents_total, "open": incidents_open, "resolved": incidents_resolved},
                "changes": {"total": changes_total},
                "evidence": {"total": evidence_total},
                "outstanding": bau_total - bau_done,
            }

    def weekly_trend(self, weeks: int = 6) -> list[dict[str, Any]]:
        """Return weekly counts of BAU, incidents, changes for the last N weeks."""
        with get_session() as session:
            today = datetime.now().date()
            trend: list[dict[str, Any]] = []
            for i in range(weeks - 1, -1, -1):
                start = today - timedelta(days=today.weekday() + 7 * i)
                end = start + timedelta(days=6)
                s, e = start.isoformat(), end.isoformat()
                bau = session.scalar(
                    select(func.count()).select_from(DailyBAU).where(DailyBAU.date.between(s, e))
                ) or 0
                inc = session.scalar(
                    select(func.count()).select_from(Incident).where(Incident.date.between(s, e))
                ) or 0
                chg = session.scalar(
                    select(func.count()).select_from(ChangeLog).where(ChangeLog.date.between(s, e))
                ) or 0
                trend.append({"week": f"{s}~{e}", "bau": bau, "incidents": inc, "changes": chg})
            return trend

    def objectives_progress(self) -> list[dict[str, Any]]:
        with get_session() as session:
            rows = session.scalars(select(Objective)).all()
            out = []
            for o in rows:
                krs = session.scalars(select(KeyResult).where(KeyResult.objective_id == o.id)).all()
                avg = round(sum(kr.progress for kr in krs) / len(krs), 1) if krs else 0.0
                out.append({
                    "id": o.id,
                    "name": o.name,
                    "progress": o.progress,
                    "key_results": len(krs),
                    "kr_avg_progress": avg,
                })
            return out
