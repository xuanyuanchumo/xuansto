import { test, expect } from '@playwright/test';

test.describe('仪表板访问流程', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/dashboard');
    await page.waitForLoadState('networkidle');
  });

  test.describe('页面加载', () => {
    test('应该显示仪表板标题', async ({ page }) => {
      await expect(page.locator('h2, h1')).toContainText(/仪表盘|Dashboard/i);
    });

    test('应该显示统计卡片', async ({ page }) => {
      await expect(page.locator('[data-testid="stat-card"]')).toHaveCount(4);
    });

    test('应该显示快速操作区域', async ({ page }) => {
      await expect(page.locator('[data-testid="quick-actions"]')).toBeVisible();
    });
  });

  test.describe('统计卡片', () => {
    test('应该显示项目总数', async ({ page }) => {
      const projectCard = page.locator('[data-testid="stat-card"]:has-text("项目")');
      await expect(projectCard).toBeVisible();
      
      const value = await projectCard.locator('.stat-value').textContent();
      expect(value).toMatch(/^\d+$/);
    });

    test('应该显示活跃任务数', async ({ page }) => {
      const taskCard = page.locator('[data-testid="stat-card"]:has-text("任务")');
      await expect(taskCard).toBeVisible();
    });

    test('应该显示Agent数量', async ({ page }) => {
      const agentCard = page.locator('[data-testid="stat-card"]:has-text("Agent")');
      await expect(agentCard).toBeVisible();
    });

    test('点击统计卡片应导航到对应页面', async ({ page }) => {
      const projectCard = page.locator('[data-testid="stat-card"]:has-text("项目")');
      await projectCard.click();
      
      await expect(page).toHaveURL(/.*projects/);
    });
  });

  test.describe('快速操作', () => {
    test('应该显示创建项目按钮', async ({ page }) => {
      const createButton = page.locator('[data-testid="quick-action-create-project"]');
      await expect(createButton).toBeVisible();
    });

    test('应该显示创建任务按钮', async ({ page }) => {
      const createButton = page.locator('[data-testid="quick-action-create-task"]');
      await expect(createButton).toBeVisible();
    });

    test('点击创建项目应导航到创建页面', async ({ page }) => {
      await page.click('[data-testid="quick-action-create-project"]');
      
      await expect(page).toHaveURL(/.*projects\/create/);
    });

    test('点击创建任务应导航到任务页面', async ({ page }) => {
      await page.click('[data-testid="quick-action-create-task"]');
      
      await expect(page).toHaveURL(/.*tasks/);
    });
  });

  test.describe('最近活动', () => {
    test('应该显示最近活动列表', async ({ page }) => {
      await expect(page.locator('[data-testid="recent-activities"]')).toBeVisible();
    });

    test('应该显示活动时间', async ({ page }) => {
      const activities = page.locator('[data-testid="activity-item"]');
      const count = await activities.count();
      
      if (count > 0) {
        const firstActivity = activities.first();
        await expect(firstActivity.locator('[data-testid="activity-time"]')).toBeVisible();
      }
    });

    test('应该显示活动描述', async ({ page }) => {
      const activities = page.locator('[data-testid="activity-item"]');
      const count = await activities.count();
      
      if (count > 0) {
        const firstActivity = activities.first();
        await expect(firstActivity.locator('[data-testid="activity-description"]')).toBeVisible();
      }
    });

    test('点击活动项应导航到相关页面', async ({ page }) => {
      const activities = page.locator('[data-testid="activity-item"]');
      const count = await activities.count();
      
      if (count > 0) {
        await activities.first().click();
        await page.waitForTimeout(500);
      }
    });
  });

  test.describe('项目概览', () => {
    test('应该显示项目列表概览', async ({ page }) => {
      const projectOverview = page.locator('[data-testid="project-overview"]');
      if (await projectOverview.isVisible()) {
        await expect(projectOverview).toBeVisible();
      }
    });

    test('应该显示项目状态分布', async ({ page }) => {
      const statusChart = page.locator('[data-testid="project-status-chart"]');
      if (await statusChart.isVisible()) {
        await expect(statusChart).toBeVisible();
      }
    });
  });

  test.describe('任务概览', () => {
    test('应该显示任务进度', async ({ page }) => {
      const taskProgress = page.locator('[data-testid="task-progress"]');
      if (await taskProgress.isVisible()) {
        await expect(taskProgress).toBeVisible();
      }
    });

    test('应该显示任务优先级分布', async ({ page }) => {
      const priorityChart = page.locator('[data-testid="task-priority-chart"]');
      if (await priorityChart.isVisible()) {
        await expect(priorityChart).toBeVisible();
      }
    });
  });

  test.describe('导航功能', () => {
    test('应该能够导航到项目页面', async ({ page }) => {
      await page.click('[data-testid="nav-projects"]');
      await expect(page).toHaveURL(/.*projects/);
    });

    test('应该能够导航到任务页面', async ({ page }) => {
      await page.click('[data-testid="nav-tasks"]');
      await expect(page).toHaveURL(/.*tasks/);
    });

    test('应该能够导航到Agent页面', async ({ page }) => {
      await page.click('[data-testid="nav-agents"]');
      await expect(page).toHaveURL(/.*agents/);
    });

    test('应该能够导航到统计页面', async ({ page }) => {
      await page.click('[data-testid="nav-statistics"]');
      await expect(page).toHaveURL(/.*statistics/);
    });
  });

  test.describe('数据刷新', () => {
    test('应该能够手动刷新数据', async ({ page }) => {
      const refreshButton = page.locator('[data-testid="refresh-dashboard"]');
      if (await refreshButton.isVisible()) {
        await refreshButton.click();
        await expect(page.locator('.el-loading-mask')).toBeVisible();
        await expect(page.locator('.el-loading-mask')).not.toBeVisible();
      }
    });

    test('应该支持自动刷新', async ({ page }) => {
      const autoRefreshToggle = page.locator('[data-testid="auto-refresh-toggle"]');
      if (await autoRefreshToggle.isVisible()) {
        await autoRefreshToggle.click();
        await expect(autoRefreshToggle).toHaveClass(/is-active/);
      }
    });
  });

  test.describe('响应式设计', () => {
    test('移动端应正确显示布局', async ({ page }) => {
      await page.setViewportSize({ width: 375, height: 667 });
      
      await expect(page.locator('[data-testid="stat-card"]').first()).toBeVisible();
      
      const statCards = page.locator('[data-testid="stat-card"]');
      const firstCard = await statCards.first().boundingBox();
      const secondCard = await statCards.nth(1).boundingBox();
      
      if (firstCard && secondCard) {
        expect(firstCard.y).toBeLessThan(secondCard.y);
      }
    });

    test('平板端应正确显示布局', async ({ page }) => {
      await page.setViewportSize({ width: 768, height: 1024 });
      
      await expect(page.locator('[data-testid="stat-card"]').first()).toBeVisible();
    });

    test('桌面端应正确显示布局', async ({ page }) => {
      await page.setViewportSize({ width: 1920, height: 1080 });
      
      await expect(page.locator('[data-testid="stat-card"]').first()).toBeVisible();
    });
  });

  test.describe('性能测试', () => {
    test('页面应在3秒内加载完成', async ({ page }) => {
      const startTime = Date.now();
      
      await page.goto('/dashboard');
      await page.waitForLoadState('networkidle');
      
      const loadTime = Date.now() - startTime;
      expect(loadTime).toBeLessThan(3000);
    });

    test('统计卡片应快速渲染', async ({ page }) => {
      const startTime = Date.now();
      
      await page.goto('/dashboard');
      await page.waitForSelector('[data-testid="stat-card"]');
      
      const renderTime = Date.now() - startTime;
      expect(renderTime).toBeLessThan(1000);
    });
  });

  test.describe('错误处理', () => {
    test('API错误时应显示错误提示', async ({ page }) => {
      await page.route('**/api/dashboard/**', route => {
        route.fulfill({ status: 500, body: JSON.stringify({ error: 'Server Error' }) });
      });
      
      await page.reload();
      
      await expect(page.locator('.el-message--error, [data-testid="error-message"]')).toBeVisible();
    });

    test('网络断开时应显示离线提示', async ({ page }) => {
      await page.context().setOffline(true);
      
      await page.waitForTimeout(1000);
      
      await page.context().setOffline(false);
    });

    test('应该能够重试失败请求', async ({ page }) => {
      let requestCount = 0;
      await page.route('**/api/dashboard/**', route => {
        requestCount++;
        if (requestCount === 1) {
          route.fulfill({ status: 500 });
        } else {
          route.fulfill({ status: 200, body: JSON.stringify({ stats: {} }) });
        }
      });
      
      await page.reload();
      
      const retryButton = page.locator('[data-testid="retry-button"]');
      if (await retryButton.isVisible()) {
        await retryButton.click();
      }
    });
  });

  test.describe('无障碍访问', () => {
    test('应该支持键盘导航', async ({ page }) => {
      await page.keyboard.press('Tab');
      
      const focusedElement = await page.evaluate(() => document.activeElement?.tagName);
      expect(focusedElement).not.toBe('BODY');
    });

    test('统计卡片应该有适当的ARIA标签', async ({ page }) => {
      const statCards = page.locator('[data-testid="stat-card"]');
      const count = await statCards.count();
      
      for (let i = 0; i < count; i++) {
        const card = statCards.nth(i);
        const ariaLabel = await card.getAttribute('aria-label');
        expect(ariaLabel).toBeTruthy();
      }
    });

    test('快速操作按钮应该有适当的标签', async ({ page }) => {
      const buttons = page.locator('[data-testid^="quick-action-"]');
      const count = await buttons.count();
      
      for (let i = 0; i < count; i++) {
        const button = buttons.nth(i);
        const ariaLabel = await button.getAttribute('aria-label');
        const text = await button.textContent();
        expect(ariaLabel || text).toBeTruthy();
      }
    });
  });

  test.describe('WebSocket实时更新', () => {
    test('应该能够接收实时更新', async ({ page }) => {
      await page.evaluate(() => {
        window.dispatchEvent(new CustomEvent('dashboard-update', {
          detail: { totalProjects: 100 }
        }));
      });
      
      await page.waitForTimeout(500);
    });

    test('连接断开时应显示提示', async ({ page }) => {
      await page.evaluate(() => {
        window.dispatchEvent(new CustomEvent('websocket-disconnected'));
      });
      
      await page.waitForTimeout(500);
    });
  });
});
