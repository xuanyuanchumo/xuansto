import sys
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from xuansto_mcp.core.degradation import (
    FALLBACK_MAP,
    _fallback_success,
    _fallback_error,
    _standardize_result,
    skill_analyze_fallback,
    knowledge_search_fallback,
    quality_gate_fallback,
    spec_drift_fallback,
    security_scan_fallback,
    code_simplify_fallback,
    session_manage_fallback,
    workflow_dispatch_fallback,
    agent_status_fallback,
    hook_manage_fallback,
    resource_load_status_fallback,
    context_compress_fallback,
    server_health_fallback,
)

SCRIPT_OK = {"error": False, "data": {"result": "mock"}}
SCRIPT_ERR = {"error": True, "code": "SCRIPT_NOT_FOUND", "message": "脚本不存在", "fallback": True}

ALL_13_TOOL_NAMES = list(FALLBACK_MAP.keys())


def _get_source(result):
    if result.get("error"):
        return result.get("details", {}).get("source")
    data = result.get("data", {})
    if isinstance(data, dict):
        return data.get("source")
    return None


class TestHelperFunctions:
    def test_fallback_success_format(self):
        result = _fallback_success("test_tool", {"key": "val"})
        assert result["error"] is False
        assert "data" in result
        assert result["data"]["tool"] == "test_tool"
        assert result["data"]["source"] == "fallback"
        assert result["data"]["status"] == "degraded"
        assert result["data"]["note"] == "主工具不可用，使用降级响应"
        assert result["data"]["key"] == "val"

    def test_fallback_success_preserves_existing_status(self):
        result = _fallback_success("test_tool", {"status": "unknown"})
        assert result["data"]["status"] == "unknown"

    def test_fallback_success_preserves_existing_note(self):
        result = _fallback_success("test_tool", {"note": "自定义备注"})
        assert result["data"]["note"] == "自定义备注"

    def test_fallback_success_with_degradation_level(self):
        result = _fallback_success("test_tool", degradation_level="inline")
        assert result.get("degradation_level") == "inline"

    def test_fallback_error_format(self):
        result = _fallback_error("test_tool", "ERR_CODE", "错误消息")
        assert result["error"] is True
        assert result["code"] == "ERR_CODE"
        assert result["message"] == "错误消息"
        assert result["details"]["tool"] == "test_tool"
        assert result["details"]["source"] == "fallback"

    def test_standardize_result_success(self):
        raw = {"error": False, "data": {"items": [1, 2]}, "fallback": True}
        result = _standardize_result(raw, "my_tool")
        assert result["error"] is False
        assert result["data"]["source"] == "fallback"
        assert result["data"]["tool"] == "my_tool"
        assert result["data"]["items"] == [1, 2]

    def test_standardize_result_error(self):
        raw = {"error": True, "code": "TIMEOUT", "message": "超时", "fallback": True}
        result = _standardize_result(raw, "my_tool")
        assert result["error"] is True
        assert result["code"] == "TIMEOUT"
        assert result["details"]["source"] == "fallback"
        assert result["details"]["tool"] == "my_tool"

    def test_standardize_result_non_dict_data(self):
        raw = {"error": False, "data": "plain_string", "fallback": True}
        result = _standardize_result(raw, "my_tool")
        assert result["error"] is False
        assert result["data"]["result"] == "plain_string"
        assert result["data"]["source"] == "fallback"


class TestFallbackMapCompleteness:
    def test_fallback_map_has_13_entries(self):
        assert len(FALLBACK_MAP) == 13

    def test_all_13_tool_names_present(self):
        expected = {
            "skill_analyze",
            "knowledge_search",
            "quality_gate_check",
            "spec_drift_detect",
            "security_scan",
            "code_simplify",
            "session_manage",
            "workflow_dispatch",
            "agent_status",
            "hook_manage",
            "resource_load_status",
            "context_compress",
            "server_health",
        }
        assert set(FALLBACK_MAP.keys()) == expected


class TestAllFallbacksHaveErrorKey:
    @patch("xuansto_mcp.core.degradation.run_script_fallback", return_value=SCRIPT_OK)
    def test_script_based_fallbacks(self, mock_rs):
        script_tools = [
            ("skill_analyze", skill_analyze_fallback, {"skill_path": "/tmp/test"}),
            ("knowledge_search", knowledge_search_fallback, {"query": "test"}),
            ("session_manage", session_manage_fallback, {"action": "list"}),
            ("agent_status", agent_status_fallback, {}),
            ("context_compress", context_compress_fallback, {}),
        ]
        for name, fn, kwargs in script_tools:
            result = fn(**kwargs)
            assert "error" in result, f"{name}: missing 'error' key"

    def test_server_health_has_error_key(self):
        result = server_health_fallback()
        assert "error" in result

    def test_resource_load_status_has_error_key(self):
        result = resource_load_status_fallback()
        assert "error" in result

    @patch("xuansto_mcp.core.degradation.run_script_fallback", return_value=SCRIPT_OK)
    def test_hook_manage_has_error_key(self, mock_rs):
        result = hook_manage_fallback()
        assert "error" in result

    @patch("xuansto_mcp.core.degradation.run_script_fallback", return_value=SCRIPT_OK)
    def test_quality_gate_has_error_key(self, mock_rs):
        result = quality_gate_fallback(gate_ids=[])
        assert "error" in result

    @patch("xuansto_mcp.core.degradation.run_script_fallback", return_value=SCRIPT_OK)
    def test_workflow_dispatch_status_has_error_key(self, mock_rs):
        result = workflow_dispatch_fallback(action="status")
        assert "error" in result

    def test_workflow_dispatch_abort_has_error_key(self):
        result = workflow_dispatch_fallback(action="abort")
        assert "error" in result

    def test_workflow_dispatch_unknown_has_error_key(self):
        result = workflow_dispatch_fallback(action="nonexistent")
        assert "error" in result


class TestAllFallbacksIncludeSourceFallback:
    @patch("xuansto_mcp.core.degradation.run_script_fallback", return_value=SCRIPT_OK)
    def test_script_based_success_has_source(self, mock_rs):
        script_tools = [
            ("skill_analyze", skill_analyze_fallback, {"skill_path": "/tmp/test"}),
            ("knowledge_search", knowledge_search_fallback, {"query": "test"}),
            ("session_manage", session_manage_fallback, {"action": "list"}),
            ("agent_status", agent_status_fallback, {}),
            ("context_compress", context_compress_fallback, {}),
        ]
        for name, fn, kwargs in script_tools:
            result = fn(**kwargs)
            source = _get_source(result)
            assert source == "fallback", f"{name}: expected source=fallback, got {source}"

    def test_server_health_has_source_fallback(self):
        result = server_health_fallback()
        assert result["data"]["source"] == "fallback"

    def test_resource_load_status_has_source_fallback(self):
        result = resource_load_status_fallback()
        assert result["data"]["source"] == "fallback"

    @patch("xuansto_mcp.core.degradation.run_script_fallback", return_value=SCRIPT_OK)
    def test_hook_manage_has_source_fallback(self, mock_rs):
        result = hook_manage_fallback()
        assert result["data"]["source"] == "fallback"

    @patch("xuansto_mcp.core.degradation.run_script_fallback", return_value=SCRIPT_OK)
    def test_quality_gate_has_source_fallback(self, mock_rs):
        result = quality_gate_fallback(gate_ids=[])
        assert result["data"]["source"] == "fallback"

    @patch("xuansto_mcp.core.degradation.run_script_fallback", return_value=SCRIPT_OK)
    def test_workflow_dispatch_status_has_source_fallback(self, mock_rs):
        result = workflow_dispatch_fallback(action="status")
        assert result["data"]["source"] == "fallback"

    def test_workflow_dispatch_abort_has_source_fallback(self):
        result = workflow_dispatch_fallback(action="abort")
        assert result["data"]["source"] == "fallback"

    def test_workflow_dispatch_unknown_error_has_source_fallback(self):
        result = workflow_dispatch_fallback(action="nonexistent")
        assert result["details"]["source"] == "fallback"

    @patch("xuansto_mcp.core.degradation.run_script_fallback", return_value=SCRIPT_ERR)
    def test_script_error_has_source_fallback(self, mock_rs):
        result = skill_analyze_fallback(skill_path="/tmp/test")
        assert result["error"] is True
        assert result["details"]["source"] == "fallback"


class TestFormatConsistency:
    def _assert_success_format(self, result, tool_name):
        assert isinstance(result, dict), f"{tool_name}: result is not a dict"
        assert "error" in result, f"{tool_name}: missing 'error' key"
        assert result["error"] is False, f"{tool_name}: expected error=False"
        assert "data" in result, f"{tool_name}: missing 'data' key"
        assert isinstance(result["data"], dict), f"{tool_name}: data is not a dict"
        assert result["data"]["source"] == "fallback", f"{tool_name}: missing source=fallback"
        assert result["data"]["tool"] == tool_name, f"{tool_name}: tool name mismatch"

    def _assert_error_format(self, result, tool_name):
        assert isinstance(result, dict), f"{tool_name}: result is not a dict"
        assert "error" in result, f"{tool_name}: missing 'error' key"
        assert result["error"] is True, f"{tool_name}: expected error=True"
        assert "code" in result, f"{tool_name}: missing 'code' in error response"
        assert "message" in result, f"{tool_name}: missing 'message' in error response"
        assert "details" in result, f"{tool_name}: missing 'details' in error response"
        assert result["details"]["source"] == "fallback", f"{tool_name}: missing source=fallback in details"

    @patch("xuansto_mcp.core.degradation.run_script_fallback", return_value=SCRIPT_OK)
    def test_skill_analyze_success_format(self, mock_rs):
        result = skill_analyze_fallback(skill_path="/tmp/test")
        self._assert_success_format(result, "skill_analyze")

    @patch("xuansto_mcp.core.degradation.run_script_fallback", return_value=SCRIPT_OK)
    def test_knowledge_search_success_format(self, mock_rs):
        result = knowledge_search_fallback(query="test")
        self._assert_success_format(result, "knowledge_search")

    @patch("xuansto_mcp.core.degradation.run_script_fallback", return_value=SCRIPT_OK)
    def test_session_manage_success_format(self, mock_rs):
        result = session_manage_fallback(action="list")
        self._assert_success_format(result, "session_manage")

    @patch("xuansto_mcp.core.degradation.run_script_fallback", return_value=SCRIPT_OK)
    def test_agent_status_success_format(self, mock_rs):
        result = agent_status_fallback()
        self._assert_success_format(result, "agent_status")

    @patch("xuansto_mcp.core.degradation.run_script_fallback", return_value=SCRIPT_OK)
    def test_context_compress_success_format(self, mock_rs):
        result = context_compress_fallback()
        self._assert_success_format(result, "context_compress")

    @patch("xuansto_mcp.core.degradation.run_script_fallback", return_value=SCRIPT_OK)
    def test_hook_manage_success_format(self, mock_rs):
        result = hook_manage_fallback()
        self._assert_success_format(result, "hook_manage")

    @patch("xuansto_mcp.core.degradation.run_script_fallback", return_value=SCRIPT_OK)
    def test_quality_gate_success_format(self, mock_rs):
        result = quality_gate_fallback(gate_ids=[])
        self._assert_success_format(result, "quality_gate_check")

    @patch("xuansto_mcp.core.degradation.run_script_fallback", return_value=SCRIPT_OK)
    def test_workflow_dispatch_start_success_format(self, mock_rs):
        result = workflow_dispatch_fallback(action="start")
        self._assert_success_format(result, "workflow_dispatch")

    def test_workflow_dispatch_status_success_format(self):
        result = workflow_dispatch_fallback(action="status")
        self._assert_success_format(result, "workflow_dispatch")

    def test_workflow_dispatch_abort_success_format(self):
        result = workflow_dispatch_fallback(action="abort")
        self._assert_success_format(result, "workflow_dispatch")

    def test_workflow_dispatch_unknown_error_format(self):
        result = workflow_dispatch_fallback(action="bad_action")
        self._assert_error_format(result, "workflow_dispatch")

    def test_server_health_success_format(self):
        result = server_health_fallback()
        self._assert_success_format(result, "server_health")

    def test_resource_load_status_success_format(self):
        result = resource_load_status_fallback()
        self._assert_success_format(result, "resource_load_status")

    @patch("xuansto_mcp.core.degradation.run_script_fallback", return_value=SCRIPT_ERR)
    def test_skill_analyze_error_format(self, mock_rs):
        result = skill_analyze_fallback(skill_path="/tmp/test")
        self._assert_error_format(result, "skill_analyze")

    @patch("xuansto_mcp.core.degradation.run_script_fallback", return_value=SCRIPT_ERR)
    def test_knowledge_search_error_format(self, mock_rs):
        result = knowledge_search_fallback(query="test")
        self._assert_error_format(result, "knowledge_search")

    @patch("xuansto_mcp.core.degradation.run_script_fallback", return_value=SCRIPT_ERR)
    def test_session_manage_error_format(self, mock_rs):
        result = session_manage_fallback(action="list")
        self._assert_error_format(result, "session_manage")


class TestFallbackDataHasToolField:
    @patch("xuansto_mcp.core.degradation.run_script_fallback", return_value=SCRIPT_OK)
    def test_all_success_responses_have_tool_field(self, mock_rs):
        script_tools = [
            ("skill_analyze", skill_analyze_fallback, {"skill_path": "/tmp/test"}),
            ("knowledge_search", knowledge_search_fallback, {"query": "test"}),
            ("session_manage", session_manage_fallback, {"action": "list"}),
            ("agent_status", agent_status_fallback, {}),
            ("context_compress", context_compress_fallback, {}),
            ("hook_manage", hook_manage_fallback, {}),
            ("quality_gate_check", quality_gate_fallback, {"gate_ids": []}),
            ("workflow_dispatch", workflow_dispatch_fallback, {"action": "status"}),
        ]
        for name, fn, kwargs in script_tools:
            result = fn(**kwargs)
            if not result.get("error"):
                assert result["data"].get("tool") == name, f"{name}: tool name mismatch in data"

    def test_no_script_tools_have_tool_field(self):
        direct_tools = [
            ("server_health", server_health_fallback, {}),
            ("resource_load_status", resource_load_status_fallback, {}),
            ("workflow_dispatch", workflow_dispatch_fallback, {"action": "abort"}),
        ]
        for name, fn, kwargs in direct_tools:
            result = fn(**kwargs)
            if not result.get("error"):
                assert result["data"].get("tool") == name, f"{name}: tool name mismatch in data"


class TestFallbackDataHasNoteField:
    def test_server_health_has_note(self):
        result = server_health_fallback()
        assert "note" in result["data"]

    def test_resource_load_status_fallback_path_has_custom_note(self):
        result = resource_load_status_fallback()
        assert "note" in result["data"]

    @patch("xuansto_mcp.core.degradation.run_script_fallback", return_value=SCRIPT_OK)
    def test_script_based_has_note(self, mock_rs):
        result = skill_analyze_fallback(skill_path="/tmp/test")
        assert "note" in result["data"]
