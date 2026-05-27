---
name: /simplify
aliases:
  - simp
category: quality
phase: "7"
description: 代码简化审查与执行
trigger: 需要简化代码或消除不必要复杂性时
workflow: sdd-tdd-fast
---

# /simplify 命令

## 命令描述

`/simplify` 命令用于代码简化审查与执行，遵循 Chesterton's Fence 原则（理解先于修改），通过五步简化审查流程系统性地识别和消除代码中的不必要复杂性。该命令确保简化后行为等价、可读性提升、风格一致。

---

## 触发条件

| 触发方式 | 说明 |
|----------|------|
| 命令输入 | 用户输入 `/simplify` |
| 关键词触发 | 用户提及"代码简化"、"消除复杂性"、"简化代码" |
| 自动触发 | `/refactor --simplify` 启用简化审查时自动调用 |
| 条件触发 | Code Simplifier 检测到简化机会（死代码、深层嵌套、复杂条件等）时建议 |

---

## 命令名称与语法

```
/simplify [scope]
```

---

## 参数定义

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| scope | string | 否 | recent | 简化范围：file(当前文件)、dir(当前目录)、recent(最近修改文件) |
| `--dry-run` | boolean | 否 | false | 模拟简化，不实际修改代码 |
| `--auto` | boolean | 否 | false | 自动执行简化，无需确认 |
| `--verify` | boolean | 否 | true | 简化后运行测试验证行为等价 |
| `--exclude` | string | 否 | - | 逗号分隔的文件/目录模式，排除不简化 |

---

## 执行流程

> 五步简化审查框架：1. 理解先于修改 → 2. 识别简化机会 → 3. 三方面验证 → 4. 执行简化 → 5. 验证结果

```
┌─────────────────────────────────────────────────────────────┐
│                    /simplify 执行流程                        │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Step 1: 理解先于修改（Chesterton's Fence）                  │
│     ├── 阅读目标代码的完整上下文                              │
│     ├── 理解每段代码的存在原因                                │
│     ├── 查阅 git blame / 注释 / 文档 了解历史                │
│     ├── 标记"不确定存在原因"的代码段                          │
│     └── 不确定则不修改（Chesterton's Fence 原则）             │
│                                                             │
│  Step 2: 识别简化机会                                        │
│     ├── 运行 scripts/code-simplifier.py 检测                 │
│     │   ├── 死代码（未使用的导入、变量、函数）                │
│     │   ├── 深层嵌套（>3层if/else）                          │
│     │   ├── 复杂条件（密集三元链、复杂布尔表达式）            │
│     │   ├── 长函数（>50行）                                  │
│     │   └── 重复字符串常量                                   │
│     ├── 运行 scripts/deduplication-detector.py 检测          │
│     │   ├── 相同代码块（3+次相同模式）                       │
│     │   ├── 相似函数（参数和逻辑相似）                        │
│     │   └── 重复字符串常量                                   │
│     └── 汇总简化机会清单，按优先级排序                        │
│                                                             │
│  Step 3: 三方面验证                                          │
│     ├── 行为等价验证                                         │
│     │   ├── 相同输入 → 相同输出                              │
│     │   ├── 相同输入 → 相同错误                              │
│     │   └── 相同输入 → 相同副作用                            │
│     ├── 可读性验证                                           │
│     │   └── 新团队成员理解简化后代码是否更快？                │
│     └── 一致性验证                                           │
│         └── 简化后代码是否符合项目惯例？                      │
│                                                             │
│  Step 4: 执行简化                                            │
│     ├── 每次只改一处                                         │
│     ├── 改后立即运行测试                                     │
│     ├── 测试失败立即回滚                                     │
│     └── 记录变更到 Decision Log                              │
│                                                             │
│  Step 5: 验证                                                │
│     ├── 所有测试通过                                         │
│     ├── 公共API不变                                          │
│     └── 无新复杂度引入                                       │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 涉及Agent

| Agent | 角色 | 职责 |
|-------|------|------|
| refactoring-specialist | 主导 | 协调简化审查流程、执行代码简化 |

---

## 输出格式

### 1. 简化报告 (simplify-report.md)

```markdown
# 代码简化报告

## 简化概要
- 简化时间: 2026-05-05 10:00:00
- 简化目标: src/services/
- 简化范围: dir

## 简化统计
| 指标 | 简化前 | 简化后 | 变化 |
|------|--------|--------|------|
| 死代码项 | 8 | 0 | -100% |
| 深层嵌套 | 3 | 0 | -100% |
| 复杂条件 | 2 | 0 | -100% |
| 长函数 | 4 | 1 | -75% |
| 重复字符串 | 6 | 0 | -100% |

## 简化详情

### S-001: 移除未使用的导入
- 类型: dead_code / unused_import
- 文件: src/services/user-service.ts
- Chesterton's Fence: 已确认无引用
- 三方面验证: 行为等价✓ 可读性✓ 一致性✓

### S-002: 消除深层嵌套
- 类型: deep_nesting
- 文件: src/services/order-processor.ts
- Chesterton's Fence: 业务逻辑不变，使用早返回替代嵌套
- 三方面验证: 行为等价✓ 可读性✓ 一致性✓

## 测试验证
- 简化前测试: 128 passed / 0 failed
- 简化后测试: 128 passed / 0 failed
- 公共API: 无变更
- 新复杂度: 无引入
```

### 2. 简化记录 (simplify-result.json)

```json
{
  "simplify_id": "SIMP-20260505-001",
  "timestamp": "2026-05-05T10:30:00Z",
  "target": "src/services/",
  "scope": "dir",
  "steps_completed": 5,
  "chesterton_fence_items": [
    {
      "item": "legacy_validation",
      "reason": "不确定存在原因，保留不修改",
      "action": "skip"
    }
  ],
  "simplifications": [
    {
      "id": "S-001",
      "type": "dead_code",
      "file": "src/services/user-service.ts",
      "line": 5,
      "description": "Unused import: lodash",
      "verified": true
    }
  ],
  "verification": {
    "all_tests_passed": true,
    "public_api_unchanged": true,
    "no_new_complexity": true
  }
}
```

---

## 质量门禁

| 门禁标识 | 阻塞级别(BLOCK/WARN) | 通过标准 |
|----------|----------------------|----------|
| SIMPLIFICATION-BEHAVIOR | BLOCK | 简化后行为等价+测试通过+公共API不变 |
| CHESTERTON-FENCE | WARN | 每处删除/修改前已理解存在原因 |

---

## 示例用法

### 示例1: 简化最近修改的文件

```bash
/simplify
```

对最近修改的文件执行简化审查，默认 scope=recent。

### 示例2: 简化当前文件

```bash
/simplify file
```

对当前文件执行简化审查。

### 示例3: 简化当前目录

```bash
/simplify dir
```

对当前目录下所有源代码文件执行简化审查。

---

## 注意事项

1. **Chesterton's Fence**: 不确定代码存在原因时，绝不修改或删除
2. **行为等价**: 简化必须保证相同输入→相同输出、相同错误、相同副作用
3. **每次只改一处**: 避免批量修改导致难以定位问题
4. **立即测试**: 每次简化后立即运行测试，失败立即回滚
5. **三方面验证**: 行为等价、可读性提升、风格一致缺一不可

---

## 相关工作流

- `workflows/sdd-tdd-full.md` (Phase 7) - SDD+TDD全生命周期工作流的简化与优化阶段

---

## 相关脚本

- `scripts/code-simplifier.py` - 代码简化检测器，识别死代码、深层嵌套、复杂条件等
- `scripts/deduplication-detector.py` - 重复代码检测器，识别相同代码块和相似函数

---

## 相关命令

- `/refactor --simplify` - 在重构流程中启用简化审查
- `/review` - 代码审查发现简化机会
- `/test` - 运行测试验证简化结果
