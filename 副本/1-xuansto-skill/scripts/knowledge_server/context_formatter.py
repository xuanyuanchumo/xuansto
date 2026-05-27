import logging
import re
from collections import OrderedDict
from typing import Optional

logger = logging.getLogger("knowledge-server")

_CHARS_PER_TOKEN = 4
_HIGH_CONFIDENCE_THRESHOLD = 0.8
_SUMMARY_MAX_CHARS = 500

_SCOPE_LABELS = {
    "general": "通用",
    "workspace": "工作区",
    "experience": "经验",
}

_TYPE_LABELS = {
    "standard": "标准",
    "pattern": "模式",
    "error-solution": "错误方案",
    "bug_fix": "错误方案",
    "glossary": "术语",
    "best-practice": "最佳实践",
    "unknown": "知识",
}

_PRIORITY_ORDER = {
    "bug_fix": 0,
    "error-solution": 0,
    "standard": 1,
    "coding-standards": 1,
    "pattern": 2,
    "best-practice": 2,
    "glossary": 3,
    "unknown": 3,
}


def _entry_priority(entry: dict) -> int:
    entry_type = entry.get("type", "unknown")
    category = entry.get("category", "")
    priorities = []
    for key in (entry_type, category):
        if key and key in _PRIORITY_ORDER:
            priorities.append(_PRIORITY_ORDER[key])
    return min(priorities) if priorities else 3


def _extract_tech_stack_tag(entry: dict) -> str:
    tags = entry.get("tags", [])
    for tag in tags:
        tag_lower = tag.lower()
        for known in ("python", "node", "javascript", "typescript", "react",
                       "vue", "go", "rust", "java", "csharp", "cpp",
                       "docker", "kubernetes", "aws", "gcp", "azure",
                       "fastapi", "django", "flask", "spring", "express",
                       "nextjs", "svelte", "angular"):
            if known in tag_lower:
                return tag
    return ""


def format_knowledge_context(results: list, token_budget: int = 2048, tech_stack: Optional[dict] = None) -> str:
    if not results:
        return ""

    tech_names = set()
    if tech_stack:
        for fw in tech_stack.get("frameworks", []):
            tech_names.add(fw["name"].lower())
        for lang in tech_stack.get("languages", []):
            tech_names.add(lang.lower())

    scored = []
    for entry in results:
        score = 0.0
        confidence = entry.get("confidence", 0.0)
        if confidence >= _HIGH_CONFIDENCE_THRESHOLD:
            score += 2.0
        score += confidence

        if tech_names:
            entry_text = f"{entry.get('title', '')} {entry.get('content', '')} {entry.get('summary', '')}".lower()
            tags = entry.get("tags", [])
            for tag in tags:
                entry_text += f" {tag.lower()}"
            for tech in tech_names:
                if tech in entry_text:
                    score += 1.5
                    break

        scored.append((score, entry))

    scored.sort(key=lambda x: (_entry_priority(x[1]), -x[0]))

    grouped = OrderedDict()
    ungrouped = []
    for score, entry in scored:
        tech_tag = _extract_tech_stack_tag(entry)
        if tech_tag:
            grouped.setdefault(tech_tag, []).append(entry)
        else:
            ungrouped.append(entry)

    budget_chars = token_budget * _CHARS_PER_TOKEN
    header = "## 知识库参考\n"
    footer = ""
    budget_chars -= len(header) + len(footer)

    sections = []
    trimmed_ids = []

    for tech_tag, entries in grouped.items():
        group_header = f"## {tech_tag} 相关知识\n"
        group_chars = len(group_header)
        if group_chars > budget_chars:
            for e in entries:
                trimmed_ids.append(e.get("id", ""))
            continue

        temp_budget = budget_chars - group_chars
        group_sections = []
        for entry in entries:
            section = _format_entry(entry)
            section_chars = len(section) + 1
            if section_chars <= temp_budget:
                group_sections.append(section)
                temp_budget -= section_chars
            else:
                summary_section = _format_entry_summary(entry)
                summary_chars = len(summary_section) + 1
                if summary_chars <= temp_budget:
                    group_sections.append(summary_section)
                    temp_budget -= summary_chars
                    trimmed_ids.append(entry.get("id", ""))
                else:
                    trimmed_ids.append(entry.get("id", ""))

        if group_sections:
            sections.append(group_header + "\n".join(group_sections))
            budget_chars = temp_budget

    for entry in ungrouped:
        section = _format_entry(entry)
        section_chars = len(section) + 1
        if section_chars <= budget_chars:
            sections.append(section)
            budget_chars -= section_chars
        else:
            summary_section = _format_entry_summary(entry)
            summary_chars = len(summary_section) + 1
            if summary_chars <= budget_chars:
                sections.append(summary_section)
                budget_chars -= summary_chars
                trimmed_ids.append(entry.get("id", ""))
            else:
                trimmed_ids.append(entry.get("id", ""))

    if not sections:
        return ""

    body = "\n".join(sections)
    result = header + body + footer

    if trimmed_ids:
        trim_note = f"\n裁剪条目: {', '.join(trimmed_ids[:10])}"
        result += trim_note

    return result


def _format_entry(entry: dict) -> str:
    title = entry.get("title", "无标题")
    confidence = entry.get("confidence", 0.0)
    entry_type = entry.get("type", "unknown")
    scope = entry.get("scope", "workspace")
    entry_id = entry.get("id", "")
    updated = entry.get("updated", "")
    content = entry.get("content", "")

    type_label = _TYPE_LABELS.get(entry_type, entry_type)
    scope_label = _SCOPE_LABELS.get(scope, scope)

    lines = []
    lines.append(f"### {title} ({confidence:.2f} | {type_label})")
    meta_parts = [f"来源:{scope_label}"]
    if updated:
        meta_parts.append(f"更新:{updated[:10]}")
    if entry_id:
        meta_parts.append(f"ID:{entry_id}")
    lines.append(" | ".join(meta_parts))
    lines.append(content)

    return "\n".join(lines)


def _format_entry_summary(entry: dict) -> str:
    title = entry.get("title", "无标题")
    confidence = entry.get("confidence", 0.0)
    entry_type = entry.get("type", "unknown")
    scope = entry.get("scope", "workspace")
    entry_id = entry.get("id", "")
    updated = entry.get("updated", "")
    summary = entry.get("summary", "")

    if not summary:
        content = entry.get("content", "")
        summary = content[:_SUMMARY_MAX_CHARS]
        if len(content) > _SUMMARY_MAX_CHARS:
            summary += "..."

    type_label = _TYPE_LABELS.get(entry_type, entry_type)
    scope_label = _SCOPE_LABELS.get(scope, scope)

    lines = []
    lines.append(f"### {title} ({confidence:.2f} | {type_label}) [摘要]")
    meta_parts = [f"来源:{scope_label}"]
    if updated:
        meta_parts.append(f"更新:{updated[:10]}")
    if entry_id:
        meta_parts.append(f"ID:{entry_id}")
    lines.append(" | ".join(meta_parts))
    lines.append(summary)

    return "\n".join(lines)


def estimate_tokens(text: str) -> int:
    return max(1, len(text) // _CHARS_PER_TOKEN)
