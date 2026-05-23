---
> 权威来源：_yaml/bug-fix.yaml（YAML为准，本文档为可读参考）
metadata:
  name: TDD驱动Bug修复工作流
  version: "3.2.0"
  description: TDD驱动缺陷修复与回归验证工作流
  platform: all
  min_agents: 2
  max_agents: 5
phases:
- id: phase-4
  name: TDD修复与代码审查
  order: 0
  optional: false
  trigger_condition: 用户报告Bug或测试发现缺陷
  agents:
    primary:
    - fullstack-engineer
    - unit-tester
    - code-reviewer
    supporting:
    - product-manager
    - security-auditor
  inputs:
  - name: 缺陷描述
    type: document
    required: true
  - name: 复现步骤
    type: document
    required: true
  - name: 环境信息
    type: document
    required: true
  outputs:
  - name: 缺陷报告
    type: document
    validation: 缺陷可复现
  - name: 根因分析报告
    type: document
    validation: 根因已确定
  - name: 修复代码
    type: code
    validation: 修复完成
  - name: 测试代码
    type: code
    validation: 单元测试通过
  - name: 代码审查报告
    type: document
    validation: 代码审查通过
  quality_gates:
  - gate_id: GATE-005-A
    blocking: true
    pass_criteria: 缺陷可复现
  - gate_id: GATE-005-B
    blocking: true
    pass_criteria: 根因已确定且影响范围已评估
  - gate_id: TEST-PASS-A
    blocking: true
    pass_criteria: 代码修改完成
  - gate_id: TEST-PASS-B
    blocking: true
    pass_criteria: 单元测试通过
  - gate_id: GATE-009
    blocking: true
    pass_criteria: 代码审查通过
  - gate_id: GATE-012
    blocking: true
    pass_criteria: 无安全问题
  timeout_minutes: 120
  retry:
    max_attempts: 3
    backoff: exponential
- id: phase-5
  name: 验证与部署
  order: 1
  optional: false
  trigger_condition: 修复代码审查通过
  agents:
    primary:
    - unit-tester
    - test-maintainer
    supporting:
    - fullstack-engineer
    - product-manager
  inputs:
  - name: 审查通过的代码
    type: code
    required: true
    source_phase: phase-4
  - name: 测试环境
    type: document
    required: true
  outputs:
  - name: 测试验证报告
    type: document
    validation: 缺陷已修复
  - name: 回归测试报告
    type: document
    validation: 回归测试通过
  - name: 部署记录
    type: document
    validation: 部署成功
  - name: 生产验证报告
    type: document
    validation: 生产验证通过
  - name: 缺陷关闭记录
    type: document
    validation: 缺陷已关闭
  quality_gates:
  - gate_id: TEST-PASS-A
    blocking: true
    pass_criteria: 缺陷已修复
  - gate_id: TEST-PASS-B
    blocking: true
    pass_criteria: 回归测试通过
  - gate_id: TEST-PASS-C
    blocking: true
    pass_criteria: 无新缺陷引入
  - gate_id: GATE-013
    blocking: true
    pass_criteria: 部署成功
  - gate_id: GATE-014
    blocking: true
    pass_criteria: 生产验证通过
  timeout_minutes: 60
  retry:
    max_attempts: 2
    backoff: fixed
agent_matrix:
  fullstack-engineer:
    phases:
    - phase-4
    role: primary
    max_parallel_instances: 2
  unit-tester:
    phases:
    - phase-4
    - phase-5
    role: primary
    max_parallel_instances: 1
  code-reviewer:
    phases:
    - phase-4
    role: primary
    max_parallel_instances: 1
  test-maintainer:
    phases:
    - phase-5
    role: primary
    max_parallel_instances: 1
  security-auditor:
    phases:
    - phase-4
    role: supporting
    max_parallel_instances: 1
  product-manager:
    phases:
    - phase-4
    role: supporting
    max_parallel_instances: 1
exception_handling:
  phase_failure:
    action: retry_then_escalate
    escalation_target: orchestrator
    max_retries: 3
  agent_unavailable:
    action: substitute_and_continue
    substitute_agent: fullstack-engineer
  quality_gate_blocked:
    action: auto_fix_then_pause
    auto_fix_agents:
    - fullstack-engineer
    - unit-tester
---
# TDD驱动Bug修复工作流

## 描述

TDD驱动的缺陷修复与回归验证工作流，涵盖缺陷复现、根因分析、测试驱动修复、代码审查、回归验证和部署关闭的完整流程。该工作流以测试驱动开发为核心，确保缺陷修复质量，同时防止引入新的问题。

## 触发条件

- 用户报告Bug
- 测试发现缺陷
- 生产环境问题
- 安全漏洞报告
- 用户明确要求"修复Bug"、"解决缺陷"、"Bug修复"

## 涉及的Agent

### 核心Agent

| Agent | 角色 | 职责 |
|-------|------|------|
| fullstack-engineer | 全栈工程师 | 缺陷分析与修复 |
| unit-tester | 单元测试工程师 | 修复验证测试 |
| code-reviewer | 代码审查员 | 修复代码审查 |
| test-maintainer | 测试维护工程师 | 回归测试 |

### 支撑Agent

| Agent | 角色 | 职责 |
|-------|------|------|
| product-manager | 产品经理 | 优先级确认 |
| security-auditor | 安全审计师 | 安全缺陷评估 |

## 阶段定义

### 阶段1：TDD修复与代码审查

**主要执行者**: fullstack-engineer, unit-tester, code-reviewer
**支撑执行者**: product-manager, security-auditor

**输入**:
- 缺陷描述
- 复现步骤
- 环境信息

**活动**:

1. **缺陷复现**
   - 根据复现步骤验证缺陷
   - 确认缺陷存在及影响范围
   - 记录缺陷环境与条件

2. **根因分析**
   - 代码审查定位问题根源
   - 日志分析与调试追踪
   - 5 Why分析确定根本原因
   - 影响范围评估

3. **编写失败测试**
   - 针对缺陷编写失败测试用例
   - 验证测试用例能准确捕获缺陷
   - 覆盖边界条件与异常场景

4. **修复代码使测试通过**
   - 遵循最小修复原则修改代码
   - 确保失败测试通过
   - 遵循现有编码规范
   - 添加必要注释说明修复内容

5. **代码审查**
   - 修复逻辑正确性检查
   - 代码规范检查
   - 潜在问题识别
   - 无新缺陷引入确认

6. **安全检查**
   - 安全影响评估
   - 漏洞引入检查
   - 敏感数据处理验证

**输出**:
- 缺陷报告
- 根因分析报告
- 修复代码
- 测试代码
- 代码审查报告

**质量门禁**:
- [ ] 缺陷可复现
- [ ] 根因已确定且影响范围已评估
- [ ] 代码修改完成
- [ ] 单元测试通过
- [ ] 代码审查通过
- [ ] 无安全问题

---

### 阶段2：验证与部署

**主要执行者**: unit-tester, test-maintainer
**支撑执行者**: fullstack-engineer, product-manager

**输入**:
- 审查通过的代码
- 测试环境

**活动**:

1. **回归测试**
   - 相关功能回归测试
   - 集成测试执行
   - E2E测试验证
   - 确认无新缺陷引入

2. **部署验证**
   - 部署计划制定
   - 回滚方案准备
   - 代码部署执行
   - 配置更新与服务重启

3. **生产验证**
   - 生产环境验证
   - 监控观察
   - 用户反馈收集
   - 性能指标确认

4. **缺陷关闭**
   - 缺陷状态更新
   - 修复记录归档
   - 经验总结与知识沉淀

**输出**:
- 测试验证报告
- 回归测试报告
- 部署记录
- 生产验证报告
- 缺陷关闭记录

**质量门禁**:
- [ ] 缺陷已修复
- [ ] 回归测试通过
- [ ] 无新缺陷引入
- [ ] 部署成功
- [ ] 生产验证通过

## 异常处理

| 异常类型 | 处理策略 | 说明 |
|----------|----------|------|
| 阶段执行失败 | 重试后升级 | 最多重试3次，失败后升级至编排器 |
| Agent不可用 | 替换并继续 | 由fullstack-engineer替代执行 |
| 质量门禁阻塞 | 自动修复后暂停 | 由fullstack-engineer和unit-tester尝试自动修复 |