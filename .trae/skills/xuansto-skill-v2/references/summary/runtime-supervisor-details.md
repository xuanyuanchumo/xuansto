# Runtime Supervisor 详细参考

## Core Points
- 三层记忆：短期(运行状态/活跃告警)、中期(故障历史/恢复策略库)、长期(故障模式库/容量规划)
- 协作关系：上游接收DevOps运维策略和Monitor监控数据，下游提供运行时洞察，同级与CI/CD和安全协作
- 遵循Karpathy Guidelines：监控前理解系统拓扑、不添加未要求监控、只修复相关故障、每个恢复动作有验证标准
- 核心职责：运行时监控、熔断机制、检查点恢复、级联故障防护

## Applicable Scenarios
- Runtime Supervisor Agent执行运行时监控和故障恢复
- 设计熔断机制和级联故障防护策略
- 配置健康检查和检查点恢复流程
