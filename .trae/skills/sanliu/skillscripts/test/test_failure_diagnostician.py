#!/usr/bin/env python3
"""
Test Failure Diagnostician - 增强测试失败诊断器

TDD红阶段智能增强组件，支持：
1. 测试失败原因分析
2. 智能诊断建议
3. 诊断报告生成
4. 根因分析
5. 修复建议
6. 失败根因自动分析
7. 问题代码定位
8. 修复建议生成
9. 失败模式识别

使用示例：
    python test_failure_diagnostician.py --pytest-output test_output.txt --diagnose
    python test_failure_diagnostician.py --pytest-output test_output.txt --report diagnosis_report.html
    python test_failure_diagnostician.py --pytest-output test_output.txt --deep-analysis
"""

import argparse
import ast
import json
import logging
import os
import re
import sys
import traceback
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple, Union

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class FailureType(Enum):
    ASSERTION = "assertion"
    EXCEPTION = "exception"
    TIMEOUT = "timeout"
    IMPORT = "import"
    ATTRIBUTE = "attribute"
    TYPE = "type"
    VALUE = "value"
    KEY = "key"
    INDEX = "index"
    FILE_NOT_FOUND = "file_not_found"
    PERMISSION = "permission"
    CONNECTION = "connection"
    SYNTAX = "syntax"
    RECURSION = "recursion"
    MEMORY = "memory"
    UNKNOWN = "unknown"


class Severity(Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class DiagnosticCategory(Enum):
    CODE_ERROR = "code_error"
    TEST_ERROR = "test_error"
    ENVIRONMENT = "environment"
    DATA = "data"
    CONFIGURATION = "configuration"
    DEPENDENCY = "dependency"
    PERFORMANCE = "performance"
    SECURITY = "security"
    NETWORK = "network"
    RESOURCE = "resource"


@dataclass
class StackFrame:
    file_path: str
    line_number: int
    function_name: str
    code_line: str
    context: List[str] = field(default_factory=list)


@dataclass
class FailureContext:
    test_name: str
    test_file: str
    failure_type: FailureType
    error_message: str
    exception_type: Optional[str] = None
    exception_value: Optional[str] = None
    stack_trace: List[StackFrame] = field(default_factory=list)
    local_variables: Dict[str, Any] = field(default_factory=dict)
    test_output: str = ""
    expected_value: Optional[Any] = None
    actual_value: Optional[Any] = None


@dataclass
class DiagnosticFinding:
    finding_id: str
    category: DiagnosticCategory
    severity: Severity
    title: str
    description: str
    evidence: List[str] = field(default_factory=list)
    affected_files: List[str] = field(default_factory=list)
    related_code: List[str] = field(default_factory=list)


@dataclass
class DiagnosticSuggestion:
    suggestion_id: str
    priority: int
    action: str
    rationale: str
    code_example: Optional[str] = None
    references: List[str] = field(default_factory=list)
    estimated_effort: str = "medium"


@dataclass
class RootCauseAnalysis:
    primary_cause: str
    contributing_factors: List[str] = field(default_factory=list)
    cascade_effects: List[str] = field(default_factory=list)
    confidence: float = 0.0
    analysis_path: List[str] = field(default_factory=list)


@dataclass
class DiagnosisReport:
    """诊断报告数据类 - 包含完整的诊断结果
    
    该类存储诊断报告的所有信息，包括：
    1. 报告元数据 - ID、测试名称、生成时间
    2. 失败上下文 - 失败的详细信息
    3. 诊断发现 - 发现的问题列表
    4. 修复建议 - 建议的修复方案
    5. 根因分析 - 根本原因分析结果
    6. 摘要和下一步 - 总结和行动计划
    """
    report_id: str
    test_name: str
    generated_at: str
    failure_context: FailureContext
    findings: List[DiagnosticFinding] = field(default_factory=list)
    suggestions: List[DiagnosticSuggestion] = field(default_factory=list)
    root_cause: Optional[RootCauseAnalysis] = None
    summary: str = ""
    next_steps: List[str] = field(default_factory=list)
    
    def _escape_markdown(self, text: str) -> str:
        """转义Markdown特殊字符 - 防止格式问题
        
        Args:
            text: 原始文本
            
        Returns:
            str: 转义后的文本
        """
        if not text:
            return ""
        text = str(text)
        escape_chars = ['`', '*', '_', '#', '+', '-', '!', '[', ']', '(', ')']
        for char in escape_chars:
            text = text.replace(char, '\\' + char)
        return text


class PytestOutputParser:
    """Pytest输出解析器"""
    
    FAILURE_PATTERNS = {
        "assertion": [
            r"AssertionError:",
            r"assert\s+.*\s*==",
            r"assert\s+.*\s*!=",
            r"assert\s+.*\s*in\s+",
        ],
        "exception": [
            r"(\w+Error):\s*(.+)",
            r"(\w+Exception):\s*(.+)",
            r"Traceback \(most recent call last\):",
        ],
        "timeout": [
            r"TimeoutError",
            r"timed out after",
            r"Timeout exceeded",
        ],
        "import": [
            r"ImportError:",
            r"ModuleNotFoundError:",
            r"cannot import name",
        ],
        "attribute": [
            r"AttributeError:",
            r"has no attribute",
        ],
        "type": [
            r"TypeError:",
            r"unsupported operand type",
            r"'NoneType' object",
        ],
        "value": [
            r"ValueError:",
            r"invalid value",
        ],
        "key": [
            r"KeyError:",
        ],
        "index": [
            r"IndexError:",
            r"list index out of range",
        ],
        "file_not_found": [
            r"FileNotFoundError:",
            r"No such file or directory",
        ],
    }
    
    def parse(self, output: str) -> List[FailureContext]:
        failures = []
        
        failure_blocks = self._extract_failure_blocks(output)
        
        for block in failure_blocks:
            context = self._parse_failure_block(block)
            if context:
                failures.append(context)
        
        return failures
    
    def _extract_failure_blocks(self, output: str) -> List[str]:
        blocks = []
        pattern = r"(FAILED|ERROR)[^\n]*\n((?:.*\n)*?)(?=(?:FAILED|ERROR|=+$)|$)"
        
        for match in re.finditer(pattern, output, re.MULTILINE):
            blocks.append(match.group(0))
        
        return blocks
    
    def _parse_failure_block(self, block: str) -> Optional[FailureContext]:
        lines = block.strip().split("\n")
        if not lines:
            return None
        
        test_match = re.match(r"(FAILED|ERROR)\s+([^\s]+)", lines[0])
        if not test_match:
            return None
        
        test_name = test_match.group(2)
        
        test_file = ""
        file_match = re.search(r"File\s+\"([^\"]+)\"", block)
        if file_match:
            test_file = file_match.group(1)
        
        failure_type = self._detect_failure_type(block)
        
        error_message = self._extract_error_message(block)
        
        exception_type = None
        exception_value = None
        exc_match = re.search(r"(\w+(?:Error|Exception)):\s*(.+)", block)
        if exc_match:
            exception_type = exc_match.group(1)
            exception_value = exc_match.group(2)
        
        stack_trace = self._extract_stack_trace(block)
        
        expected_value, actual_value = self._extract_assertion_values(block)
        
        return FailureContext(
            test_name=test_name,
            test_file=test_file,
            failure_type=failure_type,
            error_message=error_message,
            exception_type=exception_type,
            exception_value=exception_value,
            stack_trace=stack_trace,
            test_output=block,
            expected_value=expected_value,
            actual_value=actual_value
        )
    
    def _detect_failure_type(self, block: str) -> FailureType:
        for failure_type, patterns in self.FAILURE_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, block, re.IGNORECASE):
                    return FailureType(failure_type)
        
        return FailureType.UNKNOWN
    
    def _extract_error_message(self, block: str) -> str:
        lines = block.strip().split("\n")
        for line in reversed(lines):
            line = line.strip()
            if line and not line.startswith((" ", "\t", "File", "During", "Traceback")):
                if re.search(r"(Error|Exception|assert)", line):
                    return line
        
        return "Unknown error"
    
    def _extract_stack_trace(self, block: str) -> List[StackFrame]:
        frames = []
        pattern = r'File\s+"([^"]+)",\s+line\s+(\d+),\s+in\s+(\w+)\s*\n\s*(.+)'
        
        for match in re.finditer(pattern, block):
            frames.append(StackFrame(
                file_path=match.group(1),
                line_number=int(match.group(2)),
                function_name=match.group(3),
                code_line=match.group(4).strip()
            ))
        
        return frames
    
    def _extract_assertion_values(self, block: str) -> Tuple[Optional[str], Optional[str]]:
        expected = None
        actual = None
        
        assert_match = re.search(r"assert\s+(.+?)\s*==\s*(.+)", block)
        if assert_match:
            actual = assert_match.group(1).strip()
            expected = assert_match.group(2).strip()
            return expected, actual
        
        assert_match = re.search(r"Expected:\s*(.+?)\nActual:\s*(.+)", block, re.IGNORECASE)
        if assert_match:
            expected = assert_match.group(1).strip()
            actual = assert_match.group(2).strip()
            return expected, actual
        
        return expected, actual


class FailureAnalyzer:
    """失败分析器"""
    
    ANALYSIS_RULES = {
        FailureType.ASSERTION: {
            "category": DiagnosticCategory.TEST_ERROR,
            "severity": Severity.MEDIUM,
            "common_causes": [
                "预期值与实际值不匹配",
                "测试数据不正确",
                "业务逻辑实现有误",
                "断言条件过于严格"
            ]
        },
        FailureType.EXCEPTION: {
            "category": DiagnosticCategory.CODE_ERROR,
            "severity": Severity.HIGH,
            "common_causes": [
                "未处理的异常情况",
                "边界条件未考虑",
                "依赖服务不可用",
                "资源竞争问题"
            ]
        },
        FailureType.TIMEOUT: {
            "category": DiagnosticCategory.PERFORMANCE,
            "severity": Severity.HIGH,
            "common_causes": [
                "操作耗时过长",
                "死锁或无限循环",
                "外部服务响应慢",
                "资源不足"
            ]
        },
        FailureType.IMPORT: {
            "category": DiagnosticCategory.DEPENDENCY,
            "severity": Severity.CRITICAL,
            "common_causes": [
                "模块未安装",
                "模块路径错误",
                "虚拟环境问题",
                "包版本不兼容"
            ]
        },
        FailureType.ATTRIBUTE: {
            "category": DiagnosticCategory.CODE_ERROR,
            "severity": Severity.HIGH,
            "common_causes": [
                "对象属性不存在",
                "拼写错误",
                "类型不匹配",
                "对象未正确初始化"
            ]
        },
        FailureType.TYPE: {
            "category": DiagnosticCategory.CODE_ERROR,
            "severity": Severity.HIGH,
            "common_causes": [
                "类型不匹配",
                "None值处理不当",
                "参数类型错误",
                "返回类型错误"
            ]
        },
        FailureType.VALUE: {
            "category": DiagnosticCategory.DATA,
            "severity": Severity.MEDIUM,
            "common_causes": [
                "输入值无效",
                "参数范围错误",
                "格式不正确",
                "空值处理问题"
            ]
        },
        FailureType.KEY: {
            "category": DiagnosticCategory.DATA,
            "severity": Severity.MEDIUM,
            "common_causes": [
                "字典键不存在",
                "键名拼写错误",
                "数据结构变更",
                "数据缺失"
            ]
        },
        FailureType.INDEX: {
            "category": DiagnosticCategory.DATA,
            "severity": Severity.MEDIUM,
            "common_causes": [
                "数组越界",
                "列表为空",
                "索引计算错误",
                "数据长度不匹配"
            ]
        },
        FailureType.FILE_NOT_FOUND: {
            "category": DiagnosticCategory.ENVIRONMENT,
            "severity": Severity.HIGH,
            "common_causes": [
                "文件路径错误",
                "文件未创建",
                "权限问题",
                "工作目录不正确"
            ]
        }
    }
    
    def __init__(self):
        self.finding_counter = 0
    
    def analyze(self, context: FailureContext) -> List[DiagnosticFinding]:
        findings = []
        
        rule = self.ANALYSIS_RULES.get(context.failure_type, {})
        
        self.finding_counter += 1
        primary_finding = DiagnosticFinding(
            finding_id=f"DF-{self.finding_counter:03d}",
            category=rule.get("category", DiagnosticCategory.CODE_ERROR),
            severity=rule.get("severity", Severity.MEDIUM),
            title=f"{context.failure_type.value.upper()} 失败分析",
            description=f"测试 '{context.test_name}' 因 {context.failure_type.value} 类型错误而失败",
            evidence=[context.error_message],
            affected_files=[context.test_file] if context.test_file else []
        )
        findings.append(primary_finding)
        
        if context.stack_trace:
            self.finding_counter += 1
            stack_finding = self._analyze_stack_trace(context)
            if stack_finding:
                findings.append(stack_finding)
        
        if context.expected_value and context.actual_value:
            self.finding_counter += 1
            value_finding = self._analyze_value_mismatch(context)
            if value_finding:
                findings.append(value_finding)
        
        if context.exception_type:
            self.finding_counter += 1
            exception_finding = self._analyze_exception(context)
            if exception_finding:
                findings.append(exception_finding)
        
        return findings
    
    def _analyze_stack_trace(self, context: FailureContext) -> Optional[DiagnosticFinding]:
        if not context.stack_trace:
            return None
        
        user_frames = [
            f for f in context.stack_trace
            if not any(skip in f.file_path for skip in ["site-packages", "lib/python", "pytest"])
        ]
        
        if not user_frames:
            return None
        
        top_frame = user_frames[0]
        
        return DiagnosticFinding(
            finding_id=f"DF-{self.finding_counter:03d}",
            category=DiagnosticCategory.CODE_ERROR,
            severity=Severity.HIGH,
            title="错误发生位置",
            description=f"错误发生在 {top_frame.file_path}:{top_frame.line_number}，函数 {top_frame.function_name}",
            evidence=[f"代码行: {top_frame.code_line}"],
            affected_files=[top_frame.file_path],
            related_code=[top_frame.code_line]
        )
    
    def _analyze_value_mismatch(self, context: FailureContext) -> Optional[DiagnosticFinding]:
        if not context.expected_value or not context.actual_value:
            return None
        
        expected_type = type(context.expected_value).__name__
        actual_type = type(context.actual_value).__name__
        
        if expected_type != actual_type:
            return DiagnosticFinding(
                finding_id=f"DF-{self.finding_counter:03d}",
                category=DiagnosticCategory.CODE_ERROR,
                severity=Severity.HIGH,
                title="类型不匹配",
                description=f"预期类型 {expected_type} 与实际类型 {actual_type} 不匹配",
                evidence=[
                    f"预期值: {context.expected_value} ({expected_type})",
                    f"实际值: {context.actual_value} ({actual_type})"
                ],
                affected_files=[context.test_file] if context.test_file else []
            )
        
        return DiagnosticFinding(
            finding_id=f"DF-{self.finding_counter:03d}",
            category=DiagnosticCategory.TEST_ERROR,
            severity=Severity.MEDIUM,
            title="值不匹配",
            description="预期值与实际值不一致",
            evidence=[
                f"预期: {context.expected_value}",
                f"实际: {context.actual_value}"
            ],
            affected_files=[context.test_file] if context.test_file else []
        )
    
    def _analyze_exception(self, context: FailureContext) -> Optional[DiagnosticFinding]:
        if not context.exception_type:
            return None
        
        exception_insights = {
            "AssertionError": "断言失败，检查测试预期是否正确",
            "TypeError": "类型错误，检查参数类型和返回值类型",
            "ValueError": "值错误，检查输入值的有效性",
            "KeyError": "键错误，检查字典键是否存在",
            "IndexError": "索引错误，检查数组/列表边界",
            "AttributeError": "属性错误，检查对象是否有该属性",
            "ImportError": "导入错误，检查模块是否安装",
            "FileNotFoundError": "文件未找到，检查文件路径",
            "PermissionError": "权限错误，检查文件/目录权限",
            "TimeoutError": "超时错误，检查操作是否耗时过长",
            "ConnectionError": "连接错误，检查网络和服务状态"
        }
        
        insight = exception_insights.get(context.exception_type, "未知异常类型")
        
        return DiagnosticFinding(
            finding_id=f"DF-{self.finding_counter:03d}",
            category=DiagnosticCategory.CODE_ERROR,
            severity=Severity.HIGH,
            title=f"异常分析: {context.exception_type}",
            description=insight,
            evidence=[f"异常信息: {context.exception_value or '无详细信息'}"],
            affected_files=[context.test_file] if context.test_file else []
        )


class SuggestionGenerator:
    """诊断建议生成器"""
    
    SUGGESTION_TEMPLATES = {
        FailureType.ASSERTION: [
            {
                "action": "检查测试数据",
                "rationale": "验证测试输入数据是否符合预期",
                "code_example": "# 打印实际值进行调试\nprint(f\"Actual: {actual}\")\nprint(f\"Expected: {expected}\")"
            },
            {
                "action": "放宽断言条件",
                "rationale": "如果断言过于严格，考虑使用更灵活的匹配",
                "code_example": "# 使用近似匹配\nassert abs(actual - expected) < 0.001"
            },
            {
                "action": "检查业务逻辑",
                "rationale": "验证被测代码的业务逻辑是否正确实现"
            }
        ],
        FailureType.EXCEPTION: [
            {
                "action": "添加异常处理",
                "rationale": "为可能抛出异常的代码添加try-except块",
                "code_example": "try:\n    result = risky_operation()\nexcept ExpectedException as e:\n    handle_error(e)"
            },
            {
                "action": "检查边界条件",
                "rationale": "验证输入参数的边界值处理"
            },
            {
                "action": "添加前置检查",
                "rationale": "在操作前验证必要条件"
            }
        ],
        FailureType.IMPORT: [
            {
                "action": "安装缺失模块",
                "rationale": "使用pip安装所需的模块",
                "code_example": "pip install module_name"
            },
            {
                "action": "检查模块路径",
                "rationale": "验证模块是否在Python路径中"
            },
            {
                "action": "检查虚拟环境",
                "rationale": "确认在正确的虚拟环境中运行"
            }
        ],
        FailureType.ATTRIBUTE: [
            {
                "action": "检查对象初始化",
                "rationale": "确保对象在使用前已正确初始化"
            },
            {
                "action": "验证属性名称",
                "rationale": "检查属性名拼写是否正确"
            },
            {
                "action": "检查对象类型",
                "rationale": "确认对象是预期的类型"
            }
        ],
        FailureType.TYPE: [
            {
                "action": "添加类型检查",
                "rationale": "在关键位置添加类型验证",
                "code_example": "if not isinstance(value, ExpectedType):\n    raise TypeError(f\"Expected {ExpectedType}, got {type(value)}\")"
            },
            {
                "action": "处理None值",
                "rationale": "添加None值检查和处理"
            },
            {
                "action": "使用类型转换",
                "rationale": "必要时进行显式类型转换"
            }
        ],
        FailureType.VALUE: [
            {
                "action": "添加值验证",
                "rationale": "在处理前验证输入值的有效性"
            },
            {
                "action": "提供默认值",
                "rationale": "为可选参数提供合理的默认值"
            }
        ],
        FailureType.KEY: [
            {
                "action": "使用get方法",
                "rationale": "使用dict.get()避免KeyError",
                "code_example": "value = my_dict.get('key', default_value)"
            },
            {
                "action": "检查键存在",
                "rationale": "使用in操作符检查键是否存在"
            }
        ],
        FailureType.INDEX: [
            {
                "action": "添加边界检查",
                "rationale": "访问前检查索引是否有效"
            },
            {
                "action": "使用切片",
                "rationale": "使用切片避免索引越界"
            }
        ],
        FailureType.FILE_NOT_FOUND: [
            {
                "action": "检查文件路径",
                "rationale": "验证文件路径是否正确"
            },
            {
                "action": "使用Path对象",
                "rationale": "使用pathlib处理路径",
                "code_example": "from pathlib import Path\nfile_path = Path('data') / 'file.txt'"
            }
        ]
    }
    
    def __init__(self):
        self.suggestion_counter = 0
    
    def generate(self, context: FailureContext, findings: List[DiagnosticFinding]) -> List[DiagnosticSuggestion]:
        suggestions = []
        
        templates = self.SUGGESTION_TEMPLATES.get(context.failure_type, [])
        
        for i, template in enumerate(templates):
            self.suggestion_counter += 1
            suggestion = DiagnosticSuggestion(
                suggestion_id=f"DS-{self.suggestion_counter:03d}",
                priority=i + 1,
                action=template.get("action", ""),
                rationale=template.get("rationale", ""),
                code_example=template.get("code_example"),
                estimated_effort="low" if i == 0 else "medium"
            )
            suggestions.append(suggestion)
        
        for finding in findings:
            if finding.severity in [Severity.CRITICAL, Severity.HIGH]:
                self.suggestion_counter += 1
                suggestions.append(DiagnosticSuggestion(
                    suggestion_id=f"DS-{self.suggestion_counter:03d}",
                    priority=1,
                    action=f"优先处理: {finding.title}",
                    rationale=finding.description,
                    estimated_effort="high"
                ))
        
        return sorted(suggestions, key=lambda s: s.priority)


class RootCauseAnalyzer:
    """根因分析器 - 深度分析测试失败的根本原因
    
    该类负责深入分析测试失败的根因，包括：
    1. 主要原因识别 - 识别导致失败的最直接原因
    2. 促成因素分析 - 分析导致失败的其他相关因素
    3. 级联效应分析 - 分析错误传播路径
    4. 置信度计算 - 评估分析结果的可信程度
    5. 分析路径构建 - 构建完整的分析推理链
    """
    
    def __init__(self):
        self._analysis_cache: Dict[str, RootCauseAnalysis] = {}
        self._call_chain_analyzer = CallChainAnalyzer()
        self._data_flow_analyzer = DataFlowAnalyzer()
        self._environment_analyzer = EnvironmentFactorAnalyzer()
    
    def analyze(self, context: FailureContext, findings: List[DiagnosticFinding]) -> RootCauseAnalysis:
        """执行根因分析
        
        Args:
            context: 失败上下文，包含测试失败的详细信息
            findings: 诊断发现列表，包含已识别的问题
            
        Returns:
            RootCauseAnalysis: 根因分析结果
        """
        primary_cause = self._identify_primary_cause(context, findings)
        contributing_factors = self._identify_contributing_factors(context, findings)
        cascade_effects = self._identify_cascade_effects(context, findings)
        confidence = self._calculate_confidence(context, findings)
        analysis_path = self._build_analysis_path(context, findings)
        
        deep_analysis = self._perform_deep_analysis(context, findings)
        contributing_factors.extend(deep_analysis.get("contributing_factors", []))
        cascade_effects.extend(deep_analysis.get("cascade_effects", []))
        
        contributing_factors = list(dict.fromkeys(contributing_factors))[:10]
        cascade_effects = list(dict.fromkeys(cascade_effects))[:8]
        
        return RootCauseAnalysis(
            primary_cause=primary_cause,
            contributing_factors=contributing_factors,
            cascade_effects=cascade_effects,
            confidence=confidence,
            analysis_path=analysis_path
        )
    
    def _identify_primary_cause(self, context: FailureContext, findings: List[DiagnosticFinding]) -> str:
        """识别主要原因 - 分析导致测试失败的最直接原因
        
        根据失败类型和上下文信息，识别出最可能的根本原因。
        使用多层分析策略，从最具体到最一般逐步识别。
        
        Args:
            context: 失败上下文
            findings: 诊断发现列表
            
        Returns:
            str: 主要原因描述
        """
        if context.failure_type == FailureType.ASSERTION:
            if context.expected_value and context.actual_value:
                return f"断言失败: 预期 {context.expected_value} 但实际为 {context.actual_value}"
            return f"断言失败: {context.error_message}"
        
        if context.failure_type == FailureType.EXCEPTION:
            exception_info = context.exception_type or 'Unknown'
            exception_detail = f" - {context.exception_value}" if context.exception_value else ""
            return f"未处理的异常: {exception_info}{exception_detail}"
        
        if context.failure_type == FailureType.IMPORT:
            module_name = self._extract_module_name(context.error_message)
            return f"模块导入失败: {module_name}"
        
        if context.failure_type == FailureType.TYPE:
            type_info = self._extract_type_info(context.error_message)
            return f"类型错误: {type_info}"
        
        if context.failure_type == FailureType.ATTRIBUTE:
            attr_info = self._extract_attribute_info(context.error_message)
            return f"属性错误: {attr_info}"
        
        if context.failure_type == FailureType.KEY:
            key_info = self._extract_key_info(context.error_message)
            return f"键错误: {key_info}"
        
        if context.failure_type == FailureType.INDEX:
            index_info = self._extract_index_info(context.error_message)
            return f"索引错误: {index_info}"
        
        if context.stack_trace:
            top_frame = context.stack_trace[0]
            return f"代码错误在 {top_frame.file_path}:{top_frame.line_number} ({top_frame.function_name})"
        
        return context.error_message
    
    def _identify_contributing_factors(self, context: FailureContext, findings: List[DiagnosticFinding]) -> List[str]:
        """识别促成因素 - 分析导致失败的相关因素
        
        除了主要原因外，还可能存在其他促成因素，
        如环境问题、依赖问题、数据问题等。
        
        Args:
            context: 失败上下文
            findings: 诊断发现列表
            
        Returns:
            List[str]: 促成因素列表
        """
        factors = []
        
        for finding in findings:
            if finding.category == DiagnosticCategory.ENVIRONMENT:
                factors.append(f"环境问题: {finding.title}")
            elif finding.category == DiagnosticCategory.DEPENDENCY:
                factors.append(f"依赖问题: {finding.title}")
            elif finding.category == DiagnosticCategory.DATA:
                factors.append(f"数据问题: {finding.title}")
            elif finding.category == DiagnosticCategory.CONFIGURATION:
                factors.append(f"配置问题: {finding.title}")
        
        if context.expected_value and context.actual_value:
            type_mismatch = type(context.expected_value) != type(context.actual_value)
            if type_mismatch:
                factors.append(f"类型不匹配: 预期 {type(context.expected_value).__name__}, 实际 {type(context.actual_value).__name__}")
            else:
                factors.append("预期值与实际值不匹配")
        
        if context.stack_trace and len(context.stack_trace) > 5:
            factors.append("调用链较深，可能存在多层抽象问题")
        
        if context.failure_type == FailureType.TIMEOUT:
            factors.append("可能存在性能瓶颈或死锁")
        
        return factors
    
    def _identify_cascade_effects(self, context: FailureContext, findings: List[DiagnosticFinding]) -> List[str]:
        """识别级联效应 - 分析错误传播路径
        
        一个错误可能导致其他错误，形成级联效应。
        分析这种传播路径有助于理解问题的全貌。
        
        Args:
            context: 失败上下文
            findings: 诊断发现列表
            
        Returns:
            List[str]: 级联效应列表
        """
        effects = []
        
        if len(context.stack_trace) > 3:
            effects.append("错误在调用链中传播")
            for i, frame in enumerate(context.stack_trace[:3]):
                effects.append(f"  -> {frame.file_path}:{frame.line_number} in {frame.function_name}()")
        
        for finding in findings:
            if finding.severity in [Severity.CRITICAL, Severity.HIGH]:
                effects.append(f"可能导致: {finding.title}")
        
        if context.failure_type == FailureType.EXCEPTION:
            effects.append("异常可能导致后续操作失败")
        
        return effects[:5]
    
    def _calculate_confidence(self, context: FailureContext, findings: List[DiagnosticFinding]) -> float:
        """计算置信度 - 评估分析结果的可信程度
        
        根据可用信息的完整性和质量，计算分析结果的置信度。
        置信度越高，分析结果越可靠。
        
        Args:
            context: 失败上下文
            findings: 诊断发现列表
            
        Returns:
            float: 置信度 (0.0 - 1.0)
        """
        confidence = 0.5
        
        if context.failure_type != FailureType.UNKNOWN:
            confidence += 0.15
        
        if context.stack_trace:
            confidence += 0.1
            if len(context.stack_trace) > 0:
                confidence += 0.05
        
        if context.error_message:
            confidence += 0.05
        
        if context.exception_type:
            confidence += 0.05
        
        if context.expected_value is not None and context.actual_value is not None:
            confidence += 0.05
        
        if len(findings) > 0:
            confidence += min(0.05 * len(findings), 0.1)
        
        critical_findings = sum(1 for f in findings if f.severity == Severity.CRITICAL)
        if critical_findings > 0:
            confidence += 0.05
        
        return min(confidence, 1.0)
    
    def _build_analysis_path(self, context: FailureContext, findings: List[DiagnosticFinding]) -> List[str]:
        """构建分析路径 - 构建完整的分析推理链
        
        记录分析的步骤和推理过程，便于理解和验证分析结果。
        
        Args:
            context: 失败上下文
            findings: 诊断发现列表
            
        Returns:
            List[str]: 分析路径步骤列表
        """
        path = []
        
        path.append(f"1. 检测到测试失败: {context.test_name}")
        path.append(f"2. 失败类型: {context.failure_type.value}")
        
        if context.stack_trace:
            path.append(f"3. 错误位置: {context.stack_trace[0].file_path}:{context.stack_trace[0].line_number}")
        
        if findings:
            path.append(f"4. 发现 {len(findings)} 个诊断结果")
        
        if context.exception_type:
            path.append(f"5. 异常类型: {context.exception_type}")
        
        if context.expected_value and context.actual_value:
            path.append(f"6. 值比较: 预期={context.expected_value}, 实际={context.actual_value}")
        
        return path
    
    def _perform_deep_analysis(self, context: FailureContext, findings: List[DiagnosticFinding]) -> Dict[str, List[str]]:
        """执行深度分析 - 进行更深入的分析
        
        使用多种分析器进行深度分析，包括：
        1. 调用链分析 - 分析函数调用关系
        2. 数据流分析 - 分析数据传递过程
        3. 环境因素分析 - 分析环境相关因素
        
        Args:
            context: 失败上下文
            findings: 诊断发现列表
            
        Returns:
            Dict[str, List[str]]: 深度分析结果
        """
        result = {
            "contributing_factors": [],
            "cascade_effects": []
        }
        
        call_chain_result = self._call_chain_analyzer.analyze(context)
        result["contributing_factors"].extend(call_chain_result.get("factors", []))
        result["cascade_effects"].extend(call_chain_result.get("effects", []))
        
        data_flow_result = self._data_flow_analyzer.analyze(context)
        result["contributing_factors"].extend(data_flow_result.get("factors", []))
        
        env_result = self._environment_analyzer.analyze(context)
        result["contributing_factors"].extend(env_result.get("factors", []))
        
        return result
    
    def _extract_module_name(self, error_message: str) -> str:
        """从错误消息中提取模块名称"""
        match = re.search(r"No module named '([^']+)'", error_message)
        if match:
            return match.group(1)
        match = re.search(r"cannot import name '([^']+)'", error_message)
        if match:
            return match.group(1)
        return "未知模块"
    
    def _extract_type_info(self, error_message: str) -> str:
        """从错误消息中提取类型信息"""
        match = re.search(r"unsupported operand type\(s\)", error_message)
        if match:
            return "不支持的操作数类型"
        match = re.search(r"'(\w+)' object", error_message)
        if match:
            return f"涉及 {match.group(1)} 类型对象"
        return error_message[:50]
    
    def _extract_attribute_info(self, error_message: str) -> str:
        """从错误消息中提取属性信息"""
        match = re.search(r"'(\w+)' object has no attribute '([^']+)'", error_message)
        if match:
            return f"{match.group(1)} 对象没有属性 '{match.group(2)}'"
        return error_message[:50]
    
    def _extract_key_info(self, error_message: str) -> str:
        """从错误消息中提取键信息"""
        match = re.search(r"KeyError: '?([^']*)'?", error_message)
        if match:
            return f"键 '{match.group(1)}' 不存在"
        return error_message[:50]
    
    def _extract_index_info(self, error_message: str) -> str:
        """从错误消息中提取索引信息"""
        match = re.search(r"index out of range", error_message)
        if match:
            return "索引超出范围"
        return error_message[:50]


class CallChainAnalyzer:
    """调用链分析器 - 分析函数调用关系和错误传播路径
    
    该类负责分析测试失败时的调用链，识别：
    1. 调用深度和复杂度
    2. 关键调用节点
    3. 错误传播路径
    """
    
    def analyze(self, context: FailureContext) -> Dict[str, List[str]]:
        """分析调用链
        
        Args:
            context: 失败上下文
            
        Returns:
            Dict[str, List[str]]: 分析结果
        """
        result = {
            "factors": [],
            "effects": []
        }
        
        if not context.stack_trace:
            return result
        
        user_frames = [
            f for f in context.stack_trace
            if not any(skip in f.file_path for skip in ["site-packages", "lib/python", "pytest"])
        ]
        
        if len(user_frames) > 5:
            result["factors"].append("调用链较深，可能存在过度抽象")
        
        if len(user_frames) > 1:
            result["effects"].append(
                f"错误从 {user_frames[-1].function_name}() 传播到 {user_frames[0].function_name}()"
            )
        
        recursive_calls = self._detect_recursion(user_frames)
        if recursive_calls:
            result["factors"].append(f"检测到递归调用: {recursive_calls}")
        
        return result
    
    def _detect_recursion(self, frames: List[StackFrame]) -> Optional[str]:
        """检测递归调用"""
        function_counts = defaultdict(int)
        for frame in frames:
            function_counts[frame.function_name] += 1
        
        for func, count in function_counts.items():
            if count > 2:
                return func
        return None


class DataFlowAnalyzer:
    """数据流分析器 - 分析数据传递和转换过程
    
    该类负责分析测试失败时的数据流，识别：
    1. 数据转换问题
    2. 数据完整性问题
    3. 数据类型不匹配
    """
    
    def analyze(self, context: FailureContext) -> Dict[str, List[str]]:
        """分析数据流
        
        Args:
            context: 失败上下文
            
        Returns:
            Dict[str, List[str]]: 分析结果
        """
        result = {
            "factors": []
        }
        
        if context.expected_value and context.actual_value:
            expected_type = type(context.expected_value).__name__
            actual_type = type(context.actual_value).__name__
            
            if expected_type != actual_type:
                result["factors"].append(
                    f"数据类型转换问题: {actual_type} -> {expected_type}"
                )
            
            if isinstance(context.expected_value, (list, dict, str)):
                expected_len = len(context.expected_value)
                actual_len = len(context.actual_value) if context.actual_value else 0
                if expected_len != actual_len:
                    result["factors"].append(
                        f"数据长度不匹配: 预期 {expected_len}, 实际 {actual_len}"
                    )
        
        if context.failure_type == FailureType.KEY:
            result["factors"].append("数据结构可能已变更或数据缺失")
        
        if context.failure_type == FailureType.INDEX:
            result["factors"].append("数据集合可能为空或索引计算错误")
        
        return result


class EnvironmentFactorAnalyzer:
    """环境因素分析器 - 分析环境相关因素
    
    该类负责分析测试失败时的环境因素，识别：
    1. 文件系统问题
    2. 网络连接问题
    3. 资源可用性问题
    """
    
    def analyze(self, context: FailureContext) -> Dict[str, List[str]]:
        """分析环境因素
        
        Args:
            context: 失败上下文
            
        Returns:
            Dict[str, List[str]]: 分析结果
        """
        result = {
            "factors": []
        }
        
        if context.failure_type == FailureType.FILE_NOT_FOUND:
            result["factors"].append("文件系统资源不可用")
        
        if context.failure_type == FailureType.CONNECTION:
            result["factors"].append("网络连接或服务不可用")
        
        if context.failure_type == FailureType.TIMEOUT:
            result["factors"].append("系统资源可能不足或存在性能瓶颈")
        
        if context.failure_type == FailureType.PERMISSION:
            result["factors"].append("权限配置问题")
        
        if context.failure_type == FailureType.IMPORT:
            result["factors"].append("Python环境或依赖配置问题")
        
        return result


class TestFailureDiagnostician:
    """测试失败诊断器主类"""
    
    def __init__(self):
        self.output_parser = PytestOutputParser()
        self.failure_analyzer = FailureAnalyzer()
        self.suggestion_generator = SuggestionGenerator()
        self.root_cause_analyzer = RootCauseAnalyzer()
        self.report_counter = 0
    
    def diagnose(self, pytest_output: str) -> List[DiagnosisReport]:
        failure_contexts = self.output_parser.parse(pytest_output)
        
        reports = []
        for context in failure_contexts:
            report = self._create_diagnosis_report(context)
            reports.append(report)
        
        return reports
    
    def diagnose_from_file(self, file_path: str) -> List[DiagnosisReport]:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
        
        return self.diagnose(content)
    
    def _create_diagnosis_report(self, context: FailureContext) -> DiagnosisReport:
        self.report_counter += 1
        
        findings = self.failure_analyzer.analyze(context)
        suggestions = self.suggestion_generator.generate(context, findings)
        root_cause = self.root_cause_analyzer.analyze(context, findings)
        
        summary = self._generate_summary(context, findings, root_cause)
        next_steps = self._generate_next_steps(suggestions)
        
        return DiagnosisReport(
            report_id=f"DR-{datetime.now().strftime('%Y%m%d%H%M%S')}-{self.report_counter:03d}",
            test_name=context.test_name,
            generated_at=datetime.now().isoformat(),
            failure_context=context,
            findings=findings,
            suggestions=suggestions,
            root_cause=root_cause,
            summary=summary,
            next_steps=next_steps
        )
    
    def _generate_summary(self, context: FailureContext, findings: List[DiagnosticFinding], root_cause: RootCauseAnalysis) -> str:
        severity_counts = defaultdict(int)
        for f in findings:
            severity_counts[f.severity.value] += 1
        
        summary_parts = [
            f"测试 '{context.test_name}' 失败诊断完成。",
            f"失败类型: {context.failure_type.value}。",
            f"根因: {root_cause.primary_cause}。",
            f"置信度: {root_cause.confidence:.0%}。"
        ]
        
        if severity_counts:
            severity_str = ", ".join(f"{k}: {v}" for k, v in severity_counts.items())
            summary_parts.append(f"发现: {severity_str}。")
        
        return " ".join(summary_parts)
    
    def _generate_next_steps(self, suggestions: List[DiagnosticSuggestion]) -> List[str]:
        return [s.action for s in suggestions[:5]]
    
    def generate_report_markdown(self, report: DiagnosisReport) -> str:
        lines = [
            f"# 测试失败诊断报告",
            "",
            f"**报告ID**: {report.report_id}",
            f"**测试名称**: {report.test_name}",
            f"**生成时间**: {report.generated_at}",
            "",
            "## 摘要",
            "",
            report.summary,
            "",
            "## 失败详情",
            "",
            f"- **失败类型**: {report.failure_context.failure_type.value}",
            f"- **错误消息**: {report.failure_context.error_message}",
        ]
        
        if report.failure_context.exception_type:
            lines.extend([
                f"- **异常类型**: {report.failure_context.exception_type}",
                f"- **异常值**: {report.failure_context.exception_value}",
            ])
        
        if report.failure_context.expected_value and report.failure_context.actual_value:
            lines.extend([
                f"- **预期值**: {report.failure_context.expected_value}",
                f"- **实际值**: {report.failure_context.actual_value}",
            ])
        
        lines.extend([
            "",
            "## 诊断发现",
            "",
        ])
        
        for finding in report.findings:
            lines.extend([
                f"### {finding.title}",
                "",
                f"- **类别**: {finding.category.value}",
                f"- **严重性**: {finding.severity.value}",
                f"- **描述**: {finding.description}",
            ])
            
            if finding.evidence:
                lines.append("- **证据**:")
                for e in finding.evidence:
                    lines.append(f"  - {e}")
            
            if finding.affected_files:
                lines.append(f"- **影响文件**: {', '.join(finding.affected_files)}")
            
            lines.append("")
        
        lines.extend([
            "## 根因分析",
            "",
            f"- **主要原因**: {report.root_cause.primary_cause}",
            f"- **置信度**: {report.root_cause.confidence:.0%}",
        ])
        
        if report.root_cause.contributing_factors:
            lines.append("- **促成因素**:")
            for factor in report.root_cause.contributing_factors:
                lines.append(f"  - {factor}")
        
        if report.root_cause.analysis_path:
            lines.append("- **分析路径**:")
            for step in report.root_cause.analysis_path:
                lines.append(f"  - {step}")
        
        lines.extend([
            "",
            "## 修复建议",
            "",
        ])
        
        for suggestion in report.suggestions:
            lines.extend([
                f"### 建议 {suggestion.priority}: {suggestion.action}",
                "",
                f"**理由**: {suggestion.rationale}",
                f"**预估工作量**: {suggestion.estimated_effort}",
            ])
            
            if suggestion.code_example:
                lines.extend([
                    "",
                    "**代码示例**:",
                    "```python",
                    suggestion.code_example,
                    "```",
                ])
            
            lines.append("")
        
        lines.extend([
            "## 下一步行动",
            "",
        ])
        
        for i, step in enumerate(report.next_steps, 1):
            lines.append(f"{i}. {step}")
        
        return "\n".join(lines)
    
    def generate_report_json(self, report: DiagnosisReport) -> Dict[str, Any]:
        return {
            "report_id": report.report_id,
            "test_name": report.test_name,
            "generated_at": report.generated_at,
            "summary": report.summary,
            "failure_context": {
                "test_name": report.failure_context.test_name,
                "test_file": report.failure_context.test_file,
                "failure_type": report.failure_context.failure_type.value,
                "error_message": report.failure_context.error_message,
                "exception_type": report.failure_context.exception_type,
                "exception_value": report.failure_context.exception_value,
                "expected_value": report.failure_context.expected_value,
                "actual_value": report.failure_context.actual_value,
                "stack_trace": [
                    {
                        "file_path": f.file_path,
                        "line_number": f.line_number,
                        "function_name": f.function_name,
                        "code_line": f.code_line
                    }
                    for f in report.failure_context.stack_trace
                ]
            },
            "findings": [
                {
                    "finding_id": f.finding_id,
                    "category": f.category.value,
                    "severity": f.severity.value,
                    "title": f.title,
                    "description": f.description,
                    "evidence": f.evidence,
                    "affected_files": f.affected_files
                }
                for f in report.findings
            ],
            "suggestions": [
                {
                    "suggestion_id": s.suggestion_id,
                    "priority": s.priority,
                    "action": s.action,
                    "rationale": s.rationale,
                    "code_example": s.code_example,
                    "estimated_effort": s.estimated_effort
                }
                for s in report.suggestions
            ],
            "root_cause": {
                "primary_cause": report.root_cause.primary_cause,
                "contributing_factors": report.root_cause.contributing_factors,
                "cascade_effects": report.root_cause.cascade_effects,
                "confidence": report.root_cause.confidence,
                "analysis_path": report.root_cause.analysis_path
            },
            "next_steps": report.next_steps
        }


class FailurePattern(Enum):
    NULL_POINTER = "null_pointer"
    TYPE_MISMATCH = "type_mismatch"
    INDEX_OUT_OF_BOUNDS = "index_out_of_bounds"
    MISSING_KEY = "missing_key"
    ASSERTION_FAILED = "assertion_failed"
    IMPORT_ERROR = "import_error"
    TIMEOUT = "timeout"
    RESOURCE_LEAK = "resource_leak"
    RACE_CONDITION = "race_condition"
    LOGIC_ERROR = "logic_error"
    CONFIGURATION_ERROR = "configuration_error"
    DEPENDENCY_ERROR = "dependency_error"
    UNKNOWN_PATTERN = "unknown_pattern"


@dataclass
class CodeLocation:
    file_path: str
    line_number: int
    column_number: int = 0
    function_name: str = ""
    class_name: str = ""
    code_snippet: str = ""
    context_lines: List[str] = field(default_factory=list)


@dataclass
class ProblemCodeBlock:
    location: CodeLocation
    code: str
    issue_type: str
    severity: Severity
    description: str
    suggested_fix: Optional[str] = None
    related_locations: List[CodeLocation] = field(default_factory=list)


@dataclass
class EnhancedFixSuggestion:
    suggestion_id: str
    title: str
    description: str
    priority: int
    confidence: float
    affected_locations: List[CodeLocation]
    code_changes: List[Dict[str, str]]
    rationale: str
    references: List[str] = field(default_factory=list)
    test_verification: Optional[str] = None


@dataclass
class FailurePatternMatch:
    pattern: FailurePattern
    confidence: float
    evidence: List[str]
    related_patterns: List[FailurePattern] = field(default_factory=list)
    pattern_signature: str = ""


class CodeLocator:
    """问题代码定位器 - 精确定位问题代码位置
    
    该类负责定位测试失败相关的代码位置，包括：
    1. 栈帧分析 - 分析错误发生的具体位置
    2. 代码上下文提取 - 提取问题代码的上下文
    3. 相关代码定位 - 定位与问题相关的其他代码
    4. AST分析 - 使用抽象语法树进行深度分析
    """
    
    def __init__(self):
        self._file_cache: Dict[str, List[str]] = {}
        self._ast_cache: Dict[str, ast.AST] = {}
        self._symbol_analyzer = SymbolAnalyzer()
    
    def locate_problem_code(
        self, 
        context: FailureContext,
        project_root: Optional[Path] = None
    ) -> List[ProblemCodeBlock]:
        """定位问题代码 - 主入口方法
        
        根据失败上下文定位所有相关的问题代码块。
        
        Args:
            context: 失败上下文
            project_root: 项目根目录
            
        Returns:
            List[ProblemCodeBlock]: 问题代码块列表
        """
        problems = []
        
        for frame in context.stack_trace:
            if self._is_user_code(frame.file_path):
                problem = self._analyze_frame(frame, context, project_root)
                if problem:
                    problems.append(problem)
        
        if context.test_file and context.test_file not in [p.location.file_path for p in problems]:
            test_problem = self._analyze_test_file(context, project_root)
            if test_problem:
                problems.append(test_problem)
        
        related_problems = self._locate_related_code(context, problems, project_root)
        problems.extend(related_problems)
        
        return self._deduplicate_problems(problems)
    
    def _is_user_code(self, file_path: str) -> bool:
        """判断是否为用户代码
        
        过滤掉第三方库和系统库的代码，只关注用户代码。
        
        Args:
            file_path: 文件路径
            
        Returns:
            bool: 是否为用户代码
        """
        skip_patterns = [
            "site-packages",
            "lib/python",
            "pytest",
            "unittest",
            "__pycache__",
            ".venv",
            "venv",
            "env",
            "<",
            ">",
        ]
        return not any(pattern in file_path for pattern in skip_patterns)
    
    def _analyze_frame(
        self, 
        frame: StackFrame, 
        context: FailureContext,
        project_root: Optional[Path]
    ) -> Optional[ProblemCodeBlock]:
        """分析栈帧 - 提取问题代码的详细信息
        
        Args:
            frame: 栈帧信息
            context: 失败上下文
            project_root: 项目根目录
            
        Returns:
            Optional[ProblemCodeBlock]: 问题代码块
        """
        try:
            file_path = Path(frame.file_path)
            if not file_path.exists():
                if project_root:
                    file_path = project_root / frame.file_path
                if not file_path.exists():
                    return None
            
            lines = self._read_file(str(file_path))
            if not lines:
                return None
            
            line_idx = frame.line_number - 1
            code_snippet = lines[line_idx] if 0 <= line_idx < len(lines) else ""
            context_start = max(0, line_idx - 5)
            context_end = min(len(lines), line_idx + 6)
            context_lines = lines[context_start:context_end]
            
            location = CodeLocation(
                file_path=str(file_path),
                line_number=frame.line_number,
                function_name=frame.function_name,
                code_snippet=code_snippet,
                context_lines=context_lines
            )
            
            issue_type = self._identify_issue_type(code_snippet, context)
            severity = self._determine_severity(context)
            description = self._generate_issue_description(code_snippet, context, frame)
            suggested_fix = self._generate_suggested_fix(code_snippet, context, frame)
            
            related_locations = self._find_related_locations(
                str(file_path), frame.line_number, context
            )
            
            return ProblemCodeBlock(
                location=location,
                code=code_snippet,
                issue_type=issue_type,
                severity=severity,
                description=description,
                suggested_fix=suggested_fix,
                related_locations=related_locations
            )
            
        except Exception as e:
            logger.warning(f"分析帧失败: {e}")
            return None
    
    def _analyze_test_file(
        self, 
        context: FailureContext,
        project_root: Optional[Path]
    ) -> Optional[ProblemCodeBlock]:
        """分析测试文件 - 定位测试定义位置
        
        Args:
            context: 失败上下文
            project_root: 项目根目录
            
        Returns:
            Optional[ProblemCodeBlock]: 测试代码块
        """
        try:
            file_path = Path(context.test_file)
            if not file_path.exists() and project_root:
                file_path = project_root / context.test_file
            if not file_path.exists():
                return None
            
            lines = self._read_file(str(file_path))
            if not lines:
                return None
            
            test_function_name = context.test_name.split("::")[-1]
            
            for i, line in enumerate(lines):
                if test_function_name in line and ("def " in line or "async def " in line):
                    location = CodeLocation(
                        file_path=str(file_path),
                        line_number=i + 1,
                        code_snippet=line.strip(),
                        context_lines=lines[max(0, i-3):i+4]
                    )
                    
                    return ProblemCodeBlock(
                        location=location,
                        code=line.strip(),
                        issue_type="test_definition",
                        severity=Severity.MEDIUM,
                        description=f"测试定义位置: {context.test_name}",
                        suggested_fix=self._suggest_test_fix(context)
                    )
            
            return None
            
        except Exception as e:
            logger.warning(f"分析测试文件失败: {e}")
            return None
    
    def _locate_related_code(
        self,
        context: FailureContext,
        problems: List[ProblemCodeBlock],
        project_root: Optional[Path]
    ) -> List[ProblemCodeBlock]:
        """定位相关代码 - 查找与问题相关的其他代码
        
        Args:
            context: 失败上下文
            problems: 已发现的问题列表
            project_root: 项目根目录
            
        Returns:
            List[ProblemCodeBlock]: 相关问题代码块列表
        """
        related = []
        
        for problem in problems[:2]:
            if problem.location.file_path:
                symbols = self._symbol_analyzer.find_related_symbols(
                    problem.location.file_path,
                    problem.location.function_name,
                    problem.code
                )
                
                for symbol in symbols:
                    if symbol.get("file_path") and symbol.get("line_number"):
                        location = CodeLocation(
                            file_path=symbol["file_path"],
                            line_number=symbol["line_number"],
                            function_name=symbol.get("function_name", ""),
                            code_snippet=symbol.get("code", ""),
                            context_lines=symbol.get("context", [])
                        )
                        
                        related.append(ProblemCodeBlock(
                            location=location,
                            code=symbol.get("code", ""),
                            issue_type="related_code",
                            severity=Severity.LOW,
                            description=f"相关代码: {symbol.get('description', '未知')}"
                        ))
        
        return related[:5]
    
    def _read_file(self, file_path: str) -> List[str]:
        """读取文件内容 - 带缓存机制
        
        Args:
            file_path: 文件路径
            
        Returns:
            List[str]: 文件行列表
        """
        if file_path in self._file_cache:
            return self._file_cache[file_path]
        
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                lines = f.read().splitlines()
                self._file_cache[file_path] = lines
                return lines
        except Exception as e:
            logger.warning(f"读取文件失败 {file_path}: {e}")
            return []
    
    def _identify_issue_type(self, code: str, context: FailureContext) -> str:
        """识别问题类型 - 根据代码和上下文识别问题类型
        
        Args:
            code: 代码片段
            context: 失败上下文
            
        Returns:
            str: 问题类型
        """
        type_mapping = {
            FailureType.ASSERTION: "assertion_failure",
            FailureType.TYPE: "type_error",
            FailureType.ATTRIBUTE: "attribute_error",
            FailureType.KEY: "key_error",
            FailureType.INDEX: "index_error",
            FailureType.VALUE: "value_error",
            FailureType.IMPORT: "import_error",
            FailureType.FILE_NOT_FOUND: "file_not_found",
            FailureType.PERMISSION: "permission_error",
            FailureType.TIMEOUT: "timeout_error",
            FailureType.CONNECTION: "connection_error",
            FailureType.SYNTAX: "syntax_error",
            FailureType.RECURSION: "recursion_error",
            FailureType.MEMORY: "memory_error",
        }
        return type_mapping.get(context.failure_type, "unknown_error")
    
    def _determine_severity(self, context: FailureContext) -> Severity:
        """确定严重程度 - 根据失败类型确定问题严重程度
        
        Args:
            context: 失败上下文
            
        Returns:
            Severity: 严重程度
        """
        severity_map = {
            FailureType.IMPORT: Severity.CRITICAL,
            FailureType.SYNTAX: Severity.CRITICAL,
            FailureType.RECURSION: Severity.HIGH,
            FailureType.MEMORY: Severity.HIGH,
            FailureType.TIMEOUT: Severity.HIGH,
            FailureType.EXCEPTION: Severity.HIGH,
            FailureType.TYPE: Severity.HIGH,
            FailureType.ATTRIBUTE: Severity.HIGH,
            FailureType.FILE_NOT_FOUND: Severity.HIGH,
            FailureType.PERMISSION: Severity.HIGH,
            FailureType.CONNECTION: Severity.HIGH,
            FailureType.ASSERTION: Severity.MEDIUM,
            FailureType.VALUE: Severity.MEDIUM,
            FailureType.KEY: Severity.MEDIUM,
            FailureType.INDEX: Severity.MEDIUM,
        }
        return severity_map.get(context.failure_type, Severity.MEDIUM)
    
    def _generate_issue_description(
        self, 
        code: str, 
        context: FailureContext,
        frame: StackFrame
    ) -> str:
        """生成问题描述 - 创建详细的问题描述
        
        Args:
            code: 代码片段
            context: 失败上下文
            frame: 栈帧信息
            
        Returns:
            str: 问题描述
        """
        description_parts = [
            f"在 {frame.function_name}() 中检测到 {context.failure_type.value}",
        ]
        
        if context.exception_type:
            description_parts.append(f"异常类型: {context.exception_type}")
        
        if context.error_message:
            error_summary = context.error_message[:100]
            description_parts.append(f"错误信息: {error_summary}")
        
        if code.strip():
            code_summary = code.strip()[:50]
            description_parts.append(f"代码: {code_summary}")
        
        return " | ".join(description_parts)
    
    def _generate_suggested_fix(
        self,
        code: str,
        context: FailureContext,
        frame: StackFrame
    ) -> Optional[str]:
        """生成建议修复 - 根据问题类型生成修复建议
        
        Args:
            code: 代码片段
            context: 失败上下文
            frame: 栈帧信息
            
        Returns:
            Optional[str]: 建议修复代码
        """
        if context.failure_type == FailureType.ASSERTION:
            return f"# 检查断言条件\n# 预期: {context.expected_value}\n# 实际: {context.actual_value}"
        
        if context.failure_type == FailureType.TYPE:
            return "# 添加类型检查或转换\nif isinstance(value, expected_type):\n    result = operation(value)"
        
        if context.failure_type == FailureType.ATTRIBUTE:
            return "# 添加属性检查\nif hasattr(obj, 'attribute_name'):\n    value = obj.attribute_name"
        
        if context.failure_type == FailureType.KEY:
            return "# 使用安全的字典访问\nvalue = my_dict.get('key', default_value)"
        
        if context.failure_type == FailureType.INDEX:
            return "# 添加边界检查\nif 0 <= index < len(items):\n    value = items[index]"
        
        if context.failure_type == FailureType.VALUE:
            return "# 添加值验证\nif is_valid(value):\n    process(value)\nelse:\n    handle_invalid()"
        
        return None
    
    def _suggest_test_fix(self, context: FailureContext) -> Optional[str]:
        """建议测试修复 - 为测试代码生成修复建议
        
        Args:
            context: 失败上下文
            
        Returns:
            Optional[str]: 测试修复建议
        """
        suggestions = []
        
        if context.failure_type == FailureType.ASSERTION:
            suggestions.append("# 考虑调整断言条件或测试数据")
        
        if context.expected_value and context.actual_value:
            suggestions.append(f"# 预期值: {context.expected_value}")
            suggestions.append(f"# 实际值: {context.actual_value}")
        
        return "\n".join(suggestions) if suggestions else None
    
    def _find_related_locations(
        self,
        file_path: str,
        line_number: int,
        context: FailureContext
    ) -> List[CodeLocation]:
        """查找相关位置 - 查找与问题相关的其他代码位置
        
        Args:
            file_path: 文件路径
            line_number: 行号
            context: 失败上下文
            
        Returns:
            List[CodeLocation]: 相关位置列表
        """
        locations = []
        
        lines = self._read_file(file_path)
        if not lines:
            return locations
        
        if context.exception_type:
            for i, line in enumerate(lines):
                if context.exception_type in line and i != line_number - 1:
                    locations.append(CodeLocation(
                        file_path=file_path,
                        line_number=i + 1,
                        code_snippet=line.strip(),
                        context_lines=lines[max(0, i-2):i+3]
                    ))
        
        return locations[:3]
    
    def _deduplicate_problems(self, problems: List[ProblemCodeBlock]) -> List[ProblemCodeBlock]:
        """去重问题列表 - 移除重复的问题代码块
        
        Args:
            problems: 问题列表
            
        Returns:
            List[ProblemCodeBlock]: 去重后的问题列表
        """
        seen = set()
        unique = []
        
        for problem in problems:
            key = (problem.location.file_path, problem.location.line_number)
            if key not in seen:
                seen.add(key)
                unique.append(problem)
        
        return unique


class SymbolAnalyzer:
    """符号分析器 - 分析代码符号和引用关系
    
    该类负责分析代码中的符号定义和引用，
    帮助定位与问题相关的其他代码位置。
    """
    
    def __init__(self):
        self._symbol_cache: Dict[str, List[Dict[str, Any]]] = {}
    
    def find_related_symbols(
        self,
        file_path: str,
        function_name: str,
        code_snippet: str
    ) -> List[Dict[str, Any]]:
        """查找相关符号 - 查找与给定代码相关的符号
        
        Args:
            file_path: 文件路径
            function_name: 函数名
            code_snippet: 代码片段
            
        Returns:
            List[Dict[str, Any]]: 相关符号列表
        """
        related = []
        
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
            
            tree = ast.parse(content)
            lines = content.splitlines()
            
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef) and node.name == function_name:
                    continue
                
                if isinstance(node, ast.FunctionDef):
                    for child in ast.walk(node):
                        if isinstance(child, ast.Name) and child.id in code_snippet:
                            related.append({
                                "file_path": file_path,
                                "line_number": node.lineno,
                                "function_name": node.name,
                                "code": lines[node.lineno - 1] if node.lineno <= len(lines) else "",
                                "context": lines[max(0, node.lineno-3):node.lineno+2],
                                "description": f"函数 {node.name} 使用了相关符号"
                            })
                            break
            
        except Exception as e:
            logger.debug(f"符号分析失败: {e}")
        
        return related[:5]


class RootCauseAutoAnalyzer:
    """失败根因自动分析器"""
    
    ROOT_CAUSE_PATTERNS = {
        FailurePattern.NULL_POINTER: {
            "indicators": [
                r"'NoneType' object",
                r"object is None",
                r"AttributeError.*None",
            ],
            "root_cause": "空值引用错误",
            "common_fixes": [
                "添加空值检查",
                "使用安全导航操作符",
                "提供默认值",
            ]
        },
        FailurePattern.TYPE_MISMATCH: {
            "indicators": [
                r"TypeError",
                r"unsupported operand",
                r"cannot concatenate",
                r"expected.*got",
            ],
            "root_cause": "类型不匹配",
            "common_fixes": [
                "添加类型转换",
                "使用类型检查",
                "修正返回类型",
            ]
        },
        FailurePattern.INDEX_OUT_OF_BOUNDS: {
            "indicators": [
                r"IndexError",
                r"list index out of range",
                r"tuple index out of range",
            ],
            "root_cause": "索引越界",
            "common_fixes": [
                "添加边界检查",
                "使用切片操作",
                "验证数据长度",
            ]
        },
        FailurePattern.MISSING_KEY: {
            "indicators": [
                r"KeyError",
                r"key not found",
            ],
            "root_cause": "字典键缺失",
            "common_fixes": [
                "使用 dict.get() 方法",
                "添加键存在检查",
                "提供默认值",
            ]
        },
        FailurePattern.ASSERTION_FAILED: {
            "indicators": [
                r"AssertionError",
                r"assert\s+",
            ],
            "root_cause": "断言失败",
            "common_fixes": [
                "检查测试预期",
                "验证测试数据",
                "检查业务逻辑",
            ]
        },
        FailurePattern.IMPORT_ERROR: {
            "indicators": [
                r"ImportError",
                r"ModuleNotFoundError",
                r"cannot import name",
            ],
            "root_cause": "模块导入失败",
            "common_fixes": [
                "安装缺失的包",
                "检查模块路径",
                "验证虚拟环境",
            ]
        },
        FailurePattern.TIMEOUT: {
            "indicators": [
                r"TimeoutError",
                r"timed out",
                r"Timeout exceeded",
            ],
            "root_cause": "操作超时",
            "common_fixes": [
                "增加超时时间",
                "优化性能",
                "检查死锁",
            ]
        },
        FailurePattern.LOGIC_ERROR: {
            "indicators": [
                r"ValueError",
                r"unexpected.*value",
            ],
            "root_cause": "逻辑错误",
            "common_fixes": [
                "检查业务逻辑",
                "验证输入数据",
                "添加数据验证",
            ]
        },
    }
    
    def __init__(self):
        self._pattern_counter = 0
    
    def analyze_root_cause(
        self,
        context: FailureContext,
        findings: List[DiagnosticFinding]
    ) -> Tuple[str, List[str], float]:
        pattern_match = self._identify_pattern(context)
        
        contributing_factors = self._identify_contributing_factors(context, findings)
        
        confidence = self._calculate_confidence(context, pattern_match)
        
        root_cause = self._generate_root_cause_description(
            context, pattern_match, contributing_factors
        )
        
        return root_cause, contributing_factors, confidence
    
    def _identify_pattern(self, context: FailureContext) -> FailurePatternMatch:
        error_text = context.error_message + " " + (context.exception_value or "")
        
        best_match = None
        best_confidence = 0.0
        
        for pattern, config in self.ROOT_CAUSE_PATTERNS.items():
            match_count = 0
            evidence = []
            
            for indicator in config["indicators"]:
                if re.search(indicator, error_text, re.IGNORECASE):
                    match_count += 1
                    evidence.append(f"匹配模式: {indicator}")
            
            if match_count > 0:
                confidence = match_count / len(config["indicators"])
                if confidence > best_confidence:
                    best_confidence = confidence
                    best_match = FailurePatternMatch(
                        pattern=pattern,
                        confidence=confidence,
                        evidence=evidence,
                        pattern_signature=config["root_cause"]
                    )
        
        if best_match is None:
            best_match = FailurePatternMatch(
                pattern=FailurePattern.UNKNOWN_PATTERN,
                confidence=0.3,
                evidence=["无法识别特定模式"],
                pattern_signature="未知错误模式"
            )
        
        return best_match
    
    def _identify_contributing_factors(
        self,
        context: FailureContext,
        findings: List[DiagnosticFinding]
    ) -> List[str]:
        factors = []
        
        if context.stack_trace:
            user_frames = [
                f for f in context.stack_trace
                if "site-packages" not in f.file_path
            ]
            if len(user_frames) > 3:
                factors.append("调用链较深，可能存在多层抽象")
        
        for finding in findings:
            if finding.category == DiagnosticCategory.ENVIRONMENT:
                factors.append(f"环境因素: {finding.title}")
            elif finding.category == DiagnosticCategory.DEPENDENCY:
                factors.append(f"依赖问题: {finding.title}")
            elif finding.category == DiagnosticCategory.DATA:
                factors.append(f"数据问题: {finding.title}")
        
        if context.expected_value and context.actual_value:
            factors.append("预期值与实际值不匹配")
        
        return factors[:5]
    
    def _calculate_confidence(
        self,
        context: FailureContext,
        pattern_match: FailurePatternMatch
    ) -> float:
        confidence = pattern_match.confidence
        
        if context.failure_type != FailureType.UNKNOWN:
            confidence += 0.1
        
        if context.stack_trace:
            confidence += 0.1
        
        if context.error_message:
            confidence += 0.05
        
        return min(confidence, 1.0)
    
    def _generate_root_cause_description(
        self,
        context: FailureContext,
        pattern_match: FailurePatternMatch,
        contributing_factors: List[str]
    ) -> str:
        description_parts = [pattern_match.pattern_signature]
        
        if context.stack_trace:
            top_frame = context.stack_trace[0]
            description_parts.append(
                f"位置: {top_frame.file_path}:{top_frame.line_number}"
            )
        
        if context.exception_type:
            description_parts.append(f"异常类型: {context.exception_type}")
        
        return " | ".join(description_parts)


class EnhancedFixSuggestionGenerator:
    """增强修复建议生成器 - 生成智能修复建议
    
    该类负责根据问题分析结果生成详细的修复建议，包括：
    1. 针对性修复建议 - 根据具体问题类型生成修复方案
    2. 代码示例生成 - 提供可执行的代码示例
    3. 验证方法建议 - 提供修复后的验证方法
    4. 最佳实践建议 - 提供相关的最佳实践建议
    """
    
    FIX_TEMPLATES = {
        FailurePattern.NULL_POINTER: {
            "title": "空值引用修复",
            "template": """
# 添加空值检查
if {variable} is not None:
    {original_code}
else:
    # 处理空值情况
    {default_handling}
""",
            "rationale": "添加空值检查可以防止 NoneType 错误",
            "best_practices": [
                "使用类型注解明确参数和返回值类型",
                "考虑使用 Optional 类型提示",
                "在函数入口处验证参数"
            ]
        },
        FailurePattern.TYPE_MISMATCH: {
            "title": "类型转换修复",
            "template": """
# 确保类型正确
{variable} = {target_type}({variable})
{original_code}
""",
            "rationale": "显式类型转换可以避免类型不匹配错误",
            "best_practices": [
                "使用 isinstance() 进行类型检查",
                "考虑使用 typing 模块进行类型注解",
                "避免隐式类型转换"
            ]
        },
        FailurePattern.INDEX_OUT_OF_BOUNDS: {
            "title": "边界检查修复",
            "template": """
# 添加边界检查
if 0 <= index < len({container}):
    {original_code}
else:
    # 处理越界情况
    raise IndexError(f"索引 {{index}} 超出范围")
""",
            "rationale": "添加边界检查可以防止索引越界错误",
            "best_practices": [
                "使用切片代替索引访问",
                "考虑使用 enumerate() 遍历",
                "验证数据长度是否符合预期"
            ]
        },
        FailurePattern.MISSING_KEY: {
            "title": "字典键安全访问",
            "template": """
# 使用安全的字典访问方法
value = {dict_name}.get('{key}', {default_value})
{original_code}
""",
            "rationale": "使用 get() 方法可以安全地访问字典键",
            "best_practices": [
                "使用 dict.get() 提供默认值",
                "使用 dict.setdefault() 设置默认值",
                "考虑使用 collections.defaultdict"
            ]
        },
        FailurePattern.ASSERTION_FAILED: {
            "title": "断言修复建议",
            "template": """
# 检查实际值
print(f"实际值: {{actual}}")
print(f"预期值: {{expected}}")
assert {actual} == {expected}, f"期望 {{expected}}, 实际得到 {{actual}}"
""",
            "rationale": "添加调试输出可以帮助诊断断言失败原因",
            "best_practices": [
                "使用描述性的断言消息",
                "考虑使用 pytest.approx() 进行浮点数比较",
                "验证测试数据的正确性"
            ]
        },
        FailurePattern.IMPORT_ERROR: {
            "title": "模块导入修复",
            "template": """
# 安装缺失的模块
# pip install {module_name}

# 或者使用条件导入
try:
    import {module_name}
except ImportError:
    {module_name} = None
    # 或者使用替代方案
""",
            "rationale": "确保依赖正确安装或提供替代方案",
            "best_practices": [
                "使用 requirements.txt 管理依赖",
                "考虑使用可选依赖模式",
                "提供清晰的安装说明"
            ]
        },
        FailurePattern.TIMEOUT: {
            "title": "超时问题修复",
            "template": """
# 增加超时时间或优化性能
import signal

def timeout_handler(signum, frame):
    raise TimeoutError("操作超时")

signal.signal(signal.SIGALRM, timeout_handler)
signal.alarm({timeout_seconds})  # 设置超时时间
try:
    {original_code}
finally:
    signal.alarm(0)  # 取消超时
""",
            "rationale": "合理设置超时时间并处理超时情况",
            "best_practices": [
                "分析性能瓶颈",
                "考虑使用异步操作",
                "添加超时处理逻辑"
            ]
        },
        FailurePattern.LOGIC_ERROR: {
            "title": "逻辑错误修复",
            "template": """
# 添加逻辑验证
if {condition}:
    {original_code}
else:
    # 处理异常情况
    logger.warning("逻辑条件不满足: {condition}")
""",
            "rationale": "添加逻辑验证可以捕获逻辑错误",
            "best_practices": [
                "添加单元测试覆盖边界情况",
                "使用断言验证关键假设",
                "记录关键决策点"
            ]
        }
    }
    
    def __init__(self):
        self._suggestion_counter = 0
        self._context_analyzer = FixContextAnalyzer()
    
    def generate_suggestions(
        self,
        context: FailureContext,
        problem_blocks: List[ProblemCodeBlock],
        pattern_match: FailurePatternMatch
    ) -> List[EnhancedFixSuggestion]:
        """生成修复建议 - 主入口方法
        
        根据失败上下文和问题模式生成修复建议。
        
        Args:
            context: 失败上下文
            problem_blocks: 问题代码块列表
            pattern_match: 失败模式匹配结果
            
        Returns:
            List[EnhancedFixSuggestion]: 增强修复建议列表
        """
        suggestions = []
        
        primary_suggestion = self._generate_primary_suggestion(
            context, problem_blocks, pattern_match
        )
        if primary_suggestion:
            suggestions.append(primary_suggestion)
        
        for i, block in enumerate(problem_blocks[:3]):
            block_suggestion = self._generate_block_suggestion(block, i + 2)
            if block_suggestion:
                suggestions.append(block_suggestion)
        
        general_suggestions = self._generate_general_suggestions(context)
        suggestions.extend(general_suggestions)
        
        best_practice_suggestions = self._generate_best_practice_suggestions(
            context, pattern_match
        )
        suggestions.extend(best_practice_suggestions)
        
        return suggestions
    
    def _generate_primary_suggestion(
        self,
        context: FailureContext,
        problem_blocks: List[ProblemCodeBlock],
        pattern_match: FailurePatternMatch
    ) -> Optional[EnhancedFixSuggestion]:
        """生成主要建议 - 针对主要问题的修复建议
        
        Args:
            context: 失败上下文
            problem_blocks: 问题代码块列表
            pattern_match: 失败模式匹配结果
            
        Returns:
            Optional[EnhancedFixSuggestion]: 主要修复建议
        """
        template = self.FIX_TEMPLATES.get(pattern_match.pattern)
        if not template:
            return self._generate_generic_suggestion(context, pattern_match)
        
        self._suggestion_counter += 1
        
        locations = [block.location for block in problem_blocks]
        
        code_changes = []
        for block in problem_blocks[:1]:
            suggested_code = self._apply_template(template, block, context)
            code_changes.append({
                "file": block.location.file_path,
                "line": str(block.location.line_number),
                "original": block.code,
                "suggested": suggested_code
            })
        
        return EnhancedFixSuggestion(
            suggestion_id=f"EFS-{self._suggestion_counter:03d}",
            title=template["title"],
            description=f"针对 {pattern_match.pattern_signature} 的修复建议",
            priority=1,
            confidence=pattern_match.confidence,
            affected_locations=locations,
            code_changes=code_changes,
            rationale=template["rationale"],
            test_verification=self._generate_test_verification(context)
        )
    
    def _generate_generic_suggestion(
        self,
        context: FailureContext,
        pattern_match: FailurePatternMatch
    ) -> Optional[EnhancedFixSuggestion]:
        """生成通用建议 - 当没有匹配模板时使用
        
        Args:
            context: 失败上下文
            pattern_match: 失败模式匹配结果
            
        Returns:
            Optional[EnhancedFixSuggestion]: 通用修复建议
        """
        self._suggestion_counter += 1
        
        return EnhancedFixSuggestion(
            suggestion_id=f"EFS-{self._suggestion_counter:03d}",
            title="通用修复建议",
            description=f"针对 {pattern_match.pattern_signature} 的通用修复方案",
            priority=1,
            confidence=0.6,
            affected_locations=[],
            code_changes=[],
            rationale="请根据具体错误信息进行修复",
            test_verification=self._generate_test_verification(context)
        )
    
    def _generate_block_suggestion(
        self,
        block: ProblemCodeBlock,
        priority: int
    ) -> Optional[EnhancedFixSuggestion]:
        """生成代码块建议 - 针对特定代码块的修复建议
        
        Args:
            block: 问题代码块
            priority: 优先级
            
        Returns:
            Optional[EnhancedFixSuggestion]: 代码块修复建议
        """
        self._suggestion_counter += 1
        
        suggested_fix = block.suggested_fix or "# 需要人工审查此代码"
        
        return EnhancedFixSuggestion(
            suggestion_id=f"EFS-{self._suggestion_counter:03d}",
            title=f"修复 {block.issue_type}",
            description=block.description,
            priority=priority,
            confidence=0.7,
            affected_locations=[block.location],
            code_changes=[{
                "file": block.location.file_path,
                "line": str(block.location.line_number),
                "original": block.code,
                "suggested": suggested_fix
            }],
            rationale=f"解决 {block.issue_type} 问题",
            test_verification=self._generate_block_verification(block)
        )
    
    def _generate_general_suggestions(
        self,
        context: FailureContext
    ) -> List[EnhancedFixSuggestion]:
        """生成通用建议 - 适用于大多数情况的建议
        
        Args:
            context: 失败上下文
            
        Returns:
            List[EnhancedFixSuggestion]: 通用建议列表
        """
        suggestions = []
        
        self._suggestion_counter += 1
        suggestions.append(EnhancedFixSuggestion(
            suggestion_id=f"EFS-{self._suggestion_counter:03d}",
            title="添加单元测试",
            description="为相关功能添加更多单元测试覆盖",
            priority=5,
            confidence=0.8,
            affected_locations=[],
            code_changes=[],
            rationale="增加测试覆盖可以更早发现问题",
            test_verification="运行新增的单元测试确保覆盖"
        ))
        
        self._suggestion_counter += 1
        suggestions.append(EnhancedFixSuggestion(
            suggestion_id=f"EFS-{self._suggestion_counter:03d}",
            title="添加错误日志",
            description="在关键位置添加错误日志以便调试",
            priority=6,
            confidence=0.7,
            affected_locations=[],
            code_changes=[{
                "file": "",
                "line": "",
                "original": "",
                "suggested": "import logging\nlogger = logging.getLogger(__name__)\nlogger.error(f'Error: {error}')"
            }],
            rationale="良好的日志记录有助于快速定位问题",
            test_verification="检查日志输出是否正确"
        ))
        
        self._suggestion_counter += 1
        suggestions.append(EnhancedFixSuggestion(
            suggestion_id=f"EFS-{self._suggestion_counter:03d}",
            title="添加输入验证",
            description="在函数入口添加输入参数验证",
            priority=7,
            confidence=0.7,
            affected_locations=[],
            code_changes=[{
                "file": "",
                "line": "",
                "original": "",
                "suggested": "def function(param):\n    if not param:\n        raise ValueError('param cannot be empty')"
            }],
            rationale="输入验证可以防止无效数据导致的问题",
            test_verification="使用边界值测试验证"
        ))
        
        return suggestions
    
    def _generate_best_practice_suggestions(
        self,
        context: FailureContext,
        pattern_match: FailurePatternMatch
    ) -> List[EnhancedFixSuggestion]:
        """生成最佳实践建议 - 基于最佳实践的建议
        
        Args:
            context: 失败上下文
            pattern_match: 失败模式匹配结果
            
        Returns:
            List[EnhancedFixSuggestion]: 最佳实践建议列表
        """
        suggestions = []
        
        template = self.FIX_TEMPLATES.get(pattern_match.pattern)
        if template and "best_practices" in template:
            for i, practice in enumerate(template["best_practices"]):
                self._suggestion_counter += 1
                suggestions.append(EnhancedFixSuggestion(
                    suggestion_id=f"EFS-{self._suggestion_counter:03d}",
                    title=f"最佳实践: {practice[:30]}",
                    description=practice,
                    priority=8 + i,
                    confidence=0.6,
                    affected_locations=[],
                    code_changes=[],
                    rationale="遵循最佳实践可以提高代码质量",
                    references=["Python PEP 8", "Clean Code", "Effective Python"]
                ))
        
        return suggestions
    
    def _apply_template(
        self,
        template: Dict[str, Any],
        block: ProblemCodeBlock,
        context: FailureContext
    ) -> str:
        """应用模板 - 将模板应用到具体代码
        
        Args:
            template: 修复模板
            block: 问题代码块
            context: 失败上下文
            
        Returns:
            str: 生成的修复代码
        """
        code = template["template"]
        
        code = code.replace("{variable}", "value")
        code = code.replace("{original_code}", block.code)
        code = code.replace("{default_handling}", "pass  # TODO: 添加默认处理")
        code = code.replace("{target_type}", "str")
        code = code.replace("{container}", "items")
        code = code.replace("{dict_name}", "data")
        code = code.replace("{key}", "key")
        code = code.replace("{default_value}", "None")
        code = code.replace("{actual}", "actual")
        code = code.replace("{expected}", "expected")
        code = code.replace("{module_name}", "module")
        code = code.replace("{timeout_seconds}", "30")
        code = code.replace("{condition}", "condition")
        
        return code.strip()
    
    def _generate_test_verification(self, context: FailureContext) -> str:
        """生成测试验证 - 生成修复后的验证方法
        
        Args:
            context: 失败上下文
            
        Returns:
            str: 验证代码
        """
        return f"""
# 验证修复
def test_fix_verification():
    \"\"\"验证修复是否正确\"\"\"
    # 运行原始测试
    # {context.test_name}
    # 确保测试通过
    pass

# 边界情况测试
def test_edge_cases():
    \"\"\"测试边界情况\"\"\"
    # 测试空值
    # 测试边界值
    # 测试异常情况
    pass
"""
    
    def _generate_block_verification(self, block: ProblemCodeBlock) -> str:
        """生成代码块验证 - 为特定代码块生成验证方法
        
        Args:
            block: 问题代码块
            
        Returns:
            str: 验证代码
        """
        return f"""
# 验证 {block.issue_type} 修复
def test_{block.issue_type}_fix():
    \"\"\"验证 {block.issue_type} 修复\"\"\"
    # 测试原始问题场景
    # 验证修复后行为
    pass
"""


class FixContextAnalyzer:
    """修复上下文分析器 - 分析修复的上下文环境
    
    该类负责分析代码的上下文环境，帮助生成更准确的修复建议。
    """
    
    def analyze_context(
        self,
        context: FailureContext,
        problem_blocks: List[ProblemCodeBlock]
    ) -> Dict[str, Any]:
        """分析修复上下文
        
        Args:
            context: 失败上下文
            problem_blocks: 问题代码块列表
            
        Returns:
            Dict[str, Any]: 上下文分析结果
        """
        return {
            "has_test_file": bool(context.test_file),
            "has_stack_trace": bool(context.stack_trace),
            "problem_count": len(problem_blocks),
            "failure_type": context.failure_type.value,
            "suggested_approach": self._suggest_approach(context, problem_blocks)
        }
    
    def _suggest_approach(
        self,
        context: FailureContext,
        problem_blocks: List[ProblemCodeBlock]
    ) -> str:
        """建议修复方法
        
        Args:
            context: 失败上下文
            problem_blocks: 问题代码块列表
            
        Returns:
            str: 建议的修复方法
        """
        if context.failure_type == FailureType.ASSERTION:
            return "检查测试数据和断言条件"
        elif context.failure_type == FailureType.IMPORT:
            return "安装缺失依赖或检查导入路径"
        elif context.failure_type == FailureType.TYPE:
            return "添加类型检查或类型转换"
        elif len(problem_blocks) > 3:
            return "建议逐步修复，从最严重的问题开始"
        else:
            return "根据具体错误信息进行修复"


class FailurePatternRecognizer:
    """失败模式识别器"""
    
    def __init__(self):
        self._pattern_history: Dict[str, List[FailurePattern]] = defaultdict(list)
        self._pattern_signatures: Dict[FailurePattern, Set[str]] = defaultdict(set)
    
    def recognize_pattern(
        self,
        context: FailureContext,
        findings: List[DiagnosticFinding]
    ) -> FailurePatternMatch:
        signature = self._create_signature(context)
        
        pattern = self._match_known_pattern(signature, context)
        
        if context.test_name:
            self._pattern_history[context.test_name].append(pattern.pattern)
            self._pattern_signatures[pattern.pattern].add(signature)
        
        return pattern
    
    def _create_signature(self, context: FailureContext) -> str:
        parts = [
            context.failure_type.value,
            context.exception_type or "unknown",
            self._extract_error_signature(context.error_message)
        ]
        return "|".join(parts)
    
    def _extract_error_signature(self, error_message: str) -> str:
        error_message = re.sub(r'\d+', '#', error_message)
        error_message = re.sub(r"'[^']*'", "'*'", error_message)
        error_message = re.sub(r'"[^"]*"', '"*"', error_message)
        error_message = re.sub(r'/[\w/]+/', '/*/', error_message)
        return error_message[:100]
    
    def _match_known_pattern(
        self,
        signature: str,
        context: FailureContext
    ) -> FailurePatternMatch:
        for pattern, signatures in self._pattern_signatures.items():
            if signature in signatures:
                return FailurePatternMatch(
                    pattern=pattern,
                    confidence=0.9,
                    evidence=["匹配已知模式签名"],
                    pattern_signature=f"已知模式: {pattern.value}"
                )
        
        return self._analyze_new_pattern(context)
    
    def _analyze_new_pattern(self, context: FailureContext) -> FailurePatternMatch:
        error_text = context.error_message.lower()
        
        if "nonetype" in error_text or "none" in error_text:
            return FailurePatternMatch(
                pattern=FailurePattern.NULL_POINTER,
                confidence=0.8,
                evidence=["检测到 NoneType 相关错误"],
                pattern_signature="空指针引用"
            )
        
        if "type" in error_text or "typeerror" in error_text:
            return FailurePatternMatch(
                pattern=FailurePattern.TYPE_MISMATCH,
                confidence=0.8,
                evidence=["检测到类型相关错误"],
                pattern_signature="类型不匹配"
            )
        
        if "index" in error_text or "out of range" in error_text:
            return FailurePatternMatch(
                pattern=FailurePattern.INDEX_OUT_OF_BOUNDS,
                confidence=0.8,
                evidence=["检测到索引相关错误"],
                pattern_signature="索引越界"
            )
        
        if "key" in error_text or "keyerror" in error_text:
            return FailurePatternMatch(
                pattern=FailurePattern.MISSING_KEY,
                confidence=0.8,
                evidence=["检测到键相关错误"],
                pattern_signature="字典键缺失"
            )
        
        if "assert" in error_text or "assertion" in error_text:
            return FailurePatternMatch(
                pattern=FailurePattern.ASSERTION_FAILED,
                confidence=0.8,
                evidence=["检测到断言失败"],
                pattern_signature="断言失败"
            )
        
        if "import" in error_text or "module" in error_text:
            return FailurePatternMatch(
                pattern=FailurePattern.IMPORT_ERROR,
                confidence=0.8,
                evidence=["检测到导入相关错误"],
                pattern_signature="模块导入失败"
            )
        
        if "timeout" in error_text:
            return FailurePatternMatch(
                pattern=FailurePattern.TIMEOUT,
                confidence=0.8,
                evidence=["检测到超时错误"],
                pattern_signature="操作超时"
            )
        
        return FailurePatternMatch(
            pattern=FailurePattern.UNKNOWN_PATTERN,
            confidence=0.3,
            evidence=["无法识别特定模式"],
            pattern_signature="未知模式"
        )
    
    def get_pattern_statistics(self) -> Dict[str, Any]:
        stats = {
            "total_patterns_tracked": sum(len(v) for v in self._pattern_history.values()),
            "unique_tests": len(self._pattern_history),
            "pattern_distribution": defaultdict(int),
            "most_common_patterns": []
        }
        
        for patterns in self._pattern_history.values():
            for pattern in patterns:
                stats["pattern_distribution"][pattern.value] += 1
        
        sorted_patterns = sorted(
            stats["pattern_distribution"].items(),
            key=lambda x: x[1],
            reverse=True
        )
        stats["most_common_patterns"] = sorted_patterns[:5]
        
        return stats


class EnhancedTestFailureDiagnostician:
    """增强测试失败诊断器"""
    
    def __init__(self, project_root: Optional[Path] = None):
        self.project_root = project_root
        
        self.output_parser = PytestOutputParser()
        self.failure_analyzer = FailureAnalyzer()
        self.suggestion_generator = SuggestionGenerator()
        self.root_cause_analyzer = RootCauseAnalyzer()
        
        self.code_locator = CodeLocator()
        self.root_cause_auto_analyzer = RootCauseAutoAnalyzer()
        self.enhanced_fix_generator = EnhancedFixSuggestionGenerator()
        self.pattern_recognizer = FailurePatternRecognizer()
        
        self._report_counter = 0
        self._diagnosis_history: List[Dict[str, Any]] = []
    
    def diagnose(
        self,
        pytest_output: str,
        deep_analysis: bool = True
    ) -> List[DiagnosisReport]:
        failure_contexts = self.output_parser.parse(pytest_output)
        
        reports = []
        for context in failure_contexts:
            report = self._create_enhanced_diagnosis_report(context, deep_analysis)
            reports.append(report)
            
            self._diagnosis_history.append({
                "test_name": context.test_name,
                "failure_type": context.failure_type.value,
                "timestamp": datetime.now().isoformat(),
                "pattern": report.root_cause.primary_cause if report.root_cause else "unknown"
            })
        
        return reports
    
    def diagnose_from_file(
        self,
        file_path: str,
        deep_analysis: bool = True
    ) -> List[DiagnosisReport]:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
        
        return self.diagnose(content, deep_analysis)
    
    def _create_enhanced_diagnosis_report(
        self,
        context: FailureContext,
        deep_analysis: bool
    ) -> DiagnosisReport:
        self._report_counter += 1
        
        findings = self.failure_analyzer.analyze(context)
        
        problem_blocks = []
        if deep_analysis:
            problem_blocks = self.code_locator.locate_problem_code(
                context, self.project_root
            )
        
        pattern_match = self.pattern_recognizer.recognize_pattern(context, findings)
        
        enhanced_root_cause, contributing_factors, confidence = \
            self.root_cause_auto_analyzer.analyze_root_cause(context, findings)
        
        enhanced_suggestions = []
        if deep_analysis:
            enhanced_suggestions = self.enhanced_fix_generator.generate_suggestions(
                context, problem_blocks, pattern_match
            )
        
        basic_suggestions = self.suggestion_generator.generate(context, findings)
        
        root_cause = RootCauseAnalysis(
            primary_cause=enhanced_root_cause,
            contributing_factors=contributing_factors,
            cascade_effects=self._identify_cascade_effects(context, findings),
            confidence=confidence,
            analysis_path=self._build_analysis_path(context, findings, problem_blocks)
        )
        
        all_suggestions = self._merge_suggestions(basic_suggestions, enhanced_suggestions)
        
        summary = self._generate_enhanced_summary(
            context, findings, root_cause, pattern_match, problem_blocks
        )
        
        next_steps = self._generate_next_steps(all_suggestions)
        
        return DiagnosisReport(
            report_id=f"EDR-{datetime.now().strftime('%Y%m%d%H%M%S')}-{self._report_counter:03d}",
            test_name=context.test_name,
            generated_at=datetime.now().isoformat(),
            failure_context=context,
            findings=findings,
            suggestions=all_suggestions,
            root_cause=root_cause,
            summary=summary,
            next_steps=next_steps
        )
    
    def _identify_cascade_effects(
        self,
        context: FailureContext,
        findings: List[DiagnosticFinding]
    ) -> List[str]:
        effects = []
        
        if len(context.stack_trace) > 3:
            effects.append("错误在调用链中传播")
        
        for finding in findings:
            if finding.severity in [Severity.CRITICAL, Severity.HIGH]:
                effects.append(f"可能导致: {finding.title}")
        
        return effects[:5]
    
    def _build_analysis_path(
        self,
        context: FailureContext,
        findings: List[DiagnosticFinding],
        problem_blocks: List[ProblemCodeBlock]
    ) -> List[str]:
        path = []
        
        path.append(f"1. 检测到测试失败: {context.test_name}")
        path.append(f"2. 失败类型: {context.failure_type.value}")
        
        if problem_blocks:
            for i, block in enumerate(problem_blocks[:3], 3):
                path.append(
                    f"{i}. 问题代码: {block.location.file_path}:{block.location.line_number}"
                )
        
        if findings:
            path.append(f"{len(path) + 1}. 发现 {len(findings)} 个诊断结果")
        
        return path
    
    def _merge_suggestions(
        self,
        basic: List[DiagnosticSuggestion],
        enhanced: List[EnhancedFixSuggestion]
    ) -> List[DiagnosticSuggestion]:
        merged = []
        
        for efs in enhanced:
            merged.append(DiagnosticSuggestion(
                suggestion_id=efs.suggestion_id,
                priority=efs.priority,
                action=efs.title,
                rationale=efs.rationale,
                code_example="\n".join([
                    change.get("suggested", "")
                    for change in efs.code_changes
                ]) if efs.code_changes else None,
                estimated_effort="high" if efs.priority <= 2 else "medium"
            ))
        
        for ds in basic:
            if ds.action not in [s.action for s in merged]:
                merged.append(ds)
        
        return sorted(merged, key=lambda s: s.priority)
    
    def _generate_enhanced_summary(
        self,
        context: FailureContext,
        findings: List[DiagnosticFinding],
        root_cause: RootCauseAnalysis,
        pattern_match: FailurePatternMatch,
        problem_blocks: List[ProblemCodeBlock]
    ) -> str:
        parts = [
            f"测试 '{context.test_name}' 失败诊断完成。",
            f"失败类型: {context.failure_type.value}。",
            f"识别模式: {pattern_match.pattern_signature}。",
            f"根因: {root_cause.primary_cause}。",
            f"置信度: {root_cause.confidence:.0%}。"
        ]
        
        if problem_blocks:
            parts.append(f"定位到 {len(problem_blocks)} 个问题代码块。")
        
        severity_counts = defaultdict(int)
        for f in findings:
            severity_counts[f.severity.value] += 1
        
        if severity_counts:
            severity_str = ", ".join(f"{k}: {v}" for k, v in severity_counts.items())
            parts.append(f"发现: {severity_str}。")
        
        return " ".join(parts)
    
    def _generate_next_steps(
        self,
        suggestions: List[DiagnosticSuggestion]
    ) -> List[str]:
        return [s.action for s in suggestions[:5]]
    
    def generate_enhanced_report_markdown(
        self,
        report: DiagnosisReport,
        include_code_blocks: bool = True
    ) -> str:
        """生成增强Markdown报告 - 生成详细的Markdown格式诊断报告
        
        Args:
            report: 诊断报告
            include_code_blocks: 是否包含代码块
            
        Returns:
            str: Markdown格式报告
        """
        lines = [
            f"# 增强测试失败诊断报告",
            "",
            f"**报告ID**: {report.report_id}",
            f"**测试名称**: {report.test_name}",
            f"**生成时间**: {report.generated_at}",
            "",
            "---",
            "",
            "## 📋 摘要",
            "",
            report.summary,
            "",
            "---",
            "",
            "## 🔍 失败详情",
            "",
            f"- **失败类型**: `{report.failure_context.failure_type.value}`",
            f"- **错误消息**: {report._escape_markdown(report.failure_context.error_message)}",
        ]
        
        if report.failure_context.exception_type:
            lines.extend([
                f"- **异常类型**: `{report.failure_context.exception_type}`",
                f"- **异常值**: {report._escape_markdown(str(report.failure_context.exception_value or ''))}",
            ])
        
        if report.failure_context.expected_value and report.failure_context.actual_value:
            lines.extend([
                f"- **预期值**: `{report.failure_context.expected_value}`",
                f"- **实际值**: `{report.failure_context.actual_value}`",
            ])
        
        if report.failure_context.test_file:
            lines.extend([
                f"- **测试文件**: `{report.failure_context.test_file}`",
            ])
        
        lines.extend([
            "",
            "---",
            "",
            "## 🎯 根因分析",
            "",
            f"### 主要原因",
            "",
            f"{report.root_cause.primary_cause}",
            "",
            f"- **置信度**: `{report.root_cause.confidence:.0%}`",
        ])
        
        if report.root_cause.contributing_factors:
            lines.extend([
                "",
                "### 促成因素",
                "",
            ])
            for factor in report.root_cause.contributing_factors:
                lines.append(f"- {factor}")
        
        if report.root_cause.cascade_effects:
            lines.extend([
                "",
                "### 级联效应",
                "",
            ])
            for effect in report.root_cause.cascade_effects:
                lines.append(f"- {effect}")
        
        if report.root_cause.analysis_path:
            lines.extend([
                "",
                "### 分析路径",
                "",
            ])
            for step in report.root_cause.analysis_path:
                lines.append(f"1. {step}")
        
        lines.extend([
            "",
            "---",
            "",
            "## 🔬 诊断发现",
            "",
        ])
        
        for i, finding in enumerate(report.findings, 1):
            severity_emoji = {
                "critical": "🔴",
                "high": "🟠",
                "medium": "🟡",
                "low": "🟢",
                "info": "ℹ️"
            }.get(finding.severity.value, "⚪")
            
            lines.extend([
                f"### {severity_emoji} 发现 {i}: {finding.title}",
                "",
                f"| 属性 | 值 |",
                f"|------|-----|",
                f"| 类别 | `{finding.category.value}` |",
                f"| 严重性 | `{finding.severity.value}` |",
                f"| 描述 | {finding.description} |",
            ])
            
            if finding.evidence:
                lines.extend([
                    "",
                    "**证据**:",
                    "",
                ])
                for e in finding.evidence:
                    lines.append(f"- `{report._escape_markdown(e)}`")
            
            if finding.affected_files:
                lines.extend([
                    "",
                    "**影响文件**:",
                    "",
                ])
                for f in finding.affected_files:
                    lines.append(f"- `{f}`")
            
            if finding.related_code:
                lines.extend([
                    "",
                    "**相关代码**:",
                    "",
                    "```python",
                    *[f"  {code}" for code in finding.related_code],
                    "```",
                ])
            
            lines.append("")
        
        lines.extend([
            "---",
            "",
            "## 💡 修复建议",
            "",
        ])
        
        for i, suggestion in enumerate(report.suggestions, 1):
            priority_emoji = "🔥" if suggestion.priority <= 2 else "📌" if suggestion.priority <= 5 else "💡"
            
            lines.extend([
                f"### {priority_emoji} 建议 {i}: {suggestion.action}",
                "",
                f"| 属性 | 值 |",
                f"|------|-----|",
                f"| 优先级 | `{suggestion.priority}` |",
                f"| 预估工作量 | `{suggestion.estimated_effort}` |",
                "",
                f"**理由**: {suggestion.rationale}",
            ])
            
            if suggestion.code_example and include_code_blocks:
                lines.extend([
                    "",
                    "**代码示例**:",
                    "",
                    "```python",
                    suggestion.code_example,
                    "```",
                ])
            
            if suggestion.references:
                lines.extend([
                    "",
                    "**参考资源**:",
                    "",
                ])
                for ref in suggestion.references:
                    lines.append(f"- {ref}")
            
            lines.append("")
        
        lines.extend([
            "---",
            "",
            "## 📝 下一步行动",
            "",
        ])
        
        for i, step in enumerate(report.next_steps, 1):
            lines.append(f"{i}. {step}")
        
        lines.extend([
            "",
            "---",
            "",
            f"*报告生成时间: {report.generated_at}*",
        ])
        
        return "\n".join(lines)
    
    def generate_html_report(
        self,
        report: DiagnosisReport,
        include_styles: bool = True
    ) -> str:
        """生成HTML报告 - 生成HTML格式的诊断报告
        
        Args:
            report: 诊断报告
            include_styles: 是否包含样式
            
        Returns:
            str: HTML格式报告
        """
        html_parts = []
        
        if include_styles:
            html_parts.append(self._get_html_styles())
        
        html_parts.append(f"""
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>测试失败诊断报告 - {report.test_name}</title>
</head>
<body>
    <div class="container">
        <header class="report-header">
            <h1>🔍 测试失败诊断报告</h1>
            <div class="report-meta">
                <p><strong>报告ID:</strong> {report.report_id}</p>
                <p><strong>测试名称:</strong> {report.test_name}</p>
                <p><strong>生成时间:</strong> {report.generated_at}</p>
            </div>
        </header>
        
        <section class="summary">
            <h2>📋 摘要</h2>
            <p>{report.summary}</p>
        </section>
        
        <section class="failure-details">
            <h2>🔍 失败详情</h2>
            <table>
                <tr><th>属性</th><th>值</th></tr>
                <tr><td>失败类型</td><td><code>{report.failure_context.failure_type.value}</code></td></tr>
                <tr><td>错误消息</td><td>{self._escape_html(report.failure_context.error_message)}</td></tr>
                {f'<tr><td>异常类型</td><td><code>{report.failure_context.exception_type}</code></td></tr>' if report.failure_context.exception_type else ''}
                {f'<tr><td>预期值</td><td><code>{report.failure_context.expected_value}</code></td></tr>' if report.failure_context.expected_value else ''}
                {f'<tr><td>实际值</td><td><code>{report.failure_context.actual_value}</code></td></tr>' if report.failure_context.actual_value else ''}
            </table>
        </section>
        
        <section class="root-cause">
            <h2>🎯 根因分析</h2>
            <div class="primary-cause">
                <h3>主要原因</h3>
                <p>{report.root_cause.primary_cause}</p>
                <p><strong>置信度:</strong> <span class="confidence">{report.root_cause.confidence:.0%}</span></p>
            </div>
            
            {self._generate_html_factors(report.root_cause.contributing_factors, '促成因素')}
            {self._generate_html_effects(report.root_cause.cascade_effects, '级联效应')}
            {self._generate_html_path(report.root_cause.analysis_path, '分析路径')}
        </section>
        
        <section class="findings">
            <h2>🔬 诊断发现</h2>
            {self._generate_html_findings(report.findings)}
        </section>
        
        <section class="suggestions">
            <h2>💡 修复建议</h2>
            {self._generate_html_suggestions(report.suggestions)}
        </section>
        
        <section class="next-steps">
            <h2>📝 下一步行动</h2>
            <ol>
                {''.join(f'<li>{step}</li>' for step in report.next_steps)}
            </ol>
        </section>
        
        <footer class="report-footer">
            <p>报告生成时间: {report.generated_at}</p>
        </footer>
    </div>
</body>
</html>
""")
        
        return "\n".join(html_parts)
    
    def _get_html_styles(self) -> str:
        """获取HTML样式 - 返回报告的CSS样式
        
        Returns:
            str: CSS样式
        """
        return """
<style>
    body {
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
        line-height: 1.6;
        color: #333;
        max-width: 1200px;
        margin: 0 auto;
        padding: 20px;
        background-color: #f5f5f5;
    }
    .container {
        background-color: white;
        padding: 30px;
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .report-header {
        border-bottom: 2px solid #e0e0e0;
        padding-bottom: 20px;
        margin-bottom: 30px;
    }
    .report-header h1 {
        color: #2c3e50;
        margin-bottom: 10px;
    }
    .report-meta {
        color: #666;
    }
    section {
        margin-bottom: 30px;
    }
    section h2 {
        color: #2c3e50;
        border-bottom: 1px solid #e0e0e0;
        padding-bottom: 10px;
    }
    table {
        width: 100%;
        border-collapse: collapse;
        margin: 15px 0;
    }
    th, td {
        border: 1px solid #ddd;
        padding: 12px;
        text-align: left;
    }
    th {
        background-color: #f8f9fa;
    }
    code {
        background-color: #f4f4f4;
        padding: 2px 6px;
        border-radius: 3px;
        font-family: 'Courier New', monospace;
    }
    .confidence {
        font-weight: bold;
        color: #27ae60;
    }
    .severity-critical { color: #e74c3c; }
    .severity-high { color: #e67e22; }
    .severity-medium { color: #f39c12; }
    .severity-low { color: #27ae60; }
    .finding-card {
        border: 1px solid #e0e0e0;
        border-radius: 6px;
        padding: 15px;
        margin: 15px 0;
        background-color: #fafafa;
    }
    .suggestion-card {
        border-left: 4px solid #3498db;
        padding: 15px;
        margin: 15px 0;
        background-color: #f8f9fa;
    }
    pre {
        background-color: #2d2d2d;
        color: #f8f8f2;
        padding: 15px;
        border-radius: 6px;
        overflow-x: auto;
    }
    .report-footer {
        border-top: 1px solid #e0e0e0;
        padding-top: 20px;
        margin-top: 30px;
        color: #666;
        text-align: center;
    }
</style>
"""
    
    def _escape_html(self, text: str) -> str:
        """转义HTML字符 - 防止XSS攻击
        
        Args:
            text: 原始文本
            
        Returns:
            str: 转义后的文本
        """
        if not text:
            return ""
        return (text
                .replace("&", "&amp;")
                .replace("<", "&lt;")
                .replace(">", "&gt;")
                .replace('"', "&quot;")
                .replace("'", "&#39;"))
    
    def _generate_html_factors(self, factors: List[str], title: str) -> str:
        """生成HTML促成因素列表
        
        Args:
            factors: 促成因素列表
            title: 标题
            
        Returns:
            str: HTML内容
        """
        if not factors:
            return ""
        
        items = "\n".join(f"<li>{factor}</li>" for factor in factors)
        return f"""
        <div class="contributing-factors">
            <h3>{title}</h3>
            <ul>{items}</ul>
        </div>
        """
    
    def _generate_html_effects(self, effects: List[str], title: str) -> str:
        """生成HTML级联效应列表
        
        Args:
            effects: 级联效应列表
            title: 标题
            
        Returns:
            str: HTML内容
        """
        if not effects:
            return ""
        
        items = "\n".join(f"<li>{effect}</li>" for effect in effects)
        return f"""
        <div class="cascade-effects">
            <h3>{title}</h3>
            <ul>{items}</ul>
        </div>
        """
    
    def _generate_html_path(self, path: List[str], title: str) -> str:
        """生成HTML分析路径
        
        Args:
            path: 分析路径列表
            title: 标题
            
        Returns:
            str: HTML内容
        """
        if not path:
            return ""
        
        items = "\n".join(f"<li>{step}</li>" for step in path)
        return f"""
        <div class="analysis-path">
            <h3>{title}</h3>
            <ol>{items}</ol>
        </div>
        """
    
    def _generate_html_findings(self, findings: List[DiagnosticFinding]) -> str:
        """生成HTML诊断发现
        
        Args:
            findings: 诊断发现列表
            
        Returns:
            str: HTML内容
        """
        if not findings:
            return "<p>无诊断发现</p>"
        
        html_parts = []
        for i, finding in enumerate(findings, 1):
            severity_class = f"severity-{finding.severity.value}"
            evidence_html = ""
            if finding.evidence:
                evidence_items = "\n".join(f"<li><code>{self._escape_html(e)}</code></li>" for e in finding.evidence)
                evidence_html = f"""
                <div class="evidence">
                    <strong>证据:</strong>
                    <ul>{evidence_items}</ul>
                </div>
                """
            
            html_parts.append(f"""
            <div class="finding-card">
                <h3 class="{severity_class}">发现 {i}: {finding.title}</h3>
                <table>
                    <tr><th>类别</th><td>{finding.category.value}</td></tr>
                    <tr><th>严重性</th><td class="{severity_class}">{finding.severity.value}</td></tr>
                    <tr><th>描述</th><td>{finding.description}</td></tr>
                </table>
                {evidence_html}
            </div>
            """)
        
        return "\n".join(html_parts)
    
    def _generate_html_suggestions(self, suggestions: List[DiagnosticSuggestion]) -> str:
        """生成HTML修复建议
        
        Args:
            suggestions: 修复建议列表
            
        Returns:
            str: HTML内容
        """
        if not suggestions:
            return "<p>无修复建议</p>"
        
        html_parts = []
        for i, suggestion in enumerate(suggestions, 1):
            code_html = ""
            if suggestion.code_example:
                code_html = f"""
                <div class="code-example">
                    <strong>代码示例:</strong>
                    <pre><code>{self._escape_html(suggestion.code_example)}</code></pre>
                </div>
                """
            
            html_parts.append(f"""
            <div class="suggestion-card">
                <h3>建议 {i}: {suggestion.action}</h3>
                <p><strong>优先级:</strong> {suggestion.priority} | <strong>预估工作量:</strong> {suggestion.estimated_effort}</p>
                <p><strong>理由:</strong> {suggestion.rationale}</p>
                {code_html}
            </div>
            """)
        
        return "\n".join(html_parts)
    
    def generate_detailed_json_report(
        self,
        report: DiagnosisReport
    ) -> Dict[str, Any]:
        """生成详细JSON报告 - 生成包含完整信息的JSON格式报告
        
        Args:
            report: 诊断报告
            
        Returns:
            Dict[str, Any]: JSON数据结构
        """
        return {
            "report_metadata": {
                "report_id": report.report_id,
                "test_name": report.test_name,
                "generated_at": report.generated_at,
                "summary": report.summary
            },
            "failure_context": {
                "test_name": report.failure_context.test_name,
                "test_file": report.failure_context.test_file,
                "failure_type": report.failure_context.failure_type.value,
                "error_message": report.failure_context.error_message,
                "exception_type": report.failure_context.exception_type,
                "exception_value": report.failure_context.exception_value,
                "expected_value": str(report.failure_context.expected_value) if report.failure_context.expected_value else None,
                "actual_value": str(report.failure_context.actual_value) if report.failure_context.actual_value else None,
                "stack_trace": [
                    {
                        "file_path": f.file_path,
                        "line_number": f.line_number,
                        "function_name": f.function_name,
                        "code_line": f.code_line,
                        "context": f.context
                    }
                    for f in report.failure_context.stack_trace
                ]
            },
            "root_cause_analysis": {
                "primary_cause": report.root_cause.primary_cause,
                "contributing_factors": report.root_cause.contributing_factors,
                "cascade_effects": report.root_cause.cascade_effects,
                "confidence": report.root_cause.confidence,
                "analysis_path": report.root_cause.analysis_path
            },
            "diagnostic_findings": [
                {
                    "finding_id": f.finding_id,
                    "category": f.category.value,
                    "severity": f.severity.value,
                    "title": f.title,
                    "description": f.description,
                    "evidence": f.evidence,
                    "affected_files": f.affected_files,
                    "related_code": f.related_code
                }
                for f in report.findings
            ],
            "fix_suggestions": [
                {
                    "suggestion_id": s.suggestion_id,
                    "priority": s.priority,
                    "action": s.action,
                    "rationale": s.rationale,
                    "code_example": s.code_example,
                    "estimated_effort": s.estimated_effort,
                    "references": s.references if hasattr(s, 'references') else []
                }
                for s in report.suggestions
            ],
            "next_steps": report.next_steps
        }
    
    def get_diagnosis_statistics(self) -> Dict[str, Any]:
        """获取诊断统计信息 - 返回诊断历史统计
        
        Returns:
            Dict[str, Any]: 统计信息
        """
        pattern_stats = self.pattern_recognizer.get_pattern_statistics()
        
        return {
            "total_diagnoses": len(self._diagnosis_history),
            "pattern_statistics": pattern_stats,
            "recent_failures": self._diagnosis_history[-10:]
        }


def main():
    parser = argparse.ArgumentParser(
        description="增强测试失败诊断器",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 诊断pytest输出
  python test_failure_diagnostician.py --pytest-output test_output.txt --diagnose
  
  # 生成Markdown报告
  python test_failure_diagnostician.py --pytest-output test_output.txt --report diagnosis.md
  
  # 生成JSON报告
  python test_failure_diagnostician.py --pytest-output test_output.txt --json-report diagnosis.json
  
  # 深度分析模式
  python test_failure_diagnostician.py --pytest-output test_output.txt --deep-analysis --report enhanced_diagnosis.md
        """
    )
    
    parser.add_argument(
        "--pytest-output",
        required=True,
        help="pytest输出文件路径"
    )
    
    parser.add_argument(
        "--diagnose",
        action="store_true",
        help="执行诊断"
    )
    
    parser.add_argument(
        "--deep-analysis",
        action="store_true",
        help="执行深度分析（包括代码定位和增强建议）"
    )
    
    parser.add_argument(
        "--report",
        help="Markdown报告输出路径"
    )
    
    parser.add_argument(
        "--json-report",
        help="JSON报告输出路径"
    )
    
    parser.add_argument(
        "--project-root",
        help="项目根目录路径（用于代码定位）"
    )
    
    parser.add_argument(
        "--statistics",
        action="store_true",
        help="输出诊断统计信息"
    )
    
    args = parser.parse_args()
    
    try:
        project_root = Path(args.project_root) if args.project_root else None
        
        if args.deep_analysis:
            diagnostician = EnhancedTestFailureDiagnostician(project_root=project_root)
            reports = diagnostician.diagnose_from_file(
                args.pytest_output, 
                deep_analysis=True
            )
        else:
            diagnostician = TestFailureDiagnostician()
            reports = diagnostician.diagnose_from_file(args.pytest_output)
        
        if not reports:
            print("未检测到测试失败")
            return
        
        print(f"检测到 {len(reports)} 个测试失败")
        
        for report in reports:
            print(f"\n{'='*60}")
            print(f"测试: {report.test_name}")
            print(f"失败类型: {report.failure_context.failure_type.value}")
            print(f"摘要: {report.summary}")
            
            if args.diagnose or args.deep_analysis:
                print(f"\n诊断发现:")
                for finding in report.findings:
                    print(f"  - [{finding.severity.value}] {finding.title}")
                
                print(f"\n根因: {report.root_cause.primary_cause}")
                print(f"置信度: {report.root_cause.confidence:.0%}")
                
                print(f"\n建议:")
                for suggestion in report.suggestions[:3]:
                    print(f"  {suggestion.priority}. {suggestion.action}")
        
        if args.report:
            all_reports = []
            for report in reports:
                if args.deep_analysis and isinstance(diagnostician, EnhancedTestFailureDiagnostician):
                    all_reports.append(diagnostician.generate_enhanced_report_markdown(report))
                else:
                    all_reports.append(diagnostician.generate_report_markdown(report))
            
            Path(args.report).parent.mkdir(parents=True, exist_ok=True)
            with open(args.report, "w", encoding="utf-8") as f:
                f.write("\n\n---\n\n".join(all_reports))
            print(f"\nMarkdown报告已生成: {args.report}")
        
        if args.json_report:
            json_reports = [diagnostician.generate_report_json(r) for r in reports]
            
            Path(args.json_report).parent.mkdir(parents=True, exist_ok=True)
            with open(args.json_report, "w", encoding="utf-8") as f:
                json.dump(json_reports, f, ensure_ascii=False, indent=2, default=str)
            print(f"\nJSON报告已生成: {args.json_report}")
        
        if args.statistics and isinstance(diagnostician, EnhancedTestFailureDiagnostician):
            stats = diagnostician.get_diagnosis_statistics()
            print(f"\n诊断统计信息:")
            print(f"  总诊断次数: {stats['total_diagnoses']}")
            print(f"  模式分布: {dict(stats['pattern_statistics']['pattern_distribution'])}")
        
    except FileNotFoundError as e:
        logger.error(f"文件未找到: {e}")
        print(f"错误: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"执行错误: {e}")
        print(f"执行错误: {e}")
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
