# 人机协作断点交互规范

## Core Points
- 五类决策检查点：安全确认(SECURITY_GATE)、架构决策(ARCH_DECISION)、需求澄清(REQUIREMENT_CLARIFY)、部署审批(DEPLOY_APPROVAL)、数据操作(DATA_OPERATION)
- 通知机制：断点触发时向用户发送结构化通知，包含决策类型、上下文、选项和超时
- 超时处理：默认30分钟超时，超时后按默认策略执行(安全确认默认拒绝，其他默认继续)
- 决策分级：low(自动批准)、medium(人工推荐)、high(强制人工确认)

## Applicable Scenarios
- Orchestrator实现人机协作断点和审批流程
- 设计高风险操作的安全确认机制
- 配置决策分级和超时策略
