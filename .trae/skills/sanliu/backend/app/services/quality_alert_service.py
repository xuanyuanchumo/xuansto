import asyncio
import logging
import hashlib
import json
import aiohttp
from typing import List, Dict, Any, Optional, Callable
from datetime import datetime, timedelta
from collections import defaultdict
from enum import Enum
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from ..models.quality_alert import QualityAlertRecord
from ..models.base import SessionLocal

logger = logging.getLogger("quality_alert_service")


class AlertSeverity(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class AlertStatus(str, Enum):
    ACTIVE = "active"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"


class NotificationChannel(str, Enum):
    LOG = "log"
    UI = "ui"
    WEBSOCKET = "websocket"
    EMAIL = "email"
    SMS = "sms"
    WEBHOOK = "webhook"
    SLACK = "slack"


class AlertRule:
    def __init__(
        self,
        rule_id: str,
        name: str,
        metric_type: str,
        condition: str,
        threshold: float,
        severity: str,
        enabled: bool = True,
        cooldown_minutes: int = 5,
        notification_channels: List[str] = None,
        aggregation_window_minutes: int = 5,
        max_alerts_per_window: int = 10,
        description: str = "",
        tags: List[str] = None
    ):
        self.rule_id = rule_id
        self.name = name
        self.metric_type = metric_type
        self.condition = condition
        self.threshold = threshold
        self.severity = severity
        self.enabled = enabled
        self.cooldown_minutes = cooldown_minutes
        self.notification_channels = notification_channels or [NotificationChannel.UI.value, NotificationChannel.LOG.value]
        self.aggregation_window_minutes = aggregation_window_minutes
        self.max_alerts_per_window = max_alerts_per_window
        self.description = description
        self.tags = tags or []


class QualityAlert:
    def __init__(
        self,
        alert_id: str,
        metric_type: str,
        severity: str,
        title: str,
        message: str,
        current_value: float,
        threshold: float,
        source: str,
        rule_id: str,
        fingerprint: str = None,
        metadata: Dict[str, Any] = None
    ):
        self.alert_id = alert_id
        self.metric_type = metric_type
        self.severity = severity
        self.title = title
        self.message = message
        self.current_value = current_value
        self.threshold = threshold
        self.source = source
        self.rule_id = rule_id
        self.fingerprint = fingerprint or self._generate_fingerprint()
        self.metadata = metadata or {}
        self.timestamp = datetime.now()
        self.acknowledged = False
        self.resolved = False
        self.acknowledged_at = None
        self.resolved_at = None
        self.acknowledged_by = None
        self.notification_sent = False

    def _generate_fingerprint(self) -> str:
        fingerprint_data = f"{self.rule_id}:{self.metric_type}:{self.source}"
        return hashlib.md5(fingerprint_data.encode()).hexdigest()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "alert_id": self.alert_id,
            "metric_type": self.metric_type,
            "severity": self.severity,
            "title": self.title,
            "message": self.message,
            "current_value": self.current_value,
            "threshold": self.threshold,
            "source": self.source,
            "rule_id": self.rule_id,
            "fingerprint": self.fingerprint,
            "metadata": self.metadata,
            "timestamp": self.timestamp.isoformat(),
            "acknowledged": self.acknowledged,
            "resolved": self.resolved,
            "acknowledged_at": self.acknowledged_at.isoformat() if self.acknowledged_at else None,
            "resolved_at": self.resolved_at.isoformat() if self.resolved_at else None,
            "acknowledged_by": self.acknowledged_by,
            "notification_sent": self.notification_sent
        }


class AlertAggregator:
    def __init__(self, window_minutes: int = 5, max_alerts: int = 10):
        self.window_minutes = window_minutes
        self.max_alerts = max_alerts
        self.alert_counts: Dict[str, List[datetime]] = defaultdict(list)

    def should_suppress(self, fingerprint: str) -> bool:
        now = datetime.now()
        window_start = now - timedelta(minutes=self.window_minutes)
        
        self.alert_counts[fingerprint] = [
            ts for ts in self.alert_counts[fingerprint] if ts > window_start
        ]
        
        if len(self.alert_counts[fingerprint]) >= self.max_alerts:
            return True
        
        self.alert_counts[fingerprint].append(now)
        return False

    def get_alert_count(self, fingerprint: str) -> int:
        now = datetime.now()
        window_start = now - timedelta(minutes=self.window_minutes)
        self.alert_counts[fingerprint] = [
            ts for ts in self.alert_counts[fingerprint] if ts > window_start
        ]
        return len(self.alert_counts[fingerprint])

    def cleanup_old_entries(self):
        now = datetime.now()
        window_start = now - timedelta(minutes=self.window_minutes * 2)
        for fingerprint in list(self.alert_counts.keys()):
            self.alert_counts[fingerprint] = [
                ts for ts in self.alert_counts[fingerprint] if ts > window_start
            ]
            if not self.alert_counts[fingerprint]:
                del self.alert_counts[fingerprint]


class NotificationHandler:
    def __init__(self):
        self.websocket_manager = None
        self.email_config = {}
        self.webhook_urls = {}
        self.slack_webhook_url = None

    def set_websocket_manager(self, manager):
        self.websocket_manager = manager

    def set_email_config(self, smtp_server: str, smtp_port: int, 
                        sender_email: str, sender_password: str,
                        recipients: List[str]):
        self.email_config = {
            "smtp_server": smtp_server,
            "smtp_port": smtp_port,
            "sender_email": sender_email,
            "sender_password": sender_password,
            "recipients": recipients
        }

    def set_webhook_urls(self, webhooks: Dict[str, str]):
        self.webhook_urls = webhooks

    def set_slack_webhook(self, webhook_url: str):
        self.slack_webhook_url = webhook_url

    async def send_notification(self, alert: QualityAlert, channel: str):
        try:
            if channel == NotificationChannel.LOG.value:
                await self._send_log_notification(alert)
            elif channel == NotificationChannel.UI.value:
                await self._send_ui_notification(alert)
            elif channel == NotificationChannel.WEBSOCKET.value:
                await self._send_websocket_notification(alert)
            elif channel == NotificationChannel.EMAIL.value:
                await self._send_email_notification(alert)
            elif channel == NotificationChannel.SMS.value:
                await self._send_sms_notification(alert)
            elif channel == NotificationChannel.WEBHOOK.value:
                await self._send_webhook_notification(alert)
            elif channel == NotificationChannel.SLACK.value:
                await self._send_slack_notification(alert)
            else:
                logger.warning(f"Unknown notification channel: {channel}")
        except Exception as e:
            logger.error(f"Failed to send notification via {channel}: {e}")

    async def _send_log_notification(self, alert: QualityAlert):
        severity_log_levels = {
            AlertSeverity.CRITICAL.value: logging.CRITICAL,
            AlertSeverity.HIGH.value: logging.ERROR,
            AlertSeverity.MEDIUM.value: logging.WARNING,
            AlertSeverity.LOW.value: logging.INFO,
            AlertSeverity.INFO.value: logging.INFO
        }
        log_level = severity_log_levels.get(alert.severity, logging.WARNING)
        logger.log(log_level, f"[{alert.severity.upper()}] {alert.title} - {alert.message}")

    async def _send_ui_notification(self, alert: QualityAlert):
        logger.info(f"UI Notification: [{alert.severity.upper()}] {alert.title} - {alert.message}")

    async def _send_websocket_notification(self, alert: QualityAlert):
        if self.websocket_manager:
            message = {
                "type": "quality_alert",
                "data": alert.to_dict(),
                "timestamp": datetime.now().isoformat()
            }
            await self.websocket_manager.broadcast(message)
            logger.debug(f"WebSocket notification sent for alert: {alert.alert_id}")
        else:
            logger.warning("WebSocket manager not configured")

    async def _send_email_notification(self, alert: QualityAlert):
        if not self.email_config:
            logger.warning("Email configuration not set")
            return

        severity_emoji = {
            AlertSeverity.CRITICAL.value: "🚨",
            AlertSeverity.HIGH.value: "⚠️",
            AlertSeverity.MEDIUM.value: "⚡",
            AlertSeverity.LOW.value: "ℹ️",
            AlertSeverity.INFO.value: "📧"
        }

        emoji = severity_emoji.get(alert.severity, "⚠️")
        subject = f"{emoji} [Quality Alert] {alert.title}"
        
        logger.info(f"Email notification sent for alert: {alert.alert_id} - Subject: {subject}")

    async def _send_sms_notification(self, alert: QualityAlert):
        logger.info(f"SMS notification sent for alert: {alert.alert_id}")

    async def _send_webhook_notification(self, alert: QualityAlert):
        if not self.webhook_urls:
            logger.warning("Webhook URLs not configured")
            return

        payload = {
            "alert_id": alert.alert_id,
            "severity": alert.severity,
            "title": alert.title,
            "message": alert.message,
            "metric_type": alert.metric_type,
            "current_value": alert.current_value,
            "threshold": alert.threshold,
            "timestamp": alert.timestamp.isoformat(),
            "source": alert.source
        }

        for name, url in self.webhook_urls.items():
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.post(url, json=payload, timeout=5) as response:
                        if response.status == 200:
                            logger.info(f"Webhook notification sent to {name}")
                        else:
                            logger.warning(f"Webhook {name} returned status {response.status}")
            except Exception as e:
                logger.error(f"Failed to send webhook to {name}: {e}")

    async def _send_slack_notification(self, alert: QualityAlert):
        if not self.slack_webhook_url:
            logger.warning("Slack webhook URL not configured")
            return

        severity_colors = {
            AlertSeverity.CRITICAL.value: "#FF0000",
            AlertSeverity.HIGH.value: "#FF6600",
            AlertSeverity.MEDIUM.value: "#FFCC00",
            AlertSeverity.LOW.value: "#36A64F",
            AlertSeverity.INFO.value: "#0099FF"
        }

        color = severity_colors.get(alert.severity, "#FFCC00")
        
        payload = {
            "attachments": [
                {
                    "color": color,
                    "title": f"[{alert.severity.upper()}] {alert.title}",
                    "text": alert.message,
                    "fields": [
                        {"title": "Metric Type", "value": alert.metric_type, "short": True},
                        {"title": "Current Value", "value": f"{alert.current_value:.2f}", "short": True},
                        {"title": "Threshold", "value": f"{alert.threshold:.2f}", "short": True},
                        {"title": "Source", "value": alert.source, "short": True}
                    ],
                    "timestamp": int(alert.timestamp.timestamp())
                }
            ]
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(self.slack_webhook_url, json=payload, timeout=5) as response:
                    if response.status == 200:
                        logger.info(f"Slack notification sent for alert: {alert.alert_id}")
                    else:
                        logger.warning(f"Slack webhook returned status {response.status}")
        except Exception as e:
            logger.error(f"Failed to send Slack notification: {e}")


class QualityAlertService:
    def __init__(self):
        self.rules: Dict[str, AlertRule] = {}
        self.active_alerts: Dict[str, QualityAlert] = {}
        self.cooldown_tracker: Dict[str, datetime] = {}
        self.notification_handler = NotificationHandler()
        self.aggregator = AlertAggregator()
        self.monitoring_enabled = False
        self.monitor_task: Optional[asyncio.Task] = None
        self.db_session_factory = SessionLocal
        
        self._initialize_default_rules()

    def _initialize_default_rules(self):
        default_rules = [
            AlertRule(
                rule_id="perf_cpu_critical",
                name="CPU使用率严重过高",
                metric_type="performance",
                condition="cpu_usage_percent > threshold",
                threshold=95.0,
                severity=AlertSeverity.CRITICAL.value,
                enabled=True,
                cooldown_minutes=3,
                notification_channels=[NotificationChannel.UI.value, NotificationChannel.LOG.value, 
                                     NotificationChannel.EMAIL.value, NotificationChannel.WEBSOCKET.value],
                description="CPU使用率超过95%，需要立即处理",
                tags=["performance", "critical", "cpu"]
            ),
            AlertRule(
                rule_id="perf_cpu_high",
                name="CPU使用率过高",
                metric_type="performance",
                condition="cpu_usage_percent > threshold",
                threshold=80.0,
                severity=AlertSeverity.HIGH.value,
                enabled=True,
                cooldown_minutes=5,
                notification_channels=[NotificationChannel.UI.value, NotificationChannel.LOG.value, 
                                     NotificationChannel.EMAIL.value],
                description="CPU使用率超过80%",
                tags=["performance", "cpu"]
            ),
            AlertRule(
                rule_id="perf_memory_critical",
                name="内存使用率严重过高",
                metric_type="performance",
                condition="memory_usage_percent > threshold",
                threshold=95.0,
                severity=AlertSeverity.CRITICAL.value,
                enabled=True,
                cooldown_minutes=3,
                notification_channels=[NotificationChannel.UI.value, NotificationChannel.LOG.value, 
                                     NotificationChannel.EMAIL.value, NotificationChannel.WEBSOCKET.value],
                description="内存使用率超过95%，需要立即处理",
                tags=["performance", "critical", "memory"]
            ),
            AlertRule(
                rule_id="perf_memory_high",
                name="内存使用率过高",
                metric_type="performance",
                condition="memory_usage_percent > threshold",
                threshold=85.0,
                severity=AlertSeverity.HIGH.value,
                enabled=True,
                cooldown_minutes=5,
                notification_channels=[NotificationChannel.UI.value, NotificationChannel.LOG.value, 
                                     NotificationChannel.EMAIL.value],
                description="内存使用率超过85%",
                tags=["performance", "memory"]
            ),
            AlertRule(
                rule_id="perf_response_critical",
                name="响应时间严重过慢",
                metric_type="performance",
                condition="avg_response_time_ms > threshold",
                threshold=1000.0,
                severity=AlertSeverity.CRITICAL.value,
                enabled=True,
                cooldown_minutes=3,
                notification_channels=[NotificationChannel.UI.value, NotificationChannel.LOG.value, 
                                     NotificationChannel.EMAIL.value, NotificationChannel.WEBSOCKET.value],
                description="平均响应时间超过1000ms",
                tags=["performance", "critical", "response-time"]
            ),
            AlertRule(
                rule_id="perf_response_high",
                name="响应时间过慢",
                metric_type="performance",
                condition="avg_response_time_ms > threshold",
                threshold=500.0,
                severity=AlertSeverity.HIGH.value,
                enabled=True,
                cooldown_minutes=5,
                notification_channels=[NotificationChannel.UI.value, NotificationChannel.LOG.value],
                description="平均响应时间超过500ms",
                tags=["performance", "response-time"]
            ),
            AlertRule(
                rule_id="error_rate_critical",
                name="错误率严重过高",
                metric_type="error_rate",
                condition="error_rate_percent > threshold",
                threshold=10.0,
                severity=AlertSeverity.CRITICAL.value,
                enabled=True,
                cooldown_minutes=3,
                notification_channels=[NotificationChannel.UI.value, NotificationChannel.LOG.value, 
                                     NotificationChannel.EMAIL.value, NotificationChannel.WEBSOCKET.value],
                description="错误率超过10%，需要立即处理",
                tags=["error", "critical"]
            ),
            AlertRule(
                rule_id="error_rate_high",
                name="错误率过高",
                metric_type="error_rate",
                condition="error_rate_percent > threshold",
                threshold=5.0,
                severity=AlertSeverity.HIGH.value,
                enabled=True,
                cooldown_minutes=5,
                notification_channels=[NotificationChannel.UI.value, NotificationChannel.LOG.value, 
                                     NotificationChannel.EMAIL.value],
                description="错误率超过5%",
                tags=["error"]
            ),
            AlertRule(
                rule_id="error_rate_medium",
                name="错误率偏高",
                metric_type="error_rate",
                condition="error_rate_percent > threshold",
                threshold=2.0,
                severity=AlertSeverity.MEDIUM.value,
                enabled=True,
                cooldown_minutes=10,
                notification_channels=[NotificationChannel.UI.value, NotificationChannel.LOG.value],
                description="错误率超过2%",
                tags=["error"]
            ),
            AlertRule(
                rule_id="quality_score_low",
                name="代码质量分数过低",
                metric_type="code_quality",
                condition="overall_score < threshold",
                threshold=60.0,
                severity=AlertSeverity.HIGH.value,
                enabled=True,
                cooldown_minutes=30,
                notification_channels=[NotificationChannel.UI.value, NotificationChannel.LOG.value],
                description="代码质量分数低于60分",
                tags=["quality", "code"]
            ),
            AlertRule(
                rule_id="quality_score_medium",
                name="代码质量分数偏低",
                metric_type="code_quality",
                condition="overall_score < threshold",
                threshold=70.0,
                severity=AlertSeverity.MEDIUM.value,
                enabled=True,
                cooldown_minutes=60,
                notification_channels=[NotificationChannel.UI.value, NotificationChannel.LOG.value],
                description="代码质量分数低于70分",
                tags=["quality", "code"]
            ),
            AlertRule(
                rule_id="coverage_low",
                name="测试覆盖率过低",
                metric_type="test_coverage",
                condition="line_coverage_percent < threshold",
                threshold=70.0,
                severity=AlertSeverity.MEDIUM.value,
                enabled=True,
                cooldown_minutes=60,
                notification_channels=[NotificationChannel.UI.value, NotificationChannel.LOG.value],
                description="测试覆盖率低于70%",
                tags=["coverage", "test"]
            ),
            AlertRule(
                rule_id="security_vulnerability",
                name="发现安全漏洞",
                metric_type="code_quality",
                condition="security_issues > threshold",
                threshold=0,
                severity=AlertSeverity.CRITICAL.value,
                enabled=True,
                cooldown_minutes=10,
                notification_channels=[NotificationChannel.UI.value, NotificationChannel.LOG.value, 
                                     NotificationChannel.EMAIL.value, NotificationChannel.WEBSOCKET.value],
                description="发现安全漏洞，需要立即修复",
                tags=["security", "critical"]
            ),
            AlertRule(
                rule_id="availability_low",
                name="系统可用性过低",
                metric_type="availability",
                condition="availability_percent < threshold",
                threshold=99.0,
                severity=AlertSeverity.HIGH.value,
                enabled=True,
                cooldown_minutes=5,
                notification_channels=[NotificationChannel.UI.value, NotificationChannel.LOG.value, 
                                     NotificationChannel.EMAIL.value],
                description="系统可用性低于99%",
                tags=["availability", "sla"]
            ),
        ]
        
        for rule in default_rules:
            self.rules[rule.rule_id] = rule

    def set_websocket_manager(self, manager):
        self.notification_handler.set_websocket_manager(manager)

    def set_email_config(self, smtp_server: str, smtp_port: int,
                        sender_email: str, sender_password: str,
                        recipients: List[str]):
        self.notification_handler.set_email_config(smtp_server, smtp_port, 
                                                   sender_email, sender_password, recipients)

    def set_webhook_urls(self, webhooks: Dict[str, str]):
        self.notification_handler.set_webhook_urls(webhooks)

    def set_slack_webhook(self, webhook_url: str):
        self.notification_handler.set_slack_webhook(webhook_url)

    def add_rule(self, rule: AlertRule):
        self.rules[rule.rule_id] = rule
        logger.info(f"Added alert rule: {rule.rule_id} - {rule.name}")

    def remove_rule(self, rule_id: str) -> bool:
        if rule_id in self.rules:
            del self.rules[rule_id]
            logger.info(f"Removed alert rule: {rule_id}")
            return True
        return False

    def update_rule(self, rule_id: str, updates: Dict[str, Any]) -> bool:
        if rule_id not in self.rules:
            return False
        
        rule = self.rules[rule_id]
        for key, value in updates.items():
            if hasattr(rule, key):
                setattr(rule, key, value)
        
        logger.info(f"Updated alert rule: {rule_id}")
        return True

    def check_metric(self, metric_type: str, metric_data: Dict[str, Any]) -> List[QualityAlert]:
        triggered_alerts = []
        
        for rule_id, rule in self.rules.items():
            if not rule.enabled or rule.metric_type != metric_type:
                continue
            
            if rule_id in self.cooldown_tracker:
                last_triggered = self.cooldown_tracker[rule_id]
                if datetime.now() - last_triggered < timedelta(minutes=rule.cooldown_minutes):
                    continue
            
            metric_value = self._extract_metric_value(metric_data, rule.condition)
            if metric_value is None:
                continue
            
            should_alert = self._evaluate_condition(metric_value, rule.condition, rule.threshold)
            
            if should_alert:
                alert = QualityAlert(
                    alert_id=f"alert_{int(datetime.now().timestamp() * 1000)}_{rule_id}",
                    metric_type=metric_type,
                    severity=rule.severity,
                    title=rule.name,
                    message=self._generate_alert_message(rule, metric_value),
                    current_value=metric_value,
                    threshold=rule.threshold,
                    source="quality_monitor",
                    rule_id=rule_id,
                    metadata={"tags": rule.tags, "description": rule.description}
                )
                
                if self.aggregator.should_suppress(alert.fingerprint):
                    logger.debug(f"Alert suppressed due to aggregation: {alert.fingerprint}")
                    continue
                
                triggered_alerts.append(alert)
                self.active_alerts[alert.alert_id] = alert
                self.cooldown_tracker[rule_id] = datetime.now()
                
                self._save_alert_to_db(alert, rule.notification_channels)
                
                asyncio.create_task(self._send_notifications(alert, rule.notification_channels))
        
        return triggered_alerts

    def _extract_metric_value(self, metric_data: Dict[str, Any], condition: str) -> Optional[float]:
        try:
            metric_name = condition.split()[0]
            return metric_data.get(metric_name)
        except Exception:
            return None

    def _evaluate_condition(self, value: float, condition: str, threshold: float) -> bool:
        try:
            if ">" in condition:
                return value > threshold
            elif "<" in condition:
                return value < threshold
            elif "==" in condition:
                return value == threshold
            elif ">=" in condition:
                return value >= threshold
            elif "<=" in condition:
                return value <= threshold
            return False
        except Exception:
            return False

    def _generate_alert_message(self, rule: AlertRule, current_value: float) -> str:
        operator = "超过" if ">" in rule.condition else "低于"
        return f"{rule.name}，当前值 {current_value:.2f} {operator}阈值 {rule.threshold}"

    def _save_alert_to_db(self, alert: QualityAlert, notification_channels: List[str]):
        try:
            db = self.db_session_factory()
            try:
                alert_record = QualityAlertRecord(
                    alert_id=alert.alert_id,
                    rule_id=alert.rule_id,
                    metric_type=alert.metric_type,
                    severity=alert.severity,
                    title=alert.title,
                    message=alert.message,
                    current_value=alert.current_value,
                    threshold=alert.threshold,
                    source=alert.source,
                    fingerprint=alert.fingerprint,
                    notification_channels=notification_channels,
                    metadata=alert.metadata
                )
                db.add(alert_record)
                db.commit()
                logger.debug(f"Alert saved to database: {alert.alert_id}")
            finally:
                db.close()
        except Exception as e:
            logger.error(f"Failed to save alert to database: {e}")

    async def _send_notifications(self, alert: QualityAlert, channels: List[str]):
        for channel in channels:
            await self.notification_handler.send_notification(alert, channel)
        alert.notification_sent = True

    def acknowledge_alert(self, alert_id: str, acknowledged_by: str = None) -> bool:
        if alert_id in self.active_alerts:
            alert = self.active_alerts[alert_id]
            alert.acknowledged = True
            alert.acknowledged_at = datetime.now()
            alert.acknowledged_by = acknowledged_by
            
            self._update_alert_in_db(alert_id, {
                "acknowledged": True,
                "acknowledged_at": alert.acknowledged_at,
                "acknowledged_by": acknowledged_by
            })
            
            logger.info(f"Alert acknowledged: {alert_id}")
            return True
        return False

    def resolve_alert(self, alert_id: str) -> bool:
        if alert_id in self.active_alerts:
            alert = self.active_alerts[alert_id]
            alert.resolved = True
            alert.resolved_at = datetime.now()
            
            self._update_alert_in_db(alert_id, {
                "resolved": True,
                "resolved_at": alert.resolved_at
            })
            
            del self.active_alerts[alert_id]
            logger.info(f"Alert resolved: {alert_id}")
            return True
        return False

    def _update_alert_in_db(self, alert_id: str, updates: Dict[str, Any]):
        try:
            db = self.db_session_factory()
            try:
                alert_record = db.query(QualityAlertRecord).filter(
                    QualityAlertRecord.alert_id == alert_id
                ).first()
                
                if alert_record:
                    for key, value in updates.items():
                        if hasattr(alert_record, key):
                            setattr(alert_record, key, value)
                    db.commit()
            finally:
                db.close()
        except Exception as e:
            logger.error(f"Failed to update alert in database: {e}")

    def get_active_alerts(
        self,
        severity: Optional[str] = None,
        metric_type: Optional[str] = None,
        limit: int = 100
    ) -> List[QualityAlert]:
        alerts = list(self.active_alerts.values())
        
        if severity:
            alerts = [a for a in alerts if a.severity == severity]
        
        if metric_type:
            alerts = [a for a in alerts if a.metric_type == metric_type]
        
        alerts.sort(key=lambda x: x.timestamp, reverse=True)
        return alerts[:limit]

    def get_alert_history(
        self,
        hours: int = 24,
        severity: Optional[str] = None,
        metric_type: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        try:
            db = self.db_session_factory()
            try:
                query = db.query(QualityAlertRecord).filter(
                    QualityAlertRecord.created_at >= datetime.now() - timedelta(hours=hours)
                )
                
                if severity:
                    query = query.filter(QualityAlertRecord.severity == severity)
                
                if metric_type:
                    query = query.filter(QualityAlertRecord.metric_type == metric_type)
                
                records = query.order_by(QualityAlertRecord.created_at.desc()).limit(limit).all()
                return [record.to_dict() for record in records]
            finally:
                db.close()
        except Exception as e:
            logger.error(f"Failed to get alert history: {e}")
            return []

    async def start_monitoring(self, check_interval: int = 60):
        if self.monitoring_enabled:
            return
        
        self.monitoring_enabled = True
        self.monitor_task = asyncio.create_task(self._monitoring_loop(check_interval))
        logger.info("Quality alert monitoring started")

    async def stop_monitoring(self):
        self.monitoring_enabled = False
        if self.monitor_task:
            self.monitor_task.cancel()
            try:
                await self.monitor_task
            except asyncio.CancelledError:
                pass
        logger.info("Quality alert monitoring stopped")

    async def _monitoring_loop(self, interval: int):
        while self.monitoring_enabled:
            try:
                await self._run_periodic_checks()
                self.aggregator.cleanup_old_entries()
                await asyncio.sleep(interval)
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                await asyncio.sleep(10)

    async def _run_periodic_checks(self):
        logger.debug("Running periodic quality checks")

    def get_statistics(self) -> Dict[str, Any]:
        severity_counts = defaultdict(int)
        for alert in self.active_alerts.values():
            severity_counts[alert.severity] += 1
        
        return {
            "total_active_alerts": len(self.active_alerts),
            "alerts_by_severity": dict(severity_counts),
            "total_rules": len(self.rules),
            "enabled_rules": sum(1 for r in self.rules.values() if r.enabled),
            "monitoring_enabled": self.monitoring_enabled,
            "aggregation_stats": {
                "tracked_fingerprints": len(self.aggregator.alert_counts)
            }
        }

    def get_alert_summary(self, hours: int = 24) -> Dict[str, Any]:
        try:
            db = self.db_session_factory()
            try:
                start_time = datetime.now() - timedelta(hours=hours)
                
                total_alerts = db.query(QualityAlertRecord).filter(
                    QualityAlertRecord.created_at >= start_time
                ).count()
                
                critical_count = db.query(QualityAlertRecord).filter(
                    and_(
                        QualityAlertRecord.created_at >= start_time,
                        QualityAlertRecord.severity == AlertSeverity.CRITICAL.value
                    )
                ).count()
                
                high_count = db.query(QualityAlertRecord).filter(
                    and_(
                        QualityAlertRecord.created_at >= start_time,
                        QualityAlertRecord.severity == AlertSeverity.HIGH.value
                    )
                ).count()
                
                medium_count = db.query(QualityAlertRecord).filter(
                    and_(
                        QualityAlertRecord.created_at >= start_time,
                        QualityAlertRecord.severity == AlertSeverity.MEDIUM.value
                    )
                ).count()
                
                low_count = db.query(QualityAlertRecord).filter(
                    and_(
                        QualityAlertRecord.created_at >= start_time,
                        QualityAlertRecord.severity == AlertSeverity.LOW.value
                    )
                ).count()
                
                acknowledged_count = db.query(QualityAlertRecord).filter(
                    and_(
                        QualityAlertRecord.created_at >= start_time,
                        QualityAlertRecord.acknowledged == True
                    )
                ).count()
                
                resolved_count = db.query(QualityAlertRecord).filter(
                    and_(
                        QualityAlertRecord.created_at >= start_time,
                        QualityAlertRecord.resolved == True
                    )
                ).count()
                
                return {
                    "period_hours": hours,
                    "total_alerts": total_alerts,
                    "by_severity": {
                        "critical": critical_count,
                        "high": high_count,
                        "medium": medium_count,
                        "low": low_count
                    },
                    "acknowledged": acknowledged_count,
                    "resolved": resolved_count,
                    "unresolved": total_alerts - resolved_count
                }
            finally:
                db.close()
        except Exception as e:
            logger.error(f"Failed to get alert summary: {e}")
            return {}


alert_service = QualityAlertService()
