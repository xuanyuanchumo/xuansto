import logging
from datetime import datetime, timezone

from .config import fastapi_available, make_response, make_error_response
from .security import InputValidator, SensitiveContentFilter
from .api_models import SearchRequest, AddRequest, UpdateRequest, RollbackVersionRequest, ProgressiveSearchRequest, DeepLoadRequest, WebUpdateRequest, AutoRetrieveRequest, StatsRequest
from .web_search import (
    search_official_docs, extract_and_structure, detect_stale_entries,
    detect_new_tech_dependencies, auto_ingest_tech_knowledge, OFFICIAL_SOURCES,
)

logger = logging.getLogger("knowledge-server")

if fastapi_available:
    from fastapi import HTTPException


def register_crud_routes(application, server):
    @application.post("/v1/knowledge/search")
    async def search_knowledge(req: SearchRequest):
        validation_errors = InputValidator.validate_all(query=req.query)
        if validation_errors:
            raise HTTPException(
                status_code=400,
                detail=make_error_response(
                    code="BAD_REQUEST",
                    message="输入验证失败",
                    details={"validation_errors": validation_errors},
                ),
            )

        effective_strategy = server.degradation.get_search_strategy()
        if req.strategy != "keyword_only" and effective_strategy != "hybrid":
            req.strategy = effective_strategy

        min_confidence = 0.0
        tag_filters = None
        type_filters = None
        category_filters = None
        if req.filters:
            min_confidence = req.filters.get("min_confidence", 0.0)
            tag_filters = req.filters.get("tags")
            type_filters = req.filters.get("type")
            category_filters = req.filters.get("category")
        try:
            result = server.retrieval.search(
                query=req.query,
                scope=req.scope,
                top_k=req.top_k,
                strategy=req.strategy,
                min_confidence=min_confidence,
                tag_filters=tag_filters,
                agent_role=req.agent_role,
                type_filters=type_filters,
                category_filters=category_filters,
            )
            result["degradation_level"] = server.degradation.level
            result["degradation_name"] = server.degradation.level_name
            if req.agent_role:
                result["agent_role"] = req.agent_role
            return make_response("success", result)
        except Exception as e:
            raise HTTPException(
                status_code=503,
                detail=make_error_response(
                    code="SERVICE_DEGRADED",
                    message="检索引擎不可用",
                    details={"exception": str(e)},
                    retryable=True,
                ),
            )

    @application.post("/v1/knowledge/stats")
    async def get_stats(req: StatsRequest):
        counts = server.sqlite.count_entries()
        embedding_status_counts = server.sqlite.count_by_embedding_status()
        stats = {
            "total_entries": counts.get("total", 0),
            "by_scope": {k: v for k, v in counts.items() if k != "total"},
            "embedding": {
                "pending": embedding_status_counts.get("pending", 0),
                "ready": embedding_status_counts.get("ready", 0),
            },
            "chroma_available": server.chroma.available,
            "chroma_vector_count": server.chroma.get_vector_count() if server.chroma.available else 0,
            "degradation_level": server.degradation.level,
            "degradation_name": server.degradation.level_name,
            "embedding_level": server.embedding_manager.level,
            "embedding_level_name": server.embedding_manager.level_name,
            "last_change_timestamp": server._last_change_timestamp,
        }
        if req.since:
            from datetime import datetime as _dt
            try:
                since_dt = _dt.fromisoformat(req.since.replace("Z", "+00:00"))
                last_dt = _dt.fromisoformat(server._last_change_timestamp.replace("Z", "+00:00"))
                stats["status_changed_since_last_check"] = last_dt > since_dt
            except (ValueError, TypeError):
                stats["status_changed_since_last_check"] = None
        if req.detailed:
            all_entries = server.sqlite.get_all_entries()
            type_counts = {}
            category_counts = {}
            for e in all_entries:
                t = e.get("type", "unknown")
                c = e.get("category", "uncategorized")
                type_counts[t] = type_counts.get(t, 0) + 1
                category_counts[c] = category_counts.get(c, 0) + 1
            stats["by_type"] = type_counts
            stats["by_category"] = category_counts
        return make_response("success", stats)

    async def _get_entry_handler(entry_id: str):
        entry = server.sqlite.get_entry(entry_id)
        if entry is None:
            raise HTTPException(
                status_code=404,
                detail=make_error_response(
                    code="NOT_FOUND",
                    message="知识条目不存在",
                    details={"entry_id": entry_id},
                ),
            )
        return make_response("success", entry)

    @application.get("/v1/knowledge/get/{entry_id}")
    async def get_entry_new(entry_id: str):
        return await _get_entry_handler(entry_id)

    @application.get("/v1/knowledge/{entry_id}")
    async def get_entry_legacy(entry_id: str):
        return await _get_entry_handler(entry_id)

    @application.post("/v1/knowledge/add")
    async def add_entry(req: AddRequest):
        validation_errors = InputValidator.validate_all(
            title=req.title,
            content=req.content,
            source_path=req.source_path or "",
        )
        if validation_errors:
            raise HTTPException(
                status_code=400,
                detail=make_error_response(
                    code="BAD_REQUEST",
                    message="输入验证失败",
                    details={"validation_errors": validation_errors},
                ),
            )

        has_sensitive, findings = SensitiveContentFilter.check(req.content)
        if has_sensitive:
            raise HTTPException(
                status_code=422,
                detail=make_error_response(
                    code="VALIDATION_ERROR",
                    message="内容包含敏感信息，写入被拒绝",
                    details={"findings": findings},
                ),
            )

        entry_data = req.model_dump()
        dedup_result = server.dedup.check_duplicate(entry_data)

        if dedup_result["action"] == "merge":
            existing = server.sqlite.get_entry(dedup_result["existing_id"])
            if existing:
                merged = server.dedup.merge_entries(existing, entry_data)
                server.sqlite.update_entry(existing["id"], merged)
                if server.chroma.available:
                    try:
                        server.chroma.add_embedding(
                            existing["id"],
                            merged.get("content", req.content),
                            {"scope": req.scope, "title": merged.get("title", req.title)},
                        )
                        server.sqlite.update_embedding_status(existing["id"], "ready")
                    except Exception:
                        server.sqlite.update_embedding_status(existing["id"], "pending")
                        logger.warning("operation=add_merged_chroma_failed, entry_id=%s", existing["id"])
                logger.info("operation=add_merged, entry_id=%s", existing["id"])
                server.exporter.export_entry(existing["id"])
                server._touch_change()
                await server.ws_manager.broadcast({
                    "type": "updated",
                    "entry_id": existing["id"],
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                })
                return make_response("success", {
                    "id": existing["id"],
                    "status": "merged",
                    "dedup_status": "duplicate_merged",
                    "similarity_score": dedup_result["similarity_score"],
                })
        elif dedup_result["action"] == "skip":
            raise HTTPException(
                status_code=409,
                detail=make_error_response(
                    code="DUPLICATE_DETECTED",
                    message="知识条目重复",
                    details={
                        "similarity_score": dedup_result["similarity_score"],
                        "existing_entry_id": dedup_result["existing_id"],
                    },
                ),
            )

        try:
            result = server.sqlite.add_entry(entry_data)
            if server.chroma.available:
                try:
                    server.chroma.add_embedding(
                        result["id"],
                        req.content,
                        {"scope": req.scope, "title": req.title},
                    )
                    server.sqlite.update_embedding_status(result["id"], "ready")
                except Exception:
                    server.sqlite.update_embedding_status(result["id"], "pending")
                    logger.warning("operation=add_chroma_failed, entry_id=%s", result["id"])
            logger.info("operation=add_created, entry_id=%s", result["id"])
            server.exporter.export_entry(result["id"])
            server._touch_change()
            await server.ws_manager.broadcast({
                "type": "created",
                "entry_id": result["id"],
                "timestamp": datetime.now(timezone.utc).isoformat(),
            })
            return make_response("success", {
                "id": result["id"],
                "status": "created",
                "dedup_status": "new",
            })
        except ValueError as e:
            raise HTTPException(
                status_code=400,
                detail=make_error_response(
                    code="BAD_REQUEST",
                    message=str(e),
                ),
            )

    async def _update_entry_handler(entry_id: str, req: UpdateRequest):
        updates = req.model_dump(exclude_none=True)
        if not updates:
            raise HTTPException(
                status_code=400,
                detail=make_error_response(
                    code="BAD_REQUEST",
                    message="请求参数无效",
                    details={"reason": "未提供任何更新字段"},
                ),
            )

        validation_errors = InputValidator.validate_all(
            title=updates.get("title", ""),
            content=updates.get("content", ""),
        )
        if validation_errors:
            raise HTTPException(
                status_code=400,
                detail=make_error_response(
                    code="BAD_REQUEST",
                    message="输入验证失败",
                    details={"validation_errors": validation_errors},
                ),
            )

        if "content" in updates:
            has_sensitive, findings = SensitiveContentFilter.check(updates["content"])
            if has_sensitive:
                raise HTTPException(
                    status_code=422,
                    detail=make_error_response(
                        code="VALIDATION_ERROR",
                        message="内容包含敏感信息，写入被拒绝",
                        details={"findings": findings},
                    ),
                )

        max_retries = 3
        result = None

        for attempt in range(max_retries):
            result = server.sqlite.update_entry(entry_id, updates)
            if result is None:
                raise HTTPException(
                    status_code=404,
                    detail=make_error_response(
                        code="NOT_FOUND",
                        message="知识条目不存在",
                        details={"entry_id": entry_id},
                    ),
                )
            if isinstance(result, dict) and result.get("error") == "version_conflict":
                current = server.sqlite.get_entry(entry_id)
                if current is None:
                    raise HTTPException(
                        status_code=404,
                        detail=make_error_response(
                            code="NOT_FOUND",
                            message="知识条目不存在",
                            details={"entry_id": entry_id},
                        ),
                    )
                updates["version"] = current["version"]
                continue
            break
        else:
            current = server.sqlite.get_entry(entry_id)
            if current is None:
                raise HTTPException(
                    status_code=404,
                    detail=make_error_response(
                        code="NOT_FOUND",
                        message="知识条目不存在",
                        details={"entry_id": entry_id},
                    ),
                )
            raise HTTPException(
                status_code=409,
                detail=make_error_response(
                    code="VERSION_CONFLICT",
                    message="版本冲突：条目已被其他操作修改，请获取最新版本后重试",
                    details={
                        "entry_id": entry_id,
                        "current_version": current["version"],
                    },
                    retryable=True,
                ),
            )
        if server.chroma.available and "content" in updates:
            try:
                server.chroma.add_embedding(
                    entry_id,
                    updates["content"],
                    {"scope": result.get("scope", "workspace"), "title": result.get("title", "")},
                )
                server.sqlite.update_embedding_status(entry_id, "ready")
            except Exception:
                server.sqlite.update_embedding_status(entry_id, "pending")
                logger.warning("operation=update_chroma_failed, entry_id=%s", entry_id)
        logger.info("operation=updated, entry_id=%s", entry_id)
        server.exporter.export_entry(entry_id)
        server._touch_change()
        await server.ws_manager.broadcast({
            "type": "updated",
            "entry_id": entry_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })
        return make_response("success", {
            "id": entry_id,
            "status": "updated",
        })

    @application.put("/v1/knowledge/update/{entry_id}")
    async def update_entry_new(entry_id: str, req: UpdateRequest):
        return await _update_entry_handler(entry_id, req)

    @application.put("/v1/knowledge/{entry_id}")
    async def update_entry_legacy(entry_id: str, req: UpdateRequest):
        return await _update_entry_handler(entry_id, req)

    async def _delete_entry_handler(entry_id: str):
        deleted = server.sqlite.delete_entry(entry_id)
        if not deleted:
            raise HTTPException(
                status_code=404,
                detail=make_error_response(
                    code="NOT_FOUND",
                    message="知识条目不存在",
                    details={"entry_id": entry_id},
                ),
            )
        server.chroma.delete_embedding(entry_id)
        logger.info("operation=deleted, entry_id=%s", entry_id)
        server._touch_change()
        await server.ws_manager.broadcast({
            "type": "deleted",
            "entry_id": entry_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })
        return make_response("success", {
            "id": entry_id,
            "status": "deleted",
        })

    @application.delete("/v1/knowledge/delete/{entry_id}")
    async def delete_entry_new(entry_id: str):
        return await _delete_entry_handler(entry_id)

    @application.delete("/v1/knowledge/{entry_id}")
    async def delete_entry_legacy(entry_id: str):
        return await _delete_entry_handler(entry_id)

    @application.post("/v1/knowledge/rollback")
    async def rollback_version(req: RollbackVersionRequest):
        validation_errors = InputValidator.validate_all(entry_id=req.entry_id)
        if validation_errors:
            raise HTTPException(
                status_code=400,
                detail=make_error_response(
                    code="BAD_REQUEST",
                    message="输入验证失败",
                    details={"validation_errors": validation_errors},
                ),
            )
        result = server.sqlite.restore_version(req.entry_id, req.target_version)
        if result is None:
            raise HTTPException(
                status_code=404,
                detail=make_error_response(
                    code="NOT_FOUND",
                    message="版本不存在",
                    details={"entry_id": req.entry_id, "target_version": req.target_version},
                ),
            )
        if server.chroma.available:
            try:
                server.chroma.add_embedding(
                    req.entry_id,
                    result.get("content", ""),
                    {"scope": result.get("scope", ""), "title": result.get("title", "")},
                )
                server.sqlite.update_embedding_status(req.entry_id, "ready")
            except Exception:
                server.sqlite.update_embedding_status(req.entry_id, "pending")
                logger.warning("operation=rollback_chroma_failed, entry_id=%s", req.entry_id)
        logger.info("operation=rollback, entry_id=%s, target_version=%d", req.entry_id, req.target_version)
        server._touch_change()
        await server.ws_manager.broadcast({
            "type": "rolled_back",
            "entry_id": req.entry_id,
            "target_version": req.target_version,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })
        return make_response("success", {
            "id": req.entry_id,
            "status": "rolled_back",
            "target_version": req.target_version,
        })

    @application.get("/v1/knowledge/{entry_id}/versions")
    async def get_version_history(entry_id: str):
        versions = server.sqlite.get_version_history(entry_id)
        return make_response("success", {
            "entry_id": entry_id,
            "versions": versions,
            "total": len(versions),
        })

    @application.post("/v1/knowledge/progressive_search")
    async def progressive_search(req: ProgressiveSearchRequest):
        validation_errors = InputValidator.validate_all(query=req.query)
        if validation_errors:
            raise HTTPException(
                status_code=400,
                detail=make_error_response(
                    code="BAD_REQUEST",
                    message="输入验证失败",
                    details={"validation_errors": validation_errors},
                ),
            )

        try:
            result = server.progressive_searcher.search(
                query=req.query,
                task_type=req.task_type,
                tech_stack=req.tech_stack,
                token_budget=req.token_budget,
            )
            result["degradation_level"] = server.degradation.level
            result["degradation_name"] = server.degradation.level_name
            return make_response("success", result)
        except Exception as e:
            raise HTTPException(
                status_code=503,
                detail=make_error_response(
                    code="SERVICE_DEGRADED",
                    message="渐进式检索引擎不可用",
                    details={"exception": str(e)},
                    retryable=True,
                ),
            )

    @application.post("/v1/knowledge/deep_load")
    async def deep_load(req: DeepLoadRequest):
        result = server.progressive_searcher.deep_load(req.entry_id)
        if "error" in result:
            raise HTTPException(
                status_code=404,
                detail=make_error_response(
                    code="NOT_FOUND",
                    message="知识条目不存在",
                    details={"entry_id": req.entry_id},
                ),
            )
        return make_response("success", result)

    @application.post("/v1/knowledge/web_update")
    async def knowledge_web_update(req: WebUpdateRequest):
        target_entry = None
        query_parts = []

        if req.entry_id:
            target_entry = server.sqlite.get_entry(req.entry_id)
            if target_entry is None:
                raise HTTPException(
                    status_code=404,
                    detail=make_error_response(
                        code="NOT_FOUND",
                        message="知识条目不存在",
                        details={"entry_id": req.entry_id},
                    ),
                )
            query_parts.append(target_entry.get("title", ""))
            if target_entry.get("category") and target_entry["category"] != "uncategorized":
                query_parts.append(target_entry["category"])
        elif req.category:
            query_parts.append(req.category)

        if req.tags:
            query_parts.extend(req.tags)

        if not query_parts:
            raise HTTPException(
                status_code=400,
                detail=make_error_response(
                    code="BAD_REQUEST",
                    message="必须提供 entry_id、category 或 tags 中的至少一个参数",
                ),
            )

        query = " ".join(query_parts)
        tech_stack = req.tags if req.tags else None

        try:
            web_results = search_official_docs(query, tech_stack=tech_stack)
        except Exception as e:
            logger.warning("operation=web_update, search_error=%s", e)
            web_results = []

        if not web_results:
            return make_response("success", {
                "status": "no_results",
                "query": query,
                "message": "网络搜索未找到相关结果，可能处于离线状态",
            })

        structured = extract_and_structure(web_results, existing_entry=target_entry)
        if not structured:
            return make_response("success", {
                "status": "extraction_failed",
                "query": query,
                "sources_found": len(web_results),
                "message": "无法从搜索结果中提取有效内容",
            })

        if target_entry:
            updates = {}
            if structured.get("content"):
                updates["content"] = structured["content"]
            if structured.get("title") and structured.get("title") != target_entry.get("title"):
                updates["title"] = structured["title"]
            if structured.get("source_rating") and structured["source_rating"] > target_entry.get("source_rating", 0):
                updates["source_rating"] = structured["source_rating"]
            if structured.get("source_path"):
                updates["source_path"] = structured["source_path"]
            if structured.get("tags"):
                existing_tags = set(target_entry.get("tags", []))
                new_tags = list(existing_tags | set(structured["tags"]))
                updates["tags"] = new_tags
            if structured.get("summary"):
                updates["summary"] = structured["summary"]

            now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
            updates["last_validated"] = now

            if updates:
                result = server.sqlite.update_entry(req.entry_id, updates)
                if result and not (isinstance(result, dict) and result.get("error")):
                    if server.chroma.available and "content" in updates:
                        try:
                            server.chroma.add_embedding(
                                req.entry_id,
                                updates["content"],
                                {"scope": result.get("scope", "workspace"), "title": result.get("title", "")},
                            )
                            server.sqlite.update_embedding_status(req.entry_id, "ready")
                        except Exception:
                            server.sqlite.update_embedding_status(req.entry_id, "pending")
                    server.exporter.export_entry(req.entry_id)
                    server._touch_change()
                    await server.ws_manager.broadcast({
                        "type": "web_updated",
                        "entry_id": req.entry_id,
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                    })
                    logger.info("operation=web_update, entry_id=%s, status=updated", req.entry_id)
                    return make_response("success", {
                        "id": req.entry_id,
                        "status": "updated",
                        "sources_found": len(web_results),
                        "best_source_rating": max(r.get("source_rating", 0) for r in web_results),
                        "updated_fields": list(updates.keys()),
                    })

            return make_response("success", {
                "id": req.entry_id,
                "status": "no_change",
                "sources_found": len(web_results),
                "message": "搜索结果未带来有效更新",
            })
        else:
            now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
            structured["last_validated"] = now
            structured["confidence"] = min(structured.get("confidence", 0.6), 0.6)

            try:
                result = server.sqlite.add_entry(structured)
                entry_id = result["id"]
                if server.chroma.available:
                    try:
                        server.chroma.add_embedding(
                            entry_id,
                            structured.get("content", ""),
                            {"scope": structured.get("scope", "general"), "title": structured.get("title", "")},
                        )
                        server.sqlite.update_embedding_status(entry_id, "ready")
                    except Exception:
                        server.sqlite.update_embedding_status(entry_id, "pending")
                server.exporter.export_entry(entry_id)
                server._touch_change()
                await server.ws_manager.broadcast({
                    "type": "web_created",
                    "entry_id": entry_id,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                })
                logger.info("operation=web_update, new_entry_id=%s, status=created_pending_review", entry_id)
                return make_response("success", {
                    "id": entry_id,
                    "status": "created_pending_review",
                    "sources_found": len(web_results),
                    "best_source_rating": max(r.get("source_rating", 0) for r in web_results),
                })
            except ValueError as e:
                raise HTTPException(
                    status_code=400,
                    detail=make_error_response(
                        code="BAD_REQUEST",
                        message=str(e),
                    ),
                )

    @application.post("/v1/knowledge/auto_retrieve")
    async def auto_retrieve(req: AutoRetrieveRequest):
        try:
            result = server.auto_retrieve(
                task_type=req.task_type,
                project_path=req.project_path,
                query=req.query,
                token_budget=req.token_budget,
            )
            return make_response("success", result)
        except Exception as e:
            raise HTTPException(
                status_code=503,
                detail=make_error_response(
                    code="SERVICE_DEGRADED",
                    message="自动检索不可用",
                    details={"exception": str(e)},
                    retryable=True,
                ),
            )
