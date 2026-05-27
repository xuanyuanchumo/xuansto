# Design Token 系统架构参考文档

> 版本: 3.2.0 | 更新日期: 2026-05-06 | 编码: UTF-8 without BOM | 行尾: LF

---

## 概述

Design Token系统是连接设计与开发的桥梁，通过结构化的Token定义实现设计决策的集中管理、跨平台转换和自动化交付。本文档涵盖Style Dictionary工具链、Token分类体系、跨平台转换策略和设计工具集成。

---

## Token分类体系

### 三层分类模型

```
Global Tokens（全局层）
    │
    ├── Alias Tokens（别名层/语义层）
    │       │
    │       └── Component Tokens（组件层）
    │
    └── 直接引用Global Tokens的组件
```

### Global Tokens（全局层）

定义原始设计值，是整个系统的原子单位。

```yaml
global_tokens:
  color:
    gray:
      50: "#f9fafb"
      100: "#f3f4f6"
      200: "#e5e7eb"
      500: "#6b7280"
      900: "#111827"
    blue:
      50: "#eff6ff"
      500: "#3b82f6"
      700: "#1d4ed8"
    red:
      500: "#ef4444"
      700: "#b91c1c"
  spacing:
    0: "0px"
    1: "4px"
    2: "8px"
    3: "12px"
    4: "16px"
    6: "24px"
    8: "32px"
  typography:
    font_family:
      sans: "'Inter', system-ui, sans-serif"
      mono: "'JetBrains Mono', monospace"
    font_size:
      xs: "0.75rem"
      sm: "0.875rem"
      base: "1rem"
      lg: "1.125rem"
      xl: "1.25rem"
    font_weight:
      normal: 400
      medium: 500
      semibold: 600
      bold: 700
    line_height:
      tight: 1.25
      normal: 1.5
      relaxed: 1.75
  border_radius:
    sm: "4px"
    md: "8px"
    lg: "12px"
    full: "9999px"
  shadow:
    sm: "0 1px 2px rgba(0,0,0,0.05)"
    md: "0 4px 6px rgba(0,0,0,0.1)"
    lg: "0 10px 15px rgba(0,0,0,0.1)"
```

### Alias Tokens（语义层）

为Global Tokens赋予语义含义，支持主题切换。

```yaml
alias_tokens:
  color:
    background:
      primary: "{color.gray.50}"
      secondary: "{color.gray.100}"
      inverse: "{color.gray.900}"
    text:
      primary: "{color.gray.900}"
      secondary: "{color.gray.500}"
      inverse: "{color.gray.50}"
      link: "{color.blue.700}"
      error: "{color.red.700}"
    border:
      default: "{color.gray.200}"
      focus: "{color.blue.500}"
      error: "{color.red.500}"
    interactive:
      primary: "{color.blue.500}"
      hover: "{color.blue.700}"
      disabled: "{color.gray.200}"
  spacing:
    inline:
      xs: "{spacing.1}"
      sm: "{spacing.2}"
      md: "{spacing.4}"
    stack:
      xs: "{spacing.1}"
      sm: "{spacing.2}"
      md: "{spacing.4}"
      lg: "{spacing.6}"
```

### Component Tokens（组件层）

绑定到特定组件的Token，是最具体的层级。

```yaml
component_tokens:
  button:
    padding_x: "{spacing.4}"
    padding_y: "{spacing.2}"
    border_radius: "{border_radius.md}"
    font_size: "{typography.font_size.sm}"
    font_weight: "{typography.font_weight.medium}"
    primary:
      background: "{alias.color.interactive.primary}"
      text: "{alias.color.text.inverse}"
    secondary:
      background: "transparent"
      text: "{alias.color.interactive.primary}"
      border: "{alias.color.interactive.primary}"
  input:
    padding_x: "{spacing.3}"
    padding_y: "{spacing.2}"
    border_radius: "{border_radius.md}"
    border: "{alias.color.border.default}"
    focus_border: "{alias.color.border.focus}"
    error_border: "{alias.color.border.error}"
```

---

## Style Dictionary 工具链

### 配置

```javascript
// style-dictionary.config.js
module.exports = {
  source: ["tokens/**/*.yaml"],
  platforms: {
    css: {
      transformGroup: "css",
      buildPath: "dist/css/",
      files: [{
        destination: "variables.css",
        format: "css/variables",
        options: { outputReferences: true }
      }]
    },
    scss: {
      transformGroup: "scss",
      buildPath: "dist/scss/",
      files: [{
        destination: "_variables.scss",
        format: "scss/variables",
        options: { outputReferences: true }
      }]
    },
    js: {
      transformGroup: "js",
      buildPath: "dist/js/",
      files: [{
        destination: "tokens.js",
        format: "javascript/es6"
      }, {
        destination: "tokens.d.ts",
        format: "typescript/es6-declarations"
      }]
    },
    ios: {
      transformGroup: "ios-swift-separate",
      buildPath: "dist/ios/",
      files: [{
        destination: "Color.swift",
        format: "ios-swift/class.swift",
        filter: { attributes: { category: "color" } }
      }]
    },
    android: {
      transformGroup: "android",
      buildPath: "dist/android/",
      files: [{
        destination: "colors.xml",
        format: "android/colors",
        filter: { attributes: { category: "color" } }
      }]
    }
  }
}
```

---

## 跨平台转换

### 转换策略

| 平台 | 格式 | 颜色空间 | 单位 | 字体 |
|------|------|---------|------|------|
| Web (CSS) | CSS Variables | HEX/RGB | rem/px | font-family |
| Web (SCSS) | SCSS Variables | HEX/RGB | rem/px | font-family |
| React Native | JS Object | HEX | dp | fontFamily |
| iOS (Swift) | Swift Class | UIColor | pt | UIFont |
| Android (Kotlin) | XML/Kotlin | HEX/ColorStateList | dp/sp | Typeface |
| Flutter (Dart) | Dart Class | Color | logical pixels | TextStyle |

### 自定义Transform

```javascript
StyleDictionary.registerTransform({
  name: "size/pxToDp",
  type: "value",
  matcher: (prop) => prop.attributes.category === "size",
  transformer: (prop) => `${parseFloat(prop.value) * 2}dp`
})
```

---

## 设计工具集成

### Figma集成

```yaml
figma_integration:
  plugin: "Tokens Studio"
  sync_direction: bidirectional
  features:
    - Token导入导出
    - 主题切换预览
    - 组件Token绑定
    - 变量模式映射
  workflow:
    design_change: "Figma → Token JSON → Style Dictionary → 代码"
    code_change: "代码 → Token JSON → Figma更新"
```

### Penpot集成

```yaml
penpot_integration:
  approach: "Token CSS导出"
  features:
    - CSS变量导入
    - 设计Token映射
    - 组件样式同步
  workflow:
    - Style Dictionary导出CSS变量
    - Penpot导入CSS变量文件
    - 设计元素绑定Token
```

---

## 与xuansto-skill的集成

| xuansto模块 | Design Token | 集成方式 |
|------------|-------------|---------|
| UI/UX Workflow | Token定义 | 设计阶段输出Token |
| Component Testing | Token验证 | 组件测试检查Token使用 |
| Cross-Platform | 跨平台转换 | 多平台Token输出 |
| Quality Gates | Token一致性 | 检查Token引用完整性 |

---

> 本文档由 Multi-Agent SDD/TDD Orchestrator 维护 | 最后更新: 2026-05-06
