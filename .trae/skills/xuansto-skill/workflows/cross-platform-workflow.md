---
metadata:
  name: 跨平台协作开发工作流
  version: "3.2.0"
  description: 跨平台桌面与Web协同开发工作流
  platform: cross-platform
  min_agents: 3
  max_agents: 10
phases:
- id: phase-0
  name: 平台检测
  order: 0
  optional: false
  trigger_condition: 项目同时有Web和Desktop发布需求
  agents:
    primary:
    - fullstack-engineer
    - product-manager
    supporting: []
  inputs:
  - name: 项目需求文档
    type: document
    required: true
  - name: 技术栈约束
    type: document
    required: true
  - name: 目标用户画像
    type: document
    required: true
  outputs:
  - name: 平台需求分析报告
    type: document
    validation: Web与Desktop需求已明确区分
  - name: 技术栈选型方案
    type: document
    validation: 技术栈选型已确认
  - name: 平台差异矩阵
    type: document
    validation: 平台差异已识别并记录
  quality_gates:
  - gate_id: GATE-001-A
    blocking: true
    pass_criteria: Web与Desktop需求已明确区分
  - gate_id: GATE-003
    blocking: true
    pass_criteria: 技术栈选型已确认
  - gate_id: GATE-001-B
    blocking: true
    pass_criteria: 平台差异已识别并记录
  timeout_minutes: 60
  retry:
    max_attempts: 2
    backoff: fixed
- id: phase-2
  name: 共享层设计
  order: 1
  optional: false
  trigger_condition: 平台检测完成
  agents:
    primary:
    - fullstack-engineer
    - backend-developer
    supporting: []
  inputs:
  - name: 平台需求分析报告
    type: document
    required: true
    source_phase: phase-0
  - name: 技术栈选型方案
    type: document
    required: true
    source_phase: phase-0
  outputs:
  - name: 共享层架构设计文档
    type: document
    validation: 共享层与平台层边界清晰
  - name: API接口契约
    type: document
    validation: API接口契约已定义
  - name: 业务逻辑模块划分
    type: document
    validation: 业务逻辑无平台耦合
  quality_gates:
  - gate_id: GATE-003-A
    blocking: true
    pass_criteria: 共享层与平台层边界清晰
  - gate_id: GATE-004
    blocking: true
    pass_criteria: API接口契约已定义
  - gate_id: GATE-003-B
    blocking: true
    pass_criteria: 业务逻辑无平台耦合
  timeout_minutes: 90
  retry:
    max_attempts: 2
    backoff: fixed
- id: phase-4
  name: TDD开发与代码审查
  order: 2
  optional: false
  trigger_condition: 共享层设计完成
  agents:
    primary:
    - fullstack-engineer
    - desktop-developer
    - desktop-ui-adapter
    - backend-developer
    supporting: []
  inputs:
  - name: 共享层架构设计文档
    type: document
    required: true
    source_phase: phase-2
  - name: API接口契约
    type: document
    required: true
    source_phase: phase-2
  - name: 平台差异矩阵
    type: document
    required: true
    source_phase: phase-0
  outputs:
  - name: 共享层代码与测试
    type: code
    validation: 共享层测试覆盖率>=80%
  - name: Web端代码与测试
    type: code
    validation: Web端核心功能实现完成
  - name: Desktop端代码与测试
    type: code
    validation: Desktop端核心功能实现完成
  - name: 集成同步记录
    type: document
    validation: 两端功能对齐验证通过
  quality_gates:
  - gate_id: GATE-005
    blocking: true
    pass_criteria: 共享层测试覆盖率>=80%
  - gate_id: TEST-PASS-A
    blocking: true
    pass_criteria: Web端核心功能实现完成
  - gate_id: TEST-PASS-B
    blocking: true
    pass_criteria: Desktop端核心功能实现完成
  - gate_id: TEST-PASS-C
    blocking: true
    pass_criteria: 两端功能对齐验证通过
  timeout_minutes: 240
  retry:
    max_attempts: 3
    backoff: exponential
- id: phase-5
  name: 跨平台测试
  order: 3
  optional: false
  trigger_condition: 并行实现完成
  agents:
    primary:
    - unit-tester
    - desktop-developer
    - fullstack-engineer
    supporting: []
  inputs:
  - name: Web端构建产物
    type: artifact
    required: true
    source_phase: phase-4
  - name: Desktop端构建产物
    type: artifact
    required: true
    source_phase: phase-4
  - name: 测试用例集
    type: document
    required: true
  outputs:
  - name: 跨平台测试报告
    type: document
    validation: 核心功能一致性100%
  - name: 功能一致性矩阵
    type: document
  - name: 性能基准报告
    type: document
    validation: 性能指标达标
  - name: 兼容性测试报告
    type: document
  quality_gates:
  - gate_id: DESKTOP-CROSS
    blocking: true
    pass_criteria: 核心功能一致性100%
  - gate_id: GATE-011
    blocking: true
    pass_criteria: 各平台冒烟测试全部通过
  - gate_id: PERFORMANCE
    blocking: true
    pass_criteria: 性能指标达标
  - gate_id: GATE-012
    blocking: true
    pass_criteria: 无P0/P1级缺陷
  timeout_minutes: 120
  retry:
    max_attempts: 2
    backoff: fixed
- id: phase-8
  name: 统一验收与发布
  order: 4
  optional: false
  trigger_condition: 跨平台测试通过
  agents:
    primary:
    - build-release-engineer
    - desktop-developer
    supporting:
    - product-manager
  inputs:
  - name: 跨平台测试报告
    type: document
    required: true
    source_phase: phase-5
  - name: 功能一致性矩阵
    type: document
    required: true
    source_phase: phase-5
  - name: 各端构建产物
    type: artifact
    required: true
  outputs:
  - name: 统一验收报告
    type: document
    validation: Web端和Desktop端验收通过
  - name: 待改进项清单
    type: document
  - name: 发布就绪确认
    type: document
    validation: 无阻塞性问题
  quality_gates:
  - gate_id: UX-ACCEPTANCE-A
    blocking: true
    pass_criteria: Web端验收通过
  - gate_id: UX-ACCEPTANCE-B
    blocking: true
    pass_criteria: Desktop端验收通过
  - gate_id: DESKTOP-CROSS
    blocking: true
    pass_criteria: 跨平台一致性验收通过
  - gate_id: GATE-013
    blocking: true
    pass_criteria: 无阻塞性问题
  timeout_minutes: 90
  retry:
    max_attempts: 2
    backoff: fixed
agent_matrix:
  fullstack-engineer:
    phases:
    - phase-0
    - phase-2
    - phase-4
    - phase-5
    role: primary
    max_parallel_instances: 2
  product-manager:
    phases:
    - phase-0
    role: primary
    max_parallel_instances: 1
  backend-developer:
    phases:
    - phase-2
    - phase-4
    role: primary
    max_parallel_instances: 1
  desktop-developer:
    phases:
    - phase-4
    - phase-5
    - phase-8
    role: primary
    max_parallel_instances: 1
  desktop-ui-adapter:
    phases:
    - phase-4
    role: primary
    max_parallel_instances: 1
  unit-tester:
    phases:
    - phase-5
    role: primary
    max_parallel_instances: 1
  build-release-engineer:
    phases:
    - phase-8
    role: primary
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
    - desktop-developer
---

# 跨平台协作开发工作流

## 描述

面向同时具备 Web 与 Desktop 需求的项目，通过共享 API/业务逻辑层与独立 UI 层的架构策略，实现 Web 与 Desktop 端的并行开发与高效协作。该工作流确保两端功能一致性，同时尊重各平台的交互范式与用户体验差异。

## 触发条件

- 项目同时有 Web 与 Desktop 发布需求
- 需求文档明确包含多平台适配要求
- 产品路线图涵盖 Web 端与桌面端
- 用户明确要求"跨平台开发"、"Web+Desktop"、"多平台适配"

## 涉及的Agent

### 核心Agent

| Agent | 角色 | 职责 |
|-------|------|------|
| fullstack-engineer | 全栈工程师 | 共享层架构设计与实现 |
| desktop-developer | 桌面开发工程师 | Desktop 端原生能力与 UI 实现 |
| desktop-ui-adapter | 桌面UI适配工程师 | Web UI 到 Desktop UI 的适配转换 |
| backend-developer | 后端开发工程师 | API 层设计与实现 |

### 支撑Agent

| Agent | 角色 | 职责 |
|-------|------|------|
| code-reviewer | 代码审查工程师 | 跨平台代码一致性审查 |
| unit-tester | 单元测试工程师 | 共享层与平台层测试 |
| security-auditor | 安全审计师 | 跨平台安全策略审查 |
| product-manager | 产品经理 | 平台差异化需求协调 |

## 阶段定义

### Phase 0：平台检测

**执行者**: fullstack-engineer, product-manager

**输入**:
- 项目需求文档
- 技术栈约束
- 目标用户画像

**活动**:
1. 需求平台分析
   - 识别 Web 端功能需求
   - 识别 Desktop 端功能需求
   - 标注平台独有需求
   - 确认功能交集与差异
2. 技术栈评估
   - 评估现有技术栈兼容性
   - 确定桌面框架选型（Electron/Tauri/Flutter）
   - 确定前端框架选型
   - 评估跨平台共享可行性
3. 平台差异清单
   - 列出平台能力差异
   - 标注需要原生适配的功能
   - 确定降级方案
   - 制定平台特性矩阵

**输出**:
- 平台需求分析报告
- 技术栈选型方案
- 平台差异矩阵

**质量门禁**:
- [ ] Web 与 Desktop 需求已明确区分
- [ ] 技术栈选型已确认
- [ ] 平台差异已识别并记录

---

### Phase 2：共享层设计

**执行者**: fullstack-engineer, backend-developer

**输入**:
- 平台需求分析报告
- 技术栈选型方案

**活动**:
1. 共享 API 层设计
   - 定义统一 API 接口
   - 设计 API 版本策略
   - 规划离线/在线数据同步
   - 定义错误码与异常体系
2. 共享业务逻辑层设计
   - 抽取平台无关业务逻辑
   - 设计业务逻辑模块边界
   - 定义数据模型与状态管理
   - 设计事件/消息总线
3. 共享层接口契约
   - 定义 TypeScript 类型契约
   - 编写接口文档
   - 制定共享层变更规则
   - 建立契约测试

**输出**:
- 共享层架构设计文档
- API 接口契约
- 业务逻辑模块划分

**质量门禁**:
- [ ] 共享层与平台层边界清晰
- [ ] API 接口契约已定义
- [ ] 业务逻辑无平台耦合

---

### Phase 4：TDD开发与代码审查

**执行者**: fullstack-engineer, desktop-developer, desktop-ui-adapter, backend-developer

**输入**:
- 共享层架构设计文档
- API 接口契约
- 平台差异矩阵

**活动**:
1. 共享层实现
   - 实现 API 客户端
   - 实现业务逻辑模块
   - 实现数据模型与状态管理
   - 编写共享层单元测试
2. Web 端并行实现
   - 实现 Web UI 组件
   - 集成共享业务逻辑
   - 实现 Web 端特有功能
   - Web 端测试
3. Desktop 端并行实现
   - 实现 Desktop UI 适配
   - 集成共享业务逻辑
   - 实现桌面原生能力（文件系统、系统托盘、通知等）
   - Desktop 端测试
4. 持续同步与代码审查
   - 定期同步共享层变更
   - 解决集成冲突
   - 确保两端功能一致性
   - 跨平台代码一致性审查

**输出**:
- 共享层代码与测试
- Web 端代码与测试
- Desktop 端代码与测试
- 集成同步记录

**质量门禁**:
- [ ] 共享层测试覆盖率 ≥ 80%
- [ ] Web 端核心功能实现完成
- [ ] Desktop 端核心功能实现完成
- [ ] 两端功能对齐验证通过

---

### Phase 5：跨平台测试

**执行者**: unit-tester, desktop-developer, fullstack-engineer

**输入**:
- Web 端构建产物
- Desktop 端构建产物
- 测试用例集

**活动**:
1. 功能一致性测试
   - 对比验证 Web 与 Desktop 功能一致性
   - 验证共享业务逻辑行为一致
   - 验证 API 调用行为一致
   - 差异功能专项测试
2. 平台适配测试
   - Windows 平台功能测试
   - macOS 平台功能测试
   - Linux 平台功能测试
   - 各平台 UI 交互测试
3. 性能基准测试
   - Web 端性能基准
   - Desktop 端性能基准
   - 启动时间对比
   - 内存占用对比
4. 兼容性测试
   - 不同操作系统版本兼容性
   - 不同屏幕分辨率适配
   - 辅助功能可访问性
   - 国际化与本地化

**输出**:
- 跨平台测试报告
- 功能一致性矩阵
- 性能基准报告
- 兼容性测试报告

**质量门禁**:
- [ ] 核心功能一致性 100%
- [ ] 各平台冒烟测试全部通过
- [ ] 性能指标达标
- [ ] 无 P0/P1 级缺陷

---

### Phase 8：统一验收与发布

**执行者**: build-release-engineer, desktop-developer; 支撑: product-manager

**输入**:
- 跨平台测试报告
- 功能一致性矩阵
- 各端构建产物

**活动**:
1. 验收准备
   - 整理各端验收清单
   - 准备演示环境
   - 编写验收操作指南
2. 功能验收
   - Web 端功能验收
   - Desktop 端功能验收
   - 跨平台一致性验收
   - 平台特有功能验收
3. 体验验收
   - 各平台交互体验评估
   - UI 一致性检查
   - 性能体验评估
   - 可访问性验收
4. 验收结论与发布
   - 汇总验收结果
   - 记录待改进项
   - 确认发布就绪状态
   - 签署验收报告

**输出**:
- 统一验收报告
- 待改进项清单
- 发布就绪确认

**质量门禁**:
- [ ] Web 端验收通过
- [ ] Desktop 端验收通过
- [ ] 跨平台一致性验收通过
- [ ] 无阻塞性问题

## 异常处理

| 异常类型 | 处理策略 | 说明 |
|----------|----------|------|
| 阶段执行失败 | retry_then_escalate | 重试后升级至编排器，最多重试3次 |
| Agent不可用 | substitute_and_continue | 替换为 fullstack-engineer 继续执行 |
| 质量门禁阻塞 | auto_fix_then_pause | 由 fullstack-engineer 和 desktop-developer 自动修复后暂停 |
