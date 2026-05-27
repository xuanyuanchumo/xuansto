# Specification Keeper 详细参考

## Core Points
- 三层记忆：短期(一致性检查任务/文档变更)、中期(文档索引/依赖关系图)、长期(文档规范库/一致性规则)
- 协作关系：上游接收Documentation Engineer和Product Manager的更新，下游提供索引和一致性检查服务
- 遵循Karpathy Guidelines：检查前理解文档结构、不添加未要求的规范、只标记相关漂移、每个检查有明确结果
- 核心职责：规格文档维护、规格漂移审核、知识沉淀、跨分支经验同步、ADR归档

## Applicable Scenarios
- Specification Keeper Agent执行文档一致性检查
- 实现规格漂移检测和跨分支经验同步
- 设计文档索引和版本追踪机制
