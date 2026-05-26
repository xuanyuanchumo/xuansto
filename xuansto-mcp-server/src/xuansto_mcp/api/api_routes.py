from __future__ import annotations

from typing import Any

from ..core.errors import ERROR_CODE_TO_HTTP_STATUS, make_error_response, make_success_response
from ..core.logging_config import get_logger

logger = get_logger("api_routes")

try:
    from fastapi import FastAPI
    from fastapi.responses import JSONResponse
    _FASTAPI_AVAILABLE = True
except ImportError:
    _FASTAPI_AVAILABLE = False


def _error_response_to_http_status(result: dict[str, Any]) -> int:
    error_info = result.get("error")
    if isinstance(error_info, dict):
        error_code = error_info.get("code", "")
    else:
        error_code = result.get("error_code", "")
    return ERROR_CODE_TO_HTTP_STATUS.get(error_code, 500)


def create_api_app() -> Any:
    if not _FASTAPI_AVAILABLE:
        raise ImportError("FastAPI is required for HTTP API. Install with: pip install fastapi")

    app = FastAPI(
        title="Xuansto MCP Server HTTP API",
        description="HTTP API with unified response format matching MCP tool responses",
        version="1.0.0",
    )

    @app.get("/health")
    async def health_check() -> dict[str, Any]:
        try:
            from ..core.config import MCP_API_VERSION, MCP_MIN_SUPPORTED_VERSION
            from .tools.server_health import _check_chromadb_health
            chromadb_status = _check_chromadb_health()
            result = make_success_response(data={
                "status": "healthy",
                "api_version": MCP_API_VERSION,
                "min_supported_version": MCP_MIN_SUPPORTED_VERSION,
                "services": {
                    "chromadb": chromadb_status,
                },
            })
            return JSONResponse(content=result)
        except Exception as e:
            result = make_error_response(e)
            return JSONResponse(content=result, status_code=500)

    @app.get("/health/version")
    async def health_version(client_api_version: str | None = None) -> dict[str, Any]:
        try:
            from ..core.config import API_CHANGELOG, MCP_API_VERSION, MCP_MIN_SUPPORTED_VERSION
            from .tools.server_health import _negotiate_api_version
            if client_api_version:
                negotiation = _negotiate_api_version(client_api_version)
                result = make_success_response(data=negotiation)
            else:
                result = make_success_response(data={
                    "server_version": MCP_API_VERSION,
                    "min_supported_version": MCP_MIN_SUPPORTED_VERSION,
                    "api_changelog": API_CHANGELOG,
                })
            return JSONResponse(content=result)
        except Exception as e:
            result = make_error_response(e)
            status = _error_response_to_http_status(result)
            return JSONResponse(content=result, status_code=status)

    @app.get("/knowledge/search")
    async def knowledge_search_get(query: str, top_k: int = 5, scope: str | None = None) -> dict[str, Any]:
        try:
            from ..core.search_engine import get_search_engine
            from .tools.knowledge_search import _ensure_knowledge_index
            _ensure_knowledge_index()
            engine = get_search_engine("hybrid")
            results = engine.search(query, top_k, {"scope": scope})
            items = [
                {
                    "source": r.source,
                    "content": r.content,
                    "match_type": r.match_type,
                    "relevance": r.relevance,
                }
                for r in results
            ]
            result = make_success_response(data={"results": items, "total": len(items)})
            return JSONResponse(content=result)
        except Exception as e:
            result = make_error_response(e)
            status = _error_response_to_http_status(result)
            return JSONResponse(content=result, status_code=status)

    @app.get("/config/status")
    async def config_status() -> dict[str, Any]:
        try:
            from .tools.config_manage import _get_config_status
            result = make_success_response(data=_get_config_status())
            return JSONResponse(content=result)
        except Exception as e:
            result = make_error_response(e)
            status = _error_response_to_http_status(result)
            return JSONResponse(content=result, status_code=status)

    @app.post("/config/reload")
    async def config_reload() -> dict[str, Any]:
        try:
            from ..core.config import reload_config
            reload_result = reload_config()
            result = make_success_response(data=reload_result)
            return JSONResponse(content=result)
        except Exception as e:
            result = make_error_response(e)
            status = _error_response_to_http_status(result)
            return JSONResponse(content=result, status_code=status)

    @app.get("/token-budget/status")
    async def token_budget_status() -> dict[str, Any]:
        try:
            from .tools.token_budget import _get_status
            result = make_success_response(data=_get_status())
            return JSONResponse(content=result)
        except Exception as e:
            result = make_error_response(e)
            status = _error_response_to_http_status(result)
            return JSONResponse(content=result, status_code=status)

    return app
