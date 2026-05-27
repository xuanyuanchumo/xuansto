import asyncio
import json
import logging
from datetime import datetime, timezone

from .config import mcp_available, make_response, make_error_response
from .security import InputValidator, SensitiveContentFilter

logger = logging.getLogger("knowledge-server")

if mcp_available:
    from mcp.server import Server
    from mcp.server.stdio import stdio_server
    from mcp.types import Tool, TextContent


def register_mcp_tools(server, mcp_server):
    if not mcp_server:
        return

    @mcp_server.list_tools()
    async def list_tools():
        return [
            Tool(
                name="knowledge_search",
                description="Search knowledge base entries with hybrid/semantic/keyword strategy",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "Search query text"},
                        "top_k": {"type": "integer", "description": "Max results to return", "default": 5},
                        "search_type": {"type": "string", "description": "Search strategy: hybrid, semantic_only, keyword_only", "default": "hybrid"},
                        "filters": {
                            "type": "object",
                            "description": "Optional filters",
                            "properties": {
                                "type": {"type": "array", "items": {"type": "string"}, "description": "Filter by entry types"},
                                "category": {"type": "array", "items": {"type": "string"}, "description": "Filter by categories"},
                                "tags": {"type": "array", "items": {"type": "string"}, "description": "Filter by tags"},
                                "min_confidence": {"type": "number", "description": "Minimum confidence threshold", "default": 0.0},
                            },
                        },
                    },
                    "required": ["query"],
                },
            ),
            Tool(
                name="knowledge_add",
                description="Add a new knowledge entry with dedup detection",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "content": {"type": "string", "description": "Knowledge content text"},
                        "metadata": {
                            "type": "object",
                            "description": "Entry metadata",
                            "properties": {
                                "id": {"type": "string", "description": "Optional custom entry ID"},
                                "type": {"type": "string", "description": "Entry type", "default": "unknown"},
                                "category": {"type": "string", "description": "Entry category", "default": "uncategorized"},
                                "tags": {"type": "array", "items": {"type": "string"}, "description": "Tags"},
                                "confidence": {"type": "number", "description": "Confidence score 0-1", "default": 0.6},
                                "source": {"type": "string", "description": "Source path"},
                            },
                        },
                        "auto_dedup": {"type": "boolean", "description": "Enable automatic dedup detection", "default": True},
                    },
                    "required": ["content"],
                },
            ),
            Tool(
                name="knowledge_update",
                description="Update an existing knowledge entry",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "id": {"type": "string", "description": "Entry ID to update"},
                        "content": {"type": "string", "description": "New content text"},
                        "metadata": {
                            "type": "object",
                            "description": "Updatable metadata fields",
                            "properties": {
                                "type": {"type": "string"},
                                "category": {"type": "string"},
                                "tags": {"type": "array", "items": {"type": "string"}},
                                "confidence": {"type": "number"},
                            },
                        },
                    },
                    "required": ["id"],
                },
            ),
            Tool(
                name="knowledge_delete",
                description="Delete a knowledge entry by ID",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "id": {"type": "string", "description": "Entry ID to delete"},
                    },
                    "required": ["id"],
                },
            ),
            Tool(
                name="knowledge_rollback",
                description="Roll back a knowledge entry to a specific version",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "id": {"type": "string", "description": "Entry ID to roll back"},
                        "target_version": {"type": "integer", "description": "Target version number to restore"},
                    },
                    "required": ["id", "target_version"],
                },
            ),
        ]

    @mcp_server.call_tool()
    async def call_tool(name: str, arguments: dict):
        if name == "knowledge_search":
            query = arguments.get("query", "")
            top_k = arguments.get("top_k", 5)
            search_type = arguments.get("search_type", "hybrid")
            filters = arguments.get("filters", {})
            min_confidence = filters.get("min_confidence", 0.0)
            tag_filters = filters.get("tags")
            type_filters = filters.get("type")
            category_filters = filters.get("category")
            effective_strategy = server.degradation.get_search_strategy()
            if search_type != "keyword_only" and effective_strategy != "hybrid":
                search_type = effective_strategy
            result = server.retrieval.search(
                query=query,
                top_k=top_k,
                strategy=search_type,
                min_confidence=min_confidence,
                tag_filters=tag_filters,
            )
            result["degradation_level"] = server.degradation.level
            result["degradation_name"] = server.degradation.level_name
            return [TextContent(type="text", text=json.dumps(make_response("ok", result), ensure_ascii=False))]

        elif name == "knowledge_add":
            content = arguments.get("content", "")
            metadata = arguments.get("metadata", {})
            auto_dedup = arguments.get("auto_dedup", True)
            has_sensitive, findings = SensitiveContentFilter.check(content)
            if has_sensitive:
                return [TextContent(type="text", text=json.dumps(make_error_response(
                    code="VALIDATION_ERROR",
                    message="Content contains sensitive information",
                    details={"findings": findings},
                ), ensure_ascii=False))]
            validation_errors = InputValidator.validate_all(content=content)
            if validation_errors:
                return [TextContent(type="text", text=json.dumps(make_error_response(
                    code="BAD_REQUEST",
                    message="Input validation failed",
                    details={"validation_errors": validation_errors},
                ), ensure_ascii=False))]
            entry_data = {
                "title": metadata.get("title", "") or metadata.get("id", ""),
                "content": content,
                "scope": "workspace",
                "tags": metadata.get("tags", []),
                "confidence": metadata.get("confidence", 0.6),
                "source_path": metadata.get("source"),
                "type": metadata.get("type", "unknown"),
                "category": metadata.get("category", "uncategorized"),
            }
            if auto_dedup:
                dedup_result = server.dedup.check_duplicate(entry_data)
                if dedup_result["action"] == "merge":
                    existing = server.sqlite.get_entry(dedup_result["existing_id"])
                    if existing:
                        merged = server.dedup.merge_entries(existing, entry_data)
                        server.sqlite.update_entry(existing["id"], merged)
                        if server.chroma.available:
                            try:
                                server.chroma.add_embedding(existing["id"], content, {"scope": "workspace", "title": merged.get("title", "")})
                                server.sqlite.update_embedding_status(existing["id"], "ready")
                            except Exception:
                                server.sqlite.update_embedding_status(existing["id"], "pending")
                        server.exporter.export_entry(existing["id"])
                        return [TextContent(type="text", text=json.dumps(make_response("ok", {
                            "id": existing["id"],
                            "status": "merged",
                            "dedup_status": "duplicate_merged",
                        }), ensure_ascii=False))]
                elif dedup_result["action"] == "skip":
                    return [TextContent(type="text", text=json.dumps(make_response("conflict", {
                        "id": dedup_result["existing_id"],
                        "status": "duplicate_rejected",
                        "dedup_status": "duplicate",
                        "similarity_score": dedup_result["similarity_score"],
                    }), ensure_ascii=False))]
            result = server.sqlite.add_entry(entry_data)
            if server.chroma.available:
                try:
                    server.chroma.add_embedding(result["id"], content, {"scope": "workspace", "title": entry_data.get("title", "")})
                    server.sqlite.update_embedding_status(result["id"], "ready")
                except Exception:
                    server.sqlite.update_embedding_status(result["id"], "pending")
            server.exporter.export_entry(result["id"])
            return [TextContent(type="text", text=json.dumps(make_response("ok", {
                "id": result["id"],
                "status": "created",
                "dedup_status": "new",
            }), ensure_ascii=False))]

        elif name == "knowledge_update":
            entry_id = arguments.get("id", "")
            content = arguments.get("content")
            metadata = arguments.get("metadata", {})
            updates = {}
            if content is not None:
                has_sensitive, findings = SensitiveContentFilter.check(content)
                if has_sensitive:
                    return [TextContent(type="text", text=json.dumps(make_error_response(
                        code="VALIDATION_ERROR",
                        message="Content contains sensitive information",
                        details={"findings": findings},
                    ), ensure_ascii=False))]
                updates["content"] = content
            if "type" in metadata:
                updates["type"] = metadata["type"]
            if "category" in metadata:
                updates["category"] = metadata["category"]
            if "tags" in metadata:
                updates["tags"] = metadata["tags"]
            if "confidence" in metadata:
                updates["confidence"] = metadata["confidence"]
            if not updates:
                return [TextContent(type="text", text=json.dumps(make_error_response(
                    code="BAD_REQUEST",
                    message="No update fields provided",
                ), ensure_ascii=False))]
            result = server.sqlite.update_entry(entry_id, updates)
            if result is None:
                return [TextContent(type="text", text=json.dumps(make_error_response(
                    code="NOT_FOUND",
                    message="Knowledge entry not found",
                    details={"entry_id": entry_id},
                ), ensure_ascii=False))]
            if isinstance(result, dict) and result.get("error") == "version_conflict":
                return [TextContent(type="text", text=json.dumps(make_error_response(
                    code="VERSION_CONFLICT",
                    message="Version conflict",
                    details={
                        "entry_id": entry_id,
                        "current_version": result["current_version"],
                        "expected_version": result["expected_version"],
                    },
                    retryable=True,
                ), ensure_ascii=False))]
            if server.chroma.available and content is not None:
                try:
                    server.chroma.add_embedding(entry_id, content, {"scope": result.get("scope", ""), "title": result.get("title", "")})
                    server.sqlite.update_embedding_status(entry_id, "ready")
                except Exception:
                    server.sqlite.update_embedding_status(entry_id, "pending")
            server.exporter.export_entry(entry_id)
            return [TextContent(type="text", text=json.dumps(make_response("ok", {
                "id": entry_id,
                "status": "updated",
            }), ensure_ascii=False))]

        elif name == "knowledge_delete":
            entry_id = arguments.get("id", "")
            result = server.mcp_knowledge_delete(entry_id)
            return [TextContent(type="text", text=json.dumps(result, ensure_ascii=False))]

        elif name == "knowledge_rollback":
            entry_id = arguments.get("id", "")
            target_version = arguments.get("target_version", 1)
            result = server.mcp_knowledge_rollback_version(entry_id, target_version)
            return [TextContent(type="text", text=json.dumps(result, ensure_ascii=False))]

        return [TextContent(type="text", text=json.dumps(make_error_response(
            code="UNKNOWN_TOOL",
            message=f"Unknown tool: {name}",
        ), ensure_ascii=False))]


async def run_mcp_server(server):
    if not server._mcp_server:
        return
    async with stdio_server() as (read_stream, write_stream):
        await server._mcp_server.run(read_stream, write_stream, server._mcp_server.create_initialization_options())
