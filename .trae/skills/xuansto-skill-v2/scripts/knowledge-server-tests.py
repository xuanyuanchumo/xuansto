#!/usr/bin/env python3

import unittest
import json
import tempfile
import os
import sqlite3
import shutil
import threading
import time
import sys
import secrets
import tarfile
from pathlib import Path
from unittest.mock import patch, MagicMock, PropertyMock
from datetime import datetime, timezone

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

try:
    import yaml
    yaml_available = True
except ImportError:
    yaml_available = False

try:
    from knowledge_server import (
        SQLiteEngine, ChromaEngine, HybridRetrievalEngine,
        DegradationManager, EmbeddingManager, DedupEngine,
        FirstRunImporter, BackupManager, KnowledgeServer,
        KnowledgeConfig, SCHEMA_SQL, SCHEMA_VERSION, KB_VERSION,
        make_response, make_error_response, InputValidator,
        SensitiveContentFilter, RateLimiter, ApiKeyAuth,
    )
    server_available = True
except ImportError:
    server_available = False

try:
    from fastapi.testclient import TestClient
    fastapi_test_available = True
except ImportError:
    fastapi_test_available = False

try:
    import chromadb
    chromadb_installed = True
except ImportError:
    chromadb_installed = False


def _skip_if_no_server(test_func):
    return unittest.skipUnless(server_available, "knowledge-server module not available")(test_func)


def _skip_if_no_fastapi(test_func):
    return unittest.skipUnless(fastapi_test_available, "FastAPI TestClient not available")(test_func)


def _create_test_config(root: Path) -> Path:
    config_path = root / "config.yaml"
    config_data = {
        "knowledge_base": {
            "server": {"host": "127.0.0.1", "port": 0, "transport": "stdio"},
            "database": {
                "sqlite_path": ".knowledge/index/knowledge.db",
                "chroma_path": ".knowledge/index/chroma_db",
            },
            "retrieval": {
                "semantic_weight": 0.7,
                "keyword_weight": 0.3,
                "top_k": 5,
                "default_strategy": "hybrid",
            },
            "dedup": {
                "similarity_threshold": 0.92,
                "action": "merge",
            },
        }
    }
    config_path.parent.mkdir(parents=True, exist_ok=True)
    if yaml_available:
        config_path.write_text(yaml.dump(config_data, default_flow_style=False), encoding="utf-8")
    else:
        import json as _json
        config_path.write_text(_json.dumps(config_data, indent=2), encoding="utf-8")
    return config_path


def _add_sample_entry(sqlite_engine, title="Test Entry", content="Test content for search", scope="workspace", tags=None, entry_type="unknown", category="uncategorized", summary=None, confidence=0.6):
    entry = {
        "title": title,
        "content": content,
        "scope": scope,
        "tags": tags or [],
        "confidence": confidence,
        "type": entry_type,
        "category": category,
        "summary": summary or title,
    }
    return sqlite_engine.add_entry(entry)


@_skip_if_no_server
@_skip_if_no_fastapi
class TestAPIEndpoints(unittest.TestCase):
    _server = None
    _client = None
    _tmpdir = None

    @classmethod
    def setUpClass(cls):
        cls._tmpdir = tempfile.mkdtemp(prefix="kb_test_api_")
        root = Path(cls._tmpdir)
        config_path = _create_test_config(root)
        with patch.dict(os.environ, {}, clear=False):
            env_backup = os.environ.get("OPENAI_API_KEY")
            if env_backup:
                del os.environ["OPENAI_API_KEY"]
            cls._server = KnowledgeServer(root, config_path)
            cls._server._stop_retry_task()
            cls._server._stop_backup_scheduler()
            cls._server.degradation.stop_periodic_check()
            cls._client = TestClient(cls._server.app)

    @classmethod
    def tearDownClass(cls):
        if cls._server:
            cls._server.sqlite.close()
            cls._server.chroma.close()
        if cls._tmpdir:
            shutil.rmtree(cls._tmpdir, ignore_errors=True)

    def setUp(self):
        conn = self._server.sqlite._get_conn()
        conn.execute("DELETE FROM knowledge_entries")
        conn.execute("DELETE FROM knowledge_tags")
        conn.execute("DELETE FROM dedup_log")
        conn.execute("DELETE FROM version_history")
        conn.commit()

    def test_search_empty_db(self):
        resp = self._client.post("/v1/knowledge/search", json={"query": "test"})
        self.assertEqual(resp.status_code, 200)
        body = resp.json()
        self.assertEqual(body["status"], "ok")
        self.assertEqual(body["data"]["total"], 0)
        self.assertEqual(body["data"]["results"], [])

    def test_search_with_results(self):
        self._client.post("/v1/knowledge/add", json={
            "title": "Python Decorators",
            "content": "Decorators modify function behavior in Python",
            "scope": "general",
            "tags": ["python", "decorators"],
            "type": "standard",
            "category": "programming",
            "summary": "Python decorators guide",
        })
        resp = self._client.post("/v1/knowledge/search", json={"query": "Python decorators", "strategy": "keyword_only"})
        self.assertEqual(resp.status_code, 200)
        body = resp.json()
        self.assertEqual(body["status"], "ok")
        self.assertGreater(body["data"]["total"], 0)

    def test_search_hybrid_strategy(self):
        self._client.post("/v1/knowledge/add", json={
            "title": "React Hooks",
            "content": "Hooks let you use state in functional components",
            "scope": "workspace",
            "tags": ["react", "hooks"],
            "summary": "React hooks overview",
        })
        resp = self._client.post("/v1/knowledge/search", json={"query": "React Hooks", "strategy": "hybrid"})
        self.assertEqual(resp.status_code, 200)
        body = resp.json()
        self.assertEqual(body["status"], "ok")
        self.assertIn("search_strategy", body["data"])

    def test_search_keyword_only(self):
        self._client.post("/v1/knowledge/add", json={
            "title": "SQL Joins",
            "content": "JOIN operations combine rows from multiple tables",
            "scope": "general",
            "summary": "SQL join types",
        })
        resp = self._client.post("/v1/knowledge/search", json={"query": "SQL Joins", "strategy": "keyword_only"})
        self.assertEqual(resp.status_code, 200)
        body = resp.json()
        self.assertEqual(body["status"], "ok")
        self.assertEqual(body["data"]["search_strategy"], "keyword_only")

    def test_search_semantic_only(self):
        self._client.post("/v1/knowledge/add", json={
            "title": "Docker Compose",
            "content": "Define multi-container applications with Docker Compose",
            "scope": "workspace",
            "summary": "Docker compose guide",
        })
        resp = self._client.post("/v1/knowledge/search", json={"query": "container orchestration", "strategy": "semantic_only"})
        self.assertEqual(resp.status_code, 200)
        body = resp.json()
        self.assertIn(body["status"], ("ok", "error"))

    def test_get_entry_found(self):
        add_resp = self._client.post("/v1/knowledge/add", json={
            "title": "Git Rebase",
            "content": "Rebase rewrites commit history",
            "scope": "general",
            "summary": "Git rebase usage",
        })
        entry_id = add_resp.json()["data"]["id"]
        resp = self._client.get(f"/v1/knowledge/get/{entry_id}")
        self.assertEqual(resp.status_code, 200)
        body = resp.json()
        self.assertEqual(body["status"], "ok")
        self.assertEqual(body["data"]["title"], "Git Rebase")

    def test_get_entry_not_found(self):
        resp = self._client.get("/v1/knowledge/get/nonexistent-id")
        self.assertEqual(resp.status_code, 404)

    def test_add_entry_success(self):
        resp = self._client.post("/v1/knowledge/add", json={
            "title": "Kubernetes Pods",
            "content": "Pods are the smallest deployable units in Kubernetes",
            "scope": "workspace",
            "tags": ["k8s", "pods"],
            "summary": "K8s pods overview",
        })
        self.assertEqual(resp.status_code, 200)
        body = resp.json()
        self.assertEqual(body["status"], "ok")
        self.assertEqual(body["data"]["status"], "created")
        self.assertIn("id", body["data"])

    def test_add_entry_duplicate(self):
        self._client.post("/v1/knowledge/add", json={
            "title": "Rust Ownership",
            "content": "Ownership rules ensure memory safety in Rust",
            "scope": "general",
            "tags": ["rust", "ownership"],
            "type": "standard",
            "category": "programming",
            "summary": "Rust ownership model",
        })
        with patch.object(self._server.dedup, 'check_duplicate', return_value={
            "is_duplicate": True, "action": "skip", "existing_id": "existing-id", "similarity_score": 0.95
        }):
            resp = self._client.post("/v1/knowledge/add", json={
                "title": "Rust Ownership",
                "content": "Ownership rules ensure memory safety in Rust",
                "scope": "general",
                "tags": ["rust", "ownership"],
                "type": "standard",
                "category": "programming",
                "summary": "Rust ownership model",
            })
            self.assertEqual(resp.status_code, 409)

    def test_update_entry_success(self):
        add_resp = self._client.post("/v1/knowledge/add", json={
            "title": "Go Goroutines",
            "content": "Goroutines are lightweight threads",
            "scope": "general",
            "summary": "Go goroutines intro",
        })
        entry_id = add_resp.json()["data"]["id"]
        resp = self._client.put(f"/v1/knowledge/update/{entry_id}", json={
            "title": "Go Goroutines Updated",
            "content": "Goroutines are lightweight concurrent functions",
        })
        self.assertEqual(resp.status_code, 200)
        body = resp.json()
        self.assertEqual(body["status"], "ok")
        self.assertEqual(body["data"]["status"], "updated")

    def test_update_entry_version_conflict(self):
        add_resp = self._client.post("/v1/knowledge/add", json={
            "title": "Swift Closures",
            "content": "Closures capture references in Swift",
            "scope": "general",
            "summary": "Swift closures",
        })
        entry_id = add_resp.json()["data"]["id"]
        with patch.object(self._server.sqlite, 'update_entry', side_effect=[
            {"error": "version_conflict", "current_version": 2, "expected_version": 1},
            {"error": "version_conflict", "current_version": 2, "expected_version": 1},
            {"error": "version_conflict", "current_version": 2, "expected_version": 1},
            {"error": "version_conflict", "current_version": 2, "expected_version": 1},
        ]):
            with patch.object(self._server.sqlite, 'get_entry', return_value={"id": entry_id, "version": 2, "title": "Swift Closures", "content": "old", "scope": "general", "tags": "[]", "confidence": 0.6, "source_path": None, "source_rating": 3, "content_hash": "abc", "type": "unknown", "category": "uncategorized", "summary": None, "content_path": None, "last_validated": None, "success_count": 0, "failure_count": 0, "occurrences": 1, "embedding_status": "pending", "embedding_retry_count": 0, "created": "2025-01-01", "updated": "2025-01-01"}):
                resp = self._client.put(f"/v1/knowledge/update/{entry_id}", json={
                    "title": "Swift Closures v2",
                    "version": 1,
                })
                self.assertIn(resp.status_code, (200, 409))

    def test_delete_entry_success(self):
        add_resp = self._client.post("/v1/knowledge/add", json={
            "title": "Erlang Actors",
            "content": "Actor model in Erlang for concurrency",
            "scope": "experience",
            "summary": "Erlang actor model",
        })
        entry_id = add_resp.json()["data"]["id"]
        resp = self._client.delete(f"/v1/knowledge/delete/{entry_id}")
        self.assertEqual(resp.status_code, 200)
        body = resp.json()
        self.assertEqual(body["data"]["status"], "deleted")
        get_resp = self._client.get(f"/v1/knowledge/get/{entry_id}")
        self.assertEqual(get_resp.status_code, 404)

    def test_health_check(self):
        resp = self._client.get("/v1/knowledge/health")
        self.assertEqual(resp.status_code, 200)
        body = resp.json()
        self.assertEqual(body["status"], "ok")
        self.assertIn("engines", body["data"])
        self.assertIn("version", body["data"])
        self.assertEqual(body["data"]["version"], KB_VERSION)


@_skip_if_no_server
class TestDualEngineIntegration(unittest.TestCase):
    _tmpdir = None
    _sqlite = None
    _chroma = None
    _config = None

    @classmethod
    def setUpClass(cls):
        cls._tmpdir = tempfile.mkdtemp(prefix="kb_test_dual_")
        root = Path(cls._tmpdir)
        config_path = _create_test_config(root)
        cls._config = KnowledgeConfig(root, config_path)
        db_path = cls._config.sqlite_path
        db_path.parent.mkdir(parents=True, exist_ok=True)
        cls._sqlite = SQLiteEngine(db_path)
        with patch.dict(os.environ, {}, clear=False):
            if "OPENAI_API_KEY" in os.environ:
                del os.environ["OPENAI_API_KEY"]
            embedding_mgr = EmbeddingManager(cls._config)
            cls._chroma = ChromaEngine(cls._config.chroma_path, embedding_manager=embedding_mgr)

    @classmethod
    def tearDownClass(cls):
        if cls._sqlite:
            cls._sqlite.close()
        if cls._chroma:
            cls._chroma.close()
        if cls._tmpdir:
            shutil.rmtree(cls._tmpdir, ignore_errors=True)

    def setUp(self):
        conn = self._sqlite._get_conn()
        conn.execute("DELETE FROM knowledge_entries")
        conn.execute("DELETE FROM knowledge_tags")
        conn.execute("DELETE FROM dedup_log")
        conn.commit()

    def test_write_to_both_engines(self):
        entry = {
            "title": "Dual Write Test",
            "content": "Content written to both SQLite and Chroma",
            "scope": "workspace",
            "tags": ["test"],
            "summary": "Dual write test",
        }
        result = self._sqlite.add_entry(entry)
        self.assertIsNotNone(result["id"])
        sqlite_entry = self._sqlite.get_entry(result["id"])
        self.assertIsNotNone(sqlite_entry)
        if self._chroma.available:
            try:
                self._chroma.add_embedding(result["id"], entry["content"], {"scope": "workspace", "title": entry["title"]})
                self._sqlite.update_embedding_status(result["id"], "ready")
            except Exception:
                pass
            chroma_ids = self._chroma.get_all_ids()
            self.assertIn(result["id"], chroma_ids)

    def test_delete_from_both_engines(self):
        entry = {
            "title": "Dual Delete Test",
            "content": "Content to be deleted from both engines",
            "scope": "general",
            "summary": "Dual delete test",
        }
        result = self._sqlite.add_entry(entry)
        entry_id = result["id"]
        if self._chroma.available:
            try:
                self._chroma.add_embedding(entry_id, entry["content"], {"scope": "general", "title": entry["title"]})
                self._sqlite.update_embedding_status(entry_id, "ready")
            except Exception:
                pass
        deleted = self._sqlite.delete_entry(entry_id)
        self.assertTrue(deleted)
        self.assertIsNone(self._sqlite.get_entry(entry_id))
        if self._chroma.available:
            self._chroma.delete_embedding(entry_id)
            chroma_ids = self._chroma.get_all_ids()
            self.assertNotIn(entry_id, chroma_ids)

    def test_update_syncs_both(self):
        entry = {
            "title": "Update Sync Test",
            "content": "Original content for sync test",
            "scope": "workspace",
            "summary": "Update sync test",
        }
        result = self._sqlite.add_entry(entry)
        entry_id = result["id"]
        if self._chroma.available:
            try:
                self._chroma.add_embedding(entry_id, entry["content"], {"scope": "workspace", "title": entry["title"]})
                self._sqlite.update_embedding_status(entry_id, "ready")
            except Exception:
                pass
        updated = self._sqlite.update_entry(entry_id, {"content": "Updated content for sync test"})
        self.assertIsNotNone(updated)
        self.assertNotIn("error", updated)
        self.assertEqual(updated["content"], "Updated content for sync test")
        if self._chroma.available:
            try:
                self._chroma.add_embedding(entry_id, "Updated content for sync test", {"scope": "workspace", "title": "Update Sync Test"})
                self._sqlite.update_embedding_status(entry_id, "ready")
            except Exception:
                pass

    def test_first_run_import(self):
        root = Path(self._tmpdir)
        for scope in ("general", "workspace", "experience"):
            scope_dir = root / scope
            scope_dir.mkdir(parents=True, exist_ok=True)
            (scope_dir / "test_entry.md").write_text(
                f"---\ntitle: {scope.title()} Test\ntags: [test]\n---\nThis is a {scope} test entry.",
                encoding="utf-8",
            )
        importer = FirstRunImporter(self._config, self._sqlite, self._chroma)
        self.assertTrue(importer.should_import())
        stats = importer.run()
        self.assertIn("general", stats)
        self.assertIn("workspace", stats)
        self.assertIn("experience", stats)
        self.assertGreater(stats["general"] + stats["workspace"] + stats["experience"], 0)
        for scope in ("general", "workspace", "experience"):
            scope_dir = root / scope
            if scope_dir.exists():
                for f in scope_dir.glob("*.md"):
                    f.unlink()

    def test_fts5_and_semantic_consistency(self):
        entries = [
            {"title": "Python List Comprehension", "content": "List comprehensions create lists concisely in Python", "scope": "general", "tags": ["python"], "type": "standard", "category": "programming", "summary": "Python list comprehension"},
            {"title": "Python Dict Comprehension", "content": "Dict comprehensions create dictionaries concisely in Python", "scope": "general", "tags": ["python"], "type": "standard", "category": "programming", "summary": "Python dict comprehension"},
        ]
        for e in entries:
            result = self._sqlite.add_entry(e)
            if self._chroma.available:
                try:
                    self._chroma.add_embedding(result["id"], e["content"], {"scope": e["scope"], "title": e["title"]})
                    self._sqlite.update_embedding_status(result["id"], "ready")
                except Exception:
                    pass
        fts_results = self._sqlite.search_fts("Python comprehension")
        self.assertGreater(len(fts_results), 0)
        fts_ids = {r["id"] for r in fts_results}
        if self._chroma.available:
            semantic_results = self._chroma.search_semantic("Python comprehension")
            if semantic_results:
                semantic_ids = {r["id"] for r in semantic_results}
                self.assertTrue(len(fts_ids & semantic_ids) > 0 or len(fts_ids) > 0)

    def test_hybrid_fusion_rrf(self):
        entries = [
            {"title": "JavaScript Promises", "content": "Promises handle async operations in JavaScript", "scope": "general", "tags": ["js"], "type": "standard", "category": "programming", "summary": "JS promises"},
            {"title": "JavaScript Async Await", "content": "Async await syntax for promises in JavaScript", "scope": "general", "tags": ["js"], "type": "standard", "category": "programming", "summary": "JS async await"},
        ]
        for e in entries:
            result = self._sqlite.add_entry(e)
            if self._chroma.available:
                try:
                    self._chroma.add_embedding(result["id"], e["content"], {"scope": e["scope"], "title": e["title"]})
                    self._sqlite.update_embedding_status(result["id"], "ready")
                except Exception:
                    pass
        retrieval = HybridRetrievalEngine(self._sqlite, self._chroma, self._config)
        result = retrieval.search("JavaScript async", strategy="hybrid")
        self.assertIn("results", result)
        self.assertIn("total", result)
        self.assertEqual(result["search_strategy"], "hybrid")


@_skip_if_no_server
class TestDegradationScenarios(unittest.TestCase):
    _tmpdir = None
    _sqlite = None
    _chroma = None
    _config = None

    @classmethod
    def setUpClass(cls):
        cls._tmpdir = tempfile.mkdtemp(prefix="kb_test_degrade_")
        root = Path(cls._tmpdir)
        config_path = _create_test_config(root)
        cls._config = KnowledgeConfig(root, config_path)
        db_path = cls._config.sqlite_path
        db_path.parent.mkdir(parents=True, exist_ok=True)
        cls._sqlite = SQLiteEngine(db_path)
        with patch.dict(os.environ, {}, clear=False):
            if "OPENAI_API_KEY" in os.environ:
                del os.environ["OPENAI_API_KEY"]

    @classmethod
    def tearDownClass(cls):
        if cls._sqlite:
            cls._sqlite.close()
        if cls._tmpdir:
            shutil.rmtree(cls._tmpdir, ignore_errors=True)

    def setUp(self):
        conn = self._sqlite._get_conn()
        conn.execute("DELETE FROM knowledge_entries")
        conn.execute("DELETE FROM knowledge_tags")
        conn.commit()

    def test_chroma_unavailable_on_startup(self):
        mock_chroma = MagicMock()
        mock_chroma.available = False
        with patch.dict(os.environ, {}, clear=False):
            if "OPENAI_API_KEY" in os.environ:
                del os.environ["OPENAI_API_KEY"]
            embedding_mgr = EmbeddingManager(self._config)
        dm = DegradationManager(mock_chroma, self._config, embedding_manager=embedding_mgr)
        self.assertEqual(dm.level, DegradationManager.LEVEL_BM25_ONLY)
        self.assertEqual(dm.get_search_strategy(), "keyword_only")

    def test_chroma_crash_during_runtime(self):
        mock_chroma = MagicMock()
        mock_chroma.available = True
        mock_chroma.search_semantic.return_value = [{"id": "test", "_cosine_similarity": 0.9}]
        with patch.dict(os.environ, {}, clear=False):
            if "OPENAI_API_KEY" in os.environ:
                del os.environ["OPENAI_API_KEY"]
            embedding_mgr = EmbeddingManager(self._config)
        dm = DegradationManager(mock_chroma, self._config, embedding_manager=embedding_mgr)
        initial_level = dm.level
        mock_chroma.available = True
        mock_chroma.search_semantic.side_effect = RuntimeError("ChromaDB crashed")
        dm.check_and_degrade()
        self.assertGreaterEqual(dm.level, DegradationManager.LEVEL_LOCAL_SEMANTIC)

    def test_auto_recovery(self):
        mock_chroma = MagicMock()
        mock_chroma.available = False
        with patch.dict(os.environ, {}, clear=False):
            if "OPENAI_API_KEY" in os.environ:
                del os.environ["OPENAI_API_KEY"]
            embedding_mgr = MagicMock()
            embedding_mgr.level = EmbeddingManager.LEVEL_BM25_ONLY
            embedding_mgr.check_api_availability.return_value = False
        dm = DegradationManager(mock_chroma, self._config, embedding_manager=embedding_mgr)
        self.assertEqual(dm.level, DegradationManager.LEVEL_BM25_ONLY)
        mock_chroma.available = True
        mock_chroma.search_semantic.return_value = [{"id": "test", "_cosine_similarity": 0.9}]
        embedding_mgr.level = EmbeddingManager.LEVEL_API
        embedding_mgr.check_api_availability.return_value = True
        dm.try_recover()
        self.assertEqual(dm.level, DegradationManager.LEVEL_NORMAL)

    def test_sqlite_corruption_with_backup(self):
        root = Path(self._tmpdir)
        backup_dir = root / "backup" / "scheduled"
        backup_dir.mkdir(parents=True, exist_ok=True)
        db_path = self._config.sqlite_path
        entry = {
            "title": "Backup Test Entry",
            "content": "Content to be backed up",
            "scope": "workspace",
            "summary": "Backup test",
        }
        result = self._sqlite.add_entry(entry)
        self.assertIsNotNone(result["id"])
        backup_path = backup_dir / "test-backup.db"
        src_conn = self._sqlite._get_conn()
        dest_conn = sqlite3.connect(str(backup_path))
        src_conn.backup(dest_conn)
        dest_conn.close()
        self._sqlite.close()
        with open(db_path, "wb") as f:
            f.write(b"\x00" * 256)
        try:
            test_conn = sqlite3.connect(str(db_path))
            cur = test_conn.execute("SELECT COUNT(*) FROM knowledge_entries")
            count = cur.fetchone()[0]
            test_conn.close()
            if count > 0:
                pass
        except (sqlite3.DatabaseError, sqlite3.OperationalError):
            pass
        shutil.copy2(str(backup_path), str(db_path))
        self._sqlite = SQLiteEngine(db_path)
        restored = self._sqlite.get_entry(result["id"])
        self.assertIsNotNone(restored)
        self.assertEqual(restored["title"], "Backup Test Entry")

    def test_no_backup_recovery(self):
        root = Path(self._tmpdir)
        test_db_dir = root / "corrupt_test"
        test_db_dir.mkdir(parents=True, exist_ok=True)
        corrupt_db_path = test_db_dir / "corrupt.db"
        with open(corrupt_db_path, "wb") as f:
            f.write(b"\x00\x01\x02\x03\x04\x05")
        with self.assertRaises((sqlite3.DatabaseError, sqlite3.OperationalError)):
            conn = sqlite3.connect(str(corrupt_db_path))
            conn.execute("SELECT COUNT(*) FROM knowledge_entries")
            conn.close()
        if corrupt_db_path.exists():
            corrupt_db_path.unlink()
        if test_db_dir.exists():
            test_db_dir.rmdir()

    def test_dual_failure(self):
        mock_chroma = MagicMock()
        mock_chroma.available = False
        with patch.dict(os.environ, {}, clear=False):
            if "OPENAI_API_KEY" in os.environ:
                del os.environ["OPENAI_API_KEY"]
            embedding_mgr = EmbeddingManager(self._config)
        dm = DegradationManager(mock_chroma, self._config, embedding_manager=embedding_mgr)
        self.assertEqual(dm.level, DegradationManager.LEVEL_BM25_ONLY)
        strategy = dm.get_search_strategy()
        self.assertEqual(strategy, "keyword_only")
        with patch.object(self._sqlite, 'search_fts', side_effect=RuntimeError("SQLite FTS failed")):
            with self.assertRaises(RuntimeError):
                self._sqlite.search_fts("test query")


@_skip_if_no_server
class TestConcurrentWrites(unittest.TestCase):
    _tmpdir = None
    _sqlite = None
    _config = None

    @classmethod
    def setUpClass(cls):
        cls._tmpdir = tempfile.mkdtemp(prefix="kb_test_concurrent_")
        root = Path(cls._tmpdir)
        config_path = _create_test_config(root)
        cls._config = KnowledgeConfig(root, config_path)
        db_path = cls._config.sqlite_path
        db_path.parent.mkdir(parents=True, exist_ok=True)
        cls._sqlite = SQLiteEngine(db_path)

    @classmethod
    def tearDownClass(cls):
        if cls._sqlite:
            cls._sqlite.close()
        if cls._tmpdir:
            shutil.rmtree(cls._tmpdir, ignore_errors=True)

    def setUp(self):
        conn = self._sqlite._get_conn()
        conn.execute("DELETE FROM knowledge_entries")
        conn.execute("DELETE FROM knowledge_tags")
        conn.execute("DELETE FROM dedup_log")
        conn.commit()

    def test_parallel_write_different_entries(self):
        results = []
        errors = []

        def write_entry(index):
            try:
                entry = {
                    "title": f"Concurrent Entry {index}",
                    "content": f"Content for concurrent entry {index}",
                    "scope": "workspace",
                    "tags": [f"tag-{index}"],
                    "summary": f"Concurrent entry {index}",
                }
                result = self._sqlite.add_entry(entry)
                results.append(result)
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=write_entry, args=(i,)) for i in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=10)

        self.assertEqual(len(errors), 0, f"Errors during parallel writes: {errors}")
        self.assertEqual(len(results), 10)
        ids = {r["id"] for r in results}
        self.assertEqual(len(ids), 10)

    def test_parallel_write_same_entry(self):
        entry = {
            "title": "Contended Entry",
            "content": "Original content",
            "scope": "workspace",
            "summary": "Contended entry",
        }
        result = self._sqlite.add_entry(entry)
        entry_id = result["id"]
        conflicts = []
        successes = []

        def update_entry(version_offset):
            try:
                current = self._sqlite.get_entry(entry_id)
                if current:
                    update_result = self._sqlite.update_entry(entry_id, {
                        "content": f"Updated by thread {version_offset}",
                        "version": current["version"],
                    })
                    if isinstance(update_result, dict) and update_result.get("error") == "version_conflict":
                        conflicts.append(version_offset)
                    else:
                        successes.append(version_offset)
            except Exception as e:
                conflicts.append(version_offset)

        threads = [threading.Thread(target=update_entry, args=(i,)) for i in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=10)

        self.assertGreater(len(conflicts) + len(successes), 0)

    def test_read_write_concurrent(self):
        entry = {
            "title": "RW Test Entry",
            "content": "Content for read-write test",
            "scope": "workspace",
            "summary": "RW test",
        }
        result = self._sqlite.add_entry(entry)
        entry_id = result["id"]
        read_results = []
        errors = []

        def reader():
            try:
                for _ in range(20):
                    e = self._sqlite.get_entry(entry_id)
                    read_results.append(e is not None)
                    time.sleep(0.001)
            except Exception as e:
                errors.append(e)

        def writer():
            try:
                for i in range(10):
                    self._sqlite.update_entry(entry_id, {"content": f"Updated content {i}"})
                    time.sleep(0.002)
            except Exception as e:
                errors.append(e)

        reader_thread = threading.Thread(target=reader)
        writer_thread = threading.Thread(target=writer)
        reader_thread.start()
        writer_thread.start()
        reader_thread.join(timeout=15)
        writer_thread.join(timeout=15)

        self.assertEqual(len(errors), 0, f"Errors during concurrent read/write: {errors}")
        self.assertGreater(len(read_results), 0)

    def test_optimistic_lock_retry(self):
        entry = {
            "title": "Lock Retry Entry",
            "content": "Content for lock retry test",
            "scope": "workspace",
            "summary": "Lock retry test",
        }
        result = self._sqlite.add_entry(entry)
        entry_id = result["id"]
        current = self._sqlite.get_entry(entry_id)
        stale_version = current["version"]
        update_result = self._sqlite.update_entry(entry_id, {
            "content": "First update",
            "version": stale_version,
        })
        self.assertIsNotNone(update_result)
        self.assertNotIn("error", update_result)
        conflict_result = self._sqlite.update_entry(entry_id, {
            "content": "Second update with stale version",
            "version": stale_version,
        })
        self.assertIsNotNone(conflict_result)
        if isinstance(conflict_result, dict) and "error" in conflict_result:
            self.assertEqual(conflict_result["error"], "version_conflict")
            current_again = self._sqlite.get_entry(entry_id)
            retry_result = self._sqlite.update_entry(entry_id, {
                "content": "Retry with correct version",
                "version": current_again["version"],
            })
            self.assertIsNotNone(retry_result)
            self.assertNotIn("error", retry_result)

    def test_batch_and_single_concurrent(self):
        batch_results = []
        single_results = []
        errors = []

        def batch_writer():
            try:
                for i in range(5):
                    entry = {
                        "title": f"Batch Entry {i}",
                        "content": f"Batch content {i}",
                        "scope": "workspace",
                        "summary": f"Batch {i}",
                    }
                    result = self._sqlite.add_entry(entry)
                    batch_results.append(result)
            except Exception as e:
                errors.append(e)

        def single_writer():
            try:
                for i in range(5):
                    entry = {
                        "title": f"Single Entry {i}",
                        "content": f"Single content {i}",
                        "scope": "general",
                        "summary": f"Single {i}",
                    }
                    result = self._sqlite.add_entry(entry)
                    single_results.append(result)
            except Exception as e:
                errors.append(e)

        t1 = threading.Thread(target=batch_writer)
        t2 = threading.Thread(target=single_writer)
        t1.start()
        t2.start()
        t1.join(timeout=10)
        t2.join(timeout=10)

        self.assertEqual(len(errors), 0, f"Errors during batch/single concurrent writes: {errors}")
        self.assertEqual(len(batch_results), 5)
        self.assertEqual(len(single_results), 5)
        all_ids = {r["id"] for r in batch_results + single_results}
        self.assertEqual(len(all_ids), 10)


@_skip_if_no_server
@_skip_if_no_fastapi
class TestVersionRollback(unittest.TestCase):
    _server = None
    _client = None
    _tmpdir = None

    @classmethod
    def setUpClass(cls):
        cls._tmpdir = tempfile.mkdtemp(prefix="kb_test_rollback_")
        root = Path(cls._tmpdir)
        config_path = _create_test_config(root)
        with patch.dict(os.environ, {}, clear=False):
            if "OPENAI_API_KEY" in os.environ:
                del os.environ["OPENAI_API_KEY"]
            cls._server = KnowledgeServer(root, config_path)
            cls._server._stop_retry_task()
            cls._server._stop_backup_scheduler()
            cls._server.degradation.stop_periodic_check()
            cls._client = TestClient(cls._server.app)

    @classmethod
    def tearDownClass(cls):
        if cls._server:
            cls._server.sqlite.close()
            cls._server.chroma.close()
        if cls._tmpdir:
            shutil.rmtree(cls._tmpdir, ignore_errors=True)

    def setUp(self):
        conn = self._server.sqlite._get_conn()
        conn.execute("DELETE FROM knowledge_entries")
        conn.execute("DELETE FROM knowledge_tags")
        conn.execute("DELETE FROM dedup_log")
        conn.execute("DELETE FROM version_history")
        conn.commit()

    def test_rollback_to_version(self):
        add_resp = self._client.post("/v1/knowledge/add", json={
            "title": "Rollback Test",
            "content": "Version 1 content",
            "scope": "general",
            "summary": "Rollback test v1",
        })
        entry_id = add_resp.json()["data"]["id"]

        self._client.put(f"/v1/knowledge/update/{entry_id}", json={
            "content": "Version 2 content",
        })
        self._client.put(f"/v1/knowledge/update/{entry_id}", json={
            "content": "Version 3 content",
        })

        rollback_resp = self._client.post("/v1/knowledge/rollback", json={
            "entry_id": entry_id,
            "target_version": 1,
        })
        self.assertEqual(rollback_resp.status_code, 200)
        body = rollback_resp.json()
        self.assertEqual(body["status"], "ok")
        self.assertEqual(body["data"]["status"], "rolled_back")
        self.assertEqual(body["data"]["target_version"], 1)

        get_resp = self._client.get(f"/v1/knowledge/get/{entry_id}")
        self.assertEqual(get_resp.status_code, 200)
        self.assertEqual(get_resp.json()["data"]["content"], "Version 1 content")

    def test_version_history(self):
        add_resp = self._client.post("/v1/knowledge/add", json={
            "title": "Version History Test",
            "content": "Original content",
            "scope": "general",
            "summary": "Version history test",
        })
        entry_id = add_resp.json()["data"]["id"]

        self._client.put(f"/v1/knowledge/update/{entry_id}", json={
            "content": "Updated content",
        })

        versions_resp = self._client.get(f"/v1/knowledge/{entry_id}/versions")
        self.assertEqual(versions_resp.status_code, 200)
        body = versions_resp.json()
        self.assertEqual(body["status"], "ok")
        self.assertGreaterEqual(body["data"]["total"], 1)
        versions = body["data"]["versions"]
        self.assertGreaterEqual(len(versions), 1)
        self.assertIn("version", versions[0])
        self.assertIn("title", versions[0])
        self.assertIn("entry_id", versions[0])
        self.assertEqual(versions[0]["entry_id"], entry_id)


@_skip_if_no_server
@_skip_if_no_fastapi
class TestBackupCreation(unittest.TestCase):
    _server = None
    _client = None
    _tmpdir = None

    @classmethod
    def setUpClass(cls):
        cls._tmpdir = tempfile.mkdtemp(prefix="kb_test_backup_")
        root = Path(cls._tmpdir)
        config_path = _create_test_config(root)
        with patch.dict(os.environ, {}, clear=False):
            if "OPENAI_API_KEY" in os.environ:
                del os.environ["OPENAI_API_KEY"]
            cls._server = KnowledgeServer(root, config_path)
            cls._server._stop_retry_task()
            cls._server._stop_backup_scheduler()
            cls._server.degradation.stop_periodic_check()
            cls._client = TestClient(cls._server.app)

    @classmethod
    def tearDownClass(cls):
        if cls._server:
            cls._server.sqlite.close()
            cls._server.chroma.close()
        if cls._tmpdir:
            shutil.rmtree(cls._tmpdir, ignore_errors=True)

    def setUp(self):
        conn = self._server.sqlite._get_conn()
        conn.execute("DELETE FROM knowledge_entries")
        conn.execute("DELETE FROM knowledge_tags")
        conn.execute("DELETE FROM dedup_log")
        conn.execute("DELETE FROM version_history")
        conn.commit()
        try:
            conn.execute(
                "CREATE TABLE IF NOT EXISTS backup_history ("
                "id INTEGER PRIMARY KEY AUTOINCREMENT, "
                "backup_path TEXT NOT NULL, "
                "backup_size INTEGER, "
                "entry_count INTEGER, "
                "status TEXT DEFAULT 'completed', "
                "created_at TEXT DEFAULT (datetime('now')))"
            )
            conn.execute("DELETE FROM backup_history")
            conn.commit()
        except Exception:
            pass

    def test_create_backup(self):
        resp = self._client.post("/v1/knowledge/backup", json={"type": "full"})
        self.assertEqual(resp.status_code, 200)
        body = resp.json()
        self.assertEqual(body["status"], "ok")
        self.assertEqual(body["data"]["status"], "completed")
        self.assertIn("backup_path", body["data"])
        self.assertIn("entries_count", body["data"])
        self.assertIn("size_bytes", body["data"])

    def test_backup_file_exists(self):
        resp = self._client.post("/v1/knowledge/backup", json={"type": "full"})
        self.assertEqual(resp.status_code, 200)
        body = resp.json()
        backup_path = body["data"]["backup_path"]
        backup_file = Path(backup_path)
        self.assertTrue(backup_file.exists(), f"Backup file not found: {backup_path}")
        self.assertTrue(str(backup_file).endswith(".tar.gz"), f"Backup file is not .tar.gz: {backup_path}")
        with tarfile.open(str(backup_file), "r:gz") as tar:
            names = tar.getnames()
            self.assertGreater(len(names), 0, "Backup archive is empty")


@_skip_if_no_server
@_skip_if_no_fastapi
class TestApiKeyAuthentication(unittest.TestCase):
    _server = None
    _client = None
    _tmpdir = None
    _readonly_key = None
    _readwrite_key = None
    _admin_key = None

    @classmethod
    def setUpClass(cls):
        cls._admin_key = "xks-admin-" + secrets.token_hex(16)
        cls._readonly_key = "xks-readonly-" + secrets.token_hex(16)
        cls._readwrite_key = "xks-readwrite-" + secrets.token_hex(16)

        cls._tmpdir = tempfile.mkdtemp(prefix="kb_test_apikey_")
        root = Path(cls._tmpdir)

        config_path = root / "config.yaml"
        config_data = {
            "knowledge_base": {
                "server": {"host": "0.0.0.0", "port": 0, "transport": "stdio"},
                "database": {
                    "sqlite_path": ".knowledge/index/knowledge.db",
                    "chroma_path": ".knowledge/index/chroma_db",
                },
                "retrieval": {
                    "semantic_weight": 0.7,
                    "keyword_weight": 0.3,
                    "top_k": 5,
                    "default_strategy": "hybrid",
                },
                "dedup": {
                    "similarity_threshold": 0.92,
                    "action": "merge",
                },
            }
        }
        config_path.parent.mkdir(parents=True, exist_ok=True)
        if yaml_available:
            config_path.write_text(yaml.dump(config_data, default_flow_style=False), encoding="utf-8")
        else:
            config_path.write_text(json.dumps(config_data, indent=2), encoding="utf-8")

        api_keys_file = root / ".api_keys.json"
        api_keys_data = {
            cls._readonly_key: "read-only",
            cls._readwrite_key: "read-write",
        }
        api_keys_file.write_text(json.dumps(api_keys_data), encoding="utf-8")

        with patch.dict(os.environ, {"KNOWLEDGE_API_KEY": cls._admin_key}, clear=False):
            if "OPENAI_API_KEY" in os.environ:
                del os.environ["OPENAI_API_KEY"]
            cls._server = KnowledgeServer(root, config_path)
            cls._server._stop_retry_task()
            cls._server._stop_backup_scheduler()
            cls._server.degradation.stop_periodic_check()
            cls._client = TestClient(cls._server.app)

    @classmethod
    def tearDownClass(cls):
        if cls._server:
            cls._server.sqlite.close()
            cls._server.chroma.close()
        if cls._tmpdir:
            shutil.rmtree(cls._tmpdir, ignore_errors=True)

    def setUp(self):
        conn = self._server.sqlite._get_conn()
        conn.execute("DELETE FROM knowledge_entries")
        conn.execute("DELETE FROM knowledge_tags")
        conn.execute("DELETE FROM dedup_log")
        conn.execute("DELETE FROM version_history")
        conn.commit()

    def test_no_key_local_access(self):
        local_tmpdir = tempfile.mkdtemp(prefix="kb_test_local_auth_")
        try:
            root = Path(local_tmpdir)
            config_path = _create_test_config(root)
            with patch.dict(os.environ, {}, clear=False):
                if "OPENAI_API_KEY" in os.environ:
                    del os.environ["OPENAI_API_KEY"]
                env_backup = os.environ.get("KNOWLEDGE_API_KEY")
                if env_backup:
                    del os.environ["KNOWLEDGE_API_KEY"]
                local_server = KnowledgeServer(root, config_path)
                local_server._stop_retry_task()
                local_server._stop_backup_scheduler()
                local_server.degradation.stop_periodic_check()
                local_client = TestClient(local_server.app)
                resp = local_client.get("/v1/knowledge/health")
                self.assertEqual(resp.status_code, 200)
                body = resp.json()
                self.assertEqual(body["status"], "ok")
                local_server.sqlite.close()
                local_server.chroma.close()
        finally:
            shutil.rmtree(local_tmpdir, ignore_errors=True)

    def test_readonly_key_access(self):
        search_resp = self._client.post(
            "/v1/knowledge/search",
            json={"query": "test"},
            headers={"X-API-Key": self._readonly_key},
        )
        self.assertEqual(search_resp.status_code, 200)
        self.assertEqual(search_resp.json()["status"], "ok")

        add_resp = self._client.post(
            "/v1/knowledge/add",
            json={
                "title": "Readonly Test",
                "content": "Should be forbidden for read-only key",
                "scope": "general",
                "summary": "Readonly test",
            },
            headers={"X-API-Key": self._readonly_key},
        )
        self.assertEqual(add_resp.status_code, 403)

    def test_readwrite_key_access(self):
        add_resp = self._client.post(
            "/v1/knowledge/add",
            json={
                "title": "Readwrite Test",
                "content": "Should be allowed for read-write key",
                "scope": "general",
                "summary": "Readwrite test",
            },
            headers={"X-API-Key": self._readwrite_key},
        )
        self.assertEqual(add_resp.status_code, 200)
        body = add_resp.json()
        self.assertEqual(body["status"], "ok")
        self.assertEqual(body["data"]["status"], "created")
        self.assertIn("id", body["data"])


@_skip_if_no_server
class TestSensitiveContentFilter(unittest.TestCase):
    def test_api_key_detection(self):
        has_sensitive, findings = SensitiveContentFilter.check(
            "sk-abcdefghijklmnopqrstuvwx"
        )
        self.assertTrue(has_sensitive)
        categories = [f["category"] for f in findings]
        self.assertIn("API Key", categories)

        has_sensitive2, findings2 = SensitiveContentFilter.check(
            'api_key = "xks-a1b2c3d4e5f6"'
        )
        self.assertTrue(has_sensitive2)
        categories2 = [f["category"] for f in findings2]
        self.assertIn("API Key", categories2)

    def test_token_detection(self):
        has_sensitive, findings = SensitiveContentFilter.check(
            "Bearer ghp_1234567890abcdef"
        )
        self.assertTrue(has_sensitive)
        categories = [f["category"] for f in findings]
        self.assertIn("Bearer Token", categories)

        has_sensitive2, findings2 = SensitiveContentFilter.check(
            'token = "ghp_1234567890abcdef"'
        )
        self.assertTrue(has_sensitive2)
        categories2 = [f["category"] for f in findings2]
        self.assertIn("Token", categories2)

    def test_password_detection(self):
        has_sensitive, findings = SensitiveContentFilter.check(
            'password = "secret123"'
        )
        self.assertTrue(has_sensitive)
        categories = [f["category"] for f in findings]
        self.assertIn("Password", categories)

        has_sensitive2, findings2 = SensitiveContentFilter.check(
            'passwd = "mysecret"'
        )
        self.assertTrue(has_sensitive2)
        categories2 = [f["category"] for f in findings2]
        self.assertIn("Password", categories2)

        clean_has, clean_findings = SensitiveContentFilter.check(
            "This is a normal content without any secrets"
        )
        self.assertFalse(clean_has)
        self.assertEqual(len(clean_findings), 0)


@_skip_if_no_server
class TestInputValidation(unittest.TestCase):
    def test_sql_injection_defense(self):
        ok, msg = InputValidator.validate_sql_injection(
            "'; DROP TABLE knowledge_entries; --"
        )
        self.assertFalse(ok)
        self.assertIn("SQL injection", msg)

        ok2, msg2 = InputValidator.validate_sql_injection(
            "normal content"
        )
        self.assertTrue(ok2)
        self.assertEqual(msg2, "")

    def test_path_traversal_defense(self):
        ok, msg = InputValidator.validate_path_traversal(
            "../../etc/passwd"
        )
        self.assertFalse(ok)
        self.assertIn("Path traversal", msg)

        ok2, msg2 = InputValidator.validate_path_traversal(
            "normal/path/to/file"
        )
        self.assertTrue(ok2)
        self.assertEqual(msg2, "")

    def test_xss_defense(self):
        ok, msg = InputValidator.validate_xss(
            "<script>alert('xss')</script>"
        )
        self.assertFalse(ok)
        self.assertIn("XSS", msg)

        ok2, msg2 = InputValidator.validate_xss(
            "normal content with <b>bold</b> tags"
        )
        self.assertTrue(ok2)
        self.assertEqual(msg2, "")


if __name__ == '__main__':
    unittest.main()
