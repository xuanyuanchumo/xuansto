from __future__ import annotations

import ast as ast_module
import hashlib
import os
import re
import time
from pathlib import Path
from typing import Any

from mcp.server.fastmcp import FastMCP
from mcp.types import ToolAnnotations

from ..core.config import SCRIPTS_DIR
from ..core.errors import make_success_response, make_error_response, ERR_VALIDATION
from ..core.logging_config import get_logger
from ..core.subprocess_utils import run_script
from ..core.validator import validate_input, validate_path_safety
from ..models.schemas import CodeSimplifyInput

logger = get_logger("code_simplify")

SOURCE_EXTENSIONS = {".py", ".js", ".ts", ".java", ".go"}


def _collect_source_files(target: str, scope: str) -> list[Path]:
    target_path = Path(target).resolve()
    files: list[Path] = []

    if target_path.is_file():
        if target_path.suffix in SOURCE_EXTENSIONS:
            files.append(target_path)
        return files

    if not target_path.is_dir():
        return files

    cutoff = time.time() - 86400 if scope == "recent" else 0

    for root, _dirs, filenames in os.walk(target_path):
        for fname in filenames:
            fpath = Path(root) / fname
            if fpath.suffix not in SOURCE_EXTENSIONS:
                continue
            if scope == "recent":
                try:
                    if fpath.stat().st_mtime < cutoff:
                        continue
                except OSError:
                    continue
            files.append(fpath)

    return files


def _calculate_cyclomatic_complexity(func_node: ast_module.AST) -> int:
    complexity = 1
    for node in ast_module.walk(func_node):
        if isinstance(node, (ast_module.If, ast_module.While, ast_module.For, ast_module.ExceptHandler)):
            complexity += 1
        elif isinstance(node, ast_module.BoolOp):
            complexity += len(node.values) - 1
        elif isinstance(node, (ast_module.ListComp, ast_module.SetComp, ast_module.DictComp, ast_module.GeneratorExp)):
            complexity += sum(1 for _ in node.generators)
    return complexity


def _calculate_quality_score(suggestions: list[dict[str, Any]], total_lines: int) -> int:
    if total_lines == 0:
        return 100
    severity_weights = {"high": 5, "medium": 3, "low": 1}
    total_deduction = 0
    for s in suggestions:
        total_deduction += severity_weights.get(s.get("severity", "low"), 1)
    max_deduction = max(total_lines / 5, 1)
    deduction_ratio = min(total_deduction / max_deduction, 1.0)
    return max(0, int(100 * (1 - deduction_ratio)))


def _analyze_python_ast(file_path: Path, rel: str, suggestions: list[dict[str, Any]], by_type: dict[str, int]) -> None:
    try:
        source = file_path.read_text(encoding="utf-8", errors="replace")
        tree = ast_module.parse(source)
    except (SyntaxError, OSError):
        return
    for node in ast_module.walk(tree):
        if isinstance(node, (ast_module.FunctionDef, ast_module.AsyncFunctionDef)):
            complexity = _calculate_cyclomatic_complexity(node)
            if complexity > 10:
                suggestions.append({
                    "type": "high_complexity",
                    "file": rel,
                    "line": node.lineno,
                    "description": f"函数 {node.name} 圈复杂度 {complexity}，超过 10 阈值",
                    "severity": "high",
                    "complexity": complexity,
                })
                by_type["high_complexity"] = by_type.get("high_complexity", 0) + 1


def _inline_simplify(target: str, scope: str) -> dict[str, Any]:
    suggestions: list[dict[str, Any]] = []
    by_type: dict[str, int] = {
        "long_function": 0,
        "deep_nesting": 0,
        "unused_import": 0,
        "dead_code": 0,
    }

    files = _collect_source_files(target, scope)

    analysis_level = "text_level"
    total_lines = 0
    for fpath in files:
        try:
            lines = fpath.read_text(encoding="utf-8", errors="replace").splitlines()
            total_lines += len(lines)
        except OSError:
            continue

        rel = str(fpath)

        if fpath.suffix == ".py":
            _analyze_python_ast(fpath, rel, suggestions, by_type)
            analysis_level = "ast"
            _detect_python_issues(lines, rel, suggestions, by_type)
        else:
            _detect_generic_issues(lines, rel, suggestions, by_type)

    quality_score = _calculate_quality_score(suggestions, total_lines)

    return {
        "suggestions": suggestions,
        "total": len(suggestions),
        "by_type": by_type,
        "quality_score": quality_score,
        "analysis_level": analysis_level,
    }


def _detect_python_issues(
    lines: list[str],
    rel: str,
    suggestions: list[dict[str, Any]],
    by_type: dict[str, int],
) -> None:
    _detect_long_functions(lines, rel, suggestions, by_type)
    _detect_deep_nesting(lines, rel, suggestions, by_type)
    _detect_unused_imports(lines, rel, suggestions, by_type)
    _detect_dead_code(lines, rel, suggestions, by_type)


def _detect_generic_issues(
    lines: list[str],
    rel: str,
    suggestions: list[dict[str, Any]],
    by_type: dict[str, int],
) -> None:
    _detect_long_functions(lines, rel, suggestions, by_type)
    _detect_deep_nesting(lines, rel, suggestions, by_type)


def _detect_long_functions(
    lines: list[str],
    rel: str,
    suggestions: list[dict[str, Any]],
    by_type: dict[str, int],
) -> None:
    func_starts: list[tuple[int, int]] = []

    for i, line in enumerate(lines):
        stripped = line.lstrip()
        if not stripped:
            continue
        indent = len(line) - len(stripped)
        if re.match(r"^(async\s+)?def\s+", stripped) or re.match(r"^(public|private|protected|static)?\s*(async\s+)?\w+\s*\(", stripped) and indent == 0:
            func_starts.append((i, indent))

    func_starts.append((len(lines), 0))

    for idx in range(len(func_starts) - 1):
        start_line, start_indent = func_starts[idx]
        end_line = func_starts[idx + 1][0]

        actual_end = end_line
        for j in range(start_line + 1, end_line):
            if j < len(lines):
                stripped = lines[j].lstrip()
                if stripped:
                    cur_indent = len(lines[j]) - len(stripped)
                    if cur_indent <= start_indent and stripped:
                        actual_end = j
                        break

        func_len = actual_end - start_line
        if func_len > 50:
            suggestions.append({
                "type": "long_function",
                "file": rel,
                "line": start_line + 1,
                "description": f"函数长度 {func_len} 行，超过 50 行阈值",
                "severity": "medium",
            })
            by_type["long_function"] += 1


def _detect_deep_nesting(
    lines: list[str],
    rel: str,
    suggestions: list[dict[str, Any]],
    by_type: dict[str, int],
) -> None:
    for i, line in enumerate(lines):
        stripped = line.lstrip()
        if not stripped:
            continue
        indent = len(line) - len(stripped)
        levels = indent // 4
        if indent % 4 != 0:
            levels = indent // 2 if indent % 2 == 0 else levels
        if levels > 4:
            suggestions.append({
                "type": "deep_nesting",
                "file": rel,
                "line": i + 1,
                "description": f"嵌套层级 {levels}，超过 4 层阈值",
                "severity": "high",
            })
            by_type["deep_nesting"] += 1


def _detect_unused_imports(
    lines: list[str],
    rel: str,
    suggestions: list[dict[str, Any]],
    by_type: dict[str, int],
) -> None:
    import_pattern = re.compile(r"^import\s+(\w+)")
    from_import_pattern = re.compile(r"^from\s+[\w.]+\s+import\s+(.+)")

    imports: list[tuple[int, str]] = []

    for i, line in enumerate(lines):
        stripped = line.lstrip()
        m = import_pattern.match(stripped)
        if m:
            imports.append((i, m.group(1)))
            continue
        m = from_import_pattern.match(stripped)
        if m:
            names = [n.strip().split(" as ")[0].strip() for n in m.group(1).split(",")]
            for name in names:
                if name and name != "*":
                    imports.append((i, name))

    for line_no, name in imports:
        used = False
        for j, line in enumerate(lines):
            if j == line_no:
                continue
            if re.search(r"\b" + re.escape(name) + r"\b", line):
                used = True
                break
        if not used:
            suggestions.append({
                "type": "unused_import",
                "file": rel,
                "line": line_no + 1,
                "description": f"未使用的导入: {name}",
                "severity": "low",
            })
            by_type["unused_import"] += 1


def _detect_dead_code(
    lines: list[str],
    rel: str,
    suggestions: list[dict[str, Any]],
    by_type: dict[str, int],
) -> None:
    for i, line in enumerate(lines):
        stripped = line.lstrip()
        indent = len(line) - len(stripped)

        if re.match(r"^return\b", stripped):
            for j in range(i + 1, len(lines)):
                next_stripped = lines[j].lstrip()
                if not next_stripped:
                    continue
                next_indent = len(lines[j]) - len(next_stripped)
                if next_indent < indent:
                    break
                if next_indent == indent:
                    if not re.match(r"^(def |class |async def |@)", next_stripped):
                        suggestions.append({
                            "type": "dead_code",
                            "file": rel,
                            "line": j + 1,
                            "description": "return 语句后的不可达代码",
                            "severity": "high",
                        })
                        by_type["dead_code"] += 1
                    break

        if re.match(r"^if\s+False\s*:", stripped):
            suggestions.append({
                "type": "dead_code",
                "file": rel,
                "line": i + 1,
                "description": "if False: 永远不会执行的代码",
                "severity": "high",
            })
            by_type["dead_code"] += 1

        if stripped == "pass":
            in_class = False
            for k in range(i - 1, -1, -1):
                prev_stripped = lines[k].lstrip()
                prev_indent = len(lines[k]) - len(prev_stripped)
                if prev_indent < indent:
                    if re.match(r"^(class |class\()", prev_stripped):
                        in_class = True
                    break
            if not in_class:
                has_abstract = False
                for k in range(max(0, i - 3), i):
                    if re.match(r"^\s*@(abstractmethod|abstract)", lines[k]):
                        has_abstract = True
                        break
                if not has_abstract:
                    suggestions.append({
                        "type": "dead_code",
                        "file": rel,
                        "line": i + 1,
                        "description": "非类/非抽象上下文中的 pass 语句",
                        "severity": "low",
                    })
                    by_type["dead_code"] += 1


def _inline_dedup(target: str) -> dict[str, Any]:
    files = _collect_source_files(target, "dir")
    block_map: list[tuple[str, tuple[str, int]]] = []

    for fpath in files:
        try:
            lines = fpath.read_text(encoding="utf-8", errors="replace").splitlines()
        except OSError:
            continue

        rel = str(fpath)
        code_lines: list[tuple[int, str]] = []
        for idx, line in enumerate(lines):
            stripped = line.strip()
            if stripped and not stripped.startswith("#") and not stripped.startswith("//"):
                code_lines.append((idx, stripped))

        for start in range(len(code_lines) - 2):
            consecutive = True
            for k in range(1, 3):
                if code_lines[start + k][0] != code_lines[start + k - 1][0] + 1:
                    consecutive = False
                    break
            if not consecutive:
                continue
            block_text = "\n".join(code_lines[start + k][1] for k in range(3))
            h = hashlib.md5(block_text.encode()).hexdigest()
            block_map.append((h, (rel, code_lines[start][0] + 1)))

    hash_groups: dict[str, list[tuple[str, int]]] = {}
    for h, location in block_map:
        hash_groups.setdefault(h, []).append(location)

    duplicates: list[dict[str, Any]] = []
    total_duplicate_lines = 0

    for h, locations in hash_groups.items():
        if len(locations) < 2:
            continue
        files_list = sorted(set(loc[0] for loc in locations))
        preview_lines: list[str] = []
        for fpath in files:
            if str(fpath) == files_list[0]:
                try:
                    all_lines = fpath.read_text(encoding="utf-8", errors="replace").splitlines()
                    start = locations[0][1] - 1
                    preview_lines = all_lines[start:start + 3]
                except OSError:
                    pass
                break
        preview = "\n".join(preview_lines)[:200]
        count = len(locations)
        duplicates.append({
            "hash": h,
            "count": count,
            "files": files_list,
            "preview": preview,
        })
        total_duplicate_lines += count * 3

    return {
        "duplicates": duplicates,
        "total_groups": len(duplicates),
        "total_duplicate_lines": total_duplicate_lines,
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
    async def code_simplify(
        target: str,
        scope: str = "recent",
        include_dedup: bool = True,
    ) -> dict[str, Any]:
        """代码简化分析：检测死代码、深层嵌套、过长函数和重复代码。支持文件/目录/最近修改三种扫描范围，返回简化建议和重复代码报告。"""
        validated, err = validate_input(CodeSimplifyInput, target=target, scope=scope, include_dedup=include_dedup)
        if err:
            return err
        logger.info("code_simplify called: target=%s", target)
        try:
            safe_path, path_err = validate_path_safety(target, allow_absolute=True)
            if path_err:
                return make_error_response(ValueError(path_err), error_code=ERR_VALIDATION)
            results: dict[str, Any] = {}
            degradation_level = "full"

            simplifier_path = SCRIPTS_DIR / "code-simplifier.py"
            if simplifier_path.exists():
                result = run_script(
                    simplifier_path,
                    args=["--target", target, "--scope", scope, "--format", "json"],
                    timeout=60,
                )
                if not result.get("error"):
                    results["simplification"] = result.get("data", result)
                else:
                    results["simplification"] = _inline_simplify(target, scope)
                    logger.warning("code_simplify degraded: simplification -> inline")
                    from .server_health import track_degradation
                    track_degradation("code_simplify")
                    degradation_level = "inline"
            else:
                results["simplification"] = _inline_simplify(target, scope)
                logger.warning("code_simplify degraded: simplification -> inline (no script)")
                from .server_health import track_degradation
                track_degradation("code_simplify")
                degradation_level = "inline"

            if include_dedup:
                dedup_path = SCRIPTS_DIR / "deduplication-detector.py"
                if dedup_path.exists():
                    result = run_script(
                        dedup_path,
                        args=["--target", target, "--format", "json"],
                        timeout=60,
                    )
                    if not result.get("error"):
                        results["deduplication"] = result.get("data", result)
                    else:
                        results["deduplication"] = _inline_dedup(target)
                        if degradation_level == "full":
                            degradation_level = "partial"
                else:
                    results["deduplication"] = _inline_dedup(target)
                    if degradation_level == "full":
                        degradation_level = "partial"

            return make_success_response(results, degradation_level=degradation_level)
        except Exception as e:
            logger.error("code_simplify error: %s", e)
            return make_error_response(e)
