/**
 * E2E测试 - 项目管理流程
 * 测试项目创建、编辑、删除等完整用户流程
 */

import { test, expect, Page } from '@playwright/test';

test.describe('项目管理流程', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
  });

  test('创建新项目完整流程', async ({ page }) => {
    await page.click('[data-testid="new-project-button"]');
    
    await expect(page.locator('[data-testid="project-form"]')).toBeVisible();
    
    await page.fill('[data-testid="project-name"]', 'E2E测试项目');
    await page.fill('[data-testid="project-description"]', '这是一个E2E测试项目');
    
    await page.click('[data-testid="tech-stack-dropdown"]');
    await page.click('[data-testid="tech-option-Python"]');
    await page.click('[data-testid="tech-option-FastAPI"]');
    
    await page.click('[data-testid="submit-project"]');
    
    await expect(page.locator('.toast-success')).toBeVisible();
    await expect(page.locator('[data-testid="project-card"]')).toContainText('E2E测试项目');
  });

  test('编辑项目流程', async ({ page }) => {
    await page.click('[data-testid="project-card"]:first-child');
    await page.click('[data-testid="edit-project-button"]');
    
    await page.fill('[data-testid="project-name"]', '更新后的项目名');
    await page.click('[data-testid="submit-project"]');
    
    await expect(page.locator('.toast-success')).toBeVisible();
    await expect(page.locator('[data-testid="project-title"]')).toContainText('更新后的项目名');
  });

  test('删除项目流程', async ({ page }) => {
    await page.click('[data-testid="project-card"]:first-child');
    await page.click('[data-testid="delete-project-button"]');
    
    await expect(page.locator('[data-testid="confirm-dialog"]')).toBeVisible();
    await page.click('[data-testid="confirm-delete"]');
    
    await expect(page.locator('.toast-success')).toBeVisible();
  });

  test('项目状态变更流程', async ({ page }) => {
    await page.click('[data-testid="project-card"]:first-child');
    
    await page.click('[data-testid="status-dropdown"]');
    await page.click('[data-testid="status-DEVELOPMENT"]');
    
    await expect(page.locator('[data-testid="project-status"]')).toContainText('开发中');
  });

  test('项目搜索流程', async ({ page }) => {
    await page.fill('[data-testid="search-input"]', '测试');
    await page.press('[data-testid="search-input"]', 'Enter');
    
    await expect(page.locator('[data-testid="search-results"]')).toBeVisible();
    
    const results = await page.locator('[data-testid="project-card"]').count();
    expect(results).toBeGreaterThan(0);
  });

  test('项目分页流程', async ({ page }) => {
    await page.click('[data-testid="pagination-next"]');
    
    await expect(page.locator('[data-testid="page-indicator"]')).toContainText('2');
    
    await page.click('[data-testid="pagination-prev"]');
    await expect(page.locator('[data-testid="page-indicator"]')).toContainText('1');
  });
});

test.describe('任务管理流程', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
    await page.click('[data-testid="project-card"]:first-child');
  });

  test('创建任务流程', async ({ page }) => {
    await page.click('[data-testid="new-task-button"]');
    
    await page.fill('[data-testid="task-title"]', 'E2E测试任务');
    await page.fill('[data-testid="task-description"]', '任务描述');
    await page.selectOption('[data-testid="task-priority"]', 'high');
    
    await page.click('[data-testid="submit-task"]');
    
    await expect(page.locator('.toast-success')).toBeVisible();
    await expect(page.locator('[data-testid="task-item"]')).toContainText('E2E测试任务');
  });

  test('任务状态拖拽更新', async ({ page }) => {
    const task = page.locator('[data-testid="task-item"]:first-child');
    const targetColumn = page.locator('[data-testid="column-in-progress"]');
    
    await task.dragTo(targetColumn);
    
    await expect(page.locator('[data-testid="column-in-progress"] [data-testid="task-item"]')).toBeVisible();
  });

  test('任务分配流程', async ({ page }) => {
    await page.click('[data-testid="task-item"]:first-child');
    await page.click('[data-testid="assign-task-button"]');
    
    await page.click('[data-testid="agent-dropdown"]');
    await page.click('[data-testid="agent-option"]:first-child');
    
    await page.click('[data-testid="confirm-assign"]');
    
    await expect(page.locator('[data-testid="assigned-agent"]')).toBeVisible();
  });

  test('任务筛选流程', async ({ page }) => {
    await page.selectOption('[data-testid="filter-priority"]', 'high');
    
    const tasks = await page.locator('[data-testid="task-item"]').count();
    
    for (let i = 0; i < tasks; i++) {
      const priority = await page.locator('[data-testid="task-item"]').nth(i)
        .locator('[data-testid="task-priority-badge"]').textContent();
      expect(priority).toContain('高');
    }
  });
});

test.describe('里程碑管理流程', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
    await page.click('[data-testid="project-card"]:first-child');
    await page.click('[data-testid="milestones-tab"]');
  });

  test('创建里程碑流程', async ({ page }) => {
    await page.click('[data-testid="new-milestone-button"]');
    
    await page.fill('[data-testid="milestone-name"]', 'E2E里程碑');
    await page.fill('[data-testid="milestone-description"]', '里程碑描述');
    await page.fill('[data-testid="milestone-date"]', '2025-12-31');
    
    await page.click('[data-testid="submit-milestone"]');
    
    await expect(page.locator('.toast-success')).toBeVisible();
    await expect(page.locator('[data-testid="milestone-card"]')).toContainText('E2E里程碑');
  });

  test('完成里程碑流程', async ({ page }) => {
    await page.click('[data-testid="milestone-card"]:first-child');
    await page.click('[data-testid="complete-milestone-button"]');
    
    await expect(page.locator('[data-testid="milestone-status"]')).toContainText('已完成');
  });
});

test.describe('报告查看流程', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
    await page.click('[data-testid="project-card"]:first-child');
  });

  test('查看进度报告', async ({ page }) => {
    await page.click('[data-testid="reports-tab"]');
    await page.click('[data-testid="progress-report"]');
    
    await expect(page.locator('[data-testid="report-content"]')).toBeVisible();
    await expect(page.locator('[data-testid="completion-rate"]')).toBeVisible();
  });

  test('导出报告', async ({ page }) => {
    await page.click('[data-testid="reports-tab"]');
    await page.click('[data-testid="export-report-button"]');
    
    await page.click('[data-testid="export-format-markdown"]');
    await page.click('[data-testid="confirm-export"]');
    
    const download = await page.waitForEvent('download');
    expect(download.suggestedFilename()).toContain('.md');
  });
});

test.describe('错误处理流程', () => {
  test('表单验证错误', async ({ page }) => {
    await page.goto('/');
    await page.click('[data-testid="new-project-button"]');
    
    await page.click('[data-testid="submit-project"]');
    
    await expect(page.locator('[data-testid="validation-error"]')).toBeVisible();
  });

  test('网络错误处理', async ({ page }) => {
    await page.route('**/api/projects/**', route => route.abort());
    
    await page.goto('/');
    
    await expect(page.locator('[data-testid="error-message"]')).toBeVisible();
  });

  test('404页面处理', async ({ page }) => {
    await page.goto('/nonexistent-page');
    
    await expect(page.locator('[data-testid="not-found-page"]')).toBeVisible();
  });
});

test.describe('响应式设计测试', () => {
  test('移动端布局', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 667 });
    await page.goto('/');
    
    await expect(page.locator('[data-testid="mobile-menu-button"]')).toBeVisible();
    
    await page.click('[data-testid="mobile-menu-button"]');
    await expect(page.locator('[data-testid="mobile-nav"]')).toBeVisible();
  });

  test('平板布局', async ({ page }) => {
    await page.setViewportSize({ width: 768, height: 1024 });
    await page.goto('/');
    
    await expect(page.locator('[data-testid="sidebar"]')).toBeVisible();
  });

  test('桌面布局', async ({ page }) => {
    await page.setViewportSize({ width: 1920, height: 1080 });
    await page.goto('/');
    
    await expect(page.locator('[data-testid="full-sidebar"]')).toBeVisible();
  });
});

test.describe('无障碍访问测试', () => {
  test('键盘导航', async ({ page }) => {
    await page.goto('/');
    
    await page.keyboard.press('Tab');
    await page.keyboard.press('Tab');
    
    const focusedElement = await page.evaluate(() => document.activeElement?.getAttribute('data-testid'));
    expect(focusedElement).toBeTruthy();
  });

  test('屏幕阅读器标签', async ({ page }) => {
    await page.goto('/');
    
    const buttons = await page.locator('button[aria-label]').count();
    expect(buttons).toBeGreaterThan(0);
    
    const images = await page.locator('img[alt]').count();
    expect(images).toBeGreaterThan(0);
  });
});

test.describe('性能测试', () => {
  test('页面加载性能', async ({ page }) => {
    const startTime = Date.now();
    await page.goto('/');
    const loadTime = Date.now() - startTime;
    
    expect(loadTime).toBeLessThan(3000);
  });

  test('列表渲染性能', async ({ page }) => {
    await page.goto('/');
    
    const startTime = Date.now();
    await page.waitForSelector('[data-testid="project-card"]');
    const renderTime = Date.now() - startTime;
    
    expect(renderTime).toBeLessThan(1000);
  });
});
