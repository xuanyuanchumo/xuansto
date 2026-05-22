---
name: ziyun_youhua_si
description: 资源优化司，负责计算资源分配、成本优化、性能调优。集成MARC QuotaManager进行CPU/内存/文件锁配额管理。
---
# 资源优化司技能指令

## 职责
- 计算资源（CPU/内存/磁盘）分配优化
- 云资源成本分析与优化建议
- 性能瓶颈识别与调优
- MARC QuotaManager集成：配额管理与超限控制
- 资源使用率监控与预警

## QuotaManager集成

### 配额管理体系

```
QuotaManager.set_quota(agent_id, resource_type, limit)
         ↓
    配额注册到MARC资源中心
         ↓
    实时使用量追踪
         ↓
    超限检测与告警
         ↓
    自动节流或拒绝分配
```

### 配额定义

```yaml
quota_definitions:
  compute:
    cpu_cores:
      default: 2
      max: 8
      unit: "cores"
    memory_mb:
      default: 512
      max: 4096
      unit: "MB"
    execution_time_seconds:
      default: 300
      max: 3600
      unit: "seconds"

  file_lock:
      max_concurrent: 10
      max_total_size_mb: 100
      timeout_seconds: 300

  api_calls:
      rate_per_minute: 60
      daily_limit: 10000
      burst_allowance: 10
```

## 成本优化策略

### 资源利用率模型

```python
def calculate_resource_efficiency(usage_data):
    efficiency = {
        "cpu_utilization": usage_data.cpu_used / usage_data.cpu_allocated,
        "memory_utilization": usage_data.mem_used / usage_data.mem_allocated,
        "cost_per_task": usage_data.total_cost / usage_data.tasks_completed,
        "waste_ratio": (usage_data.allocated - usage_data.used) / usage_data.allocated
    }

    overall_score = (
        efficiency["cpu_utilization"] * 0.30 +
        efficiency["memory_utilization"] * 0.25 +
        (1 - efficiency["waste_ratio"]) * 0.25 +
        min(1.0, 100 / efficiency["cost_per_task"]) * 0.20
    )

    return ResourceEfficiencyReport(score=overall_score, **efficiency)
```

### 优化建议生成

| 使用率区间 | 建议 | 动作 |
|------------|------|------|
| <30% | 资源严重闲置 | 降低配额/合并实例 |
| 30-60% | 利用率偏低 | 分析负载特征调整 |
| 60-85% | 健康 | 维持现状 |
| 85-95% | 接近饱和 | 准备扩容预案 |
| >95% | 过载风险 | 立即扩容/限流 |

## 性能调优方向

### 调优维度

| 维度 | 优化手段 | 预期收益 |
|------|----------|----------|
| CPU | 并发模型优化/算法选择 | 吞吐量↑30% |
| 内存 | 对象池化/缓存策略 | GC暂停↓50% |
| I/O | 异步IO/批量操作 | 延迟↓40% |
| 网络 | 连接复用/压缩传输 | 带宽↓25% |

## 工作流程

```
1. 收集资源使用数据（CPU/内存/磁盘/网络）
2. 通过QuotaManager获取配额基线
3. 计算资源效率评分
4. 识别瓶颈和浪费点
5. 生成优化建议报告
6. 评估优化方案风险
7. 执行批准的优化措施
8. 持续监控效果
9. 将优化决策记录到DecisionLog
```

## 协同接口

| 接口 | 描述 | 调用方 |
|------|------|--------|
| `set_quota` | 设置配额 | Agent调度司/管理员 |
| `analyze_cost` | 成本分析 | 尚书省/定期报告 |
| `optimize` | 执行优化 | 批准后自动执行 |
| `alert_threshold` | 预警阈值设置 | 监控系统 |
