#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
演化配置管理器 - Sanliu 技能

功能：
- 演化触发条件配置（错误率阈值、性能阈值、定时配置等）
- 演化策略配置（修复策略、学习策略、报告策略）
- 配置热重载支持
- 配置验证和默认值
- 配置持久化和版本管理

使用方法：
    from evolution_config_manager import EvolutionConfigManager, EvolutionTriggerType
    
    # 创建配置管理器
    manager = EvolutionConfigManager()
    
    # 获取触发条件配置
    triggers = manager.get_trigger_config()
    
    # 检查是否应该触发演化
    if manager.should_trigger_evolution(error_rate=0.08):
        manager.execute_evolution()
    
    # 热重载配置
    manager.reload_config()
"""

import hashlib
import json
import logging
import os
import sys
import threading
from dataclasses import dataclass, field, asdict
from datetime import datetime, time, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set, Tuple

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - [%(name)s] %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


class EvolutionTriggerType(Enum):
    """演化触发类型枚举"""
    ERROR_RATE = "error_rate"
    PERFORMANCE_DEGRADATION = "performance_degradation"
    SCHEDULE = "schedule"
    MANUAL = "manual"
    THRESHOLD = "threshold"
    PATTERN_DETECTED = "pattern_detected"
    USER_REQUEST = "user_request"


class EvolutionStrategyType(Enum):
    """演化策略类型枚举"""
    FIX = "fix"
    LEARNING = "learning"
    REPORT = "report"
    ROLLBACK = "rollback"
    OPTIMIZATION = "optimization"
    ADAPTATION = "adaptation"


class EvolutionPriority(Enum):
    """演化优先级枚举"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class EvolutionStatus(Enum):
    """演化状态枚举"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    ROLLED_BACK = "rolled_back"


class EvolutionConfigError(Exception):
    """演化配置基础异常类"""
    
    def __init__(self, message: str, config_key: Optional[str] = None):
        super().__init__(message)
        self.config_key = config_key
    
    def __str__(self) -> str:
        base_msg = super().__str__()
        if self.config_key:
            return f"{base_msg} (配置项: {self.config_key})"
        return base_msg


class ConfigValidationError(EvolutionConfigError):
    """配置验证异常"""
    pass


class ConfigReloadError(EvolutionConfigError):
    """配置重载异常"""
    pass


@dataclass
class ScheduleConfig:
    """定时调度配置"""
    daily: Optional[str] = None
    weekly: Optional[str] = None
    cron_expression: Optional[str] = None
    timezone: str = "Asia/Shanghai"
    enabled: bool = True
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ScheduleConfig':
        return cls(
            daily=data.get('daily'),
            weekly=data.get('weekly'),
            cron_expression=data.get('cron_expression'),
            timezone=data.get('timezone', 'Asia/Shanghai'),
            enabled=data.get('enabled', True)
        )
    
    def validate(self) -> Tuple[bool, List[str]]:
        errors = []
        
        if self.daily:
            try:
                time.fromisoformat(self.daily)
            except ValueError:
                errors.append(f"无效的每日时间格式: {self.daily}")
        
        if self.weekly:
            parts = self.weekly.split()
            if len(parts) != 2:
                errors.append(f"无效的每周时间格式: {self.weekly}")
            else:
                valid_days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
                if parts[0] not in valid_days:
                    errors.append(f"无效的星期: {parts[0]}")
                try:
                    time.fromisoformat(parts[1])
                except ValueError:
                    errors.append(f"无效的时间格式: {parts[1]}")
        
        return len(errors) == 0, errors


@dataclass
class TriggerConfig:
    """触发条件配置"""
    error_rate_threshold: float = 0.05
    performance_degradation_threshold: float = 0.2
    consecutive_failures_threshold: int = 3
    min_data_points: int = 10
    cooldown_minutes: int = 30
    schedule: ScheduleConfig = field(default_factory=ScheduleConfig)
    enabled_triggers: Set[EvolutionTriggerType] = field(default_factory=lambda: {
        EvolutionTriggerType.ERROR_RATE,
        EvolutionTriggerType.PERFORMANCE_DEGRADATION,
        EvolutionTriggerType.SCHEDULE
    })
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "error_rate_threshold": self.error_rate_threshold,
            "performance_degradation_threshold": self.performance_degradation_threshold,
            "consecutive_failures_threshold": self.consecutive_failures_threshold,
            "min_data_points": self.min_data_points,
            "cooldown_minutes": self.cooldown_minutes,
            "schedule": self.schedule.to_dict(),
            "enabled_triggers": [t.value for t in self.enabled_triggers]
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TriggerConfig':
        enabled_triggers = set()
        for t in data.get('enabled_triggers', []):
            try:
                enabled_triggers.add(EvolutionTriggerType(t))
            except ValueError:
                logger.warning(f"未知的触发类型: {t}")
        
        schedule_data = data.get('schedule', {})
        
        return cls(
            error_rate_threshold=data.get('error_rate_threshold', 0.05),
            performance_degradation_threshold=data.get('performance_degradation_threshold', 0.2),
            consecutive_failures_threshold=data.get('consecutive_failures_threshold', 3),
            min_data_points=data.get('min_data_points', 10),
            cooldown_minutes=data.get('cooldown_minutes', 30),
            schedule=ScheduleConfig.from_dict(schedule_data),
            enabled_triggers=enabled_triggers or {
                EvolutionTriggerType.ERROR_RATE,
                EvolutionTriggerType.PERFORMANCE_DEGRADATION,
                EvolutionTriggerType.SCHEDULE
            }
        )
    
    def validate(self) -> Tuple[bool, List[str]]:
        errors = []
        
        if not 0 <= self.error_rate_threshold <= 1:
            errors.append(f"错误率阈值必须在 0-1 之间: {self.error_rate_threshold}")
        
        if not 0 <= self.performance_degradation_threshold <= 1:
            errors.append(f"性能下降阈值必须在 0-1 之间: {self.performance_degradation_threshold}")
        
        if self.consecutive_failures_threshold < 1:
            errors.append(f"连续失败阈值必须大于 0: {self.consecutive_failures_threshold}")
        
        if self.min_data_points < 1:
            errors.append(f"最小数据点数必须大于 0: {self.min_data_points}")
        
        if self.cooldown_minutes < 0:
            errors.append(f"冷却时间不能为负: {self.cooldown_minutes}")
        
        schedule_valid, schedule_errors = self.schedule.validate()
        errors.extend(schedule_errors)
        
        return len(errors) == 0, errors


@dataclass
class FixStrategyConfig:
    """修复策略配置"""
    auto_fix_enabled: bool = True
    max_attempts: int = 3
    rollback_enabled: bool = True
    fix_timeout_seconds: int = 300
    validation_enabled: bool = True
    priority_threshold: EvolutionPriority = EvolutionPriority.MEDIUM
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "auto_fix_enabled": self.auto_fix_enabled,
            "max_attempts": self.max_attempts,
            "rollback_enabled": self.rollback_enabled,
            "fix_timeout_seconds": self.fix_timeout_seconds,
            "validation_enabled": self.validation_enabled,
            "priority_threshold": self.priority_threshold.value
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'FixStrategyConfig':
        priority_str = data.get('priority_threshold', 'medium')
        try:
            priority = EvolutionPriority(priority_str)
        except ValueError:
            priority = EvolutionPriority.MEDIUM
        
        return cls(
            auto_fix_enabled=data.get('auto_fix_enabled', True),
            max_attempts=data.get('max_attempts', 3),
            rollback_enabled=data.get('rollback_enabled', True),
            fix_timeout_seconds=data.get('fix_timeout_seconds', 300),
            validation_enabled=data.get('validation_enabled', True),
            priority=priority
        )
    
    def validate(self) -> Tuple[bool, List[str]]:
        errors = []
        
        if self.max_attempts < 1:
            errors.append(f"最大尝试次数必须大于 0: {self.max_attempts}")
        
        if self.fix_timeout_seconds < 1:
            errors.append(f"修复超时时间必须大于 0: {self.fix_timeout_seconds}")
        
        return len(errors) == 0, errors


@dataclass
class LearningStrategyConfig:
    """学习策略配置"""
    pattern_learning_enabled: bool = True
    knowledge_base_path: str = "data/knowledge"
    max_patterns: int = 1000
    learning_rate: float = 0.1
    min_confidence: float = 0.7
    retention_days: int = 90
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "pattern_learning_enabled": self.pattern_learning_enabled,
            "knowledge_base_path": self.knowledge_base_path,
            "max_patterns": self.max_patterns,
            "learning_rate": self.learning_rate,
            "min_confidence": self.min_confidence,
            "retention_days": self.retention_days
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'LearningStrategyConfig':
        return cls(
            pattern_learning_enabled=data.get('pattern_learning_enabled', True),
            knowledge_base_path=data.get('knowledge_base_path', 'data/knowledge'),
            max_patterns=data.get('max_patterns', 1000),
            learning_rate=data.get('learning_rate', 0.1),
            min_confidence=data.get('min_confidence', 0.7),
            retention_days=data.get('retention_days', 90)
        )
    
    def validate(self) -> Tuple[bool, List[str]]:
        errors = []
        
        if self.max_patterns < 1:
            errors.append(f"最大模式数必须大于 0: {self.max_patterns}")
        
        if not 0 < self.learning_rate <= 1:
            errors.append(f"学习率必须在 0-1 之间: {self.learning_rate}")
        
        if not 0 <= self.min_confidence <= 1:
            errors.append(f"最小置信度必须在 0-1 之间: {self.min_confidence}")
        
        if self.retention_days < 1:
            errors.append(f"保留天数必须大于 0: {self.retention_days}")
        
        return len(errors) == 0, errors


@dataclass
class ReportStrategyConfig:
    """报告策略配置"""
    auto_report_enabled: bool = True
    report_format: str = "json"
    report_path: str = None
    include_metrics: bool = True
    include_history: bool = True
    max_history_entries: int = 100
    notify_on_complete: bool = True
    notify_on_failure: bool = True
    
    def __post_init__(self):
        if self.report_path is None:
            try:
                from skillscripts.utils.enhanced_path_config_manager import create_path_manager, OutputType
                _path_mgr = create_path_manager()
                self.report_path = str(_path_mgr.get_output_path(OutputType.REPORT, subdirectory="evolution"))
            except Exception:
                self.report_path = "reports/evolution"
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "auto_report_enabled": self.auto_report_enabled,
            "report_format": self.report_format,
            "report_path": self.report_path,
            "include_metrics": self.include_metrics,
            "include_history": self.include_history,
            "max_history_entries": self.max_history_entries,
            "notify_on_complete": self.notify_on_complete,
            "notify_on_failure": self.notify_on_failure
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ReportStrategyConfig':
        report_path = data.get('report_path')
        if report_path is None:
            try:
                from skillscripts.utils.enhanced_path_config_manager import create_path_manager, OutputType
                _path_mgr = create_path_manager()
                report_path = str(_path_mgr.get_output_path(OutputType.REPORT, subdirectory="evolution"))
            except Exception:
                report_path = "reports/evolution"
        return cls(
            auto_report_enabled=data.get('auto_report_enabled', True),
            report_format=data.get('report_format', 'json'),
            report_path=report_path,
            include_metrics=data.get('include_metrics', True),
            include_history=data.get('include_history', True),
            max_history_entries=data.get('max_history_entries', 100),
            notify_on_complete=data.get('notify_on_complete', True),
            notify_on_failure=data.get('notify_on_failure', True)
        )
    
    def validate(self) -> Tuple[bool, List[str]]:
        errors = []
        
        valid_formats = ["json", "yaml", "markdown", "html", "text"]
        if self.report_format not in valid_formats:
            errors.append(f"无效的报告格式: {self.report_format}, 支持的格式: {valid_formats}")
        
        if self.max_history_entries < 1:
            errors.append(f"最大历史条目数必须大于 0: {self.max_history_entries}")
        
        return len(errors) == 0, errors


@dataclass
class StrategyConfig:
    """策略配置集合"""
    fix: FixStrategyConfig = field(default_factory=FixStrategyConfig)
    learning: LearningStrategyConfig = field(default_factory=LearningStrategyConfig)
    report: ReportStrategyConfig = field(default_factory=ReportStrategyConfig)
    enabled_strategies: Set[EvolutionStrategyType] = field(default_factory=lambda: {
        EvolutionStrategyType.FIX,
        EvolutionStrategyType.LEARNING,
        EvolutionStrategyType.REPORT
    })
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "fix": self.fix.to_dict(),
            "learning": self.learning.to_dict(),
            "report": self.report.to_dict(),
            "enabled_strategies": [s.value for s in self.enabled_strategies]
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'StrategyConfig':
        enabled_strategies = set()
        for s in data.get('enabled_strategies', []):
            try:
                enabled_strategies.add(EvolutionStrategyType(s))
            except ValueError:
                logger.warning(f"未知的策略类型: {s}")
        
        return cls(
            fix=FixStrategyConfig.from_dict(data.get('fix', {})),
            learning=LearningStrategyConfig.from_dict(data.get('learning', {})),
            report=ReportStrategyConfig.from_dict(data.get('report', {})),
            enabled_strategies=enabled_strategies or {
                EvolutionStrategyType.FIX,
                EvolutionStrategyType.LEARNING,
                EvolutionStrategyType.REPORT
            }
        )
    
    def validate(self) -> Tuple[bool, List[str]]:
        errors = []
        
        fix_valid, fix_errors = self.fix.validate()
        errors.extend(fix_errors)
        
        learning_valid, learning_errors = self.learning.validate()
        errors.extend(learning_errors)
        
        report_valid, report_errors = self.report.validate()
        errors.extend(report_errors)
        
        return len(errors) == 0, errors


@dataclass
class EvolutionConfig:
    """演化配置主类"""
    triggers: TriggerConfig = field(default_factory=TriggerConfig)
    strategies: StrategyConfig = field(default_factory=StrategyConfig)
    version: str = "1.0.0"
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "evolution": {
                "triggers": self.triggers.to_dict(),
                "strategies": self.strategies.to_dict(),
                "version": self.version,
                "created_at": self.created_at,
                "updated_at": self.updated_at
            }
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'EvolutionConfig':
        evolution_data = data.get('evolution', data)
        
        return cls(
            triggers=TriggerConfig.from_dict(evolution_data.get('triggers', {})),
            strategies=StrategyConfig.from_dict(evolution_data.get('strategies', {})),
            version=evolution_data.get('version', '1.0.0'),
            created_at=evolution_data.get('created_at', datetime.now().isoformat()),
            updated_at=evolution_data.get('updated_at', datetime.now().isoformat())
        )
    
    def validate(self) -> Tuple[bool, List[str]]:
        errors = []
        
        triggers_valid, triggers_errors = self.triggers.validate()
        errors.extend(triggers_errors)
        
        strategies_valid, strategies_errors = self.strategies.validate()
        errors.extend(strategies_errors)
        
        return len(errors) == 0, errors
    
    def update_timestamp(self) -> None:
        self.updated_at = datetime.now().isoformat()


class ConfigWatcher:
    """配置文件监视器"""
    
    def __init__(self, config_path: Path, callback: Callable[[], None]):
        self.config_path = config_path
        self.callback = callback
        self._last_hash: Optional[str] = None
        self._running = False
        self._thread: Optional[threading.Thread] = None
    
    def start(self) -> None:
        if self._running:
            return
        
        self._running = True
        self._last_hash = self._calculate_hash()
        self._thread = threading.Thread(target=self._watch_loop, daemon=True)
        self._thread.start()
        logger.info(f"配置监视器已启动: {self.config_path}")
    
    def stop(self) -> None:
        self._running = False
        if self._thread:
            self._thread.join(timeout=5)
        logger.info("配置监视器已停止")
    
    def _watch_loop(self) -> None:
        import time
        while self._running:
            try:
                current_hash = self._calculate_hash()
                if current_hash and current_hash != self._last_hash:
                    logger.info("检测到配置文件变更")
                    self._last_hash = current_hash
                    self.callback()
            except Exception as e:
                logger.error(f"配置监视错误: {e}")
            
            time.sleep(5)
    
    def _calculate_hash(self) -> Optional[str]:
        if not self.config_path.exists():
            return None
        
        try:
            content = self.config_path.read_bytes()
            return hashlib.md5(content).hexdigest()
        except Exception as e:
            logger.error(f"计算文件哈希失败: {e}")
            return None


class EvolutionConfigManager:
    """
    演化配置管理器
    
    核心功能：
    - 演化触发条件配置管理
    - 演化策略配置管理
    - 配置热重载支持
    - 配置验证和默认值
    - 配置持久化
    - 配置变更通知
    """
    
    DEFAULT_CONFIG_FILE = "evolution_config.yaml"
    
    def __init__(
        self,
        config_path: Optional[str] = None,
        auto_reload: bool = False,
        base_path: Optional[Path] = None
    ):
        self._config_path = Path(config_path) if config_path else None
        self._base_path = base_path or Path.cwd()
        self._auto_reload = auto_reload
        self._config: Optional[EvolutionConfig] = None
        self._lock = threading.RLock()
        self._change_callbacks: List[Callable[[EvolutionConfig], None]] = []
        self._watcher: Optional[ConfigWatcher] = None
        self._last_reload_time: Optional[datetime] = None
        self._reload_count: int = 0
        
        self._initialize_config()
        
        if auto_reload and self._config_path:
            self._start_watcher()
        
        logger.info(f"EvolutionConfigManager 初始化完成, 配置路径: {self._config_path}")
    
    def _initialize_config(self) -> None:
        if self._config_path and self._config_path.exists():
            self._load_config()
        else:
            self._config = EvolutionConfig()
            logger.info("使用默认配置")
    
    def _load_config(self) -> None:
        if not self._config_path or not self._config_path.exists():
            raise ConfigReloadError("配置文件不存在", str(self._config_path))
        
        try:
            content = self._config_path.read_text(encoding='utf-8')
            
            if self._config_path.suffix in ['.yaml', '.yml']:
                data = self._parse_yaml(content)
            else:
                data = json.loads(content)
            
            new_config = EvolutionConfig.from_dict(data)
            
            valid, errors = new_config.validate()
            if not valid:
                raise ConfigValidationError(f"配置验证失败: {'; '.join(errors)}")
            
            with self._lock:
                old_config = self._config
                self._config = new_config
                self._last_reload_time = datetime.now()
                self._reload_count += 1
            
            self._notify_change(new_config)
            logger.info(f"配置加载成功: {self._config_path}")
            
        except json.JSONDecodeError as e:
            raise ConfigReloadError(f"JSON 解析失败: {e}", str(self._config_path))
        except Exception as e:
            raise ConfigReloadError(f"加载配置失败: {e}", str(self._config_path))
    
    def _parse_yaml(self, content: str) -> Dict[str, Any]:
        try:
            import yaml
            return yaml.safe_load(content) or {}
        except ImportError:
            logger.warning("PyYAML 未安装，尝试简单解析")
            return self._simple_yaml_parse(content)
    
    def _simple_yaml_parse(self, content: str) -> Dict[str, Any]:
        result: Dict[str, Any] = {}
        current_section: Optional[str] = None
        current_subsection: Optional[str] = None
        
        for line in content.split('\n'):
            stripped = line.rstrip()
            if not stripped or stripped.startswith('#'):
                continue
            
            indent = len(line) - len(line.lstrip())
            
            if ':' in stripped:
                key, value = stripped.split(':', 1)
                key = key.strip()
                value = value.strip()
                
                if indent == 0:
                    current_section = key
                    current_subsection = None
                    result[current_section] = {}
                elif indent == 2 and current_section:
                    current_subsection = key
                    result[current_section][current_subsection] = {}
                elif indent == 4 and current_section and current_subsection:
                    if value:
                        result[current_section][current_subsection][key] = self._parse_value(value)
                elif current_section and not current_subsection:
                    if value:
                        result[current_section][key] = self._parse_value(value)
        
        return result
    
    def _parse_value(self, value: str) -> Any:
        if value.lower() == 'true':
            return True
        elif value.lower() == 'false':
            return False
        elif value.isdigit():
            return int(value)
        elif value.replace('.', '').isdigit():
            return float(value)
        elif value.startswith('"') and value.endswith('"'):
            return value[1:-1]
        elif value.startswith("'") and value.endswith("'"):
            return value[1:-1]
        elif value.startswith('[') and value.endswith(']'):
            items = value[1:-1].split(',')
            return [self._parse_value(item.strip()) for item in items if item.strip()]
        return value
    
    def _start_watcher(self) -> None:
        if self._watcher:
            return
        
        self._watcher = ConfigWatcher(
            self._config_path,
            self._on_config_change
        )
        self._watcher.start()
    
    def _stop_watcher(self) -> None:
        if self._watcher:
            self._watcher.stop()
            self._watcher = None
    
    def _on_config_change(self) -> None:
        try:
            self._load_config()
            logger.info("配置热重载成功")
        except Exception as e:
            logger.error(f"配置热重载失败: {e}")
    
    def _notify_change(self, config: EvolutionConfig) -> None:
        for callback in self._change_callbacks:
            try:
                callback(config)
            except Exception as e:
                logger.error(f"配置变更回调执行失败: {e}")
    
    def get_config(self) -> EvolutionConfig:
        with self._lock:
            return self._config
    
    def get_trigger_config(self) -> TriggerConfig:
        with self._lock:
            return self._config.triggers
    
    def get_strategy_config(self) -> StrategyConfig:
        with self._lock:
            return self._config.strategies
    
    def get_fix_strategy(self) -> FixStrategyConfig:
        with self._lock:
            return self._config.strategies.fix
    
    def get_learning_strategy(self) -> LearningStrategyConfig:
        with self._lock:
            return self._config.strategies.learning
    
    def get_report_strategy(self) -> ReportStrategyConfig:
        with self._lock:
            return self._config.strategies.report
    
    def should_trigger_evolution(
        self,
        error_rate: Optional[float] = None,
        performance_degradation: Optional[float] = None,
        consecutive_failures: Optional[int] = None,
        trigger_type: Optional[EvolutionTriggerType] = None
    ) -> Tuple[bool, List[str]]:
        reasons = []
        should_trigger = False
        
        with self._lock:
            triggers = self._config.triggers
            
            if trigger_type and trigger_type not in triggers.enabled_triggers:
                return False, ["触发类型未启用"]
            
            if error_rate is not None and EvolutionTriggerType.ERROR_RATE in triggers.enabled_triggers:
                if error_rate >= triggers.error_rate_threshold:
                    reasons.append(f"错误率 {error_rate:.2%} 超过阈值 {triggers.error_rate_threshold:.2%}")
                    should_trigger = True
            
            if performance_degradation is not None and EvolutionTriggerType.PERFORMANCE_DEGRADATION in triggers.enabled_triggers:
                if performance_degradation >= triggers.performance_degradation_threshold:
                    reasons.append(f"性能下降 {performance_degradation:.2%} 超过阈值 {triggers.performance_degradation_threshold:.2%}")
                    should_trigger = True
            
            if consecutive_failures is not None and EvolutionTriggerType.THRESHOLD in triggers.enabled_triggers:
                if consecutive_failures >= triggers.consecutive_failures_threshold:
                    reasons.append(f"连续失败次数 {consecutive_failures} 超过阈值 {triggers.consecutive_failures_threshold}")
                    should_trigger = True
        
        return should_trigger, reasons
    
    def is_strategy_enabled(self, strategy_type: EvolutionStrategyType) -> bool:
        with self._lock:
            return strategy_type in self._config.strategies.enabled_strategies
    
    def update_trigger_config(self, updates: Dict[str, Any]) -> bool:
        with self._lock:
            try:
                current = self._config.triggers.to_dict()
                current.update(updates)
                
                new_trigger = TriggerConfig.from_dict(current)
                valid, errors = new_trigger.validate()
                
                if not valid:
                    raise ConfigValidationError(f"触发配置验证失败: {'; '.join(errors)}")
                
                self._config.triggers = new_trigger
                self._config.update_timestamp()
                
                self._notify_change(self._config)
                logger.info("触发配置已更新")
                return True
                
            except Exception as e:
                logger.error(f"更新触发配置失败: {e}")
                return False
    
    def update_strategy_config(self, strategy_type: str, updates: Dict[str, Any]) -> bool:
        with self._lock:
            try:
                if strategy_type == "fix":
                    current = self._config.strategies.fix.to_dict()
                    current.update(updates)
                    new_strategy = FixStrategyConfig.from_dict(current)
                    valid, errors = new_strategy.validate()
                    if not valid:
                        raise ConfigValidationError(f"修复策略验证失败: {'; '.join(errors)}")
                    self._config.strategies.fix = new_strategy
                    
                elif strategy_type == "learning":
                    current = self._config.strategies.learning.to_dict()
                    current.update(updates)
                    new_strategy = LearningStrategyConfig.from_dict(current)
                    valid, errors = new_strategy.validate()
                    if not valid:
                        raise ConfigValidationError(f"学习策略验证失败: {'; '.join(errors)}")
                    self._config.strategies.learning = new_strategy
                    
                elif strategy_type == "report":
                    current = self._config.strategies.report.to_dict()
                    current.update(updates)
                    new_strategy = ReportStrategyConfig.from_dict(current)
                    valid, errors = new_strategy.validate()
                    if not valid:
                        raise ConfigValidationError(f"报告策略验证失败: {'; '.join(errors)}")
                    self._config.strategies.report = new_strategy
                    
                else:
                    raise ConfigValidationError(f"未知的策略类型: {strategy_type}")
                
                self._config.update_timestamp()
                self._notify_change(self._config)
                logger.info(f"策略配置已更新: {strategy_type}")
                return True
                
            except Exception as e:
                logger.error(f"更新策略配置失败: {e}")
                return False
    
    def reload_config(self) -> bool:
        try:
            self._load_config()
            return True
        except Exception as e:
            logger.error(f"重载配置失败: {e}")
            return False
    
    def save_config(self, path: Optional[str] = None) -> bool:
        save_path = Path(path) if path else self._config_path
        
        if not save_path:
            save_path = self._base_path / "config" / self.DEFAULT_CONFIG_FILE
        
        try:
            save_path.parent.mkdir(parents=True, exist_ok=True)
            
            with self._lock:
                self._config.update_timestamp()
                data = self._config.to_dict()
            
            if save_path.suffix in ['.yaml', '.yml']:
                content = self._to_yaml(data)
            else:
                content = json.dumps(data, indent=2, ensure_ascii=False)
            
            save_path.write_text(content, encoding='utf-8')
            
            logger.info(f"配置已保存: {save_path}")
            return True
            
        except Exception as e:
            logger.error(f"保存配置失败: {e}")
            return False
    
    def _to_yaml(self, data: Dict[str, Any]) -> str:
        try:
            import yaml
            return yaml.dump(data, allow_unicode=True, default_flow_style=False)
        except ImportError:
            return self._dict_to_yaml(data)
    
    def _dict_to_yaml(self, data: Dict[str, Any], indent: int = 0) -> str:
        lines = []
        prefix = "  " * indent
        
        for key, value in data.items():
            if isinstance(value, dict):
                lines.append(f"{prefix}{key}:")
                lines.append(self._dict_to_yaml(value, indent + 1))
            elif isinstance(value, list):
                lines.append(f"{prefix}{key}:")
                for item in value:
                    if isinstance(item, dict):
                        lines.append(f"{prefix}  -")
                        for k, v in item.items():
                            lines.append(f"{prefix}    {k}: {self._format_yaml_value(v)}")
                    else:
                        lines.append(f"{prefix}  - {self._format_yaml_value(item)}")
            elif isinstance(value, bool):
                lines.append(f"{prefix}{key}: {str(value).lower()}")
            elif value is None:
                lines.append(f"{prefix}{key}: null")
            else:
                lines.append(f"{prefix}{key}: {self._format_yaml_value(value)}")
        
        return "\n".join(lines)
    
    def _format_yaml_value(self, value: Any) -> str:
        if isinstance(value, str):
            if ' ' in value or ':' in value:
                return f'"{value}"'
            return value
        elif isinstance(value, bool):
            return str(value).lower()
        elif value is None:
            return "null"
        return str(value)
    
    def register_change_callback(self, callback: Callable[[EvolutionConfig], None]) -> None:
        self._change_callbacks.append(callback)
    
    def unregister_change_callback(self, callback: Callable[[EvolutionConfig], None]) -> None:
        if callback in self._change_callbacks:
            self._change_callbacks.remove(callback)
    
    def get_config_info(self) -> Dict[str, Any]:
        with self._lock:
            return {
                "config_path": str(self._config_path) if self._config_path else None,
                "auto_reload": self._auto_reload,
                "last_reload_time": self._last_reload_time.isoformat() if self._last_reload_time else None,
                "reload_count": self._reload_count,
                "watcher_active": self._watcher is not None and self._watcher._running,
                "config_version": self._config.version,
                "created_at": self._config.created_at,
                "updated_at": self._config.updated_at,
                "enabled_triggers": [t.value for t in self._config.triggers.enabled_triggers],
                "enabled_strategies": [s.value for s in self._config.strategies.enabled_strategies]
            }
    
    def validate_current_config(self) -> Tuple[bool, List[str]]:
        with self._lock:
            return self._config.validate()
    
    def reset_to_defaults(self) -> bool:
        with self._lock:
            try:
                self._config = EvolutionConfig()
                self._notify_change(self._config)
                logger.info("配置已重置为默认值")
                return True
            except Exception as e:
                logger.error(f"重置配置失败: {e}")
                return False
    
    def export_config(self, format: str = "json") -> str:
        with self._lock:
            data = self._config.to_dict()
        
        if format.lower() == "yaml":
            return self._to_yaml(data)
        return json.dumps(data, indent=2, ensure_ascii=False)
    
    def import_config(self, config_data: Dict[str, Any]) -> bool:
        try:
            new_config = EvolutionConfig.from_dict(config_data)
            valid, errors = new_config.validate()
            
            if not valid:
                raise ConfigValidationError(f"配置验证失败: {'; '.join(errors)}")
            
            with self._lock:
                self._config = new_config
            
            self._notify_change(new_config)
            logger.info("配置导入成功")
            return True
            
        except Exception as e:
            logger.error(f"导入配置失败: {e}")
            return False
    
    def shutdown(self) -> None:
        self._stop_watcher()
        self._change_callbacks.clear()
        logger.info("EvolutionConfigManager 已关闭")


def create_default_config_file(path: str) -> bool:
    manager = EvolutionConfigManager()
    return manager.save_config(path)


def main():
    import argparse
    
    parser = argparse.ArgumentParser(
        description="演化配置管理器 - Sanliu 技能",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        '--config',
        type=str,
        help='配置文件路径'
    )
    parser.add_argument(
        '--info',
        action='store_true',
        help='显示配置信息'
    )
    parser.add_argument(
        '--validate',
        action='store_true',
        help='验证当前配置'
    )
    parser.add_argument(
        '--save',
        type=str,
        help='保存配置到指定路径'
    )
    parser.add_argument(
        '--export',
        type=str,
        choices=['json', 'yaml'],
        default='json',
        help='导出配置格式'
    )
    parser.add_argument(
        '--create-default',
        type=str,
        help='创建默认配置文件'
    )
    parser.add_argument(
        '--check-trigger',
        type=str,
        nargs='+',
        help='检查是否应该触发演化 (格式: error_rate=X performance=Y)'
    )
    
    args = parser.parse_args()
    
    if args.create_default:
        result = create_default_config_file(args.create_default)
        print(f"创建默认配置文件: {'成功' if result else '失败'}")
        return
    
    manager = EvolutionConfigManager(config_path=args.config)
    
    if args.info:
        info = manager.get_config_info()
        print(json.dumps(info, indent=2, ensure_ascii=False))
    
    if args.validate:
        valid, errors = manager.validate_current_config()
        print(f"配置验证: {'通过' if valid else '失败'}")
        if errors:
            for error in errors:
                print(f"  - {error}")
    
    if args.save:
        result = manager.save_config(args.save)
        print(f"保存配置: {'成功' if result else '失败'}")
    
    if args.export and not args.save:
        content = manager.export_config(args.export)
        print(content)
    
    if args.check_trigger:
        params = {}
        for item in args.check_trigger:
            if '=' in item:
                key, value = item.split('=', 1)
                try:
                    params[key] = float(value)
                except ValueError:
                    params[key] = value
        
        should_trigger, reasons = manager.should_trigger_evolution(**params)
        print(f"是否触发演化: {'是' if should_trigger else '否'}")
        if reasons:
            print("触发原因:")
            for reason in reasons:
                print(f"  - {reason}")
    
    if not any([args.info, args.validate, args.save, args.export, args.check_trigger, args.create_default]):
        print("演化配置管理器")
        print(f"配置版本: {manager.get_config().version}")
        print(f"启用的触发器: {[t.value for t in manager.get_config().triggers.enabled_triggers]}")
        print(f"启用的策略: {[s.value for s in manager.get_config().strategies.enabled_strategies]}")


if __name__ == "__main__":
    main()
