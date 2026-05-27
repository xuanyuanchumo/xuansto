# Token降级策略详细文档

## Core Points
- 三级渐进降级策略：L1轻度(≥80%)→L2中度(≥95%)→L3重度(≥99%)
- L1降级：减少并行Agent至5、禁用非关键MCP工具、快速模型优先、搜索降级为keyword-only、知识Top-5→Top-2
- L2降级：并行Agent降至3、仅保留核心Agent(工程+测试+安全)、禁用知识检索、串行执行
- L3降级：单Agent串行、仅核心功能、最小Token输出、紧急完成模式
- 降级恢复：Token使用率回落到阈值以下后逐级恢复

## Applicable Scenarios
- Token Optimizer Agent管理Token预算和降级策略
- Runtime Supervisor Agent执行降级和恢复
- 配置Token降级阈值和恢复条件
