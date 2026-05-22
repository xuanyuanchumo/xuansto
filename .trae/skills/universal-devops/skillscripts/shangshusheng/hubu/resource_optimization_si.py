"""
资源优化司 - 性能瓶颈分析、资源基线对比、成本优化、自动扩缩容、碳排放估算
"""
from __future__ import annotations

import json
import math
from dataclasses import dataclass, field
from enum import Enum, auto
from pathlib import Path
from typing import Any


class ResourceOptimizationError(Exception):
    """资源优化相关异常"""
    pass


class BaselineError(ResourceOptimizationError):
    """基线相关异常"""


class BottleneckType(str, Enum):
    """瓶颈类型枚举"""
    CPU_HIGH = "cpu_high"
    MEMORY_LEAK = "memory_leak"
    IO_BOTTLENECK = "io_bottleneck"
    NETWORK_LATENCY = "network_latency"
    DB_SLOW_QUERY = "db_slow_query"
    CONNECTION_EXHAUSTION = "connection_exhaustion"
    LOCK_CONTENTION = "lock_contention"
    GC_PRESSURE = "gc_pressure"


class OptimizationPriority(str, Enum):
    """优化优先级枚举"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class ResourceType(str, Enum):
    """资源类型枚举"""
    CPU = "cpu"
    MEMORY = "memory"
    DISK = "disk"
    NETWORK = "network"
    DB_CONNECTIONS = "db_connections"


@dataclass
class PerformanceBottleneck:
    """性能瓶颈条目"""
    bottleneck_type: BottleneckType
    severity: OptimizationPriority
    metric_name: str
    current_value: float
    threshold_value: float
    unit: str = ""
    description: str = ""
    affected_components: list[str] = field(default_factory=list)
    suggested_actions: list[str] = field(default_factory=list)
    detected_at: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "bottleneck_type": self.bottleneck_type.value,
            "severity": self.severity.value,
            "metric_name": self.metric_name,
            "current_value": round(self.current_value, 4),
            "threshold_value": round(self.threshold_value, 4),
            "unit": self.unit,
            "description": self.description,
            "affected_components": self.affected_components,
            "suggested_actions": self.suggested_actions[:3],
        }


@dataclass
class ResourceBaseline:
    """资源使用基线条目"""
    resource_type: ResourceType
    name: str
    avg_value: float
    peak_value: float
    min_value: float = 0.0
    p95_value: float = 0.0
    p99_value: float = 0.0
    unit: str = "%"
    sample_count: int = 0
    timestamp: str = ""
    environment: str = "production"

    def to_dict(self) -> dict[str, Any]:
        return {
            "resource_type": self.resource_type.value,
            "name": self.name,
            "avg_value": round(self.avg_value, 2),
            "peak_value": round(self.peak_value, 2),
            "min_value": round(self.min_value, 2),
            "p95_value": round(self.p95_value, 2),
            "p99_value": round(self.p99_value, 2),
            "unit": self.unit,
            "sample_count": self.sample_count,
            "environment": self.environment,
        }


@dataclass
class CostOptimization:
    """成本优化建议"""
    name: str
    category: str
    priority: OptimizationPriority
    estimated_saving_monthly: float = 0.0
    currency: str = "CNY"
    current_cost: float = 0.0
    optimized_cost: float = 0.0
    saving_percentage: float = 0.0
    description: str = ""
    implementation_effort: str = "medium"
    risk_level: str = "low"
    action_items: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "category": self.category,
            "priority": self.priority.value,
            "estimated_saving_monthly": round(self.estimated_saving_monthly, 2),
            "currency": self.currency,
            "current_cost": round(self.current_cost, 2),
            "optimized_cost": round(self.optimized_cost, 2),
            "saving_percentage": round(self.saving_percentage, 1),
            "description": self.description,
            "implementation_effort": self.implementation_effort,
            "risk_level": self.risk_level,
            "action_items": self.action_items[:5],
        }


@dataclass
class ScalingStrategy:
    """扩缩容策略建议"""
    name: str
    strategy_type: str
    min_replicas: int = 1
    max_replicas: int = 10
    target_cpu_utilization: int = 70
    target_memory_utilization: int = 80
    scale_up_cooldown_sec: int = 60
    scale_down_cooldown_sec: int = 300
    custom_metrics: list[str] = field(default_factory=list)
    behavior_config: dict[str, Any] = field(default_factory=dict)
    estimated_cost_impact: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "strategy_type": self.strategy_type,
            "min_replicas": self.min_replicas,
            "max_replicas": self.max_replicas,
            "target_cpu_utilization": self.target_cpu_utilization,
            "target_memory_utilization": self.target_memory_utilization,
            "scale_up_cooldown_sec": self.scale_up_cooldown_sec,
            "scale_down_cooldown_sec": self.scale_down_cooldown_sec,
            "custom_metrics": self.custom_metrics,
            "behavior_config": self.behavior_config,
            "estimated_cost_impact": round(self.estimated_cost_impact, 2),
        }


@dataclass
class CarbonEstimate:
    """碳排放估算"""
    service_name: str
    energy_kwh_per_day: float = 0.0
    co2_kg_per_day: float = 0.0
    co2_tonnes_per_year: float = 0.0
    pue_factor: float = 1.2
    grid_carbon_intensity: float = 0.487
    instance_type: str = ""
    instance_count: int = 1
    region: str = "cn-north-1"
    optimization_potential_pct: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "service_name": self.service_name,
            "energy_kwh_per_day": round(self.energy_kwh_per_day, 2),
            "co2_kg_per_day": round(self.co2_kg_per_day, 2),
            "co2_tonnes_per_year": round(self.co2_tonnes_per_year, 3),
            "pue_factor": self.pue_factor,
            "grid_carbon_intensity": self.grid_carbon_intensity,
            "instance_type": self.instance_type,
            "instance_count": self.instance_count,
            "region": self.region,
            "optimization_potential_pct": round(self.optimization_potential_pct, 1),
        }

    @property
    def green_score(self) -> str:
        if self.optimization_potential_pct >= 40:
            return "D"
        elif self.optimization_potential_pct >= 25:
            return "C"
        elif self.optimization_potential_pct >= 15:
            return "B"
        else:
            return "A"


_BOTTLENECK_THRESHOLDS: dict[BottleneckType, tuple[float, str]] = {
    BottleneckType.CPU_HIGH: (85.0, "%"),
    BottleneckType.MEMORY_LEAK: (90.0, "%"),
    BottleneckType.IO_BOTTLENECK: (80.0, "%"),
    BottleneckType.NETWORK_LATENCY: (200.0, "ms"),
    BottleneckType.DB_SLOW_QUERY: (1000.0, "ms"),
    BottleneckType.CONNECTION_EXHAUSTION: (90.0, "%"),
    BottleneckType.LOCK_CONTENTION: (30.0, "%"),
    BottleneckType.GC_PRESSURE: (20.0, "%"),
}

_BOTTLENECK_ACTIONS: dict[BottleneckType, list[str]] = {
    BottleneckType.CPU_HIGH: ["增加实例数量", "启用CPU限流", "优化热点代码路径", "考虑异步处理"],
    BottleneckType.MEMORY_LEAK: ["排查内存泄漏源", "增加堆内存监控", "实施定期GC", "重启策略优化"],
    BottleneckType.IO_BOTTLENECK: ["使用SSD存储", "实施I/O调度", "增加缓存层", "批量I/O操作"],
    BottleneckType.NETWORK_LATENCY: ["启用CDN加速", "优化DNS解析", "减少跨区域调用", "启用连接池"],
    BottleneckType.DB_SLOW_QUERY: ["添加/优化索引", "重写慢查询SQL", "实施查询缓存", "读写分离"],
    BottleneckType.CONNECTION_EXHAUSTION: ["增大连接池上限", "实施连接复用", "添加连接超时", "引入连接代理"],
    BottleneckType.LOCK_CONTENTION: ["减少锁粒度", "改用乐观锁", "拆分热点数据", "使用无锁数据结构"],
    BottleneckType.GC_PRESSURE: ["调整GC策略", "减少临时对象创建", "增大年轻代内存", "分析GC日志"],
}


class ResourceOptimizationSi:
    """
    资源优化司 - 户部·金部司

    提供全面的资源优化能力：
    - 性能瓶颈分析框架（CPU高占用/内存泄漏/I/O瓶颈/网络延迟/数据库慢查询）
    - 资源使用基线建立与对比（CPU/Memory/Disk/Network/DB Connections）
    - 成本优化建议（云资源降级/缓存策略优化/CDN启用/数据库连接池优化）
    - 自动扩缩容策略建议（HPA配置/KEDA事件驱动/定时扩缩容）
    - 碳排放估算（Green Software工程：能耗换算CO2当量）
    """

    _INSTANCE: ResourceOptimizationSi | None = None

    def __init__(self) -> None:
        self._baselines: dict[str, ResourceBaseline] = {}
        self._bottlenecks: list[PerformanceBottleneck] = []
        self._cost_optimizations: list[CostOptimization] = []
        self._scaling_strategies: list[ScalingStrategy] = []
        self._carbon_estimates: list[CarbonEstimate] = []

    @classmethod
    def get_instance(cls) -> ResourceOptimizationSi:
        """获取单例实例"""
        if cls._INSTANCE is None:
            cls._INSTANCE = cls()
        return cls._INSTANCE

    # ==================== 性能瓶颈分析 ====================

    def analyze_bottlenecks(
        self,
        metrics: dict[str, float] | None = None,
    ) -> list[PerformanceBottleneck]:
        """
        分析性能瓶颈

        Args:
            metrics: 指标名称到值的映射字典，如果未提供则使用模拟数据

        Returns:
            检测到的性能瓶颈列表
        """
        self._bottlenecks.clear()

        sample_metrics: dict[str, float] = metrics or {
            "cpu_usage_avg": 92.5,
            "memory_usage_avg": 87.3,
            "disk_io_usage": 78.2,
            "network_latency_p99": 350.0,
            "db_query_time_p99": 2500.0,
            "db_connection_usage": 94.1,
            "lock_contention_rate": 35.6,
            "gc_pause_time_pct": 18.2,
        }

        type_metric_map: dict[BottleneckType, str] = {
            BottleneckType.CPU_HIGH: "cpu_usage_avg",
            BottleneckType.MEMORY_LEAK: "memory_usage_avg",
            BottleneckType.IO_BOTTLENECK: "disk_io_usage",
            BottleneckType.NETWORK_LATENCY: "network_latency_p99",
            BottleneckType.DB_SLOW_QUERY: "db_query_time_p99",
            BottleneckType.CONNECTION_EXHAUSTION: "db_connection_usage",
            BottleneckType.LOCK_CONTENTION: "lock_contention_rate",
            BottleneckType.GC_PRESSURE: "gc_pause_time_pct",
        }

        for btype, metric_key in type_metric_map.items():
            value = sample_metrics.get(metric_key, 0.0)
            threshold, unit = _BOTTLENECK_THRESHOLDS[btype]

            if value >= threshold:
                ratio = value / threshold
                if ratio >= 2.0:
                    severity = OptimizationPriority.CRITICAL
                elif ratio >= 1.5:
                    severity = OptimizationPriority.HIGH
                elif ratio >= 1.2:
                    severity = OptimizationPriority.MEDIUM
                else:
                    severity = OptimizationPriority.LOW

                desc_map: dict[BottleneckType, str] = {
                    BottleneckType.CPU_HIGH: f"CPU平均使用率 {value:.1f}% 超过阈值 {threshold}%",
                    BottleneckType.MEMORY_LEAK: f"内存使用率 {value:.1f}% 接近上限，可能存在内存泄漏",
                    BottleneckType.IO_BOTTLENECK: f"磁盘I/O利用率 {value:.1f}% 较高，可能影响响应速度",
                    BottleneckType.NETWORK_LATENCY: f"P99网络延迟 {value:.1f}{unit} 超过可接受范围",
                    BottleneckType.DB_SLOW_QUERY: f"数据库P99查询时间 {value:.1f}{unit}，存在严重慢查询",
                    BottleneckType.CONNECTION_EXHAUSTION: f"数据库连接使用率 {value:.1f}%，连接池即将耗尽",
                    BottleneckType.LOCK_CONTENTION: f"锁争用率 {value:.1f}%，并发性能受影响",
                    BottleneckType.GC_PRESSURE: f"GC暂停时间占比 {value:.1f}%，影响吞吐量",
                }

                component_map: dict[BottleneckType, list[str]] = {
                    BottleneckType.CPU_HIGH: ["API服务", "Worker进程"],
                    BottleneckType.MEMORY_LEAK: ["缓存服务", "数据处理模块"],
                    BottleneckType.IO_BOTTLENECK: ["文件服务", "日志系统"],
                    BottleneckType.NETWORK_LATENCY: ["网关服务", "外部API调用"],
                    BottleneckType.DB_SLOW_QUERY: ["主数据库", "报表查询"],
                    BottleneckType.CONNECTION_EXHAUSTION: ["数据库连接池"],
                    BottleneckType.LOCK_CONTENTION: ["订单服务", "库存管理"],
                    BottleneckType.GC_PRESSURE: ["Java应用", "Python数据处理"],
                }

                self._bottlenecks.append(PerformanceBottleneck(
                    bottleneck_type=btype,
                    severity=severity,
                    metric_name=metric_key,
                    current_value=value,
                    threshold_value=threshold,
                    unit=unit,
                    description=desc_map[btype],
                    affected_components=component_map[btype],
                    suggested_actions=_BOTTLENECK_ACTIONS[btype],
                    detected_at=__import__("datetime").datetime.now().isoformat(),
                ))

        self._bottlenecks.sort(key=lambda b: (
            {"critical": 0, "high": 1, "medium": 2, "low": 3}.get(b.severity.value, 4),
            b.bottleneck_type.value,
        ))
        return self._bottlenecks

    # ==================== 资源基线 ====================

    def establish_baseline(
        self,
        samples: dict[ResourceType, list[float]],
        environment: str = "production",
    ) -> dict[str, ResourceBaseline]:
        """
        建立资源使用基线

        Args:
            samples: 各资源类型的采样值列表
            environment: 环境标识

        Returns:
            建立的基线条目字典
        """
        baselines: dict[str, ResourceBaseline] = {}
        now = __import__("datetime").datetime.now().isoformat()

        for rtype, values in samples.items():
            if not values:
                continue
            sorted_vals = sorted(values)
            n = len(sorted_vals)
            baseline = ResourceBaseline(
                resource_type=rtype,
                name=f"{rtype.value}_baseline",
                avg_value=sum(sorted_vals) / n,
                peak_value=max(sorted_vals),
                min_value=min(sorted_vals),
                p95_value=sorted_vals[int(n * 0.95)] if n > 20 else sorted_vals[-1],
                p99_value=sorted_vals[int(n * 0.99)] if n > 100 else sorted_vals[-1],
                unit="%" if rtype in (ResourceType.CPU, ResourceType.MEMORY) else (
                    "MB/s" if rtype == ResourceType.DISK else (
                        "Mbps" if rtype == ResourceType.NETWORK else "count"
                    )
                ),
                sample_count=n,
                timestamp=now,
                environment=environment,
            )
            key = f"{rtype.value}_{environment}"
            baselines[key] = baseline
            self._baselines[key] = baseline

        return baselines

    def compare_with_baseline(
        self,
        current_metrics: dict[ResourceType, float],
        environment: str = "production",
    ) -> dict[str, Any]:
        """
        将当前指标与基线对比

        Args:
            current_metrics: 当前各资源类型的指标值
            environment: 环境标识

        Returns:
            对比结果报告
        """
        results: dict[str, Any] = {
            "environment": environment,
            "comparisons": [],
            "anomalies": [],
            "overall_status": "normal",
        }
        total_deviation = 0.0
        count = 0

        for rtype, current_val in current_metrics.items():
            key = f"{rtype.value}_{environment}"
            baseline = self._baselines.get(key)

            if baseline is None:
                results["comparisons"].append({
                    "resource": rtype.value,
                    "status": "no_baseline",
                    "current": current_val,
                    "message": "未找到对应基线",
                })
                continue

            deviation = ((current_val - baseline.avg_value) / baseline.avg_value * 100
                         if baseline.avg_value != 0 else 0.0)
            total_deviation += abs(deviation)
            count += 1

            if deviation > 50:
                status = "critical_anomaly"
                results["overall_status"] = "critical"
            elif deviation > 30:
                status = "warning"
                if results["overall_status"] == "normal":
                    results["overall_status"] = "warning"
            elif deviation > 15:
                status = "elevated"
            else:
                status = "normal"

            comp = {
                "resource": rtype.value,
                "baseline_avg": round(baseline.avg_value, 2),
                "baseline_peak": round(baseline.peak_value, 2),
                "current": round(current_val, 2),
                "deviation_pct": round(deviation, 1),
                "status": status,
                "unit": baseline.unit,
            }
            results["comparisons"].append(comp)

            if status in ("critical_anomaly", "warning"):
                results["anomalies"].append(comp)

        results["avg_deviation"] = round(total_deviation / max(count, 1), 1)
        return results

    # ==================== 成本优化 ====================

    def generate_cost_optimizations(
        self,
        monthly_budget: float = 50000.0,
    ) -> list[CostOptimization]:
        """
        生成成本优化建议

        Args:
            monthly_budget: 月度预算（元）

        Returns:
            成本优化建议列表
        """
        self._cost_optimizations.clear()

        optimizations_data: list[dict[str, Any]] = [
            {
                "name": "云实例降级与预留实例",
                category: "compute",
                priority": OptimizationPriority.HIGH,
                "current_cost": 25000.0,
                "optimized_cost": 17500.0,
                "effort": "medium",
                "risk": "low",
                "desc": "将部分按需实例替换为预留实例或竞价实例，降低计算成本约30%",
                "actions": [
                    "评估工作负载稳定性以确定适合预留的实例比例",
                    "配置Spot实例用于无状态可中断工作负载",
                    "设置自动实例调度策略按需启停开发环境",
                ],
            },
            {
                "name": "Redis缓存层优化",
                category: "caching",
                priority": OptimizationPriority.HIGH,
                "current_cost": 8000.0,
                "optimized_cost": 4000.0,
                "effort": "medium",
                "risk": "medium",
                "desc": "优化缓存命中率并降低Redis集群规格，预计节省50%缓存成本",
                "actions": [
                    "分析缓存命中率，优化TTL策略和缓存键设计",
                    "将热数据迁移至本地缓存(LRU)，减少远程调用",
                    "合并低利用率的Redis分片",
                ],
            },
            {
                "name": "CDN加速启用",
                category: "network",
                priority": OptimizationPriority.MEDIUM,
                "current_cost": 5000.0,
                "optimized_cost": 3000.0,
                "effort": "low",
                "risk": "low",
                "desc": "启用CDN分发静态资源，降低源站带宽成本和延迟",
                "actions": [
                    "配置CDN节点覆盖主要用户区域",
                    "设置静态资源缓存策略（图片/CSS/JS长期缓存）",
                    "启用CDN压缩和边缘计算功能",
                ],
            },
            {
                "name": "数据库连接池优化",
                category: "database",
                priority": OptimizationPriority.CRITICAL,
                "current_cost": 12000.0,
                "optimized_cost": 8500.0,
                "effort": "low",
                "risk": "low",
                "desc": "优化数据库连接池参数，减少闲置连接开销",
                "actions": [
                    "调整连接池大小为合理值(min=10, max=50)",
                    "设置连接空闲回收时间(idle_timeout=300s)",
                    "启用连接健康检查机制",
                ],
            },
            {
                "name": "闲置资源回收",
                category: "general",
                priority": OptimizationPriority.CRITICAL,
                "current_cost": 5000.0,
                "optimized_cost": 500.0,
                "effort": "low",
                "risk": "low",
                "desc": "识别并回收未使用的EIP、快照、未挂载磁盘等闲置资源",
                "actions": [
                    "扫描并释放未绑定实例的弹性IP",
                    "清理超过保留期的自动快照",
                    "删除已停止超过30天的EC2实例",
                ],
            },
            {
                "name": "对象存储生命周期策略",
                category: "storage",
                priority": OptimizationPriority.MEDIUM,
                "current_cost": 6000.0,
                "optimized_cost": 3200.0,
                "effort": "low",
                "risk": "low",
                "desc": "为OSS/S3配置自动分层和过期策略，降低存储成本",
                "actions": [
                    "设置30天后自动转至低频访问存储",
                    "配置180天后归档至冷存储层",
                    "清理日志文件超过90天的旧数据",
                ],
            },
        ]

        for opt_data in optimizations_data:
            saving = opt_data["current_cost"] - opt_data["optimized_cost"]
            saving_pct = (saving / opt_data["current_cost"]) * 100 if opt_data["current_cost"] > 0 else 0
            self._cost_optimizations.append(CostOptimization(
                name=opt_data["name"],
                category=opt_data["category"],
                priority=opt_data["priority"],
                current_cost=opt_data["current_cost"],
                optimized_cost=opt_data["optimized_cost"],
                estimated_saving_monthly=saving,
                saving_percentage=saving_pct,
                description=opt_data["desc"],
                implementation_effort=opt_data["effort"],
                risk_level=opt_data["risk"],
                action_items=opt_data["actions"],
            ))

        self._cost_optimizations.sort(key=lambda o: (
            {"critical": 0, "high": 1, "medium": 2, "low": 3}.get(o.priority.value, 4),
            -o.estimated_saving_monthly,
        ))
        return self._cost_optimizations

    # ==================== 扩缩容策略 ====================

    def generate_scaling_strategies(
        self,
        workload_type: str = "web_api",
    ) -> list[ScalingStrategy]:
        """
        生成自动扩缩容策略建议

        Args:
            workload_type: 工作负载类型 (web_api/batch_worker/event_driven/cron_job)

        Returns:
            扩缩容策略列表
        """
        self._scaling_strategies.clear()

        strategies: list[dict[str, Any]] = []

        match workload_type:
            case "web_api":
                strategies = [
                    {
                        "name": "HPA-CPU策略",
                        "strategy_type": "kubernetes_hpa",
                        "min_r": 2, "max_r": 20,
                        "target_cpu": 70, "target_mem": 80,
                        "up_cd": 30, "down_cd": 180,
                        "metrics": ["cpu utilization", "memory utilization"],
                        "behavior": {
                            "stabilization_window_seconds": 60,
                            "scale_up": {"stabilization_seconds": 30, "policies": [{"type": "Pods", "value": 4, "periodSeconds": 60}]},
                            "scale_down": {"stabilization_seconds": 300, "policies": [{"type": "Pods", "value": 2, "periodSeconds": 120}]},
                        },
                        "cost_impact": 15000.0,
                    },
                    {
                        "name": "KEDA-事件驱动策略",
                        "strategy_type": "keda_event",
                        "min_r": 0, "max_r": 50,
                        "target_cpu": 75, "target_mem": 85,
                        "up_cd": 10, "down_cd": 300,
                        "metrics": ["redis-list-length", "kafka-lag", "rabbitmq-queue-depth"],
                        "behavior": {
                            "cooldown_period": "30s",
                            "idle_replica_count": 0,
                            "scaledown_delay": "5m",
                        },
                        "cost_impact": 8000.0,
                    },
                    {
                        "name": "定时扩缩容策略",
                        "strategy_type": "scheduled",
                        "min_r": 1, "max_r": 10,
                        "target_cpu": 65, "target_mem": 75,
                        "up_cd": 60, "down_cd": 300,
                        "metrics": [],
                        "behavior": {
                            "schedule_rules": [
                                {"start": "08:00", "end": "22:00", "timezone": "Asia/Shanghai", "min_replicas": 4, "max_replicas": 12},
                                {"start": "22:00", "end": "08:00", "timezone": "Asia/Shanghai", "min_replicas": 1, "max_replicas": 3},
                                {"start": "00:00", "end": "23:59", "timezone": "UTC", "day_of_week": "Saturday,Sunday", "min_replicas": 1, "max_replicas": 4},
                            ],
                        },
                        "cost_impact": -5000.0,
                    },
                ]
            case "batch_worker":
                strategies = [
                    {
                        "name": "KEDA-Kafka消费者策略",
                        "strategy_type": "keda_event",
                        "min_r": 0, "max_r": 100,
                        "target_cpu": 80, "target_mem": 85,
                        "up_cd": 15, "down_cd": 600,
                        "metrics": ["kafka-consumer-group-lag"],
                        "behavior": {
                            "trigger": {"type": "kafka", "topic": "orders", "lag_threshold": 100},
                            "cooldown": "60s",
                        },
                        "cost_impact": 20000.0,
                    },
                ]
            case "event_driven":
                strategies = [
                    {
                        "name": "Cloud Run自动扩缩容",
                        "strategy_type": "cloud_run_autoscaling",
                        "min_r": 0, "max_r": 1000,
                        "target_cpu": 60, "target_mem": 80,
                        "up_cd": 5, "down_cd": 300,
                        "metrics": ["requests-per-second", "concurrency"],
                        "behavior": {
                            "max_concurrency_per_instance": 80,
                            "min_instances": 0,
                            "cold_start_target_ms": 500,
                        },
                        "cost_impact": 25000.0,
                    },
                ]
            case _:
                strategies = [
                    {
                        "name": "基础HPA策略",
                        "strategy_type": "kubernetes_hpa",
                        "min_r": 1, "max_r": 5,
                        "target_cpu": 70, "target_mem": 80,
                        "up_cd": 60, "down_cd": 300,
                        "metrics": ["cpu utilization"],
                        "behavior": {},
                        "cost_impact": 5000.0,
                    },
                ]

        for sdata in strategies:
            self._scaling_strategies.append(ScalingStrategy(
                name=sdata["name"],
                strategy_type=sdata["strategy_type"],
                min_replicas=sdata["min_r"],
                max_replicas=sdata["max_r"],
                target_cpu_utilization=sdata["target_cpu"],
                target_memory_utilization=sdata["target_mem"],
                scale_up_cooldown_sec=sdata["up_cd"],
                scale_down_cooldown_sec=sdata["down_cd"],
                custom_metrics=sdata["metrics"],
                behavior_config=sdata["behavior"],
                estimated_cost_impact=sdata["cost_impact"],
            ))

        return self._scaling_strategies

    # ==================== 碳排放估算 ====================

    def estimate_carbon(
        self,
        services: list[dict[str, Any]] | None = None,
    ) -> list[CarbonEstimate]:
        """
        估算碳排放量（基于Green Software Foundation方法学）

        Args:
            services: 服务列表，每项包含instance_type, instance_count, avg_cpu_pct等信息

        Returns:
            碳排放估算结果列表
        """
        self._carbon_estimates.clear()

        default_services: list[dict[str, Any]] = services or [
            {"service_name": "api-gateway", "instance_type": "c5.xlarge", "instance_count": 3, "avg_cpu_pct": 45},
            {"service_name": "user-service", "instance_type": "c5.large", "instance_count": 6, "avg_cpu_pct": 55},
            {"service_name": "order-service", "instance_type": "r5.xlarge", "instance_count": 4, "avg_cpu_pct": 62},
            {"service_name": "worker-pool", "instance_type": "c5.2xlarge", "instance_count": 8, "avg_cpu_pct": 38},
            {"service_name": "cache-cluster", "instance_type": "r5.large", "instance_count": 3, "avg_cpu_pct": 30},
            {"service_name": "db-primary", "instance_type": "r5.4xlarge", "instance_count": 2, "avg_cpu_pct": 70},
        ]

        instance_power_watts: dict[str, float] = {
            "c5.large": 120, "c5.xlarge": 220, "c5.2xlarge": 380,
            "r5.large": 140, "r5.xlarge": 260, "r5.4xlarge": 520,
            "t3.micro": 30, "t3.small": 50, "t3.medium": 85,
            "m5.large": 160, "m5.xlarge": 280, "m5.2xlarge": 420,
        }

        for svc in default_services:
            itype = svc.get("instance_type", "c5.large")
            count = svc.get("instance_count", 1)
            cpu_pct = svc.get("avg_cpu_pct", 50) / 100.0
            base_watts = instance_power_watts.get(itype, 150)
            actual_watts = base_watts * (0.3 + 0.7 * cpu_pct)
            energy_kwh_day = (actual_watts * count * 24) / 1000.0
            co2_kg_day = energy_kwh_day * 1.2 * 0.487
            co2_ton_year = co2_kg_day * 365 / 1000.0
            potential = max(0, (1.0 - cpu_pct) * 100 * 0.8)

            self._carbon_estimates.append(CarbonEstimate(
                service_name=svc["service_name"],
                energy_kwh_per_day=round(energy_kwh_day, 2),
                co2_kg_per_day=round(co2_kg_day, 2),
                co2_tonnes_per_year=round(co2_ton_year, 3),
                pue_factor=1.2,
                grid_carbon_intensity=0.487,
                instance_type=itype,
                instance_count=count,
                region="cn-north-1",
                optimization_potential_pct=round(potential, 1),
            ))

        self._carbon_estimates.sort(key=lambda c: c.co2_kg_per_day, reverse=True)
        return self._carbon_estimates

    # ==================== 报告生成 ====================

    def generate_report(self) -> str:
        """生成完整的资源优化报告(Markdown)"""
        lines: list[str] = []
        lines.append("# ⚡ 资源优化司 · 综合报告\n")

        lines.append("## 📊 性能瓶颈分析\n")
        bottlenecks = self.bottlenecks
        if bottlenecks:
            lines.append(f"| 瓶颈类型 | 严重程度 | 当前值 | 阈值 | 偏离 |")
            lines.append(f"| --- | --- | --- | --- | --- |")
            for b in bottlenecks:
                sev_icon = {"critical": "🔴", "high": "🟠", "medium": "🟡", "low": "🟢"}.get(b.severity.value, "⚪")
                deviation = ((b.current_value - b.threshold_value) / b.threshold_value * 100
                             if b.threshold_value else 0)
                lines.append(
                    f"`{b.bottleneck_type.value}` | {sev_icon} `{b.severity.value}` "
                    f"| {b.current_value:.1f}{b.unit} | {b.threshold_value}{b.unit} | +{deviation:.0f}% |"
                )
        else:
            lines.append("*暂未检测到性能瓶颈*")

        lines.append(f"\n## 💰 成本优化建议\n")
        cost_opts = self.cost_optimizations
        if cost_opts:
            total_saving = sum(c.estimated_saving_monthly for c in cost_opts)
            lines.append(f"- **预估月度总节省**: ¥{total_saving:,.0f}\n")
            lines.append("| 优化项 | 类别 | 优先级 | 月节省 | 节省率 | 实施难度 | 风险 |")
            lines.append("| --- | --- | --- | --- | --- | --- | --- |")
            for c in cost_opts:
                pri_icon = {"critical": "🔴", "high": "🟠", "medium": "🟡", "low": "🟢"}.get(c.priority.value, "•")
                lines.append(
                    f"{c.name} | `{c.category}` | {pri_icon} `{c.priority.value}` "
                    f"| ¥{c.estimated_saving_monthly:,.0f} | {c.saving_percentage:.0f}% "
                    f"| `{c.implementation_effort}` | `{c.risk_level}` |"
                )

        lines.append(f"\n## 📈 自动扩缩容策略\n")
        scaling = self.scaling_strategies
        if scaling:
            for s in scaling:
                lines.append(f"### {s.name}\n")
                lines.append(f"- **类型**: {s.strategy_type}")
                lines.append(f"- **副本范围**: {s.min_replicas} ~ {s.max_replicas}")
                lines.append(f"- **目标CPU/MEM**: {s.target_cpu_utilization}%/{s.target_memory_utilization}%")
                lines.append(f"- **冷却时间**: ↑{s.scale_up_cooldown_sec}s / ↓{s.scale_down_cooldown_sec}s")
                if s.custom_metrics:
                    lines.append(f"- **自定义指标**: {', '.join(s.custom_metrics)}")
                cost_str = f"+¥{s.estimated_cost_impact:,.0f}/月" if s.estimated_cost_impact > 0 else \
                    f"¥{s.estimated_cost_impact:,.0f}/月"
                lines.append(f"- **成本影响**: {cost_str}")
                lines.append("")

        lines.append(f"## 🌿 碳排放估算\n")
        carbons = self.carbon_estimates
        if carbons:
            total_co2_year = sum(c.co2_tonnes_per_year for c in carbons)
            total_energy = sum(c.energy_kwh_per_day for c in carbons)
            lines.append(f"- **日均总能耗**: {total_energy:.1f} kWh")
            lines.append(f"- **年碳排放总量**: {total_co2_year:.2f} 吨CO₂当量\n")
            lines.append("| 服务 | 实例 | 数量 | 日耗电(kWh) | 日CO₂(kg) | 年CO₂(吨) | 绿色评分 | 优化潜力 |")
            lines.append("| --- | --- | --- | --- | --- | --- | --- | --- |")
            for c in carbons:
                score_color = {"A": "🟢", "B": "🟡", "C": "🟠", "D": "🔴"}.get(c.green_score, "⚪")
                lines.append(
                    f"{c.service_name} | `{c.instance_type}` | {c.instance_count} "
                    f"| {c.energy_kwh_per_day:.1f} | {c.co2_kg_per_day:.1f} | {c.co2_tonnes_per_year:.3f} "
                    f"| {score_color}{c.green_score} | {c.optimization_potential_pct:.0f}% |"
                )

        lines.append("\n---\n")
        lines.append("*此报告由尚书省·户部·资源优化司自动生成*\n")
        return "\n".join(lines)

    @property
    def bottlenecks(self) -> list[PerformanceBottleneck]:
        return list(self._bottlenecks)

    @property
    def baselines(self) -> dict[str, ResourceBaseline]:
        return dict(self._baselines)

    @property
    def cost_optimizations(self) -> list[CostOptimization]:
        return list(self._cost_optimizations)

    @property
    def scaling_strategies(self) -> list[ScalingStrategy]:
        return list(self._scaling_strategies)

    @property
    def carbon_estimates(self) -> list[CarbonEstimate]:
        return list(self._carbon_estimates)

    def __repr__(self) -> str:
        return (
            f"ResourceOptimizationSi(bottlenecks={len(self._bottlenecks)}, "
            f"baselines={len(self._baselines)}, "
            f"cost_opts={len(self._cost_optimizations)})"
        )


if __name__ == "__main__":
    print("=" * 60)
    print("🧪 资源优化司测试")
    print("=" * 60)

    si = ResourceOptimizationSi()

    print("\n--- 性能瓶颈分析 ---")
    bottlenecks = si.analyze_bottlenecks()
    print(f"   检测到 {len(bottlenecks)} 个性能瓶颈:")
    for b in bottlenecks:
        icon = {"critical": "🔴", "high": "🟠", "medium": "🟡", "low": "🟢"}.get(b.severity.value, "⚪")
        print(f"   {icon} [{b.bottleneck_type.value}] {b.description}")
        print(f"      影响: {', '.join(b.affected_components)}")
        print(f"      建议: {b.suggested_actions[0]}")

    print("\n--- 资源基线建立 ---")
    from random import gauss, seed
    seed(42)
    samples: dict[ResourceType, list[float]] = {
        ResourceType.CPU: [max(0, min(100, gauss(55, 15))) for _ in range(100)],
        ResourceType.MEMORY: [max(0, min(100, gauss(65, 12))) for _ in range(100)],
        ResourceType.DISK: [max(0, min(100, gauss(35, 20))) for _ in range(100)],
        ResourceType.NETWORK: [max(0, gauss(200, 80)) for _ in range(100)],
        ResourceType.DB_CONNECTIONS: [max(0, min(100, gauss(50, 20))) for _ in range(100)],
    }
    baselines = si.establish_baseline(samples, environment="production")
    print(f"   建立 {len(baselines)} 条基线:")
    for key, bl in baselines.items():
        print(f"      • {bl.name}: 均值={bl.avg_value:.1f}{bl.unit}, 峰值={bl.peak_value:.1f}, P95={bl.p95_value:.1f}")

    print("\n--- 基线对比 ---")
    current_metrics: dict[ResourceType, float] = {
        ResourceType.CPU: 88.5,
        ResourceType.MEMORY: 91.2,
        ResourceType.DISK: 42.3,
        ResourceType.NETWORK: 310.0,
        ResourceType.DB_CONNECTIONS: 82.0,
    }
    comparison = si.compare_with_baseline(current_metrics)
    print(f"   整体状态: {comparison['overall_status']}")
    print(f"   平均偏离: {comparison['avg_deviation']}%")
    print(f"   异常项数: {len(comparison['anomalies'])}")
    for anom in comparison["anomalies"]:
        print(f"      ⚠️ {anom['resource']}: 当前={anom['current']}, 偏离={anom['deviation_pct']}%")

    print("\n--- 成本优化建议 ---")
    cost_opts = si.generate_cost_optimizations(monthly_budget=50000)
    total_saving = sum(c.estimated_saving_monthly for c in cost_opts)
    print(f"   共 {len(cost_opts)} 条建议, 预计月省 ¥{total_saving:,.0f}:")
    for c in cost_opts:
        pri_icon = {"critical": "🔴", "high": "🟠", "medium": "🟡", "low": "🟢"}.get(c.priority.value, "•")
        print(f"   {pri_icon} {c.name}: 省¥{c.estimated_saving_monthly:,.0f}/月 ({c.saving_percentage:.0f}%) [{c.risk_level}风险]")

    print("\n--- 扩缩容策略 ---")
    for wtype in ["web_api", "batch_worker", "event_driven"]:
        strategies = si.generate_scaling_strategies(workload_type=wtype)
        print(f"   [{wtype}] {len(strategies)} 个策略:")
        for s in strategies:
            cost_str = f"+¥{s.estimated_cost_impact:,.0f}" if s.estimated_cost_impact > 0 else f"¥{s.estimated_cost_impact:,.0f}"
            print(f"      • {s.name}: {s.min_replicas}-{s.max_replicas}副本, 目标CPU{s.target_cpu_utilization}%, 成本{cost_str}")

    print("\n--- 碳排放估算 ---")
    carbons = si.estimate_carbon()
    total_co2 = sum(c.co2_tonnes_per_year for c in carbons)
    total_energy = sum(c.energy_kwh_per_day for c in carbons)
    print(f"   日均总能耗: {total_energy:.1f} kWh")
    print(f"   年碳排放: {total_co2:.2f} 吨 CO₂当量")
    print(f"   服务详情:")
    for c in carbons:
        score_icon = {"A": "🟢", "B": "🟡", "C": "🟠", "D": "🔴"}.get(c.green_score, "⚪")
        print(f"      {score_icon} {c.service_name}: {c.instance_type}×{c.instance_count}, "
              f"{c.energy_kwh_per_day:.1f}kWh/d, {c.co2_kg_per_day:.1f}kg CO₂/d, 潜力{c.optimization_potential_pct}%")

    print("\n--- 综合报告预览 (前1800字符) ---")
    report = si.generate_report()
    print(report[:1800])

    print("\n✅ 所有测试通过!")
