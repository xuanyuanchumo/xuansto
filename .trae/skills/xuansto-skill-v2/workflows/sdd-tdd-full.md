---
metadata:
  name: SDD+TDD完整开发工作流
  version: "3.2.0"
  description: 完整9阶段SDD+TDD融合开发工作流
  platform: all
  min_agents: 5
  max_agents: 15
phases:
- id: phase-0
  name: UX/UI设计
  order: 0
  optional: false
  trigger_condition: 项目启动且需要UI/UX设计
  agents:
    primary:
    - ux-designer
    - ui-designer
    supporting:
    - product-manager
    - frontend-stylist
    - desktop-ui-adapter
  inputs:
  - name: 产品需求概述
    type: document
    required: true
  - name: 用户画像
    type: document
    required: true
  - name: 业务目标
    type: document
    required: true
  outputs:
  - name: UX研究报告
    type: document
    validation: 用户旅程完整
  - name: 高保真设计稿
    type: document
    validation: 设计评审通过
  - name: 桌面窗口布局规范
    type: document
    validation: 窗口尺寸适配方案明确
  - name: 系统菜单结构图
    type: document
    validation: 菜单结构合理
  - name: 交互说明文档
    type: document
  quality_gates:
  - gate_id: DESIGN-REVIEW
    blocking: true
    pass_criteria: 设计评审通过且设计令牌与技术栈兼容
  - gate_id: DESIGN-ACCESSIBILITY
    blocking: true
    pass_criteria: 可访问性无A级违规
  timeout_minutes: 120
  retry:
    max_attempts: 2
    backoff: fixed
- id: phase-1
  name: 需求分析
  order: 1
  optional: false
  trigger_condition: UX/UI设计完成或跳过
  agents:
    primary:
    - product-manager
    supporting: []
  inputs:
  - name: 用户需求描述
    type: document
    required: true
  - name: 业务背景信息
    type: document
    required: true
  outputs:
  - name: 需求规格说明书
    type: document
    validation: 需求已获用户确认
  - name: 用户故事列表
    type: document
    validation: 符合INVEST原则
  - name: 验收标准文档
    type: document
    validation: 验收标准明确可测试
  - name: 平台需求分析报告
    type: document
  quality_gates:
  - gate_id: GATE-001
    blocking: true
    pass_criteria: 所有用户故事符合INVEST原则
  - gate_id: GATE-001
    blocking: true
    pass_criteria: 验收标准明确可测试且歧义已解决
  timeout_minutes: 60
  retry:
    max_attempts: 2
    backoff: fixed
- id: phase-2
  name: 架构设计
  order: 2
  optional: false
  trigger_condition: 需求分析完成
  agents:
    primary:
    - system-architect
    supporting: []
  inputs:
  - name: 需求规格说明书
    type: document
    required: true
    source_phase: phase-1
  - name: 用户故事列表
    type: document
    required: true
    source_phase: phase-1
  outputs:
  - name: 架构设计文档
    type: document
    validation: 符合SOLID原则
  - name: API接口规范
    type: document
    validation: 接口定义清晰完整
  - name: 数据模型图
    type: document
  - name: 技术决策记录
    type: document
    validation: 技术选型有充分理由
  - name: 跨平台架构方案
    type: document
  - name: 桌面框架选型ADR
    type: document
  quality_gates:
  - gate_id: GATE-003
    blocking: true
    pass_criteria: 架构设计符合SOLID原则
  - gate_id: GATE-004
    blocking: true
    pass_criteria: 接口定义清晰完整且跨平台边界明确
  timeout_minutes: 90
  retry:
    max_attempts: 2
    backoff: fixed
- id: phase-3
  name: 测试策略
  order: 3
  optional: false
  trigger_condition: 架构设计完成
  agents:
    primary:
    - test-architect
    supporting: []
  inputs:
  - name: 架构设计文档
    type: document
    required: true
    source_phase: phase-2
  - name: 用户故事列表
    type: document
    required: true
    source_phase: phase-1
  outputs:
  - name: 测试策略文档
    type: document
  - name: 测试用例清单
    type: document
    validation: 覆盖所有用户故事
  - name: 测试数据方案
    type: document
  - name: 桌面测试用例清单
    type: document
  quality_gates:
  - gate_id: GATE-005
    blocking: true
    pass_criteria: 测试覆盖所有用户故事
  - gate_id: GATE-006
    blocking: true
    pass_criteria: 测试用例可自动化执行且边界条件已覆盖
  timeout_minutes: 60
  retry:
    max_attempts: 2
    backoff: fixed
- id: phase-4
  name: TDD开发与代码审查
  order: 4
  optional: false
  trigger_condition: 测试策略完成
  agents:
    primary:
    - fullstack-engineer
    - unit-tester
    - code-reviewer
    supporting:
    - frontend-stylist
    - desktop-ui-adapter
    - native-module-developer
  inputs:
  - name: 架构设计文档
    type: document
    required: true
    source_phase: phase-2
  - name: 测试用例清单
    type: document
    required: true
    source_phase: phase-3
  outputs:
  - name: 源代码文件
    type: code
    validation: 代码审查通过
  - name: 单元测试文件
    type: code
    validation: 覆盖率>=80%
  - name: 代码覆盖率报告
    type: document
    validation: 覆盖率>=80%
  - name: 代码审查报告
    type: document
  - name: 改进建议清单
    type: document
  quality_gates:
  - gate_id: TEST-PASS
    blocking: true
    pass_criteria: 所有测试用例通过
  - gate_id: GATE-005
    blocking: true
    pass_criteria: 代码覆盖率>=80%
  - gate_id: GATE-002
    blocking: true
    pass_criteria: 所有Spec-Drift标记已按影响级别复核
  timeout_minutes: 240
  retry:
    max_attempts: 3
    backoff: exponential
- id: phase-5
  name: 验证
  order: 5
  optional: false
  trigger_condition: TDD开发与代码审查通过
  agents:
    primary:
    - qa-engineer
    - security-auditor
    - ai-penetration-tester
    - performance-tester
    supporting: []
  inputs:
  - name: 通过审查的代码
    type: code
    required: true
    source_phase: phase-4
  - name: 测试用例清单
    type: document
    required: true
    source_phase: phase-3
  - name: 安全测试清单
    type: document
    required: true
  outputs:
  - name: 测试执行报告
    type: document
    validation: 通过率和覆盖率达标
  - name: 安全审计报告
    type: document
    validation: 无P0/P1安全问题
  - name: 性能测试报告
    type: document
  - name: 视觉差异报告
    type: document
  - name: 可访问性违规清单
    type: document
  - name: 规格一致性报告
    type: document
  - name: 桌面跨平台兼容性报告
    type: document
    validation: 三平台功能一致性>95%
  quality_gates:
  - gate_id: TEST-PASS
    blocking: true
    pass_criteria: 所有测试通过
  - gate_id: GATE-012
    blocking: true
    pass_criteria: 无P0/P1安全问题
  - gate_id: GATE-005
    blocking: true
    pass_criteria: 覆盖率达标且视觉差异<1%
  timeout_minutes: 120
  retry:
    max_attempts: 2
    backoff: fixed
- id: phase-6
  name: 验收
  order: 6
  optional: false
  trigger_condition: 验证阶段通过
  agents:
    primary:
    - product-manager
    supporting:
    - desktop-developer
    - build-release-engineer
  inputs:
  - name: Phase5验证通过的产物
    type: document
    required: true
    source_phase: phase-5
  - name: 用户故事和验收标准
    type: document
    required: true
    source_phase: phase-1
  outputs:
  - name: 用户验收测试报告
    type: document
  - name: 合规检查清单签署
    type: document
  - name: 文档完整性报告
    type: document
  - name: 体验验收报告
    type: document
  - name: 正式发布建议
    type: document
    validation: 批准或驳回
  quality_gates:
  - gate_id: UX-ACCEPTANCE
    blocking: true
    pass_criteria: 所有验收标准通过
  - gate_id: GATE-013
    blocking: true
    pass_criteria: 无阻塞性问题且文档覆盖率100%
  timeout_minutes: 60
  retry:
    max_attempts: 2
    backoff: fixed
- id: phase-7
  name: 迭代
  order: 7
  optional: true
  trigger_condition: 验证或验收阶段未通过
  agents:
    primary:
    - orchestrator
    - refactoring-specialist
    supporting:
    - fullstack-engineer
    - test-architect
  inputs:
  - name: 验证阶段或验收阶段的反馈
    type: document
    required: true
    source_phase: phase-5
  outputs:
  - name: 修复后的代码
    type: code
    validation: 修复项验证通过
  - name: 迭代总结报告
    type: document
  - name: 学习到的模式
    type: document
  - name: 更新后的规格文档
    type: document
  - name: RCA报告
    type: document
    validation: RCA已完成并归档
  - name: 安全工单闭环记录
    type: document
  - name: 知识同步日志
    type: document
  quality_gates:
  - gate_id: TEST-PASS
    blocking: true
    pass_criteria: 所有修复项验证通过
  - gate_id: TEST-PASS
    blocking: true
    pass_criteria: 回归测试通过
  - gate_id: GATE-015
    blocking: false
    pass_criteria: RCA报告已完成并归档
  timeout_minutes: 120
  retry:
    max_attempts: 3
    backoff: exponential
- id: phase-8
  name: 构建与发布
  order: 8
  optional: false
  trigger_condition: 验收通过
  agents:
    primary:
    - build-release-engineer
    - desktop-developer
    supporting:
    - cicd-specialist
  inputs:
  - name: 部署通过的代码
    type: code
    required: true
    source_phase: phase-6
  - name: 桌面打包配置
    type: document
    required: true
  outputs:
  - name: 多平台安装包
    type: artifact
    validation: 所有平台构建成功
  - name: 代码签名证书
    type: artifact
    validation: 签名与公证通过
  - name: 自动更新配置文件
    type: document
    validation: 自动更新功能验证通过
  - name: 发布说明文档
    type: document
    validation: 发布说明完整
  - name: 分发清单
    type: document
  quality_gates:
  - gate_id: DESKTOP-BUILD
    blocking: true
    pass_criteria: 所有平台构建成功
  - gate_id: DESKTOP-SIGN
    blocking: true
    pass_criteria: 代码签名与公证通过
  - gate_id: DESKTOP-UPDATE
    blocking: true
    pass_criteria: 自动更新功能验证通过
  timeout_minutes: 180
  retry:
    max_attempts: 2
    backoff: exponential
agent_matrix:
  ux-designer:
    phases:
    - phase-0
    role: primary
    max_parallel_instances: 1
  ui-designer:
    phases:
    - phase-0
    role: primary
    max_parallel_instances: 1
  product-manager:
    phases:
    - phase-1
    - phase-6
    role: primary
    max_parallel_instances: 1
  system-architect:
    phases:
    - phase-2
    role: primary
    max_parallel_instances: 1
  test-architect:
    phases:
    - phase-3
    role: primary
    max_parallel_instances: 1
  fullstack-engineer:
    phases:
    - phase-4
    role: primary
    max_parallel_instances: 3
  unit-tester:
    phases:
    - phase-4
    role: primary
    max_parallel_instances: 2
  code-reviewer:
    phases:
    - phase-4
    role: primary
    max_parallel_instances: 2
  qa-engineer:
    phases:
    - phase-5
    role: primary
    max_parallel_instances: 1
  security-auditor:
    phases:
    - phase-5
    role: primary
    max_parallel_instances: 1
  ai-penetration-tester:
    phases:
    - phase-5
    role: primary
    max_parallel_instances: 1
  performance-tester:
    phases:
    - phase-5
    role: primary
    max_parallel_instances: 1
  orchestrator:
    phases:
    - phase-7
    role: primary
    max_parallel_instances: 1
  refactoring-specialist:
    phases:
    - phase-7
    role: primary
    max_parallel_instances: 1
  build-release-engineer:
    phases:
    - phase-8
    role: primary
    max_parallel_instances: 1
  desktop-developer:
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
    - refactoring-specialist
---

# SDD+TDD完整开发工作流

## 描述

完整9阶段SDD（Story-Driven Development）+ TDD（Test-Driven Development）软件开发工作流，适用于中大型项目的系统性开发。该工作流融合了三省六部二十四司协同机制，确保从需求分析到迭代交付的全生命周期质量保障，并支持桌面/跨平台应用开发。

## 触发条件

- 用户请求完整的软件开发流程
- 项目规模：中大型（预估开发周期 > 2周）
- 需要完整的文档和测试覆盖
- 涉及多个模块或组件的开发
- 用户明确要求"完整流程"、"全生命周期"、"SDD+TDD"

## 涉及的Agent

### 核心Agent

| Agent | 角色 | 职责 |
|-------|------|------|
| ux-designer | UX设计师 | 用户研究、交互设计（阶段0） |
| ui-designer | UI设计师 | 视觉设计、设计系统定义（阶段0） |
| product-manager | 产品经理 | 需求分析、用户故事编写、验收（阶段1、6） |
| system-architect | 系统架构师 | 架构设计、技术选型（阶段2） |
| test-architect | 测试架构师 | 测试策略设计（阶段3） |
| fullstack-engineer | 全栈工程师 | 代码实现（阶段4） |
| unit-tester | 单元测试工程师 | TDD测试编写（阶段4） |
| code-reviewer | 代码审查工程师 | 代码质量把关（阶段4） |
| qa-engineer | QA工程师 | 全量测试执行（阶段5） |
| orchestrator | 编排器 | 迭代调度与修复协调（阶段7） |
| refactoring-specialist | 重构专家 | 代码优化与重构（阶段7） |
| build-release-engineer | 构建发布工程师 | 桌面打包、签名、分发（阶段8） |
| desktop-developer | 桌面开发工程师 | 桌面原生实现、IPC通信（阶段8） |

### 支撑Agent

| Agent | 角色 | 职责 |
|-------|------|------|
| security-auditor | 安全审计师 | 安全扫描与审计（阶段5） |
| ai-penetration-tester | AI渗透测试工程师 | AI自主渗透测试（阶段5） |
| performance-tester | 性能测试工程师 | 性能基准测试（阶段5） |
| frontend-stylist | 前端样式专家 | 前端样式实现与设计令牌同步（阶段0、4） |
| desktop-ui-adapter | 桌面UI适配师 | 桌面端UI适配（阶段0、4） |
| native-module-developer | 原生模块开发者 | 原生模块开发与集成（阶段4） |
| cicd-specialist | CI/CD专家 | 持续集成与部署流水线（阶段8） |

## 阶段定义

### 阶段0: UX/UI设计 **执行者**: ux-designer, ui-designer

**辅助**: product-manager, frontend-stylist, desktop-ui-adapter

**输入**:
- 产品需求概述
- 用户画像
- 业务目标

**活动**:
1. 用户研究与交互设计：分析用户画像，梳理用户旅程地图，定义核心交互流程
2. 视觉设计与设计系统定义：建立设计令牌（颜色、字体、间距），创建组件库规范
3. 桌面窗口尺寸设计：定义最小/默认/全屏布局方案，确保不同分辨率下的适配
4. 系统菜单设计：设计应用菜单、右键菜单、托盘菜单的层级结构与交互逻辑
5. 桌面特有交互模式设计：规划拖拽行为、系统通知集成、全局快捷键绑定

**输出**:
- UX研究报告（验证：用户旅程完整）
- 高保真设计稿（验证：设计评审通过）
- 桌面窗口布局规范（验证：窗口尺寸适配方案明确）
- 系统菜单结构图（验证：菜单结构合理）
- 交互说明文档

**质量门禁**:
- [ ] 用户旅程完整
- [ ] 桌面窗口尺寸适配方案明确
- [ ] 系统菜单结构合理
- [ ] 设计评审通过
- [ ] 设计令牌与开发技术栈兼容性验证
- [ ] 可访问性无A级违规

---

### 阶段1: 需求分析 **执行者**: product-manager

**输入**:
- 用户需求描述
- 业务背景信息

**活动**:
1. 需求收集与整理：从用户描述中提取功能需求和非功能需求，消除歧义
2. 用户故事编写（User Story）：按照"作为...我希望...以便..."格式编写，确保符合INVEST原则
3. 验收标准定义（Acceptance Criteria）：为每个用户故事定义明确的、可测试的验收条件
4. 优先级排序：基于业务价值和技术依赖关系对用户故事进行优先级排列
5. 平台类型识别：确定目标平台类型（Web/桌面/移动/跨平台），输出平台需求分析报告

**输出**:
- 需求规格说明书（验证：需求已获用户确认）
- 用户故事列表（验证：符合INVEST原则）
- 验收标准文档（验证：验收标准明确可测试）
- 平台需求分析报告

**质量门禁**:
- [ ] 所有用户故事符合INVEST原则
- [ ] 验收标准明确可测试
- [ ] 需求已获得用户确认
- [ ] 所有歧义问题已解决或标注为待定

---

### 阶段2: 架构设计 **执行者**: system-architect

**输入**:
- 需求规格说明书
- 用户故事列表

**活动**:
1. 系统架构设计：确定整体架构风格（分层/微服务/事件驱动），定义模块边界与依赖关系
2. 模块划分与接口定义：将系统拆分为高内聚低耦合的模块，定义模块间通信接口
3. 技术选型决策：评估并选择框架、库、中间件，记录技术决策理由（ADR）
4. 数据模型设计：设计实体关系图，定义数据存储方案与访问策略
5. 跨平台架构决策：确定共享逻辑层与平台特定实现层的边界划分策略
6. 桌面框架选型ADR：评估Electron/Tauri/Qt/WPF等方案，输出选型决策记录

**输出**:
- 架构设计文档（验证：符合SOLID原则）
- API接口规范（验证：接口定义清晰完整）
- 数据模型图
- 技术决策记录（ADR）
- 跨平台架构方案
- 桌面框架选型ADR

**质量门禁**:
- [ ] 架构设计符合SOLID原则
- [ ] 接口定义清晰完整
- [ ] 技术选型有充分理由
- [ ] 设计令牌与代码组件一一对应
- [ ] 跨平台架构边界已明确

---

### 阶段3: 测试策略 **执行者**: test-architect

**输入**:
- 架构设计文档
- 用户故事列表

**活动**:
1. 测试策略制定：确定测试层级（单元/集成/E2E）、测试范围和测试优先级
2. 测试用例设计：基于用户故事和验收标准编写测试用例，确保正向和反向场景覆盖
3. 测试数据规划：准备测试数据集，包括边界值、异常数据和隐私脱敏数据
4. 自动化测试框架搭建：选择并配置测试运行器、断言库、Mock工具等基础设施
5. 桌面特有测试用例设计：覆盖窗口管理、系统菜单、托盘图标、文件系统访问、IPC通信、自动更新等场景

**输出**:
- 测试策略文档
- 测试用例清单（验证：覆盖所有用户故事）
- 测试数据方案
- 桌面测试用例清单

**质量门禁**:
- [ ] 测试覆盖所有用户故事
- [ ] 测试用例可自动化执行
- [ ] 边界条件和异常场景已覆盖
- [ ] 非功能测试用例清单通过System Architect审核

---

### 阶段4: TDD开发与代码审查 **执行者**: fullstack-engineer, unit-tester, code-reviewer

**辅助**: frontend-stylist, desktop-ui-adapter, native-module-developer

**输入**:
- 架构设计文档
- 测试用例清单

**活动**:
1. **Red**：编写失败的测试用例，明确预期行为和验收条件
2. **Green**：编写最小代码使测试通过，不做过度设计
3. **Refactor**：重构代码优化结构，消除重复，提升可读性和可维护性
4. **Verify**：快速回归验证重构未引入新问题
5. 桌面IPC通信实现：实现主进程与渲染进程之间的安全通信通道
6. 原生模块集成：集成Node.js Native Addon或Rust FFI，处理跨语言调用与内存管理
7. 跨平台并行开发：共享逻辑层统一实现，平台适配层分别开发
8. **代码审查**（code-reviewer执行）：代码规范检查、设计模式审查、安全漏洞扫描、性能问题识别、桌面特有代码审查（IPC安全性、原生模块内存管理、跨平台兼容性）

**规格漂移处理与自动调整权限分配**:
- **低影响漂移**（仅影响单个函数或组件内部实现细节）：Agent可自行补全，但需在提交信息中标记 `Spec-Drift: [low] <说明>`，并在PR中阐述变更。Specification Keeper事后审核并决定是否更新规格文档。
- **中影响漂移**（影响模块间接口或数据格式）：Agent立即暂停，上报Orchestrator。Orchestrator联合System Architect快速评估，若方案明确且风险可控，授权修改并通知Specification Keeper更新规格；若出现不确定因素，转为高影响处理。
- **高影响漂移**（影响外部API契约、安全模型、关键业务逻辑、跨平台共享层）：必须触发"人机协作断点"，等待Product Manager或对应人类负责人确认。此级别漂移强制要求人工介入，不得由Agent自主决策。
- 所有Spec-Drift标记将在质量门禁SPEC-CONSISTENCY中汇总，按影响级别分别复核。

**增量实施约束**:
- Agent必须遵循"分解复杂任务→实现单个步骤→测试验证→重构"的工作模式
- 若在同一错误上连续3次尝试失败，必须停止、记录反模式到知识库、从头重新开始
- 此约束参考@hivehub/rulebook的增量实施规则

**设计令牌同步**:
- 设计令牌（CSS变量/JS对象）必须与设计系统保持一致，通过design-tokens-sync.js脚本自动同步

**Git分支规则**:
- 每个功能开发必须在独立的feature/*分支上进行
- 分支命名规则：feature/<功能简述>
- 跨平台功能建议使用feature/<功能>-cross-platform命名

**输出**:
- 源代码文件（验证：代码审查通过）
- 单元测试文件（验证：覆盖率>=80%）
- 代码覆盖率报告（验证：覆盖率>=80%）
- 代码审查报告
- 改进建议清单

**质量门禁**:
- [ ] 所有测试用例通过
- [ ] 代码覆盖率 >= 80%
- [ ] 无严重代码异味
- [ ] SPEC-CONSISTENCY：所有Spec-Drift标记已按影响级别复核
- [ ] 代码审查通过（无严重代码问题，所有审查意见已处理，代码符合团队规范）

---

### 阶段5: 验证 **执行者**: qa-engineer, security-auditor, ai-penetration-tester, performance-tester

**输入**:
- 通过审查的代码
- 测试用例清单
- 安全测试清单

**活动**:
1. 全量测试执行：单元+集成+E2E+桌面专项，强制包含非功能基础设施测试
2. 安全扫描：SAST静态分析 + 依赖漏洞扫描，识别已知CVE和潜在安全风险
3. AI自主渗透测试：利用AI代理模拟攻击者行为，发现逻辑漏洞和权限绕过
4. 性能基准测试：建立性能基线，检测响应时间、内存占用、CPU利用率等指标
5. 规格一致性校验：对所有Spec-Drift标记进行最终复核，确认规格与实现一致
6. 文档完整性检查：验证API文档、部署文档与代码实现的一致性
7. 视觉回归测试：使用Chromatic/Percy等工具检测UI视觉差异
8. 可访问性自动化测试：使用axe-core等工具检测WCAG合规性
9. 桌面专项验证：窗口行为自动化测试（Spectron/Playwright for Electron）、安装包完整性验证（文件校验、签名验证）、跨平台兼容性矩阵测试（Windows 10/11, macOS 13+, Ubuntu 22.04+）、系统集成测试（系统托盘、通知、文件关联、自动启动）

**输出**:
- 测试执行报告（验证：通过率和覆盖率达标）
- 安全审计报告（验证：无P0/P1安全问题）
- 性能测试报告
- 视觉差异报告
- 可访问性违规清单
- 规格一致性报告
- 桌面跨平台兼容性报告（验证：三平台功能一致性>95%）

**质量门禁**:
- [ ] 所有测试通过
- [ ] 无P0/P1安全问题
- [ ] 覆盖率达标
- [ ] 视觉差异 < 1%（需人工审核）
- [ ] 桌面三平台功能一致性 > 95%

---

### 阶段6: 验收 **执行者**: product-manager

**辅助**: desktop-developer, build-release-engineer

**输入**:
- Phase 5验证通过的产物
- 用户故事和验收标准

**活动**:
1. 用户验收测试（UAT）：基于用户故事和验收标准，模拟最终用户执行关键场景
2. 合规验收：检查GDPR/PCI-DSS等法规要求（如适用）
3. 文档验收：确保用户手册、API文档、部署指南完整且与实现一致
4. 体验验收：检查设计实现是否与设计稿一致，可用性指标是否达标（任务完成率≥95%，满意度≥4/5）
5. 性能验收：验证是否满足非功能性需求（响应时间、并发用户等）
6. 安全验收：确认所有安全门禁已通过，无未修复的中高危漏洞
7. 桌面端专项验收：安装包可直接安装并成功启动、自动更新流程端到端验证通过、应用商店审核要求检查（如适用）、桌面端用户手册操作步骤准确性验证

**输出**:
- 用户验收测试报告
- 合规检查清单签署
- 文档完整性报告
- 体验验收报告
- 正式发布建议（验证：批准或驳回）

**质量门禁**:
- [ ] 所有验收标准通过
- [ ] 无阻塞性问题
- [ ] 文档覆盖率100%（关键文档）
- [ ] 体验指标达标
- [ ] 桌面安装与更新验证通过
- [ ] 若验收不通过，返回阶段7迭代修复

---

### 阶段7: 迭代 **执行者**: orchestrator, refactoring-specialist

**辅助**: fullstack-engineer, test-architect

**输入**:
- 验证阶段或验收阶段的反馈

**活动**:
1. 失败测试分析与修复：优先采用结构化根因分析（RCA），定位问题根因并实施修复
2. 安全问题修复：按严重等级排序修复安全漏洞，确保修复不引入新问题
3. 代码优化与重构：消除技术债务，提升代码质量和可维护性
4. 设计不一致调整：修复视觉差异，确保实现与设计稿一致
5. 桌面跨平台兼容性问题修复：解决平台特定问题，确保三平台行为一致
6. 模式学习：将成功模式和反模式持久化到知识库，供后续开发参考
7. 知识库更新：同步更新经验知识条目，确保知识库与代码库同步
8. 规格文档与设计文档同步更新：确保规格文档反映最新实现状态

**智能迭代调度与优先级排序**:
- 当验证或验收暴露出多个待修复项时，Orchestrator根据优先级矩阵自动生成修复计划
- 优先级：阻塞性Gate失败 > 高影响范围（多个模块/用户旅程/多平台受影响） > 低影响范围 > 低修复置信度（需人工介入）
- 修复价值评估 = 阻塞等级 × 影响范围系数 + 修复置信度，按评分降序执行
- 增量验证策略：根据代码变更范围，由Test Architect智能选择受影响测试子集执行，而非每次全量回归

**人机协作断点**:
- 工作流中定义以下决策检查点，当满足条件时系统自动暂停并生成决策报告，等待人类输入：
  - 验收不通过，且产品方向可能需要调整
  - 发现Spec存在逻辑漏洞，且属于高影响漂移
  - 连续迭代3次仍未收敛（相同Gate重复失败）
  - 安全渗透测试发现高危零日漏洞，需人工评估业务风险
- 其余低影响、中影响Spec漂移及明确的技术修复，可由系统自主决策并记录日志

**根因分析框架**:
- 当发生测试失败、安全漏洞或运行时异常时，负责修复的Agent必须遵循RCA模板：
  - **症状**：可观察到的错误现象，精确到日志/堆栈
  - **直接原因**：导致症状的直接代码缺陷或配置错误
  - **根本原因**：为什么会存在这个直接原因？流程/设计/假设的哪个环节出错？
  - **修复措施**：解决根本原因的具体代码变更
  - **预防措施**：如何防止同类问题再次发生？包括新增测试用例、知识库条目、规范更新等
  - **影响范围评估**：此根本原因可能影响的其它模块/服务
- 报告自动存储为经验知识库条目（experience/errors/）
- 每完成一个Bug修复，Test Architect必须自动生成至少一个回归测试用例

**安全修复闭环**:
- 将AI Penetration Tester、Security Auditor、Developer和Test Architect串联为自动工作流：
  1. AI Penetration Tester发现漏洞 → 自动创建安全工单
  2. Security Auditor验证并确认漏洞，指派给对应的Developer Agent
  3. Developer Agent实施修复，同时Test Architect生成回归测试
  4. 修复分支提交后，自动触发AI Penetration Tester复测
  5. 闭环完成，工单关闭，经验沉淀

**跨分支经验同步**:
- Specification Keeper在阶段7迭代完成后，评估新沉淀的知识条目是否具有通用性
- 对于高置信度（≥0.8）且标记为"安全修复"或"常见错误"的条目，自动创建knowledge-sync/<brief-description>分支，向所有活跃的feature/*分支发起合并请求
- 若目标分支已有冲突经验，知识库合并流程自动触发条目去重和置信度比较
- 所有跨分支同步操作记录在knowledge/sync-log.md

**扩展自愈范围**:
- DevOps Engineer和Runtime Supervisor可尝试在沙箱中自动修复常见环境配置问题（环境变量缺失、端口冲突、依赖服务不可用），验证后自动提交修复PR
- 当Spec自身被发现逻辑漏洞时，Specification Keeper在更新规格后，自动触发级联影响分析，标记下游产物中需要同步修改的部分，并生成相应的修复任务

**输出**:
- 修复后的代码（验证：修复项验证通过）
- 迭代总结报告
- 学习到的模式
- 更新后的规格文档
- RCA报告（验证：RCA已完成并归档）
- 安全工单闭环记录
- 知识同步日志

**质量门禁**:
- [ ] 所有修复项验证通过
- [ ] 回归测试通过
- [ ] RCA报告已完成并归档
- [ ] 安全工单全部闭环
- [ ] 跨分支知识同步已完成或已记录待处理
- [ ] 知识库已更新

**回退路径**:
- 如发现架构层问题则返回阶段2
- 如发现实现层问题则返回阶段4
- 如发现部署配置问题则返回阶段6

---

### 阶段8: 构建与发布 **执行者**: build-release-engineer, desktop-developer

**辅助**: cicd-specialist

**输入**:
- 部署通过的代码
- 桌面打包配置

**活动**:
1. 多平台构建：Windows/macOS/Linux并行构建，生成各平台安装包
2. 代码签名与公证：Apple Notarization / Windows Authenticode，确保安装包可信
3. 自动更新配置：配置增量更新/全量更新策略，定义更新检查频率和回滚机制
4. 安装包测试：验证MSI/DMG/AppImage/DEB等格式安装包的安装、卸载和升级流程
5. 分发渠道配置：配置官网下载、应用商店、内部分发等渠道
6. 发布说明编写：汇总功能变更、修复项、已知问题和升级指南

**输出**:
- 多平台安装包（验证：所有平台构建成功）
- 代码签名证书（验证：签名与公证通过）
- 自动更新配置文件（验证：自动更新功能验证通过）
- 发布说明文档（验证：发布说明完整）
- 分发清单

**质量门禁**:
- [ ] 所有平台构建成功
- [ ] 代码签名与公证通过
- [ ] 安装包在目标平台可正常安装运行
- [ ] 自动更新功能验证通过
- [ ] 发布说明完整

## 异常处理

| 异常类型 | 处理策略 | 详情 |
|----------|----------|------|
| 阶段失败 | 重试后升级 | 最多重试3次，失败后升级至orchestrator |
| Agent不可用 | 替换并继续 | 使用fullstack-engineer作为替代Agent |
| 质量门禁阻塞 | 自动修复后暂停 | 由fullstack-engineer和refactoring-specialist尝试自动修复，失败则暂停等待人工介入 |
| 连续迭代未收敛 | 触发人机协作断点 | 连续3次相同Gate失败，暂停并生成决策报告 |
| 高危安全漏洞 | 触发人机协作断点 | 发现零日漏洞，暂停等待人工评估业务风险 |
