#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
技能演化管理器 - Skill Evolution Manager

整合技能内容变化检测、演化触发机制、知识积累和回滚机制。

核心功能:
- 基于内容变化自动触发演化
- 支持定时触发演化
- 支持手动触发演化
- 触发条件可配置
- 记录演化前状态
- 支持单步回滚
- 支持多步回滚
- 回滚验证

使用示例:
    from skill_evolution_manager import SkillEvolutionManager
    
    manager = SkillEvolutionManager(skill_dir='./')
    
    # 启动自动演化
    manager.start_auto_evolution()
    
    # 手动触发演化
    result = await manager.trigger_evolution()
    
    # 回滚演化
    success = await manager.rollback(steps=1)
"""

import asyncio
import json
import logging
import os
import shutil
import threading
import time
import traceback
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum, auto
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set, Tuple, Union

from skill_content_change_detector import (
    ChangeDetectionResult,
    ChangeType,
    FileType,
    SkillContentChangeDetector
)
from skill_evolution_knowledge import (
    BestPractice,
    EvolutionEvent,
    EvolutionPattern,
    EvolutionStatus,
    EvolutionType,
    SkillEvolutionKnowledge
)


class TriggerType(Enum):
    """触发类型枚举"""
    AUTO = "auto"
    SCHEDULED = "scheduled"
    MANUAL = "manual"
    CONTENT_CHANGE = "content_change"
    EVENT_DRIVEN = "event_driven"


class RollbackType(Enum):
    """回滚类型枚举"""
    SINGLE_STEP = "single_step"
    MULTI_STEP = "multi_step"
    FULL = "full"
    SELECTIVE = "selective"


class EvolutionPriority(Enum):
    """演化优先级枚举"""
    CRITICAL = 0
    HIGH = 1
    MEDIUM = 2
    LOW = 3
    BACKGROUND = 4


class ManagerState(Enum):
    """管理器状态枚举"""
    IDLE = "idle"
    MONITORING = "monitoring"
    EVOLVING = "evolving"
    ROLLING_BACK = "rolling_back"
    PAUSED = "paused"
    ERROR = "error"


@dataclass
class EvolutionSnapshot:
    """演化快照数据类"""
    snapshot_id: str
    created_at: datetime
    trigger_type: TriggerType
    files_backup: Dict[str, str] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    evolution_event_id: Optional[str] = None
    verified: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "snapshot_id": self.snapshot_id,
            "created_at": self.created_at.isoformat(),
            "trigger_type": self.trigger_type.value,
            "files_backup": self.files_backup,
            "metadata": self.metadata,
            "evolution_event_id": self.evolution_event_id,
            "verified": self.verified
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'EvolutionSnapshot':
        return cls(
            snapshot_id=data["snapshot_id"],
            created_at=datetime.fromisoformat(data["created_at"]),
            trigger_type=TriggerType(data["trigger_type"]),
            files_backup=data.get("files_backup", {}),
            metadata=data.get("metadata", {}),
            evolution_event_id=data.get("evolution_event_id"),
            verified=data.get("verified", False)
        )


@dataclass
class RollbackResult:
    """回滚结果数据类"""
    rollback_id: str
    success: bool
    rollback_type: RollbackType
    steps_rolled_back: int
    files_restored: List[str] = field(default_factory=list)
    files_failed: List[str] = field(default_factory=list)
    started_at: datetime = field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    verification_passed: Optional[bool] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "rollback_id": self.rollback_id,
            "success": self.success,
            "rollback_type": self.rollback_type.value,
            "steps_rolled_back": self.steps_rolled_back,
            "files_restored": self.files_restored,
            "files_failed": self.files_failed,
            "started_at": self.started_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "error_message": self.error_message,
            "verification_passed": self.verification_passed
        }


@dataclass
class TriggerCondition:
    """触发条件数据类"""
    condition_id: str
    name: str
    description: str
    trigger_type: TriggerType
    enabled: bool = True
    priority: EvolutionPriority = EvolutionPriority.MEDIUM
    config: Dict[str, Any] = field(default_factory=dict)
    last_triggered: Optional[datetime] = None
    trigger_count: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "condition_id": self.condition_id,
            "name": self.name,
            "description": self.description,
            "trigger_type": self.trigger_type.value,
            "enabled": self.enabled,
            "priority": self.priority.value,
            "config": self.config,
            "last_triggered": self.last_triggered.isoformat() if self.last_triggered else None,
            "trigger_count": self.trigger_count
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TriggerCondition':
        return cls(
            condition_id=data["condition_id"],
            name=data["name"],
            description=data["description"],
            trigger_type=TriggerType(data["trigger_type"]),
            enabled=data.get("enabled", True),
            priority=EvolutionPriority(data.get("priority", 2)),
            config=data.get("config", {}),
            last_triggered=datetime.fromisoformat(data["last_triggered"]) if data.get("last_triggered") else None,
            trigger_count=data.get("trigger_count", 0)
        )


@dataclass
class EvolutionConfig:
    """演化配置数据类"""
    auto_trigger_enabled: bool = True
    auto_trigger_interval_seconds: int = 3600
    scheduled_times: List[str] = field(default_factory=lambda: ["09:00", "15:00", "21:00"])
    content_change_trigger_enabled: bool = True
    content_change_check_interval_seconds: int = 60
    max_snapshots: int = 20
    auto_rollback_on_failure: bool = True
    verify_after_rollback: bool = True
    max_concurrent_evolutions: int = 1
    evolution_timeout_seconds: int = 300
    snapshot_dir: str = ".evolution/snapshots"
    log_level: str = "INFO"
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'EvolutionConfig':
        return cls(
            auto_trigger_enabled=data.get('auto_trigger_enabled', True),
            auto_trigger_interval_seconds=data.get('auto_trigger_interval_seconds', 3600),
            scheduled_times=data.get('scheduled_times', ["09:00", "15:00", "21:00"]),
            content_change_trigger_enabled=data.get('content_change_trigger_enabled', True),
            content_change_check_interval_seconds=data.get('content_change_check_interval_seconds', 60),
            max_snapshots=data.get('max_snapshots', 20),
            auto_rollback_on_failure=data.get('auto_rollback_on_failure', True),
            verify_after_rollback=data.get('verify_after_rollback', True),
            max_concurrent_evolutions=data.get('max_concurrent_evolutions', 1),
            evolution_timeout_seconds=data.get('evolution_timeout_seconds', 300),
            snapshot_dir=data.get('snapshot_dir', '.evolution/snapshots'),
            log_level=data.get('log_level', 'INFO')
        )


class SnapshotManager:
    """快照管理器"""
    
    def __init__(self, snapshot_dir: Path, max_snapshots: int = 20):
        self._snapshot_dir = snapshot_dir
        self._snapshot_dir.mkdir(parents=True, exist_ok=True)
        self._max_snapshots = max_snapshots
        self._lock = threading.Lock()
        self._logger = logging.getLogger('SnapshotManager')
        
        self._snapshots: Dict[str, EvolutionSnapshot] = {}
        self._snapshot_stack: List[str] = []
        self._load_snapshots()
    
    def _load_snapshots(self) -> None:
        """加载快照"""
        for snapshot_file in self._snapshot_dir.glob("snapshot_*.json"):
            try:
                with open(snapshot_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                snapshot = EvolutionSnapshot.from_dict(data)
                self._snapshots[snapshot.snapshot_id] = snapshot
                self._snapshot_stack.append(snapshot.snapshot_id)
            except Exception as e:
                self._logger.error(f"加载快照失败 {snapshot_file}: {e}")
        
        self._snapshot_stack.sort(key=lambda sid: self._snapshots[sid].created_at)
        self._logger.info(f"已加载 {len(self._snapshots)} 个快照")
    
    def create_snapshot(
        self,
        files: List[str],
        trigger_type: TriggerType,
        metadata: Optional[Dict[str, Any]] = None
    ) -> EvolutionSnapshot:
        """创建快照"""
        snapshot_id = f"SNAP-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        files_backup: Dict[str, str] = {}
        for file_path in files:
            path = Path(file_path)
            if path.exists():
                try:
                    backup_path = self._snapshot_dir / f"{snapshot_id}_{path.name}"
                    shutil.copy2(path, backup_path)
                    files_backup[str(path)] = str(backup_path)
                except Exception as e:
                    self._logger.error(f"备份文件失败 {file_path}: {e}")
        
        snapshot = EvolutionSnapshot(
            snapshot_id=snapshot_id,
            created_at=datetime.now(),
            trigger_type=trigger_type,
            files_backup=files_backup,
            metadata=metadata or {}
        )
        
        with self._lock:
            self._snapshots[snapshot_id] = snapshot
            self._snapshot_stack.append(snapshot_id)
            self._cleanup_old_snapshots()
        
        self._save_snapshot(snapshot)
        
        self._logger.info(f"已创建快照: {snapshot_id}, 包含 {len(files_backup)} 个文件")
        return snapshot
    
    def _save_snapshot(self, snapshot: EvolutionSnapshot) -> None:
        """保存快照"""
        snapshot_file = self._snapshot_dir / f"snapshot_{snapshot.snapshot_id}.json"
        
        try:
            with open(snapshot_file, 'w', encoding='utf-8') as f:
                json.dump(snapshot.to_dict(), f, indent=2, ensure_ascii=False)
        except Exception as e:
            self._logger.error(f"保存快照失败: {e}")
    
    def _cleanup_old_snapshots(self) -> None:
        """清理旧快照"""
        while len(self._snapshot_stack) > self._max_snapshots:
            old_id = self._snapshot_stack.pop(0)
            old_snapshot = self._snapshots.pop(old_id, None)
            
            if old_snapshot:
                for backup_path in old_snapshot.files_backup.values():
                    try:
                        Path(backup_path).unlink(missing_ok=True)
                    except Exception:
                        pass
                
                snapshot_file = self._snapshot_dir / f"snapshot_{old_id}.json"
                try:
                    snapshot_file.unlink(missing_ok=True)
                except Exception:
                    pass
    
    def get_snapshot(self, snapshot_id: str) -> Optional[EvolutionSnapshot]:
        """获取快照"""
        return self._snapshots.get(snapshot_id)
    
    def get_latest_snapshot(self) -> Optional[EvolutionSnapshot]:
        """获取最新快照"""
        if not self._snapshot_stack:
            return None
        return self._snapshots.get(self._snapshot_stack[-1])
    
    def get_snapshots(self, limit: int = 10) -> List[EvolutionSnapshot]:
        """获取快照列表"""
        with self._lock:
            snapshot_ids = self._snapshot_stack[-limit:]
            return [self._snapshots[sid] for sid in reversed(snapshot_ids) if sid in self._snapshots]
    
    def restore_snapshot(self, snapshot_id: str) -> Tuple[List[str], List[str]]:
        """恢复快照
        
        Returns:
            (成功恢复的文件列表, 失败的文件列表)
        """
        snapshot = self._snapshots.get(snapshot_id)
        if not snapshot:
            return [], []
        
        restored: List[str] = []
        failed: List[str] = []
        
        for original_path, backup_path in snapshot.files_backup.items():
            try:
                if Path(backup_path).exists():
                    shutil.copy2(backup_path, original_path)
                    restored.append(original_path)
                else:
                    failed.append(original_path)
            except Exception as e:
                self._logger.error(f"恢复文件失败 {original_path}: {e}")
                failed.append(original_path)
        
        return restored, failed
    
    def delete_snapshot(self, snapshot_id: str) -> bool:
        """删除快照"""
        with self._lock:
            snapshot = self._snapshots.pop(snapshot_id, None)
            if not snapshot:
                return False
            
            if snapshot_id in self._snapshot_stack:
                self._snapshot_stack.remove(snapshot_id)
            
            for backup_path in snapshot.files_backup.values():
                try:
                    Path(backup_path).unlink(missing_ok=True)
                except Exception:
                    pass
            
            snapshot_file = self._snapshot_dir / f"snapshot_{snapshot_id}.json"
            try:
                snapshot_file.unlink(missing_ok=True)
            except Exception:
                pass
            
            return True


class TriggerManager:
    """触发管理器"""
    
    def __init__(self, config: EvolutionConfig):
        self._config = config
        self._conditions: Dict[str, TriggerCondition] = {}
        self._lock = threading.Lock()
        self._logger = logging.getLogger('TriggerManager')
        
        self._init_default_conditions()
    
    def _init_default_conditions(self) -> None:
        """初始化默认触发条件"""
        self._conditions["auto_interval"] = TriggerCondition(
            condition_id="auto_interval",
            name="自动间隔触发",
            description="按固定时间间隔自动触发演化",
            trigger_type=TriggerType.AUTO,
            enabled=self._config.auto_trigger_enabled,
            priority=EvolutionPriority.LOW,
            config={"interval_seconds": self._config.auto_trigger_interval_seconds}
        )
        
        self._conditions["scheduled"] = TriggerCondition(
            condition_id="scheduled",
            name="定时触发",
            description="在指定时间点触发演化",
            trigger_type=TriggerType.SCHEDULED,
            enabled=True,
            priority=EvolutionPriority.MEDIUM,
            config={"times": self._config.scheduled_times}
        )
        
        self._conditions["content_change"] = TriggerCondition(
            condition_id="content_change",
            name="内容变化触发",
            description="检测到文件内容变化时触发演化",
            trigger_type=TriggerType.CONTENT_CHANGE,
            enabled=self._config.content_change_trigger_enabled,
            priority=EvolutionPriority.HIGH,
            config={"check_interval_seconds": self._config.content_change_check_interval_seconds}
        )
    
    def add_condition(self, condition: TriggerCondition) -> None:
        """添加触发条件"""
        with self._lock:
            self._conditions[condition.condition_id] = condition
    
    def remove_condition(self, condition_id: str) -> bool:
        """移除触发条件"""
        with self._lock:
            if condition_id in self._conditions:
                del self._conditions[condition_id]
                return True
            return False
    
    def get_condition(self, condition_id: str) -> Optional[TriggerCondition]:
        """获取触发条件"""
        return self._conditions.get(condition_id)
    
    def get_all_conditions(self) -> List[TriggerCondition]:
        """获取所有触发条件"""
        return list(self._conditions.values())
    
    def get_enabled_conditions(self) -> List[TriggerCondition]:
        """获取启用的触发条件"""
        return [c for c in self._conditions.values() if c.enabled]
    
    def enable_condition(self, condition_id: str) -> bool:
        """启用触发条件"""
        condition = self._conditions.get(condition_id)
        if condition:
            condition.enabled = True
            return True
        return False
    
    def disable_condition(self, condition_id: str) -> bool:
        """禁用触发条件"""
        condition = self._conditions.get(condition_id)
        if condition:
            condition.enabled = False
            return True
        return False
    
    def record_trigger(self, condition_id: str) -> None:
        """记录触发"""
        condition = self._conditions.get(condition_id)
        if condition:
            condition.last_triggered = datetime.now()
            condition.trigger_count += 1


class RollbackManager:
    """回滚管理器"""
    
    def __init__(
        self,
        snapshot_manager: SnapshotManager,
        verify_after_rollback: bool = True
    ):
        self._snapshot_manager = snapshot_manager
        self._verify_after_rollback = verify_after_rollback
        self._lock = threading.Lock()
        self._logger = logging.getLogger('RollbackManager')
        
        self._rollback_history: List[RollbackResult] = []
    
    async def rollback_single_step(self) -> RollbackResult:
        """单步回滚"""
        rollback_id = f"ROLLBACK-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        self._logger.info(f"开始单步回滚: {rollback_id}")
        
        result = RollbackResult(
            rollback_id=rollback_id,
            success=False,
            rollback_type=RollbackType.SINGLE_STEP,
            steps_rolled_back=0
        )
        
        try:
            snapshot = self._snapshot_manager.get_latest_snapshot()
            if not snapshot:
                result.error_message = "没有可用的快照"
                result.completed_at = datetime.now()
                self._add_to_history(result)
                return result
            
            restored, failed = self._snapshot_manager.restore_snapshot(snapshot.snapshot_id)
            
            result.files_restored = restored
            result.files_failed = failed
            result.steps_rolled_back = 1
            result.success = len(failed) == 0
            
            if self._verify_after_rollback:
                result.verification_passed = await self._verify_rollback(restored)
                if not result.verification_passed:
                    result.success = False
                    result.error_message = "回滚验证失败"
            
            if result.success:
                self._snapshot_manager.delete_snapshot(snapshot.snapshot_id)
            
            result.completed_at = datetime.now()
            
        except Exception as e:
            result.error_message = str(e)
            result.completed_at = datetime.now()
            self._logger.error(f"单步回滚失败: {e}")
        
        self._add_to_history(result)
        return result
    
    async def rollback_multi_step(self, steps: int) -> RollbackResult:
        """多步回滚"""
        rollback_id = f"ROLLBACK-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        self._logger.info(f"开始多步回滚: {rollback_id}, 步数: {steps}")
        
        result = RollbackResult(
            rollback_id=rollback_id,
            success=False,
            rollback_type=RollbackType.MULTI_STEP,
            steps_rolled_back=0
        )
        
        try:
            snapshots = self._snapshot_manager.get_snapshots(steps)
            
            if not snapshots:
                result.error_message = f"没有足够的快照（需要 {steps} 个）"
                result.completed_at = datetime.now()
                self._add_to_history(result)
                return result
            
            all_restored: List[str] = []
            all_failed: List[str] = []
            
            for snapshot in reversed(snapshots):
                restored, failed = self._snapshot_manager.restore_snapshot(snapshot.snapshot_id)
                all_restored.extend(restored)
                all_failed.extend(failed)
                result.steps_rolled_back += 1
            
            result.files_restored = list(set(all_restored))
            result.files_failed = list(set(all_failed))
            result.success = len(all_failed) == 0
            
            if self._verify_after_rollback:
                result.verification_passed = await self._verify_rollback(result.files_restored)
                if not result.verification_passed:
                    result.success = False
                    result.error_message = "回滚验证失败"
            
            if result.success:
                for snapshot in snapshots:
                    self._snapshot_manager.delete_snapshot(snapshot.snapshot_id)
            
            result.completed_at = datetime.now()
            
        except Exception as e:
            result.error_message = str(e)
            result.completed_at = datetime.now()
            self._logger.error(f"多步回滚失败: {e}")
        
        self._add_to_history(result)
        return result
    
    async def rollback_full(self) -> RollbackResult:
        """完全回滚"""
        rollback_id = f"ROLLBACK-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        self._logger.info(f"开始完全回滚: {rollback_id}")
        
        result = RollbackResult(
            rollback_id=rollback_id,
            success=False,
            rollback_type=RollbackType.FULL,
            steps_rolled_back=0
        )
        
        try:
            snapshots = self._snapshot_manager.get_snapshots(100)
            
            if not snapshots:
                result.error_message = "没有可用的快照"
                result.completed_at = datetime.now()
                self._add_to_history(result)
                return result
            
            oldest_snapshot = snapshots[-1]
            
            restored, failed = self._snapshot_manager.restore_snapshot(oldest_snapshot.snapshot_id)
            
            result.files_restored = restored
            result.files_failed = failed
            result.steps_rolled_back = len(snapshots)
            result.success = len(failed) == 0
            
            if self._verify_after_rollback:
                result.verification_passed = await self._verify_rollback(restored)
                if not result.verification_passed:
                    result.success = False
                    result.error_message = "回滚验证失败"
            
            if result.success:
                for snapshot in snapshots:
                    self._snapshot_manager.delete_snapshot(snapshot.snapshot_id)
            
            result.completed_at = datetime.now()
            
        except Exception as e:
            result.error_message = str(e)
            result.completed_at = datetime.now()
            self._logger.error(f"完全回滚失败: {e}")
        
        self._add_to_history(result)
        return result
    
    async def rollback_to_snapshot(self, snapshot_id: str) -> RollbackResult:
        """回滚到指定快照"""
        rollback_id = f"ROLLBACK-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        self._logger.info(f"开始回滚到快照: {snapshot_id}")
        
        result = RollbackResult(
            rollback_id=rollback_id,
            success=False,
            rollback_type=RollbackType.SELECTIVE,
            steps_rolled_back=0
        )
        
        try:
            snapshot = self._snapshot_manager.get_snapshot(snapshot_id)
            if not snapshot:
                result.error_message = f"快照不存在: {snapshot_id}"
                result.completed_at = datetime.now()
                self._add_to_history(result)
                return result
            
            restored, failed = self._snapshot_manager.restore_snapshot(snapshot_id)
            
            result.files_restored = restored
            result.files_failed = failed
            result.steps_rolled_back = 1
            result.success = len(failed) == 0
            
            if self._verify_after_rollback:
                result.verification_passed = await self._verify_rollback(restored)
                if not result.verification_passed:
                    result.success = False
                    result.error_message = "回滚验证失败"
            
            result.completed_at = datetime.now()
            
        except Exception as e:
            result.error_message = str(e)
            result.completed_at = datetime.now()
            self._logger.error(f"回滚到快照失败: {e}")
        
        self._add_to_history(result)
        return result
    
    async def _verify_rollback(self, files: List[str]) -> bool:
        """验证回滚"""
        for file_path in files:
            path = Path(file_path)
            if not path.exists():
                self._logger.warning(f"验证失败: 文件不存在 {file_path}")
                return False
            
            if file_path.endswith('.py'):
                try:
                    with open(path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    compile(content, file_path, 'exec')
                except SyntaxError as e:
                    self._logger.warning(f"验证失败: 语法错误 {file_path}: {e}")
                    return False
        
        return True
    
    def _add_to_history(self, result: RollbackResult) -> None:
        """添加到历史"""
        with self._lock:
            self._rollback_history.append(result)
            if len(self._rollback_history) > 100:
                self._rollback_history = self._rollback_history[-100:]
    
    def get_rollback_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """获取回滚历史"""
        with self._lock:
            return [r.to_dict() for r in self._rollback_history[-limit:]]


class SkillEvolutionManager:
    """技能演化管理器"""
    
    def __init__(
        self,
        skill_dir: str,
        config: Optional[EvolutionConfig] = None
    ):
        self._skill_dir = Path(skill_dir)
        self._config = config or EvolutionConfig()
        self._logger = self._setup_logger()
        
        self._state = ManagerState.IDLE
        self._state_lock = threading.Lock()
        
        evolution_dir = self._skill_dir / ".evolution"
        evolution_dir.mkdir(parents=True, exist_ok=True)
        
        self._change_detector = SkillContentChangeDetector(
            str(self._skill_dir),
            str(evolution_dir / "cache")
        )
        
        self._knowledge = SkillEvolutionKnowledge(
            str(self._skill_dir),
            str(evolution_dir / "knowledge")
        )
        
        self._snapshot_manager = SnapshotManager(
            evolution_dir / "snapshots",
            self._config.max_snapshots
        )
        
        self._trigger_manager = TriggerManager(self._config)
        
        self._rollback_manager = RollbackManager(
            self._snapshot_manager,
            self._config.verify_after_rollback
        )
        
        self._running = False
        self._monitor_thread: Optional[threading.Thread] = None
        self._scheduler_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        
        self._evolution_callbacks: List[Callable[[EvolutionEvent], None]] = []
        self._current_evolution: Optional[EvolutionEvent] = None
        
        self._evolution_history: List[EvolutionEvent] = []
    
    def _setup_logger(self) -> logging.Logger:
        logger = logging.getLogger('SkillEvolutionManager')
        logger.setLevel(getattr(logging, self._config.log_level))
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        
        return logger
    
    @property
    def state(self) -> ManagerState:
        return self._state
    
    @property
    def change_detector(self) -> SkillContentChangeDetector:
        return self._change_detector
    
    @property
    def knowledge(self) -> SkillEvolutionKnowledge:
        return self._knowledge
    
    @property
    def snapshot_manager(self) -> SnapshotManager:
        return self._snapshot_manager
    
    @property
    def trigger_manager(self) -> TriggerManager:
        return self._trigger_manager
    
    @property
    def rollback_manager(self) -> RollbackManager:
        return self._rollback_manager
    
    def start_auto_evolution(self) -> None:
        """启动自动演化"""
        if self._running:
            return
        
        self._running = True
        self._stop_event.clear()
        self._set_state(ManagerState.MONITORING)
        
        self._monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._monitor_thread.start()
        
        self._scheduler_thread = threading.Thread(target=self._scheduler_loop, daemon=True)
        self._scheduler_thread.start()
        
        self._logger.info("自动演化已启动")
    
    def stop_auto_evolution(self) -> None:
        """停止自动演化"""
        self._running = False
        self._stop_event.set()
        
        if self._monitor_thread:
            self._monitor_thread.join(timeout=5)
        if self._scheduler_thread:
            self._scheduler_thread.join(timeout=5)
        
        self._set_state(ManagerState.IDLE)
        self._logger.info("自动演化已停止")
    
    def _monitor_loop(self) -> None:
        """监控循环"""
        while self._running and not self._stop_event.is_set():
            try:
                condition = self._trigger_manager.get_condition("content_change")
                if condition and condition.enabled:
                    result = self._change_detector.detect_changes(incremental=True)
                    
                    if result.has_changes:
                        self._logger.info(f"检测到内容变化: {len(result.changed_files)} 个文件")
                        self._trigger_manager.record_trigger("content_change")
                        
                        asyncio.run(self._trigger_evolution_internal(
                            TriggerType.CONTENT_CHANGE,
                            result
                        ))
                
            except Exception as e:
                self._logger.error(f"监控循环错误: {e}")
            
            interval = self._config.content_change_check_interval_seconds
            self._stop_event.wait(interval)
    
    def _scheduler_loop(self) -> None:
        """调度循环"""
        last_auto_trigger: Optional[datetime] = None
        last_scheduled_check: Optional[datetime] = None
        
        while self._running and not self._stop_event.is_set():
            try:
                now = datetime.now()
                
                auto_condition = self._trigger_manager.get_condition("auto_interval")
                if auto_condition and auto_condition.enabled:
                    interval = auto_condition.config.get("interval_seconds", 3600)
                    if last_auto_trigger is None or (now - last_auto_trigger).total_seconds() >= interval:
                        self._logger.info("自动间隔触发演化")
                        self._trigger_manager.record_trigger("auto_interval")
                        asyncio.run(self._trigger_evolution_internal(TriggerType.AUTO))
                        last_auto_trigger = now
                
                scheduled_condition = self._trigger_manager.get_condition("scheduled")
                if scheduled_condition and scheduled_condition.enabled:
                    times = scheduled_condition.config.get("times", [])
                    current_time = now.strftime("%H:%M")
                    
                    if current_time in times:
                        if last_scheduled_check is None or (now - last_scheduled_check).total_seconds() >= 60:
                            self._logger.info(f"定时触发演化: {current_time}")
                            self._trigger_manager.record_trigger("scheduled")
                            asyncio.run(self._trigger_evolution_internal(TriggerType.SCHEDULED))
                            last_scheduled_check = now
                
            except Exception as e:
                self._logger.error(f"调度循环错误: {e}")
            
            self._stop_event.wait(60)
    
    async def trigger_evolution(
        self,
        trigger_type: TriggerType = TriggerType.MANUAL,
        context: Optional[Dict[str, Any]] = None
    ) -> EvolutionEvent:
        """手动触发演化"""
        return await self._trigger_evolution_internal(trigger_type, context)
    
    async def _trigger_evolution_internal(
        self,
        trigger_type: TriggerType,
        context: Optional[Any] = None
    ) -> EvolutionEvent:
        """内部触发演化"""
        with self._state_lock:
            if self._state == ManagerState.EVOLVING:
                return EvolutionEvent(
                    event_id=f"EVT-{datetime.now().strftime('%Y%m%d%H%M%S')}",
                    evolution_type=EvolutionType.CONTENT_UPDATE,
                    status=EvolutionStatus.FAILED,
                    triggered_at=datetime.now(),
                    trigger_reason="演化正在进行中",
                    error_message="演化正在进行中，请稍后再试"
                )
            self._set_state(ManagerState.EVOLVING)
        
        event_id = f"EVT-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        event = EvolutionEvent(
            event_id=event_id,
            evolution_type=EvolutionType.CONTENT_UPDATE,
            status=EvolutionStatus.IN_PROGRESS,
            triggered_at=datetime.now(),
            trigger_reason=f"触发类型: {trigger_type.value}"
        )
        
        self._current_evolution = event
        
        try:
            affected_files = self._get_affected_files(context)
            event.affected_files = affected_files
            
            snapshot = self._snapshot_manager.create_snapshot(
                affected_files,
                trigger_type,
                {"event_id": event_id}
            )
            event.rollback_available = True
            event.rollback_data = {"snapshot_id": snapshot.snapshot_id}
            
            start_time = time.time()
            
            success = await self._execute_evolution(event, context)
            
            event.execution_time_seconds = time.time() - start_time
            event.completed_at = datetime.now()
            event.status = EvolutionStatus.COMPLETED if success else EvolutionStatus.FAILED
            
            if success:
                event.changes_summary = f"成功处理 {len(affected_files)} 个文件"
            else:
                event.error_message = "演化执行失败"
                
                if self._config.auto_rollback_on_failure:
                    self._logger.info("自动回滚失败的演化")
                    rollback_result = await self._rollback_manager.rollback_single_step()
                    if rollback_result.success:
                        event.status = EvolutionStatus.ROLLED_BACK
                        event.changes_summary = "演化失败，已自动回滚"
            
            self._knowledge.record_evolution(event)
            
            for callback in self._evolution_callbacks:
                try:
                    callback(event)
                except Exception as e:
                    self._logger.error(f"演化回调执行失败: {e}")
            
        except Exception as e:
            event.status = EvolutionStatus.FAILED
            event.error_message = str(e)
            event.completed_at = datetime.now()
            self._logger.error(f"演化执行异常: {e}\n{traceback.format_exc()}")
        
        finally:
            self._evolution_history.append(event)
            if len(self._evolution_history) > 100:
                self._evolution_history = self._evolution_history[-100:]
            
            self._current_evolution = None
            self._set_state(ManagerState.MONITORING if self._running else ManagerState.IDLE)
        
        return event
    
    def _get_affected_files(self, context: Optional[Any]) -> List[str]:
        """获取受影响的文件"""
        files: List[str] = []
        
        skill_md = self._skill_dir / "SKILL.md"
        if skill_md.exists():
            files.append(str(skill_md))
        
        subskills_dir = self._skill_dir / "subskills"
        if subskills_dir.exists():
            for md_file in subskills_dir.rglob("*.md"):
                files.append(str(md_file))
        
        scripts_dir = self._skill_dir / "skillscripts"
        if scripts_dir.exists():
            for py_file in scripts_dir.rglob("*.py"):
                if "__pycache__" not in str(py_file):
                    files.append(str(py_file))
        
        return files[:50]
    
    async def _execute_evolution(
        self,
        event: EvolutionEvent,
        context: Optional[Any]
    ) -> bool:
        """执行演化"""
        await asyncio.sleep(0.1)
        return True
    
    async def rollback(self, steps: int = 1) -> RollbackResult:
        """回滚演化
        
        Args:
            steps: 回滚步数，1 表示单步回滚，-1 表示完全回滚
        
        Returns:
            回滚结果
        """
        with self._state_lock:
            if self._state == ManagerState.ROLLING_BACK:
                return RollbackResult(
                    rollback_id=f"ROLLBACK-{datetime.now().strftime('%Y%m%d%H%M%S')}",
                    success=False,
                    rollback_type=RollbackType.SINGLE_STEP,
                    steps_rolled_back=0,
                    error_message="回滚正在进行中"
                )
            self._set_state(ManagerState.ROLLING_BACK)
        
        try:
            if steps == 1:
                result = await self._rollback_manager.rollback_single_step()
            elif steps == -1:
                result = await self._rollback_manager.rollback_full()
            else:
                result = await self._rollback_manager.rollback_multi_step(steps)
            
            if result.success:
                event = EvolutionEvent(
                    event_id=f"EVT-{datetime.now().strftime('%Y%m%d%H%M%S')}",
                    evolution_type=EvolutionType.CONTENT_UPDATE,
                    status=EvolutionStatus.ROLLED_BACK,
                    triggered_at=datetime.now(),
                    trigger_reason=f"回滚 {result.steps_rolled_back} 步",
                    affected_files=result.files_restored,
                    changes_summary=f"已恢复 {len(result.files_restored)} 个文件"
                )
                self._knowledge.record_evolution(event)
            
            return result
            
        finally:
            self._set_state(ManagerState.MONITORING if self._running else ManagerState.IDLE)
    
    async def rollback_to_snapshot(self, snapshot_id: str) -> RollbackResult:
        """回滚到指定快照"""
        return await self._rollback_manager.rollback_to_snapshot(snapshot_id)
    
    def _set_state(self, state: ManagerState) -> None:
        """设置状态"""
        self._state = state
        self._logger.debug(f"状态变更: {state.value}")
    
    def register_evolution_callback(
        self,
        callback: Callable[[EvolutionEvent], None]
    ) -> None:
        """注册演化回调"""
        self._evolution_callbacks.append(callback)
    
    def unregister_evolution_callback(
        self,
        callback: Callable[[EvolutionEvent], None]
    ) -> bool:
        """注销演化回调"""
        if callback in self._evolution_callbacks:
            self._evolution_callbacks.remove(callback)
            return True
        return False
    
    def get_status(self) -> Dict[str, Any]:
        """获取状态"""
        return {
            "state": self._state.value,
            "running": self._running,
            "current_evolution": self._current_evolution.to_dict() if self._current_evolution else None,
            "evolution_history_count": len(self._evolution_history),
            "snapshots_count": len(self._snapshot_manager.get_snapshots(100)),
            "trigger_conditions": [c.to_dict() for c in self._trigger_manager.get_all_conditions()],
            "knowledge_stats": self._knowledge.get_statistics()
        }
    
    def get_evolution_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """获取演化历史"""
        return [e.to_dict() for e in self._evolution_history[-limit:]]
    
    def get_available_snapshots(self) -> List[Dict[str, Any]]:
        """获取可用快照"""
        snapshots = self._snapshot_manager.get_snapshots(20)
        return [s.to_dict() for s in snapshots]
    
    def pause(self) -> None:
        """暂停"""
        if self._state == ManagerState.MONITORING:
            self._set_state(ManagerState.PAUSED)
            self._logger.info("演化管理器已暂停")
    
    def resume(self) -> None:
        """恢复"""
        if self._state == ManagerState.PAUSED:
            self._set_state(ManagerState.MONITORING)
            self._logger.info("演化管理器已恢复")
    
    def enable_trigger(self, condition_id: str) -> bool:
        """启用触发条件"""
        return self._trigger_manager.enable_condition(condition_id)
    
    def disable_trigger(self, condition_id: str) -> bool:
        """禁用触发条件"""
        return self._trigger_manager.disable_condition(condition_id)
    
    def add_custom_trigger(self, condition: TriggerCondition) -> None:
        """添加自定义触发条件"""
        self._trigger_manager.add_condition(condition)
    
    def remove_custom_trigger(self, condition_id: str) -> bool:
        """移除自定义触发条件"""
        return self._trigger_manager.remove_condition(condition_id)


async def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='技能演化管理器')
    parser.add_argument('--skill-dir', default='.', help='技能目录')
    parser.add_argument('--start', action='store_true', help='启动自动演化')
    parser.add_argument('--trigger', action='store_true', help='手动触发演化')
    parser.add_argument('--rollback', type=int, default=0, help='回滚步数')
    parser.add_argument('--status', action='store_true', help='获取状态')
    parser.add_argument('--snapshots', action='store_true', help='获取快照列表')
    parser.add_argument('--history', action='store_true', help='获取演化历史')
    
    args = parser.parse_args()
    
    manager = SkillEvolutionManager(args.skill_dir)
    
    if args.status:
        print(json.dumps(manager.get_status(), indent=2, default=str))
        return
    
    if args.snapshots:
        print(json.dumps(manager.get_available_snapshots(), indent=2, default=str))
        return
    
    if args.history:
        print(json.dumps(manager.get_evolution_history(), indent=2, default=str))
        return
    
    if args.rollback > 0:
        result = await manager.rollback(args.rollback)
        print(json.dumps(result.to_dict(), indent=2, default=str))
        return
    
    if args.trigger:
        event = await manager.trigger_evolution(TriggerType.MANUAL)
        print(json.dumps(event.to_dict(), indent=2, default=str))
        return
    
    if args.start:
        print("启动自动演化...")
        manager.start_auto_evolution()
        
        try:
            while True:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            print("\n停止自动演化...")
            manager.stop_auto_evolution()


if __name__ == '__main__':
    asyncio.run(main())
