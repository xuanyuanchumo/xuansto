#!/usr/bin/env python3

import unittest
import sys
from pathlib import Path
from collections import OrderedDict

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from context_formatter import (
    format_knowledge_context,
    estimate_tokens,
    _format_entry,
    _format_entry_summary,
    _entry_priority,
    _extract_tech_stack_tag,
)

_CHARS_PER_TOKEN = 4

_OLD_FORMAT_ENTRY_TEMPLATE = (
    "### [{type_label}] {title} (置信度: {confidence:.2f})\n"
    "> 来源: {scope_label} | 更新: {updated} | 引用: {entry_id} | 标签: {tags}\n"
    "\n"
    "{content}\n"
    "\n"
)

_OLD_HEADER = "## 📚 知识库参考 (Knowledge Base References)\n\n"
_OLD_FOOTER = "\n---\n⚠️ 以上知识仅供参考，请结合项目实际情况判断适用性。"


def _old_format_entry(entry: dict) -> str:
    _SCOPE_LABELS_OLD = {
        "general": "通用知识库",
        "workspace": "工作区知识库",
        "experience": "经验知识库",
    }
    _TYPE_LABELS_OLD = {
        "standard": "标准",
        "pattern": "模式",
        "error-solution": "错误方案",
        "glossary": "术语",
        "best-practice": "最佳实践",
        "unknown": "知识",
    }
    title = entry.get("title", "无标题")
    confidence = entry.get("confidence", 0.0)
    entry_type = entry.get("type", "unknown")
    scope = entry.get("scope", "workspace")
    entry_id = entry.get("id", "")
    updated = entry.get("updated", "")
    content = entry.get("content", "")
    tags = entry.get("tags", [])

    type_label = _TYPE_LABELS_OLD.get(entry_type, entry_type)
    scope_label = _SCOPE_LABELS_OLD.get(scope, scope)

    lines = []
    lines.append(f"### [{type_label}] {title} (置信度: {confidence:.2f})")
    meta_parts = [f"来源: {scope_label}"]
    if updated:
        meta_parts.append(f"更新: {updated[:10]}")
    if entry_id:
        meta_parts.append(f"引用: {entry_id}")
    if tags:
        meta_parts.append(f"标签: {', '.join(tags[:5])}")
    lines.append(f"> {' | '.join(meta_parts)}")
    lines.append("")
    lines.append(content)
    lines.append("")

    return "\n".join(lines)


def _old_format_full(results: list) -> str:
    if not results:
        return ""
    sections = []
    for entry in results:
        sections.append(_old_format_entry(entry))
    body = "\n".join(sections)
    return _OLD_HEADER + body + _OLD_FOOTER


def _make_sample_results() -> list:
    return [
        {
            "id": "kb-pattern-react-001",
            "title": "React 组件设计模式",
            "type": "pattern",
            "scope": "workspace",
            "confidence": 0.85,
            "updated": "2026-04-10T12:00:00Z",
            "tags": ["react", "frontend", "design"],
            "content": "使用自定义 Hook 抽离业务逻辑，保持组件纯净。避免在 useEffect 中直接操作 DOM。",
            "summary": "React 组件设计模式摘要",
        },
        {
            "id": "ekb-bugfix-oom-handler-001",
            "title": "Node.js OOM 处理方案",
            "type": "bug_fix",
            "scope": "experience",
            "confidence": 0.75,
            "updated": "2026-04-15T08:30:00Z",
            "tags": ["node", "memory", "debug"],
            "content": "使用 stream.Readable 替代 fs.readFileSync，设置 --max-old-space-size=4096。",
            "summary": "Node.js OOM 处理摘要",
        },
        {
            "id": "kb-standard-ts-001",
            "title": "TypeScript 编码规范",
            "type": "standard",
            "scope": "workspace",
            "confidence": 0.90,
            "updated": "2026-03-20T10:00:00Z",
            "tags": ["typescript", "coding-standards", "lint"],
            "content": "严格启用 strict 模式，禁止使用 any，接口优先于类型别名。",
            "summary": "TypeScript 编码规范摘要",
        },
        {
            "id": "kb-glossary-api-001",
            "title": "REST API 术语表",
            "type": "glossary",
            "scope": "general",
            "confidence": 0.60,
            "updated": "2026-01-05T00:00:00Z",
            "tags": ["api", "rest", "http"],
            "content": "REST: 表述性状态转移。Idempotent: 多次调用结果一致。",
            "summary": "REST API 术语摘要",
        },
        {
            "id": "ekb-error-solution-cors-001",
            "title": "CORS 跨域错误解决方案",
            "type": "error-solution",
            "scope": "experience",
            "confidence": 0.80,
            "updated": "2026-04-18T09:00:00Z",
            "tags": ["cors", "http", "frontend"],
            "content": "在服务端设置 Access-Control-Allow-Origin，使用代理转发避免浏览器限制。",
            "summary": "CORS 错误解决摘要",
        },
    ]


class TestTokenReduction(unittest.TestCase):
    def test_token_reduction_at_least_25_percent(self):
        results = _make_sample_results()
        old_output = _old_format_full(results)
        new_output = format_knowledge_context(results, token_budget=8192)
        old_tokens = estimate_tokens(old_output)
        new_tokens = estimate_tokens(new_output)
        reduction = (old_tokens - new_tokens) / old_tokens
        self.assertGreaterEqual(
            reduction, 0.25,
            f"Token reduction {reduction:.1%} is less than 25%. "
            f"Old: {old_tokens}, New: {new_tokens}"
        )

    def test_compact_format_no_emoji_or_blockquote(self):
        results = _make_sample_results()
        output = format_knowledge_context(results, token_budget=8192)
        self.assertNotIn("📚", output)
        self.assertNotIn("⚠️", output)
        self.assertNotIn("📝", output)
        self.assertNotIn("> ", output)
        self.assertNotIn("---", output)
        self.assertNotIn("置信度:", output)
        self.assertNotIn("引用:", output)

    def test_compact_format_uses_short_labels(self):
        results = _make_sample_results()
        output = format_knowledge_context(results, token_budget=8192)
        self.assertIn("来源:", output)
        self.assertIn("ID:", output)
        self.assertIn("更新:", output)


class TestTechStackGrouping(unittest.TestCase):
    def test_grouped_entries_share_header(self):
        results = [
            {
                "id": "kb-react-001",
                "title": "React Hooks 最佳实践",
                "type": "best-practice",
                "scope": "workspace",
                "confidence": 0.88,
                "tags": ["react", "hooks"],
                "content": "使用 useCallback 和 useMemo 优化性能。",
            },
            {
                "id": "kb-react-002",
                "title": "React 状态管理方案",
                "type": "pattern",
                "scope": "workspace",
                "confidence": 0.82,
                "tags": ["react", "state"],
                "content": "小型项目用 Context，大型项目用 Zustand。",
            },
            {
                "id": "kb-general-001",
                "title": "Git 提交规范",
                "type": "standard",
                "scope": "workspace",
                "confidence": 0.70,
                "tags": ["git", "convention"],
                "content": "使用 Conventional Commits 格式。",
            },
        ]
        output = format_knowledge_context(results, token_budget=8192)
        self.assertIn("react 相关知识", output)
        react_group_start = output.index("react 相关知识")
        self.assertIn("React Hooks 最佳实践", output)
        self.assertIn("React 状态管理方案", output)
        self.assertIn("Git 提交规范", output)

    def test_extract_tech_stack_tag(self):
        self.assertEqual(_extract_tech_stack_tag({"tags": ["Python", "backend"]}), "Python")
        self.assertEqual(_extract_tech_stack_tag({"tags": ["docker", "devops"]}), "docker")
        self.assertEqual(_extract_tech_stack_tag({"tags": ["security", "auth"]}), "")
        self.assertEqual(_extract_tech_stack_tag({"tags": []}), "")


class TestPrioritySorting(unittest.TestCase):
    def test_bug_fix_before_standard(self):
        bug_entry = {
            "id": "bug-001", "title": "Bug Fix", "type": "bug_fix",
            "scope": "experience", "confidence": 0.5, "tags": [],
            "content": "fix",
        }
        std_entry = {
            "id": "std-001", "title": "Standard", "type": "standard",
            "scope": "workspace", "confidence": 0.9, "tags": [],
            "content": "std",
        }
        self.assertLess(_entry_priority(bug_entry), _entry_priority(std_entry))

    def test_error_solution_highest_priority(self):
        error_entry = {
            "id": "err-001", "title": "Error", "type": "error-solution",
            "scope": "experience", "confidence": 0.5, "tags": [],
            "content": "err",
        }
        pattern_entry = {
            "id": "pat-001", "title": "Pattern", "type": "pattern",
            "scope": "workspace", "confidence": 0.9, "tags": [],
            "content": "pat",
        }
        self.assertLess(_entry_priority(error_entry), _entry_priority(pattern_entry))

    def test_standard_before_pattern(self):
        std_entry = {
            "id": "std-001", "title": "Standard", "type": "standard",
            "scope": "workspace", "confidence": 0.5, "tags": [],
            "content": "std",
        }
        pat_entry = {
            "id": "pat-001", "title": "Pattern", "type": "pattern",
            "scope": "workspace", "confidence": 0.9, "tags": [],
            "content": "pat",
        }
        self.assertLess(_entry_priority(std_entry), _entry_priority(pat_entry))

    def test_pattern_before_glossary(self):
        pat_entry = {
            "id": "pat-001", "title": "Pattern", "type": "pattern",
            "scope": "workspace", "confidence": 0.5, "tags": [],
            "content": "pat",
        }
        glossary_entry = {
            "id": "glo-001", "title": "Glossary", "type": "glossary",
            "scope": "general", "confidence": 0.9, "tags": [],
            "content": "glo",
        }
        self.assertLess(_entry_priority(pat_entry), _entry_priority(glossary_entry))

    def test_category_coding_standards_priority(self):
        entry = {
            "id": "cs-001", "title": "Coding Standards",
            "type": "unknown", "category": "coding-standards",
            "scope": "workspace", "confidence": 0.5, "tags": [],
            "content": "cs",
        }
        self.assertEqual(_entry_priority(entry), 1)

    def test_output_ordering_matches_priority(self):
        results = [
            {
                "id": "kb-pattern-001", "title": "设计模式",
                "type": "pattern", "scope": "workspace",
                "confidence": 0.85, "tags": [], "content": "pattern content",
            },
            {
                "id": "ekb-bugfix-001", "title": "OOM 修复",
                "type": "bug_fix", "scope": "experience",
                "confidence": 0.70, "tags": [], "content": "bugfix content",
            },
            {
                "id": "kb-glossary-001", "title": "术语表",
                "type": "glossary", "scope": "general",
                "confidence": 0.60, "tags": [], "content": "glossary content",
            },
            {
                "id": "kb-standard-001", "title": "编码规范",
                "type": "standard", "scope": "workspace",
                "confidence": 0.90, "tags": [], "content": "standard content",
            },
        ]
        output = format_knowledge_context(results, token_budget=8192)
        bug_pos = output.index("OOM 修复")
        std_pos = output.index("编码规范")
        pat_pos = output.index("设计模式")
        glo_pos = output.index("术语表")
        self.assertLess(bug_pos, std_pos, "bug_fix should come before standard")
        self.assertLess(std_pos, pat_pos, "standard should come before pattern")
        self.assertLess(pat_pos, glo_pos, "pattern should come before glossary")


class TestFormatEntryCompact(unittest.TestCase):
    def test_format_entry_no_extra_blank_lines(self):
        entry = {
            "id": "test-001", "title": "Test", "type": "unknown",
            "scope": "workspace", "confidence": 0.75, "content": "content here",
        }
        result = _format_entry(entry)
        self.assertNotIn("\n\n", result)

    def test_format_entry_three_lines(self):
        entry = {
            "id": "test-001", "title": "Test", "type": "unknown",
            "scope": "workspace", "confidence": 0.75,
            "updated": "2026-04-10", "content": "content here",
        }
        result = _format_entry(entry)
        lines = result.split("\n")
        self.assertLessEqual(len(lines), 3)

    def test_format_entry_summary_marked(self):
        entry = {
            "id": "test-001", "title": "Test", "type": "unknown",
            "scope": "workspace", "confidence": 0.75,
            "content": "x" * 600, "summary": "short summary",
        }
        result = _format_entry_summary(entry)
        self.assertIn("[摘要]", result)


class TestEmptyInput(unittest.TestCase):
    def test_empty_results(self):
        self.assertEqual(format_knowledge_context([]), "")

    def test_none_tech_stack(self):
        results = [{"id": "t1", "title": "T", "type": "unknown",
                     "scope": "workspace", "confidence": 0.5,
                     "tags": [], "content": "c"}]
        output = format_knowledge_context(results, tech_stack=None)
        self.assertIn("T", output)


if __name__ == "__main__":
    unittest.main()
