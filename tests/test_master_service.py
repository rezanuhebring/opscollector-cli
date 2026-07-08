from __future__ import annotations

import pytest

from app.core.exceptions import DuplicateError, ValidationError
from app.services.master_service import MasterService


@pytest.fixture()
def svc() -> MasterService:
    return MasterService()


class TestMasterService:
    def test_list_types(self, svc: MasterService):
        types_ = svc.list_types()
        assert isinstance(types_, list)
        assert "objective" in types_
        assert "status" in types_
        assert types_ == sorted(types_)

    def test_create_and_get_objective(self, svc: MasterService):
        created = svc.create("objective", name="Q1 Target", title="T1", description="Desc")
        assert created["name"] == "Q1 Target"
        assert "id" in created

        fetched = svc.get("objective", created["id"])
        assert fetched["name"] == "Q1 Target"

    def test_create_duplicate_raises(self, svc: MasterService):
        svc.create("status", name="Custom")
        with pytest.raises(DuplicateError):
            svc.create("status", name="Custom")

    def test_get_missing_raises(self, svc: MasterService):
        with pytest.raises(ValidationError):
            svc.get("department", 99999)

    def test_list_after_create(self, svc: MasterService):
        svc.create("department", name="IT", description="Tech")
        all_ = svc.list("department")
        assert any(r["name"] == "IT" for r in all_)

    def test_update_department(self, svc: MasterService):
        created = svc.create("department", name="HR", description="Human")
        updated = svc.update("department", created["id"], description="Updated")
        assert updated["description"] == "Updated"
        assert updated["name"] == "HR"

    def test_delete_department(self, svc: MasterService):
        created = svc.create("department", name="Temp", description="Del")
        svc.delete("department", created["id"])
        with pytest.raises(ValidationError):
            svc.get("department", created["id"])

    def test_create_pic_with_optional_fields(self, svc: MasterService):
        created = svc.create("pic", name="Alice", email="alice@example.com", description="PM")
        assert created["email"] == "alice@example.com"

    def test_list_types_unknown(self, svc: MasterService):
        with pytest.raises(ValidationError):
            svc.create("unknown_entity", name="X")
