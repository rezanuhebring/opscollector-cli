"""Evidence service: file intake into the evidence repository.

Copies a source file into the evidence directory under a stable, renamed path,
records metadata, and supports linking to any operational entity
(entity_type + entity_id). Files are organised by year/month for consistency.
"""

from __future__ import annotations

import mimetypes
import shutil
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from sqlalchemy import select

from app.core.config import get_settings
from app.core.exceptions import EvidenceError, ValidationError
from app.database.db import get_session
from app.models import Evidence

_VALID_ENTITY_TYPES = {"bau", "okr", "incident", "change"}


class EvidenceService:
    """Business operations for the evidence repository."""

    def add_file(
        self,
        *,
        source_path: str | Path,
        title: str | None = None,
        description: str | None = None,
        evidence_category_id: int | None = None,
        uploaded_by: str | None = None,
        entity_type: str | None = None,
        entity_id: int | None = None,
    ) -> dict[str, Any]:
        settings = get_settings()
        src = Path(source_path)
        if not src.exists() or not src.is_file():
            raise EvidenceError(f"Source file not found: {src}")

        ext = src.suffix.lstrip(".").lower()
        if ext not in settings.evidence.allowed_extensions:
            raise ValidationError(
                f"File type '.{ext}' not allowed. Allowed: "
                f"{', '.join(settings.evidence.allowed_extensions)}"
            )

        size = src.stat().st_size
        max_bytes = settings.evidence.max_size_mb * 1024 * 1024
        if size > max_bytes:
            raise ValidationError(
                f"File too large ({size} bytes > {max_bytes} bytes limit)"
            )

        if entity_type and entity_type not in _VALID_ENTITY_TYPES:
            raise ValidationError(
                f"entity_type must be one of {_VALID_ENTITY_TYPES}"
            )

        # Build a stable stored name: <uuid>.<ext>
        now = datetime.now(timezone.utc)
        year_month = now.strftime("%Y/%m")
        stored_name = f"{uuid.uuid4().hex}.{ext}"
        dest_dir = settings.evidence_dir / year_month
        dest_dir.mkdir(parents=True, exist_ok=True)
        dest = dest_dir / stored_name
        shutil.copy2(src, dest)

        mime_type = mimetypes.guess_type(str(src))[0]
        relative_path = f"{year_month}/{stored_name}"

        with get_session() as session:
            obj = Evidence(
                original_filename=src.name,
                stored_filename=stored_name,
                relative_path=relative_path,
                extension=ext,
                size_bytes=size,
                mime_type=mime_type,
                evidence_category_id=evidence_category_id,
                title=title or src.stem,
                description=description,
                uploaded_by=uploaded_by,
                entity_type=entity_type,
                entity_id=entity_id,
                uploaded_at=now,
            )
            session.add(obj)
            session.commit()
            session.refresh(obj)
            return _to_dict(obj)

    def list(
        self,
        *,
        entity_type: str | None = None,
        entity_id: int | None = None,
        evidence_category_id: int | None = None,
        limit: int | None = 50,
    ) -> list[dict[str, Any]]:
        with get_session() as session:
            stmt = select(Evidence)
            if entity_type:
                stmt = stmt.where(Evidence.entity_type == entity_type)
            if entity_id is not None:
                stmt = stmt.where(Evidence.entity_id == entity_id)
            if evidence_category_id is not None:
                stmt = stmt.where(Evidence.evidence_category_id == evidence_category_id)
            stmt = stmt.order_by(Evidence.uploaded_at.desc())
            if limit:
                stmt = stmt.limit(limit)
            rows = session.scalars(stmt).all()
            return [_to_dict(r) for r in rows]

    def get(self, evidence_id: int) -> dict[str, Any]:
        with get_session() as session:
            obj = session.get(Evidence, evidence_id)
            if obj is None:
                raise ValidationError(f"Evidence id={evidence_id} not found")
            return _to_dict(obj)

    def get_path(self, evidence_id: int) -> Path:
        """Return the absolute path to the stored evidence file."""
        data = self.get(evidence_id)
        return get_settings().evidence_dir / data["relative_path"]

    def update(self, evidence_id: int, **fields: Any) -> dict[str, Any]:
        """Patch mutable metadata on an evidence record (title/description/category/link)."""
        allowed = {
            "title",
            "description",
            "evidence_category_id",
            "entity_type",
            "entity_id",
            "uploaded_by",
        }
        clean = {k: v for k, v in fields.items() if k in allowed}
        with get_session() as session:
            obj = session.get(Evidence, evidence_id)
            if obj is None:
                raise ValidationError(f"Evidence id={evidence_id} not found")
            if clean:
                for key, value in clean.items():
                    setattr(obj, key, value)
                session.commit()
                session.refresh(obj)
            return _to_dict(obj)

    def delete(self, evidence_id: int, *, remove_file: bool = True) -> None:
        with get_session() as session:
            obj = session.get(Evidence, evidence_id)
            if obj is None:
                raise ValidationError(f"Evidence id={evidence_id} not found")
            if remove_file:
                f = get_settings().evidence_dir / obj.relative_path
                if f.exists():
                    f.unlink()
            session.delete(obj)
            session.commit()


def _to_dict(obj: Any) -> dict[str, Any]:
    return {c.name: getattr(obj, c.name) for c in obj.__table__.columns}  # type: ignore[attr-defined]
