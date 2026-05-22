#!/usr/bin/env python3
"""
技能性能监控脚本
实现技能调用统计、响应时间监控、成功率监控

功能:
- 技能调用统计（调用次数、调用频率、调用来源）
- 响应时间监控（平均响应时间、P95/P99响应时间、响应时间分布）
- 成功率监控（成功率统计、失败原因分析、告警机制）
- 性能报告生成
"""

import os
import sys
import json
import time
import logging
import argparse
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, asdict, field
from enum import Enum
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
import threading
import statistics

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


class MetricType(Enum):
    CALL_COUNT = "call_count"
    RESPONSE_TIME = "response_time"
    SUCCESS_RATE = "success_rate"
    ERROR_COUNT = "error_count"
    THROUGHPUT = "throughput"


class AlertSeverity(Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class TimeGranularity(Enum):
    MINUTE = "minute"
    HOUR = "hour"
    DAY = "day"
    WEEK = "week"
    MONTH = "month"


@dataclass
class SkillCallRecord:
    call_id: str
    skill_name: str
    timestamp: str
    duration_ms: float
    success: bool
    error_message: str = ""
    error_type: str = ""
    caller: str = ""
    department: str = ""
    input_size: int = 0
    output_size: int = 0
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


@dataclass
class PerformanceMetrics:
    skill_name: str
    period_start: str
    period_end: str
    total_calls: int
    successful_calls: int
    failed_calls: int
    success_rate: float
    avg_response_time_ms: float
    min_response_time_ms: float
    max_response_time_ms: float
    p50_response_time_ms: float
    p95_response_time_ms: float
    p99_response_time_ms: float
    throughput_per_minute: float
    error_types: Dict[str, int]
    callers: Dict[str, int]
    departments: Dict[str, int]
    timestamp: str = ""
    
    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()


@dataclass
class Alert:
    alert_id: str
    skill_name: str
    metric_type: MetricType
    severity: AlertSeverity
    message: str
    current_value: float
    threshold: float
    timestamp: str
    acknowledged: bool = False
    resolved: bool = False
    resolution_time: str = ""
    
    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()


@dataclass
class MonitoringConfig:
    collection_interval_seconds: int = 60
    retention_days: int = 30
    alert_thresholds: Dict[str, float] = None
    enabled_metrics: List[str] = None
    alert_recipients: List[str] = None
    
    def __post_init__(self):
        if self.alert_thresholds is None:
            self.alert_thresholds = {
                "success_rate_warning": 0.9,
                "success_rate_critical": 0.8,
                "response_time_warning_ms": 5000,
                "response_time_critical_ms": 10000,
                "error_rate_warning": 0.1,
                "error_rate_critical": 0.2,
            }
        if self.enabled_metrics is None:
            self.enabled_metrics = [m.value for m in MetricType]
        if self.alert_recipients is None:
            self.alert_recipients = []


class SkillCallCollector:
    """技能调用收集器"""
    
    def __init__(self, storage_path: str):
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self.logger = self._setup_logger()
        self._lock = threading.Lock()
        self._buffer: List[SkillCallRecord] = []
        self._buffer_size = 100
        self._last_flush = datetime.now()
    
    def _setup_logger(self) -> logging.Logger:
        logger = logging.getLogger('SkillCallCollector')
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        
        return logger
    
    def record_call(self, record: SkillCallRecord) -> None:
        with self._lock:
            self._buffer.append(record)
            
            if len(self._buffer) >= self._buffer_size:
                self._flush_buffer()
    
    def _flush_buffer(self) -> None:
        if not self._buffer:
            return
        
        date_str = datetime.now().strftime('%Y-%m-%d')
        file_path = self.storage_path / f"calls_{date_str}.jsonl"
        
        with open(file_path, 'a', encoding='utf-8') as f:
            for record in self._buffer:
                f.write(json.dumps(asdict(record), ensure_ascii=False) + '\n')
        
        self._buffer = []
        self._last_flush = datetime.now()
    
    def get_calls(self, skill_name: str = None, start_time: datetime = None,
                  end_time: datetime = None, limit: int = 1000) -> List[SkillCallRecord]:
        records = []
        
        if start_time is None:
            start_time = datetime.now() - timedelta(days=7)
        if end_time is None:
            end_time = datetime.now()
        
        current_date = start_time.date()
        end_date = end_time.date()
        
        while current_date <= end_date:
            date_str = current_date.strftime('%Y-%m-%d')
            file_path = self.storage_path / f"calls_{date_str}.jsonl"
            
            if file_path.exists():
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        for line in f:
                            try:
                                data = json.loads(line.strip())
                                record = SkillCallRecord(**data)
                                
                                record_time = datetime.fromisoformat(record.timestamp)
                                if start_time <= record_time <= end_time:
                                    if skill_name is None or record.skill_name == skill_name:
                                        records.append(record)
                                        
                                        if len(records) >= limit:
                                            return records
                            except Exception:
                                continue
                except Exception as e:
                    self.logger.error(f"读取调用记录失败 {file_path}: {e}")
            
            current_date += timedelta(days=1)
        
        return records
    
    def get_call_count_by_skill(self, start_time: datetime = None,
                                 end_time: datetime = None) -> Dict[str, int]:
        counts = defaultdict(int)
        records = self.get_calls(start_time=start_time, end_time=end_time, limit=100000)
        
        for record in records:
            counts[record.skill_name] += 1
        
        return dict(counts)
    
    def cleanup_old_records(self, retention_days: int = 30) -> int:
        cutoff_date = datetime.now() - timedelta(days=retention_days)
        removed_count = 0
        
        for file_path in self.storage_path.glob("calls_*.jsonl"):
            try:
                date_str = file_path.stem.replace("calls_", "")
                file_date = datetime.strptime(date_str, '%Y-%m-%d')
                
                if file_date < cutoff_date:
                    file_path.unlink()
                    removed_count += 1
            except Exception:
                continue
        
        return removed_count


class ResponseTimeAnalyzer:
    """响应时间分析器"""
    
    def __init__(self):
        self.logger = self._setup_logger()
    
    def _setup_logger(self) -> logging.Logger:
        logger = logging.getLogger('ResponseTimeAnalyzer')
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        
        return logger
    
    def analyze(self, records: List[SkillCallRecord]) -> Dict[str, Any]:
        if not records:
            return {
                "avg_ms": 0,
                "min_ms": 0,
                "max_ms": 0,
                "p50_ms": 0,
                "p95_ms": 0,
                "p99_ms": 0,
                "std_dev": 0,
                "distribution": {}
            }
        
        response_times = [r.duration_ms for r in records]
        
        sorted_times = sorted(response_times)
        n = len(sorted_times)
        
        def percentile(data: List[float], p: float) -> float:
            if not data:
                return 0
            k = (len(data) - 1) * p / 100
            f = int(k)
            c = f + 1 if f + 1 < len(data) else f
            if f == c:
                return data[f]
            return data[f] * (c - k) + data[c] * (k - f)
        
        distribution = self._create_distribution(response_times)
        
        return {
            "avg_ms": statistics.mean(response_times),
            "min_ms": min(response_times),
            "max_ms": max(response_times),
            "p50_ms": percentile(sorted_times, 50),
            "p95_ms": percentile(sorted_times, 95),
            "p99_ms": percentile(sorted_times, 99),
            "std_dev": statistics.stdev(response_times) if len(response_times) > 1 else 0,
            "distribution": distribution
        }
    
    def _create_distribution(self, response_times: List[float]) -> Dict[str, int]:
        buckets = {
            "0-100ms": 0,
            "100-500ms": 0,
            "500-1000ms": 0,
            "1000-2000ms": 0,
            "2000-5000ms": 0,
            "5000-10000ms": 0,
            "10000ms+": 0
        }
        
        for t in response_times:
            if t < 100:
                buckets["0-100ms"] += 1
            elif t < 500:
                buckets["100-500ms"] += 1
            elif t < 1000:
                buckets["500-1000ms"] += 1
            elif t < 2000:
                buckets["1000-2000ms"] += 1
            elif t < 5000:
                buckets["2000-5000ms"] += 1
            elif t < 10000:
                buckets["5000-10000ms"] += 1
            else:
                buckets["10000ms+"] += 1
        
        return buckets
    
    def get_trend(self, records: List[SkillCallRecord], 
                  granularity: TimeGranularity = TimeGranularity.HOUR) -> List[Dict[str, Any]]:
        if not records:
            return []
        
        grouped = defaultdict(list)
        
        for record in records:
            record_time = datetime.fromisoformat(record.timestamp)
            
            if granularity == TimeGranularity.MINUTE:
                key = record_time.strftime('%Y-%m-%d %H:%M')
            elif granularity == TimeGranularity.HOUR:
                key = record_time.strftime('%Y-%m-%d %H:00')
            elif granularity == TimeGranularity.DAY:
                key = record_time.strftime('%Y-%m-%d')
            elif granularity == TimeGranularity.WEEK:
                key = record_time.strftime('%Y-%W')
            else:
                key = record_time.strftime('%Y-%m')
            
            grouped[key].append(record.duration_ms)
        
        trend = []
        for key in sorted(grouped.keys()):
            times = grouped[key]
            trend.append({
                "period": key,
                "avg_ms": statistics.mean(times),
                "min_ms": min(times),
                "max_ms": max(times),
                "count": len(times)
            })
        
        return trend


class SuccessRateMonitor:
    """成功率监控器"""
    
    def __init__(self):
        self.logger = self._setup_logger()
    
    def _setup_logger(self) -> logging.Logger:
        logger = logging.getLogger('SuccessRateMonitor')
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        
        return logger
    
    def calculate_success_rate(self, records: List[SkillCallRecord]) -> float:
        if not records:
            return 1.0
        
        successful = sum(1 for r in records if r.success)
        return successful / len(records)
    
    def analyze_failures(self, records: List[SkillCallRecord]) -> Dict[str, Any]:
        failed_records = [r for r in records if not r.success]
        
        if not failed_records:
            return {
                "total_failures": 0,
                "error_types": {},
                "error_messages": {},
                "failure_rate": 0.0,
                "recent_failures": []
            }
        
        error_types = defaultdict(int)
        error_messages = defaultdict(int)
        
        for record in failed_records:
            if record.error_type:
                error_types[record.error_type] += 1
            if record.error_message:
                error_messages[record.error_message[:100]] += 1
        
        recent_failures = sorted(
            failed_records,
            key=lambda r: r.timestamp,
            reverse=True
        )[:10]
        
        return {
            "total_failures": len(failed_records),
            "error_types": dict(error_types),
            "error_messages": dict(error_messages),
            "failure_rate": len(failed_records) / len(records) if records else 0,
            "recent_failures": [
                {
                    "call_id": r.call_id,
                    "timestamp": r.timestamp,
                    "error_type": r.error_type,
                    "error_message": r.error_message[:200]
                }
                for r in recent_failures
            ]
        }
    
    def get_success_rate_trend(self, records: List[SkillCallRecord],
                                granularity: TimeGranularity = TimeGranularity.HOUR) -> List[Dict[str, Any]]:
        if not records:
            return []
        
        grouped = defaultdict(list)
        
        for record in records:
            record_time = datetime.fromisoformat(record.timestamp)
            
            if granularity == TimeGranularity.MINUTE:
                key = record_time.strftime('%Y-%m-%d %H:%M')
            elif granularity == TimeGranularity.HOUR:
                key = record_time.strftime('%Y-%m-%d %H:00')
            elif granularity == TimeGranularity.DAY:
                key = record_time.strftime('%Y-%m-%d')
            elif granularity == TimeGranularity.WEEK:
                key = record_time.strftime('%Y-%W')
            else:
                key = record_time.strftime('%Y-%m')
            
            grouped[key].append(record)
        
        trend = []
        for key in sorted(grouped.keys()):
            period_records = grouped[key]
            successful = sum(1 for r in period_records if r.success)
            total = len(period_records)
            
            trend.append({
                "period": key,
                "success_rate": successful / total if total > 0 else 1.0,
                "total_calls": total,
                "successful_calls": successful,
                "failed_calls": total - successful
            })
        
        return trend


class AlertManager:
    """告警管理器"""
    
    def __init__(self, config: MonitoringConfig, storage_path: str):
        self.config = config
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self.alerts_file = self.storage_path / "alerts.json"
        self.logger = self._setup_logger()
        self._alerts: List[Alert] = []
        self._load_alerts()
    
    def _setup_logger(self) -> logging.Logger:
        logger = logging.getLogger('AlertManager')
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        
        return logger
    
    def _load_alerts(self) -> None:
        if self.alerts_file.exists():
            try:
                with open(self.alerts_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self._alerts = [Alert(**a) for a in data]
            except Exception:
                self._alerts = []
    
    def _save_alerts(self) -> None:
        with open(self.alerts_file, 'w', encoding='utf-8') as f:
            json.dump([asdict(a) for a in self._alerts], f, ensure_ascii=False, indent=2)
    
    def check_and_alert(self, skill_name: str, metrics: PerformanceMetrics) -> List[Alert]:
        alerts = []
        thresholds = self.config.alert_thresholds
        
        if metrics.success_rate < thresholds.get("success_rate_critical", 0.8):
            alert = Alert(
                alert_id=f"ALERT-{datetime.now().strftime('%Y%m%d%H%M%S')}-{skill_name}",
                skill_name=skill_name,
                metric_type=MetricType.SUCCESS_RATE,
                severity=AlertSeverity.CRITICAL,
                message=f"技能 '{skill_name}' 成功率严重下降: {metrics.success_rate:.2%}",
                current_value=metrics.success_rate,
                threshold=thresholds["success_rate_critical"]
            )
            alerts.append(alert)
            self._alerts.append(alert)
            
        elif metrics.success_rate < thresholds.get("success_rate_warning", 0.9):
            alert = Alert(
                alert_id=f"ALERT-{datetime.now().strftime('%Y%m%d%H%M%S')}-{skill_name}",
                skill_name=skill_name,
                metric_type=MetricType.SUCCESS_RATE,
                severity=AlertSeverity.WARNING,
                message=f"技能 '{skill_name}' 成功率下降: {metrics.success_rate:.2%}",
                current_value=metrics.success_rate,
                threshold=thresholds["success_rate_warning"]
            )
            alerts.append(alert)
            self._alerts.append(alert)
        
        if metrics.avg_response_time_ms > thresholds.get("response_time_critical_ms", 10000):
            alert = Alert(
                alert_id=f"ALERT-{datetime.now().strftime('%Y%m%d%H%M%S')}-{skill_name}",
                skill_name=skill_name,
                metric_type=MetricType.RESPONSE_TIME,
                severity=AlertSeverity.CRITICAL,
                message=f"技能 '{skill_name}' 响应时间过长: {metrics.avg_response_time_ms:.0f}ms",
                current_value=metrics.avg_response_time_ms,
                threshold=thresholds["response_time_critical_ms"]
            )
            alerts.append(alert)
            self._alerts.append(alert)
            
        elif metrics.avg_response_time_ms > thresholds.get("response_time_warning_ms", 5000):
            alert = Alert(
                alert_id=f"ALERT-{datetime.now().strftime('%Y%m%d%H%M%S')}-{skill_name}",
                skill_name=skill_name,
                metric_type=MetricType.RESPONSE_TIME,
                severity=AlertSeverity.WARNING,
                message=f"技能 '{skill_name}' 响应时间较慢: {metrics.avg_response_time_ms:.0f}ms",
                current_value=metrics.avg_response_time_ms,
                threshold=thresholds["response_time_warning_ms"]
            )
            alerts.append(alert)
            self._alerts.append(alert)
        
        if alerts:
            self._save_alerts()
            for alert in alerts:
                self.logger.warning(f"告警: {alert.message}")
        
        return alerts
    
    def get_active_alerts(self, skill_name: str = None) -> List[Alert]:
        active = [a for a in self._alerts if not a.resolved]
        
        if skill_name:
            active = [a for a in active if a.skill_name == skill_name]
        
        return sorted(active, key=lambda a: a.timestamp, reverse=True)
    
    def acknowledge_alert(self, alert_id: str) -> bool:
        for alert in self._alerts:
            if alert.alert_id == alert_id:
                alert.acknowledged = True
                self._save_alerts()
                return True
        return False
    
    def resolve_alert(self, alert_id: str) -> bool:
        for alert in self._alerts:
            if alert.alert_id == alert_id:
                alert.resolved = True
                alert.resolution_time = datetime.now().isoformat()
                self._save_alerts()
                return True
        return False
    
    def cleanup_old_alerts(self, days: int = 30) -> int:
        cutoff = datetime.now() - timedelta(days=days)
        
        original_count = len(self._alerts)
        self._alerts = [
            a for a in self._alerts
            if datetime.fromisoformat(a.timestamp) > cutoff or not a.resolved
        ]
        
        self._save_alerts()
        return original_count - len(self._alerts)


class SkillPerformanceMonitor:
    """技能性能监控主类"""
    
    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root).resolve()
        self.storage_path = self.project_root / "monitoring"
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        self.config = self._load_config()
        self.collector = SkillCallCollector(str(self.storage_path / "calls"))
        self.response_analyzer = ResponseTimeAnalyzer()
        self.success_monitor = SuccessRateMonitor()
        self.alert_manager = AlertManager(self.config, str(self.storage_path))
        
        self.logger = self._setup_logger()
    
    def _setup_logger(self) -> logging.Logger:
        logger = logging.getLogger('SkillPerformanceMonitor')
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        
        return logger
    
    def _load_config(self) -> MonitoringConfig:
        config_file = self.storage_path / "monitoring_config.json"
        
        if config_file.exists():
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return MonitoringConfig(**data)
            except Exception:
                pass
        
        return MonitoringConfig()
    
    def _save_config(self) -> None:
        config_file = self.storage_path / "monitoring_config.json"
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(asdict(self.config), f, indent=2, ensure_ascii=False)
    
    def record_skill_call(self, skill_name: str, duration_ms: float, success: bool,
                          error_message: str = "", error_type: str = "",
                          caller: str = "", department: str = "",
                          metadata: Dict[str, Any] = None) -> str:
        call_id = f"CALL-{datetime.now().strftime('%Y%m%d%H%M%S')}-{skill_name}"
        
        record = SkillCallRecord(
            call_id=call_id,
            skill_name=skill_name,
            timestamp=datetime.now().isoformat(),
            duration_ms=duration_ms,
            success=success,
            error_message=error_message,
            error_type=error_type,
            caller=caller,
            department=department,
            metadata=metadata
        )
        
        self.collector.record_call(record)
        
        return call_id
    
    def get_skill_metrics(self, skill_name: str, 
                          start_time: datetime = None,
                          end_time: datetime = None) -> PerformanceMetrics:
        if start_time is None:
            start_time = datetime.now() - timedelta(hours=24)
        if end_time is None:
            end_time = datetime.now()
        
        records = self.collector.get_calls(
            skill_name=skill_name,
            start_time=start_time,
            end_time=end_time
        )
        
        if not records:
            return PerformanceMetrics(
                skill_name=skill_name,
                period_start=start_time.isoformat(),
                period_end=end_time.isoformat(),
                total_calls=0,
                successful_calls=0,
                failed_calls=0,
                success_rate=1.0,
                avg_response_time_ms=0,
                min_response_time_ms=0,
                max_response_time_ms=0,
                p50_response_time_ms=0,
                p95_response_time_ms=0,
                p99_response_time_ms=0,
                throughput_per_minute=0,
                error_types={},
                callers={},
                departments={}
            )
        
        successful = [r for r in records if r.success]
        failed = [r for r in records if not r.success]
        
        response_analysis = self.response_analyzer.analyze(records)
        
        duration_hours = (end_time - start_time).total_seconds() / 3600
        throughput = len(records) / (duration_hours * 60) if duration_hours > 0 else 0
        
        error_types = defaultdict(int)
        callers = defaultdict(int)
        departments = defaultdict(int)
        
        for r in records:
            if r.error_type:
                error_types[r.error_type] += 1
            if r.caller:
                callers[r.caller] += 1
            if r.department:
                departments[r.department] += 1
        
        metrics = PerformanceMetrics(
            skill_name=skill_name,
            period_start=start_time.isoformat(),
            period_end=end_time.isoformat(),
            total_calls=len(records),
            successful_calls=len(successful),
            failed_calls=len(failed),
            success_rate=len(successful) / len(records),
            avg_response_time_ms=response_analysis["avg_ms"],
            min_response_time_ms=response_analysis["min_ms"],
            max_response_time_ms=response_analysis["max_ms"],
            p50_response_time_ms=response_analysis["p50_ms"],
            p95_response_time_ms=response_analysis["p95_ms"],
            p99_response_time_ms=response_analysis["p99_ms"],
            throughput_per_minute=throughput,
            error_types=dict(error_types),
            callers=dict(callers),
            departments=dict(departments)
        )
        
        self.alert_manager.check_and_alert(skill_name, metrics)
        
        return metrics
    
    def get_all_skills_metrics(self, start_time: datetime = None,
                                end_time: datetime = None) -> Dict[str, PerformanceMetrics]:
        call_counts = self.collector.get_call_count_by_skill(start_time, end_time)
        
        metrics = {}
        for skill_name in call_counts.keys():
            metrics[skill_name] = self.get_skill_metrics(skill_name, start_time, end_time)
        
        return metrics
    
    def get_performance_report(self, skill_name: str = None,
                               start_time: datetime = None,
                               end_time: datetime = None) -> str:
        if start_time is None:
            start_time = datetime.now() - timedelta(hours=24)
        if end_time is None:
            end_time = datetime.now()
        
        lines = [
            "# 技能性能监控报告",
            "",
            f"报告时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"统计周期: {start_time.strftime('%Y-%m-%d %H:%M')} - {end_time.strftime('%Y-%m-%d %H:%M')}",
            "",
        ]
        
        if skill_name:
            metrics = self.get_skill_metrics(skill_name, start_time, end_time)
            lines.extend(self._format_skill_metrics(metrics))
        else:
            all_metrics = self.get_all_skills_metrics(start_time, end_time)
            
            lines.append("## 技能概览")
            lines.append("")
            lines.append("| 技能名称 | 调用次数 | 成功率 | 平均响应时间 |")
            lines.append("|----------|----------|--------|--------------|")
            
            for name, m in sorted(all_metrics.items(), key=lambda x: x[1].total_calls, reverse=True):
                lines.append(f"| {name} | {m.total_calls} | {m.success_rate:.1%} | {m.avg_response_time_ms:.0f}ms |")
            
            lines.append("")
            
            for name, m in all_metrics.items():
                lines.extend(self._format_skill_metrics(m))
        
        active_alerts = self.alert_manager.get_active_alerts(skill_name)
        if active_alerts:
            lines.extend([
                "",
                "## 活跃告警",
                "",
            ])
            for alert in active_alerts[:10]:
                lines.append(f"- [{alert.severity.value}] {alert.message}")
        
        return '\n'.join(lines)
    
    def _format_skill_metrics(self, metrics: PerformanceMetrics) -> List[str]:
        lines = [
            f"## {metrics.skill_name}",
            "",
            "### 调用统计",
            "",
            f"- 总调用次数: {metrics.total_calls}",
            f"- 成功次数: {metrics.successful_calls}",
            f"- 失败次数: {metrics.failed_calls}",
            f"- 成功率: {metrics.success_rate:.2%}",
            f"- 吞吐量: {metrics.throughput_per_minute:.2f} 次/分钟",
            "",
            "### 响应时间",
            "",
            f"- 平均: {metrics.avg_response_time_ms:.0f}ms",
            f"- 最小: {metrics.min_response_time_ms:.0f}ms",
            f"- 最大: {metrics.max_response_time_ms:.0f}ms",
            f"- P50: {metrics.p50_response_time_ms:.0f}ms",
            f"- P95: {metrics.p95_response_time_ms:.0f}ms",
            f"- P99: {metrics.p99_response_time_ms:.0f}ms",
            "",
        ]
        
        if metrics.error_types:
            lines.extend([
                "### 错误类型分布",
                "",
            ])
            for error_type, count in sorted(metrics.error_types.items(), key=lambda x: x[1], reverse=True):
                lines.append(f"- {error_type}: {count}")
            lines.append("")
        
        if metrics.callers:
            lines.extend([
                "### 调用来源",
                "",
            ])
            for caller, count in sorted(metrics.callers.items(), key=lambda x: x[1], reverse=True)[:5]:
                lines.append(f"- {caller}: {count}")
            lines.append("")
        
        return lines
    
    def export_metrics(self, output_path: str, format: str = "json",
                       skill_name: str = None,
                       start_time: datetime = None,
                       end_time: datetime = None) -> str:
        if skill_name:
            metrics = self.get_skill_metrics(skill_name, start_time, end_time)
            data = asdict(metrics)
        else:
            all_metrics = self.get_all_skills_metrics(start_time, end_time)
            data = {name: asdict(m) for name, m in all_metrics.items()}
        
        if format == "json":
            output = json.dumps(data, ensure_ascii=False, indent=2)
        else:
            output = self.get_performance_report(skill_name, start_time, end_time)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(output)
        
        return output_path


def main():
    parser = argparse.ArgumentParser(description='技能性能监控脚本')
    
    parser.add_argument('--project-root', '-p', default='.', help='项目根目录')
    
    subparsers = parser.add_subparsers(dest='command', help='可用命令')
    
    record_parser = subparsers.add_parser('record', help='记录技能调用')
    record_parser.add_argument('--skill', required=True, help='技能名称')
    record_parser.add_argument('--duration', type=float, required=True, help='执行时间(ms)')
    record_parser.add_argument('--success', type=bool, default=True, help='是否成功')
    record_parser.add_argument('--error', default='', help='错误信息')
    record_parser.add_argument('--error-type', default='', help='错误类型')
    record_parser.add_argument('--caller', default='', help='调用者')
    record_parser.add_argument('--department', default='', help='部门')
    
    metrics_parser = subparsers.add_parser('metrics', help='获取性能指标')
    metrics_parser.add_argument('--skill', help='技能名称(不指定则获取所有)')
    metrics_parser.add_argument('--hours', type=int, default=24, help='统计时长(小时)')
    
    report_parser = subparsers.add_parser('report', help='生成性能报告')
    report_parser.add_argument('--skill', help='技能名称')
    report_parser.add_argument('--hours', type=int, default=24, help='统计时长(小时)')
    report_parser.add_argument('--output', '-o', help='输出文件路径')
    
    alerts_parser = subparsers.add_parser('alerts', help='查看告警')
    alerts_parser.add_argument('--skill', help='技能名称')
    alerts_parser.add_argument('--acknowledge', help='确认告警ID')
    alerts_parser.add_argument('--resolve', help='解决告警ID')
    
    export_parser = subparsers.add_parser('export', help='导出指标数据')
    export_parser.add_argument('--skill', help='技能名称')
    export_parser.add_argument('--hours', type=int, default=24, help='统计时长(小时)')
    export_parser.add_argument('--output', '-o', required=True, help='输出文件路径')
    export_parser.add_argument('--format', choices=['json', 'markdown'], default='json', help='输出格式')
    
    cleanup_parser = subparsers.add_parser('cleanup', help='清理旧数据')
    cleanup_parser.add_argument('--days', type=int, default=30, help='保留天数')
    
    args = parser.parse_args()
    
    monitor = SkillPerformanceMonitor(args.project_root)
    
    if args.command == 'record':
        call_id = monitor.record_skill_call(
            skill_name=args.skill,
            duration_ms=args.duration,
            success=args.success,
            error_message=args.error,
            error_type=args.error_type,
            caller=args.caller,
            department=args.department
        )
        print(f"调用记录已保存: {call_id}")
        
    elif args.command == 'metrics':
        start_time = datetime.now() - timedelta(hours=args.hours)
        
        if args.skill:
            metrics = monitor.get_skill_metrics(args.skill, start_time)
            print(f"\n=== {args.skill} 性能指标 ===")
            print(f"调用次数: {metrics.total_calls}")
            print(f"成功率: {metrics.success_rate:.2%}")
            print(f"平均响应时间: {metrics.avg_response_time_ms:.0f}ms")
            print(f"P95响应时间: {metrics.p95_response_time_ms:.0f}ms")
        else:
            all_metrics = monitor.get_all_skills_metrics(start_time)
            print(f"\n=== 所有技能性能指标 ===")
            for name, m in sorted(all_metrics.items(), key=lambda x: x[1].total_calls, reverse=True):
                print(f"{name}: {m.total_calls}次, 成功率{m.success_rate:.1%}, 平均{m.avg_response_time_ms:.0f}ms")
        
    elif args.command == 'report':
        start_time = datetime.now() - timedelta(hours=args.hours)
        report = monitor.get_performance_report(args.skill, start_time)
        
        if args.output:
            with open(args.output, 'w', encoding='utf-8') as f:
                f.write(report)
            print(f"报告已保存: {args.output}")
        else:
            print(report)
        
    elif args.command == 'alerts':
        if args.acknowledge:
            if monitor.alert_manager.acknowledge_alert(args.acknowledge):
                print(f"告警已确认: {args.acknowledge}")
            else:
                print(f"告警不存在: {args.acknowledge}")
        elif args.resolve:
            if monitor.alert_manager.resolve_alert(args.resolve):
                print(f"告警已解决: {args.resolve}")
            else:
                print(f"告警不存在: {args.resolve}")
        else:
            alerts = monitor.alert_manager.get_active_alerts(args.skill)
            print(f"\n=== 活跃告警 ({len(alerts)}) ===")
            for alert in alerts[:20]:
                print(f"[{alert.severity.value}] {alert.skill_name}: {alert.message}")
                print(f"  时间: {alert.timestamp}")
                print(f"  ID: {alert.alert_id}")
                print()
        
    elif args.command == 'export':
        start_time = datetime.now() - timedelta(hours=args.hours)
        output_path = monitor.export_metrics(
            args.output, args.format, args.skill, start_time
        )
        print(f"数据已导出: {output_path}")
        
    elif args.command == 'cleanup':
        calls_removed = monitor.collector.cleanup_old_records(args.days)
        alerts_removed = monitor.alert_manager.cleanup_old_alerts(args.days)
        print(f"清理完成: 调用记录 {calls_removed} 个, 告警 {alerts_removed} 个")
        
    else:
        parser.print_help()
    
    return 0


if __name__ == '__main__':
    exit(main())
