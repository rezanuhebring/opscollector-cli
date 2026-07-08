"""Master / reference data models.

These are the lookup tables used by operational records (status, priority,
categories, departments, PICs). They are independent of any module so they can
be reused verbatim by a future web/API backend.
"""

from __future__ import annotations

from sqlalchemy import Boolean, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class MasterMixin(TimestampMixin):
    """Common columns for named reference entities."""

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class Objective(MasterMixin, Base):
    __tablename__ = "objectives"

    title: Mapped[str] = mapped_column(String(255), nullable=False)
    owner_id: Mapped[int | None] = mapped_column(ForeignKey("pics.id"), nullable=True)
    status_id: Mapped[int | None] = mapped_column(ForeignKey("statuses.id"), nullable=True)
    start_date: Mapped[str | None] = mapped_column(String(20), nullable=True)
    end_date: Mapped[str | None] = mapped_column(String(20), nullable=True)
    progress: Mapped[float] = mapped_column(default=0.0, nullable=False)

    owner = relationship("PIC")
    status = relationship("Status")
    key_results = relationship(
        "KeyResult", back_populates="objective", cascade="all, delete-orphan"
    )


class KeyResult(MasterMixin, Base):
    __tablename__ = "key_results"

    objective_id: Mapped[int | None] = mapped_column(
        ForeignKey("objectives.id"), nullable=True
    )
    target_value: Mapped[float] = mapped_column(default=0.0, nullable=False)
    current_value: Mapped[float] = mapped_column(default=0.0, nullable=False)
    unit: Mapped[str | None] = mapped_column(String(50), nullable=True)
    status_id: Mapped[int | None] = mapped_column(ForeignKey("statuses.id"), nullable=True)
    progress: Mapped[float] = mapped_column(default=0.0, nullable=False)

    objective = relationship("Objective", back_populates="key_results")
    status = relationship("Status")


class BAUCategory(MasterMixin, Base):
    __tablename__ = "bau_categories"

    activities = relationship(
        "BAUActivity", back_populates="category", cascade="all, delete-orphan"
    )


class BAUActivity(MasterMixin, Base):
    __tablename__ = "bau_activities"

    bau_category_id: Mapped[int | None] = mapped_column(
        ForeignKey("bau_categories.id"), nullable=True
    )
    category = relationship("BAUCategory", back_populates="activities")


class IncidentCategory(MasterMixin, Base):
    __tablename__ = "incident_categories"


class ChangeCategory(MasterMixin, Base):
    __tablename__ = "change_categories"


class EvidenceCategory(MasterMixin, Base):
    __tablename__ = "evidence_categories"


class Department(MasterMixin, Base):
    __tablename__ = "departments"

    pics = relationship("PIC", back_populates="department", cascade="all, delete-orphan")


class PIC(MasterMixin, Base):
    __tablename__ = "pics"

    department_id: Mapped[int | None] = mapped_column(
        ForeignKey("departments.id"), nullable=True
    )
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)

    department = relationship("Department", back_populates="pics")
    owned_objectives = relationship(
        "Objective", foreign_keys="Objective.owner_id", overlaps="owner"
    )


class Priority(MasterMixin, Base):
    __tablename__ = "priorities"

    level: Mapped[int] = mapped_column(Integer, default=0, nullable=False)


class Status(MasterMixin, Base):
    __tablename__ = "statuses"
