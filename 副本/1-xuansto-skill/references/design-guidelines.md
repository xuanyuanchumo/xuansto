# 设计指南参考文档

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
