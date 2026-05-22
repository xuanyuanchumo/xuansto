# UI组件开发与视觉回归测试参考文档

> 版本: 3.2.0 | 更新日期: 2026-05-06 | 编码: UTF-8 without BOM | 行尾: LF

---

## 概述

UI组件开发与视觉回归测试是确保界面一致性和质量的关键环节。本文档涵盖Storybook组件开发工作流、Chromatic视觉回归测试和Playwright组件测试三大工具链的集成使用。

---

## Storybook 组件开发

### 项目配置

```yaml
storybook:
  version: "8.x"
  framework: "@storybook/react-vite"
  features:
    - Story文件自动生成
    - ArgsTable交互式文档
    - Controls参数面板
    - Actions事件追踪
    - Viewport响应式预览
  structure:
    stories_dir: "src/**/*.stories.tsx"
    docs_dir: "src/**/*.mdx"
```

### Story编写规范

```typescript
// Button.stories.tsx
import type { Meta, StoryObj } from "@storybook/react"
import { Button } from "./Button"

const meta: Meta<typeof Button> = {
  title: "Components/Button",
  component: Button,
  tags: ["autodocs"],
  argTypes: {
    variant: {
      control: "select",
      options: ["primary", "secondary", "ghost", "danger"],
    },
    size: {
      control: "select",
      options: ["sm", "md", "lg"],
    },
  },
}

export default meta
type Story = StoryObj<typeof Button>

export const Primary: Story = {
  args: { variant: "primary", children: "Click me" },
}

export const Secondary: Story = {
  args: { variant: "secondary", children: "Click me" },
}

export const Disabled: Story = {
  args: { variant: "primary", disabled: true, children: "Disabled" },
}
```

### 组件开发工作流

```
1. 编写组件接口（TypeScript Props）
2. 创建Story文件，定义所有变体
3. 在Storybook中交互式开发
4. 编写组件单元测试
5. 添加MDX文档
6. 提交视觉回归基线
```

---

## Chromatic 视觉回归测试

### 工作原理

Chromatic通过截图对比检测UI变更，每次Storybook发布时自动捕获所有Story的截图并与基线对比。

### 配置

```yaml
chromatic:
  version: "11.x"
  integration: "GitHub Actions"
  config:
    auto_accept_changes: false
    exit_zero_on_changes: false
    ignore_last_build_on_branch: "main"
    storybook_base_dir: "storybook-static"
  snapshot_options:
    viewports: [320, 768, 1280]
    diff_threshold: 0.06
    delay: 300
```

### CI/CD集成

```yaml
# .github/workflows/chromatic.yml
name: Visual Regression
on: [push]
jobs:
  chromatic:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with: { fetch-depth: 0 }
      - uses: actions/setup-node@v4
        with: { node-version: 20 }
      - run: npm ci
      - run: npm run build-storybook
      - uses: chromaui/action@v11
        with:
          projectToken: ${{ secrets.CHROMATIC_TOKEN }}
          exitOnceUploaded: true
```

### 变更审查流程

```
代码提交 → Chromatic截图 → 与基线对比
    │                          │
    │                    ┌─────┴─────┐
    │                    │           │
    │               无变更 ✓     检测到变更
    │                                │
    │                          ┌─────┴─────┐
    │                          │           │
    │                      接受变更     拒绝变更
    │                          │           │
    │                    更新基线     修复代码
```

---

## Playwright 组件测试

### 组件测试配置

```yaml
playwright_component:
  version: "1.48+"
  features:
    - 组件级隔离测试
    - 无需完整应用启动
    - 支持交互模拟
    - 截图对比
    - 可访问性断言
```

### 测试编写

```typescript
// Button.spec.tsx
import { test, expect } from "@playwright/experimental-ct-react"
import { Button } from "./Button"

test("renders primary variant", async ({ mount }) => {
  const component = await mount(
    <Button variant="primary">Click me</Button>
  )
  await expect(component).toHaveText("Click me")
  await expect(component).toHaveClass(/primary/)
})

test("handles click events", async ({ mount }) => {
  let clicked = false
  const component = await mount(
    <Button onClick={() => { clicked = true }}>Click me</Button>
  )
  await component.click()
  expect(clicked).toBe(true)
})

test("matches visual snapshot", async ({ mount }) => {
  const component = await mount(
    <Button variant="primary" size="md">Click me</Button>
  )
  await expect(component).toHaveScreenshot("button-primary-md.png")
})

test("is accessible", async ({ mount }) => {
  const component = await mount(
    <Button variant="primary">Click me</Button>
  )
  await expect(component).toBeAccessible()
})
```

### 测试策略矩阵

| 测试类型 | 工具 | 范围 | 速度 | 目的 |
|---------|------|------|------|------|
| 单元测试 | Vitest | 逻辑 | 快 | 函数行为验证 |
| 组件测试 | Playwright CT | 渲染+交互 | 中 | 组件渲染与交互 |
| 视觉回归 | Chromatic | 截图对比 | 中 | 视觉一致性 |
| 可访问性 | axe-core | A11y规则 | 快 | 无障碍合规 |
| E2E测试 | Playwright | 完整流程 | 慢 | 用户流程验证 |

---

## 三工具协同工作流

```
组件开发 → Storybook预览 → Playwright组件测试 → Chromatic视觉回归
    │            │                  │                    │
    ├─ 编写代码   ├─ 交互验证         ├─ 行为断言           ├─ 截图基线
    ├─ 定义Props  ├─ 变体覆盖         ├─ 交互模拟           ├─ 变更检测
    └─ 类型检查   └─ 文档生成         └─ 可访问性检查        └─ 审查流程
```

---

## 与xuansto-skill的集成

| xuansto模块 | 组件测试工具 | 集成方式 |
|------------|-----------|---------|
| UI/UX Workflow | Storybook | 设计到组件的开发流 |
| Quality Gates | Chromatic | 视觉回归门禁 |
| Webapp Testing | Playwright CT | 组件级测试覆盖 |
| TDD Workflow | Playwright CT | RED阶段组件测试 |

---

> 本文档由 Multi-Agent SDD/TDD Orchestrator 维护 | 最后更新: 2026-05-06
