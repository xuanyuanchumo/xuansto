---
name: yux_sheji_si
description: UI/UX设计司，负责界面原型、交互设计、用户体验优化。集成UXIntegration，调用ui-ux-pro-max生成设计系统和验证UI代码。
---
# UI/UX设计司技能指令

## 职责
- 用户界面原型设计与迭代
- 交互模式设计与动效规划
- 用户体验优化与可用性评估
- UXIntegration集成：调用ui-ux-pro-max生成设计系统
- 设计规范制定与UI组件库管理

## UXIntegration集成

### 设计系统生成流程

```
需求分析 → UXIntegration.generate_design_system()
         → 色彩体系 / 字体层级 / 间距网格
         → 组件规范 / 交互模式
         → Design Token输出
         ↓
    UI代码实现 → UXIntegration.validate_ui_code()
               → 一致性检查 / 可访问性审查
               → 响应式验证 / 性能评估
               ↓
           设计评审反馈闭环
```

### ui-ux-pro-max调用接口

```yaml
ux_integration_apis:
  generate_design_system:
    input:
      brand_guidelines: "品牌指南"
      user_research: "用户研究结果"
      tech_constraints: "技术约束(框架/平台)"
    output:
      design_tokens: "Design Token JSON"
      color_palette: "色彩方案"
      typography_scale: "字体层级"
      spacing_system: "间距系统"
      component_specs: "组件规格文档"

  validate_ui_code:
    input:
      ui_code_path: "UI源码路径"
      design_spec_path: "设计规格路径"
    output:
      consistency_report: "一致性报告"
      accessibility_score: "可访问性评分"
      responsive_issues: "响应式问题列表"
      performance_metrics: "性能指标"
```

## 设计规范体系

### Design Token 定义

```yaml
design_tokens:
  colors:
    primary:
      50: "#eff6ff"
      100: "#dbeafe"
      500: "#3b82f6"
      600: "#2563eb"
      700: "#1d4ed8"
      900: "#1e3a8a"
    semantic:
      success: "#22c55e"
      warning: "#f59e0b"
      error: "#ef4444"
      info: "#3b82f6"

  typography:
    font_family:
      sans: "Inter, system-ui, sans-serif"
      mono: "JetBrains Mono, monospace"
    scale:
      xs: ["12px", "16px", "-0.01em"]
      sm: ["14px", "20px", "-0.01em"]
      base: ["16px", "24px", "-0.01em"]
      lg: ["18px", "28px", "-0.025em"]
      xl: ["20px", "28px", "-0.025em"]

  spacing:
    scale: [0, 4, 8, 12, 16, 24, 32, 48, 64, 96, 128]
    unit: "px"

  breakpoints:
    sm: "640px"
    md: "768px"
    lg: "1024px"
    xl: "1280px"
    "2xl": "1536px"

  radii:
    none: "0px"
    sm: "4px"
    md: "8px"
    lg: "12px"
    full: "9999px"

  shadows:
    sm: "0 1px 2px rgba(0,0,0,0.05)"
    md: "0 4px 6px rgba(0,0,0,0.07)"
    lg: "0 10px 15px rgba(0,0,0,0.1)"
```

## 交互设计原则

### 核心原则

| 原则 | 描述 | 度量方式 |
|------|------|----------|
| 清晰性 | 用户能理解当前状态和可用操作 | 任务完成率 |
| 效率性 | 最少步骤完成目标 | 操作次数/任务时间 |
| 容错性 | 错误可恢复且提示友好 | 错误恢复率 |
| 一致性 | 相似功能有相似交互 | 模式一致性得分 |
| 可访问性 | 所有用户都能使用 | WCAG合规度 |

### 交互模式库

```yaml
interaction_patterns:
  navigation:
    - top_nav: "顶部导航栏"
    - sidebar: "侧边导航"
    - tabs: "标签页切换"
    - breadcrumbs: "面包屑导航"

  data_entry:
    - form_wizard: "分步表单"
    - inline_edit: "行内编辑"
    - bulk_actions: "批量操作"
    - search_filter: "搜索筛选组合"

  feedback:
    - toast_notification: "轻量通知"
    - modal_dialog: "模态对话框"
    - confirmation: "确认操作"
    - progress_indicator: "进度指示"

  data_display:
    - data_table: "数据表格"
    - card_grid: "卡片网格"
    - list_view: "列表视图"
    - dashboard: "仪表盘"
```

## 工作流程

```
1. 接收UI/UX设计需求
2. 收集用户研究和业务约束
3. 调用UXIntegration生成初始设计系统
4. 设计信息架构和页面流程
5. 制作低保真原型
6. 内部评审和迭代
7. 产出高保真设计稿
8. 调用UXIntegration验证UI代码一致性
9. 可用性测试（如适用）
10. 输出设计交付物
11. 将关键设计决策记录到DecisionLog
```

## 协同接口

| 接口 | 描述 | 调用方 |
|------|------|--------|
| `design_system` | 生成设计系统 | 项目启动/重构 |
| `validate_ui` | 验证UI代码 | 开发阶段 |
| `prototype` | 创建原型 | 需求确认 |
| `review_design` | 设计评审 | 定期/里程碑 |
