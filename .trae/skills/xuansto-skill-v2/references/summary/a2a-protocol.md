# A2A协议参考文档

## Core Points
- A2A（Agent-to-Agent）协议是标准化智能体间通信协议，定义发现、消息传递、任务协调和安全通信规范
- 消息类型包括TASK_ASSIGN、STATUS、GATE_CHECK、KNOWLEDGE_SHARE、ERROR_REPORT、HANDOFF等12种
- 安全层支持Bearer Token、mTLS、API Key三种认证，RBAC/ABAC两种授权模型
- 包含Google A2A Protocol v0.3.0完整规范：Agent Card、Task生命周期、Message通信、Artifact管理、Push Notification
- 定义了Xuansto 57 Agent到A2A agentType的11层映射关系和消息格式转换规则

## Applicable Scenarios
- 实现Agent间通信和协作时参考消息格式与安全规范
- 跨框架Agent互操作时参考Google A2A协议映射
- Agent发现与注册时参考Agent Card格式
