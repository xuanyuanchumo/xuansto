---
name: /design-system
aliases:
  - ds
  - design-sys
category: workflow
phase: "0"
description: 自动生成完整设计系统（风格+配色+字体+反模式检查）
trigger: 需要为项目生成设计系统时
workflow: ui-ux-workflow
---

# /design-system 命令

## 命令用途

基于UIUXProMax设计智能引擎，根据产品类型自动生成完整设计系统，包括风格、配色、字体配对、图表推荐和反模式检查。

## MCP工具调用链

| 顺序 | MCP工具 | 参数 | 说明 |
|------|---------|------|------|
| 1 | knowledge_search | scope=general, query=<产品类型> | 搜索通用设计知识库中产品类型匹配规则 |
| 2 | skill_analyze | scope=design-system | 分析设计系统技能需求和推理引擎 |

## 降级策略

| MCP工具 | 降级方式 | 降级脚本/操作 |
|---------|----------|---------------|
| knowledge_search | 脚本调用 | python scripts/knowledge-server.py --search [query] |
| skill_analyze | 脚本调用 | python scripts/skill-test.py --analyze |

## 涉及Agent

| Agent | 角色 | 职责 |
|-------|------|------|
| Design System Generator | 主导 | 5域搜索、推理引擎、设计系统输出 |
| UI Designer | 辅助 | 视觉设计细化、组件规范 |
| UX Designer | 辅助 | 可访问性验证、交互规范 |

## 命令描述

基于UIUXProMax设计智能引擎，根据产品类型自动生成完整设计系统。通过5域并行搜索和推理引擎，输出风格、配色、字体配对、图表推荐和反模式检查结果。

## 触发条件

| 触发方式 | 说明 |
|----------|------|
| 命令输入 | 用户输入 `/design-system` |
| 别名触发 | `/ds`, `/design-sys` |
| 关键词触发 | 用户提及"设计系统"、"生成设计系统"、"配色方案"、"风格推荐" |
| 流程触发 | `/design` 命令执行时自动调用Design System Generator |

## 命令名称与语法

```
/design-system [product-type] [--style=<风格>] [--palette=<配色>] [--font=<字体>] [--skip-anti-pattern]
```

## 参数定义

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `[product-type]` | string | 否 | 自动检测 | 产品类型（如SaaS/e-commerce/healthcare/fintech/education等） |
| `--style` | enum | 否 | 自动推理 | 指定UI风格（覆盖自动推理结果） |
| `--palette` | enum | 否 | 自动推理 | 指定配色方案（覆盖自动推理结果） |
| `--font` | enum | 否 | 自动推理 | 指定字体配对（覆盖自动推理结果） |
| `--skip-anti-pattern` | flag | 否 | false | 跳过反模式检查（不推荐） |
| `--dark-mode` | flag | 否 | true | 包含暗色主题方案 |
| `--framework` | enum | 否 | auto | 技术框架：react/vue/tailwind/next/svelte |

## 执行流程

> 标准四步框架：1. 输入验证 → 2. Agent调度 → 3. 任务执行 → 4. 结果验证

1. **输入验证** - 解析产品类型参数，验证`--style`/`--palette`/`--font`参数
2. **Agent调度** - 激活Design System Generator Agent
3. **5域并行搜索 + 推理** - 产品类型匹配、风格推荐、配色选择、落地页模式、字体配对
4. **结果验证** - DESIGN-SYSTEM-COMPLETE和ANTI-PATTERN-CHECK门禁检查

## 质量门禁

| 门禁标识 | 阶段 | 阻塞级别 | 通过标准 |
|----------|------|----------|----------|
| DESIGN-SYSTEM-COMPLETE | Phase 0 | BLOCK | 设计系统已生成+风格+配色+字体+反模式+检查清单 |
| ANTI-PATTERN-CHECK | Phase 0 | BLOCK | 无行业反模式违规 |

## 使用示例

### 示例1：自动推理（推荐）

```
/design-system SaaS
```

### 示例2：指定产品类型

```
/design-system healthcare
```

### 示例3：覆盖风格

```
/design-system fintech --style=Carbon
```

### 示例4：指定框架

```
/design-system e-commerce --framework=tailwind
```

### 示例5：完整指定

```
/design-system gaming --style=Dark+Mode --palette=Game-Purple --dark-mode
```

## 相关脚本

- `scripts/design-tokens-sync.js` - 设计令牌同步器，同步设计令牌到项目代码和样式文件

---

## 相关命令

- `/design` - UI/UX设计与原型制作
- `/spec` - 规格编写
- `/implement` - 开始实施
- `/sprint` - 启动完整冲刺
