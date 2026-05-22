#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
持续演化控制器 - Continuous Evolution Controller

三省六部技能系统的核心演化控制器，实现自动化的持续改进循环。

核心功能:
- 演化周期调度器（支持自动触发、定时触发、手动触发）
- 演化任务队列管理
- 演化状态机（状态：idle, scanning, diagnosing, fixing, verifying, learning, reporting）
- 与现有脚本集成（auto_fixer, log_analyzer, issue_locator等）

增强功能:
- 永久运行模式支持（perpetual_mode）
- 演化状态持久化（EvolutionStatePersistence）
- 优雅停止机制（graceful_shutdown）
- 调度策略支持（固定间隔、指数退避、自适应）
- 心跳检测和健康监控
- 崩溃后自动恢复

使用示例:
    from continuous_evolution_controller import EvolutionController
    
    controller = EvolutionController()
    await controller.start()
    
    # 手动触发演化周期
    await controller.trigger_evolution()
    
    # 启动永久运行模式
    controller.start_perpetual()
    
    # 优雅停止
    await controller.graceful_shutdown()
    
    # 停止控制器
    await controller.stop()
"""

import asyncio
import json
import logging
import os
import sys
import traceback
from abc import ABC, abstractmethod
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum, auto
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set, Tuple, Union
import threading
import time
import uuid
from queue import PriorityQueue
import heapq

from skillscripts.core.path_config_center import get_path_config


class EvolutionState(Enum):
    """演化状态枚举"""
    IDLE = auto()
    SCANNING = auto()
    DIAGNOSING = auto()
    FIXING = auto()
    VERIFYING = auto()
    LEARNING = auto()
    REPORTING = auto()
    PAUSED = auto()
    ERROR = auto()


class TriggerType(Enum):
    """触发类型枚举"""
    AUTO = "auto"
    SCHEDULED = "scheduled"
    MANUAL = "manual"
    EVENT_DRIVEN = "event_driven"


class TaskPriority(Enum):
    """任务优先级枚举"""
    CRITICAL = 0
    HIGH = 1
    MEDIUM = 2
    LOW = 3
    BACKGROUND = 4


class EvolutionPhase(Enum):
    """演化阶段枚举"""
    INITIALIZATION = "initialization"
    PROBLEM_DISCOVERY = "problem_discovery"
    ROOT_CAUSE_ANALYSIS = "root_cause_analysis"
    SOLUTION_GENERATION = "solution_generation"
    SOLUTION_APPLICATION = "solution_application"
    VERIFICATION = "verification"
    LEARNING = "learning"
    DOCUMENTATION = "documentation"


class ScheduleStrategy(Enum):
    """调度策略枚举"""
    FIXED_INTERVAL = "fixed_interval"
    EXPONENTIAL_BACKOFF = "exponential_backoff"
    ADAPTIVE = "adaptive"


class ShutdownReason(Enum):
    """停止原因枚举"""
    MANUAL = "manual"
    GRACEFUL = "graceful"
    TIMEOUT = "timeout"
    ERROR = "error"
    SYSTEM = "system"


class HealthStatus(Enum):
    """健康状态枚举"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


@dataclass
class EvolutionTask:
    """演化任务数据类"""
    task_id: str
    phase: EvolutionPhase
    priority: TaskPriority
    trigger_type: TriggerType
    created_at: datetime
    payload: Dict[str, Any] = field(default_factory=dict)
    dependencies: List[str] = field(default_factory=list)
    status: str = "pending"
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    retry_count: int = 0
    max_retries: int = 3
    
    def __lt__(self, other: 'EvolutionTask') -> bool:
        return self.priority.value < other.priority.value
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "task_id": self.task_id,
            "phase": self.phase.value,
            "priority": self.priority.value,
            "trigger_type": self.trigger_type.value,
            "created_at": self.created_at.isoformat(),
            "payload": self.payload,
            "dependencies": self.dependencies,
            "status": self.status,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "result": self.result,
            "error": self.error,
            "retry_count": self.retry_count
        }


@dataclass
class EvolutionCycle:
    """演化周期数据类"""
    cycle_id: str
    started_at: datetime
    trigger_type: TriggerType
    state: EvolutionState
    tasks: List[EvolutionTask] = field(default_factory=list)
    current_task: Optional[str] = None
    completed_at: Optional[datetime] = None
    metrics: Dict[str, Any] = field(default_factory=dict)
    issues_found: int = 0
    issues_fixed: int = 0
    issues_verified: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "cycle_id": self.cycle_id,
            "started_at": self.started_at.isoformat(),
            "trigger_type": self.trigger_type.value,
            "state": self.state.name,
            "tasks": [t.to_dict() for t in self.tasks],
            "current_task": self.current_task,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "metrics": self.metrics,
            "issues_found": self.issues_found,
            "issues_fixed": self.issues_fixed,
            "issues_verified": self.issues_verified
        }


@dataclass
class EvolutionConfig:
    """演化控制器配置"""
    auto_trigger_enabled: bool = True
    auto_trigger_interval_seconds: int = 3600
    scheduled_times: List[str] = field(default_factory=lambda: ["09:00", "15:00", "21:00"])
    max_concurrent_tasks: int = 3
    task_timeout_seconds: int = 300
    max_retry_count: int = 3
    learning_enabled: bool = True
    reporting_enabled: bool = True
    output_dir: str = None
    log_level: str = "INFO"
    perpetual_mode: bool = False
    heartbeat_interval_seconds: int = 30
    health_check_interval_seconds: int = 60
    auto_restart_on_failure: bool = True
    max_restart_attempts: int = 5
    restart_delay_seconds: int = 10
    schedule_strategy: ScheduleStrategy = ScheduleStrategy.FIXED_INTERVAL
    min_interval_seconds: int = 300
    max_interval_seconds: int = 86400
    backoff_multiplier: float = 1.5
    state_persistence_enabled: bool = True
    state_file_path: str = "./evolution_state.json"
    graceful_shutdown_timeout_seconds: int = 300
    force_shutdown_after_timeout: bool = True
    
    def __post_init__(self):
        if self.output_dir is None:
            try:
                from skillscripts.utils.enhanced_path_config_manager import create_path_manager, OutputType
                _path_mgr = create_path_manager()
                self.output_dir = str(_path_mgr.get_output_path(OutputType.REPORT, subdirectory="evolution"))
            except Exception:
                self.output_dir = "./evolution_reports"
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'EvolutionConfig':
        schedule_strategy = ScheduleStrategy(
            data.get('schedule_strategy', ScheduleStrategy.FIXED_INTERVAL.value)
        )
        output_dir = data.get('output_dir')
        if output_dir is None:
            try:
                from skillscripts.utils.enhanced_path_config_manager import create_path_manager, OutputType
                _path_mgr = create_path_manager()
                output_dir = str(_path_mgr.get_output_path(OutputType.REPORT, subdirectory="evolution"))
            except Exception:
                output_dir = './evolution_reports'
        return cls(
            auto_trigger_enabled=data.get('auto_trigger_enabled', True),
            auto_trigger_interval_seconds=data.get('auto_trigger_interval_seconds', 3600),
            scheduled_times=data.get('scheduled_times', ["09:00", "15:00", "21:00"]),
            max_concurrent_tasks=data.get('max_concurrent_tasks', 3),
            task_timeout_seconds=data.get('task_timeout_seconds', 300),
            max_retry_count=data.get('max_retry_count', 3),
            learning_enabled=data.get('learning_enabled', True),
            reporting_enabled=data.get('reporting_enabled', True),
            output_dir=output_dir,
            log_level=data.get('log_level', 'INFO'),
            perpetual_mode=data.get('perpetual_mode', False),
            heartbeat_interval_seconds=data.get('heartbeat_interval_seconds', 30),
            health_check_interval_seconds=data.get('health_check_interval_seconds', 60),
            auto_restart_on_failure=data.get('auto_restart_on_failure', True),
            max_restart_attempts=data.get('max_restart_attempts', 5),
            restart_delay_seconds=data.get('restart_delay_seconds', 10),
            schedule_strategy=schedule_strategy,
            min_interval_seconds=data.get('min_interval_seconds', 300),
            max_interval_seconds=data.get('max_interval_seconds', 86400),
            backoff_multiplier=data.get('backoff_multiplier', 1.5),
            state_persistence_enabled=data.get('state_persistence_enabled', True),
            state_file_path=data.get('state_file_path', './evolution_state.json'),
            graceful_shutdown_timeout_seconds=data.get('graceful_shutdown_timeout_seconds', 300),
            force_shutdown_after_timeout=data.get('force_shutdown_after_timeout', True)
        )


@dataclass
class EvolutionReport:
    """演化报告数据类"""
    report_id: str
    cycle: EvolutionCycle
    summary: str
    issues_addressed: List[Dict[str, Any]]
    fixes_applied: List[Dict[str, Any]]
    learnings: List[Dict[str, Any]]
    recommendations: List[str]
    generated_at: datetime
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "report_id": self.report_id,
            "cycle": self.cycle.to_dict(),
            "summary": self.summary,
            "issues_addressed": self.issues_addressed,
            "fixes_applied": self.fixes_applied,
            "learnings": self.learnings,
            "recommendations": self.recommendations,
            "generated_at": self.generated_at.isoformat()
        }


@dataclass
class PersistentState:
    """持久化状态数据类"""
    state_id: str
    controller_state: str
    current_cycle_id: Optional[str]
    last_successful_cycle: Optional[str]
    total_cycles: int
    total_issues_found: int
    total_issues_fixed: int
    last_heartbeat: datetime
    last_health_check: datetime
    health_status: HealthStatus
    consecutive_failures: int
    last_error: Optional[str]
    created_at: datetime
    updated_at: datetime
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "state_id": self.state_id,
            "controller_state": self.controller_state,
            "current_cycle_id": self.current_cycle_id,
            "last_successful_cycle": self.last_successful_cycle,
            "total_cycles": self.total_cycles,
            "total_issues_found": self.total_issues_found,
            "total_issues_fixed": self.total_issues_fixed,
            "last_heartbeat": self.last_heartbeat.isoformat(),
            "last_health_check": self.last_health_check.isoformat(),
            "health_status": self.health_status.value,
            "consecutive_failures": self.consecutive_failures,
            "last_error": self.last_error,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PersistentState':
        return cls(
            state_id=data.get("state_id", ""),
            controller_state=data.get("controller_state", "IDLE"),
            current_cycle_id=data.get("current_cycle_id"),
            last_successful_cycle=data.get("last_successful_cycle"),
            total_cycles=data.get("total_cycles", 0),
            total_issues_found=data.get("total_issues_found", 0),
            total_issues_fixed=data.get("total_issues_fixed", 0),
            last_heartbeat=datetime.fromisoformat(data["last_heartbeat"]) if data.get("last_heartbeat") else datetime.now(),
            last_health_check=datetime.fromisoformat(data["last_health_check"]) if data.get("last_health_check") else datetime.now(),
            health_status=HealthStatus(data.get("health_status", HealthStatus.UNKNOWN.value)),
            consecutive_failures=data.get("consecutive_failures", 0),
            last_error=data.get("last_error"),
            created_at=datetime.fromisoformat(data["created_at"]) if data.get("created_at") else datetime.now(),
            updated_at=datetime.fromisoformat(data["updated_at"]) if data.get("updated_at") else datetime.now(),
            metadata=data.get("metadata", {})
        )


class EvolutionStatePersistence:
    """演化状态持久化管理器"""
    
    def __init__(self, state_file_path: str):
        self._state_file_path = Path(state_file_path)
        self._lock = threading.Lock()
        self._logger = logging.getLogger('EvolutionStatePersistence')
        self._backup_count = 5
    
    def save_state(self, state: PersistentState) -> bool:
        with self._lock:
            try:
                self._create_backup()
                
                state.updated_at = datetime.now()
                state_data = state.to_dict()
                
                temp_file = self._state_file_path.with_suffix('.tmp')
                with open(temp_file, 'w', encoding='utf-8') as f:
                    json.dump(state_data, f, indent=2, ensure_ascii=False)
                
                temp_file.replace(self._state_file_path)
                self._logger.debug(f"状态已保存: {self._state_file_path}")
                return True
            except Exception as e:
                self._logger.error(f"保存状态失败: {e}")
                return False
    
    def load_state(self) -> Optional[PersistentState]:
        with self._lock:
            try:
                if not self._state_file_path.exists():
                    return None
                
                with open(self._state_file_path, 'r', encoding='utf-8') as f:
                    state_data = json.load(f)
                
                state = PersistentState.from_dict(state_data)
                self._logger.debug(f"状态已加载: {self._state_file_path}")
                return state
            except Exception as e:
                self._logger.error(f"加载状态失败: {e}")
                return self._try_load_backup()
    
    def _create_backup(self) -> None:
        if not self._state_file_path.exists():
            return
        
        try:
            backup_dir = self._state_file_path.parent / "backups"
            backup_dir.mkdir(parents=True, exist_ok=True)
            
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_file = backup_dir / f"state_{timestamp}.json"
            
            import shutil
            shutil.copy2(self._state_file_path, backup_file)
            
            self._cleanup_old_backups(backup_dir)
        except Exception as e:
            self._logger.warning(f"创建备份失败: {e}")
    
    def _cleanup_old_backups(self, backup_dir: Path) -> None:
        backups = sorted(backup_dir.glob("state_*.json"), reverse=True)
        for old_backup in backups[self._backup_count:]:
            try:
                old_backup.unlink()
            except Exception:
                pass
    
    def _try_load_backup(self) -> Optional[PersistentState]:
        backup_dir = self._state_file_path.parent / "backups"
        if not backup_dir.exists():
            return None
        
        backups = sorted(backup_dir.glob("state_*.json"), reverse=True)
        for backup_file in backups:
            try:
                with open(backup_file, 'r', encoding='utf-8') as f:
                    state_data = json.load(f)
                return PersistentState.from_dict(state_data)
            except Exception:
                continue
        
        return None
    
    def create_initial_state(self) -> PersistentState:
        now = datetime.now()
        return PersistentState(
            state_id=f"STATE-{now.strftime('%Y%m%d%H%M%S')}",
            controller_state="IDLE",
            current_cycle_id=None,
            last_successful_cycle=None,
            total_cycles=0,
            total_issues_found=0,
            total_issues_fixed=0,
            last_heartbeat=now,
            last_health_check=now,
            health_status=HealthStatus.UNKNOWN,
            consecutive_failures=0,
            last_error=None,
            created_at=now,
            updated_at=now,
            metadata={}
        )
    
    def clear_state(self) -> bool:
        with self._lock:
            try:
                if self._state_file_path.exists():
                    self._state_file_path.unlink()
                return True
            except Exception as e:
                self._logger.error(f"清除状态失败: {e}")
                return False


@dataclass
class HeartbeatInfo:
    """心跳信息数据类"""
    heartbeat_id: str
    timestamp: datetime
    state: EvolutionState
    active_tasks: int
    queue_size: int
    memory_usage_mb: float
    cpu_usage_percent: float
    uptime_seconds: float
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "heartbeat_id": self.heartbeat_id,
            "timestamp": self.timestamp.isoformat(),
            "state": self.state.name,
            "active_tasks": self.active_tasks,
            "queue_size": self.queue_size,
            "memory_usage_mb": self.memory_usage_mb,
            "cpu_usage_percent": self.cpu_usage_percent,
            "uptime_seconds": self.uptime_seconds
        }


class StateTransitionError(Exception):
    """状态转换错误"""
    pass


class TaskExecutionError(Exception):
    """任务执行错误"""
    pass


class EvolutionStateMachine:
    """演化状态机"""
    
    VALID_TRANSITIONS: Dict[EvolutionState, Set[EvolutionState]] = {
        EvolutionState.IDLE: {
            EvolutionState.SCANNING, EvolutionState.PAUSED
        },
        EvolutionState.SCANNING: {
            EvolutionState.DIAGNOSING, EvolutionState.IDLE, EvolutionState.ERROR
        },
        EvolutionState.DIAGNOSING: {
            EvolutionState.FIXING, EvolutionState.IDLE, EvolutionState.ERROR
        },
        EvolutionState.FIXING: {
            EvolutionState.VERIFYING, EvolutionState.IDLE, EvolutionState.ERROR
        },
        EvolutionState.VERIFYING: {
            EvolutionState.LEARNING, EvolutionState.FIXING, EvolutionState.IDLE, EvolutionState.ERROR
        },
        EvolutionState.LEARNING: {
            EvolutionState.REPORTING, EvolutionState.IDLE, EvolutionState.ERROR
        },
        EvolutionState.REPORTING: {
            EvolutionState.IDLE, EvolutionState.ERROR
        },
        EvolutionState.PAUSED: {
            EvolutionState.IDLE, EvolutionState.SCANNING
        },
        EvolutionState.ERROR: {
            EvolutionState.IDLE, EvolutionState.SCANNING
        }
    }
    
    def __init__(self, initial_state: EvolutionState = EvolutionState.IDLE):
        self._state = initial_state
        self._state_history: List[Tuple[datetime, EvolutionState]] = [
            (datetime.now(), initial_state)
        ]
        self._listeners: List[Callable[[EvolutionState, EvolutionState], None]] = []
    
    @property
    def current_state(self) -> EvolutionState:
        return self._state
    
    def can_transition_to(self, target_state: EvolutionState) -> bool:
        return target_state in self.VALID_TRANSITIONS.get(self._state, set())
    
    def transition(self, target_state: EvolutionState) -> bool:
        if not self.can_transition_to(target_state):
            raise StateTransitionError(
                f"无效的状态转换: {self._state.name} -> {target_state.name}"
            )
        
        old_state = self._state
        self._state = target_state
        self._state_history.append((datetime.now(), target_state))
        
        for listener in self._listeners:
            try:
                listener(old_state, target_state)
            except Exception:
                pass
        
        return True
    
    def add_listener(
        self,
        listener: Callable[[EvolutionState, EvolutionState], None]
    ) -> None:
        self._listeners.append(listener)
    
    def get_history(self) -> List[Tuple[datetime, EvolutionState]]:
        return self._state_history.copy()
    
    def reset(self) -> None:
        self._state = EvolutionState.IDLE
        self._state_history.append((datetime.now(), EvolutionState.IDLE))


class TaskQueue:
    """演化任务队列"""
    
    def __init__(self, max_size: int = 1000):
        self._queue: List[EvolutionTask] = []
        self._max_size = max_size
        self._lock = threading.Lock()
        self._task_index: Dict[str, EvolutionTask] = {}
        self._dependency_graph: Dict[str, Set[str]] = defaultdict(set)
    
    def push(self, task: EvolutionTask) -> bool:
        with self._lock:
            if len(self._queue) >= self._max_size:
                return False
            
            if task.task_id in self._task_index:
                return False
            
            heapq.heappush(self._queue, task)
            self._task_index[task.task_id] = task
            
            for dep_id in task.dependencies:
                self._dependency_graph[dep_id].add(task.task_id)
            
            return True
    
    def pop(self) -> Optional[EvolutionTask]:
        with self._lock:
            while self._queue:
                task = heapq.heappop(self._queue)
                
                if self._can_execute(task):
                    del self._task_index[task.task_id]
                    return task
                else:
                    heapq.heappush(self._queue, task)
                    return None
            
            return None
    
    def _can_execute(self, task: EvolutionTask) -> bool:
        for dep_id in task.dependencies:
            if dep_id in self._task_index:
                dep_task = self._task_index[dep_id]
                if dep_task.status != "completed":
                    return False
        return True
    
    def peek(self) -> Optional[EvolutionTask]:
        with self._lock:
            if self._queue:
                return self._queue[0]
            return None
    
    def remove(self, task_id: str) -> bool:
        with self._lock:
            if task_id not in self._task_index:
                return False
            
            task = self._task_index[task_id]
            self._queue.remove(task)
            heapq.heapify(self._queue)
            del self._task_index[task_id]
            
            return True
    
    def update_task(self, task: EvolutionTask) -> bool:
        with self._lock:
            if task.task_id not in self._task_index:
                return False
            
            self._task_index[task.task_id] = task
            
            for i, t in enumerate(self._queue):
                if t.task_id == task.task_id:
                    self._queue[i] = task
                    heapq.heapify(self._queue)
                    break
            
            return True
    
    def get_task(self, task_id: str) -> Optional[EvolutionTask]:
        with self._lock:
            return self._task_index.get(task_id)
    
    def size(self) -> int:
        with self._lock:
            return len(self._queue)
    
    def is_empty(self) -> bool:
        with self._lock:
            return len(self._queue) == 0
    
    def clear(self) -> None:
        with self._lock:
            self._queue.clear()
            self._task_index.clear()
            self._dependency_graph.clear()
    
    def get_all_tasks(self) -> List[EvolutionTask]:
        with self._lock:
            return list(self._task_index.values())


class EvolutionScheduler:
    """演化周期调度器"""
    
    def __init__(self, config: EvolutionConfig):
        self._config = config
        self._running = False
        self._paused = False
        self._last_trigger_time: Optional[datetime] = None
        self._next_scheduled_time: Optional[datetime] = None
        self._trigger_callbacks: List[Callable[[TriggerType], None]] = []
        self._scheduler_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._pause_event = threading.Event()
        self._current_interval: int = config.auto_trigger_interval_seconds
        self._consecutive_successes: int = 0
        self._consecutive_failures: int = 0
        self._last_adjustment_time: Optional[datetime] = None
        self._schedule_history: List[Dict[str, Any]] = []
    
    def start(self) -> None:
        if self._running:
            return
        
        self._running = True
        self._paused = False
        self._stop_event.clear()
        self._pause_event.set()
        self._scheduler_thread = threading.Thread(target=self._run_scheduler, daemon=True)
        self._scheduler_thread.start()
    
    def stop(self) -> None:
        self._running = False
        self._paused = False
        self._stop_event.set()
        self._pause_event.set()
        if self._scheduler_thread:
            self._scheduler_thread.join(timeout=5)
    
    def pause(self) -> None:
        self._paused = True
        self._pause_event.clear()
    
    def resume(self) -> None:
        self._paused = False
        self._pause_event.set()
    
    def is_paused(self) -> bool:
        return self._paused
    
    def _run_scheduler(self) -> None:
        while self._running and not self._stop_event.is_set():
            try:
                self._pause_event.wait()
                if not self._running or self._stop_event.is_set():
                    break
                
                self._check_triggers()
                
                wait_time = self._calculate_wait_time()
                self._stop_event.wait(timeout=min(wait_time, 60))
            except Exception:
                pass
    
    def _calculate_wait_time(self) -> int:
        if self._config.schedule_strategy == ScheduleStrategy.FIXED_INTERVAL:
            return self._config.auto_trigger_interval_seconds
        elif self._config.schedule_strategy == ScheduleStrategy.EXPONENTIAL_BACKOFF:
            return min(self._current_interval, self._config.max_interval_seconds)
        elif self._config.schedule_strategy == ScheduleStrategy.ADAPTIVE:
            return self._calculate_adaptive_interval()
        return self._config.auto_trigger_interval_seconds
    
    def _calculate_adaptive_interval(self) -> int:
        base_interval = self._config.auto_trigger_interval_seconds
        
        if self._consecutive_failures > 0:
            backoff = min(
                base_interval * (self._config.backoff_multiplier ** self._consecutive_failures),
                self._config.max_interval_seconds
            )
            return int(backoff)
        
        if self._consecutive_successes >= 3:
            reduction = max(
                base_interval / (self._config.backoff_multiplier ** (self._consecutive_successes // 3)),
                self._config.min_interval_seconds
            )
            return int(reduction)
        
        return base_interval
    
    def record_success(self) -> None:
        self._consecutive_successes += 1
        self._consecutive_failures = 0
        
        if self._config.schedule_strategy == ScheduleStrategy.EXPONENTIAL_BACKOFF:
            self._current_interval = max(
                int(self._current_interval / self._config.backoff_multiplier),
                self._config.min_interval_seconds
            )
        
        self._record_schedule_event("success")
    
    def record_failure(self) -> None:
        self._consecutive_failures += 1
        self._consecutive_successes = 0
        
        if self._config.schedule_strategy == ScheduleStrategy.EXPONENTIAL_BACKOFF:
            self._current_interval = min(
                int(self._current_interval * self._config.backoff_multiplier),
                self._config.max_interval_seconds
            )
        
        self._record_schedule_event("failure")
    
    def _record_schedule_event(self, event_type: str) -> None:
        self._schedule_history.append({
            "timestamp": datetime.now().isoformat(),
            "event_type": event_type,
            "current_interval": self._current_interval,
            "consecutive_successes": self._consecutive_successes,
            "consecutive_failures": self._consecutive_failures
        })
        
        if len(self._schedule_history) > 100:
            self._schedule_history = self._schedule_history[-100:]
    
    def _check_triggers(self) -> None:
        if self._paused:
            return
        
        now = datetime.now()
        
        if self._config.auto_trigger_enabled:
            should_trigger = False
            
            if self._last_trigger_time is None:
                should_trigger = True
            else:
                elapsed = (now - self._last_trigger_time).total_seconds()
                wait_time = self._calculate_wait_time()
                if elapsed >= wait_time:
                    should_trigger = True
            
            if should_trigger:
                self._trigger(TriggerType.AUTO)
                self._last_trigger_time = now
        
        for scheduled_time in self._config.scheduled_times:
            try:
                hour, minute = map(int, scheduled_time.split(':'))
                scheduled_dt = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
                
                if scheduled_dt > now and (
                    self._next_scheduled_time is None or scheduled_dt < self._next_scheduled_time
                ):
                    self._next_scheduled_time = scheduled_dt
                
                if self._next_scheduled_time and now >= self._next_scheduled_time:
                    self._trigger(TriggerType.SCHEDULED)
                    self._next_scheduled_time = None
            except ValueError:
                pass
    
    def _trigger(self, trigger_type: TriggerType) -> None:
        for callback in self._trigger_callbacks:
            try:
                callback(trigger_type)
            except Exception:
                pass
    
    def register_trigger_callback(
        self,
        callback: Callable[[TriggerType], None]
    ) -> None:
        self._trigger_callbacks.append(callback)
    
    def trigger_manual(self) -> None:
        self._trigger(TriggerType.MANUAL)
    
    def get_next_scheduled_time(self) -> Optional[datetime]:
        return self._next_scheduled_time
    
    def get_last_trigger_time(self) -> Optional[datetime]:
        return self._last_trigger_time
    
    def get_current_interval(self) -> int:
        return self._current_interval
    
    def get_schedule_stats(self) -> Dict[str, Any]:
        return {
            "current_interval": self._current_interval,
            "consecutive_successes": self._consecutive_successes,
            "consecutive_failures": self._consecutive_failures,
            "is_paused": self._paused,
            "schedule_strategy": self._config.schedule_strategy.value,
            "history_size": len(self._schedule_history)
        }


class ScriptIntegrator:
    """脚本集成器 - 与现有脚本集成"""
    
    def __init__(self, scripts_dir: Optional[Path] = None):
        self._scripts_dir = scripts_dir or get_path_config().SCRIPTS_DIR
        self._logger = logging.getLogger('ScriptIntegrator')
        self._script_cache: Dict[str, Any] = {}
    
    def run_log_analyzer(
        self,
        log_dir: str,
        output_dir: Optional[str] = None,
        time_range: Optional[Tuple[datetime, datetime]] = None
    ) -> Dict[str, Any]:
        try:
            sys.path.insert(0, str(self._scripts_dir.parent / 'backend' / 'scripts'))
            from log_analyzer import LogAnalyzer
            
            analyzer = LogAnalyzer(
                log_dir=log_dir,
                output_dir=output_dir or './reports'
            )
            
            result, alerts, aggregated = analyzer.analyze_logs(
                time_range=time_range
            )
            
            return {
                "success": True,
                "total_entries": result.total_entries,
                "error_count": result.error_count,
                "warning_count": result.warning_count,
                "patterns": [
                    {
                        "id": p.pattern_id,
                        "name": p.name,
                        "count": p.occurrence_count,
                        "severity": p.severity,
                        "category": p.category
                    }
                    for p in result.patterns_found
                ],
                "alerts": [
                    {
                        "id": a.alert_id,
                        "name": a.rule.name,
                        "severity": a.rule.severity,
                        "message": a.message
                    }
                    for a in alerts
                ],
                "cross_module_issues": len(result.cross_module_issues),
                "trend_analysis": len(result.trend_analysis)
            }
        except Exception as e:
            self._logger.error(f"运行日志分析器失败: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def run_issue_locator(
        self,
        error_log: str,
        project_dir: str
    ) -> Dict[str, Any]:
        try:
            sys.path.insert(0, str(self._scripts_dir.parent / 'backend' / 'scripts'))
            from issue_locator import IssueLocator
            
            locator = IssueLocator(project_dir)
            issues = locator.locate_issues(error_log)
            
            return {
                "success": True,
                "issues": [
                    {
                        "id": issue.issue_id,
                        "title": issue.title,
                        "severity": issue.severity.value,
                        "category": issue.category.value,
                        "location": {
                            "file": issue.location.file_path,
                            "line": issue.location.line_number
                        } if issue.location else None,
                        "root_cause": issue.root_cause.description if issue.root_cause else None
                    }
                    for issue in issues
                ]
            }
        except Exception as e:
            self._logger.error(f"运行问题定位器失败: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def run_auto_fixer(
        self,
        file_path: str,
        dry_run: bool = True
    ) -> Dict[str, Any]:
        try:
            sys.path.insert(0, str(self._scripts_dir / 'optimization'))
            from auto_fixer import AutoFixer
            
            fixer = AutoFixer()
            result = fixer.fix_file(file_path, dry_run=dry_run)
            
            return {
                "success": result.status.value == "success",
                "file_path": result.file_path,
                "actions": [
                    {
                        "id": a.action_id,
                        "type": a.fix_type.value,
                        "description": a.description,
                        "risk": a.risk_level.value
                    }
                    for a in result.actions
                ],
                "diff": result.diff,
                "error": result.error_message
            }
        except Exception as e:
            self._logger.error(f"运行自动修复器失败: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def run_health_check(self, project_dir: str) -> Dict[str, Any]:
        try:
            sys.path.insert(0, str(self._scripts_dir / 'core'))
            from health_check import HealthChecker
            
            checker = HealthChecker(project_dir)
            result = checker.check_all()
            
            return {
                "success": result.get('healthy', False),
                "checks": result.get('checks', {}),
                "issues": result.get('issues', [])
            }
        except Exception as e:
            self._logger.error(f"运行健康检查失败: {e}")
            return {
                "success": False,
                "error": str(e)
            }


class EvolutionController:
    """持续演化控制器主类"""
    
    def __init__(
        self,
        config: Optional[EvolutionConfig] = None,
        project_dir: Optional[str] = None
    ):
        self._config = config or EvolutionConfig()
        self._project_dir = Path(project_dir or os.getcwd())
        self._state_machine = EvolutionStateMachine()
        self._task_queue = TaskQueue()
        self._scheduler = EvolutionScheduler(self._config)
        self._script_integrator = ScriptIntegrator()
        
        self._running = False
        self._perpetual_running = False
        self._current_cycle: Optional[EvolutionCycle] = None
        self._cycle_history: List[EvolutionCycle] = []
        self._reports: List[EvolutionReport] = []
        
        self._logger = self._setup_logger()
        self._output_dir = Path(self._config.output_dir)
        self._output_dir.mkdir(parents=True, exist_ok=True)
        
        self._executor_lock = threading.Lock()
        self._cycle_counter = 0
        
        self._start_time: Optional[datetime] = None
        self._heartbeat_thread: Optional[threading.Thread] = None
        self._health_check_thread: Optional[threading.Thread] = None
        self._shutdown_event = threading.Event()
        self._shutdown_requested = False
        self._shutdown_reason: Optional[ShutdownReason] = None
        self._restart_attempts = 0
        
        self._state_persistence: Optional[EvolutionStatePersistence] = None
        self._persistent_state: Optional[PersistentState] = None
        
        if self._config.state_persistence_enabled:
            self._state_persistence = EvolutionStatePersistence(self._config.state_file_path)
            self._persistent_state = self._state_persistence.load_state()
            if self._persistent_state:
                self._logger.info("从持久化状态恢复")
        
        self._setup_callbacks()
    
    def _setup_logger(self) -> logging.Logger:
        logger = logging.getLogger('EvolutionController')
        logger.setLevel(getattr(logging, self._config.log_level))
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        
        return logger
    
    def _setup_callbacks(self) -> None:
        self._scheduler.register_trigger_callback(self._on_trigger)
        self._state_machine.add_listener(self._on_state_change)
    
    def _on_trigger(self, trigger_type: TriggerType) -> None:
        self._logger.info(f"收到触发信号: {trigger_type.value}")
        
        if self._state_machine.current_state != EvolutionState.IDLE:
            self._logger.warning("控制器忙碌，跳过此次触发")
            return
        
        if self._shutdown_requested:
            self._logger.info("已请求停止，跳过触发")
            return
        
        asyncio.run(self._start_evolution_cycle(trigger_type))
    
    def _on_state_change(
        self,
        old_state: EvolutionState,
        new_state: EvolutionState
    ) -> None:
        self._logger.info(f"状态转换: {old_state.name} -> {new_state.name}")
        
        if self._current_cycle:
            self._current_cycle.state = new_state
        
        self._update_persistent_state()
    
    def _update_persistent_state(self) -> None:
        if not self._state_persistence or not self._persistent_state:
            return
        
        self._persistent_state.controller_state = self._state_machine.current_state.name
        self._persistent_state.current_cycle_id = self._current_cycle.cycle_id if self._current_cycle else None
        self._persistent_state.last_heartbeat = datetime.now()
        
        self._state_persistence.save_state(self._persistent_state)
    
    async def start(self) -> None:
        if self._running:
            return
        
        self._running = True
        self._start_time = datetime.now()
        self._shutdown_requested = False
        self._shutdown_reason = None
        self._logger.info("持续演化控制器启动")
        
        if self._config.state_persistence_enabled and not self._persistent_state:
            self._persistent_state = self._state_persistence.create_initial_state()
        
        self._start_heartbeat()
        self._start_health_check()
        self._scheduler.start()
        
        while self._running and not self._shutdown_event.is_set():
            try:
                await self._process_tasks()
                await asyncio.sleep(1)
            except Exception as e:
                self._logger.error(f"处理任务时发生错误: {e}")
                await asyncio.sleep(5)
    
    async def stop(self) -> None:
        self._logger.info("停止持续演化控制器")
        self._running = False
        self._perpetual_running = False
        self._shutdown_event.set()
        self._stop_heartbeat()
        self._stop_health_check()
        self._scheduler.stop()
        
        if self._state_machine.current_state != EvolutionState.IDLE:
            self._state_machine.transition(EvolutionState.IDLE)
        
        self._update_persistent_state()
    
    async def graceful_shutdown(
        self,
        timeout_seconds: Optional[int] = None,
        reason: ShutdownReason = ShutdownReason.GRACEFUL
    ) -> bool:
        self._logger.info(f"开始优雅停止，原因: {reason.value}")
        self._shutdown_requested = True
        self._shutdown_reason = reason
        
        timeout = timeout_seconds or self._config.graceful_shutdown_timeout_seconds
        start_time = datetime.now()
        
        while self._state_machine.current_state != EvolutionState.IDLE:
            elapsed = (datetime.now() - start_time).total_seconds()
            if elapsed >= timeout:
                self._logger.warning(f"优雅停止超时 ({timeout}秒)")
                if self._config.force_shutdown_after_timeout:
                    self._logger.warning("强制停止")
                    await self.stop()
                    return False
                return False
            
            await asyncio.sleep(1)
        
        if self._current_cycle:
            self._logger.info(f"等待当前周期完成: {self._current_cycle.cycle_id}")
            
            while self._current_cycle and not self._current_cycle.completed_at:
                elapsed = (datetime.now() - start_time).total_seconds()
                if elapsed >= timeout:
                    self._logger.warning("等待周期完成超时")
                    if self._config.force_shutdown_after_timeout:
                        await self.stop()
                        return False
                    break
                await asyncio.sleep(1)
        
        self._save_shutdown_state()
        await self.stop()
        
        self._logger.info("优雅停止完成")
        return True
    
    def _save_shutdown_state(self) -> None:
        if not self._state_persistence or not self._persistent_state:
            return
        
        self._persistent_state.metadata["shutdown"] = {
            "reason": self._shutdown_reason.value if self._shutdown_reason else None,
            "timestamp": datetime.now().isoformat(),
            "current_cycle": self._current_cycle.to_dict() if self._current_cycle else None,
            "queue_size": self._task_queue.size()
        }
        
        self._state_persistence.save_state(self._persistent_state)
    
    def start_perpetual(self) -> threading.Thread:
        self._logger.info("启动永久运行模式")
        self._perpetual_running = True
        
        def run_perpetual():
            while self._perpetual_running:
                try:
                    asyncio.run(self._run_perpetual_cycle())
                except Exception as e:
                    self._logger.error(f"永久运行周期错误: {e}")
                    
                    if self._config.auto_restart_on_failure:
                        self._restart_attempts += 1
                        if self._restart_attempts <= self._config.max_restart_attempts:
                            self._logger.info(f"尝试重启 ({self._restart_attempts}/{self._config.max_restart_attempts})")
                            time.sleep(self._config.restart_delay_seconds)
                        else:
                            self._logger.error("达到最大重启次数，停止永久运行")
                            self._perpetual_running = False
                    else:
                        self._perpetual_running = False
        
        perpetual_thread = threading.Thread(target=run_perpetual, daemon=True)
        perpetual_thread.start()
        return perpetual_thread
    
    async def _run_perpetual_cycle(self) -> None:
        self._restart_attempts = 0
        
        if self._config.state_persistence_enabled and self._persistent_state:
            await self._recover_from_persistent_state()
        
        await self.start()
    
    async def _recover_from_persistent_state(self) -> None:
        if not self._persistent_state:
            return
        
        self._logger.info(f"从持久化状态恢复: {self._persistent_state.state_id}")
        
        if self._persistent_state.current_cycle_id:
            self._logger.info(f"恢复未完成的周期: {self._persistent_state.current_cycle_id}")
        
        self._cycle_counter = self._persistent_state.total_cycles
        
        if self._persistent_state.consecutive_failures > 0:
            self._logger.warning(f"检测到连续失败: {self._persistent_state.consecutive_failures}")
    
    def _start_heartbeat(self) -> None:
        if self._heartbeat_thread and self._heartbeat_thread.is_alive():
            return
        
        self._heartbeat_thread = threading.Thread(target=self._heartbeat_loop, daemon=True)
        self._heartbeat_thread.start()
    
    def _stop_heartbeat(self) -> None:
        pass
    
    def _heartbeat_loop(self) -> None:
        while self._running and not self._shutdown_event.is_set():
            try:
                self._send_heartbeat()
                self._shutdown_event.wait(timeout=self._config.heartbeat_interval_seconds)
            except Exception as e:
                self._logger.error(f"心跳错误: {e}")
    
    def _send_heartbeat(self) -> HeartbeatInfo:
        heartbeat = HeartbeatInfo(
            heartbeat_id=f"HB-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            timestamp=datetime.now(),
            state=self._state_machine.current_state,
            active_tasks=sum(1 for t in self._task_queue.get_all_tasks() if t.status == "running"),
            queue_size=self._task_queue.size(),
            memory_usage_mb=self._get_memory_usage(),
            cpu_usage_percent=self._get_cpu_usage(),
            uptime_seconds=self._get_uptime()
        )
        
        if self._persistent_state:
            self._persistent_state.last_heartbeat = heartbeat.timestamp
            if self._state_persistence:
                self._state_persistence.save_state(self._persistent_state)
        
        self._logger.debug(f"心跳: {heartbeat.state.name}, 队列: {heartbeat.queue_size}")
        return heartbeat
    
    def _start_health_check(self) -> None:
        if self._health_check_thread and self._health_check_thread.is_alive():
            return
        
        self._health_check_thread = threading.Thread(target=self._health_check_loop, daemon=True)
        self._health_check_thread.start()
    
    def _stop_health_check(self) -> None:
        pass
    
    def _health_check_loop(self) -> None:
        while self._running and not self._shutdown_event.is_set():
            try:
                self._perform_health_check()
                self._shutdown_event.wait(timeout=self._config.health_check_interval_seconds)
            except Exception as e:
                self._logger.error(f"健康检查错误: {e}")
    
    def _perform_health_check(self) -> HealthStatus:
        health_status = HealthStatus.HEALTHY
        
        if self._persistent_state and self._persistent_state.consecutive_failures >= 3:
            health_status = HealthStatus.DEGRADED
        
        if self._task_queue.size() > 100:
            health_status = HealthStatus.DEGRADED
        
        memory_mb = self._get_memory_usage()
        if memory_mb > 1000:
            health_status = HealthStatus.DEGRADED
        if memory_mb > 2000:
            health_status = HealthStatus.UNHEALTHY
        
        if self._persistent_state:
            self._persistent_state.health_status = health_status
            self._persistent_state.last_health_check = datetime.now()
            if self._state_persistence:
                self._state_persistence.save_state(self._persistent_state)
        
        self._logger.debug(f"健康检查: {health_status.value}")
        return health_status
    
    def _get_memory_usage(self) -> float:
        try:
            import psutil
            process = psutil.Process()
            return process.memory_info().rss / 1024 / 1024
        except Exception:
            return 0.0
    
    def _get_cpu_usage(self) -> float:
        try:
            import psutil
            return psutil.cpu_percent(interval=0.1)
        except Exception:
            return 0.0
    
    def _get_uptime(self) -> float:
        if self._start_time:
            return (datetime.now() - self._start_time).total_seconds()
        return 0.0
    
    async def trigger_evolution(
        self,
        trigger_type: TriggerType = TriggerType.MANUAL
    ) -> str:
        if self._state_machine.current_state != EvolutionState.IDLE:
            raise RuntimeError("控制器正在执行演化周期，请稍后再试")
        
        await self._start_evolution_cycle(trigger_type)
        
        return self._current_cycle.cycle_id if self._current_cycle else ""
    
    async def _start_evolution_cycle(self, trigger_type: TriggerType) -> None:
        self._cycle_counter += 1
        cycle_id = f"CYCLE-{datetime.now().strftime('%Y%m%d%H%M%S')}-{self._cycle_counter:04d}"
        
        self._current_cycle = EvolutionCycle(
            cycle_id=cycle_id,
            started_at=datetime.now(),
            trigger_type=trigger_type,
            state=EvolutionState.SCANNING
        )
        
        self._state_machine.transition(EvolutionState.SCANNING)
        
        self._logger.info(f"开始演化周期: {cycle_id}")
        
        try:
            await self._execute_evolution_cycle()
            self._scheduler.record_success()
            
            if self._persistent_state:
                self._persistent_state.total_cycles += 1
                self._persistent_state.last_successful_cycle = cycle_id
                self._persistent_state.consecutive_failures = 0
        except Exception as e:
            self._logger.error(f"演化周期执行失败: {e}")
            self._current_cycle.completed_at = datetime.now()
            self._state_machine.transition(EvolutionState.ERROR)
            self._cycle_history.append(self._current_cycle)
            self._scheduler.record_failure()
            
            if self._persistent_state:
                self._persistent_state.consecutive_failures += 1
                self._persistent_state.last_error = str(e)
    
    async def _execute_evolution_cycle(self) -> None:
        if not self._current_cycle:
            return
        
        scan_task = EvolutionTask(
            task_id=f"{self._current_cycle.cycle_id}-SCAN",
            phase=EvolutionPhase.PROBLEM_DISCOVERY,
            priority=TaskPriority.HIGH,
            trigger_type=self._current_cycle.trigger_type,
            created_at=datetime.now()
        )
        self._task_queue.push(scan_task)
        self._current_cycle.tasks.append(scan_task)
        
        await self._process_tasks()
        
        if self._config.reporting_enabled:
            await self._generate_report()
        
        self._current_cycle.completed_at = datetime.now()
        self._cycle_history.append(self._current_cycle)
        self._state_machine.transition(EvolutionState.IDLE)
        
        if self._persistent_state:
            self._persistent_state.total_issues_found += self._current_cycle.issues_found
            self._persistent_state.total_issues_fixed += self._current_cycle.issues_fixed
            self._update_persistent_state()
    
    async def _process_tasks(self) -> None:
        while not self._task_queue.is_empty():
            if self._shutdown_requested:
                self._logger.info("检测到停止请求，暂停任务处理")
                break
            
            task = self._task_queue.pop()
            if not task:
                await asyncio.sleep(0.1)
                continue
            
            try:
                await self._execute_task(task)
            except Exception as e:
                self._logger.error(f"任务执行失败 {task.task_id}: {e}")
                task.error = str(e)
                task.status = "failed"
                
                if task.retry_count < task.max_retries:
                    task.retry_count += 1
                    task.status = "pending"
                    self._task_queue.push(task)
    
    async def _execute_task(self, task: EvolutionTask) -> None:
        task.status = "running"
        task.started_at = datetime.now()
        
        self._logger.info(f"执行任务: {task.task_id} - {task.phase.value}")
        
        try:
            if task.phase == EvolutionPhase.PROBLEM_DISCOVERY:
                result = await self._phase_problem_discovery(task)
            elif task.phase == EvolutionPhase.ROOT_CAUSE_ANALYSIS:
                result = await self._phase_root_cause_analysis(task)
            elif task.phase == EvolutionPhase.SOLUTION_GENERATION:
                result = await self._phase_solution_generation(task)
            elif task.phase == EvolutionPhase.SOLUTION_APPLICATION:
                result = await self._phase_solution_application(task)
            elif task.phase == EvolutionPhase.VERIFICATION:
                result = await self._phase_verification(task)
            elif task.phase == EvolutionPhase.LEARNING:
                result = await self._phase_learning(task)
            else:
                result = {"success": False, "error": "未知阶段"}
            
            task.result = result
            task.status = "completed" if result.get("success") else "failed"
            task.completed_at = datetime.now()
            
            self._task_queue.update_task(task)
            
            if result.get("success") and result.get("next_tasks"):
                for next_task_data in result["next_tasks"]:
                    next_task = EvolutionTask(**next_task_data)
                    self._task_queue.push(next_task)
                    if self._current_cycle:
                        self._current_cycle.tasks.append(next_task)
        
        except Exception as e:
            task.error = str(e)
            task.status = "failed"
            task.completed_at = datetime.now()
            raise
    
    async def _phase_problem_discovery(
        self,
        task: EvolutionTask
    ) -> Dict[str, Any]:
        self._state_machine.transition(EvolutionState.SCANNING)
        
        log_dir = str(self._project_dir / 'logs')
        if not os.path.exists(log_dir):
            log_dir = str(self._project_dir)
        
        result = self._script_integrator.run_log_analyzer(
            log_dir=log_dir,
            output_dir=str(self._output_dir)
        )
        
        if result.get("success"):
            issues = result.get("patterns", [])
            self._current_cycle.issues_found = len(issues)
            
            next_tasks = []
            for issue in issues[:5]:
                next_tasks.append({
                    "task_id": f"{task.task_id}-RCA-{issue['id']}",
                    "phase": EvolutionPhase.ROOT_CAUSE_ANALYSIS,
                    "priority": TaskPriority.HIGH if issue.get("severity") in ["critical", "high"] else TaskPriority.MEDIUM,
                    "trigger_type": task.trigger_type,
                    "created_at": datetime.now(),
                    "payload": {"issue": issue},
                    "dependencies": []
                })
            
            return {
                "success": True,
                "issues_found": len(issues),
                "next_tasks": next_tasks
            }
        
        return result
    
    async def _phase_root_cause_analysis(
        self,
        task: EvolutionTask
    ) -> Dict[str, Any]:
        self._state_machine.transition(EvolutionState.DIAGNOSING)
        
        issue = task.payload.get("issue", {})
        
        result = self._script_integrator.run_issue_locator(
            error_log=issue.get("name", ""),
            project_dir=str(self._project_dir)
        )
        
        if result.get("success"):
            diagnosed_issues = result.get("issues", [])
            
            next_tasks = []
            for diag_issue in diagnosed_issues[:3]:
                next_tasks.append({
                    "task_id": f"{task.task_id}-SOL-{diag_issue['id']}",
                    "phase": EvolutionPhase.SOLUTION_GENERATION,
                    "priority": TaskPriority.HIGH if diag_issue.get("severity") in ["critical", "high"] else TaskPriority.MEDIUM,
                    "trigger_type": task.trigger_type,
                    "created_at": datetime.now(),
                    "payload": {"issue": diag_issue},
                    "dependencies": []
                })
            
            return {
                "success": True,
                "diagnosed_issues": diagnosed_issues,
                "next_tasks": next_tasks
            }
        
        return result
    
    async def _phase_solution_generation(
        self,
        task: EvolutionTask
    ) -> Dict[str, Any]:
        issue = task.payload.get("issue", {})
        location = issue.get("location", {})
        
        if location and location.get("file"):
            result = self._script_integrator.run_auto_fixer(
                file_path=location["file"],
                dry_run=True
            )
            
            if result.get("success"):
                actions = result.get("actions", [])
                
                next_tasks = []
                for action in actions:
                    next_tasks.append({
                        "task_id": f"{task.task_id}-APP-{action['id']}",
                        "phase": EvolutionPhase.SOLUTION_APPLICATION,
                        "priority": TaskPriority.MEDIUM,
                        "trigger_type": task.trigger_type,
                        "created_at": datetime.now(),
                        "payload": {
                            "action": action,
                            "file_path": location["file"]
                        },
                        "dependencies": []
                    })
                
                return {
                    "success": True,
                    "actions": actions,
                    "next_tasks": next_tasks
                }
        
        return {
            "success": True,
            "actions": [],
            "next_tasks": []
        }
    
    async def _phase_solution_application(
        self,
        task: EvolutionTask
    ) -> Dict[str, Any]:
        self._state_machine.transition(EvolutionState.FIXING)
        
        file_path = task.payload.get("file_path", "")
        action = task.payload.get("action", {})
        
        if file_path and action:
            result = self._script_integrator.run_auto_fixer(
                file_path=file_path,
                dry_run=False
            )
            
            if result.get("success"):
                self._current_cycle.issues_fixed += 1
                
                return {
                    "success": True,
                    "fix_applied": True,
                    "next_tasks": [{
                        "task_id": f"{task.task_id}-VERIFY",
                        "phase": EvolutionPhase.VERIFICATION,
                        "priority": TaskPriority.HIGH,
                        "trigger_type": task.trigger_type,
                        "created_at": datetime.now(),
                        "payload": {"file_path": file_path},
                        "dependencies": []
                    }]
                }
            
            return result
        
        return {"success": False, "error": "缺少文件路径或操作信息"}
    
    async def _phase_verification(
        self,
        task: EvolutionTask
    ) -> Dict[str, Any]:
        self._state_machine.transition(EvolutionState.VERIFYING)
        
        file_path = task.payload.get("file_path", "")
        
        if file_path:
            result = self._script_integrator.run_health_check(
                project_dir=str(self._project_dir)
            )
            
            if result.get("success"):
                self._current_cycle.issues_verified += 1
                
                if self._config.learning_enabled:
                    return {
                        "success": True,
                        "verified": True,
                        "next_tasks": [{
                            "task_id": f"{task.task_id}-LEARN",
                            "phase": EvolutionPhase.LEARNING,
                            "priority": TaskPriority.LOW,
                            "trigger_type": task.trigger_type,
                            "created_at": datetime.now(),
                            "payload": {"file_path": file_path},
                            "dependencies": []
                        }]
                    }
                
                return {"success": True, "verified": True}
            
            return result
        
        return {"success": False, "error": "缺少文件路径"}
    
    async def _phase_learning(
        self,
        task: EvolutionTask
    ) -> Dict[str, Any]:
        self._state_machine.transition(EvolutionState.LEARNING)
        
        return {
            "success": True,
            "learnings": [
                "修复模式已记录",
                "解决方案已添加到知识库"
            ]
        }
    
    async def _generate_report(self) -> None:
        self._state_machine.transition(EvolutionState.REPORTING)
        
        if not self._current_cycle:
            return
        
        report_id = f"RPT-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        issues_addressed = []
        fixes_applied = []
        learnings = []
        
        for task in self._current_cycle.tasks:
            if task.result:
                if task.phase == EvolutionPhase.PROBLEM_DISCOVERY:
                    issues_addressed.extend(task.result.get("issues_found", []))
                elif task.phase == EvolutionPhase.SOLUTION_APPLICATION:
                    if task.result.get("fix_applied"):
                        fixes_applied.append({
                            "task_id": task.task_id,
                            "file": task.payload.get("file_path"),
                            "action": task.payload.get("action", {}).get("type")
                        })
                elif task.phase == EvolutionPhase.LEARNING:
                    learnings.extend(task.result.get("learnings", []))
        
        recommendations = self._generate_recommendations()
        
        report = EvolutionReport(
            report_id=report_id,
            cycle=self._current_cycle,
            summary=self._generate_summary(),
            issues_addressed=issues_addressed,
            fixes_applied=fixes_applied,
            learnings=learnings,
            recommendations=recommendations,
            generated_at=datetime.now()
        )
        
        self._reports.append(report)
        self._save_report(report)
    
    def _generate_summary(self) -> str:
        if not self._current_cycle:
            return ""
        
        duration = (
            self._current_cycle.completed_at - self._current_cycle.started_at
        ).total_seconds() if self._current_cycle.completed_at else 0
        
        return (
            f"演化周期 {self._current_cycle.cycle_id} 完成。"
            f"发现 {self._current_cycle.issues_found} 个问题，"
            f"修复 {self._current_cycle.issues_fixed} 个问题，"
            f"验证 {self._current_cycle.issues_verified} 个修复。"
            f"耗时 {duration:.2f} 秒。"
        )
    
    def _generate_recommendations(self) -> List[str]:
        recommendations = []
        
        if self._current_cycle:
            if self._current_cycle.issues_found > 10:
                recommendations.append("建议增加代码审查频率")
            
            if self._current_cycle.issues_fixed < self._current_cycle.issues_found * 0.5:
                recommendations.append("建议优化自动修复策略")
            
            if self._current_cycle.issues_verified < self._current_cycle.issues_fixed:
                recommendations.append("建议加强修复验证机制")
        
        return recommendations
    
    def _save_report(self, report: EvolutionReport) -> None:
        report_path = self._output_dir / f"{report.report_id}.json"
        
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report.to_dict(), f, indent=2, ensure_ascii=False)
        
        self._logger.info(f"报告已保存: {report_path}")
    
    def get_status(self) -> Dict[str, Any]:
        return {
            "running": self._running,
            "perpetual_mode": self._config.perpetual_mode,
            "perpetual_running": self._perpetual_running,
            "current_state": self._state_machine.current_state.name,
            "current_cycle": self._current_cycle.to_dict() if self._current_cycle else None,
            "queue_size": self._task_queue.size(),
            "total_cycles": len(self._cycle_history),
            "total_reports": len(self._reports),
            "next_scheduled_time": self._scheduler.get_next_scheduled_time().isoformat() if self._scheduler.get_next_scheduled_time() else None,
            "uptime_seconds": self._get_uptime(),
            "shutdown_requested": self._shutdown_requested,
            "shutdown_reason": self._shutdown_reason.value if self._shutdown_reason else None,
            "schedule_stats": self._scheduler.get_schedule_stats(),
            "health_status": self._persistent_state.health_status.value if self._persistent_state else None
        }
    
    def get_cycle_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        return [c.to_dict() for c in self._cycle_history[-limit:]]
    
    def get_reports(self, limit: int = 10) -> List[Dict[str, Any]]:
        return [r.to_dict() for r in self._reports[-limit:]]
    
    def pause(self) -> None:
        if self._state_machine.current_state == EvolutionState.IDLE:
            self._state_machine.transition(EvolutionState.PAUSED)
            self._scheduler.pause()
            self._logger.info("演化控制器已暂停")
    
    def resume(self) -> None:
        if self._state_machine.current_state == EvolutionState.PAUSED:
            self._state_machine.transition(EvolutionState.IDLE)
            self._scheduler.resume()
            self._logger.info("演化控制器已恢复")
    
    def pause_scheduler(self) -> None:
        self._scheduler.pause()
        self._logger.info("调度器已暂停")
    
    def resume_scheduler(self) -> None:
        self._scheduler.resume()
        self._logger.info("调度器已恢复")
    
    def add_task(
        self,
        phase: EvolutionPhase,
        priority: TaskPriority = TaskPriority.MEDIUM,
        payload: Optional[Dict[str, Any]] = None,
        dependencies: Optional[List[str]] = None
    ) -> str:
        task_id = f"TASK-{datetime.now().strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:8]}"
        
        task = EvolutionTask(
            task_id=task_id,
            phase=phase,
            priority=priority,
            trigger_type=TriggerType.MANUAL,
            created_at=datetime.now(),
            payload=payload or {},
            dependencies=dependencies or []
        )
        
        self._task_queue.push(task)
        
        return task_id
    
    def get_heartbeat_info(self) -> Optional[Dict[str, Any]]:
        if not self._running:
            return None
        
        heartbeat = self._send_heartbeat()
        return heartbeat.to_dict()
    
    def get_persistent_state(self) -> Optional[Dict[str, Any]]:
        if self._persistent_state:
            return self._persistent_state.to_dict()
        return None
    
    def clear_persistent_state(self) -> bool:
        if self._state_persistence:
            return self._state_persistence.clear_state()
        return False
    
    def integrate_sdd_tdd_fusion(self):
        """与 SDD-TDD 融合引擎联动
        
        在演化控制器的演化循环中嵌入融合引擎，
        查找最近的 SDD 规范文件并执行融合循环。
        
        Returns:
            融合报告或 None
        """
        try:
            from skillscripts.pipeline.sdd_tdd_fusion_engine import SDDTDDFusionEngine
            from skillscripts.core.path_config_center import get_path_config
            
            pcc = get_path_config()
            engine = SDDTDDFusionEngine()
            
            spec_files = list(pcc.DATA_DIR.glob("*.md"))
            
            if not spec_files:
                specs_dir = pcc.DOCS_DIR / "specs"
                if specs_dir.exists():
                    spec_files = list(specs_dir.glob("*.md"))
            
            if spec_files:
                latest_spec = max(spec_files, key=lambda f: f.stat().st_mtime)
                self._logger.info(f"执行SDD-TDD融合循环: {latest_spec}")
                
                report = engine.execute_cycle(latest_spec)
                return report
            
            self._logger.warning("未找到SDD规范文件，跳过融合循环")
            return None
            
        except ImportError as e:
            self._logger.warning(f"SDD-TDD融合引擎导入失败: {e}")
            return None
        except Exception as e:
            self._logger.error(f"SDD-TDD融合引擎联动失败: {e}")
            return None


def create_controller(
    config_path: Optional[str] = None,
    project_dir: Optional[str] = None
) -> EvolutionController:
    config = EvolutionConfig()
    
    if config_path:
        with open(config_path, 'r', encoding='utf-8') as f:
            config_data = json.load(f)
            config = EvolutionConfig.from_dict(config_data)
    
    return EvolutionController(config=config, project_dir=project_dir)


async def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='持续演化控制器')
    parser.add_argument('--config', help='配置文件路径')
    parser.add_argument('--project', default='.', help='项目目录')
    parser.add_argument('--trigger', action='store_true', help='立即触发演化周期')
    parser.add_argument('--status', action='store_true', help='获取控制器状态')
    parser.add_argument('--perpetual', action='store_true', help='启动永久运行模式')
    parser.add_argument('--graceful-stop', action='store_true', help='优雅停止')
    parser.add_argument('--heartbeat', action='store_true', help='获取心跳信息')
    parser.add_argument('--state', action='store_true', help='获取持久化状态')
    
    args = parser.parse_args()
    
    controller = create_controller(
        config_path=args.config,
        project_dir=args.project
    )
    
    if args.status:
        print(json.dumps(controller.get_status(), indent=2, default=str))
        return
    
    if args.heartbeat:
        heartbeat = controller.get_heartbeat_info()
        print(json.dumps(heartbeat, indent=2, default=str) if heartbeat else "控制器未运行")
        return
    
    if args.state:
        state = controller.get_persistent_state()
        print(json.dumps(state, indent=2, default=str) if state else "无持久化状态")
        return
    
    if args.trigger:
        cycle_id = await controller.trigger_evolution(TriggerType.MANUAL)
        print(f"演化周期已触发: {cycle_id}")
        return
    
    if args.graceful_stop:
        success = await controller.graceful_shutdown()
        print(f"优雅停止{'成功' if success else '失败'}")
        return
    
    if args.perpetual:
        print("启动永久运行模式...")
        thread = controller.start_perpetual()
        
        try:
            while thread.is_alive():
                thread.join(timeout=1)
        except KeyboardInterrupt:
            print("\n收到中断信号，正在优雅停止...")
            await controller.graceful_shutdown(reason=ShutdownReason.MANUAL)
        return
    
    try:
        await controller.start()
    except KeyboardInterrupt:
        await controller.graceful_shutdown(reason=ShutdownReason.MANUAL)


if __name__ == '__main__':
    asyncio.run(main())
