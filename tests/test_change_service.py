from __future__ import annotations

import pytest

from app.core.exceptions import ValidationError
from app.services.change_service import ChangeService


@pytest.fixture()
def svc() -> ChangeService:
    return ChangeService()


class TestChangeService:
    def test_create_minimal(self, svc: ChangeService):
        record = svc.create(date="2026-07-08", title="Patch")
        assert record["title"] == "Patch"
        assert record["change_type"] == "Change"
        assert record["id"] is not None

    def test_create_change_type(self, svc: ChangeService):
        record = svc.create(date="2026-07-08", title="Patch", change_type="Emergency")
        assert record["change_type"] == "Emergency"

    def test_get_existing(self, svc: ChangeService):
        created = svc.create(date="2026-07-08", title="A")
        got = svc.get(created["id"])
        assert got["title"] == "A"

    def test_get_missing_raises(self, svc: ChangeService):
        with pytest.raises(ValidationError):
            svc.get(999_999)

    def test_list_filters(self, svc: ChangeService):
        svc.create(date="2026-07-01", title="a", change_type="Normal")
        svc.create(date="2026-07-02", title="b", change_type="Emergency")
        by_type = svc.list(change_type="Emergency", limit=50)
        assert len(by_type) == 1

        from_d = svc.list(date_from="2026-07-02", limit=50)
        assert all(r["date"] >= "2026-07-02" for r in from_d)

    def test_update_fields(self, svc: ChangeService):
        created = svc.create(date="2026-07-08", title="old")
        updated = svc.update(created["id"], title="new")
        assert updated["title"] == "new"

    def test_delete_existing(self, svc: ChangeService):
        created = svc.create(date="2026-07-08", title="del")
        svc.delete(created["id"])
        with pytest.raises(ValidationError):
            svc.get(created["id"])
