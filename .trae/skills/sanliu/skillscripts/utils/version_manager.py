#!/usr/bin/env python3
"""
版本号管理脚本 - Sanliu 技能

功能：
- 管理项目版本号（语义化版本控制）
- 自动更新版本号文件
- 生成版本变更日志
- 支持版本比较和验证
- 与 Git 集成
- 版本迭代生命周期管理
- 版本发布计划管理
- 版本依赖关系追踪

使用方法：
    python scripts/version_manager.py --help
    python scripts/version_manager.py current
    python scripts/version_manager.py bump patch
    python scripts/version_manager.py bump minor --changelog
    python scripts/version_manager.py release --plan
    python scripts/version_manager.py lifecycle status
"""

import argparse
import json
import logging
import os
import re
import subprocess
import sys
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Optional


# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - [%(name)s] %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('version_manager.log', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)


class VersionPart(Enum):
    """版本号部分枚举"""
    MAJOR = "major"
    MINOR = "minor"
    PATCH = "patch"


class VersionStatus(Enum):
    """版本状态枚举"""
    PLANNED = "planned"
    DEVELOPMENT = "development"
    TESTING = "testing"
    RELEASE_CANDIDATE = "rc"
    RELEASED = "released"
    DEPRECATED = "deprecated"
    RETIRED = "retired"


class ReleaseType(Enum):
    """发布类型枚举"""
    MAJOR = "major"
    MINOR = "minor"
    PATCH = "patch"
    HOTFIX = "hotfix"
    BETA = "beta"
    ALPHA = "alpha"


@dataclass
class Version:
    """版本号数据类"""
    major: int
    minor: int
    patch: int
    prerelease: str = ""
    build: str = ""

    @classmethod
    def parse(cls, version_str: str) -> "Version":
        """解析版本号字符串"""
        # 语义化版本正则: MAJOR.MINOR.PATCH[-prerelease][+build]
        pattern = r'^(\d+)\.(\d+)\.(\d+)(?:-([a-zA-Z0-9.]+))?(?:\+([a-zA-Z0-9.]+))?$'
        match = re.match(pattern, version_str)

        if not match:
            raise ValueError(f"无效的版本号格式: {version_str}")

        return cls(
            major=int(match.group(1)),
            minor=int(match.group(2)),
            patch=int(match.group(3)),
            prerelease=match.group(4) or "",
            build=match.group(5) or ""
        )

    def __str__(self) -> str:
        """转换为字符串"""
        version = f"{self.major}.{self.minor}.{self.patch}"
        if self.prerelease:
            version += f"-{self.prerelease}"
        if self.build:
            version += f"+{self.build}"
        return version

    def bump(self, part: VersionPart) -> "Version":
        """递增版本号"""
        if part == VersionPart.MAJOR:
            return Version(
                major=self.major + 1,
                minor=0,
                patch=0,
                prerelease=self.prerelease,
                build=self.build
            )
        elif part == VersionPart.MINOR:
            return Version(
                major=self.major,
                minor=self.minor + 1,
                patch=0,
                prerelease=self.prerelease,
                build=self.build
            )
        else:  # PATCH
            return Version(
                major=self.major,
                minor=self.minor,
                patch=self.patch + 1,
                prerelease=self.prerelease,
                build=self.build
            )

    def set_prerelease(self, prerelease: str) -> "Version":
        """设置预发布版本"""
        return Version(
            major=self.major,
            minor=self.minor,
            patch=self.patch,
            prerelease=prerelease,
            build=self.build
        )

    def set_build(self, build: str) -> "Version":
        """设置构建元数据"""
        return Version(
            major=self.major,
            minor=self.minor,
            patch=self.patch,
            prerelease=self.prerelease,
            build=build
        )

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Version):
            return False
        return (self.major, self.minor, self.patch) == (other.major, other.minor, other.patch)

    def __lt__(self, other: "Version") -> bool:
        if (self.major, self.minor, self.patch) != (other.major, other.minor, other.patch):
            return (self.major, self.minor, self.patch) < (other.major, other.minor, other.patch)
        # 预发布版本比较逻辑简化处理
        if self.prerelease and not other.prerelease:
            return True
        if not self.prerelease and other.prerelease:
            return False
        return self.prerelease < other.prerelease

    def __le__(self, other: "Version") -> bool:
        return self == other or self < other

    def __gt__(self, other: "Version") -> bool:
        return not self <= other

    def __ge__(self, other: "Version") -> bool:
        return not self < other


@dataclass
class VersionConfig:
    """版本管理配置"""
    version_file: Path
    changelog_file: Optional[Path] = None
    package_files: list[Path] = field(default_factory=list)
    git_tag: bool = False
    git_commit: bool = False
    git_remote: str = "origin"


@dataclass
class ChangelogEntry:
    """变更日志条目"""
    version: str
    date: str
    changes: list[str]
    author: str = ""


@dataclass
class ReleasePlan:
    """发布计划"""
    version: str
    release_type: ReleaseType
    target_date: datetime
    features: list[str] = field(default_factory=list)
    bugfixes: list[str] = field(default_factory=list)
    breaking_changes: list[str] = field(default_factory=list)
    dependencies: list[str] = field(default_factory=list)
    status: VersionStatus = VersionStatus.PLANNED
    progress: float = 0.0
    notes: str = ""


@dataclass
class VersionLifecycle:
    """版本生命周期"""
    version: str
    status: VersionStatus
    created_at: datetime
    planned_release: Optional[datetime] = None
    actual_release: Optional[datetime] = None
    end_of_life: Optional[datetime] = None
    support_end: Optional[datetime] = None
    milestones: dict[str, datetime] = field(default_factory=dict)


@dataclass
class VersionDependency:
    """版本依赖关系"""
    version: str
    depends_on: list[str] = field(default_factory=list)
    compatible_with: list[str] = field(default_factory=list)
    conflicts_with: list[str] = field(default_factory=list)


class VersionManager:
    """版本号管理器"""

    def __init__(self, config: VersionConfig):
        self.config = config
        self._version: Optional[Version] = None
        self._release_plans: dict[str, ReleasePlan] = {}
        self._lifecycles: dict[str, VersionLifecycle] = {}
        self._dependencies: dict[str, VersionDependency] = {}
        self._load_extended_data()

    def _load_extended_data(self):
        """加载扩展数据"""
        data_file = self.config.version_file.parent / "version_data.json"
        if data_file.exists():
            try:
                with open(data_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                for ver, plan_data in data.get('release_plans', {}).items():
                    self._release_plans[ver] = ReleasePlan(
                        version=ver,
                        release_type=ReleaseType(plan_data['release_type']),
                        target_date=datetime.fromisoformat(plan_data['target_date']),
                        features=plan_data.get('features', []),
                        bugfixes=plan_data.get('bugfixes', []),
                        breaking_changes=plan_data.get('breaking_changes', []),
                        dependencies=plan_data.get('dependencies', []),
                        status=VersionStatus(plan_data.get('status', 'planned')),
                        progress=plan_data.get('progress', 0.0),
                        notes=plan_data.get('notes', '')
                    )

                for ver, lifecycle_data in data.get('lifecycles', {}).items():
                    self._lifecycles[ver] = VersionLifecycle(
                        version=ver,
                        status=VersionStatus(lifecycle_data['status']),
                        created_at=datetime.fromisoformat(lifecycle_data['created_at']),
                        planned_release=datetime.fromisoformat(lifecycle_data['planned_release']) if lifecycle_data.get('planned_release') else None,
                        actual_release=datetime.fromisoformat(lifecycle_data['actual_release']) if lifecycle_data.get('actual_release') else None,
                        end_of_life=datetime.fromisoformat(lifecycle_data['end_of_life']) if lifecycle_data.get('end_of_life') else None,
                        support_end=datetime.fromisoformat(lifecycle_data['support_end']) if lifecycle_data.get('support_end') else None,
                        milestones={k: datetime.fromisoformat(v) for k, v in lifecycle_data.get('milestones', {}).items()}
                    )

                for ver, dep_data in data.get('dependencies', {}).items():
                    self._dependencies[ver] = VersionDependency(
                        version=ver,
                        depends_on=dep_data.get('depends_on', []),
                        compatible_with=dep_data.get('compatible_with', []),
                        conflicts_with=dep_data.get('conflicts_with', [])
                    )

            except Exception as e:
                logger.warning(f"加载扩展数据失败: {e}")

    def _save_extended_data(self):
        """保存扩展数据"""
        data_file = self.config.version_file.parent / "version_data.json"
        data_file.parent.mkdir(parents=True, exist_ok=True)

        data = {
            'release_plans': {},
            'lifecycles': {},
            'dependencies': {}
        }

        for ver, plan in self._release_plans.items():
            data['release_plans'][ver] = {
                'version': plan.version,
                'release_type': plan.release_type.value,
                'target_date': plan.target_date.isoformat(),
                'features': plan.features,
                'bugfixes': plan.bugfixes,
                'breaking_changes': plan.breaking_changes,
                'dependencies': plan.dependencies,
                'status': plan.status.value,
                'progress': plan.progress,
                'notes': plan.notes
            }

        for ver, lifecycle in self._lifecycles.items():
            data['lifecycles'][ver] = {
                'version': lifecycle.version,
                'status': lifecycle.status.value,
                'created_at': lifecycle.created_at.isoformat(),
                'planned_release': lifecycle.planned_release.isoformat() if lifecycle.planned_release else None,
                'actual_release': lifecycle.actual_release.isoformat() if lifecycle.actual_release else None,
                'end_of_life': lifecycle.end_of_life.isoformat() if lifecycle.end_of_life else None,
                'support_end': lifecycle.support_end.isoformat() if lifecycle.support_end else None,
                'milestones': {k: v.isoformat() for k, v in lifecycle.milestones.items()}
            }

        for ver, dep in self._dependencies.items():
            data['dependencies'][ver] = {
                'version': dep.version,
                'depends_on': dep.depends_on,
                'compatible_with': dep.compatible_with,
                'conflicts_with': dep.conflicts_with
            }

        with open(data_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def get_current_version(self) -> Version:
        """获取当前版本号"""
        if self._version is None:
            self._version = self._read_version_file()
        return self._version

    def _read_version_file(self) -> Version:
        """读取版本号文件"""
        if not self.config.version_file.exists():
            logger.warning(f"版本文件不存在: {self.config.version_file}")
            # 创建默认版本
            default_version = Version(0, 1, 0)
            self._write_version_file(default_version)
            return default_version

        try:
            with open(self.config.version_file, 'r', encoding='utf-8') as f:
                content = f.read().strip()

            # 尝试解析 JSON 格式
            try:
                data = json.loads(content)
                version_str = data.get('version', content)
            except json.JSONDecodeError:
                version_str = content

            return Version.parse(version_str)

        except Exception as e:
            logger.error(f"读取版本文件失败: {e}")
            raise

    def _write_version_file(self, version: Version):
        """写入版本号文件"""
        self.config.version_file.parent.mkdir(parents=True, exist_ok=True)

        # 检查文件扩展名决定格式
        if self.config.version_file.suffix == '.json':
            data = {
                "version": str(version),
                "updated_at": datetime.now().isoformat()
            }
            with open(self.config.version_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        else:
            with open(self.config.version_file, 'w', encoding='utf-8') as f:
                f.write(str(version))

        logger.info(f"版本文件已更新: {self.config.version_file}")

    def bump_version(self, part: VersionPart, message: str = "") -> Version:
        """递增版本号"""
        current = self.get_current_version()
        new_version = current.bump(part)

        logger.info(f"版本号更新: {current} -> {new_version}")

        # 更新版本文件
        self._write_version_file(new_version)

        # 更新 package 文件
        self._update_package_files(new_version)

        # 更新变更日志
        if self.config.changelog_file:
            self._update_changelog(new_version, message)

        # Git 操作
        if self.config.git_commit:
            self._git_commit(new_version, message)

        if self.config.git_tag:
            self._git_tag(new_version)

        self._version = new_version
        return new_version

    def set_version(self, version_str: str, message: str = "") -> Version:
        """设置特定版本号"""
        new_version = Version.parse(version_str)
        current = self.get_current_version()

        logger.info(f"版本号设置: {current} -> {new_version}")

        # 更新版本文件
        self._write_version_file(new_version)

        # 更新 package 文件
        self._update_package_files(new_version)

        # 更新变更日志
        if self.config.changelog_file:
            self._update_changelog(new_version, message)

        self._version = new_version
        return new_version

    def _update_package_files(self, version: Version):
        """更新 package 文件中的版本号"""
        version_str = str(version)

        for package_file in self.config.package_files:
            if not package_file.exists():
                continue

            try:
                with open(package_file, 'r', encoding='utf-8') as f:
                    content = f.read()

                # 根据文件类型更新版本号
                if package_file.name == 'package.json':
                    data = json.loads(content)
                    data['version'] = version_str
                    with open(package_file, 'w', encoding='utf-8') as f:
                        json.dump(data, f, indent=2, ensure_ascii=False)

                elif package_file.name == 'pyproject.toml':
                    # 简单替换版本号行
                    content = re.sub(
                        r'version\s*=\s*"[^"]+"',
                        f'version = "{version_str}"',
                        content
                    )
                    with open(package_file, 'w', encoding='utf-8') as f:
                        f.write(content)

                elif package_file.name == 'setup.py':
                    content = re.sub(
                        r'version\s*=\s*["\'][^"\']+["\']',
                        f'version="{version_str}"',
                        content
                    )
                    with open(package_file, 'w', encoding='utf-8') as f:
                        f.write(content)

                logger.info(f"已更新: {package_file}")

            except Exception as e:
                logger.error(f"更新 {package_file} 失败: {e}")

    def _update_changelog(self, version: Version, message: str = ""):
        """更新变更日志"""
        if not self.config.changelog_file:
            return

        self.config.changelog_file.parent.mkdir(parents=True, exist_ok=True)

        entry = ChangelogEntry(
            version=str(version),
            date=datetime.now().strftime('%Y-%m-%d'),
            changes=self._get_changes_from_git() if not message else [message],
            author=self._get_git_user()
        )

        # 读取现有变更日志
        existing_content = ""
        if self.config.changelog_file.exists():
            with open(self.config.changelog_file, 'r', encoding='utf-8') as f:
                existing_content = f.read()

        # 生成新条目
        new_entry = f"\n## [{entry.version}] - {entry.date}\n\n"
        if entry.changes:
            for change in entry.changes:
                new_entry += f"- {change}\n"
        else:
            new_entry += "- 版本更新\n"

        # 写入变更日志
        header = "# 变更日志\n\n所有显著的变更都将记录在此文件中。\n"
        if not existing_content:
            content = header + new_entry
        else:
            # 在第一个 ## 之前插入新条目
            if '## [' in existing_content:
                parts = existing_content.split('## [', 1)
                content = parts[0] + new_entry + "\n## [" + parts[1]
            else:
                content = existing_content + new_entry

        with open(self.config.changelog_file, 'w', encoding='utf-8') as f:
            f.write(content)

        logger.info(f"变更日志已更新: {self.config.changelog_file}")

    def _get_changes_from_git(self) -> list[str]:
        """从 Git 获取最近的变更"""
        try:
            # 获取最近的提交信息
            result = subprocess.run(
                ['git', 'log', '-10', '--pretty=format:%s'],
                capture_output=True,
                text=True,
                check=True
            )
            return result.stdout.strip().split('\n')
        except Exception:
            return []

    def _get_git_user(self) -> str:
        """获取 Git 用户名"""
        try:
            result = subprocess.run(
                ['git', 'config', 'user.name'],
                capture_output=True,
                text=True,
                check=True
            )
            return result.stdout.strip()
        except Exception:
            return ""

    def _git_commit(self, version: Version, message: str = ""):
        """创建 Git 提交"""
        try:
            commit_message = message or f"chore: bump version to {version}"

            # 添加文件
            subprocess.run(['git', 'add', str(self.config.version_file)], check=True)

            if self.config.changelog_file and self.config.changelog_file.exists():
                subprocess.run(['git', 'add', str(self.config.changelog_file)], check=True)

            for package_file in self.config.package_files:
                if package_file.exists():
                    subprocess.run(['git', 'add', str(package_file)], check=True)

            # 提交
            subprocess.run(['git', 'commit', '-m', commit_message], check=True)

            logger.info(f"Git 提交已创建: {commit_message}")

        except subprocess.CalledProcessError as e:
            logger.error(f"Git 提交失败: {e}")
        except FileNotFoundError:
            logger.warning("Git 命令未找到，跳过 Git 操作")

    def _git_tag(self, version: Version):
        """创建 Git 标签"""
        try:
            tag_name = f"v{version}"
            subprocess.run(
                ['git', 'tag', '-a', tag_name, '-m', f"Release {version}"],
                check=True
            )

            # 推送标签
            if self.config.git_remote:
                subprocess.run(
                    ['git', 'push', self.config.git_remote, tag_name],
                    check=True
                )

            logger.info(f"Git 标签已创建: {tag_name}")

        except subprocess.CalledProcessError as e:
            logger.error(f"Git 标签创建失败: {e}")
        except FileNotFoundError:
            logger.warning("Git 命令未找到，跳过 Git 操作")

    def compare_versions(self, version1: str, version2: str) -> dict[str, Any]:
        """比较两个版本号"""
        v1 = Version.parse(version1)
        v2 = Version.parse(version2)

        return {
            "version1": str(v1),
            "version2": str(v2),
            "equal": v1 == v2,
            "less_than": v1 < v2,
            "greater_than": v1 > v2,
            "difference": self._calculate_difference(v1, v2)
        }

    def _calculate_difference(self, v1: Version, v2: Version) -> dict[str, int]:
        """计算版本差异"""
        return {
            "major": v2.major - v1.major,
            "minor": v2.minor - v1.minor,
            "patch": v2.patch - v1.patch
        }

    def validate_version(self, version_str: str) -> dict[str, Any]:
        """验证版本号格式"""
        try:
            version = Version.parse(version_str)
            return {
                "valid": True,
                "version": str(version),
                "parts": {
                    "major": version.major,
                    "minor": version.minor,
                    "patch": version.patch,
                    "prerelease": version.prerelease,
                    "build": version.build
                }
            }
        except ValueError as e:
            return {
                "valid": False,
                "error": str(e)
            }

    def get_version_history(self) -> list[dict[str, Any]]:
        """获取版本历史"""
        history = []

        if not self.config.changelog_file or not self.config.changelog_file.exists():
            return history

        try:
            with open(self.config.changelog_file, 'r', encoding='utf-8') as f:
                content = f.read()

            pattern = r'##\s*\[([^\]]+)\]\s*-\s*(\d{4}-\d{2}-\d{2})'
            matches = re.findall(pattern, content)

            for version_str, date in matches:
                try:
                    version = Version.parse(version_str)
                    history.append({
                        "version": str(version),
                        "date": date,
                        "parts": {
                            "major": version.major,
                            "minor": version.minor,
                            "patch": version.patch
                        }
                    })
                except ValueError:
                    continue

        except Exception as e:
            logger.error(f"读取版本历史失败: {e}")

        return history

    def create_release_plan(self, version: str, release_type: ReleaseType, target_date: datetime, features: list[str] = None, notes: str = "") -> ReleasePlan:
        """创建发布计划"""
        plan = ReleasePlan(
            version=version,
            release_type=release_type,
            target_date=target_date,
            features=features or [],
            notes=notes
        )
        self._release_plans[version] = plan
        self._save_extended_data()
        logger.info(f"创建发布计划: {version} - {release_type.value}")
        return plan

    def update_release_plan(self, version: str, **kwargs) -> Optional[ReleasePlan]:
        """更新发布计划"""
        if version not in self._release_plans:
            return None

        plan = self._release_plans[version]
        for key, value in kwargs.items():
            if hasattr(plan, key):
                setattr(plan, key, value)

        self._save_extended_data()
        logger.info(f"更新发布计划: {version}")
        return plan

    def get_release_plan(self, version: str) -> Optional[ReleasePlan]:
        """获取发布计划"""
        return self._release_plans.get(version)

    def list_release_plans(self, status: VersionStatus = None) -> list[ReleasePlan]:
        """列出发布计划"""
        plans = list(self._release_plans.values())
        if status:
            plans = [p for p in plans if p.status == status]
        return sorted(plans, key=lambda p: p.target_date)

    def start_lifecycle(self, version: str) -> VersionLifecycle:
        """开始版本生命周期"""
        lifecycle = VersionLifecycle(
            version=version,
            status=VersionStatus.DEVELOPMENT,
            created_at=datetime.now(),
            milestones={'development_start': datetime.now()}
        )
        self._lifecycles[version] = lifecycle
        self._save_extended_data()
        logger.info(f"开始版本生命周期: {version}")
        return lifecycle

    def update_lifecycle_status(self, version: str, status: VersionStatus) -> Optional[VersionLifecycle]:
        """更新生命周期状态"""
        if version not in self._lifecycles:
            return None

        lifecycle = self._lifecycles[version]
        old_status = lifecycle.status
        lifecycle.status = status

        milestone_map = {
            VersionStatus.DEVELOPMENT: 'development_start',
            VersionStatus.TESTING: 'testing_start',
            VersionStatus.RELEASE_CANDIDATE: 'rc_start',
            VersionStatus.RELEASED: 'released',
            VersionStatus.DEPRECATED: 'deprecated',
            VersionStatus.RETIRED: 'retired'
        }

        if status in milestone_map:
            lifecycle.milestones[milestone_map[status]] = datetime.now()

        if status == VersionStatus.RELEASED:
            lifecycle.actual_release = datetime.now()
            lifecycle.support_end = datetime.now() + timedelta(days=365)
            lifecycle.end_of_life = datetime.now() + timedelta(days=730)

        self._save_extended_data()
        logger.info(f"生命周期状态更新: {version} {old_status.value} -> {status.value}")
        return lifecycle

    def get_lifecycle(self, version: str) -> Optional[VersionLifecycle]:
        """获取版本生命周期"""
        return self._lifecycles.get(version)

    def list_active_versions(self) -> list[VersionLifecycle]:
        """列出活跃版本"""
        active_statuses = {VersionStatus.DEVELOPMENT, VersionStatus.TESTING, VersionStatus.RELEASE_CANDIDATE, VersionStatus.RELEASED}
        return [l for l in self._lifecycles.values() if l.status in active_statuses]

    def check_version_health(self) -> dict[str, Any]:
        """检查版本健康状态"""
        now = datetime.now()
        health = {
            'active_versions': [],
            'deprecated_versions': [],
            'eol_warnings': [],
            'recommendations': []
        }

        for lifecycle in self._lifecycles.values():
            if lifecycle.status == VersionStatus.RELEASED:
                health['active_versions'].append({
                    'version': lifecycle.version,
                    'released': lifecycle.actual_release.isoformat() if lifecycle.actual_release else None,
                    'support_end': lifecycle.support_end.isoformat() if lifecycle.support_end else None,
                    'eol': lifecycle.end_of_life.isoformat() if lifecycle.end_of_life else None
                })

                if lifecycle.support_end and lifecycle.support_end < now + timedelta(days=90):
                    health['eol_warnings'].append({
                        'version': lifecycle.version,
                        'type': 'support_ending',
                        'date': lifecycle.support_end.isoformat()
                    })

            elif lifecycle.status == VersionStatus.DEPRECATED:
                health['deprecated_versions'].append(lifecycle.version)

        if health['eol_warnings']:
            health['recommendations'].append('考虑升级即将结束支持的版本')

        return health

    def add_dependency(self, version: str, depends_on: list[str] = None, compatible_with: list[str] = None, conflicts_with: list[str] = None) -> VersionDependency:
        """添加版本依赖"""
        dep = VersionDependency(
            version=version,
            depends_on=depends_on or [],
            compatible_with=compatible_with or [],
            conflicts_with=conflicts_with or []
        )
        self._dependencies[version] = dep
        self._save_extended_data()
        logger.info(f"添加版本依赖: {version}")
        return dep

    def check_compatibility(self, version1: str, version2: str) -> dict[str, Any]:
        """检查版本兼容性"""
        dep1 = self._dependencies.get(version1)
        dep2 = self._dependencies.get(version2)

        result = {
            'version1': version1,
            'version2': version2,
            'compatible': True,
            'warnings': [],
            'errors': []
        }

        if dep1 and version2 in dep1.conflicts_with:
            result['compatible'] = False
            result['errors'].append(f"{version1} 与 {version2} 冲突")

        if dep2 and version1 in dep2.conflicts_with:
            result['compatible'] = False
            result['errors'].append(f"{version2} 与 {version1} 冲突")

        if dep1 and dep1.compatible_with and version2 not in dep1.compatible_with:
            result['warnings'].append(f"{version1} 未明确兼容 {version2}")

        if dep2 and dep2.compatible_with and version1 not in dep2.compatible_with:
            result['warnings'].append(f"{version2} 未明确兼容 {version1}")

        return result

    def generate_release_notes(self, version: str) -> str:
        """生成发布说明"""
        plan = self._release_plans.get(version)
        lifecycle = self._lifecycles.get(version)

        notes = f"# 发布说明 - {version}\n\n"

        if lifecycle:
            notes += f"**发布日期**: {lifecycle.actual_release.strftime('%Y-%m-%d') if lifecycle.actual_release else '待定'}\n"
            notes += f"**状态**: {lifecycle.status.value}\n\n"

        if plan:
            if plan.features:
                notes += "## 新功能\n\n"
                for feature in plan.features:
                    notes += f"- {feature}\n"
                notes += "\n"

            if plan.bugfixes:
                notes += "## 问题修复\n\n"
                for bugfix in plan.bugfixes:
                    notes += f"- {bugfix}\n"
                notes += "\n"

            if plan.breaking_changes:
                notes += "## 破坏性变更\n\n"
                for change in plan.breaking_changes:
                    notes += f"- ⚠️ {change}\n"
                notes += "\n"

            if plan.dependencies:
                notes += "## 依赖更新\n\n"
                for dep in plan.dependencies:
                    notes += f"- {dep}\n"
                notes += "\n"

            if plan.notes:
                notes += "## 备注\n\n"
                notes += plan.notes + "\n"

        return notes

    def schedule_release(self, version: str, target_date: datetime, release_type: ReleaseType = ReleaseType.MINOR) -> dict[str, Any]:
        """安排发布"""
        plan = self.create_release_plan(version, release_type, target_date)
        lifecycle = self.start_lifecycle(version)

        return {
            'version': version,
            'target_date': target_date.isoformat(),
            'release_type': release_type.value,
            'plan_created': True,
            'lifecycle_started': True
        }

    def get_upcoming_releases(self, days: int = 30) -> list[dict[str, Any]]:
        """获取即将发布的版本"""
        now = datetime.now()
        end_date = now + timedelta(days=days)
        upcoming = []

        for plan in self._release_plans.values():
            if plan.target_date >= now and plan.target_date <= end_date:
                upcoming.append({
                    'version': plan.version,
                    'target_date': plan.target_date.isoformat(),
                    'release_type': plan.release_type.value,
                    'status': plan.status.value,
                    'progress': plan.progress
                })

        return sorted(upcoming, key=lambda x: x['target_date'])
    
    def auto_generate_changelog(self, from_version: Optional[str] = None, to_version: Optional[str] = None) -> Dict[str, Any]:
        """自动生成变更日志
        
        从Git提交记录、发布计划和生命周期数据自动生成变更日志。
        
        Args:
            from_version: 起始版本
            to_version: 目标版本
            
        Returns:
            生成的变更日志数据
        """
        current = self.get_current_version()
        from_v = from_version or str(current)
        to_v = to_version or str(current)
        
        changelog = {
            "version": to_v,
            "generated_at": datetime.now().isoformat(),
            "sections": {
                "features": [],
                "bugfixes": [],
                "breaking_changes": [],
                "improvements": [],
                "dependencies": [],
                "documentation": []
            },
            "contributors": set(),
            "commits": []
        }
        
        git_commits = self._get_detailed_git_commits(from_v, to_v)
        for commit in git_commits:
            changelog["commits"].append(commit)
            changelog["contributors"].add(commit.get("author", "unknown"))
            
            message = commit.get("message", "").lower()
            
            if message.startswith("feat:") or message.startswith("feature:"):
                changelog["sections"]["features"].append({
                    "description": commit["message"],
                    "commit": commit["hash"],
                    "author": commit.get("author", "")
                })
            elif message.startswith("fix:") or message.startswith("bugfix:"):
                changelog["sections"]["bugfixes"].append({
                    "description": commit["message"],
                    "commit": commit["hash"],
                    "author": commit.get("author", "")
                })
            elif message.startswith("breaking:") or message.startswith("break:"):
                changelog["sections"]["breaking_changes"].append({
                    "description": commit["message"],
                    "commit": commit["hash"],
                    "author": commit.get("author", "")
                })
            elif message.startswith("docs:") or message.startswith("doc:"):
                changelog["sections"]["documentation"].append({
                    "description": commit["message"],
                    "commit": commit["hash"],
                    "author": commit.get("author", "")
                })
            elif message.startswith("dep:") or message.startswith("deps:"):
                changelog["sections"]["dependencies"].append({
                    "description": commit["message"],
                    "commit": commit["hash"],
                    "author": commit.get("author", "")
                })
            else:
                changelog["sections"]["improvements"].append({
                    "description": commit["message"],
                    "commit": commit["hash"],
                    "author": commit.get("author", "")
                })
        
        plan = self._release_plans.get(to_v)
        if plan:
            for feature in plan.features:
                if not any(f["description"] == feature for f in changelog["sections"]["features"]):
                    changelog["sections"]["features"].append({
                        "description": feature,
                        "source": "release_plan"
                    })
            
            for bugfix in plan.bugfixes:
                if not any(f["description"] == bugfix for f in changelog["sections"]["bugfixes"]):
                    changelog["sections"]["bugfixes"].append({
                        "description": bugfix,
                        "source": "release_plan"
                    })
        
        changelog["contributors"] = list(changelog["contributors"])
        changelog["summary"] = {
            "total_commits": len(changelog["commits"]),
            "total_contributors": len(changelog["contributors"]),
            "features_count": len(changelog["sections"]["features"]),
            "bugfixes_count": len(changelog["sections"]["bugfixes"]),
            "breaking_changes_count": len(changelog["sections"]["breaking_changes"])
        }
        
        return changelog
    
    def _get_detailed_git_commits(self, from_version: str, to_version: str) -> List[Dict[str, Any]]:
        """获取详细的Git提交记录
        
        Args:
            from_version: 起始版本
            to_version: 目标版本
            
        Returns:
            提交记录列表
        """
        commits = []
        
        try:
            from_tag = f"v{from_version}" if not from_version.startswith("v") else from_version
            to_ref = f"v{to_version}" if not to_version.startswith("v") else to_version
            
            result = subprocess.run(
                ['git', 'log', f'{from_tag}..{to_ref}', '--pretty=format:%H|%s|%an|%ad', '--date=short'],
                capture_output=True,
                text=True,
                check=False
            )
            
            if result.returncode == 0:
                for line in result.stdout.strip().split('\n'):
                    if line:
                        parts = line.split('|')
                        if len(parts) >= 4:
                            commits.append({
                                "hash": parts[0],
                                "message": parts[1],
                                "author": parts[2],
                                "date": parts[3]
                            })
            else:
                result = subprocess.run(
                    ['git', 'log', '-20', '--pretty=format:%H|%s|%an|%ad', '--date=short'],
                    capture_output=True,
                    text=True,
                    check=False
                )
                if result.returncode == 0:
                    for line in result.stdout.strip().split('\n'):
                        if line:
                            parts = line.split('|')
                            if len(parts) >= 4:
                                commits.append({
                                    "hash": parts[0],
                                    "message": parts[1],
                                    "author": parts[2],
                                    "date": parts[3]
                                })
                                
        except FileNotFoundError:
            logger.warning("Git命令未找到，无法获取提交记录")
        except Exception as e:
            logger.warning(f"获取Git提交记录失败: {e}")
        
        return commits
    
    def write_changelog_file(self, changelog: Dict[str, Any], output_path: Optional[Path] = None) -> None:
        """将变更日志写入文件
        
        Args:
            changelog: 变更日志数据
            output_path: 输出文件路径
        """
        path = output_path or self.config.changelog_file or Path("CHANGELOG.md")
        path.parent.mkdir(parents=True, exist_ok=True)
        
        lines = [
            f"# 变更日志",
            f"",
            f"## [{changelog['version']}] - {datetime.now().strftime('%Y-%m-%d')}",
            f""
        ]
        
        sections = changelog.get("sections", {})
        
        if sections.get("features"):
            lines.append("### ✨ 新功能")
            lines.append("")
            for item in sections["features"]:
                desc = item.get("description", "")
                if desc.startswith("feat:"):
                    desc = desc[5:].strip()
                elif desc.startswith("feature:"):
                    desc = desc[8:].strip()
                lines.append(f"- {desc}")
                if item.get("commit"):
                    lines.append(f"  - 提交: `{item['commit'][:8]}`")
            lines.append("")
        
        if sections.get("bugfixes"):
            lines.append("### 🐛 问题修复")
            lines.append("")
            for item in sections["bugfixes"]:
                desc = item.get("description", "")
                if desc.startswith("fix:"):
                    desc = desc[4:].strip()
                elif desc.startswith("bugfix:"):
                    desc = desc[7:].strip()
                lines.append(f"- {desc}")
                if item.get("commit"):
                    lines.append(f"  - 提交: `{item['commit'][:8]}`")
            lines.append("")
        
        if sections.get("breaking_changes"):
            lines.append("### ⚠️ 破坏性变更")
            lines.append("")
            for item in sections["breaking_changes"]:
                desc = item.get("description", "")
                if desc.startswith("breaking:"):
                    desc = desc[9:].strip()
                elif desc.startswith("break:"):
                    desc = desc[6:].strip()
                lines.append(f"- {desc}")
            lines.append("")
        
        if sections.get("improvements"):
            lines.append("### 🔧 改进")
            lines.append("")
            for item in sections["improvements"][:10]:
                lines.append(f"- {item.get('description', '')}")
            lines.append("")
        
        if sections.get("dependencies"):
            lines.append("### 📦 依赖更新")
            lines.append("")
            for item in sections["dependencies"]:
                lines.append(f"- {item.get('description', '')}")
            lines.append("")
        
        summary = changelog.get("summary", {})
        lines.append("---")
        lines.append("")
        lines.append(f"**统计**: {summary.get('total_commits', 0)} 个提交, {summary.get('total_contributors', 0)} 位贡献者")
        lines.append("")
        
        if path.exists():
            with open(path, 'r', encoding='utf-8') as f:
                existing = f.read()
            
            header_end = existing.find("## [")
            if header_end > 0:
                new_content = existing[:header_end] + "\n".join(lines) + existing[header_end:]
            else:
                new_content = "\n".join(lines) + existing
        else:
            new_content = "\n".join(lines)
        
        with open(path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        
        logger.info(f"变更日志已写入: {path}")
    
    def auto_release(self, version: Optional[str] = None, release_type: ReleaseType = ReleaseType.MINOR) -> Dict[str, Any]:
        """自动发布流程
        
        执行完整的自动发布流程，包括：
        1. 版本号更新
        2. 变更日志生成
        3. Git标签创建
        4. 发布说明生成
        
        Args:
            version: 目标版本号，如果不指定则自动递增
            release_type: 发布类型
            
        Returns:
            发布结果
        """
        result = {
            "status": "started",
            "steps": [],
            "errors": []
        }
        
        try:
            if version:
                new_version = self.set_version(version, f"自动发布 {version}")
            else:
                part_map = {
                    ReleaseType.MAJOR: VersionPart.MAJOR,
                    ReleaseType.MINOR: VersionPart.MINOR,
                    ReleaseType.PATCH: VersionPart.PATCH,
                    ReleaseType.HOTFIX: VersionPart.PATCH
                }
                part = part_map.get(release_type, VersionPart.PATCH)
                new_version = self.bump_version(part, f"自动发布 {release_type.value}")
            
            result["steps"].append({
                "step": "version_update",
                "status": "success",
                "version": str(new_version)
            })
            
            changelog = self.auto_generate_changelog()
            self.write_changelog_file(changelog)
            
            result["steps"].append({
                "step": "changelog_generation",
                "status": "success",
                "commits": changelog.get("summary", {}).get("total_commits", 0)
            })
            
            self.config.git_tag = True
            self.config.git_commit = True
            self._git_tag(new_version)
            
            result["steps"].append({
                "step": "git_tag",
                "status": "success",
                "tag": f"v{new_version}"
            })
            
            release_notes = self.generate_release_notes(str(new_version))
            notes_path = self.config.version_file.parent / "release_notes" / f"v{new_version}.md"
            notes_path.parent.mkdir(parents=True, exist_ok=True)
            with open(notes_path, 'w', encoding='utf-8') as f:
                f.write(release_notes)
            
            result["steps"].append({
                "step": "release_notes",
                "status": "success",
                "path": str(notes_path)
            })
            
            self.update_lifecycle_status(str(new_version), VersionStatus.RELEASED)
            
            result["steps"].append({
                "step": "lifecycle_update",
                "status": "success",
                "new_status": "released"
            })
            
            result["status"] = "success"
            result["version"] = str(new_version)
            
        except Exception as e:
            result["status"] = "failed"
            result["errors"].append(str(e))
            logger.error(f"自动发布失败: {e}")
        
        return result
    
    def prepare_release(self, version: str, release_type: ReleaseType = ReleaseType.MINOR, target_date: Optional[datetime] = None) -> Dict[str, Any]:
        """准备发布
        
        创建发布计划并初始化生命周期。
        
        Args:
            version: 版本号
            release_type: 发布类型
            target_date: 目标发布日期
            
        Returns:
            准备结果
        """
        target = target_date or datetime.now() + timedelta(days=7)
        
        plan = self.create_release_plan(version, release_type, target)
        lifecycle = self.start_lifecycle(version)
        
        return {
            "status": "prepared",
            "version": version,
            "release_type": release_type.value,
            "target_date": target.isoformat(),
            "plan": {
                "features": plan.features,
                "bugfixes": plan.bugfixes,
                "breaking_changes": plan.breaking_changes
            },
            "lifecycle": {
                "status": lifecycle.status.value,
                "created_at": lifecycle.created_at.isoformat()
            }
        }
    
    def get_release_status(self, version: Optional[str] = None) -> Dict[str, Any]:
        """获取发布状态
        
        Args:
            version: 版本号，如果不指定则使用当前版本
            
        Returns:
            发布状态信息
        """
        ver = version or str(self.get_current_version())
        
        plan = self._release_plans.get(ver)
        lifecycle = self._lifecycles.get(ver)
        dependency = self._dependencies.get(ver)
        
        status = {
            "version": ver,
            "current": ver == str(self.get_current_version()),
            "plan": None,
            "lifecycle": None,
            "dependencies": None
        }
        
        if plan:
            status["plan"] = {
                "release_type": plan.release_type.value,
                "target_date": plan.target_date.isoformat(),
                "status": plan.status.value,
                "progress": plan.progress,
                "features_count": len(plan.features),
                "bugfixes_count": len(plan.bugfixes)
            }
        
        if lifecycle:
            status["lifecycle"] = {
                "status": lifecycle.status.value,
                "created_at": lifecycle.created_at.isoformat(),
                "planned_release": lifecycle.planned_release.isoformat() if lifecycle.planned_release else None,
                "actual_release": lifecycle.actual_release.isoformat() if lifecycle.actual_release else None,
                "milestones": {k: v.isoformat() for k, v in lifecycle.milestones.items()}
            }
        
        if dependency:
            status["dependencies"] = {
                "depends_on": dependency.depends_on,
                "compatible_with": dependency.compatible_with,
                "conflicts_with": dependency.conflicts_with
            }
        
        return status
    
    def rollback_release(self, version: str) -> Dict[str, Any]:
        """回滚发布
        
        将发布状态回滚到之前的状态。
        
        Args:
            version: 要回滚的版本号
            
        Returns:
            回滚结果
        """
        result = {
            "status": "started",
            "version": version,
            "steps": []
        }
        
        try:
            lifecycle = self._lifecycles.get(version)
            if lifecycle:
                old_status = lifecycle.status
                self.update_lifecycle_status(version, VersionStatus.DEPRECATED)
                result["steps"].append({
                    "step": "lifecycle_rollback",
                    "from": old_status.value,
                    "to": "deprecated"
                })
            
            try:
                subprocess.run(['git', 'tag', '-d', f'v{version}'], check=False, capture_output=True)
                result["steps"].append({
                    "step": "tag_deletion",
                    "tag": f"v{version}",
                    "status": "success"
                })
            except Exception as e:
                result["steps"].append({
                    "step": "tag_deletion",
                    "status": "failed",
                    "error": str(e)
                })
            
            history = self.get_version_history()
            if history:
                prev_version = None
                for i, entry in enumerate(history):
                    if entry["version"] == version and i > 0:
                        prev_version = history[i - 1]["version"]
                        break
                
                if prev_version:
                    self.set_version(prev_version, f"回滚到 {prev_version}")
                    result["steps"].append({
                        "step": "version_rollback",
                        "to": prev_version
                    })
            
            result["status"] = "success"
            
        except Exception as e:
            result["status"] = "failed"
            result["error"] = str(e)
        
        return result


def parse_args() -> tuple[str, VersionConfig, Any]:
    """解析命令行参数"""
    parser = argparse.ArgumentParser(
        description="版本号管理脚本 - Sanliu 技能",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 查看当前版本
  python scripts/version_manager.py current

  # 递增补丁版本
  python scripts/version_manager.py bump patch

  # 递增次要版本并生成变更日志
  python scripts/version_manager.py bump minor --changelog

  # 设置特定版本
  python scripts/version_manager.py set 1.2.3

  # 比较两个版本
  python scripts/version_manager.py compare 1.0.0 1.2.0

  # 验证版本号格式
  python scripts/version_manager.py validate 1.2.3-beta

  # 查看版本历史
  python scripts/version_manager.py history

  # 创建发布计划
  python scripts/version_manager.py plan 1.1.0 --type minor --date 2024-06-01

  # 查看生命周期状态
  python scripts/version_manager.py lifecycle status

  # 更新生命周期状态
  python scripts/version_manager.py lifecycle update 1.0.0 --status released

  # 检查版本健康
  python scripts/version_manager.py health

  # 添加版本依赖
  python scripts/version_manager.py dependency 1.1.0 --depends 1.0.0

  # 检查版本兼容性
  python scripts/version_manager.py compatibility 1.0.0 1.1.0

  # 生成发布说明
  python scripts/version_manager.py release-notes 1.0.0

  # 查看即将发布的版本
  python scripts/version_manager.py upcoming --days 30
        """
    )

    subparsers = parser.add_subparsers(dest='command', help='可用命令')

    current_parser = subparsers.add_parser('current', help='显示当前版本')

    bump_parser = subparsers.add_parser('bump', help='递增版本号')
    bump_parser.add_argument(
        'part',
        choices=['major', 'minor', 'patch'],
        help='要递增的版本部分'
    )
    bump_parser.add_argument(
        '--message', '-m',
        help='变更说明'
    )
    bump_parser.add_argument(
        '--changelog', '-c',
        action='store_true',
        help='更新变更日志'
    )
    bump_parser.add_argument(
        '--git-tag', '-t',
        action='store_true',
        help='创建 Git 标签'
    )
    bump_parser.add_argument(
        '--git-commit',
        action='store_true',
        help='创建 Git 提交'
    )

    set_parser = subparsers.add_parser('set', help='设置特定版本')
    set_parser.add_argument('version', help='版本号')
    set_parser.add_argument('--message', '-m', help='变更说明')

    compare_parser = subparsers.add_parser('compare', help='比较两个版本')
    compare_parser.add_argument('version1', help='第一个版本')
    compare_parser.add_argument('version2', help='第二个版本')

    validate_parser = subparsers.add_parser('validate', help='验证版本号格式')
    validate_parser.add_argument('version', help='要验证的版本号')

    subparsers.add_parser('history', help='显示版本历史')

    plan_parser = subparsers.add_parser('plan', help='创建发布计划')
    plan_parser.add_argument('version', help='版本号')
    plan_parser.add_argument('--type', choices=['major', 'minor', 'patch', 'hotfix', 'beta', 'alpha'], default='minor', help='发布类型')
    plan_parser.add_argument('--date', required=True, help='目标发布日期 (YYYY-MM-DD)')
    plan_parser.add_argument('--feature', action='append', help='新功能 (可多次使用)')
    plan_parser.add_argument('--notes', help='备注')

    lifecycle_parser = subparsers.add_parser('lifecycle', help='生命周期管理')
    lifecycle_parser.add_argument('action', choices=['status', 'update', 'list', 'start'], help='生命周期操作')
    lifecycle_parser.add_argument('--version', help='版本号')
    lifecycle_parser.add_argument('--status', choices=['planned', 'development', 'testing', 'rc', 'released', 'deprecated', 'retired'], help='新状态')

    subparsers.add_parser('health', help='检查版本健康状态')

    dependency_parser = subparsers.add_parser('dependency', help='版本依赖管理')
    dependency_parser.add_argument('version', help='版本号')
    dependency_parser.add_argument('--depends', action='append', help='依赖版本 (可多次使用)')
    dependency_parser.add_argument('--compatible', action='append', help='兼容版本 (可多次使用)')
    dependency_parser.add_argument('--conflicts', action='append', help='冲突版本 (可多次使用)')

    compatibility_parser = subparsers.add_parser('compatibility', help='检查版本兼容性')
    compatibility_parser.add_argument('version1', help='第一个版本')
    compatibility_parser.add_argument('version2', help='第二个版本')

    release_notes_parser = subparsers.add_parser('release-notes', help='生成发布说明')
    release_notes_parser.add_argument('version', help='版本号')

    upcoming_parser = subparsers.add_parser('upcoming', help='查看即将发布的版本')
    upcoming_parser.add_argument('--days', type=int, default=30, help='查看未来N天 (默认: 30)')

    parser.add_argument(
        '--version-file',
        type=Path,
        default=Path('version.json'),
        help='版本号文件路径 (默认: version.json)'
    )

    parser.add_argument(
        '--changelog-file',
        type=Path,
        help='变更日志文件路径'
    )

    parser.add_argument(
        '--package-files',
        nargs='+',
        type=Path,
        default=[],
        help='要更新的 package 文件列表'
    )

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    config = VersionConfig(
        version_file=args.version_file,
        changelog_file=args.changelog_file,
        package_files=args.package_files
    )

    if args.command == 'bump':
        config.git_tag = getattr(args, 'git_tag', False)
        config.git_commit = getattr(args, 'git_commit', False)
        if getattr(args, 'changelog', False):
            config.changelog_file = args.changelog_file or Path('CHANGELOG.md')

    return args.command, config, args


def main():
    """主入口函数"""
    try:
        command, config, args = parse_args()
        manager = VersionManager(config)

        if command == 'current':
            version = manager.get_current_version()
            print(f"\n当前版本: {version}")

        elif command == 'bump':
            part = VersionPart(args.part)
            message = getattr(args, 'message', '') or ""
            new_version = manager.bump_version(part, message)
            print(f"\n版本已更新: {new_version}")

        elif command == 'set':
            message = getattr(args, 'message', '') or ""
            new_version = manager.set_version(args.version, message)
            print(f"\n版本已设置: {new_version}")

        elif command == 'compare':
            result = manager.compare_versions(args.version1, args.version2)
            print(f"\n版本比较:")
            print(f"  {result['version1']} vs {result['version2']}")
            print(f"  相等: {result['equal']}")
            print(f"  小于: {result['less_than']}")
            print(f"  大于: {result['greater_than']}")
            if not result['equal']:
                diff = result['difference']
                print(f"  差异: major={diff['major']}, minor={diff['minor']}, patch={diff['patch']}")

        elif command == 'validate':
            result = manager.validate_version(args.version)
            print(f"\n版本验证:")
            if result['valid']:
                print(f"  ✓ 有效的版本号: {result['version']}")
                parts = result['parts']
                print(f"  主版本: {parts['major']}")
                print(f"  次版本: {parts['minor']}")
                print(f"  补丁版本: {parts['patch']}")
                if parts['prerelease']:
                    print(f"  预发布: {parts['prerelease']}")
                if parts['build']:
                    print(f"  构建: {parts['build']}")
            else:
                print(f"  ✗ 无效的版本号")
                print(f"  错误: {result['error']}")

        elif command == 'history':
            history = manager.get_version_history()
            print(f"\n版本历史:")
            if history:
                for entry in history:
                    print(f"  {entry['version']} ({entry['date']})")
            else:
                print("  暂无版本历史记录")

        elif command == 'plan':
            target_date = datetime.strptime(args.date, '%Y-%m-%d')
            release_type = ReleaseType(args.type)
            plan = manager.create_release_plan(
                version=args.version,
                release_type=release_type,
                target_date=target_date,
                features=args.feature or [],
                notes=args.notes or ""
            )
            print(f"\n发布计划已创建:")
            print(f"  版本: {plan.version}")
            print(f"  类型: {plan.release_type.value}")
            print(f"  目标日期: {plan.target_date.strftime('%Y-%m-%d')}")
            if plan.features:
                print(f"  新功能: {', '.join(plan.features)}")

        elif command == 'lifecycle':
            action = args.action
            if action == 'status':
                version = args.version or str(manager.get_current_version())
                lifecycle = manager.get_lifecycle(version)
                if lifecycle:
                    print(f"\n版本 {version} 生命周期状态:")
                    print(f"  状态: {lifecycle.status.value}")
                    print(f"  创建时间: {lifecycle.created_at.strftime('%Y-%m-%d')}")
                    if lifecycle.planned_release:
                        print(f"  计划发布: {lifecycle.planned_release.strftime('%Y-%m-%d')}")
                    if lifecycle.actual_release:
                        print(f"  实际发布: {lifecycle.actual_release.strftime('%Y-%m-%d')}")
                    if lifecycle.end_of_life:
                        print(f"  生命周期结束: {lifecycle.end_of_life.strftime('%Y-%m-%d')}")
                else:
                    print(f"\n版本 {version} 暂无生命周期记录")

            elif action == 'update':
                if not args.version or not args.status:
                    print("错误: 需要指定 --version 和 --status")
                    sys.exit(1)
                status = VersionStatus(args.status)
                lifecycle = manager.update_lifecycle_status(args.version, status)
                if lifecycle:
                    print(f"\n版本 {args.version} 状态已更新为: {status.value}")
                else:
                    print(f"\n版本 {args.version} 不存在")

            elif action == 'list':
                active = manager.list_active_versions()
                print(f"\n活跃版本:")
                for lc in active:
                    print(f"  {lc.version} - {lc.status.value}")

            elif action == 'start':
                version = args.version or str(manager.get_current_version())
                lifecycle = manager.start_lifecycle(version)
                print(f"\n版本 {version} 生命周期已开始")

        elif command == 'health':
            health = manager.check_version_health()
            print(f"\n版本健康状态:")
            print(f"  活跃版本: {len(health['active_versions'])}")
            for ver in health['active_versions']:
                print(f"    - {ver['version']}")
            print(f"  已弃用版本: {len(health['deprecated_versions'])}")
            for ver in health['deprecated_versions']:
                print(f"    - {ver}")
            if health['eol_warnings']:
                print(f"  ⚠️ 生命周期警告:")
                for warning in health['eol_warnings']:
                    print(f"    - {warning['version']}: {warning['type']} on {warning['date']}")
            if health['recommendations']:
                print(f"  建议:")
                for rec in health['recommendations']:
                    print(f"    - {rec}")

        elif command == 'dependency':
            dep = manager.add_dependency(
                version=args.version,
                depends_on=args.depends,
                compatible_with=args.compatible,
                conflicts_with=args.conflicts
            )
            print(f"\n版本依赖已添加:")
            print(f"  版本: {dep.version}")
            if dep.depends_on:
                print(f"  依赖: {', '.join(dep.depends_on)}")
            if dep.compatible_with:
                print(f"  兼容: {', '.join(dep.compatible_with)}")
            if dep.conflicts_with:
                print(f"  冲突: {', '.join(dep.conflicts_with)}")

        elif command == 'compatibility':
            result = manager.check_compatibility(args.version1, args.version2)
            print(f"\n版本兼容性检查:")
            print(f"  {result['version1']} vs {result['version2']}")
            print(f"  兼容: {'✓ 是' if result['compatible'] else '✗ 否'}")
            if result['warnings']:
                print(f"  警告:")
                for warning in result['warnings']:
                    print(f"    - {warning}")
            if result['errors']:
                print(f"  错误:")
                for error in result['errors']:
                    print(f"    - {error}")

        elif command == 'release-notes':
            notes = manager.generate_release_notes(args.version)
            print(notes)

        elif command == 'upcoming':
            days = args.days
            upcoming = manager.get_upcoming_releases(days)
            print(f"\n未来 {days} 天即将发布的版本:")
            if upcoming:
                for release in upcoming:
                    print(f"  {release['version']} - {release['target_date'][:10]} - {release['release_type']} - {release['progress']*100:.0f}% 完成")
            else:
                print("  暂无即将发布的版本")

        sys.exit(0)

    except KeyboardInterrupt:
        logger.info("用户中断执行")
        sys.exit(130)
    except Exception as e:
        logger.error(f"执行失败: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
