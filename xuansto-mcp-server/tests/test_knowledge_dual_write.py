from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from xuansto_mcp.core.database import (
    cleanup_stale_pending_entries,
    get_db,
    init_db,
    persist_knowledge_dual_write,
    persist_state,
    reconcile_knowledge_stores,
)


@pytest.fixture(autouse=True)
def _isolate_db(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    db_path = tmp_path / "xuansto.db"
    monkeypatch.setattr("xuansto_mcp.core.database.DB_PATH", db_path)
    monkeypatch.setattr("xuansto_mcp.core.database.WORK_DIR", tmp_path)
    init_db()
    yield


class TestPersistKnowledgeDualWrite:
    def test_dual_write_synced_when_chroma_succeeds(self):
        def chroma_ok(entry_id, data):
            return True

        result = persist_knowledge_dual_write("k1", {"title": "Test", "content": "Hello"}, chroma_ok)
        assert result["status"] == "synced"
        assert result["entry_id"] == "k1"
        conn = get_db()
        try:
            cursor = conn.execute("SELECT sync_status FROM knowledge_entries WHERE id = 'k1'")
            row = cursor.fetchone()
            assert row is not None
            assert row["sync_status"] == "ready"
        finally:
            conn.close()

    def test_dual_write_pending_when_chroma_fails(self):
        def chroma_fail(entry_id, data):
            return False

        result = persist_knowledge_dual_write("k2", {"title": "Fail", "content": "Bad"}, chroma_fail)
        assert result["status"] == "pending"
        conn = get_db()
        try:
            cursor = conn.execute("SELECT sync_status FROM knowledge_entries WHERE id = 'k2'")
            row = cursor.fetchone()
            assert row is not None
            assert row["sync_status"] == "pending"
        finally:
            conn.close()

    def test_dual_write_pending_when_chroma_raises(self):
        def chroma_error(entry_id, data):
            raise RuntimeError("connection refused")

        result = persist_knowledge_dual_write("k3", {"title": "Error", "content": "Oops"}, chroma_error)
        assert result["status"] == "pending"

    def test_dual_write_pending_when_no_chroma_fn(self):
        result = persist_knowledge_dual_write("k4", {"title": "No Chroma", "content": "Skip"})
        assert result["status"] == "pending"

    def test_dual_write_logs_to_reconciliation_on_failure(self):
        def chroma_fail(entry_id, data):
            return False

        persist_knowledge_dual_write("k5", {"title": "Recon", "content": "Log"}, chroma_fail)
        conn = get_db()
        try:
            cursor = conn.execute("SELECT * FROM reconciliation_log WHERE entry_id = 'k5'")
            rows = cursor.fetchall()
            assert len(rows) >= 1
            assert rows[0]["issue_type"] == "write_failed"
        finally:
            conn.close()


class TestReconcileKnowledgeStores:
    def test_reconcile_repairs_pending_entries(self):
        def chroma_ok(entry_id, data):
            return True

        persist_knowledge_dual_write("r1", {"title": "Repair", "content": "Fix me"}, chroma_write_fn=None)
        conn = get_db()
        try:
            cursor = conn.execute("SELECT sync_status FROM knowledge_entries WHERE id = 'r1'")
            assert cursor.fetchone()["sync_status"] == "pending"
        finally:
            conn.close()

        result = reconcile_knowledge_stores(chroma_ok)
        assert result["repaired"] >= 1
        assert result["total_pending"] >= 1

        conn = get_db()
        try:
            cursor = conn.execute("SELECT sync_status FROM knowledge_entries WHERE id = 'r1'")
            assert cursor.fetchone()["sync_status"] == "ready"
        finally:
            conn.close()

    def test_reconcile_reports_failed_when_chroma_fails(self):
        def chroma_fail(entry_id, data):
            return False

        persist_knowledge_dual_write("r2", {"title": "Fail", "content": "No fix"}, chroma_write_fn=None)
        result = reconcile_knowledge_stores(chroma_fail)
        assert result["failed"] >= 1

    def test_reconcile_no_pending_entries(self):
        def chroma_ok(entry_id, data):
            return True

        persist_knowledge_dual_write("r3", {"title": "Synced", "content": "OK"}, chroma_ok)
        result = reconcile_knowledge_stores(chroma_ok)
        assert result["total_pending"] == 0
        assert result["success_rate"] == 100.0

    def test_reconcile_logs_repair_success(self):
        def chroma_ok(entry_id, data):
            return True

        persist_knowledge_dual_write("r4", {"title": "Log", "content": "Repair"}, chroma_write_fn=None)
        reconcile_knowledge_stores(chroma_ok)
        conn = get_db()
        try:
            cursor = conn.execute("SELECT * FROM reconciliation_log WHERE entry_id = 'r4' AND issue_type = 'repair_success'")
            rows = cursor.fetchall()
            assert len(rows) >= 1
        finally:
            conn.close()


class TestCleanupStalePendingEntries:
    def test_cleanup_purges_old_pending_without_chroma(self):
        old_time = (datetime.now(timezone.utc) - timedelta(hours=48)).isoformat()
        persist_state("knowledge_entries", {
            "id": "s1",
            "title": "Stale",
            "content": "Old pending",
            "scope": "general",
            "tags_json": [],
            "sync_status": "pending",
            "created_at": old_time,
            "updated_at": old_time,
        })
        result = cleanup_stale_pending_entries(max_age_hours=24, chroma_write_fn=None)
        assert result["total_stale"] >= 1
        assert result["purged"] >= 1
        conn = get_db()
        try:
            cursor = conn.execute("SELECT deleted_at FROM knowledge_entries WHERE id = 's1'")
            row = cursor.fetchone()
            assert row["deleted_at"] is not None
        finally:
            conn.close()

    def test_cleanup_retries_with_chroma(self):
        old_time = (datetime.now(timezone.utc) - timedelta(hours=48)).isoformat()
        persist_state("knowledge_entries", {
            "id": "s2",
            "title": "Retry",
            "content": "Old but retryable",
            "scope": "general",
            "tags_json": [],
            "sync_status": "pending",
            "created_at": old_time,
            "updated_at": old_time,
        })

        def chroma_ok(entry_id, data):
            return True

        result = cleanup_stale_pending_entries(max_age_hours=24, chroma_write_fn=chroma_ok)
        assert result["retried"] >= 1
        assert result["purged"] == 0
        conn = get_db()
        try:
            cursor = conn.execute("SELECT sync_status, deleted_at FROM knowledge_entries WHERE id = 's2'")
            row = cursor.fetchone()
            assert row["sync_status"] == "ready"
            assert row["deleted_at"] is None
        finally:
            conn.close()

    def test_cleanup_skips_recent_entries(self):
        recent_time = datetime.now(timezone.utc).isoformat()
        persist_state("knowledge_entries", {
            "id": "s3",
            "title": "Recent",
            "content": "Fresh pending",
            "scope": "general",
            "tags_json": [],
            "sync_status": "pending",
            "created_at": recent_time,
            "updated_at": recent_time,
        })
        result = cleanup_stale_pending_entries(max_age_hours=24, chroma_write_fn=None)
        assert result["total_stale"] == 0
        conn = get_db()
        try:
            cursor = conn.execute("SELECT deleted_at FROM knowledge_entries WHERE id = 's3'")
            row = cursor.fetchone()
            assert row["deleted_at"] is None
        finally:
            conn.close()

    def test_cleanup_logs_purge_to_reconciliation(self):
        old_time = (datetime.now(timezone.utc) - timedelta(hours=48)).isoformat()
        persist_state("knowledge_entries", {
            "id": "s4",
            "title": "Purge Log",
            "content": "Check recon log",
            "scope": "general",
            "tags_json": [],
            "sync_status": "pending",
            "created_at": old_time,
            "updated_at": old_time,
        })
        cleanup_stale_pending_entries(max_age_hours=24, chroma_write_fn=None)
        conn = get_db()
        try:
            cursor = conn.execute("SELECT * FROM reconciliation_log WHERE entry_id = 's4' AND issue_type = 'stale_purged'")
            rows = cursor.fetchall()
            assert len(rows) >= 1
        finally:
            conn.close()
