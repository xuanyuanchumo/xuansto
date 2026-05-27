# 质量门禁详细定义

> 版本: 1.9.0 | 更新日期: 2026-04-29 | 编码: UTF-8 | 行尾: LF

本文档包含 Xuansto Skill 的三十七项质量门禁完整定义。

## 门禁别名映射表

SKILL.md 及需求文档中引用门禁时使用语义化别名（如 TEST-PASS、COVERAGE），本文档使用结构化 ID（如 GATE-008）。下表为两者的映射关系：

| 阶段 | 别名 (Alias) | 对应门禁ID | 说明 |
| ---- | ------------ | ---------- | ---- |
| **Phase 0** | DESIGN-REVIEW | DESIGN-REVIEW | 设计评审验证 |
| **Phase 0** | DESIGN-TOKENS | DESIGN-TOKENS | 设计令牌同步验证 |
| **Phase 0** | DESIGN-VISUAL-REGRESSION | DESIGN-VISUAL-REGRESSION | 设计阶段视觉回归验证 |
| **Phase 0** | DESIGN-ACCESSIBILITY | DESIGN-ACCESSIBILITY | 设计阶段可访问性验证 |
| **Phase 1** | REQ-COMPLETENESS | GATE-001 | 需求完整性验证 |
| **Phase 1** | SPEC-CONSISTENCY | GATE-002 | 规格一致性验证 |
| **Phase 2** | ARCH-REVIEW | GATE-003 | 架构合理性验证 |
| **Phase 2** | CONTRACT | GATE-004 | 接口契约验证 |
| **Phase 3** | COVERAGE | GATE-005 | 代码覆盖率达标 |
| **Phase 3** | TEST-DESIGN | GATE-006 | 测试数据和用例验证 |
| **Phase 4** | LINT | GATE-007 | 代码规范检查 |
| **Phase 4** | TEST-PASS | GATE-008, GATE-010 | 单元测试和集成测试通过 |
| **Phase 4** | CODE-REVIEW | GATE-009 | 代码审查验证 |
| **Phase 4** | FILE-ENCODING | FILE-ENCODING | 文件编码格式验证 |
| **Phase 4** | COMMENT-LANGUAGE | COMMENT-LANGUAGE | 注释语言规范验证 |
| **Phase 4** | SCRIPT-SECURITY | SCRIPT-SECURITY | 脚本安全约束合规 |
| **Phase 4/7** | SCRIPT-CLEANUP | SCRIPT-CLEANUP | 临时脚本清理验证 |
| **跨阶段** | TOKEN-BUDGET | TOKEN-BUDGET | Token预算控制 |
| **Phase 5** | E2E-TEST | GATE-011 | 端到端测试验证 |
| **Phase 5** | SECURITY | GATE-012, AGENTIC-SECURITY | 安全扫描和Agentic安全合规 |
| **Phase 5** | SPEC-DRIFT | SPEC-CONSISTENCY | 规格与实现一致性验证 |
| **Phase 5** | AGENTIC-SEC | AGENTIC-SECURITY | Agentic安全合规验证 |
| **Phase 5** | AI-PENTEST | AI-PENTEST | AI渗透测试验证 |
| **Phase 5** | VISUAL-REG | VISUAL-REGRESSION | 视觉回归测试验证 |
| **Phase 5** | A11Y | ACCESSIBILITY | 可访问性验证 |
| **Phase 5** | PERFORMANCE | PERFORMANCE | 性能基准验证（独立门禁，见Phase 5定义） |
| **Phase 6** | DEPLOY-READY | GATE-013 | 部署就绪验证 |
| **Phase 6** | PROD-VERIFY | GATE-014 | 生产环境验证 |
| **Phase 6** | INFRA-HEALTH | INFRA-HEALTH | 基础设施健康验证 |
| **Phase 6** | UAT | GATE-013, UX-ACCEPTANCE | 用户验收测试和体验验收 |
| **Phase 6** | UX-ACCEPTANCE | UX-ACCEPTANCE | 用户体验验收验证 |
| **Phase 7** | ITERATION-CLOSE | GATE-015 | 迭代闭环验证 |
| **Phase 7** | DOCUMENTATION | DOC-COMPLETENESS | 文档完整性检查 |
| **Phase 8** | DESKTOP-BUILD | DESKTOP-BUILD | 桌面构建验证 |
| **Phase 8** | DESKTOP-SIGN | DESKTOP-SIGN | 代码签名验证 |
| **Phase 8** | DESKTOP-UPDATE | DESKTOP-UPDATE | 自动更新验证 |
| **Phase 8** | DESKTOP-CROSS | DESKTOP-CROSS | 跨平台兼容性验证 |
| **Phase 8** | IPC-CONTRACT | IPC-CONTRACT | IPC契约验证 |

## 目录

- [Phase 0: 设计阶段](#phase-0-设计阶段)
  - [DESIGN-REVIEW: 设计评审门禁](#design-review-设计评审门禁)
  - [DESIGN-TOKENS: Design Tokens完整性验证门禁](#design-tokens-design-tokens完整性验证门禁)
  - [DESIGN-VISUAL-REGRESSION: 视觉回归测试门禁](#design-visual-regression-视觉回归测试门禁)
  - [DESIGN-ACCESSIBILITY: 可访问性检查门禁](#design-accessibility-可访问性检查门禁)
- [Phase 1: 需求阶段](#phase-1-需求阶段)
  - [GATE-001: 需求完整性门禁](#gate-001-需求完整性门禁)
  - [GATE-002: 规格一致性门禁](#gate-002-规格一致性门禁)
- [Phase 2: 架构阶段](#phase-2-架构阶段)
  - [GATE-003: 架构合理性门禁](#gate-003-架构合理性门禁)
  - [GATE-004: 接口契约门禁](#gate-004-接口契约门禁)
- [Phase 3: 测试设计阶段](#phase-3-测试设计阶段)
  - [GATE-005: 测试覆盖门禁](#gate-005-测试覆盖门禁)
  - [GATE-006: 测试数据门禁](#gate-006-测试数据门禁)
- [Phase 4: 代码实现阶段](#phase-4-代码实现阶段)
  - [GATE-007: 代码质量门禁](#gate-007-代码质量门禁)
  - [TEST-PASS: 单元测试与集成测试门禁](#test-pass-单元测试与集成测试门禁)
  - [GATE-009: 代码审查门禁](#gate-009-代码审查门禁)
  - [FILE-ENCODING: 文件编码格式门禁](#file-encoding-文件编码格式门禁)
  - [COMMENT-LANGUAGE: 注释语言规范门禁](#comment-language-注释语言规范门禁)
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
  - [ACCESSIBILITY: 可访问性门禁](#accessibility-可访问性门禁)
  - [PERFORMANCE: 性能基准门禁](#performance-性能基准门禁)
- [Phase 6: 验收阶段](#phase-6-验收阶段)
  - [GATE-013: 部署就绪门禁](#gate-013-部署就绪门禁)
  - [GATE-014: 生产验证门禁](#gate-014-生产验证门禁)
  - [INFRA-HEALTH: 非功能基础设施健康门禁](#infra-health-非功能基础设施健康门禁)
  - [UX-ACCEPTANCE: 用户体验验收门禁](#ux-acceptance-用户体验验收门禁)
- [Phase 7: 迭代阶段](#phase-7-迭代阶段)
  - [GATE-015: 演化闭环门禁](#gate-015-演化闭环门禁)
  - [DOC-COMPLETENESS: 文档完整性门禁](#doc-completeness-文档完整性门禁)
- [Phase 8: 桌面端阶段](#phase-8-桌面端阶段)
  - [DESKTOP-BUILD: 桌面端构建门禁](#desktop-build-桌面端构建门禁)
  - [DESKTOP-SIGN: 代码签名门禁](#desktop-sign-代码签名门禁)
  - [DESKTOP-UPDATE: 自动更新门禁](#desktop-update-自动更新门禁)
  - [DESKTOP-CROSS: 跨平台一致性门禁](#desktop-cross-跨平台一致性门禁)
  - [IPC-CONTRACT: IPC契约门禁](#ipc-contract-ipc契约门禁)
- [门禁快速参考表](#门禁快速参考表)

***

## Phase 0: 设计阶段

### DESIGN-REVIEW: 设计评审门禁

```yaml
名称: 设计评审通过
阶段: Phase 0
检查项:
  - UI/UX设计稿完成
  - 设计评审会议通过
  - 设计与需求对齐
  - 技术可行性确认
  - 无障碍设计审查通过
通过条件: 设计稿评审通过
阻塞级别: BLOCK
自动化: 否（需人工评审）
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

### DESIGN-VISUAL-REGRESSION: 视觉回归测试门禁

```yaml
名称: 视觉回归测试验证
阶段: Phase 0
检查项:
  - 关键页面/组件视觉回归测试执行
  - 设计稿截图与实现截图对比
  - 差异像素比例计算
通过条件: 差异像素 < 0.1% 或 所有差异需人工确认无影响
阻塞级别: WARN/BLOCK
自动化: 是
```

***

### DESIGN-ACCESSIBILITY: 可访问性检查门禁

```yaml
名称: 可访问性检查验证
阶段: Phase 0
检查项:
  - WCAG 2.1 AA标准合规检查
  - 色彩对比度验证
  - 键盘导航可用性
  - 屏幕阅读器兼容性
通过条件: 无A级违规，AA级违规数≤0
阻塞级别: BLOCK
自动化: 是
```

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
通过条件: 完整性评分 >= 90分
阻塞级别: BLOCK
自动化: 半自动
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
通过条件: 架构评审通过
阻塞级别: BLOCK
自动化: 否（需人工评审）
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

## Phase 3: 测试设计阶段

### GATE-005: 测试覆盖门禁

```yaml
名称: 测试用例覆盖率验证
阶段: Phase 3
检查项:
  - 单元测试覆盖
  - 集成测试覆盖
  - 边界条件测试
  - 异常路径测试
通过条件: 覆盖率 >= 80%
阻塞级别: BLOCK
自动化: 是
```

- **依赖脚本**：`scripts/coverage-check.py`

***

### GATE-006: 测试数据门禁

```yaml
名称: 测试数据准备验证
阶段: Phase 3
检查项:
  - 测试数据完整性
  - 数据隔离性
  - 敏感数据脱敏
  - 数据生成脚本
通过条件: 数据准备完成
阻塞级别: BLOCK
自动化: 是
```

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
通过条件: 无严重问题，警告 < 5
阻塞级别: BLOCK
自动化: 是
```

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
通过条件: 审查通过且无阻塞意见
阻塞级别: BLOCK
自动化: 否（需人工审查）
```

***

### FILE-ENCODING: 文件编码格式门禁

```yaml
名称: 文件编码格式验证
阶段: Phase 4
检查项:
  - 所有源代码文件为UTF-8 without BOM
  - 配置文件编码正确
  - 资源文件编码正确
  - 无混合编码文件
通过条件: 所有文件为UTF-8 without BOM
阻塞级别: BLOCK
自动化: 是
```

- **依赖脚本**：`scripts/check-encoding.py`

***

### COMMENT-LANGUAGE: 注释语言规范门禁

```yaml
名称: 注释语言规范验证
阶段: Phase 4
检查项:
  - 业务注释包含中文说明
  - 技术注释语言一致性
  - 公共API注释完整性
  - 注释与代码同步
通过条件: 业务注释包含中文说明
阻塞级别: WARN/BLOCK
自动化: 是
```

- **依赖脚本**：`scripts/check-comment-lang.py`

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
通过条件: E2E测试100%通过
阻塞级别: BLOCK
自动化: 是
```

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
通过条件: 通过OWASP Agentic Top 10检查
阻塞级别: BLOCK
自动化: 是
```

- **依赖脚本**：`scripts/agentic-security-scanner.py`

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
通过条件: 差异像素<0.1%
阻塞级别: WARN/BLOCK
自动化: 是
```

- **依赖脚本**：`scripts/visual-regression.js`

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
通过条件: 生产验证通过
阻塞级别: BLOCK
自动化: 是
```

***

### INFRA-HEALTH: 非功能基础设施健康门禁

```yaml
名称: 非功能基础设施健康验证
阶段: Phase 6
检查项:
  - 健康检查端点可访问且返回200
  - 指标端点可访问且返回200
  - 日志包含必要trace字段
  - 基础设施监控告警配置
通过条件: 健康检查端点/指标端点可访问且返回200；日志含必要trace字段
阻塞级别: BLOCK
自动化: 是
```

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
通过条件: 任务完成率≥95%，SUS分数≥70
阻塞级别: BLOCK
自动化: 半自动
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

| 门禁ID              | 名称                 | 阶段        | 阻塞级别       | 自动化 |
| ----------------- | ------------------ | --------- | ---------- | --- |
| DESIGN-REVIEW     | 设计评审通过             | Phase 0   | BLOCK      | 否   |
| DESIGN-TOKENS     | Design Tokens完整性验证 | Phase 0   | BLOCK      | 是   |
| DESIGN-VISUAL-REGRESSION | 视觉回归测试验证   | Phase 0   | WARN/BLOCK | 是   |
| DESIGN-ACCESSIBILITY | 可访问性检查验证    | Phase 0   | BLOCK      | 是   |
| GATE-001          | 需求规格完整性验证          | Phase 1   | BLOCK      | 半自动 |
| GATE-002          | 规格文档一致性验证          | Phase 1   | BLOCK      | 是   |
| SPEC-CONSISTENCY  | 规格与实现一致性验证         | Phase 5   | BLOCK      | 是   |
| GATE-003          | 架构设计合理性验证          | Phase 2   | BLOCK      | 否   |
| GATE-004          | 接口契约完整性验证          | Phase 2   | BLOCK      | 是   |
| GATE-005          | 测试用例覆盖率验证          | Phase 3   | BLOCK      | 是   |
| GATE-006          | 测试数据准备验证           | Phase 3   | BLOCK      | 是   |
| GATE-007          | 代码静态质量验证           | Phase 4   | BLOCK      | 是   |
| TEST-PASS         | 单元测试与集成测试执行验证      | Phase 4/5  | BLOCK      | 是   |
| GATE-009          | 代码审查完成验证           | Phase 4   | BLOCK      | 否   |
| FILE-ENCODING     | 文件编码格式验证           | Phase 4   | BLOCK      | 是   |
| COMMENT-LANGUAGE  | 注释语言规范验证           | Phase 4   | WARN/BLOCK | 是   |
| SCRIPT-SECURITY  | 脚本安全约束合规验证        | Phase 4   | WARN/BLOCK | 是   |
| SCRIPT-CLEANUP   | 临时脚本清理验证           | Phase 4/7 | BLOCK      | 是   |
| TOKEN-BUDGET     | Token预算控制验证          | 跨阶段     | WARN/BLOCK | 是   |
| GATE-011          | 端到端测试验证            | Phase 5   | BLOCK      | 是   |
| GATE-012          | 安全合规验证             | Phase 5   | BLOCK      | 是   |
| AGENTIC-SECURITY  | Agentic安全合规验证      | Phase 5   | BLOCK      | 是   |
| AI-PENTEST        | AI渗透测试验证           | Phase 5   | BLOCK      | 是   |
| VISUAL-REGRESSION | 视觉回归测试验证           | Phase 5   | WARN/BLOCK | 是   |
| ACCESSIBILITY     | 可访问性验证             | Phase 5   | BLOCK      | 是   |
| PERFORMANCE       | 性能基准验证             | Phase 5   | WARN       | 是   |
| GATE-013          | 部署准备验证             | Phase 6   | BLOCK      | 是   |
| GATE-014          | 生产环境验证             | Phase 6   | BLOCK      | 是   |
| INFRA-HEALTH      | 非功能基础设施健康验证        | Phase 6   | BLOCK      | 是   |
| UX-ACCEPTANCE     | 用户体验验收验证           | Phase 6   | BLOCK      | 半自动 |
| GATE-015          | 持续演化验证             | Phase 7   | WARN       | 是   |
| DOC-COMPLETENESS  | 文档完整性验证            | Phase 7   | BLOCK      | 是   |
| DESKTOP-BUILD     | 桌面端安装包构建验证         | Phase 8   | BLOCK      | 是   |
| DESKTOP-SIGN      | 代码签名与公证验证          | Phase 8   | BLOCK      | 是   |
| DESKTOP-UPDATE    | 自动更新端到端验证          | Phase 8   | BLOCK      | 是   |
| DESKTOP-CROSS     | 三平台功能一致性验证         | Phase 8   | WARN/BLOCK | 是   |
| IPC-CONTRACT      | IPC通道契约验证          | Phase 8   | BLOCK      | 是   |


***

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
