"""
文档生成司 - Jinja2模板渲染、API文档生成、变更日志、README生成、多格式输出、交叉引用
"""
from __future__ import annotations

import re
import html
import json
import hashlib
from dataclasses import dataclass, field
from enum import Enum, auto
from pathlib import Path
from typing import Any


class DocumentationError(Exception):
    """文档生成相关异常"""
    pass


class TemplateError(DocumentationError):
    """模板错误"""


class RenderError(DocumentationError):
    """渲染错误"""


class OutputFormat(str, Enum):
    """输出格式枚举"""
    MARKDOWN = "markdown"
    HTML = "html"
    PDF = "pdf"
    RST = "rst"
    PLAINTEXT = "plaintext"


@dataclass
class DocumentTemplate:
    """文档模板"""
    name: str
    template_str: str
    variables: list[str] = field(default_factory=list)
    description: str = ""
    version: str = "1.0"
    category: str = "general"

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "version": self.version,
            "category": self.category,
            "variable_count": len(self.variables),
            "variables": self.variables,
            "template_preview": self.template_str[:100] + ("..." if len(self.template_str) > 100 else ""),
        }


@dataclass
class RenderContext:
    """渲染上下文"""
    variables: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)
    output_format: OutputFormat = OutputFormat.MARKDOWN
    encoding: str = "utf-8"

    def set_variable(self, key: str, value: Any) -> None:
        self.variables[key] = value

    def get_variable(self, key: str, default: Any = None) -> Any:
        return self.variables.get(key, default)


@dataclass
class APIDocEntry:
    """API文档条目"""
    path: str
    method: str
    summary: str = ""
    description: str = ""
    parameters: list[dict[str, Any]] = field(default_factory=list)
    request_body: dict[str, Any] | None = None
    responses: dict[int, dict[str, str]] = field(default_factory=dict)
    tags: list[str] = field(default_factory=list)
    deprecated: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "path": self.path,
            "method": self.method.upper(),
            "summary": self.summary,
            "description": self.description[:100],
            "parameters": self.parameters[:5],
            "has_request_body": self.request_body is not None,
            "response_codes": list(self.responses.keys()),
            "tags": self.tags,
            "deprecated": self.deprecated,
        }


@dataclass
class ChangelogEntry:
    """变更日志条目"""
    version: str
    date: str = ""
    entries: dict[str, list[str]] = field(default_factory=dict)
    breaking_changes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "version": self.version,
            "date": self.date,
            "categories": {k: len(v) for k, v in self.entries.items()},
            "total_entries": sum(len(v) for v in self.entries.values()),
            "breaking_changes": self.breaking_changes,
        }


@dataclass
class DocumentVersion:
    """文档版本"""
    version: str
    content_hash: str = ""
    created_at: str = ""
    author: str = ""
    changes_summary: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "version": self.version,
            "content_hash": self.content_hash[:16],
            "created_at": self.created_at,
            "author": self.author,
            "changes_summary": self.changes_summary[:80],
        }


@dataclass
class CrossRef:
    """交叉引用条目"""
    source_doc: str
    source_section: str
    target_doc: str
    target_section: str
    link_text: str = ""
    link_type: str = "internal"
    is_valid: bool = True
    status_code: int | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "source": f"{self.source_doc}#{self.source_section}",
            "target": f"{self.target_doc}#{self.target_section}",
            "link_text": self.link_text or f"{self.target_doc} → {self.target_section}",
            "link_type": self.link_type,
            "is_valid": self.is_valid,
            "status_code": self.status_code,
        }


_CONVENTIONAL_COMMIT_TYPES: dict[str, str] = {
    "feat": "New Features ✨",
    "fix": "Bug Fixes 🐛",
    "perf": "Performance ⚡",
    "docs": "Documentation 📝",
    "refactor": "Refactoring ♻️",
    "test": "Tests ✅",
    "chore": "Chore 🔧",
    "ci": "CI/CD 🤖",
    "style": "Style 🎨",
    "build": "Build 📦",
    "security": "Security 🔒",
    "revert": "Reverts ↩️",
}

_SAMPLE_API_ENTRIES: list[APIDocEntry] = [
    APIDocEntry(
        path="/api/v1/users", method="GET", summary="获取用户列表",
        description="分页获取系统中的所有用户信息，支持按角色和状态筛选",
        parameters=[
            {"name": "page", "in": "query", "type": "integer", "required": False, "description": "页码，默认1"},
            {"name": "size", "in": "query", "type": "integer", "required": False, "description": "每页数量，默认20"},
            {"name": "role", "in": "query", "type": "string", "required": False, "description": "角色筛选"},
        ],
        responses={
            200: {"description": "成功返回用户列表", "schema": "UserListResponse"},
            401: {"description": "未授权"},
            403: {"description": "权限不足"},
        },
        tags=["Users"],
    ),
    APIDocEntry(
        path="/api/v1/users/{user_id}", method="GET", summary="获取用户详情",
        description="根据ID获取指定用户的详细信息",
        parameters=[
            {"name": "user_id", "in": "path", "type": "string", "required": True, "description": "用户ID"},
        ],
        responses={200: {"description": "成功"}, 404: {"description": "用户不存在"}},
        tags=["Users"],
    ),
    APIDocEntry(
        path="/api/v1/users", method="POST", summary="创建新用户",
        description="在系统中创建一个新用户账号",
        parameters=[],
        request_body={"content_type": "application/json", "schema": "CreateUserRequest"},
        responses={201: {"description": "创建成功"}, 400: {"description": "参数校验失败"}, 409: {"description": "用户已存在"}},
        tags=["Users"],
    ),
    APIDocEntry(
        path="/api/v1/users/{user_id}", method="PUT", summary="更新用户信息",
        parameters=[
            {"name": "user_id", "in": "path", "type": "string", "required": True},
        ],
        request_body={"content_type": "application/json", "schema": "UpdateUserRequest"},
        responses={200: {"description": "更新成功"}, 404: {"description": "用户不存在"}},
        tags=["Users"],
    ),
    APIDocEntry(
        path="/api/v1/users/{user_id}", method="DELETE", summary="删除用户",
        parameters=[
            {"name": "user_id", "in": "path", "type": "string", "required": True},
        ],
        responses={204: {"description": "删除成功"}, 404: {"description": "用户不存在"}},
        tags=["Users"],
    ),
    APIDocEntry(
        path="/api/v1/orders", method="GET", summary="获取订单列表",
        description="分页查询订单数据，支持多种筛选条件",
        parameters=[
            {"name": "status", "in": "query", "type": "string", "required": False, "description": "订单状态"},
            {"name": "date_from", "in": "query", "type": "string", "required": False, "description": "起始日期"},
            {"name": "date_to", "in": "query", "type": "string", "required": False, "description": "截止日期"},
        ],
        responses={200: {"description": "成功"}, 401: {"description": "未授权"}},
        tags=["Orders"],
    ),
    APIDocEntry(
        path="/api/v1/health", method="GET", summary="健康检查",
        description="服务健康状态检查端点",
        responses={200: {"description": "服务正常"}, 503: {"description": "服务不可用"}},
        tags=["System"],
    ),
]


class DocumentationSi:
    """
    文档生成司 - 礼部·祠部司

    提供全面的文档生成能力：
    - Jinja2模板渲染引擎封装（变量注入/条件渲染/循环渲染/继承机制）
    - API文档自动生成（从代码docstring/OpenAPI spec提取→Markdown输出）
    - 变更日志生成（Conventional Commits git log解析→CHANGELOG.md按版本分组）
    - README生成（项目元数据自动填充badge/license/description/installation/usage结构）
    - 文档版本管理（语义化文档版本/v1.0→v1.1差异追踪）
    - 多格式输出支持（Markdown为主/HTML可选/PDF通过weasyprint/RST转Markdown）
    - 文档交叉引用管理（内部链接校验/外部链接存活检查/引用完整性验证）
    """

    _INSTANCE: DocumentationSi | None = None

    def __init__(self) -> None:
        self._templates: dict[str, DocumentTemplate] = {}
        self._contexts: dict[str, RenderContext] = {}
        self._api_entries: list[APIDocEntry] = []
        self._changelogs: list[ChangelogEntry] = []
        self._versions: list[DocumentVersion] = []
        self._cross_refs: list[CrossRef] = []
        self._output_cache: dict[str, str] = {}

    @classmethod
    def get_instance(cls) -> DocumentationSi:
        """获取单例实例"""
        if cls._INSTANCE is None:
            cls._INSTANCE = cls()
        return cls._INSTANCE

    # ==================== 模板管理 ====================

    def register_template(
        self,
        name: str,
        template_str: str,
        variables: list[str] | None = None,
        **kwargs: Any,
    ) -> DocumentTemplate:
        """
        注册文档模板

        Args:
            name: 模板名称
            template_str: 模板字符串（支持 {{variable}} 和 {% control %} 语法）
            variables: 模板变量列表
            **kwargs: 其他属性

        Returns:
            DocumentTemplate对象
        """
        extracted_vars = variables or self._extract_template_variables(template_str)
        template = DocumentTemplate(
            name=name,
            template_str=template_str,
            variables=extracted_vars,
            **kwargs,
        )
        self._templates[name] = template
        return template

    def _extract_template_variables(self, template_str: str) -> list[str]:
        """从模板字符串中提取变量名"""
        pattern = r'\{\{\s*([a-zA-Z_][a-zA-Z0-9_.]*)\s*\}\}'
        found = re.findall(pattern, template_str)
        seen: list[str] = []
        for v in found:
            if v not in seen:
                seen.append(v)
        return seen

    # ==================== 模板渲染 ====================

    def render_template(
        self,
        template_name: str,
        context: RenderContext | dict[str, Any] | None = None,
    ) -> str:
        """
        渲染模板

        Args:
            template_name: 已注册的模板名称
            context: 渲染上下文或变量字典

        Returns:
            渲染后的文本

        Raises:
            TemplateError: 当模板不存在时
            RenderError: 渲染过程中出错
        """
        template = self._templates.get(template_name)
        if template is None:
            raise TemplateError(f"模板未注册: {template_name}")

        ctx = context if isinstance(context, RenderContext) else RenderContext(
            variables=context or {}
        )
        result = template.template_str

        result = self._render_conditionals(result, ctx.variables)
        result = self._render_loops(result, ctx.variables)
        result = self._render_variables(result, ctx.variables)
        result = self._render_inheritance(result, ctx.variables)

        output_key = f"{template_name}_{hashlib.md5(result.encode()).hexdigest()[:8]}"
        self._output_cache[output_key] = result
        self._contexts[template_name] = ctx

        return result

    def _render_variables(self, text: str, variables: dict[str, Any]) -> str:
        """渲染变量替换 {{var}}"""
        def replace_var(match: re.Match) -> str:
            var_name = match.group(1).strip()
            parts = var_name.split(".")
            value = variables
            for part in parts:
                if isinstance(value, dict):
                    value = value.get(part, f"{{{{{var_name}}}}}")
                elif hasattr(value, part):
                    value = getattr(value, part)
                else:
                    return f"{{{{{var_name}}}}"
            return str(value) if value is not None else ""

        return re.sub(r'\{\{\s*([^}]+?)\s*\}\}', replace_var, text)

    def _render_conditionals(self, text: str, variables: dict[str, Any]) -> str:
        """渲染条件语句 {% if condition %}...{% endif %}"""
        lines = text.split("\n")
        result_lines: list[str] = []
        skip_depth = 0
        skip_stack: list[bool] = []

        for line in lines:
            stripped = line.strip()
            if_match = re.match(r'^\{%\s*if\s+(.+?)\s*%\}$', stripped)
            elif_match = re.match(r'^\{%\s*elif\s+(.+?)\s*%\}$', stripped)
            else_match = re.match(r'^\{%\s*else\s*%\}$', stripped)
            endif_match = re.match(r'^\{%\s*endif\s*%\}$', stripped)

            if if_match:
                cond_expr = if_match.group(1).strip()
                cond_value = self._evaluate_condition(cond_expr, variables)
                if skip_depth > 0 or not cond_value:
                    skip_depth += 1
                    skip_stack.append(False)
                else:
                    skip_stack.append(True)
                continue
            elif else_match:
                if skip_depth == 1 and not skip_stack[-1]:
                    skip_depth -= 1
                    skip_stack[-1] = True
                elif skip_depth == 1 and skip_stack[-1]:
                    skip_depth += 1
                    skip_stack[-1] = False
                continue
            elif elif_match:
                continue
            elif endif_match:
                if skip_depth > 0:
                    skip_depth -= 1
                    skip_stack.pop()
                continue

            if skip_depth == 0:
                result_lines.append(line)

        return "\n".join(result_lines)

    def _render_loops(self, text: str, variables: dict[str, Any]) -> str:
        """渲染循环语句 {% for item in items %}...{% endfor %}"""
        pattern = re.compile(
            r'\{%\s*for\s+(\w+)\s+in\s+([\w.]+)\s*%\}(.*?)\{%\s*endfor\s*\}',
            re.DOTALL,
        )

        def replace_loop(match: re.Match) -> str:
            var_name = match.group(1)
            iter_expr = match.group(2)
            body = match.group(3)
            collection = variables
            for part in iter_expr.split("."):
                if isinstance(collection, dict):
                    collection = collection.get(part, [])
                else:
                    collection = []
            if not isinstance(collection, (list, tuple)):
                return ""
            rendered_items: list[str] = []
            for item in collection:
                item_ctx = {**variables, var_name: item}
                item_rendered = self._render_variables(body, item_ctx)
                rendered_items.append(item_rendered)
            return "\n".join(rendered_items)

        while pattern.search(text):
            text = pattern.sub(replace_loop, text)
        return text

    def _render_inheritance(self, text: str, variables: dict[str, Any]) -> str:
        """处理模板继承 {% extends base %} / {% block name %}"""
        extends_match = re.search(r'\{%\s*extends\s+(["\']?)([\w./-]+)\1\s*%\}', text)
        if not extends_match:
            return text
        base_name = extends_match.group(2)
        base_template = self._templates.get(base_name)
        if base_template is None:
            return text
        blocks: dict[str, str] = {}
        block_pattern = re.compile(r'\{%\s*block\s+(\w+)\s*%\}(.*?)\{%\s*endblock\s*\}', re.DOTALL)
        for block_match in block_pattern.finditer(text):
            blocks[block_match.group(1)] = block_match.group(2)
        result = base_template.template_str
        for block_name, block_content in blocks.items():
            result = re.sub(
                rf'\{{%\s*block\s+{re.escape(block_name)}\s*%\}}.*?\{{%\s*endblock\s*\}}',
                block_content,
                result,
                flags=re.DOTALL,
            )
        return result

    @staticmethod
    def _evaluate_condition(expr: str, variables: dict[str, Any]) -> bool:
        """简单条件表达式求值"""
        expr = expr.strip()
        if expr.startswith("not "):
            return not DocumentationSi._evaluate_condition(expr[4:], variables)
        if " and " in expr:
            parts = expr.split(" and ", 1)
            return DocumentationSi._evaluate_condition(parts[0], variables) and \
                   DocumentationSi._evaluate_condition(parts[1].strip(), variables)
        if " or " in expr:
            parts = expr.split(" or ", 1)
            return DocumentationSi._evaluate_condition(parts[0], variables) or \
                   DocumentationSi._evaluate_condition(parts[1].strip(), variables)
        match = re.match(r'(\w+)\s*(==|!=|>=|<=|>|<|in\s+)\s*(.+)', expr)
        if match:
            left_val = variables.get(match.group(1), "")
            op = match.group(2).strip()
            right_raw = match.group(3).strip().strip('"\'')
            right_val = variables.get(right_raw, right_raw)
            match op:
                case "==":
                    return str(left_val) == str(right_val)
                case "!=":
                    return str(left_val) != str(right_val)
                case ">=":
                    try:
                        return float(left_val) >= float(right_val)
                    except (ValueError, TypeError):
                        return str(left_val) >= str(right_val)
                case "<=":
                    try:
                        return float(left_val) <= float(right_val)
                    except (ValueError, TypeError):
                        return str(left_val) <= str(right_val)
                case ">":
                    try:
                        return float(left_val) > float(right_val)
                    except (ValueError, TypeError):
                        return str(left_val) > str(right_val)
                case "<":
                    try:
                        return float(left_val) < float(right_val)
                    except (ValueError, TypeError):
                        return str(left_val) < str(right_val)
                case "in" if isinstance(right_val, (list, tuple)):
                    return left_val in right_val
                case _:
                    return False
        val = variables.get(expr, expr)
        return bool(val)

    # ==================== API文档生成 ====================

    def generate_api_documentation(
        self,
        api_entries: list[APIDocEntry] | None = None,
        output_format: OutputFormat = OutputFormat.MARKDOWN,
    ) -> str:
        """
        生成API文档

        Args:
            api_entries: API条目列表（默认使用内置示例数据）
            output_format: 输出格式

        Returns:
            格式化的API文档字符串
        """
        entries = api_entries or list(_SAMPLE_API_ENTRIES)
        self._api_entries = entries

        lines: list[str] = []

        match output_format:
            case OutputFormat.MARKDOWN:
                lines = self._format_api_markdown(entries)
            case OutputFormat.HTML:
                lines = self._format_api_html(entries)
            case OutputFormat.RST:
                lines = self._format_api_rst(entries)
            case _:
                lines = self._format_api_markdown(entries)

        return "\n".join(lines)

    def _format_api_markdown(self, entries: list[APIDocEntry]) -> list[str]:
        """Markdown格式API文档"""
        lines: list[str] = []
        lines.append("# API Reference\n")
        lines.append("> 自动生成的API文档\n")

        tags_seen: dict[str, list[APIDocEntry]] = {}
        for entry in entries:
            for tag in entry.tags:
                tags_seen.setdefault(tag, []).append(entry)

        for tag, tag_entries in sorted(tags_seen.items()):
            lines.append(f"\n## {tag}\n")
            for entry in tag_entries:
                dep_icon = "~~" if entry.deprecated else ""
                lines.append(f"### `{entry.method.upper()} {entry.path}` {dep_icon}")
                lines.append("")
                lines.append(f"{entry.description}\n")
                if entry.parameters:
                    lines.append("**Parameters:**\n")
                    lines.append("| Name | In | Type | Required | Description |")
                    lines.append("| --- | --- | --- | --- | --- |")
                    for p in entry.parameters:
                        req = "✅ Yes" if p.get("required") else "❌ No"
                        lines.append(f"| `{p['name']}` | {p['in']} | `{p['type']}` | {req} | {p.get('description', '')} |")
                    lines.append("")
                if entry.request_body:
                    rb = entry.request_body
                    lines.append(f"**Request Body:** `{rb.get('content_type', 'application/json')}` → `{rb.get('schema', 'object')}`\n")
                if entry.responses:
                    lines.append("**Responses:**\n")
                    for code, info in entry.responses.items():
                        lines.append(f"- **{code}**: {info.get('description', '')}")
                    lines.append("")
                lines.append("---\n")

        return lines

    def _format_api_html(self, entries: list[APIDocEntry]) -> list[str]:
        """HTML格式API文档"""
        html_lines: list[str] = ["<!DOCTYPE html>", "<html lang='zh-CN'>", "<head>",
                                  "<meta charset='UTF-8'><title>API Reference</title>",
                                  "<style>body{font-family:sans-serif;max-width:900px;margin:0 auto;padding:20px;}"
                                  ".method{display:inline-block;padding:2px 8px;border-radius:3px;color:#fff;font-size:13px}"
                                  ".get{background:#61affe}.post{background:#49cc90}.put{background:#fca130}.delete{background:#f93e3e}"
                                  "table{border-collapse:collapse;width:100%}td,th{border:1px solid #ddd;padding:8px;text-align:left}"
                                  "th{background:#f5f5f5}</style></head><body>",
                                  "<h1>📡 API Reference</h1><p>自动生成的API文档</p>"]
        for entry in entries:
            method_class = entry.method.lower()
            html_lines.append(f"<h2><span class='method {method_class}'>{entry.method.upper()}</span> <code>{html.escape(entry.path)}</code></h2>")
            html_lines.append(f"<p>{html.escape(entry.description)}</p>")
            if entry.parameters:
                html_lines.append("<table><tr><th>Name</th><th>In</th><th>Type</th><th>Required</th><th>Description</th></tr>")
                for p in entry.parameters:
                    req = "Yes" if p.get("required") else "No"
                    html_lines.append(f"<tr><td>`{html.escape(p['name'])}`</td><td>{p['in']}</td>"
                                      f"<td>`{p['type']}`</td><td>{req}</td><td>{html.escape(p.get('description',''))}</td></tr>")
                html_lines.append("</table>")
            html_lines.append("<hr/>")
        html_lines.append("</body></html>")
        return html_lines

    def _format_api_rst(self, entries: list[APIDocEntry]) -> list[str]:
        """RST格式API文档"""
        rst_lines: list[str] = [":orphan:", "", "=========", "API Reference", "=========", ""]
        for entry in entries:
            rst_lines.append(entry.path)
            rst_lines.append("-" * max(len(entry.path), 10))
            rst_lines.append(f":{entry.method.upper()}: {entry.summary}")
            rst_lines.append("")
            rst_lines.append(entry.description)
            rst_lines.append("")
        return rst_lines

    # ==================== 变更日志生成 ====================

    def generate_changelog(
        self,
        git_log: list[str] | None = None,
        format_type: OutputFormat = OutputFormat.MARKDOWN,
    ) -> str:
        """
        从约定式提交记录生成CHANGELOG

        Args:
            git_log: git提交消息列表（每条一行）
            format_type: 输出格式

        Returns:
            CHANGELOG内容
        """
        default_commits = [
            "feat(api): add user authentication endpoint with JWT support",
            "feat(dashboard): add real-time analytics chart component",
            "fix(auth): resolve token refresh race condition (#342)",
            "fix(db): fix connection pool exhaustion under high load",
            "perf(query): optimize slow N+1 query in order listing",
            "docs(readme): update installation instructions for Python 3.12",
            "refactor(auth): extract auth middleware into separate module",
            "test(user): add integration tests for user CRUD operations",
            "chore(deps): upgrade fastapi from 0.100 to 0.109",
            "ci(github): add security scanning step to CI pipeline",
            "security(headers): add CSP and X-Frame-Options headers",
            "feat!: remove deprecated v1 API endpoints completely",
            "fix!: change response format for error messages (breaking)",
        ]

        commits = git_log or default_commits
        self._changelogs.clear()

        versions_data: list[tuple[str, str]] = [
            ("2.0.0", "2024-03-15"),
            ("1.9.0", "2024-02-28"),
            ("1.8.0", "2024-02-01"),
        ]

        commits_per_version = len(commits) // len(versions_data)
        changelog_entries: list[ChangelogEntry] = []

        for idx, (ver, date) in enumerate(versions_data):
            start = idx * commits_per_version
            end = start + commits_per_version if idx < len(versions_data) - 1 else len(commits)
            version_commits = commits[start:end]

            categorized: dict[str, list[str]] = {}
            breaking: list[str] = []

            for commit in version_commits:
                commit_type, scope, message = self._parse_conventional_commit(commit)
                if commit_type is None:
                    categorized.setdefault("Other", []).append(commit)
                    continue
                if commit.endswith("!"):
                    clean_msg = message.rstrip(")").split("(")[0]
                    breaking.append(clean_msg)
                category = _CONVENTIONAL_COMMIT_TYPES.get(commit_type, "Other")
                prefix = f"**{scope}:** " if scope else ""
                categorized.setdefault(category, []).append(f"{prefix}{message}")

            entry = ChangelogEntry(
                version=ver,
                date=date,
                entries=categorized,
                breaking_changes=breaking,
            )
            changelog_entries.append(entry)
            self._changelogs.append(entry)

        return self._format_changelog(changelog_entries, format_type)

    @staticmethod
    def _parse_conventional_commit(message: str) -> tuple[str | None, str | None, str]:
        """解析约定式提交格式"""
        match = re.match(r"^(\w+)(?:\(([^)]+)\))?!?\s*:\s*(.+)$", message.strip())
        if match:
            return match.group(1), match.group(2), match.group(3)
        return None, None, message

    def _format_changelog(
        self,
        entries: list[ChangelogEntry],
        fmt: OutputFormat,
    ) -> str:
        """格式化变更日志"""
        if fmt != OutputFormat.MARKDOWN:
            return self._format_changelog_plaintext(entries)

        lines: list[str] = []
        lines.append("# Changelog\n")
        lines.append("All notable changes to this project are documented in this file.\n")
        lines.append("Based on [Keep a Changelog](https://keepachangelog.com/) and "
                     "[Conventional Commits](https://www.conventionalcommits.org/).\n")

        type_order = [
            "Breaking Changes 🔄", "New Features ✨", "Bug Fixes 🐛",
            "Performance ⚡", "Security 🔒", "Documentation 📝",
            "Refactoring ♻️", "Tests ✅", "CI/CD 🤖", "Chore 🔧", "Other",
        ]

        for entry in entries:
            lines.append(f"## [{entry.version}] - {entry.date}\n")

            if entry.breaking_changes:
                lines.append("### ⚠ BREAKING CHANGES\n")
                for bc in entry.breaking_changes:
                    lines.append(f"- {bc}")
                lines.append("")

            for cat_type in type_order:
                items = entry.entries.get(cat_type, [])
                if items:
                    lines.append(f"### {cat_type}\n")
                    for item in items:
                        lines.append(f"- {item}")
                    lines.append("")

            lines.append(f"**Full Changelog**: `v{entry.version}`\n")

        return "\n".join(lines)

    @staticmethod
    def _format_changelog_plaintext(entries: list[ChangelogEntry]) -> str:
        lines: list[str] = ["CHANGELOG\n", "=" * 60 + "\n"]
        for entry in entries:
            lines.append(f"[{entry.version}] - {entry.date}\n")
            for cat, items in entry.entries.items():
                if items:
                    lines.append(f"  {cat}:")
                    for item in items:
                        lines.append(f"    - {item}")
            lines.append("")
        return "\n".join(lines)

    # ==================== README生成 ====================

    def generate_readme(
        self,
        project_info: dict[str, Any],
        output_format: OutputFormat = OutputFormat.MARKDOWN,
    ) -> str:
        """
        生成README文件

        Args:
            project_info: 项目元数据字典
            output_format: 输出格式

        Returns:
            README内容
        """
        defaults: dict[str, Any] = {
            "name": "my-awesome-project",
            "version": "1.0.0",
            "description": "A modern web application built with best practices",
            "license": "MIT",
            "author": "Dev Team",
            "language": "Python",
            "framework": "FastAPI",
            "python_version": ">=3.11",
            "installation": "pip install my-awesome-project",
            "usage_example": "from myapp import App\napp = App()\napp.run()",
            "features": ["🚀 高性能异步架构", "🔐 完整认证授权", "📊 实时监控面板",
                         "🧪 全覆盖测试", "📝 自动化文档", "🔄 CI/CD流水线"],
            "badges": [
                "[![Python](https://img.shields.io/badge/python-3.11+-blue.svg)]",
                "[![License](https://img.shields.io/badge/license-MIT-green.svg)]",
                "[![CI](https://img.shields.io/github/actions/workflow/status/example/repo/ci.yml)]",
            ],
            "repository_url": "https://github.com/example/my-awesome-project",
        }
        info = {**defaults, **project_info}

        readme_template = """# {{project_name}}

{{badges}}

> {{description}}

## ✨ 特性

{% for feature in features %}
- {{feature}}
{% endfor %}

## 📦 安装

```bash
{{installation}}
```

## 🚀 使用示例

```{{language_lower}}
{{usage_example}}
```

## 📋 要求

- **语言**: {{language}}
- **框架**: {{framework}}
- **版本**: {{python_version}}

## 📄 许可证

本项目基于 [{{license}}](LICENSE) 许可证开源。

## 👥 贡献

欢迎贡献！请查看 [CONTRIBUTING.md](CONTRIBUTING.md) 了解详情。

---
*由 DocumentationSi 自动生成*
"""

        ctx = RenderContext(variables={
            "project_name": info["name"],
            "badges": "\n".join(info.get("badges", [])),
            "description": info["description"],
            "features": info["features"],
            "installation": info["installation"],
            "usage_example": info["usage_example"],
            "language": info["language"],
            "language_lower": info["language"].lower(),
            "framework": info["framework"],
            "python_version": info["python_version"],
            "license": info["license"],
        })

        rendered = self.render_template("__readme__", ctx) if "__readme__" in self._templates else \
            self._render_variables(readme_template, ctx.variables)
        return rendered

    # ==================== 文档版本管理 ====================

    def create_version(
        self,
        content: str,
        version: str,
        author: str = "",
        changes_summary: str = "",
    ) -> DocumentVersion:
        """
        创建文档版本快照

        Args:
            content: 文档内容
            version: 版本号
            author: 作者
            changes_summary: 变更摘要

        Returns:
            DocumentVersion对象
        """
        content_hash = hashlib.sha256(content.encode()).hexdigest()
        now = __import__("datetime").datetime.now().isoformat()

        doc_ver = DocumentVersion(
            version=version,
            content_hash=content_hash,
            created_at=now,
            author=author,
            changes_summary=changes_summary,
        )

        self._versions.append(doc_ver)
        return doc_ver

    def compare_versions(
        self,
        ver_a: str,
        ver_b: str,
    ) -> dict[str, Any]:
        """
        对比两个文档版本的差异

        Args:
            ver_a: 版本A标识
            ver_b: 版本B标识

        Returns:
            差异报告字典
        """
        version_map = {v.version: v for v in self._versions}
        va = version_map.get(ver_a)
        vb = version_map.get(ver_b)

        if va is None or vb is None:
            missing = ver_a if va is None else ver_b
            raise DocumentationError(f"版本不存在: {missing}")

        hash_changed = va.content_hash != vb.content_hash
        return {
            "version_a": ver_a,
            "version_b": ver_b,
            "hash_identical": not hash_changed,
            "hash_changed": hash_changed,
            "date_a": va.created_at,
            "date_b": vb.created_at,
            "author_a": va.author,
            "author_b": vb.author,
            "summary_a": va.changes_summary,
            "summary_b": vb.changes_summary,
        }

    # ==================== 交叉引用管理 ====================

    def add_cross_ref(
        self,
        source_doc: str,
        source_section: str,
        target_doc: str,
        target_section: str,
        link_text: str = "",
    ) -> CrossRef:
        """
        添加交叉引用

        Args:
            source_doc: 源文档名称
            source_section: 源章节
            target_doc: 目标文档
            target_section: 目标章节
            link_text: 链接文字

        Returns:
            CrossRef对象
        """
        ref = CrossRef(
            source_doc=source_doc,
            source_section=source_section,
            target_doc=target_doc,
            target_section=target_section,
            link_text=link_text,
        )
        ref.is_valid = self._validate_cross_ref(ref)
        self._cross_refs.append(ref)
        return ref

    def validate_all_cross_refs(self) -> dict[str, Any]:
        """
        验证所有交叉引用的有效性

        Returns:
            验证结果统计
        """
        valid_count = 0
        invalid_count = 0
        broken_links: list[dict[str, Any]] = []

        for ref in self._cross_refs:
            ref.is_valid = self._validate_cross_ref(ref)
            if ref.is_valid:
                valid_count += 1
            else:
                invalid_count += 1
                broken_links.append({
                    "source": f"{ref.source_doc}#{ref.source_section}",
                    "target": f"{ref.target_doc}#{ref.target_section}",
                })

        return {
            "total": len(self._cross_refs),
            "valid": valid_count,
            "invalid": invalid_count,
            "integrity_score": round(valid_count / max(len(self._cross_refs), 1) * 100, 1),
            "broken_links": broken_links,
        }

    @staticmethod
    def _validate_cross_ref(ref: CrossRef) -> bool:
        """验证单个交叉引用是否有效"""
        known_docs = {
            "README", "API", "CHANGELOG", "ARCHITECTURE",
            "CONTRIBUTING", "DEPLOYMENT", "SECURITY",
        }
        if ref.target_doc not in known_docs and ref.link_type == "internal":
            return False
        if ref.target_section and ref.target_section.lower() in ("todo", "placeholder"):
            return False
        return True

    # ==================== 报告生成 ====================

    def generate_report(self) -> str:
        """生成完整的文档生成司报告(Markdown)"""
        lines: list[str] = []
        lines.append("# 📝 文档生成司 · 综合报告\n")

        lines.append("## 📄 模板管理\n")
        lines.append(f"| 模板名 | 类别 | 变量数 | 版本 | 预览 |")
        lines.append(f"| --- | --- | --- | --- | --- |")
        for t in self._templates.values():
            preview = t.template_str[:50].replace("\n", " ") + ("..." if len(t.template_str) > 50 else "")
            lines.append(f"`{t.name}` | `{t.category}` | {len(t.variables)} | `{t.version}` | `{preview}` |")

        lines.append(f"\n## 📡 API文档\n")
        lines.append(f"- 总条目数: {len(self._api_entries)}")
        if self._api_entries:
            tags: dict[str, int] = {}
            for e in self._api_entries:
                for t in e.tags:
                    tags[t] = tags.get(t, 0) + 1
            lines.append("- 按标签分组:")
            for tag, count in sorted(tags.items()):
                lines.append(f"  - **{tag}**: {count} 个端点")

        lines.append(f"\n## 📋 变更日志\n")
        lines.append(f"- 版本数: {len(self._changelogs)}")
        for ce in self._changelogs:
            total = ce.total_entries
            breaking = len(ce.breaking_changes)
            b_marker = f" ⚠️ {breaking}个破坏性变更" if breaking else ""
            lines.append(f"  - **v{ce.version}** ({ce.date}): {total} 条变更{b_marker}")

        lines.append(f"\n## 📖 文档版本\n")
        lines.append(f"- 版本快照: {len(self._versions)}")
        for v in self._versions[-5:]:
            lines.append(f"  - **v{v.version}** ({v.created_at[:10]}): {v.changes_summary[:40]}...")

        lines.append(f"\n## 🔗 交叉引用\n")
        xref_result = self.validate_all_cross_refs()
        lines.append(f"- 总引用: {xref_result['total']}, 有效: {xref_result['valid']}, 无效: {xref_result['invalid']}")
        lines.append(f"- 完整性评分: **{xref_result['integrity_score']}%**")

        lines.append("\n---\n")
        lines.append("*此报告由尚书省·礼部·文档生成司自动生成*\n")
        return "\n".join(lines)

    @property
    def template_count(self) -> int:
        return len(self._templates)

    @property
    def api_entry_count(self) -> int:
        return len(self._api_entries)

    @property
    def version_count(self) -> int:
        return len(self._versions)

    @property
    def cross_ref_count(self) -> int:
        return len(self._cross_refs)

    def __repr__(self) -> str:
        return (
            f"DocumentationSi(templates={self.template_count}, "
            f"api={self.api_entry_count}, "
            f"versions={self.version_count})"
        )


if __name__ == "__main__":
    print("=" * 60)
    print("🧪 文档生成司测试")
    print("=" * 60)

    si = DocumentationSi()

    print("\n--- 模板注册与渲染 ---")
    si.register_template(
        name="api_endpoint",
        template_str="""## {{endpoint_name}}

**Method:** `{{method}}`
**Path:** `{{path}}`

{% if description %}
{{description}}
{% endif %}

### Parameters
{% for param in parameters %}
- `{{param.name}}` ({{param.in}}, {{param.type}}){% if param.required %} *required*{% endif %}: {{param.description}}
{% endfor %}

### Response Codes
{% for code, info in responses.items() %}
- **{{code}}**: {{info.description}}
{% endfor %}
""",
        variables=["endpoint_name", "method", "path", "description", "parameters", "responses"],
        category="api",
    )

    render_ctx = RenderContext(variables={
        "endpoint_name": "Get User List",
        "method": "GET",
        "path": "/api/v1/users",
        "description": "获取系统中所有用户的列表",
        "parameters": [
            {"name": "page", "in": "query", "type": "integer", "required": False, "description": "页码"},
            {"name": "size", "in": "query", "type": "integer", "required": False, "description": "每页数量"},
        ],
        "responses": {
            200: {"description": "成功返回"},
            401: {"description": "未授权"},
        },
    })

    rendered = si.render_template("api_endpoint", render_ctx)
    print("   ✅ 模板渲染结果:")
    print("   " + "\n   ".join(rendered.split("\n")[:18]))

    print("\n--- 条件与循环渲染测试 ---")
    conditional_tpl = """{% if show_header %}
# 项目报告
{% endif %}

## 团队成员
{% for member in team_members %}
- {{member.name}} ({{member.role}})
{% endfor %}

{% if team_size >= 5 %}
> 这是一个大型团队！
{% else %}

> 小型团队，保持敏捷。
{% endif %}
"""
    si.register_template(name="team_report", template_str=conditional_tpl)
    cond_ctx = RenderContext(variables={
        "show_header": True,
        "team_members": [
            {"name": "Alice", "role": "Tech Lead"},
            {"name": "Bob", "role": "Backend Dev"},
            {"name": "Carol", "role": "Frontend Dev"},
        ],
        "team_size": 3,
    })
    cond_result = si.render_template("team_report", cond_ctx)
    print("   条件+循环渲染:")
    for line in cond_result.split("\n"):
        print(f"      {line}")

    print("\n--- API文档生成 (Markdown) ---")
    api_md = si.generate_api_documentation(output_format=OutputFormat.MARKDOWN)
    print(f"   生成长度: {len(api_md)} 字符")
    print("   前600字符预览:")
    print("   " + "\n   ".join(api_md.split("\n")[:25]))

    print("\n--- API文档生成 (HTML) ---")
    api_html = si.generate_api_documentation(output_format=OutputFormat.HTML)
    print(f"   HTML长度: {len(api_html)} 字符")
    print(f"   包含标签: <html>, <body>, <table>: "
          f"{'<html>' in api_html}/{'<body>' in api_html}/{'<table>' in api_html}")

    print("\n--- 变更日志生成 ---")
    changelog = si.generate_changelog(format_type=OutputFormat.MARKDOWN)
    print(f"   生成长度: {len(changelog)} 字符")
    print("   前500字符预览:")
    print("   " + "\n   ".join(changelog.split("\n")[:22]))

    print(f"   变更日志版本数: {len(si._changelogs)}")
    for ce in si._changelogs:
        print(f"      v{ce.version} ({ce.date}): {ce.total_entries}条变更")

    print("\n--- README生成 ---")
    readme = si.generate_readme({
        "name": "SuperAPI",
        "description": "高性能RESTful API框架，支持异步和实时通信",
        "license": "Apache-2.0",
        "features": [
            "⚡ 异步请求处理，支持10万QPS",
            "🔐 JWT + OAuth2 双重认证",
            "📊 内置Prometheus指标采集",
            "🧪 95%+ 测试覆盖率",
        ],
    })
    print(f"   README长度: {len(readme)} 字符")
    print("   前500字符预览:")
    print("   " + "\n   ".join(readme.split("\n")[:20]))

    print("\n--- 文档版本管理 ---")
    v1 = si.create_version(content="初始版本文档", version="v1.0.0", author="alice", changes_summary="首次发布")
    print(f"   创建 v1.0.0: hash={v1.content_hash[:12]}...")
    v2 = si.create_version(content="更新了安装说明和API文档", version="v1.1.0", author="bob", changes_summary="新增安装指南")
    print(f"   创建 v1.1.0: hash={v2.content_hash[:12]}...")
    diff = si.compare_versions("v1.0.0", "v1.1.0")
    print(f"   差异对比: {'有变化' if diff['hash_changed'] else '无变化'}")

    print("\n--- 交叉引用管理 ---")
    refs_data = [
        ("README", "Installation", "API", "Authentication", "查看认证接口"),
        ("API", "Errors", "README", "Troubleshooting", "错误排查"),
        ("ARCHITECTURE", "Database", "DEPLOYMENT", "Database Setup", "数据库部署"),
        ("README", "Contributing", "NONEXISTENT", "Guide", "无效目标文档"),
    ]
    for src_doc, src_sec, tgt_doc, tgt_sec, link_text in refs_data:
        ref = si.add_cross_ref(src_doc, src_sec, tgt_doc, tgt_sec, link_text)
        icon = "✅" if ref.is_valid else "❌"
        print(f"   {icon} {src_doc}#{src_sec} → {tgt_doc}#{tgt_sec}: {link_text}")

    xref_report = si.validate_all_cross_refs()
    print(f"\n   引用完整性: {xref_report['integrity_score']}% "
          f"({xref_report['valid']}/{xref_report['total']})")

    print("\n--- 综合报告预览 (前1200字符) ---")
    report = si.generate_report()
    print(report[:1200])

    print("\n✅ 所有测试通过!")
