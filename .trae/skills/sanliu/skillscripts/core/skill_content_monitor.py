#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
技能内容监控器 - Skill Content Monitor

监控技能文件的内容变化，提供深入的内容分析和变化报告。

核心功能:
- SKILL.md 内容监控: 解析内容结构、版本信息、功能描述变化
- 子技能文档监控: 检测新增/删除/修改的子技能，解析元数据变化
- 脚本内容监控: 检测函数签名、类结构、导入依赖变化
- 配置文件监控: 检测配置项变化，验证配置格式

使用示例:
    from skill_content_monitor import SkillContentMonitor
    
    monitor = SkillContentMonitor(skill_dir='./')
    report = await monitor.scan_and_report()
    
    for change in report.changes:
        print(f"{change.change_type.name}: {change.file_path}")
"""

import ast
import asyncio
import hashlib
import json
import logging
import re
import threading
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set, Tuple, Union

try:
    import yaml
    YAML_AVAILABLE = True
except ImportError:
    YAML_AVAILABLE = False

try:
    import tomli
    TOMLI_AVAILABLE = True
except ImportError:
    TOMLI_AVAILABLE = False


class ChangeType(Enum):
    CREATED = auto()
    MODIFIED = auto()
    DELETED = auto()


class ContentType(Enum):
    SKILL_MD = "skill_md"
    SUBSKILL = "subskill"
    SCRIPT = "script"
    CONFIG = "config"


class AnalysisLevel(Enum):
    BASIC = "basic"
    STANDARD = "standard"
    DEEP = "deep"


@dataclass
class ContentChange:
    file_path: Path
    change_type: ChangeType
    content_type: ContentType
    old_content: Optional[str] = None
    new_content: Optional[str] = None
    diff_summary: str = ""
    timestamp: datetime = field(default_factory=datetime.now)
    details: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "file_path": str(self.file_path),
            "change_type": self.change_type.name,
            "content_type": self.content_type.value,
            "diff_summary": self.diff_summary,
            "timestamp": self.timestamp.isoformat(),
            "details": self.details
        }


@dataclass
class MonitorReport:
    timestamp: datetime
    total_changes: int
    changes_by_type: Dict[ContentType, int]
    changes: List[ContentChange]
    recommendations: List[str]
    scan_duration_seconds: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp.isoformat(),
            "total_changes": self.total_changes,
            "changes_by_type": {k.value: v for k, v in self.changes_by_type.items()},
            "changes": [c.to_dict() for c in self.changes],
            "recommendations": self.recommendations,
            "scan_duration_seconds": self.scan_duration_seconds,
            "metadata": self.metadata
        }


@dataclass
class SkillMdMetadata:
    name: str = ""
    description: str = ""
    version: str = ""
    sections: List[str] = field(default_factory=list)
    keywords: List[str] = field(default_factory=list)
    triggers: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "version": self.version,
            "sections": self.sections,
            "keywords": self.keywords,
            "triggers": self.triggers
        }


@dataclass
class SubskillMetadata:
    name: str = ""
    description: str = ""
    version: str = ""
    category: str = ""
    dependencies: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "version": self.version,
            "category": self.category,
            "dependencies": self.dependencies,
            "tags": self.tags
        }


@dataclass
class ScriptStructure:
    file_path: Path
    imports: List[str] = field(default_factory=list)
    classes: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    functions: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    variables: List[str] = field(default_factory=list)
    has_main: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "file_path": str(self.file_path),
            "imports": self.imports,
            "classes": self.classes,
            "functions": self.functions,
            "variables": self.variables,
            "has_main": self.has_main
        }


@dataclass
class ConfigStructure:
    file_path: Path
    format: str = ""
    keys: List[str] = field(default_factory=list)
    nested_keys: Dict[str, List[str]] = field(default_factory=dict)
    is_valid: bool = True
    errors: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "file_path": str(self.file_path),
            "format": self.format,
            "keys": self.keys,
            "nested_keys": self.nested_keys,
            "is_valid": self.is_valid,
            "errors": self.errors
        }


class FileWatcher:
    SKILL_MD_NAME = "SKILL.md"
    SUBSKILL_DIR = "subskills"
    SCRIPTS_DIR = "skillscripts"
    CONFIG_PATTERNS = ["*.json", "*.yaml", "*.yml", "*.toml"]
    IGNORE_PATTERNS = [
        "__pycache__", "*.pyc", "*.pyo", ".git", "node_modules",
        "*.tmp", "*.bak", ".pytest_cache", "*.egg-info", "dist", "build"
    ]

    def __init__(self, skill_dir: Path):
        self._skill_dir = Path(skill_dir)
        self._file_states: Dict[str, Dict[str, Any]] = {}
        self._logger = logging.getLogger('FileWatcher')
        self._lock = threading.Lock()

    def scan_all(self) -> Dict[ContentType, List[Path]]:
        result: Dict[ContentType, List[Path]] = {
            ContentType.SKILL_MD: [],
            ContentType.SUBSKILL: [],
            ContentType.SCRIPT: [],
            ContentType.CONFIG: []
        }

        skill_md = self._skill_dir / self.SKILL_MD_NAME
        if skill_md.exists():
            result[ContentType.SKILL_MD].append(skill_md)

        subskill_dir = self._skill_dir / self.SUBSKILL_DIR
        if subskill_dir.exists():
            for md_file in subskill_dir.rglob("*.md"):
                if not self._should_ignore(md_file):
                    result[ContentType.SUBSKILL].append(md_file)

        scripts_dir = self._skill_dir / self.SCRIPTS_DIR
        if scripts_dir.exists():
            for py_file in scripts_dir.rglob("*.py"):
                if not self._should_ignore(py_file):
                    result[ContentType.SCRIPT].append(py_file)

        for pattern in self.CONFIG_PATTERNS:
            for config_file in self._skill_dir.rglob(pattern):
                if not self._should_ignore(config_file):
                    result[ContentType.CONFIG].append(config_file)

        return result

    def detect_changes(self) -> List[ContentChange]:
        changes: List[ContentChange] = []
        current_files = self.scan_all()
        current_paths: Set[str] = set()

        for content_type, files in current_files.items():
            for file_path in files:
                path_str = str(file_path)
                current_paths.add(path_str)

                current_state = self._get_file_state(file_path)
                cached_state = self._file_states.get(path_str)

                if cached_state is None:
                    changes.append(ContentChange(
                        file_path=file_path,
                        change_type=ChangeType.CREATED,
                        content_type=content_type,
                        new_content=self._read_file(file_path),
                        diff_summary="新文件创建"
                    ))
                elif current_state["hash"] != cached_state["hash"]:
                    changes.append(ContentChange(
                        file_path=file_path,
                        change_type=ChangeType.MODIFIED,
                        content_type=content_type,
                        old_content=cached_state.get("content"),
                        new_content=current_state.get("content"),
                        diff_summary="文件内容已修改"
                    ))

                with self._lock:
                    self._file_states[path_str] = current_state

        cached_paths = set(self._file_states.keys())
        deleted_paths = cached_paths - current_paths

        for path_str in deleted_paths:
            cached_state = self._file_states[path_str]
            content_type = self._determine_content_type(Path(path_str))

            changes.append(ContentChange(
                file_path=Path(path_str),
                change_type=ChangeType.DELETED,
                content_type=content_type,
                old_content=cached_state.get("content"),
                diff_summary="文件已删除"
            ))

            with self._lock:
                del self._file_states[path_str]

        return changes

    def _get_file_state(self, file_path: Path) -> Dict[str, Any]:
        content = self._read_file(file_path)
        hash_value = hashlib.sha256(content.encode('utf-8')).hexdigest() if content else ""

        return {
            "hash": hash_value,
            "mtime": file_path.stat().st_mtime if file_path.exists() else 0,
            "size": file_path.stat().st_size if file_path.exists() else 0,
            "content": content
        }

    def _read_file(self, file_path: Path) -> Optional[str]:
        try:
            return file_path.read_text(encoding='utf-8')
        except Exception as e:
            self._logger.error(f"读取文件失败 {file_path}: {e}")
            return None

    def _should_ignore(self, file_path: Path) -> bool:
        path_str = str(file_path)

        for pattern in self.IGNORE_PATTERNS:
            if pattern.startswith('*'):
                if path_str.endswith(pattern[1:]):
                    return True
            elif pattern in path_str:
                return True

        return False

    def _determine_content_type(self, file_path: Path) -> ContentType:
        name = file_path.name
        parent = file_path.parent.name

        if name == self.SKILL_MD_NAME:
            return ContentType.SKILL_MD

        if parent == self.SUBSKILL_DIR and name.endswith('.md'):
            return ContentType.SUBSKILL

        if name.endswith('.py'):
            return ContentType.SCRIPT

        if any(name.endswith(ext) for ext in ['.json', '.yaml', '.yml', '.toml']):
            return ContentType.CONFIG

        return ContentType.CONFIG

    def get_cached_files(self) -> Dict[str, Dict[str, Any]]:
        with self._lock:
            return self._file_states.copy()

    def clear_cache(self) -> None:
        with self._lock:
            self._file_states.clear()


class ContentAnalyzer:
    YAML_FRONTMATTER_PATTERN = re.compile(r'^---\s*\n(.*?)\n---\s*\n', re.DOTALL)
    SECTION_PATTERN = re.compile(r'^##\s+(.+)$', re.MULTILINE)
    KEYWORD_PATTERN = re.compile(r'[-*]\s+`?([^`\n]+)`?')

    def __init__(self):
        self._logger = logging.getLogger('ContentAnalyzer')
        self._script_cache: Dict[str, ScriptStructure] = {}
        self._config_cache: Dict[str, ConfigStructure] = {}

    def analyze_skill_md(self, content: str) -> SkillMdMetadata:
        metadata = SkillMdMetadata()

        frontmatter = self._parse_frontmatter(content)
        metadata.name = frontmatter.get('name', '')
        metadata.description = frontmatter.get('description', '')
        metadata.version = frontmatter.get('version', '')

        metadata.sections = self._extract_sections(content)
        metadata.keywords = self._extract_keywords(content)
        metadata.triggers = self._extract_triggers(content)

        return metadata

    def analyze_subskill(self, content: str) -> SubskillMetadata:
        metadata = SubskillMetadata()

        frontmatter = self._parse_frontmatter(content)
        metadata.name = frontmatter.get('name', '')
        metadata.description = frontmatter.get('description', '')
        metadata.version = frontmatter.get('version', '1.0.0')
        metadata.category = frontmatter.get('category', '')
        metadata.dependencies = self._extract_dependencies(content)
        metadata.tags = self._extract_tags(frontmatter, content)

        return metadata

    def analyze_script(self, content: str, file_path: Path) -> ScriptStructure:
        cache_key = str(file_path)
        content_hash = hashlib.sha256(content.encode()).hexdigest()

        if cache_key in self._script_cache:
            cached = self._script_cache[cache_key]
            if hasattr(cached, '_content_hash') and cached._content_hash == content_hash:
                return cached

        structure = ScriptStructure(file_path=file_path)
        structure._content_hash = content_hash

        try:
            tree = ast.parse(content)

            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        structure.imports.append(alias.name)
                elif isinstance(node, ast.ImportFrom):
                    module = node.module or ''
                    for alias in node.names:
                        structure.imports.append(f"{module}.{alias.name}" if module else alias.name)
                elif isinstance(node, ast.ClassDef):
                    structure.classes[node.name] = self._analyze_class(node)
                elif isinstance(node, ast.FunctionDef):
                    if not self._is_method(node, tree):
                        structure.functions[node.name] = self._analyze_function(node)
                elif isinstance(node, ast.AsyncFunctionDef):
                    if not self._is_method(node, tree):
                        structure.functions[node.name] = self._analyze_function(node)

            structure.has_main = self._check_main_guard(content)

        except SyntaxError as e:
            self._logger.error(f"解析脚本失败 {file_path}: {e}")
            structure._error = str(e)

        self._script_cache[cache_key] = structure
        return structure

    def analyze_config(self, content: str, file_path: Path) -> ConfigStructure:
        cache_key = str(file_path)
        content_hash = hashlib.sha256(content.encode()).hexdigest()

        if cache_key in self._config_cache:
            cached = self._config_cache[cache_key]
            if hasattr(cached, '_content_hash') and cached._content_hash == content_hash:
                return cached

        structure = ConfigStructure(file_path=file_path)
        structure._content_hash = content_hash

        suffix = file_path.suffix.lower()
        structure.format = suffix[1:] if suffix else 'unknown'

        try:
            if suffix == '.json':
                data = json.loads(content)
                structure.is_valid = True
                self._extract_config_keys(data, structure)
            elif suffix in ('.yaml', '.yml'):
                if YAML_AVAILABLE:
                    data = yaml.safe_load(content)
                    structure.is_valid = True
                    self._extract_config_keys(data, structure)
                else:
                    structure.errors.append("YAML库未安装")
            elif suffix == '.toml':
                if TOMLI_AVAILABLE:
                    data = tomli.loads(content)
                    structure.is_valid = True
                    self._extract_config_keys(data, structure)
                else:
                    structure.errors.append("TOML库未安装")
        except json.JSONDecodeError as e:
            structure.is_valid = False
            structure.errors.append(f"JSON解析错误: {e}")
        except yaml.YAMLError as e:
            structure.is_valid = False
            structure.errors.append(f"YAML解析错误: {e}")
        except Exception as e:
            structure.is_valid = False
            structure.errors.append(f"解析错误: {e}")

        self._config_cache[cache_key] = structure
        return structure

    def compare_skill_md(
        self,
        old_metadata: SkillMdMetadata,
        new_metadata: SkillMdMetadata
    ) -> Dict[str, Any]:
        diff = {
            "name_changed": old_metadata.name != new_metadata.name,
            "description_changed": old_metadata.description != new_metadata.description,
            "version_changed": old_metadata.version != new_metadata.version,
            "sections_added": list(set(new_metadata.sections) - set(old_metadata.sections)),
            "sections_removed": list(set(old_metadata.sections) - set(new_metadata.sections)),
            "keywords_added": list(set(new_metadata.keywords) - set(old_metadata.keywords)),
            "keywords_removed": list(set(old_metadata.keywords) - set(new_metadata.keywords)),
            "triggers_added": list(set(new_metadata.triggers) - set(old_metadata.triggers)),
            "triggers_removed": list(set(old_metadata.triggers) - set(new_metadata.triggers))
        }

        diff["has_changes"] = any([
            diff["name_changed"],
            diff["description_changed"],
            diff["version_changed"],
            diff["sections_added"],
            diff["sections_removed"],
            diff["keywords_added"],
            diff["keywords_removed"],
            diff["triggers_added"],
            diff["triggers_removed"]
        ])

        return diff

    def compare_subskill(
        self,
        old_metadata: SubskillMetadata,
        new_metadata: SubskillMetadata
    ) -> Dict[str, Any]:
        diff = {
            "name_changed": old_metadata.name != new_metadata.name,
            "description_changed": old_metadata.description != new_metadata.description,
            "version_changed": old_metadata.version != new_metadata.version,
            "category_changed": old_metadata.category != new_metadata.category,
            "dependencies_added": list(set(new_metadata.dependencies) - set(old_metadata.dependencies)),
            "dependencies_removed": list(set(old_metadata.dependencies) - set(new_metadata.dependencies)),
            "tags_added": list(set(new_metadata.tags) - set(old_metadata.tags)),
            "tags_removed": list(set(old_metadata.tags) - set(new_metadata.tags))
        }

        diff["has_changes"] = any([
            diff["name_changed"],
            diff["description_changed"],
            diff["version_changed"],
            diff["category_changed"],
            diff["dependencies_added"],
            diff["dependencies_removed"],
            diff["tags_added"],
            diff["tags_removed"]
        ])

        return diff

    def compare_scripts(
        self,
        old_structure: ScriptStructure,
        new_structure: ScriptStructure
    ) -> Dict[str, Any]:
        old_funcs = set(old_structure.functions.keys())
        new_funcs = set(new_structure.functions.keys())

        old_classes = set(old_structure.classes.keys())
        new_classes = set(new_structure.classes.keys())

        old_imports = set(old_structure.imports)
        new_imports = set(new_structure.imports)

        func_changes = []
        for func_name in old_funcs & new_funcs:
            old_sig = old_structure.functions[func_name]
            new_sig = new_structure.functions[func_name]
            if old_sig != new_sig:
                func_changes.append({
                    "name": func_name,
                    "old": old_sig,
                    "new": new_sig
                })

        class_changes = []
        for class_name in old_classes & new_classes:
            old_class = old_structure.classes[class_name]
            new_class = new_structure.classes[class_name]
            if old_class != new_class:
                class_changes.append({
                    "name": class_name,
                    "old": old_class,
                    "new": new_class
                })

        return {
            "functions_added": list(new_funcs - old_funcs),
            "functions_removed": list(old_funcs - new_funcs),
            "functions_modified": func_changes,
            "classes_added": list(new_classes - old_classes),
            "classes_removed": list(old_classes - new_classes),
            "classes_modified": class_changes,
            "imports_added": list(new_imports - old_imports),
            "imports_removed": list(old_imports - new_imports),
            "main_guard_changed": old_structure.has_main != new_structure.has_main,
            "has_changes": bool(
                new_funcs - old_funcs or
                old_funcs - new_funcs or
                func_changes or
                new_classes - old_classes or
                old_classes - new_classes or
                class_changes or
                new_imports - old_imports or
                old_imports - new_imports
            )
        }

    def compare_configs(
        self,
        old_structure: ConfigStructure,
        new_structure: ConfigStructure
    ) -> Dict[str, Any]:
        old_keys = set(old_structure.keys)
        new_keys = set(new_structure.keys)

        return {
            "keys_added": list(new_keys - old_keys),
            "keys_removed": list(old_keys - new_keys),
            "validity_changed": old_structure.is_valid != new_structure.is_valid,
            "errors_added": list(set(new_structure.errors) - set(old_structure.errors)),
            "errors_removed": list(set(old_structure.errors) - set(new_structure.errors)),
            "has_changes": bool(
                new_keys - old_keys or
                old_keys - new_keys or
                old_structure.is_valid != new_structure.is_valid
            )
        }

    def _parse_frontmatter(self, content: str) -> Dict[str, Any]:
        match = self.YAML_FRONTMATTER_PATTERN.match(content)
        if not match:
            return {}

        frontmatter = match.group(1)
        metadata = {}

        for line in frontmatter.split('\n'):
            if ':' in line:
                key, value = line.split(':', 1)
                key = key.strip()
                value = value.strip()

                if value.startswith('[') and value.endswith(']'):
                    value = [v.strip().strip('\'"') for v in value[1:-1].split(',') if v.strip()]

                metadata[key] = value

        return metadata

    def _extract_sections(self, content: str) -> List[str]:
        sections = []
        for match in self.SECTION_PATTERN.finditer(content):
            sections.append(match.group(1).strip())
        return sections

    def _extract_keywords(self, content: str) -> List[str]:
        keywords = set()
        for match in self.KEYWORD_PATTERN.finditer(content):
            keyword = match.group(1).strip()
            if keyword and len(keyword) > 1:
                keywords.add(keyword)
        return list(keywords)

    def _extract_triggers(self, content: str) -> List[str]:
        triggers = set()
        trigger_patterns = [
            r'关键词[：:]\s*([^\n]+)',
            r'触发[条件]?\s*[：:]\s*([^\n]+)',
            r'trigger[s]?\s*[：:]\s*([^\n]+)',
        ]

        for pattern in trigger_patterns:
            for match in re.finditer(pattern, content, re.IGNORECASE):
                trigger_text = match.group(1).strip()
                for trigger in re.split(r'[,，、;；]', trigger_text):
                    trigger = trigger.strip().strip('`\'"')
                    if trigger:
                        triggers.add(trigger)

        return list(triggers)

    def _extract_dependencies(self, content: str) -> List[str]:
        dependencies = set()
        dep_patterns = [
            r'调用\s+[`\'"]?([^`\'"\s]+\.(?:md|py|sh))[`\'"]?',
            r'依赖\s+[`\'"]?([^`\'"\s]+)[`\'"]?',
            r'requires?\s*:\s*([^\n]+)',
        ]

        for pattern in dep_patterns:
            for match in re.finditer(pattern, content, re.IGNORECASE):
                dep = match.group(1).strip()
                if dep:
                    dependencies.add(dep)

        return list(dependencies)

    def _extract_tags(self, frontmatter: Dict[str, Any], content: str) -> List[str]:
        tags = set()

        if 'tags' in frontmatter:
            if isinstance(frontmatter['tags'], list):
                tags.update(frontmatter['tags'])
            else:
                tags.add(str(frontmatter['tags']))

        for match in re.finditer(r'#(\w+)', content):
            tag = match.group(1)
            if len(tag) > 1:
                tags.add(tag)

        return list(tags)

    def _analyze_class(self, node: ast.ClassDef) -> Dict[str, Any]:
        bases = [self._get_name(base) for base in node.bases]

        methods = {}
        for item in node.body:
            if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                methods[item.name] = self._analyze_function(item)

        return {
            "bases": bases,
            "methods": list(methods.keys()),
            "method_details": methods,
            "docstring": ast.get_docstring(node) or ""
        }

    def _analyze_function(self, node: Union[ast.FunctionDef, ast.AsyncFunctionDef]) -> Dict[str, Any]:
        args = []
        defaults = []

        for arg in node.args.args:
            args.append(arg.arg)

        for default in node.args.defaults:
            defaults.append(self._get_value(default))

        return_type = ""
        if node.returns:
            return_type = self._get_annotation(node.returns)

        return {
            "args": args,
            "defaults": defaults,
            "return_type": return_type,
            "is_async": isinstance(node, ast.AsyncFunctionDef),
            "docstring": ast.get_docstring(node) or ""
        }

    def _is_method(self, node: ast.AST, tree: ast.Module) -> bool:
        for parent in ast.walk(tree):
            if isinstance(parent, ast.ClassDef):
                if node in parent.body:
                    return True
        return False

    def _check_main_guard(self, content: str) -> bool:
        return '__name__' in content and '__main__' in content

    def _get_name(self, node: ast.AST) -> str:
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            return f"{self._get_name(node.value)}.{node.attr}"
        elif isinstance(node, ast.Constant):
            return repr(node.value)
        return ""

    def _get_value(self, node: ast.AST) -> str:
        if isinstance(node, ast.Constant):
            return repr(node.value)
        elif isinstance(node, ast.Name):
            return node.id
        return ""

    def _get_annotation(self, node: ast.AST) -> str:
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Constant):
            return repr(node.value)
        elif isinstance(node, ast.Subscript):
            return f"{self._get_name(node.value)}[...]"
        return ""

    def _extract_config_keys(self, data: Any, structure: ConfigStructure, prefix: str = "") -> None:
        if isinstance(data, dict):
            for key, value in data.items():
                full_key = f"{prefix}.{key}" if prefix else key
                structure.keys.append(full_key)

                if isinstance(value, dict):
                    if full_key not in structure.nested_keys:
                        structure.nested_keys[full_key] = []
                    self._extract_config_keys(value, structure, full_key)
                elif isinstance(value, list) and value and isinstance(value[0], dict):
                    self._extract_config_keys(value[0], structure, f"{full_key}[]")

    def clear_cache(self) -> None:
        self._script_cache.clear()
        self._config_cache.clear()


class ChangeReporter:
    def __init__(self):
        self._logger = logging.getLogger('ChangeReporter')

    def generate_report(
        self,
        changes: List[ContentChange],
        analyzer: ContentAnalyzer,
        scan_duration: float = 0.0
    ) -> MonitorReport:
        timestamp = datetime.now()

        changes_by_type: Dict[ContentType, int] = {}
        for ct in ContentType:
            changes_by_type[ct] = 0

        for change in changes:
            changes_by_type[change.content_type] += 1
            self._enrich_change_details(change, analyzer)

        recommendations = self._generate_recommendations(changes)

        return MonitorReport(
            timestamp=timestamp,
            total_changes=len(changes),
            changes_by_type=changes_by_type,
            changes=changes,
            recommendations=recommendations,
            scan_duration_seconds=scan_duration,
            metadata={
                "analyzer_version": "1.0.0",
                "report_type": "content_monitor"
            }
        )

    def _enrich_change_details(self, change: ContentChange, analyzer: ContentAnalyzer) -> None:
        if change.change_type == ChangeType.DELETED:
            return

        if change.content_type == ContentType.SKILL_MD:
            if change.new_content:
                metadata = analyzer.analyze_skill_md(change.new_content)
                change.details["metadata"] = metadata.to_dict()

        elif change.content_type == ContentType.SUBSKILL:
            if change.new_content:
                metadata = analyzer.analyze_subskill(change.new_content)
                change.details["metadata"] = metadata.to_dict()

        elif change.content_type == ContentType.SCRIPT:
            if change.new_content:
                structure = analyzer.analyze_script(change.new_content, change.file_path)
                change.details["structure"] = structure.to_dict()

        elif change.content_type == ContentType.CONFIG:
            if change.new_content:
                structure = analyzer.analyze_config(change.new_content, change.file_path)
                change.details["structure"] = structure.to_dict()

    def _generate_recommendations(self, changes: List[ContentChange]) -> List[str]:
        recommendations = []

        skill_md_changes = [c for c in changes if c.content_type == ContentType.SKILL_MD]
        if skill_md_changes:
            recommendations.append("SKILL.md 文件已变更，建议检查版本号和功能描述是否需要更新")

        script_changes = [c for c in changes if c.content_type == ContentType.SCRIPT]
        new_scripts = [c for c in script_changes if c.change_type == ChangeType.CREATED]
        if new_scripts:
            recommendations.append(f"检测到 {len(new_scripts)} 个新脚本文件，建议检查是否符合脚本规范")

        deleted_scripts = [c for c in script_changes if c.change_type == ChangeType.DELETED]
        if deleted_scripts:
            recommendations.append(f"检测到 {len(deleted_scripts)} 个脚本文件被删除，建议检查是否有其他文件依赖这些脚本")

        config_changes = [c for c in changes if c.content_type == ContentType.CONFIG]
        invalid_configs = [
            c for c in config_changes
            if c.details.get("structure", {}).get("is_valid") is False
        ]
        if invalid_configs:
            recommendations.append(f"检测到 {len(invalid_configs)} 个配置文件格式无效，建议检查配置格式")

        subskill_changes = [c for c in changes if c.content_type == ContentType.SUBSKILL]
        new_subskills = [c for c in subskill_changes if c.change_type == ChangeType.CREATED]
        if new_subskills:
            recommendations.append(f"检测到 {len(new_subskills)} 个新子技能，建议检查子技能文档格式是否符合规范")

        return recommendations

    def format_report(self, report: MonitorReport, format_type: str = "text") -> str:
        if format_type == "json":
            return json.dumps(report.to_dict(), indent=2, ensure_ascii=False)
        elif format_type == "markdown":
            return self._format_as_markdown(report)
        else:
            return self._format_as_text(report)

    def _format_as_text(self, report: MonitorReport) -> str:
        lines = [
            f"=== 技能内容监控报告 ===",
            f"时间: {report.timestamp.strftime('%Y-%m-%d %H:%M:%S')}",
            f"总变化数: {report.total_changes}",
            f"扫描耗时: {report.scan_duration_seconds:.2f}秒",
            "",
            "变化统计:"
        ]

        for content_type, count in report.changes_by_type.items():
            lines.append(f"  - {content_type.value}: {count}")

        if report.changes:
            lines.append("")
            lines.append("变化详情:")
            for change in report.changes:
                lines.append(f"  [{change.change_type.name}] {change.file_path}")
                if change.diff_summary:
                    lines.append(f"    摘要: {change.diff_summary}")

        if report.recommendations:
            lines.append("")
            lines.append("建议:")
            for rec in report.recommendations:
                lines.append(f"  - {rec}")

        return "\n".join(lines)

    def _format_as_markdown(self, report: MonitorReport) -> str:
        lines = [
            f"# 技能内容监控报告",
            "",
            f"**时间**: {report.timestamp.strftime('%Y-%m-%d %H:%M:%S')}",
            f"**总变化数**: {report.total_changes}",
            f"**扫描耗时**: {report.scan_duration_seconds:.2f}秒",
            "",
            "## 变化统计",
            "",
            "| 类型 | 数量 |",
            "|------|------|"
        ]

        for content_type, count in report.changes_by_type.items():
            lines.append(f"| {content_type.value} | {count} |")

        if report.changes:
            lines.extend(["", "## 变化详情", ""])
            for change in report.changes:
                lines.append(f"- **[{change.change_type.name}]** `{change.file_path}`")
                if change.diff_summary:
                    lines.append(f"  - 摘要: {change.diff_summary}")

        if report.recommendations:
            lines.extend(["", "## 建议", ""])
            for rec in report.recommendations:
                lines.append(f"- {rec}")

        return "\n".join(lines)


class SkillContentMonitor:
    def __init__(
        self,
        skill_dir: Union[str, Path],
        analysis_level: AnalysisLevel = AnalysisLevel.STANDARD
    ):
        self._skill_dir = Path(skill_dir)
        self._analysis_level = analysis_level
        self._watcher = FileWatcher(self._skill_dir)
        self._analyzer = ContentAnalyzer()
        self._reporter = ChangeReporter()
        self._logger = logging.getLogger('SkillContentMonitor')

        self._watch_callbacks: List[Callable[[MonitorReport], None]] = []
        self._watch_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()

    def scan(self) -> List[ContentChange]:
        return self._watcher.detect_changes()

    def scan_and_report(self) -> MonitorReport:
        import time
        start_time = time.time()

        changes = self.scan()
        duration = time.time() - start_time

        return self._reporter.generate_report(changes, self._analyzer, duration)

    async def scan_async(self) -> List[ContentChange]:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.scan)

    async def scan_and_report_async(self) -> MonitorReport:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.scan_and_report)

    def get_skill_md_info(self) -> Optional[SkillMdMetadata]:
        skill_md = self._skill_dir / "SKILL.md"
        if not skill_md.exists():
            return None

        content = skill_md.read_text(encoding='utf-8')
        return self._analyzer.analyze_skill_md(content)

    def get_subskill_info(self, subskill_name: str) -> Optional[SubskillMetadata]:
        subskill_path = self._skill_dir / "subskills" / f"{subskill_name}.md"
        if not subskill_path.exists():
            return None

        content = subskill_path.read_text(encoding='utf-8')
        return self._analyzer.analyze_subskill(content)

    def get_script_info(self, script_path: Union[str, Path]) -> Optional[ScriptStructure]:
        path = Path(script_path)
        if not path.exists():
            return None

        content = path.read_text(encoding='utf-8')
        return self._analyzer.analyze_script(content, path)

    def get_config_info(self, config_path: Union[str, Path]) -> Optional[ConfigStructure]:
        path = Path(config_path)
        if not path.exists():
            return None

        content = path.read_text(encoding='utf-8')
        return self._analyzer.analyze_config(content, path)

    def list_all_files(self) -> Dict[ContentType, List[Path]]:
        return self._watcher.scan_all()

    def watch(
        self,
        callback: Callable[[MonitorReport], None],
        interval_seconds: int = 60
    ) -> None:
        self._watch_callbacks.append(callback)

        if self._watch_thread is None or not self._watch_thread.is_alive():
            self._stop_event.clear()
            self._watch_thread = threading.Thread(
                target=self._watch_loop,
                args=(interval_seconds,),
                daemon=True
            )
            self._watch_thread.start()

    def stop_watch(self) -> None:
        self._stop_event.set()
        self._watch_callbacks.clear()

        if self._watch_thread and self._watch_thread.is_alive():
            self._watch_thread.join(timeout=5)

    def _watch_loop(self, interval_seconds: int) -> None:
        while not self._stop_event.is_set():
            try:
                report = self.scan_and_report()

                if report.total_changes > 0:
                    for callback in self._watch_callbacks:
                        try:
                            callback(report)
                        except Exception as e:
                            self._logger.error(f"回调函数执行失败: {e}")

            except Exception as e:
                self._logger.error(f"监视循环错误: {e}")

            self._stop_event.wait(interval_seconds)

    def export_report(self, output_path: Union[str, Path], format_type: str = "json") -> bool:
        try:
            report = self.scan_and_report()
            content = self._reporter.format_report(report, format_type)

            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)

            output_path.write_text(content, encoding='utf-8')
            return True

        except Exception as e:
            self._logger.error(f"导出报告失败: {e}")
            return False

    def clear_cache(self) -> None:
        self._watcher.clear_cache()
        self._analyzer.clear_cache()

    def get_statistics(self) -> Dict[str, Any]:
        files = self.list_all_files()

        return {
            "skill_dir": str(self._skill_dir),
            "analysis_level": self._analysis_level.value,
            "files_count": {
                "skill_md": len(files[ContentType.SKILL_MD]),
                "subskills": len(files[ContentType.SUBSKILL]),
                "scripts": len(files[ContentType.SCRIPT]),
                "configs": len(files[ContentType.CONFIG])
            },
            "total_files": sum(len(f) for f in files.values()),
            "is_watching": self._watch_thread is not None and self._watch_thread.is_alive()
        }


def create_monitor(
    skill_dir: Union[str, Path],
    analysis_level: str = "standard"
) -> SkillContentMonitor:
    level_map = {
        "basic": AnalysisLevel.BASIC,
        "standard": AnalysisLevel.STANDARD,
        "deep": AnalysisLevel.DEEP
    }

    level = level_map.get(analysis_level.lower(), AnalysisLevel.STANDARD)
    return SkillContentMonitor(skill_dir, level)


def quick_scan(skill_dir: Union[str, Path]) -> MonitorReport:
    monitor = SkillContentMonitor(skill_dir)
    return monitor.scan_and_report()


async def quick_scan_async(skill_dir: Union[str, Path]) -> MonitorReport:
    monitor = SkillContentMonitor(skill_dir)
    return await monitor.scan_and_report_async()
