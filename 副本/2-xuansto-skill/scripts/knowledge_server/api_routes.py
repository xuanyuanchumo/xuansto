import logging
from datetime import datetime, timezone

from .config import fastapi_available, make_response, make_error_response
from .security import InputValidator, SensitiveContentFilter
from .api_models import SearchRequest, AddRequest, UpdateRequest, RollbackVersionRequest
from .exporter import KnowledgeExporter

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
        if req.filters:
            min_confidence = req.filters.get("min_confidence", 0.0)
            tag_filters = req.filters.get("tags")
        try:
            result = server.retrieval.search(
                query=req.query,
                scope=req.scope,
                top_k=req.top_k,
                strategy=req.strategy,
                min_confidence=min_confidence,
                tag_filters=tag_filters,
                agent_role=req.agent_role,
            )
            result["degradation_level"] = server.degradation.level
            result["degradation_name"] = server.degradation.level_name
            if req.agent_role:
                result["agent_role"] = req.agent_role
            return make_response("ok", result)
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
        return make_response("ok", entry)

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
                await server.ws_manager.broadcast({
                    "type": "updated",
                    "entry_id": existing["id"],
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                })
                return make_response("ok", {
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
            await server.ws_manager.broadcast({
                "type": "created",
                "entry_id": result["id"],
                "timestamp": datetime.now(timezone.utc).isoformat(),
            })
            return make_response("ok", {
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
        await server.ws_manager.broadcast({
            "type": "updated",
            "entry_id": entry_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })
        return make_response("ok", {
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
        await server.ws_manager.broadcast({
            "type": "deleted",
            "entry_id": entry_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })
        return make_response("ok", {
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
        await server.ws_manager.broadcast({
            "type": "rolled_back",
            "entry_id": req.entry_id,
            "target_version": req.target_version,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })
        return make_response("ok", {
            "id": req.entry_id,
            "status": "rolled_back",
            "target_version": req.target_version,
        })

    @application.get("/v1/knowledge/{entry_id}/versions")
    async def get_version_history(entry_id: str):
        versions = server.sqlite.get_version_history(entry_id)
        return make_response("ok", {
            "entry_id": entry_id,
            "versions": versions,
            "total": len(versions),
        })
