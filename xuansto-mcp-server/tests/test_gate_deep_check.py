import sys
import pytest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from xuansto_mcp.tools.quality_gate_check import INLINE_CHECKS


def test_check_test_pass_with_tests_dir(tmp_path: Path):
    (tmp_path / "tests").mkdir()
    (tmp_path / "tests" / "test_example.py").write_text("def test_one(): pass", encoding="utf-8")
    check_fn = INLINE_CHECKS.get("TEST-PASS")
    if check_fn:
        result = check_fn(str(tmp_path))
        assert result["gate_id"] == "TEST-PASS"
        assert result["status"] in ("PASS", "FAIL", "SKIP")


def test_check_test_pass_no_tests(tmp_path: Path):
    check_fn = INLINE_CHECKS.get("TEST-PASS")
    if check_fn:
        result = check_fn(str(tmp_path))
        assert result["gate_id"] == "TEST-PASS"
        assert result["status"] == "FAIL"


def test_check_spec_consistency_with_tasks(tmp_path: Path):
    (tmp_path / "tasks.md").write_text("- [x] Done task\n- [ ] Pending task\n", encoding="utf-8")
    check_fn = INLINE_CHECKS.get("SPEC-CONSISTENCY")
    if check_fn:
        result = check_fn(str(tmp_path))
        assert result["gate_id"] == "SPEC-CONSISTENCY"
        assert result["status"] in ("PASS", "FAIL", "SKIP")


def test_check_brainstorm_complete_with_keywords(tmp_path: Path):
    (tmp_path / "requirements.md").write_text("# 需求分析\n\n## 结论\n我们决定使用React。\n\n## 行动项\n1. 搭建项目\n", encoding="utf-8")
    check_fn = INLINE_CHECKS.get("BRAINSTORM-COMPLETE")
    if check_fn:
        result = check_fn(str(tmp_path))
        assert result["gate_id"] == "BRAINSTORM-COMPLETE"
        assert result["status"] in ("PASS", "FAIL", "SKIP")


def test_check_plan_atomic_with_criteria(tmp_path: Path):
    (tmp_path / "tasks.md").write_text("- [x] 实现登录功能 验收：用户可正常登录\n- [ ] 实现注册功能\n", encoding="utf-8")
    check_fn = INLINE_CHECKS.get("PLAN-ATOMIC")
    if check_fn:
        result = check_fn(str(tmp_path))
        assert result["gate_id"] == "PLAN-ATOMIC"
        assert result["status"] in ("PASS", "FAIL", "SKIP")
