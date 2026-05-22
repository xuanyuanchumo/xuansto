#!/usr/bin/env python3
"""
增强版版本迭代器
实现语义化版本自动升级、变更日志自动生成、版本快照自动创建、版本回滚机制
"""

import json
import os
import sys
import shutil
import hashlib
import subprocess
import re
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple, Set
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


class CompatibilityLevel(Enum):
    BREAKING = "breaking"
    COMPATIBLE = "compatible"
    DEPRECATED = "deprecated"
    EXPERIMENTAL = "experimental"


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


@dataclass
class SemanticVersion:
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

    def __lt__(self, other: "SemanticVersion") -> bool:
        if self.major != other.major:
            return self.major < other.major
        if self.minor != other.minor:
            return self.minor < other.minor
        if self.patch != other.patch:
            return self.patch < other.patch
        return False

    def __le__(self, other: "SemanticVersion") -> bool:
        return self == other or self < other

    def __gt__(self, other: "SemanticVersion") -> bool:
        return not self <= other

    def __ge__(self, other: "SemanticVersion") -> bool:
        return not self < other

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, SemanticVersion):
            return False
        return (
            self.major == other.major and
            self.minor == other.minor and
            self.patch == other.patch and
            self.prerelease == other.prerelease
        )

    @classmethod
    def parse(cls, version_str: str) -> "SemanticVersion":
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

    def bump(self, bump_type: VersionBumpType, prerelease_id: str = "", build_metadata: str = "") -> "SemanticVersion":
        if bump_type == VersionBumpType.MAJOR:
            return SemanticVersion(
                major=self.major + 1,
                minor=0,
                patch=0,
                prerelease=prerelease_id,
                build_metadata=build_metadata
            )
        elif bump_type == VersionBumpType.MINOR:
            return SemanticVersion(
                major=self.major,
                minor=self.minor + 1,
                patch=0,
                prerelease=prerelease_id,
                build_metadata=build_metadata
            )
        elif bump_type == VersionBumpType.PATCH:
            return SemanticVersion(
                major=self.major,
                minor=self.minor,
                patch=self.patch + 1,
                prerelease=prerelease_id,
                build_metadata=build_metadata
            )
        elif bump_type == VersionBumpType.PRERELEASE:
            return SemanticVersion(
                major=self.major,
                minor=self.minor,
                patch=self.patch,
                prerelease=prerelease_id or f"alpha.{self._get_next_prerelease_number()}",
                build_metadata=build_metadata
            )
        elif bump_type == VersionBumpType.BUILD:
            return SemanticVersion(
                major=self.major,
                minor=self.minor,
                patch=self.patch,
                prerelease=self.prerelease,
                build_metadata=build_metadata or datetime.now().strftime('%Y%m%d%H%M%S')
            )
        else:
            raise ValueError(f"未知的版本升级类型: {bump_type}")

    def _get_next_prerelease_number(self) -> int:
        if self.prerelease and 'alpha' in self.prerelease:
            try:
                return int(self.prerelease.split('.')[-1]) + 1
            except ValueError:
                return 1
        return 1


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

    def to_dict(self) -> Dict[str, Any]:
        return {
            "change_type": self.change_type.value,
            "description": self.description,
            "scope": self.scope,
            "breaking": self.breaking,
            "issue_refs": self.issue_refs,
            "author": self.author,
            "timestamp": self.timestamp.isoformat(),
            "commit_hash": self.commit_hash,
            "file_paths": self.file_paths,
            "impact_level": self.impact_level
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ChangeEntry":
        return cls(
            change_type=ChangeType(data.get("change_type", "chore")),
            description=data.get("description", ""),
            scope=data.get("scope", ""),
            breaking=data.get("breaking", False),
            issue_refs=data.get("issue_refs", []),
            author=data.get("author", ""),
            timestamp=datetime.fromisoformat(data.get("timestamp", datetime.now().isoformat())),
            commit_hash=data.get("commit_hash", ""),
            file_paths=data.get("file_paths", []),
            impact_level=data.get("impact_level", "low")
        )


@dataclass
class VersionSnapshot:
    version: str
    timestamp: str
    snapshot_id: str
    files: Dict[str, Dict[str, str]] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    description: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "version": self.version,
            "timestamp": self.timestamp,
            "snapshot_id": self.snapshot_id,
            "files": self.files,
            "metadata": self.metadata,
            "description": self.description
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "VersionSnapshot":
        return cls(
            version=data.get("version", ""),
            timestamp=data.get("timestamp", ""),
            snapshot_id=data.get("snapshot_id", ""),
            files=data.get("files", {}),
            metadata=data.get("metadata", {}),
            description=data.get("description", "")
        )


@dataclass
class DependencyInfo:
    name: str
    version_range: str
    compatibility: CompatibilityLevel
    required: bool = True
    notes: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "version_range": self.version_range,
            "compatibility": self.compatibility.value,
            "required": self.required,
            "notes": self.notes
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DependencyInfo":
        return cls(
            name=data.get("name", ""),
            version_range=data.get("version_range", ""),
            compatibility=CompatibilityLevel(data.get("compatibility", "compatible")),
            required=data.get("required", True),
            notes=data.get("notes", "")
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
    test_coverage: float = 0.0
    performance_metrics: Dict[str, float] = field(default_factory=dict)
    snapshot_id: str = ""
    compatibility_level: CompatibilityLevel = CompatibilityLevel.COMPATIBLE
    dependencies: List[DependencyInfo] = field(default_factory=list)
    deprecation_warnings: List[str] = field(default_factory=list)
    migration_guide: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "version": self.version,
            "previous_version": self.previous_version,
            "timestamp": self.timestamp,
            "changes": [c.to_dict() for c in self.changes],
            "author": self.author,
            "commit_hash": self.commit_hash,
            "tag_name": self.tag_name,
            "notes": self.notes,
            "release_type": self.release_type,
            "stability": self.stability,
            "test_coverage": self.test_coverage,
            "performance_metrics": self.performance_metrics,
            "snapshot_id": self.snapshot_id,
            "compatibility_level": self.compatibility_level.value,
            "dependencies": [d.to_dict() for d in self.dependencies],
            "deprecation_warnings": self.deprecation_warnings,
            "migration_guide": self.migration_guide
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "VersionEntry":
        return cls(
            version=data.get("version", "0.0.0"),
            previous_version=data.get("previous_version", ""),
            timestamp=data.get("timestamp", ""),
            changes=[ChangeEntry.from_dict(c) for c in data.get("changes", [])],
            author=data.get("author", ""),
            commit_hash=data.get("commit_hash", ""),
            tag_name=data.get("tag_name", ""),
            notes=data.get("notes", ""),
            release_type=data.get("release_type", "patch"),
            stability=data.get("stability", "stable"),
            test_coverage=data.get("test_coverage", 0.0),
            performance_metrics=data.get("performance_metrics", {}),
            snapshot_id=data.get("snapshot_id", ""),
            compatibility_level=CompatibilityLevel(data.get("compatibility_level", "compatible")),
            dependencies=[DependencyInfo.from_dict(d) for d in data.get("dependencies", [])],
            deprecation_warnings=data.get("deprecation_warnings", []),
            migration_guide=data.get("migration_guide", "")
        )


@dataclass
class VersionHistory:
    project_name: str
    current_version: str
    versions: List[VersionEntry]
    iteration_count: int = 0
    total_changes: int = 0
    last_iteration_time: str = ""
    snapshots: List[VersionSnapshot] = field(default_factory=list)
    statistics: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "project_name": self.project_name,
            "current_version": self.current_version,
            "versions": [v.to_dict() for v in self.versions],
            "iteration_count": self.iteration_count,
            "total_changes": self.total_changes,
            "last_iteration_time": self.last_iteration_time,
            "snapshots": [s.to_dict() for s in self.snapshots],
            "statistics": self.statistics
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "VersionHistory":
        return cls(
            project_name=data.get("project_name", "Unknown"),
            current_version=data.get("current_version", "0.0.0"),
            versions=[VersionEntry.from_dict(v) for v in data.get("versions", [])],
            iteration_count=data.get("iteration_count", 0),
            total_changes=data.get("total_changes", 0),
            last_iteration_time=data.get("last_iteration_time", ""),
            snapshots=[VersionSnapshot.from_dict(s) for s in data.get("snapshots", [])],
            statistics=data.get("statistics", {})
        )


class ChangelogGenerator:
    """变更日志生成器"""

    TYPE_TITLES = {
        ChangeType.BREAKING: "⚠️ 重大变更",
        ChangeType.FEATURE: "✨ 新功能",
        ChangeType.FIX: "🐛 Bug修复",
        ChangeType.PERF: "⚡ 性能优化",
        ChangeType.REFACTOR: "♻️ 代码重构",
        ChangeType.DOCS: "📝 文档",
        ChangeType.STYLE: "💄 代码风格",
        ChangeType.TEST: "✅ 测试",
        ChangeType.SECURITY: "🔒 安全",
        ChangeType.DEPRECATE: "⚠️ 废弃",
        ChangeType.CHORE: "🔧 其他",
    }

    def __init__(self, version_history: VersionHistory):
        self.history = version_history

    def generate(self, output_format: str = "markdown", include_unreleased: bool = True, detail_level: str = "normal") -> str:
        if output_format == "json":
            return self._generate_json()
        return self._generate_markdown(include_unreleased, detail_level)

    def _generate_markdown(self, include_unreleased: bool = True, detail_level: str = "normal") -> str:
        lines = [
            f"# {self.history.project_name} 变更日志",
            "",
            "所有显著变更都将记录在此文件中。",
            "",
            "格式基于 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.0.0/)，",
            "并且本项目遵循 [语义化版本](https://semver.org/lang/zh-CN/)。",
            "",
        ]

        for version in self.history.versions:
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

        return '\n'.join(lines)

    def _generate_json(self) -> str:
        data = {
            "project": self.history.project_name,
            "current_version": self.history.current_version,
            "versions": [v.to_dict() for v in self.history.versions]
        }
        return json.dumps(data, indent=2, ensure_ascii=False)

    def _format_changes_by_type(self, changes: List[ChangeEntry], detail_level: str = "normal") -> List[str]:
        grouped = defaultdict(list)
        for change in changes:
            grouped[change.change_type].append(change)

        lines = []
        for change_type in ChangeType:
            if change_type in grouped:
                lines.append(f"### {self.TYPE_TITLES.get(change_type, change_type.value)}")
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

    def _generate_version_details(self, version: VersionEntry) -> List[str]:
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

    def generate_release_notes(self, version: str) -> str:
        version_entry = None
        for v in self.history.versions:
            if v.version == version:
                version_entry = v
                break

        if not version_entry:
            return f"版本 {version} 未找到"

        lines = [
            f"# {self.history.project_name} v{version} 发布说明",
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


class EnhancedVersionIterator:
    """增强版版本迭代器"""

    DEFAULT_VERSION_FILE = "version.json"
    DEFAULT_CHANGELOG_FILE = "CHANGELOG.md"
    DEFAULT_SNAPSHOT_DIR = ".version_snapshots"

    def __init__(self, project_root: str = ".", version_file: Optional[str] = None):
        self.project_root = Path(project_root).resolve()
        self.version_file = Path(version_file) if version_file else self.project_root / self.DEFAULT_VERSION_FILE
        self.changelog_file = self.project_root / self.DEFAULT_CHANGELOG_FILE
        self.snapshot_dir = self.project_root / self.DEFAULT_SNAPSHOT_DIR
        self.snapshot_dir.mkdir(parents=True, exist_ok=True)
        self.logger = self._setup_logger()
        self.history = self._load_history()
        self.changelog_generator = ChangelogGenerator(self.history)

    def _setup_logger(self) -> logging.Logger:
        logger = logging.getLogger('EnhancedVersionIterator')
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
        if self.version_file.exists():
            try:
                with open(self.version_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                return VersionHistory.from_dict(data)
            except Exception as e:
                self.logger.error(f"加载版本历史失败: {e}")

        return VersionHistory(
            project_name=self.project_root.name,
            current_version="0.0.0",
            versions=[],
            iteration_count=0
        )

    def _save_history(self) -> None:
        with open(self.version_file, 'w', encoding='utf-8') as f:
            json.dump(self.history.to_dict(), f, indent=2, ensure_ascii=False)

    def get_current_version(self) -> SemanticVersion:
        return SemanticVersion.parse(self.history.current_version)

    def bump_version(
        self,
        bump_type: VersionBumpType,
        prerelease_id: str = "",
        build_metadata: str = ""
    ) -> str:
        current = self.get_current_version()
        new_version = current.bump(bump_type, prerelease_id, build_metadata)
        return str(new_version)

    def create_snapshot(self, version: str, description: str = "") -> VersionSnapshot:
        snapshot_id = f"SNAP-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        snapshot_dir = self.snapshot_dir / snapshot_id
        snapshot_dir.mkdir(parents=True, exist_ok=True)

        snapshot = VersionSnapshot(
            version=version,
            timestamp=datetime.now().isoformat(),
            snapshot_id=snapshot_id,
            description=description
        )

        for py_file in self.project_root.rglob("*.py"):
            try:
                rel_path = py_file.relative_to(self.project_root)
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()

                snapshot.files[str(rel_path)] = {
                    "content": content,
                    "hash": hashlib.md5(content.encode()).hexdigest()
                }
            except Exception:
                continue

        snapshot_file = snapshot_dir / "snapshot.json"
        with open(snapshot_file, 'w', encoding='utf-8') as f:
            json.dump(snapshot.to_dict(), f, indent=2, ensure_ascii=False)

        self.history.snapshots.append(snapshot)
        self._save_history()

        self.logger.info(f"创建版本快照: {snapshot_id}")
        return snapshot

    def restore_snapshot(self, snapshot_id: str) -> bool:
        snapshot = None
        for s in self.history.snapshots:
            if s.snapshot_id == snapshot_id:
                snapshot = s
                break

        if not snapshot:
            self.logger.error(f"快照不存在: {snapshot_id}")
            return False

        try:
            for rel_path, file_data in snapshot.files.items():
                file_path = self.project_root / rel_path
                file_path.parent.mkdir(parents=True, exist_ok=True)
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(file_data["content"])

            self.history.current_version = snapshot.version
            self._save_history()

            self.logger.info(f"恢复快照成功: {snapshot_id}")
            return True

        except Exception as e:
            self.logger.error(f"恢复快照失败: {e}")
            return False

    def list_snapshots(self) -> List[Dict[str, Any]]:
        return [
            {
                "snapshot_id": s.snapshot_id,
                "version": s.version,
                "timestamp": s.timestamp,
                "file_count": len(s.files),
                "description": s.description
            }
            for s in self.history.snapshots
        ]

    def create_version_entry(
        self,
        new_version: str,
        changes: List[ChangeEntry],
        author: str = "",
        notes: str = "",
        create_snapshot: bool = True
    ) -> VersionEntry:
        previous_version = self.history.current_version
        commit_hash = self._get_git_commit_hash()
        tag_name = f"v{new_version}"

        snapshot_id = ""
        if create_snapshot:
            snapshot = self.create_snapshot(new_version, f"Version {new_version}")
            snapshot_id = snapshot.snapshot_id

        entry = VersionEntry(
            version=new_version,
            previous_version=previous_version,
            timestamp=datetime.now().isoformat(),
            changes=changes,
            author=author or self._get_git_user(),
            commit_hash=commit_hash,
            tag_name=tag_name,
            notes=notes,
            snapshot_id=snapshot_id
        )

        self.history.versions.insert(0, entry)
        self.history.current_version = new_version
        self.history.iteration_count += 1
        self.history.total_changes += len(changes)
        self.history.last_iteration_time = datetime.now().isoformat()

        self._save_history()

        return entry

    def _get_git_commit_hash(self) -> str:
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
        if not target_version:
            if len(self.history.versions) < 2:
                self.logger.error("没有可回滚的版本")
                return False
            target_version = self.history.versions[1].version

        target_entry = None
        target_index = -1
        for i, version in enumerate(self.history.versions):
            if version.version == target_version:
                target_entry = version
                target_index = i
                break

        if not target_entry:
            self.logger.error(f"未找到版本: {target_version}")
            return False

        if target_entry.snapshot_id:
            if not self.restore_snapshot(target_entry.snapshot_id):
                self.logger.warning(f"快照恢复失败，仅回滚版本号")

        self.history.current_version = target_version
        self.history.versions = self.history.versions[target_index:]
        self._save_history()

        self.logger.info(f"已回滚到版本: {target_version}")
        return True

    def iterate(
        self,
        bump_type: VersionBumpType,
        changes: List[ChangeEntry],
        author: str = "",
        notes: str = "",
        prerelease_id: str = "",
        build_metadata: str = "",
        create_snapshot: bool = True
    ) -> VersionEntry:
        new_version = self.bump_version(bump_type, prerelease_id, build_metadata)

        entry = self.create_version_entry(
            new_version=new_version,
            changes=changes,
            author=author,
            notes=notes,
            create_snapshot=create_snapshot
        )

        self.changelog_generator = ChangelogGenerator(self.history)
        changelog = self.changelog_generator.generate()
        with open(self.changelog_file, 'w', encoding='utf-8') as f:
            f.write(changelog)

        self.logger.info(f"版本迭代完成: {entry.previous_version} -> {new_version}")

        return entry

    def auto_iterate(self, author: str = "") -> VersionEntry:
        changes = self._get_unreleased_changes()

        if not changes:
            self.logger.warning("没有检测到变更，使用默认变更记录")
            changes = [ChangeEntry(
                change_type=ChangeType.CHORE,
                description="版本迭代",
                scope="version"
            )]

        has_breaking = any(c.breaking or c.change_type == ChangeType.BREAKING for c in changes)
        has_feature = any(c.change_type == ChangeType.FEATURE for c in changes)

        if has_breaking:
            bump_type = VersionBumpType.MAJOR
        elif has_feature:
            bump_type = VersionBumpType.MINOR
        else:
            bump_type = VersionBumpType.PATCH

        return self.iterate(bump_type, changes, author)

    def _get_unreleased_changes(self) -> List[ChangeEntry]:
        try:
            result = subprocess.run(
                ['git', 'log', f'{self.history.current_version}..HEAD', '--pretty=format:%s'],
                cwd=self.project_root,
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

    def suggest_next_version(self, changes: List[ChangeEntry]) -> Tuple[str, VersionBumpType]:
        has_breaking = any(c.breaking or c.change_type == ChangeType.BREAKING for c in changes)
        has_feature = any(c.change_type == ChangeType.FEATURE for c in changes)
        has_security = any(c.change_type == ChangeType.SECURITY for c in changes)

        if has_breaking:
            bump_type = VersionBumpType.MAJOR
        elif has_feature:
            bump_type = VersionBumpType.MINOR
        else:
            bump_type = VersionBumpType.PATCH

        next_version = self.bump_version(bump_type)
        return next_version, bump_type

    def get_status(self) -> Dict[str, Any]:
        return {
            "project_name": self.history.project_name,
            "current_version": self.history.current_version,
            "iteration_count": self.history.iteration_count,
            "total_versions": len(self.history.versions),
            "total_changes": self.history.total_changes,
            "last_iteration_time": self.history.last_iteration_time,
            "snapshots_count": len(self.history.snapshots)
        }

    def generate_report(self, output_path: Optional[str] = None) -> str:
        status = self.get_status()

        lines = [
            "# 版本迭代报告",
            f"\n生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"\n## 项目信息",
            f"- 项目名称: {status['project_name']}",
            f"- 当前版本: {status['current_version']}",
            f"- 迭代次数: {status['iteration_count']}",
            f"- 版本总数: {status['total_versions']}",
            f"- 变更总数: {status['total_changes']}",
            f"- 快照数量: {status['snapshots_count']}",
        ]

        if self.history.versions:
            lines.extend([
                f"\n## 最近版本",
                "| 版本 | 时间 | 作者 | 变更数 |",
                "|------|------|------|--------|",
            ])

            for v in self.history.versions[:10]:
                lines.append(
                    f"| {v.version} | {v.timestamp[:10]} | {v.author} | {len(v.changes)} |"
                )

        report = '\n'.join(lines)

        if output_path:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(report)

        return report

    def check_compatibility(self, from_version: str, to_version: str) -> Dict[str, Any]:
        """
        检查版本兼容性
        """
        from_ver = SemanticVersion.parse(from_version)
        to_ver = SemanticVersion.parse(to_version)

        compatibility_result = {
            "from_version": from_version,
            "to_version": to_version,
            "compatible": True,
            "breaking_changes": [],
            "deprecations": [],
            "migration_required": False,
            "migration_guide": ""
        }

        from_entry = None
        to_entry = None
        for v in self.history.versions:
            if v.version == from_version:
                from_entry = v
            if v.version == to_version:
                to_entry = v

        if to_entry:
            compatibility_result["compatible"] = to_entry.compatibility_level != CompatibilityLevel.BREAKING
            compatibility_result["deprecations"] = to_entry.deprecation_warnings
            compatibility_result["migration_guide"] = to_entry.migration_guide
            compatibility_result["migration_required"] = len(to_entry.deprecation_warnings) > 0

            breaking_changes = [c for c in to_entry.changes if c.breaking]
            compatibility_result["breaking_changes"] = [
                {
                    "description": c.description,
                    "scope": c.scope,
                    "file_paths": c.file_paths
                }
                for c in breaking_changes
            ]

        if from_ver.major != to_ver.major:
            compatibility_result["compatible"] = False
            compatibility_result["migration_required"] = True

        return compatibility_result

    def manage_dependencies(self, version: str, dependencies: List[DependencyInfo]) -> None:
        """
        管理版本依赖
        """
        for v in self.history.versions:
            if v.version == version:
                v.dependencies = dependencies
                self._save_history()
                self.logger.info(f"已更新版本 {version} 的依赖信息")
                return

        self.logger.warning(f"版本 {version} 未找到")

    def get_dependencies(self, version: str) -> List[DependencyInfo]:
        """
        获取版本依赖
        """
        for v in self.history.versions:
            if v.version == version:
                return v.dependencies

        return []

    def compare_versions(self, version1: str, version2: str) -> Dict[str, Any]:
        """
        比较两个版本
        """
        v1 = SemanticVersion.parse(version1)
        v2 = SemanticVersion.parse(version2)

        comparison = {
            "version1": version1,
            "version2": version2,
            "v1_greater": v1 > v2,
            "v2_greater": v2 > v1,
            "equal": v1 == v2,
            "difference": {
                "major": abs(v1.major - v2.major),
                "minor": abs(v1.minor - v2.minor),
                "patch": abs(v1.patch - v2.patch)
            }
        }

        entry1 = None
        entry2 = None
        for v in self.history.versions:
            if v.version == version1:
                entry1 = v
            if v.version == version2:
                entry2 = v

        if entry1 and entry2:
            comparison["changes_between"] = abs(len(entry1.changes) - len(entry2.changes))
            comparison["time_difference"] = self._calculate_time_difference(
                entry1.timestamp, entry2.timestamp
            )

        return comparison

    def _calculate_time_difference(self, timestamp1: str, timestamp2: str) -> str:
        """
        计算时间差
        """
        try:
            t1 = datetime.fromisoformat(timestamp1)
            t2 = datetime.fromisoformat(timestamp2)
            diff = abs(t1 - t2)

            days = diff.days
            hours = diff.seconds // 3600

            if days > 0:
                return f"{days}天{hours}小时"
            else:
                return f"{hours}小时"
        except Exception:
            return "未知"

    def create_version_branch(self, branch_name: str, from_version: str) -> bool:
        """
        创建版本分支
        """
        from_entry = None
        for v in self.history.versions:
            if v.version == from_version:
                from_entry = v
                break

        if not from_entry:
            self.logger.error(f"版本 {from_version} 未找到")
            return False

        branch_dir = self.snapshot_dir / "branches" / branch_name
        branch_dir.mkdir(parents=True, exist_ok=True)

        branch_file = branch_dir / "version.json"
        branch_history = VersionHistory(
            project_name=f"{self.history.project_name}-{branch_name}",
            current_version=from_version,
            versions=[from_entry],
            iteration_count=0,
            total_changes=len(from_entry.changes)
        )

        with open(branch_file, 'w', encoding='utf-8') as f:
            json.dump(branch_history.to_dict(), f, indent=2, ensure_ascii=False)

        self.logger.info(f"已创建版本分支: {branch_name} (基于版本 {from_version})")
        return True

    def suggest_version_upgrade(self, changes: List[ChangeEntry]) -> Dict[str, Any]:
        """
        智能版本升级建议
        """
        suggestion = {
            "current_version": self.history.current_version,
            "suggested_version": "",
            "bump_type": "",
            "reasoning": [],
            "risk_level": "low",
            "recommendations": []
        }

        has_breaking = any(c.breaking or c.change_type == ChangeType.BREAKING for c in changes)
        has_feature = any(c.change_type == ChangeType.FEATURE for c in changes)
        has_security = any(c.change_type == ChangeType.SECURITY for c in changes)
        has_deprecate = any(c.change_type == ChangeType.DEPRECATE for c in changes)
        has_fix = any(c.change_type == ChangeType.FIX for c in changes)

        if has_breaking:
            suggestion["bump_type"] = "major"
            suggestion["reasoning"].append("包含破坏性变更")
            suggestion["risk_level"] = "high"
            suggestion["recommendations"].append("建议提供详细的迁移指南")
        elif has_feature or has_deprecate:
            suggestion["bump_type"] = "minor"
            suggestion["reasoning"].append("包含新功能或废弃标记")
            suggestion["risk_level"] = "medium"
            if has_deprecate:
                suggestion["recommendations"].append("建议在文档中明确废弃计划")
        else:
            suggestion["bump_type"] = "patch"
            suggestion["reasoning"].append("仅包含修复和改进")
            suggestion["risk_level"] = "low"

        if has_security:
            suggestion["recommendations"].append("建议优先发布安全更新")

        next_version = self.bump_version(VersionBumpType(suggestion["bump_type"]))
        suggestion["suggested_version"] = next_version

        return suggestion


def main():
    parser = argparse.ArgumentParser(description='增强版版本迭代器')
    parser.add_argument('--project-root', default='.', help='项目根目录')
    parser.add_argument('--version-file', help='版本文件路径')

    subparsers = parser.add_subparsers(dest='command', help='可用命令')

    iterate_parser = subparsers.add_parser('iterate', help='执行版本迭代')
    iterate_parser.add_argument('--type', choices=['major', 'minor', 'patch', 'prerelease', 'build'], default='patch', help='版本升级类型')
    iterate_parser.add_argument('--change', action='append', help='变更描述 (格式: type:description)')
    iterate_parser.add_argument('--author', help='迭代作者')
    iterate_parser.add_argument('--notes', help='版本说明')
    iterate_parser.add_argument('--auto', action='store_true', help='自动检测变更类型')
    iterate_parser.add_argument('--no-snapshot', action='store_true', help='不创建快照')

    status_parser = subparsers.add_parser('status', help='查看版本状态')

    rollback_parser = subparsers.add_parser('rollback', help='回滚版本')
    rollback_parser.add_argument('--to', help='目标版本号')

    snapshot_parser = subparsers.add_parser('snapshot', help='快照管理')
    snapshot_parser.add_argument('action', choices=['list', 'create', 'restore'], help='快照操作')
    snapshot_parser.add_argument('--id', help='快照ID')
    snapshot_parser.add_argument('--description', help='快照描述')

    changelog_parser = subparsers.add_parser('changelog', help='生成变更日志')
    changelog_parser.add_argument('-o', '--output', help='输出路径')
    changelog_parser.add_argument('-f', '--format', choices=['markdown', 'json'], default='markdown', help='输出格式')

    report_parser = subparsers.add_parser('report', help='生成迭代报告')
    report_parser.add_argument('-o', '--output', help='输出路径')

    args = parser.parse_args()

    iterator = EnhancedVersionIterator(args.project_root, args.version_file)

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
                notes=args.notes,
                create_snapshot=not args.no_snapshot
            )

        print(f"版本迭代完成!")
        print(f"新版本: {entry.version}")
        print(f"上一版本: {entry.previous_version}")
        print(f"变更数: {len(entry.changes)}")
        print(f"快照ID: {entry.snapshot_id}")

    elif args.command == 'status':
        status = iterator.get_status()
        print(f"项目名称: {status['project_name']}")
        print(f"当前版本: {status['current_version']}")
        print(f"迭代次数: {status['iteration_count']}")
        print(f"版本总数: {status['total_versions']}")
        print(f"变更总数: {status['total_changes']}")
        print(f"快照数量: {status['snapshots_count']}")

    elif args.command == 'rollback':
        if iterator.rollback_version(args.to):
            print(f"成功回滚到版本: {iterator.history.current_version}")
        else:
            print("回滚失败")
            return 1

    elif args.command == 'snapshot':
        if args.action == 'list':
            snapshots = iterator.list_snapshots()
            print("=== 版本快照列表 ===")
            for snap in snapshots:
                print(f"ID: {snap['snapshot_id']}")
                print(f"  版本: {snap['version']}")
                print(f"  时间: {snap['timestamp']}")
                print(f"  文件数: {snap['file_count']}")
                print()
        elif args.action == 'create':
            snapshot = iterator.create_snapshot(
                iterator.history.current_version,
                args.description or "手动创建快照"
            )
            print(f"快照创建成功: {snapshot.snapshot_id}")
        elif args.action == 'restore':
            if not args.id:
                print("错误: 需要指定快照ID")
                return 1
            if iterator.restore_snapshot(args.id):
                print(f"快照恢复成功: {args.id}")
            else:
                print("快照恢复失败")
                return 1

    elif args.command == 'changelog':
        changelog = iterator.changelog_generator.generate(args.format)

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

    else:
        parser.print_help()

    return 0


if __name__ == '__main__':
    exit(main())
