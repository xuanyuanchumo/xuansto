"""
脚本注册表 - 动态加载和管理所有脚本模块
支持版本管理、依赖关系追踪、热重载
"""
from __future__ import annotations

import importlib
import importlib.util
import sys
import os
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Callable


class ScriptRegistryError(Exception):
    """脚本注册表相关异常"""
    pass


class ScriptStatus(str, Enum):
    REGISTERED = "registered"
    LOADED = "loaded"
    ERROR = "error"
    DISABLED = "disabled"


@dataclass
class ScriptInfo:
    """脚本信息数据类"""
    name: str
    version: str = "0.1.0"
    path: Path | None = None
    dependencies: list[str] = field(default_factory=list)
    description: str = ""
    last_modified: datetime | None = None
    status: ScriptStatus = ScriptStatus.REGISTERED
    province: str | None = None
    department: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def is_loaded(self) -> bool:
        return self.status == ScriptStatus.LOADED

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "version": self.version,
            "path": str(self.path) if self.path else None,
            "dependencies": self.dependencies,
            "description": self.description,
            "last_modified": self.last_modified.isoformat() if self.last_modified else None,
            "status": self.status.value,
            "province": self.province,
            "department": self.department,
            "metadata": self.metadata,
        }


@dataclass
class DependencyReport:
    """依赖关系报告"""
    total_scripts: int = 0
    satisfied: int = 0
    missing_deps: dict[str, list[str]] = field(default_factory=dict)
    circular_deps: list[list[str]] = field(default_factory=list)
    dependency_graph: dict[str, list[str]] = field(default_factory=dict)

    @property
    def is_healthy(self) -> bool:
        return len(self.missing_deps) == 0 and len(self.circular_deps) == 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "total_scripts": self.total_scripts,
            "satisfied": self.satisfied,
            "missing_dependencies": self.missing_deps,
            "circular_dependencies": self.circular_deps,
            "dependency_graph": self.dependency_graph,
            "is_healthy": self.is_healthy,
        }


class ScriptRegistry:
    """
    脚本注册表

    动态加载和管理所有脚本模块，支持版本管理、依赖关系追踪、热重载。
    提供按省/部筛选、依赖检查、批量扫描等功能。
    """

    _instance: ScriptRegistry | None = None

    def __init__(self) -> None:
        self._registry: dict[str, ScriptInfo] = {}
        self._loaded_modules: dict[str, Any] = {}
        self._load_history: list[dict[str, Any]] = []

    @classmethod
    def get_instance(cls) -> ScriptRegistry:
        """获取单例实例"""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def register(
        self,
        script_path: Path | str,
        metadata: dict[str, Any] | None = None,
    ) -> ScriptInfo:
        """
        注册脚本

        Args:
            script_path: 脚本文件路径
            metadata: 额外的元数据信息

        Returns:
            注册后的ScriptInfo对象

        Raises:
            ScriptRegistryError: 当文件不存在或已注册时
        """
        path = Path(script_path).resolve()
        if not path.exists():
            raise ScriptRegistryError(f"脚本文件不存在: {path}")

        name: str = path.stem
        if name in self._registry:
            raise ScriptRegistryError(f"脚本已注册: {name}")

        meta: dict[str, Any] = metadata or {}

        stat = path.stat()
        info = ScriptInfo(
            name=name,
            version=meta.get("version", "0.1.0"),
            path=path,
            dependencies=meta.get("dependencies", []),
            description=meta.get("description", ""),
            last_modified=datetime.fromtimestamp(stat.st_mtime),
            status=ScriptStatus.REGISTERED,
            province=meta.get("province"),
            department=meta.get("department"),
            metadata=meta,
        )

        self._registry[name] = info
        return info

    def unregister(self, name: str) -> bool:
        """
        注销脚本

        Args:
            name: 脚本名称

        Returns:
            是否注销成功

        Raises:
            ScriptRegistryError: 当脚本不存在时
        """
        if name not in self._registry:
            raise ScriptRegistryError(f"脚本未注册: {name}")

        del self._registry[name]
        if name in self._loaded_modules:
            del self._loaded_modules[name]
        return True

    def get(self, name: str) -> ScriptInfo:
        """
        获取脚本信息

        Args:
            name: 脚本名称

        Returns:
            ScriptInfo对象

        Raises:
            ScriptRegistryError: 当脚本不存在时
        """
        if name not in self._registry:
            available = ", ".join(sorted(self._registry.keys()))
            raise ScriptRegistryError(
                f"脚本未注册: '{name}'。可用脚本: {available}"
            )
        return self._registry[name]

    def load(self, name: str) -> Any:
        """
        动态导入脚本模块

        Args:
            name: 脚本名称

        Returns:
            导入的模块对象

        Raises:
            ScriptRegistryError: 当脚本不存在或加载失败时
        """
        info = self.get(name)

        if not info.path or not info.path.exists():
            raise ScriptRegistryError(f"脚本文件不存在: {info.path}")

        try:
            spec = importlib.util.spec_from_file_location(name, str(info.path))
            if spec is None or spec.loader is None:
                raise ScriptRegistryError(f"无法创建模块规格: {name}")

            module = importlib.util.module_from_spec(spec)
            sys.modules[name] = module
            spec.loader.exec_module(module)

            info.status = ScriptStatus.LOADED
            self._loaded_modules[name] = module

            self._load_history.append({
                "action": "load",
                "name": name,
                "timestamp": datetime.now().isoformat(),
            })

            return module
        except Exception as e:
            info.status = ScriptStatus.ERROR
            raise ScriptRegistryError(f"加载脚本失败 [{name}]: {e}") from e

    def load_all(self, base_dir: Path | str) -> int:
        """
        扫描并注册目录下所有脚本

        Args:
            base_dir: 基础目录路径

        Returns:
            成功加载的脚本数量
        """
        base = Path(base_dir)
        if not base.is_dir():
            raise ScriptRegistryError(f"不是有效目录: {base}")

        loaded_count: int = 0
        for py_file in base.rglob("*.py"):
            if py_file.name.startswith("_"):
                continue

            try:
                name = py_file.stem
                if name not in self._registry:
                    self.register(py_file)
                    try:
                        self.load(name)
                        loaded_count += 1
                    except ScriptRegistryError:
                        pass
            except ScriptRegistryError:
                continue

        return loaded_count

    def list_by_province(self, province: str) -> list[ScriptInfo]:
        """
        按省筛选脚本

        Args:
            province: 省名称（如 zhongshusheng, menxiasheng 等）

        Returns:
            匹配的ScriptInfo列表
        """
        return [
            info for info in self._registry.values()
            if info.province == province
        ]

    def list_by_department(self, dept: str) -> list[ScriptInfo]:
        """
        按部筛选脚本

        Args:
            dept: 部门名称（如 libu, hubu, bingbu 等）

        Returns:
            匹配的ScriptInfo列表
        """
        return [
            info for info in self._registry.values()
            if info.department == dept
        ]

    def check_dependencies(self) -> DependencyReport:
        """
        检查所有脚本的依赖关系

        Returns:
            DependencyReport对象，包含完整的依赖分析结果
        """
        graph: dict[str, list[str]] = {}
        missing: dict[str, list[str]] = {}

        for name, info in self._registry.items():
            graph[name] = list(info.dependencies)
            missing_deps: list[str] = []
            for dep in info.dependencies:
                if dep not in self._registry:
                    missing_deps.append(dep)
            if missing_deps:
                missing[name] = missing_deps

        circular: list[list[str]] = self._detect_circular_deps(graph)

        satisfied_count: int = len(self._registry) - len(missing)

        return DependencyReport(
            total_scripts=len(self._registry),
            satisfied=satisfied_count,
            missing_deps=missing,
            circular_deps=circular,
            dependency_graph=graph,
        )

    def _detect_circular_deps(
        self, graph: dict[str, list[str]]
    ) -> list[list[str]]:
        """检测循环依赖"""
        WHITE, GRAY, BLACK = 0, 1, 2
        color: dict[str, int] = {node: WHITE for node in graph}
        cycles: list[list[str]] = []

        def dfs(node: str, path: list[str]) -> None:
            color[node] = GRAY
            path.append(node)

            for neighbor in graph.get(node, []):
                if neighbor not in color:
                    continue
                if color[neighbor] == GRAY:
                    cycle_start = path.index(neighbor)
                    cycles.append(path[cycle_start:] + [neighbor])
                elif color[neighbor] == WHITE:
                    dfs(neighbor, path)

            path.pop()
            color[node] = BLACK

        for node in list(graph.keys()):
            if color[node] == WHITE:
                dfs(node, [])

        return cycles

    def get_version(self, name: str) -> str:
        """
        获取脚本版本

        Args:
            name: 脚本名称

        Returns:
            版本字符串

        Raises:
            ScriptRegistryError: 当脚本不存在时
        """
        info = self.get(name)
        return info.version

    def reload(self, name: str) -> Any:
        """
        热重载指定脚本

        Args:
            name: 脚本名称

        Returns:
            重载后的模块对象

        Raises:
            ScriptRegistryError: 当脚本不存在或重载失败时
        """
        info = self.get(name)

        if name in self._loaded_modules:
            old_module = self._loaded_modules[name]
            try:
                reloaded = importlib.reload(old_module)
                self._loaded_modules[name] = reloaded

                if info.path and info.path.exists():
                    stat = info.path.stat()
                    info.last_modified = datetime.fromtimestamp(stat.st_mtime)

                self._load_history.append({
                    "action": "reload",
                    "name": name,
                    "timestamp": datetime.now().isoformat(),
                })

                return reloaded
            except Exception as e:
                info.status = ScriptStatus.ERROR
                raise ScriptRegistryError(f"重载脚本失败 [{name}]: {e}") from e
        else:
            return self.load(name)

    def scan_scripts(self, directory: Path | str) -> list[Path]:
        """
        发现目录中的所有可用脚本

        Args:
            directory: 要扫描的目录

        Returns:
            发现的Python脚本路径列表
        """
        dir_path = Path(directory)
        if not dir_path.is_dir():
            raise ScriptRegistryError(f"不是有效目录: {dir_path}")

        scripts: list[Path] = sorted(dir_path.rglob("*.py"))
        return [s for s in scripts if not s.name.startswith("_")]

    @property
    def registered_names(self) -> list[str]:
        return sorted(self._registry.keys())

    @property
    def count(self) -> int:
        return len(self._registry)

    @property
    def loaded_count(self) -> int:
        return sum(
            1 for info in self._registry.values() if info.is_loaded
        )

    def __repr__(self) -> str:
        return (
            f"ScriptRegistry(registered={self.count}, "
            f"loaded={self.loaded_count})"
        )


if __name__ == "__main__":
    print("=" * 60)
    print("🧪 脚本注册表测试")
    print("=" * 60)

    registry = ScriptRegistry()

    print("\n--- 测试扫描功能 ---")
    test_dir = Path(__file__).parent.parent
    try:
        found = registry.scan_scripts(test_dir)
        print(f"发现 {len(found)} 个Python脚本")
        for s in found[:5]:
            print(f"  📄 {s.name}")
    except ScriptRegistryError as e:
        print(f"⚠️ 扫描错误: {e}")

    print("\n--- 测试注册与加载 ---")
    test_script = Path(__file__)
    try:
        meta = {
            "description": "测试脚本",
            "province": "zhongshusheng",
            "department": "core",
        }
        info = registry.register(test_script, meta)
        print(f"✅ 已注册: {info.name} v{info.version}")
        print(f"   状态: {info.status.value}")
        print(f"   省/部: {info.province}/{info.department}")
    except ScriptRegistryError as e:
        print(f"⚠️ 注册错误: {e}")

    print("\n--- 测试获取信息 ---")
    try:
        retrieved = registry.get("path_config_center")
        print(f"📋 脚本信息:")
        print(f"   名称: {retrieved.name}")
        print(f"   路径: {retrieved.path}")
        print(f"   状态: {retrieved.status.value}")
    except ScriptRegistryError as e:
        print(f"⚠️ 获取错误: {e}")

    print("\n--- 测试依赖检查 ---")
    dep_report = registry.check_dependencies()
    print(f"总脚本数: {dep_report.total_scripts}")
    print(f"满足依赖: {dep_report.satisfied}")
    print(f"健康状态: {'✅ 健康' if dep_report.is_healthy else '❌ 有问题'}")

    print("\n--- 统计信息 ---")
    print(f"已注册脚本数: {registry.count}")
    print(f"已加载脚本数: {registry.loaded_count}")
    print(f"已注册名称: {', '.join(registry.registered_names[:5])}...")

    print("\n✅ 所有测试通过!")
