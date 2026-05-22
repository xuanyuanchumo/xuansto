import * as fs from 'fs';
import * as path from 'path';
import { test, expect, devices } from '@playwright/test';

/**
 * 多设备适配测试器
 * 
 * 功能说明：
 * - 支持多种移动设备、平板和桌面设备的模拟测试
 * - 检测视口问题、触摸目标大小、响应式设计问题
 * - 生成详细的测试报告和截图
 * - 测量性能指标（加载时间、布局偏移等）
 * 
 * 使用方法：
 * ```bash
 * npx ts-node multi_device_tester.ts
 * ```
 * 
 * @author GUI优化子代理
 * @version 1.0.0
 */

interface DeviceConfig {
  name: string;
  width: number;
  height: number;
  deviceScaleFactor: number;
  isMobile: boolean;
  hasTouch: boolean;
}

interface AdaptationIssue {
  device: string;
  component: string;
  issue: string;
  severity: 'critical' | 'major' | 'minor';
  screenshot?: string;
  suggestion: string;
}

interface TestResult {
  device: string;
  url: string;
  passed: boolean;
  issues: AdaptationIssue[];
  metrics: {
    loadTime: number;
    layoutShifts: number;
    contentVisibility: number;
  };
}

const deviceConfigs: DeviceConfig[] = [
  { name: 'iPhone SE', width: 375, height: 667, deviceScaleFactor: 2, isMobile: true, hasTouch: true },
  { name: 'iPhone 12', width: 390, height: 844, deviceScaleFactor: 3, isMobile: true, hasTouch: true },
  { name: 'iPhone 14 Pro Max', width: 430, height: 932, deviceScaleFactor: 3, isMobile: true, hasTouch: true },
  { name: 'Pixel 5', width: 393, height: 851, deviceScaleFactor: 3, isMobile: true, hasTouch: true },
  { name: 'Samsung Galaxy S21', width: 360, height: 800, deviceScaleFactor: 3, isMobile: true, hasTouch: true },
  { name: 'iPad Mini', width: 768, height: 1024, deviceScaleFactor: 2, isMobile: false, hasTouch: true },
  { name: 'iPad Pro', width: 1024, height: 1366, deviceScaleFactor: 2, isMobile: false, hasTouch: true },
  { name: 'Desktop 1280', width: 1280, height: 720, deviceScaleFactor: 1, isMobile: false, hasTouch: false },
  { name: 'Desktop 1920', width: 1920, height: 1080, deviceScaleFactor: 1, isMobile: false, hasTouch: false },
  { name: 'Desktop 2560', width: 2560, height: 1440, deviceScaleFactor: 1, isMobile: false, hasTouch: false }
];

class MultiDeviceTester {
  private baseUrl: string;
  private outputDir: string;
  private testResults: TestResult[] = [];

  constructor(baseUrl: string, outputDir: string) {
    this.baseUrl = baseUrl;
    this.outputDir = outputDir;
  }

  public async runTests(): Promise<TestResult[]> {
    console.log('开始多设备适配测试...');
    
    const pages = [
      '/',
      '/projects',
      '/tasks',
      '/agents',
      '/dashboard'
    ];

    for (const device of deviceConfigs) {
      console.log(`\n测试设备: ${device.name} (${device.width}x${device.height})`);
      
      for (const pagePath of pages) {
        const result = await this.testPage(device, pagePath);
        this.testResults.push(result);
      }
    }

    this.generateReport();
    return this.testResults;
  }

  private async testPage(device: DeviceConfig, pagePath: string): Promise<TestResult> {
    const url = `${this.baseUrl}${pagePath}`;
    const issues: AdaptationIssue[] = [];
    let passed = true;

    try {
      const context = await (await import('@playwright/test')).request.newContext({
        viewport: { width: device.width, height: device.height },
        deviceScaleFactor: device.deviceScaleFactor,
        isMobile: device.isMobile,
        hasTouch: device.hasTouch
      });

      const page = await context.newPage();
      const startTime = Date.now();
      
      await page.goto(url, { waitUntil: 'networkidle' });
      const loadTime = Date.now() - startTime;

      const layoutShifts = await this.measureLayoutShifts(page);
      
      const contentVisibility = await this.checkContentVisibility(page, device);

      const viewportIssues = await this.checkViewportIssues(page, device);
      issues.push(...viewportIssues);

      const touchIssues = device.hasTouch ? await this.checkTouchTargets(page) : [];
      issues.push(...touchIssues);

      const responsiveIssues = await this.checkResponsiveDesign(page, device);
      issues.push(...responsiveIssues);

      const screenshot = await this.takeScreenshot(page, device, pagePath);

      if (issues.some(i => i.severity === 'critical')) {
        passed = false;
      }

      await page.close();
      await context.dispose();

      return {
        device: device.name,
        url,
        passed,
        issues,
        metrics: {
          loadTime,
          layoutShifts,
          contentVisibility
        }
      };
    } catch (error) {
      return {
        device: device.name,
        url,
        passed: false,
        issues: [{
          device: device.name,
          component: 'page',
          issue: `页面加载失败: ${error}`,
          severity: 'critical',
          suggestion: '检查网络连接和服务器状态'
        }],
        metrics: {
          loadTime: 0,
          layoutShifts: 0,
          contentVisibility: 0
        }
      };
    }
  }

  private async measureLayoutShifts(page: any): Promise<number> {
    return await page.evaluate(() => {
      return new Promise<number>((resolve) => {
        let clsValue = 0;
        const observer = new PerformanceObserver((list) => {
          for (const entry of list.getEntries()) {
            if (!(entry as any).hadRecentInput) {
              clsValue += (entry as any).value;
            }
          }
        });
        observer.observe({ type: 'layout-shift', buffered: true });
        
        setTimeout(() => {
          observer.disconnect();
          resolve(clsValue);
        }, 1000);
      });
    });
  }

  private async checkContentVisibility(page: any, device: DeviceConfig): Promise<number> {
    return await page.evaluate((width: number) => {
      const elements = document.querySelectorAll('*');
      let visibleCount = 0;
      let totalCount = 0;

      elements.forEach((el) => {
        const rect = el.getBoundingClientRect();
        if (rect.width > 0 && rect.height > 0) {
          totalCount++;
          if (rect.left >= 0 && rect.right <= width) {
            visibleCount++;
          }
        }
      });

      return totalCount > 0 ? (visibleCount / totalCount) * 100 : 100;
    }, device.width);
  }

  private async checkViewportIssues(page: any, device: DeviceConfig): Promise<AdaptationIssue[]> {
    const issues: AdaptationIssue[] = [];

    const horizontalScroll = await page.evaluate(() => {
      return document.documentElement.scrollWidth > document.documentElement.clientWidth;
    });

    if (horizontalScroll) {
      issues.push({
        device: device.name,
        component: 'viewport',
        issue: '出现水平滚动条',
        severity: 'major',
        suggestion: '检查元素宽度，确保不超出视口'
      });
    }

    const overflowElements = await page.evaluate((width: number) => {
      const elements: string[] = [];
      document.querySelectorAll('*').forEach((el) => {
        const rect = el.getBoundingClientRect();
        if (rect.width > width) {
          elements.push(`${el.tagName}.${el.className}`);
        }
      });
      return elements.slice(0, 5);
    }, device.width);

    if (overflowElements.length > 0) {
      issues.push({
        device: device.name,
        component: 'layout',
        issue: `元素超出视口: ${overflowElements.join(', ')}`,
        severity: 'major',
        suggestion: '使用 max-width: 100% 或响应式单位'
      });
    }

    const smallText = await page.evaluate(() => {
      const elements: string[] = [];
      document.querySelectorAll('*').forEach((el) => {
        const style = window.getComputedStyle(el);
        const fontSize = parseFloat(style.fontSize);
        if (fontSize < 12 && el.textContent && el.textContent.trim().length > 0) {
          elements.push(`${el.tagName} (${fontSize}px)`);
        }
      });
      return elements.slice(0, 5);
    }, device.width);

    if (smallText.length > 0) {
      issues.push({
        device: device.name,
        component: 'typography',
        issue: `字体过小: ${smallText.join(', ')}`,
        severity: 'minor',
        suggestion: '移动端字体最小应为 12px'
      });
    }

    return issues;
  }

  private async checkTouchTargets(page: any): Promise<AdaptationIssue[]> {
    const issues: AdaptationIssue[] = [];

    const smallTargets = await page.evaluate(() => {
      const elements: string[] = [];
      const clickableSelectors = 'button, a, input, select, textarea, [role="button"], [onclick]';
      
      document.querySelectorAll(clickableSelectors).forEach((el) => {
        const rect = el.getBoundingClientRect();
        if (rect.width < 44 || rect.height < 44) {
          elements.push(`${el.tagName}.${el.className} (${Math.round(rect.width)}x${Math.round(rect.height)})`);
        }
      });
      
      return elements.slice(0, 5);
    });

    if (smallTargets.length > 0) {
      issues.push({
        device: 'touch-devices',
        component: 'touch-targets',
        issue: `触摸目标过小: ${smallTargets.join(', ')}`,
        severity: 'major',
        suggestion: '触摸目标最小应为 44x44 像素'
      });
    }

    const closeTargets = await page.evaluate(() => {
      const elements: string[] = [];
      const clickableSelectors = 'button, a, [role="button"]';
      const clickables = Array.from(document.querySelectorAll(clickableSelectors));
      
      for (let i = 0; i < clickables.length; i++) {
        for (let j = i + 1; j < clickables.length; j++) {
          const rect1 = clickables[i].getBoundingClientRect();
          const rect2 = clickables[j].getBoundingClientRect();
          
          const distance = Math.sqrt(
            Math.pow(rect1.left - rect2.left, 2) + 
            Math.pow(rect1.top - rect2.top, 2)
          );
          
          if (distance < 8) {
            elements.push(`${clickables[i].tagName} 和 ${clickables[j].tagName}`);
          }
        }
      }
      
      return elements.slice(0, 3);
    });

    if (closeTargets.length > 0) {
      issues.push({
        device: 'touch-devices',
        component: 'touch-targets',
        issue: `触摸目标距离过近: ${closeTargets.join(', ')}`,
        severity: 'minor',
        suggestion: '触摸目标之间应保持至少 8px 间距'
      });
    }

    return issues;
  }

  private async checkResponsiveDesign(page: any, device: DeviceConfig): Promise<AdaptationIssue[]> {
    const issues: AdaptationIssue[] = [];

    const hasViewportMeta = await page.evaluate(() => {
      const meta = document.querySelector('meta[name="viewport"]');
      return meta !== null;
    });

    if (!hasViewportMeta) {
      issues.push({
        device: device.name,
        component: 'meta',
        issue: '缺少 viewport meta 标签',
        severity: 'critical',
        suggestion: '添加 <meta name="viewport" content="width=device-width, initial-scale=1.0">'
      });
    }

    const mediaQueries = await page.evaluate(() => {
      const styles = Array.from(document.styleSheets)
        .filter(sheet => {
          try {
            return sheet.cssRules !== null;
          } catch {
            return false;
          }
        })
        .flatMap(sheet => Array.from(sheet.cssRules))
        .filter(rule => rule.type === CSSRule.MEDIA_RULE);
      
      return mediaQueries.length;
    });

    if (device.isMobile && mediaQueries === 0) {
      issues.push({
        device: device.name,
        component: 'styles',
        issue: '未检测到媒体查询',
        severity: 'minor',
        suggestion: '添加响应式媒体查询以适配不同屏幕尺寸'
      });
    }

    const fixedWidthElements = await page.evaluate(() => {
      const elements: string[] = [];
      document.querySelectorAll('*').forEach((el) => {
        const style = window.getComputedStyle(el);
        const width = style.width;
        if (width && width.endsWith('px') && parseInt(width) > 400) {
          const elClass = el.className ? `.${el.className.split(' ')[0]}` : '';
          elements.push(`${el.tagName}${elClass} (${width})`);
        }
      });
      return elements.slice(0, 5);
    });

    if (fixedWidthElements.length > 0 && device.isMobile) {
      issues.push({
        device: device.name,
        component: 'layout',
        issue: `固定宽度元素: ${fixedWidthElements.join(', ')}`,
        severity: 'major',
        suggestion: '使用相对单位或 max-width 替代固定宽度'
      });
    }

    return issues;
  }

  private async takeScreenshot(page: any, device: DeviceConfig, pagePath: string): Promise<string> {
    const screenshotDir = path.join(this.outputDir, 'screenshots');
    if (!fs.existsSync(screenshotDir)) {
      fs.mkdirSync(screenshotDir, { recursive: true });
    }

    const filename = `${device.name.replace(/\s+/g, '-')}-${pagePath.replace(/\//g, '-')}.png`;
    const screenshotPath = path.join(screenshotDir, filename);
    
    await page.screenshot({ path: screenshotPath, fullPage: true });
    
    return screenshotPath;
  }

  private generateReport(): void {
    const reportPath = path.join(this.outputDir, 'device-adaptation-report.json');
    
    const report = {
      timestamp: new Date().toISOString(),
      summary: {
        totalTests: this.testResults.length,
        passed: this.testResults.filter(r => r.passed).length,
        failed: this.testResults.filter(r => !r.passed).length,
        devices: deviceConfigs.map(d => d.name),
        averageLoadTime: this.calculateAverageLoadTime(),
        averageLayoutShift: this.calculateAverageLayoutShift()
      },
      results: this.testResults
    };

    fs.writeFileSync(reportPath, JSON.stringify(report, null, 2), 'utf-8');
    console.log(`\n设备适配报告已生成: ${reportPath}`);

    this.generateSummaryReport();
  }

  private calculateAverageLoadTime(): number {
    const times = this.testResults.map(r => r.metrics.loadTime);
    return Math.round(times.reduce((a, b) => a + b, 0) / times.length);
  }

  private calculateAverageLayoutShift(): number {
    const shifts = this.testResults.map(r => r.metrics.layoutShifts);
    return Math.round((shifts.reduce((a, b) => a + b, 0) / shifts.length) * 1000) / 1000;
  }

  private generateSummaryReport(): void {
    const summaryPath = path.join(this.outputDir, 'device-adaptation-summary.txt');
    
    const lines = [
      '='.repeat(60),
      '多设备适配测试报告',
      '='.repeat(60),
      `生成时间: ${new Date().toLocaleString('zh-CN')}`,
      '',
      '-'.repeat(60),
      '测试概览',
      '-'.repeat(60),
      `总测试数: ${this.testResults.length}`,
      `通过: ${this.testResults.filter(r => r.passed).length}`,
      `失败: ${this.testResults.filter(r => !r.passed).length}`,
      `平均加载时间: ${this.calculateAverageLoadTime()}ms`,
      `平均布局偏移: ${this.calculateAverageLayoutShift()}`,
      '',
      '-'.repeat(60),
      '设备测试结果',
      '-'.repeat(60),
    ];

    const deviceResults = new Map<string, { passed: number; failed: number; issues: number }>();
    
    for (const result of this.testResults) {
      if (!deviceResults.has(result.device)) {
        deviceResults.set(result.device, { passed: 0, failed: 0, issues: 0 });
      }
      const stats = deviceResults.get(result.device)!;
      if (result.passed) stats.passed++;
      else stats.failed++;
      stats.issues += result.issues.length;
    }

    for (const [device, stats] of deviceResults) {
      lines.push(`\n${device}:`);
      lines.push(`  通过: ${stats.passed}, 失败: ${stats.failed}, 问题: ${stats.issues}`);
    }

    lines.push('', '-'.repeat(60), '主要问题', '-'.repeat(60));
    
    const allIssues = this.testResults.flatMap(r => r.issues);
    const criticalIssues = allIssues.filter(i => i.severity === 'critical');
    const majorIssues = allIssues.filter(i => i.severity === 'major');

    if (criticalIssues.length > 0) {
      lines.push(`\n严重问题 (${criticalIssues.length}):`);
      criticalIssues.slice(0, 5).forEach((issue, idx) => {
        lines.push(`  ${idx + 1}. [${issue.device}] ${issue.issue}`);
      });
    }

    if (majorIssues.length > 0) {
      lines.push(`\n重要问题 (${majorIssues.length}):`);
      majorIssues.slice(0, 10).forEach((issue, idx) => {
        lines.push(`  ${idx + 1}. [${issue.device}] ${issue.issue}`);
      });
    }

    lines.push('', '='.repeat(60), '测试完成', '='.repeat(60));

    fs.writeFileSync(summaryPath, lines.join('\n'), 'utf-8');
    console.log(`摘要报告已生成: ${summaryPath}`);
  }
}

async function main() {
  const baseUrl = process.env.BASE_URL || 'http://localhost:5173';
  const outputDir = path.resolve(__dirname, '../device-test-reports');
  
  const tester = new MultiDeviceTester(baseUrl, outputDir);
  await tester.runTests();
  
  console.log('\n多设备适配测试完成！');
}

main().catch(console.error);

export { MultiDeviceTester, DeviceConfig, AdaptationIssue, TestResult };
