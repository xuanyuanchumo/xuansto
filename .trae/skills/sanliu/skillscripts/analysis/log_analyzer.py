#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
增强智能日志分析器 - Enhanced Intelligent Log Analyzer

支持多种日志格式的智能分析，包括：
- 多种日志格式解析（JSON、文本、CSV）
- 错误模式智能识别（正则表达式匹配 + 智能学习）
- 错误类型自动分类（基于规则和统计学习）
- 潜在问题预测（基于历史趋势分析）
- 日志关联分析（跨文件追踪）
- 异常检测和告警
- 生成日志分析报告

使用示例:
    python log_analyzer.py --log-dir ./logs --analyze
    python log_analyzer.py --log-file app.log --format json --report report.html
    python log_analyzer.py --log-dir ./logs --correlate --alert
    python log_analyzer.py --log-dir ./logs --predict --forecast-hours 24
"""

import argparse
import csv
import hashlib
import json
import logging
import math
import os
import re
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Pattern, Tuple, Union


class LogLevel(Enum):
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"
    UNKNOWN = "unknown"


class LogFormat(Enum):
    JSON = "json"
    TEXT = "text"
    CSV = "csv"
    AUTO = "auto"


class AlertSeverity(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ErrorCategory(Enum):
    NETWORK = "network"
    DATABASE = "database"
    MEMORY = "memory"
    FILE_SYSTEM = "file_system"
    PERMISSION = "permission"
    CONFIGURATION = "configuration"
    RUNTIME = "runtime"
    LOGIC = "logic"
    SECURITY = "security"
    PERFORMANCE = "performance"
    EXTERNAL_SERVICE = "external_service"
    RESOURCE = "resource"
    UNKNOWN = "unknown"


class PredictionConfidence(Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass
class LogEntry:
    timestamp: Optional[datetime] = None
    level: LogLevel = LogLevel.UNKNOWN
    message: str = ""
    source: str = ""
    logger_name: str = ""
    thread: str = ""
    extra: Dict[str, Any] = field(default_factory=dict)
    raw_line: str = ""
    file_path: str = ""
    line_number: int = 0
    error_category: ErrorCategory = ErrorCategory.UNKNOWN
    error_signature: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "level": self.level.value,
            "message": self.message,
            "source": self.source,
            "logger_name": self.logger_name,
            "thread": self.thread,
            "extra": self.extra,
            "file_path": self.file_path,
            "line_number": self.line_number,
            "error_category": self.error_category.value,
            "error_signature": self.error_signature
        }


@dataclass
class ErrorPattern:
    pattern_id: str
    name: str
    pattern: str
    severity: AlertSeverity
    description: str
    suggestion: str
    category: ErrorCategory = ErrorCategory.UNKNOWN
    keywords: List[str] = field(default_factory=list)
    compiled_pattern: Optional[Pattern] = None
    occurrence_count: int = 0
    first_seen: Optional[datetime] = None
    last_seen: Optional[datetime] = None

    def __post_init__(self):
        if self.pattern:
            self.compiled_pattern = re.compile(self.pattern, re.IGNORECASE)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "pattern_id": self.pattern_id,
            "name": self.name,
            "pattern": self.pattern,
            "severity": self.severity.value,
            "description": self.description,
            "suggestion": self.suggestion,
            "category": self.category.value,
            "keywords": self.keywords,
            "occurrence_count": self.occurrence_count,
            "first_seen": self.first_seen.isoformat() if self.first_seen else None,
            "last_seen": self.last_seen.isoformat() if self.last_seen else None
        }


@dataclass
class LogAlert:
    alert_id: str
    timestamp: str
    severity: AlertSeverity
    pattern_name: str
    message: str
    log_entry: LogEntry
    suggestion: str
    related_entries: List[LogEntry] = field(default_factory=list)
    category: ErrorCategory = ErrorCategory.UNKNOWN

    def to_dict(self) -> Dict[str, Any]:
        return {
            "alert_id": self.alert_id,
            "timestamp": self.timestamp,
            "severity": self.severity.value,
            "pattern_name": self.pattern_name,
            "message": self.message,
            "log_entry": self.log_entry.to_dict(),
            "suggestion": self.suggestion,
            "related_count": len(self.related_entries),
            "category": self.category.value
        }


@dataclass
class CorrelationResult:
    correlation_id: str
    entries: List[LogEntry]
    time_span_seconds: float
    pattern_type: str
    description: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "correlation_id": self.correlation_id,
            "entry_count": len(self.entries),
            "time_span_seconds": self.time_span_seconds,
            "pattern_type": self.pattern_type,
            "description": self.description,
            "entries": [e.to_dict() for e in self.entries[:10]]
        }


@dataclass
class ErrorClassification:
    category: ErrorCategory
    subcategory: str
    confidence: float
    keywords_matched: List[str]
    pattern_matched: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "category": self.category.value,
            "subcategory": self.subcategory,
            "confidence": self.confidence,
            "keywords_matched": self.keywords_matched,
            "pattern_matched": self.pattern_matched
        }


@dataclass
class PredictionResult:
    prediction_id: str
    prediction_type: str
    predicted_issue: str
    confidence: PredictionConfidence
    probability: float
    time_window_hours: int
    based_on_patterns: List[str]
    contributing_factors: List[str]
    recommendations: List[str]
    historical_context: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "prediction_id": self.prediction_id,
            "prediction_type": self.prediction_type,
            "predicted_issue": self.predicted_issue,
            "confidence": self.confidence.value,
            "probability": self.probability,
            "time_window_hours": self.time_window_hours,
            "based_on_patterns": self.based_on_patterns,
            "contributing_factors": self.contributing_factors,
            "recommendations": self.recommendations,
            "historical_context": self.historical_context
        }


@dataclass
class LogAnalysisReport:
    report_id: str
    generated_at: str
    log_files: List[str]
    total_entries: int
    entries_by_level: Dict[str, int]
    entries_by_category: Dict[str, int]
    error_patterns_found: List[Dict[str, Any]]
    alerts: List[LogAlert]
    correlations: List[CorrelationResult]
    anomalies: List[Dict[str, Any]]
    predictions: List[PredictionResult]
    summary: str
    recommendations: List[str]
    trend_analysis: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "report_id": self.report_id,
            "generated_at": self.generated_at,
            "log_files": self.log_files,
            "total_entries": self.total_entries,
            "entries_by_level": self.entries_by_level,
            "entries_by_category": self.entries_by_category,
            "error_patterns_found": self.error_patterns_found,
            "alerts": [a.to_dict() for a in self.alerts],
            "correlations": [c.to_dict() for c in self.correlations],
            "anomalies": self.anomalies,
            "predictions": [p.to_dict() for p in self.predictions],
            "summary": self.summary,
            "recommendations": self.recommendations,
            "trend_analysis": self.trend_analysis
        }


DEFAULT_ERROR_PATTERNS = [
    ErrorPattern(
        pattern_id="EP001",
        name="NullPointerException",
        pattern=r"NullPointerException|NoneType.*has no attribute|AttributeError",
        severity=AlertSeverity.CRITICAL,
        description="空指针异常，通常表示代码未正确处理None值",
        suggestion="添加None值检查，使用安全的访问方式",
        category=ErrorCategory.RUNTIME,
        keywords=["null", "none", "attribute", "pointer"]
    ),
    ErrorPattern(
        pattern_id="EP002",
        name="DatabaseConnectionError",
        pattern=r"ConnectionRefusedError|database.*connection.*failed|SQLSTATE|OperationalError|ConnectionPool",
        severity=AlertSeverity.HIGH,
        description="数据库连接错误",
        suggestion="检查数据库服务状态、连接配置和网络连通性",
        category=ErrorCategory.DATABASE,
        keywords=["database", "connection", "sql", "pool"]
    ),
    ErrorPattern(
        pattern_id="EP003",
        name="OutOfMemoryError",
        pattern=r"OutOfMemoryError|MemoryError|out of memory|MemoryAllocation",
        severity=AlertSeverity.CRITICAL,
        description="内存溢出错误",
        suggestion="检查内存泄漏、优化数据结构、增加内存限制",
        category=ErrorCategory.MEMORY,
        keywords=["memory", "allocation", "oom", "heap"]
    ),
    ErrorPattern(
        pattern_id="EP004",
        name="TimeoutError",
        pattern=r"TimeoutError|timed out|timeout.*exceeded|ReadTimeout|ConnectTimeout",
        severity=AlertSeverity.HIGH,
        description="超时错误",
        suggestion="检查网络延迟、优化查询、增加超时时间",
        category=ErrorCategory.NETWORK,
        keywords=["timeout", "timed out", "deadline"]
    ),
    ErrorPattern(
        pattern_id="EP005",
        name="FileNotFoundError",
        pattern=r"FileNotFoundError|No such file or directory|FileNotExists",
        severity=AlertSeverity.MEDIUM,
        description="文件未找到错误",
        suggestion="检查文件路径、权限和文件是否存在",
        category=ErrorCategory.FILE_SYSTEM,
        keywords=["file", "not found", "path", "directory"]
    ),
    ErrorPattern(
        pattern_id="EP006",
        name="PermissionDenied",
        pattern=r"PermissionError|Permission denied|Access denied|UnauthorizedAccess",
        severity=AlertSeverity.HIGH,
        description="权限拒绝错误",
        suggestion="检查文件/目录权限、用户权限配置",
        category=ErrorCategory.PERMISSION,
        keywords=["permission", "access", "denied", "unauthorized"]
    ),
    ErrorPattern(
        pattern_id="EP007",
        name="ImportError",
        pattern=r"ImportError|ModuleNotFoundError|cannot import name|DLL load failed",
        severity=AlertSeverity.HIGH,
        description="模块导入错误",
        suggestion="检查模块安装、Python路径配置",
        category=ErrorCategory.CONFIGURATION,
        keywords=["import", "module", "dll", "library"]
    ),
    ErrorPattern(
        pattern_id="EP008",
        name="StackOverflow",
        pattern=r"RecursionError|maximum recursion depth|stack overflow|StackOverflowError",
        severity=AlertSeverity.CRITICAL,
        description="栈溢出/递归错误",
        suggestion="检查递归终止条件、优化递归深度",
        category=ErrorCategory.RUNTIME,
        keywords=["recursion", "stack", "overflow", "depth"]
    ),
    ErrorPattern(
        pattern_id="EP009",
        name="HTTPError",
        pattern=r"HTTP.*[45]\d{2}|status code [45]\d{2}|HttpError|RequestException",
        severity=AlertSeverity.MEDIUM,
        description="HTTP错误响应",
        suggestion="检查API端点、请求参数、认证信息",
        category=ErrorCategory.NETWORK,
        keywords=["http", "status", "request", "response"]
    ),
    ErrorPattern(
        pattern_id="EP010",
        name="ValidationError",
        pattern=r"ValidationError|validation failed|invalid.*value|DataError",
        severity=AlertSeverity.MEDIUM,
        description="数据验证错误",
        suggestion="检查输入数据格式、验证规则配置",
        category=ErrorCategory.LOGIC,
        keywords=["validation", "invalid", "data", "format"]
    ),
    ErrorPattern(
        pattern_id="EP011",
        name="SecurityException",
        pattern=r"SecurityException|AuthenticationException|AccessControlException|SSLException",
        severity=AlertSeverity.CRITICAL,
        description="安全相关异常",
        suggestion="检查认证凭据、安全配置、访问控制策略",
        category=ErrorCategory.SECURITY,
        keywords=["security", "authentication", "ssl", "access control"]
    ),
    ErrorPattern(
        pattern_id="EP012",
        name="PerformanceWarning",
        pattern=r"slow query|performance warning|high latency|response time.*exceeded",
        severity=AlertSeverity.MEDIUM,
        description="性能警告",
        suggestion="优化查询、检查资源使用、考虑缓存策略",
        category=ErrorCategory.PERFORMANCE,
        keywords=["slow", "performance", "latency", "response time"]
    ),
    ErrorPattern(
        pattern_id="EP013",
        name="ResourceExhausted",
        pattern=r"ResourceExhausted|too many open files|disk.*full|quota.*exceeded",
        severity=AlertSeverity.HIGH,
        description="资源耗尽错误",
        suggestion="检查资源使用情况、增加资源配额、优化资源管理",
        category=ErrorCategory.RESOURCE,
        keywords=["resource", "exhausted", "disk", "quota", "limit"]
    ),
    ErrorPattern(
        pattern_id="EP014",
        name="ExternalServiceError",
        pattern=r"ExternalServiceException|ThirdParty.*Error|upstream.*failed|service unavailable",
        severity=AlertSeverity.HIGH,
        description="外部服务错误",
        suggestion="检查外部服务状态、配置重试机制、实现熔断策略",
        category=ErrorCategory.EXTERNAL_SERVICE,
        keywords=["external", "third party", "upstream", "service"]
    ),
    ErrorPattern(
        pattern_id="EP015",
        name="ConfigurationError",
        pattern=r"ConfigurationError|ConfigException|invalid.*config|missing.*setting",
        severity=AlertSeverity.HIGH,
        description="配置错误",
        suggestion="检查配置文件、环境变量、配置项完整性",
        category=ErrorCategory.CONFIGURATION,
        keywords=["config", "setting", "environment", "property"]
    ),
    ErrorPattern(
        pattern_id="EP016",
        name="DeadlockError",
        pattern=r"deadlock|DeadlockError|lock.*deadlock|DeadlockFoundException",
        severity=AlertSeverity.HIGH,
        description="数据库死锁错误",
        suggestion="优化事务设计、减少锁持有时间、检查并发访问模式",
        category=ErrorCategory.DATABASE,
        keywords=["deadlock", "lock", "transaction", "concurrent"]
    ),
    ErrorPattern(
        pattern_id="EP017",
        name="ConnectionReset",
        pattern=r"ConnectionResetError|connection reset by peer|ECONNRESET|broken pipe",
        severity=AlertSeverity.HIGH,
        description="连接重置错误",
        suggestion="检查网络稳定性、实现重连机制、检查服务端状态",
        category=ErrorCategory.NETWORK,
        keywords=["connection", "reset", "pipe", "peer"]
    ),
    ErrorPattern(
        pattern_id="EP018",
        name="SSLHandshakeError",
        pattern=r"SSLHandshakeException|certificate.*verify.*failed|SSL.*error|CERTIFICATE_VERIFY_FAILED",
        severity=AlertSeverity.HIGH,
        description="SSL握手错误",
        suggestion="检查证书有效性、证书链配置、TLS版本兼容性",
        category=ErrorCategory.SECURITY,
        keywords=["ssl", "tls", "certificate", "handshake"]
    ),
    ErrorPattern(
        pattern_id="EP019",
        name="RateLimitExceeded",
        pattern=r"rate limit.*exceeded|RateLimitExceeded|429|TooManyRequestsException",
        severity=AlertSeverity.MEDIUM,
        description="请求频率限制",
        suggestion="实现请求限流、添加退避重试策略、检查API配额",
        category=ErrorCategory.EXTERNAL_SERVICE,
        keywords=["rate", "limit", "throttle", "quota"]
    ),
    ErrorPattern(
        pattern_id="EP020",
        name="DiskIOError",
        pattern=r"IOError|InputOutputError|disk.*I/O.*error|EIO|read.*failed|write.*failed",
        severity=AlertSeverity.HIGH,
        description="磁盘IO错误",
        suggestion="检查磁盘健康状态、文件系统完整性、存储设备连接",
        category=ErrorCategory.FILE_SYSTEM,
        keywords=["disk", "io", "read", "write", "storage"]
    ),
    ErrorPattern(
        pattern_id="EP021",
        name="ThreadDeadlock",
        pattern=r"thread.*deadlock|ThreadDeadlockError|potential deadlock|lock.*timeout",
        severity=AlertSeverity.CRITICAL,
        description="线程死锁",
        suggestion="检查线程同步逻辑、优化锁使用、避免嵌套锁",
        category=ErrorCategory.RUNTIME,
        keywords=["thread", "deadlock", "lock", "synchronization"]
    ),
    ErrorPattern(
        pattern_id="EP022",
        name="DataCorruption",
        pattern=r"data.*corruption|corrupted.*data|checksum.*mismatch|DataIntegrityError",
        severity=AlertSeverity.CRITICAL,
        description="数据损坏错误",
        suggestion="检查存储介质、验证数据备份、执行数据恢复",
        category=ErrorCategory.DATABASE,
        keywords=["corruption", "integrity", "checksum", "data"]
    ),
    ErrorPattern(
        pattern_id="EP023",
        name="ServiceDiscoveryError",
        pattern=r"service.*not.*found|discovery.*failed|Eureka.*error|Consul.*error|NoServiceAvailable",
        severity=AlertSeverity.HIGH,
        description="服务发现错误",
        suggestion="检查服务注册中心、验证服务实例状态、检查网络配置",
        category=ErrorCategory.EXTERNAL_SERVICE,
        keywords=["service", "discovery", "registry", "eureka", "consul"]
    ),
    ErrorPattern(
        pattern_id="EP024",
        name="MessageQueueError",
        pattern=r"QueueFullException|MessageQueue.*error|MQ.*error|RabbitMQ.*error|Kafka.*error",
        severity=AlertSeverity.HIGH,
        description="消息队列错误",
        suggestion="检查队列容量、消费者状态、消息积压情况",
        category=ErrorCategory.EXTERNAL_SERVICE,
        keywords=["queue", "message", "mq", "rabbitmq", "kafka"]
    ),
    ErrorPattern(
        pattern_id="EP025",
        name="CacheError",
        pattern=r"Redis.*error|CacheException|Memcached.*error|cache.*connection.*failed",
        severity=AlertSeverity.MEDIUM,
        description="缓存服务错误",
        suggestion="检查缓存服务状态、连接配置、内存使用情况",
        category=ErrorCategory.EXTERNAL_SERVICE,
        keywords=["cache", "redis", "memcached", "connection"]
    ),
    ErrorPattern(
        pattern_id="EP026",
        name="IndexError",
        pattern=r"IndexError|IndexOutOfBoundsException|list index out of range|array.*index",
        severity=AlertSeverity.HIGH,
        description="索引越界错误",
        suggestion="检查数组/列表边界条件、添加索引范围验证",
        category=ErrorCategory.RUNTIME,
        keywords=["index", "array", "list", "bounds", "range"]
    ),
    ErrorPattern(
        pattern_id="EP027",
        name="KeyError",
        pattern=r"KeyError|KeyNotFoundException|dictionary.*key|NoSuchElementException",
        severity=AlertSeverity.MEDIUM,
        description="键不存在错误",
        suggestion="检查字典/映射键是否存在、使用get()方法安全访问",
        category=ErrorCategory.RUNTIME,
        keywords=["key", "dictionary", "map", "not found"]
    ),
    ErrorPattern(
        pattern_id="EP028",
        name="TypeError",
        pattern=r"TypeError|ClassCastException|type.*mismatch|unsupported operand",
        severity=AlertSeverity.HIGH,
        description="类型错误",
        suggestion="检查变量类型、添加类型转换、验证输入数据类型",
        category=ErrorCategory.RUNTIME,
        keywords=["type", "cast", "mismatch", "operand"]
    ),
    ErrorPattern(
        pattern_id="EP029",
        name="ValueError",
        pattern=r"ValueError|IllegalArgumentException|invalid.*argument|invalid.*parameter",
        severity=AlertSeverity.MEDIUM,
        description="值错误",
        suggestion="检查参数值范围、添加参数验证、检查业务逻辑约束",
        category=ErrorCategory.LOGIC,
        keywords=["value", "argument", "parameter", "invalid"]
    ),
    ErrorPattern(
        pattern_id="EP030",
        name="ConcurrentModificationError",
        pattern=r"ConcurrentModificationException|concurrent.*modification|race.*condition",
        severity=AlertSeverity.HIGH,
        description="并发修改错误",
        suggestion="使用线程安全集合、添加同步机制、检查并发访问模式",
        category=ErrorCategory.RUNTIME,
        keywords=["concurrent", "modification", "race", "thread"]
    ),
]

CATEGORY_KEYWORDS: Dict[ErrorCategory, List[str]] = {
    ErrorCategory.NETWORK: ["network", "socket", "connection", "timeout", "http", "tcp", "udp", "dns", "ssl", "tls", "proxy"],
    ErrorCategory.DATABASE: ["database", "sql", "query", "table", "column", "index", "transaction", "deadlock", "constraint", "orm"],
    ErrorCategory.MEMORY: ["memory", "heap", "allocation", "oom", "gc", "garbage", "leak", "buffer"],
    ErrorCategory.FILE_SYSTEM: ["file", "directory", "path", "disk", "read", "write", "permission", "io"],
    ErrorCategory.PERMISSION: ["permission", "access", "denied", "unauthorized", "forbidden", "privilege", "role"],
    ErrorCategory.CONFIGURATION: ["config", "setting", "property", "environment", "initialization", "startup"],
    ErrorCategory.RUNTIME: ["runtime", "exception", "error", "crash", "null", "pointer", "index", "array"],
    ErrorCategory.LOGIC: ["logic", "validation", "invalid", "assert", "condition", "state", "business"],
    ErrorCategory.SECURITY: ["security", "auth", "token", "credential", "encryption", "ssl", "certificate", "injection"],
    ErrorCategory.PERFORMANCE: ["performance", "slow", "latency", "timeout", "throughput", "bottleneck", "optimize"],
    ErrorCategory.EXTERNAL_SERVICE: ["external", "third", "party", "api", "service", "upstream", "downstream", "integration"],
    ErrorCategory.RESOURCE: ["resource", "limit", "quota", "exhausted", "thread", "pool", "connection pool", "file descriptor"]
}


class LogParser:
    """日志解析器基类"""

    TEXT_LOG_PATTERNS = [
        re.compile(
            r'(?P<timestamp>\d{4}-\d{2}-\d{2}[T\s]\d{2}:\d{2}:\d{2}(?:\.\d+)?)\s*'
            r'\[?(?P<level>DEBUG|INFO|WARNING|WARN|ERROR|CRITICAL|FATAL)\]?\s*'
            r'(?:\[(?P<logger>[^\]]+)\])?\s*'
            r'(?:\[(?P<thread>[^\]]+)\])?\s*'
            r'(?P<message>.*)',
            re.IGNORECASE
        ),
        re.compile(
            r'(?P<level>DEBUG|INFO|WARNING|WARN|ERROR|CRITICAL|FATAL)\s*'
            r'(?P<timestamp>\d{4}-\d{2}-\d{2}[T\s]\d{2}:\d{2}:\d{2}(?:\.\d+)?)\s*'
            r'(?P<message>.*)',
            re.IGNORECASE
        ),
        re.compile(
            r'\[(?P<timestamp>\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2})\]\s*'
            r'\[(?P<level>\w+)\]\s*'
            r'(?P<message>.*)'
        )
    ]

    LEVEL_MAP = {
        'debug': LogLevel.DEBUG,
        'info': LogLevel.INFO,
        'warning': LogLevel.WARNING,
        'warn': LogLevel.WARNING,
        'error': LogLevel.ERROR,
        'critical': LogLevel.CRITICAL,
        'fatal': LogLevel.CRITICAL
    }

    def parse_file(self, file_path: Path, log_format: LogFormat = LogFormat.AUTO) -> List[LogEntry]:
        if log_format == LogFormat.AUTO:
            log_format = self._detect_format(file_path)

        with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
            content = f.read()

        if log_format == LogFormat.JSON:
            return self._parse_json(content, str(file_path))
        elif log_format == LogFormat.CSV:
            return self._parse_csv(content, str(file_path))
        else:
            return self._parse_text(content, str(file_path))

    def _detect_format(self, file_path: Path) -> LogFormat:
        suffix = file_path.suffix.lower()
        if suffix == '.json':
            return LogFormat.JSON
        elif suffix == '.csv':
            return LogFormat.CSV

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                first_line = f.readline().strip()
                if first_line.startswith('{') and first_line.endswith('}'):
                    return LogFormat.JSON
                if ',' in first_line and first_line.count(',') >= 2:
                    return LogFormat.CSV
        except Exception:
            pass

        return LogFormat.TEXT

    def _parse_json(self, content: str, file_path: str) -> List[LogEntry]:
        entries = []
        lines = content.strip().split('\n')

        for line_num, line in enumerate(lines, 1):
            line = line.strip()
            if not line:
                continue

            try:
                data = json.loads(line)
                entry = self._json_to_entry(data, file_path, line_num, line)
                entries.append(entry)
            except json.JSONDecodeError:
                entry = LogEntry(
                    message=line,
                    raw_line=line,
                    file_path=file_path,
                    line_number=line_num
                )
                entries.append(entry)

        return entries

    def _json_to_entry(self, data: Dict[str, Any], file_path: str, line_num: int, raw_line: str) -> LogEntry:
        timestamp = None
        if 'timestamp' in data:
            timestamp = self._parse_timestamp(data['timestamp'])
        elif 'time' in data:
            timestamp = self._parse_timestamp(data['time'])
        elif '@timestamp' in data:
            timestamp = self._parse_timestamp(data['@timestamp'])

        level_str = str(data.get('level', data.get('severity', 'unknown'))).lower()
        level = self.LEVEL_MAP.get(level_str, LogLevel.UNKNOWN)

        message = data.get('message', data.get('msg', data.get('log', '')))

        extra = {k: v for k, v in data.items()
                 if k not in ['timestamp', 'time', '@timestamp', 'level', 'severity', 'message', 'msg', 'log', 'logger', 'thread']}

        return LogEntry(
            timestamp=timestamp,
            level=level,
            message=str(message),
            source=data.get('source', data.get('app', '')),
            logger_name=data.get('logger', data.get('logger_name', '')),
            thread=data.get('thread', data.get('thread_name', '')),
            extra=extra,
            raw_line=raw_line,
            file_path=file_path,
            line_number=line_num
        )

    def _parse_csv(self, content: str, file_path: str) -> List[LogEntry]:
        entries = []
        lines = content.strip().split('\n')

        if not lines:
            return entries

        reader = csv.DictReader(lines)
        for line_num, row in enumerate(reader, 2):
            entry = self._csv_row_to_entry(row, file_path, line_num)
            entries.append(entry)

        return entries

    def _csv_row_to_entry(self, row: Dict[str, str], file_path: str, line_num: int) -> LogEntry:
        timestamp = None
        for key in ['timestamp', 'time', 'datetime', 'date']:
            if key in row:
                timestamp = self._parse_timestamp(row[key])
                break

        level_str = row.get('level', row.get('severity', 'unknown')).lower()
        level = self.LEVEL_MAP.get(level_str, LogLevel.UNKNOWN)

        message = row.get('message', row.get('msg', row.get('log', '')))

        return LogEntry(
            timestamp=timestamp,
            level=level,
            message=message,
            source=row.get('source', ''),
            logger_name=row.get('logger', ''),
            thread=row.get('thread', ''),
            raw_line=str(row),
            file_path=file_path,
            line_number=line_num
        )

    def _parse_text(self, content: str, file_path: str) -> List[LogEntry]:
        entries = []
        lines = content.split('\n')

        for line_num, line in enumerate(lines, 1):
            line = line.rstrip()
            if not line:
                continue

            entry = self._parse_text_line(line, file_path, line_num)
            entries.append(entry)

        return entries

    def _parse_text_line(self, line: str, file_path: str, line_num: int) -> LogEntry:
        for pattern in self.TEXT_LOG_PATTERNS:
            match = pattern.match(line)
            if match:
                groups = match.groupdict()

                timestamp = self._parse_timestamp(groups.get('timestamp', ''))

                level_str = groups.get('level', 'unknown').lower()
                level = self.LEVEL_MAP.get(level_str, LogLevel.UNKNOWN)

                return LogEntry(
                    timestamp=timestamp,
                    level=level,
                    message=groups.get('message', '').strip(),
                    logger_name=groups.get('logger', ''),
                    thread=groups.get('thread', ''),
                    raw_line=line,
                    file_path=file_path,
                    line_number=line_num
                )

        return LogEntry(
            message=line,
            raw_line=line,
            file_path=file_path,
            line_number=line_num
        )

    def _parse_timestamp(self, ts_str: str) -> Optional[datetime]:
        if not ts_str:
            return None

        formats = [
            '%Y-%m-%dT%H:%M:%S.%f',
            '%Y-%m-%dT%H:%M:%S',
            '%Y-%m-%d %H:%M:%S.%f',
            '%Y-%m-%d %H:%M:%S',
            '%Y/%m/%d %H:%M:%S',
            '%d/%b/%Y:%H:%M:%S',
        ]

        for fmt in formats:
            try:
                return datetime.strptime(ts_str.replace('Z', ''), fmt)
            except ValueError:
                continue

        return None


class IntelligentErrorPatternMatcher:
    """智能错误模式匹配器 - 支持学习和自适应"""

    CONTEXTUAL_PATTERNS = [
        (r'failed to .* after \d+ attempts?', 'retry_exhausted', AlertSeverity.HIGH, ErrorCategory.RUNTIME),
        (r'connection.*reset.*by.*peer', 'connection_reset', AlertSeverity.HIGH, ErrorCategory.NETWORK),
        (r'too many open files', 'file_descriptor_exhaustion', AlertSeverity.CRITICAL, ErrorCategory.RESOURCE),
        (r'certificate.*verify.*failed', 'ssl_verification_error', AlertSeverity.HIGH, ErrorCategory.SECURITY),
        (r'deadline.*exceeded', 'deadline_exceeded', AlertSeverity.HIGH, ErrorCategory.PERFORMANCE),
        (r'rate.*limit.*exceeded', 'rate_limited', AlertSeverity.MEDIUM, ErrorCategory.EXTERNAL_SERVICE),
        (r'service.*unavailable', 'service_unavailable', AlertSeverity.HIGH, ErrorCategory.EXTERNAL_SERVICE),
        (r'broken pipe', 'broken_pipe', AlertSeverity.MEDIUM, ErrorCategory.NETWORK),
        (r'no such host', 'dns_resolution_error', AlertSeverity.HIGH, ErrorCategory.NETWORK),
        (r'access.*denied.*for.*user', 'database_access_denied', AlertSeverity.HIGH, ErrorCategory.DATABASE),
        (r'duplicate.*key.*value', 'duplicate_key', AlertSeverity.MEDIUM, ErrorCategory.DATABASE),
        (r'lock.*wait.*timeout', 'lock_timeout', AlertSeverity.HIGH, ErrorCategory.DATABASE),
        (r'serialization.*error', 'serialization_error', AlertSeverity.MEDIUM, ErrorCategory.RUNTIME),
        (r'deserialization.*error', 'deserialization_error', AlertSeverity.MEDIUM, ErrorCategory.RUNTIME),
        (r'invalid.*json', 'json_parse_error', AlertSeverity.MEDIUM, ErrorCategory.LOGIC),
        (r'null.*pointer|nullptr', 'null_pointer', AlertSeverity.CRITICAL, ErrorCategory.RUNTIME),
        (r'array.*index.*out.*of.*bounds', 'array_index_out_of_bounds', AlertSeverity.HIGH, ErrorCategory.RUNTIME),
        (r'integer.*overflow', 'integer_overflow', AlertSeverity.HIGH, ErrorCategory.RUNTIME),
        (r'stack.*buffer.*overflow', 'buffer_overflow', AlertSeverity.CRITICAL, ErrorCategory.SECURITY),
        (r'heap.*buffer.*overflow', 'heap_overflow', AlertSeverity.CRITICAL, ErrorCategory.SECURITY),
        (r'connection.*pool.*exhausted', 'connection_pool_exhausted', AlertSeverity.HIGH, ErrorCategory.RESOURCE),
        (r'cannot acquire.*lock', 'lock_acquisition_failed', AlertSeverity.HIGH, ErrorCategory.RUNTIME),
        (r'circuit.*breaker.*open', 'circuit_breaker_open', AlertSeverity.HIGH, ErrorCategory.EXTERNAL_SERVICE),
        (r'fallback.*triggered', 'fallback_triggered', AlertSeverity.MEDIUM, ErrorCategory.EXTERNAL_SERVICE),
        (r'thread.*pool.*rejected', 'thread_pool_rejected', AlertSeverity.HIGH, ErrorCategory.RESOURCE),
        (r'queue.*capacity.*exceeded', 'queue_capacity_exceeded', AlertSeverity.HIGH, ErrorCategory.RESOURCE),
        (r'backpressure.*applied', 'backpressure_applied', AlertSeverity.MEDIUM, ErrorCategory.PERFORMANCE),
        (r'garbage.*collection.*overhead', 'gc_overhead', AlertSeverity.HIGH, ErrorCategory.MEMORY),
        (r'heap.*space.*exhausted', 'heap_space_exhausted', AlertSeverity.CRITICAL, ErrorCategory.MEMORY),
        (r'metaspace.*out.*of.*memory', 'metaspace_oom', AlertSeverity.CRITICAL, ErrorCategory.MEMORY),
        (r'direct.*buffer.*memory.*exceeded', 'direct_buffer_oom', AlertSeverity.HIGH, ErrorCategory.MEMORY),
        (r'foreign.*key.*violation', 'foreign_key_violation', AlertSeverity.MEDIUM, ErrorCategory.DATABASE),
        (r'unique.*constraint.*violation', 'unique_constraint_violation', AlertSeverity.MEDIUM, ErrorCategory.DATABASE),
        (r'check.*constraint.*violation', 'check_constraint_violation', AlertSeverity.MEDIUM, ErrorCategory.DATABASE),
        (r'null.*constraint.*violation', 'null_constraint_violation', AlertSeverity.MEDIUM, ErrorCategory.DATABASE),
        (r'syntax.*error.*in.*sql', 'sql_syntax_error', AlertSeverity.HIGH, ErrorCategory.DATABASE),
        (r'invalid.*column.*name', 'invalid_column', AlertSeverity.HIGH, ErrorCategory.DATABASE),
        (r'table.*or.*view.*not.*found', 'table_not_found', AlertSeverity.HIGH, ErrorCategory.DATABASE),
        (r'socket.*hang.*up', 'socket_hang_up', AlertSeverity.MEDIUM, ErrorCategory.NETWORK),
        (r'connect.*ECONNREFUSED', 'connection_refused', AlertSeverity.HIGH, ErrorCategory.NETWORK),
        (r'connect.*ETIMEDOUT', 'connection_timeout', AlertSeverity.HIGH, ErrorCategory.NETWORK),
        (r'getaddrinfo.*ENOTFOUND', 'dns_not_found', AlertSeverity.HIGH, ErrorCategory.NETWORK),
        (r'network.*unreachable', 'network_unreachable', AlertSeverity.HIGH, ErrorCategory.NETWORK),
        (r'host.*unreachable', 'host_unreachable', AlertSeverity.HIGH, ErrorCategory.NETWORK),
        (r'protocol.*error', 'protocol_error', AlertSeverity.HIGH, ErrorCategory.NETWORK),
        (r'invalid.*message.*format', 'invalid_message_format', AlertSeverity.MEDIUM, ErrorCategory.LOGIC),
        (r'payload.*too.*large', 'payload_too_large', AlertSeverity.MEDIUM, ErrorCategory.LOGIC),
        (r'unsupported.*media.*type', 'unsupported_media_type', AlertSeverity.MEDIUM, ErrorCategory.LOGIC),
        (r'missing.*required.*field', 'missing_required_field', AlertSeverity.MEDIUM, ErrorCategory.LOGIC),
        (r'invalid.*enum.*value', 'invalid_enum_value', AlertSeverity.MEDIUM, ErrorCategory.LOGIC),
        (r'encoding.*error', 'encoding_error', AlertSeverity.MEDIUM, ErrorCategory.RUNTIME),
        (r'decoding.*error', 'decoding_error', AlertSeverity.MEDIUM, ErrorCategory.RUNTIME),
        (r'character.*encoding.*error', 'charset_error', AlertSeverity.MEDIUM, ErrorCategory.RUNTIME),
        (r'file.*locked', 'file_locked', AlertSeverity.MEDIUM, ErrorCategory.FILE_SYSTEM),
        (r'directory.*not.*empty', 'directory_not_empty', AlertSeverity.LOW, ErrorCategory.FILE_SYSTEM),
        (r'disk.*quota.*exceeded', 'disk_quota_exceeded', AlertSeverity.HIGH, ErrorCategory.FILE_SYSTEM),
        (r'read.*only.*file.*system', 'read_only_filesystem', AlertSeverity.HIGH, ErrorCategory.FILE_SYSTEM),
        (r'no.*space.*left.*on.*device', 'no_space_left', AlertSeverity.CRITICAL, ErrorCategory.FILE_SYSTEM),
        (r'token.*expired', 'token_expired', AlertSeverity.MEDIUM, ErrorCategory.SECURITY),
        (r'invalid.*token', 'invalid_token', AlertSeverity.HIGH, ErrorCategory.SECURITY),
        (r'session.*expired', 'session_expired', AlertSeverity.MEDIUM, ErrorCategory.SECURITY),
        (r'authentication.*failed', 'auth_failed', AlertSeverity.HIGH, ErrorCategory.SECURITY),
        (r'authorization.*failed', 'authorization_failed', AlertSeverity.HIGH, ErrorCategory.SECURITY),
        (r'insufficient.*privileges', 'insufficient_privileges', AlertSeverity.HIGH, ErrorCategory.SECURITY),
        (r'account.*locked', 'account_locked', AlertSeverity.HIGH, ErrorCategory.SECURITY),
        (r'account.*disabled', 'account_disabled', AlertSeverity.HIGH, ErrorCategory.SECURITY),
        (r'password.*expired', 'password_expired', AlertSeverity.MEDIUM, ErrorCategory.SECURITY),
        (r'captcha.*required', 'captcha_required', AlertSeverity.LOW, ErrorCategory.SECURITY),
        (r'suspicious.*activity', 'suspicious_activity', AlertSeverity.HIGH, ErrorCategory.SECURITY),
        (r'xss.*attempt', 'xss_attempt', AlertSeverity.CRITICAL, ErrorCategory.SECURITY),
        (r'sql.*injection.*attempt', 'sql_injection_attempt', AlertSeverity.CRITICAL, ErrorCategory.SECURITY),
        (r'csrf.*token.*mismatch', 'csrf_token_mismatch', AlertSeverity.HIGH, ErrorCategory.SECURITY),
    ]

    SEVERITY_ESCALATION_RULES = {
        'frequency_threshold': 5,
        'time_window_minutes': 10,
        'escalation_factor': 1.5,
    }

    def __init__(self, custom_patterns: Optional[List[ErrorPattern]] = None, learning_enabled: bool = True):
        self.patterns = DEFAULT_ERROR_PATTERNS.copy()
        if custom_patterns:
            self.patterns.extend(custom_patterns)
        self.learning_enabled = learning_enabled
        self.learned_patterns: Dict[str, ErrorPattern] = {}
        self.pattern_stats: Dict[str, Dict[str, Any]] = defaultdict(lambda: {
            'count': 0,
            'first_seen': None,
            'last_seen': None,
            'contexts': [],
            'severity_history': [],
            'correlated_patterns': []
        })
        self._compiled_contextual = [
            (re.compile(p, re.IGNORECASE), name, sev, cat) 
            for p, name, sev, cat in self.CONTEXTUAL_PATTERNS
        ]
        self._pattern_co_occurrence: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))
        self._temporal_frequency: Dict[str, List[datetime]] = defaultdict(list)

    def match(self, entry: LogEntry) -> List[Tuple[ErrorPattern, re.Match]]:
        matches = []
        for pattern in self.patterns:
            if pattern.compiled_pattern:
                match = pattern.compiled_pattern.search(entry.message)
                if match:
                    matches.append((pattern, match))
                    self._update_stats(pattern, entry)

        for pattern in self.learned_patterns.values():
            if pattern.compiled_pattern:
                match = pattern.compiled_pattern.search(entry.message)
                if match:
                    matches.append((pattern, match))
                    self._update_stats(pattern, entry)

        contextual_matches = self._match_contextual_patterns(entry)
        matches.extend(contextual_matches)

        self._update_co_occurrence(matches)
        self._update_temporal_frequency(matches, entry)

        return matches

    def _match_contextual_patterns(self, entry: LogEntry) -> List[Tuple[ErrorPattern, re.Match]]:
        matches = []
        for compiled, name, severity, category in self._compiled_contextual:
            match = compiled.search(entry.message)
            if match:
                pattern = ErrorPattern(
                    pattern_id=f"CTX-{name}",
                    name=name.replace('_', ' ').title(),
                    pattern=compiled.pattern,
                    severity=severity,
                    description=f"上下文感知模式: {name}",
                    suggestion=self._get_contextual_suggestion(name),
                    category=category,
                    keywords=[name]
                )
                matches.append((pattern, match))
                self._update_stats(pattern, entry)
        return matches

    def _get_contextual_suggestion(self, pattern_name: str) -> str:
        suggestions = {
            'retry_exhausted': '增加重试次数或优化重试间隔策略',
            'connection_reset': '检查网络稳定性，考虑实现连接池和重连机制',
            'file_descriptor_exhaustion': '增加系统文件描述符限制，检查资源泄漏',
            'ssl_verification_error': '检查SSL证书配置，验证证书链完整性',
            'deadline_exceeded': '优化处理逻辑，增加超时时间或实现异步处理',
            'rate_limited': '实现请求限流，添加退避重试策略',
            'service_unavailable': '实现熔断机制，添加服务降级策略',
            'broken_pipe': '检查连接状态，实现优雅的连接关闭',
            'dns_resolution_error': '检查DNS配置，考虑使用IP直连或DNS缓存',
            'database_access_denied': '检查数据库用户权限配置',
            'duplicate_key': '检查数据唯一性约束，实现幂等性处理',
            'lock_timeout': '优化事务设计，减少锁持有时间',
            'serialization_error': '检查数据格式，添加序列化验证',
            'deserialization_error': '验证输入数据格式，添加错误处理',
            'json_parse_error': '验证JSON格式，添加格式校验',
            'null_pointer': '添加空值检查，使用安全的访问方式',
            'array_index_out_of_bounds': '添加数组边界检查',
            'integer_overflow': '添加数值范围检查，使用大整数类型',
            'buffer_overflow': '检查缓冲区大小，使用安全的字符串操作',
            'heap_overflow': '检查内存分配，使用内存安全函数',
            'connection_pool_exhausted': '增加连接池大小，检查连接泄漏，优化连接复用',
            'lock_acquisition_failed': '检查锁竞争情况，优化锁粒度，减少锁持有时间',
            'circuit_breaker_open': '检查下游服务健康状态，调整熔断阈值，准备降级方案',
            'fallback_triggered': '检查主服务状态，优化降级逻辑，确保降级服务质量',
            'thread_pool_rejected': '增加线程池大小，优化任务处理时间，实现任务队列',
            'queue_capacity_exceeded': '增加队列容量，优化消费者处理速度，实现背压机制',
            'backpressure_applied': '优化生产者速率，增加处理能力，调整背压阈值',
            'gc_overhead': '优化内存使用，调整GC参数，检查内存泄漏',
            'heap_space_exhausted': '增加堆内存大小，优化对象创建，检查内存泄漏',
            'metaspace_oom': '增加元空间大小，检查类加载泄漏，优化反射使用',
            'direct_buffer_oom': '增加直接内存限制，优化NIO使用，检查缓冲区泄漏',
            'foreign_key_violation': '检查关联数据完整性，确保外键约束满足',
            'unique_constraint_violation': '检查数据唯一性，实现幂等性处理',
            'check_constraint_violation': '检查数据有效性，确保满足约束条件',
            'null_constraint_violation': '确保必填字段不为空，添加默认值处理',
            'sql_syntax_error': '检查SQL语句语法，验证字段名和表名',
            'invalid_column': '检查列名是否正确，验证表结构',
            'table_not_found': '检查表名是否正确，验证数据库结构',
            'socket_hang_up': '检查服务端状态，实现重连机制',
            'connection_refused': '检查目标服务是否运行，验证端口配置',
            'connection_timeout': '检查网络连通性，增加连接超时时间',
            'dns_not_found': '检查域名配置，验证DNS解析',
            'network_unreachable': '检查网络配置，验证路由设置',
            'host_unreachable': '检查目标主机状态，验证网络连接',
            'protocol_error': '检查协议版本兼容性，验证消息格式',
            'invalid_message_format': '检查消息格式规范，添加格式验证',
            'payload_too_large': '减小请求体大小，实现分片上传',
            'unsupported_media_type': '检查Content-Type设置，支持正确的媒体类型',
            'missing_required_field': '检查必填字段，添加字段验证',
            'invalid_enum_value': '检查枚举值范围，添加值验证',
            'encoding_error': '检查字符编码设置，使用正确的编码方式',
            'decoding_error': '验证输入编码，添加编码检测',
            'charset_error': '统一字符编码设置，添加编码转换',
            'file_locked': '检查文件锁定状态，优化文件访问策略',
            'directory_not_empty': '检查目录内容，使用递归删除',
            'disk_quota_exceeded': '清理磁盘空间，增加配额限制',
            'read_only_filesystem': '检查文件系统挂载模式，修复写入权限',
            'no_space_left': '清理磁盘空间，扩展存储容量',
            'token_expired': '实现令牌刷新机制，延长令牌有效期',
            'invalid_token': '检查令牌格式，验证签名',
            'session_expired': '延长会话超时时间，实现会话刷新',
            'auth_failed': '检查认证凭据，验证认证流程',
            'authorization_failed': '检查用户权限，验证授权配置',
            'insufficient_privileges': '检查用户角色权限，申请必要权限',
            'account_locked': '联系管理员解锁账户，检查锁定原因',
            'account_disabled': '联系管理员启用账户，检查禁用原因',
            'password_expired': '更新密码，延长密码有效期',
            'captcha_required': '完成验证码验证，优化验证码触发条件',
            'suspicious_activity': '检查账户安全，审计异常行为',
            'xss_attempt': '加强输入过滤，实现输出编码',
            'sql_injection_attempt': '使用参数化查询，加强输入验证',
            'csrf_token_mismatch': '检查CSRF令牌生成，确保令牌同步',
        }
        return suggestions.get(pattern_name, '分析错误详情并制定解决方案')

    def _update_stats(self, pattern: ErrorPattern, entry: LogEntry) -> None:
        stats = self.pattern_stats[pattern.pattern_id]
        stats['count'] += 1
        if stats['first_seen'] is None:
            stats['first_seen'] = entry.timestamp
        stats['last_seen'] = entry.timestamp
        if len(stats['contexts']) < 10:
            stats['contexts'].append({
                'message': entry.message[:200],
                'timestamp': entry.timestamp.isoformat() if entry.timestamp else None,
                'file': entry.file_path,
                'line': entry.line_number
            })
        stats['severity_history'].append({
            'timestamp': entry.timestamp.isoformat() if entry.timestamp else None,
            'level': entry.level.value
        })

    def _update_co_occurrence(self, matches: List[Tuple[ErrorPattern, re.Match]]) -> None:
        if len(matches) >= 2:
            pattern_ids = [p.pattern_id for p, _ in matches]
            for i, pid1 in enumerate(pattern_ids):
                for pid2 in pattern_ids[i+1:]:
                    self._pattern_co_occurrence[pid1][pid2] += 1
                    self._pattern_co_occurrence[pid2][pid1] += 1

    def _update_temporal_frequency(self, matches: List[Tuple[ErrorPattern, re.Match]], entry: LogEntry) -> None:
        if entry.timestamp:
            for pattern, _ in matches:
                self._temporal_frequency[pattern.pattern_id].append(entry.timestamp)

    def get_escalated_severity(self, pattern: ErrorPattern) -> AlertSeverity:
        stats = self.pattern_stats.get(pattern.pattern_id, {})
        frequency = stats.get('count', 0)
        severity_history = stats.get('severity_history', [])
        
        recent_errors = sum(
            1 for h in severity_history[-20:]
            if h.get('level') in ['error', 'critical']
        )
        
        if frequency >= self.SEVERITY_ESCALATION_RULES['frequency_threshold']:
            if recent_errors >= frequency * 0.8:
                severity_order = [AlertSeverity.LOW, AlertSeverity.MEDIUM, AlertSeverity.HIGH, AlertSeverity.CRITICAL]
                current_idx = severity_order.index(pattern.severity) if pattern.severity in severity_order else 0
                escalated_idx = min(current_idx + 1, len(severity_order) - 1)
                return severity_order[escalated_idx]
        
        return pattern.severity

    def get_correlated_patterns(self, pattern_id: str) -> List[Tuple[str, int]]:
        co_occur = self._pattern_co_occurrence.get(pattern_id, {})
        return sorted(co_occur.items(), key=lambda x: x[1], reverse=True)[:5]

    def analyze_pattern_frequency(self, pattern_id: str) -> Dict[str, Any]:
        timestamps = self._temporal_frequency.get(pattern_id, [])
        if not timestamps:
            return {'frequency': 0, 'trend': 'unknown'}
        
        hourly_counts: Dict[str, int] = defaultdict(int)
        for ts in timestamps:
            hour_key = ts.strftime('%Y-%m-%d %H')
            hourly_counts[hour_key] += 1
        
        counts = list(hourly_counts.values())
        if len(counts) >= 2:
            recent = sum(counts[-3:]) / min(3, len(counts))
            earlier = sum(counts[:-3]) / max(1, len(counts) - 3) if len(counts) > 3 else recent
            
            if recent > earlier * 1.5:
                trend = 'increasing'
            elif recent < earlier * 0.7:
                trend = 'decreasing'
            else:
                trend = 'stable'
        else:
            trend = 'insufficient_data'
        
        return {
            'frequency': len(timestamps),
            'hourly_distribution': dict(hourly_counts),
            'trend': trend,
            'first_seen': min(timestamps).isoformat() if timestamps else None,
            'last_seen': max(timestamps).isoformat() if timestamps else None,
        }

    def learn_pattern(self, entries: List[LogEntry]) -> int:
        if not self.learning_enabled:
            return 0

        new_patterns = 0
        error_entries = [e for e in entries if e.level in [LogLevel.ERROR, LogLevel.CRITICAL]]

        message_signatures: Dict[str, List[LogEntry]] = defaultdict(list)
        for entry in error_entries:
            signature = self._extract_signature(entry.message)
            message_signatures[signature].append(entry)

        for signature, sig_entries in message_signatures.items():
            if len(sig_entries) >= 3 and signature not in self.learned_patterns:
                pattern = self._create_learned_pattern(signature, sig_entries)
                if pattern:
                    self.learned_patterns[signature] = pattern
                    new_patterns += 1

        cluster_patterns = self._learn_cluster_patterns(error_entries)
        for cluster_sig, cluster_pattern in cluster_patterns.items():
            if cluster_sig not in self.learned_patterns:
                self.learned_patterns[cluster_sig] = cluster_pattern
                new_patterns += 1

        return new_patterns

    def _learn_cluster_patterns(self, error_entries: List[LogEntry]) -> Dict[str, ErrorPattern]:
        cluster_patterns = {}
        
        semantic_groups: Dict[str, List[LogEntry]] = defaultdict(list)
        for entry in error_entries:
            semantic_key = self._extract_semantic_key(entry.message)
            semantic_groups[semantic_key].append(entry)
        
        for semantic_key, group_entries in semantic_groups.items():
            if len(group_entries) >= 5:
                pattern = self._create_semantic_pattern(semantic_key, group_entries)
                if pattern:
                    cluster_patterns[semantic_key] = pattern
        
        return cluster_patterns

    def _extract_semantic_key(self, message: str) -> str:
        key = message.lower()
        key = re.sub(r'\d+', '#NUM#', key)
        key = re.sub(r'0x[a-fA-F0-9]+', '#HEX#', key)
        key = re.sub(r'[a-fA-F0-9]{8}-[a-fA-F0-9]{4}-[a-fA-F0-9]{4}-[a-fA-F0-9]{4}-[a-fA-F0-9]{12}', '#UUID#', key)
        key = re.sub(r'/[\w/\.]+', '#PATH#', key)
        key = re.sub(r'https?://[^\s]+', '#URL#', key)
        key = re.sub(r'[\w\.-]+@[\w\.-]+', '#EMAIL#', key)
        key = re.sub(r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b', '#IP#', key)
        key = re.sub(r'\s+', ' ', key).strip()
        return key[:150]

    def _create_semantic_pattern(self, semantic_key: str, entries: List[LogEntry]) -> Optional[ErrorPattern]:
        pattern_regex = re.escape(semantic_key)
        pattern_regex = pattern_regex.replace(r'\#NUM\#', r'\d+')
        pattern_regex = pattern_regex.replace(r'\#HEX\#', r'0x[a-fA-F0-9]+')
        pattern_regex = pattern_regex.replace(r'\#UUID\#', r'[a-fA-F0-9]{8}-[a-fA-F0-9]{4}-[a-fA-F0-9]{4}-[a-fA-F0-9]{4}-[a-fA-F0-9]{12}')
        pattern_regex = pattern_regex.replace(r'\#PATH\#', r'/[\w/\.]+')
        pattern_regex = pattern_regex.replace(r'\#URL\#', r'https?://[^\s]+')
        pattern_regex = pattern_regex.replace(r'\#EMAIL\#', r'[\w\.-]+@[\w\.-]+')
        pattern_regex = pattern_regex.replace(r'\#IP\#', r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}')

        try:
            re.compile(pattern_regex, re.IGNORECASE)
        except re.error:
            return None

        severity = AlertSeverity.MEDIUM
        if any(e.level == LogLevel.CRITICAL for e in entries):
            severity = AlertSeverity.HIGH

        return ErrorPattern(
            pattern_id=f"SEMANTIC-{hashlib.md5(semantic_key.encode()).hexdigest()[:8]}",
            name=f"Semantic Pattern: {semantic_key[:40]}...",
            pattern=pattern_regex,
            severity=severity,
            description=f"语义聚类模式，出现 {len(entries)} 次",
            suggestion="分析此语义模式的根本原因",
            category=self._infer_category_from_message(semantic_key),
            keywords=semantic_key.split()[:5]
        )

    def _infer_category_from_message(self, message: str) -> ErrorCategory:
        message_lower = message.lower()
        category_scores: Dict[ErrorCategory, int] = defaultdict(int)
        
        for category, keywords in CATEGORY_KEYWORDS.items():
            for keyword in keywords:
                if keyword in message_lower:
                    category_scores[category] += 1
        
        if category_scores:
            return max(category_scores.keys(), key=lambda k: category_scores[k])
        return ErrorCategory.UNKNOWN

    def _extract_signature(self, message: str) -> str:
        sig = re.sub(r'\d+', 'N', message)
        sig = re.sub(r'0x[a-fA-F0-9]+', 'HEX', sig)
        sig = re.sub(r'[a-fA-F0-9]{8}-[a-fA-F0-9]{4}-[a-fA-F0-9]{4}-[a-fA-F0-9]{4}-[a-fA-F0-9]{12}', 'UUID', sig)
        sig = re.sub(r'/[\w/]+', '/PATH', sig)
        sig = re.sub(r'\s+', ' ', sig).strip()
        return sig[:100]

    def _create_learned_pattern(self, signature: str, entries: List[LogEntry]) -> Optional[ErrorPattern]:
        pattern_regex = re.escape(signature)
        pattern_regex = pattern_regex.replace(r'N', r'\d+')
        pattern_regex = pattern_regex.replace(r'HEX', r'0x[a-fA-F0-9]+')
        pattern_regex = pattern_regex.replace(r'UUID', r'[a-fA-F0-9]{8}-[a-fA-F0-9]{4}-[a-fA-F0-9]{4}-[a-fA-F0-9]{4}-[a-fA-F0-9]{12}')
        pattern_regex = pattern_regex.replace(r'/PATH', r'/[\w/]+')

        try:
            re.compile(pattern_regex, re.IGNORECASE)
        except re.error:
            return None

        return ErrorPattern(
            pattern_id=f"LEARNED-{hashlib.md5(signature.encode()).hexdigest()[:8]}",
            name=f"Learned Pattern: {signature[:30]}...",
            pattern=pattern_regex,
            severity=AlertSeverity.MEDIUM,
            description=f"自动学习的错误模式，出现 {len(entries)} 次",
            suggestion="分析此模式的具体原因并制定解决方案",
            category=ErrorCategory.UNKNOWN,
            keywords=signature.split()[:5]
        )

    def get_pattern_statistics(self) -> Dict[str, Any]:
        return {
            "total_patterns": len(self.patterns) + len(self.learned_patterns),
            "default_patterns": len(self.patterns),
            "learned_patterns": len(self.learned_patterns),
            "pattern_stats": dict(self.pattern_stats),
            "co_occurrence_analysis": {
                pid: dict(co_occur) 
                for pid, co_occur in self._pattern_co_occurrence.items()
            },
            "frequency_analysis": {
                pid: self.analyze_pattern_frequency(pid)
                for pid in self.pattern_stats.keys()
            }
        }

    def predict_next_occurrence(self, pattern_id: str) -> Optional[Dict[str, Any]]:
        timestamps = self._temporal_frequency.get(pattern_id, [])
        if len(timestamps) < 3:
            return None
        
        sorted_ts = sorted(timestamps)
        intervals = []
        for i in range(1, len(sorted_ts)):
            interval = (sorted_ts[i] - sorted_ts[i-1]).total_seconds()
            intervals.append(interval)
        
        if not intervals:
            return None
        
        avg_interval = sum(intervals) / len(intervals)
        last_occurrence = sorted_ts[-1]
        predicted_next = last_occurrence + timedelta(seconds=avg_interval)
        
        return {
            'pattern_id': pattern_id,
            'last_occurrence': last_occurrence.isoformat(),
            'predicted_next': predicted_next.isoformat(),
            'average_interval_seconds': avg_interval,
            'confidence': 'high' if len(timestamps) >= 10 else 'medium' if len(timestamps) >= 5 else 'low'
        }

    def detect_anomalous_patterns(self, entries: List[LogEntry]) -> List[Dict[str, Any]]:
        anomalies = []
        
        recent_window = timedelta(minutes=30)
        now = datetime.now()
        
        for pattern_id, timestamps in self._temporal_frequency.items():
            recent_count = sum(1 for ts in timestamps if (now - ts) <= recent_window)
            
            if len(timestamps) >= 10:
                historical_rate = len(timestamps) / max(1, (max(timestamps) - min(timestamps)).total_seconds() / 3600)
                recent_rate = recent_count / 0.5
                
                if recent_rate > historical_rate * 3:
                    anomalies.append({
                        'pattern_id': pattern_id,
                        'type': 'frequency_spike',
                        'recent_count': recent_count,
                        'historical_rate': historical_rate,
                        'recent_rate': recent_rate,
                        'deviation_factor': recent_rate / max(0.001, historical_rate),
                        'severity': 'high' if recent_rate > historical_rate * 5 else 'medium',
                    })
        
        return anomalies

    def extract_error_context(self, entry: LogEntry, all_entries: List[LogEntry], context_window: int = 5) -> Dict[str, Any]:
        context = {
            'before': [],
            'after': [],
            'related_errors': [],
        }
        
        try:
            idx = all_entries.index(entry)
        except ValueError:
            return context
        
        for i in range(max(0, idx - context_window), idx):
            context['before'].append(all_entries[i].to_dict())
        
        for i in range(idx + 1, min(len(all_entries), idx + context_window + 1)):
            context['after'].append(all_entries[i].to_dict())
        
        for e in all_entries:
            if e.event_id != entry.event_id and e.level in [LogLevel.ERROR, LogLevel.CRITICAL]:
                if e.timestamp and entry.timestamp:
                    time_diff = abs((e.timestamp - entry.timestamp).total_seconds())
                    if time_diff < 60:
                        context['related_errors'].append(e.to_dict())
        
        return context

    def generate_pattern_signature(self, message: str) -> str:
        signature = message.lower()
        signature = re.sub(r'\d+\.?\d*', '#NUM#', signature)
        signature = re.sub(r'0x[a-fA-F0-9]+', '#HEX#', signature)
        signature = re.sub(r'[a-fA-F0-9]{8}-[a-fA-F0-9]{4}-[a-fA-F0-9]{4}-[a-fA-F0-9]{4}-[a-fA-F0-9]{12}', '#UUID#', signature)
        signature = re.sub(r'/[\w/\.]+', '#PATH#', signature)
        signature = re.sub(r'https?://[^\s]+', '#URL#', signature)
        signature = re.sub(r'[\w\.-]+@[\w\.-]+', '#EMAIL#', signature)
        signature = re.sub(r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b', '#IP#', signature)
        signature = re.sub(r'"[^"]*"', '#STRING#', signature)
        signature = re.sub(r"'[^']*'", '#STRING#', signature)
        signature = re.sub(r'\s+', ' ', signature).strip()
        return signature[:200]

    def calculate_pattern_similarity(self, pattern1: str, pattern2: str) -> float:
        sig1 = self.generate_pattern_signature(pattern1)
        sig2 = self.generate_pattern_signature(pattern2)
        
        if sig1 == sig2:
            return 1.0
        
        words1 = set(sig1.split())
        words2 = set(sig2.split())
        
        if not words1 or not words2:
            return 0.0
        
        intersection = len(words1 & words2)
        union = len(words1 | words2)
        
        return intersection / union if union > 0 else 0.0

    def cluster_similar_patterns(self, threshold: float = 0.7) -> Dict[str, List[str]]:
        clusters: Dict[str, List[str]] = {}
        pattern_messages: Dict[str, str] = {}
        
        for pattern_id, stats in self.pattern_stats.items():
            if stats.get('contexts'):
                pattern_messages[pattern_id] = stats['contexts'][0].get('message', '')
        
        assigned = set()
        
        for pid1, msg1 in pattern_messages.items():
            if pid1 in assigned:
                continue
            
            cluster_key = pid1
            clusters[cluster_key] = [pid1]
            assigned.add(pid1)
            
            for pid2, msg2 in pattern_messages.items():
                if pid2 in assigned:
                    continue
                
                similarity = self.calculate_pattern_similarity(msg1, msg2)
                if similarity >= threshold:
                    clusters[cluster_key].append(pid2)
                    assigned.add(pid2)
        
        return clusters


class ErrorClassifier:
    """错误类型自动分类器 - 增强版
    
    支持多种分类策略：
    1. 模式匹配分类 - 基于预定义的错误模式
    2. 层级分类 - 基于错误类型层级结构
    3. 关键词分类 - 基于关键词权重评分
    4. 特征分类 - 基于消息特征提取
    5. 上下文分类 - 基于日志上下文信息
    6. 组合分类 - 综合多种分类策略
    """

    HIERARCHICAL_CATEGORIES = {
        ErrorCategory.NETWORK: {
            'connection': ['connection_refused', 'connection_timeout', 'connection_reset', 'connection_pool_exhausted', 'connection_aborted'],
            'dns': ['dns_resolution_failed', 'dns_timeout', 'unknown_host', 'dns_server_error'],
            'ssl': ['ssl_handshake_failed', 'certificate_invalid', 'certificate_expired', 'ssl_protocol_error'],
            'http': ['http_4xx_error', 'http_5xx_error', 'http_timeout', 'http_redirect_error'],
            'protocol': ['protocol_error', 'invalid_response', 'malformed_packet', 'protocol_version_mismatch'],
            'socket': ['socket_error', 'socket_timeout', 'socket_closed', 'socket_hang_up'],
            'proxy': ['proxy_error', 'proxy_connection_failed', 'proxy_timeout', 'proxy_auth_failed'],
        },
        ErrorCategory.DATABASE: {
            'connection': ['db_connection_failed', 'db_connection_timeout', 'db_pool_exhausted', 'db_connection_lost'],
            'query': ['query_timeout', 'syntax_error', 'invalid_column', 'table_not_found', 'query_too_complex'],
            'transaction': ['deadlock', 'lock_timeout', 'serialization_failure', 'constraint_violation', 'transaction_rollback'],
            'data': ['data_truncation', 'invalid_data_type', 'duplicate_key', 'data_integrity_error', 'data_corruption'],
            'replication': ['replication_lag', 'replication_error', 'master_slave_switch', 'sync_failed'],
            'index': ['index_corruption', 'index_not_used', 'index_creation_failed'],
        },
        ErrorCategory.MEMORY: {
            'allocation': ['allocation_failed', 'out_of_memory', 'heap_exhausted', 'native_memory_error'],
            'leak': ['memory_leak_detected', 'unbounded_growth', 'memory_fragmentation'],
            'gc': ['gc_overhead_exceeded', 'gc_pause_too_long', 'frequent_gc', 'gc_threshold_exceeded'],
            'buffer': ['buffer_overflow', 'buffer_underflow', 'buffer_exhausted'],
        },
        ErrorCategory.RUNTIME: {
            'null': ['null_pointer', 'none_type_error', 'attribute_error', 'undefined_variable'],
            'type': ['type_mismatch', 'invalid_cast', 'type_conversion_failed', 'incompatible_types'],
            'index': ['index_out_of_bounds', 'key_not_found', 'slice_error', 'array_index_exception'],
            'recursion': ['stack_overflow', 'recursion_depth_exceeded', 'infinite_loop'],
            'concurrent': ['race_condition', 'concurrent_modification', 'thread_interference'],
            'class_loading': ['class_not_found', 'class_cast_exception', 'no_such_method'],
        },
        ErrorCategory.SECURITY: {
            'authentication': ['auth_failed', 'invalid_token', 'session_expired', 'credential_error', 'mfa_failed'],
            'authorization': ['access_denied', 'permission_denied', 'insufficient_privileges', 'forbidden'],
            'injection': ['sql_injection_detected', 'xss_detected', 'command_injection', 'ldap_injection'],
            'encryption': ['decryption_failed', 'invalid_key', 'encryption_error', 'signature_verification_failed'],
            'audit': ['audit_log_failed', 'compliance_violation', 'security_policy_violation'],
            'certificate': ['certificate_revoked', 'certificate_chain_error', 'certificate_expired'],
        },
        ErrorCategory.FILE_SYSTEM: {
            'access': ['file_not_found', 'permission_denied', 'access_denied', 'file_locked'],
            'io': ['io_error', 'read_error', 'write_error', 'disk_io_error'],
            'space': ['disk_full', 'quota_exceeded', 'no_space_left', 'inode_exhausted'],
            'corruption': ['file_corruption', 'filesystem_error', 'bad_blocks'],
        },
        ErrorCategory.PERFORMANCE: {
            'latency': ['high_latency', 'slow_response', 'timeout_warning'],
            'throughput': ['low_throughput', 'bottleneck_detected', 'queue_overflow'],
            'resource': ['cpu_high', 'memory_high', 'io_wait_high'],
        },
        ErrorCategory.EXTERNAL_SERVICE: {
            'availability': ['service_unavailable', 'service_timeout', 'service_degraded'],
            'integration': ['api_error', 'integration_failed', 'webhook_failed'],
            'rate_limit': ['rate_limit_exceeded', 'throttle_applied', 'quota_exceeded'],
            'circuit_breaker': ['circuit_open', 'fallback_active', 'service_circuit_open'],
        },
        ErrorCategory.RESOURCE: {
            'pool': ['pool_exhausted', 'pool_timeout', 'pool_leak'],
            'thread': ['thread_pool_full', 'thread_deadlock', 'thread_starvation'],
            'connection': ['connection_limit_reached', 'connection_leak', 'connection_timeout'],
            'file_handle': ['too_many_open_files', 'file_handle_leak', 'handle_exhausted'],
        },
        ErrorCategory.CONFIGURATION: {
            'missing': ['missing_config', 'missing_property', 'missing_environment'],
            'invalid': ['invalid_config', 'invalid_value', 'config_parse_error'],
            'initialization': ['init_failed', 'startup_error', 'bootstrap_error'],
        },
        ErrorCategory.LOGIC: {
            'validation': ['validation_error', 'invalid_input', 'constraint_violation'],
            'business': ['business_rule_violation', 'invalid_state', 'invalid_operation'],
            'data': ['data_format_error', 'parse_error', 'serialization_error'],
        },
    }

    SEVERITY_SCORING = {
        'critical_keywords': ['critical', 'fatal', 'crash', 'panic', 'abort', 'emergency', 'severe', 'catastrophic'],
        'high_keywords': ['error', 'failed', 'exception', 'timeout', 'denied', 'unavailable', 'refused', 'exhausted'],
        'medium_keywords': ['warning', 'warn', 'deprecated', 'slow', 'retry', 'recoverable', 'partial'],
        'low_keywords': ['info', 'debug', 'trace', 'notice', 'verbose'],
    }

    CONTEXT_WEIGHTS = {
        'production': 1.5,
        'staging': 1.2,
        'development': 0.8,
        'test': 0.5,
    }

    ERROR_INDICATORS = {
        'exception_indicators': ['exception', 'error', 'failed', 'failure', 'fault', 'crash'],
        'warning_indicators': ['warning', 'warn', 'caution', 'attention', 'alert'],
        'info_indicators': ['info', 'information', 'notice', 'status'],
        'debug_indicators': ['debug', 'trace', 'verbose', 'diagnostic'],
    }

    STACK_TRACE_PATTERNS = [
        r'Traceback\s*\(most recent call last\)',
        r'at\s+[\w\.$]+\([\w\.]+:\d+\)',
        r'at\s+[\w\.$]+\([\w\.]+\)',
        r'Caused by:\s*[\w\.]+Exception',
        r'Stack trace:',
        r'java\.lang\.\w+Exception',
        r'\w+Error:\s+',
    ]

    def __init__(self):
        self.category_keywords = CATEGORY_KEYWORDS
        self.classification_history: Dict[str, int] = defaultdict(int)
        self._classification_cache: Dict[str, ErrorClassification] = {}
        self._pattern_to_category: Dict[str, ErrorCategory] = {}
        self._compiled_stack_patterns = [re.compile(p, re.IGNORECASE) for p in self.STACK_TRACE_PATTERNS]
        self._classification_rules: List[Dict[str, Any]] = []
        self._init_classification_rules()

    def _init_classification_rules(self) -> None:
        """初始化分类规则 - 定义优先级分类规则"""
        self._classification_rules = [
            {
                'name': 'database_constraint',
                'patterns': [r'foreign key', r'unique constraint', r'check constraint', r'primary key'],
                'category': ErrorCategory.DATABASE,
                'subcategory': 'constraint_violation',
                'confidence': 0.95,
            },
            {
                'name': 'network_connection',
                'patterns': [r'connection refused', r'connection reset', r'connection timeout', r'ECONNREFUSED'],
                'category': ErrorCategory.NETWORK,
                'subcategory': 'connection_error',
                'confidence': 0.95,
            },
            {
                'name': 'security_auth',
                'patterns': [r'authentication failed', r'invalid credentials', r'login failed', r'access denied'],
                'category': ErrorCategory.SECURITY,
                'subcategory': 'authentication',
                'confidence': 0.95,
            },
            {
                'name': 'memory_oom',
                'patterns': [r'out of memory', r'oom', r'memory exhausted', r'heap space'],
                'category': ErrorCategory.MEMORY,
                'subcategory': 'allocation_failed',
                'confidence': 0.95,
            },
            {
                'name': 'file_system',
                'patterns': [r'no such file', r'file not found', r'disk full', r'permission denied'],
                'category': ErrorCategory.FILE_SYSTEM,
                'subcategory': 'access_error',
                'confidence': 0.90,
            },
            {
                'name': 'external_service',
                'patterns': [r'service unavailable', r'upstream failed', r'circuit breaker', r'rate limit'],
                'category': ErrorCategory.EXTERNAL_SERVICE,
                'subcategory': 'availability',
                'confidence': 0.90,
            },
            {
                'name': 'runtime_exception',
                'patterns': [r'NullPointerException', r'IndexError', r'KeyError', r'TypeError', r'ValueError'],
                'category': ErrorCategory.RUNTIME,
                'subcategory': 'exception',
                'confidence': 0.95,
            },
            {
                'name': 'timeout_error',
                'patterns': [r'timeout', r'timed out', r'deadline exceeded'],
                'category': ErrorCategory.NETWORK,
                'subcategory': 'timeout',
                'confidence': 0.85,
            },
            {
                'name': 'resource_exhausted',
                'patterns': [r'too many open files', r'pool exhausted', r'queue full', r'thread pool'],
                'category': ErrorCategory.RESOURCE,
                'subcategory': 'pool_exhausted',
                'confidence': 0.90,
            },
            {
                'name': 'config_error',
                'patterns': [r'configuration error', r'missing config', r'invalid setting', r'property not found'],
                'category': ErrorCategory.CONFIGURATION,
                'subcategory': 'invalid',
                'confidence': 0.90,
            },
        ]

    def classify(self, entry: LogEntry, matched_pattern: Optional[ErrorPattern] = None) -> ErrorClassification:
        """分类日志条目 - 使用多策略分类方法
        
        分类策略优先级：
        1. 缓存命中 - 返回缓存的分类结果
        2. 模式匹配 - 使用预定义的错误模式
        3. 规则匹配 - 使用优先级分类规则
        4. 层级分类 - 使用层级分类结构
        5. 关键词分类 - 使用关键词权重评分
        6. 特征分类 - 使用消息特征提取
        7. 默认分类 - 返回未知分类
        """
        cache_key = hashlib.md5(entry.message.encode()).hexdigest()[:16]
        if cache_key in self._classification_cache:
            cached = self._classification_cache[cache_key]
            self.classification_history[cached.category.value] += 1
            return cached

        if matched_pattern and matched_pattern.category != ErrorCategory.UNKNOWN:
            classification = ErrorClassification(
                category=matched_pattern.category,
                subcategory=matched_pattern.name,
                confidence=0.95,
                keywords_matched=matched_pattern.keywords,
                pattern_matched=matched_pattern.pattern_id
            )
            self._classification_cache[cache_key] = classification
            self.classification_history[matched_pattern.category.value] += 1
            return classification

        rule_classification = self._classify_by_rules(entry.message)
        if rule_classification:
            self._classification_cache[cache_key] = rule_classification
            self.classification_history[rule_classification.category.value] += 1
            return rule_classification

        message_lower = entry.message.lower()
        scores: Dict[ErrorCategory, Tuple[float, List[str]]] = {}

        for category, keywords in self.category_keywords.items():
            matched_keywords = []
            score = 0.0
            for keyword in keywords:
                if keyword in message_lower:
                    matched_keywords.append(keyword)
                    score += 1.0

            if matched_keywords:
                scores[category] = (score / len(keywords), matched_keywords)

        hierarchical_result = self._classify_hierarchically(message_lower)
        if hierarchical_result:
            category, subcategory, confidence = hierarchical_result
            if category not in scores or confidence > scores.get(category, (0, []))[0]:
                classification = ErrorClassification(
                    category=category,
                    subcategory=subcategory,
                    confidence=confidence,
                    keywords_matched=self._get_keywords_for_category(category, message_lower)
                )
                self._classification_cache[cache_key] = classification
                self.classification_history[category.value] += 1
                return classification

        if scores:
            best_category = max(scores.keys(), key=lambda k: scores[k][0])
            score, keywords = scores[best_category]
            confidence = min(0.9, score * 2)

            self.classification_history[best_category.value] += 1

            classification = ErrorClassification(
                category=best_category,
                subcategory=self._determine_subcategory(best_category, message_lower),
                confidence=confidence,
                keywords_matched=keywords
            )
            self._classification_cache[cache_key] = classification
            return classification

        ml_classification = self._classify_with_ml_features(entry)
        if ml_classification:
            self._classification_cache[cache_key] = ml_classification
            self.classification_history[ml_classification.category.value] += 1
            return ml_classification

        context_classification = self._classify_by_context(entry)
        if context_classification:
            self._classification_cache[cache_key] = context_classification
            self.classification_history[context_classification.category.value] += 1
            return context_classification

        classification = ErrorClassification(
            category=ErrorCategory.UNKNOWN,
            subcategory="unclassified",
            confidence=0.0,
            keywords_matched=[]
        )
        self._classification_cache[cache_key] = classification
        return classification

    def _classify_by_rules(self, message: str) -> Optional[ErrorClassification]:
        """基于规则的分类 - 使用预定义的分类规则"""
        message_lower = message.lower()
        
        for rule in self._classification_rules:
            for pattern in rule['patterns']:
                if re.search(pattern, message_lower, re.IGNORECASE):
                    matched_keywords = [p for p in rule['patterns'] if re.search(p, message_lower, re.IGNORECASE)]
                    return ErrorClassification(
                        category=rule['category'],
                        subcategory=rule['subcategory'],
                        confidence=rule['confidence'],
                        keywords_matched=matched_keywords[:5],
                        pattern_matched=f"rule:{rule['name']}"
                    )
        return None

    def _classify_by_context(self, entry: LogEntry) -> Optional[ErrorClassification]:
        """基于上下文的分类 - 使用日志条目的上下文信息"""
        message_lower = entry.message.lower()
        
        if entry.logger_name:
            logger_lower = entry.logger_name.lower()
            if any(kw in logger_lower for kw in ['db', 'sql', 'database', 'hibernate', 'jpa', 'mybatis']):
                return ErrorClassification(
                    category=ErrorCategory.DATABASE,
                    subcategory='database_operation',
                    confidence=0.75,
                    keywords_matched=['logger:database']
                )
            elif any(kw in logger_lower for kw in ['http', 'rest', 'api', 'web', 'controller', 'servlet']):
                return ErrorClassification(
                    category=ErrorCategory.NETWORK,
                    subcategory='http_request',
                    confidence=0.75,
                    keywords_matched=['logger:http']
                )
            elif any(kw in logger_lower for kw in ['security', 'auth', 'login', 'oauth', 'jwt']):
                return ErrorClassification(
                    category=ErrorCategory.SECURITY,
                    subcategory='security_operation',
                    confidence=0.75,
                    keywords_matched=['logger:security']
                )
            elif any(kw in logger_lower for kw in ['cache', 'redis', 'memcached']):
                return ErrorClassification(
                    category=ErrorCategory.EXTERNAL_SERVICE,
                    subcategory='cache_operation',
                    confidence=0.75,
                    keywords_matched=['logger:cache']
                )
        
        for pattern in self._compiled_stack_patterns:
            if pattern.search(message_lower):
                return ErrorClassification(
                    category=ErrorCategory.RUNTIME,
                    subcategory='exception_with_stack_trace',
                    confidence=0.85,
                    keywords_matched=['stack_trace']
                )
        
        return None

    def _classify_hierarchically(self, message: str) -> Optional[Tuple[ErrorCategory, str, float]]:
        for category, subcategories in self.HIERARCHICAL_CATEGORIES.items():
            for subcategory, patterns in subcategories.items():
                for pattern in patterns:
                    if pattern.replace('_', ' ') in message or pattern in message:
                        confidence = 0.85
                        if any(kw in message for kw in self.SEVERITY_SCORING['critical_keywords']):
                            confidence = 0.95
                        return (category, subcategory, confidence)
        return None

    def _classify_with_ml_features(self, entry: LogEntry) -> Optional[ErrorClassification]:
        message = entry.message.lower()
        
        features = self._extract_features(message)
        
        category_scores: Dict[ErrorCategory, float] = defaultdict(float)
        
        for category, keywords in self.category_keywords.items():
            for keyword in keywords:
                if keyword in message:
                    category_scores[category] += features.get('keyword_weight', 1.0)
        
        if entry.level in [LogLevel.ERROR, LogLevel.CRITICAL]:
            for cat in [ErrorCategory.RUNTIME, ErrorCategory.DATABASE, ErrorCategory.NETWORK]:
                category_scores[cat] *= 1.2
        
        if features.get('has_stack_trace'):
            category_scores[ErrorCategory.RUNTIME] *= 1.3
        
        if features.get('has_timeout'):
            category_scores[ErrorCategory.NETWORK] *= 1.5
            category_scores[ErrorCategory.DATABASE] *= 1.3
        
        if features.get('has_memory_keyword'):
            category_scores[ErrorCategory.MEMORY] *= 2.0
        
        if category_scores:
            best_category = max(category_scores.keys(), key=lambda k: category_scores[k])
            confidence = min(0.8, category_scores[best_category] / 10)
            return ErrorClassification(
                category=best_category,
                subcategory=self._determine_subcategory(best_category, message),
                confidence=confidence,
                keywords_matched=self._get_keywords_for_category(best_category, message)
            )
        
        return None

    def _extract_features(self, message: str) -> Dict[str, Any]:
        features = {
            'has_stack_trace': bool(re.search(r'(traceback|stack trace|at\s+\w+\()', message, re.IGNORECASE)),
            'has_timeout': bool(re.search(r'(timeout|timed out|deadline)', message, re.IGNORECASE)),
            'has_memory_keyword': bool(re.search(r'(memory|oom|heap|allocation)', message, re.IGNORECASE)),
            'has_connection_keyword': bool(re.search(r'(connection|connect|socket)', message, re.IGNORECASE)),
            'has_file_keyword': bool(re.search(r'(file|path|directory)', message, re.IGNORECASE)),
            'has_db_keyword': bool(re.search(r'(sql|query|database|table)', message, re.IGNORECASE)),
            'message_length': len(message),
            'word_count': len(message.split()),
            'has_numbers': bool(re.search(r'\d+', message)),
            'has_url': bool(re.search(r'https?://', message)),
            'has_ip': bool(re.search(r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}', message)),
        }
        
        for level, keywords in self.SEVERITY_SCORING.items():
            features[f'has_{level}_keywords'] = any(kw in message for kw in keywords)
        
        features['keyword_weight'] = sum(
            1 for f in features if f.startswith('has_') and features[f]
        )
        
        return features

    def _get_keywords_for_category(self, category: ErrorCategory, message: str) -> List[str]:
        keywords = self.category_keywords.get(category, [])
        return [kw for kw in keywords if kw in message][:5]

    def _determine_subcategory(self, category: ErrorCategory, message: str) -> str:
        subcategory_patterns = {
            ErrorCategory.NETWORK: [
                (r'timeout', 'timeout'),
                (r'connection.*refused', 'connection_refused'),
                (r'dns', 'dns_error'),
                (r'ssl|tls', 'ssl_error'),
                (r'proxy', 'proxy_error'),
                (r'reset', 'connection_reset'),
                (r'broken pipe', 'broken_pipe'),
            ],
            ErrorCategory.DATABASE: [
                (r'deadlock', 'deadlock'),
                (r'constraint', 'constraint_violation'),
                (r'timeout', 'query_timeout'),
                (r'connection.*pool', 'pool_exhausted'),
                (r'transaction', 'transaction_error'),
                (r'duplicate', 'duplicate_key'),
                (r'lock', 'lock_error'),
            ],
            ErrorCategory.MEMORY: [
                (r'out of memory', 'oom'),
                (r'leak', 'memory_leak'),
                (r'heap', 'heap_error'),
                (r'buffer', 'buffer_overflow'),
                (r'allocation', 'allocation_failed'),
            ],
            ErrorCategory.FILE_SYSTEM: [
                (r'not found', 'file_not_found'),
                (r'permission', 'permission_denied'),
                (r'disk.*full', 'disk_full'),
                (r'io error', 'io_error'),
                (r'read only', 'read_only'),
            ],
            ErrorCategory.RUNTIME: [
                (r'null|none', 'null_reference'),
                (r'type', 'type_error'),
                (r'index', 'index_error'),
                (r'key', 'key_error'),
                (r'value', 'value_error'),
                (r'attribute', 'attribute_error'),
            ],
            ErrorCategory.SECURITY: [
                (r'auth', 'authentication'),
                (r'permission|denied', 'authorization'),
                (r'certificate', 'certificate_error'),
                (r'encryption|decrypt', 'encryption_error'),
                (r'injection', 'injection_attempt'),
            ],
        }

        patterns = subcategory_patterns.get(category, [])
        for pattern, subcategory in patterns:
            if re.search(pattern, message, re.IGNORECASE):
                return subcategory

        return "general"

    def get_classification_stats(self) -> Dict[str, Any]:
        return {
            "total_classifications": sum(self.classification_history.values()),
            "by_category": dict(self.classification_history),
            "cache_size": len(self._classification_cache),
            "hierarchical_categories": {
                cat.value: list(subcats.keys()) 
                for cat, subcats in self.HIERARCHICAL_CATEGORIES.items()
            }
        }

    def get_category_distribution(self) -> Dict[str, float]:
        total = sum(self.classification_history.values())
        if total == 0:
            return {}
        return {
            cat: count / total 
            for cat, count in self.classification_history.items()
        }

    def suggest_category_for_pattern(self, pattern: str) -> ErrorCategory:
        pattern_lower = pattern.lower()
        scores: Dict[ErrorCategory, int] = defaultdict(int)
        
        for category, keywords in self.category_keywords.items():
            for keyword in keywords:
                if keyword in pattern_lower:
                    scores[category] += 1
        
        if scores:
            return max(scores.keys(), key=lambda k: scores[k])
        return ErrorCategory.UNKNOWN


class ProblemPredictor:
    """潜在问题预测器 - 增强版
    
    支持多种预测策略：
    1. 趋势预测 - 基于历史趋势分析
    2. 模式预测 - 基于错误模式识别
    3. 资源预测 - 基于资源使用趋势
    4. 异常指标预测 - 基于异常指标检测
    5. 级联故障预测 - 基于错误序列分析
    6. 容量预测 - 基于容量使用趋势
    7. 服务健康预测 - 基于服务状态分析
    8. 时间序列预测 - 基于时间序列分析
    """

    PREDICTION_MODELS = {
        'linear_regression': {'weight': 0.3, 'min_samples': 5},
        'moving_average': {'weight': 0.25, 'window_size': 5},
        'exponential_smoothing': {'weight': 0.25, 'alpha': 0.3},
        'pattern_matching': {'weight': 0.2, 'threshold': 0.7},
        'weighted_average': {'weight': 0.15, 'decay_factor': 0.9},
        'trend_projection': {'weight': 0.2, 'min_trend_points': 3},
    }

    ANOMALY_INDICATORS = [
        ('error_rate_spike', r'error.*rate.*increased|spike.*in.*errors|error.*burst', 0.8),
        ('latency_increase', r'latency.*increased|response.*time.*slow|p99.*high', 0.7),
        ('resource_pressure', r'memory.*usage.*high|cpu.*usage.*high|disk.*almost.*full', 0.75),
        ('connection_pool_drain', r'connection.*pool.*low|pool.*exhausted|pool.*depleted', 0.85),
        ('queue_backup', r'queue.*size.*growing|backlog.*increasing|queue.*depth.*high', 0.7),
        ('retry_escalation', r'retry.*count.*increasing|retry.*failed|retry.*exhausted', 0.8),
        ('timeout_trend', r'timeout.*rate.*increasing|timeout.*frequency.*high', 0.75),
        ('degradation_pattern', r'degraded.*performance|slow.*response|performance.*drop', 0.65),
        ('throughput_drop', r'throughput.*decreased|request.*rate.*low|traffic.*drop', 0.7),
        ('availability_drop', r'availability.*decreased|uptime.*drop|service.*degraded', 0.85),
        ('error_budget_burn', r'error.*budget.*fast|slo.*violation.*risk', 0.8),
        ('saturation_warning', r'saturation.*high|resource.*saturated|capacity.*limit', 0.75),
        ('latency_percentile', r'p95.*high|p99.*high|percentile.*exceeded', 0.7),
        ('gc_pressure', r'gc.*frequency.*high|gc.*pause.*long|garbage.*collection.*pressure', 0.65),
        ('thread_starvation', r'thread.*starvation|thread.*pool.*blocked|thread.*wait.*long', 0.75),
    ]

    SEASONALITY_PATTERNS = {
        'hourly': 24,
        'daily': 24 * 7,
        'weekly': 24 * 7 * 4,
        'monthly': 24 * 7 * 4 * 3,
    }

    RISK_FACTORS = {
        'high_frequency_errors': {'threshold': 10, 'weight': 0.3},
        'error_rate_increasing': {'threshold': 1.5, 'weight': 0.25},
        'multiple_error_types': {'threshold': 3, 'weight': 0.2},
        'recent_deployment': {'window_hours': 24, 'weight': 0.15},
        'resource_near_limit': {'threshold': 0.8, 'weight': 0.25},
        'service_dependency_failure': {'threshold': 1, 'weight': 0.3},
        'recurring_pattern': {'threshold': 3, 'weight': 0.2},
    }

    SERVICE_HEALTH_INDICATORS = {
        'response_time': {'healthy': 100, 'warning': 500, 'critical': 1000},
        'error_rate': {'healthy': 0.01, 'warning': 0.05, 'critical': 0.1},
        'availability': {'healthy': 0.999, 'warning': 0.99, 'critical': 0.95},
        'throughput': {'healthy': 1000, 'warning': 500, 'critical': 100},
    }

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.history_window_days = self.config.get('history_window_days', 7)
        self.prediction_threshold = self.config.get('prediction_threshold', 0.6)
        self.error_trends: Dict[str, List[Tuple[datetime, int]]] = defaultdict(list)
        self.pattern_sequences: Dict[str, List[str]] = defaultdict(list)
        self._prediction_cache: Dict[str, PredictionResult] = {}
        self._baseline_metrics: Dict[str, float] = {}
        self._anomaly_history: List[Dict[str, Any]] = []
        self._service_health_scores: Dict[str, Dict[str, float]] = defaultdict(dict)
        self._risk_assessment: Dict[str, float] = defaultdict(float)
        self._pattern_frequency: Dict[str, List[datetime]] = defaultdict(list)
        self._error_correlation_matrix: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))

    def analyze_trends(self, entries: List[LogEntry]) -> Dict[str, Any]:
        if not entries:
            return {}

        hourly_errors: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))

        for entry in entries:
            if entry.level in [LogLevel.ERROR, LogLevel.CRITICAL] and entry.timestamp:
                hour_key = entry.timestamp.strftime('%Y-%m-%d %H')
                category = entry.error_category.value if entry.error_category else 'unknown'
                hourly_errors[hour_key][category] += 1

        trend_analysis = {
            "hourly_distribution": dict(hourly_errors),
            "total_hours": len(hourly_errors),
            "peak_hours": self._find_peak_hours(hourly_errors),
            "trend_direction": self._calculate_trend_direction(hourly_errors),
            "seasonality": self._detect_seasonality(hourly_errors),
            "anomaly_periods": self._detect_anomaly_periods(hourly_errors),
            "forecast": self._generate_forecast(hourly_errors),
        }

        return trend_analysis

    def _detect_seasonality(self, hourly_errors: Dict[str, Dict[str, int]]) -> Dict[str, Any]:
        if len(hourly_errors) < 24:
            return {'detected': False, 'reason': 'insufficient_data'}
        
        hour_totals = [sum(counts.values()) for counts in hourly_errors.values()]
        
        hourly_pattern = self._calculate_hourly_pattern(hourly_errors)
        
        return {
            'detected': hourly_pattern['strength'] > 0.3,
            'type': 'hourly',
            'strength': hourly_pattern['strength'],
            'peak_hours': hourly_pattern['peak_hours'],
            'low_hours': hourly_pattern['low_hours'],
        }

    def _calculate_hourly_pattern(self, hourly_errors: Dict[str, Dict[str, int]]) -> Dict[str, Any]:
        hour_of_day_totals: Dict[int, List[int]] = defaultdict(list)
        
        for hour_key, counts in hourly_errors.items():
            try:
                dt = datetime.strptime(hour_key, '%Y-%m-%d %H')
                hour_of_day = dt.hour
                hour_of_day_totals[hour_of_day].append(sum(counts.values()))
            except ValueError:
                continue
        
        hour_averages = {
            hour: sum(vals) / len(vals) 
            for hour, vals in hour_of_day_totals.items()
        }
        
        if not hour_averages:
            return {'strength': 0, 'peak_hours': [], 'low_hours': []}
        
        avg = sum(hour_averages.values()) / len(hour_averages)
        variance = sum((v - avg) ** 2 for v in hour_averages.values()) / len(hour_averages)
        strength = min(1.0, variance / (avg + 1) ** 0.5) if avg > 0 else 0
        
        sorted_hours = sorted(hour_averages.items(), key=lambda x: x[1], reverse=True)
        peak_hours = [h for h, v in sorted_hours[:3]]
        low_hours = [h for h, v in sorted_hours[-3:]]
        
        return {
            'strength': strength,
            'peak_hours': peak_hours,
            'low_hours': low_hours,
        }

    def _detect_anomaly_periods(self, hourly_errors: Dict[str, Dict[str, int]]) -> List[Dict[str, Any]]:
        anomalies = []
        
        if len(hourly_errors) < 3:
            return anomalies
        
        totals = [(hour, sum(counts.values())) for hour, counts in hourly_errors.items()]
        values = [t[1] for t in totals]
        
        mean = sum(values) / len(values)
        std = (sum((v - mean) ** 2 for v in values) / len(values)) ** 0.5
        
        threshold = mean + 2 * std if std > 0 else mean * 2
        
        for hour, total in totals:
            if total > threshold:
                anomalies.append({
                    'period': hour,
                    'value': total,
                    'expected': mean,
                    'deviation': (total - mean) / std if std > 0 else 0,
                    'type': 'spike' if total > mean * 2 else 'elevated',
                })
        
        return anomalies

    def _generate_forecast(self, hourly_errors: Dict[str, Dict[str, int]]) -> Dict[str, Any]:
        if len(hourly_errors) < 5:
            return {'available': False, 'reason': 'insufficient_data'}
        
        totals = [sum(counts.values()) for counts in hourly_errors.values()]
        
        ma_forecast = self._moving_average_forecast(totals)
        exp_forecast = self._exponential_smoothing_forecast(totals)
        
        combined_forecast = (
            ma_forecast * self.PREDICTION_MODELS['moving_average']['weight'] +
            exp_forecast * self.PREDICTION_MODELS['exponential_smoothing']['weight']
        )
        
        trend = self._calculate_trend_direction(hourly_errors)
        
        return {
            'available': True,
            'next_hour_estimate': combined_forecast,
            'trend': trend,
            'confidence': self._calculate_forecast_confidence(totals),
            'models': {
                'moving_average': ma_forecast,
                'exponential_smoothing': exp_forecast,
            }
        }

    def _moving_average_forecast(self, values: List[int], window: int = 5) -> float:
        if len(values) < window:
            return sum(values) / len(values)
        return sum(values[-window:]) / window

    def _exponential_smoothing_forecast(self, values: List[int], alpha: float = 0.3) -> float:
        if not values:
            return 0
        
        forecast = values[0]
        for value in values[1:]:
            forecast = alpha * value + (1 - alpha) * forecast
        return forecast

    def _calculate_forecast_confidence(self, values: List[int]) -> str:
        if len(values) < 10:
            return 'low'
        elif len(values) < 30:
            return 'medium'
        else:
            return 'high'

    def _find_peak_hours(self, hourly_errors: Dict[str, Dict[str, int]]) -> List[Dict[str, Any]]:
        hour_totals = [
            (hour, sum(counts.values()))
            for hour, counts in hourly_errors.items()
        ]
        hour_totals.sort(key=lambda x: x[1], reverse=True)
        return [{"hour": h, "error_count": c} for h, c in hour_totals[:5]]

    def _calculate_trend_direction(self, hourly_errors: Dict[str, Dict[str, int]]) -> str:
        if len(hourly_errors) < 2:
            return "insufficient_data"

        sorted_hours = sorted(hourly_errors.keys())
        recent_hours = sorted_hours[-5:] if len(sorted_hours) >= 5 else sorted_hours
        earlier_hours = sorted_hours[:5] if len(sorted_hours) >= 10 else sorted_hours[:len(sorted_hours)//2]

        recent_avg = sum(sum(hourly_errors[h].values()) for h in recent_hours) / len(recent_hours)
        earlier_avg = sum(sum(hourly_errors[h].values()) for h in earlier_hours) / len(earlier_hours) if earlier_hours else recent_avg

        if recent_avg > earlier_avg * 1.5:
            return "increasing"
        elif recent_avg < earlier_avg * 0.7:
            return "decreasing"
        else:
            return "stable"

    def predict(self, entries: List[LogEntry], forecast_hours: int = 24) -> List[PredictionResult]:
        """预测潜在问题 - 使用多维度预测策略
        
        预测策略：
        1. 趋势预测 - 基于历史趋势分析
        2. 模式预测 - 基于错误模式识别
        3. 资源预测 - 基于资源使用趋势
        4. 异常指标预测 - 基于异常指标检测
        5. 级联故障预测 - 基于错误序列分析
        6. 容量预测 - 基于容量使用趋势
        7. 服务健康预测 - 基于服务状态分析
        8. 风险评估预测 - 基于综合风险评估
        """
        predictions = []
        
        self._update_internal_state(entries)
        
        trend_analysis = self.analyze_trends(entries)

        if trend_analysis.get("trend_direction") == "increasing":
            predictions.extend(self._predict_from_trend(trend_analysis, forecast_hours))

        predictions.extend(self._predict_from_patterns(entries, forecast_hours))
        predictions.extend(self._predict_resource_exhaustion(entries, forecast_hours))
        predictions.extend(self._predict_from_anomaly_indicators(entries, forecast_hours))
        predictions.extend(self._predict_cascading_failures(entries, forecast_hours))
        predictions.extend(self._predict_capacity_issues(entries, forecast_hours))
        predictions.extend(self._predict_service_health(entries, forecast_hours))
        predictions.extend(self._predict_from_risk_assessment(entries, forecast_hours))
        predictions.extend(self._predict_time_based_patterns(entries, forecast_hours))
        predictions.extend(self._predict_error_correlation(entries, forecast_hours))

        unique_predictions = self._deduplicate_predictions(predictions)

        return [p for p in unique_predictions if p.probability >= self.prediction_threshold]

    def _update_internal_state(self, entries: List[LogEntry]) -> None:
        """更新内部状态 - 用于预测分析"""
        for entry in entries:
            if entry.level in [LogLevel.ERROR, LogLevel.CRITICAL]:
                pattern_key = entry.error_signature or entry.message[:50]
                if entry.timestamp:
                    self._pattern_frequency[pattern_key].append(entry.timestamp)
                
                if entry.error_category:
                    category = entry.error_category.value
                    for other_entry in entries:
                        if other_entry.event_id != entry.event_id and other_entry.error_category:
                            other_category = other_entry.error_category.value
                            if entry.timestamp and other_entry.timestamp:
                                time_diff = abs((entry.timestamp - other_entry.timestamp).total_seconds())
                                if time_diff < 300:
                                    self._error_correlation_matrix[category][other_category] += 1

    def _predict_service_health(self, entries: List[LogEntry], forecast_hours: int) -> List[PredictionResult]:
        """预测服务健康状态"""
        predictions = []
        
        service_errors: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))
        
        for entry in entries:
            if entry.level in [LogLevel.ERROR, LogLevel.CRITICAL] and entry.source:
                service_errors[entry.source]['errors'] += 1
                if entry.error_category:
                    service_errors[entry.source][entry.error_category.value] += 1
        
        for service, error_stats in service_errors.items():
            total_errors = error_stats.get('errors', 0)
            
            if total_errors >= 5:
                error_types = len([k for k in error_stats.keys() if k != 'errors'])
                
                health_score = max(0, 1 - (total_errors / 100) - (error_types * 0.1))
                
                if health_score < 0.7:
                    predictions.append(PredictionResult(
                        prediction_id=f"PRED-HEALTH-{service}-{datetime.now().strftime('%Y%m%d%H%M%S')}",
                        prediction_type="service_health_degradation",
                        predicted_issue=f"服务 {service} 健康状态可能下降 (健康分数: {health_score:.2f})",
                        confidence=PredictionConfidence.HIGH if health_score < 0.5 else PredictionConfidence.MEDIUM,
                        probability=min(0.95, 1 - health_score),
                        time_window_hours=forecast_hours,
                        based_on_patterns=[f"service:{service}"],
                        contributing_factors=[
                            f"错误总数: {total_errors}",
                            f"错误类型数: {error_types}",
                            f"健康分数: {health_score:.2f}",
                        ],
                        recommendations=[
                            f"检查服务 {service} 的健康状态",
                            "分析错误根因并修复",
                            "考虑服务重启或扩容",
                            "检查服务依赖项状态",
                        ],
                        historical_context={
                            "service": service,
                            "health_score": health_score,
                            "error_stats": dict(error_stats),
                        }
                    ))
        
        return predictions

    def _predict_from_risk_assessment(self, entries: List[LogEntry], forecast_hours: int) -> List[PredictionResult]:
        """基于风险评估的预测"""
        predictions = []
        
        risk_scores: Dict[str, float] = defaultdict(float)
        risk_factors_found: Dict[str, List[str]] = defaultdict(list)
        
        error_count = sum(1 for e in entries if e.level in [LogLevel.ERROR, LogLevel.CRITICAL])
        if error_count >= self.RISK_FACTORS['high_frequency_errors']['threshold']:
            risk_scores['frequency'] += self.RISK_FACTORS['high_frequency_errors']['weight']
            risk_factors_found['frequency'].append(f"高频错误: {error_count}次")
        
        warning_count = sum(1 for e in entries if e.level == LogLevel.WARNING)
        if error_count > 0:
            error_warning_ratio = error_count / (error_count + warning_count) if (error_count + warning_count) > 0 else 0
            if error_warning_ratio > self.RISK_FACTORS['error_rate_increasing']['threshold']:
                risk_scores['rate'] += self.RISK_FACTORS['error_rate_increasing']['weight']
                risk_factors_found['rate'].append(f"错误率上升: {error_warning_ratio:.2%}")
        
        error_categories = set(e.error_category for e in entries if e.error_category and e.error_category != ErrorCategory.UNKNOWN)
        if len(error_categories) >= self.RISK_FACTORS['multiple_error_types']['threshold']:
            risk_scores['diversity'] += self.RISK_FACTORS['multiple_error_types']['weight']
            risk_factors_found['diversity'].append(f"多种错误类型: {len(error_categories)}种")
        
        recurring_patterns = sum(1 for freq in self._pattern_frequency.values() if len(freq) >= self.RISK_FACTORS['recurring_pattern']['threshold'])
        if recurring_patterns > 0:
            risk_scores['recurring'] += self.RISK_FACTORS['recurring_pattern']['weight']
            risk_factors_found['recurring'].append(f"重复模式: {recurring_patterns}个")
        
        total_risk = sum(risk_scores.values())
        
        if total_risk >= 0.5:
            predictions.append(PredictionResult(
                prediction_id=f"PRED-RISK-{datetime.now().strftime('%Y%m%d%H%M%S')}",
                prediction_type="risk_assessment",
                predicted_issue=f"系统风险评分较高 (风险分数: {total_risk:.2f})",
                confidence=PredictionConfidence.HIGH if total_risk >= 0.7 else PredictionConfidence.MEDIUM,
                probability=min(0.95, total_risk),
                time_window_hours=forecast_hours,
                based_on_patterns=list(risk_scores.keys()),
                contributing_factors=[f for factors in risk_factors_found.values() for f in factors],
                recommendations=[
                    "全面检查系统状态",
                    "优先处理高风险因素",
                    "加强监控和告警",
                    "准备应急响应方案",
                ],
                historical_context={
                    "total_risk_score": total_risk,
                    "risk_breakdown": dict(risk_scores),
                    "factors_found": dict(risk_factors_found),
                }
            ))
        
        return predictions

    def _predict_time_based_patterns(self, entries: List[LogEntry], forecast_hours: int) -> List[PredictionResult]:
        """基于时间模式的预测"""
        predictions = []
        
        hourly_errors: Dict[int, int] = defaultdict(int)
        
        for entry in entries:
            if entry.level in [LogLevel.ERROR, LogLevel.CRITICAL] and entry.timestamp:
                hourly_errors[entry.timestamp.hour] += 1
        
        if len(hourly_errors) >= 3:
            sorted_hours = sorted(hourly_errors.items(), key=lambda x: x[1], reverse=True)
            peak_hours = [h for h, c in sorted_hours[:3]]
            
            current_hour = datetime.now().hour
            hours_until_peak = [(peak - current_hour) % 24 for peak in peak_hours]
            nearest_peak_hours = min(hours_until_peak)
            
            if nearest_peak_hours <= forecast_hours:
                peak_hour = (current_hour + nearest_peak_hours) % 24
                peak_count = hourly_errors.get(peak_hour, 0)
                
                if peak_count >= 5:
                    predictions.append(PredictionResult(
                        prediction_id=f"PRED-TIME-{datetime.now().strftime('%Y%m%d%H%M%S')}",
                        prediction_type="time_based_pattern",
                        predicted_issue=f"预计在 {peak_hour}:00 时段错误率可能达到峰值",
                        confidence=PredictionConfidence.MEDIUM,
                        probability=min(0.85, peak_count / 20),
                        time_window_hours=nearest_peak_hours,
                        based_on_patterns=["hourly_pattern"],
                        contributing_factors=[
                            f"历史峰值时段: {peak_hour}:00",
                            f"历史峰值错误数: {peak_count}",
                            f"距离峰值时段: {nearest_peak_hours}小时",
                        ],
                        recommendations=[
                            f"在 {peak_hour}:00 前增加监控频率",
                            "提前准备应急响应资源",
                            "检查高峰时段的系统负载",
                            "考虑在高峰前进行预防性扩容",
                        ],
                        historical_context={
                            "peak_hour": peak_hour,
                            "peak_count": peak_count,
                            "hourly_distribution": dict(hourly_errors),
                        }
                    ))
        
        return predictions

    def _predict_error_correlation(self, entries: List[LogEntry], forecast_hours: int) -> List[PredictionResult]:
        """基于错误关联的预测"""
        predictions = []
        
        strong_correlations = []
        
        for cat1, correlations in self._error_correlation_matrix.items():
            for cat2, count in correlations.items():
                if cat1 != cat2 and count >= 3:
                    strong_correlations.append((cat1, cat2, count))
        
        for cat1, cat2, count in sorted(strong_correlations, key=lambda x: x[2], reverse=True)[:5]:
            predictions.append(PredictionResult(
                prediction_id=f"PRED-CORR-{cat1}-{cat2}-{datetime.now().strftime('%Y%m%d%H%M%S')}",
                prediction_type="error_correlation",
                predicted_issue=f"检测到 {cat1} 和 {cat2} 错误存在强关联 (共现 {count} 次)",
                confidence=PredictionConfidence.HIGH if count >= 5 else PredictionConfidence.MEDIUM,
                probability=min(0.9, count / 10),
                time_window_hours=forecast_hours,
                based_on_patterns=["error_correlation"],
                contributing_factors=[
                    f"关联错误类型: {cat1} <-> {cat2}",
                    f"共现次数: {count}",
                ],
                recommendations=[
                    f"同时检查 {cat1} 和 {cat2} 相关的系统组件",
                    "分析两个错误类型的因果关系",
                    "考虑是否需要修复根本原因",
                    "监控关联错误的发展趋势",
                ],
                historical_context={
                    "category1": cat1,
                    "category2": cat2,
                    "correlation_count": count,
                }
            ))
        
        return predictions

    def _predict_from_anomaly_indicators(self, entries: List[LogEntry], forecast_hours: int) -> List[PredictionResult]:
        predictions = []
        
        indicator_counts: Dict[str, List[LogEntry]] = defaultdict(list)
        
        for entry in entries:
            message_lower = entry.message.lower()
            for indicator_name, pattern, _ in self.ANOMALY_INDICATORS:
                if re.search(pattern, message_lower, re.IGNORECASE):
                    indicator_counts[indicator_name].append(entry)
        
        for indicator_name, matched_entries in indicator_counts.items():
            if len(matched_entries) >= 2:
                indicator_info = next(
                    (i for i in self.ANOMALY_INDICATORS if i[0] == indicator_name),
                    (indicator_name, '', 0.5)
                )
                
                predictions.append(PredictionResult(
                    prediction_id=f"PRED-ANOM-{indicator_name}-{datetime.now().strftime('%Y%m%d%H%M%S')}",
                    prediction_type="anomaly_indicator",
                    predicted_issue=f"检测到 {indicator_name.replace('_', ' ')} 异常指标",
                    confidence=PredictionConfidence.HIGH if len(matched_entries) >= 5 else PredictionConfidence.MEDIUM,
                    probability=min(0.95, indicator_info[2] + len(matched_entries) * 0.05),
                    time_window_hours=forecast_hours,
                    based_on_patterns=[indicator_name],
                    contributing_factors=[
                        f"匹配日志数: {len(matched_entries)}",
                        f"最近发生: {matched_entries[-1].timestamp.isoformat() if matched_entries[-1].timestamp else 'unknown'}",
                    ],
                    recommendations=self._get_indicator_recommendations(indicator_name),
                    historical_context={"indicator": indicator_name, "count": len(matched_entries)}
                ))
        
        return predictions

    def _predict_cascading_failures(self, entries: List[LogEntry], forecast_hours: int) -> List[PredictionResult]:
        predictions = []
        
        error_sequences: List[List[LogEntry]] = []
        current_sequence: List[LogEntry] = []
        
        sorted_entries = sorted(
            [e for e in entries if e.level in [LogLevel.ERROR, LogLevel.CRITICAL]],
            key=lambda x: x.timestamp or datetime.min
        )
        
        for entry in sorted_entries:
            if not entry.timestamp:
                continue
            
            if current_sequence:
                time_diff = (entry.timestamp - current_sequence[-1].timestamp).total_seconds()
                if time_diff < 60:
                    current_sequence.append(entry)
                else:
                    if len(current_sequence) >= 3:
                        error_sequences.append(current_sequence)
                    current_sequence = [entry]
            else:
                current_sequence = [entry]
        
        if len(current_sequence) >= 3:
            error_sequences.append(current_sequence)
        
        for seq in error_sequences:
            if len(seq) >= 5:
                systems = set(e.source for e in seq if e.source)
                categories = set(e.error_category.value for e in seq if e.error_category)
                
                predictions.append(PredictionResult(
                    prediction_id=f"PRED-CASC-{datetime.now().strftime('%Y%m%d%H%M%S')}-{hash(str(seq[0].event_id)) % 10000:04d}",
                    prediction_type="cascading_failure",
                    predicted_issue=f"检测到级联故障风险，涉及 {len(systems)} 个系统",
                    confidence=PredictionConfidence.HIGH,
                    probability=min(0.9, 0.5 + len(seq) * 0.05),
                    time_window_hours=forecast_hours,
                    based_on_patterns=["cascading_failure_pattern"],
                    contributing_factors=[
                        f"连续错误数: {len(seq)}",
                        f"涉及系统: {', '.join(str(s) for s in systems)}",
                        f"错误类别: {', '.join(categories)}",
                    ],
                    recommendations=[
                        "检查服务依赖关系",
                        "实现熔断机制防止故障传播",
                        "检查各系统健康状态",
                        "准备回滚计划",
                    ],
                    historical_context={"sequence_length": len(seq)}
                ))
        
        return predictions

    def _predict_capacity_issues(self, entries: List[LogEntry], forecast_hours: int) -> List[PredictionResult]:
        predictions = []
        
        capacity_keywords = {
            'memory': ['memory', 'heap', 'oom', 'allocation'],
            'disk': ['disk', 'storage', 'space', 'quota'],
            'connection': ['connection', 'pool', 'socket'],
            'thread': ['thread', 'worker', 'executor'],
            'cpu': ['cpu', 'processor', 'load'],
        }
        
        capacity_metrics: Dict[str, Dict[str, Any]] = defaultdict(lambda: {'count': 0, 'trend': [], 'entries': []})
        
        for entry in entries:
            if entry.level not in [LogLevel.ERROR, LogLevel.WARNING]:
                continue
            
            message_lower = entry.message.lower()
            for resource, keywords in capacity_keywords.items():
                if any(kw in message_lower for kw in keywords):
                    capacity_metrics[resource]['count'] += 1
                    capacity_metrics[resource]['entries'].append(entry)
                    if entry.timestamp:
                        capacity_metrics[resource]['trend'].append(
                            (entry.timestamp, 1)
                        )
        
        for resource, metrics in capacity_metrics.items():
            if metrics['count'] >= 3:
                trend = self._analyze_resource_trend(metrics['trend'])
                
                if trend['direction'] == 'increasing':
                    predictions.append(PredictionResult(
                        prediction_id=f"PRED-CAP-{resource}-{datetime.now().strftime('%Y%m%d%H%M%S')}",
                        prediction_type="capacity_exhaustion",
                        predicted_issue=f"预计 {resource} 资源可能在 {forecast_hours} 小时内耗尽",
                        confidence=PredictionConfidence.HIGH if trend['rate'] > 0.5 else PredictionConfidence.MEDIUM,
                        probability=min(0.9, 0.4 + metrics['count'] * 0.05 + trend['rate'] * 0.3),
                        time_window_hours=forecast_hours,
                        based_on_patterns=[f"capacity:{resource}"],
                        contributing_factors=[
                            f"资源相关警告/错误数: {metrics['count']}",
                            f"趋势: {trend['direction']}",
                            f"增长率: {trend['rate']:.2f}/小时",
                        ],
                        recommendations=[
                            f"检查 {resource} 使用情况",
                            f"考虑增加 {resource} 配额",
                            "优化资源使用效率",
                            "设置资源使用告警阈值",
                        ],
                        historical_context={
                            "resource": resource,
                            "count": metrics['count'],
                            "trend": trend,
                        }
                    ))
        
        return predictions

    def _analyze_resource_trend(self, trend_data: List[Tuple[datetime, int]]) -> Dict[str, Any]:
        if len(trend_data) < 2:
            return {'direction': 'unknown', 'rate': 0}
        
        sorted_data = sorted(trend_data, key=lambda x: x[0])
        
        hourly_counts: Dict[str, int] = defaultdict(int)
        for ts, count in sorted_data:
            hour_key = ts.strftime('%Y-%m-%d %H')
            hourly_counts[hour_key] += count
        
        if len(hourly_counts) < 2:
            return {'direction': 'stable', 'rate': 0}
        
        counts = list(hourly_counts.values())
        recent = sum(counts[-3:]) / min(3, len(counts))
        earlier = sum(counts[:-3]) / max(1, len(counts) - 3) if len(counts) > 3 else recent
        
        rate = (recent - earlier) / max(1, earlier)
        
        if rate > 0.2:
            direction = 'increasing'
        elif rate < -0.2:
            direction = 'decreasing'
        else:
            direction = 'stable'
        
        return {
            'direction': direction,
            'rate': abs(rate),
            'recent_avg': recent,
            'earlier_avg': earlier,
        }

    def _get_indicator_recommendations(self, indicator_name: str) -> List[str]:
        recommendations_map = {
            'error_rate_spike': ['检查最近的部署变更', '分析错误日志模式', '考虑回滚或扩容'],
            'latency_increase': ['检查网络延迟', '分析数据库查询性能', '优化慢请求'],
            'resource_pressure': ['检查资源使用情况', '考虑扩容', '优化资源使用'],
            'connection_pool_drain': ['增加连接池大小', '检查连接泄漏', '优化连接复用'],
            'queue_backup': ['增加消费者数量', '检查处理性能', '考虑消息丢弃策略'],
            'retry_escalation': ['检查下游服务状态', '优化重试策略', '实现熔断机制'],
            'timeout_trend': ['增加超时时间', '优化处理逻辑', '检查网络稳定性'],
            'degradation_pattern': ['分析性能瓶颈', '优化关键路径', '考虑缓存策略'],
            'throughput_drop': ['检查系统负载', '分析请求处理链路', '优化瓶颈环节'],
            'availability_drop': ['检查服务健康状态', '验证依赖服务可用性', '准备故障转移'],
            'error_budget_burn': ['评估SLO状态', '考虑暂停发布', '优先修复关键问题'],
            'saturation_warning': ['检查资源容量', '优化资源使用', '考虑扩容'],
            'latency_percentile': ['分析长尾请求', '优化慢查询', '检查GC影响'],
            'gc_pressure': ['调整GC参数', '优化内存分配', '检查内存泄漏'],
            'thread_starvation': ['增加线程池大小', '优化任务处理时间', '检查阻塞操作'],
        }
        return recommendations_map.get(indicator_name, ['分析问题详情并制定解决方案'])

    def _deduplicate_predictions(self, predictions: List[PredictionResult]) -> List[PredictionResult]:
        seen: Dict[str, PredictionResult] = {}
        
        for pred in predictions:
            key = f"{pred.prediction_type}:{pred.predicted_issue}"
            if key not in seen or pred.probability > seen[key].probability:
                seen[key] = pred
        
        return list(seen.values())

    def _predict_from_trend(self, trend_analysis: Dict[str, Any], forecast_hours: int) -> List[PredictionResult]:
        predictions = []
        peak_hours = trend_analysis.get("peak_hours", [])

        if peak_hours:
            peak_hour = peak_hours[0]["hour"]
            peak_count = peak_hours[0]["error_count"]

            predictions.append(PredictionResult(
                prediction_id=f"PRED-TREND-{datetime.now().strftime('%Y%m%d%H%M%S')}",
                prediction_type="error_rate_increase",
                predicted_issue=f"预计在 {peak_hour.split()[1] if ' ' in peak_hour else peak_hour} 时段错误率可能达到峰值",
                confidence=PredictionConfidence.MEDIUM,
                probability=0.7,
                time_window_hours=forecast_hours,
                based_on_patterns=["historical_trend"],
                contributing_factors=[
                    f"历史峰值时段: {peak_hour}",
                    f"历史峰值错误数: {peak_count}"
                ],
                recommendations=[
                    "在预测的高峰时段增加监控频率",
                    "提前准备应急响应资源",
                    "检查高峰时段的系统负载"
                ],
                historical_context=trend_analysis
            ))

        return predictions

    def _predict_from_patterns(self, entries: List[LogEntry], forecast_hours: int) -> List[PredictionResult]:
        predictions = []
        error_by_category: Dict[ErrorCategory, List[LogEntry]] = defaultdict(list)

        for entry in entries:
            if entry.level in [LogLevel.ERROR, LogLevel.CRITICAL]:
                error_by_category[entry.error_category].append(entry)

        for category, cat_entries in error_by_category.items():
            if len(cat_entries) >= 5:
                recent_rate = self._calculate_recent_rate(cat_entries, hours=1)
                if recent_rate > 2:
                    predictions.append(PredictionResult(
                        prediction_id=f"PRED-CAT-{category.value}-{datetime.now().strftime('%Y%m%d%H%M%S')}",
                        prediction_type="category_increase",
                        predicted_issue=f"预计 {category.value} 类错误可能持续发生",
                        confidence=PredictionConfidence.HIGH if recent_rate > 5 else PredictionConfidence.MEDIUM,
                        probability=min(0.95, recent_rate / 10),
                        time_window_hours=forecast_hours,
                        based_on_patterns=[f"category:{category.value}"],
                        contributing_factors=[
                            f"最近1小时错误数: {len([e for e in cat_entries if e.timestamp and (datetime.now() - e.timestamp).total_seconds() < 3600])}",
                            f"错误率: {recent_rate:.2f}/小时"
                        ],
                        recommendations=self._get_category_recommendations(category),
                        historical_context={"category": category.value, "total_errors": len(cat_entries)}
                    ))

        return predictions

    def _predict_resource_exhaustion(self, entries: List[LogEntry], forecast_hours: int) -> List[PredictionResult]:
        predictions = []
        resource_keywords = ['memory', 'disk', 'connection', 'thread', 'file descriptor', 'pool']

        resource_errors: Dict[str, List[LogEntry]] = defaultdict(list)
        for entry in entries:
            if entry.level in [LogLevel.ERROR, LogLevel.WARNING]:
                message_lower = entry.message.lower()
                for keyword in resource_keywords:
                    if keyword in message_lower:
                        resource_errors[keyword].append(entry)
                        break

        for resource, res_entries in resource_errors.items():
            if len(res_entries) >= 3:
                rate = self._calculate_recent_rate(res_entries, hours=1)
                if rate > 0.5:
                    predictions.append(PredictionResult(
                        prediction_id=f"PRED-RES-{resource}-{datetime.now().strftime('%Y%m%d%H%M%S')}",
                        prediction_type="resource_exhaustion",
                        predicted_issue=f"预计 {resource} 资源可能耗尽",
                        confidence=PredictionConfidence.HIGH if rate > 1 else PredictionConfidence.MEDIUM,
                        probability=min(0.9, rate * 0.5),
                        time_window_hours=forecast_hours,
                        based_on_patterns=[f"resource:{resource}"],
                        contributing_factors=[
                            f"资源相关警告/错误数: {len(res_entries)}",
                            f"最近1小时发生率: {rate:.2f}/小时"
                        ],
                        recommendations=[
                            f"检查 {resource} 使用情况",
                            "考虑增加资源配额或优化使用",
                            "设置资源使用告警阈值"
                        ],
                        historical_context={"resource": resource, "error_count": len(res_entries)}
                    ))

        return predictions

    def _calculate_recent_rate(self, entries: List[LogEntry], hours: int = 1) -> float:
        if not entries:
            return 0.0

        recent_entries = [
            e for e in entries
            if e.timestamp and (datetime.now() - e.timestamp).total_seconds() < hours * 3600
        ]

        return len(recent_entries) / hours

    def _get_category_recommendations(self, category: ErrorCategory) -> List[str]:
        recommendations = {
            ErrorCategory.NETWORK: ["检查网络连接状态", "验证服务端点可用性", "考虑增加重试机制"],
            ErrorCategory.DATABASE: ["检查数据库连接池", "优化慢查询", "检查数据库服务器资源"],
            ErrorCategory.MEMORY: ["分析内存使用情况", "检查内存泄漏", "考虑增加内存限制"],
            ErrorCategory.FILE_SYSTEM: ["检查磁盘空间", "验证文件权限", "检查文件系统健康状态"],
            ErrorCategory.PERMISSION: ["验证用户权限", "检查访问控制配置", "审计权限变更"],
            ErrorCategory.CONFIGURATION: ["验证配置文件", "检查环境变量", "确认配置项完整性"],
            ErrorCategory.RUNTIME: ["检查代码逻辑", "添加异常处理", "增加日志详细度"],
            ErrorCategory.SECURITY: ["审计安全事件", "检查认证配置", "验证访问控制"],
            ErrorCategory.PERFORMANCE: ["分析性能瓶颈", "优化关键路径", "考虑缓存策略"],
            ErrorCategory.EXTERNAL_SERVICE: ["检查外部服务状态", "实现熔断机制", "添加降级策略"],
            ErrorCategory.RESOURCE: ["检查资源使用", "优化资源管理", "增加资源配额"],
        }
        return recommendations.get(category, ["分析错误详情并制定解决方案"])


class LogCorrelator:
    """日志关联分析器"""

    def __init__(self, time_window_seconds: int = 60):
        self.time_window = time_window_seconds

    def correlate(self, entries: List[LogEntry]) -> List[CorrelationResult]:
        correlations = []
        correlations.extend(self._find_error_sequences(entries))
        correlations.extend(self._find_request_traces(entries))
        correlations.extend(self._find_recurring_patterns(entries))

        return correlations

    def _find_error_sequences(self, entries: List[LogEntry]) -> List[CorrelationResult]:
        correlations = []
        error_entries = [e for e in entries if e.level in [LogLevel.ERROR, LogLevel.CRITICAL]]

        if len(error_entries) < 2:
            return correlations

        current_sequence = [error_entries[0]]

        for i in range(1, len(error_entries)):
            current = error_entries[i]
            prev = error_entries[i - 1]

            if current.timestamp and prev.timestamp:
                time_diff = (current.timestamp - prev.timestamp).total_seconds()
                if time_diff <= self.time_window:
                    current_sequence.append(current)
                else:
                    if len(current_sequence) >= 2:
                        correlations.append(self._create_correlation(
                            current_sequence, "error_sequence", "连续错误序列"
                        ))
                    current_sequence = [current]

        if len(current_sequence) >= 2:
            correlations.append(self._create_correlation(
                current_sequence, "error_sequence", "连续错误序列"
            ))

        return correlations

    def _find_request_traces(self, entries: List[LogEntry]) -> List[CorrelationResult]:
        correlations = []
        trace_patterns = [
            (r'request[_-]?id[=:]\s*([a-zA-Z0-9-]+)', 'request_id'),
            (r'trace[_-]?id[=:]\s*([a-zA-Z0-9-]+)', 'trace_id'),
            (r'correlation[_-]?id[=:]\s*([a-zA-Z0-9-]+)', 'correlation_id'),
        ]

        trace_entries: Dict[str, List[LogEntry]] = defaultdict(list)

        for entry in entries:
            for pattern, trace_type in trace_patterns:
                match = re.search(pattern, entry.message, re.IGNORECASE)
                if match:
                    trace_id = match.group(1)
                    trace_entries[f"{trace_type}:{trace_id}"].append(entry)
                    break

        for trace_key, trace_list in trace_entries.items():
            if len(trace_list) >= 2:
                trace_type, trace_id = trace_key.split(':', 1)
                correlations.append(self._create_correlation(
                    trace_list, trace_type, f"请求追踪: {trace_id}"
                ))

        return correlations

    def _find_recurring_patterns(self, entries: List[LogEntry]) -> List[CorrelationResult]:
        correlations = []
        message_counts: Dict[str, List[LogEntry]] = defaultdict(list)

        for entry in entries:
            normalized = self._normalize_message(entry.message)
            message_counts[normalized].append(entry)

        for normalized_msg, msg_entries in message_counts.items():
            if len(msg_entries) >= 5:
                correlations.append(self._create_correlation(
                    msg_entries[:20], "recurring_pattern",
                    f"重复模式 (出现{len(msg_entries)}次): {normalized_msg[:50]}"
                ))

        return correlations

    def _normalize_message(self, message: str) -> str:
        normalized = re.sub(r'\d+', 'N', message)
        normalized = re.sub(r'0x[a-fA-F0-9]+', 'HEX', normalized)
        normalized = re.sub(r'[a-fA-F0-9]{8}-[a-fA-F0-9]{4}-[a-fA-F0-9]{4}-[a-fA-F0-9]{4}-[a-fA-F0-9]{12}', 'UUID', normalized)
        normalized = re.sub(r'\s+', ' ', normalized).strip()
        return normalized[:100]

    def _create_correlation(self, entries: List[LogEntry], pattern_type: str, description: str) -> CorrelationResult:
        time_span = 0.0
        if len(entries) >= 2 and entries[0].timestamp and entries[-1].timestamp:
            time_span = (entries[-1].timestamp - entries[0].timestamp).total_seconds()

        return CorrelationResult(
            correlation_id=f"CORR-{datetime.now().strftime('%Y%m%d%H%M%S')}-{id(entries) % 10000:04d}",
            entries=entries,
            time_span_seconds=time_span,
            pattern_type=pattern_type,
            description=description
        )


class AnomalyDetector:
    """异常检测器"""

    def __init__(self, threshold_multiplier: float = 3.0):
        self.threshold_multiplier = threshold_multiplier

    def detect(self, entries: List[LogEntry]) -> List[Dict[str, Any]]:
        anomalies = []
        anomalies.extend(self._detect_error_spike(entries))
        anomalies.extend(self._detect_unusual_patterns(entries))
        anomalies.extend(self._detect_time_anomalies(entries))

        return anomalies

    def _detect_error_spike(self, entries: List[LogEntry]) -> List[Dict[str, Any]]:
        anomalies = []

        error_counts: Dict[str, int] = defaultdict(int)
        for entry in entries:
            if entry.level in [LogLevel.ERROR, LogLevel.CRITICAL]:
                if entry.timestamp:
                    minute_key = entry.timestamp.strftime('%Y-%m-%d %H:%M')
                    error_counts[minute_key] += 1

        if not error_counts:
            return anomalies

        counts = list(error_counts.values())
        avg_count = sum(counts) / len(counts) if counts else 0
        threshold = avg_count * self.threshold_multiplier

        for minute, count in error_counts.items():
            if count > threshold and count > 5:
                anomalies.append({
                    "type": "error_spike",
                    "severity": AlertSeverity.HIGH.value,
                    "timestamp": minute,
                    "description": f"错误数量激增: {count}个错误 (平均: {avg_count:.1f})",
                    "count": count,
                    "average": avg_count
                })

        return anomalies

    def _detect_unusual_patterns(self, entries: List[LogEntry]) -> List[Dict[str, Any]]:
        anomalies = []

        suspicious_patterns = [
            (r'password|passwd|pwd', '可能泄露敏感信息'),
            (r'secret|api[_-]?key|token', '可能泄露认证信息'),
            (r'stack[_-]?trace|Traceback', '可能存在未处理的异常'),
            (r'exception|error.*occurred', '错误信息'),
        ]

        for entry in entries:
            for pattern, description in suspicious_patterns:
                if re.search(pattern, entry.message, re.IGNORECASE):
                    anomalies.append({
                        "type": "suspicious_content",
                        "severity": AlertSeverity.MEDIUM.value,
                        "timestamp": entry.timestamp.isoformat() if entry.timestamp else None,
                        "description": description,
                        "file_path": entry.file_path,
                        "line_number": entry.line_number,
                        "message_preview": entry.message[:100]
                    })

        return anomalies[:50]

    def _detect_time_anomalies(self, entries: List[LogEntry]) -> List[Dict[str, Any]]:
        anomalies = []

        timestamps = [e.timestamp for e in entries if e.timestamp]
        if len(timestamps) < 2:
            return anomalies

        timestamps.sort()
        gaps = []
        for i in range(1, len(timestamps)):
            gap = (timestamps[i] - timestamps[i - 1]).total_seconds()
            gaps.append(gap)

        if not gaps:
            return anomalies

        avg_gap = sum(gaps) / len(gaps)
        threshold = avg_gap * self.threshold_multiplier * 10

        for i, gap in enumerate(gaps):
            if gap > threshold and gap > 300:
                anomalies.append({
                    "type": "time_gap",
                    "severity": AlertSeverity.LOW.value,
                    "timestamp": timestamps[i].isoformat(),
                    "description": f"日志时间间隔异常: {gap:.0f}秒 (平均: {avg_gap:.1f}秒)",
                    "gap_seconds": gap,
                    "average_gap": avg_gap
                })

        return anomalies[:10]


class IntelligentLogAnalyzer:
    """增强智能日志分析器主类"""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.parser = LogParser()
        self.pattern_matcher = IntelligentErrorPatternMatcher(
            self.config.get('custom_patterns', []),
            self.config.get('learning_enabled', True)
        )
        self.error_classifier = ErrorClassifier()
        self.problem_predictor = ProblemPredictor(self.config.get('predictor_config', {}))
        self.correlator = LogCorrelator(
            time_window_seconds=self.config.get('correlation_window', 60)
        )
        self.anomaly_detector = AnomalyDetector(
            threshold_multiplier=self.config.get('anomaly_threshold', 3.0)
        )
        self.alert_counter = 0

    def analyze(
        self,
        log_paths: List[Path],
        log_format: LogFormat = LogFormat.AUTO,
        enable_prediction: bool = False,
        forecast_hours: int = 24
    ) -> LogAnalysisReport:
        all_entries: List[LogEntry] = []
        log_files = []

        for path in log_paths:
            if path.is_file():
                entries = self.parser.parse_file(path, log_format)
                all_entries.extend(entries)
                log_files.append(str(path))
            elif path.is_dir():
                for log_file in path.rglob('*.log'):
                    entries = self.parser.parse_file(log_file, log_format)
                    all_entries.extend(entries)
                    log_files.append(str(log_file))
                for log_file in path.rglob('*.json'):
                    if 'log' in log_file.name.lower():
                        entries = self.parser.parse_file(log_file, log_format)
                        all_entries.extend(entries)
                        log_files.append(str(log_file))

        self.pattern_matcher.learn_pattern(all_entries)
        self._classify_entries(all_entries)

        entries_by_level = self._count_by_level(all_entries)
        entries_by_category = self._count_by_category(all_entries)
        alerts = self._generate_alerts(all_entries)
        correlations = self.correlator.correlate(all_entries)
        anomalies = self.anomaly_detector.detect(all_entries)
        error_patterns = self._summarize_patterns(alerts)

        predictions = []
        trend_analysis = {}
        if enable_prediction:
            predictions = self.problem_predictor.predict(all_entries, forecast_hours)
            trend_analysis = self.problem_predictor.analyze_trends(all_entries)

        summary = self._generate_summary(all_entries, alerts, correlations, anomalies, predictions)
        recommendations = self._generate_recommendations(alerts, anomalies, predictions)

        return LogAnalysisReport(
            report_id=f"LOG-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            generated_at=datetime.now().isoformat(),
            log_files=log_files,
            total_entries=len(all_entries),
            entries_by_level=entries_by_level,
            entries_by_category=entries_by_category,
            error_patterns_found=error_patterns,
            alerts=alerts,
            correlations=correlations,
            anomalies=anomalies,
            predictions=predictions,
            summary=summary,
            recommendations=recommendations,
            trend_analysis=trend_analysis
        )

    def _classify_entries(self, entries: List[LogEntry]) -> None:
        for entry in entries:
            if entry.level in [LogLevel.ERROR, LogLevel.CRITICAL, LogLevel.WARNING]:
                matches = self.pattern_matcher.match(entry)
                matched_pattern = matches[0][0] if matches else None
                classification = self.error_classifier.classify(entry, matched_pattern)
                entry.error_category = classification.category
                entry.error_signature = self.pattern_matcher._extract_signature(entry.message)

    def _count_by_level(self, entries: List[LogEntry]) -> Dict[str, int]:
        counts: Dict[str, int] = defaultdict(int)
        for entry in entries:
            counts[entry.level.value] += 1
        return dict(counts)

    def _count_by_category(self, entries: List[LogEntry]) -> Dict[str, int]:
        counts: Dict[str, int] = defaultdict(int)
        for entry in entries:
            if entry.error_category != ErrorCategory.UNKNOWN:
                counts[entry.error_category.value] += 1
        return dict(counts)

    def _generate_alerts(self, entries: List[LogEntry]) -> List[LogAlert]:
        alerts = []

        for entry in entries:
            if entry.level not in [LogLevel.ERROR, LogLevel.CRITICAL, LogLevel.WARNING]:
                continue

            matches = self.pattern_matcher.match(entry)
            for pattern, match in matches:
                self.alert_counter += 1
                alert = LogAlert(
                    alert_id=f"ALERT-{self.alert_counter:04d}",
                    timestamp=entry.timestamp.isoformat() if entry.timestamp else datetime.now().isoformat(),
                    severity=pattern.severity,
                    pattern_name=pattern.name,
                    message=f"检测到 {pattern.name}: {entry.message[:100]}",
                    log_entry=entry,
                    suggestion=pattern.suggestion,
                    category=pattern.category
                )
                alerts.append(alert)

        return alerts

    def _summarize_patterns(self, alerts: List[LogAlert]) -> List[Dict[str, Any]]:
        pattern_counts: Dict[str, Dict[str, Any]] = defaultdict(lambda: {'count': 0, 'severity': '', 'suggestion': '', 'category': ''})

        for alert in alerts:
            pattern_counts[alert.pattern_name]['count'] += 1
            pattern_counts[alert.pattern_name]['severity'] = alert.severity.value
            pattern_counts[alert.pattern_name]['suggestion'] = alert.suggestion
            pattern_counts[alert.pattern_name]['category'] = alert.category.value

        return [
            {
                'pattern_name': name,
                'count': data['count'],
                'severity': data['severity'],
                'suggestion': data['suggestion'],
                'category': data['category']
            }
            for name, data in sorted(pattern_counts.items(), key=lambda x: x[1]['count'], reverse=True)
        ]

    def _generate_summary(
        self,
        entries: List[LogEntry],
        alerts: List[LogAlert],
        correlations: List[CorrelationResult],
        anomalies: List[Dict],
        predictions: List[PredictionResult]
    ) -> str:
        parts = [
            f"分析了 {len(entries)} 条日志记录。",
            f"发现 {len(alerts)} 个告警，{len(correlations)} 个关联模式，{len(anomalies)} 个异常。"
        ]

        error_count = sum(1 for e in entries if e.level == LogLevel.ERROR)
        critical_count = sum(1 for e in entries if e.level == LogLevel.CRITICAL)

        if critical_count > 0:
            parts.append(f"包含 {critical_count} 条严重错误。")
        if error_count > 0:
            parts.append(f"包含 {error_count} 条错误。")

        if predictions:
            high_confidence = sum(1 for p in predictions if p.confidence == PredictionConfidence.HIGH)
            parts.append(f"生成 {len(predictions)} 个预测，其中 {high_confidence} 个高置信度预测。")

        return " ".join(parts)

    def _generate_recommendations(
        self,
        alerts: List[LogAlert],
        anomalies: List[Dict],
        predictions: List[PredictionResult]
    ) -> List[str]:
        recommendations = set()

        for alert in alerts[:10]:
            if alert.suggestion:
                recommendations.add(alert.suggestion)

        for anomaly in anomalies:
            if anomaly['type'] == 'error_spike':
                recommendations.add("调查错误激增的原因，检查相关服务和依赖")
            elif anomaly['type'] == 'time_gap':
                recommendations.add("检查日志采集是否正常，确认服务是否中断")

        for prediction in predictions:
            recommendations.update(prediction.recommendations[:2])

        return list(recommendations)[:15]

    def generate_markdown_report(self, report: LogAnalysisReport) -> str:
        lines = [
            "# 日志分析报告",
            "",
            f"**报告ID**: {report.report_id}",
            f"**生成时间**: {report.generated_at}",
            f"**分析文件数**: {len(report.log_files)}",
            f"**总日志条数**: {report.total_entries}",
            "",
            "## 摘要",
            "",
            report.summary,
            "",
            "## 日志级别分布",
            "",
            "| 级别 | 数量 |",
            "|------|------|",
        ]

        for level, count in sorted(report.entries_by_level.items()):
            lines.append(f"| {level} | {count} |")

        if report.entries_by_category:
            lines.extend([
                "",
                "## 错误分类分布",
                "",
                "| 分类 | 数量 |",
                "|------|------|",
            ])

            for category, count in sorted(report.entries_by_category.items(), key=lambda x: x[1], reverse=True):
                lines.append(f"| {category} | {count} |")

        if report.error_patterns_found:
            lines.extend([
                "",
                "## 错误模式统计",
                "",
                "| 模式名称 | 出现次数 | 严重程度 | 分类 |",
                "|----------|----------|----------|------|",
            ])

            for pattern in report.error_patterns_found[:10]:
                lines.append(f"| {pattern['pattern_name']} | {pattern['count']} | {pattern['severity']} | {pattern.get('category', 'unknown')} |")

        if report.alerts:
            lines.extend([
                "",
                "## 告警列表",
                "",
            ])

            for alert in report.alerts[:20]:
                lines.extend([
                    f"### {alert.alert_id}: {alert.pattern_name}",
                    "",
                    f"- **严重程度**: {alert.severity.value}",
                    f"- **分类**: {alert.category.value}",
                    f"- **时间**: {alert.timestamp}",
                    f"- **消息**: {alert.message}",
                    f"- **建议**: {alert.suggestion}",
                    f"- **文件**: {alert.log_entry.file_path}:{alert.log_entry.line_number}",
                    "",
                ])

        if report.predictions:
            lines.extend([
                "",
                "## 问题预测",
                "",
            ])

            for pred in report.predictions:
                lines.extend([
                    f"### {pred.prediction_type}",
                    "",
                    f"- **预测问题**: {pred.predicted_issue}",
                    f"- **置信度**: {pred.confidence.value} ({pred.probability:.0%})",
                    f"- **时间窗口**: {pred.time_window_hours} 小时",
                    f"- **建议**: {', '.join(pred.recommendations[:3])}",
                    "",
                ])

        if report.trend_analysis:
            lines.extend([
                "",
                "## 趋势分析",
                "",
                f"- **趋势方向**: {report.trend_analysis.get('trend_direction', 'unknown')}",
                f"- **分析时长**: {report.trend_analysis.get('total_hours', 0)} 小时",
            ])

            peak_hours = report.trend_analysis.get('peak_hours', [])
            if peak_hours:
                lines.append(f"- **峰值时段**: {', '.join(h['hour'] for h in peak_hours[:3])}")

        if report.correlations:
            lines.extend([
                "",
                "## 关联分析",
                "",
            ])

            for corr in report.correlations[:10]:
                lines.extend([
                    f"### {corr.pattern_type}",
                    "",
                    f"- **描述**: {corr.description}",
                    f"- **条目数**: {len(corr.entries)}",
                    f"- **时间跨度**: {corr.time_span_seconds:.1f}秒",
                    "",
                ])

        if report.anomalies:
            lines.extend([
                "",
                "## 异常检测",
                "",
            ])

            for anomaly in report.anomalies[:10]:
                lines.extend([
                    f"- **{anomaly['type']}**: {anomaly['description']}",
                ])

        if report.recommendations:
            lines.extend([
                "",
                "## 建议",
                "",
            ])

            for i, rec in enumerate(report.recommendations, 1):
                lines.append(f"{i}. {rec}")

        return "\n".join(lines)

    def generate_html_report(self, report: LogAnalysisReport) -> str:
        html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <title>日志分析报告 - {report.report_id}</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; margin: 20px; background: #f5f5f5; }}
        .container {{ max-width: 1400px; margin: 0 auto; background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        h1 {{ color: #333; border-bottom: 2px solid #007bff; padding-bottom: 10px; }}
        h2 {{ color: #555; margin-top: 30px; }}
        .summary {{ background: #e7f3ff; padding: 15px; border-radius: 5px; margin: 20px 0; }}
        table {{ width: 100%; border-collapse: collapse; margin: 15px 0; }}
        th, td {{ padding: 10px; text-align: left; border-bottom: 1px solid #ddd; }}
        th {{ background: #f8f9fa; }}
        .alert-critical {{ background: #f8d7da; border-left: 4px solid #dc3545; padding: 10px; margin: 10px 0; }}
        .alert-high {{ background: #fff3cd; border-left: 4px solid #ffc107; padding: 10px; margin: 10px 0; }}
        .alert-medium {{ background: #e2e3e5; border-left: 4px solid #6c757d; padding: 10px; margin: 10px 0; }}
        .alert-low {{ background: #d4edda; border-left: 4px solid #28a745; padding: 10px; margin: 10px 0; }}
        .prediction {{ background: #f0f8ff; border-left: 4px solid #17a2b8; padding: 10px; margin: 10px 0; }}
        .recommendations {{ background: #d4edda; padding: 15px; border-radius: 5px; }}
        .meta {{ color: #666; font-size: 0.9em; }}
        .trend {{ background: #fff3cd; padding: 10px; border-radius: 5px; margin: 10px 0; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>日志分析报告</h1>
        <div class="meta">
            <p>报告ID: {report.report_id} | 生成时间: {report.generated_at}</p>
            <p>分析文件数: {len(report.log_files)} | 总日志条数: {report.total_entries}</p>
        </div>

        <div class="summary">
            <h2>摘要</h2>
            <p>{report.summary}</p>
        </div>

        <h2>日志级别分布</h2>
        <table>
            <tr><th>级别</th><th>数量</th></tr>
"""

        for level, count in sorted(report.entries_by_level.items()):
            html += f"            <tr><td>{level}</td><td>{count}</td></tr>\n"

        html += """        </table>
"""

        if report.entries_by_category:
            html += """        <h2>错误分类分布</h2>
        <table>
            <tr><th>分类</th><th>数量</th></tr>
"""
            for category, count in sorted(report.entries_by_category.items(), key=lambda x: x[1], reverse=True):
                html += f"            <tr><td>{category}</td><td>{count}</td></tr>\n"
            html += """        </table>
"""

        if report.predictions:
            html += """        <h2>问题预测</h2>
"""
            for pred in report.predictions:
                html += f"""        <div class="prediction">
            <strong>{pred.prediction_type}</strong> ({pred.confidence.value})<br>
            <span class="meta">预测: {pred.predicted_issue}</span><br>
            <span class="meta">概率: {pred.probability:.0%} | 时间窗口: {pred.time_window_hours}小时</span><br>
            <em>建议: {', '.join(pred.recommendations[:2])}</em>
        </div>
"""

        if report.trend_analysis:
            html += f"""        <div class="trend">
            <h2>趋势分析</h2>
            <p>趋势方向: {report.trend_analysis.get('trend_direction', 'unknown')}</p>
            <p>分析时长: {report.trend_analysis.get('total_hours', 0)} 小时</p>
        </div>
"""

        if report.alerts:
            html += """        <h2>告警列表</h2>
"""
            for alert in report.alerts[:20]:
                alert_class = f"alert-{alert.severity.value}"
                html += f"""        <div class="{alert_class}">
            <strong>{alert.pattern_name}</strong> [{alert.category.value}]<br>
            <span class="meta">{alert.timestamp}</span><br>
            {alert.message}<br>
            <em>建议: {alert.suggestion}</em>
        </div>
"""

        if report.recommendations:
            html += """        <div class="recommendations">
            <h2>建议</h2>
            <ol>
"""
            for rec in report.recommendations:
                html += f"                <li>{rec}</li>\n"
            html += """            </ol>
        </div>
"""

        html += """    </div>
</body>
</html>
"""
        return html


def load_config(config_path: Path) -> Dict[str, Any]:
    if not config_path.exists():
        return {}

    with open(config_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def main():
    parser = argparse.ArgumentParser(
        description="增强智能日志分析器 - 支持错误模式智能识别、自动分类和问题预测",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 分析单个日志文件
  python log_analyzer.py --log-file app.log --analyze

  # 分析日志目录并生成报告
  python log_analyzer.py --log-dir ./logs --analyze --report report.html

  # 启用问题预测功能
  python log_analyzer.py --log-dir ./logs --predict --forecast-hours 24

  # 使用配置文件
  python log_analyzer.py --config analyzer_config.json --log-dir ./logs
        """
    )

    parser.add_argument(
        "--log-file",
        type=Path,
        help="单个日志文件路径"
    )

    parser.add_argument(
        "--log-dir",
        type=Path,
        help="日志目录路径"
    )

    parser.add_argument(
        "--format",
        choices=["auto", "json", "text", "csv"],
        default="auto",
        help="日志格式 (默认: auto)"
    )

    parser.add_argument(
        "--analyze",
        action="store_true",
        help="执行分析"
    )

    parser.add_argument(
        "--predict",
        action="store_true",
        help="启用问题预测"
    )

    parser.add_argument(
        "--forecast-hours",
        type=int,
        default=24,
        help="预测时间窗口（小时）"
    )

    parser.add_argument(
        "--correlate",
        action="store_true",
        help="启用日志关联分析"
    )

    parser.add_argument(
        "--alert",
        action="store_true",
        help="生成告警"
    )

    parser.add_argument(
        "--report",
        type=str,
        help="报告输出路径 (支持 .json, .md, .html)"
    )

    parser.add_argument(
        "--config",
        type=Path,
        help="配置文件路径"
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

    log_paths = []
    if args.log_file:
        log_paths.append(args.log_file)
    if args.log_dir:
        log_paths.append(args.log_dir)

    if not log_paths:
        parser.print_help()
        print("\n错误: 请指定 --log-file 或 --log-dir")
        sys.exit(1)

    config = {}
    if args.config:
        config = load_config(args.config)

    log_format = LogFormat(args.format)

    analyzer = IntelligentLogAnalyzer(config)
    report = analyzer.analyze(log_paths, log_format, args.predict, args.forecast_hours)

    print("\n" + "=" * 60)
    print("日志分析报告")
    print("=" * 60)
    print(f"报告ID: {report.report_id}")
    print(f"分析文件数: {len(report.log_files)}")
    print(f"总日志条数: {report.total_entries}")
    print(f"\n日志级别分布:")
    for level, count in sorted(report.entries_by_level.items()):
        print(f"  {level}: {count}")

    if report.entries_by_category:
        print(f"\n错误分类分布:")
        for category, count in sorted(report.entries_by_category.items(), key=lambda x: x[1], reverse=True)[:5]:
            print(f"  {category}: {count}")

    if report.alerts:
        print(f"\n告警数: {len(report.alerts)}")
        for alert in report.alerts[:5]:
            print(f"  [{alert.severity.value}] {alert.pattern_name}: {alert.message[:50]}...")

    if report.predictions:
        print(f"\n预测数: {len(report.predictions)}")
        for pred in report.predictions[:3]:
            print(f"  [{pred.confidence.value}] {pred.predicted_issue[:60]}...")

    if report.correlations:
        print(f"\n关联模式数: {len(report.correlations)}")

    if report.anomalies:
        print(f"\n异常数: {len(report.anomalies)}")

    print(f"\n摘要: {report.summary}")

    if args.report:
        report_path = Path(args.report)
        report_path.parent.mkdir(parents=True, exist_ok=True)

        suffix = report_path.suffix.lower()
        if suffix == '.json':
            with open(report_path, 'w', encoding='utf-8') as f:
                json.dump(report.to_dict(), f, ensure_ascii=False, indent=2)
        elif suffix == '.html':
            with open(report_path, 'w', encoding='utf-8') as f:
                f.write(analyzer.generate_html_report(report))
        else:
            with open(report_path, 'w', encoding='utf-8') as f:
                f.write(analyzer.generate_markdown_report(report))

        print(f"\n报告已保存: {report_path}")

    return 0


if __name__ == "__main__":
    sys.exit(main())


class LogAggregator:
    """日志聚合统计器 - 提供高级日志聚合和统计功能
    
    功能包括：
    - 时间窗口聚合
    - 错误模式聚类
    - 统计摘要生成
    - 趋势分析
    - 分布分析
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.window_size_minutes = self.config.get('window_size_minutes', 5)
        self.top_n = self.config.get('top_n', 10)
    
    def aggregate(self, entries: List[LogEntry]) -> Dict[str, Any]:
        """执行完整的日志聚合分析"""
        if not entries:
            return {'error': 'No entries to aggregate'}
        
        return {
            'time_window_aggregation': self._aggregate_by_time_window(entries),
            'level_distribution': self._aggregate_by_level(entries),
            'category_distribution': self._aggregate_by_category(entries),
            'source_distribution': self._aggregate_by_source(entries),
            'error_clustering': self._cluster_errors(entries),
            'hourly_distribution': self._aggregate_by_hour(entries),
            'daily_distribution': self._aggregate_by_day(entries),
            'statistical_summary': self._generate_statistical_summary(entries),
            'top_error_messages': self._get_top_error_messages(entries),
            'error_rate_trend': self._calculate_error_rate_trend(entries),
            'burst_detection': self._detect_error_bursts(entries),
        }
    
    def _aggregate_by_time_window(self, entries: List[LogEntry]) -> List[Dict[str, Any]]:
        """按时间窗口聚合"""
        if not any(e.timestamp for e in entries):
            return []
        
        sorted_entries = sorted([e for e in entries if e.timestamp], key=lambda x: x.timestamp)
        if not sorted_entries:
            return []
        
        window = timedelta(minutes=self.window_size_minutes)
        windows = []
        current_window_start = sorted_entries[0].timestamp
        current_window_entries = []
        
        for entry in sorted_entries:
            if entry.timestamp <= current_window_start + window:
                current_window_entries.append(entry)
            else:
                if current_window_entries:
                    windows.append(self._summarize_window(current_window_start, current_window_entries))
                current_window_start = entry.timestamp
                current_window_entries = [entry]
        
        if current_window_entries:
            windows.append(self._summarize_window(current_window_start, current_window_entries))
        
        return windows
    
    def _summarize_window(self, start_time: datetime, entries: List[LogEntry]) -> Dict[str, Any]:
        """汇总时间窗口内的日志"""
        error_count = sum(1 for e in entries if e.level in [LogLevel.ERROR, LogLevel.CRITICAL])
        warning_count = sum(1 for e in entries if e.level == LogLevel.WARNING)
        
        return {
            'window_start': start_time.isoformat(),
            'window_end': (start_time + timedelta(minutes=self.window_size_minutes)).isoformat(),
            'total_count': len(entries),
            'error_count': error_count,
            'warning_count': warning_count,
            'info_count': sum(1 for e in entries if e.level == LogLevel.INFO),
            'error_rate': error_count / len(entries) if entries else 0,
            'categories': dict(Counter(e.error_category.value for e in entries if e.error_category)),
        }
    
    def _aggregate_by_level(self, entries: List[LogEntry]) -> Dict[str, Any]:
        """按日志级别聚合"""
        level_counts = Counter(e.level.value for e in entries)
        total = len(entries)
        
        return {
            'counts': dict(level_counts),
            'percentages': {level: count / total * 100 for level, count in level_counts.items()},
            'total': total,
        }
    
    def _aggregate_by_category(self, entries: List[LogEntry]) -> Dict[str, Any]:
        """按错误类别聚合"""
        error_entries = [e for e in entries if e.level in [LogLevel.ERROR, LogLevel.CRITICAL, LogLevel.WARNING]]
        category_counts = Counter(e.error_category.value for e in error_entries if e.error_category)
        
        return {
            'counts': dict(category_counts),
            'total_errors': len(error_entries),
            'category_ranking': sorted(category_counts.items(), key=lambda x: x[1], reverse=True),
        }
    
    def _aggregate_by_source(self, entries: List[LogEntry]) -> Dict[str, Any]:
        """按日志来源聚合"""
        source_counts = Counter(e.source for e in entries if e.source)
        source_errors = defaultdict(int)
        
        for e in entries:
            if e.source and e.level in [LogLevel.ERROR, LogLevel.CRITICAL]:
                source_errors[e.source] += 1
        
        return {
            'counts': dict(source_counts),
            'error_counts': dict(source_errors),
            'top_sources': sorted(source_counts.items(), key=lambda x: x[1], reverse=True)[:self.top_n],
        }
    
    def _cluster_errors(self, entries: List[LogEntry]) -> List[Dict[str, Any]]:
        """错误聚类分析"""
        error_entries = [e for e in entries if e.level in [LogLevel.ERROR, LogLevel.CRITICAL]]
        
        signature_groups: Dict[str, List[LogEntry]] = defaultdict(list)
        for entry in error_entries:
            sig = self._extract_error_signature(entry.message)
            signature_groups[sig].append(entry)
        
        clusters = []
        for signature, group in sorted(signature_groups.items(), key=lambda x: len(x[1]), reverse=True)[:self.top_n]:
            clusters.append({
                'signature': signature[:100],
                'count': len(group),
                'first_occurrence': min(e.timestamp for e in group if e.timestamp).isoformat() if group else None,
                'last_occurrence': max(e.timestamp for e in group if e.timestamp).isoformat() if group else None,
                'sample_message': group[0].message[:200] if group else '',
                'severity_distribution': dict(Counter(e.level.value for e in group)),
            })
        
        return clusters
    
    def _extract_error_signature(self, message: str) -> str:
        """提取错误签名"""
        sig = message.lower()
        sig = re.sub(r'\d+\.?\d*', '#NUM#', sig)
        sig = re.sub(r'0x[a-fA-F0-9]+', '#HEX#', sig)
        sig = re.sub(r'[a-fA-F0-9]{8}-[a-fA-F0-9]{4}-[a-fA-F0-9]{4}-[a-fA-F0-9]{4}-[a-fA-F0-9]{12}', '#UUID#', sig)
        sig = re.sub(r'https?://[^\s]+', '#URL#', sig)
        sig = re.sub(r'/[\w/\.]+', '#PATH#', sig)
        sig = re.sub(r'"[^"]*"', '#STR#', sig)
        sig = re.sub(r"'[^']*'", '#STR#', sig)
        sig = re.sub(r'\s+', ' ', sig).strip()
        return sig[:150]
    
    def _aggregate_by_hour(self, entries: List[LogEntry]) -> Dict[str, Any]:
        """按小时聚合"""
        hourly_counts: Dict[int, Dict[str, int]] = defaultdict(lambda: defaultdict(int))
        
        for entry in entries:
            if entry.timestamp:
                hour = entry.timestamp.hour
                hourly_counts[hour][entry.level.value] += 1
        
        return {
            'distribution': {h: dict(counts) for h, counts in hourly_counts.items()},
            'peak_hour': max(hourly_counts.keys(), key=lambda h: sum(hourly_counts[h].values())) if hourly_counts else None,
            'quiet_hour': min(hourly_counts.keys(), key=lambda h: sum(hourly_counts[h].values())) if hourly_counts else None,
        }
    
    def _aggregate_by_day(self, entries: List[LogEntry]) -> Dict[str, Any]:
        """按日期聚合"""
        daily_counts: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))
        
        for entry in entries:
            if entry.timestamp:
                day = entry.timestamp.strftime('%Y-%m-%d')
                daily_counts[day][entry.level.value] += 1
        
        return {
            'distribution': dict(daily_counts),
            'days_analyzed': len(daily_counts),
            'daily_totals': {day: sum(counts.values()) for day, counts in daily_counts.items()},
        }
    
    def _generate_statistical_summary(self, entries: List[LogEntry]) -> Dict[str, Any]:
        """生成统计摘要"""
        error_entries = [e for e in entries if e.level in [LogLevel.ERROR, LogLevel.CRITICAL]]
        
        timestamps = [e.timestamp for e in entries if e.timestamp]
        time_span = None
        if len(timestamps) >= 2:
            time_span = (max(timestamps) - min(timestamps)).total_seconds()
        
        return {
            'total_entries': len(entries),
            'error_entries': len(error_entries),
            'error_rate': len(error_entries) / len(entries) if entries else 0,
            'unique_sources': len(set(e.source for e in entries if e.source)),
            'unique_categories': len(set(e.error_category for e in error_entries if e.error_category)),
            'time_span_seconds': time_span,
            'entries_per_second': len(entries) / time_span if time_span and time_span > 0 else 0,
            'error_rate_per_minute': len(error_entries) / (time_span / 60) if time_span and time_span > 0 else 0,
        }
    
    def _get_top_error_messages(self, entries: List[LogEntry]) -> List[Dict[str, Any]]:
        """获取最常见的错误消息"""
        error_entries = [e for e in entries if e.level in [LogLevel.ERROR, LogLevel.CRITICAL]]
        message_counts = Counter(e.message[:100] for e in error_entries)
        
        return [
            {
                'message': msg,
                'count': count,
                'percentage': count / len(error_entries) * 100 if error_entries else 0,
            }
            for msg, count in message_counts.most_common(self.top_n)
        ]
    
    def _calculate_error_rate_trend(self, entries: List[LogEntry]) -> Dict[str, Any]:
        """计算错误率趋势"""
        error_entries = [e for e in entries if e.level in [LogLevel.ERROR, LogLevel.CRITICAL] and e.timestamp]
        
        if len(error_entries) < 2:
            return {'trend': 'insufficient_data'}
        
        hourly_errors: Dict[str, int] = defaultdict(int)
        for e in error_entries:
            hour_key = e.timestamp.strftime('%Y-%m-%d %H')
            hourly_errors[hour_key] += 1
        
        if len(hourly_errors) < 2:
            return {'trend': 'insufficient_data'}
        
        sorted_hours = sorted(hourly_errors.keys())
        counts = [hourly_errors[h] for h in sorted_hours]
        
        recent_avg = sum(counts[-3:]) / min(3, len(counts))
        earlier_avg = sum(counts[:-3]) / max(1, len(counts) - 3) if len(counts) > 3 else recent_avg
        
        if recent_avg > earlier_avg * 1.3:
            trend = 'increasing'
        elif recent_avg < earlier_avg * 0.7:
            trend = 'decreasing'
        else:
            trend = 'stable'
        
        return {
            'trend': trend,
            'recent_avg': recent_avg,
            'earlier_avg': earlier_avg,
            'change_rate': (recent_avg - earlier_avg) / earlier_avg if earlier_avg > 0 else 0,
        }
    
    def _detect_error_bursts(self, entries: List[LogEntry]) -> List[Dict[str, Any]]:
        """检测错误爆发"""
        error_entries = [e for e in entries if e.level in [LogLevel.ERROR, LogLevel.CRITICAL] and e.timestamp]
        
        if len(error_entries) < 5:
            return []
        
        minute_counts: Dict[str, int] = defaultdict(int)
        for e in error_entries:
            minute_key = e.timestamp.strftime('%Y-%m-%d %H:%M')
            minute_counts[minute_key] += 1
        
        counts = list(minute_counts.values())
        if not counts:
            return []
        
        avg = sum(counts) / len(counts)
        std = (sum((c - avg) ** 2 for c in counts) / len(counts)) ** 0.5 if len(counts) > 1 else 0
        threshold = avg + 2 * std if std > 0 else avg * 2
        
        bursts = []
        for minute, count in minute_counts.items():
            if count > threshold and count > 3:
                bursts.append({
                    'minute': minute,
                    'count': count,
                    'expected': avg,
                    'deviation': (count - avg) / std if std > 0 else 0,
                })
        
        return sorted(bursts, key=lambda x: x['count'], reverse=True)[:10]


class SyntaxErrorDetector:
    """语法错误检测器 - 专门识别代码语法错误
    
    支持检测：
    - Python语法错误
    - JavaScript语法错误
    - Java语法错误
    - SQL语法错误
    - JSON/XML解析错误
    - 配置文件语法错误
    """
    
    SYNTAX_ERROR_PATTERNS = [
        (r'SyntaxError[:\s]*(.+?)(?:\n|$)', 'python_syntax', 'Python语法错误'),
        (r'IndentationError[:\s]*(.+?)(?:\n|$)', 'python_indentation', 'Python缩进错误'),
        (r'TabError[:\s]*(.+?)(?:\n|$)', 'python_tab', 'Python制表符错误'),
        (r'Unexpected token[\'"]?(\w+)[\'"]?', 'js_unexpected_token', 'JavaScript意外标记'),
        (r'Unexpected end of input', 'js_unexpected_end', 'JavaScript意外结束'),
        (r'Uncaught SyntaxError[:\s]*(.+?)(?:\n|$)', 'js_syntax', 'JavaScript语法错误'),
        (r'Parse error[:\s]*syntax error[,:\s]*(.+?)(?:\n|$)', 'php_syntax', 'PHP语法错误'),
        (r'java\.lang\.SyntaxError[:\s]*(.+?)(?:\n|$)', 'java_syntax', 'Java语法错误'),
        (r'cannot find symbol[:\s]*(.+?)(?:\n|$)', 'java_symbol', 'Java符号未找到'),
        (r'; expected', 'java_semicolon', 'Java缺少分号'),
        (r'\) expected', 'java_parenthesis', 'Java缺少右括号'),
        (r'} expected', 'java_brace', 'Java缺少右大括号'),
        (r'SQL syntax[:\s]*(.+?)(?:\n|$)', 'sql_syntax', 'SQL语法错误'),
        (r'You have an error in your SQL syntax', 'mysql_syntax', 'MySQL语法错误'),
        (r'ORA-\d+[:\s]*(.+?)(?:\n|$)', 'oracle_error', 'Oracle数据库错误'),
        (r'PG::SyntaxError[:\s]*(.+?)(?:\n|$)', 'postgres_syntax', 'PostgreSQL语法错误'),
        (r'JSONDecodeError[:\s]*(.+?)(?:\n|$)', 'json_parse', 'JSON解析错误'),
        (r'Expecting property name enclosed in double quotes', 'json_property', 'JSON属性名错误'),
        (r'Extra data[:\s]*(.+?)(?:\n|$)', 'json_extra', 'JSON额外数据'),
        (r'XML parsing error[:\s]*(.+?)(?:\n|$)', 'xml_parse', 'XML解析错误'),
        (r'mismatched tag[:\s]*(.+?)(?:\n|$)', 'xml_tag', 'XML标签不匹配'),
        (r'YAML syntax error[:\s]*(.+?)(?:\n|$)', 'yaml_syntax', 'YAML语法错误'),
        (r'while scanning a simple key', 'yaml_key', 'YAML键错误'),
        (r'ConfigParser[:\s]*(.+?)(?:\n|$)', 'config_parse', '配置文件解析错误'),
        (r'Invalid configuration[:\s]*(.+?)(?:\n|$)', 'config_invalid', '无效配置'),
        (r'TemplateSyntaxError[:\s]*(.+?)(?:\n|$)', 'template_syntax', '模板语法错误'),
        (r'Jinja2 syntax error[:\s]*(.+?)(?:\n|$)', 'jinja2_syntax', 'Jinja2模板语法错误'),
    ]
    
    def __init__(self):
        self._compiled_patterns = [
            (re.compile(p, re.IGNORECASE | re.MULTILINE), error_type, description)
            for p, error_type, description in self.SYNTAX_ERROR_PATTERNS
        ]
    
    def detect(self, entry: LogEntry) -> List[Dict[str, Any]]:
        """检测日志条目中的语法错误"""
        detected_errors = []
        
        for pattern, error_type, description in self._compiled_patterns:
            matches = pattern.finditer(entry.message)
            for match in matches:
                detected_errors.append({
                    'error_type': error_type,
                    'description': description,
                    'matched_text': match.group(0),
                    'detail': match.group(1) if match.lastindex else '',
                    'position': match.start(),
                    'severity': self._determine_severity(error_type),
                    'suggestion': self._get_suggestion(error_type),
                })
        
        return detected_errors
    
    def _determine_severity(self, error_type: str) -> str:
        """确定语法错误的严重程度"""
        critical_types = ['python_syntax', 'js_syntax', 'java_syntax', 'sql_syntax']
        high_types = ['python_indentation', 'js_unexpected_token', 'json_parse', 'xml_parse']
        
        if error_type in critical_types:
            return 'critical'
        elif error_type in high_types:
            return 'high'
        else:
            return 'medium'
    
    def _get_suggestion(self, error_type: str) -> str:
        """获取修复建议"""
        suggestions = {
            'python_syntax': '检查Python代码语法，确保括号、引号匹配',
            'python_indentation': '统一使用空格或制表符进行缩进，建议使用4个空格',
            'python_tab': '避免混用制表符和空格，统一缩进风格',
            'js_unexpected_token': '检查JavaScript代码中的语法错误，注意标点符号',
            'js_unexpected_end': '检查代码是否缺少闭合括号或大括号',
            'js_syntax': '检查JavaScript语法，确保语句完整',
            'java_syntax': '检查Java代码语法，注意分号和大括号',
            'java_symbol': '确保变量或方法已定义，检查导入语句',
            'java_semicolon': '在语句末尾添加分号',
            'java_parenthesis': '检查括号是否匹配',
            'java_brace': '检查大括号是否匹配',
            'sql_syntax': '检查SQL语句语法，确保关键字正确',
            'mysql_syntax': '检查MySQL特定语法，注意引号和关键字',
            'json_parse': '验证JSON格式，确保引号和逗号正确',
            'xml_parse': '验证XML格式，确保标签正确闭合',
            'yaml_syntax': '检查YAML缩进和格式',
            'config_parse': '检查配置文件格式和语法',
            'template_syntax': '检查模板语法，确保标签正确',
            'jinja2_syntax': '检查Jinja2模板语法，注意{% %}标签',
        }
        return suggestions.get(error_type, '检查相关语法错误并修复')
    
    def detect_all(self, entries: List[LogEntry]) -> Dict[str, Any]:
        """检测所有日志条目中的语法错误"""
        all_errors = []
        error_by_type: Dict[str, int] = defaultdict(int)
        error_by_file: Dict[str, int] = defaultdict(int)
        
        for entry in entries:
            errors = self.detect(entry)
            if errors:
                all_errors.extend(errors)
                for error in errors:
                    error_by_type[error['error_type']] += 1
                    if entry.file_path:
                        error_by_file[entry.file_path] += 1
        
        return {
            'total_syntax_errors': len(all_errors),
            'errors': all_errors[:50],
            'by_type': dict(error_by_type),
            'by_file': dict(sorted(error_by_file.items(), key=lambda x: x[1], reverse=True)[:10]),
            'summary': self._generate_summary(all_errors),
        }
    
    def _generate_summary(self, errors: List[Dict[str, Any]]) -> str:
        """生成语法错误摘要"""
        if not errors:
            return '未检测到语法错误'
        
        type_counts = Counter(e['error_type'] for e in errors)
        top_type = type_counts.most_common(1)[0]
        
        return f'检测到 {len(errors)} 个语法错误，最常见的是 {top_type[0]} ({top_type[1]} 次)'


class LogicErrorDetector:
    """逻辑错误检测器 - 识别代码逻辑问题
    
    支持检测：
    - 断言失败
    - 条件逻辑错误
    - 状态不一致
    - 数据验证错误
    - 业务规则违反
    """
    
    LOGIC_ERROR_PATTERNS = [
        (r'AssertionError[:\s]*(.+?)(?:\n|$)', 'assertion_failed', '断言失败'),
        (r'assert\s+failed[:\s]*(.+?)(?:\n|$)', 'assert_failed', '断言失败'),
        (r'Invariant violation[:\s]*(.+?)(?:\n|$)', 'invariant_violation', '不变量违反'),
        (r'Precondition failed[:\s]*(.+?)(?:\n|$)', 'precondition_failed', '前置条件失败'),
        (r'Postcondition failed[:\s]*(.+?)(?:\n|$)', 'postcondition_failed', '后置条件失败'),
        (r'Invalid state[:\s]*(.+?)(?:\n|$)', 'invalid_state', '无效状态'),
        (r'Illegal state[:\s]*(.+?)(?:\n|$)', 'illegal_state', '非法状态'),
        (r'State transition error[:\s]*(.+?)(?:\n|$)', 'state_transition', '状态转换错误'),
        (r'Validation failed[:\s]*(.+?)(?:\n|$)', 'validation_failed', '验证失败'),
        (r'Invalid input[:\s]*(.+?)(?:\n|$)', 'invalid_input', '无效输入'),
        (r'Business rule violation[:\s]*(.+?)(?:\n|$)', 'business_rule', '业务规则违反'),
        (r'Constraint violation[:\s]*(.+?)(?:\n|$)', 'constraint_violation', '约束违反'),
        (r'Data integrity error[:\s]*(.+?)(?:\n|$)', 'data_integrity', '数据完整性错误'),
        (r'Consistency error[:\s]*(.+?)(?:\n|$)', 'consistency_error', '一致性错误'),
        (r'Unexpected value[:\s]*(.+?)(?:\n|$)', 'unexpected_value', '意外值'),
        (r'Invalid argument[:\s]*(.+?)(?:\n|$)', 'invalid_argument', '无效参数'),
        (r'IllegalArgumentException[:\s]*(.+?)(?:\n|$)', 'illegal_argument', '非法参数'),
        (r'IllegalStateException[:\s]*(.+?)(?:\n|$)', 'illegal_state_exception', '非法状态异常'),
    ]
    
    def __init__(self):
        self._compiled_patterns = [
            (re.compile(p, re.IGNORECASE | re.MULTILINE), error_type, description)
            for p, error_type, description in self.LOGIC_ERROR_PATTERNS
        ]
    
    def detect(self, entry: LogEntry) -> List[Dict[str, Any]]:
        """检测日志条目中的逻辑错误"""
        detected_errors = []
        
        for pattern, error_type, description in self._compiled_patterns:
            matches = pattern.finditer(entry.message)
            for match in matches:
                detected_errors.append({
                    'error_type': error_type,
                    'description': description,
                    'matched_text': match.group(0),
                    'detail': match.group(1) if match.lastindex else '',
                    'severity': self._determine_severity(error_type),
                    'suggestion': self._get_suggestion(error_type),
                    'category': self._categorize(error_type),
                })
        
        return detected_errors
    
    def _determine_severity(self, error_type: str) -> str:
        """确定逻辑错误的严重程度"""
        critical_types = ['assertion_failed', 'invariant_violation', 'data_integrity']
        high_types = ['invalid_state', 'illegal_state', 'business_rule', 'constraint_violation']
        
        if error_type in critical_types:
            return 'critical'
        elif error_type in high_types:
            return 'high'
        else:
            return 'medium'
    
    def _categorize(self, error_type: str) -> str:
        """对逻辑错误进行分类"""
        categories = {
            'assertion': ['assertion_failed', 'assert_failed', 'invariant_violation'],
            'state': ['invalid_state', 'illegal_state', 'state_transition', 'illegal_state_exception'],
            'validation': ['validation_failed', 'invalid_input', 'invalid_argument', 'illegal_argument'],
            'business': ['business_rule', 'constraint_violation', 'data_integrity', 'consistency_error'],
            'contract': ['precondition_failed', 'postcondition_failed'],
        }
        
        for category, types in categories.items():
            if error_type in types:
                return category
        return 'other'
    
    def _get_suggestion(self, error_type: str) -> str:
        """获取修复建议"""
        suggestions = {
            'assertion_failed': '检查断言条件是否正确，验证输入数据',
            'assert_failed': '检查断言语句，确保条件符合预期',
            'invariant_violation': '检查类或模块的不变量约束',
            'precondition_failed': '验证方法调用前的条件是否满足',
            'postcondition_failed': '检查方法执行后的状态是否正确',
            'invalid_state': '检查对象状态是否处于有效状态',
            'illegal_state': '确保在正确的状态下执行操作',
            'state_transition': '验证状态转换逻辑是否正确',
            'validation_failed': '检查输入验证规则',
            'invalid_input': '验证输入数据格式和范围',
            'business_rule': '检查业务规则实现是否正确',
            'constraint_violation': '验证数据约束条件',
            'data_integrity': '检查数据一致性',
            'consistency_error': '确保数据在不同组件间保持一致',
        }
        return suggestions.get(error_type, '分析逻辑错误原因并修复')
    
    def detect_all(self, entries: List[LogEntry]) -> Dict[str, Any]:
        """检测所有日志条目中的逻辑错误"""
        all_errors = []
        error_by_type: Dict[str, int] = defaultdict(int)
        error_by_category: Dict[str, int] = defaultdict(int)
        
        for entry in entries:
            errors = self.detect(entry)
            if errors:
                all_errors.extend(errors)
                for error in errors:
                    error_by_type[error['error_type']] += 1
                    error_by_category[error['category']] += 1
        
        return {
            'total_logic_errors': len(all_errors),
            'errors': all_errors[:50],
            'by_type': dict(error_by_type),
            'by_category': dict(error_by_category),
            'summary': self._generate_summary(all_errors),
        }
    
    def _generate_summary(self, errors: List[Dict[str, Any]]) -> str:
        """生成逻辑错误摘要"""
        if not errors:
            return '未检测到逻辑错误'
        
        category_counts = Counter(e['category'] for e in errors)
        top_category = category_counts.most_common(1)[0]
        
        return f'检测到 {len(errors)} 个逻辑错误，主要类别: {top_category[0]} ({top_category[1]} 次)'
