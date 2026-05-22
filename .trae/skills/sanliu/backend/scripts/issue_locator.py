#!/usr/bin/env python3
"""
问题定位脚本 - 自动定位问题根源，分析问题影响范围，生成问题诊断报告，提供修复建议
增强功能：智能根因分析、代码模式匹配、问题关联分析、修复置信度评估、版本化报告输出
"""

import re
import json
import os
import sys
import ast
import subprocess
import hashlib
import difflib
import statistics
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional, Set, Tuple, Callable, Union
from dataclasses import dataclass, field, asdict
from collections import defaultdict, Counter
from enum import Enum
import argparse
import logging
import traceback


class IssueSeverity(Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class IssueCategory(Enum):
    SYNTAX = "syntax"
    RUNTIME = "runtime"
    LOGIC = "logic"
    PERFORMANCE = "performance"
    SECURITY = "security"
    DEPENDENCY = "dependency"
    CONFIGURATION = "configuration"
    ENVIRONMENT = "environment"
    UNKNOWN = "unknown"


@dataclass
class StackFrame:
    file_path: str
    line_number: int
    function_name: str
    code_snippet: str = ""
    is_project_file: bool = False


@dataclass
class IssueLocation:
    file_path: str
    line_number: int
    column: int
    function_name: str = ""
    class_name: str = ""
    code_snippet: str = ""
    context_lines: List[str] = field(default_factory=list)


@dataclass
class ImpactAnalysis:
    affected_files: Set[str] = field(default_factory=set)
    affected_functions: Set[str] = field(default_factory=set)
    affected_modules: Set[str] = field(default_factory=set)
    downstream_dependencies: Set[str] = field(default_factory=set)
    user_impact: str = ""
    severity_score: float = 0.0


@dataclass
class RootCause:
    description: str
    category: IssueCategory
    confidence: float
    evidence: List[str] = field(default_factory=list)
    related_files: Set[str] = field(default_factory=set)
    suggested_fixes: List[str] = field(default_factory=list)


@dataclass
class DiagnosedIssue:
    issue_id: str
    title: str
    description: str
    severity: IssueSeverity
    category: IssueCategory
    location: IssueLocation
    stack_trace: List[StackFrame]
    root_cause: RootCause
    impact: ImpactAnalysis
    timestamp: datetime
    raw_error: str = ""
    confidence: float = 0.0
    related_issues: List[str] = field(default_factory=list)
    fix_suggestions: List[Dict[str, Any]] = field(default_factory=list)
    diagnostic_steps: List[str] = field(default_factory=list)


@dataclass
class IssueRelation:
    source_id: str
    target_id: str
    relation_type: str
    confidence: float
    evidence: List[str] = field(default_factory=list)


@dataclass
class CodePattern:
    pattern_id: str
    name: str
    description: str
    regex: str
    category: IssueCategory
    severity: IssueSeverity
    suggested_fix: str


@dataclass
class DiagnosticStep:
    step_id: int
    description: str
    action: str
    expected_result: str
    status: str = "pending"


@dataclass
class DiagnosisReport:
    timestamp: str
    total_issues: int
    critical_count: int
    high_count: int
    medium_count: int
    low_count: int
    issues: List[DiagnosedIssue]
    summary: str
    recommendations: List[str]


class StackTraceParser:
    """堆栈跟踪解析器"""

    PYTHON_TRACE_PATTERN = re.compile(
        r'File "([^"]+)", line (\d+), in (\w+)\s*\n\s*(.+)'
    )

    JAVASCRIPT_TRACE_PATTERN = re.compile(
        r'at\s+(?:(\w+)\s+)?\(?(?:([^)]+):(\d+):(\d+))\)?'
    )

    def parse_python_trace(self, trace_text: str) -> List[StackFrame]:
        """解析Python堆栈跟踪"""
        frames = []

        for match in self.PYTHON_TRACE_PATTERN.finditer(trace_text):
            file_path, line_num, func_name, code = match.groups()

            is_project = not any(x in file_path for x in [
                '/usr/lib', '/usr/local/lib', 'site-packages',
                'lib/python', 'node_modules'
            ])

            frames.append(StackFrame(
                file_path=file_path,
                line_number=int(line_num),
                function_name=func_name,
                code_snippet=code.strip(),
                is_project_file=is_project
            ))

        return frames

    def parse_javascript_trace(self, trace_text: str) -> List[StackFrame]:
        """解析JavaScript堆栈跟踪"""
        frames = []

        for match in self.JAVASCRIPT_TRACE_PATTERN.finditer(trace_text):
            func_name, file_path, line_num, col = match.groups()

            is_project = 'node_modules' not in (file_path or '')

            frames.append(StackFrame(
                file_path=file_path or "",
                line_number=int(line_num) if line_num else 0,
                function_name=func_name or "<anonymous>",
                is_project_file=is_project
            ))

        return frames

    def parse(self, trace_text: str, language: str = "auto") -> List[StackFrame]:
        """自动解析堆栈跟踪"""
        if language == "python" or "Traceback" in trace_text:
            return self.parse_python_trace(trace_text)
        elif language == "javascript" or "Error:" in trace_text:
            return self.parse_javascript_trace(trace_text)
        else:
            python_frames = self.parse_python_trace(trace_text)
            if python_frames:
                return python_frames
            return self.parse_javascript_trace(trace_text)


class CodeAnalyzer:
    """代码分析器"""

    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root).resolve()

    def get_code_context(
        self,
        file_path: str,
        line_number: int,
        context_lines: int = 5
    ) -> Tuple[str, List[str]]:
        """获取代码上下文"""
        try:
            path = Path(file_path)
            if not path.is_absolute():
                path = self.project_root / path

            with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()

            if line_number < 1 or line_number > len(lines):
                return "", []

            start = max(0, line_number - context_lines - 1)
            end = min(len(lines), line_number + context_lines)

            code_snippet = lines[line_number - 1].strip() if line_number <= len(lines) else ""
            context = [f"{i+1}: {line.rstrip()}" for i, line in enumerate(lines[start:end], start)]

            return code_snippet, context

        except Exception as e:
            return "", [f"无法读取文件: {e}"]

    def analyze_function(self, file_path: str, function_name: str) -> Dict[str, Any]:
        """分析函数定义"""
        try:
            path = Path(file_path)
            if not path.is_absolute():
                path = self.project_root / path

            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()

            tree = ast.parse(content)

            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    if node.name == function_name:
                        return {
                            "name": node.name,
                            "line_start": node.lineno,
                            "line_end": node.end_lineno if hasattr(node, 'end_lineno') else node.lineno,
                            "args": [arg.arg for arg in node.args.args],
                            "docstring": ast.get_docstring(node),
                            "complexity": self._calculate_complexity(node)
                        }

            return {}

        except SyntaxError:
            return {}
        except Exception as e:
            return {"error": str(e)}

    def _calculate_complexity(self, node: ast.AST) -> int:
        """计算圈复杂度"""
        complexity = 1

        for child in ast.walk(node):
            if isinstance(child, (ast.If, ast.While, ast.For, ast.ExceptHandler)):
                complexity += 1
            elif isinstance(child, ast.BoolOp):
                complexity += len(child.values) - 1

        return complexity

    def find_callers(self, function_name: str, file_pattern: str = "*.py") -> Set[str]:
        """查找函数的调用者"""
        callers = set()

        for py_file in self.project_root.rglob(file_pattern):
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()

                if function_name in content:
                    lines = content.split('\n')
                    for i, line in enumerate(lines, 1):
                        if re.search(rf'\b{function_name}\s*\(', line):
                            callers.add(f"{py_file}:{i}")

            except Exception:
                continue

        return callers


class ImpactAnalyzer:
    """影响范围分析器"""

    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root).resolve()
        self.code_analyzer = CodeAnalyzer(project_root)

    def analyze_impact(
        self,
        file_path: str,
        function_name: str = ""
    ) -> ImpactAnalysis:
        """分析问题的影响范围"""
        impact = ImpactAnalysis()

        impact.affected_files.add(file_path)

        if function_name:
            impact.affected_functions.add(function_name)
            callers = self.code_analyzer.find_callers(function_name)
            impact.downstream_dependencies.update(callers)

        module_name = self._get_module_name(file_path)
        if module_name:
            impact.affected_modules.add(module_name)

        dependents = self._find_dependents(file_path)
        impact.affected_files.update(dependents)

        impact.user_impact = self._assess_user_impact(
            file_path, function_name, len(dependents)
        )

        impact.severity_score = self._calculate_severity_score(impact)

        return impact

    def _get_module_name(self, file_path: str) -> str:
        """获取模块名称"""
        try:
            rel_path = Path(file_path).relative_to(self.project_root)
            parts = rel_path.parts

            if parts[0] in ['app', 'src', 'lib']:
                return '.'.join(parts[:-1])
            return parts[0] if parts else ""
        except ValueError:
            return ""

    def _find_dependents(self, file_path: str) -> Set[str]:
        """查找依赖该文件的模块"""
        dependents = set()
        file_name = Path(file_path).stem

        for py_file in self.project_root.rglob("*.py"):
            if str(py_file) == file_path:
                continue

            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()

                import_patterns = [
                    rf'from\s+\S*\.{file_name}\s+import',
                    rf'import\s+\S*\.{file_name}',
                    rf'from\s+{file_name}\s+import',
                    rf'import\s+{file_name}\b',
                ]

                for pattern in import_patterns:
                    if re.search(pattern, content):
                        dependents.add(str(py_file))
                        break

            except Exception:
                continue

        return dependents

    def _assess_user_impact(
        self,
        file_path: str,
        function_name: str,
        dependent_count: int
    ) -> str:
        """评估对用户的影响"""
        path_lower = file_path.lower()

        if any(x in path_lower for x in ['api', 'endpoint', 'route', 'view']):
            return "高 - 影响API接口，可能导致服务不可用"

        if any(x in path_lower for x in ['auth', 'login', 'security']):
            return "高 - 影响认证授权，存在安全风险"

        if any(x in path_lower for x in ['test', 'spec']):
            return "低 - 仅影响测试"

        if dependent_count > 10:
            return "高 - 被大量模块依赖"
        elif dependent_count > 5:
            return "中 - 被多个模块依赖"
        elif dependent_count > 0:
            return "低 - 被少量模块依赖"

        return "低 - 影响范围有限"

    def _calculate_severity_score(self, impact: ImpactAnalysis) -> float:
        """计算严重程度分数"""
        score = 0.0

        score += len(impact.affected_files) * 0.5
        score += len(impact.affected_functions) * 1.0
        score += len(impact.downstream_dependencies) * 0.3

        if "高" in impact.user_impact:
            score += 10.0
        elif "中" in impact.user_impact:
            score += 5.0
        else:
            score += 1.0

        return min(score, 100.0)


class RootCauseAnalyzer:
    """根因分析器"""

    ERROR_PATTERNS = {
        r"NameError.*'(\w+)'": {
            "category": IssueCategory.SYNTAX,
            "cause_template": "变量或名称 '{group1}' 未定义",
            "fix_template": "定义变量 '{group1}' 或检查拼写"
        },
        r"TypeError.*'(\w+)'.*'(\w+)'": {
            "category": IssueCategory.LOGIC,
            "cause_template": "类型不匹配: 期望 '{group1}'，实际 '{group2}'",
            "fix_template": "检查类型转换，使用isinstance()验证类型"
        },
        r"KeyError:\s*'(\w+)'": {
            "category": IssueCategory.LOGIC,
            "cause_template": "字典中不存在键 '{group1}'",
            "fix_template": "使用dict.get()方法或先检查键是否存在"
        },
        r"IndexError.*out of range": {
            "category": IssueCategory.LOGIC,
            "cause_template": "索引超出序列范围",
            "fix_template": "检查索引范围，确保小于len(sequence)"
        },
        r"ModuleNotFoundError.*'(\w+)'": {
            "category": IssueCategory.DEPENDENCY,
            "cause_template": "模块 '{group1}' 未安装",
            "fix_template": "运行: pip install {group1}"
        },
        r"ImportError.*'(\w+)'": {
            "category": IssueCategory.DEPENDENCY,
            "cause_template": "无法导入 '{group1}'",
            "fix_template": "检查模块安装和PYTHONPATH设置"
        },
        r"Connection.*refused": {
            "category": IssueCategory.ENVIRONMENT,
            "cause_template": "连接被拒绝，服务未运行或端口错误",
            "fix_template": "检查服务状态和端口配置"
        },
        r"Permission.*denied": {
            "category": IssueCategory.CONFIGURATION,
            "cause_template": "权限不足，无法访问资源",
            "fix_template": "检查文件/目录权限或运行身份"
        },
        r"Timeout": {
            "category": IssueCategory.PERFORMANCE,
            "cause_template": "操作超时",
            "fix_template": "增加超时时间或优化操作性能"
        },
        r"MemoryError": {
            "category": IssueCategory.PERFORMANCE,
            "cause_template": "内存不足",
            "fix_template": "优化内存使用，分批处理数据"
        },
        r"RecursionError": {
            "category": IssueCategory.LOGIC,
            "cause_template": "递归深度超限，可能存在无限递归",
            "fix_template": "检查递归终止条件，考虑使用迭代替代"
        },
        r"AssertionError": {
            "category": IssueCategory.LOGIC,
            "cause_template": "断言失败，程序状态不符合预期",
            "fix_template": "检查断言条件或修复逻辑错误"
        },
        r"FileNotFoundError.*'([^']+)'": {
            "category": IssueCategory.ENVIRONMENT,
            "cause_template": "文件 '{group1}' 不存在",
            "fix_template": "检查文件路径，创建缺失文件或目录"
        },
        r"ZeroDivisionError": {
            "category": IssueCategory.LOGIC,
            "cause_template": "除零错误",
            "fix_template": "添加除数检查，处理零值情况"
        },
        r"AttributeError.*'(\w+)'": {
            "category": IssueCategory.LOGIC,
            "cause_template": "对象没有属性 '{group1}'",
            "fix_template": "检查对象类型，使用hasattr()验证属性"
        },
        r"ValueError.*invalid literal": {
            "category": IssueCategory.LOGIC,
            "cause_template": "值转换失败，数据格式不正确",
            "fix_template": "验证输入数据格式，添加异常处理"
        },
        r"RuntimeError": {
            "category": IssueCategory.RUNTIME,
            "cause_template": "运行时错误",
            "fix_template": "检查运行环境，添加错误处理逻辑"
        },
        r"StopIteration": {
            "category": IssueCategory.LOGIC,
            "cause_template": "迭代器已耗尽",
            "fix_template": "检查迭代器状态，使用for循环或next()默认值"
        },
        r"OverflowError": {
            "category": IssueCategory.LOGIC,
            "cause_template": "数值溢出",
            "fix_template": "检查数值范围，使用大数类型"
        },
        r"FloatingPointError": {
            "category": IssueCategory.LOGIC,
            "cause_template": "浮点运算错误",
            "fix_template": "检查浮点运算，使用decimal模块处理精度"
        },
        r"OSError.*\[Errno\s*(\d+)\]": {
            "category": IssueCategory.ENVIRONMENT,
            "cause_template": "操作系统错误 (错误码: {group1})",
            "fix_template": "检查系统资源、权限或文件状态"
        },
        r"UnicodeError": {
            "category": IssueCategory.LOGIC,
            "cause_template": "Unicode编码/解码错误",
            "fix_template": "指定正确的编码格式，处理特殊字符"
        },
        r"IndentationError": {
            "category": IssueCategory.SYNTAX,
            "cause_template": "缩进错误",
            "fix_template": "检查代码缩进，保持一致性"
        },
        r"TabError": {
            "category": IssueCategory.SYNTAX,
            "cause_template": "Tab和空格混用",
            "fix_template": "统一使用空格或Tab缩进"
        },
        r"NotImplementedError": {
            "category": IssueCategory.LOGIC,
            "cause_template": "方法未实现",
            "fix_template": "实现该方法或使用其他替代方案"
        },
        r"GeneratorExit": {
            "category": IssueCategory.RUNTIME,
            "cause_template": "生成器被关闭",
            "fix_template": "检查生成器使用方式，处理关闭事件"
        },
        r"SystemExit": {
            "category": IssueCategory.RUNTIME,
            "cause_template": "程序主动退出",
            "fix_template": "检查退出原因，处理清理逻辑"
        },
    }

    def __init__(self):
        self._error_chain: List[Dict[str, Any]] = []
        self._causality_graph: Dict[str, Set[str]] = defaultdict(set)

    def analyze(self, error_message: str, stack_trace: List[StackFrame]) -> RootCause:
        """分析错误根因"""
        for pattern, info in self.ERROR_PATTERNS.items():
            match = re.search(pattern, error_message, re.IGNORECASE)
            if match:
                groups = match.groups()
                cause = info["cause_template"]
                fix = info["fix_template"]

                for i, group in enumerate(groups, 1):
                    cause = cause.replace(f"{{group{i}}}", group or "")
                    fix = fix.replace(f"{{group{i}}}", group or "")

                return RootCause(
                    description=cause,
                    category=info["category"],
                    confidence=0.8,
                    evidence=[error_message],
                    related_files={f.file_path for f in stack_trace if f.is_project_file},
                    suggested_fixes=[fix]
                )

        if stack_trace:
            project_frames = [f for f in stack_trace if f.is_project_file]
            if project_frames:
                deepest = project_frames[-1]
                return RootCause(
                    description=f"在 {deepest.function_name} 中发生错误",
                    category=IssueCategory.UNKNOWN,
                    confidence=0.5,
                    evidence=[error_message, f"文件: {deepest.file_path}:{deepest.line_number}"],
                    related_files={deepest.file_path},
                    suggested_fixes=[
                        f"检查 {deepest.file_path}:{deepest.line_number} 的代码",
                        "添加日志以获取更多信息"
                    ]
                )

        return RootCause(
            description="无法确定具体根因",
            category=IssueCategory.UNKNOWN,
            confidence=0.0,
            evidence=[error_message],
            suggested_fixes=["查看完整堆栈跟踪", "添加调试日志"]
        )

    def analyze_with_context(
        self,
        error_message: str,
        stack_trace: List[StackFrame],
        code_context: Optional[Dict[str, Any]] = None
    ) -> RootCause:
        """带上下文的深度根因分析"""
        basic_cause = self.analyze(error_message, stack_trace)
        
        if basic_cause.confidence >= 0.8:
            return basic_cause
        
        enhanced_evidence = list(basic_cause.evidence)
        enhanced_fixes = list(basic_cause.suggested_fixes)
        
        if code_context:
            if 'variables' in code_context:
                for var_name, var_value in code_context['variables'].items():
                    if var_value is None:
                        enhanced_evidence.append(f"变量 '{var_name}' 值为 None")
                        enhanced_fixes.append(f"检查变量 '{var_name}' 是否正确初始化")
            
            if 'function_args' in code_context:
                for arg_name, arg_value in code_context['function_args'].items():
                    if arg_value is None:
                        enhanced_evidence.append(f"参数 '{arg_name}' 为 None")
        
        if stack_trace:
            for frame in stack_trace[:3]:
                if frame.is_project_file:
                    enhanced_fixes.append(f"在 {frame.file_path}:{frame.line_number} 添加调试日志")
        
        return RootCause(
            description=basic_cause.description,
            category=basic_cause.category,
            confidence=min(basic_cause.confidence + 0.1, 1.0),
            evidence=enhanced_evidence,
            related_files=basic_cause.related_files,
            suggested_fixes=list(dict.fromkeys(enhanced_fixes))
        )

    def analyze_causality_chain(
        self,
        error_message: str,
        stack_trace: List[StackFrame],
        related_errors: Optional[List[str]] = None
    ) -> List[RootCause]:
        """分析因果链，识别一系列相关问题的根因"""
        causes = []
        
        primary_cause = self.analyze(error_message, stack_trace)
        causes.append(primary_cause)
        
        if related_errors:
            for related_error in related_errors:
                secondary_cause = self.analyze(related_error, [])
                if secondary_cause.confidence > 0.5:
                    causes.append(secondary_cause)
                    self._causality_graph[primary_cause.description].add(secondary_cause.description)
        
        if len(stack_trace) > 1:
            project_frames = [f for f in stack_trace if f.is_project_file]
            for i, frame in enumerate(project_frames[:-1]):
                next_frame = project_frames[i + 1]
                chain_key = f"{frame.file_path}:{frame.line_number}"
                chain_value = f"{next_frame.file_path}:{next_frame.line_number}"
                self._causality_graph[chain_key].add(chain_value)
        
        return causes

    def get_causality_graph(self) -> Dict[str, Set[str]]:
        """获取因果关系图"""
        return dict(self._causality_graph)

    def identify_root_node(self, causes: List[RootCause]) -> Optional[RootCause]:
        """识别因果链中的根节点（最根本的原因）"""
        if not causes:
            return None
        
        if len(causes) == 1:
            return causes[0]
        
        cause_scores = []
        for cause in causes:
            score = cause.confidence
            if cause.category == IssueCategory.SYNTAX:
                score += 0.3
            elif cause.category == IssueCategory.LOGIC:
                score += 0.2
            elif cause.category == IssueCategory.DEPENDENCY:
                score += 0.25
            cause_scores.append((cause, score))
        
        cause_scores.sort(key=lambda x: x[1], reverse=True)
        return cause_scores[0][0]

    def multi_factor_analysis(
        self,
        error_message: str,
        stack_trace: List[StackFrame],
        runtime_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """多因素分析，综合考虑多个可能的原因"""
        factors = {
            'primary_cause': None,
            'contributing_factors': [],
            'environmental_factors': [],
            'code_quality_factors': [],
            'confidence_breakdown': {}
        }
        
        primary_cause = self.analyze(error_message, stack_trace)
        factors['primary_cause'] = primary_cause
        factors['confidence_breakdown']['pattern_match'] = primary_cause.confidence
        
        if stack_trace:
            project_frames = [f for f in stack_trace if f.is_project_file]
            if project_frames:
                frame_count_factor = min(len(project_frames) / 5.0, 1.0)
                factors['confidence_breakdown']['stack_depth'] = frame_count_factor
                
                for frame in project_frames[:3]:
                    factors['contributing_factors'].append({
                        'file': frame.file_path,
                        'line': frame.line_number,
                        'function': frame.function_name,
                        'snippet': frame.code_snippet
                    })
        
        if runtime_context:
            if runtime_context.get('memory_usage', 0) > 80:
                factors['environmental_factors'].append({
                    'type': 'memory',
                    'description': '内存使用率过高',
                    'value': runtime_context.get('memory_usage')
                })
            
            if runtime_context.get('cpu_usage', 0) > 90:
                factors['environmental_factors'].append({
                    'type': 'cpu',
                    'description': 'CPU使用率过高',
                    'value': runtime_context.get('cpu_usage')
                })
            
            if runtime_context.get('disk_usage', 0) > 90:
                factors['environmental_factors'].append({
                    'type': 'disk',
                    'description': '磁盘使用率过高',
                    'value': runtime_context.get('disk_usage')
                })
        
        if error_message:
            if 'deprecated' in error_message.lower():
                factors['code_quality_factors'].append({
                    'type': 'deprecation',
                    'description': '使用了已弃用的API'
                })
            
            if 'warning' in error_message.lower():
                factors['code_quality_factors'].append({
                    'type': 'warning',
                    'description': '存在警告级别的问题'
                })
        
        total_confidence = sum(factors['confidence_breakdown'].values()) / len(factors['confidence_breakdown'])
        factors['confidence_breakdown']['overall'] = min(total_confidence, 1.0)
        
        return factors


class CodePatternMatcher:
    """代码模式匹配器"""

    COMMON_PATTERNS = [
        CodePattern(
            pattern_id="CP001",
            name="空值检查缺失",
            description="可能存在空值引用",
            regex=r"(\w+)\.\w+\s*\(",
            category=IssueCategory.LOGIC,
            severity=IssueSeverity.MEDIUM,
            suggested_fix="添加空值检查: if var is not None:"
        ),
        CodePattern(
            pattern_id="CP002",
            name="异常捕获过于宽泛",
            description="捕获了过于宽泛的异常类型",
            regex=r"except\s*:",
            category=IssueCategory.LOGIC,
            severity=IssueSeverity.MEDIUM,
            suggested_fix="指定具体的异常类型"
        ),
        CodePattern(
            pattern_id="CP003",
            name="硬编码配置",
            description="发现硬编码的配置值",
            regex=r"(password|secret|api_key|token)\s*=\s*['\"][^'\"]+['\"]",
            category=IssueCategory.SECURITY,
            severity=IssueSeverity.HIGH,
            suggested_fix="将敏感配置移至环境变量或配置文件"
        ),
        CodePattern(
            pattern_id="CP004",
            name="资源未关闭",
            description="文件或连接资源可能未正确关闭",
            regex=r"open\s*\([^)]+\)(?!\s*as)",
            category=IssueCategory.RUNTIME,
            severity=IssueSeverity.MEDIUM,
            suggested_fix="使用 with 语句确保资源正确关闭"
        ),
        CodePattern(
            pattern_id="CP005",
            name="无限循环风险",
            description="可能存在无限循环",
            regex=r"while\s+True\s*:",
            category=IssueCategory.LOGIC,
            severity=IssueSeverity.MEDIUM,
            suggested_fix="确保循环有明确的退出条件"
        ),
        CodePattern(
            pattern_id="CP006",
            name="SQL注入风险",
            description="SQL查询可能存在注入风险",
            regex=r"execute\s*\(\s*[f]?['\"]",
            category=IssueCategory.SECURITY,
            severity=IssueSeverity.HIGH,
            suggested_fix="使用参数化查询替代字符串拼接"
        ),
        CodePattern(
            pattern_id="CP007",
            name="未处理返回值",
            description="函数返回值未被使用",
            regex=r"^\s*(?!return|if|while|for)\w+\s*\([^)]*\)\s*$",
            category=IssueCategory.LOGIC,
            severity=IssueSeverity.LOW,
            suggested_fix="检查是否需要处理函数返回值"
        ),
    ]

    def __init__(self):
        self.compiled_patterns = [
            (p, re.compile(p.regex, re.IGNORECASE | re.MULTILINE))
            for p in self.COMMON_PATTERNS
        ]

    def scan_code(self, code: str, file_path: str = "") -> List[Dict[str, Any]]:
        """扫描代码中的模式"""
        findings = []
        
        for pattern, compiled in self.compiled_patterns:
            for match in compiled.finditer(code):
                line_num = code[:match.start()].count('\n') + 1
                findings.append({
                    'pattern_id': pattern.pattern_id,
                    'name': pattern.name,
                    'description': pattern.description,
                    'file_path': file_path,
                    'line_number': line_num,
                    'matched_text': match.group(0),
                    'category': pattern.category.value,
                    'severity': pattern.severity.value,
                    'suggested_fix': pattern.suggested_fix
                })
        
        return findings

    def scan_file(self, file_path: str) -> List[Dict[str, Any]]:
        """扫描文件中的模式"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                code = f.read()
            return self.scan_code(code, file_path)
        except Exception:
            return []


class IssueCorrelator:
    """问题关联分析器"""

    def __init__(self):
        self.issue_graph: Dict[str, Set[str]] = defaultdict(set)
        self.issue_patterns: Dict[str, str] = {}

    def add_issue(self, issue: DiagnosedIssue):
        """添加问题到关联图"""
        pattern_hash = self._compute_pattern_hash(issue)
        self.issue_patterns[issue.issue_id] = pattern_hash

    def _compute_pattern_hash(self, issue: DiagnosedIssue) -> str:
        """计算问题模式哈希"""
        key_parts = [
            issue.category.value,
            issue.root_cause.category.value if issue.root_cause else "",
            issue.location.file_path,
        ]
        key = "|".join(key_parts)
        return hashlib.md5(key.encode()).hexdigest()[:12]

    def find_related_issues(
        self,
        issues: List[DiagnosedIssue]
    ) -> List[IssueRelation]:
        """查找相关问题"""
        relations = []
        
        for i, issue1 in enumerate(issues):
            for issue2 in issues[i+1:]:
                relation = self._compute_relation(issue1, issue2)
                if relation:
                    relations.append(relation)
        
        return relations

    def _compute_relation(
        self,
        issue1: DiagnosedIssue,
        issue2: DiagnosedIssue
    ) -> Optional[IssueRelation]:
        """计算两个问题之间的关联"""
        evidence = []
        confidence = 0.0
        relation_type = "unknown"
        
        if issue1.location.file_path == issue2.location.file_path:
            evidence.append("同一文件")
            confidence += 0.3
            relation_type = "same_file"
        
        if issue1.category == issue2.category:
            evidence.append("相同类别")
            confidence += 0.2
        
        if issue1.root_cause.category == issue2.root_cause.category:
            evidence.append("相同根因类别")
            confidence += 0.3
            relation_type = "same_root_cause"
        
        if abs((issue1.timestamp - issue2.timestamp).total_seconds()) < 60:
            evidence.append("相近时间")
            confidence += 0.2
            relation_type = "temporal"
        
        if confidence >= 0.5:
            return IssueRelation(
                source_id=issue1.issue_id,
                target_id=issue2.issue_id,
                relation_type=relation_type,
                confidence=min(confidence, 1.0),
                evidence=evidence
            )
        
        return None


class IntelligentDiagnostics:
    """智能诊断引擎"""

    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root).resolve()
        self.pattern_matcher = CodePatternMatcher()
        self.correlator = IssueCorrelator()

    def diagnose(
        self,
        error_text: str,
        stack_trace: List[StackFrame],
        code_context: Optional[Dict[str, Any]] = None
    ) -> List[DiagnosticStep]:
        """生成诊断步骤"""
        steps = []
        step_id = 1
        
        steps.append(DiagnosticStep(
            step_id=step_id,
            description="分析错误消息",
            action=f"解析错误类型和位置",
            expected_result="确定错误基本类型"
        ))
        step_id += 1
        
        if stack_trace:
            project_frames = [f for f in stack_trace if f.is_project_file]
            if project_frames:
                steps.append(DiagnosticStep(
                    step_id=step_id,
                    description="定位问题代码",
                    action=f"检查 {project_frames[-1].file_path}:{project_frames[-1].line_number}",
                    expected_result="找到问题代码位置"
                ))
                step_id += 1
        
        if code_context:
            steps.append(DiagnosticStep(
                step_id=step_id,
                description="检查变量状态",
                action="检查相关变量的值和类型",
                expected_result="确认变量状态正确"
            ))
            step_id += 1
        
        steps.append(DiagnosticStep(
            step_id=step_id,
            description="验证修复",
            action="运行测试验证修复效果",
            expected_result="测试通过，问题解决"
        ))
        
        return steps

    def generate_fix_suggestions(
        self,
        issue: DiagnosedIssue
    ) -> List[Dict[str, Any]]:
        """生成修复建议"""
        suggestions = []
        
        if issue.root_cause.suggested_fixes:
            suggestions.append({
                'type': 'primary',
                'priority': 'high',
                'description': issue.root_cause.suggested_fixes[0],
                'confidence': issue.confidence,
                'steps': [
                    f"1. 定位问题: {issue.location.file_path}:{issue.location.line_number}",
                    f"2. 分析根因: {issue.root_cause.description}",
                    f"3. 实施修复: {issue.root_cause.suggested_fixes[0]}",
                    "4. 验证修复: 运行相关测试"
                ]
            })
        
        if issue.category == IssueCategory.SECURITY:
            suggestions.append({
                'type': 'security',
                'priority': 'critical',
                'description': '安全问题需要立即处理',
                'confidence': 0.9,
                'steps': [
                    "1. 评估安全风险",
                    "2. 实施安全修复",
                    "3. 进行安全审查",
                    "4. 更新安全文档"
                ]
            })
        
        if issue.impact.severity_score > 20:
            suggestions.append({
                'type': 'mitigation',
                'priority': 'high',
                'description': '高影响问题建议临时缓解措施',
                'confidence': 0.7,
                'steps': [
                    "1. 添加异常处理防止问题扩散",
                    "2. 记录详细日志便于追踪",
                    "3. 实施降级方案",
                    "4. 后续进行完整修复"
                ]
            })
        
        return suggestions


class IssueLocator:
    """问题定位器主类"""

    def __init__(self, project_root: str = ".", output_dir: str = "docs/reports", version: str = "latest"):
        self.project_root = Path(project_root).resolve()
        self.output_dir = Path(output_dir).resolve()
        self.version = version
        self.versioned_output_dir = self.output_dir / version
        self.versioned_output_dir.mkdir(parents=True, exist_ok=True)
        
        self.stack_parser = StackTraceParser()
        self.code_analyzer = CodeAnalyzer(project_root)
        self.impact_analyzer = ImpactAnalyzer(project_root)
        self.root_cause_analyzer = RootCauseAnalyzer()
        self.pattern_matcher = CodePatternMatcher()
        self.correlator = IssueCorrelator()
        self.diagnostics = IntelligentDiagnostics(project_root)
        self.logger = self._setup_logger()
        self.issue_counter = 0

    def _setup_logger(self) -> logging.Logger:
        """设置日志记录器"""
        logger = logging.getLogger('IssueLocator')
        logger.setLevel(logging.INFO)

        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)

        return logger

    def _generate_issue_id(self) -> str:
        """生成问题ID"""
        self.issue_counter += 1
        return f"ISSUE-{datetime.now().strftime('%Y%m%d')}-{self.issue_counter:04d}"

    def locate_from_error(self, error_text: str, language: str = "auto") -> DiagnosedIssue:
        """从错误文本定位问题"""
        lines = error_text.strip().split('\n')

        error_line = ""
        for line in lines:
            if any(x in line for x in ['Error:', 'Exception:', '错误']):
                error_line = line
                break

        if not error_line and lines:
            error_line = lines[-1]

        stack_trace = self.stack_parser.parse(error_text, language)

        location = self._determine_location(stack_trace)

        root_cause = self.root_cause_analyzer.analyze(error_line, stack_trace)

        impact = ImpactAnalysis()
        if location.file_path:
            impact = self.impact_analyzer.analyze_impact(
                location.file_path,
                location.function_name
            )

        severity = self._determine_severity(root_cause, impact)
        
        code_context = None
        if location.file_path and location.line_number > 0:
            code_context = self._get_code_context(location.file_path, location.line_number)

        confidence = self._calculate_confidence(root_cause, stack_trace, location)
        
        diagnostic_steps = self.diagnostics.diagnose(error_line, stack_trace, code_context)

        issue = DiagnosedIssue(
            issue_id=self._generate_issue_id(),
            title=self._generate_title(error_line, root_cause),
            description=error_line,
            severity=severity,
            category=root_cause.category,
            location=location,
            stack_trace=stack_trace,
            root_cause=root_cause,
            impact=impact,
            timestamp=datetime.now(),
            raw_error=error_text,
            confidence=confidence,
            diagnostic_steps=[f"{s.step_id}. {s.description}: {s.action}" for s in diagnostic_steps]
        )
        
        issue.fix_suggestions = self.diagnostics.generate_fix_suggestions(issue)
        
        self.correlator.add_issue(issue)

        return issue

    def _get_code_context(self, file_path: str, line_number: int) -> Dict[str, Any]:
        """获取代码上下文"""
        context = {}
        try:
            code_snippet, context_lines = self.code_analyzer.get_code_context(
                file_path, line_number, 10
            )
            context['code_snippet'] = code_snippet
            context['context_lines'] = context_lines
        except Exception:
            pass
        return context

    def _calculate_confidence(
        self,
        root_cause: RootCause,
        stack_trace: List[StackFrame],
        location: IssueLocation
    ) -> float:
        """计算问题定位置信度"""
        confidence = root_cause.confidence
        
        if stack_trace:
            project_frames = [f for f in stack_trace if f.is_project_file]
            if project_frames:
                confidence += 0.1
        
        if location.file_path and location.line_number > 0:
            confidence += 0.1
        
        return min(confidence, 1.0)

    def locate_from_file(
        self,
        file_path: str,
        line_number: int,
        context: str = ""
    ) -> DiagnosedIssue:
        """从文件位置定位问题"""
        code_snippet, context_lines = self.code_analyzer.get_code_context(
            file_path, line_number, 5
        )

        location = IssueLocation(
            file_path=file_path,
            line_number=line_number,
            column=0,
            code_snippet=code_snippet,
            context_lines=context_lines
        )

        func_info = self.code_analyzer.analyze_function(file_path, "")
        if func_info:
            location.function_name = func_info.get("name", "")

        impact = self.impact_analyzer.analyze_impact(file_path, location.function_name)

        root_cause = RootCause(
            description=f"代码位于 {file_path}:{line_number}",
            category=IssueCategory.UNKNOWN,
            confidence=0.3,
            evidence=[code_snippet],
            related_files={file_path},
            suggested_fixes=["检查代码逻辑", "运行静态分析工具"]
        )

        return DiagnosedIssue(
            issue_id=self._generate_issue_id(),
            title=f"代码问题: {Path(file_path).name}:{line_number}",
            description=context or code_snippet,
            severity=IssueSeverity.MEDIUM,
            category=IssueCategory.UNKNOWN,
            location=location,
            stack_trace=[],
            root_cause=root_cause,
            impact=impact,
            timestamp=datetime.now()
        )

    def _determine_location(self, stack_trace: List[StackFrame]) -> IssueLocation:
        """确定问题位置"""
        if not stack_trace:
            return IssueLocation(file_path="", line_number=0, column=0)

        project_frames = [f for f in stack_trace if f.is_project_file]

        if project_frames:
            frame = project_frames[-1]
        else:
            frame = stack_trace[-1]

        code_snippet, context_lines = self.code_analyzer.get_code_context(
            frame.file_path, frame.line_number, 3
        )

        return IssueLocation(
            file_path=frame.file_path,
            line_number=frame.line_number,
            column=0,
            function_name=frame.function_name,
            code_snippet=code_snippet,
            context_lines=context_lines
        )

    def _determine_severity(
        self,
        root_cause: RootCause,
        impact: ImpactAnalysis
    ) -> IssueSeverity:
        """确定问题严重程度"""
        if root_cause.category == IssueCategory.SECURITY:
            return IssueSeverity.CRITICAL

        if root_cause.category == IssueCategory.SYNTAX:
            return IssueSeverity.HIGH

        if impact.severity_score > 20:
            return IssueSeverity.HIGH
        elif impact.severity_score > 10:
            return IssueSeverity.MEDIUM
        elif impact.severity_score > 5:
            return IssueSeverity.LOW

        return IssueSeverity.INFO

    def _generate_title(self, error_line: str, root_cause: RootCause) -> str:
        """生成问题标题"""
        if root_cause.description:
            return f"{root_cause.category.value}: {root_cause.description[:50]}"

        error_type = error_line.split(':')[0] if ':' in error_line else "Error"
        return f"{error_type}: {error_line[:50]}"

    def diagnose_project(self, file_pattern: str = "*.py") -> List[DiagnosedIssue]:
        """诊断整个项目"""
        issues = []

        for py_file in self.project_root.rglob(file_pattern):
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()

                try:
                    ast.parse(content)
                except SyntaxError as e:
                    location = IssueLocation(
                        file_path=str(py_file),
                        line_number=e.lineno or 1,
                        column=e.offset or 0,
                        code_snippet=e.text or ""
                    )

                    root_cause = RootCause(
                        description=f"语法错误: {e.msg}",
                        category=IssueCategory.SYNTAX,
                        confidence=1.0,
                        evidence=[str(e)],
                        related_files={str(py_file)},
                        suggested_fixes=["修复语法错误", "检查括号和缩进"]
                    )

                    impact = self.impact_analyzer.analyze_impact(str(py_file))

                    issues.append(DiagnosedIssue(
                        issue_id=self._generate_issue_id(),
                        title=f"语法错误: {py_file.name}",
                        description=str(e),
                        severity=IssueSeverity.HIGH,
                        category=IssueCategory.SYNTAX,
                        location=location,
                        stack_trace=[],
                        root_cause=root_cause,
                        impact=impact,
                        timestamp=datetime.now()
                    ))

            except Exception as e:
                self.logger.error(f"无法分析文件 {py_file}: {e}")

        return issues

    def generate_report(
        self,
        issues: List[DiagnosedIssue],
        output_format: str = "markdown"
    ) -> str:
        """生成诊断报告"""
        if output_format == "json":
            return self._generate_json_report(issues)
        return self._generate_markdown_report(issues)

    def _generate_markdown_report(self, issues: List[DiagnosedIssue]) -> str:
        """生成Markdown格式报告"""
        lines = [
            "# 问题诊断报告",
            f"\n生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"\n## 概览",
            f"- 总问题数: {len(issues)}",
            f"- 严重: {sum(1 for i in issues if i.severity == IssueSeverity.CRITICAL)}",
            f"- 高: {sum(1 for i in issues if i.severity == IssueSeverity.HIGH)}",
            f"- 中: {sum(1 for i in issues if i.severity == IssueSeverity.MEDIUM)}",
            f"- 低: {sum(1 for i in issues if i.severity == IssueSeverity.LOW)}",
        ]
        
        relations = self.correlator.find_related_issues(issues)
        if relations:
            lines.extend([
                f"\n## 问题关联分析",
                f"发现 {len(relations)} 组相关问题",
            ])
            for rel in relations[:10]:
                lines.append(f"- {rel.source_id} ↔ {rel.target_id} ({rel.relation_type}, 置信度: {rel.confidence:.0%})")

        severity_order = [
            IssueSeverity.CRITICAL,
            IssueSeverity.HIGH,
            IssueSeverity.MEDIUM,
            IssueSeverity.LOW,
            IssueSeverity.INFO
        ]

        for severity in severity_order:
            severity_issues = [i for i in issues if i.severity == severity]
            if severity_issues:
                lines.extend([
                    f"\n## {severity.value.upper()} 优先级问题",
                ])

                for issue in severity_issues:
                    lines.extend([
                        f"\n### {issue.issue_id}: {issue.title}",
                        f"**类别**: {issue.category.value}",
                        f"**时间**: {issue.timestamp.strftime('%Y-%m-%d %H:%M:%S')}",
                        f"**置信度**: {issue.confidence:.0%}",
                    ])

                    if issue.location.file_path:
                        lines.append(f"**位置**: {issue.location.file_path}:{issue.location.line_number}")

                    if issue.location.code_snippet:
                        lines.extend([
                            "**代码**:",
                            "```python",
                            issue.location.code_snippet,
                            "```"
                        ])

                    lines.extend([
                        f"\n**根因分析** ({issue.root_cause.confidence*100:.0f}% 置信度):",
                        issue.root_cause.description,
                    ])

                    if issue.root_cause.suggested_fixes:
                        lines.extend([
                            "\n**修复建议**:",
                        ])
                        for fix in issue.root_cause.suggested_fixes:
                            lines.append(f"- {fix}")
                    
                    if issue.fix_suggestions:
                        lines.extend([
                            "\n**智能修复建议**:",
                        ])
                        for suggestion in issue.fix_suggestions:
                            lines.append(f"- [{suggestion['priority']}] {suggestion['description']} (置信度: {suggestion['confidence']:.0%})")

                    if issue.diagnostic_steps:
                        lines.extend([
                            "\n**诊断步骤**:",
                        ])
                        for step in issue.diagnostic_steps:
                            lines.append(f"  {step}")

                    if issue.impact.user_impact:
                        lines.extend([
                            f"\n**影响范围**: {issue.impact.user_impact}",
                            f"- 影响文件: {len(issue.impact.affected_files)} 个",
                            f"- 影响函数: {len(issue.impact.affected_functions)} 个",
                            f"- 下游依赖: {len(issue.impact.downstream_dependencies)} 个",
                        ])

                    if issue.stack_trace:
                        lines.extend([
                            "\n**堆栈跟踪**:",
                            "```",
                        ])
                        for frame in issue.stack_trace[-5:]:
                            marker = "👉 " if frame.is_project_file else "   "
                            lines.append(
                                f"{marker}{frame.file_path}:{frame.line_number} in {frame.function_name}()"
                            )
                        lines.append("```")

        lines.extend([
            "\n## 修复优先级建议",
            "1. 首先处理 CRITICAL 级别的问题",
            "2. 优先修复影响范围广的问题",
            "3. 按照依赖关系从底层向上修复",
            "4. 验证修复后运行完整测试套件",
        ])

        return '\n'.join(lines)

    def _generate_json_report(self, issues: List[DiagnosedIssue]) -> str:
        """生成JSON格式报告"""
        report = {
            "timestamp": datetime.now().isoformat(),
            "summary": {
                "total": len(issues),
                "critical": sum(1 for i in issues if i.severity == IssueSeverity.CRITICAL),
                "high": sum(1 for i in issues if i.severity == IssueSeverity.HIGH),
                "medium": sum(1 for i in issues if i.severity == IssueSeverity.MEDIUM),
                "low": sum(1 for i in issues if i.severity == IssueSeverity.LOW),
            },
            "issues": [
                {
                    "id": i.issue_id,
                    "title": i.title,
                    "description": i.description,
                    "severity": i.severity.value,
                    "category": i.category.value,
                    "location": {
                        "file": i.location.file_path,
                        "line": i.location.line_number,
                        "column": i.location.column,
                        "function": i.location.function_name,
                        "code": i.location.code_snippet
                    },
                    "root_cause": {
                        "description": i.root_cause.description,
                        "category": i.root_cause.category.value,
                        "confidence": i.root_cause.confidence,
                        "suggested_fixes": i.root_cause.suggested_fixes
                    },
                    "impact": {
                        "affected_files": list(i.impact.affected_files),
                        "affected_functions": list(i.impact.affected_functions),
                        "user_impact": i.impact.user_impact,
                        "severity_score": i.impact.severity_score
                    },
                    "stack_trace": [
                        {
                            "file": f.file_path,
                            "line": f.line_number,
                            "function": f.function_name,
                            "is_project_file": f.is_project_file
                        }
                        for f in i.stack_trace
                    ]
                }
                for i in issues
            ]
        }

        return json.dumps(report, indent=2, ensure_ascii=False)


def main():
    parser = argparse.ArgumentParser(
        description='问题定位脚本 - 自动定位问题根源，分析影响范围'
    )
    parser.add_argument(
        '--error-file',
        help='包含错误信息的文件路径'
    )
    parser.add_argument(
        '--error-text',
        help='直接提供错误文本'
    )
    parser.add_argument(
        '--file',
        help='问题所在文件路径'
    )
    parser.add_argument(
        '--line',
        type=int,
        help='问题所在行号'
    )
    parser.add_argument(
        '--project-root',
        default='.',
        help='项目根目录 (默认: 当前目录)'
    )
    parser.add_argument(
        '--output-dir',
        default='docs/reports',
        help='报告输出目录'
    )
    parser.add_argument(
        '--version',
        default='latest',
        help='版本号，报告将输出到 docs/reports/{version}/ 目录'
    )
    parser.add_argument(
        '-o', '--output',
        help='报告输出路径'
    )
    parser.add_argument(
        '-f', '--format',
        choices=['markdown', 'json'],
        default='markdown',
        help='输出格式 (默认: markdown)'
    )
    parser.add_argument(
        '--scan-project',
        action='store_true',
        help='扫描整个项目查找问题'
    )
    parser.add_argument(
        '--multi-factor',
        action='store_true',
        help='启用多因素分析'
    )

    args = parser.parse_args()

    locator = IssueLocator(args.project_root, args.output_dir, args.version)
    issues = []

    if args.scan_project:
        print("正在扫描项目...")
        issues = locator.diagnose_project()
    elif args.error_file:
        with open(args.error_file, 'r', encoding='utf-8') as f:
            error_text = f.read()
        issues = [locator.locate_from_error(error_text)]
    elif args.error_text:
        issues = [locator.locate_from_error(args.error_text)]
    elif args.file:
        issues = [locator.locate_from_file(args.file, args.line or 1)]
    else:
        print("请提供 --error-file、--error-text、--file 或 --scan-project 参数")
        return 1

    report = locator.generate_report(issues, args.format)

    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            f.write(report)
        print(f"报告已保存到: {args.output}")
    else:
        output_path = locator.versioned_output_dir / f"diagnosis_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{'md' if args.format == 'markdown' else 'json'}"
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(report)
        print(f"报告已保存到: {output_path}")

    print(f"\n诊断完成! 发现问题: {len(issues)} 个")

    critical = sum(1 for i in issues if i.severity == IssueSeverity.CRITICAL)
    if critical > 0:
        print(f"⚠️  有 {critical} 个严重问题需要立即处理!")
        return 1

    return 0


class CrossModuleLocator:
    """跨模块问题定位器"""

    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root).resolve()
        self.module_graph: Dict[str, Set[str]] = defaultdict(set)
        self.call_graph: Dict[str, List[str]] = defaultdict(list)

    def build_dependency_graph(self) -> None:
        """构建模块依赖图"""
        for py_file in self.project_root.rglob("*.py"):
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                module_name = self._get_module_name(str(py_file))
                imports = self._extract_imports(content)
                
                self.module_graph[module_name] = set(imports)
                
            except Exception:
                continue

    def _get_module_name(self, file_path: str) -> str:
        """获取模块名称"""
        try:
            rel_path = Path(file_path).relative_to(self.project_root)
            parts = list(rel_path.parts)
            if parts[-1].endswith('.py'):
                parts[-1] = parts[-1][:-3]
            return '.'.join(parts)
        except ValueError:
            return Path(file_path).stem

    def _extract_imports(self, content: str) -> List[str]:
        """提取导入的模块"""
        imports = []
        
        import_patterns = [
            r'^import\s+(\S+)',
            r'^from\s+(\S+)\s+import',
        ]
        
        for pattern in import_patterns:
            for match in re.finditer(pattern, content, re.MULTILINE):
                module = match.group(1).split('.')[0]
                imports.append(module)
        
        return imports

    def locate_cross_module_issue(
        self,
        error_location: IssueLocation,
        stack_trace: List[StackFrame]
    ) -> Dict[str, Any]:
        """定位跨模块问题"""
        self.build_dependency_graph()
        
        affected_modules = set()
        propagation_chain = []
        
        for frame in stack_trace:
            if frame.is_project_file:
                module = self._get_module_name(frame.file_path)
                affected_modules.add(module)
                propagation_chain.append({
                    "module": module,
                    "file": frame.file_path,
                    "line": frame.line_number,
                    "function": frame.function_name
                })
        
        root_module = self._identify_root_cause_module(propagation_chain)
        
        related_modules = set()
        for module in affected_modules:
            related_modules.update(self._get_dependents(module))
        
        return {
            "affected_modules": list(affected_modules),
            "propagation_chain": propagation_chain,
            "root_module": root_module,
            "related_modules": list(related_modules),
            "complexity_score": len(affected_modules) * 0.3 + len(propagation_chain) * 0.2
        }

    def _identify_root_cause_module(self, chain: List[Dict]) -> str:
        """识别根因模块"""
        if not chain:
            return ""
        
        module_depth = defaultdict(int)
        for i, item in enumerate(chain):
            module_depth[item["module"]] += (len(chain) - i)
        
        if module_depth:
            return max(module_depth.items(), key=lambda x: x[1])[0]
        return chain[0]["module"]

    def _get_dependents(self, module: str) -> Set[str]:
        """获取依赖该模块的其他模块"""
        dependents = set()
        for mod, deps in self.module_graph.items():
            if module in deps:
                dependents.add(mod)
        return dependents

    def analyze_module_coupling(self) -> Dict[str, float]:
        """分析模块耦合度"""
        coupling = {}
        
        for module, deps in self.module_graph.items():
            afferent = len(self._get_dependents(module))
            efferent = len(deps)
            
            if afferent + efferent > 0:
                coupling[module] = efferent / (afferent + efferent)
            else:
                coupling[module] = 0.0
        
        return coupling


class EnhancedRootCauseAnalyzer(RootCauseAnalyzer):
    """增强的根因分析器"""

    def __init__(self):
        super().__init__()
        self.analysis_depth = 3
        self.context_window = 10

    def deep_analyze(
        self,
        error_message: str,
        stack_trace: List[StackFrame],
        code_context: Optional[Dict[str, Any]] = None
    ) -> RootCause:
        """深度根因分析"""
        basic_cause = self.analyze(error_message, stack_trace)
        
        if basic_cause.confidence >= 0.8:
            return basic_cause
        
        enhanced_evidence = list(basic_cause.evidence)
        
        if stack_trace:
            project_frames = [f for f in stack_trace if f.is_project_file]
            if project_frames:
                for frame in project_frames[:self.analysis_depth]:
                    frame_analysis = self._analyze_frame(frame)
                    enhanced_evidence.extend(frame_analysis)
        
        if code_context:
            context_analysis = self._analyze_code_context(code_context)
            enhanced_evidence.extend(context_analysis)
        
        pattern_cause = self._match_error_pattern(error_message, stack_trace)
        if pattern_cause:
            return pattern_cause
        
        return RootCause(
            description=basic_cause.description,
            category=basic_cause.category,
            confidence=min(basic_cause.confidence + 0.1, 1.0),
            evidence=enhanced_evidence,
            related_files=basic_cause.related_files,
            suggested_fixes=self._generate_enhanced_fixes(basic_cause, stack_trace)
        )

    def _analyze_frame(self, frame: StackFrame) -> List[str]:
        """分析堆栈帧"""
        evidence = []
        
        try:
            with open(frame.file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            if frame.line_number > 0 and frame.line_number <= len(lines):
                start = max(0, frame.line_number - self.context_window)
                end = min(len(lines), frame.line_number + self.context_window)
                
                for i in range(start, end):
                    line = lines[i].strip()
                    if line and not line.startswith('#'):
                        if 'try' in line or 'except' in line:
                            evidence.append(f"异常处理上下文 (行 {i+1}): {line}")
                        elif 'if' in line or 'for' in line or 'while' in line:
                            evidence.append(f"控制流上下文 (行 {i+1}): {line}")
        
        except Exception:
            pass
        
        return evidence

    def _analyze_code_context(self, context: Dict[str, Any]) -> List[str]:
        """分析代码上下文"""
        evidence = []
        
        if 'variables' in context:
            for var_name, var_value in context['variables'].items():
                if var_value is None:
                    evidence.append(f"变量 '{var_name}' 可能为 None")
                elif isinstance(var_value, str) and not var_value:
                    evidence.append(f"变量 '{var_name}' 为空字符串")
        
        if 'recent_changes' in context:
            for change in context['recent_changes'][:3]:
                evidence.append(f"最近变更: {change}")
        
        return evidence

    def _match_error_pattern(
        self,
        error_message: str,
        stack_trace: List[StackFrame]
    ) -> Optional[RootCause]:
        """匹配错误模式"""
        patterns = [
            {
                "regex": r"cannot access local variable '(\w+)' where it is not associated with a value",
                "category": IssueCategory.LOGIC,
                "cause": "变量 '{group1}' 在赋值前被使用",
                "fix": "确保变量在使用前已正确初始化"
            },
            {
                "regex": r"object is not (?:subscriptable|iterable|callable)",
                "category": IssueCategory.LOGIC,
                "cause": "对象类型不支持该操作",
                "fix": "检查对象类型，确保支持所需操作"
            },
            {
                "regex": r"too many values to unpack",
                "category": IssueCategory.LOGIC,
                "cause": "解包时值的数量不匹配",
                "fix": "检查返回值的数量，确保与变量数量匹配"
            },
            {
                "regex": r"argument of type '(\w+)' is not iterable",
                "category": IssueCategory.LOGIC,
                "cause": "类型 '{group1}' 不可迭代",
                "fix": "使用可迭代类型或添加类型检查"
            },
        ]
        
        for pattern_info in patterns:
            match = re.search(pattern_info["regex"], error_message, re.IGNORECASE)
            if match:
                groups = match.groups()
                cause = pattern_info["cause"]
                fix = pattern_info["fix"]
                
                for i, group in enumerate(groups, 1):
                    cause = cause.replace(f"{{group{i}}}", group)
                    fix = fix.replace(f"{{group{i}}}", group)
                
                return RootCause(
                    description=cause,
                    category=pattern_info["category"],
                    confidence=0.85,
                    evidence=[error_message],
                    related_files={f.file_path for f in stack_trace if f.is_project_file},
                    suggested_fixes=[fix]
                )
        
        return None

    def _generate_enhanced_fixes(
        self,
        basic_cause: RootCause,
        stack_trace: List[StackFrame]
    ) -> List[str]:
        """生成增强的修复建议"""
        fixes = list(basic_cause.suggested_fixes)
        
        if stack_trace:
            project_frames = [f for f in stack_trace if f.is_project_file]
            if project_frames:
                frame = project_frames[0]
                fixes.append(f"在 {frame.file_path}:{frame.line_number} 添加调试日志")
                fixes.append(f"检查函数 {frame.function_name} 的输入参数")
        
        if basic_cause.category == IssueCategory.LOGIC:
            fixes.append("添加单元测试验证逻辑正确性")
        elif basic_cause.category == IssueCategory.PERFORMANCE:
            fixes.append("使用性能分析工具定位瓶颈")
        elif basic_cause.category == IssueCategory.DEPENDENCY:
            fixes.append("检查依赖版本兼容性")
        
        return fixes


class ImpactScopeEvaluator:
    """影响范围评估器"""

    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root).resolve()
        self.code_analyzer = CodeAnalyzer(project_root)

    def evaluate(
        self,
        location: IssueLocation,
        root_cause: RootCause
    ) -> ImpactAnalysis:
        """评估影响范围"""
        impact = ImpactAnalysis()
        
        impact.affected_files.add(location.file_path)
        
        if location.function_name:
            impact.affected_functions.add(location.function_name)
            callers = self.code_analyzer.find_callers(location.function_name)
            impact.downstream_dependencies.update(callers)
        
        module_name = self._get_module_name(location.file_path)
        if module_name:
            impact.affected_modules.add(module_name)
        
        dependents = self._find_file_dependents(location.file_path)
        impact.affected_files.update(dependents)
        
        if root_cause.related_files:
            impact.affected_files.update(root_cause.related_files)
        
        impact.user_impact = self._assess_user_impact(
            location, len(impact.downstream_dependencies)
        )
        
        impact.severity_score = self._calculate_severity_score(impact, root_cause)
        
        return impact

    def _get_module_name(self, file_path: str) -> str:
        """获取模块名称"""
        try:
            rel_path = Path(file_path).relative_to(self.project_root)
            parts = list(rel_path.parts)
            if parts and parts[-1].endswith('.py'):
                parts[-1] = parts[-1][:-3]
            return '.'.join(parts) if parts else ""
        except ValueError:
            return ""

    def _find_file_dependents(self, file_path: str) -> Set[str]:
        """查找文件依赖者"""
        dependents = set()
        file_name = Path(file_path).stem
        
        for py_file in self.project_root.rglob("*.py"):
            if str(py_file) == file_path:
                continue
            
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                import_patterns = [
                    rf'from\s+\S*\.{file_name}\s+import',
                    rf'import\s+\S*\.{file_name}',
                    rf'from\s+{file_name}\s+import',
                    rf'import\s+{file_name}\b',
                ]
                
                for pattern in import_patterns:
                    if re.search(pattern, content):
                        dependents.add(str(py_file))
                        break
            
            except Exception:
                continue
        
        return dependents

    def _assess_user_impact(
        self,
        location: IssueLocation,
        dependent_count: int
    ) -> str:
        """评估用户影响"""
        path_lower = location.file_path.lower()
        
        if any(x in path_lower for x in ['api', 'endpoint', 'route', 'view', 'controller']):
            return "高 - 影响API接口，可能导致服务不可用"
        
        if any(x in path_lower for x in ['auth', 'login', 'security', 'permission']):
            return "高 - 影响认证授权，存在安全风险"
        
        if any(x in path_lower for x in ['payment', 'order', 'transaction']):
            return "高 - 影响核心业务流程"
        
        if any(x in path_lower for x in ['model', 'schema', 'entity']):
            return "中 - 影响数据模型，可能影响多个功能"
        
        if any(x in path_lower for x in ['util', 'helper', 'common', 'lib']):
            return "中 - 影响公共工具，可能影响多个模块"
        
        if any(x in path_lower for x in ['test', 'spec', '__test__']):
            return "低 - 仅影响测试"
        
        if dependent_count > 10:
            return "高 - 被大量模块依赖"
        elif dependent_count > 5:
            return "中 - 被多个模块依赖"
        elif dependent_count > 0:
            return "低 - 被少量模块依赖"
        
        return "低 - 影响范围有限"

    def _calculate_severity_score(
        self,
        impact: ImpactAnalysis,
        root_cause: RootCause
    ) -> float:
        """计算严重程度分数"""
        score = 0.0
        
        score += len(impact.affected_files) * 0.5
        score += len(impact.affected_functions) * 1.0
        score += len(impact.downstream_dependencies) * 0.3
        score += len(impact.affected_modules) * 0.8
        
        severity_multiplier = {
            IssueCategory.SECURITY: 3.0,
            IssueCategory.RUNTIME: 2.0,
            IssueCategory.LOGIC: 1.5,
            IssueCategory.PERFORMANCE: 1.2,
            IssueCategory.DEPENDENCY: 1.0,
            IssueCategory.CONFIGURATION: 0.8,
            IssueCategory.ENVIRONMENT: 0.8,
            IssueCategory.SYNTAX: 1.5,
            IssueCategory.UNKNOWN: 1.0,
        }
        score *= severity_multiplier.get(root_cause.category, 1.0)
        
        if "高" in impact.user_impact:
            score += 10.0
        elif "中" in impact.user_impact:
            score += 5.0
        else:
            score += 1.0
        
        return min(score, 100.0)

    def get_impact_report(self, impact: ImpactAnalysis) -> str:
        """生成影响报告"""
        lines = [
            "## 影响范围分析",
            "",
            f"**用户影响**: {impact.user_impact}",
            f"**严重程度分数**: {impact.severity_score:.1f}/100",
            "",
            "### 影响详情",
            f"- 影响文件: {len(impact.affected_files)} 个",
            f"- 影响函数: {len(impact.affected_functions)} 个",
            f"- 影响模块: {len(impact.affected_modules)} 个",
            f"- 下游依赖: {len(impact.downstream_dependencies)} 个",
        ]
        
        if impact.affected_files:
            lines.extend([
                "",
                "### 受影响文件",
            ])
            for file_path in sorted(impact.affected_files)[:10]:
                lines.append(f"- {file_path}")
            if len(impact.affected_files) > 10:
                lines.append(f"- ... 还有 {len(impact.affected_files) - 10} 个文件")
        
        if impact.downstream_dependencies:
            lines.extend([
                "",
                "### 下游依赖",
            ])
            for dep in sorted(impact.downstream_dependencies)[:10]:
                lines.append(f"- {dep}")
            if len(impact.downstream_dependencies) > 10:
                lines.append(f"- ... 还有 {len(impact.downstream_dependencies) - 10} 个依赖")
        
        return '\n'.join(lines)


class CausalChainAnalyzer:
    """因果链分析器 - 分析问题之间的因果关系"""

    def __init__(self):
        self.causal_graph: Dict[str, Set[str]] = defaultdict(set)
        self.evidence_map: Dict[str, List[str]] = defaultdict(list)
        self.confidence_map: Dict[str, float] = {}

    def add_causal_relation(
        self,
        cause: str,
        effect: str,
        evidence: str,
        confidence: float = 0.7
    ):
        """添加因果关系"""
        self.causal_graph[cause].add(effect)
        self.evidence_map[f"{cause}->{effect}"].append(evidence)
        self.confidence_map[f"{cause}->{effect}"] = confidence

    def find_root_causes(self, effect: str) -> List[Tuple[str, float, List[str]]]:
        """找到导致某个效果的所有根因"""
        root_causes = []
        visited = set()
        
        def dfs(node: str, path: List[str], confidence: float):
            if node in visited:
                return
            visited.add(node)
            
            predecessors = []
            for cause, effects in self.causal_graph.items():
                if node in effects:
                    predecessors.append(cause)
            
            if not predecessors:
                root_causes.append((node, confidence, path.copy()))
            else:
                for pred in predecessors:
                    edge_key = f"{pred}->{node}"
                    edge_confidence = self.confidence_map.get(edge_key, 0.5)
                    new_confidence = confidence * edge_confidence
                    dfs(pred, path + [pred], new_confidence)
        
        dfs(effect, [effect], 1.0)
        root_causes.sort(key=lambda x: x[1], reverse=True)
        return root_causes

    def find_effects(self, cause: str, max_depth: int = 3) -> List[Tuple[str, int, float]]:
        """找到某个原因导致的所有效果"""
        effects = []
        visited = set()
        
        def bfs(start: str, depth: int, cumulative_confidence: float):
            if depth > max_depth or start in visited:
                return
            visited.add(start)
            
            for effect in self.causal_graph.get(start, []):
                edge_key = f"{start}->{effect}"
                edge_confidence = self.confidence_map.get(edge_key, 0.5)
                new_confidence = cumulative_confidence * edge_confidence
                effects.append((effect, depth, new_confidence))
                bfs(effect, depth + 1, new_confidence)
        
        bfs(cause, 1, 1.0)
        return effects

    def get_causal_chain(self, cause: str, effect: str) -> Optional[List[str]]:
        """获取从原因到效果的因果链"""
        visited = set()
        path = []
        
        def dfs(node: str) -> bool:
            if node == effect:
                path.append(node)
                return True
            
            if node in visited:
                return False
            visited.add(node)
            path.append(node)
            
            for next_node in self.causal_graph.get(node, []):
                if dfs(next_node):
                    return True
            
            path.pop()
            return False
        
        if dfs(cause):
            return path
        return None

    def analyze_causal_importance(self) -> Dict[str, float]:
        """分析每个节点的重要性（PageRank风格）"""
        importance = defaultdict(float)
        damping = 0.85
        iterations = 20
        
        all_nodes = set(self.causal_graph.keys())
        for effects in self.causal_graph.values():
            all_nodes.update(effects)
        
        for node in all_nodes:
            importance[node] = 1.0 / len(all_nodes)
        
        for _ in range(iterations):
            new_importance = defaultdict(float)
            for node in all_nodes:
                incoming_sum = 0.0
                for cause, effects in self.causal_graph.items():
                    if node in effects:
                        outgoing_count = len(self.causal_graph[cause])
                        if outgoing_count > 0:
                            incoming_sum += importance[cause] / outgoing_count
                
                new_importance[node] = (1 - damping) / len(all_nodes) + damping * incoming_sum
            
            importance = new_importance
        
        return dict(importance)


class CallStackAnalyzer:
    """调用栈分析器 - 深度分析调用栈"""

    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root).resolve()
        self.call_graph: Dict[str, Set[str]] = defaultdict(set)
        self.function_locations: Dict[str, List[Tuple[str, int]]] = defaultdict(list)

    def build_call_graph(self, file_pattern: str = "*.py"):
        """构建调用图"""
        for py_file in self.project_root.rglob(file_pattern):
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                tree = ast.parse(content)
                
                for node in ast.walk(tree):
                    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        func_name = node.name
                        self.function_locations[func_name].append((str(py_file), node.lineno))
                        
                        for child in ast.walk(node):
                            if isinstance(child, ast.Call):
                                called_func = self._extract_called_function(child)
                                if called_func:
                                    self.call_graph[func_name].add(called_func)
            
            except Exception:
                continue

    def _extract_called_function(self, call_node: ast.Call) -> Optional[str]:
        """提取被调用的函数名"""
        if isinstance(call_node.func, ast.Name):
            return call_node.func.id
        elif isinstance(call_node.func, ast.Attribute):
            return call_node.func.attr
        return None

    def analyze_stack_trace(
        self,
        stack_frames: List[StackFrame]
    ) -> Dict[str, Any]:
        """分析调用栈"""
        analysis = {
            "depth": len(stack_frames),
            "project_frames": [],
            "library_frames": [],
            "call_chain": [],
            "potential_issues": [],
            "suspicious_patterns": []
        }
        
        for frame in stack_frames:
            frame_info = {
                "file": frame.file_path,
                "line": frame.line_number,
                "function": frame.function_name,
                "code": frame.code_snippet
            }
            
            if frame.is_project_file:
                analysis["project_frames"].append(frame_info)
            else:
                analysis["library_frames"].append(frame_info)
        
        if len(analysis["project_frames"]) > 0:
            for i, frame in enumerate(analysis["project_frames"]):
                analysis["call_chain"].append(frame["function"])
        
        if len(stack_frames) > 20:
            analysis["suspicious_patterns"].append({
                "type": "deep_recursion",
                "description": f"调用栈深度过大 ({len(stack_frames)} 层)",
                "severity": "medium"
            })
        
        func_counts = Counter(f.function_name for f in stack_frames)
        for func, count in func_counts.items():
            if count > 3:
                analysis["suspicious_patterns"].append({
                    "type": "repeated_function",
                    "description": f"函数 {func} 在调用栈中出现 {count} 次",
                    "severity": "low"
                })
        
        return analysis

    def find_callers(self, function_name: str, depth: int = 3) -> Set[str]:
        """查找函数的调用者"""
        callers = set()
        
        def _find_callers_recursive(func: str, current_depth: int):
            if current_depth >= depth:
                return
            
            for caller, callees in self.call_graph.items():
                if func in callees:
                    callers.add(caller)
                    _find_callers_recursive(caller, current_depth + 1)
        
        _find_callers_recursive(function_name, 0)
        return callers

    def find_callees(self, function_name: str, depth: int = 3) -> Set[str]:
        """查找函数调用的函数"""
        callees = set()
        
        def _find_callees_recursive(func: str, current_depth: int):
            if current_depth >= depth:
                return
            
            for callee in self.call_graph.get(func, []):
                callees.add(callee)
                _find_callees_recursive(callee, current_depth + 1)
        
        _find_callees_recursive(function_name, 0)
        return callees


class FixSuggestionGenerator:
    """修复建议生成器"""

    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root).resolve()

    def generate(
        self,
        issue: DiagnosedIssue,
        impact: ImpactAnalysis
    ) -> List[Dict[str, Any]]:
        """生成修复建议"""
        suggestions = []
        
        primary_fix = self._generate_primary_fix(issue)
        if primary_fix:
            suggestions.append(primary_fix)
        
        if impact.severity_score > 20:
            quick_fix = self._generate_quick_fix(issue)
            if quick_fix:
                suggestions.append(quick_fix)
        
        preventive_fix = self._generate_preventive_fix(issue)
        if preventive_fix:
            suggestions.append(preventive_fix)
        
        if len(impact.affected_files) > 3:
            refactoring_fix = self._generate_refactoring_fix(issue, impact)
            if refactoring_fix:
                suggestions.append(refactoring_fix)
        
        return suggestions

    def _generate_primary_fix(self, issue: DiagnosedIssue) -> Optional[Dict[str, Any]]:
        """生成主要修复建议"""
        if not issue.root_cause.suggested_fixes:
            return None
        
        return {
            "type": "primary",
            "priority": "high",
            "title": "主要修复方案",
            "description": issue.root_cause.suggested_fixes[0],
            "steps": [
                f"1. 定位问题: {issue.location.file_path}:{issue.location.line_number}",
                f"2. 分析根因: {issue.root_cause.description}",
                f"3. 实施修复: {issue.root_cause.suggested_fixes[0]}",
                "4. 验证修复: 运行相关测试",
            ],
            "estimated_effort": self._estimate_effort(issue),
            "risk_level": self._assess_risk(issue),
        }

    def _generate_quick_fix(self, issue: DiagnosedIssue) -> Optional[Dict[str, Any]]:
        """生成快速修复建议"""
        if issue.category == IssueCategory.RUNTIME:
            return {
                "type": "quick_fix",
                "priority": "high",
                "title": "快速修复（临时方案）",
                "description": "添加异常处理以防止问题扩散",
                "steps": [
                    "1. 在问题位置添加 try-except 块",
                    "2. 记录详细错误日志",
                    "3. 提供降级处理方案",
                    "4. 后续实施完整修复",
                ],
                "code_example": self._generate_exception_handling_code(issue),
                "estimated_effort": "低",
                "risk_level": "低",
            }
        
        return None

    def _generate_preventive_fix(self, issue: DiagnosedIssue) -> Optional[Dict[str, Any]]:
        """生成预防性修复建议"""
        return {
            "type": "preventive",
            "priority": "medium",
            "title": "预防性改进",
            "description": "添加防护措施防止问题再次发生",
            "steps": [
                "1. 添加输入验证",
                "2. 增加边界检查",
                "3. 添加单元测试覆盖",
                "4. 更新文档说明",
            ],
            "test_suggestion": self._generate_test_suggestion(issue),
            "estimated_effort": "中",
            "risk_level": "低",
        }

    def _generate_refactoring_fix(
        self,
        issue: DiagnosedIssue,
        impact: ImpactAnalysis
    ) -> Optional[Dict[str, Any]]:
        """生成重构建议"""
        return {
            "type": "refactoring",
            "priority": "low",
            "title": "代码重构建议",
            "description": "降低模块耦合度，提高代码可维护性",
            "steps": [
                f"1. 分析模块依赖关系（当前影响 {len(impact.affected_files)} 个文件）",
                "2. 提取公共逻辑到独立模块",
                "3. 引入接口抽象降低耦合",
                "4. 逐步迁移和测试",
            ],
            "benefits": [
                "降低未来问题的影响范围",
                "提高代码可测试性",
                "便于后续维护",
            ],
            "estimated_effort": "高",
            "risk_level": "中",
        }

    def _estimate_effort(self, issue: DiagnosedIssue) -> str:
        """估算修复工作量"""
        if issue.severity in [IssueSeverity.CRITICAL, IssueSeverity.HIGH]:
            return "高"
        elif issue.severity == IssueSeverity.MEDIUM:
            return "中"
        return "低"

    def _assess_risk(self, issue: DiagnosedIssue) -> str:
        """评估修复风险"""
        if issue.category == IssueCategory.SECURITY:
            return "高"
        elif issue.category in [IssueCategory.RUNTIME, IssueCategory.LOGIC]:
            return "中"
        return "低"

    def _generate_exception_handling_code(self, issue: DiagnosedIssue) -> str:
        """生成异常处理代码示例"""
        return f'''try:
    # 原有代码: {issue.location.code_snippet[:50] if issue.location.code_snippet else "..."}
    pass
except Exception as e:
    logger.error(f"Error in {issue.location.function_name}: {{e}}")
    # 降级处理
    raise'''

    def _generate_test_suggestion(self, issue: DiagnosedIssue) -> str:
        """生成测试建议"""
        return f'''def test_{issue.location.function_name or "function"}():
    """测试 {issue.location.function_name or "相关功能"}"""
    # 正常情况
    # 边界情况
    # 异常情况
    pass'''


if __name__ == '__main__':
    exit(main())
