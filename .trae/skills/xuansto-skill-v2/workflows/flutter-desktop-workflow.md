---
> 权威来源：_yaml/flutter-desktop-workflow.yaml（YAML为准，本文档为可读参考）
metadata:
  name: Flutter桌面应用开发工作流
  version: "3.2.0"
  description: Flutter桌面应用开发与构建工作流
  platform: desktop
  min_agents: 3
  max_agents: 8
phases:
- id: phase-0
  name: Flutter桌面架构设计
  order: 0
  optional: false
  trigger_condition: 用户请求Flutter桌面应用开发
  agents:
    primary:
    - system-architect
    - desktop-developer
    supporting: []
  inputs:
  - name: 产品需求文档
    type: document
    required: true
  - name: Flutter版本约束
    type: document
    required: true
  outputs:
  - name: Flutter架构设计文档
    type: document
    validation: 架构设计符合Flutter最佳实践
  - name: 桌面框架选型ADR
    type: document
    validation: Flutter桌面可行性已评估
  - name: 平台通道设计文档
    type: document
    validation: 平台通道接口已定义
  quality_gates:
  - gate_id: GATE-003
    blocking: true
    pass_criteria: 架构设计符合Flutter最佳实践
  - gate_id: GATE-004
    blocking: true
    pass_criteria: 平台通道接口已定义
  timeout_minutes: 90
  retry:
    max_attempts: 2
    backoff: fixed
- id: phase-4
  name: Flutter桌面TDD开发
  order: 1
  optional: false
  trigger_condition: 架构设计完成
  agents:
    primary:
    - fullstack-engineer
    - desktop-developer
    - desktop-ui-adapter
    supporting: []
  inputs:
  - name: Flutter架构设计文档
    type: document
    required: true
    source_phase: phase-0
  - name: 平台通道设计文档
    type: document
    required: true
    source_phase: phase-0
  outputs:
  - name: Flutter Dart代码
    type: code
    validation: 代码审查通过
  - name: 平台特定代码
    type: code
    validation: 原生代码审查通过
  - name: 测试代码
    type: code
    validation: 覆盖率>=80%
  - name: 集成测试代码
    type: code
  quality_gates:
  - gate_id: TEST-PASS
    blocking: true
    pass_criteria: 所有测试通过
  - gate_id: GATE-005
    blocking: true
    pass_criteria: 覆盖率>=80%
  - gate_id: GATE-009
    blocking: true
    pass_criteria: 代码审查通过
  timeout_minutes: 240
  retry:
    max_attempts: 3
    backoff: exponential
- id: phase-5
  name: Flutter桌面验证
  order: 2
  optional: false
  trigger_condition: TDD开发完成
  agents:
    primary:
    - qa-engineer
    - desktop-developer
    supporting: []
  inputs:
  - name: 通过审查的代码
    type: code
    required: true
    source_phase: phase-4
  outputs:
  - name: 跨平台测试报告
    type: document
    validation: 三平台功能一致性>95%
  - name: 性能测试报告
    type: document
    validation: 性能指标达标
  - name: 可访问性报告
    type: document
  quality_gates:
  - gate_id: DESKTOP-CROSS
    blocking: true
    pass_criteria: 三平台功能一致性>95%
  - gate_id: GATE-011
    blocking: true
    pass_criteria: 各平台冒烟测试通过
  - gate_id: PERFORMANCE
    blocking: true
    pass_criteria: 性能指标达标
  timeout_minutes: 120
  retry:
    max_attempts: 2
    backoff: fixed
- id: phase-8
  name: Flutter桌面构建与发布
  order: 3
  optional: false
  trigger_condition: 验证通过
  agents:
    primary:
    - build-release-engineer
    - desktop-developer
    supporting: []
  inputs:
  - name: 验证通过的代码
    type: code
    required: true
    source_phase: phase-5
  outputs:
  - name: MSIX安装包
    type: artifact
    validation: Windows构建成功
  - name: DMG安装包
    type: artifact
    validation: macOS构建成功
  - name: AppImage/DEB安装包
    type: artifact
    validation: Linux构建成功
  - name: 发布说明文档
    type: document
    validation: 发布说明完整
  quality_gates:
  - gate_id: DESKTOP-BUILD
    blocking: true
    pass_criteria: 所有平台构建成功
  - gate_id: DESKTOP-SIGN
    blocking: true
    pass_criteria: 代码签名与公证通过
  - gate_id: DOC-COMPLETENESS
    blocking: true
    pass_criteria: 发布说明完整
  timeout_minutes: 180
  retry:
    max_attempts: 2
    backoff: exponential
agent_matrix:
  system-architect:
    phases:
    - phase-0
    role: primary
    max_parallel_instances: 1
  desktop-developer:
    phases:
    - phase-0
    - phase-4
    - phase-5
    - phase-8
    role: primary
    max_parallel_instances: 1
  fullstack-engineer:
    phases:
    - phase-4
    role: primary
    max_parallel_instances: 2
  desktop-ui-adapter:
    phases:
    - phase-4
    role: primary
    max_parallel_instances: 1
  qa-engineer:
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
    substitute_agent: desktop-developer
  quality_gate_blocked:
    action: auto_fix_then_pause
    auto_fix_agents:
    - desktop-developer
    - fullstack-engineer
---

# Flutter桌面应用开发工作流

## 描述

Flutter桌面应用开发的专用工作流，涵盖架构设计、TDD开发、跨平台验证和构建发布的完整流程。该工作流针对Flutter框架特性进行优化，包括平台通道设计、原生插件集成、三平台一致性验证等Flutter桌面特有的开发挑战。

## 触发条件

- 用户请求Flutter桌面应用开发
- 项目技术栈包含Flutter
- 需要同时支持Windows/macOS/Linux的桌面应用
- 用户明确要求"Flutter桌面"、"Flutter Desktop"

## 涉及的Agent

### 核心Agent

| Agent | 角色 | 职责 |
|-------|------|------|
| system-architect | 系统架构师 | Flutter架构设计 |
| desktop-developer | 桌面开发者 | Flutter桌面开发、平台通道实现 |
| fullstack-engineer | 全栈工程师 | Dart代码实现 |
| desktop-ui-adapter | 桌面UI适配师 | Flutter UI适配 |
| qa-engineer | QA工程师 | 跨平台测试 |
| build-release-engineer | 构建发布工程师 | Flutter构建与发布 |

## 阶段定义

### 阶段1：Flutter桌面架构设计

**主要执行者**: system-architect, desktop-developer

**输入**:
- 产品需求文档
- Flutter版本约束

**活动**:
1. Flutter桌面可行性评估
   - 评估Flutter版本对目标平台的支持
   - 评估所需原生功能的可行性
   - 评估第三方包的桌面支持
   - 评估性能需求与Flutter渲染能力
2. 架构设计
   - 设计分层架构（Presentation/Business/Data）
   - 设计状态管理方案（Riverpod/Bloc/Provider）
   - 设计路由与导航方案
   - 设计依赖注入方案
3. 平台通道设计
   - 识别需要平台通道的功能
   - 设计MethodChannel接口
   - 设计EventChannel接口
   - 设计BasicMessageChannel接口
4. 原生插件选型与设计
   - 评估现有插件对桌面的支持
   - 设计需要自研的原生插件
   - 设计插件接口与平台实现
5. 桌面框架选型ADR
   - 评估Flutter vs Electron vs Tauri vs Qt
   - 输出选型决策记录

**输出**:
- Flutter架构设计文档
- 桌面框架选型ADR
- 平台通道设计文档

**质量门禁**:
- [ ] 架构设计符合Flutter最佳实践
- [ ] 平台通道接口已定义
- [ ] Flutter桌面可行性已评估

---

### 阶段2：Flutter桌面TDD开发

**主要执行者**: fullstack-engineer, desktop-developer, desktop-ui-adapter

**输入**:
- Flutter架构设计文档
- 平台通道设计文档

**活动**:
1. Dart层TDD开发
   - Red: 编写失败的Widget/Unit测试
   - Green: 实现最小功能代码
   - Refactor: 重构优化
   - Verify: 快速回归验证
2. 平台通道实现
   - 实现Dart侧平台通道调用
   - 实现Kotlin/Java侧通道处理（Android，如需）
   - 实现Swift侧通道处理（macOS/iOS，如需）
   - 实现C++侧通道处理（Windows/Linux）
3. 原生插件开发
   - 开发插件Dart接口
   - 开发各平台原生实现
   - 编写插件集成测试
4. UI适配
   - 适配不同屏幕尺寸
   - 适配鼠标/键盘交互
   - 适配桌面特有UI模式
   - 适配各平台视觉规范

**输出**:
- Flutter Dart代码
- 平台特定代码
- 测试代码
- 集成测试代码

**质量门禁**:
- [ ] 所有测试通过
- [ ] 覆盖率 >= 80%
- [ ] 代码审查通过

---

### 阶段3：Flutter桌面验证

**主要执行者**: qa-engineer, desktop-developer

**输入**:
- 通过审查的代码

**活动**:
1. 跨平台功能一致性测试
   - Windows平台功能测试
   - macOS平台功能测试
   - Linux平台功能测试
   - 三平台行为一致性验证
2. 性能测试
   - 启动时间测试
   - 内存占用测试
   - 滚动性能测试
   - 动画流畅度测试
3. 可访问性测试
   - Semantics节点验证
   - 屏幕阅读器兼容性
   - 键盘导航验证
   - 高对比度模式验证

**输出**:
- 跨平台测试报告
- 性能测试报告
- 可访问性报告

**质量门禁**:
- [ ] 三平台功能一致性 > 95%
- [ ] 各平台冒烟测试通过
- [ ] 性能指标达标

---

### 阶段4：Flutter桌面构建与发布

**主要执行者**: build-release-engineer, desktop-developer

**输入**:
- 验证通过的代码

**活动**:
1. Flutter构建配置
   - 配置构建模式（release/profile）
   - 配置目标平台
   - 配置树摇和代码分割
   - 配置Dart编译优化
2. 各平台构建
   - Windows: `flutter build windows` → MSIX打包
   - macOS: `flutter build macos` → DMG打包
   - Linux: `flutter build linux` → AppImage/DEB打包
3. 代码签名与公证
   - Windows代码签名
   - macOS代码签名与公证
4. 自动更新配置
   - 配置更新检查URL
   - 配置更新下载源
   - 配置回滚版本
5. 发布说明编写

**输出**:
- MSIX安装包
- DMG安装包
- AppImage/DEB安装包
- 发布说明文档

**质量门禁**:
- [ ] 所有平台构建成功
- [ ] 代码签名与公证通过
- [ ] 发布说明完整

## 异常处理

| 异常类型 | 处理策略 | 说明 |
|----------|----------|------|
| 阶段执行失败 | retry_then_escalate | 最多重试3次，之后升级至编排器 |
| Agent不可用 | substitute_and_continue | 由 desktop-developer 替代继续执行 |
| 质量门禁阻塞 | auto_fix_then_pause | 由 desktop-developer 和 fullstack-engineer 自动修复，修复失败则暂停 |