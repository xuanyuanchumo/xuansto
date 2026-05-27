#!/usr/bin/env node
/**
 * 视觉回归测试脚本
 * 功能：使用Playwright进行截图对比，检测视觉差异
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
        baselineDir: 'baselines',
        outputDir: 'screenshots',
        threshold: 0.1
    };

    for (let i = 0; i < args.length; i++) {
        switch (args[i]) {
            case '--url':
                params.url = args[++i];
                break;
            case '--baseline-dir':
                params.baselineDir = args[++i];
                break;
            case '--output-dir':
                params.outputDir = args[++i];
                break;
            case '--threshold':
                params.threshold = parseFloat(args[++i]);
                break;
            case '--help':
                console.log(`
视觉回归测试脚本

用法: node visual-regression.js [选项]

选项:
  --url <url>             目标URL (必需，多个URL用逗号分隔)
  --baseline-dir <dir>    基线截图目录 (默认: baselines)
  --output-dir <dir>      当前截图输出目录 (默认: screenshots)
  --threshold <percent>   像素差异阈值百分比 (默认: 0.1)
  --help                  显示帮助信息

示例:
  node visual-regression.js --url http://localhost:3000
  node visual-regression.js --url http://localhost:3000,http://localhost:3000/about --threshold 0.5
                `);
                process.exit(0);
        }
    }

    return params;
}

/**
 * 像素差异计算器
 */
class PixelDiffCalculator {
    /**
     * 比较两个PNG图片的像素数据
     * @param {Buffer} img1Data 图片1的原始像素数据
     * @param {Buffer} img2Data 图片2的原始像素数据
     * @param {number} width 图片宽度
     * @param {number} height 图片高度
     * @returns {Object} 差异结果
     */
    static compare(img1Data, img2Data, width, height) {
        const totalPixels = width * height;
        let diffPixels = 0;
        const channels = 4;

        for (let i = 0; i < img1Data.length; i += channels) {
            const r1 = img1Data[i];
            const g1 = img1Data[i + 1];
            const b1 = img1Data[i + 2];
            const a1 = img1Data[i + 3];

            const r2 = img2Data[i];
            const g2 = img2Data[i + 1];
            const b2 = img2Data[i + 2];
            const a2 = img2Data[i + 3];

            if (r1 !== r2 || g1 !== g2 || b1 !== b2 || a1 !== a2) {
                diffPixels++;
            }
        }

        const diffPercentage = totalPixels > 0 ? (diffPixels / totalPixels) * 100 : 0;

        return {
            totalPixels,
            diffPixels,
            diffPercentage: parseFloat(diffPercentage.toFixed(4))
        };
    }
}

/**
 * 视觉回归测试器
 */
class VisualRegressionTester {
    /**
     * @param {Object} options 配置选项
     */
    constructor(options) {
        this.options = options;
        this.urls = options.url.split(',').map(u => u.trim()).filter(u => u.length > 0);
        this.baselineDir = path.resolve(options.baselineDir);
        this.outputDir = path.resolve(options.outputDir);
        this.threshold = options.threshold;
        this.results = [];
    }

    /**
     * 初始化目录
     */
    initDirs() {
        if (!fs.existsSync(this.baselineDir)) {
            fs.mkdirSync(this.baselineDir, { recursive: true });
            console.log(`创建基线目录: ${this.baselineDir}`);
        }

        if (!fs.existsSync(this.outputDir)) {
            fs.mkdirSync(this.outputDir, { recursive: true });
            console.log(`创建输出目录: ${this.outputDir}`);
        }
    }

    /**
     * 根据URL生成文件名
     * @param {string} url 目标URL
     * @returns {string} 安全的文件名
     */
    urlToFilename(url) {
        try {
            const parsed = new URL(url);
            const name = (parsed.hostname + parsed.pathname)
                .replace(/[^a-zA-Z0-9]/g, '_')
                .replace(/_+/g, '_')
                .replace(/^_|_$/g, '');
            return name || 'index';
        } catch {
            return url.replace(/[^a-zA-Z0-9]/g, '_');
        }
    }

    /**
     * 捕获页面截图
     * @param {import('playwright').Page} page Playwright页面对象
     * @param {string} url 目标URL
     * @param {string} screenshotPath 截图保存路径
     */
    async captureScreenshot(page, url, screenshotPath) {
        await page.goto(url, { waitUntil: 'networkidle', timeout: 30000 });
        await page.waitForTimeout(500);
        await page.screenshot({ path: screenshotPath, fullPage: true });
    }

    /**
     * 比较当前截图与基线
     * @param {string} baselinePath 基线截图路径
     * @param {string} currentPath 当前截图路径
     * @returns {Object} 比较结果
     */
    async compareScreenshots(baselinePath, currentPath) {
        const { PNG } = require('playwright/lib/image_tools/png');

        const baselineImg = PNG.read(fs.readFileSync(baselinePath));
        const currentImg = PNG.read(fs.readFileSync(currentPath));

        if (baselineImg.width !== currentImg.width || baselineImg.height !== currentImg.height) {
            return {
                diffPercentage: 100,
                totalPixels: currentImg.width * currentImg.height,
                diffPixels: currentImg.width * currentImg.height,
                sizeMismatch: true,
                baselineSize: { width: baselineImg.width, height: baselineImg.height },
                currentSize: { width: currentImg.width, height: currentImg.height }
            };
        }

        const result = PixelDiffCalculator.compare(
            baselineImg.data,
            currentImg.data,
            baselineImg.width,
            baselineImg.height
        );

        return {
            ...result,
            sizeMismatch: false
        };
    }

    /**
     * 运行视觉回归测试
     * @returns {Object} 测试报告
     */
    async run() {
        this.initDirs();

        if (this.urls.length === 0) {
            console.error('错误: 未指定目标URL，请使用 --url 参数');
            process.exit(1);
        }

        const browser = await chromium.launch();
        const context = await browser.newContext({
            viewport: { width: 1280, height: 720 },
            deviceScaleFactor: 1
        });
        const page = await context.newPage();

        console.log(`\n开始视觉回归测试，共 ${this.urls.length} 个页面\n`);

        for (const url of this.urls) {
            const filename = this.urlToFilename(url);
            const baselinePath = path.join(this.baselineDir, `${filename}.png`);
            const currentPath = path.join(this.outputDir, `${filename}.png`);

            console.log(`测试页面: ${url}`);

            try {
                await this.captureScreenshot(page, url, currentPath);
                console.log(`  截图已保存: ${currentPath}`);

                if (!fs.existsSync(baselinePath)) {
                    fs.copyFileSync(currentPath, baselinePath);
                    console.log(`  基线不存在，已创建基线: ${baselinePath}`);

                    this.results.push({
                        page_url: url,
                        diff_percentage: 0,
                        status: 'baseline_created',
                        screenshot_path: currentPath,
                        baseline_path: baselinePath
                    });
                    continue;
                }

                const comparison = await this.compareScreenshots(baselinePath, currentPath);
                const passed = comparison.diffPercentage <= this.threshold;
                const status = passed ? 'passed' : 'failed';

                console.log(`  像素差异: ${comparison.diffPercentage}% (阈值: ${this.threshold}%)`);
                console.log(`  状态: ${passed ? '✅ 通过' : '❌ 未通过'}`);

                if (comparison.sizeMismatch) {
                    console.log(`  ⚠️ 尺寸不匹配: 基线 ${comparison.baselineSize.width}x${comparison.baselineSize.height}, 当前 ${comparison.currentSize.width}x${comparison.currentSize.height}`);
                }

                this.results.push({
                    page_url: url,
                    diff_percentage: comparison.diffPercentage,
                    status,
                    screenshot_path: currentPath,
                    baseline_path: baselinePath,
                    diff_pixels: comparison.diffPixels,
                    total_pixels: comparison.totalPixels,
                    size_mismatch: comparison.sizeMismatch || false
                });
            } catch (e) {
                console.error(`  ❌ 测试失败: ${e.message}`);

                this.results.push({
                    page_url: url,
                    diff_percentage: -1,
                    status: 'error',
                    screenshot_path: currentPath,
                    error: e.message
                });
            }
        }

        await browser.close();

        return this.generateReport();
    }

    /**
     * 生成测试报告
     * @returns {Object} JSON报告
     */
    generateReport() {
        const passed = this.results.filter(r => r.status === 'passed' || r.status === 'baseline_created').length;
        const failed = this.results.filter(r => r.status === 'failed' || r.status === 'error').length;

        return {
            timestamp: new Date().toISOString(),
            total_pages: this.results.length,
            passed,
            failed,
            threshold: this.threshold,
            results: this.results
        };
    }
}

/**
 * 打印摘要
 * @param {Object} report 测试报告
 */
function printSummary(report) {
    console.log('\n' + '='.repeat(60));
    console.log('视觉回归测试结果');
    console.log('='.repeat(60));
    console.log(`总页面数: ${report.total_pages}`);
    console.log(`通过: ${report.passed}`);
    console.log(`未通过: ${report.failed}`);
    console.log(`阈值: ${report.threshold}%`);

    for (const result of report.results) {
        const icon = result.status === 'passed' ? '✅' :
                     result.status === 'baseline_created' ? '🆕' :
                     result.status === 'failed' ? '❌' : '⚠️';
        console.log(`  ${icon} ${result.page_url} - ${result.diff_percentage}%`);
    }

    console.log('='.repeat(60));
}

/**
 * 保存报告
 * @param {Object} report 测试报告
 * @param {string} outputDir 输出目录
 */
function saveReport(report, outputDir) {
    const reportDir = path.resolve(outputDir);
    if (!fs.existsSync(reportDir)) {
        fs.mkdirSync(reportDir, { recursive: true });
    }

    const timestamp = new Date().toISOString().replace(/[:.]/g, '-').slice(0, 19);
    const reportFile = path.join(reportDir, `visual-regression-${timestamp}.json`);
    fs.writeFileSync(reportFile, JSON.stringify(report, null, 2), 'utf8');
    console.log(`\n报告已保存: ${reportFile}`);
}

async function main() {
    const args = parseArgs();

    if (!args.url) {
        console.error('错误: 未指定目标URL，请使用 --url 参数');
        console.log('使用 --help 查看帮助信息');
        process.exit(1);
    }

    const tester = new VisualRegressionTester(args);
    const report = await tester.run();

    saveReport(report, args.outputDir);
    printSummary(report);

    if (report.failed > 0) {
        process.exit(1);
    }
}

main().catch(console.error);
