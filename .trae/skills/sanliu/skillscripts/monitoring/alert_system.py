"""
智能告警系统 - Intelligent Alert System v3.3.0

五级告警机制：INFO → WARNING → CRITICAL → SEVERE → FATAL
支持：自定义规则、聚合降噪、多通道通知
"""

from enum import IntEnum
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Callable, Any
from datetime import datetime, timedelta
import json
import hashlib
import random
import asyncio
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AlertLevel(IntEnum):
    """五级告警级别"""
    INFO = 1       # 信息：正常运行信息
    WARNING = 2    # 警告：接近阈值或轻微异常
    CRITICAL = 3   # 严重：指标偏离需关注
    SEVERE = 4     # 非常严重：关键功能受影响
    FATAL = 5      # 致命：系统不可用
    
    def __str__(self):
        return ['INFO', 'WARNING', 'CRITICAL', 'SEVERE', 'FATAL'][self.value - 1]
    
    def get_emoji(self) -> str:
        """获取级别对应的emoji图标"""
        emojis = {
            self.INFO: 'ℹ️',
            self.WARNING: '⚠️',
            self.CRITICAL: '🔴',
            self.SEVERE: '💥',
            self.FATAL: '☠️'
        }
        return emojis.get(self, '')
    
    @classmethod
    def from_string(cls, level_str: str) -> 'AlertLevel':
        """从字符串转换为AlertLevel"""
        mapping = {
            'INFO': cls.INFO,
            'WARNING': cls.WARNING,
            'CRITICAL': cls.CRITICAL,
            'SEVERE': cls.SEVERE,
            'FATAL': cls.FATAL
        }
        return mapping.get(level_str.upper(), cls.INFO)


@dataclass
class Alert:
    """告警数据结构"""
    id: str
    level: AlertLevel
    source: str           # 来源模块
    title: str            # 告警标题
    message: str          # 详细消息
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict = field(default_factory=dict)
    
    def to_dict(self) -> dict:
        """转换为字典格式"""
        return {
            'id': self.id,
            'level': str(self.level),
            'level_value': int(self.level),
            'source': self.source,
            'title': self.title,
            'message': self.message,
            'timestamp': self.timestamp.isoformat(),
            'metadata': self.metadata
        }
    
    def to_json(self) -> str:
        """转换为JSON字符串"""
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Alert':
        """从字典创建Alert对象"""
        return cls(
            id=data['id'],
            level=AlertLevel.from_string(data['level']),
            source=data['source'],
            title=data['title'],
            message=data['message'],
            timestamp=datetime.fromisoformat(data['timestamp']),
            metadata=data.get('metadata', {})
        )


class AlertAggregator:
    """
    告警聚合器 - 避免告警风暴
    
    使用滑动窗口和去重机制减少重复告警，
    防止在短时间内产生大量相似告警淹没运维人员。
    """
    
    def __init__(self, window_seconds: int = 60, max_alerts_per_source: int = 10):
        """
        初始化聚合器
        
        Args:
            window_seconds: 滑动窗口大小（秒）
            max_alerts_per_source: 每个来源最大允许的告警数
        """
        self.window = window_seconds
        self.max_per_source = max_alerts_per_source
        self.alert_buffer: Dict[str, List[Alert]] = {}
        self.suppressed_count = 0
        self.total_received = 0
        self.total_sent = 0
        
    def add(self, alert: Alert) -> bool:
        """
        添加告警，返回是否应该发送
        
        Args:
            alert: 告警对象
            
        Returns:
            True表示应该发送，False表示被抑制
        """
        self.total_received += 1
        
        key = f"{alert.source}:{alert.title}"
        
        # 清理过期告警
        self._cleanup_expired(key)
        
        # FATAL和SEVERE级别始终发送
        if alert.level in [AlertLevel.FATAL, AlertLevel.SEVERE]:
            self.alert_buffer.setdefault(key, []).append(alert)
            self.total_sent += 1
            return True
        
        # 检查是否超过阈值
        if key in self.alert_buffer and len(self.alert_buffer[key]) >= self.max_per_source:
            self.suppressed_count += 1
            logger.debug(f"Alert suppressed: {alert.title} (rate limit reached)")
            return False
        
        if key not in self.alert_buffer:
            self.alert_buffer[key] = []
        self.alert_buffer[key].append(alert)
        self.total_sent += 1
        return True
    
    def _cleanup_expired(self, key: str):
        """清理过期告警"""
        now = datetime.now()
        if key in self.alert_buffer:
            self.alert_buffer[key] = [
                a for a in self.alert_buffer[key] 
                if (now - a.timestamp).total_seconds() < self.window
            ]
            if not self.alert_buffer[key]:
                del self.alert_buffer[key]
    
    def get_stats(self) -> dict:
        """获取聚合统计信息"""
        return {
            'total_received': self.total_received,
            'total_sent': self.total_sent,
            'suppressed_count': self.suppressed_count,
            'suppression_rate': (self.suppressed_count / max(self.total_received, 1)) * 100,
            'active_sources': len(self.alert_buffer),
            'buffer_size': sum(len(v) for v in self.alert_buffer.values())
        }
    
    def clear(self):
        """清空所有缓冲区"""
        self.alert_buffer.clear()
        self.suppressed_count = 0


class MultiChannelNotifier:
    """
    多通道通知器
    
    支持多种通知渠道：
    - Webhook (HTTP回调)
    - Console (控制台输出)
    - Log (日志文件记录)
    - Email (邮件通知)
    - Slack/钉钉/企业微信 (即时通讯)
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """
        初始化通知器
        
        Args:
            config_path: 配置文件路径
        """
        self.channels = {
            'webhook': self._send_webhook,
            'console': self._send_console,
            'log': self._send_log,
            'email': self._send_email,
            'slack': self._send_slack,
            'dingtalk': self._send_dingtalk,
            'wecom': self._send_wecom
        }
        self.config = self._load_config(config_path)
        self.send_history: List[dict] = []
        
    def _load_config(self, config_path: Optional[str]) -> dict:
        """加载配置"""
        if config_path and Path(config_path).exists():
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}
    
    async def send(self, alert: Alert, channels: List[str] = None) -> Dict[str, bool]:
        """
        发送告警到指定通道
        
        Args:
            alert: 告警对象
            channels: 通知通道列表，默认使用console和log
            
        Returns:
            各通道发送结果字典 {channel_name: success}
        """
        channels = channels or ['console', 'log']
        results = {}
        
        for channel in channels:
            handler = self.channels.get(channel)
            if handler:
                try:
                    await handler(alert)
                    results[channel] = True
                    logger.info(f"Alert sent via {channel}: {alert.title}")
                except Exception as e:
                    results[channel] = False
                    logger.error(f"Failed to send via {channel}: {e}")
            else:
                results[channel] = False
                logger.warning(f"Unknown channel: {channel}")
        
        self.send_history.append({
            'alert_id': alert.id,
            'channels': channels,
            'results': results,
            'timestamp': datetime.now().isoformat()
        })
        
        return results
    
    async def _send_webhook(self, alert: Alert):
        """Webhook通知"""
        try:
            import aiohttp
            url = self.config.get('webhook_url')
            if url:
                payload = {'alert': alert.to_dict()}
                timeout = aiohttp.ClientTimeout(total=10)
                async with aiohttp.ClientSession(timeout=timeout) as session:
                    async with session.post(url, json=payload) as response:
                        if response.status != 200:
                            raise Exception(f"Webhook returned status {response.status}")
        except ImportError:
            logger.warning("aiohttp not installed, webhook notification skipped")
        except Exception as e:
            raise Exception(f"Webhook send failed: {e}")
    
    async def _send_console(self, alert: Alert):
        """控制台输出"""
        level_str = str(alert.level)
        emoji = alert.level.get_emoji()
        timestamp = alert.timestamp.strftime('%Y-%m-%d %H:%M:%S')
        print(f"{emoji} [{timestamp}] [{level_str}] [{alert.source}] {alert.title}: {alert.message}")
    
    async def _send_log(self, alert: Alert):
        """日志记录"""
        log_file = self.config.get('log_file', 'logs/alerts.log')
        log_dir = Path(log_file).parent
        log_dir.mkdir(parents=True, exist_ok=True)
        
        timestamp = alert.timestamp.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
        log_entry = f"{timestamp} | {alert.level} | {alert.source} | {alert.title} | {alert.message}\n"
        
        with open(log_file, 'a', encoding='utf-8') as f:
            f.write(log_entry)
    
    async def _send_email(self, alert: Alert):
        """邮件通知（简化实现）"""
        import smtplib
        from email.mime.text import MIMEText
        from email.mime.multipart import MIMEMultipart
        
        smtp_config = self.config.get('smtp', {})
        if not smtp_config:
            logger.warning("SMTP configuration not found")
            return
        
        msg = MIMEMultipart()
        msg['From'] = smtp_config.get('from', 'alerts@system.com')
        msg['To'] = ', '.join(smtp_config.get('to', []))
        msg['Subject'] = f"[{alert.level}] {alert.title}"
        
        body = f"""
告警详情：
- 级别: {alert.level}
- 来源: {alert.source}
- 标题: {alert.title}
- 消息: {alert.message}
- 时间: {alert.timestamp}
- 元数据: {json.dumps(alert.metadata, ensure_ascii=False)}
        """
        msg.attach(MIMEText(body, 'plain', 'utf-8'))
        
        try:
            with smtplib.SMTP(
                smtp_config.get('host', 'localhost'),
                smtp_config.get('port', 25)
            ) as server:
                if smtp_config.get('use_tls'):
                    server.starttls()
                if smtp_config.get('username'):
                    server.login(smtp_config['username'], smtp_config.get('password', ''))
                server.send_message(msg)
        except Exception as e:
            raise Exception(f"Email send failed: {e}")
    
    async def _send_slack(self, alert: Alert):
        """Slack通知"""
        webhook_url = self.config.get('slack_webhook_url')
        if not webhook_url:
            return
        
        emoji = alert.level.get_emoji()
        payload = {
            'text': f"{emoji} *[{alert.level}]* `{alert.source}`: {alert.title}",
            'attachments': [{
                'color': self._get_slack_color(alert.level),
                'fields': [
                    {'title': 'Message', 'value': alert.message, 'short': False},
                    {'title': 'Source', 'value': alert.source, 'short': True},
                    {'title': 'Time', 'value': alert.timestamp.isoformat(), 'short': True}
                ]
            }]
        }
        
        try:
            import aiohttp
            async with aiohttp.ClientSession() as session:
                await session.post(webhook_url, json=payload)
        except ImportError:
            logger.warning("aiohttp not installed, slack notification skipped")
    
    async def _send_dingtalk(self, alert: Alert):
        """钉钉机器人通知"""
        webhook_url = self.config.get('dingtalk_webhook_url')
        if not webhook_url:
            return
        
        emoji = alert.level.get_emoji()
        payload = {
            'msgtype': 'markdown',
            'markdown': {
                'title': f"{emoji} {alert.title}",
                'text': f"### {emoji} {alert.level} 告警\n\n"
                       f"**来源**: {alert.source}\n\n"
                       f"**标题**: {alert.title}\n\n"
                       f"**详情**: {alert.message}\n\n"
                       f"**时间**: {alert.timestamp}"
            }
        }
        
        try:
            import aiohttp
            async with aiohttp.ClientSession() as session:
                await session.post(webhook_url, json=payload)
        except ImportError:
            logger.warning("aiohttp not installed, dingtalk notification skipped")
    
    async def _send_wecom(self, alert: Alert):
        """企业微信通知"""
        webhook_url = self.config.get('wecom_webhook_url')
        if not webhook_url:
            return
        
        emoji = alert.level.get_emoji()
        payload = {
            'msgtype': 'markdown',
            'markdown': {
                'content': f"{emoji} **<font color=\\\"warning\\\">{alert.level}</font>告警**\n\n"
                          f"> 来源: {alert.source}\n\n"
                          f"> 标题: {alert.title}\n\n"
                          f"> 详情: {alert.message}\n\n"
                          f"> 时间: {alert.timestamp}"
            }
        }
        
        try:
            import aiohttp
            async with aiohttp.ClientSession() as session:
                await session.post(webhook_url, json=payload)
        except ImportError:
            logger.warning("aiohttp not installed, wecom notification skipped")
    
    @staticmethod
    def _get_slack_color(level: AlertLevel) -> str:
        """获取Slack颜色代码"""
        colors = {
            AlertLevel.INFO: '#36a64f',
            AlertLevel.WARNING: '#ff9800',
            AlertLevel.CRITICAL: '#f44336',
            AlertLevel.SEVERE: '#9c27b0',
            AlertLevel.FATAL: '#000000'
        }
        return colors.get(level, '#808080')


class IntelligentAlertSystem:
    """
    智能告警系统主类
    
    整合五级告警、自定义规则、聚合降噪、多通道通知功能，
    提供统一的告警管理接口。
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """
        初始化智能告警系统
        
        Args:
            config_path: 配置文件路径
        """
        self.aggregator = AlertAggregator(
            window_seconds=60,
            max_alerts_per_source=10
        )
        self.notifier = MultiChannelNotifier(config_path)
        self.rules: Dict[str, dict] = {}  # 自定义告警规则
        self.alert_history: List[Alert] = []
        self.max_history_size = 10000
        self._load_rules(config_path)
        self._initialize_default_rules()
        logger.info("Intelligent Alert System v3.3.0 initialized")
    
    def _load_rules(self, config_path: Optional[str]):
        """从配置文件加载规则"""
        if config_path and Path(config_path).exists():
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
                rules = config.get('rules', {})
                for rule_id, rule_config in rules.items():
                    # 简化版规则加载，实际可扩展为动态条件解析
                    pass
    
    def _initialize_default_rules(self):
        """初始化默认告警规则"""
        default_rules = [
            {
                'rule_id': 'high_error_rate',
                'condition': lambda ctx: ctx.get('error_rate', 0) > 5,
                'level': AlertLevel.CRITICAL,
                'source': 'api_monitor',
                'title': 'Error rate too high',
                'message_template': 'Error rate is {error_rate}% (threshold: 5%)',
                'cooldown': 300
            },
            {
                'rule_id': 'low_test_coverage',
                'condition': lambda ctx: ctx.get('test_coverage', 100) < 70,
                'level': AlertLevel.WARNING,
                'source': 'quality_monitor',
                'title': 'Test coverage below threshold',
                'message_template': 'Test coverage is {test_coverage}% (threshold: 70%)',
                'cooldown': 600
            },
            {
                'rule_id': 'high_response_time',
                'condition': lambda ctx: ctx.get('response_time_ms', 0) > 1000,
                'level': AlertLevel.WARNING,
                'source': 'performance_monitor',
                'title': 'Response time exceeded',
                'message_template': 'API response time is {response_time_ms}ms (threshold: 1000ms)',
                'cooldown': 120
            },
            {
                'rule_id': 'memory_usage_high',
                'condition': lambda ctx: ctx.get('memory_usage_mb', 0) > 450,
                'level': AlertLevel.CRITICAL,
                'source': 'resource_monitor',
                'title': 'Memory usage critical',
                'message_template': 'Memory usage is {memory_usage_mb}MB (threshold: 450MB)',
                'cooldown': 180
            },
            {
                'rule_id': 'service_down',
                'condition': lambda ctx: ctx.get('service_status') == 'down',
                'level': AlertLevel.FATAL,
                'source': 'health_checker',
                'title': 'Service is down',
                'message_template': 'Service {service_name} is down!',
                'cooldown': 60
            }
        ]
        
        for rule_def in default_rules:
            self.add_rule(**rule_def)
    
    def add_rule(self, rule_id: str, condition: Callable, level: AlertLevel, 
                 source: str = 'custom', title: str = '', message_template: str = '',
                 cooldown: int = 300, **kwargs):
        """
        添加自定义告警规则
        
        Args:
            rule_id: 规则唯一标识
            condition: 判断函数，接收上下文字典返回布尔值
            level: 触发时的告警级别
            source: 告警来源
            title: 告警标题
            message_template: 消息模板（支持{key}格式）
            cooldown: 冷却时间（秒），防止重复触发
        """
        self.rules[rule_id] = {
            'condition': condition,
            'level': level,
            'source': source,
            'title': title or f'Rule {rule_id}',
            'message_template': message_template or 'Threshold exceeded',
            'cooldown': cooldown,
            'last_triggered': None,
            **kwargs
        }
        logger.info(f"Rule added: {rule_id} (level={level}, source={source})")
    
    def remove_rule(self, rule_id: str) -> bool:
        """移除告警规则"""
        if rule_id in self.rules:
            del self.rules[rule_id]
            logger.info(f"Rule removed: {rule_id}")
            return True
        return False
    
    def check_metric(self, metric_name: str, value: float, threshold: float, 
                     operator: str = '>', level: AlertLevel = AlertLevel.WARNING,
                     source: str = 'monitor') -> Optional[Alert]:
        """
        检查指标是否触发告警
        
        Args:
            metric_name: 指标名称
            value: 当前值
            threshold: 阈值
            operator: 比较操作符 ('>', '<', '>=', '<=', '==', '!=')
            level: 告警级别
            source: 来源
            
        Returns:
            Alert对象或None
        """
        operators = {
            '>': lambda a, b: a > b,
            '<': lambda a, b: a < b,
            '>=': lambda a, b: a >= b,
            '<=': lambda a, b: a <= b,
            '==': lambda a, b: a == b,
            '!=': lambda a, b: a != b
        }
        
        op_func = operators.get(operator, operators['>'])
        should_alert = op_func(value, threshold)
        
        if should_alert:
            alert = Alert(
                id=self._generate_alert_id(),
                level=level,
                source=source,
                title=f"{metric_name} threshold exceeded",
                message=f"{metric_name}={value}, threshold={threshold} ({operator})",
                metadata={
                    'metric': metric_name,
                    'value': value,
                    'threshold': threshold,
                    'operator': operator
                }
            )
            
            if self.aggregator.add(alert):
                self.alert_history.append(alert)
                self._trim_history()
                return alert
        return None
    
    def evaluate_rules(self, context: Dict[str, Any]) -> List[Alert]:
        """
        评估所有自定义规则
        
        Args:
            context: 包含各指标值的上下文字典
            
        Returns:
            触发的告警列表
        """
        triggered_alerts = []
        now = datetime.now()
        
        for rule_id, rule in self.rules.items():
            try:
                condition = rule['condition']
                
                if condition(context):
                    last_triggered = rule.get('last_triggered')
                    cooldown = rule.get('cooldown', 300)
                    
                    if last_triggered is None or (now - last_triggered).total_seconds() >= cooldown:
                        message = rule['message_template'].format(**context)
                        
                        alert = Alert(
                            id=self._generate_alert_id(),
                            level=rule['level'],
                            source=rule['source'],
                            title=rule['title'],
                            message=message,
                            metadata={
                                'rule_id': rule_id,
                                'context': context
                            }
                        )
                        
                        if self.aggregator.add(alert):
                            triggered_alerts.append(alert)
                            self.alert_history.append(alert)
                            self._trim_history()
                            rule['last_triggered'] = now
                            
            except Exception as e:
                logger.error(f"Error evaluating rule {rule_id}: {e}")
        
        return triggered_alerts
    
    async def process_alert(self, alert: Alert, channels: List[str] = None) -> bool:
        """
        处理单个告警（经过聚合后发送）
        
        Args:
            alert: 告警对象
            channels: 通知通道列表
            
        Returns:
            是否成功发送
        """
        results = await self.notifier.send(alert, channels)
        return all(results.values()) if results else False
    
    async def process_alerts_batch(self, alerts: List[Alert], channels: List[str] = None) -> Dict[str, bool]:
        """
        批量处理多个告警
        
        Args:
            alerts: 告警列表
            channels: 通知通道列表
            
        Returns:
            各告警的处理结果
        """
        results = {}
        for alert in alerts:
            success = await self.process_alert(alert, channels)
            results[alert.id] = success
        return results
    
    def get_alert_summary(self, since: Optional[datetime] = None) -> dict:
        """
        获取告警摘要统计
        
        Args:
            since: 统计起始时间，默认最近1小时
            
        Returns:
            摘要统计字典
        """
        since = since or (datetime.now() - timedelta(hours=1))
        recent = [a for a in self.alert_history if a.timestamp >= since]
        
        by_level = {}
        for level in AlertLevel:
            count = len([a for a in recent if a.level == level])
            by_level[str(level)] = count
        
        by_source = self._count_by_source(recent)
        
        return {
            'total': len(recent),
            'by_level': by_level,
            'by_source': by_source,
            'suppressed': self.aggregator.suppressed_count,
            'top_sources': self._get_top_sources(recent, 5),
            'aggregator_stats': self.aggregator.get_stats(),
            'time_range': {
                'since': since.isoformat(),
                'until': datetime.now().isoformat()
            }
        }
    
    def get_recent_alerts(self, limit: int = 50, level: Optional[AlertLevel] = None) -> List[Alert]:
        """
        获取最近的告警列表
        
        Args:
            limit: 返回数量限制
            level: 可选，按级别过滤
            
        Returns:
            告警列表（按时间倒序）
        """
        alerts = sorted(self.alert_history, key=lambda a: a.timestamp, reverse=True)
        
        if level:
            alerts = [a for a in alerts if a.level == level]
        
        return alerts[:limit]
    
    def export_alerts(self, filepath: str, format: str = 'json',
                     since: Optional[datetime] = None) -> bool:
        """
        导出告警历史
        
        Args:
            filepath: 导出文件路径
            format: 导出格式 ('json', 'csv')
            since: 起始时间
            
        Returns:
            是否成功
        """
        since = since or datetime.min
        alerts = [a for a in self.alert_history if a.timestamp >= since]
        
        try:
            if format == 'json':
                data = [a.to_dict() for a in alerts]
                with open(filepath, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
            
            elif format == 'csv':
                import csv
                with open(filepath, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    writer.writerow(['ID', 'Level', 'Source', 'Title', 'Message', 'Timestamp'])
                    for a in alerts:
                        writer.writerow([
                            a.id, a.level, a.source, a.title, 
                            a.message, a.timestamp.isoformat()
                        ])
            
            logger.info(f"Exported {len(alerts)} alerts to {filepath}")
            return True
            
        except Exception as e:
            logger.error(f"Export failed: {e}")
            return False
    
    def clear_history(self):
        """清空告警历史"""
        self.alert_history.clear()
        self.aggregator.clear()
        logger.info("Alert history cleared")
    
    def _generate_alert_id(self) -> str:
        """生成唯一告警ID"""
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S%f')
        random_str = hashlib.md5(str(random.random()).encode()).hexdigest()[:6]
        return f"ALT-{timestamp}-{random_str}"
    
    def _count_by_source(self, alerts: List[Alert]) -> Dict[str, int]:
        """按来源统计告警数"""
        counts = {}
        for alert in alerts:
            counts[alert.source] = counts.get(alert.source, 0) + 1
        return counts
    
    def _get_top_sources(self, alerts: List[Alert], limit: int) -> List[tuple]:
        """获取告警最多的来源TOP N"""
        counts = self._count_by_source(alerts)
        sorted_sources = sorted(counts.items(), key=lambda x: x[1], reverse=True)
        return sorted_sources[:limit]
    
    def _trim_history(self):
        """修剪历史记录，保持最大容量"""
        if len(self.alert_history) > self.max_history_size:
            self.alert_history = self.alert_history[-self.max_history_size:]
    
    def get_system_status(self) -> dict:
        """获取系统状态概览"""
        return {
            'version': 'v3.3.0',
            'uptime_start': datetime.now().isoformat(),  # 简化版
            'rules_count': len(self.rules),
            'history_size': len(self.alert_history),
            'aggregator_stats': self.aggregator.get_stats(),
            'recent_summary': self.get_alert_summary()
        }


# 使用示例和快速启动函数
async def quick_alert_example():
    """快速示例：演示基本用法"""
    system = IntelligentAlertSystem()
    
    # 示例1: 手动创建并发送告警
    alert = Alert(
        id=system._generate_alert_id(),
        level=AlertLevel.WARNING,
        source='demo',
        title='Test Alert',
        message='This is a test alert message'
    )
    await system.process_alert(alert)
    
    # 示例2: 使用指标检查
    system.check_metric('cpu_usage', 85.5, 80, '>', AlertLevel.CRITICAL, 'system_monitor')
    
    # 示例3: 使用规则评估
    context = {
        'error_rate': 6.2,
        'test_coverage': 65,
        'response_time_ms': 1200,
        'memory_usage_mb': 480
    }
    triggered = system.evaluate_rules(context)
    await system.process_alerts_batch(triggered)
    
    print("\n=== Alert System Summary ===")
    summary = system.get_alert_summary()
    print(json.dumps(summary, indent=2, ensure_ascii=False))


if __name__ == '__main__':
    print("="*60)
    print("  Intelligent Alert System v3.3.0")
    print("  五级告警机制 | 自定义规则 | 聚合降噪 | 多通道通知")
    print("="*60)
    
    system = IntelligentAlertSystem()
    
    print("\n✅ 已初始化默认告警规则:")
    for rule_id, rule in system.rules.items():
        print(f"   - {rule_id}: {rule['title']} [{rule['level']}]")
    
    print(f"\n📊 系统状态:")
    status = system.get_system_status()
    print(f"   版本: {status['version']}")
    print(f"   规则数: {status['rules_count']}")
    print(f"   支持的通知通道: {list(system.notifier.channels.keys())}")
    
    print("\n💡 运行 quick_alert_example() 查看完整示例")
