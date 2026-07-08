from __future__ import annotations

import pytest

from app.core.exceptions import ValidationError
from app.services.master_service import MasterService
from app.services.okr_service import OKRService


@pytest.fixture()
def svc() -> OKRService:
    return OKRService()


@pytest.fixture()
def kr_ids() -> list[int]:
    master = MasterService()
    obj = master.create("objective", name="OKR Test Objective", title="OKRTO")
    kr1 = master.create("key_result", name="KR1", objective_id=obj["id"], target_value=100.0)
    kr2 = master.create("key_result", name="KR2", objective_id=obj["id"], target_value=50.0)
    return [kr1["id"], kr2["id"]]


class TestOKRService:
    def test_create_minimal(self, svc: OKRService, kr_ids: list[int]):
        record = svc.create(key_result_id=kr_ids[0], date="2026-07-08")
        assert record["key_result_id"] == kr_ids[0]
        assert record["date"] == "2026-07-08"
        assert record["id"] is not None

    def test_create_full(self, svc: OKRService, kr_ids: list[int]):
        record = svc.create(
            key_result_id=kr_ids[0],
            date="2026-07-08",
            current_value=5.0,
            gap=2.0,
            progress=10.0,
            achievement="Great",
            risk="Low",
            issue="None",
            action_plan="Keep going",
        )
        assert record["achievement"] == "Great"

    def test_get_existing(self, svc: OKRService, kr_ids: list[int]):
        created = svc.create(key_result_id=kr_ids[0], date="2026-07-08")
        got = svc.get(created["id"])
        assert got["date"] == "2026-07-08"

    def test_get_missing_raises(self, svc: OKRService):
        with pytest.raises(ValidationError):
            svc.get(999_999)

    def test_list_empty(self, svc: OKRService):
        assert svc.list() == []

    def test_list_filtered(self, svc: OKRService, kr_ids: list[int]):
        svc.create(key_result_id=kr_ids[0], date="2026-07-01")
        svc.create(key_result_id=kr_ids[1], date="2026-07-02")
        all_ = svc.list(limit=50)
        assert len(all_) == 2

    def test_update_progress(self, svc: OKRService, kr_ids: list[int]):
        created = svc.create(key_result_id=kr_ids[0], date="2026-07-08")
        updated = svc.update(created["id"], progress=55.0)
        assert updated["progress"] == 55.0

    def test_delete_existing(self, svc: OKRService, kr_ids: list[int]):
        created = svc.create(key_result_id=kr_ids[0], date="2026-07-08")
        svc.delete(created["id"])
        with pytest.raises(ValidationError):
            svc.get(created["id"])
