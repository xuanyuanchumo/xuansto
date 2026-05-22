import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from xuansto_mcp.resources import skill_resources
from xuansto_mcp.core.config import TEMPLATES_DIR
from mcp.server.fastmcp import FastMCP


def _get_template_func():
    mcp = FastMCP("test")
    skill_resources.register(mcp)
    for tmpl in mcp._resource_manager._templates.values():
        if "templates" in str(tmpl.uri_template):
            return tmpl.fn
    raise RuntimeError("template resource not found")


def test_normal_template_name():
    template_fn = _get_template_func()
    TEMPLATES_DIR.mkdir(parents=True, exist_ok=True)
    test_file = TEMPLATES_DIR / "test-normal.md"
    try:
        test_file.write_text("hello world", encoding="utf-8")
        result = template_fn(name="test-normal")
        assert result == "hello world", f"Expected 'hello world', got {result!r}"
    finally:
        test_file.unlink(missing_ok=True)


def test_path_traversal_dotdot_slash():
    template_fn = _get_template_func()
    result = template_fn(name="../etc/passwd")
    assert "Error" in result or "invalid" in result.lower(), \
        f"Path traversal with ../ should be blocked, got {result!r}"


def test_path_traversal_dotdot_backslash():
    template_fn = _get_template_func()
    result = template_fn(name="..\\etc\\passwd")
    assert "Error" in result or "invalid" in result.lower(), \
        f"Path traversal with ..\\ should be blocked, got {result!r}"


def test_path_traversal_deep_dotdot():
    template_fn = _get_template_func()
    result = template_fn(name="../../etc/passwd")
    assert "Error" in result or "invalid" in result.lower(), \
        f"Deep path traversal should be blocked, got {result!r}"


def test_absolute_path_blocked():
    template_fn = _get_template_func()
    result = template_fn(name="/etc/passwd")
    assert "Error" in result or "invalid" in result.lower() or "not found" in result.lower(), \
        f"Absolute path should be blocked, got {result!r}"


def test_nonexistent_template():
    template_fn = _get_template_func()
    result = template_fn(name="nonexistent-template-xyz")
    assert "not found" in result.lower(), \
        f"Nonexistent template should return not found, got {result!r}"


def test_dotdot_in_middle():
    template_fn = _get_template_func()
    result = template_fn(name="foo/../bar")
    assert "Error" in result or "invalid" in result.lower(), \
        f"Path traversal with .. in middle should be blocked, got {result!r}"
