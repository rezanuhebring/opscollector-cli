"""Service layer: business logic independent of the CLI.

Services depend only on the repository/ORM layer, never on Typer/Rich, so the
logic can be reused by a future web/API backend. Each service wraps a repository
(or the session directly) and exposes domain operations with validation.
"""

from __future__ import annotations

from .master_service import MasterService
from .bau_service import BAUService
from .okr_service import OKRService
from .incident_service import IncidentService
from .change_service import ChangeService
from .evidence_service import EvidenceService
from .search_service import SearchService
from .dashboard_service import DashboardService
from .backup_service import BackupService
from .excel_service import ExcelService
from .watcher_service import start_watcher

__all__ = [
    "MasterService",
    "BAUService",
    "OKRService",
    "IncidentService",
    "ChangeService",
    "EvidenceService",
    "SearchService",
    "DashboardService",
    "BackupService",
    "ExcelService",
    "start_watcher",
]
