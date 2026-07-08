"""Operational and evidence models.

DailyBAU, OKRProgress, Incident, ChangeLog capture operational activities.
Evidence stores metadata for files copied into the evidence repository and can
be linked to any of the operational entities via (entity_type, entity_id).
"""

from __future__ import annotations

from sqlalchemy import (
    DateTime,
    Date,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class DailyBAU(TimestampMixin, Base):
    __tablename__ = "daily_bau"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    date: Mapped[str] = mapped_column(String(20), nullable=False)
    bau_activity_id: Mapped[int | None] = mapped_column(
        ForeignKey("bau_activities.id"), nullable=True
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    status_id: Mapped[int | None] = mapped_column(ForeignKey("statuses.id"), nullable=True)
    pic_id: Mapped[int | None] = mapped_column(ForeignKey("pics.id"), nullable=True)
    department_id: Mapped[int | None] = mapped_column(
        ForeignKey("departments.id"), nullable=True
    )
    duration_minutes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    activity = relationship("BAUActivity")
    status = relationship("Status")
    pic = relationship("PIC")
    department = relationship("Department")


class OKRProgress(TimestampMixin, Base):
    __tablename__ = "okr_progress"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    key_result_id: Mapped[int | None] = mapped_column(
        ForeignKey("key_results.id"), nullable=True
    )
    date: Mapped[str] = mapped_column(String(20), nullable=False)
    achievement: Mapped[str | None] = mapped_column(Text, nullable=True)
    current_value: Mapped[float] = mapped_column(default=0.0, nullable=False)
    gap: Mapped[float] = mapped_column(default=0.0, nullable=False)
    progress: Mapped[float] = mapped_column(default=0.0, nullable=False)
    risk: Mapped[str | None] = mapped_column(Text, nullable=True)
    issue: Mapped[str | None] = mapped_column(Text, nullable=True)
    action_plan: Mapped[str | None] = mapped_column(Text, nullable=True)

    key_result = relationship("KeyResult")


class Incident(TimestampMixin, Base):
    __tablename__ = "incidents"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    incident_no: Mapped[str | None] = mapped_column(String(50), unique=True, nullable=True)
    date: Mapped[str] = mapped_column(String(20), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    incident_category_id: Mapped[int | None] = mapped_column(
        ForeignKey("incident_categories.id"), nullable=True
    )
    severity: Mapped[str] = mapped_column(String(20), default="Medium", nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    root_cause: Mapped[str | None] = mapped_column(Text, nullable=True)
    resolution: Mapped[str | None] = mapped_column(Text, nullable=True)
    status_id: Mapped[int | None] = mapped_column(ForeignKey("statuses.id"), nullable=True)
    pic_id: Mapped[int | None] = mapped_column(ForeignKey("pics.id"), nullable=True)
    department_id: Mapped[int | None] = mapped_column(
        ForeignKey("departments.id"), nullable=True
    )
    resolution_time_minutes: Mapped[int | None] = mapped_column(Integer, nullable=True)

    category = relationship("IncidentCategory")
    status = relationship("Status")
    pic = relationship("PIC")
    department = relationship("Department")


class ChangeLog(TimestampMixin, Base):
    __tablename__ = "change_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    change_no: Mapped[str | None] = mapped_column(String(50), unique=True, nullable=True)
    date: Mapped[str] = mapped_column(String(20), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    change_category_id: Mapped[int | None] = mapped_column(
        ForeignKey("change_categories.id"), nullable=True
    )
    change_type: Mapped[str] = mapped_column(String(20), default="Change", nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    status_id: Mapped[int | None] = mapped_column(ForeignKey("statuses.id"), nullable=True)
    pic_id: Mapped[int | None] = mapped_column(ForeignKey("pics.id"), nullable=True)
    department_id: Mapped[int | None] = mapped_column(
        ForeignKey("departments.id"), nullable=True
    )
    scheduled_start: Mapped[str | None] = mapped_column(String(30), nullable=True)
    scheduled_end: Mapped[str | None] = mapped_column(String(30), nullable=True)
    result: Mapped[str | None] = mapped_column(Text, nullable=True)

    category = relationship("ChangeCategory")
    status = relationship("Status")
    pic = relationship("PIC")
    department = relationship("Department")


class Evidence(TimestampMixin, Base):
    __tablename__ = "evidence"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    stored_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    relative_path: Mapped[str] = mapped_column(String(512), nullable=False)
    extension: Mapped[str] = mapped_column(String(20), nullable=False)
    size_bytes: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    mime_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    evidence_category_id: Mapped[int | None] = mapped_column(
        ForeignKey("evidence_categories.id"), nullable=True
    )
    title: Mapped[str | None] = mapped_column(String(255), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    uploaded_by: Mapped[str | None] = mapped_column(String(100), nullable=True)
    entity_type: Mapped[str | None] = mapped_column(String(30), nullable=True)
    entity_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    uploaded_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), nullable=False)

    category = relationship("EvidenceCategory")
