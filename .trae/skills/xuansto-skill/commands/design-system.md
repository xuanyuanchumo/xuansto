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

```
┌─────────────────────────────────────────────────────────────┐
│              /design-system 执行流程                          │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌──────────────┐                                          │
│  │  1.输入验证    │                                          │
│  │  解析产品类型  │                                          │
│  │  验证参数     │                                          │
│  └──────┬───────┘                                          │
│         │                                                   │
│         ▼                                                   │
│  ┌──────────────┐                                          │
│  │  2.Agent调度   │                                          │
│  │  Design System │                                          │
│  │  Generator    │                                          │
│  └──────┬───────┘                                          │
│         │                                                   │
│         ▼                                                   │
│  ┌──────────────────────────────────────────┐              │
│  │  3.5域并行搜索                             │              │
│  │  ├─ 产品类型匹配 (161种)                   │              │
│  │  ├─ 风格推荐 (67种)                       │              │
│  │  ├─ 配色选择 (161套)                       │              │
│  │  ├─ 落地页模式 (24种)                      │              │
│  │  └─ 字体配对 (57组)                        │              │
│  └──────┬───────────────────────────────────┘              │
│         │                                                   │
│         ▼                                                   │
│  ┌──────────────┐                                          │
│  │  推理引擎     │                                          │
│  │  ├─ 风格排序  │                                          │
│  │  ├─ 反模式过滤│                                          │
│  │  └─ 决策输出  │                                          │
│  └──────┬───────┘                                          │
│         │                                                   │
│         ▼                                                   │
│  ┌──────────────┐    ┌──────────────┐                      │
│  │  4.结果验证    │───▶│  输出产物     │                      │
│  │  门禁检查     │    │              │                      │
│  └──────────────┘    └──────────────┘                      │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 执行阶段详情

1. **输入验证**
   - 解析产品类型参数
   - 如未指定，从项目上下文自动推断
   - 验证`--style`/`--palette`/`--font`参数是否在参考数据库中

2. **Agent调度**
   - 激活Design System Generator Agent
   - 传入产品类型和用户偏好参数

3. **5域并行搜索 + 推理**
   - 产品类型匹配：搜索product-reasoning-rules.md
   - 风格推荐：搜索design-database.md
   - 配色选择：搜索color-palettes.md
   - 落地页模式：基于产品类型推理
   - 字体配对：搜索font-pairings.md
   - 推理引擎：排序+过滤+决策

4. **结果验证**
   - DESIGN-SYSTEM-COMPLETE门禁检查
   - ANTI-PATTERN-CHECK门禁检查

## 涉及Agent

| Agent | 角色 | 职责 |
|-------|------|------|
| Design System Generator | 主导 | 5域搜索、推理引擎、设计系统输出 |
| UI Designer | 辅助 | 视觉设计细化、组件规范 |
| UX Designer | 辅助 | 可访问性验证、交互规范 |

## 输出格式

### 输出文件结构

```
.agent_cache/<task>/
├── design-system.md          # 完整设计系统文档
└── design-system-report.md   # 推理链+反模式检查报告

templates/
└── design-tokens.json        # 设计令牌更新
```

### design-system.md 输出示例

```markdown
# 设计系统 - SaaS项目管理平台

## 产品分析
- 产品类型: 项目管理SaaS
- UI分类规则: Dashboard-first + 看板
- 推理来源: product-reasoning-rules.md #2

## 风格选择
- 推荐风格: Clean Design
- 选择理由: 项目管理工具需要清晰的信息层级和高效的操作流程，
  Clean Design的整洁规范特性最匹配Dashboard-first+看板的需求
- 备选风格: Flat Design 2.0
- 推理来源: design-database.md #2

## 配色方案
- 主色: #EA580C (橙色 - 行动感)
- 辅色: #F97316 (浅橙 - 辅助)
- CTA色: #2563EB (蓝色 - 行动引导)
- 背景色: #FFF7ED (暖白 - 舒适)
- 文字色: #7C2D12 (深棕 - 可读)
- 推理来源: color-palettes.md SaaS-Orange
- 反模式检查: PASS (无行业反模式违规)

## 字体配对
- 标题字体: Outfit (600/700) - 现代、简洁、高效
- 正文字体: Outfit (400/500) - 与标题统一
- 推理来源: font-pairings.md #6

## 图表推荐
- 任务进度: 柱状图/子弹图
- 团队工作量: 雷达图
- 项目时间线: 甘特图
- 推理来源: chart-recommendations.md

## 组件规范
- 圆角: 8px (rounded-lg)
- 阴影: shadow-sm / shadow-md
- 间距: 4px基础单位

## 暗色主题
- 背景: #1C1410
- 表面: #2D2018
- 文字: #FFF7ED
- 主色: #F97316
```

### design-tokens.json 输出示例

```json
{
  "colors": {
    "brand": {
      "primary": { "value": "#EA580C", "type": "color" },
      "secondary": { "value": "#F97316", "type": "color" },
      "cta": { "value": "#2563EB", "type": "color" }
    },
    "background": {
      "default": { "value": "#FFF7ED", "type": "color" },
      "surface": { "value": "#FFFFFF", "type": "color" },
      "dark": { "value": "#1C1410", "type": "color" }
    },
    "text": {
      "primary": { "value": "#7C2D12", "type": "color" },
      "secondary": { "value": "#9A3412", "type": "color" },
      "dark": { "value": "#FFF7ED", "type": "color" }
    },
    "semantic": {
      "success": { "value": "#16A34A", "type": "color" },
      "warning": { "value": "#F59E0B", "type": "color" },
      "error": { "value": "#DC2626", "type": "color" },
      "info": { "value": "#2563EB", "type": "color" }
    }
  },
  "typography": {
    "fontFamily": {
      "heading": { "value": "'Outfit', sans-serif", "type": "fontFamily" },
      "body": { "value": "'Outfit', sans-serif", "type": "fontFamily" }
    },
    "fontWeight": {
      "regular": { "value": "400" },
      "medium": { "value": "500" },
      "semibold": { "value": "600" },
      "bold": { "value": "700" }
    }
  },
  "spacing": {
    "1": { "value": "4px" },
    "2": { "value": "8px" },
    "3": { "value": "12px" },
    "4": { "value": "16px" },
    "6": { "value": "24px" },
    "8": { "value": "32px" }
  },
  "borderRadius": {
    "sm": { "value": "4px" },
    "md": { "value": "6px" },
    "lg": { "value": "8px" },
    "xl": { "value": "12px" }
  },
  "shadows": {
    "sm": { "value": "0 1px 2px 0 rgba(0,0,0,0.05)" },
    "md": { "value": "0 4px 6px -1px rgba(0,0,0,0.1)" },
    "lg": { "value": "0 10px 15px -3px rgba(0,0,0,0.1)" }
  },
  "breakpoints": {
    "sm": { "value": "640px" },
    "md": { "value": "768px" },
    "lg": { "value": "1024px" },
    "xl": { "value": "1280px" },
    "2xl": { "value": "1536px" }
  }
}
```

## 质量门禁

| 门禁标识 | 阶段 | 阻塞级别 | 通过标准 |
|----------|------|----------|----------|
| DESIGN-SYSTEM-COMPLETE | Phase 0 | BLOCK | 设计系统已生成+风格+配色+字体+反模式+检查清单 |
| ANTI-PATTERN-CHECK | Phase 0 | BLOCK | 无行业反模式违规 |

设计系统生成后自动检查：

- [ ] 产品类型已匹配
- [ ] 风格已选择并说明理由
- [ ] 配色方案已选择并说明理由
- [ ] 反模式检查已通过
- [ ] 字体配对已选择
- [ ] WCAG AA对比度达标
- [ ] 暗色主题方案已包含
- [ ] 设计令牌已输出

## 示例用法

### 示例1：自动推理（推荐）

```
/design-system SaaS
```

Agent自动推理：SaaS → Dashboard-first → Clean Design → SaaS-Blue配色 → Inter字体

### 示例2：指定产品类型

```
/design-system healthcare
```

Agent自动推理：Healthcare → Mobile-first → Clean Design → Health-Blue配色 → Nunito字体

### 示例3：覆盖风格

```
/design-system fintech --style=Carbon
```

使用Carbon风格替代自动推理的Corporate风格

### 示例4：指定框架

```
/design-system e-commerce --framework=tailwind
```

输出Tailwind CSS特定的设计令牌和类名

### 示例5：完整指定

```
/design-system gaming --style=Dark+Mode --palette=Game-Purple --dark-mode
```

完全自定义设计系统参数

## 相关脚本

- `scripts/design-tokens-sync.js` - 设计令牌同步器，同步设计令牌到项目代码和样式文件

---

## 相关工作流

- `workflows/ui-ux-workflow.md` - UI/UX工作流，定义设计系统生成的完整执行流程

---

## 相关命令

- `/design` - UI/UX设计与原型制作
- `/spec` - 规格编写
- `/implement` - 开始实施
- `/sprint` - 启动完整冲刺
