from __future__ import annotations

import shutil
import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


class _FakeCollection:
    def __init__(self):
        self._docs = {}

    def upsert(self, ids, documents, metadatas=None):
        for i, doc_id in enumerate(ids):
            self._docs[doc_id] = {
                "document": documents[i],
                "metadata": metadatas[i] if metadatas else {},
            }

    def query(self, query_texts, n_results=5):
        matched_ids = []
        matched_docs = []
        matched_metas = []
        matched_dists = []
        query = query_texts[0].lower() if query_texts else ""
        for doc_id, entry in self._docs.items():
            if query in entry["document"].lower():
                matched_ids.append(doc_id)
                matched_docs.append(entry["document"])
                matched_metas.append(entry["metadata"])
                matched_dists.append(0.1)
        return {
            "ids": [matched_ids[:n_results]],
            "documents": [matched_docs[:n_results]],
            "metadatas": [matched_metas[:n_results]],
            "distances": [matched_dists[:n_results]],
        }

    def count(self):
        return len(self._docs)


class _FakeClient:
    _shared_collections: dict[str, _FakeCollection] = {}

    def __init__(self, path=None):
        self._path = path

    def get_or_create_collection(self, name):
        if name not in self._shared_collections:
            self._shared_collections[name] = _FakeCollection()
        return self._shared_collections[name]

    @classmethod
    def _reset(cls):
        cls._shared_collections.clear()


class _FakeChromadb:
    PersistentClient = _FakeClient


class _ImportErrorChromadb:
    @staticmethod
    def PersistentClient(*args, **kwargs):
        raise ImportError("No module named 'chromadb'")


class TestInjectChromaDB(unittest.TestCase):
    def setUp(self):
        _FakeClient._reset()
        self._tmpdir = Path(tempfile.mkdtemp(prefix="test_inject_chroma_"))
        self._db_path = self._tmpdir / "index" / "knowledge.db"
        self._chroma_path = self._tmpdir / "index" / "chroma_db"
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        self._chroma_path.mkdir(parents=True, exist_ok=True)

        conn = sqlite3.connect(str(self._db_path))
        conn.execute("""
            CREATE TABLE IF NOT EXISTS knowledge_entries (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                content TEXT NOT NULL,
                type TEXT NOT NULL DEFAULT 'general',
                metadata_json TEXT DEFAULT '{}',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        """)
        conn.execute("""
            CREATE VIRTUAL TABLE IF NOT EXISTS knowledge_fts
            USING fts5(content, title, type, content=knowledge_entries, content_rowid=rowid, tokenize='unicode61')
        """)
        conn.execute("""
            CREATE TRIGGER IF NOT EXISTS knowledge_ai AFTER INSERT ON knowledge_entries BEGIN
                INSERT INTO knowledge_fts(rowid, content, title, type) VALUES (new.rowid, new.content, new.title, new.type);
            END
        """)
        conn.commit()
        conn.close()

        self._patcher_db = patch(
            "xuansto_mcp.tools.knowledge_search.KNOWLEDGE_DB_PATH",
            self._db_path,
        )
        self._patcher_chroma = patch(
            "xuansto_mcp.tools.knowledge_search.KNOWLEDGE_CHROMA_PATH",
            self._chroma_path,
        )
        self._patcher_general = patch(
            "xuansto_mcp.tools.knowledge_search.KNOWLEDGE_GENERAL_DIR",
            self._tmpdir / "general",
        )
        self._patcher_workspace = patch(
            "xuansto_mcp.tools.knowledge_search.KNOWLEDGE_WORKSPACE_DIR",
            self._tmpdir / "workspace",
        )
        self._patcher_experience = patch(
            "xuansto_mcp.tools.knowledge_search.KNOWLEDGE_EXPERIENCE_DIR",
            self._tmpdir / "experience",
        )
        for p in [
            self._patcher_db,
            self._patcher_chroma,
            self._patcher_general,
            self._patcher_workspace,
            self._patcher_experience,
        ]:
            p.start()

    def tearDown(self):
        for p in [
            self._patcher_db,
            self._patcher_chroma,
            self._patcher_general,
            self._patcher_workspace,
            self._patcher_experience,
        ]:
            p.stop()
        shutil.rmtree(self._tmpdir, ignore_errors=True)

    def test_inject_writes_to_both_sqlite_and_chromadb(self):
        from xuansto_mcp.tools.knowledge_search import _inject_knowledge

        with patch.dict(sys.modules, {"chromadb": _FakeChromadb()}):
            result = _inject_knowledge(
                content="Python async patterns for concurrent programming",
                knowledge_type="general",
                metadata=None,
            )

        self.assertTrue(result["indexed"], "SQLite index should succeed")
        self.assertTrue(result["chroma_indexed"], "ChromaDB index should succeed")

        conn = sqlite3.connect(str(self._db_path))
        cursor = conn.cursor()
        cursor.execute("SELECT content FROM knowledge_entries WHERE id = ?", (result["injected_id"],))
        row = cursor.fetchone()
        conn.close()
        self.assertIsNotNone(row, "Row should exist in SQLite")
        self.assertEqual(row[0], "Python async patterns for concurrent programming")

    def test_inject_works_without_chromadb(self):
        from xuansto_mcp.tools.knowledge_search import _inject_knowledge

        chromadb_backup = sys.modules.get("chromadb")
        try:
            sys.modules["chromadb"] = None

            result = _inject_knowledge(
                content="Fallback knowledge without ChromaDB",
                knowledge_type="general",
                metadata=None,
            )

            self.assertTrue(result["indexed"], "SQLite index should succeed even without ChromaDB")
            self.assertFalse(result["chroma_indexed"], "ChromaDB index should be False when unavailable")
        finally:
            if chromadb_backup is not None:
                sys.modules["chromadb"] = chromadb_backup
            else:
                sys.modules.pop("chromadb", None)

    def test_chromadb_failure_does_not_affect_sqlite(self):
        from xuansto_mcp.tools.knowledge_search import _inject_knowledge

        class _BrokenClient:
            def __init__(self, *args, **kwargs):
                raise RuntimeError("ChromaDB connection failed")

        class _BrokenChromadb:
            PersistentClient = _BrokenClient

        with patch.dict(sys.modules, {"chromadb": _BrokenChromadb()}):
            result = _inject_knowledge(
                content="Knowledge with broken ChromaDB",
                knowledge_type="general",
                metadata=None,
            )

        self.assertTrue(result["indexed"], "SQLite index should succeed even when ChromaDB fails")
        self.assertFalse(result["chroma_indexed"], "ChromaDB index should be False on failure")

        conn = sqlite3.connect(str(self._db_path))
        cursor = conn.cursor()
        cursor.execute("SELECT content FROM knowledge_entries WHERE id = ?", (result["injected_id"],))
        row = cursor.fetchone()
        conn.close()
        self.assertIsNotNone(row, "Row should exist in SQLite despite ChromaDB failure")
        self.assertEqual(row[0], "Knowledge with broken ChromaDB")

    def test_injected_knowledge_found_by_search(self):
        from xuansto_mcp.tools.knowledge_search import _inject_knowledge, _chromadb_search

        fake_chroma = _FakeChromadb()

        with patch.dict(sys.modules, {"chromadb": fake_chroma}):
            _inject_knowledge(
                content="Docker containerization best practices for microservices",
                knowledge_type="general",
                metadata=None,
            )

            search_result = _chromadb_search(
                query="Docker containerization",
                top_k=5,
                scope=None,
                min_confidence=0.0,
            )

        self.assertIsNotNone(search_result, "ChromaDB search should return results")
        self.assertGreater(search_result["total"], 0, "Should find at least one result")
        self.assertEqual(search_result["strategy"], "chromadb_semantic")

    def test_chromadb_not_indexed_when_sqlite_fails(self):
        from xuansto_mcp.tools.knowledge_search import _inject_knowledge

        bad_db_path = self._tmpdir / "nonexistent" / "bad.db"

        with patch(
            "xuansto_mcp.tools.knowledge_search.KNOWLEDGE_DB_PATH",
            bad_db_path,
        ):
            with patch.dict(sys.modules, {"chromadb": _FakeChromadb()}):
                result = _inject_knowledge(
                    content="This should fail SQLite",
                    knowledge_type="general",
                    metadata=None,
                )

        self.assertFalse(result["indexed"], "SQLite index should fail")
        self.assertFalse(result["chroma_indexed"], "ChromaDB should not be attempted when SQLite fails")


if __name__ == "__main__":
    unittest.main()
