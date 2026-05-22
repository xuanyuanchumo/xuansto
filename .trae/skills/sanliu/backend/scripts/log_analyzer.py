#!/usr/bin/env python3
"""
日志分析脚本 - 分析技能调用日志，识别常见错误模式，生成错误统计报告
支持多种日志格式：JSON、文本、结构化日志、CSV、Syslog、Apache/Nginx、自定义格式
增强功能：跨模块问题追踪、问题趋势分析、问题优先级评估、日志聚合分析、智能告警、版本化报告输出
"""

import re
import json
import os
import sys
import csv
import hashlib
import statistics
import gzip
import zipfile
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any, Optional, Callable, Set, Tuple, Union, Iterator
from dataclasses import dataclass, field, asdict
from collections import defaultdict, Counter
from enum import Enum
import argparse
import logging
import traceback


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
    TEXT = "text"
    STRUCTURED = "structured"
    CSV = "csv"
    SYSLOG = "syslog"
    APACHE = "apache"
    NGINX = "nginx"
    AUTO = "auto"


class IssuePriority(Enum):
    P0_CRITICAL = "P0"
    P1_HIGH = "P1"
    P2_MEDIUM = "P2"
    P3_LOW = "P3"
    P4_INFO = "P4"


class TrendDirection(Enum):
    INCREASING = "increasing"
    DECREASING = "decreasing"
    STABLE = "stable"
    SPIKE = "spike"


@dataclass
class LogEntry:
    timestamp: datetime
    level: LogLevel
    message: str
    source: str
    line_number: Optional[int] = None
    context: Dict[str, Any] = field(default_factory=dict)
    raw_line: str = ""
    module: str = ""
    function: str = ""


@dataclass
class ErrorPattern:
    pattern_id: str
    name: str
    regex: str
    description: str
    severity: str
    category: str
    suggested_fix: str
    occurrence_count: int = 0
    affected_files: Set[str] = field(default_factory=set)
    examples: List[str] = field(default_factory=list)


@dataclass
class CrossModuleIssue:
    issue_id: str
    pattern: ErrorPattern
    affected_modules: Set[str] = field(default_factory=set)
    propagation_path: List[str] = field(default_factory=list)
    root_module: str = ""
    priority: IssuePriority = IssuePriority.P3_LOW
    estimated_impact: float = 0.0


@dataclass
class TrendData:
    pattern_id: str
    time_series: List[Tuple[datetime, int]] = field(default_factory=list)
    direction: TrendDirection = TrendDirection.STABLE
    change_rate: float = 0.0
    prediction: Optional[int] = None
    anomaly_detected: bool = False


@dataclass
class PriorityAssessment:
    issue_id: str
    priority: IssuePriority
    score: float
    factors: Dict[str, float] = field(default_factory=dict)
    reasoning: str = ""
    recommended_action: str = ""


@dataclass
class AnalysisResult:
    total_entries: int
    error_count: int
    warning_count: int
    unique_errors: int
    time_range: Tuple[datetime, datetime]
    patterns_found: List[ErrorPattern]
    file_stats: Dict[str, Dict[str, int]]
    hourly_distribution: Dict[str, int]
    top_errors: List[Dict[str, Any]]
    cross_module_issues: List[CrossModuleIssue] = field(default_factory=list)
    trend_analysis: List[TrendData] = field(default_factory=list)
    priority_assessments: List[PriorityAssessment] = field(default_factory=list)


@dataclass
class AnalysisReport:
    timestamp: str
    log_files: List[str]
    analysis_result: AnalysisResult
    recommendations: List[str]
    summary: str


class LogParser:
    """日志解析器，支持多种日志格式"""

    JSON_PATTERN = re.compile(
        r'^\s*\{.*"timestamp".*\}.*$',
        re.MULTILINE | re.DOTALL
    )

    STRUCTURED_PATTERN = re.compile(
        r'^(\d{4}-\d{2}-\d{2}[T\s]\d{2}:\d{2}:\d{2}[\.,]?\d*)\s+'
        r'(\w+)\s+'
        r'\[([^\]]+)\]\s+'
        r'(.*)$'
    )

    SIMPLE_PATTERN = re.compile(
        r'^(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2})\s+'
        r'(DEBUG|INFO|WARNING|ERROR|CRITICAL|TRACE|FATAL)\s+'
        r'(.+)$'
    )

    SYSLOG_PATTERN = re.compile(
        r'^(\w{3}\s+\d{1,2}\s+\d{2}:\d{2}:\d{2})\s+'
        r'(\S+)\s+'
        r'(\S+?)(?:\[\d+\])?:\s+'
        r'(.*)$'
    )

    APACHE_PATTERN = re.compile(
        r'^(\S+)\s+\S+\s+\S+\s+\[([^\]]+)\]\s+'
        r'"(\S+)\s+(\S+)\s+(\S+)"\s+'
        r'(\d+)\s+(\d+|-)'
    )

    NGINX_PATTERN = re.compile(
        r'^(\S+)\s+-\s+\S+\s+\[([^\]]+)\]\s+'
        r'"(\S+)\s+(\S+)\s+(\S+)"\s+'
        r'(\d+)\s+(\d+)'
    )

    CSV_HEADER_PATTERNS = ['timestamp', 'level', 'message', 'time', 'date', 'log_level']

    MODULE_PATTERN = re.compile(
        r'(?:module|mod|component)[:\s]+(\w+)',
        re.IGNORECASE
    )

    FUNCTION_PATTERN = re.compile(
        r'(?:function|func|method)[:\s]+(\w+)',
        re.IGNORECASE
    )

    REQUEST_ID_PATTERN = re.compile(
        r'(?:request_id|requestId|trace_id|traceId|correlation_id)[:\s]+([a-zA-Z0-9\-_]+)',
        re.IGNORECASE
    )

    def __init__(self):
        self.parsers: List[Callable[[str], Optional[LogEntry]]] = [
            self._parse_json,
            self._parse_structured,
            self._parse_syslog,
            self._parse_apache,
            self._parse_nginx,
            self._parse_simple,
        ]
        self._csv_headers: Optional[List[str]] = None

    def detect_format(self, sample_lines: List[str]) -> LogFormat:
        """自动检测日志格式"""
        if not sample_lines:
            return LogFormat.TEXT

        sample = '\n'.join(sample_lines[:10])

        try:
            for line in sample_lines:
                line = line.strip()
                if line and line.startswith('{'):
                    json.loads(line)
                    return LogFormat.JSON
        except json.JSONDecodeError:
            pass

        if self.STRUCTURED_PATTERN.search(sample):
            return LogFormat.STRUCTURED

        if self.SYSLOG_PATTERN.search(sample):
            return LogFormat.SYSLOG

        if self.APACHE_PATTERN.search(sample):
            return LogFormat.APACHE

        if self.NGINX_PATTERN.search(sample):
            return LogFormat.NGINX

        if self._detect_csv(sample_lines):
            return LogFormat.CSV

        if self.SIMPLE_PATTERN.search(sample):
            return LogFormat.TEXT

        return LogFormat.TEXT

    def _detect_csv(self, sample_lines: List[str]) -> bool:
        """检测CSV格式"""
        if len(sample_lines) < 2:
            return False
        try:
            reader = csv.reader(sample_lines[:2])
            rows = list(reader)
            if len(rows) >= 2:
                header = [h.lower().strip() for h in rows[0]]
                return any(h in header for h in self.CSV_HEADER_PATTERNS)
        except Exception:
            pass
        return False

    def parse_line(self, line: str, source: str = "unknown") -> Optional[LogEntry]:
        """解析单行日志"""
        line = line.strip()
        if not line:
            return None

        for parser in self.parsers:
            try:
                entry = parser(line)
                if entry:
                    entry.source = source
                    entry.raw_line = line
                    entry.module = self._extract_module(line)
                    entry.function = self._extract_function(line)
                    return entry
            except Exception:
                continue

        return self._create_default_entry(line, source)

    def _parse_json(self, line: str) -> Optional[LogEntry]:
        """解析JSON格式日志"""
        if not line.startswith('{'):
            return None

        try:
            data = json.loads(line)

            timestamp_str = data.get('timestamp') or data.get('time') or data.get('ts')
            timestamp = self._parse_timestamp(timestamp_str) or datetime.now()

            level_str = data.get('level') or data.get('severity') or 'INFO'
            level = self._parse_level(level_str)

            message = data.get('message') or data.get('msg') or data.get('log') or str(data)

            context = {k: v for k, v in data.items()
                      if k not in ['timestamp', 'time', 'ts', 'level', 'severity', 'message', 'msg', 'log']}

            return LogEntry(
                timestamp=timestamp,
                level=level,
                message=message,
                source="",
                context=context,
                raw_line=line,
                module=data.get('module', data.get('component', '')),
                function=data.get('function', data.get('method', ''))
            )
        except (json.JSONDecodeError, KeyError):
            return None

    def _parse_structured(self, line: str) -> Optional[LogEntry]:
        """解析结构化日志"""
        match = self.STRUCTURED_PATTERN.match(line)
        if not match:
            return None

        timestamp_str, level_str, source, message = match.groups()

        return LogEntry(
            timestamp=self._parse_timestamp(timestamp_str) or datetime.now(),
            level=self._parse_level(level_str),
            message=message.strip(),
            source=source.strip(),
            raw_line=line,
            module=self._extract_module(message),
            function=self._extract_function(message)
        )

    def _parse_simple(self, line: str) -> Optional[LogEntry]:
        """解析简单文本日志"""
        match = self.SIMPLE_PATTERN.match(line)
        if not match:
            return None

        timestamp_str, level_str, message = match.groups()

        return LogEntry(
            timestamp=self._parse_timestamp(timestamp_str) or datetime.now(),
            level=self._parse_level(level_str),
            message=message.strip(),
            source="",
            raw_line=line,
            module=self._extract_module(message),
            function=self._extract_function(message)
        )

    def _create_default_entry(self, line: str, source: str) -> LogEntry:
        """创建默认日志条目"""
        return LogEntry(
            timestamp=datetime.now(),
            level=LogLevel.INFO,
            message=line,
            source=source,
            raw_line=line,
            module=self._extract_module(line),
            function=self._extract_function(line)
        )

    def _extract_module(self, text: str) -> str:
        """提取模块名称"""
        match = self.MODULE_PATTERN.search(text)
        return match.group(1) if match else ""

    def _extract_function(self, text: str) -> str:
        """提取函数名称"""
        match = self.FUNCTION_PATTERN.search(text)
        return match.group(1) if match else ""

    def _parse_timestamp(self, timestamp_str: Optional[str]) -> Optional[datetime]:
        """解析时间戳"""
        if not timestamp_str:
            return None

        formats = [
            '%Y-%m-%dT%H:%M:%S.%f',
            '%Y-%m-%dT%H:%M:%S',
            '%Y-%m-%d %H:%M:%S.%f',
            '%Y-%m-%d %H:%M:%S',
            '%Y-%m-%dT%H:%M:%S.%fZ',
            '%Y-%m-%dT%H:%M:%SZ',
            '%d/%b/%Y:%H:%M:%S',
        ]

        for fmt in formats:
            try:
                return datetime.strptime(timestamp_str.strip(), fmt)
            except ValueError:
                continue

        try:
            from dateutil import parser
            return parser.parse(timestamp_str)
        except ImportError:
            pass

        return None

    def _parse_level(self, level_str: str) -> LogLevel:
        """解析日志级别"""
        level_map = {
            'DEBUG': LogLevel.DEBUG,
            'INFO': LogLevel.INFO,
            'WARNING': LogLevel.WARNING,
            'WARN': LogLevel.WARNING,
            'ERROR': LogLevel.ERROR,
            'CRITICAL': LogLevel.CRITICAL,
            'FATAL': LogLevel.FATAL,
            'TRACE': LogLevel.TRACE,
        }
        return level_map.get(level_str.upper(), LogLevel.INFO)

    def _parse_syslog(self, line: str) -> Optional[LogEntry]:
        """解析Syslog格式日志"""
        match = self.SYSLOG_PATTERN.match(line)
        if not match:
            return None
        
        timestamp_str, hostname, program, message = match.groups()
        timestamp = self._parse_syslog_timestamp(timestamp_str)
        
        level = LogLevel.INFO
        level_match = re.search(r'\b(DEBUG|INFO|WARNING|WARN|ERROR|CRITICAL|FATAL)\b', message, re.IGNORECASE)
        if level_match:
            level = self._parse_level(level_match.group(1))
        
        return LogEntry(
            timestamp=timestamp,
            level=level,
            message=message.strip(),
            source=hostname,
            raw_line=line,
            module=program,
            function=self._extract_function(message)
        )

    def _parse_syslog_timestamp(self, timestamp_str: str) -> datetime:
        """解析Syslog时间戳"""
        try:
            current_year = datetime.now().year
            parsed = datetime.strptime(f"{current_year} {timestamp_str}", "%Y %b %d %H:%M:%S")
            if parsed > datetime.now():
                parsed = parsed.replace(year=current_year - 1)
            return parsed
        except ValueError:
            return datetime.now()

    def _parse_apache(self, line: str) -> Optional[LogEntry]:
        """解析Apache访问日志"""
        match = self.APACHE_PATTERN.match(line)
        if not match:
            return None
        
        ip, timestamp_str, method, path, protocol, status, size = match.groups()
        
        timestamp = self._parse_apache_timestamp(timestamp_str)
        
        status_code = int(status)
        if status_code >= 500:
            level = LogLevel.ERROR
        elif status_code >= 400:
            level = LogLevel.WARNING
        else:
            level = LogLevel.INFO
        
        message = f"{method} {path} {protocol} - {status} ({size} bytes)"
        
        return LogEntry(
            timestamp=timestamp,
            level=level,
            message=message,
            source=ip,
            raw_line=line,
            context={'method': method, 'path': path, 'status': status_code, 'size': size}
        )

    def _parse_apache_timestamp(self, timestamp_str: str) -> datetime:
        """解析Apache时间戳"""
        try:
            return datetime.strptime(timestamp_str, "%d/%b/%Y:%H:%M:%S %z")
        except ValueError:
            try:
                return datetime.strptime(timestamp_str.split()[0], "%d/%b/%Y:%H:%M:%S")
            except ValueError:
                return datetime.now()

    def _parse_nginx(self, line: str) -> Optional[LogEntry]:
        """解析Nginx访问日志"""
        match = self.NGINX_PATTERN.match(line)
        if not match:
            return None
        
        ip, timestamp_str, method, path, protocol, status, size = match.groups()
        
        timestamp = self._parse_nginx_timestamp(timestamp_str)
        
        status_code = int(status)
        if status_code >= 500:
            level = LogLevel.ERROR
        elif status_code >= 400:
            level = LogLevel.WARNING
        else:
            level = LogLevel.INFO
        
        message = f"{method} {path} {protocol} - {status} ({size} bytes)"
        
        return LogEntry(
            timestamp=timestamp,
            level=level,
            message=message,
            source=ip,
            raw_line=line,
            context={'method': method, 'path': path, 'status': status_code, 'size': size}
        )

    def _parse_nginx_timestamp(self, timestamp_str: str) -> datetime:
        """解析Nginx时间戳"""
        try:
            return datetime.strptime(timestamp_str, "%d/%b/%Y:%H:%M:%S %z")
        except ValueError:
            try:
                return datetime.strptime(timestamp_str.split()[0], "%d/%b/%Y:%H:%M:%S")
            except ValueError:
                return datetime.now()

    def parse_csv_file(self, file_path: str) -> List[LogEntry]:
        """解析CSV格式日志文件"""
        entries = []
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    entry = self._parse_csv_row(row, file_path)
                    if entry:
                        entries.append(entry)
        except Exception:
            pass
        return entries

    def _parse_csv_row(self, row: Dict[str, str], source: str) -> Optional[LogEntry]:
        """解析CSV行"""
        timestamp_str = row.get('timestamp') or row.get('time') or row.get('date') or ''
        level_str = row.get('level') or row.get('log_level') or row.get('severity') or 'INFO'
        message = row.get('message') or row.get('msg') or row.get('log') or ''
        
        if not message:
            message = ' | '.join(f"{k}: {v}" for k, v in row.items() if k.lower() not in ['timestamp', 'time', 'date', 'level', 'log_level'])
        
        timestamp = self._parse_timestamp(timestamp_str) or datetime.now()
        level = self._parse_level(level_str)
        
        context = {k: v for k, v in row.items() if k.lower() not in ['timestamp', 'time', 'date', 'level', 'log_level', 'message', 'msg']}
        
        return LogEntry(
            timestamp=timestamp,
            level=level,
            message=message,
            source=source,
            context=context
        )

    def extract_request_id(self, text: str) -> Optional[str]:
        """提取请求ID"""
        match = self.REQUEST_ID_PATTERN.search(text)
        return match.group(1) if match else None


class MLErrorClassifier:
    """机器学习错误分类器 - 使用简单的统计学习方法进行错误分类"""

    def __init__(self):
        self.feature_weights: Dict[str, Dict[str, float]] = defaultdict(lambda: defaultdict(float))
        self.category_counts: Dict[str, int] = defaultdict(int)
        self.word_category_association: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))
        self.is_trained = False
        self.min_confidence = 0.3

    def extract_features(self, message: str) -> Dict[str, float]:
        """从错误消息中提取特征"""
        features = {}
        message_lower = message.lower()
        
        words = re.findall(r'\b\w+\b', message_lower)
        for word in words:
            features[f'word_{word}'] = 1.0
        
        features['has_traceback'] = 1.0 if 'traceback' in message_lower else 0.0
        features['has_exception'] = 1.0 if 'exception' in message_lower else 0.0
        features['has_error'] = 1.0 if 'error' in message_lower else 0.0
        features['has_failed'] = 1.0 if 'failed' in message_lower or 'failure' in message_lower else 0.0
        features['has_timeout'] = 1.0 if 'timeout' in message_lower else 0.0
        features['has_connection'] = 1.0 if 'connection' in message_lower or 'connect' in message_lower else 0.0
        features['has_memory'] = 1.0 if 'memory' in message_lower else 0.0
        features['has_permission'] = 1.0 if 'permission' in message_lower or 'access' in message_lower else 0.0
        features['has_file'] = 1.0 if 'file' in message_lower or 'path' in message_lower else 0.0
        features['has_network'] = 1.0 if any(x in message_lower for x in ['network', 'socket', 'dns', 'http']) else 0.0
        features['has_database'] = 1.0 if any(x in message_lower for x in ['database', 'sql', 'query', 'table']) else 0.0
        features['has_api'] = 1.0 if any(x in message_lower for x in ['api', 'request', 'response', 'endpoint']) else 0.0
        
        features['message_length'] = min(len(message) / 500.0, 1.0)
        features['has_numbers'] = 1.0 if re.search(r'\d+', message) else 0.0
        features['has_path'] = 1.0 if re.search(r'[/\\]', message) else 0.0
        features['has_url'] = 1.0 if re.search(r'https?://', message) else 0.0
        
        return features

    def train(self, labeled_data: List[Tuple[str, str]]):
        """训练分类器"""
        for message, category in labeled_data:
            features = self.extract_features(message)
            self.category_counts[category] += 1
            
            for feature, value in features.items():
                self.word_category_association[feature][category] += value
        
        total_samples = sum(self.category_counts.values())
        for category, count in self.category_counts.items():
            prior = count / total_samples if total_samples > 0 else 0
            self.feature_weights['_prior_'][category] = prior
        
        for feature, category_counts in self.word_category_association.items():
            total_for_feature = sum(category_counts.values())
            for category, count in category_counts.items():
                self.feature_weights[feature][category] = count / total_for_feature if total_for_feature > 0 else 0
        
        self.is_trained = True

    def predict(self, message: str) -> Tuple[str, float]:
        """预测错误类别"""
        if not self.is_trained:
            return "unknown", 0.0
        
        features = self.extract_features(message)
        scores: Dict[str, float] = defaultdict(float)
        
        for category in self.category_counts.keys():
            scores[category] = self.feature_weights['_prior_'].get(category, 0)
        
        for feature, value in features.items():
            if value > 0:
                for category, weight in self.feature_weights[feature].items():
                    scores[category] += value * weight
        
        if not scores:
            return "unknown", 0.0
        
        total_score = sum(scores.values())
        if total_score > 0:
            for category in scores:
                scores[category] /= total_score
        
        best_category = max(scores.keys(), key=lambda k: scores[k])
        confidence = scores[best_category]
        
        return best_category, confidence

    def classify_batch(self, messages: List[str]) -> List[Tuple[str, float]]:
        """批量分类"""
        return [self.predict(msg) for msg in messages]

    def get_category_keywords(self, category: str, top_n: int = 10) -> List[Tuple[str, float]]:
        """获取类别的关键词"""
        keywords = []
        for feature, weights in self.feature_weights.items():
            if feature.startswith('word_') and category in weights:
                word = feature[5:]
                keywords.append((word, weights[category]))
        
        keywords.sort(key=lambda x: x[1], reverse=True)
        return keywords[:top_n]


class ErrorPatternDetector:
    """错误模式检测器"""

    DEFAULT_PATTERNS = [
        ErrorPattern(
            pattern_id="E001",
            name="ImportError",
            regex=r"ImportError|ModuleNotFoundError|No module named",
            description="模块导入错误，可能是依赖缺失或路径问题",
            severity="high",
            category="dependency",
            suggested_fix="检查依赖安装: pip install <module>; 检查PYTHONPATH设置"
        ),
        ErrorPattern(
            pattern_id="E002",
            name="ConnectionError",
            regex=r"ConnectionError|Connection refused|Connection timeout|无法连接",
            description="连接错误，网络或服务不可用",
            severity="high",
            category="network",
            suggested_fix="检查网络连接; 验证服务状态; 检查防火墙设置"
        ),
        ErrorPattern(
            pattern_id="E003",
            name="PermissionError",
            regex=r"PermissionError|Access denied|Permission denied|权限不足",
            description="权限错误，无法访问资源",
            severity="high",
            category="security",
            suggested_fix="检查文件/目录权限; 使用sudo或以管理员身份运行; 检查SELinux设置"
        ),
        ErrorPattern(
            pattern_id="E004",
            name="KeyError/IndexError",
            regex=r"KeyError|IndexError|list index out of range|Key not found",
            description="键或索引访问错误",
            severity="medium",
            category="logic",
            suggested_fix="添加边界检查; 使用.get()方法访问字典; 验证索引范围"
        ),
        ErrorPattern(
            pattern_id="E005",
            name="TypeError",
            regex=r"TypeError|类型错误|takes \d+ positional arguments but",
            description="类型错误，参数或操作类型不匹配",
            severity="medium",
            category="logic",
            suggested_fix="检查参数类型; 添加类型注解; 使用isinstance()验证类型"
        ),
        ErrorPattern(
            pattern_id="E006",
            name="ValueError",
            regex=r"ValueError|invalid value|值错误",
            description="值错误，参数值不合法",
            severity="medium",
            category="logic",
            suggested_fix="验证输入值; 添加值范围检查; 提供清晰的错误信息"
        ),
        ErrorPattern(
            pattern_id="E007",
            name="TimeoutError",
            regex=r"TimeoutError|timeout|timed out|超时",
            description="操作超时",
            severity="medium",
            category="performance",
            suggested_fix="增加超时时间; 优化操作性能; 实现重试机制"
        ),
        ErrorPattern(
            pattern_id="E008",
            name="MemoryError",
            regex=r"MemoryError|out of memory|内存不足",
            description="内存不足错误",
            severity="critical",
            category="resource",
            suggested_fix="优化内存使用; 分批处理数据; 增加系统内存"
        ),
        ErrorPattern(
            pattern_id="E009",
            name="DatabaseError",
            regex=r"DatabaseError|IntegrityError|OperationalError|SQL",
            description="数据库操作错误",
            severity="high",
            category="database",
            suggested_fix="检查SQL语法; 验证数据库连接; 检查约束条件"
        ),
        ErrorPattern(
            pattern_id="E010",
            name="APIError",
            regex=r"APIError|HTTPError|status code [45]\d{2}|请求失败",
            description="API调用错误",
            severity="medium",
            category="api",
            suggested_fix="检查API端点; 验证认证信息; 查看API文档"
        ),
        ErrorPattern(
            pattern_id="E011",
            name="FileNotFoundError",
            regex=r"FileNotFoundError|No such file|文件不存在",
            description="文件未找到",
            severity="medium",
            category="filesystem",
            suggested_fix="检查文件路径; 创建缺失目录; 验证文件权限"
        ),
        ErrorPattern(
            pattern_id="E012",
            name="SyntaxError",
            regex=r"SyntaxError|语法错误|invalid syntax",
            description="语法错误",
            severity="critical",
            category="code",
            suggested_fix="检查代码语法; 验证括号匹配; 检查缩进"
        ),
        ErrorPattern(
            pattern_id="E013",
            name="AttributeError",
            regex=r"AttributeError|has no attribute|对象没有",
            description="属性访问错误",
            severity="medium",
            category="logic",
            suggested_fix="检查对象类型; 验证属性名; 使用hasattr()检查"
        ),
        ErrorPattern(
            pattern_id="E014",
            name="NullPointerError",
            regex=r"NoneType|null pointer|cannot access|空指针",
            description="空值引用错误",
            severity="high",
            category="logic",
            suggested_fix="添加空值检查; 使用可选链操作; 初始化变量"
        ),
        ErrorPattern(
            pattern_id="E015",
            name="SkillCallError",
            regex=r"skill.*error|技能.*错误|SkillCall.*failed",
            description="技能调用错误",
            severity="high",
            category="skill",
            suggested_fix="检查技能参数; 验证技能可用性; 查看技能文档"
        ),
        ErrorPattern(
            pattern_id="E016",
            name="RateLimitError",
            regex=r"RateLimit|rate limit|Too Many Requests|429|限流|频率限制",
            description="API请求频率超限",
            severity="medium",
            category="api",
            suggested_fix="实现请求重试机制; 添加请求限流; 检查API配额"
        ),
        ErrorPattern(
            pattern_id="E017",
            name="AuthenticationError",
            regex=r"Authentication|Unauthorized|401|认证失败|token.*invalid|token.*expired",
            description="认证授权失败",
            severity="high",
            category="security",
            suggested_fix="检查认证凭据; 刷新Token; 验证权限配置"
        ),
        ErrorPattern(
            pattern_id="E018",
            name="ConfigurationError",
            regex=r"ConfigError|配置错误|config.*not found|invalid config|配置项缺失",
            description="配置错误",
            severity="high",
            category="configuration",
            suggested_fix="检查配置文件; 验证配置项; 检查环境变量"
        ),
        ErrorPattern(
            pattern_id="E019",
            name="SerializationError",
            regex=r"SerializationError|JSON.*decode|JSON.*encode|序列化|反序列化|marshal",
            description="序列化/反序列化错误",
            severity="medium",
            category="logic",
            suggested_fix="检查数据格式; 验证JSON结构; 处理特殊字符"
        ),
        ErrorPattern(
            pattern_id="E020",
            name="ConcurrencyError",
            regex=r"Deadlock|RaceCondition|thread.*error|concurrent|并发|锁超时|lock.*timeout",
            description="并发错误",
            severity="high",
            category="logic",
            suggested_fix="检查锁使用; 避免死锁; 使用线程安全的数据结构"
        ),
        ErrorPattern(
            pattern_id="E021",
            name="ResourceExhausted",
            regex=r"ResourceExhausted|too many open files|磁盘空间不足|disk.*full|quota.*exceeded",
            description="资源耗尽",
            severity="critical",
            category="resource",
            suggested_fix="释放资源; 增加系统资源; 优化资源使用"
        ),
        ErrorPattern(
            pattern_id="E022",
            name="NetworkError",
            regex=r"NetworkError|网络错误|DNS.*failed|dns.*error|host.*unreachable|网络不可达",
            description="网络错误",
            severity="high",
            category="network",
            suggested_fix="检查网络连接; 验证DNS配置; 检查防火墙规则"
        ),
        ErrorPattern(
            pattern_id="E023",
            name="ValidationError",
            regex=r"ValidationError|validation.*failed|验证失败|invalid.*input|输入无效",
            description="数据验证错误",
            severity="medium",
            category="logic",
            suggested_fix="检查输入数据; 验证数据格式; 添加数据清洗"
        ),
        ErrorPattern(
            pattern_id="E024",
            name="CacheError",
            regex=r"CacheError|Redis.*error|缓存错误|cache.*miss|memcache.*failed",
            description="缓存错误",
            severity="medium",
            category="performance",
            suggested_fix="检查缓存服务; 验证缓存配置; 实现缓存降级"
        ),
        ErrorPattern(
            pattern_id="E025",
            name="AsyncError",
            regex=r"AsyncError|asyncio.*error|coroutine.*error|await.*error|异步.*错误|Future.*exception",
            description="异步操作错误",
            severity="medium",
            category="logic",
            suggested_fix="检查异步代码; 验证await使用; 处理异步异常"
        ),
        ErrorPattern(
            pattern_id="E026",
            name="DatabaseConnectionError",
            regex=r"connection.*pool|pool.*exhausted|too many connections|数据库连接池|连接池耗尽",
            description="数据库连接池问题",
            severity="high",
            category="database",
            suggested_fix="增加连接池大小; 检查连接泄漏; 优化连接使用"
        ),
        ErrorPattern(
            pattern_id="E027",
            name="DiskIOError",
            regex=r"IOError|disk.*error|disk.*full|No space left|磁盘.*错误|写入失败",
            description="磁盘I/O错误",
            severity="critical",
            category="resource",
            suggested_fix="检查磁盘空间; 检查磁盘健康状态; 清理临时文件"
        ),
        ErrorPattern(
            pattern_id="E028",
            name="SSLTLSError",
            regex=r"SSL.*error|TLS.*error|certificate.*error|SSL.*handshake|证书.*错误|SSL.*验证",
            description="SSL/TLS错误",
            severity="high",
            category="security",
            suggested_fix="检查证书有效性; 更新证书; 检查TLS配置"
        ),
        ErrorPattern(
            pattern_id="E029",
            name="LoadBalancerError",
            regex=r"502|503|504|Bad Gateway|Service Unavailable|Gateway Timeout|负载均衡.*错误",
            description="负载均衡/网关错误",
            severity="high",
            category="network",
            suggested_fix="检查后端服务状态; 检查负载均衡配置; 增加服务实例"
        ),
        ErrorPattern(
            pattern_id="E030",
            name="ContainerError",
            regex=r"container.*error|docker.*error|pod.*error|OOMKilled|容器.*错误|镜像.*拉取失败",
            description="容器/编排错误",
            severity="high",
            category="environment",
            suggested_fix="检查容器资源限制; 检查镜像可用性; 检查编排配置"
        ),
        ErrorPattern(
            pattern_id="E031",
            name="MessageQueueError",
            regex=r"queue.*error|kafka.*error|rabbitmq.*error|消息队列.*错误|MQ.*连接失败",
            description="消息队列错误",
            severity="high",
            category="logic",
            suggested_fix="检查消息队列服务状态; 检查队列配置; 实现消息重试"
        ),
        ErrorPattern(
            pattern_id="E032",
            name="GraphQLerror",
            regex=r"GraphQL.*error|query.*error|mutation.*error|subscription.*error",
            description="GraphQL错误",
            severity="medium",
            category="api",
            suggested_fix="检查GraphQL语法; 验证字段存在; 检查权限配置"
        ),
        ErrorPattern(
            pattern_id="E033",
            name="WebSocketError",
            regex=r"WebSocket.*error|ws.*error|socket.*closed|连接已关闭|websocket.*disconnect",
            description="WebSocket错误",
            severity="medium",
            category="network",
            suggested_fix="检查WebSocket连接状态; 实现重连机制; 检查心跳配置"
        ),
        ErrorPattern(
            pattern_id="E034",
            name="EncodingError",
            regex=r"UnicodeDecodeError|UnicodeEncodeError|encoding.*error|编码.*错误|字符集.*错误",
            description="编码错误",
            severity="medium",
            category="logic",
            suggested_fix="指定正确的编码格式; 使用utf-8编码; 处理特殊字符"
        ),
        ErrorPattern(
            pattern_id="E035",
            name="DependencyVersionError",
            regex=r"version.*conflict|dependency.*conflict|incompatible.*version|版本.*冲突|依赖.*不兼容",
            description="依赖版本冲突",
            severity="high",
            category="dependency",
            suggested_fix="检查依赖版本; 更新依赖; 使用虚拟环境隔离"
        ),
    ]

    def __init__(self, custom_patterns: Optional[List[ErrorPattern]] = None):
        self.patterns = custom_patterns or self.DEFAULT_PATTERNS.copy()
        self.compiled_patterns = {
            p.pattern_id: re.compile(p.regex, re.IGNORECASE)
            for p in self.patterns
        }

    def add_pattern(self, pattern: ErrorPattern):
        """添加自定义错误模式"""
        self.patterns.append(pattern)
        self.compiled_patterns[pattern.pattern_id] = re.compile(
            pattern.regex, re.IGNORECASE
        )

    def detect_patterns(self, entries: List[LogEntry]) -> List[ErrorPattern]:
        """检测日志中的错误模式"""
        pattern_counts = defaultdict(lambda: {"count": 0, "files": set(), "examples": []})

        for entry in entries:
            if entry.level not in [LogLevel.ERROR, LogLevel.CRITICAL]:
                continue

            for pattern in self.patterns:
                compiled = self.compiled_patterns.get(pattern.pattern_id)
                if compiled and compiled.search(entry.message):
                    pid = pattern.pattern_id
                    pattern_counts[pid]["count"] += 1
                    pattern_counts[pid]["files"].add(entry.source)
                    if len(pattern_counts[pid]["examples"]) < 3:
                        pattern_counts[pid]["examples"].append(entry.message[:200])

        results = []
        for pattern in self.patterns:
            if pattern.pattern_id in pattern_counts:
                stats = pattern_counts[pattern.pattern_id]
                pattern.occurrence_count = stats["count"]
                pattern.affected_files = stats["files"]
                pattern.examples = stats["examples"]
                results.append(pattern)

        return sorted(results, key=lambda x: x.occurrence_count, reverse=True)


class CrossModuleTracker:
    """跨模块问题追踪器"""

    def __init__(self):
        self.module_graph: Dict[str, Set[str]] = defaultdict(set)
        self.error_propagation: Dict[str, List[str]] = defaultdict(list)

    def build_module_graph(self, entries: List[LogEntry]) -> None:
        """构建模块依赖图"""
        for entry in entries:
            if entry.module:
                self.module_graph[entry.source].add(entry.module)

    def track_cross_module_issues(
        self,
        entries: List[LogEntry],
        patterns: List[ErrorPattern]
    ) -> List[CrossModuleIssue]:
        """追踪跨模块问题"""
        cross_issues = []
        issue_counter = 0

        for pattern in patterns:
            affected_modules = set()
            propagation_path = []
            error_entries = []

            for entry in entries:
                if entry.level in [LogLevel.ERROR, LogLevel.CRITICAL]:
                    compiled = re.compile(pattern.regex, re.IGNORECASE)
                    if compiled.search(entry.message):
                        error_entries.append(entry)
                        if entry.module:
                            affected_modules.add(entry.module)
                        if entry.source not in propagation_path:
                            propagation_path.append(entry.source)

            if len(affected_modules) > 1 or len(propagation_path) > 1:
                issue_counter += 1
                root_module = self._identify_root_module(error_entries)

                cross_issue = CrossModuleIssue(
                    issue_id=f"CMI-{issue_counter:04d}",
                    pattern=pattern,
                    affected_modules=affected_modules,
                    propagation_path=propagation_path,
                    root_module=root_module,
                    priority=IssuePriority.P2_MEDIUM,
                    estimated_impact=len(affected_modules) * 0.5 + len(propagation_path) * 0.3
                )
                cross_issues.append(cross_issue)

        return cross_issues

    def _identify_root_module(self, error_entries: List[LogEntry]) -> str:
        """识别根模块"""
        module_counts = Counter(entry.module for entry in error_entries if entry.module)
        if module_counts:
            return module_counts.most_common(1)[0][0]
        return ""

    def get_module_dependencies(self, module: str) -> Set[str]:
        """获取模块的依赖"""
        dependencies = set()
        for source, modules in self.module_graph.items():
            if module in modules:
                dependencies.add(source)
        return dependencies

    def analyze_error_propagation(self, entries: List[LogEntry]) -> Dict[str, List[str]]:
        """分析错误传播路径"""
        propagation = defaultdict(list)
        
        error_entries = [e for e in entries if e.level in [LogLevel.ERROR, LogLevel.CRITICAL]]
        
        for i, entry in enumerate(error_entries):
            if entry.module:
                for j in range(i + 1, min(i + 5, len(error_entries))):
                    next_entry = error_entries[j]
                    if next_entry.module and next_entry.module != entry.module:
                        if next_entry.module not in propagation[entry.module]:
                            propagation[entry.module].append(next_entry.module)
        
        return dict(propagation)


class TrendAnalyzer:
    """问题趋势分析器"""

    def __init__(self, window_size: int = 7):
        self.window_size = window_size

    def analyze_trends(
        self,
        entries: List[LogEntry],
        patterns: List[ErrorPattern],
        time_granularity: str = "hour"
    ) -> List[TrendData]:
        """分析问题趋势"""
        trends = []
        
        for pattern in patterns:
            time_series = self._build_time_series(entries, pattern, time_granularity)
            
            if not time_series:
                continue
            
            direction = self._determine_trend_direction(time_series)
            change_rate = self._calculate_change_rate(time_series)
            prediction = self._predict_next_value(time_series)
            anomaly_detected = self._detect_anomaly(time_series)
            
            trend_data = TrendData(
                pattern_id=pattern.pattern_id,
                time_series=time_series,
                direction=direction,
                change_rate=change_rate,
                prediction=prediction,
                anomaly_detected=anomaly_detected
            )
            trends.append(trend_data)
        
        return trends

    def _build_time_series(
        self,
        entries: List[LogEntry],
        pattern: ErrorPattern,
        granularity: str
    ) -> List[Tuple[datetime, int]]:
        """构建时间序列"""
        compiled = re.compile(pattern.regex, re.IGNORECASE)
        
        counts_by_time: Dict[datetime, int] = defaultdict(int)
        
        for entry in entries:
            if compiled.search(entry.message):
                time_key = self._truncate_time(entry.timestamp, granularity)
                counts_by_time[time_key] += 1
        
        sorted_times = sorted(counts_by_time.items())
        return sorted_times

    def _truncate_time(self, dt: datetime, granularity: str) -> datetime:
        """截断时间到指定粒度"""
        if granularity == "minute":
            return dt.replace(second=0, microsecond=0)
        elif granularity == "hour":
            return dt.replace(minute=0, second=0, microsecond=0)
        elif granularity == "day":
            return dt.replace(hour=0, minute=0, second=0, microsecond=0)
        return dt

    def _determine_trend_direction(self, time_series: List[Tuple[datetime, int]]) -> TrendDirection:
        """确定趋势方向"""
        if len(time_series) < 2:
            return TrendDirection.STABLE
        
        values = [v for _, v in time_series]
        
        recent_values = values[-min(5, len(values)):]
        older_values = values[:min(5, len(values))]
        
        recent_avg = sum(recent_values) / len(recent_values)
        older_avg = sum(older_values) / len(older_values)
        
        if older_avg == 0:
            if recent_avg > 0:
                return TrendDirection.SPIKE
            return TrendDirection.STABLE
        
        change_ratio = (recent_avg - older_avg) / older_avg
        
        if change_ratio > 0.5:
            return TrendDirection.SPIKE
        elif change_ratio > 0.1:
            return TrendDirection.INCREASING
        elif change_ratio < -0.1:
            return TrendDirection.DECREASING
        
        return TrendDirection.STABLE

    def _calculate_change_rate(self, time_series: List[Tuple[datetime, int]]) -> float:
        """计算变化率"""
        if len(time_series) < 2:
            return 0.0
        
        values = [v for _, v in time_series]
        
        changes = []
        for i in range(1, len(values)):
            if values[i-1] > 0:
                changes.append((values[i] - values[i-1]) / values[i-1])
        
        if not changes:
            return 0.0
        
        return sum(changes) / len(changes)

    def _predict_next_value(self, time_series: List[Tuple[datetime, int]]) -> Optional[int]:
        """预测下一个值（简单移动平均）"""
        if len(time_series) < 3:
            return None
        
        values = [v for _, v in time_series[-self.window_size:]]
        return int(sum(values) / len(values))

    def _detect_anomaly(self, time_series: List[Tuple[datetime, int]]) -> bool:
        """检测异常"""
        if len(time_series) < 5:
            return False
        
        values = [v for _, v in time_series]
        mean = sum(values) / len(values)
        
        variance = sum((v - mean) ** 2 for v in values) / len(values)
        std_dev = variance ** 0.5
        
        if std_dev == 0:
            return False
        
        last_value = values[-1]
        z_score = abs(last_value - mean) / std_dev
        
        return z_score > 2.0


class PriorityEvaluator:
    """问题优先级评估器"""

    PRIORITY_WEIGHTS = {
        "frequency": 0.25,
        "severity": 0.30,
        "impact_scope": 0.25,
        "recency": 0.20
    }

    def evaluate(
        self,
        pattern: ErrorPattern,
        cross_module_issue: Optional[CrossModuleIssue] = None,
        trend_data: Optional[TrendData] = None
    ) -> PriorityAssessment:
        """评估问题优先级"""
        factors = {}
        
        factors["frequency"] = self._score_frequency(pattern.occurrence_count)
        
        factors["severity"] = self._score_severity(pattern.severity)
        
        impact_scope = len(pattern.affected_files)
        if cross_module_issue:
            impact_scope += len(cross_module_issue.affected_modules)
        factors["impact_scope"] = self._score_impact_scope(impact_scope)
        
        recency_score = 0.5
        if trend_data:
            recency_score = self._score_trend_recency(trend_data)
        factors["recency"] = recency_score
        
        total_score = sum(
            factors[key] * self.PRIORITY_WEIGHTS[key]
            for key in self.PRIORITY_WEIGHTS
        )
        
        priority = self._determine_priority(total_score)
        
        reasoning = self._generate_reasoning(factors, pattern)
        
        recommended_action = self._recommend_action(priority, pattern)
        
        return PriorityAssessment(
            issue_id=cross_module_issue.issue_id if cross_module_issue else f"PAT-{pattern.pattern_id}",
            priority=priority,
            score=total_score,
            factors=factors,
            reasoning=reasoning,
            recommended_action=recommended_action
        )

    def _score_frequency(self, count: int) -> float:
        """评分频率"""
        if count >= 100:
            return 1.0
        elif count >= 50:
            return 0.8
        elif count >= 20:
            return 0.6
        elif count >= 10:
            return 0.4
        elif count >= 5:
            return 0.2
        return 0.1

    def _score_severity(self, severity: str) -> float:
        """评分严重程度"""
        severity_map = {
            "critical": 1.0,
            "high": 0.8,
            "medium": 0.5,
            "low": 0.3,
            "info": 0.1
        }
        return severity_map.get(severity.lower(), 0.5)

    def _score_impact_scope(self, scope: int) -> float:
        """评分影响范围"""
        if scope >= 20:
            return 1.0
        elif scope >= 10:
            return 0.8
        elif scope >= 5:
            return 0.6
        elif scope >= 3:
            return 0.4
        elif scope >= 1:
            return 0.2
        return 0.1

    def _score_trend_recency(self, trend: TrendData) -> float:
        """评分趋势近期性"""
        if trend.direction == TrendDirection.SPIKE:
            return 1.0
        elif trend.direction == TrendDirection.INCREASING:
            return 0.8
        elif trend.direction == TrendDirection.STABLE:
            return 0.5
        return 0.3

    def _determine_priority(self, score: float) -> IssuePriority:
        """确定优先级"""
        if score >= 0.8:
            return IssuePriority.P0_CRITICAL
        elif score >= 0.6:
            return IssuePriority.P1_HIGH
        elif score >= 0.4:
            return IssuePriority.P2_MEDIUM
        elif score >= 0.2:
            return IssuePriority.P3_LOW
        return IssuePriority.P4_INFO

    def _generate_reasoning(self, factors: Dict[str, float], pattern: ErrorPattern) -> str:
        """生成推理说明"""
        reasons = []
        
        if factors["frequency"] >= 0.6:
            reasons.append(f"高频发生({pattern.occurrence_count}次)")
        
        if factors["severity"] >= 0.8:
            reasons.append(f"严重程度高({pattern.severity})")
        
        if factors["impact_scope"] >= 0.6:
            reasons.append(f"影响范围广({len(pattern.affected_files)}个文件)")
        
        if not reasons:
            reasons.append("常规问题")
        
        return "；".join(reasons)

    def _recommend_action(self, priority: IssuePriority, pattern: ErrorPattern) -> str:
        """推荐行动"""
        if priority == IssuePriority.P0_CRITICAL:
            return f"立即处理: {pattern.suggested_fix}"
        elif priority == IssuePriority.P1_HIGH:
            return f"优先处理: {pattern.suggested_fix}"
        elif priority == IssuePriority.P2_MEDIUM:
            return f"计划处理: {pattern.suggested_fix}"
        elif priority == IssuePriority.P3_LOW:
            return f"有时间时处理: {pattern.suggested_fix}"
        return f"记录观察: {pattern.suggested_fix}"


@dataclass
class AggregatedLog:
    hash_key: str
    pattern_signature: str
    count: int
    first_seen: datetime
    last_seen: datetime
    sample_messages: List[str]
    sources: Set[str]
    avg_interval: float


@dataclass
class AlertRule:
    rule_id: str
    name: str
    condition: str
    threshold: float
    time_window_minutes: int
    severity: str
    enabled: bool = True


@dataclass
class Alert:
    alert_id: str
    rule: AlertRule
    triggered_at: datetime
    value: float
    message: str
    related_patterns: List[str]


class LogAggregator:
    """日志聚合分析器"""

    def __init__(self, similarity_threshold: float = 0.8):
        self.similarity_threshold = similarity_threshold
        self.aggregated_logs: Dict[str, AggregatedLog] = {}

    def aggregate(self, entries: List[LogEntry]) -> List[AggregatedLog]:
        """聚合相似日志"""
        for entry in entries:
            signature = self._create_signature(entry.message)
            hash_key = hashlib.md5(signature.encode()).hexdigest()[:12]

            if hash_key not in self.aggregated_logs:
                self.aggregated_logs[hash_key] = AggregatedLog(
                    hash_key=hash_key,
                    pattern_signature=signature,
                    count=1,
                    first_seen=entry.timestamp,
                    last_seen=entry.timestamp,
                    sample_messages=[entry.message[:200]],
                    sources={entry.source},
                    avg_interval=0.0
                )
            else:
                agg = self.aggregated_logs[hash_key]
                prev_time = agg.last_seen
                agg.count += 1
                agg.last_seen = entry.timestamp
                agg.sources.add(entry.source)
                if len(agg.sample_messages) < 5:
                    agg.sample_messages.append(entry.message[:200])
                if prev_time:
                    interval = (entry.timestamp - prev_time).total_seconds()
                    agg.avg_interval = (agg.avg_interval * (agg.count - 1) + interval) / agg.count

        return sorted(self.aggregated_logs.values(), key=lambda x: x.count, reverse=True)

    def _create_signature(self, message: str) -> str:
        """创建日志签名"""
        normalized = re.sub(r'\d+', '<NUM>', message)
        normalized = re.sub(r'0x[0-9a-fA-F]+', '<HEX>', normalized)
        normalized = re.sub(r'[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}', '<UUID>', normalized)
        normalized = re.sub(r'/[\w/.-]+', '<PATH>', normalized)
        normalized = re.sub(r'https?://[^\s]+', '<URL>', normalized)
        normalized = re.sub(r'\b[\w.-]+@[\w.-]+\.\w+\b', '<EMAIL>', normalized)
        normalized = re.sub(r'\s+', ' ', normalized).strip()
        return normalized[:100]

    def get_top_patterns(self, limit: int = 10) -> List[AggregatedLog]:
        """获取高频日志模式"""
        return sorted(self.aggregated_logs.values(), key=lambda x: x.count, reverse=True)[:limit]

    def get_burst_patterns(self, threshold_factor: float = 3.0) -> List[AggregatedLog]:
        """获取突发日志模式"""
        if not self.aggregated_logs:
            return []
        
        intervals = [agg.avg_interval for agg in self.aggregated_logs.values() if agg.avg_interval > 0]
        if not intervals:
            return []
        
        avg_interval = statistics.mean(intervals)
        return [
            agg for agg in self.aggregated_logs.values()
            if agg.avg_interval > 0 and agg.avg_interval < avg_interval / threshold_factor
        ]


class AlertManager:
    """智能告警管理器"""

    DEFAULT_ALERT_RULES = [
        AlertRule(
            rule_id="ALERT001",
            name="错误率过高",
            condition="error_rate",
            threshold=0.1,
            time_window_minutes=5,
            severity="high"
        ),
        AlertRule(
            rule_id="ALERT002",
            name="错误数量激增",
            condition="error_spike",
            threshold=3.0,
            time_window_minutes=10,
            severity="medium"
        ),
        AlertRule(
            rule_id="ALERT003",
            name="新错误模式出现",
            condition="new_pattern",
            threshold=1.0,
            time_window_minutes=30,
            severity="medium"
        ),
        AlertRule(
            rule_id="ALERT004",
            name="关键错误发生",
            condition="critical_error",
            threshold=1.0,
            time_window_minutes=1,
            severity="critical"
        ),
        AlertRule(
            rule_id="ALERT005",
            name="连接错误持续",
            condition="connection_error_streak",
            threshold=5.0,
            time_window_minutes=5,
            severity="high"
        ),
    ]

    def __init__(self, custom_rules: Optional[List[AlertRule]] = None):
        self.rules = custom_rules or self.DEFAULT_ALERT_RULES.copy()
        self.alert_history: List[Alert] = []
        self.alert_counter = 0

    def check_alerts(
        self,
        entries: List[LogEntry],
        patterns: List[ErrorPattern]
    ) -> List[Alert]:
        """检查告警条件"""
        alerts = []
        now = datetime.now()

        for rule in self.rules:
            if not rule.enabled:
                continue

            window_start = now - timedelta(minutes=rule.time_window_minutes)
            window_entries = [e for e in entries if e.timestamp >= window_start]

            triggered, value, message = self._check_condition(rule, window_entries, patterns)

            if triggered:
                self.alert_counter += 1
                alert = Alert(
                    alert_id=f"ALERT-{now.strftime('%Y%m%d')}-{self.alert_counter:04d}",
                    rule=rule,
                    triggered_at=now,
                    value=value,
                    message=message,
                    related_patterns=[p.pattern_id for p in patterns if p.occurrence_count > 0]
                )
                alerts.append(alert)
                self.alert_history.append(alert)

        return alerts

    def _check_condition(
        self,
        rule: AlertRule,
        entries: List[LogEntry],
        patterns: List[ErrorPattern]
    ) -> Tuple[bool, float, str]:
        """检查告警条件"""
        if not entries:
            return False, 0.0, ""

        if rule.condition == "error_rate":
            error_count = sum(1 for e in entries if e.level in [LogLevel.ERROR, LogLevel.CRITICAL])
            rate = error_count / len(entries) if entries else 0
            if rate > rule.threshold:
                return True, rate, f"错误率 {rate:.2%} 超过阈值 {rule.threshold:.2%}"

        elif rule.condition == "error_spike":
            if len(entries) < 10:
                return False, 0.0, ""
            half = len(entries) // 2
            recent_errors = sum(1 for e in entries[half:] if e.level in [LogLevel.ERROR, LogLevel.CRITICAL])
            older_errors = sum(1 for e in entries[:half] if e.level in [LogLevel.ERROR, LogLevel.CRITICAL])
            if older_errors > 0:
                spike = recent_errors / older_errors
                if spike > rule.threshold:
                    return True, spike, f"错误数量激增 {spike:.1f} 倍"

        elif rule.condition == "critical_error":
            critical_count = sum(1 for e in entries if e.level == LogLevel.CRITICAL)
            if critical_count >= rule.threshold:
                return True, critical_count, f"发现 {critical_count} 个严重错误"

        elif rule.condition == "connection_error_streak":
            conn_errors = sum(1 for e in entries if e.level == LogLevel.ERROR and
                            any(x in e.message.lower() for x in ['connection', 'connect', '网络', '连接']))
            if conn_errors >= rule.threshold:
                return True, conn_errors, f"连续 {conn_errors} 次连接错误"

        return False, 0.0, ""


class ReportGenerator:
    """增强的报告生成器"""

    def __init__(self, output_dir: str = "."):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def generate_html_report(self, result: 'AnalysisResult', alerts: List[Alert] = None) -> str:
        """生成HTML格式报告"""
        alerts = alerts or []
        html_template = '''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>日志分析报告</title>
    <style>
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; margin: 0; padding: 20px; background: #f5f5f5; }
        .container { max-width: 1200px; margin: 0 auto; background: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        h1 { color: #333; border-bottom: 2px solid #4CAF50; padding-bottom: 10px; }
        h2 { color: #555; margin-top: 30px; }
        .summary-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin: 20px 0; }
        .summary-card { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; border-radius: 8px; }
        .summary-card.error { background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); }
        .summary-card.warning { background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%); }
        .summary-card h3 { margin: 0 0 10px 0; font-size: 14px; opacity: 0.9; }
        .summary-card .value { font-size: 32px; font-weight: bold; }
        table { width: 100%; border-collapse: collapse; margin: 20px 0; }
        th, td { padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }
        th { background: #f8f9fa; font-weight: 600; }
        tr:hover { background: #f5f5f5; }
        .badge { display: inline-block; padding: 4px 8px; border-radius: 4px; font-size: 12px; font-weight: 500; }
        .badge-critical { background: #dc3545; color: white; }
        .badge-high { background: #fd7e14; color: white; }
        .badge-medium { background: #ffc107; color: #333; }
        .badge-low { background: #28a745; color: white; }
        .alert-box { background: #fff3cd; border: 1px solid #ffc107; border-radius: 4px; padding: 15px; margin: 10px 0; }
        .alert-box.critical { background: #f8d7da; border-color: #dc3545; }
        .alert-box.high { background: #fff3cd; border-color: #fd7e14; }
        .trend-up { color: #dc3545; }
        .trend-down { color: #28a745; }
        .trend-stable { color: #6c757d; }
        code { background: #f4f4f4; padding: 2px 6px; border-radius: 3px; font-size: 13px; }
        .chart-placeholder { background: #f8f9fa; height: 200px; display: flex; align-items: center; justify-content: center; border-radius: 4px; color: #666; }
    </style>
</head>
<body>
    <div class="container">
        <h1>📊 日志分析报告</h1>
        <p>生成时间: {timestamp}</p>
        
        <div class="summary-grid">
            <div class="summary-card">
                <h3>总日志条目</h3>
                <div class="value">{total_entries}</div>
            </div>
            <div class="summary-card error">
                <h3>错误数量</h3>
                <div class="value">{error_count}</div>
            </div>
            <div class="summary-card warning">
                <h3>警告数量</h3>
                <div class="value">{warning_count}</div>
            </div>
            <div class="summary-card">
                <h3>唯一错误模式</h3>
                <div class="value">{unique_errors}</div>
            </div>
        </div>

        {alerts_section}

        <h2>🔥 高频错误模式</h2>
        <table>
            <tr><th>模式ID</th><th>名称</th><th>出现次数</th><th>严重程度</th><th>类别</th><th>建议修复</th></tr>
            {patterns_table}
        </table>

        <h2>📈 趋势分析</h2>
        <table>
            <tr><th>模式ID</th><th>趋势方向</th><th>变化率</th><th>异常检测</th><th>预测值</th></tr>
            {trends_table}
        </table>

        <h2>🎯 优先级评估</h2>
        <table>
            <tr><th>问题ID</th><th>优先级</th><th>评分</th><th>推理</th><th>推荐行动</th></tr>
            {priorities_table}
        </table>

        <h2>🔗 跨模块问题</h2>
        {cross_module_section}

        <h2>💡 修复建议</h2>
        <ul>
        {recommendations}
        </ul>
    </div>
</body>
</html>'''

        patterns_table = ""
        for p in result.patterns_found[:10]:
            severity_class = f"badge-{p.severity}" if p.severity in ['critical', 'high', 'medium', 'low'] else "badge-low"
            patterns_table += f'''<tr>
                <td><code>{p.pattern_id}</code></td>
                <td>{p.name}</td>
                <td>{p.occurrence_count}</td>
                <td><span class="badge {severity_class}">{p.severity}</span></td>
                <td>{p.category}</td>
                <td>{p.suggested_fix[:50]}...</td>
            </tr>'''

        trends_table = ""
        for t in result.trend_analysis[:10]:
            trend_class = "trend-up" if t.direction == TrendDirection.INCREASING else ("trend-down" if t.direction == TrendDirection.DECREASING else "trend-stable")
            trends_table += f'''<tr>
                <td><code>{t.pattern_id}</code></td>
                <td class="{trend_class}">{t.direction.value}</td>
                <td>{t.change_rate:.2%}</td>
                <td>{"✅ 是" if t.anomaly_detected else "❌ 否"}</td>
                <td>{t.prediction or "-"}</td>
            </tr>'''

        priorities_table = ""
        for a in result.priority_assessments[:10]:
            priority_class = f"badge-{a.priority.value.lower()}" if a.priority.value in ['P0', 'P1', 'P2', 'P3'] else "badge-low"
            priorities_table += f'''<tr>
                <td><code>{a.issue_id}</code></td>
                <td><span class="badge {priority_class}">{a.priority.value}</span></td>
                <td>{a.score:.2f}</td>
                <td>{a.reasoning}</td>
                <td>{a.recommended_action[:50]}...</td>
            </tr>'''

        alerts_section = ""
        if alerts:
            alerts_section = "<h2>🚨 告警信息</h2>"
            for alert in alerts:
                alert_class = alert.rule.severity if alert.rule.severity in ['critical', 'high'] else ""
                alerts_section += f'''<div class="alert-box {alert_class}">
                    <strong>{alert.rule.name}</strong> ({alert.rule.severity})<br>
                    {alert.message}<br>
                    <small>触发时间: {alert.triggered_at.strftime('%Y-%m-%d %H:%M:%S')}</small>
                </div>'''

        cross_module_section = ""
        if result.cross_module_issues:
            cross_module_section = "<ul>"
            for issue in result.cross_module_issues:
                cross_module_section += f'''<li>
                    <strong>{issue.issue_id}</strong>: {issue.pattern.name}<br>
                    影响模块: {', '.join(issue.affected_modules)}<br>
                    传播路径: {' → '.join(issue.propagation_path)}
                </li>'''
            cross_module_section += "</ul>"
        else:
            cross_module_section = "<p>未发现跨模块问题</p>"

        recommendations = ""
        for rec in self._generate_recommendations(result):
            recommendations += f"<li>{rec}</li>"

        return html_template.format(
            timestamp=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            total_entries=result.total_entries,
            error_count=result.error_count,
            warning_count=result.warning_count,
            unique_errors=result.unique_errors,
            alerts_section=alerts_section,
            patterns_table=patterns_table,
            trends_table=trends_table,
            priorities_table=priorities_table,
            cross_module_section=cross_module_section,
            recommendations=recommendations
        )

    def _generate_recommendations(self, result: 'AnalysisResult') -> List[str]:
        """生成修复建议"""
        recommendations = []

        critical_patterns = [p for p in result.patterns_found if p.severity == 'critical']
        if critical_patterns:
            recommendations.append(f"立即处理 {len(critical_patterns)} 个严重错误模式")

        if result.trend_analysis:
            increasing = [t for t in result.trend_analysis if t.direction == TrendDirection.INCREASING]
            if increasing:
                recommendations.append(f"关注 {len(increasing)} 个呈上升趋势的错误模式")

        if result.cross_module_issues:
            recommendations.append(f"排查 {len(result.cross_module_issues)} 个跨模块问题的根因")

        high_priority = [a for a in result.priority_assessments if a.priority in [IssuePriority.P0_CRITICAL, IssuePriority.P1_HIGH]]
        if high_priority:
            recommendations.append(f"优先解决 {len(high_priority)} 个高优先级问题")

        if result.error_count > result.total_entries * 0.1:
            recommendations.append("错误率超过10%，建议进行系统健康检查")

        return recommendations


class LogAnalyzer:
    """日志分析器主类"""

    def __init__(self, log_dir: str = ".", output_dir: str = ".", version: str = "latest"):
        self.log_dir = Path(log_dir).resolve()
        self.output_dir = Path(output_dir).resolve()
        self.version = version
        self.versioned_output_dir = self.output_dir / version
        self.versioned_output_dir.mkdir(parents=True, exist_ok=True)
        
        self.parser = LogParser()
        self.pattern_detector = ErrorPatternDetector()
        self.cross_module_tracker = CrossModuleTracker()
        self.trend_analyzer = TrendAnalyzer()
        self.priority_evaluator = PriorityEvaluator()
        self.aggregator = LogAggregator()
        self.alert_manager = AlertManager()
        self.report_generator = ReportGenerator(str(self.versioned_output_dir))
        
        self.logger = self._setup_logger()
        self._request_id_index: Dict[str, List[LogEntry]] = defaultdict(list)

    def _setup_logger(self) -> logging.Logger:
        """设置日志记录器"""
        logger = logging.getLogger('LogAnalyzer')
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        
        return logger

    def analyze_logs(
        self,
        log_files: Optional[List[str]] = None,
        time_range: Optional[Tuple[datetime, datetime]] = None,
        enable_aggregation: bool = True,
        enable_alerts: bool = True
    ) -> Tuple[AnalysisResult, List[Alert], List[AggregatedLog]]:
        """分析日志"""
        if not log_files:
            log_files = self._find_log_files()
        
        all_entries: List[LogEntry] = []
        
        for log_file in log_files:
            entries = self._parse_log_file(log_file)
            all_entries.extend(entries)
        
        if time_range:
            start_time, end_time = time_range
            all_entries = [
                e for e in all_entries
                if start_time <= e.timestamp <= end_time
            ]
        
        all_entries.sort(key=lambda x: x.timestamp)
        
        patterns = self.pattern_detector.detect_patterns(all_entries)
        
        cross_module_issues = self.cross_module_tracker.track_cross_module_issues(
            all_entries, patterns
        )
        
        trend_analysis = self.trend_analyzer.analyze_trends(all_entries, patterns)
        
        priority_assessments = []
        for i, pattern in enumerate(patterns):
            cross_issue = cross_module_issues[i] if i < len(cross_module_issues) else None
            trend = trend_analysis[i] if i < len(trend_analysis) else None
            
            assessment = self.priority_evaluator.evaluate(pattern, cross_issue, trend)
            priority_assessments.append(assessment)
        
        aggregated_logs = []
        if enable_aggregation:
            aggregated_logs = self.aggregator.aggregate(all_entries)
        
        alerts = []
        if enable_alerts:
            alerts = self.alert_manager.check_alerts(all_entries, patterns)
        
        result = AnalysisResult(
            total_entries=len(all_entries),
            error_count=sum(1 for e in all_entries if e.level == LogLevel.ERROR),
            warning_count=sum(1 for e in all_entries if e.level == LogLevel.WARNING),
            unique_errors=len(patterns),
            time_range=self._get_time_range(all_entries),
            patterns_found=patterns,
            file_stats=self._calculate_file_stats(all_entries),
            hourly_distribution=self._calculate_hourly_distribution(all_entries),
            top_errors=self._get_top_errors(patterns, 10),
            cross_module_issues=cross_module_issues,
            trend_analysis=trend_analysis,
            priority_assessments=priority_assessments
        )
        
        return result, alerts, aggregated_logs

    def _find_log_files(self) -> List[str]:
        """查找日志文件"""
        log_files = []
        
        patterns = ['*.log', '*.json', '*.txt', '*.csv', '*.gz', '*.zip']
        for pattern in patterns:
            log_files.extend(str(f) for f in self.log_dir.rglob(pattern))
        
        return log_files

    def _parse_log_file(self, file_path: str) -> List[LogEntry]:
        """解析日志文件"""
        entries = []
        
        try:
            if file_path.endswith('.gz'):
                entries = self._parse_gzipped_log(file_path)
            elif file_path.endswith('.zip'):
                entries = self._parse_zipped_log(file_path)
            elif file_path.endswith('.csv'):
                entries = self.parser.parse_csv_file(file_path)
            else:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    for line in f:
                        entry = self.parser.parse_line(line, file_path)
                        if entry:
                            entries.append(entry)
                            request_id = self.parser.extract_request_id(line)
                            if request_id:
                                self._request_id_index[request_id].append(entry)
        except Exception as e:
            self.logger.error(f"解析日志文件失败 {file_path}: {e}")
        
        return entries

    def _parse_gzipped_log(self, file_path: str) -> List[LogEntry]:
        """解析gzip压缩的日志文件"""
        entries = []
        try:
            with gzip.open(file_path, 'rt', encoding='utf-8', errors='ignore') as f:
                for line in f:
                    entry = self.parser.parse_line(line, file_path)
                    if entry:
                        entries.append(entry)
        except Exception as e:
            self.logger.error(f"解析gzip日志文件失败 {file_path}: {e}")
        return entries

    def _parse_zipped_log(self, file_path: str) -> List[LogEntry]:
        """解析zip压缩的日志文件"""
        entries = []
        try:
            with zipfile.ZipFile(file_path, 'r') as zf:
                for name in zf.namelist():
                    if name.endswith(('.log', '.txt', '.json', '.csv')):
                        with zf.open(name) as f:
                            content = f.read().decode('utf-8', errors='ignore')
                            for line in content.split('\n'):
                                entry = self.parser.parse_line(line, f"{file_path}/{name}")
                                if entry:
                                    entries.append(entry)
        except Exception as e:
            self.logger.error(f"解析zip日志文件失败 {file_path}: {e}")
        return entries

    def get_entries_by_request_id(self, request_id: str) -> List[LogEntry]:
        """根据请求ID获取相关日志条目"""
        return self._request_id_index.get(request_id, [])

    def _get_time_range(self, entries: List[LogEntry]) -> Tuple[datetime, datetime]:
        """获取时间范围"""
        if not entries:
            return (datetime.now(), datetime.now())
        
        timestamps = [e.timestamp for e in entries]
        return (min(timestamps), max(timestamps))

    def _calculate_file_stats(self, entries: List[LogEntry]) -> Dict[str, Dict[str, int]]:
        """计算文件统计"""
        stats = defaultdict(lambda: defaultdict(int))
        
        for entry in entries:
            stats[entry.source][entry.level.value] += 1
        
        return dict(stats)

    def _calculate_hourly_distribution(self, entries: List[LogEntry]) -> Dict[str, int]:
        """计算小时分布"""
        distribution = defaultdict(int)
        
        for entry in entries:
            hour_key = entry.timestamp.strftime('%Y-%m-%d %H:00')
            distribution[hour_key] += 1
        
        return dict(sorted(distribution.items()))

    def _get_top_errors(self, patterns: List[ErrorPattern], limit: int) -> List[Dict[str, Any]]:
        """获取顶部错误"""
        sorted_patterns = sorted(patterns, key=lambda x: x.occurrence_count, reverse=True)
        
        return [
            {
                "pattern_id": p.pattern_id,
                "name": p.name,
                "count": p.occurrence_count,
                "severity": p.severity,
                "category": p.category
            }
            for p in sorted_patterns[:limit]
        ]

    def generate_report(
        self,
        result: AnalysisResult,
        output_format: str = "markdown",
        alerts: List[Alert] = None,
        aggregated_logs: List[AggregatedLog] = None
    ) -> str:
        """生成分析报告"""
        if output_format == "json":
            return self._generate_json_report(result, alerts, aggregated_logs)
        elif output_format == "html":
            return self.report_generator.generate_html_report(result, alerts)
        return self._generate_markdown_report(result, alerts, aggregated_logs)

    def _generate_markdown_report(
        self,
        result: AnalysisResult,
        alerts: List[Alert] = None,
        aggregated_logs: List[AggregatedLog] = None
    ) -> str:
        """生成Markdown报告"""
        alerts = alerts or []
        aggregated_logs = aggregated_logs or []
        
        lines = [
            "# 日志分析报告",
            f"\n生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"\n## 概览",
            f"- 总日志条目: {result.total_entries}",
            f"- 错误数量: {result.error_count}",
            f"- 警告数量: {result.warning_count}",
            f"- 唯一错误模式: {result.unique_errors}",
            f"- 时间范围: {result.time_range[0].strftime('%Y-%m-%d %H:%M')} - {result.time_range[1].strftime('%Y-%m-%d %H:%M')}",
        ]
        
        if alerts:
            lines.extend([
                f"\n## 🚨 告警信息 ({len(alerts)})",
            ])
            for alert in alerts:
                lines.extend([
                    f"\n### {alert.alert_id}: {alert.rule.name}",
                    f"- **严重程度**: {alert.rule.severity}",
                    f"- **消息**: {alert.message}",
                    f"- **触发时间**: {alert.triggered_at.strftime('%Y-%m-%d %H:%M:%S')}",
                ])
        
        if aggregated_logs:
            lines.extend([
                f"\n## 📊 日志聚合分析 (Top 10)",
            ])
            for agg in aggregated_logs[:10]:
                lines.extend([
                    f"\n### 模式 {agg.hash_key}",
                    f"- **出现次数**: {agg.count}",
                    f"- **签名**: {agg.pattern_signature}",
                    f"- **首次出现**: {agg.first_seen.strftime('%Y-%m-%d %H:%M:%S')}",
                    f"- **最后出现**: {agg.last_seen.strftime('%Y-%m-%d %H:%M:%S')}",
                    f"- **平均间隔**: {agg.avg_interval:.2f}秒",
                ])
        
        if result.cross_module_issues:
            lines.extend([
                f"\n## 跨模块问题 ({len(result.cross_module_issues)})",
            ])
            for issue in result.cross_module_issues:
                lines.extend([
                    f"\n### {issue.issue_id}",
                    f"- **模式**: {issue.pattern.name}",
                    f"- **影响模块**: {', '.join(issue.affected_modules)}",
                    f"- **传播路径**: {' -> '.join(issue.propagation_path)}",
                    f"- **根模块**: {issue.root_module}",
                    f"- **优先级**: {issue.priority.value}",
                ])
        
        if result.trend_analysis:
            lines.extend([
                f"\n## 趋势分析",
            ])
            for trend in result.trend_analysis:
                lines.extend([
                    f"\n### {trend.pattern_id}",
                    f"- **方向**: {trend.direction.value}",
                    f"- **变化率**: {trend.change_rate:.2%}",
                    f"- **异常检测**: {'是' if trend.anomaly_detected else '否'}",
                ])
                if trend.prediction:
                    lines.append(f"- **预测值**: {trend.prediction}")
        
        if result.priority_assessments:
            lines.extend([
                f"\n## 优先级评估",
            ])
            for assessment in result.priority_assessments:
                lines.extend([
                    f"\n### {assessment.issue_id}",
                    f"- **优先级**: {assessment.priority.value}",
                    f"- **评分**: {assessment.score:.2f}",
                    f"- **推理**: {assessment.reasoning}",
                    f"- **推荐行动**: {assessment.recommended_action}",
                ])
        
        if result.patterns_found:
            lines.extend([
                f"\n## 错误模式详情",
            ])
            for pattern in result.patterns_found[:10]:
                lines.extend([
                    f"\n### {pattern.pattern_id}: {pattern.name}",
                    f"- **描述**: {pattern.description}",
                    f"- **严重程度**: {pattern.severity}",
                    f"- **类别**: {pattern.category}",
                    f"- **出现次数**: {pattern.occurrence_count}",
                    f"- **影响文件数**: {len(pattern.affected_files)}",
                    f"- **建议修复**: {pattern.suggested_fix}",
                ])
        
        return '\n'.join(lines)

    def _generate_json_report(
        self,
        result: AnalysisResult,
        alerts: List[Alert] = None,
        aggregated_logs: List[AggregatedLog] = None
    ) -> str:
        """生成JSON报告"""
        alerts = alerts or []
        aggregated_logs = aggregated_logs or []
        
        report = {
            "timestamp": datetime.now().isoformat(),
            "summary": {
                "total_entries": result.total_entries,
                "error_count": result.error_count,
                "warning_count": result.warning_count,
                "unique_errors": result.unique_errors,
                "time_range": [
                    result.time_range[0].isoformat(),
                    result.time_range[1].isoformat()
                ]
            },
            "patterns": [
                {
                    "id": p.pattern_id,
                    "name": p.name,
                    "severity": p.severity,
                    "category": p.category,
                    "count": p.occurrence_count,
                    "affected_files": list(p.affected_files)
                }
                for p in result.patterns_found
            ],
            "cross_module_issues": [
                {
                    "id": i.issue_id,
                    "pattern": i.pattern.name,
                    "affected_modules": list(i.affected_modules),
                    "propagation_path": i.propagation_path,
                    "priority": i.priority.value
                }
                for i in result.cross_module_issues
            ],
            "trends": [
                {
                    "pattern_id": t.pattern_id,
                    "direction": t.direction.value,
                    "change_rate": t.change_rate,
                    "anomaly": t.anomaly_detected
                }
                for t in result.trend_analysis
            ],
            "priorities": [
                {
                    "issue_id": a.issue_id,
                    "priority": a.priority.value,
                    "score": a.score,
                    "reasoning": a.reasoning
                }
                for a in result.priority_assessments
            ],
            "alerts": [
                {
                    "alert_id": a.alert_id,
                    "rule_name": a.rule.name,
                    "severity": a.rule.severity,
                    "message": a.message,
                    "triggered_at": a.triggered_at.isoformat(),
                    "value": a.value
                }
                for a in alerts
            ],
            "aggregated_patterns": [
                {
                    "hash_key": agg.hash_key,
                    "signature": agg.pattern_signature,
                    "count": agg.count,
                    "first_seen": agg.first_seen.isoformat(),
                    "last_seen": agg.last_seen.isoformat(),
                    "avg_interval": agg.avg_interval,
                    "sources": list(agg.sources)
                }
                for agg in aggregated_logs[:20]
            ]
        }
        
        return json.dumps(report, indent=2, ensure_ascii=False)

    def save_report(
        self,
        result: AnalysisResult,
        output_path: Optional[str] = None,
        output_format: str = "markdown",
        alerts: List[Alert] = None,
        aggregated_logs: List[AggregatedLog] = None
    ) -> str:
        """保存报告"""
        if not output_path:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            ext_map = {'json': 'json', 'html': 'html', 'markdown': 'md'}
            ext = ext_map.get(output_format, 'md')
            output_path = str(self.output_dir / f"analysis_report_{timestamp}.{ext}")
        
        report = self.generate_report(result, output_format, alerts, aggregated_logs)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(report)
        
        return output_path


def main():
    parser = argparse.ArgumentParser(
        description='日志分析脚本 - 分析日志，识别错误模式，追踪跨模块问题'
    )
    parser.add_argument(
        '--log-dir',
        default='.',
        help='日志目录路径'
    )
    parser.add_argument(
        '--log-file',
        action='append',
        help='指定日志文件（可多次使用）'
    )
    parser.add_argument(
        '--output-dir',
        default='docs/reports',
        help='输出目录'
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
        choices=['markdown', 'json', 'html'],
        default='markdown',
        help='输出格式'
    )
    parser.add_argument(
        '--start-time',
        help='开始时间 (YYYY-MM-DD HH:MM:SS)'
    )
    parser.add_argument(
        '--end-time',
        help='结束时间 (YYYY-MM-DD HH:MM:SS)'
    )
    parser.add_argument(
        '--no-aggregation',
        action='store_true',
        help='禁用日志聚合分析'
    )
    parser.add_argument(
        '--no-alerts',
        action='store_true',
        help='禁用告警检测'
    )
    parser.add_argument(
        '--request-id',
        help='按请求ID筛选相关日志'
    )

    args = parser.parse_args()

    analyzer = LogAnalyzer(args.log_dir, args.output_dir, args.version)

    time_range = None
    if args.start_time or args.end_time:
        start = datetime.strptime(args.start_time, '%Y-%m-%d %H:%M:%S') if args.start_time else datetime.min
        end = datetime.strptime(args.end_time, '%Y-%m-%d %H:%M:%S') if args.end_time else datetime.now()
        time_range = (start, end)

    print("正在分析日志...")
    result, alerts, aggregated_logs = analyzer.analyze_logs(
        args.log_file, 
        time_range,
        enable_aggregation=not args.no_aggregation,
        enable_alerts=not args.no_alerts
    )

    if args.request_id:
        request_entries = analyzer.get_entries_by_request_id(args.request_id)
        print(f"\n请求ID {args.request_id} 相关日志条目: {len(request_entries)}")

    output_path = analyzer.save_report(result, args.output, args.format, alerts, aggregated_logs)

    print(f"\n分析完成!")
    print(f"总日志条目: {result.total_entries}")
    print(f"错误数量: {result.error_count}")
    print(f"警告数量: {result.warning_count}")
    print(f"唯一错误模式: {result.unique_errors}")
    print(f"跨模块问题: {len(result.cross_module_issues)}")
    print(f"告警数量: {len(alerts)}")
    print(f"聚合模式: {len(aggregated_logs)}")
    print(f"\n报告已保存到: {output_path}")

    return 0


if __name__ == '__main__':
    exit(main())