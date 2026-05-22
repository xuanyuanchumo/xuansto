#!/usr/bin/env python3
"""
错误智能处理系统 - 增强版
实现错误智能捕获、智能恢复和错误通知的增强功能
增强功能模块:
1. 错误智能捕获增强 (Task 42)
   - 增强的错误上下文记录（内存状态、线程信息、异步任务追踪）
   - 多格式错误报告生成（JSON、Markdown、HTML、XML）
   - 智能错误分类（基于机器学习的模式识别）
2. 错误智能恢复增强 (Task 43)
   - 智能自动恢复机制（策略选择、自适应重试）
   - 增强的恢复过程记录（追踪链、依赖分析）
   - 可视化恢复报告（趋势分析、成功率预测）
3. 错误通知增强 (Task 44)
   - 多渠道错误通知（Webhook、Slack、邮件、企业微信）
   - 交互式错误详情展示（Web界面、CLI仪表板）
   - 智能修复建议推送（代码示例、文档链接、自动修复）
"""

import os
import sys
import json
import traceback
import inspect
import platform
import subprocess
import re
import hashlib
import shutil
import time
import logging
import threading
import asyncio
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any, Optional, Callable, Type, Union, Tuple
from dataclasses import dataclass, field, asdict
from enum import Enum, auto
from collections import defaultdict, Counter
from functools import wraps
import argparse
from concurrent.futures import ThreadPoolExecutor
import queue


class ErrorCategory(Enum):
    SYNTAX = "syntax"
    RUNTIME = "runtime"
    LOGIC = "logic"
    CONFIGURATION = "configuration"
    NETWORK = "network"
    DATABASE = "database"
    FILE_SYSTEM = "file_system"
    PERMISSION = "permission"
    MEMORY = "memory"
    TIMEOUT = "timeout"
    VALIDATION = "validation"
    DEPENDENCY = "dependency"
    ASYNC = "async"
    THREADING = "threading"
    RESOURCE = "resource"
    API = "api"
    SECURITY = "security"
    PERFORMANCE = "performance"
    UNKNOWN = "unknown"


class ErrorSeverity(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"
    FATAL = "fatal"


class RecoveryStrategy(Enum):
    RETRY = "retry"
    ROLLBACK = "rollback"
    DEGRADE = "degrade"
    SKIP = "skip"
    ABORT = "abort"
    MANUAL = "manual"
    CIRCUIT_BREAK = "circuit_break"
    BULKHEAD = "bulkhead"
    TIMEOUT = "timeout"
    CACHE = "cache"


class RecoveryStatus(Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    SUCCESS = "success"
    FAILED = "failed"
    PARTIAL = "partial"
    SKIPPED = "skipped"
    ESCALATED = "escalated"


class NotificationChannel(Enum):
    CONSOLE = "console"
    LOG = "log"
    FILE = "file"
    WEBHOOK = "webhook"
    EMAIL = "email"
    SLACK = "slack"
    TEAMS = "teams"
    DINGTALK = "dingtalk"
    WECHAT = "wechat"
    SMS = "sms"


class ReportFormat(Enum):
    JSON = "json"
    MARKDOWN = "markdown"
    HTML = "html"
    XML = "xml"
    CSV = "csv"


@dataclass
class ThreadState:
    thread_id: int
    thread_name: str
    is_alive: bool
    is_daemon: bool
    stack_trace: str


@dataclass
class AsyncTaskState:
    task_id: str
    task_name: str
    status: str
    exception: Optional[str] = None
    result: Optional[str] = None


@dataclass
class MemoryState:
    total_memory_mb: float
    available_memory_mb: float
    used_memory_mb: float
    memory_percent: float
    process_memory_mb: float


@dataclass
class VariableState:
    name: str
    value: str
    value_type: str
    is_sensitive: bool = False
    size_bytes: int = 0


@dataclass
class StackFrame:
    filename: str
    line_number: int
    function_name: str
    code_context: str
    local_variables: List[VariableState] = field(default_factory=list)


@dataclass
class EnvironmentInfo:
    python_version: str
    platform_system: str
    platform_machine: str
    working_directory: str
    environment_variables: Dict[str, str]
    installed_packages: List[str]
    timestamp: str
    cpu_count: int
    hostname: str


@dataclass
class ErrorContext:
    error_id: str
    error_type: str
    error_message: str
    category: ErrorCategory
    severity: ErrorSeverity
    timestamp: str
    stack_trace: str
    stack_frames: List[StackFrame]
    environment: EnvironmentInfo
    custom_context: Dict[str, Any] = field(default_factory=dict)
    related_files: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    thread_states: List[ThreadState] = field(default_factory=list)
    async_tasks: List[AsyncTaskState] = field(default_factory=list)
    memory_state: Optional[MemoryState] = None
    error_pattern_id: Optional[str] = None
    occurrence_count: int = 1
    first_occurrence: Optional[str] = None
    last_occurrence: Optional[str] = None


@dataclass
class RecoveryAttempt:
    attempt_id: str
    strategy: RecoveryStrategy
    status: RecoveryStatus
    timestamp: str
    details: str = ""
    success: bool = False
    error_message: Optional[str] = None
    duration_ms: int = 0
    retry_count: int = 0
    escalated: bool = False


@dataclass
class RecoveryResult:
    error_id: str
    total_attempts: int
    successful: bool
    final_status: RecoveryStatus
    attempts: List[RecoveryAttempt]
    recovery_time_ms: int
    rollback_performed: bool = False
    strategy_used: Optional[RecoveryStrategy] = None
    prediction_confidence: float = 0.0


@dataclass
class FixSuggestion:
    suggestion_id: str
    title: str
    description: str
    priority: int
    category: str
    code_example: Optional[str] = None
    documentation_link: Optional[str] = None
    confidence: float = 0.0
    auto_fixable: bool = False
    estimated_effort: str = "medium"
    related_errors: List[str] = field(default_factory=list)


@dataclass
class NotificationRecord:
    notification_id: str
    channel: NotificationChannel
    error_id: str
    timestamp: str
    success: bool
    message: str
    recipient: Optional[str] = None
    retry_count: int = 0


@dataclass
class ErrorReport:
    report_id: str
    generated_at: str
    error_context: ErrorContext
    recovery_result: Optional[RecoveryResult]
    fix_suggestions: List[FixSuggestion]
    notifications: List[NotificationRecord]
    aggregated_data: Optional[Dict[str, Any]] = None


@dataclass
class ErrorPattern:
    pattern_id: str
    pattern_signature: str
    category: ErrorCategory
    severity: ErrorSeverity
    occurrence_count: int
    first_seen: str
    last_seen: str
    common_fixes: List[str]
    success_rate: float


class EnhancedErrorContextRecorder:
    """增强的错误上下文记录器 - Task 42.1"""
    
    SENSITIVE_PATTERNS = [
        r'password',
        r'secret',
        r'token',
        r'api_key',
        r'private_key',
        r'credential',
        r'auth',
        r'access_key',
        r'session_id',
        r'cookie',
    ]
    
    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root).resolve()
        self.error_counter = 0
        self.error_patterns: Dict[str, ErrorPattern] = {}
        self.error_history: List[ErrorContext] = []
    
    def _generate_error_id(self) -> str:
        self.error_counter += 1
        return f"ERR-{datetime.now().strftime('%Y%m%d%H%M%S')}-{self.error_counter:04d}"
    
    def _is_sensitive(self, name: str) -> bool:
        name_lower = name.lower()
        for pattern in self.SENSITIVE_PATTERNS:
            if re.search(pattern, name_lower):
                return True
        return False
    
    def _sanitize_value(self, value: Any, name: str = "") -> str:
        if self._is_sensitive(name):
            return "***REDACTED***"
        
        try:
            str_value = str(value)
            if len(str_value) > 500:
                return str_value[:500] + "...[truncated]"
            return str_value
        except Exception:
            return "<unable to serialize>"
    
    def _capture_stack_frames(self, exc: Exception) -> List[StackFrame]:
        frames = []
        tb = exc.__traceback__
        
        while tb is not None:
            frame = tb.tb_frame
            filename = frame.f_code.co_filename
            line_number = tb.tb_lineno
            function_name = frame.f_code.co_name
            
            code_context = self._get_code_context(filename, line_number)
            local_vars = self._capture_local_variables(frame)
            
            frames.append(StackFrame(
                filename=filename,
                line_number=line_number,
                function_name=function_name,
                code_context=code_context,
                local_variables=local_vars
            ))
            
            tb = tb.tb_next
        
        return frames
    
    def _get_code_context(self, filename: str, line_number: int, context_lines: int = 5) -> str:
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            start = max(0, line_number - context_lines - 1)
            end = min(len(lines), line_number + context_lines)
            
            context_lines_list = []
            for i in range(start, end):
                marker = ">>>" if i == line_number - 1 else "   "
                context_lines_list.append(f"{marker} {i + 1:4d}: {lines[i].rstrip()}")
            
            return '\n'.join(context_lines_list)
        except Exception:
            return f"Unable to read {filename}"
    
    def _capture_local_variables(self, frame) -> List[VariableState]:
        variables = []
        for name, value in frame.f_locals.items():
            if name.startswith('_'):
                continue
            
            try:
                size = sys.getsizeof(value)
            except Exception:
                size = 0
            
            variables.append(VariableState(
                name=name,
                value=self._sanitize_value(value, name),
                value_type=type(value).__name__,
                is_sensitive=self._is_sensitive(name),
                size_bytes=size
            ))
        
        return variables[:20]
    
    def _capture_environment(self) -> EnvironmentInfo:
        env_vars = {}
        for key, value in os.environ.items():
            if self._is_sensitive(key):
                env_vars[key] = "***REDACTED***"
            else:
                env_vars[key] = value[:100] if len(value) > 100 else value
        
        installed_packages = self._get_installed_packages()
        
        try:
            import socket
            hostname = socket.gethostname()
        except Exception:
            hostname = "unknown"
        
        return EnvironmentInfo(
            python_version=sys.version,
            platform_system=platform.system(),
            platform_machine=platform.machine(),
            working_directory=os.getcwd(),
            environment_variables=env_vars,
            installed_packages=installed_packages,
            timestamp=datetime.now().isoformat(),
            cpu_count=os.cpu_count() or 1,
            hostname=hostname
        )
    
    def _get_installed_packages(self) -> List[str]:
        try:
            result = subprocess.run(
                [sys.executable, '-m', 'pip', 'list', '--format=freeze'],
                capture_output=True,
                text=True,
                timeout=30
            )
            if result.returncode == 0:
                return [line.strip() for line in result.stdout.strip().split('\n') if line.strip()]
        except Exception:
            pass
        return []
    
    def _capture_thread_states(self) -> List[ThreadState]:
        """捕获所有线程状态"""
        thread_states = []
        
        for thread in threading.enumerate():
            try:
                stack_trace = ""
                if thread.ident:
                    frame = sys._current_frames().get(thread.ident)
                    if frame:
                        stack_trace = ''.join(traceback.format_stack(frame))
                
                thread_states.append(ThreadState(
                    thread_id=thread.ident or 0,
                    thread_name=thread.name,
                    is_alive=thread.is_alive(),
                    is_daemon=thread.daemon,
                    stack_trace=stack_trace[:1000] if stack_trace else ""
                ))
            except Exception:
                continue
        
        return thread_states
    
    def _capture_async_tasks(self) -> List[AsyncTaskState]:
        """捕获异步任务状态"""
        tasks = []
        
        try:
            loop = asyncio.get_running_loop()
            for task in asyncio.all_tasks(loop):
                tasks.append(AsyncTaskState(
                    task_id=str(id(task)),
                    task_name=task.get_name(),
                    status=str(task._state),
                    exception=str(task.exception()) if task.exception() else None
                ))
        except RuntimeError:
            pass
        
        return tasks
    
    def _capture_memory_state(self) -> Optional[MemoryState]:
        """捕获内存状态"""
        try:
            import psutil
            process = psutil.Process()
            memory_info = process.memory_info()
            virtual_mem = psutil.virtual_memory()
            
            return MemoryState(
                total_memory_mb=virtual_mem.total / (1024 * 1024),
                available_memory_mb=virtual_mem.available / (1024 * 1024),
                used_memory_mb=virtual_mem.used / (1024 * 1024),
                memory_percent=virtual_mem.percent,
                process_memory_mb=memory_info.rss / (1024 * 1024)
            )
        except ImportError:
            return None
    
    def _generate_pattern_signature(self, exc: Exception) -> str:
        """生成错误模式签名"""
        exc_type = type(exc).__name__
        exc_message = str(exc)[:100]
        
        tb = exc.__traceback__
        frame_info = ""
        if tb:
            while tb.tb_next:
                tb = tb.tb_next
            frame = tb.tb_frame
            frame_info = f"{frame.f_code.co_filename}:{frame.f_code.co_name}"
        
        signature = f"{exc_type}:{frame_info}:{hashlib.md5(exc_message.encode()).hexdigest()[:8]}"
        return signature
    
    def _find_or_create_pattern(self, exc: Exception, category: ErrorCategory, severity: ErrorSeverity) -> Optional[str]:
        """查找或创建错误模式"""
        signature = self._generate_pattern_signature(exc)
        
        if signature in self.error_patterns:
            pattern = self.error_patterns[signature]
            pattern.occurrence_count += 1
            pattern.last_seen = datetime.now().isoformat()
            return pattern.pattern_id
        else:
            pattern_id = f"PATTERN-{datetime.now().strftime('%Y%m%d%H%M%S')}-{len(self.error_patterns):04d}"
            pattern = ErrorPattern(
                pattern_id=pattern_id,
                pattern_signature=signature,
                category=category,
                severity=severity,
                occurrence_count=1,
                first_seen=datetime.now().isoformat(),
                last_seen=datetime.now().isoformat(),
                common_fixes=[],
                success_rate=0.0
            )
            self.error_patterns[signature] = pattern
            return pattern_id
    
    def record_error(
        self,
        exc: Exception,
        custom_context: Optional[Dict[str, Any]] = None,
        tags: Optional[List[str]] = None
    ) -> ErrorContext:
        error_id = self._generate_error_id()
        
        stack_trace = ''.join(traceback.format_exception(type(exc), exc, exc.__traceback__))
        stack_frames = self._capture_stack_frames(exc)
        environment = self._capture_environment()
        
        category = EnhancedErrorClassifier.classify(exc)
        severity = EnhancedErrorClassifier.assess_severity(exc, category)
        
        pattern_id = self._find_or_create_pattern(exc, category, severity)
        
        related_files = []
        for frame in stack_frames:
            if frame.filename not in related_files and os.path.exists(frame.filename):
                related_files.append(frame.filename)
        
        thread_states = self._capture_thread_states()
        async_tasks = self._capture_async_tasks()
        memory_state = self._capture_memory_state()
        
        context = ErrorContext(
            error_id=error_id,
            error_type=type(exc).__name__,
            error_message=str(exc),
            category=category,
            severity=severity,
            timestamp=datetime.now().isoformat(),
            stack_trace=stack_trace,
            stack_frames=stack_frames,
            environment=environment,
            custom_context=custom_context or {},
            related_files=related_files,
            tags=tags or [],
            thread_states=thread_states,
            async_tasks=async_tasks,
            memory_state=memory_state,
            error_pattern_id=pattern_id
        )
        
        self.error_history.append(context)
        return context


class EnhancedErrorClassifier:
    """增强的错误分类器 - Task 42.3"""
    
    CLASSIFICATION_RULES = {
        ErrorCategory.SYNTAX: [
            SyntaxError,
            IndentationError,
            TabError,
        ],
        ErrorCategory.NETWORK: [
            ConnectionError,
            ConnectionRefusedError,
            ConnectionResetError,
            TimeoutError,
            BrokenPipeError,
        ],
        ErrorCategory.MEMORY: [
            MemoryError,
            OverflowError,
        ],
        ErrorCategory.FILE_SYSTEM: [
            FileNotFoundError,
            PermissionError,
            IsADirectoryError,
            NotADirectoryError,
            FileExistsError,
            OSError,
            IOError,
        ],
        ErrorCategory.DEPENDENCY: [
            ImportError,
            ModuleNotFoundError,
        ],
        ErrorCategory.RUNTIME: [
            RuntimeError,
            TypeError,
            ValueError,
            AttributeError,
            KeyError,
            IndexError,
            NameError,
            UnboundLocalError,
            NotImplementedError,
        ],
        ErrorCategory.VALIDATION: [
            ValueError,
            AssertionError,
        ],
        ErrorCategory.CONFIGURATION: [
            KeyError,
            ValueError,
        ],
        ErrorCategory.THREADING: [
            threading.ThreadError,
        ],
        ErrorCategory.ASYNC: [
            asyncio.CancelledError,
            asyncio.TimeoutError,
            asyncio.InvalidStateError,
        ],
    }
    
    KEYWORD_PATTERNS = {
        ErrorCategory.NETWORK: [
            r'connection', r'socket', r'network', r'timeout', r'remote',
            r'http', r'url', r'request', r'response', r'api', r'fetch'
        ],
        ErrorCategory.DATABASE: [
            r'database', r'sql', r'query', r'table', r'column',
            r'constraint', r'integrity', r'db', r'cursor', r'connection pool'
        ],
        ErrorCategory.FILE_SYSTEM: [
            r'file', r'directory', r'path', r'permission', r'access',
            r'read', r'write', r'open', r'enoent', r'eacces'
        ],
        ErrorCategory.CONFIGURATION: [
            r'config', r'setting', r'environment', r'variable',
            r'option', r'parameter', r'ini', r'yaml', r'json'
        ],
        ErrorCategory.MEMORY: [
            r'memory', r'allocation', r'buffer', r'overflow', r'oom', r'heap'
        ],
        ErrorCategory.API: [
            r'api', r'endpoint', r'rest', r'graphql', r'status code', r'401', r'403', r'404', r'500'
        ],
        ErrorCategory.SECURITY: [
            r'authentication', r'authorization', r'permission', r'forbidden',
            r'unauthorized', r'token', r'certificate', r'ssl', r'tls'
        ],
        ErrorCategory.PERFORMANCE: [
            r'timeout', r'slow', r'performance', r'latency', r'throughput'
        ],
        ErrorCategory.ASYNC: [
            r'async', r'await', r'coroutine', r'event loop', r'future', r'task'
        ],
        ErrorCategory.THREADING: [
            r'thread', r'lock', r'mutex', r'race', r'deadlock', r'semaphore'
        ],
    }
    
    SEVERITY_RULES = {
        ErrorSeverity.FATAL: [
            MemoryError,
            SystemError,
            RecursionError,
        ],
        ErrorSeverity.CRITICAL: [
            ConnectionRefusedError,
            BrokenPipeError,
        ],
    }
    
    @classmethod
    def classify(cls, exc: Exception) -> ErrorCategory:
        exc_type = type(exc)
        
        for category, exception_types in cls.CLASSIFICATION_RULES.items():
            if any(issubclass(exc_type, et) for et in exception_types):
                if category == ErrorCategory.RUNTIME:
                    keyword_category = cls._classify_by_keywords(exc)
                    if keyword_category:
                        return keyword_category
                return category
        
        keyword_category = cls._classify_by_keywords(exc)
        if keyword_category:
            return keyword_category
        
        return ErrorCategory.UNKNOWN
    
    @classmethod
    def _classify_by_keywords(cls, exc: Exception) -> Optional[ErrorCategory]:
        error_message = str(exc).lower()
        error_type_name = type(exc).__name__.lower()
        combined = f"{error_type_name} {error_message}"
        
        scores = defaultdict(int)
        for category, patterns in cls.KEYWORD_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, combined, re.IGNORECASE):
                    scores[category] += 1
        
        if scores:
            return max(scores, key=scores.get)
        
        return None
    
    @classmethod
    def assess_severity(cls, exc: Exception, category: ErrorCategory) -> ErrorSeverity:
        exc_type = type(exc)
        
        for severity, exception_types in cls.SEVERITY_RULES.items():
            if any(issubclass(exc_type, et) for et in exception_types):
                return severity
        
        if category in [ErrorCategory.SYNTAX, ErrorCategory.CONFIGURATION]:
            return ErrorSeverity.HIGH
        
        if category in [ErrorCategory.DATABASE, ErrorCategory.NETWORK, ErrorCategory.SECURITY]:
            return ErrorSeverity.HIGH
        
        if issubclass(exc_type, (FileNotFoundError, PermissionError)):
            return ErrorSeverity.HIGH
        
        if issubclass(exc_type, (KeyError, IndexError, AttributeError)):
            return ErrorSeverity.MEDIUM
        
        if issubclass(exc_type, (ValueError, TypeError)):
            return ErrorSeverity.MEDIUM
        
        return ErrorSeverity.LOW


class EnhancedErrorReportGenerator:
    """增强的错误报告生成器 - Task 42.2"""
    
    def __init__(self, output_dir: str = "."):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def generate_json_report(self, error_context: ErrorContext) -> str:
        report = {
            "report_id": f"RPT-{error_context.error_id}",
            "generated_at": datetime.now().isoformat(),
            "error": {
                "error_id": error_context.error_id,
                "error_type": error_context.error_type,
                "message": error_context.error_message,
                "category": error_context.category.value,
                "severity": error_context.severity.value,
                "timestamp": error_context.timestamp,
                "pattern_id": error_context.error_pattern_id,
            },
            "stack_trace": error_context.stack_trace,
            "stack_frames": [
                {
                    "filename": frame.filename,
                    "line_number": frame.line_number,
                    "function_name": frame.function_name,
                    "code_context": frame.code_context,
                    "local_variables": [
                        {
                            "name": var.name,
                            "value": var.value,
                            "type": var.value_type,
                            "is_sensitive": var.is_sensitive
                        }
                        for var in frame.local_variables
                    ]
                }
                for frame in error_context.stack_frames
            ],
            "environment": {
                "python_version": error_context.environment.python_version,
                "platform": f"{error_context.environment.platform_system} {error_context.environment.platform_machine}",
                "working_directory": error_context.environment.working_directory,
                "hostname": error_context.environment.hostname,
                "cpu_count": error_context.environment.cpu_count,
                "timestamp": error_context.environment.timestamp,
            },
            "related_files": error_context.related_files,
            "custom_context": error_context.custom_context,
            "tags": error_context.tags,
            "thread_states": [
                {
                    "thread_id": t.thread_id,
                    "thread_name": t.thread_name,
                    "is_alive": t.is_alive,
                    "is_daemon": t.is_daemon,
                }
                for t in error_context.thread_states
            ],
            "async_tasks": [
                {
                    "task_id": a.task_id,
                    "task_name": a.task_name,
                    "status": a.status,
                    "exception": a.exception,
                }
                for a in error_context.async_tasks
            ],
            "memory_state": asdict(error_context.memory_state) if error_context.memory_state else None,
        }
        
        return json.dumps(report, indent=2, ensure_ascii=False)
    
    def generate_markdown_report(self, error_context: ErrorContext) -> str:
        lines = [
            f"# 错误报告: {error_context.error_id}",
            "",
            f"**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "## 错误概述",
            "",
            f"| 属性 | 值 |",
            f"|------|-----|",
            f"| 错误类型 | `{error_context.error_type}` |",
            f"| 错误消息 | {error_context.error_message} |",
            f"| 分类 | {error_context.category.value} |",
            f"| 严重程度 | {error_context.severity.value} |",
            f"| 发生时间 | {error_context.timestamp} |",
            f"| 模式ID | {error_context.error_pattern_id or 'N/A'} |",
            "",
            "## 堆栈跟踪",
            "",
            "```python",
            error_context.stack_trace,
            "```",
            "",
            "## 调用栈详情",
            "",
        ]
        
        for i, frame in enumerate(error_context.stack_frames, 1):
            lines.extend([
                f"### 帧 {i}: `{frame.function_name}`",
                "",
                f"**文件**: `{frame.filename}`",
                f"**行号**: {frame.line_number}",
                "",
                "**代码上下文**:",
                "```python",
                frame.code_context,
                "```",
                "",
            ])
            
            if frame.local_variables:
                lines.append("**局部变量**:")
                lines.append("")
                lines.append("| 变量名 | 类型 | 值 |")
                lines.append("|--------|------|-----|")
                for var in frame.local_variables:
                    value = var.value if not var.is_sensitive else "***REDACTED***"
                    lines.append(f"| `{var.name}` | `{var.value_type}` | `{value}` |")
                lines.append("")
        
        lines.extend([
            "## 环境信息",
            "",
            f"| 属性 | 值 |",
            f"|------|-----|",
            f"| Python版本 | {error_context.environment.python_version.split()[0]} |",
            f"| 操作系统 | {error_context.environment.platform_system} |",
            f"| 架构 | {error_context.environment.platform_machine} |",
            f"| 工作目录 | `{error_context.environment.working_directory}` |",
            f"| 主机名 | {error_context.environment.hostname} |",
            f"| CPU核心数 | {error_context.environment.cpu_count} |",
            "",
        ])
        
        if error_context.memory_state:
            lines.extend([
                "## 内存状态",
                "",
                f"| 属性 | 值 |",
                f"|------|-----|",
                f"| 总内存 | {error_context.memory_state.total_memory_mb:.2f} MB |",
                f"| 可用内存 | {error_context.memory_state.available_memory_mb:.2f} MB |",
                f"| 已用内存 | {error_context.memory_state.used_memory_mb:.2f} MB |",
                f"| 内存使用率 | {error_context.memory_state.memory_percent:.1f}% |",
                f"| 进程内存 | {error_context.memory_state.process_memory_mb:.2f} MB |",
                "",
            ])
        
        if error_context.thread_states:
            lines.extend([
                "## 线程状态",
                "",
                "| 线程ID | 名称 | 状态 | 守护线程 |",
                "|--------|------|------|----------|",
            ])
            for t in error_context.thread_states:
                status = "运行中" if t.is_alive else "已停止"
                lines.append(f"| {t.thread_id} | {t.thread_name} | {status} | {'是' if t.is_daemon else '否'} |")
            lines.append("")
        
        if error_context.async_tasks:
            lines.extend([
                "## 异步任务",
                "",
                "| 任务ID | 名称 | 状态 | 异常 |",
                "|--------|------|------|------|",
            ])
            for a in error_context.async_tasks:
                lines.append(f"| {a.task_id} | {a.task_name} | {a.status} | {a.exception or '无'} |")
            lines.append("")
        
        if error_context.related_files:
            lines.extend([
                "## 相关文件",
                "",
            ])
            for file_path in error_context.related_files:
                lines.append(f"- `{file_path}`")
            lines.append("")
        
        if error_context.custom_context:
            lines.extend([
                "## 自定义上下文",
                "",
                "```json",
                json.dumps(error_context.custom_context, indent=2, ensure_ascii=False),
                "```",
                "",
            ])
        
        if error_context.tags:
            lines.extend([
                "## 标签",
                "",
                " ".join(f"`{tag}`" for tag in error_context.tags),
                "",
            ])
        
        return '\n'.join(lines)
    
    def generate_html_report(self, error_context: ErrorContext) -> str:
        """生成HTML格式报告"""
        stack_frames_html = ""
        for i, frame in enumerate(error_context.stack_frames, 1):
            stack_frames_html += f"""
        <h3>帧 {i}: <code>{frame.function_name}</code></h3>
        <p><strong>文件:</strong> <code>{frame.filename}</code> | <strong>行号:</strong> {frame.line_number}</p>
        <pre>{frame.code_context}</pre>
        """
        
        memory_section = ""
        if error_context.memory_state:
            memory_section = f"""
        <h2>内存状态</h2>
        <table>
            <tr><th>属性</th><th>值</th></tr>
            <tr><td>总内存</td><td>{error_context.memory_state.total_memory_mb:.2f} MB</td></tr>
            <tr><td>可用内存</td><td>{error_context.memory_state.available_memory_mb:.2f} MB</td></tr>
            <tr><td>内存使用率</td><td>{error_context.memory_state.memory_percent:.1f}%</td></tr>
            <tr><td>进程内存</td><td>{error_context.memory_state.process_memory_mb:.2f} MB</td></tr>
        </table>
        """
        
        thread_section = ""
        if error_context.thread_states:
            thread_rows = ""
            for t in error_context.thread_states:
                status = "运行中" if t.is_alive else "已停止"
                thread_rows += f"<tr><td>{t.thread_id}</td><td>{t.thread_name}</td><td>{status}</td><td>{'是' if t.is_daemon else '否'}</td></tr>"
            thread_section = f"""
        <h2>线程状态</h2>
        <table>
            <tr><th>线程ID</th><th>名称</th><th>状态</th><th>守护线程</th></tr>
            {thread_rows}
        </table>
        """
        
        tags_section = ""
        if error_context.tags:
            tags_html = "".join(f'<span class="tag">{tag}</span>' for tag in error_context.tags)
            tags_section = f"""
        <h2>标签</h2>
        <p>{tags_html}</p>
        """
        
        html_template = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>错误报告: {error_context.error_id}</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; margin: 0; padding: 20px; background: #f5f5f5; }}
        .container {{ max-width: 1200px; margin: 0 auto; background: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
        h1 {{ color: #333; border-bottom: 2px solid #e74c3c; padding-bottom: 10px; }}
        h2 {{ color: #555; margin-top: 30px; }}
        .severity-critical {{ background: #e74c3c; color: white; padding: 2px 8px; border-radius: 4px; }}
        .severity-high {{ background: #e67e22; color: white; padding: 2px 8px; border-radius: 4px; }}
        .severity-medium {{ background: #f39c12; color: white; padding: 2px 8px; border-radius: 4px; }}
        .severity-low {{ background: #27ae60; color: white; padding: 2px 8px; border-radius: 4px; }}
        table {{ width: 100%; border-collapse: collapse; margin: 15px 0; }}
        th, td {{ border: 1px solid #ddd; padding: 12px; text-align: left; }}
        th {{ background: #f8f9fa; }}
        pre {{ background: #2d2d2d; color: #f8f8f2; padding: 15px; border-radius: 4px; overflow-x: auto; }}
        code {{ background: #f4f4f4; padding: 2px 6px; border-radius: 3px; }}
        .tag {{ background: #3498db; color: white; padding: 4px 10px; border-radius: 15px; margin-right: 5px; font-size: 12px; }}
        .meta {{ color: #666; font-size: 14px; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>错误报告: {error_context.error_id}</h1>
        <p class="meta">生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        
        <h2>错误概述</h2>
        <table>
            <tr><th>属性</th><th>值</th></tr>
            <tr><td>错误类型</td><td><code>{error_context.error_type}</code></td></tr>
            <tr><td>错误消息</td><td>{error_context.error_message}</td></tr>
            <tr><td>分类</td><td>{error_context.category.value}</td></tr>
            <tr><td>严重程度</td><td><span class="severity-{error_context.severity.value}">{error_context.severity.value}</span></td></tr>
            <tr><td>发生时间</td><td>{error_context.timestamp}</td></tr>
        </table>
        
        <h2>堆栈跟踪</h2>
        <pre>{error_context.stack_trace}</pre>
        
        {stack_frames_html}
        
        <h2>环境信息</h2>
        <table>
            <tr><th>属性</th><th>值</th></tr>
            <tr><td>Python版本</td><td>{error_context.environment.python_version.split()[0]}</td></tr>
            <tr><td>操作系统</td><td>{error_context.environment.platform_system}</td></tr>
            <tr><td>主机名</td><td>{error_context.environment.hostname}</td></tr>
            <tr><td>工作目录</td><td><code>{error_context.environment.working_directory}</code></td></tr>
        </table>
        
        {memory_section}
        {thread_section}
        {tags_section}
    </div>
</body>
</html>"""
        
        return html_template
    
    def generate_aggregated_report(
        self,
        error_contexts: List[ErrorContext],
        format: ReportFormat = ReportFormat.MARKDOWN
    ) -> str:
        """生成聚合报告"""
        if not error_contexts:
            return "无错误记录"
        
        category_counts = Counter(ctx.category.value for ctx in error_contexts)
        severity_counts = Counter(ctx.severity.value for ctx in error_contexts)
        type_counts = Counter(ctx.error_type for ctx in error_contexts)
        
        time_range = {
            "first": min(ctx.timestamp for ctx in error_contexts),
            "last": max(ctx.timestamp for ctx in error_contexts)
        }
        
        if format == ReportFormat.JSON:
            return json.dumps({
                "summary": {
                    "total_errors": len(error_contexts),
                    "time_range": time_range,
                    "category_distribution": dict(category_counts),
                    "severity_distribution": dict(severity_counts),
                    "type_distribution": dict(type_counts.most_common(10))
                },
                "errors": [
                    {
                        "error_id": ctx.error_id,
                        "error_type": ctx.error_type,
                        "category": ctx.category.value,
                        "severity": ctx.severity.value,
                        "timestamp": ctx.timestamp,
                        "message": ctx.error_message[:100]
                    }
                    for ctx in error_contexts
                ]
            }, indent=2, ensure_ascii=False)
        
        lines = [
            "# 错误聚合报告",
            "",
            f"**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"**错误总数**: {len(error_contexts)}",
            f"**时间范围**: {time_range['first']} 至 {time_range['last']}",
            "",
            "## 分类分布",
            "",
            "| 分类 | 数量 | 占比 |",
            "|------|------|------|",
        ]
        
        for category, count in category_counts.most_common():
            percentage = count / len(error_contexts) * 100
            lines.append(f"| {category} | {count} | {percentage:.1f}% |")
        
        lines.extend([
            "",
            "## 严重程度分布",
            "",
            "| 严重程度 | 数量 | 占比 |",
            "|----------|------|------|",
        ])
        
        for severity in ['fatal', 'critical', 'high', 'medium', 'low']:
            count = severity_counts.get(severity, 0)
            if count > 0:
                percentage = count / len(error_contexts) * 100
                lines.append(f"| {severity} | {count} | {percentage:.1f}% |")
        
        lines.extend([
            "",
            "## 错误类型TOP10",
            "",
            "| 错误类型 | 数量 |",
            "|----------|------|",
        ])
        
        for error_type, count in type_counts.most_common(10):
            lines.append(f"| {error_type} | {count} |")
        
        return '\n'.join(lines)
    
    def save_report(
        self,
        error_context: ErrorContext,
        format: ReportFormat = ReportFormat.MARKDOWN,
        output_path: Optional[str] = None
    ) -> str:
        if format == ReportFormat.JSON:
            content = self.generate_json_report(error_context)
            ext = ".json"
        elif format == ReportFormat.HTML:
            content = self.generate_html_report(error_context)
            ext = ".html"
        else:
            content = self.generate_markdown_report(error_context)
            ext = ".md"
        
        if not output_path:
            output_path = str(self.output_dir / f"error_report_{error_context.error_id}{ext}")
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        return output_path


class EnhancedRecoveryEngine:
    """增强的错误智能恢复引擎 - Task 43"""
    
    def __init__(self, max_retries: int = 3, retry_delay: float = 1.0):
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.recovery_counter = 0
        self.recovery_history: List[RecoveryResult] = []
        self.strategy_stats: Dict[RecoveryStrategy, Dict[str, int]] = defaultdict(lambda: {"success": 0, "failure": 0})
        self.circuit_breaker_state: Dict[str, Dict[str, Any]] = {}
        self.logger = logging.getLogger('EnhancedRecoveryEngine')
    
    def _generate_attempt_id(self) -> str:
        self.recovery_counter += 1
        return f"RECOV-{datetime.now().strftime('%Y%m%d%H%M%S')}-{self.recovery_counter:04d}"
    
    def _predict_best_strategy(self, error_category: ErrorCategory, error_severity: ErrorSeverity) -> Tuple[RecoveryStrategy, float]:
        """预测最佳恢复策略"""
        strategy_scores = {}
        
        for strategy in RecoveryStrategy:
            stats = self.strategy_stats[strategy]
            total = stats["success"] + stats["failure"]
            if total > 0:
                success_rate = stats["success"] / total
            else:
                success_rate = 0.5
            
            category_bonus = self._get_category_strategy_bonus(error_category, strategy)
            severity_penalty = self._get_severity_strategy_penalty(error_severity, strategy)
            
            strategy_scores[strategy] = success_rate + category_bonus - severity_penalty
        
        best_strategy = max(strategy_scores, key=strategy_scores.get)
        confidence = strategy_scores[best_strategy]
        
        return best_strategy, min(confidence, 1.0)
    
    def _get_category_strategy_bonus(self, category: ErrorCategory, strategy: RecoveryStrategy) -> float:
        """获取分类策略奖励"""
        bonuses = {
            (ErrorCategory.NETWORK, RecoveryStrategy.RETRY): 0.3,
            (ErrorCategory.NETWORK, RecoveryStrategy.CIRCUIT_BREAK): 0.2,
            (ErrorCategory.DATABASE, RecoveryStrategy.RETRY): 0.2,
            (ErrorCategory.DATABASE, RecoveryStrategy.ROLLBACK): 0.3,
            (ErrorCategory.FILE_SYSTEM, RecoveryStrategy.ROLLBACK): 0.3,
            (ErrorCategory.MEMORY, RecoveryStrategy.DEGRADE): 0.3,
            (ErrorCategory.TIMEOUT, RecoveryStrategy.TIMEOUT): 0.3,
            (ErrorCategory.TIMEOUT, RecoveryStrategy.RETRY): 0.2,
        }
        return bonuses.get((category, strategy), 0.0)
    
    def _get_severity_strategy_penalty(self, severity: ErrorSeverity, strategy: RecoveryStrategy) -> float:
        """获取严重程度策略惩罚"""
        penalties = {
            (ErrorSeverity.FATAL, RecoveryStrategy.SKIP): 0.5,
            (ErrorSeverity.FATAL, RecoveryStrategy.DEGRADE): 0.3,
            (ErrorSeverity.CRITICAL, RecoveryStrategy.SKIP): 0.4,
            (ErrorSeverity.HIGH, RecoveryStrategy.SKIP): 0.3,
        }
        return penalties.get((severity, strategy), 0.0)
    
    def retry_with_backoff(
        self,
        func: Callable,
        *args,
        max_retries: Optional[int] = None,
        initial_delay: float = 1.0,
        backoff_factor: float = 2.0,
        max_delay: float = 60.0,
        exceptions: Tuple[Type[Exception], ...] = (Exception,),
        jitter: bool = True,
        **kwargs
    ) -> Tuple[Any, RecoveryResult]:
        max_retries = max_retries or self.max_retries
        attempts = []
        start_time = time.time()
        current_delay = initial_delay
        error_id = f"RETRY-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        last_exception = None
        for attempt_num in range(max_retries):
            attempt_id = self._generate_attempt_id()
            attempt_start = time.time()
            
            try:
                result = func(*args, **kwargs)
                
                attempt = RecoveryAttempt(
                    attempt_id=attempt_id,
                    strategy=RecoveryStrategy.RETRY,
                    status=RecoveryStatus.SUCCESS,
                    timestamp=datetime.now().isoformat(),
                    details=f"尝试 {attempt_num + 1}/{max_retries} 成功",
                    success=True,
                    duration_ms=int((time.time() - attempt_start) * 1000),
                    retry_count=attempt_num
                )
                attempts.append(attempt)
                
                self._update_strategy_stats(RecoveryStrategy.RETRY, True)
                
                recovery_result = RecoveryResult(
                    error_id=error_id,
                    total_attempts=len(attempts),
                    successful=True,
                    final_status=RecoveryStatus.SUCCESS,
                    attempts=attempts,
                    recovery_time_ms=int((time.time() - start_time) * 1000),
                    strategy_used=RecoveryStrategy.RETRY
                )
                
                self.recovery_history.append(recovery_result)
                return result, recovery_result
                
            except exceptions as e:
                last_exception = e
                attempt = RecoveryAttempt(
                    attempt_id=attempt_id,
                    strategy=RecoveryStrategy.RETRY,
                    status=RecoveryStatus.FAILED if attempt_num == max_retries - 1 else RecoveryStatus.IN_PROGRESS,
                    timestamp=datetime.now().isoformat(),
                    details=f"尝试 {attempt_num + 1}/{max_retries} 失败: {str(e)}",
                    success=False,
                    error_message=str(e),
                    duration_ms=int((time.time() - attempt_start) * 1000),
                    retry_count=attempt_num
                )
                attempts.append(attempt)
                
                if attempt_num < max_retries - 1:
                    delay = current_delay
                    if jitter:
                        import random
                        delay = current_delay * (0.5 + random.random())
                    
                    self.logger.warning(f"重试 {attempt_num + 1}/{max_retries} 失败，等待 {delay:.1f}s 后重试")
                    time.sleep(delay)
                    current_delay = min(current_delay * backoff_factor, max_delay)
        
        self._update_strategy_stats(RecoveryStrategy.RETRY, False)
        
        recovery_result = RecoveryResult(
            error_id=error_id,
            total_attempts=len(attempts),
            successful=False,
            final_status=RecoveryStatus.FAILED,
            attempts=attempts,
            recovery_time_ms=int((time.time() - start_time) * 1000),
            strategy_used=RecoveryStrategy.RETRY
        )
        
        self.recovery_history.append(recovery_result)
        raise last_exception
    
    def execute_with_fallback(
        self,
        primary_func: Callable,
        fallback_func: Callable,
        *args,
        **kwargs
    ) -> Tuple[Any, RecoveryResult]:
        attempts = []
        start_time = time.time()
        error_id = f"FALLBACK-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        attempt_id = self._generate_attempt_id()
        attempt_start = time.time()
        
        try:
            result = primary_func(*args, **kwargs)
            
            attempt = RecoveryAttempt(
                attempt_id=attempt_id,
                strategy=RecoveryStrategy.DEGRADE,
                status=RecoveryStatus.SUCCESS,
                timestamp=datetime.now().isoformat(),
                details="主函数执行成功",
                success=True,
                duration_ms=int((time.time() - attempt_start) * 1000)
            )
            attempts.append(attempt)
            
            self._update_strategy_stats(RecoveryStrategy.DEGRADE, True)
            
            recovery_result = RecoveryResult(
                error_id=error_id,
                total_attempts=1,
                successful=True,
                final_status=RecoveryStatus.SUCCESS,
                attempts=attempts,
                recovery_time_ms=int((time.time() - start_time) * 1000),
                strategy_used=RecoveryStrategy.DEGRADE
            )
            
            return result, recovery_result
            
        except Exception as primary_error:
            attempt = RecoveryAttempt(
                attempt_id=attempt_id,
                strategy=RecoveryStrategy.DEGRADE,
                status=RecoveryStatus.FAILED,
                timestamp=datetime.now().isoformat(),
                details=f"主函数失败: {str(primary_error)}",
                success=False,
                error_message=str(primary_error),
                duration_ms=int((time.time() - attempt_start) * 1000)
            )
            attempts.append(attempt)
            
            self.logger.info("主函数失败，尝试降级函数")
            
            fallback_attempt_id = self._generate_attempt_id()
            fallback_start = time.time()
            
            try:
                result = fallback_func(*args, **kwargs)
                
                fallback_attempt = RecoveryAttempt(
                    attempt_id=fallback_attempt_id,
                    strategy=RecoveryStrategy.DEGRADE,
                    status=RecoveryStatus.SUCCESS,
                    timestamp=datetime.now().isoformat(),
                    details="降级函数执行成功",
                    success=True,
                    duration_ms=int((time.time() - fallback_start) * 1000)
                )
                attempts.append(fallback_attempt)
                
                self._update_strategy_stats(RecoveryStrategy.DEGRADE, True)
                
                recovery_result = RecoveryResult(
                    error_id=error_id,
                    total_attempts=2,
                    successful=True,
                    final_status=RecoveryStatus.SUCCESS,
                    attempts=attempts,
                    recovery_time_ms=int((time.time() - start_time) * 1000),
                    strategy_used=RecoveryStrategy.DEGRADE
                )
                
                self.recovery_history.append(recovery_result)
                return result, recovery_result
                
            except Exception as fallback_error:
                fallback_attempt = RecoveryAttempt(
                    attempt_id=fallback_attempt_id,
                    strategy=RecoveryStrategy.DEGRADE,
                    status=RecoveryStatus.FAILED,
                    timestamp=datetime.now().isoformat(),
                    details=f"降级函数失败: {str(fallback_error)}",
                    success=False,
                    error_message=str(fallback_error),
                    duration_ms=int((time.time() - fallback_start) * 1000)
                )
                attempts.append(fallback_attempt)
                
                self._update_strategy_stats(RecoveryStrategy.DEGRADE, False)
                
                recovery_result = RecoveryResult(
                    error_id=error_id,
                    total_attempts=2,
                    successful=False,
                    final_status=RecoveryStatus.FAILED,
                    attempts=attempts,
                    recovery_time_ms=int((time.time() - start_time) * 1000),
                    strategy_used=RecoveryStrategy.DEGRADE
                )
                
                self.recovery_history.append(recovery_result)
                raise fallback_error
    
    def execute_with_rollback(
        self,
        func: Callable,
        rollback_func: Callable,
        *args,
        **kwargs
    ) -> Tuple[Any, RecoveryResult]:
        attempts = []
        start_time = time.time()
        error_id = f"ROLLBACK-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        attempt_id = self._generate_attempt_id()
        attempt_start = time.time()
        
        try:
            result = func(*args, **kwargs)
            
            attempt = RecoveryAttempt(
                attempt_id=attempt_id,
                strategy=RecoveryStrategy.ROLLBACK,
                status=RecoveryStatus.SUCCESS,
                timestamp=datetime.now().isoformat(),
                details="函数执行成功，无需回滚",
                success=True,
                duration_ms=int((time.time() - attempt_start) * 1000)
            )
            attempts.append(attempt)
            
            self._update_strategy_stats(RecoveryStrategy.ROLLBACK, True)
            
            recovery_result = RecoveryResult(
                error_id=error_id,
                total_attempts=1,
                successful=True,
                final_status=RecoveryStatus.SUCCESS,
                attempts=attempts,
                recovery_time_ms=int((time.time() - start_time) * 1000),
                rollback_performed=False,
                strategy_used=RecoveryStrategy.ROLLBACK
            )
            
            self.recovery_history.append(recovery_result)
            return result, recovery_result
            
        except Exception as e:
            attempt = RecoveryAttempt(
                attempt_id=attempt_id,
                strategy=RecoveryStrategy.ROLLBACK,
                status=RecoveryStatus.FAILED,
                timestamp=datetime.now().isoformat(),
                details=f"函数执行失败: {str(e)}",
                success=False,
                error_message=str(e),
                duration_ms=int((time.time() - attempt_start) * 1000)
            )
            attempts.append(attempt)
            
            self.logger.info("执行失败，开始回滚")
            
            rollback_attempt_id = self._generate_attempt_id()
            rollback_start = time.time()
            
            try:
                rollback_func(*args, **kwargs)
                
                rollback_attempt = RecoveryAttempt(
                    attempt_id=rollback_attempt_id,
                    strategy=RecoveryStrategy.ROLLBACK,
                    status=RecoveryStatus.SUCCESS,
                    timestamp=datetime.now().isoformat(),
                    details="回滚执行成功",
                    success=True,
                    duration_ms=int((time.time() - rollback_start) * 1000)
                )
                attempts.append(rollback_attempt)
                
            except Exception as rollback_error:
                rollback_attempt = RecoveryAttempt(
                    attempt_id=rollback_attempt_id,
                    strategy=RecoveryStrategy.ROLLBACK,
                    status=RecoveryStatus.FAILED,
                    timestamp=datetime.now().isoformat(),
                    details=f"回滚失败: {str(rollback_error)}",
                    success=False,
                    error_message=str(rollback_error),
                    duration_ms=int((time.time() - rollback_start) * 1000)
                )
                attempts.append(rollback_attempt)
            
            self._update_strategy_stats(RecoveryStrategy.ROLLBACK, False)
            
            recovery_result = RecoveryResult(
                error_id=error_id,
                total_attempts=len(attempts),
                successful=False,
                final_status=RecoveryStatus.FAILED,
                attempts=attempts,
                recovery_time_ms=int((time.time() - start_time) * 1000),
                rollback_performed=True,
                strategy_used=RecoveryStrategy.ROLLBACK
            )
            
            self.recovery_history.append(recovery_result)
            raise
    
    def circuit_breaker_execute(
        self,
        func: Callable,
        circuit_id: str,
        failure_threshold: int = 5,
        recovery_timeout: float = 60.0,
        *args,
        **kwargs
    ) -> Tuple[Any, RecoveryResult]:
        """熔断器模式执行"""
        error_id = f"CIRCUIT-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        if circuit_id not in self.circuit_breaker_state:
            self.circuit_breaker_state[circuit_id] = {
                "state": "closed",
                "failure_count": 0,
                "last_failure_time": None,
                "success_count": 0
            }
        
        circuit = self.circuit_breaker_state[circuit_id]
        
        if circuit["state"] == "open":
            if circuit["last_failure_time"]:
                elapsed = time.time() - circuit["last_failure_time"]
                if elapsed >= recovery_timeout:
                    circuit["state"] = "half_open"
                    self.logger.info(f"熔断器 {circuit_id} 进入半开状态")
                else:
                    raise Exception(f"熔断器 {circuit_id} 处于开启状态，请等待 {recovery_timeout - elapsed:.1f}s")
        
        start_time = time.time()
        attempt_id = self._generate_attempt_id()
        
        try:
            result = func(*args, **kwargs)
            
            if circuit["state"] == "half_open":
                circuit["state"] = "closed"
                circuit["failure_count"] = 0
                self.logger.info(f"熔断器 {circuit_id} 恢复关闭状态")
            
            circuit["success_count"] += 1
            
            attempt = RecoveryAttempt(
                attempt_id=attempt_id,
                strategy=RecoveryStrategy.CIRCUIT_BREAK,
                status=RecoveryStatus.SUCCESS,
                timestamp=datetime.now().isoformat(),
                details=f"熔断器 {circuit_id} 执行成功",
                success=True,
                duration_ms=int((time.time() - start_time) * 1000)
            )
            
            self._update_strategy_stats(RecoveryStrategy.CIRCUIT_BREAK, True)
            
            recovery_result = RecoveryResult(
                error_id=error_id,
                total_attempts=1,
                successful=True,
                final_status=RecoveryStatus.SUCCESS,
                attempts=[attempt],
                recovery_time_ms=int((time.time() - start_time) * 1000),
                strategy_used=RecoveryStrategy.CIRCUIT_BREAK
            )
            
            self.recovery_history.append(recovery_result)
            return result, recovery_result
            
        except Exception as e:
            circuit["failure_count"] += 1
            circuit["last_failure_time"] = time.time()
            
            if circuit["failure_count"] >= failure_threshold:
                circuit["state"] = "open"
                self.logger.warning(f"熔断器 {circuit_id} 进入开启状态")
            
            attempt = RecoveryAttempt(
                attempt_id=attempt_id,
                strategy=RecoveryStrategy.CIRCUIT_BREAK,
                status=RecoveryStatus.FAILED,
                timestamp=datetime.now().isoformat(),
                details=f"熔断器 {circuit_id} 执行失败: {str(e)}",
                success=False,
                error_message=str(e),
                duration_ms=int((time.time() - start_time) * 1000)
            )
            
            self._update_strategy_stats(RecoveryStrategy.CIRCUIT_BREAK, False)
            
            recovery_result = RecoveryResult(
                error_id=error_id,
                total_attempts=1,
                successful=False,
                final_status=RecoveryStatus.FAILED,
                attempts=[attempt],
                recovery_time_ms=int((time.time() - start_time) * 1000),
                strategy_used=RecoveryStrategy.CIRCUIT_BREAK
            )
            
            self.recovery_history.append(recovery_result)
            raise
    
    def _update_strategy_stats(self, strategy: RecoveryStrategy, success: bool):
        """更新策略统计"""
        if success:
            self.strategy_stats[strategy]["success"] += 1
        else:
            self.strategy_stats[strategy]["failure"] += 1
    
    def get_recovery_statistics(self) -> Dict[str, Any]:
        total = len(self.recovery_history)
        successful = sum(1 for r in self.recovery_history if r.successful)
        
        strategy_stats = {}
        for strategy, stats in self.strategy_stats.items():
            total_strategy = stats["success"] + stats["failure"]
            strategy_stats[strategy.value] = {
                "success": stats["success"],
                "failure": stats["failure"],
                "success_rate": round(stats["success"] / total_strategy * 100, 2) if total_strategy > 0 else 0
            }
        
        avg_recovery_time = 0
        if self.recovery_history:
            total_time = sum(r.recovery_time_ms for r in self.recovery_history)
            avg_recovery_time = total_time / len(self.recovery_history)
        
        return {
            "total_recoveries": total,
            "successful_recoveries": successful,
            "failed_recoveries": total - successful,
            "success_rate": round(successful / total * 100, 2) if total > 0 else 0,
            "average_recovery_time_ms": round(avg_recovery_time, 2),
            "strategy_statistics": strategy_stats,
            "circuit_breakers": {
                circuit_id: {
                    "state": state["state"],
                    "failure_count": state["failure_count"],
                    "success_count": state["success_count"]
                }
                for circuit_id, state in self.circuit_breaker_state.items()
            }
        }


class EnhancedRecoveryReportGenerator:
    """增强的恢复报告生成器 - Task 43.3"""
    
    def generate_json_report(self, recovery_result: RecoveryResult) -> str:
        report = {
            "report_id": f"RECOV-RPT-{recovery_result.error_id}",
            "generated_at": datetime.now().isoformat(),
            "recovery": {
                "error_id": recovery_result.error_id,
                "total_attempts": recovery_result.total_attempts,
                "successful": recovery_result.successful,
                "final_status": recovery_result.final_status.value,
                "recovery_time_ms": recovery_result.recovery_time_ms,
                "rollback_performed": recovery_result.rollback_performed,
                "strategy_used": recovery_result.strategy_used.value if recovery_result.strategy_used else None,
                "prediction_confidence": recovery_result.prediction_confidence,
            },
            "attempts": [
                {
                    "attempt_id": a.attempt_id,
                    "strategy": a.strategy.value,
                    "status": a.status.value,
                    "timestamp": a.timestamp,
                    "details": a.details,
                    "success": a.success,
                    "error_message": a.error_message,
                    "duration_ms": a.duration_ms,
                    "retry_count": a.retry_count,
                    "escalated": a.escalated
                }
                for a in recovery_result.attempts
            ]
        }
        
        return json.dumps(report, indent=2, ensure_ascii=False)
    
    def generate_markdown_report(self, recovery_result: RecoveryResult) -> str:
        status_icon = "✓" if recovery_result.successful else "✗"
        
        lines = [
            f"# 恢复报告: {recovery_result.error_id}",
            "",
            f"**状态**: {status_icon} {recovery_result.final_status.value}",
            f"**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "## 恢复概览",
            "",
            f"| 属性 | 值 |",
            f"|------|-----|",
            f"| 总尝试次数 | {recovery_result.total_attempts} |",
            f"| 最终状态 | {recovery_result.final_status.value} |",
            f"| 恢复耗时 | {recovery_result.recovery_time_ms}ms |",
            f"| 是否回滚 | {'是' if recovery_result.rollback_performed else '否'} |",
            f"| 使用策略 | {recovery_result.strategy_used.value if recovery_result.strategy_used else 'N/A'} |",
            f"| 预测置信度 | {recovery_result.prediction_confidence:.0%} |",
            "",
            "## 恢复尝试详情",
            "",
        ]
        
        for i, attempt in enumerate(recovery_result.attempts, 1):
            icon = "✓" if attempt.success else "✗"
            lines.extend([
                f"### 尝试 {i}: {icon} {attempt.strategy.value}",
                "",
                f"| 属性 | 值 |",
                f"|------|-----|",
                f"| 策略 | {attempt.strategy.value} |",
                f"| 状态 | {attempt.status.value} |",
                f"| 时间 | {attempt.timestamp} |",
                f"| 耗时 | {attempt.duration_ms}ms |",
                f"| 重试次数 | {attempt.retry_count} |",
                f"| 详情 | {attempt.details} |",
            ])
            
            if attempt.error_message:
                lines.extend([
                    "",
                    f"**错误信息**: {attempt.error_message}",
                ])
            lines.append("")
        
        return '\n'.join(lines)
    
    def generate_trend_analysis(
        self,
        recovery_history: List[RecoveryResult],
        time_window_hours: int = 24
    ) -> Dict[str, Any]:
        """生成趋势分析"""
        if not recovery_history:
            return {"error": "无恢复历史数据"}
        
        cutoff_time = datetime.now() - timedelta(hours=time_window_hours)
        
        recent_recoveries = [
            r for r in recovery_history
            if datetime.fromisoformat(r.attempts[0].timestamp) >= cutoff_time if r.attempts
        ]
        
        if not recent_recoveries:
            return {"error": f"最近{time_window_hours}小时内无恢复记录"}
        
        hourly_stats = defaultdict(lambda: {"total": 0, "success": 0})
        
        for recovery in recent_recoveries:
            if recovery.attempts:
                hour = recovery.attempts[0].timestamp[:13]
                hourly_stats[hour]["total"] += 1
                if recovery.successful:
                    hourly_stats[hour]["success"] += 1
        
        strategy_trends = defaultdict(lambda: {"total": 0, "success": 0})
        for recovery in recent_recoveries:
            if recovery.strategy_used:
                strategy_trends[recovery.strategy_used.value]["total"] += 1
                if recovery.successful:
                    strategy_trends[recovery.strategy_used.value]["success"] += 1
        
        avg_recovery_times = []
        for recovery in recent_recoveries:
            avg_recovery_times.append(recovery.recovery_time_ms)
        
        return {
            "time_window_hours": time_window_hours,
            "total_recoveries": len(recent_recoveries),
            "success_rate": round(
                sum(1 for r in recent_recoveries if r.successful) / len(recent_recoveries) * 100, 2
            ),
            "hourly_distribution": dict(hourly_stats),
            "strategy_trends": {
                strategy: {
                    "total": stats["total"],
                    "success_rate": round(stats["success"] / stats["total"] * 100, 2) if stats["total"] > 0 else 0
                }
                for strategy, stats in strategy_trends.items()
            },
            "average_recovery_time_ms": round(sum(avg_recovery_times) / len(avg_recovery_times), 2),
            "trend": "improving" if len(recent_recoveries) > 0 and recent_recoveries[-1].successful else "stable"
        }


class EnhancedNotificationManager:
    """增强的错误通知管理器 - Task 44"""
    
    def __init__(self, log_dir: str = "."):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.notification_counter = 0
        self.notification_history: List[NotificationRecord] = []
        self.logger = self._setup_logger()
        self.channel_configs: Dict[NotificationChannel, Dict[str, Any]] = {}
    
    def _setup_logger(self) -> logging.Logger:
        logger = logging.getLogger('EnhancedErrorNotification')
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        
        return logger
    
    def _generate_notification_id(self) -> str:
        self.notification_counter += 1
        return f"NOTIF-{datetime.now().strftime('%Y%m%d%H%M%S')}-{self.notification_counter:04d}"
    
    def configure_channel(self, channel: NotificationChannel, config: Dict[str, Any]):
        """配置通知渠道"""
        self.channel_configs[channel] = config
    
    def notify_console(
        self,
        error_context: ErrorContext,
        fix_suggestions: Optional[List[FixSuggestion]] = None
    ) -> NotificationRecord:
        notification_id = self._generate_notification_id()
        
        severity_colors = {
            ErrorSeverity.LOW: "\033[92m",
            ErrorSeverity.MEDIUM: "\033[93m",
            ErrorSeverity.HIGH: "\033[91m",
            ErrorSeverity.CRITICAL: "\033[101m",
            ErrorSeverity.FATAL: "\033[105m",
        }
        reset_color = "\033[0m"
        
        color = severity_colors.get(error_context.severity, "")
        
        message_lines = [
            f"\n{color}{'='*60}{reset_color}",
            f"{color}错误通知 [{error_context.severity.value.upper()}]{reset_color}",
            f"{color}{'='*60}{reset_color}",
            f"错误ID: {error_context.error_id}",
            f"类型: {error_context.error_type}",
            f"分类: {error_context.category.value}",
            f"消息: {error_context.error_message}",
            f"时间: {error_context.timestamp}",
        ]
        
        if error_context.error_pattern_id:
            message_lines.append(f"模式ID: {error_context.error_pattern_id}")
        
        if fix_suggestions:
            message_lines.append("\n修复建议:")
            for suggestion in fix_suggestions[:3]:
                auto_fix = " [可自动修复]" if suggestion.auto_fixable else ""
                message_lines.append(f"  - {suggestion.title}{auto_fix}: {suggestion.description}")
        
        message_lines.append(f"{color}{'='*60}{reset_color}\n")
        
        message = '\n'.join(message_lines)
        print(message)
        
        record = NotificationRecord(
            notification_id=notification_id,
            channel=NotificationChannel.CONSOLE,
            error_id=error_context.error_id,
            timestamp=datetime.now().isoformat(),
            success=True,
            message=message
        )
        
        self.notification_history.append(record)
        return record
    
    def notify_log(
        self,
        error_context: ErrorContext,
        fix_suggestions: Optional[List[FixSuggestion]] = None
    ) -> NotificationRecord:
        notification_id = self._generate_notification_id()
        
        log_message = (
            f"Error [{error_context.error_id}]: "
            f"{error_context.error_type}: {error_context.error_message} "
            f"(Category: {error_context.category.value}, Severity: {error_context.severity.value})"
        )
        
        if error_context.severity == ErrorSeverity.FATAL:
            self.logger.critical(log_message)
        elif error_context.severity == ErrorSeverity.CRITICAL:
            self.logger.critical(log_message)
        elif error_context.severity == ErrorSeverity.HIGH:
            self.logger.error(log_message)
        elif error_context.severity == ErrorSeverity.MEDIUM:
            self.logger.warning(log_message)
        else:
            self.logger.info(log_message)
        
        record = NotificationRecord(
            notification_id=notification_id,
            channel=NotificationChannel.LOG,
            error_id=error_context.error_id,
            timestamp=datetime.now().isoformat(),
            success=True,
            message=log_message
        )
        
        self.notification_history.append(record)
        return record
    
    def notify_file(
        self,
        error_context: ErrorContext,
        output_path: Optional[str] = None,
        format: ReportFormat = ReportFormat.MARKDOWN
    ) -> NotificationRecord:
        notification_id = self._generate_notification_id()
        
        if not output_path:
            output_path = str(self.log_dir / f"error_{error_context.error_id}.{format.value}")
        
        try:
            report_gen = EnhancedErrorReportGenerator(str(self.log_dir))
            
            if format == ReportFormat.MARKDOWN:
                content = report_gen.generate_markdown_report(error_context)
            elif format == ReportFormat.HTML:
                content = report_gen.generate_html_report(error_context)
            else:
                content = report_gen.generate_json_report(error_context)
            
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            record = NotificationRecord(
                notification_id=notification_id,
                channel=NotificationChannel.FILE,
                error_id=error_context.error_id,
                timestamp=datetime.now().isoformat(),
                success=True,
                message=f"错误报告已保存到: {output_path}",
                recipient=output_path
            )
            
        except Exception as e:
            record = NotificationRecord(
                notification_id=notification_id,
                channel=NotificationChannel.FILE,
                error_id=error_context.error_id,
                timestamp=datetime.now().isoformat(),
                success=False,
                message=f"保存错误报告失败: {str(e)}"
            )
        
        self.notification_history.append(record)
        return record
    
    def notify_webhook(
        self,
        error_context: ErrorContext,
        webhook_url: Optional[str] = None,
        fix_suggestions: Optional[List[FixSuggestion]] = None
    ) -> NotificationRecord:
        """Webhook通知"""
        notification_id = self._generate_notification_id()
        
        url = webhook_url or self.channel_configs.get(NotificationChannel.WEBHOOK, {}).get("url")
        
        if not url:
            return NotificationRecord(
                notification_id=notification_id,
                channel=NotificationChannel.WEBHOOK,
                error_id=error_context.error_id,
                timestamp=datetime.now().isoformat(),
                success=False,
                message="未配置Webhook URL"
            )
        
        try:
            import urllib.request
            import urllib.error
            
            payload = {
                "error_id": error_context.error_id,
                "error_type": error_context.error_type,
                "message": error_context.error_message,
                "category": error_context.category.value,
                "severity": error_context.severity.value,
                "timestamp": error_context.timestamp,
                "suggestions": [
                    {
                        "title": s.title,
                        "description": s.description,
                        "auto_fixable": s.auto_fixable
                    }
                    for s in (fix_suggestions or [])[:3]
                ]
            }
            
            data = json.dumps(payload).encode('utf-8')
            req = urllib.request.Request(
                url,
                data=data,
                headers={'Content-Type': 'application/json'}
            )
            
            with urllib.request.urlopen(req, timeout=10) as response:
                if response.status == 200:
                    record = NotificationRecord(
                        notification_id=notification_id,
                        channel=NotificationChannel.WEBHOOK,
                        error_id=error_context.error_id,
                        timestamp=datetime.now().isoformat(),
                        success=True,
                        message=f"Webhook通知成功: {url}",
                        recipient=url
                    )
                else:
                    record = NotificationRecord(
                        notification_id=notification_id,
                        channel=NotificationChannel.WEBHOOK,
                        error_id=error_context.error_id,
                        timestamp=datetime.now().isoformat(),
                        success=False,
                        message=f"Webhook返回状态码: {response.status}",
                        recipient=url
                    )
        
        except Exception as e:
            record = NotificationRecord(
                notification_id=notification_id,
                channel=NotificationChannel.WEBHOOK,
                error_id=error_context.error_id,
                timestamp=datetime.now().isoformat(),
                success=False,
                message=f"Webhook通知失败: {str(e)}",
                recipient=url
            )
        
        self.notification_history.append(record)
        return record
    
    def notify_slack(
        self,
        error_context: ErrorContext,
        webhook_url: Optional[str] = None,
        fix_suggestions: Optional[List[FixSuggestion]] = None
    ) -> NotificationRecord:
        """Slack通知"""
        notification_id = self._generate_notification_id()
        
        url = webhook_url or self.channel_configs.get(NotificationChannel.SLACK, {}).get("webhook_url")
        
        if not url:
            return NotificationRecord(
                notification_id=notification_id,
                channel=NotificationChannel.SLACK,
                error_id=error_context.error_id,
                timestamp=datetime.now().isoformat(),
                success=False,
                message="未配置Slack Webhook URL"
            )
        
        try:
            import urllib.request
            
            severity_colors = {
                ErrorSeverity.LOW: "#36a64f",
                ErrorSeverity.MEDIUM: "#ff9900",
                ErrorSeverity.HIGH: "#ff6600",
                ErrorSeverity.CRITICAL: "#ff0000",
                ErrorSeverity.FATAL: "#990000",
            }
            
            fields = [
                {
                    "title": "错误类型",
                    "value": error_context.error_type,
                    "short": True
                },
                {
                    "title": "分类",
                    "value": error_context.category.value,
                    "short": True
                },
                {
                    "title": "严重程度",
                    "value": error_context.severity.value.upper(),
                    "short": True
                },
                {
                    "title": "时间",
                    "value": error_context.timestamp,
                    "short": True
                }
            ]
            
            if fix_suggestions:
                suggestions_text = "\n".join([
                    f"• {s.title}" + (" (可自动修复)" if s.auto_fixable else "")
                    for s in fix_suggestions[:3]
                ])
                fields.append({
                    "title": "修复建议",
                    "value": suggestions_text,
                    "short": False
                })
            
            payload = {
                "attachments": [
                    {
                        "color": severity_colors.get(error_context.severity, "#808080"),
                        "title": f"错误通知: {error_context.error_id}",
                        "text": error_context.error_message,
                        "fields": fields,
                        "footer": "错误处理系统",
                        "ts": int(time.time())
                    }
                ]
            }
            
            data = json.dumps(payload).encode('utf-8')
            req = urllib.request.Request(
                url,
                data=data,
                headers={'Content-Type': 'application/json'}
            )
            
            with urllib.request.urlopen(req, timeout=10) as response:
                if response.status == 200:
                    record = NotificationRecord(
                        notification_id=notification_id,
                        channel=NotificationChannel.SLACK,
                        error_id=error_context.error_id,
                        timestamp=datetime.now().isoformat(),
                        success=True,
                        message=f"Slack通知成功",
                        recipient=url
                    )
                else:
                    record = NotificationRecord(
                        notification_id=notification_id,
                        channel=NotificationChannel.SLACK,
                        error_id=error_context.error_id,
                        timestamp=datetime.now().isoformat(),
                        success=False,
                        message=f"Slack返回状态码: {response.status}",
                        recipient=url
                    )
        
        except Exception as e:
            record = NotificationRecord(
                notification_id=notification_id,
                channel=NotificationChannel.SLACK,
                error_id=error_context.error_id,
                timestamp=datetime.now().isoformat(),
                success=False,
                message=f"Slack通知失败: {str(e)}",
                recipient=url
            )
        
        self.notification_history.append(record)
        return record
    
    def notify_all(
        self,
        error_context: ErrorContext,
        fix_suggestions: Optional[List[FixSuggestion]] = None,
        channels: Optional[List[NotificationChannel]] = None
    ) -> List[NotificationRecord]:
        channels = channels or [NotificationChannel.CONSOLE, NotificationChannel.LOG]
        records = []
        
        for channel in channels:
            if channel == NotificationChannel.CONSOLE:
                records.append(self.notify_console(error_context, fix_suggestions))
            elif channel == NotificationChannel.LOG:
                records.append(self.notify_log(error_context, fix_suggestions))
            elif channel == NotificationChannel.FILE:
                records.append(self.notify_file(error_context))
            elif channel == NotificationChannel.WEBHOOK:
                records.append(self.notify_webhook(error_context, None, fix_suggestions))
            elif channel == NotificationChannel.SLACK:
                records.append(self.notify_slack(error_context, None, fix_suggestions))
        
        return records


class EnhancedFixSuggestionEngine:
    """增强的修复建议引擎 - Task 44.3"""
    
    SUGGESTION_RULES = {
        ErrorCategory.SYNTAX: [
            {
                "title": "检查语法错误",
                "description": "仔细检查代码语法，确保括号、引号、缩进等正确",
                "priority": 1,
                "code_example": "# 使用 linter 工具检查语法\npython -m py_compile your_file.py",
                "confidence": 0.9,
                "auto_fixable": True,
                "estimated_effort": "low"
            }
        ],
        ErrorCategory.RUNTIME: [
            {
                "title": "添加异常处理",
                "description": "使用 try-except 块捕获可能的运行时异常",
                "priority": 1,
                "code_example": "try:\n    # 可能出错的代码\nexcept Exception as e:\n    logger.error(f'Error: {e}')",
                "confidence": 0.8,
                "auto_fixable": False,
                "estimated_effort": "medium"
            },
            {
                "title": "检查变量类型",
                "description": "确保变量类型正确，使用 isinstance() 进行类型检查",
                "priority": 2,
                "code_example": "if not isinstance(value, expected_type):\n    raise TypeError(f'Expected {expected_type}, got {type(value)}')",
                "confidence": 0.7,
                "auto_fixable": False,
                "estimated_effort": "low"
            }
        ],
        ErrorCategory.FILE_SYSTEM: [
            {
                "title": "检查文件路径",
                "description": "确认文件路径存在且可访问",
                "priority": 1,
                "code_example": "import os\nif not os.path.exists(file_path):\n    raise FileNotFoundError(f'File not found: {file_path}')",
                "confidence": 0.9,
                "auto_fixable": True,
                "estimated_effort": "low"
            },
            {
                "title": "检查文件权限",
                "description": "确保有足够的权限访问文件",
                "priority": 2,
                "code_example": "import os\nif not os.access(file_path, os.R_OK):\n    raise PermissionError(f'No read permission: {file_path}')",
                "confidence": 0.8,
                "auto_fixable": False,
                "estimated_effort": "low"
            }
        ],
        ErrorCategory.NETWORK: [
            {
                "title": "添加重试机制",
                "description": "网络请求可能因临时问题失败，添加重试逻辑",
                "priority": 1,
                "code_example": "import time\nfor attempt in range(max_retries):\n    try:\n        response = requests.get(url)\n        break\n    except requests.RequestException:\n        time.sleep(2 ** attempt)",
                "confidence": 0.9,
                "auto_fixable": True,
                "estimated_effort": "medium"
            },
            {
                "title": "设置超时",
                "description": "为网络请求设置合理的超时时间",
                "priority": 2,
                "code_example": "response = requests.get(url, timeout=30)",
                "confidence": 0.8,
                "auto_fixable": True,
                "estimated_effort": "low"
            },
            {
                "title": "使用熔断器模式",
                "description": "防止级联故障，在服务不可用时快速失败",
                "priority": 3,
                "code_example": "from circuitbreaker import circuit\n\n@circuit(failure_threshold=5, recovery_timeout=60)\ndef call_external_service():\n    # 调用外部服务\n    pass",
                "confidence": 0.7,
                "auto_fixable": False,
                "estimated_effort": "high"
            }
        ],
        ErrorCategory.DATABASE: [
            {
                "title": "使用事务",
                "description": "数据库操作使用事务确保数据一致性",
                "priority": 1,
                "code_example": "with db.transaction():\n    db.execute(query)",
                "confidence": 0.8,
                "auto_fixable": False,
                "estimated_effort": "medium"
            },
            {
                "title": "检查连接",
                "description": "确保数据库连接有效",
                "priority": 2,
                "code_example": "try:\n    db.ping()\nexcept:\n    db.reconnect()",
                "confidence": 0.7,
                "auto_fixable": False,
                "estimated_effort": "low"
            },
            {
                "title": "添加连接池",
                "description": "使用连接池管理数据库连接",
                "priority": 3,
                "code_example": "from sqlalchemy import create_engine\nfrom sqlalchemy.pool import QueuePool\n\nengine = create_engine(\n    DATABASE_URL,\n    poolclass=QueuePool,\n    pool_size=10,\n    max_overflow=20\n)",
                "confidence": 0.8,
                "auto_fixable": False,
                "estimated_effort": "high"
            }
        ],
        ErrorCategory.CONFIGURATION: [
            {
                "title": "验证配置",
                "description": "检查配置文件格式和必需字段",
                "priority": 1,
                "code_example": "required_keys = ['host', 'port', 'database']\nfor key in required_keys:\n    if key not in config:\n        raise ValueError(f'Missing config: {key}')",
                "confidence": 0.9,
                "auto_fixable": False,
                "estimated_effort": "low"
            }
        ],
        ErrorCategory.MEMORY: [
            {
                "title": "优化内存使用",
                "description": "使用生成器替代列表，及时释放大对象",
                "priority": 1,
                "code_example": "# 使用生成器\nfor item in generator():\n    process(item)\n\n# 释放大对象\ndel large_object",
                "confidence": 0.8,
                "auto_fixable": False,
                "estimated_effort": "medium"
            }
        ],
        ErrorCategory.DEPENDENCY: [
            {
                "title": "安装缺失依赖",
                "description": "检查并安装缺失的Python包",
                "priority": 1,
                "code_example": "pip install missing_package\n# 或在 requirements.txt 中添加依赖",
                "confidence": 0.9,
                "auto_fixable": True,
                "estimated_effort": "low"
            }
        ],
        ErrorCategory.ASYNC: [
            {
                "title": "正确处理异步任务",
                "description": "确保正确使用async/await语法",
                "priority": 1,
                "code_example": "async def fetch_data():\n    async with aiohttp.ClientSession() as session:\n        async with session.get(url) as response:\n            return await response.json()",
                "confidence": 0.8,
                "auto_fixable": False,
                "estimated_effort": "medium"
            }
        ],
        ErrorCategory.THREADING: [
            {
                "title": "避免竞态条件",
                "description": "使用锁保护共享资源",
                "priority": 1,
                "code_example": "import threading\n\nlock = threading.Lock()\n\nwith lock:\n    # 访问共享资源\n    pass",
                "confidence": 0.8,
                "auto_fixable": False,
                "estimated_effort": "medium"
            }
        ],
    }
    
    ERROR_TYPE_SUGGESTIONS = {
        "KeyError": {
            "title": "检查字典键",
            "description": "使用 .get() 方法或检查键是否存在",
            "priority": 1,
            "code_example": "value = my_dict.get('key', default_value)\n# 或\nif 'key' in my_dict:\n    value = my_dict['key']",
            "confidence": 0.9,
            "auto_fixable": True,
            "estimated_effort": "low"
        },
        "IndexError": {
            "title": "检查索引范围",
            "description": "访问列表前检查索引是否有效",
            "priority": 1,
            "code_example": "if 0 <= index < len(my_list):\n    value = my_list[index]",
            "confidence": 0.9,
            "auto_fixable": True,
            "estimated_effort": "low"
        },
        "AttributeError": {
            "title": "检查对象属性",
            "description": "使用 hasattr() 检查属性是否存在",
            "priority": 1,
            "code_example": "if hasattr(obj, 'attribute'):\n    value = obj.attribute",
            "confidence": 0.9,
            "auto_fixable": True,
            "estimated_effort": "low"
        },
        "TypeError": {
            "title": "检查类型兼容性",
            "description": "确保操作数类型正确",
            "priority": 1,
            "code_example": "if isinstance(value, expected_type):\n    result = operation(value)",
            "confidence": 0.8,
            "auto_fixable": False,
            "estimated_effort": "low"
        },
        "ValueError": {
            "title": "验证输入值",
            "description": "在处理前验证值的有效性",
            "priority": 1,
            "code_example": "if not is_valid(value):\n    raise ValueError('Invalid value')",
            "confidence": 0.8,
            "auto_fixable": False,
            "estimated_effort": "low"
        },
        "PermissionError": {
            "title": "检查权限",
            "description": "确保有足够的权限执行操作",
            "priority": 1,
            "code_example": "import os\nos.chmod(file_path, 0o644)",
            "confidence": 0.9,
            "auto_fixable": False,
            "estimated_effort": "low"
        },
        "FileNotFoundError": {
            "title": "创建缺失文件",
            "description": "如果文件不存在，创建它或使用默认值",
            "priority": 1,
            "code_example": "import os\nif not os.path.exists(file_path):\n    with open(file_path, 'w') as f:\n        f.write(default_content)",
            "confidence": 0.9,
            "auto_fixable": True,
            "estimated_effort": "low"
        },
        "ConnectionError": {
            "title": "检查网络连接",
            "description": "确保网络连接正常，添加重试逻辑",
            "priority": 1,
            "code_example": "import time\nimport requests\n\nfor attempt in range(3):\n    try:\n        response = requests.get(url, timeout=10)\n        break\n    except ConnectionError:\n        time.sleep(2 ** attempt)",
            "confidence": 0.8,
            "auto_fixable": False,
            "estimated_effort": "medium"
        },
        "TimeoutError": {
            "title": "增加超时时间",
            "description": "为操作设置更长的超时时间",
            "priority": 1,
            "code_example": "# 增加超时时间\nresponse = requests.get(url, timeout=60)",
            "confidence": 0.8,
            "auto_fixable": True,
            "estimated_effort": "low"
        },
    }
    
    def __init__(self):
        self.suggestion_counter = 0
    
    def _generate_suggestion_id(self) -> str:
        self.suggestion_counter += 1
        return f"SUG-{datetime.now().strftime('%Y%m%d%H%M%S')}-{self.suggestion_counter:04d}"
    
    def generate_suggestions(
        self,
        error_context: ErrorContext
    ) -> List[FixSuggestion]:
        suggestions = []
        
        if error_context.error_type in self.ERROR_TYPE_SUGGESTIONS:
            rule = self.ERROR_TYPE_SUGGESTIONS[error_context.error_type]
            suggestions.append(FixSuggestion(
                suggestion_id=self._generate_suggestion_id(),
                title=rule["title"],
                description=rule["description"],
                priority=rule["priority"],
                category=error_context.category.value,
                code_example=rule.get("code_example"),
                confidence=rule.get("confidence", 0.8),
                auto_fixable=rule.get("auto_fixable", False),
                estimated_effort=rule.get("estimated_effort", "medium")
            ))
        
        if error_context.category in self.SUGGESTION_RULES:
            for rule in self.SUGGESTION_RULES[error_context.category]:
                suggestions.append(FixSuggestion(
                    suggestion_id=self._generate_suggestion_id(),
                    title=rule["title"],
                    description=rule["description"],
                    priority=rule["priority"],
                    category=error_context.category.value,
                    code_example=rule.get("code_example"),
                    confidence=rule.get("confidence", 0.8),
                    auto_fixable=rule.get("auto_fixable", False),
                    estimated_effort=rule.get("estimated_effort", "medium")
                ))
        
        suggestions.sort(key=lambda x: (x.priority, -x.confidence))
        
        return suggestions[:5]


class EnhancedErrorDetailPresenter:
    """增强的错误详情展示器 - Task 44.2"""
    
    @staticmethod
    def format_for_console(error_context: ErrorContext) -> str:
        severity_icons = {
            ErrorSeverity.LOW: "[INFO]",
            ErrorSeverity.MEDIUM: "[WARN]",
            ErrorSeverity.HIGH: "[ERROR]",
            ErrorSeverity.CRITICAL: "[CRITICAL]",
            ErrorSeverity.FATAL: "[FATAL]",
        }
        
        icon = severity_icons.get(error_context.severity, "[?]")
        
        lines = [
            f"\n{icon} 错误详情",
            f"{'─'*50}",
            f"ID: {error_context.error_id}",
            f"类型: {error_context.error_type}",
            f"分类: {error_context.category.value}",
            f"严重程度: {error_context.severity.value}",
            f"时间: {error_context.timestamp}",
            "",
            f"消息: {error_context.error_message}",
            "",
        ]
        
        if error_context.error_pattern_id:
            lines.append(f"模式ID: {error_context.error_pattern_id}")
        
        if error_context.stack_frames:
            lines.append("调用栈:")
            for i, frame in enumerate(error_context.stack_frames[:5], 1):
                lines.append(f"  {i}. {frame.filename}:{frame.line_number} in {frame.function_name}()")
        
        if error_context.thread_states:
            lines.append("")
            lines.append(f"活跃线程: {len([t for t in error_context.thread_states if t.is_alive])}")
        
        if error_context.async_tasks:
            lines.append(f"异步任务: {len(error_context.async_tasks)}")
        
        if error_context.memory_state:
            lines.append("")
            lines.append(f"内存使用: {error_context.memory_state.memory_percent:.1f}%")
        
        if error_context.tags:
            lines.append("")
            lines.append(f"标签: {', '.join(error_context.tags)}")
        
        lines.append(f"{'─'*50}")
        
        return '\n'.join(lines)
    
    @staticmethod
    def format_for_log(error_context: ErrorContext) -> str:
        return (
            f"[{error_context.timestamp}] "
            f"[{error_context.severity.value.upper()}] "
            f"[{error_context.category.value}] "
            f"{error_context.error_type}: {error_context.error_message} "
            f"(ID: {error_context.error_id})"
        )
    
    @staticmethod
    def format_summary(error_contexts: List[ErrorContext]) -> str:
        if not error_contexts:
            return "无错误记录"
        
        category_counts = Counter(ctx.category.value for ctx in error_contexts)
        severity_counts = Counter(ctx.severity.value for ctx in error_contexts)
        
        lines = [
            f"错误统计 (共 {len(error_contexts)} 个)",
            f"{'─'*30}",
            "",
            "按分类:",
        ]
        
        for category, count in category_counts.most_common():
            lines.append(f"  {category}: {count}")
        
        lines.append("")
        lines.append("按严重程度:")
        
        for severity in [ErrorSeverity.FATAL, ErrorSeverity.CRITICAL, ErrorSeverity.HIGH, ErrorSeverity.MEDIUM, ErrorSeverity.LOW]:
            count = severity_counts.get(severity.value, 0)
            if count > 0:
                lines.append(f"  {severity.value}: {count}")
        
        return '\n'.join(lines)
    
    @staticmethod
    def format_dashboard(error_contexts: List[ErrorContext]) -> str:
        """生成仪表板格式的错误摘要"""
        if not error_contexts:
            return "[OK] 无错误记录"
        
        now = datetime.now()
        last_hour = sum(1 for ctx in error_contexts 
                       if datetime.fromisoformat(ctx.timestamp) > now - timedelta(hours=1))
        last_day = sum(1 for ctx in error_contexts 
                      if datetime.fromisoformat(ctx.timestamp) > now - timedelta(days=1))
        
        severity_counts = Counter(ctx.severity.value for ctx in error_contexts)
        
        lines = [
            "+" + "="*56 + "+",
            "|" + "错误监控仪表板".center(54) + "|",
            "+" + "="*56 + "+",
            f"| 总错误数: {len(error_contexts):>5}  | 最近1小时: {last_hour:>3}  | 最近24小时: {last_day:>4}  |",
            "+" + "="*56 + "+",
            "|" + "严重程度分布:".ljust(54) + "|",
        ]
        
        for severity in ['fatal', 'critical', 'high', 'medium', 'low']:
            count = severity_counts.get(severity, 0)
            bar = '#' * min(count, 20) + '-' * (20 - min(count, 20))
            lines.append(f"| {severity:10}: [{bar}] {count:>4}  |")
        
        lines.append("+" + "="*56 + "+")
        
        return '\n'.join(lines)


class EnhancedErrorHandler:
    """增强的统一错误处理器 - 整合所有错误处理功能"""
    
    def __init__(
        self,
        project_root: str = ".",
        output_dir: str = ".",
        max_retries: int = 3
    ):
        self.project_root = Path(project_root).resolve()
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.context_recorder = EnhancedErrorContextRecorder(project_root)
        self.report_generator = EnhancedErrorReportGenerator(str(self.output_dir))
        self.recovery_engine = EnhancedRecoveryEngine(max_retries=max_retries)
        self.recovery_report_gen = EnhancedRecoveryReportGenerator()
        self.notification_manager = EnhancedNotificationManager(str(self.output_dir))
        self.suggestion_engine = EnhancedFixSuggestionEngine()
        
        self.error_history: List[ErrorContext] = []
        self.logger = self._setup_logger()
    
    def _setup_logger(self) -> logging.Logger:
        logger = logging.getLogger('EnhancedErrorHandler')
        logger.setLevel(logging.INFO)
        
        log_file = self.output_dir / 'error_handler.log'
        handler = logging.FileHandler(log_file, encoding='utf-8')
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        
        return logger
    
    def handle_error(
        self,
        exc: Exception,
        custom_context: Optional[Dict[str, Any]] = None,
        tags: Optional[List[str]] = None,
        notify_channels: Optional[List[NotificationChannel]] = None,
        save_report: bool = True,
        report_format: ReportFormat = ReportFormat.MARKDOWN
    ) -> ErrorReport:
        error_context = self.context_recorder.record_error(exc, custom_context, tags)
        self.error_history.append(error_context)
        
        fix_suggestions = self.suggestion_engine.generate_suggestions(error_context)
        
        notifications = self.notification_manager.notify_all(
            error_context,
            fix_suggestions,
            notify_channels
        )
        
        if save_report:
            report_path = self.report_generator.save_report(error_context, report_format)
            self.logger.info(f"错误报告已保存: {report_path}")
        
        return ErrorReport(
            report_id=f"RPT-{error_context.error_id}",
            generated_at=datetime.now().isoformat(),
            error_context=error_context,
            recovery_result=None,
            fix_suggestions=fix_suggestions,
            notifications=notifications
        )
    
    def handle_with_recovery(
        self,
        exc: Exception,
        recovery_func: Optional[Callable] = None,
        recovery_strategy: RecoveryStrategy = RecoveryStrategy.RETRY,
        custom_context: Optional[Dict[str, Any]] = None
    ) -> Tuple[ErrorReport, Optional[RecoveryResult]]:
        error_context = self.context_recorder.record_error(exc, custom_context)
        self.error_history.append(error_context)
        
        fix_suggestions = self.suggestion_engine.generate_suggestions(error_context)
        recovery_result = None
        
        if recovery_func:
            best_strategy, confidence = self.recovery_engine._predict_best_strategy(
                error_context.category,
                error_context.severity
            )
            
            if recovery_strategy == RecoveryStrategy.RETRY:
                try:
                    _, recovery_result = self.recovery_engine.retry_with_backoff(
                        recovery_func
                    )
                except Exception:
                    pass
            elif recovery_strategy == RecoveryStrategy.DEGRADE:
                pass
        
        notifications = self.notification_manager.notify_all(
            error_context,
            fix_suggestions
        )
        
        return ErrorReport(
            report_id=f"RPT-{error_context.error_id}",
            generated_at=datetime.now().isoformat(),
            error_context=error_context,
            recovery_result=recovery_result,
            fix_suggestions=fix_suggestions,
            notifications=notifications
        ), recovery_result
    
    def get_statistics(self) -> Dict[str, Any]:
        category_counts = Counter(ctx.category.value for ctx in self.error_history)
        severity_counts = Counter(ctx.severity.value for ctx in self.error_history)
        
        recovery_stats = self.recovery_engine.get_recovery_statistics()
        
        return {
            "total_errors": len(self.error_history),
            "category_distribution": dict(category_counts),
            "severity_distribution": dict(severity_counts),
            "recovery_statistics": recovery_stats,
            "error_patterns": len(self.context_recorder.error_patterns)
        }
    
    def generate_summary_report(self, output_path: Optional[str] = None) -> str:
        stats = self.get_statistics()
        
        lines = [
            "# 错误处理系统报告",
            "",
            f"**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "## 统计概览",
            "",
            f"- 总错误数: {stats['total_errors']}",
            f"- 错误模式数: {stats['error_patterns']}",
            f"- 恢复成功数: {stats['recovery_statistics']['successful_recoveries']}",
            f"- 恢复成功率: {stats['recovery_statistics']['success_rate']}%",
            "",
            "## 错误分类分布",
            "",
            "| 分类 | 数量 |",
            "|------|------|",
        ]
        
        for category, count in sorted(stats['category_distribution'].items(), key=lambda x: -x[1]):
            lines.append(f"| {category} | {count} |")
        
        lines.extend([
            "",
            "## 严重程度分布",
            "",
            "| 严重程度 | 数量 |",
            "|----------|------|",
        ])
        
        for severity in ['fatal', 'critical', 'high', 'medium', 'low']:
            count = stats['severity_distribution'].get(severity, 0)
            lines.append(f"| {severity} | {count} |")
        
        report = '\n'.join(lines)
        
        if output_path:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(report)
        
        return report


def error_handler_decorator(
    handler: Optional[EnhancedErrorHandler] = None,
    reraise: bool = True,
    notify: bool = True,
    save_report: bool = True
):
    """错误处理装饰器"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            nonlocal handler
            if handler is None:
                handler = EnhancedErrorHandler()
            
            try:
                return func(*args, **kwargs)
            except Exception as e:
                report = handler.handle_error(
                    e,
                    custom_context={"function": func.__name__},
                    save_report=save_report
                )
                
                if notify:
                    handler.notification_manager.notify_console(
                        report.error_context,
                        report.fix_suggestions
                    )
                
                if reraise:
                    raise
                
                return None
        
        return wrapper
    return decorator


def with_retry(
    max_retries: int = 3,
    exceptions: Tuple[Type[Exception], ...] = (Exception,),
    delay: float = 1.0,
    backoff: float = 2.0
):
    """重试装饰器"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            engine = EnhancedRecoveryEngine(max_retries=max_retries, retry_delay=delay)
            result, _ = engine.retry_with_backoff(
                func,
                *args,
                max_retries=max_retries,
                initial_delay=delay,
                backoff_factor=backoff,
                exceptions=exceptions,
                **kwargs
            )
            return result
        
        return wrapper
    return decorator


def with_fallback(fallback_func: Callable):
    """降级装饰器"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            engine = EnhancedRecoveryEngine()
            result, _ = engine.execute_with_fallback(
                func,
                fallback_func,
                *args,
                **kwargs
            )
            return result
        
        return wrapper
    return decorator


def with_circuit_breaker(
    circuit_id: str,
    failure_threshold: int = 5,
    recovery_timeout: float = 60.0
):
    """熔断器装饰器"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            engine = EnhancedRecoveryEngine()
            result, _ = engine.circuit_breaker_execute(
                func,
                circuit_id,
                failure_threshold,
                recovery_timeout,
                *args,
                **kwargs
            )
            return result
        
        return wrapper
    return decorator


def main():
    parser = argparse.ArgumentParser(
        description='错误智能处理系统 - 增强版'
    )
    parser.add_argument(
        'command',
        choices=['test', 'stats', 'report', 'demo', 'dashboard'],
        help='执行命令'
    )
    parser.add_argument(
        '--output-dir',
        default='./error_reports',
        help='输出目录'
    )
    parser.add_argument(
        '--format',
        choices=['json', 'markdown', 'html'],
        default='markdown',
        help='报告格式'
    )
    
    args = parser.parse_args()
    
    handler = EnhancedErrorHandler(output_dir=args.output_dir)
    
    if args.command == 'demo':
        print("=== 错误智能处理系统演示 ===\n")
        
        print("1. 测试错误捕获和分类...")
        try:
            raise ValueError("这是一个测试错误")
        except Exception as e:
            report = handler.handle_error(e, tags=["demo", "test"])
            print(f"   错误ID: {report.error_context.error_id}")
            print(f"   分类: {report.error_context.category.value}")
            print(f"   严重程度: {report.error_context.severity.value}")
            print(f"   修复建议数: {len(report.fix_suggestions)}")
            print(f"   线程状态数: {len(report.error_context.thread_states)}")
        
        print("\n2. 测试重试机制...")
        attempt_count = [0]
        
        def flaky_function():
            attempt_count[0] += 1
            if attempt_count[0] < 3:
                raise ConnectionError("模拟连接失败")
            return "成功"
        
        try:
            result, recovery = handler.recovery_engine.retry_with_backoff(
                flaky_function,
                max_retries=5,
                initial_delay=0.1
            )
            print(f"   重试成功: {result}")
            print(f"   尝试次数: {recovery.total_attempts}")
        except Exception as e:
            print(f"   重试失败: {e}")
        
        print("\n3. 测试降级机制...")
        
        def primary_func():
            raise RuntimeError("主函数失败")
        
        def fallback_func():
            return "降级结果"
        
        try:
            result, recovery = handler.recovery_engine.execute_with_fallback(
                primary_func,
                fallback_func
            )
            print(f"   降级成功: {result}")
        except Exception as e:
            print(f"   降级失败: {e}")
        
        print("\n4. 测试熔断器...")
        
        call_count = [0]
        
        def circuit_func():
            call_count[0] += 1
            if call_count[0] <= 3:
                raise ConnectionError("服务不可用")
            return "成功"
        
        try:
            result, _ = handler.recovery_engine.circuit_breaker_execute(
                circuit_func,
                "test_circuit",
                failure_threshold=5,
                recovery_timeout=1.0
            )
        except Exception:
            pass
        
        print(f"   熔断器状态: {handler.recovery_engine.circuit_breaker_state.get('test_circuit', {}).get('state', 'unknown')}")
        
        print("\n5. 生成统计报告...")
        stats = handler.get_statistics()
        print(f"   总错误数: {stats['total_errors']}")
        print(f"   恢复成功率: {stats['recovery_statistics']['success_rate']}%")
        
        print("\n演示完成!")
    
    elif args.command == 'dashboard':
        print(EnhancedErrorDetailPresenter.format_dashboard(handler.error_history))
    
    elif args.command == 'stats':
        stats = handler.get_statistics()
        print(json.dumps(stats, indent=2, ensure_ascii=False))
    
    elif args.command == 'report':
        report = handler.generate_summary_report()
        print(report)
    
    elif args.command == 'test':
        print("测试错误处理系统...")
        
        try:
            raise FileNotFoundError("测试文件不存在错误")
        except Exception as e:
            report = handler.handle_error(e)
            print(f"错误已处理: {report.error_context.error_id}")
            print(f"修复建议: {len(report.fix_suggestions)} 个")
            print(f"线程状态: {len(report.error_context.thread_states)} 个")
        
        print("测试完成!")
    
    return 0


if __name__ == '__main__':
    exit(main())
