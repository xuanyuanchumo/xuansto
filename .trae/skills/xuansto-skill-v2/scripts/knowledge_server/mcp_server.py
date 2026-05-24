import asyncio
import json
import logging
from datetime import datetime, timezone

from .config import mcp_available, make_response, make_error_response
from .security import InputValidator, SensitiveContentFilter
from .progressive_loader import LoadPhase, ProgressiveLoader
from .skill_tools import get_skill_tool_definitions, SkillToolHandler, SKILL_TOOL_NAMES

logger = logging.getLogger("knowledge-server")

MCP_JSON_SCHEMA_URI = "https://json-schema.org/draft/2020-12/schema"

MCP_ERROR_CODES = {
    "PARSE_ERROR": -32700,
    "INVALID_REQUEST": -32600,
    "METHOD_NOT_FOUND": -32601,
    "INVALID_PARAMS": -32602,
    "INTERNAL_ERROR": -32603,
}

APP_ERROR_CODES = {
    "VALIDATION_ERROR": -32100,
    "BAD_REQUEST": -32101,
    "NOT_FOUND": -32102,
    "VERSION_CONFLICT": -32103,
    "DUPLICATE_DETECTED": -32104,
    "UNKNOWN_TOOL": -32105,
    "SENSITIVE_CONTENT": -32106,
}

if mcp_available:
    from mcp.server import Server
    from mcp.server.stdio import stdio_server
    from mcp.types import Tool, TextContent, ToolAnnotations


def register_mcp_tools(server, mcp_server):
    if not mcp_server:
        return

    _status_pushed = False
    _skill_handler = SkillToolHandler(server=server)

    @mcp_server.list_tools()
    async def list_tools():
        knowledge_tools = [
            Tool(
                name="knowledge_search",
                description=(
                    "[Read-Only] [Idempotent] Search the knowledge base for entries matching a query.\n\n"
                    "Use this tool when you need to find coding standards, best practices, design patterns, "
                    "error solutions, or technical documentation stored in the knowledge base. "
                    "Supports three search strategies: hybrid (default, combines semantic + keyword), "
                    "semantic_only (meaning-based, requires embeddings), and keyword_only (text matching, always available).\n\n"
                    "Parameters:\n"
                    "- query (string, required): The search text. Use natural language for semantic search, keywords for keyword search.\n"
                    "- top_k (integer, default=5, range 1-50): Maximum number of results to return.\n"
                    "- search_type (string, default='hybrid', enum: hybrid|semantic_only|keyword_only): Search strategy. "
                    "'hybrid' blends semantic and keyword results; 'semantic_only' uses vector similarity (degrades to keyword if embeddings unavailable); "
                    "'keyword_only' uses FTS5 full-text search.\n"
                    "- filters (object, optional): Narrow results by type (array of strings), category (array of strings), "
                    "tags (array of strings), or min_confidence (number 0-1, default 0.0).\n\n"
                    "Returns an object with:\n"
                    "- results: Array of matched entries, each containing id, type, category, title, content (truncated), "
                    "confidence (0-1), scope (general|workspace|experience), and tags.\n"
                    "- total: Total number of matched entries.\n"
                    "- search_strategy: The effective strategy used (may differ from requested if degraded).\n"
                    "- degradation_level/name: Engine health indicator (0=full, 1=keyword-only, 2=unavailable).\n\n"
                    "Example: Search for React error patterns with high confidence:\n"
                    '{"query": "React useEffect cleanup memory leak", "top_k": 3, "search_type": "hybrid", '
                    '"filters": {"type": ["error-solution"], "min_confidence": 0.7}}'
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "Search query text"},
                        "top_k": {"type": "integer", "description": "Max results to return", "default": 5},
                        "search_type": {"type": "string", "description": "Search strategy: hybrid, semantic_only, keyword_only", "default": "hybrid", "enum": ["hybrid", "semantic_only", "keyword_only"]},
                        "filters": {
                            "type": "object",
                            "description": "Optional filters",
                            "properties": {
                                "type": {"type": "array", "items": {"type": "string"}, "description": "Filter by entry types"},
                                "category": {"type": "array", "items": {"type": "string"}, "description": "Filter by categories"},
                                "tags": {"type": "array", "items": {"type": "string"}, "description": "Filter by tags"},
                                "min_confidence": {"type": "number", "description": "Minimum confidence threshold", "default": 0.0, "minimum": 0, "maximum": 1},
                            },
                        },
                    },
                    "required": ["query"],
                    "additionalProperties": False,
                    "$schema": MCP_JSON_SCHEMA_URI,
                },
                outputSchema={
                    "type": "object",
                    "properties": {
                        "results": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "id": {"type": "string"},
                                    "type": {"type": "string"},
                                    "category": {"type": "string"},
                                    "title": {"type": "string"},
                                    "content": {"type": "string"},
                                    "confidence": {"type": "number"},
                                    "scope": {"type": "string"},
                                    "tags": {"type": "array", "items": {"type": "string"}},
                                },
                            },
                        },
                        "total": {"type": "integer"},
                        "search_strategy": {"type": "string"},
                        "degradation_level": {"type": "integer"},
                        "degradation_name": {"type": "string"},
                    },
                },
                annotations=ToolAnnotations(readOnlyHint=True, destructiveHint=False, idempotentHint=True, openWorldHint=False),
            ),
            Tool(
                name="knowledge_add",
                description=(
                    "Add a new knowledge entry to the knowledge base with automatic dedup detection.\n\n"
                    "Use this tool when you need to persist new coding standards, error solutions, project experience, "
                    "or technical insights into the knowledge base for future retrieval. "
                    "When auto_dedup is enabled (default), the system checks for similar existing entries and either "
                    "merges, rejects, or creates a new entry based on similarity score.\n\n"
                    "Parameters:\n"
                    "- content (string, required): The knowledge content text. Must not contain sensitive information (API keys, passwords, etc.).\n"
                    "- metadata (object, optional): Entry metadata including:\n"
                    "  - id (string, optional): Custom entry ID. Auto-generated if omitted.\n"
                    "  - type (string, default='unknown'): Entry type (e.g., standard, pattern, error-solution, glossary).\n"
                    "  - category (string, default='uncategorized'): Entry category (e.g., security, database, testing).\n"
                    "  - tags (array of strings, optional): Tags for categorization and filtering.\n"
                    "  - confidence (number, default=0.6, range 0-1): Confidence score reflecting source reliability.\n"
                    "  - source (string, optional): Source file path or URL.\n"
                    "- auto_dedup (boolean, default=true): Enable automatic duplicate detection. If a similar entry exists, "
                    "it will be merged or rejected based on similarity threshold.\n\n"
                    "Returns an object with:\n"
                    "- id: The entry ID (new or existing if merged).\n"
                    "- status: 'created' for new entries, 'merged' when merged into existing.\n"
                    "- dedup_status: 'new' (no duplicate), 'duplicate_merged' (merged into existing), 'duplicate_rejected' (skipped).\n"
                    "- similarity_score: Present when dedup detected a duplicate (0-1).\n\n"
                    "Example: Add a Python async best practice:\n"
                    '{"content": "Always use asyncio.gather() for concurrent I/O instead of sequential awaits...", '
                    '"metadata": {"type": "standard", "category": "async", "tags": ["python", "asyncio"], "confidence": 0.9}, '
                    '"auto_dedup": true}'
                ),
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
                                "confidence": {"type": "number", "description": "Confidence score 0-1", "default": 0.6, "minimum": 0, "maximum": 1},
                                "source": {"type": "string", "description": "Source path"},
                            },
                        },
                        "auto_dedup": {"type": "boolean", "description": "Enable automatic dedup detection", "default": True},
                    },
                    "required": ["content"],
                    "additionalProperties": False,
                    "$schema": MCP_JSON_SCHEMA_URI,
                },
                outputSchema={
                    "type": "object",
                    "properties": {
                        "id": {"type": "string"},
                        "status": {"type": "string", "enum": ["created", "merged"]},
                        "dedup_status": {"type": "string", "enum": ["new", "duplicate_merged", "duplicate_rejected"]},
                        "similarity_score": {"type": "number"},
                    },
                },
                annotations=ToolAnnotations(readOnlyHint=False, destructiveHint=False, idempotentHint=False, openWorldHint=False),
            ),
            Tool(
                name="knowledge_update",
                description=(
                    "Update an existing knowledge entry's content and/or metadata.\n\n"
                    "Use this tool when you need to correct or supplement existing knowledge content, update confidence scores, "
                    "add new tags, or change the entry type/category. Supports optimistic locking via version control — "
                    "if the entry was modified concurrently, a VERSION_CONFLICT error is returned.\n\n"
                    "Parameters:\n"
                    "- id (string, required): The unique entry ID to update.\n"
                    "- content (string, optional): New content text. If provided, sensitive content check is applied. "
                    "Triggers embedding re-indexing when ChromaDB is available.\n"
                    "- metadata (object, optional): Updatable metadata fields:\n"
                    "  - type (string, optional): New entry type.\n"
                    "  - category (string, optional): New entry category.\n"
                    "  - tags (array of strings, optional): Replace tags entirely.\n"
                    "  - confidence (number, optional, range 0-1): New confidence score.\n"
                    "At least one of 'content' or 'metadata' must be provided.\n\n"
                    "Returns an object with:\n"
                    "- id: The updated entry ID.\n"
                    "- status: 'updated' on success.\n\n"
                    "Error codes: NOT_FOUND (entry does not exist), VERSION_CONFLICT (concurrent modification), "
                    "SENSITIVE_CONTENT (content contains secrets), BAD_REQUEST (no fields to update).\n\n"
                    "Example: Update confidence and add a tag:\n"
                    '{"id": "entry-abc123", "metadata": {"confidence": 0.95, "tags": ["python", "verified"]}}'
                ),
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
                                "confidence": {"type": "number", "minimum": 0, "maximum": 1},
                            },
                        },
                    },
                    "required": ["id"],
                    "additionalProperties": False,
                    "$schema": MCP_JSON_SCHEMA_URI,
                },
                outputSchema={
                    "type": "object",
                    "properties": {
                        "id": {"type": "string"},
                        "status": {"type": "string", "enum": ["updated"]},
                    },
                },
                annotations=ToolAnnotations(readOnlyHint=False, destructiveHint=False, idempotentHint=False, openWorldHint=False),
            ),
            Tool(
                name="knowledge_delete",
                description=(
                    "[Destructive] Delete a knowledge entry from the knowledge base by ID.\n\n"
                    "Use this tool when a knowledge entry is outdated, incorrect, or no longer needed. "
                    "This operation is IRREVERSIBLE — the entry and its version history are permanently removed. "
                    "Consider using knowledge_update to correct content instead of deleting.\n\n"
                    "Parameters:\n"
                    "- id (string, required): The unique entry ID to delete.\n\n"
                    "Returns an object with:\n"
                    "- id: The deleted entry ID.\n"
                    "- status: 'deleted' on success.\n\n"
                    "Error codes: NOT_FOUND (entry does not exist).\n\n"
                    "Example: Delete an outdated entry:\n"
                    '{"id": "entry-deprecated-456"}'
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "id": {"type": "string", "description": "Entry ID to delete"},
                    },
                    "required": ["id"],
                    "additionalProperties": False,
                    "$schema": MCP_JSON_SCHEMA_URI,
                },
                outputSchema={
                    "type": "object",
                    "properties": {
                        "id": {"type": "string"},
                        "status": {"type": "string", "enum": ["deleted"]},
                    },
                },
                annotations=ToolAnnotations(readOnlyHint=False, destructiveHint=True, idempotentHint=False, openWorldHint=False),
            ),
            Tool(
                name="knowledge_stats",
                description=(
                    "[Read-Only] [Idempotent] Get knowledge base statistics including entry counts, embedding status, and engine health.\n\n"
                    "Use this tool when you need an overview of the knowledge base: total entry count, "
                    "distribution by scope/type/category, embedding readiness, ChromaDB vector count, "
                    "and current degradation level. Useful for monitoring and diagnostics.\n\n"
                    "Parameters:\n"
                    "- detailed (boolean, default=false): When true, includes per-type and per-category breakdowns "
                    "in addition to the default per-scope counts.\n"
                    "- since (string, optional): ISO 8601 timestamp. When provided, the response includes "
                    "status_changed_since_last_check (boolean) indicating whether the knowledge base has changed "
                    "since this timestamp. Use the last_change_timestamp from a previous response as the since value.\n\n"
                    "Returns an object with:\n"
                    "- total_entries: Total number of active knowledge entries.\n"
                    "- by_scope: Entry counts grouped by scope (general, workspace, experience).\n"
                    "- embedding: Object with 'pending' and 'ready' counts for embedding status.\n"
                    "- chroma_available: Whether ChromaDB vector store is connected.\n"
                    "- chroma_vector_count: Number of vectors in ChromaDB (0 if unavailable).\n"
                    "- degradation_level/name: Engine health (0=full, 1=keyword-only, 2=unavailable).\n"
                    "- embedding_level/name: Embedding tier (0=OpenAI, 1=sentence-transformers, 2=unavailable).\n"
                    "- last_change_timestamp: ISO 8601 timestamp of the last knowledge base modification.\n"
                    "- status_changed_since_last_check (only if since provided): Whether KB changed since the given timestamp.\n"
                    "- by_type (only if detailed=true): Entry counts grouped by type.\n"
                    "- by_category (only if detailed=true): Entry counts grouped by category.\n\n"
                    "Example: Get detailed statistics with change detection:\n"
                    '{"detailed": true, "since": "2025-01-15T10:30:00+00:00"}'
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "detailed": {"type": "boolean", "description": "Include per-scope and per-type breakdowns", "default": False},
                        "since": {"type": "string", "description": "ISO 8601 timestamp to check for changes since"},
                    },
                    "additionalProperties": False,
                    "$schema": MCP_JSON_SCHEMA_URI,
                },
                outputSchema={
                    "type": "object",
                    "properties": {
                        "total_entries": {"type": "integer"},
                        "by_scope": {"type": "object"},
                        "embedding": {"type": "object"},
                        "chroma_available": {"type": "boolean"},
                        "chroma_vector_count": {"type": "integer"},
                        "degradation_level": {"type": "integer"},
                        "degradation_name": {"type": "string"},
                        "embedding_level": {"type": "integer"},
                        "embedding_level_name": {"type": "string"},
                        "last_change_timestamp": {"type": "string"},
                        "status_changed_since_last_check": {"type": "boolean"},
                        "by_type": {"type": "object"},
                        "by_category": {"type": "object"},
                    },
                },
                annotations=ToolAnnotations(readOnlyHint=True, destructiveHint=False, idempotentHint=True, openWorldHint=False),
            ),
            Tool(
                name="knowledge_rollback",
                description=(
                    "[Destructive] [Idempotent] Roll back a knowledge entry to a specific previous version.\n\n"
                    "Use this tool when a knowledge update introduced errors or incorrect information and you need to "
                    "restore a previous known-good version. This operation OVERWRITES the current version — "
                    "the current state is saved to version history before rollback, so it can still be recovered.\n\n"
                    "Parameters:\n"
                    "- id (string, required): The unique entry ID to roll back.\n"
                    "- target_version (integer, required, minimum=1): The version number to restore. "
                    "Check version history to find the desired version number.\n\n"
                    "Returns an object with:\n"
                    "- id: The entry ID that was rolled back.\n"
                    "- status: 'rolled_back' on success.\n"
                    "- target_version: The version number that was restored.\n"
                    "- current_version: The new current version number (incremented from rollback).\n\n"
                    "Error codes: NOT_FOUND (entry does not exist), INVALID_PARAMS (target_version out of range).\n\n"
                    "Example: Roll back entry to version 3:\n"
                    '{"id": "entry-abc123", "target_version": 3}'
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "id": {"type": "string", "description": "Entry ID to roll back"},
                        "target_version": {"type": "integer", "description": "Target version number to restore", "minimum": 1},
                    },
                    "required": ["id", "target_version"],
                    "additionalProperties": False,
                    "$schema": MCP_JSON_SCHEMA_URI,
                },
                outputSchema={
                    "type": "object",
                    "properties": {
                        "id": {"type": "string"},
                        "status": {"type": "string", "enum": ["rolled_back"]},
                        "target_version": {"type": "integer"},
                        "current_version": {"type": "integer"},
                    },
                },
                annotations=ToolAnnotations(readOnlyHint=False, destructiveHint=True, idempotentHint=True, openWorldHint=False),
            ),
            Tool(
                name="knowledge_auto_retrieve",
                description=(
                    "[Read-Only] [Idempotent] Automatically retrieve knowledge context based on task type and project tech stack.\n\n"
                    "Use this tool when starting a new development task (bug fix, feature implementation, code review, "
                    "deployment, security audit) to automatically inject relevant knowledge context. "
                    "It detects the project's technology stack from the filesystem and tailors search queries "
                    "to the task type, returning a pre-formatted context string ready for injection into prompts.\n\n"
                    "Parameters:\n"
                    "- task_type (string, default='feature', enum: bug_fix|feature|refactor|review|deploy|security): "
                    "The type of development task. Determines the search strategy and query formulation.\n"
                    "- project_path (string, required): Absolute path to the project root directory. "
                    "Used to auto-detect the tech stack (package.json, requirements.txt, Cargo.toml, etc.).\n"
                    "- query (string, optional): Override the auto-generated search query. Defaults to task_type-based query.\n"
                    "- token_budget (integer, default=2048, range 256-8192): Maximum token budget for the formatted context output.\n\n"
                    "Returns an object with:\n"
                    "- context: Pre-formatted knowledge context string ready for prompt injection.\n"
                    "- tech_stack: Detected technology stack object (languages, frameworks, runtimes).\n"
                    "- task_type: The effective task type used.\n"
                    "- query_used: The actual search query executed.\n"
                    "- results_count: Number of knowledge entries included in the context.\n"
                    "- degradation_level/name: Engine health indicator.\n\n"
                    "Example: Retrieve context for a bug fix in a Python project:\n"
                    '{"task_type": "bug_fix", "project_path": "/home/user/my-fastapi-app", "token_budget": 4096}'
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "task_type": {"type": "string", "description": "Task type: bug_fix, feature, refactor, review, deploy, security", "default": "feature", "enum": ["bug_fix", "feature", "refactor", "review", "deploy", "security"]},
                        "project_path": {"type": "string", "description": "Absolute path to the project root directory"},
                        "query": {"type": "string", "description": "Optional search query override (defaults to task_type)"},
                        "token_budget": {"type": "integer", "description": "Maximum token budget for formatted context", "default": 2048, "minimum": 256, "maximum": 8192},
                    },
                    "required": ["project_path"],
                    "additionalProperties": False,
                    "$schema": MCP_JSON_SCHEMA_URI,
                },
                outputSchema={
                    "type": "object",
                    "properties": {
                        "context": {"type": "string"},
                        "tech_stack": {"type": "object"},
                        "task_type": {"type": "string"},
                        "query_used": {"type": "string"},
                        "results_count": {"type": "integer"},
                        "degradation_level": {"type": "integer"},
                        "degradation_name": {"type": "string"},
                    },
                },
                annotations=ToolAnnotations(readOnlyHint=True, destructiveHint=False, idempotentHint=True, openWorldHint=False),
            ),
            Tool(
                name="knowledge_progressive_search",
                description=(
                    "[Read-Only] [Idempotent] Progressive multi-round knowledge retrieval with task-type-aware search strategy and token budget control.\n\n"
                    "Use this tool when you need smarter, deeper retrieval than knowledge_search provides. "
                    "It searches across multiple scope levels (workspace > experience > general) in priority order, "
                    "adjusts search depth based on task type, and prunes results to fit within a token budget. "
                    "Slower than knowledge_search but more comprehensive and context-aware.\n\n"
                    "Parameters:\n"
                    "- query (string, required): The search query text.\n"
                    "- task_type (string, default='feature', enum: bug_fix|feature|refactor|review|deploy|security): "
                    "Determines search strategy — e.g., 'bug_fix' prioritizes error-solution entries, "
                    "'security' prioritizes high-confidence standards.\n"
                    "- tech_stack (object, optional): Technology stack for filtering:\n"
                    "  - languages (array of strings): Programming languages (e.g., ['python', 'typescript']).\n"
                    "  - frameworks (array of strings): Frameworks and libraries (e.g., ['react', 'fastapi']).\n"
                    "  - runtimes (array of strings): Runtime environments (e.g., ['node', 'docker']).\n"
                    "- token_budget (integer, default=2048, range 256-8192): Maximum token budget for results. "
                    "Entries are truncated or pruned to fit.\n\n"
                    "Returns an object with:\n"
                    "- results: Array of matched entries with id, title, content (may be truncated), scope, confidence, tags, and _truncated flag.\n"
                    "- total: Total matched entries before pruning.\n"
                    "- task_type: The task type used for search strategy.\n"
                    "- search_config: The resolved search configuration object.\n"
                    "- token_budget: The effective token budget used.\n"
                    "- pruned_entry_ids: IDs of entries removed due to budget constraints.\n"
                    "- degradation_level/name: Engine health indicator.\n\n"
                    "Example: Progressive search for a security audit:\n"
                    '{"query": "SQL injection prevention", "task_type": "security", '
                    '"tech_stack": {"languages": ["python"], "frameworks": ["django"]}, "token_budget": 4096}'
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "Search query text"},
                        "task_type": {"type": "string", "description": "Task type determining search strategy", "default": "feature", "enum": ["bug_fix", "feature", "refactor", "review", "deploy", "security"]},
                        "tech_stack": {
                            "type": "object",
                            "description": "Technology stack for filtering",
                            "properties": {
                                "languages": {"type": "array", "items": {"type": "string"}, "description": "Programming languages"},
                                "frameworks": {"type": "array", "items": {"type": "string"}, "description": "Frameworks and libraries"},
                                "runtimes": {"type": "array", "items": {"type": "string"}, "description": "Runtime environments"},
                            },
                        },
                        "token_budget": {"type": "integer", "description": "Maximum token budget for results", "default": 2048, "minimum": 256, "maximum": 8192},
                    },
                    "required": ["query"],
                    "additionalProperties": False,
                    "$schema": MCP_JSON_SCHEMA_URI,
                },
                outputSchema={
                    "type": "object",
                    "properties": {
                        "results": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "id": {"type": "string"},
                                    "title": {"type": "string"},
                                    "content": {"type": "string"},
                                    "scope": {"type": "string"},
                                    "confidence": {"type": "number"},
                                    "tags": {"type": "array", "items": {"type": "string"}},
                                    "_truncated": {"type": "boolean"},
                                },
                            },
                        },
                        "total": {"type": "integer"},
                        "task_type": {"type": "string"},
                        "search_config": {"type": "object"},
                        "token_budget": {"type": "integer"},
                        "pruned_entry_ids": {"type": "array", "items": {"type": "string"}},
                        "degradation_level": {"type": "integer"},
                        "degradation_name": {"type": "string"},
                    },
                },
                annotations=ToolAnnotations(readOnlyHint=True, destructiveHint=False, idempotentHint=True, openWorldHint=False),
            ),
            Tool(
                name="knowledge_deep_load",
                description=(
                    "[Read-Only] [Idempotent] Load the full content of a specific knowledge entry by ID, bypassing daily token budget limits.\n\n"
                    "Use this tool when knowledge_search or knowledge_auto_retrieve returned a truncated or summary result "
                    "and you need the complete entry content for detailed analysis. Unlike search tools, this returns "
                    "the full untruncated content regardless of token budget constraints.\n\n"
                    "Parameters:\n"
                    "- entry_id (string, required): The unique entry ID to load. Obtain this from search results or auto_retrieve output.\n\n"
                    "Returns an object with:\n"
                    "- id: The entry ID.\n"
                    "- title: The entry title.\n"
                    "- content: The full, untruncated knowledge content.\n"
                    "- scope: Entry scope (general, workspace, experience).\n"
                    "- confidence: Confidence score (0-1).\n"
                    "- tags: Array of tags.\n"
                    "- type: Entry type (standard, pattern, error-solution, glossary, etc.).\n"
                    "- category: Entry category.\n\n"
                    "Error codes: NOT_FOUND (entry does not exist).\n\n"
                    "Example: Load full content of a search result:\n"
                    '{"entry_id": "entry-abc123"}'
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "entry_id": {"type": "string", "description": "Entry ID to load"},
                    },
                    "required": ["entry_id"],
                    "additionalProperties": False,
                    "$schema": MCP_JSON_SCHEMA_URI,
                },
                outputSchema={
                    "type": "object",
                    "properties": {
                        "id": {"type": "string"},
                        "title": {"type": "string"},
                        "content": {"type": "string"},
                        "scope": {"type": "string"},
                        "confidence": {"type": "number"},
                        "tags": {"type": "array", "items": {"type": "string"}},
                        "type": {"type": "string"},
                        "category": {"type": "string"},
                    },
                },
                annotations=ToolAnnotations(readOnlyHint=True, destructiveHint=False, idempotentHint=True, openWorldHint=False),
            ),
            Tool(
                name="knowledge_web_update",
                description=(
                    "[Open-World] Search official documentation from the web and update the knowledge base.\n\n"
                    "Use this tool when knowledge entries are outdated and need refreshing with the latest official docs, "
                    "or when a project introduces new technology and you need to ingest reference knowledge. "
                    "This tool accesses external network resources to search, extract, and structure documentation. "
                    "If an entry_id is provided, the existing entry is updated; otherwise a new entry is created with "
                    "a lower confidence score pending review.\n\n"
                    "Parameters:\n"
                    "- entry_id (string, optional): ID of an existing entry to update with fresh documentation. "
                    "If provided, the entry's title, category, and tags are used to formulate the search query.\n"
                    "- category (string, optional): Technology category to search for (e.g., 'react', 'fastapi', 'rust'). "
                    "Used as the search query when entry_id is not provided.\n"
                    "- tags (array of strings, optional): Tags to refine the search query and filter results.\n"
                    "At least one of entry_id, category, or tags must be provided.\n\n"
                    "Returns an object with:\n"
                    "- id: The entry ID (updated or newly created).\n"
                    "- status: 'updated' (existing entry refreshed), 'created_pending_review' (new entry created), "
                    "'no_change' (search found nothing new), 'no_results' (web search returned nothing), "
                    "or 'extraction_failed' (could not parse results).\n"
                    "- sources_found: Number of web sources found.\n"
                    "- best_source_rating: Highest source rating among results (1-5).\n"
                    "- updated_fields: List of fields that were updated (only when status='updated').\n\n"
                    "Example: Update a React hooks entry from official docs:\n"
                    '{"entry_id": "entry-react-hooks-123"}'
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "entry_id": {"type": "string", "description": "Existing entry ID to update with fresh docs"},
                        "category": {"type": "string", "description": "Technology category to search for (e.g., react, fastapi)"},
                        "tags": {"type": "array", "items": {"type": "string"}, "description": "Tags to refine search query"},
                    },
                    "additionalProperties": False,
                    "$schema": MCP_JSON_SCHEMA_URI,
                },
                outputSchema={
                    "type": "object",
                    "properties": {
                        "id": {"type": "string"},
                        "status": {"type": "string", "enum": ["updated", "created_pending_review", "no_change", "no_results", "extraction_failed"]},
                        "sources_found": {"type": "integer"},
                        "best_source_rating": {"type": "integer"},
                        "updated_fields": {"type": "array", "items": {"type": "string"}},
                    },
                },
                annotations=ToolAnnotations(readOnlyHint=False, destructiveHint=False, idempotentHint=False, openWorldHint=True),
            ),
            Tool(
                name="resource_load_status",
                description=(
                    "[Read-Only/Stateful] Query and control the progressive loading disclosure state.\n\n"
                    "Use this tool to check which resources are currently loaded, preload resources for a target phase, "
                    "query cache state, clear cache (degrades to SKELETON), or check loading progress. "
                    "The progressive loading system controls which skill resources are available at any time, "
                    "advancing through SKELETON→FUNCTIONAL→ENHANCED→FULL phases and degrading when token budgets are tight.\n\n"
                    "Parameters:\n"
                    "- action (string, required, enum: status|preload|cache|clear_cache|loading_progress): The operation to perform.\n"
                    "  - status: Return current loading state including phase, loaded resources, and disclosure note.\n"
                    "  - preload: Advance to the specified target phase, loading all resources for that phase.\n"
                    "  - cache: Query the current cache state of loaded resources.\n"
                    "  - clear_cache: Clear all cached resources and degrade to SKELETON phase.\n"
                    "  - loading_progress: Query the loading progress of each resource.\n"
                    "- target_phase (string, optional, enum: skeleton|functional|enhanced|full): Target phase for preload action.\n"
                    "- resource_ids (array of strings, optional): Specific resource IDs to check (for cache/loading_progress actions).\n\n"
                    "Returns an object with:\n"
                    "- action: The action performed.\n"
                    "- current_phase: The current loading phase name.\n"
                    "- phase_index: The numeric phase index (0-3).\n"
                    "- loaded_resources: List of currently loaded resource IDs.\n"
                    "- loaded_count: Number of loaded resources.\n"
                    "- available_resources: List of resources available in current phase.\n"
                    "- available_commands: List of commands available in current phase.\n"
                    "- disclosure_note: Human-readable note about current availability (Chinese).\n"
                    "- upgrade_hint: Hint about how to advance to the next phase (Chinese).\n"
                    "- progress: Per-resource loading progress (for loading_progress action).\n"
                    "- timestamp: ISO 8601 timestamp of the response.\n\n"
                    "Example: Check current loading status:\n"
                    '{"action": "status"}\n\n'
                    "Example: Preload to enhanced phase:\n"
                    '{"action": "preload", "target_phase": "enhanced"}'
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "action": {"type": "string", "description": "Operation: status, preload, cache, clear_cache, loading_progress", "enum": ["status", "preload", "cache", "clear_cache", "loading_progress"]},
                        "target_phase": {"type": "string", "description": "Target phase for preload: skeleton, functional, enhanced, full", "enum": ["skeleton", "functional", "enhanced", "full"]},
                        "resource_ids": {"type": "array", "items": {"type": "string"}, "description": "Specific resource IDs to check"},
                    },
                    "required": ["action"],
                    "additionalProperties": False,
                    "$schema": MCP_JSON_SCHEMA_URI,
                },
                outputSchema={
                    "type": "object",
                    "properties": {
                        "action": {"type": "string"},
                        "current_phase": {"type": "string"},
                        "phase_index": {"type": "integer"},
                        "loaded_resources": {"type": "array", "items": {"type": "string"}},
                        "loaded_count": {"type": "integer"},
                        "available_resources": {"type": "array", "items": {"type": "string"}},
                        "available_commands": {"type": "array", "items": {"type": "string"}},
                        "disclosure_note": {"type": "string"},
                        "upgrade_hint": {"type": "string"},
                        "progress": {"type": "object"},
                        "timestamp": {"type": "string"},
                    },
                },
                annotations=ToolAnnotations(readOnlyHint=False, destructiveHint=False, idempotentHint=False, openWorldHint=False),
            ),
        ]
        return knowledge_tools + get_skill_tool_definitions()

    @mcp_server.call_tool()
    async def call_tool(name: str, arguments: dict):
        nonlocal _status_pushed
        if not _status_pushed:
            _status_pushed = True
            try:
                summary = server.get_status_summary()
                logger.info(
                    "operation=mcp_status_push, total_entries=%d, embedding_status=%s, last_updated=%s",
                    summary["total_entries"],
                    summary["embedding_status"],
                    summary["last_updated"],
                )
            except Exception as e:
                logger.warning("operation=mcp_status_push, error=%s", e)

        try:
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
                    type_filters=type_filters,
                    category_filters=category_filters,
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
                        code="SENSITIVE_CONTENT",
                        message="Content contains sensitive information",
                        details={"findings": findings, "mcp_error_code": APP_ERROR_CODES["SENSITIVE_CONTENT"]},
                    ), ensure_ascii=False), isError=True)]
                validation_errors = InputValidator.validate_all(content=content)
                if validation_errors:
                    return [TextContent(type="text", text=json.dumps(make_error_response(
                        code="BAD_REQUEST",
                        message="Input validation failed",
                        details={"validation_errors": validation_errors, "mcp_error_code": APP_ERROR_CODES["BAD_REQUEST"]},
                    ), ensure_ascii=False), isError=True)]
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
                            server._touch_change()
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
                server._touch_change()
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
                            code="SENSITIVE_CONTENT",
                            message="Content contains sensitive information",
                            details={"findings": findings, "mcp_error_code": APP_ERROR_CODES["SENSITIVE_CONTENT"]},
                        ), ensure_ascii=False), isError=True)]
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
                        details={"mcp_error_code": APP_ERROR_CODES["BAD_REQUEST"]},
                    ), ensure_ascii=False), isError=True)]
                result = server.sqlite.update_entry(entry_id, updates)
                if result is None:
                    return [TextContent(type="text", text=json.dumps(make_error_response(
                        code="NOT_FOUND",
                        message="Knowledge entry not found",
                        details={"entry_id": entry_id, "mcp_error_code": APP_ERROR_CODES["NOT_FOUND"]},
                    ), ensure_ascii=False), isError=True)]
                if isinstance(result, dict) and result.get("error") == "version_conflict":
                    return [TextContent(type="text", text=json.dumps(make_error_response(
                        code="VERSION_CONFLICT",
                        message="Version conflict",
                        details={
                            "entry_id": entry_id,
                            "current_version": result["current_version"],
                            "expected_version": result["expected_version"],
                            "mcp_error_code": APP_ERROR_CODES["VERSION_CONFLICT"],
                        },
                        retryable=True,
                    ), ensure_ascii=False), isError=True)]
                if server.chroma.available and content is not None:
                    try:
                        server.chroma.add_embedding(entry_id, content, {"scope": result.get("scope", ""), "title": result.get("title", "")})
                        server.sqlite.update_embedding_status(entry_id, "ready")
                    except Exception:
                        server.sqlite.update_embedding_status(entry_id, "pending")
                server.exporter.export_entry(entry_id)
                server._touch_change()
                return [TextContent(type="text", text=json.dumps(make_response("ok", {
                    "id": entry_id,
                    "status": "updated",
                }), ensure_ascii=False))]
    
            elif name == "knowledge_delete":
                entry_id = arguments.get("id", "")
                result = server.mcp_knowledge_delete(entry_id)
                return [TextContent(type="text", text=json.dumps(result, ensure_ascii=False))]
    
            elif name == "knowledge_stats":
                detailed = arguments.get("detailed", False)
                since = arguments.get("since")
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
                if since:
                    try:
                        since_dt = datetime.fromisoformat(since.replace("Z", "+00:00"))
                        last_dt = datetime.fromisoformat(server._last_change_timestamp.replace("Z", "+00:00"))
                        stats["status_changed_since_last_check"] = last_dt > since_dt
                    except (ValueError, TypeError):
                        stats["status_changed_since_last_check"] = None
                if detailed:
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
                return [TextContent(type="text", text=json.dumps(make_response("ok", stats), ensure_ascii=False))]
    
            elif name == "knowledge_rollback":
                entry_id = arguments.get("id", "")
                target_version = arguments.get("target_version", 1)
                result = server.mcp_knowledge_rollback_version(entry_id, target_version)
                return [TextContent(type="text", text=json.dumps(result, ensure_ascii=False))]
    
            elif name == "knowledge_progressive_search":
                query = arguments.get("query", "")
                task_type = arguments.get("task_type", "feature")
                tech_stack = arguments.get("tech_stack", {})
                token_budget = arguments.get("token_budget", 2048)
                result = server.mcp_knowledge_progressive_search(
                    query=query,
                    task_type=task_type,
                    tech_stack=tech_stack,
                    token_budget=token_budget,
                )
                return [TextContent(type="text", text=json.dumps(result, ensure_ascii=False))]
    
            elif name == "knowledge_deep_load":
                entry_id = arguments.get("entry_id", "")
                result = server.mcp_knowledge_deep_load(entry_id)
                return [TextContent(type="text", text=json.dumps(result, ensure_ascii=False))]
    
            elif name == "knowledge_auto_retrieve":
                task_type = arguments.get("task_type", "feature")
                project_path = arguments.get("project_path", "")
                query = arguments.get("query")
                token_budget = arguments.get("token_budget", 2048)
                if not project_path:
                    return [TextContent(type="text", text=json.dumps(make_error_response(
                        code="BAD_REQUEST",
                        message="project_path is required",
                        details={"mcp_error_code": APP_ERROR_CODES["BAD_REQUEST"]},
                    ), ensure_ascii=False), isError=True)]
                try:
                    result = server.auto_retrieve(
                        task_type=task_type,
                        project_path=project_path,
                        query=query,
                        token_budget=token_budget,
                    )
                    return [TextContent(type="text", text=json.dumps(make_response("ok", result), ensure_ascii=False))]
                except Exception as e:
                    return [TextContent(type="text", text=json.dumps(make_error_response(
                        code="INTERNAL_ERROR",
                        message=f"Auto-retrieve failed: {e}",
                        details={"mcp_error_code": MCP_ERROR_CODES["INTERNAL_ERROR"]},
                    ), ensure_ascii=False), isError=True)]
    
            elif name == "knowledge_web_update":
                entry_id = arguments.get("entry_id")
                category = arguments.get("category")
                tags = arguments.get("tags")
                if not entry_id and not category and not tags:
                    return [TextContent(type="text", text=json.dumps(make_error_response(
                        code="BAD_REQUEST",
                        message="At least one of entry_id, category, or tags must be provided",
                        details={"mcp_error_code": APP_ERROR_CODES["BAD_REQUEST"]},
                    ), ensure_ascii=False), isError=True)]
                try:
                    from .web_search import search_official_docs, extract_and_structure
                except ImportError:
                    return [TextContent(type="text", text=json.dumps(make_error_response(
                        code="INTERNAL_ERROR",
                        message="Web search module not available",
                        details={"mcp_error_code": MCP_ERROR_CODES["INTERNAL_ERROR"]},
                    ), ensure_ascii=False), isError=True)]
                target_entry = None
                query_parts = []
                if entry_id:
                    target_entry = server.sqlite.get_entry(entry_id)
                    if target_entry is None:
                        return [TextContent(type="text", text=json.dumps(make_error_response(
                            code="NOT_FOUND",
                            message="Knowledge entry not found",
                            details={"entry_id": entry_id, "mcp_error_code": APP_ERROR_CODES["NOT_FOUND"]},
                        ), ensure_ascii=False), isError=True)]
                    query_parts.append(target_entry.get("title", ""))
                    if target_entry.get("category") and target_entry["category"] != "uncategorized":
                        query_parts.append(target_entry["category"])
                elif category:
                    query_parts.append(category)
                if tags:
                    query_parts.extend(tags)
                query = " ".join(query_parts)
                tech_stack = tags if tags else None
                try:
                    web_results = search_official_docs(query, tech_stack=tech_stack)
                except Exception as e:
                    logger.warning("operation=mcp_web_update, search_error=%s", e)
                    web_results = []
                if not web_results:
                    return [TextContent(type="text", text=json.dumps(make_response("ok", {
                        "status": "no_results",
                        "query": query,
                        "message": "Web search returned no results, may be offline",
                    }), ensure_ascii=False))]
                structured = extract_and_structure(web_results, existing_entry=target_entry)
                if not structured:
                    return [TextContent(type="text", text=json.dumps(make_response("ok", {
                        "status": "extraction_failed",
                        "query": query,
                        "sources_found": len(web_results),
                        "message": "Could not extract valid content from search results",
                    }), ensure_ascii=False))]
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
                        result = server.sqlite.update_entry(entry_id, updates)
                        if result and not (isinstance(result, dict) and result.get("error")):
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
                            server.exporter.export_entry(entry_id)
                            logger.info("operation=mcp_web_update, entry_id=%s, status=updated", entry_id)
                            return [TextContent(type="text", text=json.dumps(make_response("ok", {
                                "id": entry_id,
                                "status": "updated",
                                "sources_found": len(web_results),
                                "best_source_rating": max(r.get("source_rating", 0) for r in web_results),
                                "updated_fields": list(updates.keys()),
                            }), ensure_ascii=False))]
                    return [TextContent(type="text", text=json.dumps(make_response("ok", {
                        "id": entry_id,
                        "status": "no_change",
                        "sources_found": len(web_results),
                        "message": "Search results did not yield any updates",
                    }), ensure_ascii=False))]
                else:
                    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
                    structured["last_validated"] = now
                    structured["confidence"] = min(structured.get("confidence", 0.6), 0.6)
                    try:
                        result = server.sqlite.add_entry(structured)
                        new_id = result["id"]
                        if server.chroma.available:
                            try:
                                server.chroma.add_embedding(
                                    new_id,
                                    structured.get("content", ""),
                                    {"scope": structured.get("scope", "general"), "title": structured.get("title", "")},
                                )
                                server.sqlite.update_embedding_status(new_id, "ready")
                            except Exception:
                                server.sqlite.update_embedding_status(new_id, "pending")
                        server.exporter.export_entry(new_id)
                        logger.info("operation=mcp_web_update, new_entry_id=%s, status=created_pending_review", new_id)
                        return [TextContent(type="text", text=json.dumps(make_response("ok", {
                            "id": new_id,
                            "status": "created_pending_review",
                            "sources_found": len(web_results),
                            "best_source_rating": max(r.get("source_rating", 0) for r in web_results),
                        }), ensure_ascii=False))]
                    except ValueError as e:
                        return [TextContent(type="text", text=json.dumps(make_error_response(
                            code="BAD_REQUEST",
                            message=str(e),
                            details={"mcp_error_code": APP_ERROR_CODES["BAD_REQUEST"]},
                        ), ensure_ascii=False), isError=True)]
    
            else:
                pass
        except Exception as e:
            logger.error("operation=mcp_call_tool_error, tool=%s, error=%s", name, e)
            return [TextContent(type="text", text=json.dumps(make_error_response(
                code="INTERNAL_ERROR",
                message=str(e),
                details={"mcp_error_code": MCP_ERROR_CODES["INTERNAL_ERROR"]},
            ), ensure_ascii=False), isError=True)]

        if name == "resource_load_status":
            action = arguments.get("action", "status")
            loader = server.progressive_loader
            now_iso = datetime.now(timezone.utc).isoformat()

            if action == "status":
                state = loader._state
                result = {
                    "action": "status",
                    "current_phase": state.current_phase.value,
                    "phase_index": state.current_phase.index,
                    "loaded_resources": state.loaded_resources,
                    "loaded_count": len(state.loaded_resources),
                    "available_resources": loader.get_available_resources(),
                    "available_commands": loader.get_available_commands(),
                    "disclosure_note": loader.get_disclosure_note(),
                    "upgrade_hint": loader.get_upgrade_hint(),
                    "timestamp": now_iso,
                }
                return [TextContent(type="text", text=json.dumps(make_response("ok", result), ensure_ascii=False))]

            elif action == "preload":
                target_phase_str = arguments.get("target_phase", "functional")
                try:
                    target_phase = LoadPhase(target_phase_str)
                except ValueError:
                    return [TextContent(type="text", text=json.dumps(make_error_response(
                        code="BAD_REQUEST",
                        message=f"Invalid target_phase: {target_phase_str}",
                        details={"mcp_error_code": APP_ERROR_CODES["BAD_REQUEST"]},
                    ), ensure_ascii=False), isError=True)]
                state = loader.advance_phase(target_phase)
                loader.record_activity()
                result = {
                    "action": "preload",
                    "current_phase": state.current_phase.value,
                    "phase_index": state.current_phase.index,
                    "loaded_resources": state.loaded_resources,
                    "loaded_count": len(state.loaded_resources),
                    "available_resources": loader.get_available_resources(),
                    "available_commands": loader.get_available_commands(),
                    "disclosure_note": loader.get_disclosure_note(),
                    "upgrade_hint": loader.get_upgrade_hint(),
                    "timestamp": now_iso,
                }
                return [TextContent(type="text", text=json.dumps(make_response("ok", result), ensure_ascii=False))]

            elif action == "cache":
                state = loader._state
                resource_ids = arguments.get("resource_ids")
                progress = state.progress
                if resource_ids:
                    progress = {k: v for k, v in progress.items() if k in resource_ids}
                result = {
                    "action": "cache",
                    "current_phase": state.current_phase.value,
                    "phase_index": state.current_phase.index,
                    "cached_resources": list(progress.keys()),
                    "cache_details": progress,
                    "loaded_count": len(state.loaded_resources),
                    "timestamp": now_iso,
                }
                return [TextContent(type="text", text=json.dumps(make_response("ok", result), ensure_ascii=False))]

            elif action == "clear_cache":
                loader._state = ProgressiveLoader()._state
                state = loader._state
                result = {
                    "action": "clear_cache",
                    "current_phase": state.current_phase.value,
                    "phase_index": state.current_phase.index,
                    "loaded_resources": state.loaded_resources,
                    "loaded_count": len(state.loaded_resources),
                    "disclosure_note": loader.get_disclosure_note(),
                    "upgrade_hint": loader.get_upgrade_hint(),
                    "timestamp": now_iso,
                }
                return [TextContent(type="text", text=json.dumps(make_response("ok", result), ensure_ascii=False))]

            elif action == "loading_progress":
                state = loader._state
                resource_ids = arguments.get("resource_ids")
                progress = state.progress
                if resource_ids:
                    progress = {k: v for k, v in progress.items() if k in resource_ids}
                result = {
                    "action": "loading_progress",
                    "current_phase": state.current_phase.value,
                    "phase_index": state.current_phase.index,
                    "progress": progress,
                    "total_resources": len(loader.get_available_resources()),
                    "loaded_count": len(state.loaded_resources),
                    "timestamp": now_iso,
                }
                return [TextContent(type="text", text=json.dumps(make_response("ok", result), ensure_ascii=False))]

            else:
                return [TextContent(type="text", text=json.dumps(make_error_response(
                    code="BAD_REQUEST",
                    message=f"Invalid action: {action}",
                    details={"valid_actions": ["status", "preload", "cache", "clear_cache", "loading_progress"], "mcp_error_code": APP_ERROR_CODES["BAD_REQUEST"]},
                ), ensure_ascii=False), isError=True)]

        if name in SKILL_TOOL_NAMES:
            skill_result = await _skill_handler.handle(name, arguments)
            if skill_result is not None:
                return skill_result

        return [TextContent(type="text", text=json.dumps(make_error_response(
            code="UNKNOWN_TOOL",
            message=f"Unknown tool: {name}",
            details={"tool_name": name, "mcp_error_code": MCP_ERROR_CODES["METHOD_NOT_FOUND"]},
        ), ensure_ascii=False), isError=True)]


async def run_mcp_server(server):
    if not server._mcp_server:
        return
    init_options = server._mcp_server.create_initialization_options()
    if isinstance(init_options, dict):
        init_options.setdefault("capabilities", {})
        init_options["capabilities"].setdefault("tools", {"listChanged": False})
    async with stdio_server() as (read_stream, write_stream):
        await server._mcp_server.run(read_stream, write_stream, init_options)
