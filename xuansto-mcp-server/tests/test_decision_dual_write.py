from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

import pytest

from xuansto_mcp.tools import decision_log as dl
from xuansto_mcp.tools.decision_log import _get_connection


@pytest.fixture(autouse=True)
def _isolate_db(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    db_path = tmp_path / "decisions.db"
    json_path = tmp_path / "decisions.json"
    monkeypatch.setattr(dl, "DECISIONS_DB", db_path)
    monkeypatch.setattr(dl, "DECISIONS_JSON_FILE", json_path)
    monkeypatch.setattr(dl, "DECISIONS_FILE", json_path)
    monkeypatch.setattr(dl, "WORK_DIR", tmp_path)
    dl._cache.clear()
    conn = _get_connection()
    try:
        conn.executescript(dl._CREATE_TABLE_SQL)
        try:
            conn.executescript(dl._CREATE_FTS_SQL)
            conn.executescript(dl._CREATE_FTS_TRIGGERS_SQL)
        except Exception:
            pass
        conn.executescript(dl._CREATE_INDEX_SQL)
        conn.commit()
    finally:
        conn.close()
    yield


class TestDualWriteOnLog:
    def test_log_writes_to_both_sqlite_and_file(self):
        result = dl._log_decision(title="Test Decision", decision="Use SQLite")
        entry_id = result["id"]
        conn = _get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM decisions WHERE id = ?", (entry_id,))
            assert cursor.fetchone() is not None
        finally:
            conn.close()
        assert dl.DECISIONS_JSON_FILE.exists()
        file_data = json.loads(dl.DECISIONS_JSON_FILE.read_text(encoding="utf-8"))
        assert any(e["id"] == entry_id for e in file_data)

    def test_file_write_failure_rolls_back_sqlite(self):
        with patch("xuansto_mcp.tools.decision_log._write_decision_file", side_effect=OSError("disk full")), \
             pytest.raises(OSError, match="disk full"):
            dl._log_decision(title="Rollback Test")
        conn = _get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM decisions WHERE title = 'Rollback Test'")
            count = cursor.fetchone()[0]
            assert count == 0
        finally:
            conn.close()


class TestReconcileDecisions:
    def test_reconcile_no_inconsistencies(self):
        dl._log_decision(title="Consistent Entry")
        result = dl._reconcile_decisions()
        assert result["total_inconsistencies"] == 0
        assert result["repaired"] == 0
        assert result["success_rate"] == 100.0

    def test_reconcile_entry_only_in_sqlite(self):
        dl._log_decision(title="SQLite Only")
        dl.DECISIONS_JSON_FILE.write_text("[]", encoding="utf-8")
        result = dl._reconcile_decisions()
        assert result["only_in_sqlite"] >= 1
        assert result["repaired"] >= 1
        file_data = json.loads(dl.DECISIONS_JSON_FILE.read_text(encoding="utf-8"))
        assert any(e.get("title") == "SQLite Only" for e in file_data)

    def test_reconcile_entry_only_in_file(self):
        entry = {
            "id": "ADR-20260101-001",
            "title": "File Only",
            "context": "",
            "decision": "Test",
            "rationale": "",
            "alternatives": [],
            "status": "proposed",
            "created_at": "2026-01-01T00:00:00",
            "updated_at": "2026-01-01T00:00:00",
        }
        dl.DECISIONS_JSON_FILE.write_text(
            json.dumps([entry], ensure_ascii=False), encoding="utf-8"
        )
        result = dl._reconcile_decisions()
        assert result["only_in_file"] >= 1
        assert result["repaired"] >= 1
        conn = _get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM decisions WHERE id = ?", ("ADR-20260101-001",))
            assert cursor.fetchone() is not None
        finally:
            conn.close()

    def test_reconcile_returns_success_rate(self):
        dl._log_decision(title="Good Entry")
        dl.DECISIONS_JSON_FILE.write_text("[]", encoding="utf-8")
        result = dl._reconcile_decisions()
        assert "success_rate" in result
        assert isinstance(result["success_rate"], float)

    def test_reconcile_empty_stores(self):
        dl.DECISIONS_JSON_FILE.write_text("[]", encoding="utf-8")
        result = dl._reconcile_decisions()
        assert result["total_inconsistencies"] == 0
        assert result["success_rate"] == 100.0
