from __future__ import annotations

from datetime import datetime
import json

from sqlalchemy import (
    Column,
    DateTime,
    String,
    Boolean,
    Integer,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.types import TypeDecorator

from server.db import Base


class JSONType(TypeDecorator):
    """Use JSONB on Postgres, JSON on other backends (e.g. SQLite)."""
    impl = String
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            return dialect.type_descriptor(JSONB())
        return dialect.type_descriptor(Text())

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        return json.dumps(value)

    def process_result_value(self, value, dialect):
        if value is None:
            return None
        if isinstance(value, str):
            return json.loads(value)
        return value


class Client(Base):
    __tablename__ = "client"

    client_id = Column(String, primary_key=True)
    name = Column(String, nullable=True)
    api_token = Column(String, nullable=False, index=True)
    token_issued_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    token_rotated_at = Column(DateTime, nullable=True)
    revoked = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class Department(Base):
    __tablename__ = "department"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    description = Column(String, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    version = Column(Integer, default=1, nullable=False)
    schema_version = Column(Integer, default=1, nullable=False)
    payload = Column(JSONType, nullable=True)


class PIC(Base):
    __tablename__ = "pic"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    description = Column(String, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    version = Column(Integer, default=1, nullable=False)
    schema_version = Column(Integer, default=1, nullable=False)
    payload = Column(JSONType, nullable=True)


class Status(Base):
    __tablename__ = "status"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    description = Column(String, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    version = Column(Integer, default=1, nullable=False)
    schema_version = Column(Integer, default=1, nullable=False)
    payload = Column(JSONType, nullable=True)


model_for = {
    "department": Department,
    "pic": PIC,
    "status": Status,
}


class ChangeFeed(Base):
    __tablename__ = "change_feed"

    id = Column(Integer, primary_key=True, autoincrement=True)
    entity = Column(String, nullable=False, index=True)
    row_id = Column(String, nullable=False, index=True)
    op = Column(String, nullable=False)
    client_id = Column(String, nullable=False, index=True)
    version = Column(Integer, nullable=False)
    payload = Column(JSONType, nullable=False)
    base_schema_version = Column(Integer, nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    schema_version = Column(Integer, nullable=True)

    __table_args__ = (
        UniqueConstraint(
            "client_id", "entity", "row_id", "version", "op",
            name="uq_change_idempotency",
        ),
    )


class ConflictEvent(Base):
    __tablename__ = "conflict_event"

    id = Column(Integer, primary_key=True, autoincrement=True)
    entity = Column(String, nullable=False, index=True)
    row_id = Column(String, nullable=False, index=True)
    winning_payload = Column(JSONType, nullable=True)
    losing_payload = Column(JSONType, nullable=True)
    status = Column(String, default="open", nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    resolved_by = Column(String, nullable=True)
    resolved_at = Column(DateTime, nullable=True)


class SettingsKV(Base):
    __tablename__ = "settings_kv"

    key = Column(String, primary_key=True)
    value = Column(String, nullable=False)
