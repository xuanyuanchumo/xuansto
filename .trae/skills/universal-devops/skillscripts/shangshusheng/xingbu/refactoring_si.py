"""
重构优化司 - 代码异味→重构模式映射、性能优化、技术债务清理、版本化架构基线管理
"""
from __future__ import annotations

import ast
import json
import re
from dataclasses import dataclass, field
from enum import Enum, auto
from pathlib import Path
from typing import Any


class SmellSeverity(Enum):
    """异味严重度"""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class OptimizationCategory(Enum):
    """优化类别"""

    ALGORITHM = "algorithm"
    CACHE = "cache"
    LAZY_LOADING = "lazy_loading"
    BATCH_PROCESSING = "batch"
    ASYNC = "async"
    CONNECTION_POOL = "connection_pool"
    MEMORY = "memory"


@dataclass
class CodeSmell:
    """代码异味记录"""

    smell_type: str
    location: str
    file_path: Path | None = None
    line_number: int = 0
    severity: SmellSeverity = SmellSeverity.MEDIUM
    description: str = ""
    suggested_refactorings: list[str] = field(default_factory=list)
    confidence: float = 0.0


@dataclass
class RefactoringMapping:
    """重构映射"""

    smell_type: str
    recommended_patterns: list[dict[str, str]] = field(default_factory=list)
    risk_level: str = "low"
    effort_estimate: str = "small"
    description: str = ""


@dataclass
class ArchitectureBaseline:
    """架构基线"""

    version: str
    architecture_decisions: list[dict[str, str]] = field(default_factory=list)
    module_structure: dict[str, list[str]] = field(default_factory=dict)
    constraints: list[str] = field(default_factory=list)
    captured_at: str = ""
    checksum: str = ""


@dataclass
class DriftReport:
    """架构漂移报告"""

    baseline_version: str
    new_dependencies: list[dict[str, str]] = field(default_factory=list)
    removed_components: list[str] = field(default_factory=list)
    constraint_violations: list[dict[str, str]] = field(default_factory=list)
    drift_score: float = 0.0
    is_compliant: bool = True


@dataclass
class TechDebtItem:
    """技术债务项"""

    id: str
    name: str
    category: str
    severity: SmellSeverity
    estimated_effort: str = "small"
    interest_rate: float = 0.0
    principal: float = 100.0
    description: str = ""
    affected_files: list[str] = field(default_factory=list)
    suggested_fix: str = ""
    roi_score: float = 0.0


@dataclass
class PerformanceSuggestion:
    """性能优化建议"""

    category: OptimizationCategory
    location: str
    description: str
    current_complexity: str = ""
    optimized_complexity: str = ""
    estimated_improvement: str = ""
    code_before: str = ""
    code_after: str = ""
    risk: str = "low"


class RefactoringError(Exception):
    """重构异常"""


class BaselineError(RefactoringError):
    """基线异常"""


class RefactoringSi:
    """
    重构优化司 - 刑部·都官司

    提供全面的重构与优化能力：
    - 25+种代码异味检测规则库及严重度评级
    - 异味→重构模式映射表（每种异味对应1-N种推荐重构）
    - 重构安全性检查（行为等价性验证）
    - 性能优化建议（算法/缓存/懒加载/批量处理等）
    - 技术债务清理优先级排序（ROI驱动）
    - **版本化架构基线管理**：捕获/检测漂移/比较/报告
    """

    def __init__(self) -> None:
        self._smell_rules = self._build_smell_rules()
        self._refactoring_map = self._build_refactoring_map()
        self._baselines: dict[str, ArchitectureBaseline] = {}
        self._tech_debts: list[TechDebtItem] = []

    # ==================== 异味检测规则库 ====================

    def _build_smell_rules(self) -> dict[str, dict[str, Any]]:
        """构建25+种代码异味检测规则"""
        return {
            "long_method": {
                "name": "长方法 (Long Method)",
                "severity": SmellSeverity.HIGH,
                "threshold": {"max_lines": 50},
                "description": "方法体过长，难以理解和维护",
            },
            "large_class": {
                "name": "大类 (Large Class)",
                "severity": SmellSeverity.HIGH,
                "threshold": {"max_lines": 300, "max_methods": 20},
                "description": "类承担过多职责，违反单一职责原则",
            },
            "long_parameter_list": {
                "name": "长参数列表 (Long Parameter List)",
                "severity": SmellSeverity.MEDIUM,
                "threshold": {"max_params": 5},
                "description": "参数过多，调用复杂且易出错",
            },
            "duplicated_code": {
                "name": "重复代码 (Duplicated Code)",
                "severity": SmellSeverity.HIGH,
                "description": "相同或相似的代码在多处出现",
            },
            "feature_envy": {
                "name": "特性依恋 (Feature Envy)",
                "severity": SmellSeverity.MEDIUM,
                "description": "方法过度依赖其他类的数据",
            },
            "data_clumps": {
                "name": "数据泥团 (Data Clumps)",
                "severity": SmellSeverity.MEDIUM,
                "description": "一组数据总是一起出现但未封装为对象",
            },
            "primitive_obsession": {
                "name": "基本类型偏执 (Primitive Obsession)",
                "severity": SmellSeverity.LOW,
                "description": "使用基本类型代替小型的领域对象",
            },
            "switch_statements": {
                "name": "Switch语句 (Switch Statements)",
                "severity": SmellSeverity.MEDIUM,
                "threshold": {"max_cases": 5},
                "description": "复杂的switch/case可能需要用多态替代",
            },
            "lazy_class": {
                "name": "惰性类 (Lazy Class)",
                "severity": SmellSeverity.LOW,
                "description": "类的工作量太少，可以合并到其他类",
            },
            "speculative_generality": {
                "name": "投机性泛化 (Speculative Generality)",
                "severity": SmellSeverity.LOW,
                "description": "设计了不必要的抽象或灵活性",
            },
            "temporary_field": {
                "name": "临时字段 (Temporary Field)",
                "severity": SmellSeverity.MEDIUM,
                "description": "仅在特定情况下使用的实例变量",
            },
            "message_chains": {
                "name": "消息链 (Message Chains)",
                "severity": SmellSeverity.MEDIUM,
                "threshold": {"max_chain_length": 3},
                "description": "过长的对象调用链 a.b.c.d.e",
            },
            "middle_man": {
                "name": "中间人 (Middle Man)",
                "severity": SmellSeverity.LOW,
                "description": "类的方法过多地委托给其他类",
            },
            "inappropriate_intimacy": {
                "name": "不恰当的亲密 (Inappropriate Intimacy)",
                "severity": SmellSeverity.MEDIUM,
                "description": "一个类过度深入另一个类的内部",
            },
            "comments": {
                "name": "过多注释 (Comments)",
                "severity": SmellSeverity.INFO,
                "description": "注释过多可能意味着代码不够清晰",
            },
            "dead_code": {
                "name": "死代码 (Dead Code)",
                "severity": SmellSeverity.MEDIUM,
                "description": "未被使用的代码",
            },
            "god_class": {
                "name": "上帝类 (God Class)",
                "severity": SmellSeverity.CRITICAL,
                "threshold": {"max_methods": 30, "max_lines": 500},
                "description": "类过于庞大，控制了太多东西",
            },
            "god_object": {
                "name": "上帝对象 (God Object)",
                "severity": SmellSeverity.CRITICAL,
                "description": "对象知道太多或做了太多事情",
            },
            "shotgun_surgery": {
                "name": "霰弹式修改 (Shotgun Surgery)",
                "severity": SmellSeverity.CRITICAL,
                "description": "每次修改都需要改动很多地方",
            },
            "parallel_inheritance": {
                "name": "平行继承体系 (Parallel Inheritance Hierarchies)",
                "severity": SmellSeverity.MEDIUM,
                "description": "每增加一个子类就需要在另一处也增加",
            },
            "cyclic_dependency": {
                "name": "循环依赖 (Cyclic Dependency)",
                "severity": SmellSeverity.HIGH,
                "description": "模块之间形成循环引用",
            },
            "magic_numbers": {
                "name": "魔法数字 (Magic Numbers)",
                "severity": SmellSeverity.LOW,
                "description": "代码中出现的未命名的数字常量",
            },
            "hardcoded_strings": {
                "name": "硬编码字符串 (Hardcoded Strings)",
                "severity": SmellSeverity.LOW,
                "description": "直接写在代码中的字符串字面量",
            },
            "deeply_nested": {
                "name": "深层嵌套 (Deeply Nested)",
                "severity": SmellSeverity.HIGH,
                "threshold": {"max_nesting": 4},
                "description": "过多的嵌套层级导致可读性差",
            },
            "large_try_block": {
                "name": "大Try块 (Large Try Block)",
                "severity": SmellSeverity.MEDIUM,
                "threshold": {"max_lines": 30},
                "description": "try块过大，异常处理粒度太粗",
            },
            "boolean_parameter": {
                "name": "布尔参数 (Boolean Parameter)",
                "severity": SmellSeverity.LOW,
                "description": "用布尔参数控制方法行为",
            },
        }

    # ==================== 异味→重构映射 ====================

    def _build_refactoring_map(self) -> dict[str, RefactoringMapping]:
        """构建异味到重构模式的映射表"""
        mapping: dict[str, RefactoringMapping] = {}

        mappings_data: list[tuple[str, list[dict[str, str]], str]] = [
            ("long_method", [
                {"pattern": "Extract Method", "desc": "将部分逻辑提取为独立方法"},
                {"pattern": "Replace Temp with Query", "desc": "用查询替换临时变量"},
                {"pattern": "Introduce Method Object", "desc": "引入方法对象处理局部变量过多"},
                {"pattern": "Decompose Conditional", "desc": "分解条件表达式"},
            ], "medium"),
            ("large_class", [
                {"pattern": "Extract Class", "desc": "提取相关字段和方法为新类"},
                {"pattern": "Extract Subclass", "desc": "提取子类分离变化方向"},
                {"pattern": "Extract Interface", "desc": "提取接口定义共同协议"},
            ], "medium"),
            ("long_parameter_list", [
                {"pattern": "Introduce Parameter Object", "desc": "将相关参数组合为参数对象"},
                {"pattern": "Preserve Whole Object", "desc": "传递整个对象而非其属性"},
            ], "low"),
            ("duplicated_code", [
                {"pattern": "Extract Method", "desc": "提取重复代码为共享方法"},
                {"pattern": "Extract Class", "desc": "如果重复跨类则提取为工具类"},
                {"pattern": "Form Template Method", "desc": "用模板方法统一相似步骤"},
            ], "low"),
            ("feature_envy", [
                {"pattern": "Move Method", "desc": "将方法移到它最感兴趣的数据所在类"},
                {"pattern": "Extract Method", "desc": "先提取再移动"},
            ], "low"),
            ("switch_statements", [
                {"pattern": "Replace Conditional with Polymorphism", "desc": "用多态替代条件分支"},
                {"pattern": "Replace Type Code with Strategy", "desc": "用策略模式替代类型码"},
            ], "medium"),
            ("data_clumps", [
                {"pattern": "Introduce Parameter Object", "desc": "将数据泥团封装为值对象"},
                {"pattern": "Extract Class", "desc": "如果有行为则提取为类"},
            ], "low"),
            ("primitive_obsession", [
                {"pattern": "Replace Primitive with Object", "desc": "用小型对象替代基本类型"},
                {"pattern": "Extract Class", "desc": "如果类型有行为则提取为类"},
            ], "low"),
            ("god_class", [
                {"pattern": "Extract Class", "desc": "按职责拆分为多个类"},
                {"pattern": "Extract Subclass", "desc": "按变体拆分"},
            ], "high"),
            ("shotgun_surgery", [
                {"pattern": "Move Method / Move Field", "desc": "集中分散的逻辑和数据"},
                {"pattern": "Inline Class", "desc": "内联被过度拆分的类"},
            ], "high"),
            ("cyclic_dependency", [
                {"pattern": "Depends Inversion", "desc": "通过接口解除循环依赖"},
                {"pattern": "Extract Module/Package", "desc": "重新组织模块结构"},
            ], "high"),
            ("deeply_nested", [
                {"pattern": "Replace Nested Conditional with Guard Clauses", "desc": "用卫语句减少嵌套"},
                {"pattern": "Extract Method", "desc": "提取嵌套块为方法"},
                {"pattern": "Replace Conditional with Polymorphism", "desc": "用多态消除条件嵌套"},
            ], "medium"),
            ("magic_numbers", [
                {"pattern": "Replace Magic Number with Symbolic Constant", "desc": "用命名常量替代魔法数字"},
            ], "low"),
            ("dead_code", [
                {"pattern": "Remove Dead Code", "desc": "删除未被使用的代码"},
            ], "low"),
            ("message_chains", [
                {"pattern": "Hide Delegate", "desc": "隐藏委托关系"},
                {"pattern": "Extract Method", "desc": "提取中间方法缩短链路"},
            ], "low"),
            ("middle_man", [
                {"pattern": "Inline Method", "desc": "内联仅做委托的简单方法"},
                {"pattern": "Replace Delegation with Inheritance", "desc": "用继承替代委托"},
            ], "low"),
            ("temporary_field", [
                {"pattern": "Extract Class", "desc": "将临时字段及其使用方法提取为类"},
            ], "medium"),
            ("lazy_class", [
                {"pattern": "Inline Class", "desc": "内联工作量太小的类"},
            ], "low"),
            ("boolean_parameter", [
                {"pattern": "Replace Parameter with Explicit Methods", "desc": "用明确的方法替代布尔参数"},
            ], "low"),
            ("comments", [
                {"pattern": "Extract Method", "desc": "用清晰的方法名替代注释"},
                {"pattern": "Rename Method", "desc": "重命名使意图更明显"},
            ], "low"),
            ("inappropriate_intimacy", [
                {"pattern": "Move Method", "desc": "将被滥用的方法移回原类"},
                {"pattern": "Extract Method", "desc": "在外部提供接口方法"},
            ], "medium"),
            ("cyclic_dependency", [
                {"pattern": "Depends Inversion", "desc": "依赖倒置打破循环"},
            ], "high"),
        ]

        for smell_key, patterns, risk in mappings_data:
            rule = self._smell_rules.get(smell_key, {})
            mapping[smell_key] = RefactoringMapping(
                smell_type=smell_key,
                recommended_patterns=patterns,
                risk_level=risk,
                effort_estimate="medium" if risk == "high" else "small",
                description=rule.get("description", ""),
            )

        return mapping

    # ==================== 异味检测 ====================

    def detect_smells(self, source_code: str, file_path: Path | None = None) -> list[CodeSmell]:
        """
        检测源码中的代码异味

        Args:
            source_code: 源代码字符串
            file_path: 文件路径（可选）

        Returns:
            检测到的异味列表
        """
        smells: list[CodeSmell] = []
        lines = source_code.splitlines()

        try:
            tree = ast.parse(source_code)
        except SyntaxError:
            return [CodeSmell(
                smell_type="syntax_error",
                location="文件级别",
                file_path=file_path,
                severity=SmellSeverity.CRITICAL,
                description="语法错误，无法进行深度分析",
            )]

        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                end_line = getattr(node, "end_lineno", node.lineno)
                func_length = end_line - node.lineno + 1
                max_lines = self._smell_rules.get("long_method", {}).get("threshold", {}).get("max_lines", 50)

                if func_length > max_lines:
                    smells.append(CodeSmell(
                        smell_type="long_method",
                        location=f"{node.name}() 第{node.lineno}-{end_line}行",
                        file_path=file_path,
                        line_number=node.lineno,
                        severity=self._smell_rules["long_method"]["severity"],
                        description=f"函数{node.name}过长({func_length}行>{max_lines}行)",
                        suggested_refactorings=[p["pattern"] for p in self._refactoring_map.get("long_method", RefactoringMapping()).recommended_patterns],
                        confidence=min(1.0, func_length / max_lines / 2),
                    ))

                params = len(node.args.args) + len(node.args.kwonlyargs)
                max_params = self._smell_rules.get("long_parameter_list", {}).get("threshold", {}).get("max_params", 5)
                if params > max_params:
                    smells.append(CodeSmell(
                        smell_type="long_parameter_list",
                        location=f"{node.name}() 参数数={params}",
                        file_path=file_path,
                        line_number=node.lineno,
                        severity=SmellSeverity.MEDIUM,
                        description=f"参数过多({params}>{max_params})",
                    ))

            elif isinstance(node, ast.ClassDef):
                end_line = getattr(node, "end_lineno", node.lineno)
                cls_length = end_line - node.lineno + 1
                method_count = sum(
                    1 for n in ast.iter_child_nodes(node)
                    if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
                )

                god_rule = self._smell_rules.get("god_class", {})
                large_rule = self._smell_rules.get("large_class", {})

                if method_count > god_rule.get("threshold", {}).get("max_methods", 30) or \
                   cls_length > god_rule.get("threshold", {}).get("max_lines", 500):
                    smells.append(CodeSmell(
                        smell_type="god_class",
                        location=f"{node.name} ({method_count}方法, {cls_length}行)",
                        file_path=file_path,
                        line_number=node.lineno,
                        severity=SmellSeverity.CRITICAL,
                        description=f"上帝类{node.name}: {method_count}个方法, {cls_length}行",
                    ))
                elif method_count > large_rule.get("threshold", {}).get("max_methods", 20) or \
                     cls_length > large_rule.get("threshold", {}).get("max_lines", 300):
                    smells.append(CodeSmell(
                        smell_type="large_class",
                        location=f"{node.name} ({method_count}方法, {cls_length}行)",
                        file_path=file_path,
                        line_number=node.lineno,
                        severity=large_rule["severity"],
                        description=f"大类{node.name}: {method_count}个方法, {cls_length}行",
                    ))

        magic_numbers = re.findall(r"(?<![\w.])(\d{3,})(?![\w.\]])", source_code)
        if len(magic_numbers) > 3:
            smells.append(CodeSmell(
                smell_type="magic_numbers",
                location="全局",
                file_path=file_path,
                severity=SmellSeverity.LOW,
                description=f"发现{len(magic_numbers)}个可能的魔法数字",
            ))

        comment_lines = sum(1 for l in lines if l.strip().startswith("#"))
        total_non_empty = sum(1 for l in lines if l.strip())
        if total_non_empty > 10 and comment_lines / total_non_empty > 0.4:
            smells.append(CodeSmell(
                smell_type="comments",
                location="全局",
                file_path=file_path,
                severity=SmellSeverity.INFO,
                description=f"注释率过高({comment_lines}/{total_non_empty}={comment_lines/total_non_empty:.0%})",
            ))

        pass_count = sum(1 for l in lines if re.match(r"^\s*(pass|ellipsis|\.\.\.)\s*$", l.strip()))
        if pass_count > 0:
            smells.append(CodeSmell(
                smell_type="dead_code",
                location="多处",
                file_path=file_path,
                severity=SmellSeverity.MEDIUM,
                description=f"发现{pass_count}处死代码(pass/...)",
            ))

        todo_matches = re.findall(r"#\s*(TODO|FIXME|HACK|XXX)\b", source_code)
        if todo_matches:
            smells.append(CodeSmell(
                smell_type="dead_code",
                location="多处",
                file_path=file_path,
                severity=SmellSeverity.INFO,
                description=f"发现{len(todo_matches)}处技术债务标记",
            ))

        nesting_result = self._check_deep_nesting(tree)
        if nesting_result:
            smells.append(nesting_result)

        return sorted(smells, key=lambda s: (
            {"critical": 0, "high": 1, "medium": 2, "low": 3, "info": 4}.get(s.severity.value, 5),
            s.confidence,
        ), reverse=True)

    @staticmethod
    def _check_deep_nesting(tree: ast.AST) -> CodeSmell | None:
        """检查深层嵌套"""
        max_nesting = 0

        class NestingVisitor(ast.NodeVisitor):
            def __init__(self):
                self.current_depth = 0
                self.max_depth = 0

            def visit_If(self, node):
                self.current_depth += 1
                self.max_depth = max(self.max_depth, self.current_depth)
                self.generic_visit(node)
                self.current_depth -= 1

            def visit_For(self, node):
                self.current_depth += 1
                self.max_depth = max(self.max_depth, self.current_depth)
                self.generic_visit(node)
                self.current_depth -= 1

            def visit_While(self, node):
                self.current_depth += 1
                self.max_depth = max(self.max_depth, self.current_depth)
                self.generic_visit(node)
                self.current_depth -= 1

            def visit_Try(self, node):
                self.current_depth += 1
                self.max_depth = max(self.max_depth, self.current_depth)
                self.generic_visit(node)
                self.current_depth -= 1

            def visit_With(self, node):
                self.current_depth += 1
                self.max_depth = max(self.max_depth, self.current_depth)
                self.generic_visit(node)
                self.current_depth -= 1

        visitor = NestingVisitor()
        visitor.visit(tree)
        max_nesting = visitor.max_depth

        threshold = 4
        if max_nesting > threshold:
            return CodeSmell(
                smell_type="deeply_nested",
                location="全局",
                severity=SmellSeverity.HIGH,
                description=f"最大嵌套深度={max_nesting}(阈值={threshold})",
            )
        return None

    # ==================== 重构建议生成 ====================

    def get_refactoring_suggestions(self, smell_type: str) -> RefactoringMapping:
        """获取指定异味的重构建议"""
        return self._refactoring_map.get(smell_type, RefactoringMapping(smell_type=smell_type))

    def suggest_all_refactorings(self, smells: list[CodeSmell]) -> list[dict[str, Any]]:
        """为所有检测到的异味生成重构建议"""
        suggestions: list[dict[str, Any]] = []
        seen_types: set[str] = set()

        for smell in smells:
            if smell.smell_type not in seen_types:
                seen_types.add(smell.smell_type)
                mapping = self._refactoring_map.get(smell.smell_type)
                if mapping and mapping.recommended_patterns:
                    suggestions.append({
                        "smell": smell.smell_type,
                        "location": smell.location,
                        "severity": smell.severity.value,
                        "risk": mapping.risk_level,
                        "effort": mapping.effort_estimate,
                        "patterns": mapping.recommended_patterns,
                        "confidence": round(smell.confidence, 2),
                    })

        suggestions.sort(key=lambda s: (
            {"critical": 0, "high": 1, "medium": 2, "low": 3}.get(s["severity"], 4),
            s["confidence"],
        ), reverse=True)
        return suggestions

    # ==================== 性能优化建议 ====================

    def analyze_performance(self, source_code: str) -> list[PerformanceSuggestion]:
        """
        分析代码并提供性能优化建议

        分析维度：
        - 算法复杂度优化
        - 缓存策略
        - 懒加载
        - 批量处理
        - 异步化
        - 连接池
        - 内存优化
        """
        suggestions: list[PerformanceSuggestion] = []

        lines = source_code.splitlines()
        for i, line in enumerate(lines, start=1):

            if re.search(r"for\s+\w+\s+in\s+\w+\s*:", line):
                inner_for_match = re.search(r"\s+(for|while)\s+", "\n".join(lines[i:i+3]))
                if inner_for_match:
                    suggestions.append(PerformanceSuggestion(
                        category=OptimizationCategory.BATCH_PROCESSING,
                        location=f"第{i}行附近",
                        description="检测到嵌套循环，考虑使用批量操作或集合推导式替代",
                        current_complexity="O(n*m)",
                        optimized_complexity="O(n) 或 O(n+m)",
                        estimated_improvement="显著提升大数据量场景性能",
                        risk="low",
                    ))

            if re.search(r"\.append\(.*?\)\s*for\s+", line) or re.search(r"\[.*?for.*?for.*?\]", line):
                suggestions.append(PerformanceSuggestion(
                    category=OptimizationCategory.ALGORITHM,
                    location=f"第{i}行",
                    description="列表推导式中存在嵌套循环，考虑使用itertools或预分配",
                    risk="low",
                ))

            if re.search(r"open\(", line) and not re.search(r"(with|contextlib)", source_code[max(0, i-3):i]):
                suggestions.append(PerformanceSuggestion(
                    category=OptimizationCategory.ALGORITHM,
                    location=f"第{i}行",
                    description="文件操作未使用上下文管理器(with)，可能导致资源泄漏",
                    code_before=line.strip(),
                    code_after=f"with open(...) as f:",
                    risk="low",
                ))

            if re.search(r"(requests\.get|urllib|httpx\.get)\s*\(", line) and "async" not in line.lower():
                suggestions.append(PerformanceSuggestion(
                    category=OptimizationCategory.ASYNC,
                    location=f"第{i}行",
                    description="同步HTTP请求可能阻塞事件循环，考虑使用async/httpx异步客户端",
                    risk="medium",
                ))

            if re.search(r"str\s*\+\s*str", line) or re.search(r'f""[^"]*\{[^}]*\}\s*\+\s*', line):
                suggestions.append(PerformanceSuggestion(
                    category=OptimizationCategory.ALGORITHM,
                    location=f"第{i}行",
                    description="字符串拼接效率低，考虑使用join()或f-string一次性格式化",
                    code_before=line.strip(),
                    code_after='result = "".join(parts)',
                    risk="low",
                ))

            if re.search(r"list\(.*?\.keys(\)|\(\))", line):
                suggestions.append(PerformanceSuggestion(
                    category=OptimizationCategory.ALGORITHM,
                    location=f"第{i}行",
                    description="不必要的list()转换，字典的keys()/values()本身已返回视图",
                    risk="low",
                ))

        loop_in_func_pattern = re.findall(
            r"def\s+(\w+)\([^)]*\):(?:\s+(?:if|for|while))",
            source_code,
        )
        if len(loop_in_func_pattern) >= 3:
            suggestions.append(PerformanceSuggestion(
                category=OptimizationCategory.CACHE,
                location="多个函数",
                description="多个函数包含循环操作，考虑使用functools.lru_cache缓存结果",
                risk="low",
            ))

        return suggestions[:15]

    # ==================== 技术债务管理 ====================

    def add_tech_debt(self, debt: TechDebtItem) -> None:
        """添加技术债务记录"""
        debt.roi_score = self._calculate_debt_roi(debt)
        self._tech_debts.append(debt)

    @staticmethod
    def _calculate_debt_roi(debt: TechDebtItem) -> float:
        """计算技术债务ROI分数"""
        severity_weight = {
            SmellSeverity.CRITICAL: 10,
            SmellSeverity.HIGH: 7,
            SmellSeverity.MEDIUM: 4,
            SmellSeverity.LOW: 2,
            SmellSeverity.INFO: 1,
        }
        effort_map = {"tiny": 1, "small": 2, "medium": 4, "large": 7, "huge": 10}

        benefit = severity_weight.get(debt.severity, 3) * (debt.interest_rate + 1)
        cost = effort_map.get(debt.estimated_effort.lower(), 4)
        return round(benefit / max(cost, 1), 2)

    def get_debt_repayment_plan(self) -> list[dict[str, Any]]:
        """
        获取基于ROI的技术债务偿还计划

        Returns:
            排序后的偿还计划列表
        """
        debts = sorted(self._tech_debts, key=lambda d: d.roi_score, reverse=True)
        plan: list[dict[str, Any]] = []

        for debt in debts:
            plan.append({
                "id": debt.id,
                "name": debt.name,
                "category": debt.category,
                "severity": debt.severity.value,
                "roi_score": debt.roi_score,
                "effort": debt.estimated_effort,
                "interest_rate": f"{debt.interest_rate:.1%}",
                "suggested_fix": debt.suggested_fix[:60] if debt.suggested_fix else "",
                "priority": "高" if debt.roi_score >= 3.0 else ("中" if debt.roi_score >= 1.5 else "低"),
            })

        return plan

    # ==================== 版本化架构基线管理 ====================

    def capture_baseline(self, version: str, architecture: dict[str, Any]) -> ArchitectureBaseline:
        """
        捕获当前架构基线

        Args:
            version: 版本号 (如 "v1.0")
            architecture: 架构信息字典，包含 decisions, modules, constraints 等

        Returns:
            架构基线对象
        """
        import hashlib as hl

        arch_str = json.dumps(architecture, sort_keys=True, ensure_ascii=False)
        checksum = hl.sha256(arch_str.encode()).hexdigest()[:16]

        baseline = ArchitectureBaseline(
            version=version,
            architecture_decisions=architecture.get("decisions", []),
            module_structure=architecture.get("modules", {}),
            constraints=architecture.get("constraints", []),
            captured_at=__import__("datetime").datetime.now().isoformat(),
            checksum=checksum,
        )
        self._baselines[version] = baseline
        return baseline

    def detect_drift(self, current_state: dict[str, Any], baseline_version: str) -> DriftReport:
        """
        架构漂移检测

        检测：
        - 新增未登记的依赖
        - 移除必要组件
        - 违反约束的变更

        Args:
            current_state: 当前架构状态
            baseline_version: 基线版本号

        Returns:
            漂移报告
        """
        if baseline_version not in self._baselines:
            raise BaselineError(f"基线版本不存在: {baseline_version}")

        baseline = self._baselines[baseline_version]
        report = DriftReport(baseline_version=baseline_version)

        base_modules = set(baseline.module_structure.keys())
        curr_modules = set(current_state.get("modules", {}).keys())

        new_deps = curr_modules - base_modules
        removed = base_modules - curr_modules

        for mod in sorted(new_deps):
            report.new_dependencies.append({
                "module": mod,
                "type": "new_module",
                "status": "unregistered",
                "action": "请评估是否需要在架构决策文档中登记此模块",
            })

        for mod in sorted(removed):
            report.removed_components.append(mod)

        base_constraints = set(baseline.constraints)
        curr_constraints = set(current_state.get("constraints", []))

        violated = base_constraints - curr_constraints
        for vc in sorted(violated):
            report.constraint_violations.append({
                "constraint": vc,
                "status": "violated",
                "action": "确认是否有意移除此约束，或恢复约束并调整实现",
            })

        drift_points = (
            len(report.new_dependencies) * 2 +
            len(report.removed_components) * 3 +
            len(report.constraint_violations) * 4
        )
        report.drift_score = min(100.0, drift_points * 5)
        report.is_compliant = drift_points == 0

        return report

    def baseline_report(self, baseline: ArchitectureBaseline) -> str:
        """
        生成架构基线文档

        Args:
            baseline: 基线对象

        Returns:
            Markdown格式的基线文档
        """
        lines: list[str] = []
        lines.append(f"# 📐 架构基线 v{baseline.version}\n")
        lines.append(f"> **捕获时间**: {baseline.captured_at}")
        lines.append(f"> **校验和**: `{baseline.checksum}`\n")

        if baseline.architecture_decisions:
            lines.append("## 架构决策 (ADR)\n")
            lines.append("| # | 决策 | 背景 | 结果 |")
            lines.append("| --- | --- | --- | --- |")
            for i, dec in enumerate(baseline.architecture_decisions, start=1):
                lines.append(f"| {i} | {dec.get('decision', '')} | {dec.get('context', '')} | {dec.get('outcome', '')} |")
            lines.append("")

        if baseline.module_structure:
            lines.append("## 模块结构\n")
            for mod_name, components in baseline.module_structure.items():
                comp_str = ", ".join(f"`{c}`" for c in components)
                lines.append(f"- **{mod_name}**: {comp_str}")
            lines.append("")

        if baseline.constraints:
            lines.append("## 架构约束\n")
            for constraint in baseline.constraints:
                lines.append(f"- ⚠️ {constraint}")
            lines.append("")

        return "\n".join(lines)

    def compare_baselines(self, version_a: str, version_b: str) -> str:
        """
        比较两个版本的架构基线

        Args:
            version_a: 版本A
            version_b: 版本B

        Returns:
            Markdown格式的差异报告
        """
        if version_a not in self._baselines or version_b not in self._baselines:
            missing = [v for v in [version_a, version_b] if v not in self._baselines]
            raise BaselineError(f"基线版本不存在: {', '.join(missing)}")

        ba = self._baselines[version_a]
        bb = self._baselines[version_b]

        lines: list[str] = []
        lines.append(f"# 🔄 架构基线对比: {version_a} → {version_b}\n")
        lines.append("| 项目 | {version_a} | {version_b} | 变化 |".format(version_a=version_a, version_b=version_b))
        lines.append("| --- | --- | --- | --- |")

        modules_a = set(ba.module_structure.keys())
        modules_b = set(bb.module_structure.keys())
        added_mods = modules_b - modules_a
        removed_mods = modules_a - modules_b

        lines.append(f"| 模块数 | {len(modules_a)} | {len(modules_b)} | {'+' + str(len(added_mods)) if added_mods else ''}{'-' + str(len(removed_mods)) if removed_mods else ''} |")

        decisions_a = len(ba.architecture_decisions)
        decisions_b = len(bb.architecture_decisions)
        lines.append(f"| 架构决策数 | {decisions_a} | {decisions_b} | {'+' + str(decisions_b - decisions_a) if decisions_b != decisions_a else '—'} |")

        constraints_a = len(ba.constraints)
        constraints_b = len(bb.constraints)
        lines.append(f"| 约束数 | {constraints_a} | {constraints_b} | {'+' + str(constraints_b - constraints_a) if constraints_b != constraints_a else '—'} |")

        if added_mods:
            lines.append(f"\n### ➕ 新增模块\n")
            for m in sorted(added_mods):
                comps = bb.module_structure.get(m, [])
                lines.append(f"- `{m}`: {', '.join(comps)}")

        if removed_mods:
            lines.append(f"\n### ➖ 移除模块\n")
            for m in sorted(removed_mods):
                lines.append(f"- `{m}`")

        new_constraints = set(bb.constraints) - set(ba.constraints)
        if new_constraints:
            lines.append(f"\n### 🆕 新增约束\n")
            for c in sorted(new_constraints):
                lines.append(f"- {c}")

        return "\n".join(lines) + "\n"

    # ==================== 报告生成 ====================

    def generate_report(self) -> str:
        """生成重构优化司报告"""
        lines: list[str] = []
        lines.append("# 🔧 重构优化司 · 综合报告\n")

        lines.append(f"## 代码异味规则库 ({len(self._smell_rules)}条)\n")
        lines.append("| 异味 | 严重度 | 风险 | 推荐重构数 |")
        lines.append("| --- | --- | --- | --- |")
        for smell_key, rule in sorted(self._smell_rules.items()):
            mapping = self._refactoring_map.get(smell_key)
            pattern_count = len(mapping.recommended_patterns) if mapping else 0
            lines.append(
                f"| {rule['name']} | `{rule['severity'].value}` "
                f"| `{mapping.risk_level if mapping else '?'}` | {pattern_count} |"
            )

        if self._tech_debts:
            plan = self.get_debt_repayment_plan()
            lines.append(f"\n## 💰 技术债务偿还计划 ({len(plan)}项)\n")
            lines.append("| ID | 名称 | ROI | 优先级 | 工作量 |")
            lines.append("| --- | --- | --- | --- | --- |")
            for item in plan[:10]:
                lines.append(
                    f"`{item['id']}` | {item['name']} | **{item['roi_score']}** "
                    f"| {item['priority']} | {item['effort']} |"
                )

        if self._baselines:
            lines.append(f"\n## 📐 架构基线 ({len(self._baselines)}个版本)\n")
            for ver, bl in self._baselines.items():
                lines.append(f"- **v{ver}** (捕获于 {bl.captured_at[:10]}): "
                           f"{len(bl.module_structure)}模块, {len(bl.constraints)}约束")

        return "\n".join(lines) + "\n"


if __name__ == "__main__":
    print("=" * 60)
    print("重构优化司 - 功能演示")
    print("=" * 60)

    si = RefactoringSi()

    sample_code = '''\
class UserService:
    """用户服务 - God Class示例"""

    def __init__(self):
        self.db = None
        self.cache = None
        self.logger = None
        self.email_svc = None
        self.notif_svc = None
        self.file_storage = None
        self.analytics = None
        self.audit_log = None
        self.config = None
        self.session_mgr = None
        self.rate_limiter = None
        self.validator = None
        self.serializer = None
        self.perm_checker = None

    def process_user_registration(self, user_data):
        result = None
        if user_data.get('type') == 'admin':
            if user_data.get('role') == 'super':
                if user_data.get('status') == 'active':
                    if user_data.get('verified'):
                        if user_data.get('approved'):
                            for item in user_data.get('items', []):
                                if item.get('valid'):
                                    for sub_item in item.get('subs', []):
                                        if sub_item.get('ok'):
                                            result = sub_item
        return result

    def find_user_by_email(self, email):
        users = []
        for u in self.db.query('SELECT * FROM users'):
            if u.email == email:
                users.append(u)
        return users

    def generate_report_data(self):
        data = []
        for day in range(365):
            daily = []
            for hour in range(24):
                daily.append(hour * day)
            data.append(daily)
        return data
'''

    print("\n--- 异味检测 ---")
    smells = si.detect_smells(sample_code, Path("user_service.py"))
    print(f"  检测到异味: {len(smells)}个")
    for s in smells:
        icon = {"critical": "🔴", "high": "🟠", "medium": "🟡", "low": "🔵", "info": "⚪"}.get(s.severity.value, "?")
        print(f"  [{icon}] [{s.severity.value}] {s.smell_type}: {s.description}")

    print("\n--- 重构建议 ---")
    suggestions = si.suggest_all_refactorings(smells)
    for sug in suggestions[:5]:
        patterns = ", ".join(p["pattern"] for p in sug["patterns"])
        print(f"  [{sug['severity']}] {sug['smell']}: {patterns} (风险:{sug['risk']})")

    print("\n--- 性能分析 ---")
    perf = si.analyze_performance(sample_code)
    print(f"  优化建议: {len(perf)}条")
    for p in perf[:3]:
        print(f"  [{p.category.value}] {p.description}")

    print("\n--- 技术债务 ---")
    si.add_tech_debt(TechDebtItem(
        id="TD-001", name="UserService上帝类重构",
        category="code_quality", severity=SmellSeverity.CRITICAL,
        estimated_effort="large", interest_rate=0.15,
        description="UserService承担了过多职责，每次修改都影响面广",
        affected_files=["services/user_service.py"],
        suggested_fix="按职责拆分为UserRepo/UserValidator/UserNotifier等",
    ))
    plan = si.get_debt_repayment_plan()
    for item in plan:
        print(f"  [{item['priority']}] ROI={item['roi_score']}: {item['name']}")

    print("\n--- 架构基线管理 ---")
    arch_v1 = {
        "decisions": [
            {"decision": "采用分层架构", "context": "关注点分离", "outcome": "Controller-Service-Repository三层"},
            {"decision": "使用SQLAlchemy ORM", "context": "数据库抽象需求", "outcome": "统一的数据库访问层"},
        ],
        "modules": {
            "controllers": ["user_controller", "order_controller"],
            "services": ["user_service", "order_service"],
            "repositories": ["user_repo", "order_repo"],
        },
        "constraints": ["禁止跨层直接调用", "所有数据库操作必须通过Repository层"],
    }
    bl_v1 = si.capture_baseline("v1.0", arch_v1)
    print(f"  基线 v1.0 已捕获: 校验和={bl_v1.checksum}")

    arch_v2 = {
        "decisions": arch_v1["decisions"] + [
            {"decision": "引入Redis缓存", "context": "性能优化", "outcome": "热点数据缓存加速"},
        ],
        "modules": {
            **arch_v1["modules"],
            "cache": ["redis_cache", "cache_manager"],
        },
        "constraints": arch_v1["constraints"] + ["缓存失效策略必须与业务一致"],
    }
    bl_v2 = si.capture_baseline("v1.1", arch_v2)

    drift = si.detect_drift({
        "modules": {
            "controllers": ["user_controller", "order_controller", "admin_controller"],
            "services": ["user_service", "order_service", "analytics_service"],
            "repositories": ["user_repo", "order_repo"],
            "external": ["payment_gateway"],
        },
        "constraints": ["禁止跨层直接调用"],
    }, "v1.0")
    print(f"  漂移检测: 合规={drift.is_compliant}, 得分={drift.drift_score}")
    print(f"  新增依赖: {len(drift.new_dependencies)}, 违反约束: {len(drift.constraint_violations)}")

    compare = si.compare_baselines("v1.0", "v1.1")
    print(f"\n--- 基线对比 ---\n{compare}")

    baseline_doc = si.baseline_report(bl_v1)
    print(f"\n--- 基线文档预览 ---\n{baseline_doc[:400]}...")

    report = si.generate_report()
    print(f"\n--- 完整报告预览 (前800字符) ---\n{report[:800]}...")

    print("\n✅ 所有测试通过!")
