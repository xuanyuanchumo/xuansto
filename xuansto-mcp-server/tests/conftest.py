from __future__ import annotations

import json
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

SKILL_PATH = Path(__file__).resolve().parent.parent.parent / ".trae" / "skills" / "xuansto-skill"


@pytest.fixture
def tmp_work_dir(tmp_path):
    work = tmp_path / ".xuansto"
    work.mkdir()
    return work


@pytest.fixture
def tmp_knowledge_dir(tmp_path):
    kdir = tmp_path / "knowledge"
    kdir.mkdir()
    (kdir / "general").mkdir()
    (kdir / "workspace").mkdir()
    (kdir / "experience").mkdir()
    idx = kdir / "index"
    idx.mkdir()
    return kdir


@pytest.fixture
def tmp_db_path(tmp_knowledge_dir):
    return tmp_knowledge_dir / "index" / "knowledge.db"


@pytest.fixture
def tmp_chroma_path(tmp_knowledge_dir):
    return tmp_knowledge_dir / "index" / "chroma_db"


@pytest.fixture
def mock_config_paths(tmp_work_dir, tmp_knowledge_dir, tmp_db_path, tmp_chroma_path):
    data_dir = tmp_knowledge_dir.parent
    patches = {
        "WORK_DIR": tmp_work_dir,
        "DATA_DIR": data_dir,
        "KNOWLEDGE_DB_PATH": tmp_db_path,
        "KNOWLEDGE_CHROMA_PATH": tmp_chroma_path,
        "KNOWLEDGE_GENERAL_DIR": tmp_knowledge_dir / "general",
        "KNOWLEDGE_WORKSPACE_DIR": tmp_knowledge_dir / "workspace",
        "KNOWLEDGE_EXPERIENCE_DIR": tmp_knowledge_dir / "experience",
        "REFERENCES_DIR": data_dir / "references",
        "AGENTS_DIR": data_dir / "agents",
        "SCRIPTS_DIR": data_dir / "scripts",
        "HOOKS_PATH": data_dir / "hooks" / "hooks.json",
    }
    return patches


@pytest.fixture
def patch_config(mock_config_paths):
    import xuansto_mcp.core.config as cfg_mod

    originals = {}
    for key, val in mock_config_paths.items():
        originals[key] = getattr(cfg_mod, key, None)
        setattr(cfg_mod, key, val)
    yield cfg_mod
    for key, val in originals.items():
        if val is not None:
            setattr(cfg_mod, key, val)
        elif hasattr(cfg_mod, key):
            delattr(cfg_mod, key)


@pytest.fixture
def fresh_degradation_manager():
    from xuansto_mcp.core.degradation import DegradationManager
    mgr = DegradationManager(health_interval=9999)
    return mgr


@pytest.fixture
def fresh_hook_engine():
    from xuansto_mcp.core.hook_engine import HookEngine
    return HookEngine()


@pytest.fixture
def sqlite_fts_db(tmp_db_path):
    import sqlite3
    conn = sqlite3.connect(str(tmp_db_path))
    conn.execute(
        "CREATE TABLE IF NOT EXISTS knowledge_entries "
        "(id TEXT PRIMARY KEY, title TEXT, content TEXT)"
    )
    try:
        conn.execute(
            "CREATE VIRTUAL TABLE IF NOT EXISTS knowledge_fts "
            "USING fts5(id, title, content)"
        )
    except sqlite3.OperationalError:
        pass
    conn.executemany(
        "INSERT OR IGNORE INTO knowledge_entries (id, title, content) VALUES (?, ?, ?)",
        [
            ("doc1", "Python Testing", "pytest is a great testing framework for Python"),
            ("doc2", "FastAPI Guide", "FastAPI is a modern web framework for building APIs"),
            ("doc3", "MCP Protocol", "Model Context Protocol enables LLM tool integration"),
        ],
    )
    try:
        conn.executemany(
            "INSERT OR IGNORE INTO knowledge_fts (id, title, content) VALUES (?, ?, ?)",
            [
                ("doc1", "Python Testing", "pytest is a great testing framework for Python"),
                ("doc2", "FastAPI Guide", "FastAPI is a modern web framework for building APIs"),
                ("doc3", "MCP Protocol", "Model Context Protocol enables LLM tool integration"),
            ],
        )
    except sqlite3.OperationalError:
        pass
    conn.commit()
    conn.close()
    return tmp_db_path
