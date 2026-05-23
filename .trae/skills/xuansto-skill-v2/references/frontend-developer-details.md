# Frontend Developer 详细参考

## 记忆系统

- **短期记忆**: 当前任务上下文、活跃组件状态、临时变量
- **中期记忆**: 项目组件库、样式规范、API契约
- **长期记忆**: 最佳实践模式、性能优化经验、错误处理策略

## 协作关系

- **上游**: 接收 Architect 的设计规范、Tech Lead 的技术决策
- **下游**: 输出组件给 Backend Developer 进行接口联调
- **同级**: 与 Mobile Developer 保持跨端一致性

## Karpathy Guidelines 详细说明

### 1. Think Before Coding（编码前思考）
- 理解组件交互和数据流再动手写代码；若需求有歧义，先提问
- 分析现有组件结构，确定最佳实现路径
- 不假设需求细节，必须与产品经理确认

### 2. Simplicity First（简洁优先）
- 不添加未要求的功能；严格按需求实现，不预加功能，不过度抽象
- 用最少的代码实现功能，避免过度工程化
- 不为不可能场景写防御性逻辑，信任类型系统

### 3. Surgical Changes（外科手术式修改）
- 只修改必要的代码行；保持现有代码风格；不重构无关代码
- 组件变更只影响目标范围，不扩散到无关模块
- 不顺手优化其他组件的实现

### 4. Goal-Driven Execution（目标驱动执行）
- 每个组件必须有可验证的渲染结果和交互行为
- 组件必须通过单元测试和视觉回归测试
- 代码变更必须有明确的验收标准

## 代码风格规范

```javascript
// 组件命名: PascalCase
export const UserProfile = () => {};

// Hook命名: use前缀
const useUserData = () => {};

// 事件处理: handle前缀
const handleClick = () => {};

// 常量: UPPER_SNAKE_CASE
const MAX_RETRIES = 3;
```

## 语言规范应用

```yaml
规范文件: references/typescript-standards.md

前端框架规范:
  React:
    - 组件命名: PascalCase
    - Hook使用规范
    - 状态管理最佳实践
    - 性能优化模式
  Vue:
    - 组合式API规范
    - Pinia状态管理
    - 组件通信模式
  Angular:
    - 组件/Service分离
    - 依赖注入模式
    - RxJS响应式编程

Node.js后端规范:
  NestJS:
    - 模块化架构
    - 装饰器使用
    - DTO验证
  Express:
    - 路由组织
    - 中间件链
    - 错误处理

测试规范:
  单元测试: Jest / Vitest
  E2E测试: Playwright / Cypress
  组件测试: Testing Library
```

## Critical Rules 详细示例

### 禁止内联样式泛滥

```javascript
// ❌ 错误
<div style={{ color: 'red', fontSize: '14px', margin: '10px' }}>

// ✅ 正确
<div className="error-text">
```

### 禁止直接操作DOM

```javascript
// ❌ 错误
document.getElementById('myElement').style.display = 'none';

// ✅ 正确
const [isVisible, setIsVisible] = useState(true);
```

### 禁止未处理的异步操作

```javascript
// ❌ 错误
useEffect(() => {
  fetchData().then(setData);
}, []);

// ✅ 正确
useEffect(() => {
  let cancelled = false;
  fetchData()
    .then(data => !cancelled && setData(data))
    .catch(handleError);
  return () => { cancelled = true; };
}, []);
```

### 禁止硬编码配置

```javascript
// ❌ 错误
const API_URL = 'https://api.example.com';

// ✅ 正确
const API_URL = process.env.REACT_APP_API_URL;
```

## 状态管理交付规范

```typescript
interface StoreStructure {
  state: {
    data: DataType;
    ui: {
      loading: boolean;
      error: Error | null;
    };
  };
  actions: {
    setData: (data: DataType) => void;
    fetchData: () => Promise<void>;
  };
  selectors: {
    getFilteredData: (state: State) => FilteredData;
  };
}
```

## 性能优化交付

```typescript
const performanceChecklist = {
  codeSplitting: '使用React.lazy动态导入',
  memoization: '使用React.memo/useMemo/useCallback',
  virtualization: '长列表使用虚拟滚动',
  imageOptimization: '使用WebP/懒加载',
  bundleAnalysis: '打包体积分析报告'
};
```

## 开发流程

```
1. 需求接收 → 解析设计稿/需求文档 → 确认交互细节
2. 技术设计 → 组件拆分 → 状态设计 → API对接方案
3. 编码实现 → 基础组件开发 → 业务组件开发 → 样式实现
4. 测试验证 → 单元测试 → 集成测试 → 视觉回归测试
5. 代码提交 → 代码审查 → 合并主分支
```

## 任务执行模板

```markdown
## 任务: [组件名称]开发

### 输入
- 设计稿: [Figma链接]
- API文档: [Swagger链接]
- 技术规范: [规范文档]

### 执行步骤
1. [ ] 分析设计稿，拆分组件
2. [ ] 创建组件骨架
3. [ ] 实现基础样式
4. [ ] 实现交互逻辑
5. [ ] 对接API
6. [ ] 编写测试
7. [ ] 性能优化

### 输出
- 组件文件: `src/components/[ComponentName]/index.tsx`
- 样式文件: `src/components/[ComponentName]/styles.ts`
- 测试文件: `src/components/[ComponentName]/index.test.tsx`
```

## 错误处理与恢复

```typescript
// API错误处理
const handleApiError = (error: ApiError) => {
  switch (error.code) {
    case 'NETWORK_ERROR':
      showToast('网络连接失败，请检查网络');
      break;
    case 'UNAUTHORIZED':
      redirectToLogin();
      break;
    case 'VALIDATION_ERROR':
      showFieldErrors(error.details);
      break;
    default:
      showToast('操作失败，请稍后重试');
  }
};

// 组件错误边界
class ErrorBoundary extends React.Component {
  state = { hasError: false };
  static getDerivedStateFromError() {
    return { hasError: true };
  }
  componentDidCatch(error: Error, info: ErrorInfo) {
    logError(error, info);
  }
  render() {
    if (this.state.hasError) {
      return <FallbackUI />;
    }
    return this.props.children;
  }
}
```

## 工具与资源

### 推荐工具链
- **框架**: React 18+ / Vue 3+
- **状态管理**: Zustand / Jotai / Pinia
- **样式方案**: Tailwind CSS / CSS Modules / Styled Components
- **测试**: Vitest / Jest + Testing Library
- **构建**: Vite / Next.js
- **代码质量**: ESLint + Prettier + TypeScript

### 调试技巧

```javascript
// React DevTools Profiler
<Profiler id="ComponentName" onRender={onRenderCallback}>
  <Component />
</Profiler>

// 性能标记
performance.mark('component-start');
// ... 渲染逻辑
performance.mark('component-end');
performance.measure('component-render', 'component-start', 'component-end');
```
