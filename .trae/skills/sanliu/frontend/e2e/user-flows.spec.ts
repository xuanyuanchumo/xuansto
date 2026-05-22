/**
 * Critical User Flows E2E Tests
 *
 * 测试关键用户流程
 */

import { test, expect } from '@playwright/test';

test.describe('User Authentication Flow', () => {
  test('should login successfully', async ({ page }) => {
    // 导航到登录页面
    await page.goto('/login');

    // 填写登录表单
    await page.fill('[data-testid="email-input"]', 'test@example.com');
    await page.fill('[data-testid="password-input"]', 'password123');

    // 点击登录按钮
    await page.click('[data-testid="login-btn"]');

    // 验证重定向到仪表盘
    await page.waitForURL('/dashboard');

    // 验证用户菜单可见
    await expect(page.locator('[data-testid="user-menu"]')).toBeVisible();
  });

  test('should show error for invalid credentials', async ({ page }) => {
    await page.goto('/login');

    // 填写错误的凭据
    await page.fill('[data-testid="email-input"]', 'wrong@example.com');
    await page.fill('[data-testid="password-input"]', 'wrongpassword');

    // 点击登录
    await page.click('[data-testid="login-btn"]');

    // 验证显示错误消息
    await expect(page.locator('[data-testid="error-message"]')).toBeVisible();
    await expect(page.locator('[data-testid="error-message"]')).toContainText('Invalid');
  });

  test('should logout successfully', async ({ page }) => {
    // 先登录
    await page.goto('/login');
    await page.fill('[data-testid="email-input"]', 'test@example.com');
    await page.fill('[data-testid="password-input"]', 'password123');
    await page.click('[data-testid="login-btn"]');
    await page.waitForURL('/dashboard');

    // 点击用户菜单
    await page.click('[data-testid="user-menu"]');

    // 点击登出
    await page.click('[data-testid="logout-btn"]');

    // 验证重定向到登录页面
    await page.waitForURL('/login');

    // 验证用户菜单不可见
    await expect(page.locator('[data-testid="user-menu"]')).not.toBeVisible();
  });
});

test.describe('Project Management Flow', () => {
  test.beforeEach(async ({ page }) => {
    // 登录
    await page.goto('/login');
    await page.fill('[data-testid="email-input"]', 'test@example.com');
    await page.fill('[data-testid="password-input"]', 'password123');
    await page.click('[data-testid="login-btn"]');
    await page.waitForURL('/dashboard');
  });

  test('should create and manage project', async ({ page }) => {
    // 1. 导航到项目页面
    await page.click('[data-testid="projects-nav"]');
    await page.waitForURL('/projects');

    // 2. 创建新项目
    await page.click('[data-testid="create-project-btn"]');
    await page.fill('[data-testid="project-name-input"]', 'E2E Flow Project');
    await page.fill('[data-testid="project-description-input"]', 'Created by E2E test');
    await page.click('[data-testid="submit-project-btn"]');

    // 3. 验证项目创建成功
    await expect(page.locator('[data-testid="project-card"]:has-text("E2E Flow Project")')).toBeVisible();

    // 4. 打开项目详情
    await page.click('[data-testid="project-card"]:has-text("E2E Flow Project")');

    // 5. 验证项目详情页
    await expect(page).toHaveURL(/.*projects\/\d+/);
    await expect(page.locator('h1')).toContainText('E2E Flow Project');

    // 6. 编辑项目
    await page.click('[data-testid="edit-project-btn"]');
    await page.fill('[data-testid="project-name-input"]', 'Updated E2E Project');
    await page.click('[data-testid="save-btn"]');

    // 7. 验证更新成功
    await expect(page.locator('h1')).toContainText('Updated E2E Project');

    // 8. 删除项目
    await page.click('[data-testid="delete-project-btn"]');
    await page.click('[data-testid="confirm-delete-btn"]');

    // 9. 验证返回项目列表
    await expect(page).toHaveURL('/projects');
    await expect(page.locator('[data-testid="project-card"]:has-text("Updated E2E Project")')).not.toBeVisible();
  });

  test('should search and filter projects', async ({ page }) => {
    // 导航到项目页面
    await page.click('[data-testid="projects-nav"]');
    await page.waitForURL('/projects');

    // 搜索项目
    await page.fill('[data-testid="search-input"]', 'Test');
    await page.waitForTimeout(500);

    // 验证搜索结果
    const projectCards = page.locator('[data-testid="project-card"]');
    const count = await projectCards.count();

    for (let i = 0; i < count; i++) {
      const name = await projectCards.nth(i).locator('[data-testid="project-name"]').textContent();
      expect(name!.toLowerCase()).toContain('test');
    }

    // 清除搜索
    await page.click('[data-testid="clear-filters"]');

    // 验证显示所有项目
    const totalCount = await page.locator('[data-testid="project-card"]').count();
    expect(totalCount).toBeGreaterThanOrEqual(count);
  });
});

test.describe('Task Management Flow', () => {
  test.beforeEach(async ({ page }) => {
    // 登录
    await page.goto('/login');
    await page.fill('[data-testid="email-input"]', 'test@example.com');
    await page.fill('[data-testid="password-input"]', 'password123');
    await page.click('[data-testid="login-btn"]');
    await page.waitForURL('/dashboard');
  });

  test('should create and manage task', async ({ page }) => {
    // 1. 导航到项目页面
    await page.click('[data-testid="projects-nav"]');
    await page.waitForURL('/projects');

    // 2. 打开第一个项目
    await page.click('[data-testid="project-card"]').first();
    await page.waitForURL(/.*projects\/\d+/);

    // 3. 创建新任务
    await page.click('[data-testid="create-task-btn"]');
    await page.fill('[data-testid="task-title-input"]', 'E2E Task');
    await page.fill('[data-testid="task-description-input"]', 'Task created by E2E test');
    await page.selectOption('[data-testid="task-priority-select"]', 'high');
    await page.click('[data-testid="submit-task-btn"]');

    // 4. 验证任务创建成功
    await expect(page.locator('[data-testid="task-item"]:has-text("E2E Task")')).toBeVisible();

    // 5. 编辑任务
    await page.click('[data-testid="task-item"]:has-text("E2E Task")');
    await page.click('[data-testid="edit-task-btn"]');
    await page.fill('[data-testid="task-title-input"]', 'Updated E2E Task');
    await page.click('[data-testid="save-btn"]');

    // 6. 验证更新成功
    await expect(page.locator('[data-testid="task-title"]')).toContainText('Updated E2E Task');

    // 7. 完成任务
    await page.click('[data-testid="complete-task-btn"]');
    await expect(page.locator('[data-testid="task-status"]')).toContainText('Completed');
  });

  test('should assign task to agent', async ({ page }) => {
    // 导航到任务页面
    await page.click('[data-testid="tasks-nav"]');
    await page.waitForURL('/tasks');

    // 打开第一个任务
    await page.click('[data-testid="task-item"]').first();

    // 分配代理
    await page.click('[data-testid="assign-agent-btn"]');
    await page.selectOption('[data-testid="agent-select"]', '1'); // 选择第一个代理
    await page.click('[data-testid="confirm-assign-btn"]');

    // 验证分配成功
    await expect(page.locator('[data-testid="assigned-agent"]')).toBeVisible();
  });
});

test.describe('Dashboard Navigation Flow', () => {
  test.beforeEach(async ({ page }) => {
    // 登录
    await page.goto('/login');
    await page.fill('[data-testid="email-input"]', 'test@example.com');
    await page.fill('[data-testid="password-input"]', 'password123');
    await page.click('[data-testid="login-btn"]');
    await page.waitForURL('/dashboard');
  });

  test('should navigate through all main sections', async ({ page }) => {
    // 1. 仪表盘
    await expect(page.locator('h1')).toContainText('Dashboard');

    // 2. 导航到项目
    await page.click('[data-testid="projects-nav"]');
    await page.waitForURL('/projects');
    await expect(page.locator('h1')).toContainText('Projects');

    // 3. 导航到任务
    await page.click('[data-testid="tasks-nav"]');
    await page.waitForURL('/tasks');
    await expect(page.locator('h1')).toContainText('Tasks');

    // 4. 导航到代理
    await page.click('[data-testid="agents-nav"]');
    await page.waitForURL('/agents');
    await expect(page.locator('h1')).toContainText('Agents');

    // 5. 返回仪表盘
    await page.click('[data-testid="dashboard-nav"]');
    await page.waitForURL('/dashboard');
    await expect(page.locator('h1')).toContainText('Dashboard');
  });

  test('should view project stats from dashboard', async ({ page }) => {
    // 点击项目统计卡片
    await page.click('[data-testid="total-projects"]');

    // 验证导航到项目页面
    await page.waitForURL('/projects');
    await expect(page.locator('h1')).toContainText('Projects');
  });
});

test.describe('Settings Flow', () => {
  test.beforeEach(async ({ page }) => {
    // 登录
    await page.goto('/login');
    await page.fill('[data-testid="email-input"]', 'test@example.com');
    await page.fill('[data-testid="password-input"]', 'password123');
    await page.click('[data-testid="login-btn"]');
    await page.waitForURL('/dashboard');
  });

  test('should update user profile', async ({ page }) => {
    // 导航到设置
    await page.click('[data-testid="user-menu"]');
    await page.click('[data-testid="settings-link"]');
    await page.waitForURL('/settings');

    // 更新用户名
    await page.fill('[data-testid="username-input"]', 'Updated User');
    await page.click('[data-testid="save-profile-btn"]');

    // 验证更新成功
    await expect(page.locator('[data-testid="success-message"]')).toBeVisible();
    await expect(page.locator('[data-testid="success-message"]')).toContainText('Profile updated');
  });

  test('should change password', async ({ page }) => {
    // 导航到设置
    await page.click('[data-testid="user-menu"]');
    await page.click('[data-testid="settings-link"]');
    await page.waitForURL('/settings');

    // 切换到安全设置
    await page.click('[data-testid="security-tab"]');

    // 填写密码更改表单
    await page.fill('[data-testid="current-password-input"]', 'password123');
    await page.fill('[data-testid="new-password-input"]', 'newpassword123');
    await page.fill('[data-testid="confirm-password-input"]', 'newpassword123');
    await page.click('[data-testid="change-password-btn"]');

    // 验证密码更改成功
    await expect(page.locator('[data-testid="success-message"]')).toBeVisible();
  });
});

test.describe('Error Handling Flow', () => {
  test.beforeEach(async ({ page }) => {
    // 登录
    await page.goto('/login');
    await page.fill('[data-testid="email-input"]', 'test@example.com');
    await page.fill('[data-testid="password-input"]', 'password123');
    await page.click('[data-testid="login-btn"]');
    await page.waitForURL('/dashboard');
  });

  test('should handle 404 error', async ({ page }) => {
    // 访问不存在的页面
    await page.goto('/nonexistent-page');

    // 验证显示 404 页面
    await expect(page.locator('[data-testid="error-404"]')).toBeVisible();
    await expect(page.locator('[data-testid="error-404"]')).toContainText('Page not found');

    // 点击返回首页
    await page.click('[data-testid="back-home-btn"]');
    await page.waitForURL('/dashboard');
  });

  test('should handle network errors gracefully', async ({ page }) => {
    // 模拟网络错误
    await page.route('**/api/projects', route => route.abort('failed'));

    // 导航到项目页面
    await page.click('[data-testid="projects-nav"]');
    await page.waitForURL('/projects');

    // 验证显示错误提示
    await expect(page.locator('[data-testid="error-message"]')).toBeVisible();

    // 点击重试
    await page.unroute('**/api/projects');
    await page.click('[data-testid="retry-btn"]');

    // 验证项目列表加载
    await expect(page.locator('[data-testid="project-list"]')).toBeVisible();
  });
});

test.describe('Responsive User Flow', () => {
  test.beforeEach(async ({ page }) => {
    // 登录
    await page.goto('/login');
    await page.fill('[data-testid="email-input"]', 'test@example.com');
    await page.fill('[data-testid="password-input"]', 'password123');
    await page.click('[data-testid="login-btn"]');
    await page.waitForURL('/dashboard');
  });

  test('should work on mobile viewport', async ({ page }) => {
    // 设置移动端视口
    await page.setViewportSize({ width: 375, height: 667 });

    // 验证汉堡菜单
    await expect(page.locator('[data-testid="mobile-menu-btn"]')).toBeVisible();

    // 打开移动菜单
    await page.click('[data-testid="mobile-menu-btn"]');
    await expect(page.locator('[data-testid="mobile-menu"]')).toBeVisible();

    // 导航到项目页面
    await page.click('[data-testid="mobile-projects-link"]');
    await page.waitForURL('/projects');

    // 验证项目列表可见
    await expect(page.locator('[data-testid="project-list"]')).toBeVisible();
  });

  test('should work on tablet viewport', async ({ page }) => {
    // 设置平板视口
    await page.setViewportSize({ width: 768, height: 1024 });

    // 验证侧边栏可见
    await expect(page.locator('[data-testid="sidebar"]')).toBeVisible();

    // 导航到不同页面
    await page.click('[data-testid="projects-nav"]');
    await page.waitForURL('/projects');

    await page.click('[data-testid="tasks-nav"]');
    await page.waitForURL('/tasks');
  });
});
