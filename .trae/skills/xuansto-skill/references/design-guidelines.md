# 设计指南参考文档
> 版本: 1.9.0 | 更新日期: 2026-04-28 | 编码: UTF-8 | 行尾: LF

## 目录

- [设计系统](#设计系统)
- [组件设计](#组件设计)
- [响应式设计](#响应式设计)
- [可访问性设计](#可访问性设计)
- [设计审查清单](#设计审查清单)
- [参考资源](#参考资源)

## 设计系统

### 设计系统概述

设计系统是一套完整的、可复用的设计语言和组件库，它确保产品在不同平台和团队之间保持一致的视觉和交互体验。

### 设计系统架构

```
┌─────────────────────────────────────────────────────────────┐
│                      设计系统架构                            │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │                   设计原则层                         │   │
│  │   品牌价值 │ 设计理念 │ 用户体验目标               │   │
│  └─────────────────────────────────────────────────────┘   │
│                           │                                 │
│  ┌─────────────────────────────────────────────────────┐   │
│  │                   设计基础层                         │   │
│  │   颜色 │ 字体 │ 间距 │ 图标 │ 动效 │ 布局          │   │
│  └─────────────────────────────────────────────────────┘   │
│                           │                                 │
│  ┌─────────────────────────────────────────────────────┐   │
│  │                   组件层                             │   │
│  │   基础组件 │ 复合组件 │ 业务组件 │ 模板            │   │
│  └─────────────────────────────────────────────────────┘   │
│                           │                                 │
│  ┌─────────────────────────────────────────────────────┐   │
│  │                   文档层                             │   │
│  │   使用指南 │ 最佳实践 │ 示例代码 │ 设计规范        │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 设计令牌 (Design Tokens)

#### 颜色令牌

```json
{
  "color": {
    "brand": {
      "primary": {
        "value": "#0066CC",
        "description": "品牌主色"
      },
      "secondary": {
        "value": "#FF6600",
        "description": "品牌辅色"
      }
    },
    "semantic": {
      "success": {
        "value": "#28A745",
        "description": "成功状态"
      },
      "warning": {
        "value": "#FFC107",
        "description": "警告状态"
      },
      "error": {
        "value": "#DC3545",
        "description": "错误状态"
      },
      "info": {
        "value": "#17A2B8",
        "description": "信息状态"
      }
    },
    "neutral": {
      "gray-50": "#F9FAFB",
      "gray-100": "#F3F4F6",
      "gray-200": "#E5E7EB",
      "gray-300": "#D1D5DB",
      "gray-400": "#9CA3AF",
      "gray-500": "#6B7280",
      "gray-600": "#4B5563",
      "gray-700": "#374151",
      "gray-800": "#1F2937",
      "gray-900": "#111827"
    }
  }
}
```

#### 间距令牌

```json
{
  "spacing": {
    "0": { "value": "0", "description": "无间距" },
    "1": { "value": "4px", "description": "极小间距" },
    "2": { "value": "8px", "description": "小间距" },
    "3": { "value": "12px", "description": "中小间距" },
    "4": { "value": "16px", "description": "中间距" },
    "5": { "value": "20px", "description": "中大间距" },
    "6": { "value": "24px", "description": "大间距" },
    "8": { "value": "32px", "description": "较大间距" },
    "10": { "value": "40px", "description": "大间距" },
    "12": { "value": "48px", "description": "超大间距" },
    "16": { "value": "64px", "description": "极大间距" }
  }
}
```

#### 字体令牌

```json
{
  "typography": {
    "fontFamily": {
      "primary": {
        "value": "'Inter', -apple-system, BlinkMacSystemFont, sans-serif",
        "description": "主字体"
      },
      "monospace": {
        "value": "'Fira Code', 'Consolas', monospace",
        "description": "等宽字体"
      }
    },
    "fontSize": {
      "xs": { "value": "12px", "lineHeight": "16px" },
      "sm": { "value": "14px", "lineHeight": "20px" },
      "base": { "value": "16px", "lineHeight": "24px" },
      "lg": { "value": "18px", "lineHeight": "28px" },
      "xl": { "value": "20px", "lineHeight": "28px" },
      "2xl": { "value": "24px", "lineHeight": "32px" },
      "3xl": { "value": "30px", "lineHeight": "36px" },
      "4xl": { "value": "36px", "lineHeight": "40px" }
    },
    "fontWeight": {
      "normal": "400",
      "medium": "500",
      "semibold": "600",
      "bold": "700"
    }
  }
}
```

#### 阴影令牌

```json
{
  "shadow": {
    "sm": {
      "value": "0 1px 2px 0 rgba(0, 0, 0, 0.05)",
      "description": "小阴影"
    },
    "base": {
      "value": "0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px 0 rgba(0, 0, 0, 0.06)",
      "description": "基础阴影"
    },
    "md": {
      "value": "0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)",
      "description": "中等阴影"
    },
    "lg": {
      "value": "0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05)",
      "description": "大阴影"
    },
    "xl": {
      "value": "0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04)",
      "description": "超大阴影"
    }
  }
}
```

#### 圆角令牌

```json
{
  "borderRadius": {
    "none": "0",
    "sm": "2px",
    "base": "4px",
    "md": "6px",
    "lg": "8px",
    "xl": "12px",
    "2xl": "16px",
    "full": "9999px"
  }
}
```

### CSS变量生成

```css
:root {
  --color-brand-primary: #0066CC;
  --color-brand-secondary: #FF6600;
  --color-semantic-success: #28A745;
  --color-semantic-warning: #FFC107;
  --color-semantic-error: #DC3545;
  --color-semantic-info: #17A2B8;
  
  --spacing-1: 4px;
  --spacing-2: 8px;
  --spacing-3: 12px;
  --spacing-4: 16px;
  --spacing-5: 20px;
  --spacing-6: 24px;
  --spacing-8: 32px;
  
  --font-size-xs: 12px;
  --font-size-sm: 14px;
  --font-size-base: 16px;
  --font-size-lg: 18px;
  --font-size-xl: 20px;
  
  --shadow-sm: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
  --shadow-base: 0 1px 3px 0 rgba(0, 0, 0, 0.1);
  --shadow-md: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
  
  --radius-sm: 2px;
  --radius-base: 4px;
  --radius-md: 6px;
  --radius-lg: 8px;
}
```

## 组件设计

### 组件分类

| 类别 | 说明 | 示例 |
|------|------|------|
| 原子组件 | 最基础的UI元素 | Button, Input, Icon |
| 分子组件 | 由原子组件组合 | SearchBar, FormField |
| 组织组件 | 复杂的UI区块 | Card, Modal, Navbar |
| 模板组件 | 页面布局模板 | PageLayout, DashboardLayout |
| 页面组件 | 完整页面 | LoginPage, DashboardPage |

### 组件API设计原则

#### Props命名规范

```typescript
interface ButtonProps {
  variant?: 'primary' | 'secondary' | 'outline' | 'ghost';
  size?: 'sm' | 'md' | 'lg';
  disabled?: boolean;
  loading?: boolean;
  fullWidth?: boolean;
  leftIcon?: React.ReactNode;
  rightIcon?: React.ReactNode;
  children: React.ReactNode;
  onClick?: (event: React.MouseEvent<HTMLButtonElement>) => void;
}
```

#### 组件状态设计

```typescript
type ButtonVariant = 'primary' | 'secondary' | 'outline' | 'ghost';
type ButtonSize = 'sm' | 'md' | 'lg';

interface ButtonState {
  variant: ButtonVariant;
  size: ButtonSize;
  disabled: boolean;
  loading: boolean;
  hovered: boolean;
  focused: boolean;
  pressed: boolean;
}

const buttonStyles: Record<ButtonVariant, Record<ButtonSize, string>> = {
  primary: {
    sm: 'px-3 py-1.5 text-sm',
    md: 'px-4 py-2 text-base',
    lg: 'px-6 py-3 text-lg',
  },
  secondary: {
    sm: 'px-3 py-1.5 text-sm',
    md: 'px-4 py-2 text-base',
    lg: 'px-6 py-3 text-lg',
  },
};
```

### 组件文档模板

```typescript
/**
 * Button组件 - 用于触发操作或事件
 * 
 * @example
 * ```tsx
 * <Button variant="primary" size="md" onClick={handleClick}>
 *   点击我
 * </Button>
 * ```
 * 
 * @example
 * ```tsx
 * <Button variant="outline" leftIcon={<SearchIcon />}>
 *   搜索
 * </Button>
 * ```
 */
export const Button: React.FC<ButtonProps> = ({
  variant = 'primary',
  size = 'md',
  disabled = false,
  loading = false,
  fullWidth = false,
  leftIcon,
  rightIcon,
  children,
  onClick,
  ...props
}) => {
  return (
    <button
      className={cn(
        buttonBaseStyles,
        buttonStyles[variant][size],
        fullWidth && 'w-full',
        disabled && 'opacity-50 cursor-not-allowed'
      )}
      disabled={disabled || loading}
      onClick={onClick}
      {...props}
    >
      {loading && <Spinner className="mr-2" />}
      {leftIcon && <span className="mr-2">{leftIcon}</span>}
      {children}
      {rightIcon && <span className="ml-2">{rightIcon}</span>}
    </button>
  );
};
```

### 组件测试规范

```typescript
import { render, screen, fireEvent } from '@testing-library/react';
import { Button } from './Button';

describe('Button', () => {
  it('应该正确渲染', () => {
    render(<Button>点击我</Button>);
    expect(screen.getByRole('button')).toHaveTextContent('点击我');
  });

  it('应该响应点击事件', () => {
    const handleClick = jest.fn();
    render(<Button onClick={handleClick}>点击我</Button>);
    fireEvent.click(screen.getByRole('button'));
    expect(handleClick).toHaveBeenCalledTimes(1);
  });

  it('禁用状态下不应该响应点击', () => {
    const handleClick = jest.fn();
    render(<Button disabled onClick={handleClick}>点击我</Button>);
    fireEvent.click(screen.getByRole('button'));
    expect(handleClick).not.toHaveBeenCalled();
  });

  it('加载状态应该显示加载指示器', () => {
    render(<Button loading>点击我</Button>);
    expect(screen.getByRole('button')).toBeDisabled();
    expect(screen.getByTestId('spinner')).toBeInTheDocument();
  });
});
```

## 响应式设计

### 断点系统

```typescript
export const breakpoints = {
  sm: '640px',
  md: '768px',
  lg: '1024px',
  xl: '1280px',
  '2xl': '1536px',
} as const;

export const mediaQueries = {
  sm: `@media (min-width: ${breakpoints.sm})`,
  md: `@media (min-width: ${breakpoints.md})`,
  lg: `@media (min-width: ${breakpoints.lg})`,
  xl: `@media (min-width: ${breakpoints.xl})`,
  '2xl': `@media (min-width: ${breakpoints['2xl']})`,
} as const;
```

### 响应式布局

```
┌─────────────────────────────────────────────────────────────┐
│                      响应式断点示意                          │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Mobile (< 640px)                                          │
│  ┌─────────────────────┐                                   │
│  │      Header         │                                   │
│  ├─────────────────────┤                                   │
│  │                     │                                   │
│  │      Content        │                                   │
│  │     (单列)          │                                   │
│  │                     │                                   │
│  ├─────────────────────┤                                   │
│  │      Footer         │                                   │
│  └─────────────────────┘                                   │
│                                                             │
│  Tablet (640px - 1024px)                                   │
│  ┌─────────────────────────────────┐                       │
│  │            Header               │                       │
│  ├─────────────────────────────────┤                       │
│  │            │                    │                       │
│  │  Sidebar   │     Content        │                       │
│  │            │     (双列)         │                       │
│  │            │                    │                       │
│  ├─────────────────────────────────┤                       │
│  │            Footer               │                       │
│  └─────────────────────────────────┘                       │
│                                                             │
│  Desktop (> 1024px)                                        │
│  ┌───────────────────────────────────────────────┐         │
│  │                    Header                     │         │
│  ├──────────┬────────────────────┬───────────────┤         │
│  │          │                    │               │         │
│  │ Sidebar  │     Content        │   Aside       │         │
│  │          │     (三列)         │               │         │
│  │          │                    │               │         │
│  ├──────────┴────────────────────┴───────────────┤         │
│  │                    Footer                     │         │
│  └───────────────────────────────────────────────┘         │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 响应式组件

```typescript
import { useMediaQuery } from 'hooks/useMediaQuery';

interface ResponsiveGridProps {
  children: React.ReactNode;
}

export const ResponsiveGrid: React.FC<ResponsiveGridProps> = ({ children }) => {
  const isMobile = useMediaQuery('(max-width: 639px)');
  const isTablet = useMediaQuery('(min-width: 640px) and (max-width: 1023px)');
  const isDesktop = useMediaQuery('(min-width: 1024px)');

  const columns = isMobile ? 1 : isTablet ? 2 : 3;

  return (
    <div
      className="grid gap-4"
      style={{ gridTemplateColumns: `repeat(${columns}, minmax(0, 1fr))` }}
    >
      {children}
    </div>
  );
};
```

### Tailwind响应式

```html
<div class="
  grid 
  grid-cols-1 
  sm:grid-cols-2 
  lg:grid-cols-3 
  xl:grid-cols-4 
  gap-4
">
  {items.map(item => (
    <Card key={item.id} item={item} />
  ))}
</div>

<nav class="
  flex 
  flex-col 
  md:flex-row 
  lg:space-x-8
">
  <a href="#" class="block py-2 md:py-0">首页</a>
  <a href="#" class="block py-2 md:py-0">产品</a>
  <a href="#" class="block py-2 md:py-0">关于</a>
</nav>
```

### 图片响应式

```html
<picture>
  <source 
    media="(min-width: 1024px)" 
    srcset="image-large.webp"
  />
  <source 
    media="(min-width: 640px)" 
    srcset="image-medium.webp"
  />
  <img 
    src="image-small.webp" 
    alt="响应式图片"
    loading="lazy"
    class="w-full h-auto"
  />
</picture>
```

## 可访问性设计

### WCAG 2.1标准

#### 四大原则

| 原则 | 说明 | 要求 |
|------|------|------|
| 可感知 | 信息和UI组件必须可被用户感知 | 文本替代、字幕、对比度 |
| 可操作 | UI组件和导航必须可操作 | 键盘访问、时间控制、导航 |
| 可理解 | 信息和UI操作必须可理解 | 可读性、可预测性、输入帮助 |
| 健壮性 | 内容必须足够健壮 | 兼容辅助技术 |

### 对比度要求

```
┌─────────────────────────────────────────────────────────────┐
│                      对比度要求                              │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  AA级别（最低要求）                                         │
│  ├── 正文文本：< 18px 或 粗体 < 14px → 对比度 ≥ 4.5:1      │
│  └── 大文本：≥ 18px 或 粗体 ≥ 14px → 对比度 ≥ 3:1          │
│                                                             │
│  AAA级别（增强要求）                                        │
│  ├── 正文文本：对比度 ≥ 7:1                                 │
│  └── 大文本：对比度 ≥ 4.5:1                                 │
│                                                             │
│  示例：                                                     │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  #000000 on #FFFFFF = 21:1 ✓ (AAA)                 │   │
│  │  #767676 on #FFFFFF = 4.54:1 ✓ (AA)               │   │
│  │  #949494 on #FFFFFF = 2.85:1 ✗ (不通过)           │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### ARIA属性使用

```html
<button
  type="button"
  aria-label="关闭对话框"
  aria-describedby="close-tooltip"
>
  <XIcon aria-hidden="true" />
</button>

<div
  role="dialog"
  aria-modal="true"
  aria-labelledby="dialog-title"
  aria-describedby="dialog-description"
>
  <h2 id="dialog-title">确认删除</h2>
  <p id="dialog-description">此操作不可撤销，确定要删除吗？</p>
  <button aria-label="确认删除">删除</button>
  <button aria-label="取消">取消</button>
</div>

<nav aria-label="主导航">
  <ul role="menubar">
    <li role="none">
      <a role="menuitem" href="/">首页</a>
    </li>
    <li role="none">
      <a role="menuitem" href="/products">产品</a>
    </li>
  </ul>
</nav>
```

### 键盘导航

```typescript
const useKeyboardNavigation = (
  items: HTMLElement[],
  options?: { loop?: boolean; orientation?: 'horizontal' | 'vertical' }
) => {
  const { loop = true, orientation = 'vertical' } = options || {};

  const handleKeyDown = (event: KeyboardEvent) => {
    const currentIndex = items.findIndex(item => item === document.activeElement);
    const nextKey = orientation === 'vertical' ? 'ArrowDown' : 'ArrowRight';
    const prevKey = orientation === 'vertical' ? 'ArrowUp' : 'ArrowLeft';

    switch (event.key) {
      case nextKey:
        event.preventDefault();
        const nextIndex = currentIndex < items.length - 1 ? currentIndex + 1 : (loop ? 0 : currentIndex);
        items[nextIndex]?.focus();
        break;
      case prevKey:
        event.preventDefault();
        const prevIndex = currentIndex > 0 ? currentIndex - 1 : (loop ? items.length - 1 : currentIndex);
        items[prevIndex]?.focus();
        break;
      case 'Home':
        event.preventDefault();
        items[0]?.focus();
        break;
      case 'End':
        event.preventDefault();
        items[items.length - 1]?.focus();
        break;
    }
  };

  return { handleKeyDown };
};
```

### 焦点管理

```typescript
const useFocusTrap = (containerRef: RefObject<HTMLElement>, isActive: boolean) => {
  useEffect(() => {
    if (!isActive || !containerRef.current) return;

    const container = containerRef.current;
    const focusableElements = container.querySelectorAll<HTMLElement>(
      'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
    );
    const firstElement = focusableElements[0];
    const lastElement = focusableElements[focusableElements.length - 1];

    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key !== 'Tab') return;

      if (event.shiftKey) {
        if (document.activeElement === firstElement) {
          event.preventDefault();
          lastElement?.focus();
        }
      } else {
        if (document.activeElement === lastElement) {
          event.preventDefault();
          firstElement?.focus();
        }
      }
    };

    container.addEventListener('keydown', handleKeyDown);
    firstElement?.focus();

    return () => {
      container.removeEventListener('keydown', handleKeyDown);
    };
  }, [isActive, containerRef]);
};
```

### 屏幕阅读器支持

```html
<div class="sr-only" aria-live="polite" aria-atomic="true">
  {announcement}
</div>

<table role="table" aria-label="用户列表">
  <caption class="sr-only">系统用户列表</caption>
  <thead>
    <tr>
      <th scope="col">姓名</th>
      <th scope="col">邮箱</th>
      <th scope="col">角色</th>
    </tr>
  </thead>
  <tbody>
    {users.map(user => (
      <tr key={user.id}>
        <td>{user.name}</td>
        <td>{user.email}</td>
        <td>{user.role}</td>
      </tr>
    ))}
  </tbody>
</table>

<form aria-label="用户注册表单">
  <div role="group" aria-labelledby="personal-info">
    <span id="personal-info" class="font-bold">个人信息</span>
    <label for="name">姓名</label>
    <input id="name" type="text" required aria-required="true" />
    
    <label for="email">邮箱</label>
    <input 
      id="email" 
      type="email" 
      required 
      aria-required="true"
      aria-invalid={errors.email ? 'true' : 'false'}
      aria-describedby={errors.email ? 'email-error' : undefined}
    />
    {errors.email && (
      <span id="email-error" role="alert" class="text-red-500">
        {errors.email}
      </span>
    )}
  </div>
</form>
```

## 设计审查清单

### 视觉设计

- [ ] 颜色对比度符合WCAG标准
- [ ] 字体大小和层级清晰
- [ ] 间距一致且符合设计系统
- [ ] 图标风格统一
- [ ] 响应式布局正确

### 交互设计

- [ ] 所有交互元素有hover/focus/active状态
- [ ] 加载状态有明确指示
- [ ] 错误状态有清晰提示
- [ ] 动画流畅且有意义
- [ ] 手势操作符合平台习惯

### 可访问性

- [ ] 键盘完全可操作
- [ ] 屏幕阅读器兼容
- [ ] 颜色不是唯一的信息传达方式
- [ ] 表单有正确的标签和错误提示
- [ ] 焦点顺序合理

### 性能

- [ ] 图片优化和懒加载
- [ ] 字体加载优化
- [ ] CSS/JS压缩
- [ ] 关键渲染路径优化
- [ ] 动画性能优化

## 参考资源

- Material Design: https://material.io/design
- Ant Design: https://ant.design/docs/spec/introduce
- Tailwind CSS: https://tailwindcss.com/docs
- WCAG 2.1: https://www.w3.org/TR/WCAG21
- ARIA规范: https://www.w3.org/TR/wai-aria

***

## UX准则增强（UIUXProMax集成）

> 本章节整合99条UX准则，按10个类别组织。这些准则与UIUXProMax设计智能引擎的参考数据库联动，为Design System Generator Agent提供UX决策依据。

### 参考数据源

- UI风格定义：[references/design-database.md](references/design-database.md)（67种UI风格）
- 行业配色方案：[references/color-palettes.md](references/color-palettes.md)（161套配色）
- 字体配对：[references/font-pairings.md](references/font-pairings.md)（57组字体配对）

### 可访问性（10条）

1. **色彩对比度≥4.5:1**：正文文本与背景的对比度必须满足WCAG AA标准；大文本(≥18px或粗体≥14px)对比度≥3:1
2. **非色彩信息传达**：颜色不能是传达信息的唯一手段，必须配合图标/文字/形状等辅助标识
3. **键盘完全可操作**：所有交互元素必须可通过键盘访问，Tab顺序符合逻辑，焦点状态清晰可见
4. **触控目标≥44px**：移动端可点击区域最小44×44px，间距≥8px避免误触
5. **屏幕阅读器兼容**：使用语义化HTML + ARIA属性，确保辅助技术可正确解读页面结构
6. **焦点指示器可见**：`:focus-visible`样式必须清晰可见，不使用`outline:none`除非提供替代方案
7. **文本可缩放至200%**：页面在文本放大200%时仍可正常使用，不出现内容溢出或遮挡
8. **动画可关闭**：尊重`prefers-reduced-motion`，提供动画关闭选项
9. **错误可识别**：表单错误必须同时使用文字描述+图标标识，不能仅依赖红色边框
10. **跳转链接可用**：提供"跳至主内容"链接，允许键盘用户快速跳过重复导航

### 交互（10条）

11. **操作即时反馈**：用户操作后100ms内提供视觉反馈（按钮状态/加载指示/微动画）
12. **悬停状态明确**：所有可交互元素必须有hover/focus/active/disabled四种状态
13. **加载状态可见**：耗时>300ms的操作必须显示加载指示器，>1s显示进度条
14. **撤销优于确认**：提供撤销操作而非反复确认对话框，降低用户认知负担
15. **手势不冲突**：自定义手势不与浏览器/系统默认手势冲突
16. **拖拽有锚点**：拖拽操作提供视觉锚点和吸附提示
17. **双击/长按有反馈**：隐藏交互（双击/长按/滑动）必须有可发现的提示
18. **表单自动保存**：长表单实现自动保存草稿，防止意外丢失
19. **操作可中断**：长时间操作提供取消按钮，不强制等待完成
20. **滚动有边界**：无限滚动提供"加载更多"按钮，允许用户控制浏览节奏

### 性能（10条）

21. **首屏渲染<1.5s**：关键渲染路径优化，CSS内联关键样式，JS延迟加载
22. **图片懒加载**：视口外图片使用`loading="lazy"`，使用WebP/AVIF格式
23. **字体加载优化**：使用`font-display: swap`，预加载关键字体`<link rel="preload">`
24. **动画60fps**：动画只使用`transform`和`opacity`，避免触发布局重排
25. **虚拟滚动**：长列表(>100项)使用虚拟滚动，减少DOM节点数
26. **代码分割**：路由级代码分割，首屏不加载非必要JS
27. **缓存策略**：静态资源设置合理缓存头，使用内容哈希文件名
28. **骨架屏**：数据加载时显示骨架屏而非空白/加载圈
29. **预加载关键资源**：`<link rel="preload">`预加载首屏关键资源
30. **减少重定向**：避免不必要的重定向链，每条重定向增加延迟

### 布局（10条）

31. **8px网格系统**：所有间距使用8px基础单位（4/8/12/16/24/32/48/64）
32. **视觉层级清晰**：通过大小/颜色/间距/位置建立3级以上视觉层级
33. **内容宽度限制**：正文阅读宽度40-80字符，最大内容宽度1280px
34. **F型阅读模式**：重要信息放置在F型热区（左上→右上→左下）
35. **卡片间距一致**：同组卡片间距统一，不同组间距区分明显
36. **侧边栏可折叠**：侧边栏支持折叠/展开，记住用户偏好
37. **固定操作栏**：表格/列表底部固定操作栏，避免滚动后操作不可达
38. **留白引导视线**：使用留白而非线条分隔内容区域
39. **对齐一致性**：同一页面内对齐方式统一（左对齐/居中对齐不混用）
40. **响应式断点**：sm(640)/md(768)/lg(1024)/xl(1280)/2xl(1536)五断点体系

### 导航（10条）

41. **3次点击可达**：任何页面从首页出发3次点击内可达
42. **面包屑导航**：层级>2的页面必须提供面包屑导航
43. **当前页标识**：导航栏当前页高亮标识，使用`aria-current="page"`
44. **搜索可见性**：内容>30页时搜索框必须可见（非隐藏在图标后）
45. **返回按钮一致**：返回按钮位置和样式全局一致
46. **导航不遮挡内容**：固定导航栏不遮挡页面内容，内容区域预留偏移
47. **移动端底部导航**：移动端主导航放底部，符合单手操作习惯
48. **导航层级≤3**：导航菜单层级不超过3级，超过时使用搜索/标签
49. **URL可书签**：每个可导航状态有唯一URL，支持浏览器前进/后退
50. **404页面有用**：404页面提供搜索框+热门链接+返回首页按钮

### 表单（10条）

51. **标签始终可见**：表单标签始终可见，不使用placeholder替代label
52. **输入验证即时**：字段级即时验证，不等到提交时才显示错误
53. **错误信息具体**：错误信息说明具体原因和修复方法（如"密码需至少8位"而非"输入无效"）
54. **必填标识清晰**：必填字段使用`*`标识+`aria-required="true"`
55. **输入格式提示**：复杂格式提供格式示例（如"YYYY-MM-DD"）
56. **智能默认值**：为可预测的字段提供智能默认值
57. **密码显示切换**：密码输入框提供显示/隐藏切换按钮
58. **自动完成支持**：启用`autocomplete`属性，减少重复输入
59. **多步表单进度**：多步表单显示进度指示器，允许回退修改
60. **提交按钮防重复**：提交后禁用按钮或显示加载状态，防止重复提交

### 反馈（10条）

61. **操作成功确认**：所有操作提供成功确认（Toast/内联消息/状态变化）
62. **错误可恢复**：错误状态提供恢复路径，不将用户困在错误页面
63. **空状态有引导**：空列表/空搜索提供引导操作（"创建第一个项目"/"调整搜索条件"）
64. **Toast自动消失**：成功Toast 3-5秒自动消失，错误Toast需手动关闭
65. **进度可感知**：长时间操作显示进度百分比+预估剩余时间
66. **数据变化高亮**：数据更新时短暂高亮变化区域
67. **离线状态提示**：网络断开时顶部显示离线提示条
68. **批量操作反馈**：批量操作显示成功/失败/跳过的详细计数
69. **冲突提示**：并发编辑冲突时提示用户并提供合并选项
70. **版本历史可访问**：重要操作提供版本历史和回滚功能

### 一致性（10条）

71. **组件复用**：相同功能使用相同组件，不创建功能重复的变体
72. **术语统一**：同一概念全局使用相同术语（如"删除"vs"移除"不混用）
73. **图标语义一致**：相同图标始终表示相同操作（如齿轮=设置）
74. **交互模式一致**：相同操作触发方式一致（如删除始终用红色按钮+确认）
75. **日期格式统一**：全局统一日期格式（如YYYY-MM-DD），不混用
76. **色彩语义一致**：红色=错误/删除，绿色=成功/确认，黄色=警告，蓝色=信息
77. **间距系统统一**：全局使用同一间距系统，不随意添加间距值
78. **字体层级一致**：标题/副标题/正文/辅助文字层级全局一致
79. **动效风格一致**：过渡动画时长/缓动函数全局一致（如200ms ease-out）
80. **错误处理模式一致**：错误展示方式全局一致（位置/样式/关闭方式）

### 响应式（10条）

81. **移动优先设计**：从最小屏幕开始设计，逐步增强大屏体验
82. **触控/鼠标双适配**：交互元素同时支持触控和鼠标操作
83. **图片响应式**：使用`<picture>`+`srcset`提供不同分辨率图片
84. **表格响应式**：小屏表格转为卡片列表或提供水平滚动
85. **导航响应式**：大屏水平导航→小屏汉堡菜单/底部导航
86. **字体响应式**：使用`clamp()`实现流式字体缩放
87. **隐藏非关键内容**：小屏隐藏装饰性内容，保留核心功能
88. **触摸目标间距**：移动端相邻可点击元素间距≥8px
89. **横屏适配**：移动端横屏布局不崩溃，关键内容仍可访问
90. **打印样式**：提供`@media print`样式，隐藏导航/广告，优化打印输出

### 可发现性（9条）

91. **新功能引导**：新用户首次使用提供功能引导（非强制教程）
92. **快捷键可发现**：常用操作提供快捷键，并在Tooltip中显示
93. **搜索建议**：搜索框提供热门搜索/历史搜索/自动补全建议
94. **相关内容推荐**：内容页底部推荐相关内容，增加页面间连通性
95. **功能入口可见**：核心功能入口不隐藏在二级菜单中
96. **状态变化通知**：后台状态变化通过通知/徽标提醒用户
97. **最近使用记录**：提供最近使用/最近访问的快速入口
98. **上下文帮助**：复杂功能提供上下文帮助（Tooltip/帮助链接/示例）
99. **渐进式披露**：高级功能渐进式披露，不一次性展示所有选项
