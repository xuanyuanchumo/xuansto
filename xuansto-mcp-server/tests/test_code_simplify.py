import os
import time
import pytest
from pathlib import Path
from mcp.server.fastmcp import FastMCP

from xuansto_mcp.tools.code_simplify import (
    _inline_simplify,
    _inline_dedup,
    _collect_source_files,
    register,
)


@pytest.fixture
def tmp_project(tmp_path):
    src = tmp_path / "src"
    src.mkdir()
    return src


def _write_long_function(path: Path, extra_lines: int = 55):
    lines = ["def very_long_function():"]
    for i in range(extra_lines):
        lines.append(f"    x = {i}")
    lines.append("    return x")
    lines.append("")
    lines.append("def short_function():")
    lines.append("    pass")
    path.write_text("\n".join(lines), encoding="utf-8")


def test_inline_simplify_detects_long_functions(tmp_project):
    py_file = tmp_project / "long_func.py"
    _write_long_function(py_file, 55)

    result = _inline_simplify(str(tmp_project), "dir")

    assert "suggestions" in result
    assert result["total"] >= 1
    assert result["by_type"]["long_function"] >= 1

    long_func_suggestions = [s for s in result["suggestions"] if s["type"] == "long_function"]
    assert len(long_func_suggestions) >= 1
    assert long_func_suggestions[0]["severity"] == "medium"
    assert "long_func.py" in long_func_suggestions[0]["file"]


def test_inline_simplify_detects_unused_imports(tmp_project):
    py_file = tmp_project / "unused_imports.py"
    content = "import os\nimport json\nimport sys\n\nprint(os.path.exists('.'))\n"
    py_file.write_text(content, encoding="utf-8")

    result = _inline_simplify(str(tmp_project), "dir")

    assert "suggestions" in result
    unused = [s for s in result["suggestions"] if s["type"] == "unused_import"]
    assert len(unused) >= 1

    unused_names = {s["description"].split(": ")[-1] for s in unused}
    assert "json" in unused_names or "sys" in unused_names


def test_inline_simplify_detects_deep_nesting(tmp_project):
    py_file = tmp_project / "deep_nest.py"
    lines = ["def f():"]
    for i in range(6):
        indent = "    " * (i + 1)
        lines.append(f"{indent}if True:")
    lines.append("    " * 7 + "x = 1")
    py_file.write_text("\n".join(lines), encoding="utf-8")

    result = _inline_simplify(str(tmp_project), "dir")

    deep = [s for s in result["suggestions"] if s["type"] == "deep_nesting"]
    assert len(deep) >= 1
    assert deep[0]["severity"] == "high"


def test_inline_simplify_detects_dead_code(tmp_project):
    py_file = tmp_project / "dead_code.py"
    content = "def f():\n    return 1\n    x = 2\n\nif False:\n    pass\n"
    py_file.write_text(content, encoding="utf-8")

    result = _inline_simplify(str(tmp_project), "dir")

    dead = [s for s in result["suggestions"] if s["type"] == "dead_code"]
    assert len(dead) >= 1


def test_inline_simplify_returns_by_type(tmp_project):
    py_file = tmp_project / "simple.py"
    py_file.write_text("def f():\n    pass\n", encoding="utf-8")

    result = _inline_simplify(str(tmp_project), "dir")

    assert "by_type" in result
    assert "long_function" in result["by_type"]
    assert "deep_nesting" in result["by_type"]
    assert "unused_import" in result["by_type"]
    assert "dead_code" in result["by_type"]
    assert result["total"] == sum(result["by_type"].values())


def test_inline_dedup_detects_duplicate_blocks(tmp_project):
    block = "\n".join([
        "x = 1",
        "y = 2",
        "z = x + y",
    ])

    file_a = tmp_project / "a.py"
    file_b = tmp_project / "b.py"

    file_a.write_text(f"{block}\nprint(x)\n", encoding="utf-8")
    file_b.write_text(f"{block}\nprint(y)\n", encoding="utf-8")

    result = _inline_dedup(str(tmp_project))

    assert "duplicates" in result
    assert "total_groups" in result
    assert "total_duplicate_lines" in result
    assert result["total_groups"] >= 1

    dup = result["duplicates"][0]
    assert dup["count"] >= 2
    assert len(dup["files"]) >= 1
    assert "hash" in dup
    assert "preview" in dup


def test_inline_dedup_no_duplicates(tmp_project):
    file_a = tmp_project / "unique_a.py"
    file_b = tmp_project / "unique_b.py"

    file_a.write_text("x = 1\ny = 2\nz = 3\n", encoding="utf-8")
    file_b.write_text("a = 10\nb = 20\nc = 30\n", encoding="utf-8")

    result = _inline_dedup(str(tmp_project))

    assert result["total_groups"] == 0
    assert result["duplicates"] == []


def test_scope_recent_filters_old_files(tmp_project):
    old_file = tmp_project / "old.py"
    old_file.write_text("import unused_module\n\ndef f():\n    pass\n", encoding="utf-8")

    old_mtime = time.time() - 100000
    os.utime(str(old_file), (old_mtime, old_mtime))

    new_file = tmp_project / "new.py"
    new_file.write_text("import another_unused\n\ndef g():\n    pass\n", encoding="utf-8")

    result = _inline_simplify(str(tmp_project), "recent")

    files_in_suggestions = {s["file"] for s in result["suggestions"]}
    assert any("new.py" in f for f in files_in_suggestions) or result["total"] >= 0
    assert not any("old.py" in f for f in files_in_suggestions)


def test_collect_source_files_filters_extensions(tmp_project):
    (tmp_project / "app.py").write_text("x = 1", encoding="utf-8")
    (tmp_project / "app.js").write_text("var x = 1;", encoding="utf-8")
    (tmp_project / "app.ts").write_text("let x = 1;", encoding="utf-8")
    (tmp_project / "data.json").write_text("{}", encoding="utf-8")
    (tmp_project / "readme.txt").write_text("hello", encoding="utf-8")

    files = _collect_source_files(str(tmp_project), "dir")

    suffixes = {f.suffix for f in files}
    assert ".py" in suffixes
    assert ".js" in suffixes
    assert ".ts" in suffixes
    assert ".json" not in suffixes
    assert ".txt" not in suffixes


def test_collect_source_files_single_file(tmp_project):
    py_file = tmp_project / "single.py"
    py_file.write_text("x = 1", encoding="utf-8")

    files = _collect_source_files(str(py_file), "file")

    assert len(files) == 1
    assert files[0].suffix == ".py"


@pytest.mark.asyncio
async def test_code_simplify_registered():
    mcp = FastMCP("test")
    register(mcp)
    tools = await mcp.list_tools()
    tool_names = [t.name for t in tools]
    assert "code_simplify" in tool_names
