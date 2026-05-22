import sys
import pytest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from xuansto_mcp.tools.hook_manage import execute_pre_hooks, execute_post_hooks


def test_pre_hook_exception_isolation():
    def bad_hook(project_path, context):
        raise RuntimeError("Hook crashed")
    def good_hook(project_path, context):
        return {"status": "ok", "hook": "good"}
    with patch("xuansto_mcp.tools.hook_manage.get_pre_hooks", return_value=["bad", "good"]):
        with patch("xuansto_mcp.tools.hook_manage.INLINE_HOOK_LOGIC", {"bad": bad_hook, "good": good_hook}):
            results, errors = execute_pre_hooks("test_tool", {})
            assert len(errors) == 1
            assert errors[0]["hook"] == "bad"
            assert len(results) == 1
            assert results[0]["status"] == "ok"


def test_post_hook_exception_isolation():
    def bad_post(project_path, context):
        raise RuntimeError("Post hook crashed")
    with patch("xuansto_mcp.tools.hook_manage.get_post_hooks", return_value=["bad_post"]):
        with patch("xuansto_mcp.tools.hook_manage.INLINE_HOOK_LOGIC", {"bad_post": bad_post}):
            errors = execute_post_hooks("test_tool", {}, {"status": "ok"})
            assert len(errors) == 1
            assert errors[0]["hook"] == "bad_post"
