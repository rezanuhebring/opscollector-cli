from __future__ import annotations

import pytest

from app.services.dashboard_service import DashboardService


@pytest.fixture()
def svc() -> DashboardService:
    return DashboardService()


class TestDashboardService:
    def test_summary_structure(self, svc: DashboardService):
        summary = svc.summary()
        assert summary["objectives"]["total"] >= 0
        assert summary["bau"]["total"] == 0
        assert summary["incidents"]["total"] == 0
        assert summary["changes"]["total"] == 0
        assert summary["evidence"]["total"] == 0
        assert "outstanding" in summary

    def test_weekly_trend(self, svc: DashboardService):
        trend = svc.weekly_trend(weeks=4)
        assert len(trend) == 4
        assert all("week" in w and "bau" in w for w in trend)

    def test_objectives_progress_returns_list(self, svc: DashboardService):
        out = svc.objectives_progress()
        assert isinstance(out, list)
