#!/usr/bin/env node
/**
 * 无障碍访问测试脚本
 * 功能：使用Playwright与axe-core进行自动化无障碍测试
 */

const fs = require('fs');
const path = require('path');
const { chromium } = require('playwright');

/**
 * 解析命令行参数
 * @returns {Object} 参数对象
 */
function parseArgs() {
    const args = process.argv.slice(2);
    const params = {
        url: '',
        output: 'accessibility-report.json',
        level: 'AA'
    };

    for (let i = 0; i < args.length; i++) {
        switch (args[i]) {
            case '--url':
                params.url = args[++i];
                break;
            case '--output':
                params.output = args[++i];
                break;
            case '--level':
                params.level = args[++i].toUpperCase();
                break;
            case '--help':
                console.log(`
无障碍访问测试脚本

用法: node accessibility-test.js [选项]

选项:
  --url <url>       目标URL (必需，多个URL用逗号分隔)
  --output <file>   输出报告文件路径 (默认: accessibility-report.json)
  --level <level>   WCAG合规级别: A, AA, AAA (默认: AA)
  --help            显示帮助信息

示例:
  node accessibility-test.js --url http://localhost:3000
  node accessibility-test.js --url http://localhost:3000,http://localhost:3000/about --level AAA
  node accessibility-test.js --url http://localhost:3000 --output reports/a11y.json
                `);
                process.exit(0);
        }
    }

    return params;
}

/**
 * WCAG级别标签映射
 */
const WCAG_LEVELS = {
    'A': { tag: 'wcag2a', label: 'WCAG 2.1 A' },
    'AA': { tag: 'wcag2aa', label: 'WCAG 2.1 AA' },
    'AAA': { tag: 'wcag2aaa', label: 'WCAG 2.1 AAA' }
};

/**
 * 无障碍测试器
 */
class AccessibilityTester {
    /**
     * @param {Object} options 配置选项
     */
    constructor(options) {
        this.options = options;
        this.urls = options.url.split(',').map(u => u.trim()).filter(u => u.length > 0);
        this.level = options.level;
        this.results = [];
    }

    /**
     * 获取axe-core运行标签
     * @returns {string[]} axe-core运行标签
     */
    getAxeRunTags() {
        const tags = ['wcag2a'];

        if (this.level === 'AA' || this.level === 'AAA') {
            tags.push('wcag2aa');
        }

        if (this.level === 'AAA') {
            tags.push('wcag2aaa');
        }

        return tags;
    }

    /**
     * 注入axe-core并执行审计
     * @param {import('playwright').Page} page Playwright页面对象
     * @param {string} url 目标URL
     * @returns {Object} axe审计结果
     */
    async runAxeAudit(page, url) {
        await page.goto(url, { waitUntil: 'networkidle', timeout: 30000 });

        await page.addScriptTag({
            path: require.resolve('axe-core/axe.min.js')
        });

        const tags = this.getAxeRunTags();

        const results = await page.evaluate(async (runTags) => {
            return await axe.run(document, {
                runOnly: {
                    type: 'tag',
                    values: runTags
                },
                resultTypes: ['violations', 'passes']
            });
        }, tags);

        return results;
    }

    /**
     * 处理违规结果
     * @param {Object[]} violations axe违规列表
     * @returns {Object[]} 处理后的违规列表
     */
    processViolations(violations) {
        return violations.map(v => ({
            id: v.id,
            impact: v.impact,
            description: v.description,
            helpUrl: v.helpUrl,
            nodes: v.nodes.length,
            tags: v.tags
        }));
    }

    /**
     * 测试单个页面
     * @param {import('playwright').Page} page Playwright页面对象
     * @param {string} url 目标URL
     * @returns {Object} 页面测试结果
     */
    async testPage(page, url) {
        console.log(`测试页面: ${url}`);

        try {
            const auditResults = await this.runAxeAudit(page, url);

            const violations = this.processViolations(auditResults.violations);
            const passesCount = auditResults.passes ? auditResults.passes.length : 0;

            console.log(`  违规数: ${violations.length}`);
            console.log(`  通过数: ${passesCount}`);

            if (violations.length > 0) {
                const byImpact = {};
                for (const v of violations) {
                    byImpact[v.impact] = (byImpact[v.impact] || 0) + 1;
                }
                console.log(`  影响级别分布: ${Object.entries(byImpact).map(([k, v]) => `${k}(${v})`).join(', ')}`);
            }

            return {
                page_url: url,
                violations_count: violations.length,
                passes_count: passesCount,
                violations,
                status: violations.length === 0 ? 'passed' : 'failed'
            };
        } catch (e) {
            console.error(`  ❌ 测试失败: ${e.message}`);
            return {
                page_url: url,
                violations_count: 0,
                passes_count: 0,
                violations: [],
                status: 'error',
                error: e.message
            };
        }
    }

    /**
     * 运行所有页面测试
     * @returns {Object} 测试报告
     */
    async run() {
        if (this.urls.length === 0) {
            console.error('错误: 未指定目标URL，请使用 --url 参数');
            process.exit(1);
        }

        if (!WCAG_LEVELS[this.level]) {
            console.error(`错误: 不支持的合规级别 "${this.level}"，支持: A, AA, AAA`);
            process.exit(1);
        }

        const browser = await chromium.launch();
        const context = await browser.newContext({
            viewport: { width: 1280, height: 720 }
        });
        const page = await context.newPage();

        console.log(`\n开始无障碍测试 (标准: ${WCAG_LEVELS[this.level].label})，共 ${this.urls.length} 个页面\n`);

        for (const url of this.urls) {
            const result = await this.testPage(page, url);
            this.results.push(result);
        }

        await browser.close();

        return this.generateReport();
    }

    /**
     * 生成测试报告
     * @returns {Object} JSON报告
     */
    generateReport() {
        const totalViolations = this.results.reduce((sum, r) => sum + r.violations_count, 0);
        const totalPasses = this.results.reduce((sum, r) => sum + r.passes_count, 0);
        const allViolations = this.results.flatMap(r => r.violations);

        const violationsByImpact = { critical: 0, serious: 0, moderate: 0, minor: 0 };
        for (const v of allViolations) {
            if (violationsByImpact.hasOwnProperty(v.impact)) {
                violationsByImpact[v.impact]++;
            }
        }

        const uniqueViolationIds = [...new Set(allViolations.map(v => v.id))];

        return {
            timestamp: new Date().toISOString(),
            standard: WCAG_LEVELS[this.level].label,
            level: this.level,
            total_pages: this.results.length,
            violations_count: totalViolations,
            passes_count: totalPasses,
            violations: allViolations,
            violations_by_impact: violationsByImpact,
            unique_violation_types: uniqueViolationIds.length,
            results: this.results,
            summary: {
                total_pages: this.results.length,
                passed_pages: this.results.filter(r => r.status === 'passed').length,
                failed_pages: this.results.filter(r => r.status === 'failed').length,
                error_pages: this.results.filter(r => r.status === 'error').length,
                total_violations: totalViolations,
                total_passes: totalPasses,
                critical_violations: violationsByImpact.critical,
                serious_violations: violationsByImpact.serious
            }
        };
    }
}

/**
 * 打印摘要
 * @param {Object} report 测试报告
 */
function printSummary(report) {
    console.log('\n' + '='.repeat(60));
    console.log(`无障碍测试结果 (${report.standard})`);
    console.log('='.repeat(60));
    console.log(`总页面数: ${report.summary.total_pages}`);
    console.log(`通过页面: ${report.summary.passed_pages}`);
    console.log(`未通过页面: ${report.summary.failed_pages}`);
    console.log(`错误页面: ${report.summary.error_pages}`);
    console.log(`违规总数: ${report.summary.total_violations}`);
    console.log(`通过规则数: ${report.summary.total_passes}`);
    console.log(`唯一违规类型: ${report.unique_violation_types}`);

    if (report.summary.total_violations > 0) {
        console.log('\n违规影响级别分布:');
        for (const [impact, count] of Object.entries(report.violations_by_impact)) {
            if (count > 0) {
                const icon = impact === 'critical' ? '🔴' :
                             impact === 'serious' ? '🟠' :
                             impact === 'moderate' ? '🟡' : '🟢';
                console.log(`  ${icon} ${impact}: ${count}`);
            }
        }

        console.log('\n违规详情:');
        const seen = new Set();
        for (const v of report.violations) {
            if (!seen.has(v.id)) {
                seen.add(v.id);
                console.log(`  - [${v.impact}] ${v.description}`);
                console.log(`    ${v.helpUrl}`);
            }
        }
    }

    console.log('='.repeat(60));
}

/**
 * 保存报告
 * @param {Object} report 测试报告
 * @param {string} outputPath 输出文件路径
 */
function saveReport(report, outputPath) {
    const resolvedPath = path.resolve(outputPath);
    const outputDir = path.dirname(resolvedPath);

    if (!fs.existsSync(outputDir)) {
        fs.mkdirSync(outputDir, { recursive: true });
    }

    fs.writeFileSync(resolvedPath, JSON.stringify(report, null, 2), 'utf8');
    console.log(`\n报告已保存: ${resolvedPath}`);
}

async function main() {
    const args = parseArgs();

    if (!args.url) {
        console.error('错误: 未指定目标URL，请使用 --url 参数');
        console.log('使用 --help 查看帮助信息');
        process.exit(1);
    }

    const tester = new AccessibilityTester(args);
    const report = await tester.run();

    saveReport(report, args.output);
    printSummary(report);

    if (report.summary.failed_pages > 0 || report.summary.error_pages > 0) {
        process.exit(1);
    }
}

main().catch(console.error);
