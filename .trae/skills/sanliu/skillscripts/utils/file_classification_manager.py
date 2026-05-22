#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
文件归类管理器

功能：
1. 文档自动归类功能
   - 扫描docs/目录下所有文档文件
   - 根据文档类型自动分类（规范文档、设计文档、API文档、用户文档）
   - 根据版本号自动归类到对应版本目录
   - 支持自定义归类规则

2. 报告自动归类功能
   - 扫描docs/reports/目录下所有报告文件
   - 根据报告类型自动分类（测试报告、分析报告、审查报告）
   - 根据版本号和日期自动归类
   - 支持报告清理策略（保留最近N个版本）

3. 路径关系管理功能
   - 管理输入路径和输出路径的映射关系
   - 支持双模式路径配置（自迭代模式/指导其他项目模式）
   - 实现路径验证和修正
   - 生成路径配置报告

4. 归类报告生成功能
   - 生成JSON格式的归类报告
   - 生成Markdown格式的文件清单
   - 生成路径关系图

使用方法：
    from file_classification_manager import FileClassificationManager
    
    manager = FileClassificationManager(base_path="/path/to/project")
    
    # 文档归类
    result = manager.classify_documents()
    
    # 报告归类
    result = manager.classify_reports()
    
    # 生成报告
    manager.generate_classification_report()
"""

import json
import logging
import re
import shutil
import sys
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple, Set

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - [%(name)s] %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


class DocCategory(Enum):
    """文档类别枚举"""
    SPECIFICATION = "specification"
    DESIGN = "design"
    API = "api"
    USER = "user"
    CHANGELOG = "changelog"
    ARCHITECTURE = "architecture"
    UNKNOWN = "unknown"


class ReportCategory(Enum):
    """报告类别枚举"""
    TEST = "test"
    ANALYSIS = "analysis"
    REVIEW = "review"
    COVERAGE = "coverage"
    PERFORMANCE = "performance"
    UNKNOWN = "unknown"


class PathMode(Enum):
    """路径模式枚举"""
    SELF_ITERATION = "self_iteration"
    GUIDE_PROJECT = "guide_project"


@dataclass
class ClassificationRule:
    """归类规则数据类"""
    name: str
    pattern: str
    category: str
    priority: int = 0
    description: str = ""
    target_subdir: Optional[str] = None


@dataclass
class DocumentInfo:
    """文档信息数据类"""
    file_path: Path
    file_name: str
    category: DocCategory
    version: Optional[str]
    size_bytes: int
    created_at: str
    modified_at: str
    extension: str
    target_path: Optional[Path] = None
    classification_confidence: float = 0.0
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ReportInfo:
    """报告信息数据类"""
    file_path: Path
    file_name: str
    category: ReportCategory
    version: Optional[str]
    date: Optional[str]
    size_bytes: int
    created_at: str
    modified_at: str
    extension: str
    target_path: Optional[Path] = None
    classification_confidence: float = 0.0
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PathMapping:
    """路径映射数据类"""
    source_path: Path
    target_path: Path
    mapping_type: str
    created_at: str
    is_active: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ClassificationResult:
    """归类结果数据类"""
    total_files: int
    classified_files: int
    skipped_files: int
    error_files: int
    categories: Dict[str, int]
    details: List[Dict[str, Any]]
    execution_time: float
    timestamp: str


@dataclass
class CleanupPolicy:
    """清理策略数据类"""
    keep_versions: int = 5
    keep_days: int = 30
    keep_min_count: int = 3
    dry_run: bool = True


class FileClassificationError(Exception):
    """文件归类基础异常类"""
    
    def __init__(self, message: str, file_path: Optional[Path] = None):
        super().__init__(message)
        self.file_path = file_path
    
    def __str__(self) -> str:
        base_msg = super().__str__()
        if self.file_path:
            return f"{base_msg} (文件: {self.file_path})"
        return base_msg


class DocumentClassifier:
    """文档分类器"""
    
    DEFAULT_RULES: List[ClassificationRule] = [
        ClassificationRule(
            name="api_doc",
            pattern=r"(api|接口|API)",
            category=DocCategory.API.value,
            priority=10,
            description="API文档",
            target_subdir="api"
        ),
        ClassificationRule(
            name="design_doc",
            pattern=r"(设计|design|架构|architecture|方案)",
            category=DocCategory.DESIGN.value,
            priority=8,
            description="设计文档",
            target_subdir="design"
        ),
        ClassificationRule(
            name="spec_doc",
            pattern=r"(规范|spec|标准|standard|需求|requirement)",
            category=DocCategory.SPECIFICATION.value,
            priority=9,
            description="规范文档",
            target_subdir="specification"
        ),
        ClassificationRule(
            name="user_doc",
            pattern=r"(用户|user|手册|manual|指南|guide|使用说明)",
            category=DocCategory.USER.value,
            priority=7,
            description="用户文档",
            target_subdir="user"
        ),
        ClassificationRule(
            name="changelog_doc",
            pattern=r"(changelog|变更|更新日志|release)",
            category=DocCategory.CHANGELOG.value,
            priority=6,
            description="变更日志",
            target_subdir="changelog"
        ),
    ]
    
    VERSION_PATTERN = r'[vV]?(\d+\.\d+(?:\.\d+)?)'
    
    def __init__(self, custom_rules: Optional[List[ClassificationRule]] = None):
        self.rules = self.DEFAULT_RULES.copy()
        if custom_rules:
            self.rules.extend(custom_rules)
        self.rules.sort(key=lambda x: x.priority, reverse=True)
    
    def classify(self, file_path: Path) -> Tuple[DocCategory, float, Optional[str]]:
        """
        分类文档
        
        Args:
            file_path: 文档文件路径
            
        Returns:
            (文档类别, 置信度, 目标子目录) 元组
        """
        file_name = file_path.name
        file_stem = file_path.stem
        
        for rule in self.rules:
            if re.search(rule.pattern, file_name, re.IGNORECASE):
                return (
                    DocCategory(rule.category),
                    0.9,
                    rule.target_subdir
                )
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read(2000)
            
            for rule in self.rules:
                if re.search(rule.pattern, content, re.IGNORECASE):
                    return (
                        DocCategory(rule.category),
                        0.7,
                        rule.target_subdir
                    )
        except (UnicodeDecodeError, IOError):
            pass
        
        return (DocCategory.UNKNOWN, 0.3, None)
    
    def extract_version(self, file_path: Path) -> Optional[str]:
        """
        从文件名或路径中提取版本号
        
        Args:
            file_path: 文件路径
            
        Returns:
            版本号字符串或None
        """
        patterns = [
            r'[vV](\d+\.\d+(?:\.\d+)?)',
            r'(\d+\.\d+(?:\.\d+)?)[\._-]',
            r'version[\._-]?(\d+\.\d+(?:\.\d+)?)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, file_path.name)
            if match:
                return f"v{match.group(1)}"
        
        for part in file_path.parts:
            match = re.search(r'[vV](\d+\.\d+(?:\.\d+)?)', part)
            if match:
                return f"v{match.group(1)}"
        
        return None
    
    def get_document_info(self, file_path: Path) -> DocumentInfo:
        """
        获取文档完整信息
        
        Args:
            file_path: 文档文件路径
            
        Returns:
            DocumentInfo 对象
        """
        stat = file_path.stat()
        category, confidence, target_subdir = self.classify(file_path)
        version = self.extract_version(file_path)
        
        return DocumentInfo(
            file_path=file_path,
            file_name=file_path.name,
            category=category,
            version=version,
            size_bytes=stat.st_size,
            created_at=datetime.fromtimestamp(stat.st_ctime).isoformat(),
            modified_at=datetime.fromtimestamp(stat.st_mtime).isoformat(),
            extension=file_path.suffix.lower(),
            classification_confidence=confidence
        )


class ReportClassifier:
    """报告分类器"""
    
    DEFAULT_RULES: List[ClassificationRule] = [
        ClassificationRule(
            name="test_report",
            pattern=r"(test|测试|单元|集成|e2e)",
            category=ReportCategory.TEST.value,
            priority=10,
            description="测试报告",
            target_subdir="test"
        ),
        ClassificationRule(
            name="analysis_report",
            pattern=r"(analysis|分析|统计|statistics)",
            category=ReportCategory.ANALYSIS.value,
            priority=9,
            description="分析报告",
            target_subdir="analysis"
        ),
        ClassificationRule(
            name="review_report",
            pattern=r"(review|审查|code_review|评审)",
            category=ReportCategory.REVIEW.value,
            priority=8,
            description="审查报告",
            target_subdir="review"
        ),
        ClassificationRule(
            name="coverage_report",
            pattern=r"(coverage|覆盖|cov)",
            category=ReportCategory.COVERAGE.value,
            priority=7,
            description="覆盖率报告",
            target_subdir="coverage"
        ),
        ClassificationRule(
            name="performance_report",
            pattern=r"(performance|性能|benchmark|基准)",
            category=ReportCategory.PERFORMANCE.value,
            priority=6,
            description="性能报告",
            target_subdir="performance"
        ),
    ]
    
    DATE_PATTERN = r'(\d{4}[-_]?\d{2}[-_]?\d{2})'
    
    def __init__(self, custom_rules: Optional[List[ClassificationRule]] = None):
        self.rules = self.DEFAULT_RULES.copy()
        if custom_rules:
            self.rules.extend(custom_rules)
        self.rules.sort(key=lambda x: x.priority, reverse=True)
    
    def classify(self, file_path: Path) -> Tuple[ReportCategory, float, Optional[str]]:
        """
        分类报告
        
        Args:
            file_path: 报告文件路径
            
        Returns:
            (报告类别, 置信度, 目标子目录) 元组
        """
        file_name = file_path.name
        
        for rule in self.rules:
            if re.search(rule.pattern, file_name, re.IGNORECASE):
                return (
                    ReportCategory(rule.category),
                    0.9,
                    rule.target_subdir
                )
        
        return (ReportCategory.UNKNOWN, 0.3, None)
    
    def extract_version(self, file_path: Path) -> Optional[str]:
        """从文件名或路径中提取版本号"""
        patterns = [
            r'[vV](\d+\.\d+(?:\.\d+)?)',
            r'(\d+\.\d+(?:\.\d+)?)[\._-]',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, file_path.name)
            if match:
                return f"v{match.group(1)}"
        
        return None
    
    def extract_date(self, file_path: Path) -> Optional[str]:
        """从文件名中提取日期"""
        match = re.search(self.DATE_PATTERN, file_path.name)
        if match:
            date_str = match.group(1)
            date_str = date_str.replace('_', '-').replace(' ', '-')
            try:
                dt = datetime.strptime(date_str, '%Y-%m-%d')
                return dt.strftime('%Y-%m-%d')
            except ValueError:
                pass
        
        stat = file_path.stat()
        return datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d')
    
    def get_report_info(self, file_path: Path) -> ReportInfo:
        """获取报告完整信息"""
        stat = file_path.stat()
        category, confidence, target_subdir = self.classify(file_path)
        version = self.extract_version(file_path)
        date = self.extract_date(file_path)
        
        return ReportInfo(
            file_path=file_path,
            file_name=file_path.name,
            category=category,
            version=version,
            date=date,
            size_bytes=stat.st_size,
            created_at=datetime.fromtimestamp(stat.st_ctime).isoformat(),
            modified_at=datetime.fromtimestamp(stat.st_mtime).isoformat(),
            extension=file_path.suffix.lower(),
            classification_confidence=confidence
        )


class PathRelationshipManager:
    """路径关系管理器"""
    
    def __init__(self, base_path: Path, mode: PathMode = PathMode.SELF_ITERATION):
        self.base_path = base_path
        self.mode = mode
        self.mappings: List[PathMapping] = []
        self._config_file = base_path / "path_mappings.json"
        self._load_mappings()
    
    def _load_mappings(self) -> None:
        """加载路径映射配置"""
        if self._config_file.exists():
            try:
                with open(self._config_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                self.mappings = [
                    PathMapping(
                        source_path=Path(m['source_path']),
                        target_path=Path(m['target_path']),
                        mapping_type=m['mapping_type'],
                        created_at=m['created_at'],
                        is_active=m.get('is_active', True),
                        metadata=m.get('metadata', {})
                    )
                    for m in data.get('mappings', [])
                ]
            except Exception as e:
                logger.warning(f"加载路径映射配置失败: {e}")
    
    def _save_mappings(self) -> None:
        """保存路径映射配置"""
        try:
            data = {
                "base_path": str(self.base_path),
                "mode": self.mode.value,
                "mappings": [asdict(m) for m in self.mappings],
                "updated_at": datetime.now().isoformat()
            }
            for m in data['mappings']:
                m['source_path'] = str(m['source_path'])
                m['target_path'] = str(m['target_path'])
            
            with open(self._config_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"保存路径映射配置失败: {e}")
    
    def add_mapping(
        self,
        source_path: Path,
        target_path: Path,
        mapping_type: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """添加路径映射"""
        mapping = PathMapping(
            source_path=source_path,
            target_path=target_path,
            mapping_type=mapping_type,
            created_at=datetime.now().isoformat(),
            metadata=metadata or {}
        )
        self.mappings.append(mapping)
        self._save_mappings()
        logger.info(f"添加路径映射: {source_path} -> {target_path}")
    
    def get_mapping(self, source_path: Path) -> Optional[PathMapping]:
        """获取路径映射"""
        for mapping in self.mappings:
            if mapping.source_path == source_path and mapping.is_active:
                return mapping
        return None
    
    def validate_path(self, path: Path, must_exist: bool = False) -> Tuple[bool, Optional[str]]:
        """验证路径"""
        try:
            resolved = path.resolve()
            if must_exist and not resolved.exists():
                return False, f"路径不存在: {resolved}"
            return True, None
        except Exception as e:
            return False, f"路径验证失败: {e}"
    
    def fix_path(self, path: Path) -> Path:
        """修正路径"""
        if not path.is_absolute():
            path = self.base_path / path
        return path.resolve()
    
    def get_all_paths(self) -> Dict[str, Path]:
        """获取所有路径配置"""
        return {
            "base": self.base_path,
            "docs": self.base_path / "docs",
            "docs_libs": self.base_path / "docs" / "libs",
            "docs_reports": self.base_path / "docs" / "reports",
            "tests": self.base_path / "tests",
        }
    
    def generate_path_report(self) -> Dict[str, Any]:
        """生成路径配置报告"""
        paths = self.get_all_paths()
        path_status = {}
        
        for name, path in paths.items():
            valid, error = self.validate_path(path)
            path_status[name] = {
                "path": str(path),
                "exists": path.exists(),
                "valid": valid,
                "error": error
            }
        
        return {
            "base_path": str(self.base_path),
            "mode": self.mode.value,
            "paths": path_status,
            "mappings_count": len(self.mappings),
            "active_mappings": len([m for m in self.mappings if m.is_active]),
            "generated_at": datetime.now().isoformat()
        }


class FileClassificationManager:
    """文件归类管理器主类"""
    
    SUPPORTED_DOC_EXTENSIONS = {'.md', '.txt', '.rst', '.pdf', '.doc', '.docx', '.html', '.htm'}
    SUPPORTED_REPORT_EXTENSIONS = {'.json', '.xml', '.html', '.htm', '.md', '.txt', '.csv'}
    
    def __init__(
        self,
        base_path: Optional[str] = None,
        mode: PathMode = PathMode.SELF_ITERATION,
        custom_doc_rules: Optional[List[ClassificationRule]] = None,
        custom_report_rules: Optional[List[ClassificationRule]] = None
    ):
        if base_path:
            self.base_path = Path(base_path)
        else:
            self.base_path = Path.cwd()
        
        self.mode = mode
        self.doc_classifier = DocumentClassifier(custom_doc_rules)
        self.report_classifier = ReportClassifier(custom_report_rules)
        self.path_manager = PathRelationshipManager(self.base_path, mode)
        
        self.docs_dir = self.base_path / "docs"
        self.libs_dir = self.docs_dir / "libs"
        self.reports_dir = self.docs_dir / "reports"
        
        self._ensure_directories()
    
    def _ensure_directories(self) -> None:
        """确保必要目录存在"""
        directories = [
            self.docs_dir,
            self.libs_dir,
            self.reports_dir,
        ]
        
        for dir_path in directories:
            dir_path.mkdir(parents=True, exist_ok=True)
    
    def scan_documents(self, scan_path: Optional[Path] = None) -> List[DocumentInfo]:
        """
        扫描文档文件
        
        Args:
            scan_path: 扫描路径，默认为docs目录
            
        Returns:
            文档信息列表
        """
        scan_path = scan_path or self.docs_dir
        documents: List[DocumentInfo] = []
        
        if not scan_path.exists():
            logger.warning(f"扫描路径不存在: {scan_path}")
            return documents
        
        for file_path in scan_path.rglob('*'):
            if file_path.is_file() and file_path.suffix.lower() in self.SUPPORTED_DOC_EXTENSIONS:
                try:
                    doc_info = self.doc_classifier.get_document_info(file_path)
                    documents.append(doc_info)
                except Exception as e:
                    logger.warning(f"处理文件失败 {file_path}: {e}")
        
        logger.info(f"扫描到 {len(documents)} 个文档文件")
        return documents
    
    def scan_reports(self, scan_path: Optional[Path] = None) -> List[ReportInfo]:
        """
        扫描报告文件
        
        Args:
            scan_path: 扫描路径，默认为reports目录
            
        Returns:
            报告信息列表
        """
        scan_path = scan_path or self.reports_dir
        reports: List[ReportInfo] = []
        
        if not scan_path.exists():
            logger.warning(f"扫描路径不存在: {scan_path}")
            return reports
        
        for file_path in scan_path.rglob('*'):
            if file_path.is_file() and file_path.suffix.lower() in self.SUPPORTED_REPORT_EXTENSIONS:
                try:
                    report_info = self.report_classifier.get_report_info(file_path)
                    reports.append(report_info)
                except Exception as e:
                    logger.warning(f"处理文件失败 {file_path}: {e}")
        
        logger.info(f"扫描到 {len(reports)} 个报告文件")
        return reports
    
    def classify_documents(
        self,
        documents: Optional[List[DocumentInfo]] = None,
        dry_run: bool = True,
        version: Optional[str] = None
    ) -> ClassificationResult:
        """
        归类文档
        
        Args:
            documents: 文档列表，为None时自动扫描
            dry_run: 是否为模拟运行
            version: 目标版本
            
        Returns:
            归类结果
        """
        start_time = datetime.now()
        
        if documents is None:
            documents = self.scan_documents()
        
        total_files = len(documents)
        classified_files = 0
        skipped_files = 0
        error_files = 0
        categories: Dict[str, int] = {}
        details: List[Dict[str, Any]] = []
        
        for doc in documents:
            try:
                if doc.category == DocCategory.UNKNOWN:
                    skipped_files += 1
                    continue
                
                target_dir = self._get_document_target_dir(doc, version)
                target_path = target_dir / doc.file_name
                
                doc.target_path = target_path
                
                if not dry_run:
                    target_dir.mkdir(parents=True, exist_ok=True)
                    if doc.file_path != target_path:
                        shutil.copy2(str(doc.file_path), str(target_path))
                        self.path_manager.add_mapping(
                            doc.file_path,
                            target_path,
                            "document_classification",
                            {"category": doc.category.value, "version": doc.version}
                        )
                
                category_name = doc.category.value
                categories[category_name] = categories.get(category_name, 0) + 1
                classified_files += 1
                
                details.append({
                    "source": str(doc.file_path),
                    "target": str(target_path),
                    "category": category_name,
                    "version": doc.version,
                    "confidence": doc.classification_confidence,
                    "action": "copied" if not dry_run else "planned"
                })
                
            except Exception as e:
                error_files += 1
                logger.error(f"归类文档失败 {doc.file_path}: {e}")
                details.append({
                    "source": str(doc.file_path),
                    "error": str(e),
                    "action": "error"
                })
        
        execution_time = (datetime.now() - start_time).total_seconds()
        
        return ClassificationResult(
            total_files=total_files,
            classified_files=classified_files,
            skipped_files=skipped_files,
            error_files=error_files,
            categories=categories,
            details=details,
            execution_time=execution_time,
            timestamp=datetime.now().isoformat()
        )
    
    def classify_reports(
        self,
        reports: Optional[List[ReportInfo]] = None,
        dry_run: bool = True,
        version: Optional[str] = None
    ) -> ClassificationResult:
        """
        归类报告
        
        Args:
            reports: 报告列表，为None时自动扫描
            dry_run: 是否为模拟运行
            version: 目标版本
            
        Returns:
            归类结果
        """
        start_time = datetime.now()
        
        if reports is None:
            reports = self.scan_reports()
        
        total_files = len(reports)
        classified_files = 0
        skipped_files = 0
        error_files = 0
        categories: Dict[str, int] = {}
        details: List[Dict[str, Any]] = []
        
        for report in reports:
            try:
                if report.category == ReportCategory.UNKNOWN:
                    skipped_files += 1
                    continue
                
                target_dir = self._get_report_target_dir(report, version)
                target_path = target_dir / report.file_name
                
                report.target_path = target_path
                
                if not dry_run:
                    target_dir.mkdir(parents=True, exist_ok=True)
                    if report.file_path != target_path:
                        shutil.copy2(str(report.file_path), str(target_path))
                        self.path_manager.add_mapping(
                            report.file_path,
                            target_path,
                            "report_classification",
                            {
                                "category": report.category.value,
                                "version": report.version,
                                "date": report.date
                            }
                        )
                
                category_name = report.category.value
                categories[category_name] = categories.get(category_name, 0) + 1
                classified_files += 1
                
                details.append({
                    "source": str(report.file_path),
                    "target": str(target_path),
                    "category": category_name,
                    "version": report.version,
                    "date": report.date,
                    "confidence": report.classification_confidence,
                    "action": "copied" if not dry_run else "planned"
                })
                
            except Exception as e:
                error_files += 1
                logger.error(f"归类报告失败 {report.file_path}: {e}")
                details.append({
                    "source": str(report.file_path),
                    "error": str(e),
                    "action": "error"
                })
        
        execution_time = (datetime.now() - start_time).total_seconds()
        
        return ClassificationResult(
            total_files=total_files,
            classified_files=classified_files,
            skipped_files=skipped_files,
            error_files=error_files,
            categories=categories,
            details=details,
            execution_time=execution_time,
            timestamp=datetime.now().isoformat()
        )
    
    def _get_document_target_dir(self, doc: DocumentInfo, version: Optional[str] = None) -> Path:
        """获取文档目标目录"""
        version_str = version or doc.version or "unversioned"
        
        _, _, target_subdir = self.doc_classifier.classify(doc.file_path)
        
        if target_subdir:
            return self.libs_dir / version_str / target_subdir
        else:
            return self.libs_dir / version_str / doc.category.value
    
    def _get_report_target_dir(self, report: ReportInfo, version: Optional[str] = None) -> Path:
        """获取报告目标目录"""
        version_str = version or report.version or "unversioned"
        date_str = report.date or "undated"
        
        _, _, target_subdir = self.report_classifier.classify(report.file_path)
        
        if target_subdir:
            return self.reports_dir / version_str / target_subdir / date_str
        else:
            return self.reports_dir / version_str / report.category.value / date_str
    
    def cleanup_old_reports(
        self,
        policy: Optional[CleanupPolicy] = None,
        dry_run: bool = True
    ) -> Dict[str, Any]:
        """
        清理旧报告
        
        Args:
            policy: 清理策略
            dry_run: 是否为模拟运行
            
        Returns:
            清理结果
        """
        policy = policy or CleanupPolicy()
        result = {
            "policy": asdict(policy),
            "deleted_files": [],
            "kept_files": [],
            "errors": [],
            "timestamp": datetime.now().isoformat()
        }
        
        if not self.reports_dir.exists():
            return result
        
        version_dirs = sorted(
            [d for d in self.reports_dir.iterdir() if d.is_dir()],
            key=lambda x: x.name,
            reverse=True
        )
        
        for i, version_dir in enumerate(version_dirs):
            if i < policy.keep_versions:
                result["kept_files"].extend(
                    [str(f) for f in version_dir.rglob('*') if f.is_file()]
                )
                continue
            
            for file_path in version_dir.rglob('*'):
                if file_path.is_file():
                    try:
                        stat = file_path.stat()
                        file_age = (datetime.now() - datetime.fromtimestamp(stat.st_mtime)).days
                        
                        if file_age > policy.keep_days:
                            if not dry_run:
                                file_path.unlink()
                            result["deleted_files"].append(str(file_path))
                        else:
                            result["kept_files"].append(str(file_path))
                    except Exception as e:
                        result["errors"].append({
                            "file": str(file_path),
                            "error": str(e)
                        })
        
        logger.info(f"清理完成: 删除 {len(result['deleted_files'])} 个文件")
        return result
    
    def generate_classification_report(
        self,
        output_format: str = "json",
        output_path: Optional[Path] = None
    ) -> str:
        """
        生成归类报告
        
        Args:
            output_format: 输出格式 (json/markdown)
            output_path: 输出路径
            
        Returns:
            报告内容
        """
        documents = self.scan_documents()
        reports = self.scan_reports()
        path_report = self.path_manager.generate_path_report()
        
        doc_by_category: Dict[str, List[DocumentInfo]] = {}
        for doc in documents:
            category = doc.category.value
            if category not in doc_by_category:
                doc_by_category[category] = []
            doc_by_category[category].append(doc)
        
        report_by_category: Dict[str, List[ReportInfo]] = {}
        for report in reports:
            category = report.category.value
            if category not in report_by_category:
                report_by_category[category] = []
            report_by_category[category].append(report)
        
        if output_format == "json":
            report_content = self._generate_json_report(
                documents, reports, doc_by_category, report_by_category, path_report
            )
        else:
            report_content = self._generate_markdown_report(
                documents, reports, doc_by_category, report_by_category, path_report
            )
        
        if output_path:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(report_content)
            logger.info(f"报告已保存: {output_path}")
        
        return report_content
    
    def _generate_json_report(
        self,
        documents: List[DocumentInfo],
        reports: List[ReportInfo],
        doc_by_category: Dict[str, List[DocumentInfo]],
        report_by_category: Dict[str, List[ReportInfo]],
        path_report: Dict[str, Any]
    ) -> str:
        """生成JSON格式报告"""
        report_data = {
            "summary": {
                "total_documents": len(documents),
                "total_reports": len(reports),
                "document_categories": {k: len(v) for k, v in doc_by_category.items()},
                "report_categories": {k: len(v) for k, v in report_by_category.items()},
                "generated_at": datetime.now().isoformat()
            },
            "documents": {
                category: [
                    {
                        "file_name": doc.file_name,
                        "file_path": str(doc.file_path),
                        "version": doc.version,
                        "size_bytes": doc.size_bytes,
                        "confidence": doc.classification_confidence
                    }
                    for doc in docs
                ]
                for category, docs in doc_by_category.items()
            },
            "reports": {
                category: [
                    {
                        "file_name": report.file_name,
                        "file_path": str(report.file_path),
                        "version": report.version,
                        "date": report.date,
                        "size_bytes": report.size_bytes,
                        "confidence": report.classification_confidence
                    }
                    for report in reps
                ]
                for category, reps in report_by_category.items()
            },
            "path_configuration": path_report
        }
        
        return json.dumps(report_data, indent=2, ensure_ascii=False)
    
    def _generate_markdown_report(
        self,
        documents: List[DocumentInfo],
        reports: List[ReportInfo],
        doc_by_category: Dict[str, List[DocumentInfo]],
        report_by_category: Dict[str, List[ReportInfo]],
        path_report: Dict[str, Any]
    ) -> str:
        """生成Markdown格式报告"""
        lines = [
            "# 文件归类报告",
            "",
            f"**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "## 概览",
            "",
            f"- 文档总数: {len(documents)}",
            f"- 报告总数: {len(reports)}",
            "",
            "## 文档分类",
            "",
        ]
        
        for category, docs in doc_by_category.items():
            lines.append(f"### {category} ({len(docs)} 个文件)")
            lines.append("")
            lines.append("| 文件名 | 版本 | 大小 | 置信度 |")
            lines.append("|--------|------|------|--------|")
            for doc in docs:
                size_kb = doc.size_bytes / 1024
                lines.append(
                    f"| {doc.file_name} | {doc.version or '-'} | {size_kb:.1f}KB | {doc.classification_confidence:.0%} |"
                )
            lines.append("")
        
        lines.append("## 报告分类")
        lines.append("")
        
        for category, reps in report_by_category.items():
            lines.append(f"### {category} ({len(reps)} 个文件)")
            lines.append("")
            lines.append("| 文件名 | 版本 | 日期 | 大小 | 置信度 |")
            lines.append("|--------|------|------|------|--------|")
            for report in reps:
                size_kb = report.size_bytes / 1024
                lines.append(
                    f"| {report.file_name} | {report.version or '-'} | {report.date or '-'} | {size_kb:.1f}KB | {report.classification_confidence:.0%} |"
                )
            lines.append("")
        
        lines.append("## 路径配置")
        lines.append("")
        lines.append(f"- 基础路径: `{path_report['base_path']}`")
        lines.append(f"- 运行模式: {path_report['mode']}")
        lines.append(f"- 活跃映射: {path_report['active_mappings']}")
        lines.append("")
        
        lines.append("### 路径状态")
        lines.append("")
        lines.append("| 路径名称 | 路径 | 存在 | 有效 |")
        lines.append("|----------|------|------|------|")
        for name, info in path_report['paths'].items():
            exists = "✓" if info['exists'] else "✗"
            valid = "✓" if info['valid'] else "✗"
            lines.append(f"| {name} | `{info['path']}` | {exists} | {valid} |")
        
        return "\n".join(lines)
    
    def generate_file_manifest(
        self,
        output_path: Optional[Path] = None
    ) -> Dict[str, Any]:
        """
        生成文件清单
        
        Args:
            output_path: 输出路径
            
        Returns:
            文件清单数据
        """
        documents = self.scan_documents()
        reports = self.scan_reports()
        
        manifest = {
            "generated_at": datetime.now().isoformat(),
            "base_path": str(self.base_path),
            "documents": [
                {
                    "name": doc.file_name,
                    "path": str(doc.file_path.relative_to(self.base_path)),
                    "category": doc.category.value,
                    "version": doc.version,
                    "size": doc.size_bytes,
                    "modified": doc.modified_at
                }
                for doc in documents
            ],
            "reports": [
                {
                    "name": report.file_name,
                    "path": str(report.file_path.relative_to(self.base_path)),
                    "category": report.category.value,
                    "version": report.version,
                    "date": report.date,
                    "size": report.size_bytes,
                    "modified": report.modified_at
                }
                for report in reports
            ],
            "statistics": {
                "total_documents": len(documents),
                "total_reports": len(reports),
                "total_size": sum(d.size_bytes for d in documents) + sum(r.size_bytes for r in reports)
            }
        }
        
        if output_path:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(manifest, f, indent=2, ensure_ascii=False)
            logger.info(f"文件清单已保存: {output_path}")
        
        return manifest
    
    def generate_path_diagram(
        self,
        output_path: Optional[Path] = None
    ) -> str:
        """
        生成路径关系图
        
        Args:
            output_path: 输出路径
            
        Returns:
            Mermaid格式的关系图
        """
        paths = self.path_manager.get_all_paths()
        mappings = self.path_manager.mappings
        
        lines = [
            "```mermaid",
            "graph TD",
            f"    BASE[{self.base_path.name}]",
        ]
        
        node_names = {
            "base": "BASE",
            "docs": "DOCS",
            "docs_libs": "LIBS",
            "docs_reports": "REPORTS",
            "tests": "TESTS",
        }
        
        for name, path in paths.items():
            if name == "base":
                continue
            node_name = node_names.get(name, name.upper())
            lines.append(f"    {node_name}[{path.name}]")
            lines.append(f"    BASE --> {node_name}")
        
        for i, mapping in enumerate(mappings[:10]):
            source_name = mapping.source_path.name
            target_name = mapping.target_path.name
            lines.append(f"    M{i}[{source_name}]")
            lines.append(f"    M{i} -->|{mapping.mapping_type}| T{i}[{target_name}]")
        
        lines.append("```")
        
        diagram = "\n".join(lines)
        
        if output_path:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(diagram)
            logger.info(f"路径关系图已保存: {output_path}")
        
        return diagram
    
    def add_custom_doc_rule(
        self,
        name: str,
        pattern: str,
        category: DocCategory,
        priority: int = 0,
        target_subdir: Optional[str] = None
    ) -> None:
        """添加自定义文档归类规则"""
        rule = ClassificationRule(
            name=name,
            pattern=pattern,
            category=category.value,
            priority=priority,
            target_subdir=target_subdir
        )
        self.doc_classifier.rules.append(rule)
        self.doc_classifier.rules.sort(key=lambda x: x.priority, reverse=True)
        logger.info(f"添加自定义文档归类规则: {name}")
    
    def add_custom_report_rule(
        self,
        name: str,
        pattern: str,
        category: ReportCategory,
        priority: int = 0,
        target_subdir: Optional[str] = None
    ) -> None:
        """添加自定义报告归类规则"""
        rule = ClassificationRule(
            name=name,
            pattern=pattern,
            category=category.value,
            priority=priority,
            target_subdir=target_subdir
        )
        self.report_classifier.rules.append(rule)
        self.report_classifier.rules.sort(key=lambda x: x.priority, reverse=True)
        logger.info(f"添加自定义报告归类规则: {name}")


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="文件归类管理器",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        '--base-path',
        type=str,
        help='基础路径'
    )
    parser.add_argument(
        '--mode',
        choices=['self_iteration', 'guide_project'],
        default='self_iteration',
        help='运行模式'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='模拟运行，不实际移动文件'
    )
    
    subparsers = parser.add_subparsers(dest='command', help='可用命令')
    
    parser_scan_docs = subparsers.add_parser('scan-docs', help='扫描文档')
    parser_scan_docs.add_argument('--output', type=str, help='输出文件路径')
    
    parser_scan_reports = subparsers.add_parser('scan-reports', help='扫描报告')
    parser_scan_reports.add_argument('--output', type=str, help='输出文件路径')
    
    parser_classify_docs = subparsers.add_parser('classify-docs', help='归类文档')
    parser_classify_docs.add_argument('--version', type=str, help='目标版本')
    parser_classify_docs.add_argument('--output', type=str, help='输出报告路径')
    
    parser_classify_reports = subparsers.add_parser('classify-reports', help='归类报告')
    parser_classify_reports.add_argument('--version', type=str, help='目标版本')
    parser_classify_reports.add_argument('--output', type=str, help='输出报告路径')
    
    parser_cleanup = subparsers.add_parser('cleanup', help='清理旧报告')
    parser_cleanup.add_argument('--keep-versions', type=int, default=5, help='保留版本数')
    parser_cleanup.add_argument('--keep-days', type=int, default=30, help='保留天数')
    
    parser_report = subparsers.add_parser('report', help='生成归类报告')
    parser_report.add_argument('--format', choices=['json', 'markdown'], default='json', help='输出格式')
    parser_report.add_argument('--output', type=str, help='输出文件路径')
    
    parser_manifest = subparsers.add_parser('manifest', help='生成文件清单')
    parser_manifest.add_argument('--output', type=str, help='输出文件路径')
    
    parser_diagram = subparsers.add_parser('diagram', help='生成路径关系图')
    parser_diagram.add_argument('--output', type=str, help='输出文件路径')
    
    parser_path_info = subparsers.add_parser('path-info', help='显示路径信息')
    
    args = parser.parse_args()
    
    mode = PathMode(args.mode)
    manager = FileClassificationManager(
        base_path=args.base_path,
        mode=mode
    )
    
    if args.command == 'scan-docs':
        documents = manager.scan_documents()
        print(f"扫描到 {len(documents)} 个文档文件")
        for doc in documents[:20]:
            print(f"  [{doc.category.value}] {doc.file_name}")
        if len(documents) > 20:
            print(f"  ... 还有 {len(documents) - 20} 个文件")
        
        if args.output:
            data = [asdict(d) for d in documents]
            for d in data:
                d['file_path'] = str(d['file_path'])
                d['target_path'] = str(d['target_path']) if d['target_path'] else None
            with open(args.output, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
    
    elif args.command == 'scan-reports':
        reports = manager.scan_reports()
        print(f"扫描到 {len(reports)} 个报告文件")
        for report in reports[:20]:
            print(f"  [{report.category.value}] {report.file_name}")
        if len(reports) > 20:
            print(f"  ... 还有 {len(reports) - 20} 个文件")
        
        if args.output:
            data = [asdict(r) for r in reports]
            for d in data:
                d['file_path'] = str(d['file_path'])
                d['target_path'] = str(d['target_path']) if d['target_path'] else None
            with open(args.output, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
    
    elif args.command == 'classify-docs':
        result = manager.classify_documents(
            dry_run=args.dry_run,
            version=args.version
        )
        print(f"文档归类完成:")
        print(f"  总文件数: {result.total_files}")
        print(f"  已归类: {result.classified_files}")
        print(f"  已跳过: {result.skipped_files}")
        print(f"  错误: {result.error_files}")
        print(f"  执行时间: {result.execution_time:.2f}s")
        print(f"  分类统计:")
        for category, count in result.categories.items():
            print(f"    {category}: {count}")
        
        if args.output:
            with open(args.output, 'w', encoding='utf-8') as f:
                json.dump(asdict(result), f, indent=2, ensure_ascii=False)
    
    elif args.command == 'classify-reports':
        result = manager.classify_reports(
            dry_run=args.dry_run,
            version=args.version
        )
        print(f"报告归类完成:")
        print(f"  总文件数: {result.total_files}")
        print(f"  已归类: {result.classified_files}")
        print(f"  已跳过: {result.skipped_files}")
        print(f"  错误: {result.error_files}")
        print(f"  执行时间: {result.execution_time:.2f}s")
        print(f"  分类统计:")
        for category, count in result.categories.items():
            print(f"    {category}: {count}")
        
        if args.output:
            with open(args.output, 'w', encoding='utf-8') as f:
                json.dump(asdict(result), f, indent=2, ensure_ascii=False)
    
    elif args.command == 'cleanup':
        policy = CleanupPolicy(
            keep_versions=args.keep_versions,
            keep_days=args.keep_days,
            dry_run=args.dry_run
        )
        result = manager.cleanup_old_reports(policy=policy, dry_run=args.dry_run)
        print(f"清理完成:")
        print(f"  删除文件: {len(result['deleted_files'])}")
        print(f"  保留文件: {len(result['kept_files'])}")
        print(f"  错误: {len(result['errors'])}")
    
    elif args.command == 'report':
        output_path = Path(args.output) if args.output else None
        report = manager.generate_classification_report(
            output_format=args.format,
            output_path=output_path
        )
        if not output_path:
            print(report)
    
    elif args.command == 'manifest':
        output_path = Path(args.output) if args.output else None
        manifest = manager.generate_file_manifest(output_path=output_path)
        if not output_path:
            print(json.dumps(manifest, indent=2, ensure_ascii=False))
    
    elif args.command == 'diagram':
        output_path = Path(args.output) if args.output else None
        diagram = manager.generate_path_diagram(output_path=output_path)
        if not output_path:
            print(diagram)
    
    elif args.command == 'path-info':
        report = manager.path_manager.generate_path_report()
        print(json.dumps(report, indent=2, ensure_ascii=False))
    
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
