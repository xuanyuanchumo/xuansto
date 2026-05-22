/**
 * Authentication Setup for E2E Tests
 *
 * 设置 E2E 测试的认证状态
 */

import { test as setup, expect } from '@playwright/test';

const authFile = 'playwright/.auth/user.json';

setup('authenticate', async ({ page }) => {
  // 导航到登录页面
  await page.goto('/login');

  // 填写登录表单
  await page.fill('[data-testid="email-input"]', 'test@example.com');
  await page.fill('[data-testid="password-input"]', 'password123');

  // 点击登录按钮
  await page.click('[data-testid="login-btn"]');

  // 等待登录成功并重定向
  await page.waitForURL('/dashboard');

  // 验证登录成功
  await expect(page.locator('[data-testid="user-menu"]')).toBeVisible();

  // 保存认证状态
  await page.context().storageState({ path: authFile });
});

setup('authenticate as admin', async ({ page }) => {
  // 导航到登录页面
  await page.goto('/login');

  // 填写管理员登录表单
  await page.fill('[data-testid="email-input"]', 'admin@example.com');
  await page.fill('[data-testid="password-input"]', 'admin123');

  // 点击登录按钮
  await page.click('[data-testid="login-btn"]');

  // 等待登录成功并重定向
  await page.waitForURL('/dashboard');

  // 验证管理员权限
  await expect(page.locator('[data-testid="admin-menu"]')).toBeVisible();

  // 保存认证状态
  await page.context().storageState({ path: 'playwright/.auth/admin.json' });
});
