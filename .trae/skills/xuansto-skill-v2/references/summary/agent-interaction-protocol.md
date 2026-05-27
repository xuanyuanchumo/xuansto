# Agent 交互协议 (A2A/v1.1)

## Core Points
- 定义7种消息类型：TASK_ASSIGN、TASK_RESULT、QUERY、RESPONSE、BROADCAST、ERROR、HEARTBEAT
- 三种通信模式：请求-响应(同步)、发布-订阅(异步广播)、流水线(阶段顺序执行)
- 子Agent调度生命周期：DISPATCH→EXECUTE→REPORT→COMPLETE，单任务最大并发3个Agent
- 错误处理采用三击协议：第1次重试→第2次重试+告警→第3次停止+反模式分析+修复重启
- 通信约束：默认超时30s、单消息≤64KB、敏感数据AES-256加密、Token预算嵌入payload

## Applicable Scenarios
- 实现Agent间消息传递和通信协议
- 设计子Agent调度和结果聚合策略
- 配置Agent错误处理和故障转移机制
