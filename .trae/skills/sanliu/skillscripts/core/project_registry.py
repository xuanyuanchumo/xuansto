#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
项目注册管理器 - Sanliu 技能

功能：
- 项目注册接口：注册、注销、列出项目
- 项目配置管理：配置存储、加载、验证、继承
- 项目状态追踪：状态更新、查询、历史记录、变更通知
- 项目隔离机制：资源隔离、权限隔离、隔离验证

使用方法：
    from project_registry import (
        ProjectRegistry,
        ProjectConfigManager,
        ProjectStatusTracker,
        ProjectIsolationManager,
        ProjectStatus,
        ProjectType
    )
    
    # 创建项目注册管理器
    registry = ProjectRegistry()
    
    # 注册项目
    registry.register_project(
        name="my_project",
        root_path="/path/to/project",
        project_type="web"
    )
    
    # 获取项目配置
    config = registry.get_project_config("my_project")
    
    # 注销项目
    registry.unregister_project("my_project")
"""

import hashlib
import json
import logging
import os
import shutil
import tempfile
import threading
from abc import ABC, abstractmethod
from copy import deepcopy
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum, auto
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set, Tuple, Type, Union

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - [%(name)s] %(message)s'
)
logger = logging.getLogger(__name__)


class ProjectStatus(Enum):
    """
    项目状态枚举
    
    PENDING: 待处理状态 - 项目等待初始化
    INITIALIZING: 初始化中 - 项目正在初始化
    ACTIVE: 活跃状态 - 项目正在使用
    INACTIVE: 非活跃状态 - 项目已暂停
    ARCHIVED: 归档状态 - 项目已归档
    ERROR: 错误状态 - 项目存在错误
    DEPRECATED: 已废弃状态 - 项目已废弃
    """
    PENDING = "pending"
    INITIALIZING = "initializing"
    ACTIVE = "active"
    INACTIVE = "inactive"
    ARCHIVED = "archived"
    ERROR = "error"
    DEPRECATED = "deprecated"
    
    @classmethod
    def from_string(cls, value: str) -> Optional['ProjectStatus']:
        """
        从字符串创建状态枚举
        
        Args:
            value: 状态字符串
            
        Returns:
            对应的 ProjectStatus 枚举值
        """
        status_map = {
            "pending": cls.PENDING,
            "initializing": cls.INITIALIZING,
            "active": cls.ACTIVE,
            "inactive": cls.INACTIVE,
            "archived": cls.ARCHIVED,
            "error": cls.ERROR,
            "deprecated": cls.DEPRECATED
        }
        return status_map.get(value.lower())
    
    def get_description(self) -> str:
        """获取状态的中文描述"""
        descriptions = {
            ProjectStatus.PENDING: "待处理 - 项目等待初始化",
            ProjectStatus.INITIALIZING: "初始化中 - 项目正在初始化",
            ProjectStatus.ACTIVE: "活跃 - 项目正在使用中",
            ProjectStatus.INACTIVE: "非活跃 - 项目已暂停",
            ProjectStatus.ARCHIVED: "归档 - 项目已归档",
            ProjectStatus.ERROR: "错误 - 项目存在错误",
            ProjectStatus.DEPRECATED: "已废弃 - 项目已废弃"
        }
        return descriptions.get(self, "未知状态")
    
    def is_operational(self) -> bool:
        """判断状态是否可操作"""
        return self in (ProjectStatus.ACTIVE, ProjectStatus.INACTIVE)


class ProjectType(Enum):
    """
    项目类型枚举
    
    WEB: Web 项目
    API: API 服务项目
    CLI: 命令行工具项目
    LIBRARY: 库项目
    DESKTOP: 桌面应用项目
    MOBILE: 移动应用项目
    DATA_SCIENCE: 数据科学项目
    INFRASTRUCTURE: 基础设施项目
    OTHER: 其他类型项目
    """
    WEB = "web"
    API = "api"
    CLI = "cli"
    LIBRARY = "library"
    DESKTOP = "desktop"
    MOBILE = "mobile"
    DATA_SCIENCE = "data_science"
    INFRASTRUCTURE = "infrastructure"
    OTHER = "other"
    
    @classmethod
    def from_string(cls, value: str) -> Optional['ProjectType']:
        """
        从字符串创建类型枚举
        
        Args:
            value: 类型字符串
            
        Returns:
            对应的 ProjectType 枚举值
        """
        type_map = {
            "web": cls.WEB,
            "api": cls.API,
            "cli": cls.CLI,
            "library": cls.LIBRARY,
            "desktop": cls.DESKTOP,
            "mobile": cls.MOBILE,
            "data_science": cls.DATA_SCIENCE,
            "infrastructure": cls.INFRASTRUCTURE,
            "other": cls.OTHER
        }
        return type_map.get(value.lower())
    
    def get_description(self) -> str:
        """获取类型的中文描述"""
        descriptions = {
            ProjectType.WEB: "Web 项目",
            ProjectType.API: "API 服务项目",
            ProjectType.CLI: "命令行工具项目",
            ProjectType.LIBRARY: "库项目",
            ProjectType.DESKTOP: "桌面应用项目",
            ProjectType.MOBILE: "移动应用项目",
            ProjectType.DATA_SCIENCE: "数据科学项目",
            ProjectType.INFRASTRUCTURE: "基础设施项目",
            ProjectType.OTHER: "其他类型项目"
        }
        return descriptions.get(self, "未知类型")


class ConfigInheritanceMode(Enum):
    """配置继承模式枚举"""
    NONE = auto()
    MERGE = auto()
    OVERRIDE = auto()
    EXTEND = auto()


class IsolationLevel(Enum):
    """隔离级别枚举"""
    NONE = "none"
    BASIC = "basic"
    STANDARD = "standard"
    STRICT = "strict"
    MAXIMUM = "maximum"


class ProjectRegistryError(Exception):
    """项目注册基础异常类"""
    
    def __init__(self, message: str, project_name: Optional[str] = None):
        super().__init__(message)
        self.project_name = project_name
    
    def __str__(self) -> str:
        base_msg = super().__str__()
        if self.project_name:
            return f"{base_msg} (项目: {self.project_name})"
        return base_msg


class ProjectValidationError(ProjectRegistryError):
    """项目验证异常"""
    pass


class ProjectConfigError(ProjectRegistryError):
    """项目配置异常"""
    pass


class ProjectIsolationError(ProjectRegistryError):
    """项目隔离异常"""
    pass


class ProjectNotFoundError(ProjectRegistryError):
    """项目未找到异常"""
    pass


class ProjectAlreadyExistsError(ProjectRegistryError):
    """项目已存在异常"""
    pass


@dataclass
class ProjectMetadata:
    """
    项目元数据数据类
    
    存储项目的附加信息
    """
    created_by: str = ""
    created_at: Optional[datetime] = None
    updated_by: str = ""
    updated_at: Optional[datetime] = None
    version: str = "1.0.0"
    tags: List[str] = field(default_factory=list)
    labels: Dict[str, str] = field(default_factory=dict)
    custom: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.updated_at is None:
            self.updated_at = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "created_by": self.created_by,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_by": self.updated_by,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "version": self.version,
            "tags": self.tags,
            "labels": self.labels,
            "custom": self.custom
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ProjectMetadata':
        """从字典创建实例"""
        if isinstance(data.get('created_at'), str):
            data['created_at'] = datetime.fromisoformat(data['created_at'])
        if isinstance(data.get('updated_at'), str):
            data['updated_at'] = datetime.fromisoformat(data['updated_at'])
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})
    
    def update(self, updated_by: str = "") -> None:
        """更新元数据时间戳"""
        self.updated_at = datetime.now()
        if updated_by:
            self.updated_by = updated_by


@dataclass
class ProjectConfig:
    """
    项目配置数据类
    
    存储项目的基本配置信息
    """
    name: str
    root_path: str
    project_type: Union[ProjectType, str] = ProjectType.OTHER
    description: str = ""
    author: str = ""
    dependencies: List[str] = field(default_factory=list)
    settings: Dict[str, Any] = field(default_factory=dict)
    environment: Dict[str, str] = field(default_factory=dict)
    metadata: ProjectMetadata = field(default_factory=ProjectMetadata)
    parent_config: Optional[str] = None
    inheritance_mode: ConfigInheritanceMode = ConfigInheritanceMode.NONE
    
    def __post_init__(self):
        if isinstance(self.project_type, str):
            self.project_type = ProjectType.from_string(self.project_type) or ProjectType.OTHER
        if isinstance(self.metadata, dict):
            self.metadata = ProjectMetadata.from_dict(self.metadata)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "name": self.name,
            "root_path": self.root_path,
            "project_type": self.project_type.value if isinstance(self.project_type, ProjectType) else self.project_type,
            "description": self.description,
            "author": self.author,
            "dependencies": self.dependencies,
            "settings": self.settings,
            "environment": self.environment,
            "metadata": self.metadata.to_dict(),
            "parent_config": self.parent_config,
            "inheritance_mode": self.inheritance_mode.name
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ProjectConfig':
        """从字典创建实例"""
        if isinstance(data.get('project_type'), str):
            data['project_type'] = ProjectType.from_string(data['project_type']) or ProjectType.OTHER
        if isinstance(data.get('metadata'), dict):
            data['metadata'] = ProjectMetadata.from_dict(data['metadata'])
        if isinstance(data.get('inheritance_mode'), str):
            try:
                data['inheritance_mode'] = ConfigInheritanceMode[data['inheritance_mode']]
            except KeyError:
                data['inheritance_mode'] = ConfigInheritanceMode.NONE
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})
    
    def validate(self) -> Tuple[bool, List[str]]:
        """
        验证配置有效性
        
        Returns:
            (是否有效, 错误消息列表)
        """
        errors = []
        
        if not self.name or not self.name.strip():
            errors.append("项目名称不能为空")
        elif not self._is_valid_name(self.name):
            errors.append(f"项目名称格式无效: {self.name}")
        
        if not self.root_path or not self.root_path.strip():
            errors.append("项目根路径不能为空")
        elif not Path(self.root_path).exists():
            errors.append(f"项目根路径不存在: {self.root_path}")
        
        if not isinstance(self.project_type, (ProjectType, str)):
            errors.append("项目类型必须是 ProjectType 枚举或字符串")
        
        return len(errors) == 0, errors
    
    def _is_valid_name(self, name: str) -> bool:
        """验证项目名称格式"""
        if not name:
            return False
        if name[0].isdigit():
            return False
        allowed_chars = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-")
        return all(c in allowed_chars for c in name)
    
    def update(self, **kwargs) -> 'ProjectConfig':
        """
        更新配置
        
        Args:
            **kwargs: 要更新的配置项
            
        Returns:
            更新后的配置实例
        """
        for key, value in kwargs.items():
            if hasattr(self, key) and key != 'name':
                setattr(self, key, value)
        self.metadata.update()
        return self
    
    def clone(self) -> 'ProjectConfig':
        """创建配置的深拷贝"""
        return deepcopy(self)
    
    def merge_with_parent(self, parent_config: 'ProjectConfig') -> 'ProjectConfig':
        """
        与父配置合并
        
        Args:
            parent_config: 父配置
            
        Returns:
            合并后的配置
        """
        if self.inheritance_mode == ConfigInheritanceMode.NONE:
            return self
        
        merged = self.clone()
        
        if self.inheritance_mode == ConfigInheritanceMode.MERGE:
            merged.settings = {**parent_config.settings, **self.settings}
            merged.environment = {**parent_config.environment, **self.environment}
            merged.dependencies = list(set(parent_config.dependencies + self.dependencies))
        
        elif self.inheritance_mode == ConfigInheritanceMode.EXTEND:
            for key, value in parent_config.settings.items():
                if key not in merged.settings:
                    merged.settings[key] = value
            for key, value in parent_config.environment.items():
                if key not in merged.environment:
                    merged.environment[key] = value
            for dep in parent_config.dependencies:
                if dep not in merged.dependencies:
                    merged.dependencies.append(dep)
        
        return merged


@dataclass
class StatusChangeRecord:
    """
    状态变更记录数据类
    
    存储项目状态变更的历史记录
    """
    project_name: str
    old_status: ProjectStatus
    new_status: ProjectStatus
    timestamp: datetime
    reason: str = ""
    operator: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "project_name": self.project_name,
            "old_status": self.old_status.value,
            "new_status": self.new_status.value,
            "timestamp": self.timestamp.isoformat(),
            "reason": self.reason,
            "operator": self.operator,
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'StatusChangeRecord':
        """从字典创建实例"""
        data['old_status'] = ProjectStatus.from_string(data['old_status']) or ProjectStatus.PENDING
        data['new_status'] = ProjectStatus.from_string(data['new_status']) or ProjectStatus.PENDING
        data['timestamp'] = datetime.fromisoformat(data['timestamp'])
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


class IStatusNotifier(ABC):
    """状态变更通知器接口"""
    
    @abstractmethod
    def notify(self, record: StatusChangeRecord) -> None:
        """发送状态变更通知"""
        pass


class LoggingStatusNotifier(IStatusNotifier):
    """日志状态变更通知器"""
    
    def notify(self, record: StatusChangeRecord) -> None:
        """发送状态变更通知到日志"""
        logger.info(
            f"项目状态变更: {record.project_name} "
            f"{record.old_status.value} -> {record.new_status.value} "
            f"(原因: {record.reason}, 操作者: {record.operator})"
        )


class CallbackStatusNotifier(IStatusNotifier):
    """回调状态变更通知器"""
    
    def __init__(self, callback: Callable[[StatusChangeRecord], None]):
        self._callback = callback
    
    def notify(self, record: StatusChangeRecord) -> None:
        """通过回调发送状态变更通知"""
        try:
            self._callback(record)
        except Exception as e:
            logger.error(f"状态变更回调执行失败: {e}")


class ProjectStatusTracker:
    """
    项目状态追踪器
    
    功能：
    - 状态更新
    - 状态历史记录
    - 状态查询
    - 状态变更通知
    """
    
    DEFAULT_HISTORY_FILE = "project_status_history.json"
    
    def __init__(
        self,
        history_file: Optional[str] = None,
        max_history: int = 1000
    ):
        """
        初始化状态追踪器
        
        Args:
            history_file: 历史记录文件路径
            max_history: 最大历史记录数
        """
        self._status_map: Dict[str, ProjectStatus] = {}
        self._history: List[StatusChangeRecord] = []
        self._history_file = history_file
        self._max_history = max_history
        self._lock = threading.RLock()
        self._notifiers: List[IStatusNotifier] = [LoggingStatusNotifier()]
        
        if history_file:
            self._load_history()
    
    def _load_history(self) -> None:
        """从文件加载历史记录"""
        if not self._history_file:
            return
        
        path = Path(self._history_file)
        if not path.exists():
            return
        
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self._history = [StatusChangeRecord.from_dict(r) for r in data.get('records', [])]
                self._status_map = {
                    k: ProjectStatus.from_string(v) or ProjectStatus.PENDING
                    for k, v in data.get('status_map', {}).items()
                }
            logger.info(f"已加载 {len(self._history)} 条状态历史记录")
        except Exception as e:
            logger.error(f"加载状态历史记录失败: {e}")
    
    def _save_history(self) -> None:
        """保存历史记录到文件"""
        if not self._history_file:
            return
        
        try:
            path = Path(self._history_file)
            path.parent.mkdir(parents=True, exist_ok=True)
            
            data = {
                'records': [r.to_dict() for r in self._history],
                'status_map': {k: v.value for k, v in self._status_map.items()},
                'updated_at': datetime.now().isoformat()
            }
            
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"保存状态历史记录失败: {e}")
    
    def add_notifier(self, notifier: IStatusNotifier) -> None:
        """添加状态变更通知器"""
        self._notifiers.append(notifier)
    
    def remove_notifier(self, notifier: IStatusNotifier) -> None:
        """移除状态变更通知器"""
        if notifier in self._notifiers:
            self._notifiers.remove(notifier)
    
    def _notify_all(self, record: StatusChangeRecord) -> None:
        """通知所有监听器"""
        for notifier in self._notifiers:
            try:
                notifier.notify(record)
            except Exception as e:
                logger.error(f"通知器执行失败: {e}")
    
    def update_status(
        self,
        project_name: str,
        new_status: ProjectStatus,
        reason: str = "",
        operator: str = "",
        metadata: Optional[Dict[str, Any]] = None
    ) -> StatusChangeRecord:
        """
        更新项目状态
        
        Args:
            project_name: 项目名称
            new_status: 新状态
            reason: 变更原因
            operator: 操作者
            metadata: 附加元数据
            
        Returns:
            状态变更记录
        """
        with self._lock:
            old_status = self._status_map.get(project_name, ProjectStatus.PENDING)
            
            record = StatusChangeRecord(
                project_name=project_name,
                old_status=old_status,
                new_status=new_status,
                timestamp=datetime.now(),
                reason=reason,
                operator=operator,
                metadata=metadata or {}
            )
            
            self._status_map[project_name] = new_status
            self._history.append(record)
            
            if len(self._history) > self._max_history:
                self._history = self._history[-self._max_history:]
            
            self._save_history()
            self._notify_all(record)
            
            return record
    
    def get_status(self, project_name: str) -> ProjectStatus:
        """
        获取项目当前状态
        
        Args:
            project_name: 项目名称
            
        Returns:
            项目当前状态
        """
        return self._status_map.get(project_name, ProjectStatus.PENDING)
    
    def get_history(
        self,
        project_name: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[StatusChangeRecord]:
        """
        获取状态变更历史
        
        Args:
            project_name: 项目名称（可选，不指定则返回所有）
            limit: 返回记录数量限制
            offset: 偏移量
            
        Returns:
            状态变更历史记录列表
        """
        with self._lock:
            if project_name:
                records = [r for r in self._history if r.project_name == project_name]
            else:
                records = self._history.copy()
            
            return records[offset:offset + limit]
    
    def get_projects_by_status(self, status: ProjectStatus) -> List[str]:
        """
        获取指定状态的所有项目
        
        Args:
            status: 项目状态
            
        Returns:
            项目名称列表
        """
        with self._lock:
            return [name for name, s in self._status_map.items() if s == status]
    
    def get_status_statistics(self) -> Dict[str, int]:
        """
        获取状态统计信息
        
        Returns:
            各状态的项目数量统计
        """
        with self._lock:
            stats = {status.value: 0 for status in ProjectStatus}
            for status in self._status_map.values():
                stats[status.value] += 1
            return stats
    
    def clear_history(self, project_name: Optional[str] = None) -> int:
        """
        清除状态历史记录
        
        Args:
            project_name: 项目名称（可选，不指定则清除所有）
            
        Returns:
            清除的记录数量
        """
        with self._lock:
            if project_name:
                original_count = len(self._history)
                self._history = [r for r in self._history if r.project_name != project_name]
                cleared = original_count - len(self._history)
            else:
                cleared = len(self._history)
                self._history.clear()
                self._status_map.clear()
            
            self._save_history()
            return cleared
    
    def remove_project(self, project_name: str) -> bool:
        """
        移除项目状态追踪
        
        Args:
            project_name: 项目名称
            
        Returns:
            是否成功移除
        """
        with self._lock:
            if project_name in self._status_map:
                del self._status_map[project_name]
                self._save_history()
                return True
            return False


class ProjectConfigManager:
    """
    项目配置管理器
    
    功能：
    - 配置存储和加载
    - 配置验证
    - 配置继承
    - 配置版本管理
    """
    
    DEFAULT_CONFIG_FILE = "project_configs.json"
    
    def __init__(
        self,
        config_file: Optional[str] = None,
        auto_save: bool = True
    ):
        """
        初始化配置管理器
        
        Args:
            config_file: 配置文件路径
            auto_save: 是否自动保存
        """
        self._config_file = config_file
        self._auto_save = auto_save
        self._configs: Dict[str, ProjectConfig] = {}
        self._config_versions: Dict[str, List[Dict[str, Any]]] = {}
        self._lock = threading.RLock()
        
        if config_file:
            self._load_configs()
    
    def _load_configs(self) -> None:
        """从文件加载配置"""
        if not self._config_file:
            return
        
        path = Path(self._config_file)
        if not path.exists():
            return
        
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                for name, config_data in data.get('configs', {}).items():
                    self._configs[name] = ProjectConfig.from_dict(config_data)
                self._config_versions = data.get('versions', {})
            logger.info(f"已加载 {len(self._configs)} 个项目配置")
        except Exception as e:
            logger.error(f"加载项目配置失败: {e}")
    
    def _save_configs(self) -> None:
        """保存配置到文件"""
        if not self._config_file or not self._auto_save:
            return
        
        try:
            path = Path(self._config_file)
            path.parent.mkdir(parents=True, exist_ok=True)
            
            data = {
                'configs': {name: config.to_dict() for name, config in self._configs.items()},
                'versions': self._config_versions,
                'updated_at': datetime.now().isoformat()
            }
            
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"保存项目配置失败: {e}")
    
    def _save_version(self, config: ProjectConfig) -> None:
        """保存配置版本"""
        if config.name not in self._config_versions:
            self._config_versions[config.name] = []
        
        version_data = {
            "config": config.to_dict(),
            "timestamp": datetime.now().isoformat(),
            "version": config.metadata.version
        }
        self._config_versions[config.name].append(version_data)
        
        if len(self._config_versions[config.name]) > 10:
            self._config_versions[config.name] = self._config_versions[config.name][-10:]
    
    def add_config(self, config: ProjectConfig) -> bool:
        """
        添加项目配置
        
        Args:
            config: 项目配置
            
        Returns:
            是否成功添加
        """
        valid, errors = config.validate()
        if not valid:
            raise ProjectConfigError(f"配置验证失败: {'; '.join(errors)}", config.name)
        
        with self._lock:
            if config.name in self._configs:
                raise ProjectAlreadyExistsError(f"配置已存在: {config.name}", config.name)
            
            self._configs[config.name] = config
            self._save_version(config)
            self._save_configs()
            return True
    
    def update_config(self, name: str, updates: Dict[str, Any]) -> Optional[ProjectConfig]:
        """
        更新项目配置
        
        Args:
            name: 项目名称
            updates: 更新内容
            
        Returns:
            更新后的配置
        """
        with self._lock:
            config = self._configs.get(name)
            if not config:
                return None
            
            config.update(**updates)
            valid, errors = config.validate()
            if not valid:
                raise ProjectConfigError(f"配置验证失败: {'; '.join(errors)}", name)
            
            self._save_version(config)
            self._save_configs()
            return config
    
    def get_config(self, name: str) -> Optional[ProjectConfig]:
        """
        获取项目配置
        
        Args:
            name: 项目名称
            
        Returns:
            项目配置
        """
        return self._configs.get(name)
    
    def get_resolved_config(self, name: str) -> Optional[ProjectConfig]:
        """
        获取解析后的配置（包含继承）
        
        Args:
            name: 项目名称
            
        Returns:
            解析后的项目配置
        """
        config = self._configs.get(name)
        if not config:
            return None
        
        if config.parent_config and config.inheritance_mode != ConfigInheritanceMode.NONE:
            parent = self.get_resolved_config(config.parent_config)
            if parent:
                return config.merge_with_parent(parent)
        
        return config
    
    def remove_config(self, name: str) -> bool:
        """
        移除项目配置
        
        Args:
            name: 项目名称
            
        Returns:
            是否成功移除
        """
        with self._lock:
            if name in self._configs:
                del self._configs[name]
                self._config_versions.pop(name, None)
                self._save_configs()
                return True
            return False
    
    def list_configs(self) -> List[ProjectConfig]:
        """列出所有配置"""
        return list(self._configs.values())
    
    def get_config_versions(self, name: str) -> List[Dict[str, Any]]:
        """
        获取配置版本历史
        
        Args:
            name: 项目名称
            
        Returns:
            版本历史列表
        """
        return self._config_versions.get(name, [])
    
    def validate_config(self, name: str) -> Tuple[bool, List[str]]:
        """
        验证配置
        
        Args:
            name: 项目名称
            
        Returns:
            (是否有效, 错误消息列表)
        """
        config = self._configs.get(name)
        if not config:
            return False, [f"配置不存在: {name}"]
        return config.validate()
    
    def export_configs(self, output_path: str) -> bool:
        """
        导出配置到文件
        
        Args:
            output_path: 输出文件路径
            
        Returns:
            是否成功导出
        """
        try:
            path = Path(output_path)
            path.parent.mkdir(parents=True, exist_ok=True)
            
            data = {
                'configs': {name: config.to_dict() for name, config in self._configs.items()},
                'exported_at': datetime.now().isoformat(),
                'version': '1.0.0'
            }
            
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"配置已导出到: {output_path}")
            return True
        except Exception as e:
            logger.error(f"导出配置失败: {e}")
            return False
    
    def import_configs(self, input_path: str, merge: bool = True) -> int:
        """
        从文件导入配置
        
        Args:
            input_path: 输入文件路径
            merge: 是否合并现有配置
            
        Returns:
            导入的配置数量
        """
        try:
            path = Path(input_path)
            if not path.exists():
                raise FileNotFoundError(f"配置文件不存在: {input_path}")
            
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            with self._lock:
                if not merge:
                    self._configs.clear()
                    self._config_versions.clear()
                
                imported_count = 0
                for name, config_data in data.get('configs', {}).items():
                    config = ProjectConfig.from_dict(config_data)
                    self._configs[name] = config
                    self._save_version(config)
                    imported_count += 1
                
                self._save_configs()
            
            logger.info(f"已导入 {imported_count} 个项目配置")
            return imported_count
        except Exception as e:
            logger.error(f"导入配置失败: {e}")
            raise


class ProjectIsolationManager:
    """
    项目隔离管理器
    
    功能：
    - 资源隔离
    - 权限隔离
    - 隔离验证
    """
    
    DEFAULT_ISOLATION_DIR = "project_isolation"
    
    def __init__(
        self,
        base_isolation_dir: Optional[str] = None,
        default_level: IsolationLevel = IsolationLevel.STANDARD
    ):
        """
        初始化隔离管理器
        
        Args:
            base_isolation_dir: 隔离基础目录
            default_level: 默认隔离级别
        """
        self._base_dir = base_isolation_dir or os.path.join(tempfile.gettempdir(), self.DEFAULT_ISOLATION_DIR)
        self._default_level = default_level
        self._isolated_projects: Dict[str, IsolationLevel] = {}
        self._resource_limits: Dict[str, Dict[str, Any]] = {}
        self._permission_map: Dict[str, Set[str]] = {}
        self._data_isolation_paths: Dict[str, Dict[str, str]] = {}
        self._lock = threading.RLock()
        
        self._ensure_base_dir()
    
    def _ensure_base_dir(self) -> None:
        """确保基础目录存在"""
        Path(self._base_dir).mkdir(parents=True, exist_ok=True)
    
    def _get_project_isolation_dir(self, project_name: str) -> Path:
        """获取项目隔离目录"""
        return Path(self._base_dir) / self._sanitize_name(project_name)
    
    def _sanitize_name(self, name: str) -> str:
        """清理名称，移除危险字符"""
        return "".join(c if c.isalnum() or c in "_-" else "_" for c in name)
    
    def setup_isolation(
        self,
        project_name: str,
        level: Optional[IsolationLevel] = None,
        resource_limits: Optional[Dict[str, Any]] = None,
        permissions: Optional[Set[str]] = None
    ) -> Dict[str, Any]:
        """
        设置项目隔离环境
        
        Args:
            project_name: 项目名称
            level: 隔离级别
            resource_limits: 资源限制配置
            permissions: 权限集合
            
        Returns:
            隔离环境配置信息
        """
        isolation_level = level or self._default_level
        
        with self._lock:
            isolation_dir = self._get_project_isolation_dir(project_name)
            isolation_dir.mkdir(parents=True, exist_ok=True)
            
            sub_dirs = {
                "data": isolation_dir / "data",
                "cache": isolation_dir / "cache",
                "temp": isolation_dir / "temp",
                "logs": isolation_dir / "logs",
                "config": isolation_dir / "config"
            }
            
            for dir_path in sub_dirs.values():
                dir_path.mkdir(exist_ok=True)
            
            self._isolated_projects[project_name] = isolation_level
            self._resource_limits[project_name] = resource_limits or self._get_default_resource_limits(isolation_level)
            self._permission_map[project_name] = permissions or self._get_default_permissions(isolation_level)
            self._data_isolation_paths[project_name] = {k: str(v) for k, v in sub_dirs.items()}
            
            logger.info(f"已为项目 {project_name} 设置隔离环境 (级别: {isolation_level.value})")
            
            return {
                "project_name": project_name,
                "isolation_level": isolation_level.value,
                "isolation_dir": str(isolation_dir),
                "sub_directories": {k: str(v) for k, v in sub_dirs.items()},
                "resource_limits": self._resource_limits[project_name],
                "permissions": list(self._permission_map[project_name])
            }
    
    def _get_default_resource_limits(self, level: IsolationLevel) -> Dict[str, Any]:
        """根据隔离级别获取默认资源限制"""
        limits = {
            IsolationLevel.NONE: {},
            IsolationLevel.BASIC: {
                "max_memory_mb": 1024,
                "max_cpu_percent": 80
            },
            IsolationLevel.STANDARD: {
                "max_memory_mb": 512,
                "max_cpu_percent": 50,
                "max_disk_mb": 1024,
                "max_processes": 10
            },
            IsolationLevel.STRICT: {
                "max_memory_mb": 256,
                "max_cpu_percent": 30,
                "max_disk_mb": 512,
                "max_processes": 5,
                "network_enabled": False
            },
            IsolationLevel.MAXIMUM: {
                "max_memory_mb": 128,
                "max_cpu_percent": 20,
                "max_disk_mb": 256,
                "max_processes": 2,
                "network_enabled": False,
                "filesystem_readonly": True
            }
        }
        return limits.get(level, {})
    
    def _get_default_permissions(self, level: IsolationLevel) -> Set[str]:
        """根据隔离级别获取默认权限"""
        permissions = {
            IsolationLevel.NONE: {"read", "write", "execute", "network", "admin"},
            IsolationLevel.BASIC: {"read", "write", "execute", "network"},
            IsolationLevel.STANDARD: {"read", "write", "execute"},
            IsolationLevel.STRICT: {"read", "write"},
            IsolationLevel.MAXIMUM: {"read"}
        }
        return permissions.get(level, set())
    
    def teardown_isolation(self, project_name: str, cleanup: bool = True) -> bool:
        """
        移除项目隔离环境
        
        Args:
            project_name: 项目名称
            cleanup: 是否清理隔离目录
            
        Returns:
            是否成功移除
        """
        with self._lock:
            if project_name not in self._isolated_projects:
                return False
            
            if cleanup:
                isolation_dir = self._get_project_isolation_dir(project_name)
                if isolation_dir.exists():
                    try:
                        shutil.rmtree(isolation_dir)
                    except Exception as e:
                        logger.error(f"清理隔离目录失败: {e}")
            
            self._isolated_projects.pop(project_name, None)
            self._resource_limits.pop(project_name, None)
            self._permission_map.pop(project_name, None)
            self._data_isolation_paths.pop(project_name, None)
            
            logger.info(f"已移除项目 {project_name} 的隔离环境")
            return True
    
    def get_isolation_path(
        self,
        project_name: str,
        path_type: str = "data"
    ) -> Optional[str]:
        """
        获取项目隔离路径
        
        Args:
            project_name: 项目名称
            path_type: 路径类型 (data/cache/temp/logs/config)
            
        Returns:
            隔离路径
        """
        with self._lock:
            paths = self._data_isolation_paths.get(project_name, {})
            return paths.get(path_type)
    
    def check_permission(
        self,
        project_name: str,
        permission: str
    ) -> bool:
        """
        检查项目权限
        
        Args:
            project_name: 项目名称
            permission: 权限名称
            
        Returns:
            是否具有权限
        """
        with self._lock:
            permissions = self._permission_map.get(project_name, set())
            return permission in permissions
    
    def grant_permission(
        self,
        project_name: str,
        permission: str
    ) -> bool:
        """
        授予项目权限
        
        Args:
            project_name: 项目名称
            permission: 权限名称
            
        Returns:
            是否成功授予
        """
        with self._lock:
            if project_name not in self._isolated_projects:
                return False
            
            self._permission_map[project_name].add(permission)
            logger.info(f"已为项目 {project_name} 授予权限: {permission}")
            return True
    
    def revoke_permission(
        self,
        project_name: str,
        permission: str
    ) -> bool:
        """
        撤销项目权限
        
        Args:
            project_name: 项目名称
            permission: 权限名称
            
        Returns:
            是否成功撤销
        """
        with self._lock:
            if project_name not in self._isolated_projects:
                return False
            
            self._permission_map[project_name].discard(permission)
            logger.info(f"已撤销项目 {project_name} 的权限: {permission}")
            return True
    
    def set_resource_limit(
        self,
        project_name: str,
        resource_type: str,
        limit: Any
    ) -> bool:
        """
        设置资源限制
        
        Args:
            project_name: 项目名称
            resource_type: 资源类型
            limit: 限制值
            
        Returns:
            是否成功设置
        """
        with self._lock:
            if project_name not in self._isolated_projects:
                return False
            
            self._resource_limits[project_name][resource_type] = limit
            logger.info(f"已为项目 {project_name} 设置资源限制: {resource_type}={limit}")
            return True
    
    def get_resource_limit(
        self,
        project_name: str,
        resource_type: str
    ) -> Optional[Any]:
        """
        获取资源限制
        
        Args:
            project_name: 项目名称
            resource_type: 资源类型
            
        Returns:
            资源限制值
        """
        with self._lock:
            limits = self._resource_limits.get(project_name, {})
            return limits.get(resource_type)
    
    def validate_isolation(self, project_name: str) -> Tuple[bool, List[str]]:
        """
        验证项目隔离状态
        
        Args:
            project_name: 项目名称
            
        Returns:
            (是否有效, 错误消息列表)
        """
        errors = []
        
        with self._lock:
            if project_name not in self._isolated_projects:
                errors.append(f"项目 {project_name} 未设置隔离")
                return False, errors
            
            isolation_dir = self._get_project_isolation_dir(project_name)
            if not isolation_dir.exists():
                errors.append(f"隔离目录不存在: {isolation_dir}")
            
            paths = self._data_isolation_paths.get(project_name, {})
            for path_type, path in paths.items():
                if not Path(path).exists():
                    errors.append(f"{path_type} 目录不存在: {path}")
        
        return len(errors) == 0, errors
    
    def get_isolation_level(self, project_name: str) -> Optional[IsolationLevel]:
        """
        获取项目隔离级别
        
        Args:
            project_name: 项目名称
            
        Returns:
            隔离级别
        """
        return self._isolated_projects.get(project_name)
    
    def is_isolated(self, project_name: str) -> bool:
        """
        检查项目是否已隔离
        
        Args:
            project_name: 项目名称
            
        Returns:
            是否已隔离
        """
        return project_name in self._isolated_projects
    
    def list_isolated_projects(self) -> List[str]:
        """
        列出所有已隔离的项目
        
        Returns:
            项目名称列表
        """
        with self._lock:
            return list(self._isolated_projects.keys())
    
    def get_isolation_info(self, project_name: str) -> Optional[Dict[str, Any]]:
        """
        获取项目隔离信息
        
        Args:
            project_name: 项目名称
            
        Returns:
            隔离信息字典
        """
        with self._lock:
            if project_name not in self._isolated_projects:
                return None
            
            return {
                "project_name": project_name,
                "isolation_level": self._isolated_projects[project_name].value,
                "isolation_dir": str(self._get_project_isolation_dir(project_name)),
                "sub_directories": self._data_isolation_paths.get(project_name, {}),
                "resource_limits": self._resource_limits.get(project_name, {}),
                "permissions": list(self._permission_map.get(project_name, set()))
            }


class ProjectRegistry:
    """
    项目注册管理器
    
    功能：
    - 项目注册
    - 项目注销
    - 项目列表
    - 配置管理
    - 状态追踪
    - 隔离管理
    """
    
    DEFAULT_REGISTRY_FILE = "project_registry.json"
    
    def __init__(
        self,
        registry_file: Optional[str] = None,
        enable_isolation: bool = True,
        enable_status_tracking: bool = True,
        default_isolation_level: IsolationLevel = IsolationLevel.STANDARD
    ):
        """
        初始化项目注册管理器
        
        Args:
            registry_file: 注册表文件路径
            enable_isolation: 是否启用隔离机制
            enable_status_tracking: 是否启用状态追踪
            default_isolation_level: 默认隔离级别
        """
        self._registry_file = registry_file
        self._projects: Dict[str, ProjectConfig] = {}
        self._lock = threading.RLock()
        
        self._config_manager: Optional[ProjectConfigManager] = None
        self._status_tracker: Optional[ProjectStatusTracker] = None
        self._isolation_manager: Optional[ProjectIsolationManager] = None
        
        if registry_file:
            config_file = str(Path(registry_file).parent / ProjectConfigManager.DEFAULT_CONFIG_FILE)
            self._config_manager = ProjectConfigManager(config_file)
        
        if enable_status_tracking:
            status_file = None
            if registry_file:
                status_file = str(Path(registry_file).parent / ProjectStatusTracker.DEFAULT_HISTORY_FILE)
            self._status_tracker = ProjectStatusTracker(status_file)
        
        if enable_isolation:
            isolation_dir = None
            if registry_file:
                isolation_dir = str(Path(registry_file).parent / ProjectIsolationManager.DEFAULT_ISOLATION_DIR)
            self._isolation_manager = ProjectIsolationManager(isolation_dir, default_isolation_level)
        
        self._load_registry()
    
    def _load_registry(self) -> None:
        """从文件加载注册表"""
        if not self._registry_file:
            return
        
        path = Path(self._registry_file)
        if not path.exists():
            return
        
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                for name, config_data in data.get('projects', {}).items():
                    self._projects[name] = ProjectConfig.from_dict(config_data)
            logger.info(f"已加载 {len(self._projects)} 个项目")
        except Exception as e:
            logger.error(f"加载项目注册表失败: {e}")
    
    def _save_registry(self) -> None:
        """保存注册表到文件"""
        if not self._registry_file:
            return
        
        try:
            path = Path(self._registry_file)
            path.parent.mkdir(parents=True, exist_ok=True)
            
            data = {
                'projects': {name: config.to_dict() for name, config in self._projects.items()},
                'updated_at': datetime.now().isoformat(),
                'version': '1.0.0'
            }
            
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"保存项目注册表失败: {e}")
    
    def register_project(
        self,
        name: str,
        root_path: str,
        project_type: Union[ProjectType, str] = ProjectType.OTHER,
        description: str = "",
        author: str = "",
        setup_isolation: bool = True,
        initial_status: ProjectStatus = ProjectStatus.ACTIVE,
        **kwargs
    ) -> ProjectConfig:
        """
        注册项目
        
        Args:
            name: 项目名称
            root_path: 项目根路径
            project_type: 项目类型
            description: 项目描述
            author: 作者
            setup_isolation: 是否设置隔离环境
            initial_status: 初始状态
            **kwargs: 其他配置参数
            
        Returns:
            项目配置
        """
        with self._lock:
            if name in self._projects:
                raise ProjectAlreadyExistsError(f"项目已存在: {name}", name)
            
            config = ProjectConfig(
                name=name,
                root_path=root_path,
                project_type=project_type,
                description=description,
                author=author,
                **kwargs
            )
            
            valid, errors = config.validate()
            if not valid:
                raise ProjectValidationError(f"项目配置验证失败: {'; '.join(errors)}", name)
            
            self._projects[name] = config
            
            if self._config_manager:
                self._config_manager.add_config(config)
            
            if self._status_tracker:
                self._status_tracker.update_status(
                    name,
                    initial_status,
                    reason="项目注册",
                    operator="system"
                )
            
            if setup_isolation and self._isolation_manager:
                self._isolation_manager.setup_isolation(name)
            
            self._save_registry()
            
            logger.info(f"项目 {name} 注册成功")
            return config
    
    def unregister_project(
        self,
        project_name: str,
        cleanup_isolation: bool = True
    ) -> bool:
        """
        注销项目
        
        Args:
            project_name: 项目名称
            cleanup_isolation: 是否清理隔离环境
            
        Returns:
            是否成功注销
        """
        with self._lock:
            if project_name not in self._projects:
                raise ProjectNotFoundError(f"项目不存在: {project_name}", project_name)
            
            if self._isolation_manager:
                self._isolation_manager.teardown_isolation(project_name, cleanup_isolation)
            
            if self._status_tracker:
                self._status_tracker.remove_project(project_name)
            
            if self._config_manager:
                self._config_manager.remove_config(project_name)
            
            del self._projects[project_name]
            self._save_registry()
            
            logger.info(f"项目 {project_name} 已注销")
            return True
    
    def list_projects(
        self,
        status: Optional[ProjectStatus] = None,
        project_type: Optional[ProjectType] = None
    ) -> List[ProjectConfig]:
        """
        列出项目
        
        Args:
            status: 按状态筛选（可选）
            project_type: 按类型筛选（可选）
            
        Returns:
            项目配置列表
        """
        with self._lock:
            projects = list(self._projects.values())
            
            if status and self._status_tracker:
                status_names = self._status_tracker.get_projects_by_status(status)
                projects = [p for p in projects if p.name in status_names]
            
            if project_type:
                projects = [p for p in projects if p.project_type == project_type]
            
            return projects
    
    def get_project(self, project_name: str) -> Optional[ProjectConfig]:
        """
        获取项目配置
        
        Args:
            project_name: 项目名称
            
        Returns:
            项目配置
        """
        return self._projects.get(project_name)
    
    def update_project(
        self,
        project_name: str,
        **kwargs
    ) -> Optional[ProjectConfig]:
        """
        更新项目配置
        
        Args:
            project_name: 项目名称
            **kwargs: 要更新的配置项
            
        Returns:
            更新后的配置
        """
        with self._lock:
            config = self._projects.get(project_name)
            if not config:
                raise ProjectNotFoundError(f"项目不存在: {project_name}", project_name)
            
            config.update(**kwargs)
            valid, errors = config.validate()
            if not valid:
                raise ProjectValidationError(f"项目配置验证失败: {'; '.join(errors)}", project_name)
            
            if self._config_manager:
                self._config_manager.update_config(project_name, kwargs)
            
            self._save_registry()
            
            logger.info(f"项目 {project_name} 配置已更新")
            return config
    
    def project_exists(self, project_name: str) -> bool:
        """
        检查项目是否存在
        
        Args:
            project_name: 项目名称
            
        Returns:
            是否存在
        """
        return project_name in self._projects
    
    def get_project_count(self) -> int:
        """获取项目总数"""
        return len(self._projects)
    
    def get_project_status(self, project_name: str) -> ProjectStatus:
        """
        获取项目状态
        
        Args:
            project_name: 项目名称
            
        Returns:
            项目状态
        """
        if self._status_tracker:
            return self._status_tracker.get_status(project_name)
        return ProjectStatus.PENDING
    
    def set_project_status(
        self,
        project_name: str,
        status: ProjectStatus,
        reason: str = "",
        operator: str = ""
    ) -> Optional[StatusChangeRecord]:
        """
        设置项目状态
        
        Args:
            project_name: 项目名称
            status: 新状态
            reason: 变更原因
            operator: 操作者
            
        Returns:
            状态变更记录
        """
        if not self._status_tracker:
            return None
        
        if project_name not in self._projects:
            raise ProjectNotFoundError(f"项目不存在: {project_name}", project_name)
        
        return self._status_tracker.update_status(
            project_name,
            status,
            reason=reason,
            operator=operator
        )
    
    def get_status_tracker(self) -> Optional[ProjectStatusTracker]:
        """获取状态追踪器"""
        return self._status_tracker
    
    def get_isolation_manager(self) -> Optional[ProjectIsolationManager]:
        """获取隔离管理器"""
        return self._isolation_manager
    
    def get_config_manager(self) -> Optional[ProjectConfigManager]:
        """获取配置管理器"""
        return self._config_manager
    
    def clear_all_projects(self, cleanup_isolation: bool = True) -> int:
        """
        清除所有项目
        
        Args:
            cleanup_isolation: 是否清理隔离环境
            
        Returns:
            清除的项目数量
        """
        with self._lock:
            count = len(self._projects)
            
            if self._isolation_manager and cleanup_isolation:
                for project_name in list(self._projects.keys()):
                    self._isolation_manager.teardown_isolation(project_name, cleanup=True)
            
            if self._status_tracker:
                self._status_tracker.clear_history()
            
            if self._config_manager:
                for project_name in list(self._projects.keys()):
                    self._config_manager.remove_config(project_name)
            
            self._projects.clear()
            self._save_registry()
            
            logger.info(f"已清除 {count} 个项目")
            return count
    
    def export_registry(self, output_path: str) -> bool:
        """
        导出注册表到文件
        
        Args:
            output_path: 输出文件路径
            
        Returns:
            是否成功导出
        """
        try:
            path = Path(output_path)
            path.parent.mkdir(parents=True, exist_ok=True)
            
            data = {
                'projects': {name: config.to_dict() for name, config in self._projects.items()},
                'exported_at': datetime.now().isoformat(),
                'version': '1.0.0'
            }
            
            if self._status_tracker:
                data['status_history'] = [r.to_dict() for r in self._status_tracker.get_history(limit=1000)]
            
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"注册表已导出到: {output_path}")
            return True
        except Exception as e:
            logger.error(f"导出注册表失败: {e}")
            return False
    
    def import_registry(self, input_path: str, merge: bool = True) -> int:
        """
        从文件导入注册表
        
        Args:
            input_path: 输入文件路径
            merge: 是否合并现有注册表
            
        Returns:
            导入的项目数量
        """
        try:
            path = Path(input_path)
            if not path.exists():
                raise FileNotFoundError(f"注册表文件不存在: {input_path}")
            
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            with self._lock:
                if not merge:
                    self._projects.clear()
                
                imported_count = 0
                for name, config_data in data.get('projects', {}).items():
                    config = ProjectConfig.from_dict(config_data)
                    self._projects[name] = config
                    imported_count += 1
                
                self._save_registry()
            
            logger.info(f"已导入 {imported_count} 个项目")
            return imported_count
        except Exception as e:
            logger.error(f"导入注册表失败: {e}")
            raise
    
    def get_registry_info(self) -> Dict[str, Any]:
        """
        获取注册表信息
        
        Returns:
            注册表信息字典
        """
        with self._lock:
            info = {
                "project_count": len(self._projects),
                "registry_file": self._registry_file,
                "isolation_enabled": self._isolation_manager is not None,
                "status_tracking_enabled": self._status_tracker is not None,
                "config_management_enabled": self._config_manager is not None
            }
            
            if self._status_tracker:
                info["status_statistics"] = self._status_tracker.get_status_statistics()
            
            if self._isolation_manager:
                info["isolated_project_count"] = len(self._isolation_manager.list_isolated_projects())
            
            return info


def create_project_registry(
    config_dir: Optional[str] = None,
    enable_isolation: bool = True,
    enable_status_tracking: bool = True,
    default_isolation_level: IsolationLevel = IsolationLevel.STANDARD
) -> ProjectRegistry:
    """
    创建项目注册管理器的工厂函数
    
    Args:
        config_dir: 配置目录
        enable_isolation: 是否启用隔离机制
        enable_status_tracking: 是否启用状态追踪
        default_isolation_level: 默认隔离级别
        
    Returns:
        ProjectRegistry 实例
    """
    registry_file = None
    if config_dir:
        registry_file = str(Path(config_dir) / ProjectRegistry.DEFAULT_REGISTRY_FILE)
    
    return ProjectRegistry(
        registry_file=registry_file,
        enable_isolation=enable_isolation,
        enable_status_tracking=enable_status_tracking,
        default_isolation_level=default_isolation_level
    )


def main():
    import argparse
    
    parser = argparse.ArgumentParser(
        description="项目注册管理器 - Sanliu 技能",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        '--config-dir',
        type=str,
        help='配置目录'
    )
    parser.add_argument(
        '--info',
        action='store_true',
        help='显示注册表信息'
    )
    parser.add_argument(
        '--list',
        action='store_true',
        help='列出所有项目'
    )
    parser.add_argument(
        '--export',
        type=str,
        help='导出注册表到指定路径'
    )
    parser.add_argument(
        '--import',
        dest='import_path',
        type=str,
        help='从文件导入注册表'
    )
    
    args = parser.parse_args()
    
    registry = create_project_registry(config_dir=args.config_dir)
    
    if args.info:
        info = registry.get_registry_info()
        print(json.dumps(info, indent=2, ensure_ascii=False))
    
    if args.list:
        projects = registry.list_projects()
        for project in projects:
            status = registry.get_project_status(project.name)
            print(f"- {project.name} ({project.project_type.value}): {status.value}")
    
    if args.export:
        result = registry.export_registry(args.export)
        print(f"导出注册表: {'成功' if result else '失败'}")
    
    if args.import_path:
        count = registry.import_registry(args.import_path)
        print(f"已导入 {count} 个项目")
    
    if not any([args.info, args.list, args.export, args.import_path]):
        print("项目注册管理器")
        print(f"项目总数: {registry.get_project_count()}")
        info = registry.get_registry_info()
        if "status_statistics" in info:
            print("状态统计:")
            for status, count in info["status_statistics"].items():
                if count > 0:
                    print(f"  - {status}: {count}")


if __name__ == "__main__":
    main()
