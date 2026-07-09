from __future__ import annotations

import pytest

from app.core.exceptions import ValidationError
from app.services.bau_service import BAUService


@pytest.fixture()
def bau_svc() -> BAUService:
    return BAUService()


class TestBAUService:
    def test_create_minimal(self, bau_svc):
        record = bau_svc.create(date="2026-07-08", title="Daily ops")
        assert record["date"] == "2026-07-08"
        assert record["title"] == "Daily ops"
        assert record["id"] is not None

    def test_create_full(self, bau_svc):
        record = bau_svc.create(
            date="2026-07-08",
            title="Deploy release",
            bau_activity_id=1,
            status_id=1,
            pic_id=1,
            department_id=1,
            duration_minutes=45,
            notes="Smooth",
        )
        assert record["duration_minutes"] == 45

    def test_get_existing(self, bau_svc):
        created = bau_svc.create(date="2026-07-08", title="ops")
        got = bau_svc.get(created["id"])
        assert got["title"] == "ops"

    def test_get_missing_raises(self, bau_svc):
        with pytest.raises(ValidationError):
            bau_svc.get(999_999)

    def test_list_empty(self, bau_svc):
        assert bau_svc.list() == []

    def test_list_with_filters(self, bau_svc):
        bau_svc.create(date="2026-07-01", title="alpha", status_id=1)
        bau_svc.create(date="2026-07-02", title="beta", status_id=1)
        bau_svc.create(date="2026-07-03", title="gamma", status_id=1)

        all_recs = bau_svc.list(limit=50)
        assert len(all_recs) == 3

        from_d = bau_svc.list(date_from="2026-07-02", limit=50)
        assert all(r["date"] >= "2026-07-02" for r in from_d)

        to_d = bau_svc.list(date_to="2026-07-02", limit=50)
        assert all(r["date"] <= "2026-07-02" for r in to_d)

        by_status = bau_svc.list(status_id=1, limit=50)
        assert len(by_status) == 3

    def test_delete_existing(self, bau_svc):
        created = bau_svc.create(date="2026-07-10", title="delme")
        bau_svc.delete(created["id"])
        with pytest.raises(ValidationError):
            bau_svc.get(created["id"])

    def test_update_title(self, bau_svc):
        created = bau_svc.create(date="2026-07-08", title="old")
        updated = bau_svc.update(created["id"], title="new")
        assert updated["title"] == "new"

    def test_update_notes(self, bau_svc):
        created = bau_svc.create(date="2026-07-08", title="x")
        updated = bau_svc.update(created["id"], notes="noted")
        assert updated["notes"] == "noted"

    def test_update_missing_raises(self, bau_svc):
        with pytest.raises(ValidationError):
            bau_svc.update(999_999, title="nope")

    def test_delete_existing(self, bau_svc):
        created = bau_svc.create(date="2026-07-08", title="delme")
        bau_svc.delete(created["id"])
        with pytest.raises(ValidationError):
            bau_svc.get(created["id"])

    def test_delete_missing_raises(self, bau_svc):
        with pytest.raises(ValidationError):
            bau_svc.delete(999_999)
