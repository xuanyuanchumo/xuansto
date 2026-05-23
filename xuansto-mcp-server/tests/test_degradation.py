from __future__ import annotations

import atexit
import hashlib
import json
import threading
import time
from unittest.mock import patch, MagicMock

import pytest

from xuansto_mcp.core.degradation import (
    FALLBACK_MAP,
    _INLINE_FALLBACK_MAP,
    DegradationLevel,
    DegradationManager,
    _atexit_persist_state,
    _resolve_fallback_map,
    _load_fallback_config_from_yaml,
    _build_fallback_map_from_yaml,
    get_fallback,
    _RESOLVED_FALLBACK_MAP,
    _refresh_resolved_fallback_map,
)


_EXPECTED_TOOLS = [
    "skill_analyze",
    "knowledge_search",
    "knowledge_inject",
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


def test_degradation_manager_initialization():
    mgr = DegradationManager(health_interval=9999)
    assert mgr._health_interval == 9999
    assert mgr._started is False
    assert mgr._overall_level == DegradationLevel.L1_NORMAL
    assert len(mgr._components) == 0
    assert len(mgr._subscribers) == 0


def test_degradation_manager_default_health_interval():
    mgr = DegradationManager()
    assert mgr._health_interval == DegradationManager._DEFAULT_HEALTH_INTERVAL


def test_check_and_degrade_unknown_component():
    mgr = DegradationManager(health_interval=9999)
    result = mgr.check_and_degrade("nonexistent")
    assert result == "unknown"


def test_check_and_degrade_healthy_component_stays_normal(fresh_degradation_manager, patch_config):
    mgr = fresh_degradation_manager
    mgr.register_component("test_comp", check_fn=lambda: True, recover_fn=lambda: True, levels=["normal", "degraded", "unavailable"])
    level = mgr.check_and_degrade("test_comp")
    assert level == "normal"


def test_check_and_degrade_unhealthy_component_degrades(fresh_degradation_manager, patch_config):
    mgr = fresh_degradation_manager
    mgr.register_component("test_comp", check_fn=lambda: False, recover_fn=lambda: False, levels=["normal", "degraded", "unavailable"])
    level = mgr.check_and_degrade("test_comp")
    assert level == "degraded"


def test_check_and_degrade_propagates_through_levels(fresh_degradation_manager, patch_config):
    mgr = fresh_degradation_manager
    mgr.register_component("test_comp", check_fn=lambda: False, recover_fn=lambda: False, levels=["normal", "degraded", "unavailable"])
    mgr.check_and_degrade("test_comp")
    mgr.check_and_degrade("test_comp")
    level = mgr.check_and_degrade("test_comp")
    assert level == "unavailable"


def test_check_and_degrade_stays_at_max_level(fresh_degradation_manager, patch_config):
    mgr = fresh_degradation_manager
    mgr.register_component("test_comp", check_fn=lambda: False, recover_fn=lambda: False, levels=["normal", "degraded", "unavailable"])
    mgr.check_and_degrade("test_comp")
    mgr.check_and_degrade("test_comp")
    mgr.check_and_degrade("test_comp")
    level = mgr.check_and_degrade("test_comp")
    assert level == "unavailable"


def test_check_and_degrade_exception_in_check_fn(fresh_degradation_manager, patch_config):
    mgr = fresh_degradation_manager
    mgr.register_component("test_comp", check_fn=lambda: (_ for _ in ()).throw(RuntimeError("boom")), recover_fn=lambda: True, levels=["normal", "degraded"])
    level = mgr.check_and_degrade("test_comp")
    assert level == "degraded"


def test_attempt_recovery_unknown_component():
    mgr = DegradationManager(health_interval=9999)
    result = mgr.attempt_recovery("nonexistent")
    assert result is False


def test_attempt_recovery_already_normal(fresh_degradation_manager, patch_config):
    mgr = fresh_degradation_manager
    mgr.register_component("test_comp", check_fn=lambda: True, recover_fn=lambda: True, levels=["normal", "degraded"])
    result = mgr.attempt_recovery("test_comp")
    assert result is True


def test_attempt_recovery_before_backoff_expires(fresh_degradation_manager, patch_config):
    mgr = fresh_degradation_manager
    mgr.register_component("test_comp", check_fn=lambda: False, recover_fn=lambda: True, levels=["normal", "degraded"])
    mgr.check_and_degrade("test_comp")
    state = mgr._components["test_comp"]
    state.next_recovery_time = time.time() + 10000
    result = mgr.attempt_recovery("test_comp")
    assert result is False


def test_attempt_recovery_succeeds(fresh_degradation_manager, patch_config):
    mgr = fresh_degradation_manager
    mgr.register_component("test_comp", check_fn=lambda: False, recover_fn=lambda: True, levels=["normal", "degraded"])
    mgr.check_and_degrade("test_comp")
    state = mgr._components["test_comp"]
    state.next_recovery_time = 0.0
    result = mgr.attempt_recovery("test_comp")
    assert result is True
    assert state.level == "normal"


def test_attempt_recovery_fails(fresh_degradation_manager, patch_config):
    mgr = fresh_degradation_manager
    mgr.register_component("test_comp", check_fn=lambda: False, recover_fn=lambda: False, levels=["normal", "degraded"])
    mgr.check_and_degrade("test_comp")
    state = mgr._components["test_comp"]
    state.next_recovery_time = 0.0
    result = mgr.attempt_recovery("test_comp")
    assert result is False
    assert state.recovery_attempts >= 1


def test_attempt_recovery_exception_in_recover_fn(fresh_degradation_manager, patch_config):
    mgr = fresh_degradation_manager
    mgr.register_component("test_comp", check_fn=lambda: False, recover_fn=lambda: (_ for _ in ()).throw(RuntimeError("boom")), levels=["normal", "degraded"])
    mgr.check_and_degrade("test_comp")
    state = mgr._components["test_comp"]
    state.next_recovery_time = 0.0
    result = mgr.attempt_recovery("test_comp")
    assert result is False


def test_compute_backoff_includes_jitter():
    mgr = DegradationManager(health_interval=9999)
    results = [mgr._compute_backoff(1) for _ in range(20)]
    assert len(set(results)) > 1, "Backoff values should vary due to jitter"
    base = mgr._BASE_RECOVERY_BACKOFF * (mgr._BACKOFF_MULTIPLIER ** 1)
    for r in results:
        assert r >= base
        assert r <= mgr._MAX_RECOVERY_BACKOFF


def test_compute_backoff_respects_max():
    mgr = DegradationManager(health_interval=9999)
    result = mgr._compute_backoff(100)
    assert result <= mgr._MAX_RECOVERY_BACKOFF


def test_compute_backoff_at_zero_attempts():
    mgr = DegradationManager(health_interval=9999)
    result = mgr._compute_backoff(0)
    assert result >= mgr._BASE_RECOVERY_BACKOFF


def test_state_persist_and_load(fresh_degradation_manager, patch_config, tmp_work_dir):
    mgr = fresh_degradation_manager
    mgr.register_component("test_comp", check_fn=lambda: True, recover_fn=lambda: True, levels=["normal", "degraded"])
    mgr._persist_state()
    state_path = tmp_work_dir / mgr._STATE_FILENAME
    assert state_path.exists()
    data = json.loads(state_path.read_text(encoding="utf-8"))
    assert "_hash" in data
    assert "_timestamp" in data
    assert "components" in data


def test_state_persist_hash_verification(fresh_degradation_manager, patch_config, tmp_work_dir):
    mgr = fresh_degradation_manager
    mgr.register_component("test_comp", check_fn=lambda: True, recover_fn=lambda: True, levels=["normal", "degraded"])
    mgr._persist_state()
    state_path = tmp_work_dir / mgr._STATE_FILENAME
    data = json.loads(state_path.read_text(encoding="utf-8"))
    components_data = data.get("components", {})
    expected_hash = hashlib.sha256(json.dumps(components_data, sort_keys=True, ensure_ascii=False).encode("utf-8")).hexdigest()
    assert data["_hash"] == expected_hash


def test_load_state_hash_mismatch_skips(fresh_degradation_manager, patch_config, tmp_work_dir):
    mgr = fresh_degradation_manager
    mgr.register_component("test_comp", check_fn=lambda: True, recover_fn=lambda: True, levels=["normal", "degraded"])
    mgr._persist_state()
    state_path = tmp_work_dir / mgr._STATE_FILENAME
    data = json.loads(state_path.read_text(encoding="utf-8"))
    data["_hash"] = "corrupted_hash_value"
    state_path.write_text(json.dumps(data), encoding="utf-8")
    mgr2 = DegradationManager(health_interval=9999)
    mgr2.register_component("test_comp", check_fn=lambda: True, recover_fn=lambda: True, levels=["normal", "degraded"])
    with patch.object(DegradationManager, "_persist_state", lambda self: None):
        mgr2.load_state()
    comp = mgr2._components["test_comp"]
    assert comp.level == "normal"


def test_load_state_no_file(fresh_degradation_manager, patch_config, tmp_work_dir):
    mgr = fresh_degradation_manager
    mgr.register_component("test_comp", check_fn=lambda: True, recover_fn=lambda: True, levels=["normal", "degraded"])
    with patch.object(DegradationManager, "_persist_state", lambda self: None):
        mgr.load_state()
    comp = mgr._components["test_comp"]
    assert comp.level == "normal"


def test_load_state_backward_compatible_no_hash(fresh_degradation_manager, patch_config, tmp_work_dir):
    mgr = fresh_degradation_manager
    mgr.register_component("test_comp", check_fn=lambda: True, recover_fn=lambda: True, levels=["normal", "degraded"])
    state_path = tmp_work_dir / mgr._STATE_FILENAME
    old_state = {
        "overall_level": "L2_LOCAL_SEMANTIC",
        "components": {
            "test_comp": {
                "name": "test_comp",
                "level": "degraded",
                "last_check_time": 0.0,
                "last_check_healthy": False,
                "recovery_attempts": 1,
                "next_recovery_time": 0.0,
                "degraded_since": None,
            }
        },
    }
    state_path.write_text(json.dumps(old_state), encoding="utf-8")
    mgr2 = DegradationManager(health_interval=9999)
    mgr2.register_component("test_comp", check_fn=lambda: True, recover_fn=lambda: True, levels=["normal", "degraded"])
    with patch.object(DegradationManager, "_persist_state", lambda self: None):
        mgr2.load_state()
    comp = mgr2._components["test_comp"]
    assert comp.level == "degraded"


def test_atexit_handler_registered():
    import atexit as atexit_mod
    if hasattr(atexit_mod, "_exithandlers"):
        handlers = [h for h in atexit_mod._exithandlers if h[0] is _atexit_persist_state]
        assert len(handlers) >= 1
    else:
        mgr = DegradationManager(health_interval=9999)
        assert hasattr(mgr, "_persist_state")


def test_get_fallback_known_tool():
    fn = get_fallback("skill_analyze")
    assert fn is not None
    assert callable(fn)


def test_get_fallback_unknown_tool():
    fn = get_fallback("nonexistent_tool_xyz")
    assert fn is None


def test_fallback_map_covers_all_tools():
    for tool in _EXPECTED_TOOLS:
        assert tool in FALLBACK_MAP, f"FALLBACK_MAP missing tool: {tool}"
    assert len(FALLBACK_MAP) >= 17


_EXPECTED_INLINE_KEYS = {
    "skill_analyze": "skill_analyze_fallback",
    "knowledge_search": "knowledge_search_fallback",
    "knowledge_inject": "knowledge_inject_fallback",
    "quality_gate_check": "quality_gate_fallback",
    "spec_drift_detect": "spec_drift_fallback",
    "security_scan": "security_scan_fallback",
    "code_simplify": "code_simplify_fallback",
    "session_manage": "session_manage_fallback",
    "workflow_dispatch": "workflow_dispatch_fallback",
    "agent_status": "agent_status_fallback",
    "hook_manage": "hook_manage_fallback",
    "resource_load_status": "resource_load_status_fallback",
    "context_compress": "context_compress_fallback",
    "server_health": "server_health_fallback",
    "decision_log": "decision_log_fallback",
    "token_budget": "token_budget_fallback",
    "project_init": "project_init_fallback",
}


def test_inline_fallback_map_covers_all_tools():
    for tool, key in _EXPECTED_INLINE_KEYS.items():
        assert key in _INLINE_FALLBACK_MAP, f"_INLINE_FALLBACK_MAP missing key: {key}"
    assert len(_INLINE_FALLBACK_MAP) >= 17


def test_resolve_fallback_map_default():
    result = _resolve_fallback_map()
    assert isinstance(result, dict)
    for tool in _EXPECTED_TOOLS:
        assert tool in result


def test_resolve_fallback_map_with_yaml_config(tmp_path, patch_config):
    import xuansto_mcp.core.degradation as degr_mod
    yaml_path = tmp_path / "fallback_config.yaml"
    yaml_content = """
fallback_map:
  skill_analyze:
    inline: skill_analyze_fallback
"""
    yaml_path.write_text(yaml_content, encoding="utf-8")
    with patch.object(degr_mod, "_FALLBACK_CONFIG_PATH", yaml_path):
        with patch.object(degr_mod, "_get_fallback_config_mtime", return_value=1.0):
            with patch.object(degr_mod, "_fallback_config_mtime", 0.0):
                result = _resolve_fallback_map()
                assert "skill_analyze" in result


def test_build_fallback_map_from_yaml_with_inline():
    yaml_config = {
        "skill_analyze": {"inline": "skill_analyze_fallback"},
        "knowledge_search": {"inline": "knowledge_search_fallback"},
    }
    result = _build_fallback_map_from_yaml(yaml_config)
    assert "skill_analyze" in result
    assert "knowledge_search" in result


def test_build_fallback_map_from_yaml_fallback_to_default():
    yaml_config = {
        "skill_analyze": {"inline": "nonexistent_fallback"},
    }
    result = _build_fallback_map_from_yaml(yaml_config)
    assert "skill_analyze" in result
    assert result["skill_analyze"] is FALLBACK_MAP["skill_analyze"]


def test_degradation_level_ordering():
    assert DegradationLevel.L1_NORMAL < DegradationLevel.L2_LOCAL_SEMANTIC
    assert DegradationLevel.L2_LOCAL_SEMANTIC < DegradationLevel.L3_BM25_ONLY
    assert DegradationLevel.L1_NORMAL < DegradationLevel.L3_BM25_ONLY
    assert DegradationLevel.L3_BM25_ONLY > DegradationLevel.L1_NORMAL
    assert DegradationLevel.L2_LOCAL_SEMANTIC >= DegradationLevel.L2_LOCAL_SEMANTIC
    assert DegradationLevel.L1_NORMAL <= DegradationLevel.L2_LOCAL_SEMANTIC


def test_degradation_level_not_comparable_to_other_types():
    result = DegradationLevel.L1_NORMAL.__lt__("not_a_level")
    assert result is NotImplemented


def test_register_component_updates_existing(fresh_degradation_manager, patch_config):
    mgr = fresh_degradation_manager
    mgr.register_component("test_comp", check_fn=lambda: True, recover_fn=lambda: True, levels=["normal", "degraded"])
    new_check = lambda: False
    mgr.register_component("test_comp", check_fn=new_check, recover_fn=lambda: True, levels=["a", "b", "c"])
    assert mgr._components["test_comp"].check_fn is new_check
    assert mgr._components["test_comp"].levels == ["a", "b", "c"]


def test_subscribe_and_notify(fresh_degradation_manager, patch_config):
    mgr = fresh_degradation_manager
    notifications = []
    mgr.subscribe(lambda comp, old, new: notifications.append((comp, old, new)))
    mgr.register_component("test_comp", check_fn=lambda: False, recover_fn=lambda: False, levels=["normal", "degraded"])
    mgr.check_and_degrade("test_comp")
    assert len(notifications) >= 1
    assert notifications[0][0] == "test_comp"


def test_get_status(fresh_degradation_manager, patch_config):
    mgr = fresh_degradation_manager
    mgr.register_component("test_comp", check_fn=lambda: True, recover_fn=lambda: True, levels=["normal", "degraded"])
    status = mgr.get_status()
    assert "overall_level" in status
    assert "components" in status
    assert "test_comp" in status["components"]
    assert "health_interval" in status
    assert "started" in status


def test_concurrent_state_access(fresh_degradation_manager, patch_config, tmp_work_dir):
    mgr = fresh_degradation_manager
    mgr.register_component("comp_a", check_fn=lambda: True, recover_fn=lambda: True, levels=["normal", "degraded"])
    mgr.register_component("comp_b", check_fn=lambda: True, recover_fn=lambda: True, levels=["normal", "degraded"])
    errors = []

    def writer(comp_name):
        try:
            for _ in range(50):
                mgr.check_and_degrade(comp_name)
                mgr.attempt_recovery(comp_name)
        except Exception as e:
            errors.append(e)

    t1 = threading.Thread(target=writer, args=("comp_a",))
    t2 = threading.Thread(target=writer, args=("comp_b",))
    t1.start()
    t2.start()
    t1.join(timeout=10)
    t2.join(timeout=10)
    assert len(errors) == 0, f"Concurrent access errors: {errors}"
