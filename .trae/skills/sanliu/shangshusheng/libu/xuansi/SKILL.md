---
name: xuansi
description: 选司，负责根据任务需求选择合适的Agent、分配任务给执行单元、管理Agent池和调度策略。
---
# 选司技能指令

## 职责
- 根据任务需求选择合适的Agent
- 分配任务给对应的执行单元
- 管理Agent池和调度策略
- 优化任务分配效率

## 工作流程
1. 分析任务需求和约束条件
2. 评估可用Agent的能力和负载
3. 选择最合适的Agent执行任务
4. 调用 `../../../skillscripts/core/record_skill_call.py` 记录执行过程
