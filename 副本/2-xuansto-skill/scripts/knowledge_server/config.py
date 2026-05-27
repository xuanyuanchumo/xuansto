import json
import logging
import logging.handlers
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

try:
    import yaml
    yaml_available = True
except ImportError:
    yaml_available = False

try:
    import chromadb
    from chromadb.config import Settings as ChromaSettings
    chroma_available = True
except ImportError:
    chroma_available = False

try:
    import openai as _openai_module
    openai_available = True
except ImportError:
    openai_available = False

try:
    from sentence_transformers import SentenceTransformer as _STModel
    sentence_transformers_available = True
except ImportError:
    sentence_transformers_available = False

try:
    from fastapi import FastAPI, HTTPException, Request, WebSocket, WebSocketDisconnect
    from fastapi.responses import JSONResponse
    from pydantic import BaseModel, Field, field_validator
    import uvicorn
    fastapi_available = True
except ImportError:
    fastapi_available = False

try:
    from mcp.server import Server
    from mcp.server.stdio import stdio_server
    from mcp.types import Tool, TextContent
    mcp_available = True
except ImportError:
    mcp_available = False

logger = logging.getLogger("knowledge-server")

KB_VERSION = "2.0.0"
DEDUP_SIMILARITY_THRESHOLD = 0.92

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS schema_version (
    version INTEGER PRIMARY KEY,
    applied_at TEXT DEFAULT (datetime('now')),
    description TEXT
);

CREATE TABLE IF NOT EXISTS knowledge_entries (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    scope TEXT NOT NULL CHECK(scope IN ('general','workspace','experience')),
    tags TEXT DEFAULT '[]',
    confidence REAL DEFAULT 0.6 CHECK(confidence BETWEEN 0 AND 1),
    source_path TEXT,
    source_rating INTEGER DEFAULT 3 CHECK(source_rating BETWEEN 1 AND 5),
    occurrences INTEGER DEFAULT 1,
    content_hash TEXT,
    type TEXT NOT NULL DEFAULT 'unknown',
    category TEXT NOT NULL DEFAULT 'uncategorized',
    summary TEXT,
    content_path TEXT,
    source TEXT,
    last_validated TEXT,
    success_count INTEGER DEFAULT 0,
    failure_count INTEGER DEFAULT 0,
    version INTEGER DEFAULT 1,
    embedding_status TEXT DEFAULT 'pending' CHECK(embedding_status IN ('pending','ready')),
    embedding_retry_count INTEGER DEFAULT 0,
    status TEXT DEFAULT 'active' CHECK(status IN ('active','archived','deleted')),
    last_accessed TEXT,
    created TEXT DEFAULT (datetime('now')),
    updated TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS knowledge_tags (
    entry_id TEXT NOT NULL,
    tag TEXT NOT NULL,
    PRIMARY KEY (entry_id, tag),
    FOREIGN KEY (entry_id) REFERENCES knowledge_entries(id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_tags_tag ON knowledge_tags(tag);

CREATE TABLE IF NOT EXISTS dedup_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    new_entry_id TEXT NOT NULL,
    existing_entry_id TEXT NOT NULL,
    similarity_score REAL NOT NULL,
    action TEXT NOT NULL CHECK(action IN ('skip', 'merge', 'keep_both')),
    merged_at TEXT,
    FOREIGN KEY (new_entry_id) REFERENCES knowledge_entries(id),
    FOREIGN KEY (existing_entry_id) REFERENCES knowledge_entries(id)
);
CREATE INDEX IF NOT EXISTS idx_dedup_new ON dedup_log(new_entry_id);

CREATE VIRTUAL TABLE IF NOT EXISTS knowledge_fts USING fts5(
    id UNINDEXED,
    summary,
    type,
    category,
    content='knowledge_entries',
    content_rowid='rowid',
    tokenize='unicode61'
);

CREATE TRIGGER IF NOT EXISTS knowledge_entries_ai AFTER INSERT ON knowledge_entries BEGIN
    INSERT INTO knowledge_fts(rowid, id, summary, type, category)
    VALUES (new.rowid, new.id, new.summary, new.type, new.category);
END;

CREATE TRIGGER IF NOT EXISTS knowledge_entries_ad AFTER DELETE ON knowledge_entries BEGIN
    INSERT INTO knowledge_fts(knowledge_fts, rowid, id, summary, type, category)
    VALUES ('delete', old.rowid, old.id, old.summary, old.type, old.category);
END;

CREATE TRIGGER IF NOT EXISTS knowledge_entries_au AFTER UPDATE ON knowledge_entries BEGIN
    INSERT INTO knowledge_fts(knowledge_fts, rowid, id, summary, type, category)
    VALUES ('delete', old.rowid, old.id, old.summary, old.type, old.category);
    INSERT INTO knowledge_fts(rowid, id, summary, type, category)
    VALUES (new.rowid, new.id, new.summary, new.type, new.category);
END;

CREATE INDEX IF NOT EXISTS idx_entries_scope ON knowledge_entries(scope);
CREATE INDEX IF NOT EXISTS idx_entries_hash ON knowledge_entries(content_hash);
CREATE INDEX IF NOT EXISTS idx_entries_confidence ON knowledge_entries(confidence);
CREATE INDEX IF NOT EXISTS idx_entries_type ON knowledge_entries(type);
CREATE INDEX IF NOT EXISTS idx_entries_category ON knowledge_entries(category);
CREATE INDEX IF NOT EXISTS idx_entries_created ON knowledge_entries(created);
CREATE INDEX IF NOT EXISTS idx_entries_updated ON knowledge_entries(updated);
CREATE INDEX IF NOT EXISTS idx_entries_status ON knowledge_entries(status);
CREATE INDEX IF NOT EXISTS idx_entries_last_accessed ON knowledge_entries(last_accessed);

CREATE TABLE IF NOT EXISTS version_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    entry_id TEXT NOT NULL,
    version INTEGER NOT NULL,
    title TEXT,
    content TEXT,
    scope TEXT,
    tags TEXT,
    confidence REAL,
    source_path TEXT,
    source_rating INTEGER,
    content_hash TEXT,
    change_type TEXT DEFAULT 'update',
    content_snapshot TEXT,
    saved_at TEXT DEFAULT (datetime('now')),
    UNIQUE(entry_id, version)
);

CREATE INDEX IF NOT EXISTS idx_version_entry ON version_history(entry_id, version);

CREATE TABLE IF NOT EXISTS reconciliation_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    check_time TEXT NOT NULL,
    sqlite_ready_count INTEGER,
    chroma_vector_count INTEGER,
    missing_in_chroma INTEGER DEFAULT 0,
    orphan_in_chroma INTEGER DEFAULT 0,
    fixed_count INTEGER DEFAULT 0,
    details TEXT
);

CREATE TABLE IF NOT EXISTS usage_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    entry_id TEXT,
    agent_role TEXT,
    query_text TEXT,
    result_count INTEGER DEFAULT 0,
    elapsed_ms REAL DEFAULT 0.0,
    timestamp TEXT DEFAULT (datetime('now')),
    FOREIGN KEY (entry_id) REFERENCES knowledge_entries(id) ON DELETE SET NULL
);
CREATE INDEX IF NOT EXISTS idx_usage_entry ON usage_logs(entry_id);
CREATE INDEX IF NOT EXISTS idx_usage_agent ON usage_logs(agent_role);
CREATE INDEX IF NOT EXISTS idx_usage_timestamp ON usage_logs(timestamp);

CREATE TABLE IF NOT EXISTS backup_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    backup_type TEXT NOT NULL,
    destination TEXT,
    entry_count INTEGER DEFAULT 0,
    size_bytes INTEGER DEFAULT 0,
    status TEXT DEFAULT 'completed',
    created_at TEXT DEFAULT (datetime('now'))
);
"""

SCHEMA_VERSION = 12

AGENT_RETRIEVAL_PROFILES = {
    "code_reviewer": {
        "filters": {"type": ["standard", "pattern", "error-solution"]},
        "min_confidence": 0.7,
        "priority_layers": ["workspace", "general", "experience"]
    },
    "backend_developer": {
        "filters": {"type": ["pattern", "error-solution", "glossary"], "category": ["database"]},
        "min_confidence": 0.6,
        "priority_layers": ["workspace", "experience", "general"]
    },
    "security_auditor": {
        "filters": {"type": ["standard", "error-solution"], "category": ["security"]},
        "min_confidence": 0.8,
        "priority_layers": ["general", "experience", "workspace"]
    },
    "test_architect": {
        "filters": {"type": ["standard", "pattern"], "category": ["testing"]},
        "min_confidence": 0.7,
        "priority_layers": ["workspace", "general"]
    },
    "desktop_developer": {
        "filters": {"type": ["standard", "pattern", "error-solution"], "category": ["desktop", "electron", "tauri"]},
        "min_confidence": 0.6,
        "priority_layers": ["general", "experience", "workspace"]
    },
}


def make_response(status: str, data: Any = None, meta: dict = None) -> dict:
    return {
        "status": status,
        "data": data,
        "meta": meta or {}
    }


def make_error_response(code: str, message: str, details: dict = None, retryable: bool = False) -> dict:
    return {
        "status": "error",
        "data": None,
        "meta": {
            "error": {
                "code": code,
                "message": message,
                "details": details or {},
                "retryable": retryable
            }
        }
    }


class JsonFormatter(logging.Formatter):
    def format(self, record):
        return json.dumps({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "module": record.name,
            "message": record.getMessage()
        })


class DesensitizingFilter(logging.Filter):
    _content_patterns = [
        re.compile(r'(content["\s:=]+)["\']?[\s\S]{50,}["\']?', re.IGNORECASE),
    ]

    def filter(self, record):
        if hasattr(record, 'entry_content') and record.entry_content:
            record.entry_content = '[REDACTED]'
        if isinstance(record.msg, str):
            for pattern in self._content_patterns:
                record.msg = pattern.sub(r'\1[REDACTED]', record.msg)
        return True


class KnowledgeConfig:
    def __init__(self, knowledge_root: Path, config_path: Optional[Path] = None):
        self.knowledge_root = knowledge_root
        self._raw = {}
        self._platform_raw = {}

        default_config_path = knowledge_root / "config.yaml"
        effective_config = config_path or default_config_path
        if effective_config.exists():
            with open(effective_config, "r", encoding="utf-8") as f:
                if yaml_available:
                    self._raw = yaml.safe_load(f) or {}
                else:
                    import json as _json
                    try:
                        self._raw = _json.load(f)
                    except Exception:
                        self._raw = {}

        platform_config_path = knowledge_root / "platform-config.yaml"
        if platform_config_path.exists():
            with open(platform_config_path, "r", encoding="utf-8") as f:
                if yaml_available:
                    self._platform_raw = yaml.safe_load(f) or {}
                else:
                    self._platform_raw = {}

        kb = self._raw.get("knowledge_base", {})
        self.server = self._merge_server(kb.get("server", {}))
        self.database = kb.get("database", {})
        self.embedding = kb.get("embedding", {})
        self.retrieval = kb.get("retrieval", {})
        self.dedup = kb.get("dedup", {})
        self.sync = kb.get("sync", {})
        self.lifecycle = kb.get("lifecycle", {})
        self.active_learning = kb.get("active_learning", {})

    def _merge_server(self, server_cfg: dict) -> dict:
        result = {
            "host": os.environ.get("KB_HOST", server_cfg.get("host", "127.0.0.1")),
            "port": int(os.environ.get("KB_PORT", server_cfg.get("port", 8765))),
            "transport": server_cfg.get("transport", "stdio"),
            "log_level": os.environ.get("KB_LOG_LEVEL", server_cfg.get("log_level", "INFO")),
            "cors_origins": server_cfg.get("cors_origins", []),
        }
        return result

    @property
    def sqlite_path(self) -> Path:
        p = self.database.get("sqlite_path", ".knowledge/index/knowledge.db")
        resolved = Path(p) if Path(p).is_absolute() else self.knowledge_root / p
        return resolved

    @property
    def chroma_path(self) -> Path:
        p = self.database.get("chroma_path", ".knowledge/index/chroma_db")
        resolved = Path(p) if Path(p).is_absolute() else self.knowledge_root / p
        return resolved

    @property
    def semantic_weight(self) -> float:
        return float(self.retrieval.get("semantic_weight", 0.7))

    @property
    def keyword_weight(self) -> float:
        return float(self.retrieval.get("keyword_weight", 0.3))

    @property
    def top_k(self) -> int:
        return int(self.retrieval.get("top_k", 5))

    @property
    def default_strategy(self) -> str:
        return self.retrieval.get("default_strategy", "hybrid")

    @property
    def dedup_threshold(self) -> float:
        return float(self.dedup.get("similarity_threshold", DEDUP_SIMILARITY_THRESHOLD))

    @property
    def dedup_action(self) -> str:
        return self.dedup.get("action", "merge")

    @property
    def embedding_model(self) -> str:
        return self.embedding.get("primary", "text-embedding-3-small")

    @property
    def embedding_fallback(self) -> str:
        return self.embedding.get("fallback", "sentence-transformers/all-MiniLM-L6-v2")

    @property
    def embedding_dimension(self) -> int:
        return int(self.embedding.get("dimension", 1536))


def setup_logging(log_level: str = "INFO"):
    level = getattr(logging, log_level.upper(), logging.INFO)
    json_formatter = JsonFormatter()
    desensitizing_filter = DesensitizingFilter()

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(json_formatter)
    console_handler.addFilter(desensitizing_filter)

    log_dir = Path(__file__).resolve().parent.parent.parent / ".knowledge" / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / "knowledge-server.log"

    file_handler = logging.handlers.RotatingFileHandler(
        str(log_file),
        maxBytes=10 * 1024 * 1024,
        backupCount=5,
        encoding="utf-8",
    )
    file_handler.setFormatter(json_formatter)
    file_handler.addFilter(desensitizing_filter)

    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    root_logger.handlers = [console_handler, file_handler]
