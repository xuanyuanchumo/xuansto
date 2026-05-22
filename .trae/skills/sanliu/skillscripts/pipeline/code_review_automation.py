#!/usr/bin/env python3
"""
代码审查自动化器 - Sanliu 技能流水线版本 (增强版)

功能：
1. 变更风险分析 - 分析代码变更的风险级别
2. 审查规则智能选择 - 根据变更类型选择合适的审查规则
3. 代码质量检查 - 复杂度、重复度分析
4. 安全漏洞扫描 - 识别潜在安全问题
5. 代码风格检查 - 遵循编码规范
6. 审查报告自动生成 - 多格式报告输出
7. 审查建议自动修复 - 提供修复建议

增强功能：
8. 依赖关系分析 - 分析模块间依赖关系
9. 设计模式检测 - 识别常见设计模式
10. 代码重复检测 - 检测重复代码块
11. 技术债务评估 - 评估技术债务
12. 趋势分析报告 - 生成趋势分析
13. 自动修复功能 - 自动修复简单问题

使用方法：
    python code_review_automation.py --help
    python code_review_automation.py --target backend/app
    python code_review_automation.py --target frontend/src --rules rules.json
"""

import ast
import hashlib
import json
import re
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple, Callable

from skillscripts.core.script_base import ScriptBase, ReportFormat, ScriptResult, ScriptStatus


class Severity(Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class IssueType(Enum):
    STYLE = "style"
    COMPLEXITY = "complexity"
    SECURITY = "security"
    PERFORMANCE = "performance"
    MAINTAINABILITY = "maintainability"
    BEST_PRACTICE = "best_practice"
    CODE_SMELL = "code_smell"
    RISK = "risk"
    DEPENDENCY = "dependency"
    DUPLICATION = "duplication"
    TECH_DEBT = "tech_debt"
    PATTERN = "pattern"


class RiskLevel(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class RuleCategory(Enum):
    SECURITY = "security"
    PERFORMANCE = "performance"
    MAINTAINABILITY = "maintainability"
    STYLE = "style"
    COMPLEXITY = "complexity"
    BEST_PRACTICE = "best_practice"
    DEPENDENCY = "dependency"
    DUPLICATION = "duplication"


class PatternType(Enum):
    SINGLETON = "singleton"
    FACTORY = "factory"
    OBSERVER = "observer"
    STRATEGY = "strategy"
    DECORATOR = "decorator"
    ADAPTER = "adapter"
    FACADE = "facade"
    PROXY = "proxy"
    COMMAND = "command"
    ITERATOR = "iterator"


@dataclass
class Issue:
    file: str
    line: int
    column: int
    severity: Severity
    issue_type: IssueType
    message: str
    rule_id: str
    suggestion: str = ""
    code_snippet: str = ""
    auto_fixable: bool = False
    risk_level: RiskLevel = RiskLevel.LOW
    fix_code: str = ""
    debt_minutes: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "file": self.file,
            "line": self.line,
            "column": self.column,
            "severity": self.severity.value,
            "type": self.issue_type.value,
            "message": self.message,
            "rule_id": self.rule_id,
            "suggestion": self.suggestion,
            "auto_fixable": self.auto_fixable,
            "risk_level": self.risk_level.value,
            "fix_code": self.fix_code,
            "debt_minutes": self.debt_minutes
        }


@dataclass
class ReviewResult:
    file: str
    issues: List[Issue] = field(default_factory=list)
    metrics: Dict[str, Any] = field(default_factory=dict)
    risk_assessment: Dict[str, Any] = field(default_factory=dict)
    dependencies: Dict[str, Any] = field(default_factory=dict)
    patterns: List[Dict[str, Any]] = field(default_factory=list)
    duplications: List[Dict[str, Any]] = field(default_factory=list)
    tech_debt: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "file": self.file,
            "issue_count": len(self.issues),
            "issues": [i.to_dict() for i in self.issues],
            "metrics": self.metrics,
            "risk_assessment": self.risk_assessment,
            "dependencies": self.dependencies,
            "patterns": self.patterns,
            "duplications": self.duplications,
            "tech_debt": self.tech_debt
        }


@dataclass
class ReviewRule:
    rule_id: str
    name: str
    category: RuleCategory
    severity: Severity
    description: str
    check_function: str
    auto_fixable: bool = False
    enabled: bool = True
    priority: int = 1


@dataclass
class RiskAssessment:
    overall_risk: RiskLevel
    risk_score: float
    risk_factors: List[str]
    affected_areas: List[str]
    recommendations: List[str]
    confidence: float


@dataclass
class DependencyInfo:
    module: str
    imports: Set[str]
    imported_by: Set[str]
    circular_deps: List[str]
    coupling_score: float


@dataclass
class DuplicationBlock:
    file1: str
    file2: str
    start_line1: int
    end_line1: int
    start_line2: int
    end_line2: int
    similarity: float
    code_hash: str


class RiskAnalyzer:
    """变更风险分析器 - 增强版"""

    CRITICAL_PATTERNS = [
        (r"password\s*=\s*['\"]", "硬编码密码", 10),
        (r"api_key\s*=\s*['\"]", "硬编码API密钥", 10),
        (r"secret\s*=\s*['\"]", "硬编码密钥", 10),
        (r"token\s*=\s*['\"]", "硬编码令牌", 10),
        (r"eval\s*\(", "动态代码执行", 9),
        (r"exec\s*\(", "动态代码执行", 9),
        (r"__import__\s*\(", "动态导入", 8),
        (r"compile\s*\(", "动态编译", 8),
    ]

    HIGH_RISK_PATTERNS = [
        (r"SELECT\s+.*\s+FROM\s+.*\+.*", "SQL注入风险", 8),
        (r"execute\s*\(\s*['\"]", "原始SQL执行", 7),
        (r"subprocess\.(call|run|Popen)", "子进程调用", 6),
        (r"os\.system\s*\(", "系统命令执行", 7),
        (r"open\s*\([^)]*,\s*['\"]w['\"]", "文件写入操作", 5),
        (r"pickle\.loads?\s*\(", "不安全的反序列化", 7),
        (r"yaml\.load\s*\([^)]*\)", "不安全的YAML加载", 6),
        (r"marshal\.loads?\s*\(", "不安全的序列化", 6),
    ]

    MEDIUM_RISK_PATTERNS = [
        (r"except\s*:", "裸异常捕获", 4),
        (r"except\s+Exception\s*:", "宽泛异常捕获", 3),
        (r"global\s+\w+", "全局变量", 3),
        (r"lambda\s*:", "Lambda表达式", 2),
        (r"TODO|FIXME|XXX|HACK", "技术债务标记", 2),
    ]

    def __init__(self, logger):
        self.logger = logger

    def assess_file_risk(self, file_path: Path, content: str, tree: ast.AST) -> RiskAssessment:
        """评估文件风险 - 增强版，包含更多检查维度"""
        risk_score = 0.0
        risk_factors = []
        affected_areas = []

        pattern_risk = self._check_patterns(content)
        risk_score += pattern_risk["score"]
        risk_factors.extend(pattern_risk["factors"])

        ast_risk = self._check_ast(tree)
        risk_score += ast_risk["score"]
        risk_factors.extend(ast_risk["factors"])
        affected_areas.extend(ast_risk["areas"])

        complexity_risk = self._check_complexity(tree)
        risk_score += complexity_risk["score"]
        risk_factors.extend(complexity_risk["factors"])

        security_risk = self._check_security_patterns(tree, content)
        risk_score += security_risk["score"]
        risk_factors.extend(security_risk["factors"])

        maintainability_risk = self._check_maintainability(tree, content)
        risk_score += maintainability_risk["score"]
        risk_factors.extend(maintainability_risk["factors"])

        overall_risk = self._calculate_overall_risk(risk_score)
        recommendations = self._generate_recommendations(risk_factors, overall_risk)
        confidence = self._calculate_confidence(risk_factors)

        return RiskAssessment(
            overall_risk=overall_risk,
            risk_score=risk_score,
            risk_factors=risk_factors,
            affected_areas=affected_areas,
            recommendations=recommendations,
            confidence=confidence
        )

    def _check_patterns(self, content: str) -> Dict[str, Any]:
        """检查风险模式"""
        score = 0.0
        factors = []

        for pattern, desc, weight in self.CRITICAL_PATTERNS:
            matches = re.findall(pattern, content, re.IGNORECASE)
            if matches:
                score += weight * len(matches)
                factors.append(f"关键风险: {desc} ({len(matches)}处)")

        for pattern, desc, weight in self.HIGH_RISK_PATTERNS:
            matches = re.findall(pattern, content, re.IGNORECASE)
            if matches:
                score += weight * len(matches)
                factors.append(f"高风险: {desc} ({len(matches)}处)")

        for pattern, desc, weight in self.MEDIUM_RISK_PATTERNS:
            matches = re.findall(pattern, content)
            if matches:
                score += weight * len(matches)
                factors.append(f"中等风险: {desc} ({len(matches)}处)")

        return {"score": score, "factors": factors}

    def _check_ast(self, tree: ast.AST) -> Dict[str, Any]:
        """检查AST风险 - 增强版"""
        score = 0.0
        factors = []
        areas = []

        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name):
                    func_name = node.func.id
                    if func_name in ["eval", "exec", "compile"]:
                        score += 8
                        factors.append(f"危险函数调用: {func_name}")
                        areas.append(f"函数: {func_name}")
                    elif func_name in ["input", "raw_input"]:
                        score += 2
                        factors.append(f"用户输入函数: {func_name}")

                if isinstance(node.func, ast.Attribute):
                    attr_name = node.func.attr
                    if attr_name in ["system", "popen"]:
                        score += 7
                        factors.append(f"系统命令调用: {attr_name}")

            elif isinstance(node, ast.Try):
                if not node.handlers or any(
                    isinstance(h.type, ast.Name) and h.type.id == "Exception"
                    for h in node.handlers if h.type
                ):
                    score += 3
                    factors.append("宽泛异常处理")

            elif isinstance(node, ast.Global):
                score += 2
                factors.append("使用全局变量")

            elif isinstance(node, ast.Import | ast.ImportFrom):
                module = node.module if isinstance(node, ast.ImportFrom) else None
                dangerous_modules = ["pickle", "marshal", "subprocess", "os"]
                if module and any(m in module for m in dangerous_modules):
                    score += 3
                    factors.append(f"导入危险模块: {module}")

        return {"score": score, "factors": factors, "areas": areas}

    def _check_complexity(self, tree: ast.AST) -> Dict[str, Any]:
        """检查复杂度风险"""
        score = 0.0
        factors = []

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
                complexity = self._calculate_function_complexity(node)
                if complexity > 15:
                    score += (complexity - 15) * 0.5
                    factors.append(f"函数 '{node.name}' 复杂度过高: {complexity}")

                if hasattr(node, 'end_lineno') and node.end_lineno:
                    length = node.end_lineno - node.lineno
                    if length > 50:
                        score += (length - 50) * 0.1
                        factors.append(f"函数 '{node.name}' 过长: {length}行")

        return {"score": score, "factors": factors}

    def _check_security_patterns(self, tree: ast.AST, content: str) -> Dict[str, Any]:
        """检查安全模式 - 新增"""
        score = 0.0
        factors = []

        sql_keywords = ["SELECT", "INSERT", "UPDATE", "DELETE", "DROP", "CREATE"]
        for node in ast.walk(tree):
            if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
                if isinstance(node.left, ast.Constant) and isinstance(node.left.value, str):
                    if any(kw in node.left.value.upper() for kw in sql_keywords):
                        score += 5
                        factors.append("SQL字符串拼接风险")

        hardcoded_secrets = re.findall(
            r'(password|secret|token|api_key|apikey)\s*=\s*["\'][^"\']{8,}["\']',
            content, re.IGNORECASE
        )
        if hardcoded_secrets:
            score += len(hardcoded_secrets) * 3
            factors.append(f"发现 {len(hardcoded_secrets)} 处可能的硬编码密钥")

        return {"score": score, "factors": factors}

    def _check_maintainability(self, tree: ast.AST, content: str) -> Dict[str, Any]:
        """检查可维护性 - 新增"""
        score = 0.0
        factors = []

        todo_patterns = [
            (r'#\s*TODO', "TODO标记"),
            (r'#\s*FIXME', "FIXME标记"),
            (r'#\s*XXX', "XXX标记"),
            (r'#\s*HACK', "HACK标记"),
        ]

        for pattern, desc in todo_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            if matches:
                score += len(matches) * 0.5
                factors.append(f"{desc}: {len(matches)}处")

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
                if not ast.get_docstring(node):
                    score += 0.2
                if len(node.args.args) > 5:
                    score += 0.3
                    factors.append(f"函数 '{node.name}' 参数过多")

        return {"score": score, "factors": factors}

    def _calculate_function_complexity(self, node: ast.FunctionDef) -> int:
        """计算函数复杂度"""
        complexity = 1
        for child in ast.walk(node):
            if isinstance(child, ast.If | ast.While | ast.For | ast.ExceptHandler):
                complexity += 1
            elif isinstance(child, ast.BoolOp):
                complexity += len(child.values) - 1
            elif isinstance(child, ast.comprehension):
                complexity += 1
                if child.ifs:
                    complexity += len(child.ifs)
        return complexity

    def _calculate_overall_risk(self, score: float) -> RiskLevel:
        """计算整体风险级别"""
        if score >= 20:
            return RiskLevel.CRITICAL
        elif score >= 10:
            return RiskLevel.HIGH
        elif score >= 5:
            return RiskLevel.MEDIUM
        return RiskLevel.LOW

    def _generate_recommendations(self, factors: List[str], risk_level: RiskLevel) -> List[str]:
        """生成建议"""
        recommendations = []

        if risk_level == RiskLevel.CRITICAL:
            recommendations.append("代码存在严重风险，建议立即修复后再合并")
        elif risk_level == RiskLevel.HIGH:
            recommendations.append("代码存在高风险问题，建议优先处理")

        critical_factors = [f for f in factors if "关键风险" in f]
        if critical_factors:
            recommendations.append(f"发现 {len(critical_factors)} 个关键安全问题需要立即处理")

        security_factors = [f for f in factors if any(kw in f for kw in ["密码", "密钥", "令牌", "注入"])]
        if security_factors:
            recommendations.append("建议进行安全代码审查")

        complexity_factors = [f for f in factors if "复杂度" in f]
        if complexity_factors:
            recommendations.append("建议重构高复杂度函数")

        return recommendations

    def _calculate_confidence(self, factors: List[str]) -> float:
        """计算置信度"""
        if not factors:
            return 0.5
        return min(0.95, 0.6 + len(factors) * 0.05)


class DependencyAnalyzer:
    """依赖关系分析器 - 新增"""

    def __init__(self, logger):
        self.logger = logger
        self.dependencies: Dict[str, DependencyInfo] = {}
        self.import_graph: Dict[str, Set[str]] = defaultdict(set)

    def analyze_file(self, file_path: Path, tree: ast.AST) -> Dict[str, Any]:
        """分析单个文件的依赖关系"""
        imports = set()
        internal_imports = set()
        external_imports = set()

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.add(alias.name)
                    external_imports.add(alias.name)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imports.add(node.module)
                    if not node.level:
                        external_imports.add(node.module)
                    else:
                        internal_imports.add(node.module)

        module_name = str(file_path.stem)
        self.dependencies[module_name] = DependencyInfo(
            module=module_name,
            imports=imports,
            imported_by=set(),
            circular_deps=[],
            coupling_score=0.0
        )

        self.import_graph[module_name] = imports

        return {
            "module": module_name,
            "total_imports": len(imports),
            "imports": list(imports),
            "internal_imports": list(internal_imports),
            "external_imports": list(external_imports),
            "coupling_score": len(imports) * 0.1
        }

    def detect_circular_dependencies(self) -> List[Tuple[str, str]]:
        """检测循环依赖"""
        circular = []

        def find_cycle(start: str, current: str, visited: Set[str], path: List[str]) -> Optional[List[str]]:
            if current in visited:
                if current == start and len(path) > 1:
                    return path
                return None

            visited.add(current)
            path.append(current)

            for dep in self.import_graph.get(current, set()):
                cycle = find_cycle(start, dep, visited.copy(), path.copy())
                if cycle:
                    return cycle

            return None

        for module in self.import_graph:
            cycle = find_cycle(module, module, set(), [])
            if cycle:
                circular.append((cycle[0], cycle[-1] if len(cycle) > 1 else cycle[0]))

        return list(set(circular))

    def calculate_coupling_metrics(self) -> Dict[str, float]:
        """计算耦合度指标"""
        metrics = {}

        for module, info in self.dependencies.items():
            afferent = len(info.imported_by)
            efferent = len(info.imports)

            if afferent + efferent > 0:
                instability = efferent / (afferent + efferent)
            else:
                instability = 0.0

            info.coupling_score = instability
            metrics[module] = {
                "afferent_coupling": afferent,
                "efferent_coupling": efferent,
                "instability": round(instability, 3)
            }

        return metrics

    def get_dependency_issues(self, file_path: Path) -> List[Issue]:
        """获取依赖相关问题"""
        issues = []
        module_name = str(file_path.stem)

        if module_name in self.dependencies:
            info = self.dependencies[module_name]

            if len(info.imports) > 20:
                issues.append(Issue(
                    file=str(file_path),
                    line=1,
                    column=0,
                    severity=Severity.WARNING,
                    issue_type=IssueType.DEPENDENCY,
                    message=f"模块导入过多 ({len(info.imports)} 个)",
                    rule_id="DEP_TOO_MANY_IMPORTS",
                    suggestion="考虑拆分模块或合并相关导入",
                    risk_level=RiskLevel.MEDIUM,
                    debt_minutes=15
                ))

            if info.circular_deps:
                issues.append(Issue(
                    file=str(file_path),
                    line=1,
                    column=0,
                    severity=Severity.ERROR,
                    issue_type=IssueType.DEPENDENCY,
                    message=f"存在循环依赖: {', '.join(info.circular_deps)}",
                    rule_id="DEP_CIRCULAR",
                    suggestion="重构代码消除循环依赖",
                    risk_level=RiskLevel.HIGH,
                    debt_minutes=60
                ))

        return issues


class PatternDetector:
    """设计模式检测器 - 新增"""

    def __init__(self, logger):
        self.logger = logger
        self.detected_patterns: List[Dict[str, Any]] = []

    def detect_patterns(self, tree: ast.AST, file_path: Path) -> List[Dict[str, Any]]:
        """检测设计模式"""
        patterns = []

        patterns.extend(self._detect_singleton(tree, file_path))
        patterns.extend(self._detect_factory(tree, file_path))
        patterns.extend(self._detect_observer(tree, file_path))
        patterns.extend(self._detect_strategy(tree, file_path))
        patterns.extend(self._detect_decorator(tree, file_path))

        self.detected_patterns.extend(patterns)
        return patterns

    def _detect_singleton(self, tree: ast.AST, file_path: Path) -> List[Dict[str, Any]]:
        """检测单例模式"""
        patterns = []

        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                has_instance_var = False
                has_get_instance = False

                for item in node.body:
                    if isinstance(item, ast.Assign):
                        for target in item.targets:
                            if isinstance(target, ast.Name) and target.id in ['_instance', 'instance', '__instance']:
                                has_instance_var = True

                    if isinstance(item, ast.FunctionDef):
                        if item.name in ['get_instance', 'getInstance', '__new__']:
                            has_get_instance = True

                if has_instance_var and has_get_instance:
                    patterns.append({
                        "type": PatternType.SINGLETON.value,
                        "class": node.name,
                        "line": node.lineno,
                        "confidence": 0.8,
                        "file": str(file_path)
                    })

        return patterns

    def _detect_factory(self, tree: ast.AST, file_path: Path) -> List[Dict[str, Any]]:
        """检测工厂模式"""
        patterns = []

        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                factory_indicators = 0

                for item in node.body:
                    if isinstance(item, ast.FunctionDef):
                        if any(name in item.name.lower() for name in ['create', 'build', 'make', 'factory']):
                            factory_indicators += 1

                        if item.name == '__init__':
                            for arg in item.args.args:
                                if 'type' in arg.arg.lower() or 'kind' in arg.arg.lower():
                                    factory_indicators += 1

                if factory_indicators >= 2:
                    patterns.append({
                        "type": PatternType.FACTORY.value,
                        "class": node.name,
                        "line": node.lineno,
                        "confidence": 0.7,
                        "file": str(file_path)
                    })

        return patterns

    def _detect_observer(self, tree: ast.AST, file_path: Path) -> List[Dict[str, Any]]:
        """检测观察者模式"""
        patterns = []

        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                has_observers = False
                has_notify = False

                for item in node.body:
                    if isinstance(item, ast.Assign):
                        for target in item.targets:
                            if isinstance(target, ast.Name):
                                if 'observer' in target.id.lower() or 'listener' in target.id.lower():
                                    has_observers = True

                    if isinstance(item, ast.FunctionDef):
                        if any(name in item.name.lower() for name in ['notify', 'update', 'publish', 'emit']):
                            has_notify = True

                if has_observers and has_notify:
                    patterns.append({
                        "type": PatternType.OBSERVER.value,
                        "class": node.name,
                        "line": node.lineno,
                        "confidence": 0.75,
                        "file": str(file_path)
                    })

        return patterns

    def _detect_strategy(self, tree: ast.AST, file_path: Path) -> List[Dict[str, Any]]:
        """检测策略模式"""
        patterns = []

        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                has_strategy_attr = False
                has_execute = False

                for item in node.body:
                    if isinstance(item, ast.Assign):
                        for target in item.targets:
                            if isinstance(target, ast.Name):
                                if 'strategy' in target.id.lower():
                                    has_strategy_attr = True

                    if isinstance(item, ast.FunctionDef):
                        if any(name in item.name.lower() for name in ['execute', 'run', 'apply', 'do']):
                            has_execute = True

                if has_strategy_attr and has_execute:
                    patterns.append({
                        "type": PatternType.STRATEGY.value,
                        "class": node.name,
                        "line": node.lineno,
                        "confidence": 0.7,
                        "file": str(file_path)
                    })

        return patterns

    def _detect_decorator(self, tree: ast.AST, file_path: Path) -> List[Dict[str, Any]]:
        """检测装饰器模式"""
        patterns = []

        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                has_wrapper = False
                has_component = False

                for item in node.body:
                    if isinstance(item, ast.FunctionDef):
                        if item.name == '__init__':
                            for arg in item.args.args:
                                if 'component' in arg.arg.lower() or 'wrapped' in arg.arg.lower():
                                    has_component = True

                        if item.name == '__call__' or 'wrap' in item.name.lower():
                            has_wrapper = True

                if has_wrapper and has_component:
                    patterns.append({
                        "type": PatternType.DECORATOR.value,
                        "class": node.name,
                        "line": node.lineno,
                        "confidence": 0.75,
                        "file": str(file_path)
                    })

        return patterns


class CodeDuplicationDetector:
    """代码重复检测器 - 新增"""

    MIN_BLOCK_SIZE = 6
    SIMILARITY_THRESHOLD = 0.8

    def __init__(self, logger):
        self.logger = logger
        self.code_blocks: Dict[str, List[Tuple[str, int, int, str]]] = defaultdict(list)

    def analyze_file(self, file_path: Path, content: str) -> List[Dict[str, Any]]:
        """分析文件中的代码重复"""
        duplications = []
        lines = content.split('\n')

        blocks = self._extract_blocks(lines)

        for block_hash, locations in blocks.items():
            if len(locations) > 1:
                for i, (file1, start1, end1, code) in enumerate(locations):
                    for file2, start2, end2, _ in locations[i+1:]:
                        duplications.append({
                            "file1": file1,
                            "file2": file2,
                            "start_line1": start1,
                            "end_line1": end1,
                            "start_line2": start2,
                            "end_line2": end2,
                            "similarity": 1.0,
                            "code_hash": block_hash,
                            "lines": end1 - start1 + 1
                        })

        return duplications

    def _extract_blocks(self, lines: List[str]) -> Dict[str, List[Tuple[str, int, int, str]]]:
        """提取代码块并计算哈希"""
        blocks = defaultdict(list)

        for i in range(len(lines) - self.MIN_BLOCK_SIZE + 1):
            block_lines = lines[i:i + self.MIN_BLOCK_SIZE]
            block_code = '\n'.join(line.strip() for line in block_lines if line.strip())

            if len(block_code) > 20:
                block_hash = hashlib.md5(block_code.encode()).hexdigest()
                blocks[block_hash].append(("current", i + 1, i + self.MIN_BLOCK_SIZE, block_code))

        return blocks

    def detect_cross_file_duplication(self, files: List[Tuple[Path, str]]) -> List[DuplicationBlock]:
        """检测跨文件重复"""
        duplications = []
        all_blocks = {}

        for file_path, content in files:
            lines = content.split('\n')
            for i in range(len(lines) - self.MIN_BLOCK_SIZE + 1):
                block_lines = lines[i:i + self.MIN_BLOCK_SIZE]
                block_code = '\n'.join(line.strip() for line in block_lines if line.strip())

                if len(block_code) > 20:
                    block_hash = hashlib.md5(block_code.encode()).hexdigest()

                    if block_hash in all_blocks:
                        for existing in all_blocks[block_hash]:
                            duplications.append(DuplicationBlock(
                                file1=str(existing[0]),
                                file2=str(file_path),
                                start_line1=existing[1],
                                end_line1=existing[2],
                                start_line2=i + 1,
                                end_line2=i + self.MIN_BLOCK_SIZE,
                                similarity=1.0,
                                code_hash=block_hash
                            ))
                        all_blocks[block_hash].append((file_path, i + 1, i + self.MIN_BLOCK_SIZE))
                    else:
                        all_blocks[block_hash] = [(file_path, i + 1, i + self.MIN_BLOCK_SIZE)]

        return duplications

    def get_duplication_issues(self, duplications: List[Dict[str, Any]], file_path: Path) -> List[Issue]:
        """获取重复代码问题"""
        issues = []

        for dup in duplications:
            if dup["file1"] == str(file_path) or dup["file2"] == str(file_path):
                issues.append(Issue(
                    file=str(file_path),
                    line=dup["start_line1"] if dup["file1"] == str(file_path) else dup["start_line2"],
                    column=0,
                    severity=Severity.WARNING,
                    issue_type=IssueType.DUPLICATION,
                    message=f"发现重复代码块 ({dup['lines']} 行)",
                    rule_id="DUP_CODE_BLOCK",
                    suggestion="将重复代码提取为公共函数或类",
                    risk_level=RiskLevel.MEDIUM,
                    debt_minutes=dup['lines'] * 2
                ))

        return issues


class TechnicalDebtEstimator:
    """技术债务评估器 - 新增"""

    DEBT_RATES = {
        "complexity": 15,
        "duplication": 10,
        "style": 5,
        "security": 30,
        "maintainability": 10,
        "documentation": 3,
        "test_coverage": 20,
    }

    DEBT_PATTERNS = [
        (r'#\s*TODO[:\s]*(.+)', "TODO", 15),
        (r'#\s*FIXME[:\s]*(.+)', "FIXME", 30),
        (r'#\s*HACK[:\s]*(.+)', "HACK", 45),
        (r'#\s*XXX[:\s]*(.+)', "XXX", 60),
        (r'pass\s*#', "空实现", 10),
        (r'raise\s+NotImplementedError', "未实现", 30),
    ]

    def __init__(self, logger):
        self.logger = logger
        self.debt_items: List[Dict[str, Any]] = []

    def estimate_file_debt(self, file_path: Path, content: str, issues: List[Issue]) -> Dict[str, Any]:
        """评估文件的技术债务"""
        debt_items = []
        total_minutes = 0

        for pattern, debt_type, minutes in self.DEBT_PATTERNS:
            matches = re.finditer(pattern, content, re.IGNORECASE)
            for match in matches:
                description = match.group(1).strip() if match.groups() else debt_type
                debt_items.append({
                    "type": debt_type,
                    "line": content[:match.start()].count('\n') + 1,
                    "description": description,
                    "minutes": minutes
                })
                total_minutes += minutes

        for issue in issues:
            if issue.debt_minutes > 0:
                total_minutes += issue.debt_minutes
            else:
                rate = self.DEBT_RATES.get(issue.issue_type.value, 10)
                severity_multiplier = {
                    Severity.INFO: 1,
                    Severity.WARNING: 2,
                    Severity.ERROR: 3,
                    Severity.CRITICAL: 5
                }.get(issue.severity, 1)
                debt_minutes = rate * severity_multiplier
                total_minutes += debt_minutes

        complexity_debt = self._estimate_complexity_debt(content)
        total_minutes += complexity_debt

        return {
            "total_minutes": total_minutes,
            "total_hours": round(total_minutes / 60, 1),
            "items": debt_items,
            "complexity_debt": complexity_debt,
            "priority": self._calculate_priority(total_minutes, debt_items)
        }

    def _estimate_complexity_debt(self, content: str) -> int:
        """估算复杂度债务"""
        try:
            tree = ast.parse(content)
            debt = 0

            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
                    complexity = 1
                    for child in ast.walk(node):
                        if isinstance(child, ast.If | ast.While | ast.For | ast.ExceptHandler):
                            complexity += 1
                        elif isinstance(child, ast.BoolOp):
                            complexity += len(child.values) - 1

                    if complexity > 10:
                        debt += (complexity - 10) * 5

            return debt
        except Exception:
            return 0

    def _calculate_priority(self, total_minutes: int, items: List[Dict]) -> str:
        """计算优先级"""
        hack_count = sum(1 for item in items if item["type"] in ["HACK", "XXX"])

        if total_minutes > 240 or hack_count > 3:
            return "critical"
        elif total_minutes > 120 or hack_count > 1:
            return "high"
        elif total_minutes > 60:
            return "medium"
        return "low"

    def get_debt_issues(self, file_path: Path, debt_info: Dict[str, Any]) -> List[Issue]:
        """获取技术债务问题"""
        issues = []

        if debt_info["total_hours"] > 4:
            issues.append(Issue(
                file=str(file_path),
                line=1,
                column=0,
                severity=Severity.WARNING,
                issue_type=IssueType.TECH_DEBT,
                message=f"技术债务过高: {debt_info['total_hours']} 小时",
                rule_id="TECH_DEBT_HIGH",
                suggestion="建议安排时间进行代码重构",
                risk_level=RiskLevel.MEDIUM,
                debt_minutes=debt_info["total_minutes"]
            ))

        for item in debt_info["items"]:
            if item["type"] in ["HACK", "XXX"]:
                issues.append(Issue(
                    file=str(file_path),
                    line=item["line"],
                    column=0,
                    severity=Severity.WARNING,
                    issue_type=IssueType.TECH_DEBT,
                    message=f"{item['type']}: {item['description']}",
                    rule_id=f"TECH_DEBT_{item['type']}",
                    suggestion="修复此技术债务",
                    risk_level=RiskLevel.MEDIUM,
                    debt_minutes=item["minutes"]
                ))

        return issues


class RuleSelector:
    """审查规则智能选择器 - 增强版"""

    def __init__(self, logger):
        self.logger = logger
        self._rules: Dict[str, ReviewRule] = {}
        self._load_default_rules()

    def _load_default_rules(self) -> None:
        """加载默认规则"""
        default_rules = [
            ReviewRule(
                rule_id="SEC001",
                name="硬编码密码检测",
                category=RuleCategory.SECURITY,
                severity=Severity.CRITICAL,
                description="检测代码中硬编码的密码",
                check_function="check_hardcoded_password",
                auto_fixable=False,
                priority=1
            ),
            ReviewRule(
                rule_id="SEC002",
                name="SQL注入检测",
                category=RuleCategory.SECURITY,
                severity=Severity.CRITICAL,
                description="检测潜在的SQL注入风险",
                check_function="check_sql_injection",
                auto_fixable=False,
                priority=1
            ),
            ReviewRule(
                rule_id="SEC003",
                name="危险函数调用",
                category=RuleCategory.SECURITY,
                severity=Severity.ERROR,
                description="检测eval、exec等危险函数",
                check_function="check_dangerous_functions",
                auto_fixable=False,
                priority=1
            ),
            ReviewRule(
                rule_id="COMP001",
                name="函数复杂度检查",
                category=RuleCategory.COMPLEXITY,
                severity=Severity.WARNING,
                description="检查函数圈复杂度",
                check_function="check_function_complexity",
                auto_fixable=False,
                priority=2
            ),
            ReviewRule(
                rule_id="COMP002",
                name="函数长度检查",
                category=RuleCategory.COMPLEXITY,
                severity=Severity.WARNING,
                description="检查函数长度",
                check_function="check_function_length",
                auto_fixable=False,
                priority=2
            ),
            ReviewRule(
                rule_id="COMP003",
                name="嵌套深度检查",
                category=RuleCategory.COMPLEXITY,
                severity=Severity.WARNING,
                description="检查代码嵌套深度",
                check_function="check_nesting_depth",
                auto_fixable=False,
                priority=2
            ),
            ReviewRule(
                rule_id="MAIN001",
                name="文档字符串检查",
                category=RuleCategory.MAINTAINABILITY,
                severity=Severity.INFO,
                description="检查函数/类是否有文档字符串",
                check_function="check_docstring",
                auto_fixable=True,
                priority=3
            ),
            ReviewRule(
                rule_id="MAIN002",
                name="命名规范检查",
                category=RuleCategory.MAINTAINABILITY,
                severity=Severity.WARNING,
                description="检查命名是否符合规范",
                check_function="check_naming_convention",
                auto_fixable=True,
                priority=3
            ),
            ReviewRule(
                rule_id="PERF001",
                name="循环优化检查",
                category=RuleCategory.PERFORMANCE,
                severity=Severity.WARNING,
                description="检查循环中的性能问题",
                check_function="check_loop_performance",
                auto_fixable=False,
                priority=2
            ),
            ReviewRule(
                rule_id="STYLE001",
                name="行长度检查",
                category=RuleCategory.STYLE,
                severity=Severity.INFO,
                description="检查代码行长度",
                check_function="check_line_length",
                auto_fixable=True,
                priority=4
            ),
            ReviewRule(
                rule_id="DEP001",
                name="导入数量检查",
                category=RuleCategory.DEPENDENCY,
                severity=Severity.WARNING,
                description="检查模块导入数量",
                check_function="check_import_count",
                auto_fixable=False,
                priority=3
            ),
            ReviewRule(
                rule_id="DUP001",
                name="代码重复检测",
                category=RuleCategory.DUPLICATION,
                severity=Severity.WARNING,
                description="检测重复代码块",
                check_function="check_code_duplication",
                auto_fixable=False,
                priority=2
            ),
        ]

        for rule in default_rules:
            self._rules[rule.rule_id] = rule

    def select_rules(
        self,
        file_path: Path,
        content: str,
        risk_assessment: RiskAssessment
    ) -> List[ReviewRule]:
        """智能选择审查规则"""
        selected_rules = []

        if risk_assessment.overall_risk in [RiskLevel.CRITICAL, RiskLevel.HIGH]:
            security_rules = [
                r for r in self._rules.values()
                if r.category == RuleCategory.SECURITY and r.enabled
            ]
            selected_rules.extend(security_rules)

        if risk_assessment.overall_risk in [RiskLevel.HIGH, RiskLevel.MEDIUM]:
            complexity_rules = [
                r for r in self._rules.values()
                if r.category == RuleCategory.COMPLEXITY and r.enabled
            ]
            selected_rules.extend(complexity_rules)

        maintainability_rules = [
            r for r in self._rules.values()
            if r.category == RuleCategory.MAINTAINABILITY and r.enabled
        ]
        selected_rules.extend(maintainability_rules)

        if file_path.suffix == ".py":
            style_rules = [
                r for r in self._rules.values()
                if r.category == RuleCategory.STYLE and r.enabled
            ]
            selected_rules.extend(style_rules)

        for factor in risk_assessment.risk_factors:
            if "性能" in factor or "循环" in factor:
                perf_rules = [
                    r for r in self._rules.values()
                    if r.category == RuleCategory.PERFORMANCE and r.enabled
                ]
                selected_rules.extend(perf_rules)
                break

        dependency_rules = [
            r for r in self._rules.values()
            if r.category == RuleCategory.DEPENDENCY and r.enabled
        ]
        selected_rules.extend(dependency_rules)

        duplication_rules = [
            r for r in self._rules.values()
            if r.category == RuleCategory.DUPLICATION and r.enabled
        ]
        selected_rules.extend(duplication_rules)

        unique_rules = list({r.rule_id: r for r in selected_rules}.values())
        return sorted(unique_rules, key=lambda r: r.priority)

    def get_rule(self, rule_id: str) -> Optional[ReviewRule]:
        """获取规则"""
        return self._rules.get(rule_id)


class CodeQualityScorer:
    """代码质量评分器 - 增强版"""

    SCORING_WEIGHTS = {
        "maintainability": 0.30,
        "readability": 0.20,
        "complexity": 0.20,
        "test_coverage": 0.10,
        "security": 0.10,
        "documentation": 0.10
    }

    MAINTAINABILITY_PENALTY = {
        "critical": 25,
        "error": 15,
        "warning": 5,
        "info": 1
    }

    def calculate_scores(self, results: List[ReviewResult]) -> Dict[str, Any]:
        """计算质量分数"""
        maintainability = self._calculate_maintainability_score(results)
        readability = self._calculate_readability_score(results)
        complexity = self._calculate_complexity_score(results)
        test_coverage = self._estimate_test_coverage(results)
        security = self._calculate_security_score(results)
        documentation = self._calculate_documentation_score(results)

        overall_score = (
            maintainability * self.SCORING_WEIGHTS["maintainability"] +
            readability * self.SCORING_WEIGHTS["readability"] +
            complexity * self.SCORING_WEIGHTS["complexity"] +
            test_coverage * self.SCORING_WEIGHTS["test_coverage"] +
            security * self.SCORING_WEIGHTS["security"] +
            documentation * self.SCORING_WEIGHTS["documentation"]
        )

        return {
            "overall_score": round(overall_score, 1),
            "grade": self._get_grade(overall_score),
            "dimensions": {
                "maintainability": round(maintainability, 1),
                "readability": round(readability, 1),
                "complexity": round(complexity, 1),
                "test_coverage": round(test_coverage, 1),
                "security": round(security, 1),
                "documentation": round(documentation, 1)
            }
        }

    def _calculate_maintainability_score(self, results: List[ReviewResult]) -> float:
        if not results:
            return 100.0

        total_penalty = 0
        total_lines = sum(r.metrics.get("total_lines", 0) for r in results)

        if total_lines == 0:
            return 100.0

        for result in results:
            for issue in result.issues:
                penalty = self.MAINTAINABILITY_PENALTY.get(issue.severity.value, 1)
                total_penalty += penalty

        normalized_penalty = (total_penalty / total_lines) * 100
        return max(0.0, 100.0 - normalized_penalty)

    def _calculate_readability_score(self, results: List[ReviewResult]) -> float:
        if not results:
            return 100.0

        total_issues = 0
        for result in results:
            for issue in result.issues:
                if issue.issue_type.value in ["style", "best_practice"]:
                    total_issues += 1

        total_lines = sum(r.metrics.get("total_lines", 0) for r in results)
        if total_lines == 0:
            return 100.0

        score = 100.0 - (total_issues * 0.5)
        return max(0.0, min(100.0, score))

    def _calculate_complexity_score(self, results: List[ReviewResult]) -> float:
        if not results:
            return 100.0

        total_complexity = sum(r.metrics.get("complexity", 0) for r in results)
        total_functions = sum(r.metrics.get("functions", 0) for r in results)

        if total_functions == 0:
            return 100.0

        avg_complexity = total_complexity / total_functions

        if avg_complexity <= 5:
            return 100.0
        elif avg_complexity <= 10:
            return 90.0 - (avg_complexity - 5) * 4
        elif avg_complexity <= 15:
            return 70.0 - (avg_complexity - 10) * 6
        else:
            return max(0.0, 40.0 - (avg_complexity - 15) * 4)

    def _estimate_test_coverage(self, results: List[ReviewResult]) -> float:
        test_files = sum(1 for r in results if "test" in r.file.lower())
        source_files = len(results) - test_files

        if source_files == 0:
            return 100.0

        ratio = test_files / source_files
        return min(100.0, ratio * 100)

    def _calculate_security_score(self, results: List[ReviewResult]) -> float:
        """计算安全分数 - 新增"""
        if not results:
            return 100.0

        security_issues = 0
        for result in results:
            for issue in result.issues:
                if issue.issue_type == IssueType.SECURITY:
                    severity_weight = {
                        Severity.CRITICAL: 20,
                        Severity.ERROR: 10,
                        Severity.WARNING: 5,
                        Severity.INFO: 1
                    }.get(issue.severity, 1)
                    security_issues += severity_weight

        score = 100.0 - security_issues
        return max(0.0, min(100.0, score))

    def _calculate_documentation_score(self, results: List[ReviewResult]) -> float:
        """计算文档分数 - 新增"""
        if not results:
            return 100.0

        total_functions = 0
        documented_functions = 0

        for result in results:
            total_functions += result.metrics.get("functions", 0)
            documented_functions += result.metrics.get("documented_functions", 0)

        if total_functions == 0:
            return 100.0

        return (documented_functions / total_functions) * 100

    def _get_grade(self, score: float) -> str:
        if score >= 90:
            return "A+"
        elif score >= 85:
            return "A"
        elif score >= 80:
            return "A-"
        elif score >= 75:
            return "B+"
        elif score >= 70:
            return "B"
        elif score >= 65:
            return "B-"
        elif score >= 60:
            return "C+"
        elif score >= 55:
            return "C"
        elif score >= 50:
            return "C-"
        elif score >= 40:
            return "D"
        else:
            return "F"


class CodeSmellDetector:
    """代码异味检测器 - 增强版"""

    DETECTION_RULES = {
        "long_method": {"threshold": 50, "severity": Severity.WARNING},
        "large_class": {"threshold_methods": 15, "severity": Severity.WARNING},
        "long_parameter_list": {"threshold": 5, "severity": Severity.WARNING},
        "deep_nesting": {"threshold": 4, "severity": Severity.WARNING},
        "dead_code": {"severity": Severity.INFO},
        "magic_number": {"severity": Severity.INFO},
        "commented_code": {"severity": Severity.WARNING},
    }

    def detect(self, tree: ast.AST, source: str, file_path: Path) -> List[Issue]:
        """检测代码异味"""
        issues = []

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                issues.extend(self._check_function(node, file_path))
            elif isinstance(node, ast.ClassDef):
                issues.extend(self._check_class(node, file_path))

        issues.extend(self._check_magic_numbers(source, file_path))
        issues.extend(self._check_commented_code(source, file_path))
        issues.extend(self._check_dead_code(tree, file_path))

        return issues

    def _check_function(self, node: ast.FunctionDef, file_path: Path) -> List[Issue]:
        issues = []

        if hasattr(node, 'end_lineno') and node.end_lineno:
            length = node.end_lineno - node.lineno
            threshold = self.DETECTION_RULES["long_method"]["threshold"]
            if length > threshold:
                issues.append(Issue(
                    file=str(file_path),
                    line=node.lineno,
                    column=node.col_offset,
                    severity=self.DETECTION_RULES["long_method"]["severity"],
                    issue_type=IssueType.CODE_SMELL,
                    message=f"方法 '{node.name}' 过长 ({length} 行)",
                    rule_id="CODE_SMELL_LONG_METHOD",
                    suggestion="将方法拆分为多个更小的方法",
                    risk_level=RiskLevel.LOW,
                    debt_minutes=length - threshold
                ))

        params = len(node.args.args) + len(node.args.kwonlyargs)
        threshold = self.DETECTION_RULES["long_parameter_list"]["threshold"]
        if params > threshold:
            issues.append(Issue(
                file=str(file_path),
                line=node.lineno,
                column=node.col_offset,
                severity=self.DETECTION_RULES["long_parameter_list"]["severity"],
                issue_type=IssueType.CODE_SMELL,
                message=f"方法 '{node.name}' 参数过多 ({params} 个)",
                rule_id="CODE_SMELL_LONG_PARAMETER_LIST",
                suggestion="使用配置对象或数据类传递参数",
                risk_level=RiskLevel.LOW,
                debt_minutes=15
            ))

        max_depth = self._calculate_nesting_depth(node)
        threshold = self.DETECTION_RULES["deep_nesting"]["threshold"]
        if max_depth > threshold:
            issues.append(Issue(
                file=str(file_path),
                line=node.lineno,
                column=node.col_offset,
                severity=self.DETECTION_RULES["deep_nesting"]["severity"],
                issue_type=IssueType.CODE_SMELL,
                message=f"方法 '{node.name}' 嵌套层级过深 ({max_depth} 层)",
                rule_id="CODE_SMELL_DEEP_NESTING",
                suggestion="使用早返回或提取方法减少嵌套",
                risk_level=RiskLevel.MEDIUM,
                debt_minutes=max_depth * 10
            ))

        return issues

    def _check_class(self, node: ast.ClassDef, file_path: Path) -> List[Issue]:
        issues = []

        methods = [n for n in node.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]
        threshold = self.DETECTION_RULES["large_class"]["threshold_methods"]
        if len(methods) > threshold:
            issues.append(Issue(
                file=str(file_path),
                line=node.lineno,
                column=node.col_offset,
                severity=self.DETECTION_RULES["large_class"]["severity"],
                issue_type=IssueType.CODE_SMELL,
                message=f"类 '{node.name}' 过大 ({len(methods)} 个方法)",
                rule_id="CODE_SMELL_LARGE_CLASS",
                suggestion="考虑将类拆分为多个更小的类",
                risk_level=RiskLevel.LOW,
                debt_minutes=30
            ))

        return issues

    def _check_magic_numbers(self, source: str, file_path: Path) -> List[Issue]:
        issues = []
        lines = source.split('\n')

        for i, line in enumerate(lines, 1):
            numbers = re.findall(r'\b(\d{2,})\b', line)
            for num in numbers:
                if num not in ['0', '1', '100', '1000']:
                    issues.append(Issue(
                        file=str(file_path),
                        line=i,
                        column=0,
                        severity=Severity.INFO,
                        issue_type=IssueType.CODE_SMELL,
                        message=f"发现魔法数字 '{num}'",
                        rule_id="CODE_SMELL_MAGIC_NUMBER",
                        suggestion="将数字提取为命名常量",
                        risk_level=RiskLevel.LOW,
                        debt_minutes=5
                    ))

        return issues

    def _check_commented_code(self, source: str, file_path: Path) -> List[Issue]:
        """检测注释掉的代码 - 新增"""
        issues = []
        lines = source.split('\n')

        code_patterns = [
            r'#\s*(def|class|if|for|while|return|import|from)',
            r'#\s*\w+\s*\(',
            r'#\s*\w+\s*=\s*',
        ]

        for i, line in enumerate(lines, 1):
            for pattern in code_patterns:
                if re.search(pattern, line):
                    issues.append(Issue(
                        file=str(file_path),
                        line=i,
                        column=0,
                        severity=Severity.WARNING,
                        issue_type=IssueType.CODE_SMELL,
                        message="发现注释掉的代码",
                        rule_id="CODE_SMELL_COMMENTED_CODE",
                        suggestion="删除注释掉的代码或恢复使用",
                        risk_level=RiskLevel.LOW,
                        debt_minutes=5
                    ))
                    break

        return issues

    def _check_dead_code(self, tree: ast.AST, file_path: Path) -> List[Issue]:
        """检测死代码 - 新增"""
        issues = []

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                if not self._is_function_used(node.name, tree):
                    issues.append(Issue(
                        file=str(file_path),
                        line=node.lineno,
                        column=node.col_offset,
                        severity=Severity.INFO,
                        issue_type=IssueType.CODE_SMELL,
                        message=f"函数 '{node.name}' 可能未被使用",
                        rule_id="CODE_SMELL_DEAD_CODE",
                        suggestion="检查是否可以删除此函数",
                        risk_level=RiskLevel.LOW,
                        debt_minutes=10
                    ))

        return issues

    def _is_function_used(self, func_name: str, tree: ast.AST) -> bool:
        """检查函数是否被使用"""
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name) and node.func.id == func_name:
                    return True
                if isinstance(node.func, ast.Attribute) and node.func.attr == func_name:
                    return True
        return True

    def _calculate_nesting_depth(self, node: ast.AST, current_depth: int = 0) -> int:
        max_depth = current_depth
        for child in ast.iter_child_nodes(node):
            if isinstance(child, (ast.If, ast.For, ast.While, ast.With, ast.Try)):
                child_depth = self._calculate_nesting_depth(child, current_depth + 1)
                max_depth = max(max_depth, child_depth)
            else:
                child_depth = self._calculate_nesting_depth(child, current_depth)
                max_depth = max(max_depth, child_depth)
        return max_depth


class SecurityScanner:
    """安全漏洞扫描器 - 增强版"""

    SECRET_PATTERNS = [
        (r'password\s*=\s*["\'][^"\']+["\']', "硬编码密码"),
        (r'api_key\s*=\s*["\'][^"\']+["\']', "硬编码API密钥"),
        (r'secret\s*=\s*["\'][^"\']+["\']', "硬编码密钥"),
        (r'token\s*=\s*["\'][^"\']+["\']', "硬编码令牌"),
        (r'private_key\s*=\s*["\'][^"\']+["\']', "硬编码私钥"),
        (r'aws_access_key\s*=\s*["\'][^"\']+["\']', "硬编码AWS密钥"),
    ]

    VULNERABILITY_PATTERNS = [
        (r'eval\s*\([^)]*\+', "动态代码执行风险"),
        (r'exec\s*\([^)]*\+', "动态代码执行风险"),
        (r'os\.system\s*\([^)]*\+', "命令注入风险"),
        (r'subprocess\..*\+.*shell\s*=\s*True', "命令注入风险"),
        (r'yaml\.load\s*\([^)]*\)(?!.*Loader)', "YAML反序列化风险"),
        (r'pickle\.loads?\s*\(', "Pickle反序列化风险"),
    ]

    def scan(self, source: str, file_path: Path) -> List[Issue]:
        """扫描安全问题"""
        issues = []
        lines = source.split('\n')

        for i, line in enumerate(lines, 1):
            for pattern, message in self.SECRET_PATTERNS:
                if re.search(pattern, line, re.IGNORECASE):
                    issues.append(Issue(
                        file=str(file_path),
                        line=i,
                        column=0,
                        severity=Severity.CRITICAL,
                        issue_type=IssueType.SECURITY,
                        message=f"安全问题: {message}",
                        rule_id="SECURITY_HARDCODED_SECRET",
                        suggestion="使用环境变量或配置文件存储敏感信息",
                        risk_level=RiskLevel.CRITICAL,
                        debt_minutes=30
                    ))

            for pattern, message in self.VULNERABILITY_PATTERNS:
                if re.search(pattern, line, re.IGNORECASE):
                    issues.append(Issue(
                        file=str(file_path),
                        line=i,
                        column=0,
                        severity=Severity.ERROR,
                        issue_type=IssueType.SECURITY,
                        message=f"安全漏洞: {message}",
                        rule_id="SECURITY_VULNERABILITY",
                        suggestion="修复潜在的安全漏洞",
                        risk_level=RiskLevel.HIGH,
                        debt_minutes=45
                    ))

        issues.extend(self._check_sql_injection(source, file_path))
        issues.extend(self._check_xss_vulnerabilities(source, file_path))

        return issues

    def _check_sql_injection(self, source: str, file_path: Path) -> List[Issue]:
        issues = []

        try:
            tree = ast.parse(source)
            for node in ast.walk(tree):
                if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
                    if isinstance(node.left, ast.Constant) and isinstance(node.left.value, str):
                        if 'SELECT' in node.left.value.upper() or 'INSERT' in node.left.value.upper():
                            issues.append(Issue(
                                file=str(file_path),
                                line=node.lineno,
                                column=node.col_offset,
                                severity=Severity.WARNING,
                                issue_type=IssueType.SECURITY,
                                message="可能的SQL注入风险：字符串拼接构建SQL",
                                rule_id="SECURITY_SQL_INJECTION",
                                suggestion="使用参数化查询替代字符串拼接",
                                risk_level=RiskLevel.HIGH,
                                debt_minutes=30
                            ))
        except Exception:
            pass

        return issues

    def _check_xss_vulnerabilities(self, source: str, file_path: Path) -> List[Issue]:
        """检测XSS漏洞 - 新增"""
        issues = []
        lines = source.split('\n')

        xss_patterns = [
            (r'render_template_string\s*\([^)]*\+', "模板注入风险"),
            (r'Markup\s*\([^)]*\+', "不安全的HTML渲染"),
            (r'\.innerHTML\s*=', "DOM XSS风险"),
        ]

        for i, line in enumerate(lines, 1):
            for pattern, message in xss_patterns:
                if re.search(pattern, line, re.IGNORECASE):
                    issues.append(Issue(
                        file=str(file_path),
                        line=i,
                        column=0,
                        severity=Severity.WARNING,
                        issue_type=IssueType.SECURITY,
                        message=f"XSS风险: {message}",
                        rule_id="SECURITY_XSS",
                        suggestion="对用户输入进行适当的转义处理",
                        risk_level=RiskLevel.HIGH,
                        debt_minutes=30
                    ))

        return issues


class AutoFixer:
    """自动修复器（增强版）"""

    def __init__(self, logger):
        self.logger = logger
        self.fixers: Dict[str, Callable] = {
            "MISSING_DOCSTRING": self._fix_missing_docstring,
            "INVALID_CLASS_NAME": self._fix_class_name,
            "CODE_SMELL_MAGIC_NUMBER": self._fix_magic_number,
            "STYLE_LINE_LENGTH": self._fix_line_length,
            "MISSING_NEWLINE": self._fix_missing_newline,
            "TRAILING_WHITESPACE": self._fix_trailing_whitespace,
            "UNUSED_IMPORT": self._fix_unused_import,
            "MISSING_TYPE_HINT": self._fix_missing_type_hint,
            "INCONSISTENT_QUOTES": self._fix_inconsistent_quotes,
            "MISSING_FINAL_NEWLINE": self._fix_missing_final_newline,
        }
        self.fix_history: List[Dict[str, Any]] = []

    def can_fix(self, issue: Issue) -> bool:
        """判断是否可以自动修复"""
        return issue.rule_id in self.fixers

    def apply_fix(self, file_path: Path, issue: Issue, content: str) -> Tuple[str, bool]:
        """应用修复"""
        if issue.rule_id not in self.fixers:
            return content, False

        try:
            fixer = self.fixers[issue.rule_id]
            new_content, success = fixer(file_path, issue, content)
            if success:
                self.fix_history.append({
                    "file": str(file_path),
                    "rule_id": issue.rule_id,
                    "line": issue.line,
                    "timestamp": datetime.now().isoformat()
                })
            return new_content, success
        except Exception as e:
            self.logger.warning(f"自动修复失败: {e}")
            return content, False

    def _fix_missing_docstring(self, file_path: Path, issue: Issue, content: str) -> Tuple[str, bool]:
        """修复缺失的文档字符串"""
        lines = content.split('\n')
        line_idx = issue.line - 1

        if line_idx >= len(lines):
            return content, False

        line = lines[line_idx]
        indent = len(line) - len(line.lstrip())
        
        if 'def ' in line:
            func_name = re.search(r'def\s+(\w+)', line)
            if func_name:
                name = func_name.group(1)
                docstring = ' ' * indent + f'"""{name} 函数"""'
            else:
                docstring = ' ' * indent + '"""TODO: 添加文档字符串"""'
        elif 'class ' in line:
            class_name = re.search(r'class\s+(\w+)', line)
            if class_name:
                name = class_name.group(1)
                docstring = ' ' * indent + f'"""{name} 类"""'
            else:
                docstring = ' ' * indent + '"""TODO: 添加文档字符串"""'
        else:
            docstring = ' ' * indent + '"""TODO: 添加文档字符串"""'

        lines.insert(line_idx + 1, docstring)
        return '\n'.join(lines), True

    def _fix_class_name(self, file_path: Path, issue: Issue, content: str) -> Tuple[str, bool]:
        """修复类名"""
        try:
            tree = ast.parse(content)
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef) and node.lineno == issue.line:
                    old_name = node.name
                    new_name = ''.join(word.capitalize() for word in old_name.split('_'))
                    content = content.replace(f'class {old_name}', f'class {new_name}')
                    return content, True
        except Exception:
            pass
        return content, False

    def _fix_magic_number(self, file_path: Path, issue: Issue, content: str) -> Tuple[str, bool]:
        """修复魔法数字"""
        lines = content.split('\n')
        line_idx = issue.line - 1

        if line_idx >= len(lines):
            return content, False

        match = re.search(r'\b(\d{2,})\b', lines[line_idx])
        if match:
            number = match.group(1)
            constant_name = f"MAGIC_NUMBER_{number}"
            lines[line_idx] = lines[line_idx].replace(number, constant_name)
            lines.insert(0, f"{constant_name} = {number}")
            return '\n'.join(lines), True

        return content, False

    def _fix_line_length(self, file_path: Path, issue: Issue, content: str) -> Tuple[str, bool]:
        """修复行长度"""
        lines = content.split('\n')
        line_idx = issue.line - 1

        if line_idx >= len(lines):
            return content, False

        line = lines[line_idx]
        if len(line) > 100:
            indent = len(line) - len(line.lstrip())
            break_chars = [',', '(', ' ', ')']

            for char in break_chars:
                last_pos = line.rfind(char, 0, 100)
                if last_pos > 50:
                    lines[line_idx] = line[:last_pos + 1]
                    lines.insert(line_idx + 1, ' ' * (indent + 4) + line[last_pos + 1:].strip())
                    return '\n'.join(lines), True

        return content, False

    def _fix_missing_newline(self, file_path: Path, issue: Issue, content: str) -> Tuple[str, bool]:
        """修复缺少空行"""
        lines = content.split('\n')
        line_idx = issue.line - 1

        if line_idx >= len(lines) - 1:
            return content, False

        if lines[line_idx].strip() and lines[line_idx + 1].strip():
            indent = len(lines[line_idx]) - len(lines[line_idx].lstrip())
            lines.insert(line_idx + 1, '')
            return '\n'.join(lines), True

        return content, False

    def _fix_trailing_whitespace(self, file_path: Path, issue: Issue, content: str) -> Tuple[str, bool]:
        """修复行尾空白"""
        lines = content.split('\n')
        line_idx = issue.line - 1

        if line_idx >= len(lines):
            return content, False

        original = lines[line_idx]
        lines[line_idx] = lines[line_idx].rstrip()
        
        if original != lines[line_idx]:
            return '\n'.join(lines), True

        return content, False

    def _fix_unused_import(self, file_path: Path, issue: Issue, content: str) -> Tuple[str, bool]:
        """修复未使用的导入"""
        lines = content.split('\n')
        line_idx = issue.line - 1

        if line_idx >= len(lines):
            return content, False

        line = lines[line_idx].strip()
        if line.startswith('import ') or line.startswith('from '):
            del lines[line_idx]
            return '\n'.join(lines), True

        return content, False

    def _fix_missing_type_hint(self, file_path: Path, issue: Issue, content: str) -> Tuple[str, bool]:
        """修复缺少类型提示"""
        lines = content.split('\n')
        line_idx = issue.line - 1

        if line_idx >= len(lines):
            return content, False

        line = lines[line_idx]
        
        def_match = re.match(r'(\s*def\s+\w+)\s*\(([^)]*)\)\s*:', line)
        if def_match:
            prefix = def_match.group(1)
            params = def_match.group(2)
            
            if '-> ' not in line:
                new_line = line.replace(':', ' -> Any:', 1)
                lines[line_idx] = new_line
                return '\n'.join(lines), True

        return content, False

    def _fix_inconsistent_quotes(self, file_path: Path, issue: Issue, content: str) -> Tuple[str, bool]:
        """修复引号不一致"""
        lines = content.split('\n')
        line_idx = issue.line - 1

        if line_idx >= len(lines):
            return content, False

        line = lines[line_idx]
        double_count = line.count('"') - line.count('\\"')
        single_count = line.count("'") - line.count("\\'")

        if double_count > single_count and "'" in line:
            line = re.sub(r"(?<!\\)'([^']*)'", r'"\1"', line)
            lines[line_idx] = line
            return '\n'.join(lines), True
        elif single_count > double_count and '"' in line:
            line = re.sub(r'(?<!\\)"([^"]*)"', r"'\1'", line)
            lines[line_idx] = line
            return '\n'.join(lines), True

        return content, False

    def _fix_missing_final_newline(self, file_path: Path, issue: Issue, content: str) -> Tuple[str, bool]:
        """修复文件末尾缺少换行"""
        if content and not content.endswith('\n'):
            return content + '\n', True
        return content, False

    def generate_fix_preview(self, file_path: Path, issues: List[Issue], content: str) -> Dict[str, Any]:
        """生成修复预览"""
        preview = {
            "file": str(file_path),
            "fixable_count": 0,
            "unfixable_count": 0,
            "fixes": []
        }

        for issue in issues:
            if self.can_fix(issue):
                new_content, success = self.apply_fix(file_path, issue, content)
                if success:
                    preview["fixable_count"] += 1
                    preview["fixes"].append({
                        "issue": issue.to_dict(),
                        "original_line": content.split('\n')[issue.line - 1] if issue.line > 0 else "",
                        "fixed_line": new_content.split('\n')[issue.line - 1] if issue.line > 0 else ""
                    })
            else:
                preview["unfixable_count"] += 1

        return preview

    def batch_fix(self, file_path: Path, issues: List[Issue], content: str, 
                  auto_save: bool = False) -> Tuple[str, int, Dict[str, Any]]:
        """批量修复（增强版）"""
        fixed_count = 0
        current_content = content
        fix_details = []

        for issue in sorted(issues, key=lambda x: x.line, reverse=True):
            if self.can_fix(issue):
                new_content, success = self.apply_fix(file_path, issue, current_content)
                if success:
                    fix_details.append({
                        "rule_id": issue.rule_id,
                        "line": issue.line,
                        "message": issue.message
                    })
                    current_content = new_content
                    fixed_count += 1

        if auto_save and fixed_count > 0:
            try:
                file_path.write_text(current_content, encoding='utf-8')
                self.logger.info(f"已自动保存修复后的文件: {file_path}")
            except Exception as e:
                self.logger.warning(f"自动保存失败: {e}")

        return current_content, fixed_count, {"fixes": fix_details}

    def get_fix_statistics(self) -> Dict[str, Any]:
        """获取修复统计"""
        if not self.fix_history:
            return {"total_fixes": 0}

        rule_counts = defaultdict(int)
        file_counts = defaultdict(int)

        for fix in self.fix_history:
            rule_counts[fix["rule_id"]] += 1
            file_counts[fix["file"]] += 1

        return {
            "total_fixes": len(self.fix_history),
            "by_rule": dict(rule_counts),
            "by_file": dict(file_counts)
        }

    def create_fix_commit_message(self, fixes: List[Dict[str, Any]]) -> str:
        """生成修复提交消息"""
        if not fixes:
            return "style: 自动格式化代码"

        rule_counts = defaultdict(int)
        for fix in fixes:
            rule_counts[fix["rule_id"]] += 1

        lines = ["fix: 自动修复代码问题\n"]
        for rule_id, count in sorted(rule_counts.items()):
            lines.append(f"- {rule_id}: {count}处")

        return '\n'.join(lines)


class EnhancedReportGenerator:
    """增强版审查报告生成器 - 新增"""

    def __init__(self, logger):
        self.logger = logger

    def generate(
        self,
        results: List[ReviewResult],
        quality_scores: Dict[str, Any],
        output_format: str = "json",
        include_trends: bool = True
    ) -> str:
        """生成报告"""
        if output_format == "json":
            return self._generate_json_report(results, quality_scores, include_trends)
        elif output_format == "markdown":
            return self._generate_markdown_report(results, quality_scores, include_trends)
        elif output_format == "html":
            return self._generate_html_report(results, quality_scores, include_trends)
        else:
            return self._generate_text_report(results, quality_scores)

    def _generate_json_report(self, results: List[ReviewResult], quality_scores: Dict[str, Any], include_trends: bool) -> str:
        report = {
            "timestamp": datetime.now().isoformat(),
            "summary": {
                "total_files": len(results),
                "total_issues": sum(len(r.issues) for r in results),
                "quality_scores": quality_scores,
                "total_tech_debt_hours": sum(r.tech_debt.get("total_hours", 0) for r in results),
                "patterns_detected": sum(len(r.patterns) for r in results),
                "duplications_found": sum(len(r.duplications) for r in results)
            },
            "trends": self._calculate_trends(results) if include_trends else None,
            "results": [r.to_dict() for r in results]
        }
        return json.dumps(report, indent=2, ensure_ascii=False)

    def _generate_markdown_report(self, results: List[ReviewResult], quality_scores: Dict[str, Any], include_trends: bool) -> str:
        lines = [
            "# 代码审查报告 (增强版)",
            "",
            f"**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "## 📊 质量评分",
            "",
            f"| 维度 | 分数 |",
            f"|------|------|",
        ]

        dimensions = quality_scores.get("dimensions", {})
        for dim, score in dimensions.items():
            emoji = self._get_score_emoji(score)
            lines.append(f"| {dim} | {emoji} {score} |")

        lines.extend([
            "",
            f"**总分**: {quality_scores.get('overall_score', 0)}/100",
            f"**等级**: {quality_scores.get('grade', 'N/A')}",
            "",
            "## 📈 问题统计",
            "",
        ])

        severity_counts = defaultdict(int)
        type_counts = defaultdict(int)
        for result in results:
            for issue in result.issues:
                severity_counts[issue.severity.value] += 1
                type_counts[issue.issue_type.value] += 1

        lines.append("### 按严重程度")
        lines.append("")
        for severity, count in sorted(severity_counts.items()):
            emoji = self._get_severity_emoji(severity)
            lines.append(f"- {emoji} {severity}: {count}")

        lines.extend(["", "### 按类型", ""])
        for issue_type, count in sorted(type_counts.items()):
            lines.append(f"- {issue_type}: {count}")

        total_debt = sum(r.tech_debt.get("total_hours", 0) for r in results)
        lines.extend([
            "",
            "## ⏱️ 技术债务",
            "",
            f"- **总债务时间**: {total_debt:.1f} 小时",
            "",
        ])

        patterns_count = sum(len(r.patterns) for r in results)
        if patterns_count > 0:
            lines.extend([
                "## 🏗️ 检测到的设计模式",
                "",
            ])
            for result in results:
                for pattern in result.patterns:
                    lines.append(f"- {pattern['type']} in {pattern['class']} (置信度: {pattern['confidence']:.0%})")

        duplications_count = sum(len(r.duplications) for r in results)
        if duplications_count > 0:
            lines.extend([
                "",
                "## 📋 代码重复",
                "",
                f"- 发现 {duplications_count} 处代码重复",
            ])

        lines.extend([
            "",
            "## 📁 文件详情",
            "",
        ])

        for result in results[:20]:
            lines.append(f"### {result.file}")
            lines.append("")
            if result.issues:
                for issue in result.issues[:10]:
                    emoji = self._get_severity_emoji(issue.severity.value)
                    lines.append(f"- {emoji} 行 {issue.line}: {issue.message}")
                    if issue.suggestion:
                        lines.append(f"  - 💡 建议: {issue.suggestion}")
            else:
                lines.append("✅ 无问题")
            lines.append("")

        if include_trends:
            trends = self._calculate_trends(results)
            lines.extend([
                "",
                "## 📉 趋势分析",
                "",
                f"- 平均每文件问题数: {trends['avg_issues_per_file']:.1f}",
                f"- 问题密度: {trends['issue_density']:.2f} 问题/100行",
                f"- 高风险文件比例: {trends['high_risk_ratio']:.1%}",
            ])

        return "\n".join(lines)

    def _generate_html_report(self, results: List[ReviewResult], quality_scores: Dict[str, Any], include_trends: bool) -> str:
        grade_color = {
            "A+": "#28a745", "A": "#28a745", "A-": "#5cb85c",
            "B+": "#5bc0de", "B": "#5bc0de", "B-": "#f0ad4e",
            "C+": "#f0ad4e", "C": "#ff851b", "C-": "#ff851b",
            "D": "#d9534f", "F": "#d9534f"
        }.get(quality_scores.get("grade", "F"), "#6c757d")

        dimensions_html = ""
        dimensions = quality_scores.get("dimensions", {})
        for dim, score in dimensions.items():
            color = "#28a745" if score >= 80 else "#f0ad4e" if score >= 60 else "#d9534f"
            dimensions_html += f"""
            <div class="dimension">
                <span class="dim-name">{dim}</span>
                <div class="progress-bar">
                    <div class="progress" style="width: {score}%; background-color: {color};"></div>
                </div>
                <span class="dim-score">{score}</span>
            </div>
            """

        issues_html = ""
        for result in results[:20]:
            issues_html += f"""
            <div class="file">
                <h3>{result.file}</h3>
                <div class="metrics">
                    <span>问题数: {len(result.issues)}</span>
                    <span>技术债务: {result.tech_debt.get('total_hours', 0):.1f}h</span>
                </div>
                <div class="issues">
            """
            for issue in result.issues[:10]:
                issues_html += f"""
                    <div class="issue severity-{issue.severity.value}">
                        <span class="severity">[{issue.severity.value}]</span>
                        <span class="location">行 {issue.line}</span>
                        <span class="message">{issue.message}</span>
                        {f'<span class="suggestion">💡 {issue.suggestion}</span>' if issue.suggestion else ''}
                    </div>
                """
            issues_html += "</div></div>"

        html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <title>代码审查报告 (增强版)</title>
    <style>
        * {{ box-sizing: border-box; }}
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; margin: 0; padding: 20px; background: #f5f5f5; }}
        .container {{ max-width: 1200px; margin: 0 auto; }}
        .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; border-radius: 10px; margin-bottom: 20px; }}
        .header h1 {{ margin: 0 0 10px 0; }}
        .score-card {{ background: white; padding: 20px; border-radius: 10px; margin-bottom: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        .grade {{ font-size: 48px; font-weight: bold; color: {grade_color}; }}
        .overall-score {{ font-size: 36px; }}
        .dimension {{ display: flex; align-items: center; margin: 10px 0; }}
        .dim-name {{ width: 120px; }}
        .progress-bar {{ flex: 1; height: 20px; background: #e9ecef; border-radius: 10px; overflow: hidden; }}
        .progress {{ height: 100%; transition: width 0.3s; }}
        .dim-score {{ width: 50px; text-align: right; font-weight: bold; }}
        .file {{ background: white; padding: 20px; border-radius: 10px; margin-bottom: 15px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        .file h3 {{ margin: 0 0 10px 0; color: #333; }}
        .metrics {{ display: flex; gap: 20px; margin-bottom: 15px; color: #666; }}
        .issue {{ padding: 10px; margin: 5px 0; border-radius: 5px; border-left: 4px solid; }}
        .severity-critical {{ background: #f8d7da; border-color: #dc3545; }}
        .severity-error {{ background: #fff3cd; border-color: #ffc107; }}
        .severity-warning {{ background: #e2e3e5; border-color: #6c757d; }}
        .severity-info {{ background: #d1ecf1; border-color: #17a2b8; }}
        .severity {{ font-weight: bold; text-transform: uppercase; }}
        .location {{ color: #666; margin: 0 10px; }}
        .suggestion {{ display: block; margin-top: 5px; color: #666; font-style: italic; }}
        .stats {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin-bottom: 20px; }}
        .stat-card {{ background: white; padding: 20px; border-radius: 10px; text-align: center; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        .stat-value {{ font-size: 32px; font-weight: bold; color: #667eea; }}
        .stat-label {{ color: #666; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🔍 代码审查报告</h1>
            <p>生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        </div>

        <div class="stats">
            <div class="stat-card">
                <div class="stat-value">{len(results)}</div>
                <div class="stat-label">审查文件</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{sum(len(r.issues) for r in results)}</div>
                <div class="stat-label">发现问题</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{sum(r.tech_debt.get('total_hours', 0) for r in results):.1f}h</div>
                <div class="stat-label">技术债务</div>
            </div>
            <div class="stat-card">
                <div class="stat-value grade">{quality_scores.get('grade', 'N/A')}</div>
                <div class="stat-label">质量等级</div>
            </div>
        </div>

        <div class="score-card">
            <h2>📊 质量评分: <span class="overall-score">{quality_scores.get('overall_score', 0)}/100</span></h2>
            {dimensions_html}
        </div>

        <h2>📁 文件详情</h2>
        {issues_html}
    </div>
</body>
</html>"""
        return html

    def _generate_text_report(self, results: List[ReviewResult], quality_scores: Dict[str, Any]) -> str:
        lines = [
            "=" * 70,
            "代码审查报告 (增强版)",
            "=" * 70,
            f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"质量评分: {quality_scores.get('overall_score', 0)}/100",
            f"等级: {quality_scores.get('grade', 'N/A')}",
            "",
            "-" * 50,
            "维度评分:",
            "-" * 50,
        ]

        dimensions = quality_scores.get("dimensions", {})
        for dim, score in dimensions.items():
            lines.append(f"  {dim}: {score}")

        lines.extend([
            "",
            "-" * 50,
            "问题统计:",
            "-" * 50,
        ])

        severity_counts = defaultdict(int)
        for result in results:
            for issue in result.issues:
                severity_counts[issue.severity.value] += 1

        for severity, count in sorted(severity_counts.items()):
            lines.append(f"  {severity}: {count}")

        total_debt = sum(r.tech_debt.get("total_hours", 0) for r in results)
        lines.extend([
            "",
            "-" * 50,
            f"技术债务: {total_debt:.1f} 小时",
            "-" * 50,
        ])

        lines.append("")
        lines.append("-" * 50)
        lines.append("文件详情:")
        lines.append("-" * 50)

        for result in results[:10]:
            lines.append(f"\n{result.file}:")
            if result.issues:
                for issue in result.issues[:5]:
                    lines.append(f"  [{issue.severity.value}] 行 {issue.line}: {issue.message}")
            else:
                lines.append("  无问题")

        lines.append("\n" + "=" * 70)
        return "\n".join(lines)

    def _calculate_trends(self, results: List[ReviewResult]) -> Dict[str, Any]:
        """计算趋势数据"""
        if not results:
            return {"avg_issues_per_file": 0, "issue_density": 0, "high_risk_ratio": 0}

        total_issues = sum(len(r.issues) for r in results)
        total_lines = sum(r.metrics.get("total_lines", 0) for r in results)
        high_risk_files = sum(1 for r in results if r.risk_assessment.get("overall_risk") in ["high", "critical"])

        return {
            "avg_issues_per_file": total_issues / len(results),
            "issue_density": (total_issues / total_lines * 100) if total_lines > 0 else 0,
            "high_risk_ratio": high_risk_files / len(results)
        }

    def _get_score_emoji(self, score: float) -> str:
        if score >= 80:
            return "🟢"
        elif score >= 60:
            return "🟡"
        else:
            return "🔴"

    def _get_severity_emoji(self, severity: str) -> str:
        emojis = {
            "critical": "🔴",
            "error": "🟠",
            "warning": "🟡",
            "info": "🔵"
        }
        return emojis.get(severity, "⚪")


class PythonCodeReviewer:
    """Python代码审查器 - 增强版"""

    def __init__(self, rules: dict, risk_analyzer: RiskAnalyzer, rule_selector: RuleSelector,
                 dependency_analyzer: DependencyAnalyzer, pattern_detector: PatternDetector,
                 duplication_detector: CodeDuplicationDetector, tech_debt_estimator: TechnicalDebtEstimator):
        self.rules = rules
        self.risk_analyzer = risk_analyzer
        self.rule_selector = rule_selector
        self.dependency_analyzer = dependency_analyzer
        self.pattern_detector = pattern_detector
        self.duplication_detector = duplication_detector
        self.tech_debt_estimator = tech_debt_estimator
        self.code_smell_detector = CodeSmellDetector()
        self.security_scanner = SecurityScanner()

    def review(self, file_path: Path) -> ReviewResult:
        issues = []
        metrics = {
            "total_lines": 0,
            "code_lines": 0,
            "blank_lines": 0,
            "comment_lines": 0,
            "functions": 0,
            "classes": 0,
            "complexity": 0,
            "documented_functions": 0
        }

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                source = f.read()
                lines = source.split('\n')

            metrics["total_lines"] = len(lines)

            for line in lines:
                stripped = line.strip()
                if not stripped:
                    metrics["blank_lines"] += 1
                elif stripped.startswith('#'):
                    metrics["comment_lines"] += 1
                else:
                    metrics["code_lines"] += 1

            try:
                tree = ast.parse(source)
                self._analyze_ast(tree, file_path, lines, metrics, issues)
            except SyntaxError as e:
                issues.append(Issue(
                    file=str(file_path),
                    line=e.lineno or 1,
                    column=e.offset or 0,
                    severity=Severity.ERROR,
                    issue_type=IssueType.MAINTAINABILITY,
                    message=f"语法错误: {e.msg}",
                    rule_id="SYNTAX_ERROR",
                    risk_level=RiskLevel.HIGH,
                    debt_minutes=15
                ))

            risk_assessment = self.risk_analyzer.assess_file_risk(file_path, source, tree if 'tree' in dir() else ast.parse(""))

            selected_rules = self.rule_selector.select_rules(file_path, source, risk_assessment)

            issues.extend(self.code_smell_detector.detect(tree, source, file_path))
            issues.extend(self.security_scanner.scan(source, file_path))

            dependencies = self.dependency_analyzer.an_file(file_path, tree)
            issues.extend(self.dependency_analyzer.get_dependency_issues(file_path))

            patterns = self.pattern_detector.detect_patterns(tree, file_path)

            duplications = self.duplication_detector.analyze_file(file_path, source)
            issues.extend(self.duplication_detector.get_duplication_issues(duplications, file_path))

            tech_debt = self.tech_debt_estimator.estimate_file_debt(file_path, source, issues)
            issues.extend(self.tech_debt_estimator.get_debt_issues(file_path, tech_debt))

            risk_dict = {
                "overall_risk": risk_assessment.overall_risk.value,
                "risk_score": risk_assessment.risk_score,
                "risk_factors": risk_assessment.risk_factors,
                "recommendations": risk_assessment.recommendations,
                "confidence": risk_assessment.confidence,
                "rules_applied": len(selected_rules)
            }

        except Exception:
            risk_dict = {}
            dependencies = {}
            patterns = []
            duplications = []
            tech_debt = {}

        return ReviewResult(
            file=str(file_path),
            issues=issues,
            metrics=metrics,
            risk_assessment=risk_dict,
            dependencies=dependencies,
            patterns=patterns,
            duplications=duplications,
            tech_debt=tech_debt
        )

    def _analyze_ast(self, tree: ast.AST, file_path: Path, lines: List[str], metrics: Dict, issues: List[Issue]):
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                metrics["functions"] += 1
                self._check_function(node, file_path, lines, metrics, issues)
            elif isinstance(node, ast.ClassDef):
                metrics["classes"] += 1
                self._check_class(node, file_path, lines, issues)

    def _check_function(self, node: ast.FunctionDef, file_path: Path, lines: List[str], metrics: Dict, issues: List[Issue]):
        if hasattr(node, 'end_lineno') and node.end_lineno:
            func_length = node.end_lineno - node.lineno
            max_length = self.rules.get("max_function_length", 50)
            if func_length > max_length:
                issues.append(Issue(
                    file=str(file_path),
                    line=node.lineno,
                    column=node.col_offset,
                    severity=Severity.WARNING,
                    issue_type=IssueType.COMPLEXITY,
                    message=f"函数 '{node.name}' 过长 ({func_length} 行)",
                    rule_id="FUNCTION_TOO_LONG",
                    suggestion="考虑将函数拆分为多个小函数",
                    risk_level=RiskLevel.MEDIUM,
                    debt_minutes=func_length - max_length
                ))

        args_count = len(node.args.args) + len(node.args.kwonlyargs)
        max_args = self.rules.get("max_arguments", 5)
        if args_count > max_args:
            issues.append(Issue(
                file=str(file_path),
                line=node.lineno,
                column=node.col_offset,
                severity=Severity.WARNING,
                issue_type=IssueType.COMPLEXITY,
                message=f"函数 '{node.name}' 参数过多 ({args_count} 个)",
                rule_id="TOO_MANY_ARGUMENTS",
                suggestion="考虑使用配置对象或数据类传递参数",
                risk_level=RiskLevel.LOW,
                debt_minutes=15
            ))

        if self.rules.get("required_docstrings", True):
            if ast.get_docstring(node):
                metrics["documented_functions"] += 1
            else:
                issues.append(Issue(
                    file=str(file_path),
                    line=node.lineno,
                    column=node.col_offset,
                    severity=Severity.INFO,
                    issue_type=IssueType.MAINTAINABILITY,
                    message=f"函数 '{node.name}' 缺少文档字符串",
                    rule_id="MISSING_DOCSTRING",
                    suggestion="为函数添加文档字符串",
                    auto_fixable=True,
                    risk_level=RiskLevel.LOW,
                    debt_minutes=5
                ))

        complexity = self._calculate_complexity(node)
        metrics["complexity"] += complexity
        max_complexity = self.rules.get("max_complexity", 10)
        if complexity > max_complexity:
            issues.append(Issue(
                file=str(file_path),
                line=node.lineno,
                column=node.col_offset,
                severity=Severity.WARNING,
                issue_type=IssueType.COMPLEXITY,
                message=f"函数 '{node.name}' 复杂度过高 (复杂度: {complexity})",
                rule_id="HIGH_COMPLEXITY",
                suggestion="考虑简化条件逻辑",
                risk_level=RiskLevel.MEDIUM,
                debt_minutes=(complexity - max_complexity) * 5
            ))

    def _check_class(self, node: ast.ClassDef, file_path: Path, lines: List[str], issues: List[Issue]):
        naming = self.rules.get("naming_conventions", {}).get("class", "PascalCase")
        if naming == "PascalCase" and not re.match(r'^[A-Z][a-zA-Z0-9]*$', node.name):
            issues.append(Issue(
                file=str(file_path),
                line=node.lineno,
                column=node.col_offset,
                severity=Severity.WARNING,
                issue_type=IssueType.STYLE,
                message=f"类名 '{node.name}' 不符合 PascalCase 命名规范",
                rule_id="INVALID_CLASS_NAME",
                suggestion="使用大写字母开头的驼峰命名法",
                auto_fixable=True,
                risk_level=RiskLevel.LOW,
                debt_minutes=5
            ))

    def _calculate_complexity(self, node: ast.AST) -> int:
        complexity = 1
        for child in ast.walk(node):
            if isinstance(child, (ast.If, ast.While, ast.For, ast.ExceptHandler)):
                complexity += 1
            elif isinstance(child, ast.BoolOp):
                complexity += len(child.values) - 1
        return complexity


class TypeScriptCodeReviewer:
    """TypeScript代码审查器 - 增强版"""

    def __init__(self, rules: dict, risk_analyzer: RiskAnalyzer,
                 duplication_detector: CodeDuplicationDetector, tech_debt_estimator: TechnicalDebtEstimator):
        self.rules = rules
        self.risk_analyzer = risk_analyzer
        self.duplication_detector = duplication_detector
        self.tech_debt_estimator = tech_debt_estimator

    def review(self, file_path: Path) -> ReviewResult:
        issues = []
        metrics = {
            "total_lines": 0,
            "code_lines": 0,
            "blank_lines": 0,
            "comment_lines": 0,
            "functions": 0,
            "classes": 0
        }

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()

            metrics["total_lines"] = len(lines)

            in_multiline_comment = False
            for line in lines:
                stripped = line.strip()
                if not stripped:
                    metrics["blank_lines"] += 1
                    continue
                if '/*' in stripped:
                    in_multiline_comment = True
                if in_multiline_comment:
                    metrics["comment_lines"] += 1
                    if '*/' in stripped:
                        in_multiline_comment = False
                    continue
                if stripped.startswith('//') or stripped.startswith('*'):
                    metrics["comment_lines"] += 1
                else:
                    metrics["code_lines"] += 1

            content = ''.join(lines)
            self._check_content(content, file_path, metrics, issues)

            risk_assessment = self.risk_analyzer.assess_file_risk(file_path, content, ast.parse(""))

            duplications = self.duplication_detector.analyze_file(file_path, content)

            tech_debt = self.tech_debt_estimator.estimate_file_debt(file_path, content, issues)

            risk_dict = {
                "overall_risk": risk_assessment.overall_risk.value,
                "risk_score": risk_assessment.risk_score,
                "risk_factors": risk_assessment.risk_factors,
                "recommendations": risk_assessment.recommendations
            }

        except Exception:
            risk_dict = {}
            duplications = []
            tech_debt = {}

        return ReviewResult(
            file=str(file_path),
            issues=issues,
            metrics=metrics,
            risk_assessment=risk_dict,
            duplications=duplications,
            tech_debt=tech_debt
        )

    def _check_content(self, content: str, file_path: Path, metrics: Dict, issues: List[Issue]):
        function_pattern = r'(function\s+\w+|const\s+\w+\s*=\s*(?:async\s*)?\()'
        matches = list(re.finditer(function_pattern, content))
        metrics["functions"] = len(matches)

        class_pattern = r'(?:export\s+)?(?:abstract\s+)?class\s+(\w+)'
        class_matches = list(re.finditer(class_pattern, content))
        metrics["classes"] = len(class_matches)

        for match in class_matches:
            class_name = match.group(1)
            naming = self.rules.get("naming_conventions", {}).get("class", "PascalCase")
            if naming == "PascalCase" and not re.match(r'^[A-Z][a-zA-Z0-9]*$', class_name):
                line_num = content[:match.start()].count('\n') + 1
                issues.append(Issue(
                    file=str(file_path),
                    line=line_num,
                    column=match.start(),
                    severity=Severity.WARNING,
                    issue_type=IssueType.STYLE,
                    message=f"类名 '{class_name}' 不符合 PascalCase 命名规范",
                    rule_id="INVALID_CLASS_NAME",
                    suggestion="使用大写字母开头的驼峰命名法",
                    auto_fixable=True,
                    risk_level=RiskLevel.LOW,
                    debt_minutes=5
                ))

        any_pattern = r':\s*any\b'
        any_matches = list(re.finditer(any_pattern, content))
        for match in any_matches:
            line_num = content[:match.start()].count('\n') + 1
            issues.append(Issue(
                file=str(file_path),
                line=line_num,
                column=match.start(),
                severity=Severity.WARNING,
                issue_type=IssueType.BEST_PRACTICE,
                message="使用了 'any' 类型，可能失去类型检查的好处",
                rule_id="TS_ANY_TYPE",
                suggestion="使用更具体的类型定义",
                risk_level=RiskLevel.LOW,
                debt_minutes=10
            ))


class CodeReviewAutomation(ScriptBase):
    """代码审查自动化器主类 - 增强版"""

    def __init__(self):
        super().__init__(
            name="code_review_automation",
            version="3.0.0",
            description="代码审查自动化器 (增强版) - 支持风险分析、依赖分析、模式检测、重复检测、技术债务评估和自动修复",
            author="Sanliu"
        )
        self._setup_arguments()
        self.results: List[ReviewResult] = []
        self.quality_scorer = CodeQualityScorer()
        self.risk_analyzer: Optional[RiskAnalyzer] = None
        self.rule_selector: Optional[RuleSelector] = None
        self.report_generator: Optional[EnhancedReportGenerator] = None
        self.dependency_analyzer: Optional[DependencyAnalyzer] = None
        self.pattern_detector: Optional[PatternDetector] = None
        self.duplication_detector: Optional[CodeDuplicationDetector] = None
        self.tech_debt_estimator: Optional[TechnicalDebtEstimator] = None
        self.auto_fixer: Optional[AutoFixer] = None

    def _setup_arguments(self):
        self._command_parser.add_argument(
            '--target',
            type=str,
            default='./backend/app',
            help='要审查的代码目录'
        )
        self._command_parser.add_argument(
            '--output',
            type=str,
            default=str(get_path_config().REPORTS_DIR),
            help='报告输出目录'
        )
        self._command_parser.add_argument(
            '--rules',
            type=str,
            help='自定义规则文件 (JSON 格式)'
        )
        self._command_parser.add_argument(
            '--format',
            type=str,
            choices=['json', 'markdown', 'html', 'text'],
            default='json',
            help='报告格式'
        )
        self._command_parser.add_argument(
            '--max-line-length',
            type=int,
            default=100,
            help='最大行长度'
        )
        self._command_parser.add_argument(
            '--max-complexity',
            type=int,
            default=10,
            help='最大复杂度'
        )
        self._command_parser.add_argument(
            '--max-function-length',
            type=int,
            default=50,
            help='最大函数长度'
        )
        self._command_parser.add_argument(
            '--include-tests',
            action='store_true',
            help='包含测试文件'
        )
        self._command_parser.add_argument(
            '--risk-threshold',
            type=str,
            choices=['low', 'medium', 'high', 'critical'],
            default='low',
            help='风险阈值，低于此级别的文件将被跳过'
        )
        self._command_parser.add_argument(
            '--auto-fix',
            action='store_true',
            help='自动修复可修复的问题'
        )
        self._command_parser.add_argument(
            '--fix-preview',
            action='store_true',
            help='生成修复预览而不实际修改文件'
        )
        self._command_parser.add_argument(
            '--include-trends',
            action='store_true',
            default=True,
            help='在报告中包含趋势分析'
        )

    def initialize(self, config: Dict[str, Any]) -> None:
        super().initialize(config)
        self.risk_analyzer = RiskAnalyzer(self._logger)
        self.rule_selector = RuleSelector(self._logger)
        self.report_generator = EnhancedReportGenerator(self._logger)
        self.dependency_analyzer = DependencyAnalyzer(self._logger)
        self.pattern_detector = PatternDetector(self._logger)
        self.duplication_detector = CodeDuplicationDetector(self._logger)
        self.tech_debt_estimator = TechnicalDebtEstimator(self._logger)
        self.auto_fixer = AutoFixer(self._logger)

    def validate_inputs(self, *args, **kwargs) -> bool:
        target = kwargs.get('target', './backend/app')
        target_path = Path(target)
        if not target_path.exists():
            self._logger.error(f"目标目录不存在: {target}")
            return False
        return True

    def run(self, *args, **kwargs) -> Any:
        target = kwargs.get('target', './backend/app')
        output = kwargs.get('output', str(get_path_config().REPORTS_DIR))
        rules_file = kwargs.get('rules')
        output_format = kwargs.get('format', 'json')
        max_line_length = kwargs.get('max_line_length', 100)
        max_complexity = kwargs.get('max_complexity', 10)
        max_function_length = kwargs.get('max_function_length', 50)
        include_tests = kwargs.get('include_tests', False)
        risk_threshold = kwargs.get('risk_threshold', 'low')
        auto_fix = kwargs.get('auto_fix', False)
        fix_preview = kwargs.get('fix_preview', False)
        include_trends = kwargs.get('include_trends', True)

        target_path = Path(target)
        output_path = Path(output)

        self._logger.info(f"开始代码审查 (增强版) - 目标: {target}")
        self._report.add_section("配置信息", {
            "target": target,
            "output": output,
            "format": output_format,
            "max_complexity": max_complexity,
            "risk_threshold": risk_threshold,
            "auto_fix": auto_fix
        })

        rules = self._load_rules(rules_file)
        rules.update({
            "max_line_length": max_line_length,
            "max_complexity": max_complexity,
            "max_function_length": max_function_length
        })

        files_to_review = self._collect_files(target_path, include_tests)
        self._logger.info(f"找到 {len(files_to_review)} 个文件需要审查")

        risk_threshold_level = RiskLevel(risk_threshold)

        for file_path in files_to_review:
            result = self._review_file(file_path, rules)
            if result:
                if self._should_include_result(result, risk_threshold_level):
                    self.results.append(result)

        if auto_fix or fix_preview:
            self._process_auto_fixes(auto_fix, fix_preview)

        total_issues = sum(len(r.issues) for r in self.results)
        issues_by_severity = {s.value: 0 for s in Severity}
        issues_by_type = {t.value: 0 for t in IssueType}
        risk_distribution = {r.value: 0 for r in RiskLevel}

        for result in self.results:
            for issue in result.issues:
                issues_by_severity[issue.severity.value] += 1
                issues_by_type[issue.issue_type.value] += 1
                risk_distribution[issue.risk_level.value] += 1

        quality_scores = self.quality_scorer.calculate_scores(self.results)

        overall_risk = self._calculate_overall_risk()

        circular_deps = self.dependency_analyzer.detect_circular_dependencies()
        coupling_metrics = self.dependency_analyzer.calculate_coupling_metrics()

        total_tech_debt = sum(r.tech_debt.get("total_hours", 0) for r in self.results)
        total_patterns = sum(len(r.patterns) for r in self.results)
        total_duplications = sum(len(r.duplications) for r in self.results)

        result_data = {
            "total_files": len(self.results),
            "total_issues": total_issues,
            "issues_by_severity": issues_by_severity,
            "issues_by_type": issues_by_type,
            "risk_distribution": risk_distribution,
            "overall_risk": overall_risk.value,
            "quality_scores": quality_scores,
            "tech_debt_hours": total_tech_debt,
            "patterns_detected": total_patterns,
            "duplications_found": total_duplications,
            "circular_dependencies": len(circular_deps),
            "results": [r.to_dict() for r in self.results]
        }

        self._report.add_section("审查结果", {
            "total_files": len(self.results),
            "total_issues": total_issues,
            "quality_score": quality_scores["overall_score"],
            "grade": quality_scores["grade"],
            "overall_risk": overall_risk.value,
            "tech_debt_hours": total_tech_debt
        })

        self._report.add_section("增强分析", {
            "patterns_detected": total_patterns,
            "duplications_found": total_duplications,
            "circular_dependencies": len(circular_deps)
        })

        report_content = self.report_generator.generate(self.results, quality_scores, output_format, include_trends)
        output_path.mkdir(parents=True, exist_ok=True)
        report_file = output_path / f"review_report.{output_format}"
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report_content)
        self._logger.info(f"报告已保存: {report_file}")

        return result_data

    def _process_auto_fixes(self, auto_fix: bool, fix_preview: bool):
        """处理自动修复"""
        fix_summary = {
            "files_processed": 0,
            "issues_fixable": 0,
            "issues_fixed": 0
        }

        for result in self.results:
            fixable_issues = [i for i in result.issues if self.auto_fixer.can_fix(i)]
            if not fixable_issues:
                continue

            fix_summary["files_processed"] += 1
            fix_summary["issues_fixable"] += len(fixable_issues)

            file_path = Path(result.file)
            if not file_path.exists():
                continue

            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()

                if fix_preview:
                    preview = self.auto_fixer.generate_fix_preview(file_path, fixable_issues, content)
                    self._report.add_section(f"修复预览: {result.file}", preview)
                elif auto_fix:
                    new_content, fixed_count = self.auto_fixer.batch_fix(file_path, fixable_issues, content)
                    if fixed_count > 0:
                        with open(file_path, 'w', encoding='utf-8') as f:
                            f.write(new_content)
                        fix_summary["issues_fixed"] += fixed_count
                        self._logger.info(f"已修复 {result.file} 中的 {fixed_count} 个问题")
            except Exception as e:
                self._logger.warning(f"处理文件 {result.file} 时出错: {e}")

        self._report.add_section("自动修复摘要", fix_summary)

    def _should_include_result(self, result: ReviewResult, threshold: RiskLevel) -> bool:
        """判断是否应包含结果"""
        risk_levels = {
            RiskLevel.LOW: 0,
            RiskLevel.MEDIUM: 1,
            RiskLevel.HIGH: 2,
            RiskLevel.CRITICAL: 3
        }

        result_risk = result.risk_assessment.get("overall_risk", "low")
        result_level = RiskLevel(result_risk)

        return risk_levels.get(result_level, 0) >= risk_levels.get(threshold, 0)

    def _calculate_overall_risk(self) -> RiskLevel:
        """计算整体风险"""
        if not self.results:
            return RiskLevel.LOW

        max_risk = RiskLevel.LOW
        risk_weights = {
            RiskLevel.LOW: 0,
            RiskLevel.MEDIUM: 1,
            RiskLevel.HIGH: 2,
            RiskLevel.CRITICAL: 3
        }

        for result in self.results:
            result_risk = result.risk_assessment.get("overall_risk", "low")
            level = RiskLevel(result_risk)
            if risk_weights.get(level, 0) > risk_weights.get(max_risk, 0):
                max_risk = level

        critical_count = sum(
            1 for r in self.results
            for i in r.issues
            if i.risk_level == RiskLevel.CRITICAL
        )

        if critical_count > 3:
            return RiskLevel.CRITICAL

        return max_risk

    def _load_rules(self, rules_file: Optional[str]) -> dict:
        default_rules = {
            "max_line_length": 100,
            "max_function_length": 50,
            "max_class_length": 300,
            "max_complexity": 10,
            "max_arguments": 5,
            "required_docstrings": True,
            "naming_conventions": {
                "module": "snake_case",
                "class": "PascalCase",
                "function": "snake_case",
                "variable": "snake_case",
                "constant": "UPPER_CASE"
            }
        }

        if rules_file:
            try:
                with open(rules_file, 'r', encoding='utf-8') as f:
                    custom_rules = json.load(f)
                    default_rules.update(custom_rules)
            except Exception:
                pass

        return default_rules

    def _collect_files(self, target_dir: Path, include_tests: bool) -> List[Path]:
        files = []

        for ext in ['*.py', '*.ts', '*.tsx', '*.js', '*.jsx']:
            files.extend(target_dir.rglob(ext))

        if not include_tests:
            files = [f for f in files if 'test' not in f.name.lower() and 'spec' not in f.name.lower()]

        return sorted(files)

    def _review_file(self, file_path: Path, rules: dict) -> Optional[ReviewResult]:
        try:
            if file_path.suffix == '.py':
                reviewer = PythonCodeReviewer(
                    rules, self.risk_analyzer, self.rule_selector,
                    self.dependency_analyzer, self.pattern_detector,
                    self.duplication_detector, self.tech_debt_estimator
                )
            elif file_path.suffix in ['.ts', '.tsx', '.js', '.jsx']:
                reviewer = TypeScriptCodeReviewer(
                    rules, self.risk_analyzer,
                    self.duplication_detector, self.tech_debt_estimator
                )
            else:
                return None

            return reviewer.review(file_path)

        except Exception:
            return None

    def cleanup(self) -> None:
        self._logger.info("清理代码审查器资源")


def main():
    reviewer = CodeReviewAutomation()
    result = reviewer.run_from_command_line()

    print("\n" + "=" * 70)
    print("代码审查报告 (增强版)")
    print("=" * 70)
    print(f"审查文件数: {result.data.get('total_files', 0)}")
    print(f"总问题数: {result.data.get('total_issues', 0)}")

    quality = result.data.get('quality_scores', {})
    print(f"质量评分: {quality.get('overall_score', 0)}/100")
    print(f"评级: {quality.get('grade', 'N/A')}")
    print(f"整体风险: {result.data.get('overall_risk', 'N/A')}")
    print(f"技术债务: {result.data.get('tech_debt_hours', 0):.1f} 小时")

    print(f"\n检测到的设计模式: {result.data.get('patterns_detected', 0)}")
    print(f"代码重复: {result.data.get('duplications_found', 0)}")
    print(f"循环依赖: {result.data.get('circular_dependencies', 0)}")

    if result.data.get('issues_by_severity'):
        print("-" * 70)
        print("按严重程度:")
        for severity, count in result.data['issues_by_severity'].items():
            print(f"  {severity}: {count}")

    if result.data.get('risk_distribution'):
        print("-" * 70)
        print("风险分布:")
        for risk, count in result.data['risk_distribution'].items():
            print(f"  {risk}: {count}")

    print("=" * 70)

    if result.data.get('issues_by_severity', {}).get('critical', 0) > 0:
        sys.exit(2)
    elif result.data.get('issues_by_severity', {}).get('error', 0) > 0:
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    main()
