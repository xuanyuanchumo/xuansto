#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
增强版路径配置管理器 - Sanliu 技能

功能增强：
- 技能根路径配置（SKILL_ROOT, SKILL_MD, VERSION_FILE, CONFIG_DIR）
- 子技能路径配置（SUBSKILLS_DIR, 动态获取子技能路径）
- 脚本路径配置（SCRIPTS_DIR及各子目录）
- 资源路径配置（RESOURCES_DIR, TEMPLATES_DIR, DATA_DIR, REPORTS_DIR）
- 动态路径解析（resolve_path, get_relative_path, validate_path, ensure_path）
- 环境变量支持（SANLIU_<PATH_KEY>格式）
- 单例模式
- 配置热重载
- 目录结构自动创建
- 路径验证功能
"""

import json
import logging
import os
import shutil
import sys
import threading
import hashlib
from contextlib import contextmanager
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple, Generator, Union

try:
    from .path_config_manager import (
        PathConfigManager, PathMode, PathConfig, PathConfigError,
        PathValidationError, ModeSwitchError, SkillDetector, ProjectDetector,
        PathValidator, logger
    )
except ImportError:
    from path_config_manager import (
        PathConfigManager, PathMode, PathConfig, PathConfigError,
        PathValidationError, ModeSwitchError, SkillDetector, ProjectDetector,
        PathValidator, logger
    )


class PathKey(Enum):
    """路径键枚举"""
    SKILL_ROOT = "skill_root"
    SKILL_MD = "skill_md"
    VERSION_FILE = "version_file"
    CONFIG_DIR = "config_dir"
    
    SUBSKILLS_DIR = "subskills_dir"
    
    SCRIPTS_DIR = "scripts_dir"
    CORE_SCRIPTS_DIR = "core_scripts_dir"
    PIPELINE_SCRIPTS_DIR = "pipeline_scripts_dir"
    TEST_SCRIPTS_DIR = "test_scripts_dir"
    ANALYSIS_SCRIPTS_DIR = "analysis_scripts_dir"
    OPTIMIZATION_SCRIPTS_DIR = "optimization_scripts_dir"
    REQUIREMENTS_SCRIPTS_DIR = "requirements_scripts_dir"
    UTILITY_SCRIPTS_DIR = "utility_scripts_dir"
    MONITORING_SCRIPTS_DIR = "monitoring_scripts_dir"
    
    RESOURCES_DIR = "resources_dir"
    TEMPLATES_DIR = "templates_dir"
    DATA_DIR = "data_dir"
    REPORTS_DIR = "reports_dir"
    
    DOCS_DIR = "docs_dir"
    DOCS_REPORTS_DIR = "docs_reports_dir"
    DOCS_API_DIR = "docs_api_dir"
    DOCS_WORKFLOW_DIR = "docs_workflow_dir"
    DOCS_KNOWLEDGE_DIR = "docs_knowledge_dir"
    TESTS_DIR = "tests_dir"
    BACKEND_DIR = "backend_dir"
    FRONTEND_DIR = "frontend_dir"
    LOGS_DIR = "logs_dir"
    CACHE_DIR = "cache_dir"
    TEMP_DIR = "temp_dir"


class DocsSubdir(Enum):
    """Docs子目录枚举"""
    REPORTS = "reports"
    API = "api"
    WORKFLOW = "workflow"
    KNOWLEDGE = "knowledge"
    LIBS = "libs"
    SNAPSHOTS = "snapshots"
    DIFF_REPORTS = "diff_reports"


class OutputType(Enum):
    """输出类型枚举"""
    REPORT = "report"
    LOG = "log"
    TEMP = "temp"
    CACHE = "cache"
    DATA = "data"
    BACKUP = "backup"
    EXPORT = "export"
    DOWNLOAD = "download"
    UPLOAD = "upload"
    SNAPSHOT = "snapshot"


class DirectoryCategory(Enum):
    """目录分类枚举"""
    CORE = "core"
    DOCS = "docs"
    TESTS = "tests"
    SCRIPTS = "scripts"
    REPORTS = "reports"
    DATA = "data"
    CONFIG = "config"
    LOGS = "logs"
    CACHE = "cache"
    TEMP = "temp"
    RESOURCES = "resources"
    SUBSKILLS = "subskills"


class DirectoryStatus(Enum):
    """目录状态枚举"""
    EXISTS = "exists"
    MISSING = "missing"
    EMPTY = "empty"
    INVALID = "invalid"
    PERMISSION_DENIED = "permission_denied"


@dataclass
class OutputPathRegistration:
    """输出路径注册信息"""
    script_name: str
    output_type: OutputType
    path: Path
    description: str
    registered_at: str
    exclusive: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "script_name": self.script_name,
            "output_type": self.output_type.value,
            "path": str(self.path),
            "description": self.description,
            "registered_at": self.registered_at,
            "exclusive": self.exclusive
        }


@dataclass
class OutputPathConflict:
    """输出路径冲突信息"""
    path: Path
    registrations: List[OutputPathRegistration]
    conflict_type: str
    severity: str
    message: str
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "path": str(self.path),
            "conflict_type": self.conflict_type,
            "severity": self.severity,
            "message": self.message,
            "conflicting_scripts": [r.to_dict() for r in self.registrations]
        }


@dataclass
class OutputPathValidationResult:
    """输出路径验证结果"""
    output_type: OutputType
    path: Path
    exists: bool
    writable: bool
    has_space: bool
    space_mb: Optional[float]
    error: Optional[str]
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "output_type": self.output_type.value,
            "path": str(self.path),
            "exists": self.exists,
            "writable": self.writable,
            "has_space": self.has_space,
            "space_mb": self.space_mb,
            "error": self.error
        }


@dataclass
class SkillPathConfig:
    """技能路径配置数据类"""
    skill_root: Path
    skill_md: Path
    version_file: Path
    config_dir: Path
    subskills_dir: Path
    scripts_dir: Path
    core_scripts_dir: Path
    pipeline_scripts_dir: Path
    test_scripts_dir: Path
    analysis_scripts_dir: Path
    optimization_scripts_dir: Path
    requirements_scripts_dir: Path
    utility_scripts_dir: Path
    monitoring_scripts_dir: Path
    resources_dir: Path
    templates_dir: Path
    data_dir: Path
    reports_dir: Path
    docs_dir: Path
    docs_reports_dir: Path
    docs_api_dir: Path
    docs_workflow_dir: Path
    docs_knowledge_dir: Path
    tests_dir: Path
    backend_dir: Path
    frontend_dir: Path
    logs_dir: Path
    cache_dir: Path
    temp_dir: Path
    
    def to_dict(self) -> Dict[str, str]:
        """转换为字典"""
        return {
            key: str(value) for key, value in asdict(self).items()
        }
    
    @classmethod
    def from_skill_root(cls, skill_root: Path) -> 'SkillPathConfig':
        """从技能根目录创建配置"""
        docs_dir = skill_root / "docs"
        return cls(
            skill_root=skill_root,
            skill_md=skill_root / "SKILL.md",
            version_file=skill_root / "version.json",
            config_dir=skill_root / "config",
            subskills_dir=skill_root / "subskills",
            scripts_dir=skill_root / "skillscripts",
            core_scripts_dir=skill_root / "skillscripts" / "core",
            pipeline_scripts_dir=skill_root / "skillscripts" / "pipeline",
            test_scripts_dir=skill_root / "skillscripts" / "test",
            analysis_scripts_dir=skill_root / "skillscripts" / "analysis",
            optimization_scripts_dir=skill_root / "skillscripts" / "optimization",
            requirements_scripts_dir=skill_root / "skillscripts" / "requirements",
            utility_scripts_dir=skill_root / "skillscripts" / "utils",
            monitoring_scripts_dir=skill_root / "skillscripts" / "monitoring",
            resources_dir=skill_root / "resources",
            templates_dir=skill_root / "resources" / "templates",
            data_dir=skill_root / "data",
            reports_dir=skill_root / "reports",
            docs_dir=docs_dir,
            docs_reports_dir=docs_dir / "reports",
            docs_api_dir=docs_dir / "api",
            docs_workflow_dir=docs_dir / "workflow",
            docs_knowledge_dir=docs_dir / "knowledge",
            tests_dir=skill_root / "tests",
            backend_dir=skill_root / "backend",
            frontend_dir=skill_root / "frontend",
            logs_dir=skill_root / "logs",
            cache_dir=skill_root / "cache",
            temp_dir=skill_root / "temp"
        )


@dataclass
class DirectoryTemplate:
    """目录模板数据类"""
    name: str
    description: str
    structure: Dict[str, Any]
    required: bool = True
    category: str = "core"
    files_to_create: List[str] = field(default_factory=list)
    gitkeep: bool = True


@dataclass
class DirectoryHealthReport:
    """目录健康报告数据类"""
    timestamp: str
    base_path: str
    mode: str
    total_directories: int
    existing_directories: int
    missing_directories: int
    invalid_directories: int
    health_score: float
    details: List[Dict[str, Any]]
    recommendations: List[str]


@dataclass
class DirectorySnapshot:
    """目录快照数据类"""
    snapshot_id: str
    timestamp: str
    base_path: str
    mode: str
    structure: Dict[str, Any]
    file_count: int
    total_size: int
    checksum: str


@dataclass
class SubskillInfo:
    """子技能信息数据类"""
    name: str
    path: Path
    exists: bool
    size: int
    last_modified: Optional[str]
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "name": self.name,
            "path": str(self.path),
            "exists": self.exists,
            "size": self.size,
            "last_modified": self.last_modified
        }


class DirectoryTemplates:
    """目录模板集合"""
    
    SKILL_TEMPLATES: Dict[str, DirectoryTemplate] = {
        "subskills": DirectoryTemplate(
            name="subskills",
            description="子技能目录",
            category=DirectoryCategory.SUBSKILLS.value,
            required=True,
            structure={},
            gitkeep=True
        ),
        "skillscripts": DirectoryTemplate(
            name="skillscripts",
            description="技能脚本目录",
            category=DirectoryCategory.SCRIPTS.value,
            required=True,
            structure={
                "core": {},
                "analysis": {},
                "pipeline": {},
                "test": {},
                "utils": {},
                "requirements": {},
                "optimization": {},
                "monitoring": {}
            },
            gitkeep=True
        ),
        "resources": DirectoryTemplate(
            name="resources",
            description="资源目录",
            category=DirectoryCategory.RESOURCES.value,
            required=True,
            structure={
                "templates": {
                    "evolution_reports": {}
                },
                "best_practices": {}
            },
            gitkeep=True
        ),
        "docs": DirectoryTemplate(
            name="docs",
            description="文档目录",
            category=DirectoryCategory.DOCS.value,
            required=True,
            structure={
                "libs": {},
                "reports": {},
                "workflow": {
                    "requirements": {},
                    "design": {},
                    "implementation": {},
                    "testing": {},
                    "deployment": {}
                },
                "snapshots": {},
                "diff_reports": {}
            },
            gitkeep=True
        ),
        "tests": DirectoryTemplate(
            name="tests",
            description="测试目录",
            category=DirectoryCategory.TESTS.value,
            required=True,
            structure={
                "unit": {},
                "integration": {},
                "e2e": {},
                "database": {},
                "security": {},
                "performance": {},
                "regression": {}
            },
            gitkeep=True
        ),
        "data": DirectoryTemplate(
            name="data",
            description="数据目录",
            category=DirectoryCategory.DATA.value,
            required=False,
            structure={
                "cache": {},
                "temp": {},
                "backups": {}
            },
            gitkeep=True
        ),
        "logs": DirectoryTemplate(
            name="logs",
            description="日志目录",
            category=DirectoryCategory.LOGS.value,
            required=False,
            structure={},
            gitkeep=True
        ),
        "backend": DirectoryTemplate(
            name="backend",
            description="后端目录",
            category=DirectoryCategory.CORE.value,
            required=False,
            structure={
                "app": {
                    "api": {},
                    "models": {},
                    "services": {}
                },
                "tests": {},
                "scripts": {}
            },
            gitkeep=False
        ),
        "frontend": DirectoryTemplate(
            name="frontend",
            description="前端目录",
            category=DirectoryCategory.CORE.value,
            required=False,
            structure={
                "src": {
                    "components": {},
                    "views": {},
                    "stores": {},
                    "api": {}
                },
                "tests": {},
                "scripts": {}
            },
            gitkeep=False
        )
    }


class EnhancedPathValidator:
    """增强版路径验证器"""
    
    @classmethod
    def validate_structure(
        cls,
        base_path: Path,
        template: DirectoryTemplate
    ) -> Tuple[bool, List[str]]:
        """
        验证目录结构是否符合模板
        
        Args:
            base_path: 基础路径
            template: 目录模板
            
        Returns:
            (是否有效, 错误列表) 元组
        """
        errors = []
        
        target_path = base_path / template.name
        
        if template.required and not target_path.exists():
            errors.append(f"必需目录不存在: {template.name}")
            return False, errors
        
        if target_path.exists():
            for sub_dir in template.structure.keys():
                sub_path = target_path / sub_dir
                if not sub_path.exists():
                    errors.append(f"子目录不存在: {template.name}/{sub_dir}")
        
        return len(errors) == 0, errors
    
    @classmethod
    def validate_permissions(
        cls,
        path: Path,
        require_write: bool = True
    ) -> Tuple[bool, Optional[str]]:
        """
        验证路径权限
        
        Args:
            path: 待验证路径
            require_write: 是否需要写权限
            
        Returns:
            (是否有效, 错误信息) 元组
        """
        if not path.exists():
            try:
                path.mkdir(parents=True, exist_ok=True)
            except PermissionError:
                return False, f"无权限创建目录: {path}"
            except Exception as e:
                return False, f"创建目录失败: {e}"
        
        if not path.is_dir():
            return False, f"路径不是目录: {path}"
        
        if require_write:
            try:
                test_file = path / ".permission_test"
                test_file.touch()
                test_file.unlink()
            except PermissionError:
                return False, f"无写入权限: {path}"
            except Exception as e:
                return False, f"权限验证失败: {e}"
        
        return True, None
    
    @classmethod
    def check_disk_space(
        cls,
        path: Path,
        min_space_mb: int = 100
    ) -> Tuple[bool, Optional[str]]:
        """
        检查磁盘空间
        
        Args:
            path: 待检查路径
            min_space_mb: 最小空间要求(MB)
            
        Returns:
            (是否充足, 错误信息) 元组
        """
        try:
            if not path.exists():
                path = path.parent
            
            while not path.exists() and path != path.parent:
                path = path.parent
            
            if hasattr(shutil, 'disk_usage'):
                usage = shutil.disk_usage(path)
                free_mb = usage.free / (1024 * 1024)
                
                if free_mb < min_space_mb:
                    return False, f"磁盘空间不足: 可用 {free_mb:.1f}MB, 需要 {min_space_mb}MB"
                
                return True, None
        except Exception as e:
            return False, f"磁盘空间检查失败: {e}"
        
        return True, None


class EnvironmentVariableManager:
    """环境变量管理器"""
    
    ENV_PREFIX = "SANLIU_"
    
    ENV_KEY_MAPPING = {
        PathKey.SKILL_ROOT: "SKILL_ROOT",
        PathKey.SKILL_MD: "SKILL_MD",
        PathKey.VERSION_FILE: "VERSION_FILE",
        PathKey.CONFIG_DIR: "CONFIG_DIR",
        PathKey.SUBSKILLS_DIR: "SUBSKILLS_DIR",
        PathKey.SCRIPTS_DIR: "SCRIPTS_DIR",
        PathKey.CORE_SCRIPTS_DIR: "CORE_SCRIPTS_DIR",
        PathKey.PIPELINE_SCRIPTS_DIR: "PIPELINE_SCRIPTS_DIR",
        PathKey.TEST_SCRIPTS_DIR: "TEST_SCRIPTS_DIR",
        PathKey.ANALYSIS_SCRIPTS_DIR: "ANALYSIS_SCRIPTS_DIR",
        PathKey.OPTIMIZATION_SCRIPTS_DIR: "OPTIMIZATION_SCRIPTS_DIR",
        PathKey.REQUIREMENTS_SCRIPTS_DIR: "REQUIREMENTS_SCRIPTS_DIR",
        PathKey.UTILITY_SCRIPTS_DIR: "UTILITY_SCRIPTS_DIR",
        PathKey.MONITORING_SCRIPTS_DIR: "MONITORING_SCRIPTS_DIR",
        PathKey.RESOURCES_DIR: "RESOURCES_DIR",
        PathKey.TEMPLATES_DIR: "TEMPLATES_DIR",
        PathKey.DATA_DIR: "DATA_DIR",
        PathKey.REPORTS_DIR: "REPORTS_DIR",
        PathKey.DOCS_DIR: "DOCS_DIR",
        PathKey.DOCS_REPORTS_DIR: "DOCS_REPORTS_DIR",
        PathKey.DOCS_API_DIR: "DOCS_API_DIR",
        PathKey.DOCS_WORKFLOW_DIR: "DOCS_WORKFLOW_DIR",
        PathKey.DOCS_KNOWLEDGE_DIR: "DOCS_KNOWLEDGE_DIR",
        PathKey.TESTS_DIR: "TESTS_DIR",
        PathKey.BACKEND_DIR: "BACKEND_DIR",
        PathKey.FRONTEND_DIR: "FRONTEND_DIR",
        PathKey.LOGS_DIR: "LOGS_DIR",
        PathKey.CACHE_DIR: "CACHE_DIR",
        PathKey.TEMP_DIR: "TEMP_DIR"
    }
    
    DOCS_ENV_KEY_MAPPING = {
        DocsSubdir.REPORTS: "DOCS_REPORTS_DIR",
        DocsSubdir.API: "DOCS_API_DIR",
        DocsSubdir.WORKFLOW: "DOCS_WORKFLOW_DIR",
        DocsSubdir.KNOWLEDGE: "DOCS_KNOWLEDGE_DIR",
        DocsSubdir.LIBS: "DOCS_LIBS_DIR",
        DocsSubdir.SNAPSHOTS: "DOCS_SNAPSHOTS_DIR",
        DocsSubdir.DIFF_REPORTS: "DOCS_DIFF_REPORTS_DIR"
    }
    
    @classmethod
    def get_env_override(cls, path_key: PathKey) -> Optional[Path]:
        """
        获取环境变量覆盖的路径
        
        Args:
            path_key: 路径键
            
        Returns:
            环境变量指定的路径，未设置则返回 None
        """
        env_key = cls.ENV_KEY_MAPPING.get(path_key)
        if not env_key:
            return None
        
        full_env_key = f"{cls.ENV_PREFIX}{env_key}"
        env_value = os.environ.get(full_env_key, "").strip()
        
        if env_value:
            return Path(env_value)
        
        return None
    
    @classmethod
    def get_all_env_overrides(cls) -> Dict[str, str]:
        """获取所有环境变量覆盖"""
        overrides = {}
        for path_key, env_key in cls.ENV_KEY_MAPPING.items():
            full_env_key = f"{cls.ENV_PREFIX}{env_key}"
            env_value = os.environ.get(full_env_key, "").strip()
            if env_value:
                overrides[path_key.value] = env_value
        
        return overrides
    
    @classmethod
    def set_env_override(cls, path_key: PathKey, path: Union[str, Path]) -> None:
        """
        设置环境变量覆盖
        
        Args:
            path_key: 路径键
            path: 路径值
        """
        env_key = cls.ENV_KEY_MAPPING.get(path_key)
        if env_key:
            full_env_key = f"{cls.ENV_PREFIX}{env_key}"
            os.environ[full_env_key] = str(path)
    
    @classmethod
    def clear_env_override(cls, path_key: PathKey) -> None:
        """
        清除环境变量覆盖
        
        Args:
            path_key: 路径键
        """
        env_key = cls.ENV_KEY_MAPPING.get(path_key)
        if env_key:
            full_env_key = f"{cls.ENV_PREFIX}{env_key}"
            os.environ.pop(full_env_key, None)
    
    @classmethod
    def get_output_path_env(cls, output_type: OutputType) -> Optional[Path]:
        """
        获取输出路径的环境变量覆盖
        
        Args:
            output_type: 输出类型
            
        Returns:
            环境变量指定的路径，未设置则返回 None
        """
        env_key = f"{cls.ENV_PREFIX}OUTPUT_{output_type.value.upper()}"
        env_value = os.environ.get(env_key, "").strip()
        
        if env_value:
            return Path(env_value)
        
        return None
    
    @classmethod
    def set_output_path_env(cls, output_type: OutputType, path: Union[str, Path]) -> None:
        """
        设置输出路径的环境变量覆盖
        
        Args:
            output_type: 输出类型
            path: 路径值
        """
        env_key = f"{cls.ENV_PREFIX}OUTPUT_{output_type.value.upper()}"
        os.environ[env_key] = str(path)
    
    @classmethod
    def clear_output_path_env(cls, output_type: OutputType) -> None:
        """
        清除输出路径的环境变量覆盖
        
        Args:
            output_type: 输出类型
        """
        env_key = f"{cls.ENV_PREFIX}OUTPUT_{output_type.value.upper()}"
        os.environ.pop(env_key, None)
    
    @classmethod
    def get_docs_subdir_env(cls, docs_subdir: DocsSubdir) -> Optional[Path]:
        """
        获取docs子目录的环境变量覆盖
        
        Args:
            docs_subdir: Docs子目录类型
            
        Returns:
            环境变量指定的路径，未设置则返回 None
        """
        env_key = cls.DOCS_ENV_KEY_MAPPING.get(docs_subdir)
        if not env_key:
            return None
        
        full_env_key = f"{cls.ENV_PREFIX}{env_key}"
        env_value = os.environ.get(full_env_key, "").strip()
        
        if env_value:
            return Path(env_value)
        
        return None
    
    @classmethod
    def set_docs_subdir_env(cls, docs_subdir: DocsSubdir, path: Union[str, Path]) -> None:
        """
        设置docs子目录的环境变量覆盖
        
        Args:
            docs_subdir: Docs子目录类型
            path: 路径值
        """
        env_key = cls.DOCS_ENV_KEY_MAPPING.get(docs_subdir)
        if env_key:
            full_env_key = f"{cls.ENV_PREFIX}{env_key}"
            os.environ[full_env_key] = str(path)
    
    @classmethod
    def clear_docs_subdir_env(cls, docs_subdir: DocsSubdir) -> None:
        """
        清除docs子目录的环境变量覆盖
        
        Args:
            docs_subdir: Docs子目录类型
        """
        env_key = cls.DOCS_ENV_KEY_MAPPING.get(docs_subdir)
        if env_key:
            full_env_key = f"{cls.ENV_PREFIX}{env_key}"
            os.environ.pop(full_env_key, None)
    
    @classmethod
    def get_all_docs_env_overrides(cls) -> Dict[str, str]:
        """获取所有docs相关的环境变量覆盖"""
        overrides = {}
        for docs_subdir, env_key in cls.DOCS_ENV_KEY_MAPPING.items():
            full_env_key = f"{cls.ENV_PREFIX}{env_key}"
            env_value = os.environ.get(full_env_key, "").strip()
            if env_value:
                overrides[docs_subdir.value] = env_value
        return overrides


class OutputPathRegistry:
    """输出路径注册器 - 用于检测路径冲突"""
    
    def __init__(self):
        self._registrations: Dict[str, OutputPathRegistration] = {}
        self._path_index: Dict[str, List[str]] = {}
        self._lock = threading.Lock()
    
    def register(
        self,
        script_name: str,
        output_type: OutputType,
        path: Path,
        description: str = "",
        exclusive: bool = False
    ) -> str:
        """
        注册输出路径
        
        Args:
            script_name: 脚本名称
            output_type: 输出类型
            path: 输出路径
            description: 描述信息
            exclusive: 是否独占使用
            
        Returns:
            注册ID
        """
        with self._lock:
            registration_id = f"{script_name}_{output_type.value}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
            
            registration = OutputPathRegistration(
                script_name=script_name,
                output_type=output_type,
                path=path,
                description=description,
                registered_at=datetime.now().isoformat(),
                exclusive=exclusive
            )
            
            self._registrations[registration_id] = registration
            
            path_str = str(path.resolve())
            if path_str not in self._path_index:
                self._path_index[path_str] = []
            self._path_index[path_str].append(registration_id)
            
            logger.debug(f"注册输出路径: {script_name} -> {path}")
            
            return registration_id
    
    def unregister(self, registration_id: str) -> bool:
        """
        取消注册
        
        Args:
            registration_id: 注册ID
            
        Returns:
            是否成功
        """
        with self._lock:
            if registration_id not in self._registrations:
                return False
            
            registration = self._registrations[registration_id]
            path_str = str(registration.path.resolve())
            
            if path_str in self._path_index:
                self._path_index[path_str].remove(registration_id)
                if not self._path_index[path_str]:
                    del self._path_index[path_str]
            
            del self._registrations[registration_id]
            
            return True
    
    def check_conflicts(self) -> List[OutputPathConflict]:
        """
        检测所有路径冲突
        
        Returns:
            冲突列表
        """
        conflicts = []
        
        with self._lock:
            for path_str, registration_ids in self._path_index.items():
                if len(registration_ids) > 1:
                    registrations = [
                        self._registrations[rid] 
                        for rid in registration_ids 
                        if rid in self._registrations
                    ]
                    
                    if not registrations:
                        continue
                    
                    has_exclusive = any(r.exclusive for r in registrations)
                    
                    if has_exclusive:
                        conflicts.append(OutputPathConflict(
                            path=Path(path_str),
                            registrations=registrations,
                            conflict_type="exclusive_violation",
                            severity="high",
                            message=f"路径 {path_str} 被标记为独占使用，但被多个脚本注册"
                        ))
                    else:
                        conflicts.append(OutputPathConflict(
                            path=Path(path_str),
                            registrations=registrations,
                            conflict_type="shared_path",
                            severity="medium",
                            message=f"路径 {path_str} 被多个脚本共享使用"
                        ))
        
        return conflicts
    
    def get_registrations_by_script(self, script_name: str) -> List[OutputPathRegistration]:
        """
        获取脚本的所有注册
        
        Args:
            script_name: 脚本名称
            
        Returns:
            注册列表
        """
        with self._lock:
            return [
                reg for reg in self._registrations.values()
                if reg.script_name == script_name
            ]
    
    def get_registrations_by_path(self, path: Path) -> List[OutputPathRegistration]:
        """
        获取路径的所有注册
        
        Args:
            path: 路径
            
        Returns:
            注册列表
        """
        with self._lock:
            path_str = str(path.resolve())
            registration_ids = self._path_index.get(path_str, [])
            return [
                self._registrations[rid] 
                for rid in registration_ids 
                if rid in self._registrations
            ]
    
    def get_all_registrations(self) -> List[OutputPathRegistration]:
        """获取所有注册"""
        with self._lock:
            return list(self._registrations.values())
    
    def clear_all(self) -> None:
        """清除所有注册"""
        with self._lock:
            self._registrations.clear()
            self._path_index.clear()


class DirectoryStructureManager:
    """目录结构管理器"""
    
    def __init__(self, path_manager: 'EnhancedSkillPathManager'):
        self.path_manager = path_manager
        self._lock = threading.Lock()
    
    def create_directory_structure(
        self,
        templates: Optional[Dict[str, DirectoryTemplate]] = None,
        dry_run: bool = False,
        lazy: bool = True
    ) -> Dict[str, Any]:
        """
        创建目录结构
        
        Args:
            templates: 目录模板字典，None则使用默认模板
            dry_run: 是否只预览不实际创建
            lazy: 是否懒加载模式，True时不预创建目录结构
            
        Returns:
            创建结果字典
        """
        results = {
            "created": [],
            "skipped": [],
            "failed": [],
            "dry_run": dry_run,
            "lazy": lazy,
            "timestamp": datetime.now().isoformat()
        }
        
        if lazy:
            logger.info("懒加载模式：不预创建目录结构，将按需创建")
            results["skipped"].append("懒加载模式已启用，目录将按需创建")
            return results
        
        if templates is None:
            templates = DirectoryTemplates.SKILL_TEMPLATES
        
        base_path = self.path_manager.skill_root
        
        for name, template in templates.items():
            result = self._create_template_directories(base_path, template, dry_run)
            results["created"].extend(result["created"])
            results["skipped"].extend(result["skipped"])
            results["failed"].extend(result["failed"])
        
        return results
    
    def _create_template_directories(
        self,
        base_path: Path,
        template: DirectoryTemplate,
        dry_run: bool
    ) -> Dict[str, List[str]]:
        """创建模板目录"""
        result = {
            "created": [],
            "skipped": [],
            "failed": []
        }
        
        target_path = base_path / template.name
        
        if dry_run:
            result["skipped"].append(f"[DRY-RUN] {template.name}")
            return result
        
        try:
            if not target_path.exists():
                target_path.mkdir(parents=True, exist_ok=True)
                result["created"].append(str(target_path))
            
            for sub_dir in self._flatten_structure(template.structure):
                sub_path = target_path / sub_dir
                if not sub_path.exists():
                    sub_path.mkdir(parents=True, exist_ok=True)
                    result["created"].append(str(sub_path))
                    
                    if template.gitkeep:
                        gitkeep = sub_path / ".gitkeep"
                        gitkeep.touch()
            
            for file_name in template.files_to_create:
                file_path = target_path / file_name
                if not file_path.exists():
                    file_path.touch()
                    result["created"].append(str(file_path))
                    
        except Exception as e:
            result["failed"].append(f"{template.name}: {str(e)}")
        
        return result
    
    def _flatten_structure(
        self,
        structure: Dict[str, Any],
        prefix: str = ""
    ) -> List[str]:
        """展平嵌套的目录结构"""
        paths = []
        
        for name, sub_structure in structure.items():
            path = f"{prefix}/{name}" if prefix else name
            paths.append(path)
            
            if sub_structure:
                paths.extend(self._flatten_structure(sub_structure, path))
        
        return paths
    
    def verify_structure(
        self,
        templates: Optional[Dict[str, DirectoryTemplate]] = None
    ) -> Dict[str, Any]:
        """
        验证目录结构
        
        Args:
            templates: 目录模板字典
            
        Returns:
            验证结果字典
        """
        if templates is None:
            templates = DirectoryTemplates.SKILL_TEMPLATES
        
        base_path = self.path_manager.skill_root
        
        results = {
            "valid": True,
            "missing": [],
            "invalid": [],
            "warnings": [],
            "timestamp": datetime.now().isoformat()
        }
        
        for name, template in templates.items():
            valid, errors = EnhancedPathValidator.validate_structure(base_path, template)
            
            if not valid:
                results["valid"] = False
                if template.required:
                    results["missing"].extend(errors)
                else:
                    results["warnings"].extend(errors)
        
        return results
    
    def get_directory_status(self, relative_path: str) -> Dict[str, Any]:
        """
        获取目录状态
        
        Args:
            relative_path: 相对路径
            
        Returns:
            目录状态字典
        """
        full_path = self.path_manager.resolve_path(relative_path)
        
        status = {
            "path": str(full_path),
            "relative_path": relative_path,
            "exists": full_path.exists(),
            "status": DirectoryStatus.MISSING.value,
            "is_directory": False,
            "is_empty": True,
            "file_count": 0,
            "dir_count": 0,
            "size_bytes": 0,
            "writable": False,
            "readable": False
        }
        
        if full_path.exists():
            if full_path.is_dir():
                status["status"] = DirectoryStatus.EXISTS.value
                status["is_directory"] = True
                
                try:
                    items = list(full_path.iterdir())
                    status["file_count"] = sum(1 for i in items if i.is_file())
                    status["dir_count"] = sum(1 for i in items if i.is_dir())
                    status["is_empty"] = len(items) == 0
                    
                    status["size_bytes"] = sum(
                        f.stat().st_size for f in full_path.rglob("*") if f.is_file()
                    )
                except PermissionError:
                    status["status"] = DirectoryStatus.PERMISSION_DENIED.value
                except Exception:
                    status["status"] = DirectoryStatus.INVALID.value
                
                valid, _ = EnhancedPathValidator.validate_permissions(full_path)
                status["writable"] = valid
                status["readable"] = os.access(full_path, os.R_OK)
            else:
                status["status"] = DirectoryStatus.INVALID.value
        
        return status
    
    def ensure_directory_for_file(self, file_path: Path) -> Path:
        """
        确保文件的父目录存在，按需创建
        
        Args:
            file_path: 文件路径（Path对象或字符串）
            
        Returns:
            父目录路径
        """
        if isinstance(file_path, str):
            file_path = Path(file_path)
        
        parent = file_path.parent
        
        if not parent.exists():
            parent.mkdir(parents=True, exist_ok=True)
            logger.info(f"创建目录: {parent}")
        
        return parent
    
    def ensure_directory(self, dir_path: Path) -> Path:
        """
        确保目录存在，按需创建
        
        Args:
            dir_path: 目录路径（Path对象或字符串）
            
        Returns:
            目录路径
        """
        if isinstance(dir_path, str):
            dir_path = Path(dir_path)
        
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)
            logger.info(f"创建目录: {dir_path}")
        
        return dir_path


class DirectoryHealthChecker:
    """目录健康检查器"""
    
    def __init__(self, path_manager: 'EnhancedSkillPathManager'):
        self.path_manager = path_manager
        self.structure_manager = DirectoryStructureManager(path_manager)
    
    def perform_health_check(self) -> DirectoryHealthReport:
        """
        执行目录健康检查
        
        Returns:
            健康检查报告
        """
        base_path = self.path_manager.skill_root
        templates = DirectoryTemplates.SKILL_TEMPLATES
        
        details = []
        total = 0
        existing = 0
        missing = 0
        invalid = 0
        
        for name, template in templates.items():
            target_path = base_path / name
            
            detail = {
                "name": name,
                "path": str(target_path),
                "required": template.required,
                "category": template.category,
                "status": DirectoryStatus.MISSING.value,
                "subdirectories": {}
            }
            
            total += 1
            
            if target_path.exists():
                if target_path.is_dir():
                    detail["status"] = DirectoryStatus.EXISTS.value
                    existing += 1
                    
                    for sub_dir in template.structure.keys():
                        sub_path = target_path / sub_dir
                        detail["subdirectories"][sub_dir] = {
                            "exists": sub_path.exists(),
                            "is_directory": sub_path.is_dir() if sub_path.exists() else False
                        }
                else:
                    detail["status"] = DirectoryStatus.INVALID.value
                    invalid += 1
            else:
                if template.required:
                    missing += 1
            
            details.append(detail)
        
        health_score = self._calculate_health_score(total, existing, missing, invalid)
        recommendations = self._generate_recommendations(details, templates)
        
        return DirectoryHealthReport(
            timestamp=datetime.now().isoformat(),
            base_path=str(base_path),
            mode="skill_mode",
            total_directories=total,
            existing_directories=existing,
            missing_directories=missing,
            invalid_directories=invalid,
            health_score=health_score,
            details=details,
            recommendations=recommendations
        )
    
    def _calculate_health_score(
        self,
        total: int,
        existing: int,
        missing: int,
        invalid: int
    ) -> float:
        """计算健康分数"""
        if total == 0:
            return 100.0
        
        score = (existing / total) * 100
        score -= invalid * 10
        score -= missing * 5
        
        return max(0.0, min(100.0, score))
    
    def _generate_recommendations(
        self,
        details: List[Dict[str, Any]],
        templates: Dict[str, DirectoryTemplate]
    ) -> List[str]:
        """生成建议"""
        recommendations = []
        
        for detail in details:
            if detail["status"] == DirectoryStatus.MISSING.value:
                template = templates.get(detail["name"])
                if template and template.required:
                    recommendations.append(
                        f"创建必需目录: {detail['name']} ({template.description})"
                    )
            elif detail["status"] == DirectoryStatus.INVALID.value:
                recommendations.append(
                    f"修复无效目录: {detail['name']}"
                )
            elif detail["status"] == DirectoryStatus.EXISTS.value:
                for sub_name, sub_info in detail.get("subdirectories", {}).items():
                    if not sub_info["exists"]:
                        recommendations.append(
                            f"创建子目录: {detail['name']}/{sub_name}"
                        )
        
        return recommendations


class DirectorySnapshotManager:
    """目录快照管理器"""
    
    SNAPSHOT_DIR = "directory_snapshots"
    
    def __init__(self, path_manager: 'EnhancedSkillPathManager'):
        self.path_manager = path_manager
        self._lock = threading.Lock()
    
    def create_snapshot(
        self,
        snapshot_id: Optional[str] = None
    ) -> DirectorySnapshot:
        """
        创建目录快照
        
        Args:
            snapshot_id: 快照ID，None则自动生成
            
        Returns:
            目录快照对象
        """
        if snapshot_id is None:
            snapshot_id = f"snap_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        base_path = self.path_manager.skill_root
        
        structure = self._capture_structure(base_path)
        file_count, total_size, checksum = self._calculate_stats(base_path)
        
        snapshot = DirectorySnapshot(
            snapshot_id=snapshot_id,
            timestamp=datetime.now().isoformat(),
            base_path=str(base_path),
            mode="skill_mode",
            structure=structure,
            file_count=file_count,
            total_size=total_size,
            checksum=checksum
        )
        
        self._save_snapshot(snapshot)
        
        return snapshot
    
    def _capture_structure(self, base_path: Path) -> Dict[str, Any]:
        """捕获目录结构"""
        structure = {}
        
        try:
            for item in base_path.iterdir():
                if item.name.startswith('.'):
                    continue
                
                if item.is_dir():
                    structure[item.name] = {
                        "type": "directory",
                        "children": self._capture_structure(item)
                    }
                else:
                    structure[item.name] = {
                        "type": "file",
                        "size": item.stat().st_size
                    }
        except PermissionError:
            pass
        
        return structure
    
    def _calculate_stats(
        self,
        base_path: Path
    ) -> Tuple[int, int, str]:
        """计算统计信息"""
        file_count = 0
        total_size = 0
        
        try:
            for item in base_path.rglob("*"):
                if item.is_file():
                    file_count += 1
                    try:
                        total_size += item.stat().st_size
                    except:
                        pass
        except:
            pass
        
        checksum = f"{file_count}_{total_size}"
        
        return file_count, total_size, checksum
    
    def _save_snapshot(self, snapshot: DirectorySnapshot) -> bool:
        """保存快照到文件"""
        try:
            snapshot_dir = self.path_manager.skill_root / self.SNAPSHOT_DIR
            snapshot_dir.mkdir(parents=True, exist_ok=True)
            
            snapshot_file = snapshot_dir / f"{snapshot.snapshot_id}.json"
            
            with open(snapshot_file, 'w', encoding='utf-8') as f:
                json.dump(asdict(snapshot), f, indent=2, ensure_ascii=False)
            
            return True
        except Exception as e:
            logger.error(f"保存快照失败: {e}")
            return False
    
    def load_snapshot(self, snapshot_id: str) -> Optional[DirectorySnapshot]:
        """加载快照"""
        try:
            snapshot_file = self.path_manager.skill_root / self.SNAPSHOT_DIR / f"{snapshot_id}.json"
            
            if not snapshot_file.exists():
                return None
            
            with open(snapshot_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            return DirectorySnapshot(**data)
        except Exception as e:
            logger.error(f"加载快照失败: {e}")
            return None
    
    def list_snapshots(self) -> List[Dict[str, Any]]:
        """列出所有快照"""
        snapshots = []
        snapshot_dir = self.path_manager.skill_root / self.SNAPSHOT_DIR
        
        if not snapshot_dir.exists():
            return snapshots
        
        for snapshot_file in snapshot_dir.glob("*.json"):
            try:
                with open(snapshot_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                snapshots.append({
                    "snapshot_id": data.get("snapshot_id"),
                    "timestamp": data.get("timestamp"),
                    "mode": data.get("mode"),
                    "file_count": data.get("file_count"),
                    "total_size": data.get("total_size")
                })
            except:
                pass
        
        return sorted(snapshots, key=lambda x: x["timestamp"], reverse=True)


class EnhancedSkillPathManager:
    """
    增强版技能路径管理器
    
    单例模式实现，提供完整的技能路径配置管理功能
    """
    
    _instance: Optional['EnhancedSkillPathManager'] = None
    _lock = threading.Lock()
    _initialized = False
    
    def __new__(cls, *args, **kwargs):
        """单例模式实现"""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(
        self,
        skill_root: Optional[Union[str, Path]] = None,
        auto_detect: bool = True,
        lazy_init: bool = True
    ):
        """
        初始化技能路径管理器
        
        Args:
            skill_root: 技能根目录，None则自动检测
            auto_detect: 是否自动检测技能根目录
            lazy_init: 是否懒加载初始化
        """
        if EnhancedSkillPathManager._initialized:
            return
        
        with EnhancedSkillPathManager._lock:
            if EnhancedSkillPathManager._initialized:
                return
            
            if skill_root is None and auto_detect:
                skill_root = self._detect_skill_root()
            
            if skill_root is None:
                raise PathConfigError("无法确定技能根目录，请手动指定")
            
            self._skill_root = Path(skill_root).resolve()
            self._path_config = SkillPathConfig.from_skill_root(self._skill_root)
            self._env_overrides: Dict[str, Path] = {}
            self._config_cache: Dict[str, Any] = {}
            self._last_reload_time: Optional[datetime] = None
            self._reload_interval = 60
            
            self._structure_manager: Optional[DirectoryStructureManager] = None
            self._health_checker: Optional[DirectoryHealthChecker] = None
            self._snapshot_manager: Optional[DirectorySnapshotManager] = None
            self._output_path_registry: Optional[OutputPathRegistry] = None
            
            self._load_env_overrides()
            
            if not lazy_init:
                self._ensure_critical_paths()
            
            EnhancedSkillPathManager._initialized = True
            
            logger.info(f"技能路径管理器已初始化: {self._skill_root}")
    
    @classmethod
    def get_instance(cls) -> 'EnhancedSkillPathManager':
        """获取单例实例"""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    @classmethod
    def reset_instance(cls):
        """重置单例实例（用于测试）"""
        with cls._lock:
            cls._instance = None
            cls._initialized = False
    
    def _detect_skill_root(self) -> Optional[Path]:
        """检测技能根目录"""
        return SkillDetector.find_skill_root()
    
    def _load_env_overrides(self):
        """加载环境变量覆盖"""
        env_overrides = EnvironmentVariableManager.get_all_env_overrides()
        for key, value in env_overrides.items():
            self._env_overrides[key] = Path(value)
    
    def _ensure_critical_paths(self):
        """确保关键路径存在"""
        critical_paths = [
            PathKey.SKILL_ROOT,
            PathKey.SUBSKILLS_DIR,
            PathKey.SCRIPTS_DIR,
            PathKey.RESOURCES_DIR
        ]
        
        for path_key in critical_paths:
            self.ensure_path(path_key)
    
    @property
    def skill_root(self) -> Path:
        """获取技能根目录"""
        return self._skill_root
    
    @property
    def path_config(self) -> SkillPathConfig:
        """获取路径配置"""
        return self._path_config
    
    @property
    def structure_manager(self) -> DirectoryStructureManager:
        """获取目录结构管理器"""
        if self._structure_manager is None:
            self._structure_manager = DirectoryStructureManager(self)
        return self._structure_manager
    
    @property
    def health_checker(self) -> DirectoryHealthChecker:
        """获取目录健康检查器"""
        if self._health_checker is None:
            self._health_checker = DirectoryHealthChecker(self)
        return self._health_checker
    
    @property
    def snapshot_manager(self) -> DirectorySnapshotManager:
        """获取目录快照管理器"""
        if self._snapshot_manager is None:
            self._snapshot_manager = DirectorySnapshotManager(self)
        return self._snapshot_manager
    
    @property
    def output_path_registry(self) -> OutputPathRegistry:
        """获取输出路径注册器"""
        if self._output_path_registry is None:
            self._output_path_registry = OutputPathRegistry()
        return self._output_path_registry
    
    def resolve_path(self, path_key: Union[PathKey, str]) -> Path:
        """
        根据键名解析路径
        
        Args:
            path_key: 路径键（枚举或字符串）
            
        Returns:
            解析后的路径
        """
        if isinstance(path_key, str):
            try:
                path_key = PathKey(path_key)
            except ValueError:
                return self._skill_root / path_key
        
        env_override = EnvironmentVariableManager.get_env_override(path_key)
        if env_override:
            return env_override
        
        config_dict = asdict(self._path_config)
        path_value = config_dict.get(path_key.value)
        
        if path_value is None:
            raise PathConfigError(f"未知的路径键: {path_key}")
        
        return Path(path_value)
    
    def get_relative_path(self, absolute_path: Union[str, Path]) -> str:
        """
        获取相对路径
        
        Args:
            absolute_path: 绝对路径
            
        Returns:
            相对于技能根目录的相对路径
        """
        if isinstance(absolute_path, str):
            absolute_path = Path(absolute_path)
        
        try:
            return str(absolute_path.relative_to(self._skill_root))
        except ValueError:
            return str(absolute_path)
    
    def to_absolute_path(self, relative_path: str) -> Path:
        """
        将相对路径转换为绝对路径
        
        Args:
            relative_path: 相对路径
            
        Returns:
            绝对路径
        """
        if Path(relative_path).is_absolute():
            return Path(relative_path)
        
        return self._skill_root / relative_path
    
    def validate_path(self, path: Union[str, Path, PathKey]) -> Tuple[bool, Optional[str]]:
        """
        验证路径是否存在
        
        Args:
            path: 路径（字符串、Path对象或PathKey枚举）
            
        Returns:
            (是否有效, 错误信息) 元组
        """
        if isinstance(path, PathKey):
            path = self.resolve_path(path)
        elif isinstance(path, str):
            path = self.to_absolute_path(path)
        
        if not path.exists():
            return False, f"路径不存在: {path}"
        
        return True, None
    
    def ensure_path(self, path_key: Union[PathKey, str]) -> Path:
        """
        确保路径存在，不存在则创建
        
        Args:
            path_key: 路径键
            
        Returns:
            路径对象
        """
        path = self.resolve_path(path_key)
        
        if not path.exists():
            path.mkdir(parents=True, exist_ok=True)
            logger.info(f"创建目录: {path}")
        
        return path
    
    def get_subskill_path(self, subskill_name: str) -> Path:
        """
        获取特定子技能路径
        
        Args:
            subskill_name: 子技能名称
            
        Returns:
            子技能文件路径
        """
        subskill_file = f"{subskill_name}.md"
        return self.resolve_path(PathKey.SUBSKILLS_DIR) / subskill_file
    
    def get_all_subskills(self) -> List[SubskillInfo]:
        """
        获取所有子技能信息
        
        Returns:
            子技能信息列表
        """
        subskills_dir = self.resolve_path(PathKey.SUBSKILLS_DIR)
        subskills = []
        
        if not subskills_dir.exists():
            return subskills
        
        for subskill_file in subskills_dir.glob("*.md"):
            try:
                stat = subskill_file.stat()
                subskills.append(SubskillInfo(
                    name=subskill_file.stem,
                    path=subskill_file,
                    exists=True,
                    size=stat.st_size,
                    last_modified=datetime.fromtimestamp(stat.st_mtime).isoformat()
                ))
            except Exception as e:
                logger.warning(f"读取子技能文件失败: {subskill_file}, 错误: {e}")
        
        return sorted(subskills, key=lambda x: x.name)
    
    def get_script_path(self, script_name: str, script_type: str = "utils") -> Path:
        """
        获取脚本路径
        
        Args:
            script_name: 脚本名称（不含扩展名）
            script_type: 脚本类型（core, pipeline, test, analysis, optimization, requirements, utils, monitoring）
            
        Returns:
            脚本文件路径
        """
        type_to_key = {
            "core": PathKey.CORE_SCRIPTS_DIR,
            "pipeline": PathKey.PIPELINE_SCRIPTS_DIR,
            "test": PathKey.TEST_SCRIPTS_DIR,
            "analysis": PathKey.ANALYSIS_SCRIPTS_DIR,
            "optimization": PathKey.OPTIMIZATION_SCRIPTS_DIR,
            "requirements": PathKey.REQUIREMENTS_SCRIPTS_DIR,
            "utils": PathKey.UTILITY_SCRIPTS_DIR,
            "monitoring": PathKey.MONITORING_SCRIPTS_DIR
        }
        
        script_dir_key = type_to_key.get(script_type, PathKey.UTILITY_SCRIPTS_DIR)
        script_dir = self.resolve_path(script_dir_key)
        
        return script_dir / f"{script_name}.py"
    
    def get_template_path(self, template_name: str) -> Path:
        """
        获取模板路径
        
        Args:
            template_name: 模板名称
            
        Returns:
            模板文件路径
        """
        templates_dir = self.resolve_path(PathKey.TEMPLATES_DIR)
        return templates_dir / f"{template_name}.md"
    
    def get_report_path(self, report_name: str) -> Path:
        """
        获取报告路径
        
        Args:
            report_name: 报告名称
            
        Returns:
            报告文件路径
        """
        reports_dir = self.resolve_path(PathKey.REPORTS_DIR)
        return reports_dir / f"{report_name}.md"
    
    def get_docs_path(
        self,
        subdir: Optional[Union[DocsSubdir, str]] = None,
        filename: Optional[str] = None,
        create_if_missing: bool = True,
        validate: bool = False
    ) -> Path:
        """
        获取docs目录下的路径
        
        Args:
            subdir: 子目录类型（DocsSubdir枚举或字符串），None则返回docs根目录
            filename: 文件名，可选
            create_if_missing: 如果路径不存在是否创建
            validate: 是否验证路径（检查是否在允许的目录范围内）
            
        Returns:
            docs目录下的路径
            
        Raises:
            PathValidationError: 当validate=True且路径不在允许范围内时
            
        Example:
            >>> manager = EnhancedSkillPathManager()
            >>> # 获取docs根目录
            >>> docs_root = manager.get_docs_path()
            >>> # 获取docs/reports目录
            >>> reports_dir = manager.get_docs_path(DocsSubdir.REPORTS)
            >>> # 获取docs/api目录下的文件
            >>> api_file = manager.get_docs_path(DocsSubdir.API, filename="endpoint.md")
            >>> # 获取自定义子目录
            >>> custom_dir = manager.get_docs_path("custom/subdir")
            >>> # 获取并验证路径
            >>> validated_path = manager.get_docs_path(DocsSubdir.WORKFLOW, validate=True)
        """
        docs_dir = self.resolve_path(PathKey.DOCS_DIR)
        
        if subdir is None:
            target_path = docs_dir
        else:
            if isinstance(subdir, DocsSubdir):
                env_override = EnvironmentVariableManager.get_docs_subdir_env(subdir)
                if env_override:
                    target_path = env_override
                else:
                    subdir_to_path_key = {
                        DocsSubdir.REPORTS: PathKey.DOCS_REPORTS_DIR,
                        DocsSubdir.API: PathKey.DOCS_API_DIR,
                        DocsSubdir.WORKFLOW: PathKey.DOCS_WORKFLOW_DIR,
                        DocsSubdir.KNOWLEDGE: PathKey.DOCS_KNOWLEDGE_DIR
                    }
                    path_key = subdir_to_path_key.get(subdir)
                    if path_key:
                        target_path = self.resolve_path(path_key)
                    else:
                        target_path = docs_dir / subdir.value
            else:
                target_path = docs_dir / subdir
        
        if filename:
            target_path = target_path / filename
        
        if validate:
            validation_result = self.validate_output_path_in_allowed_dirs(target_path)
            if not validation_result["valid"]:
                raise PathValidationError(validation_result["error"])
        
        if create_if_missing:
            if filename:
                target_path.parent.mkdir(parents=True, exist_ok=True)
            else:
                target_path.mkdir(parents=True, exist_ok=True)
            logger.debug(f"确保docs路径存在: {target_path}")
        
        return target_path
    
    def validate_output_path_in_allowed_dirs(
        self,
        path: Union[str, Path],
        allowed_dirs: Optional[List[Union[PathKey, str]]] = None
    ) -> Dict[str, Any]:
        """
        验证输出路径是否在允许的目录范围内
        
        Args:
            path: 待验证的路径
            allowed_dirs: 允许的目录列表，None则使用默认允许列表
            
        Returns:
            验证结果字典，包含:
            - valid: 是否有效
            - path: 验证的路径
            - allowed_dirs: 允许的目录列表
            - error: 错误信息（如果无效）
            - matched_dir: 匹配的允许目录（如果有效）
            
        Example:
            >>> manager = EnhancedSkillPathManager()
            >>> result = manager.validate_output_path_in_allowed_dirs("/path/to/docs/reports")
            >>> if result['valid']:
            ...     print(f"路径有效，匹配目录: {result['matched_dir']}")
        """
        if isinstance(path, str):
            path = Path(path)
        
        if allowed_dirs is None:
            allowed_dirs = [
                PathKey.DOCS_DIR,
                PathKey.DOCS_REPORTS_DIR,
                PathKey.DOCS_API_DIR,
                PathKey.DOCS_WORKFLOW_DIR,
                PathKey.DOCS_KNOWLEDGE_DIR,
                PathKey.REPORTS_DIR,
                PathKey.DATA_DIR,
                PathKey.TEMP_DIR,
                PathKey.LOGS_DIR,
                PathKey.CACHE_DIR
            ]
        
        resolved_path = path.resolve()
        
        result = {
            "valid": False,
            "path": str(path),
            "resolved_path": str(resolved_path),
            "allowed_dirs": [],
            "error": None,
            "matched_dir": None
        }
        
        for allowed_dir in allowed_dirs:
            if isinstance(allowed_dir, PathKey):
                allowed_path = self.resolve_path(allowed_dir).resolve()
            else:
                allowed_path = self._skill_root / str(allowed_dir)
            
            result["allowed_dirs"].append(str(allowed_path))
            
            try:
                resolved_path.relative_to(allowed_path)
                result["valid"] = True
                result["matched_dir"] = str(allowed_path)
                result["error"] = None
                return result
            except ValueError:
                continue
        
        result["error"] = f"路径 {resolved_path} 不在允许的目录范围内"
        return result
    
    def detect_path_conflicts(
        self,
        path: Union[str, Path],
        check_existing_files: bool = True
    ) -> Dict[str, Any]:
        """
        检测路径冲突
        
        Args:
            path: 待检测的路径
            check_existing_files: 是否检查已存在的文件
            
        Returns:
            冲突检测结果字典，包含:
            - has_conflict: 是否存在冲突
            - path: 检测的路径
            - conflicts: 冲突列表
            - existing_registrations: 已注册的使用该路径的脚本
            - existing_files: 已存在的相关文件
            
        Example:
            >>> manager = EnhancedSkillPathManager()
            >>> result = manager.detect_path_conflicts("/path/to/output.json")
            >>> if result['has_conflict']:
            ...     print("发现冲突:")
            ...     for conflict in result['conflicts']:
            ...         print(f"  - {conflict}")
        """
        if isinstance(path, str):
            path = Path(path)
        
        result = {
            "has_conflict": False,
            "path": str(path),
            "conflicts": [],
            "existing_registrations": [],
            "existing_files": []
        }
        
        registrations = self.output_path_registry.get_registrations_by_path(path)
        if registrations:
            result["has_conflict"] = True
            result["existing_registrations"] = [r.to_dict() for r in registrations]
            result["conflicts"].append({
                "type": "registration_conflict",
                "message": f"路径已被 {len(registrations)} 个脚本注册",
                "scripts": [r.script_name for r in registrations]
            })
        
        if check_existing_files:
            if path.exists():
                result["has_conflict"] = True
                result["existing_files"].append(str(path))
                result["conflicts"].append({
                    "type": "file_exists",
                    "message": f"文件已存在: {path}",
                    "path": str(path)
                })
            
            if path.is_dir():
                parent = path.parent
            else:
                parent = path.parent if path.suffix else path
            
            similar_files = []
            if parent.exists():
                pattern = f"{path.stem}*" if path.suffix else "*"
                for f in parent.glob(pattern):
                    if f != path:
                        similar_files.append(str(f))
            
            if similar_files:
                result["conflicts"].append({
                    "type": "similar_files",
                    "message": f"发现 {len(similar_files)} 个相似文件",
                    "files": similar_files[:10]
                })
        
        return result
    
    def generate_validation_report(
        self,
        paths: Optional[List[Union[str, Path]]] = None,
        check_permissions: bool = True,
        check_disk_space: bool = True,
        check_conflicts: bool = True
    ) -> Dict[str, Any]:
        """
        生成路径验证报告
        
        Args:
            paths: 待验证的路径列表，None则验证所有关键路径
            check_permissions: 是否检查权限
            check_disk_space: 是否检查磁盘空间
            check_conflicts: 是否检查冲突
            
        Returns:
            验证报告字典，包含:
            - timestamp: 时间戳
            - overall_valid: 整体是否有效
            - total_paths: 总路径数
            - valid_paths: 有效路径数
            - invalid_paths: 无效路径数
            - warnings: 警告数
            - details: 详细验证结果
            - summary: 摘要信息
            
        Example:
            >>> manager = EnhancedSkillPathManager()
            >>> report = manager.generate_validation_report()
            >>> print(f"验证结果: {report['overall_valid']}")
            >>> print(f"有效路径: {report['valid_paths']}/{report['total_paths']}")
        """
        if paths is None:
            paths = [self.resolve_path(key) for key in PathKey]
        
        report = {
            "timestamp": datetime.now().isoformat(),
            "overall_valid": True,
            "total_paths": len(paths),
            "valid_paths": 0,
            "invalid_paths": 0,
            "warnings_count": 0,
            "details": [],
            "summary": {
                "missing_paths": [],
                "permission_issues": [],
                "disk_space_issues": [],
                "conflicts": []
            }
        }
        
        for path in paths:
            if isinstance(path, str):
                path = Path(path)
            
            detail = {
                "path": str(path),
                "exists": False,
                "is_directory": False,
                "writable": False,
                "has_space": False,
                "conflicts": [],
                "errors": [],
                "warnings": []
            }
            
            detail["exists"] = path.exists()
            
            if path.exists():
                detail["is_directory"] = path.is_dir()
                
                if check_permissions:
                    if path.is_dir():
                        valid, error = EnhancedPathValidator.validate_permissions(path)
                        detail["writable"] = valid
                        if not valid:
                            detail["warnings"].append(error)
                            report["summary"]["permission_issues"].append(str(path))
                    else:
                        detail["writable"] = os.access(path, os.W_OK)
                
                check_path = path if path.is_dir() else path.parent
                if check_disk_space:
                    valid, error = EnhancedPathValidator.check_disk_space(check_path)
                    detail["has_space"] = valid
                    if not valid:
                        detail["warnings"].append(error)
                        report["summary"]["disk_space_issues"].append(str(path))
            else:
                detail["warnings"].append(f"路径不存在: {path}")
                report["summary"]["missing_paths"].append(str(path))
            
            if check_conflicts:
                conflict_result = self.detect_path_conflicts(path)
                if conflict_result["has_conflict"]:
                    detail["conflicts"] = conflict_result["conflicts"]
                    report["summary"]["conflicts"].append(str(path))
            
            if detail["errors"]:
                report["overall_valid"] = False
                report["invalid_paths"] += 1
            else:
                report["valid_paths"] += 1
            
            if detail["warnings"]:
                report["warnings_count"] += 1
            
            report["details"].append(detail)
        
        return report
    
    def get_output_path(
        self,
        output_type: OutputType,
        subdirectory: Optional[str] = None,
        filename: Optional[str] = None,
        create_if_missing: bool = True,
        script_name: Optional[str] = None,
        register: bool = False,
        exclusive: bool = False
    ) -> Path:
        """
        统一获取输出路径，支持不同类型的输出
        
        Args:
            output_type: 输出类型（报告、日志、临时文件等）
            subdirectory: 子目录名称，可选
            filename: 文件名，可选
            create_if_missing: 如果路径不存在是否创建
            script_name: 脚本名称，用于注册
            register: 是否注册到路径注册器
            exclusive: 是否独占使用（仅当register=True时有效）
            
        Returns:
            输出路径
            
        Example:
            >>> manager = EnhancedSkillPathManager()
            >>> # 获取报告输出路径
            >>> report_path = manager.get_output_path(OutputType.REPORT, filename="report.md")
            >>> # 获取日志输出路径
            >>> log_path = manager.get_output_path(OutputType.LOG, subdirectory="app", filename="app.log")
            >>> # 获取临时文件路径并注册
            >>> temp_path = manager.get_output_path(
            ...     OutputType.TEMP, 
            ...     filename="temp_data.json",
            ...     script_name="data_processor",
            ...     register=True
            ... )
        """
        env_override = EnvironmentVariableManager.get_output_path_env(output_type)
        
        if env_override:
            base_path = env_override
        else:
            type_to_path_key = {
                OutputType.REPORT: PathKey.REPORTS_DIR,
                OutputType.LOG: PathKey.LOGS_DIR,
                OutputType.TEMP: PathKey.TEMP_DIR,
                OutputType.CACHE: PathKey.CACHE_DIR,
                OutputType.DATA: PathKey.DATA_DIR,
                OutputType.BACKUP: PathKey.DATA_DIR,
                OutputType.EXPORT: PathKey.REPORTS_DIR,
                OutputType.DOWNLOAD: PathKey.DATA_DIR,
                OutputType.UPLOAD: PathKey.DATA_DIR,
                OutputType.SNAPSHOT: PathKey.CACHE_DIR
            }
            
            path_key = type_to_path_key.get(output_type, PathKey.TEMP_DIR)
            base_path = self.resolve_path(path_key)
        
        output_path = base_path
        
        if subdirectory:
            output_path = output_path / subdirectory
        
        if filename:
            output_path = output_path / filename
        
        if create_if_missing and not output_path.exists():
            if filename:
                output_path.parent.mkdir(parents=True, exist_ok=True)
            else:
                output_path.mkdir(parents=True, exist_ok=True)
            logger.debug(f"创建输出路径: {output_path}")
        
        if register and script_name:
            self.output_path_registry.register(
                script_name=script_name,
                output_type=output_type,
                path=output_path if not filename else output_path.parent,
                description=f"输出路径: {output_type.value}",
                exclusive=exclusive
            )
        
        return output_path
    
    def validate_output_paths(
        self,
        output_types: Optional[List[OutputType]] = None,
        check_permissions: bool = True,
        min_space_mb: int = 100
    ) -> Dict[str, Any]:
        """
        验证输出路径配置的有效性
        
        Args:
            output_types: 要验证的输出类型列表，None则验证所有类型
            check_permissions: 是否检查写权限
            min_space_mb: 最小磁盘空间要求(MB)
            
        Returns:
            验证结果字典，包含:
            - valid: 整体是否有效
            - results: 各输出类型的验证结果
            - errors: 错误列表
            - warnings: 警告列表
            
        Example:
            >>> manager = EnhancedSkillPathManager()
            >>> result = manager.validate_output_paths()
            >>> if not result['valid']:
            ...     print("输出路径验证失败:")
            ...     for error in result['errors']:
            ...         print(f"  - {error}")
        """
        if output_types is None:
            output_types = list(OutputType)
        
        result = {
            "valid": True,
            "results": {},
            "errors": [],
            "warnings": [],
            "timestamp": datetime.now().isoformat()
        }
        
        for output_type in output_types:
            try:
                path = self.get_output_path(output_type, create_if_missing=False)
                
                exists = path.exists()
                writable = False
                has_space = False
                space_mb = None
                error = None
                
                if not exists:
                    parent = path.parent if path.suffix else path
                    while not parent.exists() and parent != parent.parent:
                        parent = parent.parent
                    
                    if parent.exists():
                        valid, perm_error = EnhancedPathValidator.validate_permissions(
                            parent, require_write=check_permissions
                        )
                        writable = valid
                        
                        valid, space_error = EnhancedPathValidator.check_disk_space(
                            parent, min_space_mb
                        )
                        has_space = valid
                        
                        if hasattr(shutil, 'disk_usage'):
                            try:
                                usage = shutil.disk_usage(parent)
                                space_mb = usage.free / (1024 * 1024)
                            except:
                                pass
                    else:
                        error = f"路径不存在且无法创建: {path}"
                        result["valid"] = False
                        result["errors"].append(error)
                else:
                    if path.is_file():
                        writable = os.access(path, os.W_OK)
                        parent = path.parent
                    else:
                        valid, perm_error = EnhancedPathValidator.validate_permissions(
                            path, require_write=check_permissions
                        )
                        writable = valid
                        parent = path
                    
                    valid, space_error = EnhancedPathValidator.check_disk_space(
                        parent, min_space_mb
                    )
                    has_space = valid
                    
                    if hasattr(shutil, 'disk_usage'):
                        try:
                            usage = shutil.disk_usage(parent)
                            space_mb = usage.free / (1024 * 1024)
                        except:
                            pass
                
                validation_result = OutputPathValidationResult(
                    output_type=output_type,
                    path=path,
                    exists=exists,
                    writable=writable,
                    has_space=has_space,
                    space_mb=space_mb,
                    error=error
                )
                
                result["results"][output_type.value] = validation_result.to_dict()
                
                if not writable and check_permissions:
                    warning = f"输出路径 {output_type.value} 不可写: {path}"
                    result["warnings"].append(warning)
                
                if not has_space:
                    warning = f"输出路径 {output_type.value} 磁盘空间不足: {path}"
                    result["warnings"].append(warning)
                
                if error:
                    result["errors"].append(error)
                    
            except Exception as e:
                error_msg = f"验证输出路径 {output_type.value} 时出错: {str(e)}"
                result["errors"].append(error_msg)
                result["valid"] = False
                result["results"][output_type.value] = {
                    "output_type": output_type.value,
                    "path": None,
                    "exists": False,
                    "writable": False,
                    "has_space": False,
                    "space_mb": None,
                    "error": error_msg
                }
        
        return result
    
    def register_output_path(
        self,
        script_name: str,
        output_type: OutputType,
        path: Optional[Path] = None,
        subdirectory: Optional[str] = None,
        filename: Optional[str] = None,
        description: str = "",
        exclusive: bool = False
    ) -> str:
        """
        注册输出路径（用于冲突检测）
        
        Args:
            script_name: 脚本名称
            output_type: 输出类型
            path: 自定义路径，None则自动获取
            subdirectory: 子目录
            filename: 文件名
            description: 描述信息
            exclusive: 是否独占使用
            
        Returns:
            注册ID
            
        Example:
            >>> manager = EnhancedSkillPathManager()
            >>> # 注册独占使用的输出路径
            >>> reg_id = manager.register_output_path(
            ...     script_name="my_script",
            ...     output_type=OutputType.TEMP,
            ...     filename="exclusive_temp.json",
            ...     description="独占临时文件",
            ...     exclusive=True
            ... )
        """
        if path is None:
            path = self.get_output_path(
                output_type=output_type,
                subdirectory=subdirectory,
                filename=filename,
                create_if_missing=True
            )
        
        return self.output_path_registry.register(
            script_name=script_name,
            output_type=output_type,
            path=path,
            description=description,
            exclusive=exclusive
        )
    
    def check_output_path_conflicts(self) -> List[OutputPathConflict]:
        """
        检查输出路径冲突
        
        Returns:
            冲突列表
            
        Example:
            >>> manager = EnhancedSkillPathManager()
            >>> conflicts = manager.check_output_path_conflicts()
            >>> for conflict in conflicts:
            ...     print(f"冲突: {conflict.message}")
            ...     for reg in conflict.registrations:
            ...         print(f"  - {reg.script_name}: {reg.path}")
        """
        return self.output_path_registry.check_conflicts()
    
    def get_output_path_registrations(
        self,
        script_name: Optional[str] = None,
        output_type: Optional[OutputType] = None
    ) -> List[OutputPathRegistration]:
        """
        获取输出路径注册信息
        
        Args:
            script_name: 脚本名称，None则获取所有
            output_type: 输出类型，None则获取所有
            
        Returns:
            注册信息列表
        """
        if script_name:
            registrations = self.output_path_registry.get_registrations_by_script(script_name)
        else:
            registrations = self.output_path_registry.get_all_registrations()
        
        if output_type:
            registrations = [r for r in registrations if r.output_type == output_type]
        
        return registrations
    
    def initialize_workspace(
        self,
        create_structure: bool = False,
        verify: bool = True,
        dry_run: bool = False,
        lazy: bool = True
    ) -> Dict[str, Any]:
        """
        初始化工作空间（懒加载模式）
        
        Args:
            create_structure: 是否创建目录结构（默认False，采用懒加载）
            verify: 是否验证结构
            dry_run: 是否只预览
            lazy: 是否使用懒加载模式（默认True）
            
        Returns:
            初始化结果字典
        """
        result = {
            "skill_root": str(self._skill_root),
            "lazy_mode": lazy,
            "structure_created": None,
            "verification": None,
            "health_report": None,
            "timestamp": datetime.now().isoformat()
        }
        
        if lazy:
            logger.info("懒加载模式：工作空间初始化不预创建目录")
            result["structure_created"] = {
                "lazy": True,
                "message": "懒加载模式已启用，目录将按需创建"
            }
        elif create_structure:
            result["structure_created"] = self.structure_manager.create_directory_structure(
                dry_run=dry_run,
                lazy=False
            )
        
        if verify:
            result["verification"] = self.structure_manager.verify_structure()
            health_report = self.health_checker.perform_health_check()
            result["health_report"] = asdict(health_report)
        
        return result
    
    def validate_workspace(
        self,
        check_permissions: bool = True,
        check_disk_space: bool = True,
        min_disk_space_mb: int = 100
    ) -> Dict[str, Any]:
        """
        验证工作空间
        
        Args:
            check_permissions: 是否检查权限
            check_disk_space: 是否检查磁盘空间
            min_disk_space_mb: 最小磁盘空间(MB)
            
        Returns:
            验证结果字典
        """
        result = {
            "valid": True,
            "errors": [],
            "warnings": [],
            "checks": {}
        }
        
        valid, error = EnhancedPathValidator.validate_permissions(
            self._skill_root, require_write=check_permissions
        )
        result["checks"]["permissions"] = {"valid": valid, "error": error}
        if not valid:
            result["valid"] = False
            result["errors"].append(error)
        
        if check_disk_space:
            valid, error = EnhancedPathValidator.check_disk_space(
                self._skill_root, min_disk_space_mb
            )
            result["checks"]["disk_space"] = {"valid": valid, "error": error}
            if not valid:
                result["warnings"].append(error)
        
        structure_result = self.structure_manager.verify_structure()
        result["checks"]["structure"] = structure_result
        if not structure_result["valid"]:
            result["valid"] = False
            result["errors"].extend(structure_result["missing"])
            result["warnings"].extend(structure_result["warnings"])
        
        return result
    
    def get_workspace_info(self) -> Dict[str, Any]:
        """
        获取工作空间信息
        
        Returns:
            工作空间信息字典
        """
        info = {
            "skill_root": str(self._skill_root),
            "path_config": self._path_config.to_dict(),
            "env_overrides": {k: str(v) for k, v in self._env_overrides.items()},
            "directory_status": {},
            "health_score": None,
            "subskills_count": 0,
            "timestamp": datetime.now().isoformat()
        }
        
        templates = DirectoryTemplates.SKILL_TEMPLATES
        for name in templates.keys():
            info["directory_status"][name] = self.structure_manager.get_directory_status(name)
        
        health_report = self.health_checker.perform_health_check()
        info["health_score"] = health_report.health_score
        
        subskills = self.get_all_subskills()
        info["subskills_count"] = len(subskills)
        
        return info
    
    def create_snapshot(self, snapshot_id: Optional[str] = None) -> DirectorySnapshot:
        """创建工作空间快照"""
        return self.snapshot_manager.create_snapshot(snapshot_id)
    
    def restore_from_snapshot(self, snapshot_id: str) -> Dict[str, Any]:
        """
        从快照恢复（仅恢复结构信息，不恢复文件内容）
        
        Args:
            snapshot_id: 快照ID
            
        Returns:
            恢复结果字典
        """
        snapshot = self.snapshot_manager.load_snapshot(snapshot_id)
        
        if snapshot is None:
            return {
                "success": False,
                "error": f"快照不存在: {snapshot_id}"
            }
        
        result = {
            "success": True,
            "snapshot_id": snapshot_id,
            "restored_directories": [],
            "missing_directories": [],
            "timestamp": datetime.now().isoformat()
        }
        
        def restore_structure(structure: Dict[str, Any], current_path: Path):
            for name, info in structure.items():
                if info.get("type") == "directory":
                    dir_path = current_path / name
                    if not dir_path.exists():
                        try:
                            dir_path.mkdir(parents=True, exist_ok=True)
                            result["restored_directories"].append(str(dir_path))
                        except Exception as e:
                            result["missing_directories"].append(str(dir_path))
                    
                    if info.get("children"):
                        restore_structure(info["children"], dir_path)
        
        restore_structure(snapshot.structure, self._skill_root)
        
        return result
    
    def reload_config(self, force: bool = False) -> bool:
        """
        重新加载配置
        
        Args:
            force: 是否强制重新加载
            
        Returns:
            是否重新加载
        """
        now = datetime.now()
        
        if not force and self._last_reload_time:
            elapsed = (now - self._last_reload_time).total_seconds()
            if elapsed < self._reload_interval:
                return False
        
        self._load_env_overrides()
        self._config_cache.clear()
        self._last_reload_time = now
        
        logger.info("配置已重新加载")
        return True
    
    def export_config(self, output_file: Optional[Union[str, Path]] = None) -> Dict[str, Any]:
        """
        导出配置
        
        Args:
            output_file: 输出文件路径，None则不保存
            
        Returns:
            配置字典
        """
        config = {
            "skill_root": str(self._skill_root),
            "path_config": self._path_config.to_dict(),
            "env_overrides": {k: str(v) for k, v in self._env_overrides.items()},
            "exported_at": datetime.now().isoformat()
        }
        
        if output_file:
            output_path = Path(output_file)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            
            logger.info(f"配置已导出到: {output_path}")
        
        return config
    
    @classmethod
    def from_config_file(cls, config_file: Union[str, Path]) -> 'EnhancedSkillPathManager':
        """
        从配置文件创建实例
        
        Args:
            config_file: 配置文件路径
            
        Returns:
            管理器实例
        """
        config_path = Path(config_file)
        
        if not config_path.exists():
            raise PathConfigError(f"配置文件不存在: {config_path}")
        
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        skill_root = config.get("skill_root")
        if not skill_root:
            raise PathConfigError("配置文件缺少 skill_root 字段")
        
        instance = cls(skill_root=skill_root, auto_detect=False)
        
        if "env_overrides" in config:
            for key, value in config["env_overrides"].items():
                instance._env_overrides[key] = Path(value)
        
        return instance


def create_path_manager(
    skill_root: Optional[Union[str, Path]] = None,
    auto_detect: bool = True,
    lazy_init: bool = True
) -> EnhancedSkillPathManager:
    """
    创建路径管理器的便捷函数
    
    Args:
        skill_root: 技能根目录
        auto_detect: 是否自动检测
        lazy_init: 是否懒加载
        
    Returns:
        路径管理器实例
    """
    return EnhancedSkillPathManager(
        skill_root=skill_root,
        auto_detect=auto_detect,
        lazy_init=lazy_init
    )


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="增强版技能路径配置管理器 - Sanliu 技能",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        '--skill-root',
        type=str,
        help='技能根目录'
    )
    parser.add_argument(
        '--init',
        action='store_true',
        help='初始化工作空间'
    )
    parser.add_argument(
        '--validate',
        action='store_true',
        help='验证工作空间'
    )
    parser.add_argument(
        '--health-check',
        action='store_true',
        help='执行健康检查'
    )
    parser.add_argument(
        '--snapshot',
        action='store_true',
        help='创建快照'
    )
    parser.add_argument(
        '--list-snapshots',
        action='store_true',
        help='列出所有快照'
    )
    parser.add_argument(
        '--info',
        action='store_true',
        help='显示工作空间信息'
    )
    parser.add_argument(
        '--list-subskills',
        action='store_true',
        help='列出所有子技能'
    )
    parser.add_argument(
        '--export-config',
        type=str,
        help='导出配置到文件'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='预览模式，不实际执行'
    )
    parser.add_argument(
        '--validate-output-paths',
        action='store_true',
        help='验证输出路径配置'
    )
    parser.add_argument(
        '--check-output-conflicts',
        action='store_true',
        help='检查输出路径冲突'
    )
    parser.add_argument(
        '--list-output-registrations',
        action='store_true',
        help='列出所有输出路径注册'
    )
    
    args = parser.parse_args()
    
    try:
        manager = EnhancedSkillPathManager(
            skill_root=args.skill_root,
            auto_detect=args.skill_root is None
        )
        
        if args.init:
            result = manager.initialize_workspace(dry_run=args.dry_run)
            print(json.dumps(result, indent=2, ensure_ascii=False))
        
        if args.validate:
            result = manager.validate_workspace()
            print(json.dumps(result, indent=2, ensure_ascii=False))
        
        if args.health_check:
            report = manager.health_checker.perform_health_check()
            print(json.dumps(asdict(report), indent=2, ensure_ascii=False))
        
        if args.snapshot:
            snapshot = manager.create_snapshot()
            print(f"快照已创建: {snapshot.snapshot_id}")
            print(json.dumps(asdict(snapshot), indent=2, ensure_ascii=False))
        
        if args.list_snapshots:
            snapshots = manager.snapshot_manager.list_snapshots()
            print(json.dumps(snapshots, indent=2, ensure_ascii=False))
        
        if args.info:
            info = manager.get_workspace_info()
            print(json.dumps(info, indent=2, ensure_ascii=False))
        
        if args.list_subskills:
            subskills = manager.get_all_subskills()
            print(json.dumps([s.to_dict() for s in subskills], indent=2, ensure_ascii=False))
        
        if args.export_config:
            manager.export_config(args.export_config)
            print(f"配置已导出到: {args.export_config}")
        
        if args.validate_output_paths:
            result = manager.validate_output_paths()
            print(json.dumps(result, indent=2, ensure_ascii=False))
        
        if args.check_output_conflicts:
            conflicts = manager.check_output_path_conflicts()
            if conflicts:
                print(f"发现 {len(conflicts)} 个输出路径冲突:")
                for conflict in conflicts:
                    print(json.dumps(conflict.to_dict(), indent=2, ensure_ascii=False))
            else:
                print("未发现输出路径冲突")
        
        if args.list_output_registrations:
            registrations = manager.get_output_path_registrations()
            if registrations:
                print(f"共有 {len(registrations)} 个输出路径注册:")
                for reg in registrations:
                    print(json.dumps(reg.to_dict(), indent=2, ensure_ascii=False))
            else:
                print("暂无输出路径注册")
        
        if not any([
            args.init, args.validate, args.health_check,
            args.snapshot, args.list_snapshots, args.info,
            args.list_subskills, args.export_config,
            args.validate_output_paths, args.check_output_conflicts,
            args.list_output_registrations
        ]):
            print(f"技能根目录: {manager.skill_root}")
            print(f"子技能数量: {len(manager.get_all_subskills())}")
            print("\n路径配置:")
            for key in PathKey:
                path = manager.resolve_path(key)
                exists = "✓" if path.exists() else "✗"
                print(f"  {exists} {key.value}: {path}")
            
    except PathConfigError as e:
        logger.error(f"配置错误: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"执行失败: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
