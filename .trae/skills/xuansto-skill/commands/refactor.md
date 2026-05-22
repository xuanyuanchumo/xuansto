---
name: /refactor
aliases:
  - rf
category: quality
phase: "7"
description: 代码重构与技术债务清理
trigger: 需要重构代码或清理技术债务时
workflow: sdd-tdd-medium
---

# /refactor 命令

## 命令描述

`/refactor` 命令用于代码重构与结构优化，是技术债务治理的核心命令。该命令遵循 TDD 安全网原则（测试必须在重构前后均通过），并以 Karpathy 准则为指导：Simplicity First（简化优先，不增加复杂性）和 Surgical Changes（仅修改必要部分），确保重构安全可控。

---

## 触发条件

| 触发方式 | 说明 |
|----------|------|
| 命令输入 | 用户输入 `/refactor` |
| 关键词触发 | 用户提及"代码重构"、"结构优化"、"技术债务" |
| 自动触发 | `/review` 审查发现高复杂度或重复代码时自动建议 |
| 条件触发 | 代码复杂度超过阈值（圈复杂度>15）时自动建议 |

---

## 命令名称与语法

```
/refactor [target] [options]
```

---

## 参数定义

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| target | string | 否 | 当前工作目录 | 重构目标路径或文件 |
| --type | string | 否 | all | 重构类型：all(全部)、extract(提取)、simplify(简化)、restructure(重组)、rename(重命名) |
| --scope | string | 否 | module | 重构范围：recent(最近修改)、file(文件)、dir(目录)、module(模块) |
| --safety | string | 否 | strict | 安全级别：strict(严格)、moderate(适中)、loose(宽松) |
| --simplify | boolean | 否 | false | 启用Code Simplifier的三方面审查流程（行为等价+可读性+一致性） |
| --aggressive | boolean | 否 | false | 启用更激进的简化（含类型收窄、命名改进） |
| --dry-run | boolean | 否 | false | 模拟运行，只显示重构计划 |
| --auto | boolean | 否 | false | 全自动重构模式，无需确认 |
| --verify | boolean | 否 | true | 重构后自动验证测试通过 |
| --backup | boolean | 否 | true | 重构前自动备份 |
| --max-changes | number | 否 | 20 | 单次最大变更文件数 |
| --exclude | string[] | 否 | [] | 排除的文件或目录模式 |

---

## 执行流程

> 标准四步框架：1. 输入验证 → 2. Agent调度 → 3. 任务执行 → 4. 结果验证

```
┌─────────────────────────────────────────────────────────────┐
│                    /refactor 执行流程                        │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  1. 代码分析阶段                                             │
│     ├── 解析命令参数和重构目标                                │
│     ├── 代码复杂度评估                                       │
│     ├── 依赖关系图构建                                       │
│     ├── 代码异味检测                                         │
│     └── 生成代码结构概览                                      │
│                                                             │
│  2. 识别重构目标                                             │
│     ├── 标记高复杂度函数                                      │
│     ├── 检测重复代码段                                        │
│     ├── 识别过长函数和类                                      │
│     ├── 发现耦合过紧的模块                                    │
│     └── 标记违反设计原则的代码                                │
│                                                             │
│  3. 确保测试覆盖                                             │
│     ├── 运行现有测试套件（基线）                              │
│     ├── 评估目标代码测试覆盖率                                │
│     ├── 为覆盖不足的代码补充测试                              │
│     ├── 确认所有基线测试通过                                  │
│     └── 记录基线测试结果                                      │
│                                                             │
│  4. 执行重构阶段                                             │
│     ├── 创建备份点                                           │
│     ├── Simplicity First：简化逻辑，消除不必要抽象            │
│     ├── Surgical Changes：仅修改必要部分                      │
│     ├── 逐步应用重构变更                                      │
│     ├── 每步变更后运行测试验证                                │
│     └── 记录变更日志到 Decision Log                          │
│                                                             │
│  5. 验证测试通过                                             │
│     ├── 运行完整测试套件                                      │
│     ├── 对比基线测试结果                                      │
│     ├── 确认无回归问题                                        │
│     ├── 性能基准对比（如适用）                                │
│     └── 如测试失败则回滚变更                                  │
│                                                             │
│  6. 更新文档阶段                                             │
│     ├── 更新 API 文档                                        │
│     ├── 更新架构说明                                         │
│     ├── 更新变更日志                                         │
│     └── 标注重构影响范围                                      │
│                                                             │
│  7. 完成阶段                                                 │
│     ├── 生成重构报告                                         │
│     ├── 更新质量门禁状态                                      │
│     ├── 提交变更（如配置）                                    │
│     └── 触发后续流程（如需要）                                │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 涉及Agent

| Agent | 角色 | 职责 |
|-------|------|------|
| refactoring-specialist | 主导 | 协调重构流程、代码重构 |
| unit-tester | 辅助 | 测试覆盖保障与验证 |
| code-reviewer | 辅助 | 重构质量审查 |
| system-architect | 辅助 | 架构合规性验证 |
| backend-developer | 辅助 | 后端代码重构实现 |
| frontend-developer | 辅助 | 前端代码重构实现 |

---

## 输出格式

### 1. 重构报告 (refactor-report.md)

```markdown
# 代码重构报告

## 重构概要
- 重构时间: 2026-04-28 14:00:00
- 重构目标: src/services/
- 重构类型: extract + simplify
- 安全级别: strict

## 重构统计
| 指标 | 重构前 | 重构后 | 变化 |
|------|--------|--------|------|
| 圈复杂度均值 | 18 | 8 | -55.6% |
| 重复代码率 | 12.5% | 3.2% | -74.4% |
| 函数平均行数 | 65 | 22 | -66.2% |
| 测试覆盖率 | 72% | 89% | +23.6% |

## 重构详情

### R-001: 提取 UserService.validateCredentials
- 类型: extract
- 文件: src/services/user-service.ts
- 变更: 将验证逻辑提取为独立方法
- Simplicity First: 消除嵌套条件，使用早返回模式
- Surgical Changes: 仅修改 validateCredentials 方法

### R-002: 简化 OrderProcessor.processOrder
- 类型: simplify
- 文件: src/services/order-processor.ts
- 变更: 消除策略模式过度抽象，还原为简单条件分支
- Simplicity First: 移除不必要的抽象层
- Surgical Changes: 仅修改 processOrder 及相关调用

## 测试验证
- 基线测试: 128 passed / 0 failed
- 重构后测试: 128 passed / 0 failed
- 新增测试: 15
- 回归问题: 0
```

### 2. 变更记录 (changes.json)

```json
{
  "refactor_id": "REF-20260428-001",
  "timestamp": "2026-04-28T14:30:00Z",
  "changes": [
    {
      "id": "R-001",
      "file": "src/services/user-service.ts",
      "change_type": "extract",
      "lines_added": 28,
      "lines_removed": 15,
      "complexity_before": 18,
      "complexity_after": 6,
      "backup_path": ".backup/user-service.ts.20260428-140000"
    }
  ],
  "total_files": 4,
  "total_lines_added": 56,
  "total_lines_removed": 42,
  "baseline_tests_passed": 128,
  "post_refactor_tests_passed": 128,
  "new_tests_added": 15
}
```

### 3. 测试验证结果 (verification.json)

```json
{
  "verification_time": "2026-04-28T14:45:00Z",
  "baseline": {
    "tests_run": 128,
    "tests_passed": 128,
    "tests_failed": 0
  },
  "post_refactor": {
    "tests_run": 143,
    "tests_passed": 143,
    "tests_failed": 0
  },
  "regression_detected": false,
  "coverage_before": 72.0,
  "coverage_after": 89.0,
  "performance_delta": "+0.3%"
}
```

---

## 示例用法

### 示例1: 基础重构

```bash
/refactor src/services/user-service.ts
```

对指定文件执行重构分析并实施重构。

### 示例2: 仅提取重构

```bash
/refactor src/services/ --type=extract --safety=strict
```

对 `src/services/` 目录执行提取类重构，严格安全级别。

### 示例3: 模拟重构

```bash
/refactor --dry-run
```

显示重构计划但不实际执行。

### 示例4: 简化重构

```bash
/refactor src/core/ --type=simplify --auto
```

对 `src/core/` 目录执行简化重构，全自动模式。

### 示例5: 全项目重构

```bash
/refactor --scope=project --max-changes=50 --verify
```

全项目范围重构，单次最多变更50个文件，重构后自动验证。

---

## Karpathy 准则

### Simplicity First（简化优先）

```
核心原则:
  - 简化逻辑，不增加复杂性
  - 消除不必要的抽象层
  - 优先选择简单直接的实现
  - 避免过度工程化

实践要点:
  - 用早返回替代深层嵌套
  - 用简单条件替代策略模式（当策略数量少时）
  - 用直接调用替代不必要的间接层
  - 删除未使用的代码和抽象
```

### Surgical Changes（精准修改）

```
核心原则:
  - 仅修改必要的部分
  - 最小化变更范围
  - 保持周围代码不变
  - 每次只做一类重构

实践要点:
  - 一次重构只关注一个目标
  - 不在重构中混入功能变更
  - 保持函数签名兼容
  - 逐步验证，频繁运行测试
```

---

## 质量门禁

| 门禁标识 | 阻塞级别(BLOCK/WARN) | 通过标准 |
|----------|----------------------|----------|
| TEST-PASS | BLOCK | 基线测试全部通过、无回归问题、测试覆盖率不降低 |
| GATE-007 | BLOCK | 代码复杂度降低、重复代码减少、代码规范合规 |
| SPEC-CONSISTENCY | WARN | 重构后代码与规格文档一致、API契约未破坏 |
| SIMPLIFICATION-BEHAVIOR | BLOCK | 简化后行为等价+测试通过+公共API不变（启用--simplify时） |
| CHESTERTON-FENCE | WARN | 每处删除/修改前已理解存在原因（启用--simplify时） |
---

## 注意事项

1. **TDD 安全网**: 重构前必须确保测试通过，重构后必须验证测试仍然通过
2. **逐步验证**: 每次重构变更后立即运行测试，避免大规模变更后难以定位问题
3. **回滚机制**: 测试失败时自动回滚到备份点
4. **单一职责**: 每次重构只做一类变更，不在重构中混入功能修改
5. **文档同步**: 重构后必须同步更新相关文档

---

## 相关脚本

- `scripts/code-simplifier.py` - 代码简化器，检测死代码、深层嵌套、复杂条件等简化机会
- `scripts/deduplication-detector.py` - 重复检测器，识别相同代码块、相似函数和重复字符串常量

---

## 相关工作流

- `workflows/sdd-tdd-full.md` (Phase 7) - SDD+TDD全生命周期工作流的重构与简化阶段

---

## 相关命令

- `/review` - 执行代码审查发现重构目标
- `/fix` - 修复重构中发现的问题
- `/test` - 运行测试验证重构结果
