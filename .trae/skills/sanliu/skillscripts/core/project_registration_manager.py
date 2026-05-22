#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
项目注册管理器 - Sanliu 技能

功能：
- 项目注册接口：注册、注销、列出项目
- 项目配置管理：配置验证、更新、持久化
- 项目状态追踪：状态更新、历史记录、状态查询
- 项目隔离机制：资源隔离、权限隔离、数据隔离

使用方法：
    from project_registration_manager import (
        ProjectRegistrationManager,
        ProjectConfig,
        ProjectStatusTracker,
        ProjectIsolationManager,
        ProjectStatus
    )
    
    # 创建项目注册管理器
    manager = ProjectRegistrationManager()
    
    # 注册项目
    config = ProjectConfig(
        name="my_project",
        root_path="/path/to/project",
        project_type="web"
    )
    manager.register_project(config)
    
    # 列出所有项目
    projects = manager.list_projects()
    
    # 注销项目
    manager.unregister_project("my_project")
"""

import json
import logging
import os
import shutil
import threading
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Callable, Union
from copy import deepcopy

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - [%(name)s] %(message)s'
)
logger = logging.getLogger(__name__)


class ProjectStatus(Enum):
    """
    项目状态枚举
    
    ACTIVE: 活跃状态 - 项目正在使用
    INACTIVE: 非活跃状态 - 项目已暂停
    ARCHIVED: 归档状态 - 项目已归档
    ERROR: 错误状态 - 项目存在错误
    PENDING: 待处理状态 - 项目等待初始化
    """
    ACTIVE = "active"
    INACTIVE = "inactive"
    ARCHIVED = "archived"
    ERROR = "error"
    PENDING = "pending"
    
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
            "active": cls.ACTIVE,
            "inactive": cls.INACTIVE,
            "archived": cls.ARCHIVED,
            "error": cls.ERROR,
            "pending": cls.PENDING
        }
        return status_map.get(value.lower())
    
    def get_description(self) -> str:
        """获取状态的中文描述"""
        descriptions = {
            ProjectStatus.ACTIVE: "活跃 - 项目正在使用中",
            ProjectStatus.INACTIVE: "非活跃 - 项目已暂停",
            ProjectStatus.ARCHIVED: "归档 - 项目已归档",
            ProjectStatus.ERROR: "错误 - 项目存在错误",
            ProjectStatus.PENDING: "待处理 - 项目等待初始化"
        }
        return descriptions.get(self, "未知状态")


class ProjectType(Enum):
    """
    项目类型枚举
    
    WEB: Web 项目
    API: API 服务项目
    CLI: 命令行工具项目
    LIBRARY: 库项目
    DESKTOP: 桌面应用项目
    MOBILE: 移动应用项目
    OTHER: 其他类型项目
    """
    WEB = "web"
    API = "api"
    CLI = "cli"
    LIBRARY = "library"
    DESKTOP = "desktop"
    MOBILE = "mobile"
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
            ProjectType.OTHER: "其他类型项目"
        }
        return descriptions.get(self, "未知类型")


class ProjectRegistrationError(Exception):
    """项目注册基础异常类"""
    
    def __init__(self, message: str, project_name: Optional[str] = None):
        super().__init__(message)
        self.project_name = project_name
    
    def __str__(self) -> str:
        base_msg = super().__str__()
        if self.project_name:
            return f"{base_msg} (项目: {self.project_name})"
        return base_msg


class ProjectValidationError(ProjectRegistrationError):
    """项目验证异常"""
    pass


class ProjectConfigError(ProjectRegistrationError):
    """项目配置异常"""
    pass


class ProjectIsolationError(ProjectRegistrationError):
    """项目隔离异常"""
    pass


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
    version: str = "1.0.0"
    author: str = ""
    tags: List[str] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)
    settings: Dict[str, Any] = field(default_factory=dict)
    environment: Dict[str, str] = field(default_factory=dict)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """初始化后处理"""
        if isinstance(self.project_type, str):
            self.project_type = ProjectType.from_string(self.project_type) or ProjectType.OTHER
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.updated_at is None:
            self.updated_at = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        data = asdict(self)
        data['project_type'] = self.project_type.value if isinstance(self.project_type, ProjectType) else self.project_type
        data['created_at'] = self.created_at.isoformat() if self.created_at else None
        data['updated_at'] = self.updated_at.isoformat() if self.updated_at else None
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ProjectConfig':
        """从字典创建实例"""
        if 'created_at' in data and isinstance(data['created_at'], str):
            data['created_at'] = datetime.fromisoformat(data['created_at'])
        if 'updated_at' in data and isinstance(data['updated_at'], str):
            data['updated_at'] = datetime.fromisoformat(data['updated_at'])
        return cls(**data)
    
    def validate(self) -> bool:
        """
        验证配置有效性
        
        Returns:
            配置是否有效
        """
        if not self.name or not self.name.strip():
            raise ProjectValidationError("项目名称不能为空", self.name)
        
        if not self.root_path or not self.root_path.strip():
            raise ProjectValidationError("项目根路径不能为空", self.name)
        
        if not Path(self.root_path).exists():
            raise ProjectValidationError(f"项目根路径不存在: {self.root_path}", self.name)
        
        if not isinstance(self.project_type, (ProjectType, str)):
            raise ProjectValidationError("项目类型必须是 ProjectType 枚举或字符串", self.name)
        
        return True
    
    def update(self, **kwargs) -> 'ProjectConfig':
        """
        更新配置
        
        Args:
            **kwargs: 要更新的配置项
            
        Returns:
            更新后的配置实例
        """
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
        self.updated_at = datetime.now()
        return self
    
    def clone(self) -> 'ProjectConfig':
        """创建配置的深拷贝"""
        return deepcopy(self)


@dataclass
class ProjectStatusRecord:
    """
    项目状态记录数据类
    
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
    def from_dict(cls, data: Dict[str, Any]) -> 'ProjectStatusRecord':
        """从字典创建实例"""
        data['old_status'] = ProjectStatus.from_string(data['old_status']) or ProjectStatus.PENDING
        data['new_status'] = ProjectStatus.from_string(data['new_status']) or ProjectStatus.PENDING
        data['timestamp'] = datetime.fromisoformat(data['timestamp'])
        return cls(**data)


class ProjectStatusTracker:
    """
    项目状态追踪器
    
    功能：
    - 状态更新
    - 状态历史记录
    - 状态查询
    """
    
    def __init__(self, history_file: Optional[str] = None):
        """
        初始化状态追踪器
        
        Args:
            history_file: 历史记录文件路径
        """
        self._status_map: Dict[str, ProjectStatus] = {}
        self._history: List[ProjectStatusRecord] = []
        self._history_file = history_file
        self._lock = threading.RLock()
        
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
                self._history = [ProjectStatusRecord.from_dict(r) for r in data.get('records', [])]
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
    
    def update_status(
        self,
        project_name: str,
        new_status: ProjectStatus,
        reason: str = "",
        operator: str = "",
        metadata: Optional[Dict[str, Any]] = None
    ) -> ProjectStatusRecord:
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
            
            record = ProjectStatusRecord(
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
            self._save_history()
            
            logger.info(f"项目 {project_name} 状态已更新: {old_status.value} -> {new_status.value}")
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
        limit: int = 100
    ) -> List[ProjectStatusRecord]:
        """
        获取状态变更历史
        
        Args:
            project_name: 项目名称（可选，不指定则返回所有）
            limit: 返回记录数量限制
            
        Returns:
            状态变更历史记录列表
        """
        with self._lock:
            if project_name:
                records = [r for r in self._history if r.project_name == project_name]
            else:
                records = self._history.copy()
            
            return records[-limit:]
    
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


class ProjectIsolationManager:
    """
    项目隔离管理器
    
    功能：
    - 资源隔离
    - 权限隔离
    - 数据隔离
    """
    
    def __init__(self, base_isolation_dir: Optional[str] = None):
        """
        初始化隔离管理器
        
        Args:
            base_isolation_dir: 隔离基础目录
        """
        self._base_dir = base_isolation_dir or os.path.join(tempfile.gettempdir(), "project_isolation")
        self._isolated_projects: Set[str] = set()
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
        resource_limits: Optional[Dict[str, Any]] = None,
        permissions: Optional[Set[str]] = None
    ) -> Dict[str, str]:
        """
        设置项目隔离环境
        
        Args:
            project_name: 项目名称
            resource_limits: 资源限制配置
            permissions: 权限集合
            
        Returns:
            隔离环境配置信息
        """
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
            
            self._isolated_projects.add(project_name)
            self._resource_limits[project_name] = resource_limits or {}
            self._permission_map[project_name] = permissions or set()
            self._data_isolation_paths[project_name] = {k: str(v) for k, v in sub_dirs.items()}
            
            logger.info(f"已为项目 {project_name} 设置隔离环境: {isolation_dir}")
            
            return {
                "isolation_dir": str(isolation_dir),
                "sub_directories": {k: str(v) for k, v in sub_dirs.items()},
                "resource_limits": self._resource_limits[project_name],
                "permissions": list(self._permission_map[project_name])
            }
    
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
            
            self._isolated_projects.discard(project_name)
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
            return list(self._isolated_projects)
    
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
                "isolation_dir": str(self._get_project_isolation_dir(project_name)),
                "sub_directories": self._data_isolation_paths.get(project_name, {}),
                "resource_limits": self._resource_limits.get(project_name, {}),
                "permissions": list(self._permission_map.get(project_name, set()))
            }


class ProjectRegistrationManager:
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
    
    DEFAULT_CONFIG_FILE = "project_registry.json"
    
    def __init__(
        self,
        config_file: Optional[str] = None,
        enable_isolation: bool = True,
        enable_status_tracking: bool = True
    ):
        """
        初始化项目注册管理器
        
        Args:
            config_file: 配置文件路径
            enable_isolation: 是否启用隔离机制
            enable_status_tracking: 是否启用状态追踪
        """
        self._config_file = config_file
        self._projects: Dict[str, ProjectConfig] = {}
        self._lock = threading.RLock()
        
        self._status_tracker: Optional[ProjectStatusTracker] = None
        self._isolation_manager: Optional[ProjectIsolationManager] = None
        
        if enable_status_tracking:
            status_file = None
            if config_file:
                status_file = str(Path(config_file).parent / "project_status_history.json")
            self._status_tracker = ProjectStatusTracker(status_file)
        
        if enable_isolation:
            isolation_dir = None
            if config_file:
                isolation_dir = str(Path(config_file).parent / "project_isolation")
            self._isolation_manager = ProjectIsolationManager(isolation_dir)
        
        self._path_config_manager = None
        self._load_config()
    
    def _load_config(self) -> None:
        """从文件加载配置"""
        if not self._config_file:
            return
        
        path = Path(self._config_file)
        if not path.exists():
            return
        
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                for name, config_data in data.get('projects', {}).items():
                    self._projects[name] = ProjectConfig.from_dict(config_data)
            logger.info(f"已加载 {len(self._projects)} 个项目配置")
        except Exception as e:
            logger.error(f"加载项目配置失败: {e}")
    
    def _save_config(self) -> None:
        """保存配置到文件"""
        if not self._config_file:
            return
        
        try:
            path = Path(self._config_file)
            path.parent.mkdir(parents=True, exist_ok=True)
            
            data = {
                'projects': {name: config.to_dict() for name, config in self._projects.items()},
                'updated_at': datetime.now().isoformat(),
                'version': '1.0.0'
            }
            
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"保存项目配置失败: {e}")
    
    def set_path_config_manager(self, manager: Any) -> None:
        """
        设置路径配置管理器
        
        Args:
            manager: PathConfigManager 实例
        """
        self._path_config_manager = manager
        logger.info("已设置路径配置管理器")
    
    def register_project(
        self,
        config: ProjectConfig,
        setup_isolation: bool = True,
        initial_status: ProjectStatus = ProjectStatus.ACTIVE
    ) -> bool:
        """
        注册项目
        
        Args:
            config: 项目配置
            setup_isolation: 是否设置隔离环境
            initial_status: 初始状态
            
        Returns:
            是否成功注册
        """
        with self._lock:
            try:
                config.validate()
                
                if config.name in self._projects:
                    raise ProjectRegistrationError(f"项目已存在: {config.name}", config.name)
                
                self._projects[config.name] = config
                self._save_config()
                
                if self._status_tracker:
                    self._status_tracker.update_status(
                        config.name,
                        initial_status,
                        reason="项目注册",
                        operator="system"
                    )
                
                if setup_isolation and self._isolation_manager:
                    self._isolation_manager.setup_isolation(config.name)
                
                logger.info(f"项目 {config.name} 注册成功")
                return True
                
            except ProjectValidationError as e:
                logger.error(f"项目配置验证失败: {e}")
                raise
            except Exception as e:
                logger.error(f"项目注册失败: {e}")
                raise ProjectRegistrationError(f"项目注册失败: {e}", config.name)
    
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
                logger.warning(f"项目不存在: {project_name}")
                return False
            
            if self._isolation_manager:
                self._isolation_manager.teardown_isolation(project_name, cleanup_isolation)
            
            if self._status_tracker:
                self._status_tracker.remove_project(project_name)
            
            del self._projects[project_name]
            self._save_config()
            
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
    
    def update_project_config(
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
                return None
            
            config.update(**kwargs)
            self._save_config()
            
            logger.info(f"项目 {project_name} 配置已更新")
            return config
    
    def get_status_tracker(self) -> Optional[ProjectStatusTracker]:
        """获取状态追踪器"""
        return self._status_tracker
    
    def get_isolation_manager(self) -> Optional[ProjectIsolationManager]:
        """获取隔离管理器"""
        return self._isolation_manager
    
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
    ) -> Optional[ProjectStatusRecord]:
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
            return None
        
        return self._status_tracker.update_status(
            project_name,
            status,
            reason=reason,
            operator=operator
        )
    
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
            
            self._projects.clear()
            self._save_config()
            
            logger.info(f"已清除 {count} 个项目")
            return count
    
    def export_config(self, output_path: str) -> bool:
        """
        导出配置到指定文件
        
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
            
            logger.info(f"配置已导出到: {output_path}")
            return True
        except Exception as e:
            logger.error(f"导出配置失败: {e}")
            return False
    
    def import_config(self, input_path: str, merge: bool = True) -> int:
        """
        从文件导入配置
        
        Args:
            input_path: 输入文件路径
            merge: 是否合并现有配置
            
        Returns:
            导入的项目数量
        """
        try:
            path = Path(input_path)
            if not path.exists():
                raise FileNotFoundError(f"配置文件不存在: {input_path}")
            
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
                
                self._save_config()
            
            logger.info(f"已导入 {imported_count} 个项目配置")
            return imported_count
        except Exception as e:
            logger.error(f"导入配置失败: {e}")
            raise


def create_project_registration_manager(
    config_dir: Optional[str] = None,
    enable_isolation: bool = True,
    enable_status_tracking: bool = True
) -> ProjectRegistrationManager:
    """
    创建项目注册管理器的工厂函数
    
    Args:
        config_dir: 配置目录
        enable_isolation: 是否启用隔离机制
        enable_status_tracking: 是否启用状态追踪
        
    Returns:
        ProjectRegistrationManager 实例
    """
    config_file = None
    if config_dir:
        config_file = str(Path(config_dir) / ProjectRegistrationManager.DEFAULT_CONFIG_FILE)
    
    return ProjectRegistrationManager(
        config_file=config_file,
        enable_isolation=enable_isolation,
        enable_status_tracking=enable_status_tracking
    )
