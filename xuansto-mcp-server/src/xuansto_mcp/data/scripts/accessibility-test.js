#!/usr/bin/env node

const fs = require('fs');
const path = require('path');
const { chromium } = require('playwright');
const AxeBuilder = require('@axe-core/playwright').default;

function parseArgs() {
    const args = process.argv.slice(2);
    const params = {
        url: '',
        output: 'accessibility-report.json',
        standard: 'AA'
    };

    for (let i = 0; i < args.length; i++) {
        switch (args[i]) {
            case '--url':
                params.url = args[++i];
                break;
            case '--output':
                params.output = args[++i];
                break;
            case '--standard':
                params.standard = args[++i].toUpperCase();
                break;
            case '--help':
                console.log(`
Accessibility Test Script (Playwright + axe-core)

Usage: node accessibility-test.js <url> [options]
       node accessibility-test.js --url <url> [options]

Arguments:
  <url>               Target URL (positional, or use --url)

Options:
  --url <url>         Target URL (alternative to positional arg, multiple URLs comma-separated)
  --output <file>     Output report file path (default: accessibility-report.json)
  --standard <level>  WCAG compliance level: A, AA (default: AA)
  --help              Show help information

Examples:
  node accessibility-test.js http://localhost:3000
  node accessibility-test.js http://localhost:3000 --standard A
  node accessibility-test.js --url http://localhost:3000,http://localhost:3000/about --output reports/a11y.json
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

const WCAG_TAGS = {
    'A': ['wcag2a'],
    'AA': ['wcag2a', 'wcag2aa']
};

class AccessibilityTester {
    constructor(options) {
        this.options = options;
        this.urls = options.url.split(',').map(u => u.trim()).filter(u => u.length > 0);
        this.standard = options.standard;
        this.results = [];
    }

    getAxeTags() {
        return WCAG_TAGS[this.standard] || WCAG_TAGS['AA'];
    }

    async testPage(page, url) {
        console.log(`Testing: ${url}`);

        try {
            await page.goto(url, { waitUntil: 'networkidle', timeout: 30000 });

            const tags = this.getAxeTags();
            const results = await new AxeBuilder({ page })
                .withTags(tags)
                .analyze();

            const violations = results.violations.map(v => ({
                id: v.id,
                impact: v.impact,
                description: v.description,
                helpUrl: v.helpUrl,
                nodes: v.nodes.map(n => ({
                    html: n.html,
                    target: n.target,
                    failureSummary: n.failureSummary
                }))
            }));

            const passesCount = results.passes ? results.passes.length : 0;
            const incompleteCount = results.incomplete ? results.incomplete.length : 0;

            const byImpact = { critical: 0, serious: 0, moderate: 0, minor: 0 };
            for (const v of violations) {
                if (byImpact.hasOwnProperty(v.impact)) {
                    byImpact[v.impact]++;
                }
            }

            console.log(`  Violations: ${violations.length}`);
            console.log(`  Passes: ${passesCount}`);
            if (violations.length > 0) {
                console.log(`  Impact: ${Object.entries(byImpact).filter(([, c]) => c > 0).map(([k, v]) => `${k}(${v})`).join(', ')}`);
            }

            return {
                page_url: url,
                violations_count: violations.length,
                passes_count: passesCount,
                incomplete_count: incompleteCount,
                violations,
                violations_by_impact: byImpact,
                status: violations.length === 0 ? 'passed' : 'failed'
            };
        } catch (e) {
            console.error(`  Error: ${e.message}`);
            return {
                page_url: url,
                violations_count: 0,
                passes_count: 0,
                incomplete_count: 0,
                violations: [],
                violations_by_impact: { critical: 0, serious: 0, moderate: 0, minor: 0 },
                status: 'error',
                error: e.message
            };
        }
    }

    async run() {
        if (this.urls.length === 0) {
            throw new Error('No target URL specified. Use --url or provide URL as positional argument.');
        }

        if (!WCAG_TAGS[this.standard]) {
            throw new Error(`Unsupported standard "${this.standard}". Supported: A, AA`);
        }

        const browser = await chromium.launch();
        const context = await browser.newContext({
            viewport: { width: 1280, height: 720 }
        });
        const page = await context.newPage();

        console.log(`\nStarting accessibility audit (WCAG 2.1 ${this.standard}), ${this.urls.length} page(s)\n`);

        for (const url of this.urls) {
            const result = await this.testPage(page, url);
            this.results.push(result);
        }

        await browser.close();

        return this.generateReport();
    }

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
            standard: `WCAG 2.1 ${this.standard}`,
            level: this.standard,
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

function printSummary(report) {
    console.log('\n' + '='.repeat(60));
    console.log(`Accessibility Audit Results (${report.standard})`);
    console.log('='.repeat(60));
    console.log(`Total pages: ${report.summary.total_pages}`);
    console.log(`Passed: ${report.summary.passed_pages}`);
    console.log(`Failed: ${report.summary.failed_pages}`);
    console.log(`Errors: ${report.summary.error_pages}`);
    console.log(`Total violations: ${report.summary.total_violations}`);
    console.log(`Total passes: ${report.summary.total_passes}`);
    console.log(`Unique violation types: ${report.unique_violation_types}`);

    if (report.summary.total_violations > 0) {
        console.log('\nViolations by impact:');
        for (const [impact, count] of Object.entries(report.violations_by_impact)) {
            if (count > 0) {
                const icon = impact === 'critical' ? '[CRITICAL]' :
                             impact === 'serious' ? '[SERIOUS]' :
                             impact === 'moderate' ? '[MODERATE]' : '[MINOR]';
                console.log(`  ${icon} ${impact}: ${count}`);
            }
        }

        console.log('\nViolation details:');
        const seen = new Set();
        for (const v of report.violations) {
            if (!seen.has(v.id)) {
                seen.add(v.id);
                console.log(`  - [${v.impact}] ${v.description}`);
                console.log(`    ${v.helpUrl}`);
                console.log(`    Affected nodes: ${v.nodes.length}`);
            }
        }
    }

    console.log('='.repeat(60));
}

function saveReport(report, outputPath) {
    const resolvedPath = path.resolve(outputPath);
    const outputDir = path.dirname(resolvedPath);

    if (!fs.existsSync(outputDir)) {
        fs.mkdirSync(outputDir, { recursive: true });
    }

    fs.writeFileSync(resolvedPath, JSON.stringify(report, null, 2), 'utf8');
    console.log(`\nReport saved: ${resolvedPath}`);
}

async function main() {
    const args = parseArgs();

    if (!args.url) {
        console.error('Error: No target URL specified. Use --url or provide URL as positional argument.');
        console.log('Use --help for usage information');
        process.exit(1);
    }

    const tester = new AccessibilityTester(args);
    const report = await tester.run();

    saveReport(report, args.output);
    printSummary(report);

    const hasViolations = report.summary.failed_pages > 0 || report.summary.error_pages > 0;
    process.exit(hasViolations ? 1 : 0);
}

module.exports = { AccessibilityTester, parseArgs };

if (require.main === module) {
    main().catch(err => {
        console.error('Fatal error:', err.message);
        process.exit(1);
    });
}
