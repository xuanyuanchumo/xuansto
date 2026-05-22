# UI/UX设计司 自主操作指南 (Autonomous Operation Guide)

> 尚书省 · 工部 · 虞部司 · Universal DevOps v5.0
> 深度融合 ui-ux-pro-max 设计智能理念

## 概述

UI/UX设计司（虞部司）负责**自主 Design System 构建、界面原型生成、交互体验优化与无障碍合规**。本司不产出静态设计稿，而是输出可直接交付开发的设计决策体系——从 Design Token 到组件规范，从响应式策略到动画物理参数，全部以代码可消费的格式呈现。

### 定位

- **Design System 引擎**：自主生成完整的设计令牌系统（色彩/字体/间距/阴影/圆角/动画）
- **响应式架构师**：基于断点系统和栅格系统实现跨设备一致体验
- **无障碍守卫者**：确保所有设计决策符合 WCAG 2.1 AA 标准
- **交互物理学家**：为微交互定义符合直觉的缓动曲线和时长参数

### 目标

1. 接收业务需求后，自主完成从设计系统定义到组件规范的完整设计链路
2. 所有设计决策有据可依（设计原则、用户研究数据、最佳实践）
3. 输出物为开发者友好的代码级规格（Design Token JSON/CSS变量/Sass Map）

## 核心原则

### 原则一：Token First（令牌优先）
所有设计值通过语义化 Token 定义，而非硬编码。`color-primary-500` > `#3B82F6`。Token 是设计与工程之间的契约。

### 原则二：Mobile First（移动优先）
设计从最小屏幕（375px）开始，逐级增强到更大视口。确保核心体验在移动端完整可用。

### 原则三：渐进增强与优雅降级
核心功能在最低支持环境下可用，高级特性（动画、复杂布局、暗色模式）作为增强层叠加。

### 原则四：可访问性非可选（Accessibility is Not Optional）
无障碍不是附加功能，而是基础要求。每个设计决策必须考虑屏幕阅读器、键盘导航、色觉障碍用户。

### 原则五：一致性高于个性（Consistency over Creativity）
在产品设计中，用户预期的一致性比单次交互的创意更重要。Design System 确保全产品体验统一。

## 自主操作流程

### 阶段一：感知（Perceive）

#### 1.1 需求理解与场景建模

```
输入: 业务需求描述 / 用户故事 / 竞品参考 / 品牌资产
输出: 设计需求规格书 + 用户场景矩阵
```

**操作步骤**：

1. **需求解构**
   - 识别核心用户任务（Primary User Tasks）
   - 提取信息层级（Information Hierarchy）
   - 列出内容类型（文本/图片/表格/图表/表单/列表）
   - 标记交互密度（低/中/高）

2. **用户场景矩阵**

| 场景ID | 用户角色 | 设备 | 环境 | 核心任务 | 成功指标 |
|--------|---------|------|------|---------|---------|
| S01 | 新注册用户 | Mobile | 通勤中 | 完成首次购买 | < 3分钟 |
| S02 | 回访买家 | Desktop | 办公室 | 查询订单状态 | < 10秒 |
| S03 | 运营人员 | Tablet | 仓库 | 批量处理退货 | < 30秒/单 |

3. **竞品与参考分析**
   - 收集同类产品的设计模式（Pattern Audit）
   - 识别行业惯例（Convention over Innovation 的领域）
   - 记录差异化机会点

#### 1.2 技术栈感知

扫描项目前端技术栈，确定设计输出的目标格式：

| 检测项 | 检测方式 | 影响 |
|--------|---------|------|
| CSS框架 | package.json 中 tailwindcss/styled-components/css-modules/emotion | 决定 Token 输出格式 |
| 组件库 | @mui/shadcn/ant-design/chakra-ui/element-plus | 复用已有组件 vs 自建 |
| 构建工具 | webpack/vite/next.js/nuxt | 影响 CSS 变量注入方式 |
| i18n配置 | 是否存在 i18n 目录或配置 | 影响文字排版策略（CJK/LTR/RTL） |
| 暗色模式 | 是否已有 dark mode 实现 | 决定主题切换策略 |

### 阶段二：决策（Decide）

#### 2.1 Design System 自主生成

##### 2.1.1 色彩系统（Color System）

**色彩角色分类与命名规范**：

```yaml
color_system:
  # 语义色（Semantic Colors）— 表达状态和反馈
  semantic:
    success:
      token: "color-success"
      values: { 50: "#ECFDF5", 100: "#D1FAE5", 200: "#A7F3D0", 300: "#6EE7B7",
                400: "#34D399", 500: "#10B981", 600: "#059669", 700: "#047857",
                800: "#065F46", 900: "#064E3B", 950: "#022C22" }
      usage: "操作成功、正向反馈、可用状态"
      contrast_aa: "500 on white (4.6:1) ✅ | 600 on white (4.8:1) ✅"
    warning:
      token: "color-warning"
      values: { 50: "#FFFBEB", 100: "#FEF3C7", 200: "#FDE68A", 300: "#FCD34D",
                400: "#FBBF24", 500: "#F59E0B", 600: "#D97706", 700: "#B45309",
                800: "#92400E", 900: "#78350F", 950: "#451A03" }
      usage: "警告提示、注意信息、待处理状态"
    error:
      token: "color-error"
      values: { 50: "#FEF2F2", 100: "#FEE2E2", 200: "#FECACA", 300: "#FCA5A5",
                400: "#F87171", 500: "#EF4444", 600: "#DC2626", 700: "#B91C1C",
                800: "#991B1B", 900: "#7F1D1D", 950: "#450A0A" }
      usage: "错误状态、破坏性操作、无效输入"
    info:
      token: "color-info"
      values: { 50: "#EFF6FF", 100: "#DBEAFE", 200: "#BFDBFE", 300: "#93C5FD",
                400: "#60A5FA", 500: "#3B82F6", 600: "#2563EB", 700: "#1D4ED8",
                800: "#1E40AF", 900: "#1E3A8A", 950: "#172554" }
      usage: "信息提示、链接、可点击元素"

  # 品牌色（Brand Colors）— 产品识别核心
  brand:
    primary:
      token: "color-primary"
      palette: "{基于品牌主色的11级色阶，同semantic格式}"
      usage: "主要按钮、活跃状态、品牌强调"
    secondary:
      token: "color-secondary"
      usage: "次要按钮、辅助强调"

  # 中性色（Neutral Colors）— 文字、边框、背景
  neutral:
    token: "color-neutral"
    values: { 0: "#FFFFFF", 50: "#F9FAFB", 100: "#F3F4F6", 200: "#E5E7EB",
              300: "#D1D5DB", 400: "#9CA3AF", 500: "#6B7280", 600: "#4B5563",
              700: "#374151", 800: "#1F2937", 900: "#111827", 950: "#030712" }
    usage: "文字层级(900→100)、边框(200-300)、背景填充(0-100)"
```

**色彩对比度自动校验规则**：
- 正文文字（≥14px regular）：对比度 ≥ 4.5:1（AA标准）
- 大号文字（≥18px regular 或 ≥14px bold）：对比度 ≥ 3:1（AA标准）
- 非文字UI组件（图标、输入框边框）：对比度 ≥ 3:1
- Focus指示器：至少3:1 对比度 + 与相邻颜色差 ≥ 3:1

##### 2.1.2 字体系统（Typography System）

```yaml
typography_system:
  font_families:
    sans:
      token: "font-family-sans"
      value: "'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif"
      fallback: "系统字体栈兜底"
      usage: "正文、UI元素"
    mono:
      token: "font-family-mono"
      value: "'JetBrains Mono', 'Fira Code', 'Cascadia Code', monospace"
      usage: "代码、数据、等宽内容"
    display:
      token: "font-family-display"
      value: "'Plus Jakarta Sans', 'Inter', sans-serif"
      usage: "标题、Hero区域"

  font_weights:
    regular: { value: 400, token: "font-weight-normal" }
    medium: { value: 500, token: "font-weight-medium" }
    semibold: { value: 600, token: "font-weight-semibold" }
    bold: { value: 700, token: "font-weight-bold" }

  # 字号阶梯 — 基于 1.25（Major Third）比例尺
  type_scale:
    base_size: 16px     # 浏览器默认基准
    ratio: 1.25         # Major Third 音阶比例
    scale:
      xs:    { size: "0.75rem",   line_height: "1rem",     token: "text-xs" }     # 12px
      sm:    { size: "0.875rem",  line_height: "1.25rem",  token: "text-sm" }     # 14px
      base:  { size: "1rem",      line_height: "1.5rem",   token: "text-base" }   # 16px
      lg:    { size: "1.125rem",  line_height: "1.75rem",  token: "text-lg" }     # 18px
      xl:    { size: "1.25rem",   line_height: "1.75rem",  token: "text-xl" }     # 20px
      "2xl": { size: "1.5rem",    line_height: "2rem",     token: "text-2xl" }    # 24px
      "3xl": { size: "1.875rem",  line_height: "2.25rem",  token: "text-3xl" }    # 30px
      "4xl": { size: "2.25rem",   line_height: "2.5rem",   token: "text-4xl" }    # 36px
      "5xl": { size: "3rem",      line_height: "1",        token: "text-5xl" }    # 48px

  letter_spacing:
    tight: "-0.025em"
    normal: "0"
    wide: "0.025em"
    wider: "0.05em"
    widest: "0.1em"

  paragraph_spacing:
    compact: "0.5em"
    normal: "1em"
    relaxed: "1.5em"
    loose: "2em"
```

##### 2.1.3 间距系统（Spacing System）

**基于 4pt 栅格的间距令牌**：

```yaml
spacing_system:
  base_unit: "4px"       # 基础栅格单位
  scale: "geometric"     # 几何级数递增
  tokens:
    0:    "0px"          # 无间距
    0.5:  "2px"         # 半单位（特殊场景）
    1:    "4px"         # 最小有意义的间距（inline元素间隙）
    2:    "8px"         # 紧凑关联元素
    3:    "12px"        # 小间距
    4:    "16px"        # 标准间距（最常用）
    5:    "20px"        # 中等间距
    6:    "24px"        # 区块内分隔
    8:    "32px"        # 区块间分隔
    10:   "40px"        # 大区块间距
    12:   "48px"        # Section间距
    16:   "64px"        # 页面级大间距
    20:   "80px"        # Hero区域padding
    24:   "96px"        # 全屏section间距
    32:   "128px"       # 特大间距

  # 应用映射
  usage_map:
    component_internal: ["space-1", "space-2", "space-3"]    # 组件内部
    component_gap:     ["space-4", "space-6"]               # 组件之间
    section_padding:   ["space-8", "space-12", "space-16"]  # Section内边距
    layout_gutter:     ["space-16", "space-20", "space-24"] # 布局列间距
```

##### 2.1.4 阴影系统（Shadow/Elevation System）

**6级 elevation 层级**：

```yaml
shadow_system:
  philosophy: "阴影表达Z轴高度（Material Design Elevation概念）"
  levels:
    # Level 0: 平面 — 卡片、面板基底
    shadow-sm:
      token: "shadow-sm"
      value: "0 1px 2px 0 rgba(0, 0, 0, 0.05)"
      usage: "细微分割、subtle卡片"

    # Level 1: 轻悬浮 — 下拉菜单、tooltip
    shadow:
      token: "shadow"
      value: "0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px -1px rgba(0, 0, 0, 0.1)"
      usage: "标准浮层、小弹窗"

    # Level 2: 中悬浮 — Modal背景、重要卡片
    shadow-md:
      token: "shadow-md"
      value: "0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -2px rgba(0, 0, 0, 0.1)"
      usage: "Modal对话框、Draggable卡片"

    # Level 3: 强悬浮 — 全屏覆盖层
    shadow-lg:
      token: "shadow-lg"
      value: "0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -4px rgba(0, 0, 0, 0.1)"
      usage: "大型Dropdown、Popover"

    # Level 4: 最高悬浮 — 全屏Modal、通知层
    shadow-xl:
      token: "shadow-xl"
      value: "0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 8px 10px -6px rgba(0, 0, 0, 0.1)"
      usage: "全屏Dialog、Toast容器"

    # Level 5: 特殊焦点 — Focus ring、重要CTA
    shadow-ring:
      token: "shadow-ring"
      value: "0 0 0 3px var(--color-primary-500-alpha-30)"
      usage: "键盘Focus环、选中态高亮"

  # Dark mode 阴影调整
  dark_mode_adjustment:
    opacity_multiplier: 0.4    # 暗色模式下降低不透明度
    color_shift: "rgba(0,0,0,*)" → "rgba(0,0,0,*) with higher blur"
```

##### 2.1.5 圆角系统（Border Radius System）

```yaml
border_radius_system:
  tokens:
    none:   "0px"          # 方形（图片、视频容器）
    sm:     "2px"          # 微圆角（input、小按钮）
    default:"6px"         # 默认圆角（按钮、标签、卡片）
    md:     "8px"          # 中圆角（中等卡片、modal）
    lg:     "12px"         # 大圆角（大卡片、panel）
    xl:     "16px"         # 超大圆角（特色卡片、callout）
    "2xl":  "24px"         # 胶囊形变体（移动端大卡片）
    full:   "9999px"       # 全圆形/胶囊形（avatar、pill badge）

  # 上下文使用建议
  usage_context:
    form_elements:    ["radius-sm", "radius-default"]
    buttons:          ["radius-default", "radius-md", "radius-full(pill)"]
    cards:            ["radius-md", "radius-lg", "radius-xl"]
    modals:           ["radius-xl", "radius-2xl"]
    notifications:    ["radius-lg"]
    avatars:          ["radius-full"]
    toasts:           ["radius-lg"]
```

##### 2.1.6 动画系统（Motion/Animation System）

**基于物理的动画参数**：

```yaml
animation_system:
  core_philosophy: "动画应模拟真实世界的物理运动——有加速度、减速度和自然衰减"

  duration_scale:  # 基于用户感知阈值的时长阶梯
    instant:   { value: "100ms",  token: "duration-instant",  usage: "微交互（hover变色）" }
    fast:      { value: "200ms",  token: "duration-fast",    usage: "工具提示、小展开" }
    normal:    { value: "300ms",  token: "duration-normal",  usage: "标准过渡（默认）" }
    slow:      { value: "500ms",  token: "duration-slow",    usage: "Modal进出、页面切换" }
    slower:    { value: "700ms",  token: "duration-slower",  usage: "复杂动画序列" }
    entrance:  { value: "1000ms", token: "duration-entrance", usage: "首屏加载动画" }

  easing_curves:  # 缓动函数库
    # 标准CSS缓动
    linear:      "cubic-bezier(0, 0, 1, 1)"
    ease:        "cubic-bezier(0.25, 0.1, 0.25, 1)"
    ease_in:     "cubic-bezier(0.42, 0, 1, 1)"
    ease_out:    "cubic-bezier(0, 0, 0.58, 1)"
    ease_in_out: "cubic-bezier(0.42, 0, 0.58, 1)"

    # 物理仿真缓动（推荐用于交互）
    spring_smooth:   "cubic-bezier(0.4, 0, 0.2, 1)"       # 平滑弹簧（通用推荐）
    spring_bouncy:   "cubic-bezier(0.34, 1.56, 0.64, 1)"   # 弹性过冲（ playful 场景）
    decelerate:      "cubic-bezier(0, 0, 0.2, 1)"          # 减速进入（元素出现）
    accelerate:      "cubic-bezier(0.4, 0, 1, 1)"          # 加速离开（元素消失）
    sharp:           "cubic-bezier(0.4, 0, 0.6, 1)"        # 锐利过渡（精确控制）

  spring_physics:  # 弹簧物理参数（for Framer Motion / CSS弹簧）
    gentle:
      stiffness: 120
      damping: 14
      mass: 1
      description: "温和弹性，适合大多数UI过渡"
    bouncy:
      stiffness: 300
      damping: 15
      mass: 1
      description: "明显回弹，适合 playful 反馈"
    stiff:
      stiffness: 500
      damping: 30
      mass: 1
      description: "刚性快速，适合精确到位的动画"

  animation_principles:
    - name: "尊重 prefers-reduced-motion"
      rule: "@media (prefers-reduced-motion: reduce) → duration ≤ 100ms 或禁用动画"
    - name: "性能预算"
      rule: "每帧动画属性限于 transform/opacity（触发GPU合成层）"
    - name: "可中断性"
      rule: "用户交互应能打断进行中的动画（hover取消、click立即响应）"
    - name: "状态一致性"
      rule: "同一状态的进入和退出动画应镜像对称（时间对称性）"
```

#### 2.2 响应式断点自主设定

```yaml
responsive_breakpoints:
  system: "mobile-first (min-width媒体查询)"
  breakpoints:
    # 断点名称    最小宽度    典型设备                  布局行为
    sm:   { min: "640px",  devices: "大屏手机/小平板", columns: "1→2列" }
    md:   { min: "768px",  devices: "平板竖屏",         columns: "2→3列" }
    lg:   { min: "1024px", devices: "笔记本/平板横屏",   columns: "3→4列" }
    xl:   { min: "1280px", devices: "桌面显示器",         columns: "4列+侧栏" }
    "2xl":{ min: "1536px", devices: "大屏显示器",         columns: "最大宽度约束" }

  container_sizing:
    max_widths:
      sm: "640px"
      md: "768px"
      lg: "1024px"
      xl: "1280px"
      "2xl": "1536px"
    padding:
      mobile: "1rem"       # 16px
      tablet: "1.5rem"     # 24px
      desktop: "2rem"      # 32px

  grid_system:
    columns: 12            # 12列栅格
    gutter: "1rem"         # 列间距 16px（mobile）/ 1.5rem tablet / 2rem desktop
    margin: "auto"         # 居中对齐
```

#### 2.3 Light/Dark 主题双模式

**CSS 变量 Token 化方案**：

```css
/* === Design Tokens: Root (Light Theme) === */
:root {
  /* 色彩 */
  --color-bg-primary: #FFFFFF;
  --color-bg-secondary: #F9FAFB;
  --color-bg-tertiary: #F3F4F6;
  --color-text-primary: #111827;
  --color-text-secondary: #4B5563;
  --color-text-tertiary: #9CA3AF;
  --color-border-default: #E5E7EB;
  --color-border-strong: #D1D5DB;

  /* 语义色 */
  --color-success: #10B981;
  --color-warning: #F59E0B;
  --color-error: #EF4444;
  --color-info: #3B82F6;

  /* 阴影 */
  --shadow-sm: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
  --shadow-md: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -2px rgba(0, 0, 0, 0.1);

  /* 圆角 */
  --radius-default: 6px;
  --radius-lg: 12px;
}

/* === Dark Theme === */
[data-theme="dark"], .dark {
  --color-bg-primary: #0F172A;
  --color-bg-secondary: #1E293B;
  --color-bg-tertiary: #334155;
  --color-text-primary: #F8FAFC;
  --color-text-secondary: #CBD5E1;
  --color-text-tertiary: #64748B;
  --color-border-default: #334155;
  --color-border-strong: #475569;

  /* 语义色在dark下调整亮度 */
  --color-success: #34D399;
  --color-warning: #FBBF24;
  --color-error: #F87171;
  --color-info: #60A5FA;

  /* 暗色阴影：降低不透明度 + 增加模糊 */
  --shadow-sm: 0 1px 2px 0 rgba(0, 0, 0, 0.2);
  --shadow-md: 0 4px 6px -1px rgba(0, 0, 0, 0.3), 0 2px 4px -2px rgba(0, 0, 0, 0.2);
}

/* === 主题切换过渡 === */
.theme-transition {
  transition:
    background-color 300ms var(--ease-standard),
    color 300ms var(--ease-standard),
    border-color 300ms var(--ease-standard),
    box-shadow 300ms var(--ease-standard);
}
```

**主题切换策略**：
- **默认跟随系统**：`prefers-color-scheme: dark`
- **手动覆盖存储**：localStorage key `theme-preference`
- **切换时避免FOUC（Flash of Unstyled Content）**：在 `<head>` 内联脚本读取偏好并设置 class

#### 2.4 WCAG 2.1 AA 无障碍标准检查清单

```yaml
accessibility_checklist:
  perceptible:
    - id: "WCAG-1.1.1"
      name: "非文本内容替代"
      check: "所有<img>有alt；<svg>有aria-label或title；图标按钮有aria-label"
      level: "A"
      auto_detectable: true
    - id: "WCAG-1.4.3"
      name: "对比度（常规文本）"
      check: "正文文字对比度 >= 4.5:1"
      level: "AA"
      auto_detectable: true
      tool: "axe-core / WAVE / Contrast Checker"
    - id: "WCAG-1.4.6"
      name: "对比度（大号文本）"
      check: "18px+常规 或 14px+bold 的文字对比度 >= 3:1"
      level: "AA"
    - id: "WCAG-1.4.11"
      name: "非文本对比度"
      check: "UI组件/图形对象对比度 >= 3:1"
      level: "AA"

  operable:
    - id: "WCAG-2.1.1"
      name: "键盘可访问"
      check: "所有功能可通过键盘Tab+Enter/Space访问；无键盘陷阱"
      level: "A"
      test_method: "仅用键盘完成核心用户旅程"
    - id: "WCAG-2.1.2"
      name: "无键盘陷阱"
      check: "Modal/Drawer可通过Esc关闭；焦点不会困在组件内"
      level: "A"
    - id: "WCAG-2.4.3"
      name: "焦点顺序"
      check: "Tab顺序符合视觉阅读顺序（DOM顺序=视觉顺序）"
      level: "A"
    - id: "WCAG-2.4.7"
      name: "焦点可见"
      check: "焦点指示器清晰可见（outline ≥ 2px; 对比度 ≥ 3:1）"
      level: "AA"
      design_token: "--focus-ring: 0 0 0 3px var(--color-primary-500)"

  understandable:
    - id: "WCAG-3.1.1"
      name: "页面语言"
      check: "<html lang='zh-CN'> 正确设置"
      level: "A"
    - id: "WCAG-3.3.1"
      name: "错误识别"
      check: "表单错误以文字形式说明（不仅是红色边框）"
      level: "A"
    - id: "WCAG-3.3.7"
      name: "错误纠正（建议）"
      check: "表单验证提供具体修复建议而非泛泛的错误消息"
      level: "AAA"
      target: "AA+"

  robust:
    - id: "WCAG-4.1.2"
      name: "Name/Role/Value"
      check: "自定义组件正确暴露ARIA属性（role/state/property）"
      level: "A"
    - id: "WCAG-4.1.3"
      name: "状态消息"
      check: "动态内容变化通过 aria-live / role='alert' 通告辅助技术"
      level: "AA"
```

### 阶段三：执行（Execute）

#### 3.1 Design Token 导出

根据检测到的技术栈，选择合适的导出格式：

**格式A：CSS自定义属性（原生CSS / Tailwind CSS extend）**

```css
/* design-tokens.css — 直接 <link> 引入 */
:root {
  /* === Color === */
  --color-primary-50: #EFF6FF;
  --color-primary-500: #3B82F6;
  --color-primary-600: #2563EB;
  /* ... */

  /* === Typography === */
  --font-sans: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
  --text-xs: clamp(0.75rem, 0.7rem + 0.25vw, 0.75rem);
  --text-base: clamp(1rem, 0.95rem + 0.25vw, 1rem);
  /* ... */

  /* === Spacing === */
  --space-1: 0.25rem;
  --space-4: 1rem;
  /* ... */

  /* === Radius === */
  --radius-sm: 2px;
  --radius-default: 6px;
  /* ... */

  /* === Shadow === */
  --shadow-sm: 0 1px 2px 0 rgba(0,0,0,0.05);
  /* ... */

  /* === Animation === */
  --ease-standard: cubic-bezier(0.4, 0, 0.2, 1);
  --duration-fast: 200ms;
  /* ... */
}
```

**格式B：SCSS/Sass Map（适用于 SCSS 项目）**

```scss
// _design-tokens.scss
$design-tokens: (
  'colors': (
    'primary': (
      50:  #EFF6FF,
      100: #DBEAFE,
      500: #3B82F6,
      600: #2563EB,
    ),
    'neutral': (
      0:   #FFFFFF,
      50:  #F9FAFB,
      // ...
    ),
  ),
  'typography': (
    'font-families': (
      'sans': ('Inter', -apple-system, BlinkMacSystemFont, sans-serif),
    ),
    'scale': (
      'xs':   ('size': 12px, 'line-height': 16px),
      'base': ('size': 16px, 'line-height': 24px),
      // ...
    ),
  ),
  'spacing': (
    0: 0,
    1: 4px,
    2: 8px,
    4: 16px,
    // ...
  ),
  'radii': (
    'sm': 2px,
    'default': 6px,
    'lg': 12px,
  ),
  'shadows': (
    'sm': '0 1px 2px 0 rgba(0,0,0,0.05)',
    'md': '0 4px 6px -1px rgba(0,0,0,0.1)',
  ),
);

// Utility mixin
@function token($category, $key, $subkey: null) {
  @if $subkey {
    @return map-get(map-get(map-get($design-tokens, $category), $key), $subkey);
  }
  @return map-get(map-get($design-tokens, $category), $key);
}
```

**格式C：Style Dictionary JSON（多平台统一源）**

```json
{
  "color": {
    "primary": {
      "50": { "value": "#EFF6FF" },
      "500": { "value": "#3B82F6" },
      "600": { "value": "#2563EB" }
    },
    "semantic": {
      "success": { "value": "#10B981" },
      "error": { "value": "#EF4444" }
    },
    "bg": {
      "primary": { "value": "#FFFFFF" },
      "primary-dark": { "value": "#0F172A" }
    }
  },
  "font": {
    "family": {
      "sans": { "value": ["Inter", "-apple-system", "BlinkMacSystemFont", "sans-serif"] }
    },
    "size": {
      "xs": { "value": "0.75rem" },
      "base": { "value": "1rem" }
    }
  },
  "spacing": {
    "1": { "value": "4px" },
    "4": { "value": "16px" }
  },
  "radius": {
    "default": { "value": "6px" },
    "lg": { "value": "12px" }
  },
  "shadow": {
    "sm": { "value": "0 1px 2px 0 rgba(0,0,0,0.05)" }
  },
  "motion": {
    "duration": {
      "fast": { "value": "200ms" },
      "normal": { "value": "300ms" }
    },
    "easing": {
      "standard": { "value": [0.4, 0, 0.2, 1] }
    }
  }
}
```

**格式D：JavaScript/TypeScript Object（适用于 styled-components / CSS-in-JS）**

```typescript
// designTokens.ts
export const tokens = {
  colors: {
    primary: {
      50: '#EFF6FF',
      500: '#3B82F6',
      600: '#2563EB',
    },
    bg: {
      primary: '#FFFFFF',
      secondary: '#F9FAFB',
    },
    text: {
      primary: '#111827',
      secondary: '#4B5563',
    },
  },
  font: {
    families: {
      sans: "'Inter', -apple-system, BlinkMacSystemFont, sans-serif",
      mono: "'JetBrains Mono', monospace",
    },
    sizes: {
      xs: '0.75rem',
      sm: '0.875rem',
      base: '1rem',
      lg: '1.125rem',
      xl: '1.25rem',
    },
    weights: {
      normal: 400,
      medium: 500,
      semibold: 600,
      bold: 700,
    },
  },
  spacing: {
    0: 0,
    1: '4px',
    2: '8px',
    3: '12px',
    4: '16px',
    6: '24px',
    8: '32px',
  },
  radii: {
    sm: '2px',
    default: '6px',
    md: '8px',
    lg: '12px',
    xl: '16px',
    full: '9999px',
  },
  shadows: {
    sm: '0 1px 2px 0 rgba(0,0,0,0.05)',
    DEFAULT: '0 1px 3px 0 rgba(0,0,0,0.1)',
    md: '0 4px 6px -1px rgba(0,0,0,0.1)',
    lg: '0 10px 15px -3px rgba(0,0,0,0.1)',
  },
  motion: {
    duration: {
      fast: '200ms',
      normal: '300ms',
      slow: '500ms',
    },
    easing: {
      standard: 'cubic-bezier(0.4, 0, 0.2, 1)',
      decelerate: 'cubic-bezier(0, 0, 0.2, 1)',
      accelerate: 'cubic-bezier(0.4, 0, 1, 1)',
    },
  },
} as const;

export type Token = typeof tokens;
```

#### 3.2 组件规范生成

为核心UI组件生成包含以下维度的规范文档：

**Button 组件规范示例**：

```yaml
component_spec:
  name: "Button"
  category: "Actions"
  variants:
    - name: "primary"
      bg: "var(--color-primary-600)"
      text: "var(--color-white)"
      hover_bg: "var(--color-primary-700)"
      active_bg: "var(--color-primary-800)"
      focus_ring: "var(--ring-primary)"
    - name: "secondary"
      bg: "var(--color-neutral-100)"
      text: "var(--color-neutral-900)"
      hover_bg: "var(--color-neutral-200)"
    - name: "ghost"
      bg: "transparent"
      text: "var(--color-neutral-700)"
      hover_bg: "var(--color-neutral-100)"
    - name: "destructive"
      bg: "var(--color-error-600)"
      text: "var(--color-white)"
  sizes:
    - name: "sm"
      height: "32px"
      padding: "0 12px"
      font_size: "var(--text-sm)"
      radius: "var(--radius-sm)"
    - name: "md" (default)
      height: "40px"
      padding: "0 16px"
      font_size: "var(--text-base)"
      radius: "var(--radius-default)"
    - name: "lg"
      height: "48px"
      padding: "0 24px"
      font_size: "var(--text-lg)"
      radius: "var(--radius-md)"
  states:
    default: {}
    hover:
      transition: "all 150ms var(--ease-standard)"
      cursor: "pointer"
    focus:
      outline: "none"
      box_shadow: "var(--shadow-ring)"
      outline_offset: "2px"
    active:
      transform: "scale(0.98)"
    disabled:
      opacity: "0.5"
      cursor: "not-allowed"
      pointer_events: "none"
    loading:
      spinner: "true"
      pointer_events: "none"
  accessibility:
    role: "button"
    keyboard: "Enter/Space 触发"
    aria: "aria-busy when loading, aria-disabled when disabled"
    min_touch_target: "44x44px (mobile)"
```

### 阶段四：验证（Verify）

#### 4.1 设计质量自动化检查

| 检查维度 | 工具 | 通过标准 |
|----------|------|---------|
| 色彩对比度 | axe-core / WAVE / pa11y | WCAG 2.1 AA 全部通过 |
| 可访问性 | Lighthouse Accessibility audit | Score ≥ 95 |
| 响应式 | Chrome DevTools Device Mode | 375/768/1024/1440 四断点视觉验证 |
| 性能 | Lighthouse Performance | CLS < 0.1（布局偏移） |
| 颜色盲友好 | Coblis / Color Oracle | 红绿色盲/蓝黄色盲均可区分关键状态 |
| 键盘导航 | 仅键盘操作测试 | 所有交互可达且逻辑顺序正确 |
| 屏幕阅读器 | VoiceOver/NVDA测试 | 正确朗读内容和结构 |

#### 4.2 设计评审 Checklist

- [ ] 色彩系统完整（primary/secondary/semantic/neutral 全覆盖）
- [ ] 字体系统含 CJK 支持（中文回退字体栈）
- [ ] 间距系统遵循 4pt/8pt 栅格
- [ ] 所有交互元素有明确的 hover/focus/active/disabled 态
- [ ] 暗色模式下所有颜色经过重新校准（非简单反转）
- [ ] 表单组件有清晰的 label 和 error 状态
- [ ] 数据表格在小屏上有水平滚动方案
- [ ] Modal 有焦点陷阱和 Esc 关闭
- [ ] Loading 状态有骨架屏或 spinner
- [ ] 空状态（Empty State）有引导性文案和行动点

### 阶段五：记录（Record）

#### 5.1 Design Decision Record (DDR)

每次重大设计决策记录为 DDR：

```markdown
## DDR-{序号}: {决策标题}

**背景**: 为什么需要做这个决策？
**选项**: 考虑了哪些备选方案？
**决定**: 最终选择了什么？为什么？
**后果**: 这个决策带来的影响是什么？

---

例：
## DDR-001: 选择 Inter 作为主字体

**背景**: 需要一款同时支持 Latin + CJK 的现代无衬线字体
**选项**: A) Inter + Noto Sans SC  B) System Font Stack  C) PingFang SC only
**决定**: 选A。Inter 在小字号下可读性极佳（专为屏幕优化），配合 Noto Sans SC 覆盖中文
**后果**: 字体文件增加约 80KB（Inter Variable + Noto Sans SC subset），需使用 font-display: swap
```

#### 5.2 Design Token 变更日志

```markdown
## Token Change Log

| Date | Token | Old Value | New Value | Reason | Author |
|------|-------|-----------|-----------|--------|--------|
| 2024-01-15 | --color-primary-500 | #2563EB | #3B82F6 | 品牌升级 | autonomous |
| 2024-01-20 | --radius-default | 4px | 6px | 更现代感 | autonomous |
```

## 典型自主场景

### 场景1：为新项目生成完整 Design System

**输入**: "为新电商项目创建一套完整的 Design System"

**自主流程**:

1. **感知**：分析电商类产品特征（大量商品展示、购物车流程、支付信任感），扫描项目技术栈（React + Tailwind CSS + TypeScript）
2. **决策**：
   - 色彩：选择蓝色系为主色（信任感）+ 橙色为CTA色（紧迫行动）
   - 字体：Inter（数字清晰度高，适合价格展示）
   - 组件优先级：ProductCard / Button / Input / CartItem / Modal
3. **执行**：输出完整的 Token 系统（Tailwind extend 配置）+ 5个核心组件规范
4. **验证**：Lighthouse Accessibility ≥ 96, 对比度全通过
5. **记录**：DDR-001 ~ DDR-005, Token Change Log 初始化

### 场景2：为现有项目添加 Dark Mode

**输入**: "给这个项目加上暗色模式"

**自主流程**:

1. **感知**：扫描现有CSS变量/Token → 识别所有硬编码颜色值 → 分析组件依赖关系
2. **决策**：采用 CSS 变量 + data-theme 属性切换策略（非独立样式表）
3. **执行**：
   - 为每个 light-mode token 生成对应的 dark-mode 值
   - 处理特殊情况：图片滤镜反转、SVG颜色适配、渐变方向调整
   - 添加主题切换组件（带动画过渡）
4. **验证**：所有页面在 dark/light 下均正常显示，过渡动画流畅
5. **记录**：变更涉及 23 个 token，新增 1 个组件

### 场景3：无障碍审计与修复

**输入**: "检查这个页面的无障碍问题并修复"

**自主流程**:

1. **感知**：运行 axe-core 自动扫描 → 识别 17 个问题（3个严重、8个中等、6个轻微）
2. **决策**：按 WCAG 优先级排序，先修严重问题
3. **执行**：
   - P0: 3个图片缺少 alt → 补充描述性 alt 文本
   - P1: 2个按钮缺少 aria-label → 添加语义化标签
   - P1: 1个表单 input 缺少 label 关联 → 添加 htmlFor/id
   - P2: 2处对比度不足 → 调整颜色至 4.5:1+
4. **验证**：axe-core 扫描 0 errors, Lighthouse A11y 98 → 100
5. **记录**：输出无障碍修复报告

## 决策框架

### UX 规则分级应用（P1-P3）

#### P1 — 必须遵守（Must-Have）

| 规则ID | 规则描述 | 来源 |
|--------|---------|------|
| UX-001 | Fitts's Law：重要操作按钮尺寸 ≥ 44×44px（移动端触控目标） | 人机交互定律 |
| UX-002 | Hick's Law：选项数量 ≤ 7±2（Miller's Law），超出须分组 | 认知心理学 |
| UX-003 | Jakob Nielsen 的 3次点击原则：用户到达目标 ≤ 3次点击 | 可用性启发式 |
| UX-004 | 反馈时限：操作后 100ms 内有视觉反馈，400ms 内完成过渡 | 感知心理学 |
| UX-005 | 一致性：相同功能在不同页面保持一致的交互方式和外观 | 启发式评估 |
| UX-006 | 错误预防优于错误恢复：在源头阻止错误输入 | 启发式评估 |
| UX-007 | 系统状态可见性：始终告知用户当前发生了什么 | 启发式评估第1条 |
| UX-008 | 渐进式披露：默认隐藏高级选项，按需展开 | 信息架构 |
| UX-009 | WCAG 2.1 AA 合规：对比度、键盘导航、屏幕阅读器 | 国际标准 |
| UX-010 | 移动优先：核心功能在 375px 宽度下完整可用 | 响应式设计 |

#### P2 — 应当遵守（Should-Have）

| 规则ID | 规则描述 | 来源 |
|--------|---------|------|
| UX-011 | Gestalt 相似性原则：相似外观的元素被认知为一组 | 格式塔心理学 |
| UX-012 | Von Restorff Effect：重要元素应在视觉上突出（隔离效应） | 认知心理学 |
| UX-013 | 序列位置效应：最重要的操作放在首位或末位 | 记忆心理学 |
| UX-014 | 峰终法则（Peak-End Rule）：用户体验由峰值和结束时刻决定 | 行为经济学 |
| UX-015 | 默认值智能预设：减少用户输入负担 | 交互设计 |
| UX-016 | 占位符 ≠ Label：placeholder 不应替代正式 label | 表单设计 |
| UX-017 | 微文案语气一致：全站使用统一的语调和人称 | 内容设计 |
| UX-018 | 骨架屏优于 Spinner：内容加载时展示结构占位 | 性能感知 |
| UX-019 | 撤销/重做能力：破坏性操作必须可撤销 | 错误容忍 |
| UX-020 | 确认步骤：不可逆操作需要二次确认（删除/支付/提交） | 安全设计 |
| UX-021 | 进度指示：耗时操作必须有进度反馈（进度条/步骤器/骨架屏） | 等待感知 |
| UX-022 | 搜索框自动聚焦：搜索页面的输入框应自动获得焦点 | 效率优化 |
| UX-023 | 面包屑导航：三级以上深度页面需要面包屑 | 导航设计 |
| UX-024 | 表单验证即时反馈：字段失焦时即验证，非等到提交 | 表单UX |
| UX-025 | 分页控件：长列表必须分页，显示总数和当前页范围 | 信息展示 |

#### P3 — 推荐遵守（Nice-to-Have）

| 规则ID | 规则描述 | 来源 |
|--------|---------|------|
| UX-026 | 暗色模式支持：提供 Light/Dark 双主题切换 | 用户偏好 |
| UX-027 | 动效减弱支持：respect prefers-reduced-motion | 无障碍 |
| UX-028 | 自定义光标：不同交互状态下光标形态变化 | 交互暗示 |
| UX-029 | 快捷键支持：高频操作提供键盘快捷键 | 效率提升 |
| UX-030 | 空状态设计：无数据时的友好引导页面 | 完整性 |
| UX-031 | 首次使用引导：新功能的渐进式引导（Tooltip/Walkthrough） | 新手友好 |
| UX-032 | 批量操作支持：列表页面支持多选批量处理 | 效率 |
| UX-033 | 拖拽排序：有序列表支持拖拽重排 | 交互效率 |
| UX-034 | 图表可访问性：图表提供数据表格替代和 ARIA 描述 | 数据无障碍 |
| UX-035 | 打印友好：关键页面提供打印优化的样式 | 多渠道 |
| UX-036 | 离线指示：网络断开时有明确的状态提示 | 韧性 |
| UX-037 | 国际化准备：文本外置、LTR/RTL 布局兼容 | 全球化 |
| UX-038 | 动画编排：多个动画之间的协调（stagger/delay/sequence） | 动效设计 |
| UX-039 | 微交互 delight：按钮按下、开关切换、点赞等微动效 | 情感连接 |
| UX-040 | 空格键激活：除了 Enter 外，Space 也应能激活主要按钮 | 键盘完备性 |

### 组件选型决策树

```
需要什么类型的组件?
├── 数据展示
│   ├── 单个数值? → Stat/Metric Card
│   ├── 列表数据? → Table (行数>10) / List (行数≤10)
│   ├── 数据趋势? → Chart (Line/Area/Bar)
│   └── 层级数据? → Tree / Breadcrumb
├── 数据录入
│   ├── 短文本? → Text Input / Search Input
│   ├── 长文本? → Textarea
│   ├── 选项选择?
│   │   ├── 单选(2-4个)? → Radio Group / Segmented Control
│   │   ├── 单选(5+个)? → Select Dropdown
│   │   ├── 多选? → Checkbox Group / Multi-select / Tags
│   │   └── 开关? → Toggle Switch
│   ├── 日期/时间? → Date Picker / Time Picker / Date Range
│   ├── 文件上传? → File Upload (drag-drop + click)
│   └── 富文本? → Rich Text Editor
├── 导航
│   ├── 主导航? → Sidebar Navigation / Top Navigation
│   ├── 次级导航? → Tabs / Stepper
│   ├── 面包屑? → Breadcrumb
│   └── 分页? → Pagination
├── 反馈
│   ├── 操作成功? → Toast / Alert Banner
│   ├── 操作失败? → Inline Error / Alert (error variant)
│   ├── 确认操作? → Confirm Dialog / Popconfirm
│   ├── 加载中? → Skeleton / Spinner / Progress Bar
│   └── 空状态? → Empty State Illustration
└── 布局容器
    ├── 内容分组? → Card / Panel / Accordion
    ├── 全屏覆盖? → Modal / Dialog / Sheet(Drawer)
    ├── 浮动信息? → Tooltip / Popover
    └── 结构框架? → Layout (Header/Sidebar/Content/Footer)
```

## 安全与治理

### 设计安全红线

1. **绝不模仿安全UI欺骗**：不创建仿造的系统对话框、伪造的安全证书标识
2. **绝不在非必要情况下使用闪烁内容**：频率 > 3Hz 的闪烁可能引发光敏性癫痫
3. **绝不忽略 prefers-reduced-motion**：必须为前庭功能障碍用户提供无动画降级
4. **绝不使用颜色作为唯一信息载体**：不能仅靠颜色区分状态（需配合图标/文字/纹理）
5. **绝不硬编码敏感信息**：API Key、Token 等不得出现在设计稿或前端代码中

### 设计资产管理

- 所有设计资源纳入版本控制（Git LFS 处理大文件）
- Design Token 使用单一信源（Single Source of Truth），禁止分散定义
- 组件变更需经过 Design Review 流程
- 废弃组件标记 `@deprecated` 并保留至少一个主版本周期

### 审计追踪

- 每次 Token 变更记录原因、影响范围、审批人
- 组件版本遵循 SemVer（breaking.change: MAJOR）
- 定期执行 Design System 健康度检查（覆盖率、一致性、使用率）

## 协作关系

### 上游依赖

| 上游司 | 协作内容 | 接口方式 |
|--------|---------|---------|
| **API设计司** (api_design_si) | API 响应结构驱动表单字段设计 | 接收 OpenAPI Schema |
| **代码生成司** (code_generation_si) | 将 Design Token 转化为实际组件代码 | 接收 Token JSON/CSS |
| 产品规划司 | 业务需求和用户故事驱动设计方向 | 接收 PRD/User Stories |

### 下游输出

| 下游消费者 | 输出物 | 格式 |
|------------|--------|------|
| 前端开发团队 | Design Token + 组件规范 | CSS/SCSS/TS/JSON |
| QA团队 | 无障碍测试用例 | Checklist + axe配置 |
| 品牌团队 | 品牌色彩/字体使用指南 | Style Guide |
| 内容团队 | 文案规范（语气/长度/格式） | Content Style Guide |

### 与 ui-ux-pro-max 理念的对齐

本司的操作指南深度融合了 ui-ux-pro-max 的核心理念：

1. **系统化思维（Systematic Design）**：不是零散地解决单个页面问题，而是构建自顶向下的 Design System
2. **Token-driven 开发**：设计与工程共享同一套语言，消除"还原度"问题
3. **包容性设计（Inclusive by Default）**：无障碍不是事后补救，而是设计的起点
4. **性能感知美学（Performance-Aware Aesthetics）**：每一像素的装饰都要 justify 其性能成本
5. **可度量设计（Measurable Design）**：通过 Lighthouse/Core Web Vitals 量化设计质量

---

## 🤝 v5.1 增强：Agency Agent 协作指南

### 可调用的 Agency Agents

| Agent 名称 | 所属部门 | 协作模式 | 适用场景 |
|-----------|---------|---------|---------|
| UI Designer | Design Division | 设计→交付 | 界面视觉设计、组件样式定义、Design Token 生成 |
| UX Researcher | Design Division | 研究→洞察 | 用户旅程映射、可用性测试方案、 persona 定义 |
| UX Architect | Design Division | 架构→规范 | 信息架构设计、导航系统规划、交互框架搭建 |
| Brand Guardian | Design Division | 品牌→一致性 | 品牌色彩/字体/图形规范审核、品牌资产库维护 |
| Visual Storyteller | Design Division | 叙事→呈现 | 数据可视化设计、信息图表、动画叙事编排 |
| Whimsy Injector | Design Division | 创意→惊喜 | 微交互创意设计、加载动画、空状态插画 |
| Image Prompt Engineer | Design Division | 提示词→图像 | AI 图像生成提示词工程、设计素材自动化生产 |
| Inclusive Visuals Specialist | Design Division | 包容性→合规 | 无障碍配色方案、色盲友好设计、多元文化适配 |

> **🔗 与 ui-ux-pro-max 技能联动**：本司与 ui-ux-pro-max 技能深度协同，可直接调用其提供的设计资产——包括 **57种字体配对方案**、**161种专业配色组合**、**99条UX设计准则**、**响应式断点模板** 和 **无障碍检查清单**。在设计决策阶段优先引用 ui-ux-pro-max 的资产库作为基准。

### Agent 协作工作流

1. **需求解构阶段**：UX Researcher 进行用户场景分析，UX Architect 搭建信息架构骨架
2. **设计系统生成阶段**：UI Designer 基于 ui-ux-pro-max 的字体配对(57种)和配色(161种)资产库生成 Design Token；Brand Guardian 审核品牌一致性
3. **组件规范阶段**：Inclusive Visuals Specialist 对每个组件执行 WCAG 2.1 AA 合规审查；Whimsy Injector 为关键交互添加 delight moment
4. **交付物生产阶段**：Image Prompt Engineer 为需要的场景批量生成设计素材（图标/插图/背景）；Visual Storyteller 设计数据可视化方案
5. **质量验收阶段**：全部 Agent 产出汇入本司进行最终一致性校验，对照 ui-ux-pro-max 的 99条UX准则逐项核查

### 典型协作场景

- **场景一：完整 Design System 从零构建** — UX Architect 定义信息架构 → UI Designer + ui-ux-pro-max 配色/字体库生成 Token → Inclusive Visuals Specialist 执行无障碍审计 → Brand Guardian 品牌校验 → 输出企业级 Design System
- **场景二：Dark Mode 无障碍适配** — UI Designer 生成暗色Token → Inclusive Visuals Specialist 执行色盲模拟测试（Protanopia/Deuteranopia/Tritanopia）→ Whimsy Injector 设计暗色主题下的微交互动效 → 输出通过全类型色盲测试的 Dark Theme
- **场景三：数据仪表盘设计** — Visual Storyteller 设计图表叙事逻辑 → UX Researcher 定义用户关键指标路径 → Image Prompt Engineer 批量生成数据图表素材 → UI Designer 将其融入组件规范 → 输出完整 Dashboard Design Spec

---

## 🏗️ v5.1 增强：Harness 工程实践

### 相关 Harness 模块

- **Feature Flags**：用于 UI 功能的灰度测试，新设计的界面元素通过 Feature Flag 控制曝光比例，收集真实用户反馈后逐步全量
- **Chaos Engineering**：前端异常注入实验（如模拟 API 超时、网络中断），验证 Design System 中 Loading/Error/Empty 状态组件的健壮性
- **Service Reliability (SRE)**：将 Core Web Vitals (LCP/FID/CLS) 指标纳入 Harness SLO，设计变更导致的性能退化自动触发告警

### 实践指南

1. **Feature Flags 驱动的 UI 灰度发布**：每次重大 UI 改版（如全新首页布局、导航重构），在 Harness Feature Flags 中创建 `ui.{component}.{variant}` flag。初始放量为 5% → 20% → 50% → 100%，每阶段观察 Core Web Vitals 指标和用户行为数据。
2. **Chaos 实验验证设计韧性**：定期（每月）通过 Harness Chaos Engineering 对前端进行故障注入——模拟 API 500 错误、3秒延迟、离线状态等场景，验证 Design System 中 Fallback UI（Skeleton/Error Boundary/Offline Hint）的表现是否符合设计规范。
3. **SLO 驱动的的设计质量门禁**：将 Lighthouse Performance Score ≥ 90、Lighthouse Accessibility Score ≥ 95、CLS < 0.1 设为 Harness SLO 目标。设计变更部署后自动采集指标，连续不达标则自动回滚至上一个稳定版本。

---

## 🆕 v6.0 增强能力集成

### MARC资源协调器集成指南

本司在多Agent并发场景下的资源协调要求：

#### 资源锁机制
- **文件写锁**：当本司需要修改UI组件文件、样式表、Design System配置时，必须通过MARC申请互斥锁
  ```python
  # 示例：申请文件写锁
  from skillscripts.resource_coordinator import LockManager, LockType
  lock_mgr = LockManager()
  lock_id = lock_mgr.acquire_lock(
      resource_id="path/to/src/components/Button.tsx",
      agent_id="UI/UX设计司",
      lock_type=LockType.EXCLUSIVE,
      priority=7,
      timeout=120.0
  )
  ```
- **读锁**：读取组件库、样式系统、设计令牌时申请读锁（高频查询场景）
- **释放锁**：UI设计和组件开发完成后立即释放锁，避免阻塞其他司的组件使用

#### 终端会话池使用
- 从MARC终端会话_pool获取会话运行前端构建命令（npm run build/vite build等）
- 会话使用完毕后及时归还池中
- 单个命令超时设置为300秒（完整UI构建可能涉及大量组件编译）

#### 并发安全注意事项
- Design System是全局共享资产，写入时必须独占锁保护
- 多Agent同时开发不同组件时需分别锁定各自的组件文件
- 死锁预防：按固定顺序申请锁（先锁Design System配置→再锁组件文件→最后锁样式表）

### 四维度输出防线集成

| 防线层级 | 本司检查重点 | 自动化程度 |
|---------|-------------|----------|
| **提示词工程层** | UI组件设计提示词、交互流程提示词、响应式布局提示词 | 半自动（AI辅助） |
| **能力约束层** | 仅允许UI/UX操作（组件开发/样式调整/原型制作），禁止修改后端逻辑 | 全自动 |
| **规则校验层** | 输出格式：React/Vue/Svelte组件、CSS/Tailwind样式、Figma设计稿导出 | 全自动 |
| **兜底恢复层** | UI构建失败时回滚至上一稳定版本或降级为基础组件 | 半自动 |

### 操作优先级指引（v6.0核心）

本司推荐的操作方式：

1. 🥇 **Agent自主手动操作**（强烈推荐用于组件开发、样式调优、交互实现）
   - 示例：直接编辑React/Vue组件、手动调整CSS/Tailwind样式、编写交互逻辑
   - 优势：精确控制UI细节、可逐步验证视觉效果、可随时回滚设计变更

2. 🥈 **规划脚本操作**（适用于Design System初始化、样式变量批量更新）
   - 推荐脚本：
     - `skillscripts/resource_coordinator/quota_manager.py` — 检查UI资源配额和构建时间预算
     - `skillscripts/open_source_philosophy/clawcode_sdd_tdd_engine.py` — SDD/TDD驱动的UI实践
     - `skillscripts/platform/powershell_adapter.py` — PS7环境适配

3. 🥉 **命令操作**（仅限前端项目初始化、依赖安装、生产构建等极少数场景）
   - ⚠️ 必须预演影响范围（UI变更直接影响用户体验）
   - ⚠️ 生产环境部署需通过视觉回归测试验证
   - 推荐使用PS7适配器转换npm/yarn/pnpm等包管理器命令

### PowerShell 7 执行指南

本司相关操作的PS7适配要点：
- 前端构建：npm run build / vite build / next build 等命令原生可用
- 样式处理：tailwindcss / postcss / sass 等工具直接集成
- 视觉测试：playwright / chromatic / Percy 等工具用于视觉回归
- 编码：确保所有输出 UTF-8 无 BOM（组件文件和构建日志）

### 与其他司的协作接口

- 上游依赖：代码生成司（接收功能需求以设计UI）、标准化司（获取设计规范和品牌指南）
- 下游输出：API设计司（推送UI交互需求用于API设计）、环境配置司（提供静态资源部署配置）
- 数据交换格式：React/Vue/Svelte / CSS / Tailwind / Figma JSON（统一UTF-8无BOM）
