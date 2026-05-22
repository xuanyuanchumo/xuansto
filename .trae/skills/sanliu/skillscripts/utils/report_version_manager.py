#!/usr/bin/env python3
"""
报告版本管理模块 - Sanliu 技能

功能：
- 报告版本存储
- 报告索引管理
- 报告历史查询
- 报告对比分析

使用方法：
    python scripts/report_version_manager.py --store <report_file>
    python scripts/report_version_manager.py --list
    python scripts/report_version_manager.py --query --version v1.0.0
    python scripts/report_version_manager.py --compare v1.0.0 v1.1.0
"""

import argparse
import hashlib
import json
import logging
import random
import re
import shutil
import string
import sys
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Optional


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - [%(name)s] %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('report_version_manager.log', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)


class ReportType(Enum):
    TEST = "test"
    COVERAGE = "coverage"
    PERFORMANCE = "performance"
    SECURITY = "security"
    PIPELINE = "pipeline"
    UI_VALIDATION = "ui_validation"
    DOC_CHANGE = "doc_change"


class ReportStatus(Enum):
    ACTIVE = "active"
    ARCHIVED = "archived"
    DEPRECATED = "deprecated"


class TestCategory(Enum):
    UNIT = "unit"
    INTEGRATION = "integration"
    DATABASE = "database"
    E2E = "e2e"
    PERFORMANCE = "performance"
    SECURITY = "security"
    REGRESSION = "regression"

    @classmethod
    def get_default_dir(cls, category: "TestCategory") -> str:
        dir_mapping = {
            cls.UNIT: "unit_tests",
            cls.INTEGRATION: "integration_tests",
            cls.DATABASE: "database_tests",
            cls.E2E: "e2e_tests",
            cls.PERFORMANCE: "performance_tests",
            cls.SECURITY: "security_tests",
            cls.REGRESSION: "regression_tests",
        }
        return dir_mapping.get(category, "other_tests")


@dataclass
class SemanticVersion:
    """
    语义化版本号类
    
    用于解析、比较和管理版本号，支持语义化版本规范 (SemVer)
    格式: major.minor.patch[-prerelease][+build]
    例如: 1.2.3-alpha.1+build.123
    """
    major: int = 0
    minor: int = 0
    patch: int = 0
    prerelease: str = ""
    build: str = ""
    original: str = ""
    
    VERSION_PATTERN = re.compile(
        r'^(?P<major>0|[1-9]\d*)'
        r'\.(?P<minor>0|[1-9]\d*)'
        r'\.(?P<patch>0|[1-9]\d*)'
        r'(?:-(?P<prerelease>(?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*)'
        r'(?:\.(?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*))*))?'
        r'(?:\+(?P<build>[0-9a-zA-Z-]+(?:\.[0-9a-zA-Z-]+)*))?$'
    )
    
    @classmethod
    def parse(cls, version_str: str) -> "SemanticVersion":
        """
        解析版本字符串为 SemanticVersion 对象
        
        Args:
            version_str: 版本字符串，如 "v1.2.3" 或 "1.2.3-alpha+build"
            
        Returns:
            SemanticVersion 对象
        """
        version_str = version_str.strip()
        if version_str.startswith('v') or version_str.startswith('V'):
            version_str = version_str[1:]
        
        match = cls.VERSION_PATTERN.match(version_str)
        if not match:
            return cls(original=version_str)
        
        return cls(
            major=int(match.group('major')),
            minor=int(match.group('minor')),
            patch=int(match.group('patch')),
            prerelease=match.group('prerelease') or "",
            build=match.group('build') or "",
            original=version_str
        )
    
    def __str__(self) -> str:
        """返回版本字符串表示"""
        version = f"{self.major}.{self.minor}.{self.patch}"
        if self.prerelease:
            version += f"-{self.prerelease}"
        if self.build:
            version += f"+{self.build}"
        return version
    
    def __repr__(self) -> str:
        return f"SemanticVersion({self})"
    
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, SemanticVersion):
            return False
        return (
            self.major == other.major and
            self.minor == other.minor and
            self.patch == other.patch and
            self.prerelease == other.prerelease
        )
    
    def __lt__(self, other: "SemanticVersion") -> bool:
        """比较版本号大小（小于）"""
        if not isinstance(other, SemanticVersion):
            return NotImplemented
        
        if (self.major, self.minor, self.patch) != (other.major, other.minor, other.patch):
            return (self.major, self.minor, self.patch) < (other.major, other.minor, other.patch)
        
        if self.prerelease and not other.prerelease:
            return True
        if not self.prerelease and other.prerelease:
            return False
        if not self.prerelease and not other.prerelease:
            return False
        
        return self._compare_prerelease(self.prerelease, other.prerelease) < 0
    
    def __le__(self, other: "SemanticVersion") -> bool:
        return self == other or self < other
    
    def __gt__(self, other: "SemanticVersion") -> bool:
        return not self <= other
    
    def __ge__(self, other: "SemanticVersion") -> bool:
        return not self < other
    
    def _compare_prerelease(self, pre1: str, pre2: str) -> int:
        """
        比较预发布版本号
        
        Args:
            pre1: 第一个预发布版本字符串
            pre2: 第二个预发布版本字符串
            
        Returns:
            -1, 0, 1 分别表示小于、等于、大于
        """
        parts1 = pre1.split('.') if pre1 else []
        parts2 = pre2.split('.') if pre2 else []
        
        for p1, p2 in zip(parts1, parts2):
            if p1.isdigit() and p2.isdigit():
                n1, n2 = int(p1), int(p2)
                if n1 != n2:
                    return -1 if n1 < n2 else 1
            elif p1.isdigit():
                return -1
            elif p2.isdigit():
                return 1
            else:
                if p1 != p2:
                    return -1 if p1 < p2 else 1
        
        if len(parts1) < len(parts2):
            return -1
        elif len(parts1) > len(parts2):
            return 1
        return 0
    
    def bump_major(self) -> "SemanticVersion":
        """递增主版本号"""
        return SemanticVersion(
            major=self.major + 1,
            minor=0,
            patch=0,
            original=f"{self.major + 1}.0.0"
        )
    
    def bump_minor(self) -> "SemanticVersion":
        """递增次版本号"""
        return SemanticVersion(
            major=self.major,
            minor=self.minor + 1,
            patch=0,
            original=f"{self.major}.{self.minor + 1}.0"
        )
    
    def bump_patch(self) -> "SemanticVersion":
        """递增补丁版本号"""
        return SemanticVersion(
            major=self.major,
            minor=self.minor,
            patch=self.patch + 1,
            original=f"{self.major}.{self.minor}.{self.patch + 1}"
        )
    
    def is_prerelease(self) -> bool:
        """检查是否为预发布版本"""
        return bool(self.prerelease)
    
    def is_stable(self) -> bool:
        """检查是否为稳定版本"""
        return self.major > 0 and not self.prerelease
    
    def to_dict(self) -> dict[str, Any]:
        """转换为字典格式"""
        return {
            "major": self.major,
            "minor": self.minor,
            "patch": self.patch,
            "prerelease": self.prerelease,
            "build": self.build,
            "full_version": str(self),
            "is_prerelease": self.is_prerelease(),
            "is_stable": self.is_stable()
        }


@dataclass
class VersionDependency:
    """
    版本依赖关系
    
    用于管理版本之间的依赖关系
    """
    version: str
    depends_on: list[str] = field(default_factory=list)
    conflicts: list[str] = field(default_factory=list)
    replaces: Optional[str] = None
    deprecated_by: Optional[str] = None


class VersionManager:
    """
    版本管理器
    
    提供版本迭代、依赖关系管理和版本生命周期管理功能
    """
    
    def __init__(self, storage: "ReportStorage"):
        self.storage = storage
        self.dependencies: dict[str, VersionDependency] = {}
        self.version_order: list[str] = []
        self._load_dependencies()
    
    def _load_dependencies(self):
        """从存储加载版本依赖关系"""
        deps_file = self.storage.index_dir / "version_dependencies.json"
        if deps_file.exists():
            try:
                with open(deps_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for ver, dep_data in data.items():
                        self.dependencies[ver] = VersionDependency(
                            version=ver,
                            depends_on=dep_data.get("depends_on", []),
                            conflicts=dep_data.get("conflicts", []),
                            replaces=dep_data.get("replaces"),
                            deprecated_by=dep_data.get("deprecated_by")
                        )
            except Exception as e:
                logger.warning(f"加载版本依赖关系失败: {e}")
    
    def _save_dependencies(self):
        """保存版本依赖关系到存储"""
        deps_file = self.storage.index_dir / "version_dependencies.json"
        data = {}
        for ver, dep in self.dependencies.items():
            data[ver] = {
                "depends_on": dep.depends_on,
                "conflicts": dep.conflicts,
                "replaces": dep.replaces,
                "deprecated_by": dep.deprecated_by
            }
        with open(deps_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    def create_version(
        self,
        base_version: str,
        bump_type: str = "patch",
        prerelease: str = ""
    ) -> str:
        """
        创建新版本号
        
        Args:
            base_version: 基础版本号
            bump_type: 递增类型 (major/minor/patch)
            prerelease: 预发布标识
            
        Returns:
            新版本号字符串
        """
        sem_ver = SemanticVersion.parse(base_version)
        
        if bump_type == "major":
            new_ver = sem_ver.bump_major()
        elif bump_type == "minor":
            new_ver = sem_ver.bump_minor()
        else:
            new_ver = sem_ver.bump_patch()
        
        if prerelease:
            new_ver.prerelease = prerelease
        
        return str(new_ver)
    
    def get_next_version(self, current_version: str) -> str:
        """
        获取下一个建议版本号
        
        Args:
            current_version: 当前版本号
            
        Returns:
            建议的下一个版本号
        """
        sem_ver = SemanticVersion.parse(current_version)
        
        if sem_ver.is_prerelease():
            return f"{sem_ver.major}.{sem_ver.minor}.{sem_ver.patch}"
        
        return str(sem_ver.bump_patch())
    
    def compare_versions(self, version1: str, version2: str) -> int:
        """
        比较两个版本号
        
        Args:
            version1: 第一个版本号
            version2: 第二个版本号
            
        Returns:
            -1, 0, 1 分别表示 version1 小于、等于、大于 version2
        """
        v1 = SemanticVersion.parse(version1)
        v2 = SemanticVersion.parse(version2)
        
        if v1 < v2:
            return -1
        elif v1 > v2:
            return 1
        return 0
    
    def get_version_range(
        self,
        start_version: str,
        end_version: str
    ) -> list[str]:
        """
        获取版本范围内的所有版本
        
        Args:
            start_version: 起始版本（包含）
            end_version: 结束版本（包含）
            
        Returns:
            版本列表
        """
        all_versions = self.get_all_versions()
        
        start_sem = SemanticVersion.parse(start_version)
        end_sem = SemanticVersion.parse(end_version)
        
        result = []
        for ver in all_versions:
            sem = SemanticVersion.parse(ver)
            if start_sem <= sem <= end_sem:
                result.append(ver)
        
        return sorted(result, key=lambda v: SemanticVersion.parse(v))
    
    def get_all_versions(self) -> list[str]:
        """获取所有版本列表"""
        versions = set()
        
        for index_file in self.storage.index_dir.glob("version_*.json"):
            version = index_file.stem.replace("version_", "")
            versions.add(version)
        
        for category_dir in self.storage.category_dirs.iterdir():
            if category_dir.is_dir():
                for version_dir in category_dir.iterdir():
                    if version_dir.is_dir():
                        versions.add(version_dir.name)
        
        return sorted(versions, key=lambda v: SemanticVersion.parse(v), reverse=True)
    
    def get_latest_version(self, stable_only: bool = False) -> Optional[str]:
        """
        获取最新版本
        
        Args:
            stable_only: 是否只获取稳定版本
            
        Returns:
            最新版本号，如果没有则返回 None
        """
        versions = self.get_all_versions()
        
        if not stable_only:
            return versions[0] if versions else None
        
        for ver in versions:
            sem = SemanticVersion.parse(ver)
            if sem.is_stable():
                return ver
        
        return None
    
    def set_dependency(
        self,
        version: str,
        depends_on: list[str] = None,
        conflicts: list[str] = None,
        replaces: str = None,
        deprecated_by: str = None
    ):
        """
        设置版本依赖关系
        
        Args:
            version: 版本号
            depends_on: 依赖的版本列表
            conflicts: 冲突的版本列表
            replaces: 替换的版本
            deprecated_by: 废弃此版本的版本号
        """
        dep = VersionDependency(
            version=version,
            depends_on=depends_on or [],
            conflicts=conflicts or [],
            replaces=replaces,
            deprecated_by=deprecated_by
        )
        self.dependencies[version] = dep
        self._save_dependencies()
        logger.info(f"已设置版本依赖关系: {version}")
    
    def get_dependencies(self, version: str) -> Optional[VersionDependency]:
        """
        获取版本的依赖关系
        
        Args:
            version: 版本号
            
        Returns:
            版本依赖关系对象
        """
        return self.dependencies.get(version)
    
    def check_compatibility(self, version1: str, version2: str) -> dict[str, Any]:
        """
        检查两个版本的兼容性
        
        Args:
            version1: 第一个版本
            version2: 第二个版本
            
        Returns:
            兼容性检查结果
        """
        result = {
            "version1": version1,
            "version2": version2,
            "compatible": True,
            "warnings": [],
            "errors": []
        }
        
        dep1 = self.dependencies.get(version1)
        dep2 = self.dependencies.get(version2)
        
        if dep1 and version2 in dep1.conflicts:
            result["compatible"] = False
            result["errors"].append(f"{version1} 与 {version2} 冲突")
        
        if dep2 and version1 in dep2.conflicts:
            result["compatible"] = False
            result["errors"].append(f"{version2} 与 {version1} 冲突")
        
        if dep1 and dep1.deprecated_by:
            result["warnings"].append(f"{version1} 已被 {dep1.deprecated_by} 废弃")
        
        if dep2 and dep2.deprecated_by:
            result["warnings"].append(f"{version2} 已被 {dep2.deprecated_by} 废弃")
        
        return result
    
    def get_version_lineage(self, version: str) -> dict[str, Any]:
        """
        获取版本的演变谱系
        
        Args:
            version: 版本号
            
        Returns:
            版本演变谱系信息
        """
        lineage = {
            "version": version,
            "predecessors": [],
            "successors": [],
            "replaces": None,
            "replaced_by": None,
            "deprecated_by": None
        }
        
        dep = self.dependencies.get(version)
        if dep:
            lineage["replaces"] = dep.replaces
            lineage["deprecated_by"] = dep.deprecated_by
            lineage["predecessors"] = dep.depends_on
        
        for ver, dep_info in self.dependencies.items():
            if version in dep_info.depends_on:
                lineage["successors"].append(ver)
            if dep_info.replaces == version:
                lineage["replaced_by"] = ver
        
        return lineage
    
    def get_version_statistics(self) -> dict[str, Any]:
        """
        获取版本统计信息
        
        Returns:
            版本统计信息
        """
        versions = self.get_all_versions()
        
        stats = {
            "total_versions": len(versions),
            "stable_versions": 0,
            "prerelease_versions": 0,
            "major_versions": set(),
            "minor_versions": {},
            "latest_version": None,
            "oldest_version": None,
            "deprecated_versions": []
        }
        
        for ver in versions:
            sem = SemanticVersion.parse(ver)
            
            if sem.is_stable():
                stats["stable_versions"] += 1
            elif sem.is_prerelease():
                stats["prerelease_versions"] += 1
            
            stats["major_versions"].add(sem.major)
            
            if sem.major not in stats["minor_versions"]:
                stats["minor_versions"][sem.major] = set()
            stats["minor_versions"][sem.major].add(sem.minor)
            
            dep = self.dependencies.get(ver)
            if dep and dep.deprecated_by:
                stats["deprecated_versions"].append(ver)
        
        stats["major_versions"] = sorted(stats["major_versions"])
        stats["minor_versions"] = {
            k: sorted(v) for k, v in stats["minor_versions"].items()
        }
        
        if versions:
            stats["latest_version"] = versions[0]
            stats["oldest_version"] = versions[-1]
        
        return stats


@dataclass
class ReportMetadata:
    report_id: str
    report_type: ReportType
    version: str
    created_at: datetime
    file_path: str
    file_size: int
    status: ReportStatus = ReportStatus.ACTIVE
    tags: list[str] = field(default_factory=list)
    summary: dict[str, Any] = field(default_factory=dict)
    description: str = ""
    test_category: Optional["TestCategory"] = None
    metrics: dict[str, Any] = field(default_factory=dict)


@dataclass
class MergedReport:
    """合并报告数据类"""
    merged_id: str
    name: str
    created_at: datetime
    source_reports: list[str]
    merged_metrics: dict[str, Any]
    merged_summary: dict[str, Any]
    test_category: Optional["TestCategory"] = None
    versions: list[str] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)


@dataclass
class ExportConfig:
    """导出配置数据类"""
    format: str = "json"
    include_summary: bool = True
    include_metrics: bool = True
    include_details: bool = False
    template: Optional[str] = None
    output_path: Optional[str] = None
    compress: bool = False


@dataclass
class DiffSummary:
    """差异摘要数据类"""
    similarity_percentage: float = 0.0
    total_changes: int = 0
    added_lines: int = 0
    removed_lines: int = 0
    change_type: str = "unknown"


@dataclass
class DiffReport:
    """差异报告数据类"""
    report_id: str
    generated_at: str
    file1_info: dict[str, Any]
    file2_info: dict[str, Any]
    summary: DiffSummary = field(default_factory=DiffSummary)
    recommendations: list[str] = field(default_factory=list)


@dataclass
class ReportIndex:
    version: str
    reports: list[str]
    created_at: datetime
    total_size: int = 0
    summary: dict[str, Any] = field(default_factory=dict)


class ReportStorage:
    """报告存储管理器"""

    TEST_CATEGORIES = [
        "unit_tests",
        "integration_tests",
        "database_tests",
        "e2e_tests",
        "performance_tests",
        "security_tests",
        "regression_tests",
    ]

    def __init__(self, base_dir: Path = None):
        if base_dir is None:
            try:
                from skillscripts.utils.enhanced_path_config_manager import create_path_manager, PathKey
                manager = create_path_manager()
                self.base_dir = manager.resolve_path(PathKey.DOCS_DIR) / "reports"
            except Exception:
                self.base_dir = Path("docs/reports")
        else:
            self.base_dir = base_dir
        self.reports_dir = self.base_dir / "versions"
        self.index_dir = self.base_dir / "index"
        self.archive_dir = self.base_dir / "archive"
        self.category_dirs = self.base_dir / "categories"

        self._ensure_dirs()
        self._ensure_category_dirs()

    def _ensure_dirs(self):
        self.reports_dir.mkdir(parents=True, exist_ok=True)
        self.index_dir.mkdir(parents=True, exist_ok=True)
        self.archive_dir.mkdir(parents=True, exist_ok=True)

    def _ensure_category_dirs(self):
        self.category_dirs.mkdir(parents=True, exist_ok=True)
        for category_dir in self.TEST_CATEGORIES:
            category_path = self.category_dirs / category_dir
            category_path.mkdir(parents=True, exist_ok=True)

    def _get_category_dir(self, test_category: Optional[TestCategory]) -> Path:
        if test_category is None:
            return self.reports_dir
        category_name = TestCategory.get_default_dir(test_category)
        return self.category_dirs / category_name

    def store_report(
        self,
        report_file: Path,
        version: str,
        report_type: ReportType,
        description: str = "",
        tags: list[str] = None,
        test_category: TestCategory = None
    ) -> ReportMetadata:
        if test_category:
            version_dir = self._get_category_dir(test_category) / version
        else:
            version_dir = self.reports_dir / version
        version_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now()
        random_suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=6))
        report_id = f"{report_type.value}_{timestamp.strftime('%Y%m%d_%H%M%S')}_{random_suffix}"

        target_file = version_dir / f"{report_id}{report_file.suffix}"
        shutil.copy2(str(report_file), str(target_file))

        file_size = target_file.stat().st_size

        summary = self._extract_summary(report_file)
        metrics = self._extract_metrics(report_file, test_category)

        metadata = ReportMetadata(
            report_id=report_id,
            report_type=report_type,
            version=version,
            created_at=timestamp,
            file_path=str(target_file),
            file_size=file_size,
            tags=tags or [],
            summary=summary,
            description=description,
            test_category=test_category,
            metrics=metrics
        )

        self._save_metadata(metadata)
        self._update_index(version, metadata)

        logger.info(f"报告已存储: {report_id} -> {target_file}")
        return metadata

    def _extract_summary(self, report_file: Path) -> dict[str, Any]:
        summary = {}

        if report_file.suffix == '.json':
            try:
                with open(report_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                if 'summary' in data:
                    summary = data['summary']
                elif 'metadata' in data:
                    summary = data['metadata']
                elif 'results' in data:
                    results = data['results']
                    if isinstance(results, dict):
                        summary = results
                    elif isinstance(results, list) and results:
                        summary = {"total_tests": len(results)}

                if 'statistics' in data:
                    summary['statistics'] = data['statistics']

            except Exception:
                pass

        elif report_file.suffix in ['.xml', '.junit']:
            try:
                import xml.etree.ElementTree as ET
                tree = ET.parse(report_file)
                root = tree.getroot()
                summary = {
                    "tests": int(root.attrib.get('tests', 0)),
                    "failures": int(root.attrib.get('failures', 0)),
                    "errors": int(root.attrib.get('errors', 0)),
                    "skipped": int(root.attrib.get('skipped', 0)),
                    "time": float(root.attrib.get('time', 0)),
                }
            except Exception:
                pass

        return summary

    def _extract_metrics(
        self,
        report_file: Path,
        test_category: Optional[TestCategory]
    ) -> dict[str, Any]:
        metrics = {
            "category": test_category.value if test_category else None,
            "extracted_at": datetime.now().isoformat(),
        }

        if report_file.suffix == '.json':
            try:
                with open(report_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                if test_category == TestCategory.UNIT:
                    metrics.update(self._extract_unit_metrics(data))
                elif test_category == TestCategory.INTEGRATION:
                    metrics.update(self._extract_integration_metrics(data))
                elif test_category == TestCategory.DATABASE:
                    metrics.update(self._extract_database_metrics(data))
                elif test_category == TestCategory.E2E:
                    metrics.update(self._extract_e2e_metrics(data))
                elif test_category == TestCategory.PERFORMANCE:
                    metrics.update(self._extract_performance_metrics(data))
                elif test_category == TestCategory.SECURITY:
                    metrics.update(self._extract_security_metrics(data))
                elif test_category == TestCategory.REGRESSION:
                    metrics.update(self._extract_regression_metrics(data))

            except Exception:
                pass

        return metrics

    def _extract_unit_metrics(self, data: dict) -> dict[str, Any]:
        metrics = {}
        if 'summary' in data:
            s = data['summary']
            metrics.update({
                "total_tests": s.get('total', s.get('tests', 0)),
                "passed": s.get('passed', s.get('successes', 0)),
                "failed": s.get('failed', s.get('failures', 0)),
                "skipped": s.get('skipped', 0),
                "duration": s.get('duration', s.get('time', 0)),
                "pass_rate": self._calculate_pass_rate(s),
            })
        return metrics

    def _extract_integration_metrics(self, data: dict) -> dict[str, Any]:
        metrics = {}
        if 'summary' in data:
            s = data['summary']
            metrics.update({
                "total_scenarios": s.get('scenarios', s.get('total', 0)),
                "passed_scenarios": s.get('passed', 0),
                "failed_scenarios": s.get('failed', 0),
                "integration_points": s.get('integration_points', []),
                "duration": s.get('duration', 0),
            })
        return metrics

    def _extract_database_metrics(self, data: dict) -> dict[str, Any]:
        metrics = {}
        if 'summary' in data:
            s = data['summary']
            metrics.update({
                "total_queries": s.get('queries', s.get('total', 0)),
                "successful_queries": s.get('successful', s.get('passed', 0)),
                "failed_queries": s.get('failed', 0),
                "query_time_avg": s.get('query_time_avg', 0),
                "connections_tested": s.get('connections_tested', 0),
            })
        return metrics

    def _extract_e2e_metrics(self, data: dict) -> dict[str, Any]:
        metrics = {}
        if 'summary' in data:
            s = data['summary']
            metrics.update({
                "total_flows": s.get('flows', s.get('total', 0)),
                "passed_flows": s.get('passed', 0),
                "failed_flows": s.get('failed', 0),
                "screenshots": s.get('screenshots', 0),
                "duration": s.get('duration', 0),
                "browser_coverage": s.get('browsers', []),
            })
        return metrics

    def _extract_performance_metrics(self, data: dict) -> dict[str, Any]:
        metrics = {}
        if 'summary' in data:
            s = data['summary']
            metrics.update({
                "avg_response_time": s.get('avg_response_time', 0),
                "max_response_time": s.get('max_response_time', 0),
                "min_response_time": s.get('min_response_time', 0),
                "throughput": s.get('throughput', 0),
                "error_rate": s.get('error_rate', 0),
                "p95_latency": s.get('p95', s.get('p95_latency', 0)),
                "p99_latency": s.get('p99', s.get('p99_latency', 0)),
            })
        return metrics

    def _extract_security_metrics(self, data: dict) -> dict[str, Any]:
        metrics = {}
        if 'summary' in data:
            s = data['summary']
            metrics.update({
                "vulnerabilities_found": s.get('vulnerabilities', s.get('total_issues', 0)),
                "critical": s.get('critical', 0),
                "high": s.get('high', 0),
                "medium": s.get('medium', 0),
                "low": s.get('low', 0),
                "scan_duration": s.get('duration', 0),
            })
        return metrics

    def _extract_regression_metrics(self, data: dict) -> dict[str, Any]:
        metrics = {}
        if 'summary' in data:
            s = data['summary']
            metrics.update({
                "regressions_found": s.get('regressions', 0),
                "tests_compared": s.get('tests_compared', 0),
                "baseline_version": s.get('baseline_version', ''),
                "current_version": s.get('current_version', ''),
                "improvements": s.get('improvements', 0),
                "degradations": s.get('degradations', 0),
            })
        return metrics

    @staticmethod
    def _calculate_pass_rate(summary: dict) -> float:
        total = summary.get('total', summary.get('tests', 0))
        passed = summary.get('passed', summary.get('successes', 0))
        if total > 0:
            return round((passed / total) * 100, 2)
        return 0.0

    def _save_metadata(self, metadata: ReportMetadata):
        metadata_file = self.index_dir / f"{metadata.report_id}.json"

        data = {
            "report_id": metadata.report_id,
            "report_type": metadata.report_type.value,
            "version": metadata.version,
            "created_at": metadata.created_at.isoformat(),
            "file_path": metadata.file_path,
            "file_size": metadata.file_size,
            "status": metadata.status.value,
            "tags": metadata.tags,
            "summary": metadata.summary,
            "description": metadata.description,
            "test_category": metadata.test_category.value if metadata.test_category else None,
            "metrics": metadata.metrics
        }

        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def _update_index(self, version: str, metadata: ReportMetadata):
        index_file = self.index_dir / f"version_{version}.json"

        if index_file.exists():
            with open(index_file, 'r', encoding='utf-8') as f:
                index_data = json.load(f)
        else:
            index_data = {
                "version": version,
                "reports": [],
                "created_at": datetime.now().isoformat(),
                "total_size": 0
            }

        index_data["reports"].append(metadata.report_id)
        index_data["total_size"] += metadata.file_size
        index_data["updated_at"] = datetime.now().isoformat()

        with open(index_file, 'w', encoding='utf-8') as f:
            json.dump(index_data, f, indent=2, ensure_ascii=False)

    def get_report(self, report_id: str) -> Optional[ReportMetadata]:
        metadata_file = self.index_dir / f"{report_id}.json"

        if not metadata_file.exists():
            return None

        with open(metadata_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        test_category = None
        if data.get('test_category'):
            try:
                test_category = TestCategory(data['test_category'])
            except ValueError:
                pass

        return ReportMetadata(
            report_id=data['report_id'],
            report_type=ReportType(data['report_type']),
            version=data['version'],
            created_at=datetime.fromisoformat(data['created_at']),
            file_path=data['file_path'],
            file_size=data['file_size'],
            status=ReportStatus(data.get('status', 'active')),
            tags=data.get('tags', []),
            summary=data.get('summary', {}),
            description=data.get('description', ''),
            test_category=test_category,
            metrics=data.get('metrics', {})
        )

    def list_reports(
        self,
        version: str = None,
        report_type: ReportType = None,
        days: int = None,
        test_category: TestCategory = None
    ) -> list[ReportMetadata]:
        reports = []

        for metadata_file in self.index_dir.glob("*.json"):
            if metadata_file.name.startswith("version_"):
                continue

            metadata = self.get_report(metadata_file.stem)
            if metadata:
                if version and metadata.version != version:
                    continue
                if report_type and metadata.report_type != report_type:
                    continue
                if test_category and metadata.test_category != test_category:
                    continue
                if days:
                    cutoff = datetime.now() - timedelta(days=days)
                    if metadata.created_at < cutoff:
                        continue
                reports.append(metadata)

        return sorted(reports, key=lambda x: x.created_at, reverse=True)

    def list_reports_by_category(self, test_category: TestCategory) -> list[ReportMetadata]:
        return self.list_reports(test_category=test_category)

    def get_category_statistics(self) -> dict[str, dict[str, Any]]:
        stats = {}
        for category in TestCategory:
            reports = self.list_reports(test_category=category)
            stats[category.value] = {
                "total_reports": len(reports),
                "total_size": sum(r.file_size for r in reports),
                "latest_report": max((r.created_at for r in reports), default=None),
                "versions": list(set(r.version for r in reports)),
            }
        return stats
    
    def store_batch_reports(
        self,
        reports: list[dict[str, Any]],
        version: str
    ) -> list[ReportMetadata]:
        """
        批量存储报告
        
        Args:
            reports: 报告信息列表，每个元素包含 report_file, report_type, 
                     description, tags, test_category 等字段
            version: 版本号
            
        Returns:
            存储的元数据列表
        """
        stored_metadata = []
        
        for report_info in reports:
            try:
                metadata = self.store_report(
                    report_file=Path(report_info["report_file"]),
                    version=version,
                    report_type=report_info.get("report_type", ReportType.TEST),
                    description=report_info.get("description", ""),
                    tags=report_info.get("tags"),
                    test_category=report_info.get("test_category")
                )
                stored_metadata.append(metadata)
            except Exception as e:
                logger.error(f"批量存储报告失败: {report_info.get('report_file')}, 错误: {e}")
        
        self._update_category_index(version)
        return stored_metadata
    
    def _update_category_index(self, version: str):
        """
        更新分类索引
        
        为每个测试分类创建独立的索引文件，便于快速查询
        """
        for category in TestCategory:
            reports = self.list_reports(version=version, test_category=category)
            
            if reports:
                category_index_file = self.index_dir / f"category_{category.value}_{version}.json"
                
                index_data = {
                    "category": category.value,
                    "version": version,
                    "report_count": len(reports),
                    "reports": [r.report_id for r in reports],
                    "total_size": sum(r.file_size for r in reports),
                    "created_at": datetime.now().isoformat(),
                    "metrics_summary": self._aggregate_category_metrics(reports, category)
                }
                
                with open(category_index_file, 'w', encoding='utf-8') as f:
                    json.dump(index_data, f, indent=2, ensure_ascii=False)
    
    def _aggregate_category_metrics(
        self,
        reports: list[ReportMetadata],
        category: TestCategory
    ) -> dict[str, Any]:
        """
        聚合分类指标
        
        Args:
            reports: 报告列表
            category: 测试分类
            
        Returns:
            聚合后的指标数据
        """
        summary = {
            "total_reports": len(reports),
            "avg_pass_rate": 0,
            "total_tests": 0,
            "total_passed": 0,
            "total_failed": 0
        }
        
        pass_rates = []
        for report in reports:
            metrics = report.metrics
            if 'pass_rate' in metrics and metrics['pass_rate'] > 0:
                pass_rates.append(metrics['pass_rate'])
            if 'total_tests' in metrics:
                summary["total_tests"] += metrics['total_tests']
            if 'passed' in metrics:
                summary["total_passed"] += metrics['passed']
            if 'failed' in metrics:
                summary["total_failed"] += metrics['failed']
        
        if pass_rates:
            summary["avg_pass_rate"] = round(sum(pass_rates) / len(pass_rates), 2)
        
        if category == TestCategory.PERFORMANCE:
            summary.update(self._aggregate_performance_metrics(reports))
        elif category == TestCategory.SECURITY:
            summary.update(self._aggregate_security_metrics(reports))
        
        return summary
    
    def _aggregate_performance_metrics(self, reports: list[ReportMetadata]) -> dict[str, Any]:
        """聚合性能测试指标"""
        avg_times = []
        throughputs = []
        
        for report in reports:
            if 'avg_response_time' in report.metrics:
                avg_times.append(report.metrics['avg_response_time'])
            if 'throughput' in report.metrics:
                throughputs.append(report.metrics['throughput'])
        
        result = {}
        if avg_times:
            result["avg_response_time"] = round(sum(avg_times) / len(avg_times), 2)
        if throughputs:
            result["avg_throughput"] = round(sum(throughputs) / len(throughputs), 2)
        
        return result
    
    def _aggregate_security_metrics(self, reports: list[ReportMetadata]) -> dict[str, Any]:
        """聚合安全测试指标"""
        result = {
            "total_vulnerabilities": 0,
            "total_critical": 0,
            "total_high": 0,
            "total_medium": 0,
            "total_low": 0
        }
        
        for report in reports:
            result["total_vulnerabilities"] += report.metrics.get('vulnerabilities_found', 0)
            result["total_critical"] += report.metrics.get('critical', 0)
            result["total_high"] += report.metrics.get('high', 0)
            result["total_medium"] += report.metrics.get('medium', 0)
            result["total_low"] += report.metrics.get('low', 0)
        
        return result
    
    def get_category_index(
        self,
        category: TestCategory,
        version: str
    ) -> Optional[dict[str, Any]]:
        """
        获取分类索引
        
        Args:
            category: 测试分类
            version: 版本号
            
        Returns:
            分类索引数据
        """
        index_file = self.index_dir / f"category_{category.value}_{version}.json"
        
        if not index_file.exists():
            return None
        
        with open(index_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def rebuild_category_indexes(self):
        """
        重建所有分类索引
        
        用于修复或更新损坏的索引
        """
        versions = set()
        
        for metadata_file in self.index_dir.glob("*.json"):
            if metadata_file.name.startswith("version_"):
                version = metadata_file.stem.replace("version_", "")
                versions.add(version)
        
        for category_dir in self.category_dirs.iterdir():
            if category_dir.is_dir():
                for version_dir in category_dir.iterdir():
                    if version_dir.is_dir():
                        versions.add(version_dir.name)
        
        for version in versions:
            self._update_category_index(version)
        
        logger.info(f"已重建 {len(versions)} 个版本的分类索引")
    
    def get_reports_by_version_range(
        self,
        start_version: str,
        end_version: str,
        test_category: TestCategory = None
    ) -> dict[str, list[ReportMetadata]]:
        """
        获取版本范围内的报告
        
        Args:
            start_version: 起始版本
            end_version: 结束版本
            test_category: 测试分类（可选）
            
        Returns:
            按版本分组的报告字典
        """
        result = {}
        
        start_sem = SemanticVersion.parse(start_version)
        end_sem = SemanticVersion.parse(end_version)
        
        all_reports = self.list_reports(test_category=test_category)
        
        for report in all_reports:
            report_sem = SemanticVersion.parse(report.version)
            
            if start_sem <= report_sem <= end_sem:
                if report.version not in result:
                    result[report.version] = []
                result[report.version].append(report)
        
        return result
    
    def migrate_reports(
        self,
        source_version: str,
        target_version: str,
        test_category: TestCategory = None
    ) -> int:
        """
        迁移报告到新版本
        
        Args:
            source_version: 源版本
            target_version: 目标版本
            test_category: 测试分类（可选，不指定则迁移所有分类）
            
        Returns:
            迁移的报告数量
        """
        reports = self.list_reports(version=source_version, test_category=test_category)
        migrated_count = 0
        
        for report in reports:
            try:
                source_path = Path(report.file_path)
                if not source_path.exists():
                    continue
                
                if report.test_category:
                    target_dir = self._get_category_dir(report.test_category) / target_version
                else:
                    target_dir = self.reports_dir / target_version
                
                target_dir.mkdir(parents=True, exist_ok=True)
                target_file = target_dir / source_path.name
                
                shutil.copy2(str(source_path), str(target_file))
                
                new_metadata = ReportMetadata(
                    report_id=f"{report.report_type.value}_{datetime.now().strftime('%Y%m%d_%H%M%S')}_migrated",
                    report_type=report.report_type,
                    version=target_version,
                    created_at=datetime.now(),
                    file_path=str(target_file),
                    file_size=target_file.stat().st_size,
                    tags=report.tags + ["migrated"],
                    summary=report.summary,
                    description=f"从 {source_version} 迁移: {report.description}",
                    test_category=report.test_category,
                    metrics=report.metrics
                )
                
                self._save_metadata(new_metadata)
                self._update_index(target_version, new_metadata)
                migrated_count += 1
                
            except Exception as e:
                logger.error(f"迁移报告失败: {report.report_id}, 错误: {e}")
        
        self._update_category_index(target_version)
        logger.info(f"已迁移 {migrated_count} 个报告从 {source_version} 到 {target_version}")
        return migrated_count
    
    def cleanup_old_versions(
        self,
        keep_versions: int = 5,
        archive: bool = True
    ) -> dict[str, Any]:
        """
        清理旧版本报告
        
        Args:
            keep_versions: 保留的版本数量
            archive: 是否归档（否则直接删除）
            
        Returns:
            清理结果统计
        """
        versions = []
        for index_file in self.index_dir.glob("version_*.json"):
            version = index_file.stem.replace("version_", "")
            versions.append(version)
        
        versions.sort(key=lambda v: SemanticVersion.parse(v), reverse=True)
        
        versions_to_remove = versions[keep_versions:]
        
        result = {
            "kept_versions": versions[:keep_versions],
            "removed_versions": versions_to_remove,
            "reports_processed": 0,
            "reports_archived": 0,
            "reports_deleted": 0,
            "space_freed": 0
        }
        
        for version in versions_to_remove:
            reports = self.list_reports(version=version)
            
            for report in reports:
                result["reports_processed"] += 1
                
                if archive:
                    if self.archive_report(report.report_id):
                        result["reports_archived"] += 1
                else:
                    file_path = Path(report.file_path)
                    if file_path.exists():
                        result["space_freed"] += report.file_size
                    
                    if self.delete_report(report.report_id):
                        result["reports_deleted"] += 1
        
        logger.info(f"清理完成: 保留 {len(result['kept_versions'])} 个版本, "
                   f"处理 {result['reports_processed']} 个报告")
        
        return result
    
    def get_storage_summary(self) -> dict[str, Any]:
        """
        获取存储摘要信息
        
        Returns:
            存储摘要数据
        """
        all_reports = self.list_reports()
        
        summary = {
            "total_reports": len(all_reports),
            "total_size_bytes": sum(r.file_size for r in all_reports),
            "total_size_mb": round(sum(r.file_size for r in all_reports) / (1024 * 1024), 2),
            "by_category": {},
            "by_type": {},
            "by_status": {},
            "by_version": {},
            "oldest_report": None,
            "newest_report": None
        }
        
        for report in all_reports:
            category_key = report.test_category.value if report.test_category else "uncategorized"
            summary["by_category"][category_key] = summary["by_category"].get(category_key, 0) + 1
            
            type_key = report.report_type.value
            summary["by_type"][type_key] = summary["by_type"].get(type_key, 0) + 1
            
            status_key = report.status.value
            summary["by_status"][status_key] = summary["by_status"].get(status_key, 0) + 1
            
            summary["by_version"][report.version] = summary["by_version"].get(report.version, 0) + 1
        
        if all_reports:
            sorted_reports = sorted(all_reports, key=lambda x: x.created_at)
            summary["oldest_report"] = sorted_reports[0].created_at.isoformat()
            summary["newest_report"] = sorted_reports[-1].created_at.isoformat()
        
        return summary

    def archive_report(self, report_id: str) -> bool:
        metadata = self.get_report(report_id)
        if not metadata:
            return False

        source_path = Path(metadata.file_path)
        if not source_path.exists():
            return False

        archive_path = self.archive_dir / metadata.version / source_path.name
        archive_path.parent.mkdir(parents=True, exist_ok=True)

        shutil.move(str(source_path), str(archive_path))

        metadata.status = ReportStatus.ARCHIVED
        metadata.file_path = str(archive_path)
        self._save_metadata(metadata)

        logger.info(f"报告已归档: {report_id}")
        return True

    def delete_report(self, report_id: str) -> bool:
        metadata = self.get_report(report_id)
        if not metadata:
            return False

        file_path = Path(metadata.file_path)
        if file_path.exists():
            file_path.unlink()

        metadata_file = self.index_dir / f"{report_id}.json"
        if metadata_file.exists():
            metadata_file.unlink()

        logger.info(f"报告已删除: {report_id}")
        return True

    def merge_reports(
        self,
        report_ids: list[str],
        name: str,
        test_category: Optional[TestCategory] = None,
        tags: list[str] = None
    ) -> Optional[MergedReport]:
        """
        合并多个报告
        
        Args:
            report_ids: 要合并的报告ID列表
            name: 合并报告名称
            test_category: 测试分类
            tags: 标签列表
            
        Returns:
            合并后的报告
        """
        if len(report_ids) < 2:
            logger.warning("至少需要两个报告才能合并")
            return None

        reports = []
        for report_id in report_ids:
            report = self.get_report(report_id)
            if report:
                reports.append(report)

        if len(reports) < 2:
            logger.warning("有效的报告数量不足")
            return None

        merged_id = f"merged_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{hashlib.md5('_'.join(report_ids).encode()).hexdigest()[:8]}"
        
        merged_metrics = self._merge_metrics(reports)
        merged_summary = self._merge_summaries(reports)
        
        versions = list(set(r.version for r in reports))
        all_tags = list(set(tag for r in reports for tag in r.tags))
        if tags:
            all_tags = list(set(all_tags + tags))

        merged = MergedReport(
            merged_id=merged_id,
            name=name,
            created_at=datetime.now(),
            source_reports=report_ids,
            merged_metrics=merged_metrics,
            merged_summary=merged_summary,
            test_category=test_category or reports[0].test_category,
            versions=versions,
            tags=all_tags
        )

        self._save_merged_report(merged)
        
        logger.info(f"报告已合并: {merged_id}, 包含 {len(reports)} 个报告")
        return merged

    def _merge_metrics(self, reports: list[ReportMetadata]) -> dict[str, Any]:
        """合并多个报告的指标"""
        merged = {
            "total_reports": len(reports),
            "total_tests": 0,
            "total_passed": 0,
            "total_failed": 0,
            "total_skipped": 0,
            "avg_pass_rate": 0,
            "total_duration": 0,
            "by_version": {}
        }

        pass_rates = []
        
        for report in reports:
            metrics = report.metrics
            
            merged["total_tests"] += metrics.get("total_tests", 0)
            merged["total_passed"] += metrics.get("passed", 0)
            merged["total_failed"] += metrics.get("failed", 0)
            merged["total_skipped"] += metrics.get("skipped", 0)
            merged["total_duration"] += metrics.get("duration", 0)
            
            if "pass_rate" in metrics and metrics["pass_rate"] > 0:
                pass_rates.append(metrics["pass_rate"])
            
            if report.version not in merged["by_version"]:
                merged["by_version"][report.version] = {
                    "report_count": 0,
                    "total_tests": 0,
                    "passed": 0,
                    "failed": 0
                }
            
            merged["by_version"][report.version]["report_count"] += 1
            merged["by_version"][report.version]["total_tests"] += metrics.get("total_tests", 0)
            merged["by_version"][report.version]["passed"] += metrics.get("passed", 0)
            merged["by_version"][report.version]["failed"] += metrics.get("failed", 0)

        if pass_rates:
            merged["avg_pass_rate"] = round(sum(pass_rates) / len(pass_rates), 2)

        if merged["total_tests"] > 0:
            merged["overall_pass_rate"] = round(
                (merged["total_passed"] / merged["total_tests"]) * 100, 2
            )

        return merged

    def _merge_summaries(self, reports: list[ReportMetadata]) -> dict[str, Any]:
        """合并多个报告的摘要"""
        merged = {
            "total_reports": len(reports),
            "report_types": {},
            "test_categories": {},
            "date_range": {
                "earliest": None,
                "latest": None
            }
        }

        dates = []
        
        for report in reports:
            type_name = report.report_type.value
            if type_name not in merged["report_types"]:
                merged["report_types"][type_name] = 0
            merged["report_types"][type_name] += 1
            
            if report.test_category:
                cat_name = report.test_category.value
                if cat_name not in merged["test_categories"]:
                    merged["test_categories"][cat_name] = 0
                merged["test_categories"][cat_name] += 1
            
            dates.append(report.created_at)

        if dates:
            merged["date_range"]["earliest"] = min(dates).isoformat()
            merged["date_range"]["latest"] = max(dates).isoformat()

        return merged

    def _save_merged_report(self, merged: MergedReport):
        """保存合并报告"""
        merged_dir = self.base_dir / "merged"
        merged_dir.mkdir(parents=True, exist_ok=True)
        
        merged_file = merged_dir / f"{merged.merged_id}.json"
        
        data = {
            "merged_id": merged.merged_id,
            "name": merged.name,
            "created_at": merged.created_at.isoformat(),
            "source_reports": merged.source_reports,
            "merged_metrics": merged.merged_metrics,
            "merged_summary": merged.merged_summary,
            "test_category": merged.test_category.value if merged.test_category else None,
            "versions": merged.versions,
            "tags": merged.tags
        }
        
        with open(merged_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def get_merged_report(self, merged_id: str) -> Optional[MergedReport]:
        """获取合并报告"""
        merged_file = self.base_dir / "merged" / f"{merged_id}.json"
        
        if not merged_file.exists():
            return None
        
        with open(merged_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        test_category = None
        if data.get("test_category"):
            try:
                test_category = TestCategory(data["test_category"])
            except ValueError:
                pass
        
        return MergedReport(
            merged_id=data["merged_id"],
            name=data["name"],
            created_at=datetime.fromisoformat(data["created_at"]),
            source_reports=data["source_reports"],
            merged_metrics=data["merged_metrics"],
            merged_summary=data["merged_summary"],
            test_category=test_category,
            versions=data.get("versions", []),
            tags=data.get("tags", [])
        )

    def list_merged_reports(
        self,
        test_category: TestCategory = None
    ) -> list[MergedReport]:
        """列出合并报告"""
        merged_dir = self.base_dir / "merged"
        
        if not merged_dir.exists():
            return []
        
        merged_reports = []
        for merged_file in merged_dir.glob("merged_*.json"):
            merged = self.get_merged_report(merged_file.stem)
            if merged:
                if test_category and merged.test_category != test_category:
                    continue
                merged_reports.append(merged)
        
        return sorted(merged_reports, key=lambda x: x.created_at, reverse=True)

    def merge_reports_by_category(
        self,
        version: str,
        test_category: TestCategory,
        name: Optional[str] = None
    ) -> Optional[MergedReport]:
        """
        按分类合并版本的所有报告
        
        Args:
            version: 版本号
            test_category: 测试分类
            name: 合并报告名称
            
        Returns:
            合并后的报告
        """
        reports = self.list_reports(version=version, test_category=test_category)
        
        if len(reports) < 2:
            logger.warning(f"版本 {version} 的 {test_category.value} 分类报告数量不足")
            return None

        name = name or f"{test_category.value}_{version}_merged"
        
        return self.merge_reports(
            report_ids=[r.report_id for r in reports],
            name=name,
            test_category=test_category
        )

    def merge_version_reports(
        self,
        version: str,
        name: Optional[str] = None
    ) -> list[MergedReport]:
        """
        合并版本的所有分类报告
        
        Args:
            version: 版本号
            name: 合并报告名称前缀
            
        Returns:
            合并报告列表
        """
        merged_reports = []
        
        for category in TestCategory:
            reports = self.list_reports(version=version, test_category=category)
            
            if len(reports) >= 2:
                merged_name = f"{name or version}_{category.value}_merged"
                merged = self.merge_reports(
                    report_ids=[r.report_id for r in reports],
                    name=merged_name,
                    test_category=category
                )
                if merged:
                    merged_reports.append(merged)
        
        return merged_reports


class ReportExporter:
    """报告导出器"""

    def __init__(self, storage: ReportStorage):
        self.storage = storage

    def export_report(
        self,
        report_id: str,
        config: ExportConfig
    ) -> Optional[str]:
        """
        导出单个报告
        
        Args:
            report_id: 报告ID
            config: 导出配置
            
        Returns:
            导出文件路径
        """
        report = self.storage.get_report(report_id)
        if not report:
            logger.warning(f"报告不存在: {report_id}")
            return None

        if config.format == "json":
            return self._export_json(report, config)
        elif config.format == "html":
            return self._export_html(report, config)
        elif config.format == "pdf":
            return self._export_pdf(report, config)
        else:
            logger.warning(f"不支持的导出格式: {config.format}")
            return None

    def _export_json(self, report: ReportMetadata, config: ExportConfig) -> str:
        """导出为JSON格式"""
        export_data = {
            "report_id": report.report_id,
            "report_type": report.report_type.value,
            "version": report.version,
            "created_at": report.created_at.isoformat(),
            "test_category": report.test_category.value if report.test_category else None,
            "tags": report.tags,
            "description": report.description
        }

        if config.include_summary:
            export_data["summary"] = report.summary

        if config.include_metrics:
            export_data["metrics"] = report.metrics

        if config.include_details:
            export_data["details"] = self._load_report_details(report)

        output_path = self._get_output_path(report, "json", config)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False)

        logger.info(f"报告已导出为JSON: {output_path}")
        return str(output_path)

    def _export_html(self, report: ReportMetadata, config: ExportConfig) -> str:
        """导出为HTML格式"""
        html_content = self._generate_html_report(report, config)
        
        output_path = self._get_output_path(report, "html", config)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)

        logger.info(f"报告已导出为HTML: {output_path}")
        return str(output_path)

    def _export_pdf(self, report: ReportMetadata, config: ExportConfig) -> str:
        """导出为PDF格式（生成HTML后提示转换）"""
        html_content = self._generate_html_report(report, config, for_pdf=True)
        
        html_path = self._get_output_path(report, "html", config, suffix="_for_pdf")
        
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(html_content)

        output_path = self._get_output_path(report, "pdf", config)
        
        try:
            import subprocess
            result = subprocess.run(
                ['wkhtmltopdf', str(html_path), str(output_path)],
                capture_output=True,
                text=True,
                timeout=60
            )
            if result.returncode == 0:
                logger.info(f"报告已导出为PDF: {output_path}")
                return str(output_path)
        except FileNotFoundError:
            logger.warning("wkhtmltopdf 未安装，将保存为HTML格式")
        except subprocess.TimeoutExpired:
            logger.warning("PDF转换超时，将保存为HTML格式")
        except Exception as e:
            logger.warning(f"PDF转换失败: {e}，将保存为HTML格式")

        logger.info(f"报告已导出为HTML（PDF转换失败）: {html_path}")
        return str(html_path)

    def _generate_html_report(
        self,
        report: ReportMetadata,
        config: ExportConfig,
        for_pdf: bool = False
    ) -> str:
        """生成HTML报告内容"""
        category_name = report.test_category.value if report.test_category else "未分类"
        
        html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>测试报告 - {report.report_id}</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        .container {{
            background-color: white;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            padding: 30px;
        }}
        h1 {{
            color: #2c3e50;
            border-bottom: 2px solid #3498db;
            padding-bottom: 10px;
        }}
        h2 {{
            color: #34495e;
            margin-top: 30px;
        }}
        .meta-info {{
            background-color: #ecf0f1;
            padding: 15px;
            border-radius: 4px;
            margin-bottom: 20px;
        }}
        .meta-info p {{
            margin: 5px 0;
        }}
        .metrics-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin: 20px 0;
        }}
        .metric-card {{
            background-color: #f8f9fa;
            border-left: 4px solid #3498db;
            padding: 15px;
            border-radius: 4px;
        }}
        .metric-card h3 {{
            margin: 0 0 10px 0;
            color: #7f8c8d;
            font-size: 14px;
        }}
        .metric-card .value {{
            font-size: 24px;
            font-weight: bold;
            color: #2c3e50;
        }}
        .pass-rate {{
            border-left-color: #27ae60;
        }}
        .pass-rate .value {{
            color: #27ae60;
        }}
        .fail-count {{
            border-left-color: #e74c3c;
        }}
        .fail-count .value {{
            color: #e74c3c;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
        }}
        th, td {{
            border: 1px solid #ddd;
            padding: 12px;
            text-align: left;
        }}
        th {{
            background-color: #3498db;
            color: white;
        }}
        tr:nth-child(even) {{
            background-color: #f2f2f2;
        }}
        .tag {{
            display: inline-block;
            background-color: #3498db;
            color: white;
            padding: 2px 8px;
            border-radius: 12px;
            font-size: 12px;
            margin-right: 5px;
        }}
        .footer {{
            margin-top: 30px;
            padding-top: 20px;
            border-top: 1px solid #ddd;
            color: #7f8c8d;
            font-size: 12px;
        }}
        @media print {{
            body {{
                background-color: white;
            }}
            .container {{
                box-shadow: none;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>测试报告</h1>
        
        <div class="meta-info">
            <p><strong>报告ID:</strong> {report.report_id}</p>
            <p><strong>报告类型:</strong> {report.report_type.value}</p>
            <p><strong>版本:</strong> {report.version}</p>
            <p><strong>测试分类:</strong> {category_name}</p>
            <p><strong>创建时间:</strong> {report.created_at.strftime('%Y-%m-%d %H:%M:%S')}</p>
            <p><strong>状态:</strong> {report.status.value}</p>
            <p><strong>标签:</strong> {' '.join(f'<span class="tag">{tag}</span>' for tag in report.tags)}</p>
        </div>
"""

        if report.description:
            html += f"""
        <h2>描述</h2>
        <p>{report.description}</p>
"""

        if config.include_metrics and report.metrics:
            html += """
        <h2>关键指标</h2>
        <div class="metrics-grid">
"""
            
            pass_rate = report.metrics.get("pass_rate", report.metrics.get("overall_pass_rate", 0))
            total_tests = report.metrics.get("total_tests", 0)
            passed = report.metrics.get("passed", 0)
            failed = report.metrics.get("failed", 0)
            duration = report.metrics.get("duration", 0)
            
            html += f"""
            <div class="metric-card pass-rate">
                <h3>通过率</h3>
                <div class="value">{pass_rate:.1f}%</div>
            </div>
            <div class="metric-card">
                <h3>总测试数</h3>
                <div class="value">{total_tests}</div>
            </div>
            <div class="metric-card">
                <h3>通过数</h3>
                <div class="value">{passed}</div>
            </div>
            <div class="metric-card fail-count">
                <h3>失败数</h3>
                <div class="value">{failed}</div>
            </div>
            <div class="metric-card">
                <h3>执行时间</h3>
                <div class="value">{duration:.2f}s</div>
            </div>
"""
            html += "        </div>\n"

            other_metrics = {k: v for k, v in report.metrics.items() 
                           if k not in ["pass_rate", "overall_pass_rate", "total_tests", "passed", "failed", "duration", "category", "extracted_at"]}
            
            if other_metrics:
                html += """
        <h2>其他指标</h2>
        <table>
            <tr><th>指标名称</th><th>值</th></tr>
"""
                for key, value in other_metrics.items():
                    if isinstance(value, (int, float, str)):
                        html += f"            <tr><td>{key}</td><td>{value}</td></tr>\n"
                html += "        </table>\n"

        if config.include_summary and report.summary:
            html += """
        <h2>摘要信息</h2>
        <table>
            <tr><th>项目</th><th>值</th></tr>
"""
            for key, value in report.summary.items():
                if isinstance(value, (int, float, str)):
                    html += f"            <tr><td>{key}</td><td>{value}</td></tr>\n"
                elif isinstance(value, dict):
                    html += f"            <tr><td>{key}</td><td>{json.dumps(value, ensure_ascii=False)}</td></tr>\n"
            html += "        </table>\n"

        html += f"""
        <div class="footer">
            <p>报告生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            <p>报告导出工具: ReportVersionManager</p>
        </div>
    </div>
</body>
</html>"""

        return html

    def _get_output_path(
        self,
        report: ReportMetadata,
        format: str,
        config: ExportConfig,
        suffix: str = ""
    ) -> Path:
        """获取输出路径"""
        if config.output_path:
            return Path(config.output_path)
        
        export_dir = self.storage.base_dir / "exports"
        export_dir.mkdir(parents=True, exist_ok=True)
        
        filename = f"{report.report_id}{suffix}.{format}"
        return export_dir / filename

    def _load_report_details(self, report: ReportMetadata) -> dict[str, Any]:
        """加载报告详情"""
        file_path = Path(report.file_path)
        
        if not file_path.exists():
            return {}
        
        if file_path.suffix == '.json':
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception:
                return {}
        
        return {"file_path": str(file_path)}

    def export_merged_report(
        self,
        merged_id: str,
        config: ExportConfig
    ) -> Optional[str]:
        """
        导出合并报告
        
        Args:
            merged_id: 合并报告ID
            config: 导出配置
            
        Returns:
            导出文件路径
        """
        merged = self.storage.get_merged_report(merged_id)
        if not merged:
            logger.warning(f"合并报告不存在: {merged_id}")
            return None

        if config.format == "json":
            return self._export_merged_json(merged, config)
        elif config.format == "html":
            return self._export_merged_html(merged, config)
        else:
            logger.warning(f"不支持的导出格式: {config.format}")
            return None

    def _export_merged_json(self, merged: MergedReport, config: ExportConfig) -> str:
        """导出合并报告为JSON"""
        export_data = {
            "merged_id": merged.merged_id,
            "name": merged.name,
            "created_at": merged.created_at.isoformat(),
            "test_category": merged.test_category.value if merged.test_category else None,
            "versions": merged.versions,
            "tags": merged.tags,
            "source_reports": merged.source_reports
        }

        if config.include_summary:
            export_data["summary"] = merged.merged_summary

        if config.include_metrics:
            export_data["metrics"] = merged.merged_metrics

        output_path = self._get_merged_output_path(merged, "json", config)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False)

        logger.info(f"合并报告已导出为JSON: {output_path}")
        return str(output_path)

    def _export_merged_html(self, merged: MergedReport, config: ExportConfig) -> str:
        """导出合并报告为HTML"""
        html_content = self._generate_merged_html_report(merged, config)
        
        output_path = self._get_merged_output_path(merged, "html", config)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)

        logger.info(f"合并报告已导出为HTML: {output_path}")
        return str(output_path)

    def _generate_merged_html_report(
        self,
        merged: MergedReport,
        config: ExportConfig
    ) -> str:
        """生成合并报告HTML"""
        category_name = merged.test_category.value if merged.test_category else "未分类"
        
        html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>合并报告 - {merged.name}</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        .container {{
            background-color: white;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            padding: 30px;
        }}
        h1 {{
            color: #2c3e50;
            border-bottom: 2px solid #9b59b6;
            padding-bottom: 10px;
        }}
        h2 {{
            color: #34495e;
            margin-top: 30px;
        }}
        .meta-info {{
            background-color: #ecf0f1;
            padding: 15px;
            border-radius: 4px;
            margin-bottom: 20px;
        }}
        .metrics-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin: 20px 0;
        }}
        .metric-card {{
            background-color: #f8f9fa;
            border-left: 4px solid #9b59b6;
            padding: 15px;
            border-radius: 4px;
        }}
        .metric-card h3 {{
            margin: 0 0 10px 0;
            color: #7f8c8d;
            font-size: 14px;
        }}
        .metric-card .value {{
            font-size: 24px;
            font-weight: bold;
            color: #2c3e50;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
        }}
        th, td {{
            border: 1px solid #ddd;
            padding: 12px;
            text-align: left;
        }}
        th {{
            background-color: #9b59b6;
            color: white;
        }}
        tr:nth-child(even) {{
            background-color: #f2f2f2;
        }}
        .tag {{
            display: inline-block;
            background-color: #9b59b6;
            color: white;
            padding: 2px 8px;
            border-radius: 12px;
            font-size: 12px;
            margin-right: 5px;
        }}
        .footer {{
            margin-top: 30px;
            padding-top: 20px;
            border-top: 1px solid #ddd;
            color: #7f8c8d;
            font-size: 12px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>合并测试报告</h1>
        
        <div class="meta-info">
            <p><strong>合并ID:</strong> {merged.merged_id}</p>
            <p><strong>名称:</strong> {merged.name}</p>
            <p><strong>测试分类:</strong> {category_name}</p>
            <p><strong>创建时间:</strong> {merged.created_at.strftime('%Y-%m-%d %H:%M:%S')}</p>
            <p><strong>包含版本:</strong> {', '.join(merged.versions)}</p>
            <p><strong>标签:</strong> {' '.join(f'<span class="tag">{tag}</span>' for tag in merged.tags)}</p>
            <p><strong>源报告数量:</strong> {len(merged.source_reports)}</p>
        </div>
"""

        if config.include_metrics and merged.merged_metrics:
            html += """
        <h2>合并指标</h2>
        <div class="metrics-grid">
"""
            
            total_tests = merged.merged_metrics.get("total_tests", 0)
            total_passed = merged.merged_metrics.get("total_passed", 0)
            total_failed = merged.merged_metrics.get("total_failed", 0)
            avg_pass_rate = merged.merged_metrics.get("avg_pass_rate", 0)
            overall_pass_rate = merged.merged_metrics.get("overall_pass_rate", 0)
            
            html += f"""
            <div class="metric-card">
                <h3>总测试数</h3>
                <div class="value">{total_tests}</div>
            </div>
            <div class="metric-card">
                <h3>总通过数</h3>
                <div class="value">{total_passed}</div>
            </div>
            <div class="metric-card">
                <h3>总失败数</h3>
                <div class="value">{total_failed}</div>
            </div>
            <div class="metric-card">
                <h3>平均通过率</h3>
                <div class="value">{avg_pass_rate:.1f}%</div>
            </div>
            <div class="metric-card">
                <h3>整体通过率</h3>
                <div class="value">{overall_pass_rate:.1f}%</div>
            </div>
"""
            html += "        </div>\n"

            by_version = merged.merged_metrics.get("by_version", {})
            if by_version:
                html += """
        <h2>按版本统计</h2>
        <table>
            <tr><th>版本</th><th>报告数</th><th>总测试数</th><th>通过数</th><th>失败数</th></tr>
"""
                for version, stats in by_version.items():
                    html += f"""
            <tr>
                <td>{version}</td>
                <td>{stats.get('report_count', 0)}</td>
                <td>{stats.get('total_tests', 0)}</td>
                <td>{stats.get('passed', 0)}</td>
                <td>{stats.get('failed', 0)}</td>
            </tr>
"""
                html += "        </table>\n"

        if config.include_summary and merged.merged_summary:
            html += """
        <h2>摘要信息</h2>
        <table>
            <tr><th>项目</th><th>值</th></tr>
"""
            for key, value in merged.merged_summary.items():
                if isinstance(value, (int, float, str)):
                    html += f"            <tr><td>{key}</td><td>{value}</td></tr>\n"
            html += "        </table>\n"

        html += f"""
        <div class="footer">
            <p>报告生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            <p>报告导出工具: ReportVersionManager</p>
        </div>
    </div>
</body>
</html>"""

        return html

    def _get_merged_output_path(
        self,
        merged: MergedReport,
        format: str,
        config: ExportConfig
    ) -> Path:
        """获取合并报告输出路径"""
        if config.output_path:
            return Path(config.output_path)
        
        export_dir = self.storage.base_dir / "exports"
        export_dir.mkdir(parents=True, exist_ok=True)
        
        filename = f"{merged.merged_id}.{format}"
        return export_dir / filename

    def export_batch(
        self,
        report_ids: list[str],
        config: ExportConfig
    ) -> dict[str, str]:
        """
        批量导出报告
        
        Args:
            report_ids: 报告ID列表
            config: 导出配置
            
        Returns:
            导出结果字典 {report_id: output_path}
        """
        results = {}
        
        for report_id in report_ids:
            output_path = self.export_report(report_id, config)
            if output_path:
                results[report_id] = output_path
        
        return results

    def export_trend_report(
        self,
        test_category: TestCategory,
        days: int,
        config: ExportConfig
    ) -> Optional[str]:
        """
        导出趋势分析报告
        
        Args:
            test_category: 测试分类
            days: 分析天数
            config: 导出配置
            
        Returns:
            导出文件路径
        """
        analyzer = ReportTrendAnalyzer(self.storage)
        trend_report = analyzer.export_trend_report(test_category, days=days)
        
        if config.format == "json":
            output_path = self._get_trend_output_path(test_category, "json", config)
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(trend_report, f, indent=2, ensure_ascii=False)
            return str(output_path)
        elif config.format == "html":
            html_content = self._generate_trend_html(trend_report, test_category, days)
            output_path = self._get_trend_output_path(test_category, "html", config)
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
            return str(output_path)
        
        return None

    def _get_trend_output_path(
        self,
        test_category: TestCategory,
        format: str,
        config: ExportConfig
    ) -> Path:
        """获取趋势报告输出路径"""
        if config.output_path:
            return Path(config.output_path)
        
        export_dir = self.storage.base_dir / "exports"
        export_dir.mkdir(parents=True, exist_ok=True)
        
        filename = f"trend_{test_category.value}_{datetime.now().strftime('%Y%m%d')}.{format}"
        return export_dir / filename

    def _generate_trend_html(
        self,
        trend_report: dict[str, Any],
        test_category: TestCategory,
        days: int
    ) -> str:
        """生成趋势报告HTML"""
        html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>趋势分析报告 - {test_category.value}</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        .container {{
            background-color: white;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            padding: 30px;
            margin-bottom: 20px;
        }}
        h1 {{
            color: #2c3e50;
            border-bottom: 2px solid #e67e22;
            padding-bottom: 10px;
        }}
        h2 {{
            color: #34495e;
            margin-top: 20px;
        }}
        .risk-critical {{ color: #e74c3c; }}
        .risk-high {{ color: #e67e22; }}
        .risk-medium {{ color: #f39c12; }}
        .risk-low {{ color: #27ae60; }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
        }}
        th, td {{
            border: 1px solid #ddd;
            padding: 12px;
            text-align: left;
        }}
        th {{
            background-color: #e67e22;
            color: white;
        }}
        tr:nth-child(even) {{
            background-color: #f2f2f2;
        }}
        .stat-box {{
            display: inline-block;
            background-color: #f8f9fa;
            padding: 15px 20px;
            border-radius: 4px;
            margin: 5px;
        }}
        .stat-box strong {{
            display: block;
            color: #7f8c8d;
            font-size: 12px;
        }}
        .stat-box span {{
            font-size: 24px;
            font-weight: bold;
            color: #2c3e50;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>趋势分析报告</h1>
        <p><strong>测试分类:</strong> {test_category.value}</p>
        <p><strong>分析周期:</strong> 最近 {days} 天</p>
        <p><strong>生成时间:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
    </div>
"""

        risk_analysis = trend_report.get("risk_analysis", {})
        if risk_analysis:
            risk_level = risk_analysis.get("risk_level", "unknown")
            risk_class = f"risk-{risk_level}" if risk_level in ["critical", "high", "medium", "low"] else ""
            
            html += f"""
    <div class="container">
        <h2>风险分析</h2>
        <p><strong>风险等级:</strong> <span class="{risk_class}">{risk_level.upper()}</span></p>
        <p><strong>风险分数:</strong> {risk_analysis.get('risk_score', 0)}/100</p>
        
        <h3>风险因素</h3>
        <table>
            <tr><th>因素</th><th>严重程度</th><th>描述</th></tr>
"""
            for factor in risk_analysis.get("risk_factors", []):
                html += f"""
            <tr>
                <td>{factor.get('factor', '')}</td>
                <td>{factor.get('severity', '')}</td>
                <td>{factor.get('description', '')}</td>
            </tr>
"""
            html += "        </table>\n"
            
            if risk_analysis.get("recommendations"):
                html += """
        <h3>建议</h3>
        <ul>
"""
                for rec in risk_analysis["recommendations"]:
                    html += f"            <li>{rec}</li>\n"
                html += "        </ul>\n"
            
            html += "    </div>\n"

        analyses = trend_report.get("analyses", {})
        if analyses:
            html += """
    <div class="container">
        <h2>分析数据</h2>
"""
            for analysis_name, analysis_data in analyses.items():
                stats = analysis_data.get("statistics", {})
                html += f"""
        <h3>{analysis_name}</h3>
        <div class="stat-box">
            <strong>趋势方向</strong>
            <span>{analysis_data.get('trend_direction', 'unknown')}</span>
        </div>
        <div class="stat-box">
            <strong>变化率</strong>
            <span>{analysis_data.get('change_rate', 0):.2f}%</span>
        </div>
        <div class="stat-box">
            <strong>平均值</strong>
            <span>{stats.get('average', 0):.2f}</span>
        </div>
        <div class="stat-box">
            <strong>最小值</strong>
            <span>{stats.get('minimum', 0):.2f}</span>
        </div>
        <div class="stat-box">
            <strong>最大值</strong>
            <span>{stats.get('maximum', 0):.2f}</span>
        </div>
"""
            html += "    </div>\n"

        html += """
</body>
</html>"""

        return html


class ReportIndexManager:
    """报告索引管理器"""

    def __init__(self, storage: ReportStorage):
        self.storage = storage

    def get_version_index(self, version: str) -> Optional[ReportIndex]:
        index_file = self.storage.index_dir / f"version_{version}.json"

        if not index_file.exists():
            return None

        with open(index_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        return ReportIndex(
            version=data['version'],
            reports=data['reports'],
            created_at=datetime.fromisoformat(data['created_at']),
            total_size=data.get('total_size', 0),
            summary=data.get('summary', {})
        )

    def list_versions(self) -> list[ReportIndex]:
        versions = []

        for index_file in self.storage.index_dir.glob("version_*.json"):
            version = index_file.stem.replace("version_", "")
            index = self.get_version_index(version)
            if index:
                versions.append(index)

        return sorted(versions, key=lambda x: x.created_at, reverse=True)

    def get_reports_by_type(self, version: str) -> dict[str, list[ReportMetadata]]:
        reports = self.storage.list_reports(version=version)
        by_type = {}

        for report in reports:
            type_name = report.report_type.value
            if type_name not in by_type:
                by_type[type_name] = []
            by_type[type_name].append(report)

        return by_type

    def generate_summary(self, version: str) -> dict[str, Any]:
        reports = self.storage.list_reports(version=version)

        summary = {
            "version": version,
            "total_reports": len(reports),
            "by_type": {},
            "total_size": sum(r.file_size for r in reports),
            "earliest_report": None,
            "latest_report": None
        }

        for report in reports:
            type_name = report.report_type.value
            if type_name not in summary["by_type"]:
                summary["by_type"][type_name] = 0
            summary["by_type"][type_name] += 1

        if reports:
            sorted_reports = sorted(reports, key=lambda x: x.created_at)
            summary["earliest_report"] = sorted_reports[0].created_at.isoformat()
            summary["latest_report"] = sorted_reports[-1].created_at.isoformat()

        return summary


class ReportHistoryQuery:
    """报告历史查询器"""

    def __init__(self, storage: ReportStorage):
        self.storage = storage

    def query_by_date_range(
        self,
        start_date: datetime,
        end_date: datetime,
        report_type: ReportType = None
    ) -> list[ReportMetadata]:
        reports = self.storage.list_reports(report_type=report_type)

        return [
            r for r in reports
            if start_date <= r.created_at <= end_date
        ]

    def query_by_tags(self, tags: list[str]) -> list[ReportMetadata]:
        reports = self.storage.list_reports()

        return [
            r for r in reports
            if any(tag in r.tags for tag in tags)
        ]

    def query_by_status(self, status: ReportStatus) -> list[ReportMetadata]:
        reports = self.storage.list_reports()

        return [r for r in reports if r.status == status]

    def get_trend_data(
        self,
        report_type: ReportType,
        days: int = 30
    ) -> list[dict[str, Any]]:
        cutoff = datetime.now() - timedelta(days=days)
        reports = self.storage.list_reports(report_type=report_type)

        trend_data = []
        for report in reports:
            if report.created_at >= cutoff:
                trend_data.append({
                    "report_id": report.report_id,
                    "version": report.version,
                    "created_at": report.created_at.isoformat(),
                    "summary": report.summary
                })

        return sorted(trend_data, key=lambda x: x["created_at"])


class TrendPoint:
    """趋势数据点"""

    def __init__(
        self,
        timestamp: datetime,
        value: float,
        metadata: dict[str, Any] = None
    ):
        self.timestamp = timestamp
        self.value = value
        self.metadata = metadata or {}

    def to_dict(self) -> dict[str, Any]:
        return {
            "timestamp": self.timestamp.isoformat(),
            "value": self.value,
            "metadata": self.metadata
        }


class TrendAnalysisResult:
    """趋势分析结果"""

    def __init__(self, metric_name: str):
        self.metric_name = metric_name
        self.data_points: list[TrendPoint] = []
        self.trend_direction: str = "stable"
        self.change_rate: float = 0.0
        self.average: float = 0.0
        self.minimum: float = 0.0
        self.maximum: float = 0.0
        self.std_deviation: float = 0.0
        self.predictions: list[TrendPoint] = []
        self.anomalies: list[dict[str, Any]] = []

    def to_dict(self) -> dict[str, Any]:
        return {
            "metric_name": self.metric_name,
            "data_points": [p.to_dict() for p in self.data_points],
            "trend_direction": self.trend_direction,
            "change_rate": self.change_rate,
            "statistics": {
                "average": self.average,
                "minimum": self.minimum,
                "maximum": self.maximum,
                "std_deviation": self.std_deviation
            },
            "predictions": [p.to_dict() for p in self.predictions],
            "anomalies": self.anomalies
        }


class ReportTrendAnalyzer:
    """报告趋势分析器"""

    def __init__(self, storage: ReportStorage):
        self.storage = storage

    def analyze_pass_rate_trend(
        self,
        test_category: TestCategory,
        days: int = 30
    ) -> TrendAnalysisResult:
        result = TrendAnalysisResult(f"{test_category.value}_pass_rate")

        cutoff = datetime.now() - timedelta(days=days)
        reports = self.storage.list_reports(test_category=test_category)

        for report in reports:
            if report.created_at < cutoff:
                continue

            pass_rate = report.metrics.get('pass_rate', 0)
            if pass_rate > 0:
                point = TrendPoint(
                    timestamp=report.created_at,
                    value=pass_rate,
                    metadata={
                        "report_id": report.report_id,
                        "version": report.version
                    }
                )
                result.data_points.append(point)

        self._calculate_trend_statistics(result)
        self._detect_anomalies(result)
        self._predict_trend(result)

        return result

    def analyze_test_count_trend(
        self,
        test_category: TestCategory,
        days: int = 30
    ) -> TrendAnalysisResult:
        result = TrendAnalysisResult(f"{test_category.value}_test_count")

        cutoff = datetime.now() - timedelta(days=days)
        reports = self.storage.list_reports(test_category=test_category)

        for report in reports:
            if report.created_at < cutoff:
                continue

            total_tests = report.metrics.get('total_tests', 0)
            if total_tests > 0:
                point = TrendPoint(
                    timestamp=report.created_at,
                    value=float(total_tests),
                    metadata={
                        "report_id": report.report_id,
                        "version": report.version
                    }
                )
                result.data_points.append(point)

        self._calculate_trend_statistics(result)
        self._detect_anomalies(result)
        self._predict_trend(result)

        return result

    def analyze_performance_trend(
        self,
        metric_key: str = "avg_response_time",
        days: int = 30
    ) -> TrendAnalysisResult:
        result = TrendAnalysisResult(f"performance_{metric_key}")

        cutoff = datetime.now() - timedelta(days=days)
        reports = self.storage.list_reports(test_category=TestCategory.PERFORMANCE)

        for report in reports:
            if report.created_at < cutoff:
                continue

            value = report.metrics.get(metric_key, 0)
            if value > 0:
                point = TrendPoint(
                    timestamp=report.created_at,
                    value=float(value),
                    metadata={
                        "report_id": report.report_id,
                        "version": report.version
                    }
                )
                result.data_points.append(point)

        self._calculate_trend_statistics(result)
        self._detect_anomalies(result)
        self._predict_trend(result)

        return result

    def analyze_security_trend(self, days: int = 30) -> TrendAnalysisResult:
        result = TrendAnalysisResult("security_vulnerabilities")

        cutoff = datetime.now() - timedelta(days=days)
        reports = self.storage.list_reports(test_category=TestCategory.SECURITY)

        for report in reports:
            if report.created_at < cutoff:
                continue

            vuln_count = report.metrics.get('vulnerabilities_found', 0)
            point = TrendPoint(
                timestamp=report.created_at,
                value=float(vuln_count),
                metadata={
                    "report_id": report.report_id,
                    "version": report.version,
                    "critical": report.metrics.get('critical', 0),
                    "high": report.metrics.get('high', 0),
                    "medium": report.metrics.get('medium', 0),
                    "low": report.metrics.get('low', 0)
                }
            )
            result.data_points.append(point)

        self._calculate_trend_statistics(result)
        self._detect_anomalies(result)
        self._predict_trend(result)

        return result

    def analyze_all_categories(self, days: int = 30) -> dict[str, TrendAnalysisResult]:
        results = {}

        for category in TestCategory:
            if category == TestCategory.PERFORMANCE:
                results[f"{category.value}_response_time"] = self.analyze_performance_trend(
                    "avg_response_time", days
                )
            elif category == TestCategory.SECURITY:
                results[f"{category.value}_vulnerabilities"] = self.analyze_security_trend(days)
            else:
                results[f"{category.value}_pass_rate"] = self.analyze_pass_rate_trend(category, days)
                results[f"{category.value}_test_count"] = self.analyze_test_count_trend(category, days)

        return results

    def get_comparison_summary(
        self,
        test_category: TestCategory,
        days: int = 7
    ) -> dict[str, Any]:
        cutoff = datetime.now() - timedelta(days=days)
        reports = self.storage.list_reports(test_category=test_category)

        recent_reports = [r for r in reports if r.created_at >= cutoff]
        older_reports = [r for r in reports if r.created_at < cutoff]

        def calc_avg_metric(report_list: list[ReportMetadata], metric_key: str) -> float:
            values = [r.metrics.get(metric_key, 0) for r in report_list]
            values = [v for v in values if v > 0]
            return sum(values) / len(values) if values else 0

        summary = {
            "category": test_category.value,
            "period_days": days,
            "recent_reports": len(recent_reports),
            "older_reports": len(older_reports),
            "metrics_comparison": {}
        }

        metric_keys = ['pass_rate', 'total_tests', 'duration']
        for key in metric_keys:
            recent_avg = calc_avg_metric(recent_reports, key)
            older_avg = calc_avg_metric(older_reports, key)

            change = recent_avg - older_avg
            change_pct = (change / older_avg * 100) if older_avg > 0 else 0

            summary["metrics_comparison"][key] = {
                "recent_avg": round(recent_avg, 2),
                "older_avg": round(older_avg, 2),
                "change": round(change, 2),
                "change_percent": round(change_pct, 2)
            }

        return summary

    def _calculate_trend_statistics(self, result: TrendAnalysisResult):
        if not result.data_points:
            return

        values = [p.value for p in result.data_points]

        result.average = sum(values) / len(values)
        result.minimum = min(values)
        result.maximum = max(values)

        if len(values) > 1:
            variance = sum((v - result.average) ** 2 for v in values) / len(values)
            result.std_deviation = variance ** 0.5

        if len(values) >= 2:
            first_val = values[0]
            last_val = values[-1]
            if first_val != 0:
                result.change_rate = ((last_val - first_val) / first_val) * 100

            if result.change_rate > 5:
                result.trend_direction = "increasing"
            elif result.change_rate < -5:
                result.trend_direction = "decreasing"
            else:
                result.trend_direction = "stable"

    def _detect_anomalies(self, result: TrendAnalysisResult):
        if len(result.data_points) < 3 or result.std_deviation == 0:
            return

        threshold = 2 * result.std_deviation

        for point in result.data_points:
            deviation = abs(point.value - result.average)
            if deviation > threshold:
                anomaly = {
                    "timestamp": point.timestamp.isoformat(),
                    "value": point.value,
                    "expected_range": [
                        result.average - threshold,
                        result.average + threshold
                    ],
                    "deviation": deviation,
                    "metadata": point.metadata
                }
                result.anomalies.append(anomaly)

    def _predict_trend(self, result: TrendAnalysisResult):
        if len(result.data_points) < 3:
            return

        values = [p.value for p in result.data_points]
        n = len(values)

        x_sum = sum(range(n))
        y_sum = sum(values)
        xy_sum = sum(i * values[i] for i in range(n))
        x_sq_sum = sum(i * i for i in range(n))

        denominator = n * x_sq_sum - x_sum * x_sum
        if denominator == 0:
            return

        slope = (n * xy_sum - x_sum * y_sum) / denominator
        intercept = (y_sum - slope * x_sum) / n

        for i in range(1, 4):
            future_x = n - 1 + i
            predicted_value = slope * future_x + intercept

            if result.minimum > 0:
                predicted_value = max(0, predicted_value)

            prediction = TrendPoint(
                timestamp=datetime.now() + timedelta(days=i),
                value=predicted_value,
                metadata={"prediction": True, "days_ahead": i}
            )
            result.predictions.append(prediction)
    
    def analyze_duration_trend(
        self,
        test_category: TestCategory,
        days: int = 30
    ) -> TrendAnalysisResult:
        """
        分析测试执行时间趋势
        
        Args:
            test_category: 测试分类
            days: 分析天数
            
        Returns:
            趋势分析结果
        """
        result = TrendAnalysisResult(f"{test_category.value}_duration")
        
        cutoff = datetime.now() - timedelta(days=days)
        reports = self.storage.list_reports(test_category=test_category)
        
        for report in reports:
            if report.created_at < cutoff:
                continue
            
            duration = report.metrics.get('duration', 0)
            if duration > 0:
                point = TrendPoint(
                    timestamp=report.created_at,
                    value=float(duration),
                    metadata={
                        "report_id": report.report_id,
                        "version": report.version
                    }
                )
                result.data_points.append(point)
        
        self._calculate_trend_statistics(result)
        self._detect_anomalies(result)
        self._predict_trend(result)
        
        return result
    
    def analyze_failure_rate_trend(
        self,
        test_category: TestCategory,
        days: int = 30
    ) -> TrendAnalysisResult:
        """
        分析失败率趋势
        
        Args:
            test_category: 测试分类
            days: 分析天数
            
        Returns:
            趋势分析结果
        """
        result = TrendAnalysisResult(f"{test_category.value}_failure_rate")
        
        cutoff = datetime.now() - timedelta(days=days)
        reports = self.storage.list_reports(test_category=test_category)
        
        for report in reports:
            if report.created_at < cutoff:
                continue
            
            total = report.metrics.get('total_tests', 0)
            failed = report.metrics.get('failed', 0)
            
            if total > 0:
                failure_rate = (failed / total) * 100
                point = TrendPoint(
                    timestamp=report.created_at,
                    value=failure_rate,
                    metadata={
                        "report_id": report.report_id,
                        "version": report.version,
                        "total_tests": total,
                        "failed_tests": failed
                    }
                )
                result.data_points.append(point)
        
        self._calculate_trend_statistics(result)
        self._detect_anomalies(result)
        self._predict_trend(result)
        
        return result
    
    def analyze_flakiness_trend(
        self,
        test_category: TestCategory,
        days: int = 30
    ) -> TrendAnalysisResult:
        """
        分析测试不稳定性趋势
        
        通过分析通过率的波动来评估测试的不稳定性
        
        Args:
            test_category: 测试分类
            days: 分析天数
            
        Returns:
            趋势分析结果
        """
        result = TrendAnalysisResult(f"{test_category.value}_flakiness")
        
        cutoff = datetime.now() - timedelta(days=days)
        reports = self.storage.list_reports(test_category=test_category)
        
        pass_rates = []
        for report in reports:
            if report.created_at < cutoff:
                continue
            
            pass_rate = report.metrics.get('pass_rate', 0)
            if pass_rate > 0:
                pass_rates.append((report.created_at, pass_rate, report.report_id, report.version))
        
        if len(pass_rates) < 2:
            return result
        
        sorted_rates = sorted(pass_rates, key=lambda x: x[0])
        
        for i in range(1, len(sorted_rates)):
            prev_rate = sorted_rates[i-1][1]
            curr_rate = sorted_rates[i][1]
            
            flakiness = abs(curr_rate - prev_rate)
            
            point = TrendPoint(
                timestamp=sorted_rates[i][0],
                value=flakiness,
                metadata={
                    "report_id": sorted_rates[i][2],
                    "version": sorted_rates[i][3],
                    "prev_pass_rate": prev_rate,
                    "curr_pass_rate": curr_rate
                }
            )
            result.data_points.append(point)
        
        self._calculate_trend_statistics(result)
        self._detect_anomalies(result)
        
        return result
    
    def generate_visualization_data(
        self,
        test_category: TestCategory,
        metrics: list[str] = None,
        days: int = 30
    ) -> dict[str, Any]:
        """
        生成可视化数据
        
        生成可用于图表展示的数据格式
        
        Args:
            test_category: 测试分类
            metrics: 要分析的指标列表
            days: 分析天数
            
        Returns:
            可视化数据
        """
        if metrics is None:
            metrics = ['pass_rate', 'test_count', 'duration']
        
        visualization = {
            "category": test_category.value,
            "period_days": days,
            "generated_at": datetime.now().isoformat(),
            "charts": {}
        }
        
        for metric in metrics:
            if metric == 'pass_rate':
                result = self.analyze_pass_rate_trend(test_category, days)
            elif metric == 'test_count':
                result = self.analyze_test_count_trend(test_category, days)
            elif metric == 'duration':
                result = self.analyze_duration_trend(test_category, days)
            elif metric == 'failure_rate':
                result = self.analyze_failure_rate_trend(test_category, days)
            elif metric == 'flakiness':
                result = self.analyze_flakiness_trend(test_category, days)
            else:
                continue
            
            chart_data = {
                "title": f"{test_category.value} - {metric}",
                "type": "line",
                "x_axis": {
                    "label": "时间",
                    "data": [p.timestamp.strftime('%Y-%m-%d') for p in result.data_points]
                },
                "y_axis": {
                    "label": metric,
                    "data": [p.value for p in result.data_points]
                },
                "statistics": {
                    "average": round(result.average, 2),
                    "minimum": round(result.minimum, 2),
                    "maximum": round(result.maximum, 2),
                    "trend_direction": result.trend_direction,
                    "change_rate": round(result.change_rate, 2)
                },
                "predictions": [
                    {
                        "date": p.timestamp.strftime('%Y-%m-%d'),
                        "value": round(p.value, 2)
                    }
                    for p in result.predictions
                ],
                "anomalies": result.anomalies
            }
            
            visualization["charts"][metric] = chart_data
        
        return visualization
    
    def generate_dashboard_data(
        self,
        days: int = 30
    ) -> dict[str, Any]:
        """
        生成仪表板数据
        
        生成所有测试分类的综合仪表板数据
        
        Args:
            days: 分析天数
            
        Returns:
            仪表板数据
        """
        dashboard = {
            "title": "测试报告趋势仪表板",
            "generated_at": datetime.now().isoformat(),
            "period_days": days,
            "categories": {},
            "summary": {
                "total_categories": len(TestCategory),
                "categories_with_data": 0,
                "overall_health": "unknown"
            }
        }
        
        health_scores = []
        
        for category in TestCategory:
            reports = self.storage.list_reports(test_category=category, days=days)
            
            if not reports:
                continue
            
            dashboard["summary"]["categories_with_data"] += 1
            
            pass_rate_result = self.analyze_pass_rate_trend(category, days)
            
            avg_pass_rate = pass_rate_result.average
            health_score = avg_pass_rate
            health_scores.append(health_score)
            
            category_data = {
                "name": category.value,
                "report_count": len(reports),
                "latest_version": reports[0].version if reports else None,
                "avg_pass_rate": round(avg_pass_rate, 2),
                "trend_direction": pass_rate_result.trend_direction,
                "change_rate": round(pass_rate_result.change_rate, 2),
                "health_score": round(health_score, 2),
                "health_status": self._get_health_status(health_score),
                "anomaly_count": len(pass_rate_result.anomalies),
                "quick_stats": {
                    "total_tests": sum(r.metrics.get('total_tests', 0) for r in reports),
                    "total_passed": sum(r.metrics.get('passed', 0) for r in reports),
                    "total_failed": sum(r.metrics.get('failed', 0) for r in reports)
                }
            }
            
            dashboard["categories"][category.value] = category_data
        
        if health_scores:
            avg_health = sum(health_scores) / len(health_scores)
            dashboard["summary"]["overall_health"] = self._get_health_status(avg_health)
            dashboard["summary"]["average_health_score"] = round(avg_health, 2)
        
        return dashboard
    
    def _get_health_status(self, score: float) -> str:
        """
        获取健康状态描述
        
        Args:
            score: 健康分数 (0-100)
            
        Returns:
            健康状态描述
        """
        if score >= 90:
            return "excellent"
        elif score >= 80:
            return "good"
        elif score >= 70:
            return "fair"
        elif score >= 60:
            return "poor"
        else:
            return "critical"
    
    def analyze_regression_risk(
        self,
        test_category: TestCategory,
        days: int = 30
    ) -> dict[str, Any]:
        """
        分析回归风险
        
        通过趋势分析识别潜在的回归风险
        
        Args:
            test_category: 测试分类
            days: 分析天数
            
        Returns:
            回归风险分析结果
        """
        risk_analysis = {
            "category": test_category.value,
            "analysis_period_days": days,
            "risk_level": "low",
            "risk_score": 0,
            "risk_factors": [],
            "recommendations": []
        }
        
        pass_rate_result = self.analyze_pass_rate_trend(test_category, days)
        failure_rate_result = self.analyze_failure_rate_trend(test_category, days)
        flakiness_result = self.analyze_flakiness_trend(test_category, days)
        
        risk_score = 0
        
        if pass_rate_result.trend_direction == "decreasing":
            risk_score += 30
            risk_analysis["risk_factors"].append({
                "factor": "pass_rate_declining",
                "severity": "high",
                "description": f"通过率呈下降趋势，变化率: {pass_rate_result.change_rate:.2f}%"
            })
        
        if len(pass_rate_result.anomalies) > 0:
            risk_score += len(pass_rate_result.anomalies) * 5
            risk_analysis["risk_factors"].append({
                "factor": "pass_rate_anomalies",
                "severity": "medium",
                "description": f"发现 {len(pass_rate_result.anomalies)} 个通过率异常点"
            })
        
        if failure_rate_result.trend_direction == "increasing":
            risk_score += 25
            risk_analysis["risk_factors"].append({
                "factor": "failure_rate_increasing",
                "severity": "high",
                "description": f"失败率呈上升趋势，变化率: {failure_rate_result.change_rate:.2f}%"
            })
        
        if flakiness_result.average > 10:
            risk_score += 20
            risk_analysis["risk_factors"].append({
                "factor": "high_flakiness",
                "severity": "medium",
                "description": f"测试不稳定性较高，平均波动: {flakiness_result.average:.2f}%"
            })
        
        if pass_rate_result.average < 80:
            risk_score += 15
            risk_analysis["risk_factors"].append({
                "factor": "low_pass_rate",
                "severity": "medium",
                "description": f"平均通过率较低: {pass_rate_result.average:.2f}%"
            })
        
        risk_analysis["risk_score"] = min(risk_score, 100)
        
        if risk_score >= 70:
            risk_analysis["risk_level"] = "critical"
        elif risk_score >= 50:
            risk_analysis["risk_level"] = "high"
        elif risk_score >= 30:
            risk_analysis["risk_level"] = "medium"
        else:
            risk_analysis["risk_level"] = "low"
        
        risk_analysis["recommendations"] = self._generate_risk_recommendations(
            risk_analysis["risk_factors"]
        )
        
        return risk_analysis
    
    def _generate_risk_recommendations(
        self,
        risk_factors: list[dict[str, Any]]
    ) -> list[str]:
        """
        根据风险因素生成建议
        
        Args:
            risk_factors: 风险因素列表
            
        Returns:
            建议列表
        """
        recommendations = []
        
        for factor in risk_factors:
            if factor["factor"] == "pass_rate_declining":
                recommendations.append("建议检查最近的代码变更，识别导致测试失败的原因")
                recommendations.append("考虑增加测试覆盖率以捕获更多潜在问题")
            
            elif factor["factor"] == "failure_rate_increasing":
                recommendations.append("建议分析失败的测试用例，查找共同模式")
                recommendations.append("考虑对失败率高的模块进行重构")
            
            elif factor["factor"] == "high_flakiness":
                recommendations.append("建议识别和修复不稳定的测试用例")
                recommendations.append("考虑增加测试等待时间或改进异步测试处理")
            
            elif factor["factor"] == "low_pass_rate":
                recommendations.append("建议优先修复失败的测试用例")
                recommendations.append("考虑对测试套件进行健康检查")
            
            elif factor["factor"] == "pass_rate_anomalies":
                recommendations.append("建议调查异常点对应的时间段，查找环境或配置问题")
        
        return list(set(recommendations))
    
    def export_trend_report(
        self,
        test_category: TestCategory,
        output_format: str = "json",
        days: int = 30
    ) -> dict[str, Any]:
        """
        导出趋势分析报告
        
        Args:
            test_category: 测试分类
            output_format: 输出格式
            days: 分析天数
            
        Returns:
            完整的趋势分析报告
        """
        report = {
            "report_type": "trend_analysis",
            "category": test_category.value,
            "generated_at": datetime.now().isoformat(),
            "analysis_period": {
                "days": days,
                "start": (datetime.now() - timedelta(days=days)).isoformat(),
                "end": datetime.now().isoformat()
            },
            "analyses": {},
            "visualization_data": self.generate_visualization_data(test_category, days=days),
            "risk_analysis": self.analyze_regression_risk(test_category, days),
            "comparison_summary": self.get_comparison_summary(test_category, days)
        }
        
        analyses = {
            "pass_rate": self.analyze_pass_rate_trend(test_category, days),
            "test_count": self.analyze_test_count_trend(test_category, days),
            "duration": self.analyze_duration_trend(test_category, days),
            "failure_rate": self.analyze_failure_rate_trend(test_category, days),
            "flakiness": self.analyze_flakiness_trend(test_category, days)
        }
        
        for name, result in analyses.items():
            report["analyses"][name] = result.to_dict()
        
        return report


class ReportComparator:
    """报告对比分析器"""

    def __init__(self, storage: ReportStorage):
        self.storage = storage

    def compare_versions(self, version1: str, version2: str) -> dict[str, Any]:
        reports1 = self.storage.list_reports(version=version1)
        reports2 = self.storage.list_reports(version=version2)

        comparison = {
            "version1": version1,
            "version2": version2,
            "reports_v1": len(reports1),
            "reports_v2": len(reports2),
            "by_type_comparison": {},
            "by_category_comparison": {},
            "size_comparison": {
                "v1_total": sum(r.file_size for r in reports1),
                "v2_total": sum(r.file_size for r in reports2)
            },
            "metrics_comparison": {},
            "changes": []
        }

        types1 = {}
        types2 = {}
        categories1 = {}
        categories2 = {}

        for r in reports1:
            types1[r.report_type.value] = types1.get(r.report_type.value, 0) + 1
            if r.test_category:
                cat = r.test_category.value
                categories1[cat] = categories1.get(cat, 0) + 1
        for r in reports2:
            types2[r.report_type.value] = types2.get(r.report_type.value, 0) + 1
            if r.test_category:
                cat = r.test_category.value
                categories2[cat] = categories2.get(cat, 0) + 1

        all_types = set(types1.keys()) | set(types2.keys())
        for t in all_types:
            comparison["by_type_comparison"][t] = {
                "v1": types1.get(t, 0),
                "v2": types2.get(t, 0),
                "diff": types2.get(t, 0) - types1.get(t, 0)
            }

        all_categories = set(categories1.keys()) | set(categories2.keys())
        for c in all_categories:
            comparison["by_category_comparison"][c] = {
                "v1": categories1.get(c, 0),
                "v2": categories2.get(c, 0),
                "diff": categories2.get(c, 0) - categories1.get(c, 0)
            }

        comparison["metrics_comparison"] = self._compare_version_metrics(reports1, reports2)

        return comparison

    def compare_reports(self, report_id1: str, report_id2: str) -> dict[str, Any]:
        report1 = self.storage.get_report(report_id1)
        report2 = self.storage.get_report(report_id2)

        if not report1 or not report2:
            return {"error": "报告不存在"}

        comparison = {
            "report1": {
                "id": report1.report_id,
                "type": report1.report_type.value,
                "version": report1.version,
                "created_at": report1.created_at.isoformat(),
                "summary": report1.summary,
                "test_category": report1.test_category.value if report1.test_category else None,
                "metrics": report1.metrics
            },
            "report2": {
                "id": report2.report_id,
                "type": report2.report_type.value,
                "version": report2.version,
                "created_at": report2.created_at.isoformat(),
                "summary": report2.summary,
                "test_category": report2.test_category.value if report2.test_category else None,
                "metrics": report2.metrics
            },
            "summary_diff": self._compare_summaries(report1.summary, report2.summary),
            "metrics_diff": self._compare_metrics(report1.metrics, report2.metrics)
        }

        return comparison

    def compare_categories(
        self,
        category: TestCategory,
        version1: str,
        version2: str
    ) -> dict[str, Any]:
        reports1 = self.storage.list_reports(version=version1, test_category=category)
        reports2 = self.storage.list_reports(version=version2, test_category=category)

        comparison = {
            "category": category.value,
            "version1": version1,
            "version2": version2,
            "reports_v1": len(reports1),
            "reports_v2": len(reports2),
            "metrics_comparison": {}
        }

        metrics1 = self._aggregate_metrics(reports1)
        metrics2 = self._aggregate_metrics(reports2)

        comparison["metrics_comparison"] = self._compare_metrics(metrics1, metrics2)

        return comparison

    def compare_time_periods(
        self,
        test_category: TestCategory,
        period1_start: datetime,
        period1_end: datetime,
        period2_start: datetime,
        period2_end: datetime
    ) -> dict[str, Any]:
        reports1 = [
            r for r in self.storage.list_reports(test_category=test_category)
            if period1_start <= r.created_at <= period1_end
        ]
        reports2 = [
            r for r in self.storage.list_reports(test_category=test_category)
            if period2_start <= r.created_at <= period2_end
        ]

        comparison = {
            "category": test_category.value,
            "period1": {
                "start": period1_start.isoformat(),
                "end": period1_end.isoformat(),
                "report_count": len(reports1)
            },
            "period2": {
                "start": period2_start.isoformat(),
                "end": period2_end.isoformat(),
                "report_count": len(reports2)
            },
            "metrics_comparison": {}
        }

        metrics1 = self._aggregate_metrics(reports1)
        metrics2 = self._aggregate_metrics(reports2)

        comparison["metrics_comparison"] = self._compare_metrics(metrics1, metrics2)

        return comparison

    def generate_comparison_report(
        self,
        version1: str,
        version2: str,
        output_format: str = "json"
    ) -> dict[str, Any]:
        version_comparison = self.compare_versions(version1, version2)

        report = {
            "comparison_type": "version",
            "generated_at": datetime.now().isoformat(),
            "versions": {
                "version1": version1,
                "version2": version2
            },
            "summary": {
                "total_reports_change": version_comparison["reports_v2"] - version_comparison["reports_v1"],
                "total_size_change": version_comparison["size_comparison"]["v2_total"] - version_comparison["size_comparison"]["v1_total"]
            },
            "details": version_comparison,
            "recommendations": self._generate_recommendations(version_comparison)
        }

        return report

    def _compare_summaries(self, summary1: dict, summary2: dict) -> dict[str, Any]:
        diff = {}

        all_keys = set(summary1.keys()) | set(summary2.keys())

        for key in all_keys:
            val1 = summary1.get(key)
            val2 = summary2.get(key)

            if isinstance(val1, (int, float)) and isinstance(val2, (int, float)):
                diff[key] = {
                    "v1": val1,
                    "v2": val2,
                    "change": val2 - val1,
                    "change_percent": ((val2 - val1) / val1 * 100) if val1 != 0 else 0
                }
            elif val1 != val2:
                diff[key] = {
                    "v1": val1,
                    "v2": val2,
                    "changed": True
                }

        return diff

    def _compare_metrics(self, metrics1: dict, metrics2: dict) -> dict[str, Any]:
        diff = {}

        all_keys = set(metrics1.keys()) | set(metrics2.keys())

        for key in all_keys:
            val1 = metrics1.get(key)
            val2 = metrics2.get(key)

            if val1 is None and val2 is None:
                continue

            if isinstance(val1, (int, float)) and isinstance(val2, (int, float)):
                change = val2 - val1
                change_pct = ((val2 - val1) / val1 * 100) if val1 != 0 else 0

                status = "unchanged"
                if abs(change_pct) > 10:
                    status = "significant_change"
                elif abs(change_pct) > 5:
                    status = "minor_change"

                diff[key] = {
                    "v1": val1,
                    "v2": val2,
                    "change": round(change, 4),
                    "change_percent": round(change_pct, 2),
                    "status": status
                }
            elif isinstance(val1, list) and isinstance(val2, list):
                diff[key] = {
                    "v1": val1,
                    "v2": val2,
                    "added": [x for x in val2 if x not in val1],
                    "removed": [x for x in val1 if x not in val2]
                }
            elif val1 != val2:
                diff[key] = {
                    "v1": val1,
                    "v2": val2,
                    "changed": True
                }

        return diff

    def _compare_version_metrics(
        self,
        reports1: list[ReportMetadata],
        reports2: list[ReportMetadata]
    ) -> dict[str, Any]:
        metrics1 = self._aggregate_metrics(reports1)
        metrics2 = self._aggregate_metrics(reports2)

        return self._compare_metrics(metrics1, metrics2)

    def _aggregate_metrics(self, reports: list[ReportMetadata]) -> dict[str, Any]:
        aggregated = {
            "total_reports": len(reports),
            "total_file_size": sum(r.file_size for r in reports),
            "avg_pass_rate": 0,
            "total_tests": 0,
            "total_passed": 0,
            "total_failed": 0
        }

        pass_rates = []
        for report in reports:
            metrics = report.metrics
            if 'pass_rate' in metrics:
                pass_rates.append(metrics['pass_rate'])
            if 'total_tests' in metrics:
                aggregated["total_tests"] += metrics['total_tests']
            if 'passed' in metrics:
                aggregated["total_passed"] += metrics['passed']
            if 'failed' in metrics:
                aggregated["total_failed"] += metrics['failed']

        if pass_rates:
            aggregated["avg_pass_rate"] = sum(pass_rates) / len(pass_rates)

        return aggregated

    def _generate_recommendations(self, comparison: dict) -> list[str]:
        recommendations = []

        reports_change = comparison["reports_v2"] - comparison["reports_v1"]
        if reports_change < 0:
            recommendations.append(f"报告数量减少了 {abs(reports_change)} 个，建议检查是否有遗漏的测试报告")

        for type_name, data in comparison.get("by_type_comparison", {}).items():
            if data["diff"] < 0:
                recommendations.append(f"{type_name} 类型报告减少，建议确认是否需要补充")

        for category, data in comparison.get("by_category_comparison", {}).items():
            if data["diff"] < 0:
                recommendations.append(f"{category} 测试类别报告减少，建议检查测试覆盖率")

        metrics = comparison.get("metrics_comparison", {})
        if "avg_pass_rate" in metrics:
            rate_change = metrics["avg_pass_rate"].get("change_percent", 0)
            if rate_change < -5:
                recommendations.append(f"平均通过率下降 {abs(rate_change):.2f}%，建议关注测试稳定性")

        return recommendations


class ReportVersionManagerTest:
    """报告版本管理器测试用例"""

    def __init__(self, test_dir: Path = None):
        self.test_dir = test_dir or Path("test_reports_temp")
        self.storage: Optional[ReportStorage] = None
        self.test_results: list[dict[str, Any]] = []

    def setup(self) -> bool:
        try:
            self.test_dir.mkdir(parents=True, exist_ok=True)
            self.storage = ReportStorage(base_dir=self.test_dir)
            logger.info("测试环境初始化完成")
            return True
        except Exception as e:
            logger.error(f"测试环境初始化失败: {e}")
            return False

    def teardown(self):
        try:
            if self.test_dir.exists():
                shutil.rmtree(self.test_dir)
            logger.info("测试环境清理完成")
        except Exception as e:
            logger.error(f"测试环境清理失败: {e}")

    def run_all_tests(self) -> dict[str, Any]:
        self.test_results = []

        test_methods = [
            self.test_category_directory_creation,
            self.test_store_report_with_category,
            self.test_list_reports_by_category,
            self.test_extract_metrics,
            self.test_trend_analysis,
            self.test_version_comparison,
            self.test_category_comparison,
            self.test_time_period_comparison,
            self.test_generate_comparison_report,
            self.test_semantic_version_parsing,
            self.test_semantic_version_comparison,
            self.test_version_manager_create_version,
            self.test_version_manager_dependencies,
            self.test_batch_store_reports,
            self.test_category_index_management,
            self.test_storage_summary,
            self.test_duration_trend_analysis,
            self.test_failure_rate_trend_analysis,
            self.test_flakiness_trend_analysis,
            self.test_visualization_data_generation,
            self.test_dashboard_data_generation,
            self.test_regression_risk_analysis,
            self.test_export_trend_report,
        ]

        passed = 0
        failed = 0

        for test_method in test_methods:
            try:
                test_method()
                self.test_results.append({
                    "test": test_method.__name__,
                    "status": "passed"
                })
                passed += 1
            except AssertionError as e:
                self.test_results.append({
                    "test": test_method.__name__,
                    "status": "failed",
                    "error": str(e)
                })
                failed += 1
            except Exception as e:
                self.test_results.append({
                    "test": test_method.__name__,
                    "status": "error",
                    "error": str(e)
                })
                failed += 1

        return {
            "total": len(test_methods),
            "passed": passed,
            "failed": failed,
            "results": self.test_results
        }

    def test_category_directory_creation(self):
        assert self.storage is not None

        for category in TestCategory:
            category_dir = self.storage._get_category_dir(category)
            assert category_dir.exists(), f"分类目录不存在: {category_dir}"
            expected_name = TestCategory.get_default_dir(category)
            assert expected_name in str(category_dir), f"分类目录名称不正确: {category_dir}"

    def test_store_report_with_category(self):
        assert self.storage is not None

        test_report = self.test_dir / "test_report.json"
        test_data = {
            "summary": {
                "total": 100,
                "passed": 95,
                "failed": 5,
                "skipped": 0
            }
        }
        with open(test_report, 'w', encoding='utf-8') as f:
            json.dump(test_data, f)

        metadata = self.storage.store_report(
            report_file=test_report,
            version="v1.0.0",
            report_type=ReportType.TEST,
            description="单元测试报告",
            tags=["unit", "smoke"],
            test_category=TestCategory.UNIT
        )

        assert metadata is not None
        assert metadata.test_category == TestCategory.UNIT
        assert metadata.version == "v1.0.0"
        assert "pass_rate" in metadata.metrics
        assert metadata.metrics["pass_rate"] == 95.0

    def test_list_reports_by_category(self):
        assert self.storage is not None

        reports = self.storage.list_reports(test_category=TestCategory.UNIT)
        assert isinstance(reports, list)

        stats = self.storage.get_category_statistics()
        assert isinstance(stats, dict)
        assert TestCategory.UNIT.value in stats

    def test_extract_metrics(self):
        assert self.storage is not None

        test_report = self.test_dir / "perf_report.json"
        test_data = {
            "summary": {
                "avg_response_time": 150.5,
                "max_response_time": 500.0,
                "min_response_time": 50.0,
                "throughput": 1000,
                "error_rate": 0.5,
                "p95": 300.0,
                "p99": 450.0
            }
        }
        with open(test_report, 'w', encoding='utf-8') as f:
            json.dump(test_data, f)

        metadata = self.storage.store_report(
            report_file=test_report,
            version="v1.0.0",
            report_type=ReportType.PERFORMANCE,
            test_category=TestCategory.PERFORMANCE
        )

        assert metadata.metrics.get("avg_response_time") == 150.5
        assert metadata.metrics.get("throughput") == 1000
        assert metadata.metrics.get("p95_latency") == 300.0

    def test_trend_analysis(self):
        assert self.storage is not None

        for i in range(5):
            test_report = self.test_dir / f"trend_report_{i}.json"
            test_data = {
                "summary": {
                    "total": 100 + i * 10,
                    "passed": 90 + i * 5,
                    "failed": 10 - i,
                    "skipped": 0
                }
            }
            with open(test_report, 'w', encoding='utf-8') as f:
                json.dump(test_data, f)

            self.storage.store_report(
                report_file=test_report,
                version=f"v1.{i}.0",
                report_type=ReportType.TEST,
                test_category=TestCategory.UNIT
            )

        analyzer = ReportTrendAnalyzer(self.storage)
        result = analyzer.analyze_pass_rate_trend(TestCategory.UNIT, days=30)

        assert result is not None
        assert len(result.data_points) > 0
        assert result.trend_direction in ["increasing", "decreasing", "stable"]

    def test_version_comparison(self):
        assert self.storage is not None

        for version in ["v1.0.0", "v2.0.0"]:
            for i in range(3):
                test_report = self.test_dir / f"compare_{version}_{i}.json"
                test_data = {"summary": {"total": 100, "passed": 90, "failed": 10}}
                with open(test_report, 'w', encoding='utf-8') as f:
                    json.dump(test_data, f)

                self.storage.store_report(
                    report_file=test_report,
                    version=version,
                    report_type=ReportType.TEST,
                    test_category=TestCategory.UNIT
                )

        comparator = ReportComparator(self.storage)
        result = comparator.compare_versions("v1.0.0", "v2.0.0")

        assert result is not None
        assert "version1" in result
        assert "version2" in result
        assert "by_type_comparison" in result
        assert "by_category_comparison" in result

    def test_category_comparison(self):
        assert self.storage is not None

        for version in ["v1.0.0", "v2.0.0"]:
            test_report = self.test_dir / f"cat_compare_{version}.json"
            test_data = {"summary": {"total": 50, "passed": 45, "failed": 5}}
            with open(test_report, 'w', encoding='utf-8') as f:
                json.dump(test_data, f)

            self.storage.store_report(
                report_file=test_report,
                version=version,
                report_type=ReportType.TEST,
                test_category=TestCategory.INTEGRATION
            )

        comparator = ReportComparator(self.storage)
        result = comparator.compare_categories(TestCategory.INTEGRATION, "v1.0.0", "v2.0.0")

        assert result is not None
        assert result["category"] == "integration"
        assert "metrics_comparison" in result

    def test_time_period_comparison(self):
        assert self.storage is not None

        now = datetime.now()
        period1_start = now - timedelta(days=14)
        period1_end = now - timedelta(days=7)
        period2_start = now - timedelta(days=7)
        period2_end = now

        comparator = ReportComparator(self.storage)
        result = comparator.compare_time_periods(
            test_category=TestCategory.UNIT,
            period1_start=period1_start,
            period1_end=period1_end,
            period2_start=period2_start,
            period2_end=period2_end
        )

        assert result is not None
        assert "period1" in result
        assert "period2" in result
        assert "metrics_comparison" in result

    def test_generate_comparison_report(self):
        assert self.storage is not None

        comparator = ReportComparator(self.storage)
        result = comparator.generate_comparison_report("v1.0.0", "v2.0.0")

        assert result is not None
        assert "comparison_type" in result
        assert "generated_at" in result
        assert "summary" in result
        assert "recommendations" in result
    
    def test_semantic_version_parsing(self):
        """测试语义化版本号解析"""
        v1 = SemanticVersion.parse("v1.2.3")
        assert v1.major == 1
        assert v1.minor == 2
        assert v1.patch == 3
        assert not v1.is_prerelease()
        
        v2 = SemanticVersion.parse("2.0.0-alpha.1")
        assert v2.major == 2
        assert v2.minor == 0
        assert v2.patch == 0
        assert v2.prerelease == "alpha.1"
        assert v2.is_prerelease()
        
        v3 = SemanticVersion.parse("1.0.0+build.123")
        assert v3.build == "build.123"
        
        v4 = SemanticVersion.parse("1.0.0-beta.2+build.456")
        assert v4.prerelease == "beta.2"
        assert v4.build == "build.456"
    
    def test_semantic_version_comparison(self):
        """测试语义化版本号比较"""
        v1 = SemanticVersion.parse("1.0.0")
        v2 = SemanticVersion.parse("1.0.1")
        v3 = SemanticVersion.parse("1.1.0")
        v4 = SemanticVersion.parse("2.0.0")
        
        assert v1 < v2
        assert v2 < v3
        assert v3 < v4
        assert v1 < v4
        
        v_pre1 = SemanticVersion.parse("1.0.0-alpha")
        v_pre2 = SemanticVersion.parse("1.0.0-beta")
        v_stable = SemanticVersion.parse("1.0.0")
        
        assert v_pre1 < v_pre2
        assert v_pre2 < v_stable
        
        v_bumped = v1.bump_minor()
        assert v_bumped.major == 1
        assert v_bumped.minor == 1
        assert v_bumped.patch == 0
    
    def test_version_manager_create_version(self):
        """测试版本管理器创建版本"""
        assert self.storage is not None
        
        version_manager = VersionManager(self.storage)
        
        new_version = version_manager.create_version("v1.0.0", "patch")
        assert new_version == "1.0.1"
        
        new_version = version_manager.create_version("v1.0.0", "minor")
        assert new_version == "1.1.0"
        
        new_version = version_manager.create_version("v1.0.0", "major")
        assert new_version == "2.0.0"
        
        next_version = version_manager.get_next_version("v1.0.0")
        assert next_version == "1.0.1"
    
    def test_version_manager_dependencies(self):
        """测试版本依赖关系管理"""
        assert self.storage is not None
        
        version_manager = VersionManager(self.storage)
        
        version_manager.set_dependency(
            version="v2.0.0",
            depends_on=["v1.0.0"],
            conflicts=["v0.9.0"],
            replaces="v1.5.0"
        )
        
        dep = version_manager.get_dependencies("v2.0.0")
        assert dep is not None
        assert "v1.0.0" in dep.depends_on
        assert "v0.9.0" in dep.conflicts
        assert dep.replaces == "v1.5.0"
        
        compatibility = version_manager.check_compatibility("v2.0.0", "v0.9.0")
        assert not compatibility["compatible"]
        assert len(compatibility["errors"]) > 0
        
        lineage = version_manager.get_version_lineage("v2.0.0")
        assert lineage["replaces"] == "v1.5.0"
    
    def test_batch_store_reports(self):
        """测试批量存储报告"""
        assert self.storage is not None
        
        reports_to_store = []
        for i in range(3):
            test_report = self.test_dir / f"batch_report_{i}.json"
            test_data = {
                "summary": {
                    "total": 100 + i * 10,
                    "passed": 95 + i * 2,
                    "failed": 5 - i * 2,
                    "skipped": 0
                }
            }
            with open(test_report, 'w', encoding='utf-8') as f:
                json.dump(test_data, f)
            
            reports_to_store.append({
                "report_file": str(test_report),
                "report_type": ReportType.TEST,
                "description": f"批量测试报告 {i}",
                "tags": ["batch", "test"],
                "test_category": TestCategory.UNIT
            })
        
        stored = self.storage.store_batch_reports(reports_to_store, "v3.0.0")
        assert len(stored) == 3
        
        for metadata in stored:
            assert metadata.version == "v3.0.0"
            assert metadata.test_category == TestCategory.UNIT
    
    def test_category_index_management(self):
        """测试分类索引管理"""
        assert self.storage is not None
        
        test_report = self.test_dir / "index_test_report.json"
        test_data = {"summary": {"total": 50, "passed": 45, "failed": 5}}
        with open(test_report, 'w', encoding='utf-8') as f:
            json.dump(test_data, f)
        
        self.storage.store_report(
            report_file=test_report,
            version="v4.0.0",
            report_type=ReportType.TEST,
            test_category=TestCategory.DATABASE
        )
        
        self.storage._update_category_index("v4.0.0")
        
        index = self.storage.get_category_index(TestCategory.DATABASE, "v4.0.0")
        assert index is not None
        assert index["category"] == "database"
        assert index["version"] == "v4.0.0"
        assert index["report_count"] >= 1
    
    def test_storage_summary(self):
        """测试存储摘要"""
        assert self.storage is not None
        
        summary = self.storage.get_storage_summary()
        
        assert "total_reports" in summary
        assert "total_size_bytes" in summary
        assert "by_category" in summary
        assert "by_type" in summary
        assert "by_status" in summary
        assert "by_version" in summary
        
        assert isinstance(summary["total_reports"], int)
        assert summary["total_reports"] >= 0
    
    def test_duration_trend_analysis(self):
        """测试执行时间趋势分析"""
        assert self.storage is not None
        
        for i in range(3):
            test_report = self.test_dir / f"duration_report_{i}.json"
            test_data = {
                "summary": {
                    "total": 100,
                    "passed": 90,
                    "failed": 10,
                    "duration": 100.0 + i * 20
                }
            }
            with open(test_report, 'w', encoding='utf-8') as f:
                json.dump(test_data, f)
            
            self.storage.store_report(
                report_file=test_report,
                version=f"v5.{i}.0",
                report_type=ReportType.TEST,
                test_category=TestCategory.UNIT
            )
        
        analyzer = ReportTrendAnalyzer(self.storage)
        result = analyzer.analyze_duration_trend(TestCategory.UNIT, days=30)
        
        assert result is not None
        assert len(result.data_points) > 0
        assert result.metric_name == "unit_duration"
    
    def test_failure_rate_trend_analysis(self):
        """测试失败率趋势分析"""
        assert self.storage is not None
        
        analyzer = ReportTrendAnalyzer(self.storage)
        result = analyzer.analyze_failure_rate_trend(TestCategory.UNIT, days=30)
        
        assert result is not None
        assert result.metric_name == "unit_failure_rate"
    
    def test_flakiness_trend_analysis(self):
        """测试不稳定性趋势分析"""
        assert self.storage is not None
        
        analyzer = ReportTrendAnalyzer(self.storage)
        result = analyzer.analyze_flakiness_trend(TestCategory.UNIT, days=30)
        
        assert result is not None
        assert result.metric_name == "unit_flakiness"
    
    def test_visualization_data_generation(self):
        """测试可视化数据生成"""
        assert self.storage is not None
        
        analyzer = ReportTrendAnalyzer(self.storage)
        viz_data = analyzer.generate_visualization_data(
            TestCategory.UNIT,
            metrics=['pass_rate', 'test_count'],
            days=30
        )
        
        assert viz_data is not None
        assert "category" in viz_data
        assert "charts" in viz_data
        assert "pass_rate" in viz_data["charts"]
        assert "test_count" in viz_data["charts"]
        
        pass_rate_chart = viz_data["charts"]["pass_rate"]
        assert "title" in pass_rate_chart
        assert "x_axis" in pass_rate_chart
        assert "y_axis" in pass_rate_chart
        assert "statistics" in pass_rate_chart
    
    def test_dashboard_data_generation(self):
        """测试仪表板数据生成"""
        assert self.storage is not None
        
        analyzer = ReportTrendAnalyzer(self.storage)
        dashboard = analyzer.generate_dashboard_data(days=30)
        
        assert dashboard is not None
        assert "title" in dashboard
        assert "generated_at" in dashboard
        assert "categories" in dashboard
        assert "summary" in dashboard
        
        assert "total_categories" in dashboard["summary"]
        assert "categories_with_data" in dashboard["summary"]
    
    def test_regression_risk_analysis(self):
        """测试回归风险分析"""
        assert self.storage is not None
        
        analyzer = ReportTrendAnalyzer(self.storage)
        risk = analyzer.analyze_regression_risk(TestCategory.UNIT, days=30)
        
        assert risk is not None
        assert "category" in risk
        assert "risk_level" in risk
        assert "risk_score" in risk
        assert "risk_factors" in risk
        assert "recommendations" in risk
        
        assert risk["risk_level"] in ["low", "medium", "high", "critical"]
        assert isinstance(risk["risk_score"], (int, float))
        assert 0 <= risk["risk_score"] <= 100
    
    def test_export_trend_report(self):
        """测试导出趋势分析报告"""
        assert self.storage is not None
        
        analyzer = ReportTrendAnalyzer(self.storage)
        report = analyzer.export_trend_report(TestCategory.UNIT, days=30)
        
        assert report is not None
        assert report["report_type"] == "trend_analysis"
        assert "category" in report
        assert "generated_at" in report
        assert "analyses" in report
        assert "visualization_data" in report
        assert "risk_analysis" in report
        assert "comparison_summary" in report
        
        assert "pass_rate" in report["analyses"]
        assert "test_count" in report["analyses"]
        assert "duration" in report["analyses"]

    def test_merge_reports(self):
        """测试报告合并功能"""
        assert self.storage is not None
        
        for i in range(3):
            test_report = self.test_dir / f"merge_report_{i}.json"
            test_data = {
                "summary": {
                    "total": 100 + i * 10,
                    "passed": 90 + i * 5,
                    "failed": 10 - i * 3,
                    "skipped": 0
                }
            }
            with open(test_report, 'w', encoding='utf-8') as f:
                json.dump(test_data, f)
            
            self.storage.store_report(
                report_file=test_report,
                version=f"v1.{i}.0",
                report_type=ReportType.TEST,
                test_category=TestCategory.UNIT
            )
        
        reports = self.storage.list_reports(test_category=TestCategory.UNIT)
        report_ids = [r.report_id for r in reports[:3]]
        
        merged = self.storage.merge_reports(
            report_ids=report_ids,
            name="合并测试报告",
            test_category=TestCategory.UNIT
        )
        
        assert merged is not None
        assert merged.name == "合并测试报告"
        assert len(merged.source_reports) == 3
        assert "total_tests" in merged.merged_metrics
        assert "total_passed" in merged.merged_metrics

    def test_get_merged_report(self):
        """测试获取合并报告"""
        assert self.storage is not None
        
        for i in range(2):
            test_report = self.test_dir / f"get_merge_{i}.json"
            test_data = {"summary": {"total": 50, "passed": 45, "failed": 5}}
            with open(test_report, 'w', encoding='utf-8') as f:
                json.dump(test_data, f)
            
            self.storage.store_report(
                report_file=test_report,
                version="v2.0.0",
                report_type=ReportType.TEST,
                test_category=TestCategory.INTEGRATION
            )
        
        reports = self.storage.list_reports(test_category=TestCategory.INTEGRATION)
        merged = self.storage.merge_reports(
            report_ids=[r.report_id for r in reports],
            name="集成测试合并报告"
        )
        
        assert merged is not None
        
        retrieved = self.storage.get_merged_report(merged.merged_id)
        assert retrieved is not None
        assert retrieved.merged_id == merged.merged_id

    def test_list_merged_reports(self):
        """测试列出合并报告"""
        assert self.storage is not None
        
        merged_reports = self.storage.list_merged_reports()
        assert isinstance(merged_reports, list)

    def test_merge_reports_by_category(self):
        """测试按分类合并报告"""
        assert self.storage is not None
        
        for i in range(3):
            test_report = self.test_dir / f"category_merge_{i}.json"
            test_data = {"summary": {"total": 30, "passed": 28, "failed": 2}}
            with open(test_report, 'w', encoding='utf-8') as f:
                json.dump(test_data, f)
            
            self.storage.store_report(
                report_file=test_report,
                version="v3.0.0",
                report_type=ReportType.TEST,
                test_category=TestCategory.E2E
            )
        
        merged = self.storage.merge_reports_by_category(
            version="v3.0.0",
            test_category=TestCategory.E2E
        )
        
        assert merged is not None
        assert merged.test_category == TestCategory.E2E

    def test_export_report_json(self):
        """测试导出报告为JSON"""
        assert self.storage is not None
        
        test_report = self.test_dir / "export_json_report.json"
        test_data = {
            "summary": {"total": 100, "passed": 95, "failed": 5},
            "details": {"test_cases": []}
        }
        with open(test_report, 'w', encoding='utf-8') as f:
            json.dump(test_data, f)
        
        metadata = self.storage.store_report(
            report_file=test_report,
            version="v4.0.0",
            report_type=ReportType.TEST,
            test_category=TestCategory.UNIT
        )
        
        exporter = ReportExporter(self.storage)
        config = ExportConfig(
            format="json",
            include_summary=True,
            include_metrics=True,
            include_details=True
        )
        
        output_path = exporter.export_report(metadata.report_id, config)
        assert output_path is not None
        assert output_path.endswith(".json")
        
        with open(output_path, 'r', encoding='utf-8') as f:
            exported_data = json.load(f)
        
        assert "report_id" in exported_data
        assert "summary" in exported_data
        assert "metrics" in exported_data

    def test_export_report_html(self):
        """测试导出报告为HTML"""
        assert self.storage is not None
        
        test_report = self.test_dir / "export_html_report.json"
        test_data = {"summary": {"total": 50, "passed": 48, "failed": 2}}
        with open(test_report, 'w', encoding='utf-8') as f:
            json.dump(test_data, f)
        
        metadata = self.storage.store_report(
            report_file=test_report,
            version="v5.0.0",
            report_type=ReportType.TEST,
            test_category=TestCategory.UNIT
        )
        
        exporter = ReportExporter(self.storage)
        config = ExportConfig(format="html", include_summary=True)
        
        output_path = exporter.export_report(metadata.report_id, config)
        assert output_path is not None
        assert output_path.endswith(".html")
        
        with open(output_path, 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        assert "<!DOCTYPE html>" in html_content
        assert "测试报告" in html_content

    def test_export_merged_report(self):
        """测试导出合并报告"""
        assert self.storage is not None
        
        for i in range(2):
            test_report = self.test_dir / f"export_merged_{i}.json"
            test_data = {"summary": {"total": 40, "passed": 38, "failed": 2}}
            with open(test_report, 'w', encoding='utf-8') as f:
                json.dump(test_data, f)
            
            self.storage.store_report(
                report_file=test_report,
                version="v6.0.0",
                report_type=ReportType.TEST,
                test_category=TestCategory.DATABASE
            )
        
        reports = self.storage.list_reports(test_category=TestCategory.DATABASE)
        merged = self.storage.merge_reports(
            report_ids=[r.report_id for r in reports],
            name="数据库测试合并报告"
        )
        
        assert merged is not None
        
        exporter = ReportExporter(self.storage)
        config = ExportConfig(format="json", include_metrics=True)
        
        output_path = exporter.export_merged_report(merged.merged_id, config)
        assert output_path is not None

    def test_export_batch(self):
        """测试批量导出报告"""
        assert self.storage is not None
        
        report_ids = []
        for i in range(3):
            test_report = self.test_dir / f"batch_export_{i}.json"
            test_data = {"summary": {"total": 20, "passed": 18, "failed": 2}}
            with open(test_report, 'w', encoding='utf-8') as f:
                json.dump(test_data, f)
            
            metadata = self.storage.store_report(
                report_file=test_report,
                version="v7.0.0",
                report_type=ReportType.TEST,
                test_category=TestCategory.UNIT
            )
            report_ids.append(metadata.report_id)
        
        exporter = ReportExporter(self.storage)
        config = ExportConfig(format="json")
        
        results = exporter.export_batch(report_ids, config)
        assert len(results) == 3
        
        for report_id, output_path in results.items():
            assert report_id in report_ids
            assert Path(output_path).exists()

    def test_export_trend_report_html(self):
        """测试导出趋势报告为HTML"""
        assert self.storage is not None
        
        for i in range(3):
            test_report = self.test_dir / f"trend_export_{i}.json"
            test_data = {
                "summary": {
                    "total": 100,
                    "passed": 90 + i * 2,
                    "failed": 10 - i * 2,
                    "duration": 50.0 + i * 10
                }
            }
            with open(test_report, 'w', encoding='utf-8') as f:
                json.dump(test_data, f)
            
            self.storage.store_report(
                report_file=test_report,
                version=f"v8.{i}.0",
                report_type=ReportType.TEST,
                test_category=TestCategory.PERFORMANCE
            )
        
        exporter = ReportExporter(self.storage)
        config = ExportConfig(format="html")
        
        output_path = exporter.export_trend_report(
            TestCategory.PERFORMANCE,
            days=30,
            config=config
        )
        
        assert output_path is not None
        assert output_path.endswith(".html")


def main():
    parser = argparse.ArgumentParser(description="报告版本管理模块")
    subparsers = parser.add_subparsers(dest="command", help="可用命令")

    parser_store = subparsers.add_parser("store", help="存储报告")
    parser_store.add_argument("report_file", type=Path, help="报告文件路径")
    parser_store.add_argument("--version", required=True, help="版本号")
    parser_store.add_argument("--type", required=True, choices=[t.value for t in ReportType], help="报告类型")
    parser_store.add_argument("--description", default="", help="描述")
    parser_store.add_argument("--tags", nargs="+", help="标签")
    parser_store.add_argument("--category", choices=[c.value for c in TestCategory], help="测试项目分类")

    parser_list = subparsers.add_parser("list", help="列出报告")
    parser_list.add_argument("--version", help="版本号")
    parser_list.add_argument("--type", choices=[t.value for t in ReportType], help="报告类型")
    parser_list.add_argument("--days", type=int, help="最近天数")
    parser_list.add_argument("--category", choices=[c.value for c in TestCategory], help="测试项目分类")

    parser_query = subparsers.add_parser("query", help="查询报告")
    parser_query.add_argument("--version", help="版本号")
    parser_query.add_argument("--report-id", help="报告ID")
    parser_query.add_argument("--tags", nargs="+", help="标签")

    parser_compare = subparsers.add_parser("compare", help="对比报告")
    parser_compare.add_argument("version1", help="版本1")
    parser_compare.add_argument("version2", help="版本2")
    parser_compare.add_argument("--category", choices=[c.value for c in TestCategory], help="测试项目分类")

    parser_archive = subparsers.add_parser("archive", help="归档报告")
    parser_archive.add_argument("report_id", help="报告ID")

    parser_delete = subparsers.add_parser("delete", help="删除报告")
    parser_delete.add_argument("report_id", help="报告ID")

    parser_versions = subparsers.add_parser("versions", help="列出所有版本")

    parser_trend = subparsers.add_parser("trend", help="趋势分析")
    parser_trend.add_argument("--category", required=True, choices=[c.value for c in TestCategory], help="测试项目分类")
    parser_trend.add_argument("--days", type=int, default=30, help="分析天数")
    parser_trend.add_argument("--metric", default="pass_rate", help="分析指标")

    parser_stats = subparsers.add_parser("stats", help="分类统计")

    parser_test = subparsers.add_parser("test", help="运行测试用例")
    
    parser_version_mgmt = subparsers.add_parser("version", help="版本管理")
    parser_version_mgmt.add_argument("action", choices=["create", "next", "compare", "stats", "lineage"], help="版本操作")
    parser_version_mgmt.add_argument("--base", help="基础版本号")
    parser_version_mgmt.add_argument("--type", choices=["major", "minor", "patch"], default="patch", help="版本递增类型")
    parser_version_mgmt.add_argument("--version1", help="版本1（用于比较）")
    parser_version_mgmt.add_argument("--version2", help="版本2（用于比较）")
    
    parser_dashboard = subparsers.add_parser("dashboard", help="生成仪表板数据")
    parser_dashboard.add_argument("--days", type=int, default=30, help="分析天数")
    parser_dashboard.add_argument("--output", help="输出文件路径")
    
    parser_risk = subparsers.add_parser("risk", help="回归风险分析")
    parser_risk.add_argument("--category", required=True, choices=[c.value for c in TestCategory], help="测试项目分类")
    parser_risk.add_argument("--days", type=int, default=30, help="分析天数")
    
    parser_export = subparsers.add_parser("export", help="导出趋势报告")
    parser_export.add_argument("--category", required=True, choices=[c.value for c in TestCategory], help="测试项目分类")
    parser_export.add_argument("--days", type=int, default=30, help="分析天数")
    parser_export.add_argument("--output", help="输出文件路径")
    
    parser_viz = subparsers.add_parser("visualize", help="生成可视化数据")
    parser_viz.add_argument("--category", required=True, choices=[c.value for c in TestCategory], help="测试项目分类")
    parser_viz.add_argument("--days", type=int, default=30, help="分析天数")
    parser_viz.add_argument("--metrics", nargs="+", default=["pass_rate", "test_count"], help="分析指标列表")
    parser_viz.add_argument("--output", help="输出文件路径")
    
    parser_summary = subparsers.add_parser("summary", help="存储摘要")
    
    parser_migrate = subparsers.add_parser("migrate", help="迁移报告")
    parser_migrate.add_argument("--source", required=True, help="源版本")
    parser_migrate.add_argument("--target", required=True, help="目标版本")
    parser_migrate.add_argument("--category", choices=[c.value for c in TestCategory], help="测试项目分类")
    
    parser_cleanup = subparsers.add_parser("cleanup", help="清理旧版本")
    parser_cleanup.add_argument("--keep", type=int, default=5, help="保留版本数量")
    parser_cleanup.add_argument("--delete", action="store_true", help="直接删除而非归档")

    args = parser.parse_args()

    storage = ReportStorage()

    if args.command == "store":
        test_category = TestCategory(args.category) if args.category else None
        metadata = storage.store_report(
            report_file=args.report_file,
            version=args.version,
            report_type=ReportType(args.type),
            description=args.description,
            tags=args.tags,
            test_category=test_category
        )

        print("\n" + "=" * 60)
        print("报告已存储")
        print("=" * 60)
        print(f"报告ID: {metadata.report_id}")
        print(f"版本: {metadata.version}")
        print(f"类型: {metadata.report_type.value}")
        if metadata.test_category:
            print(f"测试分类: {metadata.test_category.value}")
        print(f"文件大小: {metadata.file_size} bytes")

    elif args.command == "list":
        report_type = ReportType(args.type) if args.type else None
        test_category = TestCategory(args.category) if args.category else None
        reports = storage.list_reports(
            version=args.version,
            report_type=report_type,
            days=args.days,
            test_category=test_category
        )

        print("\n" + "=" * 60)
        print("报告列表")
        print("=" * 60)
        print(f"总数: {len(reports)}")

        for report in reports[:20]:
            category_str = f" [{report.test_category.value}]" if report.test_category else ""
            print(f"  [{report.created_at.strftime('%Y-%m-%d')}] {report.report_id} ({report.report_type.value}){category_str}")

    elif args.command == "query":
        if args.report_id:
            metadata = storage.get_report(args.report_id)
            if metadata:
                print("\n" + "=" * 60)
                print(f"报告详情: {args.report_id}")
                print("=" * 60)
                print(f"类型: {metadata.report_type.value}")
                print(f"版本: {metadata.version}")
                print(f"创建时间: {metadata.created_at}")
                print(f"状态: {metadata.status.value}")
                print(f"文件路径: {metadata.file_path}")
                if metadata.test_category:
                    print(f"测试分类: {metadata.test_category.value}")
                if metadata.description:
                    print(f"描述: {metadata.description}")
                if metadata.metrics:
                    print(f"指标: {json.dumps(metadata.metrics, indent=2, ensure_ascii=False)}")
            else:
                print(f"报告不存在: {args.report_id}")

        elif args.tags:
            query = ReportHistoryQuery(storage)
            reports = query.query_by_tags(args.tags)
            print("\n" + "=" * 60)
            print(f"标签查询结果: {args.tags}")
            print("=" * 60)
            for report in reports[:20]:
                print(f"  {report.report_id} - {report.report_type.value}")

    elif args.command == "compare":
        comparator = ReportComparator(storage)
        if args.category:
            result = comparator.compare_categories(
                TestCategory(args.category),
                args.version1,
                args.version2
            )
            print("\n" + "=" * 60)
            print(f"分类对比: {args.category} ({args.version1} vs {args.version2})")
            print("=" * 60)
            print(f"版本1报告数: {result['reports_v1']}")
            print(f"版本2报告数: {result['reports_v2']}")
        else:
            result = comparator.compare_versions(args.version1, args.version2)

            print("\n" + "=" * 60)
            print(f"版本对比: {args.version1} vs {args.version2}")
            print("=" * 60)
            print(f"版本1报告数: {result['reports_v1']}")
            print(f"版本2报告数: {result['reports_v2']}")

            print("\n按类型对比:")
            for type_name, data in result['by_type_comparison'].items():
                print(f"  {type_name}: {data['v1']} -> {data['v2']} ({data['diff']:+d})")

            if result.get('by_category_comparison'):
                print("\n按测试分类对比:")
                for cat_name, data in result['by_category_comparison'].items():
                    print(f"  {cat_name}: {data['v1']} -> {data['v2']} ({data['diff']:+d})")

    elif args.command == "archive":
        success = storage.archive_report(args.report_id)
        if success:
            print(f"报告已归档: {args.report_id}")
        else:
            print(f"归档失败: {args.report_id}")

    elif args.command == "delete":
        success = storage.delete_report(args.report_id)
        if success:
            print(f"报告已删除: {args.report_id}")
        else:
            print(f"删除失败: {args.report_id}")

    elif args.command == "versions":
        index_manager = ReportIndexManager(storage)
        versions = index_manager.list_versions()

        print("\n" + "=" * 60)
        print("版本列表")
        print("=" * 60)
        for ver in versions:
            print(f"  {ver.version} - {len(ver.reports)} 报告 - {ver.total_size} bytes")

    elif args.command == "trend":
        analyzer = ReportTrendAnalyzer(storage)
        category = TestCategory(args.category)

        if args.metric == "pass_rate":
            result = analyzer.analyze_pass_rate_trend(category, args.days)
        elif args.metric == "test_count":
            result = analyzer.analyze_test_count_trend(category, args.days)
        else:
            result = analyzer.analyze_pass_rate_trend(category, args.days)

        print("\n" + "=" * 60)
        print(f"趋势分析: {category.value} - {args.metric}")
        print("=" * 60)
        print(f"趋势方向: {result.trend_direction}")
        print(f"变化率: {result.change_rate:.2f}%")
        print(f"平均值: {result.average:.2f}")
        print(f"最小值: {result.minimum:.2f}")
        print(f"最大值: {result.maximum:.2f}")
        print(f"数据点数量: {len(result.data_points)}")

        if result.anomalies:
            print(f"\n异常点 ({len(result.anomalies)} 个):")
            for anomaly in result.anomalies[:5]:
                print(f"  {anomaly['timestamp']}: {anomaly['value']:.2f}")

        if result.predictions:
            print(f"\n预测值:")
            for pred in result.predictions:
                print(f"  {pred.timestamp.strftime('%Y-%m-%d')}: {pred.value:.2f}")

    elif args.command == "stats":
        stats = storage.get_category_statistics()

        print("\n" + "=" * 60)
        print("分类统计")
        print("=" * 60)
        for category, data in stats.items():
            print(f"\n{category}:")
            print(f"  报告总数: {data['total_reports']}")
            print(f"  总大小: {data['total_size']} bytes")
            if data['latest_report']:
                print(f"  最新报告: {data['latest_report']}")

    elif args.command == "test":
        tester = ReportVersionManagerTest()
        if tester.setup():
            results = tester.run_all_tests()
            tester.teardown()

            print("\n" + "=" * 60)
            print("测试结果")
            print("=" * 60)
            print(f"总计: {results['total']}")
            print(f"通过: {results['passed']}")
            print(f"失败: {results['failed']}")

            print("\n详细结果:")
            for result in results['results']:
                status = "✓" if result['status'] == 'passed' else "✗"
                print(f"  {status} {result['test']}")
                if result['status'] != 'passed':
                    print(f"    错误: {result.get('error', 'Unknown')}")
    
    elif args.command == "version":
        version_manager = VersionManager(storage)
        
        if args.action == "create":
            if not args.base:
                print("错误: 需要指定 --base 参数")
                return
            new_version = version_manager.create_version(args.base, args.type)
            print(f"\n创建的新版本: {new_version}")
            
        elif args.action == "next":
            if not args.base:
                print("错误: 需要指定 --base 参数")
                return
            next_version = version_manager.get_next_version(args.base)
            print(f"\n建议的下一个版本: {next_version}")
            
        elif args.action == "compare":
            if not args.version1 or not args.version2:
                print("错误: 需要指定 --version1 和 --version2 参数")
                return
            result = version_manager.compare_versions(args.version1, args.version2)
            comparison = "小于" if result < 0 else ("等于" if result == 0 else "大于")
            print(f"\n{args.version1} {comparison} {args.version2}")
            
        elif args.action == "stats":
            stats = version_manager.get_version_statistics()
            print("\n" + "=" * 60)
            print("版本统计")
            print("=" * 60)
            print(f"总版本数: {stats['total_versions']}")
            print(f"稳定版本: {stats['stable_versions']}")
            print(f"预发布版本: {stats['prerelease_versions']}")
            print(f"主版本号: {stats['major_versions']}")
            if stats['latest_version']:
                print(f"最新版本: {stats['latest_version']}")
            if stats['oldest_version']:
                print(f"最旧版本: {stats['oldest_version']}")
            if stats['deprecated_versions']:
                print(f"已废弃版本: {stats['deprecated_versions']}")
                
        elif args.action == "lineage":
            if not args.base:
                print("错误: 需要指定 --base 参数")
                return
            lineage = version_manager.get_version_lineage(args.base)
            print("\n" + "=" * 60)
            print(f"版本演变谱系: {args.base}")
            print("=" * 60)
            if lineage['predecessors']:
                print(f"前置版本: {', '.join(lineage['predecessors'])}")
            if lineage['successors']:
                print(f"后续版本: {', '.join(lineage['successors'])}")
            if lineage['replaces']:
                print(f"替换版本: {lineage['replaces']}")
            if lineage['replaced_by']:
                print(f"被替换为: {lineage['replaced_by']}")
            if lineage['deprecated_by']:
                print(f"被废弃于: {lineage['deprecated_by']}")
    
    elif args.command == "dashboard":
        analyzer = ReportTrendAnalyzer(storage)
        dashboard = analyzer.generate_dashboard_data(args.days)
        
        output = json.dumps(dashboard, indent=2, ensure_ascii=False)
        
        if args.output:
            with open(args.output, 'w', encoding='utf-8') as f:
                f.write(output)
            print(f"仪表板数据已保存到: {args.output}")
        else:
            print(output)
    
    elif args.command == "risk":
        analyzer = ReportTrendAnalyzer(storage)
        category = TestCategory(args.category)
        risk = analyzer.analyze_regression_risk(category, args.days)
        
        print("\n" + "=" * 60)
        print(f"回归风险分析: {category.value}")
        print("=" * 60)
        print(f"风险等级: {risk['risk_level']}")
        print(f"风险分数: {risk['risk_score']}/100")
        
        if risk['risk_factors']:
            print("\n风险因素:")
            for factor in risk['risk_factors']:
                print(f"  [{factor['severity']}] {factor['factor']}: {factor['description']}")
        
        if risk['recommendations']:
            print("\n建议:")
            for rec in risk['recommendations']:
                print(f"  - {rec}")
    
    elif args.command == "export":
        analyzer = ReportTrendAnalyzer(storage)
        category = TestCategory(args.category)
        report = analyzer.export_trend_report(category, days=args.days)
        
        output = json.dumps(report, indent=2, ensure_ascii=False)
        
        if args.output:
            with open(args.output, 'w', encoding='utf-8') as f:
                f.write(output)
            print(f"趋势报告已导出到: {args.output}")
        else:
            print(output)
    
    elif args.command == "visualize":
        analyzer = ReportTrendAnalyzer(storage)
        category = TestCategory(args.category)
        viz_data = analyzer.generate_visualization_data(category, args.metrics, args.days)
        
        output = json.dumps(viz_data, indent=2, ensure_ascii=False)
        
        if args.output:
            with open(args.output, 'w', encoding='utf-8') as f:
                f.write(output)
            print(f"可视化数据已保存到: {args.output}")
        else:
            print(output)
    
    elif args.command == "summary":
        summary = storage.get_storage_summary()
        
        print("\n" + "=" * 60)
        print("存储摘要")
        print("=" * 60)
        print(f"总报告数: {summary['total_reports']}")
        print(f"总大小: {summary['total_size_mb']} MB")
        
        if summary['by_category']:
            print("\n按分类:")
            for cat, count in summary['by_category'].items():
                print(f"  {cat}: {count}")
        
        if summary['by_type']:
            print("\n按类型:")
            for type_name, count in summary['by_type'].items():
                print(f"  {type_name}: {count}")
        
        if summary['by_version']:
            print("\n按版本:")
            for ver, count in sorted(summary['by_version'].items()):
                print(f"  {ver}: {count}")
        
        if summary['oldest_report']:
            print(f"\n最早报告: {summary['oldest_report']}")
        if summary['newest_report']:
            print(f"最新报告: {summary['newest_report']}")
    
    elif args.command == "migrate":
        test_category = TestCategory(args.category) if args.category else None
        count = storage.migrate_reports(args.source, args.target, test_category)
        print(f"\n已迁移 {count} 个报告从 {args.source} 到 {args.target}")
    
    elif args.command == "cleanup":
        result = storage.cleanup_old_versions(args.keep, archive=not args.delete)
        
        print("\n" + "=" * 60)
        print("清理结果")
        print("=" * 60)
        print(f"保留版本: {result['kept_versions']}")
        print(f"移除版本: {result['removed_versions']}")
        print(f"处理报告数: {result['reports_processed']}")
        if not args.delete:
            print(f"归档报告数: {result['reports_archived']}")
        else:
            print(f"删除报告数: {result['reports_deleted']}")
            print(f"释放空间: {result['space_freed']} bytes")

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
