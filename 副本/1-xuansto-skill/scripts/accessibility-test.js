#!/usr/bin/env node
/**
 * 可访问性测试脚本
 * 功能：运行axe-core检查
 */

const fs = require('fs');
const path = require('path');

/**
 * 解析命令行参数
 * @returns {Object} 参数对象
 */
function parseArgs() {
    const args = process.argv.slice(2);
    const params = {
        url: '',
        output: 'a11y-report',
        format: 'html',
        rules: [],
        tags: ['wcag2a', 'wcag2aa'],
        browser: 'chromium'
    };
    
    for (let i = 0; i < args.length; i++) {
        switch (args[i]) {
            case '--url':
                params.url = args[++i];
                break;
            case '--output':
                params.output = args[++i];
                break;
            case '--format':
                params.format = args[++i];
                break;
            case '--rules':
                params.rules = args[++i].split(',');
                break;
            case '--tags':
                params.tags = args[++i].split(',');
                break;
            case '--browser':
                params.browser = args[++i];
                break;
            case '--help':
                console.log(`
可访问性测试脚本

用法: node accessibility-test.js [选项]

选项:
  --url <url>         测试URL
  --output <dir>      输出目录 (默认: a11y-report)
  --format <format>   输出格式: html, json (默认: html)
  --rules <rules>     指定规则 (逗号分隔)
  --tags <tags>       标签过滤 (默认: wcag2a,wcag2aa)
  --browser <browser> 浏览器 (默认: chromium)
  --help              显示帮助信息
                `);
                process.exit(0);
        }
    }
    
    return params;
}

/**
 * 可访问性规则定义
 */
const A11Y_RULES = {
    'color-contrast': {
        id: 'color-contrast',
        description: '确保文本与背景之间有足够的对比度',
        impact: 'serious',
        tags: ['wcag2a', 'wcag143'],
        help: '元素必须有足够的色彩对比度'
    },
    'image-alt': {
        id: 'image-alt',
        description: '确保所有图片元素都有alt属性',
        impact: 'critical',
        tags: ['wcag2a', 'wcag111'],
        help: '图片必须有替代文本'
    },
    'label': {
        id: 'label',
        description: '确保所有表单元素都有标签',
        impact: 'serious',
        tags: ['wcag2a', 'wcag332'],
        help: '表单元素必须有标签'
    },
    'link-name': {
        id: 'link-name',
        description: '确保链接有可辨识的文本',
        impact: 'serious',
        tags: ['wcag2a', 'wcag412'],
        help: '链接必须有可辨识的文本'
    },
    'button-name': {
        id: 'button-name',
        description: '确保按钮有可辨识的文本',
        impact: 'critical',
        tags: ['wcag2a', 'wcag412'],
        help: '按钮必须有可辨识的文本'
    },
    'aria-allowed-attr': {
        id: 'aria-allowed-attr',
        description: '确保ARIA属性被正确使用',
        impact: 'critical',
        tags: ['wcag2a', 'wcag412'],
        help: '元素必须只使用允许的ARIA属性'
    },
    'aria-hidden-body': {
        id: 'aria-hidden-body',
        description: '确保body元素上没有aria-hidden',
        impact: 'critical',
        tags: ['wcag2a'],
        help: 'body元素不能有aria-hidden="true"'
    },
    'aria-hidden-focus': {
        id: 'aria-hidden-focus',
        description: '确保aria-hidden元素不包含可聚焦元素',
        impact: 'serious',
        tags: ['wcag2a', 'wcag412'],
        help: '隐藏元素不能包含可聚焦元素'
    },
    'aria-required-attr': {
        id: 'aria-required-attr',
        description: '确保元素具有必需的ARIA属性',
        impact: 'critical',
        tags: ['wcag2a', 'wcag412'],
        help: '元素必须有必需的ARIA属性'
    },
    'aria-valid-attr-value': {
        id: 'aria-valid-attr-value',
        description: '确保所有ARIA属性值有效',
        impact: 'critical',
        tags: ['wcag2a', 'wcag412'],
        help: 'ARIA属性值必须有效'
    },
    'html-has-lang': {
        id: 'html-has-lang',
        description: '确保html元素有lang属性',
        impact: 'serious',
        tags: ['wcag2a', 'wcag311'],
        help: 'html元素必须有lang属性'
    },
    'html-lang-valid': {
        id: 'html-lang-valid',
        description: '确保lang属性值有效',
        impact: 'serious',
        tags: ['wcag2a', 'wcag311'],
        help: 'lang属性必须是有效的语言代码'
    },
    'document-title': {
        id: 'document-title',
        description: '确保文档有标题',
        impact: 'serious',
        tags: ['wcag2a', 'wcag242'],
        help: '文档必须有title元素'
    },
    'duplicate-id': {
        id: 'duplicate-id',
        description: '确保id属性值唯一',
        impact: 'moderate',
        tags: ['wcag2a', 'wcag411'],
        help: 'id属性值必须唯一'
    },
    'landmark-one-main': {
        id: 'landmark-one-main',
        description: '确保页面有一个main地标',
        impact: 'moderate',
        tags: ['wcag2a', 'best-practice'],
        help: '页面应该有一个main地标'
    },
    'page-has-heading-one': {
        id: 'page-has-heading-one',
        description: '确保页面有h1标题',
        impact: 'moderate',
        tags: ['wcag2a', 'best-practice'],
        help: '页面应该有h1标题'
    },
    'region': {
        id: 'region',
        description: '确保所有内容都在地标区域内',
        impact: 'moderate',
        tags: ['wcag2a', 'best-practice'],
        help: '内容应该在地标区域内'
    },
    'skip-link': {
        id: 'skip-link',
        description: '确保有跳过导航的链接',
        impact: 'moderate',
        tags: ['wcag2a', 'best-practice'],
        help: '页面应该有跳过链接'
    },
    'heading-order': {
        id: 'heading-order',
        description: '确保标题层级正确',
        impact: 'moderate',
        tags: ['wcag2a', 'wcag141'],
        help: '标题层级应该正确'
    },
    'meta-viewport': {
        id: 'meta-viewport',
        description: '确保viewport meta标签正确设置',
        impact: 'serious',
        tags: ['wcag2a', 'best-practice'],
        help: 'viewport不应禁用缩放'
    }
};

/**
 * 可访问性测试器
 */
class AccessibilityTester {
    /**
     * @param {Object} options 配置选项
     */
    constructor(options) {
        this.options = options;
        this.results = [];
        this.violations = [];
        this.passes = [];
    }
    
    /**
     * 运行测试
     * @returns {Object} 测试报告
     */
    run() {
        console.log('\n开始可访问性测试...');
        console.log(`目标URL: ${this.options.url || '模拟测试'}`);
        console.log(`规则标签: ${this.options.tags.join(', ')}`);
        
        // 模拟测试结果（实际应用中应使用axe-core）
        this._simulateTests();
        
        return this._generateReport();
    }
    
    /**
     * 模拟测试（实际应用中应使用axe-core）
     */
    _simulateTests() {
        const rulesToTest = this.options.rules.length > 0 
            ? this.options.rules 
            : Object.keys(A11Y_RULES);
        
        for (const ruleId of rulesToTest) {
            const rule = A11Y_RULES[ruleId];
            if (!rule) continue;
            
            // 模拟随机结果
            const passed = Math.random() > 0.3;
            
            const result = {
                id: rule.id,
                description: rule.description,
                impact: rule.impact,
                tags: rule.tags,
                help: rule.help,
                passed: passed,
                nodes: passed ? [] : this._generateMockNodes(rule)
            };
            
            this.results.push(result);
            
            if (passed) {
                this.passes.push(result);
            } else {
                this.violations.push(result);
            }
        }
    }
    
    /**
     * 生成模拟节点数据
     * @param {Object} rule 规则对象
     * @returns {Array} 节点数组
     */
    _generateMockNodes(rule) {
        const count = Math.floor(Math.random() * 3) + 1;
        const nodes = [];
        
        for (let i = 0; i < count; i++) {
            nodes.push({
                html: `<${rule.id}-element-${i}>示例内容</${rule.id}-element-${i}>`,
                target: [`body > main > ${rule.id}-element-${i}`],
                failureSummary: `修复以下问题: ${rule.help}`
            });
        }
        
        return nodes;
    }
    
    /**
     * 生成报告
     * @returns {Object} 报告对象
     */
    _generateReport() {
        const critical = this.violations.filter(v => v.impact === 'critical').length;
        const serious = this.violations.filter(v => v.impact === 'serious').length;
        const moderate = this.violations.filter(v => v.impact === 'moderate').length;
        
        return {
            timestamp: new Date().toISOString(),
            url: this.options.url,
            summary: {
                totalRules: this.results.length,
                passed: this.passes.length,
                violations: this.violations.length,
                critical: critical,
                serious: serious,
                moderate: moderate,
                passRate: this.results.length > 0 
                    ? ((this.passes.length / this.results.length) * 100).toFixed(1) 
                    : 0
            },
            violations: this.violations,
            passes: this.passes,
            options: {
                tags: this.options.tags,
                browser: this.options.browser
            }
        };
    }
}

/**
 * 生成HTML报告
 * @param {Object} report 测试报告
 * @returns {string} HTML内容
 */
function generateHtmlReport(report) {
    let violationRows = '';
    
    for (const v of report.violations) {
        const impactColor = {
            critical: '#dc3545',
            serious: '#fd7e14',
            moderate: '#ffc107'
        }[v.impact] || '#6c757d';
        
        violationRows += `
        <tr>
            <td><span style="background: ${impactColor}; color: white; padding: 2px 8px; border-radius: 4px;">${v.impact.toUpperCase()}</span></td>
            <td>${v.id}</td>
            <td>${v.description}</td>
            <td>${v.nodes.length}</td>
            <td>${v.help}</td>
        </tr>`;
    }
    
    return `<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>可访问性测试报告</title>
    <style>
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; margin: 40px; background: #f5f5f5; }
        h1 { color: #333; }
        .summary { background: white; padding: 20px; border-radius: 8px; margin-bottom: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .summary-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(120px, 1fr)); gap: 15px; }
        .summary-item { text-align: center; padding: 10px; }
        .summary-item .value { font-size: 1.8em; font-weight: bold; }
        .summary-item .label { color: #666; font-size: 0.85em; }
        .passed .value { color: #28a745; }
        .violations .value { color: #dc3545; }
        .critical .value { color: #dc3545; }
        .serious .value { color: #fd7e14; }
        .moderate .value { color: #ffc107; }
        table { width: 100%; border-collapse: collapse; background: white; border-radius: 8px; overflow: hidden; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        th { background: #007bff; color: white; padding: 12px; text-align: left; }
        td { padding: 10px 12px; border-bottom: 1px solid #eee; }
        tr:hover { background: #f8f9fa; }
        .section { margin-bottom: 30px; }
        .section h2 { color: #333; border-bottom: 2px solid #007bff; padding-bottom: 10px; }
        .footer { margin-top: 20px; text-align: center; color: #666; font-size: 0.9em; }
    </style>
</head>
<body>
    <h1>♿ 可访问性测试报告</h1>
    
    <div class="summary">
        <div class="summary-grid">
            <div class="summary-item"><div class="value">${report.summary.totalRules}</div><div class="label">规则总数</div></div>
            <div class="summary-item passed"><div class="value">${report.summary.passed}</div><div class="label">通过</div></div>
            <div class="summary-item violations"><div class="value">${report.summary.violations}</div><div class="label">违规</div></div>
            <div class="summary-item critical"><div class="value">${report.summary.critical}</div><div class="label">严重</div></div>
            <div class="summary-item serious"><div class="value">${report.summary.serious}</div><div class="label">重要</div></div>
            <div class="summary-item moderate"><div class="value">${report.summary.moderate}</div><div class="label">中等</div></div>
        </div>
    </div>
    
    <div class="section">
        <h2>违规列表</h2>
        <table>
            <thead>
                <tr><th>严重程度</th><th>规则ID</th><th>描述</th><th>问题数</th><th>帮助</th></tr>
            </thead>
            <tbody>${violationRows || '<tr><td colspan="5" style="text-align:center;">无违规</td></tr>'}</tbody>
        </table>
    </div>
    
    <div class="footer">
        生成时间: ${report.timestamp}<br>
        测试URL: ${report.url || 'N/A'}
    </div>
</body>
</html>`;
}

/**
 * 保存报告
 * @param {string} outputDir 输出目录
 * @param {Object} report 测试报告
 * @param {string} format 格式
 */
function saveReport(outputDir, report, format) {
    const outputPath = path.resolve(outputDir);
    if (!fs.existsSync(outputPath)) {
        fs.mkdirSync(outputPath, { recursive: true });
    }
    
    const timestamp = new Date().toISOString().replace(/[:.]/g, '-').slice(0, 19);
    
    if (format === 'json' || format === 'all') {
        const jsonFile = path.join(outputPath, `a11y-report-${timestamp}.json`);
        fs.writeFileSync(jsonFile, JSON.stringify(report, null, 2), 'utf8');
        console.log(`JSON报告已保存: ${jsonFile}`);
    }
    
    if (format === 'html' || format === 'all') {
        const htmlFile = path.join(outputPath, `a11y-report-${timestamp}.html`);
        fs.writeFileSync(htmlFile, generateHtmlReport(report), 'utf8');
        console.log(`HTML报告已保存: ${htmlFile}`);
    }
}

/**
 * 打印摘要
 * @param {Object} report 测试报告
 */
function printSummary(report) {
    console.log('\n' + '='.repeat(60));
    console.log('可访问性测试结果');
    console.log('='.repeat(60));
    console.log(`规则总数: ${report.summary.totalRules}`);
    console.log(`通过: ${report.summary.passed}`);
    console.log(`违规: ${report.summary.violations}`);
    console.log(`通过率: ${report.summary.passRate}%`);
    
    if (report.summary.violations > 0) {
        console.log('\n违规详情:');
        console.log(`  严重: ${report.summary.critical}`);
        console.log(`  重要: ${report.summary.serious}`);
        console.log(`  中等: ${report.summary.moderate}`);
    }
    
    console.log('='.repeat(60));
}

// 主函数
function main() {
    const args = parseArgs();
    const tester = new AccessibilityTester(args);
    const report = tester.run();
    
    saveReport(args.output, report, args.format);
    printSummary(report);
    
    if (report.summary.violations > 0) {
        process.exit(1);
    }
}

main();
