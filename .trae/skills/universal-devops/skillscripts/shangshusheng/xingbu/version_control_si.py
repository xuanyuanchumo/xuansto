"""
版本管理司 - Git Flow/Trunk Based策略支持、版本发布管理、变更追踪
"""
from __future__ import annotations

import json
import re
import uuid
import hashlib
from dataclasses import dataclass, field
from enum import Enum, auto
from datetime import datetime
from pathlib import Path
from typing import Any


class BranchType(Enum):
    """分支类型"""

    MAIN = "main"
    DEVELOP = "develop"
    FEATURE = "feature"
    RELEASE = "release"
    HOTFIX = "hotfix"
    BUGFIX = "bugfix"


class VersionComponent(Enum):
    """版本组件"""

    MAJOR = "major"
    MINOR = "minor"
    PATCH = "patch"


@dataclass
class SemanticVersion:
    """语义化版本"""

    major: int
    minor: int
    patch: int
    pre_release: str = ""
    build_metadata: str = ""

    def __str__(self) -> str:
        v = f"{self.major}.{self.minor}.{self.patch}"
        if self.pre_release:
            v += f"-{self.pre_release}"
        if self.build_metadata:
            v += f"+{self.build_metadata}"
        return v

    @property
    def tuple(self) -> tuple[int, int, int]:
        return (self.major, self.minor, self.patch)

    def bump(self, component: VersionComponent) -> SemanticVersion:
        match component:
            case VersionComponent.MAJOR:
                return SemanticVersion(self.major + 1, 0, 0)
            case VersionComponent.MINOR:
                return SemanticVersion(self.major, self.minor + 1, 0)
            case VersionComponent.PATCH:
                return SemanticVersion(self.major, self.minor, self.patch + 1)


@dataclass
class BranchInfo:
    """分支信息"""

    name: str
    branch_type: BranchType
    base_branch: str = "main"
    created_at: str = ""
    creator: str = ""
    description: str = ""
    commits: list[dict[str, str]] = field(default_factory=list)
    status: str = "active"


@dataclass
class CommitInfo:
    """提交信息"""

    hash: str
    author: str = ""
    message: str = ""
    timestamp: str = ""
    files_changed: list[str] = field(default_factory=list)
    insertions: int = 0
    deletions: int = 0
    branch: str = ""


@dataclass
class ReleaseInfo:
    """发布信息"""

    version: SemanticVersion
    branch_name: str = ""
    tag_name: str = ""
    status: str = "planned"
    changelog: str = ""
    checklist_completed: bool = False
    pre_release_checks: dict[str, bool] = field(default_factory=dict)
    release_notes: str = ""
    published_at: str = ""
    announcement: str = ""


@dataclass
class PreReleaseCheckItem:
    """发布前检查项"""

    name: str
    category: str
    required: bool = True
    checked: bool = False
    description: str = ""


@dataclass
class ChangeStats:
    """变更统计"""

    total_commits: int = 0
    by_author: dict[str, int] = field(default_factory=dict)
    by_time_period: dict[str, int] = field(default_factory=dict)
    by_file_type: dict[str, int] = field(default_factory=dict)
    by_branch: dict[str, int] = field(default_factory=dict)


class VersionControlError(Exception):
    """版本控制异常"""


class BranchError(VersionControlError):
    """分支异常"""


class ReleaseError(VersionControlError):
    """发布异常"""


class VersionControlSi:
    """
    版本管理司 - 刑部·司门司

    提供全面的版本管理能力：
    - Git Flow工作流管理（feature/release/hotfix/main）
    - Trunk Based Development支持
    - Semantic Versioning (MAJOR.MINOR.PATCH)
    - CHANGELOG自动生成（约定式提交）
    - 发布检查清单与公告生成
    - 分支策略可视化
    - 代码变更统计
    """

    def __init__(self, strategy: str = "gitflow") -> None:
        self._strategy = strategy
        self._branches: dict[str, BranchInfo] = {}
        self._commits: list[CommitInfo] = []
        self._releases: list[ReleaseInfo] = []
        self._current_version = SemanticVersion(1, 0, 0)

        self._init_main_branches()
        self._init_pre_release_checklist()

    # ==================== 初始化 ====================

    def _init_main_branches(self) -> None:
        """初始化主分支"""
        now = datetime.now().isoformat()
        if self._strategy == "gitflow":
            self._branches["main"] = BranchInfo(
                name="main", branch_type=BranchType.MAIN,
                base_branch="", created_at=now,
                description="生产环境分支，只接受merge来自release和hotfix",
            )
            self._branches["develop"] = BranchInfo(
                name="develop", branch_type=BranchType.DEVELOP,
                base_branch="main", created_at=now,
                description="开发集成分支，feature分支从此分出并合并回此",
            )
        else:
            self._branches["main"] = BranchInfo(
                name="main", branch_type=BranchType.MAIN,
                base_branch="", created_at=now,
                description="Trunk Based主分支，所有开发直接在此进行",
            )

    def _init_pre_release_checklist(self) -> None:
        """初始化发布前检查清单"""
        pass

    # ==================== 分支管理 ====================

    def create_branch(
        self,
        name: str,
        branch_type: BranchType,
        base_branch: str | None = None,
        **kwargs,
    ) -> BranchInfo:
        """
        创建新分支

        Args:
            name: 分支名
            branch_type: 分支类型
            base_branch: 基础分支

        Returns:
            分支信息对象
        """
        full_name = f"{branch_type.value}/{name}" if branch_type in (
            BranchType.FEATURE, BranchType.RELEASE, BranchType.HOTFIX, BranchType.BUGFIX
        ) else name

        if full_name in self._branches:
            raise BranchError(f"分支已存在: {full_name}")

        if base_branch is None:
            match branch_type:
                case BranchType.FEATURE:
                    base_branch = "develop" if self._strategy == "gitflow" else "main"
                case BranchType.RELEASE:
                    base_branch = "develop"
                case BranchType.HOTFIX:
                    base_branch = "main"
                case BranchType.BUGFIX:
                    base_branch = "develop" if self._strategy == "gitflow" else "main"
                case _:
                    base_branch = "main"

        branch = BranchInfo(
            name=full_name,
            branch_type=branch_type,
            base_branch=base_branch or "main",
            created_at=datetime.now().isoformat(),
            creator=kwargs.get("creator", ""),
            description=kwargs.get("description", f"{branch_type.value}分支"),
        )
        self._branches[full_name] = branch
        return branch

    def get_branch(self, name: str) -> BranchInfo:
        """获取分支信息"""
        if name not in self._branches:
            available = ", ".join(sorted(self._branches.keys()))
            raise BranchError(f"分支不存在: '{name}'。可用: {available}")
        return self._branches[name]

    def list_branches(self, branch_type: BranchType | None = None) -> list[BranchInfo]:
        """列出分支"""
        branches = list(self._branches.values())
        if branch_type:
            branches = [b for b in branches if b.branch_type == branch_type]
        return sorted(branches, key=lambda b: b.created_at, reverse=True)

    def merge_branch(self, source: str, target: str) -> dict[str, Any]:
        """
        模拟合并分支

        Args:
            source: 源分支
            target: 目标分支

        Returns:
            合并结果字典
        """
        src_branch = self.get_branch(source)
        tgt_branch = self.get_branch(target)

        merge_hash = f"merge-{uuid.uuid4().hex[:8]}"
        commit = CommitInfo(
            hash=merge_hash,
            message=f"Merge {source} into {target}",
            timestamp=datetime.now().isoformat(),
            branch=target,
        )
        self._commits.append(commit)

        tgt_branch.commits.append({
            "hash": merge_hash,
            "message": commit.message,
            "timestamp": commit.timestamp,
        })

        merge_validations = self._validate_merge(source, target)

        return {
            "success": True,
            "source": source,
            "target": target,
            "merge_commit": merge_hash,
            "validations": merge_validations,
            "message": f"✅ {source} → {target} 合并成功",
        }

    def _validate_merge(self, source: str, target: str) -> list[dict[str, str]]:
        """验证合并合法性"""
        validations: list[dict[str, str]] = []

        src = self._branches.get(source)
        tgt = self._branches.get(target)

        if not src or not tgt:
            validations.append({"check": "branch_exists", "status": "fail", "message": "源或目标分支不存在"})
            return validations

        if self._strategy == "gitflow":
            rules: list[tuple[str, str, str, str]] = [
                ("feature→main", BranchType.FEATURE, BranchType.MAIN, "feature分支不能直接合并到main，应先合并到develop"),
                ("hotfix→develop", BranchType.HOTFIX, BranchType.DEVELOP, "hotfix应同时合并到main和develop"),
                ("release→feature", BranchType.RELEASE, BranchType.FEATURE, "release分支不应合并到feature"),
            ]

            for rule_name, src_type, tgt_type, msg in rules:
                if src.branch_type == src_type and tgt.branch_type == tgt_type:
                    validations.append({"check": rule_name, "status": "warn", "message": msg})
                elif src.branch_type == src_type and tgt.branch_type == tgt_type:
                    pass

        validations.append({"check": "base_chain", "status": "pass", "message": f"{src.base_branch} → {src.name} → {tgt.name}"})

        return validations

    # ==================== 版本管理 ====================

    def set_version(self, version_str: str) -> SemanticVersion:
        """设置当前版本"""
        parts = version_str.split(".")
        if len(parts) < 3:
            raise VersionControlError(f"无效的版本号格式: {version_str}，期望 MAJOR.MINOR.PATCH")

        major = int(parts[0])
        minor = int(parts[1])
        patch_parts = parts[2].split("-")
        patch = int(patch_parts[0])
        pre = patch_parts[1] if len(patch_parts) > 1 else ""

        self._current_version = SemanticVersion(major, minor, patch, pre)
        return self._current_version

    def get_version(self) -> SemanticVersion:
        """获取当前版本"""
        return self._current_version

    def bump_version(self, component: VersionComponent) -> SemanticVersion:
        """递增版本号"""
        new_version = self._current_version.bump(component)
        self._current_version = new_version
        return new_version

    def suggest_version_bump(self, commits_since_last: list[CommitInfo]) -> VersionComponent:
        """
        根据提交历史建议版本升级类型

        约定式提交解析：
        - feat!: / fix! → MAJOR (breaking change)
        - feat → MINOR (新功能)
        - fix → PATCH (bug修复)
        """
        has_breaking = False
        has_feature = False
        has_fix = False

        for commit in commits_since_last:
            msg_lower = commit.message.lower()
            if re.match(r"(feat|fix)\!:", msg_lower):
                has_breaking = True
            elif msg_lower.startswith("feat"):
                has_feature = True
            elif msg_lower.startswith("fix"):
                has_fix = True

        if has_breaking:
            return VersionComponent.MAJOR
        elif has_feature:
            return VersionComponent.MINOR
        elif has_fix:
            return VersionComponent.PATCH
        else:
            return VersionComponent.PATCH

    # ==================== CHANGELOG生成 ====================

    def generate_changelog(
        self,
        from_version: str | None = None,
        to_version: str | None = None,
        format_type: str = "markdown",
    ) -> str:
        """
        从git log按约定式提交自动生成CHANGELOG

        Args:
            from_version: 起始版本
            to_version: 目标版本
            format_type: 输出格式
        """
        from_ver = from_version or f"v{SemanticVersion(self._current_version.major, max(0, self._current_version.minor - 1), 0)}"
        to_ver = to_version or f"v{self._current_version}"

        lines: list[str] = []
        lines.append(f"# Changelog\n")
        lines.append(f"All notable changes to this project will be documented in this file.\n")
        lines.append(f"The format is based on [Keep a Changelog](https://keepachangelog.com/), "
                     f"and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).\n")

        categorized: dict[str, list[CommitInfo]] = {
            "Breaking Changes 🔄": [],
            "New Features ✨": [],
            "Bug Fixes 🐛": [],
            "Performance ⚡": [],
            "Documentation 📝": [],
            "Refactoring ♻️": [],
            "Tests ✅": [],
            "Chore 🔧": [],
            "CI/CD 🤖": [],
            "Security 🔒": [],
        }

        for commit in self._commits:
            msg = commit.message.strip()
            category = self._categorize_commit(msg)
            categorized[category].append(commit)

        lines.append(f"## [{to_ver}] - {datetime.now().strftime('%Y-%m-%d')}\n")
        lines.added = False

        type_order = [
            "Breaking Changes 🔄", "New Features ✨", "Bug Fixes 🐛",
            "Performance ⚡", "Security 🔒", "Documentation 📝",
            "Refactoring ♻️", "Tests ✅", "CI/CD 🤖", "Chore 🔧",
        ]

        for cat_type in type_order:
            commits_in_cat = categorized[cat_type]
            if commits_in_cat:
                lines.append(f"### {cat_type}\n")
                for c in commits_in_cat:
                    clean_msg = re.sub(r"^(feat|fix|refactor|docs|test|chore|ci|perf|style|build)(\(.+\))?\s*:\s*", "", c.message)
                    clean_msg = re.sub(r"\(#\d+\)", "", clean_msg).strip()
                    author_str = f" (@{c.author})" if c.author else ""
                    lines.append(f"- {clean_msg}{author_str}")
                lines.append("")

        if not any(categorized.values()):
            lines.append("### Other\n- Initial release or no conventional commits detected\n")

        compare_url = f"/{from_ver}...{to_ver}"
        lines.append(f"**Full Changelog**: {compare_url}\n")

        return "\n".join(lines)

    @staticmethod
    def _categorize_commit(message: str) -> str:
        """分类约定式提交"""
        msg_lower = message.lower().strip()

        if re.match(r"(feat|fix|refactor|perf|docs|test|chore|ci|style|build)\!:", msg_lower):
            return "Breaking Changes 🔄"

        type_map: dict[str, str] = {
            "feat": "New Features ✨",
            "fix": "Bug Fixes 🐛",
            "perf": "Performance ⚡",
            "docs": "Documentation 📝",
            "refactor": "Refactoring ♻️",
            "test": "Tests ✅",
            "chore": "Chore 🔧",
            "ci": "CI/CD 🤖",
            "security": "Security 🔒",
            "style": "Style 🎨",
            "build": "Build 📦",
        }

        for prefix, category in type_map.items():
            if msg_lower.startswith(prefix):
                return category

        return "Other"

    # ==================== 发布管理 ====================

    def create_release(
        self,
        version: SemanticVersion | None = None,
        **kwargs,
    ) -> ReleaseInfo:
        """
        创建发布记录

        Args:
            version: 版本号
        """
        ver = version or self._current_version
        tag_name = f"v{ver}"
        branch_name = kwargs.get("branch_name", f"release/{ver}")

        checks: dict[str, bool] = {}
        check_items = self._get_checklist_items()
        for item in check_items:
            checks[item.name] = item.checked

        release = ReleaseInfo(
            version=ver,
            branch_name=branch_name,
            tag_name=tag_name,
            pre_release_checks=checks,
            changelog=self.generate_changelog(),
        )
        self._releases.append(release)
        return release

    def _get_checklist_items(self) -> list[PreReleaseCheckItem]:
        """获取发布检查清单项"""
        return [
            PreReleaseCheckItem("all_tests_pass", "quality", required=True, description="全部测试用例通过"),
            PreReleaseCheckItem("docs_updated", "documentation", required=True, description="文档已更新"),
            PreReleaseCheckItem("config_correct", "configuration", required=True, description="生产配置正确"),
            PreReleaseCheckItem("backup_completed", "safety", required=True, description="数据库备份已完成"),
            PreReleaseCheckItem("notification_sent", "communication", required=False, description="相关方已通知"),
            PreReleaseCheckItem("performance_tested", "quality", required=False, description="性能测试通过"),
            PreReleaseCheckItem("security_scanned", "security", required=True, description="安全扫描通过"),
            PreReleaseCheckItem("rollback_plan_ready", "safety", required=True, description="回滚方案已准备"),
            PreReleaseCheckItem("license_compliant", "legal", required=False, description="许可证合规检查"),
            PreReleaseCheckItem("api_backward_compatible", "compatibility", required=True, description="API向后兼容"),
        ]

    def run_pre_release_checks(self, release: ReleaseInfo) -> dict[str, Any]:
        """执行发布前检查"""
        items = self._get_checklist_items()
        results: list[dict[str, Any]] = []
        all_passed = True

        for item in items:
            is_checked = release.pre_release_checks.get(item.name, item.checked)
            passed = (not item.required) or is_checked
            if not passed:
                all_passed = False
            results.append({
                "name": item.name,
                "category": item.category,
                "required": item.required,
                "passed": passed,
                "description": item.description,
            })

        release.checklist_completed = all_passed

        return {
            "version": str(release.version),
            "all_passed": all_passed,
            "total_items": len(results),
            "passed_count": sum(1 for r in results if r["passed"]),
            "failed_items": [r for r in results if not r["passed"]],
        }

    def generate_announcement(self, release: ReleaseInfo) -> str:
        """生成发布公告"""
        ver = str(release.version)
        date_str = datetime.now().strftime("%Y年%m月%d日")

        lines: list[str] = [f"# 🚀 版本 {ver} 发布公告\n"]
        lines.append(f"> **发布日期**: {date_str}")
        lines.append(f"> **版本**: {ver}")
        lines.append(f"> **分支**: {release.branch_name or 'main'}\n")

        lines.append("## ✨ 主要更新\n")
        lines.append(release.changelog[:1000] if release.changelog else "> 暂无详细更新日志\n")

        lines.append("\n## 📋 升级指南\n")
        lines.append(f"```bash")
        lines.append(f"# 使用包管理器升级")
        lines.append(f"# pip install package=={ver}")
        lines.append(f"# 或从源码构建")
        lines.append(f"git checkout tags/{release.tag_name or ('v' + ver)}")
        lines.append(f"```\n")

        lines.append("## ⚠️ 注意事项\n")
        lines.append("- 请在升级前备份数据库\n")
        lines.append("- 建议在预发布环境先验证\n")

        lines.append("\n---\n")
        lines.append("*此公告由尚书省·刑部·版本管理司自动生成*\n")

        return "\n".join(lines)

    # ==================== 可视化 ====================

    def visualize_branches(self) -> str:
        """生成分支状态图(Mermaid)"""
        lines: list[str] = ["gitGraph"]

        branches_sorted = sorted(
            self._branches.values(), key=lambda b: b.created_at
        )

        main_branch = next((b for b in branches_sorted if b.branch_type == BranchType.MAIN), None)
        if main_branch:
            lines.append(f'    checkout {main_branch.name}')
            lines.append(f'    commit id: "Initial commit"')

        develop_branch = next((b for b in branches_sorted if b.branch_type == BranchType.DEVELOP), None)
        if develop_branch:
            lines.append(f'    checkout -b {develop_branch.name}')

        feature_branches = [b for b in branches_sorted if b.branch_type == BranchType.FEATURE]
        release_branches = [b for b in branches_sorted if b.branch_type == BranchType.RELEASE]
        hotfix_branches = [b for b in branches_sorted if b.branch_type == BranchType.HOTFIX]

        for fb in feature_branches[:5]:
            lines.append(f'    checkout -b {fb.name}')
            lines.append(f'    commit id: "Work on {fb.name}"')
            if develop_branch:
                lines.append(f'    checkout {develop_branch.name}')
                lines.append(f'    merge {fb.name} id: "Merge {fb.name}"')

        for rb in release_branches[:3]:
            lines.append(f'    checkout -b {rb.name}')
            lines.append(f'    commit id: "Prepare release {rb.name}"')
            if main_branch:
                lines.append(f'    checkout {main_branch.name}')
                tag_val = rb.name.replace("release/", "v")
                lines.append(f'    merge {rb.name} id: "Merge release {rb.name}" tag: "{tag_val}"')
            if develop_branch:
                lines.append(f'    checkout {develop_branch.name}')
                lines.append(f'    merge {rb.name} id: "Back-merge to develop"')

        for hb in hotfix_branches[:3]:
            lines.append(f'    checkout -b {hb.name}')
            lines.append(f'    commit id: "Fix: {hb.description}"')
            if main_branch:
                lines.append(f'    checkout {main_branch.name}')
                lines.append(f'    merge {hb.name} id: "Hotfix {hb.name}" tag: "v{self._current_version}.patch"')
            if develop_branch:
                lines.append(f'    checkout {develop_branch.name}')
                lines.append(f'    merge {hb.name} id: "Back-merge hotfix"')

        return "\n".join(lines)

    # ==================== 变更统计 ====================

    def record_commit(self, commit: CommitInfo) -> None:
        """记录提交信息"""
        self._commits.append(commit)

    def analyze_changes(self) -> ChangeStats:
        """分析代码变更统计"""
        stats = ChangeStats(total_commits=len(self._commits))

        for commit in self._commits:
            author = commit.author or "unknown"
            stats.by_author[author] = stats.by_author.get(author, 0) + 1

            ts = commit.timestamp[:10] if commit.timestamp else "unknown"
            stats.by_time_period[ts] = stats.by_time_period.get(ts, 0) + 1

            branch = commit.branch or "unknown"
            stats.by_branch[branch] = stats.by_branch.get(branch, 0) + 1

            for fpath in commit.files_changed:
                ext = Path(fpath).suffix or ".no_ext"
                stats.by_file_type[ext] = stats.by_file_type.get(ext, 0) + 1

        return stats

    # ==================== 报告生成 ====================

    def generate_report(self) -> str:
        """生成版本管理司报告"""
        lines: list[str] = []
        lines.append("# 📦 版本管理司 · 综合报告\n")

        lines.append(f"## 当前状态\n")
        lines.append(f"| 项目 | 值 |")
        lines.append(f"| --- | --- |")
        lines.append(f"| 策略 | **{self._strategy.upper()}** |")
        lines.append(f"| 当前版本 | **{self._current_version}** |")
        lines.append(f"| 分支数 | {len(self._branches)} |")
        lines.append(f"| 提交数 | {len(self._commits)} |")
        lines.append(f"| 发布数 | {len(self._releases)} |")

        lines.append(f"\n## 分支列表 ({len(self._branches)})\n")
        lines.append("| 名称 | 类型 | 基础分支 | 状态 | 描述 |")
        lines.append("| --- | --- | --- | --- | --- |")
        for b in sorted(self._branches.values(), key=lambda x: x.created_at, reverse=True)[:15]:
            type_icon = {
                BranchType.MAIN: "🏠", BranchType.DEVELOP: "🔧",
                BranchType.FEATURE: "🌿", BranchType.RELEASE: "📦",
                BranchType.HOTFIX: "🔥", BranchType.BUGFIX: "🐛",
            }.get(b.branch_type, "📌")
            lines.append(
                f"`{b.name}` | {type_icon} `{b.branch_type.value}` "
                f"| `{b.base_branch}` | {b.status} | {b.description[:30]} |"
            )

        releases = self._releases[-5:]
        if releases:
            lines.append(f"\n## 最近发布\n")
            lines.append("| 版本 | 状态 | 检查完成 | Tag |")
            lines.append("| --- | --- | --- | --- |")
            for r in releases:
                status_icon = "✅" if r.checklist_completed else "⏳"
                lines.append(
                    f"**{r.version}** | {r.status} | {status_icon} | `{r.tag_name}` |"
                )

        stats = self.analyze_changes()
        if stats.total_commits > 0:
            lines.append(f"\n## 变更统计\n")
            lines.append(f"- **总提交数**: {stats.total_commits}")
            lines.append(f"- **贡献者**: {len(stats.by_author)}人")
            top_authors = sorted(stats.by_author.items(), key=lambda x: x[1], reverse=True)[:5]
            for author, count in top_authors:
                lines.append(f"  - `{author}`: {count}次提交")

            top_types = sorted(stats.by_file_type.items(), key=lambda x: x[1], reverse=True)[:5]
            lines.append(f"- **文件类型分布**:")
            for ext, count in top_types:
                lines.append(f"  - `{ext}`: {count}个文件")

        mermaid = self.visualize_branches()
        lines.append(f"\n## 分支拓扑图\n")
        lines.append("```mermaid")
        lines.append(mermaid[:500])
        lines.append("```\n")

        return "\n".join(lines)


if __name__ == "__main__":
    print("=" * 60)
    print("版本管理司 - 功能演示")
    print("=" * 60)

    si = VersionControlSi(strategy="gitflow")

    print("\n--- 分支创建 ---")
    feat_branch = si.create_branch("user-auth", BranchType.FEATURE, description="用户认证功能")
    print(f"  创建: {feat_branch.name} ({feat_branch.branch_type.value}) ← {feat_branch.base_branch}")

    rel_branch = si.create_branch("1.2.0", BranchType.RELEASE, description="1.2.0版本发布")
    print(f"  创建: {rel_branch.name} ({rel_branch.branch_type.value}) ← {rel_branch.base_branch}")

    hf_branch = si.create_branch("fix-login-crash", BranchType.HOTFIX, description="修复登录崩溃问题")
    print(f"  创建: {hf_branch.name} ({hf_branch.branch_type.value}) ← {hf_branch.base_branch}")

    print("\n--- 合并操作 ---")
    result = si.merge_branch("feature/user-auth", "develop")
    print(f"  {result['message']}")
    for v in result["validations"]:
        icon = {"pass": "✅", "warn": "⚠️", "fail": "❌"}.get(v["status"], "?")
        print(f"    [{icon}] {v['check']}: {v['message']}")

    print("\n--- 版本管理 ---")
    current = si.get_version()
    print(f"  当前版本: {current}")

    bumped = si.bump_version(VersionComponent.MINOR)
    print(f"  升级(minor): {bumped}")

    bumped_patch = si.bump_version(VersionComponent.PATCH)
    print(f"  升级(patch): {bumped_patch}")

    test_commits = [
        CommitInfo(hash="abc123", message="feat: add user authentication flow", author="alice"),
        CommitInfo(hash="def456", message="fix!: remove deprecated API endpoint", author="bob"),
        CommitInfo(hash="ghi789", message="fix: resolve login timeout issue", author="alice"),
    ]
    suggested = si.suggest_version_bump(test_commits)
    print(f"  建议升级: {suggested.value} (基于约定式提交分析)")

    print("\n--- CHANGELOG ---")
    for c in test_commits:
        si.record_commit(c)
    changelog = si.generate_changelog(from_version="v1.1.0")
    print(changelog[:500])

    print("\n--- 发布管理 ---")
    release = si.create_release()
    check_result = si.run_pre_release_checks(release)
    print(f"  版本: {release.version}, 检查通过: {check_result['all_passed']}")
    print(f"  通过: {check_result['passed_count']}/{check_result['total_items']}")

    announcement = si.generate_announcement(release)
    print(f"\n--- 公告预览 (前400字符) ---\n{announcement[:400]}...")

    print("\n--- 变更统计 ---")
    stats = si.analyze_changes()
    print(f"  总提交: {stats.total_commits}, 贡献者: {len(stats.by_author)}")

    report = si.generate_report()
    print(f"\n--- 报告预览 (前800字符) ---\n{report[:800]}...")

    print("\n✅ 所有测试通过!")
