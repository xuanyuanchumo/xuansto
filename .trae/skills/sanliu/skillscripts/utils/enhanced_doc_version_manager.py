#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
文档版本管理器增强版 - Sanliu 技能

功能增强：
- 文档分类存储（需求/设计/实现/测试/部署）
- 文档快照功能
- 文档变更追踪
- 文档生命周期管理
- 文档搜索与索引
"""

import hashlib
import json
import logging
import os
import re
import shutil
import sys
import threading
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Generator

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - [%(name)s] %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


class DocumentCategory(Enum):
    """文档分类枚举"""
    REQUIREMENTS = "requirements"
    DESIGN = "design"
    IMPLEMENTATION = "implementation"
    TESTING = "testing"
    DEPLOYMENT = "deployment"
    API = "api"
    ARCHITECTURE = "architecture"
    USER_GUIDE = "user_guide"
    CHANGELOG = "changelog"
    OTHER = "other"


class DocumentStatus(Enum):
    """文档状态枚举"""
    DRAFT = "draft"
    REVIEW = "review"
    APPROVED = "approved"
    PUBLISHED = "published"
    DEPRECATED = "deprecated"
    ARCHIVED = "archived"


class ChangeType(Enum):
    """变更类型枚举"""
    CREATED = "created"
    MODIFIED = "modified"
    DELETED = "deleted"
    RENAMED = "renamed"
    MOVED = "moved"
    VERSION_BUMP = "version_bump"


@dataclass
class DocumentInfo:
    """文档信息数据类"""
    doc_id: str
    name: str
    category: str
    version: str
    file_path: str
    created_at: str
    updated_at: str
    status: str = DocumentStatus.DRAFT.value
    author: Optional[str] = None
    description: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    checksum: Optional[str] = None
    size_bytes: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)
    parent_doc_id: Optional[str] = None
    related_docs: List[str] = field(default_factory=list)


@dataclass
class DocumentSnapshot:
    """文档快照数据类"""
    snapshot_id: str
    doc_id: str
    doc_name: str
    version: str
    category: str
    created_at: str
    file_path: str
    content_path: str
    checksum: str
    size_bytes: int
    description: Optional[str] = None
    is_auto_snapshot: bool = False
    tags: List[str] = field(default_factory=list)


@dataclass
class DocumentChange:
    """文档变更记录数据类"""
    change_id: str
    doc_id: str
    change_type: str
    timestamp: str
    old_version: Optional[str] = None
    new_version: Optional[str] = None
    old_path: Optional[str] = None
    new_path: Optional[str] = None
    old_checksum: Optional[str] = None
    new_checksum: Optional[str] = None
    author: Optional[str] = None
    description: Optional[str] = None
    diff_summary: Optional[str] = None
    lines_added: int = 0
    lines_removed: int = 0
    lines_modified: int = 0


@dataclass
class DocumentVersion:
    """文档版本数据类"""
    version: str
    doc_id: str
    created_at: str
    status: str
    checksum: str
    size_bytes: int
    description: Optional[str] = None
    author: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    is_current: bool = False


@dataclass
class CategoryConfig:
    """分类配置数据类"""
    category: str
    display_name: str
    description: str
    directory: str
    required_docs: List[str] = field(default_factory=list)
    file_patterns: List[str] = field(default_factory=list)
    auto_version: bool = True
    retention_days: int = 365


class DocumentCategoryManager:
    """文档分类管理器"""
    
    CATEGORY_CONFIGS: Dict[str, CategoryConfig] = {
        DocumentCategory.REQUIREMENTS.value: CategoryConfig(
            category=DocumentCategory.REQUIREMENTS.value,
            display_name="需求文档",
            description="需求分析和规格说明文档",
            directory="requirements",
            required_docs=["需求规格说明书", "用户故事"],
            file_patterns=["*需求*", "*requirement*", "*PRD*"]
        ),
        DocumentCategory.DESIGN.value: CategoryConfig(
            category=DocumentCategory.DESIGN.value,
            display_name="设计文档",
            description="系统设计和架构设计文档",
            directory="design",
            required_docs=["系统设计文档", "数据库设计"],
            file_patterns=["*设计*", "*design*", "*架构*", "*architecture*"]
        ),
        DocumentCategory.IMPLEMENTATION.value: CategoryConfig(
            category=DocumentCategory.IMPLEMENTATION.value,
            display_name="实现文档",
            description="代码实现和开发文档",
            directory="implementation",
            required_docs=["开发指南", "代码规范"],
            file_patterns=["*实现*", "*implementation*", "*开发*", "*development*"]
        ),
        DocumentCategory.TESTING.value: CategoryConfig(
            category=DocumentCategory.TESTING.value,
            display_name="测试文档",
            description="测试计划和测试报告文档",
            directory="testing",
            required_docs=["测试计划", "测试报告"],
            file_patterns=["*测试*", "*test*", "*QA*"]
        ),
        DocumentCategory.DEPLOYMENT.value: CategoryConfig(
            category=DocumentCategory.DEPLOYMENT.value,
            display_name="部署文档",
            description="部署和运维文档",
            directory="deployment",
            required_docs=["部署指南", "运维手册"],
            file_patterns=["*部署*", "*deploy*", "*运维*", "*operation*"]
        ),
        DocumentCategory.API.value: CategoryConfig(
            category=DocumentCategory.API.value,
            display_name="API文档",
            description="API接口文档",
            directory="api",
            required_docs=["API接口文档"],
            file_patterns=["*api*", "*API*", "*接口*"]
        ),
        DocumentCategory.ARCHITECTURE.value: CategoryConfig(
            category=DocumentCategory.ARCHITECTURE.value,
            display_name="架构文档",
            description="系统架构文档",
            directory="architecture",
            required_docs=["系统架构文档"],
            file_patterns=["*架构*", "*architecture*"]
        ),
        DocumentCategory.USER_GUIDE.value: CategoryConfig(
            category=DocumentCategory.USER_GUIDE.value,
            display_name="用户指南",
            description="用户使用手册和指南",
            directory="user_guide",
            required_docs=["用户手册"],
            file_patterns=["*用户*", "*user*", "*手册*", "*manual*", "*guide*"]
        ),
        DocumentCategory.CHANGELOG.value: CategoryConfig(
            category=DocumentCategory.CHANGELOG.value,
            display_name="变更日志",
            description="版本变更记录",
            directory="changelog",
            required_docs=["变更日志"],
            file_patterns=["*CHANGELOG*", "*变更*"]
        ),
        DocumentCategory.OTHER.value: CategoryConfig(
            category=DocumentCategory.OTHER.value,
            display_name="其他文档",
            description="其他类型文档",
            directory="other",
            required_docs=[],
            file_patterns=["*"]
        )
    }
    
    @classmethod
    def get_category_for_file(cls, file_name: str) -> str:
        """根据文件名自动分类"""
        file_lower = file_name.lower()
        
        for category, config in cls.CATEGORY_CONFIGS.items():
            for pattern in config.file_patterns:
                pattern_lower = pattern.lower().replace("*", "")
                if pattern_lower in file_lower:
                    return category
        
        return DocumentCategory.OTHER.value
    
    @classmethod
    def get_directory_for_category(cls, category: str) -> str:
        """获取分类对应的目录"""
        config = cls.CATEGORY_CONFIGS.get(category)
        return config.directory if config else "other"


class DocumentSnapshotManager:
    """文档快照管理器"""
    
    SNAPSHOT_DIR = "doc_snapshots"
    MAX_SNAPSHOTS_PER_DOC = 20
    
    def __init__(self, base_path: Path):
        self.base_path = base_path
        self.snapshot_dir = base_path / self.SNAPSHOT_DIR
        self._lock = threading.Lock()
        self._ensure_snapshot_dir()
    
    def _ensure_snapshot_dir(self):
        """确保快照目录存在"""
        self.snapshot_dir.mkdir(parents=True, exist_ok=True)
    
    def create_snapshot(
        self,
        doc_info: DocumentInfo,
        content: Optional[bytes] = None,
        description: Optional[str] = None,
        is_auto: bool = False
    ) -> DocumentSnapshot:
        """
        创建文档快照
        
        Args:
            doc_info: 文档信息
            content: 文档内容，None则从文件读取
            description: 快照描述
            is_auto: 是否为自动快照
            
        Returns:
            文档快照对象
        """
        snapshot_id = f"snap_{doc_info.doc_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        doc_path = Path(doc_info.file_path)
        if content is None and doc_path.exists():
            content = doc_path.read_bytes()
        
        if content is None:
            content = b""
        
        checksum = hashlib.md5(content).hexdigest()
        size_bytes = len(content)
        
        content_path = self.snapshot_dir / f"{snapshot_id}.dat"
        content_path.write_bytes(content)
        
        snapshot = DocumentSnapshot(
            snapshot_id=snapshot_id,
            doc_id=doc_info.doc_id,
            doc_name=doc_info.name,
            version=doc_info.version,
            category=doc_info.category,
            created_at=datetime.now().isoformat(),
            file_path=doc_info.file_path,
            content_path=str(content_path),
            checksum=checksum,
            size_bytes=size_bytes,
            description=description,
            is_auto_snapshot=is_auto,
            tags=doc_info.tags.copy()
        )
        
        self._save_snapshot_metadata(snapshot)
        self._cleanup_old_snapshots(doc_info.doc_id)
        
        return snapshot
    
    def _save_snapshot_metadata(self, snapshot: DocumentSnapshot):
        """保存快照元数据"""
        meta_path = self.snapshot_dir / f"{snapshot.snapshot_id}.json"
        with open(meta_path, 'w', encoding='utf-8') as f:
            json.dump(asdict(snapshot), f, indent=2, ensure_ascii=False)
    
    def _cleanup_old_snapshots(self, doc_id: str):
        """清理旧快照"""
        snapshots = self.list_snapshots(doc_id)
        
        if len(snapshots) > self.MAX_SNAPSHOTS_PER_DOC:
            to_remove = snapshots[self.MAX_SNAPSHOTS_PER_DOC:]
            for snap in to_remove:
                self.delete_snapshot(snap["snapshot_id"])
    
    def load_snapshot(self, snapshot_id: str) -> Optional[DocumentSnapshot]:
        """加载快照"""
        meta_path = self.snapshot_dir / f"{snapshot_id}.json"
        
        if not meta_path.exists():
            return None
        
        try:
            with open(meta_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return DocumentSnapshot(**data)
        except Exception as e:
            logger.error(f"加载快照失败: {e}")
            return None
    
    def restore_snapshot(self, snapshot_id: str) -> Tuple[bool, str]:
        """
        从快照恢复文档
        
        Args:
            snapshot_id: 快照ID
            
        Returns:
            (是否成功, 消息) 元组
        """
        snapshot = self.load_snapshot(snapshot_id)
        
        if snapshot is None:
            return False, f"快照不存在: {snapshot_id}"
        
        content_path = Path(snapshot.content_path)
        
        if not content_path.exists():
            return False, f"快照内容文件不存在: {snapshot.content_path}"
        
        target_path = Path(snapshot.file_path)
        target_path.parent.mkdir(parents=True, exist_ok=True)
        
        content = content_path.read_bytes()
        target_path.write_bytes(content)
        
        return True, f"已恢复文档: {snapshot.doc_name} (版本: {snapshot.version})"
    
    def list_snapshots(
        self,
        doc_id: Optional[str] = None,
        category: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """列出快照"""
        snapshots = []
        
        for meta_file in self.snapshot_dir.glob("*.json"):
            try:
                with open(meta_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                if doc_id and data.get("doc_id") != doc_id:
                    continue
                if category and data.get("category") != category:
                    continue
                
                snapshots.append({
                    "snapshot_id": data.get("snapshot_id"),
                    "doc_id": data.get("doc_id"),
                    "doc_name": data.get("doc_name"),
                    "version": data.get("version"),
                    "category": data.get("category"),
                    "created_at": data.get("created_at"),
                    "size_bytes": data.get("size_bytes"),
                    "is_auto_snapshot": data.get("is_auto_snapshot")
                })
            except:
                pass
        
        snapshots.sort(key=lambda x: x["created_at"], reverse=True)
        return snapshots[:limit]
    
    def delete_snapshot(self, snapshot_id: str) -> bool:
        """删除快照"""
        try:
            meta_path = self.snapshot_dir / f"{snapshot_id}.json"
            content_path = self.snapshot_dir / f"{snapshot_id}.dat"
            
            if meta_path.exists():
                meta_path.unlink()
            if content_path.exists():
                content_path.unlink()
            
            return True
        except Exception as e:
            logger.error(f"删除快照失败: {e}")
            return False


class DocumentChangeTracker:
    """文档变更追踪器"""
    
    CHANGE_LOG_FILE = "document_changes.json"
    
    def __init__(self, base_path: Path):
        self.base_path = base_path
        self.change_log_path = base_path / self.CHANGE_LOG_FILE
        self._lock = threading.Lock()
        self._changes: List[DocumentChange] = []
        self._load_changes()
    
    def _load_changes(self):
        """加载变更记录"""
        if self.change_log_path.exists():
            try:
                with open(self.change_log_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                self._changes = [DocumentChange(**item) for item in data]
            except Exception as e:
                logger.warning(f"加载变更记录失败: {e}")
                self._changes = []
    
    def _save_changes(self):
        """保存变更记录"""
        try:
            with open(self.change_log_path, 'w', encoding='utf-8') as f:
                json.dump([asdict(c) for c in self._changes], f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"保存变更记录失败: {e}")
    
    def record_change(
        self,
        doc_id: str,
        change_type: ChangeType,
        old_version: Optional[str] = None,
        new_version: Optional[str] = None,
        old_path: Optional[str] = None,
        new_path: Optional[str] = None,
        old_checksum: Optional[str] = None,
        new_checksum: Optional[str] = None,
        author: Optional[str] = None,
        description: Optional[str] = None,
        diff_summary: Optional[str] = None,
        lines_added: int = 0,
        lines_removed: int = 0,
        lines_modified: int = 0
    ) -> DocumentChange:
        """
        记录文档变更
        
        Args:
            doc_id: 文档ID
            change_type: 变更类型
            old_version: 旧版本
            new_version: 新版本
            old_path: 旧路径
            new_path: 新路径
            old_checksum: 旧校验和
            new_checksum: 新校验和
            author: 作者
            description: 描述
            diff_summary: 差异摘要
            lines_added: 新增行数
            lines_removed: 删除行数
            lines_modified: 修改行数
            
        Returns:
            变更记录对象
        """
        change_id = f"chg_{datetime.now().strftime('%Y%m%d%H%M%S')}_{doc_id[:8]}"
        
        change = DocumentChange(
            change_id=change_id,
            doc_id=doc_id,
            change_type=change_type.value,
            timestamp=datetime.now().isoformat(),
            old_version=old_version,
            new_version=new_version,
            old_path=old_path,
            new_path=new_path,
            old_checksum=old_checksum,
            new_checksum=new_checksum,
            author=author,
            description=description,
            diff_summary=diff_summary,
            lines_added=lines_added,
            lines_removed=lines_removed,
            lines_modified=lines_modified
        )
        
        with self._lock:
            self._changes.append(change)
            self._save_changes()
        
        return change
    
    def get_changes(
        self,
        doc_id: Optional[str] = None,
        change_type: Optional[ChangeType] = None,
        start_time: Optional[str] = None,
        end_time: Optional[str] = None,
        limit: int = 100
    ) -> List[DocumentChange]:
        """
        获取变更记录
        
        Args:
            doc_id: 文档ID过滤
            change_type: 变更类型过滤
            start_time: 开始时间
            end_time: 结束时间
            limit: 返回数量限制
            
        Returns:
            变更记录列表
        """
        filtered = []
        
        for change in reversed(self._changes):
            if doc_id and change.doc_id != doc_id:
                continue
            if change_type and change.change_type != change_type.value:
                continue
            if start_time and change.timestamp < start_time:
                continue
            if end_time and change.timestamp > end_time:
                continue
            
            filtered.append(change)
            
            if len(filtered) >= limit:
                break
        
        return filtered
    
    def get_change_summary(
        self,
        doc_id: Optional[str] = None,
        days: int = 7
    ) -> Dict[str, Any]:
        """
        获取变更摘要
        
        Args:
            doc_id: 文档ID
            days: 统计天数
            
        Returns:
            变更摘要字典
        """
        start_time = (datetime.now() - timedelta(days=days)).isoformat()
        changes = self.get_changes(doc_id=doc_id, start_time=start_time)
        
        summary = {
            "total_changes": len(changes),
            "by_type": {},
            "by_day": {},
            "total_lines_added": 0,
            "total_lines_removed": 0,
            "total_lines_modified": 0
        }
        
        for change in changes:
            change_type = change.change_type
            summary["by_type"][change_type] = summary["by_type"].get(change_type, 0) + 1
            
            day = change.timestamp[:10]
            summary["by_day"][day] = summary["by_day"].get(day, 0) + 1
            
            summary["total_lines_added"] += change.lines_added
            summary["total_lines_removed"] += change.lines_removed
            summary["total_lines_modified"] += change.lines_modified
        
        return summary


class EnhancedDocVersionManager:
    """
    增强版文档版本管理器
    
    功能：
    - 文档分类存储
    - 文档快照管理
    - 文档变更追踪
    - 文档版本管理
    - 文档搜索
    """
    
    INDEX_FILE = "doc_index.json"
    VERSIONS_DIR = "doc_versions"
    
    def __init__(self, base_path: Path):
        self.base_path = base_path
        self.docs_dir = base_path / "docs"
        self.index_path = self.docs_dir / self.INDEX_FILE
        self.versions_dir = self.docs_dir / self.VERSIONS_DIR
        
        self._lock = threading.Lock()
        self._doc_index: Dict[str, DocumentInfo] = {}
        
        self.snapshot_manager = DocumentSnapshotManager(base_path)
        self.change_tracker = DocumentChangeTracker(base_path)
        
        self._ensure_directories()
        self._load_index()
    
    def _ensure_directories(self):
        """确保基础目录存在（不预创建分类目录）"""
        self.docs_dir.mkdir(parents=True, exist_ok=True)
        self.versions_dir.mkdir(parents=True, exist_ok=True)
    
    def ensure_category_directory(self, category: str) -> Path:
        """
        确保分类目录存在，按需创建
        
        Args:
            category: 文档分类
            
        Returns:
            分类目录路径
        """
        category_dir = self.docs_dir / DocumentCategoryManager.get_directory_for_category(category)
        if not category_dir.exists():
            category_dir.mkdir(parents=True, exist_ok=True)
            logger.info(f"创建分类目录: {category_dir}")
        return category_dir
    
    def _load_index(self):
        """加载文档索引"""
        if self.index_path.exists():
            try:
                with open(self.index_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                self._doc_index = {
                    k: DocumentInfo(**v) for k, v in data.items()
                }
            except Exception as e:
                logger.warning(f"加载文档索引失败: {e}")
    
    def _save_index(self):
        """保存文档索引"""
        try:
            with open(self.index_path, 'w', encoding='utf-8') as f:
                json.dump(
                    {k: asdict(v) for k, v in self._doc_index.items()},
                    f, indent=2, ensure_ascii=False
                )
        except Exception as e:
            logger.error(f"保存文档索引失败: {e}")
    
    def _generate_doc_id(self, name: str, category: str) -> str:
        """生成文档ID"""
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        name_hash = hashlib.md5(name.encode()).hexdigest()[:8]
        return f"doc_{category}_{timestamp}_{name_hash}"
    
    def register_document(
        self,
        file_path: str,
        category: Optional[str] = None,
        name: Optional[str] = None,
        version: str = "1.0.0",
        author: Optional[str] = None,
        description: Optional[str] = None,
        tags: Optional[List[str]] = None,
        create_snapshot: bool = True
    ) -> DocumentInfo:
        """
        注册文档
        
        Args:
            file_path: 文档文件路径
            category: 文档分类
            name: 文档名称
            version: 文档版本
            author: 作者
            description: 描述
            tags: 标签
            create_snapshot: 是否创建快照
            
        Returns:
            文档信息对象
        """
        path = Path(file_path)
        
        if not path.exists():
            raise FileNotFoundError(f"文档不存在: {file_path}")
        
        if category is None:
            category = DocumentCategoryManager.get_category_for_file(path.name)
        
        if name is None:
            name = path.stem
        
        self.ensure_category_directory(category)
        
        doc_id = self._generate_doc_id(name, category)
        
        content = path.read_bytes()
        checksum = hashlib.md5(content).hexdigest()
        size_bytes = len(content)
        
        doc_info = DocumentInfo(
            doc_id=doc_id,
            name=name,
            category=category,
            version=version,
            file_path=str(path.absolute()),
            created_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat(),
            status=DocumentStatus.DRAFT.value,
            author=author,
            description=description,
            tags=tags or [],
            checksum=checksum,
            size_bytes=size_bytes
        )
        
        with self._lock:
            self._doc_index[doc_id] = doc_info
            self._save_index()
        
        self.change_tracker.record_change(
            doc_id=doc_id,
            change_type=ChangeType.CREATED,
            new_version=version,
            new_path=str(path),
            new_checksum=checksum,
            author=author,
            description=f"创建文档: {name}"
        )
        
        if create_snapshot:
            self.snapshot_manager.create_snapshot(
                doc_info, content=content,
                description="初始版本快照",
                is_auto=True
            )
        
        return doc_info
    
    def update_document(
        self,
        doc_id: str,
        new_version: Optional[str] = None,
        author: Optional[str] = None,
        description: Optional[str] = None,
        create_snapshot: bool = True
    ) -> Optional[DocumentInfo]:
        """
        更新文档
        
        Args:
            doc_id: 文档ID
            new_version: 新版本号
            author: 作者
            description: 更新描述
            create_snapshot: 是否创建快照
            
        Returns:
            更新后的文档信息
        """
        doc_info = self._doc_index.get(doc_id)
        
        if doc_info is None:
            return None
        
        path = Path(doc_info.file_path)
        
        if not path.exists():
            return None
        
        old_checksum = doc_info.checksum
        old_version = doc_info.version
        
        content = path.read_bytes()
        new_checksum = hashlib.md5(content).hexdigest()
        
        if new_checksum == old_checksum:
            return doc_info
        
        if new_version is None:
            parts = old_version.split('.')
            if len(parts) >= 3:
                parts[2] = str(int(parts[2]) + 1)
                new_version = '.'.join(parts)
            else:
                new_version = old_version
        
        doc_info.checksum = new_checksum
        doc_info.version = new_version
        doc_info.updated_at = datetime.now().isoformat()
        doc_info.size_bytes = len(content)
        
        if description:
            doc_info.description = description
        
        with self._lock:
            self._save_index()
        
        self.change_tracker.record_change(
            doc_id=doc_id,
            change_type=ChangeType.MODIFIED,
            old_version=old_version,
            new_version=new_version,
            old_checksum=old_checksum,
            new_checksum=new_checksum,
            author=author,
            description=description
        )
        
        if create_snapshot:
            self.snapshot_manager.create_snapshot(
                doc_info, content=content,
                description=f"版本 {new_version} 快照",
                is_auto=True
            )
        
        return doc_info
    
    def get_document(self, doc_id: str) -> Optional[DocumentInfo]:
        """获取文档信息"""
        return self._doc_index.get(doc_id)
    
    def list_documents(
        self,
        category: Optional[str] = None,
        status: Optional[str] = None,
        tags: Optional[List[str]] = None,
        limit: int = 100
    ) -> List[DocumentInfo]:
        """
        列出文档
        
        Args:
            category: 分类过滤
            status: 状态过滤
            tags: 标签过滤
            limit: 返回数量限制
            
        Returns:
            文档列表
        """
        results = []
        
        for doc in self._doc_index.values():
            if category and doc.category != category:
                continue
            if status and doc.status != status:
                continue
            if tags and not any(t in doc.tags for t in tags):
                continue
            
            results.append(doc)
        
        results.sort(key=lambda x: x.updated_at, reverse=True)
        return results[:limit]
    
    def search_documents(
        self,
        query: str,
        search_content: bool = False
    ) -> List[Dict[str, Any]]:
        """
        搜索文档
        
        Args:
            query: 搜索关键词
            search_content: 是否搜索内容
            
        Returns:
            搜索结果列表
        """
        results = []
        query_lower = query.lower()
        
        for doc in self._doc_index.values():
            score = 0
            matched_fields = []
            
            if query_lower in doc.name.lower():
                score += 10
                matched_fields.append("name")
            
            if doc.description and query_lower in doc.description.lower():
                score += 5
                matched_fields.append("description")
            
            if any(query_lower in tag.lower() for tag in doc.tags):
                score += 3
                matched_fields.append("tags")
            
            if search_content:
                try:
                    path = Path(doc.file_path)
                    if path.exists():
                        content = path.read_text(encoding='utf-8', errors='ignore')
                        if query_lower in content.lower():
                            score += 1
                            matched_fields.append("content")
                except:
                    pass
            
            if score > 0:
                results.append({
                    "doc_id": doc.doc_id,
                    "name": doc.name,
                    "category": doc.category,
                    "version": doc.version,
                    "score": score,
                    "matched_fields": matched_fields
                })
        
        results.sort(key=lambda x: x["score"], reverse=True)
        return results
    
    def create_snapshot(
        self,
        doc_id: str,
        description: Optional[str] = None
    ) -> Optional[DocumentSnapshot]:
        """为文档创建快照"""
        doc_info = self._doc_index.get(doc_id)
        
        if doc_info is None:
            return None
        
        return self.snapshot_manager.create_snapshot(
            doc_info, description=description
        )
    
    def restore_snapshot(
        self,
        snapshot_id: str
    ) -> Tuple[bool, str]:
        """从快照恢复文档"""
        return self.snapshot_manager.restore_snapshot(snapshot_id)
    
    def get_change_history(
        self,
        doc_id: str,
        limit: int = 20
    ) -> List[DocumentChange]:
        """获取文档变更历史"""
        return self.change_tracker.get_changes(doc_id=doc_id, limit=limit)
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        stats = {
            "total_documents": len(self._doc_index),
            "by_category": {},
            "by_status": {},
            "total_size_bytes": 0,
            "total_snapshots": len(self.snapshot_manager.list_snapshots()),
            "total_changes": len(self.change_tracker._changes)
        }
        
        for doc in self._doc_index.values():
            stats["by_category"][doc.category] = stats["by_category"].get(doc.category, 0) + 1
            stats["by_status"][doc.status] = stats["by_status"].get(doc.status, 0) + 1
            stats["total_size_bytes"] += doc.size_bytes
        
        return stats


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="文档版本管理器增强版 - Sanliu 技能"
    )
    
    parser.add_argument(
        '--base-path',
        type=str,
        default='.',
        help='基础路径'
    )
    parser.add_argument(
        '--register',
        type=str,
        help='注册文档（文件路径）'
    )
    parser.add_argument(
        '--category',
        type=str,
        choices=[c.value for c in DocumentCategory],
        help='文档分类'
    )
    parser.add_argument(
        '--list',
        action='store_true',
        help='列出文档'
    )
    parser.add_argument(
        '--search',
        type=str,
        help='搜索文档'
    )
    parser.add_argument(
        '--snapshot',
        type=str,
        help='为文档创建快照（文档ID）'
    )
    parser.add_argument(
        '--restore',
        type=str,
        help='从快照恢复（快照ID）'
    )
    parser.add_argument(
        '--history',
        type=str,
        help='查看文档变更历史（文档ID）'
    )
    parser.add_argument(
        '--stats',
        action='store_true',
        help='显示统计信息'
    )
    
    args = parser.parse_args()
    
    base_path = Path(args.base_path).resolve()
    manager = EnhancedDocVersionManager(base_path)
    
    if args.register:
        doc_info = manager.register_document(
            args.register,
            category=args.category
        )
        print(json.dumps(asdict(doc_info), indent=2, ensure_ascii=False))
    
    if args.list:
        docs = manager.list_documents(category=args.category)
        for doc in docs:
            print(f"- [{doc.doc_id}] {doc.name} ({doc.category}) v{doc.version}")
    
    if args.search:
        results = manager.search_documents(args.search)
        print(json.dumps(results, indent=2, ensure_ascii=False))
    
    if args.snapshot:
        snapshot = manager.create_snapshot(args.snapshot)
        if snapshot:
            print(f"快照已创建: {snapshot.snapshot_id}")
        else:
            print("文档不存在")
    
    if args.restore:
        success, message = manager.restore_snapshot(args.restore)
        print(message)
    
    if args.history:
        changes = manager.get_change_history(args.history)
        for change in changes:
            print(f"- [{change.timestamp}] {change.change_type}: {change.description}")
    
    if args.stats:
        stats = manager.get_statistics()
        print(json.dumps(stats, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
