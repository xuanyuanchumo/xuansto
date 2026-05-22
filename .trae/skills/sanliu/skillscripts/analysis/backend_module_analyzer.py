#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
后端模块分析器 - Sanliu 技能

提供全面的后端模块分析功能，包括：
- 目录结构和模块作用分析
- 冗余和相似脚本识别
- 服务依赖关系分析
- 后端优化建议报告生成

使用示例:
    python backend_module_analyzer.py --backend ./backend
    python backend_module_analyzer.py --backend ./backend --output html
"""

import ast
import json
import logging
import re
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from difflib import SequenceMatcher
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple


class ModuleType(Enum):
    """模块类型枚举"""
    API = "api"
    MODEL = "model"
    SERVICE = "service"
    ROUTER = "router"
    MIDDLEWARE = "middleware"
    CONFIG = "config"
    UTILITY = "utility"
    TEST = "test"
    SCRIPT = "script"
    UNKNOWN = "unknown"


class IssueSeverity(Enum):
    """问题严重程度"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class SimilarityType(Enum):
    """相似类型"""
    DUPLICATE = "duplicate"
    SIMILAR = "similar"
    RELATED = "related"


@dataclass
class ImportInfo:
    """导入信息"""
    module: str
    name: str
    alias: Optional[str] = None
    is_relative: bool = False
    source_file: str = ""
    line_number: int = 0


@dataclass
class FunctionInfo:
    """函数信息"""
    name: str
    args: List[str]
    return_type: Optional[str]
    docstring: Optional[str]
    line_number: int
    end_line: int
    complexity: int = 1
    is_async: bool = False
    decorators: List[str] = field(default_factory=list)
    source_file: str = ""


@dataclass
class ClassInfo:
    """类信息"""
    name: str
    bases: List[str]
    docstring: Optional[str]
    line_number: int
    methods: List[FunctionInfo] = field(default_factory=list)
    attributes: List[str] = field(default_factory=list)
    source_file: str = ""


@dataclass
class ModuleInfo:
    """模块信息"""
    path: str
    name: str
    module_type: ModuleType
    description: str = ""
    imports: List[ImportInfo] = field(default_factory=list)
    exports: List[str] = field(default_factory=list)
    functions: List[FunctionInfo] = field(default_factory=list)
    classes: List[ClassInfo] = field(default_factory=list)
    dependencies: Set[str] = field(default_factory=set)
    dependents: Set[str] = field(default_factory=set)
    lines_of_code: int = 0
    file_size_bytes: int = 0


@dataclass
class SimilarityResult:
    """相似性检测结果"""
    file1: str
    file2: str
    similarity_type: SimilarityType
    similarity_score: float
    similar_parts: List[Dict[str, Any]] = field(default_factory=list)
    recommendation: str = ""


@dataclass
class DependencyEdge:
    """依赖边"""
    source: str
    target: str
    dependency_type: str
    strength: int = 1


@dataclass
class OptimizationIssue:
    """优化问题"""
    issue_type: str
    severity: IssueSeverity
    location: str
    description: str
    recommendation: str
    impact: str = ""


@dataclass
class BackendAnalysisReport:
    """后端分析报告"""
    timestamp: str
    backend_path: str
    total_modules: int
    total_lines_of_code: int
    modules: List[ModuleInfo] = field(default_factory=list)
    similarities: List[SimilarityResult] = field(default_factory=list)
    dependencies: List[DependencyEdge] = field(default_factory=list)
    issues: List[OptimizationIssue] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    statistics: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp,
            "backend_path": self.backend_path,
            "total_modules": self.total_modules,
            "total_lines_of_code": self.total_lines_of_code,
            "modules": [
                {
                    "path": m.path,
                    "name": m.name,
                    "module_type": m.module_type.value,
                    "description": m.description,
                    "lines_of_code": m.lines_of_code,
                    "dependencies": list(m.dependencies),
                    "dependents": list(m.dependents),
                    "function_count": len(m.functions),
                    "class_count": len(m.classes)
                }
                for m in self.modules
            ],
            "similarities": [
                {
                    "file1": s.file1,
                    "file2": s.file2,
                    "similarity_type": s.similarity_type.value,
                    "similarity_score": s.similarity_score,
                    "recommendation": s.recommendation
                }
                for s in self.similarities
            ],
            "dependencies": [
                {
                    "source": d.source,
                    "target": d.target,
                    "dependency_type": d.dependency_type,
                    "strength": d.strength
                }
                for d in self.dependencies
            ],
            "issues": [
                {
                    "issue_type": i.issue_type,
                    "severity": i.severity.value,
                    "location": i.location,
                    "description": i.description,
                    "recommendation": i.recommendation,
                    "impact": i.impact
                }
                for i in self.issues
            ],
            "recommendations": self.recommendations,
            "statistics": self.statistics
        }


class BackendModuleAnalyzer:
    """后端模块分析器"""
    
    MODULE_TYPE_PATTERNS = {
        ModuleType.API: [r'/api/', r'api\.py$', r'_api\.py$'],
        ModuleType.MODEL: [r'/models/', r'model\.py$', r'_model\.py$', r'models\.py$'],
        ModuleType.SERVICE: [r'/services/', r'service\.py$', r'_service\.py$'],
        ModuleType.ROUTER: [r'/routers/', r'router\.py$', r'_router\.py$'],
        ModuleType.MIDDLEWARE: [r'/middleware/', r'middleware\.py$'],
        ModuleType.CONFIG: [r'config\.py$', r'settings\.py$', r'/config/'],
        ModuleType.UTILITY: [r'/utils/', r'/helpers/', r'util\.py$', r'helper\.py$'],
        ModuleType.TEST: [r'/tests/', r'test_.*\.py$', r'.*_test\.py$'],
        ModuleType.SCRIPT: [r'/scripts/', r'script\.py$'],
    }
    
    SIMILARITY_THRESHOLDS = {
        SimilarityType.DUPLICATE: 0.95,
        SimilarityType.SIMILAR: 0.75,
        SimilarityType.RELATED: 0.50
    }
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        self.logger = logger or self._setup_logger()
        self.modules: Dict[str, ModuleInfo] = {}
        self.import_graph: Dict[str, Set[str]] = defaultdict(set)
        
    def _setup_logger(self) -> logging.Logger:
        logger = logging.getLogger("BackendModuleAnalyzer")
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
    
    def analyze(self, backend_path: Path) -> BackendAnalysisReport:
        """执行后端模块分析"""
        self.logger.info(f"开始分析后端目录: {backend_path}")
        
        self.modules = {}
        self.import_graph = defaultdict(set)
        
        py_files = list(backend_path.rglob("*.py"))
        
        for py_file in py_files:
            if self._should_skip_file(py_file):
                continue
            self._analyze_file(py_file, backend_path)
        
        self._build_dependency_graph()
        
        similarities = self._detect_similarities()
        
        dependencies = self._analyze_dependencies()
        
        issues = self._identify_issues()
        
        recommendations = self._generate_recommendations(similarities, issues)
        
        statistics = self._calculate_statistics()
        
        total_loc = sum(m.lines_of_code for m in self.modules.values())
        
        report = BackendAnalysisReport(
            timestamp=datetime.now().isoformat(),
            backend_path=str(backend_path),
            total_modules=len(self.modules),
            total_lines_of_code=total_loc,
            modules=list(self.modules.values()),
            similarities=similarities,
            dependencies=dependencies,
            issues=issues,
            recommendations=recommendations,
            statistics=statistics
        )
        
        self.logger.info(f"后端分析完成: {len(self.modules)} 个模块, {total_loc} 行代码")
        
        return report
    
    def _should_skip_file(self, file_path: Path) -> bool:
        """判断是否应该跳过文件"""
        skip_patterns = [
            '__pycache__', '.pytest_cache', 'htmlcov', '.git',
            'node_modules', 'venv', 'env', '.venv'
        ]
        return any(pattern in str(file_path) for pattern in skip_patterns)
    
    def _analyze_file(self, file_path: Path, backend_path: Path) -> None:
        """分析单个Python文件"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                source = f.read()
            
            rel_path = str(file_path.relative_to(backend_path))
            module_name = file_path.stem
            
            module_type = self._determine_module_type(rel_path)
            
            tree = ast.parse(source)
            
            imports = self._extract_imports(tree, rel_path)
            
            functions = self._extract_functions(tree, rel_path)
            
            classes = self._extract_classes(tree, rel_path)
            
            docstring = ast.get_docstring(tree)
            
            lines_of_code = len(source.splitlines())
            file_size = file_path.stat().st_size
            
            module_info = ModuleInfo(
                path=rel_path,
                name=module_name,
                module_type=module_type,
                description=docstring or "",
                imports=imports,
                functions=functions,
                classes=classes,
                lines_of_code=lines_of_code,
                file_size_bytes=file_size
            )
            
            self.modules[rel_path] = module_info
            
            for imp in imports:
                if imp.module and not imp.is_relative:
                    self.import_graph[rel_path].add(imp.module)
            
        except Exception as e:
            self.logger.warning(f"分析文件失败 {file_path}: {e}")
    
    def _determine_module_type(self, path: str) -> ModuleType:
        """确定模块类型"""
        path_lower = path.lower()
        
        for module_type, patterns in self.MODULE_TYPE_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, path_lower):
                    return module_type
        
        return ModuleType.UNKNOWN
    
    def _extract_imports(self, tree: ast.AST, source_file: str) -> List[ImportInfo]:
        """提取导入信息"""
        imports = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(ImportInfo(
                        module=alias.name,
                        name=alias.name,
                        alias=alias.asname,
                        is_relative=False,
                        source_file=source_file,
                        line_number=node.lineno
                    ))
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ""
                is_relative = node.level > 0
                for alias in node.names:
                    imports.append(ImportInfo(
                        module=module,
                        name=alias.name,
                        alias=alias.asname,
                        is_relative=is_relative,
                        source_file=source_file,
                        line_number=node.lineno
                    ))
        
        return imports
    
    def _extract_functions(self, tree: ast.AST, source_file: str) -> List[FunctionInfo]:
        """提取函数信息"""
        functions = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) or isinstance(node, ast.AsyncFunctionDef):
                args = [arg.arg for arg in node.args.args]
                
                return_type = None
                if node.returns:
                    return_type = ast.unparse(node.returns) if hasattr(ast, 'unparse') else str(node.returns)
                
                decorators = []
                for dec in node.decorator_list:
                    if isinstance(dec, ast.Name):
                        decorators.append(dec.id)
                    elif isinstance(dec, ast.Attribute):
                        decorators.append(dec.attr)
                
                complexity = self._calculate_complexity(node)
                
                func_info = FunctionInfo(
                    name=node.name,
                    args=args,
                    return_type=return_type,
                    docstring=ast.get_docstring(node),
                    line_number=node.lineno,
                    end_line=node.end_lineno or node.lineno,
                    complexity=complexity,
                    is_async=isinstance(node, ast.AsyncFunctionDef),
                    decorators=decorators,
                    source_file=source_file
                )
                functions.append(func_info)
        
        return functions
    
    def _extract_classes(self, tree: ast.AST, source_file: str) -> List[ClassInfo]:
        """提取类信息"""
        classes = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                bases = []
                for base in node.bases:
                    if isinstance(base, ast.Name):
                        bases.append(base.id)
                    elif isinstance(base, ast.Attribute):
                        bases.append(base.attr)
                
                methods = []
                attributes = []
                
                for item in node.body:
                    if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        method_info = FunctionInfo(
                            name=item.name,
                            args=[arg.arg for arg in item.args.args],
                            return_type=None,
                            docstring=ast.get_docstring(item),
                            line_number=item.lineno,
                            end_line=item.end_lineno or item.lineno,
                            is_async=isinstance(item, ast.AsyncFunctionDef)
                        )
                        methods.append(method_info)
                    elif isinstance(item, ast.Assign):
                        for target in item.targets:
                            if isinstance(target, ast.Name):
                                attributes.append(target.id)
                
                class_info = ClassInfo(
                    name=node.name,
                    bases=bases,
                    docstring=ast.get_docstring(node),
                    line_number=node.lineno,
                    methods=methods,
                    attributes=attributes,
                    source_file=source_file
                )
                classes.append(class_info)
        
        return classes
    
    def _calculate_complexity(self, node: ast.FunctionDef) -> int:
        """计算圈复杂度"""
        complexity = 1
        
        for child in ast.walk(node):
            if isinstance(child, (ast.If, ast.While, ast.For, ast.ExceptHandler)):
                complexity += 1
            elif isinstance(child, ast.BoolOp):
                complexity += len(child.values) - 1
            elif isinstance(child, ast.comprehension):
                complexity += 1
                if child.ifs:
                    complexity += len(child.ifs)
        
        return complexity
    
    def _build_dependency_graph(self) -> None:
        """构建依赖图"""
        for module_path, module_info in self.modules.items():
            for imp in module_info.imports:
                if imp.is_relative:
                    continue
                
                for other_path in self.modules:
                    if other_path != module_path:
                        other_module = self.modules[other_path]
                        if imp.module and imp.module.endswith(other_module.name):
                            module_info.dependencies.add(other_path)
                            other_module.dependents.add(module_path)
    
    def _detect_similarities(self) -> List[SimilarityResult]:
        """检测相似模块"""
        similarities = []
        processed_pairs = set()
        
        module_paths = list(self.modules.keys())
        
        for i, path1 in enumerate(module_paths):
            for path2 in module_paths[i+1:]:
                pair_key = tuple(sorted([path1, path2]))
                if pair_key in processed_pairs:
                    continue
                processed_pairs.add(pair_key)
                
                similarity = self._calculate_similarity(path1, path2)
                
                if similarity >= self.SIMILARITY_THRESHOLDS[SimilarityType.RELATED]:
                    sim_type = self._get_similarity_type(similarity)
                    
                    similar_parts = self._find_similar_parts(path1, path2)
                    
                    recommendation = self._generate_similarity_recommendation(
                        path1, path2, sim_type, similarity
                    )
                    
                    similarities.append(SimilarityResult(
                        file1=path1,
                        file2=path2,
                        similarity_type=sim_type,
                        similarity_score=similarity,
                        similar_parts=similar_parts,
                        recommendation=recommendation
                    ))
        
        similarities.sort(key=lambda x: x.similarity_score, reverse=True)
        return similarities
    
    def _calculate_similarity(self, path1: str, path2: str) -> float:
        """计算两个模块的相似度"""
        module1 = self.modules[path1]
        module2 = self.modules[path2]
        
        funcs1 = set(f.name for f in module1.functions)
        funcs2 = set(f.name for f in module2.functions)
        
        if funcs1 or funcs2:
            func_similarity = len(funcs1 & funcs2) / max(len(funcs1 | funcs2), 1)
        else:
            func_similarity = 0
        
        classes1 = set(c.name for c in module1.classes)
        classes2 = set(c.name for c in module2.classes)
        
        if classes1 or classes2:
            class_similarity = len(classes1 & classes2) / max(len(classes1 | classes2), 1)
        else:
            class_similarity = 0
        
        imports1 = set(i.module for i in module1.imports)
        imports2 = set(i.module for i in module2.imports)
        
        if imports1 or imports2:
            import_similarity = len(imports1 & imports2) / max(len(imports1 | imports2), 1)
        else:
            import_similarity = 0
        
        name_similarity = SequenceMatcher(None, path1, path2).ratio()
        
        weights = {
            'function': 0.35,
            'class': 0.25,
            'import': 0.20,
            'name': 0.20
        }
        
        total_similarity = (
            func_similarity * weights['function'] +
            class_similarity * weights['class'] +
            import_similarity * weights['import'] +
            name_similarity * weights['name']
        )
        
        return total_similarity
    
    def _get_similarity_type(self, score: float) -> SimilarityType:
        """根据分数获取相似类型"""
        if score >= self.SIMILARITY_THRESHOLDS[SimilarityType.DUPLICATE]:
            return SimilarityType.DUPLICATE
        elif score >= self.SIMILARITY_THRESHOLDS[SimilarityType.SIMILAR]:
            return SimilarityType.SIMILAR
        else:
            return SimilarityType.RELATED
    
    def _find_similar_parts(self, path1: str, path2: str) -> List[Dict[str, Any]]:
        """找出相似的部分"""
        similar_parts = []
        
        module1 = self.modules[path1]
        module2 = self.modules[path2]
        
        funcs1 = {f.name: f for f in module1.functions}
        funcs2 = {f.name: f for f in module2.functions}
        
        common_funcs = set(funcs1.keys()) & set(funcs2.keys())
        for func_name in common_funcs:
            similar_parts.append({
                "type": "function",
                "name": func_name,
                "location1": f"{path1}:{funcs1[func_name].line_number}",
                "location2": f"{path2}:{funcs2[func_name].line_number}"
            })
        
        classes1 = {c.name: c for c in module1.classes}
        classes2 = {c.name: c for c in module2.classes}
        
        common_classes = set(classes1.keys()) & set(classes2.keys())
        for class_name in common_classes:
            similar_parts.append({
                "type": "class",
                "name": class_name,
                "location1": f"{path1}:{classes1[class_name].line_number}",
                "location2": f"{path2}:{classes2[class_name].line_number}"
            })
        
        return similar_parts
    
    def _generate_similarity_recommendation(
        self,
        path1: str,
        path2: str,
        sim_type: SimilarityType,
        score: float
    ) -> str:
        """生成相似性建议"""
        if sim_type == SimilarityType.DUPLICATE:
            return f"检测到重复代码 ({score:.0%})，建议合并或提取公共模块"
        elif sim_type == SimilarityType.SIMILAR:
            return f"检测到相似代码 ({score:.0%})，建议提取公共函数或基类"
        else:
            return f"检测到相关代码 ({score:.0%})，可考虑统一管理"
    
    def _analyze_dependencies(self) -> List[DependencyEdge]:
        """分析依赖关系"""
        dependencies = []
        
        for module_path, module_info in self.modules.items():
            for dep in module_info.dependencies:
                dependencies.append(DependencyEdge(
                    source=module_path,
                    target=dep,
                    dependency_type="import",
                    strength=1
                ))
        
        return dependencies
    
    def _identify_issues(self) -> List[OptimizationIssue]:
        """识别优化问题"""
        issues = []
        
        for path, module in self.modules.items():
            for func in module.functions:
                if func.complexity > 10:
                    issues.append(OptimizationIssue(
                        issue_type="high_complexity",
                        severity=IssueSeverity.HIGH if func.complexity > 15 else IssueSeverity.MEDIUM,
                        location=f"{path}:{func.line_number}",
                        description=f"函数 '{func.name}' 圈复杂度过高 ({func.complexity})",
                        recommendation="重构函数，拆分为更小的函数",
                        impact="降低代码可维护性和可测试性"
                    ))
            
            if module.lines_of_code > 500:
                issues.append(OptimizationIssue(
                    issue_type="large_file",
                    severity=IssueSeverity.MEDIUM,
                    location=path,
                    description=f"文件过大 ({module.lines_of_code} 行)",
                    recommendation="考虑拆分为多个模块",
                    impact="影响代码可读性和维护性"
                ))
            
            if len(module.functions) > 20:
                issues.append(OptimizationIssue(
                    issue_type="too_many_functions",
                    severity=IssueSeverity.LOW,
                    location=path,
                    description=f"函数数量过多 ({len(module.functions)})",
                    recommendation="考虑按职责拆分模块",
                    impact="降低代码组织性"
                ))
            
            if not module.description and module.module_type in [ModuleType.API, ModuleType.SERVICE, ModuleType.MODEL]:
                issues.append(OptimizationIssue(
                    issue_type="missing_docstring",
                    severity=IssueSeverity.LOW,
                    location=path,
                    description="模块缺少文档字符串",
                    recommendation="添加模块级别的文档字符串",
                    impact="降低代码可读性"
                ))
            
            if len(module.dependencies) > 10:
                issues.append(OptimizationIssue(
                    issue_type="high_coupling",
                    severity=IssueSeverity.MEDIUM,
                    location=path,
                    description=f"模块依赖过多 ({len(module.dependencies)})",
                    recommendation="减少依赖，提高模块独立性",
                    impact="增加维护成本和测试难度"
                ))
        
        for path, module in self.modules.items():
            if len(module.dependents) == 0 and module.module_type not in [ModuleType.TEST, ModuleType.SCRIPT, ModuleType.CONFIG]:
                if not path.endswith('__init__.py') and not path.endswith('main.py'):
                    issues.append(OptimizationIssue(
                        issue_type="unused_module",
                        severity=IssueSeverity.LOW,
                        location=path,
                        description="模块未被其他模块引用",
                        recommendation="确认模块是否仍在使用，或添加引用",
                        impact="可能是死代码"
                    ))
        
        issues.sort(key=lambda x: {
            IssueSeverity.CRITICAL: 0,
            IssueSeverity.HIGH: 1,
            IssueSeverity.MEDIUM: 2,
            IssueSeverity.LOW: 3,
            IssueSeverity.INFO: 4
        }[x.severity])
        
        return issues
    
    def _generate_recommendations(
        self,
        similarities: List[SimilarityResult],
        issues: List[OptimizationIssue]
    ) -> List[str]:
        """生成优化建议"""
        recommendations = []
        
        duplicates = [s for s in similarities if s.similarity_type == SimilarityType.DUPLICATE]
        if duplicates:
            recommendations.append(f"发现 {len(duplicates)} 组重复代码，建议合并或提取公共模块")
        
        similar = [s for s in similarities if s.similarity_type == SimilarityType.SIMILAR]
        if similar:
            recommendations.append(f"发现 {len(similar)} 组相似代码，建议提取公共函数或基类")
        
        high_complexity = [i for i in issues if i.issue_type == "high_complexity"]
        if high_complexity:
            recommendations.append(f"发现 {len(high_complexity)} 个高复杂度函数，建议重构拆分")
        
        large_files = [i for i in issues if i.issue_type == "large_file"]
        if large_files:
            recommendations.append(f"发现 {len(large_files)} 个过大文件，建议拆分模块")
        
        high_coupling = [i for i in issues if i.issue_type == "high_coupling"]
        if high_coupling:
            recommendations.append(f"发现 {len(high_coupling)} 个高耦合模块，建议降低依赖")
        
        unused = [i for i in issues if i.issue_type == "unused_module"]
        if unused:
            recommendations.append(f"发现 {len(unused)} 个可能未使用的模块，建议确认是否需要保留")
        
        return recommendations
    
    def _calculate_statistics(self) -> Dict[str, Any]:
        """计算统计信息"""
        if not self.modules:
            return {}
        
        type_counts = defaultdict(int)
        for module in self.modules.values():
            type_counts[module.module_type.value] += 1
        
        total_functions = sum(len(m.functions) for m in self.modules.values())
        total_classes = sum(len(m.classes) for m in self.modules.values())
        total_loc = sum(m.lines_of_code for m in self.modules.values())
        
        avg_complexity = 0
        total_funcs = 0
        for module in self.modules.values():
            for func in module.functions:
                avg_complexity += func.complexity
                total_funcs += 1
        avg_complexity = avg_complexity / total_funcs if total_funcs > 0 else 0
        
        return {
            "modules_by_type": dict(type_counts),
            "total_functions": total_functions,
            "total_classes": total_classes,
            "total_lines_of_code": total_loc,
            "average_complexity": round(avg_complexity, 2),
            "average_file_size": round(total_loc / len(self.modules), 2) if self.modules else 0
        }
    
    def generate_report_markdown(self, report: BackendAnalysisReport) -> str:
        """生成Markdown格式报告"""
        lines = [
            f"# 后端模块分析报告",
            "",
            f"**生成时间**: {report.timestamp}",
            f"**分析路径**: {report.backend_path}",
            "",
            "## 概览",
            "",
            f"- **总模块数**: {report.total_modules}",
            f"- **总代码行数**: {report.total_lines_of_code:,}",
            f"- **函数总数**: {report.statistics.get('total_functions', 0)}",
            f"- **类总数**: {report.statistics.get('total_classes', 0)}",
            f"- **平均复杂度**: {report.statistics.get('average_complexity', 0)}",
            "",
            "## 模块类型分布",
            "",
            "| 类型 | 数量 |",
            "|------|------|",
        ]
        
        for module_type, count in report.statistics.get('modules_by_type', {}).items():
            lines.append(f"| {module_type} | {count} |")
        
        if report.similarities:
            lines.extend([
                "",
                "## 相似模块检测",
                "",
                "| 文件1 | 文件2 | 相似度 | 类型 | 建议 |",
                "|-------|-------|--------|------|------|",
            ])
            for sim in report.similarities[:20]:
                lines.append(
                    f"| {sim.file1[:30]}... | {sim.file2[:30]}... | "
                    f"{sim.similarity_score:.0%} | {sim.similarity_type.value} | "
                    f"{sim.recommendation[:30]}... |"
                )
        
        if report.issues:
            lines.extend([
                "",
                "## 问题列表",
                "",
                "| 严重程度 | 类型 | 位置 | 描述 | 建议 |",
                "|----------|------|------|------|------|",
            ])
            for issue in report.issues[:30]:
                lines.append(
                    f"| {issue.severity.value} | {issue.issue_type} | "
                    f"{issue.location[:30]}... | {issue.description[:40]}... | "
                    f"{issue.recommendation[:30]}... |"
                )
        
        if report.recommendations:
            lines.extend([
                "",
                "## 优化建议",
                "",
            ])
            for i, rec in enumerate(report.recommendations, 1):
                lines.append(f"{i}. {rec}")
        
        return "\n".join(lines)


def main() -> int:
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="后端模块分析器")
    parser.add_argument("--backend", type=str, required=True, help="后端代码路径")
    parser.add_argument("--output", type=str, choices=["console", "json", "markdown"], 
                       default="console", help="输出格式")
    parser.add_argument("--report-dir", type=str, default=str(get_path_config().REPORTS_DIR), help="报告输出目录")
    
    args = parser.parse_args()
    
    analyzer = BackendModuleAnalyzer()
    backend_path = Path(args.backend)
    
    if not backend_path.exists():
        print(f"错误: 路径不存在 {backend_path}")
        return 1
    
    report = analyzer.analyze(backend_path)
    
    if args.output == "console":
        print(analyzer.generate_report_markdown(report))
    elif args.output == "json":
        print(json.dumps(report.to_dict(), indent=2, ensure_ascii=False))
    elif args.output == "markdown":
        report_dir = Path(args.report_dir)
        report_dir.mkdir(parents=True, exist_ok=True)
        report_path = report_dir / "backend_analysis_report.md"
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(analyzer.generate_report_markdown(report))
        print(f"报告已保存: {report_path}")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
