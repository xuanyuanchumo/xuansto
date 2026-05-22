# 资源优化司 自主操作指南 (Autonomous Operation Guide)

## 概述

资源优化司（Resource Optimization Si）是尚书省·户部下属四司之一，负责**计算资源的全维度自主优化与调度**。本司核心使命：在保障服务 SLA 的前提下，通过 8 维性能分析、成本优化、弹性扩缩容和容量规划，实现资源利用率最大化与运营成本最小化。

### 定位

- **上级机构**：尚书省 · 户部（Hubu）
- **同级司署**：环境配置司、依赖管理司、基础设施司
- **核心能力域**：性能瓶颈诊断、成本优化、HPA/KEDA 弹性调度、碳排放估算、容量规划
- **自主等级**：L3（条件自主）— 可在预设安全边界内独立执行资源调整决策
- **成本参考基准**：月度优化目标 ¥45,000+ 节省（基于中规模集群估算）

## 核心原则

1. **SLA 优先**：任何资源优化操作不得导致 SLO 违约（可用性 ≥ 99.9%，P99 延迟不退化 > 5%）
2. **渐进式调整**：单次资源变更幅度不超过当前值的 ±30%，避免剧烈波动
3. **数据驱动**：所有决策基于至少 7 天的历史数据趋势，拒绝瞬时指标驱动的冲动操作
4. **可回滚性**：每次资源调整必须保留回滚方案，MTTR ≤ 10 分钟
5. **绿色计算**：在性能等效的前提下，优先选择能效比更高的资源配置方案

## 自主操作流程

### 阶段一：感知（Perceive）

#### 1.1 八维性能瓶颈分析框架

本司采用 8 维度全方位性能扫描，系统化识别瓶颈所在：

```
┌─────────────────────────────────────────────────────────────┐
│                    8维性能瓶颈分析矩阵                        │
├──────────┬──────────────┬──────────────┬───────────────────┤
│   维度    │   检测指标     │   告警阈值     │   数据采集方式      │
├──────────┼──────────────┼──────────────┼───────────────────┤
│ ① CPU    │ 使用率/饱和度  │ >80% 持续5min │ top / prometheus   │
│ ② 内存   │ 使用率/OOM率   │ >85% / OOM>0 │ free / cAdvisor     │
│ ③ 磁盘   │ 使用率/IOPS    │ >85% / IOPS饱和│ df / iostat        │
│ ④ I/O    │ 等待时间/吞吐  │ await>10ms   │ iostat / blktrace   │
│ ⑤ 网络   │ 带宽/丢包率    │ >80% / >0.1% │ iftop / sar         │
│ ⑥ 数据库  | 连接池/QPS    │ 池满/慢查询>1s│ slow_log / pg_stat  │
│ ⑦ 缓存   | 命中率/淘汰率  │ <95% / 频繁淘汰| redis INFO          │
│ ⑧ 队列   | 积压深度/消费延迟| >1000 / >30s | rabbitmq_admin      │
└──────────┴──────────────┴──────────────┴───────────────────┘
```

**统一采集脚本**：

```bash
#!/bin/bash
# 8dim_performance_scan.sh — 8维性能瓶颈自主采集工具
set -euo pipefail
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
OUTPUT="/tmp/perf-scan-${TIMESTAMP}"
mkdir -p "${OUTPUT}"

log() { echo "[$(date '+%H:%M:%S')] $*"; }

# === 维度1: CPU ===
log "[1/8] 采集 CPU 指标..."
mpstat -P ALL 1 3 > "${OUTPUT}/cpu_mpstat.txt" 2>/dev/null || true
top -bn1 -o %CPU | head -20 > "${OUTPUT}/cpu_top.txt"
cat /proc/loadavg > "${OUTPUT}/cpu_loadavg.txt"

# === 维度2: 内存 ===
log "[2/8] 采集内存指标..."
free -h > "${OUTPUT}/mem_free.txt"
cat /proc/meminfo > "${OUTPUT}/mem_procinfo.txt"
vmstat -s > "${OUTPUT}/mem_vmstat.txt"

# === 维度3: 磁盘 ===
log "[3/8] 采集磁盘指标..."
df -h > "${OUTPUT}/disk_df.txt"
lsblk > "${OUTPUT}/disk_lsblk.txt"
iostat -dx 1 3 > "${OUTPUT}/disk_iostat.txt" 2>/dev/null || true

# === 维度4: I/O ===
log "[4/8] 采集 I/O 指标..."
iostat -x 1 3 > "${OUTPUT}/io_detail.txt" 2>/dev/null || true
cat /proc/diskstats > "${OUTPUT}/io_diskstats.txt"

# === 维度5: 网络 ===
log "[5/8] 采集网络指标..."
sar -n DEV 1 3 > "${OUTPUT}/net_sar.txt" 2>/dev/null || true
cat /proc/net/dev > "${OUTPUT}/net_dev.txt"
ss -s > "${OUTPUT}/net_ss.txt"

# === 维度6: 数据库（条件采集）===
if command -v psql &>/dev/null; then
    log "[6/8] 采集 PostgreSQL 指标..."
    PGPASSWORD="${DB_PASSWORD:-}" psql -h "${DB_HOST:-localhost}" -U "${DB_USER:-postgres}" -d "${DB_NAME:-postgres}" \
        -c "SELECT datname, numbackends, xact_commit, xact_rollback FROM pg_stat_database;" \
        > "${OUTPUT}/db_pg_stats.txt" 2>/dev/null || true
elif command -v mysql &>/dev/null; then
    log "[6/8] 采集 MySQL 指标..."
    mysql -h "${DB_HOST:-localhost}" -u "${DB_USER:-root}" -p"${DB_PASSWORD:-}" -e "SHOW STATUS LIKE 'Threads_%';" \
        > "${OUTPUT}/db_mysql_status.txt" 2>/dev/null || true
fi

# === 维度7: 缓存（Redis）===
if command -v redis-cli &>/dev/null; then
    log "[7/8] 采集 Redis 指标..."
    redis-cli -h "${REDIS_HOST:-localhost}" -p "${REDIS_PORT:-6379}" INFO stats > "${OUTPUT}/cache_redis_stats.txt" 2>/dev/null || true
    redis-cli -h "${REDIS_HOST:-localhost}" -p "${REDIS_PORT:-6379}" INFO memory > "${OUTPUT}/cache_redis_mem.txt" 2>/dev/null || true
fi

# === 维度8: 消息队列（RabbitMQ）===
if command -v rabbitmqctl &>/dev/null; then
    log "[8/8] 采集 RabbitMQ 指标..."
    rabbitmqctl list_queues name messages messages_unacknowledged consumers > "${OUTPUT}/queue_rabbitmq.txt" 2>/dev/null || true
fi

# === K8s 补充采集（如果在集群内）===
if command -v kubectl &>/dev/null; then
    log "[K8S] 采集集群资源拓扑..."
    kubectl top nodes > "${OUTPUT}/k8s_nodes.txt" 2>/dev/null || true
    kubectl top pods -A --sort-by=cpu > "${OUTPUT}/k8s_pods_cpu.txt" 2>/dev/null || true
    kubectl top pods -A --sort-by=memory > "${OUTPUT}/k8s_pods_mem.txt" 2>/dev/null || true
    kubectl get hpa -A -o wide > "${OUTPUT}/k8s_hpa.txt" 2>/dev/null || true
fi

log ""
log "========================================="
log "8维性能扫描完成！结果目录: ${OUTPUT}"
echo "${OUTPUT}"
```

#### 1.2 瓶颈智能诊断引擎

```python
"""
8维性能瓶颈诊断引擎 — 自动定位根因并生成修复建议
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional
import statistics

class BottleneckSeverity(Enum):
    CRITICAL = 5    # 立即影响服务可用性
    HIGH = 4        # 显著性能退化
    MEDIUM = 3      # 可观测到性能影响
    LOW = 2         # 潜在风险，暂未显现
    INFO = 1        # 正常，仅记录

@dataclass
class MetricPoint:
    dimension: str       # cpu/memory/disk/io/network/db/cache/queue
    metric_name: str
    value: float
    unit: str
    threshold_warning: float
    threshold_critical: float
    timestamp: str

@dataclass
class BottleneckFinding:
    dimension: str
    severity: BottleneckSeverity
    metric: str
    current_value: float
    threshold: float
    root_cause_hypothesis: str
    recommended_actions: list[str]
    estimated_impact: str
    confidence: float       # 0.0-1.0 诊断置信度

class PerformanceDiagnosticEngine:
    def __init__(self):
        self.findings: list[BottleneckFinding] = []
        self.metrics_history = {}  # 用于趋势分析

    def analyze_cpu(self, metrics: dict) -> Optional[BottleneckFinding]:
        """CPU 瓶颈分析"""
        usage_pct = metrics.get('cpu_usage_percent', 0)
        load_avg_1m = metrics.get('load_avg_1m', 0)
        cpu_count = metrics.get('cpu_count', 1)
        iowait_pct = metrics.get('iowait_percent', 0)

        # 规则1: CPU 使用率持续过高
        if usage_pct > 90:
            return BottleneckFinding(
                dimension="CPU", severity=BottleneckSeverity.CRITICAL,
                metric="cpu_usage", current_value=usage_pct,
                threshold=90.0,
                root_cause_hypothesis="CPU 计算密集型负载或无限循环",
                recommended_actions=[
                    "检查是否有异常进程占用 CPU (top -o %CPU)",
                    "分析是否可增加 Pod 副本数进行水平扩展",
                    "审查代码中的热点函数（使用 profiler）",
                    "考虑将计算密集任务异步化或 offload 到 Worker 节点"
                ],
                estimated_impact="请求延迟可能上升 200%+",
                confidence=0.92
            )

        # 规则2: IOWait 占比过高 → 实际是 I/O 瓶颈
        if iowait_pct > 30:
            return BottleneckFinding(
                dimension="I/O", severity=BottleneckSeverity.HIGH,
                metric="iowait_percent", current_value=iowait_pct,
                threshold=30.0,
                root_cause_hypothesis="CPU 大量时间等待 I/O 完成，实际瓶颈在存储层",
                recommended_actions=[
                    "检查磁盘 IOPS 是否达到上限",
                    "评估是否需要 SSD 替代 HDD 或升级存储 tier",
                    "检查数据库慢查询是否过多",
                    "考虑增加缓存层减少磁盘读取"
                ],
                estimated_impact="吞吐量下降约 40%",
                confidence=0.88
            )

        # 规则3: 负载不均衡
        if load_avg_1m > cpu_count * 0.8 and usage_pct < 70:
            return BottleneckFinding(
                dimension="CPU", severity=BottleneckSeverity.MEDIUM,
                metric="load_average", current_value=load_avg_1m,
                threshold=cpu_count * 0.8,
                root_cause_hypothesis="存在大量可运行但等待调度的进程（上下文切换开销）",
                recommended_actions=[
                    "检查线程/协程数量是否合理",
                    "分析是否存在锁竞争（strace + perf）",
                    "评估是否需要减少并发数或优化调度策略"
                ],
                estimated_impact="响应时间抖动增大",
                confidence=0.75
            )
        return None

    def analyze_memory(self, metrics: dict) -> Optional[BottleneckFinding]:
        """内存瓶颈分析"""
        usage_pct = metrics.get('memory_usage_percent', 0)
        oom_kills = metrics.get('oom_kill_count', 0)
        swap_usage_pct = metrics.get('swap_usage_percent', 0)

        if oom_kills > 0:
            return BottleneckFinding(
                dimension="内存", severity=BottleneckSeverity.CRITICAL,
                metric="oom_kills", current_value=float(oom_kills),
                threshold=0.0,
                root_cause_hypothesis="内存不足导致 OOM Killer 终止进程",
                recommended_actions=[
                    f"立即增加 memory limit（当前 {usage_pct}% 已满）",
                    "排查内存泄漏：导出 heap dump 分析对象分布",
                    "检查是否有不合理的大对象分配",
                    "临时缓解：重启服务释放碎片化内存"
                ],
                estimated_impact="服务不可用或频繁重启",
                confidence=0.98
            )

        if swap_usage_pct > 50:
            return BottleneckFinding(
                dimension="内存", severity=BottleneckSeverity.HIGH,
                metric="swap_usage", current_value=swap_usage_pct,
                threshold=50.0,
                root_cause_hypothesis="物理内存不足，频繁使用 Swap 导致严重性能退化",
                recommended_actions=[
                    "增加物理内存或调整容器 memory limit",
                    "优化应用内存使用（减少缓存大小、优化数据结构）",
                    "如果使用 K8s，确保设置了合理的 memory request/limit",
                    "禁用或限制 swap 使用（kubernetes 场景推荐）"
                ],
                estimated_impact="延迟增加 10-100倍（取决于 swap 介质速度）",
                confidence=0.95
            )
        return None

    def analyze_database(self, metrics: dict) -> Optional[BottleneckFinding]:
        """数据库瓶颈分析"""
        active_connections = metrics.get('db_active_connections', 0)
        max_connections = metrics.get('db_max_connections', 100)
        slow_query_rate = metrics.get('db_slow_query_rate', 0)  # 慢查询占比
        connection_utilization = active_connections / max_connections if max_connections > 0 else 0

        if connection_utilization > 0.85:
            return BottleneckFinding(
                dimension="数据库", severity=BottleneckSeverity.CRITICAL,
                metric="connection_pool_utilization",
                current_value=round(connection_utilization * 100, 1),
                threshold=85.0,
                root_cause_hypothesis="数据库连接池接近耗尽，新请求将被排队或拒绝",
                recommended_actions=[
                    "立即增加数据库最大连接数配置",
                    "检查是否存在连接泄漏（连接未正确释放）",
                    "审查连接池超时和空闲回收策略",
                    "评估引入连接池中间件（PgBouncer/ProxySQL）",
                    "长期方案：读写分离 + 分库分表"
                ],
                estimated_impact="数据库请求超时率飙升",
                confidence=0.94
            )

        if slow_query_rate > 0.05:  # 5% 以上为慢查询
            return BottleneckFinding(
                dimension="数据库", severity=BottleneckSeverity.HIGH,
                metric="slow_query_rate",
                current_value=round(slow_query_rate * 100, 2),
                threshold=5.0,
                root_cause_hypothesis="存在大量执行时间过长的 SQL 查询",
                recommended_actions=[
                    "启用并分析 slow query log",
                    "为高频慢查询添加合适的索引（EXPLAIN ANALYZE）",
                    "检查是否缺少必要的复合索引",
                    "评估查询重写或拆分为多次小查询",
                    "考虑对大表进行分区（partitioning）"
                ],
                estimated_impact="API 响应时间 P99 可能超过 SLO",
                confidence=0.87
            )
        return None

    def run_full_diagnosis(self, all_metrics: dict) -> list[BottleneckFinding]:
        """运行完整的 8 维诊断"""
        self.findings = []

        analyzers = [
            ("CPU", self.analyze_cpu),
            ("内存", self.analyze_memory),
            ("数据库", self.analyze_database),
            # ... 其他维度分析器类似实现
        ]

        for dim_name, analyzer in analyzers:
            dim_metrics = all_metrics.get(dim_name.lower(), {})
            finding = analyzer(dim_metrics)
            if finding:
                self.findings.append(finding)

        # 按严重程度排序
        self.findings.sort(key=lambda f: f.severity.value, reverse=True)
        return self.findings

    def generate_report(self) -> str:
        """生成结构化的诊断报告"""
        report_lines = ["# 性能诊断报告\n"]
        report_lines.append(f"| 优先级 | 维度 | 指标 | 当前值 | 阈值 | 置信度 |")
        report_lines.append("|--------|------|------|--------|------|--------|")

        for f in self.findings:
            severity_icon = {
                BottleneckSeverity.CRITICAL: "🔴",
                BottleneckSeverity.HIGH: "🟠",
                BottleneckSeverity.MEDIUM: "🟡",
                BottleneckSeverity.LOW: "🟢",
                BottleneckSeverity.INFO: "⚪",
            }[f.severity]
            report_lines.append(
                f"| {severity_icon} {f.severity.name} | {f.dimension} | "
                f"{f.metric} | {f.current_value}{f.unit if hasattr(f,'unit') else ''} | "
                f"{f.threshold} | {f.confidence:.0%} |"
            )
        report_lines.append("\n## 详细分析与建议\n")
        for f in self.findings:
            report_lines.append(f"### {f.dimension} - {f.severity.name}\n")
            report_lines.append(f"**根因假设**: {f.root_cause_hypothesis}\n\n")
            report_lines.append(f"**预期影响**: {f.estimated_impact}\n\n")
            report_lines.append("**建议操作**:\n")
            for action in f.recommended_actions:
                report_lines.append(f"- {action}")
            report_lines.append("")
        return "\n".join(report_lines)
```

### 阶段二：决策（Decide）

#### 2.1 成本优化决策引擎

```python
@dataclass
class CostOptimizationRecommendation:
    resource_type: str           # instance / disk / network / reserved
    current_config: dict
    suggested_config: dict
    monthly_savings_cny: float   # 月节省金额（人民币）
    savings_percentage: float    # 节省比例
    risk_level: str              # low / medium / high
    implementation_effort: str   # easy / moderate / complex
    confidence: float
    rationale: str

def generate_cost_optimization_recommendations(cluster_data: dict) -> list[CostOptimizationRecommendation]:
    """
    基于集群使用数据生成成本优化建议
    目标：月度节省 ¥45,000+
    """
    recommendations = []

    # === 建议1: 低利用率实例降配 ===
    for node in cluster_data['nodes']:
        cpu_avg = node['metrics']['cpu_avg_7d']
        mem_avg = node['metrics']['mem_avg_7d']
        cpu_capacity = node['spec']['cpu_cores']
        mem_capacity_gb = node['spec']['memory_gb']

        utilization_ratio = (cpu_avg / cpu_capacity + mem_avg / mem_capacity_gb) / 2

        if utilization_ratio < 0.25:  # 平均利用率低于25%
            current_cost = node['pricing']['monthly_cny']
            suggested_tier = downsize_instance(node['instance_type'], utilization_ratio)
            new_cost = get_instance_price(suggested_tier)
            savings = current_cost - new_cost

            recommendations.append(CostOptimizationRecommendation(
                resource_type="instance",
                current_config={"type": node['instance_type'], "cost": current_cost},
                suggested_config={"type": suggested_tier, "cost": new_cost},
                monthly_savings_cny=savings,
                savings_percentage=round(savings / current_cost * 100, 1),
                risk_level="low" if utilization_ratio < 0.15 else "medium",
                implementation_effort="moderate",
                confidence=0.88,
                rationale=f"7天平均利用率仅{utilization_ratio:.0%}，建议从 {node['instance_type']} 降配至 {suggested_tier}"
            ))

    # === 建议2: 未使用 EBS 卷清理 ===
    for volume in cluster_data['unattached_volumes']:
        age_days = volume['age_days']
        size_gb = volume['size_gb']
        cost_per_month = size_gb * 0.12  # gp3 价格参考

        if age_days > 30 and cost_per_month > 10:
            recommendations.append(CostOptimizationRecommendation(
                resource_type="disk",
                current_config={"volume_id": volume['id'], "size_gb": size_gb, "age_days": age_days},
                suggested_config={"action": "delete_or_snapshot"},
                monthly_savings_cny=cost_per_month,
                savings_percentage=100.0,
                risk_level="low",
                implementation_effort="easy",
                confidence=0.95,
                rationale=f"EBS 卷 {volume['id']} 已闲置 {age_days}天 ({size_gb}GB)，建议快照后删除"
            ))

    # === 建议3: RI/SP 转换（预留实例/节省计划）===
    stable_workloads = identify_stable_workloads(cluster_data, min_uptime_ratio=0.8)
    for wl in stable_workloads:
        on_demand_cost = wl['monthly_on_demand_cost']
        ri_savings = on_demand_cost * 0.4  # RI 通常节省 40%

        recommendations.append(CostOptimizationRecommendation(
            resource_type="reserved_instance",
            current_config={"billing": "on_demand", "cost": on_demand_cost},
            suggested_config={"billing": "ri_1year", "cost": on_demand_cost * 0.6},
            monthly_savings_cny=ri_savings,
            savings_percentage=40.0,
            risk_level="low",
            implementation_effort="easy",
            confidence=0.92,
            rationale=f"工作负载 '{wl['name']}' 运行稳定性 {wl['uptime_ratio']:.0%}，适合转换为预留实例"
        ))

    # 按节省金额排序
    recommendations.sort(key=lambda r: r.monthly_savings_cny, reverse=True)
    total_savings = sum(r.monthly_savings_cny for r in recommendations)

    print(f"\n💰 成本优化建议汇总:")
    print(f"   总计可节省: ¥{total_savings:,.0f}/月")
    print(f"   建议数量: {len(recommendations)} 条")

    return recommendations
```

**成本优化典型收益表（参考）**：

| 优化措施 | 适用场景 | 单项月节省 | 实施难度 | 风险 |
|---------|---------|-----------|---------|------|
| 低利用率 EC2 降配 | CPU<20% 持续7天+ | ¥2,000-8,000/台 | 中 | 低 |
| 未使用 EBS 清理 | 闲置卷 >30天 | ¥50-500/卷 | 低 | 极低 |
| On-Demand → RI | 稳定工作负载 | 节省 30-40% | 低 | 低 |
| Spot 实例替换 | 可中断批处理 | 节省 60-90% | 中 | 中 |
| 自动停止开发环境 | 非工作时间 | ¥1,000-3,000/环境 | 低 | 无 |
| S3 智能分层 | 冷数据归档 | 节省 40-60% | 低 | 无 |
| 容器 Request 合理化 | over-provisioned | ¥5,000-20,000/集群 | 高 | 中 |

#### 2.2 HPA/KEDA 扩缩容决策模型

```yaml
# hpa_decision_policy.yaml — HPA/KEDA 自主扩缩容策略
policy_version: "1.0"
si_department: "resource_optimization_si"

scaling_rules:
  - rule_id: "SR-001"
    name: "QPS驱动水平扩展"
    target_metric: "requests_per_second"
    scale_up:
      trigger: "qps_per_pod > 800"
      stabilization_window_seconds: 60
      max_replicas: 20
      step_size: 2
      cooldown_seconds: 120
    scale_down:
      trigger: "qps_per_pod < 200"
      stabilization_window_seconds: 300
      min_replicas: 2
      step_size: 1
      cooldown_seconds: 300

  - rule_id: "SR-002"
    name: "延迟驱动紧急扩展"
    target_metric: "latency_p99_ms"
    scale_up:
      trigger: "latency_p99 > 500"
      behavior: "urgent"  # 紧急模式，忽略稳定窗口
      max_replicas: 30
      step_size: 4
    scale_down:
      trigger: "latency_p99 < 100"
      stabilization_window_seconds: 600

  - rule_id: "SR-003"
    name: "内存驱动扩展"
    target_metric: "memory_usage_percent"
    scale_up:
      trigger: "memory_usage > 75%"
      stabilization_window_seconds: 60
      max_replicas: 15
    scale_down:
      trigger: "memory_usage < 40%"
      stabilization_window_seconds: 300

  - rule_id: "SR-004"
    name: "KEDA事件驱动（队列深度）"
    scaler_type: "keda"
    target: "rabbitmq_queue_length"
    queue_name: "order-processing"
    scale_up:
      trigger: "queue_depth > 500"
      threshold: 50  # 每个 worker 处理 50 条消息
      max_replicas: 50
    scale_down:
      trigger: "queue_depth == 0"
      min_replicas: 0  # 允许缩零
      cooldown_period: 300

safety_guards:
  max_total_cluster_resources:
    cpu: "128 cores"
    memory: "256Gi"
  burst_protection:
    enabled: true
    max_burst_replicas: 10
    burst_duration_limit: "15min"
  budget_protection:
    enabled: true
    max_monthly_overrun_cny: 15000
```

### 阶段三：执行（Execute）

#### 3.1 资源调整执行器

```python
"""
资源调整执行器 — 在安全边界内执行自主资源变更
"""

import subprocess
import json
from dataclasses import dataclass
from enum import Enum
from typing import Optional

class ChangeType(Enum):
    SCALE_UP = "scale_up"
    SCALE_DOWN = "scale_down"
    RESIZE = "resize"          # 改变单个 Pod 的 resources
    RIGHT_SIZING = "right_sizing"  # 调整 request/limit 比例
    SCHEDULING = "scheduling"  # 调整 nodeSelector/tolerations

@dataclass
class ResourceChange:
    change_id: str
    change_type: ChangeType
    target: str                 # deployment/statefulset/daemonset 名称
    namespace: str
    current_state: dict
    desired_state: dict
    reason: str
    rollback_state: dict
    approved: bool = False
    executed: bool = False
    verified: bool = False

class ResourceAdjustmentExecutor:
    def __init__(self, dry_run: bool = True):
        self.dry_run = dry_run
        self.change_log: list[ResourceChange] = []

    def validate_change(self, change: ResourceChange) -> tuple[bool, str]:
        """
        安全边界校验：
        1. 单次变更幅度不超过 ±30%
        2. 不低于最小保证值
        3. 不超过集群总预算
        """
        ct = change.change_type

        if ct == ChangeType.SCALE_UP:
            current_replicas = change.current_state.get('replicas', 1)
            desired_replicas = change.desired_state.get('replicas', 1)
            increase_ratio = (desired_replicas - current_replicas) / current_replicas

            if increase_ratio > 3.0:  # 不允许一次翻3倍以上
                return False, f"扩容幅度 {increase_ratio:.0%} 超过安全上限 300%"
            if desired_replicas > change.desired_state.get('max_replicas', 20):
                return False, f"期望副本数 {desired_replicas} 超过上限"

        elif ct == ChangeType.RESIZE:
            current_cpu = change.current_state.get('cpu_request', '0')
            desired_cpu = change.desired_state.get('cpu_request', '0')
            current_mem = change.current_state.get('memory_request', '0')
            desired_mem = change.desired_state.get('memory_request', '0')

            cpu_change = self._parse_resource(desired_cpu) / max(self._parse_resource(current_cpu), 1)
            mem_change = self._parse_resource(desired_mem) / max(self._parse_resource(current_mem), 1)

            if cpu_change > 1.3 or cpu_change < 0.7:
                return False, f"CPU 变更幅度 {cpu_change:.0%} 超过 ±30% 安全范围"
            if mem_change > 1.3 or mem_change < 0.7:
                return False, f"Memory 变更幅度 {mem_change:.0%} 超过 ±30% 安全范围"

        return True, "校验通过"

    def execute_change(self, change: ResourceChange) -> bool:
        """执行经过审批的资源变更"""
        valid, msg = self.validate_change(change)
        if not valid:
            print(f"[BLOCKED] 变更被安全规则拦截: {msg}")
            return False

        cmd_parts = ["kubectl"]
        if self.dry_run:
            cmd_parts.append("--dry-run=client")

        if change.change_type == ChangeType.SCALE_UP:
            replicas = change.desired_state['replicas']
            cmd_parts.extend([
                "scale", "deployment", change.target,
                "-n", change.namespace,
                f"--replicas={replicas}"
            ])
        elif change.change_type == ChangeType.RESIZE:
            cmd_parts.extend([
                "patch", "deployment", change.target,
                "-n", change.namespace,
                "--type=json", '-p=' + json.dumps([
                    {"op": "replace", "path": "/spec/template/spec/containers/0/resources/requests/cpu",
                     "value": change.desired_state.get('cpu_request', '')},
                    {"op": "replace", "path": "/spec/template/spec/containers/0/resources/requests/memory",
                     "value": change.desired_state.get('memory_request', '')}
                ])
            ])

        print(f"[EXEC] 执行命令: {' '.join(cmd_parts)}")
        result = subprocess.run(cmd_parts, capture_output=True, text=True)
        if result.returncode == 0:
            change.executed = True
            print(f"[SUCCESS] 变更 {change.change_id} 执行成功")
            return True
        else:
            print(f"[FAILED] 变更执行失败: {result.stderr}")
            return False

    @staticmethod
    def _parse_resource(value: str) -> int:
        """解析 K8s 资源字符串为 millicores / MiB"""
        if value.endswith('Gi'):
            return int(float(value[:-2]) * 1024)
        elif value.endswith('Mi'):
            return int(float(value[:-2]))
        elif value.endswith('m'):  # millicores
            return int(value[:-1])
        else:
            return int(float(value)) * 1000  # assume cores
```

#### 3.2 碳排放估算模块

```python
@dataclass
class CarbonEstimate:
    energy_kwh: float           # 能耗（千瓦时）
    co2_kg: float               # CO2 排放量（千克）
    pue_factor: float           # PUE 因子（数据中心效率）
    region: str                 # 区域（影响电网碳强度）
    grid_carbon_intensity: float  # gCO2/kWh（电网碳强度）
    equivalent_km_driven: float  # 相当于驾车公里数
    equivalent_trees: float     # 相当于种植树木数量

def estimate_carbon_footprint(
    cpu_hours: float,
    memory_gb_hours: float,
    storage_gb_hours: float,
    region: str = "cn-north-1",
    pue: float = 1.2
) -> CarbonEstimate:
    """
    估算 IT 资源的碳足迹
    参考: https://www.cloudcarbonfootprint.org/
    """
    # 各区域电网碳强度 (gCO2/kWh) — 2024年参考值
    GRID_INTENSITY = {
        "cn-north-1": 585.0,    # 华北（火电为主）
        "cn-east-1": 490.0,    # 华东（混合能源）
        "cn-south-1": 420.0,    # 华南（水电比例较高）
        "us-east-1": 380.0,    # 美国（天然气为主）
        "eu-west-1": 250.0,    # 欧洲（可再生能源占比高）
        "ap-northeast-1": 450.0, # 日本
    }

    intensity = GRID_INTENSITY.get(region, 500.0)

    # 能耗估算模型（粗略）
    # CPU: ~0.0005 kWh per core-hour (现代服务器)
    # Memory: ~0.0004 kWh per GB-hour
    # Storage (SSD): ~0.0002 kWh per GB-hour
    # Storage (HDD): ~0.0001 kWh per GB-hour

    cpu_energy = cpu_hours * 0.0005
    mem_energy = memory_gb_hours * 0.0004
    storage_energy = storage_gb_hours * 0.00015  # 混合存储

    total_it_energy = cpu_energy + mem_energy + storage_energy
    total_energy = total_it_energy * pue  # 含数据中心冷却等损耗

    co2_kg = (total_energy * intensity) / 1000  # g → kg

    return CarbonEstimate(
        energy_kwh=round(total_energy, 2),
        co2_kg=round(co2_kg, 2),
        pue_factor=pue,
        region=region,
        grid_carbon_intensity=intensity,
        equivalent_km_driven=round(co2_kg * 5.0, 1),  # 平均燃油车 ~200g CO2/km
        equivalent_trees=round(co2_kg / 21.0, 2),    # 一棵树年吸收 ~21kg CO2
    )

GREEN_COMPUTING_RECOMMENDATIONS = [
    "将非关键工作负载调度到低碳区域（如 eu-west-1）",
    "启用云提供商的碳感知调度功能（AWS Carbon Aware, Azure Carbon Optimization）",
    "利用 spot/preemptible 实例提高硬件利用率（间接降低碳排放）",
    "实施自动关机策略：开发/测试环境非工作时间关闭",
    "迁移到 ARM 架构实例（Graviton/Ampere）— 能效比 x86 高 60%",
    "启用容器镜像去重和精简（distroless/alpine），减少传输能耗",
]
```

#### 3.3 容量预测模型

```python
"""
基于历史数据的资源容量预测 — 时间序列趋势外推
"""

import math
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import List

@dataclass
class CapacityForecast:
    resource_type: str           # cpu / memory / storage / cost
    current_value: float
    forecast_30d: float
    forecast_90d: float
    forecast_180d: float
    growth_rate_daily: float     # 日均增长率 (%)
    trend: str                   # growing / stable / declining
    recommendation: str
    confidence_interval: tuple[float, float]

def linear_regression_forecast(data_points: List[tuple[datetime, float]], days_ahead: int) -> CapacityForecast:
    """
    简单线性回归预测
    data_points: [(timestamp, value), ...]
    """
    n = len(data_points)
    if n < 7:
        return CapacityForecast(resource_type="unknown", current_value=0,
                                 forecast_30d=0, forecast_90d=0, forecast_180d=0,
                                 growth_rate_daily=0, trend="insufficient_data",
                                 recommendation="需要更多历史数据（至少7天）",
                                 confidence_interval=(0, 0))

    # 将日期转为数值（距第一天的天数）
    base_time = data_points[0][0]
    x = [(t - base_time).days for t, _ in data_points]
    y = [v for _, v in data_points]

    x_mean = sum(x) / n
    y_mean = sum(y) / n

    # 最小二乘法
    numerator = sum((xi - x_mean) * (yi - y_mean) for xi, yi in zip(x, y))
    denominator = sum((xi - x_mean) ** 2 for xi in x)
    slope = numerator / denominator if denominator != 0 else 0
    intercept = y_mean - slope * x_mean

    current = y[-1]
    daily_growth_rate = slope / current if current != 0 else 0

    forecasts = {}
    for d in [30, 90, 180]:
        pred = intercept + slope * (n - 1 + d)
        forecasts[d] = max(pred, 0)  # 不预测负值

    # 趋势判断
    if daily_growth_rate > 0.005:
        trend = "growing"
        rec = f"预计 {days_ahead} 天后将达 {forecasts[days_ahead]:.1f}，建议提前规划扩容"
    elif daily_growth_rate < -0.003:
        trend = "declining"
        rec = f"用量呈下降趋势，可考虑降配以节约成本"
    else:
        trend = "stable"
        rec = "用量平稳，维持当前配置即可"

    # 置信区间（简化：±15%）
    ci_low = forecasts[min(forecasts.keys(), key=lambda k: abs(k - days_ahead))] * 0.85
    ci_high = forecasts[min(forecasts.keys(), key=lambda k: abs(k - days_ahead))] * 1.15

    return CapacityForecast(
        resource_type="generic",
        current_value=current,
        forecast_30d=forecasts[30],
        forecast_90d=forecasts[90],
        forecast_180d=forecasts[180],
        growth_rate_daily=daily_growth_rate * 100,
        trend=trend,
        recommendation=rec,
        confidence_interval=(ci_low, ci_high)
    )
```

### 阶段四：验证（Verify）

#### 4.1 资源调整后验证 Checklist

| 验证项 | 方法 | 通过标准 | 回滚触发 |
|-------|------|---------|---------|
| 服务可用性 | health check endpoint | HTTP 200 | 连续3次失败 |
| 响应延迟 | P99 latency 对比 | 退化 < 5% | 退化 > 10% |
| 错误率 | error count / total requests | < 0.1% | > 1% |
| 资源利用率 | 新配置下的实际使用 | 在合理范围内 | 仍然过载/过度空闲 |
| Pod 状态 | kubectl get pods | 全部 Running+Ready | 有 CrashLoop |
| 自动扩缩容 | HPA 当前副本数 | 符合预期范围 | 异常震荡 |

#### 4.2 渐进式验证策略

```python
def progressive_verification(change: ResourceChange, phases: list[dict]) -> bool:
    """
    分阶段验证资源变更效果：
    Phase 1 (0-5min): 基础健康检查
    Phase 2 (5-30min): 性能指标监控
    Phase 3 (30min-2h): 稳定性观察
    Phase 4 (2h-24h): 长期趋势确认
    """
    for phase in phases:
        duration = phase['duration_minutes']
        checks = phase['checks']

        print(f"[VERIFY] 进入阶段: {phase['name']} ({duration}min)")

        for check in checks:
            result = run_check(check)
            if not result.passed:
                if check['critical']:
                    print(f"[FAIL] 关键检查失败: {check['name']}")
                    print(f"       原因: {result.reason}")
                    return False
                else:
                    print(f"[WARN] 非关键检查告警: {check['name']}")

        wait_for_duration(duration * 60)

    return True
```

### 阶段五：记录（Record）

#### 5.1 资源变更审计日志

```json
{
  "event_id": "RESO-20260406-001",
  "timestamp": "2026-04-06T09:00:00Z",
  "si_department": "resource_optimization_si",
  "operation_type": "horizontal_scale_up",
  "trigger_mode": "autonomous_qps_based",
  "target": {
    "kind": "Deployment",
    "name": "api-server",
    "namespace": "production"
  },
  "change_details": {
    "replicas_before": 4,
    "replicas_after": 8,
    "change_reason": "QPS per pod exceeded threshold of 800 (actual: 1120)",
    "decision_policy": "SR-001 QPS驱动水平扩展"
  },
  "resource_impact": {
    "cpu_additional": "8 cores",
    "memory_additional": "16Gi",
    "estimated_cost_increase_cny": 2400
  },
  "verification": {
    "post_change_latency_p99_ms": 145,
    "pre_change_latency_p99_ms": 380,
    "error_rate_after": "0.03%",
    "all_pods_healthy": true,
    "status": "VERIFIED_SUCCESS"
  },
  "carbon_impact": {
    "additional_co2_kg": 2.8,
    "offset_action": "none"
  },
  "rollback_executed": false
}
```

## 典型自主场景

### 场景1：低利用率实例自动降配

**背景**：生产集群中有 3 台 `c5.2xlarge`（8C/16G）实例，7天平均 CPU 利用率仅 12%，内存利用率 28%。

**自主处理流程**：

1. **感知**：每日定时采集发现持续低利用率
2. **决策**：利用率 < 25%，且无突发流量历史 → **批准降配**
3. **执行**：
   - 生成降配方案：`c5.2xlarge` → `c5.large`（2C/4G）
   - 预计月节省：¥4,500 × 3 = **¥13,500**
   - 先在一台节点上试点，观察 24 小时
4. **验证**：服务指标无明显变化，Pod 正常调度
5. **推广**：其余两台依次降配
6. **记录**：完整变更日志 + 成本节省报告

### 场景2：HPA 突发流量自适应扩容

**背景**：电商大促期间流量突增 5 倍，常规 HPA 扩容速度跟不上。

**自主处理流程**：

1. **感知**：Prometheus AlertManager 触发 `HighQPS` 告警
2. **决策**：检测到大促日历标记 → 启用**紧急扩展模式**
3. **执行**：
   - �即将 `stableWindowSeconds` 从 300 降至 30
   - 提升最大副本数 20→50
   - 步长从 2 提升至 5
   - 预热 Spot 实例池
4. **监控**：实时跟踪扩容进度和服务质量
5. **恢复**：流量回落后逐步恢复常规策略参数
6. **复盘**：生成大促期间资源使用报告

### 场景3：碳排放优化调度

**背景**：公司承诺碳中和目标，需优化数据中心碳排放。

**自主处理流程**：

1. **感知**：定期计算各区域碳足迹
2. **分析**：发现 cn-north-1 区域碳强度最高（585 gCO2/kWh）
3. **决策**：识别可迁移的非延迟敏感工作负载（批处理、数据处理）
4. **执行**：
   - 将 nightly ETL 任务调度到 eu-west-1（250 gCO2/kWh）
   - 开发测试环境切换到 ARM 架构（Graviton3，能效提升 60%）
   - 设置自动关机：开发环境 19:00-09:00 关闭
5. **量化**：月减排 CO2 约 180kg ≈ 种植 8.5 棵树
6. **记录**：ESG 报告数据支撑

### 场景4：季度容量规划

**背景**：Q2 业务预计增长 40%，需提前规划资源采购。

**自主处理流程**：

1. **数据收集**：拉取过去 90 天的 CPU/内存/存储/网络使用时序数据
2. **趋势建模**：线性回归 + 季节因子校正（考虑业务周期）
3. **预测输出**：
   - 30天后预计需求：当前 × 1.08
   - 90天后预计需求：当前 × 1.35
   - 180天后预计需求：当前 × 1.52
4. **方案生成**：
   - 方案A（保守）：按 1.5x 预留，RI 采购 70%
   - 方案B（平衡）：按 1.4x 预留，RI 50% + Auto Scaling
   - 方案C（激进）：按 1.3x 预留，重度依赖 Spot + HPA
5. **推荐**：结合预算约束和风险偏好，推荐方案B
6. **审批提交**：生成容量规划报告供管理层决策

## 决策框架

### 自主操作权限边界

| 操作类型 | 自主执行 | 需审批 | 禁止 |
|---------|---------|--------|------|
| HPA 副本数调整（±50%内） | ✅ | - | - |
| HPA 副本数调整（超出范围） | - | ✅ | - |
| 单实例 request/limit 微调（±30%） | ✅ | - | - |
| 实例类型降配（低利用率确认） | ✅（先试点1台） | - | - |
| 实例类型升配 | - | ✅ | - |
| 新增节点/购买资源 | - | ✅ | - |
| 删除生产资源 | - | ✅ | - |
| 修改 PDB（PodDisruptionBudget） | - | ✅ | - |
| 修改集群级网络策略 | - | - | ❌ |
| 修改 kube-system 组件 | - | - | ❌ |

### 成本-性能权衡矩阵

| 成本优化力度 | 性能风险 | 适用场景 |
|------------|---------|---------|
| 激进 (>30%节省) | 高（可能影响SLA） | 开发/测试环境，非关键服务 |
| 适度 (15-30%节省) | 中（需密切监控） | 生产非核心服务 |
| 保守 (5-15%节省) | 低（几乎无感） | 核心生产服务 |
| 观察期 (<5%节省) | 极低 | 新上线服务首月 |

## 安全与治理

### 资源配额保护

- **Namespace 级 ResourceQuota**：防止单个团队超额占用
- **ClusterResourceQuota**：集群总量硬上限
- **LimitRange**：默认 request/limit 范围约束
- **预算告警**：月度云账单超过预警线时阻断非必要扩容

### 变更冻结期

- 大促前 72 小时至结束后 24 小时：禁止降配操作
- 财务月末最后 3 个工作日：禁止新增资源采购
- 法定节假日：仅允许紧急扩容，禁止任何缩减操作

## 协作关系

### 向上汇报（户部）

| 报送内容 | 频率 | 格式 |
|---------|------|------|
| 资源健康日报 | 每日 | 8维评分 + 异常事件 |
| 成本优化周报 | 每周 | 节省金额 + 执行进展 |
| 容量规划季报 | 每季度 | 预测模型 + 采购建议 |
| 碳排放月报 | 每月 | CO2 排放 + 绿色举措成效 |

### 平级协作

| 协作对象 | 协作内容 | 接口协议 |
|---------|---------|---------|
| **环境配置司** | 配置变更后的资源需求变化 | 共享 config-change-events |
| **依赖管理司** | 依赖升级后的资源消耗基线偏移 | 提供 resource-profile-delta |
| **基础设施司** | CI/CD 流水线中的资源测试环节 | 性能基准测试结果 |

---

## 🤝 v5.1 增强：Agency Agent 协作指南

### 可调用的 Agency Agents

| Agent 名称 | 所属部门 | 协作模式 | 适用场景 |
|-----------|---------|---------|---------|
| **SRE** | Agency Reliability | SLO 导向优化 | 为仓部司提供 SLO/Error Budget 驱动的资源优化视角，将资源调整决策建立在可靠性数据而非单纯成本考量之上 |
| **Finance Tracker** | Agency Finance | 成本追踪与预算管控 | 直接对接仓部司的成本优化引擎，提供精细化的云账单追踪、预算预警和 ROI 分析能力 |
| **Infrastructure Maintainer** | Agency Operations | 基础设施维护 | 执行仓部司的资源调整决策，负责实例升降配、存储清理、网络策略变更等实际运维操作 |

### Agent 协作工作流

1. **SLO 驱动的资源基线**: SRE 定义各服务的 SLO（可用性 ≥99.9%，延迟 P99 <200ms）及 Error Budget → 仓部司在进行资源优化时必须以不消耗 Error Budget 为前提条件
2. **成本实时追踪**: Finance Tracker 接入云厂商账单 API → 为仓部司的每个优化建议附带精确的成本节省测算 → 当月度预算使用率超 80% 时触发预警
3. **8维诊断→优化决策→执行闭环**: 仓部司执行 8 维性能瓶颈分析 → 生成优化建议（附带风险评分）→ SRE 审核 SLO 影响 → Finance Tracker 确认成本收益 → Infrastructure Maintainer 执行变更 → 仓部司验证效果
4. **容量预测协同**: 仓部司基于历史数据进行容量预测 → SRE 根据业务日历（大促/新品发布）修正预测峰值 → Finance Tracker 评估预算可行性 → 三方共同确定采购/扩容方案
5. **碳排放联合优化**: 仓部司计算碳足迹 → Finance Tracker 提供碳定价数据 → SRE 评估低碳方案的可靠性风险 → 共同制定绿色计算优化路线图
6. **突发事件联动**: SRE 检测到 SLO 退化信号 → 仓部司立即暂停一切降本操作 → Infrastructure Maintainer 执行紧急扩容 → Finance Tracker 追踪额外成本 → 事件结束后复盘优化策略

### 典型协作场景

- **场景一 - SLO 守护下的智能降配**: 仓部司发现 3 台 c5.2xlarge 实例利用率仅 12% → 生成降配建议（预计节省 ¥13,500/月）→ SRE 审核确认该服务 Error Budget 充裕（当前 burn rate 仅 2%）→ 批准降配 → Infra Maintainer 逐步执行 → 连续观察 7 天 SLO 未受影响 → Finance Tracker 确认节省金额入账
- **场景二 - 大促前容量联合规划**: Q2 大促预计流量增长 5 倍 → 仓部司预测需 3× 当前资源 → SRE 根据去年大促数据修正为 4×（含安全缓冲）→ Finance Tracker 评估 RI vs Spot 混合方案的成本最优解（RI 60% + Spot 30% + On-Demand 10%）→ 最终采用混合方案，较纯 On-Demand 节省 45%
- **场景三 - 成本异常根因分析**: Finance Tracker 发现本月云账单异常增高 30% → 触发仓部司进行 8 维诊断 → 发现某开发环境忘记关机（连续运行 15 天，浪费 ¥8,000）+ 一个 HPA 配置错误导致过度扩容（多余 ¥12,000）→ Infra Maintainer 立即修复 → SRE 设置自动化关机策略防止复发

---

## 🏗️ v5.1 增强：Harness 工程实践

### 相关 Harness 模块

- **Harness Cloud Cost Management (CCM)**: **核心对接模块** — 仓部司的所有成本优化操作直接映射到 Harness CMM 的功能集，包括云资产可视化、闲置资源识别、RI/SP 推荐、成本分配与预算告警
- **Harness SRE (Service Reliability Management)**: 将仓部司的资源调整与 Harness SLM (Service Level Management) 深度集成，确保每一次资源变更都经过 Error Budget 检查

### 实践指南

1. **CCM 驱动的成本优化自动化**: 将仓部司的低利用率实例检测算法与 Harness CMM 的 Idle Resource Identification 功能对接 —— CMM 发现闲置资源后自动触发仓部司的降配评估流程，评估通过后由 CMM 直接执行或推荐执行
2. **SLI/SLO 门禁化资源变更**: 在 Harness Pipeline 中添加自定义 Step —— 调用仓部司的资源调整 API 前先查询 Harness SLM 的当前 Error Budget 余量，若余量不足则自动阻塞变更并升级给 SRE 审批

---

## 🆕 v6.0 增强能力集成

### MARC资源协调器集成指南

本司在多Agent并发场景下的资源协调要求：

#### 资源锁机制
- **文件写锁**：当本司需要修改HPA配置、资源配额、成本预算文件、容量规划文档时，必须通过MARC申请互斥锁
  ```python
  # 示例：申请文件写锁
  from skillscripts.resource_coordinator import LockManager, LockType
  lock_mgr = LockManager()
  lock_id = lock_mgr.acquire_lock(
      resource_id="path/to/hpa-config.yaml",
      agent_id="资源优化司",
      lock_type=LockType.EXCLUSIVE,
      priority=7,
      timeout=120.0
  )
  ```
- **读锁**：读取资源使用指标、成本数据、性能基准时申请读锁（高频监控场景）
- **释放锁**：资源调整操作完成后立即释放锁，避免阻塞其他司的资源状态查询

#### 终端会话池使用
- 从MARC终端会话池获取会话执行kubectl scale、性能诊断命令、成本查询API调用
- 会话使用完毕后及时归还池中
- 单个命令超时设置为300秒（容量规划和成本分析可能涉及大量数据处理）

#### 并发安全注意事项
- HPA和资源配额变更需独占锁保护，避免并发调整导致资源震荡
- 成本预算文件写入时需锁定，防止超支
- 死锁预防：按固定顺序申请锁（先锁HPA配置→再锁ResourceQuota→最后锁预算文件）

### 四维度输出防线集成

| 防线层级 | 本司检查重点 | 自动化程度 |
|---------|-------------|----------|
| **提示词工程层** | 性能诊断提示词、成本优化建议提示词、容量预测提示词 | 半自动（AI辅助） |
| **能力约束层** | 仅允许资源优化操作（扩缩容/降配/成本调整），禁止修改业务代码 | 全自动 |
| **规则校验层** | 输出格式：YAML HPA配置、JSON成本报告、Markdown容量规划 | 全自动 |
| **兜底恢复层** | 资源调整导致SLO退化时自动回滚至上一个稳定配置 | 半自动 |

### 操作优先级指引（v6.0核心）

本司推荐的操作方式：

1. 🥇 **Agent自主手动操作**（强烈推荐用于HPA调优、实例降配、成本优化决策）
   - 示例：直接编辑HPA YAML配置、手动调整Pod副本数、编写成本优化方案
   - 优势：精确控制资源参数、可逐步验证优化效果、可随时回滚资源变更

2. 🥈 **规划脚本操作**（适用于周期性性能扫描、自动化成本分析）
   - 推荐脚本：
     - `skillscripts/resource_coordinator/quota_manager.py` — 检查和管理资源配额
     - `skillscripts/open_source_philosophy/clawcode_sdd_tdd_engine.py` — SDD/TDD驱动的性能基准测试
     - `skillscripts/platform/powershell_adapter.py` — PS7环境适配

3. 🥉 **命令操作**（仅限紧急扩容、生产故障恢复等极少数场景）
   - ⚠️ 必须预演影响范围（资源变更直接影响服务SLA）
   - ⚠️ 生产环境扩缩容需逐条确认并监控Golden Signal
   - 推荐使用PS7适配器转换kubectl/aws命令

### PowerShell 7 执行指南

本司相关操作的PS7适配要点：
- K8s操作：kubectl命令在PS7中原生可用于HPA/Pod/Node管理
- 云API调用：aws/az/gcloud CLI用于实例升降配和成本查询
- 数据处理：使用PowerShell处理CSV/JSON格式的性能指标和账单数据
- 编码：确保所有输出 UTF-8 无 BOM（成本报告和审计记录）

### 与其他司的协作接口

- 上游依赖：环境配置司（接收配置变更后的资源需求）、依赖管理司（获取依赖升级后的资源基线）
- 下游输出：协同调度司（推送资源状态和容量预警）、刑部安全司（报告资源安全合规性）
- 数据交换格式：YAML / JSON / Markdown（统一UTF-8无BOM）
