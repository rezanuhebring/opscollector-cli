from __future__ import annotations

import pytest

from app.core.exceptions import ValidationError
from app.services.incident_service import IncidentService


@pytest.fixture()
def svc() -> IncidentService:
    return IncidentService()


class TestIncidentService:
    def test_create_minimal(self, svc: IncidentService):
        record = svc.create(date="2026-07-08", title="DB down")
        assert record["title"] == "DB down"
        assert record["incident_no"].startswith("INC-")
        assert record["severity"] == "Medium"
        assert record["id"] is not None

    def test_get_existing(self, svc: IncidentService):
        created = svc.create(date="2026-07-08", title="Disk full")
        got = svc.get(created["id"])
        assert got["title"] == "Disk full"

    def test_get_missing_raises(self, svc: IncidentService):
        with pytest.raises(ValidationError):
            svc.get(999_999)

    def test_list_filters(self, svc: IncidentService):
        svc.create(date="2026-07-01", title="a", severity="Low")
        svc.create(date="2026-07-02", title="b", severity="High")
        by_sev = svc.list(severity="Low", limit=50)
        assert all(r["severity"] == "Low" for r in by_sev)

        from_d = svc.list(date_from="2026-07-02", limit=50)
        assert all(r["date"] >= "2026-07-02" for r in from_d)

    def test_update_fields(self, svc: IncidentService):
        created = svc.create(date="2026-07-08", title="old")
        updated = svc.update(created["id"], title="new")
        assert updated["title"] == "new"

    def test_update_status(self, svc: IncidentService):
        created = svc.create(date="2026-07-08", title="old")
        updated = svc.update(created["id"], status_id=1)
        assert updated["status_id"] == 1

    def test_delete_existing(self, svc: IncidentService):
        created = svc.create(date="2026-07-08", title="del")
        svc.delete(created["id"])
        with pytest.raises(ValidationError):
            svc.get(created["id"])
