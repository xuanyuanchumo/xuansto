#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
问题定位器 - Issue Locator

智能问题定位系统，包括：
- 根因分析算法
- 调用链追踪
- 影响范围分析
- 代码位置定位
- 生成问题定位报告

使用示例:
    python issue_locator.py --error-log error.log --analyze
    python issue_locator.py --error "TypeError: 'NoneType' object" --codebase ./src
    python issue_locator.py --trace-file trace.json --locate
"""

import argparse
import ast
import json
import logging
import os
import re
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple, Union


SCRIPT_METADATA = {
    "name": "issue_locator",
    "version": "2.0.0",
    "description": "智能问题定位系统 - 提供根因分析、调用链追踪、影响范围分析等功能",
    "category": "analysis",
    "dependencies": [],
    "entry_point": "main",
    "author": "Sanliu Skill Team",
    "tags": ["analysis", "debugging", "error-locating", "root-cause"],
    "config_schema": {
        "codebase_path": {"type": "string", "description": "代码库路径"},
        "output_format": {"type": "string", "default": "markdown", "enum": ["json", "markdown", "html"]}
    }
}


class IssueType(Enum):
    RUNTIME_ERROR = "runtime_error"
    LOGIC_ERROR = "logic_error"
    PERFORMANCE_ISSUE = "performance_issue"
    SECURITY_ISSUE = "security_issue"
    CONFIGURATION_ERROR = "configuration_error"
    DEPENDENCY_ISSUE = "dependency_issue"
    DATA_ISSUE = "data_issue"
    UNKNOWN = "unknown"


class Severity(Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class Confidence(Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass
class CodeLocation:
    file_path: str
    line_number: int
    column: int = 0
    function_name: str = ""
    class_name: str = ""
    code_snippet: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "file_path": self.file_path,
            "line_number": self.line_number,
            "column": self.column,
            "function_name": self.function_name,
            "class_name": self.class_name,
            "code_snippet": self.code_snippet
        }


@dataclass
class StackTraceFrame:
    file_path: str
    line_number: int
    function_name: str
    code_line: str
    is_user_code: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return {
            "file_path": self.file_path,
            "line_number": self.line_number,
            "function_name": self.function_name,
            "code_line": self.code_line,
            "is_user_code": self.is_user_code
        }


@dataclass
class CallChain:
    chain_id: str
    frames: List[StackTraceFrame]
    entry_point: str
    error_point: str
    depth: int

    def to_dict(self) -> Dict[str, Any]:
        return {
            "chain_id": self.chain_id,
            "frames": [f.to_dict() for f in self.frames],
            "entry_point": self.entry_point,
            "error_point": self.error_point,
            "depth": self.depth
        }


@dataclass
class ImpactScope:
    affected_files: List[str]
    affected_functions: List[str]
    affected_classes: List[str]
    affected_tests: List[str]
    estimated_impact: str
    affected_modules: List[str] = field(default_factory=list)
    affected_apis: List[str] = field(default_factory=list)
    data_flow_impact: List[str] = field(default_factory=list)
    test_coverage_impact: str = ""
    business_impact: str = ""
    risk_level: str = "medium"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "affected_files": self.affected_files,
            "affected_functions": self.affected_functions,
            "affected_classes": self.affected_classes,
            "affected_tests": self.affected_tests,
            "estimated_impact": self.estimated_impact,
            "affected_modules": self.affected_modules,
            "affected_apis": self.affected_apis,
            "data_flow_impact": self.data_flow_impact,
            "test_coverage_impact": self.test_coverage_impact,
            "business_impact": self.business_impact,
            "risk_level": self.risk_level
        }


@dataclass
class RootCause:
    cause_id: str
    description: str
    location: Optional[CodeLocation]
    confidence: Confidence
    evidence: List[str]
    contributing_factors: List[str]
    causal_chain: List[str] = field(default_factory=list)
    related_code_patterns: List[str] = field(default_factory=list)
    historical_similarity: float = 0.0
    fix_complexity: str = "medium"
    estimated_fix_time: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "cause_id": self.cause_id,
            "description": self.description,
            "location": self.location.to_dict() if self.location else None,
            "confidence": self.confidence.value,
            "evidence": self.evidence,
            "contributing_factors": self.contributing_factors,
            "causal_chain": self.causal_chain,
            "related_code_patterns": self.related_code_patterns,
            "historical_similarity": self.historical_similarity,
            "fix_complexity": self.fix_complexity,
            "estimated_fix_time": self.estimated_fix_time
        }


@dataclass
class FixPriority:
    priority_id: str
    priority_level: int
    priority_label: str
    urgency_score: float
    impact_score: float
    effort_score: float
    risk_score: float
    composite_score: float
    recommended_action: str
    deadline_suggestion: str
    dependencies: List[str]
    blockers: List[str]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "priority_id": self.priority_id,
            "priority_level": self.priority_level,
            "priority_label": self.priority_label,
            "urgency_score": self.urgency_score,
            "impact_score": self.impact_score,
            "effort_score": self.effort_score,
            "risk_score": self.risk_score,
            "composite_score": self.composite_score,
            "recommended_action": self.recommended_action,
            "deadline_suggestion": self.deadline_suggestion,
            "dependencies": self.dependencies,
            "blockers": self.blockers
        }


@dataclass
class IssueLocation:
    location_id: str
    issue_type: IssueType
    severity: Severity
    title: str
    description: str
    primary_location: Optional[CodeLocation]
    root_cause: Optional[RootCause]
    call_chain: Optional[CallChain]
    impact_scope: Optional[ImpactScope]
    suggestions: List[str]
    related_issues: List[str]
    fix_priority: Optional[FixPriority] = None
    tags: List[str] = field(default_factory=list)
    first_seen: str = ""
    last_seen: str = ""
    occurrence_count: int = 1

    def to_dict(self) -> Dict[str, Any]:
        return {
            "location_id": self.location_id,
            "issue_type": self.issue_type.value,
            "severity": self.severity.value,
            "title": self.title,
            "description": self.description,
            "primary_location": self.primary_location.to_dict() if self.primary_location else None,
            "root_cause": self.root_cause.to_dict() if self.root_cause else None,
            "call_chain": self.call_chain.to_dict() if self.call_chain else None,
            "impact_scope": self.impact_scope.to_dict() if self.impact_scope else None,
            "suggestions": self.suggestions,
            "related_issues": self.related_issues,
            "fix_priority": self.fix_priority.to_dict() if self.fix_priority else None,
            "tags": self.tags,
            "first_seen": self.first_seen,
            "last_seen": self.last_seen,
            "occurrence_count": self.occurrence_count
        }


@dataclass
class IssueLocationReport:
    report_id: str
    generated_at: str
    issues: List[IssueLocation]
    summary: str
    total_issues: int
    critical_count: int
    high_count: int = 0
    medium_count: int = 0
    low_count: int = 0
    issue_type_distribution: Dict[str, int] = field(default_factory=dict)
    severity_distribution: Dict[str, int] = field(default_factory=dict)
    top_affected_files: List[str] = field(default_factory=list)
    common_root_causes: List[str] = field(default_factory=list)
    recommended_fix_order: List[str] = field(default_factory=list)
    estimated_total_effort: str = ""
    risk_assessment: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "report_id": self.report_id,
            "generated_at": self.generated_at,
            "issues": [i.to_dict() for i in self.issues],
            "summary": self.summary,
            "total_issues": self.total_issues,
            "critical_count": self.critical_count,
            "high_count": self.high_count,
            "medium_count": self.medium_count,
            "low_count": self.low_count,
            "issue_type_distribution": self.issue_type_distribution,
            "severity_distribution": self.severity_distribution,
            "top_affected_files": self.top_affected_files,
            "common_root_causes": self.common_root_causes,
            "recommended_fix_order": self.recommended_fix_order,
            "estimated_total_effort": self.estimated_total_effort,
            "risk_assessment": self.risk_assessment
        }


class StackTraceParser:
    """堆栈跟踪解析器"""

    PYTHON_TRACE_PATTERN = re.compile(
        r'File\s+"([^"]+)",\s+line\s+(\d+),\s+in\s+(\w+)\s*\n\s*(.+)',
        re.MULTILINE
    )

    JAVA_TRACE_PATTERN = re.compile(
        r'at\s+([\w.]+)\(([\w.]+):(\d+)\)'
    )

    def parse(self, trace_text: str) -> List[StackTraceFrame]:
        frames = []

        for match in self.PYTHON_TRACE_PATTERN.finditer(trace_text):
            file_path = match.group(1)
            line_number = int(match.group(2))
            function_name = match.group(3)
            code_line = match.group(4).strip()

            is_user_code = self._is_user_code(file_path)

            frames.append(StackTraceFrame(
                file_path=file_path,
                line_number=line_number,
                function_name=function_name,
                code_line=code_line,
                is_user_code=is_user_code
            ))

        return frames

    def _is_user_code(self, file_path: str) -> bool:
        exclude_patterns = [
            'site-packages',
            'lib/python',
            'dist-packages',
            '__pycache__',
            '<',
            'built-in',
        ]
        return not any(p in file_path for p in exclude_patterns)


class ErrorClassifier:
    """错误分类器"""

    ERROR_PATTERNS = {
        IssueType.RUNTIME_ERROR: [
            (r'TypeError', '类型错误'),
            (r'AttributeError', '属性错误'),
            (r'NameError', '名称错误'),
            (r'IndexError', '索引错误'),
            (r'KeyError', '键错误'),
            (r'ValueError', '值错误'),
            (r'ZeroDivisionError', '除零错误'),
            (r'OverflowError', '溢出错误'),
        ],
        IssueType.LOGIC_ERROR: [
            (r'AssertionError', '断言错误'),
            (r'assert\s+failed', '断言失败'),
        ],
        IssueType.PERFORMANCE_ISSUE: [
            (r'TimeoutError', '超时错误'),
            (r'MemoryError', '内存错误'),
            (r'RecursionError', '递归错误'),
        ],
        IssueType.SECURITY_ISSUE: [
            (r'PermissionError', '权限错误'),
            (r'SecurityError', '安全错误'),
        ],
        IssueType.CONFIGURATION_ERROR: [
            (r'ImportError', '导入错误'),
            (r'ModuleNotFoundError', '模块未找到'),
            (r'ConfigParser', '配置解析错误'),
        ],
        IssueType.DEPENDENCY_ISSUE: [
            (r'ConnectionError', '连接错误'),
            (r'ConnectionRefusedError', '连接被拒绝'),
            (r'DatabaseError', '数据库错误'),
        ],
        IssueType.DATA_ISSUE: [
            (r'FileNotFoundError', '文件未找到'),
            (r'JSONDecodeError', 'JSON解析错误'),
            (r'UnicodeDecodeError', '编码错误'),
        ]
    }

    SEVERITY_MAP = {
        'TypeError': Severity.HIGH,
        'AttributeError': Severity.HIGH,
        'NameError': Severity.HIGH,
        'IndexError': Severity.MEDIUM,
        'KeyError': Severity.MEDIUM,
        'ValueError': Severity.MEDIUM,
        'ZeroDivisionError': Severity.HIGH,
        'MemoryError': Severity.CRITICAL,
        'RecursionError': Severity.HIGH,
        'TimeoutError': Severity.HIGH,
        'ImportError': Severity.HIGH,
        'ModuleNotFoundError': Severity.HIGH,
        'FileNotFoundError': Severity.MEDIUM,
        'PermissionError': Severity.HIGH,
        'ConnectionError': Severity.HIGH,
        'AssertionError': Severity.MEDIUM,
    }

    def classify(self, error_message: str) -> Tuple[IssueType, Severity, str]:
        for issue_type, patterns in self.ERROR_PATTERNS.items():
            for pattern, description in patterns:
                if re.search(pattern, error_message, re.IGNORECASE):
                    severity = self._determine_severity(error_message, pattern)
                    return issue_type, severity, description

        return IssueType.UNKNOWN, Severity.MEDIUM, '未知错误类型'

    def _determine_severity(self, error_message: str, matched_pattern: str) -> Severity:
        for error_name, severity in self.SEVERITY_MAP.items():
            if error_name in matched_pattern or error_name in error_message:
                return severity
        return Severity.MEDIUM


class CodebaseAnalyzer:
    """代码库分析器"""

    def __init__(self, codebase_path: Path):
        self.codebase_path = codebase_path
        self.file_cache: Dict[str, str] = {}
        self.ast_cache: Dict[str, ast.AST] = {}

    def find_function_definition(self, function_name: str) -> Optional[CodeLocation]:
        for py_file in self.codebase_path.rglob('*.py'):
            if '__pycache__' in str(py_file):
                continue

            try:
                tree = self._get_ast(py_file)
                for node in ast.walk(tree):
                    if isinstance(node, ast.FunctionDef) and node.name == function_name:
                        return CodeLocation(
                            file_path=str(py_file),
                            line_number=node.lineno,
                            function_name=function_name,
                            code_snippet=self._get_code_line(py_file, node.lineno)
                        )
            except Exception:
                continue

        return None

    def find_class_definition(self, class_name: str) -> Optional[CodeLocation]:
        for py_file in self.codebase_path.rglob('*.py'):
            if '__pycache__' in str(py_file):
                continue

            try:
                tree = self._get_ast(py_file)
                for node in ast.walk(tree):
                    if isinstance(node, ast.ClassDef) and node.name == class_name:
                        return CodeLocation(
                            file_path=str(py_file),
                            line_number=node.lineno,
                            class_name=class_name,
                            code_snippet=self._get_code_line(py_file, node.lineno)
                        )
            except Exception:
                continue

        return None

    def find_symbol_usages(self, symbol_name: str) -> List[CodeLocation]:
        usages = []

        for py_file in self.codebase_path.rglob('*.py'):
            if '__pycache__' in str(py_file):
                continue

            try:
                content = self._get_content(py_file)
                lines = content.split('\n')

                for i, line in enumerate(lines, 1):
                    if re.search(rf'\b{re.escape(symbol_name)}\b', line):
                        usages.append(CodeLocation(
                            file_path=str(py_file),
                            line_number=i,
                            code_snippet=line.strip()
                        ))
            except Exception:
                continue

        return usages

    def analyze_dependencies(self, file_path: Path) -> Dict[str, List[str]]:
        dependencies = {
            'imports': [],
            'imported_by': []
        }

        try:
            tree = self._get_ast(file_path)

            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        dependencies['imports'].append(alias.name)
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        dependencies['imports'].append(node.module)

        except Exception:
            pass

        module_name = self._get_module_name(file_path)
        for other_file in self.codebase_path.rglob('*.py'):
            if other_file == file_path or '__pycache__' in str(other_file):
                continue

            try:
                other_tree = self._get_ast(other_file)
                for node in ast.walk(other_tree):
                    if isinstance(node, ast.ImportFrom):
                        if node.module and module_name in node.module:
                            dependencies['imported_by'].append(str(other_file))
            except Exception:
                continue

        return dependencies

    def _get_content(self, file_path: Path) -> str:
        path_str = str(file_path)
        if path_str not in self.file_cache:
            with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
                self.file_cache[path_str] = f.read()
        return self.file_cache[path_str]

    def _get_ast(self, file_path: Path) -> ast.AST:
        path_str = str(file_path)
        if path_str not in self.ast_cache:
            content = self._get_content(file_path)
            self.ast_cache[path_str] = ast.parse(content)
        return self.ast_cache[path_str]

    def _get_code_line(self, file_path: Path, line_number: int) -> str:
        try:
            content = self._get_content(file_path)
            lines = content.split('\n')
            if 0 < line_number <= len(lines):
                return lines[line_number - 1].strip()
        except Exception:
            pass
        return ""

    def _get_module_name(self, file_path: Path) -> str:
        rel_path = file_path.relative_to(self.codebase_path)
        parts = list(rel_path.parts)
        if parts[-1] == '__init__.py':
            parts = parts[:-1]
        else:
            parts[-1] = parts[-1].replace('.py', '')
        return '.'.join(parts)


class RootCauseAnalyzer:
    """根因分析器 - 增强版
    
    提供深度根因分析功能，包括：
    - 模式匹配识别
    - 因果链分析
    - 代码模式关联
    - 历史相似度计算
    - 修复复杂度评估
    """

    ROOT_CAUSE_PATTERNS = {
        'null_reference': {
            'patterns': [r'NoneType', r'NullPointerException', r'null reference', r'undefined'],
            'root_cause': '空值引用',
            'suggestion': '添加空值检查，使用安全的访问方式（如 ?. 或 getattr）',
            'fix_complexity': 'low',
            'avg_fix_time': '15分钟',
        },
        'type_mismatch': {
            'patterns': [r'TypeError', r'type mismatch', r'invalid type', r'cannot convert'],
            'root_cause': '类型不匹配',
            'suggestion': '添加类型检查和转换，确保参数类型正确',
            'fix_complexity': 'medium',
            'avg_fix_time': '30分钟',
        },
        'resource_unavailable': {
            'patterns': [r'ConnectionRefused', r'ConnectionError', r'SocketError', r'timeout'],
            'root_cause': '资源不可用',
            'suggestion': '检查服务状态，添加重试机制和超时处理',
            'fix_complexity': 'high',
            'avg_fix_time': '2小时',
        },
        'permission_denied': {
            'patterns': [r'PermissionError', r'AccessDenied', r'Unauthorized', r'Forbidden'],
            'root_cause': '权限不足',
            'suggestion': '检查用户权限配置，验证访问控制策略',
            'fix_complexity': 'medium',
            'avg_fix_time': '1小时',
        },
        'data_integrity': {
            'patterns': [r'KeyError', r'IndexError', r'ValueError', r'IntegrityError'],
            'root_cause': '数据完整性问题',
            'suggestion': '验证数据存在性，添加数据校验逻辑',
            'fix_complexity': 'low',
            'avg_fix_time': '20分钟',
        },
        'configuration_error': {
            'patterns': [r'ImportError', r'ModuleNotFoundError', r'ConfigError', r'SettingNotFound'],
            'root_cause': '配置错误',
            'suggestion': '检查配置文件，验证依赖安装和环境变量',
            'fix_complexity': 'low',
            'avg_fix_time': '10分钟',
        },
        'memory_issue': {
            'patterns': [r'MemoryError', r'OutOfMemory', r'heap', r'allocation failed'],
            'root_cause': '内存问题',
            'suggestion': '检查内存泄漏，优化数据结构，增加内存限制',
            'fix_complexity': 'high',
            'avg_fix_time': '4小时',
        },
        'concurrency_issue': {
            'patterns': [r'Deadlock', r'RaceCondition', r'LockTimeout', r'concurrent'],
            'root_cause': '并发问题',
            'suggestion': '检查锁机制，优化并发控制策略',
            'fix_complexity': 'high',
            'avg_fix_time': '4小时',
        },
        'syntax_error': {
            'patterns': [r'SyntaxError', r'IndentationError', r'TabError', r'parse error'],
            'root_cause': '语法错误',
            'suggestion': '检查代码语法，修复缩进和括号匹配问题',
            'fix_complexity': 'low',
            'avg_fix_time': '5分钟',
        },
        'logic_error': {
            'patterns': [r'AssertionError', r'assert failed', r'logic error', r'unexpected'],
            'root_cause': '逻辑错误',
            'suggestion': '检查业务逻辑，验证条件判断和循环逻辑',
            'fix_complexity': 'medium',
            'avg_fix_time': '1小时',
        },
    }

    CAUSAL_CHAIN_INDICATORS = [
        (r'caused by[:\s]*(.+)', 'direct_cause'),
        (r'due to[:\s]*(.+)', 'reason'),
        (r'because[:\s]*(.+)', 'explanation'),
        (r'as a result of[:\s]*(.+)', 'result'),
        (r'triggered by[:\s]*(.+)', 'trigger'),
        (r'following[:\s]*(.+)', 'sequence'),
        (r'while trying to[:\s]*(.+)', 'attempt'),
        (r'when[:\s]*(.+)', 'condition'),
        (r'after[:\s]*(.+)', 'sequence'),
        (r'before[:\s]*(.+)', 'sequence'),
    ]

    CODE_PATTERN_INDICATORS = {
        'missing_null_check': [
            r'\.\w+\s*\(',  # 直接调用方法，可能对象为None
            r'\[\s*\w+\s*\]',  # 直接索引访问
        ],
        'unsafe_type_operation': [
            r'\+\s*\w+',  # 加法操作
            r'\-\s*\w+',  # 减法操作
            r'str\s*\(',  # 类型转换
            r'int\s*\(',
        ],
        'missing_error_handling': [
            r'open\s*\(',  # 文件操作
            r'requests\.\w+',  # 网络请求
            r'execute\s*\(',  # 数据库操作
        ],
        'resource_leak_risk': [
            r'open\s*\([^)]*\)(?!\s*with)',  # 没有使用with的文件打开
            r'connect\s*\([^)]*\)(?!\s*with)',  # 没有使用with的连接
        ],
    }

    def __init__(self, codebase_analyzer: CodebaseAnalyzer):
        self.codebase = codebase_analyzer
        self.cause_counter = 0
        self._compiled_root_patterns = {
            name: [re.compile(p, re.IGNORECASE) for p in info['patterns']]
            for name, info in self.ROOT_CAUSE_PATTERNS.items()
        }
        self._compiled_causal_indicators = [
            (re.compile(p, re.IGNORECASE), name) for p, name in self.CAUSAL_CHAIN_INDICATORS
        ]
        self._compiled_code_patterns = {
            name: [re.compile(p) for p in patterns]
            for name, patterns in self.CODE_PATTERN_INDICATORS.items()
        }
        self._root_cause_history: List[Dict[str, Any]] = []
        self._issue_knowledge_base: Dict[str, List[Dict[str, Any]]] = defaultdict(list)

    def analyze(self, error_message: str, stack_trace: List[StackTraceFrame]) -> Optional[RootCause]:
        """执行深度根因分析
        
        Args:
            error_message: 错误消息文本
            stack_trace: 堆栈跟踪帧列表
            
        Returns:
            RootCause对象，包含详细的根因分析结果
        """
        if not stack_trace:
            return self._analyze_without_trace(error_message)

        user_frames = [f for f in stack_trace if f.is_user_code]
        if not user_frames:
            user_frames = stack_trace

        primary_frame = user_frames[0]

        self.cause_counter += 1
        cause_id = f"RC-{self.cause_counter:03d}"

        location = CodeLocation(
            file_path=primary_frame.file_path,
            line_number=primary_frame.line_number,
            function_name=primary_frame.function_name,
            code_snippet=primary_frame.code_line
        )

        pattern_based_cause = self._analyze_with_patterns(error_message)
        
        description = self._generate_description(error_message, primary_frame, pattern_based_cause)
        evidence = self._gather_evidence(error_message, stack_trace)
        contributing_factors = self._identify_contributing_factors(error_message, stack_trace)
        confidence = self._calculate_confidence(error_message, stack_trace, pattern_based_cause)
        
        causal_chain = self._build_causal_chain(error_message, stack_trace)
        related_code_patterns = self._analyze_code_patterns(primary_frame.code_line) if primary_frame.code_line else []
        historical_similarity = self._calculate_historical_similarity(error_message, pattern_based_cause)
        fix_complexity = self._assess_fix_complexity(pattern_based_cause, stack_trace)
        estimated_fix_time = self._estimate_fix_time(pattern_based_cause, fix_complexity)

        root_cause = RootCause(
            cause_id=cause_id,
            description=description,
            location=location,
            confidence=confidence,
            evidence=evidence,
            contributing_factors=contributing_factors,
            causal_chain=causal_chain,
            related_code_patterns=related_code_patterns,
            historical_similarity=historical_similarity,
            fix_complexity=fix_complexity,
            estimated_fix_time=estimated_fix_time
        )

        self._record_root_cause(root_cause, error_message, pattern_based_cause)
        self._update_knowledge_base(error_message, root_cause)

        return root_cause

    def _analyze_without_trace(self, error_message: str) -> Optional[RootCause]:
        pattern_based_cause = self._analyze_with_patterns(error_message)
        
        if not pattern_based_cause:
            return None
        
        self.cause_counter += 1
        cause_id = f"RC-{self.cause_counter:03d}"
        
        return RootCause(
            cause_id=cause_id,
            description=pattern_based_cause['root_cause'],
            location=None,
            confidence=Confidence.MEDIUM,
            evidence=[f"错误消息: {error_message[:200]}"],
            contributing_factors=[f"匹配模式: {pattern_based_cause['name']}"]
        )

    def _analyze_with_patterns(self, error_message: str) -> Optional[Dict[str, Any]]:
        for name, info in self.ROOT_CAUSE_PATTERNS.items():
            for pattern in self._compiled_root_patterns[name]:
                if pattern.search(error_message):
                    return {
                        'name': name,
                        'root_cause': info['root_cause'],
                        'suggestion': info['suggestion'],
                    }
        return None

    def _generate_description(self, error_message: str, frame: StackTraceFrame, 
                             pattern_cause: Optional[Dict[str, Any]]) -> str:
        error_type = self._extract_error_type(error_message)

        if pattern_cause:
            return f"在 {frame.function_name} 中发生 {pattern_cause['root_cause']}: {error_message[:100]}"

        descriptions = {
            'TypeError': f"在 {frame.function_name} 中发生类型错误，可能是参数类型不匹配",
            'AttributeError': f"在 {frame.function_name} 中访问了不存在的属性，对象可能为None",
            'NameError': f"在 {frame.function_name} 中使用了未定义的变量或函数",
            'KeyError': f"在 {frame.function_name} 中访问了不存在的字典键",
            'IndexError': f"在 {frame.function_name} 中访问了越界的索引",
            'ValueError': f"在 {frame.function_name} 中传入了无效的值",
            'ImportError': f"模块导入失败，可能是模块未安装或路径错误",
            'FileNotFoundError': f"文件未找到，路径可能不正确或文件不存在",
        }

        return descriptions.get(error_type, f"在 {frame.function_name} 中发生错误: {error_message[:100]}")

    def _extract_error_type(self, error_message: str) -> str:
        match = re.match(r'^(\w+Error|\w+Exception)', error_message)
        if match:
            return match.group(1)
        return 'Unknown'

    def _gather_evidence(self, error_message: str, stack_trace: List[StackTraceFrame]) -> List[str]:
        evidence = [f"错误消息: {error_message[:200]}"]

        if stack_trace:
            frame = stack_trace[0]
            evidence.append(f"错误位置: {frame.file_path}:{frame.line_number}")
            evidence.append(f"函数: {frame.function_name}")
            if frame.code_line:
                evidence.append(f"代码: {frame.code_line}")

        causal_chain = self._extract_causal_chain(error_message)
        if causal_chain:
            evidence.append(f"因果链: {' -> '.join(causal_chain)}")

        for i, frame in enumerate(stack_trace[:3]):
            if i > 0:
                evidence.append(f"调用栈[{i}]: {frame.function_name} at {frame.file_path}:{frame.line_number}")

        return evidence

    def _extract_causal_chain(self, error_message: str) -> List[str]:
        chain = []
        for pattern, name in self._compiled_causal_indicators:
            matches = pattern.findall(error_message)
            for match in matches:
                chain.append(f"{name}: {match[:50]}")
        return chain

    def _identify_contributing_factors(self, error_message: str, stack_trace: List[StackTraceFrame]) -> List[str]:
        factors = []

        if len(stack_trace) > 5:
            factors.append("调用链较深，可能存在复杂的依赖关系")

        user_frames = [f for f in stack_trace if f.is_user_code]
        if len(user_frames) < len(stack_trace) // 2:
            factors.append("大部分错误发生在库代码中，可能是使用方式不当")

        error_type = self._extract_error_type(error_message)
        if error_type == 'AttributeError':
            factors.append("可能存在None值未检查的情况")
        elif error_type == 'KeyError':
            factors.append("字典键可能不存在，建议使用.get()方法")
        elif error_type == 'IndexError':
            factors.append("可能未检查列表/数组边界")
        elif error_type == 'TypeError':
            factors.append("参数类型可能不匹配，建议添加类型检查")

        pattern_cause = self._analyze_with_patterns(error_message)
        if pattern_cause:
            factors.append(f"根因类型: {pattern_cause['root_cause']}")
            factors.append(f"建议: {pattern_cause['suggestion']}")

        if self._has_recursion_pattern(stack_trace):
            factors.append("检测到递归调用模式，可能存在无限递归")

        if self._has_loop_pattern(stack_trace):
            factors.append("检测到循环调用模式，可能存在循环依赖")

        return factors

    def _has_recursion_pattern(self, stack_trace: List[StackTraceFrame]) -> bool:
        if len(stack_trace) < 3:
            return False
        
        function_names = [f.function_name for f in stack_trace]
        for i in range(len(function_names) - 2):
            if function_names[i] == function_names[i + 2]:
                return True
        return False

    def _has_loop_pattern(self, stack_trace: List[StackTraceFrame]) -> bool:
        if len(stack_trace) < 4:
            return False
        
        function_names = [f.function_name for f in stack_trace]
        seen_patterns: Dict[str, int] = defaultdict(int)
        
        for i in range(len(function_names) - 1):
            pattern = f"{function_names[i]}->{function_names[i+1]}"
            seen_patterns[pattern] += 1
            if seen_patterns[pattern] >= 2:
                return True
        return False

    def _calculate_confidence(self, error_message: str, stack_trace: List[StackTraceFrame],
                             pattern_cause: Optional[Dict[str, Any]]) -> Confidence:
        if not stack_trace:
            return Confidence.LOW if not pattern_cause else Confidence.MEDIUM

        user_frames = [f for f in stack_trace if f.is_user_code]

        base_confidence = Confidence.LOW
        
        if user_frames:
            base_confidence = Confidence.HIGH
        elif stack_trace:
            base_confidence = Confidence.MEDIUM

        if pattern_cause:
            if base_confidence == Confidence.LOW:
                base_confidence = Confidence.MEDIUM
            elif base_confidence == Confidence.MEDIUM:
                base_confidence = Confidence.HIGH

        return base_confidence

    def _record_root_cause(self, root_cause: RootCause, error_message: str, 
                          pattern_cause: Optional[Dict[str, Any]]) -> None:
        self._root_cause_history.append({
            'cause_id': root_cause.cause_id,
            'description': root_cause.description,
            'confidence': root_cause.confidence.value,
            'error_type': self._extract_error_type(error_message),
            'pattern_matched': pattern_cause['name'] if pattern_cause else None,
            'timestamp': datetime.now().isoformat(),
        })

    def get_root_cause_statistics(self) -> Dict[str, Any]:
        if not self._root_cause_history:
            return {'total_analyzed': 0}
        
        pattern_counts: Dict[str, int] = defaultdict(int)
        confidence_counts: Dict[str, int] = defaultdict(int)
        error_type_counts: Dict[str, int] = defaultdict(int)
        
        for record in self._root_cause_history:
            if record['pattern_matched']:
                pattern_counts[record['pattern_matched']] += 1
            confidence_counts[record['confidence']] += 1
            error_type_counts[record['error_type']] += 1
        
        return {
            'total_analyzed': len(self._root_cause_history),
            'pattern_distribution': dict(pattern_counts),
            'confidence_distribution': dict(confidence_counts),
            'error_type_distribution': dict(error_type_counts),
        }

    def analyze_multiple(self, issues: List[Tuple[str, List[StackTraceFrame]]]) -> List[RootCause]:
        root_causes = []
        for error_message, stack_trace in issues:
            root_cause = self.analyze(error_message, stack_trace)
            if root_cause:
                root_causes.append(root_cause)
        return root_causes

    def find_common_root_causes(self, root_causes: List[RootCause]) -> List[Dict[str, Any]]:
        common_patterns: Dict[str, List[RootCause]] = defaultdict(list)
        
        for rc in root_causes:
            for factor in rc.contributing_factors:
                if '根因类型:' in factor:
                    pattern = factor.replace('根因类型: ', '')
                    common_patterns[pattern].append(rc)
        
        return [
            {
                'pattern': pattern,
                'count': len(causes),
                'confidence_avg': sum(
                    1 if c.confidence == Confidence.HIGH else 
                    0.5 if c.confidence == Confidence.MEDIUM else 0.25
                    for c in causes
                ) / len(causes),
                'locations': [c.location.file_path if c.location else 'unknown' for c in causes[:5]],
            }
            for pattern, causes in sorted(common_patterns.items(), key=lambda x: len(x[1]), reverse=True)
        ]

    def _build_causal_chain(self, error_message: str, stack_trace: List[StackTraceFrame]) -> List[str]:
        """构建因果链，分析问题的传播路径
        
        Args:
            error_message: 错误消息
            stack_trace: 堆栈跟踪
            
        Returns:
            因果链列表，按时间顺序排列
        """
        chain = []
        
        for pattern, name in self._compiled_causal_indicators:
            matches = pattern.findall(error_message)
            for match in matches:
                chain.append(f"{name}: {match[:80]}")
        
        if stack_trace:
            user_frames = [f for f in stack_trace if f.is_user_code]
            if len(user_frames) >= 2:
                chain.append(f"调用路径: {' -> '.join(f.function_name for f in reversed(user_frames[:5]))}")
        
        error_type = self._extract_error_type(error_message)
        if error_type != 'Unknown':
            chain.insert(0, f"错误类型: {error_type}")
        
        return chain[:10]

    def _analyze_code_patterns(self, code_line: str) -> List[str]:
        """分析代码行中的潜在问题模式
        
        Args:
            code_line: 代码行文本
            
        Returns:
            检测到的代码模式列表
        """
        patterns_found = []
        
        for pattern_name, pattern_list in self._compiled_code_patterns.items():
            for pattern in pattern_list:
                if pattern.search(code_line):
                    pattern_desc = {
                        'missing_null_check': '可能缺少空值检查',
                        'unsafe_type_operation': '可能存在不安全的类型操作',
                        'missing_error_handling': '可能缺少错误处理',
                        'resource_leak_risk': '可能存在资源泄漏风险',
                    }
                    patterns_found.append(pattern_desc.get(pattern_name, pattern_name))
                    break
        
        return patterns_found

    def _calculate_historical_similarity(self, error_message: str, 
                                         pattern_cause: Optional[Dict[str, Any]]) -> float:
        """计算与历史问题的相似度
        
        Args:
            error_message: 错误消息
            pattern_cause: 模式匹配结果
            
        Returns:
            相似度分数 (0.0-1.0)
        """
        if not pattern_cause:
            return 0.0
        
        pattern_name = pattern_cause.get('name', '')
        similar_issues = self._issue_knowledge_base.get(pattern_name, [])
        
        if not similar_issues:
            return 0.0
        
        error_type = self._extract_error_type(error_message)
        matching_count = sum(
            1 for issue in similar_issues
            if issue.get('error_type') == error_type
        )
        
        similarity = min(1.0, matching_count / max(len(similar_issues), 1) * 0.8 + 0.2)
        return round(similarity, 2)

    def _assess_fix_complexity(self, pattern_cause: Optional[Dict[str, Any]], 
                               stack_trace: List[StackTraceFrame]) -> str:
        """评估修复复杂度
        
        Args:
            pattern_cause: 模式匹配结果
            stack_trace: 堆栈跟踪
            
        Returns:
            复杂度级别: low, medium, high
        """
        if pattern_cause:
            base_complexity = pattern_cause.get('fix_complexity', 'medium')
        else:
            base_complexity = 'medium'
        
        complexity_score = {'low': 1, 'medium': 2, 'high': 3}.get(base_complexity, 2)
        
        if len(stack_trace) > 10:
            complexity_score = min(3, complexity_score + 1)
        
        user_frames = [f for f in stack_trace if f.is_user_code]
        if len(user_frames) < len(stack_trace) // 3:
            complexity_score = min(3, complexity_score + 1)
        
        if self._has_recursion_pattern(stack_trace) or self._has_loop_pattern(stack_trace):
            complexity_score = min(3, complexity_score + 1)
        
        return {1: 'low', 2: 'medium', 3: 'high'}.get(complexity_score, 'medium')

    def _estimate_fix_time(self, pattern_cause: Optional[Dict[str, Any]], 
                          fix_complexity: str) -> str:
        """估算修复时间
        
        Args:
            pattern_cause: 模式匹配结果
            fix_complexity: 修复复杂度
            
        Returns:
            估算的修复时间
        """
        if pattern_cause and 'avg_fix_time' in pattern_cause:
            return pattern_cause['avg_fix_time']
        
        time_estimates = {
            'low': '15-30分钟',
            'medium': '30分钟-2小时',
            'high': '2-4小时或更长'
        }
        return time_estimates.get(fix_complexity, '30分钟-2小时')

    def _update_knowledge_base(self, error_message: str, root_cause: RootCause) -> None:
        """更新问题知识库
        
        Args:
            error_message: 错误消息
            root_cause: 根因分析结果
        """
        error_type = self._extract_error_type(error_message)
        
        for factor in root_cause.contributing_factors:
            if '根因类型:' in factor:
                pattern = factor.replace('根因类型: ', '')
                self._issue_knowledge_base[pattern].append({
                    'error_type': error_type,
                    'cause_id': root_cause.cause_id,
                    'timestamp': datetime.now().isoformat(),
                })
                break


class CallChainAnalyzer:
    """调用链分析器"""

    def __init__(self, codebase_analyzer: CodebaseAnalyzer):
        self.codebase = codebase_analyzer
        self.chain_counter = 0

    def analyze(self, stack_trace: List[StackTraceFrame]) -> Optional[CallChain]:
        if not stack_trace:
            return None

        self.chain_counter += 1

        user_frames = [f for f in stack_trace if f.is_user_code]
        if not user_frames:
            user_frames = stack_trace

        entry_point = user_frames[-1].function_name if user_frames else "unknown"
        error_point = user_frames[0].function_name if user_frames else "unknown"

        return CallChain(
            chain_id=f"CC-{self.chain_counter:03d}",
            frames=stack_trace,
            entry_point=entry_point,
            error_point=error_point,
            depth=len(stack_trace)
        )


class ImpactAnalyzer:
    """影响范围分析器 - 增强版
    
    提供全面的影响范围分析，包括：
    - 文件和模块影响分析
    - API影响分析
    - 数据流影响分析
    - 测试覆盖影响分析
    - 业务影响评估
    - 风险等级评估
    """

    API_INDICATORS = [
        r'@app\.route',
        r'@router\.',
        r'@api_view',
        r'@GetMapping',
        r'@PostMapping',
        r'@RequestMapping',
        r'def\s+\w+_api',
        r'async\s+def\s+\w+',
        r'@_blueprint',
    ]

    BUSINESS_CRITICAL_PATTERNS = [
        r'payment',
        r'auth',
        r'login',
        r'user',
        r'order',
        r'transaction',
        r'checkout',
        r'invoice',
        r'account',
        r'security',
    ]

    def __init__(self, codebase_analyzer: CodebaseAnalyzer):
        self.codebase = codebase_analyzer
        self._compiled_api_patterns = [re.compile(p, re.IGNORECASE) for p in self.API_INDICATORS]
        self._compiled_business_patterns = [re.compile(p, re.IGNORECASE) for p in self.BUSINESS_CRITICAL_PATTERNS]

    def analyze(self, location: CodeLocation, issue_type: IssueType = None, 
                severity: Severity = None) -> ImpactScope:
        """执行全面的影响范围分析
        
        Args:
            location: 代码位置
            issue_type: 问题类型
            severity: 严重程度
            
        Returns:
            ImpactScope对象，包含详细的影响范围信息
        """
        affected_files = set()
        affected_functions = set()
        affected_classes = set()
        affected_tests = set()
        affected_modules = set()
        affected_apis = set()
        data_flow_impact = []

        file_path = Path(location.file_path)
        if file_path.exists():
            deps = self.codebase.analyze_dependencies(file_path)
            affected_files.update(deps.get('imported_by', []))
            affected_modules.add(self._extract_module_name(file_path))

        if location.function_name:
            usages = self.codebase.find_symbol_usages(location.function_name)
            for usage in usages:
                affected_files.add(usage.file_path)
                if 'test' in usage.file_path.lower():
                    affected_tests.add(usage.file_path)
                affected_functions.add(location.function_name)
                
                if self._is_api_endpoint(usage.code_snippet):
                    affected_apis.add(f"{usage.file_path}:{usage.line_number}")

        if location.class_name:
            usages = self.codebase.find_symbol_usages(location.class_name)
            for usage in usages:
                affected_files.add(usage.file_path)
                affected_classes.add(location.class_name)

        data_flow_impact = self._analyze_data_flow_impact(location, affected_files)
        test_coverage_impact = self._assess_test_coverage_impact(affected_tests, affected_files)
        business_impact = self._assess_business_impact(location, affected_files)
        risk_level = self._calculate_risk_level(
            severity, len(affected_files), len(affected_apis), business_impact
        )

        estimated_impact = self._estimate_impact(
            len(affected_files),
            len(affected_functions),
            len(affected_classes),
            len(affected_apis),
            risk_level
        )

        return ImpactScope(
            affected_files=list(affected_files)[:20],
            affected_functions=list(affected_functions)[:10],
            affected_classes=list(affected_classes)[:10],
            affected_tests=list(affected_tests)[:10],
            estimated_impact=estimated_impact,
            affected_modules=list(affected_modules)[:10],
            affected_apis=list(affected_apis)[:10],
            data_flow_impact=data_flow_impact[:5],
            test_coverage_impact=test_coverage_impact,
            business_impact=business_impact,
            risk_level=risk_level
        )

    def _extract_module_name(self, file_path: Path) -> str:
        """从文件路径提取模块名"""
        parts = file_path.parts
        if 'src' in parts:
            idx = parts.index('src')
            return '.'.join(parts[idx+1:]).replace('.py', '')
        return file_path.stem

    def _is_api_endpoint(self, code_snippet: str) -> bool:
        """检查代码是否为API端点"""
        for pattern in self._compiled_api_patterns:
            if pattern.search(code_snippet):
                return True
        return False

    def _analyze_data_flow_impact(self, location: CodeLocation, 
                                   affected_files: Set[str]) -> List[str]:
        """分析数据流影响
        
        Args:
            location: 代码位置
            affected_files: 受影响的文件集合
            
        Returns:
            数据流影响描述列表
        """
        impacts = []
        
        if location.function_name:
            func_lower = location.function_name.lower()
            if any(kw in func_lower for kw in ['save', 'write', 'update', 'delete', 'create']):
                impacts.append("可能影响数据写入操作")
            if any(kw in func_lower for kw in ['read', 'get', 'fetch', 'load']):
                impacts.append("可能影响数据读取操作")
            if any(kw in func_lower for kw in ['process', 'transform', 'convert']):
                impacts.append("可能影响数据处理流程")
        
        file_path_lower = location.file_path.lower()
        if 'model' in file_path_lower or 'schema' in file_path_lower:
            impacts.append("可能影响数据模型定义")
        if 'service' in file_path_lower:
            impacts.append("可能影响业务服务层")
        if 'repository' in file_path_lower or 'dao' in file_path_lower:
            impacts.append("可能影响数据访问层")
        
        if len(affected_files) > 5:
            impacts.append(f"影响 {len(affected_files)} 个相关文件的数据流")
        
        return impacts

    def _assess_test_coverage_impact(self, affected_tests: Set[str], 
                                      affected_files: Set[str]) -> str:
        """评估测试覆盖影响
        
        Args:
            affected_tests: 受影响的测试文件
            affected_files: 受影响的文件
            
        Returns:
            测试覆盖影响描述
        """
        test_count = len(affected_tests)
        file_count = len(affected_files)
        
        if file_count == 0:
            return "无相关文件"
        
        coverage_ratio = test_count / file_count
        
        if coverage_ratio >= 0.8:
            return "测试覆盖良好，修复风险较低"
        elif coverage_ratio >= 0.5:
            return "测试覆盖中等，建议补充测试用例"
        elif coverage_ratio > 0:
            return "测试覆盖不足，修复需要谨慎验证"
        else:
            return "缺少相关测试，修复风险较高"

    def _assess_business_impact(self, location: CodeLocation, 
                                 affected_files: Set[str]) -> str:
        """评估业务影响
        
        Args:
            location: 代码位置
            affected_files: 受影响的文件
            
        Returns:
            业务影响描述
        """
        business_keywords_found = []
        
        all_text = f"{location.file_path} {location.function_name} {location.class_name}".lower()
        for pattern in self._compiled_business_patterns:
            if pattern.search(all_text):
                business_keywords_found.append(pattern.pattern)
        
        for file_path in affected_files:
            for pattern in self._compiled_business_patterns:
                if pattern.search(file_path.lower()):
                    business_keywords_found.append(pattern.pattern)
        
        if not business_keywords_found:
            return "业务影响较小"
        
        unique_keywords = list(set(business_keywords_found))[:3]
        
        if any(kw in ['payment', 'transaction', 'security', 'auth'] for kw in unique_keywords):
            return f"高业务影响: 涉及关键业务功能 ({', '.join(unique_keywords)})"
        elif any(kw in ['user', 'order', 'account'] for kw in unique_keywords):
            return f"中等业务影响: 涉及核心业务功能 ({', '.join(unique_keywords)})"
        else:
            return f"一般业务影响: 涉及业务功能 ({', '.join(unique_keywords)})"

    def _calculate_risk_level(self, severity: Severity, file_count: int, 
                              api_count: int, business_impact: str) -> str:
        """计算风险等级
        
        Args:
            severity: 严重程度
            file_count: 受影响文件数
            api_count: 受影响API数
            business_impact: 业务影响描述
            
        Returns:
            风险等级: low, medium, high, critical
        """
        risk_score = 0
        
        if severity:
            severity_scores = {
                Severity.CRITICAL: 40,
                Severity.HIGH: 30,
                Severity.MEDIUM: 20,
                Severity.LOW: 10,
                Severity.INFO: 5,
            }
            risk_score += severity_scores.get(severity, 10)
        
        if file_count > 10:
            risk_score += 20
        elif file_count > 5:
            risk_score += 10
        elif file_count > 0:
            risk_score += 5
        
        if api_count > 3:
            risk_score += 15
        elif api_count > 0:
            risk_score += 8
        
        if '高业务影响' in business_impact:
            risk_score += 25
        elif '中等业务影响' in business_impact:
            risk_score += 15
        elif '一般业务影响' in business_impact:
            risk_score += 5
        
        if risk_score >= 70:
            return "critical"
        elif risk_score >= 50:
            return "high"
        elif risk_score >= 30:
            return "medium"
        else:
            return "low"

    def _estimate_impact(self, file_count: int, func_count: int, class_count: int,
                         api_count: int, risk_level: str) -> str:
        """估算影响范围
        
        Args:
            file_count: 文件数
            func_count: 函数数
            class_count: 类数
            api_count: API数
            risk_level: 风险等级
            
        Returns:
            影响范围描述
        """
        total = file_count + func_count + class_count
        
        impact_descriptions = {
            'critical': "关键影响",
            'high': "重大影响",
            'medium': "中等影响",
            'low': "轻微影响"
        }
        
        base_impact = impact_descriptions.get(risk_level, "未知影响")
        
        details = []
        if total == 0:
            return "局部影响"
        if file_count > 0:
            details.append(f"{file_count}个文件")
        if api_count > 0:
            details.append(f"{api_count}个API")
        
        if details:
            return f"{base_impact}，涉及{', '.join(details)}"
        return base_impact


class FixPriorityEvaluator:
    """修复优先级评估器
    
    基于多维度评估修复优先级，包括：
    - 紧急程度评分
    - 影响范围评分
    - 修复难度评分
    - 风险评分
    - 综合优先级计算
    """
    
    PRIORITY_LABELS = {
        1: "P0 - 紧急",
        2: "P1 - 高优先级",
        3: "P2 - 中优先级",
        4: "P3 - 低优先级",
        5: "P4 - 可延后"
    }
    
    DEADLINE_SUGGESTIONS = {
        1: "立即修复（24小时内）",
        2: "尽快修复（3天内）",
        3: "计划修复（1-2周内）",
        4: "安排修复（1个月内）",
        5: "有空修复（可排期）"
    }
    
    RECOMMENDED_ACTIONS = {
        1: "立即组织修复，必要时暂停其他工作",
        2: "优先安排修复资源，确保及时完成",
        3: "纳入迭代计划，按优先级处理",
        4: "在空闲时间处理或批量修复",
        5: "可考虑在重构时一并处理"
    }

    def __init__(self):
        self.priority_counter = 0

    def evaluate(self, issue: IssueLocation) -> FixPriority:
        """评估问题的修复优先级
        
        Args:
            issue: 问题定位结果
            
        Returns:
            FixPriority对象，包含详细的优先级评估
        """
        self.priority_counter += 1
        priority_id = f"FP-{self.priority_counter:03d}"
        
        urgency_score = self._calculate_urgency_score(issue)
        impact_score = self._calculate_impact_score(issue)
        effort_score = self._calculate_effort_score(issue)
        risk_score = self._calculate_risk_score(issue)
        
        composite_score = self._calculate_composite_score(
            urgency_score, impact_score, effort_score, risk_score
        )
        
        priority_level = self._determine_priority_level(composite_score)
        priority_label = self.PRIORITY_LABELS.get(priority_level, "P3 - 中优先级")
        
        recommended_action = self.RECOMMENDED_ACTIONS.get(priority_level, "纳入计划处理")
        deadline_suggestion = self.DEADLINE_SUGGESTIONS.get(priority_level, "计划修复")
        
        dependencies = self._identify_dependencies(issue)
        blockers = self._identify_blockers(issue)
        
        return FixPriority(
            priority_id=priority_id,
            priority_level=priority_level,
            priority_label=priority_label,
            urgency_score=urgency_score,
            impact_score=impact_score,
            effort_score=effort_score,
            risk_score=risk_score,
            composite_score=composite_score,
            recommended_action=recommended_action,
            deadline_suggestion=deadline_suggestion,
            dependencies=dependencies,
            blockers=blockers
        )

    def _calculate_urgency_score(self, issue: IssueLocation) -> float:
        """计算紧急程度评分
        
        Args:
            issue: 问题定位结果
            
        Returns:
            紧急程度评分 (0.0-1.0)
        """
        score = 0.0
        
        severity_scores = {
            Severity.CRITICAL: 0.4,
            Severity.HIGH: 0.3,
            Severity.MEDIUM: 0.2,
            Severity.LOW: 0.1,
            Severity.INFO: 0.05,
        }
        score += severity_scores.get(issue.severity, 0.1)
        
        issue_type_scores = {
            IssueType.SECURITY_ISSUE: 0.3,
            IssueType.RUNTIME_ERROR: 0.2,
            IssueType.DATA_ISSUE: 0.15,
            IssueType.DEPENDENCY_ISSUE: 0.15,
            IssueType.CONFIGURATION_ERROR: 0.1,
            IssueType.PERFORMANCE_ISSUE: 0.1,
            IssueType.LOGIC_ERROR: 0.1,
            IssueType.UNKNOWN: 0.05,
        }
        score += issue_type_scores.get(issue.issue_type, 0.05)
        
        if issue.root_cause and issue.root_cause.confidence == Confidence.HIGH:
            score += 0.15
        elif issue.root_cause and issue.root_cause.confidence == Confidence.MEDIUM:
            score += 0.1
        
        if issue.occurrence_count > 5:
            score += 0.15
        elif issue.occurrence_count > 2:
            score += 0.1
        
        return min(1.0, score)

    def _calculate_impact_score(self, issue: IssueLocation) -> float:
        """计算影响范围评分
        
        Args:
            issue: 问题定位结果
            
        Returns:
            影响范围评分 (0.0-1.0)
        """
        if not issue.impact_scope:
            return 0.3
        
        score = 0.0
        
        risk_level_scores = {
            'critical': 0.4,
            'high': 0.3,
            'medium': 0.2,
            'low': 0.1,
        }
        score += risk_level_scores.get(issue.impact_scope.risk_level, 0.1)
        
        file_count = len(issue.impact_scope.affected_files)
        if file_count > 10:
            score += 0.2
        elif file_count > 5:
            score += 0.15
        elif file_count > 0:
            score += 0.1
        
        api_count = len(issue.impact_scope.affected_apis)
        if api_count > 0:
            score += min(0.2, api_count * 0.05)
        
        if '高业务影响' in issue.impact_scope.business_impact:
            score += 0.2
        elif '中等业务影响' in issue.impact_scope.business_impact:
            score += 0.1
        
        return min(1.0, score)

    def _calculate_effort_score(self, issue: IssueLocation) -> float:
        """计算修复难度评分（分数越高越容易修复）
        
        Args:
            issue: 问题定位结果
            
        Returns:
            修复难度评分 (0.0-1.0)，越高表示越容易
        """
        score = 0.5
        
        if issue.root_cause:
            complexity_scores = {
                'low': 0.3,
                'medium': 0.1,
                'high': -0.1,
            }
            score += complexity_scores.get(issue.root_cause.fix_complexity, 0)
        
        if issue.call_chain and issue.call_chain.depth > 10:
            score -= 0.15
        elif issue.call_chain and issue.call_chain.depth > 5:
            score -= 0.1
        
        if issue.impact_scope:
            if '缺少相关测试' in issue.impact_scope.test_coverage_impact:
                score -= 0.1
            elif '测试覆盖不足' in issue.impact_scope.test_coverage_impact:
                score -= 0.05
        
        if issue.suggestions and len(issue.suggestions) > 0:
            score += 0.1
        
        return max(0.0, min(1.0, score))

    def _calculate_risk_score(self, issue: IssueLocation) -> float:
        """计算修复风险评分（分数越高风险越低）
        
        Args:
            issue: 问题定位结果
            
        Returns:
            修复风险评分 (0.0-1.0)，越高表示风险越低
        """
        score = 0.5
        
        if issue.impact_scope:
            if '测试覆盖良好' in issue.impact_scope.test_coverage_impact:
                score += 0.2
            elif '测试覆盖中等' in issue.impact_scope.test_coverage_impact:
                score += 0.1
        
        if issue.root_cause and issue.root_cause.confidence == Confidence.HIGH:
            score += 0.15
        
        if issue.impact_scope and len(issue.impact_scope.affected_apis) > 3:
            score -= 0.15
        
        if issue.impact_scope and len(issue.impact_scope.affected_files) > 5:
            score -= 0.1
        
        return max(0.0, min(1.0, score))

    def _calculate_composite_score(self, urgency: float, impact: float, 
                                   effort: float, risk: float) -> float:
        """计算综合优先级评分
        
        Args:
            urgency: 紧急程度评分
            impact: 影响范围评分
            effort: 修复难度评分
            risk: 修复风险评分
            
        Returns:
            综合评分 (0.0-100.0)
        """
        urgency_weight = 0.35
        impact_weight = 0.30
        effort_weight = 0.20
        risk_weight = 0.15
        
        composite = (
            urgency * urgency_weight +
            impact * impact_weight +
            effort * effort_weight +
            risk * risk_weight
        )
        
        return round(composite * 100, 1)

    def _determine_priority_level(self, composite_score: float) -> int:
        """确定优先级等级
        
        Args:
            composite_score: 综合评分
            
        Returns:
            优先级等级 (1-5)
        """
        if composite_score >= 75:
            return 1
        elif composite_score >= 60:
            return 2
        elif composite_score >= 45:
            return 3
        elif composite_score >= 30:
            return 4
        else:
            return 5

    def _identify_dependencies(self, issue: IssueLocation) -> List[str]:
        """识别修复依赖
        
        Args:
            issue: 问题定位结果
            
        Returns:
            依赖项列表
        """
        dependencies = []
        
        if issue.impact_scope:
            if len(issue.impact_scope.affected_files) > 3:
                dependencies.append("需要协调多个文件的修改")
            
            if len(issue.impact_scope.affected_tests) == 0:
                dependencies.append("建议先编写测试用例")
        
        if issue.root_cause and issue.root_cause.fix_complexity == 'high':
            dependencies.append("可能需要架构层面的调整")
        
        return dependencies[:3]

    def _identify_blockers(self, issue: IssueLocation) -> List[str]:
        """识别修复阻碍因素
        
        Args:
            issue: 问题定位结果
            
        Returns:
            阻碍因素列表
        """
        blockers = []
        
        if issue.root_cause and issue.root_cause.confidence == Confidence.LOW:
            blockers.append("根因不明确，需要进一步调查")
        
        if issue.issue_type == IssueType.DEPENDENCY_ISSUE:
            blockers.append("依赖外部服务或库")
        
        if issue.impact_scope and '高业务影响' in issue.impact_scope.business_impact:
            blockers.append("涉及关键业务，需要充分测试")
        
        if issue.call_chain and issue.call_chain.depth > 15:
            blockers.append("调用链复杂，需要仔细分析")
        
        return blockers[:3]

    def prioritize_issues(self, issues: List[IssueLocation]) -> List[IssueLocation]:
        """对问题列表按优先级排序
        
        Args:
            issues: 问题列表
            
        Returns:
            按优先级排序后的问题列表
        """
        for issue in issues:
            if not issue.fix_priority:
                issue.fix_priority = self.evaluate(issue)
        
        return sorted(issues, key=lambda x: x.fix_priority.composite_score, reverse=True)


class IssueLocator:
    """问题定位器主类 - 增强版
    
    提供完整的问题定位功能，包括：
    - 错误分类和定位
    - 根因深度分析
    - 影响范围评估
    - 修复优先级评估
    - 详细报告生成
    """

    def __init__(self, codebase_path: Path = None):
        self.codebase = CodebaseAnalyzer(codebase_path) if codebase_path else None
        self.trace_parser = StackTraceParser()
        self.error_classifier = ErrorClassifier()
        self.root_cause_analyzer = RootCauseAnalyzer(self.codebase) if self.codebase else None
        self.call_chain_analyzer = CallChainAnalyzer(self.codebase) if self.codebase else None
        self.impact_analyzer = ImpactAnalyzer(self.codebase) if self.codebase else None
        self.priority_evaluator = FixPriorityEvaluator()
        self.issue_counter = 0

    def locate(self, error_message: str, stack_trace_text: str = None) -> IssueLocation:
        """定位问题并生成完整的分析结果
        
        Args:
            error_message: 错误消息
            stack_trace_text: 堆栈跟踪文本
            
        Returns:
            IssueLocation对象，包含完整的问题定位信息
        """
        self.issue_counter += 1
        issue_id = f"ISSUE-{self.issue_counter:03d}"

        issue_type, severity, description = self.error_classifier.classify(error_message)

        stack_trace = []
        if stack_trace_text:
            stack_trace = self.trace_parser.parse(stack_trace_text)

        primary_location = self._determine_primary_location(stack_trace)

        root_cause = None
        if self.root_cause_analyzer:
            root_cause = self.root_cause_analyzer.analyze(error_message, stack_trace)

        call_chain = None
        if self.call_chain_analyzer:
            call_chain = self.call_chain_analyzer.analyze(stack_trace)

        impact_scope = None
        if self.impact_analyzer and primary_location:
            impact_scope = self.impact_analyzer.analyze(primary_location, issue_type, severity)

        suggestions = self._generate_suggestions(issue_type, error_message, root_cause)
        
        tags = self._generate_tags(issue_type, severity, root_cause, impact_scope)

        issue = IssueLocation(
            location_id=issue_id,
            issue_type=issue_type,
            severity=severity,
            title=f"{issue_type.value}: {description}",
            description=error_message,
            primary_location=primary_location,
            root_cause=root_cause,
            call_chain=call_chain,
            impact_scope=impact_scope,
            suggestions=suggestions,
            related_issues=[],
            tags=tags,
            first_seen=datetime.now().isoformat(),
            last_seen=datetime.now().isoformat(),
            occurrence_count=1
        )
        
        issue.fix_priority = self.priority_evaluator.evaluate(issue)
        
        return issue

    def locate_from_file(self, error_log_path: Path) -> List[IssueLocation]:
        issues = []

        with open(error_log_path, 'r', encoding='utf-8', errors='replace') as f:
            content = f.read()

        error_blocks = self._extract_error_blocks(content)

        for error_msg, trace_text in error_blocks:
            issue = self.locate(error_msg, trace_text)
            issues.append(issue)

        return issues

    def _determine_primary_location(self, stack_trace: List[StackTraceFrame]) -> Optional[CodeLocation]:
        if not stack_trace:
            return None

        user_frames = [f for f in stack_trace if f.is_user_code]
        frame = user_frames[0] if user_frames else stack_trace[0]

        return CodeLocation(
            file_path=frame.file_path,
            line_number=frame.line_number,
            function_name=frame.function_name,
            code_snippet=frame.code_line
        )

    def _extract_error_blocks(self, content: str) -> List[Tuple[str, str]]:
        blocks = []

        error_pattern = re.compile(
            r'((?:Traceback\s*\(most recent call last\):)?\s*'
            r'((?:File\s+"[^"]+",\s+line\s+\d+.*\n)+)\s*'
            r'(\w+(?:Error|Exception)[^\n]*))',
            re.MULTILINE
        )

        for match in error_pattern.finditer(content):
            full_match = match.group(0)
            error_msg = match.group(3) if match.group(3) else "Unknown error"
            trace_text = match.group(2) if match.group(2) else ""
            blocks.append((error_msg.strip(), trace_text.strip()))

        if not blocks:
            error_lines = re.findall(r'^.*(?:Error|Exception).*$', content, re.MULTILINE)
            for line in error_lines[:10]:
                blocks.append((line.strip(), ""))

        return blocks

    def _generate_suggestions(self, issue_type: IssueType, error_message: str,
                              root_cause: Optional[RootCause]) -> List[str]:
        suggestions = []

        if issue_type == IssueType.RUNTIME_ERROR:
            if 'TypeError' in error_message:
                suggestions.append("检查参数类型是否正确")
                suggestions.append("添加类型检查和转换")
            elif 'AttributeError' in error_message:
                suggestions.append("添加None值检查")
                suggestions.append("使用hasattr()验证属性存在")
            elif 'KeyError' in error_message:
                suggestions.append("使用dict.get()方法避免KeyError")
                suggestions.append("添加键存在性检查")
            elif 'IndexError' in error_message:
                suggestions.append("添加索引边界检查")
                suggestions.append("使用切片代替直接索引")

        elif issue_type == IssueType.PERFORMANCE_ISSUE:
            suggestions.append("检查是否存在无限循环或递归")
            suggestions.append("优化算法复杂度")
            suggestions.append("考虑使用缓存")

        elif issue_type == IssueType.CONFIGURATION_ERROR:
            suggestions.append("检查模块是否正确安装")
            suggestions.append("验证Python路径配置")
            suggestions.append("检查虚拟环境")

        elif issue_type == IssueType.DEPENDENCY_ISSUE:
            suggestions.append("检查依赖服务状态")
            suggestions.append("验证连接配置")
            suggestions.append("添加重试机制")

        if root_cause and root_cause.location:
            suggestions.append(f"检查文件 {root_cause.location.file_path}:{root_cause.location.line_number}")

        return suggestions[:5]

    def _generate_tags(self, issue_type: IssueType, severity: Severity,
                       root_cause: Optional[RootCause], 
                       impact_scope: Optional[ImpactScope]) -> List[str]:
        """生成问题标签
        
        Args:
            issue_type: 问题类型
            severity: 严重程度
            root_cause: 根因分析结果
            impact_scope: 影响范围
            
        Returns:
            标签列表
        """
        tags = []
        
        tags.append(f"severity:{severity.value}")
        tags.append(f"type:{issue_type.value}")
        
        if root_cause:
            tags.append(f"confidence:{root_cause.confidence.value}")
            tags.append(f"complexity:{root_cause.fix_complexity}")
            
            for factor in root_cause.contributing_factors[:2]:
                if '根因类型:' in factor:
                    pattern = factor.replace('根因类型: ', '')
                    tags.append(f"root-cause:{pattern}")
        
        if impact_scope:
            tags.append(f"risk:{impact_scope.risk_level}")
            
            if impact_scope.affected_apis:
                tags.append("has-api-impact")
            if '高业务影响' in impact_scope.business_impact:
                tags.append("business-critical")
        
        return tags[:8]

    def generate_report(self, issues: List[IssueLocation]) -> IssueLocationReport:
        """生成详细的问题定位报告
        
        Args:
            issues: 问题列表
            
        Returns:
            IssueLocationReport对象
        """
        critical_count = sum(1 for i in issues if i.severity == Severity.CRITICAL)
        high_count = sum(1 for i in issues if i.severity == Severity.HIGH)
        medium_count = sum(1 for i in issues if i.severity == Severity.MEDIUM)
        low_count = sum(1 for i in issues if i.severity == Severity.LOW)
        
        issue_type_distribution: Dict[str, int] = defaultdict(int)
        severity_distribution: Dict[str, int] = defaultdict(int)
        for issue in issues:
            issue_type_distribution[issue.issue_type.value] += 1
            severity_distribution[issue.severity.value] += 1
        
        file_counts: Dict[str, int] = defaultdict(int)
        for issue in issues:
            if issue.primary_location:
                file_counts[issue.primary_location.file_path] += 1
        top_affected_files = sorted(file_counts.keys(), key=lambda x: file_counts[x], reverse=True)[:5]
        
        common_root_causes = []
        root_cause_counts: Dict[str, int] = defaultdict(int)
        for issue in issues:
            if issue.root_cause:
                for factor in issue.root_cause.contributing_factors:
                    if '根因类型:' in factor:
                        pattern = factor.replace('根因类型: ', '')
                        root_cause_counts[pattern] += 1
        common_root_causes = [f"{k} ({v}次)" for k, v in 
                              sorted(root_cause_counts.items(), key=lambda x: x[1], reverse=True)[:5]]
        
        sorted_issues = self.priority_evaluator.prioritize_issues(issues)
        recommended_fix_order = [f"{i.location_id}: {i.title} (优先级: {i.fix_priority.priority_label})" 
                                 for i in sorted_issues[:10]]
        
        total_effort_hours = 0
        for issue in issues:
            if issue.root_cause and issue.root_cause.estimated_fix_time:
                time_str = issue.root_cause.estimated_fix_time
                if '小时' in time_str:
                    match = re.search(r'(\d+)', time_str)
                    if match:
                        total_effort_hours += int(match.group(1))
                elif '分钟' in time_str:
                    match = re.search(r'(\d+)', time_str)
                    if match:
                        total_effort_hours += int(match.group(1)) / 60
        
        if total_effort_hours > 8:
            estimated_total_effort = f"约 {total_effort_hours:.1f} 小时（建议分多天完成）"
        elif total_effort_hours > 0:
            estimated_total_effort = f"约 {total_effort_hours:.1f} 小时"
        else:
            estimated_total_effort = "待评估"
        
        risk_assessment = self._assess_overall_risk(issues)
        
        summary_parts = [
            f"共定位 {len(issues)} 个问题",
            f"严重: {critical_count} 个",
            f"高优先级: {high_count} 个",
            f"中优先级: {medium_count} 个"
        ]

        return IssueLocationReport(
            report_id=f"LOC-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            generated_at=datetime.now().isoformat(),
            issues=sorted_issues,
            summary="，".join(summary_parts),
            total_issues=len(issues),
            critical_count=critical_count,
            high_count=high_count,
            medium_count=medium_count,
            low_count=low_count,
            issue_type_distribution=dict(issue_type_distribution),
            severity_distribution=dict(severity_distribution),
            top_affected_files=top_affected_files,
            common_root_causes=common_root_causes,
            recommended_fix_order=recommended_fix_order,
            estimated_total_effort=estimated_total_effort,
            risk_assessment=risk_assessment
        )

    def _assess_overall_risk(self, issues: List[IssueLocation]) -> str:
        """评估整体风险
        
        Args:
            issues: 问题列表
            
        Returns:
            风险评估描述
        """
        if not issues:
            return "无风险"
        
        critical_count = sum(1 for i in issues if i.severity == Severity.CRITICAL)
        high_count = sum(1 for i in issues if i.severity == Severity.HIGH)
        
        business_critical_count = sum(
            1 for i in issues 
            if i.impact_scope and '高业务影响' in i.impact_scope.business_impact
        )
        
        api_impact_count = sum(
            1 for i in issues 
            if i.impact_scope and i.impact_scope.affected_apis
        )
        
        risk_factors = []
        
        if critical_count > 0:
            risk_factors.append(f"{critical_count}个严重问题需立即处理")
        if high_count > 3:
            risk_factors.append(f"{high_count}个高优先级问题积压")
        if business_critical_count > 0:
            risk_factors.append(f"{business_critical_count}个问题影响关键业务")
        if api_impact_count > 2:
            risk_factors.append(f"{api_impact_count}个问题影响API接口")
        
        if not risk_factors:
            return "整体风险较低，建议按计划处理"
        elif len(risk_factors) <= 2:
            return f"中等风险: {', '.join(risk_factors)}"
        else:
            return f"高风险: {', '.join(risk_factors[:3])}，建议优先处理"

    def generate_markdown_report(self, report: IssueLocationReport) -> str:
        """生成详细的Markdown格式报告
        
        Args:
            report: 问题定位报告
            
        Returns:
            Markdown格式的报告文本
        """
        lines = [
            "# 问题定位报告",
            "",
            f"**报告ID**: {report.report_id}",
            f"**生成时间**: {report.generated_at}",
            "",
            "---",
            "",
            "## 📊 概览",
            "",
            f"| 指标 | 数值 |",
            f"|------|------|",
            f"| 问题总数 | {report.total_issues} |",
            f"| 🔴 严重 | {report.critical_count} |",
            f"| 🟠 高优先级 | {report.high_count} |",
            f"| 🟡 中优先级 | {report.medium_count} |",
            f"| 🟢 低优先级 | {report.low_count} |",
            "",
            "---",
            "",
            "## 📋 摘要",
            "",
            report.summary,
            "",
        ]
        
        if report.issue_type_distribution:
            lines.extend([
                "### 问题类型分布",
                "",
            ])
            for issue_type, count in sorted(report.issue_type_distribution.items(), 
                                           key=lambda x: x[1], reverse=True):
                lines.append(f"- **{issue_type}**: {count} 个")
            lines.append("")
        
        if report.common_root_causes:
            lines.extend([
                "### 常见根因",
                "",
            ])
            for cause in report.common_root_causes:
                lines.append(f"- {cause}")
            lines.append("")
        
        if report.top_affected_files:
            lines.extend([
                "### 最受影响的文件",
                "",
            ])
            for file_path in report.top_affected_files:
                lines.append(f"- `{file_path}`")
            lines.append("")
        
        if report.recommended_fix_order:
            lines.extend([
                "### 建议修复顺序",
                "",
            ])
            for i, item in enumerate(report.recommended_fix_order, 1):
                lines.append(f"{i}. {item}")
            lines.append("")
        
        if report.estimated_total_effort or report.risk_assessment:
            lines.extend([
                "### 修复评估",
                "",
            ])
            if report.estimated_total_effort:
                lines.append(f"- **预估总工时**: {report.estimated_total_effort}")
            if report.risk_assessment:
                lines.append(f"- **风险评估**: {report.risk_assessment}")
            lines.append("")
        
        lines.extend([
            "---",
            "",
            "## 🔍 详细问题分析",
            "",
        ])

        for issue in report.issues:
            priority_emoji = {
                1: "🔴",
                2: "🟠",
                3: "🟡",
                4: "🟢",
                5: "⚪"
            }.get(issue.fix_priority.priority_level if issue.fix_priority else 3, "🟡")
            
            lines.extend([
                f"### {priority_emoji} {issue.location_id}: {issue.title}",
                "",
                f"- **类型**: {issue.issue_type.value}",
                f"- **严重程度**: {issue.severity.value}",
                f"- **描述**: {issue.description[:200]}",
                "",
            ])
            
            if issue.fix_priority:
                lines.extend([
                    "#### 优先级评估",
                    "",
                    f"- **优先级**: {issue.fix_priority.priority_label}",
                    f"- **综合评分**: {issue.fix_priority.composite_score}",
                    f"- **建议截止**: {issue.fix_priority.deadline_suggestion}",
                    f"- **建议操作**: {issue.fix_priority.recommended_action}",
                    "",
                ])

            if issue.primary_location:
                lines.extend([
                    "#### 位置信息",
                    "",
                    f"- **文件**: `{issue.primary_location.file_path}`",
                    f"- **行号**: {issue.primary_location.line_number}",
                ])
                if issue.primary_location.function_name:
                    lines.append(f"- **函数**: `{issue.primary_location.function_name}`")
                if issue.primary_location.code_snippet:
                    lines.append(f"- **代码**: `{issue.primary_location.code_snippet}`")
                lines.append("")

            if issue.root_cause:
                lines.extend([
                    "#### 根因分析",
                    "",
                    f"- **原因**: {issue.root_cause.description}",
                    f"- **置信度**: {issue.root_cause.confidence.value}",
                    f"- **修复复杂度**: {issue.root_cause.fix_complexity}",
                ])
                if issue.root_cause.estimated_fix_time:
                    lines.append(f"- **预估修复时间**: {issue.root_cause.estimated_fix_time}")
                if issue.root_cause.evidence:
                    lines.append("- **证据**:")
                    for e in issue.root_cause.evidence[:5]:
                        lines.append(f"  - {e}")
                if issue.root_cause.causal_chain:
                    lines.append("- **因果链**:")
                    for c in issue.root_cause.causal_chain[:5]:
                        lines.append(f"  - {c}")
                lines.append("")

            if issue.call_chain:
                lines.extend([
                    "#### 调用链",
                    "",
                    f"- **入口**: `{issue.call_chain.entry_point}`",
                    f"- **错误点**: `{issue.call_chain.error_point}`",
                    f"- **深度**: {issue.call_chain.depth} 层",
                    "",
                ])

            if issue.impact_scope:
                lines.extend([
                    "#### 影响范围",
                    "",
                    f"- **影响评估**: {issue.impact_scope.estimated_impact}",
                    f"- **风险等级**: {issue.impact_scope.risk_level}",
                    f"- **业务影响**: {issue.impact_scope.business_impact}",
                    f"- **测试覆盖**: {issue.impact_scope.test_coverage_impact}",
                    f"- **影响文件数**: {len(issue.impact_scope.affected_files)}",
                ])
                if issue.impact_scope.affected_apis:
                    lines.append(f"- **影响API数**: {len(issue.impact_scope.affected_apis)}")
                if issue.impact_scope.data_flow_impact:
                    lines.append("- **数据流影响**:")
                    for d in issue.impact_scope.data_flow_impact:
                        lines.append(f"  - {d}")
                lines.append("")

            if issue.suggestions:
                lines.extend([
                    "#### 修复建议",
                    "",
                ])
                for i, s in enumerate(issue.suggestions, 1):
                    lines.append(f"{i}. {s}")
                lines.append("")
            
            if issue.tags:
                lines.extend([
                    "#### 标签",
                    "",
                    " ".join(f"`{tag}`" for tag in issue.tags),
                    "",
                ])
            
            lines.extend([
                "---",
                "",
            ])

        return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="问题定位器 - 智能问题定位系统",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 从错误日志定位问题
  python issue_locator.py --error-log error.log --analyze

  # 直接分析错误消息
  python issue_locator.py --error "TypeError: 'NoneType' object has no attribute 'x'" --codebase ./src

  # 从堆栈跟踪文件分析
  python issue_locator.py --trace-file trace.json --locate

  # 生成报告
  python issue_locator.py --error-log error.log --report location_report.md
        """
    )

    parser.add_argument(
        "--error-log",
        type=Path,
        help="错误日志文件路径"
    )

    parser.add_argument(
        "--error",
        type=str,
        help="直接指定错误消息"
    )

    parser.add_argument(
        "--trace",
        type=str,
        help="堆栈跟踪文本"
    )

    parser.add_argument(
        "--trace-file",
        type=Path,
        help="堆栈跟踪文件路径"
    )

    parser.add_argument(
        "--codebase",
        type=Path,
        help="代码库路径"
    )

    parser.add_argument(
        "--analyze",
        action="store_true",
        help="执行分析"
    )

    parser.add_argument(
        "--locate",
        action="store_true",
        help="执行定位"
    )

    parser.add_argument(
        "--report",
        type=str,
        help="报告输出路径"
    )

    parser.add_argument(
        "--verbose",
        action="store_true",
        help="详细输出"
    )

    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    logger = logging.getLogger(__name__)

    locator = IssueLocator(codebase_path=args.codebase)

    issues = []

    if args.error_log:
        issues = locator.locate_from_file(args.error_log)
    elif args.error:
        trace_text = args.trace
        if args.trace_file:
            with open(args.trace_file, 'r', encoding='utf-8') as f:
                trace_text = f.read()
        issues = [locator.locate(args.error, trace_text)]

    if not issues:
        parser.print_help()
        print("\n错误: 请指定 --error-log 或 --error")
        sys.exit(1)

    print("\n" + "=" * 60)
    print("问题定位报告")
    print("=" * 60)

    report = locator.generate_report(issues)

    print(f"报告ID: {report.report_id}")
    print(f"问题总数: {report.total_issues}")
    print(f"严重问题: {report.critical_count}")
    print(f"\n摘要: {report.summary}")

    for issue in issues:
        print(f"\n{'-' * 40}")
        print(f"[{issue.severity.value.upper()}] {issue.title}")
        print(f"类型: {issue.issue_type.value}")

        if issue.primary_location:
            print(f"位置: {issue.primary_location.file_path}:{issue.primary_location.line_number}")

        if issue.root_cause:
            print(f"根因: {issue.root_cause.description}")
            print(f"置信度: {issue.root_cause.confidence.value}")

        if issue.suggestions:
            print("建议:")
            for s in issue.suggestions[:3]:
                print(f"  - {s}")

    if args.report:
        report_path = Path(args.report)
        report_path.parent.mkdir(parents=True, exist_ok=True)

        suffix = report_path.suffix.lower()
        if suffix == '.json':
            with open(report_path, 'w', encoding='utf-8') as f:
                json.dump(report.to_dict(), f, ensure_ascii=False, indent=2)
        else:
            with open(report_path, 'w', encoding='utf-8') as f:
                f.write(locator.generate_markdown_report(report))

        print(f"\n报告已保存: {report_path}")

    return 0


if __name__ == "__main__":
    sys.exit(main())


SCRIPT_METADATA = {
    "name": "issue_locator",
    "version": "2.0.0",
    "description": "智能问题定位系统，包括根因分析、调用链追踪、影响范围分析和修复优先级评估",
    "category": "analysis",
    "dependencies": [],
    "entry_point": "main",
    "author": "Sanliu Team",
    "tags": ["analysis", "issue", "locator", "root-cause", "debugging"],
    "config_schema": {
        "codebase_path": {"type": "string", "description": "代码库路径"},
        "error_log": {"type": "string", "description": "错误日志文件路径"},
        "report_format": {"type": "string", "enum": ["json", "markdown"], "default": "markdown"}
    }
}


def register(registry) -> bool:
    try:
        return registry.register(
            name=SCRIPT_METADATA["name"],
            version=SCRIPT_METADATA["version"],
            description=SCRIPT_METADATA["description"],
            category=registry.__class__.__module__.split('.')[-2] if hasattr(registry, '__class__') else 'analysis',
            dependencies=SCRIPT_METADATA["dependencies"],
            entry_point=SCRIPT_METADATA["entry_point"],
            config_schema=SCRIPT_METADATA["config_schema"],
            author=SCRIPT_METADATA["author"],
            tags=SCRIPT_METADATA["tags"]
        )
    except Exception:
        return False


def get_dependencies() -> list:
    return SCRIPT_METADATA.get("dependencies", [])


def get_metadata() -> dict:
    return SCRIPT_METADATA.copy()


class EnhancedImpactAnalyzer:
    """增强影响范围分析器 - 提供更精确的影响评估
    
    功能：
    - 服务依赖影响分析
    - 数据库影响分析
    - 缓存影响分析
    - 消息队列影响分析
    - 外部API影响分析
    - 用户体验影响评估
    """
    
    SERVICE_INDICATORS = [
        (r'@service', 'service'),
        (r'@component', 'component'),
        (r'@repository', 'repository'),
        (r'class\s+\w*Service', 'service'),
        (r'class\s+\w*Controller', 'controller'),
        (r'class\s+\w*Handler', 'handler'),
    ]
    
    DATABASE_INDICATORS = [
        (r'SELECT\s+', 'query'),
        (r'INSERT\s+', 'insert'),
        (r'UPDATE\s+', 'update'),
        (r'DELETE\s+', 'delete'),
        (r'execute\s*\(', 'execute'),
        (r'query\s*\(', 'query'),
        (r'cursor\.', 'cursor'),
        (r'session\.', 'session'),
        (r'transaction', 'transaction'),
    ]
    
    CACHE_INDICATORS = [
        (r'redis', 'redis'),
        (r'memcached', 'memcached'),
        (r'cache', 'cache'),
        (r'@cacheable', 'cacheable'),
        (r'@cacheevict', 'cacheevict'),
        (r'get_cache', 'get'),
        (r'set_cache', 'set'),
    ]
    
    MQ_INDICATORS = [
        (r'kafka', 'kafka'),
        (r'rabbitmq', 'rabbitmq'),
        (r'activemq', 'activemq'),
        (r'publish', 'publish'),
        (r'subscribe', 'subscribe'),
        (r'queue', 'queue'),
        (r'message', 'message'),
    ]
    
    EXTERNAL_API_INDICATORS = [
        (r'requests\.(get|post|put|delete)', 'http'),
        (r'httpx\.', 'http'),
        (r'aiohttp', 'http'),
        (r'fetch\s*\(', 'fetch'),
        (r'api\s*\.', 'api'),
        (r'webhook', 'webhook'),
    ]
    
    def __init__(self, codebase_analyzer: CodebaseAnalyzer = None):
        self.codebase = codebase_analyzer
        self._compiled_service = [(re.compile(p, re.IGNORECASE), t) for p, t in self.SERVICE_INDICATORS]
        self._compiled_db = [(re.compile(p, re.IGNORECASE), t) for p, t in self.DATABASE_INDICATORS]
        self._compiled_cache = [(re.compile(p, re.IGNORECASE), t) for p, t in self.CACHE_INDICATORS]
        self._compiled_mq = [(re.compile(p, re.IGNORECASE), t) for p, t in self.MQ_INDICATORS]
        self._compiled_api = [(re.compile(p, re.IGNORECASE), t) for p, t in self.EXTERNAL_API_INDICATORS]
    
    def analyze_enhanced(self, location: CodeLocation, code_content: str = None) -> Dict[str, Any]:
        """执行增强影响分析"""
        return {
            'service_impact': self._analyze_service_impact(location, code_content),
            'database_impact': self._analyze_database_impact(location, code_content),
            'cache_impact': self._analyze_cache_impact(location, code_content),
            'mq_impact': self._analyze_mq_impact(location, code_content),
            'external_api_impact': self._analyze_external_api_impact(location, code_content),
            'user_experience_impact': self._analyze_user_experience_impact(location),
            'overall_impact_score': 0.0,
            'recommendations': [],
        }
    
    def _analyze_service_impact(self, location: CodeLocation, code_content: str = None) -> Dict[str, Any]:
        """分析服务层影响"""
        impact = {
            'affected_services': [],
            'service_type': 'unknown',
            'impact_level': 'low',
            'description': ''
        }
        
        text = f"{location.file_path} {location.function_name} {location.class_name or ''}"
        if code_content:
            text += f" {code_content}"
        
        for pattern, service_type in self._compiled_service:
            if pattern.search(text):
                impact['affected_services'].append(service_type)
                impact['service_type'] = service_type
        
        if impact['affected_services']:
            impact['impact_level'] = 'high' if 'service' in impact['affected_services'] else 'medium'
            impact['description'] = f"影响服务层组件: {', '.join(impact['affected_services'])}"
        
        return impact
    
    def _analyze_database_impact(self, location: CodeLocation, code_content: str = None) -> Dict[str, Any]:
        """分析数据库影响"""
        impact = {
            'db_operations': [],
            'impact_level': 'low',
            'data_risk': 'none',
            'description': ''
        }
        
        text = f"{location.function_name or ''} {location.code_snippet or ''}"
        if code_content:
            text += f" {code_content}"
        
        for pattern, op_type in self._compiled_db:
            if pattern.search(text):
                impact['db_operations'].append(op_type)
        
        if impact['db_operations']:
            write_ops = {'insert', 'update', 'delete'}
            if any(op in write_ops for op in impact['db_operations']):
                impact['impact_level'] = 'high'
                impact['data_risk'] = 'potential_data_loss'
                impact['description'] = "涉及数据库写操作，可能影响数据完整性"
            else:
                impact['impact_level'] = 'medium'
                impact['description'] = "涉及数据库读操作，可能影响查询性能"
        
        return impact
    
    def _analyze_cache_impact(self, location: CodeLocation, code_content: str = None) -> Dict[str, Any]:
        """分析缓存影响"""
        impact = {
            'cache_operations': [],
            'impact_level': 'low',
            'cache_risk': 'none',
            'description': ''
        }
        
        text = f"{location.file_path} {location.function_name or ''}"
        if code_content:
            text += f" {code_content}"
        
        for pattern, cache_type in self._compiled_cache:
            if pattern.search(text):
                impact['cache_operations'].append(cache_type)
        
        if impact['cache_operations']:
            impact['impact_level'] = 'medium'
            impact['cache_risk'] = 'potential_cache_inconsistency'
            impact['description'] = f"涉及缓存操作: {', '.join(impact['cache_operations'])}"
        
        return impact
    
    def _analyze_mq_impact(self, location: CodeLocation, code_content: str = None) -> Dict[str, Any]:
        """分析消息队列影响"""
        impact = {
            'mq_operations': [],
            'impact_level': 'low',
            'message_risk': 'none',
            'description': ''
        }
        
        text = f"{location.file_path} {location.function_name or ''}"
        if code_content:
            text += f" {code_content}"
        
        for pattern, mq_type in self._compiled_mq:
            if pattern.search(text):
                impact['mq_operations'].append(mq_type)
        
        if impact['mq_operations']:
            impact['impact_level'] = 'medium'
            impact['message_risk'] = 'potential_message_loss'
            impact['description'] = f"涉及消息队列: {', '.join(impact['mq_operations'])}"
        
        return impact
    
    def _analyze_external_api_impact(self, location: CodeLocation, code_content: str = None) -> Dict[str, Any]:
        """分析外部API影响"""
        impact = {
            'api_calls': [],
            'impact_level': 'low',
            'external_dependency': False,
            'description': ''
        }
        
        text = f"{location.function_name or ''} {location.code_snippet or ''}"
        if code_content:
            text += f" {code_content}"
        
        for pattern, api_type in self._compiled_api:
            if pattern.search(text):
                impact['api_calls'].append(api_type)
                impact['external_dependency'] = True
        
        if impact['api_calls']:
            impact['impact_level'] = 'medium'
            impact['description'] = f"涉及外部API调用: {', '.join(impact['api_calls'])}"
        
        return impact
    
    def _analyze_user_experience_impact(self, location: CodeLocation) -> Dict[str, Any]:
        """分析用户体验影响"""
        impact = {
            'affected_user_flows': [],
            'impact_level': 'low',
            'user_facing': False,
            'description': ''
        }
        
        file_path_lower = location.file_path.lower()
        func_lower = (location.function_name or '').lower()
        
        user_facing_indicators = [
            ('api', 'API接口'),
            ('controller', '控制器'),
            ('handler', '处理器'),
            ('view', '视图'),
            ('route', '路由'),
            ('endpoint', '端点'),
        ]
        
        for indicator, desc in user_facing_indicators:
            if indicator in file_path_lower or indicator in func_lower:
                impact['affected_user_flows'].append(desc)
                impact['user_facing'] = True
        
        if impact['affected_user_flows']:
            impact['impact_level'] = 'high'
            impact['description'] = f"影响用户交互: {', '.join(impact['affected_user_flows'])}"
        
        return impact


class EnhancedFixPriorityEvaluator:
    """增强修复优先级评估器 - 提供更全面的优先级评估
    
    评估维度：
    - 业务影响权重
    - 技术债务权重
    - 安全风险权重
    - 用户体验权重
    - 修复成本权重
    """
    
    BUSINESS_IMPACT_WEIGHTS = {
        'payment': 1.0,
        'transaction': 0.95,
        'security': 0.95,
        'auth': 0.9,
        'user': 0.8,
        'order': 0.85,
        'account': 0.8,
        'checkout': 0.9,
        'invoice': 0.75,
        'report': 0.5,
        'admin': 0.6,
        'config': 0.4,
    }
    
    SECURITY_RISK_PATTERNS = [
        (r'sql\s*injection', 1.0),
        (r'xss', 0.9),
        (r'csrf', 0.85),
        (r'auth(entication)?\s*(fail|error|bypass)', 0.95),
        (r'permission\s*(denied|error)', 0.8),
        (r'access\s*(denied|violation)', 0.85),
        (r'sensitive\s*data', 0.9),
        (r'password', 0.85),
        (r'token', 0.8),
        (r'credential', 0.85),
    ]
    
    TECH_DEBT_INDICATORS = [
        (r'todo', 0.3),
        (r'fixme', 0.4),
        (r'hack', 0.5),
        (r'workaround', 0.5),
        (r'deprecated', 0.6),
        (r'legacy', 0.4),
    ]
    
    def __init__(self):
        self.priority_counter = 0
        self._compiled_security = [(re.compile(p, re.IGNORECASE), w) for p, w in self.SECURITY_RISK_PATTERNS]
        self._compiled_debt = [(re.compile(p, re.IGNORECASE), w) for p, w in self.TECH_DEBT_INDICATORS]
    
    def evaluate_enhanced(self, issue: IssueLocation) -> Dict[str, Any]:
        """执行增强优先级评估"""
        self.priority_counter += 1
        
        business_score = self._calculate_business_impact_score(issue)
        security_score = self._calculate_security_risk_score(issue)
        tech_debt_score = self._calculate_tech_debt_score(issue)
        user_exp_score = self._calculate_user_experience_score(issue)
        cost_score = self._calculate_fix_cost_score(issue)
        
        composite = self._calculate_weighted_composite(
            business_score, security_score, tech_debt_score, user_exp_score, cost_score
        )
        
        return {
            'priority_id': f"EFP-{self.priority_counter:03d}",
            'business_impact_score': business_score,
            'security_risk_score': security_score,
            'tech_debt_score': tech_debt_score,
            'user_experience_score': user_exp_score,
            'fix_cost_score': cost_score,
            'composite_score': composite,
            'priority_level': self._determine_priority_level(composite),
            'priority_label': self._get_priority_label(composite),
            'deadline': self._suggest_deadline(composite),
            'recommended_action': self._recommend_action(composite),
            'risk_factors': self._identify_risk_factors(issue),
            'mitigation_strategies': self._suggest_mitigation(issue),
        }
    
    def _calculate_business_impact_score(self, issue: IssueLocation) -> float:
        """计算业务影响分数"""
        score = 0.0
        
        text = ""
        if issue.primary_location:
            text += f"{issue.primary_location.file_path} {issue.primary_location.function_name or ''} "
        if issue.description:
            text += issue.description
        text_lower = text.lower()
        
        for keyword, weight in self.BUSINESS_IMPACT_WEIGHTS.items():
            if keyword in text_lower:
                score = max(score, weight)
        
        if issue.impact_scope:
            if '高业务影响' in issue.impact_scope.business_impact:
                score = max(score, 0.9)
            elif '中等业务影响' in issue.impact_scope.business_impact:
                score = max(score, 0.7)
        
        return score
    
    def _calculate_security_risk_score(self, issue: IssueLocation) -> float:
        """计算安全风险分数"""
        if issue.issue_type == IssueType.SECURITY_ISSUE:
            return 1.0
        
        score = 0.0
        text = issue.description or ""
        
        for pattern, weight in self._compiled_security:
            if pattern.search(text):
                score = max(score, weight)
        
        return score
    
    def _calculate_tech_debt_score(self, issue: IssueLocation) -> float:
        """计算技术债务分数"""
        score = 0.0
        text = issue.description or ""
        
        if issue.primary_location and issue.primary_location.code_snippet:
            text += " " + issue.primary_location.code_snippet
        
        for pattern, weight in self._compiled_debt:
            if pattern.search(text):
                score = max(score, weight)
        
        return score
    
    def _calculate_user_experience_score(self, issue: IssueLocation) -> float:
        """计算用户体验影响分数"""
        score = 0.0
        
        if issue.impact_scope:
            if issue.impact_scope.affected_apis:
                score += 0.3 * min(1.0, len(issue.impact_scope.affected_apis) / 3)
            
            if 'user' in str(issue.impact_scope.affected_functions).lower():
                score += 0.3
        
        if issue.severity in [Severity.CRITICAL, Severity.HIGH]:
            score += 0.4
        elif issue.severity == Severity.MEDIUM:
            score += 0.2
        
        return min(1.0, score)
    
    def _calculate_fix_cost_score(self, issue: IssueLocation) -> float:
        """计算修复成本分数（分数越高成本越低）"""
        score = 0.5
        
        if issue.root_cause:
            complexity_scores = {'low': 0.4, 'medium': 0.2, 'high': 0.0}
            score += complexity_scores.get(issue.root_cause.fix_complexity, 0.1)
        
        if issue.call_chain:
            if issue.call_chain.depth > 10:
                score -= 0.2
            elif issue.call_chain.depth > 5:
                score -= 0.1
        
        if issue.impact_scope:
            if '测试覆盖良好' in issue.impact_scope.test_coverage_impact:
                score += 0.2
            elif '缺少相关测试' in issue.impact_scope.test_coverage_impact:
                score -= 0.2
        
        return max(0.0, min(1.0, score))
    
    def _calculate_weighted_composite(
        self,
        business: float,
        security: float,
        tech_debt: float,
        user_exp: float,
        cost: float
    ) -> float:
        """计算加权综合分数"""
        weights = {
            'business': 0.30,
            'security': 0.25,
            'tech_debt': 0.10,
            'user_exp': 0.20,
            'cost': 0.15,
        }
        
        composite = (
            business * weights['business'] +
            security * weights['security'] +
            tech_debt * weights['tech_debt'] +
            user_exp * weights['user_exp'] +
            cost * weights['cost']
        )
        
        return round(composite * 100, 1)
    
    def _determine_priority_level(self, composite: float) -> int:
        """确定优先级等级"""
        if composite >= 75:
            return 1
        elif composite >= 60:
            return 2
        elif composite >= 45:
            return 3
        elif composite >= 30:
            return 4
        else:
            return 5
    
    def _get_priority_label(self, composite: float) -> str:
        """获取优先级标签"""
        labels = {
            1: "P0 - 紧急",
            2: "P1 - 高优先级",
            3: "P2 - 中优先级",
            4: "P3 - 低优先级",
            5: "P4 - 可延后"
        }
        return labels.get(self._determine_priority_level(composite), "P3")
    
    def _suggest_deadline(self, composite: float) -> str:
        """建议截止时间"""
        deadlines = {
            1: "立即修复（4小时内）",
            2: "尽快修复（24小时内）",
            3: "计划修复（本周内）",
            4: "安排修复（两周内）",
            5: "有空修复（可排期）"
        }
        return deadlines.get(self._determine_priority_level(composite), "计划修复")
    
    def _recommend_action(self, composite: float) -> str:
        """推荐行动"""
        actions = {
            1: "立即组织修复，必要时升级处理",
            2: "优先安排资源，确保及时完成",
            3: "纳入迭代计划，按优先级处理",
            4: "在空闲时间处理或批量修复",
            5: "可考虑在重构时一并处理"
        }
        return actions.get(self._determine_priority_level(composite), "纳入计划处理")
    
    def _identify_risk_factors(self, issue: IssueLocation) -> List[str]:
        """识别风险因素"""
        factors = []
        
        if issue.severity == Severity.CRITICAL:
            factors.append("严重级别问题")
        if issue.issue_type == IssueType.SECURITY_ISSUE:
            factors.append("安全相关问题")
        if issue.impact_scope and len(issue.impact_scope.affected_apis) > 3:
            factors.append("影响多个API接口")
        if issue.root_cause and issue.root_cause.confidence == Confidence.LOW:
            factors.append("根因不明确")
        if issue.call_chain and issue.call_chain.depth > 10:
            factors.append("调用链复杂")
        
        return factors[:5]
    
    def _suggest_mitigation(self, issue: IssueLocation) -> List[str]:
        """建议缓解策略"""
        strategies = []
        
        if issue.severity in [Severity.CRITICAL, Severity.HIGH]:
            strategies.append("考虑临时回滚或禁用相关功能")
        
        if issue.issue_type == IssueType.SECURITY_ISSUE:
            strategies.append("立即评估安全风险范围")
            strategies.append("检查是否存在数据泄露")
        
        if issue.impact_scope and '高业务影响' in issue.impact_scope.business_impact:
            strategies.append("通知相关业务方")
            strategies.append("准备应急预案")
        
        if issue.root_cause and issue.root_cause.fix_complexity == 'high':
            strategies.append("考虑分阶段修复")
            strategies.append("准备充分的测试用例")
        
        return strategies[:5]


class CodeLocationPreciseLocator:
    """代码位置精确定位器 - 提供精确的代码位置定位
    
    功能：
    - AST解析定位
    - 符号表分析
    - 调用图构建
    - 依赖关系追踪
    """
    
    def __init__(self, codebase_path: Path = None):
        self.codebase_path = codebase_path
        self._ast_cache: Dict[str, ast.AST] = {}
        self._symbol_table: Dict[str, List[CodeLocation]] = defaultdict(list)
    
    def locate_precise(self, error_message: str, stack_trace: List[StackTraceFrame] = None) -> Dict[str, Any]:
        """执行精确代码定位"""
        return {
            'primary_location': self._locate_primary(error_message, stack_trace),
            'related_locations': self._locate_related(error_message, stack_trace),
            'symbol_references': self._find_symbol_references(error_message),
            'call_graph': self._build_call_graph(stack_trace) if stack_trace else None,
            'dependency_chain': self._trace_dependencies(error_message),
            'confidence': self._calculate_location_confidence(error_message, stack_trace),
        }
    
    def _locate_primary(self, error_message: str, stack_trace: List[StackTraceFrame] = None) -> Optional[Dict[str, Any]]:
        """定位主要位置"""
        if not stack_trace:
            return self._locate_from_error_message(error_message)
        
        user_frames = [f for f in stack_trace if f.is_user_code]
        if not user_frames:
            user_frames = stack_trace
        
        primary_frame = user_frames[0]
        
        return {
            'file_path': primary_frame.file_path,
            'line_number': primary_frame.line_number,
            'function_name': primary_frame.function_name,
            'code_snippet': primary_frame.code_line,
            'location_type': 'stack_trace',
            'confidence': 0.9 if primary_frame.is_user_code else 0.7,
        }
    
    def _locate_from_error_message(self, error_message: str) -> Optional[Dict[str, Any]]:
        """从错误消息定位"""
        file_pattern = re.compile(r'File\s+"([^"]+)",\s+line\s+(\d+)')
        match = file_pattern.search(error_message)
        
        if match:
            return {
                'file_path': match.group(1),
                'line_number': int(match.group(2)),
                'location_type': 'error_message',
                'confidence': 0.8,
            }
        
        return None
    
    def _locate_related(self, error_message: str, stack_trace: List[StackTraceFrame] = None) -> List[Dict[str, Any]]:
        """定位相关位置"""
        related = []
        
        if stack_trace:
            for i, frame in enumerate(stack_trace[:5]):
                related.append({
                    'file_path': frame.file_path,
                    'line_number': frame.line_number,
                    'function_name': frame.function_name,
                    'relation': 'call_chain',
                    'depth': i,
                })
        
        return related
    
    def _find_symbol_references(self, error_message: str) -> List[Dict[str, Any]]:
        """查找符号引用"""
        references = []
        
        symbol_patterns = [
            r"'(\w+)'",
            r'"(\w+)"',
            r'variable\s+[\'"]?(\w+)[\'"]?',
            r'function\s+[\'"]?(\w+)[\'"]?',
            r'module\s+[\'"]?(\w+)[\'"]?',
        ]
        
        for pattern in symbol_patterns:
            for match in re.finditer(pattern, error_message, re.IGNORECASE):
                symbol = match.group(1)
                if len(symbol) > 2:
                    references.append({
                        'symbol': symbol,
                        'context': match.group(0),
                        'type': 'referenced_in_error',
                    })
        
        return references[:10]
    
    def _build_call_graph(self, stack_trace: List[StackTraceFrame]) -> Dict[str, Any]:
        """构建调用图"""
        if not stack_trace:
            return {'nodes': [], 'edges': []}
        
        nodes = []
        edges = []
        
        for i, frame in enumerate(stack_trace):
            node_id = f"{frame.file_path}:{frame.function_name}"
            nodes.append({
                'id': node_id,
                'file': frame.file_path,
                'function': frame.function_name,
                'line': frame.line_number,
                'is_user_code': frame.is_user_code,
            })
            
            if i > 0:
                prev_node_id = f"{stack_trace[i-1].file_path}:{stack_trace[i-1].function_name}"
                edges.append({
                    'source': prev_node_id,
                    'target': node_id,
                    'type': 'calls',
                })
        
        return {'nodes': nodes, 'edges': edges}
    
    def _trace_dependencies(self, error_message: str) -> List[Dict[str, Any]]:
        """追踪依赖链"""
        dependencies = []
        
        import_patterns = [
            r'import\s+(\w+)',
            r'from\s+([\w.]+)\s+import',
            r'module\s+[\'"]?([\w.]+)[\'"]?',
        ]
        
        for pattern in import_patterns:
            for match in re.finditer(pattern, error_message, re.IGNORECASE):
                dependencies.append({
                    'module': match.group(1),
                    'type': 'import_dependency',
                    'context': match.group(0),
                })
        
        return dependencies[:10]
    
    def _calculate_location_confidence(self, error_message: str, stack_trace: List[StackTraceFrame] = None) -> float:
        """计算位置置信度"""
        if not stack_trace:
            if 'File' in error_message and 'line' in error_message:
                return 0.7
            return 0.3
        
        user_frames = [f for f in stack_trace if f.is_user_code]
        
        if user_frames:
            return 0.9
        elif stack_trace:
            return 0.6
        
        return 0.4


class IssueLocationReportEnhancer:
    """问题定位报告增强器 - 生成更详细的报告
    
    功能：
    - 执行摘要生成
    - 详细问题分析
    - 趋势分析
    - 修复建议汇总
    """
    
    def enhance_report(self, report: IssueLocationReport) -> Dict[str, Any]:
        """增强问题定位报告"""
        return {
            'enhanced_summary': self._generate_enhanced_summary(report),
            'issue_breakdown': self._generate_issue_breakdown(report),
            'trend_analysis': self._analyze_trends(report),
            'fix_recommendations': self._generate_fix_recommendations(report),
            'resource_estimation': self._estimate_resources(report),
            'risk_assessment': self._assess_risks(report),
        }
    
    def _generate_enhanced_summary(self, report: IssueLocationReport) -> Dict[str, Any]:
        """生成增强摘要"""
        return {
            'total_issues': report.total_issues,
            'severity_breakdown': {
                'critical': report.critical_count,
                'high': report.high_count,
                'medium': report.medium_count,
                'low': report.low_count,
            },
            'health_score': self._calculate_health_score(report),
            'priority_summary': self._summarize_priorities(report),
            'key_concerns': self._identify_key_concerns(report),
        }
    
    def _calculate_health_score(self, report: IssueLocationReport) -> float:
        """计算健康分数"""
        score = 100.0
        
        score -= report.critical_count * 20
        score -= report.high_count * 10
        score -= report.medium_count * 5
        score -= report.low_count * 2
        
        return max(0.0, min(100.0, score))
    
    def _summarize_priorities(self, report: IssueLocationReport) -> Dict[str, int]:
        """汇总优先级"""
        priorities = defaultdict(int)
        
        for issue in report.issues:
            if issue.fix_priority:
                priorities[issue.fix_priority.priority_label] += 1
        
        return dict(priorities)
    
    def _identify_key_concerns(self, report: IssueLocationReport) -> List[str]:
        """识别关键关注点"""
        concerns = []
        
        if report.critical_count > 0:
            concerns.append(f"存在 {report.critical_count} 个严重问题需要立即处理")
        
        security_issues = sum(1 for i in report.issues if i.issue_type == IssueType.SECURITY_ISSUE)
        if security_issues > 0:
            concerns.append(f"发现 {security_issues} 个安全问题")
        
        if report.high_count > 3:
            concerns.append(f"高优先级问题积压 ({report.high_count} 个)")
        
        return concerns[:5]
    
    def _generate_issue_breakdown(self, report: IssueLocationReport) -> Dict[str, Any]:
        """生成问题分解"""
        by_type = defaultdict(int)
        by_file = defaultdict(int)
        by_root_cause = defaultdict(int)
        
        for issue in report.issues:
            by_type[issue.issue_type.value] += 1
            
            if issue.primary_location:
                by_file[issue.primary_location.file_path] += 1
            
            if issue.root_cause:
                for factor in issue.root_cause.contributing_factors:
                    if '根因类型:' in factor:
                        cause = factor.replace('根因类型: ', '')
                        by_root_cause[cause] += 1
        
        return {
            'by_type': dict(sorted(by_type.items(), key=lambda x: x[1], reverse=True)),
            'by_file': dict(sorted(by_file.items(), key=lambda x: x[1], reverse=True)[:10]),
            'by_root_cause': dict(sorted(by_root_cause.items(), key=lambda x: x[1], reverse=True)[:5]),
        }
    
    def _analyze_trends(self, report: IssueLocationReport) -> Dict[str, Any]:
        """分析趋势"""
        return {
            'issue_frequency': self._analyze_issue_frequency(report),
            'severity_trend': self._analyze_severity_trend(report),
            'type_distribution_trend': self._analyze_type_trend(report),
        }
    
    def _analyze_issue_frequency(self, report: IssueLocationReport) -> Dict[str, Any]:
        """分析问题频率"""
        total = report.total_issues
        
        return {
            'total': total,
            'average_per_file': total / max(1, len(set(
                i.primary_location.file_path for i in report.issues if i.primary_location
            ))),
        }
    
    def _analyze_severity_trend(self, report: IssueLocationReport) -> Dict[str, Any]:
        """分析严重程度趋势"""
        total = max(1, report.total_issues)
        
        return {
            'critical_ratio': report.critical_count / total,
            'high_ratio': report.high_count / total,
            'medium_ratio': report.medium_count / total,
            'low_ratio': report.low_count / total,
        }
    
    def _analyze_type_trend(self, report: IssueLocationReport) -> Dict[str, Any]:
        """分析类型趋势"""
        return report.issue_type_distribution
    
    def _generate_fix_recommendations(self, report: IssueLocationReport) -> List[Dict[str, Any]]:
        """生成修复建议"""
        recommendations = []
        
        critical_issues = [i for i in report.issues if i.severity == Severity.CRITICAL]
        if critical_issues:
            recommendations.append({
                'priority': 1,
                'action': '立即处理严重问题',
                'details': f'共 {len(critical_issues)} 个严重问题需要立即修复',
                'estimated_effort': '高',
            })
        
        security_issues = [i for i in report.issues if i.issue_type == IssueType.SECURITY_ISSUE]
        if security_issues:
            recommendations.append({
                'priority': 1,
                'action': '修复安全问题',
                'details': f'共 {len(security_issues)} 个安全问题',
                'estimated_effort': '高',
            })
        
        common_causes = report.common_root_causes[:3]
        if common_causes:
            recommendations.append({
                'priority': 2,
                'action': '解决常见根因',
                'details': f'常见问题: {", ".join(common_causes)}',
                'estimated_effort': '中',
            })
        
        return recommendations
    
    def _estimate_resources(self, report: IssueLocationReport) -> Dict[str, Any]:
        """估算资源需求"""
        total_hours = 0
        
        for issue in report.issues:
            if issue.root_cause and issue.root_cause.estimated_fix_time:
                time_str = issue.root_cause.estimated_fix_time
                if '小时' in time_str:
                    match = re.search(r'(\d+)', time_str)
                    if match:
                        total_hours += int(match.group(1))
                elif '分钟' in time_str:
                    match = re.search(r'(\d+)', time_str)
                    if match:
                        total_hours += int(match.group(1)) / 60
        
        return {
            'estimated_hours': round(total_hours, 1),
            'recommended_team_size': max(1, int(total_hours / 8)),
            'estimated_days': round(total_hours / 8, 1),
        }
    
    def _assess_risks(self, report: IssueLocationReport) -> Dict[str, Any]:
        """评估风险"""
        risks = []
        
        if report.critical_count > 0:
            risks.append({
                'type': 'critical_issues',
                'level': 'high',
                'description': f'存在 {report.critical_count} 个严重问题',
            })
        
        security_count = sum(1 for i in report.issues if i.issue_type == IssueType.SECURITY_ISSUE)
        if security_count > 0:
            risks.append({
                'type': 'security',
                'level': 'high',
                'description': f'存在 {security_count} 个安全问题',
            })
        
        api_impact_count = sum(
            1 for i in report.issues
            if i.impact_scope and i.impact_scope.affected_apis
        )
        if api_impact_count > 3:
            risks.append({
                'type': 'api_impact',
                'level': 'medium',
                'description': f'{api_impact_count} 个问题影响API接口',
            })
        
        return {
            'overall_risk': 'high' if any(r['level'] == 'high' for r in risks) else 'medium' if risks else 'low',
            'risk_factors': risks,
        }
