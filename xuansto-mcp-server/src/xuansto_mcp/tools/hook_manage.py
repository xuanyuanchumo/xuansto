"""
Hook管理模块。

hooks.json: 声明式配置文件，定义Hook名称、触发类型(matcher)、执行动作和参数。
hook_manage.py: 运行时接口，提供INLINE_HOOK_LOGIC内嵌执行逻辑和MCP工具注册。

两者关系: hooks.json描述"何时触发+做什么"，hook_manage.py实现"怎么做"。
当脚本不可用时，INLINE_HOOK_LOGIC作为内嵌降级逻辑执行。
"""

from __future__ import annotations

import asyncio
import contextlib
import json
import re
import subprocess
from collections.abc import Callable
from pathlib import Path
from typing import Any

from mcp.server.fastmcp import FastMCP
from mcp.types import ToolAnnotations

from ..core.config import HOOK_SCRIPTS_MAP, SCRIPTS_DIR
from ..core.errors import ERR_INTERNAL, ERR_VALIDATION, make_error_response, make_success_response
from ..core.hook_engine import get_hook_timeout
from ..core.logging_config import get_logger
from ..core.subprocess_utils import run_script
from ..core.validator import validate_input
from ..models.schemas import HookManageInput

logger = get_logger("hook_manage")

HOOK_PROFILES = {
    "minimal": ["security-block", "session-save"],
    "standard": ["security-block", "token-budget-check", "auto-format", "encoding-check", "load-context", "kb-health-check", "session-save", "git-status-check", "experience-precipitate", "save-state"],
    "strict": list(HOOK_SCRIPTS_MAP.keys()),
}

PHASE_HOOK_PROFILE_MAP: dict[int, str] = {
    0: "minimal",
    1: "standard",
    2: "standard",
    3: "strict",
}

_DANGEROUS_PATTERNS = [
    re.compile(r"\brm\s+-rf\b", re.IGNORECASE),
    re.compile(r"\bDROP\s+TABLE\b", re.IGNORECASE),
    re.compile(r"\bsudo\b", re.IGNORECASE),
    re.compile(r"\bchmod\s+777\b", re.IGNORECASE),
    re.compile(r"\bformat\s+[A-Z]:", re.IGNORECASE),
    re.compile(r"\bdd\s+if=", re.IGNORECASE),
    re.compile(r">\s*/dev/sd", re.IGNORECASE),
    re.compile(r"\bmkfs\b", re.IGNORECASE),
]

_MODERATE_DANGEROUS_PATTERNS = [
    re.compile(r"\bgit\s+push\s+--force\b", re.IGNORECASE),
    re.compile(r"\bgit\s+push\s+-f\b", re.IGNORECASE),
    re.compile(r"\bnpm\s+publish\b", re.IGNORECASE),
    re.compile(r"\bpip\s+upload\b", re.IGNORECASE),
    re.compile(r"\bdocker\s+rm\b", re.IGNORECASE),
    re.compile(r"\bkubectl\s+delete\b", re.IGNORECASE),
    re.compile(r"\bALTER\s+TABLE\b", re.IGNORECASE),
    re.compile(r"\bTRUNCATE\b", re.IGNORECASE),
]

_CONSOLE_LOG_PATTERNS = [
    re.compile(r"\bconsole\.log\s*\("),
    re.compile(r"\bprint\s*\("),
    re.compile(r"\bfmt\.Println\s*\("),
    re.compile(r"\bfmt\.Printf\s*\("),
    re.compile(r"\bSystem\.out\.println\s*\("),
]

_SOURCE_EXTENSIONS = {".py", ".js", ".ts", ".tsx", ".jsx", ".go", ".java", ".rb", ".rs", ".c", ".cpp", ".h"}

_TEST_DIR_NAMES = {"test", "tests", "__tests__", "spec", "specs"}

_TEST_FILE_PATTERNS = [
    re.compile(r"_test\.\w+$"),
    re.compile(r"\.test\.\w+$"),
    re.compile(r"\.spec\.\w+$"),
    re.compile(r"test_\w+\.\w+$"),
]


def _is_test_file(filepath: Path) -> bool:
    name = filepath.name
    for pat in _TEST_FILE_PATTERNS:
        if pat.search(name):
            return True
    parts = filepath.parts
    return any(part.lower() in _TEST_DIR_NAMES for part in parts)


def _security_block_logic(project_path: str, context: dict[str, Any] | None = None) -> dict[str, Any]:
    command = ""
    if context:
        command = context.get("command", "") or context.get("tool_input", "") or ""
    if not command:
        return {"status": "pass", "message": "无可检查的命令", "details": {}}
    matched = []
    for pat in _DANGEROUS_PATTERNS:
        m = pat.search(command)
        if m:
            matched.append(m.group())
    if matched:
        return {
            "status": "block",
            "message": f"检测到危险命令模式: {', '.join(matched)}",
            "details": {"matched_patterns": matched, "command": command},
        }
    return {"status": "pass", "message": "未检测到危险命令", "details": {"command": command}}


def _dangerous_cmd_confirm_logic(project_path: str, context: dict[str, Any] | None = None) -> dict[str, Any]:
    command = ""
    if context:
        command = context.get("command", "") or context.get("tool_input", "") or ""
    if not command:
        return {"status": "pass", "message": "无可检查的命令", "details": {}}
    matched = []
    for pat in _MODERATE_DANGEROUS_PATTERNS:
        m = pat.search(command)
        if m:
            matched.append(m.group())
    if matched:
        return {
            "status": "warn",
            "message": f"检测到需确认的命令: {', '.join(matched)}",
            "details": {"matched_patterns": matched, "command": command},
        }
    return {"status": "pass", "message": "未检测到需确认的命令", "details": {"command": command}}


def _auto_format_logic(project_path: str, context: dict[str, Any] | None = None) -> dict[str, Any]:
    root = Path(project_path)
    if not root.exists():
        return {"status": "pass", "message": "项目路径不存在，跳过格式检查", "details": {}}
    issues = []
    target_dirs = {"src", "lib", "app", "pkg", "cmd"}
    scan_dirs = []
    for d in root.iterdir():
        if d.is_dir() and d.name in target_dirs:
            scan_dirs.append(d)
    if not scan_dirs:
        scan_dirs = [root]
    for scan_dir in scan_dirs:
        for filepath in scan_dir.rglob("*"):
            if not filepath.is_file():
                continue
            if filepath.suffix not in _SOURCE_EXTENSIONS:
                continue
            if _is_test_file(filepath):
                continue
            try:
                content = filepath.read_text(encoding="utf-8", errors="ignore")
            except Exception:
                continue
            lines = content.splitlines(keepends=True)
            file_issues = []
            for i, line in enumerate(lines, 1):
                if line.rstrip("\r\n") != line.rstrip():
                    file_issues.append({"line": i, "type": "trailing_whitespace"})
                if "\t" in line and " " in line[:8]:
                    file_issues.append({"line": i, "type": "mixed_tabs_spaces"})
            if content and not content.endswith("\n"):
                file_issues.append({"line": len(lines), "type": "missing_newline_at_eof"})
            if file_issues:
                rel = str(filepath.relative_to(root))
                issues.append({"file": rel, "problems": file_issues})
            if len(issues) >= 10:
                break
        if len(issues) >= 10:
            break
    if issues:
        return {
            "status": "warn",
            "message": f"发现 {len(issues)} 个文件存在格式问题",
            "details": {"files_with_issues": len(issues), "issues": issues},
        }
    return {"status": "pass", "message": "未发现格式问题", "details": {}}


def _console_log_detect_logic(project_path: str, context: dict[str, Any] | None = None) -> dict[str, Any]:
    root = Path(project_path)
    if not root.exists():
        return {"status": "pass", "message": "项目路径不存在，跳过console检测", "details": {}}
    findings: list[dict[str, Any]] = []
    target_dirs = {"src", "lib", "app", "pkg", "cmd"}
    scan_dirs = []
    for d in root.iterdir():
        if d.is_dir() and d.name in target_dirs:
            scan_dirs.append(d)
    if not scan_dirs:
        scan_dirs = [root]
    for scan_dir in scan_dirs:
        for filepath in scan_dir.rglob("*"):
            if not filepath.is_file():
                continue
            if filepath.suffix not in _SOURCE_EXTENSIONS:
                continue
            if _is_test_file(filepath):
                continue
            try:
                content = filepath.read_text(encoding="utf-8", errors="ignore")
            except Exception:
                continue
            lines = content.splitlines()
            file_hits = []
            for i, line in enumerate(lines, 1):
                for pat in _CONSOLE_LOG_PATTERNS:
                    if pat.search(line):
                        file_hits.append({"line": i, "content": line.strip()[:120]})
                        break
            if file_hits:
                rel = str(filepath.relative_to(root))
                findings.append({"file": rel, "hits": file_hits, "count": len(file_hits)})
            if len(findings) >= 20:
                break
        if len(findings) >= 20:
            break
    total = sum(f["count"] for f in findings)
    if findings:
        return {
            "status": "warn",
            "message": f"在 {len(findings)} 个文件中发现 {total} 处调试输出语句",
            "details": {"files": len(findings), "total_hits": total, "findings": findings},
        }
    return {"status": "pass", "message": "未发现调试输出语句", "details": {}}


def _type_check_logic(project_path: str, context: dict[str, Any] | None = None) -> dict[str, Any]:
    root = Path(project_path)
    if not root.exists():
        return {"status": "pass", "message": "项目路径不存在，跳过类型检查", "details": {}}
    ts_files = list(root.rglob("*.ts")) + list(root.rglob("*.tsx"))
    ts_files = [f for f in ts_files if not _is_test_file(f)]
    if not ts_files:
        return {"status": "pass", "message": "未发现TypeScript文件", "details": {}}
    tsconfig = (root / "tsconfig.json").exists()
    if not tsconfig:
        return {
            "status": "warn",
            "message": f"发现 {len(ts_files)} 个TypeScript文件但缺少tsconfig.json",
            "details": {"ts_file_count": len(ts_files), "has_tsconfig": False},
        }
    return {
        "status": "pass",
        "message": f"TypeScript环境正常，{len(ts_files)} 个文件",
        "details": {"ts_file_count": len(ts_files), "has_tsconfig": True},
    }


def _git_status_check_logic(project_path: str, context: dict[str, Any] | None = None) -> dict[str, Any]:
    root = Path(project_path)
    if not root.exists():
        return {"status": "pass", "message": "项目路径不存在，跳过git状态检查", "details": {}}
    try:
        result = subprocess.run(
            ["git", "status", "--porcelain"],
            capture_output=True,
            text=True,
            timeout=10,
            cwd=str(root),
        )
        if result.returncode != 0:
            return {"status": "pass", "message": "非Git仓库或git不可用", "details": {}}
        lines = [ln for ln in result.stdout.strip().splitlines() if ln.strip()]
        if lines:
            staged = [ln for ln in lines if ln[0] in "MADRC"]
            unstaged = [ln for ln in lines if ln[1] in "MADRC"]
            untracked = [ln for ln in lines if ln.startswith("??")]
            return {
                "status": "warn",
                "message": f"存在未提交的变更: {len(lines)} 个文件",
                "details": {
                    "total": len(lines),
                    "staged": len(staged),
                    "unstaged": len(unstaged),
                    "untracked": len(untracked),
                    "files": [ln.strip() for ln in lines[:20]],
                },
            }
        return {"status": "pass", "message": "工作区干净", "details": {}}
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        return {"status": "pass", "message": "Git不可用，跳过检查", "details": {}}


def _decision_log_persist_logic(project_path: str, context: dict[str, Any] | None = None) -> dict[str, Any]:
    root = Path(project_path)
    if not root.exists():
        return {"status": "pass", "message": "项目路径不存在，跳过决策日志检查", "details": {}}
    decisions_dir = root / ".xuansto" / "decisions"
    if not decisions_dir.exists():
        try:
            decisions_dir.mkdir(parents=True, exist_ok=True)
            return {
                "status": "pass",
                "message": "已创建决策日志目录",
                "details": {"path": str(decisions_dir), "created": True},
            }
        except OSError:
            return {
                "status": "warn",
                "message": "无法创建决策日志目录",
                "details": {"path": str(decisions_dir), "created": False},
            }
    return {
        "status": "pass",
        "message": "决策日志目录已存在",
        "details": {"path": str(decisions_dir), "created": False},
    }


def _token_budget_check_logic(project_path: str, context: dict[str, Any] | None = None) -> dict[str, Any]:
    ratio = 0.0
    if context:
        ratio = float(context.get("token_usage_ratio", 0.0))
    if ratio >= 0.95:
        return {
            "status": "block",
            "message": f"Token预算严重超限: 使用率{ratio:.0%}，已阻断操作",
            "details": {"token_usage_ratio": ratio, "threshold_block": 0.95},
        }
    if ratio >= 0.8:
        return {
            "status": "warn",
            "message": f"Token预算警告: 使用率{ratio:.0%}",
            "details": {"token_usage_ratio": ratio, "threshold_warn": 0.8},
        }
    return {"status": "pass", "message": f"Token预算正常: 使用率{ratio:.0%}", "details": {"token_usage_ratio": ratio}}


def _encoding_check_logic(project_path: str, context: dict[str, Any] | None = None) -> dict[str, Any]:
    root = Path(project_path)
    if not root.exists():
        return {"status": "pass", "message": "项目路径不存在，跳过编码检查", "details": {}}
    target_file = ""
    if context:
        target_file = context.get("file", "") or context.get("path", "")
    check_path = root / target_file if target_file else root
    if target_file and check_path.is_file():
        try:
            raw = check_path.read_bytes()
            issues = []
            if raw[:3] == b"\xef\xbb\xbf":
                issues.append("UTF-8 BOM")
            try:
                raw.decode("utf-8")
            except UnicodeDecodeError:
                issues.append("非UTF-8编码")
            if b"\xfffd" in raw.replace(b"\xef\xbb\xbf", b""):
                issues.append("U+FFFD替换字符")
            if issues:
                return {"status": "warn", "message": f"编码问题: {', '.join(issues)}", "details": {"file": target_file, "issues": issues}}
            return {"status": "pass", "message": "编码检查通过", "details": {"file": target_file}}
        except OSError:
            return {"status": "pass", "message": "无法读取文件，跳过编码检查", "details": {}}
    return {"status": "pass", "message": "编码检查通过(无指定文件)", "details": {}}


def _load_context_logic(project_path: str, context: dict[str, Any] | None = None) -> dict[str, Any]:
    root = Path(project_path)
    logs_dir = root / ".skill-logs"
    if not logs_dir.exists():
        with contextlib.suppress(OSError):
            logs_dir.mkdir(parents=True, exist_ok=True)
        return {"status": "pass", "message": "无历史会话日志，首次会话", "details": {"sessions_found": 0}}
    sessions = sorted(logs_dir.glob("session-*.md"), reverse=True)
    if sessions:
        return {"status": "pass", "message": f"加载最近会话上下文: {sessions[0].name}", "details": {"sessions_found": len(sessions), "latest": sessions[0].name}}
    return {"status": "pass", "message": "无历史会话日志", "details": {"sessions_found": 0}}


def _kb_health_check_logic(project_path: str, context: dict[str, Any] | None = None) -> dict[str, Any]:
    root = Path(project_path)
    kb_dir = root / ".knowledge"
    if not kb_dir.exists():
        return {"status": "warn", "message": "知识库目录不存在", "details": {"kb_exists": False}}
    index_dir = kb_dir / "index"
    has_index = index_dir.exists() and any(index_dir.iterdir()) if index_dir.exists() else False
    if has_index:
        return {"status": "pass", "message": "知识库健康", "details": {"kb_exists": True, "has_index": True}}
    return {"status": "warn", "message": "知识库索引缺失，将使用文件系统降级", "details": {"kb_exists": True, "has_index": False}}


def _platform_detect_logic(project_path: str, context: dict[str, Any] | None = None) -> dict[str, Any]:
    root = Path(project_path)
    detected = []
    if (root / "package.json").exists():
        detected.append("node")
    if (root / "Cargo.toml").exists():
        detected.append("rust")
    if (root / "go.mod").exists():
        detected.append("go")
    if (root / "pyproject.toml").exists() or (root / "setup.py").exists():
        detected.append("python")
    if (root / "pubspec.yaml").exists():
        detected.append("flutter")
    if not detected:
        return {"status": "pass", "message": "未检测到已知平台", "details": {"platforms": []}}
    return {"status": "pass", "message": f"检测到平台: {', '.join(detected)}", "details": {"platforms": detected}}


def _session_save_logic(project_path: str, context: dict[str, Any] | None = None) -> dict[str, Any]:
    root = Path(project_path)
    logs_dir = root / ".skill-logs"
    try:
        logs_dir.mkdir(parents=True, exist_ok=True)
    except OSError:
        return {"status": "warn", "message": "无法创建会话日志目录", "details": {}}
    from datetime import datetime, timezone
    ts = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    session_file = logs_dir / f"session-{ts}.md"
    tasks = context.get("completed_tasks", []) if context else []
    decisions = context.get("decisions", []) if context else []
    content_parts = [f"# Session {ts}\n"]
    if tasks:
        content_parts.append("## Completed Tasks\n" + "\n".join(f"- {t}" for t in tasks))
    if decisions:
        content_parts.append("## Key Decisions\n" + "\n".join(f"- {d}" for d in decisions))
    try:
        session_file.write_text("\n".join(content_parts), encoding="utf-8")
        return {"status": "pass", "message": f"会话已保存: {session_file.name}", "details": {"file": session_file.name}}
    except OSError:
        return {"status": "warn", "message": "无法写入会话文件", "details": {}}


def _experience_precipitate_logic(project_path: str, context: dict[str, Any] | None = None) -> dict[str, Any]:
    root = Path(project_path)
    exp_dir = root / ".knowledge" / "experience"
    try:
        exp_dir.mkdir(parents=True, exist_ok=True)
    except OSError:
        return {"status": "warn", "message": "无法创建经验目录", "details": {}}
    task_completed = False
    if context:
        task_completed = bool(context.get("task_completed", False) or context.get("completed_tasks"))
    if not task_completed:
        return {"status": "pass", "message": "无已完成任务，跳过经验沉淀", "details": {"precipitated": False}}
    return {"status": "pass", "message": "经验沉淀触发条件满足", "details": {"precipitated": True, "target": str(exp_dir)}}


def _pattern_detect_logic(project_path: str, context: dict[str, Any] | None = None) -> dict[str, Any]:
    root = Path(project_path)
    patterns_dir = root / ".knowledge" / "experience" / "patterns"
    error_count = 0
    if context:
        errors = context.get("session_errors", [])
        error_count = len(errors) if isinstance(errors, list) else 0
    if error_count >= 2:
        with contextlib.suppress(OSError):
            patterns_dir.mkdir(parents=True, exist_ok=True)
        return {"status": "warn", "message": f"检测到{error_count}个会话错误，建议分析模式", "details": {"error_count": error_count, "threshold": 2, "output": str(patterns_dir)}}
    return {"status": "pass", "message": f"会话错误数({error_count})低于阈值", "details": {"error_count": error_count}}


def _save_state_logic(project_path: str, context: dict[str, Any] | None = None) -> dict[str, Any]:
    root = Path(project_path)
    cache_dir = root / ".agent_cache"
    try:
        cache_dir.mkdir(parents=True, exist_ok=True)
    except OSError:
        return {"status": "warn", "message": "无法创建缓存目录", "details": {}}
    state_file = cache_dir / "workflow-state.json"
    import json as _json
    state = {
        "current_phase": context.get("current_phase", "") if context else "",
        "workflow_state": context.get("workflow_state", "") if context else "",
        "active_agents": context.get("active_agents", []) if context else [],
    }
    try:
        state_file.write_text(_json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")
        return {"status": "pass", "message": "工作流状态已保存", "details": {"file": str(state_file)}}
    except OSError:
        return {"status": "warn", "message": "无法写入状态文件", "details": {}}


INLINE_HOOK_LOGIC: dict[str, Callable[..., dict[str, Any]]] = {
    "security-block": _security_block_logic,
    "dangerous-cmd-confirm": _dangerous_cmd_confirm_logic,
    "auto-format": _auto_format_logic,
    "console-log-detect": _console_log_detect_logic,
    "type-check": _type_check_logic,
    "git-status-check": _git_status_check_logic,
    "decision-log-persist": _decision_log_persist_logic,
    "token-budget-check": _token_budget_check_logic,
    "encoding-check": _encoding_check_logic,
    "load-context": _load_context_logic,
    "kb-health-check": _kb_health_check_logic,
    "platform-detect": _platform_detect_logic,
    "session-save": _session_save_logic,
    "experience-precipitate": _experience_precipitate_logic,
    "pattern-detect": _pattern_detect_logic,
    "save-state": _save_state_logic,
}

def register(mcp: FastMCP) -> None:
    @mcp.tool(
        annotations=ToolAnnotations(
            readOnlyHint=False,
            destructiveHint=False,
            idempotentHint=False,
            openWorldHint=False,
        )
    )
    async def hook_manage(
        action: str,
        profile: str = "standard",
        hook_name: str | None = None,
        context: dict[str, Any] | None = None,
        phase: int | None = None,
    ) -> dict[str, Any]:
        """Hook管理：列出指定profile的Hook配置，执行指定Hook，查询Phase对应的活跃Hook Profile。支持minimal/standard/strict三种配置级别，16个Hook。"""
        validated, err = validate_input(HookManageInput, action=action, profile=profile, hook_name=hook_name, context=context, phase=phase)
        if err:
            return err
        logger.info("hook_manage called: action=%s hook_name=%s", action, hook_name)
        try:
            if action == "list":
                hooks = HOOK_PROFILES.get(profile, [])
                if not hooks:
                    return make_error_response(ValueError(f"未知profile: {profile}，支持: minimal, standard, strict"), error_code=ERR_VALIDATION)
                result: list[dict[str, Any]] = []
                for h in hooks:
                    script = HOOK_SCRIPTS_MAP.get(h)
                    has_inline = h in INLINE_HOOK_LOGIC
                    result.append({"name": h, "has_script": script is not None, "script": script, "has_inline_logic": has_inline})
                try:
                    from .resource_load_status import _current_phase, _phase_lock
                    with _phase_lock:
                        current_phase_val = _current_phase
                    active_profile = PHASE_HOOK_PROFILE_MAP.get(current_phase_val, "standard")
                except Exception:
                    active_profile = "standard"
                return make_success_response({"profile": profile, "hooks": result, "total": len(result), "active_profile": active_profile})
            elif action == "execute":
                if not hook_name:
                    return make_error_response(ValueError("execute操作需要hook_name参数"), error_code=ERR_VALIDATION)
                script = HOOK_SCRIPTS_MAP.get(hook_name)
                if script:
                    script_path = SCRIPTS_DIR / script
                    if not script_path.exists():
                        inline_fn = INLINE_HOOK_LOGIC.get(hook_name)
                        if inline_fn:
                            project_path = context.get("project_path", ".") if context else "."
                            inline_result = await asyncio.to_thread(inline_fn, project_path, context)
                            return make_success_response({"hook": hook_name, "status": inline_result["status"], "message": inline_result["message"], "details": inline_result["details"], "source": "inline_fallback"})
                        return make_success_response({"hook": hook_name, "status": "skipped", "reason": f"脚本不存在且无内嵌逻辑: {script}"})
                    args = []
                    if context:
                        args.extend(["--context", json.dumps(context, ensure_ascii=False)])
                    script_result = await run_script(script_path, args=args, timeout=get_hook_timeout(hook_name))
                    if script_result.get("error"):
                        error_info = script_result["error"]
                        return make_error_response(Exception(error_info.get("message", "脚本执行失败")), error_code=ERR_INTERNAL)
                    return make_success_response({"hook": hook_name, "status": "executed", "result": script_result.get("data", {})})
                inline_fn = INLINE_HOOK_LOGIC.get(hook_name)
                if inline_fn:
                    project_path = context.get("project_path", ".") if context else "."
                    inline_result = await asyncio.to_thread(inline_fn, project_path, context)
                    return make_success_response({"hook": hook_name, "status": inline_result["status"], "message": inline_result["message"], "details": inline_result["details"], "source": "inline"})
                return make_success_response({"hook": hook_name, "status": "skipped", "reason": "无对应脚本或内联逻辑，需手动执行"})
            elif action == "get_active_profile":
                if phase is None:
                    try:
                        from .resource_load_status import _current_phase, _phase_lock
                        with _phase_lock:
                            phase = _current_phase
                    except Exception:
                        phase = 0
                if phase < 0 or phase > 3:
                    return make_error_response(ValueError(f"无效phase: {phase}，支持0-3"), error_code=ERR_VALIDATION)
                active_profile = PHASE_HOOK_PROFILE_MAP.get(phase, "standard")
                hooks = HOOK_PROFILES.get(active_profile, [])
                return make_success_response({
                    "phase": phase,
                    "active_profile": active_profile,
                    "hooks": hooks,
                    "hook_count": len(hooks),
                })
            else:
                return make_error_response(ValueError(f"未知操作: {action}，支持: list, execute, get_active_profile"), error_code=ERR_VALIDATION)
        except Exception as e:
            logger.error("hook_manage error: %s", e)
            return make_error_response(e)


_HOOK_TOOL_MAP: dict[str, list[str]] = {
    "security-block": ["code_simplify", "security_scan", "spec_drift_detect"],
    "dangerous-cmd-confirm": ["workflow_dispatch"],
    "auto-format": ["code_simplify"],
    "console-log-detect": ["code_simplify"],
    "type-check": ["quality_gate_check"],
    "git-status-check": ["workflow_dispatch"],
    "decision-log-persist": ["workflow_dispatch", "session_manage"],
    "token-budget-check": ["quality_gate_check", "token_budget"],
    "encoding-check": ["quality_gate_check", "code_simplify"],
    "load-context": ["session_manage"],
    "kb-health-check": ["knowledge_search"],
    "platform-detect": ["skill_analyze", "project_init"],
    "session-save": ["session_manage", "workflow_dispatch"],
    "experience-precipitate": ["knowledge_inject", "session_manage"],
    "pattern-detect": ["session_manage", "metrics_report"],
    "save-state": ["session_manage", "workflow_dispatch"],
}


def get_pre_hooks(tool_name: str) -> list[str]:
    hooks = []
    for hook_name, tools in _HOOK_TOOL_MAP.items():
        if tool_name in tools:
            hooks.append(hook_name)
    return hooks


def get_post_hooks(tool_name: str) -> list[str]:
    return ["decision-log-persist"] if tool_name in _HOOK_TOOL_MAP.get("decision-log-persist", []) else []


def execute_pre_hooks(tool_name: str, kwargs: dict[str, Any]) -> tuple[list[dict[str, Any]], list[dict[str, str]]]:
    pre_hooks = get_pre_hooks(tool_name)
    results = []
    errors = []
    for hook_name in pre_hooks:
        inline_fn = INLINE_HOOK_LOGIC.get(hook_name)
        if inline_fn:
            try:
                project_path = kwargs.get("project_path", kwargs.get("target", kwargs.get("skill_path", ".")))
                context = kwargs
                result = inline_fn(project_path, context)
                result["hook"] = hook_name
                results.append(result)
                if result.get("status") == "block":
                    break
            except Exception as e:
                errors.append({"hook": hook_name, "error": str(e)})
                logger.error("Pre-hook %s failed: %s", hook_name, e)
    return results, errors


def execute_post_hooks(tool_name: str, kwargs: dict[str, Any], tool_result: dict[str, Any]) -> list[dict[str, str]]:
    post_hooks = get_post_hooks(tool_name)
    errors = []
    for hook_name in post_hooks:
        inline_fn = INLINE_HOOK_LOGIC.get(hook_name)
        if inline_fn:
            try:
                project_path = kwargs.get("project_path", kwargs.get("target", kwargs.get("skill_path", ".")))
                inline_fn(project_path, {"tool_name": tool_name, "result_summary": str(tool_result)[:200]})
            except Exception as e:
                errors.append({"hook": hook_name, "error": str(e)})
                logger.error("Post-hook %s failed: %s", hook_name, e)
    return errors


async def async_execute_pre_hooks(tool_name: str, kwargs: dict[str, Any]) -> tuple[list[dict[str, Any]], list[dict[str, str]]]:
    try:
        result = await asyncio.to_thread(execute_pre_hooks, tool_name, kwargs)
        return result
    except Exception as e:
        return [], [{"hook": "async_pre_hooks", "error": str(e)}]


async def async_execute_post_hooks(tool_name: str, kwargs: dict[str, Any], result: dict[str, Any]) -> list[dict[str, str]]:
    try:
        errors = await asyncio.to_thread(execute_post_hooks, tool_name, kwargs, result)
        return errors
    except Exception as e:
        return [{"hook": "async_post_hooks", "error": str(e)}]
