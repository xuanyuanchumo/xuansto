---
name: sdd-tdd-medium
description: SDD+TDD 中等流程（5 Phase）
phases:
  - id: 0
    name: 初始化+需求
    gates: [DESIGN-SYSTEM-COMPLETE, BRAINSTORM-COMPLETE, GATE-001]
    agents: [design-reviewer, brainstormer]
  - id: 1
    name: 设计+测试
    gates: [PLAN-ATOMIC, GATE-003, TEST-FIRST]
    agents: [architect, tdd-agent]
  - id: 2
    name: 实现+审查
    gates: [SUBAGENT-REVIEW, TEST-PASS, GATE-007]
    agents: [coder, reviewer]
  - id: 3
    name: 集成+部署
    gates: [GATE-011, INFRA-HEALTH, GATE-013]
    agents: [integrator, devops]
  - id: 4
    name: 优化+发布
    gates: [SIMPLIFICATION-BEHAVIOR, GATE-015, DESKTOP-BUILD]
    agents: [refactorer, desktop-builder]
---

# SDD+TDD Medium Workflow

6阶段中等规模开发流程，适用于中型项目。

## Phases

| Phase | 名称 | 说明 |
|-------|------|------|
| 0 | 初始化 | 项目结构检测 |
| 1 | 需求+设计 | 需求澄清与架构设计合并 |
| 2 | 测试先行 | 编写测试用例 |
| 3 | 代码实现 | 按测试驱动实现代码 |
| 4 | 测试+验收 | 测试验证与验收合并 |
| 5 | 部署交付 | 构建与发布 |
