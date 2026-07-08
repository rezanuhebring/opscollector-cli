"""Seed mandatory reference data on first initialisation.

Status and Priority values are referenced by operational records, so sensible
defaults are inserted exactly once (guarded by an existing-value check).
"""

from __future__ import annotations

from sqlalchemy import select

from app.database.db import get_session
from app.models import Priority, Status


def seed_reference_data() -> None:
    """Insert default statuses and priorities if not already present."""
    with get_session() as session:
        if session.scalar(select(Status)) is not None:
            return  # already seeded

        statuses = [
            "Not Started",
            "In Progress",
            "On Hold",
            "Completed",
            "Cancelled",
            "Open",
            "Resolved",
            "Closed",
        ]
        for name in statuses:
            session.add(Status(name=name))

        priorities = [
            ("Low", 1),
            ("Medium", 2),
            ("High", 3),
            ("Critical", 4),
        ]
        for name, level in priorities:
            session.add(Priority(name=name, level=level))

        session.commit()
