---
name: resource-optimization-si
parent: universal-devops
department: hubu
province: shangshusheng
description: |
  资源优化司 - 户部·仓部司

  【职责】计算资源分配、成本优化、性能调优、资源利用率监控

  【触发条件】
  - 云资源成本优化
  - 应用性能瓶颈分析
  - 资源扩缩容决策

  【能力】
  - 资源使用分析
  - 成本优化建议
  - 性能基线建立
  - 自动扩缩容策略
---

# 资源优化司 (Resource Optimization Si)

> 尚书省 · 户部 · Universal DevOps v4.0

**状态**: 占位符 - 具体内容由后续任务填充

## 🤖 自主化操作指南 (v7.0)

### 推荐操作模式
| 操作场景 | 推荐模式 | 置信度 | 说明 |
|---------|---------|--------|------|
| 资源使用监控 | SCRIPTED_BATCH | 97% | Prometheus/Grafana自动采集和展示 |
| 成本分析报告 | HYBRID_ASSISTED | 86% | 数据自动聚合 + 人工解读趋势 |
| 扩缩容决策 | HYBRID_ASSISTED | 82% | 算法建议 + 人工确认业务影响 |
| 性能调优方案制定 | AUTONOMOUS_MANUAL | 73% | 需要深入理解业务特点和瓶颈根因 |

### 常用工具组合
- **读操作**: Read, SearchCodebase, Grep（读取监控指标、账单数据、资源配置）
- **写操作**: Write, SearchReplace（生成优化报告、调整资源配置）
- **批量操作**: CloudWatch/Prometheus查询、成本分析ETL脚本、HPA/VPA配置生成器
- **验证操作**: 负载测试工具(k6/locust)、性能profiler(pprof/py-spy)、成本模拟器

### 注意事项
- ⚠️ 优化不能牺牲可用性：过度降配可能导致服务不稳定，需平衡成本与可靠性
- ⚠️ 关注长期合约 vs 按需付费的权衡：预留实例虽便宜但灵活性差
- ✅ 建立"资源利用率基线": 正常业务负载下的CPU/内存/网络使用基准，便于异常检测
- ✅ 采用"右-sizing"而非"over-provisioning": 根据实际需求精确配置，避免浪费

## 🔗 资源协调要点 (v7.0)

### 常访问资源
| 资源类型 | 典型路径 | 锁策略建议 |
|---------|---------|-----------|
| METRIC | Prometheus/Grafana面板 | SHARED (读) |
| BILL | 云服务商账单API | READ_ONLY (只读访问) |
| CONFIG | HPA/VPA配置(K8s) | SHARED (读) / EXCLUSIVE (修改) |
| RESOURCE | EC2/VM/Pod规格 | LIFECYCLE_MANAGED (按需创建销毁) |
| BUDGET | 成本预算和配额设置 | APPROVAL_REQUIRED |

### 竞争规避策略
1. **资源配额(Resource Quota)**: 为每个namespace/team设置资源上限，防止个别任务占用过多
2. **优先级抢占机制**: 当集群资源不足时，低优先级workload可被高优先级任务抢占
3. **成本预警阈值**: 设置月度/日度预算红线，接近时自动通知负责人并考虑限流

## 💡 开源哲学应用 (v7.0)

### OpenCode 透明化
- 成本数据全员透明：每个团队成员可查看自己负责服务的资源成本和优化机会
- 优化决策过程公开：为什么选择某个优化方案、预期节省多少、风险评估都记录在案
- 浪费曝光机制：定期公示闲置资源(zombie instances)、低利用率资产，形成节约文化

### OpenClaude 编排
- 智能容量规划：基于历史增长趋势预测未来资源需求，提前规划扩容
- 异常消耗检测：自动识别突发的资源飙升（可能是bug或攻击）并及时告警
- 多维度优化推荐：综合考虑性能、成本、可用性给出Pareto最优解

### Claw-Code 契约驱动
- 资源效率SLA契约：定义CPU利用率>40%、内存利用率>60%等最低效率目标
- 成本预算硬约束：超过预算时自动触发审批流程或限制新资源创建
- FinOps实践制度化：建立"标注→优化→运营"闭环，持续改进云成本管理成熟度
