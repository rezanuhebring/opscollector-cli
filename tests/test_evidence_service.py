from __future__ import annotations

import shutil
import tempfile
from pathlib import Path

import pytest

from app.core.exceptions import EvidenceError, ValidationError
from app.services.evidence_service import EvidenceService


class TestEvidenceService:
    @pytest.fixture()
    def svc(self):
        return EvidenceService()

    def _make_file(self, tmp_path: Path, name="sample.txt") -> Path:
        f = tmp_path / name
        f.write_text("hello", encoding="utf-8")
        return f

    def test_add_file(self, svc: EvidenceService, tmp_path: Path):
        src = self._make_file(tmp_path)
        rec = svc.add_file(source_path=src, title="My evidence", uploaded_by="tester")
        assert rec["original_filename"] == "sample.txt"
        assert rec["extension"] == "txt"
        assert rec["title"] == "My evidence"
        assert "id" in rec
        assert "relative_path" in rec

    def test_add_file_invalid_ext(self, svc: EvidenceService, tmp_path: Path):
        src = tmp_path / "bad.exe"
        src.write_text("x", encoding="utf-8")
        with pytest.raises(ValidationError):
            svc.add_file(source_path=src, title="bad")

    def test_add_file_missing_source(self, svc: EvidenceService):
        with pytest.raises(EvidenceError):
            svc.add_file(source_path="/does/not/exist.txt", title="x")

    def test_add_file_too_large(self, svc: EvidenceService, tmp_path: Path):
        src = tmp_path / "huge.txt"
        src.write_bytes(b"x" * (100 * 1024 * 1024 + 1))
        with pytest.raises(ValidationError):
            svc.add_file(source_path=src, title="big")

    def test_add_file_with_entity(self, svc: EvidenceService, tmp_path: Path):
        src = self._make_file(tmp_path)
        rec = svc.add_file(source_path=src, entity_type="bau", entity_id=1)
        assert rec["entity_type"] == "bau"
        assert rec["entity_id"] == 1

    def test_add_file_invalid_entity(self, svc: EvidenceService, tmp_path: Path):
        src = self._make_file(tmp_path)
        with pytest.raises(ValidationError):
            svc.add_file(source_path=src, entity_type="weird")

    def test_list_empty(self, svc: EvidenceService):
        assert svc.list() == []

    def test_list_by_entity(self, svc: EvidenceService, tmp_path: Path):
        src = self._make_file(tmp_path)
        svc.add_file(source_path=src, entity_type="bau", entity_id=1)
        svc.add_file(source_path=src, entity_type="incident", entity_id=2)
        bau_ev = svc.list(entity_type="bau")
        assert len(bau_ev) == 1
        assert bau_ev[0]["entity_type"] == "bau"

    def test_get_existing(self, svc: EvidenceService, tmp_path: Path):
        rec = svc.add_file(source_path=self._make_file(tmp_path))
        got = svc.get(rec["id"])
        assert got["title"] == rec["title"]

    def test_get_missing_raises(self, svc: EvidenceService):
        with pytest.raises(ValidationError):
            svc.get(999_999)

    def test_get_path(self, svc: EvidenceService, tmp_path: Path):
        rec = svc.add_file(source_path=self._make_file(tmp_path))
        p = svc.get_path(rec["id"])
        assert p.exists()

    def test_delete(self, svc: EvidenceService, tmp_path: Path):
        rec = svc.add_file(source_path=self._make_file(tmp_path))
        rel = rec["relative_path"]
        svc.delete(rec["id"])
        with pytest.raises(ValidationError):
            svc.get(rec["id"])
