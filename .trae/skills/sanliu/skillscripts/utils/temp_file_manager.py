#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
三省六部协同开发系统 - 增强临时文件管理器

实现自迭代临时文件策略：
- 临时文件命名策略：<原文件名>_temp_<timestamp>.<扩展名>
- 原子性文件替换机制（创建临时文件→等待→删除旧文件→重命名临时文件）
- 冲突检测和等待机制
- 临时文件清理机制
- 运行状态检测（检测脚本是否正在执行）
- 超时等待机制（指数退避策略）
- 自迭代安全保护
- 跨平台文件锁定检测

使用示例:
    from temp_file_manager import TempFileManager
    
    manager = TempFileManager()
    
    # 创建临时文件
    temp_path = manager.create_temp_file("script.py")
    
    # 检测文件是否在使用
    if not manager.is_file_in_use(temp_path):
        # 原子性替换
        manager.atomic_replace(temp_path, "script.py")
    
    # 检测脚本是否正在运行
    if manager.is_script_running("script.py"):
        manager.wait_for_script_stop("script.py", timeout=60)
    
    # 安全替换（包含脚本运行检测）
    result = manager.safe_atomic_replace(temp_path, "script.py")
    
    # 清理过期临时文件
    manager.cleanup_temp_files("./")

CLI使用:
    python temp_file_manager.py create script.py --content "print('hello')"
    python temp_file_manager.py replace script.py.tmp script.py --wait-script
    python temp_file_manager.py check script.py
    python temp_file_manager.py cleanup ./ --expire 3600
"""

import os
import time
import shutil
import tempfile
import threading
import subprocess
import hashlib
import json
import sys
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Set, Callable, Any, Tuple, Union, TypeVar
from contextlib import contextmanager
from enum import Enum
import platform
import logging
import argparse
import signal
import atexit
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeoutError
from functools import wraps

if platform.system() == 'Windows':
    import msvcrt
    try:
        import psutil
        HAS_PSUTIL = True
    except ImportError:
        HAS_PSUTIL = False
else:
    import fcntl
    try:
        import psutil
        HAS_PSUTIL = True
    except ImportError:
        HAS_PSUTIL = False

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - [%(name)s] %(message)s'
)
logger = logging.getLogger(__name__)


class ScriptStatus(Enum):
    RUNNING = "running"
    STOPPED = "stopped"
    UNKNOWN = "unknown"
    ERROR = "error"
    STARTING = "starting"
    STOPPING = "stopping"


class TempFileState(Enum):
    CREATED = "created"
    IN_USE = "in_use"
    READY_FOR_REPLACE = "ready_for_replace"
    REPLACED = "replaced"
    CLEANED = "cleaned"
    ERROR = "error"
    PENDING = "pending"
    LOCKED = "locked"


class FileLockStatus(Enum):
    UNLOCKED = "unlocked"
    LOCKED = "locked"
    UNKNOWN = "unknown"


class WaitStrategy(Enum):
    LINEAR = "linear"
    EXPONENTIAL = "exponential"
    FIXED = "fixed"
    EXPONENTIAL_JITTER = "exponential_jitter"
    ADAPTIVE = "adaptive"
    FIBONACCI = "fibonacci"


class ConflictType(Enum):
    FILE_LOCK = "file_lock"
    PROCESS_RUNNING = "process_running"
    TEMP_FILE_EXISTS = "temp_file_exists"
    PERMISSION_DENIED = "permission_denied"
    DISK_SPACE = "disk_space"
    NETWORK_SHARE = "network_share"
    ANTIVIRUS_LOCK = "antivirus_lock"
    IDE_LOCK = "ide_lock"
    UNKNOWN = "unknown"


class ConflictSeverity(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class CleanupPriority(Enum):
    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4


class VerificationLevel(Enum):
    NONE = "none"
    BASIC = "basic"
    HASH = "hash"
    FULL = "full"
    MULTI_STAGE = "multi_stage"


class ConflictResolutionAction(Enum):
    """冲突解决动作类型"""
    WAIT = "wait"
    RETRY = "retry"
    FORCE_RELEASE = "force_release"
    TERMINATE_PROCESS = "terminate_process"
    SKIP = "skip"
    ABORT = "abort"
    DEFER = "defer"
    NOTIFY_USER = "notify_user"


class RetryPolicy(Enum):
    """重试策略类型"""
    NONE = "none"
    SIMPLE = "simple"
    EXPONENTIAL_BACKOFF = "exponential_backoff"
    LINEAR_BACKOFF = "linear_backoff"
    FIXED_INTERVAL = "fixed_interval"
    JITTER = "jitter"
    CIRCUIT_BREAKER = "circuit_breaker"


class ProcessState(Enum):
    """进程状态类型"""
    INITIALIZING = "initializing"
    RUNNING = "running"
    IDLE = "idle"
    BUSY = "busy"
    BLOCKED = "blocked"
    ZOMBIE = "zombie"
    TERMINATING = "terminating"
    STOPPED = "stopped"
    UNKNOWN = "unknown"


class CleanupTrigger(Enum):
    """清理触发条件"""
    MANUAL = "manual"
    SCHEDULED = "scheduled"
    THRESHOLD = "threshold"
    SHUTDOWN = "shutdown"
    ERROR = "error"
    DISK_FULL = "disk_full"
    AGE_BASED = "age_based"
    SIZE_BASED = "size_based"


@dataclass
class TempFileInfo:
    temp_path: str
    original_path: str
    created_at: datetime
    registered: bool = True
    last_access: datetime = None
    state: TempFileState = TempFileState.CREATED
    content_hash: str = ""
    size_bytes: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)
    lock_status: FileLockStatus = FileLockStatus.UNKNOWN
    retry_count: int = 0
    
    def __post_init__(self):
        if self.last_access is None:
            self.last_access = self.created_at


@dataclass
class TempFileResult:
    success: bool
    message: str
    temp_path: Optional[str] = None
    error: Optional[str] = None
    state: TempFileState = TempFileState.CREATED


@dataclass
class ScriptRunInfo:
    script_path: str
    pid: Optional[int] = None
    start_time: Optional[datetime] = None
    status: ScriptStatus = ScriptStatus.UNKNOWN
    command_line: str = ""
    cpu_percent: float = 0.0
    memory_mb: float = 0.0
    threads: int = 1
    user: str = ""


@dataclass
class WaitResult:
    success: bool
    waited_seconds: float
    timeout: bool = False
    final_status: ScriptStatus = ScriptStatus.UNKNOWN
    error: Optional[str] = None
    iterations: int = 0
    strategy_used: WaitStrategy = WaitStrategy.LINEAR


@dataclass
class AtomicReplaceResult:
    success: bool
    message: str
    backup_path: Optional[str] = None
    verified: bool = False
    rollback_available: bool = False
    error: Optional[str] = None
    waited_for_script: bool = False
    script_wait_seconds: float = 0.0
    file_wait_seconds: float = 0.0


@dataclass
class FileLockResult:
    locked: bool
    lock_holder: Optional[str] = None
    lock_time: Optional[datetime] = None
    error: Optional[str] = None


@dataclass
class ConflictInfo:
    conflict_type: ConflictType
    severity: ConflictSeverity
    file_path: str
    detected_at: datetime
    holder_info: Optional[str] = None
    suggested_action: str = ""
    auto_resolvable: bool = True
    retry_count: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ConflictDetectionResult:
    has_conflict: bool
    conflicts: List[ConflictInfo] = field(default_factory=list)
    total_severity: ConflictSeverity = ConflictSeverity.LOW
    resolution_suggestions: List[str] = field(default_factory=list)
    predicted_conflicts: List[ConflictInfo] = field(default_factory=list)


@dataclass
class ProcessHealthInfo:
    pid: int
    script_path: str
    status: ScriptStatus
    cpu_percent: float = 0.0
    memory_mb: float = 0.0
    thread_count: int = 1
    file_descriptors: int = 0
    io_read_mb: float = 0.0
    io_write_mb: float = 0.0
    uptime_seconds: float = 0.0
    is_responsive: bool = True
    last_activity: Optional[datetime] = None
    resource_trend: str = "stable"
    health_score: float = 100.0


@dataclass
class AdaptiveWaitState:
    initial_interval: float = 0.5
    current_interval: float = 0.5
    max_interval: float = 10.0
    total_waited: float = 0.0
    iterations: int = 0
    successes: int = 0
    failures: int = 0
    last_adjustment: Optional[datetime] = None
    jitter_factor: float = 0.1


@dataclass
class VerificationResult:
    success: bool
    level: VerificationLevel
    original_hash: str = ""
    final_hash: str = ""
    size_match: bool = True
    content_match: bool = True
    permissions_preserved: bool = True
    timestamp_preserved: bool = True
    stages_passed: int = 0
    total_stages: int = 0
    error_details: List[str] = field(default_factory=list)


@dataclass
class CleanupPolicy:
    max_age_seconds: int = 3600
    max_total_size_mb: float = 100.0
    priority: CleanupPriority = CleanupPriority.NORMAL
    preserve_patterns: List[str] = field(default_factory=list)
    aggressive_mode: bool = False
    min_disk_free_mb: float = 500.0
    cleanup_interval: int = 300


@dataclass
class ConflictResolution:
    """冲突解决方案"""
    action: ConflictResolutionAction
    reason: str
    estimated_time: float = 0.0
    auto_execute: bool = True
    requires_user_confirmation: bool = False
    fallback_action: Optional['ConflictResolutionAction'] = None
    parameters: Dict[str, Any] = field(default_factory=dict)


@dataclass
class RetryConfig:
    """重试配置"""
    policy: RetryPolicy = RetryPolicy.EXPONENTIAL_BACKOFF
    max_retries: int = 10
    initial_delay: float = 0.5
    max_delay: float = 30.0
    backoff_factor: float = 2.0
    jitter_range: float = 0.1
    retryable_errors: List[str] = field(default_factory=lambda: [
        "FILE_IN_USE", "PERMISSION_DENIED", "TIMEOUT", "LOCK_ERROR"
    ])
    on_max_retries: ConflictResolutionAction = ConflictResolutionAction.ABORT


@dataclass
class RetryState:
    """重试状态"""
    attempt: int = 0
    last_error: Optional[str] = None
    last_attempt_time: Optional[datetime] = None
    total_wait_time: float = 0.0
    success_history: List[bool] = field(default_factory=list)
    error_history: List[str] = field(default_factory=list)


@dataclass
class ProcessStateInfo:
    """进程状态详细信息"""
    pid: int
    script_path: str
    state: ProcessState
    cpu_percent: float = 0.0
    memory_mb: float = 0.0
    thread_count: int = 1
    file_handles: int = 0
    io_read_bytes: int = 0
    io_write_bytes: int = 0
    uptime_seconds: float = 0.0
    is_responsive: bool = True
    last_activity: Optional[datetime] = None
    predicted_completion: Optional[float] = None
    resource_trend: str = "stable"
    health_score: float = 100.0
    child_processes: List[int] = field(default_factory=list)
    open_files: List[str] = field(default_factory=list)


@dataclass
class SmartWaitResult:
    """智能等待结果"""
    success: bool
    waited_seconds: float
    iterations: int
    strategy_used: WaitStrategy
    final_state: Any = None
    timeout: bool = False
    error: Optional[str] = None
    retry_count: int = 0
    resolution_applied: Optional[ConflictResolution] = None


@dataclass
class AtomicVerificationContext:
    """原子验证上下文"""
    source_path: str
    target_path: str
    source_hash: str
    source_size: int
    source_permissions: Optional[int]
    source_timestamp: Optional[float]
    backup_path: Optional[str]
    verification_stages: List[str] = field(default_factory=list)
    current_stage: int = 0
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


@dataclass
class CleanupResult:
    """清理结果"""
    trigger: CleanupTrigger
    cleaned_files: List[str] = field(default_factory=list)
    skipped_files: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    total_size_freed: int = 0
    duration_seconds: float = 0.0
    policy_used: Optional[CleanupPolicy] = None


@dataclass
class CleanupSchedule:
    """清理调度配置"""
    directories: List[str]
    interval_seconds: int = 300
    policy: CleanupPolicy = field(default_factory=CleanupPolicy)
    enabled: bool = True
    last_run: Optional[datetime] = None
    next_run: Optional[datetime] = None
    run_count: int = 0
    total_freed_mb: float = 0.0


@dataclass
class TimeoutConfig:
    file_wait_timeout: float = 30.0
    script_wait_timeout: float = 60.0
    retry_interval: float = 0.5
    max_retry_interval: float = 5.0
    exponential_base: float = 1.5
    max_retries: int = 100
    strategy: WaitStrategy = WaitStrategy.EXPONENTIAL
    jitter_enabled: bool = True
    jitter_factor: float = 0.1
    adaptive_threshold: float = 0.7
    fibonacci_limit: int = 20


class ConflictResolver:
    """智能冲突解决器 - 分析冲突并提供解决方案"""
    
    def __init__(self):
        self._resolution_history: List[Tuple[ConflictInfo, ConflictResolution]] = []
        self._max_history = 200
        self._auto_resolution_rules = self._build_auto_resolution_rules()
    
    def _build_auto_resolution_rules(self) -> Dict[ConflictType, Dict[ConflictSeverity, ConflictResolutionAction]]:
        """构建自动解决规则"""
        return {
            ConflictType.FILE_LOCK: {
                ConflictSeverity.LOW: ConflictResolutionAction.WAIT,
                ConflictSeverity.MEDIUM: ConflictResolutionAction.WAIT,
                ConflictSeverity.HIGH: ConflictResolutionAction.RETRY,
                ConflictSeverity.CRITICAL: ConflictResolutionAction.NOTIFY_USER,
            },
            ConflictType.PROCESS_RUNNING: {
                ConflictSeverity.LOW: ConflictResolutionAction.WAIT,
                ConflictSeverity.MEDIUM: ConflictResolutionAction.WAIT,
                ConflictSeverity.HIGH: ConflictResolutionAction.TERMINATE_PROCESS,
                ConflictSeverity.CRITICAL: ConflictResolutionAction.NOTIFY_USER,
            },
            ConflictType.TEMP_FILE_EXISTS: {
                ConflictSeverity.LOW: ConflictResolutionAction.SKIP,
                ConflictSeverity.MEDIUM: ConflictResolutionAction.RETRY,
                ConflictSeverity.HIGH: ConflictResolutionAction.FORCE_RELEASE,
                ConflictSeverity.CRITICAL: ConflictResolutionAction.FORCE_RELEASE,
            },
            ConflictType.PERMISSION_DENIED: {
                ConflictSeverity.LOW: ConflictResolutionAction.RETRY,
                ConflictSeverity.MEDIUM: ConflictResolutionAction.NOTIFY_USER,
                ConflictSeverity.HIGH: ConflictResolutionAction.ABORT,
                ConflictSeverity.CRITICAL: ConflictResolutionAction.ABORT,
            },
            ConflictType.DISK_SPACE: {
                ConflictSeverity.LOW: ConflictResolutionAction.DEFER,
                ConflictSeverity.MEDIUM: ConflictResolutionAction.FORCE_RELEASE,
                ConflictSeverity.HIGH: ConflictResolutionAction.FORCE_RELEASE,
                ConflictSeverity.CRITICAL: ConflictResolutionAction.ABORT,
            },
            ConflictType.NETWORK_SHARE: {
                ConflictSeverity.LOW: ConflictResolutionAction.WAIT,
                ConflictSeverity.MEDIUM: ConflictResolutionAction.RETRY,
                ConflictSeverity.HIGH: ConflictResolutionAction.NOTIFY_USER,
                ConflictSeverity.CRITICAL: ConflictResolutionAction.ABORT,
            },
            ConflictType.ANTIVIRUS_LOCK: {
                ConflictSeverity.LOW: ConflictResolutionAction.WAIT,
                ConflictSeverity.MEDIUM: ConflictResolutionAction.WAIT,
                ConflictSeverity.HIGH: ConflictResolutionAction.WAIT,
                ConflictSeverity.CRITICAL: ConflictResolutionAction.NOTIFY_USER,
            },
            ConflictType.IDE_LOCK: {
                ConflictSeverity.LOW: ConflictResolutionAction.WAIT,
                ConflictSeverity.MEDIUM: ConflictResolutionAction.WAIT,
                ConflictSeverity.HIGH: ConflictResolutionAction.NOTIFY_USER,
                ConflictSeverity.CRITICAL: ConflictResolutionAction.NOTIFY_USER,
            },
        }
    
    def analyze_conflict(self, conflict: ConflictInfo) -> ConflictResolution:
        """分析冲突并生成解决方案"""
        action = self._determine_action(conflict)
        
        resolution = ConflictResolution(
            action=action,
            reason=self._generate_reason(conflict, action),
            estimated_time=self._estimate_resolution_time(conflict, action),
            auto_execute=self._should_auto_execute(conflict, action),
            requires_user_confirmation=self._requires_confirmation(conflict, action),
            fallback_action=self._get_fallback_action(conflict, action),
            parameters=self._generate_parameters(conflict, action)
        )
        
        self._record_resolution(conflict, resolution)
        return resolution
    
    def _determine_action(self, conflict: ConflictInfo) -> ConflictResolutionAction:
        """确定解决动作"""
        if conflict.conflict_type in self._auto_resolution_rules:
            severity_rules = self._auto_resolution_rules[conflict.conflict_type]
            if conflict.severity in severity_rules:
                return severity_rules[conflict.severity]
        
        if not conflict.auto_resolvable:
            return ConflictResolutionAction.NOTIFY_USER
        
        return ConflictResolutionAction.WAIT
    
    def _generate_reason(self, conflict: ConflictInfo, action: ConflictResolutionAction) -> str:
        """生成解决原因说明"""
        reasons = {
            ConflictResolutionAction.WAIT: f"等待{conflict.conflict_type.value}解除",
            ConflictResolutionAction.RETRY: f"重试操作以解决{conflict.conflict_type.value}",
            ConflictResolutionAction.FORCE_RELEASE: f"强制释放{conflict.conflict_type.value}",
            ConflictResolutionAction.TERMINATE_PROCESS: f"终止占用进程以解决{conflict.conflict_type.value}",
            ConflictResolutionAction.SKIP: f"跳过当前{conflict.conflict_type.value}",
            ConflictResolutionAction.ABORT: f"因{conflict.conflict_type.value}严重程度过高而中止",
            ConflictResolutionAction.DEFER: f"推迟处理{conflict.conflict_type.value}",
            ConflictResolutionAction.NOTIFY_USER: f"需要用户干预解决{conflict.conflict_type.value}",
        }
        return reasons.get(action, "未知原因")
    
    def _estimate_resolution_time(self, conflict: ConflictInfo, action: ConflictResolutionAction) -> float:
        """估算解决时间"""
        time_estimates = {
            ConflictResolutionAction.WAIT: 5.0,
            ConflictResolutionAction.RETRY: 2.0,
            ConflictResolutionAction.FORCE_RELEASE: 1.0,
            ConflictResolutionAction.TERMINATE_PROCESS: 3.0,
            ConflictResolutionAction.SKIP: 0.0,
            ConflictResolutionAction.ABORT: 0.0,
            ConflictResolutionAction.DEFER: 60.0,
            ConflictResolutionAction.NOTIFY_USER: -1.0,
        }
        
        base_time = time_estimates.get(action, 5.0)
        
        if conflict.severity == ConflictSeverity.HIGH:
            base_time *= 2
        elif conflict.severity == ConflictSeverity.CRITICAL:
            base_time *= 3
        
        return base_time
    
    def _should_auto_execute(self, conflict: ConflictInfo, action: ConflictResolutionAction) -> bool:
        """判断是否应自动执行"""
        auto_actions = {
            ConflictResolutionAction.WAIT,
            ConflictResolutionAction.RETRY,
            ConflictResolutionAction.SKIP,
        }
        
        if action in auto_actions and conflict.auto_resolvable:
            return True
        
        if conflict.severity in [ConflictSeverity.LOW, ConflictSeverity.MEDIUM]:
            return action != ConflictResolutionAction.TERMINATE_PROCESS
        
        return False
    
    def _requires_confirmation(self, conflict: ConflictInfo, action: ConflictResolutionAction) -> bool:
        """判断是否需要用户确认"""
        confirm_actions = {
            ConflictResolutionAction.TERMINATE_PROCESS,
            ConflictResolutionAction.FORCE_RELEASE,
            ConflictResolutionAction.ABORT,
        }
        
        if action in confirm_actions:
            return True
        
        if conflict.severity == ConflictSeverity.CRITICAL:
            return True
        
        return False
    
    def _get_fallback_action(self, conflict: ConflictInfo, action: ConflictResolutionAction) -> Optional[ConflictResolutionAction]:
        """获取备用动作"""
        fallback_map = {
            ConflictResolutionAction.WAIT: ConflictResolutionAction.RETRY,
            ConflictResolutionAction.RETRY: ConflictResolutionAction.NOTIFY_USER,
            ConflictResolutionAction.FORCE_RELEASE: ConflictResolutionAction.ABORT,
            ConflictResolutionAction.TERMINATE_PROCESS: ConflictResolutionAction.NOTIFY_USER,
            ConflictResolutionAction.SKIP: None,
            ConflictResolutionAction.ABORT: None,
            ConflictResolutionAction.DEFER: ConflictResolutionAction.WAIT,
            ConflictResolutionAction.NOTIFY_USER: ConflictResolutionAction.ABORT,
        }
        return fallback_map.get(action)
    
    def _generate_parameters(self, conflict: ConflictInfo, action: ConflictResolutionAction) -> Dict[str, Any]:
        """生成解决参数"""
        params = {}
        
        if action == ConflictResolutionAction.WAIT:
            params['timeout'] = 30.0
            params['interval'] = 0.5
            params['strategy'] = WaitStrategy.EXPONENTIAL.value
        
        elif action == ConflictResolutionAction.RETRY:
            params['max_retries'] = 3
            params['delay'] = 1.0
        
        elif action == ConflictResolutionAction.TERMINATE_PROCESS:
            if conflict.metadata.get('pid'):
                params['pid'] = conflict.metadata['pid']
            params['force'] = conflict.severity == ConflictSeverity.CRITICAL
        
        elif action == ConflictResolutionAction.FORCE_RELEASE:
            params['file_path'] = conflict.file_path
        
        if conflict.holder_info:
            params['holder_info'] = conflict.holder_info
        
        return params
    
    def _record_resolution(self, conflict: ConflictInfo, resolution: ConflictResolution):
        """记录解决历史"""
        self._resolution_history.append((conflict, resolution))
        if len(self._resolution_history) > self._max_history:
            self._resolution_history = self._resolution_history[-self._max_history:]
    
    def get_resolution_history(self, limit: int = 50) -> List[Tuple[ConflictInfo, ConflictResolution]]:
        """获取解决历史"""
        return self._resolution_history[-limit:]
    
    def batch_analyze(self, conflicts: List[ConflictInfo]) -> List[ConflictResolution]:
        """批量分析冲突"""
        return [self.analyze_conflict(c) for c in conflicts]
    
    def get_best_resolution(self, conflicts: List[ConflictInfo]) -> Optional[ConflictResolution]:
        """获取最佳解决方案（针对多个冲突）"""
        if not conflicts:
            return None
        
        resolutions = self.batch_analyze(conflicts)
        
        severity_order = [
            ConflictSeverity.CRITICAL,
            ConflictSeverity.HIGH,
            ConflictSeverity.MEDIUM,
            ConflictSeverity.LOW,
        ]
        
        for severity in severity_order:
            for conflict, resolution in zip(conflicts, resolutions):
                if conflict.severity == severity:
                    return resolution
        
        return resolutions[0] if resolutions else None


class RetryManager:
    """重试管理器 - 管理重试逻辑和状态"""
    
    def __init__(self, config: Optional[RetryConfig] = None):
        self.config = config or RetryConfig()
        self._state = RetryState()
        self._circuit_open = False
        self._circuit_open_time: Optional[datetime] = None
        self._circuit_reset_timeout = 60.0
    
    def should_retry(self, error: str) -> bool:
        """判断是否应该重试"""
        if self._circuit_open:
            if self._should_attempt_circuit_reset():
                self._reset_circuit()
            else:
                return False
        
        if self._state.attempt >= self.config.max_retries:
            return False
        
        for retryable_error in self.config.retryable_errors:
            if retryable_error.lower() in error.lower():
                return True
        
        return False
    
    def _should_attempt_circuit_reset(self) -> bool:
        """判断是否应该尝试重置熔断器"""
        if not self._circuit_open_time:
            return True
        
        elapsed = (datetime.now() - self._circuit_open_time).total_seconds()
        return elapsed >= self._circuit_reset_timeout
    
    def _reset_circuit(self):
        """重置熔断器"""
        self._circuit_open = False
        self._circuit_open_time = None
        logger.info("熔断器已重置")
    
    def get_next_delay(self) -> float:
        """获取下一次重试延迟"""
        if self.config.policy == RetryPolicy.NONE:
            return 0.0
        
        elif self.config.policy == RetryPolicy.SIMPLE:
            return self.config.initial_delay
        
        elif self.config.policy == RetryPolicy.FIXED_INTERVAL:
            return self.config.initial_delay
        
        elif self.config.policy == RetryPolicy.LINEAR_BACKOFF:
            delay = self.config.initial_delay * self._state.attempt
            return min(delay, self.config.max_delay)
        
        elif self.config.policy == RetryPolicy.EXPONENTIAL_BACKOFF:
            delay = self.config.initial_delay * (self.config.backoff_factor ** self._state.attempt)
            return min(delay, self.config.max_delay)
        
        elif self.config.policy == RetryPolicy.JITTER:
            base_delay = self.config.initial_delay * (self.config.backoff_factor ** self._state.attempt)
            jitter = base_delay * self.config.jitter_range * (random.random() * 2 - 1)
            delay = base_delay + jitter
            return min(max(delay, 0), self.config.max_delay)
        
        elif self.config.policy == RetryPolicy.CIRCUIT_BREAKER:
            if self._should_open_circuit():
                self._open_circuit()
            return self.config.initial_delay
        
        return self.config.initial_delay
    
    def _should_open_circuit(self) -> bool:
        """判断是否应该打开熔断器"""
        if len(self._state.success_history) < 5:
            return False
        
        recent = self._state.success_history[-5:]
        failure_rate = sum(1 for s in recent if not s) / len(recent)
        return failure_rate >= 0.6
    
    def _open_circuit(self):
        """打开熔断器"""
        self._circuit_open = True
        self._circuit_open_time = datetime.now()
        logger.warning("熔断器已打开，暂停重试")
    
    def record_attempt(self, success: bool, error: Optional[str] = None):
        """记录尝试结果"""
        self._state.attempt += 1
        self._state.last_attempt_time = datetime.now()
        self._state.success_history.append(success)
        
        if error:
            self._state.error_history.append(error)
            self._state.last_error = error
        
        if success:
            self._state.attempt = 0
            if self._circuit_open:
                self._reset_circuit()
    
    def reset(self):
        """重置状态"""
        self._state = RetryState()
        self._circuit_open = False
        self._circuit_open_time = None
    
    def get_state(self) -> RetryState:
        """获取当前状态"""
        return self._state
    
    def execute_with_retry(
        self,
        operation: Callable[[], T],
        on_retry: Optional[Callable[[int, str, float], None]] = None
    ) -> Tuple[bool, Optional[T], Optional[str]]:
        """执行操作并在失败时重试"""
        while True:
            try:
                result = operation()
                self.record_attempt(True)
                return True, result, None
            
            except Exception as e:
                error_str = str(e)
                
                if not self.should_retry(error_str):
                    self.record_attempt(False, error_str)
                    return False, None, error_str
                
                delay = self.get_next_delay()
                
                if on_retry:
                    on_retry(self._state.attempt, error_str, delay)
                
                self.record_attempt(False, error_str)
                self._state.total_wait_time += delay
                
                time.sleep(delay)


T = TypeVar('T')


class FileLockDetector:
    """增强跨平台文件锁定检测器 - 支持多维度冲突检测"""
    
    def __init__(self):
        self._lock_cache: Dict[str, Tuple[bool, float]] = {}
        self._cache_ttl = 2.0
        self._conflict_history: List[ConflictInfo] = []
        self._max_history = 100
    
    def is_locked(self, file_path: str) -> FileLockResult:
        """检测文件是否被锁定"""
        path = Path(file_path)
        
        if not path.exists():
            return FileLockResult(locked=False)
        
        cache_key = str(path.resolve())
        if cache_key in self._lock_cache:
            cached_locked, cached_time = self._lock_cache[cache_key]
            if time.time() - cached_time < self._cache_ttl:
                return FileLockResult(locked=cached_locked)
        
        result = self._check_lock(file_path)
        self._lock_cache[cache_key] = (result.locked, time.time())
        return result
    
    def _check_lock(self, file_path: str) -> FileLockResult:
        """执行实际的锁定检测"""
        try:
            if platform.system() == 'Windows':
                return self._check_lock_windows(file_path)
            else:
                return self._check_lock_unix(file_path)
        except Exception as e:
            return FileLockResult(locked=False, error=str(e))
    
    def _check_lock_windows(self, file_path: str) -> FileLockResult:
        """Windows平台锁定检测 - 增强版"""
        try:
            path = Path(file_path)
            if not path.exists():
                return FileLockResult(locked=False)
            
            with open(file_path, 'r+b') as f:
                try:
                    msvcrt.locking(f.fileno(), msvcrt.LK_NBLCK, 1)
                    msvcrt.locking(f.fileno(), msvcrt.LK_UNLCK, 1)
                    return FileLockResult(locked=False)
                except OSError:
                    return FileLockResult(locked=True)
                except IOError:
                    return FileLockResult(locked=True)
        except PermissionError:
            return FileLockResult(locked=True)
        except FileNotFoundError:
            return FileLockResult(locked=False)
        except OSError as e:
            if e.errno == 13:
                return FileLockResult(locked=True)
            return FileLockResult(locked=False, error=str(e))
        except Exception as e:
            return FileLockResult(locked=False, error=str(e))
    
    def _check_lock_unix(self, file_path: str) -> FileLockResult:
        """Unix/Linux平台锁定检测 - 增强版"""
        try:
            path = Path(file_path)
            if not path.exists():
                return FileLockResult(locked=False)
            
            with open(file_path, 'r+b') as f:
                try:
                    fcntl.flock(f.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                    fcntl.flock(f.fileno(), fcntl.LOCK_UN)
                    return FileLockResult(locked=False)
                except IOError:
                    return FileLockResult(locked=True)
                except BlockingIOError:
                    return FileLockResult(locked=True)
        except PermissionError:
            return FileLockResult(locked=True)
        except FileNotFoundError:
            return FileLockResult(locked=False)
        except OSError as e:
            if e.errno in (13, 1):
                return FileLockResult(locked=True)
            return FileLockResult(locked=False, error=str(e))
        except Exception as e:
            return FileLockResult(locked=False, error=str(e))
    
    def get_lock_holder(self, file_path: str) -> Optional[str]:
        """获取锁定持有者信息（需要psutil）"""
        if not HAS_PSUTIL:
            return None
        
        try:
            resolved_path = str(Path(file_path).resolve())
            for proc in psutil.process_iter(['pid', 'name', 'open_files', 'exe']):
                try:
                    open_files = proc.info.get('open_files') or []
                    for of in open_files:
                        if of and hasattr(of, 'path'):
                            try:
                                of_resolved = str(Path(of.path).resolve())
                                if of_resolved == resolved_path:
                                    proc_name = proc.info.get('name', 'unknown')
                                    proc_exe = proc.info.get('exe', '')
                                    return f"PID:{proc.info['pid']} ({proc_name}) [{proc_exe}]"
                            except (OSError, ValueError):
                                if of.path == file_path:
                                    return f"PID:{proc.info['pid']} ({proc.info.get('name', 'unknown')})"
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    continue
        except Exception as e:
            logger.debug(f"获取锁定持有者失败: {e}")
        
        return None
    
    def detect_conflicts(
        self,
        file_path: str,
        check_process: bool = True,
        check_temp_files: bool = True,
        check_permissions: bool = True,
        check_disk_space: bool = True
    ) -> ConflictDetectionResult:
        """多维度冲突检测"""
        conflicts: List[ConflictInfo] = []
        predicted_conflicts: List[ConflictInfo] = []
        suggestions: List[str] = []
        
        path = Path(file_path)
        
        lock_result = self.is_locked(file_path)
        if lock_result.locked:
            holder = self.get_lock_holder(file_path)
            conflict = ConflictInfo(
                conflict_type=ConflictType.FILE_LOCK,
                severity=self._determine_lock_severity(file_path, holder),
                file_path=file_path,
                detected_at=datetime.now(),
                holder_info=holder,
                suggested_action="等待文件解锁或关闭占用进程",
                auto_resolvable=True
            )
            conflicts.append(conflict)
            suggestions.append(f"文件被锁定，持有者: {holder or '未知'}")
        
        if check_process and HAS_PSUTIL:
            process_conflicts = self._detect_process_conflicts(file_path)
            conflicts.extend(process_conflicts)
        
        if check_temp_files:
            temp_conflicts = self._detect_temp_file_conflicts(file_path)
            conflicts.extend(temp_conflicts)
        
        if check_permissions:
            perm_conflicts = self._detect_permission_conflicts(file_path)
            conflicts.extend(perm_conflicts)
        
        if check_disk_space:
            space_conflicts = self._detect_disk_space_conflicts(file_path)
            conflicts.extend(space_conflicts)
            predicted_conflicts.extend(self._predict_disk_conflicts(file_path))
        
        predicted_conflicts.extend(self._predict_ide_conflicts(file_path))
        predicted_conflicts.extend(self._predict_antivirus_conflicts(file_path))
        
        total_severity = self._calculate_total_severity(conflicts)
        
        if conflicts:
            self._record_conflicts(conflicts)
        
        return ConflictDetectionResult(
            has_conflict=len(conflicts) > 0,
            conflicts=conflicts,
            total_severity=total_severity,
            resolution_suggestions=suggestions,
            predicted_conflicts=predicted_conflicts
        )
    
    def _determine_lock_severity(self, file_path: str, holder: Optional[str]) -> ConflictSeverity:
        """确定锁定严重程度"""
        if not holder:
            return ConflictSeverity.MEDIUM
        
        holder_lower = holder.lower()
        
        if any(ide in holder_lower for ide in ['code', 'pycharm', 'idea', 'sublime', 'vim', 'emacs']):
            return ConflictSeverity.LOW
        elif any(av in holder_lower for av in ['defender', 'antivirus', 'avast', 'avg', 'kasper', 'norton', 'mcafee']):
            return ConflictSeverity.HIGH
        elif 'python' in holder_lower:
            return ConflictSeverity.MEDIUM
        
        return ConflictSeverity.MEDIUM
    
    def _detect_process_conflicts(self, file_path: str) -> List[ConflictInfo]:
        """检测进程相关冲突"""
        conflicts = []
        
        if not HAS_PSUTIL:
            return conflicts
        
        try:
            script_name = Path(file_path).name
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    cmdline = proc.info.get('cmdline') or []
                    if not cmdline:
                        continue
                    
                    if 'python' not in proc.info['name'].lower():
                        continue
                    
                    command_line = ' '.join(cmdline)
                    if script_name in command_line:
                        conflicts.append(ConflictInfo(
                            conflict_type=ConflictType.PROCESS_RUNNING,
                            severity=ConflictSeverity.MEDIUM,
                            file_path=file_path,
                            detected_at=datetime.now(),
                            holder_info=f"PID:{proc.info['pid']} ({proc.info['name']})",
                            suggested_action="等待脚本执行完成或手动终止",
                            auto_resolvable=True,
                            metadata={'pid': proc.info['pid']}
                        ))
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    continue
        except Exception as e:
            logger.debug(f"进程冲突检测失败: {e}")
        
        return conflicts
    
    def _detect_temp_file_conflicts(self, file_path: str) -> List[ConflictInfo]:
        """检测临时文件冲突"""
        conflicts = []
        path = Path(file_path)
        parent = path.parent
        stem = path.stem
        
        try:
            for temp_file in parent.glob(f"{stem}_temp_*"):
                if temp_file.is_file():
                    conflicts.append(ConflictInfo(
                        conflict_type=ConflictType.TEMP_FILE_EXISTS,
                        severity=ConflictSeverity.LOW,
                        file_path=str(temp_file),
                        detected_at=datetime.now(),
                        suggested_action="清理已存在的临时文件",
                        auto_resolvable=True
                    ))
        except Exception as e:
            logger.debug(f"临时文件冲突检测失败: {e}")
        
        return conflicts
    
    def _detect_permission_conflicts(self, file_path: str) -> List[ConflictInfo]:
        """检测权限冲突"""
        conflicts = []
        path = Path(file_path)
        
        if path.exists():
            try:
                if not os.access(file_path, os.W_OK):
                    conflicts.append(ConflictInfo(
                        conflict_type=ConflictType.PERMISSION_DENIED,
                        severity=ConflictSeverity.HIGH,
                        file_path=file_path,
                        detected_at=datetime.now(),
                        suggested_action="检查文件权限或以管理员身份运行",
                        auto_resolvable=False
                    ))
            except Exception:
                pass
        
        parent = path.parent
        if parent.exists():
            try:
                if not os.access(str(parent), os.W_OK):
                    conflicts.append(ConflictInfo(
                        conflict_type=ConflictType.PERMISSION_DENIED,
                        severity=ConflictSeverity.HIGH,
                        file_path=str(parent),
                        detected_at=datetime.now(),
                        suggested_action="检查目录权限",
                        auto_resolvable=False
                    ))
            except Exception:
                pass
        
        return conflicts
    
    def _detect_disk_space_conflicts(self, file_path: str) -> List[ConflictInfo]:
        """检测磁盘空间冲突"""
        conflicts = []
        
        try:
            path = Path(file_path)
            if path.exists():
                stat = shutil.disk_usage(str(path.parent if path.is_file() else path))
                free_gb = stat.free / (1024 ** 3)
                
                if free_gb < 0.5:
                    conflicts.append(ConflictInfo(
                        conflict_type=ConflictType.DISK_SPACE,
                        severity=ConflictSeverity.CRITICAL,
                        file_path=file_path,
                        detected_at=datetime.now(),
                        suggested_action="释放磁盘空间",
                        auto_resolvable=False,
                        metadata={'free_gb': free_gb}
                    ))
                elif free_gb < 2:
                    conflicts.append(ConflictInfo(
                        conflict_type=ConflictType.DISK_SPACE,
                        severity=ConflictSeverity.HIGH,
                        file_path=file_path,
                        detected_at=datetime.now(),
                        suggested_action="磁盘空间不足，建议清理",
                        auto_resolvable=False,
                        metadata={'free_gb': free_gb}
                    ))
        except Exception as e:
            logger.debug(f"磁盘空间检测失败: {e}")
        
        return conflicts
    
    def _predict_ide_conflicts(self, file_path: str) -> List[ConflictInfo]:
        """预测IDE可能产生的冲突"""
        predicted = []
        
        if not HAS_PSUTIL:
            return predicted
        
        try:
            ide_processes = ['code', 'pycharm', 'idea', 'sublime', 'vim', 'emacs']
            for proc in psutil.process_iter(['name']):
                try:
                    proc_name = proc.info.get('name', '').lower()
                    if any(ide in proc_name for ide in ide_processes):
                        predicted.append(ConflictInfo(
                            conflict_type=ConflictType.IDE_LOCK,
                            severity=ConflictSeverity.LOW,
                            file_path=file_path,
                            detected_at=datetime.now(),
                            suggested_action="IDE可能正在监控文件变化",
                            auto_resolvable=True,
                            metadata={'ide_name': proc_name}
                        ))
                        break
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
        except Exception:
            pass
        
        return predicted
    
    def _predict_antivirus_conflicts(self, file_path: str) -> List[ConflictInfo]:
        """预测杀毒软件可能产生的冲突"""
        predicted = []
        
        if not HAS_PSUTIL:
            return predicted
        
        try:
            av_processes = ['defender', 'antivirus', 'avast', 'avg', 'kasper', 'norton', 'mcafee', 'malwarebytes']
            for proc in psutil.process_iter(['name']):
                try:
                    proc_name = proc.info.get('name', '').lower()
                    if any(av in proc_name for av in av_processes):
                        predicted.append(ConflictInfo(
                            conflict_type=ConflictType.ANTIVIRUS_LOCK,
                            severity=ConflictSeverity.MEDIUM,
                            file_path=file_path,
                            detected_at=datetime.now(),
                            suggested_action="杀毒软件可能扫描新创建的文件",
                            auto_resolvable=True,
                            metadata={'av_name': proc_name}
                        ))
                        break
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
        except Exception:
            pass
        
        return predicted
    
    def _predict_disk_conflicts(self, file_path: str) -> List[ConflictInfo]:
        """预测磁盘空间可能产生的冲突"""
        predicted = []
        
        try:
            path = Path(file_path)
            if path.exists():
                stat = shutil.disk_usage(str(path.parent if path.is_file() else path))
                free_gb = stat.free / (1024 ** 3)
                
                if free_gb < 5:
                    predicted.append(ConflictInfo(
                        conflict_type=ConflictType.DISK_SPACE,
                        severity=ConflictSeverity.LOW,
                        file_path=file_path,
                        detected_at=datetime.now(),
                        suggested_action="磁盘空间即将不足",
                        auto_resolvable=False,
                        metadata={'free_gb': free_gb}
                    ))
        except Exception:
            pass
        
        return predicted
    
    def _calculate_total_severity(self, conflicts: List[ConflictInfo]) -> ConflictSeverity:
        """计算总体冲突严重程度"""
        if not conflicts:
            return ConflictSeverity.LOW
        
        severity_weights = {
            ConflictSeverity.CRITICAL: 4,
            ConflictSeverity.HIGH: 3,
            ConflictSeverity.MEDIUM: 2,
            ConflictSeverity.LOW: 1
        }
        
        max_weight = max(severity_weights.get(c.severity, 0) for c in conflicts)
        
        for severity, weight in severity_weights.items():
            if weight == max_weight:
                return severity
        
        return ConflictSeverity.MEDIUM
    
    def _record_conflicts(self, conflicts: List[ConflictInfo]):
        """记录冲突历史"""
        self._conflict_history.extend(conflicts)
        if len(self._conflict_history) > self._max_history:
            self._conflict_history = self._conflict_history[-self._max_history:]
    
    def get_conflict_history(self, limit: int = 50) -> List[ConflictInfo]:
        """获取冲突历史"""
        return self._conflict_history[-limit:]
    
    def clear_cache(self):
        """清除缓存"""
        self._lock_cache.clear()
    
    def wait_for_unlock(
        self,
        file_path: str,
        timeout: float = 30.0,
        interval: float = 0.5,
        strategy: WaitStrategy = WaitStrategy.LINEAR,
        callback: Callable[[float, bool], None] = None,
        adaptive_state: Optional[AdaptiveWaitState] = None
    ) -> WaitResult:
        """等待文件解锁 - 支持多种等待策略"""
        start_time = time.time()
        current_interval = interval
        iterations = 0
        fib_sequence = self._fibonacci_sequence()
        
        if adaptive_state is None:
            adaptive_state = AdaptiveWaitState(initial_interval=interval)
        
        while time.time() - start_time < timeout:
            lock_result = self.is_locked(file_path)
            
            if not lock_result.locked:
                return WaitResult(
                    success=True,
                    waited_seconds=time.time() - start_time,
                    final_status=ScriptStatus.STOPPED,
                    iterations=iterations,
                    strategy_used=strategy
                )
            
            iterations += 1
            
            if callback:
                callback(time.time() - start_time, lock_result.locked)
            
            time.sleep(current_interval)
            
            current_interval = self._calculate_next_interval(
                strategy, current_interval, interval, iterations, 
                fib_sequence, adaptive_state
            )
        
        return WaitResult(
            success=False,
            waited_seconds=timeout,
            timeout=True,
            final_status=ScriptStatus.RUNNING,
            error=f"等待文件解锁超时: {file_path}",
            iterations=iterations,
            strategy_used=strategy
        )
    
    def _calculate_next_interval(
        self,
        strategy: WaitStrategy,
        current: float,
        initial: float,
        iteration: int,
        fib_sequence: List[int],
        adaptive_state: AdaptiveWaitState
    ) -> float:
        """计算下一次等待间隔"""
        if strategy == WaitStrategy.LINEAR:
            return initial
        elif strategy == WaitStrategy.EXPONENTIAL:
            return min(current * 1.5, 5.0)
        elif strategy == WaitStrategy.EXPONENTIAL_JITTER:
            jitter = current * adaptive_state.jitter_factor * (0.5 - random.random() * 1.0)
            return min(current * 1.5 + jitter, 5.0)
        elif strategy == WaitStrategy.FIBONACCI:
            fib_index = min(iteration, len(fib_sequence) - 1)
            return min(initial * fib_sequence[fib_index], 5.0)
        elif strategy == WaitStrategy.ADAPTIVE:
            return self._adaptive_interval(adaptive_state, current)
        else:
            return initial
    
    def _adaptive_interval(self, state: AdaptiveWaitState, current: float) -> float:
        """自适应等待间隔计算"""
        if state.iterations > 0:
            success_rate = state.successes / state.iterations
            if success_rate > 0.7:
                state.current_interval = max(state.initial_interval, state.current_interval * 0.9)
            elif success_rate < 0.3:
                state.current_interval = min(state.max_interval, state.current_interval * 1.1)
        
        jitter = state.current_interval * state.jitter_factor * (0.5 - random.random() * 1.0)
        state.iterations += 1
        state.last_adjustment = datetime.now()
        
        return max(state.initial_interval, min(state.current_interval + jitter, state.max_interval))
    
    def _fibonacci_sequence(self, limit: int = 20) -> List[int]:
        """生成斐波那契数列"""
        fib = [1, 1]
        while len(fib) < limit:
            fib.append(fib[-1] + fib[-2])
        return fib


import random


class ProcessDetector:
    """增强进程检测器 - 支持智能状态检测和资源分析"""
    
    def __init__(self):
        self._cache: Dict[str, Tuple[List[ScriptRunInfo], float]] = {}
        self._cache_ttl = 3.0
        self._use_psutil = HAS_PSUTIL
        self._health_history: Dict[int, List[ProcessHealthInfo]] = {}
        self._max_history_per_process = 20
        self._responsiveness_threshold = 5.0
    
    def detect_running_scripts(self, script_name: str = None) -> List[ScriptRunInfo]:
        """检测正在运行的脚本"""
        cache_key = script_name or "__all__"
        
        if cache_key in self._cache:
            cached_info, cached_time = self._cache[cache_key]
            if time.time() - cached_time < self._cache_ttl:
                return cached_info
        
        running_scripts = []
        
        try:
            if self._use_psutil:
                running_scripts = self._detect_psutil(script_name)
            elif platform.system() == 'Windows':
                running_scripts = self._detect_windows(script_name)
            else:
                running_scripts = self._detect_unix(script_name)
        except Exception as e:
            logger.error(f"检测运行脚本失败: {e}")
        
        self._cache[cache_key] = (running_scripts, time.time())
        return running_scripts
    
    def _detect_psutil(self, script_name: str = None) -> List[ScriptRunInfo]:
        """使用psutil检测进程"""
        scripts = []
        
        try:
            for proc in psutil.process_iter(['pid', 'name', 'cmdline', 'cpu_percent', 'memory_info', 'num_threads', 'username', 'create_time']):
                try:
                    cmdline = proc.info.get('cmdline') or []
                    if not cmdline:
                        continue
                    
                    if 'python' not in proc.info['name'].lower():
                        continue
                    
                    command_line = ' '.join(cmdline)
                    
                    if script_name and script_name not in command_line:
                        continue
                    
                    script_path = self._extract_script_path(command_line)
                    if not script_path:
                        continue
                    
                    try:
                        cpu = proc.cpu_percent(interval=0.1)
                        memory = proc.memory_info().rss / (1024 * 1024)
                        create_time = datetime.fromtimestamp(proc.info.get('create_time', time.time()))
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        cpu = 0.0
                        memory = 0.0
                        create_time = None
                    
                    scripts.append(ScriptRunInfo(
                        script_path=script_path,
                        pid=proc.info['pid'],
                        start_time=create_time,
                        status=ScriptStatus.RUNNING,
                        command_line=command_line,
                        cpu_percent=cpu,
                        memory_mb=memory,
                        threads=proc.info.get('num_threads', 1),
                        user=proc.info.get('username', '')
                    ))
                    
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    continue
                    
        except Exception as e:
            logger.error(f"psutil检测失败: {e}")
        
        return scripts
    
    def _detect_windows(self, script_name: str = None) -> List[ScriptRunInfo]:
        """Windows平台检测"""
        scripts = []
        
        try:
            result = subprocess.run(
                ['tasklist', '/FI', 'IMAGENAME eq python.exe', '/FO', 'CSV', '/V'],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')
                for line in lines[1:]:
                    if not line.strip():
                        continue
                    
                    parts = line.split('","')
                    if len(parts) >= 9:
                        pid_str = parts[1].replace('"', '')
                        command_line = parts[8].replace('"', '') if len(parts) > 8 else ""
                        
                        if script_name and script_name not in command_line:
                            continue
                        
                        if '.py' in command_line or 'python' in command_line.lower():
                            try:
                                pid = int(pid_str)
                                scripts.append(ScriptRunInfo(
                                    script_path=self._extract_script_path(command_line),
                                    pid=pid,
                                    status=ScriptStatus.RUNNING,
                                    command_line=command_line
                                ))
                            except ValueError:
                                continue
        except subprocess.TimeoutExpired:
            logger.warning("Windows进程检测超时")
        except Exception as e:
            logger.error(f"Windows进程检测失败: {e}")
        
        return scripts
    
    def _detect_unix(self, script_name: str = None) -> List[ScriptRunInfo]:
        """Unix/Linux平台检测"""
        scripts = []
        
        try:
            result = subprocess.run(
                ['ps', 'aux'],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')
                for line in lines[1:]:
                    if 'python' not in line.lower():
                        continue
                    
                    if script_name and script_name not in line:
                        continue
                    
                    parts = line.split()
                    if len(parts) >= 11:
                        try:
                            pid = int(parts[1])
                            command_line = ' '.join(parts[10:])
                            
                            scripts.append(ScriptRunInfo(
                                script_path=self._extract_script_path(command_line),
                                pid=pid,
                                status=ScriptStatus.RUNNING,
                                command_line=command_line
                            ))
                        except (ValueError, IndexError):
                            continue
        except subprocess.TimeoutExpired:
            logger.warning("Unix进程检测超时")
        except Exception as e:
            logger.error(f"Unix进程检测失败: {e}")
        
        return scripts
    
    def _extract_script_path(self, command_line: str) -> str:
        """从命令行提取脚本路径"""
        parts = command_line.split()
        for part in parts:
            if part.endswith('.py'):
                return part
            if '/' in part and not part.startswith('-'):
                return part
            if '\\' in part and not part.startswith('-'):
                return part
        return ""
    
    def is_script_running(self, script_path: str) -> bool:
        """检查指定脚本是否正在运行"""
        script_name = Path(script_path).name
        running = self.detect_running_scripts(script_name)
        
        for info in running:
            if script_path in info.script_path or script_name in info.script_path:
                return True
            if script_name in info.command_line:
                return True
        
        return False
    
    def get_script_info(self, script_path: str) -> Optional[ScriptRunInfo]:
        """获取脚本运行信息"""
        script_name = Path(script_path).name
        running = self.detect_running_scripts(script_name)
        
        for info in running:
            if script_path in info.script_path or script_name in info.script_path:
                return info
            if script_name in info.command_line:
                return info
        
        return None
    
    def get_all_python_processes(self) -> List[ScriptRunInfo]:
        """获取所有Python进程"""
        return self.detect_running_scripts()
    
    def wait_for_script_stop(
        self,
        script_path: str,
        timeout: float = 60.0,
        interval: float = 1.0,
        strategy: WaitStrategy = WaitStrategy.EXPONENTIAL,
        callback: Callable[[float, ScriptRunInfo], None] = None
    ) -> WaitResult:
        """等待脚本停止运行"""
        start_time = time.time()
        current_interval = interval
        iterations = 0
        
        while time.time() - start_time < timeout:
            script_info = self.get_script_info(script_path)
            
            if script_info is None:
                return WaitResult(
                    success=True,
                    waited_seconds=time.time() - start_time,
                    final_status=ScriptStatus.STOPPED,
                    iterations=iterations,
                    strategy_used=strategy
                )
            
            iterations += 1
            
            if callback:
                callback(time.time() - start_time, script_info)
            
            time.sleep(current_interval)
            
            if strategy == WaitStrategy.EXPONENTIAL:
                current_interval = min(current_interval * 1.5, 5.0)
        
        return WaitResult(
            success=False,
            waited_seconds=timeout,
            timeout=True,
            final_status=ScriptStatus.RUNNING,
            error=f"等待脚本停止超时: {script_path}",
            iterations=iterations,
            strategy_used=strategy
        )
    
    def terminate_script(self, script_path: str, force: bool = False) -> bool:
        """终止脚本运行"""
        script_info = self.get_script_info(script_path)
        
        if not script_info or not script_info.pid:
            return True
        
        try:
            if self._use_psutil:
                proc = psutil.Process(script_info.pid)
                if force:
                    proc.kill()
                else:
                    proc.terminate()
                return True
            else:
                if platform.system() == 'Windows':
                    cmd = ['taskkill', '/F' if force else '', '/PID', str(script_info.pid)]
                    subprocess.run(cmd, capture_output=True, timeout=10)
                else:
                    sig = signal.SIGKILL if force else signal.SIGTERM
                    os.kill(script_info.pid, sig)
                return True
        except Exception as e:
            logger.error(f"终止脚本失败: {e}")
            return False
    
    def get_process_health(self, script_path: str) -> Optional[ProcessHealthInfo]:
        """获取进程健康状态"""
        if not HAS_PSUTIL:
            return None
        
        script_info = self.get_script_info(script_path)
        if not script_info or not script_info.pid:
            return None
        
        try:
            proc = psutil.Process(script_info.pid)
            
            cpu = proc.cpu_percent(interval=0.1)
            memory_info = proc.memory_info()
            memory_mb = memory_info.rss / (1024 * 1024)
            
            try:
                io_counters = proc.io_counters()
                io_read_mb = io_counters.read_bytes / (1024 * 1024)
                io_write_mb = io_counters.write_bytes / (1024 * 1024)
            except (AttributeError, psutil.AccessDenied):
                io_read_mb = 0.0
                io_write_mb = 0.0
            
            try:
                num_fds = proc.num_fds() if hasattr(proc, 'num_fds') else 0
            except (AttributeError, psutil.AccessDenied):
                num_fds = 0
            
            create_time = datetime.fromtimestamp(proc.create_time())
            uptime = (datetime.now() - create_time).total_seconds()
            
            is_responsive = self._check_process_responsiveness(proc)
            
            health_score = self._calculate_health_score(
                cpu, memory_mb, is_responsive, uptime
            )
            
            resource_trend = self._analyze_resource_trend(
                script_info.pid, cpu, memory_mb
            )
            
            health_info = ProcessHealthInfo(
                pid=script_info.pid,
                script_path=script_path,
                status=ScriptStatus.RUNNING,
                cpu_percent=cpu,
                memory_mb=memory_mb,
                thread_count=proc.num_threads(),
                file_descriptors=num_fds,
                io_read_mb=io_read_mb,
                io_write_mb=io_write_mb,
                uptime_seconds=uptime,
                is_responsive=is_responsive,
                last_activity=datetime.now(),
                resource_trend=resource_trend,
                health_score=health_score
            )
            
            self._record_health_history(script_info.pid, health_info)
            
            return health_info
            
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess) as e:
            logger.debug(f"获取进程健康状态失败: {e}")
            return None
        except Exception as e:
            logger.error(f"获取进程健康状态失败: {e}")
            return None
    
    def _check_process_responsiveness(self, proc: psutil.Process) -> bool:
        """检查进程响应性"""
        try:
            status = proc.status()
            if status in [psutil.STATUS_ZOMBIE, psutil.STATUS_DEAD]:
                return False
            
            if status == psutil.STATUS_STOPPED:
                return False
            
            if proc.cpu_percent(interval=0.05) == 0:
                try:
                    proc.num_threads()
                except psutil.AccessDenied:
                    pass
            
            return True
            
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            return False
    
    def _calculate_health_score(
        self,
        cpu: float,
        memory_mb: float,
        is_responsive: bool,
        uptime: float
    ) -> float:
        """计算进程健康分数"""
        score = 100.0
        
        if not is_responsive:
            score -= 40.0
        
        if cpu > 90:
            score -= 20.0
        elif cpu > 70:
            score -= 10.0
        elif cpu > 50:
            score -= 5.0
        
        if memory_mb > 1000:
            score -= 20.0
        elif memory_mb > 500:
            score -= 10.0
        elif memory_mb > 200:
            score -= 5.0
        
        if uptime < 1:
            score -= 10.0
        
        return max(0.0, min(100.0, score))
    
    def _analyze_resource_trend(
        self,
        pid: int,
        current_cpu: float,
        current_memory: float
    ) -> str:
        """分析资源使用趋势"""
        if pid not in self._health_history:
            return "unknown"
        
        history = self._health_history[pid]
        if len(history) < 3:
            return "insufficient_data"
        
        recent = history[-3:]
        
        avg_cpu = sum(h.cpu_percent for h in recent) / len(recent)
        avg_memory = sum(h.memory_mb for h in recent) / len(recent)
        
        cpu_trend = "stable"
        memory_trend = "stable"
        
        if current_cpu > avg_cpu * 1.3:
            cpu_trend = "increasing"
        elif current_cpu < avg_cpu * 0.7:
            cpu_trend = "decreasing"
        
        if current_memory > avg_memory * 1.3:
            memory_trend = "increasing"
        elif current_memory < avg_memory * 0.7:
            memory_trend = "decreasing"
        
        if cpu_trend == "increasing" and memory_trend == "increasing":
            return "resource_intensive"
        elif cpu_trend == "increasing":
            return "cpu_intensive"
        elif memory_trend == "increasing":
            return "memory_intensive"
        elif cpu_trend == "decreasing" and memory_trend == "decreasing":
            return "cooling_down"
        else:
            return "stable"
    
    def _record_health_history(self, pid: int, health_info: ProcessHealthInfo):
        """记录健康历史"""
        if pid not in self._health_history:
            self._health_history[pid] = []
        
        self._health_history[pid].append(health_info)
        
        if len(self._health_history[pid]) > self._max_history_per_process:
            self._health_history[pid] = self._health_history[pid][-self._max_history_per_process:]
    
    def predict_completion_time(self, script_path: str) -> Optional[float]:
        """预测脚本完成时间"""
        if not HAS_PSUTIL:
            return None
        
        health = self.get_process_health(script_path)
        if not health:
            return None
        
        if health.resource_trend == "cooling_down":
            return 5.0
        elif health.resource_trend == "stable":
            return 15.0
        elif health.resource_trend in ["cpu_intensive", "memory_intensive"]:
            return 30.0
        elif health.resource_trend == "resource_intensive":
            return 60.0
        else:
            return None
    
    def is_process_stuck(self, script_path: str) -> bool:
        """检测进程是否卡住"""
        health = self.get_process_health(script_path)
        if not health:
            return False
        
        if not health.is_responsive:
            return True
        
        if health.health_score < 30:
            return True
        
        if health.cpu_percent < 1.0 and health.uptime_seconds > 60:
            return True
        
        return False
    
    def get_all_processes_health(self) -> List[ProcessHealthInfo]:
        """获取所有Python进程的健康状态"""
        health_list = []
        scripts = self.detect_running_scripts()
        
        for script in scripts:
            health = self.get_process_health(script.script_path)
            if health:
                health_list.append(health)
        
        return health_list
    
    def wait_for_script_stop(
        self,
        script_path: str,
        timeout: float = 60.0,
        interval: float = 1.0,
        strategy: WaitStrategy = WaitStrategy.EXPONENTIAL,
        callback: Callable[[float, ScriptRunInfo], None] = None,
        check_health: bool = True,
        adaptive_state: Optional[AdaptiveWaitState] = None
    ) -> WaitResult:
        """等待脚本停止运行 - 支持智能等待"""
        start_time = time.time()
        current_interval = interval
        iterations = 0
        fib_sequence = self._fibonacci_sequence()
        
        if adaptive_state is None:
            adaptive_state = AdaptiveWaitState(initial_interval=interval)
        
        while time.time() - start_time < timeout:
            script_info = self.get_script_info(script_path)
            
            if script_info is None:
                return WaitResult(
                    success=True,
                    waited_seconds=time.time() - start_time,
                    final_status=ScriptStatus.STOPPED,
                    iterations=iterations,
                    strategy_used=strategy
                )
            
            iterations += 1
            
            if check_health and iterations % 5 == 0:
                health = self.get_process_health(script_path)
                if health and health.is_responsive == False:
                    logger.info(f"检测到进程无响应: {script_path}")
                elif health and health.resource_trend == "cooling_down":
                    logger.debug(f"进程正在冷却: {script_path}")
            
            if callback:
                callback(time.time() - start_time, script_info)
            
            time.sleep(current_interval)
            
            current_interval = self._calculate_wait_interval(
                strategy, current_interval, interval, iterations,
                fib_sequence, adaptive_state
            )
        
        return WaitResult(
            success=False,
            waited_seconds=timeout,
            timeout=True,
            final_status=ScriptStatus.RUNNING,
            error=f"等待脚本停止超时: {script_path}",
            iterations=iterations,
            strategy_used=strategy
        )
    
    def _calculate_wait_interval(
        self,
        strategy: WaitStrategy,
        current: float,
        initial: float,
        iteration: int,
        fib_sequence: List[int],
        adaptive_state: AdaptiveWaitState
    ) -> float:
        """计算等待间隔"""
        if strategy == WaitStrategy.LINEAR:
            return initial
        elif strategy == WaitStrategy.EXPONENTIAL:
            return min(current * 1.5, 5.0)
        elif strategy == WaitStrategy.EXPONENTIAL_JITTER:
            jitter = current * adaptive_state.jitter_factor * (0.5 - random.random() * 1.0)
            return min(current * 1.5 + jitter, 5.0)
        elif strategy == WaitStrategy.FIBONACCI:
            fib_index = min(iteration, len(fib_sequence) - 1)
            return min(initial * fib_sequence[fib_index], 5.0)
        elif strategy == WaitStrategy.ADAPTIVE:
            return self._adaptive_wait_interval(adaptive_state, current)
        else:
            return initial
    
    def _adaptive_wait_interval(self, state: AdaptiveWaitState, current: float) -> float:
        """自适应等待间隔"""
        if state.iterations > 0:
            success_rate = state.successes / state.iterations
            if success_rate > 0.7:
                state.current_interval = max(state.initial_interval, state.current_interval * 0.9)
            elif success_rate < 0.3:
                state.current_interval = min(state.max_interval, state.current_interval * 1.1)
        
        jitter = state.current_interval * state.jitter_factor * (0.5 - random.random() * 1.0)
        state.iterations += 1
        state.last_adjustment = datetime.now()
        
        return max(state.initial_interval, min(state.current_interval + jitter, state.max_interval))
    
    def _fibonacci_sequence(self, limit: int = 20) -> List[int]:
        """生成斐波那契数列"""
        fib = [1, 1]
        while len(fib) < limit:
            fib.append(fib[-1] + fib[-2])
        return fib
    
    def clear_cache(self):
        """清除缓存"""
        self._cache.clear()
        self._health_history.clear()


class SmartProcessAnalyzer:
    """智能进程分析器 - 提供进程状态预测和智能分析"""
    
    def __init__(self, process_detector: ProcessDetector):
        self._detector = process_detector
        self._state_history: Dict[int, List[ProcessStateInfo]] = {}
        self._max_history_per_process = 30
        self._prediction_models: Dict[str, Any] = {}
    
    def get_detailed_state(self, script_path: str) -> Optional[ProcessStateInfo]:
        """获取进程详细状态"""
        if not HAS_PSUTIL:
            return None
        
        script_info = self._detector.get_script_info(script_path)
        if not script_info or not script_info.pid:
            return None
        
        try:
            proc = psutil.Process(script_info.pid)
            
            cpu = proc.cpu_percent(interval=0.1)
            memory_info = proc.memory_info()
            memory_mb = memory_info.rss / (1024 * 1024)
            
            try:
                io_counters = proc.io_counters()
                io_read = io_counters.read_bytes
                io_write = io_counters.write_bytes
            except (AttributeError, psutil.AccessDenied):
                io_read = 0
                io_write = 0
            
            try:
                num_fds = proc.num_fds() if hasattr(proc, 'num_fds') else 0
            except (AttributeError, psutil.AccessDenied):
                num_fds = 0
            
            try:
                open_files = [f.path for f in proc.open_files()] if hasattr(proc, 'open_files') else []
            except (psutil.AccessDenied, psutil.NoSuchProcess):
                open_files = []
            
            try:
                children = [c.pid for c in proc.children(recursive=False)]
            except (psutil.AccessDenied, psutil.NoSuchProcess):
                children = []
            
            create_time = datetime.fromtimestamp(proc.create_time())
            uptime = (datetime.now() - create_time).total_seconds()
            
            state = self._determine_process_state(proc, cpu, memory_mb)
            
            is_responsive = self._check_responsiveness(proc)
            
            resource_trend = self._analyze_resource_trend(script_info.pid, cpu, memory_mb)
            
            health_score = self._calculate_health_score(cpu, memory_mb, is_responsive, state)
            
            predicted_completion = self._predict_completion(script_info.pid, state, resource_trend)
            
            state_info = ProcessStateInfo(
                pid=script_info.pid,
                script_path=script_path,
                state=state,
                cpu_percent=cpu,
                memory_mb=memory_mb,
                thread_count=proc.num_threads(),
                file_handles=num_fds,
                io_read_bytes=io_read,
                io_write_bytes=io_write,
                uptime_seconds=uptime,
                is_responsive=is_responsive,
                last_activity=datetime.now(),
                predicted_completion=predicted_completion,
                resource_trend=resource_trend,
                health_score=health_score,
                child_processes=children,
                open_files=open_files[:20]
            )
            
            self._record_state(script_info.pid, state_info)
            
            return state_info
            
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess) as e:
            logger.debug(f"获取进程状态失败: {e}")
            return None
    
    def _determine_process_state(self, proc: psutil.Process, cpu: float, memory_mb: float) -> ProcessState:
        """确定进程状态"""
        try:
            status = proc.status()
            
            if status == psutil.STATUS_ZOMBIE:
                return ProcessState.ZOMBIE
            elif status == psutil.STATUS_STOPPED:
                return ProcessState.STOPPED
            elif status == psutil.STATUS_DEAD:
                return ProcessState.STOPPED
            
            if cpu < 1.0:
                return ProcessState.IDLE
            elif cpu > 80.0:
                return ProcessState.BUSY
            elif cpu > 50.0:
                return ProcessState.RUNNING
            
            if memory_mb > 500:
                return ProcessState.BUSY
            
            return ProcessState.RUNNING
            
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            return ProcessState.UNKNOWN
    
    def _check_responsiveness(self, proc: psutil.Process) -> bool:
        """检查进程响应性"""
        try:
            status = proc.status()
            if status in [psutil.STATUS_ZOMBIE, psutil.STATUS_DEAD, psutil.STATUS_STOPPED]:
                return False
            
            proc.num_threads()
            return True
            
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            return False
    
    def _analyze_resource_trend(self, pid: int, current_cpu: float, current_memory: float) -> str:
        """分析资源使用趋势"""
        if pid not in self._state_history:
            return "unknown"
        
        history = self._state_history[pid]
        if len(history) < 3:
            return "insufficient_data"
        
        recent = history[-5:]
        
        avg_cpu = sum(s.cpu_percent for s in recent) / len(recent)
        avg_memory = sum(s.memory_mb for s in recent) / len(recent)
        
        cpu_trend = "stable"
        memory_trend = "stable"
        
        if current_cpu > avg_cpu * 1.3:
            cpu_trend = "increasing"
        elif current_cpu < avg_cpu * 0.7:
            cpu_trend = "decreasing"
        
        if current_memory > avg_memory * 1.3:
            memory_trend = "increasing"
        elif current_memory < avg_memory * 0.7:
            memory_trend = "decreasing"
        
        if cpu_trend == "increasing" and memory_trend == "increasing":
            return "resource_intensive"
        elif cpu_trend == "increasing":
            return "cpu_intensive"
        elif memory_trend == "increasing":
            return "memory_intensive"
        elif cpu_trend == "decreasing" and memory_trend == "decreasing":
            return "cooling_down"
        else:
            return "stable"
    
    def _calculate_health_score(self, cpu: float, memory_mb: float, is_responsive: bool, state: ProcessState) -> float:
        """计算进程健康分数"""
        score = 100.0
        
        if not is_responsive:
            score -= 40.0
        
        if state == ProcessState.ZOMBIE:
            score -= 50.0
        elif state == ProcessState.BLOCKED:
            score -= 30.0
        
        if cpu > 90:
            score -= 20.0
        elif cpu > 70:
            score -= 10.0
        elif cpu > 50:
            score -= 5.0
        
        if memory_mb > 1000:
            score -= 20.0
        elif memory_mb > 500:
            score -= 10.0
        elif memory_mb > 200:
            score -= 5.0
        
        return max(0.0, min(100.0, score))
    
    def _predict_completion(self, pid: int, state: ProcessState, trend: str) -> Optional[float]:
        """预测完成时间"""
        if state in [ProcessState.IDLE, ProcessState.STOPPED]:
            return 0.0
        
        if state == ProcessState.ZOMBIE:
            return None
        
        trend_predictions = {
            "cooling_down": 5.0,
            "stable": 15.0,
            "cpu_intensive": 30.0,
            "memory_intensive": 30.0,
            "resource_intensive": 60.0,
            "unknown": None,
            "insufficient_data": None,
        }
        
        return trend_predictions.get(trend)
    
    def _record_state(self, pid: int, state_info: ProcessStateInfo):
        """记录状态历史"""
        if pid not in self._state_history:
            self._state_history[pid] = []
        
        self._state_history[pid].append(state_info)
        
        if len(self._state_history[pid]) > self._max_history_per_process:
            self._state_history[pid] = self._state_history[pid][-self._max_history_per_process:]
    
    def predict_behavior(self, script_path: str) -> Dict[str, Any]:
        """预测进程行为"""
        state = self.get_detailed_state(script_path)
        
        if not state:
            return {
                "prediction": "unknown",
                "confidence": 0.0,
                "estimated_completion": None,
                "recommendations": ["无法获取进程状态"]
            }
        
        predictions = []
        confidence = 0.5
        recommendations = []
        
        if state.state == ProcessState.IDLE:
            predictions.append("进程空闲，可能即将完成")
            confidence = 0.8
            recommendations.append("可以安全进行文件操作")
        
        elif state.state == ProcessState.BUSY:
            predictions.append("进程繁忙，建议等待")
            confidence = 0.6
            recommendations.append("等待进程完成当前任务")
        
        elif state.state == ProcessState.ZOMBIE:
            predictions.append("进程已僵死，需要清理")
            confidence = 0.9
            recommendations.append("终止僵死进程")
        
        elif state.resource_trend == "cooling_down":
            predictions.append("进程正在冷却，即将完成")
            confidence = 0.7
            recommendations.append("稍等片刻即可操作")
        
        elif state.resource_trend == "resource_intensive":
            predictions.append("进程资源占用高，可能需要较长时间")
            confidence = 0.5
            recommendations.append("建议等待或考虑终止")
        
        if state.health_score < 50:
            recommendations.append("进程健康状态较差，建议检查")
        
        return {
            "prediction": predictions[0] if predictions else "无法预测",
            "confidence": confidence,
            "estimated_completion": state.predicted_completion,
            "recommendations": recommendations,
            "state": state.state.value,
            "health_score": state.health_score,
            "resource_trend": state.resource_trend
        }
    
    def is_safe_to_modify(self, script_path: str) -> Tuple[bool, str]:
        """判断是否可以安全修改文件"""
        state = self.get_detailed_state(script_path)
        
        if not state:
            return True, "进程未运行"
        
        if state.state == ProcessState.ZOMBIE:
            return True, "进程已僵死，可以安全修改"
        
        if state.state == ProcessState.STOPPED:
            return True, "进程已停止"
        
        if state.state == ProcessState.IDLE and state.resource_trend == "cooling_down":
            return True, "进程空闲且正在冷却"
        
        if state.health_score < 30:
            return True, "进程健康状态极差，建议终止后修改"
        
        return False, f"进程正在运行 (状态: {state.state.value}, 健康分数: {state.health_score:.1f})"
    
    def get_state_history(self, pid: int) -> List[ProcessStateInfo]:
        """获取状态历史"""
        return self._state_history.get(pid, [])
    
    def clear_history(self, pid: Optional[int] = None):
        """清除历史"""
        if pid:
            self._state_history.pop(pid, None)
        else:
            self._state_history.clear()


class AtomicVerifier:
    """原子性验证器 - 提供多阶段文件替换验证"""
    
    def __init__(self):
        self._verification_history: List[VerificationResult] = []
        self._max_history = 100
    
    def create_context(
        self,
        source_path: str,
        target_path: str,
        backup_path: Optional[str] = None
    ) -> AtomicVerificationContext:
        """创建验证上下文"""
        source_file = Path(source_path)
        
        source_hash = ""
        source_size = 0
        source_permissions = None
        source_timestamp = None
        
        if source_file.exists():
            source_hash = self._calculate_hash(source_path)
            source_size = source_file.stat().st_size
            source_permissions = os.stat(source_path).st_mode
            source_timestamp = source_file.stat().st_mtime
        
        return AtomicVerificationContext(
            source_path=source_path,
            target_path=target_path,
            source_hash=source_hash,
            source_size=source_size,
            source_permissions=source_permissions,
            source_timestamp=source_timestamp,
            backup_path=backup_path,
            verification_stages=[
                "existence_check",
                "size_verification",
                "hash_verification",
                "permission_check",
                "integrity_check",
                "accessibility_check"
            ]
        )
    
    def verify_stage(self, context: AtomicVerificationContext, stage: str) -> Tuple[bool, str]:
        """验证单个阶段"""
        target_file = Path(context.target_path)
        
        if stage == "existence_check":
            if not target_file.exists():
                return False, "目标文件不存在"
            context.current_stage = 1
            return True, "文件存在检查通过"
        
        elif stage == "size_verification":
            if not target_file.exists():
                return False, "目标文件不存在"
            actual_size = target_file.stat().st_size
            if actual_size != context.source_size:
                context.errors.append(f"大小不匹配: 期望 {context.source_size}, 实际 {actual_size}")
                return False, f"文件大小不匹配"
            context.current_stage = 2
            return True, f"文件大小验证通过 ({actual_size} bytes)"
        
        elif stage == "hash_verification":
            if not target_file.exists():
                return False, "目标文件不存在"
            actual_hash = self._calculate_hash(context.target_path)
            if actual_hash != context.source_hash:
                context.errors.append(f"哈希不匹配: 期望 {context.source_hash}, 实际 {actual_hash}")
                return False, "文件哈希不匹配"
            context.current_stage = 3
            return True, "文件哈希验证通过"
        
        elif stage == "permission_check":
            if context.source_permissions:
                try:
                    current_permissions = os.stat(context.target_path).st_mode
                    if current_permissions != context.source_permissions:
                        context.warnings.append(f"权限已改变，尝试恢复")
                        os.chmod(context.target_path, context.source_permissions)
                except Exception as e:
                    context.warnings.append(f"权限检查失败: {e}")
            context.current_stage = 4
            return True, "权限检查通过"
        
        elif stage == "integrity_check":
            try:
                with open(context.target_path, 'rb') as f:
                    header = f.read(1024)
                    if b'\x00' in header[:100]:
                        context.warnings.append("文件可能包含空字节")
            except Exception as e:
                context.errors.append(f"完整性检查失败: {e}")
                return False, f"完整性检查失败: {e}"
            context.current_stage = 5
            return True, "完整性检查通过"
        
        elif stage == "accessibility_check":
            try:
                with open(context.target_path, 'r', encoding='utf-8', errors='ignore') as f:
                    f.read(1024)
            except Exception as e:
                context.warnings.append(f"可读性检查警告: {e}")
            context.current_stage = 6
            return True, "可访问性检查通过"
        
        return False, f"未知验证阶段: {stage}"
    
    def full_verify(self, context: AtomicVerificationContext) -> VerificationResult:
        """执行完整验证"""
        all_passed = True
        stages_passed = 0
        
        for stage in context.verification_stages:
            passed, message = self.verify_stage(context, stage)
            if passed:
                stages_passed += 1
                logger.debug(f"验证阶段 [{stage}] 通过: {message}")
            else:
                all_passed = False
                logger.warning(f"验证阶段 [{stage}] 失败: {message}")
                break
        
        result = VerificationResult(
            success=all_passed,
            level=VerificationLevel.MULTI_STAGE,
            original_hash=context.source_hash,
            final_hash=self._calculate_hash(context.target_path) if Path(context.target_path).exists() else "",
            size_match=stages_passed >= 2,
            content_match=stages_passed >= 3,
            permissions_preserved=stages_passed >= 4,
            stages_passed=stages_passed,
            total_stages=len(context.verification_stages),
            error_details=context.errors
        )
        
        self._record_verification(result)
        return result
    
    def quick_verify(self, target_path: str, expected_hash: str, expected_size: int) -> VerificationResult:
        """快速验证"""
        target_file = Path(target_path)
        
        if not target_file.exists():
            return VerificationResult(
                success=False,
                level=VerificationLevel.BASIC,
                error_details=["文件不存在"]
            )
        
        actual_size = target_file.stat().st_size
        size_match = (actual_size == expected_size)
        
        actual_hash = self._calculate_hash(target_path)
        content_match = (actual_hash == expected_hash)
        
        return VerificationResult(
            success=size_match and content_match,
            level=VerificationLevel.HASH,
            original_hash=expected_hash,
            final_hash=actual_hash,
            size_match=size_match,
            content_match=content_match,
            stages_passed=2 if size_match and content_match else (1 if size_match else 0),
            total_stages=2
        )
    
    def _calculate_hash(self, file_path: str) -> str:
        """计算文件哈希"""
        hasher = hashlib.sha256()
        try:
            with open(file_path, 'rb') as f:
                for chunk in iter(lambda: f.read(8192), b''):
                    hasher.update(chunk)
            return hasher.hexdigest()[:16]
        except Exception:
            return ""
    
    def _record_verification(self, result: VerificationResult):
        """记录验证历史"""
        self._verification_history.append(result)
        if len(self._verification_history) > self._max_history:
            self._verification_history = self._verification_history[-self._max_history:]
    
    def get_verification_history(self, limit: int = 50) -> List[VerificationResult]:
        """获取验证历史"""
        return self._verification_history[-limit:]


class CleanupScheduler:
    """清理调度器 - 管理定时清理任务"""
    
    def __init__(self, manager: 'TempFileManager'):
        self._manager = manager
        self._schedules: Dict[str, CleanupSchedule] = {}
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
    
    def add_schedule(
        self,
        name: str,
        directories: List[str],
        interval_seconds: int = 300,
        policy: Optional[CleanupPolicy] = None
    ) -> CleanupSchedule:
        """添加清理调度"""
        schedule = CleanupSchedule(
            directories=directories,
            interval_seconds=interval_seconds,
            policy=policy or CleanupPolicy(),
            next_run=datetime.now() + timedelta(seconds=interval_seconds)
        )
        
        self._schedules[name] = schedule
        logger.info(f"添加清理调度: {name}, 间隔: {interval_seconds}秒")
        
        return schedule
    
    def remove_schedule(self, name: str) -> bool:
        """移除清理调度"""
        if name in self._schedules:
            del self._schedules[name]
            logger.info(f"移除清理调度: {name}")
            return True
        return False
    
    def enable_schedule(self, name: str) -> bool:
        """启用调度"""
        if name in self._schedules:
            self._schedules[name].enabled = True
            return True
        return False
    
    def disable_schedule(self, name: str) -> bool:
        """禁用调度"""
        if name in self._schedules:
            self._schedules[name].enabled = False
            return True
        return False
    
    def start(self):
        """启动调度器"""
        if self._running:
            return
        
        self._running = True
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()
        logger.info("清理调度器已启动")
    
    def stop(self):
        """停止调度器"""
        self._running = False
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=5)
        logger.info("清理调度器已停止")
    
    def _run_loop(self):
        """运行循环"""
        while self._running and not self._stop_event.is_set():
            try:
                self._check_schedules()
            except Exception as e:
                logger.error(f"调度检查失败: {e}")
            
            self._stop_event.wait(10)
    
    def _check_schedules(self):
        """检查调度"""
        now = datetime.now()
        
        for name, schedule in self._schedules.items():
            if not schedule.enabled:
                continue
            
            if schedule.next_run and now >= schedule.next_run:
                self._execute_schedule(name, schedule)
    
    def _execute_schedule(self, name: str, schedule: CleanupSchedule):
        """执行调度"""
        logger.info(f"执行清理调度: {name}")
        
        start_time = time.time()
        total_freed = 0
        
        for directory in schedule.directories:
            try:
                result = self._manager.cleanup_temp_files(
                    directory,
                    cleanup_policy=schedule.policy
                )
                
                if 'stats' in result:
                    total_freed += result['stats'].get('freed_size_mb', 0)
                
            except Exception as e:
                logger.error(f"清理目录失败 {directory}: {e}")
        
        schedule.last_run = datetime.now()
        schedule.next_run = datetime.now() + timedelta(seconds=schedule.interval_seconds)
        schedule.run_count += 1
        schedule.total_freed_mb += total_freed
        
        duration = time.time() - start_time
        logger.info(f"清理调度 {name} 完成, 释放: {total_freed:.2f}MB, 耗时: {duration:.2f}秒")
    
    def run_now(self, name: str) -> Optional[CleanupResult]:
        """立即执行调度"""
        if name not in self._schedules:
            return None
        
        schedule = self._schedules[name]
        
        start_time = time.time()
        all_cleaned = []
        all_skipped = []
        all_errors = []
        total_freed = 0
        
        for directory in schedule.directories:
            result = self._manager.cleanup_temp_files(
                directory,
                cleanup_policy=schedule.policy
            )
            
            all_cleaned.extend(result.get('cleaned', []))
            all_skipped.extend(result.get('skipped', []))
            all_errors.extend(result.get('errors', []))
            
            if 'stats' in result:
                total_freed += result['stats'].get('freed_size_mb', 0) * 1024 * 1024
        
        schedule.last_run = datetime.now()
        schedule.run_count += 1
        
        return CleanupResult(
            trigger=CleanupTrigger.MANUAL,
            cleaned_files=all_cleaned,
            skipped_files=all_skipped,
            errors=all_errors,
            total_size_freed=int(total_freed),
            duration_seconds=time.time() - start_time,
            policy_used=schedule.policy
        )
    
    def get_schedule_status(self, name: str) -> Optional[Dict[str, Any]]:
        """获取调度状态"""
        if name not in self._schedules:
            return None
        
        schedule = self._schedules[name]
        return {
            "name": name,
            "enabled": schedule.enabled,
            "directories": schedule.directories,
            "interval_seconds": schedule.interval_seconds,
            "last_run": schedule.last_run.isoformat() if schedule.last_run else None,
            "next_run": schedule.next_run.isoformat() if schedule.next_run else None,
            "run_count": schedule.run_count,
            "total_freed_mb": schedule.total_freed_mb
        }
    
    def get_all_schedules(self) -> Dict[str, Dict[str, Any]]:
        """获取所有调度状态"""
        return {name: self.get_schedule_status(name) for name in self._schedules}


class TempFileManager:
    """增强临时文件管理器"""
    
    DEFAULT_TEMP_SUFFIX = "_temp"
    DEFAULT_EXPIRE_SECONDS = 3600
    DEFAULT_WAIT_TIMEOUT = 30
    DEFAULT_RETRY_INTERVAL = 0.5
    DEFAULT_SCRIPT_WAIT_TIMEOUT = 60
    
    def __init__(
        self,
        temp_dir: Optional[str] = None,
        expire_seconds: int = None,
        wait_timeout: int = None,
        timeout_config: TimeoutConfig = None,
        retry_config: Optional[RetryConfig] = None
    ):
        self.temp_dir = temp_dir
        self.expire_seconds = expire_seconds or self.DEFAULT_EXPIRE_SECONDS
        self.wait_timeout = wait_timeout or self.DEFAULT_WAIT_TIMEOUT
        self.timeout_config = timeout_config or TimeoutConfig()
        self.retry_config = retry_config or RetryConfig()
        self._registered_files: Dict[str, TempFileInfo] = {}
        self._lock = threading.Lock()
        
        self._process_detector = ProcessDetector()
        self._file_lock_detector = FileLockDetector()
        self._conflict_resolver = ConflictResolver()
        self._retry_manager = RetryManager(self.retry_config)
        self._smart_analyzer = SmartProcessAnalyzer(self._process_detector)
        self._atomic_verifier = AtomicVerifier()
        self._cleanup_scheduler = CleanupScheduler(self)
        
        self._replace_history: List[Dict[str, Any]] = []
        self._cleanup_registered = False
        self._register_cleanup()
    
    def _register_cleanup(self):
        """注册清理函数"""
        if not self._cleanup_registered:
            atexit.register(self._cleanup_on_exit)
            self._cleanup_registered = True
    
    def _cleanup_on_exit(self):
        """退出时清理"""
        try:
            for temp_path, info in list(self._registered_files.items()):
                if info.state == TempFileState.CREATED:
                    Path(temp_path).unlink(missing_ok=True)
        except Exception:
            pass
    
    def _generate_temp_filename(self, original_path: str) -> str:
        original = Path(original_path)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        
        stem = original.stem
        suffix = original.suffix
        
        temp_name = f"{stem}{self.DEFAULT_TEMP_SUFFIX}_{timestamp}{suffix}"
        
        if self.temp_dir:
            return str(Path(self.temp_dir) / temp_name)
        else:
            return str(original.parent / temp_name)
    
    def _calculate_hash(self, file_path: str) -> str:
        """计算文件哈希值"""
        hasher = hashlib.sha256()
        try:
            with open(file_path, 'rb') as f:
                for chunk in iter(lambda: f.read(8192), b''):
                    hasher.update(chunk)
            return hasher.hexdigest()[:16]
        except Exception:
            return ""
    
    def create_temp_file(
        self,
        original_path: str,
        content: Optional[str] = None,
        copy_original: bool = False,
        metadata: Optional[Dict[str, Any]] = None
    ) -> TempFileResult:
        original = Path(original_path)
        
        if not original.exists() and copy_original and content is None:
            return TempFileResult(
                success=False,
                message=f"原文件不存在: {original_path}",
                error="FILE_NOT_FOUND",
                state=TempFileState.ERROR
            )
        
        temp_path = self._generate_temp_filename(original_path)
        temp_file = Path(temp_path)
        
        try:
            temp_file.parent.mkdir(parents=True, exist_ok=True)
            
            if copy_original and original.exists():
                shutil.copy2(original_path, temp_path)
            elif content is not None:
                with open(temp_path, 'w', encoding='utf-8') as f:
                    f.write(content)
            else:
                temp_file.touch()
            
            content_hash = self._calculate_hash(temp_path)
            size_bytes = temp_file.stat().st_size if temp_file.exists() else 0
            
            self.register_temp_file(
                temp_path,
                original_path,
                state=TempFileState.CREATED,
                content_hash=content_hash,
                size_bytes=size_bytes,
                metadata=metadata
            )
            
            logger.info(f"临时文件创建成功: {temp_path}")
            
            return TempFileResult(
                success=True,
                message=f"临时文件创建成功: {temp_path}",
                temp_path=temp_path,
                state=TempFileState.CREATED
            )
            
        except Exception as e:
            logger.error(f"创建临时文件失败: {e}")
            return TempFileResult(
                success=False,
                message=f"创建临时文件失败: {e}",
                error=str(e),
                state=TempFileState.ERROR
            )
    
    def is_file_in_use(self, file_path: str) -> bool:
        """检测文件是否正在被使用"""
        lock_result = self._file_lock_detector.is_locked(file_path)
        return lock_result.locked
    
    def is_script_running(self, script_path: str) -> bool:
        """检测脚本是否正在运行"""
        return self._process_detector.is_script_running(script_path)
    
    def get_script_run_info(self, script_path: str) -> Optional[ScriptRunInfo]:
        """获取脚本运行信息"""
        return self._process_detector.get_script_info(script_path)
    
    def get_file_lock_info(self, file_path: str) -> FileLockResult:
        """获取文件锁定信息"""
        return self._file_lock_detector.is_locked(file_path)
    
    def wait_for_release(
        self,
        file_path: str,
        timeout: int = None,
        interval: float = None,
        strategy: WaitStrategy = None,
        callback: Callable[[float, bool], None] = None
    ) -> WaitResult:
        """等待文件释放"""
        timeout = timeout or self.timeout_config.file_wait_timeout
        interval = interval or self.timeout_config.retry_interval
        strategy = strategy or self.timeout_config.strategy
        
        return self._file_lock_detector.wait_for_unlock(
            file_path,
            timeout=timeout,
            interval=interval,
            strategy=strategy,
            callback=callback
        )
    
    def wait_for_script_stop(
        self,
        script_path: str,
        timeout: float = None,
        interval: float = 1.0,
        strategy: WaitStrategy = None,
        callback: Callable[[float, ScriptRunInfo], None] = None
    ) -> WaitResult:
        """等待脚本停止运行"""
        timeout = timeout or self.timeout_config.script_wait_timeout
        strategy = strategy or self.timeout_config.strategy
        
        return self._process_detector.wait_for_script_stop(
            script_path,
            timeout=timeout,
            interval=interval,
            strategy=strategy,
            callback=callback
        )
    
    def atomic_replace(
        self,
        temp_path: str,
        original_path: str,
        backup: bool = True,
        verify: bool = True,
        wait_for_release: bool = True,
        wait_timeout: int = None,
        verification_level: VerificationLevel = VerificationLevel.HASH
    ) -> AtomicReplaceResult:
        """原子性文件替换 - 增强版，支持多阶段验证"""
        temp_file = Path(temp_path)
        original = Path(original_path)
        
        if not temp_file.exists():
            return AtomicReplaceResult(
                success=False,
                message=f"临时文件不存在: {temp_path}",
                error="TEMP_FILE_NOT_FOUND"
            )
        
        file_wait_seconds = 0.0
        
        if wait_for_release:
            timeout = wait_timeout or self.timeout_config.file_wait_timeout
            start_wait = time.time()
            wait_result = self.wait_for_release(original_path, timeout)
            file_wait_seconds = time.time() - start_wait
            
            if not wait_result.success:
                return AtomicReplaceResult(
                    success=False,
                    message=f"原文件被占用，等待超时: {original_path}",
                    error="FILE_IN_USE_TIMEOUT",
                    file_wait_seconds=file_wait_seconds
                )
        
        backup_path = None
        original_stat = None
        original_permissions = None
        
        try:
            if original.exists():
                original_stat = original.stat()
                original_permissions = os.stat(original_path).st_mode
                
                if backup:
                    backup_path = str(original) + f".bak_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                    shutil.copy2(original_path, backup_path)
            
            original.parent.mkdir(parents=True, exist_ok=True)
            
            temp_hash = self._calculate_hash(temp_path)
            temp_size = temp_file.stat().st_size
            
            if platform.system() == 'Windows':
                if original.exists():
                    os.replace(temp_path, original_path)
                else:
                    shutil.move(temp_path, original_path)
            else:
                os.rename(temp_path, original_path)
            
            verification_result = self._verify_replacement(
                original_path, temp_hash, temp_size, 
                original_permissions, verification_level
            )
            
            self.unregister_temp_file(temp_path)
            
            self._update_temp_file_state(temp_path, TempFileState.REPLACED)
            
            self._replace_history.append({
                "temp_path": temp_path,
                "original_path": original_path,
                "backup_path": backup_path,
                "timestamp": datetime.now().isoformat(),
                "verified": verification_result.success,
                "verification_level": verification_level.value,
                "success": True,
                "file_wait_seconds": file_wait_seconds
            })
            
            logger.info(f"原子替换成功: {original_path}, 验证: {verification_result.success}, 级别: {verification_level.value}")
            
            return AtomicReplaceResult(
                success=True,
                message=f"原子替换成功: {original_path}",
                backup_path=backup_path,
                verified=verification_result.success,
                rollback_available=backup_path is not None,
                file_wait_seconds=file_wait_seconds
            )
            
        except Exception as e:
            logger.error(f"原子替换失败: {e}")
            
            if backup_path and Path(backup_path).exists():
                try:
                    shutil.copy2(backup_path, original_path)
                    if original_permissions:
                        os.chmod(original_path, original_permissions)
                    logger.info(f"已从备份恢复: {original_path}")
                except Exception as restore_error:
                    logger.error(f"恢复备份失败: {restore_error}")
            
            self._replace_history.append({
                "temp_path": temp_path,
                "original_path": original_path,
                "backup_path": backup_path,
                "timestamp": datetime.now().isoformat(),
                "success": False,
                "error": str(e),
                "file_wait_seconds": file_wait_seconds
            })
            
            return AtomicReplaceResult(
                success=False,
                message=f"原子替换失败: {e}",
                error=str(e),
                backup_path=backup_path,
                rollback_available=backup_path is not None and Path(backup_path).exists(),
                file_wait_seconds=file_wait_seconds
            )
    
    def _verify_replacement(
        self,
        file_path: str,
        expected_hash: str,
        expected_size: int,
        original_permissions: Optional[int],
        level: VerificationLevel
    ) -> VerificationResult:
        """多阶段验证替换结果"""
        errors = []
        stages_passed = 0
        total_stages = 1
        
        if level == VerificationLevel.NONE:
            return VerificationResult(
                success=True,
                level=level,
                stages_passed=1,
                total_stages=1
            )
        
        path = Path(file_path)
        
        if not path.exists():
            errors.append("文件不存在")
            return VerificationResult(
                success=False,
                level=level,
                stages_passed=0,
                total_stages=total_stages,
                error_details=errors
            )
        
        stages_passed += 1
        total_stages = 2
        
        actual_size = path.stat().st_size
        size_match = (actual_size == expected_size)
        if not size_match:
            errors.append(f"文件大小不匹配: 期望 {expected_size}, 实际 {actual_size}")
        
        if level == VerificationLevel.BASIC:
            return VerificationResult(
                success=size_match,
                level=level,
                size_match=size_match,
                stages_passed=stages_passed if size_match else 1,
                total_stages=total_stages,
                error_details=errors
            )
        
        stages_passed += 1
        total_stages = 3
        
        actual_hash = self._calculate_hash(file_path)
        content_match = (actual_hash == expected_hash)
        if not content_match:
            errors.append(f"文件哈希不匹配: 期望 {expected_hash}, 实际 {actual_hash}")
        
        if level == VerificationLevel.HASH:
            return VerificationResult(
                success=content_match and size_match,
                level=level,
                original_hash=expected_hash,
                final_hash=actual_hash,
                size_match=size_match,
                content_match=content_match,
                stages_passed=stages_passed if content_match else (stages_passed - 1),
                total_stages=total_stages,
                error_details=errors
            )
        
        stages_passed += 1
        total_stages = 4
        
        permissions_preserved = True
        if original_permissions:
            try:
                current_permissions = os.stat(file_path).st_mode
                permissions_preserved = (current_permissions == original_permissions)
                if not permissions_preserved:
                    os.chmod(file_path, original_permissions)
                    permissions_preserved = True
                    logger.debug(f"已恢复文件权限: {file_path}")
            except Exception as e:
                permissions_preserved = False
                errors.append(f"权限检查失败: {e}")
        
        if level == VerificationLevel.FULL:
            return VerificationResult(
                success=content_match and size_match and permissions_preserved,
                level=level,
                original_hash=expected_hash,
                final_hash=actual_hash,
                size_match=size_match,
                content_match=content_match,
                permissions_preserved=permissions_preserved,
                stages_passed=stages_passed,
                total_stages=total_stages,
                error_details=errors
            )
        
        stages_passed += 1
        total_stages = 5
        
        timestamp_preserved = True
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                if content and not content.startswith('\x00'):
                    timestamp_preserved = True
        except Exception as e:
            timestamp_preserved = False
            errors.append(f"文件可读性检查失败: {e}")
        
        return VerificationResult(
            success=content_match and size_match and permissions_preserved,
            level=level,
            original_hash=expected_hash,
            final_hash=actual_hash,
            size_match=size_match,
            content_match=content_match,
            permissions_preserved=permissions_preserved,
            timestamp_preserved=timestamp_preserved,
            stages_passed=stages_passed,
            total_stages=total_stages,
            error_details=errors
        )
    
    def safe_atomic_replace(
        self,
        temp_path: str,
        original_path: str,
        script_wait_timeout: float = None,
        wait_for_script: bool = True,
        **kwargs
    ) -> AtomicReplaceResult:
        """安全原子替换 - 包含脚本运行检测和文件锁定检测
        
        实现完整的原子性替换流程：
        1. 检测目标脚本是否正在运行
        2. 如果正在运行，等待脚本停止
        3. 检测文件是否被锁定
        4. 如果被锁定，等待解锁
        5. 创建备份
        6. 执行原子替换
        7. 验证替换结果
        """
        script_wait_timeout = script_wait_timeout or self.timeout_config.script_wait_timeout
        script_wait_seconds = 0.0
        
        if wait_for_script and self.is_script_running(original_path):
            logger.info(f"检测到脚本正在运行: {original_path}, 等待停止...")
            
            start_wait = time.time()
            wait_result = self.wait_for_script_stop(
                original_path,
                timeout=script_wait_timeout
            )
            script_wait_seconds = time.time() - start_wait
            
            if not wait_result.success:
                return AtomicReplaceResult(
                    success=False,
                    message=f"脚本仍在运行，无法替换: {original_path}",
                    error="SCRIPT_STILL_RUNNING",
                    waited_for_script=True,
                    script_wait_seconds=script_wait_seconds
                )
        
        result = self.atomic_replace(temp_path, original_path, **kwargs)
        result.waited_for_script = script_wait_seconds > 0
        result.script_wait_seconds = script_wait_seconds
        
        return result
    
    def safe_replace_with_script_check(
        self,
        temp_path: str,
        original_path: str,
        script_wait_timeout: float = 60.0,
        **kwargs
    ) -> AtomicReplaceResult:
        """安全替换 - 包含脚本运行检测（向后兼容）"""
        return self.safe_atomic_replace(
            temp_path,
            original_path,
            script_wait_timeout=script_wait_timeout,
            **kwargs
        )
    
    def register_temp_file(
        self,
        temp_path: str,
        original_path: str = None,
        state: TempFileState = TempFileState.CREATED,
        content_hash: str = "",
        size_bytes: int = 0,
        metadata: Dict[str, Any] = None
    ) -> bool:
        with self._lock:
            if temp_path in self._registered_files:
                return False
            
            info = TempFileInfo(
                temp_path=temp_path,
                original_path=original_path or "",
                created_at=datetime.now(),
                state=state,
                content_hash=content_hash,
                size_bytes=size_bytes,
                metadata=metadata or {}
            )
            self._registered_files[temp_path] = info
            return True
    
    def unregister_temp_file(self, temp_path: str) -> bool:
        with self._lock:
            if temp_path in self._registered_files:
                del self._registered_files[temp_path]
                return True
            return False
    
    def _update_temp_file_state(self, temp_path: str, state: TempFileState):
        with self._lock:
            if temp_path in self._registered_files:
                self._registered_files[temp_path].state = state
    
    def get_registered_temp_files(self) -> List[TempFileInfo]:
        with self._lock:
            return list(self._registered_files.values())
    
    def get_temp_file_info(self, temp_path: str) -> Optional[TempFileInfo]:
        with self._lock:
            return self._registered_files.get(temp_path)
    
    def cleanup_temp_files(
        self,
        directory: str,
        pattern: str = "*_temp_*",
        expire_seconds: int = None,
        dry_run: bool = False,
        force: bool = False,
        cleanup_policy: CleanupPolicy = None,
        priority: CleanupPriority = None
    ) -> Dict[str, List[str]]:
        """清理临时文件 - 支持分级清理和优先级策略"""
        policy = cleanup_policy or CleanupPolicy()
        expire_seconds = expire_seconds or policy.max_age_seconds
        dir_path = Path(directory)
        
        if not dir_path.exists():
            return {
                "cleaned": [],
                "skipped": [],
                "errors": [f"目录不存在: {directory}"],
                "stats": {"total_size_mb": 0, "freed_size_mb": 0}
            }
        
        cleaned = []
        skipped = []
        errors = []
        now = datetime.now()
        total_size = 0
        freed_size = 0
        
        temp_files = list(dir_path.glob(pattern))
        prioritized_files = self._prioritize_cleanup(temp_files, policy, priority)
        
        for temp_file, file_priority in prioritized_files:
            if not temp_file.is_file():
                continue
            
            temp_path = str(temp_file)
            file_size = temp_file.stat().st_size
            total_size += file_size
            
            if not force and self.is_file_in_use(temp_path):
                skipped.append(f"{temp_path} (文件被占用)")
                continue
            
            if not force:
                info = self.get_temp_file_info(temp_path)
                if info and info.state == TempFileState.IN_USE:
                    skipped.append(f"{temp_path} (状态: IN_USE)")
                    continue
            
            if policy.preserve_patterns:
                should_preserve = False
                for preserve_pattern in policy.preserve_patterns:
                    if temp_file.match(preserve_pattern):
                        skipped.append(f"{temp_path} (匹配保留模式)")
                        should_preserve = True
                        break
                if should_preserve:
                    continue
            
            try:
                mtime = datetime.fromtimestamp(temp_file.stat().st_mtime)
                age_seconds = (now - mtime).total_seconds()
                
                should_clean = self._should_clean_file(
                    temp_file, age_seconds, expire_seconds, 
                    file_priority, policy, force
                )
                
                if should_clean:
                    if not dry_run:
                        temp_file.unlink()
                        self.unregister_temp_file(temp_path)
                        self._update_temp_file_state(temp_path, TempFileState.CLEANED)
                    cleaned.append(temp_path)
                    freed_size += file_size
                else:
                    skipped.append(f"{temp_path} (未过期或优先级不足)")
                    
            except Exception as e:
                errors.append(f"{temp_path}: {e}")
        
        if policy.aggressive_mode and not dry_run:
            additional_cleaned = self._aggressive_cleanup(dir_path, policy)
            cleaned.extend(additional_cleaned)
        
        logger.info(f"临时文件清理完成: 清理 {len(cleaned)} 个, 跳过 {len(skipped)} 个, 错误 {len(errors)} 个, 释放 {freed_size / (1024*1024):.2f}MB")
        
        return {
            "cleaned": cleaned,
            "skipped": skipped,
            "errors": errors,
            "stats": {
                "total_size_mb": round(total_size / (1024*1024), 2),
                "freed_size_mb": round(freed_size / (1024*1024), 2),
                "files_processed": len(temp_files),
                "priority_used": priority.value if priority else CleanupPriority.NORMAL.value
            }
        }
    
    def _prioritize_cleanup(
        self,
        files: List[Path],
        policy: CleanupPolicy,
        priority: CleanupPriority = None
    ) -> List[Tuple[Path, CleanupPriority]]:
        """根据优先级排序待清理文件"""
        prioritized = []
        
        for file_path in files:
            try:
                file_priority = self._determine_file_priority(file_path, policy)
                if priority and file_priority.value < priority.value:
                    continue
                prioritized.append((file_path, file_priority))
            except Exception:
                prioritized.append((file_path, CleanupPriority.NORMAL))
        
        prioritized.sort(key=lambda x: x[1].value, reverse=True)
        
        return prioritized
    
    def _determine_file_priority(self, file_path: Path, policy: CleanupPolicy) -> CleanupPriority:
        """确定文件清理优先级"""
        try:
            stat = file_path.stat()
            age_hours = (datetime.now() - datetime.fromtimestamp(stat.st_mtime)).total_seconds() / 3600
            size_mb = stat.st_size / (1024 * 1024)
            
            if age_hours > 24:
                return CleanupPriority.CRITICAL
            elif age_hours > 12 or size_mb > 10:
                return CleanupPriority.HIGH
            elif age_hours > 6 or size_mb > 5:
                return CleanupPriority.NORMAL
            else:
                return CleanupPriority.LOW
                
        except Exception:
            return CleanupPriority.NORMAL
    
    def _should_clean_file(
        self,
        file_path: Path,
        age_seconds: float,
        expire_seconds: int,
        priority: CleanupPriority,
        policy: CleanupPolicy,
        force: bool
    ) -> bool:
        """判断是否应该清理文件"""
        if force:
            return True
        
        if age_seconds > expire_seconds:
            return True
        
        if priority == CleanupPriority.CRITICAL and age_seconds > expire_seconds * 0.5:
            return True
        
        if policy.aggressive_mode and age_seconds > expire_seconds * 0.7:
            return True
        
        try:
            disk_usage = shutil.disk_usage(str(file_path.parent))
            free_gb = disk_usage.free / (1024 ** 3)
            
            if free_gb < policy.min_disk_free_mb / 1024:
                return True
        except Exception:
            pass
        
        return False
    
    def _aggressive_cleanup(self, dir_path: Path, policy: CleanupPolicy) -> List[str]:
        """激进清理模式"""
        cleaned = []
        
        try:
            disk_usage = shutil.disk_usage(str(dir_path))
            free_mb = disk_usage.free / (1024 * 1024)
            
            if free_mb < policy.min_disk_free_mb:
                logger.warning(f"磁盘空间不足 ({free_mb:.2f}MB < {policy.min_disk_free_mb}MB)，启用激进清理")
                
                for temp_file in dir_path.glob("*_temp_*"):
                    if temp_file.is_file():
                        try:
                            if not self.is_file_in_use(str(temp_file)):
                                temp_file.unlink()
                                cleaned.append(str(temp_file))
                        except Exception:
                            pass
        except Exception as e:
            logger.error(f"激进清理失败: {e}")
        
        return cleaned
    
    def scheduled_cleanup(
        self,
        directories: List[str],
        interval_seconds: int = 300,
        policy: CleanupPolicy = None,
        callback: Callable[[Dict], None] = None
    ) -> None:
        """定时清理调度"""
        policy = policy or CleanupPolicy()
        
        def cleanup_task():
            while True:
                try:
                    for directory in directories:
                        result = self.cleanup_temp_files(
                            directory,
                            cleanup_policy=policy
                        )
                        if callback:
                            callback(result)
                    time.sleep(interval_seconds)
                except Exception as e:
                    logger.error(f"定时清理任务失败: {e}")
                    time.sleep(60)
        
        thread = threading.Thread(target=cleanup_task, daemon=True)
        thread.start()
        logger.info(f"已启动定时清理任务，间隔: {interval_seconds}秒")
    
    def cleanup_by_age_tiers(
        self,
        directory: str,
        tiers: Dict[str, int] = None
    ) -> Dict[str, Dict[str, List[str]]]:
        """按年龄层级清理"""
        tiers = tiers or {
            "critical": 86400,
            "high": 43200,
            "normal": 21600,
            "low": 3600
        }
        
        results = {}
        
        for tier_name, max_age in tiers.items():
            priority = {
                "critical": CleanupPriority.CRITICAL,
                "high": CleanupPriority.HIGH,
                "normal": CleanupPriority.NORMAL,
                "low": CleanupPriority.LOW
            }.get(tier_name, CleanupPriority.NORMAL)
            
            result = self.cleanup_temp_files(
                directory,
                expire_seconds=max_age,
                priority=priority
            )
            results[tier_name] = result
        
        return results
    
    def cleanup_orphaned_files(
        self,
        directory: str,
        pattern: str = "*_temp_*"
    ) -> Dict[str, List[str]]:
        """清理孤立临时文件（未注册的）"""
        dir_path = Path(directory)
        
        if not dir_path.exists():
            return {
                "cleaned": [],
                "errors": [f"目录不存在: {directory}"]
            }
        
        cleaned = []
        errors = []
        
        for temp_file in dir_path.glob(pattern):
            if not temp_file.is_file():
                continue
            
            temp_path = str(temp_file)
            
            if temp_path not in self._registered_files:
                try:
                    if not self.is_file_in_use(temp_path):
                        temp_file.unlink()
                        cleaned.append(temp_path)
                except Exception as e:
                    errors.append(f"{temp_path}: {e}")
        
        logger.info(f"孤立文件清理完成: 清理 {len(cleaned)} 个")
        
        return {
            "cleaned": cleaned,
            "errors": errors
        }
    
    def cleanup_all_registered(self, dry_run: bool = False) -> Dict[str, List[str]]:
        cleaned = []
        errors = []
        
        with self._lock:
            temp_files = list(self._registered_files.keys())
        
        for temp_path in temp_files:
            temp_file = Path(temp_path)
            try:
                if temp_file.exists():
                    if not dry_run:
                        temp_file.unlink()
                    cleaned.append(temp_path)
                self.unregister_temp_file(temp_path)
            except Exception as e:
                errors.append(f"{temp_path}: {e}")
        
        return {
            "cleaned": cleaned,
            "errors": errors
        }
    
    def cleanup_backups(
        self,
        directory: str,
        pattern: str = "*.bak_*",
        expire_seconds: int = None,
        dry_run: bool = False
    ) -> Dict[str, List[str]]:
        """清理备份文件"""
        expire_seconds = expire_seconds or self.expire_seconds * 24
        dir_path = Path(directory)
        
        if not dir_path.exists():
            return {
                "cleaned": [],
                "skipped": [],
                "errors": [f"目录不存在: {directory}"]
            }
        
        cleaned = []
        skipped = []
        errors = []
        now = datetime.now()
        
        for backup_file in dir_path.glob(pattern):
            if not backup_file.is_file():
                continue
            
            try:
                mtime = datetime.fromtimestamp(backup_file.stat().st_mtime)
                age_seconds = (now - mtime).total_seconds()
                
                if age_seconds > expire_seconds:
                    if not dry_run:
                        backup_file.unlink()
                    cleaned.append(str(backup_file))
                else:
                    skipped.append(str(backup_file))
                    
            except Exception as e:
                errors.append(f"{backup_file}: {e}")
        
        return {
            "cleaned": cleaned,
            "skipped": skipped,
            "errors": errors
        }
    
    def get_replace_history(self, limit: int = 100) -> List[Dict[str, Any]]:
        """获取替换历史"""
        return self._replace_history[-limit:]
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息 - 增强版"""
        with self._lock:
            total_registered = len(self._registered_files)
            states = {}
            total_size = 0
            for info in self._registered_files.values():
                state_name = info.state.value
                states[state_name] = states.get(state_name, 0) + 1
                total_size += info.size_bytes
        
        total_replaces = len(self._replace_history)
        successful_replaces = sum(1 for r in self._replace_history if r.get('success', False))
        
        conflict_history = self._file_lock_detector.get_conflict_history(50)
        conflict_types = {}
        for conflict in conflict_history:
            type_name = conflict.conflict_type.value
            conflict_types[type_name] = conflict_types.get(type_name, 0) + 1
        
        return {
            "registered_temp_files": total_registered,
            "state_distribution": states,
            "total_size_mb": round(total_size / (1024 * 1024), 2),
            "total_replaces": total_replaces,
            "successful_replaces": successful_replaces,
            "failed_replaces": total_replaces - successful_replaces,
            "success_rate": round(successful_replaces / total_replaces * 100, 2) if total_replaces > 0 else 0,
            "has_psutil": HAS_PSUTIL,
            "conflict_history_count": len(conflict_history),
            "conflict_types": conflict_types
        }
    
    def detect_file_conflicts(
        self,
        file_path: str,
        comprehensive: bool = True
    ) -> ConflictDetectionResult:
        """检测文件冲突 - 增强版"""
        return self._file_lock_detector.detect_conflicts(
            file_path,
            check_process=comprehensive,
            check_temp_files=comprehensive,
            check_permissions=comprehensive,
            check_disk_space=comprehensive
        )
    
    def get_process_health(self, script_path: str) -> Optional[ProcessHealthInfo]:
        """获取进程健康状态"""
        return self._process_detector.get_process_health(script_path)
    
    def is_process_stuck(self, script_path: str) -> bool:
        """检测进程是否卡住"""
        return self._process_detector.is_process_stuck(script_path)
    
    def predict_script_completion(self, script_path: str) -> Optional[float]:
        """预测脚本完成时间"""
        return self._process_detector.predict_completion_time(script_path)
    
    def resolve_conflict(self, conflict: ConflictInfo) -> ConflictResolution:
        """解决冲突 - 使用智能冲突解决器"""
        return self._conflict_resolver.analyze_conflict(conflict)
    
    def resolve_conflicts_batch(self, conflicts: List[ConflictInfo]) -> List[ConflictResolution]:
        """批量解决冲突"""
        return self._conflict_resolver.batch_analyze(conflicts)
    
    def get_best_conflict_resolution(self, conflicts: List[ConflictInfo]) -> Optional[ConflictResolution]:
        """获取最佳冲突解决方案"""
        return self._conflict_resolver.get_best_resolution(conflicts)
    
    def smart_wait_for_script(
        self,
        script_path: str,
        timeout: float = 60.0,
        check_health: bool = True
    ) -> SmartWaitResult:
        """智能等待脚本 - 结合进程状态分析"""
        start_time = time.time()
        iterations = 0
        
        while time.time() - start_time < timeout:
            iterations += 1
            
            state = self._smart_analyzer.get_detailed_state(script_path)
            
            if state is None:
                return SmartWaitResult(
                    success=True,
                    waited_seconds=time.time() - start_time,
                    iterations=iterations,
                    strategy_used=WaitStrategy.ADAPTIVE,
                    final_state=ProcessState.STOPPED
                )
            
            if check_health and state.health_score < 30:
                logger.warning(f"进程健康分数过低: {state.health_score:.1f}")
            
            if state.state == ProcessState.ZOMBIE:
                return SmartWaitResult(
                    success=True,
                    waited_seconds=time.time() - start_time,
                    iterations=iterations,
                    strategy_used=WaitStrategy.ADAPTIVE,
                    final_state=ProcessState.ZOMBIE
                )
            
            predicted = state.predicted_completion
            if predicted and predicted < (timeout - (time.time() - start_time)):
                wait_time = min(predicted, 5.0)
            else:
                wait_time = min(1.0 * (1.5 ** min(iterations, 5)), 5.0)
            
            time.sleep(wait_time)
        
        return SmartWaitResult(
            success=False,
            waited_seconds=timeout,
            iterations=iterations,
            strategy_used=WaitStrategy.ADAPTIVE,
            timeout=True,
            error=f"智能等待超时: {script_path}"
        )
    
    def is_safe_to_modify(self, script_path: str) -> Tuple[bool, str]:
        """判断是否可以安全修改文件"""
        return self._smart_analyzer.is_safe_to_modify(script_path)
    
    def predict_process_behavior(self, script_path: str) -> Dict[str, Any]:
        """预测进程行为"""
        return self._smart_analyzer.predict_behavior(script_path)
    
    def get_detailed_process_state(self, script_path: str) -> Optional[ProcessStateInfo]:
        """获取进程详细状态"""
        return self._smart_analyzer.get_detailed_state(script_path)
    
    def execute_with_retry(
        self,
        operation: Callable[[], T],
        on_retry: Optional[Callable[[int, str, float], None]] = None
    ) -> Tuple[bool, Optional[T], Optional[str]]:
        """执行操作并在失败时重试"""
        return self._retry_manager.execute_with_retry(operation, on_retry)
    
    def verify_replacement_full(
        self,
        source_path: str,
        target_path: str,
        backup_path: Optional[str] = None
    ) -> VerificationResult:
        """完整验证替换结果"""
        context = self._atomic_verifier.create_context(source_path, target_path, backup_path)
        return self._atomic_verifier.full_verify(context)
    
    def verify_replacement_quick(
        self,
        target_path: str,
        expected_hash: str,
        expected_size: int
    ) -> VerificationResult:
        """快速验证替换结果"""
        return self._atomic_verifier.quick_verify(target_path, expected_hash, expected_size)
    
    def add_cleanup_schedule(
        self,
        name: str,
        directories: List[str],
        interval_seconds: int = 300,
        policy: Optional[CleanupPolicy] = None
    ) -> CleanupSchedule:
        """添加清理调度"""
        return self._cleanup_scheduler.add_schedule(name, directories, interval_seconds, policy)
    
    def remove_cleanup_schedule(self, name: str) -> bool:
        """移除清理调度"""
        return self._cleanup_scheduler.remove_schedule(name)
    
    def start_cleanup_scheduler(self):
        """启动清理调度器"""
        self._cleanup_scheduler.start()
    
    def stop_cleanup_scheduler(self):
        """停止清理调度器"""
        self._cleanup_scheduler.stop()
    
    def run_cleanup_now(self, name: str) -> Optional[CleanupResult]:
        """立即执行清理调度"""
        return self._cleanup_scheduler.run_now(name)
    
    def get_cleanup_schedule_status(self, name: str) -> Optional[Dict[str, Any]]:
        """获取清理调度状态"""
        return self._cleanup_scheduler.get_schedule_status(name)
    
    def get_all_cleanup_schedules(self) -> Dict[str, Dict[str, Any]]:
        """获取所有清理调度状态"""
        return self._cleanup_scheduler.get_all_schedules()
    
    def enhanced_safe_replace(
        self,
        temp_path: str,
        original_path: str,
        max_retries: int = 3,
        verify_level: VerificationLevel = VerificationLevel.HASH
    ) -> AtomicReplaceResult:
        """增强安全替换 - 集成冲突检测、智能等待和验证"""
        
        conflicts = self.detect_file_conflicts(original_path)
        
        if conflicts.has_conflict:
            resolution = self.get_best_conflict_resolution(conflicts.conflicts)
            
            if resolution and resolution.action == ConflictResolutionAction.ABORT:
                return AtomicReplaceResult(
                    success=False,
                    message=f"检测到严重冲突，中止操作: {resolution.reason}",
                    error="CONFLICT_DETECTED"
                )
            
            if resolution and resolution.action == ConflictResolutionAction.WAIT:
                wait_params = resolution.parameters
                self.wait_for_release(
                    original_path,
                    timeout=wait_params.get('timeout', 30.0)
                )
        
        safe, reason = self.is_safe_to_modify(original_path)
        if not safe:
            wait_result = self.smart_wait_for_script(original_path, timeout=30.0)
            if not wait_result.success:
                return AtomicReplaceResult(
                    success=False,
                    message=f"等待脚本停止失败: {wait_result.error}",
                    error="SCRIPT_WAIT_TIMEOUT"
                )
        
        def do_replace():
            return self.atomic_replace(
                temp_path,
                original_path,
                verify=(verify_level != VerificationLevel.NONE),
                verification_level=verify_level
            )
        
        success, result, error = self.execute_with_retry(
            lambda: do_replace(),
            on_retry=lambda attempt, err, delay: logger.warning(f"替换重试 {attempt}: {err}")
        )
        
        if success and result:
            return result
        
        return AtomicReplaceResult(
            success=False,
            message=f"替换失败: {error}",
            error=error
        )
    
    @contextmanager
    def temp_file_context(
        self,
        original_path: str,
        content: Optional[str] = None,
        auto_replace: bool = True,
        safe_replace: bool = False
    ):
        result = self.create_temp_file(original_path, content=content)
        
        if not result.success:
            raise RuntimeError(result.message)
        
        temp_path = result.temp_path
        
        try:
            self._update_temp_file_state(temp_path, TempFileState.IN_USE)
            yield temp_path
            
            if auto_replace:
                if safe_replace:
                    replace_result = self.safe_atomic_replace(temp_path, original_path)
                else:
                    replace_result = self.atomic_replace(temp_path, original_path)
                
                if not replace_result.success:
                    raise RuntimeError(replace_result.message)
                    
        except Exception:
            if Path(temp_path).exists():
                Path(temp_path).unlink()
                self.unregister_temp_file(temp_path)
                self._update_temp_file_state(temp_path, TempFileState.ERROR)
            raise


_process_detector = ProcessDetector()
_file_lock_detector = FileLockDetector()


def create_temp_file(original_path: str, **kwargs) -> TempFileResult:
    manager = TempFileManager()
    return manager.create_temp_file(original_path, **kwargs)


def atomic_replace(temp_path: str, original_path: str, **kwargs) -> AtomicReplaceResult:
    manager = TempFileManager()
    return manager.atomic_replace(temp_path, original_path, **kwargs)


def is_file_in_use(file_path: str) -> bool:
    manager = TempFileManager()
    return manager.is_file_in_use(file_path)


def is_script_running(script_path: str) -> bool:
    return _process_detector.is_script_running(script_path)


def wait_for_release(file_path: str, timeout: int = None) -> WaitResult:
    manager = TempFileManager()
    return manager.wait_for_release(file_path, timeout)


def wait_for_script_stop(script_path: str, timeout: float = None) -> WaitResult:
    return _process_detector.wait_for_script_stop(script_path, timeout=timeout)


def cleanup_temp_files(directory: str, **kwargs) -> Dict[str, List[str]]:
    manager = TempFileManager()
    return manager.cleanup_temp_files(directory, **kwargs)


def get_running_scripts(script_name: str = None) -> List[ScriptRunInfo]:
    return _process_detector.detect_running_scripts(script_name)


def get_file_lock_info(file_path: str) -> FileLockResult:
    return _file_lock_detector.is_locked(file_path)


def safe_atomic_replace(temp_path: str, original_path: str, **kwargs) -> AtomicReplaceResult:
    manager = TempFileManager()
    return manager.safe_atomic_replace(temp_path, original_path, **kwargs)


def detect_file_conflicts(file_path: str, comprehensive: bool = True) -> ConflictDetectionResult:
    manager = TempFileManager()
    return manager.detect_file_conflicts(file_path, comprehensive)


def get_process_health(script_path: str) -> Optional[ProcessHealthInfo]:
    return _process_detector.get_process_health(script_path)


def is_process_stuck(script_path: str) -> bool:
    return _process_detector.is_process_stuck(script_path)


def predict_script_completion(script_path: str) -> Optional[float]:
    return _process_detector.predict_completion_time(script_path)


def cleanup_by_age_tiers(directory: str, tiers: Dict[str, int] = None) -> Dict[str, Dict[str, List[str]]]:
    manager = TempFileManager()
    return manager.cleanup_by_age_tiers(directory, tiers)


def cleanup_orphaned_files(directory: str, pattern: str = "*_temp_*") -> Dict[str, List[str]]:
    manager = TempFileManager()
    return manager.cleanup_orphaned_files(directory, pattern)


def run_cli():
    """CLI入口"""
    parser = argparse.ArgumentParser(
        description='临时文件管理器 - 自迭代冲突安全处理',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 创建临时文件
  python temp_file_manager.py create script.py --content "print('hello')"
  
  # 检测脚本是否运行
  python temp_file_manager.py check script.py
  
  # 安全替换文件（等待脚本停止）
  python temp_file_manager.py replace script.py.tmp script.py --wait-script
  
  # 清理临时文件
  python temp_file_manager.py cleanup ./ --expire 3600
  
  # 查看统计信息
  python temp_file_manager.py stats
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='可用命令')
    
    create_parser = subparsers.add_parser('create', help='创建临时文件')
    create_parser.add_argument('file', help='原文件路径')
    create_parser.add_argument('--content', '-c', help='文件内容')
    create_parser.add_argument('--copy', action='store_true', help='复制原文件')
    
    replace_parser = subparsers.add_parser('replace', help='原子替换文件')
    replace_parser.add_argument('temp_file', help='临时文件路径')
    replace_parser.add_argument('original_file', help='原文件路径')
    replace_parser.add_argument('--wait-script', action='store_true', help='等待脚本停止')
    replace_parser.add_argument('--timeout', '-t', type=float, default=60, help='等待超时')
    replace_parser.add_argument('--no-backup', action='store_true', help='不创建备份')
    replace_parser.add_argument('--no-verify', action='store_true', help='不验证')
    
    check_parser = subparsers.add_parser('check', help='检测文件/脚本状态')
    check_parser.add_argument('file', help='文件路径')
    check_parser.add_argument('--script', action='store_true', help='检测脚本运行状态')
    check_parser.add_argument('--health', action='store_true', help='检测进程健康状态')
    check_parser.add_argument('--conflicts', action='store_true', help='检测文件冲突')
    
    wait_parser = subparsers.add_parser('wait', help='等待文件释放或脚本停止')
    wait_parser.add_argument('file', help='文件路径')
    wait_parser.add_argument('--script', action='store_true', help='等待脚本停止')
    wait_parser.add_argument('--timeout', '-t', type=float, default=60, help='超时时间')
    wait_parser.add_argument('--strategy', '-s', choices=['linear', 'exponential', 'adaptive', 'fibonacci'], 
                            default='exponential', help='等待策略')
    
    cleanup_parser = subparsers.add_parser('cleanup', help='清理临时文件')
    cleanup_parser.add_argument('directory', help='目录路径')
    cleanup_parser.add_argument('--expire', '-e', type=int, default=3600, help='过期时间(秒)')
    cleanup_parser.add_argument('--force', '-f', action='store_true', help='强制清理')
    cleanup_parser.add_argument('--dry-run', action='store_true', help='试运行')
    cleanup_parser.add_argument('--priority', '-p', choices=['low', 'normal', 'high', 'critical'],
                               default='normal', help='清理优先级')
    cleanup_parser.add_argument('--orphaned', action='store_true', help='清理孤立文件')
    cleanup_parser.add_argument('--tiers', action='store_true', help='按年龄层级清理')
    
    subparsers.add_parser('stats', help='显示统计信息')
    
    list_parser = subparsers.add_parser('list', help='列出运行中的脚本')
    list_parser.add_argument('--filter', '-f', help='过滤脚本名')
    list_parser.add_argument('--health', action='store_true', help='显示健康状态')
    
    predict_parser = subparsers.add_parser('predict', help='预测脚本完成时间')
    predict_parser.add_argument('file', help='脚本路径')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    manager = TempFileManager()
    
    if args.command == 'create':
        result = manager.create_temp_file(
            args.file,
            content=args.content,
            copy_original=args.copy
        )
        if result.success:
            print(f"临时文件创建成功: {result.temp_path}")
        else:
            print(f"创建失败: {result.message}")
            sys.exit(1)
    
    elif args.command == 'replace':
        kwargs = {
            'backup': not args.no_backup,
            'verify': not args.no_verify
        }
        
        if args.wait_script:
            result = manager.safe_atomic_replace(
                args.temp_file,
                args.original_file,
                script_wait_timeout=args.timeout,
                **kwargs
            )
        else:
            result = manager.atomic_replace(
                args.temp_file,
                args.original_file,
                **kwargs
            )
        
        if result.success:
            print(f"替换成功: {args.original_file}")
            if result.backup_path:
                print(f"备份: {result.backup_path}")
            if result.waited_for_script:
                print(f"等待脚本停止: {result.script_wait_seconds:.2f}秒")
        else:
            print(f"替换失败: {result.message}")
            sys.exit(1)
    
    elif args.command == 'check':
        if args.script:
            if manager.is_script_running(args.file):
                info = manager.get_script_run_info(args.file)
                print(f"脚本正在运行:")
                print(f"  PID: {info.pid}")
                print(f"  命令行: {info.command_line}")
                print(f"  CPU: {info.cpu_percent}%")
                print(f"  内存: {info.memory_mb:.2f}MB")
            else:
                print("脚本未运行")
        elif args.health:
            health = manager.get_process_health(args.file)
            if health:
                print(f"进程健康状态:")
                print(f"  PID: {health.pid}")
                print(f"  健康分数: {health.health_score:.1f}/100")
                print(f"  CPU: {health.cpu_percent}%")
                print(f"  内存: {health.memory_mb:.2f}MB")
                print(f"  运行时间: {health.uptime_seconds:.1f}秒")
                print(f"  响应性: {'正常' if health.is_responsive else '无响应'}")
                print(f"  资源趋势: {health.resource_trend}")
                if manager.is_process_stuck(args.file):
                    print(f"  警告: 进程可能已卡住!")
            else:
                print("无法获取进程健康状态")
        elif args.conflicts:
            conflicts = manager.detect_file_conflicts(args.file)
            print(f"冲突检测结果:")
            print(f"  存在冲突: {'是' if conflicts.has_conflict else '否'}")
            print(f"  总体严重程度: {conflicts.total_severity.value}")
            if conflicts.conflicts:
                print(f"  检测到的冲突:")
                for c in conflicts.conflicts:
                    print(f"    - {c.conflict_type.value}: {c.severity.value}")
                    if c.holder_info:
                        print(f"      持有者: {c.holder_info}")
                    print(f"      建议: {c.suggested_action}")
            if conflicts.predicted_conflicts:
                print(f"  预测的潜在冲突:")
                for c in conflicts.predicted_conflicts:
                    print(f"    - {c.conflict_type.value}: {c.suggested_action}")
        else:
            lock_info = manager.get_file_lock_info(args.file)
            if lock_info.locked:
                print(f"文件被锁定")
                holder = _file_lock_detector.get_lock_holder(args.file)
                if holder:
                    print(f"  锁定者: {holder}")
            else:
                print("文件未被锁定")
    
    elif args.command == 'wait':
        if args.script:
            print(f"等待脚本停止: {args.file}")
            result = manager.wait_for_script_stop(args.file, timeout=args.timeout)
            if result.success:
                print(f"脚本已停止，等待时间: {result.waited_seconds:.2f}秒")
            else:
                print(f"等待超时")
                sys.exit(1)
        else:
            print(f"等待文件释放: {args.file}")
            result = manager.wait_for_release(args.file, timeout=args.timeout)
            if result.success:
                print(f"文件已释放，等待时间: {result.waited_seconds:.2f}秒")
            else:
                print(f"等待超时")
                sys.exit(1)
    
    elif args.command == 'cleanup':
        priority_map = {
            'low': CleanupPriority.LOW,
            'normal': CleanupPriority.NORMAL,
            'high': CleanupPriority.HIGH,
            'critical': CleanupPriority.CRITICAL
        }
        
        if args.orphaned:
            result = manager.cleanup_orphaned_files(args.directory)
            print(f"孤立文件清理完成:")
            print(f"  已清理: {len(result['cleaned'])}")
            print(f"  错误: {len(result['errors'])}")
        elif args.tiers:
            results = manager.cleanup_by_age_tiers(args.directory)
            print(f"层级清理完成:")
            for tier, tier_result in results.items():
                print(f"  {tier}: 清理 {len(tier_result['cleaned'])} 个")
        else:
            result = manager.cleanup_temp_files(
                args.directory,
                expire_seconds=args.expire,
                force=args.force,
                dry_run=args.dry_run,
                priority=priority_map.get(args.priority, CleanupPriority.NORMAL)
            )
            print(f"清理完成:")
            print(f"  已清理: {len(result['cleaned'])}")
            print(f"  已跳过: {len(result['skipped'])}")
            print(f"  错误: {len(result['errors'])}")
            if 'stats' in result:
                print(f"  释放空间: {result['stats']['freed_size_mb']:.2f}MB")
    
    elif args.command == 'stats':
        stats = manager.get_statistics()
        print("=== 临时文件管理器统计 ===")
        print(f"已注册临时文件: {stats['registered_temp_files']}")
        print(f"总大小: {stats['total_size_mb']:.2f}MB")
        print(f"状态分布: {stats['state_distribution']}")
        print(f"总替换次数: {stats['total_replaces']}")
        print(f"成功替换: {stats['successful_replaces']}")
        print(f"失败替换: {stats['failed_replaces']}")
        print(f"成功率: {stats['success_rate']}%")
        print(f"支持psutil: {stats['has_psutil']}")
        if stats.get('conflict_types'):
            print(f"冲突类型统计: {stats['conflict_types']}")
    
    elif args.command == 'list':
        scripts = get_running_scripts(args.filter)
        print(f"运行中的Python脚本: {len(scripts)}")
        for info in scripts[:20]:
            print(f"  PID {info.pid}: {info.script_path}")
            if info.cpu_percent > 0:
                print(f"       CPU: {info.cpu_percent}%, 内存: {info.memory_mb:.2f}MB")
            if args.health:
                health = manager.get_process_health(info.script_path)
                if health:
                    print(f"       健康分数: {health.health_score:.1f}, 趋势: {health.resource_trend}")
    
    elif args.command == 'predict':
        prediction = manager.predict_script_completion(args.file)
        if prediction is not None:
            print(f"预测完成时间: 约 {prediction:.1f} 秒")
        else:
            print("无法预测完成时间")
            sys.exit(1)


class IntelligentProcessStateDetector:
    """智能进程状态检测器 - 增强版运行状态智能检测"""
    
    def __init__(self, process_detector: ProcessDetector):
        self._detector = process_detector
        self._state_history: Dict[int, List[Dict[str, Any]]] = {}
        self._prediction_models: Dict[str, Any] = {}
        self._anomaly_thresholds = {
            'cpu_spike': 50.0,
            'memory_leak_rate': 10.0,
            'unresponsive_time': 30.0,
            'zombie_detection_time': 60.0
        }
        self._lock = threading.Lock()
    
    def detect_intelligent_state(self, script_path: str) -> Dict[str, Any]:
        """智能检测进程状态"""
        state = self._detector.get_script_info(script_path)
        
        if not state:
            return {
                'status': 'not_running',
                'confidence': 1.0,
                'prediction': None,
                'anomalies': [],
                'recommendations': ['脚本未运行，可以安全操作']
            }
        
        health = self._detector.get_process_health(script_path)
        
        result = {
            'status': 'running',
            'pid': state.pid,
            'confidence': 0.0,
            'prediction': None,
            'anomalies': [],
            'recommendations': []
        }
        
        if health:
            result['health_score'] = health.health_score
            result['cpu_percent'] = health.cpu_percent
            result['memory_mb'] = health.memory_mb
            result['uptime_seconds'] = health.uptime_seconds
            result['is_responsive'] = health.is_responsive
            result['resource_trend'] = health.resource_trend
            
            anomalies = self._detect_anomalies(health, state.pid)
            result['anomalies'] = anomalies
            
            prediction = self._predict_state(health, state.pid)
            result['prediction'] = prediction
            
            result['confidence'] = self._calculate_confidence(health, anomalies)
            
            result['recommendations'] = self._generate_recommendations(health, anomalies, prediction)
        
        self._record_state(state.pid, result)
        
        return result
    
    def _detect_anomalies(self, health: ProcessHealthInfo, pid: int) -> List[Dict[str, Any]]:
        """检测异常"""
        anomalies = []
        
        if not health.is_responsive:
            anomalies.append({
                'type': 'unresponsive',
                'severity': 'high',
                'description': '进程无响应',
                'suggested_action': '考虑终止进程'
            })
        
        if health.cpu_percent > 90:
            anomalies.append({
                'type': 'high_cpu',
                'severity': 'medium',
                'description': f'CPU使用率过高: {health.cpu_percent:.1f}%',
                'suggested_action': '等待CPU使用率下降'
            })
        
        if health.memory_mb > 500:
            anomalies.append({
                'type': 'high_memory',
                'severity': 'medium',
                'description': f'内存使用过高: {health.memory_mb:.1f}MB',
                'suggested_action': '监控内存使用'
            })
        
        with self._lock:
            if pid in self._state_history:
                history = self._state_history[pid]
                if len(history) >= 5:
                    recent_memory = [h.get('memory_mb', 0) for h in history[-5:]]
                    if recent_memory:
                        avg_memory = sum(recent_memory) / len(recent_memory)
                        if health.memory_mb > avg_memory * 1.5:
                            anomalies.append({
                                'type': 'memory_leak',
                                'severity': 'high',
                                'description': f'疑似内存泄漏: {health.memory_mb:.1f}MB (平均: {avg_memory:.1f}MB)',
                                'suggested_action': '检查内存泄漏'
                            })
        
        if health.health_score < 30:
            anomalies.append({
                'type': 'low_health',
                'severity': 'critical',
                'description': f'进程健康分数过低: {health.health_score:.1f}',
                'suggested_action': '建议终止进程'
            })
        
        return anomalies
    
    def _predict_state(self, health: ProcessHealthInfo, pid: int) -> Dict[str, Any]:
        """预测进程状态"""
        prediction = {
            'estimated_completion': None,
            'state_trend': 'unknown',
            'safe_to_modify': False,
            'confidence': 0.0
        }
        
        if health.resource_trend == 'cooling_down':
            prediction['estimated_completion'] = 5.0
            prediction['state_trend'] = 'completing'
            prediction['safe_to_modify'] = True
            prediction['confidence'] = 0.8
        elif health.resource_trend == 'stable':
            prediction['estimated_completion'] = 15.0
            prediction['state_trend'] = 'stable'
            prediction['safe_to_modify'] = False
            prediction['confidence'] = 0.6
        elif health.resource_trend in ['cpu_intensive', 'memory_intensive']:
            prediction['estimated_completion'] = 30.0
            prediction['state_trend'] = 'busy'
            prediction['safe_to_modify'] = False
            prediction['confidence'] = 0.5
        elif health.resource_trend == 'resource_intensive':
            prediction['estimated_completion'] = 60.0
            prediction['state_trend'] = 'very_busy'
            prediction['safe_to_modify'] = False
            prediction['confidence'] = 0.4
        
        if health.health_score < 30:
            prediction['safe_to_modify'] = True
            prediction['state_trend'] = 'unhealthy'
        
        return prediction
    
    def _calculate_confidence(self, health: ProcessHealthInfo, anomalies: List[Dict]) -> float:
        """计算预测置信度"""
        confidence = 0.5
        
        if health.is_responsive:
            confidence += 0.2
        
        if health.uptime_seconds > 10:
            confidence += 0.1
        
        if health.resource_trend != 'unknown':
            confidence += 0.1
        
        critical_anomalies = [a for a in anomalies if a.get('severity') == 'critical']
        confidence -= len(critical_anomalies) * 0.2
        
        return max(0.0, min(1.0, confidence))
    
    def _generate_recommendations(self, health: ProcessHealthInfo, anomalies: List[Dict], prediction: Dict) -> List[str]:
        """生成建议"""
        recommendations = []
        
        if prediction.get('safe_to_modify'):
            recommendations.append('可以安全修改文件')
        else:
            recommendations.append(f'等待进程完成 (预计 {prediction.get("estimated_completion", "?")} 秒)')
        
        critical_anomalies = [a for a in anomalies if a.get('severity') == 'critical']
        if critical_anomalies:
            recommendations.append('检测到严重异常，建议终止进程')
        
        if health.resource_trend == 'cooling_down':
            recommendations.append('进程正在冷却，即将完成')
        
        return recommendations
    
    def _record_state(self, pid: int, state: Dict[str, Any]):
        """记录状态历史"""
        with self._lock:
            if pid not in self._state_history:
                self._state_history[pid] = []
            
            self._state_history[pid].append({
                'timestamp': datetime.now().isoformat(),
                'health_score': state.get('health_score'),
                'cpu_percent': state.get('cpu_percent'),
                'memory_mb': state.get('memory_mb'),
                'resource_trend': state.get('resource_trend')
            })
            
            if len(self._state_history[pid]) > 50:
                self._state_history[pid] = self._state_history[pid][-50:]
    
    def get_state_history(self, pid: int) -> List[Dict[str, Any]]:
        """获取状态历史"""
        with self._lock:
            return self._state_history.get(pid, []).copy()


class EnhancedTimeoutManager:
    """增强超时管理器 - 智能超时等待和重试机制"""
    
    def __init__(self):
        self._timeout_history: List[Dict[str, Any]] = []
        self._adaptive_timeouts: Dict[str, float] = {}
        self._lock = threading.Lock()
    
    def smart_wait(
        self,
        check_func: Callable[[], bool],
        timeout: float = 30.0,
        strategy: str = 'adaptive',
        initial_interval: float = 0.5,
        max_interval: float = 5.0,
        callback: Optional[Callable[[float, int], None]] = None
    ) -> Dict[str, Any]:
        """智能等待"""
        start_time = time.time()
        current_interval = initial_interval
        iterations = 0
        total_wait = 0.0
        
        adaptive_state = {
            'successes': 0,
            'failures': 0,
            'last_interval': initial_interval
        }
        
        while time.time() - start_time < timeout:
            iterations += 1
            
            if check_func():
                elapsed = time.time() - start_time
                self._record_wait_result(True, elapsed, iterations, strategy)
                return {
                    'success': True,
                    'elapsed': elapsed,
                    'iterations': iterations,
                    'strategy': strategy,
                    'final_interval': current_interval
                }
            
            if callback:
                callback(time.time() - start_time, iterations)
            
            time.sleep(current_interval)
            total_wait += current_interval
            
            current_interval = self._calculate_next_interval(
                strategy, current_interval, initial_interval, 
                max_interval, iterations, adaptive_state
            )
        
        elapsed = time.time() - start_time
        self._record_wait_result(False, elapsed, iterations, strategy)
        
        return {
            'success': False,
            'elapsed': elapsed,
            'iterations': iterations,
            'strategy': strategy,
            'timeout': True,
            'final_interval': current_interval
        }
    
    def _calculate_next_interval(
        self,
        strategy: str,
        current: float,
        initial: float,
        max_interval: float,
        iteration: int,
        adaptive_state: Dict
    ) -> float:
        """计算下一次等待间隔"""
        if strategy == 'linear':
            return initial
        elif strategy == 'exponential':
            return min(current * 1.5, max_interval)
        elif strategy == 'exponential_jitter':
            jitter = current * 0.1 * (0.5 - random.random())
            return min(current * 1.5 + jitter, max_interval)
        elif strategy == 'fibonacci':
            fib = self._fibonacci(min(iteration, 15))
            return min(initial * fib, max_interval)
        elif strategy == 'adaptive':
            return self._adaptive_interval(adaptive_state, current, initial, max_interval)
        else:
            return initial
    
    def _adaptive_interval(
        self,
        state: Dict,
        current: float,
        initial: float,
        max_interval: float
    ) -> float:
        """自适应间隔"""
        total = state['successes'] + state['failures']
        if total > 0:
            success_rate = state['successes'] / total
            if success_rate > 0.7:
                state['last_interval'] = max(initial, current * 0.9)
            elif success_rate < 0.3:
                state['last_interval'] = min(max_interval, current * 1.1)
        
        jitter = state['last_interval'] * 0.1 * (0.5 - random.random())
        return max(initial, min(state['last_interval'] + jitter, max_interval))
    
    def _fibonacci(self, n: int) -> int:
        """斐波那契数"""
        if n <= 1:
            return 1
        a, b = 1, 1
        for _ in range(n - 1):
            a, b = b, a + b
        return b
    
    def _record_wait_result(self, success: bool, elapsed: float, iterations: int, strategy: str):
        """记录等待结果"""
        with self._lock:
            self._timeout_history.append({
                'timestamp': datetime.now().isoformat(),
                'success': success,
                'elapsed': elapsed,
                'iterations': iterations,
                'strategy': strategy
            })
            
            if len(self._timeout_history) > 200:
                self._timeout_history = self._timeout_history[-200:]
    
    def get_adaptive_timeout(self, operation_key: str, default: float = 30.0) -> float:
        """获取自适应超时"""
        with self._lock:
            if operation_key in self._adaptive_timeouts:
                return self._adaptive_timeouts[operation_key]
        return default
    
    def update_adaptive_timeout(self, operation_key: str, actual_time: float):
        """更新自适应超时"""
        with self._lock:
            current = self._adaptive_timeouts.get(operation_key, actual_time * 1.5)
            self._adaptive_timeouts[operation_key] = current * 0.7 + actual_time * 0.8
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        with self._lock:
            if not self._timeout_history:
                return {'total_waits': 0}
            
            successes = sum(1 for w in self._timeout_history if w['success'])
            total = len(self._timeout_history)
            
            return {
                'total_waits': total,
                'successful_waits': successes,
                'failed_waits': total - successes,
                'success_rate': round(successes / total * 100, 2) if total > 0 else 0,
                'average_iterations': sum(w['iterations'] for w in self._timeout_history) / total
            }


class EnhancedAtomicVerifier:
    """增强原子性验证器 - 多阶段文件替换验证"""
    
    def __init__(self):
        self._verification_history: List[Dict[str, Any]] = []
        self._lock = threading.Lock()
    
    def multi_stage_verify(
        self,
        source_path: str,
        target_path: str,
        stages: Optional[List[str]] = None,
        expected_hash: Optional[str] = None,
        expected_size: Optional[int] = None
    ) -> Dict[str, Any]:
        """多阶段验证"""
        stages = stages or [
            'existence',
            'size',
            'hash',
            'permissions',
            'integrity',
            'readability',
            'encoding'
        ]
        
        results = {
            'success': True,
            'stages_passed': 0,
            'stages_failed': 0,
            'stage_results': {},
            'errors': [],
            'warnings': []
        }
        
        target_file = Path(target_path)
        
        for stage in stages:
            stage_result = self._verify_stage(
                stage, source_path, target_path, 
                target_file, expected_hash, expected_size
            )
            
            results['stage_results'][stage] = stage_result
            
            if stage_result['passed']:
                results['stages_passed'] += 1
            else:
                results['stages_failed'] += 1
                results['errors'].append(f"{stage}: {stage_result.get('error', 'unknown error')}")
                
                if stage in ['existence', 'hash']:
                    results['success'] = False
                    break
        
        self._record_verification(results)
        
        return results
    
    def _verify_stage(
        self,
        stage: str,
        source_path: str,
        target_path: str,
        target_file: Path,
        expected_hash: Optional[str],
        expected_size: Optional[int]
    ) -> Dict[str, Any]:
        """验证单个阶段"""
        result = {'passed': False, 'error': None}
        
        try:
            if stage == 'existence':
                if target_file.exists():
                    result['passed'] = True
                else:
                    result['error'] = '文件不存在'
            
            elif stage == 'size':
                if not target_file.exists():
                    result['error'] = '文件不存在'
                else:
                    actual_size = target_file.stat().st_size
                    if expected_size and actual_size != expected_size:
                        result['error'] = f'大小不匹配: 期望 {expected_size}, 实际 {actual_size}'
                    else:
                        result['passed'] = True
                        result['size'] = actual_size
            
            elif stage == 'hash':
                if not target_file.exists():
                    result['error'] = '文件不存在'
                else:
                    actual_hash = self._calculate_hash(target_path)
                    if expected_hash and actual_hash != expected_hash:
                        result['error'] = f'哈希不匹配'
                    else:
                        result['passed'] = True
                        result['hash'] = actual_hash
            
            elif stage == 'permissions':
                if target_file.exists():
                    result['passed'] = True
                    result['permissions'] = oct(target_file.stat().st_mode)[-3:]
            
            elif stage == 'integrity':
                if target_file.exists():
                    with open(target_path, 'rb') as f:
                        header = f.read(1024)
                        if b'\x00' in header[:100]:
                            result['error'] = '文件可能损坏（包含空字节）'
                        else:
                            result['passed'] = True
            
            elif stage == 'readability':
                if target_file.exists():
                    try:
                        with open(target_path, 'r', encoding='utf-8', errors='ignore') as f:
                            f.read(1024)
                        result['passed'] = True
                    except Exception as e:
                        result['error'] = f'文件不可读: {e}'
            
            elif stage == 'encoding':
                if target_file.exists():
                    try:
                        content = target_file.read_bytes()
                        content.decode('utf-8')
                        result['passed'] = True
                        result['encoding'] = 'utf-8'
                    except UnicodeDecodeError:
                        result['passed'] = True
                        result['encoding'] = 'binary'
        
        except Exception as e:
            result['error'] = str(e)
        
        return result
    
    def _calculate_hash(self, file_path: str) -> str:
        """计算文件哈希"""
        hasher = hashlib.sha256()
        try:
            with open(file_path, 'rb') as f:
                for chunk in iter(lambda: f.read(8192), b''):
                    hasher.update(chunk)
            return hasher.hexdigest()[:16]
        except Exception:
            return ""
    
    def _record_verification(self, results: Dict[str, Any]):
        """记录验证结果"""
        with self._lock:
            self._verification_history.append({
                'timestamp': datetime.now().isoformat(),
                **results
            })
            
            if len(self._verification_history) > 100:
                self._verification_history = self._verification_history[-100:]
    
    def get_verification_statistics(self) -> Dict[str, Any]:
        """获取验证统计"""
        with self._lock:
            if not self._verification_history:
                return {'total_verifications': 0}
            
            successes = sum(1 for v in self._verification_history if v['success'])
            total = len(self._verification_history)
            
            return {
                'total_verifications': total,
                'successful': successes,
                'failed': total - successes,
                'success_rate': round(successes / total * 100, 2) if total > 0 else 0
            }


class IntelligentCleanupStrategy:
    """智能临时文件清理策略"""
    
    def __init__(self, manager: TempFileManager):
        self._manager = manager
        self._usage_patterns: Dict[str, List[Dict[str, Any]]] = {}
        self._cleanup_history: List[Dict[str, Any]] = []
        self._lock = threading.Lock()
    
    def analyze_and_cleanup(
        self,
        directory: str,
        strategy: str = 'intelligent',
        max_age_seconds: int = 3600,
        dry_run: bool = False
    ) -> Dict[str, Any]:
        """分析并清理"""
        dir_path = Path(directory)
        
        if not dir_path.exists():
            return {'error': '目录不存在', 'cleaned': [], 'skipped': []}
        
        temp_files = list(dir_path.glob('*_temp_*'))
        
        analysis = self._analyze_files(temp_files)
        
        cleanup_plan = self._create_cleanup_plan(analysis, strategy, max_age_seconds)
        
        results = self._execute_cleanup_plan(cleanup_plan, dry_run)
        
        self._record_cleanup(directory, results, strategy)
        
        return results
    
    def _analyze_files(self, files: List[Path]) -> Dict[str, Any]:
        """分析文件"""
        analysis = {
            'total_files': len(files),
            'total_size': 0,
            'by_age': {'new': 0, 'medium': 0, 'old': 0, 'very_old': 0},
            'by_size': {'small': 0, 'medium': 0, 'large': 0},
            'by_state': {},
            'recommendations': []
        }
        
        now = datetime.now()
        
        for file_path in files:
            try:
                stat = file_path.stat()
                size = stat.st_size
                age_seconds = (now - datetime.fromtimestamp(stat.st_mtime)).total_seconds()
                
                analysis['total_size'] += size
                
                if age_seconds < 3600:
                    analysis['by_age']['new'] += 1
                elif age_seconds < 21600:
                    analysis['by_age']['medium'] += 1
                elif age_seconds < 86400:
                    analysis['by_age']['old'] += 1
                else:
                    analysis['by_age']['very_old'] += 1
                
                if size < 1024:
                    analysis['by_size']['small'] += 1
                elif size < 1024 * 1024:
                    analysis['by_size']['medium'] += 1
                else:
                    analysis['by_size']['large'] += 1
                
                info = self._manager.get_temp_file_info(str(file_path))
                if info:
                    state = info.state.value
                    analysis['by_state'][state] = analysis['by_state'].get(state, 0) + 1
            
            except Exception:
                continue
        
        if analysis['by_age']['very_old'] > 10:
            analysis['recommendations'].append('建议清理超过24小时的临时文件')
        
        if analysis['by_size']['large'] > 5:
            analysis['recommendations'].append('发现多个大文件，建议检查')
        
        return analysis
    
    def _create_cleanup_plan(
        self,
        analysis: Dict[str, Any],
        strategy: str,
        max_age_seconds: int
    ) -> Dict[str, Any]:
        """创建清理计划"""
        plan = {
            'strategy': strategy,
            'files_to_clean': [],
            'files_to_keep': [],
            'estimated_freed': 0
        }
        
        if strategy == 'intelligent':
            plan['files_to_clean'] = [
                f for f in analysis.get('files', [])
                if self._should_clean_intelligent(f, max_age_seconds)
            ]
        elif strategy == 'aggressive':
            plan['files_to_clean'] = analysis.get('files', [])
        elif strategy == 'conservative':
            plan['files_to_clean'] = [
                f for f in analysis.get('files', [])
                if self._should_clean_conservative(f, max_age_seconds)
            ]
        
        return plan
    
    def _should_clean_intelligent(self, file_info: Dict, max_age: int) -> bool:
        """智能判断是否清理"""
        age = file_info.get('age_seconds', 0)
        state = file_info.get('state', 'unknown')
        
        if state == 'in_use':
            return False
        
        if age > max_age * 2:
            return True
        
        if age > max_age and state != 'ready_for_replace':
            return True
        
        return False
    
    def _should_clean_conservative(self, file_info: Dict, max_age: int) -> bool:
        """保守判断是否清理"""
        age = file_info.get('age_seconds', 0)
        state = file_info.get('state', 'unknown')
        
        if state in ['in_use', 'ready_for_replace']:
            return False
        
        return age > max_age * 2
    
    def _execute_cleanup_plan(
        self,
        plan: Dict[str, Any],
        dry_run: bool
    ) -> Dict[str, Any]:
        """执行清理计划"""
        results = {
            'cleaned': [],
            'skipped': [],
            'errors': [],
            'freed_size': 0
        }
        
        for file_path in plan['files_to_clean']:
            try:
                path = Path(file_path) if isinstance(file_path, str) else file_path
                
                if self._manager.is_file_in_use(str(path)):
                    results['skipped'].append(str(path))
                    continue
                
                if not dry_run:
                    size = path.stat().st_size
                    path.unlink()
                    results['freed_size'] += size
                
                results['cleaned'].append(str(path))
            
            except Exception as e:
                results['errors'].append(f"{file_path}: {e}")
        
        return results
    
    def _record_cleanup(self, directory: str, results: Dict[str, Any], strategy: str):
        """记录清理历史"""
        with self._lock:
            self._cleanup_history.append({
                'timestamp': datetime.now().isoformat(),
                'directory': directory,
                'strategy': strategy,
                'cleaned_count': len(results['cleaned']),
                'freed_size': results['freed_size']
            })
            
            if len(self._cleanup_history) > 100:
                self._cleanup_history = self._cleanup_history[-100:]
    
    def get_cleanup_statistics(self) -> Dict[str, Any]:
        """获取清理统计"""
        with self._lock:
            if not self._cleanup_history:
                return {'total_cleanups': 0}
            
            total_freed = sum(c['freed_size'] for c in self._cleanup_history)
            
            return {
                'total_cleanups': len(self._cleanup_history),
                'total_freed_mb': round(total_freed / (1024 * 1024), 2),
                'average_cleaned_per_run': sum(c['cleaned_count'] for c in self._cleanup_history) / len(self._cleanup_history)
            }


class EnhancedTempFileManager(TempFileManager):
    """增强临时文件管理器 - 集成所有增强功能"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        self._intelligent_detector = IntelligentProcessStateDetector(self._process_detector)
        self._enhanced_timeout = EnhancedTimeoutManager()
        self._enhanced_verifier = EnhancedAtomicVerifier()
        self._intelligent_cleanup = IntelligentCleanupStrategy(self)
    
    def detect_intelligent_state(self, script_path: str) -> Dict[str, Any]:
        """智能检测进程状态"""
        return self._intelligent_detector.detect_intelligent_state(script_path)
    
    def smart_wait_with_timeout(
        self,
        check_func: Callable[[], bool],
        timeout: float = 30.0,
        strategy: str = 'adaptive',
        callback: Optional[Callable[[float, int], None]] = None
    ) -> Dict[str, Any]:
        """智能等待"""
        return self._enhanced_timeout.smart_wait(
            check_func, timeout, strategy, callback=callback
        )
    
    def multi_stage_verify(
        self,
        source_path: str,
        target_path: str,
        stages: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """多阶段验证"""
        return self._enhanced_verifier.multi_stage_verify(
            source_path, target_path, stages
        )
    
    def intelligent_cleanup(
        self,
        directory: str,
        strategy: str = 'intelligent',
        max_age_seconds: int = 3600,
        dry_run: bool = False
    ) -> Dict[str, Any]:
        """智能清理"""
        return self._intelligent_cleanup.analyze_and_cleanup(
            directory, strategy, max_age_seconds, dry_run
        )
    
    def enhanced_safe_replace_v2(
        self,
        temp_path: str,
        original_path: str,
        verify_stages: Optional[List[str]] = None,
        wait_strategy: str = 'adaptive',
        max_wait: float = 60.0
    ) -> AtomicReplaceResult:
        """增强安全替换 V2"""
        
        state = self.detect_intelligent_state(original_path)
        
        if state['status'] == 'running':
            if not state.get('prediction', {}).get('safe_to_modify', False):
                wait_result = self.smart_wait_with_timeout(
                    lambda: not self.is_script_running(original_path),
                    timeout=max_wait,
                    strategy=wait_strategy
                )
                
                if not wait_result['success']:
                    return AtomicReplaceResult(
                        success=False,
                        message=f"等待脚本停止超时: {original_path}",
                        error="WAIT_TIMEOUT"
                    )
        
        conflicts = self.detect_file_conflicts(original_path)
        
        if conflicts.has_conflict:
            resolution = self.get_best_conflict_resolution(conflicts.conflicts)
            
            if resolution and resolution.action == ConflictResolutionAction.ABORT:
                return AtomicReplaceResult(
                    success=False,
                    message=f"检测到严重冲突: {resolution.reason}",
                    error="CONFLICT_DETECTED"
                )
        
        result = self.atomic_replace(temp_path, original_path, verify=False)
        
        if result.success and verify_stages:
            verification = self.multi_stage_verify(
                temp_path, original_path, verify_stages
            )
            
            if not verification['success']:
                return AtomicReplaceResult(
                    success=False,
                    message=f"验证失败: {verification['errors']}",
                    error="VERIFICATION_FAILED"
                )
        
        return result
    
    def get_enhanced_statistics(self) -> Dict[str, Any]:
        """获取增强统计信息"""
        base_stats = self.get_statistics()
        
        enhanced_stats = {
            'timeout_stats': self._enhanced_timeout.get_statistics(),
            'verification_stats': self._enhanced_verifier.get_verification_statistics(),
            'cleanup_stats': self._intelligent_cleanup.get_cleanup_statistics()
        }
        
        return {**base_stats, 'enhanced': enhanced_stats}


if __name__ == "__main__":
    run_cli()
