from __future__ import annotations

import pytest

from app.services.search_service import SearchService


@pytest.fixture()
def svc() -> SearchService:
    return SearchService()


class TestSearchService:
    def _seed_bau(self):
        from app.services.bau_service import BAUService
        BAUService().create(date="2026-07-08", title="alpha ops", status_id=1)
        BAUService().create(date="2026-07-09", title="beta ops", status_id=1)

    def _seed_incident(self):
        from app.services.incident_service import IncidentService
        IncidentService().create(date="2026-07-08", title="alpha incident", status_id=1)
        IncidentService().create(date="2026-07-09", title="beta incident", status_id=1)

    def _seed_change(self):
        from app.services.change_service import ChangeService
        ChangeService().create(date="2026-07-08", title="alpha change", status_id=1)
        ChangeService().create(date="2026-07-09", title="beta change", status_id=1)

    def _seed_okr(self):
        from app.services.master_service import MasterService
        from app.services.okr_service import OKRService

        master = MasterService()
        obj = master.create("objective", name="Search OKR Obj", title="SOKR")
        kr = master.create("key_result", name="Search KR", objective_id=obj["id"], target_value=100.0)
        OKRService().create(key_result_id=kr["id"], date="2026-07-08", achievement="protein")
        OKRService().create(key_result_id=kr["id"], date="2026-07-09", achievement="winrate")

    def test_search_empty(self, svc: SearchService):
        result = svc.search(keyword="nothing")
        assert result["bau"] == []
        assert result["okr"] == []
        assert result["incident"] == []
        assert result["change"] == []

    def test_search_bau_keyword(self, svc: SearchService):
        self._seed_bau()
        result = svc.search(keyword="alpha")
        assert len(result["bau"]) == 1
        assert result["bau"][0]["title"] == "alpha ops"

    def test_search_incident_keyword(self, svc: SearchService):
        self._seed_incident()
        result = svc.search(keyword="beta")
        assert len(result["incident"]) == 1

    def test_search_change_keyword(self, svc: SearchService):
        self._seed_change()
        result = svc.search(keyword="alpha")
        assert len(result["change"]) == 1

    def test_search_okr_keyword(self, svc: SearchService):
        self._seed_okr()
        result = svc.search(keyword="winrate")
        assert len(result["okr"]) == 1

    def test_search_entity_types_filter(self, svc: SearchService):
        self._seed_bau()
        self._seed_change()
        result = svc.search(keyword="alpha", entity_types=["bau"])
        assert len(result["bau"]) == 1
        assert result["change"] == []

    def test_search_date_filter(self, svc: SearchService):
        self._seed_bau()
        result = svc.search(date_from="2026-07-09")
        assert all(r["date"] >= "2026-07-09" for r in result["bau"])

    def test_search_returns_all_keys(self, svc: SearchService):
        result = svc.search()
        assert set(result.keys()) == {"bau", "okr", "incident", "change"}
