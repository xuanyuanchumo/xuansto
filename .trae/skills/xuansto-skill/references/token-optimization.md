# Token消耗优化体系

> 版本: 1.9.0 | 更新日期: 2026-05-01 | 编码: UTF-8 | 行尾: LF

## 目录

- [8.1 SKILL.md精简加载策略](#81-skillmd精简加载策略)
- [8.2 按需加载策略](#82-按需加载策略)
- [8.3 Token预算门禁](#83-token预算门禁)
- [8.4 上下文压缩增强](#84-上下文压缩增强)
- [8.5 Token消耗监控与优化指标](#85-token消耗监控与优化指标)

***

## 8.1 SKILL.md精简加载策略

### 三层精简结构

SKILL.md采用三层渐进式加载，根据平台上下文窗口大小自动选择精简级别：

| 精简级别 | 适用场景 | SKILL.md内容 | 预估Token |
|----------|----------|-------------|-----------|
| full | 200K+上下文 | 完整SKILL.md | ~3000 |
| compact | 128K上下文 | 核心规则+索引表 | ~1500 |
| ultra_compact | 64K及以下 | 仅核心规则摘要 | ~800 |

### 精简效果对比

| 指标 | full | compact | ultra_compact |
|------|------|---------|---------------|
| 行数 | ~150 | ~80 | ~40 |
| Token消耗 | ~3000 | ~1500 | ~800 |
| 包含引用索引 | 是 | 是 | 否 |
| 包含命令一览 | 是 | 精简 | 否 |
| 包含版本历史 | 是 | 否 | 否 |

### 精简规则

1. **full级别**：保留SKILL.md全部内容
2. **compact级别**：移除版本历史、多语言规范详细表格，保留核心规则摘要和引用索引表
3. **ultra_compact级别**：仅保留Karpathy准则、STC规则、九阶段工作流摘要、Agent角色概要

***

## 8.2 按需加载策略

### Phase-Agent-Reference映射矩阵

每个Phase只加载该阶段所需的参考文件，避免全量加载：

| Phase | 活跃Agent | 需加载参考文件 |
|-------|-----------|---------------|
| Phase 0 | UX/UI Designer, UI Stylist | design-guidelines.md, design-system-template.md |
| Phase 1 | Product Manager | coding-standards.md, acceptance-criteria.md |
| Phase 2 | System Architect | coding-standards.md, database-guidelines.md, a2a-protocol.md |
| Phase 3 | Test Architect | test-guidelines.md, coding-standards.md |
| Phase 4 | FE/BE/Desktop Dev, Code Reviewer | coding-standards.md, script-standards.md, python-standards.md等 |
| Phase 5 | QA Engineer, Security Auditor, Perf Tester | test-guidelines.md, security-guidelines.md, owasp-top10-2026.md |
| Phase 6 | Product Manager | acceptance-criteria.md, documentation-standards.md |
| Phase 7 | Orchestrator, Refactoring Agent | coding-standards.md, knowledge-base-architecture.md |
| Phase 8 | Build & Release Engineer | desktop-dev-guidelines.md, tauri-dev-guidelines.md, ipc-contracts.md |

### 卸载策略

当Phase切换时，自动卸载上一Phase的参考文件：

1. Phase开始：加载当前Phase所需参考文件
2. Phase执行：仅保留当前Phase参考文件在上下文中
3. Phase结束：卸载当前Phase参考文件，保留核心决策摘要
4. 跨Phase共享文件（如coding-standards.md）常驻上下文

***

## 8.3 Token预算门禁

### 预算配置

| 配置项 | 默认值 | 说明 |
|--------|--------|------|
| budget | 100000 | 默认Token预算上限 |
| warn_threshold | 0.8 | 警告阈值（80%） |
| block_threshold | 1.0 | 阻断阈值（100%） |
| compression_level | semantic | 默认压缩级别 |

### 门禁触发机制

```
Token使用率 < 80%  → 正常运行，无特殊动作
Token使用率 ≥ 80%  → WARN：自动触发上下文压缩（Level 2语义压缩），暂停低优先级Agent
Token使用率 ≥ 100% → BLOCK：强制降级为串行模式，拒绝新Agent激活
Token使用率降至70%以下 → 自动恢复并行模式
```

### 降级模式

| 降级级别 | 触发条件 | 行为 |
|----------|----------|------|
| Level 0 | < 80% | 正常并行执行 |
| Level 1 | 80%-99% | 压缩上下文，暂停非关键Agent |
| Level 2 | ≥ 100% | 串行模式，最高级压缩 |
| 恢复 | < 70% | 恢复并行，停止压缩 |

### 消耗日志

Token消耗日志存储在 `.knowledge/token-usage/` 目录下，包含：
- 任务级Token消耗统计
- Phase级Token消耗分布
- Agent级Token消耗排名
- 压缩效果记录

***

## 8.4 上下文压缩增强

### 三级压缩策略

| 级别 | 名称 | 压缩率 | 精度损失 | 触发条件 |
|------|------|--------|----------|----------|
| Level 1 | Lossless | 10%-20% | 0% | Token使用率 > 60% |
| Level 2 | Semantic | 30%-50% | < 2% | Token使用率 > 80% |
| Level 3 | Selective | 50%-70% | < 5% | Token使用率 > 95% |

### Level 1: Lossless（无损压缩）

- 移除多余空白行和注释
- 合并重复引用
- 压缩JSON/YAML为单行
- 移除残留的引用加载标记

### Level 2: Semantic（语义压缩）

- 长文本摘要化（保留核心语义）
- 知识条目精简（保留Top-K条目）
- 知识蒸馏压缩（CangjieSkills方法论：将冗长的经验知识蒸馏为精炼的通用模式，去除项目特定细节，保留可复用的核心语义）
- 消息压缩（合并连续短消息）
- 代码片段保留签名和接口，移除实现细节

### Level 3: Selective（选择性压缩）

- 丢弃低相关性历史消息
- 仅保留核心上下文（当前Phase + 关键决策）
- 知识条目仅保留Top-3
- 参考文件仅保留当前Phase所需

### 精度保证

- 压缩后自动比对核心决策点完整性
- 关键事实损失 > 2% 自动回退到上一级压缩
- 压缩操作记录至日志，支持审计

***

## 8.5 Token消耗监控与优化指标

### 监控指标体系

| 指标 | 计算方式 | 优化目标 |
|------|----------|----------|
| TES (Token Efficiency Score) | 有效输出Token / 总消耗Token | ≥ 0.4 |
| 平均单Phase消耗 | 单Phase总Token / Phase数 | < 15000 |
| 压缩触发率 | 压缩触发次数 / 总Phase数 | < 30% |
| 预算超支率 | 超预算次数 / 总任务数 | < 5% |
| 参考文件命中率 | 实际使用参考 / 加载参考 | ≥ 0.7 |

### 优化目标

| 场景 | 目标Token消耗 | 优化策略 |
|------|-------------|----------|
| 小型任务（< 10文件） | < 30K | ultra_compact + 精简Agent |
| 中型任务（10-50文件） | 30K-80K | compact + 按需加载 |
| 大型任务（> 50文件） | 80K-150K | full + 完整工作流 |

### TES评分等级

| TES范围 | 等级 | 说明 |
|---------|------|------|
| ≥ 0.5 | A | 优秀，Token利用率高 |
| 0.4-0.5 | B | 良好，符合预期 |
| 0.3-0.4 | C | 一般，有优化空间 |
| < 0.3 | D | 较差，需立即优化 |

### Dashboard

Token消耗监控Dashboard提供以下视图：
- 实时Token消耗曲线
- Phase级消耗分布饼图
- Agent级消耗排名柱状图
- 压缩效果趋势图
- TES评分趋势图

## Token效率评分（TES）

### 计算公式

```
TES = 任务产出价值 / 平均Token使用量
```

### 5维评分标准

| 维度 | 权重 | 评分标准 |
|------|------|----------|
| 功能完整性 | 30% | 需求覆盖率、功能点完成率 |
| 测试通过率 | 25% | 单元测试通过率、集成测试通过率 |
| 代码质量 | 20% | Lint通过率、复杂度评分、Code Review通过率 |
| 安全合规 | 15% | 安全门禁通过率、漏洞修复率 |
| 文档完整性 | 10% | API文档覆盖率、README完整性 |

### TES评分等级

| 等级 | TES范围 | 说明 |
|------|---------|------|
| A | ≥0.8 | 高效产出，Token利用率优秀 |
| B | 0.6-0.8 | 良好，有优化空间 |
| C | 0.4-0.6 | 一般，需关注Token浪费 |
| D | <0.4 | 低效，需重新评估任务分解策略 |

## 并发任务Token预算分配

### 4种分配策略

详见 [concurrency-standards.md](concurrency-standards.md) 的完整定义。

| 策略 | 公式 | 适用场景 |
|------|------|----------|
| 均分 | budget_per_agent = total / count | Agent优先级相同 |
| 优先级加权 | budget_i = total × (priority_i / Σpriority) | 任务优先级明确 |
| 主从 | 主70% + 从30%均分 | 存在编排Agent |
| 动态调整 | 基于实时消耗率每5分钟调整 | 任务复杂度不确定 |
