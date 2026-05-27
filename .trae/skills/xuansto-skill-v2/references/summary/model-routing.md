# 模型路由策略

## Core Points
- 基于任务复杂度智能选择模型层级，优化Token消耗和响应速度
- 四个模型层级：fast(快速/文件搜索)、standard(标准/常规开发)、extended(扩展/架构设计)、reasoning(推理/安全审计)
- Agent frontmatter的model字段声明所需层级，Orchestrator据此选择执行策略
- 未声明model字段的Agent默认使用standard层级

## Applicable Scenarios
- Orchestrator根据Agent的model字段路由任务到对应模型
- Token Optimizer Agent优化模型选择和Token消耗
- 配置Agent的模型层级声明
