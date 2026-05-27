import asyncio
import logging
import sys
import threading
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from .config import (
    KnowledgeConfig, KB_VERSION, fastapi_available, mcp_available,
    chroma_available, make_response, make_error_response,
)
from .db_engine import SQLiteEngine
from .embedding import EmbeddingManager
from .vector_engine import ChromaEngine
from .hybrid_search import HybridRetrievalEngine
from .progressive_search import ProgressiveSearcher
from .dedup import DedupEngine
from .auth import ApiKeyAuth
from .security import InputValidator, SensitiveContentFilter, RateLimiter
from .websocket_manager import WebSocketManager
from .degradation import DegradationManager
from .backup import BackupManager
from .importer import FirstRunImporter
from .exporter import KnowledgeExporter
from .lifecycle import LifecycleManager
from .sync import IncrementalSync
from .api import create_app
from .mcp_server import register_mcp_tools
from .tech_stack_detector import detect_tech_stack
from .context_formatter import format_knowledge_context

logger = logging.getLogger("knowledge-server")


class KnowledgeServer:
    def __init__(self, knowledge_root: Path, config_path: Optional[Path] = None):
        self.knowledge_root = knowledge_root
        self.config = KnowledgeConfig(knowledge_root, config_path)
        self.sqlite = SQLiteEngine(self.config.sqlite_path)
        self.embedding_manager = EmbeddingManager(self.config)
        self.chroma = ChromaEngine(self.config.chroma_path, embedding_manager=self.embedding_manager)
        self.retrieval = HybridRetrievalEngine(self.sqlite, self.chroma, self.config)
        self.progressive_searcher = ProgressiveSearcher(
            db_engine=self.sqlite,
            vector_engine=self.chroma,
            retrieval_engine=self.retrieval,
        )
        self.dedup = DedupEngine(self.sqlite, self.chroma, self.config)
        self.importer = FirstRunImporter(self.config, self.sqlite, self.chroma)
        self.exporter = KnowledgeExporter(self.config.knowledge_root, self.sqlite)
        self.lifecycle_mgr = LifecycleManager(
            self.config.knowledge_root,
            self.sqlite,
            exporter=self.exporter,
            lifecycle_config=self.config.lifecycle,
        )
        self.backup_mgr = BackupManager(self.config, self.sqlite)
        self.sync_engine = IncrementalSync(
            knowledge_root,
            self.sqlite,
            self.importer,
            chroma_engine=self.chroma,
            sync_config=self.config.sync,
        )
        self.ws_manager = WebSocketManager()
        self.degradation = DegradationManager(self.chroma, self.config, embedding_manager=self.embedding_manager, sqlite_engine=self.sqlite)
        self.api_key_auth = ApiKeyAuth(knowledge_root)
        self.rate_limiter = RateLimiter()
        self._app = None
        self._mcp_server = None
        self._retry_running = False
        self._shutting_down = False
        self._active_requests = 0
        self._active_requests_lock = asyncio.Lock()
        self._backup_timer_sqlite = None
        self._backup_timer_chroma = None
        self._backup_timer_cleanup = None
        self._sync_timer = None
        self._lifecycle_timer = None
        self._last_change_timestamp = datetime.now(timezone.utc).isoformat()

    def initialize(self):
        self._ensure_backup_dirs()
        if self.importer.should_import():
            logger.info("operation=first_import, status=starting")
            stats = self.importer.run()
            logger.info("operation=first_import, status=completed, stats=%s", stats)
        else:
            if self.config.sync.get("watch_enabled", False) or self.config.sync.get("full_sync_on_startup", False):
                self.run_incremental_sync()
        self._check_dual_engine_consistency()
        self.degradation.start_periodic_check()
        self._start_retry_task()
        self._start_backup_scheduler()
        self._start_lifecycle_scheduler()
        transport = self.config.server.get("transport", "stdio")
        if mcp_available and transport in ("mcp", "stdio", "http+mcp"):
            from mcp.server import Server
            self._mcp_server = Server("xuansto-knowledge")
            register_mcp_tools(self, self._mcp_server)
            logger.info("operation=mcp_server_init, status=ready, transport=%s", transport)

    def _ensure_backup_dirs(self):
        root = self.config.knowledge_root
        for subdir in ("full", "incremental", "snapshot"):
            (root / "backup" / subdir).mkdir(parents=True, exist_ok=True)

    def _start_retry_task(self):
        if self._retry_running:
            return
        self._retry_running = True
        t = threading.Thread(target=self._retry_loop, daemon=True)
        t.start()

    def _stop_retry_task(self):
        self._retry_running = False

    def _start_backup_scheduler(self):
        self._schedule_sqlite_backup()
        self._schedule_chroma_backup()
        self._schedule_cleanup()

    def _stop_backup_scheduler(self):
        for timer in (self._backup_timer_sqlite, self._backup_timer_chroma, self._backup_timer_cleanup):
            if timer is not None:
                timer.cancel()

    def _start_lifecycle_scheduler(self):
        if not self.lifecycle_mgr.archive_enabled:
            return
        self._schedule_lifecycle_check()

    def _schedule_lifecycle_check(self):
        if self._shutting_down:
            return
        interval = self.lifecycle_mgr.archive_check_interval
        self._lifecycle_timer = threading.Timer(interval, self._run_lifecycle_check)
        self._lifecycle_timer.daemon = True
        self._lifecycle_timer.start()

    def _run_lifecycle_check(self):
        self.run_lifecycle_check()
        self._schedule_lifecycle_check()

    def run_lifecycle_check(self) -> dict:
        report = self.lifecycle_mgr.check_and_archive()
        logger.info(
            "operation=run_lifecycle_check, checked=%d, archived=%d, errors=%d",
            report.get("checked", 0), report.get("archived", 0), report.get("errors", 0),
        )
        return report

    def run_incremental_sync(self) -> dict:
        report = self.sync_engine.sync()
        logger.info(
            "operation=run_incremental_sync, added=%d, modified=%d, deleted=%d",
            report["added"], report["modified"], report["deleted"],
        )
        if self.config.sync.get("watch_enabled", False):
            self._schedule_incremental_sync()
        return report

    def _schedule_incremental_sync(self):
        if self._shutting_down:
            return
        interval = self.config.sync.get("delta_sync_interval", 300)
        self._sync_timer = threading.Timer(interval, self._run_scheduled_sync)
        self._sync_timer.daemon = True
        self._sync_timer.start()

    def _run_scheduled_sync(self):
        self.run_incremental_sync()

    def _schedule_sqlite_backup(self):
        if self._shutting_down:
            return
        self._backup_timer_sqlite = threading.Timer(6 * 3600, self._run_sqlite_backup)
        self._backup_timer_sqlite.daemon = True
        self._backup_timer_sqlite.start()

    def _run_sqlite_backup(self):
        self.backup_mgr._scheduled_sqlite_backup()
        self._schedule_sqlite_backup()

    def _schedule_chroma_backup(self):
        if self._shutting_down:
            return
        self._backup_timer_chroma = threading.Timer(86400, self._run_chroma_backup)
        self._backup_timer_chroma.daemon = True
        self._backup_timer_chroma.start()

    def _run_chroma_backup(self):
        self.backup_mgr._scheduled_chroma_backup()
        self._schedule_chroma_backup()

    def _schedule_cleanup(self):
        if self._shutting_down:
            return
        self._backup_timer_cleanup = threading.Timer(86400, self._run_cleanup)
        self._backup_timer_cleanup.daemon = True
        self._backup_timer_cleanup.start()

    def _run_cleanup(self):
        self.backup_mgr._cleanup_old_backups()
        self._schedule_cleanup()

    def _retry_loop(self):
        while self._retry_running:
            time.sleep(60)
            self._retry_pending_embeddings()
            self._re_embed_stale_entries()

    def _retry_pending_embeddings(self):
        pending = self.sqlite.get_pending_embeddings(limit=20)
        if not pending:
            return
        for entry in pending:
            if not self.chroma.available:
                break
            try:
                self.chroma.add_embedding(
                    entry["id"],
                    entry["content"],
                    {"scope": entry.get("scope", "workspace"), "title": entry.get("title", "")},
                )
                self.sqlite.update_embedding_status(entry["id"], "ready")
                logger.info("operation=retry_embedding, entry_id=%s, status=ready", entry["id"])
            except Exception as e:
                self.sqlite.update_embedding_status(entry["id"], "pending")
                self.sqlite.increment_retry_count(entry["id"])
                logger.warning("operation=retry_embedding, entry_id=%s, status=failed, error=%s", entry["id"], e)

    def _check_dual_engine_consistency(self):
        if not self.chroma.available:
            return
        ready_ids = self.sqlite.get_ready_entry_ids()
        chroma_ids = self.chroma.get_all_ids()
        all_sqlite_ids = {e["id"] for e in self.sqlite.get_all_entries()}

        missing_in_chroma = ready_ids - chroma_ids
        orphan_in_chroma = chroma_ids - all_sqlite_ids

        fixed_count = 0
        for entry_id in missing_in_chroma:
            entry = self.sqlite.get_entry(entry_id)
            if entry:
                try:
                    self.chroma.add_embedding(
                        entry_id,
                        entry["content"],
                        {"scope": entry.get("scope", "workspace"), "title": entry.get("title", "")},
                    )
                    fixed_count += 1
                except Exception as e:
                    logger.warning("operation=consistency_fix, entry_id=%s, error=%s", entry_id, e)

        for entry_id in orphan_in_chroma:
            self.chroma.delete_embedding(entry_id)
            fixed_count += 1

        if missing_in_chroma or orphan_in_chroma:
            self.sqlite.log_reconciliation(
                sqlite_ready_count=len(ready_ids),
                chroma_vector_count=len(chroma_ids),
                missing_in_chroma=len(missing_in_chroma),
                orphan_in_chroma=len(orphan_in_chroma),
                fixed_count=fixed_count,
                details=f"missing={len(missing_in_chroma)}, orphan={len(orphan_in_chroma)}",
            )
            logger.info(
                "operation=consistency_check, missing_in_chroma=%d, orphan_in_chroma=%d, fixed=%d",
                len(missing_in_chroma), len(orphan_in_chroma), fixed_count,
            )

    def _re_embed_stale_entries(self):
        if not self.chroma.available:
            return
        if not self.embedding_manager or self.embedding_manager.level != EmbeddingManager.LEVEL_API:
            return
        stale_ids = self.chroma.get_stale_entry_ids(limit=10)
        if not stale_ids:
            return
        for entry_id in stale_ids:
            entry = self.sqlite.get_entry(entry_id)
            if not entry:
                continue
            try:
                self.chroma.add_embedding(
                    entry_id,
                    entry["content"],
                    {"scope": entry.get("scope", "workspace"), "title": entry.get("title", "")},
                )
                self.sqlite.update_embedding_status(entry_id, "ready")
                logger.info("operation=re_embed_stale, entry_id=%s, status=ready", entry_id)
            except Exception as e:
                logger.warning("operation=re_embed_stale, entry_id=%s, error=%s", entry_id, e)

    def _touch_change(self):
        self._last_change_timestamp = datetime.now(timezone.utc).isoformat()

    def get_status_summary(self) -> dict:
        counts = self.sqlite.count_entries()
        embedding_status_counts = self.sqlite.count_by_embedding_status()
        total = counts.get("total", 0)
        scope_distribution = {k: v for k, v in counts.items() if k != "total"}
        tech_stack_coverage = []
        if total > 0:
            all_entries = self.sqlite.get_all_entries()
            tag_set = set()
            for e in all_entries:
                for t in e.get("tags", []):
                    tag_set.add(t.lower())
            tech_stack_coverage = sorted(tag_set)
        if self.chroma.available and self.embedding_manager.level == 0:
            embedding_status = "ready"
        elif self.chroma.available:
            embedding_status = "degraded"
        else:
            embedding_status = "pending"
        return {
            "total_entries": total,
            "scope_distribution": scope_distribution,
            "last_updated": self._last_change_timestamp,
            "tech_stack_coverage": tech_stack_coverage,
            "embedding_status": embedding_status,
        }

    @property
    def app(self):
        if not fastapi_available:
            raise RuntimeError("FastAPI/uvicorn未安装，无法启动HTTP服务")
        if self._app is None:
            self._app = create_app(self)
        return self._app

    def _is_remote_mode(self) -> bool:
        host = self.config.server.get("host", "127.0.0.1")
        return host == "0.0.0.0" or host == "::"

    def auto_retrieve(self, task_type: str, project_path: str, query: Optional[str] = None, token_budget: int = 2048) -> dict:
        tech_stack = detect_tech_stack(project_path)

        search_query = query or task_type
        if not search_query:
            search_query = "general"

        effective_strategy = self.degradation.get_search_strategy()

        type_filters = None
        category_filters = None
        min_confidence = 0.0

        if task_type == "bug_fix":
            type_filters = ["error-solution", "pattern"]
            min_confidence = 0.6
        elif task_type == "security":
            type_filters = ["standard", "error-solution"]
            category_filters = ["security"]
            min_confidence = 0.8
        elif task_type == "review":
            type_filters = ["standard", "pattern"]
            min_confidence = 0.7
        elif task_type == "refactor":
            type_filters = ["pattern", "best-practice"]
            min_confidence = 0.6
        elif task_type == "deploy":
            type_filters = ["standard", "pattern"]
            category_filters = ["devops", "deployment"]
            min_confidence = 0.6
        elif task_type == "feature":
            type_filters = ["pattern", "standard"]
            min_confidence = 0.5

        try:
            search_result = self.retrieval.search(
                query=search_query,
                top_k=10,
                strategy=effective_strategy,
                min_confidence=min_confidence,
                type_filters=type_filters,
                category_filters=category_filters,
            )
            results = search_result.get("results", [])
        except Exception as e:
            logger.warning("operation=auto_retrieve_search_failed, error=%s", e)
            results = []

        context = format_knowledge_context(
            results=results,
            token_budget=token_budget,
            tech_stack=tech_stack,
        )

        return {
            "context": context,
            "tech_stack": tech_stack,
            "task_type": task_type,
            "query_used": search_query,
            "results_count": len(results),
            "degradation_level": self.degradation.level,
            "degradation_name": self.degradation.level_name,
        }

    def mcp_knowledge_search(self, query: str, scope: Optional[str] = None, top_k: int = 5, strategy: str = "hybrid", agent_role: Optional[str] = None, type_filters: Optional[list[str]] = None, category_filters: Optional[list[str]] = None) -> dict:
        effective_strategy = self.degradation.get_search_strategy()
        if strategy != "keyword_only" and effective_strategy != "hybrid":
            strategy = effective_strategy
        result = self.retrieval.search(query=query, scope=scope, top_k=top_k, strategy=strategy, agent_role=agent_role, type_filters=type_filters, category_filters=category_filters)
        result["degradation_level"] = self.degradation.level
        result["degradation_name"] = self.degradation.level_name
        if agent_role:
            result["agent_role"] = agent_role
        return make_response("ok", result)

    def mcp_knowledge_progressive_search(self, query: str, task_type: str = "feature", tech_stack: Optional[dict] = None, token_budget: int = 2048) -> dict:
        result = self.progressive_searcher.search(
            query=query,
            task_type=task_type,
            tech_stack=tech_stack or {},
            token_budget=token_budget,
        )
        result["degradation_level"] = self.degradation.level
        result["degradation_name"] = self.degradation.level_name
        return make_response("ok", result)

    def mcp_knowledge_deep_load(self, entry_id: str) -> dict:
        result = self.progressive_searcher.deep_load(entry_id)
        if "error" in result:
            return make_error_response(
                code="NOT_FOUND",
                message="知识条目不存在",
                details={"entry_id": entry_id},
            )
        return make_response("ok", result)

    def mcp_knowledge_add(self, title: str, content: str, scope: str = "workspace", tags: Optional[list[str]] = None, source_rating: int = 3) -> dict:
        has_sensitive, findings = SensitiveContentFilter.check(content)
        if has_sensitive:
            return make_error_response(
                code="VALIDATION_ERROR",
                message="内容包含敏感信息，写入被拒绝",
                details={"findings": findings},
            )

        validation_errors = InputValidator.validate_all(title=title, content=content)
        if validation_errors:
            return make_error_response(
                code="BAD_REQUEST",
                message="输入验证失败",
                details={"validation_errors": validation_errors},
            )

        entry_data = {
            "title": title,
            "content": content,
            "scope": scope,
            "tags": tags or [],
            "source_rating": source_rating,
        }
        dedup_result = self.dedup.check_duplicate(entry_data)
        if dedup_result["action"] == "merge":
            existing = self.sqlite.get_entry(dedup_result["existing_id"])
            if existing:
                merged = self.dedup.merge_entries(existing, entry_data)
                self.sqlite.update_entry(existing["id"], merged)
                if self.chroma.available:
                    try:
                        self.chroma.add_embedding(existing["id"], content, {"scope": scope, "title": title})
                        self.sqlite.update_embedding_status(existing["id"], "ready")
                    except Exception:
                        self.sqlite.update_embedding_status(existing["id"], "pending")
                        logger.warning("operation=mcp_add_merged_chroma_failed, entry_id=%s", existing["id"])
                logger.info("operation=mcp_add_merged, entry_id=%s", existing["id"])
                self._touch_change()
                self.ws_manager.broadcast_sync({
                    "type": "updated",
                    "entry_id": existing["id"],
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                })
                return make_response("ok", {
                    "id": existing["id"],
                    "status": "merged",
                    "dedup_status": "duplicate_merged",
                })
        elif dedup_result["action"] == "skip":
            return make_response("conflict", {
                "id": dedup_result["existing_id"],
                "status": "duplicate_rejected",
                "dedup_status": "duplicate",
                "similarity_score": dedup_result["similarity_score"],
            })

        result = self.sqlite.add_entry(entry_data)
        if self.chroma.available:
            try:
                self.chroma.add_embedding(result["id"], content, {"scope": scope, "title": title})
                self.sqlite.update_embedding_status(result["id"], "ready")
            except Exception:
                self.sqlite.update_embedding_status(result["id"], "pending")
                logger.warning("operation=mcp_add_chroma_failed, entry_id=%s", result["id"])
        logger.info("operation=mcp_add_created, entry_id=%s", result["id"])
        self._touch_change()
        self.ws_manager.broadcast_sync({
            "type": "created",
            "entry_id": result["id"],
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })
        return make_response("ok", {"id": result["id"], "status": "created", "dedup_status": "new"})

    def mcp_knowledge_update(self, entry_id: str, content: Optional[str] = None, tags: Optional[list[str]] = None, confidence: Optional[float] = None) -> dict:
        updates = {}
        if content is not None:
            has_sensitive, findings = SensitiveContentFilter.check(content)
            if has_sensitive:
                return make_error_response(
                    code="VALIDATION_ERROR",
                    message="内容包含敏感信息，写入被拒绝",
                    details={"findings": findings},
                )
            validation_errors = InputValidator.validate_all(content=content)
            if validation_errors:
                return make_error_response(
                    code="BAD_REQUEST",
                    message="输入验证失败",
                    details={"validation_errors": validation_errors},
                )
            updates["content"] = content
        if tags is not None:
            updates["tags"] = tags
        if confidence is not None:
            updates["confidence"] = confidence
        result = self.sqlite.update_entry(entry_id, updates)
        if result is None:
            return make_error_response(
                code="NOT_FOUND",
                message="知识条目不存在",
                details={"entry_id": entry_id},
            )
        if isinstance(result, dict) and result.get("error") == "version_conflict":
            return make_error_response(
                code="VERSION_CONFLICT",
                message="版本冲突，条目已被其他操作修改",
                details={
                    "entry_id": entry_id,
                    "current_version": result["current_version"],
                    "expected_version": result["expected_version"],
                },
                retryable=True,
            )
        if self.chroma.available and content is not None:
            try:
                self.chroma.add_embedding(entry_id, content, {"scope": result.get("scope", ""), "title": result.get("title", "")})
                self.sqlite.update_embedding_status(entry_id, "ready")
            except Exception:
                self.sqlite.update_embedding_status(entry_id, "pending")
                logger.warning("operation=mcp_update_chroma_failed, entry_id=%s", entry_id)
        logger.info("operation=mcp_updated, entry_id=%s", entry_id)
        self._touch_change()
        self.ws_manager.broadcast_sync({
            "type": "updated",
            "entry_id": entry_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })
        return make_response("ok", {"id": entry_id, "status": "updated"})

    def mcp_knowledge_delete(self, entry_id: str) -> dict:
        deleted = self.sqlite.delete_entry(entry_id)
        if deleted:
            self.chroma.delete_embedding(entry_id)
            logger.info("operation=mcp_deleted, entry_id=%s", entry_id)
            self._touch_change()
            self.ws_manager.broadcast_sync({
                "type": "deleted",
                "entry_id": entry_id,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            })
            return make_response("ok", {"id": entry_id, "status": "deleted"})
        return make_error_response(
            code="NOT_FOUND",
            message="知识条目不存在",
            details={"entry_id": entry_id},
        )

    def mcp_knowledge_rollback(self, backup_path: str, dry_run: bool = False) -> dict:
        try:
            result = self.backup_mgr.rollback(backup_path, dry_run=dry_run)
            return make_response("ok", result)
        except FileNotFoundError as e:
            return make_error_response(
                code="NOT_FOUND",
                message=str(e),
            )
        except Exception as e:
            return make_error_response(
                code="INTERNAL_ERROR",
                message=f"回滚失败: {e}",
            )

    def mcp_knowledge_rollback_version(self, entry_id: str, target_version: int) -> dict:
        result = self.sqlite.restore_version(entry_id, target_version)
        if result is None:
            return make_error_response(
                code="NOT_FOUND",
                message=f"版本不存在: entry_id={entry_id}, target_version={target_version}",
                details={"entry_id": entry_id, "target_version": target_version},
            )
        if self.chroma.available:
            try:
                self.chroma.add_embedding(
                    entry_id,
                    result.get("content", ""),
                    {"scope": result.get("scope", ""), "title": result.get("title", "")},
                )
                self.sqlite.update_embedding_status(entry_id, "ready")
            except Exception:
                self.sqlite.update_embedding_status(entry_id, "pending")
                logger.warning("operation=mcp_rollback_chroma_failed, entry_id=%s", entry_id)
        logger.info("operation=mcp_rollback, entry_id=%s, target_version=%d", entry_id, target_version)
        self._touch_change()
        self.ws_manager.broadcast_sync({
            "type": "rolled_back",
            "entry_id": entry_id,
            "target_version": target_version,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })
        return make_response("ok", {"id": entry_id, "status": "rolled_back", "target_version": target_version})

    def shutdown(self):
        logger.info("operation=shutdown, status=starting")
        self._shutting_down = True

        timeout = 30
        start = time.time()
        while self._active_requests > 0 and (time.time() - start) < timeout:
            time.sleep(0.5)

        timed_out = self._active_requests > 0
        if timed_out:
            logger.warning("operation=shutdown, status=timeout, active_requests=%d", self._active_requests)

        self._stop_retry_task()
        self._stop_backup_scheduler()
        if self._sync_timer is not None:
            self._sync_timer.cancel()
        if self._lifecycle_timer is not None:
            self._lifecycle_timer.cancel()
        self.degradation.stop_periodic_check()

        try:
            conn = self.sqlite._get_conn()
            conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")
            logger.info("operation=shutdown_wal_checkpoint, status=completed")
        except Exception as e:
            logger.warning("operation=shutdown_wal_checkpoint, status=failed, error=%s", e)

        try:
            if self.chroma.available and self.chroma._client is not None:
                if hasattr(self.chroma._client, 'persist'):
                    self.chroma._client.persist()
                logger.info("operation=shutdown_chroma_persist, status=completed")
        except Exception as e:
            logger.warning("operation=shutdown_chroma_persist, status=failed, error=%s", e)

        self.chroma.close()
        self.sqlite.close()
        logger.info("operation=shutdown, status=completed")
        sys.exit(1 if timed_out else 0)
