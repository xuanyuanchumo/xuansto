from __future__ import annotations

import asyncio
import contextlib
import hashlib
import json
import re
import subprocess
import sys
import threading
import time
from collections.abc import Callable
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from mcp.server.fastmcp import FastMCP
from mcp.types import ToolAnnotations

from ..core import atomic_write
from ..core.config import GATE_SCRIPTS_MAP, QUALITY_GATES_PHASE_MAP, SCRIPTS_DIR, WORK_DIR
from ..core.errors import ERR_VALIDATION, make_error_response, make_success_response
from ..core.logging_config import get_logger
from ..core.notifications import notify
from ..core.validator import validate_input, validate_path_safety
from ..models.schemas import QualityGateCheckInput

logger = get_logger("quality_gate_check")

_SECURITY_HARD_GATES: set[str] = {
    "production_deploy",
    "secret_key_rotation",
    "database_schema_destructive_change",
}


def _load_hard_gates_from_config() -> set[str]:
    try:
        from ..core.config import _load_yaml_config, _resolve_skill_file
        config_path = _resolve_skill_file("configs/default.yaml")
        config = _load_yaml_config(config_path)
        hc = config.get("human_collaboration", {})
        hard_gates = hc.get("security_hard_gates", [])
        if isinstance(hard_gates, list) and hard_gates:
            return set(hard_gates)
    except Exception:
        pass
    return _SECURITY_HARD_GATES


_SECURITY_HARD_GATES = _load_hard_gates_from_config()


def _check_hard_gate(gate_id: str) -> dict[str, Any]:
    if gate_id in _SECURITY_HARD_GATES:
        logger.info("hard_gate_triggered: gate_id=%s requires_manual_approval", gate_id)
        return {"approved": False, "reason": "hard_gate_requires_manual_approval", "gate_id": gate_id}
    return {"approved": True, "reason": "not_a_hard_gate", "gate_id": gate_id}


def _resolve_gates(gate_ids: list[str] | None, phase: str | None) -> list[str]:
    if gate_ids:
        return gate_ids
    if phase is not None:
        return list(QUALITY_GATES_PHASE_MAP.get(str(phase), []))
    all_gates = list(GATE_SCRIPTS_MAP.keys())
    for phase_gates in QUALITY_GATES_PHASE_MAP.values():
        for g in phase_gates:
            if g not in all_gates:
                all_gates.append(g)
    return all_gates


def _parse_gate_result(gate_id: str, result: subprocess.CompletedProcess[str]) -> dict[str, Any]:
    status = "PASS" if result.returncode == 0 else "FAIL"
    output = result.stdout.strip() if result.stdout else ""
    try:
        parsed = json.loads(output)
        return {
            "gate_id": gate_id,
            "status": status,
            "details": parsed,
        }
    except (json.JSONDecodeError, TypeError):
        return {
            "gate_id": gate_id,
            "status": status,
            "details": {"raw_output": output[:500]},
        }


def _find_files(root: Path, patterns: list[str]) -> list[Path]:
    results: list[Path] = []
    for pattern in patterns:
        results.extend(root.rglob(pattern))
    return results


def _find_files_by_name_part(root: Path, parts: list[str]) -> list[Path]:
    results: list[Path] = []
    for f in root.rglob("*"):
        if not f.is_file():
            continue
        name_lower = f.name.lower()
        if any(p in name_lower for p in parts):
            results.append(f)
    return results


def _check_test_pass(project_path: str) -> dict[str, Any]:
    test_dirs = ["tests", "test"]
    project = Path(project_path).resolve()
    found_tests = False
    for d in test_dirs:
        if (project / d).is_dir():
            found_tests = True
            break
    if not found_tests:
        return {"status": "FAIL", "gate_id": "TEST-PASS", "message": "No test directory found", "suggestion": "Create a tests/ directory with test files"}
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pytest", "--co", "-q", "--no-header"],
            capture_output=True, text=True, timeout=30, cwd=str(project),
        )
        if result.returncode == 0:
            test_count = len([ln for ln in result.stdout.strip().split("\n") if ln.strip() and not ln.startswith("=")])
            return {"status": "PASS", "gate_id": "TEST-PASS", "message": f"Tests collectible: {test_count} tests found"}
        else:
            return {"status": "FAIL", "gate_id": "TEST-PASS", "message": f"pytest collection failed: {result.stderr[:200]}", "suggestion": "Fix test collection errors before proceeding"}
    except (subprocess.TimeoutExpired, FileNotFoundError):
        test_files = list(project.rglob("test_*.py")) + list(project.rglob("*_test.py"))
        if test_files:
            return {"status": "PASS", "gate_id": "TEST-PASS", "message": f"Found {len(test_files)} test files (pytest not available for deep check)"}
        return {"status": "FAIL", "gate_id": "TEST-PASS", "message": "No test files found", "suggestion": "Create test files matching test_*.py or *_test.py"}


def _check_spec_consistency(project_path: str) -> dict[str, Any]:
    project = Path(project_path).resolve()
    spec_files = list(project.rglob("spec.md")) + list(project.rglob("tasks.md"))
    if not spec_files:
        return {"status": "SKIP", "gate_id": "SPEC-CONSISTENCY", "message": "No spec/tasks files found"}
    total_tasks = 0
    completed_tasks = 0
    for sf in spec_files:
        try:
            content = sf.read_text(encoding="utf-8")
        except OSError:
            continue
        unchecked = re.findall(r'- \[ \]', content)
        checked = re.findall(r'- \[x\]', content)
        total_tasks += len(unchecked) + len(checked)
        completed_tasks += len(checked)
    if total_tasks == 0:
        return {"status": "PASS", "gate_id": "SPEC-CONSISTENCY", "message": "No task items found in spec files"}
    completion_rate = completed_tasks / total_tasks
    if completion_rate >= 0.8:
        return {"status": "PASS", "gate_id": "SPEC-CONSISTENCY", "message": f"Task completion rate: {completion_rate:.0%} ({completed_tasks}/{total_tasks})"}
    else:
        return {"status": "FAIL", "gate_id": "SPEC-CONSISTENCY", "message": f"Task completion rate too low: {completion_rate:.0%} ({completed_tasks}/{total_tasks})", "suggestion": f"Complete at least {int(total_tasks * 0.8) - completed_tasks} more tasks to reach 80% completion"}


def _check_brainstorm_complete(project_path: str) -> dict[str, Any]:
    project = Path(project_path).resolve()
    doc_files = list(project.rglob("*.md"))
    if not doc_files:
        return {"status": "SKIP", "gate_id": "BRAINSTORM-COMPLETE", "message": "No markdown files found"}
    required_keywords = ["结论", "决定", "行动项", "conclusion", "decision", "action item"]
    found_keywords: set[str] = set()
    for df in doc_files:
        try:
            content = df.read_text(encoding="utf-8").lower()
        except OSError:
            continue
        for kw in required_keywords:
            if kw.lower() in content:
                found_keywords.add(kw)
    coverage = len(found_keywords) / len(required_keywords)
    if coverage >= 0.5:
        return {"status": "PASS", "gate_id": "BRAINSTORM-COMPLETE", "message": f"Requirements analysis keywords found: {sorted(found_keywords)} ({coverage:.0%})"}
    else:
        return {"status": "FAIL", "gate_id": "BRAINSTORM-COMPLETE", "message": f"Requirements analysis incomplete: missing keywords {sorted(set(required_keywords) - found_keywords)}", "suggestion": "Add conclusion, decisions, and action items to your requirements document"}


def _check_plan_atomic(project_path: str) -> dict[str, Any]:
    project = Path(project_path).resolve()
    task_files = list(project.rglob("tasks.md"))
    if not task_files:
        return {"status": "SKIP", "gate_id": "PLAN-ATOMIC", "message": "No tasks.md found"}
    total_tasks = 0
    tasks_with_criteria = 0
    for tf in task_files:
        try:
            content = tf.read_text(encoding="utf-8")
        except OSError:
            continue
        task_lines = re.findall(r'- \[[ x]\] .+', content)
        total_tasks += len(task_lines)
        for line in task_lines:
            if any(kw in line.lower() for kw in ["验收", "acceptance", "验证", "verify", "should", "shall", "必须"]):
                tasks_with_criteria += 1
    if total_tasks == 0:
        return {"status": "PASS", "gate_id": "PLAN-ATOMIC", "message": "No task items found"}
    criteria_rate = tasks_with_criteria / total_tasks
    if criteria_rate >= 0.5:
        return {"status": "PASS", "gate_id": "PLAN-ATOMIC", "message": f"Tasks with acceptance criteria: {criteria_rate:.0%} ({tasks_with_criteria}/{total_tasks})"}
    else:
        return {"status": "FAIL", "gate_id": "PLAN-ATOMIC", "message": f"Too few tasks with acceptance criteria: {criteria_rate:.0%} ({tasks_with_criteria}/{total_tasks})", "suggestion": "Add acceptance criteria (验收标准) to each task in tasks.md"}


def _check_ux_acceptance(project_path: str) -> dict[str, Any]:
    root = Path(project_path)
    keywords = ["acceptance", "验收"]
    search_dirs = [root / ".trae", root / "docs", root]
    found_files: list[Path] = []
    for d in search_dirs:
        if d.exists():
            found_files.extend(_find_files_by_name_part(d, keywords))
    if found_files:
        return {"status": "PASS", "message": f"发现{len(found_files)}个验收标准文件", "details": {"files_found": len(found_files), "sample_files": [str(f.relative_to(root)) for f in found_files[:5]]}}
    return {"status": "FAIL", "message": "未发现验收标准文件", "suggestion": "通过 UX 验收：确保用户界面符合设计稿，交互流畅", "details": {"files_found": 0}}


def _check_desktop_build(project_path: str) -> dict[str, Any]:
    root = Path(project_path)
    pkg_json = root / "package.json"
    tauri_conf = root / "tauri.conf.json"
    tauri_conf_src = root / "src-tauri" / "tauri.conf.json"
    if tauri_conf.exists() or tauri_conf_src.exists():
        return {"status": "PASS", "message": "发现Tauri配置", "details": {"tauri_conf_found": True}}
    if pkg_json.exists():
        try:
            data = json.loads(pkg_json.read_text(encoding="utf-8"))
            deps = {**data.get("dependencies", {}), **data.get("devDependencies", {})}
            if any(k in deps for k in ["electron", "electron-builder"]):
                return {"status": "PASS", "message": "发现Electron依赖", "details": {"electron_found": True}}
        except (json.JSONDecodeError, OSError):
            pass
    return {"status": "FAIL", "message": "未发现桌面构建配置", "suggestion": "修复桌面构建：检查 Electron/Tauri 构建配置和依赖", "details": {"desktop_config_found": False}}


def _check_desktop_sign(project_path: str) -> dict[str, Any]:
    root = Path(project_path)
    sign_keywords = ["sign", "certificate", "cert", "entitlements", "provision"]
    sign_files = _find_files_by_name_part(root, sign_keywords)
    env_files = list(root.rglob(".env*"))
    has_sign_config = False
    for ef in env_files:
        try:
            content = ef.read_text(encoding="utf-8", errors="ignore")
            if any(k in content.lower() for k in ["signing", "certificate", "csc_link", "sign"]):
                has_sign_config = True
                break
        except OSError:
            pass
    if sign_files or has_sign_config:
        return {"status": "PASS", "message": "发现签名配置", "details": {"sign_files_found": len(sign_files), "env_sign_config": has_sign_config}}
    return {"status": "FAIL", "message": "未发现签名配置", "suggestion": "完成代码签名：确保使用有效证书对应用进行签名", "details": {"sign_files_found": 0, "env_sign_config": False}}


def _check_desktop_update(project_path: str) -> dict[str, Any]:
    root = Path(project_path)
    update_keywords = ["update", "updater", "auto-update"]
    update_files = _find_files_by_name_part(root, update_keywords)
    pkg_json = root / "package.json"
    has_update_config = False
    if pkg_json.exists():
        try:
            content = pkg_json.read_text(encoding="utf-8")
            if any(k in content for k in ["update", "updater", "autoUpdate", "publish"]):
                has_update_config = True
        except OSError:
            pass
    tauri_conf_paths = [root / "tauri.conf.json", root / "src-tauri" / "tauri.conf.json"]
    for tp in tauri_conf_paths:
        if tp.exists():
            try:
                content = tp.read_text(encoding="utf-8")
                if "updater" in content:
                    has_update_config = True
            except OSError:
                pass
    if update_files or has_update_config:
        return {"status": "PASS", "message": "发现更新配置", "details": {"update_files_found": len(update_files), "update_config": has_update_config}}
    return {"status": "FAIL", "message": "未发现更新配置", "suggestion": "验证自动更新：确保更新服务器配置正确，增量更新可用", "details": {"update_files_found": 0, "update_config": False}}


def _check_desktop_cross(project_path: str) -> dict[str, Any]:
    root = Path(project_path)
    pkg_json = root / "package.json"
    if pkg_json.exists():
        try:
            data = json.loads(pkg_json.read_text(encoding="utf-8"))
            build_cfg = data.get("build", {})
            platforms = build_cfg.get("mac", []) + build_cfg.get("win", []) + build_cfg.get("linux", [])
            if platforms:
                return {"status": "PASS", "message": "发现多平台构建目标", "details": {"platforms_configured": True}}
        except (json.JSONDecodeError, OSError):
            pass
    tauri_conf_paths = [root / "tauri.conf.json", root / "src-tauri" / "tauri.conf.json"]
    for tp in tauri_conf_paths:
        if tp.exists():
            try:
                content = tp.read_text(encoding="utf-8")
                if any(t in content for t in ["targets", "macos", "windows", "linux"]):
                    return {"status": "PASS", "message": "发现Tauri多平台配置", "details": {"platforms_configured": True}}
            except OSError:
                pass
    return {"status": "FAIL", "message": "未发现跨平台构建配置", "suggestion": "确保跨平台兼容：在 Windows/macOS/Linux 上测试核心功能", "details": {"platforms_configured": False}}


def _check_gate_001(project_path: str) -> dict[str, Any]:
    root = Path(project_path)
    design_files = _find_files_by_name_part(root, ["design", "ui", "ux", "wireframe", "mockup"])
    if design_files:
        return {"status": "PASS", "message": f"发现{len(design_files)}个设计文件", "details": {"files_found": len(design_files)}}
    return {"status": "FAIL", "message": "未发现设计文件", "suggestion": "完善需求文档：确保每个需求都有明确的验收标准", "details": {"files_found": 0}}


def _check_gate_002(project_path: str) -> dict[str, Any]:
    root = Path(project_path)
    review_files = _find_files_by_name_part(root / ".trae", ["review", "feedback", "评审"])
    if review_files:
        return {"status": "PASS", "message": f"发现{len(review_files)}个设计评审文件", "details": {"files_found": len(review_files)}}
    return {"status": "FAIL", "message": "未发现设计评审文件", "suggestion": "确保需求可追溯：每个需求应关联到设计文档中的实现方案", "details": {"files_found": 0}}


def _check_gate_003(project_path: str) -> dict[str, Any]:
    root = Path(project_path)
    spec_dir = root / ".trae" / "specs"
    if spec_dir.exists():
        spec_files = [f for f in spec_dir.rglob("*") if f.is_file()]
        if spec_files:
            return {"status": "PASS", "message": f"规格目录包含{len(spec_files)}个文件", "details": {"spec_files": len(spec_files)}}
    return {"status": "FAIL", "message": "规格目录不完整", "suggestion": "验证架构设计：确保模块间依赖关系清晰，无循环依赖", "details": {"spec_files": 0}}


def _check_gate_004(project_path: str) -> dict[str, Any]:
    root = Path(project_path)
    plan_files = _find_files_by_name_part(root / ".trae", ["plan", "schedule", "roadmap", "milestone"])
    if plan_files:
        return {"status": "PASS", "message": f"发现{len(plan_files)}个计划文件", "details": {"files_found": len(plan_files)}}
    return {"status": "FAIL", "message": "未发现计划文件", "suggestion": "确保接口定义完整：每个公共接口应有类型注解和文档字符串", "details": {"files_found": 0}}


def _check_gate_009(project_path: str) -> dict[str, Any]:
    root = Path(project_path)
    test_patterns = ["test_*.py", "*_test.py", "*.test.ts", "*.test.js"]
    test_files = _find_files(root, test_patterns)
    if test_files:
        return {"status": "PASS", "message": f"发现{len(test_files)}个测试文件", "details": {"test_files": len(test_files)}}
    return {"status": "FAIL", "message": "未发现测试文件", "suggestion": "确保代码风格一致：运行 `ruff check --fix` 自动修复风格问题", "details": {"test_files": 0}}


def _check_gate_011(project_path: str) -> dict[str, Any]:
    root = Path(project_path)
    e2e_patterns = ["*e2e*", "*e2e*.*", "*playwright*", "*cypress*"]
    e2e_files: list[Path] = []
    for p in e2e_patterns:
        e2e_files.extend(root.rglob(p))
    e2e_files = [f for f in e2e_files if f.is_file()]
    if e2e_files:
        return {"status": "PASS", "message": f"发现{len(e2e_files)}个E2E相关文件", "details": {"e2e_files": len(e2e_files)}}
    return {"status": "FAIL", "message": "未发现E2E相关文件", "suggestion": "确保集成测试通过：检查模块间接口调用是否正常", "details": {"e2e_files": 0}}


def _check_gate_012(project_path: str) -> dict[str, Any]:
    root = Path(project_path)
    perf_patterns = ["*perf*", "*benchmark*", "*load-test*"]
    perf_files: list[Path] = []
    for p in perf_patterns:
        perf_files.extend(root.rglob(p))
    perf_files = [f for f in perf_files if f.is_file()]
    if perf_files:
        return {"status": "PASS", "message": f"发现{len(perf_files)}个性能测试文件", "details": {"perf_files": len(perf_files)}}
    return {"status": "FAIL", "message": "未发现性能测试文件", "suggestion": "验证性能指标：确保关键路径响应时间在阈值内", "details": {"perf_files": 0}}


def _check_gate_013(project_path: str) -> dict[str, Any]:
    root = Path(project_path)
    ci_patterns = [".github/workflows/*.yml", ".github/workflows/*.yaml", ".gitlab-ci.yml", "Jenkinsfile", ".circleci/config.yml"]
    ci_files: list[Path] = []
    for p in ci_patterns:
        ci_files.extend(root.glob(p))
    if ci_files:
        return {"status": "PASS", "message": f"发现{len(ci_files)}个CI配置文件", "details": {"ci_files": len(ci_files)}}
    return {"status": "FAIL", "message": "未发现CI配置文件", "suggestion": "确保部署配置完整：检查 Dockerfile、环境变量、健康检查端点", "details": {"ci_files": 0}}


def _check_gate_014(project_path: str) -> dict[str, Any]:
    root = Path(project_path)
    deploy_keywords = ["deploy", "docker", "kubernetes", "k8s", "helm", "terraform"]
    deploy_files = _find_files_by_name_part(root, deploy_keywords)
    deploy_files = [f for f in deploy_files if f.is_file()]
    if deploy_files:
        return {"status": "PASS", "message": f"发现{len(deploy_files)}个部署配置文件", "details": {"deploy_files": len(deploy_files)}}
    return {"status": "FAIL", "message": "未发现部署配置文件", "suggestion": "验证监控告警：确保关键指标有告警规则和通知渠道", "details": {"deploy_files": 0}}


def _check_gate_015(project_path: str) -> dict[str, Any]:
    root = Path(project_path)
    release_keywords = ["changelog", "release", "version"]
    release_files = _find_files_by_name_part(root, release_keywords)
    release_files = [f for f in release_files if f.is_file()]
    if release_files:
        return {"status": "PASS", "message": f"发现{len(release_files)}个发布相关文件", "details": {"release_files": len(release_files)}}
    return {"status": "FAIL", "message": "未发现发布相关文件", "suggestion": "确保发布就绪：检查版本号、CHANGELOG、迁移脚本", "details": {"release_files": 0}}


def _check_anti_pattern(project_path: str) -> dict[str, Any]:
    root = Path(project_path)
    source_patterns = ["*.py", "*.ts", "*.js"]
    source_files: list[Path] = []
    for p in source_patterns:
        source_files.extend(root.rglob(p))
    source_files = [f for f in source_files if f.is_file() and "node_modules" not in str(f) and ".git" not in str(f)]
    anti_pattern_counts = {"any_usage": 0, "bare_except": 0, "todo_fixme": 0}
    for sf in source_files[:200]:
        try:
            content = sf.read_text(encoding="utf-8", errors="ignore")
            if ".any(" in content:
                anti_pattern_counts["any_usage"] += 1
            if "except:" in content or "except\n" in content:
                anti_pattern_counts["bare_except"] += 1
            for kw in ["TODO", "FIXME", "HACK", "XXX"]:
                if kw in content:
                    anti_pattern_counts["todo_fixme"] += 1
                    break
        except OSError:
            pass
    total_issues = sum(anti_pattern_counts.values())
    if total_issues == 0:
        return {"status": "PASS", "message": "未发现常见反模式", "details": anti_pattern_counts}
    pattern_list = ", ".join(k for k, v in anti_pattern_counts.items() if v > 0)
    return {"status": "FAIL", "message": f"发现{total_issues}处潜在反模式", "suggestion": f"修复反模式：{pattern_list}。参考 python-standards.md 中的规范", "details": anti_pattern_counts}


def _check_design_system_complete(project_path: str) -> dict[str, Any]:
    root = Path(project_path)
    design_patterns = ["tailwind.config.*", "theme.*", "design-tokens.*", "tokens.json", "*.theme.*"]
    design_files: list[Path] = []
    for p in design_patterns:
        design_files.extend(root.glob(p))
    design_files = [f for f in design_files if f.is_file()]
    if design_files:
        return {"status": "PASS", "message": f"发现{len(design_files)}个设计系统文件", "details": {"design_files": len(design_files), "sample_files": [str(f.relative_to(root)) for f in design_files[:5]]}}
    return {"status": "FAIL", "message": "未发现设计系统文件", "suggestion": "完成设计系统定义：确保 .trae/specs/ 下包含完整的设计规范文档", "details": {"design_files": 0}}


def _check_design_review_product(project_path: str) -> dict[str, Any]:
    root = Path(project_path)
    product_keywords = ["product-review", "product_review", "需求评审", "产品评审", "prd-review", "prd_review"]
    search_dirs = [root / ".trae", root / "docs"]
    found_files: list[Path] = []
    for d in search_dirs:
        if d.exists():
            found_files.extend(_find_files_by_name_part(d, product_keywords))
    if found_files:
        return {"status": "PASS", "message": f"发现{len(found_files)}个产品设计评审文件", "details": {"files_found": len(found_files)}}
    return {"status": "FAIL", "message": "未发现产品设计评审文件", "suggestion": "完成产品设计评审：确保产品需求文档经过评审并标记为已审核", "details": {"files_found": 0}}


def _check_design_review_tech(project_path: str) -> dict[str, Any]:
    root = Path(project_path)
    tech_keywords = ["tech-review", "tech_review", "技术评审", "架构评审", "arch-review", "arch_review"]
    search_dirs = [root / ".trae", root / "docs"]
    found_files: list[Path] = []
    for d in search_dirs:
        if d.exists():
            found_files.extend(_find_files_by_name_part(d, tech_keywords))
    if found_files:
        return {"status": "PASS", "message": f"发现{len(found_files)}个技术评审文件", "details": {"files_found": len(found_files)}}
    return {"status": "FAIL", "message": "未发现技术评审文件", "suggestion": "完成技术评审：确保技术方案经过评审并标记为已审核", "details": {"files_found": 0}}


def _check_design_review_design(project_path: str) -> dict[str, Any]:
    root = Path(project_path)
    design_keywords = ["design-review", "design_review", "ui-review", "ux-review", "设计评审"]
    search_dirs = [root / ".trae", root / "docs"]
    found_files: list[Path] = []
    for d in search_dirs:
        if d.exists():
            found_files.extend(_find_files_by_name_part(d, design_keywords))
    if found_files:
        return {"status": "PASS", "message": f"发现{len(found_files)}个设计评审文件", "details": {"files_found": len(found_files)}}
    return {"status": "FAIL", "message": "未发现设计评审文件", "suggestion": "完成设计评审：确保设计文档经过至少一人评审并标记为已审核", "details": {"files_found": 0}}


def _check_subagent_review(project_path: str) -> dict[str, Any]:
    root = Path(project_path)
    review_keywords = ["review", "subagent", "agent-review"]
    search_dirs = [root / ".trae", root / ".xuansto"]
    found_files: list[Path] = []
    for d in search_dirs:
        if d.exists():
            found_files.extend(_find_files_by_name_part(d, review_keywords))
    if found_files:
        return {"status": "PASS", "message": f"发现{len(found_files)}个评审产物文件", "details": {"files_found": len(found_files)}}
    return {"status": "FAIL", "message": "未发现评审产物文件", "suggestion": "完成子Agent审查：确保代码经过至少一个子Agent的审查", "details": {"files_found": 0}}


def _check_review_confidence(project_path: str) -> dict[str, Any]:
    root = Path(project_path)
    confidence_keywords = ["confidence", "score", "评分", "置信度"]
    search_dirs = [root / ".trae", root / ".xuansto"]
    found_files: list[Path] = []
    for d in search_dirs:
        if d.exists():
            found_files.extend(_find_files_by_name_part(d, confidence_keywords))
    if found_files:
        return {"status": "PASS", "message": f"发现{len(found_files)}个评审置信度文件", "details": {"files_found": len(found_files)}}
    return {"status": "FAIL", "message": "未发现评审置信度文件", "suggestion": "提高审查置信度：确保审查覆盖率 > 80%，关键路径 100%", "details": {"files_found": 0}}


def _check_playwright_e2e(project_path: str) -> dict[str, Any]:
    root = Path(project_path)
    e2e_patterns = ["*.spec.ts", "*.spec.js", "*.e2e.ts", "*.e2e.js", "playwright.config.*"]
    e2e_files: list[Path] = []
    for p in e2e_patterns:
        e2e_files.extend(root.rglob(p))
    e2e_files = [f for f in e2e_files if f.is_file()]
    has_playwright = (root / "playwright.config.ts").exists() or (root / "playwright.config.js").exists()
    if e2e_files or has_playwright:
        return {"status": "PASS", "message": f"发现{len(e2e_files)}个E2E测试文件", "details": {"e2e_files": len(e2e_files), "playwright_config": has_playwright}}
    return {"status": "FAIL", "message": "未发现E2E测试文件", "suggestion": "修复 E2E 测试：运行 `pytest tests/e2e/ --headed` 调试失败用例", "details": {"e2e_files": 0, "playwright_config": False}}


def _check_ai_pentest(project_path: str) -> dict[str, Any]:
    root = Path(project_path)
    security_keywords = ["pentest", "security-test", "vulnerability", "owasp", "渗透"]
    search_dirs = [root / "tests", root / "test", root / ".trae"]
    found_files: list[Path] = []
    for d in search_dirs:
        if d.exists():
            found_files.extend(_find_files_by_name_part(d, security_keywords))
    if found_files:
        return {"status": "PASS", "message": f"发现{len(found_files)}个安全测试文件", "details": {"files_found": len(found_files)}}
    return {"status": "FAIL", "message": "未发现安全测试文件", "suggestion": "修复安全漏洞：参考 OWASP Top 10 进行修复", "details": {"files_found": 0}}


def _check_infra_health(project_path: str) -> dict[str, Any]:
    root = Path(project_path)
    infra_keywords = ["docker-compose", "Dockerfile", "health-check", "healthcheck", "monitoring", "prometheus", "grafana"]
    found_files: list[Path] = []
    for kw in infra_keywords:
        found_files.extend(root.rglob(kw))
        found_files.extend(root.rglob(f"{kw}.*"))
    found_files = [f for f in found_files if f.is_file()]
    if found_files:
        return {"status": "PASS", "message": f"发现{len(found_files)}个基础设施配置文件", "details": {"files_found": len(found_files)}}
    return {"status": "FAIL", "message": "未发现基础设施配置文件", "suggestion": "确保基础设施健康：检查服务可用性、资源使用率、日志完整性", "details": {"files_found": 0}}


def _check_simplification_behavior(project_path: str) -> dict[str, Any]:
    root = Path(project_path)
    simplify_keywords = ["simplif", "refactor", "cleanup"]
    search_dirs = [root / ".trae", root / ".xuansto"]
    found_files: list[Path] = []
    for d in search_dirs:
        if d.exists():
            found_files.extend(_find_files_by_name_part(d, simplify_keywords))
    if found_files:
        return {"status": "PASS", "message": f"发现{len(found_files)}个简化记录文件", "details": {"files_found": len(found_files)}}
    return {"status": "FAIL", "message": "未发现简化记录文件", "suggestion": "验证简化后行为不变：运行完整测试套件确认无回归", "details": {"files_found": 0}}


def _check_chesterton_fence(project_path: str) -> dict[str, Any]:
    root = Path(project_path)
    fence_markers = ["CHESTERTON", "FENCE", "DO-NOT-REMOVE", "PRESERVE", "chesterton", "fence"]
    source_patterns = ["*.py", "*.ts", "*.js", "*.md"]
    source_files: list[Path] = []
    for p in source_patterns:
        source_files.extend(root.rglob(p))
    source_files = [f for f in source_files if f.is_file() and "node_modules" not in str(f) and ".git" not in str(f)]
    fence_count = 0
    for sf in source_files[:200]:
        try:
            content = sf.read_text(encoding="utf-8", errors="ignore")
            if any(m in content for m in fence_markers):
                fence_count += 1
        except OSError:
            pass
    if fence_count > 0:
        return {"status": "PASS", "message": f"发现{fence_count}个围栏标记文件", "details": {"fence_marked_files": fence_count}}
    return {"status": "FAIL", "message": "未发现围栏标记", "suggestion": "谨慎移除代码：确保理解被移除代码的原始意图，避免引入隐含缺陷", "details": {"fence_marked_files": 0}}


def _check_ipc_contract(project_path: str) -> dict[str, Any]:
    root = Path(project_path)
    ipc_keywords = ["ipc", "ipc-contract", "ipc-contract", "channel", "bridge"]
    search_dirs = [root / ".trae", root / "src"]
    found_files: list[Path] = []
    for d in search_dirs:
        if d.exists():
            found_files.extend(_find_files_by_name_part(d, ipc_keywords))
    ipc_patterns = ["*ipc*", "*channel*", "*bridge*", "*preload*"]
    for p in ipc_patterns:
        found_files.extend(root.rglob(p))
    found_files = list({str(f): f for f in found_files if f.is_file()}.values())
    if found_files:
        return {"status": "PASS", "message": f"发现{len(found_files)}个IPC契约定义文件", "details": {"files_found": len(found_files)}}
    return {"status": "FAIL", "message": "未发现IPC契约定义文件", "suggestion": "验证 IPC 契约：确保主进程与渲染进程通信协议一致", "details": {"files_found": 0}}


_SKIP_DIRS = {"node_modules", ".git", "__pycache__", ".venv", "venv", ".tox", "dist", "build"}


def _should_skip(path: Path, root: Path) -> bool:
    try:
        rel = path.relative_to(root)
    except ValueError:
        return False
    return any(part in _SKIP_DIRS for part in rel.parts)


def _check_gate_007(project_path: str) -> dict[str, Any]:
    root = Path(project_path)
    source_patterns = ["*.py", "*.js", "*.ts"]
    source_files: list[Path] = []
    for p in source_patterns:
        source_files.extend(root.rglob(p))
    source_files = [f for f in source_files if f.is_file() and not _should_skip(f, root)]
    issues: list[dict[str, str]] = []
    for sf in source_files[:300]:
        try:
            raw = sf.read_bytes()
            if raw[:3] == b"\xef\xbb\xbf":
                issues.append({"file": str(sf.relative_to(root)), "issue": "UTF-8 BOM marker detected"})
            content = raw.decode("utf-8", errors="replace")
            if "\ufffd" in content:
                issues.append({"file": str(sf.relative_to(root)), "issue": "U+FFFD replacement character detected"})
        except OSError:
            pass
    if issues:
        file_list = ", ".join(sorted(set(i["file"] for i in issues[:10])))
        return {
            "status": "FAIL",
            "message": f"发现{len(issues)}个编码问题",
            "suggestion": f"修复编码问题：使用 `dos2unix` 或编辑器设置 UTF-8 无 BOM 编码保存文件: {file_list}",
            "details": {"issues": issues[:20], "total_issues": len(issues)},
        }
    return {"status": "PASS", "message": "未发现编码问题", "details": {"files_scanned": len(source_files)}}


def _check_comment_language(project_path: str) -> dict[str, Any]:
    import re

    root = Path(project_path)
    source_patterns = ["*.py", "*.js", "*.ts"]
    source_files: list[Path] = []
    for p in source_patterns:
        source_files.extend(root.rglob(p))
    source_files = [f for f in source_files if f.is_file() and not _should_skip(f, root)]
    py_comment_re = re.compile(r"#\s*(.*)")
    js_comment_re = re.compile(r"//\s*(.*)")
    js_block_comment_re = re.compile(r"/\*\s*(.*?)\s*\*/", re.DOTALL)
    cn_char_re = re.compile(r"[\u4e00-\u9fff]")
    en_word_re = re.compile(r"[a-zA-Z]{2,}")
    mixed_files: list[dict[str, Any]] = []
    for sf in source_files[:300]:
        try:
            content = sf.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        comments: list[str] = []
        if sf.suffix == ".py":
            for line in content.splitlines():
                m = py_comment_re.search(line)
                if m:
                    comments.append(m.group(1).strip())
        else:
            for line in content.splitlines():
                m = js_comment_re.search(line)
                if m:
                    comments.append(m.group(1).strip())
            for m in js_block_comment_re.finditer(content):
                comments.append(m.group(1).strip())
        comments = [c for c in comments if len(c) >= 2]
        if not comments:
            continue
        cn_count = sum(1 for c in comments if cn_char_re.search(c))
        en_count = sum(1 for c in comments if en_word_re.search(c))
        total = len(comments)
        if cn_count > 0 and en_count > 0:
            mixing_ratio = (cn_count + en_count) / total
            if mixing_ratio > 0.3:
                mixed_files.append({
                    "file": str(sf.relative_to(root)),
                    "cn_comments": cn_count,
                    "en_comments": en_count,
                    "total_comments": total,
                    "mixing_ratio": round(mixing_ratio, 2),
                })
    if mixed_files:
        file_list = ", ".join(f["file"] for f in mixed_files[:10])
        return {
            "status": "FAIL",
            "message": f"发现{len(mixed_files)}个文件注释中英文混用",
            "suggestion": f"统一注释语言：以下文件注释混用中英文，建议统一为一种语言: {file_list}",
            "details": {"mixed_files": mixed_files[:20], "total_mixed": len(mixed_files)},
        }
    return {"status": "PASS", "message": "注释语言一致性检查通过", "details": {"files_scanned": len(source_files)}}


def _check_file_encoding(project_path: str) -> dict[str, Any]:
    root = Path(project_path)
    text_extensions = {
        ".py", ".js", ".ts", ".tsx", ".jsx", ".json", ".yaml", ".yml",
        ".md", ".txt", ".csv", ".toml", ".cfg", ".ini", ".sh", ".bat",
        ".html", ".css", ".scss", ".less", ".xml", ".sql", ".env",
    }
    all_files: list[Path] = []
    for f in root.rglob("*"):
        if f.is_file() and f.suffix in text_extensions and not _should_skip(f, root):
            all_files.append(f)
    non_utf8: list[dict[str, str]] = []
    bom_files: list[dict[str, str]] = []
    for f in all_files[:500]:
        try:
            raw = f.read_bytes()
            if raw[:3] == b"\xef\xbb\xbf":
                bom_files.append({"file": str(f.relative_to(root)), "issue": "UTF-8 BOM"})
            elif raw[:2] in (b"\xff\xfe", b"\xfe\xff"):
                bom_files.append({"file": str(f.relative_to(root)), "issue": "UTF-16 BOM"})
            try:
                raw.decode("utf-8")
            except UnicodeDecodeError:
                non_utf8.append({"file": str(f.relative_to(root)), "issue": "非UTF-8编码"})
        except OSError:
            pass
    all_issues = non_utf8 + bom_files
    if all_issues:
        file_list = ", ".join(sorted(set(i["file"] for i in all_issues[:10])))
        return {
            "status": "FAIL",
            "message": f"发现{len(all_issues)}个编码不合规文件",
            "suggestion": f"修复文件编码：将以下文件转换为 UTF-8 编码: {file_list}",
            "details": {
                "non_utf8_files": non_utf8[:20],
                "bom_files": bom_files[:20],
                "total_issues": len(all_issues),
            },
        }
    return {"status": "PASS", "message": "所有文件编码合规(UTF-8)", "details": {"files_scanned": len(all_files)}}


def _check_script_security(project_path: str) -> dict[str, Any]:
    root = Path(project_path)
    scripts_dir = root / "scripts"
    script_patterns = ["*.sh", "*.bash", "*.py", "*.ps1", "*.bat", "*.cmd"]
    script_files: list[Path] = []
    if scripts_dir.exists():
        for p in script_patterns:
            script_files.extend(scripts_dir.rglob(p))
    script_files = [f for f in script_files if f.is_file()]
    secret_patterns = [
        "api_key=", "apikey=", "api-key=",
        "password=", "passwd=",
        "secret=", "secret_key=",
        "token=", "access_token=",
        "private_key=",
        "auth=",
    ]
    dangerous_commands = [
        "rm -rf /", "rm -rf /*",
        "sudo rm",
        "chmod 777",
        "curl | sh", "curl | bash", "wget | sh", "wget | bash",
        "> /dev/sda",
        "mkfs.",
        "dd if=",
    ]
    vulnerabilities: list[dict[str, str]] = []
    for sf in script_files:
        try:
            content = sf.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        content_lower = content.lower()
        for pattern in secret_patterns:
            if pattern in content_lower:
                for line_no, line in enumerate(content.splitlines(), 1):
                    if pattern in line.lower():
                        if "example" not in line.lower() and "placeholder" not in line.lower() and "xxx" not in line.lower():
                            vulnerabilities.append({
                                "file": str(sf.relative_to(root)),
                                "line": str(line_no),
                                "type": "hardcoded_secret",
                                "detail": f"疑似硬编码密钥: {pattern}",
                            })
                            break
        for cmd in dangerous_commands:
            if cmd in content_lower:
                vulnerabilities.append({
                    "file": str(sf.relative_to(root)),
                    "type": "dangerous_command",
                    "detail": f"危险命令: {cmd}",
                })
    if vulnerabilities:
        issue_list = ", ".join(sorted(set(v["detail"] for v in vulnerabilities[:10])))
        return {
            "status": "FAIL",
            "message": f"发现{len(vulnerabilities)}个安全问题",
            "suggestion": f"修复安全问题：{issue_list}。将硬编码密钥移至环境变量，移除危险命令",
            "details": {"vulnerabilities": vulnerabilities[:20], "total_vulnerabilities": len(vulnerabilities)},
        }
    return {"status": "PASS", "message": "未发现脚本安全问题", "details": {"scripts_scanned": len(script_files)}}


DECLARED_GATE_IDS: list[str] = [
    "DESIGN-REVIEW-PRODUCT",
    "DESIGN-REVIEW-TECH",
    "DESIGN-REVIEW-DESIGN",
    "DESIGN-TOKENS",
    "DESIGN-SYSTEM-COMPLETE",
    "ANTI-PATTERN-CHECK",
    "GATE-001",
    "GATE-002",
    "BRAINSTORM-COMPLETE",
    "GATE-003",
    "GATE-004",
    "PLAN-ATOMIC",
    "SPEC-ATOMIC",
    "TEST-FIRST",
    "GATE-007",
    "TEST-PASS",
    "GATE-009",
    "MULTI-PERSPECTIVE-COVERAGE",
    "TDD-RED",
    "TDD-GREEN",
    "TDD-REFACTOR",
    "EXECUTION-VERIFY",
    "SCRIPT-SECURITY",
    "SCRIPT-CLEANUP",
    "TOKEN-BUDGET",
    "GATE-011",
    "GATE-012",
    "SPEC-CONSISTENCY",
    "AGENTIC-SECURITY",
    "AI-PENTEST",
    "VISUAL-REGRESSION",
    "RENDER-CHECK",
    "ACCESSIBILITY",
    "PERFORMANCE",
    "SECURITY-FIX-CLOSED",
    "GATE-013",
    "GATE-014",
    "UX-ACCEPTANCE",
    "DOD-CHECK",
    "GATE-015",
    "DOC-COMPLETENESS",
    "SIMPLIFICATION-BEHAVIOR",
    "CHESTERTON-FENCE",
    "DESKTOP-BUILD",
    "DESKTOP-SIGN",
    "DESKTOP-UPDATE",
    "DESKTOP-CROSS",
    "IPC-CONTRACT",
    "ITERATION-BUDGET",
    "SESSION-RECOVERY",
    "BUILD-SUCCESS",
    "ROLLBACK-SAFETY",
    "INIT-COMPLETE",
    "STATUS-HEALTHY",
    "SUBAGENT-REVIEW",
    "REVIEW-CONFIDENCE",
    "PLAYWRIGHT-E2E-PASS",
    "INFRA-HEALTH",
    "COMMENT-LANGUAGE",
    "FILE-ENCODING",
]

INLINE_CHECKS: dict[str, Callable[[str], dict[str, Any]] | None] = {
    "TEST-PASS": _check_test_pass,
    "SPEC-CONSISTENCY": _check_spec_consistency,
    "BRAINSTORM-COMPLETE": _check_brainstorm_complete,
    "PLAN-ATOMIC": _check_plan_atomic,
    "UX-ACCEPTANCE": _check_ux_acceptance,
    "DESKTOP-BUILD": _check_desktop_build,
    "DESKTOP-SIGN": _check_desktop_sign,
    "DESKTOP-UPDATE": _check_desktop_update,
    "DESKTOP-CROSS": _check_desktop_cross,
    "GATE-001": _check_gate_001,
    "GATE-002": _check_gate_002,
    "GATE-003": _check_gate_003,
    "GATE-004": _check_gate_004,
    "GATE-009": _check_gate_009,
    "GATE-011": _check_gate_011,
    "GATE-012": _check_gate_012,
    "GATE-013": _check_gate_013,
    "GATE-014": _check_gate_014,
    "GATE-015": _check_gate_015,
    "ANTI-PATTERN-CHECK": _check_anti_pattern,
    "DESIGN-SYSTEM-COMPLETE": _check_design_system_complete,
    "DESIGN-REVIEW-PRODUCT": _check_design_review_product,
    "DESIGN-REVIEW-TECH": _check_design_review_tech,
    "DESIGN-REVIEW-DESIGN": _check_design_review_design,
    "SUBAGENT-REVIEW": _check_subagent_review,
    "REVIEW-CONFIDENCE": _check_review_confidence,
    "PLAYWRIGHT-E2E-PASS": _check_playwright_e2e,
    "AI-PENTEST": _check_ai_pentest,
    "INFRA-HEALTH": _check_infra_health,
    "SIMPLIFICATION-BEHAVIOR": _check_simplification_behavior,
    "CHESTERTON-FENCE": _check_chesterton_fence,
    "IPC-CONTRACT": _check_ipc_contract,
    "GATE-007": _check_gate_007,
    "COMMENT-LANGUAGE": _check_comment_language,
    "FILE-ENCODING": _check_file_encoding,
    "SCRIPT-SECURITY": _check_script_security,
    "DESIGN-TOKENS": None,
    "SPEC-ATOMIC": None,
    "TEST-FIRST": None,
    "MULTI-PERSPECTIVE-COVERAGE": None,
    "TDD-RED": None,
    "TDD-GREEN": None,
    "TDD-REFACTOR": None,
    "EXECUTION-VERIFY": None,
    "SCRIPT-CLEANUP": None,
    "TOKEN-BUDGET": None,
    "AGENTIC-SECURITY": None,
    "VISUAL-REGRESSION": None,
    "RENDER-CHECK": None,
    "ACCESSIBILITY": None,
    "PERFORMANCE": None,
    "SECURITY-FIX-CLOSED": None,
    "DOD-CHECK": None,
    "DOC-COMPLETENESS": None,
    "ITERATION-BUDGET": None,
    "SESSION-RECOVERY": None,
    "BUILD-SUCCESS": None,
    "ROLLBACK-SAFETY": None,
    "INIT-COMPLETE": None,
    "STATUS-HEALTHY": None,
}


_GATE_CACHE_DIR_NAME = ".xuansto"

_MAX_SCAN_DEPTH = 10
_MAX_SCAN_FILES = 5000
_SKIP_HASH_DIRS = frozenset({
    ".git", "__pycache__", "node_modules", ".xuansto",
    ".venv", "venv", ".mypy_cache", ".pytest_cache", ".ruff_cache",
})

_file_hash_cache: dict[str, dict[str, str]] = {}
_file_mtime_cache: dict[str, dict[str, float]] = {}
_hash_cache_lock = threading.Lock()
_HASH_CACHE_PATH = WORK_DIR / "file_hashes.json"


def _load_persistent_hash_cache() -> None:
    global _file_hash_cache, _file_mtime_cache
    if not _HASH_CACHE_PATH.exists():
        return
    try:
        data = json.loads(_HASH_CACHE_PATH.read_text(encoding="utf-8"))
        with _hash_cache_lock:
            for proj_path, entries in data.items():
                _file_hash_cache[proj_path] = {}
                _file_mtime_cache.setdefault(proj_path, {})
                for rel, info in entries.items():
                    if isinstance(info, dict) and "hash" in info and "mtime" in info:
                        _file_hash_cache[proj_path][rel] = info["hash"]
                        _file_mtime_cache[proj_path][rel] = info["mtime"]
    except (json.JSONDecodeError, OSError, TypeError):
        pass


_load_persistent_hash_cache()


def _save_persistent_hash_cache() -> None:
    with _hash_cache_lock:
        merged: dict[str, dict[str, dict[str, Any]]] = {}
        all_projects = set(_file_hash_cache.keys()) | set(_file_mtime_cache.keys())
        for proj in all_projects:
            hashes = _file_hash_cache.get(proj, {})
            mtimes = _file_mtime_cache.get(proj, {})
            entries: dict[str, dict[str, Any]] = {}
            for rel in set(hashes.keys()) | set(mtimes.keys()):
                entries[rel] = {
                    "hash": hashes.get(rel, ""),
                    "mtime": mtimes.get(rel, 0.0),
                }
            merged[proj] = entries
    with contextlib.suppress(OSError):
        atomic_write(_HASH_CACHE_PATH, json.dumps(merged, ensure_ascii=False, indent=2))


def _compute_file_hashes(project_path: str, force_refresh: bool = False) -> dict[str, str]:
    project = Path(project_path).resolve()
    proj_key = str(project)

    with _hash_cache_lock:
        if force_refresh:
            _file_hash_cache.pop(proj_key, None)
            _file_mtime_cache.pop(proj_key, None)

        cached_hashes = dict(_file_hash_cache.get(proj_key, {}))
        cached_mtimes = dict(_file_mtime_cache.get(proj_key, {}))

    current_mtimes: dict[str, float] = {}
    current_files: set[str] = set()

    for fpath in project.rglob("*"):
        if not fpath.is_file():
            continue
        try:
            rel = str(fpath.relative_to(project))
        except ValueError:
            continue
        parts = Path(rel).parts
        if any(part in _SKIP_HASH_DIRS for part in parts):
            continue
        depth = len(parts) - 1
        if depth > _MAX_SCAN_DEPTH:
            continue
        if len(current_files) >= _MAX_SCAN_FILES:
            break
        current_files.add(rel)
        try:
            current_mtimes[rel] = fpath.stat().st_mtime
        except OSError:
            current_files.discard(rel)
            continue

    result_hashes: dict[str, str] = {}
    recomputed = 0

    for rel in sorted(current_files):
        mtime = current_mtimes[rel]
        cached_mtime = cached_mtimes.get(rel)
        if cached_mtime is not None and cached_mtime == mtime and rel in cached_hashes:
            result_hashes[rel] = cached_hashes[rel]
        else:
            try:
                content = (project / rel).read_bytes()
                result_hashes[rel] = hashlib.sha256(content).hexdigest()
                recomputed += 1
            except (OSError, PermissionError):
                current_files.discard(rel)
                continue

    with _hash_cache_lock:
        _file_hash_cache[proj_key] = result_hashes
        _file_mtime_cache[proj_key] = {rel: current_mtimes[rel] for rel in result_hashes}
    _save_persistent_hash_cache()

    if recomputed > 0:
        logger.debug("_compute_file_hashes: %d files total, %d recomputed, %d cached", len(result_hashes), recomputed, len(result_hashes) - recomputed)

    return result_hashes


def _load_gate_cache(project_path: str) -> dict[str, Any]:
    cache_path = Path(project_path).resolve() / _GATE_CACHE_DIR_NAME / "gate_cache.json"
    if not cache_path.exists():
        return {}
    try:
        data = cache_path.read_text(encoding="utf-8")
        loaded: dict[str, Any] = json.loads(data)
        return loaded
    except (json.JSONDecodeError, OSError):
        return {}


def _save_gate_cache(project_path: str, cache: dict[str, Any]) -> None:
    cache_path = Path(project_path).resolve() / _GATE_CACHE_DIR_NAME / "gate_cache.json"
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    atomic_write(cache_path, json.dumps(cache, ensure_ascii=False, indent=2))


def _is_cache_valid(cache: dict[str, Any], current_hashes: dict[str, str]) -> bool:
    if "file_hashes" not in cache:
        return False
    cached_hashes = cache["file_hashes"]
    if set(cached_hashes.keys()) != set(current_hashes.keys()):
        return False
    return all(cached_hashes.get(k) == v for k, v in current_hashes.items())


def register(mcp: FastMCP) -> None:
    @mcp.tool(
        annotations=ToolAnnotations(
            readOnlyHint=False,
            destructiveHint=False,
            idempotentHint=True,
            openWorldHint=False,
        )
    )
    async def quality_gate_check(
        gate_ids: list[str] | None = None,
        phase: str | None = None,
        project_path: str = ".",
        severity_filter: str = "all",
        force_refresh: bool = False,
    ) -> dict[str, Any]:
        """执行54项质量门禁检查，支持按门禁ID或开发阶段(0-8)过滤。自动映射门禁到检查脚本，返回PASS/FAIL/SKIP状态和详细结果。Prefer using Resource xuansto://gates/list for read-only access."""
        validated, err = validate_input(QualityGateCheckInput, gate_ids=gate_ids, phase=phase, project_path=project_path, severity_filter=severity_filter, force_refresh=force_refresh)
        if err:
            return err
        logger.info("quality_gate_check called: gate_ids=%s phase=%s", gate_ids, phase)
        try:
            safe_path, path_err = validate_path_safety(project_path, allow_absolute=True)
            if path_err:
                return make_error_response(ValueError(path_err), error_code=ERR_VALIDATION)
            gates_to_check = _resolve_gates(gate_ids, phase)

            current_hashes = await asyncio.to_thread(_compute_file_hashes, project_path, force_refresh=force_refresh)
            cache = await asyncio.to_thread(_load_gate_cache, project_path)
            cache_hit = not force_refresh and _is_cache_valid(cache, current_hashes)
            cache_age = 0.0
            if cache_hit and "timestamp" in cache:
                ts = cache["timestamp"]
                if isinstance(ts, (int, float)):
                    cache_age = time.time() - ts
                else:
                    try:
                        cache_age = (datetime.now(timezone.utc) - datetime.fromisoformat(ts)).total_seconds()
                    except (ValueError, OSError):
                        cache_age = 0.0

            if cache_hit and "checks" in cache:
                cached_checks = cache["checks"]
                cached_gate_ids = {c["gate_id"] for c in cached_checks}
                if set(gates_to_check).issubset(cached_gate_ids):
                    filtered = [c for c in cached_checks if c["gate_id"] in gates_to_check]
                    for c in filtered:
                        c["source"] = "cache"
                    passed = sum(1 for c in filtered if c["status"] == "PASS")
                    failed = sum(1 for c in filtered if c["status"] == "FAIL")
                    return make_success_response({
                        "checks": filtered,
                        "summary": {
                            "total": len(filtered),
                            "passed": passed,
                            "failed": failed,
                            "skipped": sum(1 for c in filtered if c["status"] == "SKIP"),
                            "blocked": any(c["status"] == "FAIL" for c in filtered),
                        },
                        "cache_info": {
                            "hit": True,
                            "hit_count": len(filtered),
                            "miss_count": 0,
                            "cache_age_seconds": round(cache_age, 1),
                        },
                    })

            checks: list[dict[str, Any]] = []
            hard_gate_wait_start = time.time()

            for gate_id in gates_to_check:
                hard_gate_result = _check_hard_gate(gate_id)
                if not hard_gate_result["approved"]:
                    wait_duration = time.time() - hard_gate_wait_start
                    logger.info("hard_gate_wait_duration: gate_id=%s wait_seconds=%.2f", gate_id, wait_duration)
                    checks.append({
                        "gate_id": gate_id,
                        "status": "BLOCKED",
                        "source": "hard_gate",
                        "message": "安全硬门禁：必须人工确认",
                        "hard_gate": True,
                        "auto_approve": False,
                        "reason": hard_gate_result["reason"],
                    })
                    continue
                script = GATE_SCRIPTS_MAP.get(gate_id)
                if script:
                    script_path = SCRIPTS_DIR / script
                    if not script_path.exists():
                        if gate_id in INLINE_CHECKS and INLINE_CHECKS[gate_id] is not None:
                            try:
                                inline_result = await asyncio.to_thread(INLINE_CHECKS[gate_id], project_path)
                                check_entry: dict[str, Any] = {
                                    "gate_id": gate_id,
                                    "status": inline_result["status"],
                                    "source": "inline",
                                    "details": {
                                        "message": inline_result["message"],
                                        **inline_result.get("details", {}),
                                    },
                                }
                                if "suggestion" in inline_result:
                                    check_entry["suggestion"] = inline_result["suggestion"]
                                checks.append(check_entry)
                            except Exception as e:
                                checks.append({"gate_id": gate_id, "status": "ERROR", "source": "inline", "details": str(e)})
                            continue
                        if gate_id in INLINE_CHECKS and INLINE_CHECKS[gate_id] is None:
                            checks.append({
                                "gate_id": gate_id,
                                "status": "SKIP",
                                "source": "no_inline_check",
                                "message": "该门禁无内嵌检查，需外部脚本支持",
                                "severity": "WARN",
                            })
                        else:
                            checks.append({"gate_id": gate_id, "status": "SKIP", "source": "no_inline_check", "details": "检查脚本不存在且无内嵌检查"})
                        continue
                    try:
                        result = await asyncio.to_thread(
                            subprocess.run,
                            [sys.executable, str(script_path), "--format", "json"],
                            capture_output=True,
                            text=True,
                            timeout=30,
                            cwd=project_path,
                        )
                        parsed = _parse_gate_result(gate_id, result)
                        parsed["source"] = "script"
                        checks.append(parsed)
                    except subprocess.TimeoutExpired:
                        checks.append({"gate_id": gate_id, "status": "SKIP", "source": "script", "details": "执行超时(30s)"})
                    except Exception as e:
                        checks.append({"gate_id": gate_id, "status": "ERROR", "source": "script", "details": str(e)})
                elif gate_id in INLINE_CHECKS:
                    if INLINE_CHECKS[gate_id] is None:
                        checks.append({
                            "gate_id": gate_id,
                            "status": "SKIP",
                            "source": "no_inline_check",
                            "message": "该门禁无内嵌检查，需外部脚本支持",
                            "severity": "WARN",
                        })
                    else:
                        try:
                            inline_result = await asyncio.to_thread(INLINE_CHECKS[gate_id], project_path)
                            check_entry = {
                                "gate_id": gate_id,
                                "status": inline_result["status"],
                                "source": "inline",
                                "details": {
                                    "message": inline_result["message"],
                                    **inline_result.get("details", {}),
                                },
                            }
                            if "suggestion" in inline_result:
                                check_entry["suggestion"] = inline_result["suggestion"]
                            checks.append(check_entry)
                        except Exception as e:
                            checks.append({"gate_id": gate_id, "status": "ERROR", "source": "inline", "details": str(e)})
                else:
                    checks.append({
                        "gate_id": gate_id,
                        "status": "SKIP",
                        "source": "no_inline_check",
                        "details": "无对应检查脚本，需手动验证",
                    })

            passed = sum(1 for c in checks if c["status"] == "PASS")
            failed = sum(1 for c in checks if c["status"] == "FAIL")
            blocked = any(c["status"] == "FAIL" for c in checks) or any(c.get("hard_gate") for c in checks)

            if blocked:
                failed_ids = [c["gate_id"] for c in checks if c["status"] == "FAIL" or c.get("hard_gate")]
                notify(f"Quality gates blocked: {failed_ids}", "warning")

            await asyncio.to_thread(_save_gate_cache, project_path, {
                "file_hashes": current_hashes,
                "checks": checks,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            })

            cache_hit_count = 0
            cache_miss_count = len(checks)

            return make_success_response({
                "checks": checks,
                "summary": {
                    "total": len(checks),
                    "passed": passed,
                    "failed": failed,
                    "skipped": sum(1 for c in checks if c["status"] == "SKIP"),
                    "blocked": blocked,
                    "hard_gate_blocked": sum(1 for c in checks if c.get("hard_gate")),
                },
                "cache_info": {
                    "hit": cache_hit,
                    "hit_count": cache_hit_count,
                    "miss_count": cache_miss_count,
                    "cache_age_seconds": round(cache_age, 1) if cache_hit else 0.0,
                },
            })
        except Exception as e:
            logger.error("quality_gate_check error: %s", e)
            return make_error_response(e)
