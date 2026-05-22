#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
报告版本管理器增强版 - Sanliu 技能

功能增强：
- 报告分类存储（单元/集成/E2E/性能/安全/回归）
- 报告归档功能
- 报告查询接口
- 报告统计分析
- 报告对比功能
"""

import gzip
import hashlib
import json
import logging
import os
import re
import shutil
import sys
import threading
import zipfile
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Generator

from path_config_manager import PathConfigManager

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - [%(name)s] %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


class ReportCategory(Enum):
    """报告分类枚举"""
    UNIT_TEST = "unit"
    INTEGRATION_TEST = "integration"
    E2E_TEST = "e2e"
    PERFORMANCE = "performance"
    SECURITY = "security"
    REGRESSION = "regression"
    COVERAGE = "coverage"
    PIPELINE = "pipeline"
    QUALITY = "quality"
    CUSTOM = "custom"


class ReportStatus(Enum):
    """报告状态枚举"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    ARCHIVED = "archived"
    DEPRECATED = "deprecated"


class ReportFormat(Enum):
    """报告格式枚举"""
    JSON = "json"
    XML = "xml"
    HTML = "html"
    MARKDOWN = "md"
    JUNIT = "junit"
    COVERAGE = "coverage"
    CUSTOM = "custom"


class ArchiveFormat(Enum):
    """归档格式枚举"""
    ZIP = "zip"
    GZIP = "gzip"
    TAR = "tar"
    NONE = "none"


@dataclass
class ReportInfo:
    """报告信息数据类"""
    report_id: str
    name: str
    category: str
    version: str
    format: str
    file_path: str
    created_at: str
    status: str = ReportStatus.COMPLETED.value
    project: Optional[str] = None
    branch: Optional[str] = None
    commit: Optional[str] = None
    author: Optional[str] = None
    description: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    checksum: Optional[str] = None
    size_bytes: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)
    metrics: Dict[str, Any] = field(default_factory=dict)
    is_archived: bool = False
    archive_path: Optional[str] = None
    archived_at: Optional[str] = None


@dataclass
class ReportArchive:
    """报告归档数据类"""
    archive_id: str
    name: str
    created_at: str
    format: str
    file_path: str
    size_bytes: int
    report_count: int
    report_ids: List[str]
    categories: List[str]
    date_range: Dict[str, str]
    description: Optional[str] = None
    checksum: Optional[str] = None


@dataclass
class ReportQuery:
    """报告查询数据类"""
    categories: Optional[List[str]] = None
    status: Optional[List[str]] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    project: Optional[str] = None
    branch: Optional[str] = None
    author: Optional[str] = None
    tags: Optional[List[str]] = None
    min_size: Optional[int] = None
    max_size: Optional[int] = None
    search_text: Optional[str] = None
    limit: int = 100
    offset: int = 0
    sort_by: str = "created_at"
    sort_order: str = "desc"


@dataclass
class ReportComparison:
    """报告对比数据类"""
    comparison_id: str
    report1_id: str
    report2_id: str
    created_at: str
    metrics_diff: Dict[str, Any]
    summary: Dict[str, Any]
    recommendations: List[str]


@dataclass
class CategoryConfig:
    """分类配置数据类"""
    category: str
    display_name: str
    description: str
    directory: str
    file_patterns: List[str]
    retention_days: int = 90
    auto_archive: bool = True
    archive_after_days: int = 30


class ReportCategoryManager:
    """报告分类管理器"""
    
    CATEGORY_CONFIGS: Dict[str, CategoryConfig] = {
        ReportCategory.UNIT_TEST.value: CategoryConfig(
            category=ReportCategory.UNIT_TEST.value,
            display_name="单元测试报告",
            description="单元测试执行报告",
            directory="unit_tests",
            file_patterns=["*unit*test*", "*test_unit*", "pytest_unit*"],
            retention_days=90,
            auto_archive=True,
            archive_after_days=30
        ),
        ReportCategory.INTEGRATION_TEST.value: CategoryConfig(
            category=ReportCategory.INTEGRATION_TEST.value,
            display_name="集成测试报告",
            description="集成测试执行报告",
            directory="integration_tests",
            file_patterns=["*integration*test*", "*test_integration*"],
            retention_days=90,
            auto_archive=True,
            archive_after_days=30
        ),
        ReportCategory.E2E_TEST.value: CategoryConfig(
            category=ReportCategory.E2E_TEST.value,
            display_name="E2E测试报告",
            description="端到端测试执行报告",
            directory="e2e_tests",
            file_patterns=["*e2e*", "*end_to_end*", "*playwright*"],
            retention_days=90,
            auto_archive=True,
            archive_after_days=30
        ),
        ReportCategory.PERFORMANCE.value: CategoryConfig(
            category=ReportCategory.PERFORMANCE.value,
            display_name="性能测试报告",
            description="性能测试和基准测试报告",
            directory="performance_tests",
            file_patterns=["*performance*", "*benchmark*", "*load*"],
            retention_days=180,
            auto_archive=True,
            archive_after_days=60
        ),
        ReportCategory.SECURITY.value: CategoryConfig(
            category=ReportCategory.SECURITY.value,
            display_name="安全测试报告",
            description="安全扫描和渗透测试报告",
            directory="security_tests",
            file_patterns=["*security*", "*vulnerability*", "*sast*"],
            retention_days=365,
            auto_archive=True,
            archive_after_days=90
        ),
        ReportCategory.REGRESSION.value: CategoryConfig(
            category=ReportCategory.REGRESSION.value,
            display_name="回归测试报告",
            description="回归测试执行报告",
            directory="regression_tests",
            file_patterns=["*regression*", "*smoke*"],
            retention_days=90,
            auto_archive=True,
            archive_after_days=30
        ),
        ReportCategory.COVERAGE.value: CategoryConfig(
            category=ReportCategory.COVERAGE.value,
            display_name="覆盖率报告",
            description="代码覆盖率分析报告",
            directory="coverage",
            file_patterns=["*coverage*", "*cov*"],
            retention_days=90,
            auto_archive=True,
            archive_after_days=30
        ),
        ReportCategory.PIPELINE.value: CategoryConfig(
            category=ReportCategory.PIPELINE.value,
            display_name="流水线报告",
            description="CI/CD流水线执行报告",
            directory="pipeline",
            file_patterns=["*pipeline*", "*ci*", "*cd*"],
            retention_days=60,
            auto_archive=True,
            archive_after_days=14
        ),
        ReportCategory.QUALITY.value: CategoryConfig(
            category=ReportCategory.QUALITY.value,
            display_name="质量报告",
            description="代码质量和静态分析报告",
            directory="quality",
            file_patterns=["*quality*", "*sonar*", "*lint*"],
            retention_days=90,
            auto_archive=True,
            archive_after_days=30
        ),
        ReportCategory.CUSTOM.value: CategoryConfig(
            category=ReportCategory.CUSTOM.value,
            display_name="自定义报告",
            description="用户自定义报告",
            directory="custom",
            file_patterns=["*"],
            retention_days=90,
            auto_archive=False,
            archive_after_days=30
        )
    }
    
    @classmethod
    def get_category_for_file(cls, file_name: str) -> str:
        """根据文件名自动分类"""
        file_lower = file_name.lower()
        
        for category, config in cls.CATEGORY_CONFIGS.items():
            for pattern in config.file_patterns:
                pattern_lower = pattern.lower().replace("*", "")
                if pattern_lower and pattern_lower in file_lower:
                    return category
        
        return ReportCategory.CUSTOM.value
    
    @classmethod
    def get_directory_for_category(cls, category: str) -> str:
        """获取分类对应的目录"""
        config = cls.CATEGORY_CONFIGS.get(category)
        return config.directory if config else "custom"


class ReportArchiveManager:
    """报告归档管理器"""
    
    ARCHIVE_DIR = "report_archives"
    MAX_ARCHIVE_SIZE_MB = 500
    
    def __init__(self, base_path: Path):
        self.base_path = base_path
        self.archive_dir = base_path / self.ARCHIVE_DIR
        self._lock = threading.Lock()
        self._ensure_archive_dir()
    
    def _ensure_archive_dir(self):
        """确保归档目录存在"""
        self.archive_dir.mkdir(parents=True, exist_ok=True)
    
    def create_archive(
        self,
        report_ids: List[str],
        reports: Dict[str, ReportInfo],
        name: Optional[str] = None,
        description: Optional[str] = None,
        archive_format: ArchiveFormat = ArchiveFormat.ZIP
    ) -> Optional[ReportArchive]:
        """
        创建报告归档
        
        Args:
            report_ids: 要归档的报告ID列表
            reports: 报告信息字典
            name: 归档名称
            description: 归档描述
            archive_format: 归档格式
            
        Returns:
            归档对象
        """
        if not report_ids:
            return None
        
        archive_id = f"archive_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        if name is None:
            name = f"reports_archive_{datetime.now().strftime('%Y%m%d')}"
        
        archive_file = self.archive_dir / f"{archive_id}.{archive_format.value}"
        
        archived_reports = []
        total_size = 0
        categories = set()
        dates = []
        
        try:
            if archive_format == ArchiveFormat.ZIP:
                with zipfile.ZipFile(archive_file, 'w', zipfile.ZIP_DEFLATED) as zf:
                    for report_id in report_ids:
                        report = reports.get(report_id)
                        if report and not report.is_archived:
                            report_path = Path(report.file_path)
                            if report_path.exists():
                                arcname = f"{report.category}/{report_path.name}"
                                zf.write(report_path, arcname)
                                archived_reports.append(report_id)
                                total_size += report.size_bytes
                                categories.add(report.category)
                                dates.append(report.created_at)
            elif archive_format == ArchiveFormat.GZIP:
                for report_id in report_ids:
                    report = reports.get(report_id)
                    if report and not report.is_archived:
                        report_path = Path(report.file_path)
                        if report_path.exists():
                            gz_path = self.archive_dir / f"{report_id}.gz"
                            with open(report_path, 'rb') as f_in:
                                with gzip.open(gz_path, 'wb') as f_out:
                                    shutil.copyfileobj(f_in, f_out)
                            archived_reports.append(report_id)
                            total_size += report.size_bytes
                            categories.add(report.category)
                            dates.append(report.created_at)
            
            if not archived_reports:
                return None
            
            date_range = {}
            if dates:
                dates.sort()
                date_range = {
                    "start": dates[0][:10],
                    "end": dates[-1][:10]
                }
            
            archive = ReportArchive(
                archive_id=archive_id,
                name=name,
                created_at=datetime.now().isoformat(),
                format=archive_format.value,
                file_path=str(archive_file),
                size_bytes=archive_file.stat().st_size if archive_file.exists() else total_size,
                report_count=len(archived_reports),
                report_ids=archived_reports,
                categories=list(categories),
                date_range=date_range,
                description=description
            )
            
            self._save_archive_metadata(archive)
            
            return archive
            
        except Exception as e:
            logger.error(f"创建归档失败: {e}")
            return None
    
    def _save_archive_metadata(self, archive: ReportArchive):
        """保存归档元数据"""
        meta_path = self.archive_dir / f"{archive.archive_id}.json"
        with open(meta_path, 'w', encoding='utf-8') as f:
            json.dump(asdict(archive), f, indent=2, ensure_ascii=False)
    
    def load_archive(self, archive_id: str) -> Optional[ReportArchive]:
        """加载归档信息"""
        meta_path = self.archive_dir / f"{archive_id}.json"
        
        if not meta_path.exists():
            return None
        
        try:
            with open(meta_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return ReportArchive(**data)
        except Exception as e:
            logger.error(f"加载归档失败: {e}")
            return None
    
    def extract_archive(
        self,
        archive_id: str,
        target_dir: Optional[Path] = None
    ) -> Tuple[bool, List[str]]:
        """
        解压归档
        
        Args:
            archive_id: 归档ID
            target_dir: 目标目录
            
        Returns:
            (是否成功, 解压的文件列表) 元组
        """
        archive = self.load_archive(archive_id)
        
        if archive is None:
            return False, []
        
        if target_dir is None:
            target_dir = self.archive_dir / "extracted" / archive_id
        
        target_dir.mkdir(parents=True, exist_ok=True)
        
        archive_path = Path(archive.file_path)
        extracted_files = []
        
        try:
            if archive.format == ArchiveFormat.ZIP.value:
                with zipfile.ZipFile(archive_path, 'r') as zf:
                    zf.extractall(target_dir)
                    extracted_files = zf.namelist()
            elif archive.format == ArchiveFormat.GZIP.value:
                for report_id in archive.report_ids:
                    gz_path = self.archive_dir / f"{report_id}.gz"
                    if gz_path.exists():
                        target_file = target_dir / f"{report_id}"
                        with gzip.open(gz_path, 'rb') as f_in:
                            with open(target_file, 'wb') as f_out:
                                shutil.copyfileobj(f_in, f_out)
                        extracted_files.append(str(target_file))
            
            return True, extracted_files
            
        except Exception as e:
            logger.error(f"解压归档失败: {e}")
            return False, []
    
    def list_archives(
        self,
        category: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """列出归档"""
        archives = []
        
        for meta_file in self.archive_dir.glob("*.json"):
            try:
                with open(meta_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                if category and category not in data.get("categories", []):
                    continue
                
                archives.append({
                    "archive_id": data.get("archive_id"),
                    "name": data.get("name"),
                    "created_at": data.get("created_at"),
                    "report_count": data.get("report_count"),
                    "size_bytes": data.get("size_bytes"),
                    "categories": data.get("categories"),
                    "date_range": data.get("date_range")
                })
            except:
                pass
        
        archives.sort(key=lambda x: x["created_at"], reverse=True)
        return archives[:limit]
    
    def delete_archive(self, archive_id: str) -> bool:
        """删除归档"""
        try:
            archive = self.load_archive(archive_id)
            
            if archive is None:
                return False
            
            archive_path = Path(archive.file_path)
            if archive_path.exists():
                archive_path.unlink()
            
            meta_path = self.archive_dir / f"{archive_id}.json"
            if meta_path.exists():
                meta_path.unlink()
            
            return True
        except Exception as e:
            logger.error(f"删除归档失败: {e}")
            return False


class ReportQueryEngine:
    """报告查询引擎"""
    
    def __init__(self, reports: Dict[str, ReportInfo]):
        self.reports = reports
    
    def query(self, query: ReportQuery) -> List[ReportInfo]:
        """
        执行查询
        
        Args:
            query: 查询条件
            
        Returns:
            匹配的报告列表
        """
        results = []
        
        for report in self.reports.values():
            if not self._match_query(report, query):
                continue
            results.append(report)
        
        results = self._sort_results(results, query.sort_by, query.sort_order)
        
        return results[query.offset:query.offset + query.limit]
    
    def _match_query(self, report: ReportInfo, query: ReportQuery) -> bool:
        """检查报告是否匹配查询条件"""
        if query.categories and report.category not in query.categories:
            return False
        
        if query.status and report.status not in query.status:
            return False
        
        if query.start_date and report.created_at < query.start_date:
            return False
        
        if query.end_date and report.created_at > query.end_date:
            return False
        
        if query.project and report.project != query.project:
            return False
        
        if query.branch and report.branch != query.branch:
            return False
        
        if query.author and report.author != query.author:
            return False
        
        if query.tags and not any(t in report.tags for t in query.tags):
            return False
        
        if query.min_size and report.size_bytes < query.min_size:
            return False
        
        if query.max_size and report.size_bytes > query.max_size:
            return False
        
        if query.search_text:
            search_lower = query.search_text.lower()
            if not any([
                search_lower in report.name.lower(),
                report.description and search_lower in report.description.lower(),
                any(search_lower in tag.lower() for tag in report.tags)
            ]):
                return False
        
        return True
    
    def _sort_results(
        self,
        results: List[ReportInfo],
        sort_by: str,
        sort_order: str
    ) -> List[ReportInfo]:
        """排序结果"""
        reverse = sort_order.lower() == "desc"
        
        def get_sort_key(report: ReportInfo):
            value = getattr(report, sort_by, None)
            if value is None:
                value = ""
            return value
        
        return sorted(results, key=get_sort_key, reverse=reverse)


class EnhancedReportVersionManager:
    """
    增强版报告版本管理器
    
    功能：
    - 报告分类存储
    - 报告归档管理
    - 报告查询接口
    - 报告统计分析
    - 报告对比功能
    """
    
    INDEX_FILE = "report_index.json"
    
    def __init__(self, base_path: Path, path_manager: Optional[Any] = None):
        self.base_path = base_path
        self.path_manager = path_manager
        
        if path_manager is not None:
            self.reports_dir = Path(path_manager.get_docs_reports_path())
        else:
            self.reports_dir = base_path / "docs" / "reports"
        
        self.index_path = self.reports_dir / self.INDEX_FILE
        
        self._lock = threading.Lock()
        self._reports: Dict[str, ReportInfo] = {}
        
        self.archive_manager = ReportArchiveManager(base_path)
        self.query_engine: Optional[ReportQueryEngine] = None
        
        self._ensure_directories()
        self._load_index()
        self._update_query_engine()
    
    def _ensure_directories(self):
        """确保基础目录存在（不预创建报告分类目录）"""
        self.reports_dir.mkdir(parents=True, exist_ok=True)
    
    def ensure_report_category_directory(self, category: str) -> Path:
        """确保报告分类目录存在，按需创建"""
        category_dir = self.reports_dir / ReportCategoryManager.get_directory_for_category(category)
        if not category_dir.exists():
            category_dir.mkdir(parents=True, exist_ok=True)
            logger.info(f"创建报告目录: {category_dir}")
        return category_dir
    
    def _load_index(self):
        """加载报告索引"""
        if self.index_path.exists():
            try:
                with open(self.index_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                self._reports = {
                    k: ReportInfo(**v) for k, v in data.items()
                }
            except Exception as e:
                logger.warning(f"加载报告索引失败: {e}")
    
    def _save_index(self):
        """保存报告索引"""
        try:
            with open(self.index_path, 'w', encoding='utf-8') as f:
                json.dump(
                    {k: asdict(v) for k, v in self._reports.items()},
                    f, indent=2, ensure_ascii=False
                )
        except Exception as e:
            logger.error(f"保存报告索引失败: {e}")
    
    def _update_query_engine(self):
        """更新查询引擎"""
        self.query_engine = ReportQueryEngine(self._reports)
    
    def _generate_report_id(self, name: str, category: str) -> str:
        """生成报告ID"""
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        name_hash = hashlib.md5(name.encode()).hexdigest()[:8]
        return f"rpt_{category}_{timestamp}_{name_hash}"
    
    def store_report(
        self,
        file_path: str,
        category: Optional[str] = None,
        name: Optional[str] = None,
        version: str = "1.0.0",
        project: Optional[str] = None,
        branch: Optional[str] = None,
        commit: Optional[str] = None,
        author: Optional[str] = None,
        description: Optional[str] = None,
        tags: Optional[List[str]] = None,
        metrics: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> ReportInfo:
        """
        存储报告
        
        Args:
            file_path: 报告文件路径
            category: 报告分类
            name: 报告名称
            version: 版本号
            project: 项目名称
            branch: 分支名称
            commit: 提交哈希
            author: 作者
            description: 描述
            tags: 标签
            metrics: 指标数据
            metadata: 元数据
            
        Returns:
            报告信息对象
        """
        path = Path(file_path)
        
        if not path.exists():
            raise FileNotFoundError(f"报告文件不存在: {file_path}")
        
        if category is None:
            category = ReportCategoryManager.get_category_for_file(path.name)
        
        if name is None:
            name = path.stem
        
        report_id = self._generate_report_id(name, category)
        
        content = path.read_bytes()
        checksum = hashlib.md5(content).hexdigest()
        size_bytes = len(content)
        
        report_format = self._detect_format(path)
        
        category_dir = self.ensure_report_category_directory(category)
        
        stored_path = category_dir / path.name
        if path != stored_path:
            shutil.copy2(path, stored_path)
        
        report_info = ReportInfo(
            report_id=report_id,
            name=name,
            category=category,
            version=version,
            format=report_format,
            file_path=str(stored_path),
            created_at=datetime.now().isoformat(),
            status=ReportStatus.COMPLETED.value,
            project=project,
            branch=branch,
            commit=commit,
            author=author,
            description=description,
            tags=tags or [],
            checksum=checksum,
            size_bytes=size_bytes,
            metadata=metadata or {},
            metrics=metrics or {}
        )
        
        with self._lock:
            self._reports[report_id] = report_info
            self._save_index()
            self._update_query_engine()
        
        return report_info
    
    def _detect_format(self, path: Path) -> str:
        """检测报告格式"""
        suffix = path.suffix.lower()
        
        format_map = {
            '.json': ReportFormat.JSON.value,
            '.xml': ReportFormat.XML.value,
            '.html': ReportFormat.HTML.value,
            '.md': ReportFormat.MARKDOWN.value,
            '.junit': ReportFormat.JUNIT.value,
            '.coverage': ReportFormat.COVERAGE.value
        }
        
        return format_map.get(suffix, ReportFormat.CUSTOM.value)
    
    def get_report(self, report_id: str) -> Optional[ReportInfo]:
        """获取报告信息"""
        return self._reports.get(report_id)
    
    def query_reports(self, query: ReportQuery) -> List[ReportInfo]:
        """
        查询报告
        
        Args:
            query: 查询条件
            
        Returns:
            报告列表
        """
        if self.query_engine is None:
            return []
        return self.query_engine.query(query)
    
    def list_reports(
        self,
        category: Optional[str] = None,
        limit: int = 100
    ) -> List[ReportInfo]:
        """列出报告"""
        results = []
        
        for report in self._reports.values():
            if category and report.category != category:
                continue
            results.append(report)
        
        results.sort(key=lambda x: x.created_at, reverse=True)
        return results[:limit]
    
    def archive_reports(
        self,
        report_ids: List[str],
        name: Optional[str] = None,
        description: Optional[str] = None,
        archive_format: ArchiveFormat = ArchiveFormat.ZIP
    ) -> Optional[ReportArchive]:
        """
        归档报告
        
        Args:
            report_ids: 要归档的报告ID列表
            name: 归档名称
            description: 归档描述
            archive_format: 归档格式
            
        Returns:
            归档对象
        """
        archive = self.archive_manager.create_archive(
            report_ids, self._reports, name, description, archive_format
        )
        
        if archive:
            with self._lock:
                for report_id in archive.report_ids:
                    if report_id in self._reports:
                        self._reports[report_id].is_archived = True
                        self._reports[report_id].archive_path = archive.file_path
                        self._reports[report_id].archived_at = archive.created_at
                
                self._save_index()
        
        return archive
    
    def compare_reports(
        self,
        report_id1: str,
        report_id2: str
    ) -> Optional[ReportComparison]:
        """
        对比两个报告
        
        Args:
            report_id1: 第一个报告ID
            report_id2: 第二个报告ID
            
        Returns:
            对比结果
        """
        report1 = self._reports.get(report_id1)
        report2 = self._reports.get(report_id2)
        
        if report1 is None or report2 is None:
            return None
        
        comparison_id = f"cmp_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        metrics_diff = self._calculate_metrics_diff(
            report1.metrics, report2.metrics
        )
        
        summary = {
            "report1": {
                "id": report1.report_id,
                "name": report1.name,
                "category": report1.category,
                "created_at": report1.created_at
            },
            "report2": {
                "id": report2.report_id,
                "name": report2.name,
                "category": report2.category,
                "created_at": report2.created_at
            },
            "time_diff_hours": self._calculate_time_diff(
                report1.created_at, report2.created_at
            ),
            "size_diff_bytes": report2.size_bytes - report1.size_bytes
        }
        
        recommendations = self._generate_recommendations(metrics_diff)
        
        return ReportComparison(
            comparison_id=comparison_id,
            report1_id=report_id1,
            report2_id=report_id2,
            created_at=datetime.now().isoformat(),
            metrics_diff=metrics_diff,
            summary=summary,
            recommendations=recommendations
        )
    
    def _calculate_metrics_diff(
        self,
        metrics1: Dict[str, Any],
        metrics2: Dict[str, Any]
    ) -> Dict[str, Any]:
        """计算指标差异"""
        diff = {}
        
        all_keys = set(metrics1.keys()) | set(metrics2.keys())
        
        for key in all_keys:
            val1 = metrics1.get(key)
            val2 = metrics2.get(key)
            
            if isinstance(val1, (int, float)) and isinstance(val2, (int, float)):
                diff[key] = {
                    "old": val1,
                    "new": val2,
                    "change": val2 - val1,
                    "change_percent": ((val2 - val1) / val1 * 100) if val1 != 0 else None
                }
            else:
                diff[key] = {
                    "old": val1,
                    "new": val2
                }
        
        return diff
    
    def _calculate_time_diff(self, time1: str, time2: str) -> float:
        """计算时间差异（小时）"""
        try:
            t1 = datetime.fromisoformat(time1)
            t2 = datetime.fromisoformat(time2)
            return abs((t2 - t1).total_seconds() / 3600)
        except:
            return 0
    
    def _generate_recommendations(self, metrics_diff: Dict[str, Any]) -> List[str]:
        """生成建议"""
        recommendations = []
        
        for key, diff in metrics_diff.items():
            if "change_percent" in diff and diff["change_percent"] is not None:
                change = diff["change_percent"]
                
                if key in ["failures", "errors", "bugs"]:
                    if change > 0:
                        recommendations.append(f"警告: {key} 增加了 {change:.1f}%")
                    elif change < 0:
                        recommendations.append(f"改进: {key} 减少了 {abs(change):.1f}%")
                
                elif key in ["pass_rate", "coverage", "score"]:
                    if change > 0:
                        recommendations.append(f"改进: {key} 提升了 {change:.1f}%")
                    elif change < 0:
                        recommendations.append(f"警告: {key} 下降了 {abs(change):.1f}%")
        
        return recommendations
    
    def get_statistics(
        self,
        category: Optional[str] = None,
        days: int = 30
    ) -> Dict[str, Any]:
        """
        获取统计信息
        
        Args:
            category: 分类过滤
            days: 统计天数
            
        Returns:
            统计信息字典
        """
        start_time = (datetime.now() - timedelta(days=days)).isoformat()
        
        stats = {
            "total_reports": 0,
            "by_category": {},
            "by_status": {},
            "by_format": {},
            "total_size_bytes": 0,
            "avg_size_bytes": 0,
            "total_archived": 0,
            "date_range": {
                "start": start_time,
                "end": datetime.now().isoformat()
            },
            "metrics_summary": {}
        }
        
        filtered_reports = []
        
        for report in self._reports.values():
            if category and report.category != category:
                continue
            if report.created_at < start_time:
                continue
            
            filtered_reports.append(report)
            
            stats["total_reports"] += 1
            stats["by_category"][report.category] = stats["by_category"].get(report.category, 0) + 1
            stats["by_status"][report.status] = stats["by_status"].get(report.status, 0) + 1
            stats["by_format"][report.format] = stats["by_format"].get(report.format, 0) + 1
            stats["total_size_bytes"] += report.size_bytes
            
            if report.is_archived:
                stats["total_archived"] += 1
        
        if filtered_reports:
            stats["avg_size_bytes"] = stats["total_size_bytes"] / len(filtered_reports)
        
        return stats
    
    def cleanup_old_reports(
        self,
        days: int = 90,
        archive_before_delete: bool = True
    ) -> Dict[str, Any]:
        """
        清理旧报告
        
        Args:
            days: 保留天数
            archive_before_delete: 删除前是否归档
            
        Returns:
            清理结果字典
        """
        cutoff_time = (datetime.now() - timedelta(days=days)).isoformat()
        
        result = {
            "archived": [],
            "deleted": [],
            "errors": [],
            "timestamp": datetime.now().isoformat()
        }
        
        to_process = []
        
        for report_id, report in self._reports.items():
            if report.created_at < cutoff_time and not report.is_archived:
                to_process.append(report_id)
        
        if archive_before_delete and to_process:
            archive = self.archive_reports(to_process)
            if archive:
                result["archived"] = archive.report_ids
        
        for report_id in to_process:
            report = self._reports.get(report_id)
            
            if report and report.is_archived:
                try:
                    path = Path(report.file_path)
                    if path.exists():
                        path.unlink()
                    
                    with self._lock:
                        del self._reports[report_id]
                    
                    result["deleted"].append(report_id)
                except Exception as e:
                    result["errors"].append(f"{report_id}: {str(e)}")
        
        if result["deleted"]:
            self._save_index()
            self._update_query_engine()
        
        return result


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="报告版本管理器增强版 - Sanliu 技能"
    )
    
    parser.add_argument(
        '--base-path',
        type=str,
        default=None,
        help='基础路径（默认使用 PathConfigManager 自动检测）'
    )
    parser.add_argument(
        '--store',
        type=str,
        help='存储报告（文件路径）'
    )
    parser.add_argument(
        '--category',
        type=str,
        choices=[c.value for c in ReportCategory],
        help='报告分类'
    )
    parser.add_argument(
        '--list',
        action='store_true',
        help='列出报告'
    )
    parser.add_argument(
        '--query',
        type=str,
        help='查询报告（JSON格式查询条件）'
    )
    parser.add_argument(
        '--archive',
        type=str,
        nargs='+',
        help='归档报告（报告ID列表）'
    )
    parser.add_argument(
        '--list-archives',
        action='store_true',
        help='列出归档'
    )
    parser.add_argument(
        '--compare',
        type=str,
        nargs=2,
        help='对比报告（两个报告ID）'
    )
    parser.add_argument(
        '--stats',
        action='store_true',
        help='显示统计信息'
    )
    parser.add_argument(
        '--cleanup',
        type=int,
        metavar='DAYS',
        help='清理旧报告（保留天数）'
    )
    
    args = parser.parse_args()
    
    if args.base_path:
        base_path = Path(args.base_path).resolve()
        path_manager = PathConfigManager(auto_detect=False)
        path_manager._base_path = base_path
    else:
        path_manager = PathConfigManager(auto_detect=True)
        base_path = path_manager.get_base_path()
    
    manager = EnhancedReportVersionManager(base_path, path_manager=path_manager)
    
    if args.store:
        report_info = manager.store_report(
            args.store,
            category=args.category
        )
        print(json.dumps(asdict(report_info), indent=2, ensure_ascii=False))
    
    if args.list:
        reports = manager.list_reports(category=args.category)
        for report in reports:
            print(f"- [{report.report_id}] {report.name} ({report.category}) {report.created_at[:10]}")
    
    if args.query:
        try:
            query_data = json.loads(args.query)
            query = ReportQuery(**query_data)
            results = manager.query_reports(query)
            for report in results:
                print(f"- [{report.report_id}] {report.name}")
        except Exception as e:
            print(f"查询失败: {e}")
    
    if args.archive:
        archive = manager.archive_reports(args.archive)
        if archive:
            print(f"归档已创建: {archive.archive_id}")
            print(f"包含报告: {archive.report_count} 个")
        else:
            print("归档创建失败")
    
    if args.list_archives:
        archives = manager.archive_manager.list_archives()
        for archive in archives:
            print(f"- [{archive['archive_id']}] {archive['name']} ({archive['report_count']} reports)")
    
    if args.compare:
        comparison = manager.compare_reports(args.compare[0], args.compare[1])
        if comparison:
            print(json.dumps(asdict(comparison), indent=2, ensure_ascii=False))
        else:
            print("对比失败，报告不存在")
    
    if args.stats:
        stats = manager.get_statistics(category=args.category)
        print(json.dumps(stats, indent=2, ensure_ascii=False))
    
    if args.cleanup:
        result = manager.cleanup_old_reports(days=args.cleanup)
        print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
