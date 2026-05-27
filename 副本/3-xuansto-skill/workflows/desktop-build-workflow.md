---
metadata:
  name: 桌面构建与发布工作流
  version: "3.2.0"
  description: 桌面应用构建签名与发布工作流
  platform: desktop
  min_agents: 2
  max_agents: 6
phases:
- id: phase-4
  name: 构建准备
  order: 0
  optional: false
  trigger_condition: 桌面项目验收通过或用户请求构建发布
  agents:
    primary:
    - build-release-engineer
    - desktop-developer
    supporting: []
  inputs:
  - name: Phase6验收通过报告
    type: document
    required: true
  - name: 项目源代码
    type: code
    required: true
  - name: 构建配置文件
    type: document
    required: true
  outputs:
  - name: 构建环境检查报告
    type: document
    validation: 构建环境满足要求
  - name: 构建计划
    type: document
  - name: 版本信息文件
    type: document
    validation: 版本号合规且CHANGELOG已更新
  quality_gates:
  - gate_id: DESKTOP-BUILD
    blocking: true
    pass_criteria: 构建环境满足要求
  - gate_id: DESKTOP-SIGN
    blocking: true
    pass_criteria: 签名证书可用且未过期
  - gate_id: GATE-003
    blocking: true
    pass_criteria: 版本号合规
  - gate_id: DOC-COMPLETENESS
    blocking: true
    pass_criteria: CHANGELOG已更新
  timeout_minutes: 60
  retry:
    max_attempts: 2
    backoff: fixed
- id: phase-5
  name: 构建与签名验证
  order: 1
  optional: false
  trigger_condition: 构建准备完成
  agents:
    primary:
    - build-release-engineer
    - security-auditor
    supporting:
    - desktop-developer
    - cicd-specialist
  inputs:
  - name: 构建计划
    type: document
    required: true
    source_phase: phase-4
  - name: 项目源代码
    type: code
    required: true
  - name: 构建配置
    type: document
    required: true
  outputs:
  - name: 各平台安装包
    type: artifact
    validation: 所有目标平台构建成功
  - name: 已签名的安装包
    type: artifact
    validation: 所有平台签名验证通过
  - name: 签名验证报告
    type: document
  - name: 更新清单文件
    type: document
    validation: 更新清单格式正确
  quality_gates:
  - gate_id: DESKTOP-BUILD
    blocking: true
    pass_criteria: 所有目标平台构建成功
  - gate_id: DESKTOP-SIGN
    blocking: true
    pass_criteria: 所有平台签名验证通过且macOS公证通过
  - gate_id: DESKTOP-UPDATE
    blocking: true
    pass_criteria: 更新清单格式正确且回滚版本可用
  - gate_id: GATE-013
    blocking: true
    pass_criteria: 所有分发渠道可用
  timeout_minutes: 180
  retry:
    max_attempts: 2
    backoff: exponential
- id: phase-8
  name: 发布验证
  order: 2
  optional: false
  trigger_condition: 构建与签名验证通过
  agents:
    primary:
    - build-release-engineer
    - desktop-developer
    - cicd-specialist
    supporting:
    - security-auditor
  inputs:
  - name: 已签名的安装包
    type: artifact
    required: true
    source_phase: phase-5
  - name: 更新清单文件
    type: document
    required: true
    source_phase: phase-5
  outputs:
  - name: 安装验证报告
    type: document
    validation: 各平台安装卸载正常
  - name: 自动更新验证报告
    type: document
    validation: 自动更新流程验证通过
  - name: 安全验证报告
    type: document
    validation: 安全验证无问题
  - name: Release Notes
    type: document
    validation: 发布文档完整
  quality_gates:
  - gate_id: DESKTOP-BUILD
    blocking: true
    pass_criteria: 各平台安装卸载正常
  - gate_id: DESKTOP-UPDATE
    blocking: true
    pass_criteria: 自动更新流程验证通过
  - gate_id: GATE-012
    blocking: true
    pass_criteria: 安全验证无问题
  - gate_id: DOC-COMPLETENESS
    blocking: true
    pass_criteria: 发布文档完整
  timeout_minutes: 120
  retry:
    max_attempts: 2
    backoff: fixed
agent_matrix:
  build-release-engineer:
    phases:
    - phase-4
    - phase-5
    - phase-8
    role: primary
    max_parallel_instances: 1
  desktop-developer:
    phases:
    - phase-4
    - phase-8
    role: primary
    max_parallel_instances: 1
  security-auditor:
    phases:
    - phase-5
    role: primary
    max_parallel_instances: 1
  cicd-specialist:
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
    substitute_agent: build-release-engineer
  quality_gate_blocked:
    action: auto_fix_then_pause
    auto_fix_agents:
    - desktop-developer
    - build-release-engineer
---

# 桌面构建与发布工作流

## 描述

桌面应用构建与发布的系统化工作流，对应项目生命周期 Phase 8。该工作流覆盖从构建准备到分发验证的完整流程，确保桌面应用在各平台上的构建质量、签名安全、自动更新可靠性和分发可达性。

## 触发条件

- 桌面项目 Phase 6 验收通过
- 用户明确要求"构建桌面应用"、"发布桌面版本"、"打包桌面应用"
- 版本发布计划到达构建阶段
- 紧急热修复需要快速构建发布

## 涉及的Agent

### 核心Agent

| Agent | 角色 | 职责 |
|-------|------|------|
| build-release-engineer | 构建发布工程师 | 构建流程编排、发布执行 |
| desktop-developer | 桌面开发者 | 构建配置、原生模块处理 |
| security-auditor | 安全审计师 | 签名验证、安全检查 |
| cicd-specialist | CI/CD专家 | 流水线配置、自动化构建 |

## 阶段定义

### 阶段1：构建准备

**主要执行者**: build-release-engineer, desktop-developer

**输入**:
- Phase 6 验收通过报告
- 项目源代码
- 构建配置文件

**活动**:
1. 构建环境检查
   - 验证各平台构建工具链完整性
   - 检查 Node.js/Rust/Dart 版本
   - 验证原生编译环境
   - 确认磁盘空间与内存充足
2. 签名证书验证
   - 读取构建配置文件
   - 确认目标平台列表
   - 确认框架版本与依赖锁定
   - 确认签名证书与密钥可用且未过期
3. 版本号合规检查
   - 确认版本号（遵循 SemVer）
   - 更新 package.json / Cargo.toml / pubspec.yaml 版本
   - 生成版本信息文件
   - 确认 CHANGELOG 已更新
4. CHANGELOG更新
   - 确认 CHANGELOG 条目完整
   - 验证变更记录与版本号对应
5. 构建计划制定
   - 制定各平台构建顺序
   - 评估构建时间与资源需求
   - 制定构建失败回退策略
   - 通知相关干系人

**输出**:
- 构建环境检查报告
- 构建计划
- 版本信息文件

**质量门禁**:
- [ ] DESKTOP-BUILD: 构建环境满足要求
- [ ] DESKTOP-SIGN: 签名证书可用且未过期
- [ ] GATE-003: 版本号合规
- [ ] DOC-COMPLETENESS: CHANGELOG已更新

---

### 阶段2：构建与签名验证

**主要执行者**: build-release-engineer, security-auditor
**支撑执行者**: desktop-developer, cicd-specialist

**输入**:
- 构建计划
- 项目源代码
- 构建配置

**活动**:
1. 各平台安装包构建
   - 依赖安装与锁定
   - 主进程构建（编译主进程/后端代码、原生模块编译与链接、代码优化与 Tree-shaking）
   - 渲染进程构建（编译前端资源、资源压缩与哈希、静态资源内联/打包）
   - Windows 平台构建（NSIS/WiX）
   - macOS 平台构建（DMG/PKG）
   - Linux 平台构建（AppImage/deb/rpm）
   - 构建产物校验（文件完整性校验、SHA256 哈希计算、构建产物大小记录）
2. 代码签名与公证
   - Windows 代码签名（Authenticode 证书签名、SHA256 哈希签名、时间戳服务器签名）
   - macOS 代码签名（Developer ID Application 证书签名、硬化运行时配置）
   - macOS 公证（提交 Apple 公证请求、装订公证票据、公证结果验证）
   - Linux GPG 签名（GPG 密钥签名、签名文件生成、签名验证）
3. 签名验证
   - 各平台签名状态记录
   - 签名证书信息记录
   - 签名验证结果归档
4. 更新清单生成
   - 生成 latest.yml / latest-mac.yml / latest-linux.yml
   - 填充版本号、下载地址、哈希值、文件大小
   - 配置最低兼容版本
   - 配置强制更新规则
   - Delta 更新配置（计算差异、生成 delta 更新包、验证完整性）
   - 更新通道配置（stable/beta/alpha 通道、回滚版本信息）
5. 分发渠道检查
   - CDN/OSS 上传与缓存策略配置
   - GitHub Releases 创建与发布
   - 应用商店提交（如适用）
   - 分发验证（CDN 下载链接、GitHub Release 可访问、更新清单可获取）

**输出**:
- 各平台安装包
- 已签名的安装包
- 签名验证报告
- 更新清单文件

**质量门禁**:
- [ ] DESKTOP-BUILD: 所有目标平台构建成功
- [ ] DESKTOP-SIGN: 所有平台签名验证通过且macOS公证通过
- [ ] DESKTOP-UPDATE: 更新清单格式正确且回滚版本可用
- [ ] GATE-013: 所有分发渠道可用

---

### 阶段3：发布验证

**主要执行者**: build-release-engineer, desktop-developer, cicd-specialist
**支撑执行者**: security-auditor

**输入**:
- 已签名的安装包
- 更新清单文件

**活动**:
1. 安装卸载验证
   - Windows: 安装、启动、卸载验证
   - macOS: 安装、启动、卸载验证
   - Linux: 安装、启动、卸载验证
   - 记录安装过程问题
2. 自动更新验证
   - 从上一版本模拟更新
   - 验证全量更新流程
   - 验证增量更新流程（如适用）
   - 验证回滚机制
3. 安全验证
   - 签名验证（各平台）
   - 安全扫描
   - 权限检查
   - 网络安全验证
4. Release Notes编写
   - 生成 Release Notes
   - 更新 CHANGELOG
   - 生成升级指南
   - 生成已知问题清单
   - 发送发布通知
   - 更新官网下载页
   - 更新文档站点

**输出**:
- 安装验证报告
- 自动更新验证报告
- 安全验证报告
- Release Notes

**质量门禁**:
- [ ] DESKTOP-BUILD: 各平台安装卸载正常
- [ ] DESKTOP-UPDATE: 自动更新流程验证通过
- [ ] GATE-012: 安全验证无问题
- [ ] DOC-COMPLETENESS: 发布文档完整

## 异常处理

| 异常类型 | 处理策略 | 说明 |
|----------|----------|------|
| 阶段执行失败 | retry_then_escalate | 最多重试3次，之后升级至编排器 |
| Agent不可用 | substitute_and_continue | 由 build-release-engineer 替代继续执行 |
| 质量门禁阻塞 | auto_fix_then_pause | 由 desktop-developer 和 build-release-engineer 自动修复，修复失败则暂停 |
