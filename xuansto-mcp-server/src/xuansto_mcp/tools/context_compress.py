from __future__ import annotations

from typing import Any

from mcp.server.fastmcp import FastMCP
from mcp.types import ToolAnnotations

from ..core.errors import ERR_VALIDATION, make_error_response, make_success_response
from ..core.logging_config import get_logger
from ..core.validator import validate_input
from ..models.schemas import ContextCompressInput

logger = get_logger("context_compress")

_HAS_TIKTOKEN = False
_tiktoken_encoding = None
try:
    import tiktoken
    _tiktoken_encoding = tiktoken.get_encoding("cl100k_base")
    _HAS_TIKTOKEN = True
except ImportError:
    _HAS_TIKTOKEN = False
except Exception:
    _HAS_TIKTOKEN = False


def _estimate_tokens(text: str) -> int:
    if _HAS_TIKTOKEN and _tiktoken_encoding is not None:
        try:
            return len(_tiktoken_encoding.encode(text))
        except Exception:
            pass
    return max(1, len(text) // 4)

def _split_into_semantic_chunks(content: str) -> list[dict[str, Any]]:
    chunks: list[dict[str, Any]] = []
    current_lines: list[str] = []
    current_type = "prose"

    for line in content.split("\n"):
        if line.startswith("#") or line.startswith("//"):
            if current_lines:
                chunks.append({"content": "\n".join(current_lines), "type": current_type})
                current_lines = []
            current_type = "heading"
            current_lines.append(line)
        elif line.startswith("def ") or line.startswith("async def ") or line.startswith("function "):
            if current_lines:
                chunks.append({"content": "\n".join(current_lines), "type": current_type})
                current_lines = []
            current_type = "function"
            current_lines.append(line)
        elif line.startswith("class "):
            if current_lines:
                chunks.append({"content": "\n".join(current_lines), "type": current_type})
                current_lines = []
            current_type = "class"
            current_lines.append(line)
        elif line.startswith("import ") or line.startswith("from "):
            if current_lines and current_type != "import":
                chunks.append({"content": "\n".join(current_lines), "type": current_type})
                current_lines = []
            current_type = "import"
            current_lines.append(line)
        else:
            if current_type in ("heading", "function", "class") and not line.startswith(" ") and not line.startswith("\t") and line.strip():
                chunks.append({"content": "\n".join(current_lines), "type": current_type})
                current_lines = []
                current_type = "prose"
            current_lines.append(line)

    if current_lines:
        chunks.append({"content": "\n".join(current_lines), "type": current_type})

    return chunks

def _score_chunk_importance(chunk: dict[str, Any]) -> float:
    chunk_type = chunk.get("type", "prose")
    content = chunk.get("content", "")
    scores = {"heading": 3.0, "import": 2.5, "class": 3.0, "function": 2.5, "prose": 1.0}
    base = scores.get(chunk_type, 1.0)
    if "TODO" in content or "FIXME" in content:
        base += 0.5
    if "class " in content:
        base += 0.5
    if "def " in content:
        base += 0.3
    return base

def _summarize_chunk(chunk: dict[str, Any]) -> str:
    content = chunk.get("content", "")
    chunk_type = chunk.get("type", "prose")
    first_line = content.split("\n")[0][:80] if content else ""
    if chunk_type == "function":
        return f"函数: {first_line}"
    elif chunk_type == "class":
        return f"类: {first_line}"
    elif chunk_type == "heading":
        return f"标题: {first_line}"
    elif chunk_type == "import":
        return f"导入: {first_line}"
    return f"段落: {first_line}"

def _semantic_compress(content: str, target_tokens: int) -> dict[str, Any]:
    chunks = _split_into_semantic_chunks(content)
    if not chunks:
        return {"compressed_content": content, "original_tokens": _estimate_tokens(content), "compressed_tokens": _estimate_tokens(content), "ratio": 1.0}

    total_tokens = sum(_estimate_tokens(c["content"]) for c in chunks)
    if total_tokens <= target_tokens:
        return {"compressed_content": content, "original_tokens": total_tokens, "compressed_tokens": total_tokens, "ratio": 1.0}

    for chunk in chunks:
        chunk["score"] = _score_chunk_importance(chunk)

    sorted_chunks = sorted(chunks, key=lambda c: c["score"], reverse=True)

    kept = []
    current_tokens = 0
    for chunk in sorted_chunks:
        chunk_tokens = _estimate_tokens(chunk["content"])
        if current_tokens + chunk_tokens <= target_tokens:
            kept.append(chunk)
            current_tokens += chunk_tokens

    kept_ids = {id(c) for c in kept}
    result_parts = []
    for chunk in chunks:
        if id(chunk) in kept_ids:
            result_parts.append(chunk["content"])
        else:
            summary = _summarize_chunk(chunk)
            result_parts.append(f"[...{summary}...]")

    compressed = "\n".join(result_parts)
    compressed_tokens = _estimate_tokens(compressed)
    return {"compressed_content": compressed, "original_tokens": total_tokens, "compressed_tokens": compressed_tokens, "ratio": round(compressed_tokens / max(total_tokens, 1), 2)}

def _selective_compress(content: str, target_tokens: int, preserve_keywords: list[str] | None = None) -> dict[str, Any]:
    if not preserve_keywords:
        preserve_keywords = []

    chunks = _split_into_semantic_chunks(content)
    if not chunks:
        return {"compressed_content": content, "original_tokens": _estimate_tokens(content), "compressed_tokens": _estimate_tokens(content), "ratio": 1.0}

    preserved = []
    compressed_parts = []

    for chunk in chunks:
        chunk_content = chunk.get("content", "")
        is_preserved = any(kw.lower() in chunk_content.lower() for kw in preserve_keywords)
        if is_preserved:
            preserved.append(chunk)
            compressed_parts.append(chunk_content)
        else:
            summary = _summarize_chunk(chunk)
            compressed_parts.append(f"[...{summary}...]")

    compressed = "\n".join(compressed_parts)
    total_tokens = _estimate_tokens(content)
    compressed_tokens = _estimate_tokens(compressed)

    if compressed_tokens > target_tokens:
        preserved_contents = [c.get("content", "") for c in preserved]
        for i, part in enumerate(compressed_parts):
            if part not in preserved_contents:
                lines = part.split("\n")
                if len(lines) > 3:
                    compressed_parts[i] = "\n".join(lines[:2] + [f"... ({len(lines) - 2} more lines)"])
        compressed = "\n".join(compressed_parts)
        compressed_tokens = _estimate_tokens(compressed)

    return {"compressed_content": compressed, "original_tokens": total_tokens, "compressed_tokens": compressed_tokens, "ratio": round(compressed_tokens / max(total_tokens, 1), 2), "preserved_chunks": len(preserved), "total_chunks": len(chunks)}

def _compress_lossless(content: str, target_tokens: int, preserve_sections: list[str] | None) -> str:
    lines = content.split('\n')
    result = []
    current_tokens = 0
    for line in lines:
        line_tokens = _estimate_tokens(line)
        if current_tokens + line_tokens > target_tokens:
            break
        result.append(line)
        current_tokens += line_tokens
    return '\n'.join(result)

def register(mcp: FastMCP) -> None:
    @mcp.tool(
        annotations=ToolAnnotations(
            readOnlyHint=True,
            destructiveHint=False,
            idempotentHint=True,
            openWorldHint=False,
        )
    )
    async def context_compress(
        content: str,
        strategy: str = "semantic",
        target_tokens: int = 2000,
        preserve_sections: list[str] | None = None,
    ) -> dict[str, Any]:
        """上下文压缩：支持semantic(语义保留)/selective(选择性采样)/lossless(无损截断)三种策略。保留指定章节，压缩其余内容至目标Token数。"""
        validated, err = validate_input(ContextCompressInput, content=content, strategy=strategy, target_tokens=target_tokens, preserve_sections=preserve_sections)
        if err:
            return err
        logger.info("context_compress called: strategy=%s", strategy)
        try:
            original_tokens = _estimate_tokens(content)
            if original_tokens <= target_tokens:
                return make_success_response({
                    "compressed": content,
                    "original_tokens": original_tokens,
                    "compressed_tokens": original_tokens,
                    "actual_tokens": original_tokens,
                    "target_deviation": 0,
                    "compression_ratio": 1.0,
                    "strategy": strategy,
                    "token_method": "tiktoken" if _HAS_TIKTOKEN else "char_estimate",
                })
            if strategy == "semantic":
                result = _semantic_compress(content, target_tokens)
                actual_tokens = _estimate_tokens(result["compressed_content"])
                deviation = actual_tokens - target_tokens
                return make_success_response({
                    "compressed": result["compressed_content"],
                    "original_tokens": result["original_tokens"],
                    "compressed_tokens": result["compressed_tokens"],
                    "actual_tokens": actual_tokens,
                    "target_deviation": deviation,
                    "compression_ratio": result["ratio"],
                    "strategy": strategy,
                    "token_method": "tiktoken" if _HAS_TIKTOKEN else "char_estimate",
                })
            elif strategy == "selective":
                result = _selective_compress(content, target_tokens, preserve_sections)
                actual_tokens = _estimate_tokens(result["compressed_content"])
                deviation = actual_tokens - target_tokens
                return make_success_response({
                    "compressed": result["compressed_content"],
                    "original_tokens": result["original_tokens"],
                    "compressed_tokens": result["compressed_tokens"],
                    "actual_tokens": actual_tokens,
                    "target_deviation": deviation,
                    "compression_ratio": result["ratio"],
                    "strategy": strategy,
                    "preserved_chunks": result.get("preserved_chunks"),
                    "total_chunks": result.get("total_chunks"),
                    "token_method": "tiktoken" if _HAS_TIKTOKEN else "char_estimate",
                })
            elif strategy == "lossless":
                compressed = _compress_lossless(content, target_tokens, preserve_sections)
                compressed_tokens = _estimate_tokens(compressed)
                actual_tokens = _estimate_tokens(compressed)
                deviation = actual_tokens - target_tokens
                return make_success_response({
                    "compressed": compressed,
                    "original_tokens": original_tokens,
                    "compressed_tokens": compressed_tokens,
                    "actual_tokens": actual_tokens,
                    "target_deviation": deviation,
                    "compression_ratio": round(compressed_tokens / original_tokens, 2) if original_tokens > 0 else 0,
                    "strategy": strategy,
                    "token_method": "tiktoken" if _HAS_TIKTOKEN else "char_estimate",
                })
            else:
                return make_error_response(ValueError(f"未知策略: {strategy}，支持: semantic, selective, lossless"), error_code=ERR_VALIDATION)
        except Exception as e:
            logger.error("context_compress error: %s", e)
            return make_error_response(e)
