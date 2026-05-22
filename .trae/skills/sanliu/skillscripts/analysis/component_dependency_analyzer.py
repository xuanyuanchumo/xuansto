#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
组件依赖分析器 - Sanliu 技能

提供全面的组件依赖分析功能，包括：
- 组件依赖图构建
- 循环依赖检测
- 组件结构优化建议

使用示例:
    python component_dependency_analyzer.py --path ./src
    python component_dependency_analyzer.py --path ./src --output json --output-file report.json
    python component_dependency_analyzer.py --detect-cycles --path ./src
"""

import ast
import json
import logging
import re
import sys
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple


class ComponentType(Enum):
    """组件类型"""
    MODULE = "module"
    CLASS = "class"
    FUNCTION = "function"
    PACKAGE = "package"
    SERVICE = "service"
    REPOSITORY = "repository"
    CONTROLLER = "controller"
    MODEL = "model"
    VIEW = "view"
    COMPONENT = "component"
    UTILITY = "utility"
    CONFIG = "config"
    INTERFACE = "interface"


class DependencyType(Enum):
    """依赖类型"""
    IMPORT = "import"
    INHERITANCE = "inheritance"
    COMPOSITION = "composition"
    AGGREGATION = "aggregation"
    ASSOCIATION = "association"
    DEPENDENCY = "dependency"
    IMPLEMENTATION = "implementation"
    MIXIN = "mixin"


class CycleSeverity(Enum):
    """循环严重程度"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class CouplingLevel(Enum):
    """耦合级别"""
    TIGHT = "tight"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    NONE = "none"


class ArchitectureLayer(Enum):
    """架构层"""
    PRESENTATION = "presentation"
    BUSINESS = "business"
    DATA = "data"
    INFRASTRUCTURE = "infrastructure"
    CROSS_CUTTING = "cross_cutting"
    UNKNOWN = "unknown"


@dataclass
class ComponentNode:
    """组件节点"""
    name: str
    component_type: ComponentType
    file_path: str
    layer: ArchitectureLayer = ArchitectureLayer.UNKNOWN
    line_number: Optional[int] = None
    description: str = ""
    dependencies: Set[str] = field(default_factory=set)
    dependents: Set[str] = field(default_factory=set)
    metrics: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "type": self.component_type.value,
            "file_path": self.file_path,
            "layer": self.layer.value,
            "line_number": self.line_number,
            "description": self.description,
            "dependencies": list(self.dependencies),
            "dependents": list(self.dependents),
            "metrics": self.metrics
        }


@dataclass
class DependencyEdge:
    """依赖边"""
    source: str
    target: str
    dependency_type: DependencyType
    line_number: Optional[int] = None
    weight: int = 1
    description: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "source": self.source,
            "target": self.target,
            "type": self.dependency_type.value,
            "line_number": self.line_number,
            "weight": self.weight,
            "description": self.description
        }


@dataclass
class CycleInfo:
    """循环依赖信息"""
    cycle_path: List[str]
    severity: CycleSeverity
    involved_components: Set[str]
    description: str
    suggestions: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "cycle_path": self.cycle_path,
            "severity": self.severity.value,
            "involved_components": list(self.involved_components),
            "description": self.description,
            "suggestions": self.suggestions
        }


@dataclass
class CouplingMetrics:
    """耦合度指标"""
    component_name: str
    afferent_coupling: int = 0
    efferent_coupling: int = 0
    instability: float = 0.0
    abstractness: float = 0.0
    distance_from_main: float = 0.0
    coupling_level: CouplingLevel = CouplingLevel.NONE

    def to_dict(self) -> Dict[str, Any]:
        return {
            "component_name": self.component_name,
            "afferent_coupling": self.afferent_coupling,
            "efferent_coupling": self.efferent_coupling,
            "instability": self.instability,
            "abstractness": self.abstractness,
            "distance_from_main": self.distance_from_main,
            "coupling_level": self.coupling_level.value
        }


@dataclass
class LayerMetrics:
    """层级指标"""
    layer: ArchitectureLayer
    component_count: int = 0
    dependency_count: int = 0
    internal_dependencies: int = 0
    external_dependencies: int = 0
    violation_count: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "layer": self.layer.value,
            "component_count": self.component_count,
            "dependency_count": self.dependency_count,
            "internal_dependencies": self.internal_dependencies,
            "external_dependencies": self.external_dependencies,
            "violation_count": self.violation_count
        }


@dataclass
class ComponentGraph:
    """组件依赖图"""
    nodes: Dict[str, ComponentNode] = field(default_factory=dict)
    edges: List[DependencyEdge] = field(default_factory=list)
    adjacency: Dict[str, Set[str]] = field(default_factory=lambda: defaultdict(set))
    reverse_adjacency: Dict[str, Set[str]] = field(default_factory=lambda: defaultdict(set))

    def add_node(self, node: ComponentNode) -> None:
        self.nodes[node.name] = node

    def add_edge(self, edge: DependencyEdge) -> None:
        self.edges.append(edge)
        self.adjacency[edge.source].add(edge.target)
        self.reverse_adjacency[edge.target].add(edge.source)

        if edge.source in self.nodes:
            self.nodes[edge.source].dependencies.add(edge.target)
        if edge.target in self.nodes:
            self.nodes[edge.target].dependents.add(edge.source)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "nodes": {k: v.to_dict() for k, v in self.nodes.items()},
            "edges": [e.to_dict() for e in self.edges],
            "adjacency": {k: list(v) for k, v in self.adjacency.items()}
        }


@dataclass
class OptimizationSuggestion:
    """优化建议"""
    suggestion_type: str
    priority: str
    component: str
    description: str
    impact: str
    implementation: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": self.suggestion_type,
            "priority": self.priority,
            "component": self.component,
            "description": self.description,
            "impact": self.impact,
            "implementation": self.implementation
        }


@dataclass
class ComponentDependencyReport:
    """组件依赖分析报告"""
    timestamp: str
    project_path: str
    graph: ComponentGraph
    cycles: List[CycleInfo]
    coupling_metrics: Dict[str, CouplingMetrics]
    layer_metrics: Dict[str, LayerMetrics]
    summary: Dict[str, Any] = field(default_factory=dict)
    suggestions: List[OptimizationSuggestion] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp,
            "project_path": self.project_path,
            "graph": self.graph.to_dict(),
            "cycles": [c.to_dict() for c in self.cycles],
            "coupling_metrics": {k: v.to_dict() for k, v in self.coupling_metrics.items()},
            "layer_metrics": {k: v.to_dict() for k, v in self.layer_metrics.items()},
            "summary": self.summary,
            "suggestions": [s.to_dict() for s in self.suggestions]
        }


class ComponentIdentifier:
    """组件识别器"""

    LAYER_PATTERNS = {
        ArchitectureLayer.PRESENTATION: [
            r'view', r'views', r'template', r'templates', r'static',
            r'component', r'components', r'page', r'pages', r'ui'
        ],
        ArchitectureLayer.BUSINESS: [
            r'service', r'services', r'business', r'logic', r'manager',
            r'handler', r'handlers', r'processor', r'processors'
        ],
        ArchitectureLayer.DATA: [
            r'model', r'models', r'repository', r'repositories',
            r'entity', r'entities', r'dao', r'data', r'schema'
        ],
        ArchitectureLayer.INFRASTRUCTURE: [
            r'config', r'configs', r'db', r'database', r'cache',
            r'queue', r'util', r'utils', r'helper', r'helpers'
        ],
        ArchitectureLayer.CROSS_CUTTING: [
            r'middleware', r'interceptor', r'aspect', r'logging',
            r'security', r'auth', r'common'
        ]
    }

    TYPE_PATTERNS = {
        ComponentType.CONTROLLER: [r'controller', r'controllers', r'api', r'endpoint'],
        ComponentType.SERVICE: [r'service', r'services', r'manager'],
        ComponentType.REPOSITORY: [r'repository', r'repositories', r'dao', r'repo'],
        ComponentType.MODEL: [r'model', r'models', r'entity', r'entities', r'schema'],
        ComponentType.VIEW: [r'view', r'views', r'template', r'page'],
        ComponentType.COMPONENT: [r'component', r'components'],
        ComponentType.UTILITY: [r'util', r'utils', r'helper', r'helpers', r'common'],
        ComponentType.CONFIG: [r'config', r'configs', r'setting', r'settings'],
        ComponentType.INTERFACE: [r'interface', r'interfaces', r'abstract', r'base'],
    }

    def __init__(self, logger: logging.Logger):
        self.logger = logger
        self._compiled_layer_patterns: Dict[ArchitectureLayer, List[re.Pattern]] = {}
        self._compiled_type_patterns: Dict[ComponentType, List[re.Pattern]] = {}

    def identify_layer(self, file_path: Path, class_name: str = "") -> ArchitectureLayer:
        """识别架构层"""
        path_str = str(file_path).lower()
        name_str = class_name.lower()

        for layer, patterns in self.LAYER_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, path_str) or re.search(pattern, name_str):
                    return layer

        return ArchitectureLayer.UNKNOWN

    def identify_type(self, file_path: Path, class_name: str = "") -> ComponentType:
        """识别组件类型"""
        path_str = str(file_path).lower()
        name_str = class_name.lower()

        for comp_type, patterns in self.TYPE_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, path_str) or re.search(pattern, name_str):
                    return comp_type

        return ComponentType.CLASS


class ComponentGraphBuilder:
    """组件依赖图构建器"""

    STANDARD_LIBRARY = {
        'os', 'sys', 're', 'json', 'logging', 'datetime', 'pathlib', 'typing',
        'collections', 'itertools', 'functools', 'abc', 'dataclasses', 'enum',
        'io', 'time', 'math', 'random', 'string', 'copy', 'pickle', 'shutil',
        'tempfile', 'argparse', 'configparser', 'hashlib', 'hmac', 'secrets',
        'threading', 'multiprocessing', 'asyncio', 'concurrent', 'queue',
        'socket', 'ssl', 'http', 'urllib', 'email', 'html', 'xml', 'csv',
        'sqlite3', 'unittest', 'doctest', 'pdb', 'trace', 'warnings'
    }

    def __init__(self, logger: logging.Logger, project_root: Optional[Path] = None):
        self.logger = logger
        self.project_root = project_root or Path.cwd()
        self.graph = ComponentGraph()
        self.identifier = ComponentIdentifier(logger)
        self._module_to_file: Dict[str, Path] = {}
        self._class_to_module: Dict[str, str] = {}

    def build(self, target_path: Path) -> ComponentGraph:
        """构建组件依赖图"""
        self.logger.info("开始构建组件依赖图...")
        self.graph = ComponentGraph()

        py_files = list(target_path.rglob("*.py")) if target_path.is_dir() else [target_path]

        for py_file in py_files:
            self._process_file(py_file, target_path)

        self.logger.info(f"组件图构建完成: {len(self.graph.nodes)} 个组件, {len(self.graph.edges)} 条依赖")
        return self.graph

    def _process_file(self, py_file: Path, root_path: Path) -> None:
        """处理单个文件"""
        try:
            module_name = self._get_module_name(py_file, root_path)

            with open(py_file, 'r', encoding='utf-8') as f:
                source = f.read()

            tree = ast.parse(source)

            self._extract_module_component(py_file, module_name, tree)
            self._extract_class_components(py_file, module_name, tree)
            self._extract_function_components(py_file, module_name, tree)
            self._extract_imports(py_file, module_name, tree)
            self._extract_inheritance(py_file, module_name, tree)
            self._extract_composition(py_file, module_name, tree)

            self._module_to_file[module_name] = py_file

        except Exception as e:
            self.logger.warning(f"处理文件失败 {py_file}: {e}")

    def _get_module_name(self, py_file: Path, root_path: Path) -> str:
        """获取模块名"""
        try:
            rel_path = py_file.relative_to(root_path)
            parts = list(rel_path.parts)
            if parts[-1] == '__init__.py':
                parts = parts[:-1]
            else:
                parts[-1] = parts[-1].replace('.py', '')
            return '.'.join(parts)
        except ValueError:
            return py_file.stem

    def _extract_module_component(
        self,
        file_path: Path,
        module_name: str,
        tree: ast.AST
    ) -> None:
        """提取模块组件"""
        layer = self.identifier.identify_layer(file_path)
        comp_type = self.identifier.identify_type(file_path)

        node = ComponentNode(
            name=module_name,
            component_type=ComponentType.MODULE,
            file_path=str(file_path),
            layer=layer,
            description=f"模块 {module_name}"
        )
        self.graph.add_node(node)

    def _extract_class_components(
        self,
        file_path: Path,
        module_name: str,
        tree: ast.AST
    ) -> None:
        """提取类组件"""
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                class_name = f"{module_name}.{node.name}"
                self._class_to_module[node.name] = module_name

                layer = self.identifier.identify_layer(file_path, node.name)
                comp_type = self.identifier.identify_type(file_path, node.name)

                is_abstract = any(
                    base for base in node.bases
                    if isinstance(base, ast.Name) and base.id in ['ABC', 'ABCMeta']
                )

                class_node = ComponentNode(
                    name=class_name,
                    component_type=ComponentType.INTERFACE if is_abstract else comp_type,
                    file_path=str(file_path),
                    layer=layer,
                    line_number=node.lineno,
                    description=f"类 {node.name}"
                )
                class_node.metrics["methods"] = len([
                    n for n in node.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
                ])
                class_node.metrics["attributes"] = len([
                    n for n in node.body if isinstance(n, ast.AnnAssign)
                ])

                self.graph.add_node(class_node)

                edge = DependencyEdge(
                    source=class_name,
                    target=module_name,
                    dependency_type=DependencyType.COMPOSITION,
                    line_number=node.lineno,
                    description=f"类 {node.name} 属于模块 {module_name}"
                )
                self.graph.add_edge(edge)

    def _extract_function_components(
        self,
        file_path: Path,
        module_name: str,
        tree: ast.AST
    ) -> None:
        """提取函数组件"""
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if node.col_offset > 0:
                    continue

                func_name = f"{module_name}.{node.name}"

                layer = self.identifier.identify_layer(file_path, node.name)

                func_node = ComponentNode(
                    name=func_name,
                    component_type=ComponentType.FUNCTION,
                    file_path=str(file_path),
                    layer=layer,
                    line_number=node.lineno,
                    description=f"函数 {node.name}"
                )
                func_node.metrics["parameters"] = len(node.args.args)
                func_node.metrics["is_async"] = isinstance(node, ast.AsyncFunctionDef)

                self.graph.add_node(func_node)

    def _extract_imports(
        self,
        file_path: Path,
        module_name: str,
        tree: ast.AST
    ) -> None:
        """提取导入依赖"""
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if not self._is_external_module(alias.name):
                        edge = DependencyEdge(
                            source=module_name,
                            target=alias.name,
                            dependency_type=DependencyType.IMPORT,
                            line_number=node.lineno,
                            description=f"import {alias.name}"
                        )
                        self.graph.add_edge(edge)

            elif isinstance(node, ast.ImportFrom):
                if node.module and not self._is_external_module(node.module):
                    edge = DependencyEdge(
                        source=module_name,
                        target=node.module,
                        dependency_type=DependencyType.IMPORT,
                        line_number=node.lineno,
                        description=f"from {node.module} import ..."
                    )
                    self.graph.add_edge(edge)

    def _extract_inheritance(
        self,
        file_path: Path,
        module_name: str,
        tree: ast.AST
    ) -> None:
        """提取继承依赖"""
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                class_name = f"{module_name}.{node.name}"

                for base in node.bases:
                    base_name = self._get_base_name(base)
                    if base_name and not self._is_builtin(base_name):
                        full_base = self._resolve_class_name(base_name, module_name)

                        edge = DependencyEdge(
                            source=class_name,
                            target=full_base,
                            dependency_type=DependencyType.INHERITANCE,
                            line_number=node.lineno,
                            description=f"{node.name} 继承自 {base_name}"
                        )
                        self.graph.add_edge(edge)

    def _extract_composition(
        self,
        file_path: Path,
        module_name: str,
        tree: ast.AST
    ) -> None:
        """提取组合依赖"""
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                class_name = f"{module_name}.{node.name}"

                for item in node.body:
                    if isinstance(item, ast.AnnAssign):
                        if item.annotation:
                            type_name = self._extract_type_name(item.annotation)
                            if type_name and not self._is_builtin(type_name):
                                full_type = self._resolve_class_name(type_name, module_name)

                                edge = DependencyEdge(
                                    source=class_name,
                                    target=full_type,
                                    dependency_type=DependencyType.COMPOSITION,
                                    line_number=item.lineno,
                                    description=f"属性类型依赖: {type_name}"
                                )
                                self.graph.add_edge(edge)

                    if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        for arg in item.args.args:
                            if arg.annotation:
                                type_name = self._extract_type_name(arg.annotation)
                                if type_name and not self._is_builtin(type_name):
                                    full_type = self._resolve_class_name(type_name, module_name)

                                    edge = DependencyEdge(
                                        source=class_name,
                                        target=full_type,
                                        dependency_type=DependencyType.ASSOCIATION,
                                        line_number=item.lineno,
                                        description=f"参数类型依赖: {type_name}"
                                    )
                                    self.graph.add_edge(edge)

    def _get_base_name(self, base: ast.expr) -> Optional[str]:
        """获取基类名称"""
        if isinstance(base, ast.Name):
            return base.id
        elif isinstance(base, ast.Attribute):
            if isinstance(base.value, ast.Name):
                return f"{base.value.id}.{base.attr}"
        return None

    def _extract_type_name(self, annotation: ast.expr) -> Optional[str]:
        """提取类型名称"""
        if isinstance(annotation, ast.Name):
            return annotation.id
        elif isinstance(annotation, ast.Attribute):
            if isinstance(annotation.value, ast.Name):
                return f"{annotation.value.id}.{annotation.attr}"
        elif isinstance(annotation, ast.Subscript):
            if hasattr(ast, 'unparse'):
                type_str = ast.unparse(annotation)
                return type_str.split('[')[0]
        return None

    def _resolve_class_name(self, class_name: str, current_module: str) -> str:
        """解析类全名"""
        if '.' in class_name:
            return class_name

        if class_name in self._class_to_module:
            return f"{self._class_to_module[class_name]}.{class_name}"

        return f"{current_module}.{class_name}"

    def _is_external_module(self, module_name: str) -> bool:
        """判断是否是外部模块"""
        top_level = module_name.split('.')[0]
        if top_level in self.STANDARD_LIBRARY:
            return True
        return not any(
            module_name.startswith(m.split('.')[0])
            for m in self._module_to_file.keys()
        )

    def _is_builtin(self, name: str) -> bool:
        """判断是否是内置类型"""
        builtins = {
            'str', 'int', 'float', 'bool', 'list', 'dict', 'set', 'tuple',
            'None', 'Any', 'Optional', 'Union', 'List', 'Dict', 'Set', 'Tuple',
            'Callable', 'Type', 'ClassVar', 'Final', 'Literal', 'Annotated',
            'ABC', 'ABCMeta', 'Enum', 'Exception', 'object'
        }
        return name in builtins or name in self.STANDARD_LIBRARY


class CycleDetector:
    """循环依赖检测器"""

    def __init__(self, logger: logging.Logger):
        self.logger = logger
        self.cycles: List[CycleInfo] = []

    def detect(self, graph: ComponentGraph) -> List[CycleInfo]:
        """检测循环依赖"""
        self.logger.info("开始检测循环依赖...")
        self.cycles = []

        visited: Set[str] = set()
        rec_stack: Set[str] = set()

        for node in graph.nodes:
            if node not in visited:
                self._dfs_detect(node, graph.adjacency, visited, rec_stack, [])

        self._deduplicate_cycles()
        self._assess_severity()
        self._generate_suggestions()

        self.logger.info(f"检测到 {len(self.cycles)} 个循环依赖")
        return self.cycles

    def _dfs_detect(
        self,
        node: str,
        adj_list: Dict[str, Set[str]],
        visited: Set[str],
        rec_stack: Set[str],
        path: List[str]
    ) -> None:
        """深度优先搜索检测循环"""
        visited.add(node)
        rec_stack.add(node)
        path.append(node)

        for neighbor in adj_list.get(node, set()):
            if neighbor not in visited:
                self._dfs_detect(neighbor, adj_list, visited, rec_stack, path)
            elif neighbor in rec_stack:
                cycle_start = path.index(neighbor) if neighbor in path else len(path) - 1
                cycle = path[cycle_start:] + [neighbor]

                cycle_info = CycleInfo(
                    cycle_path=cycle,
                    severity=CycleSeverity.MEDIUM,
                    involved_components=set(cycle),
                    description=f"循环依赖: {' -> '.join(cycle)}"
                )
                self.cycles.append(cycle_info)

        path.pop()
        rec_stack.remove(node)

    def _deduplicate_cycles(self) -> None:
        """去除重复的循环"""
        unique_cycles: Dict[Tuple[str, ...], CycleInfo] = {}

        for cycle in self.cycles:
            normalized = self._normalize_cycle(cycle.cycle_path)
            key = tuple(sorted(normalized))
            if key not in unique_cycles:
                unique_cycles[key] = cycle

        self.cycles = list(unique_cycles.values())

    def _normalize_cycle(self, cycle: List[str]) -> List[str]:
        """规范化循环表示"""
        if len(cycle) <= 1:
            return cycle

        min_idx = cycle.index(min(cycle[:-1]))
        return cycle[min_idx:-1] + cycle[:min_idx] + [cycle[min_idx]]

    def _assess_severity(self) -> None:
        """评估循环严重程度"""
        for cycle in self.cycles:
            length = len(cycle.cycle_path) - 1

            if length == 2:
                cycle.severity = CycleSeverity.LOW
            elif length <= 4:
                cycle.severity = CycleSeverity.MEDIUM
            elif length <= 6:
                cycle.severity = CycleSeverity.HIGH
            else:
                cycle.severity = CycleSeverity.CRITICAL

            cycle.description = f"循环依赖 ({cycle.severity.value}): {' -> '.join(cycle.cycle_path)}"

    def _generate_suggestions(self) -> None:
        """生成解决建议"""
        for cycle in self.cycles:
            suggestions = []

            if len(cycle.cycle_path) <= 3:
                suggestions.append("考虑合并这些组件到一个模块中")
            else:
                suggestions.append("引入中间层或接口来打破循环")
                suggestions.append("使用依赖注入替代直接依赖")

            cycle.suggestions = suggestions


class CouplingAnalyzer:
    """耦合度分析器"""

    HIGH_COUPLING_THRESHOLD = 0.7
    LOW_COUPLING_THRESHOLD = 0.3

    def __init__(self, logger: logging.Logger):
        self.logger = logger
        self.metrics: Dict[str, CouplingMetrics] = {}

    def analyze(self, graph: ComponentGraph) -> Dict[str, CouplingMetrics]:
        """分析耦合度"""
        self.logger.info("开始分析耦合度...")
        self.metrics = {}

        for comp_name, node in graph.nodes.items():
            if node.component_type == ComponentType.FUNCTION:
                continue

            metrics = CouplingMetrics(component_name=comp_name)

            metrics.afferent_coupling = len(node.dependents)
            metrics.efferent_coupling = len(node.dependencies)

            total_coupling = metrics.afferent_coupling + metrics.efferent_coupling
            if total_coupling > 0:
                metrics.instability = metrics.efferent_coupling / total_coupling

            metrics.abstractness = self._calculate_abstractness(node)

            metrics.distance_from_main = abs(metrics.abstractness + metrics.instability - 1)

            metrics.coupling_level = self._determine_coupling_level(metrics)

            self.metrics[comp_name] = metrics

        self.logger.info(f"耦合度分析完成: {len(self.metrics)} 个组件")
        return self.metrics

    def _calculate_abstractness(self, node: ComponentNode) -> float:
        """计算抽象度"""
        if node.component_type == ComponentType.INTERFACE:
            return 1.0

        if node.component_type not in [ComponentType.CLASS, ComponentType.MODULE]:
            return 0.0

        if node.name.split('.')[-1].startswith(('Abstract', 'Base', 'I', 'Interface')):
            return 1.0

        return 0.0

    def _determine_coupling_level(self, metrics: CouplingMetrics) -> CouplingLevel:
        """确定耦合级别"""
        if metrics.efferent_coupling == 0 and metrics.afferent_coupling == 0:
            return CouplingLevel.NONE

        total = metrics.afferent_coupling + metrics.efferent_coupling
        if total > 15:
            return CouplingLevel.TIGHT
        elif total > 10:
            return CouplingLevel.HIGH
        elif total > 5:
            return CouplingLevel.MEDIUM
        else:
            return CouplingLevel.LOW

    def get_highly_coupled_components(self, threshold: int = 10) -> List[Tuple[str, int]]:
        """获取高耦合组件"""
        coupled = [
            (name, m.afferent_coupling + m.efferent_coupling)
            for name, m in self.metrics.items()
        ]
        return sorted(coupled, key=lambda x: x[1], reverse=True)[:threshold]


class LayerAnalyzer:
    """层级分析器"""

    LAYER_DEPENDENCY_RULES = {
        ArchitectureLayer.PRESENTATION: {
            'allowed': [ArchitectureLayer.BUSINESS, ArchitectureLayer.CROSS_CUTTING],
            'forbidden': [ArchitectureLayer.DATA, ArchitectureLayer.INFRASTRUCTURE]
        },
        ArchitectureLayer.BUSINESS: {
            'allowed': [ArchitectureLayer.DATA, ArchitectureLayer.CROSS_CUTTING],
            'forbidden': [ArchitectureLayer.PRESENTATION]
        },
        ArchitectureLayer.DATA: {
            'allowed': [ArchitectureLayer.INFRASTRUCTURE, ArchitectureLayer.CROSS_CUTTING],
            'forbidden': [ArchitectureLayer.PRESENTATION, ArchitectureLayer.BUSINESS]
        },
        ArchitectureLayer.INFRASTRUCTURE: {
            'allowed': [ArchitectureLayer.CROSS_CUTTING],
            'forbidden': [ArchitectureLayer.PRESENTATION, ArchitectureLayer.BUSINESS, ArchitectureLayer.DATA]
        },
        ArchitectureLayer.CROSS_CUTTING: {
            'allowed': [],
            'forbidden': []
        }
    }

    def __init__(self, logger: logging.Logger):
        self.logger = logger
        self.metrics: Dict[str, LayerMetrics] = {}

    def analyze(self, graph: ComponentGraph) -> Dict[str, LayerMetrics]:
        """分析层级"""
        self.logger.info("开始分析层级...")
        self.metrics = {}

        for layer in ArchitectureLayer:
            self.metrics[layer.value] = LayerMetrics(layer=layer)

        for comp_name, node in graph.nodes.items():
            layer_key = node.layer.value
            self.metrics[layer_key].component_count += 1

        for edge in graph.edges:
            source_node = graph.nodes.get(edge.source)
            target_node = graph.nodes.get(edge.target)

            if source_node and target_node:
                source_layer = source_node.layer
                target_layer = target_node.layer

                layer_key = source_layer.value
                self.metrics[layer_key].dependency_count += 1

                if source_layer == target_layer:
                    self.metrics[layer_key].internal_dependencies += 1
                else:
                    self.metrics[layer_key].external_dependencies += 1

                if self._is_layer_violation(source_layer, target_layer):
                    self.metrics[layer_key].violation_count += 1

        self.logger.info("层级分析完成")
        return self.metrics

    def _is_layer_violation(
        self,
        source_layer: ArchitectureLayer,
        target_layer: ArchitectureLayer
    ) -> bool:
        """判断是否违反层级规则"""
        if source_layer == ArchitectureLayer.UNKNOWN or target_layer == ArchitectureLayer.UNKNOWN:
            return False

        rules = self.LAYER_DEPENDENCY_RULES.get(source_layer, {})
        forbidden = rules.get('forbidden', [])

        return target_layer in forbidden


class OptimizationSuggester:
    """优化建议生成器"""

    def __init__(self, logger: logging.Logger):
        self.logger = logger

    def generate(
        self,
        graph: ComponentGraph,
        cycles: List[CycleInfo],
        coupling_metrics: Dict[str, CouplingMetrics],
        layer_metrics: Dict[str, LayerMetrics]
    ) -> List[OptimizationSuggestion]:
        """生成优化建议"""
        self.logger.info("开始生成优化建议...")
        suggestions = []

        suggestions.extend(self._generate_cycle_suggestions(cycles))
        suggestions.extend(self._generate_coupling_suggestions(coupling_metrics))
        suggestions.extend(self._generate_layer_suggestions(layer_metrics))
        suggestions.extend(self._generate_structure_suggestions(graph))

        suggestions.sort(key=lambda s: {'high': 0, 'medium': 1, 'low': 2}.get(s.priority, 3))

        self.logger.info(f"生成了 {len(suggestions)} 条优化建议")
        return suggestions

    def _generate_cycle_suggestions(self, cycles: List[CycleInfo]) -> List[OptimizationSuggestion]:
        """生成循环依赖建议"""
        suggestions = []

        for cycle in cycles:
            if cycle.severity in [CycleSeverity.CRITICAL, CycleSeverity.HIGH]:
                suggestions.append(OptimizationSuggestion(
                    suggestion_type="cycle_resolution",
                    priority="high",
                    component=', '.join(cycle.involved_components),
                    description=f"解决严重循环依赖: {cycle.description}",
                    impact="消除循环依赖可以提高代码可维护性和可测试性",
                    implementation=cycle.suggestions[0] if cycle.suggestions else "重构代码结构"
                ))

        return suggestions

    def _generate_coupling_suggestions(
        self,
        coupling_metrics: Dict[str, CouplingMetrics]
    ) -> List[OptimizationSuggestion]:
        """生成耦合度建议"""
        suggestions = []

        for comp_name, metrics in coupling_metrics.items():
            total_coupling = metrics.afferent_coupling + metrics.efferent_coupling

            if total_coupling > 15:
                suggestions.append(OptimizationSuggestion(
                    suggestion_type="reduce_coupling",
                    priority="high",
                    component=comp_name,
                    description=f"组件 '{comp_name}' 耦合度过高 (总耦合度: {total_coupling})",
                    impact="降低耦合度可以提高组件的独立性和可复用性",
                    implementation="考虑拆分组件或引入接口抽象"
                ))

            if metrics.instability > 0.8 and metrics.efferent_coupling > 5:
                suggestions.append(OptimizationSuggestion(
                    suggestion_type="stabilize_component",
                    priority="medium",
                    component=comp_name,
                    description=f"组件 '{comp_name}' 不稳定性过高 ({metrics.instability:.2f})",
                    impact="提高稳定性可以减少组件变更的影响范围",
                    implementation="增加抽象层或减少外部依赖"
                ))

        return suggestions

    def _generate_layer_suggestions(
        self,
        layer_metrics: Dict[str, LayerMetrics]
    ) -> List[OptimizationSuggestion]:
        """生成层级建议"""
        suggestions = []

        for layer_name, metrics in layer_metrics.items():
            if metrics.violation_count > 0:
                suggestions.append(OptimizationSuggestion(
                    suggestion_type="layer_violation",
                    priority="high",
                    component=f"{layer_name} 层",
                    description=f"{layer_name} 层存在 {metrics.violation_count} 个层级违规",
                    impact="遵守层级规则可以保持架构清晰",
                    implementation="检查并修复违反层级原则的依赖"
                ))

        return suggestions

    def _generate_structure_suggestions(self, graph: ComponentGraph) -> List[OptimizationSuggestion]:
        """生成结构建议"""
        suggestions = []

        component_counts: Dict[ComponentType, int] = defaultdict(int)
        for node in graph.nodes.values():
            component_counts[node.component_type] += 1

        if component_counts.get(ComponentType.UTILITY, 0) > 20:
            suggestions.append(OptimizationSuggestion(
                suggestion_type="consolidate_utilities",
                priority="low",
                component="utility components",
                description="工具类组件过多，考虑合并相似功能",
                impact="减少组件数量可以提高代码组织性",
                implementation="识别功能相似的工具类并进行合并"
            ))

        return suggestions


class ComponentDependencyAnalyzer:
    """组件依赖分析器主类"""

    def __init__(
        self,
        project_path: Optional[Path] = None,
        logger: Optional[logging.Logger] = None
    ):
        self.project_path = project_path or Path.cwd()
        self.logger = logger or self._setup_logger()

        self.graph_builder = ComponentGraphBuilder(self.logger, self.project_path)
        self.cycle_detector = CycleDetector(self.logger)
        self.coupling_analyzer = CouplingAnalyzer(self.logger)
        self.layer_analyzer = LayerAnalyzer(self.logger)
        self.optimization_suggester = OptimizationSuggester(self.logger)

        self._graph: Optional[ComponentGraph] = None
        self._cycles: List[CycleInfo] = []
        self._coupling_metrics: Dict[str, CouplingMetrics] = {}
        self._layer_metrics: Dict[str, LayerMetrics] = {}

    def _setup_logger(self) -> logging.Logger:
        """配置日志记录器"""
        logger = logging.getLogger("ComponentDependencyAnalyzer")
        logger.setLevel(logging.INFO)

        if not logger.handlers:
            handler = logging.StreamHandler(sys.stdout)
            handler.setLevel(logging.INFO)
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)

        return logger

    def analyze(self, target_path: Optional[Path] = None) -> ComponentDependencyReport:
        """执行组件依赖分析"""
        self.logger.info("开始组件依赖分析...")

        target = target_path or self.project_path

        self._graph = self.graph_builder.build(target)
        self._cycles = self.cycle_detector.detect(self._graph)
        self._coupling_metrics = self.coupling_analyzer.analyze(self._graph)
        self._layer_metrics = self.layer_analyzer.analyze(self._graph)

        suggestions = self.optimization_suggester.generate(
            self._graph,
            self._cycles,
            self._coupling_metrics,
            self._layer_metrics
        )

        summary = self._build_summary()

        return ComponentDependencyReport(
            timestamp=datetime.now().isoformat(),
            project_path=str(target),
            graph=self._graph,
            cycles=self._cycles,
            coupling_metrics=self._coupling_metrics,
            layer_metrics=self._layer_metrics,
            summary=summary,
            suggestions=suggestions
        )

    def _build_summary(self) -> Dict[str, Any]:
        """构建摘要"""
        cycle_severity_counts = defaultdict(int)
        for cycle in self._cycles:
            cycle_severity_counts[cycle.severity.value] += 1

        coupling_level_counts = defaultdict(int)
        for metrics in self._coupling_metrics.values():
            coupling_level_counts[metrics.coupling_level.value] += 1

        layer_component_counts = {}
        for layer_name, metrics in self._layer_metrics.items():
            if metrics.component_count > 0:
                layer_component_counts[layer_name] = metrics.component_count

        total_violations = sum(
            m.violation_count for m in self._layer_metrics.values()
        )

        return {
            "total_components": len(self._graph.nodes),
            "total_dependencies": len(self._graph.edges),
            "cycle_count": len(self._cycles),
            "cycle_severity_breakdown": dict(cycle_severity_counts),
            "coupling_level_breakdown": dict(coupling_level_counts),
            "layer_component_counts": layer_component_counts,
            "layer_violations": total_violations,
            "architecture_health_score": self._calculate_health_score()
        }

    def _calculate_health_score(self) -> float:
        """计算架构健康得分"""
        score = 100.0

        for cycle in self._cycles:
            if cycle.severity == CycleSeverity.CRITICAL:
                score -= 15
            elif cycle.severity == CycleSeverity.HIGH:
                score -= 10
            elif cycle.severity == CycleSeverity.MEDIUM:
                score -= 5
            else:
                score -= 2

        for metrics in self._coupling_metrics.values():
            if metrics.coupling_level == CouplingLevel.TIGHT:
                score -= 5
            elif metrics.coupling_level == CouplingLevel.HIGH:
                score -= 3

        total_violations = sum(
            m.violation_count for m in self._layer_metrics.values()
        )
        score -= total_violations * 3

        return max(0.0, min(100.0, score))

    def print_report(self, report: ComponentDependencyReport) -> None:
        """打印报告"""
        print("\n" + "=" * 80)
        print("组件依赖分析报告")
        print("=" * 80)
        print(f"项目路径: {report.project_path}")
        print(f"分析时间: {report.timestamp}")
        print(f"架构健康得分: {report.summary['architecture_health_score']:.1f}%")

        print("\n" + "-" * 80)
        print("组件概览")
        print("-" * 80)
        print(f"组件总数: {report.summary['total_components']}")
        print(f"依赖总数: {report.summary['total_dependencies']}")

        print("\n层级分布:")
        for layer, count in report.summary['layer_component_counts'].items():
            print(f"  - {layer}: {count} 个组件")

        print("\n" + "-" * 80)
        print("循环依赖")
        print("-" * 80)

        if report.cycles:
            print(f"发现 {len(report.cycles)} 个循环依赖:")

            severity_icons = {
                CycleSeverity.CRITICAL.value: "🔴",
                CycleSeverity.HIGH.value: "🟠",
                CycleSeverity.MEDIUM.value: "🟡",
                CycleSeverity.LOW.value: "🔵"
            }

            for cycle in report.cycles[:10]:
                icon = severity_icons.get(cycle.severity.value, "⚪")
                print(f"  {icon} [{cycle.severity.value.upper()}] {' -> '.join(cycle.cycle_path)}")

            if len(report.cycles) > 10:
                print(f"  ... 还有 {len(report.cycles) - 10} 个循环未显示")
        else:
            print("✅ 未发现循环依赖")

        print("\n" + "-" * 80)
        print("耦合度分析")
        print("-" * 80)

        coupling_breakdown = report.summary['coupling_level_breakdown']
        coupling_icons = {
            CouplingLevel.TIGHT.value: "🔴",
            CouplingLevel.HIGH.value: "🟠",
            CouplingLevel.MEDIUM.value: "🟡",
            CouplingLevel.LOW.value: "🟢",
            CouplingLevel.NONE.value: "⚪"
        }

        for level, count in coupling_breakdown.items():
            icon = coupling_icons.get(level, "⚪")
            print(f"  {icon} {level}: {count} 个组件")

        highly_coupled = self.coupling_analyzer.get_highly_coupled_components(5)
        if highly_coupled:
            print("\n高耦合组件:")
            for comp, coupling in highly_coupled:
                print(f"  - {comp}: 总耦合度 {coupling}")

        if report.summary['layer_violations'] > 0:
            print("\n" + "-" * 80)
            print("层级违规")
            print("-" * 80)
            print(f"发现 {report.summary['layer_violations']} 个层级违规")

        if report.suggestions:
            print("\n" + "-" * 80)
            print("优化建议")
            print("-" * 80)

            for i, suggestion in enumerate(report.suggestions[:15], 1):
                priority_icon = {'high': '🔴', 'medium': '🟡', 'low': '🔵'}.get(suggestion.priority, '⚪')
                print(f"\n{i}. {priority_icon} [{suggestion.priority.upper()}] {suggestion.suggestion_type}")
                print(f"   组件: {suggestion.component}")
                print(f"   描述: {suggestion.description}")
                print(f"   建议: {suggestion.implementation}")

    def save_report(self, report: ComponentDependencyReport, output_path: str) -> None:
        """保存报告到文件"""
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)

        with open(path, 'w', encoding='utf-8') as f:
            json.dump(report.to_dict(), f, indent=2, ensure_ascii=False)

        self.logger.info(f"报告已保存: {path}")

    def export_graph_dot(self, output_path: str) -> None:
        """导出DOT格式的依赖图"""
        if not self._graph:
            self.logger.warning("请先执行分析")
            return

        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)

        lines = ['digraph component_dependencies {']
        lines.append('    rankdir=TB;')
        lines.append('    node [shape=box];')

        layer_colors = {
            ArchitectureLayer.PRESENTATION.value: '#E3F2FD',
            ArchitectureLayer.BUSINESS.value: '#E8F5E9',
            ArchitectureLayer.DATA.value: '#FFF3E0',
            ArchitectureLayer.INFRASTRUCTURE.value: '#F3E5F5',
            ArchitectureLayer.CROSS_CUTTING.value: '#FFEBEE',
            ArchitectureLayer.UNKNOWN.value: '#FAFAFA'
        }

        for comp_name, node in self._graph.nodes.items():
            safe_name = comp_name.replace('.', '_')
            color = layer_colors.get(node.layer.value, '#FAFAFA')
            lines.append(f'    "{safe_name}" [label="{comp_name}", style=filled, fillcolor="{color}"];')

        for edge in self._graph.edges:
            safe_source = edge.source.replace('.', '_')
            safe_target = edge.target.replace('.', '_')
            lines.append(f'    "{safe_source}" -> "{safe_target}";')

        lines.append('}')

        with open(path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines))

        self.logger.info(f"DOT图已导出: {path}")


def main() -> int:
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(
        description="组件依赖分析器",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument(
        "--path",
        type=str,
        default=".",
        help="要分析的路径 (默认: 当前目录)"
    )
    parser.add_argument(
        "--output",
        type=str,
        choices=["console", "json"],
        default="console",
        help="输出格式 (默认: console)"
    )
    parser.add_argument(
        "--output-file",
        type=str,
        help="输出文件路径"
    )
    parser.add_argument(
        "--detect-cycles",
        action="store_true",
        help="仅检测循环依赖"
    )
    parser.add_argument(
        "--export-dot",
        type=str,
        help="导出DOT格式的依赖图"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="启用详细日志输出"
    )

    args = parser.parse_args()

    logger = logging.getLogger("ComponentDependencyAnalyzer")
    logger.setLevel(logging.DEBUG if args.verbose else logging.INFO)

    analyzer = ComponentDependencyAnalyzer(
        project_path=Path(args.path),
        logger=logger
    )

    report = analyzer.analyze()

    if args.output == "console":
        analyzer.print_report(report)
    else:
        print(json.dumps(report.to_dict(), indent=2, ensure_ascii=False))

    if args.output_file:
        analyzer.save_report(report, args.output_file)

    if args.export_dot:
        analyzer.export_graph_dot(args.export_dot)

    return 0 if not report.cycles else 1


if __name__ == "__main__":
    sys.exit(main())
