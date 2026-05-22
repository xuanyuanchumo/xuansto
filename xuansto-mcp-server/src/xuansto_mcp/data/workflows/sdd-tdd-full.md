---
name: sdd-tdd-full
description: SDD+TDD 全流程（9 Phase）
phases:
  - id: 0
    name: 初始化
    gates: [DESIGN-SYSTEM-COMPLETE, ANTI-PATTERN-CHECK, DESIGN-REVIEW]
    agents: [design-reviewer, anti-pattern-checker]
  - id: 1
    name: 需求分析
    gates: [BRAINSTORM-COMPLETE, GATE-001, GATE-002]
    agents: [brainstormer, requirement-analyst]
  - id: 2
    name: 架构设计
    gates: [PLAN-ATOMIC, GATE-003, GATE-004]
    agents: [architect, planner]
  - id: 3
    name: 测试先行
    gates: [TEST-FIRST]
    agents: [tdd-agent]
  - id: 4
    name: 代码实现
    gates: [SUBAGENT-REVIEW, REVIEW-CONFIDENCE, GATE-007, TEST-PASS, GATE-009, FILE-ENCODING]
    agents: [coder, reviewer]
  - id: 5
    name: 集成验证
    gates: [PLAYWRIGHT-E2E-PASS, GATE-011, GATE-012, AI-PENTEST, SPEC-CONSISTENCY]
    agents: [integrator, security-tester]
  - id: 6
    name: 部署运维
    gates: [GATE-013, GATE-014, INFRA-HEALTH, UX-ACCEPTANCE]
    agents: [devops, infra-checker]
  - id: 7
    name: 重构优化
    gates: [SIMPLIFICATION-BEHAVIOR, CHESTERTON-FENCE, GATE-015]
    agents: [refactorer, simplifier]
  - id: 8
    name: 桌面发布
    gates: [DESKTOP-BUILD, DESKTOP-SIGN, DESKTOP-UPDATE, DESKTOP-CROSS, IPC-CONTRACT]
    agents: [desktop-builder, signer]
---

# SDD+TDD Full Workflow

9阶段全生命周期开发流程，适用于大型项目。

## Phases

| Phase | 名称 | 说明 |
|-------|------|------|
| 0 | 初始化 | 项目结构检测与设计系统建立 |
| 1 | 需求分析 | 需求澄清与Brainstorming |
| 2 | 架构设计 | 技术方案设计与原子任务分解 |
| 3 | 测试先行 | 编写测试用例 |
| 4 | 代码实现 | 按测试驱动实现代码 |
| 5 | 测试验证 | 全面测试与安全扫描 |
| 6 | 验收确认 | 用户验收与合规检查 |
| 7 | 持续重构 | 代码简化与Chesterton's Fence检查 |
| 8 | 部署交付 | 构建、签名与发布 |

## Quality Gates

54项质量门禁，每个Phase转换时必须通过对应门禁。
