# 9阶段工作流详细参考

## Core Points
- 9阶段工作流：Phase 0(初始化)→1(需求分析)→2(架构设计)→3(测试先行)→4(代码实现)→5(测试验证)→6(安全审计)→7(部署发布)→8(文档交付)
- 每阶段定义：目标、步骤、MCP工具、关键门禁
- Phase 0门禁：DESIGN-SYSTEM-COMPLETE、ANTI-PATTERN-CHECK
- Phase 4门禁：GATE-007、TEST-PASS、FILE-ENCODING
- 权威来源为workflows/_yaml/目录下的YAML文件

## Applicable Scenarios
- Orchestrator执行9阶段工作流调度
- Task Coordinator Agent管理阶段间任务编排
- 配置工作流阶段门禁和命令路由
