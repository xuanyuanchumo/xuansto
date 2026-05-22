import hashlib
import logging
import os
import re
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

logger = logging.getLogger("knowledge-server")

_ERROR_PATTERNS = {
    "python": [
        re.compile(r"Traceback \(most recent call last\)"),
        re.compile(r"^(\w+Error|\w+Exception):\s*(.*)", re.MULTILINE),
    ],
    "javascript": [
        re.compile(r"(\w+Error):\s*(.*?)\s+at\s+", re.DOTALL),
        re.compile(r"at\s+(\S+)\s+\(([^)]+):(\d+):(\d+)\)"),
    ],
    "java": [
        re.compile(r"^([\w.]+Exception|[\w.]+Error):\s*(.*)", re.MULTILINE),
        re.compile(r"at\s+([\w.$]+)\(([\w.]+):(\d+)\)"),
    ],
    "go": [
        re.compile(r"panic:\s*(.*)"),
        re.compile(r"goroutine\s+\d+\s+\[running\]:"),
        re.compile(r"([\w/.]+)\.go:(\d+)"),
    ],
    "rust": [
        re.compile(r"thread\s+'[^']*'\s+panicked\s+at\s+(.*?),\s+([^:]+):(\d+):(\d+)"),
        re.compile(r"panic!\((.*?)\)"),
    ],
}

_DIFF_FILE_PATTERN = re.compile(r"^---\s+a/(.+)|^\+\+\+\s+b/(.+)", re.MULTILINE)
_DIFF_HUNK_PATTERN = re.compile(r"^@@\s+-(\d+)(?:,(\d+))?\s+\+(\d+)(?:,(\d+))?\s+@@", re.MULTILINE)
_DIFF_FUNC_PATTERN = re.compile(r"^@@.*@@\s+(.*)", re.MULTILINE)

_JS_TS_EXTS = {".js", ".jsx", ".ts", ".tsx", ".mjs", ".cjs"}
_PYTHON_EXTS = {".py"}
_JAVA_EXTS = {".java", ".kt", ".scala"}
_GO_EXTS = {".go"}
_RUST_EXTS = {".rs"}
_CSHARP_EXTS = {".cs"}

_TECH_STACK_MAP = {
    "python": _PYTHON_EXTS,
    "javascript": _JS_TS_EXTS,
    "typescript": _JS_TS_EXTS,
    "java": _JAVA_EXTS,
    "go": _GO_EXTS,
    "rust": _RUST_EXTS,
    "csharp": _CSHARP_EXTS,
}

_ERROR_TYPE_TAG_MAP = {
    "ImportError": "import",
    "ModuleNotFoundError": "import",
    "TypeError": "type",
    "ValueError": "value",
    "KeyError": "key",
    "IndexError": "index",
    "AttributeError": "attribute",
    "NameError": "name",
    "SyntaxError": "syntax",
    "IndentationError": "syntax",
    "RuntimeError": "runtime",
    "RecursionError": "recursion",
    "MemoryError": "memory",
    "TimeoutError": "timeout",
    "ConnectionError": "network",
    "FileNotFoundError": "file",
    "PermissionError": "permission",
    "OSError": "os",
    "ReferenceError": "reference",
    "RangeError": "range",
    "SyntaxError": "syntax",
    "TypeError": "type",
    "UriError": "uri",
    "NullPointerException": "null-pointer",
    "ClassCastException": "class-cast",
    "IndexOutOfBoundsException": "index",
    "IllegalArgumentException": "argument",
    "StackOverflowError": "stack-overflow",
    "OutOfMemoryError": "memory",
    "ConcurrentModificationException": "concurrency",
    "ArrayIndexOutOfBoundsException": "index",
    "ArithmeticException": "arithmetic",
    "NoSuchElementException": "missing",
}


def _detect_tech_stack(project_path: str) -> list[str]:
    stack = []
    root = Path(project_path)

    if (root / "package.json").exists():
        stack.append("javascript")
        try:
            import json
            with open(root / "package.json", "r", encoding="utf-8") as f:
                pkg = json.load(f)
            deps = {**pkg.get("dependencies", {}), **pkg.get("devDependencies", {})}
            if any("typescript" in k or "@types/" in k for k in deps):
                stack.append("typescript")
            if any("react" in k for k in deps):
                stack.append("react")
            if any("vue" in k for k in deps):
                stack.append("vue")
            if any("next" in k for k in deps):
                stack.append("nextjs")
        except Exception:
            pass

    if (root / "tsconfig.json").exists():
        if "typescript" not in stack:
            stack.append("typescript")

    if (root / "requirements.txt").exists() or (root / "pyproject.toml").exists() or (root / "setup.py").exists():  # setup.py is legacy
        if "python" not in stack:
            stack.append("python")

    if (root / "pom.xml").exists() or (root / "build.gradle").exists() or (root / "build.gradle.kts").exists():
        stack.append("java")

    if (root / "go.mod").exists():
        stack.append("go")

    if (root / "Cargo.toml").exists():
        stack.append("rust")

    if (root / "*.sln").exists() or list(root.glob("*.csproj")):
        stack.append("csharp")

    if not stack:
        ext_counts: dict[str, int] = {}
        try:
            for item in root.rglob("*"):
                if item.is_file():
                    ext = item.suffix.lower()
                    for tech, exts in _TECH_STACK_MAP.items():
                        if ext in exts:
                            ext_counts[tech] = ext_counts.get(tech, 0) + 1
        except Exception:
            pass
        if ext_counts:
            sorted_stacks = sorted(ext_counts.items(), key=lambda x: x[1], reverse=True)
            stack = [s for s, _ in sorted_stacks[:3]]

    return stack


def _infer_tags_from_error(error_type: str, tech_stack: list[str]) -> list[str]:
    tags = []

    base_error = error_type.split(".")[-1] if "." in error_type else error_type
    mapped = _ERROR_TYPE_TAG_MAP.get(base_error)
    if mapped:
        tags.append(mapped)

    for tech in tech_stack:
        tags.append(tech)

    return list(dict.fromkeys(tags))


def _generate_entry_id(prefix: str = "exp") -> str:
    return f"{prefix}-{datetime.now(timezone.utc).strftime('%Y%m%d')}-{uuid.uuid4().hex[:6]}"


def _build_content_bug_fix(error_info: dict, fix_info: dict) -> str:
    sections = []

    symptom = error_info.get("symptom", "")
    error_type = error_info.get("error_type", "")
    stack_trace = error_info.get("stack_trace", "")

    sections.append(f"## 症状\n{symptom}" if symptom else f"## 症状\n{error_type}")

    if stack_trace:
        trace_lines = stack_trace.strip().split("\n")
        if len(trace_lines) > 10:
            sections.append(f"## 堆栈摘要\n```\n" + "\n".join(trace_lines[:5]) + "\n...\n" + "\n".join(trace_lines[-5:]) + "\n```")
        else:
            sections.append(f"## 堆栈信息\n```\n{stack_trace.strip()}\n```")

    root_cause = fix_info.get("root_cause", "")
    if root_cause:
        sections.append(f"## 根因\n{root_cause}")

    solution = fix_info.get("solution", "")
    if solution:
        sections.append(f"## 解决方案\n{solution}")

    diff_summary = fix_info.get("diff_summary", "")
    if diff_summary:
        sections.append(f"## 变更摘要\n{diff_summary}")

    test_result = fix_info.get("test_result", "")
    if test_result:
        sections.append(f"## 验证结果\n{test_result}")

    return "\n\n".join(sections)


def _build_content_3strike(attempts: list) -> str:
    sections = ["## 3-Strike 失败经验", "", "**状态：待验证**", ""]

    for attempt in attempts:
        num = attempt.get("attempt_number", "?")
        strategy = attempt.get("strategy", "unknown")
        reason = attempt.get("failure_reason", "unknown")
        sections.append(f"### 尝试 #{num}")
        sections.append(f"- 策略: {strategy}")
        sections.append(f"- 失败原因: {reason}")
        sections.append("")

    sections.append("### 经验教训")
    sections.append("以上策略均未成功解决问题，需要进一步分析或寻求外部协助。")

    return "\n".join(sections)


def _build_content_pattern(pattern_info: dict) -> str:
    sections = []

    name = pattern_info.get("name", "")
    if name:
        sections.append(f"## 模式: {name}")

    description = pattern_info.get("description", "")
    if description:
        sections.append(f"## 描述\n{description}")

    code_example = pattern_info.get("code_example", "")
    if code_example:
        sections.append(f"## 代码示例\n```\n{code_example}\n```")

    scenarios = pattern_info.get("applicable_scenarios", [])
    if scenarios:
        sections.append("## 适用场景")
        for s in scenarios:
            sections.append(f"- {s}")

    return "\n\n".join(sections)


def _build_content_optimization(optimization_info: dict) -> str:
    sections = []

    before = optimization_info.get("before_baseline", "")
    after = optimization_info.get("after_baseline", "")
    approach = optimization_info.get("approach", "")

    if before:
        sections.append(f"## 优化前基线\n{before}")
    if after:
        sections.append(f"## 优化后基线\n{after}")
    if approach:
        sections.append(f"## 优化方法\n{approach}")

    metrics = optimization_info.get("metrics", {})
    if metrics:
        sections.append("## 性能指标")
        for key, value in metrics.items():
            sections.append(f"- {key}: {value}")

    return "\n\n".join(sections)


class ExperiencePrecipitator:

    def precipitate_bug_fix(self, error_info: dict, fix_info: dict, project_path: str) -> dict:
        tech_stack = _detect_tech_stack(project_path)
        error_type = error_info.get("error_type", "unknown")
        tags = _infer_tags_from_error(error_type, tech_stack)
        tags.insert(0, "bug-fix")

        content = _build_content_bug_fix(error_info, fix_info)

        symptom = error_info.get("symptom", "")
        root_cause = fix_info.get("root_cause", "")
        solution = fix_info.get("solution", "")

        title_parts = [f"[Bug修复] {error_type}"]
        if symptom:
            short_symptom = symptom[:60] + ("..." if len(symptom) > 60 else "")
            title_parts.append(short_symptom)
        title = " - ".join(title_parts)

        summary_parts = []
        if root_cause:
            summary_parts.append(f"根因: {root_cause[:80]}")
        if solution:
            summary_parts.append(f"方案: {solution[:80]}")
        summary = "; ".join(summary_parts) if summary_parts else f"修复 {error_type} 错误"

        return {
            "id": _generate_entry_id("exp"),
            "title": title,
            "content": content,
            "scope": "experience",
            "type": "bug_fix",
            "category": "error-solution",
            "confidence": 0.70,
            "tags": tags,
            "summary": summary,
            "source_path": project_path,
            "source_rating": 3,
            "occurrences": 1,
        }

    def precipitate_3strike_failure(self, attempts: list, project_path: str) -> dict:
        tech_stack = _detect_tech_stack(project_path)
        tags = ["bug-fix", "3-strike", "pending-verification"]
        tags.extend(tech_stack)

        content = _build_content_3strike(attempts)

        strategies = ", ".join(a.get("strategy", "?") for a in attempts)
        title = f"[3-Strike失败] 多策略未解决 - {strategies[:80]}"

        summary = f"尝试 {len(attempts)} 次策略均失败，待验证。策略: {strategies[:100]}"

        return {
            "id": _generate_entry_id("exp"),
            "title": title,
            "content": content,
            "scope": "experience",
            "type": "bug_fix",
            "category": "error-solution",
            "confidence": 0.40,
            "tags": tags,
            "summary": summary,
            "source_path": project_path,
            "source_rating": 2,
            "occurrences": 1,
        }

    def precipitate_pattern(self, pattern_info: dict, project_path: str) -> dict:
        tech_stack = _detect_tech_stack(project_path)
        tags = ["pattern"]
        tags.extend(tech_stack)

        name = pattern_info.get("name", "unnamed-pattern")
        tags.append(name.lower().replace(" ", "-"))

        content = _build_content_pattern(pattern_info)

        title = f"[成功模式] {name}"

        description = pattern_info.get("description", "")
        summary = description[:120] if description else f"模式: {name}"

        return {
            "id": _generate_entry_id("exp"),
            "title": title,
            "content": content,
            "scope": "experience",
            "type": "pattern",
            "category": "pattern",
            "confidence": 0.75,
            "tags": tags,
            "summary": summary,
            "source_path": project_path,
            "source_rating": 4,
            "occurrences": 1,
        }

    def precipitate_optimization(self, optimization_info: dict, project_path: str) -> dict:
        tech_stack = _detect_tech_stack(project_path)
        tags = ["optimization", "performance"]
        tags.extend(tech_stack)

        content = _build_content_optimization(optimization_info)

        approach = optimization_info.get("approach", "优化")
        title = f"[性能优化] {approach[:80]}"

        before = optimization_info.get("before_baseline", "")
        after = optimization_info.get("after_baseline", "")
        summary = f"优化方法: {approach[:60]}"
        if before and after:
            summary += f"; {before} → {after}"

        return {
            "id": _generate_entry_id("exp"),
            "title": title,
            "content": content,
            "scope": "experience",
            "type": "optimization",
            "category": "performance",
            "confidence": 0.70,
            "tags": tags,
            "summary": summary,
            "source_path": project_path,
            "source_rating": 3,
            "occurrences": 1,
        }


def extract_error_info(error_output: str) -> dict:
    result = {
        "error_type": "unknown",
        "message": "",
        "file": "",
        "line": 0,
        "stack_trace": "",
    }

    if not error_output or not error_output.strip():
        return result

    text = error_output.strip()

    traceback_match = _ERROR_PATTERNS["python"][0].search(text)
    if traceback_match:
        result["stack_trace"] = text
        result["error_type"] = "python"
        error_line_match = _ERROR_PATTERNS["python"][1].search(text)
        if error_line_match:
            result["error_type"] = error_line_match.group(1)
            result["message"] = error_line_match.group(2).strip()
        file_match = re.search(r'File\s+"([^"]+)",\s+line\s+(\d+)', text)
        if file_match:
            result["file"] = file_match.group(1)
            result["line"] = int(file_match.group(2))

    if result["error_type"] == "unknown":
        for pattern in _ERROR_PATTERNS["javascript"]:
            m = pattern.search(text)
            if m:
                result["error_type"] = m.group(1)
                result["message"] = m.group(2).strip() if m.lastindex >= 2 else ""
                result["stack_trace"] = text
                at_match = re.search(r"at\s+\S+\s+\(([^)]+):(\d+):(\d+)\)", text)
                if at_match:
                    result["file"] = at_match.group(1)
                    result["line"] = int(at_match.group(2))
                break

    if result["error_type"] == "unknown":
        java_exception_match = _ERROR_PATTERNS["java"][0].search(text)
        java_at_match = _ERROR_PATTERNS["java"][1].search(text)
        if java_exception_match or java_at_match:
            if java_exception_match:
                full_name = java_exception_match.group(1)
                result["error_type"] = full_name.split(".")[-1]
                result["message"] = java_exception_match.group(2).strip() if java_exception_match.lastindex >= 2 else ""
            elif java_at_match:
                exception_name_match = re.search(r"^([\w.]+(?:Exception|Error))\b", text, re.MULTILINE)
                if exception_name_match:
                    result["error_type"] = exception_name_match.group(1).split(".")[-1]
            result["stack_trace"] = text
            if java_at_match:
                result["file"] = java_at_match.group(2)
                result["line"] = int(java_at_match.group(3))

    if result["error_type"] == "unknown":
        for pattern in _ERROR_PATTERNS["go"]:
            m = pattern.search(text)
            if m:
                result["error_type"] = "panic"
                result["message"] = m.group(1).strip() if m.lastindex else ""
                result["stack_trace"] = text
                file_match = re.search(r"([\w/.]+)\.go:(\d+)", text)
                if file_match:
                    result["file"] = file_match.group(1) + ".go"
                    result["line"] = int(file_match.group(2))
                break

    if result["error_type"] == "unknown":
        for pattern in _ERROR_PATTERNS["rust"]:
            m = pattern.search(text)
            if m:
                result["error_type"] = "panic"
                result["message"] = m.group(1).strip() if m.lastindex >= 1 else ""
                result["stack_trace"] = text
                if m.lastindex and m.lastindex >= 2:
                    result["file"] = m.group(2)
                    result["line"] = int(m.group(3))
                break

    if result["error_type"] == "unknown":
        generic_error = re.search(r"(?:error|ERROR|Error)[\s:]+(.+?)(?:\n|$)", text)
        if generic_error:
            result["error_type"] = "generic-error"
            result["message"] = generic_error.group(1).strip()
            result["stack_trace"] = text

    if not result["stack_trace"]:
        result["stack_trace"] = text

    return result


def extract_fix_summary(diff_text: str) -> dict:
    result = {
        "files_changed": [],
        "strategy": "unknown",
        "key_changes": [],
    }

    if not diff_text or not diff_text.strip():
        return result

    files = set()
    for m in _DIFF_FILE_PATTERN.finditer(diff_text):
        old_file = m.group(1)
        new_file = m.group(2)
        if new_file:
            files.add(new_file)
        elif old_file:
            files.add(old_file)

    result["files_changed"] = sorted(files)

    functions = []
    for m in _DIFF_FUNC_PATTERN.finditer(diff_text):
        func_desc = m.group(1).strip()
        if func_desc and func_desc not in functions:
            functions.append(func_desc)
    result["key_changes"] = functions[:10]

    additions = diff_text.count("\n+")
    deletions = diff_text.count("\n-")

    if additions > 0 and deletions == 0:
        result["strategy"] = "addition"
    elif additions == 0 and deletions > 0:
        result["strategy"] = "deletion"
    elif additions > 0 and deletions > 0:
        ratio = additions / deletions if deletions > 0 else float("inf")
        if 0.5 <= ratio <= 2.0:
            result["strategy"] = "replacement"
        elif ratio > 2.0:
            result["strategy"] = "addition"
        else:
            result["strategy"] = "deletion"
    else:
        result["strategy"] = "refactor"

    return result


def _compute_text_similarity(text_a: str, text_b: str) -> float:
    if not text_a or not text_b:
        return 0.0

    tokens_a = set(re.findall(r'\w+', text_a.lower()))
    tokens_b = set(re.findall(r'\w+', text_b.lower()))

    if not tokens_a or not tokens_b:
        return 0.0

    intersection = tokens_a & tokens_b
    union = tokens_a | tokens_b

    return len(intersection) / len(union) if union else 0.0


def _compute_content_fingerprint(content: str) -> str:
    normalized = re.sub(r'\s+', ' ', content.lower().strip())
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()[:32]


def check_and_merge(existing_entries: list, new_entry: dict, similarity_threshold: float = 0.85) -> dict:
    result = {
        "action": "new",
        "target_id": None,
        "merged_content": None,
    }

    if not existing_entries:
        return result

    new_content = new_entry.get("content", "")
    new_summary = new_entry.get("summary", "")
    new_text = f"{new_summary} {new_content}".strip()

    best_similarity = 0.0
    best_entry = None

    for existing in existing_entries:
        existing_content = existing.get("content", "")
        existing_summary = existing.get("summary", "")
        existing_text = f"{existing_summary} {existing_content}".strip()

        sim = _compute_text_similarity(new_text, existing_text)

        new_fp = _compute_content_fingerprint(new_content)
        existing_fp = _compute_content_fingerprint(existing_content)
        if new_fp == existing_fp:
            sim = 1.0

        if sim > best_similarity:
            best_similarity = sim
            best_entry = existing

    if best_similarity > similarity_threshold and best_entry is not None:
        new_confidence = new_entry.get("confidence", 0.6)
        existing_confidence = best_entry.get("confidence", 0.6)

        if new_confidence >= existing_confidence:
            primary = new_entry
            secondary = best_entry
        else:
            primary = best_entry
            secondary = new_entry

        primary_content = primary.get("content", "")
        secondary_content = secondary.get("content", "")
        unique_parts = []

        secondary_lines = secondary_content.split("\n")
        for line in secondary_lines:
            line_stripped = line.strip()
            if line_stripped and line_stripped not in primary_content:
                unique_parts.append(line)

        merged_content = primary_content
        if unique_parts:
            supplement = "\n".join(unique_parts)
            merged_content = f"{primary_content}\n\n---\n### 补充信息\n{supplement}"

        merged_tags = list(set(
            primary.get("tags", []) + secondary.get("tags", [])
        ))

        merged_confidence = max(new_confidence, existing_confidence)

        result["action"] = "merge"
        result["target_id"] = best_entry.get("id")
        result["merged_content"] = merged_content
        result["merged_tags"] = merged_tags
        result["merged_confidence"] = merged_confidence
        result["similarity_score"] = best_similarity

    elif best_similarity > 0.70 and best_entry is not None:
        result["action"] = "new"
        result["target_id"] = best_entry.get("id")
        result["cross_ref_id"] = best_entry.get("id")
        result["similarity_score"] = best_similarity

    return result
