#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
增强异常检测器 - Enhanced Anomaly Detector

实现实时日志监控和异常检测，支持：
- 实时日志监控与流式处理
- 多维度异常模式检测
- 智能预警通知机制
- 异常上下文记录与分析
- 自适应基线学习
- 告警抑制与聚合
- 多通道通知分发

使用示例:
    python anomaly_detector.py --log-file app.log --monitor
    python anomaly_detector.py --config detector_config.json --alert
    python anomaly_detector.py --log-dir ./logs --analyze --realtime
"""

import argparse
import hashlib
import json
import logging
import os
import re
import smtplib
import sys
import threading
import time
from abc import ABC, abstractmethod
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Protocol, Set, Tuple, Union
import queue


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class AnomalyType(Enum):
    ERROR_SPIKE = "error_spike"
    LATENCY_SPIKE = "latency_spike"
    PATTERN_DEVIATION = "pattern_deviation"
    FREQUENCY_ANOMALY = "frequency_anomaly"
    SEQUENCE_ANOMALY = "sequence_anomaly"
    THRESHOLD_BREACH = "threshold_breach"
    BEHAVIORAL_ANOMALY = "behavioral_anomaly"
    RESOURCE_EXHAUSTION = "resource_exhaustion"
    SERVICE_DEGRADATION = "service_degradation"
    SECURITY_ANOMALY = "security_anomaly"
    CORRELATION_ANOMALY = "correlation_anomaly"


class AlertLevel(Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class NotificationChannel(Enum):
    EMAIL = "email"
    WEBHOOK = "webhook"
    SLACK = "slack"
    CONSOLE = "console"
    FILE = "file"
    DINGTALK = "dingtalk"
    WECHAT = "wechat"


class AlertState(Enum):
    ACTIVE = "active"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"
    SUPPRESSED = "suppressed"


@dataclass
class AnomalyPattern:
    pattern_id: str
    name: str
    description: str
    anomaly_type: AnomalyType
    detection_rule: Dict[str, Any]
    threshold: float
    alert_level: AlertLevel
    enabled: bool = True
    tags: List[str] = field(default_factory=list)
    cooldown_seconds: int = 300
    auto_resolve_seconds: int = 3600

    def to_dict(self) -> Dict[str, Any]:
        return {
            "pattern_id": self.pattern_id,
            "name": self.name,
            "description": self.description,
            "anomaly_type": self.anomaly_type.value,
            "detection_rule": self.detection_rule,
            "threshold": self.threshold,
            "alert_level": self.alert_level.value,
            "enabled": self.enabled,
            "tags": self.tags,
            "cooldown_seconds": self.cooldown_seconds,
            "auto_resolve_seconds": self.auto_resolve_seconds
        }


@dataclass
class LogContext:
    context_id: str
    timestamp: datetime
    source: str
    level: str
    message: str
    before_events: List[Dict[str, Any]]
    after_events: List[Dict[str, Any]]
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "context_id": self.context_id,
            "timestamp": self.timestamp.isoformat(),
            "source": self.source,
            "level": self.level,
            "message": self.message,
            "before_events": self.before_events,
            "after_events": self.after_events,
            "metadata": self.metadata
        }


@dataclass
class AnomalyAlert:
    alert_id: str
    timestamp: datetime
    anomaly_type: AnomalyType
    alert_level: AlertLevel
    pattern_name: str
    message: str
    context: LogContext
    metrics: Dict[str, Any]
    suggestions: List[str]
    acknowledged: bool = False
    state: AlertState = AlertState.ACTIVE
    related_alerts: List[str] = field(default_factory=list)
    fingerprint: str = ""
    first_occurred: Optional[datetime] = None
    last_occurred: Optional[datetime] = None
    occurrence_count: int = 1
    tags: List[str] = field(default_factory=list)

    def __post_init__(self):
        if not self.fingerprint:
            self.fingerprint = self._generate_fingerprint()
        if not self.first_occurred:
            self.first_occurred = self.timestamp
        if not self.last_occurred:
            self.last_occurred = self.timestamp

    def _generate_fingerprint(self) -> str:
        content = f"{self.anomaly_type.value}:{self.pattern_name}:{self.message[:50]}"
        return hashlib.md5(content.encode()).hexdigest()[:16]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "alert_id": self.alert_id,
            "timestamp": self.timestamp.isoformat(),
            "anomaly_type": self.anomaly_type.value,
            "alert_level": self.alert_level.value,
            "pattern_name": self.pattern_name,
            "message": self.message,
            "context": self.context.to_dict(),
            "metrics": self.metrics,
            "suggestions": self.suggestions,
            "acknowledged": self.acknowledged,
            "state": self.state.value,
            "related_alerts": self.related_alerts,
            "fingerprint": self.fingerprint,
            "first_occurred": self.first_occurred.isoformat() if self.first_occurred else None,
            "last_occurred": self.last_occurred.isoformat() if self.last_occurred else None,
            "occurrence_count": self.occurrence_count,
            "tags": self.tags
        }


@dataclass
class DetectionResult:
    detected: bool
    anomaly_type: AnomalyType
    confidence: float
    details: Dict[str, Any]
    events: List[Dict[str, Any]]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "detected": self.detected,
            "anomaly_type": self.anomaly_type.value,
            "confidence": self.confidence,
            "details": self.details,
            "event_count": len(self.events)
        }


@dataclass
class AlertRule:
    rule_id: str
    name: str
    condition: Dict[str, Any]
    actions: List[Dict[str, Any]]
    enabled: bool = True
    priority: int = 0
    suppression_window_seconds: int = 300
    aggregation_window_seconds: int = 60

    def to_dict(self) -> Dict[str, Any]:
        return {
            "rule_id": self.rule_id,
            "name": self.name,
            "condition": self.condition,
            "actions": self.actions,
            "enabled": self.enabled,
            "priority": self.priority,
            "suppression_window_seconds": self.suppression_window_seconds,
            "aggregation_window_seconds": self.aggregation_window_seconds
        }


class Notifier(Protocol):
    def send(self, alert: AnomalyAlert) -> bool:
        ...


class ConsoleNotifier:
    def __init__(self, verbose: bool = True):
        self.verbose = verbose

    def send(self, alert: AnomalyAlert) -> bool:
        level_colors = {
            AlertLevel.INFO: "\033[94m",
            AlertLevel.WARNING: "\033[93m",
            AlertLevel.ERROR: "\033[91m",
            AlertLevel.CRITICAL: "\033[95m",
        }
        reset = "\033[0m"
        color = level_colors.get(alert.alert_level, "")

        print(f"\n{color}{'=' * 60}{reset}")
        print(f"{color}[{alert.alert_level.value.upper()}] {alert.pattern_name}{reset}")
        print(f"{color}{'=' * 60}{reset}")
        print(f"时间: {alert.timestamp}")
        print(f"类型: {alert.anomaly_type.value}")
        print(f"消息: {alert.message}")
        print(f"置信度: {alert.confidence:.2%}" if hasattr(alert, 'confidence') else "")
        print(f"状态: {alert.state.value}")
        print(f"出现次数: {alert.occurrence_count}")

        if self.verbose and alert.context.before_events:
            print("\n上下文 (前):")
            for event in alert.context.before_events[-3:]:
                print(f"  {event.get('timestamp', '')}: {event.get('message', '')[:60]}")

        if alert.suggestions:
            print("\n建议:")
            for suggestion in alert.suggestions:
                print(f"  - {suggestion}")

        return True


class FileNotifier:
    def __init__(self, output_path: str, rotate_size_mb: int = 10):
        self.output_path = Path(output_path)
        self.output_path.parent.mkdir(parents=True, exist_ok=True)
        self.rotate_size_mb = rotate_size_mb
        self._lock = threading.Lock()

    def send(self, alert: AnomalyAlert) -> bool:
        try:
            with self._lock:
                self._rotate_if_needed()
                with open(self.output_path, 'a', encoding='utf-8') as f:
                    f.write(json.dumps(alert.to_dict(), ensure_ascii=False) + '\n')
            return True
        except Exception as e:
            logger.error(f"写入告警文件失败: {e}")
            return False

    def _rotate_if_needed(self) -> None:
        if self.output_path.exists():
            size_mb = self.output_path.stat().st_size / (1024 * 1024)
            if size_mb >= self.rotate_size_mb:
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                rotated_path = self.output_path.with_suffix(f'.{timestamp}.json')
                self.output_path.rename(rotated_path)


class EmailNotifier:
    def __init__(
        self,
        smtp_host: str,
        smtp_port: int,
        username: str,
        password: str,
        from_addr: str,
        to_addrs: List[str],
        use_tls: bool = True,
        template: Optional[str] = None
    ):
        self.smtp_host = smtp_host
        self.smtp_port = smtp_port
        self.username = username
        self.password = password
        self.from_addr = from_addr
        self.to_addrs = to_addrs
        self.use_tls = use_tls
        self.template = template

    def send(self, alert: AnomalyAlert) -> bool:
        try:
            msg = MIMEMultipart('alternative')
            msg['Subject'] = f"[{alert.alert_level.value.upper()}] {alert.pattern_name}"
            msg['From'] = self.from_addr
            msg['To'] = ', '.join(self.to_addrs)

            text_content = self._generate_text_content(alert)
            html_content = self._generate_html_content(alert)

            msg.attach(MIMEText(text_content, 'plain', 'utf-8'))
            msg.attach(MIMEText(html_content, 'html', 'utf-8'))

            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                if self.use_tls:
                    server.starttls()
                server.login(self.username, self.password)
                server.sendmail(self.from_addr, self.to_addrs, msg.as_string())

            logger.info(f"邮件告警已发送: {alert.alert_id}")
            return True
        except Exception as e:
            logger.error(f"发送邮件告警失败: {e}")
            return False

    def _generate_text_content(self, alert: AnomalyAlert) -> str:
        return f"""
异常告警通知

告警级别: {alert.alert_level.value}
异常类型: {alert.anomaly_type.value}
时间: {alert.timestamp}
消息: {alert.message}
状态: {alert.state.value}
出现次数: {alert.occurrence_count}

建议:
{chr(10).join(f'- {s}' for s in alert.suggestions)}

指标:
{chr(10).join(f'- {k}: {v}' for k, v in alert.metrics.items())}
"""

    def _generate_html_content(self, alert: AnomalyAlert) -> str:
        level_colors = {
            AlertLevel.INFO: "#17a2b8",
            AlertLevel.WARNING: "#ffc107",
            AlertLevel.ERROR: "#dc3545",
            AlertLevel.CRITICAL: "#721c24",
        }
        color = level_colors.get(alert.alert_level, "#333")

        return f"""
<!DOCTYPE html>
<html>
<body style="font-family: Arial, sans-serif;">
    <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
        <div style="background: {color}; color: white; padding: 15px; border-radius: 5px;">
            <h2 style="margin: 0;">[{alert.alert_level.value.upper()}] {alert.pattern_name}</h2>
        </div>
        <div style="background: #f5f5f5; padding: 15px; margin-top: 10px; border-radius: 5px;">
            <p><strong>时间:</strong> {alert.timestamp}</p>
            <p><strong>类型:</strong> {alert.anomaly_type.value}</p>
            <p><strong>消息:</strong> {alert.message}</p>
            <p><strong>状态:</strong> {alert.state.value}</p>
            <p><strong>出现次数:</strong> {alert.occurrence_count}</p>
        </div>
        <div style="margin-top: 10px; padding: 15px; background: #e7f3ff; border-radius: 5px;">
            <h3>建议</h3>
            <ul>
                {''.join(f'<li>{s}</li>' for s in alert.suggestions)}
            </ul>
        </div>
    </div>
</body>
</html>
"""


class WebhookNotifier:
    def __init__(self, webhook_url: str, headers: Optional[Dict[str, str]] = None, timeout: int = 10):
        self.webhook_url = webhook_url
        self.headers = headers or {}
        self.timeout = timeout

    def send(self, alert: AnomalyAlert) -> bool:
        try:
            import urllib.request
            import urllib.error

            data = json.dumps(alert.to_dict()).encode('utf-8')
            req = urllib.request.Request(
                self.webhook_url,
                data=data,
                headers={**self.headers, 'Content-Type': 'application/json'},
                method='POST'
            )

            with urllib.request.urlopen(req, timeout=self.timeout) as response:
                return response.status == 200
        except Exception as e:
            logger.error(f"Webhook通知失败: {e}")
            return False


class DingTalkNotifier:
    """钉钉通知器 - 通过钉钉机器人发送告警通知"""
    
    def __init__(self, webhook_url: str, secret: Optional[str] = None):
        self.webhook_url = webhook_url
        self.secret = secret

    def send(self, alert: AnomalyAlert) -> bool:
        try:
            import urllib.request
            import urllib.parse
            import hmac
            import base64
            import time as time_module

            url = self.webhook_url
            if self.secret:
                timestamp = str(int(time_module.time() * 1000))
                string_to_sign = f"{timestamp}\n{self.secret}"
                hmac_code = hmac.new(
                    self.secret.encode('utf-8'),
                    string_to_sign.encode('utf-8'),
                    digestmod='sha256'
                ).digest()
                sign = urllib.parse.quote_plus(base64.b64encode(hmac_code))
                url = f"{self.webhook_url}&timestamp={timestamp}&sign={sign}"

            level_emoji = {
                AlertLevel.INFO: "ℹ️",
                AlertLevel.WARNING: "⚠️",
                AlertLevel.ERROR: "❌",
                AlertLevel.CRITICAL: "🔥",
            }

            message = {
                "msgtype": "markdown",
                "markdown": {
                    "title": f"[{alert.alert_level.value.upper()}] {alert.pattern_name}",
                    "text": f"""### {level_emoji.get(alert.alert_level, '')} {alert.pattern_name}

**级别**: {alert.alert_level.value}
**类型**: {alert.anomaly_type.value}
**时间**: {alert.timestamp}
**状态**: {alert.state.value}
**出现次数**: {alert.occurrence_count}

**消息**: {alert.message}

**建议**:
{chr(10).join(f'- {s}' for s in alert.suggestions[:5])}
"""
                }
            }

            data = json.dumps(message).encode('utf-8')
            req = urllib.request.Request(
                url,
                data=data,
                headers={'Content-Type': 'application/json'},
                method='POST'
            )

            with urllib.request.urlopen(req, timeout=10) as response:
                return response.status == 200
        except Exception as e:
            logger.error(f"钉钉通知失败: {e}")
            return False


class WeChatNotifier:
    """企业微信通知器 - 通过企业微信机器人发送告警通知"""
    
    def __init__(self, webhook_url: str, mentioned_list: Optional[List[str]] = None):
        self.webhook_url = webhook_url
        self.mentioned_list = mentioned_list or []

    def send(self, alert: AnomalyAlert) -> bool:
        try:
            import urllib.request

            level_emoji = {
                AlertLevel.INFO: "🔵",
                AlertLevel.WARNING: "🟡",
                AlertLevel.ERROR: "🔴",
                AlertLevel.CRITICAL: "🟠",
            }

            content = f"""{level_emoji.get(alert.alert_level, '')} **[{alert.alert_level.value.upper()}] {alert.pattern_name}**

> 类型: {alert.anomaly_type.value}
> 时间: {alert.timestamp}
> 状态: {alert.state.value}
> 出现次数: {alert.occurrence_count}

**消息**: {alert.message}

**建议**:
{chr(10).join(f'- {s}' for s in alert.suggestions[:5])}
"""
            message = {
                "msgtype": "markdown",
                "markdown": {
                    "content": content,
                    "mentioned_list": self.mentioned_list
                }
            }

            data = json.dumps(message).encode('utf-8')
            req = urllib.request.Request(
                self.webhook_url,
                data=data,
                headers={'Content-Type': 'application/json'},
                method='POST'
            )

            with urllib.request.urlopen(req, timeout=10) as response:
                return response.status == 200
        except Exception as e:
            logger.error(f"企业微信通知失败: {e}")
            return False


class SlackNotifier:
    """Slack通知器 - 通过Slack Webhook发送告警通知"""
    
    def __init__(self, webhook_url: str, channel: Optional[str] = None):
        self.webhook_url = webhook_url
        self.channel = channel

    def send(self, alert: AnomalyAlert) -> bool:
        try:
            import urllib.request

            level_colors = {
                AlertLevel.INFO: "#36a64f",
                AlertLevel.WARNING: "#ff9900",
                AlertLevel.ERROR: "#ff0000",
                AlertLevel.CRITICAL: "#990000",
            }

            attachment = {
                "color": level_colors.get(alert.alert_level, "#333333"),
                "title": f"[{alert.alert_level.value.upper()}] {alert.pattern_name}",
                "fields": [
                    {"title": "类型", "value": alert.anomaly_type.value, "short": True},
                    {"title": "状态", "value": alert.state.value, "short": True},
                    {"title": "出现次数", "value": str(alert.occurrence_count), "short": True},
                    {"title": "时间", "value": str(alert.timestamp), "short": True},
                    {"title": "消息", "value": alert.message, "short": False},
                ],
                "footer": "Anomaly Detector",
                "ts": int(alert.timestamp.timestamp())
            }

            message = {
                "attachments": [attachment]
            }

            if self.channel:
                message["channel"] = self.channel

            data = json.dumps(message).encode('utf-8')
            req = urllib.request.Request(
                self.webhook_url,
                data=data,
                headers={'Content-Type': 'application/json'},
                method='POST'
            )

            with urllib.request.urlopen(req, timeout=10) as response:
                return response.status == 200
        except Exception as e:
            logger.error(f"Slack通知失败: {e}")
            return False


class AlertAggregator:
    """告警聚合器 - 对相似告警进行聚合处理"""
    
    def __init__(
        self,
        aggregation_window_seconds: int = 60,
        max_alerts_per_window: int = 10
    ):
        self.aggregation_window_seconds = aggregation_window_seconds
        self.max_alerts_per_window = max_alerts_per_window
        self._alert_buckets: Dict[str, List[AnomalyAlert]] = defaultdict(list)
        self._last_aggregation: Dict[str, datetime] = {}
        self._lock = threading.Lock()
    
    def add_alert(self, alert: AnomalyAlert) -> Optional[AnomalyAlert]:
        """添加告警到聚合器，返回需要发送的聚合告警（如果有）"""
        with self._lock:
            bucket_key = f"{alert.anomaly_type.value}:{alert.alert_level.value}"
            
            now = datetime.now()
            self._alert_buckets[bucket_key].append(alert)
            
            last_agg = self._last_aggregation.get(bucket_key)
            
            if last_agg is None or (now - last_agg).total_seconds() >= self.aggregation_window_seconds:
                bucket = self._alert_buckets[bucket_key]
                
                if len(bucket) >= self.max_alerts_per_window:
                    aggregated = self._create_aggregated_alert(bucket, bucket_key)
                    self._alert_buckets[bucket_key] = []
                    self._last_aggregation[bucket_key] = now
                    return aggregated
            
            return None
    
    def _create_aggregated_alert(self, alerts: List[AnomalyAlert], bucket_key: str) -> AnomalyAlert:
        """创建聚合告警"""
        first_alert = alerts[0]
        
        unique_messages = list(set(a.message for a in alerts[:10]))
        aggregated_message = f"聚合告警 ({len(alerts)}个相似告警): " + "; ".join(unique_messages[:3])
        
        return AnomalyAlert(
            alert_id=f"AGG-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            timestamp=datetime.now(),
            anomaly_type=first_alert.anomaly_type,
            alert_level=first_alert.alert_level,
            pattern_name=f"聚合: {first_alert.pattern_name}",
            message=aggregated_message,
            context=first_alert.context,
            metrics={
                "aggregated_count": len(alerts),
                "unique_messages": len(unique_messages)
            },
            suggestions=[
                f"此告警聚合了 {len(alerts)} 个相似告警",
                "请检查是否存在系统性问题"
            ],
            occurrence_count=len(alerts)
        )
    
    def get_pending_count(self) -> Dict[str, int]:
        """获取各桶中待处理的告警数量"""
        with self._lock:
            return {k: len(v) for k, v in self._alert_buckets.items()}


class AlertEscalationPolicy:
    """告警升级策略 - 定义告警升级规则"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.escalation_rules = self._default_escalation_rules()
        self._escalation_state: Dict[str, Dict[str, Any]] = {}
        self._lock = threading.Lock()
    
    def _default_escalation_rules(self) -> Dict[str, Dict[str, Any]]:
        """默认升级规则"""
        return {
            "critical": {
                "immediate": ["console", "file"],
                "after_5min": ["email", "webhook"],
                "after_15min": ["dingtalk", "wechat"],
                "repeat_interval": 300
            },
            "error": {
                "immediate": ["console", "file"],
                "after_10min": ["email"],
                "after_30min": ["webhook"],
                "repeat_interval": 600
            },
            "warning": {
                "immediate": ["console"],
                "after_30min": ["file"],
                "repeat_interval": 1800
            },
            "info": {
                "immediate": ["console"],
                "repeat_interval": 3600
            }
        }
    
    def should_escalate(self, alert: AnomalyAlert) -> Tuple[bool, List[str]]:
        """
        判断是否需要升级告警
        返回: (是否需要发送通知, 应该使用的通知渠道列表)
        """
        with self._lock:
            level = alert.alert_level.value
            fingerprint = alert.fingerprint
            
            rule = self.escalation_rules.get(level, self.escalation_rules["info"])
            
            now = datetime.now()
            
            if fingerprint not in self._escalation_state:
                self._escalation_state[fingerprint] = {
                    "first_seen": now,
                    "last_notified": None,
                    "notification_count": 0,
                    "channels_used": []
                }
            
            state = self._escalation_state[fingerprint]
            time_elapsed = (now - state["first_seen"]).total_seconds()
            
            channels = list(rule.get("immediate", []))
            
            if time_elapsed >= 300 and "after_5min" in rule:
                channels.extend(rule["after_5min"])
            if time_elapsed >= 900 and "after_15min" in rule:
                channels.extend(rule["after_15min"])
            if time_elapsed >= 600 and "after_10min" in rule:
                channels.extend(rule["after_10min"])
            if time_elapsed >= 1800 and "after_30min" in rule:
                channels.extend(rule["after_30min"])
            
            channels = list(set(channels))
            
            repeat_interval = rule.get("repeat_interval", 300)
            if state["last_notified"]:
                time_since_last = (now - state["last_notified"]).total_seconds()
                if time_since_last < repeat_interval:
                    return False, []
            
            should_notify = any(ch not in state["channels_used"] for ch in channels)
            
            if should_notify or state["notification_count"] == 0:
                state["last_notified"] = now
                state["notification_count"] += 1
                state["channels_used"].extend(channels)
                state["channels_used"] = list(set(state["channels_used"]))
                return True, channels
            
            return False, []
    
    def reset_escalation(self, fingerprint: str) -> None:
        """重置告警升级状态"""
        with self._lock:
            if fingerprint in self._escalation_state:
                del self._escalation_state[fingerprint]


class LogFilter:
    """日志过滤器 - 根据规则过滤日志事件"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.include_levels: Set[str] = set(self.config.get('include_levels', ['ERROR', 'WARNING', 'CRITICAL', 'FATAL']))
        self.exclude_patterns: List[re.Pattern] = [
            re.compile(p, re.IGNORECASE) 
            for p in self.config.get('exclude_patterns', [])
        ]
        self.include_patterns: List[re.Pattern] = [
            re.compile(p, re.IGNORECASE) 
            for p in self.config.get('include_patterns', [])
        ]
        self.exclude_sources: Set[str] = set(self.config.get('exclude_sources', []))
        self.include_sources: Set[str] = set(self.config.get('include_sources', []))
        self.min_severity_score = self.config.get('min_severity_score', 0)
    
    def should_process(self, event: Dict[str, Any]) -> bool:
        """判断是否应该处理该事件"""
        level = event.get('level', 'INFO').upper()
        
        if self.include_levels and level not in self.include_levels:
            return False
        
        source = event.get('source', '')
        if self.include_sources and source not in self.include_sources:
            return False
        if source in self.exclude_sources:
            return False
        
        message = event.get('message', '')
        
        if self.include_patterns:
            if not any(p.search(message) for p in self.include_patterns):
                return False
        
        if any(p.search(message) for p in self.exclude_patterns):
            return False
        
        severity_score = self._calculate_severity(event)
        if severity_score < self.min_severity_score:
            return False
        
        return True
    
    def _calculate_severity(self, event: Dict[str, Any]) -> int:
        """计算事件严重程度分数"""
        score = 0
        level = event.get('level', 'INFO').upper()
        message = event.get('message', '').lower()
        
        level_scores = {
            'DEBUG': 1, 'INFO': 2, 'WARNING': 4, 'WARN': 4,
            'ERROR': 8, 'CRITICAL': 16, 'FATAL': 32
        }
        score = level_scores.get(level, 0)
        
        severity_keywords = [
            ('exception', 3), ('error', 2), ('fail', 2),
            ('timeout', 2), ('crash', 4), ('fatal', 5),
            ('security', 3), ('breach', 4), ('attack', 5)
        ]
        
        for keyword, weight in severity_keywords:
            if keyword in message:
                score += weight
        
        return score
    
    def add_exclude_pattern(self, pattern: str) -> None:
        """添加排除模式"""
        self.exclude_patterns.append(re.compile(pattern, re.IGNORECASE))
    
    def add_include_pattern(self, pattern: str) -> None:
        """添加包含模式"""
        self.include_patterns.append(re.compile(pattern, re.IGNORECASE))


class AnomalyDetectorBase(ABC):
    @abstractmethod
    def detect(self, events: List[Dict[str, Any]]) -> DetectionResult:
        pass

    @abstractmethod
    def update_baseline(self, events: List[Dict[str, Any]]) -> None:
        pass

    @abstractmethod
    def get_statistics(self) -> Dict[str, Any]:
        pass


class ErrorSpikeDetector(AnomalyDetectorBase):
    def __init__(
        self,
        window_size: int = 60,
        threshold_multiplier: float = 3.0,
        min_samples: int = 10
    ):
        self.window_size = window_size
        self.threshold_multiplier = threshold_multiplier
        self.min_samples = min_samples
        self.error_counts: deque = deque(maxlen=1000)
        self.baseline_mean: float = 0.0
        self.baseline_std: float = 0.0
        self._detection_count: int = 0

    def detect(self, events: List[Dict[str, Any]]) -> DetectionResult:
        error_events = [e for e in events if e.get('level', '').upper() in ['ERROR', 'CRITICAL', 'FATAL']]

        if len(error_events) < self.min_samples:
            return DetectionResult(
                detected=False,
                anomaly_type=AnomalyType.ERROR_SPIKE,
                confidence=0.0,
                details={"reason": "样本数不足"},
                events=[]
            )

        current_count = len(error_events)

        if self.baseline_mean > 0:
            threshold = self.baseline_mean + self.baseline_std * self.threshold_multiplier

            if current_count > threshold:
                confidence = min(1.0, (current_count - threshold) / threshold)
                self._detection_count += 1
                return DetectionResult(
                    detected=True,
                    anomaly_type=AnomalyType.ERROR_SPIKE,
                    confidence=confidence,
                    details={
                        "current_count": current_count,
                        "baseline_mean": self.baseline_mean,
                        "baseline_std": self.baseline_std,
                        "threshold": threshold,
                        "spike_ratio": current_count / self.baseline_mean if self.baseline_mean > 0 else 0
                    },
                    events=error_events[-20:]
                )

        return DetectionResult(
            detected=False,
            anomaly_type=AnomalyType.ERROR_SPIKE,
            confidence=0.0,
            details={"current_count": current_count},
            events=[]
        )

    def update_baseline(self, events: List[Dict[str, Any]]) -> None:
        error_events = [e for e in events if e.get('level', '').upper() in ['ERROR', 'CRITICAL', 'FATAL']]
        self.error_counts.append(len(error_events))

        if len(self.error_counts) >= self.min_samples:
            counts = list(self.error_counts)
            self.baseline_mean = sum(counts) / len(counts)
            variance = sum((c - self.baseline_mean) ** 2 for c in counts) / len(counts)
            self.baseline_std = variance ** 0.5

    def get_statistics(self) -> Dict[str, Any]:
        return {
            "detector_type": "error_spike",
            "baseline_mean": self.baseline_mean,
            "baseline_std": self.baseline_std,
            "sample_count": len(self.error_counts),
            "detection_count": self._detection_count
        }


class LatencySpikeDetector(AnomalyDetectorBase):
    def __init__(
        self,
        threshold_ms: float = 5000.0,
        percentile: float = 95.0,
        min_samples: int = 10
    ):
        self.threshold_ms = threshold_ms
        self.percentile = percentile
        self.min_samples = min_samples
        self.latencies: deque = deque(maxlen=1000)
        self.baseline_p95: float = 0.0
        self._detection_count: int = 0

    def detect(self, events: List[Dict[str, Any]]) -> DetectionResult:
        latency_events = []
        for event in events:
            latency = event.get('latency', event.get('duration', event.get('response_time')))
            if latency is not None:
                try:
                    latency_ms = float(latency)
                    latency_events.append((event, latency_ms))
                except (ValueError, TypeError):
                    continue

        if len(latency_events) < self.min_samples:
            return DetectionResult(
                detected=False,
                anomaly_type=AnomalyType.LATENCY_SPIKE,
                confidence=0.0,
                details={"reason": "样本数不足"},
                events=[]
            )

        latencies = [l for _, l in latency_events]
        current_p95 = self._percentile(latencies, self.percentile)

        if self.baseline_p95 > 0:
            threshold = max(self.threshold_ms, self.baseline_p95 * 2)

            if current_p95 > threshold:
                confidence = min(1.0, (current_p95 - threshold) / threshold)
                self._detection_count += 1
                return DetectionResult(
                    detected=True,
                    anomaly_type=AnomalyType.LATENCY_SPIKE,
                    confidence=confidence,
                    details={
                        "current_p95": current_p95,
                        "baseline_p95": self.baseline_p95,
                        "threshold": threshold,
                        "max_latency": max(latencies),
                        "avg_latency": sum(latencies) / len(latencies)
                    },
                    events=[e for e, _ in latency_events[-20:]]
                )

        return DetectionResult(
            detected=False,
            anomaly_type=AnomalyType.LATENCY_SPIKE,
            confidence=0.0,
            details={"current_p95": current_p95},
            events=[]
        )

    def update_baseline(self, events: List[Dict[str, Any]]) -> None:
        for event in events:
            latency = event.get('latency', event.get('duration', event.get('response_time')))
            if latency is not None:
                try:
                    self.latencies.append(float(latency))
                except (ValueError, TypeError):
                    continue

        if len(self.latencies) >= self.min_samples:
            self.baseline_p95 = self._percentile(list(self.latencies), self.percentile)

    def _percentile(self, data: List[float], p: float) -> float:
        if not data:
            return 0.0
        sorted_data = sorted(data)
        k = (len(sorted_data) - 1) * p / 100
        f = int(k)
        c = f + 1 if f + 1 < len(sorted_data) else f
        return sorted_data[f] + (k - f) * (sorted_data[c] - sorted_data[f])

    def get_statistics(self) -> Dict[str, Any]:
        return {
            "detector_type": "latency_spike",
            "baseline_p95": self.baseline_p95,
            "sample_count": len(self.latencies),
            "detection_count": self._detection_count
        }


class PatternDeviationDetector(AnomalyDetectorBase):
    def __init__(
        self,
        min_frequency: int = 5,
        deviation_threshold: float = 0.5
    ):
        self.min_frequency = min_frequency
        self.deviation_threshold = deviation_threshold
        self.pattern_counts: Dict[str, int] = defaultdict(int)
        self.total_patterns: int = 0
        self.pattern_distribution: Dict[str, float] = {}
        self._detection_count: int = 0

    def detect(self, events: List[Dict[str, Any]]) -> DetectionResult:
        current_patterns: Dict[str, int] = defaultdict(int)

        for event in events:
            pattern = self._extract_pattern(event.get('message', ''))
            current_patterns[pattern] += 1

        if not self.pattern_distribution:
            return DetectionResult(
                detected=False,
                anomaly_type=AnomalyType.PATTERN_DEVIATION,
                confidence=0.0,
                details={"reason": "基线未建立"},
                events=[]
            )

        deviations = []
        current_total = sum(current_patterns.values())

        if current_total == 0:
            return DetectionResult(
                detected=False,
                anomaly_type=AnomalyType.PATTERN_DEVIATION,
                confidence=0.0,
                details={"reason": "无事件"},
                events=[]
            )

        for pattern, count in current_patterns.items():
            current_freq = count / current_total
            baseline_freq = self.pattern_distribution.get(pattern, 0.0)

            if baseline_freq > 0:
                deviation = abs(current_freq - baseline_freq) / baseline_freq
                if deviation > self.deviation_threshold:
                    deviations.append({
                        "pattern": pattern[:50],
                        "current_frequency": current_freq,
                        "baseline_frequency": baseline_freq,
                        "deviation": deviation
                    })

        if deviations:
            max_deviation = max(d['deviation'] for d in deviations)
            confidence = min(1.0, max_deviation)
            self._detection_count += 1

            return DetectionResult(
                detected=True,
                anomaly_type=AnomalyType.PATTERN_DEVIATION,
                confidence=confidence,
                details={
                    "deviations": deviations[:10],
                    "total_patterns": len(current_patterns)
                },
                events=events[-20:]
            )

        return DetectionResult(
            detected=False,
            anomaly_type=AnomalyType.PATTERN_DEVIATION,
            confidence=0.0,
            details={},
            events=[]
        )

    def update_baseline(self, events: List[Dict[str, Any]]) -> None:
        for event in events:
            pattern = self._extract_pattern(event.get('message', ''))
            self.pattern_counts[pattern] += 1
            self.total_patterns += 1

        if self.total_patterns > 0:
            self.pattern_distribution = {
                p: c / self.total_patterns
                for p, c in self.pattern_counts.items()
            }

    def _extract_pattern(self, message: str) -> str:
        normalized = re.sub(r'\d+', 'N', message)
        normalized = re.sub(r'0x[a-fA-F0-9]+', 'HEX', normalized)
        normalized = re.sub(r'[a-fA-F0-9]{8}-[a-fA-F0-9]{4}-[a-fA-F0-9]{4}-[a-fA-F0-9]{4}-[a-fA-F0-9]{12}', 'UUID', normalized)
        normalized = re.sub(r'/[\w/]+', '/PATH', normalized)
        normalized = re.sub(r'\s+', ' ', normalized).strip()
        return normalized[:100]

    def get_statistics(self) -> Dict[str, Any]:
        return {
            "detector_type": "pattern_deviation",
            "total_patterns": len(self.pattern_counts),
            "total_events": self.total_patterns,
            "detection_count": self._detection_count
        }


class FrequencyAnomalyDetector(AnomalyDetectorBase):
    def __init__(
        self,
        window_size: int = 300,
        threshold_multiplier: float = 3.0
    ):
        self.window_size = window_size
        self.threshold_multiplier = threshold_multiplier
        self.frequency_history: deque = deque(maxlen=100)
        self.baseline_mean: float = 0.0
        self.baseline_std: float = 0.0
        self._detection_count: int = 0

    def detect(self, events: List[Dict[str, Any]]) -> DetectionResult:
        if not events:
            return DetectionResult(
                detected=False,
                anomaly_type=AnomalyType.FREQUENCY_ANOMALY,
                confidence=0.0,
                details={"reason": "无事件"},
                events=[]
            )

        current_frequency = len(events)

        if self.baseline_mean > 0:
            threshold = self.baseline_mean + self.baseline_std * self.threshold_multiplier

            if current_frequency > threshold:
                confidence = min(1.0, (current_frequency - threshold) / threshold)
                self._detection_count += 1
                return DetectionResult(
                    detected=True,
                    anomaly_type=AnomalyType.FREQUENCY_ANOMALY,
                    confidence=confidence,
                    details={
                        "current_frequency": current_frequency,
                        "baseline_mean": self.baseline_mean,
                        "threshold": threshold,
                        "anomaly_direction": "high"
                    },
                    events=events[-20:]
                )

            lower_threshold = max(0, self.baseline_mean - self.baseline_std * self.threshold_multiplier)
            if current_frequency < lower_threshold:
                confidence = min(1.0, (lower_threshold - current_frequency) / lower_threshold) if lower_threshold > 0 else 0.5
                self._detection_count += 1
                return DetectionResult(
                    detected=True,
                    anomaly_type=AnomalyType.FREQUENCY_ANOMALY,
                    confidence=confidence,
                    details={
                        "current_frequency": current_frequency,
                        "baseline_mean": self.baseline_mean,
                        "lower_threshold": lower_threshold,
                        "anomaly_direction": "low"
                    },
                    events=events[-20:]
                )

        return DetectionResult(
            detected=False,
            anomaly_type=AnomalyType.FREQUENCY_ANOMALY,
            confidence=0.0,
            details={"current_frequency": current_frequency},
            events=[]
        )

    def update_baseline(self, events: List[Dict[str, Any]]) -> None:
        self.frequency_history.append(len(events))

        if len(self.frequency_history) >= 10:
            frequencies = list(self.frequency_history)
            self.baseline_mean = sum(frequencies) / len(frequencies)
            variance = sum((f - self.baseline_mean) ** 2 for f in frequencies) / len(frequencies)
            self.baseline_std = variance ** 0.5

    def get_statistics(self) -> Dict[str, Any]:
        return {
            "detector_type": "frequency_anomaly",
            "baseline_mean": self.baseline_mean,
            "baseline_std": self.baseline_std,
            "sample_count": len(self.frequency_history),
            "detection_count": self._detection_count
        }


class SecurityAnomalyDetector(AnomalyDetectorBase):
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.suspicious_patterns = [
            (r'password\s*[=:]\s*\S+', '密码泄露风险'),
            (r'api[_-]?key\s*[=:]\s*\S+', 'API密钥泄露风险'),
            (r'secret\s*[=:]\s*\S+', '密钥泄露风险'),
            (r'token\s*[=:]\s*\S+', '令牌泄露风险'),
            (r'sql\s*injection', 'SQL注入尝试'),
            (r'xss|cross.?site.?scripting', 'XSS攻击尝试'),
            (r'authentication\s*failed', '认证失败'),
            (r'unauthorized\s*access', '未授权访问'),
            (r'brute.?force', '暴力破解尝试'),
        ]
        self._compiled_patterns = [
            (re.compile(p, re.IGNORECASE), desc) for p, desc in self.suspicious_patterns
        ]
        self._detection_count: int = 0
        self._alerts_by_type: Dict[str, int] = defaultdict(int)

    def detect(self, events: List[Dict[str, Any]]) -> DetectionResult:
        security_events = []

        for event in events:
            message = event.get('message', '')
            for pattern, description in self._compiled_patterns:
                if pattern.search(message):
                    security_events.append({
                        "event": event,
                        "type": description,
                        "pattern": pattern.pattern
                    })
                    self._alerts_by_type[description] += 1
                    break

        if security_events:
            self._detection_count += 1
            return DetectionResult(
                detected=True,
                anomaly_type=AnomalyType.SECURITY_ANOMALY,
                confidence=0.9,
                details={
                    "security_events": [
                        {
                            "type": e["type"],
                            "message": e["event"].get("message", "")[:100]
                        }
                        for e in security_events[:10]
                    ],
                    "total_count": len(security_events)
                },
                events=[e["event"] for e in security_events[:20]]
            )

        return DetectionResult(
            detected=False,
            anomaly_type=AnomalyType.SECURITY_ANOMALY,
            confidence=0.0,
            details={},
            events=[]
        )

    def update_baseline(self, events: List[Dict[str, Any]]) -> None:
        pass

    def get_statistics(self) -> Dict[str, Any]:
        return {
            "detector_type": "security_anomaly",
            "detection_count": self._detection_count,
            "alerts_by_type": dict(self._alerts_by_type)
        }


class ResourceExhaustionDetector(AnomalyDetectorBase):
    """资源耗尽检测器 - 检测系统资源耗尽情况"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.resource_patterns = [
            (r'out\s*of\s*memory|oom|memory\s*exhausted', 'memory'),
            (r'disk\s*full|no\s*space\s*left|storage\s*exhausted', 'disk'),
            (r'too\s*many\s*open\s*files|file\s*descriptor', 'file_descriptor'),
            (r'connection\s*pool\s*exhausted|no\s*available\s*connection', 'connection_pool'),
            (r'thread\s*pool\s*exhausted|no\s*available\s*thread', 'thread_pool'),
            (r'cpu\s*overload|high\s*cpu\s*usage', 'cpu'),
        ]
        self._compiled_patterns = [
            (re.compile(p, re.IGNORECASE), resource) for p, resource in self.resource_patterns
        ]
        self._detection_count: int = 0
        self._alerts_by_resource: Dict[str, int] = defaultdict(int)

    def detect(self, events: List[Dict[str, Any]]) -> DetectionResult:
        resource_events = []

        for event in events:
            message = event.get('message', '')
            for pattern, resource in self._compiled_patterns:
                if pattern.search(message):
                    resource_events.append({
                        "event": event,
                        "resource": resource
                    })
                    self._alerts_by_resource[resource] += 1
                    break

        if resource_events:
            self._detection_count += 1
            return DetectionResult(
                detected=True,
                anomaly_type=AnomalyType.RESOURCE_EXHAUSTION,
                confidence=0.85,
                details={
                    "resource_events": [
                        {
                            "resource": e["resource"],
                            "message": e["event"].get("message", "")[:100]
                        }
                        for e in resource_events[:10]
                    ],
                    "total_count": len(resource_events),
                    "resources_affected": list(set(e["resource"] for e in resource_events))
                },
                events=[e["event"] for e in resource_events[:20]]
            )

        return DetectionResult(
            detected=False,
            anomaly_type=AnomalyType.RESOURCE_EXHAUSTION,
            confidence=0.0,
            details={},
            events=[]
        )

    def update_baseline(self, events: List[Dict[str, Any]]) -> None:
        pass

    def get_statistics(self) -> Dict[str, Any]:
        return {
            "detector_type": "resource_exhaustion",
            "detection_count": self._detection_count,
            "alerts_by_resource": dict(self._alerts_by_resource)
        }


class SequenceAnomalyDetector(AnomalyDetectorBase):
    """序列异常检测器 - 检测日志事件序列中的异常模式"""
    
    def __init__(
        self,
        min_sequence_length: int = 3,
        max_sequence_length: int = 10,
        anomaly_threshold: float = 0.3
    ):
        self.min_sequence_length = min_sequence_length
        self.max_sequence_length = max_sequence_length
        self.anomaly_threshold = anomaly_threshold
        self.sequence_counts: Dict[str, int] = defaultdict(int)
        self.total_sequences: int = 0
        self._detection_count: int = 0
        self._recent_events: deque = deque(maxlen=1000)
        
        self._critical_sequences = [
            ['ERROR', 'ERROR', 'ERROR'],
            ['WARNING', 'ERROR', 'CRITICAL'],
            ['INFO', 'WARNING', 'ERROR', 'CRITICAL'],
            ['FATAL', 'FATAL'],
        ]
        self._compiled_critical = [
            [re.compile(f'\\b{lvl}\\b', re.IGNORECASE) for lvl in seq]
            for seq in self._critical_sequences
        ]
    
    def detect(self, events: List[Dict[str, Any]]) -> DetectionResult:
        if len(events) < self.min_sequence_length:
            return DetectionResult(
                detected=False,
                anomaly_type=AnomalyType.SEQUENCE_ANOMALY,
                confidence=0.0,
                details={"reason": "事件数量不足"},
                events=[]
            )
        
        levels = []
        for event in events:
            level = event.get('level', 'INFO').upper()
            levels.append(level)
        
        sequence_anomalies = []
        
        for i, critical_seq in enumerate(self._critical_sequences):
            for j in range(len(levels) - len(critical_seq) + 1):
                window = levels[j:j + len(critical_seq)]
                if window == critical_seq:
                    sequence_anomalies.append({
                        "sequence": critical_seq,
                        "position": j,
                        "severity": len(critical_seq)
                    })
        
        rare_sequences = self._detect_rare_sequences(levels)
        sequence_anomalies.extend(rare_sequences)
        
        if sequence_anomalies:
            max_severity = max(a.get("severity", 1) for a in sequence_anomalies)
            confidence = min(1.0, max_severity / 5.0)
            self._detection_count += 1
            
            return DetectionResult(
                detected=True,
                anomaly_type=AnomalyType.SEQUENCE_ANOMALY,
                confidence=confidence,
                details={
                    "sequence_anomalies": sequence_anomalies[:10],
                    "total_anomalies": len(sequence_anomalies),
                    "max_severity": max_severity
                },
                events=events[-20:]
            )
        
        return DetectionResult(
            detected=False,
            anomaly_type=AnomalyType.SEQUENCE_ANOMALY,
            confidence=0.0,
            details={},
            events=[]
        )
    
    def _detect_rare_sequences(self, levels: List[str]) -> List[Dict[str, Any]]:
        anomalies = []
        
        for length in range(self.min_sequence_length, min(len(levels) + 1, self.max_sequence_length + 1)):
            for i in range(len(levels) - length + 1):
                seq = tuple(levels[i:i + length])
                seq_key = str(seq)
                
                if self.total_sequences > 0:
                    freq = self.sequence_counts.get(seq_key, 0) / self.total_sequences
                    if freq < self.anomaly_threshold and freq > 0:
                        anomalies.append({
                            "sequence": list(seq),
                            "position": i,
                            "frequency": freq,
                            "severity": int(1.0 / freq) if freq > 0 else 10
                        })
        
        return anomalies
    
    def update_baseline(self, events: List[Dict[str, Any]]) -> None:
        self._recent_events.extend(events)
        
        levels = [e.get('level', 'INFO').upper() for e in events]
        
        for length in range(self.min_sequence_length, min(len(levels) + 1, self.max_sequence_length + 1)):
            for i in range(len(levels) - length + 1):
                seq = tuple(levels[i:i + length])
                self.sequence_counts[str(seq)] += 1
                self.total_sequences += 1
    
    def get_statistics(self) -> Dict[str, Any]:
        return {
            "detector_type": "sequence_anomaly",
            "total_sequences": self.total_sequences,
            "unique_sequences": len(self.sequence_counts),
            "detection_count": self._detection_count
        }


class BehavioralAnomalyDetector(AnomalyDetectorBase):
    """行为异常检测器 - 检测系统行为的异常变化"""
    
    def __init__(
        self,
        learning_period: int = 1000,
        anomaly_threshold: float = 2.5
    ):
        self.learning_period = learning_period
        self.anomaly_threshold = anomaly_threshold
        self._event_types: Dict[str, int] = defaultdict(int)
        self._source_distribution: Dict[str, int] = defaultdict(int)
        self._hourly_distribution: Dict[int, int] = defaultdict(int)
        self._level_distribution: Dict[str, int] = defaultdict(int)
        self._total_events: int = 0
        self._detection_count: int = 0
        self._baseline_established: bool = False
        self._baseline_event_freq: float = 0.0
        self._baseline_source_entropy: float = 0.0
        self._baseline_level_entropy: float = 0.0
    
    def detect(self, events: List[Dict[str, Any]]) -> DetectionResult:
        if not self._baseline_established:
            return DetectionResult(
                detected=False,
                anomaly_type=AnomalyType.BEHAVIORAL_ANOMALY,
                confidence=0.0,
                details={"reason": "基线尚未建立"},
                events=[]
            )
        
        anomalies = []
        
        current_event_freq = len(events)
        if self._baseline_event_freq > 0:
            freq_deviation = abs(current_event_freq - self._baseline_event_freq) / self._baseline_event_freq
            if freq_deviation > self.anomaly_threshold:
                anomalies.append({
                    "type": "frequency_deviation",
                    "current": current_event_freq,
                    "baseline": self._baseline_event_freq,
                    "deviation": freq_deviation
                })
        
        current_source_dist: Dict[str, int] = defaultdict(int)
        for event in events:
            source = event.get('source', event.get('file', 'unknown'))
            current_source_dist[source] += 1
        
        current_source_entropy = self._calculate_entropy(current_source_dist)
        if self._baseline_source_entropy > 0:
            entropy_deviation = abs(current_source_entropy - self._baseline_source_entropy)
            if entropy_deviation > 1.0:
                anomalies.append({
                    "type": "source_distribution_change",
                    "current_entropy": current_source_entropy,
                    "baseline_entropy": self._baseline_source_entropy,
                    "deviation": entropy_deviation
                })
        
        current_level_dist: Dict[str, int] = defaultdict(int)
        for event in events:
            level = event.get('level', 'INFO').upper()
            current_level_dist[level] += 1
        
        current_level_entropy = self._calculate_entropy(current_level_dist)
        if self._baseline_level_entropy > 0:
            entropy_deviation = abs(current_level_entropy - self._baseline_level_entropy)
            if entropy_deviation > 0.5:
                anomalies.append({
                    "type": "level_distribution_change",
                    "current_entropy": current_level_entropy,
                    "baseline_entropy": self._baseline_level_entropy,
                    "deviation": entropy_deviation
                })
        
        new_sources = set(current_source_dist.keys()) - set(self._source_distribution.keys())
        if new_sources:
            anomalies.append({
                "type": "new_sources",
                "sources": list(new_sources)[:10]
            })
        
        if anomalies:
            max_deviation = max(
                a.get("deviation", 1.0) for a in anomalies if "deviation" in a
            ) if anomalies else 1.0
            confidence = min(1.0, max_deviation / self.anomaly_threshold)
            self._detection_count += 1
            
            return DetectionResult(
                detected=True,
                anomaly_type=AnomalyType.BEHAVIORAL_ANOMALY,
                confidence=confidence,
                details={
                    "anomalies": anomalies,
                    "total_anomalies": len(anomalies)
                },
                events=events[-20:]
            )
        
        return DetectionResult(
            detected=False,
            anomaly_type=AnomalyType.BEHAVIORAL_ANOMALY,
            confidence=0.0,
            details={},
            events=[]
        )
    
    def _calculate_entropy(self, distribution: Dict[str, int]) -> float:
        total = sum(distribution.values())
        if total == 0:
            return 0.0
        
        entropy = 0.0
        for count in distribution.values():
            if count > 0:
                p = count / total
                entropy -= p * (p and __import__('math').log2(p))
        
        return entropy
    
    def update_baseline(self, events: List[Dict[str, Any]]) -> None:
        for event in events:
            self._event_types[event.get('type', 'default')] += 1
            source = event.get('source', event.get('file', 'unknown'))
            self._source_distribution[source] += 1
            
            timestamp = event.get('timestamp', '')
            if isinstance(timestamp, str):
                try:
                    hour = int(timestamp[11:13]) if len(timestamp) >= 13 else 0
                except (ValueError, IndexError):
                    hour = 0
            else:
                hour = datetime.now().hour
            self._hourly_distribution[hour] += 1
            
            level = event.get('level', 'INFO').upper()
            self._level_distribution[level] += 1
            
            self._total_events += 1
        
        if self._total_events >= self.learning_period:
            self._baseline_established = True
            self._baseline_event_freq = self._total_events / max(len(self._hourly_distribution), 1)
            self._baseline_source_entropy = self._calculate_entropy(self._source_distribution)
            self._baseline_level_entropy = self._calculate_entropy(self._level_distribution)
    
    def get_statistics(self) -> Dict[str, Any]:
        return {
            "detector_type": "behavioral_anomaly",
            "total_events": self._total_events,
            "baseline_established": self._baseline_established,
            "unique_sources": len(self._source_distribution),
            "detection_count": self._detection_count
        }


class ThresholdBreachDetector(AnomalyDetectorBase):
    """阈值违规检测器 - 检测指标是否超过预设阈值"""
    
    def __init__(self, thresholds: Optional[Dict[str, Dict[str, float]]] = None):
        self.thresholds = thresholds or {
            "error_rate": {"warning": 0.05, "critical": 0.10},
            "response_time_ms": {"warning": 1000, "critical": 5000},
            "memory_usage_percent": {"warning": 80, "critical": 95},
            "cpu_usage_percent": {"warning": 80, "critical": 95},
            "queue_depth": {"warning": 100, "critical": 500},
        }
        self._detection_count: int = 0
        self._breach_history: List[Dict[str, Any]] = []
        self._breach_counts: Dict[str, int] = defaultdict(int)
    
    def detect(self, events: List[Dict[str, Any]]) -> DetectionResult:
        breaches = []
        
        for event in events:
            metrics = event.get('metrics', {})
            if not metrics:
                metrics = self._extract_metrics_from_event(event)
            
            for metric_name, value in metrics.items():
                if metric_name in self.thresholds:
                    threshold_config = self.thresholds[metric_name]
                    
                    if "critical" in threshold_config and value >= threshold_config["critical"]:
                        breaches.append({
                            "metric": metric_name,
                            "value": value,
                            "threshold": threshold_config["critical"],
                            "level": "critical",
                            "event": event
                        })
                        self._breach_counts[f"{metric_name}_critical"] += 1
                    elif "warning" in threshold_config and value >= threshold_config["warning"]:
                        breaches.append({
                            "metric": metric_name,
                            "value": value,
                            "threshold": threshold_config["warning"],
                            "level": "warning",
                            "event": event
                        })
                        self._breach_counts[f"{metric_name}_warning"] += 1
        
        if breaches:
            critical_breaches = [b for b in breaches if b["level"] == "critical"]
            confidence = 0.9 if critical_breaches else 0.7
            self._detection_count += 1
            
            self._breach_history.extend(breaches[-100:])
            
            return DetectionResult(
                detected=True,
                anomaly_type=AnomalyType.THRESHOLD_BREACH,
                confidence=confidence,
                details={
                    "breaches": [
                        {
                            "metric": b["metric"],
                            "value": b["value"],
                            "threshold": b["threshold"],
                            "level": b["level"]
                        }
                        for b in breaches[:10]
                    ],
                    "total_breaches": len(breaches),
                    "critical_count": len(critical_breaches)
                },
                events=[b["event"] for b in breaches[:20]]
            )
        
        return DetectionResult(
            detected=False,
            anomaly_type=AnomalyType.THRESHOLD_BREACH,
            confidence=0.0,
            details={},
            events=[]
        )
    
    def _extract_metrics_from_event(self, event: Dict[str, Any]) -> Dict[str, float]:
        metrics = {}
        message = event.get('message', '')
        
        latency_match = re.search(r'(?:latency|duration|response.?time)[:\s]+(\d+(?:\.\d+)?)', message, re.IGNORECASE)
        if latency_match:
            metrics['response_time_ms'] = float(latency_match.group(1))
        
        memory_match = re.search(r'memory[:\s]+(\d+(?:\.\d+)?)\s*%', message, re.IGNORECASE)
        if memory_match:
            metrics['memory_usage_percent'] = float(memory_match.group(1))
        
        cpu_match = re.search(r'cpu[:\s]+(\d+(?:\.\d+)?)\s*%', message, re.IGNORECASE)
        if cpu_match:
            metrics['cpu_usage_percent'] = float(cpu_match.group(1))
        
        queue_match = re.search(r'queue[:\s]+(\d+)', message, re.IGNORECASE)
        if queue_match:
            metrics['queue_depth'] = float(queue_match.group(1))
        
        return metrics
    
    def update_baseline(self, events: List[Dict[str, Any]]) -> None:
        pass
    
    def add_threshold(self, metric_name: str, warning: float, critical: float) -> None:
        self.thresholds[metric_name] = {"warning": warning, "critical": critical}
    
    def get_statistics(self) -> Dict[str, Any]:
        return {
            "detector_type": "threshold_breach",
            "detection_count": self._detection_count,
            "breach_counts": dict(self._breach_counts),
            "configured_thresholds": list(self.thresholds.keys())
        }


class CorrelationAnomalyDetector(AnomalyDetectorBase):
    """关联异常检测器 - 检测事件之间的异常关联关系"""
    
    def __init__(
        self,
        time_window_seconds: int = 60,
        min_correlation_strength: float = 0.7
    ):
        self.time_window_seconds = time_window_seconds
        self.min_correlation_strength = min_correlation_strength
        self._event_pairs: Dict[Tuple[str, str], int] = defaultdict(int)
        self._event_counts: Dict[str, int] = defaultdict(int)
        self._total_pairs: int = 0
        self._detection_count: int = 0
        self._known_correlations: Dict[Tuple[str, str], float] = {}
        
        self._critical_correlations = [
            ("authentication failed", "unauthorized access"),
            ("connection timeout", "service unavailable"),
            ("memory warning", "out of memory"),
            ("high latency", "request timeout"),
            ("disk space low", "write failed"),
        ]
    
    def detect(self, events: List[Dict[str, Any]]) -> DetectionResult:
        if len(events) < 2:
            return DetectionResult(
                detected=False,
                anomaly_type=AnomalyType.CORRELATION_ANOMALY,
                confidence=0.0,
                details={"reason": "事件数量不足"},
                events=[]
            )
        
        correlation_anomalies = []
        
        sorted_events = sorted(
            events,
            key=lambda e: e.get('timestamp', '')
        )
        
        for i, event1 in enumerate(sorted_events):
            msg1 = event1.get('message', '').lower()
            event1_type = self._extract_event_type(msg1)
            
            for event2 in sorted_events[i + 1:]:
                msg2 = event2.get('message', '').lower()
                event2_type = self._extract_event_type(msg2)
                
                for critical_pair in self._critical_correlations:
                    if (critical_pair[0] in msg1 and critical_pair[1] in msg2) or \
                       (critical_pair[1] in msg1 and critical_pair[0] in msg2):
                        correlation_anomalies.append({
                            "type": "critical_correlation",
                            "pattern": critical_pair,
                            "event1": event1,
                            "event2": event2,
                            "severity": "high"
                        })
        
        for i, event1 in enumerate(sorted_events):
            event1_type = self._extract_event_type(event1.get('message', '').lower())
            
            for event2 in sorted_events[i + 1:]:
                event2_type = self._extract_event_type(event2.get('message', '').lower())
                
                pair = (event1_type, event2_type)
                if pair in self._known_correlations:
                    expected_strength = self._known_correlations[pair]
                    current_strength = self._event_pairs.get(pair, 0) / max(self._total_pairs, 1)
                    
                    if abs(current_strength - expected_strength) > 0.3:
                        correlation_anomalies.append({
                            "type": "correlation_deviation",
                            "pair": pair,
                            "expected": expected_strength,
                            "actual": current_strength,
                            "severity": "medium"
                        })
        
        if correlation_anomalies:
            high_severity = any(a["severity"] == "high" for a in correlation_anomalies)
            confidence = 0.9 if high_severity else 0.7
            self._detection_count += 1
            
            return DetectionResult(
                detected=True,
                anomaly_type=AnomalyType.CORRELATION_ANOMALY,
                confidence=confidence,
                details={
                    "correlation_anomalies": [
                        {
                            "type": a["type"],
                            "severity": a["severity"],
                            "details": {k: v for k, v in a.items() if k not in ["event1", "event2"]}
                        }
                        for a in correlation_anomalies[:10]
                    ],
                    "total_anomalies": len(correlation_anomalies)
                },
                events=events[-20:]
            )
        
        return DetectionResult(
            detected=False,
            anomaly_type=AnomalyType.CORRELATION_ANOMALY,
            confidence=0.0,
            details={},
            events=[]
        )
    
    def _extract_event_type(self, message: str) -> str:
        message = message.lower()
        
        if 'error' in message:
            return 'error'
        elif 'warning' in message or 'warn' in message:
            return 'warning'
        elif 'timeout' in message:
            return 'timeout'
        elif 'failed' in message or 'failure' in message:
            return 'failure'
        elif 'exception' in message:
            return 'exception'
        elif 'slow' in message:
            return 'slow'
        else:
            return 'other'
    
    def update_baseline(self, events: List[Dict[str, Any]]) -> None:
        sorted_events = sorted(
            events,
            key=lambda e: e.get('timestamp', '')
        )
        
        for i, event1 in enumerate(sorted_events):
            event1_type = self._extract_event_type(event1.get('message', '').lower())
            self._event_counts[event1_type] += 1
            
            for event2 in sorted_events[i + 1:]:
                event2_type = self._extract_event_type(event2.get('message', '').lower())
                
                pair = (event1_type, event2_type)
                self._event_pairs[pair] += 1
                self._total_pairs += 1
        
        if self._total_pairs > 100:
            for pair, count in self._event_pairs.items():
                self._known_correlations[pair] = count / self._total_pairs
    
    def get_statistics(self) -> Dict[str, Any]:
        return {
            "detector_type": "correlation_anomaly",
            "total_pairs": self._total_pairs,
            "unique_pairs": len(self._event_pairs),
            "known_correlations": len(self._known_correlations),
            "detection_count": self._detection_count
        }


class ServiceDegradationDetector(AnomalyDetectorBase):
    """服务降级检测器 - 检测服务性能降级"""
    
    def __init__(
        self,
        degradation_threshold: float = 0.3,
        window_size: int = 10
    ):
        self.degradation_threshold = degradation_threshold
        self.window_size = window_size
        self._latency_history: deque = deque(maxlen=100)
        self._error_rate_history: deque = deque(maxlen=100)
        self._throughput_history: deque = deque(maxlen=100)
        self._baseline_latency: float = 0.0
        self._baseline_error_rate: float = 0.0
        self._baseline_throughput: float = 0.0
        self._detection_count: int = 0
        self._degradation_events: List[Dict[str, Any]] = []
    
    def detect(self, events: List[Dict[str, Any]]) -> DetectionResult:
        current_latency = self._calculate_avg_latency(events)
        current_error_rate = self._calculate_error_rate(events)
        current_throughput = len(events)
        
        degradations = []
        
        if self._baseline_latency > 0:
            latency_increase = (current_latency - self._baseline_latency) / self._baseline_latency
            if latency_increase > self.degradation_threshold:
                degradations.append({
                    "type": "latency_degradation",
                    "current": current_latency,
                    "baseline": self._baseline_latency,
                    "increase_percent": latency_increase * 100
                })
        
        if self._baseline_error_rate >= 0:
            error_increase = current_error_rate - self._baseline_error_rate
            if error_increase > self.degradation_threshold:
                degradations.append({
                    "type": "error_rate_increase",
                    "current": current_error_rate,
                    "baseline": self._baseline_error_rate,
                    "increase": error_increase
                })
        
        if self._baseline_throughput > 0:
            throughput_decrease = (self._baseline_throughput - current_throughput) / self._baseline_throughput
            if throughput_decrease > self.degradation_threshold:
                degradations.append({
                    "type": "throughput_degradation",
                    "current": current_throughput,
                    "baseline": self._baseline_throughput,
                    "decrease_percent": throughput_decrease * 100
                })
        
        if degradations:
            max_severity = max(
                d.get("increase_percent", d.get("increase", d.get("decrease_percent", 0)))
                for d in degradations
            )
            confidence = min(1.0, max_severity / 100)
            self._detection_count += 1
            
            self._degradation_events.extend(degradations[-50:])
            
            return DetectionResult(
                detected=True,
                anomaly_type=AnomalyType.SERVICE_DEGRADATION,
                confidence=confidence,
                details={
                    "degradations": degradations,
                    "current_metrics": {
                        "latency": current_latency,
                        "error_rate": current_error_rate,
                        "throughput": current_throughput
                    },
                    "baseline_metrics": {
                        "latency": self._baseline_latency,
                        "error_rate": self._baseline_error_rate,
                        "throughput": self._baseline_throughput
                    }
                },
                events=events[-20:]
            )
        
        return DetectionResult(
            detected=False,
            anomaly_type=AnomalyType.SERVICE_DEGRADATION,
            confidence=0.0,
            details={},
            events=[]
        )
    
    def _calculate_avg_latency(self, events: List[Dict[str, Any]]) -> float:
        latencies = []
        for event in events:
            latency = event.get('latency', event.get('duration', event.get('response_time')))
            if latency is not None:
                try:
                    latencies.append(float(latency))
                except (ValueError, TypeError):
                    continue
        
        return sum(latencies) / len(latencies) if latencies else 0.0
    
    def _calculate_error_rate(self, events: List[Dict[str, Any]]) -> float:
        if not events:
            return 0.0
        
        error_count = sum(
            1 for e in events
            if e.get('level', '').upper() in ['ERROR', 'CRITICAL', 'FATAL']
        )
        
        return error_count / len(events)
    
    def update_baseline(self, events: List[Dict[str, Any]]) -> None:
        latency = self._calculate_avg_latency(events)
        if latency > 0:
            self._latency_history.append(latency)
        
        error_rate = self._calculate_error_rate(events)
        self._error_rate_history.append(error_rate)
        
        self._throughput_history.append(len(events))
        
        if len(self._latency_history) >= self.window_size:
            self._baseline_latency = sum(self._latency_history) / len(self._latency_history)
        
        if len(self._error_rate_history) >= self.window_size:
            self._baseline_error_rate = sum(self._error_rate_history) / len(self._error_rate_history)
        
        if len(self._throughput_history) >= self.window_size:
            self._baseline_throughput = sum(self._throughput_history) / len(self._throughput_history)
    
    def get_statistics(self) -> Dict[str, Any]:
        return {
            "detector_type": "service_degradation",
            "baseline_latency": self._baseline_latency,
            "baseline_error_rate": self._baseline_error_rate,
            "baseline_throughput": self._baseline_throughput,
            "detection_count": self._detection_count,
            "degradation_events_count": len(self._degradation_events)
        }


class AlertManager:
    """告警管理器 - 处理告警抑制、聚合和状态管理"""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.active_alerts: Dict[str, AnomalyAlert] = {}
        self.alert_history: List[AnomalyAlert] = []
        self.suppression_rules: Dict[str, datetime] = {}
        self._lock = threading.Lock()
        self._alert_counter = 0

    def process_alert(self, alert: AnomalyAlert) -> Optional[AnomalyAlert]:
        with self._lock:
            fingerprint = alert.fingerprint

            if fingerprint in self.suppression_rules:
                suppress_until = self.suppression_rules[fingerprint]
                if datetime.now() < suppress_until:
                    return None

            if fingerprint in self.active_alerts:
                existing_alert = self.active_alerts[fingerprint]
                existing_alert.occurrence_count += 1
                existing_alert.last_occurred = alert.timestamp
                existing_alert.related_alerts.append(alert.alert_id)
                return None

            self._alert_counter += 1
            alert.alert_id = f"ALERT-{datetime.now().strftime('%Y%m%d%H%M%S')}-{self._alert_counter:04d}"

            self.active_alerts[fingerprint] = alert
            self.alert_history.append(alert)

            suppression_window = self.config.get('suppression_window_seconds', 300)
            self.suppression_rules[fingerprint] = datetime.now() + timedelta(seconds=suppression_window)

            return alert

    def acknowledge_alert(self, alert_id: str) -> bool:
        with self._lock:
            for fingerprint, alert in self.active_alerts.items():
                if alert.alert_id == alert_id:
                    alert.acknowledged = True
                    alert.state = AlertState.ACKNOWLEDGED
                    return True
            return False

    def resolve_alert(self, alert_id: str) -> bool:
        with self._lock:
            for fingerprint, alert in list(self.active_alerts.items()):
                if alert.alert_id == alert_id:
                    alert.state = AlertState.RESOLVED
                    del self.active_alerts[fingerprint]
                    return True
            return False

    def auto_resolve_stale_alerts(self, max_age_seconds: int = 3600) -> List[str]:
        resolved_ids = []
        with self._lock:
            now = datetime.now()
            for fingerprint, alert in list(self.active_alerts.items()):
                if alert.last_occurred:
                    age = (now - alert.last_occurred).total_seconds()
                    if age > max_age_seconds:
                        alert.state = AlertState.RESOLVED
                        resolved_ids.append(alert.alert_id)
                        del self.active_alerts[fingerprint]
        return resolved_ids

    def get_active_alerts(self) -> List[AnomalyAlert]:
        with self._lock:
            return list(self.active_alerts.values())

    def get_statistics(self) -> Dict[str, Any]:
        with self._lock:
            level_counts: Dict[str, int] = defaultdict(int)
            type_counts: Dict[str, int] = defaultdict(int)
            state_counts: Dict[str, int] = defaultdict(int)

            for alert in self.alert_history:
                level_counts[alert.alert_level.value] += 1
                type_counts[alert.anomaly_type.value] += 1
                state_counts[alert.state.value] += 1

            return {
                "total_alerts": len(self.alert_history),
                "active_alerts": len(self.active_alerts),
                "by_level": dict(level_counts),
                "by_type": dict(type_counts),
                "by_state": dict(state_counts)
            }


class EnhancedLogMonitor:
    """增强实时日志监控器 - 支持多文件监控、日志轮转、过滤规则等功能"""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.detectors: List[AnomalyDetectorBase] = []
        self.notifiers: List[Notifier] = []
        self.patterns: List[AnomalyPattern] = []
        self.alert_manager = AlertManager(self.config.get('alert_manager_config', {}))
        self.alert_aggregator = AlertAggregator(
            aggregation_window_seconds=self.config.get('aggregation_window_seconds', 60),
            max_alerts_per_window=self.config.get('max_alerts_per_window', 10)
        )
        self.escalation_policy = AlertEscalationPolicy(self.config.get('escalation_config', {}))
        self.log_filter = LogFilter(self.config.get('filter_config', {}))
        self.context_window = self.config.get('context_window', 10)
        self._event_buffer: deque = deque(maxlen=self.config.get('buffer_size', 10000))
        self._running = False
        self._monitor_thread: Optional[threading.Thread] = None
        self._event_queue: queue.Queue = queue.Queue(maxsize=self.config.get('queue_size', 10000))
        self._lock = threading.Lock()
        self._file_positions: Dict[str, int] = {}
        self._file_inodes: Dict[str, int] = {}
        self._monitor_threads: Dict[str, threading.Thread] = {}
        self._stats: Dict[str, Any] = {
            'events_processed': 0,
            'alerts_generated': 0,
            'files_monitored': 0,
            'start_time': None
        }

        self._setup_default_detectors()
        self._setup_default_notifiers()

    def _setup_default_detectors(self) -> None:
        """设置默认检测器"""
        self.detectors.append(ErrorSpikeDetector(
            window_size=self.config.get('error_spike_window', 60),
            threshold_multiplier=self.config.get('error_spike_threshold', 3.0)
        ))

        self.detectors.append(LatencySpikeDetector(
            threshold_ms=self.config.get('latency_threshold_ms', 5000),
            percentile=self.config.get('latency_percentile', 95.0)
        ))

        self.detectors.append(PatternDeviationDetector(
            deviation_threshold=self.config.get('pattern_deviation_threshold', 0.5)
        ))

        self.detectors.append(FrequencyAnomalyDetector(
            window_size=self.config.get('frequency_window', 300),
            threshold_multiplier=self.config.get('frequency_threshold', 3.0)
        ))

        self.detectors.append(SecurityAnomalyDetector(
            config=self.config.get('security_detector_config', {})
        ))

        self.detectors.append(ResourceExhaustionDetector(
            config=self.config.get('resource_detector_config', {})
        ))
        
        if self.config.get('enable_sequence_detection', True):
            self.detectors.append(SequenceAnomalyDetector(
                min_sequence_length=self.config.get('min_sequence_length', 3),
                max_sequence_length=self.config.get('max_sequence_length', 10)
            ))
        
        if self.config.get('enable_behavioral_detection', True):
            self.detectors.append(BehavioralAnomalyDetector(
                learning_period=self.config.get('behavioral_learning_period', 1000),
                anomaly_threshold=self.config.get('behavioral_threshold', 2.5)
            ))
        
        if self.config.get('enable_threshold_detection', True):
            self.detectors.append(ThresholdBreachDetector(
                thresholds=self.config.get('threshold_config')
            ))
        
        if self.config.get('enable_correlation_detection', True):
            self.detectors.append(CorrelationAnomalyDetector(
                time_window_seconds=self.config.get('correlation_window_seconds', 60)
            ))
        
        if self.config.get('enable_degradation_detection', True):
            self.detectors.append(ServiceDegradationDetector(
                degradation_threshold=self.config.get('degradation_threshold', 0.3),
                window_size=self.config.get('degradation_window', 10)
            ))

    def _setup_default_notifiers(self) -> None:
        """设置默认通知器"""
        self.notifiers.append(ConsoleNotifier(
            verbose=self.config.get('verbose', True)
        ))

        output_file = self.config.get('alert_output_file')
        if output_file:
            self.notifiers.append(FileNotifier(output_file))

        email_config = self.config.get('email_notification')
        if email_config:
            self.notifiers.append(EmailNotifier(
                smtp_host=email_config.get('smtp_host'),
                smtp_port=email_config.get('smtp_port', 587),
                username=email_config.get('username'),
                password=email_config.get('password'),
                from_addr=email_config.get('from_addr'),
                to_addrs=email_config.get('to_addrs', []),
                use_tls=email_config.get('use_tls', True)
            ))

        webhook_url = self.config.get('webhook_url')
        if webhook_url:
            self.notifiers.append(WebhookNotifier(
                webhook_url=webhook_url,
                headers=self.config.get('webhook_headers')
            ))

        dingtalk_url = self.config.get('dingtalk_webhook')
        if dingtalk_url:
            self.notifiers.append(DingTalkNotifier(
                webhook_url=dingtalk_url,
                secret=self.config.get('dingtalk_secret')
            ))
        
        wechat_url = self.config.get('wechat_webhook')
        if wechat_url:
            self.notifiers.append(WeChatNotifier(
                webhook_url=wechat_url,
                mentioned_list=self.config.get('wechat_mentioned_list', [])
            ))
        
        slack_url = self.config.get('slack_webhook')
        if slack_url:
            self.notifiers.append(SlackNotifier(
                webhook_url=slack_url,
                channel=self.config.get('slack_channel')
            ))

    def add_detector(self, detector: AnomalyDetectorBase) -> None:
        """添加自定义检测器"""
        self.detectors.append(detector)

    def add_notifier(self, notifier: Notifier) -> None:
        """添加自定义通知器"""
        self.notifiers.append(notifier)

    def add_pattern(self, pattern: AnomalyPattern) -> None:
        """添加异常模式"""
        self.patterns.append(pattern)

    def process_event(self, event: Dict[str, Any]) -> List[AnomalyAlert]:
        """处理单个事件，返回生成的告警列表"""
        if not self.log_filter.should_process(event):
            return []
        
        with self._lock:
            self._event_buffer.append(event)
            self._stats['events_processed'] += 1

        alerts = []

        for detector in self.detectors:
            result = detector.detect([event])

            if result.detected:
                alert = self._create_alert(result, event)
                processed_alert = self.alert_manager.process_alert(alert)
                if processed_alert:
                    aggregated = self.alert_aggregator.add_alert(processed_alert)
                    if aggregated:
                        alerts.append(aggregated)
                    else:
                        alerts.append(processed_alert)
                    
                    should_notify, channels = self.escalation_policy.should_escalate(processed_alert)
                    if should_notify:
                        self._send_notifications_with_channels(processed_alert, channels)
                    
                    self._stats['alerts_generated'] += 1

        return alerts

    def process_batch(self, events: List[Dict[str, Any]]) -> List[AnomalyAlert]:
        """批量处理事件，返回生成的告警列表"""
        filtered_events = [e for e in events if self.log_filter.should_process(e)]
        
        if not filtered_events:
            return []
        
        with self._lock:
            self._event_buffer.extend(filtered_events)
            self._stats['events_processed'] += len(filtered_events)

        alerts = []

        for detector in self.detectors:
            result = detector.detect(filtered_events)

            if result.detected:
                for event in result.events:
                    alert = self._create_alert(result, event)
                    processed_alert = self.alert_manager.process_alert(alert)
                    if processed_alert:
                        aggregated = self.alert_aggregator.add_alert(processed_alert)
                        if aggregated:
                            alerts.append(aggregated)
                        else:
                            alerts.append(processed_alert)
                        
                        should_notify, channels = self.escalation_policy.should_escalate(processed_alert)
                        if should_notify:
                            self._send_notifications_with_channels(processed_alert, channels)
                        
                        self._stats['alerts_generated'] += 1

        for detector in self.detectors:
            detector.update_baseline(filtered_events)

        auto_resolve_seconds = self.config.get('auto_resolve_seconds', 3600)
        resolved = self.alert_manager.auto_resolve_stale_alerts(auto_resolve_seconds)
        if resolved:
            logger.info(f"自动解决 {len(resolved)} 个过期告警")

        return alerts

    def _create_alert(self, result: DetectionResult, event: Dict[str, Any]) -> AnomalyAlert:
        context = self._build_context(event)

        alert_level = self._determine_alert_level(result)
        suggestions = self._generate_suggestions(result)

        return AnomalyAlert(
            alert_id="",
            timestamp=datetime.now(),
            anomaly_type=result.anomaly_type,
            alert_level=alert_level,
            pattern_name=result.anomaly_type.value,
            message=self._generate_alert_message(result),
            context=context,
            metrics=result.details,
            suggestions=suggestions,
            tags=self._extract_tags(event)
        )

    def _build_context(self, event: Dict[str, Any]) -> LogContext:
        with self._lock:
            buffer = list(self._event_buffer)

        event_idx = -1
        for i, e in enumerate(buffer):
            if e is event:
                event_idx = i
                break

        before_events = []
        after_events = []

        if event_idx >= 0:
            before_start = max(0, event_idx - self.context_window)
            before_events = [
                {
                    "timestamp": e.get("timestamp", ""),
                    "level": e.get("level", ""),
                    "message": e.get("message", "")[:100]
                }
                for e in buffer[before_start:event_idx]
            ]

            after_end = min(len(buffer), event_idx + self.context_window + 1)
            after_events = [
                {
                    "timestamp": e.get("timestamp", ""),
                    "level": e.get("level", ""),
                    "message": e.get("message", "")[:100]
                }
                for e in buffer[event_idx + 1:after_end]
            ]

        return LogContext(
            context_id=hashlib.md5(str(event).encode()).hexdigest()[:12],
            timestamp=datetime.now(),
            source=event.get('source', event.get('file', 'unknown')),
            level=event.get('level', 'unknown'),
            message=event.get('message', '')[:500],
            before_events=before_events,
            after_events=after_events,
            metadata=event
        )

    def _determine_alert_level(self, result: DetectionResult) -> AlertLevel:
        if result.confidence >= 0.9:
            return AlertLevel.CRITICAL
        elif result.confidence >= 0.7:
            return AlertLevel.ERROR
        elif result.confidence >= 0.5:
            return AlertLevel.WARNING
        else:
            return AlertLevel.INFO

    def _generate_alert_message(self, result: DetectionResult) -> str:
        anomaly_type_messages = {
            AnomalyType.ERROR_SPIKE: f"检测到错误激增: {result.details.get('current_count', 0)} 个错误",
            AnomalyType.LATENCY_SPIKE: f"检测到延迟激增: P95 = {result.details.get('current_p95', 0):.2f}ms",
            AnomalyType.PATTERN_DEVIATION: "检测到日志模式偏离基线",
            AnomalyType.FREQUENCY_ANOMALY: f"检测到频率异常: {result.details.get('current_frequency', 0)} 事件",
            AnomalyType.THRESHOLD_BREACH: f"检测到阈值突破: {result.details.get('breach_count', 0)} 个违规",
            AnomalyType.SEQUENCE_ANOMALY: "检测到序列异常",
            AnomalyType.BEHAVIORAL_ANOMALY: "检测到行为异常",
            AnomalyType.RESOURCE_EXHAUSTION: f"检测到资源耗尽: {', '.join(result.details.get('resources_affected', []))}",
            AnomalyType.SERVICE_DEGRADATION: "检测到服务降级",
            AnomalyType.SECURITY_ANOMALY: f"检测到安全异常: {result.details.get('total_count', 0)} 个安全事件",
            AnomalyType.CORRELATION_ANOMALY: "检测到关联异常"
        }

        return anomaly_type_messages.get(result.anomaly_type, f"检测到异常: {result.anomaly_type.value}")

    def _generate_suggestions(self, result: DetectionResult) -> List[str]:
        suggestions = []

        if result.anomaly_type == AnomalyType.ERROR_SPIKE:
            suggestions.extend([
                "检查最近的代码部署或配置变更",
                "查看相关服务的健康状态",
                "分析错误堆栈定位根因"
            ])
        elif result.anomaly_type == AnomalyType.LATENCY_SPIKE:
            suggestions.extend([
                "检查数据库查询性能",
                "查看网络连接状态",
                "分析慢请求日志"
            ])
        elif result.anomaly_type == AnomalyType.PATTERN_DEVIATION:
            suggestions.extend([
                "对比正常和异常时段的日志模式",
                "检查是否有新的错误类型出现",
                "验证系统行为是否符合预期"
            ])
        elif result.anomaly_type == AnomalyType.FREQUENCY_ANOMALY:
            suggestions.extend([
                "检查是否有流量激增或骤降",
                "验证监控采集是否正常",
                "分析事件来源分布"
            ])
        elif result.anomaly_type == AnomalyType.SECURITY_ANOMALY:
            suggestions.extend([
                "立即审查安全日志",
                "检查是否有未授权访问",
                "考虑临时封锁可疑IP"
            ])
        elif result.anomaly_type == AnomalyType.RESOURCE_EXHAUSTION:
            suggestions.extend([
                "检查资源使用情况",
                "考虑增加资源配额",
                "优化资源使用效率"
            ])

        return suggestions

    def _extract_tags(self, event: Dict[str, Any]) -> List[str]:
        """从事件中提取标签"""
        tags = []
        if event.get('source'):
            tags.append(f"source:{event.get('source')}")
        if event.get('level'):
            tags.append(f"level:{event.get('level')}")
        return tags

    def _send_notifications(self, alert: AnomalyAlert) -> None:
        """发送通知到所有通知器"""
        for notifier in self.notifiers:
            try:
                notifier.send(alert)
            except Exception as e:
                logger.error(f"发送通知失败: {e}")
    
    def _send_notifications_with_channels(self, alert: AnomalyAlert, channels: List[str]) -> None:
        """根据指定渠道发送通知"""
        channel_notifier_map = {
            'console': ConsoleNotifier,
            'file': FileNotifier,
            'email': EmailNotifier,
            'webhook': WebhookNotifier,
            'dingtalk': DingTalkNotifier,
            'wechat': WeChatNotifier,
            'slack': SlackNotifier
        }
        
        for notifier in self.notifiers:
            notifier_type = type(notifier).__name__
            notifier_key = notifier_type.replace('Notifier', '').lower()
            
            if notifier_key in [c.lower() for c in channels]:
                try:
                    notifier.send(alert)
                except Exception as e:
                    logger.error(f"发送通知失败 ({notifier_type}): {e}")

    def start_monitoring(self, log_path: str, poll_interval: float = 1.0) -> None:
        """启动单个日志文件的监控"""
        self._running = True
        self._stats['start_time'] = datetime.now()
        self._monitor_thread = threading.Thread(
            target=self._monitor_loop,
            args=(log_path, poll_interval),
            daemon=True
        )
        self._monitor_thread.start()
        self._stats['files_monitored'] = 1
        logger.info(f"开始监控日志: {log_path}")
    
    def start_multi_file_monitoring(
        self, 
        log_paths: List[str], 
        poll_interval: float = 1.0
    ) -> None:
        """启动多个日志文件的并行监控"""
        self._running = True
        self._stats['start_time'] = datetime.now()
        
        for log_path in log_paths:
            if Path(log_path).exists():
                thread = threading.Thread(
                    target=self._monitor_loop,
                    args=(log_path, poll_interval),
                    daemon=True
                )
                thread.start()
                self._monitor_threads[log_path] = thread
                logger.info(f"开始监控日志: {log_path}")
            else:
                logger.warning(f"日志路径不存在，跳过: {log_path}")
        
        self._stats['files_monitored'] = len(self._monitor_threads)
    
    def start_directory_monitoring(
        self,
        log_dir: str,
        pattern: str = "*.log",
        poll_interval: float = 1.0,
        recursive: bool = False
    ) -> None:
        """启动目录监控，自动发现并监控匹配的日志文件"""
        dir_path = Path(log_dir)
        if not dir_path.exists():
            logger.error(f"日志目录不存在: {log_dir}")
            return
        
        self._running = True
        self._stats['start_time'] = datetime.now()
        
        if recursive:
            log_files = list(dir_path.rglob(pattern))
        else:
            log_files = list(dir_path.glob(pattern))
        
        for log_file in log_files:
            if log_file.is_file():
                thread = threading.Thread(
                    target=self._monitor_loop_with_rotation,
                    args=(str(log_file), poll_interval),
                    daemon=True
                )
                thread.start()
                self._monitor_threads[str(log_file)] = thread
                logger.info(f"开始监控日志: {log_file}")
        
        self._stats['files_monitored'] = len(self._monitor_threads)
        
        discovery_thread = threading.Thread(
            target=self._file_discovery_loop,
            args=(dir_path, pattern, poll_interval * 10, recursive),
            daemon=True
        )
        discovery_thread.start()

    def stop_monitoring(self) -> None:
        """停止所有监控"""
        self._running = False
        if self._monitor_thread:
            self._monitor_thread.join(timeout=5)
        
        for path, thread in self._monitor_threads.items():
            thread.join(timeout=2)
            logger.info(f"停止监控: {path}")
        
        self._monitor_threads.clear()
        logger.info("停止所有监控")

    def _monitor_loop(self, log_path: str, poll_interval: float) -> None:
        """单个文件的监控循环"""
        path = Path(log_path)
        if not path.exists():
            logger.error(f"日志路径不存在: {log_path}")
            return

        last_position = 0
        if path.is_file():
            last_position = path.stat().st_size
            self._file_positions[log_path] = last_position

        while self._running:
            try:
                if path.is_file():
                    current_size = path.stat().st_size

                    if current_size > last_position:
                        with open(path, 'r', encoding='utf-8', errors='replace') as f:
                            f.seek(last_position)
                            new_lines = f.readlines()
                            last_position = f.tell()
                            self._file_positions[log_path] = last_position

                        events = self._parse_lines(new_lines, log_path)
                        if events:
                            self.process_batch(events)

                    elif current_size < last_position:
                        logger.info(f"检测到日志轮转: {log_path}")
                        last_position = 0
                        self._file_positions[log_path] = 0

                time.sleep(poll_interval)

            except Exception as e:
                logger.error(f"监控循环错误: {e}")
                time.sleep(poll_interval)
    
    def _monitor_loop_with_rotation(self, log_path: str, poll_interval: float) -> None:
        """支持日志轮转检测的监控循环"""
        path = Path(log_path)
        if not path.exists():
            logger.error(f"日志路径不存在: {log_path}")
            return
        
        last_inode = None
        last_position = 0
        
        try:
            stat_info = path.stat()
            last_inode = stat_info.st_ino
            last_position = stat_info.st_size
            self._file_positions[log_path] = last_position
            self._file_inodes[log_path] = last_inode
        except FileNotFoundError:
            pass
        
        while self._running:
            try:
                if path.exists():
                    current_stat = path.stat()
                    current_inode = current_stat.st_ino
                    current_size = current_stat.st_size
                    
                    if current_inode != last_inode:
                        logger.info(f"检测到日志轮转 (inode变化): {log_path}")
                        last_inode = current_inode
                        last_position = 0
                        self._file_inodes[log_path] = current_inode
                    
                    if current_size > last_position:
                        with open(path, 'r', encoding='utf-8', errors='replace') as f:
                            f.seek(last_position)
                            new_lines = f.readlines()
                            last_position = f.tell()
                            self._file_positions[log_path] = last_position
                        
                        events = self._parse_lines(new_lines, log_path)
                        if events:
                            self.process_batch(events)
                    
                    elif current_size < last_position:
                        logger.info(f"检测到日志轮转 (大小减小): {log_path}")
                        last_position = 0
                        self._file_positions[log_path] = 0
                
                time.sleep(poll_interval)
            
            except FileNotFoundError:
                logger.warning(f"日志文件暂时不可用: {log_path}")
                time.sleep(poll_interval * 2)
            except Exception as e:
                logger.error(f"监控循环错误 ({log_path}): {e}")
                time.sleep(poll_interval)
    
    def _file_discovery_loop(
        self,
        dir_path: Path,
        pattern: str,
        interval: float,
        recursive: bool
    ) -> None:
        """定期扫描目录，发现新日志文件"""
        known_files = set(self._monitor_threads.keys())
        
        while self._running:
            try:
                if recursive:
                    current_files = {str(f) for f in dir_path.rglob(pattern) if f.is_file()}
                else:
                    current_files = {str(f) for f in dir_path.glob(pattern) if f.is_file()}
                
                new_files = current_files - known_files
                
                for new_file in new_files:
                    if new_file not in self._monitor_threads:
                        thread = threading.Thread(
                            target=self._monitor_loop_with_rotation,
                            args=(new_file, interval / 10),
                            daemon=True
                        )
                        thread.start()
                        self._monitor_threads[new_file] = thread
                        known_files.add(new_file)
                        logger.info(f"发现新日志文件: {new_file}")
                
                self._stats['files_monitored'] = len(self._monitor_threads)
                
                time.sleep(interval)
            
            except Exception as e:
                logger.error(f"文件发现循环错误: {e}")
                time.sleep(interval)

    def _parse_lines(self, lines: List[str], source: str) -> List[Dict[str, Any]]:
        events = []
        for line in lines:
            line = line.strip()
            if not line:
                continue

            if line.startswith('{'):
                try:
                    data = json.loads(line)
                    data['source'] = source
                    events.append(data)
                    continue
                except json.JSONDecodeError:
                    pass

            event = self._parse_text_line(line, source)
            if event:
                events.append(event)

        return events

    def _parse_text_line(self, line: str, source: str) -> Dict[str, Any]:
        ts_match = re.search(r'(\d{4}-\d{2}-\d{2}[T\s]\d{2}:\d{2}:\d{2})', line)
        timestamp = ts_match.group(1) if ts_match else datetime.now().isoformat()

        level_match = re.search(r'\b(DEBUG|INFO|WARNING|WARN|ERROR|CRITICAL|FATAL)\b', line, re.IGNORECASE)
        level = level_match.group(1).upper() if level_match else 'INFO'

        return {
            "timestamp": timestamp,
            "level": level,
            "message": line,
            "source": source
        }

    def get_alert_summary(self) -> Dict[str, Any]:
        """获取告警摘要统计"""
        return self.alert_manager.get_statistics()

    def get_detector_statistics(self) -> Dict[str, Any]:
        """获取所有检测器的统计信息"""
        stats = {}
        for i, detector in enumerate(self.detectors):
            stats[f"detector_{i}"] = detector.get_statistics()
        return stats
    
    def get_monitoring_stats(self) -> Dict[str, Any]:
        """获取监控统计信息"""
        return {
            **self._stats,
            'uptime_seconds': (
                (datetime.now() - self._stats['start_time']).total_seconds()
                if self._stats['start_time'] else 0
            ),
            'monitored_files': list(self._monitor_threads.keys()),
            'aggregation_pending': self.alert_aggregator.get_pending_count()
        }

    def acknowledge_alert(self, alert_id: str) -> bool:
        """确认告警"""
        return self.alert_manager.acknowledge_alert(alert_id)

    def resolve_alert(self, alert_id: str) -> bool:
        """解决告警"""
        return self.alert_manager.resolve_alert(alert_id)

    def generate_report(self) -> str:
        """生成详细的异常检测报告"""
        summary = self.get_alert_summary()
        detector_stats = self.get_detector_statistics()
        monitoring_stats = self.get_monitoring_stats()

        lines = [
            "# 异常检测报告",
            "",
            f"**生成时间**: {datetime.now().isoformat()}",
            f"**总告警数**: {summary['total_alerts']}",
            f"**活跃告警数**: {summary['active_alerts']}",
            f"**处理事件数**: {monitoring_stats['events_processed']}",
            f"**监控文件数**: {monitoring_stats['files_monitored']}",
            "",
            "## 监控统计",
            "",
            f"- **运行时长**: {monitoring_stats['uptime_seconds']:.0f} 秒",
            f"- **事件处理速率**: {monitoring_stats['events_processed'] / max(monitoring_stats['uptime_seconds'], 1):.2f} 事件/秒",
            f"- **告警生成速率**: {monitoring_stats['alerts_generated'] / max(monitoring_stats['uptime_seconds'], 1):.4f} 告警/秒",
            "",
            "## 告警级别分布",
            "",
            "| 级别 | 数量 |",
            "|------|------|",
        ]

        for level, count in sorted(summary['by_level'].items()):
            lines.append(f"| {level} | {count} |")

        lines.extend([
            "",
            "## 异常类型分布",
            "",
            "| 类型 | 数量 |",
            "|------|------|",
        ])

        for atype, count in sorted(summary['by_type'].items()):
            lines.append(f"| {atype} | {count} |")

        lines.extend([
            "",
            "## 告警状态分布",
            "",
            "| 状态 | 数量 |",
            "|------|------|",
        ])

        for state, count in sorted(summary['by_state'].items()):
            lines.append(f"| {state} | {count} |")

        active_alerts = self.alert_manager.get_active_alerts()
        if active_alerts:
            lines.extend([
                "",
                "## 活跃告警",
                "",
            ])

            for alert in active_alerts[-10:]:
                lines.extend([
                    f"### {alert.alert_id}",
                    "",
                    f"- **级别**: {alert.alert_level.value}",
                    f"- **类型**: {alert.anomaly_type.value}",
                    f"- **状态**: {alert.state.value}",
                    f"- **出现次数**: {alert.occurrence_count}",
                    f"- **首次出现**: {alert.first_occurred}",
                    f"- **最后出现**: {alert.last_occurred}",
                    "",
                ])

        lines.extend([
            "",
            "## 检测器统计",
            "",
        ])

        for name, stats in detector_stats.items():
            lines.append(f"### {name}")
            for key, value in stats.items():
                lines.append(f"- {key}: {value}")
            lines.append("")
        
        if monitoring_stats['monitored_files']:
            lines.extend([
                "## 监控的文件",
                "",
            ])
            for file_path in monitoring_stats['monitored_files']:
                lines.append(f"- {file_path}")
            lines.append("")

        return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="增强异常检测器 - 实现实时日志监控和异常检测",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 监控单个日志文件
  python anomaly_detector.py --log-file app.log --monitor

  # 分析日志文件
  python anomaly_detector.py --log-file app.log --analyze

  # 使用配置文件
  python anomaly_detector.py --config detector_config.json

  # 实时监控并启用多通道通知
  python anomaly_detector.py --log-file app.log --monitor --webhook https://hooks.example.com/alert
        """
    )

    parser.add_argument(
        "--log-file",
        type=str,
        help="日志文件路径"
    )

    parser.add_argument(
        "--log-dir",
        type=str,
        help="日志目录路径"
    )

    parser.add_argument(
        "--config",
        type=str,
        help="配置文件路径"
    )

    parser.add_argument(
        "--monitor",
        action="store_true",
        help="启动实时监控模式"
    )

    parser.add_argument(
        "--analyze",
        action="store_true",
        help="分析现有日志文件"
    )

    parser.add_argument(
        "--report",
        type=str,
        default="anomaly_report.md",
        help="报告输出路径"
    )

    parser.add_argument(
        "--poll-interval",
        type=float,
        default=1.0,
        help="监控轮询间隔（秒）"
    )

    parser.add_argument(
        "--webhook",
        type=str,
        help="Webhook通知URL"
    )

    parser.add_argument(
        "--email",
        type=str,
        help="邮件通知配置 (JSON格式)"
    )

    parser.add_argument(
        "--verbose",
        action="store_true",
        help="详细输出"
    )

    args = parser.parse_args()

    config = {}
    if args.config:
        with open(args.config, 'r', encoding='utf-8') as f:
            config = json.load(f)

    if args.verbose:
        config['verbose'] = True
        logging.getLogger().setLevel(logging.DEBUG)

    if args.webhook:
        config['webhook_url'] = args.webhook

    if args.email:
        try:
            email_config = json.loads(args.email)
            config['email_notification'] = email_config
        except json.JSONDecodeError:
            print("错误: 邮件配置JSON格式无效")
            sys.exit(1)

    monitor = EnhancedLogMonitor(config)

    if args.monitor and args.log_file:
        print(f"开始监控日志文件: {args.log_file}")
        print("按 Ctrl+C 停止监控\n")

        monitor.start_monitoring(args.log_file, args.poll_interval)

        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n正在停止监控...")
            monitor.stop_monitoring()

        report = monitor.generate_report()
        with open(args.report, 'w', encoding='utf-8') as f:
            f.write(report)
        print(f"\n报告已保存: {args.report}")

    elif args.analyze and (args.log_file or args.log_dir):
        events = []

        if args.log_file:
            path = Path(args.log_file)
            if path.exists():
                with open(path, 'r', encoding='utf-8', errors='replace') as f:
                    events.extend(monitor._parse_lines(f.readlines(), str(path)))

        if args.log_dir:
            dir_path = Path(args.log_dir)
            for log_file in dir_path.rglob('*.log'):
                with open(log_file, 'r', encoding='utf-8', errors='replace') as f:
                    events.extend(monitor._parse_lines(f.readlines(), str(log_file)))

        print(f"加载了 {len(events)} 条日志事件")

        alerts = monitor.process_batch(events)

        print(f"\n检测到 {len(alerts)} 个异常")

        summary = monitor.get_alert_summary()
        print("\n告警级别分布:")
        for level, count in summary['by_level'].items():
            print(f"  {level}: {count}")

        print("\n异常类型分布:")
        for atype, count in summary['by_type'].items():
            print(f"  {atype}: {count}")

        print("\n告警状态分布:")
        for state, count in summary['by_state'].items():
            print(f"  {state}: {count}")

        report = monitor.generate_report()
        with open(args.report, 'w', encoding='utf-8') as f:
            f.write(report)
        print(f"\n报告已保存: {args.report}")

    else:
        parser.print_help()
        print("\n示例用法:")
        print("  python anomaly_detector.py --log-file app.log --monitor")
        print("  python anomaly_detector.py --log-file app.log --analyze")
        print("  python anomaly_detector.py --log-file app.log --monitor --webhook https://hooks.example.com/alert")

    return 0


if __name__ == "__main__":
    sys.exit(main())
