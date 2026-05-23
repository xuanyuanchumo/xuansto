from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "src"))

from xuansto_mcp import __version__
from xuansto_mcp.core.config import MCP_API_VERSION, MCP_MIN_SUPPORTED_VERSION


SPEC_LOCKS_DIR = Path(__file__).resolve().parent.parent.parent / "spec-locks"


def _load_spec_lock(filename: str) -> dict:
    path = SPEC_LOCKS_DIR / filename
    if not path.exists():
        pytest.skip(f"spec-locks/{filename} not found")
    return json.loads(path.read_text(encoding="utf-8"))


class TestVersionCompatibilityMatrix:
    def test_server_version_matches_pyproject(self):
        pyproject_path = Path(__file__).resolve().parent.parent.parent / "pyproject.toml"
        import tomllib
        with open(pyproject_path, "rb") as f:
            pyproject = tomllib.load(f)
        pyproject_version = pyproject["project"]["version"]
        assert __version__ == pyproject_version

    def test_api_version_matches_spec_lock(self):
        api_contract = _load_spec_lock("api-contract-version.json")
        assert MCP_API_VERSION == api_contract["current_version"]

    def test_min_supported_version_matches_spec_lock(self):
        api_contract = _load_spec_lock("api-contract-version.json")
        assert MCP_MIN_SUPPORTED_VERSION == api_contract["min_supported_version"]

    def test_api_version_is_semver(self):
        parts = MCP_API_VERSION.split(".")
        assert len(parts) == 3
        for part in parts:
            assert part.isdigit()

    def test_min_supported_version_is_semver(self):
        parts = MCP_MIN_SUPPORTED_VERSION.split(".")
        assert len(parts) == 3
        for part in parts:
            assert part.isdigit()

    def test_current_version_gte_min_supported(self):
        current = [int(p) for p in MCP_API_VERSION.split(".")]
        minimum = [int(p) for p in MCP_MIN_SUPPORTED_VERSION.split(".")]
        assert current >= minimum

    def test_version_history_exists_in_spec_lock(self):
        api_contract = _load_spec_lock("api-contract-version.json")
        versions = [entry["version"] for entry in api_contract["version_history"]]
        assert MCP_API_VERSION in versions
        assert MCP_MIN_SUPPORTED_VERSION in versions

    def test_compatibility_rules_exist(self):
        api_contract = _load_spec_lock("api-contract-version.json")
        rules = api_contract["compatibility_rules"]
        assert "major_version_match" in rules
        assert "min_supported_match" in rules
        assert "major_version_mismatch" in rules

    def test_skill_definition_schema_valid(self):
        schema = _load_spec_lock("skill-definition-schema.json")
        assert schema["required"] == ["name", "version", "description", "triggers", "tools"]
        assert schema["type"] == "object"

    def test_tool_parameter_schemas_covers_all_16_tools(self):
        schemas = _load_spec_lock("tool-parameter-schemas.json")
        tool_schemas = schemas["tool_schemas"]
        expected_tools = [
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
            "server_health",
            "context_compress",
            "decision_log",
            "token_budget",
            "project_init",
        ]
        for tool_name in expected_tools:
            assert tool_name in tool_schemas, f"Missing tool schema: {tool_name}"
        assert len(tool_schemas) == 16

    def test_tool_parameter_schemas_definitions_match_pydantic(self):
        schemas = _load_spec_lock("tool-parameter-schemas.json")
        from xuansto_mcp.models.schemas import (
            SkillAnalyzeInput,
            KnowledgeSearchInput,
            QualityGateCheckInput,
            SpecDriftDetectInput,
            SecurityScanInput,
            CodeSimplifyInput,
            SessionManageInput,
            WorkflowDispatchInput,
            AgentStatusInput,
            HookManageInput,
            ResourceLoadStatusInput,
            ServerHealthInput,
            ContextCompressInput,
            DecisionLogInput,
            TokenBudgetInput,
            ProjectInitInput,
        )
        model_map = {
            "SkillAnalyzeInput": SkillAnalyzeInput,
            "KnowledgeSearchInput": KnowledgeSearchInput,
            "QualityGateCheckInput": QualityGateCheckInput,
            "SpecDriftDetectInput": SpecDriftDetectInput,
            "SecurityScanInput": SecurityScanInput,
            "CodeSimplifyInput": CodeSimplifyInput,
            "SessionManageInput": SessionManageInput,
            "WorkflowDispatchInput": WorkflowDispatchInput,
            "AgentStatusInput": AgentStatusInput,
            "HookManageInput": HookManageInput,
            "ResourceLoadStatusInput": ResourceLoadStatusInput,
            "ServerHealthInput": ServerHealthInput,
            "ContextCompressInput": ContextCompressInput,
            "DecisionLogInput": DecisionLogInput,
            "TokenBudgetInput": TokenBudgetInput,
            "ProjectInitInput": ProjectInitInput,
        }
        definitions = schemas["definitions"]
        for def_name, model_cls in model_map.items():
            assert def_name in definitions, f"Missing definition: {def_name}"
            schema_props = set(definitions[def_name].get("properties", {}).keys())
            pydantic_fields = set(model_cls.model_fields.keys())
            assert schema_props == pydantic_fields, (
                f"{def_name}: schema has {schema_props - pydantic_fields} extra, "
                f"pydantic has {pydantic_fields - schema_props} extra"
            )

    def test_degradation_chain_covers_all_tools(self):
        from xuansto_mcp.core.degradation import FALLBACK_MAP
        expected_tools = [
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
            "decision_log",
            "token_budget",
            "project_init",
        ]
        for tool_name in expected_tools:
            assert tool_name in FALLBACK_MAP, f"Missing fallback for tool: {tool_name}"
