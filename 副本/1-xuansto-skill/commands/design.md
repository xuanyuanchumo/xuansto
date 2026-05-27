# /design 命令

## 命令描述

执行UI/UX设计流程，包括界面设计、交互设计、视觉设计和原型制作。该命令协调设计相关Agent，确保产品具有良好的用户体验。

## 使用语法

```
/design [--type=<类型>] [--style=<风格>] [--output=<输出>]
```

## 参数说明

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

```
┌─────────────────────────────────────────────────────────────┐
│                    UI/UX设计流程                            │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌──────────────┐                                          │
│  │  加载规格     │                                          │
│  └──────┬───────┘                                          │
│         │                                                   │
│         ▼                                                   │
│  ┌──────────────┐                                          │
│  │  UX研究分析   │                                          │
│  │  用户旅程     │                                          │
│  │  信息架构     │                                          │
│  └──────┬───────┘                                          │
│         │                                                   │
│         ▼                                                   │
│  ┌──────────────┐    ┌──────────────┐                      │
│  │  线框图设计   │───▶│  UI设计      │                      │
│  └──────────────┘    └──────┬───────┘                      │
│                             │                               │
│         ┌───────────────────┼───────────────────┐          │
│         │                   │                   │          │
│         ▼                   ▼                   ▼          │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐  │
│  │  视觉设计     │    │  交互设计     │    │  原型制作     │  │
│  └──────┬───────┘    └──────────────┘    └──────────────┘  │
│         │                                                   │
│         ▼                                                   │
│  ┌──────────────┐    ┌──────────────┐                      │
│  │  设计评审     │───▶│  输出产物     │                      │
│  └──────────────┘    └──────────────┘                      │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 设计阶段详情

1. **UX研究分析**
   - 用户画像定义
   - 用户旅程地图
   - 信息架构设计
   - 任务流程分析

2. **线框图设计**
   - 页面布局
   - 内容结构
   - 导航设计
   - 功能区域划分

3. **UI设计**
   - 组件设计
   - 页面设计
   - 响应式布局
   - 主题系统

4. **视觉设计**
   - 色彩系统
   - 字体排版
   - 图标设计
   - 视觉层次

5. **交互设计**
   - 交互动效
   - 状态转换
   - 反馈机制
   - 手势操作

6. **原型制作**
   - 可交互原型
   - 动效演示
   - 用户测试
   - 迭代优化

## 涉及的Agent

| Agent | 角色 | 职责 |
|-------|------|------|
| UX Designer | UX设计师 | 用户研究、信息架构、用户旅程 |
| UI Designer | UI设计师 | 界面设计、组件设计、视觉系统 |
| Frontend Stylist | 前端样式工程师 | CSS实现、响应式、主题 |
| Product Manager | 产品经理 | 需求确认、优先级 |

## 输出产物

### 设计文档结构

```
.sprint/artifacts/design/
├── ux/
│   ├── user-personas.md
│   ├── user-journey.md
│   ├── information-architecture.md
│   └── task-flows.md
├── ui/
│   ├── wireframes/
│   │   ├── login-wireframe.html
│   │   └── dashboard-wireframe.html
│   ├── mockups/
│   │   ├── login-mockup.html
│   │   └── dashboard-mockup.html
│   └── components/
│       ├── buttons.html
│       ├── forms.html
│       └── cards.html
├── visual/
│   ├── color-system.md
│   ├── typography.md
│   └── icons/
├── interactions/
│   ├── animations.css
│   └── transitions.css
└── prototypes/
    ├── desktop/
    └── mobile/
```

### user-personas.md

```markdown
# 用户画像

## 主要用户画像

### 画像1: 企业管理员

**基本信息**
- 姓名: 张明
- 年龄: 35-45岁
- 职业: IT部门经理
- 技术水平: 中等

**目标与需求**
- 快速管理团队成员
- 查看系统使用情况
- 配置权限和安全设置

**痛点**
- 复杂的配置流程
- 缺少操作指引
- 数据展示不直观

**使用场景**
- 办公室桌面端为主
- 每日使用1-2小时
- 需要快速完成任务
```

### color-system.md

```markdown
# 色彩系统

## 主色调

| 名称 | 色值 | 用途 |
|------|------|------|
| Primary | #3B82F6 | 主要按钮、链接、强调 |
| Secondary | #6366F1 | 次要操作、图标 |
| Accent | #F59E0B | 提示、警告、高亮 |

## 语义色

| 名称 | 色值 | 用途 |
|------|------|------|
| Success | #10B981 | 成功状态、确认 |
| Warning | #F59E0B | 警告状态、注意 |
| Error | #EF4444 | 错误状态、删除 |
| Info | #3B82F6 | 信息提示 |

## 中性色

| 名称 | 色值 | 用途 |
|------|------|------|
| Gray-50 | #F9FAFB | 背景色 |
| Gray-100 | #F3F4F6 | 次级背景 |
| Gray-200 | #E5E7EB | 边框 |
| Gray-300 | #D1D5DB | 分割线 |
| Gray-400 | #9CA3AF | 禁用文字 |
| Gray-500 | #6B7280 | 次要文字 |
| Gray-600 | #4B5563 | 正文 |
| Gray-700 | #374151 | 标题 |
| Gray-800 | #1F2937 | 强调文字 |
| Gray-900 | #111827 | 主标题 |

## 暗色主题

| 名称 | 亮色值 | 暗色值 |
|------|--------|--------|
| Background | #FFFFFF | #0F172A |
| Surface | #F9FAFB | #1E293B |
| Text Primary | #111827 | #F9FAFB |
| Text Secondary | #6B7280 | #94A3B8 |
```

### typography.md

```markdown
# 字体排版系统

## 字体家族

```css
--font-sans: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
--font-mono: 'JetBrains Mono', 'Fira Code', monospace;
--font-display: 'Inter', sans-serif;
```

## 字体大小

| 名称 | 大小 | 行高 | 用途 |
|------|------|------|------|
| xs | 12px | 16px | 辅助文字、标签 |
| sm | 14px | 20px | 正文小号、说明 |
| base | 16px | 24px | 正文 |
| lg | 18px | 28px | 副标题 |
| xl | 20px | 28px | 小标题 |
| 2xl | 24px | 32px | 标题 |
| 3xl | 30px | 36px | 大标题 |
| 4xl | 36px | 40px | 页面标题 |
| 5xl | 48px | 48px | 展示标题 |

## 字重

| 名称 | 值 | 用途 |
|------|-----|------|
| Normal | 400 | 正文 |
| Medium | 500 | 强调文字 |
| Semibold | 600 | 标题、按钮 |
| Bold | 700 | 重要标题 |
```

### 组件示例

```html
<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>按钮组件</title>
  <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-gray-50 p-8">
  <div class="space-y-8">
    <section>
      <h2 class="text-xl font-semibold mb-4">主要按钮</h2>
      <div class="flex gap-4 flex-wrap">
        <button class="px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors">
          默认按钮
        </button>
        <button class="px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 opacity-50 cursor-not-allowed">
          禁用按钮
        </button>
        <button class="px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 flex items-center gap-2">
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4"/>
          </svg>
          带图标按钮
        </button>
      </div>
    </section>

    <section>
      <h2 class="text-xl font-semibold mb-4">次要按钮</h2>
      <div class="flex gap-4 flex-wrap">
        <button class="px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors">
          边框按钮
        </button>
        <button class="px-4 py-2 text-blue-500 rounded-lg hover:bg-blue-50 transition-colors">
          文字按钮
        </button>
      </div>
    </section>

    <section>
      <h2 class="text-xl font-semibold mb-4">按钮尺寸</h2>
      <div class="flex gap-4 items-center flex-wrap">
        <button class="px-2 py-1 text-sm bg-blue-500 text-white rounded hover:bg-blue-600">
          小号
        </button>
        <button class="px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600">
          中号
        </button>
        <button class="px-6 py-3 text-lg bg-blue-500 text-white rounded-lg hover:bg-blue-600">
          大号
        </button>
      </div>
    </section>
  </div>
</body>
</html>
```

## 设计风格选项

### modern（现代风格）
- 简洁清晰的界面
- 适度的圆角和阴影
- 明亮的色彩搭配

### minimal（极简风格）
- 最小化视觉元素
- 大量留白
- 单色或低饱和度色彩

### glass（玻璃拟态）
- 半透明背景
- 模糊效果
- 细腻边框

### neumorphic（新拟态）
- 柔和阴影
- 凸起/凹陷效果
- 单色调设计

### brutal（野性主义）
- 粗犷的边框
- 高对比度
- 不规则布局

## 示例用法

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

## 响应式断点

| 断点名称 | 最小宽度 | 用途 |
|----------|----------|------|
| sm | 640px | 大手机 |
| md | 768px | 平板 |
| lg | 1024px | 小桌面 |
| xl | 1280px | 桌面 |
| 2xl | 1536px | 大桌面 |

## 无障碍标准

启用 `--accessibility` 时确保：

- [ ] 色彩对比度 ≥ 4.5:1（WCAG AA）
- [ ] 所有图片有替代文本
- [ ] 键盘可完全操作
- [ ] 焦点状态清晰可见
- [ ] 表单标签完整
- [ ] 屏幕阅读器兼容

## 设计评审清单

设计完成后自动检查：

- [ ] 设计系统一致性
- [ ] 响应式适配
- [ ] 暗色主题支持
- [ ] 无障碍合规
- [ ] 交互状态完整
- [ ] 加载状态设计
- [ ] 错误状态设计

## 相关命令

- `/spec` - 规格编写
- `/implement` - 开始实施
- `/sprint` - 启动完整冲刺
