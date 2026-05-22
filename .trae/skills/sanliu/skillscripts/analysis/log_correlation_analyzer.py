#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
增强日志关联分析器 - Enhanced Log Correlation Analyzer

实现多源日志关联分析，支持：
- 多源日志智能关联
- 错误传播链识别与根因分析
- 跨系统调用链追踪
- 关联分析报告生成
- 时间序列关联分析
- 影响范围评估

使用示例:
    python log_correlation_analyzer.py --sources ./logs --analyze
    python log_correlation_analyzer.py --config correlation_config.json --report report.html
    python log_correlation_analyzer.py --source app.log --source db.log --cross-system
"""

import argparse
import hashlib
import json
import logging
import re
import sys
from collections import defaultdict, deque, Counter
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set, Tuple, Union


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class CorrelationType(Enum):
    ERROR_CHAIN = "error_chain"
    REQUEST_TRACE = "request_trace"
    TEMPORAL = "temporal"
    CAUSAL = "causal"
    CROSS_SYSTEM = "cross_system"
    RECURRING = "recurring"
    SEQUENCE = "sequence"
    PATTERN_MATCH = "pattern_match"
    DEPENDENCY = "dependency"
    RESOURCE_CONTENTION = "resource_contention"
    TIME_SERIES = "time_series"
    ANOMALY_CLUSTER = "anomaly_cluster"
    CIRCULAR_DEPENDENCY = "circular_dependency"
    SERVICE_MESH = "service_mesh"


class SeverityLevel(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class CorrelationConfidence(Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass
class LogSource:
    source_id: str
    name: str
    path: str
    system: str
    log_format: str
    timezone: str = "UTC"
    tags: Dict[str, str] = field(default_factory=dict)
    priority: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "source_id": self.source_id,
            "name": self.name,
            "path": self.path,
            "system": self.system,
            "log_format": self.log_format,
            "timezone": self.timezone,
            "tags": self.tags,
            "priority": self.priority
        }


@dataclass
class LogEvent:
    event_id: str
    timestamp: datetime
    level: str
    message: str
    source: LogSource
    logger_name: str = ""
    thread_id: str = ""
    trace_id: str = ""
    span_id: str = ""
    parent_span_id: str = ""
    correlation_id: str = ""
    session_id: str = ""
    user_id: str = ""
    request_id: str = ""
    extra: Dict[str, Any] = field(default_factory=dict)
    raw_line: str = ""
    line_number: int = 0
    error_type: str = ""
    stack_trace: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "event_id": self.event_id,
            "timestamp": self.timestamp.isoformat(),
            "level": self.level,
            "message": self.message,
            "source": self.source.source_id,
            "logger_name": self.logger_name,
            "thread_id": self.thread_id,
            "trace_id": self.trace_id,
            "span_id": self.span_id,
            "parent_span_id": self.parent_span_id,
            "correlation_id": self.correlation_id,
            "session_id": self.session_id,
            "user_id": self.user_id,
            "request_id": self.request_id,
            "extra": self.extra,
            "line_number": self.line_number,
            "error_type": self.error_type
        }


@dataclass
class ErrorPropagationNode:
    event: LogEvent
    depth: int = 0
    children: List['ErrorPropagationNode'] = field(default_factory=list)
    is_root: bool = False
    impact_score: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "event_id": self.event.event_id,
            "timestamp": self.event.timestamp.isoformat(),
            "message": self.event.message[:100],
            "source": self.event.source.name,
            "depth": self.depth,
            "is_root": self.is_root,
            "impact_score": self.impact_score,
            "children_count": len(self.children),
            "children": [c.to_dict() for c in self.children[:5]]
        }


@dataclass
class ErrorPropagationChain:
    chain_id: str
    root_cause: LogEvent
    propagation_path: List[LogEvent]
    affected_systems: Set[str]
    total_duration_seconds: float
    severity: SeverityLevel
    description: str
    confidence: CorrelationConfidence = CorrelationConfidence.MEDIUM
    impact_assessment: Dict[str, Any] = field(default_factory=dict)
    suggested_actions: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "chain_id": self.chain_id,
            "root_cause": self.root_cause.to_dict(),
            "propagation_path": [e.to_dict() for e in self.propagation_path],
            "affected_systems": list(self.affected_systems),
            "total_duration_seconds": self.total_duration_seconds,
            "severity": self.severity.value,
            "confidence": self.confidence.value,
            "description": self.description,
            "impact_assessment": self.impact_assessment,
            "suggested_actions": self.suggested_actions,
            "path_length": len(self.propagation_path)
        }


@dataclass
class CorrelationResult:
    correlation_id: str
    correlation_type: CorrelationType
    events: List[LogEvent]
    confidence_score: float
    time_span_seconds: float
    description: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    visualization_data: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "correlation_id": self.correlation_id,
            "correlation_type": self.correlation_type.value,
            "event_count": len(self.events),
            "confidence_score": self.confidence_score,
            "time_span_seconds": self.time_span_seconds,
            "description": self.description,
            "metadata": self.metadata,
            "visualization_data": self.visualization_data,
            "events": [e.to_dict() for e in self.events[:10]]
        }


@dataclass
class CrossSystemTrace:
    trace_id: str
    systems: Set[str]
    events: List[LogEvent]
    entry_point: Optional[LogEvent]
    exit_point: Optional[LogEvent]
    total_duration_seconds: float
    error_count: int
    warning_count: int
    service_calls: List[Dict[str, Any]] = field(default_factory=list)
    bottleneck_detected: bool = False
    bottleneck_service: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "trace_id": self.trace_id,
            "systems": list(self.systems),
            "event_count": len(self.events),
            "entry_point": self.entry_point.to_dict() if self.entry_point else None,
            "exit_point": self.exit_point.to_dict() if self.exit_point else None,
            "total_duration_seconds": self.total_duration_seconds,
            "error_count": self.error_count,
            "warning_count": self.warning_count,
            "service_calls": self.service_calls,
            "bottleneck_detected": self.bottleneck_detected,
            "bottleneck_service": self.bottleneck_service
        }


@dataclass
class TimeSeriesPoint:
    timestamp: datetime
    value: float
    event_count: int
    error_count: int
    warning_count: int
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp.isoformat(),
            "value": self.value,
            "event_count": self.event_count,
            "error_count": self.error_count,
            "warning_count": self.warning_count,
            "metadata": self.metadata
        }


@dataclass
class TimeSeriesCorrelation:
    correlation_id: str
    series_name: str
    points: List[TimeSeriesPoint]
    trend: str
    slope: float
    r_squared: float
    anomalies: List[Dict[str, Any]]
    seasonality_detected: bool
    forecast: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "correlation_id": self.correlation_id,
            "series_name": self.series_name,
            "point_count": len(self.points),
            "trend": self.trend,
            "slope": self.slope,
            "r_squared": self.r_squared,
            "anomaly_count": len(self.anomalies),
            "anomalies": self.anomalies[:10],
            "seasonality_detected": self.seasonality_detected,
            "forecast": self.forecast[:5]
        }


@dataclass
class CircularDependency:
    cycle_id: str
    nodes: List[str]
    cycle_length: int
    severity: SeverityLevel
    involved_events: List[LogEvent]
    description: str
    suggested_fix: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "cycle_id": self.cycle_id,
            "nodes": self.nodes,
            "cycle_length": self.cycle_length,
            "severity": self.severity.value,
            "involved_event_count": len(self.involved_events),
            "description": self.description,
            "suggested_fix": self.suggested_fix
        }


@dataclass
class RootCauseAnalysis:
    analysis_id: str
    root_cause_event: LogEvent
    contributing_factors: List[Dict[str, Any]]
    evidence_chain: List[Dict[str, Any]]
    confidence_score: float
    analysis_method: str
    related_metrics: Dict[str, Any]
    timeline: List[Dict[str, Any]]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "analysis_id": self.analysis_id,
            "root_cause_event": self.root_cause_event.to_dict(),
            "contributing_factors": self.contributing_factors,
            "evidence_chain": self.evidence_chain,
            "confidence_score": self.confidence_score,
            "analysis_method": self.analysis_method,
            "related_metrics": self.related_metrics,
            "timeline": self.timeline[:10]
        }


@dataclass
class ImpactAssessment:
    assessment_id: str
    affected_systems: List[str]
    affected_users: int
    affected_requests: int
    severity_distribution: Dict[str, int]
    estimated_downtime_minutes: float
    business_impact: str
    recovery_suggestions: List[str]
    trend_analysis: Optional[TimeSeriesCorrelation] = None
    cascade_effect: bool = False
    recovery_time_estimate_minutes: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        result = {
            "assessment_id": self.assessment_id,
            "affected_systems": self.affected_systems,
            "affected_users": self.affected_users,
            "affected_requests": self.affected_requests,
            "severity_distribution": self.severity_distribution,
            "estimated_downtime_minutes": self.estimated_downtime_minutes,
            "business_impact": self.business_impact,
            "recovery_suggestions": self.recovery_suggestions,
            "cascade_effect": self.cascade_effect,
            "recovery_time_estimate_minutes": self.recovery_time_estimate_minutes
        }
        if self.trend_analysis:
            result["trend_analysis"] = self.trend_analysis.to_dict()
        return result


@dataclass
class SourceHealthStatus:
    """日志源健康状态"""
    source_id: str
    source_name: str
    health_score: float
    error_rate: float
    warning_rate: float
    event_count: int
    error_count: int
    warning_count: int
    last_error_time: Optional[str]
    status: str
    issues: List[str] = field(default_factory=list)
    metrics: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "source_id": self.source_id,
            "source_name": self.source_name,
            "health_score": round(self.health_score, 2),
            "error_rate": round(self.error_rate, 4),
            "warning_rate": round(self.warning_rate, 4),
            "event_count": self.event_count,
            "error_count": self.error_count,
            "warning_count": self.warning_count,
            "last_error_time": self.last_error_time,
            "status": self.status,
            "issues": self.issues,
            "metrics": self.metrics
        }


@dataclass
class SourceDependency:
    """日志源依赖关系"""
    source_id: str
    depends_on: List[str]
    dependency_type: str
    strength: float
    evidence_count: int
    correlated_errors: int
    description: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "source_id": self.source_id,
            "depends_on": self.depends_on,
            "dependency_type": self.dependency_type,
            "strength": round(self.strength, 3),
            "evidence_count": self.evidence_count,
            "correlated_errors": self.correlated_errors,
            "description": self.description
        }


@dataclass
class ErrorPattern:
    """错误模式"""
    pattern_id: str
    pattern_type: str
    pattern_signature: str
    occurrence_count: int
    affected_sources: List[str]
    affected_systems: List[str]
    first_occurrence: str
    last_occurrence: str
    severity: SeverityLevel
    example_events: List[Dict[str, Any]]
    suggested_fix: str
    trend: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "pattern_id": self.pattern_id,
            "pattern_type": self.pattern_type,
            "pattern_signature": self.pattern_signature[:100],
            "occurrence_count": self.occurrence_count,
            "affected_sources": self.affected_sources,
            "affected_systems": self.affected_systems,
            "first_occurrence": self.first_occurrence,
            "last_occurrence": self.last_occurrence,
            "severity": self.severity.value,
            "example_count": len(self.example_events),
            "suggested_fix": self.suggested_fix,
            "trend": self.trend
        }


@dataclass
class ChainCluster:
    """错误传播链聚类"""
    cluster_id: str
    chains: List[ErrorPropagationChain]
    common_root_cause: str
    common_systems: Set[str]
    total_events: int
    cluster_severity: SeverityLevel
    cluster_description: str
    aggregated_actions: List[str]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "cluster_id": self.cluster_id,
            "chain_count": len(self.chains),
            "common_root_cause": self.common_root_cause[:100],
            "common_systems": list(self.common_systems),
            "total_events": self.total_events,
            "cluster_severity": self.cluster_severity.value,
            "cluster_description": self.cluster_description,
            "aggregated_actions": self.aggregated_actions
        }


@dataclass
class ExecutiveSummary:
    """执行摘要"""
    summary_id: str
    analysis_period: Dict[str, str]
    total_events_analyzed: int
    total_sources: int
    critical_issues_count: int
    high_issues_count: int
    overall_health_score: float
    top_issues: List[Dict[str, Any]]
    key_findings: List[str]
    immediate_actions: List[str]
    risk_level: str
    trend_indicator: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "summary_id": self.summary_id,
            "analysis_period": self.analysis_period,
            "total_events_analyzed": self.total_events_analyzed,
            "total_sources": self.total_sources,
            "critical_issues_count": self.critical_issues_count,
            "high_issues_count": self.high_issues_count,
            "overall_health_score": round(self.overall_health_score, 2),
            "top_issues": self.top_issues,
            "key_findings": self.key_findings,
            "immediate_actions": self.immediate_actions,
            "risk_level": self.risk_level,
            "trend_indicator": self.trend_indicator
        }


@dataclass
class KeyMetrics:
    """关键指标"""
    error_rate: float
    warning_rate: float
    avg_response_time: float
    error_chain_avg_length: float
    cross_system_call_count: int
    bottleneck_count: int
    circular_dependency_count: int
    anomaly_count: int
    health_score: float
    mttr_estimate: float

    def to_dict(self) -> Dict[str, Any]:
        return {
            "error_rate": round(self.error_rate, 4),
            "warning_rate": round(self.warning_rate, 4),
            "avg_response_time": round(self.avg_response_time, 2),
            "error_chain_avg_length": round(self.error_chain_avg_length, 2),
            "cross_system_call_count": self.cross_system_call_count,
            "bottleneck_count": self.bottleneck_count,
            "circular_dependency_count": self.circular_dependency_count,
            "anomaly_count": self.anomaly_count,
            "health_score": round(self.health_score, 2),
            "mttr_estimate_minutes": round(self.mttr_estimate, 2)
        }


@dataclass
class ChartData:
    """图表数据"""
    chart_id: str
    chart_type: str
    title: str
    data: Dict[str, Any]
    options: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "chart_id": self.chart_id,
            "chart_type": self.chart_type,
            "title": self.title,
            "data": self.data,
            "options": self.options
        }


@dataclass
class CorrelationReport:
    report_id: str
    generated_at: str
    sources: List[LogSource]
    total_events: int
    error_chains: List[ErrorPropagationChain]
    correlations: List[CorrelationResult]
    cross_system_traces: List[CrossSystemTrace]
    impact_assessments: List[ImpactAssessment]
    statistics: Dict[str, Any]
    recommendations: List[str]
    visualization_summary: Dict[str, Any] = field(default_factory=dict)
    time_series_analysis: List[TimeSeriesCorrelation] = field(default_factory=list)
    circular_dependencies: List[CircularDependency] = field(default_factory=list)
    root_cause_analyses: List[RootCauseAnalysis] = field(default_factory=list)
    trend_summary: Dict[str, Any] = field(default_factory=dict)
    anomaly_summary: Dict[str, Any] = field(default_factory=dict)
    source_health_statuses: List[SourceHealthStatus] = field(default_factory=list)
    source_dependencies: List[SourceDependency] = field(default_factory=list)
    error_patterns: List[ErrorPattern] = field(default_factory=list)
    chain_clusters: List[ChainCluster] = field(default_factory=list)
    executive_summary: Optional[ExecutiveSummary] = None
    key_metrics: Optional[KeyMetrics] = None
    chart_data: List[ChartData] = field(default_factory=list)
    detailed_statistics: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        result = {
            "report_id": self.report_id,
            "generated_at": self.generated_at,
            "sources": [s.to_dict() for s in self.sources],
            "total_events": self.total_events,
            "error_chains": [c.to_dict() for c in self.error_chains],
            "correlations": [c.to_dict() for c in self.correlations],
            "cross_system_traces": [t.to_dict() for t in self.cross_system_traces],
            "impact_assessments": [a.to_dict() for a in self.impact_assessments],
            "statistics": self.statistics,
            "recommendations": self.recommendations,
            "visualization_summary": self.visualization_summary,
            "time_series_analysis": [t.to_dict() for t in self.time_series_analysis],
            "circular_dependencies": [c.to_dict() for c in self.circular_dependencies],
            "root_cause_analyses": [r.to_dict() for r in self.root_cause_analyses],
            "trend_summary": self.trend_summary,
            "anomaly_summary": self.anomaly_summary,
            "source_health_statuses": [s.to_dict() for s in self.source_health_statuses],
            "source_dependencies": [d.to_dict() for d in self.source_dependencies],
            "error_patterns": [p.to_dict() for p in self.error_patterns],
            "chain_clusters": [c.to_dict() for c in self.chain_clusters],
            "detailed_statistics": self.detailed_statistics
        }
        if self.executive_summary:
            result["executive_summary"] = self.executive_summary.to_dict()
        if self.key_metrics:
            result["key_metrics"] = self.key_metrics.to_dict()
        if self.chart_data:
            result["chart_data"] = [c.to_dict() for c in self.chart_data]
        return result


class LogEventParser:
    """日志事件解析器"""

    TRACE_PATTERNS = [
        (r'trace[_-]?id[=:\s]*([a-zA-Z0-9-]+)', 'trace_id'),
        (r'span[_-]?id[=:\s]*([a-zA-Z0-9-]+)', 'span_id'),
        (r'parent[_-]?span[_-]?id[=:\s]*([a-zA-Z0-9-]+)', 'parent_span_id'),
        (r'correlation[_-]?id[=:\s]*([a-zA-Z0-9-]+)', 'correlation_id'),
        (r'request[_-]?id[=:\s]*([a-zA-Z0-9-]+)', 'request_id'),
        (r'session[_-]?id[=:\s]*([a-zA-Z0-9-]+)', 'session_id'),
        (r'user[_-]?id[=:\s]*([a-zA-Z0-9-]+)', 'user_id'),
        (r'thread[_-]?id[=:\s]*([a-zA-Z0-9-]+)', 'thread_id'),
    ]

    TIMESTAMP_PATTERNS = [
        r'(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?)',
        r'(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}(?:\.\d+)?)',
        r'(\d{2}/\d{2}/\d{4}\s+\d{2}:\d{2}:\d{2})',
    ]

    LEVEL_PATTERNS = [
        (r'\b(DEBUG|INFO|WARNING|WARN|ERROR|CRITICAL|FATAL)\b', 'level')
    ]

    ERROR_TYPE_PATTERNS = [
        r'(\w+Error|\w+Exception|\w+Fault)',
        r'Error:\s*(\w+)',
        r'Exception:\s*(\w+)',
    ]

    def __init__(self):
        self._compiled_trace_patterns = [
            (re.compile(p, re.IGNORECASE), name) for p, name in self.TRACE_PATTERNS
        ]
        self._compiled_ts_patterns = [
            re.compile(p) for p in self.TIMESTAMP_PATTERNS
        ]
        self._compiled_level_patterns = [
            (re.compile(p, re.IGNORECASE), name) for p, name in self.LEVEL_PATTERNS
        ]
        self._compiled_error_patterns = [
            re.compile(p, re.IGNORECASE) for p in self.ERROR_TYPE_PATTERNS
        ]

    def parse_line(self, line: str, source: LogSource, line_number: int) -> Optional[LogEvent]:
        if not line.strip():
            return None

        event_id = self._generate_event_id(line, source.source_id, line_number)
        timestamp = self._extract_timestamp(line)
        level = self._extract_level(line)
        trace_info = self._extract_trace_info(line)
        message = self._extract_message(line)
        error_type = self._extract_error_type(line)
        stack_trace = self._extract_stack_trace(line)

        return LogEvent(
            event_id=event_id,
            timestamp=timestamp or datetime.now(),
            level=level,
            message=message,
            source=source,
            trace_id=trace_info.get('trace_id', ''),
            span_id=trace_info.get('span_id', ''),
            parent_span_id=trace_info.get('parent_span_id', ''),
            correlation_id=trace_info.get('correlation_id', ''),
            thread_id=trace_info.get('thread_id', ''),
            request_id=trace_info.get('request_id', ''),
            session_id=trace_info.get('session_id', ''),
            user_id=trace_info.get('user_id', ''),
            raw_line=line,
            line_number=line_number,
            error_type=error_type,
            stack_trace=stack_trace
        )

    def parse_json_line(self, data: Dict[str, Any], source: LogSource, line_number: int) -> LogEvent:
        event_id = data.get('id', data.get('event_id', ''))
        if not event_id:
            event_id = self._generate_event_id(json.dumps(data), source.source_id, line_number)

        timestamp = self._parse_timestamp_value(data.get('timestamp', data.get('time', data.get('@timestamp'))))
        level = str(data.get('level', data.get('severity', 'info'))).upper()
        message = str(data.get('message', data.get('msg', '')))

        return LogEvent(
            event_id=event_id,
            timestamp=timestamp or datetime.now(),
            level=level,
            message=message,
            source=source,
            trace_id=str(data.get('trace_id', data.get('traceId', ''))),
            span_id=str(data.get('span_id', data.get('spanId', ''))),
            parent_span_id=str(data.get('parent_span_id', data.get('parentSpanId', ''))),
            correlation_id=str(data.get('correlation_id', data.get('correlationId', data.get('request_id', '')))),
            thread_id=str(data.get('thread_id', data.get('threadId', data.get('thread', '')))),
            logger_name=str(data.get('logger', data.get('logger_name', ''))),
            session_id=str(data.get('session_id', data.get('sessionId', ''))),
            user_id=str(data.get('user_id', data.get('userId', ''))),
            request_id=str(data.get('request_id', data.get('requestId', ''))),
            extra={k: v for k, v in data.items() if k not in ['timestamp', 'time', 'level', 'message', 'msg']},
            line_number=line_number,
            error_type=str(data.get('error_type', data.get('errorType', ''))),
            stack_trace=str(data.get('stack_trace', data.get('stackTrace', '')))
        )

    def _generate_event_id(self, line: str, source_id: str, line_number: int) -> str:
        content = f"{source_id}:{line_number}:{line[:100]}"
        return hashlib.md5(content.encode()).hexdigest()[:16]

    def _extract_timestamp(self, line: str) -> Optional[datetime]:
        for pattern in self._compiled_ts_patterns:
            match = pattern.search(line)
            if match:
                return self._parse_timestamp_value(match.group(1))
        return None

    def _parse_timestamp_value(self, ts_value: Any) -> Optional[datetime]:
        if not ts_value:
            return None

        if isinstance(ts_value, datetime):
            return ts_value

        ts_str = str(ts_value).replace('Z', '').replace('T', ' ')

        formats = [
            '%Y-%m-%d %H:%M:%S.%f',
            '%Y-%m-%d %H:%M:%S',
            '%Y/%m/%d %H:%M:%S',
            '%d/%m/%Y %H:%M:%S',
        ]

        for fmt in formats:
            try:
                return datetime.strptime(ts_str, fmt)
            except ValueError:
                continue

        return None

    def _extract_level(self, line: str) -> str:
        for pattern, _ in self._compiled_level_patterns:
            match = pattern.search(line)
            if match:
                level = match.group(1).upper()
                if level in ['WARN']:
                    return 'WARNING'
                if level in ['FATAL']:
                    return 'CRITICAL'
                return level
        return 'INFO'

    def _extract_trace_info(self, line: str) -> Dict[str, str]:
        info = {}
        for pattern, name in self._compiled_trace_patterns:
            match = pattern.search(line)
            if match:
                info[name] = match.group(1)
        return info

    def _extract_message(self, line: str) -> str:
        message = line
        for pattern in self._compiled_ts_patterns:
            message = pattern.sub('', message)
        for pattern, _ in self._compiled_level_patterns:
            message = pattern.sub('', message)
        for pattern, _ in self._compiled_trace_patterns:
            message = pattern.sub('', message)
        return message.strip()[:500]

    def _extract_error_type(self, line: str) -> str:
        for pattern in self._compiled_error_patterns:
            match = pattern.search(line)
            if match:
                return match.group(1)
        return ''

    def _extract_stack_trace(self, line: str) -> str:
        stack_trace_patterns = [
            r'(Traceback[\s\S]*?(?=\n\s*\n|\Z))',
            r'(at [\w\.]+\([^\)]*\)[\s\S]*?(?=\n\s*\n|\Z))',
            r'(Stack trace:[\s\S]*?(?=\n\s*\n|\Z))',
        ]
        for pattern in stack_trace_patterns:
            match = re.search(pattern, line, re.IGNORECASE)
            if match:
                return match.group(1)[:2000]
        return ''


class ErrorPropagationAnalyzer:
    """错误传播链分析器 - 增强版"""

    ERROR_LEVELS = {'ERROR', 'CRITICAL', 'FATAL', 'WARN', 'WARNING'}

    CAUSAL_PATTERNS = [
        (r'caused by[:\s]', 'caused_by'),
        (r'stack trace[:\s]', 'stack_trace'),
        (r'exception[:\s]', 'exception'),
        (r'error[:\s]', 'error'),
        (r'failed[:\s]', 'failed'),
        (r'because[:\s]', 'because'),
        (r'due to[:\s]', 'due_to'),
        (r'result of[:\s]', 'result_of'),
        (r'triggered by[:\s]', 'triggered_by'),
        (r'originating from[:\s]', 'originating_from'),
        (r'source[:\s]', 'source'),
        (r'upstream error[:\s]', 'upstream_error'),
        (r'downstream error[:\s]', 'downstream_error'),
        (r'propagated from[:\s]', 'propagated_from'),
    ]

    ROOT_CAUSE_INDICATORS = [
        r'initial error',
        r'original exception',
        r'root cause',
        r'first error',
        r'starting failure',
        r'primary error',
        r'source error',
        r'underlying cause',
    ]

    PROPAGATION_RULES = {
        'service_call': {
            'pattern': r'(calling|invoking|requesting)\s+service[:\s]*(\w+)',
            'weight': 0.8,
        },
        'database_query': {
            'pattern': r'(executing|running|querying)[:\s]*(SELECT|INSERT|UPDATE|DELETE)',
            'weight': 0.7,
        },
        'external_api': {
            'pattern': r'(calling|requesting)[:\s]*(api|endpoint|url)',
            'weight': 0.75,
        },
        'message_queue': {
            'pattern': r'(publishing|sending|consuming)[:\s]*(message|event|queue)',
            'weight': 0.65,
        },
    }

    def __init__(self, time_window_seconds: int = 300, config: Optional[Dict[str, Any]] = None):
        self.time_window = timedelta(seconds=time_window_seconds)
        self.config = config or {}
        self._compiled_patterns = [
            (re.compile(p, re.IGNORECASE), name) for p, name in self.CAUSAL_PATTERNS
        ]
        self._compiled_root_indicators = [
            re.compile(p, re.IGNORECASE) for p in self.ROOT_CAUSE_INDICATORS
        ]
        self._compiled_propagation_rules = {
            name: {'pattern': re.compile(info['pattern'], re.IGNORECASE), 'weight': info['weight']}
            for name, info in self.PROPAGATION_RULES.items()
        }
        self._propagation_graph: Dict[str, Set[str]] = defaultdict(set)
        self._error_frequency: Dict[str, int] = defaultdict(int)

    def analyze(self, events: List[LogEvent]) -> List[ErrorPropagationChain]:
        error_events = [e for e in events if e.level in self.ERROR_LEVELS]
        if not error_events:
            return []

        error_events.sort(key=lambda x: x.timestamp)

        chains = []
        processed_events: Set[str] = set()

        self._build_propagation_graph(error_events)

        for event in error_events:
            if event.event_id in processed_events:
                continue

            chain = self._build_chain(event, error_events, processed_events)
            if chain:
                chains.append(chain)

        enhanced_chains = self._enhance_chains_with_ml(chains, error_events)

        return sorted(enhanced_chains, key=lambda x: x.severity.value, reverse=True)

    def _build_propagation_graph(self, error_events: List[LogEvent]) -> None:
        self._propagation_graph.clear()
        
        for i, event1 in enumerate(error_events):
            for event2 in error_events[i+1:]:
                if self._has_propagation_link(event1, event2):
                    self._propagation_graph[event1.event_id].add(event2.event_id)

    def _has_propagation_link(self, event1: LogEvent, event2: LogEvent) -> bool:
        if event1.trace_id and event2.trace_id and event1.trace_id == event2.trace_id:
            return True
        
        if event1.correlation_id and event2.correlation_id and event1.correlation_id == event2.correlation_id:
            return True
        
        if event1.span_id and event2.parent_span_id and event1.span_id == event2.parent_span_id:
            return True
        
        time_diff = (event2.timestamp - event1.timestamp).total_seconds()
        if 0 < time_diff <= self.time_window.total_seconds():
            if self._has_causal_link(event1, event2):
                return True
            
            if self._has_service_call_link(event1, event2):
                return True
        
        return False

    def _has_service_call_link(self, event1: LogEvent, event2: LogEvent) -> bool:
        msg1_lower = event1.message.lower()
        msg2_lower = event2.message.lower()
        
        for rule_name, rule_info in self._compiled_propagation_rules.items():
            if rule_info['pattern'].search(msg1_lower):
                return True
        
        if 'response' in msg2_lower and 'request' in msg1_lower:
            return True
        
        if 'failed' in msg2_lower and any(kw in msg1_lower for kw in ['calling', 'requesting', 'invoking']):
            return True
        
        return False

    def _build_chain(
        self,
        root_event: LogEvent,
        all_errors: List[LogEvent],
        processed: Set[str]
    ) -> Optional[ErrorPropagationChain]:
        propagation_path = [root_event]
        processed.add(root_event.event_id)
        affected_systems = {root_event.source.system}

        current = root_event
        related_events = self._find_related_errors(root_event, all_errors, processed)

        for event in related_events:
            propagation_path.append(event)
            processed.add(event.event_id)
            affected_systems.add(event.source.system)
            current = event

        if len(propagation_path) < 2:
            return None

        duration = 0.0
        if len(propagation_path) >= 2:
            duration = (propagation_path[-1].timestamp - propagation_path[0].timestamp).total_seconds()

        severity = self._determine_severity(propagation_path)
        confidence = self._determine_confidence(propagation_path)
        impact = self._assess_impact(propagation_path, affected_systems)
        actions = self._suggest_actions(propagation_path, affected_systems)

        return ErrorPropagationChain(
            chain_id=f"EPC-{datetime.now().strftime('%Y%m%d%H%M%S')}-{hash(root_event.event_id) % 10000:04d}",
            root_cause=root_event,
            propagation_path=propagation_path,
            affected_systems=affected_systems,
            total_duration_seconds=duration,
            severity=severity,
            confidence=confidence,
            description=self._generate_description(propagation_path, affected_systems),
            impact_assessment=impact,
            suggested_actions=actions
        )

    def _enhance_chains_with_ml(
        self, 
        chains: List[ErrorPropagationChain], 
        all_events: List[LogEvent]
    ) -> List[ErrorPropagationChain]:
        for chain in chains:
            chain.impact_assessment['ml_score'] = self._calculate_ml_score(chain, all_events)
            
            chain.impact_assessment['propagation_speed'] = self._calculate_propagation_speed(chain)
            
            chain.impact_assessment['criticality_score'] = self._calculate_criticality(chain)
            
            if chain.impact_assessment['ml_score'] > 0.8:
                chain.suggested_actions.insert(0, "高优先级：立即调查根因并准备应急预案")
        
        return chains

    def _calculate_ml_score(self, chain: ErrorPropagationChain, all_events: List[LogEvent]) -> float:
        score = 0.0
        
        path_length = len(chain.propagation_path)
        score += min(0.3, path_length * 0.05)
        
        systems_count = len(chain.affected_systems)
        score += min(0.3, systems_count * 0.1)
        
        critical_count = sum(1 for e in chain.propagation_path if e.level in ['CRITICAL', 'FATAL'])
        score += min(0.2, critical_count * 0.1)
        
        if chain.total_duration_seconds > 0:
            speed_score = min(0.2, path_length / max(1, chain.total_duration_seconds) * 10)
            score += speed_score
        
        return min(1.0, score)

    def _calculate_propagation_speed(self, chain: ErrorPropagationChain) -> float:
        if chain.total_duration_seconds <= 0:
            return 0.0
        
        return len(chain.propagation_path) / chain.total_duration_seconds

    def _calculate_criticality(self, chain: ErrorPropagationChain) -> float:
        score = 0.0
        
        severity_weights = {'CRITICAL': 1.0, 'FATAL': 1.0, 'ERROR': 0.7, 'WARNING': 0.3, 'WARN': 0.3}
        
        for event in chain.propagation_path:
            score += severity_weights.get(event.level, 0.1)
        
        score /= len(chain.propagation_path)
        
        if len(chain.affected_systems) > 3:
            score *= 1.2
        
        return min(1.0, score)

    def _find_related_errors(
        self,
        root_event: LogEvent,
        all_errors: List[LogEvent],
        processed: Set[str]
    ) -> List[LogEvent]:
        related = []
        root_time = root_event.timestamp

        for event in all_errors:
            if event.event_id in processed:
                continue

            if event.timestamp < root_time:
                continue

            time_diff = event.timestamp - root_time
            if time_diff > self.time_window:
                continue

            if self._is_related(root_event, event):
                related.append(event)

        related.sort(key=lambda x: x.timestamp)
        return related

    def _is_related(self, event1: LogEvent, event2: LogEvent) -> bool:
        if event1.trace_id and event2.trace_id and event1.trace_id == event2.trace_id:
            return True

        if event1.correlation_id and event2.correlation_id and event1.correlation_id == event1.correlation_id:
            return True

        if event1.request_id and event2.request_id and event1.request_id == event2.request_id:
            return True

        if event1.session_id and event2.session_id and event1.session_id == event2.session_id:
            return True

        if self._has_causal_link(event1, event2):
            return True

        if self._has_similar_error_type(event1, event2):
            return True

        if event2.event_id in self._propagation_graph.get(event1.event_id, set()):
            return True

        return False

    def _has_causal_link(self, event1: LogEvent, event2: LogEvent) -> bool:
        msg_lower = event2.message.lower()
        for pattern, _ in self._compiled_patterns:
            if pattern.search(msg_lower):
                return True
        
        msg1_lower = event1.message.lower()
        for pattern, _ in self._compiled_patterns:
            if pattern.search(msg1_lower):
                if any(kw in msg_lower for kw in ['after', 'following', 'during']):
                    return True
        
        return False

    def _has_similar_error_type(self, event1: LogEvent, event2: LogEvent) -> bool:
        if event1.error_type and event2.error_type and event1.error_type == event2.error_type:
            return True
        return False

    def _determine_severity(self, path: List[LogEvent]) -> SeverityLevel:
        has_critical = any(e.level in ['CRITICAL', 'FATAL'] for e in path)
        if has_critical:
            return SeverityLevel.CRITICAL

        has_error = any(e.level == 'ERROR' for e in path)
        if has_error and len(path) >= 3:
            return SeverityLevel.HIGH

        if has_error:
            return SeverityLevel.MEDIUM

        return SeverityLevel.LOW

    def _determine_confidence(self, path: List[LogEvent]) -> CorrelationConfidence:
        trace_linked = any(e.trace_id for e in path)
        correlation_linked = any(e.correlation_id for e in path)
        span_linked = any(e.span_id and e.parent_span_id for e in path)
        causal_linked = any(self._has_causal_link(path[i], path[i+1]) for i in range(len(path)-1))

        if trace_linked or correlation_linked or span_linked:
            return CorrelationConfidence.HIGH
        elif causal_linked:
            return CorrelationConfidence.MEDIUM
        else:
            return CorrelationConfidence.LOW

    def _assess_impact(self, path: List[LogEvent], systems: Set[str]) -> Dict[str, Any]:
        error_count = sum(1 for e in path if e.level in ['ERROR', 'CRITICAL', 'FATAL'])
        warning_count = sum(1 for e in path if e.level in ['WARN', 'WARNING'])

        unique_users = len(set(e.user_id for e in path if e.user_id))
        unique_sessions = len(set(e.session_id for e in path if e.session_id))
        unique_requests = len(set(e.request_id for e in path if e.request_id))

        error_types = set(e.error_type for e in path if e.error_type)
        
        propagation_depth = len(path)
        affected_services = self._extract_affected_services(path)

        return {
            "error_count": error_count,
            "warning_count": warning_count,
            "affected_systems_count": len(systems),
            "unique_users_affected": unique_users,
            "unique_sessions_affected": unique_sessions,
            "unique_requests_affected": unique_requests,
            "propagation_depth": propagation_depth,
            "error_types": list(error_types),
            "affected_services": affected_services,
        }

    def _extract_affected_services(self, path: List[LogEvent]) -> List[str]:
        services = set()
        service_patterns = [
            r'service[:\s]*(\w+)',
            r'api[:\s]*(\w+)',
            r'endpoint[:\s]*(\w+)',
        ]
        
        for event in path:
            for pattern in service_patterns:
                matches = re.findall(pattern, event.message, re.IGNORECASE)
                services.update(matches)
        
        return list(services)[:10]

    def _suggest_actions(self, path: List[LogEvent], systems: Set[str]) -> List[str]:
        actions = []

        root = path[0]
        if root.error_type:
            actions.append(f"调查 {root.error_type} 类型的根因")

        if len(systems) > 1:
            actions.append("检查跨系统依赖关系和服务间通信")

        if any(e.level in ['CRITICAL', 'FATAL'] for e in path):
            actions.append("立即处理严重错误，考虑回滚最近的变更")

        if len(path) > 5:
            actions.append("分析错误传播路径，识别并修复级联故障点")

        affected_services = self._extract_affected_services(path)
        if affected_services:
            actions.append(f"检查服务健康状态: {', '.join(affected_services[:3])}")

        actions.append(f"检查 {root.source.system} 系统的健康状态")

        if self._has_database_related_errors(path):
            actions.append("检查数据库连接和查询性能")

        if self._has_network_related_errors(path):
            actions.append("检查网络连接和服务可用性")

        return actions

    def _has_database_related_errors(self, path: List[LogEvent]) -> bool:
        db_keywords = ['sql', 'database', 'query', 'connection pool', 'deadlock', 'transaction']
        for event in path:
            msg_lower = event.message.lower()
            if any(kw in msg_lower for kw in db_keywords):
                return True
        return False

    def _has_network_related_errors(self, path: List[LogEvent]) -> bool:
        network_keywords = ['timeout', 'connection', 'socket', 'network', 'dns', 'ssl']
        for event in path:
            msg_lower = event.message.lower()
            if any(kw in msg_lower for kw in network_keywords):
                return True
        return False

    def _generate_description(self, path: List[LogEvent], systems: Set[str]) -> str:
        root_msg = path[0].message[:80]
        systems_str = ', '.join(sorted(systems))
        return f"错误传播链: 从 '{root_msg}...' 开始，影响系统: {systems_str}"


class CrossSystemTracer:
    """跨系统追踪器 - 增强版"""

    def __init__(self, min_events: int = 2, config: Optional[Dict[str, Any]] = None):
        self.min_events = min_events
        self.config = config or {}
        self.slow_threshold_ms = self.config.get('slow_threshold_ms', 1000)

    def trace(self, events: List[LogEvent]) -> List[CrossSystemTrace]:
        traces_by_id: Dict[str, List[LogEvent]] = defaultdict(list)

        for event in events:
            if event.trace_id:
                traces_by_id[event.trace_id].append(event)
            elif event.correlation_id:
                traces_by_id[f"corr:{event.correlation_id}"].append(event)
            elif event.request_id:
                traces_by_id[f"req:{event.request_id}"].append(event)

        traces = []
        for trace_id, trace_events in traces_by_id.items():
            if len(trace_events) < self.min_events:
                continue

            trace = self._build_trace(trace_id, trace_events)
            if trace and len(trace.systems) >= 2:
                traces.append(trace)

        return sorted(traces, key=lambda x: x.total_duration_seconds, reverse=True)

    def _build_trace(self, trace_id: str, events: List[LogEvent]) -> Optional[CrossSystemTrace]:
        events.sort(key=lambda x: x.timestamp)

        systems = {e.source.system for e in events}
        entry_point = events[0] if events else None
        exit_point = events[-1] if events else None

        duration = 0.0
        if entry_point and exit_point:
            duration = (exit_point.timestamp - entry_point.timestamp).total_seconds()

        error_count = sum(1 for e in events if e.level in ['ERROR', 'CRITICAL', 'FATAL'])
        warning_count = sum(1 for e in events if e.level in ['WARN', 'WARNING'])

        service_calls = self._build_service_calls(events)
        bottleneck_service = self._detect_bottleneck(service_calls)

        return CrossSystemTrace(
            trace_id=trace_id,
            systems=systems,
            events=events,
            entry_point=entry_point,
            exit_point=exit_point,
            total_duration_seconds=duration,
            error_count=error_count,
            warning_count=warning_count,
            service_calls=service_calls,
            bottleneck_detected=bottleneck_service is not None,
            bottleneck_service=bottleneck_service
        )

    def _build_service_calls(self, events: List[LogEvent]) -> List[Dict[str, Any]]:
        calls = []
        current_system = None
        call_start = None

        for event in events:
            if current_system != event.source.system:
                if current_system and call_start:
                    calls.append({
                        "system": current_system,
                        "start_time": call_start.isoformat(),
                        "end_time": event.timestamp.isoformat(),
                        "duration_ms": (event.timestamp - call_start).total_seconds() * 1000
                    })
                current_system = event.source.system
                call_start = event.timestamp

        if current_system and call_start and events:
            last_event = events[-1]
            calls.append({
                "system": current_system,
                "start_time": call_start.isoformat(),
                "end_time": last_event.timestamp.isoformat(),
                "duration_ms": (last_event.timestamp - call_start).total_seconds() * 1000
            })

        return calls

    def _detect_bottleneck(self, service_calls: List[Dict[str, Any]]) -> Optional[str]:
        if not service_calls:
            return None

        for call in service_calls:
            if call.get("duration_ms", 0) > self.slow_threshold_ms:
                return call.get("system")

        return None


class MultiSourceCorrelator:
    """多源日志关联器 - 增强版"""

    CORRELATION_STRATEGIES = {
        'temporal': {'weight': 0.25, 'window_seconds': 60},
        'semantic': {'weight': 0.20, 'similarity_threshold': 0.7},
        'structural': {'weight': 0.20, 'min_common_fields': 2},
        'causal': {'weight': 0.25, 'confidence_threshold': 0.6},
        'behavioral': {'weight': 0.10, 'pattern_threshold': 0.5},
    }

    SEMANTIC_SIMILARITY_PATTERNS = [
        (r'error|exception|failed', 'error_indicator'),
        (r'warning|warn|caution', 'warning_indicator'),
        (r'timeout|timed out|deadline', 'timeout_indicator'),
        (r'connection|connect|socket', 'connection_indicator'),
        (r'memory|heap|allocation', 'memory_indicator'),
        (r'database|sql|query', 'database_indicator'),
        (r'authentication|auth|login', 'auth_indicator'),
        (r'request|response|api', 'api_indicator'),
    ]

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.temporal_window = self.config.get('temporal_window_seconds', 60)
        self.min_correlation_score = self.config.get('min_correlation_score', 0.5)
        self._compiled_semantic_patterns = [
            (re.compile(p, re.IGNORECASE), name) for p, name in self.SEMANTIC_SIMILARITY_PATTERNS
        ]
        self._correlation_cache: Dict[str, float] = {}
        self._event_embeddings: Dict[str, List[float]] = {}

    def correlate(self, events: List[LogEvent]) -> List[CorrelationResult]:
        correlations = []

        correlations.extend(self._find_temporal_correlations(events))
        correlations.extend(self._find_pattern_correlations(events))
        correlations.extend(self._find_dependency_correlations(events))
        correlations.extend(self._find_resource_contention(events))
        correlations.extend(self._find_sequence_correlations(events))
        correlations.extend(self._find_semantic_correlations(events))
        correlations.extend(self._find_cross_source_correlations(events))
        correlations.extend(self._find_causal_correlations(events))

        merged_correlations = self._merge_overlapping_correlations(correlations)

        return [c for c in merged_correlations if c.confidence_score >= self.min_correlation_score]

    def _find_semantic_correlations(self, events: List[LogEvent]) -> List[CorrelationResult]:
        correlations = []
        
        semantic_groups: Dict[str, List[LogEvent]] = defaultdict(list)
        
        for event in events:
            semantic_signature = self._extract_semantic_signature(event.message)
            semantic_groups[semantic_signature].append(event)
        
        for signature, group_events in semantic_groups.items():
            if len(group_events) >= 3:
                sources = set(e.source.source_id for e in group_events)
                if len(sources) >= 2:
                    sorted_events = sorted(group_events, key=lambda x: x.timestamp)
                    time_span = (sorted_events[-1].timestamp - sorted_events[0].timestamp).total_seconds()
                    
                    correlations.append(CorrelationResult(
                        correlation_id=f"SEM-{datetime.now().strftime('%Y%m%d%H%M%S')}-{hash(signature) % 10000:04d}",
                        correlation_type=CorrelationType.PATTERN_MATCH,
                        events=sorted_events[:20],
                        confidence_score=0.8,
                        time_span_seconds=time_span,
                        description=f"语义相似事件 (出现 {len(group_events)} 次): {signature[:60]}...",
                        metadata={
                            "semantic_signature": signature,
                            "sources": list(sources),
                            "total_count": len(group_events),
                        },
                        visualization_data={
                            "source_distribution": {s: sum(1 for e in group_events if e.source.source_id == s) for s in sources}
                        }
                    ))
        
        return correlations

    def _extract_semantic_signature(self, message: str) -> str:
        signature = message.lower()
        signature = re.sub(r'\d+', '#', signature)
        signature = re.sub(r'0x[a-fA-F0-9]+', '#HEX#', signature)
        signature = re.sub(r'[a-fA-F0-9]{8}-[a-fA-F0-9]{4}-[a-fA-F0-9]{4}-[a-fA-F0-9]{4}-[a-fA-F0-9]{12}', '#UUID#', signature)
        signature = re.sub(r'https?://[^\s]+', '#URL#', signature)
        signature = re.sub(r'/[\w/\.]+', '#PATH#', signature)
        signature = re.sub(r'\s+', ' ', signature).strip()
        return signature[:100]

    def _find_cross_source_correlations(self, events: List[LogEvent]) -> List[CorrelationResult]:
        correlations = []
        
        events_by_source: Dict[str, List[LogEvent]] = defaultdict(list)
        for event in events:
            events_by_source[event.source.source_id].append(event)
        
        if len(events_by_source) < 2:
            return correlations
        
        source_ids = list(events_by_source.keys())
        
        for i, source1 in enumerate(source_ids):
            for source2 in source_ids[i+1:]:
                cross_correlations = self._find_cross_source_pair_correlations(
                    events_by_source[source1],
                    events_by_source[source2]
                )
                correlations.extend(cross_correlations)
        
        return correlations

    def _find_cross_source_pair_correlations(
        self, 
        events1: List[LogEvent], 
        events2: List[LogEvent]
    ) -> List[CorrelationResult]:
        correlations = []
        
        error_events1 = [e for e in events1 if e.level in ['ERROR', 'CRITICAL', 'FATAL']]
        error_events2 = [e for e in events2 if e.level in ['ERROR', 'CRITICAL', 'FATAL']]
        
        time_window = timedelta(seconds=self.temporal_window)
        
        for e1 in error_events1:
            related_events = [e1]
            
            for e2 in error_events2:
                time_diff = abs((e2.timestamp - e1.timestamp).total_seconds())
                if time_diff <= time_window.total_seconds():
                    related_events.append(e2)
            
            if len(related_events) >= 2:
                sorted_events = sorted(related_events, key=lambda x: x.timestamp)
                time_span = (sorted_events[-1].timestamp - sorted_events[0].timestamp).total_seconds()
                
                correlations.append(CorrelationResult(
                    correlation_id=f"CROSS-{datetime.now().strftime('%Y%m%d%H%M%S')}-{hash(e1.event_id) % 10000:04d}",
                    correlation_type=CorrelationType.CROSS_SYSTEM,
                    events=sorted_events,
                    confidence_score=0.75,
                    time_span_seconds=time_span,
                    description=f"跨源错误关联: {e1.source.system} <-> {e2.source.system}",
                    metadata={
                        "sources": [e1.source.source_id, e2.source.source_id],
                        "systems": [e1.source.system, e2.source.system],
                    }
                ))
        
        return correlations[:20]

    def _find_causal_correlations(self, events: List[LogEvent]) -> List[CorrelationResult]:
        correlations = []
        
        causal_keywords = ['caused', 'because', 'due to', 'result of', 'triggered', 'following']
        
        for event in events:
            if event.level not in ['ERROR', 'CRITICAL', 'FATAL']:
                continue
            
            msg_lower = event.message.lower()
            has_causal = any(kw in msg_lower for kw in causal_keywords)
            
            if has_causal:
                related = self._find_causally_related_events(event, events)
                if len(related) >= 2:
                    sorted_events = sorted(related, key=lambda x: x.timestamp)
                    time_span = (sorted_events[-1].timestamp - sorted_events[0].timestamp).total_seconds()
                    
                    correlations.append(CorrelationResult(
                        correlation_id=f"CAUSAL-{datetime.now().strftime('%Y%m%d%H%M%S')}-{hash(event.event_id) % 10000:04d}",
                        correlation_type=CorrelationType.CAUSAL,
                        events=sorted_events,
                        confidence_score=0.85,
                        time_span_seconds=time_span,
                        description=f"因果关联: {event.message[:60]}...",
                        metadata={
                            "root_event": event.event_id,
                            "causal_keywords": [kw for kw in causal_keywords if kw in msg_lower],
                        }
                    ))
        
        return correlations

    def _find_causally_related_events(self, event: LogEvent, all_events: List[LogEvent]) -> List[LogEvent]:
        related = [event]
        
        time_window = timedelta(seconds=self.temporal_window * 2)
        
        for other in all_events:
            if other.event_id == event.event_id:
                continue
            
            time_diff = (other.timestamp - event.timestamp).total_seconds()
            if 0 < time_diff <= time_window.total_seconds():
                if self._has_causal_relationship(event, other):
                    related.append(other)
        
        return related

    def _has_causal_relationship(self, event1: LogEvent, event2: LogEvent) -> bool:
        if event1.trace_id and event2.trace_id and event1.trace_id == event2.trace_id:
            return True
        
        if event1.correlation_id and event2.correlation_id and event1.correlation_id == event2.correlation_id:
            return True
        
        msg1_lower = event1.message.lower()
        msg2_lower = event2.message.lower()
        
        if 'failed' in msg2_lower and any(kw in msg1_lower for kw in ['calling', 'requesting', 'connecting']):
            return True
        
        if 'error' in msg2_lower and 'response' in msg2_lower and 'request' in msg1_lower:
            return True
        
        return False

    def _merge_overlapping_correlations(self, correlations: List[CorrelationResult]) -> List[CorrelationResult]:
        if not correlations:
            return []
        
        merged = []
        used_ids: Set[str] = set()
        
        for corr in correlations:
            if corr.correlation_id in used_ids:
                continue
            
            event_ids = set(e.event_id for e in corr.events)
            
            overlapping = []
            for other in correlations:
                if other.correlation_id == corr.correlation_id or other.correlation_id in used_ids:
                    continue
                
                other_event_ids = set(e.event_id for e in other.events)
                overlap = len(event_ids & other_event_ids)
                
                if overlap >= min(len(event_ids), len(other_event_ids)) * 0.5:
                    overlapping.append(other)
            
            if overlapping:
                merged_corr = self._merge_correlations([corr] + overlapping)
                merged.append(merged_corr)
                used_ids.add(corr.correlation_id)
                for o in overlapping:
                    used_ids.add(o.correlation_id)
            else:
                merged.append(corr)
                used_ids.add(corr.correlation_id)
        
        return merged

    def _merge_correlations(self, correlations: List[CorrelationResult]) -> CorrelationResult:
        all_events = []
        for c in correlations:
            all_events.extend(c.events)
        
        unique_events = list({e.event_id: e for e in all_events}.values())
        sorted_events = sorted(unique_events, key=lambda x: x.timestamp)
        
        time_span = (sorted_events[-1].timestamp - sorted_events[0].timestamp).total_seconds() if sorted_events else 0
        
        avg_confidence = sum(c.confidence_score for c in correlations) / len(correlations)
        
        types = set(c.correlation_type for c in correlations)
        primary_type = max(types, key=lambda t: sum(1 for c in correlations if c.correlation_type == t))
        
        return CorrelationResult(
            correlation_id=f"MERGED-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            correlation_type=primary_type,
            events=sorted_events,
            confidence_score=min(0.95, avg_confidence * 1.1),
            time_span_seconds=time_span,
            description=f"合并关联: {len(correlations)} 个关联模式",
            metadata={
                "merged_types": [t.value for t in types],
                "original_count": len(correlations),
            }
        )

    def _find_temporal_correlations(self, events: List[LogEvent]) -> List[CorrelationResult]:
        correlations = []
        time_window = timedelta(seconds=self.temporal_window)

        error_events = [e for e in events if e.level in ['ERROR', 'CRITICAL', 'FATAL']]
        error_events.sort(key=lambda x: x.timestamp)

        for i, event1 in enumerate(error_events):
            related = [event1]
            for event2 in error_events[i + 1:]:
                if event2.timestamp - event1.timestamp <= time_window:
                    related.append(event2)
                else:
                    break

            if len(related) >= 3:
                time_span = (related[-1].timestamp - related[0].timestamp).total_seconds()
                systems = list(set(e.source.system for e in related))

                correlations.append(CorrelationResult(
                    correlation_id=f"TEMP-{datetime.now().strftime('%Y%m%d%H%M%S')}-{i:04d}",
                    correlation_type=CorrelationType.TEMPORAL,
                    events=related,
                    confidence_score=0.7,
                    time_span_seconds=time_span,
                    description=f"时间窗口内的错误聚集 ({len(related)} 个事件)",
                    metadata={"systems": systems},
                    visualization_data={
                        "timeline": [(e.timestamp.isoformat(), e.source.system, e.level) for e in related]
                    }
                ))

        return correlations[:50]

    def _find_pattern_correlations(self, events: List[LogEvent]) -> List[CorrelationResult]:
        correlations = []
        pattern_counts: Dict[str, List[LogEvent]] = defaultdict(list)

        for event in events:
            normalized = self._normalize_message(event.message)
            pattern_counts[normalized].append(event)

        for pattern, pattern_events in pattern_counts.items():
            if len(pattern_events) >= 5:
                time_span = 0.0
                if len(pattern_events) >= 2:
                    sorted_events = sorted(pattern_events, key=lambda x: x.timestamp)
                    time_span = (sorted_events[-1].timestamp - sorted_events[0].timestamp).total_seconds()

                correlations.append(CorrelationResult(
                    correlation_id=f"PATTERN-{datetime.now().strftime('%Y%m%d%H%M%S')}-{hash(pattern) % 10000:04d}",
                    correlation_type=CorrelationType.RECURRING,
                    events=pattern_events[:20],
                    confidence_score=0.8,
                    time_span_seconds=time_span,
                    description=f"重复模式 (出现 {len(pattern_events)} 次): {pattern[:60]}...",
                    metadata={"pattern": pattern, "total_count": len(pattern_events)},
                    visualization_data={
                        "occurrence_distribution": self._calculate_hourly_distribution(pattern_events)
                    }
                ))

        return sorted(correlations, key=lambda x: x.metadata.get('total_count', 0), reverse=True)[:20]

    def _find_dependency_correlations(self, events: List[LogEvent]) -> List[CorrelationResult]:
        correlations = []
        dependency_keywords = ['dependency', 'service', 'api', 'call', 'request', 'response', 'upstream', 'downstream']

        dep_events: Dict[str, List[LogEvent]] = defaultdict(list)
        for event in events:
            message_lower = event.message.lower()
            for keyword in dependency_keywords:
                if keyword in message_lower:
                    dep_events[keyword].append(event)
                    break

        for dep_type, dep_type_events in dep_events.items():
            if len(dep_type_events) >= 3:
                sorted_events = sorted(dep_type_events, key=lambda x: x.timestamp)
                time_span = (sorted_events[-1].timestamp - sorted_events[0].timestamp).total_seconds()

                correlations.append(CorrelationResult(
                    correlation_id=f"DEP-{datetime.now().strftime('%Y%m%d%H%M%S')}-{hash(dep_type) % 10000:04d}",
                    correlation_type=CorrelationType.DEPENDENCY,
                    events=sorted_events[:20],
                    confidence_score=0.75,
                    time_span_seconds=time_span,
                    description=f"依赖相关事件 ({dep_type}): {len(dep_type_events)} 个事件",
                    metadata={"dependency_type": dep_type, "count": len(dep_type_events)}
                ))

        return correlations

    def _find_resource_contention(self, events: List[LogEvent]) -> List[CorrelationResult]:
        correlations = []
        resource_keywords = ['lock', 'deadlock', 'mutex', 'semaphore', 'pool', 'connection', 'thread', 'timeout']

        resource_events: Dict[str, List[LogEvent]] = defaultdict(list)
        for event in events:
            message_lower = event.message.lower()
            for keyword in resource_keywords:
                if keyword in message_lower:
                    resource_events[keyword].append(event)
                    break

        for resource, res_events in resource_events.items():
            if len(res_events) >= 2:
                sorted_events = sorted(res_events, key=lambda x: x.timestamp)
                time_span = (sorted_events[-1].timestamp - sorted_events[0].timestamp).total_seconds()

                correlations.append(CorrelationResult(
                    correlation_id=f"RES-{datetime.now().strftime('%Y%m%d%H%M%S')}-{hash(resource) % 10000:04d}",
                    correlation_type=CorrelationType.RESOURCE_CONTENTION,
                    events=sorted_events[:20],
                    confidence_score=0.85,
                    time_span_seconds=time_span,
                    description=f"资源竞争/等待 ({resource}): {len(res_events)} 个事件",
                    metadata={"resource": resource, "count": len(res_events)}
                ))

        return correlations

    def _find_sequence_correlations(self, events: List[LogEvent]) -> List[CorrelationResult]:
        correlations = []
        sequence_patterns = [
            (['INFO', 'WARNING', 'ERROR'], 'escalating_severity'),
            (['request', 'process', 'response'], 'request_flow'),
            (['connect', 'auth', 'query', 'disconnect'], 'db_session'),
        ]

        for pattern, pattern_name in sequence_patterns:
            matching_sequences = self._find_sequences(events, pattern)
            for seq_events in matching_sequences:
                if len(seq_events) >= 2:
                    time_span = (seq_events[-1].timestamp - seq_events[0].timestamp).total_seconds()
                    correlations.append(CorrelationResult(
                        correlation_id=f"SEQ-{datetime.now().strftime('%Y%m%d%H%M%S')}-{hash(pattern_name) % 10000:04d}",
                        correlation_type=CorrelationType.SEQUENCE,
                        events=seq_events,
                        confidence_score=0.8,
                        time_span_seconds=time_span,
                        description=f"序列模式 ({pattern_name}): {len(seq_events)} 个事件",
                        metadata={"pattern_name": pattern_name}
                    ))

        return correlations[:20]

    def _find_sequences(self, events: List[LogEvent], pattern: List[str]) -> List[List[LogEvent]]:
        sequences = []
        current_sequence = []
        pattern_idx = 0

        sorted_events = sorted(events, key=lambda x: x.timestamp)

        for event in sorted_events:
            target = pattern[pattern_idx].lower()
            if target in event.level.lower() or target in event.message.lower():
                current_sequence.append(event)
                pattern_idx = (pattern_idx + 1) % len(pattern)

                if pattern_idx == 0 and len(current_sequence) >= len(pattern):
                    sequences.append(current_sequence.copy())
                    current_sequence = []
            else:
                if current_sequence:
                    if len(current_sequence) >= 2:
                        sequences.append(current_sequence.copy())
                    current_sequence = []
                    pattern_idx = 0

        return sequences

    def _normalize_message(self, message: str) -> str:
        normalized = re.sub(r'\d+', 'N', message)
        normalized = re.sub(r'0x[a-fA-F0-9]+', 'HEX', normalized)
        normalized = re.sub(r'[a-fA-F0-9]{8}-[a-fA-F0-9]{4}-[a-fA-F0-9]{4}-[a-fA-F0-9]{4}-[a-fA-F0-9]{12}', 'UUID', normalized)
        normalized = re.sub(r'\s+', ' ', normalized).strip()
        return normalized[:100]

    def _calculate_hourly_distribution(self, events: List[LogEvent]) -> Dict[str, int]:
        distribution: Dict[str, int] = defaultdict(int)
        for event in events:
            hour_key = event.timestamp.strftime('%Y-%m-%d %H')
            distribution[hour_key] += 1
        return dict(distribution)


class ImpactAnalyzer:
    """影响范围分析器"""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}

    def analyze(
        self,
        error_chains: List[ErrorPropagationChain],
        cross_system_traces: List[CrossSystemTrace],
        events: List[LogEvent]
    ) -> List[ImpactAssessment]:
        assessments = []

        for chain in error_chains:
            if chain.severity in [SeverityLevel.HIGH, SeverityLevel.CRITICAL]:
                assessment = self._assess_chain_impact(chain, events)
                assessments.append(assessment)

        for trace in cross_system_traces:
            if trace.error_count > 0:
                assessment = self._assess_trace_impact(trace, events)
                assessments.append(assessment)

        return assessments

    def _assess_chain_impact(self, chain: ErrorPropagationChain, events: List[LogEvent]) -> ImpactAssessment:
        affected_systems = list(chain.affected_systems)

        affected_users = chain.impact_assessment.get('unique_users_affected', 0)
        affected_requests = chain.impact_assessment.get('unique_requests_affected', 0)

        severity_dist = {
            'critical': sum(1 for e in chain.propagation_path if e.level in ['CRITICAL', 'FATAL']),
            'error': sum(1 for e in chain.propagation_path if e.level == 'ERROR'),
            'warning': sum(1 for e in chain.propagation_path if e.level in ['WARN', 'WARNING']),
        }

        downtime = chain.total_duration_seconds / 60

        business_impact = self._determine_business_impact(chain.severity, affected_systems, affected_users)

        suggestions = self._generate_recovery_suggestions(chain)

        return ImpactAssessment(
            assessment_id=f"IMPACT-{datetime.now().strftime('%Y%m%d%H%M%S')}-{hash(chain.chain_id) % 10000:04d}",
            affected_systems=affected_systems,
            affected_users=affected_users,
            affected_requests=affected_requests,
            severity_distribution=severity_dist,
            estimated_downtime_minutes=downtime,
            business_impact=business_impact,
            recovery_suggestions=suggestions
        )

    def _assess_trace_impact(self, trace: CrossSystemTrace, events: List[LogEvent]) -> ImpactAssessment:
        affected_systems = list(trace.systems)

        trace_events = trace.events
        affected_users = len(set(e.user_id for e in trace_events if e.user_id))
        affected_requests = len(set(e.request_id for e in trace_events if e.request_id))

        severity_dist = {
            'critical': trace_events.count(lambda e: e.level in ['CRITICAL', 'FATAL']),
            'error': trace.error_count,
            'warning': trace.warning_count,
        }

        downtime = trace.total_duration_seconds / 60

        business_impact = "中等" if trace.error_count > 5 else "低"

        suggestions = [
            f"检查 {trace.bottleneck_service} 服务的性能" if trace.bottleneck_service else "分析服务调用链",
            "优化跨系统调用的超时配置",
            "考虑实现熔断机制"
        ]

        return ImpactAssessment(
            assessment_id=f"IMPACT-TRACE-{datetime.now().strftime('%Y%m%d%H%M%S')}-{hash(trace.trace_id) % 10000:04d}",
            affected_systems=affected_systems,
            affected_users=affected_users,
            affected_requests=affected_requests,
            severity_distribution=severity_dist,
            estimated_downtime_minutes=downtime,
            business_impact=business_impact,
            recovery_suggestions=suggestions
        )

    def _determine_business_impact(
        self,
        severity: SeverityLevel,
        systems: List[str],
        users: int
    ) -> str:
        if severity == SeverityLevel.CRITICAL:
            if len(systems) > 3 or users > 100:
                return "严重 - 核心业务受影响"
            return "高 - 重要功能受影响"
        elif severity == SeverityLevel.HIGH:
            if len(systems) > 2:
                return "高 - 多系统受影响"
            return "中等 - 部分功能受影响"
        else:
            return "低 - 影响有限"

    def _generate_recovery_suggestions(self, chain: ErrorPropagationChain) -> List[str]:
        suggestions = list(chain.suggested_actions)
        suggestions.extend([
            "通知相关团队进行问题排查",
            "准备回滚计划（如适用）",
            "加强监控和告警"
        ])
        return suggestions[:5]


class TimeSeriesAnalyzer:
    """时间序列关联分析器 - 分析日志事件的时间序列模式"""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.window_size_minutes = self.config.get('window_size_minutes', 5)
        self.anomaly_threshold = self.config.get('anomaly_threshold', 2.0)
        self.min_points = self.config.get('min_points', 10)

    def analyze(self, events: List[LogEvent]) -> List[TimeSeriesCorrelation]:
        if len(events) < self.min_points:
            return []

        time_series_list = []

        overall_series = self._build_overall_series(events)
        if overall_series:
            time_series_list.append(overall_series)

        system_series = self._build_system_series(events)
        time_series_list.extend(system_series)

        error_series = self._build_error_rate_series(events)
        if error_series:
            time_series_list.append(error_series)

        return [ts for ts in time_series_list if ts is not None]

    def _build_overall_series(self, events: List[LogEvent]) -> Optional[TimeSeriesCorrelation]:
        if not events:
            return None

        events.sort(key=lambda x: x.timestamp)
        
        window = timedelta(minutes=self.window_size_minutes)
        points = []
        
        start_time = events[0].timestamp
        end_time = events[-1].timestamp
        current_time = start_time
        
        while current_time <= end_time:
            window_end = current_time + window
            window_events = [e for e in events if current_time <= e.timestamp < window_end]
            
            if window_events:
                error_count = sum(1 for e in window_events if e.level in ['ERROR', 'CRITICAL', 'FATAL'])
                warning_count = sum(1 for e in window_events if e.level in ['WARN', 'WARNING'])
                
                points.append(TimeSeriesPoint(
                    timestamp=current_time,
                    value=len(window_events),
                    event_count=len(window_events),
                    error_count=error_count,
                    warning_count=warning_count,
                    metadata={"window_start": current_time.isoformat()}
                ))
            
            current_time = window_end

        if len(points) < self.min_points:
            return None

        trend, slope, r_squared = self._calculate_trend(points)
        anomalies = self._detect_anomalies(points)
        seasonality = self._detect_seasonality(points)
        forecast = self._generate_forecast(points)

        return TimeSeriesCorrelation(
            correlation_id=f"TS-OVERALL-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            series_name="整体事件频率",
            points=points,
            trend=trend,
            slope=slope,
            r_squared=r_squared,
            anomalies=anomalies,
            seasonality_detected=seasonality,
            forecast=forecast
        )

    def _build_system_series(self, events: List[LogEvent]) -> List[TimeSeriesCorrelation]:
        events_by_system: Dict[str, List[LogEvent]] = defaultdict(list)
        for event in events:
            events_by_system[event.source.system].append(event)

        series_list = []
        for system, system_events in events_by_system.items():
            if len(system_events) < self.min_points:
                continue

            series = self._build_series_for_events(system_events, f"系统: {system}")
            if series:
                series_list.append(series)

        return series_list[:10]

    def _build_error_rate_series(self, events: List[LogEvent]) -> Optional[TimeSeriesCorrelation]:
        error_events = [e for e in events if e.level in ['ERROR', 'CRITICAL', 'FATAL', 'WARN', 'WARNING']]
        
        if len(error_events) < self.min_points:
            return None

        return self._build_series_for_events(error_events, "错误/警告事件频率")

    def _build_series_for_events(self, events: List[LogEvent], name: str) -> Optional[TimeSeriesCorrelation]:
        if not events:
            return None

        events.sort(key=lambda x: x.timestamp)
        
        window = timedelta(minutes=self.window_size_minutes)
        points = []
        
        start_time = events[0].timestamp
        end_time = events[-1].timestamp
        current_time = start_time
        
        while current_time <= end_time:
            window_end = current_time + window
            window_events = [e for e in events if current_time <= e.timestamp < window_end]
            
            if window_events:
                error_count = sum(1 for e in window_events if e.level in ['ERROR', 'CRITICAL', 'FATAL'])
                warning_count = sum(1 for e in window_events if e.level in ['WARN', 'WARNING'])
                
                points.append(TimeSeriesPoint(
                    timestamp=current_time,
                    value=len(window_events),
                    event_count=len(window_events),
                    error_count=error_count,
                    warning_count=warning_count
                ))
            
            current_time = window_end

        if len(points) < self.min_points:
            return None

        trend, slope, r_squared = self._calculate_trend(points)
        anomalies = self._detect_anomalies(points)

        return TimeSeriesCorrelation(
            correlation_id=f"TS-{hash(name) % 10000:04d}-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            series_name=name,
            points=points,
            trend=trend,
            slope=slope,
            r_squared=r_squared,
            anomalies=anomalies,
            seasonality_detected=self._detect_seasonality(points)
        )

    def _calculate_trend(self, points: List[TimeSeriesPoint]) -> Tuple[str, float, float]:
        if len(points) < 2:
            return "稳定", 0.0, 0.0

        n = len(points)
        x = list(range(n))
        y = [p.value for p in points]
        
        x_mean = sum(x) / n
        y_mean = sum(y) / n
        
        numerator = sum((x[i] - x_mean) * (y[i] - y_mean) for i in range(n))
        denominator = sum((x[i] - x_mean) ** 2 for i in range(n))
        
        if denominator == 0:
            return "稳定", 0.0, 0.0
        
        slope = numerator / denominator
        intercept = y_mean - slope * x_mean
        
        y_pred = [slope * xi + intercept for xi in x]
        ss_res = sum((y[i] - y_pred[i]) ** 2 for i in range(n))
        ss_tot = sum((y[i] - y_mean) ** 2 for i in range(n))
        
        r_squared = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0.0

        if slope > 0.5:
            trend = "上升"
        elif slope < -0.5:
            trend = "下降"
        else:
            trend = "稳定"

        return trend, slope, r_squared

    def _detect_anomalies(self, points: List[TimeSeriesPoint]) -> List[Dict[str, Any]]:
        if len(points) < 3:
            return []

        values = [p.value for p in points]
        mean = sum(values) / len(values)
        
        variance = sum((v - mean) ** 2 for v in values) / len(values)
        std_dev = variance ** 0.5
        
        if std_dev == 0:
            return []

        anomalies = []
        for i, point in enumerate(points):
            z_score = abs(point.value - mean) / std_dev
            if z_score > self.anomaly_threshold:
                anomalies.append({
                    "timestamp": point.timestamp.isoformat(),
                    "value": point.value,
                    "expected": mean,
                    "z_score": z_score,
                    "type": "高值" if point.value > mean else "低值",
                    "index": i
                })

        return anomalies

    def _detect_seasonality(self, points: List[TimeSeriesPoint]) -> bool:
        if len(points) < 24:
            return False

        values = [p.value for p in points]
        
        autocorr = self._autocorrelation(values, 1)
        
        return abs(autocorr) > 0.5

    def _autocorrelation(self, values: List[float], lag: int) -> float:
        n = len(values)
        if n <= lag:
            return 0.0

        mean = sum(values) / n
        variance = sum((v - mean) ** 2 for v in values) / n
        
        if variance == 0:
            return 0.0

        autocorr = sum((values[i] - mean) * (values[i - lag] - mean) for i in range(lag, n)) / (n * variance)
        return autocorr

    def _generate_forecast(self, points: List[TimeSeriesPoint]) -> List[Dict[str, Any]]:
        if len(points) < 5:
            return []

        values = [p.value for p in points]
        n = len(values)
        
        alpha = 0.3
        smoothed = [values[0]]
        
        for i in range(1, n):
            smoothed.append(alpha * values[i] + (1 - alpha) * smoothed[-1])

        forecast = []
        last_smoothed = smoothed[-1]
        last_timestamp = points[-1].timestamp
        window = timedelta(minutes=self.window_size_minutes)
        
        for i in range(1, 6):
            forecast.append({
                "timestamp": (last_timestamp + i * window).isoformat(),
                "predicted_value": round(last_smoothed, 2),
                "confidence": max(0.5, 1 - i * 0.1)
            })

        return forecast


class CircularDependencyDetector:
    """循环依赖检测器 - 检测服务间的循环依赖关系"""

    SERVICE_CALL_PATTERNS = [
        (r'calling\s+service[:\s]*(\w+)', 'caller'),
        (r'invoking\s+service[:\s]*(\w+)', 'caller'),
        (r'requesting\s+from[:\s]*(\w+)', 'caller'),
        (r'depends\s+on[:\s]*(\w+)', 'dependency'),
        (r'waiting\s+for[:\s]*(\w+)', 'dependency'),
    ]

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self._compiled_patterns = [
            (re.compile(p, re.IGNORECASE), t) for p, t in self.SERVICE_CALL_PATTERNS
        ]
        self._dependency_graph: Dict[str, Set[str]] = defaultdict(set)
        self._event_map: Dict[str, List[LogEvent]] = defaultdict(list)

    def detect(self, events: List[LogEvent]) -> List[CircularDependency]:
        self._build_dependency_graph(events)
        
        cycles = self._find_all_cycles()
        
        circular_deps = []
        for cycle in cycles:
            circular_dep = self._create_circular_dependency(cycle, events)
            if circular_dep:
                circular_deps.append(circular_dep)

        return sorted(circular_deps, key=lambda x: x.cycle_length)

    def _build_dependency_graph(self, events: List[LogEvent]) -> None:
        self._dependency_graph.clear()
        self._event_map.clear()

        for event in events:
            source_service = event.source.system
            self._event_map[source_service].append(event)
            
            for pattern, _ in self._compiled_patterns:
                matches = pattern.findall(event.message)
                for target_service in matches:
                    if target_service.lower() != source_service.lower():
                        self._dependency_graph[source_service].add(target_service)

    def _find_all_cycles(self) -> List[List[str]]:
        cycles = []
        visited = set()
        rec_stack = set()
        path = []

        def dfs(node: str) -> None:
            visited.add(node)
            rec_stack.add(node)
            path.append(node)

            for neighbor in self._dependency_graph.get(node, set()):
                if neighbor not in visited:
                    dfs(neighbor)
                elif neighbor in rec_stack:
                    cycle_start = path.index(neighbor)
                    cycle = path[cycle_start:]
                    if len(cycle) > 1:
                        cycles.append(cycle.copy())

            path.pop()
            rec_stack.remove(node)

        for node in list(self._dependency_graph.keys()):
            if node not in visited:
                dfs(node)

        unique_cycles = []
        seen = set()
        for cycle in cycles:
            normalized = tuple(sorted(cycle))
            if normalized not in seen:
                seen.add(normalized)
                unique_cycles.append(cycle)

        return unique_cycles

    def _create_circular_dependency(self, cycle: List[str], events: List[LogEvent]) -> Optional[CircularDependency]:
        involved_events = []
        for service in cycle:
            involved_events.extend(self._event_map.get(service, []))

        if not involved_events:
            return None

        severity = SeverityLevel.HIGH if len(cycle) > 3 else SeverityLevel.MEDIUM
        
        cycle_str = " -> ".join(cycle) + " -> " + cycle[0]
        description = f"检测到循环依赖: {cycle_str}"
        
        suggested_fix = self._generate_fix_suggestion(cycle)

        return CircularDependency(
            cycle_id=f"CYCLE-{hash(tuple(cycle)) % 10000:04d}",
            nodes=cycle,
            cycle_length=len(cycle),
            severity=severity,
            involved_events=involved_events[:20],
            description=description,
            suggested_fix=suggested_fix
        )

    def _generate_fix_suggestion(self, cycle: List[str]) -> str:
        if len(cycle) == 2:
            return f"考虑合并服务 {cycle[0]} 和 {cycle[1]}，或引入中间层解耦"
        elif len(cycle) == 3:
            return f"建议在 {cycle[0]} 和 {cycle[2]} 之间引入事件驱动架构或消息队列"
        else:
            return f"建议重构服务依赖关系，考虑使用服务网格或API网关来管理依赖"


class RootCauseAnalyzer:
    """智能根因分析器 - 深度分析错误的根本原因"""

    ROOT_CAUSE_INDICATORS = [
        (r'initial\s+(error|exception|failure)', 1.0),
        (r'root\s+cause', 1.0),
        (r'original\s+(error|exception)', 0.95),
        (r'first\s+(error|failure)', 0.9),
        (r'starting\s+point', 0.85),
        (r'underlying\s+(cause|error)', 0.85),
        (r'primary\s+(error|failure)', 0.8),
        (r'source\s+(error|of)', 0.75),
        (r'caused\s+by', 0.7),
        (r'due\s+to', 0.6),
        (r'because\s+of', 0.6),
        (r'triggered\s+by', 0.55),
        (r'result\s+of', 0.5),
    ]

    SYSTEMIC_PATTERNS = [
        (r'out\s+of\s+memory', 'memory_exhaustion'),
        (r'timeout', 'timeout'),
        (r'connection\s+(refused|reset|failed)', 'connection_issue'),
        (r'deadlock', 'deadlock'),
        (r'rate\s+limit', 'rate_limiting'),
        (r'quota\s+exceeded', 'quota_exceeded'),
        (r'disk\s+(full|space)', 'disk_space'),
        (r'cpu\s+(overload|high)', 'cpu_overload'),
        (r'thread\s+pool\s+exhausted', 'thread_pool_exhaustion'),
        (r'circuit\s+breaker\s+open', 'circuit_breaker'),
    ]

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self._compiled_indicators = [
            (re.compile(p, re.IGNORECASE), w) for p, w in self.ROOT_CAUSE_INDICATORS
        ]
        self._compiled_systemic = [
            (re.compile(p, re.IGNORECASE), t) for p, t in self.SYSTEMIC_PATTERNS
        ]

    def analyze(self, chain: ErrorPropagationChain, all_events: List[LogEvent]) -> RootCauseAnalysis:
        root_event = self._identify_root_cause(chain, all_events)
        contributing_factors = self._identify_contributing_factors(chain, all_events)
        evidence_chain = self._build_evidence_chain(chain)
        related_metrics = self._extract_related_metrics(chain, all_events)
        timeline = self._build_timeline(chain)

        confidence = self._calculate_confidence(chain, root_event, contributing_factors)

        return RootCauseAnalysis(
            analysis_id=f"RCA-{datetime.now().strftime('%Y%m%d%H%M%S')}-{hash(chain.chain_id) % 10000:04d}",
            root_cause_event=root_event,
            contributing_factors=contributing_factors,
            evidence_chain=evidence_chain,
            confidence_score=confidence,
            analysis_method="multi_factor_analysis",
            related_metrics=related_metrics,
            timeline=timeline
        )

    def _identify_root_cause(self, chain: ErrorPropagationChain, all_events: List[LogEvent]) -> LogEvent:
        candidates = []
        
        for event in chain.propagation_path:
            score = 0.0
            
            for pattern, weight in self._compiled_indicators:
                if pattern.search(event.message):
                    score += weight
            
            if event.level in ['CRITICAL', 'FATAL']:
                score += 0.3
            
            if not any(self._has_causal_reference(event, other) for other in chain.propagation_path if other.event_id != event.event_id):
                score += 0.2
            
            if event.error_type:
                score += 0.1
            
            candidates.append((event, score))

        if candidates:
            candidates.sort(key=lambda x: x[1], reverse=True)
            return candidates[0][0]

        return chain.root_cause

    def _has_causal_reference(self, event1: LogEvent, event2: LogEvent) -> bool:
        causal_keywords = ['caused', 'because', 'due to', 'triggered']
        msg_lower = event2.message.lower()
        return any(kw in msg_lower for kw in causal_keywords)

    def _identify_contributing_factors(self, chain: ErrorPropagationChain, all_events: List[LogEvent]) -> List[Dict[str, Any]]:
        factors = []
        
        systemic_issues = self._detect_systemic_issues(chain)
        factors.extend(systemic_issues)
        
        temporal_factors = self._analyze_temporal_factors(chain, all_events)
        factors.extend(temporal_factors)
        
        dependency_factors = self._analyze_dependency_factors(chain)
        factors.extend(dependency_factors)

        return factors[:10]

    def _detect_systemic_issues(self, chain: ErrorPropagationChain) -> List[Dict[str, Any]]:
        issues = []
        
        for event in chain.propagation_path:
            for pattern, issue_type in self._compiled_systemic:
                if pattern.search(event.message):
                    issues.append({
                        "type": "systemic_issue",
                        "issue_type": issue_type,
                        "event_id": event.event_id,
                        "description": f"检测到系统性问题: {issue_type}",
                        "confidence": 0.8
                    })

        return issues

    def _analyze_temporal_factors(self, chain: ErrorPropagationChain, all_events: List[LogEvent]) -> List[Dict[str, Any]]:
        factors = []
        
        chain_start = chain.propagation_path[0].timestamp
        window_before = timedelta(minutes=5)
        
        prior_events = [e for e in all_events if chain_start - window_before <= e.timestamp < chain_start]
        
        high_load = sum(1 for e in prior_events if 'request' in e.message.lower() or 'query' in e.message.lower())
        if high_load > 100:
            factors.append({
                "type": "temporal_factor",
                "factor": "high_load",
                "description": f"错误发生前5分钟内有 {high_load} 个请求/查询事件",
                "confidence": 0.7
            })

        prior_errors = sum(1 for e in prior_events if e.level in ['ERROR', 'CRITICAL', 'FATAL'])
        if prior_errors > 10:
            factors.append({
                "type": "temporal_factor",
                "factor": "error_escalation",
                "description": f"错误发生前5分钟内已有 {prior_errors} 个错误",
                "confidence": 0.75
            })

        return factors

    def _analyze_dependency_factors(self, chain: ErrorPropagationChain) -> List[Dict[str, Any]]:
        factors = []
        
        systems = list(chain.affected_systems)
        if len(systems) > 1:
            factors.append({
                "type": "dependency_factor",
                "factor": "multi_system_impact",
                "description": f"影响 {len(systems)} 个系统: {', '.join(systems)}",
                "confidence": 0.8
            })

        for event in chain.propagation_path:
            if 'timeout' in event.message.lower():
                factors.append({
                    "type": "dependency_factor",
                    "factor": "timeout_dependency",
                    "description": "存在超时依赖，可能是下游服务响应慢",
                    "confidence": 0.75
                })
                break

        return factors

    def _build_evidence_chain(self, chain: ErrorPropagationChain) -> List[Dict[str, Any]]:
        evidence = []
        
        for i, event in enumerate(chain.propagation_path):
            evidence.append({
                "step": i + 1,
                "event_id": event.event_id,
                "timestamp": event.timestamp.isoformat(),
                "system": event.source.system,
                "level": event.level,
                "message_preview": event.message[:100],
                "error_type": event.error_type
            })

        return evidence

    def _extract_related_metrics(self, chain: ErrorPropagationChain, all_events: List[LogEvent]) -> Dict[str, Any]:
        return {
            "propagation_depth": len(chain.propagation_path),
            "affected_systems_count": len(chain.affected_systems),
            "total_duration_seconds": chain.total_duration_seconds,
            "error_types": list(set(e.error_type for e in chain.propagation_path if e.error_type)),
            "severity_levels": list(set(e.level for e in chain.propagation_path)),
            "unique_users": len(set(e.user_id for e in chain.propagation_path if e.user_id)),
            "unique_requests": len(set(e.request_id for e in chain.propagation_path if e.request_id))
        }

    def _build_timeline(self, chain: ErrorPropagationChain) -> List[Dict[str, Any]]:
        timeline = []
        
        for i, event in enumerate(chain.propagation_path):
            timeline.append({
                "order": i,
                "timestamp": event.timestamp.isoformat(),
                "system": event.source.system,
                "event_type": "error" if event.level in ['ERROR', 'CRITICAL', 'FATAL'] else "warning",
                "summary": event.message[:80]
            })

        return timeline

    def _calculate_confidence(self, chain: ErrorPropagationChain, root_event: LogEvent, factors: List[Dict[str, Any]]) -> float:
        confidence = 0.5
        
        if root_event.error_type:
            confidence += 0.1
        
        if chain.confidence == CorrelationConfidence.HIGH:
            confidence += 0.2
        elif chain.confidence == CorrelationConfidence.MEDIUM:
            confidence += 0.1
        
        confidence += min(0.2, len(factors) * 0.05)
        
        if root_event.trace_id:
            confidence += 0.1

        return min(1.0, confidence)


class SourceHealthAnalyzer:
    """日志源健康状态分析器 - 评估各日志源的健康状况"""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.error_threshold = self.config.get('error_threshold', 0.05)
        self.warning_threshold = self.config.get('warning_threshold', 0.10)

    def analyze(self, events: List[LogEvent], sources: List[LogSource]) -> List[SourceHealthStatus]:
        """分析各日志源的健康状态"""
        events_by_source: Dict[str, List[LogEvent]] = defaultdict(list)
        for event in events:
            events_by_source[event.source.source_id].append(event)

        health_statuses = []
        for source in sources:
            source_events = events_by_source.get(source.source_id, [])
            health = self._analyze_source_health(source, source_events)
            health_statuses.append(health)

        return sorted(health_statuses, key=lambda x: x.health_score)

    def _analyze_source_health(self, source: LogSource, events: List[LogEvent]) -> SourceHealthStatus:
        """分析单个日志源的健康状态"""
        if not events:
            return SourceHealthStatus(
                source_id=source.source_id,
                source_name=source.name,
                health_score=0.0,
                error_rate=0.0,
                warning_rate=0.0,
                event_count=0,
                error_count=0,
                warning_count=0,
                last_error_time=None,
                status="无数据",
                issues=["日志源没有事件数据"]
            )

        error_events = [e for e in events if e.level in ['ERROR', 'CRITICAL', 'FATAL']]
        warning_events = [e for e in events if e.level in ['WARN', 'WARNING']]

        error_count = len(error_events)
        warning_count = len(warning_events)
        total_count = len(events)

        error_rate = error_count / total_count if total_count > 0 else 0
        warning_rate = warning_count / total_count if total_count > 0 else 0

        last_error_time = None
        if error_events:
            last_error = max(error_events, key=lambda x: x.timestamp)
            last_error_time = last_error.timestamp.isoformat()

        health_score = self._calculate_health_score(error_rate, warning_rate, events)
        status, issues = self._determine_status(error_rate, warning_rate, events)

        metrics = self._calculate_metrics(events)

        return SourceHealthStatus(
            source_id=source.source_id,
            source_name=source.name,
            health_score=health_score,
            error_rate=error_rate,
            warning_rate=warning_rate,
            event_count=total_count,
            error_count=error_count,
            warning_count=warning_count,
            last_error_time=last_error_time,
            status=status,
            issues=issues,
            metrics=metrics
        )

    def _calculate_health_score(self, error_rate: float, warning_rate: float, events: List[LogEvent]) -> float:
        """计算健康分数 (0-100)"""
        score = 100.0

        score -= error_rate * 500
        score -= warning_rate * 200

        if events:
            time_range = (events[-1].timestamp - events[0].timestamp).total_seconds()
            if time_range > 0:
                event_rate = len(events) / (time_range / 60)
                if event_rate > 1000:
                    score -= 10
                elif event_rate < 1:
                    score -= 5

        return max(0.0, min(100.0, score))

    def _determine_status(self, error_rate: float, warning_rate: float, events: List[LogEvent]) -> Tuple[str, List[str]]:
        """确定健康状态和问题列表"""
        issues = []

        if error_rate > self.error_threshold:
            issues.append(f"错误率过高 ({error_rate:.2%})")
        if warning_rate > self.warning_threshold:
            issues.append(f"警告率过高 ({warning_rate:.2%})")

        critical_count = sum(1 for e in events if e.level in ['CRITICAL', 'FATAL'])
        if critical_count > 0:
            issues.append(f"存在 {critical_count} 个严重错误")

        if error_rate > 0.1:
            status = "严重"
        elif error_rate > self.error_threshold:
            status = "警告"
        elif warning_rate > self.warning_threshold:
            status = "注意"
        elif issues:
            status = "轻微"
        else:
            status = "健康"

        return status, issues

    def _calculate_metrics(self, events: List[LogEvent]) -> Dict[str, Any]:
        """计算额外指标"""
        if not events:
            return {}

        time_range = (events[-1].timestamp - events[0].timestamp).total_seconds()

        return {
            "events_per_minute": len(events) / max(1, time_range / 60),
            "unique_threads": len(set(e.thread_id for e in events if e.thread_id)),
            "unique_users": len(set(e.user_id for e in events if e.user_id)),
            "unique_requests": len(set(e.request_id for e in events if e.request_id)),
            "time_range_minutes": time_range / 60
        }


class SourceDependencyAnalyzer:
    """日志源依赖分析器 - 分析日志源之间的依赖关系"""

    DEPENDENCY_INDICATORS = [
        (r'calling\s+service[:\s]*(\w+)', 'service_call'),
        (r'requesting\s+from[:\s]*(\w+)', 'request'),
        (r'connecting\s+to[:\s]*(\w+)', 'connection'),
        (r'querying[:\s]*(\w+)', 'database'),
        (r'publishing\s+to[:\s]*(\w+)', 'messaging'),
        (r'depending\s+on[:\s]*(\w+)', 'dependency'),
        (r'upstream[:\s]*(\w+)', 'upstream'),
        (r'downstream[:\s]*(\w+)', 'downstream'),
    ]

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self._compiled_patterns = [
            (re.compile(p, re.IGNORECASE), t) for p, t in self.DEPENDENCY_INDICATORS
        ]

    def analyze(self, events: List[LogEvent], sources: List[LogSource]) -> List[SourceDependency]:
        """分析日志源之间的依赖关系"""
        source_names = {s.source_id: s.name for s in sources}
        source_systems = {s.system.lower(): s.source_id for s in sources}

        dependency_evidence: Dict[Tuple[str, str], List[LogEvent]] = defaultdict(list)
        error_correlations: Dict[Tuple[str, str], int] = defaultdict(int)

        for event in events:
            source_id = event.source.source_id
            dependencies = self._extract_dependencies(event.message, source_systems)

            for dep_id in dependencies:
                if dep_id != source_id:
                    key = (source_id, dep_id)
                    dependency_evidence[key].append(event)
                    if event.level in ['ERROR', 'CRITICAL', 'FATAL']:
                        error_correlations[key] += 1

        dependencies = []
        for (source_id, dep_id), events_list in dependency_evidence.items():
            strength = self._calculate_dependency_strength(
                events_list, 
                error_correlations.get((source_id, dep_id), 0)
            )

            dep_type = self._determine_dependency_type(events_list)
            description = self._generate_description(
                source_names.get(source_id, source_id),
                source_names.get(dep_id, dep_id),
                dep_type,
                len(events_list)
            )

            dependencies.append(SourceDependency(
                source_id=source_id,
                depends_on=[dep_id],
                dependency_type=dep_type,
                strength=strength,
                evidence_count=len(events_list),
                correlated_errors=error_correlations.get((source_id, dep_id), 0),
                description=description
            ))

        return sorted(dependencies, key=lambda x: x.strength, reverse=True)

    def _extract_dependencies(self, message: str, source_systems: Dict[str, str]) -> List[str]:
        """从消息中提取依赖关系"""
        dependencies = []
        for pattern, _ in self._compiled_patterns:
            matches = pattern.findall(message)
            for match in matches:
                match_lower = match.lower()
                if match_lower in source_systems:
                    dependencies.append(source_systems[match_lower])
        return dependencies

    def _calculate_dependency_strength(self, events: List[LogEvent], error_count: int) -> float:
        """计算依赖强度"""
        base_strength = min(1.0, len(events) / 100)

        error_factor = min(0.3, error_count / 50)

        return min(1.0, base_strength + error_factor)

    def _determine_dependency_type(self, events: List[LogEvent]) -> str:
        """确定依赖类型"""
        type_counts: Dict[str, int] = defaultdict(int)

        for event in events:
            msg_lower = event.message.lower()
            if 'service' in msg_lower or 'api' in msg_lower:
                type_counts['service'] += 1
            elif 'database' in msg_lower or 'sql' in msg_lower or 'query' in msg_lower:
                type_counts['database'] += 1
            elif 'message' in msg_lower or 'queue' in msg_lower:
                type_counts['messaging'] += 1
            elif 'cache' in msg_lower:
                type_counts['cache'] += 1
            else:
                type_counts['unknown'] += 1

        if type_counts:
            return max(type_counts, key=type_counts.get)
        return 'unknown'

    def _generate_description(self, source_name: str, dep_name: str, dep_type: str, count: int) -> str:
        """生成依赖描述"""
        type_names = {
            'service': '服务调用',
            'database': '数据库访问',
            'messaging': '消息通信',
            'cache': '缓存访问',
            'unknown': '未知类型'
        }
        return f"{source_name} -> {dep_name} ({type_names.get(dep_type, dep_type)}, {count} 次交互)"


class ErrorPatternRecognizer:
    """错误模式识别器 - 识别和分类错误模式"""

    PATTERN_TYPES = {
        'timeout': {
            'patterns': [r'timeout', r'timed\s+out', r'deadline\s+exceeded'],
            'fix': '检查超时配置，考虑增加超时时间或优化处理逻辑'
        },
        'connection': {
            'patterns': [r'connection\s+(refused|reset|failed|closed)', r'connect\s+error'],
            'fix': '检查网络连接、防火墙设置和服务可用性'
        },
        'memory': {
            'patterns': [r'out\s+of\s+memory', r'memory\s+(exhausted|limit)', r'heap\s+space'],
            'fix': '增加内存配置，检查内存泄漏，优化内存使用'
        },
        'database': {
            'patterns': [r'sql\s+error', r'database\s+error', r'query\s+failed', r'deadlock'],
            'fix': '检查数据库连接、查询性能和锁竞争'
        },
        'authentication': {
            'patterns': [r'auth(entication)?\s+(failed|error)', r'invalid\s+(token|credentials)', r'access\s+denied'],
            'fix': '检查认证配置、凭证有效性和权限设置'
        },
        'rate_limit': {
            'patterns': [r'rate\s+limit', r'too\s+many\s+requests', r'throttl'],
            'fix': '调整限流配置，实现请求队列或退避策略'
        },
        'resource': {
            'patterns': [r'resource\s+(exhausted|unavailable)', r'thread\s+pool\s+exhausted', r'circuit\s+breaker'],
            'fix': '增加资源配额，实现资源池化和熔断机制'
        },
    }

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self._compiled_patterns = {}
        for pattern_type, info in self.PATTERN_TYPES.items():
            self._compiled_patterns[pattern_type] = [
                re.compile(p, re.IGNORECASE) for p in info['patterns']
            ]

    def recognize(self, events: List[LogEvent]) -> List[ErrorPattern]:
        """识别错误模式"""
        error_events = [e for e in events if e.level in ['ERROR', 'CRITICAL', 'FATAL', 'WARN', 'WARNING']]

        patterns_by_type: Dict[str, List[LogEvent]] = defaultdict(list)
        pattern_signatures: Dict[str, str] = {}

        for event in error_events:
            pattern_type = self._classify_error(event.message)
            if pattern_type:
                signature = self._create_signature(event.message)
                patterns_by_type[pattern_type].append(event)
                if pattern_type not in pattern_signatures:
                    pattern_signatures[pattern_type] = signature

        error_patterns = []
        for pattern_type, pattern_events in patterns_by_type.items():
            if len(pattern_events) >= 2:
                error_pattern = self._create_error_pattern(
                    pattern_type,
                    pattern_events,
                    pattern_signatures.get(pattern_type, '')
                )
                error_patterns.append(error_pattern)

        return sorted(error_patterns, key=lambda x: x.occurrence_count, reverse=True)

    def _classify_error(self, message: str) -> Optional[str]:
        """分类错误类型"""
        for pattern_type, patterns in self._compiled_patterns.items():
            for pattern in patterns:
                if pattern.search(message):
                    return pattern_type
        return None

    def _create_signature(self, message: str) -> str:
        """创建错误签名"""
        signature = message.lower()
        signature = re.sub(r'\d+', '#', signature)
        signature = re.sub(r'0x[a-fA-F0-9]+', '#HEX#', signature)
        signature = re.sub(r'[a-fA-F0-9]{8}-[a-fA-F0-9]{4}-[a-fA-F0-9]{4}-[a-fA-F0-9]{4}-[a-fA-F0-9]{12}', '#UUID#', signature)
        signature = re.sub(r'https?://[^\s]+', '#URL#', signature)
        signature = re.sub(r'/[\w/\.]+', '#PATH#', signature)
        return signature[:200]

    def _create_error_pattern(
        self, 
        pattern_type: str, 
        events: List[LogEvent],
        signature: str
    ) -> ErrorPattern:
        """创建错误模式对象"""
        sorted_events = sorted(events, key=lambda x: x.timestamp)

        affected_sources = list(set(e.source.source_id for e in events))
        affected_systems = list(set(e.source.system for e in events))

        severity = self._determine_severity(events)

        example_events = [
            {
                "event_id": e.event_id,
                "timestamp": e.timestamp.isoformat(),
                "message": e.message[:100],
                "level": e.level
            }
            for e in sorted_events[:3]
        ]

        suggested_fix = self.PATTERN_TYPES.get(pattern_type, {}).get('fix', '分析错误日志以确定根本原因')

        trend = self._calculate_trend(events)

        return ErrorPattern(
            pattern_id=f"EP-{pattern_type.upper()}-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            pattern_type=pattern_type,
            pattern_signature=signature,
            occurrence_count=len(events),
            affected_sources=affected_sources,
            affected_systems=affected_systems,
            first_occurrence=sorted_events[0].timestamp.isoformat(),
            last_occurrence=sorted_events[-1].timestamp.isoformat(),
            severity=severity,
            example_events=example_events,
            suggested_fix=suggested_fix,
            trend=trend
        )

    def _determine_severity(self, events: List[LogEvent]) -> SeverityLevel:
        """确定模式严重度"""
        critical_count = sum(1 for e in events if e.level in ['CRITICAL', 'FATAL'])
        if critical_count > 0:
            return SeverityLevel.CRITICAL

        error_count = sum(1 for e in events if e.level == 'ERROR')
        if error_count >= 5:
            return SeverityLevel.HIGH
        elif error_count >= 2:
            return SeverityLevel.MEDIUM

        return SeverityLevel.LOW

    def _calculate_trend(self, events: List[LogEvent]) -> str:
        """计算错误趋势"""
        if len(events) < 3:
            return "数据不足"

        sorted_events = sorted(events, key=lambda x: x.timestamp)
        mid = len(sorted_events) // 2

        first_half = len(sorted_events[:mid])
        second_half = len(sorted_events[mid:])

        if second_half > first_half * 1.5:
            return "上升"
        elif second_half < first_half * 0.7:
            return "下降"
        else:
            return "稳定"


class ErrorChainClusterer:
    """错误传播链聚类器 - 将相似的错误传播链聚类"""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.similarity_threshold = self.config.get('similarity_threshold', 0.6)

    def cluster(self, chains: List[ErrorPropagationChain]) -> List[ChainCluster]:
        """对错误传播链进行聚类"""
        if not chains:
            return []

        clusters: List[List[ErrorPropagationChain]] = []
        used_indices: Set[int] = set()

        for i, chain1 in enumerate(chains):
            if i in used_indices:
                continue

            cluster = [chain1]
            used_indices.add(i)

            for j, chain2 in enumerate(chains):
                if j in used_indices:
                    continue

                similarity = self._calculate_similarity(chain1, chain2)
                if similarity >= self.similarity_threshold:
                    cluster.append(chain2)
                    used_indices.add(j)

            if len(cluster) >= 1:
                clusters.append(cluster)

        chain_clusters = []
        for i, cluster in enumerate(clusters):
            chain_cluster = self._create_cluster(cluster, i)
            chain_clusters.append(chain_cluster)

        return sorted(chain_clusters, key=lambda x: x.cluster_severity.value)

    def _calculate_similarity(self, chain1: ErrorPropagationChain, chain2: ErrorPropagationChain) -> float:
        """计算两个传播链的相似度"""
        score = 0.0

        systems1 = chain1.affected_systems
        systems2 = chain2.affected_systems
        system_overlap = len(systems1 & systems2) / max(1, len(systems1 | systems2))
        score += system_overlap * 0.4

        root1 = self._normalize_message(chain1.root_cause.message)
        root2 = self._normalize_message(chain2.root_cause.message)
        if root1 == root2:
            score += 0.3
        elif root1[:50] == root2[:50]:
            score += 0.2

        error_types1 = set(e.error_type for e in chain1.propagation_path if e.error_type)
        error_types2 = set(e.error_type for e in chain2.propagation_path if e.error_type)
        if error_types1 and error_types2:
            type_overlap = len(error_types1 & error_types2) / max(1, len(error_types1 | error_types2))
            score += type_overlap * 0.3

        return score

    def _normalize_message(self, message: str) -> str:
        """标准化消息用于比较"""
        normalized = message.lower()
        normalized = re.sub(r'\d+', '#', normalized)
        normalized = re.sub(r'\s+', ' ', normalized)
        return normalized.strip()

    def _create_cluster(self, chains: List[ErrorPropagationChain], cluster_index: int) -> ChainCluster:
        """创建聚类对象"""
        common_root_cause = self._find_common_root_cause(chains)

        common_systems = set()
        for chain in chains:
            common_systems.update(chain.affected_systems)

        total_events = sum(len(chain.propagation_path) for chain in chains)

        severity = max(chains, key=lambda x: ['critical', 'high', 'medium', 'low'].index(x.severity.value)).severity

        description = f"包含 {len(chains)} 条相似错误传播链，共同影响 {len(common_systems)} 个系统"

        aggregated_actions = self._aggregate_actions(chains)

        return ChainCluster(
            cluster_id=f"CLUSTER-{cluster_index:03d}-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            chains=chains,
            common_root_cause=common_root_cause,
            common_systems=common_systems,
            total_events=total_events,
            cluster_severity=severity,
            cluster_description=description,
            aggregated_actions=aggregated_actions
        )

    def _find_common_root_cause(self, chains: List[ErrorPropagationChain]) -> str:
        """找到共同的根因描述"""
        if not chains:
            return ""

        root_messages = [chain.root_cause.message for chain in chains]
        return max(set(root_messages), key=root_messages.count)

    def _aggregate_actions(self, chains: List[ErrorPropagationChain]) -> List[str]:
        """聚合建议操作"""
        all_actions = []
        for chain in chains:
            all_actions.extend(chain.suggested_actions)

        action_counts: Dict[str, int] = defaultdict(int)
        for action in all_actions:
            action_counts[action] += 1

        sorted_actions = sorted(action_counts.items(), key=lambda x: x[1], reverse=True)
        return [action for action, _ in sorted_actions[:5]]


class ReportGenerator:
    """关联分析报告生成器 - 生成完整的分析报告"""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}

    def generate_executive_summary(
        self,
        report: CorrelationReport,
        events: List[LogEvent]
    ) -> ExecutiveSummary:
        """生成执行摘要"""
        critical_count = sum(1 for c in report.error_chains if c.severity == SeverityLevel.CRITICAL)
        high_count = sum(1 for c in report.error_chains if c.severity == SeverityLevel.HIGH)

        health_score = self._calculate_overall_health(report)

        top_issues = self._extract_top_issues(report)

        key_findings = self._generate_key_findings(report)

        immediate_actions = self._generate_immediate_actions(report)

        risk_level = self._determine_risk_level(critical_count, high_count, health_score)

        trend_indicator = self._determine_trend_indicator(report)

        analysis_period = {}
        if events:
            analysis_period = {
                "start": events[0].timestamp.isoformat(),
                "end": events[-1].timestamp.isoformat()
            }

        return ExecutiveSummary(
            summary_id=f"ES-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            analysis_period=analysis_period,
            total_events_analyzed=len(events),
            total_sources=len(report.sources),
            critical_issues_count=critical_count,
            high_issues_count=high_count,
            overall_health_score=health_score,
            top_issues=top_issues,
            key_findings=key_findings,
            immediate_actions=immediate_actions,
            risk_level=risk_level,
            trend_indicator=trend_indicator
        )

    def _calculate_overall_health(self, report: CorrelationReport) -> float:
        """计算整体健康分数"""
        if not report.source_health_statuses:
            return 50.0

        avg_health = sum(s.health_score for s in report.source_health_statuses) / len(report.source_health_statuses)

        critical_penalty = sum(10 for c in report.error_chains if c.severity == SeverityLevel.CRITICAL)
        high_penalty = sum(5 for c in report.error_chains if c.severity == SeverityLevel.HIGH)

        return max(0.0, min(100.0, avg_health - critical_penalty - high_penalty))

    def _extract_top_issues(self, report: CorrelationReport) -> List[Dict[str, Any]]:
        """提取主要问题"""
        issues = []

        for chain in sorted(report.error_chains, key=lambda x: ['critical', 'high', 'medium', 'low'].index(x.severity.value))[:5]:
            issues.append({
                "type": "error_chain",
                "severity": chain.severity.value,
                "description": chain.description[:100],
                "affected_systems": list(chain.affected_systems)
            })

        for pattern in report.error_patterns[:3]:
            issues.append({
                "type": "error_pattern",
                "severity": pattern.severity.value,
                "description": f"{pattern.pattern_type} 模式出现 {pattern.occurrence_count} 次",
                "affected_systems": pattern.affected_systems
            })

        return issues[:10]

    def _generate_key_findings(self, report: CorrelationReport) -> List[str]:
        """生成关键发现"""
        findings = []

        if report.error_chains:
            critical_chains = [c for c in report.error_chains if c.severity == SeverityLevel.CRITICAL]
            if critical_chains:
                findings.append(f"发现 {len(critical_chains)} 条严重错误传播链需要立即处理")

        if report.cross_system_traces:
            error_traces = [t for t in report.cross_system_traces if t.error_count > 0]
            if error_traces:
                findings.append(f"发现 {len(error_traces)} 条跨系统调用链存在错误")

        if report.circular_dependencies:
            findings.append(f"检测到 {len(report.circular_dependencies)} 个循环依赖可能导致系统不稳定")

        if report.source_health_statuses:
            unhealthy = [s for s in report.source_health_statuses if s.status in ['严重', '警告']]
            if unhealthy:
                findings.append(f"{len(unhealthy)} 个日志源处于非健康状态")

        if report.time_series_analysis:
            rising = [ts for ts in report.time_series_analysis if ts.trend == "上升"]
            if rising:
                findings.append(f"发现 {len(rising)} 个上升趋势的时间序列")

        return findings[:5]

    def _generate_immediate_actions(self, report: CorrelationReport) -> List[str]:
        """生成立即行动建议"""
        actions = []

        for chain in report.error_chains[:3]:
            if chain.severity in [SeverityLevel.CRITICAL, SeverityLevel.HIGH]:
                actions.extend(chain.suggested_actions[:2])

        if report.circular_dependencies:
            actions.append("优先解决循环依赖问题")

        unhealthy_sources = [s for s in report.source_health_statuses if s.status == '严重']
        if unhealthy_sources:
            actions.append(f"立即检查 {len(unhealthy_sources)} 个严重状态的日志源")

        return list(dict.fromkeys(actions))[:5]

    def _determine_risk_level(self, critical_count: int, high_count: int, health_score: float) -> str:
        """确定风险等级"""
        if critical_count > 0 or health_score < 50:
            return "高风险"
        elif high_count > 3 or health_score < 70:
            return "中风险"
        elif high_count > 0 or health_score < 85:
            return "低风险"
        else:
            return "正常"

    def _determine_trend_indicator(self, report: CorrelationReport) -> str:
        """确定趋势指标"""
        if not report.time_series_analysis:
            return "数据不足"

        rising = sum(1 for ts in report.time_series_analysis if ts.trend == "上升")
        falling = sum(1 for ts in report.time_series_analysis if ts.trend == "下降")
        stable = sum(1 for ts in report.time_series_analysis if ts.trend == "稳定")

        if rising > falling + stable:
            return "恶化"
        elif falling > rising + stable:
            return "改善"
        else:
            return "稳定"

    def generate_key_metrics(
        self,
        report: CorrelationReport,
        events: List[LogEvent]
    ) -> KeyMetrics:
        """生成关键指标"""
        total_events = len(events)
        error_events = [e for e in events if e.level in ['ERROR', 'CRITICAL', 'FATAL']]
        warning_events = [e for e in events if e.level in ['WARN', 'WARNING']]

        error_rate = len(error_events) / total_events if total_events > 0 else 0
        warning_rate = len(warning_events) / total_events if total_events > 0 else 0

        avg_chain_length = 0.0
        if report.error_chains:
            avg_chain_length = sum(len(c.propagation_path) for c in report.error_chains) / len(report.error_chains)

        bottleneck_count = sum(1 for t in report.cross_system_traces if t.bottleneck_detected)

        anomaly_count = sum(len(ts.anomalies) for ts in report.time_series_analysis)

        health_score = self._calculate_overall_health(report)

        mttr_estimate = self._estimate_mttr(report)

        avg_response_time = 0.0
        if report.cross_system_traces:
            avg_response_time = sum(t.total_duration_seconds for t in report.cross_system_traces) / len(report.cross_system_traces)

        return KeyMetrics(
            error_rate=error_rate,
            warning_rate=warning_rate,
            avg_response_time=avg_response_time,
            error_chain_avg_length=avg_chain_length,
            cross_system_call_count=len(report.cross_system_traces),
            bottleneck_count=bottleneck_count,
            circular_dependency_count=len(report.circular_dependencies),
            anomaly_count=anomaly_count,
            health_score=health_score,
            mttr_estimate=mttr_estimate
        )

    def _estimate_mttr(self, report: CorrelationReport) -> float:
        """估算平均恢复时间 (MTTR)"""
        if not report.error_chains:
            return 0.0

        durations = [c.total_duration_seconds / 60 for c in report.error_chains if c.total_duration_seconds > 0]
        if not durations:
            return 0.0

        return sum(durations) / len(durations)

    def generate_chart_data(self, report: CorrelationReport, events: List[LogEvent]) -> List[ChartData]:
        """生成图表数据"""
        charts = []

        charts.append(self._create_level_distribution_chart(events))

        charts.append(self._create_timeline_chart(events))

        charts.append(self._create_system_distribution_chart(events))

        charts.append(self._create_error_chain_chart(report))

        charts.append(self._create_source_health_chart(report))

        return charts

    def _create_level_distribution_chart(self, events: List[LogEvent]) -> ChartData:
        """创建日志级别分布图表"""
        level_counts: Dict[str, int] = defaultdict(int)
        for event in events:
            level_counts[event.level] += 1

        return ChartData(
            chart_id="level-distribution",
            chart_type="pie",
            title="日志级别分布",
            data={
                "labels": list(level_counts.keys()),
                "values": list(level_counts.values())
            },
            options={
                "colors": {
                    "ERROR": "#dc3545",
                    "CRITICAL": "#721c24",
                    "WARNING": "#ffc107",
                    "INFO": "#17a2b8",
                    "DEBUG": "#6c757d"
                }
            }
        )

    def _create_timeline_chart(self, events: List[LogEvent]) -> ChartData:
        """创建时间线图表"""
        hourly_data: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))

        for event in events:
            hour_key = event.timestamp.strftime('%Y-%m-%d %H')
            hourly_data[hour_key][event.level] += 1

        sorted_hours = sorted(hourly_data.keys())

        return ChartData(
            chart_id="timeline",
            chart_type="line",
            title="事件时间线",
            data={
                "labels": sorted_hours,
                "datasets": {
                    "ERROR": [hourly_data[h]['ERROR'] for h in sorted_hours],
                    "WARNING": [hourly_data[h]['WARNING'] + hourly_data[h]['WARN'] for h in sorted_hours],
                    "INFO": [hourly_data[h]['INFO'] for h in sorted_hours]
                }
            },
            options={
                "xAxisLabel": "时间",
                "yAxisLabel": "事件数量"
            }
        )

    def _create_system_distribution_chart(self, events: List[LogEvent]) -> ChartData:
        """创建系统分布图表"""
        system_counts: Dict[str, int] = defaultdict(int)
        for event in events:
            system_counts[event.source.system] += 1

        sorted_systems = sorted(system_counts.items(), key=lambda x: x[1], reverse=True)[:10]

        return ChartData(
            chart_id="system-distribution",
            chart_type="bar",
            title="系统事件分布 (Top 10)",
            data={
                "labels": [s[0] for s in sorted_systems],
                "values": [s[1] for s in sorted_systems]
            },
            options={
                "xAxisLabel": "系统",
                "yAxisLabel": "事件数量"
            }
        )

    def _create_error_chain_chart(self, report: CorrelationReport) -> ChartData:
        """创建错误传播链图表"""
        chain_data = []
        for chain in report.error_chains[:10]:
            chain_data.append({
                "chain_id": chain.chain_id,
                "severity": chain.severity.value,
                "length": len(chain.propagation_path),
                "duration": chain.total_duration_seconds,
                "systems": list(chain.affected_systems)
            })

        return ChartData(
            chart_id="error-chains",
            chart_type="table",
            title="错误传播链概览",
            data={
                "rows": chain_data
            },
            options={
                "columns": ["chain_id", "severity", "length", "duration", "systems"]
            }
        )

    def _create_source_health_chart(self, report: CorrelationReport) -> ChartData:
        """创建源健康状态图表"""
        health_data = []
        for status in report.source_health_statuses:
            health_data.append({
                "source": status.source_name,
                "health_score": status.health_score,
                "error_count": status.error_count,
                "status": status.status
            })

        return ChartData(
            chart_id="source-health",
            chart_type="gauge",
            title="日志源健康状态",
            data={
                "values": health_data
            },
            options={
                "thresholds": {
                    "healthy": 80,
                    "warning": 60,
                    "critical": 40
                }
            }
        )

    def generate_detailed_statistics(self, report: CorrelationReport, events: List[LogEvent]) -> Dict[str, Any]:
        """生成详细统计数据"""
        return {
            "event_statistics": self._calculate_event_statistics(events),
            "error_statistics": self._calculate_error_statistics(events),
            "time_statistics": self._calculate_time_statistics(events),
            "source_statistics": self._calculate_source_statistics(report),
            "correlation_statistics": self._calculate_correlation_statistics(report)
        }

    def _calculate_event_statistics(self, events: List[LogEvent]) -> Dict[str, Any]:
        """计算事件统计"""
        if not events:
            return {}

        level_dist: Dict[str, int] = defaultdict(int)
        for event in events:
            level_dist[event.level] += 1

        return {
            "total_events": len(events),
            "level_distribution": dict(level_dist),
            "unique_threads": len(set(e.thread_id for e in events if e.thread_id)),
            "unique_users": len(set(e.user_id for e in events if e.user_id)),
            "unique_requests": len(set(e.request_id for e in events if e.request_id)),
            "unique_traces": len(set(e.trace_id for e in events if e.trace_id))
        }

    def _calculate_error_statistics(self, events: List[LogEvent]) -> Dict[str, Any]:
        """计算错误统计"""
        error_events = [e for e in events if e.level in ['ERROR', 'CRITICAL', 'FATAL']]

        if not error_events:
            return {"total_errors": 0}

        error_types: Dict[str, int] = defaultdict(int)
        for event in error_events:
            if event.error_type:
                error_types[event.error_type] += 1

        return {
            "total_errors": len(error_events),
            "critical_count": sum(1 for e in error_events if e.level in ['CRITICAL', 'FATAL']),
            "error_types": dict(sorted(error_types.items(), key=lambda x: x[1], reverse=True)[:10]),
            "errors_per_source": {
                source: sum(1 for e in error_events if e.source.source_id == source)
                for source in set(e.source.source_id for e in error_events)
            }
        }

    def _calculate_time_statistics(self, events: List[LogEvent]) -> Dict[str, Any]:
        """计算时间统计"""
        if not events:
            return {}

        sorted_events = sorted(events, key=lambda x: x.timestamp)
        time_range = (sorted_events[-1].timestamp - sorted_events[0].timestamp).total_seconds()

        hourly_dist: Dict[int, int] = defaultdict(int)
        for event in events:
            hourly_dist[event.timestamp.hour] += 1

        return {
            "time_range_seconds": time_range,
            "time_range_hours": time_range / 3600,
            "events_per_minute": len(events) / max(1, time_range / 60),
            "hourly_distribution": dict(hourly_dist),
            "peak_hour": max(hourly_dist, key=hourly_dist.get) if hourly_dist else None
        }

    def _calculate_source_statistics(self, report: CorrelationReport) -> Dict[str, Any]:
        """计算源统计"""
        if not report.source_health_statuses:
            return {}

        return {
            "total_sources": len(report.source_health_statuses),
            "healthy_sources": sum(1 for s in report.source_health_statuses if s.status == "健康"),
            "warning_sources": sum(1 for s in report.source_health_statuses if s.status in ["警告", "注意"]),
            "critical_sources": sum(1 for s in report.source_health_statuses if s.status == "严重"),
            "average_health_score": sum(s.health_score for s in report.source_health_statuses) / len(report.source_health_statuses)
        }

    def _calculate_correlation_statistics(self, report: CorrelationReport) -> Dict[str, Any]:
        """计算关联统计"""
        type_dist: Dict[str, int] = defaultdict(int)
        for corr in report.correlations:
            type_dist[corr.correlation_type.value] += 1

        return {
            "total_correlations": len(report.correlations),
            "correlation_types": dict(type_dist),
            "average_confidence": sum(c.confidence_score for c in report.correlations) / len(report.correlations) if report.correlations else 0,
            "error_chains": len(report.error_chains),
            "cross_system_traces": len(report.cross_system_traces),
            "circular_dependencies": len(report.circular_dependencies)
        }


class EnhancedLogCorrelator:
    """增强日志关联分析主类 - 整合所有分析功能"""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        
        self.parser = LogEventParser()
        
        self.error_analyzer = ErrorPropagationAnalyzer(
            time_window_seconds=self.config.get('error_window_seconds', 300),
            config=self.config.get('error_analyzer_config', {})
        )
        
        self.cross_system_tracer = CrossSystemTracer(
            min_events=self.config.get('min_trace_events', 2),
            config=self.config.get('tracer_config', {})
        )
        
        self.multi_source_correlator = MultiSourceCorrelator(
            config=self.config.get('correlator_config', {})
        )
        
        self.impact_analyzer = ImpactAnalyzer(
            config=self.config.get('impact_config', {})
        )
        
        self.time_series_analyzer = TimeSeriesAnalyzer(
            config=self.config.get('time_series_config', {})
        )
        
        self.circular_dependency_detector = CircularDependencyDetector(
            config=self.config.get('circular_dependency_config', {})
        )
        
        self.root_cause_analyzer = RootCauseAnalyzer(
            config=self.config.get('root_cause_config', {})
        )
        
        self.source_health_analyzer = SourceHealthAnalyzer(
            config=self.config.get('source_health_config', {})
        )
        
        self.source_dependency_analyzer = SourceDependencyAnalyzer(
            config=self.config.get('source_dependency_config', {})
        )
        
        self.error_pattern_recognizer = ErrorPatternRecognizer(
            config=self.config.get('error_pattern_config', {})
        )
        
        self.error_chain_clusterer = ErrorChainClusterer(
            config=self.config.get('chain_cluster_config', {})
        )
        
        self.report_generator = ReportGenerator(
            config=self.config.get('report_generator_config', {})
        )
        
        self._events: List[LogEvent] = []
        self._sources: List[LogSource] = []
        self._correlation_cache: Dict[str, Any] = {}

    def add_source(self, source: LogSource) -> None:
        self._sources.append(source)
        logger.info(f"添加日志源: {source.name} ({source.path})")

    def load_events(self) -> int:
        total_events = 0
        for source in self._sources:
            try:
                count = self._load_from_source(source)
                total_events += count
                logger.info(f"从 {source.name} 加载了 {count} 条日志事件")
            except Exception as e:
                logger.error(f"加载日志源 {source.name} 失败: {e}")

        self._events.sort(key=lambda x: x.timestamp)
        return total_events

    def _load_from_source(self, source: LogSource) -> int:
        path = Path(source.path)
        if not path.exists():
            raise FileNotFoundError(f"日志路径不存在: {source.path}")

        events = []
        if path.is_file():
            events = self._parse_file(path, source)
        elif path.is_dir():
            for log_file in path.rglob('*'):
                if log_file.is_file() and log_file.suffix in ['.log', '.json', '.txt']:
                    events.extend(self._parse_file(log_file, source))

        self._events.extend(events)
        return len(events)

    def _parse_file(self, file_path: Path, source: LogSource) -> List[LogEvent]:
        events = []
        try:
            with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()
                    if not line:
                        continue

                    if line.startswith('{') and line.endswith('}'):
                        try:
                            data = json.loads(line)
                            event = self.parser.parse_json_line(data, source, line_num)
                            events.append(event)
                        except json.JSONDecodeError:
                            event = self.parser.parse_line(line, source, line_num)
                            if event:
                                events.append(event)
                    else:
                        event = self.parser.parse_line(line, source, line_num)
                        if event:
                            events.append(event)
        except Exception as e:
            logger.error(f"解析文件 {file_path} 失败: {e}")

        return events

    def correlate(self) -> CorrelationReport:
        """执行完整的日志关联分析"""
        logger.info("开始日志关联分析...")

        error_chains = self.error_analyzer.analyze(self._events)
        logger.info(f"发现 {len(error_chains)} 条错误传播链")

        cross_system_traces = self.cross_system_tracer.trace(self._events)
        logger.info(f"发现 {len(cross_system_traces)} 条跨系统追踪")

        correlations = self.multi_source_correlator.correlate(self._events)
        logger.info(f"发现 {len(correlations)} 个关联模式")

        impact_assessments = self.impact_analyzer.analyze(error_chains, cross_system_traces, self._events)
        logger.info(f"生成 {len(impact_assessments)} 个影响评估")

        time_series_analysis = self.time_series_analyzer.analyze(self._events)
        logger.info(f"完成 {len(time_series_analysis)} 个时间序列分析")

        circular_dependencies = self.circular_dependency_detector.detect(self._events)
        logger.info(f"检测到 {len(circular_dependencies)} 个循环依赖")

        root_cause_analyses = []
        for chain in error_chains[:10]:
            rca = self.root_cause_analyzer.analyze(chain, self._events)
            root_cause_analyses.append(rca)
        logger.info(f"完成 {len(root_cause_analyses)} 个根因分析")

        source_health_statuses = self.source_health_analyzer.analyze(self._events, self._sources)
        logger.info(f"完成 {len(source_health_statuses)} 个日志源健康状态分析")

        source_dependencies = self.source_dependency_analyzer.analyze(self._events, self._sources)
        logger.info(f"发现 {len(source_dependencies)} 个日志源依赖关系")

        error_patterns = self.error_pattern_recognizer.recognize(self._events)
        logger.info(f"识别到 {len(error_patterns)} 个错误模式")

        chain_clusters = self.error_chain_clusterer.cluster(error_chains)
        logger.info(f"生成 {len(chain_clusters)} 个错误传播链聚类")

        statistics = self._calculate_statistics()
        recommendations = self._generate_recommendations(
            error_chains, cross_system_traces, impact_assessments,
            circular_dependencies, time_series_analysis
        )
        visualization_summary = self._generate_visualization_summary(error_chains, cross_system_traces)
        trend_summary = self._generate_trend_summary(time_series_analysis)
        anomaly_summary = self._generate_anomaly_summary(time_series_analysis)

        report = CorrelationReport(
            report_id=f"CORR-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            generated_at=datetime.now().isoformat(),
            sources=self._sources,
            total_events=len(self._events),
            error_chains=error_chains,
            correlations=correlations,
            cross_system_traces=cross_system_traces,
            impact_assessments=impact_assessments,
            statistics=statistics,
            recommendations=recommendations,
            visualization_summary=visualization_summary,
            time_series_analysis=time_series_analysis,
            circular_dependencies=circular_dependencies,
            root_cause_analyses=root_cause_analyses,
            trend_summary=trend_summary,
            anomaly_summary=anomaly_summary,
            source_health_statuses=source_health_statuses,
            source_dependencies=source_dependencies,
            error_patterns=error_patterns,
            chain_clusters=chain_clusters
        )

        executive_summary = self.report_generator.generate_executive_summary(report, self._events)
        report.executive_summary = executive_summary

        key_metrics = self.report_generator.generate_key_metrics(report, self._events)
        report.key_metrics = key_metrics

        chart_data = self.report_generator.generate_chart_data(report, self._events)
        report.chart_data = chart_data

        detailed_statistics = self.report_generator.generate_detailed_statistics(report, self._events)
        report.detailed_statistics = detailed_statistics

        logger.info("日志关联分析完成")
        return report

    def _calculate_statistics(self) -> Dict[str, Any]:
        level_counts: Dict[str, int] = defaultdict(int)
        system_counts: Dict[str, int] = defaultdict(int)
        hourly_distribution: Dict[str, int] = defaultdict(int)

        for event in self._events:
            level_counts[event.level] += 1
            system_counts[event.source.system] += 1
            hour_key = event.timestamp.strftime('%Y-%m-%d %H')
            hourly_distribution[hour_key] += 1

        return {
            "total_events": len(self._events),
            "events_by_level": dict(level_counts),
            "events_by_system": dict(system_counts),
            "source_count": len(self._sources),
            "time_range": {
                "start": self._events[0].timestamp.isoformat() if self._events else None,
                "end": self._events[-1].timestamp.isoformat() if self._events else None
            },
            "hourly_distribution": dict(hourly_distribution)
        }

    def _generate_recommendations(
        self,
        error_chains: List[ErrorPropagationChain],
        traces: List[CrossSystemTrace],
        impacts: List[ImpactAssessment],
        circular_deps: List[CircularDependency],
        time_series: List[TimeSeriesCorrelation]
    ) -> List[str]:
        recommendations = []

        critical_chains = [c for c in error_chains if c.severity == SeverityLevel.CRITICAL]
        if critical_chains:
            recommendations.append(f"发现 {len(critical_chains)} 条严重错误传播链，需要立即处理根因")

        high_severity_chains = [c for c in error_chains if c.severity == SeverityLevel.HIGH]
        if high_severity_chains:
            recommendations.append(f"发现 {len(high_severity_chains)} 条高严重度错误链，建议优先排查")

        error_traces = [t for t in traces if t.error_count > 0]
        if error_traces:
            recommendations.append(f"发现 {len(error_traces)} 条跨系统调用链存在错误，建议检查服务间通信")

        slow_traces = [t for t in traces if t.total_duration_seconds > 5]
        if slow_traces:
            recommendations.append(f"发现 {len(slow_traces)} 条跨系统调用耗时超过5秒，建议优化性能")

        bottleneck_traces = [t for t in traces if t.bottleneck_detected]
        if bottleneck_traces:
            bottleneck_services = set(t.bottleneck_service for t in bottleneck_traces if t.bottleneck_service)
            recommendations.append(f"检测到性能瓶颈服务: {', '.join(bottleneck_services)}")

        high_impact = [i for i in impacts if "严重" in i.business_impact or "高" in i.business_impact]
        if high_impact:
            recommendations.append(f"发现 {len(high_impact)} 个高影响事件，建议启动应急预案")

        if circular_deps:
            recommendations.append(f"检测到 {len(circular_deps)} 个循环依赖，建议重构服务架构")

        rising_trends = [ts for ts in time_series if ts.trend == "上升"]
        if rising_trends:
            recommendations.append(f"发现 {len(rising_trends)} 个上升趋势的时间序列，建议关注资源扩容")

        total_anomalies = sum(len(ts.anomalies) for ts in time_series)
        if total_anomalies > 10:
            recommendations.append(f"检测到 {total_anomalies} 个时间序列异常点，建议深入分析")

        return recommendations

    def _generate_trend_summary(self, time_series: List[TimeSeriesCorrelation]) -> Dict[str, Any]:
        if not time_series:
            return {}

        rising = [ts for ts in time_series if ts.trend == "上升"]
        falling = [ts for ts in time_series if ts.trend == "下降"]
        stable = [ts for ts in time_series if ts.trend == "稳定"]

        avg_slope = sum(ts.slope for ts in time_series) / len(time_series) if time_series else 0
        avg_r_squared = sum(ts.r_squared for ts in time_series) / len(time_series) if time_series else 0

        seasonal_count = sum(1 for ts in time_series if ts.seasonality_detected)

        return {
            "total_series": len(time_series),
            "rising_trends": len(rising),
            "falling_trends": len(falling),
            "stable_trends": len(stable),
            "average_slope": round(avg_slope, 4),
            "average_r_squared": round(avg_r_squared, 4),
            "seasonality_detected_count": seasonal_count,
            "series_with_anomalies": sum(1 for ts in time_series if ts.anomalies),
            "trend_distribution": {
                "上升": len(rising),
                "下降": len(falling),
                "稳定": len(stable)
            }
        }

    def _generate_anomaly_summary(self, time_series: List[TimeSeriesCorrelation]) -> Dict[str, Any]:
        all_anomalies = []
        for ts in time_series:
            for anomaly in ts.anomalies:
                anomaly["series_name"] = ts.series_name
                all_anomalies.append(anomaly)

        high_anomalies = [a for a in all_anomalies if a.get("z_score", 0) > 3.0]
        medium_anomalies = [a for a in all_anomalies if 2.0 < a.get("z_score", 0) <= 3.0]

        anomaly_by_type: Dict[str, int] = defaultdict(int)
        for a in all_anomalies:
            anomaly_by_type[a.get("type", "未知")] += 1

        return {
            "total_anomalies": len(all_anomalies),
            "high_severity_count": len(high_anomalies),
            "medium_severity_count": len(medium_anomalies),
            "anomaly_by_type": dict(anomaly_by_type),
            "top_anomalies": sorted(all_anomalies, key=lambda x: x.get("z_score", 0), reverse=True)[:10]
        }

    def _generate_visualization_summary(
        self,
        error_chains: List[ErrorPropagationChain],
        traces: List[CrossSystemTrace]
    ) -> Dict[str, Any]:
        chain_nodes = []
        chain_links = []
        for chain in error_chains:
            for i, event in enumerate(chain.propagation_path):
                chain_nodes.append({
                    "id": event.event_id,
                    "system": event.source.system,
                    "level": event.level,
                    "timestamp": event.timestamp.isoformat(),
                    "message": event.message[:50]
                })
                if i > 0:
                    chain_links.append({
                        "source": chain.propagation_path[i-1].event_id,
                        "target": event.event_id,
                        "type": "propagation"
                    })

        trace_data = []
        for trace in traces[:20]:
            trace_data.append({
                "trace_id": trace.trace_id,
                "systems": list(trace.systems),
                "duration": trace.total_duration_seconds,
                "error_count": trace.error_count,
                "service_calls": trace.service_calls
            })

        return {
            "error_chain_graph": {
                "nodes": chain_nodes[:100],
                "links": chain_links[:100]
            },
            "trace_timeline": trace_data
        }

    def generate_markdown_report(self, report: CorrelationReport) -> str:
        """生成 Markdown 格式的报告"""
        lines = [
            "# 日志关联分析报告",
            "",
            f"**报告ID**: {report.report_id}",
            f"**生成时间**: {report.generated_at}",
            f"**分析事件数**: {report.total_events}",
            f"**日志源数量**: {len(report.sources)}",
            "",
        ]

        if report.executive_summary:
            es = report.executive_summary
            lines.extend([
                "## 执行摘要",
                "",
                f"- **分析时段**: {es.analysis_period.get('start', 'N/A')} 至 {es.analysis_period.get('end', 'N/A')}",
                f"- **整体健康分数**: {es.overall_health_score:.1f}/100",
                f"- **风险等级**: {es.risk_level}",
                f"- **趋势指标**: {es.trend_indicator}",
                f"- **严重问题数**: {es.critical_issues_count}",
                f"- **高优先级问题数**: {es.high_issues_count}",
                "",
                "### 关键发现",
                "",
            ])
            for finding in es.key_findings:
                lines.append(f"- {finding}")
            lines.append("")

            if es.immediate_actions:
                lines.extend([
                    "### 立即行动建议",
                    "",
                ])
                for action in es.immediate_actions:
                    lines.append(f"- {action}")
                lines.append("")

        if report.key_metrics:
            km = report.key_metrics
            lines.extend([
                "## 关键指标",
                "",
                f"| 指标 | 值 |",
                f"|------|------|",
                f"| 错误率 | {km.error_rate:.2%} |",
                f"| 警告率 | {km.warning_rate:.2%} |",
                f"| 平均响应时间 | {km.avg_response_time:.2f}s |",
                f"| 错误链平均长度 | {km.error_chain_avg_length:.1f} |",
                f"| 跨系统调用数 | {km.cross_system_call_count} |",
                f"| 瓶颈数量 | {km.bottleneck_count} |",
                f"| 循环依赖数 | {km.circular_dependency_count} |",
                f"| 异常点数 | {km.anomaly_count} |",
                f"| 健康分数 | {km.health_score:.1f} |",
                f"| MTTR 估算 | {km.mttr_estimate:.1f} 分钟 |",
                "",
            ])

        lines.extend([
            "## 摘要",
            "",
            f"本报告分析了来自 {len(report.sources)} 个日志源的 {report.total_events} 条日志事件。",
            f"发现 {len(report.error_chains)} 条错误传播链，{len(report.cross_system_traces)} 条跨系统追踪。",
            "",
            "## 日志源",
            "",
            "| 名称 | 系统 | 路径 |",
            "|------|------|------|",
        ])

        for source in report.sources:
            lines.append(f"| {source.name} | {source.system} | {source.path} |")

        if report.source_health_statuses:
            lines.extend([
                "",
                "## 日志源健康状态",
                "",
                "| 日志源 | 健康分数 | 状态 | 错误数 | 警告数 |",
                "|--------|----------|------|--------|--------|",
            ])
            for status in report.source_health_statuses:
                lines.append(f"| {status.source_name} | {status.health_score:.1f} | {status.status} | {status.error_count} | {status.warning_count} |")

        if report.source_dependencies:
            lines.extend([
                "",
                "## 日志源依赖关系",
                "",
                "| 源 | 依赖 | 类型 | 强度 | 相关错误 |",
                "|----|------|------|------|----------|",
            ])
            for dep in report.source_dependencies[:10]:
                lines.append(f"| {dep.source_id} | {', '.join(dep.depends_on)} | {dep.dependency_type} | {dep.strength:.2f} | {dep.correlated_errors} |")

        if report.error_patterns:
            lines.extend([
                "",
                "## 错误模式",
                "",
            ])
            for pattern in report.error_patterns[:10]:
                lines.extend([
                    f"### {pattern.pattern_type} ({pattern.severity.value})",
                    "",
                    f"- **出现次数**: {pattern.occurrence_count}",
                    f"- **影响系统**: {', '.join(pattern.affected_systems[:5])}",
                    f"- **趋势**: {pattern.trend}",
                    f"- **建议修复**: {pattern.suggested_fix}",
                    "",
                ])

        if report.chain_clusters:
            lines.extend([
                "",
                "## 错误传播链聚类",
                "",
            ])
            for cluster in report.chain_clusters:
                lines.extend([
                    f"### {cluster.cluster_id} ({cluster.cluster_severity.value})",
                    "",
                    f"- **包含链数**: {len(cluster.chains)}",
                    f"- **共同系统**: {', '.join(list(cluster.common_systems)[:5])}",
                    f"- **描述**: {cluster.cluster_description}",
                    "",
                ])

        if report.error_chains:
            lines.extend([
                "",
                "## 错误传播链",
                "",
            ])

            for chain in sorted(report.error_chains, key=lambda x: x.severity.value):
                lines.extend([
                    f"### {chain.chain_id} ({chain.severity.value})",
                    "",
                    f"- **根因**: {chain.root_cause.message[:100]}",
                    f"- **影响系统**: {', '.join(chain.affected_systems)}",
                    f"- **传播路径长度**: {len(chain.propagation_path)}",
                    f"- **持续时间**: {chain.total_duration_seconds:.2f}秒",
                    f"- **置信度**: {chain.confidence.value}",
                    "",
                ])

                if chain.suggested_actions:
                    lines.append("**建议操作**:")
                    for action in chain.suggested_actions[:3]:
                        lines.append(f"  - {action}")
                    lines.append("")

        if report.cross_system_traces:
            lines.extend([
                "",
                "## 跨系统追踪",
                "",
                "| 追踪ID | 系统 | 事件数 | 错误数 | 耗时 | 瓶颈 |",
                "|--------|------|--------|--------|------|------|",
            ])

            for trace in report.cross_system_traces[:20]:
                systems = ', '.join(sorted(trace.systems))
                bottleneck = trace.bottleneck_service or "-"
                lines.append(f"| {trace.trace_id[:20]}... | {systems} | {len(trace.events)} | {trace.error_count} | {trace.total_duration_seconds:.2f}s | {bottleneck} |")

        if report.correlations:
            lines.extend([
                "",
                "## 关联分析",
                "",
            ])

            for corr in report.correlations[:10]:
                lines.append(f"- **{corr.correlation_type.value}**: {corr.description}")

        if report.impact_assessments:
            lines.extend([
                "",
                "## 影响评估",
                "",
            ])

            for impact in report.impact_assessments:
                lines.extend([
                    f"### {impact.assessment_id}",
                    "",
                    f"- **影响系统**: {', '.join(impact.affected_systems)}",
                    f"- **影响用户数**: {impact.affected_users}",
                    f"- **业务影响**: {impact.business_impact}",
                    f"- **预估停机时间**: {impact.estimated_downtime_minutes:.1f} 分钟",
                    "",
                ])

        if report.recommendations:
            lines.extend([
                "",
                "## 建议",
                "",
            ])

            for i, rec in enumerate(report.recommendations, 1):
                lines.append(f"{i}. {rec}")

        return "\n".join(lines)

    def generate_html_report(self, report: CorrelationReport) -> str:
        """生成 HTML 格式的报告"""
        html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <title>日志关联分析报告 - {report.report_id}</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; margin: 20px; background: #f5f5f5; }}
        .container {{ max-width: 1400px; margin: 0 auto; background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        h1 {{ color: #333; border-bottom: 2px solid #007bff; padding-bottom: 10px; }}
        h2 {{ color: #555; margin-top: 30px; border-bottom: 1px solid #eee; padding-bottom: 5px; }}
        h3 {{ color: #666; margin-top: 20px; }}
        .summary {{ background: #e7f3ff; padding: 15px; border-radius: 5px; margin: 20px 0; }}
        .executive-summary {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; border-radius: 8px; margin: 20px 0; }}
        .executive-summary h2 {{ color: white; border-bottom: 1px solid rgba(255,255,255,0.3); }}
        .executive-summary .metric {{ display: inline-block; margin: 10px 20px 10px 0; }}
        .executive-summary .metric-value {{ font-size: 24px; font-weight: bold; }}
        .executive-summary .metric-label {{ font-size: 12px; opacity: 0.8; }}
        .key-metrics {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin: 20px 0; }}
        .metric-card {{ background: #f8f9fa; padding: 15px; border-radius: 5px; text-align: center; border-left: 4px solid #007bff; }}
        .metric-card.warning {{ border-left-color: #ffc107; }}
        .metric-card.danger {{ border-left-color: #dc3545; }}
        .metric-card.success {{ border-left-color: #28a745; }}
        .metric-card .value {{ font-size: 28px; font-weight: bold; color: #333; }}
        .metric-card .label {{ font-size: 12px; color: #666; margin-top: 5px; }}
        table {{ width: 100%; border-collapse: collapse; margin: 15px 0; }}
        th, td {{ padding: 10px; text-align: left; border-bottom: 1px solid #ddd; }}
        th {{ background: #f8f9fa; font-weight: 600; }}
        tr:hover {{ background: #f5f5f5; }}
        .severity-critical {{ background: #f8d7da; border-left: 4px solid #dc3545; padding: 10px; margin: 10px 0; }}
        .severity-high {{ background: #fff3cd; border-left: 4px solid #ffc107; padding: 10px; margin: 10px 0; }}
        .severity-medium {{ background: #e2e3e5; border-left: 4px solid #6c757d; padding: 10px; margin: 10px 0; }}
        .severity-low {{ background: #d4edda; border-left: 4px solid #28a745; padding: 10px; margin: 10px 0; }}
        .impact-high {{ background: #fff3cd; border-left: 4px solid #fd7e14; padding: 10px; margin: 10px 0; }}
        .recommendations {{ background: #d4edda; padding: 15px; border-radius: 5px; margin-top: 20px; }}
        .meta {{ color: #666; font-size: 0.9em; }}
        .bottleneck {{ color: #dc3545; font-weight: bold; }}
        .health-good {{ color: #28a745; }}
        .health-warning {{ color: #ffc107; }}
        .health-critical {{ color: #dc3545; }}
        .pattern-card {{ background: #fff; border: 1px solid #ddd; border-radius: 5px; padding: 15px; margin: 10px 0; }}
        .pattern-card .header {{ display: flex; justify-content: space-between; align-items: center; }}
        .pattern-card .badge {{ padding: 3px 8px; border-radius: 3px; font-size: 12px; }}
        .cluster-card {{ background: #f8f9fa; border: 1px solid #ddd; border-radius: 5px; padding: 15px; margin: 10px 0; }}
        .findings-list {{ list-style: none; padding: 0; }}
        .findings-list li {{ padding: 8px 0; border-bottom: 1px solid #eee; }}
        .findings-list li:before {{ content: "▸ "; color: #007bff; }}
        .actions-list {{ list-style: none; padding: 0; }}
        .actions-list li {{ padding: 10px; margin: 5px 0; background: #fff3cd; border-radius: 5px; }}
        .actions-list li:before {{ content: "⚡ "; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>日志关联分析报告</h1>
        <div class="meta">
            <p>报告ID: {report.report_id} | 生成时间: {report.generated_at}</p>
            <p>分析事件数: {report.total_events} | 日志源数量: {len(report.sources)}</p>
        </div>
"""

        if report.executive_summary:
            es = report.executive_summary
            risk_class = "danger" if es.risk_level == "高风险" else "warning" if es.risk_level == "中风险" else "success"
            html += f"""
        <div class="executive-summary">
            <h2>执行摘要</h2>
            <div class="metric">
                <div class="metric-value">{es.overall_health_score:.0f}</div>
                <div class="metric-label">健康分数</div>
            </div>
            <div class="metric">
                <div class="metric-value">{es.risk_level}</div>
                <div class="metric-label">风险等级</div>
            </div>
            <div class="metric">
                <div class="metric-value">{es.trend_indicator}</div>
                <div class="metric-label">趋势指标</div>
            </div>
            <div class="metric">
                <div class="metric-value">{es.critical_issues_count}</div>
                <div class="metric-label">严重问题</div>
            </div>
            <div class="metric">
                <div class="metric-value">{es.high_issues_count}</div>
                <div class="metric-label">高优先级问题</div>
            </div>
        </div>
"""
            if es.key_findings:
                html += """
        <div class="summary">
            <h3>关键发现</h3>
            <ul class="findings-list">
"""
                for finding in es.key_findings:
                    html += f"                <li>{finding}</li>\n"
                html += """            </ul>
        </div>
"""
            if es.immediate_actions:
                html += """
        <div class="summary" style="background: #fff3cd;">
            <h3>立即行动建议</h3>
            <ul class="actions-list">
"""
                for action in es.immediate_actions:
                    html += f"                <li>{action}</li>\n"
                html += """            </ul>
        </div>
"""

        if report.key_metrics:
            km = report.key_metrics
            html += """
        <h2>关键指标</h2>
        <div class="key-metrics">
"""
            metrics = [
                ("错误率", f"{km.error_rate:.2%}", "danger" if km.error_rate > 0.05 else "warning" if km.error_rate > 0.01 else "success"),
                ("警告率", f"{km.warning_rate:.2%}", "warning" if km.warning_rate > 0.1 else "success"),
                ("平均响应时间", f"{km.avg_response_time:.2f}s", "danger" if km.avg_response_time > 5 else "warning" if km.avg_response_time > 2 else "success"),
                ("健康分数", f"{km.health_score:.0f}", "danger" if km.health_score < 60 else "warning" if km.health_score < 80 else "success"),
                ("跨系统调用", str(km.cross_system_call_count), ""),
                ("瓶颈数量", str(km.bottleneck_count), "warning" if km.bottleneck_count > 0 else "success"),
                ("循环依赖", str(km.circular_dependency_count), "danger" if km.circular_dependency_count > 0 else "success"),
                ("异常点数", str(km.anomaly_count), "warning" if km.anomaly_count > 10 else ""),
                ("MTTR 估算", f"{km.mttr_estimate:.1f}分钟", "danger" if km.mttr_estimate > 30 else "warning" if km.mttr_estimate > 10 else "success"),
            ]
            for label, value, card_class in metrics:
                html += f"""            <div class="metric-card {card_class}">
                <div class="value">{value}</div>
                <div class="label">{label}</div>
            </div>
"""
            html += """        </div>
"""

        html += f"""
        <div class="summary">
            <h2>摘要</h2>
            <p>本报告分析了来自 {len(report.sources)} 个日志源的 {report.total_events} 条日志事件。</p>
            <p>发现 {len(report.error_chains)} 条错误传播链，{len(report.cross_system_traces)} 条跨系统追踪。</p>
        </div>

        <h2>日志源</h2>
        <table>
            <tr><th>名称</th><th>系统</th><th>路径</th></tr>
"""
        for source in report.sources:
            html += f"            <tr><td>{source.name}</td><td>{source.system}</td><td>{source.path}</td></tr>\n"
        html += """        </table>
"""

        if report.source_health_statuses:
            html += """        <h2>日志源健康状态</h2>
        <table>
            <tr><th>日志源</th><th>健康分数</th><th>状态</th><th>错误数</th><th>警告数</th><th>问题</th></tr>
"""
            for status in report.source_health_statuses:
                health_class = "health-good" if status.health_score >= 80 else "health-warning" if status.health_score >= 60 else "health-critical"
                issues_str = "; ".join(status.issues[:2]) if status.issues else "-"
                html += f"            <tr><td>{status.source_name}</td><td class='{health_class}'>{status.health_score:.1f}</td><td>{status.status}</td><td>{status.error_count}</td><td>{status.warning_count}</td><td>{issues_str}</td></tr>\n"
            html += """        </table>
"""

        if report.source_dependencies:
            html += """        <h2>日志源依赖关系</h2>
        <table>
            <tr><th>源</th><th>依赖</th><th>类型</th><th>强度</th><th>相关错误</th></tr>
"""
            for dep in report.source_dependencies[:15]:
                html += f"            <tr><td>{dep.source_id}</td><td>{', '.join(dep.depends_on)}</td><td>{dep.dependency_type}</td><td>{dep.strength:.2f}</td><td>{dep.correlated_errors}</td></tr>\n"
            html += """        </table>
"""

        if report.error_patterns:
            html += """        <h2>错误模式</h2>
"""
            for pattern in report.error_patterns[:10]:
                severity_class = f"severity-{pattern.severity.value}"
                html += f"""        <div class="pattern-card {severity_class}">
            <div class="header">
                <strong>{pattern.pattern_type}</strong>
                <span class="badge severity-{pattern.severity.value}">{pattern.severity.value}</span>
            </div>
            <p class="meta">出现 {pattern.occurrence_count} 次 | 趋势: {pattern.trend} | 影响系统: {', '.join(pattern.affected_systems[:3])}</p>
            <p><strong>建议修复:</strong> {pattern.suggested_fix}</p>
        </div>
"""

        if report.chain_clusters:
            html += """        <h2>错误传播链聚类</h2>
"""
            for cluster in report.chain_clusters:
                html += f"""        <div class="cluster-card severity-{cluster.cluster_severity.value}">
            <strong>{cluster.cluster_id}</strong> ({cluster.cluster_severity.value})<br>
            <span class="meta">包含 {len(cluster.chains)} 条链 | 共同系统: {', '.join(list(cluster.common_systems)[:5])}</span><br>
            <span class="meta">{cluster.cluster_description}</span>
        </div>
"""

        if report.error_chains:
            html += """        <h2>错误传播链</h2>
"""
            for chain in sorted(report.error_chains, key=lambda x: ['critical', 'high', 'medium', 'low'].index(x.severity.value)):
                html += f"""        <div class="severity-{chain.severity.value}">
            <strong>{chain.chain_id}</strong> ({chain.severity.value}) [{chain.confidence.value}]<br>
            <span class="meta">根因: {chain.root_cause.message[:100]}</span><br>
            <span class="meta">影响系统: {', '.join(chain.affected_systems)} | 传播路径长度: {len(chain.propagation_path)} | 持续时间: {chain.total_duration_seconds:.2f}秒</span>
        </div>
"""

        if report.cross_system_traces:
            html += """        <h2>跨系统追踪</h2>
        <table>
            <tr><th>追踪ID</th><th>系统</th><th>事件数</th><th>错误数</th><th>耗时</th><th>瓶颈</th></tr>
"""
            for trace in report.cross_system_traces[:20]:
                systems = ', '.join(sorted(trace.systems))
                bottleneck_class = "bottleneck" if trace.bottleneck_detected else ""
                bottleneck_text = f'<span class="{bottleneck_class}">{trace.bottleneck_service or "-"}</span>'
                html += f"            <tr><td>{trace.trace_id[:30]}</td><td>{systems}</td><td>{len(trace.events)}</td><td>{trace.error_count}</td><td>{trace.total_duration_seconds:.2f}s</td><td>{bottleneck_text}</td></tr>\n"
            html += """        </table>
"""

        if report.impact_assessments:
            html += """        <h2>影响评估</h2>
"""
            for impact in report.impact_assessments:
                impact_class = "impact-high" if "严重" in impact.business_impact or "高" in impact.business_impact else ""
                html += f"""        <div class="{impact_class}">
            <strong>{impact.assessment_id}</strong><br>
            <span class="meta">影响系统: {', '.join(impact.affected_systems)} | 影响用户: {impact.affected_users}</span><br>
            <span class="meta">业务影响: {impact.business_impact} | 预估停机: {impact.estimated_downtime_minutes:.1f} 分钟</span>
        </div>
"""

        if report.recommendations:
            html += """        <div class="recommendations">
            <h2>建议</h2>
            <ol>
"""
            for rec in report.recommendations:
                html += f"                <li>{rec}</li>\n"
            html += """            </ol>
        </div>
"""

        html += """    </div>
</body>
</html>
"""
        return html


def main():
    parser = argparse.ArgumentParser(
        description="增强日志关联分析器 - 实现多源日志关联分析和错误传播链识别",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 分析单个日志文件
  python log_correlation_analyzer.py --source app.log --system MyApp

  # 分析多个日志源
  python log_correlation_analyzer.py --sources source1.json

  # 使用配置文件
  python log_correlation_analyzer.py --config config.json --report report.html
        """
    )

    parser.add_argument(
        "--source",
        type=str,
        action="append",
        help="日志文件或目录路径"
    )

    parser.add_argument(
        "--system",
        type=str,
        default="default",
        help="日志所属系统名称"
    )

    parser.add_argument(
        "--sources",
        type=str,
        help="日志源配置文件 (JSON格式)"
    )

    parser.add_argument(
        "--config",
        type=str,
        help="分析配置文件"
    )

    parser.add_argument(
        "--report",
        type=str,
        default="correlation_report.html",
        help="报告输出路径"
    )

    parser.add_argument(
        "--cross-system",
        action="store_true",
        help="启用跨系统追踪分析"
    )

    parser.add_argument(
        "--verbose",
        action="store_true",
        help="详细输出"
    )

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    config = {}
    if args.config:
        with open(args.config, 'r', encoding='utf-8') as f:
            config = json.load(f)

    correlator = EnhancedLogCorrelator(config)

    if args.sources:
        with open(args.sources, 'r', encoding='utf-8') as f:
            sources_config = json.load(f)
            for src in sources_config.get('sources', []):
                source = LogSource(
                    source_id=src.get('id', src.get('name', '')),
                    name=src.get('name', ''),
                    path=src.get('path', ''),
                    system=src.get('system', 'default'),
                    log_format=src.get('format', 'auto'),
                    tags=src.get('tags', {}),
                    priority=src.get('priority', 0)
                )
                correlator.add_source(source)
    elif args.source:
        for i, path in enumerate(args.source):
            source = LogSource(
                source_id=f"source_{i}",
                name=f"Source {i}",
                path=path,
                system=args.system,
                log_format="auto"
            )
            correlator.add_source(source)
    else:
        parser.print_help()
        print("\n错误: 请指定 --source 或 --sources")
        sys.exit(1)

    correlator.load_events()
    report = correlator.correlate()

    print("\n" + "=" * 60)
    print("日志关联分析报告")
    print("=" * 60)
    print(f"报告ID: {report.report_id}")
    print(f"分析事件数: {report.total_events}")
    print(f"错误传播链: {len(report.error_chains)}")
    print(f"跨系统追踪: {len(report.cross_system_traces)}")
    print(f"关联模式: {len(report.correlations)}")
    print(f"影响评估: {len(report.impact_assessments)}")

    if report.executive_summary:
        es = report.executive_summary
        print(f"\n执行摘要:")
        print(f"  健康分数: {es.overall_health_score:.1f}/100")
        print(f"  风险等级: {es.risk_level}")
        print(f"  趋势指标: {es.trend_indicator}")
        print(f"  严重问题: {es.critical_issues_count} | 高优先级: {es.high_issues_count}")

    if report.key_metrics:
        km = report.key_metrics
        print(f"\n关键指标:")
        print(f"  错误率: {km.error_rate:.2%} | 警告率: {km.warning_rate:.2%}")
        print(f"  健康分数: {km.health_score:.1f} | MTTR估算: {km.mttr_estimate:.1f}分钟")

    if report.source_health_statuses:
        print(f"\n日志源健康状态:")
        for status in report.source_health_statuses[:5]:
            print(f"  [{status.status}] {status.source_name}: {status.health_score:.1f}")

    if report.error_patterns:
        print(f"\n错误模式 ({len(report.error_patterns)} 个):")
        for pattern in report.error_patterns[:3]:
            print(f"  [{pattern.severity.value}] {pattern.pattern_type}: {pattern.occurrence_count} 次")

    if report.error_chains:
        print("\n错误传播链摘要:")
        for chain in report.error_chains[:5]:
            print(f"  [{chain.severity.value}] {chain.chain_id}: {chain.description[:60]}...")

    if report.cross_system_traces:
        print("\n跨系统追踪摘要:")
        for trace in report.cross_system_traces[:5]:
            bottleneck = f" (瓶颈: {trace.bottleneck_service})" if trace.bottleneck_detected else ""
            print(f"  {trace.trace_id[:20]}... | {len(trace.systems)} 系统 | {trace.total_duration_seconds:.2f}s{bottleneck}")

    report_path = Path(args.report)
    report_path.parent.mkdir(parents=True, exist_ok=True)

    if report_path.suffix.lower() == '.json':
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report.to_dict(), f, ensure_ascii=False, indent=2)
    elif report_path.suffix.lower() == '.html':
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(correlator.generate_html_report(report))
    else:
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(correlator.generate_markdown_report(report))

    print(f"\n报告已保存: {report_path}")

    return 0


if __name__ == "__main__":
    sys.exit(main())


class MultiSourceLogCorrelator:
    """多源日志关联器 - 实现应用日志、系统日志、数据库日志的关联分析
    
    支持的日志类型：
    - 应用日志：业务逻辑、API调用、用户操作
    - 系统日志：操作系统、网络、硬件事件
    - 数据库日志：查询、事务、锁、性能指标
    """
    
    LOG_SOURCE_TYPES = {
        'application': {
            'patterns': [
                r'\[APP\]', r'application', r'app\.log', r'service',
                r'controller', r'handler', r'endpoint', r'api'
            ],
            'priority': 1
        },
        'system': {
            'patterns': [
                r'\[SYSTEM\]', r'syslog', r'kernel', r'system',
                r'network', r'cpu', r'memory', r'disk'
            ],
            'priority': 2
        },
        'database': {
            'patterns': [
                r'\[DB\]', r'database', r'mysql', r'postgres',
                r'oracle', r'mongodb', r'redis', r'sql'
            ],
            'priority': 3
        },
        'web_server': {
            'patterns': [
                r'\[WEB\]', r'nginx', r'apache', r'iis',
                r'access\.log', r'error\.log'
            ],
            'priority': 4
        },
        'cache': {
            'patterns': [
                r'\[CACHE\]', r'redis', r'memcached', r'cache'
            ],
            'priority': 5
        },
        'message_queue': {
            'patterns': [
                r'\[MQ\]', r'kafka', r'rabbitmq', r'activemq',
                r'queue', r'message'
            ],
            'priority': 6
        }
    }
    
    CORRELATION_RULES = [
        {
            'name': 'app_db_timeout',
            'description': '应用超时与数据库慢查询关联',
            'source_types': ['application', 'database'],
            'app_pattern': r'timeout|timed?\s*out',
            'db_pattern': r'slow\s+query|query\s+time|execution\s+time',
            'time_window_seconds': 60,
            'confidence': 0.85
        },
        {
            'name': 'app_system_resource',
            'description': '应用错误与系统资源耗尽关联',
            'source_types': ['application', 'system'],
            'app_pattern': r'out\s+of\s+memory|memory\s+error|cannot\s+allocate',
            'system_pattern': r'memory\s+(exhausted|low|critical)|OOM|out\s+of\s+memory',
            'time_window_seconds': 30,
            'confidence': 0.90
        },
        {
            'name': 'db_system_disk',
            'description': '数据库错误与系统磁盘问题关联',
            'source_types': ['database', 'system'],
            'db_pattern': r'disk\s+(full|space|error)|write\s+failed',
            'system_pattern': r'disk\s+(full|space|error)|no\s+space\s+left',
            'time_window_seconds': 120,
            'confidence': 0.95
        },
        {
            'name': 'app_cache_miss',
            'description': '应用性能问题与缓存失效关联',
            'source_types': ['application', 'cache'],
            'app_pattern': r'slow\s+response|performance|latency',
            'cache_pattern': r'cache\s+(miss|fail|error)|connection\s+refused',
            'time_window_seconds': 60,
            'confidence': 0.75
        },
        {
            'name': 'app_mq_backlog',
            'description': '应用延迟与消息队列积压关联',
            'source_types': ['application', 'message_queue'],
            'app_pattern': r'delay|backlog|processing\s+slow',
            'mq_pattern': r'queue\s+(depth|backlog|size)|consumer\s+lag',
            'time_window_seconds': 120,
            'confidence': 0.80
        },
        {
            'name': 'web_app_error',
            'description': 'Web服务器错误与应用异常关联',
            'source_types': ['web_server', 'application'],
            'web_pattern': r'5\d{2}|internal\s+server\s+error|upstream\s+error',
            'app_pattern': r'exception|error|failed',
            'time_window_seconds': 10,
            'confidence': 0.85
        }
    ]
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self._compiled_rules = self._compile_rules()
        self._source_type_patterns = self._compile_source_type_patterns()
    
    def _compile_rules(self) -> List[Dict[str, Any]]:
        """编译关联规则"""
        compiled = []
        for rule in self.CORRELATION_RULES:
            compiled_rule = rule.copy()
            primary_pattern = rule.get('app_pattern') or rule.get('db_pattern') or rule.get('web_pattern') or ''
            compiled_rule['app_pattern_re'] = re.compile(primary_pattern, re.IGNORECASE) if primary_pattern else None
            secondary_pattern = rule.get('db_pattern') or rule.get('system_pattern') or rule.get('cache_pattern') or rule.get('mq_pattern') or rule.get('app_pattern') or ''
            compiled_rule['db_pattern_re'] = re.compile(secondary_pattern, re.IGNORECASE) if secondary_pattern else None
            compiled.append(compiled_rule)
        return compiled
    
    def _compile_source_type_patterns(self) -> Dict[str, List[re.Pattern]]:
        """编译日志源类型模式"""
        compiled = {}
        for source_type, info in self.LOG_SOURCE_TYPES.items():
            compiled[source_type] = [re.compile(p, re.IGNORECASE) for p in info['patterns']]
        return compiled
    
    def classify_source(self, source: LogSource) -> str:
        """分类日志源类型"""
        source_text = f"{source.name} {source.path} {source.system}".lower()
        
        for source_type, patterns in self._source_type_patterns.items():
            for pattern in patterns:
                if pattern.search(source_text):
                    return source_type
        
        return 'application'
    
    def correlate_multi_source(
        self,
        events: List[LogEvent],
        sources: List[LogSource]
    ) -> List[Dict[str, Any]]:
        """执行多源日志关联分析"""
        source_types = {s.source_id: self.classify_source(s) for s in sources}
        
        events_by_type: Dict[str, List[LogEvent]] = defaultdict(list)
        for event in events:
            source_type = source_types.get(event.source.source_id, 'application')
            events_by_type[source_type].append(event)
        
        correlations = []
        
        for rule in self._compiled_rules:
            rule_correlations = self._apply_correlation_rule(rule, events_by_type)
            correlations.extend(rule_correlations)
        
        return correlations
    
    def _apply_correlation_rule(
        self,
        rule: Dict[str, Any],
        events_by_type: Dict[str, List[LogEvent]]
    ) -> List[Dict[str, Any]]:
        """应用关联规则"""
        correlations = []
        
        source_types = rule['source_types']
        if len(source_types) < 2:
            return correlations
        
        primary_type = source_types[0]
        secondary_type = source_types[1]
        
        primary_events = events_by_type.get(primary_type, [])
        secondary_events = events_by_type.get(secondary_type, [])
        
        if not primary_events or not secondary_events:
            return correlations
        
        primary_pattern = rule['app_pattern_re']
        secondary_pattern = rule['db_pattern_re']
        time_window = timedelta(seconds=rule['time_window_seconds'])
        
        matched_primary = [e for e in primary_events if primary_pattern.search(e.message)]
        matched_secondary = [e for e in secondary_events if secondary_pattern.search(e.message)]
        
        for primary_event in matched_primary:
            for secondary_event in matched_secondary:
                time_diff = abs((primary_event.timestamp - secondary_event.timestamp).total_seconds())
                
                if time_diff <= rule['time_window_seconds']:
                    correlations.append({
                        'rule_name': rule['name'],
                        'description': rule['description'],
                        'primary_event': {
                            'event_id': primary_event.event_id,
                            'timestamp': primary_event.timestamp.isoformat(),
                            'message': primary_event.message[:100],
                            'source_type': primary_type
                        },
                        'secondary_event': {
                            'event_id': secondary_event.event_id,
                            'timestamp': secondary_event.timestamp.isoformat(),
                            'message': secondary_event.message[:100],
                            'source_type': secondary_type
                        },
                        'time_diff_seconds': time_diff,
                        'confidence': rule['confidence'],
                        'correlation_type': 'multi_source'
                    })
        
        return correlations


class ErrorPropagationChainAnalyzer:
    """错误传播链深度分析器 - 识别复杂的错误传播模式
    
    功能：
    - 识别直接传播链
    - 识别间接传播链
    - 识别并行传播链
    - 识别循环传播链
    """
    
    PROPAGATION_INDICATORS = [
        (r'caused\s+by[:\s]*(.+?)(?:\n|$)', 'causal'),
        (r'due\s+to[:\s]*(.+?)(?:\n|$)', 'causal'),
        (r'because\s+of[:\s]*(.+?)(?:\n|$)', 'causal'),
        (r'triggered[:\s]*(.+?)(?:\n|$)', 'trigger'),
        (r'following\s+error[:\s]*(.+?)(?:\n|$)', 'sequence'),
        (r'after\s+error[:\s]*(.+?)(?:\n|$)', 'sequence'),
        (r'while\s+processing[:\s]*(.+?)(?:\n|$)', 'context'),
        (r'failed\s+to[:\s]*(.+?)(?:\n|$)', 'action'),
        (r'unable\s+to[:\s]*(.+?)(?:\n|$)', 'action'),
        (r'cannot[:\s]*(.+?)(?:\n|$)', 'action'),
    ]
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self._compiled_indicators = [
            (re.compile(p, re.IGNORECASE | re.MULTILINE), t)
            for p, t in self.PROPAGATION_INDICATORS
        ]
    
    def analyze_propagation_patterns(
        self,
        events: List[LogEvent]
    ) -> Dict[str, Any]:
        """分析错误传播模式"""
        error_events = [e for e in events if e.level in ['ERROR', 'CRITICAL', 'FATAL', 'WARN', 'WARNING']]
        
        direct_chains = self._find_direct_chains(error_events)
        indirect_chains = self._find_indirect_chains(error_events)
        parallel_chains = self._find_parallel_chains(error_events)
        circular_chains = self._find_circular_chains(error_events)
        
        return {
            'direct_propagation_chains': direct_chains,
            'indirect_propagation_chains': indirect_chains,
            'parallel_propagation_chains': parallel_chains,
            'circular_propagation_chains': circular_chains,
            'summary': {
                'total_chains': len(direct_chains) + len(indirect_chains) + len(parallel_chains) + len(circular_chains),
                'direct_count': len(direct_chains),
                'indirect_count': len(indirect_chains),
                'parallel_count': len(parallel_chains),
                'circular_count': len(circular_chains)
            }
        }
    
    def _find_direct_chains(self, events: List[LogEvent]) -> List[Dict[str, Any]]:
        """查找直接传播链"""
        chains = []
        
        for event in events:
            for pattern, indicator_type in self._compiled_indicators:
                matches = pattern.findall(event.message)
                for match in matches:
                    related_events = self._find_related_events(event, match, events)
                    if related_events:
                        chains.append({
                            'chain_type': 'direct',
                            'indicator_type': indicator_type,
                            'source_event': {
                                'event_id': event.event_id,
                                'timestamp': event.timestamp.isoformat(),
                                'message': event.message[:100]
                            },
                            'related_events': [
                                {
                                    'event_id': e.event_id,
                                    'timestamp': e.timestamp.isoformat(),
                                    'message': e.message[:100]
                                }
                                for e in related_events[:5]
                            ],
                            'propagation_detail': match[:100]
                        })
        
        return chains
    
    def _find_indirect_chains(self, events: List[LogEvent]) -> List[Dict[str, Any]]:
        """查找间接传播链（通过时间关联）"""
        chains = []
        
        sorted_events = sorted(events, key=lambda x: x.timestamp)
        
        for i, event in enumerate(sorted_events):
            if event.level not in ['ERROR', 'CRITICAL', 'FATAL']:
                continue
            
            window_events = [
                e for e in sorted_events[i+1:i+10]
                if (e.timestamp - event.timestamp).total_seconds() <= 300
            ]
            
            if len(window_events) >= 2:
                same_system_events = [
                    e for e in window_events
                    if e.source.system == event.source.system
                ]
                
                if same_system_events:
                    chains.append({
                        'chain_type': 'indirect',
                        'root_event': {
                            'event_id': event.event_id,
                            'timestamp': event.timestamp.isoformat(),
                            'system': event.source.system
                        },
                        'propagated_events': [
                            {
                                'event_id': e.event_id,
                                'timestamp': e.timestamp.isoformat(),
                                'level': e.level
                            }
                            for e in same_system_events[:5]
                        ],
                        'propagation_time_seconds': sum(
                            (e.timestamp - event.timestamp).total_seconds()
                            for e in same_system_events
                        ) / len(same_system_events)
                    })
        
        return chains[:50]
    
    def _find_parallel_chains(self, events: List[LogEvent]) -> List[Dict[str, Any]]:
        """查找并行传播链（同一时间多个系统出错）"""
        chains = []
        
        time_groups: Dict[str, List[LogEvent]] = defaultdict(list)
        for event in events:
            minute_key = event.timestamp.strftime('%Y-%m-%d %H:%M')
            time_groups[minute_key].append(event)
        
        for minute, group_events in time_groups.items():
            systems = set(e.source.system for e in group_events)
            if len(systems) >= 3:
                chains.append({
                    'chain_type': 'parallel',
                    'timestamp': minute,
                    'affected_systems': list(systems),
                    'event_count': len(group_events),
                    'severity_distribution': dict(Counter(e.level for e in group_events)),
                    'events_by_system': {
                        system: [
                            {
                                'event_id': e.event_id,
                                'message': e.message[:50]
                            }
                            for e in group_events
                            if e.source.system == system
                        ][:3]
                        for system in systems
                    }
                })
        
        return sorted(chains, key=lambda x: x['event_count'], reverse=True)[:20]
    
    def _find_circular_chains(self, events: List[LogEvent]) -> List[Dict[str, Any]]:
        """查找循环传播链"""
        chains = []
        
        system_errors: Dict[str, List[LogEvent]] = defaultdict(list)
        for event in events:
            if event.level in ['ERROR', 'CRITICAL', 'FATAL']:
                system_errors[event.source.system].append(event)
        
        systems = list(system_errors.keys())
        for i, system_a in enumerate(systems):
            for system_b in systems[i+1:]:
                errors_a = system_errors[system_a]
                errors_b = system_errors[system_b]
                
                cross_references = self._find_cross_references(errors_a, errors_b)
                if cross_references >= 3:
                    chains.append({
                        'chain_type': 'circular',
                        'systems': [system_a, system_b],
                        'cross_reference_count': cross_references,
                        'first_system_errors': len(errors_a),
                        'second_system_errors': len(errors_b),
                        'description': f'{system_a} 和 {system_b} 之间存在循环错误传播'
                    })
        
        return chains
    
    def _find_related_events(
        self,
        source_event: LogEvent,
        detail: str,
        events: List[LogEvent]
    ) -> List[LogEvent]:
        """查找相关事件"""
        keywords = set(re.findall(r'\b\w{4,}\b', detail.lower()))
        
        related = []
        for event in events:
            if event.event_id == source_event.event_id:
                continue
            
            event_keywords = set(re.findall(r'\b\w{4,}\b', event.message.lower()))
            overlap = len(keywords & event_keywords)
            
            if overlap >= 2:
                related.append(event)
        
        return sorted(related, key=lambda x: abs((x.timestamp - source_event.timestamp).total_seconds()))[:5]
    
    def _find_cross_references(
        self,
        errors_a: List[LogEvent],
        errors_b: List[LogEvent]
    ) -> int:
        """查找两个系统错误之间的交叉引用"""
        count = 0
        
        for error_a in errors_a:
            for error_b in errors_b:
                time_diff = abs((error_a.timestamp - error_b.timestamp).total_seconds())
                if time_diff <= 300:
                    count += 1
        
        return count


class TimeSeriesAdvancedAnalyzer:
    """高级时间序列分析器 - 提供深度时间序列分析
    
    功能：
    - 趋势分析
    - 季节性检测
    - 异常检测
    - 预测分析
    - 相关性分析
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.window_size_minutes = self.config.get('window_size_minutes', 5)
        self.anomaly_threshold = self.config.get('anomaly_threshold', 2.5)
    
    def analyze(
        self,
        events: List[LogEvent]
    ) -> Dict[str, Any]:
        """执行完整的时间序列分析"""
        if not events:
            return {'error': 'No events to analyze'}
        
        error_series = self._build_error_series(events)
        volume_series = self._build_volume_series(events)
        
        return {
            'error_time_series': error_series,
            'volume_time_series': volume_series,
            'cross_correlation': self._analyze_cross_correlation(error_series, volume_series),
            'periodicity_analysis': self._analyze_periodicity(error_series),
            'change_points': self._detect_change_points(error_series),
            'forecast': self._generate_forecast(error_series),
            'anomaly_summary': self._summarize_anomalies(error_series)
        }
    
    def _build_error_series(self, events: List[LogEvent]) -> Dict[str, Any]:
        """构建错误时间序列"""
        error_events = [e for e in events if e.level in ['ERROR', 'CRITICAL', 'FATAL']]
        
        if not error_events:
            return {'points': [], 'trend': 'no_errors'}
        
        window = timedelta(minutes=self.window_size_minutes)
        points = []
        
        sorted_events = sorted(error_events, key=lambda x: x.timestamp)
        start_time = sorted_events[0].timestamp
        end_time = sorted_events[-1].timestamp
        current_time = start_time
        
        while current_time <= end_time:
            window_end = current_time + window
            window_events = [e for e in sorted_events if current_time <= e.timestamp < window_end]
            
            points.append({
                'timestamp': current_time.isoformat(),
                'count': len(window_events),
                'critical_count': sum(1 for e in window_events if e.level in ['CRITICAL', 'FATAL']),
                'error_count': len(window_events)
            })
            
            current_time = window_end
        
        trend = self._calculate_trend([p['count'] for p in points])
        
        return {
            'points': points,
            'trend': trend,
            'total_errors': len(error_events),
            'avg_per_window': sum(p['count'] for p in points) / len(points) if points else 0
        }
    
    def _build_volume_series(self, events: List[LogEvent]) -> Dict[str, Any]:
        """构建日志量时间序列"""
        window = timedelta(minutes=self.window_size_minutes)
        points = []
        
        sorted_events = sorted(events, key=lambda x: x.timestamp)
        start_time = sorted_events[0].timestamp
        end_time = sorted_events[-1].timestamp
        current_time = start_time
        
        while current_time <= end_time:
            window_end = current_time + window
            window_events = [e for e in sorted_events if current_time <= e.timestamp < window_end]
            
            points.append({
                'timestamp': current_time.isoformat(),
                'count': len(window_events),
                'by_level': dict(Counter(e.level for e in window_events))
            })
            
            current_time = window_end
        
        return {
            'points': points,
            'total_events': len(events),
            'avg_per_window': sum(p['count'] for p in points) / len(points) if points else 0
        }
    
    def _calculate_trend(self, values: List[int]) -> str:
        """计算趋势"""
        if len(values) < 3:
            return 'insufficient_data'
        
        n = len(values)
        x = list(range(n))
        y = values
        
        x_mean = sum(x) / n
        y_mean = sum(y) / n
        
        numerator = sum((x[i] - x_mean) * (y[i] - y_mean) for i in range(n))
        denominator = sum((x[i] - x_mean) ** 2 for i in range(n))
        
        if denominator == 0:
            return 'stable'
        
        slope = numerator / denominator
        
        if slope > 0.5:
            return 'increasing'
        elif slope < -0.5:
            return 'decreasing'
        else:
            return 'stable'
    
    def _analyze_cross_correlation(
        self,
        error_series: Dict[str, Any],
        volume_series: Dict[str, Any]
    ) -> Dict[str, Any]:
        """分析错误序列和日志量序列的互相关"""
        error_values = [p['count'] for p in error_series.get('points', [])]
        volume_values = [p['count'] for p in volume_series.get('points', [])]
        
        if not error_values or not volume_values:
            return {'correlation': 0}
        
        min_len = min(len(error_values), len(volume_values))
        error_values = error_values[:min_len]
        volume_values = volume_values[:min_len]
        
        mean_e = sum(error_values) / len(error_values)
        mean_v = sum(volume_values) / len(volume_values)
        
        numerator = sum((e - mean_e) * (v - mean_v) for e, v in zip(error_values, volume_values))
        denom_e = sum((e - mean_e) ** 2 for e in error_values) ** 0.5
        denom_v = sum((v - mean_v) ** 2 for v in volume_values) ** 0.5
        
        if denom_e == 0 or denom_v == 0:
            return {'correlation': 0}
        
        correlation = numerator / (denom_e * denom_v)
        
        return {
            'correlation': correlation,
            'interpretation': 'strong_positive' if correlation > 0.7 else 'moderate_positive' if correlation > 0.4 else 'weak' if correlation > -0.4 else 'negative'
        }
    
    def _analyze_periodicity(self, series: Dict[str, Any]) -> Dict[str, Any]:
        """分析周期性"""
        values = [p['count'] for p in series.get('points', [])]
        
        if len(values) < 24:
            return {'periodicity_detected': False, 'reason': 'insufficient_data'}
        
        autocorr_1 = self._autocorrelation(values, 1)
        autocorr_12 = self._autocorrelation(values, 12)
        autocorr_24 = self._autocorrelation(values, 24)
        
        periodicity_detected = abs(autocorr_12) > 0.5 or abs(autocorr_24) > 0.5
        
        return {
            'periodicity_detected': periodicity_detected,
            'autocorrelation_lag_1': autocorr_1,
            'autocorrelation_lag_12': autocorr_12,
            'autocorrelation_lag_24': autocorr_24,
            'suggested_period': 'hourly' if abs(autocorr_12) > 0.5 else 'daily' if abs(autocorr_24) > 0.5 else 'none'
        }
    
    def _autocorrelation(self, values: List[int], lag: int) -> float:
        """计算自相关"""
        n = len(values)
        if n <= lag:
            return 0.0
        
        mean = sum(values) / n
        variance = sum((v - mean) ** 2 for v in values) / n
        
        if variance == 0:
            return 0.0
        
        return sum((values[i] - mean) * (values[i - lag] - mean) for i in range(lag, n)) / (n * variance)
    
    def _detect_change_points(self, series: Dict[str, Any]) -> List[Dict[str, Any]]:
        """检测变化点"""
        values = [p['count'] for p in series.get('points', [])]
        
        if len(values) < 10:
            return []
        
        change_points = []
        
        for i in range(5, len(values) - 5):
            before = values[i-5:i]
            after = values[i:i+5]
            
            mean_before = sum(before) / len(before)
            mean_after = sum(after) / len(after)
            
            all_values = before + after
            std = (sum((v - sum(all_values) / len(all_values)) ** 2 for v in all_values) / len(all_values)) ** 0.5
            
            if std > 0:
                change_magnitude = abs(mean_after - mean_before) / std
                
                if change_magnitude > 2.0:
                    change_points.append({
                        'index': i,
                        'timestamp': series['points'][i]['timestamp'] if i < len(series['points']) else None,
                        'change_type': 'increase' if mean_after > mean_before else 'decrease',
                        'magnitude': change_magnitude,
                        'before_mean': mean_before,
                        'after_mean': mean_after
                    })
        
        return change_points
    
    def _generate_forecast(self, series: Dict[str, Any]) -> Dict[str, Any]:
        """生成预测"""
        values = [p['count'] for p in series.get('points', [])]
        
        if len(values) < 5:
            return {'forecast_available': False}
        
        alpha = 0.3
        smoothed = [values[0]]
        
        for i in range(1, len(values)):
            smoothed.append(alpha * values[i] + (1 - alpha) * smoothed[-1])
        
        forecast_values = []
        last_smoothed = smoothed[-1]
        
        for i in range(1, 7):
            forecast_values.append({
                'period_ahead': i,
                'predicted_value': round(last_smoothed, 2),
                'confidence': max(0.3, 1 - i * 0.1)
            })
        
        return {
            'forecast_available': True,
            'forecast_values': forecast_values,
            'method': 'exponential_smoothing',
            'smoothing_factor': alpha
        }
    
    def _summarize_anomalies(self, series: Dict[str, Any]) -> Dict[str, Any]:
        """汇总异常"""
        values = [p['count'] for p in series.get('points', [])]
        
        if not values:
            return {'anomaly_count': 0}
        
        mean = sum(values) / len(values)
        std = (sum((v - mean) ** 2 for v in values) / len(values)) ** 0.5 if len(values) > 1 else 0
        
        anomalies = []
        for i, value in enumerate(values):
            if std > 0:
                z_score = abs(value - mean) / std
                if z_score > self.anomaly_threshold:
                    anomalies.append({
                        'index': i,
                        'timestamp': series['points'][i]['timestamp'] if i < len(series['points']) else None,
                        'value': value,
                        'z_score': z_score,
                        'type': 'high' if value > mean else 'low'
                    })
        
        return {
            'anomaly_count': len(anomalies),
            'anomalies': anomalies[:10],
            'mean': mean,
            'std': std,
            'threshold': self.anomaly_threshold
        }


class CorrelationReportEnhancer:
    """关联分析报告增强器 - 生成更详细的分析报告
    
    功能：
    - 执行摘要增强
    - 详细问题分析
    - 修复建议生成
    - 可视化数据准备
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
    
    def enhance_report(
        self,
        report: 'CorrelationReport',
        multi_source_correlations: List[Dict[str, Any]],
        propagation_analysis: Dict[str, Any],
        time_series_analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        """增强关联分析报告"""
        return {
            'enhanced_executive_summary': self._generate_enhanced_summary(
                report, multi_source_correlations, propagation_analysis
            ),
            'multi_source_analysis': self._analyze_multi_source_findings(multi_source_correlations),
            'propagation_analysis': self._analyze_propagation_findings(propagation_analysis),
            'time_series_insights': self._generate_time_series_insights(time_series_analysis),
            'prioritized_issues': self._prioritize_issues(
                report, multi_source_correlations, propagation_analysis
            ),
            'action_plan': self._generate_action_plan(
                report, multi_source_correlations, propagation_analysis
            )
        }
    
    def _generate_enhanced_summary(
        self,
        report: 'CorrelationReport',
        multi_source_correlations: List[Dict[str, Any]],
        propagation_analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        """生成增强执行摘要"""
        summary = {
            'total_issues': len(report.error_chains) + len(multi_source_correlations),
            'critical_count': sum(1 for c in report.error_chains if c.severity.value == 'critical'),
            'multi_source_correlations': len(multi_source_correlations),
            'propagation_chains': propagation_analysis.get('summary', {}).get('total_chains', 0),
            'health_score': self._calculate_enhanced_health_score(
                report, multi_source_correlations, propagation_analysis
            ),
            'risk_assessment': self._assess_risk(
                report, multi_source_correlations, propagation_analysis
            )
        }
        
        return summary
    
    def _calculate_enhanced_health_score(
        self,
        report: 'CorrelationReport',
        multi_source_correlations: List[Dict[str, Any]],
        propagation_analysis: Dict[str, Any]
    ) -> float:
        """计算增强健康分数"""
        base_score = 100.0
        
        base_score -= len(report.error_chains) * 2
        base_score -= sum(1 for c in report.error_chains if c.severity.value == 'critical') * 10
        base_score -= len(multi_source_correlations) * 3
        base_score -= propagation_analysis.get('summary', {}).get('circular_count', 0) * 5
        
        return max(0.0, min(100.0, base_score))
    
    def _assess_risk(
        self,
        report: 'CorrelationReport',
        multi_source_correlations: List[Dict[str, Any]],
        propagation_analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        """评估风险"""
        risk_factors = []
        
        critical_chains = sum(1 for c in report.error_chains if c.severity.value == 'critical')
        if critical_chains > 0:
            risk_factors.append({
                'factor': 'critical_errors',
                'severity': 'high',
                'description': f'存在 {critical_chains} 条严重错误传播链'
            })
        
        if len(multi_source_correlations) > 5:
            risk_factors.append({
                'factor': 'multi_source_issues',
                'severity': 'medium',
                'description': f'发现 {len(multi_source_correlations)} 个多源关联问题'
            })
        
        circular_count = propagation_analysis.get('summary', {}).get('circular_count', 0)
        if circular_count > 0:
            risk_factors.append({
                'factor': 'circular_propagation',
                'severity': 'high',
                'description': f'检测到 {circular_count} 个循环传播链'
            })
        
        overall_risk = 'low'
        if any(f['severity'] == 'high' for f in risk_factors):
            overall_risk = 'high'
        elif any(f['severity'] == 'medium' for f in risk_factors):
            overall_risk = 'medium'
        
        return {
            'overall_risk': overall_risk,
            'risk_factors': risk_factors
        }
    
    def _analyze_multi_source_findings(
        self,
        correlations: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """分析多源关联发现"""
        if not correlations:
            return {'findings': [], 'summary': 'No multi-source correlations found'}
        
        rule_counts: Dict[str, int] = defaultdict(int)
        for corr in correlations:
            rule_counts[corr.get('rule_name', 'unknown')] += 1
        
        findings = []
        for rule_name, count in sorted(rule_counts.items(), key=lambda x: x[1], reverse=True):
            findings.append({
                'rule': rule_name,
                'occurrence_count': count,
                'severity': 'high' if count > 5 else 'medium' if count > 2 else 'low'
            })
        
        return {
            'findings': findings,
            'total_correlations': len(correlations),
            'unique_rules': len(rule_counts)
        }
    
    def _analyze_propagation_findings(
        self,
        propagation_analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        """分析传播链发现"""
        summary = propagation_analysis.get('summary', {})
        
        return {
            'total_chains': summary.get('total_chains', 0),
            'chain_breakdown': {
                'direct': summary.get('direct_count', 0),
                'indirect': summary.get('indirect_count', 0),
                'parallel': summary.get('parallel_count', 0),
                'circular': summary.get('circular_count', 0)
            },
            'recommendations': self._generate_propagation_recommendations(propagation_analysis)
        }
    
    def _generate_propagation_recommendations(
        self,
        propagation_analysis: Dict[str, Any]
    ) -> List[str]:
        """生成传播链修复建议"""
        recommendations = []
        
        if propagation_analysis.get('summary', {}).get('circular_count', 0) > 0:
            recommendations.append('检测到循环传播链，建议检查服务依赖关系，避免循环调用')
        
        if propagation_analysis.get('summary', {}).get('parallel_count', 0) > 0:
            recommendations.append('发现并行传播链，建议检查共享资源或配置变更')
        
        if propagation_analysis.get('summary', {}).get('indirect_count', 0) > 0:
            recommendations.append('存在间接传播链，建议增强错误隔离和熔断机制')
        
        return recommendations
    
    def _generate_time_series_insights(
        self,
        time_series_analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        """生成时间序列洞察"""
        error_series = time_series_analysis.get('error_time_series', {})
        
        insights = {
            'trend': error_series.get('trend', 'unknown'),
            'periodicity': time_series_analysis.get('periodicity_analysis', {}).get('suggested_period', 'none'),
            'anomaly_count': time_series_analysis.get('anomaly_summary', {}).get('anomaly_count', 0),
            'change_points': len(time_series_analysis.get('change_points', [])),
            'forecast_available': time_series_analysis.get('forecast', {}).get('forecast_available', False)
        }
        
        if insights['trend'] == 'increasing':
            insights['trend_alert'] = '错误率呈上升趋势，需要关注'
        elif insights['trend'] == 'decreasing':
            insights['trend_alert'] = '错误率呈下降趋势，系统状态改善'
        
        return insights
    
    def _prioritize_issues(
        self,
        report: 'CorrelationReport',
        multi_source_correlations: List[Dict[str, Any]],
        propagation_analysis: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """优先级排序问题"""
        issues = []
        
        for chain in report.error_chains:
            priority = 1 if chain.severity.value == 'critical' else 2 if chain.severity.value == 'high' else 3
            issues.append({
                'type': 'error_chain',
                'id': chain.chain_id,
                'priority': priority,
                'severity': chain.severity.value,
                'description': chain.description[:100] if hasattr(chain, 'description') else chain.root_cause.message[:100],
                'affected_systems': list(chain.affected_systems)
            })
        
        for corr in multi_source_correlations:
            priority = 1 if corr.get('confidence', 0) > 0.8 else 2
            issues.append({
                'type': 'multi_source_correlation',
                'rule': corr.get('rule_name', 'unknown'),
                'priority': priority,
                'confidence': corr.get('confidence', 0),
                'description': corr.get('description', '')
            })
        
        return sorted(issues, key=lambda x: x['priority'])[:20]
    
    def _generate_action_plan(
        self,
        report: 'CorrelationReport',
        multi_source_correlations: List[Dict[str, Any]],
        propagation_analysis: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """生成行动计划"""
        actions = []
        
        critical_chains = [c for c in report.error_chains if c.severity.value == 'critical']
        if critical_chains:
            actions.append({
                'priority': 1,
                'action': '立即处理严重错误传播链',
                'details': f'共 {len(critical_chains)} 条严重传播链需要立即处理',
                'estimated_effort': '高'
            })
        
        if propagation_analysis.get('summary', {}).get('circular_count', 0) > 0:
            actions.append({
                'priority': 1,
                'action': '解决循环传播问题',
                'details': '检测到循环传播链，可能导致系统不稳定',
                'estimated_effort': '中'
            })
        
        if len(multi_source_correlations) > 3:
            actions.append({
                'priority': 2,
                'action': '分析多源关联问题',
                'details': f'发现 {len(multi_source_correlations)} 个多源关联问题',
                'estimated_effort': '中'
            })
        
        actions.append({
            'priority': 3,
            'action': '完善监控和告警',
            'details': '基于分析结果优化监控策略',
            'estimated_effort': '低'
        })
        
        return actions
