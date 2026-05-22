import { test, expect } from '@playwright/test';

test.describe('项目创建流程 - 多步骤表单', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/projects/create');
    await page.waitForLoadState('networkidle');
  });

  test.describe('步骤1: 选择模板', () => {
    test('应该显示三个项目模板选项', async ({ page }) => {
      await expect(page.locator('.template-item')).toHaveCount(3);
      
      await expect(page.locator('.template-item').nth(0)).toContainText('Web项目');
      await expect(page.locator('.template-item').nth(1)).toContainText('MCP服务器');
      await expect(page.locator('.template-item').nth(2)).toContainText('AI项目');
    });

    test('应该能够选择模板并高亮显示', async ({ page }) => {
      await page.locator('.template-item').first().click();
      
      await expect(page.locator('.template-item').first()).toHaveClass(/active/);
      await expect(page.locator('.template-check')).toBeVisible();
    });

    test('未选择模板时点击下一步应显示警告', async ({ page }) => {
      await page.click('button:has-text("下一步")');
      
      await expect(page.locator('.el-message--warning')).toBeVisible();
    });

    test('选择模板后应能进入下一步', async ({ page }) => {
      await page.locator('.template-item').first().click();
      await page.click('button:has-text("下一步")');
      
      await expect(page.locator('.el-steps')).toContainText('基本信息');
    });
  });

  test.describe('步骤2: 基本信息', () => {
    test.beforeEach(async ({ page }) => {
      await page.locator('.template-item').first().click();
      await page.click('button:has-text("下一步")');
    });

    test('应该显示基本信息表单', async ({ page }) => {
      await expect(page.locator('text=项目名称')).toBeVisible();
      await expect(page.locator('text=项目描述')).toBeVisible();
      await expect(page.locator('text=项目类型')).toBeVisible();
    });

    test('项目名称必填验证', async ({ page }) => {
      await page.click('button:has-text("下一步")');
      
      await expect(page.locator('.el-form-item__error')).toContainText('请输入项目名称');
    });

    test('项目名称长度验证', async ({ page }) => {
      await page.fill('[data-testid="project-name"] input', 'a');
      await page.click('button:has-text("下一步")');
      
      await expect(page.locator('.el-form-item__error')).toContainText('长度在 2 到 50 个字符');
    });

    test('项目类型必选验证', async ({ page }) => {
      await page.fill('[data-testid="project-name"] input', '测试项目名称');
      await page.click('button:has-text("下一步")');
      
      await expect(page.locator('.el-form-item__error')).toContainText('请选择项目类型');
    });

    test('填写完整信息后应能进入下一步', async ({ page }) => {
      await page.fill('[data-testid="project-name"] input', 'E2E测试项目');
      await page.fill('[data-testid="project-description"] textarea', '这是一个E2E测试项目的描述');
      await page.click('.el-select:has-text("请选择项目类型")');
      await page.click('.el-select-dropdown__item:has-text("企业级应用")');
      
      await page.click('button:has-text("下一步")');
      
      await expect(page.locator('.el-steps')).toContainText('技术栈配置');
    });

    test('应该能够返回上一步', async ({ page }) => {
      await page.click('button:has-text("上一步")');
      
      await expect(page.locator('.template-item')).toHaveCount(3);
    });
  });

  test.describe('步骤3: 技术栈配置', () => {
    test.beforeEach(async ({ page }) => {
      await page.locator('.template-item').first().click();
      await page.click('button:has-text("下一步")');
      
      await page.fill('[data-testid="project-name"] input', 'E2E测试项目');
      await page.fill('[data-testid="project-description"] textarea', '测试描述');
      await page.click('.el-select:has-text("请选择项目类型")');
      await page.click('.el-select-dropdown__item:has-text("企业级应用")');
      await page.click('button:has-text("下一步")');
    });

    test('应该显示技术栈配置表单', async ({ page }) => {
      await expect(page.locator('text=前端框架')).toBeVisible();
      await expect(page.locator('text=后端框架')).toBeVisible();
      await expect(page.locator('text=数据库')).toBeVisible();
    });

    test('前端框架必选验证', async ({ page }) => {
      await page.click('button:has-text("提交创建")');
      
      await expect(page.locator('.el-form-item__error')).toContainText('请选择前端框架');
    });

    test('后端框架必选验证', async ({ page }) => {
      await page.click('.el-radio-group:has-text("Vue") .el-radio-button__inner');
      await page.click('button:has-text("提交创建")');
      
      await expect(page.locator('.el-form-item__error')).toContainText('请选择后端框架');
    });

    test('数据库必选验证', async ({ page }) => {
      await page.click('.el-radio-group:has-text("Vue") .el-radio-button__inner');
      await page.click('.el-radio-group:has-text("FastAPI") .el-radio-button__inner');
      await page.click('button:has-text("提交创建")');
      
      await expect(page.locator('.el-form-item__error')).toContainText('请选择数据库');
    });

    test('完整填写后应能成功提交', async ({ page }) => {
      await page.click('.el-radio-group:has-text("Vue") .el-radio-button__inner');
      await page.click('.el-radio-group:has-text("FastAPI") .el-radio-button__inner');
      await page.click('.el-radio-group:has-text("PostgreSQL") .el-radio-button__inner');
      
      await page.click('button:has-text("提交创建")');
      
      await expect(page.locator('.el-message--success')).toBeVisible();
      await expect(page).toHaveURL(/.*projects$/);
    });
  });

  test.describe('保存草稿功能', () => {
    test('应该能够保存草稿', async ({ page }) => {
      await page.fill('[data-testid="project-name"] input', '草稿项目');
      await page.fill('[data-testid="project-description"] textarea', '草稿描述');
      
      await page.click('button:has-text("保存草稿")');
      
      await expect(page.locator('.el-message--success')).toBeVisible();
      await expect(page).toHaveURL(/.*projects$/);
    });

    test('空表单保存草稿应使用默认名称', async ({ page }) => {
      await page.click('button:has-text("保存草稿")');
      
      await expect(page.locator('.el-message--success')).toBeVisible();
    });
  });

  test.describe('步骤导航', () => {
    test('步骤指示器应正确显示当前步骤', async ({ page }) => {
      await expect(page.locator('.el-step').first()).toHaveClass(/is-process/);
      
      await page.locator('.template-item').first().click();
      await page.click('button:has-text("下一步")');
      
      await expect(page.locator('.el-step').nth(1)).toHaveClass(/is-process/);
    });

    test('应该能够通过步骤导航返回', async ({ page }) => {
      await page.locator('.template-item').first().click();
      await page.click('button:has-text("下一步")');
      await page.fill('[data-testid="project-name"] input', '测试');
      await page.click('.el-select:has-text("请选择项目类型")');
      await page.click('.el-select-dropdown__item:has-text("企业级应用")');
      await page.click('button:has-text("下一步")');
      
      await page.click('button:has-text("上一步")');
      await expect(page.locator('.el-step').nth(1)).toHaveClass(/is-process/);
      
      await page.click('button:has-text("上一步")');
      await expect(page.locator('.el-step').first()).toHaveClass(/is-process/);
    });
  });

  test.describe('完整创建流程', () => {
    test('应该能够完成完整的项目创建流程', async ({ page }) => {
      await page.locator('.template-item:has-text("Web项目")').click();
      await page.click('button:has-text("下一步")');
      
      await page.fill('[data-testid="project-name"] input', '完整E2E测试项目');
      await page.fill('[data-testid="project-description"] textarea', '这是一个完整的E2E测试项目，用于验证项目创建流程');
      await page.click('.el-select:has-text("请选择项目类型")');
      await page.click('.el-select-dropdown__item:has-text("企业级应用")');
      await page.click('button:has-text("下一步")');
      
      await page.click('.el-radio-group:has-text("Vue") .el-radio-button__inner');
      await page.click('.el-radio-group:has-text("FastAPI") .el-radio-button__inner');
      await page.click('.el-radio-group:has-text("PostgreSQL") .el-radio-button__inner');
      
      await page.click('button:has-text("提交创建")');
      
      await expect(page.locator('.el-message--success')).toBeVisible();
      await expect(page).toHaveURL('/projects');
      await expect(page.locator('text=完整E2E测试项目')).toBeVisible();
    });

    test('创建不同类型的项目', async ({ page }) => {
      const projectTypes = [
        { template: 'Web项目', name: 'Web测试项目' },
        { template: 'MCP服务器', name: 'MCP测试项目' },
        { template: 'AI项目', name: 'AI测试项目' }
      ];

      for (const type of projectTypes) {
        await page.goto('/projects/create');
        
        await page.locator(`.template-item:has-text("${type.template}")`).click();
        await page.click('button:has-text("下一步")');
        
        await page.fill('[data-testid="project-name"] input', type.name);
        await page.click('.el-select:has-text("请选择项目类型")');
        await page.click('.el-select-dropdown__item:has-text("中小型项目")');
        await page.click('button:has-text("下一步")');
        
        await page.click('.el-radio-group:has-text("React") .el-radio-button__inner');
        await page.click('.el-radio-group:has-text("Express") .el-radio-button__inner');
        await page.click('.el-radio-group:has-text("MongoDB") .el-radio-button__inner');
        
        await page.click('button:has-text("提交创建")');
        
        await expect(page.locator('.el-message--success')).toBeVisible();
      }
    });
  });

  test.describe('响应式设计', () => {
    test('移动端应正确显示步骤', async ({ page }) => {
      await page.setViewportSize({ width: 375, height: 667 });
      
      await expect(page.locator('.el-steps')).toBeVisible();
      await expect(page.locator('.template-item')).toHaveCount(3);
    });

    test('平板端应正确显示布局', async ({ page }) => {
      await page.setViewportSize({ width: 768, height: 1024 });
      
      await expect(page.locator('.template-item')).toHaveCount(3);
    });
  });

  test.describe('错误处理', () => {
    test('网络错误时应显示错误提示', async ({ page }) => {
      await page.route('**/api/projects', route => {
        route.fulfill({ status: 500, body: JSON.stringify({ error: 'Server Error' }) });
      });

      await page.locator('.template-item').first().click();
      await page.click('button:has-text("下一步")');
      await page.fill('[data-testid="project-name"] input', '错误测试项目');
      await page.click('.el-select:has-text("请选择项目类型")');
      await page.click('.el-select-dropdown__item:has-text("企业级应用")');
      await page.click('button:has-text("下一步")');
      await page.click('.el-radio-group:has-text("Vue") .el-radio-button__inner');
      await page.click('.el-radio-group:has-text("FastAPI") .el-radio-button__inner');
      await page.click('.el-radio-group:has-text("PostgreSQL") .el-radio-button__inner');
      await page.click('button:has-text("提交创建")');
      
      await expect(page.locator('.el-message--error')).toBeVisible();
    });
  });
});
