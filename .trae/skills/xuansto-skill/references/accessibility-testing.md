# 无障碍测试自动化参考文档

> 版本: 3.2.0 | 更新日期: 2026-05-06 | 编码: UTF-8 without BOM | 行尾: LF

---

## 概述

无障碍（Accessibility, a11y）测试确保Web应用对所有用户可用，包括使用辅助技术的用户。本文档涵盖axe-core、Pa11y工具链、WCAG 2.1 AA合规标准和自动化与手动测试策略。

---

## WCAG 2.1 AA合规标准

### 四大原则

| 原则 | 含义 | 关键成功标准 |
|------|------|------------|
| 可感知（Perceivable） | 信息可被所有用户感知 | 1.1.1 非文本内容、1.4.3 对比度、1.4.11 非文本对比度 |
| 可操作（Operable） | 界面可被所有用户操作 | 2.1.1 键盘可操作、2.4.3 焦点顺序、2.4.7 焦点可见 |
| 可理解（Understandable） | 内容和操作可被理解 | 3.1.1 页面语言、3.2.2 输入时标签、3.3.1 错误标识 |
| 健壮性（Robust） | 内容可被辅助技术解析 | 4.1.1 解析、4.1.2 名称/角色/值 |

### AA级关键检查项

```yaml
wcag_2_1_aa:
  perceivable:
    - id: "1.1.1"
      name: "非文本内容"
      check: "所有img有alt属性，装饰性图片alt为空"
    - id: "1.4.3"
      name: "对比度（最低要求）"
      check: "文本对比度≥4.5:1，大文本≥3:1"
    - id: "1.4.11"
      name: "非文本对比度"
      check: "UI组件和图形对象对比度≥3:1"
  operable:
    - id: "2.1.1"
      name: "键盘可操作"
      check: "所有功能可通过键盘操作"
    - id: "2.4.3"
      name: "焦点顺序"
      check: "焦点顺序保持意义和可操作性"
    - id: "2.4.7"
      name: "焦点可见"
      check: "键盘焦点始终可见"
  understandable:
    - id: "3.3.1"
      name: "错误标识"
      check: "自动检测错误并通知用户"
    - id: "3.3.2"
      name: "标签或说明"
      check: "用户输入有标签或说明"
  robust:
    - id: "4.1.2"
      name: "名称/角色/值"
      check: "UI组件有可编程确定的名称和角色"
```

---

## axe-core 自动化测试

### 核心特性

axe-core是Deque Systems开发的浏览器无障碍测试引擎，支持自动化检测WCAG违规。

### Playwright集成

```typescript
import { test, expect } from "@playwright/test"
import AxeBuilder from "@axe-core/playwright"

test("页面无障碍检查", async ({ page }) => {
  await page.goto("/dashboard")

  const results = await new AxeBuilder({ page })
    .withTags(["wcag2a", "wcag2aa", "wcag21a", "wcag21aa"])
    .exclude(".third-party-widget")
    .analyze()

  expect(results.violations).toEqual([])
})

test("组件级无障碍检查", async ({ page }) => {
  await page.goto("/components/button")

  const results = await new AxeBuilder({ page })
    .include("#button-component")
    .analyze()

  expect(results.violations).toEqual([])
})
```

### Jest集成

```typescript
import { axe, toHaveNoViolations } from "jest-axe"

expect.extend(toHaveNoViolations)

test("Button组件无障碍", async () => {
  const { container } = render(<Button>Click me</Button>)
  const results = await axe(container)
  expect(results).toHaveNoViolations()
})
```

### 规则配置

```yaml
axe_core:
  version: "4.x"
  rules:
    enabled:
      - color-contrast
      - image-alt
      - label
      - keyboard
      - focus-order
      - aria-roles
      - aria-valid-attr
    disabled:
      - region
    tags:
      - wcag2a
      - wcag2aa
      - wcag21a
      - wcag21aa
      - best-practice
```

---

## Pa11y 测试工具

### 命令行使用

```bash
# 单页面测试
pa11y https://example.com

# 配置文件测试
pa11y -c .pa11yrc.json https://example.com

# CI模式（发现错误时退出码非零）
pa11y --threshold 0 https://example.com
```

### 配置文件

```yaml
# .pa11yrc.json
pa11y:
  defaults:
    standard: WCAG2AA
    runners:
      - axe
      - htmlcs
    timeout: 30000
    wait: 1000
    actions:
      - "wait for element .app-loaded to be visible"
    ignore:
      - notice
      - warning
    threshold: 0
  urls:
    - url: "http://localhost:3000/"
      actions:
        - "set field #username to admin"
        - "set field #password to password"
        - "click element #login"
        - "wait for url to be /dashboard"
    - url: "http://localhost:3000/dashboard"
    - url: "http://localhost:3000/settings"
```

### CI/CD集成

```yaml
# .github/workflows/a11y.yml
name: Accessibility Tests
on: [push]
jobs:
  pa11y:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
      - run: npm ci
      - run: npm run build
      - run: npm run start &
      - run: npx wait-on http://localhost:3000
      - run: npx pa11y-ci
```

---

## 自动化与手动测试策略

### 测试金字塔

```
              /手动测试\
             /  (屏幕阅读器)\
            /  (键盘导航)     \
           /  (语音控制)       \
          /--------------------\
         /  半自动测试          \
        /  (axe DevTools)       \
       /  (键盘Tab检查)          \
      /----------------------------\
     /    全自动测试                 \
    /    (axe-core, Pa11y CI)        \
   /------------------------------------\
```

### 策略矩阵

| 测试类型 | 工具 | 频率 | 覆盖范围 | 自动化程度 |
|---------|------|------|---------|-----------|
| CI自动化 | axe-core + Pa11y | 每次提交 | WCAG规则 | 100% |
| 组件测试 | jest-axe | 每次提交 | 组件级 | 100% |
| 开发者检查 | axe DevTools | 开发时 | 当前页面 | 半自动 |
| 键盘导航 | 手动 | 每Sprint | 关键流程 | 手动 |
| 屏幕阅读器 | NVDA/VoiceOver | 每版本 | 核心功能 | 手动 |
| 语音控制 | Dragon | 每季度 | 关键交互 | 手动 |

---

## 与xuansto-skill的集成

| xuansto模块 | A11y工具 | 集成方式 |
|------------|---------|---------|
| Quality Gates | axe-core | 门禁检查无障碍违规 |
| Webapp Testing | Pa11y CI | 自动化测试流水线 |
| UI/UX Workflow | WCAG标准 | 设计阶段无障碍规范 |
| Component Testing | jest-axe | 组件级无障碍断言 |

---

> 本文档由 Multi-Agent SDD/TDD Orchestrator 维护 | 最后更新: 2026-05-06
