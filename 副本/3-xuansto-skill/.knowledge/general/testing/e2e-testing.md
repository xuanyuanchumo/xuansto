---
id: e2e-testing
type: knowledge
category: testing
tags: [E2E测试, Playwright, Cypress, 用户旅程, 视觉回归]
version: 1.0.0
confidence: high
---

## 端到端测试指南 (版本: 1.0 | 适用: Playwright/Cypress)

### 核心规则
- 以核心业务流程为主线编写 E2E 测试：注册→登录→核心操作→退出
- 数据准备使用 API 或数据库种子，避免通过 UI 准备
- 使用 `data-testid` 定位元素，避免依赖 CSS 类名或文本
- 每个测试独立，不依赖其他测试的副作用
- 超时设置：导航 30s，操作 10s，断言 5s
- E2E 测试控制在核心路径，数量不超过 50 个
- 视觉回归：设置合理差异阈值（0.1%-1%），截图基线纳入版本控制

### 代码示例

```typescript
test('用户完成购买流程', async ({ page }) => {
  await page.goto('/login');
  await page.fill('[data-testid=email]', 'user@test.com');
  await page.fill('[data-testid=password]', 'password123');
  await page.click('[data-testid=submit]');
  await expect(page).toHaveURL('/dashboard');
  await page.click('[data-testid=add-to-cart]');
  await expect(page.locator('.cart-count')).toHaveText('1');
});
```

### 反模式
- ❌ 依赖 CSS 类名定位元素 — UI 变更导致测试脆弱
- ❌ 测试之间有依赖关系 — 无法并行执行
- ❌ E2E 测试覆盖过多细节 — 应聚焦核心路径
