---
name: sdd-tdd-fast
description: SDD+TDD 快速流程（3 Phase）
phases:
  - id: 0
    name: 设计+测试
    gates: [DESIGN-SYSTEM-COMPLETE, TEST-FIRST]
    agents: [design-reviewer, tdd-agent]
  - id: 1
    name: 实现+验证
    gates: [TEST-PASS, GATE-007, GATE-011]
    agents: [coder, integrator]
  - id: 2
    name: 发布
    gates: [GATE-013, DESKTOP-BUILD]
    agents: [devops, desktop-builder]
---

# SDD+TDD Fast Workflow

3阶段快速开发流程，适用于小型项目或快速原型。

## Phases

| Phase | 名称 | 说明 |
|-------|------|------|
| 0 | 初始化+设计 | 快速检测与设计 |
| 1 | 测试+实现 | 测试驱动快速实现 |
| 2 | 验证+交付 | 快速验证与交付 |
