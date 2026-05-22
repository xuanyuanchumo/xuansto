#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
演化告警系统 - Evolution Alert System

三省六部技能系统的演化告警系统，实现告警规则引擎、通知机制和处理追踪。

核心功能:
- 告警规则引擎（定义告警规则、评估告警条件）
- 告警通知机制（支持多种通知渠道：日志、WebSocket、邮件等）
- 告警处理追踪（告警确认、解决、历史记录）

告警类型:
- ERROR_RATE_HIGH: 错误率超过阈值
- PERFORMANCE_DEGRADED: 性能退化
- FIX_FAILED: 修复失败
- LEARNING_STALLED: 学习停滞
- EVOLUTION_CYCLE_TIMEOUT: 演化周期超时

告警级别:
- INFO: 信息性告警
- WARNING: 警告
- ERROR: 错误
- CRITICAL: 严重

使用示例:
    from evolution_alert import EvolutionAlertSystem
    
    alert_system = EvolutionAlertSystem()
    alert_system.start()
    
    # 触发告警
    alert = alert_system.create_alert(
        alert_type=AlertType.ERROR_RATE_HIGH,
        severity=AlertSeverity.ERROR,
        message="错误率达到15%",
        context={"error_rate": 0.15, "threshold": 0.10}
    )
    
    # 确认告警
    alert_system.acknowledge_alert(alert.alert_id, "operator_001")
    
    # 解决告警
    alert_system.resolve_alert(alert.alert_id, "已修复问题")
"""

import asyncio
import json
import logging
import os
import smtplib
import threading
import time
import uuid
from abc import ABC, abstractmethod
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from enum import Enum, auto
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set, Tuple, Union
import queue


class AlertType(Enum):
    """告警类型枚举"""
    ERROR_RATE_HIGH = "error_rate_high"
    PERFORMANCE_DEGRADED = "performance_degraded"
    FIX_FAILED = "fix_failed"
    LEARNING_STALLED = "learning_stalled"
    EVOLUTION_CYCLE_TIMEOUT = "evolution_cycle_timeout"
    RESOURCE_EXHAUSTED = "resource_exhausted"
    DEPENDENCY_FAILURE = "dependency_failure"
    CONFIGURATION_ERROR = "configuration_error"
    SECURITY_VIOLATION = "security_violation"
    CUSTOM = "custom"


class AlertSeverity(Enum):
    """告警级别枚举"""
    INFO = auto()
    WARNING = auto()
    ERROR = auto()
    CRITICAL = auto()


class AlertStatus(Enum):
    """告警状态枚举"""
    ACTIVE = "active"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"
    SUPPRESSED = "suppressed"
    EXPIRED = "expired"


class NotificationChannel(Enum):
    """通知渠道枚举"""
    LOG = "log"
    WEBSOCKET = "websocket"
    EMAIL = "email"
    WEBHOOK = "webhook"
    SLACK = "slack"
    DINGTALK = "dingtalk"
    CONSOLE = "console"


class RuleOperator(Enum):
    """规则操作符枚举"""
    GREATER_THAN = "gt"
    LESS_THAN = "lt"
    GREATER_EQUAL = "ge"
    LESS_EQUAL = "le"
    EQUAL = "eq"
    NOT_EQUAL = "ne"
    CONTAINS = "contains"
    NOT_CONTAINS = "not_contains"
    IN = "in"
    NOT_IN = "not_in"


@dataclass
class AlertContext:
    """告警上下文数据类"""
    source: str
    component: str
    metric_name: Optional[str] = None
    metric_value: Optional[float] = None
    threshold: Optional[float] = None
    tags: Dict[str, str] = field(default_factory=dict)
    additional_data: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "source": self.source,
            "component": self.component,
            "metric_name": self.metric_name,
            "metric_value": self.metric_value,
            "threshold": self.threshold,
            "tags": self.tags,
            "additional_data": self.additional_data
        }


@dataclass
class Alert:
    """告警数据类"""
    alert_id: str
    alert_type: AlertType
    severity: AlertSeverity
    status: AlertStatus
    message: str
    context: AlertContext
    created_at: datetime
    updated_at: datetime
    rule_id: Optional[str] = None
    acknowledged_by: Optional[str] = None
    acknowledged_at: Optional[datetime] = None
    resolved_by: Optional[str] = None
    resolved_at: Optional[datetime] = None
    resolution_note: Optional[str] = None
    notification_sent: bool = False
    notification_channels: List[NotificationChannel] = field(default_factory=list)
    suppression_until: Optional[datetime] = None
    related_alerts: List[str] = field(default_factory=list)
    history: List[Dict[str, Any]] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "alert_id": self.alert_id,
            "alert_type": self.alert_type.value,
            "severity": self.severity.name,
            "status": self.status.value,
            "message": self.message,
            "context": self.context.to_dict(),
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "rule_id": self.rule_id,
            "acknowledged_by": self.acknowledged_by,
            "acknowledged_at": self.acknowledged_at.isoformat() if self.acknowledged_at else None,
            "resolved_by": self.resolved_by,
            "resolved_at": self.resolved_at.isoformat() if self.resolved_at else None,
            "resolution_note": self.resolution_note,
            "notification_sent": self.notification_sent,
            "notification_channels": [c.value for c in self.notification_channels],
            "suppression_until": self.suppression_until.isoformat() if self.suppression_until else None,
            "related_alerts": self.related_alerts,
            "history": self.history
        }
    
    def add_history_entry(self, action: str, details: Dict[str, Any]) -> None:
        self.history.append({
            "timestamp": datetime.now().isoformat(),
            "action": action,
            "details": details
        })


@dataclass
class AlertRule:
    """告警规则数据类"""
    rule_id: str
    name: str
    description: str
    alert_type: AlertType
    severity: AlertSeverity
    enabled: bool
    conditions: List[Dict[str, Any]]
    actions: List[Dict[str, Any]]
    notification_channels: List[NotificationChannel]
    cooldown_seconds: int = 300
    max_alerts_per_hour: int = 10
    auto_resolve: bool = False
    auto_resolve_after_seconds: int = 3600
    tags: Dict[str, str] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "rule_id": self.rule_id,
            "name": self.name,
            "description": self.description,
            "alert_type": self.alert_type.value,
            "severity": self.severity.name,
            "enabled": self.enabled,
            "conditions": self.conditions,
            "actions": self.actions,
            "notification_channels": [c.value for c in self.notification_channels],
            "cooldown_seconds": self.cooldown_seconds,
            "max_alerts_per_hour": self.max_alerts_per_hour,
            "auto_resolve": self.auto_resolve,
            "auto_resolve_after_seconds": self.auto_resolve_after_seconds,
            "tags": self.tags,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }


@dataclass
class NotificationConfig:
    """通知配置数据类"""
    channel: NotificationChannel
    enabled: bool
    config: Dict[str, Any] = field(default_factory=dict)
    min_severity: AlertSeverity = AlertSeverity.INFO
    rate_limit_per_minute: int = 60
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "channel": self.channel.value,
            "enabled": self.enabled,
            "config": self.config,
            "min_severity": self.min_severity.name,
            "rate_limit_per_minute": self.rate_limit_per_minute
        }


class INotifier(ABC):
    """通知器接口"""
    
    @abstractmethod
    def send(self, alert: Alert, config: Dict[str, Any]) -> bool:
        pass
    
    @abstractmethod
    def get_channel(self) -> NotificationChannel:
        pass


class LogNotifier(INotifier):
    """日志通知器"""
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        self.logger = logger or logging.getLogger('EvolutionAlertSystem')
    
    def get_channel(self) -> NotificationChannel:
        return NotificationChannel.LOG
    
    def send(self, alert: Alert, config: Dict[str, Any]) -> bool:
        try:
            log_level = {
                AlertSeverity.INFO: logging.INFO,
                AlertSeverity.WARNING: logging.WARNING,
                AlertSeverity.ERROR: logging.ERROR,
                AlertSeverity.CRITICAL: logging.CRITICAL
            }.get(alert.severity, logging.INFO)
            
            self.logger.log(
                log_level,
                f"[ALERT] [{alert.severity.name}] {alert.alert_type.value}: {alert.message}"
            )
            return True
        except Exception as e:
            self.logger.error(f"日志通知发送失败: {e}")
            return False


class ConsoleNotifier(INotifier):
    """控制台通知器"""
    
    def get_channel(self) -> NotificationChannel:
        return NotificationChannel.CONSOLE
    
    def send(self, alert: Alert, config: Dict[str, Any]) -> bool:
        try:
            severity_colors = {
                AlertSeverity.INFO: "\033[94m",
                AlertSeverity.WARNING: "\033[93m",
                AlertSeverity.ERROR: "\033[91m",
                AlertSeverity.CRITICAL: "\033[95m"
            }
            reset_color = "\033[0m"
            
            color = severity_colors.get(alert.severity, "")
            print(f"{color}[{alert.severity.name}] {alert.alert_type.value}: {alert.message}{reset_color}")
            print(f"  告警ID: {alert.alert_id}")
            print(f"  时间: {alert.created_at.strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"  来源: {alert.context.source}/{alert.context.component}")
            return True
        except Exception:
            return False


class EmailNotifier(INotifier):
    """邮件通知器"""
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        self.logger = logger or logging.getLogger('EvolutionAlertSystem')
    
    def get_channel(self) -> NotificationChannel:
        return NotificationChannel.EMAIL
    
    def send(self, alert: Alert, config: Dict[str, Any]) -> bool:
        try:
            smtp_host = config.get("smtp_host", "localhost")
            smtp_port = config.get("smtp_port", 25)
            smtp_user = config.get("smtp_user")
            smtp_password = config.get("smtp_password")
            use_tls = config.get("use_tls", True)
            
            from_addr = config.get("from_addr", "alerts@example.com")
            to_addrs = config.get("to_addrs", [])
            
            if not to_addrs:
                return False
            
            msg = MIMEMultipart("alternative")
            msg["Subject"] = f"[{alert.severity.name}] {alert.alert_type.value}: {alert.message[:50]}"
            msg["From"] = from_addr
            msg["To"] = ", ".join(to_addrs)
            
            text_content = f"""
告警通知

告警ID: {alert.alert_id}
类型: {alert.alert_type.value}
级别: {alert.severity.name}
状态: {alert.status.value}

消息: {alert.message}

来源: {alert.context.source}
组件: {alert.context.component}

创建时间: {alert.created_at.strftime('%Y-%m-%d %H:%M:%S')}

上下文信息:
{json.dumps(alert.context.to_dict(), indent=2, ensure_ascii=False)}
"""
            
            html_content = f"""
<html>
<head>
    <style>
        body {{ font-family: Arial, sans-serif; }}
        .alert {{ padding: 20px; border-radius: 5px; }}
        .critical {{ background-color: #fce4ec; border-left: 5px solid #c62828; }}
        .error {{ background-color: #fff3e0; border-left: 5px solid #ef6c00; }}
        .warning {{ background-color: #fffde7; border-left: 5px solid #fbc02d; }}
        .info {{ background-color: #e3f2fd; border-left: 5px solid #1976d2; }}
    </style>
</head>
<body>
    <div class="alert {alert.severity.name.lower()}">
        <h2>告警通知</h2>
        <p><strong>告警ID:</strong> {alert.alert_id}</p>
        <p><strong>类型:</strong> {alert.alert_type.value}</p>
        <p><strong>级别:</strong> {alert.severity.name}</p>
        <p><strong>状态:</strong> {alert.status.value}</p>
        <p><strong>消息:</strong> {alert.message}</p>
        <p><strong>来源:</strong> {alert.context.source}</p>
        <p><strong>组件:</strong> {alert.context.component}</p>
        <p><strong>创建时间:</strong> {alert.created_at.strftime('%Y-%m-%d %H:%M:%S')}</p>
    </div>
</body>
</html>
"""
            
            msg.attach(MIMEText(text_content, "plain"))
            msg.attach(MIMEText(html_content, "html"))
            
            with smtplib.SMTP(smtp_host, smtp_port) as server:
                if use_tls:
                    server.starttls()
                if smtp_user and smtp_password:
                    server.login(smtp_user, smtp_password)
                server.sendmail(from_addr, to_addrs, msg.as_string())
            
            self.logger.info(f"邮件通知已发送: {alert.alert_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"邮件通知发送失败: {e}")
            return False


class WebhookNotifier(INotifier):
    """Webhook通知器"""
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        self.logger = logger or logging.getLogger('EvolutionAlertSystem')
    
    def get_channel(self) -> NotificationChannel:
        return NotificationChannel.WEBHOOK
    
    def send(self, alert: Alert, config: Dict[str, Any]) -> bool:
        try:
            import urllib.request
            import urllib.error
            
            url = config.get("url")
            if not url:
                return False
            
            headers = config.get("headers", {"Content-Type": "application/json"})
            timeout = config.get("timeout", 10)
            
            payload = json.dumps(alert.to_dict(), ensure_ascii=False).encode('utf-8')
            
            req = urllib.request.Request(
                url,
                data=payload,
                headers=headers,
                method='POST'
            )
            
            with urllib.request.urlopen(req, timeout=timeout) as response:
                if response.status >= 200 and response.status < 300:
                    self.logger.info(f"Webhook通知已发送: {alert.alert_id}")
                    return True
                else:
                    self.logger.warning(f"Webhook返回非成功状态: {response.status}")
                    return False
                    
        except Exception as e:
            self.logger.error(f"Webhook通知发送失败: {e}")
            return False


class WebSocketNotifier(INotifier):
    """WebSocket通知器"""
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        self.logger = logger or logging.getLogger('EvolutionAlertSystem')
        self._connections: Dict[str, Any] = {}
    
    def get_channel(self) -> NotificationChannel:
        return NotificationChannel.WEBSOCKET
    
    def register_connection(self, connection_id: str, connection: Any) -> None:
        self._connections[connection_id] = connection
    
    def unregister_connection(self, connection_id: str) -> None:
        self._connections.pop(connection_id, None)
    
    def send(self, alert: Alert, config: Dict[str, Any]) -> bool:
        try:
            message = json.dumps({
                "type": "alert",
                "data": alert.to_dict()
            }, ensure_ascii=False)
            
            sent_count = 0
            for conn_id, conn in self._connections.items():
                try:
                    if hasattr(conn, 'send'):
                        conn.send(message)
                        sent_count += 1
                except Exception:
                    pass
            
            self.logger.info(f"WebSocket通知已发送到 {sent_count} 个连接")
            return sent_count > 0
            
        except Exception as e:
            self.logger.error(f"WebSocket通知发送失败: {e}")
            return False


class AlertRuleEngine:
    """告警规则引擎"""
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        self.logger = logger or logging.getLogger('EvolutionAlertSystem')
        self._rules: Dict[str, AlertRule] = {}
        self._rule_evaluators: Dict[str, Callable] = {}
        self._alert_counters: Dict[str, List[datetime]] = defaultdict(list)
        self._last_alert_times: Dict[str, datetime] = {}
    
    def add_rule(self, rule: AlertRule) -> bool:
        if rule.rule_id in self._rules:
            self.logger.warning(f"规则已存在: {rule.rule_id}")
            return False
        
        self._rules[rule.rule_id] = rule
        self.logger.info(f"添加告警规则: {rule.name} ({rule.rule_id})")
        return True
    
    def remove_rule(self, rule_id: str) -> bool:
        if rule_id not in self._rules:
            return False
        
        del self._rules[rule_id]
        self.logger.info(f"移除告警规则: {rule_id}")
        return True
    
    def update_rule(self, rule: AlertRule) -> bool:
        if rule.rule_id not in self._rules:
            return False
        
        rule.updated_at = datetime.now()
        self._rules[rule.rule_id] = rule
        self.logger.info(f"更新告警规则: {rule.name}")
        return True
    
    def get_rule(self, rule_id: str) -> Optional[AlertRule]:
        return self._rules.get(rule_id)
    
    def get_all_rules(self) -> List[AlertRule]:
        return list(self._rules.values())
    
    def register_evaluator(self, rule_id: str, evaluator: Callable) -> None:
        self._rule_evaluators[rule_id] = evaluator
    
    def evaluate(
        self,
        data: Dict[str, Any],
        rule_ids: Optional[List[str]] = None
    ) -> List[Tuple[AlertRule, Dict[str, Any]]]:
        results = []
        
        rules_to_evaluate = [
            self._rules[rid] for rid in rule_ids
            if rid in self._rules
        ] if rule_ids else list(self._rules.values())
        
        for rule in rules_to_evaluate:
            if not rule.enabled:
                continue
            
            if not self._check_rate_limit(rule):
                continue
            
            if self._is_in_cooldown(rule):
                continue
            
            matched, match_data = self._evaluate_rule(rule, data)
            
            if matched:
                results.append((rule, match_data))
        
        return results
    
    def _evaluate_rule(
        self,
        rule: AlertRule,
        data: Dict[str, Any]
    ) -> Tuple[bool, Dict[str, Any]]:
        if rule.rule_id in self._rule_evaluators:
            try:
                return self._rule_evaluators[rule.rule_id](rule, data)
            except Exception as e:
                self.logger.error(f"规则评估器执行失败 {rule.rule_id}: {e}")
                return False, {}
        
        match_data = {}
        all_conditions_met = True
        
        for condition in rule.conditions:
            field_path = condition.get("field")
            operator = RuleOperator(condition.get("operator"))
            expected_value = condition.get("value")
            
            actual_value = self._get_field_value(data, field_path)
            
            if not self._compare_values(actual_value, operator, expected_value):
                all_conditions_met = False
                break
            
            match_data[field_path] = {
                "actual": actual_value,
                "expected": expected_value,
                "operator": operator.value
            }
        
        return all_conditions_met, match_data
    
    def _get_field_value(self, data: Dict[str, Any], field_path: str) -> Any:
        keys = field_path.split('.')
        value = data
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return None
        return value
    
    def _compare_values(
        self,
        actual: Any,
        operator: RuleOperator,
        expected: Any
    ) -> bool:
        if actual is None:
            return False
        
        try:
            if operator == RuleOperator.GREATER_THAN:
                return actual > expected
            elif operator == RuleOperator.LESS_THAN:
                return actual < expected
            elif operator == RuleOperator.GREATER_EQUAL:
                return actual >= expected
            elif operator == RuleOperator.LESS_EQUAL:
                return actual <= expected
            elif operator == RuleOperator.EQUAL:
                return actual == expected
            elif operator == RuleOperator.NOT_EQUAL:
                return actual != expected
            elif operator == RuleOperator.CONTAINS:
                return expected in actual
            elif operator == RuleOperator.NOT_CONTAINS:
                return expected not in actual
            elif operator == RuleOperator.IN:
                return actual in expected
            elif operator == RuleOperator.NOT_IN:
                return actual not in expected
            else:
                return False
        except Exception:
            return False
    
    def _check_rate_limit(self, rule: AlertRule) -> bool:
        now = datetime.now()
        hour_ago = now - timedelta(hours=1)
        
        self._alert_counters[rule.rule_id] = [
            t for t in self._alert_counters[rule.rule_id]
            if t > hour_ago
        ]
        
        if len(self._alert_counters[rule.rule_id]) >= rule.max_alerts_per_hour:
            return False
        
        return True
    
    def _is_in_cooldown(self, rule: AlertRule) -> bool:
        if rule.rule_id not in self._last_alert_times:
            return False
        
        last_alert = self._last_alert_times[rule.rule_id]
        cooldown_end = last_alert + timedelta(seconds=rule.cooldown_seconds)
        
        return datetime.now() < cooldown_end
    
    def record_alert_triggered(self, rule_id: str) -> None:
        now = datetime.now()
        self._alert_counters[rule_id].append(now)
        self._last_alert_times[rule_id] = now


class AlertNotificationManager:
    """告警通知管理器"""
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        self.logger = logger or logging.getLogger('EvolutionAlertSystem')
        self._notifiers: Dict[NotificationChannel, INotifier] = {}
        self._configs: Dict[NotificationChannel, NotificationConfig] = {}
        self._rate_limiters: Dict[NotificationChannel, List[datetime]] = defaultdict(list)
        self._notification_queue: queue.Queue = queue.Queue()
        self._worker_thread: Optional[threading.Thread] = None
        self._running = False
    
    def register_notifier(self, notifier: INotifier) -> None:
        self._notifiers[notifier.get_channel()] = notifier
        self.logger.info(f"注册通知器: {notifier.get_channel().value}")
    
    def configure_channel(self, config: NotificationConfig) -> None:
        self._configs[config.channel] = config
        self.logger.info(f"配置通知渠道: {config.channel.value}")
    
    def start(self) -> None:
        if self._running:
            return
        
        self._running = True
        self._worker_thread = threading.Thread(target=self._process_queue, daemon=True)
        self._worker_thread.start()
        self.logger.info("通知管理器已启动")
    
    def stop(self) -> None:
        self._running = False
        if self._worker_thread:
            self._worker_thread.join(timeout=5)
        self.logger.info("通知管理器已停止")
    
    def notify(self, alert: Alert, channels: Optional[List[NotificationChannel]] = None) -> bool:
        if not channels:
            channels = alert.notification_channels
        
        for channel in channels:
            config = self._configs.get(channel)
            if not config or not config.enabled:
                continue
            
            if alert.severity.value < config.min_severity.value:
                continue
            
            if not self._check_rate_limit(channel, config):
                continue
            
            self._notification_queue.put((alert, channel, config))
        
        return True
    
    def _process_queue(self) -> None:
        while self._running:
            try:
                alert, channel, config = self._notification_queue.get(timeout=1)
                self._send_notification(alert, channel, config)
            except queue.Empty:
                continue
            except Exception as e:
                self.logger.error(f"处理通知队列失败: {e}")
    
    def _send_notification(
        self,
        alert: Alert,
        channel: NotificationChannel,
        config: NotificationConfig
    ) -> bool:
        notifier = self._notifiers.get(channel)
        if not notifier:
            self.logger.warning(f"未找到通知器: {channel.value}")
            return False
        
        try:
            result = notifier.send(alert, config.config)
            if result:
                self._record_notification(channel)
                self.logger.info(f"通知已发送: {channel.value} - {alert.alert_id}")
            return result
        except Exception as e:
            self.logger.error(f"发送通知失败 {channel.value}: {e}")
            return False
    
    def _check_rate_limit(
        self,
        channel: NotificationChannel,
        config: NotificationConfig
    ) -> bool:
        now = datetime.now()
        minute_ago = now - timedelta(minutes=1)
        
        self._rate_limiters[channel] = [
            t for t in self._rate_limiters[channel]
            if t > minute_ago
        ]
        
        return len(self._rate_limiters[channel]) < config.rate_limit_per_minute
    
    def _record_notification(self, channel: NotificationChannel) -> None:
        self._rate_limiters[channel].append(datetime.now())


class AlertTracker:
    """告警追踪器"""
    
    def __init__(self, storage_path: Optional[Path] = None, logger: Optional[logging.Logger] = None):
        self.logger = logger or logging.getLogger('EvolutionAlertSystem')
        self.storage_path = storage_path or Path("./alert_data")
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        self._alerts: Dict[str, Alert] = {}
        self._active_alerts: Set[str] = set()
        self._alert_history_file = self.storage_path / "alert_history.json"
        self._load_history()
    
    def _load_history(self) -> None:
        if self._alert_history_file.exists():
            try:
                with open(self._alert_history_file, 'r', encoding='utf-8') as f:
                    history = json.load(f)
                    for alert_data in history:
                        alert = self._deserialize_alert(alert_data)
                        self._alerts[alert.alert_id] = alert
                        if alert.status == AlertStatus.ACTIVE:
                            self._active_alerts.add(alert.alert_id)
                self.logger.info(f"加载告警历史: {len(self._alerts)} 条")
            except Exception as e:
                self.logger.error(f"加载告警历史失败: {e}")
    
    def _save_history(self) -> None:
        try:
            history = [alert.to_dict() for alert in self._alerts.values()]
            with open(self._alert_history_file, 'w', encoding='utf-8') as f:
                json.dump(history, f, indent=2, ensure_ascii=False)
        except Exception as e:
            self.logger.error(f"保存告警历史失败: {e}")
    
    def _deserialize_alert(self, data: Dict[str, Any]) -> Alert:
        return Alert(
            alert_id=data["alert_id"],
            alert_type=AlertType(data["alert_type"]),
            severity=AlertSeverity[data["severity"]],
            status=AlertStatus(data["status"]),
            message=data["message"],
            context=AlertContext(**data["context"]),
            created_at=datetime.fromisoformat(data["created_at"]),
            updated_at=datetime.fromisoformat(data["updated_at"]),
            rule_id=data.get("rule_id"),
            acknowledged_by=data.get("acknowledged_by"),
            acknowledged_at=datetime.fromisoformat(data["acknowledged_at"]) if data.get("acknowledged_at") else None,
            resolved_by=data.get("resolved_by"),
            resolved_at=datetime.fromisoformat(data["resolved_at"]) if data.get("resolved_at") else None,
            resolution_note=data.get("resolution_note"),
            notification_sent=data.get("notification_sent", False),
            notification_channels=[NotificationChannel(c) for c in data.get("notification_channels", [])],
            suppression_until=datetime.fromisoformat(data["suppression_until"]) if data.get("suppression_until") else None,
            related_alerts=data.get("related_alerts", []),
            history=data.get("history", [])
        )
    
    def add_alert(self, alert: Alert) -> None:
        self._alerts[alert.alert_id] = alert
        if alert.status == AlertStatus.ACTIVE:
            self._active_alerts.add(alert.alert_id)
        self._save_history()
        self.logger.info(f"添加告警: {alert.alert_id}")
    
    def get_alert(self, alert_id: str) -> Optional[Alert]:
        return self._alerts.get(alert_id)
    
    def get_active_alerts(self) -> List[Alert]:
        return [self._alerts[aid] for aid in self._active_alerts if aid in self._alerts]
    
    def get_alerts_by_type(self, alert_type: AlertType) -> List[Alert]:
        return [a for a in self._alerts.values() if a.alert_type == alert_type]
    
    def get_alerts_by_severity(self, severity: AlertSeverity) -> List[Alert]:
        return [a for a in self._alerts.values() if a.severity == severity]
    
    def get_alerts_by_time_range(
        self,
        start_time: datetime,
        end_time: datetime
    ) -> List[Alert]:
        return [
            a for a in self._alerts.values()
            if start_time <= a.created_at <= end_time
        ]
    
    def acknowledge_alert(
        self,
        alert_id: str,
        acknowledged_by: str,
        note: Optional[str] = None
    ) -> bool:
        alert = self._alerts.get(alert_id)
        if not alert:
            return False
        
        if alert.status != AlertStatus.ACTIVE:
            return False
        
        alert.status = AlertStatus.ACKNOWLEDGED
        alert.acknowledged_by = acknowledged_by
        alert.acknowledged_at = datetime.now()
        alert.updated_at = datetime.now()
        
        alert.add_history_entry("acknowledged", {
            "by": acknowledged_by,
            "note": note
        })
        
        self._active_alerts.discard(alert_id)
        self._save_history()
        
        self.logger.info(f"告警已确认: {alert_id} by {acknowledged_by}")
        return True
    
    def resolve_alert(
        self,
        alert_id: str,
        resolved_by: str,
        resolution_note: str
    ) -> bool:
        alert = self._alerts.get(alert_id)
        if not alert:
            return False
        
        if alert.status not in [AlertStatus.ACTIVE, AlertStatus.ACKNOWLEDGED]:
            return False
        
        alert.status = AlertStatus.RESOLVED
        alert.resolved_by = resolved_by
        alert.resolved_at = datetime.now()
        alert.resolution_note = resolution_note
        alert.updated_at = datetime.now()
        
        alert.add_history_entry("resolved", {
            "by": resolved_by,
            "note": resolution_note
        })
        
        self._active_alerts.discard(alert_id)
        self._save_history()
        
        self.logger.info(f"告警已解决: {alert_id} by {resolved_by}")
        return True
    
    def suppress_alert(
        self,
        alert_id: str,
        duration_seconds: int
    ) -> bool:
        alert = self._alerts.get(alert_id)
        if not alert:
            return False
        
        alert.status = AlertStatus.SUPPRESSED
        alert.suppression_until = datetime.now() + timedelta(seconds=duration_seconds)
        alert.updated_at = datetime.now()
        
        alert.add_history_entry("suppressed", {
            "duration_seconds": duration_seconds
        })
        
        self._active_alerts.discard(alert_id)
        self._save_history()
        
        self.logger.info(f"告警已抑制: {alert_id} for {duration_seconds} seconds")
        return True
    
    def link_alerts(self, alert_id1: str, alert_id2: str) -> bool:
        alert1 = self._alerts.get(alert_id1)
        alert2 = self._alerts.get(alert_id2)
        
        if not alert1 or not alert2:
            return False
        
        if alert_id2 not in alert1.related_alerts:
            alert1.related_alerts.append(alert_id2)
        
        if alert_id1 not in alert2.related_alerts:
            alert2.related_alerts.append(alert_id1)
        
        self._save_history()
        return True
    
    def get_statistics(self) -> Dict[str, Any]:
        now = datetime.now()
        hour_ago = now - timedelta(hours=1)
        day_ago = now - timedelta(days=1)
        
        alerts_last_hour = len(self.get_alerts_by_time_range(hour_ago, now))
        alerts_last_day = len(self.get_alerts_by_time_range(day_ago, now))
        
        by_severity = defaultdict(int)
        by_type = defaultdict(int)
        by_status = defaultdict(int)
        
        for alert in self._alerts.values():
            by_severity[alert.severity.name] += 1
            by_type[alert.alert_type.value] += 1
            by_status[alert.status.value] += 1
        
        return {
            "total_alerts": len(self._alerts),
            "active_alerts": len(self._active_alerts),
            "alerts_last_hour": alerts_last_hour,
            "alerts_last_day": alerts_last_day,
            "by_severity": dict(by_severity),
            "by_type": dict(by_type),
            "by_status": dict(by_status)
        }


class EvolutionAlertSystem:
    """演化告警系统主类"""
    
    def __init__(
        self,
        storage_path: Optional[Path] = None,
        logger: Optional[logging.Logger] = None
    ):
        self.logger = logger or logging.getLogger('EvolutionAlertSystem')
        self.storage_path = storage_path or Path("./alert_data")
        
        self.rule_engine = AlertRuleEngine(logger)
        self.notification_manager = AlertNotificationManager(logger)
        self.tracker = AlertTracker(self.storage_path, logger)
        
        self._running = False
        self._monitor_thread: Optional[threading.Thread] = None
        self._data_source: Optional[Callable[[], Dict[str, Any]]] = None
        self._monitor_interval = 60
        
        self._setup_default_notifiers()
        self._setup_default_rules()
    
    def _setup_default_notifiers(self) -> None:
        self.notification_manager.register_notifier(LogNotifier(self.logger))
        self.notification_manager.register_notifier(ConsoleNotifier())
        self.notification_manager.register_notifier(EmailNotifier(self.logger))
        self.notification_manager.register_notifier(WebhookNotifier(self.logger))
        self.notification_manager.register_notifier(WebSocketNotifier(self.logger))
        
        self.notification_manager.configure_channel(
            NotificationConfig(
                channel=NotificationChannel.LOG,
                enabled=True,
                min_severity=AlertSeverity.INFO
            )
        )
        
        self.notification_manager.configure_channel(
            NotificationConfig(
                channel=NotificationChannel.CONSOLE,
                enabled=True,
                min_severity=AlertSeverity.WARNING
            )
        )
    
    def _setup_default_rules(self) -> None:
        default_rules = [
            AlertRule(
                rule_id="error_rate_high",
                name="错误率过高",
                description="当错误率超过阈值时触发告警",
                alert_type=AlertType.ERROR_RATE_HIGH,
                severity=AlertSeverity.ERROR,
                enabled=True,
                conditions=[
                    {"field": "error_rate", "operator": "gt", "value": 0.10}
                ],
                actions=[{"type": "notify"}],
                notification_channels=[NotificationChannel.LOG, NotificationChannel.CONSOLE],
                cooldown_seconds=300
            ),
            AlertRule(
                rule_id="performance_degraded",
                name="性能退化",
                description="当响应时间超过阈值时触发告警",
                alert_type=AlertType.PERFORMANCE_DEGRADED,
                severity=AlertSeverity.WARNING,
                enabled=True,
                conditions=[
                    {"field": "response_time", "operator": "gt", "value": 5000}
                ],
                actions=[{"type": "notify"}],
                notification_channels=[NotificationChannel.LOG, NotificationChannel.CONSOLE],
                cooldown_seconds=600
            ),
            AlertRule(
                rule_id="fix_failed",
                name="修复失败",
                description="当自动修复连续失败时触发告警",
                alert_type=AlertType.FIX_FAILED,
                severity=AlertSeverity.ERROR,
                enabled=True,
                conditions=[
                    {"field": "consecutive_fix_failures", "operator": "ge", "value": 3}
                ],
                actions=[{"type": "notify"}],
                notification_channels=[NotificationChannel.LOG, NotificationChannel.CONSOLE],
                cooldown_seconds=300
            ),
            AlertRule(
                rule_id="learning_stalled",
                name="学习停滞",
                description="当学习进度停滞时触发告警",
                alert_type=AlertType.LEARNING_STALLED,
                severity=AlertSeverity.WARNING,
                enabled=True,
                conditions=[
                    {"field": "learning_progress", "operator": "eq", "value": 0},
                    {"field": "stalled_duration_minutes", "operator": "gt", "value": 30}
                ],
                actions=[{"type": "notify"}],
                notification_channels=[NotificationChannel.LOG, NotificationChannel.CONSOLE],
                cooldown_seconds=900
            ),
            AlertRule(
                rule_id="evolution_cycle_timeout",
                name="演化周期超时",
                description="当演化周期执行超时时触发告警",
                alert_type=AlertType.EVOLUTION_CYCLE_TIMEOUT,
                severity=AlertSeverity.ERROR,
                enabled=True,
                conditions=[
                    {"field": "cycle_duration_seconds", "operator": "gt", "value": 3600}
                ],
                actions=[{"type": "notify"}],
                notification_channels=[NotificationChannel.LOG, NotificationChannel.CONSOLE],
                cooldown_seconds=600
            )
        ]
        
        for rule in default_rules:
            self.rule_engine.add_rule(rule)
    
    def start(self) -> None:
        if self._running:
            return
        
        self._running = True
        self.notification_manager.start()
        
        self._monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._monitor_thread.start()
        
        self.logger.info("演化告警系统已启动")
    
    def stop(self) -> None:
        self._running = False
        self.notification_manager.stop()
        
        if self._monitor_thread:
            self._monitor_thread.join(timeout=5)
        
        self.logger.info("演化告警系统已停止")
    
    def set_data_source(self, source: Callable[[], Dict[str, Any]]) -> None:
        self._data_source = source
    
    def set_monitor_interval(self, interval_seconds: int) -> None:
        self._monitor_interval = interval_seconds
    
    def _monitor_loop(self) -> None:
        while self._running:
            try:
                if self._data_source:
                    data = self._data_source()
                    self.evaluate_and_alert(data)
                
                self._check_auto_resolve()
                self._check_suppression_expiry()
                
                time.sleep(self._monitor_interval)
            except Exception as e:
                self.logger.error(f"监控循环错误: {e}")
                time.sleep(5)
    
    def _check_auto_resolve(self) -> None:
        now = datetime.now()
        for alert in self.tracker.get_active_alerts():
            rule = self.rule_engine.get_rule(alert.rule_id) if alert.rule_id else None
            if rule and rule.auto_resolve:
                resolve_after = alert.created_at + timedelta(seconds=rule.auto_resolve_after_seconds)
                if now >= resolve_after:
                    self.resolve_alert(
                        alert.alert_id,
                        "system",
                        "自动解决：超时未处理"
                    )
    
    def _check_suppression_expiry(self) -> None:
        now = datetime.now()
        for alert in list(self.tracker._alerts.values()):
            if alert.status == AlertStatus.SUPPRESSED and alert.suppression_until:
                if now >= alert.suppression_until:
                    alert.status = AlertStatus.ACTIVE
                    alert.suppression_until = None
                    alert.updated_at = now
                    alert.add_history_entry("suppression_expired", {})
                    self.tracker._active_alerts.add(alert.alert_id)
                    self.tracker._save_history()
    
    def create_alert(
        self,
        alert_type: AlertType,
        severity: AlertSeverity,
        message: str,
        context: AlertContext,
        rule_id: Optional[str] = None,
        notification_channels: Optional[List[NotificationChannel]] = None
    ) -> Alert:
        now = datetime.now()
        alert_id = f"ALERT-{now.strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:8]}"
        
        if notification_channels is None:
            notification_channels = [NotificationChannel.LOG, NotificationChannel.CONSOLE]
        
        alert = Alert(
            alert_id=alert_id,
            alert_type=alert_type,
            severity=severity,
            status=AlertStatus.ACTIVE,
            message=message,
            context=context,
            created_at=now,
            updated_at=now,
            rule_id=rule_id,
            notification_channels=notification_channels
        )
        
        alert.add_history_entry("created", {
            "type": alert_type.value,
            "severity": severity.name
        })
        
        self.tracker.add_alert(alert)
        
        if rule_id:
            self.rule_engine.record_alert_triggered(rule_id)
        
        self.notification_manager.notify(alert)
        
        self.logger.info(f"创建告警: {alert_id} - {message}")
        return alert
    
    def evaluate_and_alert(
        self,
        data: Dict[str, Any],
        rule_ids: Optional[List[str]] = None
    ) -> List[Alert]:
        matched_rules = self.rule_engine.evaluate(data, rule_ids)
        alerts = []
        
        for rule, match_data in matched_rules:
            context = AlertContext(
                source=data.get("source", "unknown"),
                component=data.get("component", "unknown"),
                additional_data={"match_data": match_data}
            )
            
            alert = self.create_alert(
                alert_type=rule.alert_type,
                severity=rule.severity,
                message=f"规则 [{rule.name}] 触发",
                context=context,
                rule_id=rule.rule_id,
                notification_channels=rule.notification_channels
            )
            
            alerts.append(alert)
        
        return alerts
    
    def acknowledge_alert(
        self,
        alert_id: str,
        acknowledged_by: str,
        note: Optional[str] = None
    ) -> bool:
        return self.tracker.acknowledge_alert(alert_id, acknowledged_by, note)
    
    def resolve_alert(
        self,
        alert_id: str,
        resolved_by: str,
        resolution_note: str
    ) -> bool:
        return self.tracker.resolve_alert(alert_id, resolved_by, resolution_note)
    
    def suppress_alert(
        self,
        alert_id: str,
        duration_seconds: int
    ) -> bool:
        return self.tracker.suppress_alert(alert_id, duration_seconds)
    
    def get_alert(self, alert_id: str) -> Optional[Alert]:
        return self.tracker.get_alert(alert_id)
    
    def get_active_alerts(self) -> List[Alert]:
        return self.tracker.get_active_alerts()
    
    def get_statistics(self) -> Dict[str, Any]:
        return self.tracker.get_statistics()
    
    def add_rule(self, rule: AlertRule) -> bool:
        return self.rule_engine.add_rule(rule)
    
    def remove_rule(self, rule_id: str) -> bool:
        return self.rule_engine.remove_rule(rule_id)
    
    def configure_notification(
        self,
        channel: NotificationChannel,
        config: Dict[str, Any],
        enabled: bool = True,
        min_severity: AlertSeverity = AlertSeverity.INFO
    ) -> None:
        self.notification_manager.configure_channel(
            NotificationConfig(
                channel=channel,
                enabled=enabled,
                config=config,
                min_severity=min_severity
            )
        )
    
    def register_websocket_connection(
        self,
        connection_id: str,
        connection: Any
    ) -> None:
        notifier = self.notification_manager._notifiers.get(NotificationChannel.WEBSOCKET)
        if isinstance(notifier, WebSocketNotifier):
            notifier.register_connection(connection_id, connection)


def create_alert_system(
    storage_path: Optional[str] = None,
    log_level: str = "INFO"
) -> EvolutionAlertSystem:
    logger = logging.getLogger('EvolutionAlertSystem')
    logger.setLevel(getattr(logging, log_level.upper()))
    
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    
    path = Path(storage_path) if storage_path else None
    return EvolutionAlertSystem(storage_path=path, logger=logger)


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='演化告警系统')
    parser.add_argument('--storage', default='./alert_data', help='存储路径')
    parser.add_argument('--log-level', default='INFO', help='日志级别')
    parser.add_argument('--test', action='store_true', help='运行测试')
    
    args = parser.parse_args()
    
    alert_system = create_alert_system(
        storage_path=args.storage,
        log_level=args.log_level
    )
    
    if args.test:
        print("运行告警系统测试...")
        
        alert = alert_system.create_alert(
            alert_type=AlertType.ERROR_RATE_HIGH,
            severity=AlertSeverity.ERROR,
            message="测试告警：错误率达到15%",
            context=AlertContext(
                source="test_script",
                component="error_monitor",
                metric_name="error_rate",
                metric_value=0.15,
                threshold=0.10
            )
        )
        
        print(f"创建告警: {alert.alert_id}")
        
        stats = alert_system.get_statistics()
        print(f"统计信息: {json.dumps(stats, indent=2)}")
        
        alert_system.acknowledge_alert(alert.alert_id, "test_user", "确认测试告警")
        
        alert_system.resolve_alert(alert.alert_id, "test_user", "测试告警已解决")
        
        print("测试完成")
        return
    
    alert_system.start()
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        alert_system.stop()


if __name__ == '__main__':
    main()
