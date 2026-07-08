"""Generic base repository.

Provides CRUD and query primitives over a SQLAlchemy model. Concrete
repositories (in ``app/repositories``) subclass this and add domain-specific
queries. Keeping shared logic here honours DRY and SOLID.
"""

from __future__ import annotations

from typing import Any, Generic, Sequence, TypeVar

from sqlalchemy import delete as sa_delete
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError
from app.database.db import get_session

M = TypeVar("M")


class BaseRepository(Generic[M]):
    """Generic repository for a single ORM model."""

    model: type[M]

    def __init__(self, session: Session | None = None) -> None:
        self._session = session

    # --- session handling ---
    def _get_session(self) -> Session:
        if self._session is not None:
            return self._session
        # Fallback for ad-hoc use; prefer injecting a session for transactions.
        return get_session().__enter__()

    # --- CRUD ---
    def create(self, **fields: Any) -> M:
        with get_session() as session:
            obj = self.model(**fields)  # type: ignore[call-arg]
            session.add(obj)
            session.commit()
            session.refresh(obj)
            return obj

    def get(self, entity_id: int) -> M:
        with get_session() as session:
            obj = session.get(self.model, entity_id)
            if obj is None:
                raise NotFoundError(
                    f"{self.model.__name__} with id={entity_id} not found"
                )
            # Detach to avoid cross-session usage issues.
            session.expunge(obj)
            return obj

    def list(self, *, limit: int | None = None, offset: int = 0) -> Sequence[M]:
        with get_session() as session:
            stmt = select(self.model).offset(offset)
            if limit is not None:
                stmt = stmt.limit(limit)
            rows = session.scalars(stmt).all()
            for r in rows:
                session.expunge(r)
            return rows

    def update(self, entity_id: int, **fields: Any) -> M:
        with get_session() as session:
            obj = session.get(self.model, entity_id)
            if obj is None:
                raise NotFoundError(
                    f"{self.model.__name__} with id={entity_id} not found"
                )
            for key, value in fields.items():
                if value is not None:
                    setattr(obj, key, value)
            session.commit()
            session.refresh(obj)
            session.expunge(obj)
            return obj

    def delete(self, entity_id: int) -> None:
        with get_session() as session:
            obj = session.get(self.model, entity_id)
            if obj is None:
                raise NotFoundError(
                    f"{self.model.__name__} with id={entity_id} not found"
                )
            session.delete(obj)
            session.commit()

    # --- helpers ---
    def count(self) -> int:
        with get_session() as session:
            return session.scalar(select(func.count()).select_from(self.model)) or 0

    def find_by_name(self, name: str) -> M | None:
        with get_session() as session:
            stmt = select(self.model).where(self.model.name == name)  # type: ignore[attr-defined]
            obj = session.scalars(stmt).first()
            if obj is not None:
                session.expunge(obj)
            return obj

    def bulk_insert(self, rows: list[dict[str, Any]]) -> int:
        with get_session() as session:
            objs = [self.model(**r) for r in rows]  # type: ignore[call-arg]
            session.add_all(objs)
            session.commit()
            return len(objs)

    def delete_all(self) -> int:
        with get_session() as session:
            count = session.scalar(select(func.count()).select_from(self.model)) or 0
            session.execute(sa_delete(self.model))
            session.commit()
            return count
