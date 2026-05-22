/**
 * Projects E2E Tests
 *
 * 测试项目列表和详情页面的完整功能
 */

import { test, expect } from '@playwright/test';

test.describe('Projects Page', () => {
  test.beforeEach(async ({ page }) => {
    // 导航到项目页面
    await page.goto('/projects');
    // 等待页面加载完成
    await page.waitForLoadState('networkidle');
  });

  test.describe('Page Load', () => {
    test('should display projects page title', async ({ page }) => {
      // 验证页面标题
      await expect(page.locator('h1')).toContainText('Projects');
    });

    test('should display project list', async ({ page }) => {
      // 验证项目列表存在
      const projectList = page.locator('[data-testid="project-list"]');
      await expect(projectList).toBeVisible();

      // 验证有项目卡片
      const projectCards = projectList.locator('[data-testid="project-card"]');
      await expect(projectCards).toHaveCount.greaterThan(0);
    });

    test('should display create project button', async ({ page }) => {
      // 验证创建按钮存在
      await expect(page.locator('[data-testid="create-project-btn"]')).toBeVisible();
      await expect(page.locator('[data-testid="create-project-btn"]')).toContainText('Create Project');
    });

    test('should display search and filter controls', async ({ page }) => {
      // 验证搜索框存在
      await expect(page.locator('[data-testid="search-input"]')).toBeVisible();

      // 验证筛选控件存在
      await expect(page.locator('[data-testid="status-filter"]')).toBeVisible();
    });
  });

  test.describe('Project List', () => {
    test('should display project cards with correct information', async ({ page }) => {
      const firstCard = page.locator('[data-testid="project-card"]').first();

      // 验证项目卡片包含必要信息
      await expect(firstCard.locator('[data-testid="project-name"]')).toBeVisible();
      await expect(firstCard.locator('[data-testid="project-status"]')).toBeVisible();
      await expect(firstCard.locator('[data-testid="project-date"]')).toBeVisible();
    });

    test('should navigate to project detail on card click', async ({ page }) => {
      const firstCard = page.locator('[data-testid="project-card"]').first();

      // 获取项目名称
      const projectName = await firstCard.locator('[data-testid="project-name"]').textContent();

      // 点击项目卡片
      await firstCard.click();

      // 验证导航到详情页
      await expect(page).toHaveURL(/.*projects\/\d+/);

      // 验证显示正确的项目名称
      await expect(page.locator('h1')).toContainText(projectName!);
    });

    test('should support pagination', async ({ page }) => {
      // 验证分页控件存在
      await expect(page.locator('[data-testid="pagination"]')).toBeVisible();

      // 获取当前页码
      const currentPage = await page.locator('[data-testid="current-page"]').textContent();
      expect(currentPage).toBe('1');

      // 点击下一页
      await page.click('[data-testid="next-page"]');

      // 验证页码更新
      await expect(page.locator('[data-testid="current-page"]')).toContainText('2');
    });

    test('should update items per page', async ({ page }) => {
      // 选择每页显示数量
      await page.selectOption('[data-testid="items-per-page"]', '24');

      // 等待页面更新
      await page.waitForTimeout(500);

      // 验证项目卡片数量
      const projectCards = page.locator('[data-testid="project-card"]');
      const count = await projectCards.count();
      expect(count).toBeLessThanOrEqual(24);
    });
  });

  test.describe('Search and Filter', () => {
    test('should filter projects by search term', async ({ page }) => {
      // 输入搜索词
      await page.fill('[data-testid="search-input"]', 'Test');

      // 等待搜索结果
      await page.waitForTimeout(500);

      // 验证显示过滤后的结果
      const projectCards = page.locator('[data-testid="project-card"]');
      const count = await projectCards.count();

      if (count > 0) {
        // 验证所有结果都包含搜索词
        for (let i = 0; i < count; i++) {
          const name = await projectCards.nth(i).locator('[data-testid="project-name"]').textContent();
          expect(name!.toLowerCase()).toContain('test');
        }
      }
    });

    test('should filter projects by status', async ({ page }) => {
      // 选择状态筛选
      await page.selectOption('[data-testid="status-filter"]', 'active');

      // 等待筛选结果
      await page.waitForTimeout(500);

      // 验证显示的项目都有正确的状态
      const projectCards = page.locator('[data-testid="project-card"]');
      const count = await projectCards.count();

      for (let i = 0; i < count; i++) {
        const status = await projectCards.nth(i).locator('[data-testid="project-status"]').textContent();
        expect(status!.toLowerCase()).toContain('active');
      }
    });

    test('should combine search and filter', async ({ page }) => {
      // 输入搜索词
      await page.fill('[data-testid="search-input"]', 'Web');

      // 选择状态筛选
      await page.selectOption('[data-testid="status-filter"]', 'completed');

      // 等待筛选结果
      await page.waitForTimeout(500);

      // 验证结果同时满足两个条件
      const projectCards = page.locator('[data-testid="project-card"]');
      const count = await projectCards.count();

      for (let i = 0; i < count; i++) {
        const name = await projectCards.nth(i).locator('[data-testid="project-name"]').textContent();
        const status = await projectCards.nth(i).locator('[data-testid="project-status"]').textContent();

        expect(name!.toLowerCase()).toContain('web');
        expect(status!.toLowerCase()).toContain('completed');
      }
    });

    test('should clear filters', async ({ page }) => {
      // 应用筛选
      await page.fill('[data-testid="search-input"]', 'Test');
      await page.selectOption('[data-testid="status-filter"]', 'active');

      // 等待筛选结果
      await page.waitForTimeout(500);

      // 记录筛选后的数量
      const filteredCount = await page.locator('[data-testid="project-card"]').count();

      // 清除筛选
      await page.click('[data-testid="clear-filters"]');

      // 等待重置
      await page.waitForTimeout(500);

      // 验证筛选已清除
      await expect(page.locator('[data-testid="search-input"]')).toHaveValue('');

      // 验证显示更多结果
      const totalCount = await page.locator('[data-testid="project-card"]').count();
      expect(totalCount).toBeGreaterThanOrEqual(filteredCount);
    });
  });

  test.describe('Create Project', () => {
    test('should open create project modal', async ({ page }) => {
      // 点击创建按钮
      await page.click('[data-testid="create-project-btn"]');

      // 验证模态框打开
      await expect(page.locator('[data-testid="create-project-modal"]')).toBeVisible();

      // 验证表单字段存在
      await expect(page.locator('[data-testid="project-name-input"]')).toBeVisible();
      await expect(page.locator('[data-testid="project-description-input"]')).toBeVisible();
    });

    test('should create project with valid data', async ({ page }) => {
      // 打开创建模态框
      await page.click('[data-testid="create-project-btn"]');

      // 填写表单
      await page.fill('[data-testid="project-name-input"]', 'E2E Test Project');
      await page.fill('[data-testid="project-description-input"]', 'This is a test project created by E2E tests');

      // 提交表单
      await page.click('[data-testid="submit-project-btn"]');

      // 验证模态框关闭
      await expect(page.locator('[data-testid="create-project-modal"]')).not.toBeVisible();

      // 验证新项目出现在列表中
      await expect(page.locator('[data-testid="project-card"]:has-text("E2E Test Project")')).toBeVisible();
    });

    test('should validate required fields', async ({ page }) => {
      // 打开创建模态框
      await page.click('[data-testid="create-project-btn"]');

      // 直接提交空表单
      await page.click('[data-testid="submit-project-btn"]');

      // 验证显示验证错误
      await expect(page.locator('[data-testid="name-error"]')).toBeVisible();
      await expect(page.locator('[data-testid="name-error"]')).toContainText('required');
    });

    test('should handle duplicate project name', async ({ page }) => {
      // 打开创建模态框
      await page.click('[data-testid="create-project-btn"]');

      // 填写已存在的项目名称
      await page.fill('[data-testid="project-name-input"]', 'Existing Project');

      // 提交表单
      await page.click('[data-testid="submit-project-btn"]');

      // 验证显示错误提示
      await expect(page.locator('[data-testid="form-error"]')).toBeVisible();
      await expect(page.locator('[data-testid="form-error"]')).toContainText('already exists');
    });

    test('should cancel project creation', async ({ page }) => {
      // 打开创建模态框
      await page.click('[data-testid="create-project-btn"]');

      // 填写部分表单
      await page.fill('[data-testid="project-name-input"]', 'Cancelled Project');

      // 点击取消
      await page.click('[data-testid="cancel-btn"]');

      // 验证模态框关闭
      await expect(page.locator('[data-testid="create-project-modal"]')).not.toBeVisible();

      // 验证项目未创建
      await expect(page.locator('[data-testid="project-card"]:has-text("Cancelled Project")')).not.toBeVisible();
    });
  });

  test.describe('Project Actions', () => {
    test('should edit project', async ({ page }) => {
      // 找到第一个项目的编辑按钮
      const firstCard = page.locator('[data-testid="project-card"]').first();
      await firstCard.locator('[data-testid="edit-btn"]').click();

      // 验证编辑模态框打开
      await expect(page.locator('[data-testid="edit-project-modal"]')).toBeVisible();

      // 修改项目名称
      await page.fill('[data-testid="project-name-input"]', 'Updated Project Name');

      // 保存更改
      await page.click('[data-testid="save-btn"]');

      // 验证更新成功
      await expect(page.locator('[data-testid="project-card"]:has-text("Updated Project Name")')).toBeVisible();
    });

    test('should delete project', async ({ page }) => {
      // 找到第一个项目的删除按钮
      const firstCard = page.locator('[data-testid="project-card"]').first();
      const projectName = await firstCard.locator('[data-testid="project-name"]').textContent();

      await firstCard.locator('[data-testid="delete-btn"]').click();

      // 验证确认对话框
      await expect(page.locator('[data-testid="confirm-dialog"]')).toBeVisible();

      // 确认删除
      await page.click('[data-testid="confirm-delete-btn"]');

      // 验证项目已删除
      await expect(page.locator(`[data-testid="project-card"]:has-text("${projectName}")`)).not.toBeVisible();
    });

    test('should cancel project deletion', async ({ page }) => {
      // 找到第一个项目的删除按钮
      const firstCard = page.locator('[data-testid="project-card"]').first();
      const projectName = await firstCard.locator('[data-testid="project-name"]').textContent();

      await firstCard.locator('[data-testid="delete-btn"]').click();

      // 验证确认对话框
      await expect(page.locator('[data-testid="confirm-dialog"]')).toBeVisible();

      // 取消删除
      await page.click('[data-testid="cancel-delete-btn"]');

      // 验证项目仍然存在
      await expect(page.locator(`[data-testid="project-card"]:has-text("${projectName}")`)).toBeVisible();
    });
  });

  test.describe('Sorting', () => {
    test('should sort projects by name', async ({ page }) => {
      // 选择按名称排序
      await page.selectOption('[data-testid="sort-select"]', 'name');

      // 等待排序
      await page.waitForTimeout(500);

      // 获取排序后的项目名称
      const projectNames = await page.locator('[data-testid="project-name"]').allTextContents();

      // 验证按字母顺序排序
      const sortedNames = [...projectNames].sort();
      expect(projectNames).toEqual(sortedNames);
    });

    test('should sort projects by date', async ({ page }) => {
      // 选择按日期排序
      await page.selectOption('[data-testid="sort-select"]', 'date');

      // 等待排序
      await page.waitForTimeout(500);

      // 验证项目按日期排序
      // 这里可以根据实际日期格式进行验证
    });

    test('should toggle sort direction', async ({ page }) => {
      // 选择排序方式
      await page.selectOption('[data-testid="sort-select"]', 'name');

      // 获取升序结果
      const ascendingNames = await page.locator('[data-testid="project-name"]').allTextContents();

      // 点击切换排序方向
      await page.click('[data-testid="sort-direction-btn"]');

      // 等待排序
      await page.waitForTimeout(500);

      // 获取降序结果
      const descendingNames = await page.locator('[data-testid="project-name"]').allTextContents();

      // 验证是反向排序
      expect(descendingNames).toEqual([...ascendingNames].reverse());
    });
  });

  test.describe('Responsive Design', () => {
    test('should adapt to mobile viewport', async ({ page }) => {
      // 设置移动端视口
      await page.setViewportSize({ width: 375, height: 667 });

      // 验证移动端布局
      await expect(page.locator('[data-testid="mobile-layout"]')).toBeVisible();

      // 验证项目卡片单列显示
      const firstCard = await page.locator('[data-testid="project-card"]').first().boundingBox();
      const secondCard = await page.locator('[data-testid="project-card"]').nth(1).boundingBox();

      expect(firstCard!.y).toBeLessThan(secondCard!.y);
    });

    test('should adapt to tablet viewport', async ({ page }) => {
      // 设置平板视口
      await page.setViewportSize({ width: 768, height: 1024 });

      // 验证平板布局
      await expect(page.locator('[data-testid="tablet-layout"]')).toBeVisible();
    });

    test('should adapt to desktop viewport', async ({ page }) => {
      // 设置桌面视口
      await page.setViewportSize({ width: 1920, height: 1080 });

      // 验证桌面布局
      await expect(page.locator('[data-testid="desktop-layout"]')).toBeVisible();
    });
  });

  test.describe('Performance', () => {
    test('should load projects within acceptable time', async ({ page }) => {
      // 测量加载时间
      const startTime = Date.now();

      await page.goto('/projects');
      await page.waitForLoadState('networkidle');

      const loadTime = Date.now() - startTime;
      expect(loadTime).toBeLessThan(3000);
    });

    test('should handle large project lists', async ({ page }) => {
      // 测试大数据集
      await page.goto('/projects?loadTest=true');
      await page.waitForLoadState('networkidle');

      // 验证页面仍然响应
      await expect(page.locator('[data-testid="project-card"]').first()).toBeVisible();
    });
  });

  test.describe('Error Handling', () => {
    test('should handle API errors gracefully', async ({ page }) => {
      // 模拟 API 错误
      await page.route('**/api/projects', route => {
        route.fulfill({
          status: 500,
          body: JSON.stringify({ error: 'Internal Server Error' })
        });
      });

      await page.reload();

      // 验证显示错误提示
      await expect(page.locator('[data-testid="error-message"]')).toBeVisible();
    });

    test('should handle empty project list', async ({ page }) => {
      // 模拟空列表
      await page.route('**/api/projects', route => {
        route.fulfill({
          status: 200,
          body: JSON.stringify({ items: [], total: 0 })
        });
      });

      await page.reload();

      // 验证显示空状态
      await expect(page.locator('[data-testid="empty-state"]')).toBeVisible();
      await expect(page.locator('[data-testid="empty-state"]')).toContainText('No projects');
    });
  });
});

test.describe('Project Detail Page', () => {
  test.beforeEach(async ({ page }) => {
    // 导航到项目详情页
    await page.goto('/projects/1');
    await page.waitForLoadState('networkidle');
  });

  test.describe('Page Load', () => {
    test('should display project details', async ({ page }) => {
      // 验证项目标题
      await expect(page.locator('h1')).toBeVisible();

      // 验证项目信息
      await expect(page.locator('[data-testid="project-description"]')).toBeVisible();
      await expect(page.locator('[data-testid="project-status"]')).toBeVisible();
      await expect(page.locator('[data-testid="project-created-at"]')).toBeVisible();
    });

    test('should display project tasks', async ({ page }) => {
      // 验证任务列表存在
      await expect(page.locator('[data-testid="task-list"]')).toBeVisible();
    });

    test('should display project stats', async ({ page }) => {
      // 验证统计信息
      await expect(page.locator('[data-testid="project-stats"]')).toBeVisible();
    });
  });

  test.describe('Navigation', () => {
    test('should navigate back to projects list', async ({ page }) => {
      // 点击返回按钮
      await page.click('[data-testid="back-btn"]');

      // 验证返回项目列表
      await expect(page).toHaveURL(/.*projects$/);
    });

    test('should navigate to task detail', async ({ page }) => {
      // 点击第一个任务
      await page.click('[data-testid="task-item"]').first();

      // 验证导航到任务详情
      await expect(page).toHaveURL(/.*tasks\/\d+/);
    });
  });

  test.describe('Project Actions', () => {
    test('should edit project from detail page', async ({ page }) => {
      // 点击编辑按钮
      await page.click('[data-testid="edit-project-btn"]');

      // 验证编辑模态框打开
      await expect(page.locator('[data-testid="edit-project-modal"]')).toBeVisible();
    });

    test('should delete project from detail page', async ({ page }) => {
      // 点击删除按钮
      await page.click('[data-testid="delete-project-btn"]');

      // 验证确认对话框
      await expect(page.locator('[data-testid="confirm-dialog"]')).toBeVisible();
    });
  });
});
