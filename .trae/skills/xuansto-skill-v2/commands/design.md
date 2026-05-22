---
name: /design
aliases:
  - d
category: workflow
phase: "3"
description: UI/UX设计与原型制作
trigger: 需要界面设计或交互设计时
workflow: ui-ux-workflow
---

# /design 命令

## 命令用途

执行UI/UX设计流程，包括界面设计、交互设计、视觉设计和原型制作，确保产品具有良好的用户体验。

## MCP工具调用链

| 顺序 | MCP工具 | 参数 | 说明 |
|------|---------|------|------|
| 1 | knowledge_search | query=<设计需求> | 搜索知识库中设计模式和最佳实践 |
| 2 | skill_analyze | scope=design | 分析设计技能需求和组件匹配 |

## 降级策略

| MCP工具 | 降级方式 | 降级脚本/操作 |
|---------|----------|---------------|
| knowledge_search | 脚本调用 | python scripts/knowledge-server.py --search [query] |
| skill_analyze | 脚本调用 | python scripts/skill-test.py --analyze |

## 涉及Agent

| Agent | 角色 | 职责 |
|-------|------|------|
| ux-designer | 主导 | 用户研究、信息架构、用户旅程 |
| ui-designer | 主导 | 界面设计、交互设计、组件设计 |
| frontend-stylist | 辅助 | 视觉系统、CSS实现、主题系统、响应式 |
| product-manager | 辅助 | 需求确认、优先级 |

## 命令描述

执行UI/UX设计流程，包括界面设计、交互设计、视觉设计和原型制作。该命令协调设计相关Agent，确保产品具有良好的用户体验。

## 触发条件

| 触发方式 | 说明 |
|----------|------|
| 命令输入 | 用户输入 `/design` |
| 关键词触发 | 用户提及"UI/UX设计"、"界面设计"、"交互设计" |
| 自动触发 | `/sprint` 命令执行时自动调用Design阶段 |
| 流程触发 | `/spec` 完成后自动进入Design阶段 |

## 命令名称与语法

```
/design [--type=<类型>] [--style=<风格>] [--output=<输出>]
```

## 参数定义

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `--type` | enum | 否 | all | 设计类型：all/ui/ux/visual/prototype |
| `--style` | enum | 否 | modern | 设计风格：modern/minimal/brutal/glass/neumorphic |
| `--output` | enum | 否 | html | 输出格式：html/figma/sketch/code |
| `--responsive` | flag | 否 | true | 生成响应式设计 |
| `--dark-mode` | flag | 否 | true | 包含暗色主题 |
| `--accessibility` | flag | 否 | true | 符合WCAG标准 |
| `--components` | list | 否 | auto | 指定组件库：shadcn/material/ant/chakra |

## 执行流程

> 标准五步框架：1. 输入验证 → 2. Agent调度 → 3. 任务执行 → 4. 结果验证 → 5. 输出交付

1. **输入验证**：校验`--type`和`--style`参数合法、规格文件存在；检查设计系统配置
2. **Agent调度**：ux-designer主导用户研究，ui-designer主导界面设计，frontend-stylist负责视觉系统
3. **任务执行**：执行UX研究→线框图→UI设计→视觉设计→交互设计→原型制作的完整设计流程
4. **结果验证**：执行DESIGN-REVIEW和DESIGN-TOKENS门禁检查
5. **输出交付**：生成设计文档、组件HTML、design-tokens.json

## 质量门禁

| 门禁标识 | 阻塞级别(BLOCK/WARN) | 通过标准 |
|----------|----------------------|----------|
| DESIGN-REVIEW | BLOCK | 设计系统一致性、响应式适配、暗色主题支持、无障碍合规 |
| DESIGN-TOKENS | WARN | 色彩系统完整、字体排版规范、间距系统定义、主题变量可切换 |
| DESIGN-SYSTEM-COMPLETE | BLOCK | 设计系统已生成+风格+配色+字体+反模式检查通过 |
| ANTI-PATTERN-CHECK | BLOCK | 配色方案无行业反模式违规、风格选择无行业冲突 |
| DESIGN-ACCESSIBILITY | BLOCK | WCAG 2.1 AA标准合规、色彩对比度验证、键盘导航可用性 |

## 使用示例

### 示例1：完整设计流程

```
/design
```

### 示例2：仅UI设计

```
/design --type=ui --style=modern
```

### 示例3：玻璃拟态风格

```
/design --style=glass --dark-mode
```

### 示例4：生成可交互原型

```
/design --type=prototype --output=html
```

### 示例5：指定组件库

```
/design --components=shadcn --responsive
```

## 相关脚本

- `scripts/design-tokens-sync.js` - 设计令牌同步器，同步设计令牌到项目代码和样式文件

---

## 相关命令

- `/spec` - 规格编写
- `/implement` - 开始实施
- `/sprint` - 启动完整冲刺
