#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
架构检查脚本 - Sanliu 技能

检查三省六部项目的架构合规性，包括：
- 目录结构检查
- 文件命名规范
- 导入循环检查
- 依赖关系检查
- 配置文件检查
- SOLID原则检查（增强版）
- MVVM架构检查（增强版）
- DRY/KISS/YAGNI原则检查
- 架构分层检查
- 设计模式合规性检查

使用示例:
    python architecture_check.py
    python architecture_check.py --output json --output-file result.json
    python architecture_check.py --strict
    python architecture_check.py --verbose
    python architecture_check.py --version 1.0.0
"""

import os
import sys
import ast
import json
import argparse
import logging
import re
import hashlib
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple, Set, Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from collections import defaultdict
from abc import ABC, abstractmethod
from skillscripts.utils.path_config_manager import PathConfigManager


class CheckStatus(Enum):
    """检查状态枚举"""
    PASS = "pass"
    FAIL = "fail"
    WARNING = "warning"
    SKIP = "skip"


class IssueSeverity(Enum):
    """问题严重程度枚举"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass
class ArchitectureIssue:
    """架构问题数据类"""
    file_path: str
    issue_type: str
    description: str
    severity: IssueSeverity
    line_number: Optional[int] = None
    suggestion: str = ""
    principle: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "file_path": self.file_path,
            "issue_type": self.issue_type,
            "description": self.description,
            "severity": self.severity.value,
            "line_number": self.line_number,
            "suggestion": self.suggestion,
            "principle": self.principle
        }


@dataclass
class CheckResult:
    """检查结果数据类"""
    check_name: str
    status: CheckStatus
    issues: List[ArchitectureIssue] = field(default_factory=list)
    details: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "check_name": self.check_name,
            "status": self.status.value,
            "issues": [i.to_dict() for i in self.issues],
            "details": self.details
        }


@dataclass
class ArchitectureReport:
    """架构检查报告数据类"""
    timestamp: str
    project_root: str
    overall_passed: bool
    results: List[CheckResult]
    summary: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "timestamp": self.timestamp,
            "project_root": self.project_root,
            "overall_passed": self.overall_passed,
            "summary": self.summary,
            "results": [r.to_dict() for r in self.results]
        }


class SOLIDChecker:
    """SOLID原则检查器（增强版）"""

    SRP_THRESHOLDS = {
        "max_public_methods": 10,
        "max_method_categories": 3,
        "max_class_lines": 300,
        "max_dependencies": 5
    }

    OCP_PATTERNS = [
        ("type_check", r"if\s+\w+\.type\s*==", "类型检查条件"),
        ("isinstance_chain", r"isinstance\s*\([^)]+\)\s*(or|and)", "isinstance链式判断"),
        ("enum_switch", r"if\s+\w+\.kind\s*==", "枚举类型判断"),
    ]

    DIP_CONCRETE_PATTERNS = [
        "impl", "concrete", "service", "repository", "dao", "client"
    ]

    def __init__(self, logger: logging.Logger, thresholds: Optional[Dict] = None):
        self.logger = logger
        self.issues: List[ArchitectureIssue] = []
        self.thresholds = {**self.SRP_THRESHOLDS, **(thresholds or {})}
        self._class_info: Dict[str, Dict] = {}

    def check_single_responsibility(self, py_file: Path, tree: ast.AST, source: str) -> List[ArchitectureIssue]:
        """检查单一职责原则 (SRP) - 一个类应该只有一个引起变化的原因"""
        issues = []

        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                methods = [n for n in node.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]
                public_methods = [m for m in methods if not m.name.startswith('_')]

                if len(public_methods) > self.thresholds["max_public_methods"]:
                    issues.append(ArchitectureIssue(
                        file_path=str(py_file),
                        issue_type="SRP_VIOLATION",
                        description=f"类 '{node.name}' 有 {len(public_methods)} 个公共方法，可能违反单一职责原则",
                        severity=IssueSeverity.MEDIUM,
                        line_number=node.lineno,
                        suggestion="考虑将类拆分为多个更小的类，每个类只负责一个职责",
                        principle="SOLID-SRP"
                    ))

                method_categories = self._categorize_methods(methods)
                if len(method_categories) > self.thresholds["max_method_categories"]:
                    issues.append(ArchitectureIssue(
                        file_path=str(py_file),
                        issue_type="SRP_VIOLATION",
                        description=f"类 '{node.name}' 的方法涉及多个不同领域: {', '.join(method_categories.keys())}",
                        severity=IssueSeverity.MEDIUM,
                        line_number=node.lineno,
                        suggestion="考虑按职责拆分类，每个类专注于一个领域",
                        principle="SOLID-SRP"
                    ))

                dependencies = self._extract_dependencies(node, source)
                if len(dependencies) > self.thresholds["max_dependencies"]:
                    issues.append(ArchitectureIssue(
                        file_path=str(py_file),
                        issue_type="SRP_VIOLATION",
                        description=f"类 '{node.name}' 依赖了 {len(dependencies)} 个外部类，可能承担过多职责",
                        severity=IssueSeverity.MEDIUM,
                        line_number=node.lineno,
                        suggestion="减少外部依赖，考虑使用依赖注入或接口隔离",
                        principle="SOLID-SRP"
                    ))

                class_lines = self._count_class_lines(node, source)
                if class_lines > self.thresholds["max_class_lines"]:
                    issues.append(ArchitectureIssue(
                        file_path=str(py_file),
                        issue_type="SRP_VIOLATION",
                        description=f"类 '{node.name}' 有 {class_lines} 行代码，可能过大",
                        severity=IssueSeverity.LOW,
                        line_number=node.lineno,
                        suggestion="考虑拆分为多个更小的类",
                        principle="SOLID-SRP"
                    ))

        return issues

    def _extract_dependencies(self, node: ast.ClassDef, source: str) -> Set[str]:
        """提取类的依赖"""
        dependencies = set()
        for child in ast.walk(node):
            if isinstance(child, ast.Attribute):
                if isinstance(child.value, ast.Name):
                    if child.value.id not in ('self', 'cls'):
                        dependencies.add(child.value.id)
            elif isinstance(child, ast.Call):
                if isinstance(child.func, ast.Name):
                    if child.func.id[0].isupper():
                        dependencies.add(child.func.id)
        return dependencies

    def _count_class_lines(self, node: ast.ClassDef, source: str) -> int:
        """计算类的代码行数"""
        if hasattr(node, 'end_lineno') and node.end_lineno:
            return node.end_lineno - node.lineno
        return 0

    def _categorize_methods(self, methods: List) -> Dict[str, List[str]]:
        """将方法按功能分类"""
        categories = defaultdict(list)
        
        for method in methods:
            name = method.name.lower()
            
            if any(kw in name for kw in ['get', 'fetch', 'find', 'query', 'load', 'read']):
                categories['data_access'].append(method.name)
            elif any(kw in name for kw in ['save', 'create', 'update', 'delete', 'write', 'store']):
                categories['data_modification'].append(method.name)
            elif any(kw in name for kw in ['validate', 'check', 'verify']):
                categories['validation'].append(method.name)
            elif any(kw in name for kw in ['format', 'parse', 'convert', 'transform']):
                categories['transformation'].append(method.name)
            elif any(kw in name for kw in ['send', 'notify', 'emit', 'publish']):
                categories['communication'].append(method.name)
            elif any(kw in name for kw in ['calculate', 'compute', 'process']):
                categories['computation'].append(method.name)
            else:
                categories['other'].append(method.name)
        
        return {k: v for k, v in categories.items() if v}

    def check_open_closed(self, py_file: Path, tree: ast.AST, source: str) -> List[ArchitectureIssue]:
        """检查开闭原则 (OCP) - 软件实体应该对扩展开放，对修改关闭"""
        issues = []
        lines = source.split('\n')

        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                for child in ast.walk(node):
                    if isinstance(child, ast.If):
                        if isinstance(child.test, ast.Compare):
                            if hasattr(child.test, 'left') and isinstance(child.test.left, ast.Attribute):
                                if child.test.left.attr in ['type', 'kind', 'category', 'status']:
                                    issues.append(ArchitectureIssue(
                                        file_path=str(py_file),
                                        issue_type="OCP_VIOLATION",
                                        description=f"类 '{node.name}' 中存在基于类型判断的条件分支，可能违反开闭原则",
                                        severity=IssueSeverity.MEDIUM,
                                        line_number=child.lineno,
                                        suggestion="考虑使用多态或策略模式替代类型判断",
                                        principle="SOLID-OCP"
                                    ))
                                    break

                for pattern_name, pattern_regex, description in self.OCP_PATTERNS:
                    for i, line in enumerate(lines[child.lineno - 1:child.lineno + 10] if hasattr(child, 'lineno') else [], 1):
                        if re.search(pattern_regex, line):
                            issues.append(ArchitectureIssue(
                                file_path=str(py_file),
                                issue_type="OCP_VIOLATION",
                                description=f"发现{description}，可能违反开闭原则",
                                severity=IssueSeverity.MEDIUM,
                                line_number=child.lineno if hasattr(child, 'lineno') else i,
                                suggestion="使用多态、策略模式或工厂模式替代条件判断",
                                principle="SOLID-OCP"
                            ))
                            break

                method_changes = self._analyze_method_change_indicators(node)
                if method_changes:
                    issues.append(ArchitectureIssue(
                        file_path=str(py_file),
                        issue_type="OCP_VIOLATION",
                        description=f"类 '{node.name}' 的方法 {method_changes} 可能需要频繁修改",
                        severity=IssueSeverity.LOW,
                        line_number=node.lineno,
                        suggestion="考虑使用抽象基类或接口隔离变化点",
                        principle="SOLID-OCP"
                    ))

        return issues

    def _analyze_method_change_indicators(self, node: ast.ClassDef) -> List[str]:
        """分析方法中可能需要频繁修改的指示器"""
        change_indicators = []
        for method in node.body:
            if isinstance(method, ast.FunctionDef):
                for child in ast.walk(method):
                    if isinstance(child, ast.Constant):
                        if isinstance(child.value, str):
                            if any(kw in child.value.lower() for kw in ['type', 'kind', 'category']):
                                change_indicators.append(method.name)
                                break
        return change_indicators

    def check_liskov_substitution(self, py_file: Path, tree: ast.AST) -> List[ArchitectureIssue]:
        """检查里氏替换原则 (LSP) - 子类必须能够替换其基类"""
        issues = []

        class_methods: Dict[str, Dict[str, ast.FunctionDef]] = {}
        class_hierarchy: Dict[str, List[str]] = defaultdict(list)
        
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                methods = {}
                for item in node.body:
                    if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        methods[item.name] = item
                class_methods[node.name] = methods
                
                for base in node.bases:
                    if isinstance(base, ast.Name):
                        class_hierarchy[base.id].append(node.name)

        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                for base in node.bases:
                    if isinstance(base, ast.Name):
                        base_name = base.id
                        if base_name in class_methods:
                            base_methods = class_methods[base_name]
                            child_methods = class_methods.get(node.name, {})
                            
                            for method_name, base_method in base_methods.items():
                                if method_name in child_methods:
                                    child_method = child_methods[method_name]
                                    
                                    base_args = len(base_method.args.args)
                                    child_args = len(child_method.args.args)
                                    
                                    if child_args < base_args:
                                        issues.append(ArchitectureIssue(
                                            file_path=str(py_file),
                                            issue_type="LSP_VIOLATION",
                                            description=f"类 '{node.name}' 的方法 '{method_name}' 参数少于基类，违反里氏替换原则",
                                            severity=IssueSeverity.HIGH,
                                            line_number=child_method.lineno,
                                            suggestion="子类方法签名应与基类保持一致",
                                            principle="SOLID-LSP"
                                        ))

                                    base_return = self._get_return_type(base_method)
                                    child_return = self._get_return_type(child_method)
                                    if base_return and child_return and base_return != child_return:
                                        issues.append(ArchitectureIssue(
                                            file_path=str(py_file),
                                            issue_type="LSP_VIOLATION",
                                            description=f"类 '{node.name}' 的方法 '{method_name}' 返回类型与基类不一致",
                                            severity=IssueSeverity.MEDIUM,
                                            line_number=child_method.lineno,
                                            suggestion="子类返回类型应与基类兼容",
                                            principle="SOLID-LSP"
                                        ))

                                    base_exceptions = self._get_raised_exceptions(base_method)
                                    child_exceptions = self._get_raised_exceptions(child_method)
                                    new_exceptions = child_exceptions - base_exceptions
                                    if new_exceptions:
                                        issues.append(ArchitectureIssue(
                                            file_path=str(py_file),
                                            issue_type="LSP_VIOLATION",
                                            description=f"类 '{node.name}' 的方法 '{method_name}' 抛出了新的异常: {new_exceptions}",
                                            severity=IssueSeverity.MEDIUM,
                                            line_number=child_method.lineno,
                                            suggestion="子类不应抛出基类未声明的异常",
                                            principle="SOLID-LSP"
                                        ))

        return issues

    def _get_return_type(self, method: ast.FunctionDef) -> Optional[str]:
        """获取方法的返回类型注解"""
        if method.returns:
            if isinstance(method.returns, ast.Name):
                return method.returns.id
            elif isinstance(method.returns, ast.Constant):
                return str(method.returns.value)
        return None

    def _get_raised_exceptions(self, method: ast.FunctionDef) -> Set[str]:
        """获取方法抛出的异常"""
        exceptions = set()
        for node in ast.walk(method):
            if isinstance(node, ast.Raise):
                if isinstance(node.exc, ast.Call):
                    if isinstance(node.exc.func, ast.Name):
                        exceptions.add(node.exc.func.id)
                elif isinstance(node.exc, ast.Name):
                    exceptions.add(node.exc.id)
        return exceptions

    def check_interface_segregation(self, py_file: Path, tree: ast.AST) -> List[ArchitectureIssue]:
        """检查接口隔离原则 (ISP) - 客户端不应该依赖它不需要的接口"""
        issues = []

        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                methods = [n for n in node.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]
                
                abstract_methods = []
                for method in methods:
                    for decorator in method.decorator_list:
                        if isinstance(decorator, ast.Name) and decorator.id == 'abstractmethod':
                            abstract_methods.append(method.name)
                        elif isinstance(decorator, ast.Attribute) and decorator.attr == 'abstractmethod':
                            abstract_methods.append(method.name)

                if len(abstract_methods) > 7:
                    issues.append(ArchitectureIssue(
                        file_path=str(py_file),
                        issue_type="ISP_VIOLATION",
                        description=f"抽象类 '{node.name}' 有 {len(abstract_methods)} 个抽象方法，可能违反接口隔离原则",
                        severity=IssueSeverity.MEDIUM,
                        line_number=node.lineno,
                        suggestion="考虑将接口拆分为多个更小的专用接口",
                        principle="SOLID-ISP"
                    ))

                method_groups = self._group_methods_by_purpose(methods)
                if len(method_groups) > 2 and len(abstract_methods) > 3:
                    issues.append(ArchitectureIssue(
                        file_path=str(py_file),
                        issue_type="ISP_VIOLATION",
                        description=f"抽象类 '{node.name}' 的方法涉及多个目的: {list(method_groups.keys())}，建议拆分接口",
                        severity=IssueSeverity.MEDIUM,
                        line_number=node.lineno,
                        suggestion="按目的拆分为多个专用接口",
                        principle="SOLID-ISP"
                    ))

                fat_interface_methods = self._detect_fat_interface(node, tree)
                if fat_interface_methods:
                    issues.append(ArchitectureIssue(
                        file_path=str(py_file),
                        issue_type="ISP_VIOLATION",
                        description=f"类 '{node.name}' 可能实现了胖接口，包含不相关的方法: {fat_interface_methods}",
                        severity=IssueSeverity.LOW,
                        line_number=node.lineno,
                        suggestion="将不相关的方法分离到不同的接口中",
                        principle="SOLID-ISP"
                    ))

        return issues

    def _group_methods_by_purpose(self, methods: List) -> Dict[str, List[str]]:
        """按目的分组方法"""
        groups = defaultdict(list)
        for method in methods:
            name = method.name.lower()
            if any(kw in name for kw in ['get', 'fetch', 'find', 'query']):
                groups['query'].append(method.name)
            elif any(kw in name for kw in ['save', 'create', 'update', 'delete']):
                groups['command'].append(method.name)
            elif any(kw in name for kw in ['validate', 'check']):
                groups['validation'].append(method.name)
            elif any(kw in name for kw in ['handle', 'process']):
                groups['handler'].append(method.name)
            else:
                groups['other'].append(method.name)
        return dict(groups)

    def _detect_fat_interface(self, node: ast.ClassDef, tree: ast.AST) -> List[str]:
        """检测胖接口"""
        unrelated_methods = []
        method_names = [m.name for m in node.body if isinstance(m, ast.FunctionDef)]
        
        prefixes = set()
        for name in method_names:
            parts = name.split('_')
            if len(parts) > 1:
                prefixes.add(parts[0])
        
        if len(prefixes) > 2:
            for name in method_names:
                parts = name.split('_')
                if len(parts) > 1:
                    prefix_count = sum(1 for n in method_names if n.startswith(parts[0] + '_'))
                    if prefix_count == 1:
                        unrelated_methods.append(name)
        
        return unrelated_methods

    def check_dependency_inversion(self, py_file: Path, tree: ast.AST, source: str) -> List[ArchitectureIssue]:
        """检查依赖倒置原则 (DIP) - 高层模块不应该依赖低层模块"""
        issues = []

        concrete_imports = []
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                if node.module:
                    for alias in node.names:
                        module_lower = node.module.lower()
                        if any(kw in module_lower for kw in self.DIP_CONCRETE_PATTERNS):
                            if not alias.name.startswith('I') and not alias.name.startswith('Abstract'):
                                if not alias.name.startswith('_'):
                                    concrete_imports.append((node.lineno, alias.name, node.module))

        for line_no, import_name, module in concrete_imports:
            issues.append(ArchitectureIssue(
                file_path=str(py_file),
                issue_type="DIP_VIOLATION",
                description=f"可能直接依赖了具体实现 '{import_name}' (from {module})，建议依赖抽象",
                severity=IssueSeverity.LOW,
                line_number=line_no,
                suggestion="考虑通过依赖注入或抽象接口来解耦",
                principle="SOLID-DIP"
            ))

        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                high_level_indicators = self._is_high_level_module(node)
                if high_level_indicators:
                    concrete_deps = self._find_concrete_dependencies(node, tree)
                    for dep in concrete_deps:
                        issues.append(ArchitectureIssue(
                            file_path=str(py_file),
                            issue_type="DIP_VIOLATION",
                            description=f"高层模块 '{node.name}' 直接依赖具体实现 '{dep}'",
                            severity=IssueSeverity.MEDIUM,
                            line_number=node.lineno,
                            suggestion="通过接口或抽象类进行依赖",
                            principle="SOLID-DIP"
                        ))

        return issues

    def _is_high_level_module(self, node: ast.ClassDef) -> bool:
        """判断是否是高层模块"""
        high_level_keywords = ['Service', 'Manager', 'Controller', 'Handler', 'Processor', 'Coordinator']
        return any(kw in node.name for kw in high_level_keywords)

    def _find_concrete_dependencies(self, node: ast.ClassDef, tree: ast.AST) -> List[str]:
        """查找具体依赖"""
        concrete_deps = []
        for child in ast.walk(node):
            if isinstance(child, ast.Call):
                if isinstance(child.func, ast.Name):
                    name = child.func.id
                    if not name.startswith('I') and not name.startswith('Abstract'):
                        if name[0].isupper() and name not in ('List', 'Dict', 'Set', 'Tuple', 'Optional'):
                            concrete_deps.append(name)
        return concrete_deps

    def check_all_solid(self, py_file: Path) -> List[ArchitectureIssue]:
        """执行所有SOLID检查"""
        all_issues = []
        
        try:
            with open(py_file, 'r', encoding='utf-8') as f:
                source = f.read()
            tree = ast.parse(source)
            
            all_issues.extend(self.check_single_responsibility(py_file, tree, source))
            all_issues.extend(self.check_open_closed(py_file, tree, source))
            all_issues.extend(self.check_liskov_substitution(py_file, tree))
            all_issues.extend(self.check_interface_segregation(py_file, tree))
            all_issues.extend(self.check_dependency_inversion(py_file, tree, source))
            
        except Exception as e:
            self.logger.warning(f"SOLID检查失败 {py_file}: {e}")
        
        return all_issues


class MVVMChecker:
    """MVVM架构检查器（增强版）"""

    EXPECTED_STRUCTURE = {
        'model': ['models', 'entities', 'domain', 'stores'],
        'viewmodel': ['viewmodels', 'view_models', 'viewmodel', 'composables'],
        'view': ['views', 'components', 'pages', 'screens']
    }

    LAYER_DEPENDENCIES = {
        'view': ['viewmodel', 'model'],
        'viewmodel': ['model'],
        'model': []
    }

    FORBIDDEN_CROSS_LAYER = {
        'view': ['api', 'http', 'fetch', 'axios'],
        'model': ['render', 'display', 'show', 'hide', 'ui']
    }

    def __init__(self, logger: logging.Logger):
        self.logger = logger
        self.issues: List[ArchitectureIssue] = []
        self.path_manager = PathConfigManager(auto_detect=True)

    def check_structure(self, project_root: Path) -> List[ArchitectureIssue]:
        """检查MVVM目录结构"""
        issues = []
        
        frontend_path = self.path_manager.get_frontend_path() / 'src'
        if not frontend_path.exists():
            return issues

        found_layers = set()
        layer_paths = {}
        for layer, dirs in self.EXPECTED_STRUCTURE.items():
            for dir_name in dirs:
                layer_path = frontend_path / dir_name
                if layer_path.exists():
                    found_layers.add(layer)
                    layer_paths[layer] = layer_path
                    break

        missing_layers = set(self.EXPECTED_STRUCTURE.keys()) - found_layers
        if missing_layers:
            issues.append(ArchitectureIssue(
                file_path=str(frontend_path),
                issue_type="MVVM_STRUCTURE",
                description=f"缺少MVVM层目录: {', '.join(missing_layers)}",
                severity=IssueSeverity.MEDIUM,
                suggestion="创建缺失的MVVM层目录以保持架构清晰",
                principle="MVVM"
            ))

        for layer, path in layer_paths.items():
            file_count = len(list(path.rglob('*.*')))
            if file_count == 0:
                issues.append(ArchitectureIssue(
                    file_path=str(path),
                    issue_type="MVVM_EMPTY_LAYER",
                    description=f"MVVM层 '{layer}' 目录为空",
                    severity=IssueSeverity.LOW,
                    suggestion=f"在 {layer} 层添加相应的文件",
                    principle="MVVM"
                ))

        return issues

    def check_view_model_binding(self, ts_file: Path, content: str) -> List[ArchitectureIssue]:
        """检查View与ViewModel的绑定关系"""
        issues = []

        is_view = any(kw in str(ts_file).lower() for kw in ['view', 'component', 'page', 'screen'])
        is_viewmodel = any(kw in str(ts_file).lower() for kw in ['viewmodel', 'composable', 'store'])

        if is_view and not is_viewmodel:
            has_viewmodel_import = any(
                pattern in content 
                for pattern in ['ViewModel', 'viewModel', 'useViewModel', 'viewmodel', 'useStore', 'store']
            )
            
            has_business_logic = any(
                pattern in content 
                for pattern in ['fetch(', 'axios.', 'api.', 'http.', 'async (', 'async(', '.then(', '.catch(']
            )

            if has_business_logic and not has_viewmodel_import:
                issues.append(ArchitectureIssue(
                    file_path=str(ts_file),
                    issue_type="MVVM_VIOLATION",
                    description="View组件中包含业务逻辑，应移至ViewModel",
                    severity=IssueSeverity.HIGH,
                    suggestion="将API调用和业务逻辑移至ViewModel或Store，View只负责展示",
                    principle="MVVM"
                ))

            for pattern in self.FORBIDDEN_CROSS_LAYER.get('view', []):
                if pattern in content.lower():
                    if not has_viewmodel_import:
                        issues.append(ArchitectureIssue(
                            file_path=str(ts_file),
                            issue_type="MVVM_CROSS_LAYER",
                            description=f"View层直接使用了 '{pattern}'，违反MVVM分层原则",
                            severity=IssueSeverity.MEDIUM,
                            suggestion="通过ViewModel进行数据访问",
                            principle="MVVM"
                        ))
                        break

        if is_viewmodel:
            has_ui_logic = any(
                pattern in content 
                for pattern in ['document.', 'window.', 'DOM', 'render', 'template']
            )
            if has_ui_logic:
                issues.append(ArchitectureIssue(
                    file_path=str(ts_file),
                    issue_type="MVVM_VIEWMODEL_VIOLATION",
                    description="ViewModel中包含UI逻辑，应移至View",
                    severity=IssueSeverity.MEDIUM,
                    suggestion="ViewModel应只包含业务逻辑和状态管理",
                    principle="MVVM"
                ))

        return issues

    def check_model_purity(self, py_file: Path, tree: ast.AST, source: str) -> List[ArchitectureIssue]:
        """检查Model层的纯净性"""
        issues = []

        if 'model' in str(py_file).lower():
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    for method in node.body:
                        if isinstance(method, ast.FunctionDef):
                            method_source = ast.unparse(method) if hasattr(ast, 'unparse') else ''
                            
                            ui_patterns = ['print(', 'render', 'display', 'show_', 'hide_', 'alert', 'console.']
                            for pattern in ui_patterns:
                                if pattern.lower() in method_source.lower():
                                    issues.append(ArchitectureIssue(
                                        file_path=str(py_file),
                                        issue_type="MVVM_MODEL_VIOLATION",
                                        description=f"Model类 '{node.name}' 包含UI相关逻辑",
                                        severity=IssueSeverity.MEDIUM,
                                        line_number=method.lineno,
                                        suggestion="Model层应只包含数据和业务逻辑，不应包含UI逻辑",
                                        principle="MVVM"
                                    ))
                                    break

                            http_patterns = ['requests.', 'httpx.', 'aiohttp.', 'urllib.']
                            for pattern in http_patterns:
                                if pattern in method_source:
                                    issues.append(ArchitectureIssue(
                                        file_path=str(py_file),
                                        issue_type="MVVM_MODEL_VIOLATION",
                                        description=f"Model类 '{node.name}' 包含HTTP调用，应移至Repository或Service",
                                        severity=IssueSeverity.MEDIUM,
                                        line_number=method.lineno,
                                        suggestion="将HTTP调用移至Repository或Service层",
                                        principle="MVVM"
                                    ))
                                    break

        return issues

    def check_data_binding_patterns(self, vue_file: Path, content: str) -> List[ArchitectureIssue]:
        """检查Vue组件的数据绑定模式"""
        issues = []

        if not vue_file.suffix == '.vue':
            return issues

        has_reactive_data = 'ref(' in content or 'reactive(' in content or 'computed(' in content
        has_template_binding = 'v-model' in content or 'v-bind' in content or '{{' in content

        if has_template_binding and not has_reactive_data:
            issues.append(ArchitectureIssue(
                file_path=str(vue_file),
                issue_type="MVVM_BINDING",
                description="Vue组件有模板绑定但缺少响应式数据定义",
                severity=IssueSeverity.LOW,
                suggestion="使用ref或reactive定义响应式数据",
                principle="MVVM"
            ))

        has_watch = 'watch(' in content or 'watchEffect(' in content
        has_computed = 'computed(' in content

        if has_watch and not has_computed:
            lines = content.split('\n')
            watch_count = sum(1 for line in lines if 'watch(' in line)
            if watch_count > 3:
                issues.append(ArchitectureIssue(
                    file_path=str(vue_file),
                    issue_type="MVVM_COMPLEXITY",
                    description=f"Vue组件有 {watch_count} 个watch，可能过于复杂",
                    severity=IssueSeverity.LOW,
                    suggestion="考虑使用computed属性简化逻辑",
                    principle="MVVM"
                ))

        return issues

    def check_all_mvvm(self, project_root: Path) -> List[ArchitectureIssue]:
        """执行所有MVVM检查"""
        all_issues = []
        
        all_issues.extend(self.check_structure(project_root))
        
        frontend_src = self.path_manager.get_frontend_path() / 'src'
        if frontend_src.exists():
            for ts_file in frontend_src.rglob('*.ts'):
                try:
                    with open(ts_file, 'r', encoding='utf-8') as f:
                        content = f.read()
                    all_issues.extend(self.check_view_model_binding(ts_file, content))
                except Exception as e:
                    self.logger.warning(f"MVVM检查失败 {ts_file}: {e}")

            for vue_file in frontend_src.rglob('*.vue'):
                try:
                    with open(vue_file, 'r', encoding='utf-8') as f:
                        content = f.read()
                    all_issues.extend(self.check_view_model_binding(vue_file, content))
                    all_issues.extend(self.check_data_binding_patterns(vue_file, content))
                except Exception as e:
                    self.logger.warning(f"MVVM检查失败 {vue_file}: {e}")

        backend_app = self.path_manager.get_backend_path() / 'app'
        if backend_app.exists():
            for py_file in backend_app.rglob('*.py'):
                try:
                    with open(py_file, 'r', encoding='utf-8') as f:
                        source = f.read()
                    tree = ast.parse(source)
                    all_issues.extend(self.check_model_purity(py_file, tree, source))
                except Exception as e:
                    self.logger.warning(f"MVVM检查失败 {py_file}: {e}")

        return all_issues


class MVCChecker:
    """MVC架构检查器"""

    EXPECTED_STRUCTURE = {
        'model': ['models', 'entities', 'domain', 'stores'],
        'view': ['views', 'templates', 'pages', 'screens'],
        'controller': ['controllers', 'routes', 'api', 'endpoints', 'handlers']
    }

    LAYER_DEPENDENCIES = {
        'view': ['controller'],
        'controller': ['model'],
        'model': []
    }

    FORBIDDEN_CROSS_LAYER = {
        'model': ['render', 'template', 'response', 'request', 'session'],
        'view': ['query', 'execute', 'save', 'delete', 'update', 'create', 'database', 'db_']
    }

    def __init__(self, logger: logging.Logger):
        self.logger = logger
        self.issues: List[ArchitectureIssue] = []
        self.path_manager = PathConfigManager()

    def check_structure(self, project_root: Path) -> List[ArchitectureIssue]:
        """检查MVC目录结构"""
        issues = []
        
        backend_path = self.path_manager.get_backend_path() / 'app'
        if not backend_path.exists():
            return issues

        found_layers = set()
        layer_paths = {}
        for layer, dirs in self.EXPECTED_STRUCTURE.items():
            for dir_name in dirs:
                layer_path = backend_path / dir_name
                if layer_path.exists():
                    found_layers.add(layer)
                    layer_paths[layer] = layer_path
                    break

        missing_layers = set(self.EXPECTED_STRUCTURE.keys()) - found_layers
        if missing_layers:
            issues.append(ArchitectureIssue(
                file_path=str(backend_path),
                issue_type="MVC_STRUCTURE",
                description=f"缺少MVC层目录: {', '.join(missing_layers)}",
                severity=IssueSeverity.MEDIUM,
                suggestion="创建缺失的MVC层目录以保持架构清晰",
                principle="MVC"
            ))

        for layer, path in layer_paths.items():
            file_count = len(list(path.rglob('*.py')))
            if file_count == 0:
                issues.append(ArchitectureIssue(
                    file_path=str(path),
                    issue_type="MVC_EMPTY_LAYER",
                    description=f"MVC层 '{layer}' 目录为空",
                    severity=IssueSeverity.LOW,
                    suggestion=f"在 {layer} 层添加相应的文件",
                    principle="MVC"
                ))

        return issues

    def check_controller_purity(self, py_file: Path, tree: ast.AST, source: str) -> List[ArchitectureIssue]:
        """检查Controller层的纯净性"""
        issues = []

        is_controller = any(kw in str(py_file).lower() for kw in ['controller', 'route', 'api', 'endpoint', 'handler'])
        
        if is_controller:
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    for method in node.body:
                        if isinstance(method, ast.FunctionDef):
                            method_source = ast.unparse(method) if hasattr(ast, 'unparse') else ''
                            
                            db_patterns = ['session.query', 'session.add', 'session.commit', 'db.execute', 'cursor.execute']
                            for pattern in db_patterns:
                                if pattern in method_source:
                                    issues.append(ArchitectureIssue(
                                        file_path=str(py_file),
                                        issue_type="MVC_CONTROLLER_VIOLATION",
                                        description=f"Controller类 '{node.name}' 包含数据库操作，应移至Model或Repository",
                                        severity=IssueSeverity.HIGH,
                                        line_number=method.lineno,
                                        suggestion="将数据库操作移至Model层或Repository层",
                                        principle="MVC"
                                    ))
                                    break

                            business_patterns = ['calculate', 'compute', 'process', 'validate']
                            for pattern in business_patterns:
                                if pattern in method.name.lower():
                                    has_service_call = any(
                                        svc in method_source 
                                        for svc in ['service.', 'Service(', 'self.service']
                                    )
                                    if not has_service_call:
                                        issues.append(ArchitectureIssue(
                                            file_path=str(py_file),
                                            issue_type="MVC_CONTROLLER_VIOLATION",
                                            description=f"Controller方法 '{method.name}' 包含业务逻辑，应移至Service层",
                                            severity=IssueSeverity.MEDIUM,
                                            line_number=method.lineno,
                                            suggestion="将业务逻辑移至Service层，Controller只负责请求转发",
                                            principle="MVC"
                                        ))
                                        break

        return issues

    def check_model_purity(self, py_file: Path, tree: ast.AST, source: str) -> List[ArchitectureIssue]:
        """检查Model层的纯净性"""
        issues = []

        is_model = any(kw in str(py_file).lower() for kw in ['model', 'entity', 'domain', 'store'])
        
        if is_model:
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    for method in node.body:
                        if isinstance(method, ast.FunctionDef):
                            method_source = ast.unparse(method) if hasattr(ast, 'unparse') else ''
                            
                            view_patterns = ['render_template', 'jsonify', 'Response', 'redirect', 'flash', 'session']
                            for pattern in view_patterns:
                                if pattern in method_source:
                                    issues.append(ArchitectureIssue(
                                        file_path=str(py_file),
                                        issue_type="MVC_MODEL_VIOLATION",
                                        description=f"Model类 '{node.name}' 包含视图相关逻辑",
                                        severity=IssueSeverity.HIGH,
                                        line_number=method.lineno,
                                        suggestion="Model层应只包含数据和业务逻辑，不应包含视图逻辑",
                                        principle="MVC"
                                    ))
                                    break

        return issues

    def check_view_controller_binding(self, py_file: Path, content: str) -> List[ArchitectureIssue]:
        """检查View与Controller的绑定关系"""
        issues = []

        is_view = any(kw in str(py_file).lower() for kw in ['view', 'template', 'page', 'screen'])
        
        if is_view and py_file.suffix in ['.html', '.vue', '.jsx', '.tsx']:
            business_patterns = ['SELECT', 'INSERT', 'UPDATE', 'DELETE', 'query(', 'execute(']
            for pattern in business_patterns:
                if pattern in content:
                    issues.append(ArchitectureIssue(
                        file_path=str(py_file),
                        issue_type="MVC_VIEW_VIOLATION",
                        description="View文件中包含数据库或业务逻辑",
                        severity=IssueSeverity.HIGH,
                        suggestion="View应只负责展示，业务逻辑应移至Controller或Service",
                        principle="MVC"
                    ))
                    break

        return issues

    def check_all_mvc(self, project_root: Path) -> List[ArchitectureIssue]:
        """执行所有MVC检查"""
        all_issues = []
        
        all_issues.extend(self.check_structure(project_root))
        
        backend_app = self.path_manager.get_backend_path() / 'app'
        if backend_app.exists():
            for py_file in backend_app.rglob('*.py'):
                try:
                    with open(py_file, 'r', encoding='utf-8') as f:
                        source = f.read()
                    tree = ast.parse(source)
                    all_issues.extend(self.check_controller_purity(py_file, tree, source))
                    all_issues.extend(self.check_model_purity(py_file, tree, source))
                except Exception as e:
                    self.logger.warning(f"MVC检查失败 {py_file}: {e}")

            for template_file in backend_app.rglob('*.html'):
                try:
                    with open(template_file, 'r', encoding='utf-8') as f:
                        content = f.read()
                    all_issues.extend(self.check_view_controller_binding(template_file, content))
                except Exception as e:
                    self.logger.warning(f"MVC检查失败 {template_file}: {e}")

        return all_issues


class DependencyInjectionChecker:
    """依赖注入检查器"""

    DI_PATTERNS = {
        'constructor_injection': True,
        'setter_injection': True,
        'interface_injection': True
    }

    DI_FRAMEWORK_MARKERS = [
        'inject', 'Inject', 'dependency_injector', 'Injector',
        'Container', 'Provider', 'Scope', '@inject', '@Inject'
    ]

    def __init__(self, logger: logging.Logger):
        self.logger = logger
        self.issues: List[ArchitectureIssue] = []
        self.path_manager = PathConfigManager(auto_detect=True)

    def check_constructor_injection(self, py_file: Path, tree: ast.AST, source: str) -> List[ArchitectureIssue]:
        """检查构造函数注入模式"""
        issues = []

        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                if self._is_service_class(node):
                    init_method = None
                    for item in node.body:
                        if isinstance(item, ast.FunctionDef) and item.name == '__init__':
                            init_method = item
                            break

                    if init_method:
                        injected_deps = []
                        hardcoded_deps = []

                        for arg in init_method.args.args[1:]:
                            if arg.annotation:
                                if isinstance(arg.annotation, ast.Name):
                                    if arg.annotation.id.startswith('I') or arg.annotation.id.startswith('Abstract'):
                                        injected_deps.append(arg.arg)
                                    elif arg.annotation.id in ('str', 'int', 'float', 'bool', 'dict', 'list'):
                                        pass
                                    else:
                                        injected_deps.append(arg.arg)
                            else:
                                hardcoded_deps.append(arg.arg)

                        for stmt in init_method.body:
                            if isinstance(stmt, ast.Assign):
                                for target in stmt.targets:
                                    if isinstance(target, ast.Attribute):
                                        if isinstance(stmt.value, ast.Call):
                                            if isinstance(stmt.value.func, ast.Name):
                                                if stmt.value.func.id[0].isupper():
                                                    hardcoded_deps.append(stmt.value.func.id)

                        if hardcoded_deps:
                            issues.append(ArchitectureIssue(
                                file_path=str(py_file),
                                issue_type="DI_HARDCODED_DEPENDENCY",
                                description=f"类 '{node.name}' 存在硬编码依赖: {hardcoded_deps}，建议使用依赖注入",
                                severity=IssueSeverity.MEDIUM,
                                line_number=node.lineno,
                                suggestion="通过构造函数注入依赖，而不是在类内部创建实例",
                                principle="DEPENDENCY_INJECTION"
                            ))

                        if not injected_deps and self._is_service_class(node):
                            issues.append(ArchitectureIssue(
                                file_path=str(py_file),
                                issue_type="DI_MISSING_INJECTION",
                                description=f"服务类 '{node.name}' 未使用依赖注入模式",
                                severity=IssueSeverity.LOW,
                                line_number=node.lineno,
                                suggestion="考虑使用依赖注入来管理类的依赖关系",
                                principle="DEPENDENCY_INJECTION"
                            ))

        return issues

    def _is_service_class(self, node: ast.ClassDef) -> bool:
        """判断是否是服务类"""
        service_suffixes = ['Service', 'Manager', 'Handler', 'Processor', 'Repository', 'Controller']
        return any(node.name.endswith(suffix) for suffix in service_suffixes)

    def check_interface_usage(self, py_file: Path, tree: ast.AST, source: str) -> List[ArchitectureIssue]:
        """检查接口使用模式"""
        issues = []

        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                has_abstract_base = False
                abstract_methods = []

                for base in node.bases:
                    if isinstance(base, ast.Name):
                        if base.id.startswith('Abstract') or base.id.startswith('I'):
                            has_abstract_base = True
                    elif isinstance(base, ast.Attribute):
                        if base.attr.startswith('Abstract') or base.attr.startswith('I'):
                            has_abstract_base = True

                for item in node.body:
                    if isinstance(item, ast.FunctionDef):
                        for decorator in item.decorator_list:
                            if isinstance(decorator, ast.Name) and decorator.id == 'abstractmethod':
                                abstract_methods.append(item.name)
                            elif isinstance(decorator, ast.Attribute) and decorator.attr == 'abstractmethod':
                                abstract_methods.append(item.name)

                if has_abstract_base and not abstract_methods:
                    issues.append(ArchitectureIssue(
                        file_path=str(py_file),
                        issue_type="DI_INTERFACE_VIOLATION",
                        description=f"抽象类 '{node.name}' 没有抽象方法，可能不需要继承抽象基类",
                        severity=IssueSeverity.LOW,
                        line_number=node.lineno,
                        suggestion="添加抽象方法或移除抽象基类继承",
                        principle="DEPENDENCY_INJECTION"
                    ))

        return issues

    def check_container_pattern(self, py_file: Path, tree: ast.AST, source: str) -> List[ArchitectureIssue]:
        """检查容器模式使用"""
        issues = []

        has_container = any(marker in source for marker in self.DI_FRAMEWORK_MARKERS)

        if 'container' in str(py_file).lower() or 'Container' in source:
            if not has_container:
                issues.append(ArchitectureIssue(
                    file_path=str(py_file),
                    issue_type="DI_CONTAINER_PATTERN",
                    description="发现容器相关代码但未使用标准DI框架",
                    severity=IssueSeverity.INFO,
                    suggestion="考虑使用成熟的DI框架如dependency-injector",
                    principle="DEPENDENCY_INJECTION"
                ))

        return issues

    def check_all_di(self, project_root: Path) -> List[ArchitectureIssue]:
        """执行所有依赖注入检查"""
        all_issues = []
        
        backend_app = self.path_manager.get_backend_path() / 'app'
        if backend_app.exists():
            for py_file in backend_app.rglob('*.py'):
                try:
                    with open(py_file, 'r', encoding='utf-8') as f:
                        source = f.read()
                    tree = ast.parse(source)
                    all_issues.extend(self.check_constructor_injection(py_file, tree, source))
                    all_issues.extend(self.check_interface_usage(py_file, tree, source))
                    all_issues.extend(self.check_container_pattern(py_file, tree, source))
                except Exception as e:
                    self.logger.warning(f"依赖注入检查失败 {py_file}: {e}")

        return all_issues


class LayeredArchitectureChecker:
    """分层架构检查器"""

    LAYER_DEFINITIONS = {
        'presentation': {
            'dirs': ['api', 'views', 'controllers', 'routes', 'endpoints'],
            'allowed_deps': ['business', 'service', 'core'],
            'forbidden_deps': ['data', 'repository', 'dao', 'models']
        },
        'business': {
            'dirs': ['services', 'business', 'domain', 'usecases'],
            'allowed_deps': ['data', 'repository', 'core'],
            'forbidden_deps': ['presentation', 'api', 'views']
        },
        'data': {
            'dirs': ['models', 'repositories', 'dao', 'data', 'entities'],
            'allowed_deps': ['core'],
            'forbidden_deps': ['presentation', 'business', 'service']
        },
        'core': {
            'dirs': ['core', 'common', 'utils', 'helpers', 'base'],
            'allowed_deps': [],
            'forbidden_deps': []
        }
    }

    def __init__(self, logger: logging.Logger):
        self.logger = logger
        self.issues: List[ArchitectureIssue] = []
        self.path_manager = PathConfigManager(auto_detect=True)

    def check_layer_violations(self, project_root: Path) -> List[ArchitectureIssue]:
        issues = []
        backend_app = self.path_manager.get_backend_path() / 'app'
        if not backend_app.exists():
            return issues

        layer_files = self._collect_layer_files(backend_app)
        for layer, files in layer_files.items():
            for py_file in files:
                file_issues = self._check_file_layer_compliance(py_file, layer, backend_app)
                issues.extend(file_issues)

        return issues

    def _collect_layer_files(self, backend_app: Path) -> Dict[str, List[Path]]:
        layer_files: Dict[str, List[Path]] = defaultdict(list)
        
        for py_file in backend_app.rglob('*.py'):
            rel_path = py_file.relative_to(backend_app)
            path_parts = [p.lower() for p in rel_path.parts]
            
            for layer, config in self.LAYER_DEFINITIONS.items():
                for dir_name in config['dirs']:
                    if dir_name in path_parts:
                        layer_files[layer].append(py_file)
                        break

        return layer_files

    def _check_file_layer_compliance(self, py_file: Path, layer: str, backend_app: Path) -> List[ArchitectureIssue]:
        issues = []
        config = self.LAYER_DEFINITIONS.get(layer, {})
        forbidden_deps = config.get('forbidden_deps', [])

        try:
            with open(py_file, 'r', encoding='utf-8') as f:
                source = f.read()
            tree = ast.parse(source)

            for node in ast.walk(tree):
                if isinstance(node, ast.ImportFrom):
                    if node.module:
                        module_parts = node.module.split('.')
                        for forbidden in forbidden_deps:
                            if forbidden in module_parts:
                                issues.append(ArchitectureIssue(
                                    file_path=str(py_file),
                                    issue_type="LAYER_VIOLATION",
                                    description=f"分层违规: {layer}层依赖了{forbidden}层",
                                    severity=IssueSeverity.HIGH,
                                    line_number=node.lineno,
                                    suggestion=f"重构代码，{layer}层不应直接依赖{forbidden}层",
                                    principle="LAYERED_ARCHITECTURE"
                                ))

        except Exception as e:
            self.logger.warning(f"分层检查失败 {py_file}: {e}")

        return issues

    def check_dependency_injection_pattern(self, py_file: Path, tree: ast.AST, source: str) -> List[ArchitectureIssue]:
        issues = []

        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                if self._is_service_class(node):
                    has_di = self._check_di_pattern(node)
                    if not has_di:
                        issues.append(ArchitectureIssue(
                            file_path=str(py_file),
                            issue_type="DI_PATTERN_MISSING",
                            description=f"服务类 '{node.name}' 可能缺少依赖注入模式",
                            severity=IssueSeverity.LOW,
                            line_number=node.lineno,
                            suggestion="考虑使用构造函数注入或属性注入来管理依赖",
                            principle="DEPENDENCY_INJECTION"
                        ))

        return issues

    def _is_service_class(self, node: ast.ClassDef) -> bool:
        service_suffixes = ['Service', 'Manager', 'Handler', 'Processor', 'Repository']
        return any(node.name.endswith(suffix) for suffix in service_suffixes)

    def _check_di_pattern(self, node: ast.ClassDef) -> bool:
        has_init = False
        has_injected_deps = False

        for item in node.body:
            if isinstance(item, ast.FunctionDef) and item.name == '__init__':
                has_init = True
                if len(item.args.args) > 1:
                    has_injected_deps = True

        return has_init and has_injected_deps


class PrincipleChecker:
    """DRY/KISS/YAGNI原则检查器"""

    def __init__(self, logger: logging.Logger):
        self.logger = logger
        self.issues: List[ArchitectureIssue] = []
        self._code_blocks: Dict[str, List[Tuple[Path, int, str]]] = defaultdict(list)
        self._similarity_cache: Dict[str, float] = {}

    def check_dry(self, py_file: Path, tree: ast.AST) -> List[ArchitectureIssue]:
        """检查DRY原则 (Don't Repeat Yourself)"""
        issues = []

        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if hasattr(node, 'end_lineno') and node.end_lineno:
                    func_length = node.end_lineno - node.lineno
                    if 5 <= func_length <= 20:
                        body_lines = []
                        for child in node.body:
                            body_lines.append(ast.unparse(child) if hasattr(ast, 'unparse') else str(type(child)))
                        
                        body_hash = hash('\n'.join(body_lines))
                        self._code_blocks[body_hash].append((py_file, node.lineno, node.name))

        for body_hash, occurrences in self._code_blocks.items():
            if len(occurrences) > 1:
                files = set(str(o[0]) for o in occurrences)
                if len(files) > 1:
                    issues.append(ArchitectureIssue(
                        file_path=str(occurrences[0][0]),
                        issue_type="DRY_VIOLATION",
                        description=f"发现重复代码块，出现在 {len(occurrences)} 处: {[o[2] for o in occurrences]}",
                        severity=IssueSeverity.MEDIUM,
                        line_number=occurrences[0][1],
                        suggestion="提取公共代码到独立函数或工具类中",
                        principle="DRY"
                    ))

        return issues

    def check_kiss(self, py_file: Path, tree: ast.AST) -> List[ArchitectureIssue]:
        """检查KISS原则 (Keep It Simple, Stupid)"""
        issues = []

        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                complexity = self._calculate_complexity(node)
                if complexity > 15:
                    issues.append(ArchitectureIssue(
                        file_path=str(py_file),
                        issue_type="KISS_VIOLATION",
                        description=f"函数 '{node.name}' 复杂度过高 (圈复杂度: {complexity})，违反KISS原则",
                        severity=IssueSeverity.MEDIUM,
                        line_number=node.lineno,
                        suggestion="简化逻辑，拆分复杂函数，减少嵌套层级",
                        principle="KISS"
                    ))

                nesting_depth = self._calculate_nesting_depth(node)
                if nesting_depth > 4:
                    issues.append(ArchitectureIssue(
                        file_path=str(py_file),
                        issue_type="KISS_VIOLATION",
                        description=f"函数 '{node.name}' 嵌套层级过深 (深度: {nesting_depth})，违反KISS原则",
                        severity=IssueSeverity.MEDIUM,
                        line_number=node.lineno,
                        suggestion="使用早返回、提取方法等方式减少嵌套",
                        principle="KISS"
                    ))

        return issues

    def _calculate_complexity(self, node: ast.AST) -> int:
        """计算圈复杂度"""
        complexity = 1
        for child in ast.walk(node):
            if isinstance(child, (ast.If, ast.While, ast.For, ast.ExceptHandler)):
                complexity += 1
            elif isinstance(child, ast.BoolOp):
                complexity += len(child.values) - 1
            elif isinstance(child, (ast.And, ast.Or)):
                complexity += 1
            elif isinstance(child, ast.comprehension):
                complexity += 1
                if child.ifs:
                    complexity += len(child.ifs)
        return complexity

    def _calculate_nesting_depth(self, node: ast.AST, current_depth: int = 0) -> int:
        """计算嵌套深度"""
        max_depth = current_depth
        
        for child in ast.iter_child_nodes(node):
            if isinstance(child, (ast.If, ast.For, ast.While, ast.With, ast.Try)):
                child_depth = self._calculate_nesting_depth(child, current_depth + 1)
                max_depth = max(max_depth, child_depth)
            else:
                child_depth = self._calculate_nesting_depth(child, current_depth)
                max_depth = max(max_depth, child_depth)
        
        return max_depth

    def check_yagni(self, py_file: Path, tree: ast.AST, source: str) -> List[ArchitectureIssue]:
        """检查YAGNI原则 (You Aren't Gonna Need It)"""
        issues = []

        unused_patterns = [
            (r'#\s*TODO:.*future', "可能存在为未来预留的代码"),
            (r'#\s*FIXME:.*never used', "存在标记为未使用的代码"),
            (r'class\s+\w+.*:\s*\.\.\\.|pass\s*$', "可能存在空实现类"),
            (r'def\s+\w+.*:\s*\.\.\.|pass\s*$', "可能存在空实现方法"),
        ]

        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                methods = [n for n in node.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]
                
                if len(methods) == 0:
                    docstring = ast.get_docstring(node)
                    if not docstring or 'placeholder' not in docstring.lower():
                        issues.append(ArchitectureIssue(
                            file_path=str(py_file),
                            issue_type="YAGNI_VIOLATION",
                            description=f"类 '{node.name}' 没有任何方法实现，可能违反YAGNI原则",
                            severity=IssueSeverity.LOW,
                            line_number=node.lineno,
                            suggestion="如果不需要此类，请移除；如果需要实现，请完成实现",
                            principle="YAGNI"
                        ))

                for method in methods:
                    if len(method.body) == 1:
                        if isinstance(method.body[0], ast.Pass):
                            issues.append(ArchitectureIssue(
                                file_path=str(py_file),
                                issue_type="YAGNI_VIOLATION",
                                description=f"方法 '{node.name}.{method.name}' 只有pass语句，可能违反YAGNI原则",
                                severity=IssueSeverity.LOW,
                                line_number=method.lineno,
                                suggestion="如果不需要此方法，请移除；如果需要实现，请完成实现",
                                principle="YAGNI"
                            ))

        return issues

    def check_all_principles(self, py_file: Path) -> List[ArchitectureIssue]:
        """执行所有原则检查"""
        all_issues = []
        
        try:
            with open(py_file, 'r', encoding='utf-8') as f:
                source = f.read()
            tree = ast.parse(source)
            
            all_issues.extend(self.check_dry(py_file, tree))
            all_issues.extend(self.check_kiss(py_file, tree))
            all_issues.extend(self.check_yagni(py_file, tree, source))
            
        except Exception as e:
            self.logger.warning(f"原则检查失败 {py_file}: {e}")
        
        return all_issues


class ArchitectureChecker:
    """架构检查器"""

    EXPECTED_STRUCTURE = {
        "backend": [
            "app",
            "app/models",
            "app/api",
            "app/services",
            "tests"
        ],
        "frontend": [
            "src",
            "src/components",
            "src/views",
            "src/stores",
            "src/api"
        ]
    }

    FORBIDDEN_IMPORTS = [
        ("app.services", "app.models"),
    ]

    def __init__(self, project_root: Optional[Path] = None,
                 strict: bool = False, logger: Optional[logging.Logger] = None):
        self.path_manager = PathConfigManager(auto_detect=True)
        self.project_root = project_root or self.path_manager.get_base_path()
        self.strict = strict
        self.logger = logger or logging.getLogger(__name__)
        self.issues: List[ArchitectureIssue] = []
        self.results: List[CheckResult] = []
        
        self.solid_checker = SOLIDChecker(self.logger)
        self.mvvm_checker = MVVMChecker(self.logger)
        self.mvc_checker = MVCChecker(self.logger)
        self.principle_checker = PrincipleChecker(self.logger)
        self.layered_checker = LayeredArchitectureChecker(self.logger)
        self.di_checker = DependencyInjectionChecker(self.logger)

    def run_all_checks(self) -> ArchitectureReport:
        """运行所有架构检查"""
        self.logger.info("开始架构检查...")

        self.results.append(self.check_directory_structure())
        self.results.append(self.check_file_naming())
        self.results.append(self.check_import_cycles())
        self.results.append(self.check_dependencies())
        self.results.append(self.check_config_files())
        self.results.append(self.check_code_style())
        self.results.append(self.check_solid_principles())
        self.results.append(self.check_mvvm_architecture())
        self.results.append(self.check_mvc_architecture())
        self.results.append(self.check_design_principles())
        self.results.append(self.check_layered_architecture())
        self.results.append(self.check_dependency_injection())
        self.results.append(self.check_design_patterns())

        total_issues = sum(len(r.issues) for r in self.results)
        critical_issues = sum(
            1 for r in self.results for i in r.issues
            if i.severity == IssueSeverity.CRITICAL
        )
        high_issues = sum(
            1 for r in self.results for i in r.issues
            if i.severity == IssueSeverity.HIGH
        )

        overall_passed = all(r.status == CheckStatus.PASS for r in self.results)
        if self.strict:
            overall_passed = overall_passed and total_issues == 0

        summary = {
            "total_checks": len(self.results),
            "passed_checks": sum(1 for r in self.results if r.status == CheckStatus.PASS),
            "failed_checks": sum(1 for r in self.results if r.status == CheckStatus.FAIL),
            "warning_checks": sum(1 for r in self.results if r.status == CheckStatus.WARNING),
            "total_issues": total_issues,
            "critical_issues": critical_issues,
            "high_issues": high_issues,
            "medium_issues": sum(
                1 for r in self.results for i in r.issues
                if i.severity == IssueSeverity.MEDIUM
            ),
            "low_issues": sum(
                1 for r in self.results for i in r.issues
                if i.severity == IssueSeverity.LOW
            ),
            "principles_checked": {
                "SOLID": True,
                "MVVM": True,
                "MVC": True,
                "DRY": True,
                "KISS": True,
                "YAGNI": True,
                "LAYERED_ARCHITECTURE": True,
                "DEPENDENCY_INJECTION": True,
                "DESIGN_PATTERNS": True
            },
            "quality_score": self._calculate_architecture_quality_score(),
            "architecture_health": self._calculate_architecture_health()
        }

        return ArchitectureReport(
            timestamp=datetime.now().isoformat(),
            project_root=str(self.project_root),
            overall_passed=overall_passed,
            results=self.results,
            summary=summary
        )

    def _calculate_architecture_health(self) -> Dict[str, Any]:
        """计算架构健康度"""
        health_metrics = {
            "structure_score": 100,
            "solid_compliance": 100,
            "layer_compliance": 100,
            "di_compliance": 100,
            "overall_health": "excellent"
        }

        for result in self.results:
            for issue in result.issues:
                if issue.principle.startswith("SOLID"):
                    health_metrics["solid_compliance"] -= 5
                elif issue.principle == "LAYERED_ARCHITECTURE":
                    health_metrics["layer_compliance"] -= 5
                elif issue.principle == "DEPENDENCY_INJECTION":
                    health_metrics["di_compliance"] -= 5
                elif issue.issue_type in ["missing_directory", "missing_config"]:
                    health_metrics["structure_score"] -= 10

        for key in ["structure_score", "solid_compliance", "layer_compliance", "di_compliance"]:
            health_metrics[key] = max(0, health_metrics[key])

        avg_score = (
            health_metrics["structure_score"] +
            health_metrics["solid_compliance"] +
            health_metrics["layer_compliance"] +
            health_metrics["di_compliance"]
        ) / 4

        if avg_score >= 90:
            health_metrics["overall_health"] = "excellent"
        elif avg_score >= 70:
            health_metrics["overall_health"] = "good"
        elif avg_score >= 50:
            health_metrics["overall_health"] = "fair"
        else:
            health_metrics["overall_health"] = "poor"

        return health_metrics

    def _calculate_architecture_quality_score(self) -> int:
        """计算架构质量评分"""
        total_issues = sum(len(r.issues) for r in self.results)
        if total_issues == 0:
            return 100

        penalty = 0
        for r in self.results:
            for issue in r.issues:
                if issue.severity == IssueSeverity.CRITICAL:
                    penalty += 20
                elif issue.severity == IssueSeverity.HIGH:
                    penalty += 10
                elif issue.severity == IssueSeverity.MEDIUM:
                    penalty += 5
                else:
                    penalty += 1

        return max(0, 100 - penalty)

    def check_layered_architecture(self) -> CheckResult:
        """检查分层架构"""
        self.logger.info("检查分层架构...")
        issues = []

        issues.extend(self.layered_checker.check_layer_violations(self.project_root))

        backend_app = self.path_manager.get_backend_path() / "app"
        if backend_app.exists():
            for py_file in backend_app.rglob("*.py"):
                try:
                    with open(py_file, 'r', encoding='utf-8') as f:
                        source = f.read()
                    tree = ast.parse(source)
                    issues.extend(self.layered_checker.check_dependency_injection_pattern(py_file, tree, source))
                except Exception as e:
                    self.logger.warning(f"分层架构检查失败 {py_file}: {e}")

        status = CheckStatus.PASS if not issues else CheckStatus.WARNING
        return CheckResult(
            check_name="layered_architecture",
            status=status,
            issues=issues,
            details={
                "layers_checked": ["presentation", "business", "data", "core"],
                "patterns_checked": ["dependency_injection"]
            }
        )

    def check_design_patterns(self) -> CheckResult:
        """检查设计模式合规性"""
        self.logger.info("检查设计模式合规性...")
        issues = []

        backend_app = self.path_manager.get_backend_path() / "app"
        if backend_app.exists():
            for py_file in backend_app.rglob("*.py"):
                try:
                    with open(py_file, 'r', encoding='utf-8') as f:
                        source = f.read()
                    tree = ast.parse(source)
                    issues.extend(self._check_pattern_violations(py_file, tree, source))
                except Exception as e:
                    self.logger.warning(f"设计模式检查失败 {py_file}: {e}")

        status = CheckStatus.PASS if not issues else CheckStatus.WARNING
        return CheckResult(
            check_name="design_patterns",
            status=status,
            issues=issues,
            details={
                "patterns_checked": ["singleton", "factory", "observer", "strategy", "repository"]
            }
        )

    def _check_pattern_violations(self, py_file: Path, tree: ast.AST, source: str) -> List[ArchitectureIssue]:
        """检查设计模式违规"""
        issues = []

        issues.extend(self._check_singleton_pattern(py_file, tree))
        issues.extend(self._check_factory_pattern(py_file, tree))
        issues.extend(self._check_repository_pattern(py_file, tree, source))

        return issues

    def _check_singleton_pattern(self, py_file: Path, tree: ast.AST) -> List[ArchitectureIssue]:
        """检查单例模式实现"""
        issues = []

        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                has_new_method = False
                has_instance_var = False

                for item in node.body:
                    if isinstance(item, ast.FunctionDef):
                        if item.name == '__new__':
                            has_new_method = True
                        for child in ast.walk(item):
                            if isinstance(child, ast.Attribute):
                                if child.attr == '_instance':
                                    has_instance_var = True

                if has_new_method and not has_instance_var:
                    issues.append(ArchitectureIssue(
                        file_path=str(py_file),
                        issue_type="SINGLETON_PATTERN",
                        description=f"类 '{node.name}' 的单例实现可能不完整",
                        severity=IssueSeverity.LOW,
                        line_number=node.lineno,
                        suggestion="确保单例模式正确实现，包括线程安全",
                        principle="DESIGN_PATTERN_SINGLETON"
                    ))

        return issues

    def _check_factory_pattern(self, py_file: Path, tree: ast.AST) -> List[ArchitectureIssue]:
        """检查工厂模式实现"""
        issues = []

        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                if 'Factory' in node.name:
                    has_create_method = False
                    for item in node.body:
                        if isinstance(item, ast.FunctionDef):
                            if 'create' in item.name.lower() or 'build' in item.name.lower():
                                has_create_method = True

                    if not has_create_method:
                        issues.append(ArchitectureIssue(
                            file_path=str(py_file),
                            issue_type="FACTORY_PATTERN",
                            description=f"工厂类 '{node.name}' 缺少创建方法",
                            severity=IssueSeverity.LOW,
                            line_number=node.lineno,
                            suggestion="工厂类应包含create或build方法",
                            principle="DESIGN_PATTERN_FACTORY"
                        ))

        return issues

    def _check_repository_pattern(self, py_file: Path, tree: ast.AST, source: str) -> List[ArchitectureIssue]:
        """检查仓储模式实现"""
        issues = []

        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                if 'Repository' in node.name:
                    crud_methods = {'get', 'find', 'save', 'delete', 'update', 'create'}
                    found_methods = set()

                    for item in node.body:
                        if isinstance(item, ast.FunctionDef):
                            method_lower = item.name.lower()
                            for crud in crud_methods:
                                if crud in method_lower:
                                    found_methods.add(crud)

                    if len(found_methods) < 2:
                        issues.append(ArchitectureIssue(
                            file_path=str(py_file),
                            issue_type="REPOSITORY_PATTERN",
                            description=f"仓储类 '{node.name}' 缺少标准CRUD方法",
                            severity=IssueSeverity.INFO,
                            line_number=node.lineno,
                            suggestion="仓储类应实现标准的CRUD操作",
                            principle="DESIGN_PATTERN_REPOSITORY"
                        ))

        return issues

    def check_solid_principles(self) -> CheckResult:
        """检查SOLID原则"""
        self.logger.info("检查SOLID原则...")
        issues = []

        backend_app = self.path_manager.get_backend_path() / "app"
        if not backend_app.exists():
            return CheckResult(
                check_name="solid_principles",
                status=CheckStatus.SKIP,
                issues=[],
                details={"reason": "backend/app 目录不存在"}
            )

        for py_file in backend_app.rglob("*.py"):
            issues.extend(self.solid_checker.check_all_solid(py_file))

        status = CheckStatus.PASS if not issues else CheckStatus.WARNING
        return CheckResult(
            check_name="solid_principles",
            status=status,
            issues=issues,
            details={
                "files_checked": len(list(backend_app.rglob("*.py"))),
                "principles": ["SRP", "OCP", "LSP", "ISP", "DIP"]
            }
        )

    def check_mvvm_architecture(self) -> CheckResult:
        """检查MVVM架构"""
        self.logger.info("检查MVVM架构...")
        issues = []

        issues.extend(self.mvvm_checker.check_all_mvvm(self.project_root))

        status = CheckStatus.PASS if not issues else CheckStatus.WARNING
        return CheckResult(
            check_name="mvvm_architecture",
            status=status,
            issues=issues,
            details={
                "layers_checked": ["Model", "View", "ViewModel"],
                "frontend_path": "frontend/src"
            }
        )

    def check_mvc_architecture(self) -> CheckResult:
        """检查MVC架构"""
        self.logger.info("检查MVC架构...")
        issues = []

        issues.extend(self.mvc_checker.check_all_mvc(self.project_root))

        status = CheckStatus.PASS if not issues else CheckStatus.WARNING
        return CheckResult(
            check_name="mvc_architecture",
            status=status,
            issues=issues,
            details={
                "layers_checked": ["Model", "View", "Controller"],
                "backend_path": "backend/app"
            }
        )

    def check_dependency_injection(self) -> CheckResult:
        """检查依赖注入模式"""
        self.logger.info("检查依赖注入模式...")
        issues = []

        issues.extend(self.di_checker.check_all_di(self.project_root))

        status = CheckStatus.PASS if not issues else CheckStatus.WARNING
        return CheckResult(
            check_name="dependency_injection",
            status=status,
            issues=issues,
            details={
                "patterns_checked": ["constructor_injection", "interface_usage", "container_pattern"],
                "frameworks_detected": self._detect_di_frameworks()
            }
        )

    def _detect_di_frameworks(self) -> List[str]:
        """检测使用的DI框架"""
        detected = []
        di_frameworks = ['dependency_injector', 'injector', 'pinject', 'python-dependency-injector']
        
        requirements_path = self.path_manager.get_backend_path() / 'requirements.txt'
        if requirements_path.exists():
            try:
                with open(requirements_path, 'r', encoding='utf-8') as f:
                    content = f.read().lower()
                    for framework in di_frameworks:
                        if framework in content:
                            detected.append(framework)
            except Exception:
                pass
        
        return detected

    def check_design_principles(self) -> CheckResult:
        """检查DRY/KISS/YAGNI原则"""
        self.logger.info("检查DRY/KISS/YAGNI原则...")
        issues = []

        backend_app = self.path_manager.get_backend_path() / "app"
        if backend_app.exists():
            for py_file in backend_app.rglob("*.py"):
                issues.extend(self.principle_checker.check_all_principles(py_file))

        status = CheckStatus.PASS if not issues else CheckStatus.WARNING
        return CheckResult(
            check_name="design_principles",
            status=status,
            issues=issues,
            details={
                "files_checked": len(list(backend_app.rglob("*.py"))) if backend_app.exists() else 0,
                "principles": ["DRY", "KISS", "YAGNI"]
            }
        )

    def check_directory_structure(self) -> CheckResult:
        """检查目录结构"""
        self.logger.info("检查目录结构...")
        issues = []

        for project, expected_dirs in self.EXPECTED_STRUCTURE.items():
            project_path = self.project_root / project
            if not project_path.exists():
                issues.append(ArchitectureIssue(
                    file_path=str(project_path),
                    issue_type="missing_directory",
                    description=f"{project} 目录不存在",
                    severity=IssueSeverity.CRITICAL,
                    suggestion=f"创建 {project} 目录"
                ))
                continue

            for expected_dir in expected_dirs:
                dir_path = self.project_root / project / expected_dir
                if not dir_path.exists():
                    issues.append(ArchitectureIssue(
                        file_path=str(dir_path),
                        issue_type="missing_directory",
                        description=f"期望的目录不存在: {expected_dir}",
                        severity=IssueSeverity.HIGH if expected_dir.startswith("app/") else IssueSeverity.MEDIUM,
                        suggestion=f"创建目录 {expected_dir}"
                    ))

        status = CheckStatus.PASS if not issues else CheckStatus.FAIL
        return CheckResult(
            check_name="directory_structure",
            status=status,
            issues=issues,
            details={"expected_structure": self.EXPECTED_STRUCTURE}
        )

    def check_file_naming(self) -> CheckResult:
        """检查文件命名规范"""
        self.logger.info("检查文件命名规范...")
        issues = []

        backend_app = self.path_manager.get_backend_path() / "app"
        if backend_app.exists():
            for py_file in backend_app.rglob("*.py"):
                if py_file.name != py_file.name.lower():
                    issues.append(ArchitectureIssue(
                        file_path=str(py_file),
                        issue_type="naming_convention",
                        description=f"文件名应使用小写: {py_file.name}",
                        severity=IssueSeverity.LOW,
                        suggestion="将文件名改为小写"
                    ))

                if " " in py_file.name or "-" in py_file.name:
                    issues.append(ArchitectureIssue(
                        file_path=str(py_file),
                        issue_type="naming_convention",
                        description=f"文件名不应包含空格或连字符: {py_file.name}",
                        severity=IssueSeverity.MEDIUM,
                        suggestion="使用下划线替换空格和连字符"
                    ))

        status = CheckStatus.PASS if not issues else (CheckStatus.WARNING if all(i.severity == IssueSeverity.LOW for i in issues) else CheckStatus.FAIL)
        return CheckResult(
            check_name="file_naming",
            status=status,
            issues=issues,
            details={"files_checked": len(list(backend_app.rglob("*.py"))) if backend_app.exists() else 0}
        )

    def check_import_cycles(self) -> CheckResult:
        """检查导入循环"""
        self.logger.info("检查导入循环...")
        issues = []

        backend_app = self.path_manager.get_backend_path() / "app"
        if not backend_app.exists():
            return CheckResult(
                check_name="import_cycles",
                status=CheckStatus.SKIP,
                issues=[],
                details={"reason": "backend/app 目录不存在"}
            )

        import_graph: Dict[str, Set[str]] = {}

        for py_file in backend_app.rglob("*.py"):
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    tree = ast.parse(f.read())

                module_name = str(py_file.relative_to(backend_app)).replace('/', '.').replace('\\', '.')[:-3]
                imports = set()

                for node in ast.walk(tree):
                    if isinstance(node, ast.Import):
                        for alias in node.names:
                            if alias.name.startswith('app.'):
                                imports.add(alias.name)
                    elif isinstance(node, ast.ImportFrom):
                        if node.module and node.module.startswith('app.'):
                            imports.add(node.module)

                import_graph[module_name] = imports
            except Exception as e:
                self.logger.warning(f"解析文件失败 {py_file}: {e}")

        cycles = self._detect_cycles(import_graph)
        for cycle in cycles:
            issues.append(ArchitectureIssue(
                file_path=cycle[0],
                issue_type="import_cycle",
                description=f"发现导入循环: {' -> '.join(cycle)}",
                severity=IssueSeverity.HIGH,
                suggestion="重构代码以消除循环依赖"
            ))

        status = CheckStatus.PASS if not issues else CheckStatus.FAIL
        return CheckResult(
            check_name="import_cycles",
            status=status,
            issues=issues,
            details={"modules_checked": len(import_graph), "cycles_found": len(cycles)}
        )

    def _detect_cycles(self, graph: Dict[str, Set[str]]) -> List[List[str]]:
        """检测图中的循环"""
        cycles = []
        visited = set()
        rec_stack = set()

        def dfs(node: str, path: List[str]):
            visited.add(node)
            rec_stack.add(node)

            for neighbor in graph.get(node, set()):
                if neighbor not in visited:
                    dfs(neighbor, path + [neighbor])
                elif neighbor in rec_stack:
                    cycle_start = path.index(neighbor) if neighbor in path else len(path)
                    cycle = path[cycle_start:] + [neighbor]
                    cycles.append(cycle)

            rec_stack.remove(node)

        for node in graph:
            if node not in visited:
                dfs(node, [node])

        return cycles

    def check_dependencies(self) -> CheckResult:
        """检查依赖关系"""
        self.logger.info("检查依赖关系...")
        issues = []

        backend_app = self.path_manager.get_backend_path() / "app"
        if not backend_app.exists():
            return CheckResult(
                check_name="dependencies",
                status=CheckStatus.SKIP,
                issues=[],
                details={"reason": "backend/app 目录不存在"}
            )

        for py_file in backend_app.rglob("*.py"):
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    tree = ast.parse(content)

                for node in ast.walk(tree):
                    if isinstance(node, ast.ImportFrom):
                        if node.module:
                            for forbidden_from, forbidden_to in self.FORBIDDEN_IMPORTS:
                                if node.module.startswith(forbidden_from):
                                    issues.append(ArchitectureIssue(
                                        file_path=str(py_file),
                                        issue_type="forbidden_import",
                                        description=f"禁止从 {forbidden_from} 导入",
                                        line_number=node.lineno,
                                        severity=IssueSeverity.HIGH,
                                        suggestion=f"检查架构设计，避免违反分层原则"
                                    ))
            except Exception as e:
                self.logger.warning(f"检查依赖失败 {py_file}: {e}")

        status = CheckStatus.PASS if not issues else CheckStatus.FAIL
        return CheckResult(
            check_name="dependencies",
            status=status,
            issues=issues,
            details={"files_checked": len(list(backend_app.rglob("*.py")))}
        )

    def check_config_files(self) -> CheckResult:
        """检查配置文件"""
        self.logger.info("检查配置文件...")
        issues = []

        required_configs = [
            (str(self.path_manager.get_backend_path() / "requirements.txt"), IssueSeverity.HIGH),
            (str(self.path_manager.get_frontend_path() / "package.json"), IssueSeverity.HIGH),
            ("docker-compose.yml", IssueSeverity.MEDIUM),
        ]

        for config_file, severity in required_configs:
            config_path = Path(config_file) if config_file.startswith(str(self.path_manager.get_base_path())) else self.project_root / config_file
            if not config_path.exists():
                issues.append(ArchitectureIssue(
                    file_path=config_file,
                    issue_type="missing_config",
                    description=f"配置文件不存在: {config_file}",
                    severity=severity,
                    suggestion=f"创建 {config_file} 文件"
                ))

        env_example = self.project_root / ".env.example"
        if not env_example.exists():
            issues.append(ArchitectureIssue(
                file_path=".env.example",
                issue_type="missing_config",
                description="缺少 .env.example 文件",
                severity=IssueSeverity.MEDIUM,
                suggestion="创建 .env.example 文件作为环境变量模板"
            ))

        status = CheckStatus.PASS if not issues else CheckStatus.WARNING
        return CheckResult(
            check_name="config_files",
            status=status,
            issues=issues,
            details={"required_configs": [c[0] for c in required_configs]}
        )

    def check_code_style(self) -> CheckResult:
        """检查代码风格"""
        self.logger.info("检查代码风格...")
        issues = []

        backend_app = self.path_manager.get_backend_path() / "app"
        if not backend_app.exists():
            return CheckResult(
                check_name="code_style",
                status=CheckStatus.SKIP,
                issues=[],
                details={"reason": "backend/app 目录不存在"}
            )

        for py_file in backend_app.rglob("*.py"):
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    lines = f.readlines()

                for i, line in enumerate(lines, 1):
                    if len(line) > 120:
                        issues.append(ArchitectureIssue(
                            file_path=str(py_file),
                            issue_type="line_too_long",
                            description=f"行 {i} 超过 120 字符",
                            line_number=i,
                            severity=IssueSeverity.LOW,
                            suggestion="拆分行或简化代码"
                        ))

                    if line.rstrip() != line.rstrip('\n').rstrip():
                        issues.append(ArchitectureIssue(
                            file_path=str(py_file),
                            issue_type="trailing_whitespace",
                            description=f"行 {i} 有尾随空格",
                            line_number=i,
                            severity=IssueSeverity.LOW,
                            suggestion="删除尾随空格"
                        ))
            except Exception as e:
                self.logger.warning(f"检查代码风格失败 {py_file}: {e}")

        status = CheckStatus.PASS if not issues else CheckStatus.WARNING
        return CheckResult(
            check_name="code_style",
            status=status,
            issues=issues,
            details={"files_checked": len(list(backend_app.rglob("*.py")))}
        )

    def print_report(self, report: ArchitectureReport):
        """打印报告"""
        print("\n" + "=" * 80)
        print("架构检查报告")
        print("=" * 80)
        print(f"项目根目录: {report.project_root}")
        print(f"检查时间: {report.timestamp}")
        print(f"总体状态: {'✅ 通过' if report.overall_passed else '❌ 未通过'}")

        print("\n" + "-" * 80)
        print("摘要")
        print("-" * 80)
        for key, value in report.summary.items():
            if isinstance(value, dict):
                print(f"  {key}:")
                for k, v in value.items():
                    print(f"    {k}: {v}")
            else:
                print(f"  {key}: {value}")

        for result in report.results:
            print("\n" + "-" * 80)
            print(f"检查: {result.check_name}")
            print("-" * 80)
            status_icon = {
                CheckStatus.PASS: "✅",
                CheckStatus.FAIL: "❌",
                CheckStatus.WARNING: "⚠️",
                CheckStatus.SKIP: "⏭️"
            }.get(result.status, "❓")
            print(f"状态: {status_icon} {result.status.value}")

            if result.issues:
                print(f"\n发现 {len(result.issues)} 个问题:")
                for issue in result.issues[:10]:
                    severity_icon = {
                        IssueSeverity.CRITICAL: "🔴",
                        IssueSeverity.HIGH: "🟠",
                        IssueSeverity.MEDIUM: "🟡",
                        IssueSeverity.LOW: "🔵"
                    }.get(issue.severity, "⚪")
                    print(f"\n  {severity_icon} [{issue.severity.value.upper()}] {issue.issue_type}")
                    if issue.principle:
                        print(f"     原则: {issue.principle}")
                    print(f"     文件: {issue.file_path}")
                    if issue.line_number:
                        print(f"     行号: {issue.line_number}")
                    print(f"     描述: {issue.description}")
                    if issue.suggestion:
                        print(f"     建议: {issue.suggestion}")
                
                if len(result.issues) > 10:
                    print(f"\n  ... 还有 {len(result.issues) - 10} 个问题未显示")

    def save_report(self, report: ArchitectureReport, output_dir: Optional[Path] = None) -> Path:
        """保存报告"""
        if output_dir is None:
            output_dir = self.path_manager.get_docs_reports_path()
        output_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_path = output_dir / f"architecture_check_{timestamp}.json"

        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report.to_dict(), f, indent=2, ensure_ascii=False)

        latest_path = output_dir / "architecture_check_latest.json"
        with open(latest_path, 'w', encoding='utf-8') as f:
            json.dump(report.to_dict(), f, indent=2, ensure_ascii=False)

        self.logger.info(f"报告已保存: {report_path}")
        return report_path


def setup_logger(verbose: bool = False) -> logging.Logger:
    """配置日志记录器"""
    logger = logging.getLogger("ArchitectureChecker")
    logger.setLevel(logging.DEBUG if verbose else logging.INFO)

    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(logging.DEBUG if verbose else logging.INFO)
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    return logger


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="架构检查脚本",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python architecture_check.py
  python architecture_check.py --output json --output-file result.json
  python architecture_check.py --strict
  python architecture_check.py --verbose
  python architecture_check.py --check solid
  python architecture_check.py --check mvvm
        """
    )

    parser.add_argument(
        "--strict",
        action="store_true",
        help="严格模式：任何警告都视为失败"
    )

    parser.add_argument(
        "--output",
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
        "--verbose",
        action="store_true",
        help="启用详细日志输出"
    )

    parser.add_argument(
        "--check",
        choices=["all", "solid", "mvvm", "principles", "structure"],
        default="all",
        help="指定检查类型 (默认: all)"
    )

    args = parser.parse_args()

    logger = setup_logger(args.verbose)

    checker = ArchitectureChecker(strict=args.strict, logger=logger)
    report = checker.run_all_checks()

    checker.print_report(report)

    report_path = checker.save_report(report)
    print(f"\n报告已保存到: {report_path}")

    if args.output == "json":
        output_data = json.dumps(report.to_dict(), ensure_ascii=False, indent=2)

        if args.output_file:
            output_path = Path(args.output_file)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(output_data)
            print(f"\nJSON结果已保存到: {output_path}")
        else:
            print("\nJSON结果:")
            print(output_data)

    return 0 if report.overall_passed else 1


if __name__ == "__main__":
    sys.exit(main())
