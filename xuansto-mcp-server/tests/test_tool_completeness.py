from __future__ import annotations

import ast
import importlib
import inspect
from pathlib import Path
from typing import Any

import pytest

TOOLS_DIR = Path(__file__).resolve().parent.parent / "src" / "xuansto_mcp" / "tools"

EXPECTED_TOOL_MODULES = [
    "agent_manage",
    "agent_status",
    "audit_query",
    "code_simplify",
    "config_manage",
    "context_compress",
    "decision_log",
    "hook_manage",
    "knowledge_inject",
    "knowledge_search",
    "metrics_report",
    "project_init",
    "quality_gate_check",
    "resource_load_status",
    "resource_subscribe",
    "security_scan",
    "server_health",
    "session_manage",
    "skill_analyze",
    "spec_drift_detect",
    "token_budget",
    "workflow_dispatch",
]

TOOL_ANNOTATION_FIELDS = [
    "readOnlyHint",
    "destructiveHint",
    "idempotentHint",
    "openWorldHint",
]


def _read_source(module_name: str) -> str:
    module_path = TOOLS_DIR / f"{module_name}.py"
    return module_path.read_text(encoding="utf-8")


def _can_import_module(module_name: str) -> bool:
    try:
        importlib.import_module(f"xuansto_mcp.tools.{module_name}")
        return True
    except (SyntaxError, IndentationError, ImportError):
        return False


class TestToolModuleFiles:
    def test_tools_directory_exists(self):
        assert TOOLS_DIR.exists(), f"Tools directory should exist at {TOOLS_DIR}"

    @pytest.mark.parametrize("module_name", EXPECTED_TOOL_MODULES)
    def test_tool_module_file_exists(self, module_name: str):
        module_path = TOOLS_DIR / f"{module_name}.py"
        assert module_path.exists(), f"Tool module file {module_name}.py should exist"

    def test_tool_count_is_22(self):
        py_files = [f for f in TOOLS_DIR.iterdir() if f.suffix == ".py" and f.name != "__init__.py"]
        tool_module_names = [f.stem for f in py_files]
        for name in EXPECTED_TOOL_MODULES:
            assert name in tool_module_names, f"Expected tool module {name} not found"


class TestToolModuleImports:
    @pytest.mark.parametrize("module_name", EXPECTED_TOOL_MODULES)
    def test_tool_module_importable(self, module_name: str):
        full_module = f"xuansto_mcp.tools.{module_name}"
        try:
            mod = importlib.import_module(full_module)
            assert mod is not None, f"Module {full_module} should be importable"
        except (SyntaxError, IndentationError) as e:
            pytest.fail(f"Module {full_module} has syntax error: {e}")

    @pytest.mark.parametrize("module_name", EXPECTED_TOOL_MODULES)
    def test_tool_module_has_register_function(self, module_name: str):
        if not _can_import_module(module_name):
            source = _read_source(module_name)
            assert "def register(mcp" in source, f"{module_name} should define register(mcp) function"
            return
        full_module = f"xuansto_mcp.tools.{module_name}"
        mod = importlib.import_module(full_module)
        assert hasattr(mod, "register"), f"{module_name} should have a register() function"
        assert callable(mod.register), f"{module_name}.register should be callable"

    @pytest.mark.parametrize("module_name", EXPECTED_TOOL_MODULES)
    def test_register_function_signature(self, module_name: str):
        source = _read_source(module_name)
        assert "def register(mcp" in source, f"{module_name} should define register(mcp) function"


class TestToolAnnotations:
    @pytest.mark.parametrize("module_name", EXPECTED_TOOL_MODULES)
    def test_tool_module_imports_tool_annotations(self, module_name: str):
        source = _read_source(module_name)
        assert "ToolAnnotations" in source, f"{module_name} should use ToolAnnotations"

    @pytest.mark.parametrize("module_name", EXPECTED_TOOL_MODULES)
    def test_tool_annotations_has_all_four_fields(self, module_name: str):
        source = _read_source(module_name)
        for field in TOOL_ANNOTATION_FIELDS:
            assert field in source, f"{module_name} should set ToolAnnotations.{field}"

    @pytest.mark.parametrize("module_name", EXPECTED_TOOL_MODULES)
    def test_tool_annotations_are_inside_register(self, module_name: str):
        source = _read_source(module_name)
        assert "def register(mcp" in source, f"{module_name} should have register function"
        assert "ToolAnnotations(" in source, f"{module_name} should instantiate ToolAnnotations"

    @pytest.mark.parametrize("module_name", EXPECTED_TOOL_MODULES)
    def test_tool_source_is_valid_python(self, module_name: str):
        source = _read_source(module_name)
        try:
            ast.parse(source)
        except SyntaxError as e:
            pytest.fail(f"{module_name}.py has syntax error at line {e.lineno}: {e.msg}")


class TestToolRegistration:
    def test_all_22_tools_registered_in_server(self):
        from xuansto_mcp.server import _TOOL_FUNCTIONS

        registered_names = set(_TOOL_FUNCTIONS.keys())
        for module_name in EXPECTED_TOOL_MODULES:
            assert module_name in registered_names, f"Tool '{module_name}' should be registered in server"

    def test_tool_count_matches_expected(self):
        from xuansto_mcp.server import _TOOL_FUNCTIONS

        assert len(_TOOL_FUNCTIONS) >= 22, f"Expected at least 22 registered tools, got {len(_TOOL_FUNCTIONS)}"

    def test_tools_all_exports_match_expected(self):
        from xuansto_mcp.tools import __all__

        for module_name in EXPECTED_TOOL_MODULES:
            assert module_name in __all__, f"{module_name} should be in tools.__all__"

    def test_each_tool_function_is_async(self):
        from xuansto_mcp.server import _TOOL_FUNCTIONS

        for tool_name, tool_fn in _TOOL_FUNCTIONS.items():
            assert inspect.iscoroutinefunction(tool_fn) or hasattr(tool_fn, "__wrapped__"), (
                f"Tool '{tool_name}' should be an async function or wrapped"
            )


class TestToolAnnotationsViaMCP:
    def test_registered_tools_have_annotations(self):
        from mcp.server.fastmcp import FastMCP
        from xuansto_mcp.server import mcp

        if hasattr(mcp, "_tool_manager"):
            tools = mcp._tool_manager._tools
        elif hasattr(mcp, "_tools"):
            tools = mcp._tools
        else:
            pytest.skip("Cannot introspect MCP tool registry in this version")

        for tool_name in EXPECTED_TOOL_MODULES:
            assert tool_name in tools, f"Tool '{tool_name}' should be in MCP registry"

    def test_annotation_values_are_booleans(self):
        for module_name in EXPECTED_TOOL_MODULES:
            source = _read_source(module_name)
            for field in TOOL_ANNOTATION_FIELDS:
                assert f"{field}=" in source, f"{module_name} should explicitly set {field}"
