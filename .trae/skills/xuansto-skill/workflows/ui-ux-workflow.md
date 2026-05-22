---
metadata:
  name: UI/UX设计专项工作流
  version: "3.2.0"
  description: UI/UX设计专项与前端实现工作流
  platform: all
  min_agents: 2
  max_agents: 5
phases:
- id: phase-0
  name: UX/UI设计
  order: 0
  optional: false
  trigger_condition: 用户请求UI/UX设计或界面优化
  agents:
    primary:
    - ux-designer
    - ui-designer
    supporting:
    - product-manager
    - desktop-ui-adapter
  inputs:
  - name: 产品需求
    type: document
    required: true
  - name: 用户画像
    type: document
    required: true
  - name: 业务目标
    type: document
    required: true
  outputs:
  - name: 用户研究报告
    type: document
    validation: 用户画像清晰且痛点已识别
  - name: 高保真设计稿
    type: document
    validation: 设计评审通过
  - name: 设计系统文档
    type: document
    validation: 组件可复用
  - name: 桌面窗口布局规范
    type: document
    validation: 窗口尺寸适配方案完整
  - name: 系统菜单结构图
    type: document
    validation: 菜单结构符合各平台规范
  quality_gates:
  - gate_id: DESIGN-REVIEW
    blocking: true
    pass_criteria: 设计评审通过且符合品牌规范
  - gate_id: DESIGN-ACCESSIBILITY
    blocking: true
    pass_criteria: 可访问性无A级违规
  timeout_minutes: 120
  retry:
    max_attempts: 2
    backoff: fixed
- id: phase-4
  name: TDD开发与代码审查
  order: 1
  optional: false
  trigger_condition: UX/UI设计完成
  agents:
    primary:
    - frontend-stylist
    - frontend-developer
    supporting: []
  inputs:
  - name: 最终设计稿
    type: document
    required: true
    source_phase: phase-0
  - name: 设计规范文档
    type: document
    required: true
    source_phase: phase-0
  - name: 切图资源
    type: artifact
    required: true
  outputs:
  - name: 样式代码
    type: code
    validation: 还原度>=95%
  - name: UI组件库
    type: code
    validation: 响应式适配完成
  - name: 响应式页面
    type: code
    validation: 动效流畅
  quality_gates:
  - gate_id: VISUAL-REGRESSION
    blocking: true
    pass_criteria: 还原度>=95%
  - gate_id: DESIGN-REVIEW
    blocking: true
    pass_criteria: 响应式适配完成
  - gate_id: DESIGN-REVIEW
    blocking: false
    pass_criteria: 动效流畅
  timeout_minutes: 120
  retry:
    max_attempts: 2
    backoff: fixed
- id: phase-5
  name: 验证
  order: 2
  optional: false
  trigger_condition: 前端实现完成
  agents:
    primary:
    - ux-designer
    - e2e-tester
    supporting: []
  inputs:
  - name: 实现的界面
    type: code
    required: true
    source_phase: phase-4
  - name: 测试用户
    type: document
    required: false
  outputs:
  - name: 可用性测试报告
    type: document
    validation: 任务完成率>=80%
  - name: 优化建议清单
    type: document
  - name: 迭代版本
    type: code
  quality_gates:
  - gate_id: UX-ACCEPTANCE
    blocking: true
    pass_criteria: 任务完成率>=80%
  - gate_id: UX-ACCEPTANCE
    blocking: true
    pass_criteria: 用户满意度>=4/5
  - gate_id: TEST-PASS
    blocking: true
    pass_criteria: 关键问题已修复
  timeout_minutes: 60
  retry:
    max_attempts: 2
    backoff: fixed
agent_matrix:
  ux-designer:
    phases:
    - phase-0
    - phase-5
    role: primary
    max_parallel_instances: 1
  ui-designer:
    phases:
    - phase-0
    role: primary
    max_parallel_instances: 1
  frontend-stylist:
    phases:
    - phase-4
    role: primary
    max_parallel_instances: 1
  frontend-developer:
    phases:
    - phase-4
    role: primary
    max_parallel_instances: 1
  e2e-tester:
    phases:
    - phase-5
    role: primary
    max_parallel_instances: 1
exception_handling:
  phase_failure:
    action: retry_then_escalate
    escalation_target: orchestrator
    max_retries: 3
  agent_unavailable:
    action: substitute_and_continue
    substitute_agent: frontend-developer
  quality_gate_blocked:
    action: auto_fix_then_pause
    auto_fix_agents:
    - frontend-stylist
    - frontend-developer
---

# UI/UX设计专项工作流

## 描述

专注于用户界面设计和用户体验优化的工作流，涵盖从用户研究到设计交付的完整流程。该工作流强调以用户为中心的设计理念，确保产品既美观又易用。

## 触发条件

- 用户请求UI/UX设计
- 新功能界面设计
- 现有界面优化
- 用户体验改进
- 设计系统构建
- 用户明确要求"UI设计"、"UX设计"、"界面设计"、"用户体验"

## 涉及的Agent

### 核心Agent

| Agent | 角色 | 职责 |
|-------|------|------|
| ux-designer | UX设计师 | 用户研究、交互设计 |
| ui-designer | UI设计师 | 视觉设计、组件设计 |
| frontend-stylist | 前端样式师 | 样式实现、响应式适配 |
| frontend-developer | 前端开发者 | 组件开发 |
| e2e-tester | E2E测试工程师 | 可用性测试 |

### 支撑Agent

| Agent | 角色 | 职责 |
|-------|------|------|
| product-manager | 产品经理 | 需求确认、优先级 |
| desktop-ui-adapter | 桌面UI适配师 | 桌面窗口/菜单/交互适配 |

## 阶段定义

### 阶段1：UX/UI设计

**主要执行者**: ux-designer, ui-designer
**支撑者**: product-manager, desktop-ui-adapter

**输入**:
- 产品需求
- 用户画像
- 业务目标

**活动**:
1. 用户研究：用户访谈与分析、竞品分析、用户旅程映射、痛点识别
2. 交互设计：信息架构设计、交互流程设计、线框图绘制、原型制作
3. 视觉设计：设计系统定义、高保真设计稿、组件设计、设计规范文档
4. 设计系统建立：定义设计令牌、组件库规范、切图资源
5. 可访问性检查：无障碍评估、WCAG 2.1 AA标准合规检查
6. 桌面窗口布局设计：窗口尺寸适配、系统菜单设计、桌面特有交互设计、平台规范适配

**输出**:
- 用户研究报告
- 用户旅程图
- 高保真设计稿
- 设计系统文档
- 桌面窗口布局规范
- 系统菜单结构图

**质量门禁**:
- [ ] 设计评审通过且符合品牌规范
- [ ] 可访问性无A级违规
- [ ] 用户画像清晰且痛点已识别
- [ ] 组件可复用
- [ ] 窗口尺寸适配方案完整
- [ ] 菜单结构符合各平台规范

---

### 阶段2：TDD开发与代码审查

**主要执行者**: frontend-stylist, frontend-developer

**输入**:
- 最终设计稿
- 设计规范文档
- 切图资源

**活动**:
1. 设计令牌转CSS变量：将设计系统中的颜色、间距、字体等令牌转换为CSS自定义属性
2. UI组件库开发：基于设计系统文档，采用TDD方式开发可复用UI组件
3. 响应式页面实现：适配不同设备和屏幕尺寸，确保布局一致性
4. 动效实现：实现交互反馈动效、页面过渡动效，确保流畅性

**输出**:
- 样式代码
- UI组件库
- 响应式页面

**质量门禁**:
- [ ] 还原度 >= 95%
- [ ] 响应式适配完成
- [ ] 动效流畅

---

### 阶段3：验证

**主要执行者**: ux-designer, e2e-tester

**输入**:
- 实现的界面
- 测试用户

**活动**:
1. 可用性测试：执行可用性测试、收集用户反馈
2. 视觉回归测试：对比设计稿与实现界面，检查视觉还原度
3. 优化建议：分析问题、整理优化建议清单
4. 迭代改进：根据测试结果进行迭代优化

**输出**:
- 可用性测试报告
- 优化建议清单
- 迭代版本

**质量门禁**:
- [ ] 任务完成率 >= 80%
- [ ] 用户满意度 >= 4/5
- [ ] 关键问题已修复

## 异常处理

| 异常类型 | 处理策略 | 详情 |
|----------|----------|------|
| 阶段失败 | 重试后升级 | 最多重试3次，之后升级至编排器 |
| Agent不可用 | 替换并继续 | 由frontend-developer作为替代Agent |
| 质量门禁阻塞 | 自动修复后暂停 | 由frontend-stylist和frontend-developer尝试自动修复 |
