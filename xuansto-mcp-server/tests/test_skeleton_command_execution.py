from __future__ import annotations

import pytest

from xuansto_mcp.tools.resource_load_status import (
    SKELETON_ALLOWED_COMMANDS,
    PHASE_SKELETON,
    PHASE_FUNCTIONAL,
    PHASE_ENHANCED,
    PHASE_FULL,
    PHASE_NAMES,
    _PHASE_AVAILABLE_COMMANDS,
    _current_phase,
    _phase_lock,
    can_execute_command,
    advance_phase,
)


@pytest.fixture(autouse=True)
def reset_phase_state():
    import xuansto_mcp.tools.resource_load_status as mod
    with _phase_lock:
        original = mod._current_phase
        mod._current_phase = 0
    yield
    with _phase_lock:
        mod._current_phase = original


class TestSkeletonAllowedCommandsConstant:
    def test_skeleton_allowed_commands_defined(self):
        assert SKELETON_ALLOWED_COMMANDS == ["/status", "/help", "/budget"]

    def test_skeleton_allowed_commands_count(self):
        assert len(SKELETON_ALLOWED_COMMANDS) == 3

    def test_phase_0_available_commands_matches_skeleton_allowed(self):
        assert _PHASE_AVAILABLE_COMMANDS[0] == SKELETON_ALLOWED_COMMANDS


class TestCanExecuteCommandInSkeletonPhase:
    def test_status_allowed_in_skeleton(self):
        result = can_execute_command("/status")
        assert result["allowed"] is True
        assert result["command"] == "/status"
        assert result["phase"] == PHASE_SKELETON
        assert result["phase_name"] == "skeleton"
        assert result["reason"] == "skeleton_allowed_command"

    def test_help_allowed_in_skeleton(self):
        result = can_execute_command("/help")
        assert result["allowed"] is True
        assert result["command"] == "/help"
        assert result["reason"] == "skeleton_allowed_command"

    def test_budget_allowed_in_skeleton(self):
        result = can_execute_command("/budget")
        assert result["allowed"] is True
        assert result["command"] == "/budget"
        assert result["reason"] == "skeleton_allowed_command"

    def test_init_blocked_in_skeleton(self):
        result = can_execute_command("/init")
        assert result["allowed"] is False
        assert result["command"] == "/init"
        assert result["phase"] == PHASE_SKELETON
        assert result["reason"] == "command_not_available_in_skeleton"
        assert "skeleton_allowed_commands" in result
        assert result["skeleton_allowed_commands"] == SKELETON_ALLOWED_COMMANDS

    def test_implement_blocked_in_skeleton(self):
        result = can_execute_command("/implement")
        assert result["allowed"] is False
        assert result["reason"] == "command_not_available_in_skeleton"

    def test_sprint_blocked_in_skeleton(self):
        result = can_execute_command("/sprint")
        assert result["allowed"] is False
        assert result["reason"] == "command_not_available_in_skeleton"

    def test_audit_blocked_in_skeleton(self):
        result = can_execute_command("/audit")
        assert result["allowed"] is False

    def test_unknown_command_blocked_in_skeleton(self):
        result = can_execute_command("/nonexistent")
        assert result["allowed"] is False
        assert result["reason"] == "command_not_available_in_skeleton"

    def test_blocked_command_includes_upgrade_hint(self):
        result = can_execute_command("/init")
        assert "upgrade_hint" in result
        assert len(result["upgrade_hint"]) > 0


class TestCanExecuteCommandInFunctionalPhase:
    @pytest.fixture(autouse=True)
    def set_functional_phase(self):
        import xuansto_mcp.tools.resource_load_status as mod
        with _phase_lock:
            mod._current_phase = PHASE_FUNCTIONAL
        yield

    def test_status_allowed_in_functional(self):
        result = can_execute_command("/status")
        assert result["allowed"] is True
        assert result["phase"] == PHASE_FUNCTIONAL

    def test_init_allowed_in_functional(self):
        result = can_execute_command("/init")
        assert result["allowed"] is True

    def test_sprint_allowed_in_functional(self):
        result = can_execute_command("/sprint")
        assert result["allowed"] is True

    def test_audit_blocked_in_functional(self):
        result = can_execute_command("/audit")
        assert result["allowed"] is False
        assert result["reason"] == "command_not_in_available_list"

    def test_loop_blocked_in_functional(self):
        result = can_execute_command("/loop")
        assert result["allowed"] is False


class TestCanExecuteCommandInEnhancedPhase:
    @pytest.fixture(autouse=True)
    def set_enhanced_phase(self):
        import xuansto_mcp.tools.resource_load_status as mod
        with _phase_lock:
            mod._current_phase = PHASE_ENHANCED
        yield

    def test_audit_allowed_in_enhanced(self):
        result = can_execute_command("/audit")
        assert result["allowed"] is True
        assert result["phase"] == PHASE_ENHANCED

    def test_loop_allowed_in_enhanced(self):
        result = can_execute_command("/loop")
        assert result["allowed"] is True

    def test_status_allowed_in_enhanced(self):
        result = can_execute_command("/status")
        assert result["allowed"] is True


class TestCanExecuteCommandInFullPhase:
    @pytest.fixture(autouse=True)
    def set_full_phase(self):
        import xuansto_mcp.tools.resource_load_status as mod
        with _phase_lock:
            mod._current_phase = PHASE_FULL
        yield

    def test_status_allowed_in_full(self):
        result = can_execute_command("/status")
        assert result["allowed"] is True
        assert result["phase"] == PHASE_FULL

    def test_init_allowed_in_full(self):
        result = can_execute_command("/init")
        assert result["allowed"] is True

    def test_audit_allowed_in_full(self):
        result = can_execute_command("/audit")
        assert result["allowed"] is True


class TestProgressiveLoaderSkeletonCommands:
    @pytest.fixture
    def progressive_loader_module(self):
        import importlib.util
        from pathlib import Path
        scripts_dir = Path(__file__).resolve().parent.parent.parent / ".trae" / "skills" / "xuansto-skill-v2" / "scripts" / "knowledge_server"
        loader_path = scripts_dir / "progressive_loader.py"
        if not loader_path.exists():
            pytest.skip(f"progressive_loader.py not found at {loader_path}")
        spec = importlib.util.spec_from_file_location("progressive_loader", str(loader_path))
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod

    def test_progressive_loader_skeleton_allowed_commands(self, progressive_loader_module):
        assert progressive_loader_module.SKELETON_ALLOWED_COMMANDS == ["/status", "/help", "/budget"]

    def test_progressive_loader_can_execute_in_skeleton(self, progressive_loader_module):
        loader = progressive_loader_module.ProgressiveLoader()
        assert loader.get_current_phase() == progressive_loader_module.LoadPhase.SKELETON
        assert loader.can_execute_command("/status") is True
        assert loader.can_execute_command("/help") is True
        assert loader.can_execute_command("/budget") is True

    def test_progressive_loader_cannot_execute_in_skeleton(self, progressive_loader_module):
        loader = progressive_loader_module.ProgressiveLoader()
        assert loader.can_execute_command("/init") is False
        assert loader.can_execute_command("/implement") is False
        assert loader.can_execute_command("/sprint") is False

    def test_progressive_loader_can_execute_in_functional(self, progressive_loader_module):
        loader = progressive_loader_module.ProgressiveLoader()
        loader.advance_phase(progressive_loader_module.LoadPhase.FUNCTIONAL)
        assert loader.can_execute_command("/status") is True
        assert loader.can_execute_command("/init") is True
        assert loader.can_execute_command("/sprint") is True

    def test_progressive_loader_get_available_commands_in_skeleton(self, progressive_loader_module):
        loader = progressive_loader_module.ProgressiveLoader()
        commands = loader.get_available_commands()
        assert "/status" in commands
        assert "/help" in commands
        assert "/budget" in commands
        assert len(commands) == 3
