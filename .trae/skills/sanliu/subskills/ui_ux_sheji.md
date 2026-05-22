---
name: ui_ux_sheji
description: UI/UX设计指导，包含设计原则、交互设计指南和组件设计规范。
---
# UI/UX设计指导

## UI设计原则

### 1. 一致性原则
- **视觉一致性**：保持颜色、字体、图标、间距等视觉元素在整个应用中的一致使用
- **交互一致性**：相同类型的操作应具有相同的交互方式和反馈
- **语言一致性**：使用统一的术语和表达方式，避免用户困惑
- **平台一致性**：遵循各平台的设计规范（iOS Human Interface Guidelines、Material Design等）

### 2. 简洁性原则
- **减少认知负担**：每屏只展示必要信息，避免信息过载
- **简化操作流程**：用最少的步骤完成用户目标
- **清晰的视觉层次**：通过大小、颜色、位置建立信息优先级
- **留白的合理运用**：适当留白提升可读性和美观度

### 3. 可访问性原则
- **色彩对比度**：确保文本与背景的对比度符合WCAG标准（至少4.5:1）
- **字体大小**：正文不小于14px，提供字体缩放选项
- **触控目标**：可点击区域不小于44×44像素
- **辅助技术支持**：支持屏幕阅读器、键盘导航等

### 4. 反馈性原则
- **即时反馈**：用户操作后立即给予视觉或触觉反馈
- **状态可见**：清晰展示系统当前状态（加载中、成功、失败等）
- **进度指示**：长时间操作提供进度反馈
- **错误提示**：友好的错误信息，并提供解决方案

### 5. 美观性原则
- **视觉平衡**：元素布局和谐，避免视觉偏重
- **品牌一致性**：设计风格与品牌形象相符
- **细节打磨**：注重图标、动画、过渡等细节
- **情感化设计**：通过设计传递品牌温度和个性

---

## UX交互设计指南

### 1. 导航设计
- **清晰的导航结构**：用户应随时知道自己在哪里、可以去哪里
- **面包屑导航**：多层级结构中提供返回路径
- **底部导航**：移动端主要功能入口，不超过5个
- **侧边导航**：桌面端复杂系统的导航方案
- **搜索功能**：内容型应用必备，支持模糊搜索和筛选

### 2. 表单设计
- **标签清晰**：每个字段都有明确标签
- **输入验证**：实时验证，错误提示具体明确
- **默认值和占位符**：提供输入示例和引导
- **分组和分步**：长表单分组展示或分步完成
- **保存机制**：支持草稿保存，防止数据丢失

### 3. 列表与数据展示
- **分页与加载**：大数据量采用分页或无限滚动
- **排序与筛选**：提供多种排序和筛选方式
- **空状态设计**：无数据时展示友好提示和引导
- **数据可视化**：复杂数据使用图表展示

### 4. 操作与确认
- **危险操作确认**：删除等不可逆操作需二次确认
- **撤销机制**：支持操作撤销，提供容错空间
- **批量操作**：支持多选和批量处理
- **快捷操作**：常用操作提供快捷入口

### 5. 动效设计
- **过渡动画**：页面切换使用平滑过渡（200-400ms）
- **微交互**：按钮点击、开关切换等微动效
- **加载动画**：缓解用户等待焦虑
- **引导动画**：新功能引导和教学动画
- **动效原则**：自然、流畅、有意义，避免过度使用

### 6. 响应式设计
- **断点设置**：
  - 移动端：320px - 767px
  - 平板：768px - 1023px
  - 桌面：1024px - 1439px
  - 大屏：1440px+
- **弹性布局**：使用相对单位和弹性盒子
- **图片适配**：响应式图片，支持不同分辨率
- **触摸优化**：移动端优化触摸交互

---

## 组件设计规范

### 1. 按钮组件
- **主要按钮**：用于主要操作，使用品牌主色
- **次要按钮**：用于次要操作，使用边框或浅色背景
- **文字按钮**：用于低优先级操作
- **图标按钮**：用于工具栏等空间受限场景
- **禁用状态**：灰色显示，不可点击
- **加载状态**：显示加载指示器

**尺寸规范**：
| 尺寸 | 高度 | 内边距 | 字号 |
|------|------|--------|------|
| 小 | 28px | 8px 12px | 12px |
| 中 | 36px | 12px 16px | 14px |
| 大 | 44px | 16px 24px | 16px |

### 2. 输入框组件
- **文本输入框**：单行文本输入
- **文本域**：多行文本输入
- **搜索框**：带搜索图标的输入框
- **密码框**：支持密码显示/隐藏切换
- **状态**：默认、聚焦、禁用、错误、成功

**规范**：
- 高度：36px（标准）、44px（大）
- 圆角：4px
- 边框：1px solid，聚焦时2px
- 标签位置：顶部或左侧

### 3. 选择组件
- **单选框**：互斥选项，最多6个
- **复选框**：多选场景
- **开关**：二元状态切换
- **下拉选择**：选项超过6个时使用
- **级联选择**：多层级数据选择

### 4. 反馈组件
- **Toast提示**：轻量级反馈，2-3秒自动消失
- **对话框**：重要信息确认，需用户操作关闭
- **抽屉**：侧滑面板，展示详情或表单
- **气泡确认**：轻量级确认操作
- **通知**：系统消息推送

### 5. 数据展示组件
- **表格**：结构化数据展示，支持排序、筛选、分页
- **卡片**：信息聚合展示
- **列表**：同质数据列表
- **标签**：分类和状态标记
- **徽标**：数量或状态提示

### 6. 导航组件
- **顶部导航栏**：品牌标识、主要导航、用户操作
- **底部导航**：移动端主要功能入口
- **标签页**：内容分类切换
- **步骤条**：流程进度展示
- **面包屑**：层级路径展示

---

## 设计工具推荐

### 原型设计
- **Figma**：协作设计首选，支持实时协作和组件库
- **Sketch**：macOS平台经典设计工具
- **Adobe XD**：Adobe生态，支持语音原型
- **Axure RP**：高保真交互原型

### UI设计
- **Figma**：全功能设计工具
- **Sketch**：macOS平台UI设计
- **Adobe Illustrator**：矢量图形设计
- **Framer**：交互动效设计

### 协作与交付
- **Zeplin**：设计稿标注和交付
- **蓝湖**：设计协作平台
- **InVision**：原型分享和协作
- **墨刀**：国产原型设计工具

### 图标与资源
- **Iconfont**：阿里巴巴图标库
- **Font Awesome**：图标字体库
- **Undraw**：免费插画资源
- **Dribbble**：设计灵感平台

### 用户研究
- **Maze**：用户测试平台
- **Hotjar**：用户行为分析
- **UserTesting**：远程用户测试
- **问卷星**：问卷调查工具

---

## 设计评审标准

### 视觉评审
- [ ] 设计是否符合品牌规范
- [ ] 颜色使用是否一致且符合无障碍标准
- [ ] 字体层级是否清晰
- [ ] 间距是否遵循栅格系统
- [ ] 图标风格是否统一
- [ ] 视觉层次是否分明

### 交互评审
- [ ] 交互流程是否顺畅
- [ ] 操作反馈是否及时明确
- [ ] 错误处理是否友好
- [ ] 是否支持键盘操作
- [ ] 加载状态是否合理
- [ ] 动效是否自然流畅

### 可用性评审
- [ ] 是否符合用户心智模型
- [ ] 学习成本是否足够低
- [ ] 操作路径是否最短
- [ ] 信息架构是否合理
- [ ] 是否有明确的引导
- [ ] 是否支持撤销操作

### 响应式评审
- [ ] 各断点布局是否合理
- [ ] 移动端交互是否优化
- [ ] 图片是否自适应
- [ ] 文字是否可读
- [ ] 触控目标是否足够大

### 可访问性评审
- [ ] 色彩对比度是否达标
- [ ] 是否支持屏幕阅读器
- [ ] 是否支持键盘导航
- [ ] 焦点状态是否可见
- [ ] 表单是否有关联标签
- [ ] 是否有足够的操作时间

### 性能评审
- [ ] 图片是否优化压缩
- [ ] 图标是否使用SVG或字体
- [ ] 动画是否影响性能
- [ ] 首屏加载是否优化
- [ ] 是否使用懒加载

---

## ui-ux-pro-max 集成指南

### 集成概述

ui-ux-pro-max 是全面的 UI/UX 设计智能技能，包含 50+ 风格、161 色彩调色板、57 字体配对、161 产品类型、99 UX 指南和 25 图表类型。在 UI/UX 设计任务中，应调用此技能获得专业设计支持。

### 集成流程

```
识别UI/UX设计需求
    ↓
[1] 设计需求分析
    ↓
[2] 调用 ui-ux-pro-max 进行设计
    ↓
[3] UI 校验流程
    ↓
[4] 设计结果集成
    ↓
[5] 生成 UI 校验报告
    ↓
记录设计日志
```

### 触发条件

| 触发场景 | 负责部门 | 优先级 | 说明 |
|----------|----------|--------|------|
| 需要设计新页面 | 工部 | 高 | 落地页、仪表板、管理后台等 |
| 创建/重构UI组件 | 工部 | 高 | 按钮、表单、表格、图表等 |
| 选择设计系统 | 礼部 | 高 | 配色、字体、间距标准 |
| UI代码审查 | 兵部 | 中 | 用户体验、可访问性检查 |
| 响应式设计 | 工部 | 中 | 多设备适配设计 |
| 动效设计 | 工部 | 低 | 页面过渡、微交互 |

### 调用流程

#### 1. 设计系统生成流程

```bash
# 步骤1: 分析设计需求
调用 ui-ux-pro-max/SKILL.md --action=analyze-design-requirements \
  --project-type="SaaS|电商|企业官网" \
  --target-platform="web|mobile|desktop" \
  --brand-guidelines="品牌规范路径"

# 步骤2: 生成设计系统
调用 ui-ux-pro-max/SKILL.md --action=generate-design-system \
  --style="modern|minimal|corporate" \
  --color-palette="primary:#1890ff,secondary:#52c41a" \
  --typography="system-ui,Inter" \
  --output-format="json|css|scss"

# 步骤3: 导出设计令牌
调用 ui-ux-pro-max/SKILL.md --action=export-design-tokens \
  --design-system-path="design-system.json" \
  --formats="css,scss,json"
```

## 2. 组件设计流程

```bash
# 步骤1: 组件需求分析
调用 ui-ux-pro-max/SKILL.md --action=analyze-component \
  --component-type="button|form|table|modal" \
  --usage-context="使用场景描述" \
  --accessibility-level="AA|AAA"

# 步骤2: 设计组件
调用 ui-ux-pro-max/SKILL.md --action=design-component \
  --component-spec="component-spec.json" \
  --tech-stack="React|Vue|Tailwind" \
  --include-states="default,hover,active,disabled"

# 步骤3: 生成组件代码
调用 ui-ux-pro-max/SKILL.md --action=generate-component-code \
  --design-file="component-design.json" \
  --framework="React" \
  --include-tests=true
```

## 3. 页面设计流程

```bash
# 步骤1: 页面结构规划
调用 ui-ux-pro-max/SKILL.md --action=plan-page-structure \
  --page-type="landing|dashboard|detail" \
  --content-requirements="内容需求描述" \
  --user-flow="用户流程描述"

# 步骤2: 设计页面布局
调用 ui-ux-pro-max/SKILL.md --action=design-layout \
  --page-structure="page-structure.json" \
  --responsive-breakpoints="sm,md,lg,xl" \
  --grid-system="12-column"

# 步骤3: 生成页面代码
调用 ui-ux-pro-max/SKILL.md --action=generate-page \
  --layout-design="layout.json" \
  --tech-stack="Next.js+Tailwind" \
  --include-animations=true
```

## UI 校验流程

#### 校验检查清单

| 校验项 | 检查内容 | 通过标准 | 校验工具 |
|--------|----------|----------|----------|
| 视觉一致性 | 颜色、字体、间距统一 | 符合设计系统 | ui-ux-pro-max |
| 可访问性 | WCAG 2.1 合规性 | 达到 AA 级 | 可访问性检查器 |
| 响应式设计 | 各断点显示正常 | 无布局错乱 | 响应式测试 |
| 交互完整性 | 所有交互状态覆盖 | 状态完整 | 交互测试 |
| 性能指标 | 加载时间、渲染性能 | 符合性能预算 | Lighthouse |
| 代码质量 | 组件化、可维护性 | 通过代码审查 | ESLint + 人工 |

#### 校验执行命令

```bash
# 完整 UI 校验
调用 ui-ux-pro-max/SKILL.md --action=validate-ui \
  --target-path="src/components/" \
  --validation-type="comprehensive" \
  --check-accessibility=true \
  --check-responsiveness=true \
  --check-performance=true \
  --output-report="ui-validation-report.json"

# 可访问性专项校验
调用 ui-ux-pro-max/SKILL.md --action=validate-accessibility \
  --target-path="src/pages/" \
  --wcag-level="AA" \
  --check-color-contrast=true \
  --check-keyboard-navigation=true \
  --check-screen-reader=true

# 设计系统一致性校验
调用 ui-ux-pro-max/SKILL.md --action=validate-design-system \
  --design-tokens="design-tokens.json" \
  --code-path="src/" \
  --check-colors=true \
  --check-typography=true \
  --check-spacing=true
```

## 集成调用示例

#### 示例1: 设计新页面

```bash
#!/bin/bash
# scripts/design_new_page.sh

PAGE_NAME="dashboard"
PROJECT_TYPE="SaaS"
TECH_STACK="React+Tailwind"

echo "[1/6] 分析设计需求..."
调用 ui-ux-pro-max/SKILL.md --action=analyze-design-requirements \
  --project-type="${PROJECT_TYPE}" \
  --target-platform="web" \
  --page-purpose="数据展示仪表板"

echo "[2/6] 生成设计系统..."
调用 ui-ux-pro-max/SKILL.md --action=generate-design-system \
  --style="modern" \
  --primary-color="#1890ff" \
  --secondary-color="#52c41a" \
  --output-path="design/${PAGE_NAME}-design-system.json"

echo "[3/6] 设计页面布局..."
调用 ui-ux-pro-max/SKILL.md --action=design-layout \
  --page-type="dashboard" \
  --widgets="stats,cards,charts,tables" \
  --responsive-breakpoints="sm,md,lg,xl" \
  --output-path="design/${PAGE_NAME}-layout.json"

echo "[4/6] 生成页面代码..."
调用 ui-ux-pro-max/SKILL.md --action=generate-page \
  --layout-design="design/${PAGE_NAME}-layout.json" \
  --design-system="design/${PAGE_NAME}-design-system.json" \
  --tech-stack="${TECH_STACK}" \
  --output-path="src/pages/${PAGE_NAME}.tsx"

echo "[5/6] 执行 UI 校验..."
调用 ui-ux-pro-max/SKILL.md --action=validate-ui \
  --target-path="src/pages/${PAGE_NAME}.tsx" \
  --validation-type="comprehensive" \
  --output-report="reports/${PAGE_NAME}-ui-validation.json"

echo "[6/6] 生成设计文档..."
调用 ui-ux-pro-max/SKILL.md --action=generate-design-doc \
  --page-path="src/pages/${PAGE_NAME}.tsx" \
  --design-system="design/${PAGE_NAME}-design-system.json" \
  --output-path="docs/design/${PAGE_NAME}-design.md"

echo "页面设计完成: ${PAGE_NAME}"
```

## 示例2: 组件设计与实现

```bash
#!/bin/bash
# scripts/design_component.sh

COMPONENT_NAME="DataTable"
COMPONENT_TYPE="table"

echo "[1/5] 分析组件需求..."
调用 ui-ux-pro-max/SKILL.md --action=analyze-component \
  --component-type="${COMPONENT_TYPE}" \
  --features="sort,filter,pagination,selection" \
  --data-density="comfortable"

echo "[2/5] 设计组件..."
调用 ui-ux-pro-max/SKILL.md --action=design-component \
  --component-name="${COMPONENT_NAME}" \
  --states="default,hover,active,disabled,loading" \
  --variants="default,compact,striped" \
  --output-path="design/${COMPONENT_NAME}-design.json"

echo "[3/5] 生成组件代码..."
调用 ui-ux-pro-max/SKILL.md --action=generate-component-code \
  --design-file="design/${COMPONENT_NAME}-design.json" \
  --framework="React" \
  --styling="Tailwind" \
  --include-tests=true \
  --output-path="src/components/${COMPONENT_NAME}/"

echo "[4/5] 组件可访问性校验..."
调用 ui-ux-pro-max/SKILL.md --action=validate-accessibility \
  --target-path="src/components/${COMPONENT_NAME}/" \
  --wcag-level="AA" \
  --focus-on="keyboard-navigation,screen-reader"

echo "[5/5] 生成组件文档..."
调用 ui-ux-pro-max/SKILL.md --action=generate-component-doc \
  --component-path="src/components/${COMPONENT_NAME}/" \
  --output-path="docs/components/${COMPONENT_NAME}.md"

echo "组件设计完成: ${COMPONENT_NAME}"
```

## 示例3: UI 代码审查

```bash
#!/bin/bash
# scripts/ui_code_review.sh

TARGET_PATH=${1:-"src/"}

echo "[1/4] 执行设计系统一致性检查..."
调用 ui-ux-pro-max/SKILL.md --action=validate-design-system \
  --design-tokens="design-tokens.json" \
  --code-path="${TARGET_PATH}" \
  --output-report="reports/design-system-consistency.json"

echo "[2/4] 执行可访问性检查..."
调用 ui-ux-pro-max/SKILL.md --action=validate-accessibility \
  --target-path="${TARGET_PATH}" \
  --wcag-level="AA" \
  --output-report="reports/accessibility-check.json"

echo "[3/4] 执行响应式检查..."
调用 ui-ux-pro-max/SKILL.md --action=validate-responsiveness \
  --target-path="${TARGET_PATH}" \
  --breakpoints="320,768,1024,1440" \
  --output-report="reports/responsive-check.json"

echo "[4/4] 生成综合审查报告..."
调用 ui-ux-pro-max/SKILL.md --action=generate-review-report \
  --reports="reports/design-system-consistency.json,reports/accessibility-check.json,reports/responsive-check.json" \
  --output-path="reports/ui-code-review.md"

echo "UI 代码审查完成"
```

## 错误处理机制

| 错误类型 | 错误描述 | 处理策略 | 重试机制 |
|----------|----------|----------|----------|
| 设计需求不明确 | 设计需求描述模糊 | 返回补充需求信息 | 人工确认后重试 |
| 设计系统生成失败 | 设计令牌生成错误 | 检查输入参数 | 自动重试3次 |
| 组件生成失败 | 代码生成出错 | 检查设计文件格式 | 手动修复后重试 |
| 校验失败 | UI 校验发现问题 | 记录问题列表 | 修复后重新校验 |
| 导出失败 | 设计资源导出错误 | 检查输出路径 | 自动重试3次 |

**错误处理示例代码：**

```bash
# 带错误处理的 UI 设计
function design_with_retry() {
    local page_name=$1
    local max_retries=3
    local retry_count=0
    
    while [ $retry_count -lt $max_retries ]; do
        echo "尝试设计页面: ${page_name} (第 $((retry_count + 1)) 次)"
        
        if 调用 ui-ux-pro-max/SKILL.md --action=generate-page \
            --page-name="${page_name}" \
            --output-path="src/pages/"; then
            echo "页面设计成功"
            return 0
        else
            retry_count=$((retry_count + 1))
            echo "设计失败，${retry_count}秒后重试..."
            sleep $retry_count
        fi
    done
    
    echo "错误: 页面设计失败，已达到最大重试次数"
    # 记录错误日志
    log_error "ui_design_failed" "${page_name}"
    return 1
}
```

## 日志记录规范

**UI 集成日志格式：**

```json
{
  "log_id": "UI-DESIGN-001",
  "timestamp": "2024-01-01T00:00:00Z",
  "operation": "design-page|design-component|validate-ui",
  "page_component_name": "页面或组件名称",
  "project_type": "SaaS|电商|企业官网",
  "tech_stack": "React+Tailwind",
  "requesting_department": "工部|礼部",
  "trigger_context": "触发上下文描述",
  "execution_steps": [
    {
      "step": 1,
      "action": "analyze-design-requirements",
      "status": "success|failure",
      "duration_ms": 5000,
      "output_summary": "步骤输出摘要"
    }
  ],
  "design_outputs": {
    "design_system": "design-system.json",
    "layout": "layout.json",
    "component_code": "Component.tsx",
    "styles": "Component.module.css"
  },
  "validation_results": {
    "accessibility_score": 0.95,
    "design_consistency_score": 0.98,
    "responsive_score": 1.0,
    "issues_found": 2,
    "issues_fixed": 2
  },
  "final_result": {
    "status": "success|failure|partial",
    "artifacts": ["设计文件列表"],
    "documentation": "design-doc.md"
  },
  "errors": [
    {
      "error_type": "类型",
      "error_message": "错误信息",
      "recovery_action": "恢复操作"
    }
  ],
  "performance_metrics": {
    "total_duration_ms": 120000,
    "design_phase_ms": 60000,
    "validation_phase_ms": 30000,
    "documentation_phase_ms": 30000
  }
}
```

**日志记录命令：**

```bash
# 记录 UI 集成日志
调用 ui_ux_sheji.md --action=log-ui-integration \
  --log-data="logs/ui_integration.json" \
  --log-level="info|warning|error"

# 查询 UI 设计历史
调用 ui_ux_sheji.md --action=query-ui-logs \
  --project-type="项目类型" \
  --date-range="2024-01-01,2024-01-31"

# 生成 UI 设计统计报告
调用 ui_ux_sheji.md --action=generate-ui-stats \
  --period="monthly" \
  --output-path="reports/ui-stats.md"
```

## 技术栈支持

ui-ux-pro-max 支持以下技术栈：

| 技术栈 | 支持程度 | 适用场景 |
|--------|----------|----------|
| React | ⭐⭐⭐⭐⭐ | Web 应用 |
| Next.js | ⭐⭐⭐⭐⭐ | SSR/SSG 应用 |
| Vue | ⭐⭐⭐⭐⭐ | Web 应用 |
| Svelte | ⭐⭐⭐⭐ | 轻量级应用 |
| Tailwind CSS | ⭐⭐⭐⭐⭐ | 原子化 CSS |
| shadcn/ui | ⭐⭐⭐⭐⭐ | 组件库 |
| React Native | ⭐⭐⭐⭐ | 移动应用 |
| Flutter | ⭐⭐⭐⭐ | 跨平台移动应用 |
| SwiftUI | ⭐⭐⭐ | iOS 原生应用 |
| HTML/CSS | ⭐⭐⭐⭐⭐ | 静态页面 |

### 设计资源输出

调用 ui-ux-pro-max 后可获得以下设计资源：

1. **设计系统文件**
   - `design-tokens.json` - 设计令牌
   - `color-palette.json` - 色彩系统
   - `typography.json` - 字体系统
   - `spacing.json` - 间距系统

2. **组件设计文件**
   - `component-design.json` - 组件设计规范
   - `component-states.json` - 组件状态定义
   - `component-variants.json` - 组件变体定义

3. **页面设计文件**
   - `page-layout.json` - 页面布局
   - `responsive-layouts.json` - 响应式布局
   - `animations.json` - 动画定义

4. **代码文件**
   - `*.tsx/*.vue` - 组件代码
   - `*.module.css/*.scss` - 样式文件
   - `*.test.tsx` - 测试文件

5. **文档文件**
   - `design-doc.md` - 设计文档
   - `component-doc.md` - 组件文档
   - `usage-guide.md` - 使用指南
