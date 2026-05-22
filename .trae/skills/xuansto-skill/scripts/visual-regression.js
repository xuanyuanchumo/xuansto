#!/usr/bin/env node

const fs = require('fs');
const path = require('path');
const { chromium } = require('playwright');
const { PNG } = require('pngjs');
const pixelmatch = require('pixelmatch');

function parseArgs() {
    const args = process.argv.slice(2);
    const params = {
        url: '',
        baselineDir: 'baselines',
        outputDir: 'screenshots',
        threshold: 0.1,
        selector: '',
        renderCheck: false,
        criticalSelectors: ''
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
            case '--selector':
                params.selector = args[++i];
                break;
            case '--render-check':
                params.renderCheck = true;
                break;
            case '--critical-selectors':
                params.criticalSelectors = args[++i];
                break;
            case '--help':
                console.log(`
Visual Regression Test Script (Playwright + pixelmatch)

Usage: node visual-regression.js <url> [options]
       node visual-regression.js --url <url> [options]

Arguments:
  <url>                       Target URL (positional, or use --url)

Options:
  --url <url>                 Target URL (alternative to positional, multiple URLs comma-separated)
  --baseline-dir <dir>        Baseline screenshots directory (default: baselines)
  --output-dir <dir>          Current screenshots output directory (default: screenshots)
  --threshold <percent>       Pixel diff threshold percentage (default: 0.1)
  --selector <css-selector>   CSS selector for component-level screenshot (default: full page)
  --render-check              Enable render verification mode (replaces pixel comparison)
  --critical-selectors <sel>  CSS selectors for visibility check, comma-separated (default: none)
  --help                      Show help information

Examples:
  node visual-regression.js http://localhost:3000
  node visual-regression.js http://localhost:3000 --selector ".main-content"
  node visual-regression.js --url http://localhost:3000,http://localhost:3000/about --threshold 0.5
                `);
                process.exit(0);
            default:
                if (!args[i].startsWith('--') && !params.url) {
                    params.url = args[i];
                }
                break;
        }
    }

    return params;
}

class VisualRegressionTester {
    constructor(options) {
        this.options = options;
        this.urls = options.url.split(',').map(u => u.trim()).filter(u => u.length > 0);
        this.baselineDir = path.resolve(options.baselineDir);
        this.outputDir = path.resolve(options.outputDir);
        this.threshold = options.threshold;
        this.selector = options.selector;
        this.results = [];
    }

    initDirs() {
        for (const dir of [this.baselineDir, this.outputDir]) {
            if (!fs.existsSync(dir)) {
                fs.mkdirSync(dir, { recursive: true });
                console.log(`Created directory: ${dir}`);
            }
        }
    }

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

    async captureScreenshot(page, url, screenshotPath) {
        await page.goto(url, { waitUntil: 'networkidle', timeout: 30000 });
        await page.waitForTimeout(500);

        if (this.selector) {
            const element = await page.$(this.selector);
            if (!element) {
                throw new Error(`Selector "${this.selector}" not found on ${url}`);
            }
            await element.screenshot({ path: screenshotPath });
        } else {
            await page.screenshot({ path: screenshotPath, fullPage: true });
        }
    }

    compareScreenshots(baselinePath, currentPath, diffPath) {
        const baselineData = fs.readFileSync(baselinePath);
        const currentData = fs.readFileSync(currentPath);
        const baselineImg = PNG.sync.read(baselineData);
        const currentImg = PNG.sync.read(currentData);

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

        const { width, height } = baselineImg;
        const diffImg = new PNG({ width, height });
        const diffPixels = pixelmatch(
            baselineImg.data,
            currentImg.data,
            diffImg.data,
            width,
            height,
            { threshold: 0.1 }
        );

        const totalPixels = width * height;
        const diffPercentage = totalPixels > 0 ? (diffPixels / totalPixels) * 100 : 0;

        fs.writeFileSync(diffPath, PNG.sync.write(diffImg));

        return {
            diffPercentage: parseFloat(diffPercentage.toFixed(4)),
            totalPixels,
            diffPixels,
            sizeMismatch: false,
            diffImagePath: diffPath
        };
    }

    async run() {
        this.initDirs();

        if (this.urls.length === 0) {
            throw new Error('No target URL specified. Use --url or provide URL as positional argument.');
        }

        const browser = await chromium.launch();
        const context = await browser.newContext({
            viewport: { width: 1280, height: 720 },
            deviceScaleFactor: 1
        });
        const page = await context.newPage();

        console.log(`\nStarting visual regression test, ${this.urls.length} page(s)${this.selector ? ` (selector: ${this.selector})` : ''}\n`);

        for (const url of this.urls) {
            const filename = this.urlToFilename(url);
            const baselinePath = path.join(this.baselineDir, `${filename}.png`);
            const currentPath = path.join(this.outputDir, `${filename}.png`);
            const diffPath = path.join(this.outputDir, `${filename}-diff.png`);

            console.log(`Testing: ${url}`);

            try {
                await this.captureScreenshot(page, url, currentPath);
                console.log(`  Screenshot saved: ${currentPath}`);

                if (!fs.existsSync(baselinePath)) {
                    fs.copyFileSync(currentPath, baselinePath);
                    console.log(`  Baseline created: ${baselinePath}`);

                    this.results.push({
                        page_url: url,
                        diff_percentage: 0,
                        diff_pixels: 0,
                        total_pixels: 0,
                        status: 'baseline_created',
                        screenshot_path: currentPath,
                        baseline_path: baselinePath
                    });
                    continue;
                }

                const comparison = this.compareScreenshots(baselinePath, currentPath, diffPath);
                const passed = comparison.diffPercentage <= this.threshold;
                const status = passed ? 'passed' : 'failed';

                console.log(`  Diff: ${comparison.diffPercentage}% (threshold: ${this.threshold}%)`);
                console.log(`  Diff pixels: ${comparison.diffPixels} / ${comparison.totalPixels}`);
                console.log(`  Status: ${passed ? 'PASSED' : 'FAILED'}`);

                if (comparison.sizeMismatch) {
                    console.log(`  Size mismatch: baseline ${comparison.baselineSize.width}x${comparison.baselineSize.height}, current ${comparison.currentSize.width}x${comparison.currentSize.height}`);
                }

                if (comparison.diffImagePath) {
                    console.log(`  Diff image: ${comparison.diffImagePath}`);
                }

                this.results.push({
                    page_url: url,
                    diff_percentage: comparison.diffPercentage,
                    diff_pixels: comparison.diffPixels,
                    total_pixels: comparison.totalPixels,
                    status,
                    screenshot_path: currentPath,
                    baseline_path: baselinePath,
                    diff_image_path: comparison.diffImagePath || null,
                    size_mismatch: comparison.sizeMismatch || false
                });
            } catch (e) {
                console.error(`  Error: ${e.message}`);

                this.results.push({
                    page_url: url,
                    diff_percentage: -1,
                    diff_pixels: 0,
                    total_pixels: 0,
                    status: 'error',
                    screenshot_path: currentPath,
                    error: e.message
                });
            }
        }

        await browser.close();

        return this.generateReport();
    }

    generateReport() {
        const passed = this.results.filter(r => r.status === 'passed' || r.status === 'baseline_created').length;
        const failed = this.results.filter(r => r.status === 'failed' || r.status === 'error').length;

        return {
            timestamp: new Date().toISOString(),
            total_pages: this.results.length,
            passed,
            failed,
            threshold: this.threshold,
            selector: this.selector || null,
            results: this.results
        };
    }
}

class RenderChecker {
    constructor(options) {
        this.urls = options.url.split(',').map(u => u.trim()).filter(u => u.length > 0);
        this.criticalSelectors = options.criticalSelectors
            ? options.criticalSelectors.split(',').map(s => s.trim()).filter(s => s.length > 0)
            : [];
        this.results = [];
    }

    async checkPageRender(page, url) {
        const result = {
            page_url: url,
            status: 'passed',
            checks: {
                not_blank: true,
                no_js_errors: true,
                critical_elements_visible: true,
                http_status_ok: true
            },
            js_errors: [],
            invisible_elements: [],
            http_status: null
        };

        const jsErrors = [];
        const consoleErrors = [];
        let httpStatus = null;

        page.on('pageerror', error => {
            jsErrors.push(error.message);
        });

        page.on('console', msg => {
            if (msg.type() === 'error') {
                consoleErrors.push(msg.text());
            }
        });

        page.on('response', response => {
            if (!httpStatus && response.url() === url) {
                httpStatus = response.status();
            }
        });

        try {
            await page.goto(url, { waitUntil: 'networkidle', timeout: 30000 });
            await page.waitForTimeout(500);

            result.http_status = httpStatus;

            if (httpStatus && (httpStatus < 200 || httpStatus >= 400)) {
                result.checks.http_status_ok = false;
            }

            const innerHTMLLength = await page.evaluate(() => document.body.innerHTML.length);
            const innerTextLength = await page.evaluate(() => document.body.innerText.length);
            if (innerHTMLLength === 0 || innerTextLength === 0) {
                result.checks.not_blank = false;
            }

            if (this.criticalSelectors.length > 0) {
                for (const selector of this.criticalSelectors) {
                    const element = await page.$(selector);
                    if (!element) {
                        result.checks.critical_elements_visible = false;
                        result.invisible_elements.push({ selector, reason: 'not_found' });
                        continue;
                    }
                    const visible = await element.isVisible();
                    if (!visible) {
                        result.checks.critical_elements_visible = false;
                        result.invisible_elements.push({ selector, reason: 'not_visible' });
                    }
                }
            }

            const allErrors = [...jsErrors, ...consoleErrors];
            if (allErrors.length > 0) {
                result.checks.no_js_errors = false;
                result.js_errors = allErrors;
            }

            const allChecksPassed = Object.values(result.checks).every(v => v === true);
            result.status = allChecksPassed ? 'passed' : 'failed';

        } catch (e) {
            result.status = 'error';
            result.js_errors.push(e.message);
        }

        return result;
    }

    async run() {
        if (this.urls.length === 0) {
            throw new Error('No target URL specified. Use --url or provide URL as positional argument.');
        }

        const browser = await chromium.launch();
        const context = await browser.newContext({
            viewport: { width: 1280, height: 720 },
            deviceScaleFactor: 1
        });
        const page = await context.newPage();

        console.log(`\nStarting render check, ${this.urls.length} page(s)${this.criticalSelectors.length ? ` (critical selectors: ${this.criticalSelectors.join(', ')})` : ''}\n`);

        for (const url of this.urls) {
            console.log(`Checking: ${url}`);
            const result = await this.checkPageRender(page, url);
            this.results.push(result);

            const icon = result.status === 'passed' ? '[PASS]' :
                         result.status === 'failed' ? '[FAIL]' : '[ERR]';
            console.log(`  ${icon} ${url}`);
            console.log(`    not_blank: ${result.checks.not_blank}, no_js_errors: ${result.checks.no_js_errors}, critical_elements_visible: ${result.checks.critical_elements_visible}, http_status_ok: ${result.checks.http_status_ok}`);
            if (result.http_status) {
                console.log(`    HTTP status: ${result.http_status}`);
            }
            if (result.js_errors.length > 0) {
                console.log(`    JS errors: ${result.js_errors.length}`);
            }
            if (result.invisible_elements.length > 0) {
                console.log(`    Invisible elements: ${result.invisible_elements.map(e => e.selector).join(', ')}`);
            }
        }

        await browser.close();

        return this.generateReport();
    }

    generateReport() {
        const passed = this.results.filter(r => r.status === 'passed').length;
        const failed = this.results.filter(r => r.status === 'failed' || r.status === 'error').length;

        return {
            timestamp: new Date().toISOString(),
            total_pages: this.results.length,
            passed,
            failed,
            mode: 'render-check',
            results: this.results
        };
    }
}

function printSummary(report) {
    console.log('\n' + '='.repeat(60));
    console.log('Visual Regression Test Results');
    console.log('='.repeat(60));
    console.log(`Total pages: ${report.total_pages}`);
    console.log(`Passed: ${report.passed}`);
    console.log(`Failed: ${report.failed}`);
    console.log(`Threshold: ${report.threshold}%`);
    if (report.selector) {
        console.log(`Selector: ${report.selector}`);
    }

    for (const result of report.results) {
        const icon = result.status === 'passed' ? '[PASS]' :
                     result.status === 'baseline_created' ? '[NEW]' :
                     result.status === 'failed' ? '[FAIL]' : '[ERR]';
        console.log(`  ${icon} ${result.page_url} - ${result.diff_percentage}% (${result.diff_pixels}/${result.total_pixels} pixels)`);
    }

    console.log('='.repeat(60));
}

function printRenderCheckSummary(report) {
    console.log('\n' + '='.repeat(60));
    console.log('Render Check Results');
    console.log('='.repeat(60));
    console.log(`Total pages: ${report.total_pages}`);
    console.log(`Passed: ${report.passed}`);
    console.log(`Failed: ${report.failed}`);

    for (const result of report.results) {
        const icon = result.status === 'passed' ? '[PASS]' :
                     result.status === 'failed' ? '[FAIL]' : '[ERR]';
        console.log(`  ${icon} ${result.page_url}`);
        console.log(`       not_blank: ${result.checks.not_blank}, no_js_errors: ${result.checks.no_js_errors}, critical_elements_visible: ${result.checks.critical_elements_visible}, http_status_ok: ${result.checks.http_status_ok}`);
        if (result.http_status) {
            console.log(`       HTTP status: ${result.http_status}`);
        }
        if (result.js_errors.length > 0) {
            for (const err of result.js_errors) {
                console.log(`       JS error: ${err}`);
            }
        }
        if (result.invisible_elements.length > 0) {
            for (const el of result.invisible_elements) {
                console.log(`       Invisible: ${el.selector} (${el.reason})`);
            }
        }
    }

    console.log('='.repeat(60));
}

function saveReport(report, outputDir) {
    const reportDir = path.resolve(outputDir);
    if (!fs.existsSync(reportDir)) {
        fs.mkdirSync(reportDir, { recursive: true });
    }

    const timestamp = new Date().toISOString().replace(/[:.]/g, '-').slice(0, 19);
    const reportFile = path.join(reportDir, `visual-regression-${timestamp}.json`);
    fs.writeFileSync(reportFile, JSON.stringify(report, null, 2), 'utf8');
    console.log(`\nReport saved: ${reportFile}`);
}

async function main() {
    const args = parseArgs();

    if (!args.url) {
        console.error('Error: No target URL specified. Use --url or provide URL as positional argument.');
        console.log('Use --help for usage information');
        process.exit(1);
    }

    if (args.renderCheck) {
        const checker = new RenderChecker(args);
        const report = await checker.run();

        saveReport(report, args.outputDir);
        printRenderCheckSummary(report);

        if (report.failed > 0) {
            process.exit(1);
        }
    } else {
        const tester = new VisualRegressionTester(args);
        const report = await tester.run();

        saveReport(report, args.outputDir);
        printSummary(report);

        if (report.failed > 0) {
            process.exit(1);
        }
    }
}

module.exports = { VisualRegressionTester, RenderChecker, parseArgs };

if (require.main === module) {
    main().catch(err => {
        console.error('Fatal error:', err.message);
        process.exit(1);
    });
}
