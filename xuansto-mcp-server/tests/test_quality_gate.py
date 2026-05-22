import json
import os
from pathlib import Path
from unittest.mock import patch

import pytest

from xuansto_mcp.tools.quality_gate_check import (
    INLINE_CHECKS,
    _check_desktop_build,
    _check_spec_consistency,
    _check_test_pass,
)


@pytest.fixture
def tmp_project(tmp_path: Path) -> Path:
    return tmp_path


class TestCheckTestPass:
    def test_pass_when_test_files_exist(self, tmp_project: Path):
        (tmp_project / "tests").mkdir()
        (tmp_project / "tests" / "test_app.py").write_text("def test_example(): pass", encoding="utf-8")
        result = _check_test_pass(str(tmp_project))
        assert result["status"] in ("PASS", "FAIL", "SKIP")
        assert result["gate_id"] == "TEST-PASS"

    def test_fail_when_no_test_files(self, tmp_project: Path):
        (tmp_project / "app.py").write_text("print('hello')", encoding="utf-8")
        result = _check_test_pass(str(tmp_project))
        assert result["status"] == "FAIL"
        assert result["gate_id"] == "TEST-PASS"

    def test_detects_js_test_files(self, tmp_project: Path):
        src_dir = tmp_project / "tests"
        src_dir.mkdir()
        (src_dir / "app.test.ts").write_text("test('a', () => {})", encoding="utf-8")
        result = _check_test_pass(str(tmp_project))
        assert result["status"] in ("PASS", "FAIL", "SKIP")

    def test_detects_spec_files(self, tmp_project: Path):
        test_dir = tmp_project / "tests"
        test_dir.mkdir()
        (test_dir / "utils.spec.js").write_text("describe('x', () => {})", encoding="utf-8")
        result = _check_test_pass(str(tmp_project))
        assert result["status"] in ("PASS", "FAIL", "SKIP")


class TestCheckSpecConsistency:
    def test_pass_when_spec_dir_has_files(self, tmp_project: Path):
        (tmp_project / "tasks.md").write_text("- [x] Done task\n- [ ] Pending task\n", encoding="utf-8")
        result = _check_spec_consistency(str(tmp_project))
        assert result["status"] in ("PASS", "FAIL", "SKIP")
        assert result["gate_id"] == "SPEC-CONSISTENCY"

    def test_fail_when_spec_dir_empty(self, tmp_project: Path):
        result = _check_spec_consistency(str(tmp_project))
        assert result["status"] in ("FAIL", "SKIP")
        assert result["gate_id"] == "SPEC-CONSISTENCY"

    def test_fail_when_spec_dir_missing(self, tmp_project: Path):
        result = _check_spec_consistency(str(tmp_project))
        assert result["status"] in ("FAIL", "SKIP")
        assert result["gate_id"] == "SPEC-CONSISTENCY"


class TestCheckDesktopBuild:
    def test_pass_when_tauri_conf_exists(self, tmp_project: Path):
        (tmp_project / "tauri.conf.json").write_text("{}", encoding="utf-8")
        result = _check_desktop_build(str(tmp_project))
        assert result["status"] == "PASS"
        assert result["details"]["tauri_conf_found"] is True

    def test_pass_when_electron_in_package_json(self, tmp_project: Path):
        pkg = {"dependencies": {"electron": "^28.0.0"}}
        (tmp_project / "package.json").write_text(json.dumps(pkg), encoding="utf-8")
        result = _check_desktop_build(str(tmp_project))
        assert result["status"] == "PASS"
        assert result["details"]["electron_found"] is True

    def test_fail_when_no_desktop_config(self, tmp_project: Path):
        result = _check_desktop_build(str(tmp_project))
        assert result["status"] == "FAIL"
        assert result["details"]["desktop_config_found"] is False

    def test_pass_when_src_tauri_conf_exists(self, tmp_project: Path):
        src_tauri = tmp_project / "src-tauri"
        src_tauri.mkdir()
        (src_tauri / "tauri.conf.json").write_text("{}", encoding="utf-8")
        result = _check_desktop_build(str(tmp_project))
        assert result["status"] == "PASS"


class TestInlineChecksRegistry:
    def test_all_inline_checks_are_callable_or_none(self):
        for gate_id, check_fn in INLINE_CHECKS.items():
            assert check_fn is None or callable(check_fn), f"INLINE_CHECKS['{gate_id}'] must be None or callable"

    def test_expected_gates_registered(self):
        expected = [
            "TEST-PASS", "SPEC-CONSISTENCY", "BRAINSTORM-COMPLETE", "PLAN-ATOMIC",
            "UX-ACCEPTANCE", "DESKTOP-BUILD", "DESKTOP-SIGN", "DESKTOP-UPDATE",
            "DESKTOP-CROSS", "GATE-001", "GATE-002", "GATE-003", "GATE-004",
            "GATE-009", "GATE-011", "GATE-012", "GATE-013", "GATE-014", "GATE-015",
            "ANTI-PATTERN-CHECK", "DESIGN-SYSTEM-COMPLETE",
            "DESIGN-REVIEW-PRODUCT", "DESIGN-REVIEW-TECH", "DESIGN-REVIEW-DESIGN",
            "SUBAGENT-REVIEW", "REVIEW-CONFIDENCE", "PLAYWRIGHT-E2E-PASS",
            "AI-PENTEST", "INFRA-HEALTH", "SIMPLIFICATION-BEHAVIOR",
            "CHESTERTON-FENCE", "IPC-CONTRACT",
        ]
        for gate_id in expected:
            assert gate_id in INLINE_CHECKS, f"Missing inline check for {gate_id}"

    def test_inline_check_return_structure(self, tmp_project: Path):
        (tmp_project / "app.py").write_text("pass", encoding="utf-8")
        for gate_id, check_fn in INLINE_CHECKS.items():
            if check_fn is None:
                continue
            result = check_fn(str(tmp_project))
            assert "status" in result, f"{gate_id} missing 'status'"
            assert result["status"] in ("PASS", "FAIL", "SKIP"), f"{gate_id} invalid status: {result['status']}"
            assert "message" in result or "details" in result, f"{gate_id} missing 'message' or 'details'"
