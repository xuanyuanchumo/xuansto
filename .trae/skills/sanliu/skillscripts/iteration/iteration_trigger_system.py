#!/usr/bin/env python3
"""
迭代触发器系统
实现定时触发、事件触发、阈值触发、手动触发机制
"""

import json
import os
import sys
import time
import threading
import subprocess
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any, Optional, Callable, Union
from dataclasses import dataclass, field, asdict
from enum import Enum
from collections import defaultdict
import logging
import queue
import signal


class TriggerType(Enum):
    SCHEDULED = "scheduled"
    EVENT = "event"
    THRESHOLD = "threshold"
    MANUAL = "manual"


class TriggerStatus(Enum):
    IDLE = "idle"
    ACTIVE = "active"
    TRIGGERED = "triggered"
    PAUSED = "paused"
    ERROR = "error"


class EventType(Enum):
    FILE_CHANGED = "file_changed"
    TEST_FAILED = "test_failed"
    BUILD_FAILED = "build_failed"
    DEPLOYMENT_FAILED = "deployment_failed"
    ERROR_THRESHOLD_REACHED = "error_threshold_reached"
    PERFORMANCE_DEGRADATION = "performance_degradation"
    SECURITY_ALERT = "security_alert"
    DEPENDENCY_UPDATE = "dependency_update"
    CODE_COMMIT = "code_commit"
    MANUAL_REQUEST = "manual_request"


class TriggerPriority(Enum):
    CRITICAL = 1
    HIGH = 2
    MEDIUM = 3
    LOW = 4


@dataclass
class TriggerEvent:
    event_id: str
    event_type: EventType
    timestamp: str
    source: str
    data: Dict[str, Any]
    processed: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "event_id": self.event_id,
            "event_type": self.event_type.value,
            "timestamp": self.timestamp,
            "source": self.source,
            "data": self.data,
            "processed": self.processed
        }


@dataclass
class TriggerConfig:
    trigger_id: str
    trigger_type: TriggerType
    enabled: bool
    config: Dict[str, Any]
    created_at: str
    last_triggered: str = ""
    trigger_count: int = 0
    priority: TriggerPriority = TriggerPriority.MEDIUM
    conditions: List[Dict[str, Any]] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "trigger_id": self.trigger_id,
            "trigger_type": self.trigger_type.value,
            "enabled": self.enabled,
            "config": self.config,
            "created_at": self.created_at,
            "last_triggered": self.last_triggered,
            "trigger_count": self.trigger_count,
            "priority": self.priority.value,
            "conditions": self.conditions,
            "dependencies": self.dependencies
        }


@dataclass
class TriggerResult:
    trigger_id: str
    triggered_at: str
    trigger_type: TriggerType
    success: bool
    message: str
    actions_taken: List[str]
    metrics: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "trigger_id": self.trigger_id,
            "triggered_at": self.triggered_at,
            "trigger_type": self.trigger_type.value,
            "success": self.success,
            "message": self.message,
            "actions_taken": self.actions_taken,
            "metrics": self.metrics
        }


class ScheduledTrigger:
    """定时触发器"""

    def __init__(self, trigger_id: str, config: Dict[str, Any]):
        self.trigger_id = trigger_id
        self.config = config
        self.logger = logging.getLogger('ScheduledTrigger')
        self.timer = None
        self.running = False

    def start(self, callback: Callable[[], None]) -> bool:
        if self.running:
            return False

        schedule_type = self.config.get("type", "interval")
        
        if schedule_type == "interval":
            interval = self.config.get("interval_seconds", 3600)
            self._schedule_interval(callback, interval)
        elif schedule_type == "daily":
            time_str = self.config.get("time", "00:00")
            self._schedule_daily(callback, time_str)
        elif schedule_type == "weekly":
            day = self.config.get("day", 0)
            time_str = self.config.get("time", "00:00")
            self._schedule_weekly(callback, day, time_str)
        else:
            self.logger.error(f"未知的调度类型: {schedule_type}")
            return False

        self.running = True
        return True

    def _schedule_interval(self, callback: Callable[[], None], interval: int):
        def run():
            while self.running:
                time.sleep(interval)
                if self.running:
                    try:
                        callback()
                    except Exception as e:
                        self.logger.error(f"定时触发回调失败: {e}")

        self.timer = threading.Thread(target=run, daemon=True)
        self.timer.start()

    def _schedule_daily(self, callback: Callable[[], None], time_str: str):
        def run():
            while self.running:
                now = datetime.now()
                target_time = datetime.strptime(time_str, "%H:%M").time()
                target_datetime = datetime.combine(now.date(), target_time)
                
                if target_datetime <= now:
                    target_datetime += timedelta(days=1)
                
                wait_seconds = (target_datetime - now).total_seconds()
                time.sleep(wait_seconds)
                
                if self.running:
                    try:
                        callback()
                    except Exception as e:
                        self.logger.error(f"定时触发回调失败: {e}")

        self.timer = threading.Thread(target=run, daemon=True)
        self.timer.start()

    def _schedule_weekly(self, callback: Callable[[], None], day: int, time_str: str):
        def run():
            while self.running:
                now = datetime.now()
                target_time = datetime.strptime(time_str, "%H:%M").time()
                target_datetime = datetime.combine(now.date(), target_time)
                
                days_ahead = (day - now.weekday()) % 7
                if days_ahead == 0 and target_datetime <= now:
                    days_ahead = 7
                
                target_datetime += timedelta(days=days_ahead)
                wait_seconds = (target_datetime - now).total_seconds()
                time.sleep(wait_seconds)
                
                if self.running:
                    try:
                        callback()
                    except Exception as e:
                        self.logger.error(f"定时触发回调失败: {e}")

        self.timer = threading.Thread(target=run, daemon=True)
        self.timer.start()

    def stop(self) -> bool:
        self.running = False
        if self.timer:
            self.timer.join(timeout=5)
        return True

    def is_running(self) -> bool:
        return self.running


class EventTrigger:
    """事件触发器"""

    def __init__(self, trigger_id: str, config: Dict[str, Any]):
        self.trigger_id = trigger_id
        self.config = config
        self.logger = logging.getLogger('EventTrigger')
        self.event_queue = queue.Queue()
        self.running = False
        self.worker_thread = None
        self.callbacks: Dict[EventType, List[Callable]] = defaultdict(list)

    def start(self) -> bool:
        if self.running:
            return False

        self.running = True
        self.worker_thread = threading.Thread(target=self._process_events, daemon=True)
        self.worker_thread.start()
        return True

    def _process_events(self):
        while self.running:
            try:
                event = self.event_queue.get(timeout=1)
                if event:
                    self._handle_event(event)
            except queue.Empty:
                continue
            except Exception as e:
                self.logger.error(f"事件处理失败: {e}")

    def _handle_event(self, event: TriggerEvent):
        event_type = event.event_type
        
        if self._should_trigger(event):
            callbacks = self.callbacks.get(event_type, [])
            for callback in callbacks:
                try:
                    callback(event)
                except Exception as e:
                    self.logger.error(f"事件回调失败: {e}")

        event.processed = True

    def _should_trigger(self, event: TriggerEvent) -> bool:
        watch_events = self.config.get("watch_events", [])
        return event.event_type.value in watch_events

    def register_callback(self, event_type: EventType, callback: Callable):
        self.callbacks[event_type].append(callback)

    def emit_event(self, event: TriggerEvent):
        self.event_queue.put(event)

    def stop(self) -> bool:
        self.running = False
        if self.worker_thread:
            self.worker_thread.join(timeout=5)
        return True

    def is_running(self) -> bool:
        return self.running


class ThresholdTrigger:
    """阈值触发器"""

    def __init__(self, trigger_id: str, config: Dict[str, Any]):
        self.trigger_id = trigger_id
        self.config = config
        self.logger = logging.getLogger('ThresholdTrigger')
        self.metrics: Dict[str, List[float]] = defaultdict(list)
        self.running = False
        self.check_thread = None

    def start(self, callback: Callable[[Dict[str, Any]], None]) -> bool:
        if self.running:
            return False

        self.callback = callback
        self.running = True
        self.check_thread = threading.Thread(target=self._check_thresholds, daemon=True)
        self.check_thread.start()
        return True

    def _check_thresholds(self):
        check_interval = self.config.get("check_interval", 60)
        
        while self.running:
            try:
                current_metrics = self._collect_metrics()
                
                for metric_name, value in current_metrics.items():
                    self.metrics[metric_name].append(value)
                    
                    if len(self.metrics[metric_name]) > 100:
                        self.metrics[metric_name] = self.metrics[metric_name][-100:]

                triggered_metrics = self._evaluate_thresholds(current_metrics)
                
                if triggered_metrics:
                    self.callback(triggered_metrics)

                time.sleep(check_interval)

            except Exception as e:
                self.logger.error(f"阈值检查失败: {e}")
                time.sleep(check_interval)

    def _collect_metrics(self) -> Dict[str, float]:
        metrics = {}

        if self.config.get("monitor_error_rate", False):
            metrics["error_rate"] = self._get_error_rate()

        if self.config.get("monitor_performance", False):
            metrics["response_time"] = self._get_response_time()

        if self.config.get("monitor_memory", False):
            metrics["memory_usage"] = self._get_memory_usage()

        if self.config.get("monitor_cpu", False):
            metrics["cpu_usage"] = self._get_cpu_usage()

        return metrics

    def _get_error_rate(self) -> float:
        return 0.0

    def _get_response_time(self) -> float:
        return 100.0

    def _get_memory_usage(self) -> float:
        try:
            import psutil
            return psutil.virtual_memory().percent
        except Exception:
            return 0.0

    def _get_cpu_usage(self) -> float:
        try:
            import psutil
            return psutil.cpu_percent(interval=1)
        except Exception:
            return 0.0

    def _evaluate_thresholds(self, metrics: Dict[str, float]) -> Dict[str, Any]:
        triggered = {}
        thresholds = self.config.get("thresholds", {})

        for metric_name, value in metrics.items():
            if metric_name in thresholds:
                threshold_config = thresholds[metric_name]
                operator = threshold_config.get("operator", ">")
                threshold_value = threshold_config.get("value", 0)

                if operator == ">" and value > threshold_value:
                    triggered[metric_name] = {
                        "value": value,
                        "threshold": threshold_value,
                        "operator": operator
                    }
                elif operator == "<" and value < threshold_value:
                    triggered[metric_name] = {
                        "value": value,
                        "threshold": threshold_value,
                        "operator": operator
                    }
                elif operator == ">=" and value >= threshold_value:
                    triggered[metric_name] = {
                        "value": value,
                        "threshold": threshold_value,
                        "operator": operator
                    }
                elif operator == "<=" and value <= threshold_value:
                    triggered[metric_name] = {
                        "value": value,
                        "threshold": threshold_value,
                        "operator": operator
                    }

        return triggered

    def update_metric(self, metric_name: str, value: float):
        self.metrics[metric_name].append(value)

    def stop(self) -> bool:
        self.running = False
        if self.check_thread:
            self.check_thread.join(timeout=5)
        return True

    def is_running(self) -> bool:
        return self.running


class ManualTrigger:
    """手动触发器"""

    def __init__(self, trigger_id: str, config: Dict[str, Any]):
        self.trigger_id = trigger_id
        self.config = config
        self.logger = logging.getLogger('ManualTrigger')
        self.trigger_count = 0

    def trigger(self, callback: Callable[[], None], params: Optional[Dict[str, Any]] = None) -> bool:
        try:
            self.logger.info(f"手动触发: {self.trigger_id}")
            self.trigger_count += 1
            
            if params:
                self.logger.info(f"触发参数: {params}")
            
            callback()
            return True
        except Exception as e:
            self.logger.error(f"手动触发失败: {e}")
            return False

    def is_running(self) -> bool:
        return True


class IterationTriggerSystem:
    """迭代触发器系统"""

    def __init__(self, project_root: str):
        self.project_root = Path(project_root).resolve()
        self.logger = self._setup_logger()

        self.triggers: Dict[str, Union[ScheduledTrigger, EventTrigger, ThresholdTrigger, ManualTrigger]] = {}
        self.trigger_configs: Dict[str, TriggerConfig] = {}
        self.trigger_results: List[TriggerResult] = []

        self.config_file = self.project_root / ".trigger_configs.json"
        self.results_file = self.project_root / ".trigger_results.json"

        self.status = TriggerStatus.IDLE
        self.iteration_callback: Optional[Callable] = None

        self._load_configs()
        self._load_results()

    def _setup_logger(self) -> logging.Logger:
        logger = logging.getLogger('IterationTriggerSystem')
        logger.setLevel(logging.INFO)

        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            logger.addHandler(handler)

        return logger

    def _load_configs(self):
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    configs = json.load(f)
                    for config_data in configs:
                        config = TriggerConfig(
                            trigger_id=config_data["trigger_id"],
                            trigger_type=TriggerType(config_data["trigger_type"]),
                            enabled=config_data["enabled"],
                            config=config_data["config"],
                            created_at=config_data["created_at"],
                            last_triggered=config_data.get("last_triggered", ""),
                            trigger_count=config_data.get("trigger_count", 0)
                        )
                        self.trigger_configs[config.trigger_id] = config
            except Exception as e:
                self.logger.error(f"加载触发器配置失败: {e}")

    def _save_configs(self):
        configs = [config.to_dict() for config in self.trigger_configs.values()]
        with open(self.config_file, 'w', encoding='utf-8') as f:
            json.dump(configs, f, indent=2, ensure_ascii=False)

    def _load_results(self):
        if self.results_file.exists():
            try:
                with open(self.results_file, 'r', encoding='utf-8') as f:
                    results = json.load(f)
                    self.trigger_results = [TriggerResult(**r) for r in results]
            except Exception as e:
                self.logger.error(f"加载触发器结果失败: {e}")

    def _save_results(self):
        results = [result.to_dict() for result in self.trigger_results[-100:]]
        with open(self.results_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)

    def set_iteration_callback(self, callback: Callable):
        self.iteration_callback = callback

    def register_trigger(self, trigger_type: TriggerType, config: Dict[str, Any], enabled: bool = True) -> str:
        trigger_id = f"TRIGGER-{datetime.now().strftime('%Y%m%d%H%M%S')}-{len(self.triggers):04d}"

        trigger_config = TriggerConfig(
            trigger_id=trigger_id,
            trigger_type=trigger_type,
            enabled=enabled,
            config=config,
            created_at=datetime.now().isoformat()
        )

        self.trigger_configs[trigger_id] = trigger_config

        if trigger_type == TriggerType.SCHEDULED:
            trigger = ScheduledTrigger(trigger_id, config)
        elif trigger_type == TriggerType.EVENT:
            trigger = EventTrigger(trigger_id, config)
        elif trigger_type == TriggerType.THRESHOLD:
            trigger = ThresholdTrigger(trigger_id, config)
        elif trigger_type == TriggerType.MANUAL:
            trigger = ManualTrigger(trigger_id, config)
        else:
            raise ValueError(f"未知的触发器类型: {trigger_type}")

        self.triggers[trigger_id] = trigger
        self._save_configs()

        self.logger.info(f"注册触发器: {trigger_id} (类型: {trigger_type.value})")
        return trigger_id

    def start_trigger(self, trigger_id: str) -> bool:
        if trigger_id not in self.triggers:
            self.logger.error(f"触发器不存在: {trigger_id}")
            return False

        trigger = self.triggers[trigger_id]
        config = self.trigger_configs[trigger_id]

        if not config.enabled:
            self.logger.warning(f"触发器已禁用: {trigger_id}")
            return False

        def on_trigger():
            self._execute_iteration(trigger_id)

        if isinstance(trigger, ScheduledTrigger):
            return trigger.start(on_trigger)
        elif isinstance(trigger, EventTrigger):
            trigger.register_callback(EventType.MANUAL_REQUEST, lambda e: on_trigger())
            return trigger.start()
        elif isinstance(trigger, ThresholdTrigger):
            return trigger.start(lambda m: self._on_threshold_reached(trigger_id, m))
        elif isinstance(trigger, ManualTrigger):
            return True

        return False

    def _execute_iteration(self, trigger_id: str):
        self.logger.info(f"触发迭代: {trigger_id}")

        actions_taken = []
        success = False
        message = ""

        try:
            if self.iteration_callback:
                self.iteration_callback()
                actions_taken.append("执行迭代回调")
                success = True
                message = "迭代执行成功"
            else:
                message = "未设置迭代回调"

            if trigger_id in self.trigger_configs:
                self.trigger_configs[trigger_id].last_triggered = datetime.now().isoformat()
                self.trigger_configs[trigger_id].trigger_count += 1
                self._save_configs()

        except Exception as e:
            message = f"迭代执行失败: {str(e)}"
            self.logger.error(message)

        result = TriggerResult(
            trigger_id=trigger_id,
            triggered_at=datetime.now().isoformat(),
            trigger_type=self.trigger_configs[trigger_id].trigger_type,
            success=success,
            message=message,
            actions_taken=actions_taken,
            metrics={}
        )

        self.trigger_results.append(result)
        self._save_results()

    def _on_threshold_reached(self, trigger_id: str, metrics: Dict[str, Any]):
        self.logger.info(f"阈值触发: {trigger_id}, 指标: {metrics}")
        self._execute_iteration(trigger_id)

    def manual_trigger(self, trigger_id: str, params: Optional[Dict[str, Any]] = None) -> bool:
        if trigger_id not in self.triggers:
            self.logger.error(f"触发器不存在: {trigger_id}")
            return False

        trigger = self.triggers[trigger_id]

        if isinstance(trigger, ManualTrigger):
            return trigger.trigger(lambda: self._execute_iteration(trigger_id), params)
        else:
            self._execute_iteration(trigger_id)
            return True

    def stop_trigger(self, trigger_id: str) -> bool:
        if trigger_id not in self.triggers:
            return False

        trigger = self.triggers[trigger_id]
        
        if hasattr(trigger, 'stop'):
            return trigger.stop()
        
        return True

    def start_all(self) -> Dict[str, bool]:
        results = {}
        for trigger_id in self.triggers:
            results[trigger_id] = self.start_trigger(trigger_id)
        return results

    def stop_all(self) -> Dict[str, bool]:
        results = {}
        for trigger_id in self.triggers:
            results[trigger_id] = self.stop_trigger(trigger_id)
        return results

    def get_trigger_status(self, trigger_id: str) -> Optional[Dict[str, Any]]:
        if trigger_id not in self.triggers:
            return None

        trigger = self.triggers[trigger_id]
        config = self.trigger_configs[trigger_id]

        return {
            "trigger_id": trigger_id,
            "type": config.trigger_type.value,
            "enabled": config.enabled,
            "running": trigger.is_running() if hasattr(trigger, 'is_running') else False,
            "trigger_count": config.trigger_count,
            "last_triggered": config.last_triggered
        }

    def get_all_status(self) -> List[Dict[str, Any]]:
        return [self.get_trigger_status(tid) for tid in self.triggers]

    def emit_event(self, event_type: EventType, source: str, data: Dict[str, Any]):
        event = TriggerEvent(
            event_id=f"EVENT-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            event_type=event_type,
            timestamp=datetime.now().isoformat(),
            source=source,
            data=data
        )

        for trigger in self.triggers.values():
            if isinstance(trigger, EventTrigger):
                trigger.emit_event(event)

    def generate_report(self, output_path: Optional[str] = None) -> str:
        lines = [
            "# 迭代触发器系统报告",
            f"\n生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"\n## 触发器状态",
            f"\n总触发器数: {len(self.triggers)}",
        ]

        for trigger_id, config in self.trigger_configs.items():
            status = self.get_trigger_status(trigger_id)
            lines.extend([
                f"\n### {trigger_id}",
                f"- 类型: {config.trigger_type.value}",
                f"- 状态: {'运行中' if status and status.get('running') else '已停止'}",
                f"- 触发次数: {config.trigger_count}",
                f"- 最后触发: {config.last_triggered or '从未触发'}",
            ])

        if self.trigger_results:
            lines.extend([
                f"\n## 最近触发结果",
                "| 触发器ID | 时间 | 类型 | 成功 | 消息 |",
                "|----------|------|------|------|------|",
            ])

            for result in self.trigger_results[-10:]:
                lines.append(
                    f"| {result.trigger_id} | {result.triggered_at[:19]} | "
                    f"{result.trigger_type.value} | {'是' if result.success else '否'} | {result.message[:30]} |"
                )

        report = '\n'.join(lines)

        if output_path:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(report)

        return report

    def create_composite_trigger(
        self,
        trigger_configs: List[Dict[str, Any]],
        logic: str = "AND",
        priority: TriggerPriority = TriggerPriority.MEDIUM
    ) -> str:
        """
        创建组合触发器
        """
        composite_id = f"COMPOSITE-{datetime.now().strftime('%Y%m%d%H%M%S')}"

        composite_config = {
            "type": "composite",
            "logic": logic,
            "sub_triggers": []
        }

        for config in trigger_configs:
            trigger_id = self.register_trigger(
                trigger_type=TriggerType(config.get("type", "manual")),
                config=config.get("config", {}),
                enabled=config.get("enabled", True)
            )
            composite_config["sub_triggers"].append(trigger_id)

        composite_trigger_config = TriggerConfig(
            trigger_id=composite_id,
            trigger_type=TriggerType.MANUAL,
            enabled=True,
            config=composite_config,
            created_at=datetime.now().isoformat(),
            priority=priority,
            conditions=[{"type": "composite", "logic": logic}]
        )

        self.trigger_configs[composite_id] = composite_trigger_config
        self._save_configs()

        self.logger.info(f"创建组合触发器: {composite_id}")
        return composite_id

    def create_trigger_chain(
        self,
        trigger_sequence: List[Dict[str, Any]]
    ) -> str:
        """
        创建触发器链
        """
        chain_id = f"CHAIN-{datetime.now().strftime('%Y%m%d%H%M%S')}"

        chain_config = {
            "type": "chain",
            "triggers": []
        }

        for i, config in enumerate(trigger_sequence):
            trigger_id = self.register_trigger(
                trigger_type=TriggerType(config.get("type", "manual")),
                config=config.get("config", {}),
                enabled=config.get("enabled", True)
            )

            chain_config["triggers"].append({
                "trigger_id": trigger_id,
                "order": i,
                "delay": config.get("delay", 0)
            })

        chain_trigger_config = TriggerConfig(
            trigger_id=chain_id,
            trigger_type=TriggerType.MANUAL,
            enabled=True,
            config=chain_config,
            created_at=datetime.now().isoformat(),
            priority=TriggerPriority.HIGH,
            dependencies=[t["trigger_id"] for t in chain_config["triggers"]]
        )

        self.trigger_configs[chain_id] = chain_trigger_config
        self._save_configs()

        self.logger.info(f"创建触发器链: {chain_id}")
        return chain_id

    def analyze_trigger_history(self) -> Dict[str, Any]:
        """
        分析触发器历史
        """
        analysis = {
            "total_triggers": len(self.trigger_results),
            "success_rate": 0.0,
            "trigger_frequency": {},
            "performance_metrics": {},
            "recommendations": []
        }

        if not self.trigger_results:
            return analysis

        successful_triggers = sum(1 for r in self.trigger_results if r.success)
        analysis["success_rate"] = successful_triggers / len(self.trigger_results)

        trigger_counts = defaultdict(int)
        for result in self.trigger_results:
            trigger_counts[result.trigger_id] += 1

        analysis["trigger_frequency"] = dict(trigger_counts)

        if len(self.trigger_results) >= 10:
            recent_results = self.trigger_results[-10:]
            recent_success = sum(1 for r in recent_results if r.success)
            recent_rate = recent_success / len(recent_results)

            analysis["performance_metrics"]["recent_success_rate"] = recent_rate

            if recent_rate < 0.5:
                analysis["recommendations"].append(
                    "最近触发成功率较低，建议检查触发器配置或迭代回调"
                )

        most_frequent = max(trigger_counts.items(), key=lambda x: x[1])
        analysis["most_frequent_trigger"] = {
            "trigger_id": most_frequent[0],
            "count": most_frequent[1]
        }

        return analysis

    def recommend_triggers(self, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        智能推荐触发器
        """
        recommendations = []

        if context.get("has_tests", False):
            recommendations.append({
                "type": "event",
                "config": {
                    "watch_events": ["test_failed"]
                },
                "reason": "项目包含测试，建议添加测试失败触发器"
            })

        if context.get("has_deployment", False):
            recommendations.append({
                "type": "event",
                "config": {
                    "watch_events": ["deployment_failed"]
                },
                "reason": "项目有部署流程，建议添加部署失败触发器"
            })

        if context.get("needs_regular_check", False):
            recommendations.append({
                "type": "scheduled",
                "config": {
                    "type": "interval",
                    "interval_seconds": 3600
                },
                "reason": "建议添加定期检查触发器"
            })

        if context.get("performance_critical", False):
            recommendations.append({
                "type": "threshold",
                "config": {
                    "monitor_performance": True,
                    "thresholds": {
                        "response_time": {
                            "operator": ">",
                            "value": 1000
                        }
                    }
                },
                "reason": "性能敏感项目，建议添加性能阈值触发器"
            })

        return recommendations

    def prioritize_triggers(self) -> List[str]:
        """
        按优先级排序触发器
        """
        triggers_with_priority = [
            (trigger_id, config.priority)
            for trigger_id, config in self.trigger_configs.items()
        ]

        sorted_triggers = sorted(
            triggers_with_priority,
            key=lambda x: x[1].value
        )

        return [trigger_id for trigger_id, _ in sorted_triggers]

    def check_trigger_conditions(self, trigger_id: str, context: Dict[str, Any]) -> bool:
        """
        检查触发器条件
        """
        if trigger_id not in self.trigger_configs:
            return False

        config = self.trigger_configs[trigger_id]

        if not config.conditions:
            return True

        for condition in config.conditions:
            condition_type = condition.get("type")

            if condition_type == "time_window":
                start_hour = condition.get("start_hour", 0)
                end_hour = condition.get("end_hour", 23)
                current_hour = datetime.now().hour

                if not (start_hour <= current_hour <= end_hour):
                    return False

            elif condition_type == "day_of_week":
                allowed_days = condition.get("days", [0, 1, 2, 3, 4, 5, 6])
                current_day = datetime.now().weekday()

                if current_day not in allowed_days:
                    return False

            elif condition_type == "custom":
                condition_func = condition.get("function")
                if condition_func and not condition_func(context):
                    return False

        return True

    def get_trigger_dependencies(self, trigger_id: str) -> List[str]:
        """
        获取触发器依赖
        """
        if trigger_id not in self.trigger_configs:
            return []

        return self.trigger_configs[trigger_id].dependencies

    def validate_trigger_chain(self, chain_id: str) -> Dict[str, Any]:
        """
        验证触发器链
        """
        validation_result = {
            "chain_id": chain_id,
            "valid": True,
            "issues": [],
            "warnings": []
        }

        if chain_id not in self.trigger_configs:
            validation_result["valid"] = False
            validation_result["issues"].append("触发器链不存在")
            return validation_result

        config = self.trigger_configs[chain_id]
        chain_triggers = config.config.get("triggers", [])

        for trigger_info in chain_triggers:
            trigger_id = trigger_info.get("trigger_id")

            if trigger_id not in self.triggers:
                validation_result["valid"] = False
                validation_result["issues"].append(f"触发器 {trigger_id} 不存在")

            if not self.trigger_configs[trigger_id].enabled:
                validation_result["warnings"].append(f"触发器 {trigger_id} 已禁用")

        if len(chain_triggers) == 0:
            validation_result["valid"] = False
            validation_result["issues"].append("触发器链为空")

        return validation_result


def main():
    import argparse

    parser = argparse.ArgumentParser(description='迭代触发器系统')
    parser.add_argument('--project-root', default='.', help='项目根目录')

    subparsers = parser.add_subparsers(dest='command', help='可用命令')

    register_parser = subparsers.add_parser('register', help='注册触发器')
    register_parser.add_argument('--type', required=True, choices=['scheduled', 'event', 'threshold', 'manual'], help='触发器类型')
    register_parser.add_argument('--config', type=str, help='配置JSON')

    status_parser = subparsers.add_parser('status', help='查看状态')
    status_parser.add_argument('--trigger-id', help='触发器ID')

    trigger_parser = subparsers.add_parser('trigger', help='手动触发')
    trigger_parser.add_argument('--trigger-id', required=True, help='触发器ID')
    trigger_parser.add_argument('--params', type=str, help='参数JSON')

    report_parser = subparsers.add_parser('report', help='生成报告')
    report_parser.add_argument('--output', help='输出路径')

    args = parser.parse_args()

    system = IterationTriggerSystem(args.project_root)

    if args.command == 'register':
        config = json.loads(args.config) if args.config else {}
        trigger_type = TriggerType(args.type)
        trigger_id = system.register_trigger(trigger_type, config)
        print(f"触发器已注册: {trigger_id}")

    elif args.command == 'status':
        if args.trigger_id:
            status = system.get_trigger_status(args.trigger_id)
            if status:
                print(json.dumps(status, indent=2, ensure_ascii=False))
            else:
                print(f"触发器不存在: {args.trigger_id}")
        else:
            statuses = system.get_all_status()
            print(json.dumps(statuses, indent=2, ensure_ascii=False))

    elif args.command == 'trigger':
        params = json.loads(args.params) if args.params else None
        success = system.manual_trigger(args.trigger_id, params)
        print(f"手动触发{'成功' if success else '失败'}")

    elif args.command == 'report':
        report = system.generate_report(args.output)
        if args.output:
            print(f"报告已生成: {args.output}")
        else:
            print(report)

    else:
        parser.print_help()


if __name__ == '__main__':
    main()
