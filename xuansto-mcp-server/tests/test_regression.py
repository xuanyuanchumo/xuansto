from __future__ import annotations

from pathlib import Path

import pytest

SRC_ROOT = Path(__file__).resolve().parent.parent / "src" / "xuansto_mcp"
DATA_DIR = SRC_ROOT / "data"
TOOLS_DIR = SRC_ROOT / "tools"
CORE_DIR = SRC_ROOT / "core"


class TestP0_01_DegradationModeAvailable:

    def test_degradation_module_exists(self):
        degr_path = CORE_DIR / "degradation.py"
        assert degr_path.exists(), "degradation.py should exist in core/"

    def test_degradation_has_fallback_chain(self):
        from xuansto_mcp.core.degradation import FALLBACK_MAP, DegradationExecutor

        assert isinstance(FALLBACK_MAP, dict)
        assert len(FALLBACK_MAP) > 0

        key_tools = ["skill_analyze", "knowledge_search", "quality_gate_check", "security_scan"]
        for tool in key_tools:
            assert tool in FALLBACK_MAP, f"FALLBACK_MAP should contain {tool}"

    def test_degradation_executor_exists(self):
        from xuansto_mcp.core.degradation import DegradationExecutor
        executor = DegradationExecutor()
        assert hasattr(executor, "execute")
        assert hasattr(executor, "execute_sync")

    def test_degradation_manager_exists(self):
        from xuansto_mcp.core.degradation import DegradationManager
        mgr = DegradationManager(health_interval=9999)
        assert hasattr(mgr, "check_and_degrade")
        assert hasattr(mgr, "attempt_recovery")
        assert hasattr(mgr, "register_component")


class TestP0_02_ReferencesDirectoryComplete:

    def test_references_dir_exists(self):
        from xuansto_mcp.core.config import REFERENCES_DIR, DATA_DIR
        ref_dir = DATA_DIR / "references"
        if not (ref_dir.exists() or REFERENCES_DIR.exists()):
            pytest.skip("references/ directory not available in test environment")

    def test_knowledge_general_dir_has_content(self):
        from xuansto_mcp.core.config import KNOWLEDGE_GENERAL_DIR
        if KNOWLEDGE_GENERAL_DIR.exists():
            md_files = list(KNOWLEDGE_GENERAL_DIR.rglob("*.md"))
            assert len(md_files) > 0, "knowledge/general/ should contain reference docs"

    def test_knowledge_workspace_dir_has_content(self):
        from xuansto_mcp.core.config import KNOWLEDGE_WORKSPACE_DIR
        if KNOWLEDGE_WORKSPACE_DIR.exists():
            md_files = list(KNOWLEDGE_WORKSPACE_DIR.rglob("*.md"))
            assert len(md_files) > 0, "knowledge/workspace/ should contain reference docs"

    def test_skill_config_yaml_exists(self):
        config_path = DATA_DIR / ".skill-config.yaml"
        assert config_path.exists(), ".skill-config.yaml should exist in data/"

    def test_xuansto_config_yaml_exists(self):
        config_path = DATA_DIR / ".xuansto-config.yaml"
        assert config_path.exists(), ".xuansto-config.yaml should exist in data/"


class TestP1_01_VersionConsistency:

    def test_mcp_api_version_matches_skill_version(self):
        from xuansto_mcp.core.config import MCP_API_VERSION
        from xuansto_mcp import __version__

        assert MCP_API_VERSION is not None
        assert __version__ is not None

        mcp_parts = MCP_API_VERSION.split(".")
        skill_parts = __version__.split(".")

        assert len(mcp_parts) == 3, "MCP_API_VERSION should be semver"
        assert len(skill_parts) == 3, "__version__ should be semver"

        assert int(mcp_parts[0]) >= 2, "MCP API major version should be >= 2"
        assert int(skill_parts[0]) >= 2, "Skill major version should be >= 2"

    def test_version_parse_function(self):
        from xuansto_mcp.core.config import parse_version

        v = parse_version("3.0.0")
        assert v == (3, 0, 0)

        v = parse_version("v2.1.5")
        assert v == (2, 1, 5)

        v = parse_version("8.0.0")
        assert v == (8, 0, 0)


class TestP1_04_ToolsSubpackageSplit:

    def test_tools_is_package(self):
        init_path = TOOLS_DIR / "__init__.py"
        assert init_path.exists(), "tools/ should be a Python package with __init__.py"

    def test_tools_subpackage_has_modules(self):
        expected_modules = [
            "skill_analyze.py",
            "knowledge_search.py",
            "knowledge_inject.py",
            "quality_gate_check.py",
            "security_scan.py",
            "resource_load_status.py",
            "agent_status.py",
            "hook_manage.py",
            "session_manage.py",
            "workflow_dispatch.py",
            "code_simplify.py",
            "context_compress.py",
            "server_health.py",
            "decision_log.py",
            "token_budget.py",
            "project_init.py",
            "metrics_report.py",
            "config_manage.py",
            "spec_drift_detect.py",
            "agent_manage.py",
        ]
        for module_name in expected_modules:
            module_path = TOOLS_DIR / module_name
            assert module_path.exists(), f"tools/{module_name} should exist"

    def test_tools_all_exports(self):
        from xuansto_mcp.tools import __all__

        assert isinstance(__all__, list)
        assert len(__all__) >= 15

        key_tools = ["skill_analyze", "knowledge_search", "resource_load_status"]
        for tool in key_tools:
            assert tool in __all__, f"{tool} should be in tools.__all__"


class TestP1_05_DegradationMappingFromConfig:

    def test_fallback_config_yaml_exists(self):
        config_path = DATA_DIR / "fallback_config.yaml"
        assert config_path.exists(), "fallback_config.yaml should exist in data/"

    def test_fallback_config_has_fallback_map(self):
        config_path = DATA_DIR / "fallback_config.yaml"
        if not config_path.exists():
            pytest.skip("fallback_config.yaml not found")

        import yaml
        raw = yaml.safe_load(config_path.read_text(encoding="utf-8"))
        assert isinstance(raw, dict)
        assert "fallback_map" in raw, "fallback_config.yaml should have fallback_map key"

        fallback_map = raw["fallback_map"]
        assert isinstance(fallback_map, dict)
        assert len(fallback_map) > 0

    def test_degradation_loads_from_yaml(self):
        from xuansto_mcp.core.degradation import (
            _load_fallback_config_from_yaml,
            _build_fallback_map_from_yaml,
            _INLINE_FALLBACK_MAP,
        )

        yaml_config = _load_fallback_config_from_yaml()
        if yaml_config is None:
            pytest.skip("fallback_config.yaml not loaded (may not exist in test env)")

        assert isinstance(yaml_config, dict)
        built_map = _build_fallback_map_from_yaml(yaml_config)
        assert isinstance(built_map, dict)
        assert len(built_map) > 0

    def test_degradation_fallback_map_not_empty(self):
        from xuansto_mcp.core.degradation import FALLBACK_MAP

        assert len(FALLBACK_MAP) > 0
        for tool_name, fn in FALLBACK_MAP.items():
            assert callable(fn), f"FALLBACK_MAP[{tool_name}] should be callable"


class TestP1_06_SkillMCPLoadingStateSync:

    def test_resource_load_status_module_exists(self):
        rls_path = TOOLS_DIR / "resource_load_status.py"
        assert rls_path.exists(), "resource_load_status.py should exist in tools/"

    def test_phase_system_exists(self):
        from xuansto_mcp.tools.resource_load_status import (
            PHASE_NAMES,
            PHASE_SKELETON,
            PHASE_FUNCTIONAL,
            PHASE_ENHANCED,
            PHASE_FULL,
            advance_phase,
            can_advance_to,
        )

        assert PHASE_SKELETON == 0
        assert PHASE_FUNCTIONAL == 1
        assert PHASE_ENHANCED == 2
        assert PHASE_FULL == 3
        assert PHASE_NAMES == {0: "skeleton", 1: "functional", 2: "enhanced", 3: "full"}

    def test_phase_state_persistence(self):
        from xuansto_mcp.tools.resource_load_status import (
            _get_state_file,
            _save_resource_state,
            _load_resource_state,
        )

        state_file = _get_state_file()
        assert state_file is not None
        assert state_file.name == "resource_state.json"

    def test_phase_available_functions_sync(self):
        from xuansto_mcp.tools.resource_load_status import (
            PHASE_AVAILABLE_FUNCTIONS,
            PHASE_SKELETON,
            PHASE_FULL,
        )

        skeleton_funcs = PHASE_AVAILABLE_FUNCTIONS[PHASE_SKELETON]
        full_funcs = PHASE_AVAILABLE_FUNCTIONS[PHASE_FULL]

        assert skeleton_funcs["command_routing"] is True
        assert skeleton_funcs["command_execution"] is False

        assert full_funcs["command_routing"] is True
        assert full_funcs["command_execution"] is True
        assert full_funcs["knowledge_search"] is True
        assert full_funcs["full_scripts"] is True

    def test_phase_available_features_sync(self):
        from xuansto_mcp.tools.resource_load_status import PHASE_AVAILABLE_FEATURES

        assert "skeleton" in PHASE_AVAILABLE_FEATURES
        assert "functional" in PHASE_AVAILABLE_FEATURES
        assert "enhanced" in PHASE_AVAILABLE_FEATURES
        assert "full" in PHASE_AVAILABLE_FEATURES

        for phase_name, features in PHASE_AVAILABLE_FEATURES.items():
            assert "available" in features
            assert "unavailable" in features

        assert len(PHASE_AVAILABLE_FEATURES["full"]["unavailable"]) == 0

    def test_degradation_manager_and_phase_system_integration(self):
        from xuansto_mcp.core.degradation import DegradationManager
        from xuansto_mcp.tools.resource_load_status import (
            PHASE_AVAILABLE_FUNCTIONS,
            PHASE_SKELETON,
        )

        mgr = DegradationManager(health_interval=9999)

        mgr.register_component(
            "search_engine",
            check_fn=lambda: True,
            recover_fn=lambda: True,
            levels=["chromadb", "sqlite_fts", "keyword"],
        )

        status = mgr.get_status()
        assert status["overall_level"] == "L1_NORMAL"

        skeleton_funcs = PHASE_AVAILABLE_FUNCTIONS[PHASE_SKELETON]
        assert skeleton_funcs["knowledge_search"] is False
