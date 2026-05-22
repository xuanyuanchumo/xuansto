import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from xuansto_mcp.tools import context_compress
from mcp.server.fastmcp import FastMCP


def test_register():
    mcp = FastMCP("test")
    context_compress.register(mcp)
    tools = mcp._tool_manager._tools
    assert "context_compress" in tools


def test_estimate_tokens():
    assert context_compress._estimate_tokens("hello world") == 2
    assert context_compress._estimate_tokens("") == 1
    assert context_compress._estimate_tokens("a b c d") == 1


def test_compress_semantic():
    content = "# Header\n\nSome content here.\n\n## Section\n\nMore content."
    result = context_compress._semantic_compress(content, 50)
    assert isinstance(result, dict)
    assert "compressed_content" in result
    assert len(result["compressed_content"]) > 0
    assert "#" in result["compressed_content"]


def test_compress_selective():
    content = "\n".join(f"Line {i}" for i in range(100))
    result = context_compress._selective_compress(content, 50, None)
    assert isinstance(result, dict)
    assert "compressed_content" in result
    assert len(result["compressed_content"]) > 0
    assert len(result["compressed_content"]) < len(content)
    assert "Line" in result["compressed_content"]


def test_compress_lossless():
    content = "\n".join(f"Line {i}" for i in range(100))
    result = context_compress._compress_lossless(content, 50, None)
    assert isinstance(result, str)
    assert len(result) > 0
    assert "Line" in result
