# 会话持久化机制

## Core Points
- 通过Stop Hook和SessionStart Hook实现跨会话上下文保存与恢复
- 核心目标：会话结束自动保存关键状态、新会话自动恢复上下文、压缩前持久化关键数据
- Stop Hook行为：保存工作流状态、Agent状态、决策记录、Token消耗统计
- SessionStart Hook行为：加载最近会话状态、恢复Agent上下文、同步知识库更新
- PreCompact Hook：上下文压缩前保存关键数据，防止信息丢失

## Applicable Scenarios
- 实现跨会话工作流连续性
- 配置会话持久化和恢复策略
- 设计上下文压缩前的数据保护机制
