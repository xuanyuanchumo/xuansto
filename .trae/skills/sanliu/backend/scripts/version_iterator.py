#!/usr/bin/env python3
"""
版本迭代脚本 - 管理版本号，记录迭代历史，生成版本变更日志，支持版本回滚
支持语义化版本控制(SemVer)和自定义版本格式

增强功能:
- 完整的语义化版本管理 (SemVer 2.0.0)
- 版本约束解析与范围检查
- 自动变更日志生成 (Keep a Changelog)
- 版本历史追踪与统计
- 自迭代触发条件检测
- 版本兼容性检查
- 版本分支管理
- 版本文档自动生成
"""

import re
import json
import os
import sys
import shutil
import hashlib
import subprocess
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple, Set, Callable, Union
from dataclasses import dataclass, field, asdict
from enum import Enum
from collections import defaultdict
import argparse
import logging


class VersionBumpType(Enum):
    MAJOR = "major"
    MINOR = "minor"
    PATCH = "patch"
    PRERELEASE = "prerelease"
    BUILD = "build"


class ChangeType(Enum):
    FEATURE = "feat"
    FIX = "fix"
    DOCS = "docs"
    STYLE = "style"
    REFACTOR = "refactor"
    PERF = "perf"
    TEST = "test"
    CHORE = "chore"
    BREAKING = "breaking"
    SECURITY = "security"
    DEPRECATE = "deprecate"


class IterationTriggerType(Enum):
    ERROR_RATE = "error_rate"
    CONTINUOUS_FAILURE = "continuous_failure"
    PERFORMANCE_DEGRADATION = "performance_degradation"
    SECURITY_ALERT = "security_alert"
    CODE_QUALITY = "code_quality"
    SCHEDULED = "scheduled"
    MANUAL = "manual"
    TEST_FAILURE = "test_failure"
    DEPENDENCY_UPDATE = "dependency_update"


class VersionConstraintOperator(Enum):
    EXACT = "=="
    GREATER = ">"
    GREATER_EQUAL = ">="
    LESS = "<"
    LESS_EQUAL = "<="
    COMPATIBLE = "~="
    WILDCARD = "*"
    CARET = "^"


@dataclass
class VersionConstraint:
    operator: VersionConstraintOperator
    version: "VersionInfo"
    description: str = ""

    def matches(self, version: "VersionInfo") -> bool:
        if self.operator == VersionConstraintOperator.EXACT:
            return str(version) == str(self.version)
        elif self.operator == VersionConstraintOperator.GREATER:
            return self._compare(version, self.version) > 0
        elif self.operator == VersionConstraintOperator.GREATER_EQUAL:
            return self._compare(version, self.version) >= 0
        elif self.operator == VersionConstraintOperator.LESS:
            return self._compare(version, self.version) < 0
        elif self.operator == VersionConstraintOperator.LESS_EQUAL:
            return self._compare(version, self.version) <= 0
        elif self.operator == VersionConstraintOperator.COMPATIBLE:
            return (
                version.major == self.version.major and
                version.minor == self.version.minor and
                version.patch >= self.version.patch
            )
        elif self.operator == VersionConstraintOperator.CARET:
            if self.version.major > 0:
                return (
                    version.major == self.version.major and
                    self._compare(version, self.version) >= 0
                )
            else:
                return (
                    version.major == 0 and
                    version.minor == self.version.minor and
                    version.patch >= self.version.patch
                )
        elif self.operator == VersionConstraintOperator.WILDCARD:
            return True
        return False

    def _compare(self, v1: "VersionInfo", v2: "VersionInfo") -> int:
        if v1.major != v2.major:
            return 1 if v1.major > v2.major else -1
        if v1.minor != v2.minor:
            return 1 if v1.minor > v2.minor else -1
        if v1.patch != v2.patch:
            return 1 if v1.patch > v2.patch else -1
        return 0


@dataclass
class VersionRange:
    constraints: List[VersionConstraint]
    description: str = ""

    def matches(self, version: "VersionInfo") -> bool:
        return all(c.matches(version) for c in self.constraints)

    @classmethod
    def parse(cls, range_str: str) -> "VersionRange":
        constraints = []
        parts = range_str.split(",")
        
        for part in parts:
            part = part.strip()
            if not part:
                continue
            
            op = VersionConstraintOperator.EXACT
            version_str = part
            
            if part.startswith(">="):
                op = VersionConstraintOperator.GREATER_EQUAL
                version_str = part[2:].strip()
            elif part.startswith("<="):
                op = VersionConstraintOperator.LESS_EQUAL
                version_str = part[2:].strip()
            elif part.startswith("~="):
                op = VersionConstraintOperator.COMPATIBLE
                version_str = part[2:].strip()
            elif part.startswith("^"):
                op = VersionConstraintOperator.CARET
                version_str = part[1:].strip()
            elif part.startswith(">"):
                op = VersionConstraintOperator.GREATER
                version_str = part[1:].strip()
            elif part.startswith("<"):
                op = VersionConstraintOperator.LESS
                version_str = part[1:].strip()
            elif part.startswith("=="):
                op = VersionConstraintOperator.EXACT
                version_str = part[2:].strip()
            elif part == "*":
                op = VersionConstraintOperator.WILDCARD
                version_str = "0.0.0"
            
            if version_str and version_str != "0.0.0":
                version = VersionInfo.parse(version_str)
                constraints.append(VersionConstraint(operator=op, version=version))
        
        return cls(constraints=constraints, description=range_str)


@dataclass
class VersionBranch:
    branch_name: str
    base_version: str
    current_version: str
    created_at: str
    status: str = "active"
    description: str = ""
    merged_to: Optional[str] = None
    commits: List[str] = field(default_factory=list)


@dataclass
class VersionRelease:
    version: str
    release_type: str
    release_date: str
    release_notes: str
    artifacts: List[str] = field(default_factory=list)
    download_url: str = ""
    checksum: str = ""
    deprecated: bool = False
    deprecation_message: str = ""


@dataclass
class ChangeEntry:
    change_type: ChangeType
    description: str
    scope: str = ""
    breaking: bool = False
    issue_refs: List[str] = field(default_factory=list)
    author: str = ""
    timestamp: datetime = field(default_factory=datetime.now)
    commit_hash: str = ""
    file_paths: List[str] = field(default_factory=list)
    impact_level: str = "low"


@dataclass
class IterationTrigger:
    trigger_type: IterationTriggerType
    threshold: float
    current_value: float
    triggered: bool
    timestamp: datetime = field(default_factory=datetime.now)
    details: Dict[str, Any] = field(default_factory=dict)


@dataclass
class VersionCompatibility:
    version: str
    compatible_with: List[str]
    breaking_changes: List[str]
    migration_guide: str = ""
    deprecation_notices: List[str] = field(default_factory=list)


@dataclass
class VersionInfo:
    major: int
    minor: int
    patch: int
    prerelease: str = ""
    build_metadata: str = ""

    def __str__(self) -> str:
        version = f"{self.major}.{self.minor}.{self.patch}"
        if self.prerelease:
            version += f"-{self.prerelease}"
        if self.build_metadata:
            version += f"+{self.build_metadata}"
        return version

    @classmethod
    def parse(cls, version_str: str) -> "VersionInfo":
        """解析版本字符串"""
        pattern = r'^(\d+)\.(\d+)\.(\d+)(?:-([a-zA-Z0-9.-]+))?(?:\+([a-zA-Z0-9.-]+))?$'
        match = re.match(pattern, version_str)

        if not match:
            raise ValueError(f"无效的版本格式: {version_str}")

        major, minor, patch, prerelease, build = match.groups()
        return cls(
            major=int(major),
            minor=int(minor),
            patch=int(patch),
            prerelease=prerelease or "",
            build_metadata=build or ""
        )


@dataclass
class VersionEntry:
    version: str
    previous_version: str
    timestamp: str
    changes: List[ChangeEntry]
    author: str = ""
    commit_hash: str = ""
    tag_name: str = ""
    notes: str = ""
    release_type: str = "patch"
    stability: str = "stable"
    compatibility: Optional[VersionCompatibility] = None
    test_coverage: float = 0.0
    performance_metrics: Dict[str, float] = field(default_factory=dict)


@dataclass
class VersionHistory:
    project_name: str
    current_version: str
    versions: List[VersionEntry]
    iteration_count: int = 0
    total_changes: int = 0
    last_iteration_time: str = ""
    iteration_triggers: List[IterationTrigger] = field(default_factory=list)
    statistics: Dict[str, Any] = field(default_factory=dict)
    branches: List[VersionBranch] = field(default_factory=list)
    releases: List[VersionRelease] = field(default_factory=list)
    deprecations: Dict[str, str] = field(default_factory=dict)
    version_constraints: Dict[str, str] = field(default_factory=dict)


@dataclass
class VersionStatistics:
    total_versions: int
    major_versions: int
    minor_versions: int
    patch_versions: int
    prerelease_versions: int
    average_changes_per_version: float
    most_active_scope: str
    change_type_distribution: Dict[str, int]
    version_frequency: Dict[str, int]
    recent_velocity: float


class VersionManager:
    """版本管理器"""

    DEFAULT_VERSION_FILE = "version.json"
    DEFAULT_CHANGELOG_FILE = "CHANGELOG.md"
    DEFAULT_DOCS_DIR = "docs/libs"

    def __init__(self, project_root: str = ".", version_file: Optional[str] = None):
        self.project_root = Path(project_root).resolve()
        self.version_file = Path(version_file) if version_file else self.project_root / self.DEFAULT_VERSION_FILE
        self.changelog_file = self.project_root / self.DEFAULT_CHANGELOG_FILE
        self.docs_dir = self.project_root / self.DEFAULT_DOCS_DIR
        self.logger = self._setup_logger()
        self.history = self._load_history()

    def _setup_logger(self) -> logging.Logger:
        """设置日志记录器"""
        logger = logging.getLogger('VersionManager')
        logger.setLevel(logging.INFO)

        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)

        return logger

    def _load_history(self) -> VersionHistory:
        """加载版本历史"""
        if self.version_file.exists():
            try:
                with open(self.version_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                versions = []
                for v in data.get('versions', []):
                    changes = []
                    for c in v.get('changes', []):
                        changes.append(ChangeEntry(
                            change_type=ChangeType(c.get('type', 'chore')),
                            description=c.get('description', ''),
                            scope=c.get('scope', ''),
                            breaking=c.get('breaking', False),
                            issue_refs=c.get('issue_refs', []),
                            author=c.get('author', ''),
                            timestamp=datetime.fromisoformat(c.get('timestamp', datetime.now().isoformat()))
                        ))

                    versions.append(VersionEntry(
                        version=v.get('version', '0.0.0'),
                        previous_version=v.get('previous_version', ''),
                        timestamp=v.get('timestamp', ''),
                        changes=changes,
                        author=v.get('author', ''),
                        commit_hash=v.get('commit_hash', ''),
                        tag_name=v.get('tag_name', ''),
                        notes=v.get('notes', '')
                    ))

                return VersionHistory(
                    project_name=data.get('project_name', 'Unknown'),
                    current_version=data.get('current_version', '0.0.0'),
                    versions=versions,
                    iteration_count=data.get('iteration_count', 0)
                )

            except Exception as e:
                self.logger.error(f"加载版本历史失败: {e}")

        return VersionHistory(
            project_name=self.project_root.name,
            current_version="0.0.0",
            versions=[],
            iteration_count=0
        )

    def _save_history(self) -> None:
        """保存版本历史"""
        data = {
            "project_name": self.history.project_name,
            "current_version": self.history.current_version,
            "iteration_count": self.history.iteration_count,
            "versions": [
                {
                    "version": v.version,
                    "previous_version": v.previous_version,
                    "timestamp": v.timestamp,
                    "changes": [
                        {
                            "type": c.change_type.value,
                            "description": c.description,
                            "scope": c.scope,
                            "breaking": c.breaking,
                            "issue_refs": c.issue_refs,
                            "author": c.author,
                            "timestamp": c.timestamp.isoformat()
                        }
                        for c in v.changes
                    ],
                    "author": v.author,
                    "commit_hash": v.commit_hash,
                    "tag_name": v.tag_name,
                    "notes": v.notes
                }
                for v in self.history.versions
            ]
        }

        with open(self.version_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def get_current_version(self) -> VersionInfo:
        """获取当前版本"""
        return VersionInfo.parse(self.history.current_version)

    def bump_version(
        self,
        bump_type: VersionBumpType,
        prerelease_id: str = "",
        build_metadata: str = ""
    ) -> str:
        """升级版本号"""
        current = self.get_current_version()

        if bump_type == VersionBumpType.MAJOR:
            new_version = VersionInfo(
                major=current.major + 1,
                minor=0,
                patch=0,
                prerelease=prerelease_id,
                build_metadata=build_metadata
            )
        elif bump_type == VersionBumpType.MINOR:
            new_version = VersionInfo(
                major=current.major,
                minor=current.minor + 1,
                patch=0,
                prerelease=prerelease_id,
                build_metadata=build_metadata
            )
        elif bump_type == VersionBumpType.PATCH:
            new_version = VersionInfo(
                major=current.major,
                minor=current.minor,
                patch=current.patch + 1,
                prerelease=prerelease_id,
                build_metadata=build_metadata
            )
        elif bump_type == VersionBumpType.PRERELEASE:
            new_version = VersionInfo(
                major=current.major,
                minor=current.minor,
                patch=current.patch,
                prerelease=prerelease_id or f"alpha.{self._get_prerelease_number()}",
                build_metadata=build_metadata
            )
        elif bump_type == VersionBumpType.BUILD:
            new_version = VersionInfo(
                major=current.major,
                minor=current.minor,
                patch=current.patch,
                prerelease=current.prerelease,
                build_metadata=build_metadata or datetime.now().strftime('%Y%m%d%H%M%S')
            )
        else:
            raise ValueError(f"未知的版本升级类型: {bump_type}")

        return str(new_version)

    def _get_prerelease_number(self) -> int:
        """获取预发布版本号"""
        current = self.get_current_version()
        if current.prerelease and 'alpha' in current.prerelease:
            try:
                return int(current.prerelease.split('.')[-1]) + 1
            except ValueError:
                return 1
        return 1

    def create_version_entry(
        self,
        new_version: str,
        changes: List[ChangeEntry],
        author: str = "",
        notes: str = ""
    ) -> VersionEntry:
        """创建新版本条目"""
        previous_version = self.history.current_version

        commit_hash = self._get_git_commit_hash()
        tag_name = f"v{new_version}"

        entry = VersionEntry(
            version=new_version,
            previous_version=previous_version,
            timestamp=datetime.now().isoformat(),
            changes=changes,
            author=author or self._get_git_user(),
            commit_hash=commit_hash,
            tag_name=tag_name,
            notes=notes
        )

        self.history.versions.insert(0, entry)
        self.history.current_version = new_version
        self.history.iteration_count += 1

        self._save_history()

        return entry

    def _get_git_commit_hash(self) -> str:
        """获取Git提交哈希"""
        try:
            result = subprocess.run(
                ['git', 'rev-parse', '--short', 'HEAD'],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=5
            )
            return result.stdout.strip()
        except Exception:
            return ""

    def _get_git_user(self) -> str:
        """获取Git用户"""
        try:
            result = subprocess.run(
                ['git', 'config', 'user.name'],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=5
            )
            return result.stdout.strip()
        except Exception:
            return ""

    def rollback_version(self, target_version: Optional[str] = None) -> bool:
        """回滚到指定版本"""
        if not target_version:
            if len(self.history.versions) < 2:
                self.logger.error("没有可回滚的版本")
                return False
            target_version = self.history.versions[1].version

        for i, version in enumerate(self.history.versions):
            if version.version == target_version:
                self.history.current_version = target_version
                self.history.versions = self.history.versions[i:]
                self._save_history()
                self.logger.info(f"已回滚到版本: {target_version}")
                return True

        self.logger.error(f"未找到版本: {target_version}")
        return False

    def compare_versions(self, version1: str, version2: str) -> int:
        """比较两个版本号"""
        v1 = VersionInfo.parse(version1)
        v2 = VersionInfo.parse(version2)

        if v1.major != v2.major:
            return 1 if v1.major > v2.major else -1
        if v1.minor != v2.minor:
            return 1 if v1.minor > v2.minor else -1
        if v1.patch != v2.patch:
            return 1 if v1.patch > v2.patch else -1

        return 0

    def get_version_changes(self, version: str) -> List[ChangeEntry]:
        """获取指定版本的变更"""
        for v in self.history.versions:
            if v.version == version:
                return v.changes
        return []

    def get_changes_since(self, version: str) -> List[ChangeEntry]:
        """获取自指定版本以来的所有变更"""
        changes = []
        found = False

        for v in self.history.versions:
            if v.version == version:
                found = True
                break
            changes.extend(v.changes)

        return changes

    def calculate_statistics(self) -> VersionStatistics:
        """计算版本统计信息"""
        major_count = 0
        minor_count = 0
        patch_count = 0
        prerelease_count = 0
        total_changes = 0
        change_type_dist = defaultdict(int)
        scope_counts = defaultdict(int)
        version_freq = defaultdict(int)

        for version_entry in self.history.versions:
            v = VersionInfo.parse(version_entry.version)
            
            if v.prerelease:
                prerelease_count += 1
            elif version_entry.release_type == "major" or (v.major > 0 and v.minor == 0 and v.patch == 0):
                major_count += 1
            elif version_entry.release_type == "minor" or v.patch == 0:
                minor_count += 1
            else:
                patch_count += 1

            total_changes += len(version_entry.changes)

            for change in version_entry.changes:
                change_type_dist[change.change_type.value] += 1
                if change.scope:
                    scope_counts[change.scope] += 1

            month_key = version_entry.timestamp[:7]
            version_freq[month_key] += 1

        most_active_scope = max(scope_counts.items(), key=lambda x: x[1])[0] if scope_counts else ""

        avg_changes = total_changes / len(self.history.versions) if self.history.versions else 0

        recent_versions = [
            v for v in self.history.versions
            if datetime.fromisoformat(v.timestamp) > datetime.now() - timedelta(days=30)
        ]
        recent_velocity = len(recent_versions) / 4.0 if recent_versions else 0

        return VersionStatistics(
            total_versions=len(self.history.versions),
            major_versions=major_count,
            minor_versions=minor_count,
            patch_versions=patch_count,
            prerelease_versions=prerelease_count,
            average_changes_per_version=round(avg_changes, 2),
            most_active_scope=most_active_scope,
            change_type_distribution=dict(change_type_dist),
            version_frequency=dict(version_freq),
            recent_velocity=round(recent_velocity, 2)
        )

    def check_compatibility(self, version1: str, version2: str) -> Dict[str, Any]:
        """检查版本兼容性"""
        v1 = VersionInfo.parse(version1)
        v2 = VersionInfo.parse(version2)

        compatible = True
        issues = []

        if v1.major != v2.major:
            compatible = False
            issues.append(f"主版本号不同: {v1.major} vs {v2.major}")

        if v1.minor > v2.minor and v1.major == v2.major:
            issues.append(f"次版本号降级: {v1.minor} -> {v2.minor}")

        breaking_changes = []
        for version_entry in self.history.versions:
            v = VersionInfo.parse(version_entry.version)
            if self.compare_versions(version1, version_entry.version) < 0 and \
               self.compare_versions(version_entry.version, version2) <= 0:
                for change in version_entry.changes:
                    if change.breaking:
                        breaking_changes.append({
                            "version": version_entry.version,
                            "description": change.description
                        })

        return {
            "compatible": compatible,
            "version1": version1,
            "version2": version2,
            "issues": issues,
            "breaking_changes": breaking_changes
        }

    def get_version_timeline(self) -> List[Dict[str, Any]]:
        """获取版本时间线"""
        timeline = []
        for version_entry in reversed(self.history.versions):
            timeline.append({
                "version": version_entry.version,
                "timestamp": version_entry.timestamp,
                "author": version_entry.author,
                "change_count": len(version_entry.changes),
                "release_type": version_entry.release_type,
                "stability": version_entry.stability
            })
        return timeline

    def export_history(self, output_path: str, format: str = "json") -> str:
        """导出版本历史"""
        stats = self.calculate_statistics()
        
        if format == "json":
            data = {
                "project_name": self.history.project_name,
                "current_version": self.history.current_version,
                "statistics": asdict(stats),
                "timeline": self.get_version_timeline(),
                "versions": [
                    {
                        "version": v.version,
                        "timestamp": v.timestamp,
                        "changes": [
                            {
                                "type": c.change_type.value,
                                "description": c.description,
                                "scope": c.scope,
                                "breaking": c.breaking
                            }
                            for c in v.changes
                        ]
                    }
                    for v in self.history.versions
                ]
            }
            output = json.dumps(data, indent=2, ensure_ascii=False)
        else:
            output = self._generate_history_markdown(stats)

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(output)

        return output_path

    def _generate_history_markdown(self, stats: VersionStatistics) -> str:
        """生成历史Markdown报告"""
        lines = [
            f"# {self.history.project_name} 版本历史报告",
            "",
            f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "## 统计概览",
            "",
            f"- 当前版本: {self.history.current_version}",
            f"- 总版本数: {stats.total_versions}",
            f"- 主版本: {stats.major_versions}",
            f"- 次版本: {stats.minor_versions}",
            f"- 修订版本: {stats.patch_versions}",
            f"- 预发布版本: {stats.prerelease_versions}",
            f"- 平均每版本变更数: {stats.average_changes_per_version}",
            f"- 最近迭代速度: {stats.recent_velocity} 版本/周",
            "",
            "## 变更类型分布",
            "",
        ]

        for change_type, count in sorted(stats.change_type_distribution.items(), 
                                         key=lambda x: x[1], reverse=True):
            lines.append(f"- {change_type}: {count}")

        lines.extend(["", "## 版本时间线", ""])

        for entry in self.get_version_timeline()[:20]:
            lines.append(f"### {entry['version']} ({entry['timestamp'][:10]})")
            lines.append(f"- 作者: {entry['author']}")
            lines.append(f"- 变更数: {entry['change_count']}")
            lines.append(f"- 类型: {entry['release_type']}")
            lines.append("")

        return '\n'.join(lines)

    def check_version_constraint(self, version: str, constraint_str: str) -> bool:
        """检查版本是否满足约束条件"""
        try:
            version_info = VersionInfo.parse(version)
            version_range = VersionRange.parse(constraint_str)
            return version_range.matches(version_info)
        except Exception as e:
            self.logger.error(f"版本约束检查失败: {e}")
            return False

    def resolve_version_range(self, range_str: str) -> List[str]:
        """解析版本范围，返回满足条件的版本列表"""
        try:
            version_range = VersionRange.parse(range_str)
            matching_versions = []
            
            for version_entry in self.history.versions:
                version_info = VersionInfo.parse(version_entry.version)
                if version_range.matches(version_info):
                    matching_versions.append(version_entry.version)
            
            return matching_versions
        except Exception as e:
            self.logger.error(f"版本范围解析失败: {e}")
            return []

    def create_branch(
        self,
        branch_name: str,
        base_version: Optional[str] = None,
        description: str = ""
    ) -> VersionBranch:
        """创建版本分支"""
        base = base_version or self.history.current_version
        
        branch = VersionBranch(
            branch_name=branch_name,
            base_version=base,
            current_version=base,
            created_at=datetime.now().isoformat(),
            description=description
        )
        
        self.history.branches.append(branch)
        self._save_history()
        
        self.logger.info(f"创建版本分支: {branch_name} (基于 {base})")
        return branch

    def get_branch(self, branch_name: str) -> Optional[VersionBranch]:
        """获取版本分支"""
        for branch in self.history.branches:
            if branch.branch_name == branch_name:
                return branch
        return None

    def merge_branch(
        self,
        branch_name: str,
        target_branch: Optional[str] = None,
        bump_type: VersionBumpType = VersionBumpType.MINOR
    ) -> Optional[VersionEntry]:
        """合并版本分支"""
        branch = self.get_branch(branch_name)
        if not branch:
            self.logger.error(f"分支不存在: {branch_name}")
            return None
        
        changes = [
            ChangeEntry(
                change_type=ChangeType.FEATURE,
                description=f"合并分支 {branch_name}",
                scope="version"
            )
        ]
        
        entry = self.create_version_entry(
            new_version=self.bump_version(bump_type),
            changes=changes,
            notes=f"合并分支 {branch_name} (基于 {branch.base_version})"
        )
        
        branch.status = "merged"
        branch.merged_to = self.history.current_version
        self._save_history()
        
        self.logger.info(f"分支 {branch_name} 已合并到 {self.history.current_version}")
        return entry

    def create_release(
        self,
        version: str,
        release_type: str = "stable",
        release_notes: str = "",
        artifacts: Optional[List[str]] = None
    ) -> VersionRelease:
        """创建版本发布"""
        release = VersionRelease(
            version=version,
            release_type=release_type,
            release_date=datetime.now().strftime('%Y-%m-%d'),
            release_notes=release_notes,
            artifacts=artifacts or []
        )
        
        self.history.releases.append(release)
        self._save_history()
        
        self.logger.info(f"创建版本发布: {version}")
        return release

    def deprecate_version(self, version: str, message: str = "") -> bool:
        """标记版本为废弃"""
        for release in self.history.releases:
            if release.version == version:
                release.deprecated = True
                release.deprecation_message = message
                self.history.deprecations[version] = message
                self._save_history()
                self.logger.info(f"版本 {version} 已标记为废弃")
                return True
        
        self.history.deprecations[version] = message
        self._save_history()
        return True

    def get_latest_stable_version(self) -> Optional[str]:
        """获取最新稳定版本"""
        for release in self.history.releases:
            if release.release_type == "stable" and not release.deprecated:
                return release.version
        
        if self.history.versions:
            for version_entry in self.history.versions:
                if not VersionInfo.parse(version_entry.version).prerelease:
                    return version_entry.version
        
        return self.history.current_version

    def generate_version_documentation(self, version: str, output_dir: Optional[str] = None) -> str:
        """生成版本文档"""
        version_entry = None
        for v in self.history.versions:
            if v.version == version:
                version_entry = v
                break
        
        if not version_entry:
            return f"版本 {version} 未找到"
        
        docs_path = Path(output_dir) if output_dir else self.docs_dir / version
        docs_path.mkdir(parents=True, exist_ok=True)
        
        doc_content = self._generate_version_doc_content(version_entry)
        doc_file = docs_path / "README.md"
        
        with open(doc_file, 'w', encoding='utf-8') as f:
            f.write(doc_content)
        
        changes_file = docs_path / "CHANGES.md"
        self._generate_changes_doc(version_entry, changes_file)
        
        self.logger.info(f"版本文档已生成: {docs_path}")
        return str(docs_path)

    def _generate_version_doc_content(self, version_entry: VersionEntry) -> str:
        """生成版本文档内容"""
        lines = [
            f"# {self.history.project_name} v{version_entry.version}",
            "",
            f"**发布日期**: {version_entry.timestamp[:10]}",
            f"**作者**: {version_entry.author or 'N/A'}",
            f"**提交**: {version_entry.commit_hash or 'N/A'}",
            "",
        ]
        
        if version_entry.notes:
            lines.extend([
                "## 发布说明",
                "",
                version_entry.notes,
                "",
            ])
        
        lines.extend([
            "## 变更列表",
            "",
        ])
        
        for change in version_entry.changes:
            scope = f"[{change.scope}] " if change.scope else ""
            breaking = "⚠️ " if change.breaking else ""
            lines.append(f"- {breaking}{scope}{change.description}")
        
        if version_entry.previous_version:
            lines.extend([
                "",
                f"## 上一版本",
                "",
                f"[v{version_entry.previous_version}](../{version_entry.previous_version}/)",
            ])
        
        return '\n'.join(lines)

    def _generate_changes_doc(self, version_entry: VersionEntry, output_file: Path) -> None:
        """生成变更文档"""
        lines = [
            f"# v{version_entry.version} 变更详情",
            "",
            f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "",
        ]
        
        changes_by_type = defaultdict(list)
        for change in version_entry.changes:
            changes_by_type[change.change_type].append(change)
        
        type_names = {
            ChangeType.FEATURE: "新功能",
            ChangeType.FIX: "修复",
            ChangeType.REFACTOR: "重构",
            ChangeType.PERF: "性能优化",
            ChangeType.DOCS: "文档",
            ChangeType.TEST: "测试",
            ChangeType.CHORE: "其他",
            ChangeType.BREAKING: "重大变更",
            ChangeType.SECURITY: "安全",
            ChangeType.DEPRECATE: "废弃",
            ChangeType.STYLE: "风格",
        }
        
        for change_type, changes in changes_by_type.items():
            type_name = type_names.get(change_type, change_type.value)
            lines.append(f"## {type_name}")
            lines.append("")
            
            for change in changes:
                lines.append(f"### {change.description}")
                lines.append("")
                if change.scope:
                    lines.append(f"- **范围**: {change.scope}")
                if change.breaking:
                    lines.append("- **重大变更**: 是")
                if change.issue_refs:
                    lines.append(f"- **相关问题**: {', '.join(change.issue_refs)}")
                if change.author:
                    lines.append(f"- **作者**: {change.author}")
                lines.append("")
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines))

    def suggest_next_version(self, changes: List[ChangeEntry]) -> Tuple[str, VersionBumpType]:
        """根据变更建议下一个版本号"""
        has_breaking = any(c.breaking or c.change_type == ChangeType.BREAKING for c in changes)
        has_feature = any(c.change_type == ChangeType.FEATURE for c in changes)
        has_security = any(c.change_type == ChangeType.SECURITY for c in changes)
        has_fix = any(c.change_type == ChangeType.FIX for c in changes)
        
        if has_breaking:
            bump_type = VersionBumpType.MAJOR
        elif has_feature:
            bump_type = VersionBumpType.MINOR
        else:
            bump_type = VersionBumpType.PATCH
        
        next_version = self.bump_version(bump_type)
        return next_version, bump_type


class IterationTriggerDetector:
    """自迭代触发条件检测器"""

    DEFAULT_THRESHOLDS = {
        IterationTriggerType.ERROR_RATE: 0.05,
        IterationTriggerType.CONTINUOUS_FAILURE: 3,
        IterationTriggerType.PERFORMANCE_DEGRADATION: 0.5,
        IterationTriggerType.SECURITY_ALERT: 1,
        IterationTriggerType.CODE_QUALITY: 0.7,
        IterationTriggerType.TEST_FAILURE: 0.1,
        IterationTriggerType.DEPENDENCY_UPDATE: 1,
    }

    def __init__(self, version_manager: VersionManager, thresholds: Optional[Dict[IterationTriggerType, float]] = None):
        self.vm = version_manager
        self.thresholds = thresholds or self.DEFAULT_THRESHOLDS.copy()
        self.logger = logging.getLogger('IterationTriggerDetector')

    def check_all_triggers(self, metrics: Dict[str, Any]) -> List[IterationTrigger]:
        """检查所有触发条件"""
        triggers = []

        triggers.append(self._check_error_rate(metrics.get('error_rate', 0)))
        triggers.append(self._check_continuous_failure(metrics.get('continuous_failures', 0)))
        triggers.append(self._check_performance(metrics.get('performance_baseline', {}), 
                                                metrics.get('current_performance', {})))
        triggers.append(self._check_security(metrics.get('security_alerts', [])))
        triggers.append(self._check_code_quality(metrics.get('code_quality_score', 1.0)))
        triggers.append(self._check_test_failure(metrics.get('test_failure_rate', 0)))
        triggers.append(self._check_dependency_update(metrics.get('dependency_updates', [])))

        return [t for t in triggers if t.triggered]

    def _check_error_rate(self, error_rate: float) -> IterationTrigger:
        """检查错误率"""
        threshold = self.thresholds[IterationTriggerType.ERROR_RATE]
        triggered = error_rate > threshold

        return IterationTrigger(
            trigger_type=IterationTriggerType.ERROR_RATE,
            threshold=threshold,
            current_value=error_rate,
            triggered=triggered,
            details={"message": f"错误率 {error_rate:.2%} {'超过' if triggered else '未超过'} 阈值 {threshold:.2%}"}
        )

    def _check_continuous_failure(self, failure_count: int) -> IterationTrigger:
        """检查连续失败次数"""
        threshold = self.thresholds[IterationTriggerType.CONTINUOUS_FAILURE]
        triggered = failure_count >= threshold

        return IterationTrigger(
            trigger_type=IterationTriggerType.CONTINUOUS_FAILURE,
            threshold=threshold,
            current_value=float(failure_count),
            triggered=triggered,
            details={"message": f"连续失败 {failure_count} 次 {'达到' if triggered else '未达到'} 阈值 {threshold}"}
        )

    def _check_performance(self, baseline: Dict[str, float], 
                          current: Dict[str, float]) -> IterationTrigger:
        """检查性能下降"""
        threshold = self.thresholds[IterationTriggerType.PERFORMANCE_DEGRADATION]
        degradation = 0.0
        details = {}

        if baseline and current:
            for key in baseline:
                if key in current and baseline[key] > 0:
                    ratio = (current[key] - baseline[key]) / baseline[key]
                    if ratio > degradation:
                        degradation = ratio
                        details["metric"] = key
                        details["baseline"] = baseline[key]
                        details["current"] = current[key]

        triggered = degradation > threshold

        return IterationTrigger(
            trigger_type=IterationTriggerType.PERFORMANCE_DEGRADATION,
            threshold=threshold,
            current_value=degradation,
            triggered=triggered,
            details=details
        )

    def _check_security(self, alerts: List[Dict[str, Any]]) -> IterationTrigger:
        """检查安全警告"""
        threshold = self.thresholds[IterationTriggerType.SECURITY_ALERT]
        alert_count = len(alerts)
        triggered = alert_count >= threshold

        return IterationTrigger(
            trigger_type=IterationTriggerType.SECURITY_ALERT,
            threshold=threshold,
            current_value=float(alert_count),
            triggered=triggered,
            details={"alerts": alerts}
        )

    def _check_code_quality(self, quality_score: float) -> IterationTrigger:
        """检查代码质量"""
        threshold = self.thresholds[IterationTriggerType.CODE_QUALITY]
        triggered = quality_score < threshold

        return IterationTrigger(
            trigger_type=IterationTriggerType.CODE_QUALITY,
            threshold=threshold,
            current_value=quality_score,
            triggered=triggered,
            details={"message": f"代码质量分数 {quality_score:.2f} {'低于' if triggered else '高于'} 阈值 {threshold:.2f}"}
        )

    def _check_test_failure(self, failure_rate: float) -> IterationTrigger:
        """检查测试失败率"""
        threshold = self.thresholds[IterationTriggerType.TEST_FAILURE]
        triggered = failure_rate > threshold

        return IterationTrigger(
            trigger_type=IterationTriggerType.TEST_FAILURE,
            threshold=threshold,
            current_value=failure_rate,
            triggered=triggered,
            details={"message": f"测试失败率 {failure_rate:.2%} {'超过' if triggered else '未超过'} 阈值 {threshold:.2%}"}
        )

    def _check_dependency_update(self, updates: List[Dict[str, Any]]) -> IterationTrigger:
        """检查依赖更新"""
        threshold = self.thresholds[IterationTriggerType.DEPENDENCY_UPDATE]
        update_count = len(updates)
        triggered = update_count >= threshold

        return IterationTrigger(
            trigger_type=IterationTriggerType.DEPENDENCY_UPDATE,
            threshold=threshold,
            current_value=float(update_count),
            triggered=triggered,
            details={"updates": updates, "message": f"发现 {update_count} 个依赖更新"}
        )

    def determine_bump_type(self, triggers: List[IterationTrigger]) -> VersionBumpType:
        """根据触发条件确定版本升级类型"""
        trigger_types = {t.trigger_type for t in triggers}

        if IterationTriggerType.SECURITY_ALERT in trigger_types:
            return VersionBumpType.PATCH

        if IterationTriggerType.CONTINUOUS_FAILURE in trigger_types:
            return VersionBumpType.PATCH

        if IterationTriggerType.ERROR_RATE in trigger_types:
            return VersionBumpType.PATCH

        if IterationTriggerType.TEST_FAILURE in trigger_types:
            return VersionBumpType.PATCH

        if IterationTriggerType.PERFORMANCE_DEGRADATION in trigger_types:
            return VersionBumpType.MINOR

        if IterationTriggerType.CODE_QUALITY in trigger_types:
            return VersionBumpType.MINOR

        if IterationTriggerType.DEPENDENCY_UPDATE in trigger_types:
            return VersionBumpType.PATCH

        return VersionBumpType.PATCH

    def generate_trigger_report(self, triggers: List[IterationTrigger]) -> str:
        """生成触发条件报告"""
        lines = [
            "# 自迭代触发条件检测报告",
            "",
            f"检测时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "## 触发条件状态",
            "",
        ]

        for trigger in triggers:
            status = "✅ 触发" if trigger.triggered else "❌ 未触发"
            lines.append(f"### {trigger.trigger_type.value}")
            lines.append(f"- 状态: {status}")
            lines.append(f"- 阈值: {trigger.threshold}")
            lines.append(f"- 当前值: {trigger.current_value}")
            if trigger.details:
                lines.append(f"- 详情: {trigger.details.get('message', '')}")
            lines.append("")

        if any(t.triggered for t in triggers):
            lines.extend([
                "## 建议操作",
                "",
                f"- 建议版本升级类型: {self.determine_bump_type(triggers).value}",
                "- 建议执行自迭代流程",
            ])

        return '\n'.join(lines)


class ChangelogGenerator:
    """变更日志生成器"""

    def __init__(self, version_manager: VersionManager):
        self.vm = version_manager

    def generate(
        self,
        output_format: str = "markdown",
        include_unreleased: bool = True,
        detail_level: str = "normal"
    ) -> str:
        """生成变更日志"""
        if output_format == "json":
            return self._generate_json()
        return self._generate_markdown(include_unreleased, detail_level)

    def _generate_markdown(self, include_unreleased: bool = True, detail_level: str = "normal") -> str:
        """生成Markdown格式变更日志"""
        lines = [
            f"# {self.vm.history.project_name} 变更日志",
            "",
            "所有显著变更都将记录在此文件中。",
            "",
            "格式基于 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.0.0/)，",
            "并且本项目遵循 [语义化版本](https://semver.org/lang/zh-CN/)。",
            "",
        ]

        if include_unreleased:
            unreleased_changes = self._get_unreleased_changes()
            if unreleased_changes:
                lines.extend([
                    "## [未发布]",
                    "",
                ])
                lines.extend(self._format_changes_by_type(unreleased_changes, detail_level))
                lines.append("")

        for version in self.vm.history.versions:
            lines.extend([
                f"## [{version.version}] - {version.timestamp[:10]}",
                "",
            ])

            if version.notes:
                lines.extend([version.notes, ""])

            if version.changes:
                lines.extend(self._format_changes_by_type(version.changes, detail_level))
            else:
                lines.extend(["- 无显著变更", ""])

            if detail_level == "detailed":
                lines.extend(self._generate_version_details(version))

            lines.append("")

        lines.extend([
            "---",
            "",
            "## 版本历史",
            "",
        ])

        for version in self.vm.history.versions:
            compare_url = f"{version.previous_version}...{version.version}" if version.previous_version else f"...{version.version}"
            lines.append(f"- [{version.version}]: {compare_url}")

        return '\n'.join(lines)

    def _generate_version_details(self, version: VersionEntry) -> List[str]:
        """生成版本详细信息"""
        details = []
        
        if version.author:
            details.append(f"**作者**: {version.author}")
        
        if version.commit_hash:
            details.append(f"**提交**: {version.commit_hash}")
        
        if version.tag_name:
            details.append(f"**标签**: {version.tag_name}")
        
        breaking_changes = [c for c in version.changes if c.breaking]
        if breaking_changes:
            details.append("")
            details.append("**⚠️ 重大变更详情**:")
            for change in breaking_changes:
                details.append(f"- {change.description}")
                if change.issue_refs:
                    details.append(f"  相关问题: {', '.join(change.issue_refs)}")
        
        if details:
            return ["", "### 版本详情", ""] + details + [""]
        return []

    def _generate_json(self) -> str:
        """生成JSON格式变更日志"""
        data = {
            "project": self.vm.history.project_name,
            "current_version": self.vm.history.current_version,
            "versions": [
                {
                    "version": v.version,
                    "date": v.timestamp[:10],
                    "author": v.author,
                    "commit_hash": v.commit_hash,
                    "tag_name": v.tag_name,
                    "notes": v.notes,
                    "changes": [
                        {
                            "type": c.change_type.value,
                            "description": c.description,
                            "scope": c.scope,
                            "breaking": c.breaking,
                            "issue_refs": c.issue_refs,
                            "author": c.author
                        }
                        for c in v.changes
                    ]
                }
                for v in self.vm.history.versions
            ]
        }

        return json.dumps(data, indent=2, ensure_ascii=False)

    def _get_unreleased_changes(self) -> List[ChangeEntry]:
        """获取未发布的变更"""
        try:
            result = subprocess.run(
                ['git', 'log', f'{self.vm.history.current_version}..HEAD', '--pretty=format:%s'],
                cwd=self.vm.project_root,
                capture_output=True,
                text=True,
                timeout=10
            )

            changes = []
            for line in result.stdout.strip().split('\n'):
                if line:
                    change = self._parse_commit_message(line)
                    if change:
                        changes.append(change)

            return changes

        except Exception:
            return []

    def _parse_commit_message(self, message: str) -> Optional[ChangeEntry]:
        """解析提交信息"""
        pattern = r'^(\w+)(?:\(([^)]+)\))?:\s*(.+)$'
        match = re.match(pattern, message)

        if match:
            change_type_str, scope, description = match.groups()

            change_type_map = {
                'feat': ChangeType.FEATURE,
                'fix': ChangeType.FIX,
                'docs': ChangeType.DOCS,
                'style': ChangeType.STYLE,
                'refactor': ChangeType.REFACTOR,
                'perf': ChangeType.PERF,
                'test': ChangeType.TEST,
                'chore': ChangeType.CHORE,
            }

            change_type = change_type_map.get(change_type_str, ChangeType.CHORE)
            breaking = '!' in message or 'BREAKING CHANGE' in message

            return ChangeEntry(
                change_type=change_type,
                description=description,
                scope=scope or "",
                breaking=breaking
            )

        return None

    def _format_changes_by_type(self, changes: List[ChangeEntry], detail_level: str = "normal") -> List[str]:
        """按类型格式化变更"""
        grouped = defaultdict(list)

        for change in changes:
            grouped[change.change_type].append(change)

        type_titles = {
            ChangeType.BREAKING: "### ⚠️ 重大变更",
            ChangeType.FEATURE: "### ✨ 新功能",
            ChangeType.FIX: "### 🐛 Bug修复",
            ChangeType.PERF: "### ⚡ 性能优化",
            ChangeType.REFACTOR: "### ♻️ 代码重构",
            ChangeType.DOCS: "### 📝 文档",
            ChangeType.STYLE: "### 💄 代码风格",
            ChangeType.TEST: "### ✅ 测试",
            ChangeType.CHORE: "### 🔧 其他",
        }

        lines = []
        for change_type in ChangeType:
            if change_type in grouped:
                lines.append(type_titles.get(change_type, f"### {change_type.value}"))
                lines.append("")

                for change in grouped[change_type]:
                    scope = f"**{change.scope}**: " if change.scope else ""
                    breaking_marker = " 💥" if change.breaking else ""
                    
                    if detail_level == "detailed" and change.issue_refs:
                        issues = f" (refs: {', '.join(change.issue_refs)})"
                    else:
                        issues = ""
                    
                    lines.append(f"- {scope}{change.description}{breaking_marker}{issues}")

                lines.append("")

        return lines

    def save(self, output_path: Optional[str] = None) -> str:
        """保存变更日志"""
        path = Path(output_path) if output_path else self.vm.changelog_file

        changelog = self.generate()

        with open(path, 'w', encoding='utf-8') as f:
            f.write(changelog)

        return str(path)

    def generate_release_notes(self, version: str) -> str:
        """生成特定版本的发布说明"""
        version_entry = None
        for v in self.vm.history.versions:
            if v.version == version:
                version_entry = v
                break
        
        if not version_entry:
            return f"版本 {version} 未找到"
        
        lines = [
            f"# {self.vm.history.project_name} v{version} 发布说明",
            "",
            f"**发布日期**: {version_entry.timestamp[:10]}",
            "",
        ]
        
        if version_entry.notes:
            lines.extend([version_entry.notes, ""])
        
        if version_entry.changes:
            lines.extend(self._format_changes_by_type(version_entry.changes, "detailed"))
        
        if version_entry.commit_hash:
            lines.extend([
                "## 技术详情",
                "",
                f"- 提交哈希: {version_entry.commit_hash}",
                f"- 标签: {version_entry.tag_name}",
            ])
        
        return '\n'.join(lines)


class VersionRollback:
    """版本回滚管理器"""

    def __init__(self, version_manager: VersionManager):
        self.vm = version_manager
        self.rollback_dir = self.vm.project_root / '.version_rollbacks'
        self.rollback_dir.mkdir(parents=True, exist_ok=True)

    def create_snapshot(self, version: str) -> str:
        """创建版本快照"""
        snapshot_dir = self.rollback_dir / f"snapshot_{version}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        snapshot_dir.mkdir(parents=True, exist_ok=True)
        
        snapshot_data = {
            "version": version,
            "timestamp": datetime.now().isoformat(),
            "files": {}
        }
        
        for py_file in self.vm.project_root.rglob("*.py"):
            try:
                rel_path = py_file.relative_to(self.vm.project_root)
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                snapshot_data["files"][str(rel_path)] = {
                    "content": content,
                    "hash": hashlib.md5(content.encode()).hexdigest()
                }
            except Exception:
                continue
        
        snapshot_file = snapshot_dir / "snapshot.json"
        with open(snapshot_file, 'w', encoding='utf-8') as f:
            json.dump(snapshot_data, f, indent=2, ensure_ascii=False)
        
        return str(snapshot_dir)

    def restore_snapshot(self, snapshot_path: str) -> bool:
        """恢复快照"""
        try:
            snapshot_file = Path(snapshot_path) / "snapshot.json"
            
            with open(snapshot_file, 'r', encoding='utf-8') as f:
                snapshot_data = json.load(f)
            
            for rel_path, file_data in snapshot_data["files"].items():
                file_path = self.vm.project_root / rel_path
                
                file_path.parent.mkdir(parents=True, exist_ok=True)
                
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(file_data["content"])
            
            self.vm.rollback_version(snapshot_data["version"])
            
            return True
        
        except Exception as e:
            logging.error(f"恢复快照失败: {e}")
            return False

    def list_snapshots(self) -> List[Dict[str, Any]]:
        """列出所有快照"""
        snapshots = []
        
        for snapshot_dir in self.rollback_dir.iterdir():
            if snapshot_dir.is_dir() and snapshot_dir.name.startswith("snapshot_"):
                snapshot_file = snapshot_dir / "snapshot.json"
                
                if snapshot_file.exists():
                    try:
                        with open(snapshot_file, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                        
                        snapshots.append({
                            "path": str(snapshot_dir),
                            "version": data["version"],
                            "timestamp": data["timestamp"],
                            "file_count": len(data["files"])
                        })
                    except Exception:
                        continue
        
        return sorted(snapshots, key=lambda x: x["timestamp"], reverse=True)

    def cleanup_old_snapshots(self, keep_count: int = 10) -> int:
        """清理旧快照"""
        snapshots = self.list_snapshots()
        
        removed_count = 0
        for snapshot in snapshots[keep_count:]:
            try:
                shutil.rmtree(snapshot["path"])
                removed_count += 1
            except Exception:
                continue
        
        return removed_count


class ReleaseAutomator:
    """发布自动化器"""

    def __init__(self, version_manager: VersionManager):
        self.vm = version_manager
        self.changelog_generator = ChangelogGenerator(version_manager)
        self.rollback_manager = VersionRollback(version_manager)

    def prepare_release(
        self,
        bump_type: VersionBumpType,
        changes: List[ChangeEntry],
        author: str = "",
        notes: str = ""
    ) -> Dict[str, Any]:
        """准备发布"""
        current_version = self.vm.get_current_version()
        
        snapshot_path = self.rollback_manager.create_snapshot(str(current_version))
        
        new_version = self.vm.bump_version(bump_type)
        
        version_entry = self.vm.create_version_entry(
            new_version=new_version,
            changes=changes,
            author=author,
            notes=notes
        )
        
        self.changelog_generator.save()
        
        release_notes = self.changelog_generator.generate_release_notes(new_version)
        
        return {
            "previous_version": str(current_version),
            "new_version": new_version,
            "snapshot_path": snapshot_path,
            "version_entry": version_entry,
            "release_notes": release_notes,
            "changelog_updated": True
        }

    def execute_release(
        self,
        version: str,
        create_tag: bool = True,
        push_tag: bool = False,
        run_tests: bool = True
    ) -> Dict[str, Any]:
        """执行发布"""
        results = {
            "version": version,
            "success": True,
            "steps": []
        }
        
        if run_tests:
            test_result = self._run_tests()
            results["steps"].append({
                "name": "run_tests",
                "success": test_result,
                "message": "测试通过" if test_result else "测试失败"
            })
            
            if not test_result:
                results["success"] = False
                results["error"] = "测试失败，发布中止"
                return results
        
        if create_tag:
            tag_result = self._create_git_tag(version)
            results["steps"].append({
                "name": "create_tag",
                "success": tag_result,
                "message": f"标签 v{version} 创建成功" if tag_result else "标签创建失败"
            })
            
            if push_tag and tag_result:
                push_result = self._push_git_tag(version)
                results["steps"].append({
                    "name": "push_tag",
                    "success": push_result,
                    "message": f"标签 v{version} 推送成功" if push_result else "标签推送失败"
                })
        
        results["steps"].append({
            "name": "update_changelog",
            "success": True,
            "message": "变更日志已更新"
        })
        
        return results

    def _run_tests(self) -> bool:
        """运行测试"""
        test_commands = [
            [sys.executable, '-m', 'pytest', '-x'],
            [sys.executable, '-m', 'unittest', 'discover'],
        ]
        
        for cmd in test_commands:
            try:
                result = subprocess.run(
                    cmd,
                    cwd=self.vm.project_root,
                    capture_output=True,
                    timeout=300
                )
                
                if result.returncode == 0:
                    return True
            except Exception:
                continue
        
        return False

    def _create_git_tag(self, version: str) -> bool:
        """创建Git标签"""
        try:
            subprocess.run(
                ['git', 'tag', '-a', f'v{version}', '-m', f'Release version {version}'],
                cwd=self.vm.project_root,
                check=True,
                capture_output=True,
                timeout=10
            )
            return True
        except Exception:
            return False

    def _push_git_tag(self, version: str) -> bool:
        """推送Git标签"""
        try:
            subprocess.run(
                ['git', 'push', 'origin', f'v{version}'],
                cwd=self.vm.project_root,
                check=True,
                capture_output=True,
                timeout=30
            )
            return True
        except Exception:
            return False

    def generate_release_checklist(self, version: str) -> List[Dict[str, Any]]:
        """生成发布检查清单"""
        checklist = [
            {
                "category": "代码质量",
                "items": [
                    {"task": "所有测试通过", "checked": False},
                    {"task": "代码审查完成", "checked": False},
                    {"task": "静态分析无错误", "checked": False},
                    {"task": "文档已更新", "checked": False},
                ]
            },
            {
                "category": "版本管理",
                "items": [
                    {"task": f"版本号已更新为 {version}", "checked": False},
                    {"task": "变更日志已更新", "checked": False},
                    {"task": "Git标签已创建", "checked": False},
                    {"task": "快照已创建", "checked": False},
                ]
            },
            {
                "category": "发布准备",
                "items": [
                    {"task": "发布说明已生成", "checked": False},
                    {"task": "依赖已检查", "checked": False},
                    {"task": "环境配置已验证", "checked": False},
                    {"task": "回滚方案已准备", "checked": False},
                ]
            },
            {
                "category": "发布后",
                "items": [
                    {"task": "标签已推送", "checked": False},
                    {"task": "发布公告已发布", "checked": False},
                    {"task": "监控已配置", "checked": False},
                    {"task": "旧版本快照已清理", "checked": False},
                ]
            }
        ]
        
        return checklist


class VersionIterator:
    """版本迭代器主类"""

    def __init__(self, project_root: str = ".", version_file: Optional[str] = None):
        self.vm = VersionManager(project_root, version_file)
        self.changelog = ChangelogGenerator(self.vm)
        self.rollback = VersionRollback(self.vm)
        self.release = ReleaseAutomator(self.vm)
        self.trigger_detector = IterationTriggerDetector(self.vm)
        self.logger = self.vm.logger

    def iterate(
        self,
        bump_type: VersionBumpType,
        changes: List[ChangeEntry],
        author: str = "",
        notes: str = "",
        prerelease_id: str = "",
        build_metadata: str = ""
    ) -> VersionEntry:
        """执行版本迭代"""
        new_version = self.vm.bump_version(bump_type, prerelease_id, build_metadata)

        entry = self.vm.create_version_entry(
            new_version=new_version,
            changes=changes,
            author=author,
            notes=notes
        )

        self.changelog.save()

        self.logger.info(f"版本迭代完成: {entry.previous_version} -> {new_version}")

        return entry

    def auto_iterate(
        self,
        bump_type: VersionBumpType = VersionBumpType.PATCH,
        author: str = ""
    ) -> VersionEntry:
        """自动迭代（基于Git提交）"""
        changes = self.changelog._get_unreleased_changes()

        if not changes:
            self.logger.warning("没有检测到变更，使用默认变更记录")
            changes = [ChangeEntry(
                change_type=ChangeType.CHORE,
                description="版本迭代",
                scope="version"
            )]

        has_breaking = any(c.breaking for c in changes)
        has_feature = any(c.change_type == ChangeType.FEATURE for c in changes)

        if has_breaking:
            bump_type = VersionBumpType.MAJOR
        elif has_feature:
            bump_type = VersionBumpType.MINOR

        return self.iterate(bump_type, changes, author)

    def trigger_iteration(
        self,
        metrics: Dict[str, Any],
        author: str = ""
    ) -> Optional[VersionEntry]:
        """基于触发条件执行自迭代"""
        triggers = self.trigger_detector.check_all_triggers(metrics)
        
        if not triggers:
            self.logger.info("没有触发自迭代条件")
            return None

        bump_type = self.trigger_detector.determine_bump_type(triggers)
        
        trigger_report = self.trigger_detector.generate_trigger_report(triggers)
        
        changes = [
            ChangeEntry(
                change_type=ChangeType.FIX if bump_type == VersionBumpType.PATCH else ChangeType.REFACTOR,
                description=f"自迭代修复: {t.trigger_type.value}",
                scope="auto_iteration",
                impact_level="medium"
            )
            for t in triggers
        ]

        entry = self.iterate(
            bump_type=bump_type,
            changes=changes,
            author=author,
            notes=f"自动触发迭代\n\n{trigger_report}"
        )

        self.vm.history.iteration_triggers.extend(triggers)
        self.vm._save_history()

        return entry

    def check_iteration_needed(self, metrics: Dict[str, Any]) -> Dict[str, Any]:
        """检查是否需要迭代"""
        triggers = self.trigger_detector.check_all_triggers(metrics)
        
        return {
            "needs_iteration": len(triggers) > 0,
            "triggered_conditions": [
                {
                    "type": t.trigger_type.value,
                    "threshold": t.threshold,
                    "current_value": t.current_value,
                    "details": t.details
                }
                for t in triggers
            ],
            "recommended_bump_type": self.trigger_detector.determine_bump_type(triggers).value if triggers else None
        }

    def rollback(self, target_version: Optional[str] = None) -> bool:
        """回滚版本"""
        return self.vm.rollback_version(target_version)

    def get_status(self) -> Dict[str, Any]:
        """获取版本状态"""
        stats = self.vm.calculate_statistics()
        return {
            "project_name": self.vm.history.project_name,
            "current_version": self.vm.history.current_version,
            "iteration_count": self.vm.history.iteration_count,
            "total_versions": len(self.vm.history.versions),
            "statistics": asdict(stats),
            "latest_changes": [
                {
                    "type": c.change_type.value,
                    "description": c.description
                }
                for c in (self.vm.history.versions[0].changes if self.vm.history.versions else [])
            ]
        }

    def get_statistics(self) -> VersionStatistics:
        """获取版本统计信息"""
        return self.vm.calculate_statistics()

    def check_version_compatibility(self, version1: str, version2: str) -> Dict[str, Any]:
        """检查版本兼容性"""
        return self.vm.check_compatibility(version1, version2)

    def export_version_history(self, output_path: str, format: str = "json") -> str:
        """导出版本历史"""
        return self.vm.export_history(output_path, format)

    def generate_report(self, output_path: Optional[str] = None) -> str:
        """生成迭代报告"""
        status = self.get_status()

        lines = [
            "# 版本迭代报告",
            f"\n生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"\n## 项目信息",
            f"- 项目名称: {status['project_name']}",
            f"- 当前版本: {status['current_version']}",
            f"- 迭代次数: {status['iteration_count']}",
            f"- 版本总数: {status['total_versions']}",
        ]

        if self.vm.history.versions:
            lines.extend([
                f"\n## 最近版本",
                "| 版本 | 时间 | 作者 | 变更数 |",
                "|------|------|------|--------|",
            ])

            for v in self.vm.history.versions[:10]:
                lines.append(
                    f"| {v.version} | {v.timestamp[:10]} | {v.author} | {len(v.changes)} |"
                )

        lines.extend([
            f"\n## 版本趋势",
        ])

        if len(self.vm.history.versions) >= 2:
            recent = self.vm.history.versions[:5]
            for i in range(len(recent) - 1):
                v1 = VersionInfo.parse(recent[i].version)
                v2 = VersionInfo.parse(recent[i + 1].version)

                if v1.major > v2.major:
                    change_type = "重大版本"
                elif v1.minor > v2.minor:
                    change_type = "功能版本"
                else:
                    change_type = "修复版本"

                lines.append(f"- {recent[i+1].version} -> {recent[i].version}: {change_type}")

        report = '\n'.join(lines)

        if output_path:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(report)

        return report


def main():
    parser = argparse.ArgumentParser(
        description='版本迭代脚本 - 管理版本号和变更日志'
    )
    parser.add_argument(
        '--project-root',
        default='.',
        help='项目根目录'
    )
    parser.add_argument(
        '--version-file',
        help='版本文件路径'
    )

    subparsers = parser.add_subparsers(dest='command', help='可用命令')

    iterate_parser = subparsers.add_parser('iterate', help='执行版本迭代')
    iterate_parser.add_argument(
        '--type',
        choices=['major', 'minor', 'patch', 'prerelease', 'build'],
        default='patch',
        help='版本升级类型'
    )
    iterate_parser.add_argument(
        '--change',
        action='append',
        help='变更描述 (格式: type:description)'
    )
    iterate_parser.add_argument(
        '--author',
        help='迭代作者'
    )
    iterate_parser.add_argument(
        '--notes',
        help='版本说明'
    )
    iterate_parser.add_argument(
        '--auto',
        action='store_true',
        help='自动检测变更类型'
    )

    status_parser = subparsers.add_parser('status', help='查看版本状态')
    status_parser.add_argument(
        '--detailed',
        action='store_true',
        help='显示详细统计信息'
    )

    rollback_parser = subparsers.add_parser('rollback', help='回滚版本')
    rollback_parser.add_argument(
        '--to',
        help='目标版本号'
    )

    changelog_parser = subparsers.add_parser('changelog', help='生成变更日志')
    changelog_parser.add_argument(
        '-o', '--output',
        help='输出路径'
    )
    changelog_parser.add_argument(
        '-f', '--format',
        choices=['markdown', 'json'],
        default='markdown',
        help='输出格式'
    )

    report_parser = subparsers.add_parser('report', help='生成迭代报告')
    report_parser.add_argument(
        '-o', '--output',
        help='输出路径'
    )

    check_parser = subparsers.add_parser('check', help='检查迭代触发条件')
    check_parser.add_argument(
        '--error-rate',
        type=float,
        default=0.0,
        help='当前错误率'
    )
    check_parser.add_argument(
        '--failures',
        type=int,
        default=0,
        help='连续失败次数'
    )
    check_parser.add_argument(
        '--quality-score',
        type=float,
        default=1.0,
        help='代码质量分数'
    )
    check_parser.add_argument(
        '--trigger',
        action='store_true',
        help='如果条件满足则触发迭代'
    )

    stats_parser = subparsers.add_parser('stats', help='显示版本统计信息')
    stats_parser.add_argument(
        '-o', '--output',
        help='输出路径'
    )

    compatibility_parser = subparsers.add_parser('compatibility', help='检查版本兼容性')
    compatibility_parser.add_argument(
        'version1',
        help='版本1'
    )
    compatibility_parser.add_argument(
        'version2',
        help='版本2'
    )

    export_parser = subparsers.add_parser('export', help='导出版本历史')
    export_parser.add_argument(
        '-o', '--output',
        required=True,
        help='输出路径'
    )
    export_parser.add_argument(
        '-f', '--format',
        choices=['json', 'markdown'],
        default='json',
        help='输出格式'
    )

    args = parser.parse_args()

    iterator = VersionIterator(args.project_root, args.version_file)

    if args.command == 'iterate':
        if args.auto:
            entry = iterator.auto_iterate(author=args.author)
        else:
            bump_type = VersionBumpType(args.type)

            changes = []
            if args.change:
                for change_str in args.change:
                    parts = change_str.split(':', 1)
                    if len(parts) == 2:
                        change_type = ChangeType(parts[0]) if parts[0] in [t.value for t in ChangeType] else ChangeType.CHORE
                        changes.append(ChangeEntry(
                            change_type=change_type,
                            description=parts[1]
                        ))
            else:
                changes = [ChangeEntry(
                    change_type=ChangeType.CHORE,
                    description="版本迭代"
                )]

            entry = iterator.iterate(
                bump_type=bump_type,
                changes=changes,
                author=args.author,
                notes=args.notes
            )

        print(f"版本迭代完成!")
        print(f"新版本: {entry.version}")
        print(f"上一版本: {entry.previous_version}")
        print(f"变更数: {len(entry.changes)}")

    elif args.command == 'status':
        status = iterator.get_status()
        print(f"项目名称: {status['project_name']}")
        print(f"当前版本: {status['current_version']}")
        print(f"迭代次数: {status['iteration_count']}")
        print(f"版本总数: {status['total_versions']}")
        
        if args.detailed and 'statistics' in status:
            stats = status['statistics']
            print(f"\n=== 详细统计 ===")
            print(f"主版本数: {stats.get('major_versions', 0)}")
            print(f"次版本数: {stats.get('minor_versions', 0)}")
            print(f"修订版本数: {stats.get('patch_versions', 0)}")
            print(f"预发布版本数: {stats.get('prerelease_versions', 0)}")
            print(f"平均每版本变更数: {stats.get('average_changes_per_version', 0)}")
            print(f"最近迭代速度: {stats.get('recent_velocity', 0)} 版本/周")

    elif args.command == 'rollback':
        if iterator.rollback(args.to):
            print(f"成功回滚到版本: {iterator.vm.history.current_version}")
        else:
            print("回滚失败")
            return 1

    elif args.command == 'changelog':
        changelog = iterator.changelog.generate(args.format)

        if args.output:
            with open(args.output, 'w', encoding='utf-8') as f:
                f.write(changelog)
            print(f"变更日志已保存到: {args.output}")
        else:
            print(changelog)

    elif args.command == 'report':
        report = iterator.generate_report(args.output)

        if args.output:
            print(f"报告已保存到: {args.output}")
        else:
            print(report)

    elif args.command == 'check':
        metrics = {
            'error_rate': args.error_rate,
            'continuous_failures': args.failures,
            'code_quality_score': args.quality_score,
        }
        
        result = iterator.check_iteration_needed(metrics)
        
        print("=== 迭代触发条件检查 ===")
        print(f"需要迭代: {'是' if result['needs_iteration'] else '否'}")
        
        if result['triggered_conditions']:
            print("\n触发的条件:")
            for cond in result['triggered_conditions']:
                print(f"  - {cond['type']}: 当前值 {cond['current_value']}, 阈值 {cond['threshold']}")
                if cond['details']:
                    print(f"    详情: {cond['details'].get('message', '')}")
        
        if result['recommended_bump_type']:
            print(f"\n建议版本升级类型: {result['recommended_bump_type']}")
        
        if args.trigger and result['needs_iteration']:
            print("\n触发自迭代...")
            entry = iterator.trigger_iteration(metrics)
            if entry:
                print(f"迭代完成: {entry.version}")

    elif args.command == 'stats':
        stats = iterator.get_statistics()
        
        output = f"""# 版本统计信息

## 概览
- 总版本数: {stats.total_versions}
- 主版本数: {stats.major_versions}
- 次版本数: {stats.minor_versions}
- 修订版本数: {stats.patch_versions}
- 预发布版本数: {stats.prerelease_versions}

## 变更统计
- 平均每版本变更数: {stats.average_changes_per_version}
- 最近迭代速度: {stats.recent_velocity} 版本/周
- 最活跃范围: {stats.most_active_scope or '无'}

## 变更类型分布
"""
        for change_type, count in sorted(stats.change_type_distribution.items(), 
                                         key=lambda x: x[1], reverse=True):
            output += f"- {change_type}: {count}\n"

        if args.output:
            with open(args.output, 'w', encoding='utf-8') as f:
                f.write(output)
            print(f"统计信息已保存到: {args.output}")
        else:
            print(output)

    elif args.command == 'compatibility':
        result = iterator.check_version_compatibility(args.version1, args.version2)
        
        print(f"=== 版本兼容性检查 ===")
        print(f"版本1: {result['version1']}")
        print(f"版本2: {result['version2']}")
        print(f"兼容: {'是' if result['compatible'] else '否'}")
        
        if result['issues']:
            print("\n问题:")
            for issue in result['issues']:
                print(f"  - {issue}")
        
        if result['breaking_changes']:
            print("\n重大变更:")
            for bc in result['breaking_changes']:
                print(f"  - [{bc['version']}] {bc['description']}")

    elif args.command == 'export':
        output_path = iterator.export_version_history(args.output, args.format)
        print(f"版本历史已导出到: {output_path}")

    else:
        parser.print_help()

    return 0


if __name__ == '__main__':
    exit(main())
