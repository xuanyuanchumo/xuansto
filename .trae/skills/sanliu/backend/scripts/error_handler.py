#!/usr/bin/env python3
"""
错误智能处理系统
实现错误智能捕获、智能恢复和错误通知功能

功能模块:
1. 错误智能捕获 (Task 42)
   - 错误上下文记录（堆栈跟踪、变量状态、环境信息）
   - 错误报告生成（JSON、Markdown格式）
   - 错误分类（语法错误、运行时错误、逻辑错误、配置错误）

2. 错误智能恢复 (Task 43)
   - 自动恢复机制（重试、回退、降级）
   - 恢复过程记录
   - 增强恢复报告

3. 错误通知 (Task 44)
   - 错误通知机制（控制台、日志、文件）
   - 错误详情展示
   - 修复建议推送
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
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional, Callable, Type, Union, Tuple
from dataclasses import dataclass, field, asdict
from enum import Enum, auto
from collections import defaultdict
from functools import wraps
import argparse


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
    UNKNOWN = "unknown"


class ErrorSeverity(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class RecoveryStrategy(Enum):
    RETRY = "retry"
    ROLLBACK = "rollback"
    DEGRADE = "degrade"
    SKIP = "skip"
    ABORT = "abort"
    MANUAL = "manual"


class RecoveryStatus(Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    SUCCESS = "success"
    FAILED = "failed"
    PARTIAL = "partial"
    SKIPPED = "skipped"


class NotificationChannel(Enum):
    CONSOLE = "console"
    LOG = "log"
    FILE = "file"
    WEBHOOK = "webhook"
    EMAIL = "email"


@dataclass
class VariableState:
    name: str
    value: str
    value_type: str
    is_sensitive: bool = False


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


@dataclass
class RecoveryResult:
    error_id: str
    total_attempts: int
    successful: bool
    final_status: RecoveryStatus
    attempts: List[RecoveryAttempt]
    recovery_time_ms: int
    rollback_performed: bool = False


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


@dataclass
class NotificationRecord:
    notification_id: str
    channel: NotificationChannel
    error_id: str
    timestamp: str
    success: bool
    message: str
    recipient: Optional[str] = None


@dataclass
class ErrorReport:
    report_id: str
    generated_at: str
    error_context: ErrorContext
    recovery_result: Optional[RecoveryResult]
    fix_suggestions: List[FixSuggestion]
    notifications: List[NotificationRecord]


class ErrorContextRecorder:
    """错误上下文记录器 - Task 42.1"""
    
    SENSITIVE_PATTERNS = [
        r'password',
        r'secret',
        r'token',
        r'api_key',
        r'private_key',
        r'credential',
        r'auth',
    ]
    
    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root).resolve()
        self.error_counter = 0
    
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
            
            variables.append(VariableState(
                name=name,
                value=self._sanitize_value(value, name),
                value_type=type(value).__name__,
                is_sensitive=self._is_sensitive(name)
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
        
        return EnvironmentInfo(
            python_version=sys.version,
            platform_system=platform.system(),
            platform_machine=platform.machine(),
            working_directory=os.getcwd(),
            environment_variables=env_vars,
            installed_packages=installed_packages,
            timestamp=datetime.now().isoformat()
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
        
        category = ErrorClassifier.classify(exc)
        severity = ErrorClassifier.assess_severity(exc, category)
        
        related_files = []
        for frame in stack_frames:
            if frame.filename not in related_files and os.path.exists(frame.filename):
                related_files.append(frame.filename)
        
        return ErrorContext(
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
            tags=tags or []
        )


class ErrorClassifier:
    """错误分类器 - Task 42.3"""
    
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
        ErrorCategory.DATABASE: [
            Exception,
        ],
    }
    
    KEYWORD_PATTERNS = {
        ErrorCategory.NETWORK: [
            r'connection', r'socket', r'network', r'timeout', r'remote',
            r'http', r'url', r'request', r'response'
        ],
        ErrorCategory.DATABASE: [
            r'database', r'sql', r'query', r'table', r'column',
            r'constraint', r'integrity', r'db'
        ],
        ErrorCategory.FILE_SYSTEM: [
            r'file', r'directory', r'path', r'permission', r'access',
            r'read', r'write', r'open'
        ],
        ErrorCategory.CONFIGURATION: [
            r'config', r'setting', r'environment', r'variable',
            r'option', r'parameter'
        ],
        ErrorCategory.MEMORY: [
            r'memory', r'allocation', r'buffer', r'overflow'
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
        
        for category, patterns in cls.KEYWORD_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, combined, re.IGNORECASE):
                    return category
        
        return None
    
    @classmethod
    def assess_severity(cls, exc: Exception, category: ErrorCategory) -> ErrorSeverity:
        exc_type = type(exc)
        
        if issubclass(exc_type, (MemoryError, SystemError)):
            return ErrorSeverity.CRITICAL
        
        if category in [ErrorCategory.SYNTAX, ErrorCategory.CONFIGURATION]:
            return ErrorSeverity.HIGH
        
        if category in [ErrorCategory.DATABASE, ErrorCategory.NETWORK]:
            return ErrorSeverity.HIGH
        
        if issubclass(exc_type, (FileNotFoundError, PermissionError)):
            return ErrorSeverity.HIGH
        
        if issubclass(exc_type, (KeyError, IndexError, AttributeError)):
            return ErrorSeverity.MEDIUM
        
        if issubclass(exc_type, (ValueError, TypeError)):
            return ErrorSeverity.MEDIUM
        
        return ErrorSeverity.LOW


class ErrorReportGenerator:
    """错误报告生成器 - Task 42.2"""
    
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
                "timestamp": error_context.environment.timestamp,
            },
            "related_files": error_context.related_files,
            "custom_context": error_context.custom_context,
            "tags": error_context.tags
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
            "",
        ])
        
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
    
    def save_report(
        self,
        error_context: ErrorContext,
        format: str = "markdown",
        output_path: Optional[str] = None
    ) -> str:
        if format == "json":
            content = self.generate_json_report(error_context)
            ext = ".json"
        else:
            content = self.generate_markdown_report(error_context)
            ext = ".md"
        
        if not output_path:
            output_path = str(self.output_dir / f"error_report_{error_context.error_id}{ext}")
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        return output_path


class RecoveryEngine:
    """错误智能恢复引擎 - Task 43"""
    
    def __init__(self, max_retries: int = 3, retry_delay: float = 1.0):
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.recovery_counter = 0
        self.recovery_history: List[RecoveryResult] = []
        self.logger = logging.getLogger('RecoveryEngine')
    
    def _generate_attempt_id(self) -> str:
        self.recovery_counter += 1
        return f"RECOV-{datetime.now().strftime('%Y%m%d%H%M%S')}-{self.recovery_counter:04d}"
    
    def retry_with_backoff(
        self,
        func: Callable,
        *args,
        max_retries: Optional[int] = None,
        initial_delay: float = 1.0,
        backoff_factor: float = 2.0,
        max_delay: float = 60.0,
        exceptions: Tuple[Type[Exception], ...] = (Exception,),
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
                    duration_ms=int((time.time() - attempt_start) * 1000)
                )
                attempts.append(attempt)
                
                recovery_result = RecoveryResult(
                    error_id=error_id,
                    total_attempts=len(attempts),
                    successful=True,
                    final_status=RecoveryStatus.SUCCESS,
                    attempts=attempts,
                    recovery_time_ms=int((time.time() - start_time) * 1000)
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
                    duration_ms=int((time.time() - attempt_start) * 1000)
                )
                attempts.append(attempt)
                
                if attempt_num < max_retries - 1:
                    self.logger.warning(f"重试 {attempt_num + 1}/{max_retries} 失败，等待 {current_delay:.1f}s 后重试")
                    time.sleep(current_delay)
                    current_delay = min(current_delay * backoff_factor, max_delay)
        
        recovery_result = RecoveryResult(
            error_id=error_id,
            total_attempts=len(attempts),
            successful=False,
            final_status=RecoveryStatus.FAILED,
            attempts=attempts,
            recovery_time_ms=int((time.time() - start_time) * 1000)
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
            
            recovery_result = RecoveryResult(
                error_id=error_id,
                total_attempts=1,
                successful=True,
                final_status=RecoveryStatus.SUCCESS,
                attempts=attempts,
                recovery_time_ms=int((time.time() - start_time) * 1000)
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
                
                recovery_result = RecoveryResult(
                    error_id=error_id,
                    total_attempts=2,
                    successful=True,
                    final_status=RecoveryStatus.SUCCESS,
                    attempts=attempts,
                    recovery_time_ms=int((time.time() - start_time) * 1000)
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
                
                recovery_result = RecoveryResult(
                    error_id=error_id,
                    total_attempts=2,
                    successful=False,
                    final_status=RecoveryStatus.FAILED,
                    attempts=attempts,
                    recovery_time_ms=int((time.time() - start_time) * 1000)
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
            
            recovery_result = RecoveryResult(
                error_id=error_id,
                total_attempts=1,
                successful=True,
                final_status=RecoveryStatus.SUCCESS,
                attempts=attempts,
                recovery_time_ms=int((time.time() - start_time) * 1000),
                rollback_performed=False
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
            
            recovery_result = RecoveryResult(
                error_id=error_id,
                total_attempts=len(attempts),
                successful=False,
                final_status=RecoveryStatus.FAILED,
                attempts=attempts,
                recovery_time_ms=int((time.time() - start_time) * 1000),
                rollback_performed=True
            )
            
            self.recovery_history.append(recovery_result)
            raise
    
    def get_recovery_statistics(self) -> Dict[str, Any]:
        total = len(self.recovery_history)
        successful = sum(1 for r in self.recovery_history if r.successful)
        
        strategy_counts = defaultdict(int)
        for result in self.recovery_history:
            for attempt in result.attempts:
                strategy_counts[attempt.strategy.value] += 1
        
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
            "strategy_distribution": dict(strategy_counts)
        }


class RecoveryReportGenerator:
    """恢复报告生成器 - Task 43.3"""
    
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
                    "duration_ms": a.duration_ms
                }
                for a in recovery_result.attempts
            ]
        }
        
        return json.dumps(report, indent=2, ensure_ascii=False)
    
    def generate_markdown_report(self, recovery_result: RecoveryResult) -> str:
        status_icon = "✅" if recovery_result.successful else "❌"
        
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
            "",
            "## 恢复尝试详情",
            "",
        ]
        
        for i, attempt in enumerate(recovery_result.attempts, 1):
            icon = "✅" if attempt.success else "❌"
            lines.extend([
                f"### 尝试 {i}: {icon} {attempt.strategy.value}",
                "",
                f"| 属性 | 值 |",
                f"|------|-----|",
                f"| 策略 | {attempt.strategy.value} |",
                f"| 状态 | {attempt.status.value} |",
                f"| 时间 | {attempt.timestamp} |",
                f"| 耗时 | {attempt.duration_ms}ms |",
                f"| 详情 | {attempt.details} |",
            ])
            
            if attempt.error_message:
                lines.extend([
                    "",
                    f"**错误信息**: {attempt.error_message}",
                ])
            lines.append("")
        
        return '\n'.join(lines)


class NotificationManager:
    """错误通知管理器 - Task 44"""
    
    def __init__(self, log_dir: str = "."):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.notification_counter = 0
        self.notification_history: List[NotificationRecord] = []
        self.logger = self._setup_logger()
    
    def _setup_logger(self) -> logging.Logger:
        logger = logging.getLogger('ErrorNotification')
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
        
        if fix_suggestions:
            message_lines.append("\n修复建议:")
            for suggestion in fix_suggestions[:3]:
                message_lines.append(f"  - {suggestion.title}: {suggestion.description}")
        
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
        
        if error_context.severity == ErrorSeverity.CRITICAL:
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
        format: str = "markdown"
    ) -> NotificationRecord:
        notification_id = self._generate_notification_id()
        
        if not output_path:
            output_path = str(self.log_dir / f"error_{error_context.error_id}.{format}")
        
        try:
            report_gen = ErrorReportGenerator(str(self.log_dir))
            content = report_gen.generate_markdown_report(error_context) if format == "markdown" else report_gen.generate_json_report(error_context)
            
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
        
        return records


class FixSuggestionEngine:
    """修复建议引擎 - Task 44.3"""
    
    SUGGESTION_RULES = {
        ErrorCategory.SYNTAX: [
            {
                "title": "检查语法错误",
                "description": "仔细检查代码语法，确保括号、引号、缩进等正确",
                "priority": 1,
                "code_example": "# 使用 linter 工具检查语法\npython -m py_compile your_file.py",
                "confidence": 0.9
            }
        ],
        ErrorCategory.RUNTIME: [
            {
                "title": "添加异常处理",
                "description": "使用 try-except 块捕获可能的运行时异常",
                "priority": 1,
                "code_example": "try:\n    # 可能出错的代码\nexcept Exception as e:\n    logger.error(f'Error: {e}')",
                "confidence": 0.8
            },
            {
                "title": "检查变量类型",
                "description": "确保变量类型正确，使用 isinstance() 进行类型检查",
                "priority": 2,
                "code_example": "if not isinstance(value, expected_type):\n    raise TypeError(f'Expected {expected_type}, got {type(value)}')",
                "confidence": 0.7
            }
        ],
        ErrorCategory.FILE_SYSTEM: [
            {
                "title": "检查文件路径",
                "description": "确认文件路径存在且可访问",
                "priority": 1,
                "code_example": "import os\nif not os.path.exists(file_path):\n    raise FileNotFoundError(f'File not found: {file_path}')",
                "confidence": 0.9
            },
            {
                "title": "检查文件权限",
                "description": "确保有足够的权限访问文件",
                "priority": 2,
                "code_example": "import os\nif not os.access(file_path, os.R_OK):\n    raise PermissionError(f'No read permission: {file_path}')",
                "confidence": 0.8
            }
        ],
        ErrorCategory.NETWORK: [
            {
                "title": "添加重试机制",
                "description": "网络请求可能因临时问题失败，添加重试逻辑",
                "priority": 1,
                "code_example": "import time\nfor attempt in range(max_retries):\n    try:\n        response = requests.get(url)\n        break\n    except requests.RequestException:\n        time.sleep(2 ** attempt)",
                "confidence": 0.9
            },
            {
                "title": "设置超时",
                "description": "为网络请求设置合理的超时时间",
                "priority": 2,
                "code_example": "response = requests.get(url, timeout=30)",
                "confidence": 0.8
            }
        ],
        ErrorCategory.DATABASE: [
            {
                "title": "使用事务",
                "description": "数据库操作使用事务确保数据一致性",
                "priority": 1,
                "code_example": "with db.transaction():\n    db.execute(query)",
                "confidence": 0.8
            },
            {
                "title": "检查连接",
                "description": "确保数据库连接有效",
                "priority": 2,
                "code_example": "try:\n    db.ping()\nexcept:\n    db.reconnect()",
                "confidence": 0.7
            }
        ],
        ErrorCategory.CONFIGURATION: [
            {
                "title": "验证配置",
                "description": "检查配置文件格式和必需字段",
                "priority": 1,
                "code_example": "required_keys = ['host', 'port', 'database']\nfor key in required_keys:\n    if key not in config:\n        raise ValueError(f'Missing config: {key}')",
                "confidence": 0.9
            }
        ],
        ErrorCategory.MEMORY: [
            {
                "title": "优化内存使用",
                "description": "使用生成器替代列表，及时释放大对象",
                "priority": 1,
                "code_example": "# 使用生成器\nfor item in generator():\n    process(item)\n\n# 释放大对象\ndel large_object",
                "confidence": 0.8
            }
        ],
        ErrorCategory.DEPENDENCY: [
            {
                "title": "安装缺失依赖",
                "description": "检查并安装缺失的Python包",
                "priority": 1,
                "code_example": "pip install missing_package\n# 或在 requirements.txt 中添加依赖",
                "confidence": 0.9
            }
        ],
    }
    
    ERROR_TYPE_SUGGESTIONS = {
        "KeyError": {
            "title": "检查字典键",
            "description": "使用 .get() 方法或检查键是否存在",
            "priority": 1,
            "code_example": "value = my_dict.get('key', default_value)\n# 或\nif 'key' in my_dict:\n    value = my_dict['key']",
            "confidence": 0.9
        },
        "IndexError": {
            "title": "检查索引范围",
            "description": "访问列表前检查索引是否有效",
            "priority": 1,
            "code_example": "if 0 <= index < len(my_list):\n    value = my_list[index]",
            "confidence": 0.9
        },
        "AttributeError": {
            "title": "检查对象属性",
            "description": "使用 hasattr() 检查属性是否存在",
            "priority": 1,
            "code_example": "if hasattr(obj, 'attribute'):\n    value = obj.attribute",
            "confidence": 0.9
        },
        "TypeError": {
            "title": "检查类型兼容性",
            "description": "确保操作数类型正确",
            "priority": 1,
            "code_example": "if isinstance(value, expected_type):\n    result = operation(value)",
            "confidence": 0.8
        },
        "ValueError": {
            "title": "验证输入值",
            "description": "在处理前验证值的有效性",
            "priority": 1,
            "code_example": "if not is_valid(value):\n    raise ValueError('Invalid value')",
            "confidence": 0.8
        },
        "PermissionError": {
            "title": "检查权限",
            "description": "确保有足够的权限执行操作",
            "priority": 1,
            "code_example": "import os\nos.chmod(file_path, 0o644)",
            "confidence": 0.9
        },
        "FileNotFoundError": {
            "title": "创建缺失文件",
            "description": "如果文件不存在，创建它或使用默认值",
            "priority": 1,
            "code_example": "import os\nif not os.path.exists(file_path):\n    with open(file_path, 'w') as f:\n        f.write(default_content)",
            "confidence": 0.9
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
                confidence=rule.get("confidence", 0.8)
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
                    confidence=rule.get("confidence", 0.8)
                ))
        
        suggestions.sort(key=lambda x: x.priority)
        
        return suggestions[:5]


class ErrorDetailPresenter:
    """错误详情展示器 - Task 44.2"""
    
    @staticmethod
    def format_for_console(error_context: ErrorContext) -> str:
        severity_icons = {
            ErrorSeverity.LOW: "ℹ️",
            ErrorSeverity.MEDIUM: "⚠️",
            ErrorSeverity.HIGH: "🔴",
            ErrorSeverity.CRITICAL: "💀",
        }
        
        icon = severity_icons.get(error_context.severity, "❓")
        
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
        
        if error_context.stack_frames:
            lines.append("调用栈:")
            for i, frame in enumerate(error_context.stack_frames[:5], 1):
                lines.append(f"  {i}. {frame.filename}:{frame.line_number} in {frame.function_name}()")
        
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
        
        category_counts = defaultdict(int)
        severity_counts = defaultdict(int)
        
        for ctx in error_contexts:
            category_counts[ctx.category.value] += 1
            severity_counts[ctx.severity.value] += 1
        
        lines = [
            f"错误统计 (共 {len(error_contexts)} 个)",
            f"{'─'*30}",
            "",
            "按分类:",
        ]
        
        for category, count in sorted(category_counts.items(), key=lambda x: -x[1]):
            lines.append(f"  {category}: {count}")
        
        lines.append("")
        lines.append("按严重程度:")
        
        for severity in [ErrorSeverity.CRITICAL, ErrorSeverity.HIGH, ErrorSeverity.MEDIUM, ErrorSeverity.LOW]:
            count = severity_counts.get(severity.value, 0)
            if count > 0:
                lines.append(f"  {severity.value}: {count}")
        
        return '\n'.join(lines)


class ErrorHandler:
    """统一错误处理器 - 整合所有错误处理功能"""
    
    def __init__(
        self,
        project_root: str = ".",
        output_dir: str = ".",
        max_retries: int = 3
    ):
        self.project_root = Path(project_root).resolve()
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.context_recorder = ErrorContextRecorder(project_root)
        self.report_generator = ErrorReportGenerator(str(self.output_dir))
        self.recovery_engine = RecoveryEngine(max_retries=max_retries)
        self.recovery_report_gen = RecoveryReportGenerator()
        self.notification_manager = NotificationManager(str(self.output_dir))
        self.suggestion_engine = FixSuggestionEngine()
        
        self.error_history: List[ErrorContext] = []
        self.logger = self._setup_logger()
    
    def _setup_logger(self) -> logging.Logger:
        logger = logging.getLogger('ErrorHandler')
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
        save_report: bool = True
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
            report_path = self.report_generator.save_report(error_context, format="markdown")
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
        
        if recovery_func and recovery_strategy == RecoveryStrategy.RETRY:
            try:
                _, recovery_result = self.recovery_engine.retry_with_backoff(
                    recovery_func
                )
            except Exception:
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
        category_counts = defaultdict(int)
        severity_counts = defaultdict(int)
        
        for ctx in self.error_history:
            category_counts[ctx.category.value] += 1
            severity_counts[ctx.severity.value] += 1
        
        recovery_stats = self.recovery_engine.get_recovery_statistics()
        
        return {
            "total_errors": len(self.error_history),
            "category_distribution": dict(category_counts),
            "severity_distribution": dict(severity_counts),
            "recovery_statistics": recovery_stats
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
        
        for severity in ['critical', 'high', 'medium', 'low']:
            count = stats['severity_distribution'].get(severity, 0)
            lines.append(f"| {severity} | {count} |")
        
        report = '\n'.join(lines)
        
        if output_path:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(report)
        
        return report


def error_handler_decorator(
    handler: Optional[ErrorHandler] = None,
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
                handler = ErrorHandler()
            
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
            engine = RecoveryEngine(max_retries=max_retries, retry_delay=delay)
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
            engine = RecoveryEngine()
            result, _ = engine.execute_with_fallback(
                func,
                fallback_func,
                *args,
                **kwargs
            )
            return result
        
        return wrapper
    return decorator


def main():
    parser = argparse.ArgumentParser(
        description='错误智能处理系统'
    )
    parser.add_argument(
        'command',
        choices=['test', 'stats', 'report', 'demo'],
        help='执行命令'
    )
    parser.add_argument(
        '--output-dir',
        default='./error_reports',
        help='输出目录'
    )
    parser.add_argument(
        '--format',
        choices=['json', 'markdown'],
        default='markdown',
        help='报告格式'
    )
    
    args = parser.parse_args()
    
    handler = ErrorHandler(output_dir=args.output_dir)
    
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
        
        print("\n4. 生成统计报告...")
        stats = handler.get_statistics()
        print(f"   总错误数: {stats['total_errors']}")
        print(f"   恢复成功率: {stats['recovery_statistics']['success_rate']}%")
        
        print("\n演示完成!")
    
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
            print(f"修复建议: {len(report.fix_suggestions)} 条")
        
        print("测试完成!")
    
    return 0


if __name__ == '__main__':
    exit(main())
