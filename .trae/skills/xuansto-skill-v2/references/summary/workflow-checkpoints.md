# 工作流检查点与恢复

## Core Points
- 子任务粒度检查点：每个子任务开始前/完成后保存，关键决策点额外保存
- 保存内容：task_id、phase、状态、已完成步骤、待执行步骤、Token消耗、决策记录
- 恢复流程：加载最近检查点→验证上下文完整性→同步运行时状态→继续执行
- 检查点存储：.knowledge/workflow-checkpoints/目录，JSON格式，按时间戳排序

## Applicable Scenarios
- Runtime Supervisor Agent管理工作流检查点
- Orchestrator实现故障恢复和状态同步
- 设计工作流持久化和恢复策略
