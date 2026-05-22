#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
文档版本管理器
支持文档版本创建、查询、归档、差异对比、完整性验证等功能
增强功能：版本分支管理、流程分类存储、历史版本保留与差异对比
"""

import os
import json
import shutil
import argparse
import hashlib
import difflib
import re
import unittest
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple, Set
from dataclasses import dataclass, asdict, field
from enum import Enum
from copy import deepcopy

from skillscripts.core.path_config_center import get_path_config


class DocType(Enum):
    """文档类型枚举"""
    API = "api"
    ARCHITECTURE = "architecture"
    TEST_REPORT = "test_report"
    CHANGELOG = "changelog"


class WorkflowStage(Enum):
    """工作流程阶段枚举"""
    DEPLOYMENT = "deployment"
    DESIGN = "design"
    IMPLEMENTATION = "implementation"
    REQUIREMENTS = "requirements"
    TESTING = "testing"


class VersionStatus(Enum):
    """版本状态枚举"""
    DRAFT = "draft"
    RELEASED = "released"
    DEPRECATED = "deprecated"
    ARCHIVED = "archived"


class VersionRelation(Enum):
    """版本关系类型枚举"""
    PARENT = "parent"
    BRANCH = "branch"
    MERGE = "merge"
    SUCCESSOR = "successor"


@dataclass
class VersionNumber:
    """版本号数据类，支持语义化版本控制"""
    major: int
    minor: int
    patch: int
    prerelease: Optional[str] = None
    
    @classmethod
    def parse(cls, version_str: str) -> Optional['VersionNumber']:
        """解析版本字符串为VersionNumber对象，支持分支版本格式如 v1.0.0-branch-name"""
        pattern = r'^v?(\d+)\.(\d+)\.(\d+)(?:-([a-zA-Z0-9_-]+))?$'
        match = re.match(pattern, version_str)
        if not match:
            return None
        return cls(
            major=int(match.group(1)),
            minor=int(match.group(2)),
            patch=int(match.group(3)),
            prerelease=match.group(4)
        )
    
    def __str__(self) -> str:
        base = f"v{self.major}.{self.minor}.{self.patch}"
        if self.prerelease:
            base += f"-{self.prerelease}"
        return base
    
    def __lt__(self, other: 'VersionNumber') -> bool:
        if (self.major, self.minor, self.patch) != (other.major, other.minor, other.patch):
            return (self.major, self.minor, self.patch) < (other.major, other.minor, other.patch)
        if self.prerelease is None and other.prerelease is None:
            return False
        if self.prerelease is None:
            return False
        if other.prerelease is None:
            return True
        return self.prerelease < other.prerelease
    
    def __le__(self, other: 'VersionNumber') -> bool:
        return self == other or self < other
    
    def __gt__(self, other: 'VersionNumber') -> bool:
        return not self <= other
    
    def __ge__(self, other: 'VersionNumber') -> bool:
        return not self < other
    
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, VersionNumber):
            return False
        return (self.major, self.minor, self.patch, self.prerelease) == \
               (other.major, other.minor, other.patch, other.prerelease)
    
    def __hash__(self) -> int:
        return hash((self.major, self.minor, self.patch, self.prerelease))
    
    def bump_major(self) -> 'VersionNumber':
        """递增主版本号"""
        return VersionNumber(self.major + 1, 0, 0)
    
    def bump_minor(self) -> 'VersionNumber':
        """递增次版本号"""
        return VersionNumber(self.major, self.minor + 1, 0)
    
    def bump_patch(self) -> 'VersionNumber':
        """递增补丁版本号"""
        return VersionNumber(self.major, self.minor, self.patch + 1)
    
    def with_prerelease(self, prerelease: str) -> 'VersionNumber':
        """设置预发布标识"""
        return VersionNumber(self.major, self.minor, self.patch, prerelease)


@dataclass
class VersionRelationInfo:
    """版本关系信息数据类"""
    related_version: str
    relation_type: str
    created_at: str
    description: Optional[str] = None


@dataclass
class VersionInfo:
    """版本信息数据类"""
    version: str
    created_at: str
    description: str
    doc_types: List[str]
    workflow_stages: List[str] = field(default_factory=list)
    is_archived: bool = False
    archived_at: Optional[str] = None
    parent_version: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    status: str = field(default_factory=lambda: VersionStatus.DRAFT.value)
    branch_name: Optional[str] = None
    relations: List[Dict[str, Any]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    updated_at: Optional[str] = None
    deprecated_at: Optional[str] = None


@dataclass
class DocumentMetadata:
    """文档元数据数据类"""
    name: str
    doc_type: str
    workflow_stage: Optional[str]
    version: str
    created_at: str
    updated_at: str
    file_path: str
    size_bytes: int
    checksum: Optional[str] = None
    history: List[Dict[str, Any]] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    author: Optional[str] = None
    description: Optional[str] = None


@dataclass
class DiffResult:
    """差异对比结果数据类"""
    file1: str
    file2: str
    added_lines: int
    removed_lines: int
    modified_lines: int
    diff_content: str
    similarity_ratio: float
    diff_type: str = "unified"
    changes_summary: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class IntegrityCheckResult:
    """完整性检查结果数据类"""
    is_valid: bool
    missing_files: List[str]
    checksum_mismatches: List[str]
    missing_directories: List[str]
    errors: List[str]


@dataclass
class WorkflowStageInfo:
    """工作流程阶段信息数据类"""
    stage: str
    display_name: str
    description: str
    required_docs: List[str] = field(default_factory=list)
    order: int = 0
    is_active: bool = True


@dataclass
class HistoryRetentionPolicy:
    """历史版本保留策略数据类"""
    max_versions: int = 10
    max_age_days: int = 365
    keep_tagged_versions: bool = True
    auto_cleanup: bool = True
    cleanup_interval_days: int = 30


@dataclass
class DocumentVersionSnapshot:
    """文档版本快照数据类"""
    snapshot_id: str
    version: str
    doc_name: str
    doc_path: str
    created_at: str
    checksum: str
    size_bytes: int
    tags: List[str] = field(default_factory=list)
    description: Optional[str] = None
    is_auto_snapshot: bool = False
    workflow_stage: Optional[str] = None


@dataclass
class RollbackResult:
    """回滚结果数据类"""
    success: bool
    version: str
    doc_name: str
    rollback_time: str
    backup_snapshot_id: Optional[str] = None
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


@dataclass
class DiffReport:
    """差异报告数据类"""
    report_id: str
    generated_at: str
    file1_info: Dict[str, Any]
    file2_info: Dict[str, Any]
    diff_result: Optional[DiffResult] = None
    summary: Dict[str, Any] = field(default_factory=dict)
    recommendations: List[str] = field(default_factory=list)


@dataclass
class BranchInfo:
    """分支信息数据类"""
    name: str
    created_at: str
    base_version: str
    current_version: str
    description: Optional[str] = None
    is_merged: bool = False
    merged_at: Optional[str] = None
    merged_to: Optional[str] = None


class DocVersionManager:
    """文档版本管理器主类"""
    BASE_DIR = get_path_config().SKILL_ROOT
    DOCS_DIR = BASE_DIR / "docs"
    LIBS_DIR = DOCS_DIR / "libs"
    REPORTS_DIR = DOCS_DIR / "reports"
    WORKFLOW_DIR = DOCS_DIR / "workflow"
    HISTORY_DIR = DOCS_DIR / "history"
    VERSION_FILE = DOCS_DIR / "version.json"
    METADATA_FILE = DOCS_DIR / "metadata.json"
    BRANCH_FILE = DOCS_DIR / "branches.json"
    SNAPSHOT_DIR = DOCS_DIR / "snapshots"
    DIFF_REPORT_DIR = DOCS_DIR / "diff_reports"
    ROLLBACK_DIR = DOCS_DIR / "rollback_backups"
    
    WORKFLOW_STAGE_CONFIG: Dict[str, WorkflowStageInfo] = {
        "requirements": WorkflowStageInfo(
            stage="requirements",
            display_name="需求阶段",
            description="需求分析和文档编写阶段",
            required_docs=["需求规格说明书", "用户故事"],
            order=1
        ),
        "design": WorkflowStageInfo(
            stage="design",
            display_name="设计阶段",
            description="系统设计和架构设计阶段",
            required_docs=["设计文档", "架构图"],
            order=2
        ),
        "implementation": WorkflowStageInfo(
            stage="implementation",
            display_name="实现阶段",
            description="代码开发和功能实现阶段",
            required_docs=["代码文档", "API文档"],
            order=3
        ),
        "testing": WorkflowStageInfo(
            stage="testing",
            display_name="测试阶段",
            description="测试和验证阶段",
            required_docs=["测试计划", "测试报告"],
            order=4
        ),
        "deployment": WorkflowStageInfo(
            stage="deployment",
            display_name="部署阶段",
            description="部署和发布阶段",
            required_docs=["部署文档", "运维手册"],
            order=5
        )
    }
    
    def __init__(self):
        self._ensure_dirs()
        self._init_metadata()
    
    def _ensure_dirs(self):
        """确保所有必要的目录都存在"""
        self.DOCS_DIR.mkdir(parents=True, exist_ok=True)
        self.LIBS_DIR.mkdir(parents=True, exist_ok=True)
        self.REPORTS_DIR.mkdir(parents=True, exist_ok=True)
        self.WORKFLOW_DIR.mkdir(parents=True, exist_ok=True)
        self.HISTORY_DIR.mkdir(parents=True, exist_ok=True)
        self.SNAPSHOT_DIR.mkdir(parents=True, exist_ok=True)
        self.DIFF_REPORT_DIR.mkdir(parents=True, exist_ok=True)
        self.ROLLBACK_DIR.mkdir(parents=True, exist_ok=True)
        
        for stage in WorkflowStage:
            (self.WORKFLOW_DIR / stage.value).mkdir(parents=True, exist_ok=True)
    
    def _init_metadata(self):
        """初始化元数据文件"""
        if not self.METADATA_FILE.exists():
            self._save_metadata({"versions": {}, "documents": []})
        if not self.VERSION_FILE.exists():
            self._save_version_config({"current_version": "v1.0.0", "versions": [], "current_branch": "main"})
        if not self.BRANCH_FILE.exists():
            self._save_branches({"main": {
                "name": "main",
                "created_at": datetime.now().isoformat(),
                "base_version": "v1.0.0",
                "current_version": "v1.0.0",
                "description": "主分支",
                "is_merged": False,
                "merged_at": None,
                "merged_to": None
            }})
    
    def _load_metadata(self) -> Dict[str, Any]:
        """加载元数据"""
        if self.METADATA_FILE.exists():
            with open(self.METADATA_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {"versions": {}, "documents": [], "branches": {}}
    
    def _save_metadata(self, metadata: Dict[str, Any]):
        """保存元数据"""
        with open(self.METADATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)
    
    def _load_version_config(self) -> Dict[str, Any]:
        """加载版本配置"""
        if self.VERSION_FILE.exists():
            with open(self.VERSION_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {"current_version": "v1.0.0", "versions": [], "current_branch": "main"}
    
    def _save_version_config(self, config: Dict[str, Any]):
        """保存版本配置"""
        with open(self.VERSION_FILE, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
    
    def _load_branches(self) -> Dict[str, Any]:
        """加载分支信息"""
        if self.BRANCH_FILE.exists():
            with open(self.BRANCH_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}
    
    def _save_branches(self, branches: Dict[str, Any]):
        """保存分支信息"""
        with open(self.BRANCH_FILE, 'w', encoding='utf-8') as f:
            json.dump(branches, f, ensure_ascii=False, indent=2)
    
    def _calculate_checksum(self, file_path: Path) -> str:
        """计算文件校验和"""
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    
    def _ensure_workflow_dirs(self, version: str):
        """确保版本的工作流程目录存在"""
        version_workflow_dir = self.WORKFLOW_DIR / version
        version_workflow_dir.mkdir(parents=True, exist_ok=True)
        
        for stage in WorkflowStage:
            stage_dir = version_workflow_dir / stage.value
            stage_dir.mkdir(parents=True, exist_ok=True)
    
    def parse_version(self, version: str) -> Optional[VersionNumber]:
        """解析版本字符串"""
        return VersionNumber.parse(version)
    
    def compare_versions(self, v1: str, v2: str) -> int:
        """比较两个版本号"""
        ver1 = self.parse_version(v1)
        ver2 = self.parse_version(v2)
        
        if ver1 is None or ver2 is None:
            raise ValueError(f"无效的版本号: {v1 if ver1 is None else v2}")
        
        if ver1 < ver2:
            return -1
        elif ver1 > ver2:
            return 1
        return 0
    
    def get_next_version(self, bump_type: str = "patch") -> str:
        """获取下一个版本号"""
        config = self._load_version_config()
        current = config.get("current_version", "v1.0.0")
        ver = self.parse_version(current)
        
        if ver is None:
            return "v1.0.0"
        
        if bump_type == "major":
            return str(ver.bump_major())
        elif bump_type == "minor":
            return str(ver.bump_minor())
        else:
            return str(ver.bump_patch())
    
    def get_sorted_versions(self) -> List[str]:
        """获取排序后的版本列表"""
        config = self._load_version_config()
        versions = config.get("versions", [])
        parsed = [(v, self.parse_version(v)) for v in versions]
        parsed = [(v, p) for v, p in parsed if p is not None]
        parsed.sort(key=lambda x: x[1])
        return [v for v, _ in parsed]
    
    def get_version_history(self, version: str) -> List[str]:
        """获取版本历史"""
        sorted_versions = self.get_sorted_versions()
        if version not in sorted_versions:
            return []
        idx = sorted_versions.index(version)
        return sorted_versions[:idx + 1]
    
    def get_current_version(self) -> str:
        """获取当前版本"""
        config = self._load_version_config()
        return config.get("current_version", "v1.0.0")
    
    def set_current_version(self, version: str) -> bool:
        """设置当前版本"""
        config = self._load_version_config()
        if version not in config.get("versions", []):
            print(f"版本 {version} 不存在")
            return False
        config["current_version"] = version
        self._save_version_config(config)
        print(f"当前版本已设置为: {version}")
        return True
    
    def create_version(self, version: str, description: str = "", 
                       parent_version: Optional[str] = None,
                       tags: Optional[List[str]] = None,
                       status: str = VersionStatus.DRAFT.value,
                       branch_name: Optional[str] = None) -> bool:
        """创建新版本"""
        config = self._load_version_config()
        
        if version in config.get("versions", []):
            print(f"版本 {version} 已存在")
            return False
        
        ver_num = self.parse_version(version)
        if ver_num is None:
            print(f"无效的版本号格式: {version}")
            return False
        
        version_libs_dir = self.LIBS_DIR / version
        version_reports_dir = self.REPORTS_DIR / version
        
        version_libs_dir.mkdir(parents=True, exist_ok=True)
        version_reports_dir.mkdir(parents=True, exist_ok=True)
        
        for doc_type in DocType:
            if doc_type in [DocType.API, DocType.ARCHITECTURE, DocType.CHANGELOG]:
                (version_libs_dir / doc_type.value).mkdir(exist_ok=True)
            else:
                (version_reports_dir / doc_type.value).mkdir(exist_ok=True)
        
        self._ensure_workflow_dirs(version)
        
        if "versions" not in config:
            config["versions"] = []
        config["versions"].append(version)
        config["current_version"] = version
        self._save_version_config(config)
        
        metadata = self._load_metadata()
        relations = []
        if parent_version:
            relations.append({
                "related_version": parent_version,
                "relation_type": VersionRelation.PARENT.value,
                "created_at": datetime.now().isoformat(),
                "description": f"继承自 {parent_version}"
            })
        
        metadata["versions"][version] = asdict(VersionInfo(
            version=version,
            created_at=datetime.now().isoformat(),
            description=description,
            doc_types=[dt.value for dt in DocType],
            workflow_stages=[ws.value for ws in WorkflowStage],
            parent_version=parent_version,
            tags=tags or [],
            status=status,
            branch_name=branch_name,
            relations=relations
        ))
        self._save_metadata(metadata)
        
        print(f"版本 {version} 创建成功")
        return True
    
    def update_version_status(self, version: str, status: VersionStatus) -> bool:
        """更新版本状态"""
        metadata = self._load_metadata()
        version_data = metadata.get("versions", {}).get(version)
        
        if not version_data:
            print(f"版本 {version} 不存在")
            return False
        
        version_data["status"] = status.value
        version_data["updated_at"] = datetime.now().isoformat()
        
        if status == VersionStatus.DEPRECATED:
            version_data["deprecated_at"] = datetime.now().isoformat()
        
        self._save_metadata(metadata)
        print(f"版本 {version} 状态已更新为: {status.value}")
        return True
    
    def get_versions_by_status(self, status: VersionStatus) -> List[VersionInfo]:
        """按状态获取版本列表"""
        metadata = self._load_metadata()
        versions = []
        for version_data in metadata.get("versions", {}).values():
            if version_data.get("status") == status.value:
                versions.append(VersionInfo(**version_data))
        return sorted(versions, key=lambda x: self.parse_version(x.version) or VersionNumber(0, 0, 0))
    
    def create_branch(self, branch_name: str, base_version: str, 
                      description: Optional[str] = None) -> bool:
        """创建版本分支"""
        branches = self._load_branches()
        
        if branch_name in branches:
            print(f"分支 {branch_name} 已存在")
            return False
        
        base_info = self.get_version_info(base_version)
        if not base_info:
            print(f"基础版本 {base_version} 不存在")
            return False
        
        branch_version = f"{base_version}-{branch_name}"
        result = self.create_version(
            version=branch_version,
            description=f"分支 {branch_name} - {description or ''}",
            parent_version=base_version,
            branch_name=branch_name
        )
        
        if not result:
            return False
        
        branches[branch_name] = asdict(BranchInfo(
            name=branch_name,
            created_at=datetime.now().isoformat(),
            base_version=base_version,
            current_version=branch_version,
            description=description
        ))
        self._save_branches(branches)
        
        config = self._load_version_config()
        config["current_branch"] = branch_name
        self._save_version_config(config)
        
        print(f"分支 {branch_name} 创建成功，基于版本 {base_version}")
        return True
    
    def switch_branch(self, branch_name: str) -> bool:
        """切换分支"""
        branches = self._load_branches()
        
        if branch_name not in branches:
            print(f"分支 {branch_name} 不存在")
            return False
        
        branch_info = BranchInfo(**branches[branch_name])
        
        config = self._load_version_config()
        config["current_branch"] = branch_name
        config["current_version"] = branch_info.current_version
        self._save_version_config(config)
        
        print(f"已切换到分支: {branch_name} (版本: {branch_info.current_version})")
        return True
    
    def merge_branch(self, source_branch: str, target_version: str,
                     merge_message: Optional[str] = None) -> bool:
        """合并分支到目标版本"""
        branches = self._load_branches()
        
        if source_branch not in branches:
            print(f"源分支 {source_branch} 不存在")
            return False
        
        branch_info = BranchInfo(**branches[source_branch])
        
        if branch_info.is_merged:
            print(f"分支 {source_branch} 已被合并")
            return False
        
        target_info = self.get_version_info(target_version)
        if not target_info:
            print(f"目标版本 {target_version} 不存在")
            return False
        
        result = self.migrate_version(
            source_version=branch_info.current_version,
            target_version=target_version,
            copy_mode=True
        )
        
        if not result:
            return False
        
        metadata = self._load_metadata()
        target_data = metadata.get("versions", {}).get(target_version)
        if target_data:
            target_data.setdefault("relations", []).append({
                "related_version": branch_info.current_version,
                "relation_type": VersionRelation.MERGE.value,
                "created_at": datetime.now().isoformat(),
                "description": merge_message or f"合并分支 {source_branch}"
            })
        self._save_metadata(metadata)
        
        branches[source_branch]["is_merged"] = True
        branches[source_branch]["merged_at"] = datetime.now().isoformat()
        branches[source_branch]["merged_to"] = target_version
        self._save_branches(branches)
        
        print(f"分支 {source_branch} 已成功合并到版本 {target_version}")
        return True
    
    def list_branches(self) -> List[BranchInfo]:
        """列出所有分支"""
        branches = self._load_branches()
        result = []
        for b in branches.values():
            if isinstance(b, dict):
                result.append(BranchInfo(**b))
            elif isinstance(b, BranchInfo):
                result.append(b)
        return result
    
    def get_current_branch(self) -> Optional[str]:
        """获取当前分支"""
        config = self._load_version_config()
        return config.get("current_branch")
    
    def add_version_relation(self, version: str, related_version: str,
                            relation_type: VersionRelation,
                            description: Optional[str] = None) -> bool:
        """添加版本关系"""
        metadata = self._load_metadata()
        version_data = metadata.get("versions", {}).get(version)
        
        if not version_data:
            print(f"版本 {version} 不存在")
            return False
        
        related_info = self.get_version_info(related_version)
        if not related_info:
            print(f"关联版本 {related_version} 不存在")
            return False
        
        version_data.setdefault("relations", []).append({
            "related_version": related_version,
            "relation_type": relation_type.value,
            "created_at": datetime.now().isoformat(),
            "description": description
        })
        
        self._save_metadata(metadata)
        print(f"已添加版本关系: {version} -> {related_version} ({relation_type.value})")
        return True
    
    def get_version_relations(self, version: str, 
                             relation_type: Optional[VersionRelation] = None) -> List[VersionRelationInfo]:
        """获取版本关系"""
        metadata = self._load_metadata()
        version_data = metadata.get("versions", {}).get(version)
        
        if not version_data:
            return []
        
        relations = []
        for rel in version_data.get("relations", []):
            if relation_type is None or rel.get("relation_type") == relation_type.value:
                relations.append(VersionRelationInfo(
                    related_version=rel.get("related_version"),
                    relation_type=rel.get("relation_type"),
                    created_at=rel.get("created_at"),
                    description=rel.get("description")
                ))
        
        return relations
    
    def list_versions(self, include_archived: bool = True, 
                      sort_by_version: bool = True,
                      status_filter: Optional[VersionStatus] = None) -> List[VersionInfo]:
        """列出所有版本"""
        metadata = self._load_metadata()
        versions = []
        for version_data in metadata.get("versions", {}).values():
            info = VersionInfo(**version_data)
            if not include_archived and info.is_archived:
                continue
            if status_filter and info.status != status_filter.value:
                continue
            versions.append(info)
        
        if sort_by_version:
            return sorted(versions, key=lambda x: self.parse_version(x.version) or VersionNumber(0, 0, 0))
        return sorted(versions, key=lambda x: x.created_at, reverse=True)
    
    def get_version_info(self, version: str) -> Optional[VersionInfo]:
        """获取版本信息"""
        metadata = self._load_metadata()
        version_data = metadata.get("versions", {}).get(version)
        if version_data:
            return VersionInfo(**version_data)
        return None
    
    def migrate_version(self, source_version: str, target_version: str,
                        doc_types: Optional[List[DocType]] = None,
                        workflow_stages: Optional[List[WorkflowStage]] = None,
                        copy_mode: bool = True) -> bool:
        """迁移版本文档"""
        source_info = self.get_version_info(source_version)
        target_info = self.get_version_info(target_version)
        
        if not source_info:
            print(f"源版本 {source_version} 不存在")
            return False
        if not target_info:
            print(f"目标版本 {target_version} 不存在")
            return False
        
        metadata = self._load_metadata()
        migrated_count = 0
        
        if doc_types is None:
            doc_types = list(DocType)
        
        for doc_type in doc_types:
            if doc_type in [DocType.API, DocType.ARCHITECTURE, DocType.CHANGELOG]:
                source_dir = self.LIBS_DIR / source_version / doc_type.value
                target_dir = self.LIBS_DIR / target_version / doc_type.value
            else:
                source_dir = self.REPORTS_DIR / source_version / doc_type.value
                target_dir = self.REPORTS_DIR / target_version / doc_type.value
            
            if source_dir.exists():
                target_dir.mkdir(parents=True, exist_ok=True)
                for file_path in source_dir.iterdir():
                    if file_path.is_file():
                        target_path = target_dir / file_path.name
                        if copy_mode:
                            shutil.copy2(str(file_path), str(target_path))
                        else:
                            shutil.move(str(file_path), str(target_path))
                        
                        for doc in metadata.get("documents", []):
                            if doc.get("file_path") == str(file_path):
                                new_doc = deepcopy(doc)
                                new_doc["version"] = target_version
                                new_doc["file_path"] = str(target_path)
                                new_doc["updated_at"] = datetime.now().isoformat()
                                new_doc["history"].append({
                                    "action": "migrated",
                                    "from_version": source_version,
                                    "to_version": target_version,
                                    "timestamp": datetime.now().isoformat()
                                })
                                metadata["documents"].append(new_doc)
                                migrated_count += 1
        
        if workflow_stages is None:
            workflow_stages = list(WorkflowStage)
        
        for stage in workflow_stages:
            source_dir = self.WORKFLOW_DIR / source_version / stage.value
            target_dir = self.WORKFLOW_DIR / target_version / stage.value
            
            if source_dir.exists():
                target_dir.mkdir(parents=True, exist_ok=True)
                for file_path in source_dir.iterdir():
                    if file_path.is_file():
                        target_path = target_dir / file_path.name
                        if copy_mode:
                            shutil.copy2(str(file_path), str(target_path))
                        else:
                            shutil.move(str(file_path), str(target_path))
                        migrated_count += 1
        
        self._save_metadata(metadata)
        print(f"已迁移 {migrated_count} 个文档从 {source_version} 到 {target_version}")
        return True
    
    def archive_version(self, version: str) -> bool:
        """归档版本"""
        metadata = self._load_metadata()
        version_data = metadata.get("versions", {}).get(version)
        
        if not version_data:
            print(f"版本 {version} 不存在")
            return False
        
        version_data["is_archived"] = True
        version_data["archived_at"] = datetime.now().isoformat()
        version_data["status"] = VersionStatus.ARCHIVED.value
        self._save_metadata(metadata)
        
        archive_dir = self.DOCS_DIR / "archive"
        archive_dir.mkdir(exist_ok=True)
        
        version_libs_dir = self.LIBS_DIR / version
        version_reports_dir = self.REPORTS_DIR / version
        version_workflow_dir = self.WORKFLOW_DIR / version
        
        if version_libs_dir.exists():
            shutil.move(str(version_libs_dir), str(archive_dir / f"libs_{version}"))
        if version_reports_dir.exists():
            shutil.move(str(version_reports_dir), str(archive_dir / f"reports_{version}"))
        if version_workflow_dir.exists():
            shutil.move(str(version_workflow_dir), str(archive_dir / f"workflow_{version}"))
        
        print(f"版本 {version} 已归档")
        return True
    
    def restore_version(self, version: str) -> bool:
        """恢复归档版本"""
        archive_dir = self.DOCS_DIR / "archive"
        archived_libs = archive_dir / f"libs_{version}"
        archived_reports = archive_dir / f"reports_{version}"
        archived_workflow = archive_dir / f"workflow_{version}"
        
        if not archived_libs.exists() and not archived_reports.exists() and not archived_workflow.exists():
            print(f"未找到版本 {version} 的归档文件")
            return False
        
        if archived_libs.exists():
            shutil.move(str(archived_libs), str(self.LIBS_DIR / version))
        if archived_reports.exists():
            shutil.move(str(archived_reports), str(self.REPORTS_DIR / version))
        if archived_workflow.exists():
            shutil.move(str(archived_workflow), str(self.WORKFLOW_DIR / version))
        
        metadata = self._load_metadata()
        version_data = metadata.get("versions", {}).get(version)
        if version_data:
            version_data["is_archived"] = False
            version_data["archived_at"] = None
            version_data["status"] = VersionStatus.DRAFT.value
            self._save_metadata(metadata)
        
        print(f"版本 {version} 已恢复")
        return True
    
    def add_document(self, version: str, source_path: str, 
                     doc_type: Optional[DocType] = None,
                     workflow_stage: Optional[WorkflowStage] = None,
                     doc_name: Optional[str] = None,
                     tags: Optional[List[str]] = None,
                     author: Optional[str] = None,
                     description: Optional[str] = None) -> bool:
        """添加文档到版本"""
        version_info = self.get_version_info(version)
        if not version_info:
            print(f"版本 {version} 不存在")
            return False
        
        source = Path(source_path)
        if not source.exists():
            print(f"源文件 {source_path} 不存在")
            return False
        
        target_dir = None
        category = "general"
        
        if workflow_stage:
            target_dir = self.WORKFLOW_DIR / version / workflow_stage.value
            category = workflow_stage.value
        elif doc_type:
            if doc_type in [DocType.API, DocType.ARCHITECTURE, DocType.CHANGELOG]:
                target_dir = self.LIBS_DIR / version / doc_type.value
            else:
                target_dir = self.REPORTS_DIR / version / doc_type.value
            category = doc_type.value
        
        if target_dir is None:
            print("必须指定 doc_type 或 workflow_stage")
            return False
        
        target_dir.mkdir(parents=True, exist_ok=True)
        
        doc_name = doc_name or source.name
        target_path = target_dir / doc_name
        
        history_entry = {
            "action": "created",
            "timestamp": datetime.now().isoformat(),
            "source": str(source)
        }
        
        if target_path.exists():
            old_checksum = self._calculate_checksum(target_path)
            history_entry = {
                "action": "updated",
                "timestamp": datetime.now().isoformat(),
                "old_checksum": old_checksum
            }
        
        shutil.copy2(str(source), str(target_path))
        checksum = self._calculate_checksum(target_path)
        
        metadata = self._load_metadata()
        
        existing_doc = None
        for doc in metadata.get("documents", []):
            if doc.get("file_path") == str(target_path):
                existing_doc = doc
                break
        
        if existing_doc:
            existing_doc["updated_at"] = datetime.now().isoformat()
            existing_doc["checksum"] = checksum
            existing_doc["size_bytes"] = target_path.stat().st_size
            existing_doc["history"].append(history_entry)
            if tags:
                existing_doc["tags"] = list(set(existing_doc.get("tags", []) + tags))
        else:
            doc_meta = asdict(DocumentMetadata(
                name=doc_name,
                doc_type=doc_type.value if doc_type else None,
                workflow_stage=workflow_stage.value if workflow_stage else None,
                version=version,
                created_at=datetime.now().isoformat(),
                updated_at=datetime.now().isoformat(),
                file_path=str(target_path),
                size_bytes=target_path.stat().st_size,
                checksum=checksum,
                history=[history_entry],
                tags=tags or [],
                author=author,
                description=description
            ))
            metadata.setdefault("documents", []).append(doc_meta)
        
        self._save_metadata(metadata)
        print(f"文档 {doc_name} 已添加到版本 {version} ({category})")
        return True
    
    def save_document_history(self, version: str, doc_path: str,
                             change_description: Optional[str] = None) -> bool:
        """保存文档历史版本"""
        source = Path(doc_path)
        if not source.exists():
            print(f"文件 {doc_path} 不存在")
            return False
        
        history_version_dir = self.HISTORY_DIR / version
        history_version_dir.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        history_filename = f"{source.stem}_{timestamp}{source.suffix}"
        history_path = history_version_dir / history_filename
        
        shutil.copy2(str(source), str(history_path))
        
        history_meta_file = history_version_dir / "history_meta.json"
        history_meta = {}
        if history_meta_file.exists():
            with open(history_meta_file, 'r', encoding='utf-8') as f:
                history_meta = json.load(f)
        
        doc_key = source.name
        if doc_key not in history_meta:
            history_meta[doc_key] = []
        
        history_entry = {
            "timestamp": datetime.now().isoformat(),
            "history_file": history_filename,
            "checksum": self._calculate_checksum(source),
            "size_bytes": source.stat().st_size,
            "change_description": change_description
        }
        history_meta[doc_key].append(history_entry)
        
        with open(history_meta_file, 'w', encoding='utf-8') as f:
            json.dump(history_meta, f, ensure_ascii=False, indent=2)
        
        print(f"文档历史版本已保存: {history_path}")
        return True
    
    def get_document_history(self, version: str, doc_name: str) -> List[Dict[str, Any]]:
        """获取文档历史版本列表"""
        history_version_dir = self.HISTORY_DIR / version
        history_meta_file = history_version_dir / "history_meta.json"
        
        if not history_meta_file.exists():
            return []
        
        with open(history_meta_file, 'r', encoding='utf-8') as f:
            history_meta = json.load(f)
        
        return history_meta.get(doc_name, [])
    
    def restore_document_version(self, version: str, doc_name: str, 
                                 history_file: str) -> bool:
        """恢复文档到指定历史版本"""
        history_version_dir = self.HISTORY_DIR / version
        history_path = history_version_dir / history_file
        
        if not history_path.exists():
            print(f"历史版本文件 {history_file} 不存在")
            return False
        
        metadata = self._load_metadata()
        current_doc = None
        for doc in metadata.get("documents", []):
            if doc.get("name") == doc_name and doc.get("version") == version:
                current_doc = doc
                break
        
        if not current_doc:
            print(f"未找到文档 {doc_name} 的当前版本")
            return False
        
        current_path = Path(current_doc["file_path"])
        self.save_document_history(version, str(current_path), "恢复前自动备份")
        
        shutil.copy2(str(history_path), str(current_path))
        
        current_doc["checksum"] = self._calculate_checksum(current_path)
        current_doc["updated_at"] = datetime.now().isoformat()
        current_doc["history"].append({
            "action": "restored",
            "timestamp": datetime.now().isoformat(),
            "restored_from": history_file
        })
        
        self._save_metadata(metadata)
        print(f"文档 {doc_name} 已恢复到历史版本 {history_file}")
        return True
    
    def compare_documents(self, file1: str, file2: str,
                         diff_type: str = "unified") -> DiffResult:
        """比较两个文档的差异"""
        path1 = Path(file1)
        path2 = Path(file2)
        
        if not path1.exists() or not path2.exists():
            raise FileNotFoundError("一个或两个文件不存在")
        
        with open(path1, 'r', encoding='utf-8') as f:
            lines1 = f.readlines()
        with open(path2, 'r', encoding='utf-8') as f:
            lines2 = f.readlines()
        
        if diff_type == "unified":
            diff = list(difflib.unified_diff(lines1, lines2, 
                                             fromfile=str(path1), 
                                             tofile=str(path2),
                                             lineterm=''))
        elif diff_type == "context":
            diff = list(difflib.context_diff(lines1, lines2,
                                             fromfile=str(path1),
                                             tofile=str(path2),
                                             lineterm=''))
        else:
            diff = list(difflib.unified_diff(lines1, lines2,
                                             fromfile=str(path1),
                                             tofile=str(path2),
                                             lineterm=''))
        
        added = sum(1 for line in diff if line.startswith('+') and not line.startswith('+++'))
        removed = sum(1 for line in diff if line.startswith('-') and not line.startswith('---'))
        
        matcher = difflib.SequenceMatcher(None, lines1, lines2)
        similarity = matcher.ratio()
        
        changes_summary = []
        for tag, i1, i2, j1, j2 in matcher.get_opcodes():
            if tag != 'equal':
                changes_summary.append({
                    "type": tag,
                    "file1_range": (i1, i2),
                    "file2_range": (j1, j2),
                    "file1_lines": lines1[i1:i2] if i1 < len(lines1) else [],
                    "file2_lines": lines2[j1:j2] if j1 < len(lines2) else []
                })
        
        return DiffResult(
            file1=str(path1),
            file2=str(path2),
            added_lines=added,
            removed_lines=removed,
            modified_lines=added + removed,
            diff_content='\n'.join(diff),
            similarity_ratio=similarity,
            diff_type=diff_type,
            changes_summary=changes_summary
        )
    
    def compare_versions(self, version1: str, version2: str, 
                         doc_type: Optional[DocType] = None,
                         workflow_stage: Optional[WorkflowStage] = None) -> List[DiffResult]:
        """比较两个版本的文档差异"""
        results = []
        
        if workflow_stage:
            dir1 = self.WORKFLOW_DIR / version1 / workflow_stage.value
            dir2 = self.WORKFLOW_DIR / version2 / workflow_stage.value
        elif doc_type:
            if doc_type in [DocType.API, DocType.ARCHITECTURE, DocType.CHANGELOG]:
                dir1 = self.LIBS_DIR / version1 / doc_type.value
                dir2 = self.LIBS_DIR / version2 / doc_type.value
            else:
                dir1 = self.REPORTS_DIR / version1 / doc_type.value
                dir2 = self.REPORTS_DIR / version2 / doc_type.value
        else:
            print("必须指定 doc_type 或 workflow_stage")
            return results
        
        if not dir1.exists() or not dir2.exists():
            print("一个或两个版本的目录不存在")
            return results
        
        files1 = {f.name: f for f in dir1.iterdir() if f.is_file()}
        files2 = {f.name: f for f in dir2.iterdir() if f.is_file()}
        
        all_files = set(files1.keys()) | set(files2.keys())
        
        for filename in all_files:
            if filename in files1 and filename in files2:
                try:
                    diff_result = self.compare_documents(str(files1[filename]), str(files2[filename]))
                    results.append(diff_result)
                except Exception as e:
                    print(f"比较文件 {filename} 时出错: {e}")
        
        return results
    
    def compare_history_versions(self, version: str, doc_name: str,
                                 history_file1: str, history_file2: str) -> Optional[DiffResult]:
        """比较文档的两个历史版本"""
        history_dir = self.HISTORY_DIR / version
        path1 = history_dir / history_file1
        path2 = history_dir / history_file2
        
        if not path1.exists() or not path2.exists():
            print("一个或两个历史版本文件不存在")
            return None
        
        try:
            return self.compare_documents(str(path1), str(path2))
        except Exception as e:
            print(f"比较历史版本时出错: {e}")
            return None
    
    def check_integrity(self, version: Optional[str] = None) -> IntegrityCheckResult:
        """检查版本完整性"""
        metadata = self._load_metadata()
        missing_files = []
        checksum_mismatches = []
        missing_directories = []
        errors = []
        
        versions_to_check = [version] if version else list(metadata.get("versions", {}).keys())
        
        for ver in versions_to_check:
            version_info = self.get_version_info(ver)
            if not version_info:
                errors.append(f"版本 {ver} 信息不存在")
                continue
            
            for doc_type in DocType:
                if doc_type in [DocType.API, DocType.ARCHITECTURE, DocType.CHANGELOG]:
                    doc_dir = self.LIBS_DIR / ver / doc_type.value
                else:
                    doc_dir = self.REPORTS_DIR / ver / doc_type.value
                
                if not doc_dir.exists():
                    missing_directories.append(str(doc_dir))
            
            workflow_dir = self.WORKFLOW_DIR / ver
            if not workflow_dir.exists():
                missing_directories.append(str(workflow_dir))
            else:
                for stage in WorkflowStage:
                    stage_dir = workflow_dir / stage.value
                    if not stage_dir.exists():
                        missing_directories.append(str(stage_dir))
        
        for doc in metadata.get("documents", []):
            if version and doc.get("version") != version:
                continue
            
            file_path = Path(doc.get("file_path", ""))
            if not file_path.exists():
                missing_files.append(str(file_path))
                continue
            
            if doc.get("checksum"):
                current_checksum = self._calculate_checksum(file_path)
                if current_checksum != doc.get("checksum"):
                    checksum_mismatches.append(str(file_path))
        
        is_valid = not (missing_files or checksum_mismatches or missing_directories or errors)
        
        return IntegrityCheckResult(
            is_valid=is_valid,
            missing_files=missing_files,
            checksum_mismatches=checksum_mismatches,
            missing_directories=missing_directories,
            errors=errors
        )
    
    def repair_integrity(self, version: Optional[str] = None) -> bool:
        """修复版本完整性"""
        result = self.check_integrity(version)
        
        if result.is_valid:
            print("完整性检查通过，无需修复")
            return True
        
        for dir_path in result.missing_directories:
            Path(dir_path).mkdir(parents=True, exist_ok=True)
            print(f"已创建缺失目录: {dir_path}")
        
        metadata = self._load_metadata()
        docs_to_remove = []
        
        for file_path in result.missing_files:
            for i, doc in enumerate(metadata.get("documents", [])):
                if doc.get("file_path") == file_path:
                    docs_to_remove.append(i)
                    print(f"已移除无效文档记录: {file_path}")
                    break
        
        for i in reversed(docs_to_remove):
            metadata["documents"].pop(i)
        
        for file_path in result.checksum_mismatches:
            for doc in metadata.get("documents", []):
                if doc.get("file_path") == file_path:
                    doc["checksum"] = self._calculate_checksum(Path(file_path))
                    doc["updated_at"] = datetime.now().isoformat()
                    print(f"已更新文档校验和: {file_path}")
                    break
        
        self._save_metadata(metadata)
        print("完整性修复完成")
        return True
    
    def list_documents(self, version: Optional[str] = None, 
                       doc_type: Optional[DocType] = None,
                       workflow_stage: Optional[WorkflowStage] = None,
                       tags: Optional[List[str]] = None) -> List[DocumentMetadata]:
        """列出文档"""
        metadata = self._load_metadata()
        documents = []
        
        for doc_data in metadata.get("documents", []):
            if version and doc_data.get("version") != version:
                continue
            if doc_type and doc_data.get("doc_type") != doc_type.value:
                continue
            if workflow_stage and doc_data.get("workflow_stage") != workflow_stage.value:
                continue
            if tags:
                doc_tags = set(doc_data.get("tags", []))
                if not all(t in doc_tags for t in tags):
                    continue
            documents.append(DocumentMetadata(**doc_data))
        
        return documents
    
    def delete_version(self, version: str, force: bool = False) -> bool:
        """删除版本"""
        config = self._load_version_config()
        metadata = self._load_metadata()
        
        version_info = self.get_version_info(version)
        if not version_info:
            print(f"版本 {version} 不存在")
            return False
        
        if version == config.get("current_version") and not force:
            print(f"无法删除当前版本 {version}，请先切换到其他版本或使用 --force")
            return False
        
        version_libs_dir = self.LIBS_DIR / version
        version_reports_dir = self.REPORTS_DIR / version
        version_workflow_dir = self.WORKFLOW_DIR / version
        version_history_dir = self.HISTORY_DIR / version
        
        for dir_path in [version_libs_dir, version_reports_dir, version_workflow_dir, version_history_dir]:
            if dir_path.exists():
                shutil.rmtree(str(dir_path))
        
        if version in config.get("versions", []):
            config["versions"].remove(version)
        if config.get("current_version") == version:
            sorted_versions = self.get_sorted_versions()
            config["current_version"] = sorted_versions[-1] if sorted_versions else "v1.0.0"
        self._save_version_config(config)
        
        if version in metadata.get("versions", {}):
            del metadata["versions"][version]
        metadata["documents"] = [
            d for d in metadata.get("documents", []) 
            if d.get("version") != version
        ]
        self._save_metadata(metadata)
        
        print(f"版本 {version} 已删除")
        return True
    
    def generate_changelog(self, version: str, changes: List[str]) -> bool:
        """生成变更日志"""
        version_info = self.get_version_info(version)
        if not version_info:
            print(f"版本 {version} 不存在")
            return False
        
        changelog_dir = self.LIBS_DIR / version / DocType.CHANGELOG.value
        changelog_dir.mkdir(parents=True, exist_ok=True)
        
        changelog_file = changelog_dir / "CHANGELOG.md"
        
        content = f"# 更新日志 - {version}\n\n"
        content += f"**发布日期**: {datetime.now().strftime('%Y-%m-%d')}\n\n"
        content += f"**状态**: {version_info.status}\n\n"
        
        if version_info.parent_version:
            content += f"**父版本**: {version_info.parent_version}\n\n"
        
        if version_info.tags:
            content += f"**标签**: {', '.join(version_info.tags)}\n\n"
        
        content += "## 变更内容\n\n"
        
        for change in changes:
            content += f"- {change}\n"
        
        content += f"\n---\n*文档生成时间: {datetime.now().isoformat()}*\n"
        
        with open(changelog_file, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"变更日志已生成: {changelog_file}")
        return True
    
    def get_workflow_stage_info(self, stage: WorkflowStage) -> Optional[WorkflowStageInfo]:
        """获取工作流程阶段信息"""
        return self.WORKFLOW_STAGE_CONFIG.get(stage.value)
    
    def get_workflow_progress(self, version: str) -> Dict[str, Any]:
        """获取版本的工作流程进度"""
        version_info = self.get_version_info(version)
        if not version_info:
            return {}
        
        progress = {}
        for stage in WorkflowStage:
            stage_dir = self.WORKFLOW_DIR / version / stage.value
            stage_info = self.WORKFLOW_STAGE_CONFIG.get(stage.value)
            
            if stage_dir.exists():
                files = list(stage_dir.iterdir())
                progress[stage.value] = {
                    "display_name": stage_info.display_name if stage_info else stage.value,
                    "order": stage_info.order if stage_info else 0,
                    "document_count": len([f for f in files if f.is_file()]),
                    "required_docs": stage_info.required_docs if stage_info else [],
                    "completed": len([f for f in files if f.is_file()]) > 0
                }
            else:
                progress[stage.value] = {
                    "display_name": stage_info.display_name if stage_info else stage.value,
                    "order": stage_info.order if stage_info else 0,
                    "document_count": 0,
                    "required_docs": stage_info.required_docs if stage_info else [],
                    "completed": False
                }
        
        return progress
    
    def create_workflow_document(self, version: str, stage: WorkflowStage,
                                doc_name: str, content: str,
                                tags: Optional[List[str]] = None,
                                author: Optional[str] = None) -> bool:
        """创建工作流程文档"""
        version_info = self.get_version_info(version)
        if not version_info:
            print(f"版本 {version} 不存在")
            return False
        
        stage_dir = self.WORKFLOW_DIR / version / stage.value
        stage_dir.mkdir(parents=True, exist_ok=True)
        
        doc_path = stage_dir / doc_name
        
        with open(doc_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        metadata = self._load_metadata()
        
        doc_meta = asdict(DocumentMetadata(
            name=doc_name,
            doc_type=None,
            workflow_stage=stage.value,
            version=version,
            created_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat(),
            file_path=str(doc_path),
            size_bytes=doc_path.stat().st_size,
            checksum=self._calculate_checksum(doc_path),
            history=[{
                "action": "created",
                "timestamp": datetime.now().isoformat()
            }],
            tags=tags or [],
            author=author
        ))
        metadata.setdefault("documents", []).append(doc_meta)
        self._save_metadata(metadata)
        
        print(f"工作流程文档 {doc_name} 已创建于 {stage.value} 阶段")
        return True
    
    def export_version_summary(self, version: str) -> Dict[str, Any]:
        """导出版本摘要"""
        version_info = self.get_version_info(version)
        if not version_info:
            return {}

        documents = self.list_documents(version=version)
        workflow_progress = self.get_workflow_progress(version)
        relations = self.get_version_relations(version)

        doc_summary = {}
        for doc in documents:
            key = doc.workflow_stage or doc.doc_type or "general"
            if key not in doc_summary:
                doc_summary[key] = []
            doc_summary[key].append({
                "name": doc.name,
                "size_bytes": doc.size_bytes,
                "updated_at": doc.updated_at
            })

        return {
            "version": version,
            "info": asdict(version_info),
            "document_summary": doc_summary,
            "workflow_progress": workflow_progress,
            "relations": [asdict(r) for r in relations],
            "total_documents": len(documents),
            "exported_at": datetime.now().isoformat()
        }

    def store_document_by_workflow(
        self,
        version: str,
        source_path: str,
        workflow_stage: WorkflowStage,
        doc_name: Optional[str] = None,
        tags: Optional[List[str]] = None,
        author: Optional[str] = None,
        description: Optional[str] = None,
        auto_snapshot: bool = True
    ) -> bool:
        """
        按工作流程阶段存储文档
        
        Args:
            version: 版本号
            source_path: 源文件路径
            workflow_stage: 工作流程阶段
            doc_name: 文档名称
            tags: 标签列表
            author: 作者
            description: 描述
            auto_snapshot: 是否自动创建快照
            
        Returns:
            是否成功
        """
        version_info = self.get_version_info(version)
        if not version_info:
            print(f"版本 {version} 不存在")
            return False

        source = Path(source_path)
        if not source.exists():
            print(f"源文件 {source_path} 不存在")
            return False

        stage_dir = self.WORKFLOW_DIR / version / workflow_stage.value
        stage_dir.mkdir(parents=True, exist_ok=True)

        doc_name = doc_name or source.name
        target_path = stage_dir / doc_name

        if target_path.exists() and auto_snapshot:
            self._create_document_snapshot(
                version=version,
                doc_path=str(target_path),
                workflow_stage=workflow_stage.value,
                description="自动快照 - 文档更新前"
            )

        shutil.copy2(str(source), str(target_path))
        checksum = self._calculate_checksum(target_path)

        metadata = self._load_metadata()
        
        existing_doc = None
        for doc in metadata.get("documents", []):
            if doc.get("file_path") == str(target_path):
                existing_doc = doc
                break

        history_entry = {
            "action": "created" if not existing_doc else "updated",
            "timestamp": datetime.now().isoformat(),
            "workflow_stage": workflow_stage.value,
            "source": str(source),
            "checksum": checksum
        }

        if existing_doc:
            existing_doc["updated_at"] = datetime.now().isoformat()
            existing_doc["checksum"] = checksum
            existing_doc["size_bytes"] = target_path.stat().st_size
            existing_doc["history"].append(history_entry)
            if tags:
                existing_doc["tags"] = list(set(existing_doc.get("tags", []) + tags))
        else:
            doc_meta = asdict(DocumentMetadata(
                name=doc_name,
                doc_type=None,
                workflow_stage=workflow_stage.value,
                version=version,
                created_at=datetime.now().isoformat(),
                updated_at=datetime.now().isoformat(),
                file_path=str(target_path),
                size_bytes=target_path.stat().st_size,
                checksum=checksum,
                history=[history_entry],
                tags=tags or [],
                author=author,
                description=description
            ))
            metadata.setdefault("documents", []).append(doc_meta)

        self._save_metadata(metadata)
        
        stage_info = self.WORKFLOW_STAGE_CONFIG.get(workflow_stage.value)
        print(f"文档 {doc_name} 已存储到版本 {version} 的 {stage_info.display_name if stage_info else workflow_stage.value} 阶段")
        return True

    def get_documents_by_workflow_stage(
        self,
        version: str,
        workflow_stage: WorkflowStage
    ) -> List[DocumentMetadata]:
        """
        按工作流程阶段获取文档列表
        
        Args:
            version: 版本号
            workflow_stage: 工作流程阶段
            
        Returns:
            文档元数据列表
        """
        return self.list_documents(version=version, workflow_stage=workflow_stage)

    def get_workflow_documents_summary(
        self,
        version: str
    ) -> Dict[str, Dict[str, Any]]:
        """
        获取版本的工作流程文档摘要
        
        Args:
            version: 版本号
            
        Returns:
            各阶段的文档摘要
        """
        summary = {}
        
        for stage in WorkflowStage:
            docs = self.get_documents_by_workflow_stage(version, stage)
            stage_info = self.WORKFLOW_STAGE_CONFIG.get(stage.value)
            
            summary[stage.value] = {
                "display_name": stage_info.display_name if stage_info else stage.value,
                "order": stage_info.order if stage_info else 0,
                "document_count": len(docs),
                "total_size": sum(d.size_bytes for d in docs),
                "documents": [
                    {
                        "name": d.name,
                        "size_bytes": d.size_bytes,
                        "updated_at": d.updated_at,
                        "tags": d.tags
                    }
                    for d in docs
                ],
                "required_docs": stage_info.required_docs if stage_info else [],
                "completion_status": self._calculate_stage_completion(docs, stage_info)
            }

        return summary

    def _calculate_stage_completion(
        self,
        docs: List[DocumentMetadata],
        stage_info: Optional[WorkflowStageInfo]
    ) -> Dict[str, Any]:
        """计算阶段完成状态"""
        if not stage_info:
            return {"status": "unknown", "percentage": 0}

        required = stage_info.required_docs
        if not required:
            return {"status": "complete" if docs else "empty", "percentage": 100 if docs else 0}

        doc_names = [d.name.lower() for d in docs]
        matched = sum(1 for req in required if any(req.lower() in name for name in doc_names))
        percentage = int((matched / len(required)) * 100)

        if percentage == 100:
            status = "complete"
        elif percentage > 0:
            status = "partial"
        else:
            status = "empty"

        return {
            "status": status,
            "percentage": percentage,
            "matched_required": matched,
            "total_required": len(required)
        }

    def _create_document_snapshot(
        self,
        version: str,
        doc_path: str,
        workflow_stage: Optional[str] = None,
        description: Optional[str] = None,
        is_auto_snapshot: bool = False
    ) -> Optional[DocumentVersionSnapshot]:
        """
        创建文档快照
        
        Args:
            version: 版本号
            doc_path: 文档路径
            workflow_stage: 工作流程阶段
            description: 描述
            is_auto_snapshot: 是否自动快照
            
        Returns:
            快照信息
        """
        source = Path(doc_path)
        if not source.exists():
            return None

        timestamp = datetime.now()
        snapshot_id = f"snap_{timestamp.strftime('%Y%m%d_%H%M%S')}_{hashlib.md5(str(source).encode()).hexdigest()[:8]}"
        
        snapshot_version_dir = self.SNAPSHOT_DIR / version
        snapshot_version_dir.mkdir(parents=True, exist_ok=True)
        
        snapshot_file = snapshot_version_dir / f"{snapshot_id}{source.suffix}"
        shutil.copy2(str(source), str(snapshot_file))

        checksum = self._calculate_checksum(snapshot_file)

        snapshot = DocumentVersionSnapshot(
            snapshot_id=snapshot_id,
            version=version,
            doc_name=source.name,
            doc_path=str(source),
            created_at=timestamp.isoformat(),
            checksum=checksum,
            size_bytes=snapshot_file.stat().st_size,
            description=description,
            is_auto_snapshot=is_auto_snapshot,
            workflow_stage=workflow_stage
        )

        snapshot_meta_file = snapshot_version_dir / "snapshots_meta.json"
        snapshots_meta = {}
        if snapshot_meta_file.exists():
            with open(snapshot_meta_file, 'r', encoding='utf-8') as f:
                snapshots_meta = json.load(f)

        doc_key = source.name
        if doc_key not in snapshots_meta:
            snapshots_meta[doc_key] = []
        snapshots_meta[doc_key].append(asdict(snapshot))

        with open(snapshot_meta_file, 'w', encoding='utf-8') as f:
            json.dump(snapshots_meta, f, ensure_ascii=False, indent=2)

        return snapshot

    def get_document_snapshots(
        self,
        version: str,
        doc_name: str
    ) -> List[DocumentVersionSnapshot]:
        """
        获取文档的所有快照
        
        Args:
            version: 版本号
            doc_name: 文档名称
            
        Returns:
            快照列表
        """
        snapshot_meta_file = self.SNAPSHOT_DIR / version / "snapshots_meta.json"
        
        if not snapshot_meta_file.exists():
            return []

        with open(snapshot_meta_file, 'r', encoding='utf-8') as f:
            snapshots_meta = json.load(f)

        snapshots = []
        for snap_data in snapshots_meta.get(doc_name, []):
            snapshots.append(DocumentVersionSnapshot(**snap_data))

        return sorted(snapshots, key=lambda x: x.created_at, reverse=True)

    def set_history_retention_policy(
        self,
        version: str,
        policy: HistoryRetentionPolicy
    ) -> bool:
        """
        设置历史版本保留策略
        
        Args:
            version: 版本号
            policy: 保留策略
            
        Returns:
            是否成功
        """
        metadata = self._load_metadata()
        version_data = metadata.get("versions", {}).get(version)
        
        if not version_data:
            print(f"版本 {version} 不存在")
            return False

        version_data["retention_policy"] = asdict(policy)
        self._save_metadata(metadata)
        
        print(f"版本 {version} 的历史保留策略已设置")
        return True

    def get_history_retention_policy(
        self,
        version: str
    ) -> HistoryRetentionPolicy:
        """
        获取历史版本保留策略
        
        Args:
            version: 版本号
            
        Returns:
            保留策略
        """
        metadata = self._load_metadata()
        version_data = metadata.get("versions", {}).get(version)
        
        if version_data and "retention_policy" in version_data:
            return HistoryRetentionPolicy(**version_data["retention_policy"])
        
        return HistoryRetentionPolicy()

    def cleanup_old_history_versions(
        self,
        version: str,
        doc_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        清理旧的历史版本
        
        Args:
            version: 版本号
            doc_name: 文档名称（可选，不指定则清理所有文档）
            
        Returns:
            清理结果
        """
        policy = self.get_history_retention_policy(version)
        result = {
            "version": version,
            "cleaned_snapshots": 0,
            "cleaned_history": 0,
            "freed_space": 0,
            "errors": []
        }

        snapshot_meta_file = self.SNAPSHOT_DIR / version / "snapshots_meta.json"
        if not snapshot_meta_file.exists():
            return result

        with open(snapshot_meta_file, 'r', encoding='utf-8') as f:
            snapshots_meta = json.load(f)

        cutoff_date = datetime.now() - timedelta(days=policy.max_age_days)
        
        docs_to_process = [doc_name] if doc_name else list(snapshots_meta.keys())
        
        for doc_key in docs_to_process:
            if doc_key not in snapshots_meta:
                continue

            snapshots = snapshots_meta[doc_key]
            valid_snapshots = []
            
            for snap_data in snapshots:
                snap_date = datetime.fromisoformat(snap_data["created_at"])
                snap_path = self.SNAPSHOT_DIR / version / f"{snap_data['snapshot_id']}{Path(snap_data['doc_path']).suffix}"
                
                should_keep = (
                    snap_date >= cutoff_date or
                    (policy.keep_tagged_versions and snap_data.get("tags")) or
                    (len(valid_snapshots) < policy.max_versions)
                )

                if should_keep:
                    valid_snapshots.append(snap_data)
                else:
                    if snap_path.exists():
                        result["freed_space"] += snap_path.stat().st_size
                        snap_path.unlink()
                        result["cleaned_snapshots"] += 1

            snapshots_meta[doc_key] = valid_snapshots

        with open(snapshot_meta_file, 'w', encoding='utf-8') as f:
            json.dump(snapshots_meta, f, ensure_ascii=False, indent=2)

        return result

    def generate_diff_report(
        self,
        file1: str,
        file2: str,
        include_recommendations: bool = True
    ) -> DiffReport:
        """
        生成详细的差异报告
        
        Args:
            file1: 第一个文件路径
            file2: 第二个文件路径
            include_recommendations: 是否包含建议
            
        Returns:
            差异报告
        """
        path1 = Path(file1)
        path2 = Path(file2)

        report_id = f"diff_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{hashlib.md5((str(path1) + str(path2)).encode()).hexdigest()[:8]}"

        file1_info = {
            "path": str(path1),
            "name": path1.name,
            "exists": path1.exists(),
            "size": path1.stat().st_size if path1.exists() else 0,
            "modified": datetime.fromtimestamp(path1.stat().st_mtime).isoformat() if path1.exists() else None
        }

        file2_info = {
            "path": str(path2),
            "name": path2.name,
            "exists": path2.exists(),
            "size": path2.stat().st_size if path2.exists() else 0,
            "modified": datetime.fromtimestamp(path2.stat().st_mtime).isoformat() if path2.exists() else None
        }

        diff_result = None
        summary = {}
        recommendations = []

        if path1.exists() and path2.exists():
            diff_result = self.compare_documents(str(path1), str(path2))
            
            summary = {
                "similarity_percentage": round(diff_result.similarity_ratio * 100, 2),
                "total_changes": diff_result.modified_lines,
                "added_lines": diff_result.added_lines,
                "removed_lines": diff_result.removed_lines,
                "change_type": self._classify_change_type(diff_result)
            }

            if include_recommendations:
                recommendations = self._generate_diff_recommendations(diff_result)

        report = DiffReport(
            report_id=report_id,
            generated_at=datetime.now().isoformat(),
            file1_info=file1_info,
            file2_info=file2_info,
            diff_result=diff_result,
            summary=summary,
            recommendations=recommendations
        )

        self._save_diff_report(report)

        return report

    def _classify_change_type(self, diff_result: DiffResult) -> str:
        """分类变更类型"""
        if diff_result.similarity_ratio > 0.95:
            return "minor"
        elif diff_result.similarity_ratio > 0.7:
            return "moderate"
        elif diff_result.similarity_ratio > 0.3:
            return "major"
        else:
            return "significant"

    def _generate_diff_recommendations(self, diff_result: DiffResult) -> List[str]:
        """生成差异建议"""
        recommendations = []

        if diff_result.added_lines > diff_result.removed_lines * 2:
            recommendations.append("新增内容较多，建议检查是否需要更新相关文档")

        if diff_result.removed_lines > diff_result.added_lines * 2:
            recommendations.append("删除内容较多，建议确认是否有遗漏的重要信息")

        if diff_result.similarity_ratio < 0.5:
            recommendations.append("文档变化较大，建议进行全面审查")

        if diff_result.similarity_ratio > 0.95:
            recommendations.append("文档变化较小，可快速审核")

        return recommendations

    def _save_diff_report(self, report: DiffReport):
        """保存差异报告"""
        self.DIFF_REPORT_DIR.mkdir(parents=True, exist_ok=True)
        
        report_file = self.DIFF_REPORT_DIR / f"{report.report_id}.json"
        
        report_data = asdict(report)
        if report.diff_result:
            report_data["diff_result"] = asdict(report.diff_result)

        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, ensure_ascii=False, indent=2)

    def get_diff_report(self, report_id: str) -> Optional[DiffReport]:
        """获取差异报告"""
        report_file = self.DIFF_REPORT_DIR / f"{report_id}.json"
        
        if not report_file.exists():
            return None

        with open(report_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        diff_result = None
        if data.get("diff_result"):
            diff_result = DiffResult(**data["diff_result"])

        return DiffReport(
            report_id=data["report_id"],
            generated_at=data["generated_at"],
            file1_info=data["file1_info"],
            file2_info=data["file2_info"],
            diff_result=diff_result,
            summary=data.get("summary", {}),
            recommendations=data.get("recommendations", [])
        )

    def rollback_document(
        self,
        version: str,
        doc_name: str,
        target_snapshot_id: Optional[str] = None,
        create_backup: bool = True
    ) -> RollbackResult:
        """
        回滚文档到指定快照或上一版本
        
        Args:
            version: 版本号
            doc_name: 文档名称
            target_snapshot_id: 目标快照ID（可选，不指定则回滚到最近快照）
            create_backup: 是否创建备份
            
        Returns:
            回滚结果
        """
        metadata = self._load_metadata()
        
        current_doc = None
        for doc in metadata.get("documents", []):
            if doc.get("name") == doc_name and doc.get("version") == version:
                current_doc = doc
                break

        if not current_doc:
            return RollbackResult(
                success=False,
                version=version,
                doc_name=doc_name,
                rollback_time=datetime.now().isoformat(),
                errors=[f"未找到文档 {doc_name} 在版本 {version}"]
            )

        current_path = Path(current_doc["file_path"])
        
        snapshots = self.get_document_snapshots(version, doc_name)
        if not snapshots:
            return RollbackResult(
                success=False,
                version=version,
                doc_name=doc_name,
                rollback_time=datetime.now().isoformat(),
                errors=[f"未找到文档 {doc_name} 的快照"]
            )

        target_snapshot = None
        if target_snapshot_id:
            for snap in snapshots:
                if snap.snapshot_id == target_snapshot_id:
                    target_snapshot = snap
                    break
            if not target_snapshot:
                return RollbackResult(
                    success=False,
                    version=version,
                    doc_name=doc_name,
                    rollback_time=datetime.now().isoformat(),
                    errors=[f"未找到快照 {target_snapshot_id}"]
                )
        else:
            target_snapshot = snapshots[0]

        backup_snapshot_id = None
        if create_backup and current_path.exists():
            backup_snapshot = self._create_document_snapshot(
                version=version,
                doc_path=str(current_path),
                workflow_stage=current_doc.get("workflow_stage"),
                description="回滚前自动备份",
                is_auto_snapshot=True
            )
            if backup_snapshot:
                backup_snapshot_id = backup_snapshot.snapshot_id

        snapshot_file = self.SNAPSHOT_DIR / version / f"{target_snapshot.snapshot_id}{Path(target_snapshot.doc_path).suffix}"
        
        if not snapshot_file.exists():
            return RollbackResult(
                success=False,
                version=version,
                doc_name=doc_name,
                rollback_time=datetime.now().isoformat(),
                errors=[f"快照文件不存在: {snapshot_file}"],
                backup_snapshot_id=backup_snapshot_id
            )

        shutil.copy2(str(snapshot_file), str(current_path))

        current_doc["checksum"] = self._calculate_checksum(current_path)
        current_doc["updated_at"] = datetime.now().isoformat()
        current_doc["history"].append({
            "action": "rollback",
            "timestamp": datetime.now().isoformat(),
            "from_snapshot": target_snapshot.snapshot_id,
            "backup_snapshot": backup_snapshot_id
        })

        self._save_metadata(metadata)

        return RollbackResult(
            success=True,
            version=version,
            doc_name=doc_name,
            rollback_time=datetime.now().isoformat(),
            backup_snapshot_id=backup_snapshot_id,
            warnings=[] if create_backup else ["未创建回滚前备份"]
        )

    def rollback_version(
        self,
        version: str,
        target_version: str,
        doc_types: Optional[List[DocType]] = None,
        workflow_stages: Optional[List[WorkflowStage]] = None,
        create_backups: bool = True
    ) -> Dict[str, RollbackResult]:
        """
        回滚整个版本到目标版本
        
        Args:
            version: 当前版本
            target_version: 目标版本
            doc_types: 文档类型列表（可选）
            workflow_stages: 工作流程阶段列表（可选）
            create_backups: 是否创建备份
            
        Returns:
            各文档的回滚结果
        """
        results = {}
        
        current_docs = self.list_documents(version=version)
        
        for doc in current_docs:
            if doc_types and doc.doc_type:
                if DocType(doc.doc_type) not in doc_types:
                    continue
            if workflow_stages and doc.workflow_stage:
                if WorkflowStage(doc.workflow_stage) not in workflow_stages:
                    continue

            target_snapshots = self.get_document_snapshots(target_version, doc.name)
            if target_snapshots:
                result = self.rollback_document(
                    version=version,
                    doc_name=doc.name,
                    target_snapshot_id=target_snapshots[0].snapshot_id,
                    create_backup=create_backups
                )
                results[doc.name] = result

        return results

    def get_rollback_history(
        self,
        version: str,
        doc_name: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        获取回滚历史
        
        Args:
            version: 版本号
            doc_name: 文档名称（可选）
            
        Returns:
            回滚历史列表
        """
        metadata = self._load_metadata()
        rollback_history = []

        for doc in metadata.get("documents", []):
            if doc.get("version") != version:
                continue
            if doc_name and doc.get("name") != doc_name:
                continue

            for entry in doc.get("history", []):
                if entry.get("action") == "rollback":
                    rollback_history.append({
                        "doc_name": doc.get("name"),
                        "timestamp": entry.get("timestamp"),
                        "from_snapshot": entry.get("from_snapshot"),
                        "backup_snapshot": entry.get("backup_snapshot")
                    })

        return sorted(rollback_history, key=lambda x: x["timestamp"], reverse=True)


class TestDocVersionManager(unittest.TestCase):
    """文档版本管理器测试类"""
    
    @classmethod
    def setUpClass(cls):
        """测试类初始化"""
        cls.test_base = Path(__file__).parent / "test_docs"
        cls.test_base.mkdir(parents=True, exist_ok=True)
        
        cls.original_base = DocVersionManager.BASE_DIR
        DocVersionManager.BASE_DIR = cls.test_base
        DocVersionManager.DOCS_DIR = cls.test_base / "docs"
        DocVersionManager.LIBS_DIR = cls.test_base / "docs" / "libs"
        DocVersionManager.REPORTS_DIR = cls.test_base / "docs" / "reports"
        DocVersionManager.WORKFLOW_DIR = cls.test_base / "docs" / "workflow"
        DocVersionManager.HISTORY_DIR = cls.test_base / "docs" / "history"
        DocVersionManager.VERSION_FILE = cls.test_base / "docs" / "version.json"
        DocVersionManager.METADATA_FILE = cls.test_base / "docs" / "metadata.json"
        DocVersionManager.BRANCH_FILE = cls.test_base / "docs" / "branches.json"
    
    @classmethod
    def tearDownClass(cls):
        """测试类清理"""
        DocVersionManager.BASE_DIR = cls.original_base
        if cls.test_base.exists():
            shutil.rmtree(str(cls.test_base))
    
    def setUp(self):
        """每个测试前的初始化"""
        if self.test_base.exists():
            shutil.rmtree(str(self.test_base))
        self.test_base.mkdir(parents=True, exist_ok=True)
        self.manager = DocVersionManager()
    
    def test_version_number_parsing(self):
        """测试版本号解析"""
        ver = VersionNumber.parse("v1.2.3")
        self.assertIsNotNone(ver)
        self.assertEqual(ver.major, 1)
        self.assertEqual(ver.minor, 2)
        self.assertEqual(ver.patch, 3)
        self.assertEqual(str(ver), "v1.2.3")
        
        ver_prerelease = VersionNumber.parse("v2.0.0-beta")
        self.assertIsNotNone(ver_prerelease)
        self.assertEqual(ver_prerelease.prerelease, "beta")
        
        ver_invalid = VersionNumber.parse("invalid")
        self.assertIsNone(ver_invalid)
    
    def test_version_comparison(self):
        """测试版本号比较"""
        v1 = VersionNumber.parse("v1.0.0")
        v2 = VersionNumber.parse("v1.0.1")
        v3 = VersionNumber.parse("v1.1.0")
        v4 = VersionNumber.parse("v2.0.0")
        
        self.assertTrue(v1 < v2)
        self.assertTrue(v2 < v3)
        self.assertTrue(v3 < v4)
        self.assertTrue(v1 < v4)
        
        v_alpha = VersionNumber.parse("v1.0.0-alpha")
        v_beta = VersionNumber.parse("v1.0.0-beta")
        v_stable = VersionNumber.parse("v1.0.0")
        
        self.assertTrue(v_alpha < v_beta)
        self.assertTrue(v_beta < v_stable)
    
    def test_version_bumping(self):
        """测试版本号递增"""
        v = VersionNumber.parse("v1.2.3")
        
        self.assertEqual(str(v.bump_major()), "v2.0.0")
        self.assertEqual(str(v.bump_minor()), "v1.3.0")
        self.assertEqual(str(v.bump_patch()), "v1.2.4")
    
    def test_version_number_hash(self):
        """测试版本号哈希"""
        v1 = VersionNumber.parse("v1.0.0")
        v2 = VersionNumber.parse("v1.0.0")
        v3 = VersionNumber.parse("v1.0.1")
        
        self.assertEqual(hash(v1), hash(v2))
        self.assertNotEqual(hash(v1), hash(v3))
        
        version_set = {v1, v2, v3}
        self.assertEqual(len(version_set), 2)
    
    def test_create_version(self):
        """测试创建版本"""
        result = self.manager.create_version("v1.0.0", "初始版本")
        self.assertTrue(result)
        
        version_info = self.manager.get_version_info("v1.0.0")
        self.assertIsNotNone(version_info)
        self.assertEqual(version_info.version, "v1.0.0")
        self.assertEqual(version_info.description, "初始版本")
        self.assertEqual(version_info.status, VersionStatus.DRAFT.value)
        
        result = self.manager.create_version("v1.0.0", "重复版本")
        self.assertFalse(result)
    
    def test_version_status_management(self):
        """测试版本状态管理"""
        self.manager.create_version("v1.0.0")
        
        result = self.manager.update_version_status("v1.0.0", VersionStatus.RELEASED)
        self.assertTrue(result)
        
        version_info = self.manager.get_version_info("v1.0.0")
        self.assertEqual(version_info.status, VersionStatus.RELEASED.value)
        
        result = self.manager.update_version_status("v1.0.0", VersionStatus.DEPRECATED)
        self.assertTrue(result)
        
        version_info = self.manager.get_version_info("v1.0.0")
        self.assertEqual(version_info.status, VersionStatus.DEPRECATED.value)
    
    def test_get_versions_by_status(self):
        """测试按状态获取版本"""
        self.manager.create_version("v1.0.0")
        self.manager.create_version("v1.1.0")
        self.manager.create_version("v2.0.0")
        
        self.manager.update_version_status("v1.0.0", VersionStatus.RELEASED)
        self.manager.update_version_status("v1.1.0", VersionStatus.RELEASED)
        
        released = self.manager.get_versions_by_status(VersionStatus.RELEASED)
        self.assertEqual(len(released), 2)
        
        draft = self.manager.get_versions_by_status(VersionStatus.DRAFT)
        self.assertEqual(len(draft), 1)
    
    def test_version_iteration(self):
        """测试版本迭代"""
        self.manager.create_version("v1.0.0")
        self.manager.create_version("v1.1.0")
        self.manager.create_version("v2.0.0")
        
        next_patch = self.manager.get_next_version("patch")
        self.assertEqual(next_patch, "v2.0.1")
        
        next_minor = self.manager.get_next_version("minor")
        self.assertEqual(next_minor, "v2.1.0")
        
        next_major = self.manager.get_next_version("major")
        self.assertEqual(next_major, "v3.0.0")
    
    def test_sorted_versions(self):
        """测试版本排序"""
        self.manager.create_version("v2.0.0")
        self.manager.create_version("v1.0.0")
        self.manager.create_version("v1.1.0")
        
        sorted_versions = self.manager.get_sorted_versions()
        self.assertEqual(sorted_versions, ["v1.0.0", "v1.1.0", "v2.0.0"])
    
    def test_workflow_stage_directories(self):
        """测试工作流程阶段目录"""
        self.manager.create_version("v1.0.0")
        
        for stage in WorkflowStage:
            stage_dir = DocVersionManager.WORKFLOW_DIR / "v1.0.0" / stage.value
            self.assertTrue(stage_dir.exists())
    
    def test_workflow_stage_info(self):
        """测试工作流程阶段信息"""
        stage_info = self.manager.get_workflow_stage_info(WorkflowStage.DESIGN)
        self.assertIsNotNone(stage_info)
        self.assertEqual(stage_info.display_name, "设计阶段")
        self.assertEqual(stage_info.order, 2)
    
    def test_workflow_progress(self):
        """测试工作流程进度"""
        self.manager.create_version("v1.0.0")
        
        test_file = self.test_base / "design_doc.txt"
        test_file.write_text("设计文档内容", encoding='utf-8')
        
        self.manager.add_document(
            version="v1.0.0",
            source_path=str(test_file),
            workflow_stage=WorkflowStage.DESIGN
        )
        
        progress = self.manager.get_workflow_progress("v1.0.0")
        self.assertIn("design", progress)
        self.assertEqual(progress["design"]["document_count"], 1)
        self.assertTrue(progress["design"]["completed"])
    
    def test_add_document_with_workflow_stage(self):
        """测试添加工作流程阶段文档"""
        self.manager.create_version("v1.0.0")
        
        test_file = self.test_base / "test_doc.txt"
        test_file.write_text("测试内容", encoding='utf-8')
        
        result = self.manager.add_document(
            version="v1.0.0",
            source_path=str(test_file),
            workflow_stage=WorkflowStage.DESIGN,
            doc_name="design_doc.txt",
            tags=["重要", "设计"],
            author="测试作者"
        )
        self.assertTrue(result)
        
        docs = self.manager.list_documents(version="v1.0.0", workflow_stage=WorkflowStage.DESIGN)
        self.assertEqual(len(docs), 1)
        self.assertEqual(docs[0].workflow_stage, "design")
        self.assertIn("重要", docs[0].tags)
        self.assertEqual(docs[0].author, "测试作者")
    
    def test_create_workflow_document(self):
        """测试创建工作流程文档"""
        self.manager.create_version("v1.0.0")
        
        result = self.manager.create_workflow_document(
            version="v1.0.0",
            stage=WorkflowStage.REQUIREMENTS,
            doc_name="需求文档.md",
            content="# 需求文档\n\n这是需求内容。",
            tags=["需求"],
            author="产品经理"
        )
        self.assertTrue(result)
        
        docs = self.manager.list_documents(version="v1.0.0", workflow_stage=WorkflowStage.REQUIREMENTS)
        self.assertEqual(len(docs), 1)
    
    def test_document_history(self):
        """测试文档历史版本"""
        self.manager.create_version("v1.0.0")
        
        test_file = self.test_base / "test_history.txt"
        test_file.write_text("版本1", encoding='utf-8')
        
        self.manager.save_document_history("v1.0.0", str(test_file), "初始版本")
        
        test_file.write_text("版本2", encoding='utf-8')
        self.manager.save_document_history("v1.0.0", str(test_file), "更新内容")
        
        history = self.manager.get_document_history("v1.0.0", "test_history.txt")
        self.assertEqual(len(history), 2)
        self.assertEqual(history[0]["change_description"], "初始版本")
        self.assertEqual(history[1]["change_description"], "更新内容")
    
    def test_restore_document_version(self):
        """测试恢复文档历史版本"""
        self.manager.create_version("v1.0.0")
        
        test_file = self.test_base / "restore_test.txt"
        test_file.write_text("原始内容", encoding='utf-8')
        
        self.manager.add_document(
            version="v1.0.0",
            source_path=str(test_file),
            workflow_stage=WorkflowStage.DESIGN,
            doc_name="restore_test.txt"
        )
        
        self.manager.save_document_history("v1.0.0", str(DocVersionManager.WORKFLOW_DIR / "v1.0.0" / "design" / "restore_test.txt"))
        
        test_file.write_text("修改后的内容", encoding='utf-8')
        shutil.copy2(str(test_file), str(DocVersionManager.WORKFLOW_DIR / "v1.0.0" / "design" / "restore_test.txt"))
        
        history = self.manager.get_document_history("v1.0.0", "restore_test.txt")
        self.assertGreater(len(history), 0)
        
        history_file = history[0]["history_file"]
        result = self.manager.restore_document_version("v1.0.0", "restore_test.txt", history_file)
        self.assertTrue(result)
    
    def test_document_comparison(self):
        """测试文档比较"""
        file1 = self.test_base / "file1.txt"
        file2 = self.test_base / "file2.txt"
        
        file1.write_text("第一行\n第二行\n第三行", encoding='utf-8')
        file2.write_text("第一行\n修改的第二行\n第三行\n第四行", encoding='utf-8')
        
        diff_result = self.manager.compare_documents(str(file1), str(file2))
        
        self.assertGreater(diff_result.added_lines, 0)
        self.assertGreater(diff_result.removed_lines, 0)
        self.assertGreater(diff_result.modified_lines, 0)
        self.assertGreater(diff_result.similarity_ratio, 0)
        self.assertLess(diff_result.similarity_ratio, 1)
        self.assertGreater(len(diff_result.changes_summary), 0)
    
    def test_document_comparison_context_diff(self):
        """测试上下文差异比较"""
        file1 = self.test_base / "file1.txt"
        file2 = self.test_base / "file2.txt"
        
        file1.write_text("内容A\n内容B", encoding='utf-8')
        file2.write_text("内容A\n内容C", encoding='utf-8')
        
        diff_result = self.manager.compare_documents(str(file1), str(file2), diff_type="context")
        self.assertEqual(diff_result.diff_type, "context")
    
    def test_version_migration(self):
        """测试版本迁移"""
        self.manager.create_version("v1.0.0")
        self.manager.create_version("v2.0.0")
        
        test_file = self.test_base / "migrate_test.txt"
        test_file.write_text("迁移测试", encoding='utf-8')
        
        self.manager.add_document(
            version="v1.0.0",
            source_path=str(test_file),
            doc_type=DocType.API
        )
        
        result = self.manager.migrate_version("v1.0.0", "v2.0.0", doc_types=[DocType.API])
        self.assertTrue(result)
        
        docs_v2 = self.manager.list_documents(version="v2.0.0", doc_type=DocType.API)
        self.assertEqual(len(docs_v2), 1)
    
    def test_integrity_check(self):
        """测试完整性检查"""
        self.manager.create_version("v1.0.0")
        
        result = self.manager.check_integrity("v1.0.0")
        self.assertTrue(result.is_valid)
        
        test_file = self.test_base / "integrity_test.txt"
        test_file.write_text("完整性测试", encoding='utf-8')
        
        self.manager.add_document(
            version="v1.0.0",
            source_path=str(test_file),
            doc_type=DocType.API
        )
        
        result = self.manager.check_integrity("v1.0.0")
        self.assertTrue(result.is_valid)
        
        target_path = DocVersionManager.LIBS_DIR / "v1.0.0" / "api" / "integrity_test.txt"
        if target_path.exists():
            target_path.unlink()
        
        result = self.manager.check_integrity("v1.0.0")
        self.assertFalse(result.is_valid)
        self.assertGreater(len(result.missing_files), 0)
    
    def test_archive_and_restore(self):
        """测试归档和恢复"""
        self.manager.create_version("v1.0.0", "测试归档")
        
        result = self.manager.archive_version("v1.0.0")
        self.assertTrue(result)
        
        version_info = self.manager.get_version_info("v1.0.0")
        self.assertTrue(version_info.is_archived)
        self.assertEqual(version_info.status, VersionStatus.ARCHIVED.value)
        
        result = self.manager.restore_version("v1.0.0")
        self.assertTrue(result)
        
        version_info = self.manager.get_version_info("v1.0.0")
        self.assertFalse(version_info.is_archived)
        self.assertEqual(version_info.status, VersionStatus.DRAFT.value)
    
    def test_checksum_verification(self):
        """测试校验和验证"""
        self.manager.create_version("v1.0.0")
        
        test_file = self.test_base / "checksum_test.txt"
        test_file.write_text("校验和测试", encoding='utf-8')
        
        self.manager.add_document(
            version="v1.0.0",
            source_path=str(test_file),
            doc_type=DocType.API
        )
        
        docs = self.manager.list_documents(version="v1.0.0", doc_type=DocType.API)
        self.assertEqual(len(docs), 1)
        self.assertIsNotNone(docs[0].checksum)
        
        target_path = Path(docs[0].file_path)
        original_checksum = docs[0].checksum
        current_checksum = self.manager._calculate_checksum(target_path)
        self.assertEqual(original_checksum, current_checksum)
    
    def test_branch_creation(self):
        """测试分支创建"""
        self.manager.create_version("v1.0.0", "主版本")
        
        result = self.manager.create_branch("feature-x", "v1.0.0", "新功能分支")
        self.assertTrue(result)
        
        branches = self.manager.list_branches()
        feature_branches = [b for b in branches if b.name == "feature-x"]
        self.assertEqual(len(feature_branches), 1)
        self.assertEqual(feature_branches[0].base_version, "v1.0.0")
    
    def test_branch_switch(self):
        """测试分支切换"""
        self.manager.create_version("v1.0.0")
        self.manager.create_branch("develop", "v1.0.0")
        
        result = self.manager.switch_branch("develop")
        self.assertTrue(result)
        
        current_branch = self.manager.get_current_branch()
        self.assertEqual(current_branch, "develop")
    
    def test_branch_merge(self):
        """测试分支合并"""
        self.manager.create_version("v1.0.0")
        self.manager.create_version("v2.0.0")
        self.manager.create_branch("hotfix", "v1.0.0", "紧急修复")
        
        test_file = self.test_base / "hotfix_doc.txt"
        test_file.write_text("修复内容", encoding='utf-8')
        
        branch_version = f"v1.0.0-hotfix"
        self.manager.add_document(
            version=branch_version,
            source_path=str(test_file),
            doc_type=DocType.API
        )
        
        result = self.manager.merge_branch("hotfix", "v2.0.0", "合并紧急修复")
        self.assertTrue(result)
        
        branches = self.manager.list_branches()
        hotfix_branch = [b for b in branches if b.name == "hotfix"][0]
        self.assertTrue(hotfix_branch.is_merged)
    
    def test_version_relations(self):
        """测试版本关系"""
        self.manager.create_version("v1.0.0")
        self.manager.create_version("v2.0.0", parent_version="v1.0.0")
        
        result = self.manager.add_version_relation(
            "v2.0.0", "v1.0.0", 
            VersionRelation.SUCCESSOR, 
            "v2.0.0 是 v1.0.0 的后继版本"
        )
        self.assertTrue(result)
        
        relations = self.manager.get_version_relations("v2.0.0")
        self.assertGreater(len(relations), 0)
        
        parent_relations = self.manager.get_version_relations("v2.0.0", VersionRelation.PARENT)
        self.assertEqual(len(parent_relations), 1)
    
    def test_export_version_summary(self):
        """测试导出版本摘要"""
        self.manager.create_version("v1.0.0", "测试版本", tags=["release", "stable"])
        
        test_file = self.test_base / "summary_test.txt"
        test_file.write_text("摘要测试", encoding='utf-8')
        
        self.manager.add_document(
            version="v1.0.0",
            source_path=str(test_file),
            workflow_stage=WorkflowStage.DESIGN
        )
        
        summary = self.manager.export_version_summary("v1.0.0")
        
        self.assertIsNotNone(summary)
        self.assertEqual(summary["version"], "v1.0.0")
        self.assertIn("info", summary)
        self.assertIn("workflow_progress", summary)
        self.assertEqual(summary["total_documents"], 1)
    
    def test_list_documents_with_tags(self):
        """测试按标签列出文档"""
        self.manager.create_version("v1.0.0")
        
        test_file1 = self.test_base / "doc1.txt"
        test_file1.write_text("文档1", encoding='utf-8')
        
        test_file2 = self.test_base / "doc2.txt"
        test_file2.write_text("文档2", encoding='utf-8')
        
        self.manager.add_document(
            version="v1.0.0",
            source_path=str(test_file1),
            doc_type=DocType.API,
            tags=["重要", "核心"]
        )
        
        self.manager.add_document(
            version="v1.0.0",
            source_path=str(test_file2),
            doc_type=DocType.API,
            tags=["次要"]
        )
        
        docs = self.manager.list_documents(version="v1.0.0", tags=["重要"])
        self.assertEqual(len(docs), 1)
        
        docs = self.manager.list_documents(version="v1.0.0", tags=["重要", "核心"])
        self.assertEqual(len(docs), 1)
    
    def test_compare_history_versions(self):
        """测试比较历史版本"""
        import time
        self.manager.create_version("v1.0.0")
        
        test_file = self.test_base / "history_compare.txt"
        test_file.write_text("版本1内容", encoding='utf-8')
        
        self.manager.save_document_history("v1.0.0", str(test_file))
        history1 = self.manager.get_document_history("v1.0.0", "history_compare.txt")[0]
        
        time.sleep(1)
        test_file.write_text("版本2内容\n新增行\n另一新增行", encoding='utf-8')
        self.manager.save_document_history("v1.0.0", str(test_file))
        history2 = self.manager.get_document_history("v1.0.0", "history_compare.txt")[1]
        
        diff = self.manager.compare_history_versions(
            "v1.0.0", "history_compare.txt",
            history1["history_file"], history2["history_file"]
        )
        
        self.assertIsNotNone(diff)
        self.assertGreaterEqual(diff.added_lines, 0)
    
    def test_prerelease_version(self):
        """测试预发布版本"""
        v = VersionNumber.parse("v1.0.0")
        v_alpha = v.with_prerelease("alpha")
        v_beta = v.with_prerelease("beta")
        
        self.assertEqual(str(v_alpha), "v1.0.0-alpha")
        self.assertEqual(str(v_beta), "v1.0.0-beta")
        self.assertTrue(v_alpha < v_beta)
        self.assertTrue(v_beta < v)

    def test_store_document_by_workflow(self):
        """测试按工作流程阶段存储文档"""
        self.manager.create_version("v1.0.0")
        
        test_file = self.test_base / "workflow_doc.txt"
        test_file.write_text("工作流程文档内容", encoding='utf-8')
        
        result = self.manager.store_document_by_workflow(
            version="v1.0.0",
            source_path=str(test_file),
            workflow_stage=WorkflowStage.DESIGN,
            doc_name="设计文档.txt",
            tags=["设计", "重要"],
            author="测试作者"
        )
        self.assertTrue(result)
        
        docs = self.manager.get_documents_by_workflow_stage("v1.0.0", WorkflowStage.DESIGN)
        self.assertEqual(len(docs), 1)
        self.assertEqual(docs[0].workflow_stage, "design")

    def test_workflow_documents_summary(self):
        """测试工作流程文档摘要"""
        self.manager.create_version("v1.0.0")
        
        test_file = self.test_base / "summary_doc.txt"
        test_file.write_text("摘要测试文档", encoding='utf-8')
        
        self.manager.store_document_by_workflow(
            version="v1.0.0",
            source_path=str(test_file),
            workflow_stage=WorkflowStage.REQUIREMENTS
        )
        
        summary = self.manager.get_workflow_documents_summary("v1.0.0")
        self.assertIn("requirements", summary)
        self.assertEqual(summary["requirements"]["document_count"], 1)

    def test_document_snapshot(self):
        """测试文档快照功能"""
        self.manager.create_version("v1.0.0")
        
        test_file = self.test_base / "snapshot_doc.txt"
        test_file.write_text("快照测试内容", encoding='utf-8')
        
        self.manager.store_document_by_workflow(
            version="v1.0.0",
            source_path=str(test_file),
            workflow_stage=WorkflowStage.DESIGN,
            auto_snapshot=True
        )
        
        test_file.write_text("修改后的内容", encoding='utf-8')
        self.manager.store_document_by_workflow(
            version="v1.0.0",
            source_path=str(test_file),
            workflow_stage=WorkflowStage.DESIGN,
            auto_snapshot=True
        )
        
        snapshots = self.manager.get_document_snapshots("v1.0.0", "snapshot_doc.txt")
        self.assertGreater(len(snapshots), 0)

    def test_history_retention_policy(self):
        """测试历史版本保留策略"""
        self.manager.create_version("v1.0.0")
        
        policy = HistoryRetentionPolicy(
            max_versions=5,
            max_age_days=30,
            keep_tagged_versions=True
        )
        
        result = self.manager.set_history_retention_policy("v1.0.0", policy)
        self.assertTrue(result)
        
        retrieved_policy = self.manager.get_history_retention_policy("v1.0.0")
        self.assertEqual(retrieved_policy.max_versions, 5)
        self.assertEqual(retrieved_policy.max_age_days, 30)

    def test_generate_diff_report(self):
        """测试生成差异报告"""
        file1 = self.test_base / "diff_file1.txt"
        file2 = self.test_base / "diff_file2.txt"
        
        file1.write_text("原始内容\n第二行\n第三行", encoding='utf-8')
        file2.write_text("修改内容\n第二行\n第三行\n第四行", encoding='utf-8')
        
        report = self.manager.generate_diff_report(str(file1), str(file2))
        
        self.assertIsNotNone(report)
        self.assertIn("similarity_percentage", report.summary)
        self.assertGreater(len(report.recommendations), 0)

    def test_get_diff_report(self):
        """测试获取差异报告"""
        file1 = self.test_base / "get_diff1.txt"
        file2 = self.test_base / "get_diff2.txt"
        
        file1.write_text("内容A", encoding='utf-8')
        file2.write_text("内容B", encoding='utf-8')
        
        report = self.manager.generate_diff_report(str(file1), str(file2))
        
        retrieved = self.manager.get_diff_report(report.report_id)
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.report_id, report.report_id)

    def test_rollback_document(self):
        """测试文档回滚功能"""
        self.manager.create_version("v1.0.0")
        
        test_file = self.test_base / "rollback_doc.txt"
        test_file.write_text("原始内容", encoding='utf-8')
        
        self.manager.store_document_by_workflow(
            version="v1.0.0",
            source_path=str(test_file),
            workflow_stage=WorkflowStage.DESIGN,
            auto_snapshot=True
        )
        
        test_file.write_text("修改后的内容", encoding='utf-8')
        self.manager.store_document_by_workflow(
            version="v1.0.0",
            source_path=str(test_file),
            workflow_stage=WorkflowStage.DESIGN,
            auto_snapshot=True
        )
        
        snapshots = self.manager.get_document_snapshots("v1.0.0", "rollback_doc.txt")
        self.assertGreater(len(snapshots), 0)
        
        result = self.manager.rollback_document(
            version="v1.0.0",
            doc_name="rollback_doc.txt",
            create_backup=True
        )
        self.assertTrue(result.success)

    def test_rollback_history(self):
        """测试回滚历史记录"""
        self.manager.create_version("v1.0.0")
        
        test_file = self.test_base / "history_doc.txt"
        test_file.write_text("内容1", encoding='utf-8')
        
        self.manager.store_document_by_workflow(
            version="v1.0.0",
            source_path=str(test_file),
            workflow_stage=WorkflowStage.DESIGN,
            auto_snapshot=True
        )
        
        test_file.write_text("内容2", encoding='utf-8')
        self.manager.store_document_by_workflow(
            version="v1.0.0",
            source_path=str(test_file),
            workflow_stage=WorkflowStage.DESIGN,
            auto_snapshot=True
        )
        
        self.manager.rollback_document("v1.0.0", "history_doc.txt")
        
        history = self.manager.get_rollback_history("v1.0.0")
        self.assertGreater(len(history), 0)

    def test_cleanup_old_history(self):
        """测试清理旧历史版本"""
        self.manager.create_version("v1.0.0")
        
        policy = HistoryRetentionPolicy(
            max_versions=2,
            max_age_days=365,
            auto_cleanup=True
        )
        self.manager.set_history_retention_policy("v1.0.0", policy)
        
        test_file = self.test_base / "cleanup_doc.txt"
        for i in range(5):
            test_file.write_text(f"版本{i}", encoding='utf-8')
            self.manager.store_document_by_workflow(
                version="v1.0.0",
                source_path=str(test_file),
                workflow_stage=WorkflowStage.DESIGN,
                auto_snapshot=True
            )
        
        result = self.manager.cleanup_old_history_versions("v1.0.0", "cleanup_doc.txt")
        self.assertGreaterEqual(result["cleaned_snapshots"], 0)


def main():
    """主函数 - 命令行入口"""
    parser = argparse.ArgumentParser(description="文档版本管理器")
    subparsers = parser.add_subparsers(dest="command", help="可用命令")
    
    parser_current = subparsers.add_parser("current", help="获取当前版本")
    
    parser_set = subparsers.add_parser("set", help="设置当前版本")
    parser_set.add_argument("version", help="版本号")
    
    parser_create = subparsers.add_parser("create", help="创建新版本")
    parser_create.add_argument("version", help="版本号")
    parser_create.add_argument("-d", "--description", default="", help="版本描述")
    parser_create.add_argument("-p", "--parent", help="父版本号")
    parser_create.add_argument("-t", "--tags", nargs="*", help="版本标签")
    parser_create.add_argument("-s", "--status", 
                              choices=[s.value for s in VersionStatus],
                              default=VersionStatus.DRAFT.value, help="版本状态")
    
    parser_status = subparsers.add_parser("status", help="更新版本状态")
    parser_status.add_argument("version", help="版本号")
    parser_status.add_argument("status", choices=[s.value for s in VersionStatus], help="新状态")
    
    parser_list = subparsers.add_parser("list", help="列出所有版本")
    parser_list.add_argument("--all", action="store_true", help="包含已归档版本")
    parser_list.add_argument("--sort", action="store_true", help="按版本号排序")
    parser_list.add_argument("-s", "--status", choices=[s.value for s in VersionStatus],
                            help="按状态筛选")
    
    parser_info = subparsers.add_parser("info", help="查看版本详情")
    parser_info.add_argument("version", help="版本号")
    
    parser_next = subparsers.add_parser("next", help="获取下一个版本号")
    parser_next.add_argument("-t", "--type", choices=["major", "minor", "patch"], 
                            default="patch", help="版本递增类型")
    
    parser_compare_ver = subparsers.add_parser("compare-ver", help="比较两个版本号")
    parser_compare_ver.add_argument("v1", help="第一个版本号")
    parser_compare_ver.add_argument("v2", help="第二个版本号")
    
    parser_archive = subparsers.add_parser("archive", help="归档版本")
    parser_archive.add_argument("version", help="版本号")
    
    parser_restore = subparsers.add_parser("restore", help="恢复归档版本")
    parser_restore.add_argument("version", help="版本号")
    
    parser_delete = subparsers.add_parser("delete", help="删除版本")
    parser_delete.add_argument("version", help="版本号")
    parser_delete.add_argument("--force", action="store_true", help="强制删除当前版本")
    
    parser_branch = subparsers.add_parser("branch", help="分支管理")
    branch_sub = parser_branch.add_subparsers(dest="branch_cmd")
    
    branch_create = branch_sub.add_parser("create", help="创建分支")
    branch_create.add_argument("name", help="分支名称")
    branch_create.add_argument("-b", "--base", required=True, help="基础版本")
    branch_create.add_argument("-d", "--description", help="分支描述")
    
    branch_switch = branch_sub.add_parser("switch", help="切换分支")
    branch_switch.add_argument("name", help="分支名称")
    
    branch_merge = branch_sub.add_parser("merge", help="合并分支")
    branch_merge.add_argument("source", help="源分支名称")
    branch_merge.add_argument("-t", "--target", required=True, help="目标版本")
    branch_merge.add_argument("-m", "--message", help="合并说明")
    
    branch_list = branch_sub.add_parser("list", help="列出分支")
    
    parser_relation = subparsers.add_parser("relation", help="版本关系管理")
    relation_sub = parser_relation.add_subparsers(dest="relation_cmd")
    
    relation_add = relation_sub.add_parser("add", help="添加版本关系")
    relation_add.add_argument("version", help="版本号")
    relation_add.add_argument("related", help="关联版本")
    relation_add.add_argument("-t", "--type", required=True,
                             choices=[r.value for r in VersionRelation], help="关系类型")
    relation_add.add_argument("-d", "--description", help="关系描述")
    
    relation_list = relation_sub.add_parser("list", help="列出版本关系")
    relation_list.add_argument("version", help="版本号")
    relation_list.add_argument("-t", "--type", choices=[r.value for r in VersionRelation],
                              help="关系类型筛选")
    
    parser_migrate = subparsers.add_parser("migrate", help="迁移文档")
    parser_migrate.add_argument("source", help="源版本")
    parser_migrate.add_argument("target", help="目标版本")
    parser_migrate.add_argument("-t", "--type", choices=[dt.value for dt in DocType],
                               help="文档类型")
    parser_migrate.add_argument("-s", "--stage", choices=[ws.value for ws in WorkflowStage],
                               help="流程阶段")
    parser_migrate.add_argument("--move", action="store_true", help="移动而非复制")
    
    parser_add = subparsers.add_parser("add", help="添加文档")
    parser_add.add_argument("version", help="版本号")
    parser_add.add_argument("source", help="源文件路径")
    parser_add.add_argument("-t", "--type", choices=[dt.value for dt in DocType],
                           help="文档类型")
    parser_add.add_argument("-s", "--stage", choices=[ws.value for ws in WorkflowStage],
                           help="流程阶段")
    parser_add.add_argument("-n", "--name", help="文档名称")
    parser_add.add_argument("--tags", nargs="*", help="文档标签")
    parser_add.add_argument("--author", help="作者")
    
    parser_docs = subparsers.add_parser("docs", help="列出文档")
    parser_docs.add_argument("-v", "--version", help="版本号")
    parser_docs.add_argument("-t", "--type", choices=[dt.value for dt in DocType],
                            help="文档类型")
    parser_docs.add_argument("-s", "--stage", choices=[ws.value for ws in WorkflowStage],
                            help="流程阶段")
    parser_docs.add_argument("--tags", nargs="*", help="标签筛选")
    
    parser_history = subparsers.add_parser("history", help="文档历史")
    parser_history.add_argument("version", help="版本号")
    parser_history.add_argument("doc_name", help="文档名称")
    
    parser_save_history = subparsers.add_parser("save-history", help="保存文档历史")
    parser_save_history.add_argument("version", help="版本号")
    parser_save_history.add_argument("file", help="文件路径")
    parser_save_history.add_argument("-m", "--message", help="变更说明")
    
    parser_restore_doc = subparsers.add_parser("restore-doc", help="恢复文档历史版本")
    parser_restore_doc.add_argument("version", help="版本号")
    parser_restore_doc.add_argument("doc_name", help="文档名称")
    parser_restore_doc.add_argument("history_file", help="历史版本文件名")
    
    parser_diff = subparsers.add_parser("diff", help="比较文档差异")
    parser_diff.add_argument("file1", help="第一个文件")
    parser_diff.add_argument("file2", help="第二个文件")
    parser_diff.add_argument("--type", choices=["unified", "context"], default="unified",
                            help="差异格式")
    
    parser_diff_version = subparsers.add_parser("diff-version", help="比较版本差异")
    parser_diff_version.add_argument("v1", help="第一个版本")
    parser_diff_version.add_argument("v2", help="第二个版本")
    parser_diff_version.add_argument("-t", "--type", choices=[dt.value for dt in DocType],
                                    help="文档类型")
    parser_diff_version.add_argument("-s", "--stage", choices=[ws.value for ws in WorkflowStage],
                                    help="流程阶段")
    
    parser_diff_history = subparsers.add_parser("diff-history", help="比较历史版本")
    parser_diff_history.add_argument("version", help="版本号")
    parser_diff_history.add_argument("doc_name", help="文档名称")
    parser_diff_history.add_argument("history1", help="历史版本1")
    parser_diff_history.add_argument("history2", help="历史版本2")
    
    parser_integrity = subparsers.add_parser("integrity", help="完整性检查")
    parser_integrity.add_argument("-v", "--version", help="版本号")
    parser_integrity.add_argument("--repair", action="store_true", help="自动修复")
    
    parser_changelog = subparsers.add_parser("changelog", help="生成变更日志")
    parser_changelog.add_argument("version", help="版本号")
    parser_changelog.add_argument("-c", "--changes", nargs="+", required=True,
                                  help="变更内容列表")
    
    parser_workflow = subparsers.add_parser("workflow", help="工作流程管理")
    workflow_sub = parser_workflow.add_subparsers(dest="workflow_cmd")
    
    workflow_progress = workflow_sub.add_parser("progress", help="查看工作流程进度")
    workflow_progress.add_argument("version", help="版本号")
    
    workflow_create_doc = workflow_sub.add_parser("create-doc", help="创建工作流程文档")
    workflow_create_doc.add_argument("version", help="版本号")
    workflow_create_doc.add_argument("-s", "--stage", required=True,
                                    choices=[ws.value for ws in WorkflowStage], help="流程阶段")
    workflow_create_doc.add_argument("-n", "--name", required=True, help="文档名称")
    workflow_create_doc.add_argument("-c", "--content", required=True, help="文档内容")
    workflow_create_doc.add_argument("--tags", nargs="*", help="文档标签")
    workflow_create_doc.add_argument("--author", help="作者")
    
    parser_export = subparsers.add_parser("export", help="导出版本摘要")
    parser_export.add_argument("version", help="版本号")
    
    parser_test = subparsers.add_parser("test", help="运行测试")
    
    args = parser.parse_args()
    manager = DocVersionManager()
    
    if args.command == "current":
        print(f"当前版本: {manager.get_current_version()}")
        branch = manager.get_current_branch()
        if branch:
            print(f"当前分支: {branch}")
    
    elif args.command == "set":
        manager.set_current_version(args.version)
    
    elif args.command == "create":
        parent = args.parent
        tags = args.tags
        manager.create_version(args.version, args.description, parent, tags, args.status)
    
    elif args.command == "status":
        manager.update_version_status(args.version, VersionStatus(args.status))
    
    elif args.command == "list":
        status_filter = VersionStatus(args.status) if args.status else None
        versions = manager.list_versions(include_archived=args.all, 
                                         sort_by_version=args.sort,
                                         status_filter=status_filter)
        for v in versions:
            status = f"[{v.status}]" if v.status != VersionStatus.DRAFT.value else ""
            archived = "[已归档]" if v.is_archived else ""
            tags_str = f" [{', '.join(v.tags)}]" if v.tags else ""
            branch_str = f" (分支: {v.branch_name})" if v.branch_name else ""
            print(f"  {v.version} - {v.created_at[:10]}{status}{archived}{tags_str}{branch_str}")
            if v.description:
                print(f"    描述: {v.description}")
    
    elif args.command == "info":
        info = manager.get_version_info(args.version)
        if info:
            print(f"版本: {info.version}")
            print(f"创建时间: {info.created_at}")
            print(f"描述: {info.description or '无'}")
            print(f"文档类型: {', '.join(info.doc_types)}")
            print(f"流程阶段: {', '.join(info.workflow_stages)}")
            print(f"状态: {info.status}")
            if info.is_archived:
                print(f"归档状态: 已归档 ({info.archived_at})")
            if info.parent_version:
                print(f"父版本: {info.parent_version}")
            if info.branch_name:
                print(f"分支: {info.branch_name}")
            if info.tags:
                print(f"标签: {', '.join(info.tags)}")
            
            relations = manager.get_version_relations(args.version)
            if relations:
                print(f"\n版本关系:")
                for rel in relations:
                    print(f"  - {rel.relation_type}: {rel.related_version}")
                    if rel.description:
                        print(f"    {rel.description}")
    
    elif args.command == "next":
        next_ver = manager.get_next_version(args.type)
        print(f"下一个版本号: {next_ver}")
    
    elif args.command == "compare-ver":
        try:
            result = manager.compare_versions(args.v1, args.v2)
            if result < 0:
                print(f"{args.v1} < {args.v2}")
            elif result > 0:
                print(f"{args.v1} > {args.v2}")
            else:
                print(f"{args.v1} = {args.v2}")
        except ValueError as e:
            print(f"错误: {e}")
    
    elif args.command == "archive":
        manager.archive_version(args.version)
    
    elif args.command == "restore":
        manager.restore_version(args.version)
    
    elif args.command == "delete":
        manager.delete_version(args.version, args.force)
    
    elif args.command == "branch":
        if args.branch_cmd == "create":
            manager.create_branch(args.name, args.base, args.description)
        elif args.branch_cmd == "switch":
            manager.switch_branch(args.name)
        elif args.branch_cmd == "merge":
            manager.merge_branch(args.source, args.target, args.message)
        elif args.branch_cmd == "list":
            branches = manager.list_branches()
            for b in branches:
                merged = "[已合并]" if b.is_merged else ""
                print(f"  {b.name} - 基于 {b.base_version}{merged}")
                if b.description:
                    print(f"    描述: {b.description}")
                if b.is_merged:
                    print(f"    合并到: {b.merged_to} ({b.merged_at})")
        else:
            parser_branch.print_help()
    
    elif args.command == "relation":
        if args.relation_cmd == "add":
            manager.add_version_relation(args.version, args.related, 
                                        VersionRelation(args.type), args.description)
        elif args.relation_cmd == "list":
            rel_type = VersionRelation(args.type) if args.type else None
            relations = manager.get_version_relations(args.version, rel_type)
            if relations:
                print(f"版本 {args.version} 的关系:")
                for rel in relations:
                    print(f"  - {rel.relation_type}: {rel.related_version} ({rel.created_at})")
                    if rel.description:
                        print(f"    {rel.description}")
            else:
                print(f"版本 {args.version} 没有关系记录")
        else:
            parser_relation.print_help()
    
    elif args.command == "migrate":
        doc_type = DocType(args.type) if args.type else None
        stage = WorkflowStage(args.stage) if args.stage else None
        manager.migrate_version(args.source, args.target, 
                               [doc_type] if doc_type else None,
                               [stage] if stage else None,
                               copy_mode=not args.move)
    
    elif args.command == "add":
        doc_type = DocType(args.type) if args.type else None
        stage = WorkflowStage(args.stage) if args.stage else None
        manager.add_document(args.version, args.source, doc_type, stage, 
                            args.name, args.tags, args.author)
    
    elif args.command == "docs":
        doc_type = DocType(args.type) if args.type else None
        stage = WorkflowStage(args.stage) if args.stage else None
        docs = manager.list_documents(args.version, doc_type, stage, args.tags)
        for doc in docs:
            stage_str = f"[{doc.workflow_stage}]" if doc.workflow_stage else ""
            tags_str = f" [{', '.join(doc.tags)}]" if doc.tags else ""
            print(f"  [{doc.doc_type}]{stage_str} {doc.name} ({doc.version}){tags_str}")
    
    elif args.command == "history":
        history = manager.get_document_history(args.version, args.doc_name)
        if history:
            print(f"文档 {args.doc_name} 的历史版本:")
            for h in history:
                desc = f" - {h.get('change_description')}" if h.get('change_description') else ""
                print(f"  - {h['timestamp']}: {h['history_file']}{desc}")
        else:
            print(f"未找到文档 {args.doc_name} 的历史记录")
    
    elif args.command == "save-history":
        manager.save_document_history(args.version, args.file, args.message)
    
    elif args.command == "restore-doc":
        manager.restore_document_version(args.version, args.doc_name, args.history_file)
    
    elif args.command == "diff":
        try:
            result = manager.compare_documents(args.file1, args.file2, args.type)
            print(f"文件比较结果:")
            print(f"  新增行数: {result.added_lines}")
            print(f"  删除行数: {result.removed_lines}")
            print(f"  修改行数: {result.modified_lines}")
            print(f"  相似度: {result.similarity_ratio:.2%}")
            print(f"\n差异内容:")
            print(result.diff_content)
        except FileNotFoundError as e:
            print(f"错误: {e}")
    
    elif args.command == "diff-version":
        doc_type = DocType(args.type) if args.type else None
        stage = WorkflowStage(args.stage) if args.stage else None
        results = manager.compare_versions(args.v1, args.v2, doc_type, stage)
        for result in results:
            print(f"\n文件: {Path(result.file1).name}")
            print(f"  相似度: {result.similarity_ratio:.2%}")
            print(f"  新增: {result.added_lines}, 删除: {result.removed_lines}")
    
    elif args.command == "diff-history":
        result = manager.compare_history_versions(args.version, args.doc_name,
                                                  args.history1, args.history2)
        if result:
            print(f"历史版本比较结果:")
            print(f"  相似度: {result.similarity_ratio:.2%}")
            print(f"  新增: {result.added_lines}, 删除: {result.removed_lines}")
            print(f"\n差异内容:")
            print(result.diff_content)
    
    elif args.command == "integrity":
        result = manager.check_integrity(args.version)
        if result.is_valid:
            print("完整性检查通过")
        else:
            print("完整性检查失败:")
            if result.missing_files:
                print(f"  缺失文件: {len(result.missing_files)}")
                for f in result.missing_files:
                    print(f"    - {f}")
            if result.checksum_mismatches:
                print(f"  校验和不匹配: {len(result.checksum_mismatches)}")
                for f in result.checksum_mismatches:
                    print(f"    - {f}")
            if result.missing_directories:
                print(f"  缺失目录: {len(result.missing_directories)}")
                for d in result.missing_directories:
                    print(f"    - {d}")
            if result.errors:
                print(f"  错误: {len(result.errors)}")
                for e in result.errors:
                    print(f"    - {e}")
            
            if args.repair:
                print("\n正在修复...")
                manager.repair_integrity(args.version)
    
    elif args.command == "changelog":
        manager.generate_changelog(args.version, args.changes)
    
    elif args.command == "workflow":
        if args.workflow_cmd == "progress":
            progress = manager.get_workflow_progress(args.version)
            print(f"版本 {args.version} 的工作流程进度:")
            for stage, info in sorted(progress.items(), key=lambda x: x[1]["order"]):
                status = "✓" if info["completed"] else "○"
                print(f"  {status} {info['display_name']}: {info['document_count']} 个文档")
        elif args.workflow_cmd == "create-doc":
            stage = WorkflowStage(args.stage)
            manager.create_workflow_document(args.version, stage, args.name,
                                            args.content, args.tags, args.author)
        else:
            parser_workflow.print_help()
    
    elif args.command == "export":
        summary = manager.export_version_summary(args.version)
        if summary:
            print(json.dumps(summary, ensure_ascii=False, indent=2))
        else:
            print(f"版本 {args.version} 不存在")
    
    elif args.command == "test":
        unittest.main(argv=[''], exit=False, verbosity=2)
    
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
