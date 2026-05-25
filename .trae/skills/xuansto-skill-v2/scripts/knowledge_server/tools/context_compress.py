import json

from ..config import make_response, make_error_response, mcp_available
from ._shared import MCP_JSON_SCHEMA_URI, _estimate_tokens, _semantic_compress, _selective_compress, _lossless_compress

if mcp_available:
    from mcp.types import Tool, TextContent, ToolAnnotations


def get_tool_definition():
    if not mcp_available:
        return None
    return Tool(
        name="context_compress",
        description=(
            "[Read-Only] [Idempotent] Context compression: semantic, selective, lossless strategies.\n\n"
            "Use this tool to compress long context text to fit within token budgets. "
            "Supports three strategies: semantic (meaning-preserving summary), selective (keep key sections), "
            "and lossless (whitespace/format optimization only).\n\n"
            "Parameters:\n"
            "- content (string, required): Text content to compress.\n"
            "- strategy (string, default='semantic', enum: semantic|selective|lossless): Compression strategy.\n"
            "- target_tokens (integer, default=2000, range 100-50000): Target token count.\n"
            "- preserve_sections (array of strings, optional): Section titles that must be preserved.\n\n"
            "Returns an object with:\n"
            "- original_tokens: Estimated original token count.\n"
            "- compressed_tokens: Estimated compressed token count.\n"
            "- compression_ratio: Compression ratio (0-1).\n"
            "- strategy_used: The strategy used.\n"
            "- compressed_content: The compressed text.\n"
            "- preserved_sections: Sections that were preserved.\n"
            "- quality_score: Estimated quality score (0-1).\n\n"
            "Example: Semantic compression:\n"
            '{"content": "...(long text)...", "strategy": "semantic", "target_tokens": 2000}'
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "content": {"type": "string", "description": "Text content to compress"},
                "strategy": {"type": "string", "description": "Compression strategy: semantic, selective, lossless", "default": "semantic", "enum": ["semantic", "selective", "lossless"]},
                "target_tokens": {"type": "integer", "description": "Target token count", "default": 2000, "minimum": 100, "maximum": 50000},
                "preserve_sections": {"type": "array", "items": {"type": "string"}, "description": "Section titles that must be preserved"},
            },
            "required": ["content"],
            "additionalProperties": False,
            "$schema": MCP_JSON_SCHEMA_URI,
        },
        outputSchema={
            "type": "object",
            "properties": {
                "original_tokens": {"type": "integer"},
                "compressed_tokens": {"type": "integer"},
                "compression_ratio": {"type": "number"},
                "strategy_used": {"type": "string"},
                "compressed_content": {"type": "string"},
                "preserved_sections": {"type": "array", "items": {"type": "string"}},
                "quality_score": {"type": "number"},
            },
        },
        annotations=ToolAnnotations(readOnlyHint=True, destructiveHint=False, idempotentHint=True, openWorldHint=False),
    )


async def handle_tool(arguments: dict, context: dict):
    content = arguments.get("content", "")
    strategy = arguments.get("strategy", "semantic")
    target_tokens = arguments.get("target_tokens", 2000)
    preserve_sections = arguments.get("preserve_sections")

    if not content:
        return [TextContent(type="text", text=json.dumps(make_error_response(
            code="INVALID_INPUT",
            message="content is required",
            details={},
        ), ensure_ascii=False), isError=True)]

    original_tokens = _estimate_tokens(content)

    if strategy == "lossless":
        compressed = _lossless_compress(content)
        compressed_tokens = _estimate_tokens(compressed)
    elif strategy == "selective":
        compressed = _selective_compress(content, preserve_sections or [], target_tokens)
        compressed_tokens = _estimate_tokens(compressed)
    else:
        compressed = _semantic_compress(content, preserve_sections or [], target_tokens)
        compressed_tokens = _estimate_tokens(compressed)

    ratio = compressed_tokens / original_tokens if original_tokens > 0 else 0
    quality = max(0.0, min(1.0, 1.0 - (ratio * 0.5)))

    preserved = []
    if preserve_sections:
        for section in preserve_sections:
            if section in compressed:
                preserved.append(section)

    result = {
        "original_tokens": original_tokens,
        "compressed_tokens": compressed_tokens,
        "compression_ratio": round(ratio, 2),
        "strategy_used": strategy,
        "compressed_content": compressed,
        "preserved_sections": preserved,
        "quality_score": round(quality, 2),
    }
    return [TextContent(type="text", text=json.dumps(make_response("ok", result), ensure_ascii=False))]
