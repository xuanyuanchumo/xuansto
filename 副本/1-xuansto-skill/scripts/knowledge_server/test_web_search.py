#!/usr/bin/env python3

import unittest
import json
import tempfile
import shutil
import sqlite3
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock
from datetime import datetime, timezone, timedelta

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

try:
    from knowledge_server.web_search import (
        classify_source_rating,
        search_official_docs,
        detect_stale_entries,
        detect_new_tech_dependencies,
        auto_ingest_tech_knowledge,
        OFFICIAL_SOURCES,
        _parse_ddg_results,
        _build_search_url,
    )
    web_search_available = True
except ImportError:
    web_search_available = False


def _skip_if_no_web_search(test_func):
    return unittest.skipUnless(web_search_available, "web_search module not available")(test_func)


@_skip_if_no_web_search
class TestClassifySourceRating(unittest.TestCase):
    def test_classify_source_rating_official(self):
        rating = classify_source_rating("https://docs.python.org/3/library/asyncio.html")
        self.assertEqual(rating, 5)

        rating2 = classify_source_rating("https://developer.mozilla.org/en-US/docs/Web/JavaScript")
        self.assertEqual(rating2, 5)

        rating3 = classify_source_rating("https://react.dev/learn")
        self.assertEqual(rating3, 5)

    def test_classify_source_rating_github(self):
        rating = classify_source_rating("https://github.com/facebook/react/issues/123")
        self.assertEqual(rating, 4)

        rating2 = classify_source_rating("https://github.com/microsoft/TypeScript")
        self.assertEqual(rating2, 4)

        rating3 = classify_source_rating("https://github.com/rust-lang/cargo")
        self.assertEqual(rating3, 4)

    def test_classify_source_rating_stackoverflow(self):
        rating = classify_source_rating("https://stackoverflow.com/questions/12345/python-async")
        self.assertEqual(rating, 3)

        rating2 = classify_source_rating("https://serverfault.stackexchange.com/q/12345")
        self.assertEqual(rating2, 3)

    def test_classify_source_rating_medium(self):
        rating = classify_source_rating("https://medium.com/@user/python-tips")
        self.assertEqual(rating, 2)

        rating2 = classify_source_rating("https://dev.to/user/rust-guide")
        self.assertEqual(rating2, 2)

    def test_classify_source_rating_unknown(self):
        rating = classify_source_rating("https://random-blog.example.com/post/123")
        self.assertEqual(rating, 1)

        rating2 = classify_source_rating("https://unknown-site.org/article")
        self.assertNotEqual(rating2, 1)

    def test_classify_source_rating_github_non_official(self):
        rating = classify_source_rating("https://github.com/random-user/personal-project")
        self.assertEqual(rating, 2)


@_skip_if_no_web_search
class TestSearchOfficialDocs(unittest.TestCase):
    @patch("knowledge_server.web_search._fetch_url")
    def test_search_official_docs_returns_results(self, mock_fetch):
        mock_html = '''
        <a class="result__a" href="https://docs.python.org/3/library/asyncio.html">Python Asyncio</a>
        <a class="result__snippet">Async IO in Python documentation</a>
        '''
        mock_fetch.return_value = mock_html

        results = search_official_docs("asyncio", tech_stack=["python"])
        self.assertIsInstance(results, list)
        if results:
            self.assertIn("source_rating", results[0])
            self.assertIn("title", results[0])
            self.assertIn("url", results[0])
            self.assertGreaterEqual(results[0]["source_rating"], 1)
            self.assertLessEqual(results[0]["source_rating"], 5)

    @patch("knowledge_server.web_search._fetch_url")
    def test_search_official_docs_no_results(self, mock_fetch):
        mock_fetch.return_value = None
        results = search_official_docs("nonexistent query", tech_stack=["python"])
        self.assertEqual(results, [])


@_skip_if_no_web_search
class TestDetectStaleEntries(unittest.TestCase):
    _tmpdir = None
    _db_path = None

    @classmethod
    def setUpClass(cls):
        cls._tmpdir = tempfile.mkdtemp(prefix="kb_test_stale_")
        db_dir = Path(cls._tmpdir) / "db"
        db_dir.mkdir(parents=True, exist_ok=True)
        cls._db_path = str(db_dir / "knowledge.db")

        conn = sqlite3.connect(cls._db_path)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS knowledge_entries (
                id TEXT PRIMARY KEY,
                title TEXT,
                content TEXT,
                scope TEXT DEFAULT 'workspace',
                tags TEXT DEFAULT '[]',
                confidence REAL DEFAULT 0.6,
                source_path TEXT,
                source_rating INTEGER DEFAULT 3,
                content_hash TEXT,
                type TEXT DEFAULT 'unknown',
                category TEXT DEFAULT 'uncategorized',
                summary TEXT,
                content_path TEXT,
                status TEXT DEFAULT 'active',
                last_validated TEXT,
                success_count INTEGER DEFAULT 0,
                failure_count INTEGER DEFAULT 0,
                occurrences INTEGER DEFAULT 1,
                embedding_status TEXT DEFAULT 'pending',
                embedding_retry_count INTEGER DEFAULT 0,
                version INTEGER DEFAULT 1,
                created TEXT DEFAULT (datetime('now')),
                updated TEXT DEFAULT (datetime('now'))
            )
        """)
        conn.commit()
        conn.close()

    @classmethod
    def tearDownClass(cls):
        if cls._tmpdir:
            shutil.rmtree(cls._tmpdir, ignore_errors=True)

    def test_detect_stale_entries(self):
        old_date = (datetime.now(timezone.utc) - timedelta(days=120)).strftime("%Y-%m-%d %H:%M:%S")
        recent_date = (datetime.now(timezone.utc) - timedelta(days=10)).strftime("%Y-%m-%d %H:%M:%S")

        conn = sqlite3.connect(self._db_path)
        conn.execute("DELETE FROM knowledge_entries")
        conn.execute(
            "INSERT INTO knowledge_entries (id, title, content, status, last_validated, updated) VALUES (?, ?, ?, ?, ?, ?)",
            ("stale-1", "Old Entry", "Old content", "active", old_date, old_date),
        )
        conn.execute(
            "INSERT INTO knowledge_entries (id, title, content, status, last_validated, updated) VALUES (?, ?, ?, ?, ?, ?)",
            ("recent-1", "Recent Entry", "Recent content", "active", recent_date, recent_date),
        )
        conn.execute(
            "INSERT INTO knowledge_entries (id, title, content, status, last_validated, updated) VALUES (?, ?, ?, ?, ?, ?)",
            ("archived-1", "Archived Entry", "Archived content", "archived", old_date, old_date),
        )
        conn.commit()
        conn.close()

        stale = detect_stale_entries(self._db_path, days=90)
        stale_ids = [e["id"] for e in stale]
        self.assertIn("stale-1", stale_ids)
        self.assertNotIn("recent-1", stale_ids)
        self.assertNotIn("archived-1", stale_ids)

    def test_detect_stale_entries_no_db(self):
        stale = detect_stale_entries("/nonexistent/path/knowledge.db")
        self.assertEqual(stale, [])


@_skip_if_no_web_search
class TestDetectNewTechDependencies(unittest.TestCase):
    _tmpdir = None
    _db_path = None
    _project_dir = None

    @classmethod
    def setUpClass(cls):
        cls._tmpdir = tempfile.mkdtemp(prefix="kb_test_newtech_")
        project_dir = Path(cls._tmpdir) / "project"
        project_dir.mkdir(parents=True, exist_ok=True)
        cls._project_dir = str(project_dir)

        pkg = {
            "name": "test-new-tech",
            "dependencies": {
                "react": "^18.2.0",
                "next": "^14.0.0",
            },
        }
        (project_dir / "package.json").write_text(json.dumps(pkg, indent=2), encoding="utf-8")

        db_dir = Path(cls._tmpdir) / "db"
        db_dir.mkdir(parents=True, exist_ok=True)
        cls._db_path = str(db_dir / "knowledge.db")

        conn = sqlite3.connect(cls._db_path)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS knowledge_entries (
                id TEXT PRIMARY KEY,
                title TEXT,
                content TEXT,
                scope TEXT DEFAULT 'workspace',
                tags TEXT DEFAULT '[]',
                confidence REAL DEFAULT 0.6,
                source_path TEXT,
                source_rating INTEGER DEFAULT 3,
                content_hash TEXT,
                type TEXT DEFAULT 'unknown',
                category TEXT DEFAULT 'uncategorized',
                summary TEXT,
                content_path TEXT,
                status TEXT DEFAULT 'active',
                last_validated TEXT,
                success_count INTEGER DEFAULT 0,
                failure_count INTEGER DEFAULT 0,
                occurrences INTEGER DEFAULT 1,
                embedding_status TEXT DEFAULT 'pending',
                embedding_retry_count INTEGER DEFAULT 0,
                version INTEGER DEFAULT 1,
                created TEXT DEFAULT (datetime('now')),
                updated TEXT DEFAULT (datetime('now'))
            )
        """)
        conn.execute(
            "INSERT INTO knowledge_entries (id, title, content, category, tags) VALUES (?, ?, ?, ?, ?)",
            ("known-1", "React Guide", "React content", "react", json.dumps(["react"])),
        )
        conn.commit()
        conn.close()

    @classmethod
    def tearDownClass(cls):
        if cls._tmpdir:
            shutil.rmtree(cls._tmpdir, ignore_errors=True)

    def test_detect_new_tech_dependencies(self):
        missing = detect_new_tech_dependencies(self._project_dir, self._db_path)
        self.assertIsInstance(missing, list)
        missing_names = [t["name"] for t in missing]
        self.assertIn("nextjs", missing_names)
        self.assertNotIn("react", missing_names)


@_skip_if_no_web_search
class TestAutoIngestTechKnowledge(unittest.TestCase):
    @patch("knowledge_server.web_search.search_official_docs")
    @patch("knowledge_server.web_search._fetch_url")
    def test_auto_ingest_tech_knowledge(self, mock_fetch, mock_search):
        mock_search.return_value = [
            {
                "title": "Next.js Documentation",
                "url": "https://nextjs.org/docs/getting-started",
                "content": "Next.js is a React framework for production",
                "source_name": "Next.js Official",
                "source_rating": 5,
                "tech": "nextjs",
            }
        ]

        result = auto_ingest_tech_knowledge("nextjs", tech_version="14.0.0")
        self.assertEqual(result["status"], "ready_for_review")
        self.assertEqual(result["tech_name"], "nextjs")
        self.assertEqual(result["tech_version"], "14.0.0")
        self.assertIn("entry_data", result)
        self.assertGreater(result["sources_found"], 0)
        self.assertEqual(result["best_source_rating"], 5)

    @patch("knowledge_server.web_search.search_official_docs")
    @patch("knowledge_server.web_search._fetch_url")
    def test_auto_ingest_no_results(self, mock_fetch, mock_search):
        mock_search.return_value = []
        mock_fetch.return_value = None

        result = auto_ingest_tech_knowledge("obscure-tech-xyz")
        self.assertEqual(result["status"], "no_results")
        self.assertIn("tech_name", result)


if __name__ == "__main__":
    unittest.main()
