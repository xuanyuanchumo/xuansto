# 质量门禁详细定义

> 版本: 4.1.0 | 更新日期: 2026-05-08 | 编码: UTF-8 | 行尾: LF

本文档包含 Xuansto Skill 的五十四项质量门禁完整定义。

## 门禁别名映射表

SKILL.md 及需求文档中引用门禁时使用语义化别名（如 TEST-PASS、COVERAGE），本文档使用结构化 ID（如 GATE-008）。下表为两者的映射关系。规则：每行仅保留非恒等映射（别名≠规范ID），已废弃别名标注(废弃)。

| 阶段 | 别名 (Alias) | 规范门禁ID | 说明 |
| ---- | ------------ | ---------- | ---- |
| **Phase 0** | DESIGN-REVIEW(废弃) | DESIGN-REVIEW-PRODUCT | 设计评审（已拆分为PRODUCT/TECH/DESIGN三项，此别名仅映射至PRODUCT） |
| **Phase 0** | DESIGN-ACCESSIBILITY(废弃) | DESIGN-SYSTEM-COMPLETE | 可访问性检查（已合并至设计系统完整性） |
| **Phase 0** | DESIGN-VISUAL-REGRESSION(废弃) | DESIGN-SYSTEM-COMPLETE | 视觉回归（已合并至设计系统完整性） |
| **Phase 1** | REQ-COMPLETENESS | GATE-001 | 需求完整性验证 |
| **Phase 1** | SPEC-DOC-CONSISTENCY | GATE-002 | 规格文档一致性验证 |
| **Phase 2** | ARCH-REVIEW | GATE-003 | 架构合理性验证 |
| **Phase 2** | CONTRACT | GATE-004 | 接口契约验证 |
| **Phase 3** | COVERAGE(废弃) | TEST-FIRST | 代码覆盖率达标（已合并至TEST-FIRST） |
| **Phase 3** | TEST-DESIGN(废弃) | TEST-FIRST | 测试数据和用例验证（已合并至TEST-FIRST） |
| **Phase 4** | LINT | GATE-007 | 代码规范检查（含编码+注释语言） |
| **Phase 4** | GATE-008(废弃) | TEST-PASS | 单元测试通过（已合并至TEST-PASS） |
| **Phase 4** | GATE-010(废弃) | TEST-PASS | 集成测试通过（已合并至TEST-PASS） |
| **Phase 4** | FILE-ENCODING(废弃) | GATE-007 | 文件编码格式（已合并至代码质量） |
| **Phase 4** | COMMENT-LANGUAGE(废弃) | GATE-007 | 注释语言规范（已合并至代码质量） |
| **Phase 4** | REVIEW-CONFIDENCE(废弃) | MULTI-PERSPECTIVE-COVERAGE | 审查置信度（已合并至多视角覆盖） |
| **Phase 4** | SUBAGENT-REVIEW(废弃) | GATE-009 | 子代理审查（已合并至代码审查） |
| **Phase 5** | E2E-TEST | GATE-011 | 端到端测试验证 |
| **Phase 5** | SECURITY | GATE-012 | 安全扫描验证 |
| **Phase 5** | SPEC-DRIFT | SPEC-CONSISTENCY | 规格与实现一致性验证 |
| **Phase 5** | AGENTIC-SEC(废弃) | AGENTIC-SECURITY | Agentic安全合规（请使用完整名AGENTIC-SECURITY） |
| **Phase 5** | CONSOLE-ERROR-FREE(废弃) | GATE-011 | 控制台无错误（已合并至E2E测试） |
| **Phase 5** | PLAYWRIGHT-E2E-PASS(废弃) | GATE-011 | Playwright E2E（已合并至E2E测试） |
| **Phase 5** | VISUAL-REGRESSION-PASS(废弃) | VISUAL-REGRESSION | 视觉回归通过（已合并至视觉回归） |
| **Phase 5** | A11Y | ACCESSIBILITY | 可访问性验证 |
| **Phase 6** | DEPLOY-READY | GATE-013 | 部署就绪验证 |
| **Phase 6** | PROD-VERIFY | GATE-014 | 生产环境验证 |
| **Phase 6** | UAT | GATE-013 | 用户验收测试验证 |
| **Phase 6** | INFRA-HEALTH(废弃) | GATE-014 | 基础设施健康（已合并至生产验证） |
| **Phase 7** | ITERATION-CLOSE | GATE-015 | 迭代闭环验证 |
| **Phase 7** | DOCUMENTATION | DOC-COMPLETENESS | 文档完整性检查 |
| **Phase 8** | IPC-CONTRACT | IPC-CONTRACT | IPC契约验证 |
| **跨阶段** | LOOP-COMPLETION(废弃) | ITERATION-BUDGET | 循环完成（已合并至迭代预算） |
| **跨阶段** | PLAN-PERSISTENCE(废弃) | SESSION-RECOVERY | 持久规划（已合并至会话恢复） |

## 目录

- [Phase 0: 设计阶段](#phase-0-设计阶段)
  - [DESIGN-REVIEW-PRODUCT: 产品评审门禁](#design-review-product-产品评审门禁)
  - [DESIGN-REVIEW-TECH: 技术评审门禁](#design-review-tech-技术评审门禁)
  - [DESIGN-REVIEW-DESIGN: 设计评审门禁](#design-review-design-设计评审门禁)
  - [DESIGN-TOKENS: Design Tokens完整性验证门禁](#design-tokens-design-tokens完整性验证门禁)
  - [DESIGN-SYSTEM-COMPLETE: 设计系统完整性门禁](#design-system-complete-设计系统完整性门禁)
  - [ANTI-PATTERN-CHECK: 行业反模式检查门禁](#anti-pattern-check-行业反模式检查门禁)
- [Phase 1: 需求阶段](#phase-1-需求阶段)
  - [GATE-001: 需求完整性门禁](#gate-001-需求完整性门禁)
  - [GATE-002: 规格一致性门禁](#gate-002-规格一致性门禁)
  - [BRAINSTORM-COMPLETE: 需求探索完整性门禁](#brainstorm-complete-需求探索完整性门禁)
- [Phase 2: 架构阶段](#phase-2-架构阶段)
  - [GATE-003: 架构合理性门禁](#gate-003-架构合理性门禁)
  - [GATE-004: 接口契约门禁](#gate-004-接口契约门禁)
  - [PLAN-ATOMIC: 计划原子性门禁](#plan-atomic-计划原子性门禁)
  - [SPEC-ATOMIC: 规格原子性门禁](#spec-atomic-规格原子性门禁)
- [Phase 3: 测试设计阶段](#phase-3-测试设计阶段)
  - [TEST-FIRST: 测试先行门禁](#test-first-测试先行门禁)
- [Phase 4: 代码实现阶段](#phase-4-代码实现阶段)
  - [GATE-007: 代码质量门禁](#gate-007-代码质量门禁)
  - [TEST-PASS: 单元测试与集成测试门禁](#test-pass-单元测试与集成测试门禁)
  - [GATE-009: 代码审查门禁](#gate-009-代码审查门禁)
  - [MULTI-PERSPECTIVE-COVERAGE: 多视角覆盖门禁](#multi-perspective-coverage-多视角覆盖门禁)
  - [TDD-RED: TDD红灯阶段门禁](#tdd-red-tdd红灯阶段门禁)
  - [TDD-GREEN: TDD绿灯阶段门禁](#tdd-green-tdd绿灯阶段门禁)
  - [TDD-REFACTOR: TDD重构阶段门禁](#tdd-refactor-tdd重构阶段门禁)
  - [EXECUTION-VERIFY: 执行验证门禁](#execution-verify-执行验证门禁)
  - [SCRIPT-SECURITY: 脚本安全约束合规门禁](#script-security-脚本安全约束合规门禁)
  - [SCRIPT-CLEANUP: 临时脚本清理验证门禁](#script-cleanup-临时脚本清理验证门禁)
  - [TOKEN-BUDGET: Token预算控制门禁](#token-budget-token预算控制门禁)
- [Phase 5: 测试验证阶段](#phase-5-测试验证阶段)
  - [GATE-011: 端到端门禁](#gate-011-端到端门禁)
  - [GATE-012: 安全扫描门禁](#gate-012-安全扫描门禁)
  - [SPEC-CONSISTENCY: 规格与实现一致性门禁](#spec-consistency-规格与实现一致性门禁)
  - [AGENTIC-SECURITY: Agentic安全合规门禁](#agentic-security-agentic安全合规门禁)
  - [AI-PENTEST: AI渗透测试门禁](#ai-pentest-ai渗透测试门禁)
  - [VISUAL-REGRESSION: 视觉回归测试门禁](#visual-regression-视觉回归测试门禁)
  - [RENDER-CHECK: 页面渲染验证门禁](#render-check-页面渲染验证门禁)
  - [ACCESSIBILITY: 可访问性门禁](#accessibility-可访问性门禁)
  - [PERFORMANCE: 性能基准门禁](#performance-性能基准门禁)
  - [SECURITY-FIX-CLOSED: 安全修复闭环门禁](#security-fix-closed-安全修复闭环门禁)
- [Phase 6: 验收阶段](#phase-6-验收阶段)
  - [GATE-013: 部署就绪门禁](#gate-013-部署就绪门禁)
  - [GATE-014: 生产验证门禁](#gate-014-生产验证门禁)
  - [UX-ACCEPTANCE: 用户体验验收门禁](#ux-acceptance-用户体验验收门禁)
  - [DOD-CHECK: Definition of Done门禁](#dod-check-definition-of-done门禁)
- [Phase 7: 迭代阶段](#phase-7-迭代阶段)
  - [GATE-015: 演化闭环门禁](#gate-015-演化闭环门禁)
  - [DOC-COMPLETENESS: 文档完整性门禁](#doc-completeness-文档完整性门禁)
  - [SIMPLIFICATION-BEHAVIOR: 简化行为等价门禁](#simplification-behavior-简化行为等价门禁)
  - [CHESTERTON-FENCE: Chesterton's Fence验证门禁](#chesterton-fence-chestertons-fence验证门禁)
- [Phase 8: 桌面端阶段](#phase-8-桌面端阶段)
  - [DESKTOP-BUILD: 桌面端构建门禁](#desktop-build-桌面端构建门禁)
  - [DESKTOP-SIGN: 代码签名门禁](#desktop-sign-代码签名门禁)
  - [DESKTOP-UPDATE: 自动更新门禁](#desktop-update-自动更新门禁)
  - [DESKTOP-CROSS: 跨平台一致性门禁](#desktop-cross-跨平台一致性门禁)
  - [IPC-CONTRACT: IPC契约门禁](#ipc-contract-ipc契约门禁)
- [门禁快速参考表](#门禁快速参考表)

***

## Phase 0: 设计阶段

### DESIGN-REVIEW-PRODUCT: 产品评审门禁

```yaml
名称: 产品评审通过
阶段: Phase 0
检查项:
  - 产品需求与设计稿对齐
  - 用户故事覆盖完整
  - 业务逻辑验证通过
  - 产品验收标准明确
通过条件: 产品评审会议通过（自主模式下：Product Manager Agent 置信度≥0.85 自动通过）
阻塞级别: BLOCK
自动化: 自主模式下自动（置信度≥0.85时），监督模式下需人工评审
```

***

### DESIGN-REVIEW-TECH: 技术评审门禁

```yaml
名称: 技术评审通过
阶段: Phase 0
检查项:
  - 技术可行性确认
  - 技术选型合理性
  - 性能可达成性评估
  - 安全架构评审通过
  - 技术风险识别与缓解
通过条件: 技术评审会议通过（自主模式下：System Architect Agent 置信度≥0.85 自动通过）
阻塞级别: BLOCK
自动化: 自主模式下自动（置信度≥0.85时），监督模式下需人工评审
```

***

### DESIGN-REVIEW-DESIGN: 设计评审门禁

```yaml
名称: 设计评审通过
阶段: Phase 0
检查项:
  - UI/UX设计稿完成
  - 设计评审会议通过
  - 设计与需求对齐
  - 无障碍设计审查通过
  - 设计规范一致性
通过条件: 设计稿评审通过（自主模式下：UI/UX Designer Agent 置信度≥0.85 自动通过）
阻塞级别: BLOCK
自动化: 自主模式下自动（置信度≥0.85时），监督模式下需人工评审
```

***

### DESIGN-TOKENS: Design Tokens完整性验证门禁

```yaml
名称: Design Tokens完整性验证
阶段: Phase 0
检查项:
  - 设计令牌定义完整(颜色/字体/间距/圆角/阴影)
  - 设计令牌与代码变量同步
  - 主题令牌(浅色/深色)定义完整
  - 平台适配令牌定义(桌面端/Web端)
  - 令牌变更记录可追溯
通过条件: 设计令牌与代码同步
阻塞级别: BLOCK
自动化: 是
```

- **依赖脚本**：`scripts/design-tokens-sync.js`

***

## Phase 1: 需求阶段

### GATE-001: 需求完整性门禁

```yaml
名称: 需求规格完整性验证
阶段: Phase 1
检查项:
  - 用户故事完整性
  - 验收标准明确性
  - 边界条件定义
  - 异常场景覆盖
通过条件: 完整性评分 >= 90分（自主模式下：Product Manager Agent 自动评分≥90 自动通过）
阻塞级别: BLOCK
自动化: 自主模式下自动（评分≥90时），监督模式下半自动
```

***

### GATE-002: 规格一致性门禁

```yaml
名称: 规格文档一致性验证
阶段: Phase 1
检查项:
  - 内部逻辑一致性
  - 与现有系统兼容性
  - 术语使用一致性
  - 版本控制正确性
通过条件: 无一致性错误
阻塞级别: BLOCK
自动化: 是
```

***

## Phase 2: 架构阶段

### GATE-003: 架构合理性门禁

```yaml
名称: 架构设计合理性验证
阶段: Phase 2
检查项:
  - 架构模式适用性
  - 模块划分合理性
  - 扩展性设计
  - 技术选型合理性
通过条件: 架构评审通过（自主模式下：System Architect Agent 置信度≥0.85 自动通过）
阻塞级别: BLOCK
自动化: 自主模式下自动（置信度≥0.85时），监督模式下需人工评审
```

***

### GATE-004: 接口契约门禁

```yaml
名称: 接口契约完整性验证
阶段: Phase 2
检查项:
  - API定义完整性
  - 数据模型一致性
  - 错误码定义
  - 版本兼容性
通过条件: 契约测试100%通过
阻塞级别: BLOCK
自动化: 是
```

- **依赖脚本**：`scripts/api-contract-validator.py`

***

### SPEC-ATOMIC: 规格原子性门禁

```yaml
名称: 规格原子性验证
阶段: Phase 2
检查项:
  - 每个规格项可独立测试
  - 规格项之间无隐式依赖
  - 每个规格项有明确输入输出定义
  - 规格项粒度适当（不可再分）
通过条件: 每个规格项可独立测试+无隐式依赖
阻塞级别: BLOCK
自动化: 是
```

***

## Phase 3: 测试设计阶段

### TEST-FIRST: 测试先行门禁

```yaml
名称: 测试先行验证
阶段: Phase 3
检查项:
  - 测试用例在设计阶段已编写
  - 每个功能点有对应测试用例
  - 单元测试覆盖
  - 集成测试覆盖
  - 边界条件测试
  - 异常路径测试
  - 测试数据完整性
  - 数据隔离性
  - 敏感数据脱敏
  - 数据生成脚本
通过条件: 测试用例先行设计+覆盖率>=80%+数据准备完成
阻塞级别: BLOCK
自动化: 是
```

> **已合并门禁**：GATE-005（测试覆盖）和 GATE-006（测试数据）已合并至本门禁。别名 COVERAGE 和 TEST-DESIGN 仍可使用，对应门禁ID为 TEST-FIRST。

***

## Phase 4: 代码实现阶段

### GATE-007: 代码质量门禁

```yaml
名称: 代码静态质量验证
阶段: Phase 4
检查项:
  - 代码规范检查
  - 复杂度分析
  - 重复代码检测
  - 安全漏洞扫描
  - TDD红-绿-重构循环执行验证（RED:测试先行且失败 / GREEN:最小实现使测试通过 / REFACTOR:重构后测试仍通过）
  - 测试先行验证（每个功能点有对应失败测试记录）
  - 重构阶段验证（重构后测试套件全通过，公共API不变）
  - 所有源代码文件为UTF-8 without BOM
  - 配置文件编码正确
  - 资源文件编码正确
  - 无混合编码文件
  - 无U+FFFD替换字符（编码损坏标记）
  - 业务注释包含中文说明
  - 技术注释语言一致性
  - 公共API注释完整性
  - 注释与代码同步
通过条件: 无严重问题，警告<5，TDD循环完整执行，编码UTF-8无BOM，无U+FFFD字符，业务注释含中文
阻塞级别: BLOCK
自动化: 是（linter+编码检测脚本+U+FFFD检测）
```

> **已合并门禁**：FILE-ENCODING（文件编码格式）和 COMMENT-LANGUAGE（注释语言规范）已合并至本门禁。别名 FILE-ENCODING 和 COMMENT-LANGUAGE 仍可使用，对应门禁ID为 GATE-007。

***

### TEST-PASS: 单元测试与集成测试门禁

```yaml
名称: 单元测试与集成测试执行验证
阶段: Phase 4/5
检查项:
  - 所有单元测试通过
  - 单元测试覆盖率达标
  - 所有集成测试通过
  - 模块集成接口兼容性
  - 数据流验证
  - 事务一致性
  - 无内存泄漏
通过条件: 100%测试通过（单元+集成）
阻塞级别: BLOCK
自动化: 是
```

注：GATE-008（单元测试通过）和 GATE-010（集成测试通过）已合并到本门禁TEST-PASS下，统一管理单元测试和集成测试的通过验证。

***

### GATE-009: 代码审查门禁

```yaml
名称: 代码审查完成验证
阶段: Phase 4
检查项:
  - 审查意见处理
  - 设计模式遵循
  - 文档更新
  - 知识沉淀
  - Stage 1计划合规性审查通过（合规率100%）
  - Stage 2代码质量审查通过（评分≥80）
  - 无需返工的任务
  - 圈复杂度≤10（单函数）
  - 无硬编码密钥/配置
  - 测试覆盖率≥80%
通过条件: 审查通过且无阻塞意见+两阶段审查通过+无返工任务（自主模式下：Code Reviewer+5子Agent 置信度≥0.85 自动通过）
阻塞级别: BLOCK
自动化: 自主模式下自动（置信度≥0.85时），监督模式下需人工审查
```

> **已合并门禁**：SUBAGENT-REVIEW（子代理两阶段审查）已合并至本门禁。别名 SUBAGENT-REVIEW 仍可使用，对应门禁ID为 GATE-009。

***

### TDD-RED: TDD红灯阶段门禁

```yaml
名称: TDD红灯阶段验证
阶段: Phase 4
检查项:
  - 失败测试已编写
  - 测试失败原因正确（非编译错误）
  - 测试覆盖目标功能点
  - 测试命名清晰表达意图
通过条件: 失败测试已编写且验证为失败
阻塞级别: BLOCK
自动化: 是
```

***

### TDD-GREEN: TDD绿灯阶段门禁

```yaml
名称: TDD绿灯阶段验证
阶段: Phase 4
检查项:
  - 最小代码实现使测试通过
  - 无多余实现
  - 所有红灯阶段测试通过
  - 未引入新失败测试
通过条件: 最小代码使所有测试通过
阻塞级别: BLOCK
自动化: 是
```

***

### TDD-REFACTOR: TDD重构阶段门禁

```yaml
名称: TDD重构阶段验证
阶段: Phase 4
检查项:
  - 代码已重构
  - 重构后所有测试仍通过
  - 公共API不变
  - 代码质量提升（复杂度降低/重复消除）
通过条件: 重构后测试仍通过+公共API不变
阻塞级别: WARN
自动化: 是
```

***

### EXECUTION-VERIFY: 执行验证门禁

```yaml
名称: 执行验证
阶段: Phase 4
检查项:
  - 代码编译无错误
  - 代码运行无崩溃
  - 依赖安装成功
  - 测试可执行
通过条件: 代码编译/运行成功+依赖安装成功+测试可执行
阻塞级别: BLOCK
自动化: 是
```

***

### SCRIPT-SECURITY: 脚本安全约束合规门禁

```yaml
名称: 脚本安全约束合规
阶段: Phase 4
阻塞级别: WARN / BLOCK
自动化: 是
依赖脚本: scripts/agentic-security-scanner.py
```

**检查内容**：
- Agent创建的脚本文件是否遵循语言选型矩阵（通用操作Python、Web前端Node.js、系统构建少量PowerShell）
- 是否存在禁止的Shell(.sh)脚本（Agent本地创建Shell脚本为[强制]禁止）
- 脚本是否包含硬编码密钥或敏感信息
- 脚本是否设置了适当的超时和资源限制

**通过标准**：
- WARN：脚本语言选型不完全符合矩阵，但不影响安全性
- BLOCK：存在Shell脚本、硬编码密钥、或无超时限制的危险脚本

**失败处理**：
1. 自动将Shell脚本转换为Python等效实现
2. 将硬编码密钥替换为环境变量引用
3. 为无超时脚本添加默认300秒超时限制

***

### SCRIPT-CLEANUP: 临时脚本清理门禁

```yaml
名称: 临时脚本清理验证
阶段: Phase 4 / Phase 7
阻塞级别: BLOCK
自动化: 是
```

**检查内容**：
- Agent创建的临时脚本是否在验证完成后被删除
- 脚本五步闭环是否完整执行（创建→审查→执行→验证→清理）
- 是否存在超过24小时未清理的临时脚本

**通过标准**：
- 所有临时脚本在验证通过后已被删除
- 五步闭环完整执行，无遗漏
- 无超过24小时的残留临时脚本

**失败处理**：
1. 自动清理超过24小时的临时脚本
2. 记录未完成五步闭环的脚本至经验知识库
3. 通知Orchestrator标记相关Agent的脚本清理合规性

- **依赖脚本**：`scripts/script-cleanup-checker.py`

***

### TOKEN-BUDGET: Token预算控制门禁

```yaml
名称: Token预算控制
阶段: 跨阶段（Phase 1-8）
阻塞级别: WARN / BLOCK
自动化: 是
配置文件: .skill-config.yaml
```

**检查内容**：
- 单任务Token消耗率是否在预算范围内
- 上下文压缩是否按需触发
- 并行Agent数量是否受Token预算约束

**通过标准**：
- Token使用率 < 80%：正常，无特殊动作
- Token使用率 80%~100%：WARN，自动触发上下文压缩，暂停非关键Agent
- Token使用率 ≥ 100%：BLOCK，强制降级为串行模式，拒绝新Agent激活

**失败处理**：
1. WARN级别：触发上下文压缩（Level 2语义压缩），暂停低优先级Agent
2. BLOCK级别：切换串行模式，执行最高级别压缩，通知用户选择（继续串行/增加预算/中止任务）
3. 当Token使用率降至70%以下时，自动恢复并行模式

***

## Phase 5: 测试验证阶段

### GATE-011: 端到端门禁

```yaml
名称: 端到端测试验证
阶段: Phase 5
检查项:
  - 用户流程测试
  - 跨系统集成
  - 真实数据验证
  - 回归测试
  - Playwright E2E测试全部通过
  - 无测试超时
  - 无Flaky测试
  - 用户旅程验证完整
  - 浏览器控制台无error级别日志
  - 无未捕获的JavaScript异常
  - 无资源加载失败
  - 无CORS错误
  - 页面渲染验证通过（引用RENDER-CHECK）
通过条件: E2E测试100%通过+Playwright通过+控制台无error
阻塞级别: BLOCK
自动化: 是（Playwright+RENDER-CHECK）
```

> **已合并门禁**：PLAYWRIGHT-E2E-PASS（Playwright E2E测试通过）和 CONSOLE-ERROR-FREE（控制台无错误）已合并至本门禁。别名 PLAYWRIGHT-E2E-PASS 和 CONSOLE-ERROR-FREE 仍可使用，对应门禁ID为 GATE-011。

***

### GATE-012: 安全扫描门禁

```yaml
名称: 安全合规验证
阶段: Phase 5
检查项:
  - 漏洞扫描
  - 依赖安全检查
  - 敏感信息检测
  - 权限配置审计
通过条件: 无高危漏洞
阻塞级别: BLOCK
自动化: 是
```

***

### AGENTIC-SECURITY: Agentic安全合规门禁

```yaml
名称: Agentic安全合规验证
阶段: Phase 5
检查项:
  - OWASP Agentic Top 10检查
  - Agent权限边界验证
  - 敏感操作审批机制
  - Agent行为审计日志
  - TrinityGuard三层风险评估
  - OWASP Agentic ASI01-ASI10十项风险检查
通过条件: 通过OWASP Agentic Top 10检查 + TrinityGuard三层评估通过
阻塞级别: BLOCK
自动化: 是
```

- **依赖脚本**：`scripts/agentic-security-scanner.py`

#### TrinityGuard三层评估检查项

**Layer 1 评估层（Prevention-Guard）检查项**:
- [ ] 20个TrinityGuard风险类别全部评估完毕
- [ ] Critical级别风险（TG-R01/R02/R04/R05/R17）已标记并进入修复流程
- [ ] High级别风险（TG-R03/R06/R07/R08/R09/R14/R16）已评估并有缓解措施
- [ ] 风险评分与OWASP ASI风险矩阵对齐
- [ ] 评估报告已纳入安全审计总报告

**Layer 2 运行时监控层（Detection-Guard）检查项**:
- [ ] Agent行为异常检测已启用（目标一致性/工具调用合规/输出安全）
- [ ] Agent间通信安全监控已启用（加密/完整性/防重放）
- [ ] 资源使用异常检测已启用（CPU/内存/网络/Token）
- [ ] 无未处理的安全告警
- [ ] 异常行为检测率 >= 95%

**Layer 3 LLM Judge Factory（Response-Guard）检查项**:
- [ ] 所有相关Judge已调度并执行
- [ ] 评判结果无冲突或冲突已解决
- [ ] TrinityGuard综合安全评分 >= 80
- [ ] 评估报告已纳入安全审计总报告

#### OWASP Agentic Top 10 2026 (ASI01-ASI10) 检查项

| 风险编号 | 风险名称 | 检查项 | 通过标准 |
|----------|----------|--------|----------|
| ASI01 | Agent Goal Hijack（目标劫持） | 直接/间接提示注入测试通过；目标完整性校验driftScore < 0.15 | 无成功注入；目标偏离度达标 |
| ASI02 | Tool Misuse & Exploitation（工具滥用） | 未授权工具访问测试通过；参数注入测试通过；递归调用检测通过 | 所有越权调用被阻断；注入被过滤 |
| ASI03 | Identity & Privilege Abuse（身份权限滥用） | 令牌伪造测试通过；委派链权限提升测试通过；身份冒充检测通过 | 所有伪造令牌被拒绝 |
| ASI04 | Agentic Supply Chain（供应链漏洞） | MCP服务器完整性验证通过；Prompt模板完整性校验通过；插件沙箱测试通过 | 被篡改组件被检测并隔离 |
| ASI05 | Unexpected Code Execution（意外代码执行） | 生成代码安全审查通过；执行沙箱测试通过；代码签名强制验证通过 | 恶意代码模式被检测；沙箱逃逸被阻止 |
| ASI06 | Memory & Context Poisoning（记忆中毒） | 长期记忆完整性校验通过；RAG数据源完整性测试通过；记忆隔离测试通过 | 被篡改记忆被检测并隔离 |
| ASI07 | Insecure Inter-Agent Comm（不安全Agent间通信） | 消息完整性验证通过；加密强制验证通过；重放攻击防护测试通过 | 所有通信加密且可验证 |
| ASI08 | Cascading Failures（级联故障） | 故障传播测试通过；检查点恢复测试通过；熔断机制验证通过 | 故障隔离在单Agent内 |
| ASI09 | Excessive Agency（过度自主） | 人工审批门禁测试通过；权限边界测试通过；操作审计日志验证通过 | 高风险操作需人工审批 |
| ASI10 | Observability Gaps（可观测性缺失） | 日志完整性检查通过；异常检测基线验证通过；审计追踪验证通过 | 日志覆盖率 >= 99.5% |

***

### AI-PENTEST: AI渗透测试门禁

```yaml
名称: AI渗透测试验证
阶段: Phase 5
检查项:
  - Prompt注入测试
  - 数据泄露测试
  - 权限提升测试
  - 模型幻觉风险测试
通过条件: 无高危可利用漏洞
阻塞级别: BLOCK
自动化: 是
```

- **依赖脚本**：`scripts/ai-pentest-runner.py`

***

### VISUAL-REGRESSION: 视觉回归测试门禁

```yaml
名称: 视觉回归测试验证
阶段: Phase 5
检查项:
  - 截图对比基线
  - 差异像素分析
  - 布局偏移检测
  - 主题切换一致性
  - 截屏对比无回归
  - 差异像素百分比<阈值(0.1%)
  - 响应式布局在不同视口下正确
通过条件: 差异像素<0.1%+布局无偏移+主题一致
阻塞级别: WARN/BLOCK
自动化: 是
```

> **已合并门禁**：VISUAL-REGRESSION-PASS（视觉回归测试通过）已合并至本门禁。别名 VISUAL-REGRESSION-PASS 仍可使用，对应门禁ID为 VISUAL-REGRESSION。

- **依赖脚本**：`scripts/visual-regression.js`

***

### RENDER-CHECK: 页面渲染验证门禁

```yaml
名称: 页面渲染验证
阶段: Phase 5
检查项:
  - 页面非白屏（body有内容且可见）
  - 无未捕获的JavaScript错误（window.onerror和console.error）
  - 关键DOM元素可见（通过配置的selector列表验证）
  - HTTP状态码为2xx
通过条件: 页面正常渲染，无白屏，无JS错误，关键元素可见
阻塞级别: WARN/BLOCK
自动化: 是（Playwright）
```

***

### ACCESSIBILITY: 可访问性门禁

```yaml
名称: 可访问性验证
阶段: Phase 5
检查项:
  - WCAG A级合规检查
  - 键盘导航可用性
  - 屏幕阅读器兼容性
  - 颜色对比度达标
通过条件: 无A级违规
阻塞级别: BLOCK
自动化: 是
```

- **依赖脚本**：`scripts/accessibility-test.js`

***

### SPEC-CONSISTENCY: 规格与实现一致性门禁

```yaml
名称: 规格与实现一致性验证
阶段: Phase 5
检查项:
  - 规格文档与代码实现100%一致
  - Spec-Drift标记项已确认
  - 接口定义与实现匹配
  - 数据模型与规格对齐
通过条件: 100%一致，含Spec-Drift标记项已确认
阻塞级别: BLOCK
自动化: 是
```

- **依赖脚本**：`scripts/spec-drift-detector.py`

***

### PERFORMANCE: 性能基准门禁

```yaml
名称: 性能基准验证
阶段: Phase 5
检查项:
  - 性能基准测试通过，关键指标未退化超过10%
  - 响应时间P95未退化>10%
  - 桌面应用冷启动<3秒
  - 内存占用未超过基线20%
通过条件: 响应时间P95未退化>10%，桌面应用冷启动<3秒
阻塞级别: WARN
自动化: 是
```

- **依赖脚本**：`scripts/performance-benchmark.js`

***

## Phase 6: 验收阶段

### GATE-013: 部署就绪门禁

```yaml
名称: 部署准备验证
阶段: Phase 6
检查项:
  - 部署清单完整
  - 回滚方案就绪
  - 监控配置完成
  - 告警规则配置
通过条件: 所有检查项通过
阻塞级别: BLOCK
自动化: 是
```

***

### GATE-014: 生产验证门禁

```yaml
名称: 生产环境验证
阶段: Phase 6
检查项:
  - 服务健康检查
  - 功能冒烟测试
  - 性能指标达标
  - 日志正常输出
  - 健康检查端点可访问且返回200
  - 指标端点可访问且返回200
  - 日志包含必要trace字段
  - 基础设施监控告警配置
通过条件: 生产验证通过+基础设施健康端点可访问
阻塞级别: BLOCK
自动化: 是
```

> **已合并门禁**：INFRA-HEALTH（基础设施健康）已合并至本门禁。别名 INFRA-HEALTH 仍可使用，对应门禁ID为 GATE-014。

***

### UX-ACCEPTANCE: 用户体验验收门禁

```yaml
名称: 用户体验验收验证
阶段: Phase 6
检查项:
  - 任务完成率验证
  - 系统可用性量表(SUS)评分
  - 用户操作路径分析
  - 关键流程耗时达标
通过条件: 任务完成率≥95%，SUS分数≥70（自主模式下：UX Designer Agent 自动评估通过即通过）
阻塞级别: BLOCK
自动化: 自主模式下自动（评估通过时），监督模式下半自动
```

***

### DOD-CHECK: Definition of Done门禁

```yaml
名称: Definition of Done检查
阶段: Phase 6
检查项:
  - 代码审查通过
  - 测试覆盖率达标
  - 安全扫描无高危漏洞
  - 文档完整
  - 性能未退化
  - 设计一致性>=95%
通过条件: 所有DoD项全部满足
阻塞级别: BLOCK
自动化: 是
```

***

## Phase 7: 迭代阶段

### GATE-015: 演化闭环门禁

```yaml
名称: 持续演化验证
阶段: Phase 7
检查项:
  - 监控数据收集
  - 性能基线对比
  - 问题追踪闭环
  - 知识库更新
通过条件: 演化报告完成
阻塞级别: WARN
自动化: 是
```

***

### DOC-COMPLETENESS: 文档完整性门禁

```yaml
名称: 文档完整性验证
阶段: Phase 7
检查项:
  - API文档覆盖率
  - 架构文档完整性
  - 运维文档完整性
  - 用户文档完整性
通过条件: 关键文档覆盖率100%
阻塞级别: BLOCK
自动化: 是
```

- **依赖脚本**：`scripts/documentation-coverage.py`

***

## Phase 8: 桌面端阶段

### DESKTOP-BUILD: 桌面端构建门禁

```yaml
名称: 桌面端安装包构建验证
阶段: Phase 8
检查项:
  - Windows安装包(NSIS/MSI)构建成功
  - macOS安装包(dmg)构建成功
  - Linux安装包(AppImage/deb/rpm)构建成功
  - 各平台安装包签名验证
  - 安装包体积在预期范围内
通过条件: 所有目标平台安装包构建成功
阻塞级别: BLOCK
自动化: 是
```

- **依赖脚本**：`scripts/build-desktop.ps1`

***

### DESKTOP-SIGN: 代码签名门禁

```yaml
名称: 代码签名与公证验证
阶段: Phase 8
检查项:
  - Windows代码签名验证通过(Authenticode)
  - macOS代码签名验证通过(codesign)
  - macOS公证验证通过(notarytool)
  - 无安全警告弹出
  - 签名证书未过期
通过条件: 代码签名验证通过，无安全警告
阻塞级别: BLOCK
自动化: 是
```

- **依赖脚本**：`scripts/sign-desktop.ps1`

***

### DESKTOP-UPDATE: 自动更新门禁

```yaml
名称: 自动更新端到端验证
阶段: Phase 8
检查项:
  - 更新检测正常触发
  - 更新包下载完整
  - 更新安装过程无错误
  - 更新后应用重启正常
  - 更新后版本号正确
  - 回滚机制可用
通过条件: 自动更新端到端通过（检测→下载→安装→重启）
阻塞级别: BLOCK
自动化: 是
```

- **依赖脚本**：`scripts/verify-auto-update.ps1`

***

### DESKTOP-CROSS: 跨平台一致性门禁

```yaml
名称: 三平台功能一致性验证
阶段: Phase 8
检查项:
  - 核心功能在Windows/macOS/Linux行为一致
  - UI布局跨平台一致性
  - 快捷键映射正确(Ctrl/Cmd)
  - 数据存储格式跨平台兼容
  - 平台特有功能降级策略合理
通过条件: 三平台功能一致性 > 95%
阻塞级别: WARN/BLOCK
自动化: 是
```

***

### IPC-CONTRACT: IPC契约门禁

```yaml
名称: IPC通道契约验证
阶段: Phase 8
检查项:
  - IPC通道定义与预加载脚本匹配
  - 主进程与渲染进程通信类型安全
  - contextBridge暴露API完整性
  - IPC消息序列化/反序列化正确
  - 无未声明的IPC通道
通过条件: IPC通道定义与预加载脚本100%匹配
阻塞级别: BLOCK
自动化: 是
```

- **依赖脚本**：`scripts/ipc-contract-validator.js`

***

## 门禁快速参考表

| 门禁ID | 名称 | 阶段 | 阻塞级别 | 自动化 |
| ------ | ---- | ---- | -------- | ------ |
| DESIGN-REVIEW-PRODUCT | 产品评审通过 | Phase 0 | BLOCK | 否 |
| DESIGN-REVIEW-TECH | 技术评审通过 | Phase 0 | BLOCK | 否 |
| DESIGN-REVIEW-DESIGN | 设计评审通过 | Phase 0 | BLOCK | 否 |
| DESIGN-TOKENS | Design Tokens完整性验证 | Phase 0 | BLOCK | 是 |
| DESIGN-SYSTEM-COMPLETE | 设计系统完整性验证（含可访问性+视觉回归） | Phase 0 | BLOCK | 是 |
| ANTI-PATTERN-CHECK | 行业反模式检查验证 | Phase 0 | BLOCK | 是 |
| GATE-001 | 需求规格完整性验证 | Phase 1 | BLOCK | 半自动 |
| GATE-002 | 规格文档一致性验证 | Phase 1 | BLOCK | 是 |
| BRAINSTORM-COMPLETE | 需求探索完整性验证 | Phase 1 | BLOCK | 半自动 |
| GATE-003 | 架构设计合理性验证 | Phase 2 | BLOCK | 否 |
| GATE-004 | 接口契约完整性验证 | Phase 2 | BLOCK | 是 |
| PLAN-ATOMIC | 计划原子性验证 | Phase 2 | BLOCK | 是 |
| SPEC-ATOMIC | 规格原子性验证 | Phase 2 | BLOCK | 是 |
| TEST-FIRST | 测试先行验证（含覆盖率+测试数据） | Phase 3 | BLOCK | 是 |
| GATE-007 | 代码静态质量验证（含编码+注释语言+U+FFFD检测） | Phase 4 | BLOCK | 是 |
| TEST-PASS | 单元测试与集成测试执行验证 | Phase 4/5 | BLOCK | 是 |
| GATE-009 | 代码审查完成验证（含子代理审查） | Phase 4 | BLOCK | 否 |
| MULTI-PERSPECTIVE-COVERAGE | 多视角审查覆盖验证（含审查置信度） | Phase 4 | WARN+BLOCK | 是 |
| TDD-RED | TDD红灯阶段验证 | Phase 4 | BLOCK | 是 |
| TDD-GREEN | TDD绿灯阶段验证 | Phase 4 | BLOCK | 是 |
| TDD-REFACTOR | TDD重构阶段验证 | Phase 4 | WARN | 是 |
| EXECUTION-VERIFY | 执行验证 | Phase 4 | BLOCK | 是 |
| SCRIPT-SECURITY | 脚本安全约束合规验证 | Phase 4 | WARN/BLOCK | 是 |
| SCRIPT-CLEANUP | 临时脚本清理验证 | Phase 4/7 | BLOCK | 是 |
| TOKEN-BUDGET | Token预算控制验证 | 跨阶段 | WARN/BLOCK | 是 |
| GATE-011 | 端到端测试验证（含Playwright+控制台检查+RENDER-CHECK） | Phase 5 | BLOCK | 是 |
| GATE-012 | 安全合规验证 | Phase 5 | BLOCK | 是 |
| SPEC-CONSISTENCY | 规格与实现一致性验证 | Phase 5 | BLOCK | 是 |
| AGENTIC-SECURITY | Agentic安全合规验证 | Phase 5 | BLOCK | 是 |
| AI-PENTEST | AI渗透测试验证 | Phase 5 | BLOCK | 是 |
| VISUAL-REGRESSION | 视觉回归测试验证（含通过验证） | Phase 5 | WARN/BLOCK | 是 |
| RENDER-CHECK | 页面渲染验证 | Phase 5 | WARN/BLOCK | 是 |
| ACCESSIBILITY | 可访问性验证 | Phase 5 | BLOCK | 是 |
| PERFORMANCE | 性能基准验证 | Phase 5 | WARN | 是 |
| SECURITY-FIX-CLOSED | 安全修复闭环验证 | Phase 5 | BLOCK | 是 |
| GATE-013 | 部署准备验证 | Phase 6 | BLOCK | 是 |
| GATE-014 | 生产环境验证（含基础设施健康） | Phase 6 | BLOCK | 是 |
| UX-ACCEPTANCE | 用户体验验收验证 | Phase 6 | BLOCK | 半自动 |
| DOD-CHECK | Definition of Done检查 | Phase 6 | BLOCK | 是 |
| GATE-015 | 持续演化验证 | Phase 7 | WARN | 是 |
| DOC-COMPLETENESS | 文档完整性验证 | Phase 7 | BLOCK | 是 |
| SIMPLIFICATION-BEHAVIOR | 简化行为等价验证 | Phase 7 | BLOCK | 是 |
| CHESTERTON-FENCE | Chesterton's Fence验证 | Phase 7 | WARN | 半自动 |
| DESKTOP-BUILD | 桌面端安装包构建验证 | Phase 8 | BLOCK | 是 |
| DESKTOP-SIGN | 代码签名与公证验证 | Phase 8 | BLOCK | 是 |
| DESKTOP-UPDATE | 自动更新端到端验证 | Phase 8 | BLOCK | 是 |
| DESKTOP-CROSS | 三平台功能一致性验证 | Phase 8 | WARN/BLOCK | 是 |
| IPC-CONTRACT | IPC通道契约验证 | Phase 8 | BLOCK | 是 |
| ITERATION-BUDGET | 迭代预算验证（含循环完成） | 跨阶段 | WARN+BLOCK | 是 |
| SESSION-RECOVERY | 会话恢复验证（含持久规划） | 跨阶段 | WARN | 是 |
| BUILD-SUCCESS | 构建成功验证 | 跨阶段 | BLOCK | 是 |
| ROLLBACK-SAFETY | 回滚安全验证 | 跨阶段 | BLOCK | 是 |
| INIT-COMPLETE | 初始化完成验证 | 跨阶段 | BLOCK | 是 |
| STATUS-HEALTHY | 状态健康验证 | 跨阶段 | WARN | 是 |

## 门禁异常处理规则

### PASS_WITH_NOTE状态

- 定义：门禁检查结果为"通过但存在注意事项"的状态
- 误报标记流程：Agent可在门禁结果上标记`PASS_WITH_NOTE`，附带说明文字描述为何认为该结果为误报
- 标记格式：`PASS_WITH_NOTE: <reason>`，reason必须包含具体的技术依据
- 记录位置：`.skill-logs/gate-exceptions.jsonl`

### 容差规则

- 数值型指标：±0.5%容差范围（如覆盖率要求80%，实际79.6%视为通过）
- 布尔型指标：无容差（必须严格满足）
- 比率型指标：2%容差范围（如性能基准要求<200ms，实际<204ms视为通过）
- 容差适用条件：仅适用于非安全类门禁，安全类门禁（SCRIPT-SECURITY、AGENTIC-SECURITY等）无容差

### 降级判定逻辑

- 连续2次WARN状态 → 自动升级为BLOCK
- 连续3次PASS_WITH_NOTE状态 → 触发人工审查断点
- 降级不可逆：一旦从PASS降级为WARN或BLOCK，不可自动恢复，必须通过人工审查确认
- 降级事件记录：`.skill-logs/gate-degradation.jsonl`，包含门禁ID、降级前状态、降级后状态、触发原因、时间戳

***

### SESSION-RECOVERY: 会话恢复门禁

```yaml
名称: 会话恢复验证
阶段: 跨阶段（Phase 0-8）
检查项:
  - /clear后成功恢复上下文（通过session-catchup.py）
  - 恢复后无信息丢失（当前阶段、已完成项、待完成项完整）
  - 恢复后决策记录连续性保持
  - 重大决策前已重新读取计划文件（task_plan.md / findings.md / progress.md）
  - 2-Action Rule执行：每2次搜索/浏览后已保存发现到findings.md
  - Phase完成时已通过plan-sync.py归档
通过条件: /clear后成功恢复上下文+无信息丢失+计划文件持久化
阻塞级别: WARN
自动化: 是
```

> **已合并门禁**：PLAN-PERSISTENCE（持久规划）已合并至本门禁。别名 PLAN-PERSISTENCE 仍可使用，对应门禁ID为 SESSION-RECOVERY。

**检查内容**：
- `/clear` 操作后是否使用 `session-catchup.py` 恢复上下文
- 恢复的上下文是否包含完整信息：当前阶段、已完成项、待完成项、决策记录
- 恢复后Agent是否基于恢复的上下文继续工作，而非从头开始
- 在执行重大决策（架构选择、技术选型、范围变更）前，是否已重新读取 `.agent_cache/<task-name>/` 下的计划文件
- 是否遵循2-Action Research Rule：每执行2次搜索或浏览操作后，立即将发现保存到 `findings.md`
- Phase完成时是否已通过 `plan-sync.py` 归档

**通过标准**：
- WARN：恢复后存在少量信息丢失（如最新一次会话的操作记录缺失），或计划文件存在但未在重大决策前重新读取
- 恢复成功：所有关键信息完整恢复，Agent可无缝继续工作，计划文件持久化正常

**失败处理**：
1. 自动重新执行 `session-catchup.py` 尝试恢复
2. 如仍失败，提示用户手动检查 `.agent_cache/<task-name>/` 目录
3. 记录恢复失败事件至 `.skill-logs/`

- **依赖脚本**：`scripts/session-catchup.py`

***

### MULTI-PERSPECTIVE-COVERAGE: 多视角覆盖门禁

```yaml
名称: 多视角审查覆盖验证
阶段: Phase 4
检查项:
  - Compliance Reviewer视角已覆盖
  - Bug Scanner视角已覆盖
  - History Analyzer视角已覆盖
  - Comment Verifier视角已覆盖
  - Specification Keeper视角已覆盖
  - 无遗漏审查维度
  - 所有问题置信度>=80
  - 无Critical级别问题未解决
  - 无High级别问题未解决
  - 置信度评分基于代码上下文相关性、问题可复现性、规则匹配度
通过条件: 5个审查视角全部覆盖+无遗漏维度+所有问题置信度>=80
阻塞级别: WARN+BLOCK
自动化: 是
```

> **已合并门禁**：REVIEW-CONFIDENCE（审查置信度）已合并至本门禁。别名 REVIEW-CONFIDENCE 仍可使用，对应门禁ID为 MULTI-PERSPECTIVE-COVERAGE。

- **依赖脚本**：`scripts/review-aggregator.py`、`scripts/review-eligibility-check.py`

**检查内容**：
- Multi-Perspective Review模式下，5个子代理是否全部完成审查
- 每个视角的审查结果是否有效（非空、非错误）
- 是否存在因条件限制而跳过的审查视角
- 所有审查发现的置信度评分是否达到阈值（>=80）
- Critical和High级别问题是否已全部解决或确认
- 置信度评分是否基于三维评估（上下文相关性35% + 可复现性35% + 规则匹配度30%）

**通过标准**：
- WARN：1-2个视角审查结果为空（无发现），但其他视角正常完成
- BLOCK：3个及以上视角未完成审查，或关键视角（Bug Scanner、Compliance Reviewer）未执行，或存在置信度<80的Critical/High问题
- 通过：5个视角全部完成审查，无遗漏维度，所有问题置信度>=80且无Critical/High问题未解决

**失败处理**：
1. WARN级别：标记未产出发现的视角，继续执行后续步骤
2. BLOCK级别：重新调度未完成的子代理，或降级为单代理审查模式
3. 置信度不足的问题标记为"参考"，不阻塞但需人工确认
4. Critical/High问题未解决时，阻塞合并并通知开发者
5. 记录视角覆盖情况和置信度分布到审查报告

***

### ITERATION-BUDGET: 迭代预算门禁

```yaml
名称: 迭代预算验证
阶段: 跨阶段（Phase 0-8）
检查项:
  - 迭代数 <= 最大值
  - 连续无进展 <= 3次
  - Token预算未耗尽
  - Completion promise已输出
  - 所有完成标准已满足
  - 质量门禁通过
通过条件: 迭代数<=最大值+连续无进展<=3次+Token预算未耗尽+循环完成
阻塞级别: WARN+BLOCK
自动化: 是
配置文件: .skill-config.yaml
```

> **已合并门禁**：LOOP-COMPLETION（循环完成）已合并至本门禁。别名 LOOP-COMPLETION 仍可使用，对应门禁ID为 ITERATION-BUDGET。

- **依赖脚本**：`scripts/loop-guard.py`

**检查内容**：
- 当前迭代数是否超过 max_iterations（默认50）
- 连续无进展迭代数是否超过 max_stagnation（默认3）
- Token使用率是否超过 (1 - token_budget_reserve) 阈值
- 循环输出中是否包含 completion promise 字符串（默认"DONE"）
- loop-state.md 中定义的 completion_criteria 是否全部满足
- 相关质量门禁是否全部通过（无 BLOCK 级别门禁失败）

**通过标准**：
- WARN：迭代数达到最大值的80%，或连续2次无进展
- BLOCK：迭代数超过最大值，或连续3次无进展（stagnant），或Token预算耗尽，或completion promise未输出，或完成标准未满足
- 通过：迭代数在预算内 + 无停滞 + Token充足 + 循环完成

**失败处理**：
1. WARN级别：提示迭代预算消耗情况，建议优化迭代策略
2. BLOCK级别（迭代超限）：标记循环为 failed，输出当前进度报告
3. BLOCK级别（停滞）：暂停循环，建议用户检查或使用 `/cancel-loop` 取消
4. BLOCK级别（Token耗尽）：优雅退出，保留10%预算用于收尾，输出进度快照

***

### BUILD-SUCCESS: 构建成功门禁

```yaml
名称: 构建成功验证
阶段: 跨阶段（Phase 0-8）
检查项:
  - 构建退出码=0
  - 输出目录非空
  - 构建产物完整性
  - 无构建警告（或警告已确认）
通过条件: 构建退出码=0+输出目录非空
阻塞级别: BLOCK
自动化: 是
```

***

### ROLLBACK-SAFETY: 回滚安全门禁

```yaml
名称: 回滚安全验证
阶段: 跨阶段（Phase 0-8）
检查项:
  - 目标版本通过健康检查
  - 目标版本通过安全验证
  - 回滚脚本可用且测试通过
  - 数据库迁移可逆
通过条件: 目标版本通过健康检查+安全验证
阻塞级别: BLOCK
自动化: 是
```

***

### INIT-COMPLETE: 初始化完成门禁

```yaml
名称: 初始化完成验证
阶段: 跨阶段（Phase 0-8）
检查项:
  - 所有必需目录已创建
  - 配置文件存在且格式正确
  - 依赖已安装
  - 环境变量已设置
通过条件: 所有必需目录和配置文件存在
阻塞级别: BLOCK
自动化: 是
```

***

### STATUS-HEALTHY: 状态健康门禁

```yaml
名称: 状态健康验证
阶段: 跨阶段（Phase 0-8）
检查项:
  - 所有核心服务运行正常
  - 无Critical级别门禁失败
  - 系统资源使用在阈值内
  - 无未处理的阻塞问题
通过条件: 核心服务正常+无Critical门禁失败
阻塞级别: WARN
自动化: 是
```

***

### SIMPLIFICATION-BEHAVIOR: 简化行为等价门禁

```yaml
名称: 简化行为等价验证
阶段: Phase 7
检查项:
  - 简化后行为等价（相同输入→相同输出+相同错误+相同副作用）
  - 所有测试通过
  - 公共API不变
通过条件: 行为等价+测试通过+公共API不变
阻塞级别: BLOCK
自动化: 是
```

- **依赖脚本**：`scripts/code-simplifier.py`

**检查内容**：
- 代码简化后是否保持行为等价：相同输入产生相同输出、相同错误、相同副作用
- 简化后所有测试是否通过（单元测试+集成测试）
- 公共API签名和语义是否未改变

**通过标准**：
- BLOCK：简化后行为不等价，或测试失败，或公共API发生变更
- 通过：行为等价+测试全部通过+公共API不变

**失败处理**：
1. 立即回滚简化变更到简化前状态
2. 记录失败原因到简化报告
3. 通知 Refactoring Specialist Agent 重新评估简化方案

***

### CHESTERTON-FENCE: Chesterton's Fence验证门禁

```yaml
名称: Chesterton's Fence验证
阶段: Phase 7
检查项:
  - 每处删除/修改前已理解存在原因
  - 不确定存在原因的代码已标记为保留
  - 简化决策记录完整
通过条件: 每处删除/修改前已理解存在原因（自主模式下：Refactoring Specialist Agent 自动验证）
阻塞级别: WARN
自动化: 自主模式下自动，监督模式下半自动
```

- **依赖脚本**：`scripts/code-simplifier.py`、`scripts/deduplication-detector.py`

**检查内容**：
- 每处被删除或修改的代码，是否已确认其存在原因
- 不确定存在原因的代码段是否已标记为"保留不修改"
- 简化决策是否记录到 Decision Log

**通过标准**：
- WARN：存在未确认存在原因的删除/修改操作
- 通过：每处删除/修改前已理解存在原因，不确定项已保留

**失败处理**：
1. WARN级别：标记未确认项，要求补充存在原因分析
2. 对未确认项执行回滚，恢复原始代码
3. 记录 Chesterton's Fence 违规到简化报告

***

### BRAINSTORM-COMPLETE: 需求探索完整性门禁

```yaml
名称: 需求探索完整性验证
阶段: Phase 1
检查项:
  - 设计文档已生成
  - 用户已确认设计
  - 6阶段全部完成（Discovery→Option→Design→Reflect→Commit→Transition）
  - 信息缺口已全部回答
  - 方案Trade-off分析完成
  - 设计反思遗漏已修正
通过条件: 设计文档已生成+用户确认+6阶段全部完成（自主模式下：Brainstorming Facilitator Agent 自动确认）
阻塞级别: BLOCK
自动化: 自主模式下自动（6阶段完成时），监督模式下半自动
```

**检查内容**：
- 6阶段苏格拉底式需求探索流程是否全部完成
- 结构化设计文档是否已生成（包含8个必要章节）
- 用户是否已确认设计文档
- Discovery阶段的信息缺口是否已全部回答
- Option Analysis阶段是否包含至少2个方案的Trade-off对比
- Design Reflection阶段是否发现并修正了遗漏

**通过标准**：
- BLOCK：设计文档未生成，或用户未确认，或6阶段未全部完成
- 通过：设计文档已生成+用户确认+6阶段全部完成

**失败处理**：
1. 设计文档未生成：返回Phase 3重新生成
2. 用户未确认：暂停等待用户确认
3. 阶段未完成：返回对应阶段继续执行
4. 信息缺口未回答：返回Phase 1继续提问

***

### PLAN-ATOMIC: 计划原子性门禁

```yaml
名称: 计划原子性验证
阶段: Phase 2
检查项:
  - 每个任务预估时间≤5分钟
  - 每个任务包含目标文件路径
  - 每个任务包含验证步骤
  - 任务不可再分（原子性）
通过条件: 每个任务≤5分钟+含文件路径+含验证步骤
阻塞级别: BLOCK
自动化: 是
```

**检查内容**：
- 计划文件中的每个任务是否满足原子性标准
- 每个任务的预估执行时间是否≤5分钟
- 每个任务是否包含明确的目标文件路径列表
- 每个任务是否包含可执行的验证步骤
- 任务是否不可再分（无法进一步拆分为更小的独立单元）

**通过标准**：
- BLOCK：存在任务预估时间>5分钟，或缺少文件路径，或缺少验证步骤
- 通过：每个任务≤5分钟+含文件路径+含验证步骤

**失败处理**：
1. 任务预估时间>5分钟：自动拆分为更小的原子任务
2. 缺少文件路径：标记任务为不完整，要求补充目标文件
3. 缺少验证步骤：标记任务为不完整，要求补充验证标准
4. 任务可再分：自动执行二次拆分

***

### SECURITY-FIX-CLOSED: 安全修复闭环门禁

```yaml
名称: 安全修复闭环验证
阶段: Phase 5
检查项:
  - 漏洞已验证修复（原PoC不可复现）
  - 回归测试通过（修复未引入新缺陷）
  - 复测确认无残留风险（penetration-tester / ai-penetration-tester复测通过）
  - 安全修复闭环6步流程完整执行
  - 修复代码已通过代码审查门禁(GATE-009)
  - 安全扫描门禁(GATE-012)通过
通过条件: 漏洞已验证修复 + 回归测试通过 + 复测确认无残留风险
阻塞级别: BLOCK
自动化: 是
```

**检查内容**：
- 安全漏洞是否已验证修复：原漏洞PoC不可复现
- 回归测试是否全部通过：修复未引入新的安全缺陷或功能缺陷
- 复测是否确认无残留风险：penetration-tester或ai-penetration-tester执行复测，确认漏洞已完全修复
- 安全修复闭环6步流程是否完整执行：Discovery → Verification → Fix → Regression Test → Re-test → Closure Confirmation
- 修复代码是否已通过GATE-009代码审查门禁
- 安全扫描GATE-012是否通过

**通过标准**：
- BLOCK：漏洞未修复（PoC仍可复现），或回归测试失败，或复测发现残留风险，或闭环流程不完整
- 通过：漏洞已验证修复 + 回归测试通过 + 复测确认无残留风险 + 闭环流程完整

**失败处理**：
1. 漏洞未修复：返回Fix步骤，重新实施修复
2. 回归测试失败：返回Fix步骤修复新引入的问题
3. 复测发现残留风险：返回Fix步骤补充修复
4. 闭环流程不完整：补全缺失步骤后重新验证
5. 闭环超时（>7天未关闭）：自动升级为P0，通知Orchestrator介入

***

### DESIGN-SYSTEM-COMPLETE: 设计系统完整性门禁

```yaml
名称: 设计系统完整性验证
阶段: Phase 0
检查项:
  - 设计系统文档已生成(design-system.md)
  - 风格已选择并说明理由
  - 配色方案已选择并说明理由
  - 字体配对已选择并说明理由
  - 反模式检查已执行
  - WCAG AA对比度检查已通过
  - 暗色主题方案已包含
  - 设计令牌已输出(design-tokens.json)
  - 推理链完整（每个决策有来源引用）
  - WCAG 2.1 AA标准合规检查通过
  - 色彩对比度验证通过
  - 键盘导航可用性确认
  - 屏幕阅读器兼容性确认
  - 关键页面/组件视觉回归测试执行
  - 设计稿截图与实现截图对比
  - 差异像素比例计算
通过条件: 设计系统已生成+风格+配色+字体+反模式+检查清单+可访问性+视觉回归
阻塞级别: BLOCK
自动化: 是
```

**检查内容**：
- Design System Generator Agent是否已输出完整设计系统文档
- 设计系统文档是否包含所有必要章节（产品分析/风格/配色/字体/图表/组件/响应式/暗色主题）
- 每个设计决策是否有推理来源引用（design-database.md / color-palettes.md / font-pairings.md / product-reasoning-rules.md）
- 配色方案的WCAG AA对比度是否达标（正文≥4.5:1，大文本≥3:1）
- 暗色主题方案是否已包含
- design-tokens.json是否已更新
- WCAG 2.1 AA标准合规检查是否通过
- 色彩对比度验证是否通过
- 键盘导航可用性是否确认
- 屏幕阅读器兼容性是否确认
- 关键页面/组件视觉回归测试是否执行
- 设计稿截图与实现截图是否对比
- 差异像素比例是否计算

**通过标准**：
- BLOCK：设计系统文档未生成，或缺少必要章节，或推理链不完整，或WCAG AA未达标，或可访问性检查未通过，或视觉回归超出阈值
- 通过：设计系统已生成+风格+配色+字体+反模式+检查清单+可访问性+视觉回归全部完整

**失败处理**：
1. 设计系统文档未生成：重新执行Design System Generator
2. 缺少必要章节：补充缺失章节
3. 推理链不完整：补充推理来源引用
4. WCAG AA未达标：调整配色方案直到对比度达标
5. 暗色主题缺失：补充暗色主题方案

***

### ANTI-PATTERN-CHECK: 行业反模式检查门禁

```yaml
名称: 行业反模式违规检查
阶段: Phase 0
检查项:
  - 配色方案无行业反模式违规
  - 风格选择无行业冲突
  - 圆角/阴影等细节无行业禁忌
通过条件: 无行业反模式违规
阻塞级别: BLOCK
自动化: 是
```

**检查内容**：
- 配色方案是否命中行业反模式清单（见references/color-palettes.md反模式清单）
  - Healthcare: 无霓虹色、无纯黑+红色、无高饱和荧光色
  - Fintech: 无AI紫粉渐变、无霓虹绿、无高饱和红色主色
  - Government: 无鲜艳荧光色、无渐变背景、无过大圆角(>16px)
  - Non-profit: 无纯黑+金色、无军事色彩
  - Education: 无纯黑背景、无过多荧光色
  - E-commerce: 无灰色CTA按钮、无大面积紫色
  - Legal: 无渐变/彩虹色、无圆角>12px
- 风格选择是否与产品类型冲突（如医疗产品选择Cyberpunk风格）
- 组件细节是否符合行业惯例（如政府网站圆角≤8px）

**通过标准**：
- BLOCK：存在任何行业反模式违规
- 通过：无行业反模式违规

**失败处理**：
1. 配色命中反模式：从推荐配色列表中选择替代方案
2. 风格冲突：从推荐风格列表中选择下一优先级风格
3. 组件细节违规：调整圆角/阴影等参数
4. 重新执行ANTI-PATTERN-CHECK直到通过
