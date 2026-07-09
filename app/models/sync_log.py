"""Sync / change-feed log model."""

from __future__ import annotations

from datetime import datetime
from sqlalchemy import Boolean, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin


class SyncLog(Base, TimestampMixin):
    __tablename__ = "sync_log"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    entity: Mapped[str] = mapped_column(String(50), nullable=False)
    row_id: Mapped[int] = mapped_column(Integer, nullable=False)
    op: Mapped[str] = mapped_column(String(10), nullable=False)
    client_id: Mapped[str] = mapped_column(String(64), nullable=False)
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    payload: Mapped[str] = mapped_column(Text, nullable=False)
    base_schema_version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    synced: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
