---
id: e2e-testing
type: knowledge
category: testing
tags: [E2E测试, Playwright, Cypress, 用户旅程, 视觉回归]
version: 1.0.0
created: 2026-04-28
updated: 2026-04-28
confidence: high
---

# 端到端测试指南

## 框架对比

| 特性 | Playwright | Cypress |
|------|-----------|---------|
| 浏览器支持 | Chromium/Firefox/WebKit | Chromium/Firefox（有限） |
| 语言支持 | JS/TS/Python/Java/.NET | JS/TS |
| 执行方式 | 进程外控制浏览器 | 浏览器内执行 |
| 并行执行 | 内置支持 | 需付费 Dashboard |
| 移动端 | 移动端视口模拟 | 同左 |
| 自动等待 | 内置 Auto-waiting | 内置重试机制 |

## 用户旅程测试

以核心业务流程为主线编写端到端测试：

1. **识别关键路径**：注册 → 登录 → 核心操作 → 退出
2. **数据准备**：使用 API 或数据库种子数据，避免通过 UI 准备
3. **断言关键节点**：验证页面状态、URL 变化、数据持久化
4. **清理策略**：测试后清理或使用独立测试环境

```typescript
// Playwright 示例
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

## 视觉回归测试

- 使用像素对比（Pixelmatch）或结构对比（Applitools）
- 截图基线纳入版本控制
- 设置合理差异阈值（0.1%-1%），避免抗锯齿等微小差异误报
- 按组件/页面组织截图，减少基线维护成本

## 最佳实践

- 使用 `data-testid` 定位元素，避免依赖 CSS 类名或文本
- 每个测试独立，不依赖其他测试的副作用
- 设置合理超时（导航 30s，操作 10s，断言 5s）
- CI 中录制失败视频和截图，加速问题定位
- E2E 测试控制在核心路径，数量不超过 50 个
