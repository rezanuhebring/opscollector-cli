"""Seed mandatory reference data and optional demo data on first initialisation.

Status / Priority are always seeded once. Demo data (departments, sample
incidents, BAU, changes, an evidence file, an objective + key result) populates
the dashboard and lists so a fresh install is usable. ``seed_demo_data`` only
seeds when operational tables are empty (so it never clobbers real data).
``force_seed_demo_data`` always seeds (used by the ``db seed-demo`` command for
on-demand test data).
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy import func, select

from app.core.config import get_settings
from app.database.db import get_session
from app.models import (
    BAUActivity,
    ChangeCategory,
    ChangeLog,
    DailyBAU,
    Department,
    Evidence,
    Incident,
    IncidentCategory,
    KeyResult,
    Objective,
    PIC,
    Priority,
    Status,
)


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


def _insert_demo_rows(session) -> None:
    """Insert a consistent set of example operational records + an evidence file.

    Assumes reference data (statuses) has already been seeded.
    """
    status = {s.name: s.id for s in session.scalars(select(Status)).all()}
    completed = status.get("Completed")
    open_st = status.get("Open")
    in_prog = status.get("In Progress")

    dept = Department(name="IT Operations", description="Core infrastructure team")
    session.add(dept)
    session.flush()
    pic = PIC(name="Budi Santoso", department_id=dept.id, email="budi@ops.local")
    session.add(pic)
    session.flush()

    inc_cat = IncidentCategory(name="Infrastructure", description="Server/network")
    chg_cat = ChangeCategory(name="Maintenance", description="Preventive maintenance")
    bau_act = BAUActivity(name="Monitoring", bau_category_id=None)
    session.add_all([inc_cat, chg_cat, bau_act])
    session.flush()

    obj = Objective(
        name="Improve Service Reliability",
        title="Improve Service Reliability FY26",
        owner_id=pic.id, status_id=in_prog, progress=60.0,
    )
    session.add(obj)
    session.flush()
    kr = KeyResult(
        name="Reduce MTTR below 60 min", objective_id=obj.id,
        target_value=60.0, current_value=45.0, unit="min", progress=75.0,
    )
    session.add(kr)

    today = datetime.now(timezone.utc).date().isoformat()
    last_week = datetime.now(timezone.utc).date().replace(day=1).isoformat()

    existing = session.scalar(
        select(func.count()).select_from(Incident).where(Incident.incident_no.like("INC-2026-%"))
    ) or 0
    base = existing + 1

    session.add(Incident(
        incident_no=f"INC-2026-{base:04d}",
        date=today, title="Web server response slow",
        incident_category_id=inc_cat.id, severity="High",
        description="Latency spike on public web tier after deploy.",
        root_cause="Connection pool exhaustion", resolution="Increased pool size",
        status_id=status.get("Resolved", open_st),
        pic_id=pic.id, department_id=dept.id, resolution_time_minutes=45,
    ))
    session.add(Incident(
        incident_no=f"INC-2026-{base + 1:04d}",
        date=today, title="Backup job failed",
        incident_category_id=inc_cat.id, severity="Medium",
        description="Nightly DB backup failed with auth error.",
        status_id=open_st, pic_id=pic.id, department_id=dept.id,
    ))

    session.add(DailyBAU(
        date=today, bau_activity_id=bau_act.id,
        title="Morning health check", description="Checked all critical services.",
        status_id=completed, pic_id=pic.id, department_id=dept.id,
    ))
    session.add(DailyBAU(
        date=last_week, bau_activity_id=bau_act.id,
        title="Patch Tuesday review", description="Reviewed and approved patches.",
        status_id=in_prog, pic_id=pic.id, department_id=dept.id,
    ))

    session.add(ChangeLog(
        date=today, change_category_id=chg_cat.id, change_type="Maintenance",
        title="Firewall firmware upgrade",
        description="Routine preventive maintenance on perimeter firewall.",
        status_id=completed, pic_id=pic.id, department_id=dept.id, result="Success",
    ))

    # Evidence: write a small real file so the record points to something.
    settings = get_settings()
    ev_dir = settings.evidence_dir / "2026" / "07"
    ev_dir.mkdir(parents=True, exist_ok=True)
    ev_file = ev_dir / "demo-evidence.txt"
    ev_file.write_text("Demo evidence file for OpsCollector-CLI.\n", encoding="utf-8")
    session.add(Evidence(
        original_filename="demo-evidence.txt",
        stored_filename=ev_file.name,
        relative_path=f"2026/07/{ev_file.name}",
        extension="txt", size_bytes=ev_file.stat().st_size,
        mime_type="text/plain", title="Demo Evidence",
        description="Seeded sample evidence.", uploaded_by="system",
        entity_type="incident", entity_id=1,
        uploaded_at=datetime.now(timezone.utc),
    ))

    session.commit()


def seed_demo_data() -> None:
    """Populate example data only if operational tables are empty.

    Safe to call on every startup: never clobbers data the user has entered.
    """
    with get_session() as session:
        if session.scalar(select(Incident)) or session.scalar(select(DailyBAU)):
            return  # real data already exists; do not clobber
        _insert_demo_rows(session)


def force_seed_demo_data() -> int:
    """Always insert demo rows (for on-demand test data). Returns rows added."""
    from sqlalchemy import func, select as sa_select

    with get_session() as session:
        before = session.scalar(sa_select(func.count()).select_from(Incident)) or 0
        _insert_demo_rows(session)
        after = session.scalar(sa_select(func.count()).select_from(Incident)) or 0
        return after - before
