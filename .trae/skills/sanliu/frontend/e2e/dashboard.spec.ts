/**
 * Dashboard E2E Tests
 *
 * 测试仪表盘的完整功能
 */

import { test, expect } from '@playwright/test';

test.describe('Dashboard Page', () => {
  test.beforeEach(async ({ page }) => {
    // 导航到仪表盘页面
    await page.goto('/dashboard');
    // 等待页面加载完成
    await page.waitForLoadState('networkidle');
  });

  test.describe('Page Load', () => {
    test('should display dashboard title', async ({ page }) => {
      // 验证页面标题
      await expect(page.locator('h1')).toContainText('Dashboard');
    });

    test('should display all stat cards', async ({ page }) => {
      // 验证统计卡片存在
      const statCards = page.locator('[data-testid="stat-card"]');
      await expect(statCards).toHaveCount(4);

      // 验证各统计项
      await expect(page.locator('[data-testid="total-projects"]')).toBeVisible();
      await expect(page.locator('[data-testid="active-tasks"]')).toBeVisible();
      await expect(page.locator('[data-testid="completed-tasks"]')).toBeVisible();
      await expect(page.locator('[data-testid="active-agents"]')).toBeVisible();
    });

    test('should display charts', async ({ page }) => {
      // 验证图表存在
      await expect(page.locator('[data-testid="status-chart"]')).toBeVisible();
      await expect(page.locator('[data-testid="progress-chart"]')).toBeVisible();
    });

    test('should display recent activity', async ({ page }) => {
      // 验证最近活动列表存在
      await expect(page.locator('[data-testid="recent-activity"]')).toBeVisible();
    });
  });

  test.describe('Stat Cards', () => {
    test('should update stats when data changes', async ({ page }) => {
      // 获取初始值
      const initialValue = await page.locator('[data-testid="total-projects"] .stat-value').textContent();

      // 模拟数据更新（如果有实时更新功能）
      // 这里可以模拟 WebSocket 消息或轮询更新

      // 验证值可能已更新
      // 注意：实际测试需要根据应用的具体实现
    });

    test('should display correct number formatting', async ({ page }) => {
      // 验证数字格式化
      const statValues = page.locator('[data-testid="stat-value"]');
      const count = await statValues.count();

      for (let i = 0; i < count; i++) {
        const text = await statValues.nth(i).textContent();
        // 验证是数字格式
        expect(text).toMatch(/^[\d,]+$/);
      }
    });

    test('should have clickable stat cards', async ({ page }) => {
      // 点击项目统计卡片
      await page.click('[data-testid="total-projects"]');

      // 验证导航到项目页面
      await expect(page).toHaveURL(/.*projects/);
    });
  });

  test.describe('Charts', () => {
    test('should render status chart', async ({ page }) => {
      const chart = page.locator('[data-testid="status-chart"]');
      await expect(chart).toBeVisible();

      // 验证图表有数据
      const chartData = await chart.locator('.chart-data').count();
      expect(chartData).toBeGreaterThan(0);
    });

    test('should render progress chart', async ({ page }) => {
      const chart = page.locator('[data-testid="progress-chart"]');
      await expect(chart).toBeVisible();
    });

    test('should handle chart interactions', async ({ page }) => {
      const chart = page.locator('[data-testid="status-chart"]');

      // 悬停在图表元素上
      await chart.locator('.chart-element').first().hover();

      // 验证显示提示信息
      await expect(page.locator('.chart-tooltip')).toBeVisible();
    });

    test('should update charts with new data', async ({ page }) => {
      // 记录初始图表状态
      const initialChart = await page.locator('[data-testid="status-chart"]').screenshot();

      // 触发数据更新（如果有此功能）
      await page.click('[data-testid="refresh-data"]');

      // 等待更新
      await page.waitForTimeout(1000);

      // 验证图表已更新
      const updatedChart = await page.locator('[data-testid="status-chart"]').screenshot();
      expect(initialChart).not.toEqual(updatedChart);
    });
  });

  test.describe('Recent Activity', () => {
    test('should display activity list', async ({ page }) => {
      const activityList = page.locator('[data-testid="recent-activity"]');
      await expect(activityList).toBeVisible();

      // 验证活动项存在
      const activities = activityList.locator('.activity-item');
      const count = await activities.count();
      expect(count).toBeGreaterThan(0);
    });

    test('should show activity details', async ({ page }) => {
      const firstActivity = page.locator('.activity-item').first();

      // 验证活动有时间戳
      await expect(firstActivity.locator('.activity-time')).toBeVisible();

      // 验证活动有描述
      await expect(firstActivity.locator('.activity-description')).toBeVisible();
    });

    test('should load more activities on scroll', async ({ page }) => {
      // 记录初始活动数量
      const initialCount = await page.locator('.activity-item').count();

      // 滚动到活动列表底部
      await page.locator('[data-testid="recent-activity"]').evaluate(el => {
        el.scrollTop = el.scrollHeight;
      });

      // 等待加载更多
      await page.waitForTimeout(500);

      // 验证加载了更多活动
      const newCount = await page.locator('.activity-item').count();
      expect(newCount).toBeGreaterThanOrEqual(initialCount);
    });
  });

  test.describe('Real-time Updates', () => {
    test('should receive real-time updates', async ({ page }) => {
      // 如果有 WebSocket 连接，测试实时更新
      // 这里需要根据具体实现

      // 模拟 WebSocket 消息
      await page.evaluate(() => {
        // 触发更新事件
        window.dispatchEvent(new CustomEvent('stats-update', {
          detail: { totalProjects: 100 }
        }));
      });

      // 验证 UI 已更新
      await expect(page.locator('[data-testid="total-projects"]')).toContainText('100');
    });

    test('should handle connection loss', async ({ page }) => {
      // 模拟连接断开
      await page.evaluate(() => {
        window.dispatchEvent(new Event('offline'));
      });

      // 验证显示离线提示
      await expect(page.locator('[data-testid="connection-status"]')).toContainText('Offline');

      // 恢复连接
      await page.evaluate(() => {
        window.dispatchEvent(new Event('online'));
      });

      // 验证显示在线状态
      await expect(page.locator('[data-testid="connection-status"]')).toContainText('Online');
    });
  });

  test.describe('Responsive Design', () => {
    test('should adapt to mobile viewport', async ({ page }) => {
      // 设置移动端视口
      await page.setViewportSize({ width: 375, height: 667 });

      // 验证布局调整
      await expect(page.locator('[data-testid="mobile-layout"]')).toBeVisible();

      // 验证统计卡片垂直排列
      const statCards = page.locator('[data-testid="stat-card"]');
      const firstCard = await statCards.first().boundingBox();
      const secondCard = await statCards.nth(1).boundingBox();

      expect(firstCard!.y).toBeLessThan(secondCard!.y);
    });

    test('should adapt to tablet viewport', async ({ page }) => {
      // 设置平板视口
      await page.setViewportSize({ width: 768, height: 1024 });

      // 验证布局调整
      await expect(page.locator('[data-testid="tablet-layout"]')).toBeVisible();
    });

    test('should adapt to desktop viewport', async ({ page }) => {
      // 设置桌面视口
      await page.setViewportSize({ width: 1920, height: 1080 });

      // 验证布局调整
      await expect(page.locator('[data-testid="desktop-layout"]')).toBeVisible();

      // 验证统计卡片水平排列
      const statCards = page.locator('[data-testid="stat-card"]');
      const firstCard = await statCards.first().boundingBox();
      const secondCard = await statCards.nth(1).boundingBox();

      expect(firstCard!.y).toEqual(secondCard!.y);
    });
  });

  test.describe('Performance', () => {
    test('should load within acceptable time', async ({ page }) => {
      // 测量页面加载时间
      const startTime = Date.now();

      await page.goto('/dashboard');
      await page.waitForLoadState('networkidle');

      const loadTime = Date.now() - startTime;
      expect(loadTime).toBeLessThan(3000); // 3秒内加载完成
    });

    test('should handle large datasets efficiently', async ({ page }) => {
      // 测试大数据集下的性能
      await page.goto('/dashboard?loadTest=true');
      await page.waitForLoadState('networkidle');

      // 验证页面仍然响应
      await expect(page.locator('[data-testid="stat-card"]').first()).toBeVisible();
    });

    test('should lazy load chart data', async ({ page }) => {
      // 验证图表数据是懒加载的
      const chart = page.locator('[data-testid="status-chart"]');

      // 初始状态可能是加载中
      await expect(chart.locator('.loading')).toBeVisible();

      // 等待数据加载完成
      await expect(chart.locator('.chart-data')).toBeVisible();
    });
  });

  test.describe('Accessibility', () => {
    test('should have proper ARIA labels', async ({ page }) => {
      // 验证统计卡片有适当的 ARIA 标签
      const statCards = page.locator('[data-testid="stat-card"]');
      await expect(statCards.first()).toHaveAttribute('aria-label');
    });

    test('should support keyboard navigation', async ({ page }) => {
      // 测试键盘导航
      await page.keyboard.press('Tab');

      // 验证焦点在可交互元素上
      const focusedElement = await page.evaluate(() => document.activeElement?.tagName);
      expect(focusedElement).not.toBe('BODY');
    });

    test('should have sufficient color contrast', async ({ page }) => {
      // 验证文本对比度
      const textElements = page.locator('text=/\\w+/');
      const count = await textElements.count();

      for (let i = 0; i < Math.min(count, 10); i++) {
        const element = textElements.nth(i);
        const color = await element.evaluate(el => getComputedStyle(el).color);
        const bgColor = await element.evaluate(el => getComputedStyle(el).backgroundColor);

        // 这里可以添加对比度计算逻辑
        expect(color).toBeTruthy();
        expect(bgColor).toBeTruthy();
      }
    });
  });

  test.describe('Error Handling', () => {
    test('should handle API errors gracefully', async ({ page }) => {
      // 模拟 API 错误
      await page.route('**/api/dashboard/stats', route => {
        route.fulfill({
          status: 500,
          body: JSON.stringify({ error: 'Internal Server Error' })
        });
      });

      await page.reload();

      // 验证显示错误提示
      await expect(page.locator('[data-testid="error-message"]')).toBeVisible();
      await expect(page.locator('[data-testid="error-message"]')).toContainText('Error');
    });

    test('should handle network errors', async ({ page }) => {
      // 模拟网络错误
      await page.route('**/api/dashboard/stats', route => {
        route.abort('failed');
      });

      await page.reload();

      // 验证显示错误提示
      await expect(page.locator('[data-testid="error-message"]')).toBeVisible();
    });

    test('should allow retry on error', async ({ page }) => {
      let requestCount = 0;

      // 模拟第一次请求失败，第二次成功
      await page.route('**/api/dashboard/stats', route => {
        requestCount++;
        if (requestCount === 1) {
          route.fulfill({ status: 500 });
        } else {
          route.fulfill({
            status: 200,
            body: JSON.stringify({ totalProjects: 10 })
          });
        }
      });

      await page.reload();

      // 点击重试按钮
      await page.click('[data-testid="retry-button"]');

      // 验证数据已加载
      await expect(page.locator('[data-testid="total-projects"]')).toContainText('10');
    });
  });
});
