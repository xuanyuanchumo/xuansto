#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
统一脚本调用入口 - Unified Script Entry Point
提供统一的脚本调用接口，支持从skillscripts、backend/scripts、frontend/scripts调用脚本
实现脚本调用的标准化和可追溯性

功能:
1. 统一脚本发现和加载机制
2. 脚本调用链追踪
3. 脚本执行状态管理
4. 错误处理和恢复
5. 脚本注册机制
6. 脚本调用日志
7. 脚本依赖管理
8. 脚本自动发现与缓存
9. 依赖解析与循环检测
10. 执行性能统计与错误追踪
"""

import ast
import functools
import hashlib
import importlib.util
import json
import logging
import os
import sys
import threading
import time
import traceback
from collections import defaultdict, deque
from concurrent.futures import ThreadPoolExecutor, Future, as_completed
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import (
    Any,
    Callable,
    Dict,
    Generator,
    List,
    Optional,
    Set,
    Tuple,
    Type,
    Union,
)

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class ScriptSource(Enum):
    SKILLSCRIPTS = "skillscripts"
    BACKEND = "backend/scripts"
    FRONTEND = "frontend/scripts"
    UNKNOWN = "unknown"


class ScriptStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    TIMEOUT = "timeout"
    SKIPPED = "skipped"


class ScriptPriority(Enum):
    CRITICAL = 0
    HIGH = 1
    NORMAL = 2
    LOW = 3


@dataclass
class ScriptMetadata:
    name: str
    path: str
    source: ScriptSource
    category: str
    description: str = ""
    version: str = "1.0.0"
    author: str = ""
    dependencies: List[str] = field(default_factory=list)
    entry_points: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    registered_at: str = ""
    last_executed: str = ""
    execution_count: int = 0
    file_hash: str = ""
    file_size: int = 0
    last_modified: str = ""


@dataclass
class ScriptExecution:
    execution_id: str
    script_name: str
    script_path: str
    status: ScriptStatus
    start_time: str
    end_time: str = ""
    duration_ms: int = 0
    arguments: Dict[str, Any] = field(default_factory=dict)
    result: Any = None
    error: str = ""
    error_traceback: str = ""
    call_chain: List[str] = field(default_factory=list)
    log_file: str = ""
    memory_usage_mb: float = 0.0
    cpu_time_ms: int = 0


@dataclass
class ScriptRegistry:
    scripts: Dict[str, ScriptMetadata] = field(default_factory=dict)
    categories: Dict[str, List[str]] = field(default_factory=lambda: defaultdict(list))
    last_updated: str = ""
    dependency_graph: Dict[str, List[str]] = field(default_factory=dict)


@dataclass
class ScriptLog:
    log_id: str
    script_name: str
    execution_id: str
    timestamp: str
    level: str
    message: str
    details: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PerformanceStats:
    total_executions: int = 0
    successful_executions: int = 0
    failed_executions: int = 0
    total_duration_ms: int = 0
    avg_duration_ms: float = 0.0
    max_duration_ms: int = 0
    min_duration_ms: int = 0
    total_memory_mb: float = 0.0
    avg_memory_mb: float = 0.0
    error_count_by_type: Dict[str, int] = field(default_factory=lambda: defaultdict(int))
    execution_times: List[int] = field(default_factory=list)


@dataclass
class DependencyNode:
    script_name: str
    dependencies: Set[str] = field(default_factory=set)
    dependents: Set[str] = field(default_factory=set)
    depth: int = 0
    is_circular: bool = False


class ScriptDiscovery:
    """
    脚本自动发现类
    
    负责扫描脚本目录、提取脚本元数据和管理脚本缓存
    """
    
    CACHE_VERSION = "1.0"
    CACHE_EXPIRY_SECONDS = 3600
    
    CATEGORY_MAPPING = {
        "analysis": ["analyzer", "analysis", "check", "detect", "validate", "locator", "issue"],
        "optimization": ["fixer", "optimizer", "optimization", "fix", "refactor", "enhance"],
        "test": ["test", "spec", "coverage", "benchmark"],
        "pipeline": ["pipeline", "generator", "doc", "sdd", "tdd"],
        "core": ["manager", "coordinator", "checker", "init", "health", "service"],
        "utils": ["utils", "helper", "history", "tracker", "version"],
        "requirements": ["requirement", "rule", "trace", "business"],
        "monitoring": ["monitor", "tracker", "benchmark", "performance"],
    }
    
    SCRIPT_ALIASES = {
        "log_analyzer": ["log_analyzer", "analyze_log", "log_analysis"],
        "auto_fixer": ["auto_fixer", "auto_fix", "fixer", "fix_code"],
        "issue_locator": ["issue_locator", "locate_issue", "problem_locator"],
        "error_handler": ["error_handler", "handle_error", "error_handling"],
        "coverage_monitor": ["coverage_monitor", "coverage_analyzer", "test_coverage"],
        "architecture_check": ["architecture_check", "check_architecture", "arch_check"],
        "code_smell_detector": ["code_smell_detector", "detect_smell", "smell_detector"],
        "performance_benchmark": ["performance_benchmark", "benchmark", "perf_test"],
        "security_scanner": ["security_scanner", "security_check", "scan_security"],
        "self_iteration": ["self_iteration", "iterate", "auto_iteration"],
        "tech_debt_tracker": ["tech_debt_tracker", "debt_tracker", "track_debt"],
    }
    
    def __init__(self, base_path: Path, cache_dir: Optional[Path] = None):
        """
        初始化脚本发现器
        
        Args:
            base_path: 基础路径
            cache_dir: 缓存目录，默认为 base_path / "cache" / "script_discovery"
        """
        self.base_path = base_path
        self.cache_dir = cache_dir or (base_path / "cache" / "script_discovery")
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._cache_file = self.cache_dir / "script_cache.json"
        self._metadata_cache: Dict[str, ScriptMetadata] = {}
        self._lock = threading.RLock()
        
        self._load_cache()
    
    def _load_cache(self) -> None:
        """从文件加载缓存"""
        if self._cache_file.exists():
            try:
                with open(self._cache_file, 'r', encoding='utf-8') as f:
                    cache_data = json.load(f)
                    
                if cache_data.get("version") == self.CACHE_VERSION:
                    self._cache = cache_data.get("scripts", {})
                    logger.info(f"已加载 {len(self._cache)} 个脚本缓存")
            except Exception as e:
                logger.warning(f"加载缓存失败: {e}")
                self._cache = {}
    
    def _save_cache(self) -> None:
        """保存缓存到文件"""
        try:
            cache_data = {
                "version": self.CACHE_VERSION,
                "updated_at": datetime.now().isoformat(),
                "scripts": self._cache
            }
            
            with open(self._cache_file, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, ensure_ascii=False, indent=2)
                
            logger.debug(f"已保存 {len(self._cache)} 个脚本缓存")
        except Exception as e:
            logger.warning(f"保存缓存失败: {e}")
    
    def scan_directory(
        self,
        dir_path: Path,
        source: ScriptSource,
        recursive: bool = True,
        force_refresh: bool = False
    ) -> List[ScriptMetadata]:
        """
        扫描目录发现脚本
        
        Args:
            dir_path: 要扫描的目录路径
            source: 脚本来源
            recursive: 是否递归扫描子目录
            force_refresh: 是否强制刷新缓存
            
        Returns:
            发现的脚本元数据列表
        """
        if not dir_path.exists():
            logger.warning(f"目录不存在: {dir_path}")
            return []
        
        discovered_scripts = []
        
        if recursive:
            pattern = dir_path.rglob("*.py")
        else:
            pattern = dir_path.glob("*.py")
        
        for file_path in pattern:
            if self._should_skip_file(file_path):
                continue
            
            metadata = self._get_or_extract_metadata(
                file_path, source, force_refresh
            )
            
            if metadata:
                discovered_scripts.append(metadata)
        
        self._save_cache()
        logger.info(f"从 {dir_path} 发现 {len(discovered_scripts)} 个脚本")
        
        return discovered_scripts
    
    def _should_skip_file(self, file_path: Path) -> bool:
        """判断是否应该跳过该文件"""
        skip_patterns = ['__pycache__', '.git', '.venv', 'venv', 'node_modules']
        skip_names = ['__init__.py', 'setup.py', 'conftest.py']
        
        path_str = str(file_path)
        for pattern in skip_patterns:
            if pattern in path_str:
                return True
        
        if file_path.name in skip_names:
            return True
        
        if file_path.name.startswith('.') or file_path.name.startswith('_'):
            return True
        
        return False
    
    def _get_or_extract_metadata(
        self,
        file_path: Path,
        source: ScriptSource,
        force_refresh: bool = False
    ) -> Optional[ScriptMetadata]:
        """获取或提取脚本元数据（带缓存）"""
        cache_key = str(file_path)
        
        file_stat = file_path.stat()
        current_hash = self._compute_file_hash(file_path)
        current_mtime = datetime.fromtimestamp(file_stat.st_mtime).isoformat()
        
        if not force_refresh and cache_key in self._cache:
            cached = self._cache[cache_key]
            
            if (cached.get("file_hash") == current_hash and
                cached.get("last_modified") == current_mtime):
                
                metadata = self._cache_to_metadata(cached, source)
                self._metadata_cache[cache_key] = metadata
                return metadata
        
        metadata = self._extract_metadata(file_path, source)
        
        if metadata:
            metadata.file_hash = current_hash
            metadata.file_size = file_stat.st_size
            metadata.last_modified = current_mtime
            
            self._cache[cache_key] = self._metadata_to_cache(metadata)
            self._metadata_cache[cache_key] = metadata
        
        return metadata
    
    def _compute_file_hash(self, file_path: Path) -> str:
        """计算文件哈希值"""
        hasher = hashlib.md5()
        
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(8192), b''):
                hasher.update(chunk)
        
        return hasher.hexdigest()
    
    def _extract_metadata(
        self,
        file_path: Path,
        source: ScriptSource
    ) -> Optional[ScriptMetadata]:
        """
        提取脚本元数据
        
        Args:
            file_path: 脚本文件路径
            source: 脚本来源
            
        Returns:
            脚本元数据，提取失败返回 None
        """
        try:
            content = file_path.read_text(encoding='utf-8', errors='ignore')
            
            category = self._detect_category(file_path.name)
            
            description = ""
            version = "1.0.0"
            author = ""
            dependencies = []
            entry_points = []
            tags = []
            
            try:
                tree = ast.parse(content)
                
                docstring = self._extract_docstring(tree)
                if docstring:
                    description = docstring.split('\n')[0][:200]
                
                dependencies = self._extract_imports(tree)
                entry_points = self._extract_entry_points(tree)
                tags = self._extract_tags(tree, content)
                
                version = self._extract_version(tree, content) or version
                author = self._extract_author(tree, content) or author
                
            except SyntaxError:
                pass
            
            name = file_path.stem
            
            return ScriptMetadata(
                name=name,
                path=str(file_path),
                source=source,
                category=category,
                description=description,
                version=version,
                author=author,
                dependencies=dependencies,
                entry_points=entry_points,
                tags=tags,
                registered_at=datetime.now().isoformat()
            )
            
        except Exception as e:
            logger.warning(f"提取脚本元数据失败 {file_path}: {e}")
            return None
    
    def _extract_docstring(self, tree: ast.AST) -> str:
        """提取模块文档字符串"""
        if tree.body and isinstance(tree.body[0], ast.Expr):
            if isinstance(tree.body[0].value, ast.Constant):
                return tree.body[0].value.value or ""
        return ""
    
    def _extract_imports(self, tree: ast.AST) -> List[str]:
        """提取导入依赖"""
        dependencies = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    dependencies.append(alias.name)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    dependencies.append(node.module)
        
        return list(set(dependencies))
    
    def _extract_entry_points(self, tree: ast.AST) -> List[str]:
        """提取入口点函数"""
        entry_points = []
        entry_point_names = ['main', 'run', 'execute', 'start']
        
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                if node.name in entry_point_names:
                    entry_points.append(node.name)
                elif node.name.startswith('run_') or node.name.endswith('_main'):
                    entry_points.append(node.name)
        
        return entry_points
    
    def _extract_tags(self, tree: ast.AST, content: str) -> List[str]:
        """从注释和文档字符串中提取标签"""
        tags = []
        
        tag_patterns = [
            r'@tag[:\s]+(\w+)',
            r'@category[:\s]+(\w+)',
            r'#\s*TAGS?[:\s]+([\w,\s]+)',
        ]
        
        import re
        for pattern in tag_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            for match in matches:
                if ',' in match:
                    tags.extend([t.strip() for t in match.split(',')])
                else:
                    tags.append(match.strip())
        
        return list(set(tags))
    
    def _extract_version(self, tree: ast.AST, content: str) -> Optional[str]:
        """提取版本信息"""
        import re
        
        patterns = [
            r'__version__\s*=\s*["\']([^"\']+)["\']',
            r'VERSION\s*=\s*["\']([^"\']+)["\']',
            r'@version[:\s]+([\d.]+)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, content)
            if match:
                return match.group(1)
        
        return None
    
    def _extract_author(self, tree: ast.AST, content: str) -> Optional[str]:
        """提取作者信息"""
        import re
        
        patterns = [
            r'__author__\s*=\s*["\']([^"\']+)["\']',
            r'AUTHOR\s*=\s*["\']([^"\']+)["\']',
            r'@author[:\s]+(\w+)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, content)
            if match:
                return match.group(1)
        
        return None
    
    def _detect_category(self, filename: str) -> str:
        """根据文件名检测脚本类别"""
        filename_lower = filename.lower()
        
        for category, keywords in self.CATEGORY_MAPPING.items():
            for keyword in keywords:
                if keyword in filename_lower:
                    return category
        
        return "utils"
    
    def _metadata_to_cache(self, metadata: ScriptMetadata) -> Dict[str, Any]:
        """将元数据转换为缓存格式"""
        return {
            "name": metadata.name,
            "path": metadata.path,
            "source": metadata.source.value,
            "category": metadata.category,
            "description": metadata.description,
            "version": metadata.version,
            "author": metadata.author,
            "dependencies": metadata.dependencies,
            "entry_points": metadata.entry_points,
            "tags": metadata.tags,
            "registered_at": metadata.registered_at,
            "file_hash": metadata.file_hash,
            "file_size": metadata.file_size,
            "last_modified": metadata.last_modified,
        }
    
    def _cache_to_metadata(
        self,
        cached: Dict[str, Any],
        source: ScriptSource
    ) -> ScriptMetadata:
        """从缓存数据创建元数据对象"""
        return ScriptMetadata(
            name=cached["name"],
            path=cached["path"],
            source=source,
            category=cached["category"],
            description=cached.get("description", ""),
            version=cached.get("version", "1.0.0"),
            author=cached.get("author", ""),
            dependencies=cached.get("dependencies", []),
            entry_points=cached.get("entry_points", []),
            tags=cached.get("tags", []),
            registered_at=cached.get("registered_at", ""),
            file_hash=cached.get("file_hash", ""),
            file_size=cached.get("file_size", 0),
            last_modified=cached.get("last_modified", ""),
        )
    
    def get_script_by_alias(self, alias: str) -> Optional[str]:
        """通过别名获取脚本名称"""
        alias_lower = alias.lower()
        
        for canonical, aliases in self.SCRIPT_ALIASES.items():
            if alias_lower in [a.lower() for a in aliases]:
                return canonical
        
        return None
    
    def refresh_cache(self) -> None:
        """刷新所有缓存"""
        with self._lock:
            self._cache.clear()
            self._metadata_cache.clear()
            
            if self._cache_file.exists():
                self._cache_file.unlink()
            
            logger.info("脚本缓存已刷新")
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """获取缓存统计信息"""
        return {
            "total_cached": len(self._cache),
            "cache_file": str(self._cache_file),
            "cache_size_bytes": self._cache_file.stat().st_size if self._cache_file.exists() else 0,
        }


class ScriptDependencyResolver:
    """
    脚本依赖解析器
    
    负责构建依赖图、检测循环依赖和排序依赖顺序
    """
    
    def __init__(self, scripts: Dict[str, ScriptMetadata]):
        """
        初始化依赖解析器
        
        Args:
            scripts: 脚本元数据字典
        """
        self.scripts = scripts
        self._dependency_graph: Dict[str, DependencyNode] = {}
        self._topological_order: List[str] = []
        self._circular_dependencies: List[List[str]] = []
        self._lock = threading.RLock()
        
        self._build_graph()
    
    def _build_graph(self) -> None:
        """构建依赖图"""
        for script_name, metadata in self.scripts.items():
            node = DependencyNode(script_name=script_name)
            
            for dep in metadata.dependencies:
                normalized_dep = self._normalize_dependency(dep)
                
                if normalized_dep and normalized_dep in self.scripts:
                    node.dependencies.add(normalized_dep)
            
            self._dependency_graph[script_name] = node
        
        for script_name, node in self._dependency_graph.items():
            for dep in node.dependencies:
                if dep in self._dependency_graph:
                    self._dependency_graph[dep].dependents.add(script_name)
        
        self._calculate_depths()
        self._detect_circular_dependencies()
        self._compute_topological_order()
        
        logger.info(f"依赖图构建完成: {len(self._dependency_graph)} 个节点, "
                   f"{len(self._circular_dependencies)} 个循环依赖")
    
    def _normalize_dependency(self, dep: str) -> Optional[str]:
        """标准化依赖名称"""
        if dep in self.scripts:
            return dep
        
        for script_name in self.scripts:
            if dep in script_name or script_name in dep:
                return script_name
        
        dep_lower = dep.lower().replace('-', '_')
        for script_name in self.scripts:
            if dep_lower in script_name.lower():
                return script_name
        
        return None
    
    def _calculate_depths(self) -> None:
        """计算每个节点的依赖深度"""
        visited = set()
        
        def get_depth(node_name: str, path: Set[str]) -> int:
            if node_name in path:
                return 0
            
            if node_name in visited:
                return self._dependency_graph[node_name].depth
            
            node = self._dependency_graph.get(node_name)
            if not node or not node.dependencies:
                node.depth = 0
                visited.add(node_name)
                return 0
            
            path.add(node_name)
            max_dep_depth = 0
            
            for dep in node.dependencies:
                dep_depth = get_depth(dep, path.copy())
                max_dep_depth = max(max_dep_depth, dep_depth + 1)
            
            node.depth = max_dep_depth
            visited.add(node_name)
            return node.depth
        
        for script_name in self._dependency_graph:
            get_depth(script_name, set())
    
    def _detect_circular_dependencies(self) -> None:
        """检测循环依赖"""
        WHITE, GRAY, BLACK = 0, 1, 2
        colors = {name: WHITE for name in self._dependency_graph}
        
        def dfs(node: str, path: List[str]) -> Optional[List[str]]:
            colors[node] = GRAY
            path.append(node)
            
            for dep in self._dependency_graph[node].dependencies:
                if colors[dep] == GRAY:
                    if dep in path:
                        cycle_start = path.index(dep)
                        cycle = path[cycle_start:] + [dep]
                        return cycle
                    else:
                        colors[node] = BLACK
                        return None
                
                if colors[dep] == WHITE:
                    result = dfs(dep, path)
                    if result:
                        return result
            
            path.pop()
            colors[node] = BLACK
            return None
        
        visited_cycles = set()
        
        for node in self._dependency_graph:
            if colors[node] == WHITE:
                cycle = dfs(node, [])
                if cycle:
                    cycle_key = tuple(sorted(cycle))
                    if cycle_key not in visited_cycles:
                        self._circular_dependencies.append(cycle)
                        visited_cycles.add(cycle_key)
                        
                        for script_name in cycle[:-1]:
                            self._dependency_graph[script_name].is_circular = True
    
    def _compute_topological_order(self) -> None:
        """计算拓扑排序"""
        in_degree = {name: 0 for name in self._dependency_graph}
        
        for node in self._dependency_graph.values():
            for dep in node.dependencies:
                if dep in in_degree:
                    in_degree[node.script_name] += 1
        
        queue = deque([name for name, degree in in_degree.items() if degree == 0])
        result = []
        
        while queue:
            current = queue.popleft()
            result.append(current)
            
            for dependent in self._dependency_graph[current].dependents:
                in_degree[dependent] -= 1
                if in_degree[dependent] == 0:
                    queue.append(dependent)
        
        self._topological_order = result
    
    def get_dependencies(self, script_name: str, transitive: bool = False) -> List[str]:
        """
        获取脚本的依赖
        
        Args:
            script_name: 脚本名称
            transitive: 是否获取传递依赖
            
        Returns:
            依赖列表
        """
        if script_name not in self._dependency_graph:
            return []
        
        if not transitive:
            return list(self._dependency_graph[script_name].dependencies)
        
        all_deps = set()
        queue = deque(self._dependency_graph[script_name].dependencies)
        
        while queue:
            dep = queue.popleft()
            if dep not in all_deps and dep in self._dependency_graph:
                all_deps.add(dep)
                queue.extend(self._dependency_graph[dep].dependencies)
        
        return list(all_deps)
    
    def get_dependents(self, script_name: str) -> List[str]:
        """获取依赖此脚本的其他脚本"""
        if script_name not in self._dependency_graph:
            return []
        
        return list(self._dependency_graph[script_name].dependents)
    
    def get_execution_order(self, script_names: List[str]) -> List[str]:
        """
        获取脚本的执行顺序（按依赖关系排序）
        
        Args:
            script_names: 要执行的脚本列表
            
        Returns:
            排序后的脚本列表
        """
        needed = set()
        
        for name in script_names:
            needed.add(name)
            needed.update(self.get_dependencies(name, transitive=True))
        
        ordered = [name for name in self._topological_order if name in needed]
        
        return ordered
    
    def has_circular_dependencies(self) -> bool:
        """检查是否存在循环依赖"""
        return len(self._circular_dependencies) > 0
    
    def get_circular_dependencies(self) -> List[List[str]]:
        """获取所有循环依赖"""
        return self._circular_dependencies.copy()
    
    def can_execute(self, script_name: str) -> Tuple[bool, str]:
        """
        检查脚本是否可以执行
        
        Args:
            script_name: 脚本名称
            
        Returns:
            (是否可执行, 原因消息)
        """
        if script_name not in self._dependency_graph:
            return True, "脚本不在依赖图中"
        
        node = self._dependency_graph[script_name]
        
        if node.is_circular:
            return False, f"脚本存在循环依赖: {script_name}"
        
        missing_deps = []
        for dep in node.dependencies:
            if dep not in self.scripts:
                missing_deps.append(dep)
        
        if missing_deps:
            return False, f"缺少依赖: {', '.join(missing_deps)}"
        
        return True, "依赖检查通过"
    
    def get_dependency_graph(self) -> Dict[str, List[str]]:
        """获取依赖图（简化格式）"""
        return {
            name: list(node.dependencies)
            for name, node in self._dependency_graph.items()
        }
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取依赖统计信息"""
        total_deps = sum(len(node.dependencies) for node in self._dependency_graph.values())
        avg_deps = total_deps / len(self._dependency_graph) if self._dependency_graph else 0
        
        max_depth_node = max(
            self._dependency_graph.values(),
            key=lambda n: n.depth,
            default=None
        )
        
        return {
            "total_scripts": len(self._dependency_graph),
            "total_dependencies": total_deps,
            "average_dependencies": round(avg_deps, 2),
            "max_dependency_depth": max_depth_node.depth if max_depth_node else 0,
            "circular_dependencies_count": len(self._circular_dependencies),
            "scripts_with_most_dependencies": self._get_top_dependencies(),
        }
    
    def _get_top_dependencies(self, limit: int = 5) -> List[Tuple[str, int]]:
        """获取依赖最多的脚本"""
        sorted_nodes = sorted(
            self._dependency_graph.values(),
            key=lambda n: len(n.dependencies),
            reverse=True
        )
        
        return [(n.script_name, len(n.dependencies)) for n in sorted_nodes[:limit]]


class ScriptExecutionLogger:
    """
    脚本执行日志记录器
    
    负责记录执行日志、统计性能和追踪错误
    """
    
    MAX_HISTORY_SIZE = 10000
    MAX_LOG_SIZE = 100000
    
    def __init__(self, log_dir: Path):
        """
        初始化执行日志记录器
        
        Args:
            log_dir: 日志目录
        """
        self.log_dir = log_dir
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        self._execution_history: List[ScriptExecution] = []
        self._logs: List[ScriptLog] = []
        self._performance_stats: Dict[str, PerformanceStats] = defaultdict(PerformanceStats)
        self._error_tracking: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        self._lock = threading.RLock()
        
        self._setup_file_logging()
    
    def _setup_file_logging(self) -> None:
        """设置文件日志"""
        log_file = self.log_dir / f"execution_{datetime.now().strftime('%Y%m%d')}.log"
        
        self.file_handler = logging.FileHandler(log_file, encoding='utf-8')
        self.file_handler.setLevel(logging.DEBUG)
        self.file_handler.setFormatter(
            logging.Formatter('%(asctime)s - %(levelname)s - [%(name)s] %(message)s')
        )
        logger.addHandler(self.file_handler)
    
    def log_execution_start(
        self,
        execution_id: str,
        script_name: str,
        script_path: str,
        arguments: Dict[str, Any]
    ) -> ScriptExecution:
        """
        记录执行开始
        
        Args:
            execution_id: 执行ID
            script_name: 脚本名称
            script_path: 脚本路径
            arguments: 执行参数
            
        Returns:
            执行记录对象
        """
        execution = ScriptExecution(
            execution_id=execution_id,
            script_name=script_name,
            script_path=script_path,
            status=ScriptStatus.RUNNING,
            start_time=datetime.now().isoformat(),
            arguments=arguments,
        )
        
        with self._lock:
            self._execution_history.append(execution)
            self._trim_history()
        
        self._add_log(
            script_name=script_name,
            execution_id=execution_id,
            level="start",
            message=f"开始执行脚本: {script_name}",
            details={"arguments": arguments}
        )
        
        return execution
    
    def log_execution_end(
        self,
        execution: ScriptExecution,
        success: bool,
        result: Any = None,
        error: Optional[Exception] = None
    ) -> None:
        """
        记录执行结束
        
        Args:
            execution: 执行记录对象
            success: 是否成功
            result: 执行结果
            error: 错误信息
        """
        end_time = datetime.now()
        execution.end_time = end_time.isoformat()
        
        start_dt = datetime.fromisoformat(execution.start_time)
        execution.duration_ms = int((end_time - start_dt).total_seconds() * 1000)
        
        if success:
            execution.status = ScriptStatus.SUCCESS
            execution.result = result
            
            self._update_performance_stats(execution)
            
            self._add_log(
                script_name=execution.script_name,
                execution_id=execution.execution_id,
                level="success",
                message=f"脚本执行成功: {execution.script_name}",
                details={"duration_ms": execution.duration_ms}
            )
        else:
            execution.status = ScriptStatus.FAILED
            execution.error = str(error) if error else "未知错误"
            execution.error_traceback = traceback.format_exc() if error else ""
            
            self._update_error_tracking(execution, error)
            
            self._add_log(
                script_name=execution.script_name,
                execution_id=execution.execution_id,
                level="error",
                message=f"脚本执行失败: {execution.script_name}",
                details={
                    "error": execution.error,
                    "duration_ms": execution.duration_ms
                }
            )
    
    def _update_performance_stats(self, execution: ScriptExecution) -> None:
        """更新性能统计"""
        stats = self._performance_stats[execution.script_name]
        
        stats.total_executions += 1
        stats.successful_executions += 1
        stats.total_duration_ms += execution.duration_ms
        stats.execution_times.append(execution.duration_ms)
        
        if stats.max_duration_ms == 0 or execution.duration_ms > stats.max_duration_ms:
            stats.max_duration_ms = execution.duration_ms
        
        if stats.min_duration_ms == 0 or execution.duration_ms < stats.min_duration_ms:
            stats.min_duration_ms = execution.duration_ms
        
        stats.avg_duration_ms = stats.total_duration_ms / stats.successful_executions
    
    def _update_error_tracking(
        self,
        execution: ScriptExecution,
        error: Optional[Exception]
    ) -> None:
        """更新错误追踪"""
        error_type = type(error).__name__ if error else "UnknownError"
        
        stats = self._performance_stats[execution.script_name]
        stats.total_executions += 1
        stats.failed_executions += 1
        stats.error_count_by_type[error_type] += 1
        
        error_record = {
            "execution_id": execution.execution_id,
            "timestamp": execution.end_time,
            "error_type": error_type,
            "error_message": str(error) if error else "",
            "traceback": execution.error_traceback,
            "script_name": execution.script_name,
        }
        
        self._error_tracking[error_type].append(error_record)
        
        if len(self._error_tracking[error_type]) > 100:
            self._error_tracking[error_type] = self._error_tracking[error_type][-100:]
    
    def _add_log(
        self,
        script_name: str,
        execution_id: str,
        level: str,
        message: str,
        details: Optional[Dict[str, Any]] = None
    ) -> None:
        """添加日志记录"""
        log_id = hashlib.md5(
            f"{script_name}{execution_id}{datetime.now().isoformat()}".encode()
        ).hexdigest()[:12]
        
        log_entry = ScriptLog(
            log_id=log_id,
            script_name=script_name,
            execution_id=execution_id,
            timestamp=datetime.now().isoformat(),
            level=level,
            message=message,
            details=details or {}
        )
        
        with self._lock:
            self._logs.append(log_entry)
            
            if len(self._logs) > self.MAX_LOG_SIZE:
                self._logs = self._logs[-self.MAX_LOG_SIZE:]
    
    def _trim_history(self) -> None:
        """修剪历史记录"""
        if len(self._execution_history) > self.MAX_HISTORY_SIZE:
            self._execution_history = self._execution_history[-self.MAX_HISTORY_SIZE:]
    
    def get_execution_history(
        self,
        script_name: Optional[str] = None,
        status: Optional[ScriptStatus] = None,
        limit: int = 100
    ) -> List[ScriptExecution]:
        """
        获取执行历史
        
        Args:
            script_name: 按脚本名称过滤
            status: 按状态过滤
            limit: 返回数量限制
            
        Returns:
            执行历史列表
        """
        with self._lock:
            history = self._execution_history.copy()
        
        if script_name:
            history = [e for e in history if e.script_name == script_name]
        
        if status:
            history = [e for e in history if e.status == status]
        
        return history[-limit:]
    
    def get_performance_stats(self, script_name: Optional[str] = None) -> Dict[str, Any]:
        """
        获取性能统计
        
        Args:
            script_name: 脚本名称，为空则返回所有统计
            
        Returns:
            性能统计数据
        """
        if script_name:
            if script_name in self._performance_stats:
                return asdict(self._performance_stats[script_name])
            return {}
        
        return {
            name: asdict(stats)
            for name, stats in self._performance_stats.items()
        }
    
    def get_error_report(
        self,
        error_type: Optional[str] = None,
        limit: int = 50
    ) -> Dict[str, Any]:
        """
        获取错误报告
        
        Args:
            error_type: 错误类型过滤
            limit: 每种错误类型的记录限制
            
        Returns:
            错误报告
        """
        if error_type:
            errors = self._error_tracking.get(error_type, [])[:limit]
            return {
                "error_type": error_type,
                "count": len(self._error_tracking.get(error_type, [])),
                "recent_errors": errors,
            }
        
        return {
            "error_types": list(self._error_tracking.keys()),
            "total_error_count": sum(len(v) for v in self._error_tracking.values()),
            "errors_by_type": {
                k: v[:limit] for k, v in self._error_tracking.items()
            },
        }
    
    def get_logs(
        self,
        script_name: Optional[str] = None,
        level: Optional[str] = None,
        limit: int = 100
    ) -> List[ScriptLog]:
        """
        获取日志记录
        
        Args:
            script_name: 按脚本名称过滤
            level: 按日志级别过滤
            limit: 返回数量限制
            
        Returns:
            日志记录列表
        """
        with self._lock:
            logs = self._logs.copy()
        
        if script_name:
            logs = [log for log in logs if log.script_name == script_name]
        
        if level:
            logs = [log for log in logs if log.level == level]
        
        return logs[-limit:]
    
    def export_logs(self, output_path: str, script_name: Optional[str] = None) -> None:
        """
        导出日志到文件
        
        Args:
            output_path: 输出文件路径
            script_name: 脚本名称过滤
        """
        logs = self.get_logs(script_name=script_name, limit=self.MAX_LOG_SIZE)
        
        logs_data = [asdict(log) for log in logs]
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(logs_data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"日志已导出至: {output_path}")
    
    def clear_history(self) -> None:
        """清空历史记录"""
        with self._lock:
            self._execution_history.clear()
            self._logs.clear()
        
        logger.info("执行历史已清空")


class UnifiedScriptEntry:
    
    SKILLSCRIPTS_DIR = "skillscripts"
    BACKEND_SCRIPTS_DIR = "backend/scripts"
    FRONTEND_SCRIPTS_DIR = "frontend/scripts"
    LOG_DIR = "skillscripts/logs/script_executions"
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls, base_path: str = None):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self, base_path: str = None):
        if self._initialized:
            return
            
        self.base_path = Path(base_path or os.getcwd())
        self.registry = ScriptRegistry()
        self.call_chain_stack: List[str] = []
        
        log_dir = self.base_path / self.LOG_DIR
        log_dir.mkdir(parents=True, exist_ok=True)
        
        self.discovery = ScriptDiscovery(self.base_path)
        self.logger = ScriptExecutionLogger(log_dir)
        
        self._executor = ThreadPoolExecutor(max_workers=4, thread_name_prefix="script_exec")
        self._path_manager = None
        
        self._initialize_path_manager()
        self._discover_scripts()
        
        self.resolver = ScriptDependencyResolver(self.registry.scripts)
        
        self.registry.dependency_graph = self.resolver.get_dependency_graph()
        self.registry.last_updated = datetime.now().isoformat()
        
        self._initialized = True
        logger.info(f"统一脚本入口初始化完成，已注册 {len(self.registry.scripts)} 个脚本")
    
    def _initialize_path_manager(self) -> None:
        """初始化路径管理器"""
        try:
            path_manager_path = self.base_path / self.SKILLSCRIPTS_DIR / "utils" / "path_config_manager.py"
            
            if path_manager_path.exists():
                spec = importlib.util.spec_from_file_location(
                    "path_config_manager",
                    str(path_manager_path)
                )
                
                if spec and spec.loader:
                    module = importlib.util.module_from_spec(spec)
                    sys.modules["path_config_manager"] = module
                    spec.loader.exec_module(module)
                    
                    PathConfigManager = getattr(module, 'PathConfigManager', None)
                    if PathConfigManager:
                        self._path_manager = PathConfigManager()
                        logger.info("路径管理器初始化成功")
        except Exception as e:
            logger.warning(f"路径管理器初始化失败: {e}")
    
    def _discover_scripts(self) -> None:
        """发现并注册所有脚本"""
        skillscripts_path = self.base_path / self.SKILLSCRIPTS_DIR
        if skillscripts_path.exists():
            scripts = self.discovery.scan_directory(
                skillscripts_path, ScriptSource.SKILLSCRIPTS
            )
            for script in scripts:
                self.registry.scripts[script.name] = script
                self.registry.categories[script.category].append(script.name)
        
        backend_path = self.base_path / self.BACKEND_SCRIPTS_DIR
        if backend_path.exists():
            scripts = self.discovery.scan_directory(
                backend_path, ScriptSource.BACKEND
            )
            for script in scripts:
                self.registry.scripts[script.name] = script
                self.registry.categories[script.category].append(script.name)
        
        frontend_path = self.base_path / self.FRONTEND_SCRIPTS_DIR
        if frontend_path.exists():
            scripts = self.discovery.scan_directory(
                frontend_path, ScriptSource.FRONTEND
            )
            for script in scripts:
                self.registry.scripts[script.name] = script
                self.registry.categories[script.category].append(script.name)
    
    def get_script(self, name: str) -> Optional[ScriptMetadata]:
        """
        获取脚本信息
        
        Args:
            name: 脚本名称或别名
            
        Returns:
            脚本元数据，未找到返回 None
        """
        if name in self.registry.scripts:
            return self.registry.scripts[name]
        
        canonical_name = self.discovery.get_script_by_alias(name)
        if canonical_name and canonical_name in self.registry.scripts:
            return self.registry.scripts[canonical_name]
        
        for script_name, metadata in self.registry.scripts.items():
            if name.lower() == script_name.lower():
                return metadata
        
        return None
    
    def get_script_info(self, name: str) -> Optional[Dict[str, Any]]:
        """
        获取脚本详细信息
        
        Args:
            name: 脚本名称
            
        Returns:
            脚本信息字典
        """
        script = self.get_script(name)
        if not script:
            return None
        
        info = asdict(script)
        
        info["dependencies"] = self.resolver.get_dependencies(name)
        info["dependents"] = self.resolver.get_dependents(name)
        info["performance_stats"] = self.logger.get_performance_stats(name)
        
        can_exec, message = self.resolver.can_execute(name)
        info["can_execute"] = can_exec
        info["execution_check_message"] = message
        
        return info
    
    def execute(
        self,
        script_name: str,
        *args,
        timeout: Optional[float] = None,
        **kwargs
    ) -> ScriptExecution:
        """
        执行单个脚本
        
        Args:
            script_name: 脚本名称
            *args: 位置参数
            timeout: 超时时间（秒）
            **kwargs: 关键字参数
            
        Returns:
            执行记录
        """
        execution_id = self._generate_execution_id()
        
        self.call_chain_stack.append(script_name)
        
        script = self.get_script(script_name)
        if not script:
            execution = ScriptExecution(
                execution_id=execution_id,
                script_name=script_name,
                script_path="",
                status=ScriptStatus.FAILED,
                start_time=datetime.now().isoformat(),
                error=f"脚本 '{script_name}' 未找到",
                call_chain=list(self.call_chain_stack)
            )
            self.call_chain_stack.pop()
            return execution
        
        can_exec, message = self.resolver.can_execute(script_name)
        if not can_exec:
            execution = ScriptExecution(
                execution_id=execution_id,
                script_name=script_name,
                script_path=script.path,
                status=ScriptStatus.FAILED,
                start_time=datetime.now().isoformat(),
                error=f"依赖检查失败: {message}",
                call_chain=list(self.call_chain_stack)
            )
            self.call_chain_stack.pop()
            return execution
        
        execution = self.logger.log_execution_start(
            execution_id=execution_id,
            script_name=script_name,
            script_path=script.path,
            arguments={"args": args, "kwargs": kwargs}
        )
        execution.call_chain = list(self.call_chain_stack)
        
        try:
            result = self._run_script(script, args, kwargs, timeout)
            
            self.logger.log_execution_end(execution, success=True, result=result)
            
            script.execution_count += 1
            script.last_executed = datetime.now().isoformat()
            
        except Exception as e:
            self.logger.log_execution_end(execution, success=False, error=e)
        
        finally:
            self.call_chain_stack.pop()
        
        return execution
    
    def execute_batch(
        self,
        script_names: List[str],
        parallel: bool = False,
        max_workers: int = 4,
        stop_on_failure: bool = False,
        **common_kwargs
    ) -> Dict[str, ScriptExecution]:
        """
        批量执行脚本
        
        Args:
            script_names: 脚本名称列表
            parallel: 是否并行执行
            max_workers: 最大并行工作数
            stop_on_failure: 失败时是否停止
            **common_kwargs: 通用参数
            
        Returns:
            脚本名称到执行记录的映射
        """
        execution_order = self.resolver.get_execution_order(script_names)
        
        results: Dict[str, ScriptExecution] = {}
        
        if parallel:
            independent_scripts = self._get_independent_scripts(execution_order)
            
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                futures: Dict[Future, str] = {}
                
                for script_name in independent_scripts:
                    future = executor.submit(
                        self.execute, script_name, **common_kwargs
                    )
                    futures[future] = script_name
                
                for future in as_completed(futures):
                    script_name = futures[future]
                    try:
                        results[script_name] = future.result()
                    except Exception as e:
                        execution = ScriptExecution(
                            execution_id=self._generate_execution_id(),
                            script_name=script_name,
                            script_path="",
                            status=ScriptStatus.FAILED,
                            start_time=datetime.now().isoformat(),
                            error=str(e),
                        )
                        results[script_name] = execution
                    
                    if stop_on_failure and results[script_name].status == ScriptStatus.FAILED:
                        executor.shutdown(wait=False, cancel_futures=True)
                        break
        else:
            for script_name in execution_order:
                results[script_name] = self.execute(script_name, **common_kwargs)
                
                if stop_on_failure and results[script_name].status == ScriptStatus.FAILED:
                    break
        
        return results
    
    def _get_independent_scripts(self, script_names: List[str]) -> List[str]:
        """获取无相互依赖的脚本列表"""
        independent = []
        
        for name in script_names:
            deps = self.resolver.get_dependencies(name)
            if not any(d in script_names for d in deps):
                independent.append(name)
        
        return independent
    
    def _run_script(
        self,
        script: ScriptMetadata,
        args: tuple,
        kwargs: dict,
        timeout: Optional[float] = None
    ) -> Any:
        """
        运行脚本
        
        Args:
            script: 脚本元数据
            args: 位置参数
            kwargs: 关键字参数
            timeout: 超时时间
            
        Returns:
            脚本执行结果
        """
        spec = importlib.util.spec_from_file_location(script.name, script.path)
        if not spec or not spec.loader:
            raise ImportError(f"无法加载脚本: {script.path}")
        
        module = importlib.util.module_from_spec(spec)
        sys.modules[script.name] = module
        spec.loader.exec_module(module)
        
        entry_func = None
        for entry_point in ['main', 'run', 'execute']:
            if entry_point in script.entry_points:
                entry_func = getattr(module, entry_point, None)
                if callable(entry_func):
                    break
        
        if not entry_func:
            entry_func = getattr(module, 'main', None)
            if not entry_func or not callable(entry_func):
                entry_func = getattr(module, 'run', None)
        
        if not entry_func or not callable(entry_func):
            for attr_name in dir(module):
                if attr_name.startswith('run_') or attr_name.endswith('_main'):
                    func = getattr(module, attr_name)
                    if callable(func):
                        entry_func = func
                        break
        
        if entry_func and callable(entry_func):
            return entry_func(*args, **kwargs)
        
        return module
    
    def _generate_execution_id(self) -> str:
        """生成执行ID"""
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        random_hash = hashlib.md5(str(datetime.now().timestamp()).encode()).hexdigest()[:8]
        return f"EXEC-{timestamp}-{random_hash}"
    
    def register_script(
        self,
        name: str,
        path: str,
        source: ScriptSource = ScriptSource.SKILLSCRIPTS,
        category: Optional[str] = None,
        description: str = "",
        version: str = "1.0.0",
        author: str = "",
        dependencies: Optional[List[str]] = None,
        tags: Optional[List[str]] = None
    ) -> bool:
        """
        注册脚本
        
        Args:
            name: 脚本名称
            path: 脚本路径
            source: 脚本来源
            category: 类别
            description: 描述
            version: 版本
            author: 作者
            dependencies: 依赖列表
            tags: 标签列表
            
        Returns:
            是否注册成功
        """
        if name in self.registry.scripts:
            logger.warning(f"脚本 {name} 已存在，将更新注册信息")
        
        category = category or self.discovery._detect_category(name)
        
        metadata = ScriptMetadata(
            name=name,
            path=path,
            source=source,
            category=category,
            description=description,
            version=version,
            author=author,
            dependencies=dependencies or [],
            tags=tags or [],
            registered_at=datetime.now().isoformat()
        )
        
        self.registry.scripts[name] = metadata
        self.registry.categories[category].append(name)
        
        self.resolver = ScriptDependencyResolver(self.registry.scripts)
        self.registry.dependency_graph = self.resolver.get_dependency_graph()
        
        logger.info(f"脚本 {name} 注册成功，类别: {category}")
        return True
    
    def unregister_script(self, name: str) -> bool:
        """
        注销脚本
        
        Args:
            name: 脚本名称
            
        Returns:
            是否注销成功
        """
        if name not in self.registry.scripts:
            logger.warning(f"脚本 {name} 不存在")
            return False
        
        metadata = self.registry.scripts[name]
        self.registry.categories[metadata.category].remove(name)
        del self.registry.scripts[name]
        
        self.resolver = ScriptDependencyResolver(self.registry.scripts)
        self.registry.dependency_graph = self.resolver.get_dependency_graph()
        
        logger.info(f"脚本 {name} 注销成功")
        return True
    
    def list_scripts(
        self,
        category: Optional[str] = None,
        source: Optional[ScriptSource] = None
    ) -> List[ScriptMetadata]:
        """
        列出脚本
        
        Args:
            category: 按类别过滤
            source: 按来源过滤
            
        Returns:
            脚本元数据列表
        """
        scripts = list(self.registry.scripts.values())
        
        if category:
            scripts = [s for s in scripts if s.category == category]
        
        if source:
            scripts = [s for s in scripts if s.source == source]
        
        return scripts
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        获取统计信息
        
        Returns:
            统计信息字典
        """
        history = self.logger.get_execution_history(limit=10000)
        
        total = len(history)
        if total == 0:
            return {"total_executions": 0}
        
        success = sum(1 for e in history if e.status == ScriptStatus.SUCCESS)
        failed = sum(1 for e in history if e.status == ScriptStatus.FAILED)
        
        durations = [e.duration_ms for e in history if e.duration_ms > 0]
        avg_duration = sum(durations) / len(durations) if durations else 0
        
        script_counts = defaultdict(int)
        for e in history:
            script_counts[e.script_name] += 1
        
        return {
            "total_executions": total,
            "successful": success,
            "failed": failed,
            "success_rate": round(success / total * 100, 2) if total > 0 else 0,
            "average_duration_ms": round(avg_duration, 2),
            "most_used_scripts": sorted(script_counts.items(), key=lambda x: x[1], reverse=True)[:10],
            "dependency_stats": self.resolver.get_statistics(),
            "discovery_stats": self.discovery.get_cache_stats(),
        }
    
    def save_registry(self, output_path: str) -> None:
        """
        保存注册表
        
        Args:
            output_path: 输出文件路径
        """
        registry_data = {
            "last_updated": self.registry.last_updated,
            "scripts": {name: asdict(meta) for name, meta in self.registry.scripts.items()},
            "categories": dict(self.registry.categories),
            "dependency_graph": self.registry.dependency_graph,
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(registry_data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"脚本注册表已保存至: {output_path}")
    
    def get_call_chain(self) -> List[str]:
        """获取当前调用链"""
        return list(self.call_chain_stack)
    
    def get_script_dependencies(self, script_name: str) -> List[str]:
        """获取脚本依赖"""
        return self.resolver.get_dependencies(script_name)
    
    def get_dependent_scripts(self, script_name: str) -> List[str]:
        """获取依赖此脚本的其他脚本"""
        return self.resolver.get_dependents(script_name)
    
    def get_script_logs(
        self,
        script_name: Optional[str] = None,
        level: Optional[str] = None,
        limit: int = 100
    ) -> List[ScriptLog]:
        """获取脚本日志"""
        return self.logger.get_logs(script_name=script_name, level=level, limit=limit)
    
    def export_logs(self, output_path: str, script_name: Optional[str] = None) -> None:
        """导出日志"""
        self.logger.export_logs(output_path, script_name)
    
    def refresh_scripts(self) -> None:
        """刷新脚本发现"""
        self.discovery.refresh_cache()
        self.registry.scripts.clear()
        self.registry.categories.clear()
        self._discover_scripts()
        self.resolver = ScriptDependencyResolver(self.registry.scripts)
        self.registry.dependency_graph = self.resolver.get_dependency_graph()
        logger.info("脚本列表已刷新")


def create_entry(base_path: str = None) -> UnifiedScriptEntry:
    """创建统一脚本入口实例"""
    return UnifiedScriptEntry(base_path)


def execute_script(script_name: str, *args, **kwargs) -> ScriptExecution:
    """执行脚本的便捷函数"""
    entry = UnifiedScriptEntry()
    return entry.execute(script_name, *args, **kwargs)


def get_script_info(script_name: str) -> Optional[Dict[str, Any]]:
    """获取脚本信息的便捷函数"""
    entry = UnifiedScriptEntry()
    return entry.get_script_info(script_name)


def list_available_scripts(category: str = None) -> List[ScriptMetadata]:
    """列出可用脚本的便捷函数"""
    entry = UnifiedScriptEntry()
    return entry.list_scripts(category=category)


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="统一脚本调用入口")
    parser.add_argument("--list", action="store_true", help="列出所有可用脚本")
    parser.add_argument("--category", help="按类别过滤脚本")
    parser.add_argument("--execute", help="执行指定脚本")
    parser.add_argument("--batch", nargs='+', help="批量执行脚本")
    parser.add_argument("--parallel", action="store_true", help="并行执行")
    parser.add_argument("--info", help="获取脚本信息")
    parser.add_argument("--stats", action="store_true", help="显示执行统计")
    parser.add_argument("--save-registry", help="保存脚本注册表到文件")
    parser.add_argument("--register", nargs=2, metavar=("NAME", "PATH"), help="注册新脚本")
    parser.add_argument("--unregister", help="注销脚本")
    parser.add_argument("--dependencies", help="查看脚本依赖")
    parser.add_argument("--dependents", help="查看依赖此脚本的其他脚本")
    parser.add_argument("--logs", action="store_true", help="查看脚本日志")
    parser.add_argument("--export-logs", help="导出日志到文件")
    parser.add_argument("--refresh", action="store_true", help="刷新脚本缓存")
    parser.add_argument("--circular", action="store_true", help="检查循环依赖")
    
    args = parser.parse_args()
    
    entry = UnifiedScriptEntry()
    
    if args.list:
        scripts = entry.list_scripts(category=args.category)
        print(f"\n可用脚本 ({len(scripts)} 个):")
        print("-" * 80)
        for script in scripts:
            print(f"  {script.name:30} [{script.category:12}] ({script.source.value}) - 执行次数: {script.execution_count}")
    
    if args.info:
        info = entry.get_script_info(args.info)
        if info:
            print(f"\n脚本信息: {info['name']}")
            print("-" * 80)
            print(f"  路径: {info['path']}")
            print(f"  来源: {info['source']}")
            print(f"  类别: {info['category']}")
            print(f"  描述: {info['description'][:100]}...")
            print(f"  版本: {info['version']}")
            print(f"  注册时间: {info['registered_at']}")
            print(f"  最后执行: {info['last_executed'] or '未执行'}")
            print(f"  执行次数: {info['execution_count']}")
            print(f"  依赖: {', '.join(info['dependencies'][:5])}")
            print(f"  可执行: {info['can_execute']} - {info['execution_check_message']}")
        else:
            print(f"脚本 '{args.info}' 未找到")
    
    if args.execute:
        result = entry.execute(args.execute)
        print(f"\n执行结果: {result.status.value}")
        print(f"  执行ID: {result.execution_id}")
        print(f"  耗时: {result.duration_ms}ms")
        if result.error:
            print(f"  错误: {result.error}")
    
    if args.batch:
        results = entry.execute_batch(args.batch, parallel=args.parallel)
        print(f"\n批量执行结果:")
        print("-" * 80)
        for name, exec_result in results.items():
            status = "✓" if exec_result.status == ScriptStatus.SUCCESS else "✗"
            print(f"  {status} {name}: {exec_result.status.value} ({exec_result.duration_ms}ms)")
    
    if args.stats:
        stats = entry.get_statistics()
        print("\n执行统计:")
        print("-" * 80)
        for key, value in stats.items():
            print(f"  {key}: {value}")
    
    if args.save_registry:
        entry.save_registry(args.save_registry)
    
    if args.register:
        name, path = args.register
        success = entry.register_script(name, path)
        print(f"注册脚本 {name}: {'成功' if success else '失败'}")
    
    if args.unregister:
        success = entry.unregister_script(args.unregister)
        print(f"注销脚本 {args.unregister}: {'成功' if success else '失败'}")
    
    if args.dependencies:
        deps = entry.get_script_dependencies(args.dependencies)
        print(f"\n脚本 {args.dependencies} 的依赖:")
        if deps:
            for dep in deps:
                print(f"  - {dep}")
        else:
            print("  无依赖")
    
    if args.dependents:
        dependents = entry.get_dependent_scripts(args.dependents)
        print(f"\n依赖 {args.dependents} 的脚本:")
        if dependents:
            for dep in dependents:
                print(f"  - {dep}")
        else:
            print("  无依赖脚本")
    
    if args.logs:
        logs = entry.get_script_logs(limit=20)
        print("\n最近的脚本日志:")
        print("-" * 80)
        for log in logs:
            print(f"  [{log.timestamp}] [{log.level}] {log.script_name}: {log.message}")
    
    if args.export_logs:
        entry.export_logs(args.export_logs)
        print(f"日志已导出至: {args.export_logs}")
    
    if args.refresh:
        entry.refresh_scripts()
        print("脚本缓存已刷新")
    
    if args.circular:
        circular = entry.resolver.get_circular_dependencies()
        if circular:
            print("\n检测到循环依赖:")
            for cycle in circular:
                print(f"  {' -> '.join(cycle)}")
        else:
            print("\n未检测到循环依赖")
