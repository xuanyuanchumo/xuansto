import { test, expect } from '@playwright/test';

test.describe('任务管理流程', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/tasks');
    await page.waitForLoadState('networkidle');
  });

  test.describe('页面加载', () => {
    test('应该显示任务管理页面标题', async ({ page }) => {
      await expect(page.locator('h2')).toContainText('任务管理');
    });

    test('应该显示任务列表', async ({ page }) => {
      await expect(page.locator('.task-list')).toBeVisible();
    });

    test('应该显示筛选控件', async ({ page }) => {
      await expect(page.locator('.task-filter')).toBeVisible();
    });
  });

  test.describe('任务筛选', () => {
    test('应该能够按状态筛选', async ({ page }) => {
      await page.selectOption('[data-testid="filter-status"]', 'pending');
      await page.waitForTimeout(500);

      const tasks = page.locator('[data-testid="task-item"]');
      const count = await tasks.count();

      for (let i = 0; i < count; i++) {
        const status = await tasks.nth(i).locator('[data-testid="task-status"]').textContent();
        expect(status).toContain('待处理');
      }
    });

    test('应该能够按优先级筛选', async ({ page }) => {
      await page.selectOption('[data-testid="filter-priority"]', 'high');
      await page.waitForTimeout(500);

      const tasks = page.locator('[data-testid="task-item"]');
      const count = await tasks.count();

      for (let i = 0; i < count; i++) {
        const priority = await tasks.nth(i).locator('[data-testid="task-priority"]').textContent();
        expect(priority).toContain('高');
      }
    });

    test('应该能够搜索任务', async ({ page }) => {
      await page.fill('[data-testid="search-text"]', '测试');
      await page.click('[data-testid="search-button"]');
      await page.waitForTimeout(500);

      const tasks = page.locator('[data-testid="task-item"]');
      const count = await tasks.count();

      for (let i = 0; i < count; i++) {
        const name = await tasks.nth(i).locator('[data-testid="task-name"]').textContent();
        expect(name?.toLowerCase()).toContain('测试');
      }
    });

    test('应该能够组合筛选条件', async ({ page }) => {
      await page.selectOption('[data-testid="filter-status"]', 'in_progress');
      await page.selectOption('[data-testid="filter-priority"]', 'high');
      await page.fill('[data-testid="search-text"]', '重要');
      await page.click('[data-testid="search-button"]');
      await page.waitForTimeout(500);

      await expect(page.locator('[data-testid="task-item"]')).toBeVisible();
    });

    test('应该能够清除筛选条件', async ({ page }) => {
      await page.selectOption('[data-testid="filter-status"]', 'pending');
      await page.selectOption('[data-testid="filter-priority"]', 'high');
      await page.fill('[data-testid="search-text"]', '测试');
      
      await page.click('[data-testid="clear-filters"]');
      
      await expect(page.locator('[data-testid="filter-status"]')).toHaveValue('');
      await expect(page.locator('[data-testid="filter-priority"]')).toHaveValue('');
      await expect(page.locator('[data-testid="search-text"]')).toHaveValue('');
    });
  });

  test.describe('任务列表', () => {
    test('应该显示任务基本信息', async ({ page }) => {
      const firstTask = page.locator('[data-testid="task-item"]').first();
      
      await expect(firstTask.locator('[data-testid="task-name"]')).toBeVisible();
      await expect(firstTask.locator('[data-testid="task-status"]')).toBeVisible();
      await expect(firstTask.locator('[data-testid="task-priority"]')).toBeVisible();
    });

    test('应该支持分页', async ({ page }) => {
      const pagination = page.locator('.el-pagination');
      if (await pagination.isVisible()) {
        await page.click('.el-pagination .btn-next');
        await page.waitForTimeout(500);
        
        await expect(page.locator('.el-pagination .el-pager li.is-active')).toContainText('2');
      }
    });

    test('应该能够修改每页显示数量', async ({ page }) => {
      const pageSizeSelector = page.locator('.el-pagination .el-pagination__sizes');
      if (await pageSizeSelector.isVisible()) {
        await pageSizeSelector.click();
        await page.click('.el-select-dropdown__item:has-text("20 条/页")');
        await page.waitForTimeout(500);
      }
    });

    test('应该支持排序', async ({ page }) => {
      const sortHeader = page.locator('[data-testid="sort-priority"]');
      if (await sortHeader.isVisible()) {
        await sortHeader.click();
        await page.waitForTimeout(500);
        
        const tasks = page.locator('[data-testid="task-item"]');
        const count = Math.min(await tasks.count(), 5);
        
        for (let i = 0; i < count - 1; i++) {
          const currentPriority = await tasks.nth(i).locator('[data-testid="task-priority"]').getAttribute('data-value');
          const nextPriority = await tasks.nth(i + 1).locator('[data-testid="task-priority"]').getAttribute('data-value');
          expect(Number(currentPriority)).toBeGreaterThanOrEqual(Number(nextPriority));
        }
      }
    });
  });

  test.describe('任务详情', () => {
    test('应该能够查看任务详情', async ({ page }) => {
      const firstTask = page.locator('[data-testid="task-item"]').first();
      await firstTask.click();
      
      await expect(page.locator('.task-detail-dialog')).toBeVisible();
      await expect(page.locator('[data-testid="task-detail-name"]')).toBeVisible();
      await expect(page.locator('[data-testid="task-detail-description"]')).toBeVisible();
    });

    test('应该显示任务的完整信息', async ({ page }) => {
      const firstTask = page.locator('[data-testid="task-item"]').first();
      await firstTask.click();
      
      await expect(page.locator('[data-testid="task-detail-status"]')).toBeVisible();
      await expect(page.locator('[data-testid="task-detail-priority"]')).toBeVisible();
      await expect(page.locator('[data-testid="task-detail-created-at"]')).toBeVisible();
    });

    test('应该能够关闭详情对话框', async ({ page }) => {
      const firstTask = page.locator('[data-testid="task-item"]').first();
      await firstTask.click();
      
      await page.click('.task-detail-dialog .el-dialog__close');
      
      await expect(page.locator('.task-detail-dialog')).not.toBeVisible();
    });
  });

  test.describe('任务分配', () => {
    test('应该能够打开分配对话框', async ({ page }) => {
      const firstTask = page.locator('[data-testid="task-item"]').first();
      await firstTask.locator('[data-testid="assign-button"]').click();
      
      await expect(page.locator('.assign-dialog')).toBeVisible();
    });

    test('应该显示可用的Agent列表', async ({ page }) => {
      const firstTask = page.locator('[data-testid="task-item"]').first();
      await firstTask.locator('[data-testid="assign-button"]').click();
      
      await page.click('[data-testid="agent-select"]');
      
      const agents = page.locator('.el-select-dropdown__item');
      const count = await agents.count();
      expect(count).toBeGreaterThan(0);
    });

    test('应该能够分配任务给Agent', async ({ page }) => {
      const firstTask = page.locator('[data-testid="task-item"]').first();
      await firstTask.locator('[data-testid="assign-button"]').click();
      
      await page.click('[data-testid="agent-select"]');
      await page.click('.el-select-dropdown__item:first-child');
      
      await page.fill('[data-testid="estimated-hours"]', '4');
      
      await page.click('[data-testid="confirm-assign"]');
      
      await expect(page.locator('.el-message--success')).toBeVisible();
    });

    test('未选择Agent时应显示警告', async ({ page }) => {
      const firstTask = page.locator('[data-testid="task-item"]').first();
      await firstTask.locator('[data-testid="assign-button"]').click();
      
      await page.click('[data-testid="confirm-assign"]');
      
      await expect(page.locator('.el-message--warning')).toBeVisible();
    });

    test('应该能够修改已分配的任务', async ({ page }) => {
      const assignedTask = page.locator('[data-testid="task-item"]:has([data-testid="assigned-agent"])').first();
      if (await assignedTask.isVisible()) {
        await assignedTask.locator('[data-testid="assign-button"]').click();
        
        await expect(page.locator('.assign-dialog')).toBeVisible();
      }
    });
  });

  test.describe('任务依赖', () => {
    test('应该能够查看任务依赖', async ({ page }) => {
      const firstTask = page.locator('[data-testid="task-item"]').first();
      await firstTask.locator('[data-testid="view-dependencies-button"]').click();
      
      await expect(page.locator('.dependency-dialog')).toBeVisible();
    });

    test('应该显示现有依赖关系', async ({ page }) => {
      const firstTask = page.locator('[data-testid="task-item"]').first();
      await firstTask.locator('[data-testid="view-dependencies-button"]').click();
      
      const dependencies = page.locator('[data-testid="dependency-item"]');
      const count = await dependencies.count();
      
      if (count > 0) {
        await expect(dependencies.first()).toBeVisible();
      }
    });

    test('应该能够添加依赖', async ({ page }) => {
      const firstTask = page.locator('[data-testid="task-item"]').first();
      await firstTask.locator('[data-testid="view-dependencies-button"]').click();
      
      await page.click('[data-testid="add-dependency-button"]');
      
      await expect(page.locator('.add-dependency-dialog')).toBeVisible();
      
      await page.click('[data-testid="depends-on-task-select"]');
      await page.click('.el-select-dropdown__item:first-child');
      
      await page.click('[data-testid="confirm-add-dependency"]');
      
      await expect(page.locator('.el-message--success')).toBeVisible();
    });

    test('应该能够移除依赖', async ({ page }) => {
      const firstTask = page.locator('[data-testid="task-item"]').first();
      await firstTask.locator('[data-testid="view-dependencies-button"]').click();
      
      const removeButton = page.locator('[data-testid="remove-dependency-button"]').first();
      if (await removeButton.isVisible()) {
        await removeButton.click();
        
        await page.click('.el-message-box .el-button--primary');
        
        await expect(page.locator('.el-message--success')).toBeVisible();
      }
    });
  });

  test.describe('响应式设计', () => {
    test('移动端应正确显示任务列表', async ({ page }) => {
      await page.setViewportSize({ width: 375, height: 667 });
      
      await expect(page.locator('.task-list')).toBeVisible();
      
      const firstTask = page.locator('[data-testid="task-item"]').first();
      await expect(firstTask).toBeVisible();
    });

    test('移动端应能够筛选任务', async ({ page }) => {
      await page.setViewportSize({ width: 375, height: 667 });
      
      await page.selectOption('[data-testid="filter-status"]', 'pending');
      await page.waitForTimeout(500);
      
      await expect(page.locator('[data-testid="task-item"]')).toBeVisible();
    });

    test('平板端应正确显示布局', async ({ page }) => {
      await page.setViewportSize({ width: 768, height: 1024 });
      
      await expect(page.locator('.task-filter')).toBeVisible();
      await expect(page.locator('.task-list')).toBeVisible();
    });
  });

  test.describe('性能测试', () => {
    test('页面应在3秒内加载完成', async ({ page }) => {
      const startTime = Date.now();
      
      await page.goto('/tasks');
      await page.waitForLoadState('networkidle');
      
      const loadTime = Date.now() - startTime;
      expect(loadTime).toBeLessThan(3000);
    });

    test('大量任务时应保持响应', async ({ page }) => {
      await page.goto('/tasks?loadTest=true');
      await page.waitForLoadState('networkidle');
      
      await expect(page.locator('[data-testid="task-item"]').first()).toBeVisible();
    });
  });

  test.describe('错误处理', () => {
    test('API错误时应显示错误提示', async ({ page }) => {
      await page.route('**/api/tasks', route => {
        route.fulfill({ status: 500, body: JSON.stringify({ error: 'Server Error' }) });
      });
      
      await page.reload();
      
      await expect(page.locator('.el-message--error')).toBeVisible();
    });

    test('空任务列表应显示空状态', async ({ page }) => {
      await page.route('**/api/tasks', route => {
        route.fulfill({ status: 200, body: JSON.stringify({ items: [], total: 0 }) });
      });
      
      await page.reload();
      
      await expect(page.locator('.el-empty')).toBeVisible();
    });

    test('网络错误时应显示重试选项', async ({ page }) => {
      let requestCount = 0;
      await page.route('**/api/tasks', route => {
        requestCount++;
        if (requestCount === 1) {
          route.abort('failed');
        } else {
          route.fulfill({ status: 200, body: JSON.stringify({ items: [], total: 0 }) });
        }
      });
      
      await page.reload();
      
      const retryButton = page.locator('[data-testid="retry-button"]');
      if (await retryButton.isVisible()) {
        await retryButton.click();
        await expect(page.locator('.task-list')).toBeVisible();
      }
    });
  });

  test.describe('无障碍访问', () => {
    test('应该支持键盘导航', async ({ page }) => {
      await page.keyboard.press('Tab');
      
      const focusedElement = await page.evaluate(() => document.activeElement?.tagName);
      expect(focusedElement).not.toBe('BODY');
    });

    test('应该有适当的ARIA标签', async ({ page }) => {
      const taskItems = page.locator('[data-testid="task-item"]');
      const count = await taskItems.count();
      
      if (count > 0) {
        const firstItem = taskItems.first();
        const ariaLabel = await firstItem.getAttribute('aria-label');
        expect(ariaLabel).toBeTruthy();
      }
    });
  });
});
