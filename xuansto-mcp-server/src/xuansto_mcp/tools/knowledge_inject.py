from __future__ import annotations

import asyncio
import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from mcp.server.fastmcp import FastMCP
from mcp.types import ToolAnnotations

from ..core import atomic_write
from ..core.config import (
    KNOWLEDGE_CHROMA_PATH,
    KNOWLEDGE_DB_PATH,
    KNOWLEDGE_EXPERIENCE_DIR,
    KNOWLEDGE_GENERAL_DIR,
    KNOWLEDGE_WORKSPACE_DIR,
)
from ..core.database import persist_state
from ..core.errors import ERR_VALIDATION, make_error_response, make_success_response
from ..core.logging_config import get_logger
from ..core.search_engine import get_search_engine
from ..core.validator import validate_input
from ..models.schemas import KnowledgeInjectInput

logger = get_logger("knowledge_inject")

_injected_topics: set[str] = set()

_MAX_FILE_BYTES = 1 * 1024 * 1024

_SCOPE_DIR_MAP: dict[str, Path] = {
    "general": KNOWLEDGE_GENERAL_DIR,
    "workspace": KNOWLEDGE_WORKSPACE_DIR,
    "experience": KNOWLEDGE_EXPERIENCE_DIR,
}


def _estimate_tokens(text: str) -> int:
    return max(1, len(text) // 4)


def _scan_knowledge_dir(directory: Path) -> list[dict[str, Any]]:
    if not directory.exists():
        return []
    entries: list[dict[str, Any]] = []
    for f in directory.rglob("*.md"):
        try:
            if f.stat().st_size > _MAX_FILE_BYTES:
                continue
            content = f.read_text(encoding="utf-8")
            entries.append({
                "name": f.stem,
                "path": str(f.relative_to(directory)),
                "size_bytes": f.stat().st_size,
                "estimated_tokens": _estimate_tokens(content),
                "modified": datetime.fromtimestamp(f.stat().st_mtime, tz=timezone.utc).isoformat(),
            })
        except (OSError, UnicodeDecodeError):
            continue
    return entries


def _action_inject(
    topics: list[str],
    scope: str,
    max_tokens: int,
    relevance_threshold: float,
) -> dict[str, Any]:
    global _injected_topics

    target_dir = _SCOPE_DIR_MAP.get(scope, KNOWLEDGE_GENERAL_DIR)
    target_dir.mkdir(parents=True, exist_ok=True)

    injected_entries: list[dict[str, Any]] = []
    total_tokens = 0

    for topic in topics:
        if topic in _injected_topics:
            logger.info("Topic '%s' already injected in this session, skipping", topic)
            continue

        engine = get_search_engine("chromadb")
        results = engine.search(
            topic,
            top_k=10,
            filters={"scope": scope, "min_confidence": relevance_threshold},
        )

        if not results:
            engine = get_search_engine("sqlite_fts5")
            results = engine.search(
                topic,
                top_k=10,
                filters={"scope": scope, "min_confidence": relevance_threshold},
            )

        if not results:
            engine = get_search_engine("simple")
            results = engine.search(
                topic,
                top_k=10,
                filters={"scope": scope},
            )

        for r in results:
            if r.relevance < relevance_threshold:
                continue
            entry_tokens = _estimate_tokens(r.content)
            if total_tokens + entry_tokens > max_tokens:
                break
            injected_entries.append({
                "source": r.source,
                "content": r.content,
                "match_type": r.match_type,
                "relevance": r.relevance,
                "estimated_tokens": entry_tokens,
            })
            total_tokens += entry_tokens

        _injected_topics.add(topic)

    return {
        "injected_count": len(injected_entries),
        "total_estimated_tokens": total_tokens,
        "scope": scope,
        "topics_requested": len(topics),
        "topics_already_in_session": len(topics) - len([t for t in topics if t not in _injected_topics]),
        "entries": injected_entries,
    }


def _action_list_available(scope: str | None) -> dict[str, Any]:
    scopes_to_scan: list[tuple[str, Path]] = []
    if scope is None:
        scopes_to_scan = list(_SCOPE_DIR_MAP.items())
    else:
        target = _SCOPE_DIR_MAP.get(scope)
        if target:
            scopes_to_scan = [(scope, target)]

    all_entries: dict[str, list[dict[str, Any]]] = {}
    total_entries = 0
    total_tokens = 0

    for scope_name, directory in scopes_to_scan:
        entries = _scan_knowledge_dir(directory)
        all_entries[scope_name] = entries
        total_entries += len(entries)
        total_tokens += sum(e["estimated_tokens"] for e in entries)

    return {
        "scopes": all_entries,
        "total_entries": total_entries,
        "total_estimated_tokens": total_tokens,
    }


def _action_precipitate(
    category: str,
    title: str,
    content: str,
    tags: list[str] | None,
    confidence: float,
) -> dict[str, Any]:
    KNOWLEDGE_EXPERIENCE_DIR.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    safe_title = "".join(c if c.isalnum() or c in "-_" else "_" for c in title[:50])
    filename = f"precipitated-{safe_title}-{timestamp}.md"
    filepath = KNOWLEDGE_EXPERIENCE_DIR / filename

    tags_str = json.dumps(tags or [], ensure_ascii=False)
    frontmatter = (
        f"---\n"
        f"type: precipitated\n"
        f"category: {category}\n"
        f"title: {title}\n"
        f"confidence: {confidence}\n"
        f"tags: {tags_str}\n"
        f"precipitated_at: {timestamp}\n"
        f"---\n"
        f"{content}\n"
    )
    atomic_write(filepath, frontmatter)

    return {
        "precipitated_id": filename,
        "path": str(filepath),
        "category": category,
        "title": title,
        "confidence": confidence,
        "tags": tags or [],
        "estimated_tokens": _estimate_tokens(content),
    }


def _action_add(
    title: str,
    content: str,
    scope: str,
    tags: list[str] | None,
) -> dict[str, Any]:
    target_dir = _SCOPE_DIR_MAP.get(scope, KNOWLEDGE_GENERAL_DIR)
    target_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    safe_title = "".join(c if c.isalnum() or c in "-_" else "_" for c in title[:50])
    filename = f"added-{safe_title}-{timestamp}.md"
    filepath = target_dir / filename

    tags_str = json.dumps(tags or [], ensure_ascii=False)
    frontmatter = (
        f"---\n"
        f"type: added\n"
        f"title: {title}\n"
        f"scope: {scope}\n"
        f"tags: {tags_str}\n"
        f"added_at: {timestamp}\n"
        f"---\n"
        f"{content}\n"
    )
    atomic_write(filepath, frontmatter)

    indexed = False
    chroma_indexed = False
    try:
        if KNOWLEDGE_DB_PATH.exists():
            conn = sqlite3.connect(str(KNOWLEDGE_DB_PATH))
            try:
                now = datetime.now(timezone.utc).isoformat()
                conn.execute(
                    "INSERT INTO knowledge_entries (id, title, content, type, metadata_json, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (filename, title, content, scope, json.dumps({"tags": tags or [], "source": "mcp_add"}), now, now),
                )
                conn.commit()
                indexed = True
            except Exception as exc:
                logger.warning("Failed to index added knowledge in SQLite: %s", exc)
            finally:
                conn.close()
    except Exception as exc:
        logger.warning("Failed to index added knowledge: %s", exc)

    if indexed:
        try:
            import chromadb
            client = chromadb.PersistentClient(path=str(KNOWLEDGE_CHROMA_PATH))
            collection = client.get_or_create_collection("knowledge")
            collection.upsert(
                ids=[filename],
                documents=[content],
                metadatas=[{"title": title, "type": scope, "source": "mcp_add"}],
            )
            chroma_indexed = True
        except ImportError:
            logger.warning("ChromaDB not available, skipping vector index for added knowledge")
            try:
                persist_state("knowledge_entries", {
                    "id": filename,
                    "title": title,
                    "content": content,
                    "scope": scope,
                    "tags_json": tags or [],
                    "sync_status": "pending",
                })
            except Exception:
                logger.debug("Failed to mark knowledge entry %s as pending in main DB", filename)
        except Exception as exc:
            logger.warning("Failed to index added knowledge in ChromaDB: %s", exc)
            try:
                persist_state("knowledge_entries", {
                    "id": filename,
                    "title": title,
                    "content": content,
                    "scope": scope,
                    "tags_json": tags or [],
                    "sync_status": "pending",
                })
            except Exception:
                logger.debug("Failed to mark knowledge entry %s as pending in main DB", filename)

    return {
        "added_id": filename,
        "path": str(filepath),
        "title": title,
        "scope": scope,
        "tags": tags or [],
        "indexed": indexed,
        "chroma_indexed": chroma_indexed,
        "estimated_tokens": _estimate_tokens(content),
    }


def _action_update(
    entry_id: str,
    title: str | None,
    content: str | None,
    tags: list[str] | None,
) -> dict[str, Any]:
    updated_fields: list[str] = []

    if KNOWLEDGE_DB_PATH.exists():
        try:
            conn = sqlite3.connect(str(KNOWLEDGE_DB_PATH))
            try:
                cursor = conn.cursor()
                cursor.execute("SELECT id FROM knowledge_entries WHERE id = ?", (entry_id,))
                if cursor.fetchone() is None:
                    conn.close()
                    return {"entry_id": entry_id, "updated": False, "reason": "entry not found"}
                now = datetime.now(timezone.utc).isoformat()
                if title is not None:
                    conn.execute("UPDATE knowledge_entries SET title = ?, updated_at = ? WHERE id = ?", (title, now, entry_id))
                    updated_fields.append("title")
                if content is not None:
                    conn.execute("UPDATE knowledge_entries SET content = ?, updated_at = ? WHERE id = ?", (content, now, entry_id))
                    updated_fields.append("content")
                if tags is not None:
                    metadata_json = json.dumps({"tags": tags}, ensure_ascii=False)
                    conn.execute("UPDATE knowledge_entries SET metadata_json = ?, updated_at = ? WHERE id = ?", (metadata_json, now, entry_id))
                    updated_fields.append("tags")
                if not updated_fields:
                    conn.execute("UPDATE knowledge_entries SET updated_at = ? WHERE id = ?", (now, entry_id))
                conn.commit()
            finally:
                conn.close()
        except Exception as exc:
            logger.warning("Failed to update knowledge entry in SQLite: %s", exc)
            return {"entry_id": entry_id, "updated": False, "reason": str(exc)}
    else:
        return {"entry_id": entry_id, "updated": False, "reason": "database not found"}

    chroma_updated = False
    if content is not None:
        try:
            import chromadb
            client = chromadb.PersistentClient(path=str(KNOWLEDGE_CHROMA_PATH))
            collection = client.get_or_create_collection("knowledge")
            meta = {"title": title or entry_id, "source": "mcp_update"}
            if tags is not None:
                meta["tags"] = json.dumps(tags)
            collection.upsert(
                ids=[entry_id],
                documents=[content],
                metadatas=[meta],
            )
            chroma_updated = True
        except ImportError:
            logger.warning("ChromaDB not available, skipping vector index update")
            try:
                persist_state("knowledge_entries", {
                    "id": entry_id,
                    "sync_status": "pending",
                })
            except Exception:
                logger.debug("Failed to mark knowledge entry %s as pending in main DB", entry_id)
        except Exception as exc:
            logger.warning("Failed to update knowledge entry in ChromaDB: %s", exc)
            try:
                persist_state("knowledge_entries", {
                    "id": entry_id,
                    "sync_status": "pending",
                })
            except Exception:
                logger.debug("Failed to mark knowledge entry %s as pending in main DB", entry_id)

    return {
        "entry_id": entry_id,
        "updated": True,
        "updated_fields": updated_fields,
        "chroma_updated": chroma_updated,
    }


def register(mcp: FastMCP) -> None:
    @mcp.tool(
        annotations=ToolAnnotations(
            readOnlyHint=False,
            destructiveHint=False,
            idempotentHint=False,
            openWorldHint=True,
        )
    )
    async def knowledge_inject(
        action: str,
        topics: list[str] | None = None,
        scope: str = "general",
        max_tokens: int = 5000,
        relevance_threshold: float = 0.5,
        category: str | None = None,
        title: str | None = None,
        content: str | None = None,
        tags: list[str] | None = None,
        confidence: float = 0.8,
        entry_id: str | None = None,
    ) -> dict[str, Any]:
        """知识注入引擎：将相关知识注入到当前Agent上下文中，支持按主题检索注入、列出可用知识、经验沉淀保存、直接添加知识条目、以及更新已有条目。"""
        validated, err = validate_input(
            KnowledgeInjectInput,
            action=action,
            topics=topics,
            scope=scope,
            max_tokens=max_tokens,
            relevance_threshold=relevance_threshold,
            category=category,
            title=title,
            content=content,
            tags=tags,
            confidence=confidence,
            entry_id=entry_id,
        )
        if err:
            return err
        logger.info("knowledge_inject called: action=%s scope=%s", action, scope)
        try:
            if action == "inject":
                if not topics:
                    return make_error_response(
                        ValueError("inject action requires topics parameter"),
                        error_code=ERR_VALIDATION,
                    )
                result = await asyncio.to_thread(_action_inject, topics, scope, max_tokens, relevance_threshold)
                return make_success_response(data=result)

            if action == "list_available":
                result = await asyncio.to_thread(_action_list_available, scope if scope != "general" else None)
                return make_success_response(data=result)

            if action == "precipitate":
                if not category or not title or not content:
                    return make_error_response(
                        ValueError("precipitate action requires category, title, and content parameters"),
                        error_code=ERR_VALIDATION,
                    )
                result = await asyncio.to_thread(_action_precipitate, category, title, content, tags, confidence)
                return make_success_response(data=result)

            if action == "add":
                if not title or not content:
                    return make_error_response(
                        ValueError("add action requires title and content parameters"),
                        error_code=ERR_VALIDATION,
                    )
                result = await asyncio.to_thread(_action_add, title, content, scope, tags)
                return make_success_response(data=result)

            if action == "update":
                if not entry_id:
                    return make_error_response(
                        ValueError("update action requires entry_id parameter"),
                        error_code=ERR_VALIDATION,
                    )
                result = await asyncio.to_thread(_action_update, entry_id, title, content, tags)
                return make_success_response(data=result)

            return make_error_response(
                ValueError(f"Unknown action: {action}. Supported: inject, list_available, precipitate, add, update"),
                error_code=ERR_VALIDATION,
            )
        except Exception as e:
            logger.error("knowledge_inject error: %s", e)
            return make_error_response(e)
