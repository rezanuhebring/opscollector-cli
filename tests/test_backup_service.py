from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest

from app.services.backup_service import BackupService


@pytest.fixture()
def svc() -> BackupService:
    return BackupService()


class TestBackupService:
    def test_backup_creates_manifest(self, svc: BackupService):
        path = svc.backup(label="ut")
        assert path.is_dir()
        assert (path / "manifest.json").exists()
        with open(path / "manifest.json", "r", encoding="utf-8") as fh:
            data = json.load(fh)
        assert data["label"] == "ut"

    def test_list_backups(self, svc: BackupService):
        svc.backup(label="a")
        svc.backup(label="b")
        items = svc.list_backups()
        assert len(items) == 2
        assert items[0]["label"] == "b"

    def test_restore_config(self, svc: BackupService, tmp_path: Path):
        b = svc.backup(label="cfg")
        svc.restore(backup_name=b.name, selective=["config"])
        # In the isolated test configuration the config is restored into the
        # temporary backup_dir, not the real project root.
        assert (b / "config.json").exists()
