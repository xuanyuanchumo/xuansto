#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
依赖关系分析器 - Sanliu 技能 (深度优化版)

提供全面的依赖关系分析功能，包括：
- 依赖关系图构建：模块级、类级、函数级依赖分析
- 循环依赖检测：深度优先搜索、Tarjan算法、跨文件分析
- 耦合度分析：传入/传出耦合、不稳定性、抽象度、距离主序列
- 依赖层次分析：分层架构检测、依赖方向验证
- 架构健康度评估：模块化指数、依赖复杂度、架构债务

使用示例:
    python dependency_analyzer.py
    python dependency_analyzer.py --path ./src
    python dependency_analyzer.py --output json --output-file report.json
    python dependency_analyzer.py --detect-cycles
    python dependency_analyzer.py --coupling-analysis
    python dependency_analyzer.py --layer-analysis
    python dependency_analyzer.py --export-dot graph.dot
"""

import ast
import json
import logging
import sys
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple, Callable
from functools import lru_cache


class DependencyType(Enum):
    IMPORT = "import"
    FROM_IMPORT = "from_import"
    INHERITANCE = "inheritance"
    COMPOSITION = "composition"
    AGGREGATION = "aggregation"
    ATTRIBUTE = "attribute"
    PARAMETER = "parameter"
    RETURN_TYPE = "return_type"
    LOCAL_VARIABLE = "local_variable"
    TYPE_HINT = "type_hint"
    DECORATOR = "decorator"
    FUNCTION_CALL = "function_call"


class CouplingLevel(Enum):
    TIGHT = "tight"
    MEDIUM = "medium"
    LOOSE = "loose"
    NONE = "none"


class CycleSeverity(Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class ModuleLayer(Enum):
    PRESENTATION = "presentation"
    APPLICATION = "application"
    DOMAIN = "domain"
    INFRASTRUCTURE = "infrastructure"
    CROSS_CUTTING = "cross_cutting"
    UNKNOWN = "unknown"


class DependencyDirection(Enum):
    DOWNWARD = "downward"
    UPWARD = "upward"
    LATERAL = "lateral"
    UNKNOWN = "unknown"


class ArchitectureHealth(Enum):
    EXCELLENT = "excellent"
    GOOD = "good"
    FAIR = "fair"
    POOR = "poor"
    CRITICAL = "critical"


@dataclass
class DependencyNode:
    module_name: str
    file_path: str
    is_external: bool = False
    is_test: bool = False
    layer: ModuleLayer = ModuleLayer.UNKNOWN
    dependencies: Set[str] = field(default_factory=set)
    dependents: Set[str] = field(default_factory=set)
    classes: List[str] = field(default_factory=list)
    functions: List[str] = field(default_factory=list)
    imports: List[str] = field(default_factory=list)
    exported_symbols: Set[str] = field(default_factory=set)
    imported_symbols: Dict[str, str] = field(default_factory=dict)
    abstract_classes: int = 0
    concrete_classes: int = 0
    lines_of_code: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "module_name": self.module_name,
            "file_path": self.file_path,
            "is_external": self.is_external,
            "is_test": self.is_test,
            "layer": self.layer.value,
            "dependencies": list(self.dependencies),
            "dependents": list(self.dependents),
            "classes": self.classes,
            "functions": self.functions,
            "imports": self.imports,
            "exported_symbols": list(self.exported_symbols),
            "abstract_classes": self.abstract_classes,
            "concrete_classes": self.concrete_classes,
            "lines_of_code": self.lines_of_code
        }


@dataclass
class DependencyEdge:
    source: str
    target: str
    dependency_type: DependencyType
    line_number: Optional[int] = None
    details: str = ""
    weight: float = 1.0
    is_internal: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return {
            "source": self.source,
            "target": self.target,
            "dependency_type": self.dependency_type.value,
            "line_number": self.line_number,
            "details": self.details,
            "weight": self.weight,
            "is_internal": self.is_internal
        }


@dataclass
class CycleInfo:
    cycle_path: List[str]
    severity: CycleSeverity
    involved_modules: Set[str]
    description: str
    cycle_type: str = "module"
    suggested_fix: str = ""
    impact_score: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "cycle_path": self.cycle_path,
            "severity": self.severity.value,
            "involved_modules": list(self.involved_modules),
            "description": self.description,
            "cycle_type": self.cycle_type,
            "suggested_fix": self.suggested_fix,
            "impact_score": self.impact_score
        }


@dataclass
class CouplingMetrics:
    module_name: str
    afferent_coupling: int = 0
    efferent_coupling: int = 0
    total_coupling: int = 0
    instability: float = 0.0
    abstractness: float = 0.0
    distance_from_main: float = 0.0
    coupling_level: CouplingLevel = CouplingLevel.NONE
    normalized_distance: float = 0.0
    dependency_weight: float = 0.0
    fan_in: int = 0
    fan_out: int = 0
    depth: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "module_name": self.module_name,
            "afferent_coupling": self.afferent_coupling,
            "efferent_coupling": self.efferent_coupling,
            "total_coupling": self.total_coupling,
            "instability": self.instability,
            "abstractness": self.abstractness,
            "distance_from_main": self.distance_from_main,
            "coupling_level": self.coupling_level.value,
            "normalized_distance": self.normalized_distance,
            "dependency_weight": self.dependency_weight,
            "fan_in": self.fan_in,
            "fan_out": self.fan_out,
            "depth": self.depth
        }


@dataclass
class LayerInfo:
    layer: ModuleLayer
    modules: List[str]
    incoming_dependencies: int = 0
    outgoing_dependencies: int = 0
    stability: float = 0.0
    violations: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "layer": self.layer.value,
            "modules": self.modules,
            "module_count": len(self.modules),
            "incoming_dependencies": self.incoming_dependencies,
            "outgoing_dependencies": self.outgoing_dependencies,
            "stability": self.stability,
            "violations": self.violations
        }


@dataclass
class ArchitectureMetrics:
    total_modules: int = 0
    total_dependencies: int = 0
    average_coupling: float = 0.0
    average_instability: float = 0.0
    average_abstractness: float = 0.0
    cycle_count: int = 0
    layer_violation_count: int = 0
    modularity_index: float = 0.0
    dependency_complexity: float = 0.0
    architecture_debt_score: float = 0.0
    health_status: ArchitectureHealth = ArchitectureHealth.GOOD

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_modules": self.total_modules,
            "total_dependencies": self.total_dependencies,
            "average_coupling": self.average_coupling,
            "average_instability": self.average_instability,
            "average_abstractness": self.average_abstractness,
            "cycle_count": self.cycle_count,
            "layer_violation_count": self.layer_violation_count,
            "modularity_index": self.modularity_index,
            "dependency_complexity": self.dependency_complexity,
            "architecture_debt_score": self.architecture_debt_score,
            "health_status": self.health_status.value
        }


@dataclass
class DependencyGraph:
    nodes: Dict[str, DependencyNode] = field(default_factory=dict)
    edges: List[DependencyEdge] = field(default_factory=list)
    adjacency_list: Dict[str, Set[str]] = field(default_factory=lambda: defaultdict(set))
    reverse_adjacency: Dict[str, Set[str]] = field(default_factory=lambda: defaultdict(set))
    edge_weights: Dict[Tuple[str, str], float] = field(default_factory=dict)

    def add_node(self, node: DependencyNode) -> None:
        self.nodes[node.module_name] = node

    def add_edge(self, edge: DependencyEdge) -> None:
        self.edges.append(edge)
        self.adjacency_list[edge.source].add(edge.target)
        self.reverse_adjacency[edge.target].add(edge.source)

        key = (edge.source, edge.target)
        self.edge_weights[key] = self.edge_weights.get(key, 0) + edge.weight

        if edge.source in self.nodes:
            self.nodes[edge.source].dependencies.add(edge.target)
        if edge.target in self.nodes:
            self.nodes[edge.target].dependents.add(edge.source)

    def get_dependencies(self, module: str) -> Set[str]:
        return self.adjacency_list.get(module, set())

    def get_dependents(self, module: str) -> Set[str]:
        return self.reverse_adjacency.get(module, set())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "nodes": {k: v.to_dict() for k, v in self.nodes.items()},
            "edges": [e.to_dict() for e in self.edges],
            "adjacency_list": {k: list(v) for k, v in self.adjacency_list.items()},
            "node_count": len(self.nodes),
            "edge_count": len(self.edges)
        }


@dataclass
class DependencyReport:
    timestamp: str
    project_path: str
    graph: DependencyGraph
    cycles: List[CycleInfo]
    coupling_metrics: Dict[str, CouplingMetrics]
    layer_analysis: Dict[str, LayerInfo]
    architecture_metrics: ArchitectureMetrics
    summary: Dict[str, Any] = field(default_factory=dict)
    recommendations: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp,
            "project_path": self.project_path,
            "graph": self.graph.to_dict(),
            "cycles": [c.to_dict() for c in self.cycles],
            "coupling_metrics": {k: v.to_dict() for k, v in self.coupling_metrics.items()},
            "layer_analysis": {k: v.to_dict() for k, v in self.layer_analysis.items()},
            "architecture_metrics": self.architecture_metrics.to_dict(),
            "summary": self.summary,
            "recommendations": self.recommendations
        }


class DependencyGraphBuilder:
    """依赖关系图构建器 (深度优化版)"""

    STANDARD_LIBRARY = {
        'os', 'sys', 're', 'json', 'logging', 'datetime', 'pathlib', 'typing',
        'collections', 'itertools', 'functools', 'abc', 'dataclasses', 'enum',
        'io', 'time', 'math', 'random', 'string', 'copy', 'pickle', 'shutil',
        'tempfile', 'argparse', 'configparser', 'hashlib', 'hmac', 'secrets',
        'threading', 'multiprocessing', 'asyncio', 'concurrent', 'queue',
        'socket', 'ssl', 'http', 'urllib', 'email', 'html', 'xml', 'csv',
        'sqlite3', 'unittest', 'doctest', 'pdb', 'trace', 'warnings',
        'contextlib', 'decimal', 'fractions', 'statistics', 'array',
        'weakref', 'types', 'inspect', 'dis', 'ast', 'tokenize', 'keyword',
        'token', 'symbol', 'opcode', 'codeop', 'code', 'compileall',
        'importlib', 'pkgutil', 'modulefinder', 'zipimport', 'pkg_resources'
    }

    THIRD_PARTY_HINTS = {
        'django', 'flask', 'fastapi', 'tornado', 'aiohttp', 'requests',
        'numpy', 'pandas', 'scipy', 'matplotlib', 'seaborn', 'sklearn',
        'tensorflow', 'torch', 'keras', 'transformers', 'opencv',
        'sqlalchemy', 'pymongo', 'redis', 'celery', 'kombu',
        'pytest', 'selenium', 'playwright', 'locust',
        'pydantic', 'marshmallow', 'attrs', 'click', 'typer',
        'uvicorn', 'gunicorn', 'celery', 'dramatiq',
        'boto3', 'google', 'azure', 'kubernetes'
    }

    LAYER_INDICATORS = {
        ModuleLayer.PRESENTATION: ['views', 'viewsets', 'serializers', 'controllers', 'api', 'routes', 'endpoints', 'handlers', 'ui', 'templates'],
        ModuleLayer.APPLICATION: ['services', 'usecases', 'use_cases', 'applications', 'managers', 'orchestrators', 'coordinators', 'commands', 'queries'],
        ModuleLayer.DOMAIN: ['models', 'entities', 'value_objects', 'aggregates', 'repositories', 'domain', 'core', 'business'],
        ModuleLayer.INFRASTRUCTURE: ['infrastructure', 'persistence', 'external', 'adapters', 'clients', 'gateways', 'factories', 'config', 'db'],
        ModuleLayer.CROSS_CUTTING: ['utils', 'common', 'shared', 'helpers', 'decorators', 'middleware', 'logging', 'exceptions', 'constants']
    }

    def __init__(self, logger: logging.Logger, project_root: Optional[Path] = None):
        self.logger = logger
        self.project_root = project_root or Path.cwd()
        self.graph = DependencyGraph()
        self._module_to_file: Dict[str, Path] = {}
        self._class_to_module: Dict[str, str] = {}
        self._function_to_module: Dict[str, str] = {}

    def build(self, target_path: Path) -> DependencyGraph:
        self.logger.info("开始构建依赖关系图...")

        py_files = list(target_path.rglob("*.py")) if target_path.is_dir() else [target_path]

        for py_file in py_files:
            self._process_file(py_file, target_path)

        self._resolve_symbol_references()

        self.logger.info(f"依赖图构建完成: {len(self.graph.nodes)} 个模块, {len(self.graph.edges)} 条依赖")
        return self.graph

    def _process_file(self, py_file: Path, root_path: Path) -> None:
        try:
            module_name = self._get_module_name(py_file, root_path)

            node = DependencyNode(
                module_name=module_name,
                file_path=str(py_file),
                is_test=self._is_test_file(py_file),
                layer=self._determine_layer(py_file, module_name)
            )

            with open(py_file, 'r', encoding='utf-8') as f:
                source = f.read()
            node.lines_of_code = len(source.split('\n'))
            tree = ast.parse(source)

            self._extract_imports(py_file, tree, module_name, node)
            self._extract_classes_and_functions(tree, node, module_name)
            self._extract_inheritance(py_file, tree, module_name)
            self._extract_composition(py_file, tree, module_name)
            self._extract_type_hints(py_file, tree, module_name)
            self._extract_decorators(py_file, tree, module_name)
            self._extract_function_calls(py_file, tree, module_name)
            self._extract_exports(tree, node)

            self.graph.add_node(node)
            self._module_to_file[module_name] = py_file

        except Exception as e:
            self.logger.warning(f"处理文件失败 {py_file}: {e}")

    def _get_module_name(self, py_file: Path, root_path: Path) -> str:
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

    def _is_test_file(self, py_file: Path) -> bool:
        path_str = str(py_file).lower()
        return any(kw in path_str for kw in ['test', 'tests', '_test.py', 'test_', 'spec_', '_spec.py'])

    def _determine_layer(self, py_file: Path, module_name: str) -> ModuleLayer:
        path_parts = py_file.parts
        module_lower = module_name.lower()

        for layer, indicators in self.LAYER_INDICATORS.items():
            for indicator in indicators:
                if indicator in module_lower:
                    return layer
                if indicator in path_parts:
                    return layer

        return ModuleLayer.UNKNOWN

    def _extract_imports(
        self,
        py_file: Path,
        tree: ast.AST,
        module_name: str,
        node: DependencyNode
    ) -> None:
        for ast_node in ast.walk(tree):
            if isinstance(ast_node, ast.Import):
                for alias in ast_node.names:
                    is_external = self._is_external_module(alias.name)
                    edge = DependencyEdge(
                        source=module_name,
                        target=alias.name,
                        dependency_type=DependencyType.IMPORT,
                        line_number=ast_node.lineno,
                        details=f"import {alias.name}",
                        is_internal=not is_external
                    )
                    self.graph.add_edge(edge)
                    node.dependencies.add(alias.name)
                    node.imports.append(alias.name)

            elif isinstance(ast_node, ast.ImportFrom):
                if ast_node.module:
                    is_external = self._is_external_module(ast_node.module)
                    for alias in ast_node.names:
                        edge = DependencyEdge(
                            source=module_name,
                            target=ast_node.module,
                            dependency_type=DependencyType.FROM_IMPORT,
                            line_number=ast_node.lineno,
                            details=f"from {ast_node.module} import {alias.name}",
                            is_internal=not is_external
                        )
                        self.graph.add_edge(edge)
                        node.dependencies.add(ast_node.module)
                        node.imports.append(ast_node.module)

                        if alias.name != '*':
                            node.imported_symbols[alias.name] = ast_node.module

    def _extract_classes_and_functions(
        self,
        tree: ast.AST,
        node: DependencyNode,
        module_name: str
    ) -> None:
        for ast_node in ast.walk(tree):
            if isinstance(ast_node, ast.ClassDef):
                node.classes.append(ast_node.name)
                self._class_to_module[ast_node.name] = module_name

                is_abstract = any(
                    (isinstance(d, ast.Name) and d.id == 'abstractmethod') or
                    (isinstance(d, ast.Attribute) and d.attr == 'abstractmethod')
                    for item in ast_node.body if isinstance(item, ast.FunctionDef)
                    for d in item.decorator_list
                ) or any(
                    kw in ast_node.name for kw in ['Abstract', 'Base', 'Interface', 'ABC']
                )

                if is_abstract:
                    node.abstract_classes += 1
                else:
                    node.concrete_classes += 1

            elif isinstance(ast_node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if ast_node.col_offset == 0:
                    node.functions.append(ast_node.name)
                    self._function_to_module[ast_node.name] = module_name

    def _extract_inheritance(self, py_file: Path, tree: ast.AST, module_name: str) -> None:
        for ast_node in ast.walk(tree):
            if isinstance(ast_node, ast.ClassDef):
                for base in ast_node.bases:
                    base_name = self._get_base_name(base)
                    if base_name and not self._is_builtin(base_name):
                        edge = DependencyEdge(
                            source=module_name,
                            target=base_name,
                            dependency_type=DependencyType.INHERITANCE,
                            line_number=ast_node.lineno,
                            details=f"class {ast_node.name} inherits from {base_name}",
                            weight=2.0
                        )
                        self.graph.add_edge(edge)

    def _extract_composition(self, py_file: Path, tree: ast.AST, module_name: str) -> None:
        for ast_node in ast.walk(tree):
            if isinstance(ast_node, ast.ClassDef):
                for item in ast_node.body:
                    if isinstance(item, ast.AnnAssign):
                        if item.annotation:
                            type_name = self._extract_type_name(item.annotation)
                            if type_name and not self._is_builtin(type_name):
                                edge = DependencyEdge(
                                    source=module_name,
                                    target=type_name,
                                    dependency_type=DependencyType.COMPOSITION,
                                    line_number=item.lineno,
                                    details=f"attribute {item.target.id if isinstance(item.target, ast.Name) else 'unknown'}: {type_name}",
                                    weight=1.5
                                )
                                self.graph.add_edge(edge)

                    if isinstance(item, ast.FunctionDef):
                        for arg in item.args.args:
                            if arg.annotation:
                                type_name = self._extract_type_name(arg.annotation)
                                if type_name and not self._is_builtin(type_name):
                                    edge = DependencyEdge(
                                        source=module_name,
                                        target=type_name,
                                        dependency_type=DependencyType.PARAMETER,
                                        line_number=item.lineno,
                                        details=f"parameter {arg.arg}: {type_name}"
                                    )
                                    self.graph.add_edge(edge)

                        if item.returns:
                            type_name = self._extract_type_name(item.returns)
                            if type_name and not self._is_builtin(type_name):
                                edge = DependencyEdge(
                                    source=module_name,
                                    target=type_name,
                                    dependency_type=DependencyType.RETURN_TYPE,
                                    line_number=item.lineno,
                                    details=f"return type: {type_name}"
                                )
                                self.graph.add_edge(edge)

    def _extract_type_hints(self, py_file: Path, tree: ast.AST, module_name: str) -> None:
        for ast_node in ast.walk(tree):
            if isinstance(ast_node, ast.AnnAssign):
                if ast_node.annotation:
                    self._process_type_annotation(ast_node.annotation, module_name, ast_node.lineno)

            if isinstance(ast_node, ast.FunctionDef):
                for arg in ast_node.args.args + ast_node.args.kwonlyargs:
                    if arg.annotation:
                        self._process_type_annotation(arg.annotation, module_name, ast_node.lineno)

                if ast_node.returns:
                    self._process_type_annotation(ast_node.returns, module_name, ast_node.lineno)

    def _process_type_annotation(self, annotation: ast.expr, module_name: str, line_no: int) -> None:
        for node in ast.walk(annotation):
            if isinstance(node, ast.Name):
                if not self._is_builtin(node.id):
                    edge = DependencyEdge(
                        source=module_name,
                        target=node.id,
                        dependency_type=DependencyType.TYPE_HINT,
                        line_number=line_no,
                        details=f"type hint: {node.id}"
                    )
                    self.graph.add_edge(edge)
            elif isinstance(node, ast.Attribute):
                type_name = self._extract_type_name(node)
                if type_name and not self._is_builtin(type_name):
                    edge = DependencyEdge(
                        source=module_name,
                        target=type_name,
                        dependency_type=DependencyType.TYPE_HINT,
                        line_number=line_no,
                        details=f"type hint: {type_name}"
                    )
                    self.graph.add_edge(edge)

    def _extract_decorators(self, py_file: Path, tree: ast.AST, module_name: str) -> None:
        for ast_node in ast.walk(tree):
            if isinstance(ast_node, (ast.FunctionDef, ast.ClassDef)):
                for decorator in ast_node.decorator_list:
                    decorator_name = self._get_decorator_name(decorator)
                    if decorator_name and not self._is_builtin(decorator_name):
                        edge = DependencyEdge(
                            source=module_name,
                            target=decorator_name,
                            dependency_type=DependencyType.DECORATOR,
                            line_number=ast_node.lineno,
                            details=f"decorator: {decorator_name}"
                        )
                        self.graph.add_edge(edge)

    def _get_decorator_name(self, decorator: ast.expr) -> Optional[str]:
        if isinstance(decorator, ast.Name):
            return decorator.id
        elif isinstance(decorator, ast.Attribute):
            return self._extract_type_name(decorator)
        elif isinstance(decorator, ast.Call):
            if isinstance(decorator.func, ast.Name):
                return decorator.func.id
            elif isinstance(decorator.func, ast.Attribute):
                return self._extract_type_name(decorator.func)
        return None

    def _extract_function_calls(self, py_file: Path, tree: ast.AST, module_name: str) -> None:
        for ast_node in ast.walk(tree):
            if isinstance(ast_node, ast.Call):
                if isinstance(ast_node.func, ast.Name):
                    func_name = ast_node.func.id
                    if not self._is_builtin(func_name):
                        edge = DependencyEdge(
                            source=module_name,
                            target=func_name,
                            dependency_type=DependencyType.FUNCTION_CALL,
                            line_number=ast_node.lineno,
                            details=f"function call: {func_name}",
                            weight=0.5
                        )
                        self.graph.add_edge(edge)

    def _extract_exports(self, tree: ast.AST, node: DependencyNode) -> None:
        for ast_node in ast.walk(tree):
            if isinstance(ast_node, ast.Assign):
                for target in ast_node.targets:
                    if isinstance(target, ast.Name) and not target.id.startswith('_'):
                        node.exported_symbols.add(target.id)

            if isinstance(ast_node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if not ast_node.name.startswith('_'):
                    node.exported_symbols.add(ast_node.name)

            if isinstance(ast_node, ast.ClassDef):
                if not ast_node.name.startswith('_'):
                    node.exported_symbols.add(ast_node.name)

    def _resolve_symbol_references(self) -> None:
        for node in self.graph.nodes.values():
            for symbol, source_module in node.imported_symbols.items():
                if source_module in self.graph.nodes:
                    source_node = self.graph.nodes[source_module]
                    if symbol in source_node.exported_symbols:
                        edge = DependencyEdge(
                            source=node.module_name,
                            target=f"{source_module}.{symbol}",
                            dependency_type=DependencyType.FROM_IMPORT,
                            details=f"symbol reference: {symbol}"
                        )
                        self.graph.add_edge(edge)

    def _get_base_name(self, base: ast.expr) -> Optional[str]:
        if isinstance(base, ast.Name):
            return base.id
        elif isinstance(base, ast.Attribute):
            if isinstance(base.value, ast.Name):
                return f"{base.value.id}.{base.attr}"
        return None

    def _extract_type_name(self, annotation: ast.expr) -> Optional[str]:
        if isinstance(annotation, ast.Name):
            return annotation.id
        elif isinstance(annotation, ast.Attribute):
            if isinstance(annotation.value, ast.Name):
                return f"{annotation.value.id}.{annotation.attr}"
        elif isinstance(annotation, ast.Subscript):
            if hasattr(ast, 'unparse'):
                return ast.unparse(annotation)
        return None

    def _is_external_module(self, module_name: str) -> bool:
        top_level = module_name.split('.')[0]
        if top_level in self.STANDARD_LIBRARY:
            return True
        if top_level in self.THIRD_PARTY_HINTS:
            return True
        return not any(
            module_name.startswith(m.split('.')[0])
            for m in self._module_to_file.keys()
        )

    def _is_builtin(self, name: str) -> bool:
        builtins = {
            'str', 'int', 'float', 'bool', 'list', 'dict', 'set', 'tuple',
            'None', 'Any', 'Optional', 'Union', 'List', 'Dict', 'Set', 'Tuple',
            'Callable', 'Type', 'ClassVar', 'Final', 'Literal', 'Annotated',
            'Protocol', 'TypedDict', 'NamedTuple', 'Generator', 'AsyncGenerator',
            'Iterator', 'AsyncIterator', 'Iterable', 'AsyncIterable', 'Sequence',
            'MutableSequence', 'Mapping', 'MutableMapping', 'Reversible',
            'SupportsAbs', 'SupportsBytes', 'SupportsComplex', 'SupportsFloat',
            'SupportsInt', 'SupportsRound', 'Counter', 'Deque', 'DefaultDict',
            'OrderedDict', 'ChainMap', 'Awaitable', 'Coroutine', 'AsyncContextManager',
            'ContextManager', 'AsyncGenerator', 'Path', 'PurePath', 'ABC', 'ABCMeta'
        }
        return name in builtins or name in self.STANDARD_LIBRARY


class CycleDetector:
    """循环依赖检测器 (深度优化版)"""

    def __init__(self, logger: logging.Logger):
        self.logger = logger
        self.cycles: List[CycleInfo] = []

    def detect(self, graph: DependencyGraph) -> List[CycleInfo]:
        self.logger.info("开始检测循环依赖...")

        self.cycles = []

        self._tarjan_scc(graph)

        self._assess_severity()
        self._generate_fix_suggestions()

        self.logger.info(f"检测到 {len(self.cycles)} 个循环依赖")
        return self.cycles

    def _tarjan_scc(self, graph: DependencyGraph) -> None:
        index_counter = [0]
        stack = []
        lowlinks = {}
        index = {}
        on_stack = {}
        sccs = []

        def strongconnect(node: str) -> None:
            index[node] = index_counter[0]
            lowlinks[node] = index_counter[0]
            index_counter[0] += 1
            stack.append(node)
            on_stack[node] = True

            for successor in graph.adjacency_list.get(node, set()):
                if successor not in index:
                    strongconnect(successor)
                    lowlinks[node] = min(lowlinks[node], lowlinks[successor])
                elif on_stack.get(successor, False):
                    lowlinks[node] = min(lowlinks[node], index[successor])

            if lowlinks[node] == index[node]:
                scc = []
                while True:
                    w = stack.pop()
                    on_stack[w] = False
                    scc.append(w)
                    if w == node:
                        break

                if len(scc) > 1:
                    sccs.append(scc)
                    self._extract_cycles_from_scc(scc, graph)

        for node in graph.nodes:
            if node not in index:
                strongconnect(node)

    def _extract_cycles_from_scc(self, scc: List[str], graph: DependencyGraph) -> None:
        if len(scc) == 2:
            cycle = scc + [scc[0]]
            self._add_cycle(cycle, graph)
        else:
            for i, node in enumerate(scc):
                for neighbor in graph.adjacency_list.get(node, set()):
                    if neighbor in scc:
                        try:
                            start_idx = scc.index(neighbor)
                            end_idx = scc.index(node)
                            if start_idx <= end_idx:
                                cycle = scc[start_idx:end_idx + 1] + [neighbor]
                                self._add_cycle(cycle, graph)
                        except ValueError:
                            pass

    def _add_cycle(self, cycle: List[str], graph: DependencyGraph) -> None:
        normalized = self._normalize_cycle(cycle)
        key = tuple(normalized)

        for existing in self.cycles:
            if tuple(self._normalize_cycle(existing.cycle_path)) == key:
                return

        cycle_info = CycleInfo(
            cycle_path=cycle,
            severity=CycleSeverity.MEDIUM,
            involved_modules=set(cycle),
            description=f"循环依赖: {' -> '.join(cycle)}"
        )
        self.cycles.append(cycle_info)

    def _normalize_cycle(self, cycle: List[str]) -> List[str]:
        if len(cycle) <= 1:
            return cycle

        without_last = cycle[:-1]
        min_idx = without_last.index(min(without_last))
        return without_last[min_idx:] + without_last[:min_idx] + [without_last[min_idx]]

    def _assess_severity(self) -> None:
        for cycle in self.cycles:
            length = len(cycle.cycle_path) - 1

            if length == 2:
                cycle.severity = CycleSeverity.LOW
                cycle.impact_score = 2.0
            elif length <= 4:
                cycle.severity = CycleSeverity.MEDIUM
                cycle.impact_score = 5.0
            elif length <= 6:
                cycle.severity = CycleSeverity.HIGH
                cycle.impact_score = 8.0
            else:
                cycle.severity = CycleSeverity.CRITICAL
                cycle.impact_score = 10.0

            cycle.description = f"循环依赖 ({cycle.severity.value}): {' -> '.join(cycle.cycle_path)}"

    def _generate_fix_suggestions(self) -> None:
        for cycle in self.cycles:
            if len(cycle.cycle_path) <= 3:
                cycle.suggested_fix = "提取公共接口到独立模块，让双方都依赖接口"
            elif len(cycle.cycle_path) <= 5:
                cycle.suggested_fix = "使用依赖注入或事件机制解耦模块"
            else:
                cycle.suggested_fix = "重构模块结构，考虑使用分层架构"


class CouplingAnalyzer:
    """耦合度分析器 (深度优化版)"""

    HIGH_COUPLING_THRESHOLD = 0.7
    LOW_COUPLING_THRESHOLD = 0.3
    TIGHT_COUPLING_COUNT = 10

    def __init__(self, logger: logging.Logger):
        self.logger = logger
        self.metrics: Dict[str, CouplingMetrics] = {}

    def analyze(self, graph: DependencyGraph) -> Dict[str, CouplingMetrics]:
        self.logger.info("开始分析耦合度...")

        depths = self._calculate_module_depths(graph)

        for module_name, node in graph.nodes.items():
            if node.is_external:
                continue

            metrics = CouplingMetrics(module_name=module_name)

            metrics.afferent_coupling = len([
                d for d in node.dependents
                if d in graph.nodes and not graph.nodes[d].is_external
            ])
            metrics.efferent_coupling = len([
                d for d in node.dependencies
                if d in graph.nodes and not graph.nodes[d].is_external
            ])

            metrics.total_coupling = metrics.afferent_coupling + metrics.efferent_coupling

            total_coupling = metrics.afferent_coupling + metrics.efferent_coupling
            if total_coupling > 0:
                metrics.instability = metrics.efferent_coupling / total_coupling
            else:
                metrics.instability = 0.0

            metrics.abstractness = self._calculate_abstractness(node)

            metrics.distance_from_main = abs(metrics.abstractness + metrics.instability - 1)

            metrics.normalized_distance = metrics.distance_from_main / 1.414

            metrics.fan_in = metrics.afferent_coupling
            metrics.fan_out = metrics.efferent_coupling

            metrics.depth = depths.get(module_name, 0)

            metrics.dependency_weight = self._calculate_dependency_weight(module_name, graph)

            metrics.coupling_level = self._determine_coupling_level(metrics)

            self.metrics[module_name] = metrics

        self.logger.info(f"耦合度分析完成: {len(self.metrics)} 个模块")
        return self.metrics

    def _calculate_module_depths(self, graph: DependencyGraph) -> Dict[str, int]:
        depths: Dict[str, int] = {}

        roots = [
            node for node in graph.nodes
            if not any(
                node in graph.adjacency_list.get(other, set())
                for other in graph.nodes
            )
        ]

        for root in roots:
            self._bfs_depth(root, graph, depths)

        return depths

    def _bfs_depth(self, start: str, graph: DependencyGraph, depths: Dict[str, int]) -> None:
        queue = deque([(start, 0)])
        visited = set()

        while queue:
            node, depth = queue.popleft()

            if node in visited:
                continue
            visited.add(node)

            if node not in depths or depths[node] < depth:
                depths[node] = depth

            for neighbor in graph.adjacency_list.get(node, set()):
                if neighbor not in visited:
                    queue.append((neighbor, depth + 1))

    def _calculate_abstractness(self, node: DependencyNode) -> float:
        total_classes = node.abstract_classes + node.concrete_classes
        if total_classes == 0:
            return 0.0

        return node.abstract_classes / total_classes

    def _calculate_dependency_weight(self, module_name: str, graph: DependencyGraph) -> float:
        weight = 0.0

        for edge in graph.edges:
            if edge.source == module_name:
                weight += edge.weight

        return weight

    def _determine_coupling_level(self, metrics: CouplingMetrics) -> CouplingLevel:
        if metrics.total_coupling == 0:
            return CouplingLevel.NONE

        if metrics.total_coupling > self.TIGHT_COUPLING_COUNT:
            return CouplingLevel.TIGHT

        if metrics.instability > self.HIGH_COUPLING_THRESHOLD:
            return CouplingLevel.TIGHT
        elif metrics.instability < self.LOW_COUPLING_THRESHOLD:
            return CouplingLevel.LOOSE
        else:
            return CouplingLevel.MEDIUM

    def get_highly_coupled_modules(self, threshold: int = 10) -> List[Tuple[str, int]]:
        coupled = [
            (name, m.total_coupling)
            for name, m in self.metrics.items()
        ]
        return sorted(coupled, key=lambda x: x[1], reverse=True)[:threshold]

    def get_unstable_modules(self, threshold: float = 0.8) -> List[Tuple[str, float]]:
        unstable = [
            (name, m.instability)
            for name, m in self.metrics.items()
            if m.instability > threshold
        ]
        return sorted(unstable, key=lambda x: x[1], reverse=True)

    def get_painful_modules(self) -> List[Tuple[str, float]]:
        painful = [
            (name, m.distance_from_main)
            for name, m in self.metrics.items()
            if m.distance_from_main > 0.5
        ]
        return sorted(painful, key=lambda x: x[1], reverse=True)


class LayerAnalyzer:
    """分层架构分析器"""

    LAYER_ORDER = {
        ModuleLayer.PRESENTATION: 1,
        ModuleLayer.APPLICATION: 2,
        ModuleLayer.DOMAIN: 3,
        ModuleLayer.INFRASTRUCTURE: 4,
        ModuleLayer.CROSS_CUTTING: 0,
        ModuleLayer.UNKNOWN: -1
    }

    def __init__(self, logger: logging.Logger):
        self.logger = logger
        self.layer_info: Dict[str, LayerInfo] = {}

    def analyze(self, graph: DependencyGraph) -> Dict[str, LayerInfo]:
        self.logger.info("开始分层架构分析...")

        layer_modules: Dict[ModuleLayer, List[str]] = defaultdict(list)

        for module_name, node in graph.nodes.items():
            if not node.is_external:
                layer_modules[node.layer].append(module_name)

        for layer, modules in layer_modules.items():
            info = LayerInfo(layer=layer, modules=modules)

            incoming = 0
            outgoing = 0
            violations = []

            for module in modules:
                for dep in graph.adjacency_list.get(module, set()):
                    if dep in graph.nodes:
                        dep_layer = graph.nodes[dep].layer
                        if self._is_layer_violation(layer, dep_layer):
                            violations.append(f"{module} -> {dep} ({layer.value} -> {dep_layer.value})")
                        outgoing += 1

                for dependent in graph.reverse_adjacency.get(module, set()):
                    if dependent in graph.nodes:
                        incoming += 1

            info.incoming_dependencies = incoming
            info.outgoing_dependencies = outgoing
            info.violations = violations

            total = incoming + outgoing
            info.stability = incoming / total if total > 0 else 0.0

            self.layer_info[layer.value] = info

        self.logger.info(f"分层分析完成: {len(self.layer_info)} 个层")
        return self.layer_info

    def _is_layer_violation(self, source_layer: ModuleLayer, target_layer: ModuleLayer) -> bool:
        if source_layer == ModuleLayer.CROSS_CUTTING or target_layer == ModuleLayer.CROSS_CUTTING:
            return False

        if source_layer == ModuleLayer.UNKNOWN or target_layer == ModuleLayer.UNKNOWN:
            return False

        source_order = self.LAYER_ORDER.get(source_layer, -1)
        target_order = self.LAYER_ORDER.get(target_layer, -1)

        return source_order < target_order and source_order > 0 and target_order > 0


class ArchitectureAnalyzer:
    """架构健康度分析器"""

    def __init__(self, logger: logging.Logger):
        self.logger = logger
        self.metrics = ArchitectureMetrics()

    def analyze(
        self,
        graph: DependencyGraph,
        cycles: List[CycleInfo],
        coupling_metrics: Dict[str, CouplingMetrics],
        layer_info: Dict[str, LayerInfo]
    ) -> ArchitectureMetrics:
        self.logger.info("开始架构健康度分析...")

        self.metrics.total_modules = len([n for n in graph.nodes.values() if not n.is_external])
        self.metrics.total_dependencies = len([e for e in graph.edges if e.is_internal])

        if coupling_metrics:
            self.metrics.average_coupling = sum(
                m.total_coupling for m in coupling_metrics.values()
            ) / len(coupling_metrics)
            self.metrics.average_instability = sum(
                m.instability for m in coupling_metrics.values()
            ) / len(coupling_metrics)
            self.metrics.average_abstractness = sum(
                m.abstractness for m in coupling_metrics.values()
            ) / len(coupling_metrics)

        self.metrics.cycle_count = len(cycles)

        self.metrics.layer_violation_count = sum(
            len(info.violations) for info in layer_info.values()
        )

        self.metrics.modularity_index = self._calculate_modularity_index(graph)

        self.metrics.dependency_complexity = self._calculate_dependency_complexity(graph)

        self.metrics.architecture_debt_score = self._calculate_architecture_debt(
            cycles, coupling_metrics, layer_info
        )

        self.metrics.health_status = self._determine_health_status()

        return self.metrics

    def _calculate_modularity_index(self, graph: DependencyGraph) -> float:
        if not graph.nodes:
            return 1.0

        internal_nodes = [n for n in graph.nodes.values() if not n.is_external]
        if not internal_nodes:
            return 1.0

        total_possible = len(internal_nodes) * (len(internal_nodes) - 1) / 2
        if total_possible == 0:
            return 1.0

        actual_edges = len([e for e in graph.edges if e.is_internal])

        return 1.0 - (actual_edges / total_possible) if total_possible > 0 else 1.0

    def _calculate_dependency_complexity(self, graph: DependencyGraph) -> float:
        if not graph.edges:
            return 0.0

        edge_type_counts: Dict[DependencyType, int] = defaultdict(int)
        for edge in graph.edges:
            edge_type_counts[edge.dependency_type] += 1

        complexity_weights = {
            DependencyType.INHERITANCE: 2.0,
            DependencyType.COMPOSITION: 1.5,
            DependencyType.AGGREGATION: 1.2,
            DependencyType.IMPORT: 0.5,
            DependencyType.FROM_IMPORT: 0.5,
            DependencyType.PARAMETER: 0.8,
            DependencyType.RETURN_TYPE: 0.8,
            DependencyType.TYPE_HINT: 0.3,
            DependencyType.DECORATOR: 0.5,
            DependencyType.FUNCTION_CALL: 0.2
        }

        total_complexity = sum(
            count * complexity_weights.get(dt, 1.0)
            for dt, count in edge_type_counts.items()
        )

        return total_complexity / len(graph.edges)

    def _calculate_architecture_debt(
        self,
        cycles: List[CycleInfo],
        coupling_metrics: Dict[str, CouplingMetrics],
        layer_info: Dict[str, LayerInfo]
    ) -> float:
        debt = 0.0

        for cycle in cycles:
            debt += cycle.impact_score

        for metrics in coupling_metrics.values():
            if metrics.distance_from_main > 0.7:
                debt += 3.0
            elif metrics.distance_from_main > 0.5:
                debt += 1.5

            if metrics.total_coupling > 15:
                debt += 2.0

        for info in layer_info.values():
            debt += len(info.violations) * 2.0

        return debt

    def _determine_health_status(self) -> ArchitectureHealth:
        debt = self.metrics.architecture_debt_score
        cycles = self.metrics.cycle_count
        violations = self.metrics.layer_violation_count

        if debt == 0 and cycles == 0 and violations == 0:
            return ArchitectureHealth.EXCELLENT
        elif debt < 10 and cycles <= 2 and violations <= 2:
            return ArchitectureHealth.GOOD
        elif debt < 30 and cycles <= 5 and violations <= 5:
            return ArchitectureHealth.FAIR
        elif debt < 50 and cycles <= 10:
            return ArchitectureHealth.POOR
        else:
            return ArchitectureHealth.CRITICAL


class DependencyAnalyzer:
    """依赖关系分析器主类 (深度优化版)"""

    def __init__(
        self,
        project_path: Optional[Path] = None,
        logger: Optional[logging.Logger] = None
    ):
        self.project_path = project_path or Path.cwd()
        self.logger = logger or self._setup_logger()

        self.graph_builder = DependencyGraphBuilder(self.logger, self.project_path)
        self.cycle_detector = CycleDetector(self.logger)
        self.coupling_analyzer = CouplingAnalyzer(self.logger)
        self.layer_analyzer = LayerAnalyzer(self.logger)
        self.architecture_analyzer = ArchitectureAnalyzer(self.logger)

        self._graph: Optional[DependencyGraph] = None
        self._cycles: List[CycleInfo] = []
        self._coupling_metrics: Dict[str, CouplingMetrics] = {}
        self._layer_info: Dict[str, LayerInfo] = {}
        self._architecture_metrics: Optional[ArchitectureMetrics] = None

    def _setup_logger(self) -> logging.Logger:
        logger = logging.getLogger("DependencyAnalyzer")
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

    def analyze(self, target_path: Optional[Path] = None) -> DependencyReport:
        self.logger.info("开始依赖关系深度分析...")

        target = target_path or self.project_path

        self._graph = self.graph_builder.build(target)
        self._cycles = self.cycle_detector.detect(self._graph)
        self._coupling_metrics = self.coupling_analyzer.analyze(self._graph)
        self._layer_info = self.layer_analyzer.analyze(self._graph)
        self._architecture_metrics = self.architecture_analyzer.analyze(
            self._graph, self._cycles, self._coupling_metrics, self._layer_info
        )

        summary = self._build_summary()
        recommendations = self._generate_recommendations()

        return DependencyReport(
            timestamp=datetime.now().isoformat(),
            project_path=str(target),
            graph=self._graph,
            cycles=self._cycles,
            coupling_metrics=self._coupling_metrics,
            layer_analysis=self._layer_info,
            architecture_metrics=self._architecture_metrics,
            summary=summary,
            recommendations=recommendations
        )

    def _build_summary(self) -> Dict[str, Any]:
        cycle_severity_counts = defaultdict(int)
        for cycle in self._cycles:
            cycle_severity_counts[cycle.severity.value] += 1

        coupling_level_counts = defaultdict(int)
        for metrics in self._coupling_metrics.values():
            coupling_level_counts[metrics.coupling_level.value] += 1

        layer_module_counts = {
            layer: len(info.modules)
            for layer, info in self._layer_info.items()
        }

        return {
            "total_modules": self._architecture_metrics.total_modules,
            "total_dependencies": self._architecture_metrics.total_dependencies,
            "cycle_count": len(self._cycles),
            "cycle_severity_breakdown": dict(cycle_severity_counts),
            "coupling_level_breakdown": dict(coupling_level_counts),
            "layer_module_counts": layer_module_counts,
            "layer_violation_count": self._architecture_metrics.layer_violation_count,
            "average_instability": self._architecture_metrics.average_instability,
            "average_abstractness": self._architecture_metrics.average_abstractness,
            "modularity_index": self._architecture_metrics.modularity_index,
            "architecture_debt_score": self._architecture_metrics.architecture_debt_score,
            "health_status": self._architecture_metrics.health_status.value,
            "highly_coupled_modules": [
                {"module": m, "total_coupling": c}
                for m, c in self.coupling_analyzer.get_highly_coupled_modules(5)
            ],
            "unstable_modules": [
                {"module": m, "instability": i}
                for m, i in self.coupling_analyzer.get_unstable_modules(0.8)
            ],
            "painful_modules": [
                {"module": m, "distance": d}
                for m, d in self.coupling_analyzer.get_painful_modules()[:5]
            ]
        }

    def _generate_recommendations(self) -> List[Dict[str, Any]]:
        recommendations = []

        if self._cycles:
            critical_cycles = [c for c in self._cycles if c.severity == CycleSeverity.CRITICAL]
            if critical_cycles:
                recommendations.append({
                    "priority": "critical",
                    "category": "cycle",
                    "title": "消除严重循环依赖",
                    "description": f"发现 {len(critical_cycles)} 个严重循环依赖，优先处理",
                    "affected_modules": list(set(
                        m for c in critical_cycles for m in c.involved_modules
                    )),
                    "suggested_actions": [
                        "提取公共接口到独立模块",
                        "使用依赖注入解耦",
                        "考虑事件驱动架构"
                    ]
                })

            other_cycles = [c for c in self._cycles if c.severity != CycleSeverity.CRITICAL]
            if other_cycles:
                recommendations.append({
                    "priority": "high",
                    "category": "cycle",
                    "title": "消除循环依赖",
                    "description": f"发现 {len(other_cycles)} 个循环依赖需要处理",
                    "affected_modules": list(set(
                        m for c in other_cycles for m in c.involved_modules
                    )),
                    "suggested_actions": [
                        "重构模块依赖关系",
                        "引入中介模块"
                    ]
                })

        highly_coupled = self.coupling_analyzer.get_highly_coupled_modules(3)
        for module, coupling in highly_coupled:
            if coupling > 15:
                recommendations.append({
                    "priority": "high",
                    "category": "coupling",
                    "title": f"降低模块 '{module}' 的耦合度",
                    "description": f"模块耦合度为 {coupling}，过高",
                    "affected_modules": [module],
                    "suggested_actions": [
                        "拆分模块职责",
                        "引入接口抽象",
                        "使用依赖注入"
                    ]
                })

        painful = self.coupling_analyzer.get_painful_modules()[:3]
        for module, distance in painful:
            if distance > 0.7:
                recommendations.append({
                    "priority": "medium",
                    "category": "architecture",
                    "title": f"优化模块 '{module}' 的架构位置",
                    "description": f"模块距离主序列 {distance:.2f}，需要调整抽象度或稳定性",
                    "affected_modules": [module],
                    "suggested_actions": [
                        "增加抽象接口",
                        "减少外部依赖",
                        "调整模块职责"
                    ]
                })

        layer_violations = []
        for layer, info in self._layer_info.items():
            layer_violations.extend(info.violations)

        if layer_violations:
            recommendations.append({
                "priority": "medium",
                "category": "layer",
                "title": "修复分层架构违规",
                "description": f"发现 {len(layer_violations)} 处分层违规",
                "violations": layer_violations[:5],
                "suggested_actions": [
                    "确保依赖方向正确（上层依赖下层）",
                    "使用接口隔离层间依赖",
                    "考虑引入防腐层"
                ]
            })

        return recommendations

    def print_report(self, report: DependencyReport) -> None:
        print("\n" + "=" * 80)
        print("依赖关系分析报告 (深度优化版)")
        print("=" * 80)
        print(f"项目路径: {report.project_path}")
        print(f"分析时间: {report.timestamp}")

        arch = report.architecture_metrics
        print(f"\n架构健康度: {arch.health_status.value.upper()}")
        print(f"模块总数: {arch.total_modules}")
        print(f"依赖总数: {arch.total_dependencies}")
        print(f"架构债务评分: {arch.architecture_debt_score:.1f}")
        print(f"模块化指数: {arch.modularity_index:.2f}")

        print("\n" + "-" * 80)
        print("循环依赖")
        print("-" * 80)

        if report.cycles:
            print(f"发现 {len(report.cycles)} 个循环依赖:")
            for cycle in report.cycles[:10]:
                severity_icon = {
                    CycleSeverity.CRITICAL: "🔴",
                    CycleSeverity.HIGH: "🟠",
                    CycleSeverity.MEDIUM: "🟡",
                    CycleSeverity.LOW: "🔵"
                }.get(cycle.severity, "⚪")
                print(f"  {severity_icon} [{cycle.severity.value.upper()}] {' -> '.join(cycle.cycle_path)}")
                if cycle.suggested_fix:
                    print(f"      建议: {cycle.suggested_fix}")

            if len(report.cycles) > 10:
                print(f"  ... 还有 {len(report.cycles) - 10} 个循环未显示")
        else:
            print("✅ 未发现循环依赖")

        print("\n" + "-" * 80)
        print("耦合度分析")
        print("-" * 80)

        coupling_breakdown = report.summary.get("coupling_level_breakdown", {})
        for level, count in coupling_breakdown.items():
            icon = {
                CouplingLevel.TIGHT.value: "🔴",
                CouplingLevel.MEDIUM.value: "🟡",
                CouplingLevel.LOOSE.value: "🟢",
                CouplingLevel.NONE.value: "⚪"
            }.get(level, "⚪")
            print(f"  {icon} {level}: {count} 个模块")

        highly_coupled = report.summary.get("highly_coupled_modules", [])
        if highly_coupled:
            print("\n高耦合模块:")
            for item in highly_coupled[:5]:
                print(f"  - {item['module']}: 总耦合度 {item['total_coupling']}")

        print("\n" + "-" * 80)
        print("分层架构分析")
        print("-" * 80)

        for layer, info in report.layer_analysis.items():
            violation_count = len(info.violations)
            status = "✅" if violation_count == 0 else f"⚠️ {violation_count} 违规"
            print(f"  {info.layer}: {len(info.modules)} 个模块 {status}")

        print("\n" + "-" * 80)
        print("改进建议")
        print("-" * 80)

        if report.recommendations:
            for i, rec in enumerate(report.recommendations[:10], 1):
                priority_icon = {
                    "critical": "🔴",
                    "high": "🟠",
                    "medium": "🟡",
                    "low": "🔵"
                }.get(rec.get("priority", "medium"), "⚪")
                print(f"  {i}. {priority_icon} [{rec.get('priority', 'medium').upper()}] {rec.get('title', '')}")
                print(f"     {rec.get('description', '')}")
        else:
            print("  ✅ 依赖关系良好，无需改进")

    def save_report(self, report: DependencyReport, output_path: str) -> None:
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)

        with open(path, 'w', encoding='utf-8') as f:
            json.dump(report.to_dict(), f, indent=2, ensure_ascii=False)

        self.logger.info(f"报告已保存: {path}")

    def export_graph_dot(self, output_path: str) -> None:
        if not self._graph:
            self.logger.warning("请先执行分析")
            return

        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)

        lines = ['digraph dependencies {']
        lines.append('    rankdir=LR;')
        lines.append('    node [shape=box];')
        lines.append('    splines=ortho;')

        layer_colors = {
            ModuleLayer.PRESENTATION: 'lightblue',
            ModuleLayer.APPLICATION: 'lightgreen',
            ModuleLayer.DOMAIN: 'lightyellow',
            ModuleLayer.INFRASTRUCTURE: 'lightcoral',
            ModuleLayer.CROSS_CUTTING: 'lightgray',
            ModuleLayer.UNKNOWN: 'white'
        }

        for module_name, node in self._graph.nodes.items():
            safe_name = module_name.replace('.', '_')
            color = layer_colors.get(node.layer, 'white')
            lines.append(f'    "{safe_name}" [label="{module_name}", style=filled, fillcolor="{color}"];')

        for edge in self._graph.edges:
            safe_source = edge.source.replace('.', '_')
            safe_target = edge.target.replace('.', '_')
            style = 'solid' if edge.is_internal else 'dashed'
            lines.append(f'    "{safe_source}" -> "{safe_target}" [style={style}];')

        lines.append('}')

        with open(path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines))

        self.logger.info(f"DOT图已导出: {path}")


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(
        description="依赖关系分析器 (深度优化版)",
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
        "--coupling-analysis",
        action="store_true",
        help="仅分析耦合度"
    )
    parser.add_argument(
        "--layer-analysis",
        action="store_true",
        help="仅分析分层架构"
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

    logger = logging.getLogger("DependencyAnalyzer")
    logger.setLevel(logging.DEBUG if args.verbose else logging.INFO)

    analyzer = DependencyAnalyzer(
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

    health = report.architecture_metrics.health_status
    if health in (ArchitectureHealth.CRITICAL, ArchitectureHealth.POOR):
        return 2
    elif health == ArchitectureHealth.FAIR:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
