import asyncio
import json
import logging
from datetime import datetime, timezone

from .config import fastapi_available, KB_VERSION, make_response, make_error_response
from .security import InputValidator, SensitiveContentFilter
from .api_models import (
    SearchRequest, AddRequest, UpdateRequest,
    BackupRequest, RollbackVersionRequest,
)

logger = logging.getLogger("knowledge-server")

if fastapi_available:
    from fastapi import FastAPI, HTTPException, Request, WebSocket, WebSocketDisconnect
    from fastapi.responses import JSONResponse
    from fastapi.middleware.cors import CORSMiddleware


def _register_middleware(application, server, is_remote):
    @application.middleware("http")
    async def shutdown_middleware(request: Request, call_next):
        if server._shutting_down:
            return JSONResponse(
                status_code=503,
                content=make_error_response(
                    code="SERVICE_UNAVAILABLE",
                    message="服务器正在关闭",
                    retryable=True,
                ),
            )
        async with server._active_requests_lock:
            server._active_requests += 1
        try:
            response = await call_next(request)
            return response
        finally:
            async with server._active_requests_lock:
                server._active_requests -= 1

    @application.middleware("http")
    async def auth_and_rate_limit_middleware(request: Request, call_next):
        client_ip = request.client.host if request.client else "unknown"

        allowed, retry_after = server.rate_limiter.check(client_ip)
        if not allowed:
            return JSONResponse(
                status_code=429,
                content=make_error_response(
                    code="RATE_LIMITED",
                    message="请求频率超限，请稍后重试",
                    details={"retry_after": retry_after},
                    retryable=True,
                ),
            )

        if is_remote:
            api_key = request.headers.get("X-API-Key")
            if not api_key or not server.api_key_auth.validate_key(api_key):
                return JSONResponse(
                    status_code=401,
                    content=make_error_response(
                        code="UNAUTHORIZED",
                        message="缺少或无效的API Key",
                        details={"header": "X-API-Key"},
                    ),
                )

            path = request.url.path
            method = request.method
            permission_level = server.api_key_auth.get_permission_level(api_key)

            if path.startswith("/v1/knowledge/backup") or path.startswith("/v1/knowledge/rollback"):
                if permission_level != "admin":
                    return JSONResponse(
                        status_code=403,
                        content=make_error_response(
                            code="UNAUTHORIZED",
                            message="权限不足，需要admin权限",
                            details={"required": "admin", "current": permission_level},
                        ),
                    )
            elif method in ("PUT", "DELETE"):
                if permission_level not in ("read-write", "admin"):
                    return JSONResponse(
                        status_code=403,
                        content=make_error_response(
                            code="UNAUTHORIZED",
                            message="权限不足，需要read-write或admin权限",
                            details={"required": "read-write or admin", "current": permission_level},
                        ),
                    )
            elif method == "POST" and path != "/v1/knowledge/search":
                if permission_level not in ("read-write", "admin"):
                    return JSONResponse(
                        status_code=403,
                        content=make_error_response(
                            code="UNAUTHORIZED",
                            message="权限不足，需要read-write或admin权限",
                            details={"required": "read-write or admin", "current": permission_level},
                        ),
                    )

        response = await call_next(request)
        return response

    @application.exception_handler(Exception)
    async def global_exception_handler(request, exc):
        logger.error("operation=unhandled_exception, error=%s", exc, exc_info=True)
        return JSONResponse(
            status_code=500,
            content=make_error_response(
                code="INTERNAL_ERROR",
                message="内部服务器错误",
                details={"exception": str(exc)},
                retryable=False,
            ),
        )


def _register_websocket(application, server):
    @application.websocket("/ws")
    async def websocket_endpoint(websocket: WebSocket):
        await server.ws_manager.connect(websocket)
        try:
            while True:
                await websocket.receive_text()
        except WebSocketDisconnect:
            server.ws_manager.disconnect(websocket)
        except Exception:
            server.ws_manager.disconnect(websocket)


def _register_health_routes(application, server):
    @application.get("/v1/knowledge/health")
    async def health_check():
        counts = server.sqlite.count_entries()
        embedding_status_counts = server.sqlite.count_by_embedding_status()
        engines = {
            "sqlite": "connected",
            "chroma": "connected" if server.chroma.available else "unavailable",
        }
        return make_response("success", {
            "status": "healthy",
            "version": KB_VERSION,
            "engines": engines,
            "stats": counts,
            "embedding": {
                "degraded": server.embedding_manager.degraded,
                "level": server.embedding_manager.level,
                "level_name": server.embedding_manager.level_name,
                "dimension": server.embedding_manager.dimension,
                "pending_count": embedding_status_counts.get("pending", 0),
                "ready_count": embedding_status_counts.get("ready", 0),
            },
            "degradation": {
                "level": server.degradation.level,
                "name": server.degradation.level_name,
            },
            "websocket_connections": server.ws_manager.connection_count,
        })

    @application.get("/v1/health/consistency")
    async def consistency_check():
        sqlite_counts = server.sqlite.count_entries()
        sqlite_ready = server.sqlite.count_by_embedding_status().get("ready", 0)
        chroma_count = server.chroma.get_vector_count()

        missing_in_chroma = 0
        orphan_in_chroma = 0

        if server.chroma.available:
            all_entries = server.sqlite.get_all_entries()
            ready_ids = {e["id"] for e in all_entries if e.get("embedding_status") == "ready"}
            try:
                chroma_ids = server.chroma.get_all_ids()
                missing_in_chroma = len(ready_ids - chroma_ids)
                orphan_in_chroma = len(chroma_ids - {e["id"] for e in all_entries})
            except Exception as e:
                logger.warning("operation=consistency_check, chroma_error=%s", e)

        consistent = (missing_in_chroma == 0 and orphan_in_chroma == 0)

        return make_response("success", {
            "consistent": consistent,
            "sqlite": {
                "total_entries": sqlite_counts.get("total", 0),
                "embedding_ready": sqlite_ready,
            },
            "chroma": {
                "available": server.chroma.available,
                "vector_count": chroma_count,
            },
            "discrepancies": {
                "missing_in_chroma": missing_in_chroma,
                "orphan_in_chroma": orphan_in_chroma,
            },
        })

    @application.post("/v1/knowledge/backup")
    async def create_backup(req: BackupRequest):
        try:
            result = server.backup_mgr.create_backup(
                backup_type=req.type,
                destination=req.destination,
            )
            return make_response("success", result)
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=make_error_response(
                    code="INTERNAL_ERROR",
                    message="备份创建失败",
                    details={"exception": str(e)},
                ),
            )


def create_app(server):
    if not fastapi_available:
        raise RuntimeError("FastAPI/uvicorn未安装，无法启动HTTP服务")

    application = FastAPI(
        title="知识库API服务",
        version=KB_VERSION,
        description="Xuansto Skill 知识库 REST API + MCP Tool 接口",
    )

    cors_origins = server.config.server.get("cors_origins", [])
    application.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins if cors_origins else [],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    is_remote = server._is_remote_mode()

    _register_middleware(application, server, is_remote)
    _register_websocket(application, server)
    _register_health_routes(application, server)

    from .api_routes import register_crud_routes
    register_crud_routes(application, server)

    return application
