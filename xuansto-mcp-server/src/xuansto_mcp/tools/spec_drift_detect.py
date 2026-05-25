from __future__ import annotations

import ast
import re
from pathlib import Path
from typing import Any

from mcp.server.fastmcp import FastMCP
from mcp.types import ToolAnnotations

from ..core.config import SCRIPTS_DIR
from ..core.errors import ERR_VALIDATION, make_error_response, make_success_response
from ..core.logging_config import get_logger
from ..core.subprocess_utils import run_script
from ..core.validator import validate_input, validate_path_safety
from ..models.schemas import SpecDriftDetectInput

logger = get_logger("spec_drift_detect")


def _parse_python_ast(src_dir: str) -> list[dict[str, Any]]:
    src_path = Path(src_dir)
    if not src_path.exists():
        return []
    symbols: list[dict[str, Any]] = []
    for py_file in src_path.rglob("*.py"):
        try:
            tree = ast.parse(py_file.read_text(encoding="utf-8", errors="ignore"))
        except (SyntaxError, OSError):
            continue
        rel = str(py_file.relative_to(src_path)) if src_path.is_dir() else py_file.name
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                symbols.append({"name": node.name.lower(), "type": "function", "file": rel, "line": node.lineno})
            elif isinstance(node, ast.ClassDef):
                symbols.append({"name": node.name.lower(), "type": "class", "file": rel, "line": node.lineno})
                for item in node.body:
                    if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        symbols.append({"name": f"{node.name.lower()}.{item.name.lower()}", "type": "method", "file": rel, "line": item.lineno})
    return symbols


def _match_spec_to_ast(task_desc: str, ast_symbols: list[dict[str, Any]]) -> list[dict[str, Any]]:
    keywords = re.findall(r"[a-zA-Z_]\w*", task_desc.lower())
    keywords = [kw for kw in keywords if len(kw) > 2]
    keywords = list(dict.fromkeys(keywords))[:5]
    if not keywords:
        return []
    matches = []
    for sym in ast_symbols:
        name = sym["name"]
        matched_kws = [kw for kw in keywords if kw in name]
        if matched_kws:
            matches.append({**sym, "matched_keywords": matched_kws, "coverage": len(matched_kws) / len(keywords)})
    return matches


def _inline_spec_drift(spec_dir: str, src_dir: str) -> dict[str, Any]:
    spec_path = Path(spec_dir)
    src_path = Path(src_dir)

    if not spec_path.exists():
        return {
            "total_specs": 0,
            "total_pending_tasks": 0,
            "drifts": [],
            "implementation_rate": 0.0,
            "analysis_level": "none",
            "interface_coverage": 0.0,
        }

    ast_symbols = _parse_python_ast(src_dir)
    analysis_level = "ast" if ast_symbols else "keyword_match"

    tasks_files = list(spec_path.rglob("tasks.md"))

    drifts = []
    total_pending = 0

    for tasks_file in tasks_files:
        content = tasks_file.read_text(encoding="utf-8", errors="ignore")
        for line in content.splitlines():
            match = re.match(r"- \[ \] Task \d+:\s*(.+)", line.strip())
            if not match:
                continue
            total_pending += 1
            task_desc = match.group(1).strip()

            if analysis_level == "ast" and ast_symbols:
                ast_matches = _match_spec_to_ast(task_desc, ast_symbols)
                if ast_matches:
                    best = max(ast_matches, key=lambda m: m["coverage"])
                    drifts.append({
                        "task": task_desc,
                        "spec_file": str(tasks_file),
                        "has_implementation": True,
                        "potential_files": [m["file"] for m in ast_matches[:3]],
                        "best_match": best["name"],
                        "match_coverage": best["coverage"],
                    })
                else:
                    drifts.append({
                        "task": task_desc,
                        "spec_file": str(tasks_file),
                        "has_implementation": False,
                        "potential_files": [],
                        "best_match": None,
                        "match_coverage": 0.0,
                    })
            else:
                keywords = re.findall(r"[a-zA-Z_]\w*", task_desc.lower())
                keywords = [kw for kw in keywords if len(kw) > 2]
                keywords = list(dict.fromkeys(keywords))[:5]
                potential_files = []
                if src_path.exists() and keywords:
                    for src_file in src_path.rglob("*"):
                        if not src_file.is_file():
                            continue
                        fname = src_file.stem.lower()
                        if any(kw in fname for kw in keywords):
                            try:
                                potential_files.append(str(src_file.relative_to(src_path)))
                            except ValueError:
                                potential_files.append(str(src_file))
                drifts.append({
                    "task": task_desc,
                    "spec_file": str(tasks_file),
                    "has_implementation": len(potential_files) > 0,
                    "potential_files": potential_files,
                })

    impl_count = sum(1 for d in drifts if d["has_implementation"])
    impl_rate = impl_count / total_pending if total_pending > 0 else 0.0

    return {
        "total_specs": len(tasks_files),
        "total_pending_tasks": total_pending,
        "drifts": drifts,
        "implementation_rate": impl_rate,
        "analysis_level": analysis_level,
        "interface_coverage": round(impl_rate, 2),
    }


def register(mcp: FastMCP) -> None:
    @mcp.tool(
        annotations=ToolAnnotations(
            readOnlyHint=True,
            destructiveHint=False,
            idempotentHint=True,
            openWorldHint=False,
        )
    )
    async def spec_drift_detect(
        spec_dir: str = ".trae/specs",
        src_dir: str = ".",
    ) -> dict[str, Any]:
        """检测规格文档(spec)与代码实现(src)之间的偏差。扫描规格目录中的任务定义，对比源代码中的实际实现，报告缺失、过期或不一致的规格项。"""
        validated, err = validate_input(SpecDriftDetectInput, spec_dir=spec_dir, src_dir=src_dir)
        if err:
            return err
        logger.info("spec_drift_detect called: spec_dir=%s", spec_dir)
        try:
            safe_spec, spec_err = validate_path_safety(spec_dir, allow_absolute=True)
            if spec_err:
                return make_error_response(ValueError(spec_err), error_code=ERR_VALIDATION)
            safe_src, src_err = validate_path_safety(src_dir, allow_absolute=True)
            if src_err:
                return make_error_response(ValueError(src_err), error_code=ERR_VALIDATION)
            script_path = SCRIPTS_DIR / "spec-drift-detector.py"

            if script_path.exists():
                result = run_script(
                    script_path,
                    args=["--spec-dir", spec_dir, "--src-dir", src_dir, "--format", "json"],
                    timeout=60,
                )
                if not result.get("error"):
                    return make_success_response(result.get("data", {}), degradation_level="script")
                logger.warning("spec_drift_detect degraded: script -> inline")
                from .server_health import track_degradation
                track_degradation("spec_drift_detect")
                inline_result = _inline_spec_drift(spec_dir, src_dir)
                return make_success_response(inline_result, degradation_level="inline")

            logger.warning("spec_drift_detect degraded: no script -> inline")
            from .server_health import track_degradation
            track_degradation("spec_drift_detect")
            inline_result = _inline_spec_drift(spec_dir, src_dir)
            return make_success_response(inline_result, degradation_level="inline")
        except Exception as e:
            logger.error("spec_drift_detect error: %s", e)
            return make_error_response(e)
