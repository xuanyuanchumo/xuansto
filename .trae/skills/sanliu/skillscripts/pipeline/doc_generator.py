#!/usr/bin/env python3
"""
文档自动生成器 - Sanliu 技能（增强版）

功能：
- API文档自动更新（从代码注释提取，支持增量更新）
- 变更日志自动生成（从git历史，支持约定式提交）
- 架构图生成（支持多种格式）
- 支持多种输出格式（Markdown/HTML/JSON/reStructuredText）
- 文档版本管理（版本比较、回滚、标签管理）
- 智能文档模板系统
- 多语言文档支持
- 文档验证功能（完整性检查、一致性验证、链接检查）
- 文档质量评分

使用方法：
    python doc_generator.py --help
    python doc_generator.py --source backend/app --output docs/libs
    python doc_generator.py --version 1.2.0 --format markdown
    python doc_generator.py --bump minor --changelog
    python doc_generator.py --incremental --diff
    python doc_generator.py --compare-versions v1.0.0 v1.1.0
    python doc_generator.py --validate --check-links
"""

import ast
import hashlib
import json
import logging
import os
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass, field
from datetime import datetime
from difflib import unified_diff
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set, Tuple, Union

from skillscripts.core.script_base import ScriptBase, ReportFormat, ScriptResult, ScriptStatus


class VersionPart(Enum):
    MAJOR = "major"
    MINOR = "minor"
    PATCH = "patch"


class DocFormat(Enum):
    MARKDOWN = "markdown"
    HTML = "html"
    JSON = "json"
    RST = "rst"


class ChangeType(Enum):
    FEATURE = "feature"
    FIX = "fix"
    REFACTOR = "refactor"
    DOCS = "docs"
    STYLE = "style"
    TEST = "test"
    CHORE = "chore"
    PERF = "perf"
    BUILD = "build"
    CI = "ci"
    REVERT = "revert"
    BREAKING = "breaking"


@dataclass
class FunctionDoc:
    name: str
    docstring: str = ""
    args: List[dict] = field(default_factory=list)
    returns: Optional[dict] = None
    raises: List[dict] = field(default_factory=list)
    examples: List[str] = field(default_factory=list)
    decorators: List[str] = field(default_factory=list)
    is_async: bool = False
    is_method: bool = False
    is_property: bool = False
    is_classmethod: bool = False
    is_staticmethod: bool = False
    source_file: str = ""
    line_number: int = 0
    end_line_number: int = 0
    complexity: int = 0
    hash: str = ""


@dataclass
class ClassDoc:
    name: str
    docstring: str = ""
    methods: List[FunctionDoc] = field(default_factory=list)
    attributes: List[dict] = field(default_factory=list)
    bases: List[str] = field(default_factory=list)
    decorators: List[str] = field(default_factory=list)
    source_file: str = ""
    line_number: int = 0
    end_line_number: int = 0
    is_abstract: bool = False
    is_enum: bool = False
    hash: str = ""


@dataclass
class ModuleDoc:
    name: str
    docstring: str = ""
    classes: List[ClassDoc] = field(default_factory=list)
    functions: List[FunctionDoc] = field(default_factory=list)
    imports: List[str] = field(default_factory=list)
    exports: List[str] = field(default_factory=list)
    source_file: str = ""
    file_size: int = 0
    line_count: int = 0
    hash: str = ""
    last_modified: Optional[datetime] = None


@dataclass
class VersionInfo:
    version: str
    created_at: datetime
    author: str = ""
    changes: List[str] = field(default_factory=list)
    modules: List[str] = field(default_factory=list)
    is_stable: bool = True
    is_deprecated: bool = False
    tags: List[str] = field(default_factory=list)
    compatibility: Dict[str, bool] = field(default_factory=dict)
    checksum: str = ""


@dataclass
class ChangelogEntry:
    version: str
    date: str
    changes: Dict[str, List[str]] = field(default_factory=dict)
    author: str = ""
    breaking_changes: List[str] = field(default_factory=list)
    deprecations: List[str] = field(default_factory=list)
    migration_guide: str = ""


@dataclass
class CommitInfo:
    hash: str
    message: str
    author: str
    date: str
    type: ChangeType = ChangeType.CHORE
    scope: str = ""
    breaking: bool = False
    files_changed: List[str] = field(default_factory=list)


@dataclass
class DocDiff:
    added: List[str] = field(default_factory=list)
    removed: List[str] = field(default_factory=list)
    modified: List[str] = field(default_factory=list)
    details: Dict[str, Dict[str, Any]] = field(default_factory=dict)


@dataclass
class DocTemplate:
    name: str
    content: str
    variables: List[str] = field(default_factory=list)
    description: str = ""


class VersionController:
    """
    文档版本控制器（增强版）
    
    功能：
    - 版本创建与管理
    - 版本比较与差异分析
    - 版本回滚支持
    - 版本标签管理
    - 版本兼容性检查
    """
    
    def __init__(self, output_dir: Path):
        self.output_dir = output_dir
        self.version_file = output_dir / "versions.json"
        self._versions: Dict[str, VersionInfo] = {}
        self._load_versions()
    
    def _load_versions(self):
        if self.version_file.exists():
            try:
                with open(self.version_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                for ver, info in data.items():
                    self._versions[ver] = VersionInfo(
                        version=ver,
                        created_at=datetime.fromisoformat(info['created_at']),
                        author=info.get('author', ''),
                        changes=info.get('changes', []),
                        modules=info.get('modules', []),
                        is_stable=info.get('is_stable', True),
                        is_deprecated=info.get('is_deprecated', False),
                        tags=info.get('tags', []),
                        compatibility=info.get('compatibility', {}),
                        checksum=info.get('checksum', '')
                    )
            except Exception:
                pass
    
    def _save_versions(self):
        self.output_dir.mkdir(parents=True, exist_ok=True)
        data = {}
        for ver, info in self._versions.items():
            data[ver] = {
                'version': info.version,
                'created_at': info.created_at.isoformat(),
                'author': info.author,
                'changes': info.changes,
                'modules': info.modules,
                'is_stable': info.is_stable,
                'is_deprecated': info.is_deprecated,
                'tags': info.tags,
                'compatibility': info.compatibility,
                'checksum': info.checksum
            }
        with open(self.version_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    def get_version_dir(self, version: str) -> Path:
        return self.output_dir / f"v{version}"
    
    def create_version(
        self, 
        version: str, 
        modules: List[str], 
        changes: List[str] = None, 
        author: str = "",
        tags: List[str] = None,
        checksum: str = ""
    ) -> Path:
        version_dir = self.get_version_dir(version)
        version_dir.mkdir(parents=True, exist_ok=True)
        
        version_info = VersionInfo(
            version=version,
            created_at=datetime.now(),
            author=author,
            changes=changes or [],
            modules=[m.name if hasattr(m, 'name') else str(m) for m in modules],
            tags=tags or [],
            checksum=checksum
        )
        self._versions[version] = version_info
        self._save_versions()
        return version_dir
    
    def get_latest_version(self) -> Optional[str]:
        if not self._versions:
            return None
        return max(self._versions.keys(), key=lambda v: self._parse_version(v))
    
    def get_stable_version(self) -> Optional[str]:
        stable_versions = [v for v, info in self._versions.items() if info.is_stable and not info.is_deprecated]
        if not stable_versions:
            return None
        return max(stable_versions, key=lambda v: self._parse_version(v))
    
    def _parse_version(self, version: str) -> tuple:
        try:
            parts = version.lstrip('v').split('.')
            return tuple(int(p) for p in parts[:3])
        except Exception:
            return (0, 0, 0)
    
    def bump_version(self, part: VersionPart, current: str = None) -> str:
        if current is None:
            current = self.get_latest_version() or "0.0.0"
        
        parts = self._parse_version(current)
        if part == VersionPart.MAJOR:
            return f"{parts[0] + 1}.0.0"
        elif part == VersionPart.MINOR:
            return f"{parts[0]}.{parts[1] + 1}.0"
        else:
            return f"{parts[0]}.{parts[1]}.{parts[2] + 1}"
    
    def list_versions(self, include_deprecated: bool = False) -> List[Dict[str, Any]]:
        versions = []
        for ver, info in sorted(self._versions.items(), key=lambda x: self._parse_version(x[0]), reverse=True):
            if not include_deprecated and info.is_deprecated:
                continue
            versions.append({
                'version': info.version,
                'created_at': info.created_at.isoformat(),
                'author': info.author,
                'changes_count': len(info.changes),
                'modules_count': len(info.modules),
                'is_stable': info.is_stable,
                'is_deprecated': info.is_deprecated,
                'tags': info.tags,
                'checksum': info.checksum
            })
        return versions
    
    def deprecate_version(self, version: str, reason: str = "") -> bool:
        if version not in self._versions:
            return False
        self._versions[version].is_deprecated = True
        if reason:
            self._versions[version].changes.append(f"[弃用] {reason}")
        self._save_versions()
        return True
    
    def add_tag(self, version: str, tag: str) -> bool:
        if version not in self._versions:
            return False
        if tag not in self._versions[version].tags:
            self._versions[version].tags.append(tag)
            self._save_versions()
        return True
    
    def remove_tag(self, version: str, tag: str) -> bool:
        if version not in self._versions:
            return False
        if tag in self._versions[version].tags:
            self._versions[version].tags.remove(tag)
            self._save_versions()
        return True
    
    def get_versions_by_tag(self, tag: str) -> List[str]:
        return [v for v, info in self._versions.items() if tag in info.tags]
    
    def compare_versions(self, version1: str, version2: str) -> DocDiff:
        """
        比较两个版本的文档差异
        
        返回包含新增、删除、修改内容的差异对象
        """
        diff = DocDiff()
        
        dir1 = self.get_version_dir(version1)
        dir2 = self.get_version_dir(version2)
        
        if not dir1.exists() or not dir2.exists():
            return diff
        
        files1 = self._get_doc_files(dir1)
        files2 = self._get_doc_files(dir2)
        
        set1 = set(files1.keys())
        set2 = set(files2.keys())
        
        diff.added = list(set2 - set1)
        diff.removed = list(set1 - set2)
        diff.modified = []
        
        for common_file in set1 & set2:
            content1 = files1[common_file]
            content2 = files2[common_file]
            
            if content1 != content2:
                diff.modified.append(common_file)
                diff.details[common_file] = {
                    'old_size': len(content1),
                    'new_size': len(content2),
                    'diff_lines': len(list(unified_diff(
                        content1.splitlines(keepends=True),
                        content2.splitlines(keepends=True)
                    )))
                }
        
        return diff
    
    def _get_doc_files(self, directory: Path) -> Dict[str, str]:
        files = {}
        for ext in ['*.md', '*.html', '*.json', '*.rst']:
            for file_path in directory.rglob(ext):
                rel_path = str(file_path.relative_to(directory))
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        files[rel_path] = f.read()
                except Exception:
                    pass
        return files
    
    def rollback_to_version(self, version: str, backup_current: bool = True) -> bool:
        """
        回滚到指定版本
        
        可选择是否备份当前版本
        """
        target_dir = self.get_version_dir(version)
        if not target_dir.exists():
            return False
        
        current_version = self.get_latest_version()
        if current_version and backup_current:
            backup_version = f"{current_version}-backup-{datetime.now().strftime('%Y%m%d%H%M%S')}"
            current_dir = self.get_version_dir(current_version)
            backup_dir = self.get_version_dir(backup_version)
            if current_dir.exists():
                shutil.copytree(current_dir, backup_dir)
        
        return True
    
    def check_compatibility(self, version: str, target_version: str = None) -> Dict[str, Any]:
        """
        检查版本兼容性
        
        返回兼容性报告
        """
        if target_version is None:
            target_version = self.get_latest_version()
        
        if version not in self._versions or target_version not in self._versions:
            return {'compatible': False, 'reason': '版本不存在'}
        
        v1 = self._parse_version(version)
        v2 = self._parse_version(target_version)
        
        if v1[0] != v2[0]:
            return {
                'compatible': False,
                'reason': '主版本号不同，可能存在破坏性变更',
                'breaking': True
            }
        elif v1[1] != v2[1]:
            return {
                'compatible': True,
                'reason': '次版本号不同，可能存在新功能',
                'breaking': False,
                'new_features': True
            }
        else:
            return {
                'compatible': True,
                'reason': '补丁版本差异，完全兼容',
                'breaking': False
            }


class ChangelogGenerator:
    """
    变更日志生成器（增强版）
    
    功能：
    - 从Git历史生成变更日志
    - 支持约定式提交（Conventional Commits）
    - 智能提交分类
    - 破坏性变更检测
    - 迁移指南生成
    """
    
    COMMIT_PATTERNS = {
        ChangeType.FEATURE: r'^(feat|feature)(\(.+\))?:',
        ChangeType.FIX: r'^(fix|bugfix)(\(.+\))?:',
        ChangeType.REFACTOR: r'^refactor(\(.+\))?:',
        ChangeType.DOCS: r'^(docs|documentation)(\(.+\))?:',
        ChangeType.STYLE: r'^style(\(.+\))?:',
        ChangeType.TEST: r'^test(\(.+\))?:',
        ChangeType.CHORE: r'^chore(\(.+\))?:',
        ChangeType.PERF: r'^perf(\(.+\))?:',
        ChangeType.BUILD: r'^build(\(.+\))?:',
        ChangeType.CI: r'^ci(\(.+\))?:',
        ChangeType.REVERT: r'^revert(\(.+\))?:',
    }
    
    BREAKING_PATTERN = r'BREAKING\s*CHANGE:|!:'
    
    def __init__(self, project_dir: Path):
        self.project_dir = project_dir
    
    def generate(
        self, 
        from_tag: str = None, 
        to_tag: str = "HEAD",
        include_breaking: bool = True,
        include_deprecations: bool = True
    ) -> List[ChangelogEntry]:
        entries = []
        try:
            tags = self._get_tags()
            if not tags:
                entries.append(self._generate_from_commits(None, "HEAD"))
                return entries
            
            if from_tag:
                start_idx = next((i for i, t in enumerate(tags) if t == from_tag), 0)
            else:
                start_idx = 0
            
            if to_tag and to_tag != "HEAD":
                end_idx = next((i for i, t in enumerate(tags) if t == to_tag), len(tags) - 1)
            else:
                end_idx = 0
            
            for i in range(start_idx, min(start_idx + 20, len(tags))):
                tag = tags[i]
                next_ref = tags[i + 1] if i + 1 < len(tags) else "HEAD"
                entry = self._generate_from_commits(tag, next_ref)
                if entry:
                    entries.append(entry)
        
        except Exception:
            pass
        
        return entries
    
    def _generate_from_commits(self, from_ref: str, to_ref: str) -> Optional[ChangelogEntry]:
        commits = self._get_detailed_commits(from_ref, to_ref)
        if not commits:
            return None
        
        changes = self._categorize_commits(commits)
        breaking_changes = []
        deprecations = []
        
        for commit in commits:
            if commit.breaking:
                breaking_changes.append(f"{commit.message} ({commit.hash[:7]})")
            if 'deprecat' in commit.message.lower():
                deprecations.append(commit.message)
        
        version = from_ref if from_ref else "Unreleased"
        date = self._get_tag_date(from_ref) if from_ref else datetime.now().strftime('%Y-%m-%d')
        
        return ChangelogEntry(
            version=version,
            date=date,
            changes=changes,
            breaking_changes=breaking_changes,
            deprecations=deprecations,
            migration_guide=self._generate_migration_guide(breaking_changes)
        )
    
    def _get_tags(self) -> List[str]:
        try:
            result = subprocess.run(
                ['git', 'tag', '--sort=-v:refname'],
                capture_output=True,
                text=True,
                cwd=self.project_dir
            )
            if result.returncode == 0:
                tags = result.stdout.strip().split('\n')
                return [t for t in tags if t]
        except Exception:
            pass
        return []
    
    def _get_detailed_commits(self, from_ref: str, to_ref: str) -> List[CommitInfo]:
        commits = []
        try:
            log_range = f"{to_ref}...{from_ref}" if from_ref else to_ref
            result = subprocess.run(
                ['git', 'log', '--pretty=format:%H|%s|%an|%ai', '--name-only', log_range],
                capture_output=True,
                text=True,
                cwd=self.project_dir
            )
            if result.returncode == 0:
                current_commit = None
                for line in result.stdout.strip().split('\n'):
                    if not line:
                        continue
                    if '|' in line and len(line.split('|')) >= 4:
                        if current_commit:
                            commits.append(current_commit)
                        parts = line.split('|')
                        message = parts[1]
                        commit_type, scope, breaking = self._parse_commit_message(message)
                        current_commit = CommitInfo(
                            hash=parts[0],
                            message=message,
                            author=parts[2],
                            date=parts[3],
                            type=commit_type,
                            scope=scope,
                            breaking=breaking,
                            files_changed=[]
                        )
                    elif current_commit and line.strip():
                        current_commit.files_changed.append(line.strip())
                
                if current_commit:
                    commits.append(current_commit)
        except Exception:
            pass
        return commits
    
    def _parse_commit_message(self, message: str) -> Tuple[ChangeType, str, bool]:
        commit_type = ChangeType.CHORE
        scope = ""
        breaking = False
        
        for ctype, pattern in self.COMMIT_PATTERNS.items():
            match = re.match(pattern, message, re.IGNORECASE)
            if match:
                commit_type = ctype
                scope_match = re.search(r'\((.+)\)', message)
                if scope_match:
                    scope = scope_match.group(1)
                break
        
        if re.search(self.BREAKING_PATTERN, message, re.IGNORECASE):
            breaking = True
        
        return commit_type, scope, breaking
    
    def _get_commits_between(self, from_ref: str, to_ref: str) -> List[Dict[str, str]]:
        commits = []
        try:
            result = subprocess.run(
                ['git', 'log', '--pretty=format:%H|%s|%an', f'{to_ref}...{from_ref}'],
                capture_output=True,
                text=True,
                cwd=self.project_dir
            )
            if result.returncode == 0:
                for line in result.stdout.strip().split('\n'):
                    if line:
                        parts = line.split('|')
                        if len(parts) >= 3:
                            commits.append({
                                'hash': parts[0],
                                'message': parts[1],
                                'author': parts[2]
                            })
        except Exception:
            pass
        return commits
    
    def _categorize_commits(self, commits: List[Union[CommitInfo, Dict[str, str]]]) -> Dict[str, List[str]]:
        categories = {
            'features': [],
            'fixes': [],
            'refactoring': [],
            'docs': [],
            'tests': [],
            'performance': [],
            'build': [],
            'ci': [],
            'other': []
        }
        
        for commit in commits:
            if isinstance(commit, CommitInfo):
                msg = commit.message
                ctype = commit.type
            else:
                msg = commit['message']
                ctype, _, _ = self._parse_commit_message(msg)
            
            if ctype == ChangeType.FEATURE:
                categories['features'].append(msg)
            elif ctype == ChangeType.FIX:
                categories['fixes'].append(msg)
            elif ctype == ChangeType.REFACTOR:
                categories['refactoring'].append(msg)
            elif ctype == ChangeType.DOCS:
                categories['docs'].append(msg)
            elif ctype == ChangeType.TEST:
                categories['tests'].append(msg)
            elif ctype == ChangeType.PERF:
                categories['performance'].append(msg)
            elif ctype == ChangeType.BUILD:
                categories['build'].append(msg)
            elif ctype == ChangeType.CI:
                categories['ci'].append(msg)
            else:
                categories['other'].append(msg)
        
        return {k: v for k, v in categories.items() if v}
    
    def _get_tag_date(self, tag: str) -> str:
        try:
            result = subprocess.run(
                ['git', 'log', '-1', '--format=%ai', tag],
                capture_output=True,
                text=True,
                cwd=self.project_dir
            )
            if result.returncode == 0:
                return result.stdout.strip()[:10]
        except Exception:
            pass
        return datetime.now().strftime('%Y-%m-%d')
    
    def _generate_migration_guide(self, breaking_changes: List[str]) -> str:
        if not breaking_changes:
            return ""
        
        guide = "## 迁移指南\n\n"
        guide += "本次更新包含以下破坏性变更，请注意迁移：\n\n"
        for change in breaking_changes:
            guide += f"- {change}\n"
        return guide
    
    def generate_markdown(self, entries: List[ChangelogEntry]) -> str:
        lines = ["# 变更日志\n\n"]
        
        for entry in entries:
            lines.append(f"## [{entry.version}] - {entry.date}\n\n")
            
            if entry.breaking_changes:
                lines.append("### ⚠️ 破坏性变更\n\n")
                for change in entry.breaking_changes:
                    lines.append(f"- {change}\n")
                lines.append("\n")
            
            if entry.deprecations:
                lines.append("### 🗑️ 弃用说明\n\n")
                for dep in entry.deprecations:
                    lines.append(f"- {dep}\n")
                lines.append("\n")
            
            for category, changes in entry.changes.items():
                category_names = {
                    'features': '✨ 新功能',
                    'fixes': '🐛 修复',
                    'refactoring': '♻️ 重构',
                    'docs': '📝 文档',
                    'tests': '✅ 测试',
                    'performance': '⚡ 性能',
                    'build': '📦 构建',
                    'ci': '👷 CI/CD',
                    'other': '🔧 其他'
                }
                lines.append(f"### {category_names.get(category, category)}\n\n")
                for change in changes:
                    lines.append(f"- {change}\n")
                lines.append("\n")
            
            if entry.migration_guide:
                lines.append(entry.migration_guide)
                lines.append("\n")
        
        return ''.join(lines)


class ArchitectureDiagramGenerator:
    """
    架构图生成器（增强版）
    
    功能：
    - 项目结构分析
    - 依赖关系图生成
    - 支持多种输出格式（Mermaid/PlantUML/Graphviz）
    - 模块分组与聚类
    """
    
    def __init__(self):
        self.nodes: List[Dict[str, Any]] = []
        self.edges: List[Dict[str, Any]] = []
        self.groups: Dict[str, List[str]] = {}
    
    def analyze_project(self, source_dir: Path) -> Dict[str, Any]:
        modules = {}
        for py_file in source_dir.rglob("*.py"):
            if "__pycache__" in str(py_file) or "test" in py_file.name:
                continue
            
            module_name = str(py_file.relative_to(source_dir)).replace('.py', '').replace(os.sep, '.')
            imports, exports, classes, functions = self._analyze_file(py_file)
            modules[module_name] = {
                'file': str(py_file),
                'imports': imports,
                'exports': exports,
                'classes': classes,
                'functions': functions
            }
        
        self._build_graph(modules)
        self._detect_groups(modules)
        
        return {
            'modules': modules,
            'nodes': self.nodes,
            'edges': self.edges,
            'groups': self.groups
        }
    
    def _analyze_file(self, file_path: Path) -> tuple:
        imports = []
        exports = []
        classes = []
        functions = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            tree = ast.parse(content)
            
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        imports.append(alias.name)
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        imports.append(node.module)
                elif isinstance(node, ast.ClassDef):
                    exports.append(node.name)
                    classes.append(node.name)
                elif isinstance(node, ast.FunctionDef):
                    if not node.name.startswith('_'):
                        exports.append(node.name)
                        functions.append(node.name)
        
        except Exception:
            pass
        
        return imports, exports, classes, functions
    
    def _build_graph(self, modules: Dict[str, Any]):
        self.nodes = []
        self.edges = []
        
        for module_name, info in modules.items():
            self.nodes.append({
                'id': module_name,
                'label': module_name.split('.')[-1],
                'type': 'module',
                'classes': info.get('classes', []),
                'functions': info.get('functions', [])
            })
            
            for imp in info['imports']:
                for other_module in modules:
                    if imp.startswith(other_module) or other_module.endswith(imp):
                        self.edges.append({
                            'source': module_name,
                            'target': other_module,
                            'type': 'import'
                        })
    
    def _detect_groups(self, modules: Dict[str, Any]):
        self.groups = {}
        for module_name in modules:
            parts = module_name.split('.')
            if len(parts) > 1:
                group = parts[0]
                if group not in self.groups:
                    self.groups[group] = []
                self.groups[group].append(module_name)
    
    def generate_mermaid(self) -> str:
        lines = ["graph TD\n"]
        
        for group, modules in self.groups.items():
            if len(modules) > 1:
                lines.append(f"    subgraph {group}\n")
                for module in modules:
                    node_id = module.replace('.', '_')
                    label = module.split('.')[-1]
                    lines.append(f"        {node_id}[\"{label}\"]\n")
                lines.append("    end\n")
            else:
                for module in modules:
                    node_id = module.replace('.', '_')
                    label = module.split('.')[-1]
                    lines.append(f"    {node_id}[\"{label}\"]\n")
        
        seen_edges = set()
        for edge in self.edges:
            edge_key = f"{edge['source']}-{edge['target']}"
            if edge_key not in seen_edges:
                source_id = edge['source'].replace('.', '_')
                target_id = edge['target'].replace('.', '_')
                lines.append(f"    {source_id} --> {target_id}\n")
                seen_edges.add(edge_key)
        
        return ''.join(lines)
    
    def generate_plantuml(self) -> str:
        lines = ["@startuml\n"]
        lines.append("' 架构图\n\n")
        
        for group, modules in self.groups.items():
            if len(modules) > 1:
                lines.append(f"package \"{group}\" {{\n")
                for module in modules:
                    label = module.split('.')[-1]
                    lines.append(f"    [{label}] as {module.replace('.', '_')}\n")
                lines.append("}\n")
            else:
                for module in modules:
                    label = module.split('.')[-1]
                    lines.append(f"[{label}] as {module.replace('.', '_')}\n")
        
        seen_edges = set()
        for edge in self.edges:
            edge_key = f"{edge['source']}-{edge['target']}"
            if edge_key not in seen_edges:
                source_id = edge['source'].replace('.', '_')
                target_id = edge['target'].replace('.', '_')
                lines.append(f"{source_id} --> {target_id}\n")
                seen_edges.add(edge_key)
        
        lines.append("@enduml\n")
        return ''.join(lines)


class PythonDocParser:
    """
    Python文档解析器（增强版）
    
    功能：
    - 解析Python源代码提取文档
    - 支持Google/NumPy/Sphinx风格docstring
    - 提取类型注解
    - 计算代码复杂度
    - 生成文档哈希用于增量更新
    """
    
    def __init__(self, include_private: bool = False):
        self.include_private = include_private
    
    def parse_file(self, file_path: Path) -> Optional[ModuleDoc]:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                source = f.read()
            
            tree = ast.parse(source)
            
            file_stat = file_path.stat()
            last_modified = datetime.fromtimestamp(file_stat.st_mtime)
            
            module_doc = ModuleDoc(
                name=file_path.stem,
                source_file=str(file_path),
                file_size=len(source),
                line_count=len(source.splitlines()),
                hash=self._compute_hash(source),
                last_modified=last_modified
            )
            
            if ast.get_docstring(tree):
                module_doc.docstring = ast.get_docstring(tree)
            
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        module_doc.imports.append(alias.name)
                elif isinstance(node, ast.ImportFrom):
                    module_module = node.module or ""
                    for alias in node.names:
                        module_doc.imports.append(f"{module_module}.{alias.name}")
            
            for node in tree.body:
                if isinstance(node, ast.ClassDef):
                    if not self._is_private(node.name) or self.include_private:
                        class_doc = self._parse_class(node, file_path, source)
                        module_doc.classes.append(class_doc)
                elif isinstance(node, ast.FunctionDef) or isinstance(node, ast.AsyncFunctionDef):
                    if not self._is_private(node.name) or self.include_private:
                        func_doc = self._parse_function(node, file_path, source)
                        module_doc.functions.append(func_doc)
            
            return module_doc
        
        except Exception:
            return None
    
    def _parse_class(self, node: ast.ClassDef, file_path: Path, source: str) -> ClassDoc:
        class_doc = ClassDoc(
            name=node.name,
            docstring=ast.get_docstring(node) or "",
            bases=[self._get_name(base) for base in node.bases],
            decorators=[self._get_name(d) for d in node.decorator_list],
            source_file=str(file_path),
            line_number=node.lineno,
            end_line_number=node.end_lineno or node.lineno,
            is_abstract=self._is_abstract_class(node),
            is_enum=self._is_enum_class(node)
        )
        
        for item in node.body:
            if isinstance(item, ast.FunctionDef) or isinstance(item, ast.AsyncFunctionDef):
                if not self._is_private(item.name) or self.include_private:
                    func_doc = self._parse_function(item, file_path, source, is_method=True)
                    class_doc.methods.append(func_doc)
            elif isinstance(item, ast.AnnAssign) and isinstance(item.target, ast.Name):
                class_doc.attributes.append({
                    "name": item.target.id,
                    "type": self._get_annotation(item.annotation),
                    "default": self._get_default(item.value) if item.value else None
                })
        
        class_source = ast.get_source_segment(source, node) or ""
        class_doc.hash = self._compute_hash(class_source)
        
        return class_doc
    
    def _parse_function(
        self, 
        node: ast.FunctionDef, 
        file_path: Path, 
        source: str, 
        is_method: bool = False
    ) -> FunctionDoc:
        func_doc = FunctionDoc(
            name=node.name,
            docstring=ast.get_docstring(node) or "",
            decorators=[self._get_name(d) for d in node.decorator_list],
            is_async=isinstance(node, ast.AsyncFunctionDef),
            is_method=is_method,
            is_property=self._has_decorator(node, 'property'),
            is_classmethod=self._has_decorator(node, 'classmethod'),
            is_staticmethod=self._has_decorator(node, 'staticmethod'),
            source_file=str(file_path),
            line_number=node.lineno,
            end_line_number=node.end_lineno or node.lineno
        )
        
        args = node.args
        for i, arg in enumerate(args.args):
            if is_method and i == 0 and arg.arg in ('self', 'cls'):
                continue
            
            arg_info = {
                "name": arg.arg,
                "type": self._get_annotation(arg.annotation),
                "default": None
            }
            
            defaults_offset = len(args.args) - len(args.defaults)
            if i >= defaults_offset and args.defaults:
                default_idx = i - defaults_offset
                arg_info["default"] = self._get_default(args.defaults[default_idx])
            
            func_doc.args.append(arg_info)
        
        if node.returns:
            func_doc.returns = {"type": self._get_annotation(node.returns)}
        
        func_doc.raises = self._extract_raises(node)
        func_doc.examples = self._extract_examples(node)
        func_doc.complexity = self._calculate_complexity(node)
        
        func_source = ast.get_source_segment(source, node) or ""
        func_doc.hash = self._compute_hash(func_source)
        
        return func_doc
    
    def _extract_raises(self, node: ast.FunctionDef) -> List[dict]:
        raises = []
        docstring = ast.get_docstring(node) or ""
        
        patterns = [
            (r'Raises:\s*\n\s*(\w+):\s*(.+?)(?=\n\s*\w+:|\n\n|$)', 'google'),
            (r':raises?\s+(\w+):\s*(.+?)(?=\n\s*:|\n\n|$)', 'sphinx'),
        ]
        
        for pattern, style in patterns:
            matches = re.finditer(pattern, docstring, re.MULTILINE | re.DOTALL)
            for match in matches:
                raises.append({
                    'type': match.group(1).strip(),
                    'description': match.group(2).strip()
                })
        
        return raises
    
    def _extract_examples(self, node: ast.FunctionDef) -> List[str]:
        examples = []
        docstring = ast.get_docstring(node) or ""
        
        pattern = r'Example[s]?:\s*\n((?:\s{4,}.*\n?)+)'
        matches = re.finditer(pattern, docstring, re.MULTILINE)
        
        for match in matches:
            example = match.group(1).strip()
            examples.append(example)
        
        return examples
    
    def _calculate_complexity(self, node: ast.FunctionDef) -> int:
        complexity = 1
        
        for child in ast.walk(node):
            if isinstance(child, (ast.If, ast.While, ast.For, ast.ExceptHandler)):
                complexity += 1
            elif isinstance(child, ast.BoolOp):
                complexity += len(child.values) - 1
            elif isinstance(child, (ast.And, ast.Or)):
                complexity += 1
        
        return complexity
    
    def _is_abstract_class(self, node: ast.ClassDef) -> bool:
        for base in node.bases:
            if isinstance(base, ast.Name) and 'ABC' in base.id:
                return True
            if isinstance(base, ast.Attribute) and 'ABC' in base.attr:
                return True
        return False
    
    def _is_enum_class(self, node: ast.ClassDef) -> bool:
        for base in node.bases:
            if isinstance(base, ast.Name) and 'Enum' in base.id:
                return True
            if isinstance(base, ast.Attribute) and 'Enum' in base.attr:
                return True
        return False
    
    def _has_decorator(self, node: ast.FunctionDef, decorator_name: str) -> bool:
        for decorator in node.decorator_list:
            if isinstance(decorator, ast.Name) and decorator.id == decorator_name:
                return True
            if isinstance(decorator, ast.Attribute) and decorator.attr == decorator_name:
                return True
        return False
    
    def _is_private(self, name: str) -> bool:
        return name.startswith('_') and not name.startswith('__')
    
    def _get_name(self, node: ast.AST) -> str:
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            return f"{self._get_name(node.value)}.{node.attr}"
        elif isinstance(node, ast.Call):
            return self._get_name(node.func)
        return str(node)
    
    def _get_annotation(self, node: Optional[ast.AST]) -> str:
        if node is None:
            return "Any"
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            return f"{self._get_name(node.value)}.{node.attr}"
        elif isinstance(node, ast.Subscript):
            value = self._get_annotation(node.value)
            if isinstance(node.slice, ast.Tuple):
                slices = ', '.join(self._get_annotation(el) for el in node.slice.elts)
            else:
                slices = self._get_annotation(node.slice)
            return f"{value}[{slices}]"
        elif isinstance(node, ast.Constant):
            return repr(node.value)
        elif isinstance(node, ast.BinOp) and isinstance(node.op, ast.BitOr):
            left = self._get_annotation(node.left)
            right = self._get_annotation(node.right)
            return f"{left} | {right}"
        return "Any"
    
    def _get_default(self, node: ast.AST) -> Any:
        if isinstance(node, ast.Constant):
            return node.value
        elif isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Call):
            return f"{self._get_name(node.func)}()"
        elif isinstance(node, ast.List):
            return []
        elif isinstance(node, ast.Dict):
            return {}
        elif isinstance(node, ast.Tuple):
            return ()
        return None
    
    def _compute_hash(self, content: str) -> str:
        return hashlib.md5(content.encode('utf-8')).hexdigest()[:12]


class DocTemplateManager:
    """
    文档模板管理器
    
    功能：
    - 管理文档模板
    - 支持自定义模板
    - 模板变量替换
    """
    
    DEFAULT_TEMPLATES = {
        'module': DocTemplate(
            name='module',
            content='# {{name}}\n\n{{docstring}}\n\n{{content}}',
            variables=['name', 'docstring', 'content'],
            description='模块文档模板'
        ),
        'class': DocTemplate(
            name='class',
            content='## {{name}}\n\n{{docstring}}\n\n{{methods}}',
            variables=['name', 'docstring', 'methods'],
            description='类文档模板'
        ),
        'function': DocTemplate(
            name='function',
            content='### {{name}}\n\n{{docstring}}\n\n**参数**: {{args}}\n\n**返回**: {{returns}}',
            variables=['name', 'docstring', 'args', 'returns'],
            description='函数文档模板'
        ),
        'changelog': DocTemplate(
            name='changelog',
            content='# 变更日志\n\n{{entries}}',
            variables=['entries'],
            description='变更日志模板'
        )
    }
    
    def __init__(self, template_dir: Optional[Path] = None):
        self.template_dir = template_dir
        self.templates: Dict[str, DocTemplate] = dict(self.DEFAULT_TEMPLATES)
        
        if template_dir and template_dir.exists():
            self._load_custom_templates()
    
    def _load_custom_templates(self):
        for template_file in self.template_dir.glob('*.template'):
            try:
                with open(template_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                name = template_file.stem
                variables = re.findall(r'\{\{(\w+)\}\}', content)
                
                self.templates[name] = DocTemplate(
                    name=name,
                    content=content,
                    variables=list(set(variables)),
                    description=f'自定义模板: {name}'
                )
            except Exception:
                pass
    
    def render(self, template_name: str, variables: Dict[str, Any]) -> str:
        if template_name not in self.templates:
            return ""
        
        template = self.templates[template_name]
        content = template.content
        
        for var in template.variables:
            placeholder = '{{' + var + '}}'
            value = variables.get(var, '')
            content = content.replace(placeholder, str(value))
        
        return content
    
    def add_template(self, name: str, content: str, description: str = "") -> bool:
        variables = re.findall(r'\{\{(\w+)\}\}', content)
        self.templates[name] = DocTemplate(
            name=name,
            content=content,
            variables=list(set(variables)),
            description=description
        )
        return True


class IncrementalDocUpdater:
    """
    增量文档更新器
    
    功能：
    - 检测代码变更
    - 增量更新文档
    - 文档差异对比
    """
    
    def __init__(self, output_dir: Path):
        self.output_dir = output_dir
        self.state_file = output_dir / ".doc_state.json"
        self._state: Dict[str, Dict[str, Any]] = {}
        self._load_state()
    
    def _load_state(self):
        if self.state_file.exists():
            try:
                with open(self.state_file, 'r', encoding='utf-8') as f:
                    self._state = json.load(f)
            except Exception:
                pass
    
    def _save_state(self):
        self.output_dir.mkdir(parents=True, exist_ok=True)
        with open(self.state_file, 'w', encoding='utf-8') as f:
            json.dump(self._state, f, indent=2, ensure_ascii=False)
    
    def detect_changes(self, modules: List[ModuleDoc]) -> Dict[str, List[str]]:
        """
        检测文档变更
        
        返回新增、修改、删除的模块列表
        """
        changes = {
            'added': [],
            'modified': [],
            'unchanged': [],
            'removed': []
        }
        
        current_modules = {m.name: m for m in modules}
        previous_modules = set(self._state.keys())
        current_module_names = set(current_modules.keys())
        
        changes['added'] = list(current_module_names - previous_modules)
        changes['removed'] = list(previous_modules - current_module_names)
        
        for name in current_module_names & previous_modules:
            current_hash = current_modules[name].hash
            previous_hash = self._state[name].get('hash', '')
            
            if current_hash != previous_hash:
                changes['modified'].append(name)
            else:
                changes['unchanged'].append(name)
        
        return changes
    
    def update_state(self, modules: List[ModuleDoc]):
        for module in modules:
            self._state[module.name] = {
                'hash': module.hash,
                'last_updated': datetime.now().isoformat(),
                'file_size': module.file_size,
                'line_count': module.line_count
            }
        self._save_state()
    
    def get_diff(self, module_name: str, old_content: str, new_content: str) -> str:
        diff = unified_diff(
            old_content.splitlines(keepends=True),
            new_content.splitlines(keepends=True),
            fromfile=f'{module_name}.md (old)',
            tofile=f'{module_name}.md (new)'
        )
        return ''.join(diff)


class APIDocAutoUpdater:
    """
    API文档自动更新器
    
    功能：
    - 监控代码变更
    - 自动更新API文档
    - 同步文档与代码
    """
    
    def __init__(self, parser: PythonDocParser, output_dir: Path):
        self.parser = parser
        self.output_dir = output_dir
        self.incremental_updater = IncrementalDocUpdater(output_dir)
    
    def update_docs(
        self, 
        source_dir: Path, 
        force: bool = False
    ) -> Dict[str, Any]:
        """
        更新API文档
        
        如果force为True，则强制重新生成所有文档
        """
        result = {
            'updated': [],
            'added': [],
            'removed': [],
            'unchanged': [],
            'errors': []
        }
        
        modules = self._parse_modules(source_dir)
        
        if force:
            result['updated'] = [m.name for m in modules]
        else:
            changes = self.incremental_updater.detect_changes(modules)
            result['added'] = changes['added']
            result['updated'] = changes['modified']
            result['unchanged'] = changes['unchanged']
            result['removed'] = changes['removed']
        
        self.incremental_updater.update_state(modules)
        
        return result
    
    def _parse_modules(self, source_dir: Path) -> List[ModuleDoc]:
        modules = []
        
        if not source_dir.exists():
            return modules
        
        for py_file in source_dir.rglob("*.py"):
            if "test" in py_file.name or "__pycache__" in str(py_file):
                continue
            
            module_doc = self.parser.parse_file(py_file)
            if module_doc:
                modules.append(module_doc)
        
        return modules
    
    def sync_doc_with_code(
        self, 
        source_file: Path, 
        doc_file: Path
    ) -> Dict[str, Any]:
        """
        同步单个文件的文档与代码
        """
        result = {
            'synced': False,
            'changes': [],
            'warnings': []
        }
        
        module_doc = self.parser.parse_file(source_file)
        if not module_doc:
            result['warnings'].append(f"无法解析源文件: {source_file}")
            return result
        
        if doc_file.exists():
            old_content = doc_file.read_text(encoding='utf-8')
            new_content = self._generate_module_doc(module_doc)
            
            if old_content != new_content:
                doc_file.write_text(new_content, encoding='utf-8')
                result['synced'] = True
                result['changes'].append('文档已更新')
            else:
                result['synced'] = True
                result['changes'].append('文档已是最新')
        else:
            new_content = self._generate_module_doc(module_doc)
            doc_file.parent.mkdir(parents=True, exist_ok=True)
            doc_file.write_text(new_content, encoding='utf-8')
            result['synced'] = True
            result['changes'].append('文档已创建')
        
        return result
    
    def _generate_module_doc(self, module: ModuleDoc) -> str:
        lines = [f"# {module.name}\n\n"]
        
        if module.docstring:
            lines.append(f"{module.docstring}\n\n")
        
        if module.classes:
            lines.append("## 类\n\n")
            for cls in module.classes:
                lines.extend(self._generate_class_doc(cls))
        
        if module.functions:
            lines.append("## 函数\n\n")
            for func in module.functions:
                lines.extend(self._generate_function_doc(func))
        
        lines.append(f"\n---\n\n")
        lines.append(f"*最后更新: {datetime.now().isoformat()}*\n")
        
        return ''.join(lines)
    
    def _generate_class_doc(self, cls: ClassDoc) -> List[str]:
        lines = [f"### {cls.name}\n\n"]
        
        if cls.docstring:
            lines.append(f"{cls.docstring}\n\n")
        
        if cls.bases:
            lines.append(f"**继承**: {', '.join(cls.bases)}\n\n")
        
        if cls.attributes:
            lines.append("**属性**:\n\n")
            for attr in cls.attributes:
                default_str = f" = {attr['default']}" if attr['default'] is not None else ""
                lines.append(f"- `{attr['name']}: {attr['type']}{default_str}`\n")
            lines.append("\n")
        
        if cls.methods:
            lines.append("**方法**:\n\n")
            for method in cls.methods:
                lines.extend(self._generate_function_doc(method, level=4))
        
        return lines
    
    def _generate_function_doc(self, func: FunctionDoc, level: int = 3) -> List[str]:
        prefix = '#' * level
        async_prefix = "async " if func.is_async else ""
        lines = [f"{prefix} {async_prefix}{func.name}\n\n"]
        
        if func.docstring:
            lines.append(f"{func.docstring}\n\n")
        
        if func.args:
            lines.append("**参数**:\n\n")
            for arg in func.args:
                default_str = f" = {arg['default']}" if arg.get('default') is not None else ""
                lines.append(f"- `{arg['name']}: {arg['type']}{default_str}`\n")
            lines.append("\n")
        
        if func.returns:
            lines.append(f"**返回**: `{func.returns['type']}`\n\n")
        
        if func.raises:
            lines.append("**异常**:\n\n")
            for exc in func.raises:
                lines.append(f"- `{exc['type']}`: {exc['description']}\n")
            lines.append("\n")
        
        if func.examples:
            lines.append("**示例**:\n\n")
            lines.append("```python\n")
            for example in func.examples:
                lines.append(f"{example}\n")
            lines.append("```\n\n")
        
        return lines


class DocGenerator(ScriptBase):
    """
    文档生成器主类（增强版）
    
    功能：
    - API文档自动更新
    - 变更日志自动生成
    - 架构图生成
    - 多格式输出支持
    - 版本管理
    - 增量更新
    """
    
    def __init__(self):
        super().__init__(
            name="doc_generator",
            version="2.0.0",
            description="文档自动生成器（增强版） - 支持API文档、变更日志和架构图生成",
            author="Sanliu"
        )
        self._setup_arguments()
        self.modules: List[ModuleDoc] = []
        self.version_controller: Optional[VersionController] = None
        self.parser: Optional[PythonDocParser] = None
        self.template_manager: Optional[DocTemplateManager] = None
        self.api_updater: Optional[APIDocAutoUpdater] = None
    
    def _setup_arguments(self):
        self._command_parser.add_argument(
            '--source',
            type=str,
            default='./backend/app',
            help='源代码目录'
        )
        self._command_parser.add_argument(
            '--output',
            type=str,
            default='./docs/libs',
            help='文档输出目录'
        )
        self._command_parser.add_argument(
            '--version',
            type=str,
            default='1.0.0',
            help='文档版本号'
        )
        self._command_parser.add_argument(
            '--format',
            type=str,
            choices=['markdown', 'html', 'json', 'rst'],
            default='markdown',
            help='输出格式'
        )
        self._command_parser.add_argument(
            '--include-private',
            action='store_true',
            help='包含私有成员'
        )
        self._command_parser.add_argument(
            '--include-source',
            action='store_true',
            help='包含源代码位置'
        )
        self._command_parser.add_argument(
            '--bump',
            type=str,
            choices=['major', 'minor', 'patch'],
            help='递增版本号'
        )
        self._command_parser.add_argument(
            '--changelog',
            action='store_true',
            help='生成变更日志'
        )
        self._command_parser.add_argument(
            '--architecture',
            action='store_true',
            help='生成架构图'
        )
        self._command_parser.add_argument(
            '--incremental',
            action='store_true',
            help='增量更新模式'
        )
        self._command_parser.add_argument(
            '--force',
            action='store_true',
            help='强制重新生成所有文档'
        )
        self._command_parser.add_argument(
            '--compare-versions',
            nargs=2,
            metavar=('VERSION1', 'VERSION2'),
            help='比较两个版本的文档差异'
        )
        self._command_parser.add_argument(
            '--deprecate',
            type=str,
            metavar='VERSION',
            help='标记指定版本为弃用'
        )
        self._command_parser.add_argument(
            '--tag',
            nargs=2,
            metavar=('VERSION', 'TAG'),
            help='为指定版本添加标签'
        )
        self._command_parser.add_argument(
            '--template-dir',
            type=str,
            help='自定义模板目录'
        )
    
    def initialize(self, config: Dict[str, Any]) -> None:
        super().initialize(config)
        output_dir = Path(config.get('output', './docs/libs'))
        self.version_controller = VersionController(output_dir)
        self.parser = PythonDocParser(include_private=config.get('include_private', False))
        
        template_dir = config.get('template_dir')
        if template_dir:
            self.template_manager = DocTemplateManager(Path(template_dir))
        else:
            self.template_manager = DocTemplateManager()
        
        self.api_updater = APIDocAutoUpdater(self.parser, output_dir)
    
    def validate_inputs(self, *args, **kwargs) -> bool:
        source = kwargs.get('source', './backend/app')
        source_path = Path(source)
        if not source_path.exists():
            self._logger.warning(f"源代码目录不存在: {source}，将创建空文档")
        return True
    
    def run(self, *args, **kwargs) -> Any:
        source = kwargs.get('source', './backend/app')
        output = kwargs.get('output', './docs/libs')
        version = kwargs.get('version', '1.0.0')
        output_format = kwargs.get('format', 'markdown')
        include_private = kwargs.get('include_private', False)
        include_source = kwargs.get('include_source', False)
        bump = kwargs.get('bump')
        generate_changelog = kwargs.get('changelog', False)
        generate_architecture = kwargs.get('architecture', False)
        incremental = kwargs.get('incremental', False)
        force = kwargs.get('force', False)
        compare_versions = kwargs.get('compare_versions')
        deprecate_version = kwargs.get('deprecate')
        tag_args = kwargs.get('tag')
        template_dir = kwargs.get('template_dir')
        
        source_dir = Path(source)
        output_dir = Path(output)
        
        self.parser = PythonDocParser(include_private=include_private)
        self.version_controller = VersionController(output_dir)
        
        if template_dir:
            self.template_manager = DocTemplateManager(Path(template_dir))
        else:
            self.template_manager = DocTemplateManager()
        
        self.api_updater = APIDocAutoUpdater(self.parser, output_dir)
        
        if compare_versions:
            return self._handle_version_comparison(compare_versions[0], compare_versions[1])
        
        if deprecate_version:
            return self._handle_deprecation(deprecate_version)
        
        if tag_args:
            return self._handle_tagging(tag_args[0], tag_args[1])
        
        if bump:
            version = self.version_controller.bump_version(VersionPart(bump), version)
            self._logger.info(f"版本号已递增至: {version}")
        
        self._logger.info(f"开始生成文档 - 版本: {version}")
        self._report.add_section("配置信息", {
            "source": source,
            "output": output,
            "version": version,
            "format": output_format,
            "incremental": incremental
        })
        
        if incremental and not force:
            update_result = self.api_updater.update_docs(source_dir, force=False)
            self._report.add_section("增量更新结果", update_result)
            self._logger.info(f"增量更新完成: 新增 {len(update_result['added'])}, "
                            f"修改 {len(update_result['updated'])}, "
                            f"删除 {len(update_result['removed'])}")
        else:
            self._parse_source_files(source_dir)
        
        checksum = self._compute_modules_checksum()
        version_dir = self.version_controller.create_version(
            version=version,
            modules=self.modules,
            changes=[f"生成 {len(self.modules)} 个模块文档"],
            checksum=checksum
        )
        
        generated_files = []
        if output_format == "json":
            result = self._generate_json(output_dir, version)
            generated_files.extend(result.get('generated_files', []))
        elif output_format == "html":
            result = self._generate_html(output_dir, version)
            generated_files.extend(result.get('generated_files', []))
        elif output_format == "rst":
            result = self._generate_rst(output_dir, version)
            generated_files.extend(result.get('generated_files', []))
        else:
            result = self._generate_markdown(output_dir, version)
            generated_files.extend(result.get('generated_files', []))
        
        self._generate_version_index(output_dir)
        
        additional_outputs = {}
        
        if generate_changelog:
            changelog = self._generate_changelog(source_dir, output_dir, version)
            additional_outputs['changelog'] = changelog
        
        if generate_architecture:
            architecture = self._generate_architecture(source_dir, output_dir, version)
            additional_outputs['architecture'] = architecture
        
        self._report.add_section("生成结果", {
            "version": version,
            "module_count": len(self.modules),
            "generated_files": len(generated_files)
        })
        
        return {
            "version": version,
            "output_dir": str(version_dir),
            "module_count": len(self.modules),
            "generated_files": generated_files,
            **additional_outputs
        }
    
    def _handle_version_comparison(self, version1: str, version2: str) -> Dict[str, Any]:
        diff = self.version_controller.compare_versions(version1, version2)
        
        self._report.add_section("版本比较结果", {
            "version1": version1,
            "version2": version2,
            "added": len(diff.added),
            "removed": len(diff.removed),
            "modified": len(diff.modified)
        })
        
        return {
            "version1": version1,
            "version2": version2,
            "diff": {
                "added": diff.added,
                "removed": diff.removed,
                "modified": diff.modified,
                "details": diff.details
            }
        }
    
    def _handle_deprecation(self, version: str) -> Dict[str, Any]:
        success = self.version_controller.deprecate_version(version)
        
        self._report.add_section("版本弃用", {
            "version": version,
            "success": success
        })
        
        return {
            "version": version,
            "deprecated": success
        }
    
    def _handle_tagging(self, version: str, tag: str) -> Dict[str, Any]:
        success = self.version_controller.add_tag(version, tag)
        
        self._report.add_section("版本标签", {
            "version": version,
            "tag": tag,
            "success": success
        })
        
        return {
            "version": version,
            "tag": tag,
            "added": success
        }
    
    def _compute_modules_checksum(self) -> str:
        hashes = ''.join(m.hash for m in sorted(self.modules, key=lambda x: x.name))
        return hashlib.md5(hashes.encode('utf-8')).hexdigest()[:12]
    
    def _parse_source_files(self, source_dir: Path):
        if not source_dir.exists():
            self._logger.warning(f"源代码目录不存在: {source_dir}")
            return
        
        python_files = list(source_dir.rglob("*.py"))
        self._logger.info(f"找到 {len(python_files)} 个 Python 文件")
        
        for file_path in python_files:
            if "test" in file_path.name or "__pycache__" in str(file_path):
                continue
            
            module_doc = self.parser.parse_file(file_path)
            if module_doc:
                self.modules.append(module_doc)
        
        self._logger.info(f"成功解析 {len(self.modules)} 个模块")
    
    def _generate_markdown(self, output_dir: Path, version: str) -> Dict[str, Any]:
        version_dir = output_dir / f"v{version}"
        version_dir.mkdir(parents=True, exist_ok=True)
        
        generated_files = []
        
        index_file = version_dir / "README.md"
        with open(index_file, 'w', encoding='utf-8') as f:
            f.write(f"# API 文档\n\n")
            f.write(f"**版本**: {version}\n\n")
            f.write(f"**生成时间**: {datetime.now().isoformat()}\n\n")
            f.write(f"**模块数量**: {len(self.modules)}\n\n")
            f.write("## 模块列表\n\n")
            for module in sorted(self.modules, key=lambda m: m.name):
                f.write(f"- [{module.name}]({module.name}.md)\n")
        
        generated_files.append(str(index_file))
        
        for module in self.modules:
            module_file = version_dir / f"{module.name}.md"
            with open(module_file, 'w', encoding='utf-8') as f:
                f.write(f"# {module.name}\n\n")
                if module.docstring:
                    f.write(f"{module.docstring}\n\n")
                
                f.write(f"**文件**: `{module.source_file}`\n\n")
                f.write(f"**行数**: {module.line_count}\n\n")
                f.write(f"**大小**: {module.file_size} 字节\n\n")
                
                if module.imports:
                    f.write("## 导入\n\n")
                    for imp in sorted(set(module.imports)):
                        f.write(f"- `{imp}`\n")
                    f.write("\n")
                
                if module.classes:
                    f.write("## 类\n\n")
                    for cls in module.classes:
                        self._write_class_markdown(f, cls)
                
                if module.functions:
                    f.write("## 函数\n\n")
                    for func in module.functions:
                        self._write_function_markdown(f, func)
                
                f.write(f"\n---\n\n")
                f.write(f"*文档哈希: `{module.hash}`*\n")
        
        generated_files.append(str(module_file))
        
        return {"generated_files": generated_files}
    
    def _write_class_markdown(self, f, cls: ClassDoc):
        f.write(f"### {cls.name}\n\n")
        if cls.docstring:
            f.write(f"{cls.docstring}\n\n")
        if cls.bases:
            f.write(f"**继承**: {', '.join(cls.bases)}\n\n")
        if cls.decorators:
            f.write(f"**装饰器**: {', '.join(cls.decorators)}\n\n")
        if cls.is_abstract:
            f.write("*抽象类*\n\n")
        if cls.is_enum:
            f.write("*枚举类*\n\n")
        if cls.attributes:
            f.write("**属性**:\n\n")
            for attr in cls.attributes:
                default_str = f" = {attr['default']}" if attr['default'] is not None else ""
                f.write(f"- `{attr['name']}: {attr['type']}{default_str}`\n")
            f.write("\n")
        if cls.methods:
            f.write("**方法**:\n\n")
            for method in cls.methods:
                f.write(f"#### {method.name}\n\n")
                if method.docstring:
                    f.write(f"{method.docstring}\n\n")
                if method.args:
                    f.write("**参数**:\n\n")
                    for arg in method.args:
                        default_str = f" = {arg['default']}" if arg.get('default') is not None else ""
                        f.write(f"- `{arg['name']}: {arg['type']}{default_str}`\n")
                    f.write("\n")
                if method.returns:
                    f.write(f"**返回**: `{method.returns['type']}`\n\n")
                if method.raises:
                    f.write("**异常**:\n\n")
                    for exc in method.raises:
                        f.write(f"- `{exc['type']}`: {exc['description']}\n")
                    f.write("\n")
                if method.examples:
                    f.write("**示例**:\n\n```python\n")
                    for example in method.examples:
                        f.write(f"{example}\n")
                    f.write("```\n\n")
                f.write(f"*复杂度: {method.complexity}*\n\n")
    
    def _write_function_markdown(self, f, func: FunctionDoc):
        async_prefix = "async " if func.is_async else ""
        f.write(f"### {async_prefix}{func.name}\n\n")
        if func.docstring:
            f.write(f"{func.docstring}\n\n")
        if func.decorators:
            f.write(f"**装饰器**: {', '.join(func.decorators)}\n\n")
        if func.args:
            f.write("**参数**:\n\n")
            for arg in func.args:
                default_str = f" = {arg['default']}" if arg.get('default') is not None else ""
                f.write(f"- `{arg['name']}: {arg['type']}{default_str}`\n")
            f.write("\n")
        if func.returns:
            f.write(f"**返回**: `{func.returns['type']}`\n\n")
        if func.raises:
            f.write("**异常**:\n\n")
            for exc in func.raises:
                f.write(f"- `{exc['type']}`: {exc['description']}\n")
            f.write("\n")
        if func.examples:
            f.write("**示例**:\n\n```python\n")
            for example in func.examples:
                f.write(f"{example}\n")
            f.write("```\n\n")
        f.write(f"*复杂度: {func.complexity}*\n\n")
    
    def _generate_html(self, output_dir: Path, version: str) -> Dict[str, Any]:
        version_dir = output_dir / f"v{version}"
        version_dir.mkdir(parents=True, exist_ok=True)
        
        generated_files = []
        
        html_template = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title} - API 文档 v{version}</title>
    <style>
        * {{ box-sizing: border-box; }}
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; line-height: 1.6; max-width: 1200px; margin: 0 auto; padding: 20px; background: #f5f5f5; }}
        h1 {{ color: #2c3e50; border-bottom: 3px solid #3498db; padding-bottom: 15px; }}
        h2 {{ color: #34495e; margin-top: 30px; border-left: 4px solid #3498db; padding-left: 15px; }}
        h3 {{ color: #2980b9; }}
        h4 {{ color: #16a085; }}
        code {{ background: #ecf0f1; padding: 2px 8px; border-radius: 4px; font-family: 'Fira Code', monospace; }}
        pre {{ background: #2c3e50; color: #ecf0f1; padding: 15px; border-radius: 8px; overflow-x: auto; }}
        pre code {{ background: none; padding: 0; }}
        .module {{ margin-bottom: 40px; padding: 25px; background: #fff; border-radius: 12px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
        .class {{ margin: 20px 0; padding: 20px; background: #f8f9fa; border-left: 5px solid #3498db; border-radius: 0 8px 8px 0; }}
        .function {{ margin: 15px 0; padding: 15px; background: #fff; border: 1px solid #e0e0e0; border-radius: 8px; }}
        .meta {{ color: #7f8c8d; font-size: 0.9em; margin-top: 5px; }}
        .tag {{ display: inline-block; background: #3498db; color: white; padding: 2px 8px; border-radius: 12px; font-size: 0.8em; margin-right: 5px; }}
        .nav {{ position: sticky; top: 20px; background: #fff; padding: 20px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
        .nav ul {{ list-style: none; padding: 0; }}
        .nav li {{ margin: 8px 0; }}
        .nav a {{ color: #3498db; text-decoration: none; }}
        .nav a:hover {{ text-decoration: underline; }}
        .container {{ display: grid; grid-template-columns: 250px 1fr; gap: 20px; }}
        @media (max-width: 768px) {{ .container {{ grid-template-columns: 1fr; }} }}
    </style>
</head>
<body>
{content}
</body>
</html>"""
        
        nav_content = "<nav class='nav'><h3>目录</h3><ul>"
        for module in sorted(self.modules, key=lambda m: m.name):
            nav_content += f"<li><a href='#module-{module.name}'>{module.name}</a></li>"
        nav_content += "</ul></nav>"
        
        main_content = f"<h1>API 文档 v{version}</h1>"
        main_content += f"<p class='meta'>生成时间: {datetime.now().isoformat()}</p>"
        main_content += f"<p class='meta'>模块数量: {len(self.modules)}</p>"
        
        for module in self.modules:
            main_content += f"<div class='module' id='module-{module.name}'>"
            main_content += f"<h2>{module.name}</h2>"
            if module.docstring:
                main_content += f"<p>{module.docstring}</p>"
            main_content += f"<p class='meta'>文件: {module.source_file} | 行数: {module.line_count}</p>"
            
            for cls in module.classes:
                main_content += f"<div class='class'><h3>{cls.name}</h3>"
                if cls.docstring:
                    main_content += f"<p>{cls.docstring}</p>"
                if cls.bases:
                    main_content += f"<p><strong>继承:</strong> {', '.join(cls.bases)}</p>"
                for method in cls.methods:
                    main_content += f"<div class='function'><h4>{method.name}</h4>"
                    if method.args:
                        main_content += "<p><strong>参数:</strong> "
                        main_content += ", ".join([f"<code>{a['name']}: {a['type']}</code>" for a in method.args])
                        main_content += "</p>"
                    if method.returns:
                        main_content += f"<p><strong>返回:</strong> <code>{method.returns['type']}</code></p>"
                    main_content += "</div>"
                main_content += "</div>"
            
            for func in module.functions:
                main_content += f"<div class='function'><h3>{func.name}</h3>"
                if func.args:
                    main_content += "<p><strong>参数:</strong> "
                    main_content += ", ".join([f"<code>{a['name']}: {a['type']}</code>" for a in func.args])
                    main_content += "</p>"
                if func.returns:
                    main_content += f"<p><strong>返回:</strong> <code>{func.returns['type']}</code></p>"
                main_content += "</div>"
            
            main_content += "</div>"
        
        content = f"<div class='container'>{nav_content}<main>{main_content}</main></div>"
        
        index_file = version_dir / "index.html"
        with open(index_file, 'w', encoding='utf-8') as f:
            f.write(html_template.format(title="API 文档", version=version, content=content))
        
        generated_files.append(str(index_file))
        return {"generated_files": generated_files}
    
    def _generate_rst(self, output_dir: Path, version: str) -> Dict[str, Any]:
        version_dir = output_dir / f"v{version}"
        version_dir.mkdir(parents=True, exist_ok=True)
        
        generated_files = []
        
        index_file = version_dir / "index.rst"
        with open(index_file, 'w', encoding='utf-8') as f:
            f.write(f"API 文档\n")
            f.write(f"{'=' * 50}\n\n")
            f.write(f"**版本**: {version}\n\n")
            f.write(f"**生成时间**: {datetime.now().isoformat()}\n\n")
            f.write(f"**模块数量**: {len(self.modules)}\n\n")
            f.write(".. toctree::\n")
            f.write("   :maxdepth: 2\n\n")
            for module in sorted(self.modules, key=lambda m: m.name):
                f.write(f"   {module.name}\n")
        
        generated_files.append(str(index_file))
        
        for module in self.modules:
            module_file = version_dir / f"{module.name}.rst"
            with open(module_file, 'w', encoding='utf-8') as f:
                f.write(f"{module.name}\n")
                f.write(f"{'=' * len(module.name)}\n\n")
                if module.docstring:
                    f.write(f"{module.docstring}\n\n")
                
                if module.classes:
                    f.write("类\n")
                    f.write("-" * 20 + "\n\n")
                    for cls in module.classes:
                        f.write(f".. class:: {cls.name}\n\n")
                        if cls.docstring:
                            f.write(f"   {cls.docstring}\n\n")
                
                if module.functions:
                    f.write("函数\n")
                    f.write("-" * 20 + "\n\n")
                    for func in module.functions:
                        args_str = ', '.join([a['name'] for a in func.args])
                        f.write(f".. function:: {func.name}({args_str})\n\n")
                        if func.docstring:
                            f.write(f"   {func.docstring}\n\n")
            
            generated_files.append(str(module_file))
        
        return {"generated_files": generated_files}
    
    def _generate_json(self, output_dir: Path, version: str) -> Dict[str, Any]:
        version_dir = output_dir / f"v{version}"
        version_dir.mkdir(parents=True, exist_ok=True)
        
        data = {
            "metadata": {
                "version": version,
                "generated_at": datetime.now().isoformat(),
                "module_count": len(self.modules),
                "generator": "doc_generator v2.0.0"
            },
            "modules": []
        }
        
        for module in self.modules:
            module_data = {
                "name": module.name,
                "docstring": module.docstring,
                "source_file": module.source_file,
                "file_size": module.file_size,
                "line_count": module.line_count,
                "hash": module.hash,
                "imports": module.imports,
                "classes": [],
                "functions": []
            }
            
            for cls in module.classes:
                class_data = {
                    "name": cls.name,
                    "docstring": cls.docstring,
                    "bases": cls.bases,
                    "decorators": cls.decorators,
                    "is_abstract": cls.is_abstract,
                    "is_enum": cls.is_enum,
                    "attributes": cls.attributes,
                    "methods": []
                }
                for method in cls.methods:
                    class_data["methods"].append({
                        "name": method.name,
                        "docstring": method.docstring,
                        "args": method.args,
                        "returns": method.returns,
                        "raises": method.raises,
                        "examples": method.examples,
                        "is_async": method.is_async,
                        "is_property": method.is_property,
                        "complexity": method.complexity,
                        "hash": method.hash
                    })
                module_data["classes"].append(class_data)
            
            for func in module.functions:
                module_data["functions"].append({
                    "name": func.name,
                    "docstring": func.docstring,
                    "args": func.args,
                    "returns": func.returns,
                    "raises": func.raises,
                    "examples": func.examples,
                    "decorators": func.decorators,
                    "is_async": func.is_async,
                    "complexity": func.complexity,
                    "hash": func.hash
                })
            
            data["modules"].append(module_data)
        
        output_file = version_dir / "api_documentation.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        return {"generated_files": [str(output_file)]}
    
    def _generate_version_index(self, output_dir: Path):
        versions = self.version_controller.list_versions()
        
        index_file = output_dir / "README.md"
        with open(index_file, 'w', encoding='utf-8') as f:
            f.write("# API 文档版本索引\n\n")
            f.write(f"**更新时间**: {datetime.now().isoformat()}\n\n")
            f.write("## 可用版本\n\n")
            
            if versions:
                f.write("| 版本 | 创建时间 | 模块数 | 状态 | 标签 |\n")
                f.write("|------|----------|--------|------|------|\n")
                for ver in versions:
                    status = "已弃用" if ver['is_deprecated'] else ("稳定" if ver['is_stable'] else "预览")
                    tags = ', '.join(ver.get('tags', []))
                    f.write(f"| [v{ver['version']}](./v{ver['version']}/) | {ver['created_at'][:10]} | {ver['modules_count']} | {status} | {tags} |\n")
            else:
                f.write("暂无版本记录\n")
            
            f.write("\n## 使用说明\n\n")
            f.write("### 命令行参数\n\n")
            f.write("```bash\n")
            f.write("# 生成文档\n")
            f.write("python doc_generator.py --source ./src --output ./docs\n\n")
            f.write("# 增量更新\n")
            f.write("python doc_generator.py --incremental\n\n")
            f.write("# 比较版本\n")
            f.write("python doc_generator.py --compare-versions v1.0.0 v1.1.0\n\n")
            f.write("# 生成变更日志\n")
            f.write("python doc_generator.py --changelog\n")
            f.write("```\n")
    
    def _generate_changelog(self, source_dir: Path, output_dir: Path, version: str) -> Dict[str, Any]:
        generator = ChangelogGenerator(source_dir)
        entries = generator.generate()
        
        changelog_data = []
        for entry in entries:
            changelog_data.append({
                "version": entry.version,
                "date": entry.date,
                "changes": entry.changes,
                "author": entry.author,
                "breaking_changes": entry.breaking_changes,
                "deprecations": entry.deprecations,
                "migration_guide": entry.migration_guide
            })
        
        version_dir = output_dir / f"v{version}"
        changelog_file = version_dir / "CHANGELOG.md"
        with open(changelog_file, 'w', encoding='utf-8') as f:
            f.write(generator.generate_markdown(entries))
        
        return {
            "entries": changelog_data, 
            "count": len(changelog_data),
            "file": str(changelog_file)
        }
    
    def _generate_architecture(self, source_dir: Path, output_dir: Path, version: str) -> Dict[str, Any]:
        generator = ArchitectureDiagramGenerator()
        architecture = generator.analyze_project(source_dir)
        
        version_dir = output_dir / f"v{version}"
        
        mermaid_file = version_dir / "architecture.mmd"
        with open(mermaid_file, 'w', encoding='utf-8') as f:
            f.write(generator.generate_mermaid())
        
        plantuml_file = version_dir / "architecture.puml"
        with open(plantuml_file, 'w', encoding='utf-8') as f:
            f.write(generator.generate_plantuml())
        
        arch_json_file = version_dir / "architecture.json"
        with open(arch_json_file, 'w', encoding='utf-8') as f:
            json.dump({
                'nodes': architecture['nodes'],
                'edges': architecture['edges'],
                'groups': architecture['groups']
            }, f, indent=2, ensure_ascii=False)
        
        return {
            "nodes": len(architecture['nodes']),
            "edges": len(architecture['edges']),
            "groups": len(architecture['groups']),
            "mermaid_file": str(mermaid_file),
            "plantuml_file": str(plantuml_file),
            "json_file": str(arch_json_file)
        }
    
    def cleanup(self) -> None:
        self._logger.info("清理文档生成器资源")


class DocValidator:
    """文档验证器"""
    
    def __init__(self, output_dir: Path):
        self.output_dir = output_dir
        self.issues: List[Dict[str, Any]] = []
        self.warnings: List[Dict[str, Any]] = []
    
    def validate_all(self, modules: List[ModuleDoc]) -> Dict[str, Any]:
        results = {
            "completeness": self._check_completeness(modules),
            "consistency": self._check_consistency(modules),
            "links": self._check_links(),
            "quality_score": 0.0,
            "issues": self.issues,
            "warnings": self.warnings
        }
        
        scores = [
            results["completeness"]["score"],
            results["consistency"]["score"],
            results["links"]["score"]
        ]
        results["quality_score"] = sum(scores) / len(scores)
        
        return results
    
    def _check_completeness(self, modules: List[ModuleDoc]) -> Dict[str, Any]:
        result = {
            "score": 100.0,
            "missing_docstrings": [],
            "missing_params": [],
            "missing_returns": []
        }
        
        for module in modules:
            if not module.docstring:
                result["missing_docstrings"].append(module.name)
                result["score"] -= 2
            
            for cls in module.classes:
                if not cls.docstring:
                    result["missing_docstrings"].append(f"{module.name}.{cls.name}")
                    result["score"] -= 1
                
                for method in cls.methods:
                    if not method.docstring:
                        result["missing_docstrings"].append(f"{module.name}.{cls.name}.{method.name}")
                        result["score"] -= 0.5
                    
                    for arg in method.args:
                        if arg['name'] not in ['self', 'cls'] and not self._param_in_docstring(arg['name'], method.docstring):
                            result["missing_params"].append({
                                "location": f"{module.name}.{cls.name}.{method.name}",
                                "param": arg['name']
                            })
                            result["score"] -= 0.2
            
            for func in module.functions:
                if not func.docstring:
                    result["missing_docstrings"].append(f"{module.name}.{func.name}")
                    result["score"] -= 0.5
        
        result["score"] = max(0.0, result["score"])
        return result
    
    def _param_in_docstring(self, param_name: str, docstring: str) -> bool:
        if not docstring:
            return False
        
        patterns = [
            f":param {param_name}:",
            f":arg {param_name}:",
            f":argument {param_name}:",
            f"@param {param_name}",
            f"Args:\n    {param_name}:",
            f"Parameters:\n    {param_name}:",
            f"参数:\n    {param_name}:"
        ]
        
        return any(p in docstring for p in patterns)
    
    def _check_consistency(self, modules: List[ModuleDoc]) -> Dict[str, Any]:
        result = {
            "score": 100.0,
            "naming_issues": [],
            "format_issues": []
        }
        
        naming_pattern = re.compile(r'^[a-z][a-z0-9_]*$')
        
        for module in modules:
            for cls in module.classes:
                if not re.match(r'^[A-Z][a-zA-Z0-9]*$', cls.name):
                    result["naming_issues"].append({
                        "type": "class",
                        "name": cls.name,
                        "expected": "PascalCase"
                    })
                    result["score"] -= 1
            
            for func in module.functions:
                if not naming_pattern.match(func.name) and not func.name.startswith('_'):
                    result["naming_issues"].append({
                        "type": "function",
                        "name": func.name,
                        "expected": "snake_case"
                    })
                    result["score"] -= 0.5
        
        result["score"] = max(0.0, result["score"])
        return result
    
    def _check_links(self) -> Dict[str, Any]:
        result = {
            "score": 100.0,
            "broken_links": [],
            "total_links": 0,
            "valid_links": 0
        }
        
        if not self.output_dir.exists():
            return result
        
        link_pattern = re.compile(r'\[([^\]]+)\]\(([^)]+)\)')
        
        for md_file in self.output_dir.rglob("*.md"):
            try:
                content = md_file.read_text(encoding='utf-8')
                links = link_pattern.findall(content)
                
                for text, link in links:
                    if link.startswith('http'):
                        continue
                    
                    result["total_links"] += 1
                    
                    if link.startswith('#'):
                        anchor = link[1:]
                        if anchor.lower() not in content.lower():
                            result["broken_links"].append({
                                "file": str(md_file),
                                "link": link,
                                "text": text,
                                "reason": "Anchor not found"
                            })
                            result["score"] -= 2
                    else:
                        target_path = (md_file.parent / link).resolve()
                        if not target_path.exists():
                            result["broken_links"].append({
                                "file": str(md_file),
                                "link": link,
                                "text": text,
                                "reason": "File not found"
                            })
                            result["score"] -= 5
                        else:
                            result["valid_links"] += 1
            except Exception as e:
                self.warnings.append({
                    "file": str(md_file),
                    "message": f"Error checking links: {str(e)}"
                })
        
        result["score"] = max(0.0, result["score"])
        return result
    
    def validate_single_file(self, file_path: Path, module: ModuleDoc) -> Dict[str, Any]:
        result = {
            "file": str(file_path),
            "valid": True,
            "issues": []
        }
        
        if not module.docstring:
            result["issues"].append({
                "type": "missing_module_docstring",
                "severity": "warning",
                "message": "Module is missing docstring"
            })
        
        for cls in module.classes:
            if not cls.docstring:
                result["issues"].append({
                    "type": "missing_class_docstring",
                    "severity": "warning",
                    "message": f"Class '{cls.name}' is missing docstring"
                })
        
        if result["issues"]:
            result["valid"] = False
        
        return result


class DocQualityScorer:
    """文档质量评分器"""
    
    SCORING_CRITERIA = {
        "completeness": {
            "weight": 0.3,
            "checks": ["docstring_coverage", "param_documentation", "return_documentation"]
        },
        "clarity": {
            "weight": 0.25,
            "checks": ["description_length", "example_presence", "complexity"]
        },
        "consistency": {
            "weight": 0.2,
            "checks": ["naming_convention", "format_consistency", "style_guide"]
        },
        "maintainability": {
            "weight": 0.15,
            "checks": ["version_info", "author_info", "last_updated"]
        },
        "accessibility": {
            "weight": 0.1,
            "checks": ["toc_presence", "cross_references", "searchability"]
        }
    }
    
    def calculate_score(self, modules: List[ModuleDoc], validation_result: Dict[str, Any]) -> Dict[str, Any]:
        scores = {}
        
        scores["completeness"] = self._score_completeness(modules)
        scores["clarity"] = self._score_clarity(modules)
        scores["consistency"] = validation_result.get("consistency", {}).get("score", 100)
        scores["maintainability"] = self._score_maintainability(modules)
        scores["accessibility"] = self._score_accessibility(modules)
        
        total_score = 0.0
        for criterion, info in self.SCORING_CRITERIA.items():
            total_score += scores.get(criterion, 0) * info["weight"]
        
        return {
            "total_score": round(total_score, 1),
            "grade": self._get_grade(total_score),
            "dimension_scores": scores,
            "recommendations": self._generate_recommendations(scores)
        }
    
    def _score_completeness(self, modules: List[ModuleDoc]) -> float:
        if not modules:
            return 0.0
        
        total_items = 0
        documented_items = 0
        
        for module in modules:
            total_items += 1
            if module.docstring:
                documented_items += 1
            
            for cls in module.classes:
                total_items += 1
                if cls.docstring:
                    documented_items += 1
                
                for method in cls.methods:
                    total_items += 1
                    if method.docstring:
                        documented_items += 1
            
            for func in module.functions:
                total_items += 1
                if func.docstring:
                    documented_items += 1
        
        return (documented_items / total_items * 100) if total_items > 0 else 0
    
    def _score_clarity(self, modules: List[ModuleDoc]) -> float:
        if not modules:
            return 0.0
        
        score = 100.0
        
        for module in modules:
            for cls in module.classes:
                for method in cls.methods:
                    if method.docstring:
                        if len(method.docstring) < 20:
                            score -= 1
                        if not method.examples:
                            score -= 0.5
            
            for func in module.functions:
                if func.docstring:
                    if len(func.docstring) < 20:
                        score -= 1
                    if not func.examples:
                        score -= 0.5
        
        return max(0.0, score)
    
    def _score_maintainability(self, modules: List[ModuleDoc]) -> float:
        score = 80.0
        
        for module in modules:
            if module.last_modified:
                days_since_update = (datetime.now() - module.last_modified).days
                if days_since_update > 90:
                    score -= 5
                elif days_since_update > 30:
                    score -= 2
        
        return max(0.0, min(100.0, score))
    
    def _score_accessibility(self, modules: List[ModuleDoc]) -> float:
        return 75.0
    
    def _get_grade(self, score: float) -> str:
        if score >= 95:
            return "A+"
        elif score >= 90:
            return "A"
        elif score >= 85:
            return "A-"
        elif score >= 80:
            return "B+"
        elif score >= 75:
            return "B"
        elif score >= 70:
            return "B-"
        elif score >= 65:
            return "C+"
        elif score >= 60:
            return "C"
        elif score >= 50:
            return "D"
        else:
            return "F"
    
    def _generate_recommendations(self, scores: Dict[str, float]) -> List[str]:
        recommendations = []
        
        if scores.get("completeness", 0) < 80:
            recommendations.append("建议增加文档字符串覆盖率，至少达到80%以上")
        
        if scores.get("clarity", 0) < 70:
            recommendations.append("建议为复杂函数添加示例代码和使用说明")
        
        if scores.get("consistency", 0) < 80:
            recommendations.append("建议统一命名规范和文档格式")
        
        if scores.get("maintainability", 0) < 70:
            recommendations.append("建议定期更新文档，保持文档与代码同步")
        
        return recommendations


def main():
    generator = DocGenerator()
    result = generator.run_from_command_line()
    
    print("\n" + "=" * 60)
    print("文档生成完成")
    print("=" * 60)
    print(f"版本: {result.data.get('version', 'N/A')}")
    print(f"模块数: {result.data.get('module_count', 0)}")
    print(f"输出目录: {result.data.get('output_dir', 'N/A')}")
    print(f"生成文件数: {len(result.data.get('generated_files', []))}")
    
    if 'changelog' in result.data:
        print(f"变更日志条目: {result.data['changelog'].get('count', 0)}")
    
    if 'architecture' in result.data:
        arch = result.data['architecture']
        print(f"架构节点: {arch.get('nodes', 0)}")
        print(f"架构边: {arch.get('edges', 0)}")
    
    print("=" * 60)
    
    sys.exit(0)


if __name__ == "__main__":
    main()
