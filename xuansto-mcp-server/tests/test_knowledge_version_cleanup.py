from __future__ import annotations

import os
from datetime import datetime, timezone, timedelta
from unittest.mock import patch

import pytest

from xuansto_mcp.core.database import cleanup_knowledge_versions, persist_state


@pytest.fixture
def version_db(tmp_work_dir, patch_config):
    import xuansto_mcp.core.database as db_mod
    original_db_path = db_mod.DB_PATH
    db_mod.DB_PATH = tmp_work_dir / "test_version.db"
    db_mod.WORK_DIR = tmp_work_dir
    try:
        db_mod.init_db()
        yield db_mod
    finally:
        db_mod.DB_PATH = original_db_path


def _insert_knowledge_entry(db_mod, entry_id: str, scope: str, title: str, updated_at: str) -> None:
    db_mod.persist_state("knowledge_entries", {
        "id": entry_id,
        "scope": scope,
        "title": title,
        "content": f"content for {entry_id}",
        "tags_json": [],
        "metadata_json": {},
        "updated_at": updated_at,
    })


def test_cleanup_no_duplicates(version_db):
    _insert_knowledge_entry(version_db, "kb-001", "general", "Unique Entry", datetime.now(timezone.utc).isoformat())
    result = cleanup_knowledge_versions(keep_last_n=10, keep_marked=True)
    assert result["total_deleted"] == 0
    assert result["groups_processed"] == 0


def test_cleanup_removes_old_versions(version_db):
    base_time = datetime.now(timezone.utc)
    for i in range(15):
        ts = (base_time - timedelta(hours=i)).isoformat()
        _insert_knowledge_entry(version_db, f"kb-v{i:03d}", "general", "Same Title", ts)

    result = cleanup_knowledge_versions(keep_last_n=10, keep_marked=True)
    assert result["total_deleted"] == 5
    assert result["groups_processed"] == 1

    remaining = version_db.load_state("knowledge_entries", {"scope": "general"})
    active = [e for e in remaining if e.get("deleted_at") is None]
    assert len(active) == 10


def test_cleanup_keep_last_n_custom(version_db):
    base_time = datetime.now(timezone.utc)
    for i in range(20):
        ts = (base_time - timedelta(hours=i)).isoformat()
        _insert_knowledge_entry(version_db, f"kb-c{i:03d}", "workspace", "Custom Title", ts)

    result = cleanup_knowledge_versions(keep_last_n=5, keep_marked=True)
    assert result["total_deleted"] == 15
    assert result["keep_last_n"] == 5


def test_cleanup_multiple_groups(version_db):
    base_time = datetime.now(timezone.utc)
    for i in range(12):
        ts = (base_time - timedelta(hours=i)).isoformat()
        _insert_knowledge_entry(version_db, f"kb-g1-{i:03d}", "general", "Title A", ts)
    for i in range(8):
        ts = (base_time - timedelta(hours=i)).isoformat()
        _insert_knowledge_entry(version_db, f"kb-g2-{i:03d}", "general", "Title B", ts)

    result = cleanup_knowledge_versions(keep_last_n=10, keep_marked=True)
    assert result["groups_processed"] == 1
    assert result["total_deleted"] == 2


def test_cleanup_nothing_below_threshold(version_db):
    base_time = datetime.now(timezone.utc)
    for i in range(5):
        ts = (base_time - timedelta(hours=i)).isoformat()
        _insert_knowledge_entry(version_db, f"kb-few-{i:03d}", "general", "Few Title", ts)

    result = cleanup_knowledge_versions(keep_last_n=10, keep_marked=True)
    assert result["total_deleted"] == 0
    assert result["groups_processed"] == 0


def test_config_cleanup_keep_last_n_default():
    from xuansto_mcp.core.config import KNOWLEDGE_VERSION_CLEANUP_KEEP_LAST_N
    assert KNOWLEDGE_VERSION_CLEANUP_KEEP_LAST_N == 10


def test_config_cleanup_keep_last_n_from_env():
    with patch.dict(os.environ, {"XUANSTO_KNOWLEDGE_CLEANUP_KEEP_LAST_N": "20"}):
        import importlib
        import xuansto_mcp.core.config as cfg_mod
        importlib.reload(cfg_mod)
        assert cfg_mod.KNOWLEDGE_VERSION_CLEANUP_KEEP_LAST_N == 20
    importlib.reload(cfg_mod)
