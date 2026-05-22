#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
系统性优化扫描器

整合多种扫描器对项目进行全面检查，包括：
1. 架构优化扫描器 - MVVM/MVC架构合规性、SOLID原则
2. 需求优化扫描器 - 需求文档完整性和一致性
3. 设计优化扫描器 - 设计文档和实现一致性
4. 原则规范扫描器 - 编码规范和最佳实践
5. 逻辑链扫描器 - 业务逻辑链完整性
6. 代码审查扫描器 - 代码质量问题
7. 前后端模块扫描器 - 模块间接口一致性
8. 业务链扫描器 - 业务流程完整性
9. 数据扫描器 - 数据模型和数据流
10. 日志扫描器 - 日志记录规范性
11. 错误处理扫描器 - 异常处理完整性
12. GUI界面扫描器 - 界面一致性
13. UI/UX扫描器 - UI/UX问题检查

使用示例:
    python systematic_optimizer.py
    python systematic_optimizer.py --scanners architecture,code_review
    python systematic_optimizer.py --output json --output-file result.json
    python systematic_optimizer.py --verbose
"""

import os
import sys
import ast
import re
import json
import argparse
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Set, Tuple, Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from abc import ABC, abstractmethod

sys.path.insert(0, str(get_path_config().SKILL_ROOT / "skillscripts" / "utils"))
from path_config_manager import PathConfigManager


class IssueSeverity(Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class ScannerCategory(Enum):
    ARCHITECTURE = "architecture"
    REQUIREMENT = "requirement"
    DESIGN = "design"
    PRINCIPLE = "principle"
    LOGIC = "logic"
    CODE_REVIEW = "code_review"
    FRONTEND_BACKEND = "frontend_backend"
    BUSINESS = "business"
    DATA = "data"
    LOGGING = "logging"
    ERROR_HANDLING = "error_handling"
    GUI = "gui"
    UI_UX = "ui_ux"
    PERFORMANCE_CPU = "performance_cpu"
    PERFORMANCE_MEMORY = "performance_memory"
    PERFORMANCE_IO = "performance_io"
    PERFORMANCE_NETWORK = "performance_network"


@dataclass
class OptimizationIssue:
    file_path: str
    scanner_name: str
    issue_type: str
    description: str
    severity: IssueSeverity
    line_number: Optional[int] = None
    code_snippet: str = ""
    suggestion: str = ""
    category: ScannerCategory = ScannerCategory.CODE_REVIEW

    def to_dict(self) -> Dict[str, Any]:
        return {
            "file_path": self.file_path,
            "scanner_name": self.scanner_name,
            "issue_type": self.issue_type,
            "description": self.description,
            "severity": self.severity.value,
            "line_number": self.line_number,
            "code_snippet": self.code_snippet,
            "suggestion": self.suggestion,
            "category": self.category.value
        }


@dataclass
class ScannerResult:
    scanner_name: str
    category: ScannerCategory
    issues: List[OptimizationIssue] = field(default_factory=list)
    files_scanned: int = 0
    scan_time_ms: float = 0.0
    details: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "scanner_name": self.scanner_name,
            "category": self.category.value,
            "issues": [i.to_dict() for i in self.issues],
            "files_scanned": self.files_scanned,
            "scan_time_ms": round(self.scan_time_ms, 2),
            "issue_count": len(self.issues),
            "details": self.details
        }


@dataclass
class OptimizationReport:
    timestamp: str
    project_root: str
    total_scanners: int
    total_issues: int
    results: List[ScannerResult]
    summary: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp,
            "project_root": self.project_root,
            "total_scanners": self.total_scanners,
            "total_issues": self.total_issues,
            "summary": self.summary,
            "results": [r.to_dict() for r in self.results]
        }


class BaseScanner(ABC):
    def __init__(self, project_root: Path, logger: logging.Logger):
        self.project_root = project_root
        self.logger = logger
        self.issues: List[OptimizationIssue] = []
        self.path_manager = PathConfigManager()

    @abstractmethod
    def scan(self) -> ScannerResult:
        pass

    @property
    @abstractmethod
    def name(self) -> str:
        pass

    @property
    @abstractmethod
    def category(self) -> ScannerCategory:
        pass

    def _read_file(self, file_path: Path) -> Optional[str]:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            self.logger.warning(f"无法读取文件 {file_path}: {e}")
            return None

    def _parse_ast(self, content: str) -> Optional[ast.AST]:
        try:
            return ast.parse(content)
        except SyntaxError as e:
            return None


class ArchitectureScanner(BaseScanner):
    MVVM_LAYERS = {
        "model": ["models", "model"],
        "view": ["views", "view", "components", "pages"],
        "viewmodel": ["viewmodels", "viewmodel", "stores", "services"]
    }

    MVC_LAYERS = {
        "model": ["models", "model"],
        "view": ["views", "view", "templates", "components"],
        "controller": ["controllers", "controller", "routers", "api"]
    }

    SOLID_CHECKS = {
        "single_responsibility": "单一职责原则",
        "open_closed": "开闭原则",
        "liskov_substitution": "里氏替换原则",
        "interface_segregation": "接口隔离原则",
        "dependency_inversion": "依赖倒置原则"
    }

    @property
    def name(self) -> str:
        return "架构优化扫描器"

    @property
    def category(self) -> ScannerCategory:
        return ScannerCategory.ARCHITECTURE

    def scan(self) -> ScannerResult:
        import time
        start_time = time.perf_counter()
        self.issues = []
        files_scanned = 0

        backend_dir = self.path_manager.get_backend_path()
        frontend_dir = self.path_manager.get_frontend_path()

        if backend_dir.exists():
            files_scanned += self._check_backend_architecture(backend_dir)
            files_scanned += self._check_solid_principles(backend_dir)

        if frontend_dir.exists():
            files_scanned += self._check_frontend_architecture(frontend_dir)

        self._check_layer_separation()

        end_time = time.perf_counter()
        return ScannerResult(
            scanner_name=self.name,
            category=self.category,
            issues=self.issues,
            files_scanned=files_scanned,
            scan_time_ms=(end_time - start_time) * 1000
        )

    def _check_backend_architecture(self, backend_dir: Path) -> int:
        files_scanned = 0
        app_dir = backend_dir / "app"
        if not app_dir.exists():
            return files_scanned

        for py_file in app_dir.rglob("*.py"):
            if "__pycache__" in str(py_file):
                continue
            files_scanned += 1
            content = self._read_file(py_file)
            if not content:
                continue

            tree = self._parse_ast(content)
            if not tree:
                continue

            self._check_mvc_compliance(py_file, tree)
            self._check_dependency_direction(py_file, tree)

        return files_scanned

    def _check_mvc_compliance(self, file_path: Path, tree: ast.AST):
        file_str = str(file_path).lower()

        if "routers" in file_str or "api" in file_str:
            self._check_controller_responsibilities(file_path, tree)
        elif "models" in file_str:
            self._check_model_responsibilities(file_path, tree)
        elif "services" in file_str:
            self._check_service_responsibilities(file_path, tree)

    def _check_controller_responsibilities(self, file_path: Path, tree: ast.AST):
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                if self._has_database_operations(node):
                    self.issues.append(OptimizationIssue(
                        file_path=str(file_path),
                        scanner_name=self.name,
                        issue_type="mvc_violation",
                        description="控制器层包含数据库操作，违反MVC分层原则",
                        severity=IssueSeverity.HIGH,
                        line_number=node.lineno,
                        suggestion="将数据库操作移至服务层或模型层"
                    ))

    def _check_model_responsibilities(self, file_path: Path, tree: ast.AST):
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                if self._has_http_operations(node):
                    self.issues.append(OptimizationIssue(
                        file_path=str(file_path),
                        scanner_name=self.name,
                        issue_type="mvc_violation",
                        description="模型层包含HTTP操作，违反MVC分层原则",
                        severity=IssueSeverity.HIGH,
                        line_number=node.lineno,
                        suggestion="将HTTP操作移至控制器层"
                    ))

    def _check_service_responsibilities(self, file_path: Path, tree: ast.AST):
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                if self._has_http_operations(node):
                    self.issues.append(OptimizationIssue(
                        file_path=str(file_path),
                        scanner_name=self.name,
                        issue_type="mvc_violation",
                        description="服务层包含HTTP操作，应保持业务逻辑纯净",
                        severity=IssueSeverity.MEDIUM,
                        line_number=node.lineno,
                        suggestion="将HTTP响应处理移至控制器层"
                    ))

    def _check_dependency_direction(self, file_path: Path, tree: ast.AST):
        file_str = str(file_path).lower()
        forbidden_imports = []

        if "models" in file_str:
            forbidden_imports = ["routers", "api", "controllers"]
        elif "services" in file_str:
            forbidden_imports = ["routers", "api"]

        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module:
                for forbidden in forbidden_imports:
                    if forbidden in node.module:
                        self.issues.append(OptimizationIssue(
                            file_path=str(file_path),
                            scanner_name=self.name,
                            issue_type="dependency_violation",
                            description=f"违反依赖方向：从 {file_path.name} 导入 {node.module}",
                            severity=IssueSeverity.HIGH,
                            line_number=node.lineno,
                            suggestion="调整依赖方向，遵循分层架构原则"
                        ))

    def _check_frontend_architecture(self, frontend_dir: Path) -> int:
        files_scanned = 0
        src_dir = frontend_dir / "src"
        if not src_dir.exists():
            return files_scanned

        for vue_file in src_dir.rglob("*.vue"):
            if "__pycache__" in str(vue_file):
                continue
            files_scanned += 1
            content = self._read_file(vue_file)
            if content:
                self._check_vue_component_structure(vue_file, content)

        for ts_file in src_dir.rglob("*.ts"):
            if "__pycache__" in str(ts_file):
                continue
            files_scanned += 1

        return files_scanned

    def _check_vue_component_structure(self, file_path: Path, content: str):
        if "<script" in content and "setup" not in content:
            self.issues.append(OptimizationIssue(
                file_path=str(file_path),
                scanner_name=self.name,
                issue_type="vue_composition_api",
                description="建议使用Vue 3 Composition API (setup语法糖)",
                severity=IssueSeverity.LOW,
                suggestion="使用 <script setup lang='ts'> 语法"
            ))

        if "defineComponent" in content and "setup()" in content:
            self.issues.append(OptimizationIssue(
                file_path=str(file_path),
                scanner_name=self.name,
                issue_type="vue_options_api",
                description="使用Options API，建议迁移至Composition API",
                severity=IssueSeverity.INFO,
                suggestion="重构为Composition API以提高代码可维护性"
            ))

    def _check_solid_principles(self, backend_dir: Path) -> int:
        files_scanned = 0
        app_dir = backend_dir / "app"
        if not app_dir.exists():
            return files_scanned

        for py_file in app_dir.rglob("*.py"):
            if "__pycache__" in str(py_file):
                continue
            files_scanned += 1
            content = self._read_file(py_file)
            if not content:
                continue

            tree = self._parse_ast(content)
            if not tree:
                continue

            self._check_single_responsibility(py_file, tree)
            self._check_dependency_inversion(py_file, tree)

        return files_scanned

    def _check_single_responsibility(self, file_path: Path, tree: ast.AST):
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                methods = [n for n in node.body if isinstance(n, ast.FunctionDef)]
                if len(methods) > 15:
                    self.issues.append(OptimizationIssue(
                        file_path=str(file_path),
                        scanner_name=self.name,
                        issue_type="single_responsibility_violation",
                        description=f"类 {node.name} 包含 {len(methods)} 个方法，可能违反单一职责原则",
                        severity=IssueSeverity.MEDIUM,
                        line_number=node.lineno,
                        suggestion="考虑将类拆分为多个更小的类，每个类只负责一项职责"
                    ))

    def _check_dependency_inversion(self, file_path: Path, tree: ast.AST):
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                for item in node.body:
                    if isinstance(item, ast.Assign):
                        for target in item.targets:
                            if isinstance(target, ast.Name):
                                if self._is_concrete_instantiation(item.value):
                                    self.issues.append(OptimizationIssue(
                                        file_path=str(file_path),
                                        scanner_name=self.name,
                                        issue_type="dependency_inversion_violation",
                                        description=f"类 {node.name} 直接实例化具体类，违反依赖倒置原则",
                                        severity=IssueSeverity.MEDIUM,
                                        line_number=item.lineno,
                                        suggestion="使用依赖注入，依赖抽象而非具体实现"
                                    ))

    def _check_layer_separation(self):
        backend_dir = self.project_root / "backend"
        if not backend_dir.exists():
            return

        app_dir = backend_dir / "app"
        if not app_dir.exists():
            return

        expected_dirs = ["models", "routers", "services"]
        for expected_dir in expected_dirs:
            if not (app_dir / expected_dir).exists():
                self.issues.append(OptimizationIssue(
                    file_path=str(app_dir / expected_dir),
                    scanner_name=self.name,
                    issue_type="missing_layer",
                    description=f"缺少预期的架构层目录: {expected_dir}",
                    severity=IssueSeverity.HIGH,
                    suggestion=f"创建 {expected_dir} 目录以保持架构完整性"
                ))

    def _has_database_operations(self, node: ast.FunctionDef) -> bool:
        for child in ast.walk(node):
            if isinstance(child, ast.Attribute):
                if child.attr in ["query", "filter", "create", "update", "delete", "save"]:
                    return True
        return False

    def _has_http_operations(self, node: ast.FunctionDef) -> bool:
        for child in ast.walk(node):
            if isinstance(child, ast.Attribute):
                if child.attr in ["json", "status_code", "headers"]:
                    return True
            if isinstance(child, ast.Name):
                if child.id in ["Response", "JSONResponse", "HTTPException"]:
                    return True
        return False

    def _is_concrete_instantiation(self, node: ast.AST) -> bool:
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                return not node.func.id.startswith("Abstract") and not node.func.id.startswith("I")
        return False


class RequirementScanner(BaseScanner):
    @property
    def name(self) -> str:
        return "需求优化扫描器"

    @property
    def category(self) -> ScannerCategory:
        return ScannerCategory.REQUIREMENT

    def scan(self) -> ScannerResult:
        import time
        start_time = time.perf_counter()
        self.issues = []
        files_scanned = 0

        docs_dir = get_path_config().DOCS_DIR
        if docs_dir.exists():
            files_scanned += self._check_requirement_docs(docs_dir)

        self._check_requirement_traces()

        end_time = time.perf_counter()
        return ScannerResult(
            scanner_name=self.name,
            category=self.category,
            issues=self.issues,
            files_scanned=files_scanned,
            scan_time_ms=(end_time - start_time) * 1000
        )

    def _check_requirement_docs(self, docs_dir: Path) -> int:
        files_scanned = 0
        requirement_files = list(docs_dir.rglob("*requirement*.md")) + \
                           list(docs_dir.rglob("*需求*.md"))

        for req_file in requirement_files:
            files_scanned += 1
            content = self._read_file(req_file)
            if content:
                self._check_requirement_completeness(req_file, content)

        if not requirement_files:
            self.issues.append(OptimizationIssue(
                file_path=str(docs_dir),
                scanner_name=self.name,
                issue_type="missing_requirements",
                description="未找到需求文档",
                severity=IssueSeverity.HIGH,
                suggestion="创建需求文档，明确项目功能需求"
            ))

        return files_scanned

    def _check_requirement_completeness(self, file_path: Path, content: str):
        required_sections = [
            ("功能需求", ["功能", "functionality"]),
            ("非功能需求", ["非功能", "non-functional", "性能", "安全"]),
            ("用户故事", ["用户故事", "user story", "user story"]),
            ("验收标准", ["验收", "acceptance", "验收标准"])
        ]

        content_lower = content.lower()
        for section_name, keywords in required_sections:
            if not any(kw.lower() in content_lower for kw in keywords):
                self.issues.append(OptimizationIssue(
                    file_path=str(file_path),
                    scanner_name=self.name,
                    issue_type="incomplete_requirement",
                    description=f"需求文档缺少 '{section_name}' 部分",
                    severity=IssueSeverity.MEDIUM,
                    suggestion=f"补充 {section_name} 相关内容"
                ))

    def _check_requirement_traces(self):
        backend_dir = self.project_root / "backend"
        if not backend_dir.exists():
            return

        app_dir = backend_dir / "app"
        if not app_dir.exists():
            return

        models_dir = app_dir / "models"
        if models_dir.exists():
            trace_file = models_dir.parent / "models" / "requirement_trace.py"
            if not trace_file.exists():
                self.issues.append(OptimizationIssue(
                    file_path=str(app_dir),
                    scanner_name=self.name,
                    issue_type="missing_traceability",
                    description="缺少需求追溯模型",
                    severity=IssueSeverity.MEDIUM,
                    suggestion="创建需求追溯模型，建立需求与代码的映射关系"
                ))


class DesignScanner(BaseScanner):
    @property
    def name(self) -> str:
        return "设计优化扫描器"

    @property
    def category(self) -> ScannerCategory:
        return ScannerCategory.DESIGN

    def scan(self) -> ScannerResult:
        import time
        start_time = time.perf_counter()
        self.issues = []
        files_scanned = 0

        docs_dir = get_path_config().DOCS_DIR
        if docs_dir.exists():
            files_scanned += self._check_design_docs(docs_dir)

        self._check_design_implementation_consistency()

        end_time = time.perf_counter()
        return ScannerResult(
            scanner_name=self.name,
            category=self.category,
            issues=self.issues,
            files_scanned=files_scanned,
            scan_time_ms=(end_time - start_time) * 1000
        )

    def _check_design_docs(self, docs_dir: Path) -> int:
        files_scanned = 0
        design_files = list(docs_dir.rglob("*design*.md")) + \
                      list(docs_dir.rglob("*设计*.md")) + \
                      list(docs_dir.rglob("*architecture*.md"))

        for design_file in design_files:
            files_scanned += 1
            content = self._read_file(design_file)
            if content:
                self._check_design_completeness(design_file, content)

        return files_scanned

    def _check_design_completeness(self, file_path: Path, content: str):
        design_elements = [
            ("系统架构", ["架构", "architecture", "系统设计"]),
            ("数据模型", ["数据模型", "data model", "er图", "数据库"]),
            ("接口设计", ["接口", "api", "interface"]),
            ("部署架构", ["部署", "deployment", "docker"])
        ]

        content_lower = content.lower()
        for element_name, keywords in design_elements:
            if not any(kw.lower() in content_lower for kw in keywords):
                self.issues.append(OptimizationIssue(
                    file_path=str(file_path),
                    scanner_name=self.name,
                    issue_type="incomplete_design",
                    description=f"设计文档缺少 '{element_name}' 部分",
                    severity=IssueSeverity.MEDIUM,
                    suggestion=f"补充 {element_name} 相关设计内容"
                ))

    def _check_design_implementation_consistency(self):
        backend_dir = self.path_manager.get_backend_path()
        if not backend_dir.exists():
            return

        app_dir = backend_dir / "app"
        models_dir = app_dir / "models" if app_dir.exists() else None

        if models_dir and models_dir.exists():
            model_files = list(models_dir.glob("*.py"))
            if len(model_files) < 3:
                self.issues.append(OptimizationIssue(
                    file_path=str(models_dir),
                    scanner_name=self.name,
                    issue_type="insufficient_models",
                    description=f"数据模型数量较少({len(model_files)}个)，可能设计不完整",
                    severity=IssueSeverity.LOW,
                    suggestion="检查是否遗漏了必要的实体模型"
                ))


class PrincipleScanner(BaseScanner):
    @property
    def name(self) -> str:
        return "原则规范扫描器"

    @property
    def category(self) -> ScannerCategory:
        return ScannerCategory.PRINCIPLE

    def scan(self) -> ScannerResult:
        import time
        start_time = time.perf_counter()
        self.issues = []
        files_scanned = 0

        backend_dir = self.path_manager.get_backend_path()
        if backend_dir.exists():
            files_scanned += self._check_coding_standards(backend_dir)

        frontend_dir = self.project_root / "frontend"
        if frontend_dir.exists():
            files_scanned += self._check_frontend_standards(frontend_dir)

        end_time = time.perf_counter()
        return ScannerResult(
            scanner_name=self.name,
            category=self.category,
            issues=self.issues,
            files_scanned=files_scanned,
            scan_time_ms=(end_time - start_time) * 1000
        )

    def _check_coding_standards(self, backend_dir: Path) -> int:
        files_scanned = 0
        app_dir = backend_dir / "app"
        if not app_dir.exists():
            return files_scanned

        for py_file in app_dir.rglob("*.py"):
            if "__pycache__" in str(py_file):
                continue
            files_scanned += 1
            content = self._read_file(py_file)
            if not content:
                continue

            lines = content.split('\n')
            self._check_python_style(py_file, lines)
            self._check_docstrings(py_file, content)

        return files_scanned

    def _check_python_style(self, file_path: Path, lines: List[str]):
        for i, line in enumerate(lines, 1):
            if len(line) > 120:
                self.issues.append(OptimizationIssue(
                    file_path=str(file_path),
                    scanner_name=self.name,
                    issue_type="line_too_long",
                    description=f"行 {i} 超过120字符 ({len(line)}字符)",
                    severity=IssueSeverity.LOW,
                    line_number=i,
                    code_snippet=line[:80] + "..." if len(line) > 80 else line,
                    suggestion="拆分行或简化代码"
                ))

            if line.rstrip() != line.rstrip('\n').rstrip() and line.strip():
                self.issues.append(OptimizationIssue(
                    file_path=str(file_path),
                    scanner_name=self.name,
                    issue_type="trailing_whitespace",
                    description=f"行 {i} 有尾随空格",
                    severity=IssueSeverity.LOW,
                    line_number=i,
                    suggestion="删除尾随空格"
                ))

    def _check_docstrings(self, file_path: Path, content: str):
        tree = self._parse_ast(content)
        if not tree:
            return

        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.ClassDef)):
                if not ast.get_docstring(node):
                    if isinstance(node, ast.ClassDef) or \
                       (isinstance(node, ast.FunctionDef) and not node.name.startswith('_')):
                        self.issues.append(OptimizationIssue(
                            file_path=str(file_path),
                            scanner_name=self.name,
                            issue_type="missing_docstring",
                            description=f"{node.name} 缺少文档字符串",
                            severity=IssueSeverity.LOW,
                            line_number=node.lineno,
                            suggestion="添加文档字符串说明功能"
                        ))

    def _check_frontend_standards(self, frontend_dir: Path) -> int:
        files_scanned = 0
        src_dir = frontend_dir / "src"
        if not src_dir.exists():
            return files_scanned

        for ts_file in src_dir.rglob("*.ts"):
            if "__pycache__" in str(ts_file):
                continue
            files_scanned += 1
            content = self._read_file(ts_file)
            if content:
                self._check_typescript_style(ts_file, content)

        for vue_file in src_dir.rglob("*.vue"):
            if "__pycache__" in str(vue_file):
                continue
            files_scanned += 1
            content = self._read_file(vue_file)
            if content:
                self._check_vue_style(vue_file, content)

        return files_scanned

    def _check_typescript_style(self, file_path: Path, content: str):
        if ": any" in content:
            self.issues.append(OptimizationIssue(
                file_path=str(file_path),
                scanner_name=self.name,
                issue_type="any_type_usage",
                description="使用了 any 类型，降低类型安全性",
                severity=IssueSeverity.MEDIUM,
                suggestion="使用具体类型替代 any"
            ))

        if "console.log" in content:
            self.issues.append(OptimizationIssue(
                file_path=str(file_path),
                scanner_name=self.name,
                issue_type="console_log_usage",
                description="使用 console.log，生产环境应使用日志库",
                severity=IssueSeverity.LOW,
                suggestion="使用适当的日志库替代 console.log"
            ))

    def _check_vue_style(self, file_path: Path, content: str):
        if "v-for" in content and ":key" not in content:
            self.issues.append(OptimizationIssue(
                file_path=str(file_path),
                scanner_name=self.name,
                issue_type="missing_vfor_key",
                description="v-for 指令缺少 :key 绑定",
                severity=IssueSeverity.HIGH,
                suggestion="为 v-for 添加唯一的 :key 绑定"
            ))


class LogicChainScanner(BaseScanner):
    @property
    def name(self) -> str:
        return "逻辑链扫描器"

    @property
    def category(self) -> ScannerCategory:
        return ScannerCategory.LOGIC

    def scan(self) -> ScannerResult:
        import time
        start_time = time.perf_counter()
        self.issues = []
        files_scanned = 0

        backend_dir = self.project_root / "backend"
        if backend_dir.exists():
            files_scanned += self._check_logic_chains(backend_dir)

        end_time = time.perf_counter()
        return ScannerResult(
            scanner_name=self.name,
            category=self.category,
            issues=self.issues,
            files_scanned=files_scanned,
            scan_time_ms=(end_time - start_time) * 1000
        )

    def _check_logic_chains(self, backend_dir: Path) -> int:
        files_scanned = 0
        app_dir = backend_dir / "app"
        if not app_dir.exists():
            return files_scanned

        services_dir = app_dir / "services"
        if services_dir.exists():
            for service_file in services_dir.rglob("*.py"):
                if "__pycache__" in str(service_file):
                    continue
                files_scanned += 1
                content = self._read_file(service_file)
                if content:
                    self._check_service_logic(service_file, content)

        return files_scanned

    def _check_service_logic(self, file_path: Path, content: str):
        tree = self._parse_ast(content)
        if not tree:
            return

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                self._check_function_logic(file_path, node)

    def _check_function_logic(self, file_path: Path, node: ast.FunctionDef):
        has_try_except = False
        has_return = False
        has_validation = False

        for child in ast.walk(node):
            if isinstance(child, ast.Try):
                has_try_except = True
            if isinstance(child, ast.Return):
                has_return = True
            if isinstance(child, ast.Call):
                if isinstance(child.func, ast.Attribute):
                    if child.func.attr in ["validate", "check", "verify"]:
                        has_validation = True

        if node.body and not node.name.startswith('_'):
            if not has_try_except and len(list(ast.walk(node))) > 20:
                self.issues.append(OptimizationIssue(
                    file_path=str(file_path),
                    scanner_name=self.name,
                    issue_type="missing_error_handling",
                    description=f"函数 {node.name} 缺少异常处理",
                    severity=IssueSeverity.MEDIUM,
                    line_number=node.lineno,
                    suggestion="添加 try-except 块处理潜在异常"
                ))


class CodeReviewScanner(BaseScanner):
    CODE_SMELL_PATTERNS = {
        "too_many_arguments": {
            "pattern": r"def\s+\w+\s*\([^)]{80,}\)",
            "description": "函数参数过多",
            "severity": IssueSeverity.MEDIUM,
            "suggestion": "考虑使用对象封装参数"
        },
        "bare_except": {
            "pattern": r"except\s*:",
            "description": "使用裸异常捕获",
            "severity": IssueSeverity.HIGH,
            "suggestion": "捕获具体的异常类型"
        },
        "mutable_default": {
            "pattern": r"def\s+\w+\s*\([^)]*=\s*(\[\s*\]|\{\s*\})",
            "description": "使用可变默认参数",
            "severity": IssueSeverity.HIGH,
            "suggestion": "使用None作为默认值，在函数内部初始化"
        },
        "todo_comment": {
            "pattern": r"#\s*(TODO|FIXME|XXX|HACK)",
            "description": "发现待办事项注释",
            "severity": IssueSeverity.INFO,
            "suggestion": "及时处理待办事项"
        }
    }

    @property
    def name(self) -> str:
        return "代码审查扫描器"

    @property
    def category(self) -> ScannerCategory:
        return ScannerCategory.CODE_REVIEW

    def scan(self) -> ScannerResult:
        import time
        start_time = time.perf_counter()
        self.issues = []
        files_scanned = 0

        backend_dir = self.project_root / "backend"
        if backend_dir.exists():
            files_scanned += self._scan_python_files(backend_dir)

        frontend_dir = self.project_root / "frontend"
        if frontend_dir.exists():
            files_scanned += self._scan_frontend_files(frontend_dir)

        end_time = time.perf_counter()
        return ScannerResult(
            scanner_name=self.name,
            category=self.category,
            issues=self.issues,
            files_scanned=files_scanned,
            scan_time_ms=(end_time - start_time) * 1000
        )

    def _scan_python_files(self, backend_dir: Path) -> int:
        files_scanned = 0
        for py_file in backend_dir.rglob("*.py"):
            if "__pycache__" in str(py_file) or "test" in py_file.name.lower():
                continue
            files_scanned += 1
            content = self._read_file(py_file)
            if content:
                self._check_code_smells(py_file, content)
                self._check_unused_code(py_file, content)

        return files_scanned

    def _check_code_smells(self, file_path: Path, content: str):
        lines = content.split('\n')
        for i, line in enumerate(lines, 1):
            for smell_name, smell_config in self.CODE_SMELL_PATTERNS.items():
                if re.search(smell_config["pattern"], line):
                    self.issues.append(OptimizationIssue(
                        file_path=str(file_path),
                        scanner_name=self.name,
                        issue_type="code_smell",
                        description=smell_config["description"],
                        severity=smell_config["severity"],
                        line_number=i,
                        code_snippet=line.strip()[:80],
                        suggestion=smell_config["suggestion"]
                    ))

    def _check_unused_code(self, file_path: Path, content: str):
        tree = self._parse_ast(content)
        if not tree:
            return

        imports = set()
        used_names = set()

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.add((alias.asname or alias.name, node.lineno))
            elif isinstance(node, ast.ImportFrom):
                for alias in node.names:
                    imports.add((alias.asname or alias.name, node.lineno))
            elif isinstance(node, ast.Name):
                used_names.add(node.id)

        for name, lineno in imports:
            if name not in used_names and not name.startswith('_'):
                self.issues.append(OptimizationIssue(
                    file_path=str(file_path),
                    scanner_name=self.name,
                    issue_type="unused_import",
                    description=f"未使用的导入: {name}",
                    severity=IssueSeverity.MEDIUM,
                    line_number=lineno,
                    suggestion=f"删除未使用的导入: {name}"
                ))

    def _scan_frontend_files(self, frontend_dir: Path) -> int:
        files_scanned = 0
        src_dir = frontend_dir / "src"
        if not src_dir.exists():
            return files_scanned

        for ts_file in src_dir.rglob("*.ts"):
            if "__pycache__" in str(ts_file):
                continue
            files_scanned += 1
            content = self._read_file(ts_file)
            if content:
                self._check_typescript_issues(ts_file, content)

        return files_scanned

    def _check_typescript_issues(self, file_path: Path, content: str):
        if "debugger" in content:
            self.issues.append(OptimizationIssue(
                file_path=str(file_path),
                scanner_name=self.name,
                issue_type="debugger_statement",
                description="发现 debugger 语句",
                severity=IssueSeverity.HIGH,
                suggestion="移除 debugger 语句"
            ))


class CodeQualityEnhancedScanner(BaseScanner):
    @property
    def name(self) -> str:
        return "代码质量增强扫描器"

    @property
    def category(self) -> ScannerCategory:
        return ScannerCategory.CODE_REVIEW

    def scan(self) -> ScannerResult:
        import time
        start_time = time.perf_counter()
        self.issues = []
        files_scanned = 0

        try:
            from code_quality_optimizer_enhanced import UnifiedCodeQualityOptimizer
            
            optimizer = UnifiedCodeQualityOptimizer(self.project_root)
            
            complexity_issues = optimizer.complexity_analyzer.analyze_complexity(self.project_root)
            files_scanned += len(complexity_issues)
            
            for issue in complexity_issues:
                severity = IssueSeverity.HIGH if issue.complexity_level.value in ['high', 'very_high'] else IssueSeverity.MEDIUM
                
                self.issues.append(OptimizationIssue(
                    file_path=issue.file_path,
                    scanner_name=self.name,
                    issue_type=f"complexity_{issue.complexity_type}",
                    description=issue.description,
                    severity=severity,
                    line_number=issue.line_number,
                    suggestion=issue.suggestions[0] if issue.suggestions else "建议重构降低复杂度",
                    category=ScannerCategory.CODE_REVIEW
                ))
            
            duplication_issues = optimizer.duplication_detector.detect_duplications(self.project_root)
            
            for issue in duplication_issues:
                self.issues.append(OptimizationIssue(
                    file_path=issue.file_path,
                    scanner_name=self.name,
                    issue_type="code_duplication",
                    description=f"发现代码重复: {issue.duplicate_count} 处重复",
                    severity=IssueSeverity.MEDIUM,
                    line_number=issue.line_numbers[0] if issue.line_numbers else None,
                    suggestion=issue.suggested_refactoring,
                    category=ScannerCategory.CODE_REVIEW
                ))
            
        except Exception as e:
            self.logger.warning(f"代码质量增强扫描失败: {e}")

        end_time = time.perf_counter()
        return ScannerResult(
            scanner_name=self.name,
            category=self.category,
            issues=self.issues,
            files_scanned=files_scanned,
            scan_time_ms=(end_time - start_time) * 1000,
            details={
                'enhanced_scanning': True,
                'safe_refactoring_available': True
            }
        )


class FrontendBackendScanner(BaseScanner):
    @property
    def name(self) -> str:
        return "前后端模块扫描器"

    @property
    def category(self) -> ScannerCategory:
        return ScannerCategory.FRONTEND_BACKEND

    def scan(self) -> ScannerResult:
        import time
        start_time = time.perf_counter()
        self.issues = []
        files_scanned = 0

        backend_api = self.project_root / "backend" / "app" / "api"
        frontend_api = self.project_root / "frontend" / "src" / "api"

        backend_endpoints = set()
        frontend_calls = set()

        if backend_api.exists():
            files_scanned, backend_endpoints = self._extract_backend_endpoints(backend_api, files_scanned)

        if frontend_api.exists():
            files_scanned, frontend_calls = self._extract_frontend_calls(frontend_api, files_scanned)

        self._check_api_consistency(backend_endpoints, frontend_calls)

        end_time = time.perf_counter()
        return ScannerResult(
            scanner_name=self.name,
            category=self.category,
            issues=self.issues,
            files_scanned=files_scanned,
            scan_time_ms=(end_time - start_time) * 1000
        )

    def _extract_backend_endpoints(self, api_dir: Path, files_scanned: int) -> Tuple[int, Set[str]]:
        endpoints = set()
        for py_file in api_dir.rglob("*.py"):
            if "__pycache__" in str(py_file):
                continue
            files_scanned += 1
            content = self._read_file(py_file)
            if content:
                for match in re.finditer(r'@(?:router|app)\.(?:get|post|put|delete|patch)\s*\(\s*["\']([^"\']+)["\']', content):
                    endpoints.add(match.group(1))

        return files_scanned, endpoints

    def _extract_frontend_calls(self, api_dir: Path, files_scanned: int) -> Tuple[int, Set[str]]:
        calls = set()
        for ts_file in api_dir.rglob("*.ts"):
            if "__pycache__" in str(ts_file):
                continue
            files_scanned += 1
            content = self._read_file(ts_file)
            if content:
                for match in re.finditer(r'(?:get|post|put|delete|patch)\s*\(\s*["\']([^"\']+)["\']', content):
                    calls.add(match.group(1))

        return files_scanned, calls

    def _check_api_consistency(self, backend_endpoints: Set[str], frontend_calls: Set[str]):
        unused_endpoints = backend_endpoints - frontend_calls
        for endpoint in unused_endpoints:
            self.issues.append(OptimizationIssue(
                file_path="backend/api",
                scanner_name=self.name,
                issue_type="unused_endpoint",
                description=f"后端API端点未被前端调用: {endpoint}",
                severity=IssueSeverity.MEDIUM,
                suggestion="检查是否需要此端点或前端是否遗漏调用"
            ))

        missing_endpoints = frontend_calls - backend_endpoints
        for endpoint in missing_endpoints:
            self.issues.append(OptimizationIssue(
                file_path="frontend/api",
                scanner_name=self.name,
                issue_type="missing_endpoint",
                description=f"前端调用的API端点在后端不存在: {endpoint}",
                severity=IssueSeverity.HIGH,
                suggestion="检查API路径是否正确或后端是否缺少此端点"
            ))


class BusinessChainScanner(BaseScanner):
    @property
    def name(self) -> str:
        return "业务链扫描器"

    @property
    def category(self) -> ScannerCategory:
        return ScannerCategory.BUSINESS

    def scan(self) -> ScannerResult:
        import time
        start_time = time.perf_counter()
        self.issues = []
        files_scanned = 0

        backend_dir = self.project_root / "backend"
        if backend_dir.exists():
            files_scanned += self._check_business_flows(backend_dir)

        end_time = time.perf_counter()
        return ScannerResult(
            scanner_name=self.name,
            category=self.category,
            issues=self.issues,
            files_scanned=files_scanned,
            scan_time_ms=(end_time - start_time) * 1000
        )

    def _check_business_flows(self, backend_dir: Path) -> int:
        files_scanned = 0
        app_dir = backend_dir / "app"
        if not app_dir.exists():
            return files_scanned

        services_dir = app_dir / "services"
        if services_dir.exists():
            for service_file in services_dir.rglob("*.py"):
                if "__pycache__" in str(service_file):
                    continue
                files_scanned += 1
                content = self._read_file(service_file)
                if content:
                    self._check_workflow_completeness(service_file, content)

        return files_scanned

    def _check_workflow_completeness(self, file_path: Path, content: str):
        tree = self._parse_ast(content)
        if not tree:
            return

        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                if "workflow" in node.name.lower() or "executor" in node.name.lower():
                    self._check_workflow_class(file_path, node)

    def _check_workflow_class(self, file_path: Path, node: ast.ClassDef):
        methods = {n.name for n in node.body if isinstance(n, ast.FunctionDef)}

        required_methods = ["execute", "validate", "rollback"]
        for method in required_methods:
            if method not in methods:
                self.issues.append(OptimizationIssue(
                    file_path=str(file_path),
                    scanner_name=self.name,
                    issue_type="incomplete_workflow",
                    description=f"工作流类 {node.name} 缺少 {method} 方法",
                    severity=IssueSeverity.MEDIUM,
                    line_number=node.lineno,
                    suggestion=f"实现 {method} 方法以完善工作流"
                ))


class DataScanner(BaseScanner):
    @property
    def name(self) -> str:
        return "数据扫描器"

    @property
    def category(self) -> ScannerCategory:
        return ScannerCategory.DATA

    def scan(self) -> ScannerResult:
        import time
        start_time = time.perf_counter()
        self.issues = []
        files_scanned = 0

        backend_dir = self.project_root / "backend"
        if backend_dir.exists():
            files_scanned += self._check_data_models(backend_dir)

        end_time = time.perf_counter()
        return ScannerResult(
            scanner_name=self.name,
            category=self.category,
            issues=self.issues,
            files_scanned=files_scanned,
            scan_time_ms=(end_time - start_time) * 1000
        )

    def _check_data_models(self, backend_dir: Path) -> int:
        files_scanned = 0
        app_dir = backend_dir / "app"
        if not app_dir.exists():
            return files_scanned

        models_dir = app_dir / "models"
        if models_dir.exists():
            for model_file in models_dir.rglob("*.py"):
                if "__pycache__" in str(model_file) or model_file.name == "__init__.py":
                    continue
                files_scanned += 1
                content = self._read_file(model_file)
                if content:
                    self._check_model_quality(model_file, content)

        return files_scanned

    def _check_model_quality(self, file_path: Path, content: str):
        tree = self._parse_ast(content)
        if not tree:
            return

        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                self._check_model_class(file_path, node, content)

    def _check_model_class(self, file_path: Path, node: ast.ClassDef, content: str):
        has_id = False
        has_created_at = False
        has_updated_at = False

        for child in node.body:
            if isinstance(child, ast.AnnAssign):
                if isinstance(child.target, ast.Name):
                    if child.target.id == "id":
                        has_id = True
                    elif child.target.id == "created_at":
                        has_created_at = True
                    elif child.target.id == "updated_at":
                        has_updated_at = True

        if not has_id and "Base" in content:
            self.issues.append(OptimizationIssue(
                file_path=str(file_path),
                scanner_name=self.name,
                issue_type="missing_primary_key",
                description=f"模型 {node.name} 缺少主键字段",
                severity=IssueSeverity.HIGH,
                line_number=node.lineno,
                suggestion="添加 id 字段作为主键"
            ))

        if not has_created_at and not has_updated_at:
            self.issues.append(OptimizationIssue(
                file_path=str(file_path),
                scanner_name=self.name,
                issue_type="missing_timestamps",
                description=f"模型 {node.name} 缺少时间戳字段",
                severity=IssueSeverity.LOW,
                line_number=node.lineno,
                suggestion="添加 created_at 和 updated_at 字段"
            ))


class LoggingScanner(BaseScanner):
    @property
    def name(self) -> str:
        return "日志扫描器"

    @property
    def category(self) -> ScannerCategory:
        return ScannerCategory.LOGGING

    def scan(self) -> ScannerResult:
        import time
        start_time = time.perf_counter()
        self.issues = []
        files_scanned = 0

        backend_dir = self.project_root / "backend"
        if backend_dir.exists():
            files_scanned += self._check_logging(backend_dir)

        end_time = time.perf_counter()
        return ScannerResult(
            scanner_name=self.name,
            category=self.category,
            issues=self.issues,
            files_scanned=files_scanned,
            scan_time_ms=(end_time - start_time) * 1000
        )

    def _check_logging(self, backend_dir: Path) -> int:
        files_scanned = 0
        app_dir = backend_dir / "app"
        if not app_dir.exists():
            return files_scanned

        for py_file in app_dir.rglob("*.py"):
            if "__pycache__" in str(py_file):
                continue
            files_scanned += 1
            content = self._read_file(py_file)
            if content:
                self._check_logging_usage(py_file, content)

        return files_scanned

    def _check_logging_usage(self, file_path: Path, content: str):
        has_logger = "logger" in content.lower() or "logging" in content
        has_print = "print(" in content

        if has_print and not has_logger:
            self.issues.append(OptimizationIssue(
                file_path=str(file_path),
                scanner_name=self.name,
                issue_type="print_instead_of_logging",
                description="使用 print 而非日志记录器",
                severity=IssueSeverity.MEDIUM,
                suggestion="使用 logging 模块替代 print 语句"
            ))

        tree = self._parse_ast(content)
        if not tree:
            return

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                self._check_function_logging(file_path, node, content)

    def _check_function_logging(self, file_path: Path, node: ast.FunctionDef, content: str):
        func_content = ast.get_source_segment(content, node)
        if not func_content:
            return

        has_logging = "logger." in func_content or "logging." in func_content
        has_error_handling = "except" in func_content

        if has_error_handling and not has_logging:
            self.issues.append(OptimizationIssue(
                file_path=str(file_path),
                scanner_name=self.name,
                issue_type="missing_error_logging",
                description=f"函数 {node.name} 有异常处理但未记录日志",
                severity=IssueSeverity.MEDIUM,
                line_number=node.lineno,
                suggestion="在异常处理中添加日志记录"
            ))


class ErrorHandlingScanner(BaseScanner):
    @property
    def name(self) -> str:
        return "错误处理扫描器"

    @property
    def category(self) -> ScannerCategory:
        return ScannerCategory.ERROR_HANDLING

    def scan(self) -> ScannerResult:
        import time
        start_time = time.perf_counter()
        self.issues = []
        files_scanned = 0

        backend_dir = self.project_root / "backend"
        if backend_dir.exists():
            files_scanned += self._check_error_handling(backend_dir)

        end_time = time.perf_counter()
        return ScannerResult(
            scanner_name=self.name,
            category=self.category,
            issues=self.issues,
            files_scanned=files_scanned,
            scan_time_ms=(end_time - start_time) * 1000
        )

    def _check_error_handling(self, backend_dir: Path) -> int:
        files_scanned = 0
        app_dir = backend_dir / "app"
        if not app_dir.exists():
            return files_scanned

        for py_file in app_dir.rglob("*.py"):
            if "__pycache__" in str(py_file):
                continue
            files_scanned += 1
            content = self._read_file(py_file)
            if content:
                self._check_exception_handling(py_file, content)

        return files_scanned

    def _check_exception_handling(self, file_path: Path, content: str):
        tree = self._parse_ast(content)
        if not tree:
            return

        for node in ast.walk(tree):
            if isinstance(node, ast.Try):
                self._check_try_block(file_path, node)

    def _check_try_block(self, file_path: Path, node: ast.Try):
        for handler in node.handlers:
            if handler.type is None:
                self.issues.append(OptimizationIssue(
                    file_path=str(file_path),
                    scanner_name=self.name,
                    issue_type="bare_except",
                    description="使用裸异常捕获，可能隐藏错误",
                    severity=IssueSeverity.HIGH,
                    line_number=handler.lineno,
                    suggestion="捕获具体的异常类型"
                ))

            if handler.name and not any(isinstance(n, ast.Name) and n.id == handler.name for n in ast.walk(handler)):
                self.issues.append(OptimizationIssue(
                    file_path=str(file_path),
                    scanner_name=self.name,
                    issue_type="unused_exception",
                    description=f"异常变量 {handler.name} 未被使用",
                    severity=IssueSeverity.LOW,
                    line_number=handler.lineno,
                    suggestion="使用异常变量或使用 'except Exception as e'"
                ))

        if not node.finalbody and len(node.handlers) > 0:
            has_resource = any(isinstance(n, (ast.With, ast.Call)) for n in ast.walk(node))
            if has_resource:
                self.issues.append(OptimizationIssue(
                    file_path=str(file_path),
                    scanner_name=self.name,
                    issue_type="missing_finally",
                    description="涉及资源操作的 try 块缺少 finally 块",
                    severity=IssueSeverity.MEDIUM,
                    line_number=node.lineno,
                    suggestion="添加 finally 块确保资源正确释放"
                ))


class GUIScanner(BaseScanner):
    @property
    def name(self) -> str:
        return "GUI界面扫描器"

    @property
    def category(self) -> ScannerCategory:
        return ScannerCategory.GUI

    def scan(self) -> ScannerResult:
        import time
        start_time = time.perf_counter()
        self.issues = []
        files_scanned = 0

        frontend_dir = self.project_root / "frontend"
        if frontend_dir.exists():
            files_scanned += self._check_gui_components(frontend_dir)

        end_time = time.perf_counter()
        return ScannerResult(
            scanner_name=self.name,
            category=self.category,
            issues=self.issues,
            files_scanned=files_scanned,
            scan_time_ms=(end_time - start_time) * 1000
        )

    def _check_gui_components(self, frontend_dir: Path) -> int:
        files_scanned = 0
        src_dir = frontend_dir / "src"
        if not src_dir.exists():
            return files_scanned

        for vue_file in src_dir.rglob("*.vue"):
            if "__pycache__" in str(vue_file):
                continue
            files_scanned += 1
            content = self._read_file(vue_file)
            if content:
                self._check_vue_component(vue_file, content)

        return files_scanned

    def _check_vue_component(self, file_path: Path, content: str):
        if "<template>" in content:
            self._check_template_consistency(file_path, content)
        if "<style" in content:
            self._check_style_consistency(file_path, content)

    def _check_template_consistency(self, file_path: Path, content: str):
        template_match = re.search(r'<template>(.*?)</template>', content, re.DOTALL)
        if template_match:
            template = template_match.group(1)

            if "v-if" in template and "v-else" not in template:
                self.issues.append(OptimizationIssue(
                    file_path=str(file_path),
                    scanner_name=self.name,
                    issue_type="missing_else_branch",
                    description="v-if 缺少对应的 v-else 分支",
                    severity=IssueSeverity.LOW,
                    suggestion="考虑添加 v-else 处理其他情况"
                ))

            inline_styles = re.findall(r'style="[^"]*"', template)
            if len(inline_styles) > 3:
                self.issues.append(OptimizationIssue(
                    file_path=str(file_path),
                    scanner_name=self.name,
                    issue_type="excessive_inline_styles",
                    description=f"模板中包含 {len(inline_styles)} 个内联样式",
                    severity=IssueSeverity.MEDIUM,
                    suggestion="将样式移至 CSS 类中"
                ))

    def _check_style_consistency(self, file_path: Path, content: str):
        style_match = re.search(r'<style[^>]*>(.*?)</style>', content, re.DOTALL)
        if style_match:
            style = style_match.group(1)

            if "!important" in style:
                count = style.count("!important")
                self.issues.append(OptimizationIssue(
                    file_path=str(file_path),
                    scanner_name=self.name,
                    issue_type="important_usage",
                    description=f"使用了 {count} 次 !important",
                    severity=IssueSeverity.LOW,
                    suggestion="避免使用 !important，提高选择器优先级"
                ))


class UIUXScanner(BaseScanner):
    @property
    def name(self) -> str:
        return "UI/UX扫描器"

    @property
    def category(self) -> ScannerCategory:
        return ScannerCategory.UI_UX

    def scan(self) -> ScannerResult:
        import time
        start_time = time.perf_counter()
        self.issues = []
        files_scanned = 0

        frontend_dir = self.project_root / "frontend"
        if frontend_dir.exists():
            files_scanned += self._check_uiux_issues(frontend_dir)

        self._load_uiux_guidelines()

        end_time = time.perf_counter()
        return ScannerResult(
            scanner_name=self.name,
            category=self.category,
            issues=self.issues,
            files_scanned=files_scanned,
            scan_time_ms=(end_time - start_time) * 1000
        )

    def _load_uiux_guidelines(self):
        uiux_skill_path = self.project_root / ".trae" / "skills" / "ui-ux-pro-max"
        if uiux_skill_path.exists():
            self.logger.info("已集成 ui-ux-pro-max 技能")

    def _check_uiux_issues(self, frontend_dir: Path) -> int:
        files_scanned = 0
        src_dir = frontend_dir / "src"
        if not src_dir.exists():
            return files_scanned

        for vue_file in src_dir.rglob("*.vue"):
            if "__pycache__" in str(vue_file):
                continue
            files_scanned += 1
            content = self._read_file(vue_file)
            if content:
                self._check_accessibility(vue_file, content)
                self._check_responsive_design(vue_file, content)
                self._check_user_feedback(vue_file, content)

        return files_scanned

    def _check_accessibility(self, file_path: Path, content: str):
        if "<img" in content and 'alt=' not in content:
            self.issues.append(OptimizationIssue(
                file_path=str(file_path),
                scanner_name=self.name,
                issue_type="missing_alt_attribute",
                description="图片元素缺少 alt 属性",
                severity=IssueSeverity.HIGH,
                suggestion="为图片添加描述性 alt 属性"
            ))

        if "<button" in content and 'aria-label=' not in content:
            button_count = content.count("<button")
            labeled_count = content.count('aria-label=')
            if button_count > labeled_count:
                self.issues.append(OptimizationIssue(
                    file_path=str(file_path),
                    scanner_name=self.name,
                    issue_type="missing_aria_label",
                    description="部分按钮缺少 aria-label 属性",
                    severity=IssueSeverity.MEDIUM,
                    suggestion="为图标按钮添加 aria-label 提高可访问性"
                ))

        if "v-model" in content and '<label' not in content:
            self.issues.append(OptimizationIssue(
                file_path=str(file_path),
                scanner_name=self.name,
                issue_type="missing_form_label",
                description="表单输入缺少关联的 label",
                severity=IssueSeverity.MEDIUM,
                suggestion="为表单输入添加 label 元素"
            ))

    def _check_responsive_design(self, file_path: Path, content: str):
        style_match = re.search(r'<style[^>]*>(.*?)</style>', content, re.DOTALL)
        if style_match:
            style = style_match.group(1)

            if "@media" not in style and "px" in style:
                self.issues.append(OptimizationIssue(
                    file_path=str(file_path),
                    scanner_name=self.name,
                    issue_type="missing_media_queries",
                    description="样式缺少响应式媒体查询",
                    severity=IssueSeverity.MEDIUM,
                    suggestion="添加 @media 查询支持不同屏幕尺寸"
                ))

        if "fixed" in content and "width" in content:
            self.issues.append(OptimizationIssue(
                file_path=str(file_path),
                scanner_name=self.name,
                issue_type="fixed_width_layout",
                description="使用固定宽度布局，可能影响响应式",
                severity=IssueSeverity.LOW,
                suggestion="使用相对单位或弹性布局"
            ))

    def _check_user_feedback(self, file_path: Path, content: str):
        if "@click" in content or "v-on:click" in content:
            if ":loading" not in content and "loading" not in content:
                self.issues.append(OptimizationIssue(
                    file_path=str(file_path),
                    scanner_name=self.name,
                    issue_type="missing_loading_state",
                    description="点击操作缺少加载状态反馈",
                    severity=IssueSeverity.MEDIUM,
                    suggestion="添加加载状态提升用户体验"
                ))

        if "error" not in content.lower() and "catch" not in content.lower():
            if "async" in content or "await" in content:
                self.issues.append(OptimizationIssue(
                    file_path=str(file_path),
                    scanner_name=self.name,
                    issue_type="missing_error_feedback",
                    description="异步操作缺少错误反馈",
                    severity=IssueSeverity.MEDIUM,
                    suggestion="添加错误处理和用户提示"
                ))


class CPUOptimizationScanner(BaseScanner):
    @property
    def name(self) -> str:
        return "CPU优化扫描器"

    @property
    def category(self) -> ScannerCategory:
        return ScannerCategory.PERFORMANCE_CPU

    def scan(self) -> ScannerResult:
        import time
        start_time = time.perf_counter()
        self.issues = []
        files_scanned = 0

        backend_dir = self.path_manager.get_backend_path()
        if backend_dir.exists():
            files_scanned += self._scan_backend_cpu_issues(backend_dir)

        frontend_dir = self.path_manager.get_frontend_path()
        if frontend_dir.exists():
            files_scanned += self._scan_frontend_cpu_issues(frontend_dir)

        end_time = time.perf_counter()
        return ScannerResult(
            scanner_name=self.name,
            category=self.category,
            issues=self.issues,
            files_scanned=files_scanned,
            scan_time_ms=(end_time - start_time) * 1000
        )

    def _scan_backend_cpu_issues(self, backend_dir: Path) -> int:
        files_scanned = 0
        app_dir = backend_dir / "app"
        if not app_dir.exists():
            return files_scanned

        for py_file in app_dir.rglob("*.py"):
            if "__pycache__" in str(py_file):
                continue
            files_scanned += 1
            content = self._read_file(py_file)
            if not content:
                continue

            tree = self._parse_ast(content)
            if tree:
                self._check_cpu_intensive_patterns(py_file, content, tree)
                self._check_loop_optimizations(py_file, content, tree)
                self._check_algorithm_complexity(py_file, content, tree)

        return files_scanned

    def _check_cpu_intensive_patterns(self, file_path: Path, content: str, tree: ast.AST):
        patterns = [
            (r'for\s+\w+\s+in\s+range\(len\(', "使用 range(len()) 模式，建议使用 enumerate()"),
            (r'\.append\([^)]*\)\s*\n\s*for\s+', "循环内频繁 append，建议预分配列表或使用列表推导式"),
            (r'while\s+True\s*:', "无限循环可能消耗 CPU，建议添加退出条件"),
            (r'time\.sleep\([0-9]+\)', "固定时间 sleep 可能浪费 CPU，建议使用事件驱动"),
            (r're\.compile\([^)]+\)\s*\n', "重复编译正则表达式，建议预编译并缓存"),
        ]

        lines = content.split('\n')
        for i, line in enumerate(lines, 1):
            for pattern, message in patterns:
                if re.search(pattern, line):
                    self.issues.append(OptimizationIssue(
                        file_path=str(file_path),
                        scanner_name=self.name,
                        issue_type="cpu_intensive_pattern",
                        description=message,
                        severity=IssueSeverity.MEDIUM,
                        line_number=i,
                        code_snippet=line.strip()[:80],
                        suggestion="优化 CPU 使用效率"
                    ))

    def _check_loop_optimizations(self, file_path: Path, content: str, tree: ast.AST):
        for node in ast.walk(tree):
            if isinstance(node, ast.For):
                self._analyze_for_loop(file_path, node, content)
            elif isinstance(node, ast.While):
                self._analyze_while_loop(file_path, node, content)

    def _analyze_for_loop(self, file_path: Path, node: ast.For, content: str):
        nested_loops = sum(1 for n in ast.walk(node) if isinstance(n, (ast.For, ast.While)))
        if nested_loops > 2:
            self.issues.append(OptimizationIssue(
                file_path=str(file_path),
                scanner_name=self.name,
                issue_type="nested_loop",
                description=f"发现 {nested_loops} 层嵌套循环，可能导致 O(n^{nested_loops}) 复杂度",
                severity=IssueSeverity.HIGH,
                line_number=node.lineno,
                suggestion="考虑使用更高效的算法或数据结构"
            ))

        loop_body_size = len(list(ast.walk(node)))
        if loop_body_size > 50:
            self.issues.append(OptimizationIssue(
                file_path=str(file_path),
                scanner_name=self.name,
                issue_type="large_loop_body",
                description=f"循环体过大 ({loop_body_size} 个节点)，可能影响 CPU 缓存效率",
                severity=IssueSeverity.LOW,
                line_number=node.lineno,
                suggestion="考虑将循环体提取为独立函数"
            ))

    def _analyze_while_loop(self, file_path: Path, node: ast.While, content: str):
        has_break = any(isinstance(n, ast.Break) for n in ast.walk(node))
        has_condition_change = False

        for n in ast.walk(node):
            if isinstance(n, ast.Assign):
                for target in n.targets:
                    if isinstance(target, ast.Name):
                        if node.test and isinstance(node.test, ast.Compare):
                            for comparator in node.test.comparators:
                                if isinstance(comparator, ast.Name) and comparator.id == target.id:
                                    has_condition_change = True

        if not has_break and not has_condition_change:
            self.issues.append(OptimizationIssue(
                file_path=str(file_path),
                scanner_name=self.name,
                issue_type="potential_infinite_loop",
                description="while 循环可能无限执行，消耗 CPU",
                severity=IssueSeverity.HIGH,
                line_number=node.lineno,
                suggestion="确保循环有明确的退出条件"
            ))

    def _check_algorithm_complexity(self, file_path: Path, content: str, tree: ast.AST):
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Attribute):
                    if node.func.attr in ['sort', 'sorted']:
                        self._check_sort_usage(file_path, node, content)
                    elif node.func.attr in ['index', 'find']:
                        self._check_search_usage(file_path, node, content)

    def _check_sort_usage(self, file_path: Path, node: ast.Call, content: str):
        has_key = any(kw.arg == 'key' for kw in node.keywords)
        if not has_key:
            self.issues.append(OptimizationIssue(
                file_path=str(file_path),
                scanner_name=self.name,
                issue_type="sort_without_key",
                description="排序操作未使用 key 函数，可能影响性能",
                severity=IssueSeverity.LOW,
                line_number=node.lineno,
                suggestion="使用 key 参数优化排序性能"
            ))

    def _check_search_usage(self, file_path: Path, node: ast.Call, content: str):
        self.issues.append(OptimizationIssue(
            file_path=str(file_path),
            scanner_name=self.name,
            issue_type="linear_search",
            description="使用线性搜索 (index/find)，大数据集建议使用字典或集合",
            severity=IssueSeverity.INFO,
            line_number=node.lineno,
            suggestion="考虑使用 dict 或 set 实现 O(1) 查找"
        ))

    def _scan_frontend_cpu_issues(self, frontend_dir: Path) -> int:
        files_scanned = 0
        src_dir = frontend_dir / "src"
        if not src_dir.exists():
            return files_scanned

        for vue_file in src_dir.rglob("*.vue"):
            if "__pycache__" in str(vue_file):
                continue
            files_scanned += 1
            content = self._read_file(vue_file)
            if content:
                self._check_vue_cpu_issues(vue_file, content)

        for ts_file in src_dir.rglob("*.ts"):
            if "__pycache__" in str(ts_file):
                continue
            files_scanned += 1
            content = self._read_file(ts_file)
            if content:
                self._check_ts_cpu_issues(ts_file, content)

        return files_scanned

    def _check_vue_cpu_issues(self, file_path: Path, content: str):
        if content.count('v-for') > 5:
            self.issues.append(OptimizationIssue(
                file_path=str(file_path),
                scanner_name=self.name,
                issue_type="excessive_vfor",
                description=f"组件中包含 {content.count('v-for')} 个 v-for，可能影响渲染性能",
                severity=IssueSeverity.MEDIUM,
                suggestion="考虑使用虚拟滚动或分页加载"
            ))

        if 'watch:' in content and 'deep: true' in content:
            self.issues.append(OptimizationIssue(
                file_path=str(file_path),
                scanner_name=self.name,
                issue_type="deep_watch",
                description="使用深度 watch 可能消耗大量 CPU",
                severity=IssueSeverity.MEDIUM,
                suggestion="避免深度 watch，使用精确的属性监听"
            ))

    def _check_ts_cpu_issues(self, file_path: Path, content: str):
        if '.forEach(' in content and '.filter(' in content:
            self.issues.append(OptimizationIssue(
                file_path=str(file_path),
                scanner_name=self.name,
                issue_type="chained_array_methods",
                description="链式数组方法可能导致多次遍历",
                severity=IssueSeverity.LOW,
                suggestion="考虑合并操作或使用单次遍历"
            ))


class MemoryOptimizationScanner(BaseScanner):
    @property
    def name(self) -> str:
        return "内存优化扫描器"

    @property
    def category(self) -> ScannerCategory:
        return ScannerCategory.PERFORMANCE_MEMORY

    def scan(self) -> ScannerResult:
        import time
        start_time = time.perf_counter()
        self.issues = []
        files_scanned = 0

        backend_dir = self.path_manager.get_backend_path()
        if backend_dir.exists():
            files_scanned += self._scan_backend_memory_issues(backend_dir)

        end_time = time.perf_counter()
        return ScannerResult(
            scanner_name=self.name,
            category=self.category,
            issues=self.issues,
            files_scanned=files_scanned,
            scan_time_ms=(end_time - start_time) * 1000
        )

    def _scan_backend_memory_issues(self, backend_dir: Path) -> int:
        files_scanned = 0
        app_dir = backend_dir / "app"
        if not app_dir.exists():
            return files_scanned

        for py_file in app_dir.rglob("*.py"):
            if "__pycache__" in str(py_file):
                continue
            files_scanned += 1
            content = self._read_file(py_file)
            if not content:
                continue

            tree = self._parse_ast(content)
            if tree:
                self._check_memory_issues(py_file, content, tree)
                self._check_data_structure_efficiency(py_file, content, tree)
                self._check_resource_management(py_file, content, tree)

        return files_scanned

    def _check_memory_issues(self, file_path: Path, content: str, tree: ast.AST):
        patterns = [
            (r'=\s*\[\s*\]\s*\*\s*\d+', "列表乘法创建大列表，可能占用大量内存"),
            (r'=\s*\{\s*\}\s*\.\(fromkeys\)', "字典 fromkeys 可能创建大字典"),
            (r'open\([^)]+\)(?!\s+as)', "文件操作未使用 with 语句，可能导致资源泄漏"),
            (r'\.read\(\)(?!\s*in\s)', "一次性读取整个文件，大文件可能占用大量内存"),
            (r'pickle\.loads?\(', "pickle 操作可能导致内存问题"),
            (r'global\s+\w+\s*=', "全局变量可能导致内存无法释放"),
        ]

        lines = content.split('\n')
        for i, line in enumerate(lines, 1):
            for pattern, message in patterns:
                if re.search(pattern, line):
                    self.issues.append(OptimizationIssue(
                        file_path=str(file_path),
                        scanner_name=self.name,
                        issue_type="memory_pattern",
                        description=message,
                        severity=IssueSeverity.MEDIUM,
                        line_number=i,
                        code_snippet=line.strip()[:80],
                        suggestion="优化内存使用"
                    ))

    def _check_data_structure_efficiency(self, file_path: Path, content: str, tree: ast.AST):
        for node in ast.walk(tree):
            if isinstance(node, ast.ListComp):
                self._check_list_comprehension_memory(file_path, node, content)
            elif isinstance(node, ast.DictComp):
                self._check_dict_comprehension_memory(file_path, node, content)
            elif isinstance(node, ast.Call):
                self._check_collection_creation(file_path, node, content)

    def _check_list_comprehension_memory(self, file_path: Path, node: ast.ListComp, content: str):
        nested_generators = len(node.generators)
        if nested_generators > 2:
            self.issues.append(OptimizationIssue(
                file_path=str(file_path),
                scanner_name=self.name,
                issue_type="nested_comprehension",
                description=f"嵌套列表推导式 ({nestedGenerators} 层) 可能创建大型中间结果",
                severity=IssueSeverity.MEDIUM,
                line_number=node.lineno,
                suggestion="考虑使用生成器表达式或分步处理"
            ))

    def _check_dict_comprehension_memory(self, file_path: Path, node: ast.DictComp, content: str):
        self.issues.append(OptimizationIssue(
            file_path=str(file_path),
            scanner_name=self.name,
            issue_type="dict_comprehension",
            description="字典推导式可能创建大型字典，考虑惰性加载",
            severity=IssueSeverity.LOW,
            line_number=node.lineno,
            suggestion="大数据集考虑使用生成器或分批处理"
        ))

    def _check_collection_creation(self, file_path: Path, node: ast.Call, content: str):
        if isinstance(node.func, ast.Name):
            if node.func.id in ['list', 'dict', 'set']:
                if node.args and isinstance(node.args[0], ast.Call):
                    if isinstance(node.args[0].func, ast.Name):
                        if node.args[0].func.id in ['range']:
                            self.issues.append(OptimizationIssue(
                                file_path=str(file_path),
                                scanner_name=self.name,
                                issue_type="large_collection_creation",
                                description="创建大型集合可能占用大量内存",
                                severity=IssueSeverity.LOW,
                                line_number=node.lineno,
                                suggestion="考虑使用生成器或迭代器"
                            ))

    def _check_resource_management(self, file_path: Path, content: str, tree: ast.AST):
        for node in ast.walk(tree):
            if isinstance(node, ast.With):
                self._check_context_manager_usage(file_path, node)
            elif isinstance(node, ast.FunctionDef):
                self._check_function_memory_leak(file_path, node, content)

    def _check_context_manager_usage(self, file_path: Path, node: ast.With):
        resource_types = ['open', 'connect', 'cursor', 'lock']
        for item in node.items:
            if isinstance(item.context_expr, ast.Call):
                if isinstance(item.context_expr.func, ast.Name):
                    if item.context_expr.func.id in resource_types:
                        return

        if len(node.items) > 3:
            self.issues.append(OptimizationIssue(
                file_path=str(file_path),
                scanner_name=self.name,
                issue_type="multiple_context_managers",
                description="多个上下文管理器可能增加内存压力",
                severity=IssueSeverity.LOW,
                line_number=node.lineno,
                suggestion="考虑分批处理资源"
            ))

    def _check_function_memory_leak(self, file_path: Path, node: ast.FunctionDef, content: str):
        has_closure = any(isinstance(n, ast.FunctionDef) for n in ast.walk(node))
        has_mutable_default = False

        for default in node.args.defaults:
            if isinstance(default, (ast.List, ast.Dict, ast.Set)):
                has_mutable_default = True

        if has_closure and has_mutable_default:
            self.issues.append(OptimizationIssue(
                file_path=str(file_path),
                scanner_name=self.name,
                issue_type="closure_memory_leak",
                description=f"函数 {node.name} 闭包引用可变默认参数可能导致内存泄漏",
                severity=IssueSeverity.HIGH,
                line_number=node.lineno,
                suggestion="避免在闭包中引用可变默认参数"
            ))


class IOOptimizationScanner(BaseScanner):
    @property
    def name(self) -> str:
        return "I/O优化扫描器"

    @property
    def category(self) -> ScannerCategory:
        return ScannerCategory.PERFORMANCE_IO

    def scan(self) -> ScannerResult:
        import time
        start_time = time.perf_counter()
        self.issues = []
        files_scanned = 0

        backend_dir = self.path_manager.get_backend_path()
        if backend_dir.exists():
            files_scanned += self._scan_backend_io_issues(backend_dir)

        end_time = time.perf_counter()
        return ScannerResult(
            scanner_name=self.name,
            category=self.category,
            issues=self.issues,
            files_scanned=files_scanned,
            scan_time_ms=(end_time - start_time) * 1000
        )

    def _scan_backend_io_issues(self, backend_dir: Path) -> int:
        files_scanned = 0
        app_dir = backend_dir / "app"
        if not app_dir.exists():
            return files_scanned

        for py_file in app_dir.rglob("*.py"):
            if "__pycache__" in str(py_file):
                continue
            files_scanned += 1
            content = self._read_file(py_file)
            if not content:
                continue

            tree = self._parse_ast(content)
            if tree:
                self._check_file_io_issues(py_file, content, tree)
                self._check_database_io_issues(py_file, content, tree)
                self._check_async_io_issues(py_file, content, tree)

        return files_scanned

    def _check_file_io_issues(self, file_path: Path, content: str, tree: ast.AST):
        patterns = [
            (r'open\([^)]+["\']r["\']\)', "文件读取操作，建议使用缓冲或异步 I/O"),
            (r'open\([^)]+["\']w["\']\)', "文件写入操作，建议使用缓冲写入"),
            (r'\.readlines\(\)', "readlines() 一次性读取所有行，大文件建议逐行读取"),
            (r'os\.path\.exists', "频繁文件存在检查可能影响性能，建议缓存结果"),
            (r'shutil\.copy', "文件复制操作，大文件建议使用流式复制"),
        ]

        lines = content.split('\n')
        for i, line in enumerate(lines, 1):
            for pattern, message in patterns:
                if re.search(pattern, line):
                    self.issues.append(OptimizationIssue(
                        file_path=str(file_path),
                        scanner_name=self.name,
                        issue_type="file_io_pattern",
                        description=message,
                        severity=IssueSeverity.MEDIUM,
                        line_number=i,
                        code_snippet=line.strip()[:80],
                        suggestion="优化文件 I/O 性能"
                    ))

        io_operations = content.count('open(') + content.count('.read(') + content.count('.write(')
        if io_operations > 5:
            self.issues.append(OptimizationIssue(
                file_path=str(file_path),
                scanner_name=self.name,
                issue_type="excessive_io",
                description=f"文件中包含 {io_operations} 个 I/O 操作，建议批量处理",
                severity=IssueSeverity.MEDIUM,
                suggestion="考虑合并 I/O 操作或使用异步 I/O"
            ))

    def _check_database_io_issues(self, file_path: Path, content: str, tree: ast.AST):
        db_patterns = [
            (r'\.execute\([^)]+\)', "数据库查询操作"),
            (r'\.fetchall\(\)', "fetchall() 可能返回大量数据，建议使用 fetchmany 或流式处理"),
            (r'\.commit\(\)', "频繁提交事务可能影响性能，建议批量提交"),
            (r'for\s+\w+\s+in\s+\w+\.query\(', "循环内数据库查询可能导致 N+1 问题"),
        ]

        lines = content.split('\n')
        for i, line in enumerate(lines, 1):
            for pattern, message in db_patterns:
                if re.search(pattern, line):
                    self.issues.append(OptimizationIssue(
                        file_path=str(file_path),
                        scanner_name=self.name,
                        issue_type="database_io",
                        description=message,
                        severity=IssueSeverity.MEDIUM,
                        line_number=i,
                        code_snippet=line.strip()[:80],
                        suggestion="优化数据库 I/O 性能"
                    ))

        for node in ast.walk(tree):
            if isinstance(node, ast.For):
                self._check_loop_db_query(file_path, node, content)

    def _check_loop_db_query(self, file_path: Path, node: ast.For, content: str):
        db_operations = ['.execute', '.query', '.filter', '.get']
        for child in ast.walk(node):
            if isinstance(child, ast.Call):
                if isinstance(child.func, ast.Attribute):
                    if any(op in child.func.attr for op in db_operations):
                        self.issues.append(OptimizationIssue(
                            file_path=str(file_path),
                            scanner_name=self.name,
                            issue_type="n_plus_one_query",
                            description="循环内执行数据库查询，可能导致 N+1 问题",
                            severity=IssueSeverity.HIGH,
                            line_number=node.lineno,
                            suggestion="使用批量查询或预加载关联数据"
                        ))
                        return

    def _check_async_io_issues(self, file_path: Path, content: str, tree: ast.AST):
        if 'async def' in content or 'await' in content:
            if 'asyncio.sleep' in content:
                self.issues.append(OptimizationIssue(
                    file_path=str(file_path),
                    scanner_name=self.name,
                    issue_type="async_sleep",
                    description="asyncio.sleep 可能阻塞事件循环",
                    severity=IssueSeverity.LOW,
                    suggestion="考虑使用异步定时器或事件驱动"
                ))

            if content.count('await') > 5 and 'asyncio.gather' not in content:
                self.issues.append(OptimizationIssue(
                    file_path=str(file_path),
                    scanner_name=self.name,
                    issue_type="sequential_await",
                    description="多个顺序 await 可能影响性能，建议并行执行",
                    severity=IssueSeverity.MEDIUM,
                    suggestion="使用 asyncio.gather 并行执行多个异步操作"
                ))


class NetworkOptimizationScanner(BaseScanner):
    @property
    def name(self) -> str:
        return "网络优化扫描器"

    @property
    def category(self) -> ScannerCategory:
        return ScannerCategory.PERFORMANCE_NETWORK

    def scan(self) -> ScannerResult:
        import time
        from skillscripts.core.path_config_center import get_path_config
        start_time = time.perf_counter()
        self.issues = []
        files_scanned = 0

        backend_dir = self.path_manager.get_backend_path()
        if backend_dir.exists():
            files_scanned += self._scan_backend_network_issues(backend_dir)

        frontend_dir = self.path_manager.get_frontend_path()
        if frontend_dir.exists():
            files_scanned += self._scan_frontend_network_issues(frontend_dir)

        end_time = time.perf_counter()
        return ScannerResult(
            scanner_name=self.name,
            category=self.category,
            issues=self.issues,
            files_scanned=files_scanned,
            scan_time_ms=(end_time - start_time) * 1000
        )

    def _scan_backend_network_issues(self, backend_dir: Path) -> int:
        files_scanned = 0
        app_dir = backend_dir / "app"
        if not app_dir.exists():
            return files_scanned

        for py_file in app_dir.rglob("*.py"):
            if "__pycache__" in str(py_file):
                continue
            files_scanned += 1
            content = self._read_file(py_file)
            if not content:
                continue

            tree = self._parse_ast(content)
            if tree:
                self._check_http_client_issues(py_file, content, tree)
                self._check_api_performance_issues(py_file, content, tree)
                self._check_websocket_issues(py_file, content, tree)

        return files_scanned

    def _check_http_client_issues(self, file_path: Path, content: str, tree: ast.AST):
        patterns = [
            (r'requests\.get\(', "同步 HTTP 请求可能阻塞，建议使用异步客户端"),
            (r'requests\.post\(', "同步 HTTP POST 请求，建议使用异步客户端"),
            (r'httpx\.Client\(\)', "httpx 同步客户端，建议使用 AsyncClient"),
            (r'timeout\s*=\s*None', "HTTP 请求无超时设置，可能导致长时间阻塞"),
            (r'verify\s*=\s*False', "禁用 SSL 验证存在安全风险"),
        ]

        lines = content.split('\n')
        for i, line in enumerate(lines, 1):
            for pattern, message in patterns:
                if re.search(pattern, line):
                    self.issues.append(OptimizationIssue(
                        file_path=str(file_path),
                        scanner_name=self.name,
                        issue_type="http_client_pattern",
                        description=message,
                        severity=IssueSeverity.MEDIUM,
                        line_number=i,
                        code_snippet=line.strip()[:80],
                        suggestion="优化 HTTP 客户端性能"
                    ))

        if content.count('requests.') > 3 and 'Session' not in content:
            self.issues.append(OptimizationIssue(
                file_path=str(file_path),
                scanner_name=self.name,
                issue_type="no_session_reuse",
                description="多次 HTTP 请求未使用 Session，建议复用连接",
                severity=IssueSeverity.MEDIUM,
                suggestion="使用 requests.Session 或 httpx.AsyncClient 复用连接"
            ))

    def _check_api_performance_issues(self, file_path: Path, content: str, tree: ast.AST):
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                decorators = [d for d in node.decorator_list if isinstance(d, ast.Call)]
                for dec in decorators:
                    if isinstance(dec.func, ast.Attribute):
                        if dec.func.attr in ['get', 'post', 'put', 'delete', 'patch']:
                            self._check_api_endpoint_performance(file_path, node, content)

    def _check_api_endpoint_performance(self, file_path: Path, node: ast.FunctionDef, content: str):
        func_content = ast.get_source_segment(content, node) or ""

        if func_content.count('await') > 5:
            self.issues.append(OptimizationIssue(
                file_path=str(file_path),
                scanner_name=self.name,
                issue_type="slow_api_endpoint",
                description=f"API 端点 {node.name} 包含多个异步操作，可能响应缓慢",
                severity=IssueSeverity.MEDIUM,
                line_number=node.lineno,
                suggestion="考虑并行执行或添加缓存"
            ))

        if 'json.loads' in func_content or 'json.dumps' in func_content:
            if func_content.count('json.loads') + func_content.count('json.dumps') > 3:
                self.issues.append(OptimizationIssue(
                    file_path=str(file_path),
                    scanner_name=self.name,
                    issue_type="excessive_json_serialization",
                    description=f"API 端点 {node.name} 包含多次 JSON 序列化",
                    severity=IssueSeverity.LOW,
                    line_number=node.lineno,
                    suggestion="减少不必要的 JSON 序列化操作"
                ))

    def _check_websocket_issues(self, file_path: Path, content: str, tree: ast.AST):
        if 'WebSocket' in content or 'websocket' in content:
            if 'ping_interval' not in content and 'ping_timeout' not in content:
                self.issues.append(OptimizationIssue(
                    file_path=str(file_path),
                    scanner_name=self.name,
                    issue_type="websocket_no_ping",
                    description="WebSocket 连接未配置 ping 机制，可能导致连接断开",
                    severity=IssueSeverity.MEDIUM,
                    suggestion="配置 ping_interval 和 ping_timeout 保持连接"
                ))

            if 'max_size' not in content:
                self.issues.append(OptimizationIssue(
                    file_path=str(file_path),
                    scanner_name=self.name,
                    issue_type="websocket_no_max_size",
                    description="WebSocket 未设置消息大小限制，可能导致内存问题",
                    severity=IssueSeverity.LOW,
                    suggestion="设置 max_size 限制消息大小"
                ))

    def _scan_frontend_network_issues(self, frontend_dir: Path) -> int:
        files_scanned = 0
        src_dir = frontend_dir / "src"
        if not src_dir.exists():
            return files_scanned

        for ts_file in src_dir.rglob("*.ts"):
            if "__pycache__" in str(ts_file):
                continue
            files_scanned += 1
            content = self._read_file(ts_file)
            if content:
                self._check_frontend_network_patterns(ts_file, content)

        for vue_file in src_dir.rglob("*.vue"):
            if "__pycache__" in str(vue_file):
                continue
            files_scanned += 1
            content = self._read_file(vue_file)
            if content:
                self._check_vue_network_patterns(vue_file, content)

        return files_scanned

    def _check_frontend_network_patterns(self, file_path: Path, content: str):
        patterns = [
            (r'fetch\([^)]+\)', "fetch 请求，建议添加超时和错误处理"),
            (r'axios\.[get|post|put|delete]+', "axios 请求，建议配置拦截器和超时"),
            (r'XMLHttpRequest', "使用 XMLHttpRequest，建议使用 fetch 或 axios"),
        ]

        lines = content.split('\n')
        for i, line in enumerate(lines, 1):
            for pattern, message in patterns:
                if re.search(pattern, line):
                    self.issues.append(OptimizationIssue(
                        file_path=str(file_path),
                        scanner_name=self.name,
                        issue_type="frontend_network_pattern",
                        description=message,
                        severity=IssueSeverity.LOW,
                        line_number=i,
                        code_snippet=line.strip()[:80],
                        suggestion="优化前端网络请求"
                    ))

        if content.count('fetch(') > 3 and 'Promise.all' not in content:
            self.issues.append(OptimizationIssue(
                file_path=str(file_path),
                scanner_name=self.name,
                issue_type="sequential_fetch",
                description="多个顺序 fetch 请求，建议并行执行",
                severity=IssueSeverity.MEDIUM,
                suggestion="使用 Promise.all 并行执行多个请求"
            ))

    def _check_vue_network_patterns(self, file_path: Path, content: str):
        if 'mounted()' in content or 'onMounted' in content:
            if 'fetch' in content or 'axios' in content:
                if 'loading' not in content.lower():
                    self.issues.append(OptimizationIssue(
                        file_path=str(file_path),
                        scanner_name=self.name,
                        issue_type="no_loading_state",
                        description="组件挂载时发起请求但未显示加载状态",
                        severity=IssueSeverity.LOW,
                        suggestion="添加加载状态提升用户体验"
                    ))


class SystematicOptimizer:
    SCANNERS = {
        "architecture": ArchitectureScanner,
        "requirement": RequirementScanner,
        "design": DesignScanner,
        "principle": PrincipleScanner,
        "logic": LogicChainScanner,
        "code_review": CodeReviewScanner,
        "code_quality_enhanced": CodeQualityEnhancedScanner,
        "frontend_backend": FrontendBackendScanner,
        "business": BusinessChainScanner,
        "data": DataScanner,
        "logging": LoggingScanner,
        "error_handling": ErrorHandlingScanner,
        "gui": GUIScanner,
        "ui_ux": UIUXScanner,
        "performance_cpu": CPUOptimizationScanner,
        "performance_memory": MemoryOptimizationScanner,
        "performance_io": IOOptimizationScanner,
        "performance_network": NetworkOptimizationScanner
    }

    def __init__(self, project_root: Optional[Path] = None,
                 logger: Optional[logging.Logger] = None):
        self.project_root = project_root or get_path_config().SKILL_ROOT
        self.logger = logger or logging.getLogger(__name__)
        self.results: List[ScannerResult] = []

    def run_all_scanners(self, scanner_names: Optional[List[str]] = None) -> OptimizationReport:
        self.logger.info("开始系统性优化扫描...")
        self.results = []

        scanners_to_run = scanner_names if scanner_names else list(self.SCANNERS.keys())

        for scanner_name in scanners_to_run:
            if scanner_name not in self.SCANNERS:
                self.logger.warning(f"未知的扫描器: {scanner_name}")
                continue

            self.logger.info(f"运行扫描器: {scanner_name}")
            scanner = self.SCANNERS[scanner_name](self.project_root, self.logger)
            result = scanner.scan()
            self.results.append(result)

            if result.issues:
                self.logger.info(f"  发现 {len(result.issues)} 个问题")

        total_issues = sum(len(r.issues) for r in self.results)
        issues_by_severity: Dict[str, int] = {}
        issues_by_category: Dict[str, int] = {}

        for result in self.results:
            for issue in result.issues:
                sev = issue.severity.value
                issues_by_severity[sev] = issues_by_severity.get(sev, 0) + 1

                cat = issue.category.value
                issues_by_category[cat] = issues_by_category.get(cat, 0) + 1

        summary = {
            "total_scanners_run": len(self.results),
            "total_issues": total_issues,
            "issues_by_severity": issues_by_severity,
            "issues_by_category": issues_by_category,
            "critical_issues": issues_by_severity.get("critical", 0),
            "high_issues": issues_by_severity.get("high", 0),
            "medium_issues": issues_by_severity.get("medium", 0),
            "low_issues": issues_by_severity.get("low", 0),
            "info_issues": issues_by_severity.get("info", 0)
        }

        return OptimizationReport(
            timestamp=datetime.now().isoformat(),
            project_root=str(self.project_root),
            total_scanners=len(self.results),
            total_issues=total_issues,
            results=self.results,
            summary=summary
        )

    def print_report(self, report: OptimizationReport):
        print("\n" + "=" * 80)
        print("系统性优化扫描报告")
        print("=" * 80)
        print(f"项目根目录: {report.project_root}")
        print(f"扫描时间: {report.timestamp}")
        print(f"运行扫描器数: {report.total_scanners}")
        print(f"发现问题总数: {report.total_issues}")

        print("\n" + "-" * 80)
        print("摘要")
        print("-" * 80)
        print(f"  严重问题: {report.summary.get('critical_issues', 0)}")
        print(f"  高危问题: {report.summary.get('high_issues', 0)}")
        print(f"  中等问题: {report.summary.get('medium_issues', 0)}")
        print(f"  低危问题: {report.summary.get('low_issues', 0)}")
        print(f"  信息提示: {report.summary.get('info_issues', 0)}")

        print("\n按类别统计:")
        for cat, count in report.summary.get("issues_by_category", {}).items():
            print(f"  {cat}: {count}")

        severity_order = {
            IssueSeverity.CRITICAL: 0,
            IssueSeverity.HIGH: 1,
            IssueSeverity.MEDIUM: 2,
            IssueSeverity.LOW: 3,
            IssueSeverity.INFO: 4
        }

        all_issues = []
        for result in report.results:
            for issue in result.issues:
                all_issues.append(issue)

        all_issues.sort(key=lambda x: severity_order.get(x.severity, 99))

        if all_issues:
            print("\n" + "-" * 80)
            print("发现的问题")
            print("-" * 80)

            for issue in all_issues[:100]:
                severity_icon = {
                    IssueSeverity.CRITICAL: "🔴",
                    IssueSeverity.HIGH: "🟠",
                    IssueSeverity.MEDIUM: "🟡",
                    IssueSeverity.LOW: "🔵",
                    IssueSeverity.INFO: "⚪"
                }.get(issue.severity, "⚪")

                print(f"\n{severity_icon} [{issue.severity.value.upper()}] {issue.issue_type}")
                print(f"   扫描器: {issue.scanner_name}")
                print(f"   文件: {issue.file_path}")
                if issue.line_number:
                    print(f"   行号: {issue.line_number}")
                print(f"   描述: {issue.description}")
                if issue.suggestion:
                    print(f"   建议: {issue.suggestion}")

            if len(all_issues) > 100:
                print(f"\n... 还有 {len(all_issues) - 100} 个问题未显示")

    def save_report(self, report: OptimizationReport, output_dir: Optional[Path] = None) -> Path:
        if output_dir is None:
            output_dir = get_path_config().REPORTS_DIR
        output_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_path = output_dir / f"systematic_optimization_{timestamp}.json"

        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report.to_dict(), f, indent=2, ensure_ascii=False)

        latest_path = output_dir / "systematic_optimization_latest.json"
        with open(latest_path, 'w', encoding='utf-8') as f:
            json.dump(report.to_dict(), f, indent=2, ensure_ascii=False)

        self.logger.info(f"报告已保存: {report_path}")
        return report_path


def setup_logger(verbose: bool = False) -> logging.Logger:
    logger = logging.getLogger("SystematicOptimizer")
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
    parser = argparse.ArgumentParser(
        description="系统性优化扫描器",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
可用的扫描器:
  architecture      - 架构优化扫描器
  requirement       - 需求优化扫描器
  design           - 设计优化扫描器
  principle        - 原则规范扫描器
  logic            - 逻辑链扫描器
  code_review      - 代码审查扫描器
  frontend_backend - 前后端模块扫描器
  business         - 业务链扫描器
  data             - 数据扫描器
  logging          - 日志扫描器
  error_handling   - 错误处理扫描器
  gui              - GUI界面扫描器
  ui_ux            - UI/UX扫描器

示例:
  python systematic_optimizer.py
  python systematic_optimizer.py --scanners architecture,code_review
  python systematic_optimizer.py --output json --output-file result.json
  python systematic_optimizer.py --verbose
        """
    )

    parser.add_argument(
        "--scanners",
        type=str,
        help="指定要运行的扫描器，用逗号分隔"
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

    args = parser.parse_args()

    logger = setup_logger(args.verbose)

    scanner_names = None
    if args.scanners:
        scanner_names = [s.strip() for s in args.scanners.split(",")]

    optimizer = SystematicOptimizer(logger=logger)
    report = optimizer.run_all_scanners(scanner_names)

    optimizer.print_report(report)

    report_path = optimizer.save_report(report)
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

    return 0 if report.total_issues == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
