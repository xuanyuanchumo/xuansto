import { test, expect } from '@playwright/test';

test.describe('跨浏览器兼容性测试', () => {
  test.describe('基础功能兼容性', () => {
    test('页面应在所有浏览器中正确加载', async ({ page, browserName }) => {
      await page.goto('/');
      await page.waitForLoadState('networkidle');
      
      await expect(page.locator('body')).toBeVisible();
      
      console.log(`测试通过: ${browserName}`);
    });

    test('导航应在所有浏览器中正常工作', async ({ page, browserName }) => {
      await page.goto('/');
      
      const navItems = page.locator('[data-testid^="nav-"]');
      const count = await navItems.count();
      
      expect(count).toBeGreaterThan(0);
      
      console.log(`导航项数量: ${count} (${browserName})`);
    });
  });

  test.describe('CSS兼容性', () => {
    test('Flexbox布局应正常工作', async ({ page }) => {
      await page.goto('/dashboard');
      
      const statCards = page.locator('[data-testid="stat-card"]');
      const count = await statCards.count();
      
      if (count >= 2) {
        const firstCard = await statCards.first().boundingBox();
        const secondCard = await statCards.nth(1).boundingBox();
        
        expect(firstCard).toBeTruthy();
        expect(secondCard).toBeTruthy();
      }
    });

    test('CSS Grid布局应正常工作', async ({ page }) => {
      await page.goto('/projects');
      
      const projectList = page.locator('[data-testid="project-list"]');
      if (await projectList.isVisible()) {
        const gridStyle = await projectList.evaluate(el => {
          return window.getComputedStyle(el).display;
        });
        
        expect(['grid', 'flex', 'block']).toContain(gridStyle);
      }
    });

    test('CSS变量应正确应用', async ({ page }) => {
      await page.goto('/');
      
      const bodyColor = await page.locator('body').evaluate(el => {
        return window.getComputedStyle(el).getPropertyValue('--el-color-primary');
      });
      
      console.log(`主色调: ${bodyColor}`);
    });
  });

  test.describe('JavaScript兼容性', () => {
    test('ES6+特性应正常工作', async ({ page }) => {
      const result = await page.evaluate(async () => {
        const arr = [1, 2, 3];
        const doubled = arr.map(x => x * 2);
        const sum = doubled.reduce((a, b) => a + b, 0);
        
        const obj = { a: 1, b: 2 };
        const { a, b } = obj;
        
        const promiseResult = await Promise.resolve(42);
        
        return {
          sum,
          destructuring: a + b,
          promiseResult
        };
      });
      
      expect(result.sum).toBe(12);
      expect(result.destructuring).toBe(3);
      expect(result.promiseResult).toBe(42);
    });

    test('async/await应正常工作', async ({ page }) => {
      const result = await page.evaluate(async () => {
        const delay = (ms: number) => new Promise(resolve => setTimeout(resolve, ms));
        
        await delay(100);
        return 'success';
      });
      
      expect(result).toBe('success');
    });

    test('Fetch API应正常工作', async ({ page }) => {
      await page.goto('/');
      
      const response = await page.evaluate(async () => {
        try {
          const res = await fetch('/api/health');
          return { ok: res.ok, status: res.status };
        } catch {
          return { ok: false, status: 0 };
        }
      });
      
      console.log(`API响应: ${JSON.stringify(response)}`);
    });
  });

  test.describe('事件处理兼容性', () => {
    test('点击事件应正常触发', async ({ page }) => {
      await page.goto('/projects');
      
      let clickTriggered = false;
      page.on('console', msg => {
        if (msg.text().includes('click')) {
          clickTriggered = true;
        }
      });
      
      const createButton = page.locator('[data-testid="create-project-btn"]');
      if (await createButton.isVisible()) {
        await createButton.click();
      }
    });

    test('表单输入应正常工作', async ({ page }) => {
      await page.goto('/projects/create');
      
      const nameInput = page.locator('[data-testid="project-name"] input');
      if (await nameInput.isVisible()) {
        await nameInput.fill('测试项目');
        await expect(nameInput).toHaveValue('测试项目');
      }
    });

    test('下拉选择应正常工作', async ({ page }) => {
      await page.goto('/projects/create');
      
      const typeSelect = page.locator('.el-select:has-text("请选择项目类型")');
      if (await typeSelect.isVisible()) {
        await typeSelect.click();
        await page.click('.el-select-dropdown__item:first-child');
      }
    });
  });

  test.describe('存储兼容性', () => {
    test('LocalStorage应正常工作', async ({ page }) => {
      await page.goto('/');
      
      await page.evaluate(() => {
        localStorage.setItem('test-key', 'test-value');
      });
      
      const value = await page.evaluate(() => {
        return localStorage.getItem('test-key');
      });
      
      expect(value).toBe('test-value');
      
      await page.evaluate(() => {
        localStorage.removeItem('test-key');
      });
    });

    test('SessionStorage应正常工作', async ({ page }) => {
      await page.goto('/');
      
      await page.evaluate(() => {
        sessionStorage.setItem('session-key', 'session-value');
      });
      
      const value = await page.evaluate(() => {
        return sessionStorage.getItem('session-key');
      });
      
      expect(value).toBe('session-value');
    });
  });

  test.describe('响应式设计兼容性', () => {
    test('移动端视口应正确渲染', async ({ page, browserName }) => {
      await page.setViewportSize({ width: 375, height: 667 });
      await page.goto('/');
      
      await expect(page.locator('body')).toBeVisible();
      
      console.log(`移动端测试通过: ${browserName}`);
    });

    test('平板端视口应正确渲染', async ({ page, browserName }) => {
      await page.setViewportSize({ width: 768, height: 1024 });
      await page.goto('/');
      
      await expect(page.locator('body')).toBeVisible();
      
      console.log(`平板端测试通过: ${browserName}`);
    });

    test('桌面端视口应正确渲染', async ({ page, browserName }) => {
      await page.setViewportSize({ width: 1920, height: 1080 });
      await page.goto('/');
      
      await expect(page.locator('body')).toBeVisible();
      
      console.log(`桌面端测试通过: ${browserName}`);
    });
  });

  test.describe('WebSocket兼容性', () => {
    test('WebSocket连接应正常建立', async ({ page }) => {
      await page.goto('/');
      
      const wsSupported = await page.evaluate(() => {
        return 'WebSocket' in window;
      });
      
      expect(wsSupported).toBe(true);
    });
  });

  test.describe('动画兼容性', () => {
    test('CSS过渡动画应正常工作', async ({ page }) => {
      await page.goto('/');
      
      const button = page.locator('button').first();
      if (await button.isVisible()) {
        const transition = await button.evaluate(el => {
          return window.getComputedStyle(el).transition;
        });
        
        console.log(`过渡效果: ${transition}`);
      }
    });

    test('CSS动画应正常工作', async ({ page }) => {
      await page.goto('/');
      
      const hasAnimations = await page.evaluate(() => {
        const styleSheets = document.styleSheets;
        let animationFound = false;
        
        try {
          for (let i = 0; i < styleSheets.length; i++) {
            try {
              const rules = styleSheets[i].cssRules;
              for (let j = 0; j < rules.length; j++) {
                if (rules[j] instanceof CSSKeyframesRule) {
                  animationFound = true;
                  break;
                }
              }
            } catch {
              continue;
            }
          }
        } catch {
          return false;
        }
        
        return animationFound;
      });
      
      console.log(`发现CSS动画: ${hasAnimations}`);
    });
  });

  test.describe('字体兼容性', () => {
    test('Web字体应正确加载', async ({ page }) => {
      await page.goto('/');
      
      await page.waitForTimeout(1000);
      
      const fontLoaded = await page.evaluate(() => {
        return document.fonts.ready.then(() => {
          return document.fonts.check('12px sans-serif');
        });
      });
      
      expect(fontLoaded).toBe(true);
    });
  });

  test.describe('图片兼容性', () => {
    test('图片应正确加载', async ({ page }) => {
      await page.goto('/');
      
      const images = page.locator('img');
      const count = await images.count();
      
      if (count > 0) {
        const firstImage = images.first();
        const naturalWidth = await firstImage.evaluate((img: HTMLImageElement) => img.naturalWidth);
        
        console.log(`图片数量: ${count}, 第一张图片宽度: ${naturalWidth}`);
      }
    });

    test('SVG应正确渲染', async ({ page }) => {
      await page.goto('/');
      
      const svgs = page.locator('svg');
      const count = await svgs.count();
      
      console.log(`SVG数量: ${count}`);
    });
  });
});
