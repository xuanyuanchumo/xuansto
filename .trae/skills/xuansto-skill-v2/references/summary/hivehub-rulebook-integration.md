# @hivehub/rulebook 集成模式参考文档

## Core Points
- @hivehub/rulebook是面向AI Agent的规则引擎与行为约束框架
- 核心机制：三次尝试重启规则(3-Attempt Restart)、强制工作流(Forced Workflow)、持久化记忆(Persistent Memory)
- 三次尝试重启：同一任务连续失败3次后自动重启Agent并重置上下文
- 强制工作流：定义Agent必须遵循的步骤序列，跳步即违规
- 与xuansto集成：3-Strike Protocol参考三次尝试重启规则，Hook系统参考强制工作流机制

## Applicable Scenarios
- 设计Agent行为约束和规则引擎
- 实现失败重试和重启策略
- 配置Agent强制工作流和持久化记忆
