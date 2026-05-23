import pytest
from unittest.mock import patch, MagicMock
from mcp.server.fastmcp import FastMCP
from xuansto_mcp.tools.context_compress import (
    _estimate_tokens,
    _split_into_semantic_chunks,
    _score_chunk_importance,
    _summarize_chunk,
    _semantic_compress,
    _selective_compress,
    _compress_lossless,
    register,
)


@pytest.fixture
def mcp_server():
    return FastMCP("test-server")


def test_estimate_tokens():
    assert _estimate_tokens("hello") == 1
    assert _estimate_tokens("a" * 8) == 2
    assert _estimate_tokens("") == 1


def test_split_into_semantic_chunks_heading():
    content = "# Heading\nSome text\n## Sub\nMore text"
    chunks = _split_into_semantic_chunks(content)
    assert len(chunks) >= 2
    types = {c["type"] for c in chunks}
    assert "heading" in types


def test_split_into_semantic_chunks_function():
    content = "def foo():\n    pass\n\ndef bar():\n    return 1"
    chunks = _split_into_semantic_chunks(content)
    func_chunks = [c for c in chunks if c["type"] == "function"]
    assert len(func_chunks) >= 1


def test_split_into_semantic_chunks_class():
    content = "class MyClass:\n    pass"
    chunks = _split_into_semantic_chunks(content)
    class_chunks = [c for c in chunks if c["type"] == "class"]
    assert len(class_chunks) >= 1


def test_split_into_semantic_chunks_import():
    content = "import os\nimport sys\n\npass"
    chunks = _split_into_semantic_chunks(content)
    import_chunks = [c for c in chunks if c["type"] == "import"]
    assert len(import_chunks) >= 1


def test_score_chunk_importance_heading():
    chunk = {"type": "heading", "content": "# Important"}
    assert _score_chunk_importance(chunk) >= 3.0


def test_score_chunk_importance_todo():
    chunk = {"type": "prose", "content": "TODO: fix this later"}
    score = _score_chunk_importance(chunk)
    assert score > 1.0


def test_summarize_chunk_function():
    chunk = {"type": "function", "content": "def hello():\n    pass"}
    summary = _summarize_chunk(chunk)
    assert "函数" in summary


def test_summarize_chunk_class():
    chunk = {"type": "class", "content": "class Foo:\n    pass"}
    summary = _summarize_chunk(chunk)
    assert "类" in summary


def test_semantic_compress_no_reduction():
    content = "short"
    result = _semantic_compress(content, 1000)
    assert result["ratio"] == 1.0


def test_semantic_compress_with_reduction():
    content = "\n".join([f"# Section {i}\n" + "x" * 200 for i in range(50)])
    result = _semantic_compress(content, 50)
    assert result["compressed_tokens"] <= result["original_tokens"]


def test_selective_compress_with_keywords():
    content = "# Important\nKeep this section\n# Other\nSkip this section"
    result = _selective_compress(content, 100, preserve_keywords=["Important"])
    assert result["preserved_chunks"] >= 1


def test_selective_compress_no_keywords():
    content = "Some content here"
    result = _selective_compress(content, 100)
    assert "compressed_content" in result


def test_compress_lossless():
    content = "\n".join([f"Line {i}" for i in range(100)])
    result = _compress_lossless(content, 20, None)
    assert len(result) < len(content)


@pytest.mark.asyncio
async def test_context_compress_semantic_positive(mcp_server):
    register(mcp_server)
    tool_fn = mcp_server._tool_manager._tools["context_compress"].fn
    result = await tool_fn(content="Hello world", strategy="semantic", target_tokens=100)
    assert result.get("error") is False


@pytest.mark.asyncio
async def test_context_compress_selective_positive(mcp_server):
    register(mcp_server)
    tool_fn = mcp_server._tool_manager._tools["context_compress"].fn
    result = await tool_fn(content="Hello world", strategy="selective", target_tokens=100, preserve_sections=["Hello"])
    assert result.get("error") is False


@pytest.mark.asyncio
async def test_context_compress_lossless_positive(mcp_server):
    register(mcp_server)
    tool_fn = mcp_server._tool_manager._tools["context_compress"].fn
    result = await tool_fn(content="Hello world", strategy="lossless", target_tokens=100)
    assert result.get("error") is False


@pytest.mark.asyncio
async def test_context_compress_invalid_strategy(mcp_server):
    register(mcp_server)
    tool_fn = mcp_server._tool_manager._tools["context_compress"].fn
    result = await tool_fn(content="Hello world " * 500, strategy="invalid_strategy", target_tokens=100)
    assert result.get("error") is True


@pytest.mark.asyncio
async def test_context_compress_empty_content_returns_success(mcp_server):
    register(mcp_server)
    tool_fn = mcp_server._tool_manager._tools["context_compress"].fn
    result = await tool_fn(content="")
    assert result.get("error") is False
    assert result["data"]["compression_ratio"] == 1.0
