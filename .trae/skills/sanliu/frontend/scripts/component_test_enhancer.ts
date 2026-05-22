import * as fs from 'fs';
import * as path from 'path';

/**
 * 组件测试增强器
 * 
 * 功能说明：
 * - 分析项目中所有 Vue 组件的测试覆盖率
 * - 自动生成缺失的单元测试、集成测试和 E2E 测试模板
 * - 评估现有测试的质量并提出改进建议
 * - 生成测试工具函数和模拟数据
 * 
 * 输出内容：
 * - test-enhancement-reports/test-enhancement-report.json - 详细测试报告
 * - test-enhancement-reports/test-enhancement-summary.txt - 摘要报告
 * - test-enhancement-reports/generated-templates/ - 生成的测试模板
 * - test-enhancement-reports/test-utilities/ - 测试工具函数
 * 
 * 使用方法：
 * ```bash
 * npx ts-node component_test_enhancer.ts
 * ```
 * 
 * @author GUI优化子代理
 * @version 1.0.0
 */

interface TestCoverage {
  component: string;
  hasUnitTests: boolean;
  hasIntegrationTests: boolean;
  hasE2ETests: boolean;
  coverage: number;
  missingTests: string[];
  testQuality: 'low' | 'medium' | 'high';
}

interface TestTemplate {
  name: string;
  content: string;
  type: 'unit' | 'integration' | 'e2e';
}

class ComponentTestEnhancer {
  private projectRoot: string;
  private outputDir: string;
  private testResults: TestCoverage[] = [];
  private generatedTemplates: TestTemplate[] = [];

  constructor(projectRoot: string, outputDir: string) {
    this.projectRoot = projectRoot;
    this.outputDir = outputDir;
    this.ensureOutputDir();
  }

  private ensureOutputDir(): void {
    if (!fs.existsSync(this.outputDir)) {
      fs.mkdirSync(this.outputDir, { recursive: true });
    }
  }

  public async enhance(): Promise<TestCoverage[]> {
    console.log('开始组件测试增强分析...');
    
    await this.analyzeTestCoverage();
    await this.generateMissingTests();
    await this.enhanceExistingTests();
    await this.generateTestUtilities();
    
    this.generateTestReport();
    return this.testResults;
  }

  private async analyzeTestCoverage(): Promise<void> {
    console.log('\n分析测试覆盖率...');
    
    const componentsDir = path.join(this.projectRoot, 'src', 'components');
    const testsDir = path.join(this.projectRoot, 'tests', 'components');
    
    if (!fs.existsSync(componentsDir)) return;
    
    const componentFiles = this.findVueFiles(componentsDir);
    
    for (const file of componentFiles) {
      const componentName = path.basename(file, '.vue');
      const relativePath = path.relative(componentsDir, file);
      
      const unitTestPath = path.join(testsDir, `${componentName}.test.ts`);
      const integrationTestPath = path.join(testsDir, 'integration', `${componentName}.integration.test.ts`);
      const e2eTestPath = path.join(this.projectRoot, 'e2e', `${componentName}.spec.ts`);
      
      const hasUnitTests = fs.existsSync(unitTestPath);
      const hasIntegrationTests = fs.existsSync(integrationTestPath);
      const hasE2ETests = fs.existsSync(e2eTestPath);
      
      const coverage = this.calculateCoverage(hasUnitTests, hasIntegrationTests, hasE2ETests);
      const missingTests = this.identifyMissingTests(hasUnitTests, hasIntegrationTests, hasE2ETests);
      const testQuality = this.assessTestQuality(file, hasUnitTests ? unitTestPath : null);
      
      this.testResults.push({
        component: componentName,
        hasUnitTests,
        hasIntegrationTests,
        hasE2ETests,
        coverage,
        missingTests,
        testQuality
      });
    }
  }

  private calculateCoverage(unit: boolean, integration: boolean, e2e: boolean): number {
    let coverage = 0;
    if (unit) coverage += 50;
    if (integration) coverage += 30;
    if (e2e) coverage += 20;
    return coverage;
  }

  private identifyMissingTests(unit: boolean, integration: boolean, e2e: boolean): string[] {
    const missing: string[] = [];
    if (!unit) missing.push('单元测试');
    if (!integration) missing.push('集成测试');
    if (!e2e) missing.push('E2E测试');
    return missing;
  }

  private assessTestQuality(componentPath: string, testPath: string | null): 'low' | 'medium' | 'high' {
    if (!testPath) return 'low';
    
    const testContent = fs.readFileSync(testPath, 'utf-8');
    const componentContent = fs.readFileSync(componentPath, 'utf-8');
    
    let score = 0;
    
    if (testContent.includes('describe') || testContent.includes('test(')) score += 1;
    if (testContent.includes('it(') || testContent.includes('test(')) score += 1;
    if (testContent.includes('expect(')) score += 2;
    if (testContent.includes('beforeEach') || testContent.includes('afterEach')) score += 1;
    if (testContent.includes('mock') || testContent.includes('vi.fn')) score += 1;
    if (testContent.includes('mount') || testContent.includes('shallowMount')) score += 1;
    
    const props = (componentContent.match(/defineProps|props\s*:/g) || []).length;
    const hasPropsTest = testContent.includes('props');
    if (props > 0 && hasPropsTest) score += 1;
    
    const emits = (componentContent.match(/defineEmits|emits\s*:/g) || []).length;
    const hasEmitsTest = testContent.includes('emit');
    if (emits > 0 && hasEmitsTest) score += 1;
    
    if (score >= 7) return 'high';
    if (score >= 4) return 'medium';
    return 'low';
  }

  private async generateMissingTests(): Promise<void> {
    console.log('\n生成缺失的测试...');
    
    const componentsDir = path.join(this.projectRoot, 'src', 'components');
    
    for (const result of this.testResults) {
      if (result.missingTests.length === 0) continue;
      
      const componentPath = this.findComponentPath(componentsDir, result.component);
      if (!componentPath) continue;
      
      const componentContent = fs.readFileSync(componentPath, 'utf-8');
      
      if (result.missingTests.includes('单元测试')) {
        const template = this.generateUnitTestTemplate(result.component, componentContent);
        this.generatedTemplates.push(template);
      }
      
      if (result.missingTests.includes('集成测试')) {
        const template = this.generateIntegrationTestTemplate(result.component, componentContent);
        this.generatedTemplates.push(template);
      }
      
      if (result.missingTests.includes('E2E测试')) {
        const template = this.generateE2ETestTemplate(result.component, componentContent);
        this.generatedTemplates.push(template);
      }
    }
    
    this.saveGeneratedTemplates();
  }

  private findComponentPath(dir: string, componentName: string): string | null {
    const items = fs.readdirSync(dir);
    
    for (const item of items) {
      const fullPath = path.join(dir, item);
      const stat = fs.statSync(fullPath);
      
      if (stat.isDirectory()) {
        const found = this.findComponentPath(fullPath, componentName);
        if (found) return found;
      } else if (item === `${componentName}.vue`) {
        return fullPath;
      }
    }
    
    return null;
  }

  private generateUnitTestTemplate(componentName: string, content: string): TestTemplate {
    const props = this.extractPropsFromContent(content);
    const emits = this.extractEmitsFromContent(content);
    const hasSlots = content.includes('<slot');
    
    const template = `import { describe, it, expect, beforeEach, vi } from 'vitest';
import { mount } from '@vue/test-utils';
import ${componentName} from '@/components/${componentName}.vue';

describe('${componentName}', () => {
  let wrapper: any;

  beforeEach(() => {
    wrapper = mount(${componentName}, {
      props: {
        ${props.map(p => `${p}: 'test-value'`).join(',\n        ')}
      },
      global: {
        mocks: {
          \$router: {
            push: vi.fn()
          },
          \$route: {
            params: {},
            query: {}
          }
        },
        stubs: {
          RouterLink: true
        }
      }
    });
  });

  afterEach(() => {
    wrapper?.unmount();
  });

  describe('渲染', () => {
    it('应该正确渲染组件', () => {
      expect(wrapper.exists()).toBe(true);
    });

    it('应该包含必要的DOM元素', () => {
      expect(wrapper.find('.${componentName.toLowerCase()}').exists()).toBe(true);
    });
    ${hasSlots ? `
    it('应该正确渲染插槽内容', () => {
      const slotContent = '测试插槽内容';
      const wrapperWithSlot = mount(${componentName}, {
        slots: {
          default: slotContent
        }
      });
      expect(wrapperWithSlot.text()).toContain(slotContent);
    });` : ''}
  });

  describe('Props', () => {
    ${props.map(prop => `
    it('应该正确接收 ${prop} prop', () => {
      const testValue = 'test-${prop}';
      const wrapper = mount(${componentName}, {
        props: { ${prop}: testValue }
      });
      expect(wrapper.props('${prop}')).toBe(testValue);
    });`).join('')}
  });

  describe('事件', () => {
    ${emits.map(emit => `
    it('应该触发 ${emit} 事件', async () => {
      await wrapper.vm.\$emit('${emit}', { data: 'test' });
      expect(wrapper.emitted('${emit}')).toBeTruthy();
    });`).join('')}
  });

  describe('交互', () => {
    it('应该响应点击事件', async () => {
      const button = wrapper.find('button');
      if (button.exists()) {
        await button.trigger('click');
        expect(wrapper.emitted()).toBeTruthy();
      }
    });
  });

  describe('边界情况', () => {
    it('应该处理空数据', () => {
      const emptyWrapper = mount(${componentName}, {
        props: {
          ${props.map(p => `${p}: null`).join(',\n          ')}
        }
      });
      expect(emptyWrapper.exists()).toBe(true);
    });

    it('应该处理加载状态', () => {
      const loadingWrapper = mount(${componentName}, {
        props: {
          loading: true
        }
      });
      expect(loadingWrapper.exists()).toBe(true);
    });
  });
}`;

    return {
      name: `${componentName}.test.ts`,
      content: template,
      type: 'unit'
    };
  }

  private generateIntegrationTestTemplate(componentName: string, content: string): TestTemplate {
    const template = `import { describe, it, expect, beforeEach, vi } from 'vitest';
import { mount } from '@vue/test-utils';
import { createPinia, setActivePinia } from 'pinia';
import ${componentName} from '@/components/${componentName}.vue';

describe('${componentName} - 集成测试', () => {
  beforeEach(() => {
    setActivePinia(createPinia());
  });

  describe('Store 集成', () => {
    it('应该正确连接到 store', async () => {
      const wrapper = mount(${componentName}, {
        global: {
          plugins: [createPinia()]
        }
      });
      
      expect(wrapper.exists()).toBe(true);
    });

    it('应该响应 store 状态变化', async () => {
      const wrapper = mount(${componentName}, {
        global: {
          plugins: [createPinia()]
        }
      });
      
      // 测试 store 状态变化
      // const store = useSomeStore();
      // await store.someAction();
      // expect(wrapper.html()).toContain('expected content');
    });
  });

  describe('API 集成', () => {
    it('应该正确处理 API 调用', async () => {
      const mockApi = {
        fetchData: vi.fn().mockResolvedValue({ data: 'test' })
      };

      const wrapper = mount(${componentName}, {
        global: {
          provide: {
            api: mockApi
          }
        }
      });

      // 测试 API 调用
      // await wrapper.vm.someMethod();
      // expect(mockApi.fetchData).toHaveBeenCalled();
    });
  });

  describe('路由集成', () => {
    it('应该正确处理路由导航', async () => {
      const mockPush = vi.fn();
      
      const wrapper = mount(${componentName}, {
        global: {
          mocks: {
            \$router: {
              push: mockPush
            },
            \$route: {
              params: { id: '123' },
              query: {}
            }
          }
        }
      });

      // 测试路由导航
      // await wrapper.vm.navigateTo('/test');
      // expect(mockPush).toHaveBeenCalledWith('/test');
    });
  });

  describe('WebSocket 集成', () => {
    it('应该正确处理 WebSocket 消息', async () => {
      const mockWebSocket = {
        send: vi.fn(),
        close: vi.fn()
      };

      const wrapper = mount(${componentName}, {
        global: {
          provide: {
            websocket: mockWebSocket
          }
        }
      });

      // 测试 WebSocket 消息处理
    });
  });
});`;

    return {
      name: `${componentName}.integration.test.ts`,
      content: template,
      type: 'integration'
    };
  }

  private generateE2ETestTemplate(componentName: string, content: string): TestTemplate {
    const template = `import { test, expect } from '@playwright/test';

test.describe('${componentName} E2E 测试', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
    // 导航到包含该组件的页面
  });

  test('应该正确显示组件', async ({ page }) => {
    // 等待组件加载
    await page.waitForSelector('.${componentName.toLowerCase()}');
    
    // 验证组件可见
    await expect(page.locator('.${componentName.toLowerCase()}')).toBeVisible();
  });

  test('应该正确处理用户交互', async ({ page }) => {
    // 点击按钮
    const button = page.locator('button');
    if (await button.count() > 0) {
      await button.first().click();
      
      // 验证交互结果
      // await expect(page.locator('.result')).toBeVisible();
    }
  });

  test('应该正确处理表单输入', async ({ page }) => {
    const input = page.locator('input');
    if (await input.count() > 0) {
      await input.first().fill('测试输入');
      
      // 验证输入值
      await expect(input.first()).toHaveValue('测试输入');
    }
  });

  test('应该正确响应错误状态', async ({ page }) => {
    // 模拟错误状态
    await page.route('**/api/**', route => {
      route.fulfill({
        status: 500,
        body: JSON.stringify({ error: 'Server Error' })
      });
    });

    await page.reload();
    
    // 验证错误处理
    // await expect(page.locator('.error-message')).toBeVisible();
  });

  test('应该在移动设备上正确显示', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 667 });
    
    await page.waitForSelector('.${componentName.toLowerCase()}');
    await expect(page.locator('.${componentName.toLowerCase()}')).toBeVisible();
  });

  test('应该正确处理加载状态', async ({ page }) => {
    // 延迟 API 响应
    await page.route('**/api/**', async route => {
      await new Promise(resolve => setTimeout(resolve, 1000));
      route.continue();
    });

    await page.goto('/');
    
    // 验证加载指示器
    // await expect(page.locator('.loading')).toBeVisible();
    
    // 等待加载完成
    // await expect(page.locator('.loading')).not.toBeVisible();
  });
});`;

    return {
      name: `${componentName}.spec.ts`,
      content: template,
      type: 'e2e'
    };
  }

  private extractPropsFromContent(content: string): string[] {
    const props: string[] = [];
    
    const propsMatch = content.match(/defineProps<[^>]*>/);
    if (propsMatch) {
      const propNames = propsMatch[0].match(/\w+\s*:/g);
      if (propNames) {
        props.push(...propNames.map(p => p.replace(':', '').trim()));
      }
    }
    
    return [...new Set(props)];
  }

  private extractEmitsFromContent(content: string): string[] {
    const emits: string[] = [];
    
    const emitsMatch = content.match(/defineEmits<[^>]*>/);
    if (emitsMatch) {
      const emitNames = emitsMatch[0].match(/"\w+"/g);
      if (emitNames) {
        emits.push(...emitNames.map(e => e.replace(/"/g, '')));
      }
    }
    
    return [...new Set(emits)];
  }

  private saveGeneratedTemplates(): void {
    const templatesDir = path.join(this.outputDir, 'generated-templates');
    if (!fs.existsSync(templatesDir)) {
      fs.mkdirSync(templatesDir, { recursive: true });
    }
    
    for (const template of this.generatedTemplates) {
      const subDir = template.type === 'unit' ? 'unit' : 
                     template.type === 'integration' ? 'integration' : 'e2e';
      const dir = path.join(templatesDir, subDir);
      
      if (!fs.existsSync(dir)) {
        fs.mkdirSync(dir, { recursive: true });
      }
      
      const filePath = path.join(dir, template.name);
      fs.writeFileSync(filePath, template.content, 'utf-8');
    }
    
    console.log(`已生成 ${this.generatedTemplates.length} 个测试模板`);
  }

  private async enhanceExistingTests(): Promise<void> {
    console.log('\n增强现有测试...');
    
    const testsDir = path.join(this.projectRoot, 'tests', 'components');
    if (!fs.existsSync(testsDir)) return;
    
    const testFiles = this.findTestFiles(testsDir);
    
    for (const file of testFiles) {
      const content = fs.readFileSync(file, 'utf-8');
      const enhancements = this.suggestTestEnhancements(content);
      
      if (enhancements.length > 0) {
        const enhancementPath = path.join(
          this.outputDir, 
          'enhancements', 
          `${path.basename(file)}.enhancements.md`
        );
        
        const dir = path.dirname(enhancementPath);
        if (!fs.existsSync(dir)) {
          fs.mkdirSync(dir, { recursive: true });
        }
        
        fs.writeFileSync(enhancementPath, enhancements.join('\n'), 'utf-8');
      }
    }
  }

  private findTestFiles(dir: string): string[] {
    const files: string[] = [];
    const items = fs.readdirSync(dir);
    
    for (const item of items) {
      const fullPath = path.join(dir, item);
      const stat = fs.statSync(fullPath);
      
      if (stat.isDirectory()) {
        files.push(...this.findTestFiles(fullPath));
      } else if (item.endsWith('.test.ts') || item.endsWith('.spec.ts')) {
        files.push(fullPath);
      }
    }
    
    return files;
  }

  private suggestTestEnhancements(content: string): string[] {
    const suggestions: string[] = [];
    
    if (!content.includes('beforeEach') && !content.includes('afterEach')) {
      suggestions.push('- 添加 beforeEach/afterEach 进行测试设置和清理');
    }
    
    if (!content.includes('mock') && !content.includes('vi.fn')) {
      suggestions.push('- 使用 mock 函数隔离外部依赖');
    }
    
    if (!content.includes('describe(')) {
      suggestions.push('- 使用 describe 组织测试用例');
    }
    
    if (!content.includes('边界') && !content.includes('edge case')) {
      suggestions.push('- 添加边界情况测试');
    }
    
    if (!content.includes('async') && !content.includes('await')) {
      suggestions.push('- 添加异步操作测试');
    }
    
    if (!content.includes('error') && !content.includes('throw')) {
      suggestions.push('- 添加错误处理测试');
    }
    
    return suggestions;
  }

  private async generateTestUtilities(): Promise<void> {
    console.log('\n生成测试工具...');
    
    const utilsDir = path.join(this.outputDir, 'test-utilities');
    if (!fs.existsSync(utilsDir)) {
      fs.mkdirSync(utilsDir, { recursive: true });
    }
    
    const testUtils = `import { mount, VueWrapper } from '@vue/test-utils';
import { createPinia, setActivePinia } from 'pinia';
import { vi } from 'vitest';
import type { Component } from 'vue';

interface MountOptions {
  props?: Record<string, any>;
  slots?: Record<string, any>;
  global?: Record<string, any>;
}

export function mountComponent(component: Component, options: MountOptions = {}): VueWrapper {
  return mount(component, {
    props: options.props || {},
    slots: options.slots || {},
    global: {
      plugins: [createPinia()],
      mocks: {
        \$router: {
          push: vi.fn(),
          replace: vi.fn()
        },
        \$route: {
          params: {},
          query: {}
        }
      },
      ...options.global
    }
  });
}

export function createMockStore<T extends Record<string, any>>(initialState: T) {
  return {
    state: initialState,
    actions: {},
    getters: {}
  };
}

export function waitFor(condition: () => boolean, timeout = 1000): Promise<void> {
  return new Promise((resolve, reject) => {
    const startTime = Date.now();
    
    const check = () => {
      if (condition()) {
        resolve();
      } else if (Date.now() - startTime > timeout) {
        reject(new Error('Timeout waiting for condition'));
      } else {
        setTimeout(check, 50);
      }
    };
    
    check();
  });
}

export function mockApiCall(data: any, delay = 0) {
  return vi.fn().mockImplementation(() => {
    return new Promise(resolve => {
      setTimeout(() => resolve({ data }), delay);
    });
  });
}`;

    fs.writeFileSync(path.join(utilsDir, 'test-helpers.ts'), testUtils, 'utf-8');
    
    const mockData = `export const mockProjects = [
  {
    id: '1',
    name: '测试项目1',
    description: '这是一个测试项目',
    status: 'active',
    created_at: '2024-01-01T00:00:00Z'
  },
  {
    id: '2',
    name: '测试项目2',
    description: '这是另一个测试项目',
    status: 'completed',
    created_at: '2024-01-02T00:00:00Z'
  }
];

export const mockTasks = [
  {
    id: '1',
    title: '测试任务1',
    description: '测试任务描述',
    status: 'pending',
    priority: 'high',
    project_id: '1'
  },
  {
    id: '2',
    title: '测试任务2',
    description: '另一个测试任务',
    status: 'completed',
    priority: 'medium',
    project_id: '1'
  }
];

export const mockAgents = [
  {
    id: '1',
    name: '测试代理1',
    type: 'assistant',
    status: 'active'
  }
];`;

    fs.writeFileSync(path.join(utilsDir, 'mock-data.ts'), mockData, 'utf-8');
    
    console.log('测试工具已生成');
  }

  private generateTestReport(): void {
    const reportPath = path.join(this.outputDir, 'test-enhancement-report.json');
    
    const report = {
      timestamp: new Date().toISOString(),
      summary: {
        totalComponents: this.testResults.length,
        componentsWithFullTests: this.testResults.filter(r => r.coverage === 100).length,
        componentsNeedingTests: this.testResults.filter(r => r.coverage < 100).length,
        averageCoverage: this.calculateAverageCoverage(),
        generatedTemplates: this.generatedTemplates.length
      },
      coverage: this.testResults,
      templates: this.generatedTemplates.map(t => ({
        name: t.name,
        type: t.type
      }))
    };
    
    fs.writeFileSync(reportPath, JSON.stringify(report, null, 2), 'utf-8');
    console.log(`\n测试增强报告已生成: ${reportPath}`);
    
    this.generateSummaryReport();
  }

  private calculateAverageCoverage(): number {
    if (this.testResults.length === 0) return 0;
    const total = this.testResults.reduce((sum, r) => sum + r.coverage, 0);
    return Math.round(total / this.testResults.length);
  }

  private generateSummaryReport(): void {
    const summaryPath = path.join(this.outputDir, 'test-enhancement-summary.txt');
    
    const lines = [
      '='.repeat(60),
      '组件测试增强报告',
      '='.repeat(60),
      `生成时间: ${new Date().toLocaleString('zh-CN')}`,
      '',
      '-'.repeat(60),
      '测试覆盖率统计',
      '-'.repeat(60),
      `组件总数: ${this.testResults.length}`,
      `完整测试覆盖: ${this.testResults.filter(r => r.coverage === 100).length}`,
      `部分测试覆盖: ${this.testResults.filter(r => r.coverage > 0 && r.coverage < 100).length}`,
      `无测试覆盖: ${this.testResults.filter(r => r.coverage === 0).length}`,
      `平均覆盖率: ${this.calculateAverageCoverage()}%`,
      '',
      '-'.repeat(60),
      '需要增强测试的组件',
      '-'.repeat(60),
    ];
    
    const needsEnhancement = this.testResults.filter(r => r.coverage < 100);
    needsEnhancement.forEach((result, idx) => {
      lines.push(`\n${idx + 1}. ${result.component}`);
      lines.push(`   当前覆盖率: ${result.coverage}%`);
      lines.push(`   测试质量: ${result.testQuality}`);
      lines.push(`   缺失测试: ${result.missingTests.join(', ')}`);
    });
    
    lines.push('', '-'.repeat(60), '生成的测试模板', '-'.repeat(60));
    lines.push(`总计: ${this.generatedTemplates.length} 个模板`);
    
    const unitTests = this.generatedTemplates.filter(t => t.type === 'unit');
    const integrationTests = this.generatedTemplates.filter(t => t.type === 'integration');
    const e2eTests = this.generatedTemplates.filter(t => t.type === 'e2e');
    
    lines.push(`- 单元测试: ${unitTests.length}`);
    lines.push(`- 集成测试: ${integrationTests.length}`);
    lines.push(`- E2E测试: ${e2eTests.length}`);
    
    lines.push('', '='.repeat(60), '分析完成', '='.repeat(60));
    
    fs.writeFileSync(summaryPath, lines.join('\n'), 'utf-8');
    console.log(`摘要报告已生成: ${summaryPath}`);
  }
}

async function main() {
  const projectRoot = path.resolve(__dirname, '..');
  const outputDir = path.join(projectRoot, 'test-enhancement-reports');
  
  const enhancer = new ComponentTestEnhancer(projectRoot, outputDir);
  await enhancer.enhance();
  
  console.log('\n组件测试增强完成！');
}

main().catch(console.error);

export { ComponentTestEnhancer, TestCoverage };
