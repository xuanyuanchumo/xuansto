# 协作模式详细定义

## Core Points
- 8种协作模式：Auto(智能路由)、Review(交叉审查)、Challenge(对抗辩论)、Consult(专家咨询)、Sequential(串行)、Parallel(并行)、Hivecoding(蜂群编码)、Cross-Platform(跨平台协同)
- Auto模式根据任务复杂度、依赖关系、安全等级和Token预算智能路由到最佳模式
- Review模式：5个子Agent并行审查→聚合→置信度评分(0-1)
- Challenge模式：正方vs反方辩论→裁判裁决，适用于架构决策和技术选型
- 模式切换规则：任务特征变化时Orchestrator可动态切换模式

## Applicable Scenarios
- Orchestrator根据任务特征选择协作模式
- 设计多Agent协作流程和审查机制
- 实现模式间动态切换和路由逻辑
