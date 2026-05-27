# Agent注册表（57 Agents）

## Core Points
- 57个Agent分布在13个层级：编排(3)、产品(4)、设计(4)、工程(6)、跨平台(5)、数据(3)、测试(10)、安全(3)、运维(4)、质量(7)、文档(2)、知识(3)、监控(3)
- 优先级分布：P0(1个-Orchestrator)、P1(38个)、P2(18个)
- 严格依赖关系定义了Agent间上下游产出依赖，如Frontend Developer依赖UI Designer+System Architect
- 可并行Agent组：前后端可基于契约并行开发，子代理审查(Compliance+Bug+History+Comment)可并行执行
- v3.2.0新增Agent：Brainstorming Facilitator、Subagent Dispatcher、Design System Generator、IPC Specialist等

## Applicable Scenarios
- Orchestrator进行任务路由和Agent调度时查询注册信息
- 分析Agent间依赖关系和并行执行可能性
- 新增Agent时参考注册格式和依赖定义
