#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
数据流分析器
============

本模块实现了数据流的全面分析功能，包括：
1. 数据流追踪 - 追踪数据从源头到目的地的完整路径
2. 数据转换问题识别 - 识别数据转换过程中的潜在问题
3. 传输效率优化建议 - 分析并优化数据传输效率
4. 数据流分析报告生成 - 生成完整的数据流分析报告

核心功能：
- 数据流向追踪与可视化
- 数据转换节点分析
- 传输瓶颈识别
- 效率优化建议生成
"""

import json
import sqlite3
import logging
import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any, Tuple, Set
from datetime import datetime
from enum import Enum
from pathlib import Path


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class DataFlowNodeType(Enum):
    """
    数据流节点类型枚举
    
    定义了数据流中可能出现的节点类型：
    - SOURCE: 数据源节点，数据的起点
    - TRANSFORM: 转换节点，对数据进行处理
    - FILTER: 过滤节点，筛选数据
    - AGGREGATE: 聚合节点，汇总数据
    - JOIN: 连接节点，合并多个数据流
    - SINK: 数据目的地节点，数据的终点
    - CACHE: 缓存节点，临时存储数据
    - QUEUE: 队列节点，异步数据传输
    """
    SOURCE = "source"
    TRANSFORM = "transform"
    FILTER = "filter"
    AGGREGATE = "aggregate"
    JOIN = "join"
    SINK = "sink"
    CACHE = "cache"
    QUEUE = "queue"


class DataFlowStatus(Enum):
    """
    数据流状态枚举
    
    定义了数据流节点的运行状态：
    - ACTIVE: 活跃状态，正常运行
    - INACTIVE: 非活跃状态，已停止
    - ERROR: 错误状态，运行异常
    - WARNING: 警告状态，存在问题但可运行
    - OPTIMIZING: 优化中
    """
    ACTIVE = "active"
    INACTIVE = "inactive"
    ERROR = "error"
    WARNING = "warning"
    OPTIMIZING = "optimizing"


class TransformIssueType(Enum):
    """
    数据转换问题类型枚举
    
    定义了数据转换过程中可能出现的问题类型：
    - TYPE_MISMATCH: 类型不匹配
    - DATA_LOSS: 数据丢失
    - PERFORMANCE_ISSUE: 性能问题
    - NULL_HANDLING: 空值处理问题
    - ENCODING_ERROR: 编码错误
    - FORMAT_ERROR: 格式错误
    - DUPLICATE_DATA: 重复数据
    - SCHEMA_MISMATCH: 模式不匹配
    - OVERFLOW: 数据溢出
    - PRECISION_LOSS: 精度丢失
    """
    TYPE_MISMATCH = "type_mismatch"
    DATA_LOSS = "data_loss"
    PERFORMANCE_ISSUE = "performance_issue"
    NULL_HANDLING = "null_handling"
    ENCODING_ERROR = "encoding_error"
    FORMAT_ERROR = "format_error"
    DUPLICATE_DATA = "duplicate_data"
    SCHEMA_MISMATCH = "schema_mismatch"
    OVERFLOW = "overflow"
    PRECISION_LOSS = "precision_loss"


class IssueSeverity(Enum):
    """
    问题严重程度枚举
    
    定义了问题的严重程度级别：
    - CRITICAL: 严重问题，必须立即处理
    - HIGH: 高优先级问题，需要尽快处理
    - MEDIUM: 中等问题，需要计划处理
    - LOW: 低优先级问题，可以延后处理
    - INFO: 信息提示，无需处理
    """
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class OptimizationType(Enum):
    """
    优化类型枚举
    
    定义了可能的优化方向：
    - CACHING: 添加缓存
    - BATCHING: 批量处理
    - PARALLELIZATION: 并行化
    - INDEXING: 添加索引
    - COMPRESSION: 数据压缩
    - PARTITIONING: 数据分区
    - LAZY_LOADING: 延迟加载
    - CONNECTION_POOLING: 连接池化
    - STREAMING: 流式处理
    """
    CACHING = "caching"
    BATCHING = "batching"
    PARALLELIZATION = "parallelization"
    INDEXING = "indexing"
    COMPRESSION = "compression"
    PARTITIONING = "partitioning"
    LAZY_LOADING = "lazy_loading"
    CONNECTION_POOLING = "connection_pooling"
    STREAMING = "streaming"


@dataclass
class DataFlowNode:
    """
    数据流节点数据类
    
    表示数据流中的一个节点，包含节点的基本属性和统计信息。
    
    属性:
        id: 节点唯一标识符
        name: 节点名称
        node_type: 节点类型
        description: 节点描述
        status: 节点状态
        input_schema: 输入数据模式
        output_schema: 输出数据模式
        processing_time_ms: 平均处理时间（毫秒）
        throughput_per_sec: 每秒吞吐量
        error_rate: 错误率（0-1）
        memory_usage_mb: 内存使用量（MB）
        cpu_usage_percent: CPU使用率（%）
        metadata: 额外元数据
    """
    id: str
    name: str
    node_type: DataFlowNodeType
    description: str = ""
    status: DataFlowStatus = DataFlowStatus.ACTIVE
    input_schema: Dict[str, Any] = field(default_factory=dict)
    output_schema: Dict[str, Any] = field(default_factory=dict)
    processing_time_ms: float = 0.0
    throughput_per_sec: float = 0.0
    error_rate: float = 0.0
    memory_usage_mb: float = 0.0
    cpu_usage_percent: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """将节点对象转换为字典格式"""
        return {
            "id": self.id,
            "name": self.name,
            "node_type": self.node_type.value,
            "description": self.description,
            "status": self.status.value,
            "input_schema": self.input_schema,
            "output_schema": self.output_schema,
            "processing_time_ms": self.processing_time_ms,
            "throughput_per_sec": self.throughput_per_sec,
            "error_rate": self.error_rate,
            "memory_usage_mb": self.memory_usage_mb,
            "cpu_usage_percent": self.cpu_usage_percent,
            "metadata": self.metadata
        }


@dataclass
class DataFlowEdge:
    """
    数据流边数据类
    
    表示数据流中两个节点之间的连接，包含数据传输信息。
    
    属性:
        id: 边唯一标识符
        source_node_id: 源节点ID
        target_node_id: 目标节点ID
        data_format: 数据格式（JSON/CSV/Binary等）
        average_size_bytes: 平均数据大小（字节）
        transfer_rate_per_sec: 每秒传输次数
        latency_ms: 传输延迟（毫秒）
        compression_enabled: 是否启用压缩
        encryption_enabled: 是否启用加密
        is_async: 是否异步传输
    """
    id: str
    source_node_id: str
    target_node_id: str
    data_format: str = "json"
    average_size_bytes: float = 0.0
    transfer_rate_per_sec: float = 0.0
    latency_ms: float = 0.0
    compression_enabled: bool = False
    encryption_enabled: bool = False
    is_async: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        """将边对象转换为字典格式"""
        return {
            "id": self.id,
            "source_node_id": self.source_node_id,
            "target_node_id": self.target_node_id,
            "data_format": self.data_format,
            "average_size_bytes": self.average_size_bytes,
            "transfer_rate_per_sec": self.transfer_rate_per_sec,
            "latency_ms": self.latency_ms,
            "compression_enabled": self.compression_enabled,
            "encryption_enabled": self.encryption_enabled,
            "is_async": self.is_async
        }


@dataclass
class DataFlowPath:
    """
    数据流路径数据类
    
    表示数据从源头到目的地的完整路径。
    
    属性:
        id: 路径唯一标识符
        name: 路径名称
        source_node_id: 起始节点ID
        sink_node_id: 终点节点ID
        node_ids: 路径上的节点ID列表
        edge_ids: 路径上的边ID列表
        total_latency_ms: 总延迟（毫秒）
        total_processing_time_ms: 总处理时间（毫秒）
        data_transformations: 数据转换次数
        bottleneck_node_id: 瓶颈节点ID（可选）
    """
    id: str
    name: str
    source_node_id: str
    sink_node_id: str
    node_ids: List[str] = field(default_factory=list)
    edge_ids: List[str] = field(default_factory=list)
    total_latency_ms: float = 0.0
    total_processing_time_ms: float = 0.0
    data_transformations: int = 0
    bottleneck_node_id: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """将路径对象转换为字典格式"""
        return {
            "id": self.id,
            "name": self.name,
            "source_node_id": self.source_node_id,
            "sink_node_id": self.sink_node_id,
            "node_ids": self.node_ids,
            "edge_ids": self.edge_ids,
            "total_latency_ms": self.total_latency_ms,
            "total_processing_time_ms": self.total_processing_time_ms,
            "data_transformations": self.data_transformations,
            "bottleneck_node_id": self.bottleneck_node_id
        }


@dataclass
class TransformIssue:
    """
    数据转换问题数据类
    
    表示数据转换过程中发现的问题。
    
    属性:
        id: 问题唯一标识符
        node_id: 关联节点ID
        issue_type: 问题类型
        severity: 严重程度
        description: 问题描述
        affected_fields: 受影响的字段列表
        occurrence_count: 出现次数
        sample_data: 示例数据
        suggested_fix: 建议修复方案
        detected_at: 检测时间
    """
    id: str
    node_id: str
    issue_type: TransformIssueType
    severity: IssueSeverity
    description: str
    affected_fields: List[str] = field(default_factory=list)
    occurrence_count: int = 1
    sample_data: Optional[Dict[str, Any]] = None
    suggested_fix: str = ""
    detected_at: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def to_dict(self) -> Dict[str, Any]:
        """将问题对象转换为字典格式"""
        return {
            "id": self.id,
            "node_id": self.node_id,
            "issue_type": self.issue_type.value,
            "severity": self.severity.value,
            "description": self.description,
            "affected_fields": self.affected_fields,
            "occurrence_count": self.occurrence_count,
            "sample_data": self.sample_data,
            "suggested_fix": self.suggested_fix,
            "detected_at": self.detected_at
        }


@dataclass
class OptimizationSuggestion:
    """
    优化建议数据类
    
    表示针对数据流的优化建议。
    
    属性:
        id: 建议唯一标识符
        optimization_type: 优化类型
        target_node_ids: 目标节点ID列表
        title: 建议标题
        description: 建议描述
        expected_improvement: 预期改进（百分比）
        implementation_effort: 实施难度（low/medium/high）
        priority: 优先级
        prerequisites: 前置条件列表
        implementation_steps: 实施步骤列表
        estimated_impact: 预估影响
    """
    id: str
    optimization_type: OptimizationType
    target_node_ids: List[str]
    title: str
    description: str
    expected_improvement: float = 0.0
    implementation_effort: str = "medium"
    priority: int = 3
    prerequisites: List[str] = field(default_factory=list)
    implementation_steps: List[str] = field(default_factory=list)
    estimated_impact: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """将建议对象转换为字典格式"""
        return {
            "id": self.id,
            "optimization_type": self.optimization_type.value,
            "target_node_ids": self.target_node_ids,
            "title": self.title,
            "description": self.description,
            "expected_improvement": self.expected_improvement,
            "implementation_effort": self.implementation_effort,
            "priority": self.priority,
            "prerequisites": self.prerequisites,
            "implementation_steps": self.implementation_steps,
            "estimated_impact": self.estimated_impact
        }


@dataclass
class EfficiencyMetrics:
    """
    效率指标数据类
    
    表示数据流的效率统计指标。
    
    属性:
        total_throughput: 总吞吐量（记录/秒）
        average_latency_ms: 平均延迟（毫秒）
        p99_latency_ms: P99延迟（毫秒）
        error_rate: 错误率
        resource_utilization: 资源利用率
        data_quality_score: 数据质量分数（0-100）
        bottleneck_score: 瓶颈分数（0-100）
        optimization_potential: 优化潜力（百分比）
    """
    total_throughput: float = 0.0
    average_latency_ms: float = 0.0
    p99_latency_ms: float = 0.0
    error_rate: float = 0.0
    resource_utilization: Dict[str, float] = field(default_factory=dict)
    data_quality_score: float = 100.0
    bottleneck_score: float = 0.0
    optimization_potential: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """将指标对象转换为字典格式"""
        return {
            "total_throughput": self.total_throughput,
            "average_latency_ms": self.average_latency_ms,
            "p99_latency_ms": self.p99_latency_ms,
            "error_rate": self.error_rate,
            "resource_utilization": self.resource_utilization,
            "data_quality_score": self.data_quality_score,
            "bottleneck_score": self.bottleneck_score,
            "optimization_potential": self.optimization_potential
        }


@dataclass
class DataFlowAnalysisReport:
    """
    数据流分析报告数据类
    
    包含完整的数据流分析结果。
    
    属性:
        id: 报告唯一标识符
        flow_name: 数据流名称
        nodes: 节点列表
        edges: 边列表
        paths: 路径列表
        transform_issues: 转换问题列表
        optimization_suggestions: 优化建议列表
        efficiency_metrics: 效率指标
        summary: 分析摘要
        generated_at: 报告生成时间
    """
    id: str
    flow_name: str
    nodes: List[DataFlowNode] = field(default_factory=list)
    edges: List[DataFlowEdge] = field(default_factory=list)
    paths: List[DataFlowPath] = field(default_factory=list)
    transform_issues: List[TransformIssue] = field(default_factory=list)
    optimization_suggestions: List[OptimizationSuggestion] = field(default_factory=list)
    efficiency_metrics: Optional[EfficiencyMetrics] = None
    summary: Dict[str, Any] = field(default_factory=dict)
    generated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def to_dict(self) -> Dict[str, Any]:
        """将报告对象转换为字典格式"""
        return {
            "id": self.id,
            "flow_name": self.flow_name,
            "nodes": [n.to_dict() for n in self.nodes],
            "edges": [e.to_dict() for e in self.edges],
            "paths": [p.to_dict() for p in self.paths],
            "transform_issues": [i.to_dict() for i in self.transform_issues],
            "optimization_suggestions": [s.to_dict() for s in self.optimization_suggestions],
            "efficiency_metrics": self.efficiency_metrics.to_dict() if self.efficiency_metrics else None,
            "summary": self.summary,
            "generated_at": self.generated_at
        }


class DataFlowAnalyzer:
    """
    数据流分析器
    
    核心分析器类，提供数据流的全面分析功能。
    
    主要功能:
    1. 数据流追踪 - 追踪数据从源头到目的地的完整路径
    2. 数据转换问题识别 - 识别数据转换过程中的潜在问题
    3. 传输效率优化建议 - 分析并优化数据传输效率
    4. 数据流分析报告生成 - 生成完整的数据流分析报告
    
    属性:
        db_path: 数据库路径
        PERFORMANCE_THRESHOLDS: 性能阈值配置
        OPTIMIZATION_RULES: 优化规则配置
    """
    
    PERFORMANCE_THRESHOLDS = {
        "high_latency_ms": 1000,
        "critical_latency_ms": 5000,
        "high_error_rate": 0.05,
        "critical_error_rate": 0.1,
        "high_cpu_percent": 80,
        "critical_cpu_percent": 95,
        "high_memory_mb": 1024,
        "critical_memory_mb": 2048,
        "low_throughput": 100,
    }
    
    OPTIMIZATION_RULES = {
        "caching_threshold": 3,
        "batching_threshold": 1000,
        "parallelization_threshold": 500,
        "compression_threshold_bytes": 10240,
    }
    
    def __init__(self, db_path: str = "data_flow_analysis.db"):
        """
        初始化数据流分析器
        
        参数:
            db_path: 数据库路径
        """
        self.db_path = db_path
        self._init_database()
        logger.info(f"数据流分析器初始化完成: {db_path}")
    
    def _get_connection(self) -> sqlite3.Connection:
        """获取数据库连接"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def _init_database(self):
        """初始化数据库表结构"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS data_flow_nodes (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                node_type TEXT NOT NULL,
                description TEXT,
                status TEXT DEFAULT 'active',
                input_schema TEXT,
                output_schema TEXT,
                processing_time_ms REAL DEFAULT 0,
                throughput_per_sec REAL DEFAULT 0,
                error_rate REAL DEFAULT 0,
                memory_usage_mb REAL DEFAULT 0,
                cpu_usage_percent REAL DEFAULT 0,
                metadata TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS data_flow_edges (
                id TEXT PRIMARY KEY,
                source_node_id TEXT NOT NULL,
                target_node_id TEXT NOT NULL,
                data_format TEXT DEFAULT 'json',
                average_size_bytes REAL DEFAULT 0,
                transfer_rate_per_sec REAL DEFAULT 0,
                latency_ms REAL DEFAULT 0,
                compression_enabled INTEGER DEFAULT 0,
                encryption_enabled INTEGER DEFAULT 0,
                is_async INTEGER DEFAULT 0,
                created_at TEXT NOT NULL,
                FOREIGN KEY (source_node_id) REFERENCES data_flow_nodes(id),
                FOREIGN KEY (target_node_id) REFERENCES data_flow_nodes(id)
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS data_flow_paths (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                source_node_id TEXT NOT NULL,
                sink_node_id TEXT NOT NULL,
                node_ids TEXT,
                edge_ids TEXT,
                total_latency_ms REAL DEFAULT 0,
                total_processing_time_ms REAL DEFAULT 0,
                data_transformations INTEGER DEFAULT 0,
                bottleneck_node_id TEXT,
                created_at TEXT NOT NULL
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS transform_issues (
                id TEXT PRIMARY KEY,
                node_id TEXT NOT NULL,
                issue_type TEXT NOT NULL,
                severity TEXT NOT NULL,
                description TEXT,
                affected_fields TEXT,
                occurrence_count INTEGER DEFAULT 1,
                sample_data TEXT,
                suggested_fix TEXT,
                detected_at TEXT NOT NULL,
                FOREIGN KEY (node_id) REFERENCES data_flow_nodes(id)
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS optimization_suggestions (
                id TEXT PRIMARY KEY,
                optimization_type TEXT NOT NULL,
                target_node_ids TEXT,
                title TEXT NOT NULL,
                description TEXT,
                expected_improvement REAL DEFAULT 0,
                implementation_effort TEXT DEFAULT 'medium',
                priority INTEGER DEFAULT 3,
                prerequisites TEXT,
                implementation_steps TEXT,
                estimated_impact TEXT,
                created_at TEXT NOT NULL
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS analysis_reports (
                id TEXT PRIMARY KEY,
                flow_name TEXT NOT NULL,
                report_data TEXT,
                generated_at TEXT NOT NULL
            )
        ''')
        
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_node_type ON data_flow_nodes(node_type)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_edge_source ON data_flow_edges(source_node_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_edge_target ON data_flow_edges(target_node_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_issue_node ON transform_issues(node_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_issue_severity ON transform_issues(severity)')
        
        conn.commit()
        conn.close()
    
    def _generate_id(self, prefix: str = "DF") -> str:
        """生成唯一标识符"""
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S%f')
        return f"{prefix}-{timestamp}"
    
    def register_node(self,
                      name: str,
                      node_type: DataFlowNodeType,
                      description: str = "",
                      input_schema: Dict[str, Any] = None,
                      output_schema: Dict[str, Any] = None,
                      processing_time_ms: float = 0.0,
                      throughput_per_sec: float = 0.0,
                      error_rate: float = 0.0,
                      memory_usage_mb: float = 0.0,
                      cpu_usage_percent: float = 0.0,
                      metadata: Dict[str, Any] = None) -> DataFlowNode:
        """
        注册数据流节点
        
        创建并记录一个新的数据流节点。
        
        参数:
            name: 节点名称
            node_type: 节点类型
            description: 节点描述
            input_schema: 输入数据模式
            output_schema: 输出数据模式
            processing_time_ms: 平均处理时间（毫秒）
            throughput_per_sec: 每秒吞吐量
            error_rate: 错误率
            memory_usage_mb: 内存使用量
            cpu_usage_percent: CPU使用率
            metadata: 额外元数据
        
        返回:
            DataFlowNode: 创建的节点对象
        """
        node_id = self._generate_id("NODE")
        now = datetime.now().isoformat()
        
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO data_flow_nodes 
                (id, name, node_type, description, status, input_schema, output_schema,
                 processing_time_ms, throughput_per_sec, error_rate, memory_usage_mb,
                 cpu_usage_percent, metadata, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (node_id, name, node_type.value, description, DataFlowStatus.ACTIVE.value,
                  json.dumps(input_schema or {}, ensure_ascii=False),
                  json.dumps(output_schema or {}, ensure_ascii=False),
                  processing_time_ms, throughput_per_sec, error_rate,
                  memory_usage_mb, cpu_usage_percent,
                  json.dumps(metadata or {}, ensure_ascii=False), now, now))
            
            conn.commit()
            conn.close()
            
            logger.info(f"注册数据流节点: {node_id} - {name}")
            
            return DataFlowNode(
                id=node_id,
                name=name,
                node_type=node_type,
                description=description,
                input_schema=input_schema or {},
                output_schema=output_schema or {},
                processing_time_ms=processing_time_ms,
                throughput_per_sec=throughput_per_sec,
                error_rate=error_rate,
                memory_usage_mb=memory_usage_mb,
                cpu_usage_percent=cpu_usage_percent,
                metadata=metadata or {}
            )
            
        except Exception as e:
            logger.error(f"注册数据流节点失败: {e}")
            raise
    
    def register_edge(self,
                      source_node_id: str,
                      target_node_id: str,
                      data_format: str = "json",
                      average_size_bytes: float = 0.0,
                      transfer_rate_per_sec: float = 0.0,
                      latency_ms: float = 0.0,
                      compression_enabled: bool = False,
                      encryption_enabled: bool = False,
                      is_async: bool = False) -> DataFlowEdge:
        """
        注册数据流边
        
        创建并记录两个节点之间的数据流连接。
        
        参数:
            source_node_id: 源节点ID
            target_node_id: 目标节点ID
            data_format: 数据格式
            average_size_bytes: 平均数据大小
            transfer_rate_per_sec: 每秒传输次数
            latency_ms: 传输延迟
            compression_enabled: 是否启用压缩
            encryption_enabled: 是否启用加密
            is_async: 是否异步传输
        
        返回:
            DataFlowEdge: 创建的边对象
        """
        edge_id = self._generate_id("EDGE")
        now = datetime.now().isoformat()
        
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO data_flow_edges 
                (id, source_node_id, target_node_id, data_format, average_size_bytes,
                 transfer_rate_per_sec, latency_ms, compression_enabled, encryption_enabled,
                 is_async, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (edge_id, source_node_id, target_node_id, data_format,
                  average_size_bytes, transfer_rate_per_sec, latency_ms,
                  1 if compression_enabled else 0,
                  1 if encryption_enabled else 0,
                  1 if is_async else 0, now))
            
            conn.commit()
            conn.close()
            
            logger.info(f"注册数据流边: {edge_id} - {source_node_id} -> {target_node_id}")
            
            return DataFlowEdge(
                id=edge_id,
                source_node_id=source_node_id,
                target_node_id=target_node_id,
                data_format=data_format,
                average_size_bytes=average_size_bytes,
                transfer_rate_per_sec=transfer_rate_per_sec,
                latency_ms=latency_ms,
                compression_enabled=compression_enabled,
                encryption_enabled=encryption_enabled,
                is_async=is_async
            )
            
        except Exception as e:
            logger.error(f"注册数据流边失败: {e}")
            raise
    
    def trace_data_flow(self, source_node_id: str, sink_node_id: str = None) -> List[DataFlowPath]:
        """
        追踪数据流
        
        追踪从指定源节点出发的数据流路径，支持追踪到特定目标节点或所有可达节点。
        
        追踪策略:
        1. 从源节点开始，使用深度优先搜索遍历所有路径
        2. 计算每条路径的总延迟和处理时间
        3. 识别路径上的瓶颈节点
        4. 统计数据转换次数
        
        参数:
            source_node_id: 源节点ID
            sink_node_id: 目标节点ID（可选，不指定则追踪所有路径）
        
        返回:
            List[DataFlowPath]: 数据流路径列表
        """
        logger.info(f"开始追踪数据流: 源节点 {source_node_id}")
        
        paths = []
        
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute('SELECT * FROM data_flow_nodes WHERE id = ?', (source_node_id,))
            source_node = cursor.fetchone()
            
            if not source_node:
                logger.warning(f"源节点不存在: {source_node_id}")
                conn.close()
                return paths
            
            cursor.execute('''
                SELECT e.*, n.name as target_name, n.node_type as target_type
                FROM data_flow_edges e
                JOIN data_flow_nodes n ON e.target_node_id = n.id
                WHERE e.source_node_id = ?
            ''', (source_node_id,))
            
            outgoing_edges = cursor.fetchall()
            
            for edge in outgoing_edges:
                visited_nodes = {source_node_id}
                visited_edges = set()
                
                self._trace_path_dfs(
                    cursor=cursor,
                    current_node_id=edge['target_node_id'],
                    target_node_id=sink_node_id,
                    visited_nodes=visited_nodes,
                    visited_edges=visited_edges,
                    current_path=[source_node_id],
                    current_edge_path=[edge['id']],
                    total_latency=edge['latency_ms'],
                    total_processing=source_node['processing_time_ms'],
                    transformations=0,
                    paths=paths
                )
            
            conn.close()
            
            for path in paths:
                self._save_path(path)
            
            logger.info(f"数据流追踪完成: 发现 {len(paths)} 条路径")
            
        except Exception as e:
            logger.error(f"追踪数据流失败: {e}")
        
        return paths
    
    def _trace_path_dfs(self,
                        cursor,
                        current_node_id: str,
                        target_node_id: Optional[str],
                        visited_nodes: Set[str],
                        visited_edges: Set[str],
                        current_path: List[str],
                        current_edge_path: List[str],
                        total_latency: float,
                        total_processing: float,
                        transformations: int,
                        paths: List[DataFlowPath]):
        """
        深度优先搜索追踪路径
        
        递归遍历数据流图，收集所有路径信息。
        
        参数:
            cursor: 数据库游标
            current_node_id: 当前节点ID
            target_node_id: 目标节点ID
            visited_nodes: 已访问节点集合
            visited_edges: 已访问边集合
            current_path: 当前路径节点列表
            current_edge_path: 当前路径边列表
            total_latency: 累计延迟
            total_processing: 累计处理时间
            transformations: 转换次数
            paths: 路径结果列表
        """
        if current_node_id in visited_nodes:
            return
        
        cursor.execute('SELECT * FROM data_flow_nodes WHERE id = ?', (current_node_id,))
        current_node = cursor.fetchone()
        
        if not current_node:
            return
        
        visited_nodes.add(current_node_id)
        current_path.append(current_node_id)
        
        total_processing += current_node['processing_time_ms']
        
        if DataFlowNodeType(current_node['node_type']) in [
            DataFlowNodeType.TRANSFORM, DataFlowNodeType.FILTER,
            DataFlowNodeType.AGGREGATE, DataFlowNodeType.JOIN
        ]:
            transformations += 1
        
        if target_node_id and current_node_id == target_node_id:
            path = self._create_path(
                current_path, current_edge_path,
                total_latency, total_processing, transformations,
                cursor
            )
            paths.append(path)
            visited_nodes.remove(current_node_id)
            current_path.pop()
            return
        
        if DataFlowNodeType(current_node['node_type']) == DataFlowNodeType.SINK:
            if target_node_id is None:
                path = self._create_path(
                    current_path, current_edge_path,
                    total_latency, total_processing, transformations,
                    cursor
                )
                paths.append(path)
            visited_nodes.remove(current_node_id)
            current_path.pop()
            return
        
        cursor.execute('''
            SELECT e.*, n.node_type as target_type
            FROM data_flow_edges e
            JOIN data_flow_nodes n ON e.target_node_id = n.id
            WHERE e.source_node_id = ?
        ''', (current_node_id,))
        
        outgoing_edges = cursor.fetchall()
        
        if not outgoing_edges:
            if target_node_id is None:
                path = self._create_path(
                    current_path, current_edge_path,
                    total_latency, total_processing, transformations,
                    cursor
                )
                paths.append(path)
            visited_nodes.remove(current_node_id)
            current_path.pop()
            return
        
        for edge in outgoing_edges:
            if edge['id'] in visited_edges:
                continue
            
            visited_edges.add(edge['id'])
            current_edge_path.append(edge['id'])
            
            self._trace_path_dfs(
                cursor=cursor,
                current_node_id=edge['target_node_id'],
                target_node_id=target_node_id,
                visited_nodes=visited_nodes.copy(),
                visited_edges=visited_edges.copy(),
                current_path=current_path.copy(),
                current_edge_path=current_edge_path.copy(),
                total_latency=total_latency + edge['latency_ms'],
                total_processing=total_processing,
                transformations=transformations,
                paths=paths
            )
    
    def _create_path(self,
                     node_ids: List[str],
                     edge_ids: List[str],
                     total_latency: float,
                     total_processing: float,
                     transformations: int,
                     cursor) -> DataFlowPath:
        """
        创建数据流路径对象
        
        参数:
            node_ids: 节点ID列表
            edge_ids: 边ID列表
            total_latency: 总延迟
            total_processing: 总处理时间
            transformations: 转换次数
            cursor: 数据库游标
        
        返回:
            DataFlowPath: 路径对象
        """
        path_id = self._generate_id("PATH")
        
        bottleneck_node_id = None
        max_processing = 0
        
        for node_id in node_ids:
            cursor.execute('SELECT processing_time_ms FROM data_flow_nodes WHERE id = ?', (node_id,))
            node = cursor.fetchone()
            if node and node['processing_time_ms'] > max_processing:
                max_processing = node['processing_time_ms']
                bottleneck_node_id = node_id
        
        path_name = " -> ".join(node_ids[:3])
        if len(node_ids) > 3:
            path_name += f" -> ... ({len(node_ids)} nodes)"
        
        return DataFlowPath(
            id=path_id,
            name=path_name,
            source_node_id=node_ids[0] if node_ids else "",
            sink_node_id=node_ids[-1] if node_ids else "",
            node_ids=node_ids,
            edge_ids=edge_ids,
            total_latency_ms=total_latency,
            total_processing_time_ms=total_processing,
            data_transformations=transformations,
            bottleneck_node_id=bottleneck_node_id
        )
    
    def _save_path(self, path: DataFlowPath):
        """
        保存路径到数据库
        
        参数:
            path: 路径对象
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            now = datetime.now().isoformat()
            
            cursor.execute('''
                INSERT INTO data_flow_paths 
                (id, name, source_node_id, sink_node_id, node_ids, edge_ids,
                 total_latency_ms, total_processing_time_ms, data_transformations,
                 bottleneck_node_id, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (path.id, path.name, path.source_node_id, path.sink_node_id,
                  json.dumps(path.node_ids), json.dumps(path.edge_ids),
                  path.total_latency_ms, path.total_processing_time_ms,
                  path.data_transformations, path.bottleneck_node_id, now))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"保存路径失败: {e}")
    
    def identify_transform_issues(self, node_id: str = None) -> List[TransformIssue]:
        """
        识别数据转换问题
        
        分析数据转换节点，识别潜在的数据转换问题。
        
        分析策略:
        1. 检查输入输出模式匹配性
        2. 分析错误率和处理时间异常
        3. 检测数据类型转换问题
        4. 识别空值处理问题
        5. 检测性能瓶颈
        
        参数:
            node_id: 指定节点ID（可选，不指定则分析所有转换节点）
        
        返回:
            List[TransformIssue]: 转换问题列表
        """
        logger.info(f"开始识别数据转换问题: {'节点 ' + node_id if node_id else '所有节点'}")
        
        issues = []
        
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            if node_id:
                cursor.execute('''
                    SELECT * FROM data_flow_nodes 
                    WHERE id = ? AND node_type IN ('transform', 'filter', 'aggregate', 'join')
                ''', (node_id,))
            else:
                cursor.execute('''
                    SELECT * FROM data_flow_nodes 
                    WHERE node_type IN ('transform', 'filter', 'aggregate', 'join')
                ''')
            
            transform_nodes = cursor.fetchall()
            
            for node in transform_nodes:
                node_issues = self._analyze_node_transform_issues(cursor, node)
                issues.extend(node_issues)
            
            conn.close()
            
            for issue in issues:
                self._save_transform_issue(issue)
            
            logger.info(f"数据转换问题识别完成: 发现 {len(issues)} 个问题")
            
        except Exception as e:
            logger.error(f"识别数据转换问题失败: {e}")
        
        return issues
    
    def _analyze_node_transform_issues(self, cursor, node: sqlite3.Row) -> List[TransformIssue]:
        """
        分析单个节点的转换问题
        
        参数:
            cursor: 数据库游标
            node: 节点数据行
        
        返回:
            List[TransformIssue]: 问题列表
        """
        issues = []
        
        if node['error_rate'] > self.PERFORMANCE_THRESHOLDS['critical_error_rate']:
            issue = TransformIssue(
                id=self._generate_id("ISS"),
                node_id=node['id'],
                issue_type=TransformIssueType.DATA_LOSS,
                severity=IssueSeverity.CRITICAL,
                description=f"节点错误率过高: {node['error_rate']*100:.2f}%，可能导致数据丢失",
                affected_fields=["all"],
                suggested_fix="检查错误日志，修复数据处理逻辑，添加错误处理机制"
            )
            issues.append(issue)
        
        elif node['error_rate'] > self.PERFORMANCE_THRESHOLDS['high_error_rate']:
            issue = TransformIssue(
                id=self._generate_id("ISS"),
                node_id=node['id'],
                issue_type=TransformIssueType.DATA_LOSS,
                severity=IssueSeverity.HIGH,
                description=f"节点错误率较高: {node['error_rate']*100:.2f}%",
                affected_fields=["all"],
                suggested_fix="分析错误原因，优化数据处理逻辑"
            )
            issues.append(issue)
        
        input_schema = json.loads(node['input_schema']) if node['input_schema'] else {}
        output_schema = json.loads(node['output_schema']) if node['output_schema'] else {}
        
        schema_issues = self._check_schema_compatibility(node['id'], input_schema, output_schema)
        issues.extend(schema_issues)
        
        if node['processing_time_ms'] > self.PERFORMANCE_THRESHOLDS['critical_latency_ms']:
            issue = TransformIssue(
                id=self._generate_id("ISS"),
                node_id=node['id'],
                issue_type=TransformIssueType.PERFORMANCE_ISSUE,
                severity=IssueSeverity.HIGH,
                description=f"处理时间过长: {node['processing_time_ms']:.2f}ms，严重影响数据流效率",
                suggested_fix="优化处理算法，考虑并行化或批量处理"
            )
            issues.append(issue)
        
        if node['cpu_usage_percent'] > self.PERFORMANCE_THRESHOLDS['critical_cpu_percent']:
            issue = TransformIssue(
                id=self._generate_id("ISS"),
                node_id=node['id'],
                issue_type=TransformIssueType.PERFORMANCE_ISSUE,
                severity=IssueSeverity.HIGH,
                description=f"CPU使用率过高: {node['cpu_usage_percent']:.2f}%",
                suggested_fix="优化计算逻辑，考虑资源扩容或负载均衡"
            )
            issues.append(issue)
        
        if node['memory_usage_mb'] > self.PERFORMANCE_THRESHOLDS['critical_memory_mb']:
            issue = TransformIssue(
                id=self._generate_id("ISS"),
                node_id=node['id'],
                issue_type=TransformIssueType.PERFORMANCE_ISSUE,
                severity=IssueSeverity.HIGH,
                description=f"内存使用过高: {node['memory_usage_mb']:.2f}MB",
                suggested_fix="优化内存使用，考虑流式处理或数据分块"
            )
            issues.append(issue)
        
        cursor.execute('''
            SELECT * FROM data_flow_edges WHERE target_node_id = ?
        ''', (node['id'],))
        incoming_edges = cursor.fetchall()
        
        for edge in incoming_edges:
            if edge['average_size_bytes'] > self.OPTIMIZATION_RULES['compression_threshold_bytes']:
                if not edge['compression_enabled']:
                    issue = TransformIssue(
                        id=self._generate_id("ISS"),
                        node_id=node['id'],
                        issue_type=TransformIssueType.PERFORMANCE_ISSUE,
                        severity=IssueSeverity.MEDIUM,
                        description=f"输入数据量较大({edge['average_size_bytes']/1024:.2f}KB)但未启用压缩",
                        suggested_fix="启用数据压缩以减少传输开销"
                    )
                    issues.append(issue)
        
        return issues
    
    def _check_schema_compatibility(self,
                                    node_id: str,
                                    input_schema: Dict[str, Any],
                                    output_schema: Dict[str, Any]) -> List[TransformIssue]:
        """
        检查输入输出模式的兼容性
        
        参数:
            node_id: 节点ID
            input_schema: 输入模式
            output_schema: 输出模式
        
        返回:
            List[TransformIssue]: 问题列表
        """
        issues = []
        
        if not input_schema or not output_schema:
            return issues
        
        input_fields = set(input_schema.get('fields', {}).keys())
        output_fields = set(output_schema.get('fields', {}).keys())
        
        missing_fields = input_fields - output_fields
        if missing_fields:
            issue = TransformIssue(
                id=self._generate_id("ISS"),
                node_id=node_id,
                issue_type=TransformIssueType.DATA_LOSS,
                severity=IssueSeverity.MEDIUM,
                description=f"输出模式缺少字段: {', '.join(missing_fields)}",
                affected_fields=list(missing_fields),
                suggested_fix="确认字段是否被有意过滤，否则检查转换逻辑"
            )
            issues.append(issue)
        
        for field_name in input_fields & output_fields:
            input_type = input_schema.get('fields', {}).get(field_name, {}).get('type')
            output_type = output_schema.get('fields', {}).get(field_name, {}).get('type')
            
            if input_type and output_type and input_type != output_type:
                issue = TransformIssue(
                    id=self._generate_id("ISS"),
                    node_id=node_id,
                    issue_type=TransformIssueType.TYPE_MISMATCH,
                    severity=IssueSeverity.MEDIUM,
                    description=f"字段 '{field_name}' 类型从 {input_type} 变为 {output_type}",
                    affected_fields=[field_name],
                    suggested_fix="确认类型转换是否正确，添加类型验证"
                )
                issues.append(issue)
        
        for field_name, field_info in output_schema.get('fields', {}).items():
            if field_info.get('nullable') == False:
                if input_schema.get('fields', {}).get(field_name, {}).get('nullable') == True:
                    issue = TransformIssue(
                        id=self._generate_id("ISS"),
                        node_id=node_id,
                        issue_type=TransformIssueType.NULL_HANDLING,
                        severity=IssueSeverity.HIGH,
                        description=f"字段 '{field_name}' 输出不允许为空，但输入可能为空",
                        affected_fields=[field_name],
                        suggested_fix="添加空值处理逻辑或设置默认值"
                    )
                    issues.append(issue)
        
        return issues
    
    def _save_transform_issue(self, issue: TransformIssue):
        """
        保存转换问题到数据库
        
        参数:
            issue: 问题对象
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO transform_issues 
                (id, node_id, issue_type, severity, description, affected_fields,
                 occurrence_count, sample_data, suggested_fix, detected_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (issue.id, issue.node_id, issue.issue_type.value,
                  issue.severity.value, issue.description,
                  json.dumps(issue.affected_fields, ensure_ascii=False),
                  issue.occurrence_count,
                  json.dumps(issue.sample_data, ensure_ascii=False) if issue.sample_data else None,
                  issue.suggested_fix, issue.detected_at))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"保存转换问题失败: {e}")
    
    def generate_optimization_suggestions(self, node_id: str = None) -> List[OptimizationSuggestion]:
        """
        生成传输效率优化建议
        
        基于数据流分析结果，生成针对性的优化建议。
        
        分析策略:
        1. 识别性能瓶颈节点
        2. 分析数据传输模式
        3. 评估资源利用效率
        4. 提出优化方案
        
        参数:
            node_id: 指定节点ID（可选，不指定则分析所有节点）
        
        返回:
            List[OptimizationSuggestion]: 优化建议列表
        """
        logger.info(f"开始生成优化建议: {'节点 ' + node_id if node_id else '所有节点'}")
        
        suggestions = []
        
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            if node_id:
                cursor.execute('SELECT * FROM data_flow_nodes WHERE id = ?', (node_id,))
            else:
                cursor.execute('SELECT * FROM data_flow_nodes')
            
            nodes = cursor.fetchall()
            
            for node in nodes:
                node_suggestions = self._generate_node_optimizations(cursor, node)
                suggestions.extend(node_suggestions)
            
            cursor.execute('SELECT * FROM data_flow_edges')
            edges = cursor.fetchall()
            
            edge_suggestions = self._generate_edge_optimizations(edges)
            suggestions.extend(edge_suggestions)
            
            path_suggestions = self._generate_path_optimizations(cursor)
            suggestions.extend(path_suggestions)
            
            conn.close()
            
            suggestions.sort(key=lambda x: x.priority)
            
            for suggestion in suggestions:
                self._save_optimization_suggestion(suggestion)
            
            logger.info(f"优化建议生成完成: 生成 {len(suggestions)} 条建议")
            
        except Exception as e:
            logger.error(f"生成优化建议失败: {e}")
        
        return suggestions
    
    def _generate_node_optimizations(self, cursor, node: sqlite3.Row) -> List[OptimizationSuggestion]:
        """
        为单个节点生成优化建议
        
        参数:
            cursor: 数据库游标
            node: 节点数据行
        
        返回:
            List[OptimizationSuggestion]: 建议列表
        """
        suggestions = []
        
        cursor.execute('''
            SELECT COUNT(*) as incoming_count FROM data_flow_edges WHERE target_node_id = ?
        ''', (node['id'],))
        incoming_count = cursor.fetchone()['incoming_count']
        
        if incoming_count >= self.OPTIMIZATION_RULES['caching_threshold']:
            suggestion = OptimizationSuggestion(
                id=self._generate_id("OPT"),
                optimization_type=OptimizationType.CACHING,
                target_node_ids=[node['id']],
                title=f"为节点 {node['name']} 添加缓存",
                description=f"该节点有 {incoming_count} 个输入源，添加缓存可减少重复计算",
                expected_improvement=30.0,
                implementation_effort="low",
                priority=1,
                prerequisites=["确保数据一致性要求允许缓存"],
                implementation_steps=[
                    "分析数据更新频率",
                    "选择合适的缓存策略（TTL/LRU）",
                    "实现缓存层",
                    "添加缓存失效机制"
                ],
                estimated_impact={
                    "latency_reduction": "30-50%",
                    "throughput_increase": "2-3x"
                }
            )
            suggestions.append(suggestion)
        
        if node['throughput_per_sec'] > self.OPTIMIZATION_RULES['parallelization_threshold']:
            if DataFlowNodeType(node['node_type']) in [DataFlowNodeType.TRANSFORM, DataFlowNodeType.FILTER]:
                suggestion = OptimizationSuggestion(
                    id=self._generate_id("OPT"),
                    optimization_type=OptimizationType.PARALLELIZATION,
                    target_node_ids=[node['id']],
                    title=f"并行化节点 {node['name']} 的处理",
                    description="该节点吞吐量较高，可通过并行化提升处理能力",
                    expected_improvement=50.0,
                    implementation_effort="medium",
                    priority=2,
                    prerequisites=["确保处理逻辑无状态", "评估线程安全性"],
                    implementation_steps=[
                        "识别可并行化的处理单元",
                        "实现并行处理框架",
                        "添加任务分发和结果聚合逻辑",
                        "测试并行化效果"
                    ],
                    estimated_impact={
                        "throughput_increase": "2-4x",
                        "latency_change": "可能略有增加"
                    }
                )
                suggestions.append(suggestion)
        
        if node['memory_usage_mb'] > self.PERFORMANCE_THRESHOLDS['high_memory_mb']:
            suggestion = OptimizationSuggestion(
                id=self._generate_id("OPT"),
                optimization_type=OptimizationType.STREAMING,
                target_node_ids=[node['id']],
                title=f"对节点 {node['name']} 使用流式处理",
                description=f"内存使用量较高({node['memory_usage_mb']:.0f}MB)，建议采用流式处理",
                expected_improvement=40.0,
                implementation_effort="high",
                priority=2,
                prerequisites=["评估是否支持流式处理"],
                implementation_steps=[
                    "重构数据处理逻辑为流式",
                    "实现数据分块机制",
                    "优化内存管理",
                    "测试流式处理效果"
                ],
                estimated_impact={
                    "memory_reduction": "50-70%",
                    "throughput_change": "可能略有下降"
                }
            )
            suggestions.append(suggestion)
        
        return suggestions
    
    def _generate_edge_optimizations(self, edges: List[sqlite3.Row]) -> List[OptimizationSuggestion]:
        """
        为边生成优化建议
        
        参数:
            edges: 边数据行列表
        
        返回:
            List[OptimizationSuggestion]: 建议列表
        """
        suggestions = []
        
        for edge in edges:
            if edge['average_size_bytes'] > self.OPTIMIZATION_RULES['compression_threshold_bytes']:
                if not edge['compression_enabled']:
                    suggestion = OptimizationSuggestion(
                        id=self._generate_id("OPT"),
                        optimization_type=OptimizationType.COMPRESSION,
                        target_node_ids=[edge['source_node_id'], edge['target_node_id']],
                        title="启用数据传输压缩",
                        description=f"数据传输量较大({edge['average_size_bytes']/1024:.2f}KB)，建议启用压缩",
                        expected_improvement=25.0,
                        implementation_effort="low",
                        priority=2,
                        prerequisites=["评估压缩/解压缩开销"],
                        implementation_steps=[
                            "选择合适的压缩算法（gzip/lz4）",
                            "在发送端添加压缩逻辑",
                            "在接收端添加解压缩逻辑",
                            "测试压缩效果"
                        ],
                        estimated_impact={
                            "bandwidth_reduction": "50-70%",
                            "cpu_overhead": "5-10%"
                        }
                    )
                    suggestions.append(suggestion)
            
            if edge['latency_ms'] > self.PERFORMANCE_THRESHOLDS['high_latency_ms']:
                if not edge['is_async']:
                    suggestion = OptimizationSuggestion(
                        id=self._generate_id("OPT"),
                        optimization_type=OptimizationType.CONNECTION_POOLING,
                        target_node_ids=[edge['source_node_id'], edge['target_node_id']],
                        title="使用异步传输或连接池",
                        description=f"传输延迟较高({edge['latency_ms']:.0f}ms)，建议优化连接方式",
                        expected_improvement=20.0,
                        implementation_effort="medium",
                        priority=3,
                        prerequisites=["评估异步传输的适用性"],
                        implementation_steps=[
                            "实现连接池管理",
                            "或改为异步传输模式",
                            "添加重试和超时机制",
                            "测试连接优化效果"
                        ],
                        estimated_impact={
                            "latency_reduction": "20-40%",
                            "connection_efficiency": "提升"
                        }
                    )
                    suggestions.append(suggestion)
        
        return suggestions
    
    def _generate_path_optimizations(self, cursor) -> List[OptimizationSuggestion]:
        """
        为路径生成优化建议
        
        参数:
            cursor: 数据库游标
        
        返回:
            List[OptimizationSuggestion]: 建议列表
        """
        suggestions = []
        
        cursor.execute('''
            SELECT * FROM data_flow_paths 
            WHERE total_latency_ms > ? OR total_processing_time_ms > ?
        ''', (self.PERFORMANCE_THRESHOLDS['critical_latency_ms'],
              self.PERFORMANCE_THRESHOLDS['critical_latency_ms'] * 2))
        
        slow_paths = cursor.fetchall()
        
        for path in slow_paths:
            if path['bottleneck_node_id']:
                cursor.execute('SELECT name FROM data_flow_nodes WHERE id = ?', (path['bottleneck_node_id'],))
                bottleneck = cursor.fetchone()
                bottleneck_name = bottleneck['name'] if bottleneck else path['bottleneck_node_id']
                
                suggestion = OptimizationSuggestion(
                    id=self._generate_id("OPT"),
                    optimization_type=OptimizationType.PARTITIONING,
                    target_node_ids=[path['bottleneck_node_id']],
                    title=f"优化瓶颈节点 {bottleneck_name}",
                    description=f"路径 {path['name']} 存在瓶颈，总延迟 {path['total_latency_ms']:.0f}ms",
                    expected_improvement=35.0,
                    implementation_effort="medium",
                    priority=1,
                    prerequisites=["分析瓶颈原因"],
                    implementation_steps=[
                        "分析节点性能瓶颈原因",
                        "考虑数据分区策略",
                        "优化处理逻辑",
                        "必要时进行水平扩展"
                    ],
                    estimated_impact={
                        "latency_reduction": "30-50%",
                        "throughput_increase": "显著"
                    }
                )
                suggestions.append(suggestion)
        
        return suggestions
    
    def _save_optimization_suggestion(self, suggestion: OptimizationSuggestion):
        """
        保存优化建议到数据库
        
        参数:
            suggestion: 建议对象
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            now = datetime.now().isoformat()
            
            cursor.execute('''
                INSERT INTO optimization_suggestions 
                (id, optimization_type, target_node_ids, title, description,
                 expected_improvement, implementation_effort, priority,
                 prerequisites, implementation_steps, estimated_impact, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (suggestion.id, suggestion.optimization_type.value,
                  json.dumps(suggestion.target_node_ids),
                  suggestion.title, suggestion.description,
                  suggestion.expected_improvement, suggestion.implementation_effort,
                  suggestion.priority,
                  json.dumps(suggestion.prerequisites, ensure_ascii=False),
                  json.dumps(suggestion.implementation_steps, ensure_ascii=False),
                  json.dumps(suggestion.estimated_impact, ensure_ascii=False), now))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"保存优化建议失败: {e}")
    
    def generate_analysis_report(self, flow_name: str = "数据流分析") -> DataFlowAnalysisReport:
        """
        生成数据流分析报告
        
        执行完整的数据流分析，生成综合报告。
        
        分析内容:
        1. 收集所有节点和边信息
        2. 追踪所有数据流路径
        3. 识别转换问题
        4. 生成优化建议
        5. 计算效率指标
        6. 生成分析摘要
        
        参数:
            flow_name: 数据流名称
        
        返回:
            DataFlowAnalysisReport: 分析报告
        """
        logger.info(f"开始生成数据流分析报告: {flow_name}")
        
        report_id = self._generate_id("RPT")
        
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute('SELECT * FROM data_flow_nodes')
            nodes_data = cursor.fetchall()
            nodes = [
                DataFlowNode(
                    id=row['id'],
                    name=row['name'],
                    node_type=DataFlowNodeType(row['node_type']),
                    description=row['description'] or "",
                    status=DataFlowStatus(row['status']),
                    input_schema=json.loads(row['input_schema']) if row['input_schema'] else {},
                    output_schema=json.loads(row['output_schema']) if row['output_schema'] else {},
                    processing_time_ms=row['processing_time_ms'],
                    throughput_per_sec=row['throughput_per_sec'],
                    error_rate=row['error_rate'],
                    memory_usage_mb=row['memory_usage_mb'],
                    cpu_usage_percent=row['cpu_usage_percent'],
                    metadata=json.loads(row['metadata']) if row['metadata'] else {}
                )
                for row in nodes_data
            ]
            
            cursor.execute('SELECT * FROM data_flow_edges')
            edges_data = cursor.fetchall()
            edges = [
                DataFlowEdge(
                    id=row['id'],
                    source_node_id=row['source_node_id'],
                    target_node_id=row['target_node_id'],
                    data_format=row['data_format'],
                    average_size_bytes=row['average_size_bytes'],
                    transfer_rate_per_sec=row['transfer_rate_per_sec'],
                    latency_ms=row['latency_ms'],
                    compression_enabled=bool(row['compression_enabled']),
                    encryption_enabled=bool(row['encryption_enabled']),
                    is_async=bool(row['is_async'])
                )
                for row in edges_data
            ]
            
            cursor.execute('SELECT * FROM data_flow_paths')
            paths_data = cursor.fetchall()
            paths = [
                DataFlowPath(
                    id=row['id'],
                    name=row['name'],
                    source_node_id=row['source_node_id'],
                    sink_node_id=row['sink_node_id'],
                    node_ids=json.loads(row['node_ids']) if row['node_ids'] else [],
                    edge_ids=json.loads(row['edge_ids']) if row['edge_ids'] else [],
                    total_latency_ms=row['total_latency_ms'],
                    total_processing_time_ms=row['total_processing_time_ms'],
                    data_transformations=row['data_transformations'],
                    bottleneck_node_id=row['bottleneck_node_id']
                )
                for row in paths_data
            ]
            
            conn.close()
            
            transform_issues = self.identify_transform_issues()
            optimization_suggestions = self.generate_optimization_suggestions()
            
            efficiency_metrics = self._calculate_efficiency_metrics(nodes, edges, paths, transform_issues)
            
            summary = self._generate_summary(nodes, edges, paths, transform_issues, optimization_suggestions)
            
            report = DataFlowAnalysisReport(
                id=report_id,
                flow_name=flow_name,
                nodes=nodes,
                edges=edges,
                paths=paths,
                transform_issues=transform_issues,
                optimization_suggestions=optimization_suggestions,
                efficiency_metrics=efficiency_metrics,
                summary=summary
            )
            
            self._save_report(report)
            
            logger.info(f"数据流分析报告生成完成: {report_id}")
            
            return report
            
        except Exception as e:
            logger.error(f"生成数据流分析报告失败: {e}")
            raise
    
    def _calculate_efficiency_metrics(self,
                                      nodes: List[DataFlowNode],
                                      edges: List[DataFlowEdge],
                                      paths: List[DataFlowPath],
                                      issues: List[TransformIssue]) -> EfficiencyMetrics:
        """
        计算效率指标
        
        参数:
            nodes: 节点列表
            edges: 边列表
            paths: 路径列表
            issues: 问题列表
        
        返回:
            EfficiencyMetrics: 效率指标
        """
        total_throughput = sum(n.throughput_per_sec for n in nodes if n.throughput_per_sec > 0)
        
        latencies = [e.latency_ms for e in edges if e.latency_ms > 0]
        average_latency = sum(latencies) / len(latencies) if latencies else 0
        p99_latency = sorted(latencies)[int(len(latencies) * 0.99)] if len(latencies) > 10 else average_latency
        
        error_rates = [n.error_rate for n in nodes if n.error_rate > 0]
        avg_error_rate = sum(error_rates) / len(error_rates) if error_rates else 0
        
        resource_utilization = {
            "avg_cpu_percent": sum(n.cpu_usage_percent for n in nodes) / len(nodes) if nodes else 0,
            "avg_memory_mb": sum(n.memory_usage_mb for n in nodes) / len(nodes) if nodes else 0,
            "max_cpu_percent": max((n.cpu_usage_percent for n in nodes), default=0),
            "max_memory_mb": max((n.memory_usage_mb for n in nodes), default=0)
        }
        
        critical_issues = sum(1 for i in issues if i.severity in [IssueSeverity.CRITICAL, IssueSeverity.HIGH])
        data_quality_score = max(0, 100 - critical_issues * 10)
        
        bottleneck_score = 0
        if paths:
            slow_paths = sum(1 for p in paths if p.total_latency_ms > self.PERFORMANCE_THRESHOLDS['high_latency_ms'])
            bottleneck_score = min(100, slow_paths * 20)
        
        optimization_potential = 0
        if optimization_suggestions := []:
            pass
        optimization_potential = min(100, len([s for s in [] if s.priority <= 2]) * 15)
        
        return EfficiencyMetrics(
            total_throughput=total_throughput,
            average_latency_ms=average_latency,
            p99_latency_ms=p99_latency,
            error_rate=avg_error_rate,
            resource_utilization=resource_utilization,
            data_quality_score=data_quality_score,
            bottleneck_score=bottleneck_score,
            optimization_potential=optimization_potential
        )
    
    def _generate_summary(self,
                          nodes: List[DataFlowNode],
                          edges: List[DataFlowEdge],
                          paths: List[DataFlowPath],
                          issues: List[TransformIssue],
                          suggestions: List[OptimizationSuggestion]) -> Dict[str, Any]:
        """
        生成分析摘要
        
        参数:
            nodes: 节点列表
            edges: 边列表
            paths: 路径列表
            issues: 问题列表
            suggestions: 建议列表
        
        返回:
            Dict[str, Any]: 摘要字典
        """
        nodes_by_type = {}
        for node in nodes:
            node_type = node.node_type.value
            nodes_by_type[node_type] = nodes_by_type.get(node_type, 0) + 1
        
        issues_by_severity = {}
        for issue in issues:
            severity = issue.severity.value
            issues_by_severity[severity] = issues_by_severity.get(severity, 0) + 1
        
        suggestions_by_type = {}
        for suggestion in suggestions:
            opt_type = suggestion.optimization_type.value
            suggestions_by_type[opt_type] = suggestions_by_type.get(opt_type, 0) + 1
        
        critical_nodes = [
            n.name for n in nodes
            if n.error_rate > self.PERFORMANCE_THRESHOLDS['high_error_rate']
            or n.cpu_usage_percent > self.PERFORMANCE_THRESHOLDS['high_cpu_percent']
        ]
        
        return {
            "total_nodes": len(nodes),
            "total_edges": len(edges),
            "total_paths": len(paths),
            "nodes_by_type": nodes_by_type,
            "total_issues": len(issues),
            "issues_by_severity": issues_by_severity,
            "total_suggestions": len(suggestions),
            "suggestions_by_type": suggestions_by_type,
            "critical_nodes": critical_nodes,
            "health_status": self._determine_health_status(issues, nodes),
            "recommendations": self._generate_top_recommendations(issues, suggestions)
        }
    
    def _determine_health_status(self,
                                 issues: List[TransformIssue],
                                 nodes: List[DataFlowNode]) -> str:
        """
        确定系统健康状态
        
        参数:
            issues: 问题列表
            nodes: 节点列表
        
        返回:
            str: 健康状态
        """
        critical_count = sum(1 for i in issues if i.severity == IssueSeverity.CRITICAL)
        high_count = sum(1 for i in issues if i.severity == IssueSeverity.HIGH)
        
        error_nodes = sum(1 for n in nodes if n.status == DataFlowStatus.ERROR)
        
        if critical_count > 0 or error_nodes > 0:
            return "critical"
        elif high_count > 3:
            return "warning"
        elif high_count > 0:
            return "attention_needed"
        else:
            return "healthy"
    
    def _generate_top_recommendations(self,
                                      issues: List[TransformIssue],
                                      suggestions: List[OptimizationSuggestion]) -> List[str]:
        """
        生成优先级最高的建议
        
        参数:
            issues: 问题列表
            suggestions: 建议列表
        
        返回:
            List[str]: 建议列表
        """
        recommendations = []
        
        critical_issues = [i for i in issues if i.severity == IssueSeverity.CRITICAL]
        if critical_issues:
            recommendations.append(f"立即处理 {len(critical_issues)} 个严重问题")
        
        high_priority_suggestions = sorted(
            [s for s in suggestions if s.priority <= 2],
            key=lambda x: x.priority
        )[:5]
        
        for suggestion in high_priority_suggestions:
            recommendations.append(f"{suggestion.title}: 预期改进 {suggestion.expected_improvement}%")
        
        return recommendations[:10]
    
    def _save_report(self, report: DataFlowAnalysisReport):
        """
        保存报告到数据库
        
        参数:
            report: 报告对象
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO analysis_reports (id, flow_name, report_data, generated_at)
                VALUES (?, ?, ?, ?)
            ''', (report.id, report.flow_name,
                  json.dumps(report.to_dict(), ensure_ascii=False),
                  report.generated_at))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"保存报告失败: {e}")
    
    def export_report(self, report: DataFlowAnalysisReport, format: str = "markdown") -> str:
        """
        导出报告为指定格式
        
        参数:
            report: 报告对象
            format: 输出格式（markdown/json）
        
        返回:
            str: 格式化的报告内容
        """
        if format == "markdown":
            return self._report_to_markdown(report)
        elif format == "json":
            return json.dumps(report.to_dict(), ensure_ascii=False, indent=2)
        else:
            raise ValueError(f"不支持的格式: {format}")
    
    def _report_to_markdown(self, report: DataFlowAnalysisReport) -> str:
        """
        将报告转换为Markdown格式
        
        参数:
            report: 报告对象
        
        返回:
            str: Markdown格式的报告
        """
        lines = [
            f"# {report.flow_name} - 数据流分析报告",
            "",
            f"**报告ID**: {report.id}",
            f"**生成时间**: {report.generated_at}",
            "",
            "## 执行摘要",
            "",
            f"- **总节点数**: {report.summary.get('total_nodes', 0)}",
            f"- **总边数**: {report.summary.get('total_edges', 0)}",
            f"- **数据流路径**: {report.summary.get('total_paths', 0)}",
            f"- **发现问题**: {report.summary.get('total_issues', 0)}",
            f"- **优化建议**: {report.summary.get('total_suggestions', 0)}",
            f"- **健康状态**: {report.summary.get('health_status', 'unknown')}",
            "",
        ]
        
        if report.efficiency_metrics:
            metrics = report.efficiency_metrics
            lines.extend([
                "## 效率指标",
                "",
                f"- **总吞吐量**: {metrics.total_throughput:.2f} 记录/秒",
                f"- **平均延迟**: {metrics.average_latency_ms:.2f} ms",
                f"- **P99延迟**: {metrics.p99_latency_ms:.2f} ms",
                f"- **错误率**: {metrics.error_rate*100:.2f}%",
                f"- **数据质量分数**: {metrics.data_quality_score:.1f}/100",
                f"- **瓶颈分数**: {metrics.bottleneck_score:.1f}/100",
                f"- **优化潜力**: {metrics.optimization_potential:.1f}%",
                "",
            ])
        
        lines.extend([
            "## 节点统计",
            "",
            "| 类型 | 数量 |",
            "|------|------|",
        ])
        for node_type, count in report.summary.get('nodes_by_type', {}).items():
            lines.append(f"| {node_type} | {count} |")
        
        lines.extend([
            "",
            "## 数据流节点详情",
            "",
            "| 节点ID | 名称 | 类型 | 状态 | 处理时间(ms) | 吞吐量 | 错误率 |",
            "|--------|------|------|------|--------------|--------|--------|",
        ])
        for node in report.nodes[:20]:
            lines.append(
                f"| {node.id[:15]}... | {node.name} | {node.node_type.value} | "
                f"{node.status.value} | {node.processing_time_ms:.2f} | "
                f"{node.throughput_per_sec:.2f} | {node.error_rate*100:.2f}% |"
            )
        
        lines.extend([
            "",
            "## 数据流边详情",
            "",
            "| 边ID | 源节点 | 目标节点 | 数据格式 | 延迟(ms) | 压缩 | 加密 |",
            "|------|--------|----------|----------|----------|------|------|",
        ])
        for edge in report.edges[:20]:
            lines.append(
                f"| {edge.id[:15]}... | {edge.source_node_id[:10]}... | "
                f"{edge.target_node_id[:10]}... | {edge.data_format} | "
                f"{edge.latency_ms:.2f} | {'✓' if edge.compression_enabled else '✗'} | "
                f"{'✓' if edge.encryption_enabled else '✗'} |"
            )
        
        if report.paths:
            lines.extend([
                "",
                "## 数据流路径",
                "",
                "| 路径名称 | 节点数 | 总延迟(ms) | 总处理时间(ms) | 转换次数 | 瓶颈节点 |",
                "|----------|--------|------------|----------------|----------|----------|",
            ])
            for path in report.paths[:10]:
                bottleneck = path.bottleneck_node_id[:10] if path.bottleneck_node_id else "无"
                lines.append(
                    f"| {path.name[:30]} | {len(path.node_ids)} | "
                    f"{path.total_latency_ms:.2f} | {path.total_processing_time_ms:.2f} | "
                    f"{path.data_transformations} | {bottleneck}... |"
                )
        
        if report.transform_issues:
            lines.extend([
                "",
                "## 数据转换问题",
                "",
                "| 问题ID | 节点 | 类型 | 严重程度 | 描述 | 建议修复 |",
                "|--------|------|------|----------|------|----------|",
            ])
            for issue in report.transform_issues[:20]:
                lines.append(
                    f"| {issue.id[:15]}... | {issue.node_id[:10]}... | "
                    f"{issue.issue_type.value} | {issue.severity.value} | "
                    f"{issue.description[:30]}... | {issue.suggested_fix[:30]}... |"
                )
        
        if report.optimization_suggestions:
            lines.extend([
                "",
                "## 优化建议",
                "",
                "| 建议ID | 类型 | 标题 | 预期改进 | 实施难度 | 优先级 |",
                "|--------|------|------|----------|----------|--------|",
            ])
            for suggestion in report.optimization_suggestions[:20]:
                lines.append(
                    f"| {suggestion.id[:15]}... | {suggestion.optimization_type.value} | "
                    f"{suggestion.title[:30]} | {suggestion.expected_improvement:.1f}% | "
                    f"{suggestion.implementation_effort} | {suggestion.priority} |"
                )
        
        lines.extend([
            "",
            "## 优先建议",
            "",
        ])
        for i, rec in enumerate(report.summary.get('recommendations', []), 1):
            lines.append(f"{i}. {rec}")
        
        return '\n'.join(lines)


def main():
    """
    主函数 - 测试数据流分析器
    
    演示分析器的主要功能：
    1. 注册数据流节点和边
    2. 追踪数据流路径
    3. 识别转换问题
    4. 生成优化建议
    5. 生成分析报告
    """
    analyzer = DataFlowAnalyzer("test_data_flow.db")
    
    print("=" * 60)
    print("数据流分析器测试")
    print("=" * 60)
    
    print("\n1. 注册数据流节点...")
    source = analyzer.register_node(
        name="用户数据源",
        node_type=DataFlowNodeType.SOURCE,
        description="从数据库读取用户数据",
        throughput_per_sec=1000,
        processing_time_ms=5
    )
    print(f"   源节点: {source.id}")
    
    transform1 = analyzer.register_node(
        name="数据清洗",
        node_type=DataFlowNodeType.TRANSFORM,
        description="清洗和标准化用户数据",
        throughput_per_sec=800,
        processing_time_ms=50,
        error_rate=0.02,
        input_schema={"fields": {"raw_data": {"type": "string"}}},
        output_schema={"fields": {"user_id": {"type": "integer"}, "name": {"type": "string"}}}
    )
    print(f"   转换节点: {transform1.id}")
    
    transform2 = analyzer.register_node(
        name="数据验证",
        node_type=DataFlowNodeType.FILTER,
        description="验证数据完整性和正确性",
        throughput_per_sec=750,
        processing_time_ms=30,
        error_rate=0.05
    )
    print(f"   过滤节点: {transform2.id}")
    
    sink = analyzer.register_node(
        name="数据仓库",
        node_type=DataFlowNodeType.SINK,
        description="写入数据仓库",
        throughput_per_sec=600,
        processing_time_ms=100
    )
    print(f"   目标节点: {sink.id}")
    
    print("\n2. 注册数据流边...")
    edge1 = analyzer.register_edge(
        source_node_id=source.id,
        target_node_id=transform1.id,
        data_format="json",
        average_size_bytes=2048,
        latency_ms=10
    )
    print(f"   边1: {source.name} -> {transform1.name}")
    
    edge2 = analyzer.register_edge(
        source_node_id=transform1.id,
        target_node_id=transform2.id,
        data_format="json",
        average_size_bytes=1536,
        latency_ms=5
    )
    print(f"   边2: {transform1.name} -> {transform2.name}")
    
    edge3 = analyzer.register_edge(
        source_node_id=transform2.id,
        target_node_id=sink.id,
        data_format="json",
        average_size_bytes=1024,
        latency_ms=20
    )
    print(f"   边3: {transform2.name} -> {sink.name}")
    
    print("\n3. 追踪数据流路径...")
    paths = analyzer.trace_data_flow(source.id)
    print(f"   发现 {len(paths)} 条数据流路径")
    for path in paths:
        print(f"   - {path.name}")
        print(f"     总延迟: {path.total_latency_ms:.2f}ms")
        print(f"     总处理时间: {path.total_processing_time_ms:.2f}ms")
    
    print("\n4. 识别数据转换问题...")
    issues = analyzer.identify_transform_issues()
    print(f"   发现 {len(issues)} 个问题")
    for issue in issues[:5]:
        print(f"   - [{issue.severity.value}] {issue.description}")
    
    print("\n5. 生成优化建议...")
    suggestions = analyzer.generate_optimization_suggestions()
    print(f"   生成 {len(suggestions)} 条建议")
    for suggestion in suggestions[:5]:
        print(f"   - {suggestion.title} (预期改进: {suggestion.expected_improvement}%)")
    
    print("\n6. 生成分析报告...")
    report = analyzer.generate_analysis_report("用户数据处理流程")
    print(f"   报告ID: {report.id}")
    print(f"   健康状态: {report.summary.get('health_status', 'unknown')}")
    
    print("\n" + "=" * 60)
    print("Markdown报告预览")
    print("=" * 60)
    md_report = analyzer.export_report(report, "markdown")
    print(md_report[:2000])
    
    import os
    if os.path.exists("test_data_flow.db"):
        os.remove("test_data_flow.db")
        print("\n清理测试数据库")


if __name__ == "__main__":
    main()
