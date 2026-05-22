#!/usr/bin/env python3
"""
增量文档生成器 - Sanliu 技能流水线版本

基于代码变更分析，智能生成和更新文档，支持：
1. 变更内容分析 - 分析代码变更对文档的影响
2. 文档增量更新 - 只更新受影响的部分文档
3. 文档同步验证 - 验证文档与代码的一致性
4. 多种文档格式 - 支持Markdown、HTML、reStructuredText等
5. 智能变更检测 - 基于AST分析识别API变更
6. 文档版本管理 - 支持文档版本追踪

使用示例:
    python incremental_doc_generator.py --base main --head feature-branch
    python incremental_doc_generator.py --changed-files api.py,service.py
    python incremental_doc_generator.py --doc-dir docs/ --format markdown
"""

import argparse
import ast
import hashlib
import json
import logging
import re
import subprocess
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set, Tuple, Union

from skillscripts.core.script_base import ScriptBase, ReportFormat, ScriptResult, ScriptStatus


class ChangeType(Enum):
    ADDED = "added"
    MODIFIED = "modified"
    DELETED = "deleted"
    RENAMED = "renamed"


class DocFormat(Enum):
    MARKDOWN = "markdown"
    HTML = "html"
    RST = "rst"
    JSON = "json"


class UpdateType(Enum):
    FULL = "full"
    PARTIAL = "partial"
    SECTION = "section"
    NONE = "none"


class ChangeSeverity(Enum):
    MINOR = "minor"
    MODERATE = "moderate"
    MAJOR = "major"
    BREAKING = "breaking"


@dataclass
class CodeSymbol:
    name: str
    symbol_type: str
    file_path: str
    line_number: int
    docstring: Optional[str] = None
    signature: Optional[str] = None
    parameters: List[Dict[str, Any]] = field(default_factory=list)
    returns: Optional[Dict[str, Any]] = None
    decorators: List[str] = field(default_factory=list)
    is_public: bool = True
    is_deprecated: bool = False
    deprecation_message: Optional[str] = None
    is_async: bool = False
    is_classmethod: bool = False
    is_staticmethod: bool = False


@dataclass
class CodeChange:
    file_path: str
    change_type: ChangeType
    old_symbols: Set[str] = field(default_factory=set)
    new_symbols: Set[str] = field(default_factory=set)
    modified_symbols: Set[str] = field(default_factory=set)
    deleted_symbols: Set[str] = field(default_factory=set)
    added_symbols: Set[str] = field(default_factory=set)
    severity: ChangeSeverity = ChangeSeverity.MINOR
    change_details: Dict[str, Any] = field(default_factory=dict)


@dataclass
class DocSectionInfo:
    section_id: str
    section_type: str
    title: str
    content: str
    source_symbols: Set[str] = field(default_factory=set)
    last_updated: Optional[datetime] = None
    needs_update: bool = False
    update_priority: int = 0


@dataclass
class DocUpdate:
    doc_file: str
    update_type: UpdateType
    sections_to_update: List[str]
    new_content: Dict[str, str]
    reason: str
    priority: int = 0
    severity: ChangeSeverity = ChangeSeverity.MINOR


@dataclass
class SyncIssue:
    issue_type: str
    symbol_name: str
    doc_file: str
    description: str
    severity: str
    suggestion: str
    auto_fixable: bool = False


@dataclass
class GenerationResult:
    updated_files: List[str]
    created_files: List[str]
    skipped_files: List[str]
    sync_issues: List[SyncIssue]
    statistics: Dict[str, Any]
    change_summary: Dict[str, Any]


class CodeChangeAnalyzer:
    """代码变更分析器"""

    BREAKING_PATTERNS = [
        r"def\s+\w+\s*\([^)]*\)",
        r"class\s+\w+",
        r"async\s+def",
    ]

    MAJOR_PATTERNS = [
        r"return\s+",
        r"raise\s+",
        r"import\s+",
    ]

    def __init__(self, logger: logging.Logger):
        self.logger = logger

    def analyze_git_diff(
        self,
        base: str,
        head: str,
        repo_path: Path
    ) -> List[CodeChange]:
        """分析Git差异"""
        self.logger.info(f"分析Git差异: {base}...{head}")
        changes = []

        try:
            result = subprocess.run(
                ["git", "diff", "--name-status", f"{base}...{head}"],
                capture_output=True,
                text=True,
                cwd=repo_path
            )

            if result.returncode != 0:
                self.logger.error(f"Git diff失败: {result.stderr}")
                return changes

            for line in result.stdout.strip().split("\n"):
                if not line:
                    continue

                parts = line.split("\t")
                if len(parts) < 2:
                    continue

                status = parts[0]
                file_path = parts[1]

                if not file_path.endswith(".py"):
                    continue

                change = CodeChange(
                    file_path=file_path,
                    change_type=self._parse_change_type(status)
                )

                self._analyze_file_changes(change, base, head, repo_path)
                self._assess_severity(change)
                changes.append(change)

        except Exception as e:
            self.logger.error(f"分析Git差异失败: {e}")

        return changes

    def analyze_files(
        self,
        file_paths: List[str],
        repo_path: Path
    ) -> List[CodeChange]:
        """分析指定文件"""
        self.logger.info(f"分析文件: {file_paths}")
        changes = []

        for file_path in file_paths:
            full_path = repo_path / file_path
            if not full_path.exists():
                continue

            change = CodeChange(
                file_path=file_path,
                change_type=ChangeType.MODIFIED
            )

            symbols = self._extract_symbols(full_path)
            change.new_symbols = symbols
            self._assess_severity(change)
            changes.append(change)

        return changes

    def _parse_change_type(self, status: str) -> ChangeType:
        """解析变更类型"""
        status_map = {
            "A": ChangeType.ADDED,
            "M": ChangeType.MODIFIED,
            "D": ChangeType.DELETED,
            "R": ChangeType.RENAMED,
        }
        return status_map.get(status[0], ChangeType.MODIFIED)

    def _analyze_file_changes(
        self,
        change: CodeChange,
        base: str,
        head: str,
        repo_path: Path
    ) -> None:
        """分析文件变更"""
        old_content = self._get_file_content(repo_path / change.file_path, base)
        new_content = self._get_file_content(repo_path / change.file_path, head)

        change.old_symbols = self._extract_symbols_from_content(old_content)
        change.new_symbols = self._extract_symbols_from_content(new_content)

        change.added_symbols = change.new_symbols - change.old_symbols
        change.deleted_symbols = change.old_symbols - change.new_symbols
        change.modified_symbols = self._find_modified_symbols(
            old_content,
            new_content,
            change.old_symbols & change.new_symbols
        )

        change.change_details = self._analyze_change_details(
            old_content,
            new_content,
            change
        )

    def _get_file_content(self, file_path: Path, ref: str) -> Optional[str]:
        """获取指定版本的文件内容"""
        try:
            result = subprocess.run(
                ["git", "show", f"{ref}:{file_path}"],
                capture_output=True,
                text=True,
                cwd=file_path.parent if file_path.parent.exists() else Path.cwd()
            )

            if result.returncode == 0:
                return result.stdout
        except Exception:
            pass

        return None

    def _extract_symbols(self, file_path: Path) -> Set[str]:
        """提取文件中的符号"""
        try:
            content = file_path.read_text(encoding="utf-8")
            return self._extract_symbols_from_content(content)
        except Exception:
            return set()

    def _extract_symbols_from_content(self, content: Optional[str]) -> Set[str]:
        """从内容中提取符号"""
        if not content:
            return set()

        symbols = set()
        try:
            tree = ast.parse(content)
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
                    symbols.add(node.name)
                elif isinstance(node, ast.ClassDef):
                    symbols.add(node.name)
        except SyntaxError:
            pass

        return symbols

    def _find_modified_symbols(
        self,
        old_content: Optional[str],
        new_content: Optional[str],
        common_symbols: Set[str]
    ) -> Set[str]:
        """查找修改的符号"""
        modified = set()

        old_defs = self._extract_symbol_definitions(old_content)
        new_defs = self._extract_symbol_definitions(new_content)

        for symbol in common_symbols:
            old_def = old_defs.get(symbol)
            new_def = new_defs.get(symbol)

            if old_def != new_def:
                modified.add(symbol)

        return modified

    def _extract_symbol_definitions(self, content: Optional[str]) -> Dict[str, str]:
        """提取符号定义"""
        if not content:
            return {}

        definitions = {}
        try:
            tree = ast.parse(content)
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef):
                    try:
                        definitions[node.name] = ast.unparse(node)
                    except Exception:
                        definitions[node.name] = ""
        except SyntaxError:
            pass

        return definitions

    def _analyze_change_details(
        self,
        old_content: Optional[str],
        new_content: Optional[str],
        change: CodeChange
    ) -> Dict[str, Any]:
        """分析变更详情"""
        details = {
            "signature_changes": [],
            "parameter_changes": [],
            "return_type_changes": [],
            "docstring_changes": [],
            "decorator_changes": []
        }

        if not old_content or not new_content:
            return details

        try:
            old_tree = ast.parse(old_content)
            new_tree = ast.parse(new_content)

            old_funcs = self._extract_function_info(old_tree)
            new_funcs = self._extract_function_info(new_tree)

            for name in change.modified_symbols:
                old_info = old_funcs.get(name, {})
                new_info = new_funcs.get(name, {})

                if old_info.get("signature") != new_info.get("signature"):
                    details["signature_changes"].append({
                        "name": name,
                        "old": old_info.get("signature"),
                        "new": new_info.get("signature")
                    })

                if old_info.get("parameters") != new_info.get("parameters"):
                    details["parameter_changes"].append({
                        "name": name,
                        "old_params": old_info.get("parameters", []),
                        "new_params": new_info.get("parameters", [])
                    })

                if old_info.get("returns") != new_info.get("returns"):
                    details["return_type_changes"].append({
                        "name": name,
                        "old": old_info.get("returns"),
                        "new": new_info.get("returns")
                    })

                if old_info.get("docstring") != new_info.get("docstring"):
                    details["docstring_changes"].append({
                        "name": name,
                        "old": old_info.get("docstring"),
                        "new": new_info.get("docstring")
                    })

        except SyntaxError:
            pass

        return details

    def _extract_function_info(self, tree: ast.AST) -> Dict[str, Dict[str, Any]]:
        """提取函数信息"""
        funcs = {}
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
                params = []
                for arg in node.args.args:
                    params.append({
                        "name": arg.arg,
                        "type": ast.unparse(arg.annotation) if arg.annotation else None
                    })

                funcs[node.name] = {
                    "signature": self._get_signature(node),
                    "parameters": params,
                    "returns": ast.unparse(node.returns) if node.returns else None,
                    "docstring": ast.get_docstring(node),
                    "decorators": [self._get_decorator_name(d) for d in node.decorator_list]
                }
        return funcs

    def _get_signature(self, node: Union[ast.FunctionDef, ast.AsyncFunctionDef]) -> str:
        """获取函数签名"""
        try:
            return ast.unparse(node).split(":")[0].strip()
        except Exception:
            return f"{node.name}(...)"

    def _get_decorator_name(self, decorator: ast.expr) -> str:
        """获取装饰器名称"""
        if isinstance(decorator, ast.Name):
            return decorator.id
        elif isinstance(decorator, ast.Attribute):
            return decorator.attr
        elif isinstance(decorator, ast.Call):
            return self._get_decorator_name(decorator.func)
        return ""

    def _assess_severity(self, change: CodeChange) -> None:
        """评估变更严重程度"""
        if change.change_type == ChangeType.DELETED:
            change.severity = ChangeSeverity.BREAKING
            return

        if len(change.deleted_symbols) > 0:
            change.severity = ChangeSeverity.BREAKING
            return

        details = change.change_details
        if details.get("signature_changes") or details.get("parameter_changes"):
            change.severity = ChangeSeverity.MAJOR
            return

        if details.get("return_type_changes"):
            change.severity = ChangeSeverity.MODERATE
            return

        if len(change.added_symbols) > 3 or len(change.modified_symbols) > 5:
            change.severity = ChangeSeverity.MODERATE
            return

        change.severity = ChangeSeverity.MINOR


class SymbolExtractor:
    """符号提取器"""

    def __init__(self, logger: logging.Logger):
        self.logger = logger

    def extract_from_file(self, file_path: Path) -> List[CodeSymbol]:
        """从文件提取符号"""
        symbols = []

        try:
            content = file_path.read_text(encoding="utf-8")
            tree = ast.parse(content)

            for node in tree.body:
                if isinstance(node, ast.ClassDef):
                    symbols.append(self._extract_class(node, file_path))
                elif isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
                    symbols.append(self._extract_function(node, file_path))

        except Exception as e:
            self.logger.warning(f"提取符号失败 {file_path}: {e}")

        return symbols

    def _extract_class(self, node: ast.ClassDef, file_path: Path) -> CodeSymbol:
        """提取类信息"""
        decorators = [self._get_decorator_name(d) for d in node.decorator_list]
        
        symbol = CodeSymbol(
            name=node.name,
            symbol_type="class",
            file_path=str(file_path),
            line_number=node.lineno,
            docstring=ast.get_docstring(node),
            decorators=decorators,
            is_public=not node.name.startswith("_")
        )

        for item in node.body:
            if isinstance(item, ast.FunctionDef | ast.AsyncFunctionDef):
                if not item.name.startswith("_") or item.name in ["__init__", "__str__", "__repr__"]:
                    is_classmethod = any(
                        self._get_decorator_name(d) == "classmethod"
                        for d in item.decorator_list
                    )
                    is_staticmethod = any(
                        self._get_decorator_name(d) == "staticmethod"
                        for d in item.decorator_list
                    )
                    
                    symbol.parameters.append({
                        "name": item.name,
                        "type": "method",
                        "signature": self._get_function_signature(item),
                        "is_classmethod": is_classmethod,
                        "is_staticmethod": is_staticmethod,
                        "is_async": isinstance(item, ast.AsyncFunctionDef)
                    })

        return symbol

    def _extract_function(
        self,
        node: Union[ast.FunctionDef, ast.AsyncFunctionDef],
        file_path: Path
    ) -> CodeSymbol:
        """提取函数信息"""
        decorators = [self._get_decorator_name(d) for d in node.decorator_list]
        
        symbol = CodeSymbol(
            name=node.name,
            symbol_type="async_function" if isinstance(node, ast.AsyncFunctionDef) else "function",
            file_path=str(file_path),
            line_number=node.lineno,
            docstring=ast.get_docstring(node),
            signature=self._get_function_signature(node),
            decorators=decorators,
            is_public=not node.name.startswith("_"),
            is_async=isinstance(node, ast.AsyncFunctionDef),
            is_classmethod=any(d == "classmethod" for d in decorators),
            is_staticmethod=any(d == "staticmethod" for d in decorators)
        )

        for arg in node.args.args:
            param = {
                "name": arg.arg,
                "type": self._get_annotation(arg.annotation) if arg.annotation else "Any"
            }
            symbol.parameters.append(param)

        if node.returns:
            symbol.returns = {
                "type": self._get_annotation(node.returns)
            }

        return symbol

    def _get_function_signature(self, node: Union[ast.FunctionDef, ast.AsyncFunctionDef]) -> str:
        """获取函数签名"""
        try:
            return ast.unparse(node).split(":")[0].strip()
        except Exception:
            return f"{node.name}(...)"

    def _get_decorator_name(self, decorator: ast.expr) -> str:
        """获取装饰器名称"""
        if isinstance(decorator, ast.Name):
            return decorator.id
        elif isinstance(decorator, ast.Attribute):
            return f"{decorator.value.id}.{decorator.attr}" if isinstance(decorator.value, ast.Name) else decorator.attr
        elif isinstance(decorator, ast.Call):
            return self._get_decorator_name(decorator.func)
        return ""

    def _get_annotation(self, annotation: Optional[ast.expr]) -> str:
        """获取类型注解"""
        if annotation is None:
            return "Any"
        try:
            return ast.unparse(annotation)
        except Exception:
            return "Any"


class DocTemplateManager:
    """文档模板管理器"""

    def __init__(self, logger: logging.Logger):
        self.logger = logger
        self._templates: Dict[str, str] = {}
        self._load_default_templates()

    def _load_default_templates(self) -> None:
        """加载默认模板"""
        self._templates = {
            "class_markdown": """## {name}

{docstring}

**文件**: `{file_path}`

{decorators}

{deprecated_info}

### 方法

{methods}

{examples}
""",
            "function_markdown": """### {name}

```python
{signature}
```

{docstring}

{deprecated_info}

{parameters}

{returns}

{raises}

{examples}
""",
            "module_markdown": """# {module_name}

{overview}

生成时间: {timestamp}

## 模块内容

{contents}

## 变更历史

{changelog}
""",
            "api_markdown": """# API 文档

生成时间: {timestamp}

## 概述

{overview}

## 类

{classes}

## 函数

{functions}

## 变更历史

{changelog}
""",
            "changelog_markdown": """# 变更日志

## {version} ({date})

### 新增

{added}

### 修改

{modified}

### 删除

{deleted}

### 破坏性变更

{breaking}
""",
            "parameter_table": """| 参数名 | 类型 | 描述 |
| --- | --- | --- |
{parameter_rows}
""",
            "sync_issue": """## 文档同步问题

{issues}

### 修复建议

{suggestions}
"""
        }

    def get_template(self, template_name: str) -> Optional[str]:
        """获取模板"""
        return self._templates.get(template_name)

    def render(
        self,
        template_name: str,
        context: Dict[str, Any]
    ) -> str:
        """渲染模板"""
        template = self.get_template(template_name)
        if not template:
            return ""

        result = template
        for key, value in context.items():
            placeholder = "{" + key + "}"
            result = result.replace(placeholder, str(value) if value else "")

        return result


class DocSectionManager:
    """文档段落管理器"""

    def __init__(self, logger: logging.Logger):
        self.logger = logger
        self._sections: Dict[str, Dict[str, DocSectionInfo]] = defaultdict(dict)

    def parse_doc_file(self, doc_path: Path) -> Dict[str, DocSectionInfo]:
        """解析文档文件"""
        sections = {}

        try:
            content = doc_path.read_text(encoding="utf-8")
            parsed = self._parse_markdown_sections(content)

            for section_id, section_content in parsed.items():
                section = DocSectionInfo(
                    section_id=section_id,
                    section_type=self._determine_section_type(section_id),
                    title=self._extract_title(section_content),
                    content=section_content,
                    source_symbols=self._extract_source_symbols(section_content)
                )
                sections[section_id] = section

        except Exception as e:
            self.logger.warning(f"解析文档失败 {doc_path}: {e}")

        return sections

    def _parse_markdown_sections(self, content: str) -> Dict[str, str]:
        """解析Markdown段落"""
        sections = {}
        current_section = "header"
        current_content = []

        for line in content.split("\n"):
            if line.startswith("## "):
                if current_content:
                    sections[current_section] = "\n".join(current_content)
                current_section = line[3:].strip().lower().replace(" ", "_")
                current_content = [line]
            else:
                current_content.append(line)

        if current_content:
            sections[current_section] = "\n".join(current_content)

        return sections

    def _determine_section_type(self, section_id: str) -> str:
        """确定段落类型"""
        type_map = {
            "api": "api",
            "classes": "classes",
            "functions": "functions",
            "parameters": "parameters",
            "returns": "returns",
            "examples": "examples",
            "changelog": "changelog"
        }
        return type_map.get(section_id, "general")

    def _extract_title(self, content: str) -> str:
        """提取标题"""
        for line in content.split("\n"):
            if line.startswith("#"):
                return line.lstrip("#").strip()
        return ""

    def _extract_source_symbols(self, content: str) -> Set[str]:
        """提取源符号"""
        symbols = set()

        patterns = [
            r"`([^`]+)`",
            r"\*\*([^*]+)\*\*",
            r"### ([^\n]+)",
        ]

        for pattern in patterns:
            matches = re.findall(pattern, content)
            for match in matches:
                if isinstance(match, str):
                    symbols.add(match.strip())

        return symbols

    def update_section(
        self,
        doc_path: Path,
        section_id: str,
        new_content: str
    ) -> bool:
        """更新段落"""
        try:
            content = doc_path.read_text(encoding="utf-8")
            sections = self._parse_markdown_sections(content)

            if section_id in sections:
                lines = content.split("\n")
                new_lines = []
                in_section = False
                section_start = 0

                for i, line in enumerate(lines):
                    if line.startswith("## ") and section_id in line.lower().replace(" ", "_"):
                        in_section = True
                        section_start = i
                        new_lines.append(line)
                    elif in_section and line.startswith("## "):
                        in_section = False
                        new_lines.append(line)
                    elif not in_section:
                        new_lines.append(line)

                new_content_with_header = f"## {section_id.replace('_', ' ').title()}\n\n{new_content}"
                new_lines.insert(section_start + 1, new_content_with_header)

                doc_path.write_text("\n".join(new_lines), encoding="utf-8")
                return True
            else:
                with open(doc_path, "a", encoding="utf-8") as f:
                    f.write(f"\n\n## {section_id.replace('_', ' ').title()}\n\n{new_content}")
                return True

        except Exception as e:
            self.logger.error(f"更新段落失败: {e}")
            return False

    def mark_sections_for_update(
        self,
        sections: Dict[str, DocSectionInfo],
        changed_symbols: Set[str]
    ) -> None:
        """标记需要更新的段落"""
        for section_id, section in sections.items():
            if section.source_symbols & changed_symbols:
                section.needs_update = True
                section.update_priority = len(section.source_symbols & changed_symbols)


class SyncValidator:
    """文档同步验证器"""

    def __init__(self, logger: logging.Logger):
        self.logger = logger

    def validate(
        self,
        symbols: List[CodeSymbol],
        doc_sections: Dict[str, DocSectionInfo]
    ) -> List[SyncIssue]:
        """验证同步"""
        issues = []

        for symbol in symbols:
            if not symbol.is_public:
                continue

            found = False
            for section in doc_sections.values():
                if symbol.name in section.source_symbols:
                    found = True
                    break

            if not found:
                issues.append(SyncIssue(
                    issue_type="missing_documentation",
                    symbol_name=symbol.name,
                    doc_file="",
                    description=f"符号 '{symbol.name}' 缺少文档",
                    severity="warning",
                    suggestion=f"为 '{symbol.name}' 添加文档说明",
                    auto_fixable=True
                ))

        for section in doc_sections.values():
            for symbol_name in section.source_symbols:
                symbol_exists = any(s.name == symbol_name for s in symbols)
                if not symbol_exists:
                    issues.append(SyncIssue(
                        issue_type="orphan_documentation",
                        symbol_name=symbol_name,
                        doc_file="",
                        description=f"文档引用了不存在的符号 '{symbol_name}'",
                        severity="info",
                        suggestion=f"移除或更新 '{symbol_name}' 的文档",
                        auto_fixable=False
                    ))

        issues.extend(self._validate_docstrings(symbols))
        issues.extend(self._validate_signatures(symbols, doc_sections))

        return issues

    def _validate_docstrings(self, symbols: List[CodeSymbol]) -> List[SyncIssue]:
        """验证文档字符串"""
        issues = []

        for symbol in symbols:
            if not symbol.is_public:
                continue

            if not symbol.docstring:
                issues.append(SyncIssue(
                    issue_type="missing_docstring",
                    symbol_name=symbol.name,
                    doc_file="",
                    description=f"符号 '{symbol.name}' 缺少文档字符串",
                    severity="info",
                    suggestion=f"为 '{symbol.name}' 添加文档字符串",
                    auto_fixable=False
                ))
            elif len(symbol.docstring) < 10:
                issues.append(SyncIssue(
                    issue_type="insufficient_docstring",
                    symbol_name=symbol.name,
                    doc_file="",
                    description=f"符号 '{symbol.name}' 的文档字符串过短",
                    severity="info",
                    suggestion=f"扩展 '{symbol.name}' 的文档字符串",
                    auto_fixable=False
                ))

        return issues

    def _validate_signatures(
        self,
        symbols: List[CodeSymbol],
        doc_sections: Dict[str, DocSectionInfo]
    ) -> List[SyncIssue]:
        """验证签名一致性"""
        issues = []

        for symbol in symbols:
            if not symbol.signature:
                continue

            for section in doc_sections.values():
                if symbol.name in section.source_symbols:
                    if symbol.signature not in section.content:
                        issues.append(SyncIssue(
                            issue_type="signature_mismatch",
                            symbol_name=symbol.name,
                            doc_file="",
                            description=f"文档中的签名与代码不一致: {symbol.name}",
                            severity="warning",
                            suggestion=f"更新 '{symbol.name}' 的签名文档",
                            auto_fixable=True
                        ))

        return issues


class DocVersionManager:
    """文档版本管理器"""

    def __init__(self, logger: logging.Logger):
        self.logger = logger
        self._versions: Dict[str, List[Dict[str, Any]]] = defaultdict(list)

    def load_versions(self, version_file: Path) -> None:
        """加载版本历史"""
        if version_file.exists():
            try:
                with open(version_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self._versions = defaultdict(list, data)
            except Exception as e:
                self.logger.warning(f"加载版本历史失败: {e}")

    def save_versions(self, version_file: Path) -> None:
        """保存版本历史"""
        try:
            version_file.parent.mkdir(parents=True, exist_ok=True)
            with open(version_file, "w", encoding="utf-8") as f:
                json.dump(dict(self._versions), f, indent=2, ensure_ascii=False)
        except Exception as e:
            self.logger.error(f"保存版本历史失败: {e}")

    def record_version(
        self,
        doc_file: str,
        change: CodeChange,
        content_hash: str
    ) -> None:
        """记录版本"""
        version_entry = {
            "timestamp": datetime.now().isoformat(),
            "change_type": change.change_type.value,
            "severity": change.severity.value,
            "content_hash": content_hash,
            "symbols_added": list(change.added_symbols),
            "symbols_modified": list(change.modified_symbols),
            "symbols_deleted": list(change.deleted_symbols)
        }
        self._versions[doc_file].append(version_entry)

    def get_latest_version(self, doc_file: str) -> Optional[Dict[str, Any]]:
        """获取最新版本"""
        versions = self._versions.get(doc_file, [])
        return versions[-1] if versions else None


class IncrementalDocGenerator(ScriptBase):
    """增量文档生成器主类"""

    def __init__(self):
        super().__init__(
            name="incremental_doc_generator",
            version="2.0.0",
            description="增量文档生成器 - 支持变更分析、增量更新和同步验证",
            author="Sanliu"
        )
        self._setup_arguments()

        self.change_analyzer: Optional[CodeChangeAnalyzer] = None
        self.symbol_extractor: Optional[SymbolExtractor] = None
        self.template_manager: Optional[DocTemplateManager] = None
        self.section_manager: Optional[DocSectionManager] = None
        self.sync_validator: Optional[SyncValidator] = None
        self.version_manager: Optional[DocVersionManager] = None

        self._doc_cache: Dict[str, Dict[str, Any]] = {}
        self._symbol_cache: Dict[str, List[CodeSymbol]] = {}

    def _setup_arguments(self) -> None:
        self._command_parser.add_argument(
            "--project-path",
            type=str,
            default=".",
            help="项目路径"
        )
        self._command_parser.add_argument(
            "--doc-dir",
            type=str,
            default="docs",
            help="文档目录"
        )
        self._command_parser.add_argument(
            "--base",
            type=str,
            help="Git基础分支"
        )
        self._command_parser.add_argument(
            "--head",
            type=str,
            help="Git目标分支"
        )
        self._command_parser.add_argument(
            "--changed-files",
            type=str,
            help="变更文件列表 (逗号分隔)"
        )
        self._command_parser.add_argument(
            "--format",
            type=str,
            choices=["markdown", "html", "rst", "json"],
            default="markdown",
            help="文档格式"
        )
        self._command_parser.add_argument(
            "--validate",
            action="store_true",
            help="验证文档同步"
        )
        self._command_parser.add_argument(
            "--version-tracking",
            action="store_true",
            help="启用版本追踪"
        )
        self._command_parser.add_argument(
            "--output",
            type=str,
            choices=["console", "json"],
            default="console",
            help="输出格式"
        )
        self._command_parser.add_argument(
            "--output-file",
            type=str,
            help="输出文件路径"
        )

    def initialize(self, config: Dict[str, Any]) -> None:
        super().initialize(config)

        self.change_analyzer = CodeChangeAnalyzer(self._logger)
        self.symbol_extractor = SymbolExtractor(self._logger)
        self.template_manager = DocTemplateManager(self._logger)
        self.section_manager = DocSectionManager(self._logger)
        self.sync_validator = SyncValidator(self._logger)
        self.version_manager = DocVersionManager(self._logger)

    def validate_inputs(self, *args, **kwargs) -> bool:
        project_path = kwargs.get("project_path", ".")
        target_path = Path(project_path)
        if not target_path.exists():
            self._logger.error(f"项目路径不存在: {project_path}")
            return False
        return True

    def run(self, *args, **kwargs) -> Any:
        project_path = Path(kwargs.get("project_path", ".")).resolve()
        doc_dir = Path(kwargs.get("doc_dir", "docs"))
        base = kwargs.get("base")
        head = kwargs.get("head")
        changed_files_str = kwargs.get("changed_files")
        doc_format = DocFormat(kwargs.get("format", "markdown"))
        validate_sync = kwargs.get("validate", False)
        version_tracking = kwargs.get("version_tracking", False)

        self._logger.info("开始增量文档生成...")

        if version_tracking:
            version_file = doc_dir / ".doc_versions.json"
            self.version_manager.load_versions(version_file)

        changes: List[CodeChange] = []
        if base and head:
            changes = self.change_analyzer.analyze_git_diff(base, head, project_path)
        elif changed_files_str:
            changed_files = [f.strip() for f in changed_files_str.split(",")]
            changes = self.change_analyzer.analyze_files(changed_files, project_path)

        updates = self._plan_updates(changes)

        updated_files = []
        created_files = []
        skipped_files = []
        all_issues = []

        for update in updates:
            result = self._apply_update(update, doc_format)

            if result == "updated":
                updated_files.append(update.doc_file)
            elif result == "created":
                created_files.append(update.doc_file)
            else:
                skipped_files.append(update.doc_file)

            if version_tracking and result in ["updated", "created"]:
                doc_path = doc_dir / update.doc_file
                content_hash = self._compute_content_hash(doc_path)
                matching_changes = [c for c in changes if self._get_doc_file_for_source(c.file_path) == update.doc_file]
                if matching_changes:
                    self.version_manager.record_version(update.doc_file, matching_changes[0], content_hash)

        if validate_sync:
            all_issues = self._validate_all_sync(changes)

        statistics = self._build_statistics(
            changes,
            updates,
            updated_files,
            created_files,
            skipped_files
        )

        change_summary = self._build_change_summary(changes)

        result = GenerationResult(
            updated_files=updated_files,
            created_files=created_files,
            skipped_files=skipped_files,
            sync_issues=all_issues,
            statistics=statistics,
            change_summary=change_summary
        )

        self._report.add_section("生成统计", {
            "updated_count": len(updated_files),
            "created_count": len(created_files),
            "skipped_count": len(skipped_files),
            "sync_issues_count": len(all_issues)
        })

        if version_tracking:
            self.version_manager.save_versions(version_file)

        return {
            "updated_files": result.updated_files,
            "created_files": result.created_files,
            "skipped_files": result.skipped_files,
            "sync_issues": [
                {
                    "issue_type": i.issue_type,
                    "symbol_name": i.symbol_name,
                    "description": i.description,
                    "severity": i.severity,
                    "suggestion": i.suggestion,
                    "auto_fixable": i.auto_fixable
                }
                for i in result.sync_issues
            ],
            "statistics": result.statistics,
            "change_summary": result.change_summary
        }

    def _plan_updates(self, changes: List[CodeChange]) -> List[DocUpdate]:
        """规划更新"""
        updates = []

        for change in changes:
            doc_file = self._get_doc_file_for_source(change.file_path)

            if change.change_type == ChangeType.DELETED:
                updates.append(DocUpdate(
                    doc_file=doc_file,
                    update_type=UpdateType.SECTION,
                    sections_to_update=["all"],
                    new_content={},
                    reason="源文件已删除",
                    priority=1,
                    severity=change.severity
                ))
                continue

            source_path = Path(change.file_path)
            if not source_path.exists():
                continue

            symbols = self.symbol_extractor.extract_from_file(source_path)
            self._symbol_cache[change.file_path] = symbols

            new_content = self._generate_content_for_symbols(symbols, change.file_path)

            affected_sections = self._determine_affected_sections(
                change,
                symbols
            )

            update_type = UpdateType.FULL if change.change_type == ChangeType.ADDED else UpdateType.PARTIAL

            priority = 1 if change.severity == ChangeSeverity.BREAKING else 2 if change.severity == ChangeSeverity.MAJOR else 3

            updates.append(DocUpdate(
                doc_file=doc_file,
                update_type=update_type,
                sections_to_update=affected_sections,
                new_content=new_content,
                reason=f"源文件变更: {change.change_type.value} ({change.severity.value})",
                priority=priority,
                severity=change.severity
            ))

        return sorted(updates, key=lambda u: u.priority)

    def _get_doc_file_for_source(self, source_file: str) -> str:
        """获取源文件对应的文档文件"""
        module_name = source_file.replace("/", ".").replace(".py", "")
        return f"{module_name}.md"

    def _generate_content_for_symbols(
        self,
        symbols: List[CodeSymbol],
        source_file: str
    ) -> Dict[str, str]:
        """为符号生成内容"""
        content = {}

        classes = [s for s in symbols if s.symbol_type == "class"]
        functions = [s for s in symbols if s.symbol_type in ("function", "async_function")]

        if classes:
            class_content = []
            for cls in classes:
                deprecated_info = ""
                if cls.is_deprecated:
                    deprecated_info = f"\n> **已废弃**: {cls.deprecation_message or '请使用替代方案'}\n"

                methods = "\n".join(
                    f"- `{m['name']}`: {m.get('signature', '')}" +
                    (" (async)" if m.get('is_async') else "") +
                    (" (classmethod)" if m.get('is_classmethod') else "") +
                    (" (staticmethod)" if m.get('is_staticmethod') else "")
                    for m in cls.parameters
                )

                class_content.append(self.template_manager.render(
                    "class_markdown",
                    {
                        "name": cls.name,
                        "docstring": cls.docstring or "*暂无文档*",
                        "file_path": cls.file_path,
                        "decorators": f"装饰器: {', '.join(cls.decorators)}" if cls.decorators else "",
                        "deprecated_info": deprecated_info,
                        "methods": methods or "*无公共方法*",
                        "examples": ""
                    }
                ))
            content["classes"] = "\n\n".join(class_content)

        if functions:
            func_content = []
            for func in functions:
                params_str = "\n".join(
                    f"| `{p['name']}` | `{p['type']}` | |"
                    for p in func.parameters
                )
                parameters = self.template_manager.render(
                    "parameter_table",
                    {"parameter_rows": params_str}
                ) if params_str else ""

                returns_str = f"**返回**: `{func.returns['type']}`" if func.returns else ""
                
                deprecated_info = ""
                if func.is_deprecated:
                    deprecated_info = f"\n> **已废弃**: {func.deprecation_message or '请使用替代方案'}\n"

                func_content.append(self.template_manager.render(
                    "function_markdown",
                    {
                        "name": func.name,
                        "signature": func.signature or f"{func.name}(...)",
                        "docstring": func.docstring or "*暂无文档*",
                        "deprecated_info": deprecated_info,
                        "parameters": f"**参数**:\n\n{parameters}" if parameters else "",
                        "returns": returns_str,
                        "raises": "",
                        "examples": ""
                    }
                ))
            content["functions"] = "\n\n".join(func_content)

        return content

    def _determine_affected_sections(
        self,
        change: CodeChange,
        symbols: List[CodeSymbol]
    ) -> List[str]:
        """确定受影响的段落"""
        sections = set()

        has_classes = any(s.symbol_type == "class" for s in symbols)
        has_functions = any(s.symbol_type in ("function", "async_function") for s in symbols)

        if has_classes:
            sections.add("classes")
        if has_functions:
            sections.add("functions")

        if change.added_symbols or change.deleted_symbols:
            sections.add("overview")

        if change.severity in [ChangeSeverity.BREAKING, ChangeSeverity.MAJOR]:
            sections.add("changelog")

        return list(sections)

    def _apply_update(
        self,
        update: DocUpdate,
        doc_format: DocFormat
    ) -> str:
        """应用更新"""
        doc_path = Path(update.doc_file)

        if not doc_path.exists():
            return self._create_new_doc(doc_path, update, doc_format)

        if update.update_type == UpdateType.FULL:
            return self._full_update(doc_path, update, doc_format)
        elif update.update_type == UpdateType.PARTIAL:
            return self._partial_update(doc_path, update, doc_format)
        else:
            return self._section_update(doc_path, update, doc_format)

    def _create_new_doc(
        self,
        doc_path: Path,
        update: DocUpdate,
        doc_format: DocFormat
    ) -> str:
        """创建新文档"""
        try:
            doc_path.parent.mkdir(parents=True, exist_ok=True)

            module_name = doc_path.stem
            content = self.template_manager.render(
                "module_markdown",
                {
                    "module_name": module_name,
                    "overview": f"模块 {module_name} 的文档",
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "contents": "\n\n".join(update.new_content.values()),
                    "changelog": ""
                }
            )

            doc_path.write_text(content, encoding="utf-8")
            self._logger.info(f"创建文档: {doc_path}")
            return "created"

        except Exception as e:
            self._logger.error(f"创建文档失败 {doc_path}: {e}")
            return "skipped"

    def _full_update(
        self,
        doc_path: Path,
        update: DocUpdate,
        doc_format: DocFormat
    ) -> str:
        """完整更新"""
        try:
            module_name = doc_path.stem
            content = self.template_manager.render(
                "module_markdown",
                {
                    "module_name": module_name,
                    "overview": f"模块 {module_name} 的文档 (更新于 {datetime.now().strftime('%Y-%m-%d')})",
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "contents": "\n\n".join(update.new_content.values()),
                    "changelog": f"- {update.reason}"
                }
            )

            doc_path.write_text(content, encoding="utf-8")
            self._logger.info(f"完整更新文档: {doc_path}")
            return "updated"

        except Exception as e:
            self._logger.error(f"更新文档失败 {doc_path}: {e}")
            return "skipped"

    def _partial_update(
        self,
        doc_path: Path,
        update: DocUpdate,
        doc_format: DocFormat
    ) -> str:
        """部分更新"""
        try:
            for section_id, content in update.new_content.items():
                self.section_manager.update_section(doc_path, section_id, content)

            self._logger.info(f"部分更新文档: {doc_path}")
            return "updated"

        except Exception as e:
            self._logger.error(f"部分更新失败 {doc_path}: {e}")
            return "skipped"

    def _section_update(
        self,
        doc_path: Path,
        update: DocUpdate,
        doc_format: DocFormat
    ) -> str:
        """段落更新"""
        return self._partial_update(doc_path, update, doc_format)

    def _validate_all_sync(self, changes: List[CodeChange]) -> List[SyncIssue]:
        """验证所有同步"""
        all_issues = []

        for change in changes:
            if change.change_type == ChangeType.DELETED:
                continue

            source_path = Path(change.file_path)
            if not source_path.exists():
                continue

            symbols = self._symbol_cache.get(change.file_path)
            if not symbols:
                symbols = self.symbol_extractor.extract_from_file(source_path)

            doc_path = Path(self._get_doc_file_for_source(change.file_path))
            if doc_path.exists():
                sections = self.section_manager.parse_doc_file(doc_path)
                issues = self.sync_validator.validate(symbols, sections)
                all_issues.extend(issues)

        return all_issues

    def _compute_content_hash(self, file_path: Path) -> str:
        """计算内容哈希"""
        try:
            content = file_path.read_bytes()
            return hashlib.sha256(content).hexdigest()
        except Exception:
            return ""

    def _build_statistics(
        self,
        changes: List[CodeChange],
        updates: List[DocUpdate],
        updated_files: List[str],
        created_files: List[str],
        skipped_files: List[str]
    ) -> Dict[str, Any]:
        """构建统计信息"""
        severity_counts = defaultdict(int)
        for change in changes:
            severity_counts[change.severity.value] += 1

        return {
            "total_changes": len(changes),
            "added_files": sum(1 for c in changes if c.change_type == ChangeType.ADDED),
            "modified_files": sum(1 for c in changes if c.change_type == ChangeType.MODIFIED),
            "deleted_files": sum(1 for c in changes if c.change_type == ChangeType.DELETED),
            "total_updates": len(updates),
            "updated_count": len(updated_files),
            "created_count": len(created_files),
            "skipped_count": len(skipped_files),
            "severity_distribution": dict(severity_counts),
            "generation_time": datetime.now().isoformat()
        }

    def _build_change_summary(self, changes: List[CodeChange]) -> Dict[str, Any]:
        """构建变更摘要"""
        summary = {
            "breaking_changes": [],
            "major_changes": [],
            "moderate_changes": [],
            "minor_changes": [],
            "total_symbols_added": 0,
            "total_symbols_modified": 0,
            "total_symbols_deleted": 0
        }

        for change in changes:
            change_info = {
                "file": change.file_path,
                "type": change.change_type.value,
                "details": change.change_details
            }

            if change.severity == ChangeSeverity.BREAKING:
                summary["breaking_changes"].append(change_info)
            elif change.severity == ChangeSeverity.MAJOR:
                summary["major_changes"].append(change_info)
            elif change.severity == ChangeSeverity.MODERATE:
                summary["moderate_changes"].append(change_info)
            else:
                summary["minor_changes"].append(change_info)

            summary["total_symbols_added"] += len(change.added_symbols)
            summary["total_symbols_modified"] += len(change.modified_symbols)
            summary["total_symbols_deleted"] += len(change.deleted_symbols)

        return summary

    def print_report(self, result: Dict[str, Any]) -> None:
        """打印报告"""
        print("\n" + "=" * 80)
        print("增量文档生成报告")
        print("=" * 80)

        print(f"\n生成统计:")
        print(f"  更新文件: {len(result['updated_files'])}")
        print(f"  创建文件: {len(result['created_files'])}")
        print(f"  跳过文件: {len(result['skipped_files'])}")

        if result['updated_files']:
            print(f"\n已更新文件:")
            for f in result['updated_files'][:10]:
                print(f"  - {f}")
            if len(result['updated_files']) > 10:
                print(f"  ... 还有 {len(result['updated_files']) - 10} 个文件")

        if result['created_files']:
            print(f"\n已创建文件:")
            for f in result['created_files'][:10]:
                print(f"  - {f}")

        if result['sync_issues']:
            print(f"\n同步问题 ({len(result['sync_issues'])} 个):")
            for issue in result['sync_issues'][:10]:
                severity_icon = {
                    "error": "🔴",
                    "warning": "🟡",
                    "info": "🔵"
                }.get(issue['severity'], "⚪")
                auto_fix = "✓" if issue['auto_fixable'] else "✗"
                print(f"  {severity_icon} [{issue['issue_type']}] {issue['description']} [自动修复: {auto_fix}]")

        if result.get('change_summary'):
            summary = result['change_summary']
            print(f"\n变更摘要:")
            print(f"  破坏性变更: {len(summary['breaking_changes'])}")
            print(f"  重大变更: {len(summary['major_changes'])}")
            print(f"  中等变更: {len(summary['moderate_changes'])}")
            print(f"  轻微变更: {len(summary['minor_changes'])}")
            print(f"  符号变更: +{summary['total_symbols_added']} ~{summary['total_symbols_modified']} -{summary['total_symbols_deleted']}")

        print(f"\n详细统计:")
        for key, value in result['statistics'].items():
            if key != "severity_distribution":
                print(f"  {key}: {value}")

    def save_report(self, result: Dict[str, Any], output_path: Path) -> None:
        """保存报告"""
        output_path.parent.mkdir(parents=True, exist_ok=True)

        data = {
            "timestamp": datetime.now().isoformat(),
            **result
        }

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        self._logger.info(f"报告已保存: {output_path}")

    def cleanup(self) -> None:
        self._logger.info("清理增量文档生成器资源")


def main() -> int:
    generator = IncrementalDocGenerator()
    result = generator.run_from_command_line()

    args = generator._command_parser.parse()
    output_format = args.get("output", "console")
    output_file = args.get("output_file")

    if output_format == "console":
        generator.print_report(result.data)
    else:
        print(json.dumps(result.data, indent=2, ensure_ascii=False))

    if output_file:
        generator.save_report(result.data, Path(output_file))

    return 0


if __name__ == "__main__":
    sys.exit(main())
