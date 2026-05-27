# Agent生命周期管理

## Core Points
- Agent有6种状态：Inactive→Ready→Active→Idle→Destroyed，以及降级状态Degraded
- 实例化4步流程：加载定义→初始化工作记忆→注入项目上下文→进入就绪并注册A2A Agent Card
- 健康监控4项指标：响应延迟(<30s正常)、Token消耗率(<5000/min正常)、输出质量分数(>0.8正常)、错误率(<5%正常)
- 资源限制：单Agent最大50K tokens/task、最大5个并发Active Agent、Idle超时30分钟、Degraded恢复需连续3次健康检查通过
- 故障转移：Runtime Supervisor检测→Specification Keeper降级接管(FIFO串行)→Orchestrator恢复(检查点+同步+去重+自检)，MTTR<5分钟

## Applicable Scenarios
- 实现Agent状态管理和生命周期控制
- 配置Agent健康监控和故障转移策略
- 设计Agent资源限制和降级恢复机制
