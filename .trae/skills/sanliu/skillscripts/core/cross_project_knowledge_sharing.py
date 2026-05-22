#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
跨项目知识共享系统 - Sanliu 技能

功能：
1. CentralizedKnowledgeHub：知识库中心化管理
   - 知识注册和注销
   - 知识分类和标签
   - 知识版本管理

2. KnowledgeIndexer：知识索引与检索
   - 全文索引
   - 语义索引接口
   - 高级查询

3. KnowledgeSynchronizer：知识同步机制
   - 增量同步
   - 冲突检测和解决
   - 同步状态追踪

4. KnowledgeAccessControl：知识权限控制
   - 权限级别（公开、私有、共享）
   - 访问控制列表
   - 权限审计

使用示例：
    from cross_project_knowledge_sharing import (
        CentralizedKnowledgeHub,
        KnowledgeIndexer,
        KnowledgeSynchronizer,
        KnowledgeAccessControl
    )
    
    # 创建中心化知识中心
    hub = CentralizedKnowledgeHub()
    hub.initialize()
    
    # 注册知识
    hub.register_knowledge(knowledge_item, project_id="proj1")
    
    # 创建索引器
    indexer = KnowledgeIndexer(hub)
    indexer.build_all_indexes()
    
    # 高级搜索
    results = indexer.advanced_search(query="关键词", filters={...})
    
    # 同步知识
    sync = KnowledgeSynchronizer(hub)
    sync.sync_incremental(source_project="proj1", target_project="proj2")
    
    # 权限控制
    acl = KnowledgeAccessControl(hub)
    acl.set_permission(knowledge_id="kb-001", level=PermissionLevel.SHARED)
"""

import hashlib
import json
import logging
import os
import re
import threading
from abc import ABC, abstractmethod
from collections import defaultdict
from copy import deepcopy
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum, auto
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set, Tuple, Type, Union

try:
    import chardet
    CHARDET_AVAILABLE = True
except ImportError:
    CHARDET_AVAILABLE = False

try:
    from analysis.knowledge_base import KnowledgePermission
except ImportError:
    class KnowledgePermission(Enum):
        PUBLIC = "public"
        PRIVATE = "private"
        SHARED = "shared"

try:
    from core.project_registry import ProjectRegistry
except ImportError:
    ProjectRegistry = None

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def detect_and_read_file(file_path: Path, fallback_encodings: Optional[List[str]] = None) -> str:
    """
    自动检测文件编码并读取文件内容
    
    Args:
        file_path: 文件路径
        fallback_encodings: 备用编码列表，默认为 ['utf-8', 'gbk', 'gb2312', 'gb18030']
    
    Returns:
        文件内容字符串
    
    Raises:
        UnicodeDecodeError: 所有编码尝试都失败时抛出
        FileNotFoundError: 文件不存在时抛出
    """
    if fallback_encodings is None:
        fallback_encodings = ['utf-8', 'gbk', 'gb2312', 'gb18030', 'latin-1']
    
    if not file_path.exists():
        raise FileNotFoundError(f"文件不存在: {file_path}")
    
    with open(file_path, 'rb') as f:
        raw_data = f.read()
    
    if CHARDET_AVAILABLE:
        try:
            detected = chardet.detect(raw_data)
            if detected and detected.get('encoding'):
                detected_encoding = detected['encoding']
                confidence = detected.get('confidence', 0)
                
                if confidence > 0.7:
                    try:
                        content = raw_data.decode(detected_encoding)
                        logger.debug(f"文件 {file_path} 使用检测编码: {detected_encoding} (置信度: {confidence:.2f})")
                        return content
                    except (UnicodeDecodeError, LookupError) as e:
                        logger.debug(f"检测编码 {detected_encoding} 解码失败: {e}")
        except Exception as e:
            logger.debug(f"编码检测失败: {e}")
    
    for encoding in fallback_encodings:
        try:
            content = raw_data.decode(encoding)
            logger.debug(f"文件 {file_path} 使用编码: {encoding}")
            return content
        except (UnicodeDecodeError, LookupError) as e:
            logger.debug(f"编码 {encoding} 解码失败: {e}")
            continue
    
    raise UnicodeDecodeError(
        'unknown', raw_data, 0, len(raw_data),
        f'无法用以下编码解码文件 {file_path}: {", ".join(fallback_encodings)}'
    )


def safe_read_json(file_path: Path) -> Dict[str, Any]:
    """
    安全读取JSON文件，自动处理编码问题
    
    Args:
        file_path: JSON文件路径
    
    Returns:
        解析后的字典
    
    Raises:
        json.JSONDecodeError: JSON解析失败时抛出
        FileNotFoundError: 文件不存在时抛出
    """
    content = detect_and_read_file(file_path)
    return json.loads(content)


class PermissionLevel(Enum):
    """权限级别枚举"""
    PUBLIC = "public"
    PRIVATE = "private"
    SHARED = "shared"
    READ_ONLY = "read_only"
    ADMIN = "admin"
    
    def get_description(self) -> str:
        descriptions = {
            PermissionLevel.PUBLIC: "公开 - 所有人可访问",
            PermissionLevel.PRIVATE: "私有 - 仅所有者可访问",
            PermissionLevel.SHARED: "共享 - 指定项目可访问",
            PermissionLevel.READ_ONLY: "只读 - 可读不可写",
            PermissionLevel.ADMIN: "管理 - 完全控制权限"
        }
        return descriptions.get(self, "未知权限")


class KnowledgeCategory(Enum):
    """知识分类枚举"""
    FIX_PATTERN = "fix_pattern"
    BEST_PRACTICE = "best_practice"
    DIAGNOSIS = "diagnosis"
    CODE_PATTERN = "code_pattern"
    CONFIGURATION = "configuration"
    DOCUMENTATION = "documentation"
    TEMPLATE = "template"
    OTHER = "other"


class SyncStatus(Enum):
    """同步状态枚举"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CONFLICT = "conflict"
    CANCELLED = "cancelled"


class ConflictResolution(Enum):
    """冲突解决策略枚举"""
    KEEP_LOCAL = "keep_local"
    KEEP_REMOTE = "keep_remote"
    MERGE = "merge"
    KEEP_NEWER = "keep_newer"
    MANUAL = "manual"


class IndexType(Enum):
    """索引类型枚举"""
    FULLTEXT = "fulltext"
    SEMANTIC = "semantic"
    TAG = "tag"
    CATEGORY = "category"
    PROJECT = "project"


class AuditAction(Enum):
    """审计动作枚举"""
    CREATE = "create"
    READ = "read"
    UPDATE = "update"
    DELETE = "delete"
    SHARE = "share"
    SYNC = "sync"
    PERMISSION_CHANGE = "permission_change"
    ACCESS_DENIED = "access_denied"


class KnowledgeSharingError(Exception):
    """知识共享基础异常类"""
    
    def __init__(self, message: str, knowledge_id: Optional[str] = None):
        super().__init__(message)
        self.knowledge_id = knowledge_id
    
    def __str__(self) -> str:
        base_msg = super().__str__()
        if self.knowledge_id:
            return f"{base_msg} (知识ID: {self.knowledge_id})"
        return base_msg


class KnowledgeNotFoundError(KnowledgeSharingError):
    """知识未找到异常"""
    pass


class PermissionDeniedError(KnowledgeSharingError):
    """权限拒绝异常"""
    pass


class SyncConflictError(KnowledgeSharingError):
    """同步冲突异常"""
    pass


class IndexBuildError(KnowledgeSharingError):
    """索引构建异常"""
    pass


@dataclass
class KnowledgeMetadata:
    """知识元数据"""
    knowledge_id: str
    title: str
    category: KnowledgeCategory
    tags: List[str] = field(default_factory=list)
    created_at: str = ""
    updated_at: str = ""
    version: int = 1
    author: str = ""
    source_project: str = ""
    checksum: str = ""
    custom_fields: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now().isoformat()
        if not self.updated_at:
            self.updated_at = self.created_at
        if isinstance(self.category, str):
            self.category = KnowledgeCategory(self.category)
    
    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data['category'] = self.category.value
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "KnowledgeMetadata":
        if isinstance(data.get('category'), str):
            data['category'] = KnowledgeCategory(data['category'])
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})
    
    def update_checksum(self, content: str) -> None:
        self.checksum = hashlib.md5(content.encode()).hexdigest()
    
    def increment_version(self) -> None:
        self.version += 1
        self.updated_at = datetime.now().isoformat()


@dataclass
class KnowledgeVersion:
    """知识版本记录"""
    version_id: str
    knowledge_id: str
    version_number: int
    content_hash: str
    changes: List[str]
    created_at: str
    created_by: str = "system"
    metadata_snapshot: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "KnowledgeVersion":
        return cls(**data)


@dataclass
class KnowledgeRegistration:
    """知识注册记录"""
    knowledge_id: str
    project_id: str
    registered_at: str
    permission_level: PermissionLevel = PermissionLevel.PRIVATE
    owner: str = "system"
    shared_with: List[str] = field(default_factory=list)
    metadata: KnowledgeMetadata = field(default_factory=KnowledgeMetadata)
    is_active: bool = True
    
    def __post_init__(self):
        if isinstance(self.permission_level, str):
            self.permission_level = PermissionLevel(self.permission_level)
        if isinstance(self.metadata, dict):
            self.metadata = KnowledgeMetadata.from_dict(self.metadata)
    
    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data['permission_level'] = self.permission_level.value
        data['metadata'] = self.metadata.to_dict()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "KnowledgeRegistration":
        if isinstance(data.get('permission_level'), str):
            data['permission_level'] = PermissionLevel(data['permission_level'])
        if isinstance(data.get('metadata'), dict):
            data['metadata'] = KnowledgeMetadata.from_dict(data['metadata'])
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


@dataclass
class IndexEntry:
    """索引条目"""
    knowledge_id: str
    index_type: IndexType
    indexed_value: str
    score: float = 1.0
    metadata: Dict[str, Any] = field(default_factory=dict)
    indexed_at: str = ""
    
    def __post_init__(self):
        if isinstance(self.index_type, str):
            self.index_type = IndexType(self.index_type)
        if not self.indexed_at:
            self.indexed_at = datetime.now().isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data['index_type'] = self.index_type.value
        return data


@dataclass
class SyncRecord:
    """同步记录"""
    sync_id: str
    source_project: str
    target_project: str
    knowledge_ids: List[str]
    status: SyncStatus
    started_at: str
    completed_at: str = ""
    error_message: str = ""
    conflicts: List[Dict[str, Any]] = field(default_factory=list)
    resolution: ConflictResolution = ConflictResolution.MANUAL
    bytes_transferred: int = 0
    
    def __post_init__(self):
        if isinstance(self.status, str):
            self.status = SyncStatus(self.status)
        if isinstance(self.resolution, str):
            self.resolution = ConflictResolution(self.resolution)
    
    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data['status'] = self.status.value
        data['resolution'] = self.resolution.value
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SyncRecord":
        if isinstance(data.get('status'), str):
            data['status'] = SyncStatus(data['status'])
        if isinstance(data.get('resolution'), str):
            data['resolution'] = ConflictResolution(data['resolution'])
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


@dataclass
class ConflictInfo:
    """冲突信息"""
    knowledge_id: str
    source_project: str
    target_project: str
    local_version: Dict[str, Any]
    remote_version: Dict[str, Any]
    detected_at: str
    conflict_type: str = "version"
    suggested_resolution: ConflictResolution = ConflictResolution.MANUAL
    
    def __post_init__(self):
        if isinstance(self.suggested_resolution, str):
            self.suggested_resolution = ConflictResolution(self.suggested_resolution)
    
    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data['suggested_resolution'] = self.suggested_resolution.value
        return data


@dataclass
class AccessControlEntry:
    """访问控制条目"""
    knowledge_id: str
    principal: str
    principal_type: str
    permissions: Set[PermissionLevel]
    granted_at: str
    granted_by: str
    expires_at: str = ""
    conditions: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        if isinstance(self.permissions, list):
            self.permissions = {
                PermissionLevel(p) if isinstance(p, str) else p 
                for p in self.permissions
            }
    
    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data['permissions'] = [p.value for p in self.permissions]
        return data
    
    def has_permission(self, level: PermissionLevel) -> bool:
        return level in self.permissions
    
    def is_expired(self) -> bool:
        if not self.expires_at:
            return False
        return datetime.now() > datetime.fromisoformat(self.expires_at)


@dataclass
class AuditLogEntry:
    """审计日志条目"""
    log_id: str
    knowledge_id: str
    action: AuditAction
    actor: str
    actor_project: str
    timestamp: str
    details: Dict[str, Any] = field(default_factory=dict)
    result: str = "success"
    ip_address: str = ""
    
    def __post_init__(self):
        if isinstance(self.action, str):
            self.action = AuditAction(self.action)
    
    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data['action'] = self.action.value
        return data


@dataclass
class AdvancedQuery:
    """高级查询"""
    query_text: str = ""
    categories: List[KnowledgeCategory] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    projects: List[str] = field(default_factory=list)
    date_range: Tuple[Optional[str], Optional[str]] = (None, None)
    permission_levels: List[PermissionLevel] = field(default_factory=list)
    min_version: int = 0
    include_inactive: bool = False
    sort_by: str = "relevance"
    limit: int = 50
    offset: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data['categories'] = [c.value for c in self.categories]
        data['permission_levels'] = [p.value for p in self.permission_levels]
        return data


class IStorageBackend(ABC):
    """存储后端接口"""
    
    @abstractmethod
    def initialize(self) -> None:
        pass
    
    @abstractmethod
    def save(self, key: str, data: Dict[str, Any]) -> bool:
        pass
    
    @abstractmethod
    def load(self, key: str) -> Optional[Dict[str, Any]]:
        pass
    
    @abstractmethod
    def delete(self, key: str) -> bool:
        pass
    
    @abstractmethod
    def list_keys(self, prefix: str = "") -> List[str]:
        pass
    
    @abstractmethod
    def exists(self, key: str) -> bool:
        pass


class JSONStorageBackend(IStorageBackend):
    """JSON文件存储后端"""
    
    def __init__(self, storage_path: Path):
        self.storage_path = storage_path
        self._data: Dict[str, Dict[str, Any]] = {}
        self._lock = threading.RLock()
    
    def initialize(self) -> None:
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self._load_all()
    
    def _load_all(self) -> None:
        for json_file in self.storage_path.glob("*.json"):
            try:
                key = json_file.stem
                self._data[key] = safe_read_json(json_file)
            except Exception as e:
                logger.error(f"加载数据失败: {json_file} - {e}")
    
    def _save_to_file(self, key: str) -> None:
        file_path = self.storage_path / f"{key}.json"
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(self._data.get(key, {}), f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"保存数据失败: {key} - {e}")
    
    def save(self, key: str, data: Dict[str, Any]) -> bool:
        with self._lock:
            self._data[key] = data
            self._save_to_file(key)
            return True
    
    def load(self, key: str) -> Optional[Dict[str, Any]]:
        with self._lock:
            return self._data.get(key)
    
    def delete(self, key: str) -> bool:
        with self._lock:
            if key in self._data:
                del self._data[key]
                file_path = self.storage_path / f"{key}.json"
                if file_path.exists():
                    file_path.unlink()
                return True
            return False
    
    def list_keys(self, prefix: str = "") -> List[str]:
        with self._lock:
            if prefix:
                return [k for k in self._data.keys() if k.startswith(prefix)]
            return list(self._data.keys())
    
    def exists(self, key: str) -> bool:
        with self._lock:
            return key in self._data


class CentralizedKnowledgeHub:
    """中心化知识中心
    
    提供知识库的中心化管理，包括注册、分类、标签和版本管理。
    
    功能：
    - 知识注册和注销
    - 知识分类和标签管理
    - 知识版本管理
    - 知识元数据管理
    """
    
    DEFAULT_STORAGE_DIR = "centralized_knowledge_hub"
    
    def __init__(
        self,
        storage_path: Optional[Path] = None,
        auto_initialize: bool = True
    ):
        self.storage_path = storage_path or Path(f"./{self.DEFAULT_STORAGE_DIR}")
        self._backend: Optional[IStorageBackend] = None
        self._registrations: Dict[str, KnowledgeRegistration] = {}
        self._versions: Dict[str, List[KnowledgeVersion]] = defaultdict(list)
        self._category_index: Dict[KnowledgeCategory, Set[str]] = defaultdict(set)
        self._tag_index: Dict[str, Set[str]] = defaultdict(set)
        self._project_index: Dict[str, Set[str]] = defaultdict(set)
        self._lock = threading.RLock()
        
        if auto_initialize:
            self.initialize()
    
    def initialize(self) -> None:
        self._backend = JSONStorageBackend(self.storage_path / "data")
        self._backend.initialize()
        self._load_registrations()
        self._rebuild_indexes()
        logger.info(f"中心化知识中心初始化完成: {self.storage_path}")
    
    def _load_registrations(self) -> None:
        for key in self._backend.list_keys("reg_"):
            data = self._backend.load(key)
            if data:
                try:
                    reg = KnowledgeRegistration.from_dict(data)
                    self._registrations[reg.knowledge_id] = reg
                except Exception as e:
                    logger.error(f"加载注册记录失败: {key} - {e}")
        
        for key in self._backend.list_keys("ver_"):
            data = self._backend.load(key)
            if data:
                try:
                    version = KnowledgeVersion.from_dict(data)
                    self._versions[version.knowledge_id].append(version)
                except Exception as e:
                    logger.error(f"加载版本记录失败: {key} - {e}")
        
        for kid, versions in self._versions.items():
            self._versions[kid] = sorted(versions, key=lambda v: v.version_number)
        
        logger.info(f"加载 {len(self._registrations)} 条知识注册记录")
    
    def _rebuild_indexes(self) -> None:
        self._category_index.clear()
        self._tag_index.clear()
        self._project_index.clear()
        
        for kid, reg in self._registrations.items():
            if reg.is_active:
                self._category_index[reg.metadata.category].add(kid)
                for tag in reg.metadata.tags:
                    self._tag_index[tag.lower()].add(kid)
                self._project_index[reg.project_id].add(kid)
    
    def register_knowledge(
        self,
        knowledge_id: str,
        project_id: str,
        metadata: KnowledgeMetadata,
        content: Optional[str] = None,
        permission_level: PermissionLevel = PermissionLevel.PRIVATE,
        owner: str = "system"
    ) -> KnowledgeRegistration:
        with self._lock:
            if knowledge_id in self._registrations:
                raise KnowledgeSharingError(f"知识已注册: {knowledge_id}", knowledge_id)
            
            if content:
                metadata.update_checksum(content)
            
            registration = KnowledgeRegistration(
                knowledge_id=knowledge_id,
                project_id=project_id,
                registered_at=datetime.now().isoformat(),
                permission_level=permission_level,
                owner=owner,
                metadata=metadata
            )
            
            self._registrations[knowledge_id] = registration
            
            self._category_index[metadata.category].add(knowledge_id)
            for tag in metadata.tags:
                self._tag_index[tag.lower()].add(knowledge_id)
            self._project_index[project_id].add(knowledge_id)
            
            self._save_registration(registration)
            
            self._create_initial_version(knowledge_id, metadata, content)
            
            logger.info(f"注册知识: {knowledge_id} (项目: {project_id})")
            return registration
    
    def _save_registration(self, registration: KnowledgeRegistration) -> None:
        if self._backend:
            key = f"reg_{registration.knowledge_id}"
            self._backend.save(key, registration.to_dict())
    
    def _create_initial_version(
        self,
        knowledge_id: str,
        metadata: KnowledgeMetadata,
        content: Optional[str]
    ) -> None:
        version = KnowledgeVersion(
            version_id=f"ver_{knowledge_id}_1",
            knowledge_id=knowledge_id,
            version_number=1,
            content_hash=metadata.checksum,
            changes=["初始版本"],
            created_at=datetime.now().isoformat(),
            metadata_snapshot=metadata.to_dict()
        )
        
        self._versions[knowledge_id].append(version)
        self._save_version(version)
    
    def _save_version(self, version: KnowledgeVersion) -> None:
        if self._backend:
            key = f"ver_{version.knowledge_id}_{version.version_number}"
            self._backend.save(key, version.to_dict())
    
    def unregister_knowledge(
        self,
        knowledge_id: str,
        soft_delete: bool = True
    ) -> bool:
        with self._lock:
            registration = self._registrations.get(knowledge_id)
            if not registration:
                return False
            
            if soft_delete:
                registration.is_active = False
                self._save_registration(registration)
            else:
                del self._registrations[knowledge_id]
                
                if self._backend:
                    self._backend.delete(f"reg_{knowledge_id}")
                    for version in self._versions.get(knowledge_id, []):
                        self._backend.delete(f"ver_{knowledge_id}_{version.version_number}")
                    self._versions.pop(knowledge_id, None)
            
            self._rebuild_indexes()
            
            logger.info(f"注销知识: {knowledge_id} (软删除: {soft_delete})")
            return True
    
    def update_knowledge(
        self,
        knowledge_id: str,
        updates: Dict[str, Any],
        content: Optional[str] = None,
        updated_by: str = "system"
    ) -> Optional[KnowledgeRegistration]:
        with self._lock:
            registration = self._registrations.get(knowledge_id)
            if not registration:
                return None
            
            old_category = registration.metadata.category
            old_tags = registration.metadata.tags.copy()
            
            changes = []
            for key, value in updates.items():
                if hasattr(registration.metadata, key):
                    old_value = getattr(registration.metadata, key)
                    if old_value != value:
                        changes.append(f"{key}: {old_value} -> {value}")
                        setattr(registration.metadata, key, value)
            
            if content:
                registration.metadata.update_checksum(content)
            
            if changes:
                registration.metadata.increment_version()
                
                version = KnowledgeVersion(
                    version_id=f"ver_{knowledge_id}_{registration.metadata.version}",
                    knowledge_id=knowledge_id,
                    version_number=registration.metadata.version,
                    content_hash=registration.metadata.checksum,
                    changes=changes,
                    created_at=datetime.now().isoformat(),
                    created_by=updated_by,
                    metadata_snapshot=registration.metadata.to_dict()
                )
                
                self._versions[knowledge_id].append(version)
                self._save_version(version)
            
            if old_category != registration.metadata.category:
                self._category_index[old_category].discard(knowledge_id)
                self._category_index[registration.metadata.category].add(knowledge_id)
            
            old_tag_set = set(t.lower() for t in old_tags)
            new_tag_set = set(t.lower() for t in registration.metadata.tags)
            
            for tag in old_tag_set - new_tag_set:
                self._tag_index[tag].discard(knowledge_id)
            for tag in new_tag_set - old_tag_set:
                self._tag_index[tag].add(knowledge_id)
            
            self._save_registration(registration)
            
            logger.info(f"更新知识: {knowledge_id} - {len(changes)} 个变更")
            return registration
    
    def get_knowledge(self, knowledge_id: str) -> Optional[KnowledgeRegistration]:
        return self._registrations.get(knowledge_id)
    
    def get_knowledge_versions(
        self,
        knowledge_id: str,
        limit: int = 10
    ) -> List[KnowledgeVersion]:
        versions = self._versions.get(knowledge_id, [])
        return versions[-limit:]
    
    def rollback_version(
        self,
        knowledge_id: str,
        target_version: int
    ) -> Optional[KnowledgeRegistration]:
        with self._lock:
            registration = self._registrations.get(knowledge_id)
            if not registration:
                return None
            
            versions = self._versions.get(knowledge_id, [])
            target = None
            for v in versions:
                if v.version_number == target_version:
                    target = v
                    break
            
            if not target:
                return None
            
            old_metadata = registration.metadata
            registration.metadata = KnowledgeMetadata.from_dict(target.metadata_snapshot)
            registration.metadata.version = len(versions) + 1
            registration.metadata.updated_at = datetime.now().isoformat()
            
            version = KnowledgeVersion(
                version_id=f"ver_{knowledge_id}_{registration.metadata.version}",
                knowledge_id=knowledge_id,
                version_number=registration.metadata.version,
                content_hash=registration.metadata.checksum,
                changes=[f"回滚到版本 {target_version}"],
                created_at=datetime.now().isoformat(),
                created_by="system",
                metadata_snapshot=registration.metadata.to_dict()
            )
            
            self._versions[knowledge_id].append(version)
            self._save_version(version)
            
            self._rebuild_indexes()
            self._save_registration(registration)
            
            logger.info(f"回滚知识: {knowledge_id} 到版本 {target_version}")
            return registration
    
    def list_knowledge(
        self,
        category: Optional[KnowledgeCategory] = None,
        tags: Optional[List[str]] = None,
        project_id: Optional[str] = None,
        include_inactive: bool = False,
        limit: int = 100
    ) -> List[KnowledgeRegistration]:
        with self._lock:
            results = []
            
            for kid, reg in self._registrations.items():
                if not include_inactive and not reg.is_active:
                    continue
                
                if category and reg.metadata.category != category:
                    continue
                
                if tags:
                    reg_tags_lower = {t.lower() for t in reg.metadata.tags}
                    filter_tags_lower = {t.lower() for t in tags}
                    if not (reg_tags_lower & filter_tags_lower):
                        continue
                
                if project_id and reg.project_id != project_id:
                    continue
                
                results.append(reg)
            
            return results[:limit]
    
    def search_by_tags(
        self,
        tags: List[str],
        match_all: bool = False
    ) -> List[KnowledgeRegistration]:
        with self._lock:
            if not tags:
                return []
            
            tags_lower = [t.lower() for t in tags]
            
            if match_all:
                result_ids = None
                for tag in tags_lower:
                    tag_ids = self._tag_index.get(tag, set())
                    if result_ids is None:
                        result_ids = tag_ids.copy()
                    else:
                        result_ids &= tag_ids
                result_ids = result_ids or set()
            else:
                result_ids = set()
                for tag in tags_lower:
                    result_ids |= self._tag_index.get(tag, set())
            
            return [
                self._registrations[kid] 
                for kid in result_ids 
                if kid in self._registrations and self._registrations[kid].is_active
            ]
    
    def get_categories(self) -> List[KnowledgeCategory]:
        return list(self._category_index.keys())
    
    def get_tags(self, min_count: int = 1) -> List[Tuple[str, int]]:
        tag_counts = [
            (tag, len(kids)) 
            for tag, kids in self._tag_index.items() 
            if len(kids) >= min_count
        ]
        return sorted(tag_counts, key=lambda x: x[1], reverse=True)
    
    def add_knowledge(
        self,
        knowledge_item: Any,
        project_id: str = "default",
        auto_id: bool = True
    ) -> KnowledgeRegistration:
        with self._lock:
            knowledge_id = knowledge_item.knowledge_id
            if auto_id and (not knowledge_id or knowledge_id == ""):
                knowledge_id = knowledge_item.generate_id()
            
            category_map = {
                "fix_pattern": KnowledgeCategory.FIX_PATTERN,
                "best_practice": KnowledgeCategory.BEST_PRACTICE,
                "diagnosis": KnowledgeCategory.DIAGNOSIS,
                "code_pattern": KnowledgeCategory.CODE_PATTERN,
            }
            
            knowledge_type_str = knowledge_item.knowledge_type.value if hasattr(knowledge_item.knowledge_type, 'value') else str(knowledge_item.knowledge_type)
            category = category_map.get(knowledge_type_str, KnowledgeCategory.OTHER)
            
            metadata = KnowledgeMetadata(
                knowledge_id=knowledge_id,
                title=knowledge_item.title,
                category=category,
                tags=knowledge_item.tags,
                author=knowledge_item.metadata.get("author", "system") if hasattr(knowledge_item, 'metadata') else "system",
                source_project=project_id,
                custom_fields=knowledge_item.metadata if hasattr(knowledge_item, 'metadata') else {}
            )
            
            return self.register_knowledge(
                knowledge_id=knowledge_id,
                project_id=project_id,
                metadata=metadata,
                content=knowledge_item.content if hasattr(knowledge_item, 'content') else None,
                permission_level=PermissionLevel.PRIVATE,
                owner="system"
            )
    
    def search(
        self,
        query: str,
        mode: str = "keyword",
        project_id: Optional[str] = None,
        limit: int = 50
    ) -> List[Any]:
        with self._lock:
            results = []
            
            for kid, reg in self._registrations.items():
                if not reg.is_active:
                    continue
                
                if project_id and reg.project_id != project_id:
                    continue
                
                score = 0.0
                query_lower = query.lower()
                
                if query_lower in reg.metadata.title.lower():
                    score += 2.0
                if query_lower in ' '.join(reg.metadata.tags).lower():
                    score += 1.0
                if query_lower in reg.metadata.category.value.lower():
                    score += 0.5
                
                if score > 0:
                    results.append((reg, score))
            
            results.sort(key=lambda x: x[1], reverse=True)
            return [reg for reg, score in results[:limit]]
    
    def get_statistics(self) -> Dict[str, Any]:
        with self._lock:
            active_count = sum(1 for r in self._registrations.values() if r.is_active)
            
            category_counts = {
                cat.value: len(kids) 
                for cat, kids in self._category_index.items()
            }
            
            project_counts = {
                proj: len(kids) 
                for proj, kids in self._project_index.items()
            }
            
            total_versions = sum(len(v) for v in self._versions.values())
            
            return {
                "total_knowledge": len(self._registrations),
                "active_knowledge": active_count,
                "inactive_knowledge": len(self._registrations) - active_count,
                "by_category": category_counts,
                "by_project": project_counts,
                "total_tags": len(self._tag_index),
                "total_versions": total_versions,
                "storage_path": str(self.storage_path)
            }
    
    def export_knowledge(
        self,
        output_path: str,
        knowledge_ids: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        export_data = {
            "exported_at": datetime.now().isoformat(),
            "registrations": [],
            "versions": {}
        }
        
        ids_to_export = knowledge_ids or list(self._registrations.keys())
        
        for kid in ids_to_export:
            reg = self._registrations.get(kid)
            if reg:
                export_data["registrations"].append(reg.to_dict())
                export_data["versions"][kid] = [
                    v.to_dict() for v in self._versions.get(kid, [])
                ]
        
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"导出知识: {len(export_data['registrations'])} 条 -> {output_path}")
        return export_data
    
    def import_knowledge(
        self,
        input_path: str,
        merge_strategy: str = "skip"
    ) -> Dict[str, Any]:
        data = safe_read_json(Path(input_path))
        
        stats = {
            "imported": 0,
            "skipped": 0,
            "updated": 0,
            "errors": []
        }
        
        with self._lock:
            for reg_data in data.get("registrations", []):
                try:
                    reg = KnowledgeRegistration.from_dict(reg_data)
                    
                    existing = self._registrations.get(reg.knowledge_id)
                    
                    if existing:
                        if merge_strategy == "skip":
                            stats["skipped"] += 1
                            continue
                        elif merge_strategy == "update":
                            self._registrations[reg.knowledge_id] = reg
                            stats["updated"] += 1
                        elif merge_strategy == "overwrite":
                            self._registrations[reg.knowledge_id] = reg
                            stats["imported"] += 1
                    else:
                        self._registrations[reg.knowledge_id] = reg
                        stats["imported"] += 1
                    
                    versions_data = data.get("versions", {}).get(reg.knowledge_id, [])
                    for ver_data in versions_data:
                        version = KnowledgeVersion.from_dict(ver_data)
                        if version not in self._versions[reg.knowledge_id]:
                            self._versions[reg.knowledge_id].append(version)
                    
                    self._save_registration(reg)
                    
                except Exception as e:
                    stats["errors"].append(f"{reg_data.get('knowledge_id', 'unknown')}: {e}")
            
            self._rebuild_indexes()
        
        logger.info(f"导入知识: 导入 {stats['imported']}, 更新 {stats['updated']}, 跳过 {stats['skipped']}")
        return stats


class KnowledgeIndexer:
    """知识索引器
    
    提供全文索引、语义索引和高级查询功能。
    
    功能：
    - 全文索引构建和搜索
    - 语义索引接口
    - 标签和分类索引
    - 高级查询支持
    """
    
    def __init__(self, hub: CentralizedKnowledgeHub):
        self.hub = hub
        self._fulltext_index: Dict[str, List[Tuple[str, float]]] = defaultdict(list)
        self._semantic_index: Dict[str, List[float]] = {}
        self._embedding_func: Optional[Callable[[str], List[float]]] = None
        self._index_metadata: Dict[str, Dict[str, Any]] = {}
        self._lock = threading.RLock()
    
    def set_embedding_function(
        self,
        func: Callable[[str], List[float]]
    ) -> None:
        self._embedding_func = func
        logger.info("已设置语义嵌入函数")
    
    def build_fulltext_index(self) -> None:
        with self._lock:
            self._fulltext_index.clear()
            
            registrations = self.hub.list_knowledge(limit=10000)
            
            for reg in registrations:
                self._index_registration_fulltext(reg)
            
            logger.info(f"构建全文索引完成: {len(registrations)} 条知识, {len(self._fulltext_index)} 个词")
    
    def _index_registration_fulltext(
        self,
        registration: KnowledgeRegistration
    ) -> None:
        text = f"{registration.metadata.title} {' '.join(registration.metadata.tags)}"
        
        words = self._tokenize(text)
        
        word_count = len(words)
        if word_count == 0:
            return
        
        word_freq: Dict[str, int] = defaultdict(int)
        for word in words:
            word_freq[word] += 1
        
        for word, freq in word_freq.items():
            score = freq / word_count
            self._fulltext_index[word].append((registration.knowledge_id, score))
        
        self._index_metadata[registration.knowledge_id] = {
            "indexed_at": datetime.now().isoformat(),
            "word_count": word_count
        }
    
    def _tokenize(self, text: str) -> List[str]:
        words = []
        
        words.extend(re.findall(r'\w+', text.lower()))
        
        for i in range(len(text) - 1):
            bigram = text[i:i+2].lower()
            if re.match(r'\w\w', bigram):
                words.append(bigram)
        
        return [w for w in words if len(w) > 1]
    
    def build_semantic_index(self) -> None:
        with self._lock:
            self._semantic_index.clear()
            
            registrations = self.hub.list_knowledge(limit=10000)
            
            for reg in registrations:
                try:
                    text = f"{reg.metadata.title} {' '.join(reg.metadata.tags)}"
                    
                    if self._embedding_func:
                        embedding = self._embedding_func(text)
                    else:
                        embedding = self._generate_simple_embedding(text)
                    
                    self._semantic_index[reg.knowledge_id] = embedding
                    
                except Exception as e:
                    logger.warning(f"生成语义索引失败: {reg.knowledge_id} - {e}")
            
            logger.info(f"构建语义索引完成: {len(self._semantic_index)} 条知识")
    
    def _generate_simple_embedding(self, text: str) -> List[float]:
        words = re.findall(r'\w+', text.lower())
        
        embedding = [0.0] * 128
        for i, word in enumerate(words[:128]):
            hash_val = hash(word) % 1000 / 1000.0
            embedding[i % 128] += hash_val
        
        norm = sum(v * v for v in embedding) ** 0.5
        if norm > 0:
            embedding = [v / norm for v in embedding]
        
        return embedding
    
    def build_all_indexes(self) -> None:
        self.build_fulltext_index()
        self.build_semantic_index()
        logger.info("所有索引构建完成")
    
    def update_index(
        self,
        knowledge_id: str,
        registration: KnowledgeRegistration
    ) -> None:
        with self._lock:
            self._remove_from_fulltext_index(knowledge_id)
            self._index_registration_fulltext(registration)
            
            text = f"{registration.metadata.title} {' '.join(registration.metadata.tags)}"
            if self._embedding_func:
                try:
                    self._semantic_index[knowledge_id] = self._embedding_func(text)
                except Exception as e:
                    logger.warning(f"更新语义索引失败: {knowledge_id} - {e}")
            else:
                self._semantic_index[knowledge_id] = self._generate_simple_embedding(text)
    
    def _remove_from_fulltext_index(self, knowledge_id: str) -> None:
        for word in list(self._fulltext_index.keys()):
            self._fulltext_index[word] = [
                (kid, score) for kid, score in self._fulltext_index[word]
                if kid != knowledge_id
            ]
            if not self._fulltext_index[word]:
                del self._fulltext_index[word]
        
        self._index_metadata.pop(knowledge_id, None)
    
    def search_fulltext(
        self,
        query: str,
        limit: int = 50
    ) -> List[Tuple[str, float]]:
        with self._lock:
            query_words = self._tokenize(query)
            
            scores: Dict[str, float] = defaultdict(float)
            
            for word in query_words:
                if word in self._fulltext_index:
                    for kid, score in self._fulltext_index[word]:
                        scores[kid] += score
            
            results = sorted(scores.items(), key=lambda x: x[1], reverse=True)
            return results[:limit]
    
    def search_semantic(
        self,
        query: str,
        threshold: float = 0.5,
        limit: int = 10
    ) -> List[Tuple[str, float]]:
        with self._lock:
            if not self._semantic_index:
                return []
            
            if self._embedding_func:
                query_embedding = self._embedding_func(query)
            else:
                query_embedding = self._generate_simple_embedding(query)
            
            results = []
            for kid, embedding in self._semantic_index.items():
                similarity = self._cosine_similarity(query_embedding, embedding)
                if similarity >= threshold:
                    results.append((kid, similarity))
            
            results.sort(key=lambda x: x[1], reverse=True)
            return results[:limit]
    
    def _cosine_similarity(
        self,
        vec1: List[float],
        vec2: List[float]
    ) -> float:
        if len(vec1) != len(vec2):
            return 0.0
        
        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        norm1 = sum(a * a for a in vec1) ** 0.5
        norm2 = sum(b * b for b in vec2) ** 0.5
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        return dot_product / (norm1 * norm2)
    
    def advanced_search(
        self,
        query: str,
        filters: Optional[Dict[str, Any]] = None,
        mode: str = "hybrid"
    ) -> List[Tuple[KnowledgeRegistration, float]]:
        with self._lock:
            filters = filters or {}
            
            if mode == "fulltext":
                search_results = self.search_fulltext(query, limit=100)
            elif mode == "semantic":
                search_results = self.search_semantic(query, threshold=0.3, limit=100)
            else:
                ft_results = dict(self.search_fulltext(query, limit=100))
                sem_results = dict(self.search_semantic(query, threshold=0.3, limit=100))
                
                all_kids = set(ft_results.keys()) | set(sem_results.keys())
                search_results = []
                for kid in all_kids:
                    ft_score = ft_results.get(kid, 0)
                    sem_score = sem_results.get(kid, 0)
                    combined = 0.6 * ft_score + 0.4 * sem_score
                    search_results.append((kid, combined))
                search_results.sort(key=lambda x: x[1], reverse=True)
            
            results = []
            for kid, score in search_results:
                reg = self.hub.get_knowledge(kid)
                if not reg or not reg.is_active:
                    continue
                
                if not self._matches_filters(reg, filters):
                    continue
                
                results.append((reg, score))
            
            return results[:filters.get("limit", 50)]
    
    def _matches_filters(
        self,
        registration: KnowledgeRegistration,
        filters: Dict[str, Any]
    ) -> bool:
        if "category" in filters:
            cat = filters["category"]
            if isinstance(cat, KnowledgeCategory):
                cat = cat.value
            if registration.metadata.category.value != cat:
                return False
        
        if "tags" in filters:
            filter_tags = {t.lower() for t in filters["tags"]}
            reg_tags = {t.lower() for t in registration.metadata.tags}
            if not (filter_tags & reg_tags):
                return False
        
        if "project_id" in filters:
            if registration.project_id != filters["project_id"]:
                return False
        
        if "permission_level" in filters:
            perm = filters["permission_level"]
            if isinstance(perm, PermissionLevel):
                perm = perm.value
            if registration.permission_level.value != perm:
                return False
        
        if "min_version" in filters:
            if registration.metadata.version < filters["min_version"]:
                return False
        
        return True
    
    def get_index_statistics(self) -> Dict[str, Any]:
        with self._lock:
            return {
                "fulltext_words": len(self._fulltext_index),
                "semantic_indexed": len(self._semantic_index),
                "indexed_items": len(self._index_metadata),
                "has_embedding_func": self._embedding_func is not None
            }
    
    def export_index(self, output_path: str) -> None:
        with self._lock:
            data = {
                "fulltext_index": dict(self._fulltext_index),
                "semantic_index": self._semantic_index,
                "index_metadata": self._index_metadata,
                "exported_at": datetime.now().isoformat()
            }
            
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"索引已导出: {output_path}")
    
    def import_index(self, input_path: str) -> None:
        with open(input_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        with self._lock:
            self._fulltext_index = defaultdict(list, data.get("fulltext_index", {}))
            self._semantic_index = data.get("semantic_index", {})
            self._index_metadata = data.get("index_metadata", {})
        
        logger.info(f"索引已导入: {input_path}")


class KnowledgeSynchronizer:
    """知识同步器
    
    实现跨项目知识的增量同步和冲突处理。
    
    功能：
    - 增量同步
    - 冲突检测和解决
    - 同步状态追踪
    - 同步历史记录
    """
    
    def __init__(
        self,
        hub: CentralizedKnowledgeHub,
        storage_path: Optional[Path] = None
    ):
        self.hub = hub
        self.storage_path = storage_path or hub.storage_path / "sync"
        self._sync_records: Dict[str, SyncRecord] = {}
        self._sync_history: List[SyncRecord] = []
        self._change_log: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        self._lock = threading.RLock()
        
        self._ensure_storage()
    
    def _ensure_storage(self) -> None:
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self._load_sync_history()
    
    def _load_sync_history(self) -> None:
        history_file = self.storage_path / "sync_history.json"
        if history_file.exists():
            try:
                data = safe_read_json(history_file)
                self._sync_history = [
                    SyncRecord.from_dict(r) for r in data.get("history", [])
                ]
                logger.info(f"加载同步历史: {len(self._sync_history)} 条记录")
            except Exception as e:
                logger.error(f"加载同步历史失败: {e}")
    
    def _save_sync_history(self) -> None:
        history_file = self.storage_path / "sync_history.json"
        try:
            data = {
                "history": [r.to_dict() for r in self._sync_history[-1000:]],
                "updated_at": datetime.now().isoformat()
            }
            with open(history_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"保存同步历史失败: {e}")
    
    def record_change(
        self,
        knowledge_id: str,
        project_id: str,
        change_type: str,
        change_data: Dict[str, Any]
    ) -> None:
        with self._lock:
            key = f"{project_id}:{knowledge_id}"
            self._change_log[key].append({
                "type": change_type,
                "data": change_data,
                "timestamp": datetime.now().isoformat()
            })
    
    def get_changes_since(
        self,
        project_id: str,
        since: str
    ) -> List[Dict[str, Any]]:
        with self._lock:
            changes = []
            for key, log in self._change_log.items():
                if key.startswith(f"{project_id}:"):
                    for entry in log:
                        if entry["timestamp"] > since:
                            changes.append({
                                "key": key,
                                **entry
                            })
            return sorted(changes, key=lambda x: x["timestamp"])
    
    def sync_incremental(
        self,
        source_project: str,
        target_project: str,
        knowledge_ids: Optional[List[str]] = None,
        resolution_strategy: ConflictResolution = ConflictResolution.KEEP_NEWER
    ) -> SyncRecord:
        sync_id = self._generate_sync_id(source_project, target_project)
        
        record = SyncRecord(
            sync_id=sync_id,
            source_project=source_project,
            target_project=target_project,
            knowledge_ids=knowledge_ids or [],
            status=SyncStatus.PENDING,
            started_at=datetime.now().isoformat(),
            resolution=resolution_strategy
        )
        
        self._sync_records[sync_id] = record
        
        try:
            record.status = SyncStatus.IN_PROGRESS
            
            if not knowledge_ids:
                source_knowledge = self.hub.list_knowledge(project_id=source_project)
                knowledge_ids = [k.knowledge_id for k in source_knowledge]
                record.knowledge_ids = knowledge_ids
            
            conflicts = []
            synced_count = 0
            
            for kid in knowledge_ids:
                source_reg = self.hub.get_knowledge(kid)
                if not source_reg or source_reg.project_id != source_project:
                    continue
                
                target_reg = self.hub.get_knowledge(kid)
                
                if target_reg and target_reg.project_id == target_project:
                    conflict = self._detect_conflict(source_reg, target_reg)
                    if conflict:
                        conflicts.append(conflict.to_dict())
                        
                        resolved = self._resolve_conflict(
                            conflict, 
                            resolution_strategy,
                            source_reg,
                            target_reg
                        )
                        if resolved:
                            synced_count += 1
                        continue
                
                new_reg = self._copy_registration(
                    source_reg, 
                    target_project
                )
                if new_reg:
                    synced_count += 1
            
            if conflicts:
                record.status = SyncStatus.CONFLICT
                record.conflicts = conflicts
            else:
                record.status = SyncStatus.COMPLETED
            
            record.completed_at = datetime.now().isoformat()
            record.bytes_transferred = synced_count * 1024
            
        except Exception as e:
            record.status = SyncStatus.FAILED
            record.error_message = str(e)
            logger.error(f"同步失败: {sync_id} - {e}")
        
        self._sync_history.append(record)
        self._save_sync_history()
        
        logger.info(f"同步完成: {sync_id} - {record.status.value}")
        return record
    
    def _generate_sync_id(
        self,
        source: str,
        target: str
    ) -> str:
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        hash_part = hashlib.md5(f"{source}-{target}".encode()).hexdigest()[:6]
        return f"SYNC-{timestamp}-{hash_part}"
    
    def _detect_conflict(
        self,
        source: KnowledgeRegistration,
        target: KnowledgeRegistration
    ) -> Optional[ConflictInfo]:
        if source.metadata.checksum == target.metadata.checksum:
            return None
        
        if source.metadata.updated_at > target.metadata.updated_at:
            return None
        
        return ConflictInfo(
            knowledge_id=source.knowledge_id,
            source_project=source.project_id,
            target_project=target.project_id,
            local_version=target.metadata.to_dict(),
            remote_version=source.metadata.to_dict(),
            detected_at=datetime.now().isoformat(),
            conflict_type="version"
        )
    
    def _resolve_conflict(
        self,
        conflict: ConflictInfo,
        strategy: ConflictResolution,
        source: KnowledgeRegistration,
        target: KnowledgeRegistration
    ) -> bool:
        if strategy == ConflictResolution.KEEP_LOCAL:
            return True
        
        elif strategy == ConflictResolution.KEEP_REMOTE:
            self.hub.update_knowledge(
                target.knowledge_id,
                source.metadata.to_dict()
            )
            return True
        
        elif strategy == ConflictResolution.KEEP_NEWER:
            source_time = datetime.fromisoformat(source.metadata.updated_at)
            target_time = datetime.fromisoformat(target.metadata.updated_at)
            
            if source_time > target_time:
                self.hub.update_knowledge(
                    target.knowledge_id,
                    source.metadata.to_dict()
                )
            return True
        
        elif strategy == ConflictResolution.MERGE:
            merged_tags = list(set(
                source.metadata.tags + target.metadata.tags
            ))
            
            merged_data = {
                "tags": merged_tags,
                "version": max(source.metadata.version, target.metadata.version) + 1
            }
            
            self.hub.update_knowledge(target.knowledge_id, merged_data)
            return True
        
        return False
    
    def _copy_registration(
        self,
        source: KnowledgeRegistration,
        target_project: str
    ) -> Optional[KnowledgeRegistration]:
        try:
            new_metadata = KnowledgeMetadata(
                knowledge_id=source.knowledge_id,
                title=source.metadata.title,
                category=source.metadata.category,
                tags=source.metadata.tags.copy(),
                author=source.metadata.author,
                source_project=source.project_id,
                custom_fields={
                    **source.metadata.custom_fields,
                    "synced_from": source.project_id,
                    "synced_at": datetime.now().isoformat()
                }
            )
            
            return self.hub.register_knowledge(
                knowledge_id=source.knowledge_id,
                project_id=target_project,
                metadata=new_metadata,
                permission_level=source.permission_level,
                owner=source.owner
            )
        except KnowledgeSharingError:
            return None
    
    def get_sync_status(self, sync_id: str) -> Optional[SyncRecord]:
        return self._sync_records.get(sync_id)
    
    def get_sync_history(
        self,
        project_id: Optional[str] = None,
        limit: int = 50
    ) -> List[SyncRecord]:
        with self._lock:
            history = self._sync_history
            
            if project_id:
                history = [
                    r for r in history
                    if r.source_project == project_id or r.target_project == project_id
                ]
            
            return history[-limit:]
    
    def cancel_sync(self, sync_id: str) -> bool:
        with self._lock:
            record = self._sync_records.get(sync_id)
            if not record:
                return False
            
            if record.status in (SyncStatus.PENDING, SyncStatus.IN_PROGRESS):
                record.status = SyncStatus.CANCELLED
                record.completed_at = datetime.now().isoformat()
                return True
            
            return False
    
    def retry_sync(
        self,
        sync_id: str,
        resolution_strategy: Optional[ConflictResolution] = None
    ) -> Optional[SyncRecord]:
        old_record = self._sync_records.get(sync_id)
        if not old_record:
            return None
        
        return self.sync_incremental(
            source_project=old_record.source_project,
            target_project=old_record.target_project,
            knowledge_ids=old_record.knowledge_ids,
            resolution_strategy=resolution_strategy or old_record.resolution
        )
    
    def get_sync_statistics(self) -> Dict[str, Any]:
        with self._lock:
            status_counts: Dict[str, int] = defaultdict(int)
            for record in self._sync_history:
                status_counts[record.status.value] += 1
            
            return {
                "total_syncs": len(self._sync_history),
                "by_status": dict(status_counts),
                "pending_changes": sum(len(v) for v in self._change_log.values()),
                "recent_syncs": len([r for r in self._sync_history[-10:] 
                                    if r.status == SyncStatus.COMPLETED])
            }


class KnowledgeAccessControl:
    """知识访问控制
    
    实现知识的权限管理和审计功能。
    
    功能：
    - 权限级别管理
    - 访问控制列表
    - 权限审计
    - 权限继承
    """
    
    def __init__(
        self,
        hub: CentralizedKnowledgeHub,
        storage_path: Optional[Path] = None
    ):
        self.hub = hub
        self.storage_path = storage_path or hub.storage_path / "access_control"
        self._acl: Dict[str, List[AccessControlEntry]] = defaultdict(list)
        self._audit_log: List[AuditLogEntry] = []
        self._role_permissions: Dict[str, Set[PermissionLevel]] = {
            "admin": {PermissionLevel.ADMIN, PermissionLevel.PUBLIC, 
                     PermissionLevel.SHARED, PermissionLevel.READ_ONLY},
            "editor": {PermissionLevel.PUBLIC, PermissionLevel.SHARED, 
                      PermissionLevel.READ_ONLY},
            "viewer": {PermissionLevel.PUBLIC, PermissionLevel.READ_ONLY},
            "guest": {PermissionLevel.PUBLIC}
        }
        self._lock = threading.RLock()
        
        self._ensure_storage()
    
    def _ensure_storage(self) -> None:
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self._load_acl()
        self._load_audit_log()
    
    def _load_acl(self) -> None:
        acl_file = self.storage_path / "access_control_list.json"
        if acl_file.exists():
            try:
                data = safe_read_json(acl_file)
                for kid, entries in data.get("acl", {}).items():
                    self._acl[kid] = [
                        AccessControlEntry(
                            knowledge_id=e["knowledge_id"],
                            principal=e["principal"],
                            principal_type=e["principal_type"],
                            permissions={
                                PermissionLevel(p) for p in e.get("permissions", [])
                            },
                            granted_at=e["granted_at"],
                            granted_by=e["granted_by"],
                            expires_at=e.get("expires_at", ""),
                            conditions=e.get("conditions", {})
                        )
                        for e in entries
                    ]
                logger.info(f"加载访问控制列表: {sum(len(v) for v in self._acl.values())} 条")
            except Exception as e:
                logger.error(f"加载访问控制列表失败: {e}")
    
    def _save_acl(self) -> None:
        acl_file = self.storage_path / "access_control_list.json"
        try:
            data = {
                "acl": {
                    kid: [e.to_dict() for e in entries]
                    for kid, entries in self._acl.items()
                },
                "updated_at": datetime.now().isoformat()
            }
            with open(acl_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"保存访问控制列表失败: {e}")
    
    def _load_audit_log(self) -> None:
        audit_file = self.storage_path / "audit_log.json"
        if audit_file.exists():
            try:
                data = safe_read_json(audit_file)
                self._audit_log = [
                    AuditLogEntry(
                        log_id=e["log_id"],
                        knowledge_id=e["knowledge_id"],
                        action=AuditAction(e["action"]),
                        actor=e["actor"],
                        actor_project=e["actor_project"],
                        timestamp=e["timestamp"],
                        details=e.get("details", {}),
                        result=e.get("result", "success"),
                        ip_address=e.get("ip_address", "")
                    )
                    for e in data.get("logs", [])
                ]
                logger.info(f"加载审计日志: {len(self._audit_log)} 条")
            except Exception as e:
                logger.error(f"加载审计日志失败: {e}")
    
    def _save_audit_log(self) -> None:
        audit_file = self.storage_path / "audit_log.json"
        try:
            data = {
                "logs": [e.to_dict() for e in self._audit_log[-10000:]],
                "updated_at": datetime.now().isoformat()
            }
            with open(audit_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"保存审计日志失败: {e}")
    
    def set_permission(
        self,
        knowledge_id: str,
        level: PermissionLevel,
        principal: str = "*",
        principal_type: str = "user",
        granted_by: str = "system",
        expires_at: str = ""
    ) -> AccessControlEntry:
        with self._lock:
            registration = self.hub.get_knowledge(knowledge_id)
            if not registration:
                raise KnowledgeNotFoundError(f"知识不存在: {knowledge_id}", knowledge_id)
            
            entry = AccessControlEntry(
                knowledge_id=knowledge_id,
                principal=principal,
                principal_type=principal_type,
                permissions={level},
                granted_at=datetime.now().isoformat(),
                granted_by=granted_by,
                expires_at=expires_at
            )
            
            self._acl[knowledge_id] = [e for e in self._acl[knowledge_id] 
                                       if e.principal != principal]
            self._acl[knowledge_id].append(entry)
            
            registration.permission_level = level
            self.hub._save_registration(registration)
            
            self._save_acl()
            
            self._log_audit(
                knowledge_id=knowledge_id,
                action=AuditAction.PERMISSION_CHANGE,
                actor=granted_by,
                details={
                    "level": level.value,
                    "principal": principal
                }
            )
            
            logger.info(f"设置权限: {knowledge_id} -> {level.value} (主体: {principal})")
            return entry
    
    def check_permission(
        self,
        knowledge_id: str,
        principal: str,
        required_level: PermissionLevel,
        principal_type: str = "user"
    ) -> bool:
        with self._lock:
            registration = self.hub.get_knowledge(knowledge_id)
            if not registration:
                return False
            
            if registration.permission_level == PermissionLevel.PUBLIC:
                return True
            
            if required_level == PermissionLevel.PUBLIC:
                return True
            
            entries = self._acl.get(knowledge_id, [])
            
            for entry in entries:
                if entry.is_expired():
                    continue
                
                if entry.principal == principal or entry.principal == "*":
                    if entry.has_permission(required_level):
                        return True
                
                if entry.principal_type == "role":
                    role_perms = self._role_permissions.get(entry.principal, set())
                    if required_level in role_perms:
                        return True
            
            return False
    
    def grant_permission(
        self,
        knowledge_id: str,
        principal: str,
        level: PermissionLevel,
        granted_by: str = "system",
        expires_at: str = ""
    ) -> AccessControlEntry:
        return self.set_permission(
            knowledge_id=knowledge_id,
            level=level,
            principal=principal,
            granted_by=granted_by,
            expires_at=expires_at
        )
    
    def revoke_permission(
        self,
        knowledge_id: str,
        principal: str
    ) -> bool:
        with self._lock:
            entries = self._acl.get(knowledge_id, [])
            original_count = len(entries)
            
            self._acl[knowledge_id] = [
                e for e in entries if e.principal != principal
            ]
            
            if len(self._acl[knowledge_id]) < original_count:
                self._save_acl()
                
                self._log_audit(
                    knowledge_id=knowledge_id,
                    action=AuditAction.PERMISSION_CHANGE,
                    actor="system",
                    details={
                        "action": "revoke",
                        "principal": principal
                    }
                )
                
                logger.info(f"撤销权限: {knowledge_id} (主体: {principal})")
                return True
            
            return False
    
    def get_acl(
        self,
        knowledge_id: str
    ) -> List[AccessControlEntry]:
        with self._lock:
            entries = self._acl.get(knowledge_id, [])
            return [e for e in entries if not e.is_expired()]
    
    def get_accessible_knowledge(
        self,
        principal: str,
        level: PermissionLevel = PermissionLevel.READ_ONLY
    ) -> List[str]:
        with self._lock:
            accessible = []
            
            for kid, registration in self.hub._registrations.items():
                if not registration.is_active:
                    continue
                
                if self.check_permission(kid, principal, level):
                    accessible.append(kid)
            
            return accessible
    
    def _log_audit(
        self,
        knowledge_id: str,
        action: AuditAction,
        actor: str,
        actor_project: str = "",
        details: Optional[Dict[str, Any]] = None,
        result: str = "success"
    ) -> AuditLogEntry:
        entry = AuditLogEntry(
            log_id=f"AUDIT-{datetime.now().strftime('%Y%m%d%H%M%S')}-{hashlib.md5(knowledge_id.encode()).hexdigest()[:6]}",
            knowledge_id=knowledge_id,
            action=action,
            actor=actor,
            actor_project=actor_project,
            timestamp=datetime.now().isoformat(),
            details=details or {},
            result=result
        )
        
        self._audit_log.append(entry)
        self._save_audit_log()
        
        return entry
    
    def log_access(
        self,
        knowledge_id: str,
        action: AuditAction,
        actor: str,
        actor_project: str = "",
        details: Optional[Dict[str, Any]] = None,
        result: str = "success"
    ) -> None:
        self._log_audit(
            knowledge_id=knowledge_id,
            action=action,
            actor=actor,
            actor_project=actor_project,
            details=details,
            result=result
        )
    
    def get_audit_log(
        self,
        knowledge_id: Optional[str] = None,
        actor: Optional[str] = None,
        action: Optional[AuditAction] = None,
        limit: int = 100
    ) -> List[AuditLogEntry]:
        with self._lock:
            logs = self._audit_log
            
            if knowledge_id:
                logs = [l for l in logs if l.knowledge_id == knowledge_id]
            
            if actor:
                logs = [l for l in logs if l.actor == actor]
            
            if action:
                logs = [l for l in logs if l.action == action]
            
            return logs[-limit:]
    
    def get_audit_statistics(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> Dict[str, Any]:
        with self._lock:
            logs = self._audit_log
            
            if start_date:
                logs = [l for l in logs if l.timestamp >= start_date]
            if end_date:
                logs = [l for l in logs if l.timestamp <= end_date]
            
            action_counts: Dict[str, int] = defaultdict(int)
            actor_counts: Dict[str, int] = defaultdict(int)
            result_counts: Dict[str, int] = defaultdict(int)
            
            for log in logs:
                action_counts[log.action.value] += 1
                actor_counts[log.actor] += 1
                result_counts[log.result] += 1
            
            return {
                "total_entries": len(logs),
                "by_action": dict(action_counts),
                "by_actor": dict(actor_counts),
                "by_result": dict(result_counts),
                "top_actors": sorted(actor_counts.items(), key=lambda x: x[1], reverse=True)[:10]
            }
    
    def define_role(
        self,
        role_name: str,
        permissions: Set[PermissionLevel]
    ) -> None:
        with self._lock:
            self._role_permissions[role_name] = permissions
            logger.info(f"定义角色: {role_name} -> {[p.value for p in permissions]}")
    
    def get_role_permissions(
        self,
        role_name: str
    ) -> Set[PermissionLevel]:
        return self._role_permissions.get(role_name, set())
    
    def check_access_with_audit(
        self,
        knowledge_id: str,
        principal: str,
        required_level: PermissionLevel,
        actor_project: str = ""
    ) -> Tuple[bool, str]:
        has_permission = self.check_permission(
            knowledge_id, principal, required_level
        )
        
        if has_permission:
            self.log_access(
                knowledge_id=knowledge_id,
                action=AuditAction.READ,
                actor=principal,
                actor_project=actor_project,
                result="success"
            )
            return True, "访问已授权"
        else:
            self.log_access(
                knowledge_id=knowledge_id,
                action=AuditAction.ACCESS_DENIED,
                actor=principal,
                actor_project=actor_project,
                details={"required_level": required_level.value},
                result="denied"
            )
            return False, "访问被拒绝"
    
    def cleanup_expired_entries(self) -> int:
        with self._lock:
            cleaned = 0
            
            for kid in list(self._acl.keys()):
                original_count = len(self._acl[kid])
                self._acl[kid] = [e for e in self._acl[kid] if not e.is_expired()]
                cleaned += original_count - len(self._acl[kid])
            
            if cleaned > 0:
                self._save_acl()
                logger.info(f"清理过期权限条目: {cleaned} 条")
            
            return cleaned
    
    def export_acl(self, output_path: str) -> None:
        with self._lock:
            data = {
                "acl": {
                    kid: [e.to_dict() for e in entries]
                    for kid, entries in self._acl.items()
                },
                "roles": {
                    role: [p.value for p in perms]
                    for role, perms in self._role_permissions.items()
                },
                "exported_at": datetime.now().isoformat()
            }
            
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"导出访问控制列表: {output_path}")
    
    def import_acl(
        self,
        input_path: str,
        merge: bool = True
    ) -> Dict[str, Any]:
        data = safe_read_json(Path(input_path))
        
        stats = {"imported": 0, "skipped": 0}
        
        with self._lock:
            if not merge:
                self._acl.clear()
            
            for kid, entries_data in data.get("acl", {}).items():
                for e_data in entries_data:
                    entry = AccessControlEntry(
                        knowledge_id=e_data["knowledge_id"],
                        principal=e_data["principal"],
                        principal_type=e_data["principal_type"],
                        permissions={
                            PermissionLevel(p) for p in e_data.get("permissions", [])
                        },
                        granted_at=e_data["granted_at"],
                        granted_by=e_data["granted_by"],
                        expires_at=e_data.get("expires_at", ""),
                        conditions=e_data.get("conditions", {})
                    )
                    
                    existing = [
                        ex for ex in self._acl[kid] 
                        if ex.principal == entry.principal
                    ]
                    
                    if existing:
                        stats["skipped"] += 1
                    else:
                        self._acl[kid].append(entry)
                        stats["imported"] += 1
            
            for role, perms in data.get("roles", {}).items():
                self._role_permissions[role] = {PermissionLevel(p) for p in perms}
            
            self._save_acl()
        
        logger.info(f"导入访问控制列表: 导入 {stats['imported']}, 跳过 {stats['skipped']}")
        return stats


class CrossProjectKnowledgeSharing:
    """跨项目知识共享统一接口
    
    整合了知识中心、索引器、同步器和访问控制的功能。
    
    功能：
    - 项目注册和管理
    - 知识共享和同步
    - 权限控制
    - 知识检索
    """
    
    def __init__(
        self,
        storage_path: Optional[Path] = None,
        auto_initialize: bool = True
    ):
        self.storage_path = storage_path or Path("./cross_project_knowledge")
        self._hub: Optional[CentralizedKnowledgeHub] = None
        self._indexer: Optional[KnowledgeIndexer] = None
        self._synchronizer: Optional[KnowledgeSynchronizer] = None
        self._access_control: Optional[KnowledgeAccessControl] = None
        self._projects: Dict[str, Any] = {}
        
        if auto_initialize:
            self.initialize()
    
    def initialize(self) -> None:
        """初始化跨项目知识共享系统"""
        self._hub = CentralizedKnowledgeHub(
            storage_path=self.storage_path,
            auto_initialize=True
        )
        self._indexer = KnowledgeIndexer(self._hub)
        self._synchronizer = KnowledgeSynchronizer(self._hub)
        self._access_control = KnowledgeAccessControl(self._hub)
        
        self._indexer.build_all_indexes()
        logger.info("跨项目知识共享系统初始化完成")
    
    def register_project(
        self,
        project_id: str,
        project_name: str,
        project_path: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Any:
        """注册项目
        
        Args:
            project_id: 项目ID
            project_name: 项目名称
            project_path: 项目路径
            metadata: 项目元数据
            
        Returns:
            项目注册信息
        """
        from dataclasses import dataclass
        
        @dataclass
        class ProjectInfo:
            project_id: str
            project_name: str
            project_path: str
            metadata: Dict[str, Any]
            registered_at: str
        
        project_info = ProjectInfo(
            project_id=project_id,
            project_name=project_name,
            project_path=project_path,
            metadata=metadata or {},
            registered_at=datetime.now().isoformat()
        )
        
        self._projects[project_id] = project_info
        logger.info(f"注册项目: {project_id} - {project_name}")
        return project_info
    
    def unregister_project(self, project_id: str) -> bool:
        """注销项目
        
        Args:
            project_id: 项目ID
            
        Returns:
            是否成功注销
        """
        if project_id in self._projects:
            del self._projects[project_id]
            logger.info(f"注销项目: {project_id}")
            return True
        return False
    
    def get_knowledge_base(self, project_id: str) -> Optional[Any]:
        """获取项目的知识库
        
        Args:
            project_id: 项目ID
            
        Returns:
            知识库对象
        """
        if project_id not in self._projects:
            return None
        
        return self._hub
    
    def share_knowledge(
        self,
        knowledge_id: str,
        source_project_id: str,
        target_project_ids: List[str],
        permission: Optional[Any] = None
    ) -> bool:
        """共享知识到目标项目
        
        Args:
            knowledge_id: 知识ID
            source_project_id: 源项目ID
            target_project_ids: 目标项目ID列表
            permission: 权限级别
            
        Returns:
            是否成功共享
        """
        if source_project_id not in self._projects:
            logger.warning(f"源项目不存在: {source_project_id}")
            return False
        
        for target_id in target_project_ids:
            if target_id not in self._projects:
                logger.warning(f"目标项目不存在: {target_id}")
                continue
            
            try:
                self._synchronizer.sync_incremental(
                    source_project=source_project_id,
                    target_project=target_id,
                    knowledge_ids=[knowledge_id]
                )
            except Exception as e:
                logger.error(f"共享知识失败: {knowledge_id} -> {target_id}: {e}")
                return False
        
        logger.info(f"共享知识: {knowledge_id} 从 {source_project_id} 到 {target_project_ids}")
        return True
    
    def get_accessible_knowledge(
        self,
        project_id: str,
        limit: int = 100
    ) -> List[Any]:
        """获取项目可访问的知识
        
        Args:
            project_id: 项目ID
            limit: 返回数量限制
            
        Returns:
            可访问的知识列表
        """
        if project_id not in self._projects:
            return []
        
        registrations = self._hub.list_knowledge(
            project_id=project_id,
            limit=limit
        )
        
        return registrations
    
    def check_permission(
        self,
        knowledge_id: str,
        project_id: str
    ) -> bool:
        """检查项目对知识的访问权限
        
        Args:
            knowledge_id: 知识ID
            project_id: 项目ID
            
        Returns:
            是否有权限
        """
        registration = self._hub.get_knowledge(knowledge_id)
        if not registration:
            return False
        
        if registration.project_id == project_id:
            return True
        
        return self._access_control.check_permission(
            knowledge_id=knowledge_id,
            principal=project_id,
            required_level=PermissionLevel.READ_ONLY
        )
    
    def sync_knowledge(
        self,
        source_project_id: str,
        target_project_id: str,
        knowledge_ids: Optional[List[str]] = None
    ) -> Any:
        """同步知识
        
        Args:
            source_project_id: 源项目ID
            target_project_id: 目标项目ID
            knowledge_ids: 知识ID列表
            
        Returns:
            同步记录
        """
        return self._synchronizer.sync_incremental(
            source_project=source_project_id,
            target_project=target_project_id,
            knowledge_ids=knowledge_ids
        )


def create_knowledge_sharing_system(
    storage_path: Optional[Path] = None,
    auto_initialize: bool = True
) -> Tuple[CentralizedKnowledgeHub, KnowledgeIndexer, KnowledgeSynchronizer, KnowledgeAccessControl]:
    """
    创建跨项目知识共享系统的工厂函数
    
    Args:
        storage_path: 存储路径
        auto_initialize: 是否自动初始化
        
    Returns:
        (Hub, Indexer, Synchronizer, AccessControl) 元组
    """
    hub = CentralizedKnowledgeHub(
        storage_path=storage_path,
        auto_initialize=auto_initialize
    )
    
    indexer = KnowledgeIndexer(hub)
    synchronizer = KnowledgeSynchronizer(hub)
    access_control = KnowledgeAccessControl(hub)
    
    if auto_initialize:
        indexer.build_all_indexes()
    
    return hub, indexer, synchronizer, access_control


def main():
    import argparse
    
    parser = argparse.ArgumentParser(
        description="跨项目知识共享系统 - Sanliu 技能",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        '--storage-path',
        type=Path,
        default=Path('./knowledge_sharing'),
        help='存储路径'
    )
    
    subparsers = parser.add_subparsers(dest='command', help='可用命令')
    
    stats_parser = subparsers.add_parser('stats', help='显示统计信息')
    
    search_parser = subparsers.add_parser('search', help='搜索知识')
    search_parser.add_argument('query', help='搜索关键词')
    search_parser.add_argument('--mode', choices=['fulltext', 'semantic', 'hybrid'], 
                              default='hybrid', help='搜索模式')
    search_parser.add_argument('--limit', type=int, default=10, help='结果数量限制')
    
    sync_parser = subparsers.add_parser('sync', help='同步知识')
    sync_parser.add_argument('--source', required=True, help='源项目ID')
    sync_parser.add_argument('--target', required=True, help='目标项目ID')
    sync_parser.add_argument('--ids', nargs='*', help='知识ID列表')
    
    acl_parser = subparsers.add_parser('acl', help='权限管理')
    acl_parser.add_argument('--knowledge-id', required=True, help='知识ID')
    acl_parser.add_argument('--principal', required=True, help='主体')
    acl_parser.add_argument('--level', choices=['public', 'private', 'shared', 'read_only', 'admin'],
                           required=True, help='权限级别')
    
    args = parser.parse_args()
    
    hub, indexer, synchronizer, acl = create_knowledge_sharing_system(
        storage_path=args.storage_path
    )
    
    if args.command == 'stats':
        hub_stats = hub.get_statistics()
        index_stats = indexer.get_index_statistics()
        sync_stats = synchronizer.get_sync_statistics()
        
        print("\n=== 知识中心统计 ===")
        print(f"总知识数: {hub_stats['total_knowledge']}")
        print(f"活跃知识: {hub_stats['active_knowledge']}")
        print(f"按分类: {hub_stats['by_category']}")
        print(f"按项目: {hub_stats['by_project']}")
        
        print("\n=== 索引统计 ===")
        print(f"全文索引词数: {index_stats['fulltext_words']}")
        print(f"语义索引数: {index_stats['semantic_indexed']}")
        
        print("\n=== 同步统计 ===")
        print(f"总同步次数: {sync_stats['total_syncs']}")
        print(f"按状态: {sync_stats['by_status']}")
    
    elif args.command == 'search':
        results = indexer.advanced_search(
            query=args.query,
            mode=args.mode
        )
        
        print(f"\n搜索结果 ({len(results)} 条):")
        for reg, score in results[:args.limit]:
            print(f"\n[{reg.knowledge_id}] {reg.metadata.title}")
            print(f"  分类: {reg.metadata.category.value}")
            print(f"  项目: {reg.project_id}")
            print(f"  匹配度: {score:.3f}")
    
    elif args.command == 'sync':
        record = synchronizer.sync_incremental(
            source_project=args.source,
            target_project=args.target,
            knowledge_ids=args.ids
        )
        
        print(f"\n同步结果:")
        print(f"  同步ID: {record.sync_id}")
        print(f"  状态: {record.status.value}")
        print(f"  知识数: {len(record.knowledge_ids)}")
        if record.error_message:
            print(f"  错误: {record.error_message}")
    
    elif args.command == 'acl':
        level = PermissionLevel(args.level)
        entry = acl.set_permission(
            knowledge_id=args.knowledge_id,
            level=level,
            principal=args.principal
        )
        
        print(f"\n权限设置成功:")
        print(f"  知识ID: {entry.knowledge_id}")
        print(f"  主体: {entry.principal}")
        print(f"  权限: {level.value}")
        print(f"  授权时间: {entry.granted_at}")
    
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
