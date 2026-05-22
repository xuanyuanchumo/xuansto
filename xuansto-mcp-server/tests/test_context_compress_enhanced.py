import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from xuansto_mcp.tools import context_compress


SAMPLE_CODE = """# My Module

import os
import sys

class MyClass:
    def __init__(self):
        self.value = 42

    def compute(self, x):
        return x * self.value

def helper_function(a, b):
    return a + b

async def async_handler(request):
    return await request.json()

Some prose text that is not code.
It spans multiple lines.
But has no structural markers.

class AnotherClass:
    pass
"""


def test_split_into_semantic_chunks():
    chunks = context_compress._split_into_semantic_chunks(SAMPLE_CODE)
    types = [c["type"] for c in chunks]
    assert "heading" in types, f"Expected 'heading' in chunk types, got {types}"
    assert "import" in types, f"Expected 'import' in chunk types, got {types}"
    assert "class" in types, f"Expected 'class' in chunk types, got {types}"
    assert "function" in types, f"Expected 'function' in chunk types, got {types}"
    assert "prose" in types, f"Expected 'prose' in chunk types, got {types}"


def test_split_chunks_preserve_content():
    chunks = context_compress._split_into_semantic_chunks(SAMPLE_CODE)
    reconstructed = "\n".join(c["content"] for c in chunks)
    assert reconstructed == SAMPLE_CODE, "Reconstructed content should match original"


def test_semantic_compress_smaller():
    result = context_compress._semantic_compress(SAMPLE_CODE, 50)
    assert result["compressed_tokens"] < result["original_tokens"], \
        f"Compressed ({result['compressed_tokens']}) should be smaller than original ({result['original_tokens']})"
    assert result["ratio"] < 1.0, f"Ratio should be < 1.0, got {result['ratio']}"


def test_semantic_compress_keeps_important():
    result = context_compress._semantic_compress(SAMPLE_CODE, 50)
    compressed = result["compressed_content"]
    has_class_or_heading = "class" in compressed.lower() or "#" in compressed
    assert has_class_or_heading, "Semantic compression should keep high-importance chunks (class/heading)"


def test_semantic_compress_no_need():
    short = "Hello world"
    result = context_compress._semantic_compress(short, 1000)
    assert result["ratio"] == 1.0, "Short content should not be compressed"
    assert result["compressed_content"] == short


def test_selective_compress_preserves_keywords():
    result = context_compress._selective_compress(SAMPLE_CODE, 50, preserve_keywords=["MyClass"])
    compressed = result["compressed_content"]
    assert "MyClass" in compressed, "Selective compression should preserve chunks matching keywords"
    assert result["preserved_chunks"] >= 1, f"Expected at least 1 preserved chunk, got {result['preserved_chunks']}"


def test_selective_compress_no_keywords():
    result = context_compress._selective_compress(SAMPLE_CODE, 50, preserve_keywords=None)
    assert "compressed_content" in result
    assert "ratio" in result
    assert result["total_chunks"] > 0


def test_selective_compress_smaller():
    result = context_compress._selective_compress(SAMPLE_CODE, 50, preserve_keywords=["MyClass"])
    assert result["compressed_tokens"] < result["original_tokens"], \
        "Compressed should be smaller than original"


def test_score_chunk_importance():
    heading_chunk = {"content": "# Title", "type": "heading"}
    class_chunk = {"content": "class Foo:\n    pass", "type": "class"}
    prose_chunk = {"content": "Some text", "type": "prose"}
    todo_chunk = {"content": "TODO: fix this", "type": "prose"}

    heading_score = context_compress._score_chunk_importance(heading_chunk)
    class_score = context_compress._score_chunk_importance(class_chunk)
    prose_score = context_compress._score_chunk_importance(prose_chunk)
    todo_score = context_compress._score_chunk_importance(todo_chunk)

    assert heading_score > prose_score, "Heading should score higher than prose"
    assert class_score > prose_score, "Class should score higher than prose"
    assert todo_score > prose_score, "TODO chunk should score higher than plain prose"


def test_summarize_chunk():
    func_chunk = {"content": "def hello():\n    pass", "type": "function"}
    class_chunk = {"content": "class Foo:\n    pass", "type": "class"}
    heading_chunk = {"content": "# Section", "type": "heading"}
    import_chunk = {"content": "import os", "type": "import"}
    prose_chunk = {"content": "Some text here", "type": "prose"}

    assert context_compress._summarize_chunk(func_chunk).startswith("函数:")
    assert context_compress._summarize_chunk(class_chunk).startswith("类:")
    assert context_compress._summarize_chunk(heading_chunk).startswith("标题:")
    assert context_compress._summarize_chunk(import_chunk).startswith("导入:")
    assert context_compress._summarize_chunk(prose_chunk).startswith("段落:")


def test_lossless_strategy_unchanged():
    content = "\n".join(f"Line {i}" for i in range(100))
    result = context_compress._compress_lossless(content, 50, None)
    assert isinstance(result, str)
    assert len(result) > 0
    assert "Line" in result
    lines = result.split("\n")
    for line in lines:
        assert line.startswith("Line "), f"Lossless should keep complete lines, got: {line}"


def test_estimate_tokens_never_zero():
    assert context_compress._estimate_tokens("") == 1, "Empty string should estimate to at least 1 token"
    assert context_compress._estimate_tokens("a") == 1, "Single char should estimate to at least 1 token"
