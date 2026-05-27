#!/usr/bin/env node
/**
 * 视觉回归测试脚本
 * 功能：对比截图差异
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
        baseline: 'screenshots/baseline',
        current: 'screenshots/current',
        output: 'visual-diff-report',
        threshold: 0.1,
        format: 'html'
    };
    
    for (let i = 0; i < args.length; i++) {
        switch (args[i]) {
            case '--baseline':
                params.baseline = args[++i];
                break;
            case '--current':
                params.current = args[++i];
                break;
            case '--output':
                params.output = args[++i];
                break;
            case '--threshold':
                params.threshold = parseFloat(args[++i]);
                break;
            case '--format':
                params.format = args[++i];
                break;
            case '--help':
                console.log(`
视觉回归测试脚本

用法: node visual-regression.js [选项]

选项:
  --baseline <dir>    基准截图目录 (默认: screenshots/baseline)
  --current <dir>     当前截图目录 (默认: screenshots/current)
  --output <dir>      输出目录 (默认: visual-diff-report)
  --threshold <n>     差异阈值 (默认: 0.1, 即10%)
  --format <format>   输出格式: html, json (默认: html)
  --help              显示帮助信息
                `);
                process.exit(0);
        }
    }
    
    return params;
}

/**
 * 图像比较器（简化版，不依赖外部库）
 */
class ImageComparator {
    constructor(threshold) {
        this.threshold = threshold;
    }
    
    /**
     * 比较两个图像
     * @param {Buffer} img1 图像1数据
     * @param {Buffer} img2 图像2数据
     * @returns {Object} 比较结果
     */
    compare(img1, img2) {
        const diff = this._calculateDiff(img1, img2);
        
        return {
            diffPercentage: diff,
            passed: diff < this.threshold * 100,
            diffPixels: Math.floor(diff * img1.length / 100),
            totalPixels: img1.length
        };
    }
    
    /**
     * 计算差异百分比
     * @param {Buffer} a 图像A
     * @param {Buffer} b 图像B
     * @returns {number} 差异百分比
     */
    _calculateDiff(a, b) {
        if (a.length !== b.length) {
            return 100;
        }
        
        let diffCount = 0;
        const sampleSize = Math.min(a.length, 10000);
        
        for (let i = 0; i < sampleSize; i++) {
            const idx = Math.floor(Math.random() * a.length);
            if (a[idx] !== b[idx]) {
                diffCount++;
            }
        }
        
        return (diffCount / sampleSize) * 100;
    }
}

/**
 * 视觉回归测试器
 */
class VisualRegressionTester {
    constructor(options) {
        this.options = options;
        this.comparator = new ImageComparator(options.threshold);
        this.results = [];
    }
    
    /**
     * 运行测试
     * @returns {Object} 测试报告
     */
    run() {
        const baselineDir = path.resolve(this.options.baseline);
        const currentDir = path.resolve(this.options.current);
        
        if (!fs.existsSync(baselineDir)) {
            console.error(`基准目录不存在: ${baselineDir}`);
            return this._createEmptyReport();
        }
        
        if (!fs.existsSync(currentDir)) {
            console.error(`当前目录不存在: ${currentDir}`);
            return this._createEmptyReport();
        }
        
        console.log(`\n开始视觉回归测试...`);
        console.log(`基准目录: ${baselineDir}`);
        console.log(`当前目录: ${currentDir}`);
        console.log(`差异阈值: ${this.options.threshold * 100}%`);
        
        const baselineImages = this._collectImages(baselineDir);
        const currentImages = this._collectImages(currentDir);
        
        this.results = [];
        
        for (const [name, baselinePath] of baselineImages) {
            if (currentImages.has(name)) {
                const result = this._compareImages(
                    name,
                    baselinePath,
                    currentImages.get(name)
                );
                this.results.push(result);
            } else {
                this.results.push({
                    name: name,
                    status: 'missing-current',
                    passed: false,
                    message: '当前版本缺少此截图'
                });
            }
        }
        
        for (const [name, currentPath] of currentImages) {
            if (!baselineImages.has(name)) {
                this.results.push({
                    name: name,
                    status: 'new',
                    passed: true,
                    message: '新增截图'
                });
            }
        }
        
        return this._generateReport();
    }
    
    /**
     * 收集图像文件
     * @param {string} dir 目录路径
     * @returns {Map<string, string>} 图像名称到路径的映射
     */
    _collectImages(dir) {
        const images = new Map();
        const extensions = ['.png', '.jpg', '.jpeg', '.webp'];
        
        const collect = (currentDir, prefix = '') => {
            const items = fs.readdirSync(currentDir);
            
            for (const item of items) {
                const fullPath = path.join(currentDir, item);
                const stat = fs.statSync(fullPath);
                
                if (stat.isDirectory()) {
                    collect(fullPath, prefix ? `${prefix}/${item}` : item);
                } else if (extensions.includes(path.extname(item).toLowerCase())) {
                    const name = prefix ? `${prefix}/${item}` : item;
                    images.set(name, fullPath);
                }
            }
        };
        
        collect(dir);
        return images;
    }
    
    /**
     * 比较两个图像
     * @param {string} name 图像名称
     * @param {string} baselinePath 基准路径
     * @param {string} currentPath 当前路径
     * @returns {Object} 比较结果
     */
    _compareImages(name, baselinePath, currentPath) {
        try {
            const baselineData = fs.readFileSync(baselinePath);
            const currentData = fs.readFileSync(currentPath);
            
            const result = this.comparator.compare(baselineData, currentData);
            
            return {
                name: name,
                status: result.passed ? 'passed' : 'failed',
                passed: result.passed,
                diffPercentage: result.diffPercentage.toFixed(2),
                threshold: (this.options.threshold * 100).toFixed(0),
                message: result.passed 
                    ? `差异 ${result.diffPercentage.toFixed(2)}% 在阈值内`
                    : `差异 ${result.diffPercentage.toFixed(2)}% 超过阈值`,
                baselinePath: baselinePath,
                currentPath: currentPath
            };
        } catch (e) {
            return {
                name: name,
                status: 'error',
                passed: false,
                message: `比较失败: ${e.message}`
            };
        }
    }
    
    /**
     * 生成报告
     * @returns {Object} 报告对象
     */
    _generateReport() {
        const passed = this.results.filter(r => r.passed).length;
        const failed = this.results.filter(r => !r.passed).length;
        
        return {
            timestamp: new Date().toISOString(),
            summary: {
                total: this.results.length,
                passed: passed,
                failed: failed,
                passRate: this.results.length > 0 
                    ? ((passed / this.results.length) * 100).toFixed(1) 
                    : 0
            },
            threshold: this.options.threshold,
            results: this.results
        };
    }
    
    /**
     * 创建空报告
     * @returns {Object} 空报告
     */
    _createEmptyReport() {
        return {
            timestamp: new Date().toISOString(),
            summary: { total: 0, passed: 0, failed: 0, passRate: 0 },
            threshold: this.options.threshold,
            results: []
        };
    }
}

/**
 * 生成HTML报告
 * @param {Object} report 测试报告
 * @returns {string} HTML内容
 */
function generateHtmlReport(report) {
    let resultRows = '';
    
    for (const result of report.results) {
        const statusIcon = result.passed ? '✅' : '❌';
        const statusClass = result.passed ? 'passed' : 'failed';
        
        resultRows += `
        <tr class="${statusClass}">
            <td>${statusIcon}</td>
            <td>${result.name}</td>
            <td>${result.status}</td>
            <td>${result.diffPercentage || 'N/A'}</td>
            <td>${report.threshold * 100}%</td>
            <td>${result.message}</td>
        </tr>`;
    }
    
    return `<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>视觉回归测试报告</title>
    <style>
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; margin: 40px; background: #f5f5f5; }
        h1 { color: #333; }
        .summary { background: white; padding: 20px; border-radius: 8px; margin-bottom: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .summary-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 15px; }
        .summary-item { text-align: center; padding: 10px; }
        .summary-item .value { font-size: 2em; font-weight: bold; }
        .summary-item .label { color: #666; font-size: 0.9em; }
        .passed .value { color: #28a745; }
        .failed .value { color: #dc3545; }
        table { width: 100%; border-collapse: collapse; background: white; border-radius: 8px; overflow: hidden; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        th { background: #007bff; color: white; padding: 12px; text-align: left; }
        td { padding: 10px 12px; border-bottom: 1px solid #eee; }
        tr.passed { background: #f8fff8; }
        tr.failed { background: #fff8f8; }
        .footer { margin-top: 20px; text-align: center; color: #666; font-size: 0.9em; }
    </style>
</head>
<body>
    <h1>视觉回归测试报告</h1>
    <div class="summary">
        <div class="summary-grid">
            <div class="summary-item"><div class="value">${report.summary.total}</div><div class="label">总测试数</div></div>
            <div class="summary-item passed"><div class="value">${report.summary.passed}</div><div class="label">通过</div></div>
            <div class="summary-item failed"><div class="value">${report.summary.failed}</div><div class="label">失败</div></div>
            <div class="summary-item"><div class="value">${report.summary.passRate}%</div><div class="label">通过率</div></div>
        </div>
    </div>
    <table>
        <thead><tr><th>状态</th><th>图像名称</th><th>状态</th><th>差异%</th><th>阈值</th><th>消息</th></tr></thead>
        <tbody>${resultRows}</tbody>
    </table>
    <div class="footer">生成时间: ${report.timestamp}</div>
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
        const jsonFile = path.join(outputPath, `visual-diff-${timestamp}.json`);
        fs.writeFileSync(jsonFile, JSON.stringify(report, null, 2), 'utf8');
        console.log(`JSON报告已保存: ${jsonFile}`);
    }
    
    if (format === 'html' || format === 'all') {
        const htmlFile = path.join(outputPath, `visual-diff-${timestamp}.html`);
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
    console.log('视觉回归测试结果');
    console.log('='.repeat(60));
    console.log(`总测试数: ${report.summary.total}`);
    console.log(`通过: ${report.summary.passed}`);
    console.log(`失败: ${report.summary.failed}`);
    console.log(`通过率: ${report.summary.passRate}%`);
    console.log('='.repeat(60));
}

// 主函数
function main() {
    const args = parseArgs();
    const tester = new VisualRegressionTester(args);
    const report = tester.run();
    
    saveReport(args.output, report, args.format);
    printSummary(report);
    
    if (report.summary.failed > 0) {
        process.exit(1);
    }
}

main();
