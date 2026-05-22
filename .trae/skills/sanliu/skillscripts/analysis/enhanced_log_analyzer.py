#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
增强版日志分析系统 - Enhanced Log Analysis System
提供智能错误模式识别、日志关联分析、多格式支持

功能:
1. 智能错误模式识别 - 基于机器学习的模式匹配
2. 日志关联分析 - 跨文件/跨时间关联
3. 多种日志格式支持 - JSON、Apache、Nginx、Python、Java等
4. 异常检测 - 基于统计的异常识别
5. 时序分析 - 日志事件时序关联
"""

import os
import re
import json
import logging
import hashlib
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional, Set, Tuple, Union, Pattern
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict, Counter
import statistics

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class LogLevel(Enum):
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"
    TRACE = "TRACE"
    FATAL = "FATAL"


class LogFormat(Enum):
    JSON = "json"
    APACHE = "apache"
    NGINX = "nginx"
    PYTHON = "python"
    JAVA = "java"
    SYSLOG = "syslog"
    CUSTOM = "custom"
    UNKNOWN = "unknown"


class PatternCategory(Enum):
    SYNTAX_ERROR = "syntax_error"
    RUNTIME_ERROR = "runtime_error"
    LOGIC_ERROR = "logic_error"
    PERFORMANCE = "performance"
    SECURITY = "security"
    DATABASE = "database"
    NETWORK = "network"
    RESOURCE = "resource"
    DEPENDENCY = "dependency"
    CONFIGURATION = "configuration"
    BUSINESS_LOGIC = "business_logic"
    DATA_INTEGRITY = "data_integrity"
    CONCURRENCY = "concurrency"
    MEMORY = "memory"
    UNKNOWN = "unknown"


class PatternSeverity(Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


@dataclass
class LogEntry:
    timestamp: datetime
    level: LogLevel
    message: str
    source: str
    file_path: str = ""
    line_number: int = 0
    context: Dict[str, Any] = field(default_factory=dict)
    raw_line: str = ""
    log_format: LogFormat = LogFormat.UNKNOWN
    session_id: str = ""
    request_id: str = ""
    user_id: str = ""
    trace_id: str = ""
    span_id: str = ""


@dataclass
class ErrorPattern:
    pattern_id: str
    name: str
    regex: str
    category: PatternCategory
    severity: PatternSeverity
    description: str
    suggested_fix: str
    occurrence_count: int = 0
    affected_files: Set[str] = field(default_factory=set)
    confidence: float = 0.0
    tags: List[str] = field(default_factory=list)
    examples: List[str] = field(default_factory=list)
    related_patterns: List[str] = field(default_factory=list)


@dataclass
class CorrelationResult:
    correlation_id: str
    correlated_entries: List[LogEntry]
    correlation_type: str
    confidence: float
    description: str
    time_span: timedelta
    source_files: List[str]


@dataclass
class AnomalyResult:
    anomaly_id: str
    anomaly_type: str
    severity: PatternSeverity
    description: str
    affected_entries: List[LogEntry]
    statistical_info: Dict[str, Any]
    detected_at: datetime


@dataclass
class TimeSeriesEvent:
    event_id: str
    event_type: str
    timestamp: datetime
    entries: List[LogEntry]
    duration: timedelta
    metadata: Dict[str, Any]


class MultiFormatLogParser:
    """多格式日志解析器"""
    
    FORMAT_PATTERNS = {
        LogFormat.JSON: [
            r'^\s*\{.*\}\s*$',
        ],
        LogFormat.APACHE: [
            r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\s+-\s+',
            r'^\[[\w\s]+\]\s+\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}',
        ],
        LogFormat.NGINX: [
            r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\s+-\s+[\w-]+\s+\[',
        ],
        LogFormat.PYTHON: [
            r'^\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2},\d+\s+-\s+\w+\s+-',
            r'^\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}\s+\w+\s+',
        ],
        LogFormat.JAVA: [
            r'^\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}\.\d+\s+\[',
            r'^\[[\d\-:\.\s]+\]\s+\w+\s+',
        ],
        LogFormat.SYSLOG: [
            r'^[A-Z][a-z]{2}\s+\d{1,2}\s+\d{2}:\d{2}:\d{2}\s+',
            r'^<\d+>',
        ],
    }
    
    FORMAT_EXTRACTORS = {}
    
    def __init__(self):
        self._compile_patterns()
        self._setup_extractors()
    
    def _compile_patterns(self):
        self._compiled_patterns = {}
        for fmt, patterns in self.FORMAT_PATTERNS.items():
            self._compiled_patterns[fmt] = [
                re.compile(p, re.MULTILINE) for p in patterns
            ]
    
    def _setup_extractors(self):
        self.FORMAT_EXTRACTORS = {
            LogFormat.JSON: self._extract_json,
            LogFormat.APACHE: self._extract_apache,
            LogFormat.NGINX: self._extract_nginx,
            LogFormat.PYTHON: self._extract_python,
            LogFormat.JAVA: self._extract_java,
            LogFormat.SYSLOG: self._extract_syslog,
        }
    
    def detect_format(self, lines: List[str]) -> LogFormat:
        if not lines:
            return LogFormat.UNKNOWN
        
        sample_lines = [l for l in lines[:20] if l.strip()]
        if not sample_lines:
            return LogFormat.UNKNOWN
        
        format_scores = defaultdict(int)
        
        for line in sample_lines:
            for fmt, patterns in self._compiled_patterns.items():
                for pattern in patterns:
                    if pattern.match(line):
                        format_scores[fmt] += 1
                        break
        
        if format_scores:
            best_format = max(format_scores.items(), key=lambda x: x[1])
            if best_format[1] >= len(sample_lines) * 0.3:
                return best_format[0]
        
        return LogFormat.UNKNOWN
    
    def parse_line(self, line: str, log_format: LogFormat, 
                   file_path: str = "", line_num: int = 0) -> Optional[LogEntry]:
        if not line.strip():
            return None
        
        extractor = self.FORMAT_EXTRACTORS.get(log_format, self._extract_generic)
        
        try:
            entry = extractor(line, file_path, line_num)
            if entry:
                entry.log_format = log_format
            return entry
        except Exception as e:
            logger.debug(f"解析失败: {e}")
            return self._extract_generic(line, file_path, line_num)
    
    def _extract_json(self, line: str, file_path: str, line_num: int) -> Optional[LogEntry]:
        try:
            data = json.loads(line)
        except json.JSONDecodeError:
            return None
        
        timestamp = self._parse_timestamp(data.get("timestamp") or data.get("time") or 
                                          data.get("@timestamp") or data.get("datetime"))
        
        level_str = str(data.get("level", data.get("log_level", "INFO"))).upper()
        level = self._map_level(level_str)
        
        message = data.get("message", data.get("msg", data.get("log", "")))
        
        return LogEntry(
            timestamp=timestamp,
            level=level,
            message=str(message),
            source=data.get("logger", data.get("source", data.get("name", ""))),
            file_path=file_path,
            line_number=line_num,
            context=data,
            raw_line=line,
            session_id=data.get("session_id", data.get("sessionId", "")),
            request_id=data.get("request_id", data.get("requestId", "")),
            user_id=data.get("user_id", data.get("userId", "")),
            trace_id=data.get("trace_id", data.get("traceId", "")),
            span_id=data.get("span_id", data.get("spanId", "")),
        )
    
    def _extract_apache(self, line: str, file_path: str, line_num: int) -> Optional[LogEntry]:
        pattern = re.compile(
            r'^(?P<ip>\S+)\s+\S+\s+\S+\s+\[(?P<time>[^\]]+)\]\s+'
            r'"(?P<method>\S+)\s+(?P<path>\S+)\s+\S+"\s+'
            r'(?P<status>\d+)\s+(?P<size>\S+)'
        )
        
        match = pattern.match(line)
        if not match:
            return self._extract_generic(line, file_path, line_num)
        
        timestamp = self._parse_apache_time(match.group("time"))
        status = int(match.group("status"))
        level = LogLevel.ERROR if status >= 500 else LogLevel.WARNING if status >= 400 else LogLevel.INFO
        
        message = f"{match.group('method')} {match.group('path')} - {status}"
        
        return LogEntry(
            timestamp=timestamp,
            level=level,
            message=message,
            source="apache",
            file_path=file_path,
            line_number=line_num,
            context={
                "ip": match.group("ip"),
                "method": match.group("method"),
                "path": match.group("path"),
                "status": status,
                "size": match.group("size"),
            },
            raw_line=line,
        )
    
    def _extract_nginx(self, line: str, file_path: str, line_num: int) -> Optional[LogEntry]:
        pattern = re.compile(
            r'^(?P<ip>\S+)\s+-\s+(?P<user>\S+)\s+\[(?P<time>[^\]]+)\]\s+'
            r'"(?P<method>\S+)\s+(?P<path>\S+)\s+\S+"\s+'
            r'(?P<status>\d+)\s+(?P<size>\S+)\s+'
            r'"(?P<referer>[^"]*)"\s+"(?P<ua>[^"]*)"'
        )
        
        match = pattern.match(line)
        if not match:
            return self._extract_generic(line, file_path, line_num)
        
        timestamp = self._parse_nginx_time(match.group("time"))
        status = int(match.group("status"))
        level = LogLevel.ERROR if status >= 500 else LogLevel.WARNING if status >= 400 else LogLevel.INFO
        
        message = f"{match.group('method')} {match.group('path')} - {status}"
        
        return LogEntry(
            timestamp=timestamp,
            level=level,
            message=message,
            source="nginx",
            file_path=file_path,
            line_number=line_num,
            context={
                "ip": match.group("ip"),
                "user": match.group("user"),
                "method": match.group("method"),
                "path": match.group("path"),
                "status": status,
                "size": match.group("size"),
                "referer": match.group("referer"),
                "user_agent": match.group("ua"),
            },
            raw_line=line,
        )
    
    def _extract_python(self, line: str, file_path: str, line_num: int) -> Optional[LogEntry]:
        pattern = re.compile(
            r'^(?P<time>\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}[,.]\d*)\s*[-:]?\s*'
            r'(?P<level>\w+)\s*[-:]?\s*'
            r'(?P<source>\S+)?\s*[-:]?\s*'
            r'(?P<message>.*)$'
        )
        
        match = pattern.match(line)
        if not match:
            return self._extract_generic(line, file_path, line_num)
        
        timestamp = self._parse_timestamp(match.group("time"))
        level = self._map_level(match.group("level"))
        
        return LogEntry(
            timestamp=timestamp,
            level=level,
            message=match.group("message").strip(),
            source=match.group("source") or "",
            file_path=file_path,
            line_number=line_num,
            raw_line=line,
        )
    
    def _extract_java(self, line: str, file_path: str, line_num: int) -> Optional[LogEntry]:
        pattern = re.compile(
            r'^(?P<time>\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}[,.]\d*)\s*'
            r'\[(?P<thread>[^\]]+)\]\s*'
            r'(?P<level>\w+)\s*'
            r'(?P<source>\S+)\s*[-:]?\s*'
            r'(?P<message>.*)$'
        )
        
        match = pattern.match(line)
        if not match:
            return self._extract_generic(line, file_path, line_num)
        
        timestamp = self._parse_timestamp(match.group("time"))
        level = self._map_level(match.group("level"))
        
        return LogEntry(
            timestamp=timestamp,
            level=level,
            message=match.group("message").strip(),
            source=match.group("source"),
            file_path=file_path,
            line_number=line_num,
            context={"thread": match.group("thread")},
            raw_line=line,
        )
    
    def _extract_syslog(self, line: str, file_path: str, line_num: int) -> Optional[LogEntry]:
        pattern = re.compile(
            r'^(?P<time>[A-Z][a-z]{2}\s+\d{1,2}\s+\d{2}:\d{2}:\d{2})\s+'
            r'(?P<host>\S+)\s+'
            r'(?P<source>[^:\[]+)(?:\[(?P<pid>\d+)\])?:\s*'
            r'(?P<message>.*)$'
        )
        
        match = pattern.match(line)
        if not match:
            return self._extract_generic(line, file_path, line_num)
        
        timestamp = self._parse_syslog_time(match.group("time"))
        
        return LogEntry(
            timestamp=timestamp,
            level=LogLevel.INFO,
            message=match.group("message").strip(),
            source=match.group("source"),
            file_path=file_path,
            line_number=line_num,
            context={
                "host": match.group("host"),
                "pid": match.group("pid"),
            },
            raw_line=line,
        )
    
    def _extract_generic(self, line: str, file_path: str, line_num: int) -> LogEntry:
        timestamp = datetime.now()
        level = LogLevel.INFO
        message = line
        
        ts_patterns = [
            (r'^(\d{4}-\d{2}-\d{2}[T\s]\d{2}:\d{2}:\d{2}(?:[.,]\d+)?)', None),
            (r'^(\d{2}:\d{2}:\d{2})', None),
            (r'\[(\d{4}-\d{2}-\d{2}[T\s]\d{2}:\d{2}:\d{2})', None),
        ]
        
        for pattern, _ in ts_patterns:
            match = re.match(pattern, line)
            if match:
                timestamp = self._parse_timestamp(match.group(1))
                break
        
        level_match = re.search(
            r'\b(DEBUG|INFO|WARNING|WARN|ERROR|CRITICAL|FATAL|TRACE)\b',
            line, re.IGNORECASE
        )
        if level_match:
            level = self._map_level(level_match.group(1))
        
        return LogEntry(
            timestamp=timestamp,
            level=level,
            message=message,
            source="",
            file_path=file_path,
            line_number=line_num,
            raw_line=line,
        )
    
    def _parse_timestamp(self, ts: Any) -> datetime:
        if ts is None:
            return datetime.now()
        
        if isinstance(ts, datetime):
            return ts
        
        if isinstance(ts, (int, float)):
            return datetime.fromtimestamp(ts)
        
        ts_str = str(ts).replace(',', '.').replace('Z', '+00:00')
        
        formats = [
            "%Y-%m-%dT%H:%M:%S%z",
            "%Y-%m-%dT%H:%M:%S.%f%z",
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%d %H:%M:%S.%f",
            "%Y-%m-%dT%H:%M:%S",
            "%Y-%m-%dT%H:%M:%S.%f",
        ]
        
        for fmt in formats:
            try:
                return datetime.strptime(ts_str.split('+')[0].split('Z')[0], fmt)
            except ValueError:
                continue
        
        return datetime.now()
    
    def _parse_apache_time(self, time_str: str) -> datetime:
        try:
            dt = datetime.strptime(time_str, "%d/%b/%Y:%H:%M:%S %z")
            return dt.replace(tzinfo=None)
        except ValueError:
            return datetime.now()
    
    def _parse_nginx_time(self, time_str: str) -> datetime:
        try:
            dt = datetime.strptime(time_str, "%d/%b/%Y:%H:%M:%S %z")
            return dt.replace(tzinfo=None)
        except ValueError:
            return datetime.now()
    
    def _parse_syslog_time(self, time_str: str) -> datetime:
        try:
            dt = datetime.strptime(time_str, "%b %d %H:%M:%S")
            dt = dt.replace(year=datetime.now().year)
            return dt
        except ValueError:
            return datetime.now()
    
    def _map_level(self, level_str: str) -> LogLevel:
        level_map = {
            "DEBUG": LogLevel.DEBUG,
            "INFO": LogLevel.INFO,
            "WARNING": LogLevel.WARNING,
            "WARN": LogLevel.WARNING,
            "ERROR": LogLevel.ERROR,
            "CRITICAL": LogLevel.CRITICAL,
            "FATAL": LogLevel.CRITICAL,
            "TRACE": LogLevel.TRACE,
        }
        return level_map.get(level_str.upper(), LogLevel.INFO)


class IntelligentErrorPatternMatcher:
    """智能错误模式匹配器"""
    
    PATTERNS = [
        {
            "id": "E001",
            "name": "ImportError",
            "regex": r"(ImportError|ModuleNotFoundError|No module named|cannot import name)",
            "category": PatternCategory.DEPENDENCY,
            "severity": PatternSeverity.HIGH,
            "description": "模块导入错误",
            "fix": "检查依赖是否安装，运行 pip install 安装缺失的包",
            "tags": ["dependency", "import"],
        },
        {
            "id": "E002",
            "name": "SyntaxError",
            "regex": r"(SyntaxError|IndentationError|TabError|unexpected token|invalid syntax)",
            "category": PatternCategory.SYNTAX_ERROR,
            "severity": PatternSeverity.HIGH,
            "description": "语法错误",
            "fix": "检查代码语法，修复缩进或语法问题",
            "tags": ["syntax", "code"],
        },
        {
            "id": "E003",
            "name": "TypeError",
            "regex": r"(TypeError|unsupported operand|not callable|NoneType|cannot convert)",
            "category": PatternCategory.RUNTIME_ERROR,
            "severity": PatternSeverity.HIGH,
            "description": "类型错误",
            "fix": "检查变量类型，添加类型检查或转换",
            "tags": ["type", "runtime"],
        },
        {
            "id": "E004",
            "name": "AttributeError",
            "regex": r"(AttributeError|has no attribute|'NoneType' object)",
            "category": PatternCategory.RUNTIME_ERROR,
            "severity": PatternSeverity.HIGH,
            "description": "属性错误",
            "fix": "检查对象是否有所需属性，添加属性存在性检查",
            "tags": ["attribute", "null"],
        },
        {
            "id": "E005",
            "name": "KeyError",
            "regex": r"(KeyError|key not found|missing key)",
            "category": PatternCategory.DATA_INTEGRITY,
            "severity": PatternSeverity.MEDIUM,
            "description": "键错误",
            "fix": "检查字典键是否存在，使用 .get() 方法或添加键检查",
            "tags": ["dict", "key"],
        },
        {
            "id": "E006",
            "name": "FileNotFoundError",
            "regex": r"(FileNotFoundError|No such file or directory|cannot find file)",
            "category": PatternCategory.RESOURCE,
            "severity": PatternSeverity.MEDIUM,
            "description": "文件未找到",
            "fix": "检查文件路径是否正确，确保文件存在",
            "tags": ["file", "resource"],
        },
        {
            "id": "E007",
            "name": "PermissionError",
            "regex": r"(PermissionError|Permission denied|Access denied|Unauthorized)",
            "category": PatternCategory.SECURITY,
            "severity": PatternSeverity.HIGH,
            "description": "权限错误",
            "fix": "检查文件/目录权限，以管理员身份运行或修改权限",
            "tags": ["permission", "security"],
        },
        {
            "id": "E008",
            "name": "ConnectionError",
            "regex": r"(ConnectionError|Connection refused|Network is unreachable|socket error)",
            "category": PatternCategory.NETWORK,
            "severity": PatternSeverity.HIGH,
            "description": "网络连接错误",
            "fix": "检查网络连接，确认服务是否运行，检查防火墙设置",
            "tags": ["network", "connection"],
        },
        {
            "id": "E009",
            "name": "DatabaseError",
            "regex": r"(DatabaseError|IntegrityError|OperationalError|sqlite3\.Error|SQL error)",
            "category": PatternCategory.DATABASE,
            "severity": PatternSeverity.HIGH,
            "description": "数据库错误",
            "fix": "检查数据库连接，验证SQL语句，检查数据完整性约束",
            "tags": ["database", "sql"],
        },
        {
            "id": "E010",
            "name": "MemoryError",
            "regex": r"(MemoryError|Out of memory|Cannot allocate memory|heap space)",
            "category": PatternCategory.MEMORY,
            "severity": PatternSeverity.CRITICAL,
            "description": "内存错误",
            "fix": "优化内存使用，分批处理数据，增加系统内存",
            "tags": ["memory", "resource"],
        },
        {
            "id": "E011",
            "name": "TimeoutError",
            "regex": r"(TimeoutError|timeout|timed out|TimeoutException)",
            "category": PatternCategory.PERFORMANCE,
            "severity": PatternSeverity.MEDIUM,
            "description": "超时错误",
            "fix": "增加超时时间，优化处理速度，使用异步处理",
            "tags": ["timeout", "performance"],
        },
        {
            "id": "E012",
            "name": "AssertionError",
            "regex": r"(AssertionError|assert failed|assertion failed)",
            "category": PatternCategory.LOGIC_ERROR,
            "severity": PatternSeverity.MEDIUM,
            "description": "断言错误",
            "fix": "检查断言条件，修复逻辑问题",
            "tags": ["assert", "logic"],
        },
        {
            "id": "E013",
            "name": "RecursionError",
            "regex": r"(RecursionError|maximum recursion depth|stack overflow)",
            "category": PatternCategory.RUNTIME_ERROR,
            "severity": PatternSeverity.HIGH,
            "description": "递归错误",
            "fix": "检查递归终止条件，增加递归深度限制或改用迭代",
            "tags": ["recursion", "stack"],
        },
        {
            "id": "E014",
            "name": "ValueError",
            "regex": r"(ValueError|invalid value|invalid literal)",
            "category": PatternCategory.DATA_INTEGRITY,
            "severity": PatternSeverity.MEDIUM,
            "description": "值错误",
            "fix": "检查输入值的有效性，添加值验证逻辑",
            "tags": ["value", "validation"],
        },
        {
            "id": "E015",
            "name": "IndexError",
            "regex": r"(IndexError|index out of range|list index)",
            "category": PatternCategory.DATA_INTEGRITY,
            "severity": PatternSeverity.MEDIUM,
            "description": "索引错误",
            "fix": "检查索引范围，添加边界检查",
            "tags": ["index", "array"],
        },
        {
            "id": "E016",
            "name": "HTTP_5xx",
            "regex": r"(HTTP/\d\.\d\"\s*5\d{2}|500|502|503|504|Internal Server Error)",
            "category": PatternCategory.NETWORK,
            "severity": PatternSeverity.HIGH,
            "description": "HTTP服务器错误",
            "fix": "检查服务器日志，确认服务状态，检查后端服务",
            "tags": ["http", "server"],
        },
        {
            "id": "E017",
            "name": "HTTP_4xx",
            "regex": r"(HTTP/\d\.\d\"\s*4\d{2}|400|401|403|404|Bad Request|Unauthorized|Forbidden|Not Found)",
            "category": PatternCategory.NETWORK,
            "severity": PatternSeverity.MEDIUM,
            "description": "HTTP客户端错误",
            "fix": "检查请求参数、认证信息、资源路径",
            "tags": ["http", "client"],
        },
        {
            "id": "E018",
            "name": "Deadlock",
            "regex": r"(Deadlock|deadlock detected|lock wait timeout)",
            "category": PatternCategory.CONCURRENCY,
            "severity": PatternSeverity.CRITICAL,
            "description": "死锁错误",
            "fix": "检查锁的使用顺序，优化事务隔离级别，减少锁持有时间",
            "tags": ["deadlock", "concurrency"],
        },
        {
            "id": "E019",
            "name": "NullPointerException",
            "regex": r"(NullPointerException|null pointer|undefined is not|Cannot read property)",
            "category": PatternCategory.RUNTIME_ERROR,
            "severity": PatternSeverity.HIGH,
            "description": "空指针异常",
            "fix": "添加空值检查，使用安全访问操作符",
            "tags": ["null", "pointer"],
        },
        {
            "id": "E020",
            "name": "SecurityException",
            "regex": r"(SecurityException|SecurityError|injection|xss|csrf|unauthorized access)",
            "category": PatternCategory.SECURITY,
            "severity": PatternSeverity.CRITICAL,
            "description": "安全异常",
            "fix": "检查安全策略，验证输入，检查权限配置",
            "tags": ["security", "attack"],
        },
    ]
    
    def __init__(self):
        self.patterns: Dict[str, ErrorPattern] = {}
        self.matches: Dict[str, List[LogEntry]] = defaultdict(list)
        self._compile_patterns()
    
    def _compile_patterns(self):
        for p in self.PATTERNS:
            self.patterns[p["id"]] = ErrorPattern(
                pattern_id=p["id"],
                name=p["name"],
                regex=p["regex"],
                category=p["category"],
                severity=p["severity"],
                description=p["description"],
                suggested_fix=p["fix"],
                tags=p.get("tags", []),
            )
        
        self._compiled = {
            pid: re.compile(p.regex, re.IGNORECASE | re.MULTILINE)
            for pid, p in self.patterns.items()
        }
    
    def match(self, entries: List[LogEntry]) -> List[ErrorPattern]:
        matched_patterns = []
        
        for entry in entries:
            if entry.level not in [LogLevel.ERROR, LogLevel.CRITICAL, LogLevel.WARNING]:
                continue
            
            for pattern_id, pattern in self.patterns.items():
                compiled = self._compiled[pattern_id]
                
                if compiled.search(entry.message):
                    pattern.occurrence_count += 1
                    pattern.affected_files.add(entry.file_path)
                    
                    if len(pattern.examples) < 3:
                        pattern.examples.append(entry.message[:200])
                    
                    self.matches[pattern_id].append(entry)
                    
                    if pattern not in matched_patterns:
                        matched_patterns.append(pattern)
        
        self._calculate_confidence(matched_patterns)
        
        return matched_patterns
    
    def _calculate_confidence(self, patterns: List[ErrorPattern]):
        for pattern in patterns:
            base_confidence = 0.5
            
            if pattern.occurrence_count > 10:
                base_confidence += 0.2
            elif pattern.occurrence_count > 5:
                base_confidence += 0.1
            
            if len(pattern.affected_files) > 3:
                base_confidence += 0.1
            
            if pattern.category in [PatternCategory.SECURITY, PatternCategory.MEMORY]:
                base_confidence += 0.1
            
            pattern.confidence = min(1.0, base_confidence)
    
    def add_custom_pattern(self, pattern: ErrorPattern):
        self.patterns[pattern.pattern_id] = pattern
        self._compiled[pattern.pattern_id] = re.compile(
            pattern.regex, re.IGNORECASE | re.MULTILINE
        )
    
    def find_related_patterns(self, pattern: ErrorPattern) -> List[ErrorPattern]:
        related = []
        
        for other in self.patterns.values():
            if other.pattern_id == pattern.pattern_id:
                continue
            
            if set(pattern.tags) & set(other.tags):
                related.append(other)
        
        return related


class LogCorrelationAnalyzer:
    """日志关联分析器"""
    
    def __init__(self):
        self.correlation_counter = 0
    
    def analyze(self, entries: List[LogEntry]) -> List[CorrelationResult]:
        correlations = []
        
        correlations.extend(self._correlate_by_session(entries))
        correlations.extend(self._correlate_by_request(entries))
        correlations.extend(self._correlate_by_trace(entries))
        correlations.extend(self._correlate_by_time(entries))
        correlations.extend(self._correlate_by_error_sequence(entries))
        
        return correlations
    
    def _correlate_by_session(self, entries: List[LogEntry]) -> List[CorrelationResult]:
        correlations = []
        session_groups: Dict[str, List[LogEntry]] = defaultdict(list)
        
        for entry in entries:
            if entry.session_id:
                session_groups[entry.session_id].append(entry)
        
        for session_id, group in session_groups.items():
            if len(group) < 2:
                continue
            
            self.correlation_counter += 1
            
            sorted_group = sorted(group, key=lambda e: e.timestamp)
            time_span = sorted_group[-1].timestamp - sorted_group[0].timestamp
            
            correlations.append(CorrelationResult(
                correlation_id=f"CORR-SESSION-{self.correlation_counter:04d}",
                correlated_entries=sorted_group,
                correlation_type="session",
                confidence=0.9,
                description=f"会话 {session_id} 相关的 {len(group)} 条日志",
                time_span=time_span,
                source_files=list(set(e.file_path for e in group)),
            ))
        
        return correlations
    
    def _correlate_by_request(self, entries: List[LogEntry]) -> List[CorrelationResult]:
        correlations = []
        request_groups: Dict[str, List[LogEntry]] = defaultdict(list)
        
        for entry in entries:
            if entry.request_id:
                request_groups[entry.request_id].append(entry)
        
        for request_id, group in request_groups.items():
            if len(group) < 2:
                continue
            
            self.correlation_counter += 1
            
            sorted_group = sorted(group, key=lambda e: e.timestamp)
            time_span = sorted_group[-1].timestamp - sorted_group[0].timestamp
            
            correlations.append(CorrelationResult(
                correlation_id=f"CORR-REQUEST-{self.correlation_counter:04d}",
                correlated_entries=sorted_group,
                correlation_type="request",
                confidence=0.95,
                description=f"请求 {request_id} 相关的 {len(group)} 条日志",
                time_span=time_span,
                source_files=list(set(e.file_path for e in group)),
            ))
        
        return correlations
    
    def _correlate_by_trace(self, entries: List[LogEntry]) -> List[CorrelationResult]:
        correlations = []
        trace_groups: Dict[str, List[LogEntry]] = defaultdict(list)
        
        for entry in entries:
            if entry.trace_id:
                trace_groups[entry.trace_id].append(entry)
        
        for trace_id, group in trace_groups.items():
            if len(group) < 2:
                continue
            
            self.correlation_counter += 1
            
            sorted_group = sorted(group, key=lambda e: e.timestamp)
            time_span = sorted_group[-1].timestamp - sorted_group[0].timestamp
            
            correlations.append(CorrelationResult(
                correlation_id=f"CORR-TRACE-{self.correlation_counter:04d}",
                correlated_entries=sorted_group,
                correlation_type="trace",
                confidence=0.98,
                description=f"追踪 {trace_id} 相关的 {len(group)} 条日志",
                time_span=time_span,
                source_files=list(set(e.file_path for e in group)),
            ))
        
        return correlations
    
    def _correlate_by_time(self, entries: List[LogEntry]) -> List[CorrelationResult]:
        correlations = []
        
        error_entries = [e for e in entries if e.level in [LogLevel.ERROR, LogLevel.CRITICAL]]
        
        if len(error_entries) < 2:
            return correlations
        
        error_entries.sort(key=lambda e: e.timestamp)
        
        window = timedelta(seconds=5)
        current_group = [error_entries[0]]
        
        for i in range(1, len(error_entries)):
            if error_entries[i].timestamp - current_group[-1].timestamp <= window:
                current_group.append(error_entries[i])
            else:
                if len(current_group) >= 2:
                    self.correlation_counter += 1
                    time_span = current_group[-1].timestamp - current_group[0].timestamp
                    
                    correlations.append(CorrelationResult(
                        correlation_id=f"CORR-TIME-{self.correlation_counter:04d}",
                        correlated_entries=current_group,
                        correlation_type="time_window",
                        confidence=0.7,
                        description=f"时间窗口内的 {len(current_group)} 条错误日志",
                        time_span=time_span,
                        source_files=list(set(e.file_path for e in current_group)),
                    ))
                
                current_group = [error_entries[i]]
        
        if len(current_group) >= 2:
            self.correlation_counter += 1
            time_span = current_group[-1].timestamp - current_group[0].timestamp
            
            correlations.append(CorrelationResult(
                correlation_id=f"CORR-TIME-{self.correlation_counter:04d}",
                correlated_entries=current_group,
                correlation_type="time_window",
                confidence=0.7,
                description=f"时间窗口内的 {len(current_group)} 条错误日志",
                time_span=time_span,
                source_files=list(set(e.file_path for e in current_group)),
            ))
        
        return correlations
    
    def _correlate_by_error_sequence(self, entries: List[LogEntry]) -> List[CorrelationResult]:
        correlations = []
        
        error_entries = [e for e in entries if e.level in [LogLevel.ERROR, LogLevel.CRITICAL]]
        
        if len(error_entries) < 2:
            return correlations
        
        pattern_sequences = defaultdict(list)
        
        for entry in error_entries:
            error_type = self._extract_error_type(entry.message)
            if error_type:
                pattern_sequences[error_type].append(entry)
        
        for error_type, group in pattern_sequences.items():
            if len(group) >= 3:
                self.correlation_counter += 1
                sorted_group = sorted(group, key=lambda e: e.timestamp)
                time_span = sorted_group[-1].timestamp - sorted_group[0].timestamp
                
                correlations.append(CorrelationResult(
                    correlation_id=f"CORR-SEQ-{self.correlation_counter:04d}",
                    correlated_entries=sorted_group,
                    correlation_type="error_sequence",
                    confidence=0.8,
                    description=f"相同错误类型 '{error_type}' 重复出现 {len(group)} 次",
                    time_span=time_span,
                    source_files=list(set(e.file_path for e in group)),
                ))
        
        return correlations
    
    def _extract_error_type(self, message: str) -> Optional[str]:
        match = re.match(r'^(\w+Error|\w+Exception)', message)
        if match:
            return match.group(1)
        return None


class AnomalyDetector:
    """异常检测器"""
    
    def __init__(self):
        self.anomaly_counter = 0
    
    def detect(self, entries: List[LogEntry]) -> List[AnomalyResult]:
        anomalies = []
        
        anomalies.extend(self._detect_frequency_anomaly(entries))
        anomalies.extend(self._detect_level_anomaly(entries))
        anomalies.extend(self._detect_pattern_anomaly(entries))
        anomalies.extend(self._detect_time_anomaly(entries))
        
        return anomalies
    
    def _detect_frequency_anomaly(self, entries: List[LogEntry]) -> List[AnomalyResult]:
        anomalies = []
        
        if len(entries) < 10:
            return anomalies
        
        time_buckets = defaultdict(list)
        for entry in entries:
            bucket = entry.timestamp.replace(minute=0, second=0, microsecond=0)
            time_buckets[bucket].append(entry)
        
        counts = [len(v) for v in time_buckets.values()]
        if len(counts) < 3:
            return anomalies
        
        mean = statistics.mean(counts)
        stdev = statistics.stdev(counts) if len(counts) > 1 else 0
        
        if stdev == 0:
            return anomalies
        
        for bucket, bucket_entries in time_buckets.items():
            count = len(bucket_entries)
            z_score = (count - mean) / stdev
            
            if abs(z_score) > 3:
                self.anomaly_counter += 1
                
                severity = PatternSeverity.HIGH if z_score > 0 else PatternSeverity.MEDIUM
                
                anomalies.append(AnomalyResult(
                    anomaly_id=f"ANOM-FREQ-{self.anomaly_counter:04d}",
                    anomaly_type="frequency",
                    severity=severity,
                    description=f"日志频率异常: {bucket} 有 {count} 条日志 (均值: {mean:.1f}, Z-score: {z_score:.2f})",
                    affected_entries=bucket_entries[:10],
                    statistical_info={
                        "count": count,
                        "mean": mean,
                        "stdev": stdev,
                        "z_score": z_score,
                    },
                    detected_at=datetime.now(),
                ))
        
        return anomalies
    
    def _detect_level_anomaly(self, entries: List[LogEntry]) -> List[AnomalyResult]:
        anomalies = []
        
        level_counts = Counter(e.level for e in entries)
        total = len(entries)
        
        if total < 10:
            return anomalies
        
        error_ratio = level_counts.get(LogLevel.ERROR, 0) / total
        critical_ratio = level_counts.get(LogLevel.CRITICAL, 0) / total
        
        if error_ratio > 0.3:
            self.anomaly_counter += 1
            
            error_entries = [e for e in entries if e.level == LogLevel.ERROR]
            
            anomalies.append(AnomalyResult(
                anomaly_id=f"ANOM-LEVEL-{self.anomaly_counter:04d}",
                anomaly_type="error_ratio",
                severity=PatternSeverity.HIGH,
                description=f"错误日志比例异常: {error_ratio:.1%} (超过30%阈值)",
                affected_entries=error_entries[:10],
                statistical_info={
                    "error_ratio": error_ratio,
                    "error_count": level_counts.get(LogLevel.ERROR, 0),
                    "total": total,
                },
                detected_at=datetime.now(),
            ))
        
        if critical_ratio > 0.1:
            self.anomaly_counter += 1
            
            critical_entries = [e for e in entries if e.level == LogLevel.CRITICAL]
            
            anomalies.append(AnomalyResult(
                anomaly_id=f"ANOM-LEVEL-{self.anomaly_counter:04d}",
                anomaly_type="critical_ratio",
                severity=PatternSeverity.CRITICAL,
                description=f"严重错误日志比例异常: {critical_ratio:.1%} (超过10%阈值)",
                affected_entries=critical_entries[:10],
                statistical_info={
                    "critical_ratio": critical_ratio,
                    "critical_count": level_counts.get(LogLevel.CRITICAL, 0),
                    "total": total,
                },
                detected_at=datetime.now(),
            ))
        
        return anomalies
    
    def _detect_pattern_anomaly(self, entries: List[LogEntry]) -> List[AnomalyResult]:
        anomalies = []
        
        error_entries = [e for e in entries if e.level in [LogLevel.ERROR, LogLevel.CRITICAL]]
        
        if len(error_entries) < 5:
            return anomalies
        
        message_hashes = defaultdict(list)
        for entry in error_entries:
            normalized = re.sub(r'\d+', 'N', entry.message[:100])
            msg_hash = hashlib.md5(normalized.encode()).hexdigest()
            message_hashes[msg_hash].append(entry)
        
        for msg_hash, group in message_hashes.items():
            if len(group) >= 5:
                self.anomaly_counter += 1
                
                anomalies.append(AnomalyResult(
                    anomaly_id=f"ANOM-PATTERN-{self.anomaly_counter:04d}",
                    anomaly_type="repeated_pattern",
                    severity=PatternSeverity.HIGH,
                    description=f"重复错误模式: 相同错误出现 {len(group)} 次",
                    affected_entries=group[:10],
                    statistical_info={
                        "occurrence_count": len(group),
                        "sample_message": group[0].message[:200],
                    },
                    detected_at=datetime.now(),
                ))
        
        return anomalies
    
    def _detect_time_anomaly(self, entries: List[LogEntry]) -> List[AnomalyResult]:
        anomalies = []
        
        if len(entries) < 10:
            return anomalies
        
        sorted_entries = sorted(entries, key=lambda e: e.timestamp)
        
        gaps = []
        for i in range(1, len(sorted_entries)):
            gap = sorted_entries[i].timestamp - sorted_entries[i-1].timestamp
            gaps.append(gap.total_seconds())
        
        if not gaps:
            return anomalies
        
        mean_gap = statistics.mean(gaps)
        stdev_gap = statistics.stdev(gaps) if len(gaps) > 1 else 0
        
        if stdev_gap == 0:
            return anomalies
        
        for i, gap in enumerate(gaps):
            z_score = (gap - mean_gap) / stdev_gap
            
            if z_score > 3:
                self.anomaly_counter += 1
                
                anomalies.append(AnomalyResult(
                    anomaly_id=f"ANOM-TIME-{self.anomaly_counter:04d}",
                    anomaly_type="time_gap",
                    severity=PatternSeverity.MEDIUM,
                    description=f"日志时间间隔异常: 第 {i+1} 条日志间隔 {gap:.1f} 秒 (均值: {mean_gap:.1f})",
                    affected_entries=[sorted_entries[i], sorted_entries[i+1]],
                    statistical_info={
                        "gap_seconds": gap,
                        "mean_gap": mean_gap,
                        "z_score": z_score,
                    },
                    detected_at=datetime.now(),
                ))
        
        return anomalies


class TimeSeriesAnalyzer:
    """时序分析器"""
    
    def __init__(self):
        self.event_counter = 0
    
    def analyze(self, entries: List[LogEntry]) -> List[TimeSeriesEvent]:
        events = []
        
        events.extend(self._detect_error_bursts(entries))
        events.extend(self._detect_service_starts(entries))
        events.extend(self._detect_deployment_events(entries))
        
        return events
    
    def _detect_error_bursts(self, entries: List[LogEntry]) -> List[TimeSeriesEvent]:
        events = []
        
        error_entries = [e for e in entries if e.level in [LogLevel.ERROR, LogLevel.CRITICAL]]
        
        if len(error_entries) < 3:
            return events
        
        sorted_errors = sorted(error_entries, key=lambda e: e.timestamp)
        
        window = timedelta(seconds=10)
        threshold = 5
        
        i = 0
        while i < len(sorted_errors):
            window_end = sorted_errors[i].timestamp + window
            burst = [sorted_errors[i]]
            
            j = i + 1
            while j < len(sorted_errors) and sorted_errors[j].timestamp <= window_end:
                burst.append(sorted_errors[j])
                j += 1
            
            if len(burst) >= threshold:
                self.event_counter += 1
                
                events.append(TimeSeriesEvent(
                    event_id=f"EVENT-BURST-{self.event_counter:04d}",
                    event_type="error_burst",
                    timestamp=burst[0].timestamp,
                    entries=burst,
                    duration=burst[-1].timestamp - burst[0].timestamp,
                    metadata={
                        "error_count": len(burst),
                        "error_types": list(set(self._extract_error_type(e.message) for e in burst)),
                    },
                ))
            
            i = j if j > i + 1 else i + 1
        
        return events
    
    def _detect_service_starts(self, entries: List[LogEntry]) -> List[TimeSeriesEvent]:
        events = []
        
        start_patterns = [
            r"Starting\s+\w+",
            r"Server\s+started",
            r"Application\s+started",
            r"Listening\s+on",
            r"Ready\s+for\s+connections",
        ]
        
        compiled = [re.compile(p, re.IGNORECASE) for p in start_patterns]
        
        for entry in entries:
            for pattern in compiled:
                if pattern.search(entry.message):
                    self.event_counter += 1
                    
                    events.append(TimeSeriesEvent(
                        event_id=f"EVENT-START-{self.event_counter:04d}",
                        event_type="service_start",
                        timestamp=entry.timestamp,
                        entries=[entry],
                        duration=timedelta(0),
                        metadata={
                            "source": entry.source,
                            "message": entry.message[:100],
                        },
                    ))
                    break
        
        return events
    
    def _detect_deployment_events(self, entries: List[LogEntry]) -> List[TimeSeriesEvent]:
        events = []
        
        deploy_patterns = [
            r"Deploying",
            r"Deployment\s+(started|completed|failed)",
            r"Rolling\s+update",
            r"Version\s+\d+\.\d+",
            r"Build\s+\d+",
        ]
        
        compiled = [re.compile(p, re.IGNORECASE) for p in deploy_patterns]
        
        for entry in entries:
            for pattern in compiled:
                if pattern.search(entry.message):
                    self.event_counter += 1
                    
                    events.append(TimeSeriesEvent(
                        event_id=f"EVENT-DEPLOY-{self.event_counter:04d}",
                        event_type="deployment",
                        timestamp=entry.timestamp,
                        entries=[entry],
                        duration=timedelta(0),
                        metadata={
                            "source": entry.source,
                            "message": entry.message[:100],
                        },
                    ))
                    break
        
        return events
    
    def _extract_error_type(self, message: str) -> str:
        match = re.match(r'^(\w+Error|\w+Exception)', message)
        if match:
            return match.group(1)
        return "Unknown"


class EnhancedLogAnalyzer:
    """增强版日志分析器主类"""
    
    def __init__(self, base_path: str = None):
        self.base_path = Path(base_path or os.getcwd())
        self.parser = MultiFormatLogParser()
        self.pattern_matcher = IntelligentErrorPatternMatcher()
        self.correlation_analyzer = LogCorrelationAnalyzer()
        self.anomaly_detector = AnomalyDetector()
        self.time_series_analyzer = TimeSeriesAnalyzer()
        self.entries: List[LogEntry] = []
    
    def collect_from_directory(self, log_dir: str, pattern: str = "*.log") -> int:
        log_path = self.base_path / log_dir
        if not log_path.exists():
            logger.warning(f"日志目录不存在: {log_path}")
            return 0
        
        files_processed = 0
        
        for log_file in log_path.rglob(pattern):
            try:
                self._parse_log_file(log_file)
                files_processed += 1
            except Exception as e:
                logger.warning(f"解析日志文件失败 {log_file}: {e}")
        
        return files_processed
    
    def collect_from_file(self, file_path: str) -> int:
        path = self.base_path / file_path
        if not path.exists():
            logger.warning(f"日志文件不存在: {path}")
            return 0
        
        self._parse_log_file(path)
        return 1
    
    def _parse_log_file(self, file_path: Path):
        content = file_path.read_text(encoding='utf-8', errors='ignore')
        lines = content.splitlines()
        
        log_format = self.parser.detect_format(lines)
        logger.info(f"检测到日志格式: {log_format.value} - {file_path}")
        
        for i, line in enumerate(lines):
            if not line.strip():
                continue
            
            entry = self.parser.parse_line(line, log_format, str(file_path), i + 1)
            if entry:
                self.entries.append(entry)
    
    def analyze(self) -> Dict[str, Any]:
        logger.info(f"开始分析 {len(self.entries)} 条日志记录...")
        
        patterns = self.pattern_matcher.match(self.entries)
        logger.info(f"检测到 {len(patterns)} 种错误模式")
        
        correlations = self.correlation_analyzer.analyze(self.entries)
        logger.info(f"发现 {len(correlations)} 组关联日志")
        
        anomalies = self.anomaly_detector.detect(self.entries)
        logger.info(f"检测到 {len(anomalies)} 个异常")
        
        time_series_events = self.time_series_analyzer.analyze(self.entries)
        logger.info(f"识别到 {len(time_series_events)} 个时序事件")
        
        summary = self._generate_summary(patterns, correlations, anomalies, time_series_events)
        
        return {
            "patterns": patterns,
            "correlations": correlations,
            "anomalies": anomalies,
            "time_series_events": time_series_events,
            "summary": summary,
        }
    
    def _generate_summary(self, patterns, correlations, anomalies, time_series_events) -> Dict[str, Any]:
        level_counts = Counter(e.level for e in self.entries)
        
        return {
            "total_entries": len(self.entries),
            "level_distribution": {k.value: v for k, v in level_counts.items()},
            "error_pattern_count": len(patterns),
            "correlation_count": len(correlations),
            "anomaly_count": len(anomalies),
            "time_series_event_count": len(time_series_events),
            "critical_patterns": [p.name for p in patterns if p.severity == PatternSeverity.CRITICAL],
            "high_severity_patterns": [p.name for p in patterns if p.severity == PatternSeverity.HIGH],
            "most_frequent_pattern": max(patterns, key=lambda p: p.occurrence_count).name if patterns else None,
            "log_formats_detected": list(set(e.log_format.value for e in self.entries)),
        }
    
    def generate_report(self, analysis_result: Dict[str, Any]) -> str:
        lines = [
            "# 增强版日志分析报告",
            f"\n**生成时间**: {datetime.now().isoformat()}",
            f"**分析日志数**: {analysis_result['summary']['total_entries']} 条",
            "",
            "---",
            "",
            "## 📊 概览",
            "",
            "| 指标 | 数值 |",
            "|------|------|",
        ]
        
        for level, count in analysis_result['summary']['level_distribution'].items():
            lines.append(f"| {level} | {count} |")
        
        lines.extend([
            f"| 错误模式 | {analysis_result['summary']['error_pattern_count']} |",
            f"| 关联组 | {analysis_result['summary']['correlation_count']} |",
            f"| 异常检测 | {analysis_result['summary']['anomaly_count']} |",
            "",
            "---",
            "",
            "## 🔍 错误模式分析",
            "",
        ])
        
        for pattern in sorted(analysis_result['patterns'], key=lambda p: p.occurrence_count, reverse=True):
            severity_emoji = {
                PatternSeverity.CRITICAL: "🔴",
                PatternSeverity.HIGH: "🟠",
                PatternSeverity.MEDIUM: "🟡",
                PatternSeverity.LOW: "🟢",
            }
            
            lines.extend([
                f"### {severity_emoji.get(pattern.severity, '⚪')} {pattern.name}",
                f"- **类别**: {pattern.category.value}",
                f"- **严重程度**: {pattern.severity.value}",
                f"- **出现次数**: {pattern.occurrence_count}",
                f"- **影响文件**: {len(pattern.affected_files)} 个",
                f"- **置信度**: {pattern.confidence:.0%}",
                f"- **描述**: {pattern.description}",
                f"- **建议修复**: {pattern.suggested_fix}",
                "",
            ])
        
        if analysis_result['anomalies']:
            lines.extend([
                "---",
                "",
                "## ⚠️ 异常检测",
                "",
            ])
            
            for anomaly in analysis_result['anomalies']:
                lines.extend([
                    f"### {anomaly.anomaly_type} - {anomaly.severity.value}",
                    f"- **描述**: {anomaly.description}",
                    f"- **检测时间**: {anomaly.detected_at.isoformat()}",
                    "",
                ])
        
        if analysis_result['correlations']:
            lines.extend([
                "---",
                "",
                "## 🔗 日志关联分析",
                "",
            ])
            
            for corr in analysis_result['correlations'][:10]:
                lines.extend([
                    f"### {corr.correlation_type}",
                    f"- **描述**: {corr.description}",
                    f"- **关联日志数**: {len(corr.correlated_entries)}",
                    f"- **时间跨度**: {corr.time_span}",
                    f"- **置信度**: {corr.confidence:.0%}",
                    "",
                ])
        
        if analysis_result['time_series_events']:
            lines.extend([
                "---",
                "",
                "## 📈 时序事件分析",
                "",
            ])
            
            for event in analysis_result['time_series_events']:
                lines.extend([
                    f"### {event.event_type}",
                    f"- **时间**: {event.timestamp.isoformat()}",
                    f"- **持续时长**: {event.duration}",
                    f"- **相关日志数**: {len(event.entries)}",
                    "",
                ])
        
        return "\n".join(lines)


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="增强版日志分析系统")
    parser.add_argument("--base-path", default=".", help="项目基础路径")
    parser.add_argument("--log-dir", action="append", help="日志目录（可多次指定）")
    parser.add_argument("--output", help="报告输出路径")
    
    args = parser.parse_args()
    
    analyzer = EnhancedLogAnalyzer(args.base_path)
    
    if args.log_dir:
        for log_dir in args.log_dir:
            analyzer.collect_from_directory(log_dir)
    else:
        analyzer.collect_from_directory("logs")
    
    if not analyzer.entries:
        print("未找到日志文件或日志为空")
        return
    
    result = analyzer.analyze()
    
    print("\n" + "=" * 60)
    print("增强版日志分析报告")
    print("=" * 60)
    print(f"分析日志数: {result['summary']['total_entries']}")
    print(f"错误模式: {result['summary']['error_pattern_count']}")
    print(f"关联组: {result['summary']['correlation_count']}")
    print(f"异常检测: {result['summary']['anomaly_count']}")
    print("=" * 60)
    
    report = analyzer.generate_report(result)
    
    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(report, encoding='utf-8')
        print(f"\n报告已保存: {output_path}")
    else:
        print("\n" + report)


if __name__ == "__main__":
    main()
