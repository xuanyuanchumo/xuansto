#!/usr/bin/env node
/**
 * 性能基准测试脚本
 * 功能：运行性能测试并生成报告
 */

const { performance } = require('perf_hooks');
const fs = require('fs');
const path = require('path');

/**
 * 解析命令行参数
 * @returns {Object} 参数对象
 */
function parseArgs() {
    const args = process.argv.slice(2);
    const params = {
        output: 'benchmark-report',
        iterations: 100,
        warmup: 10,
        format: 'json',
        suites: []
    };
    
    for (let i = 0; i < args.length; i++) {
        switch (args[i]) {
            case '--output':
                params.output = args[++i];
                break;
            case '--iterations':
                params.iterations = parseInt(args[++i], 10);
                break;
            case '--warmup':
                params.warmup = parseInt(args[++i], 10);
                break;
            case '--format':
                params.format = args[++i];
                break;
            case '--suite':
                params.suites.push(args[++i]);
                break;
            case '--help':
                console.log(`
性能基准测试脚本

用法: node performance-benchmark.js [选项]

选项:
  --output <dir>      输出目录 (默认: benchmark-report)
  --iterations <n>    迭代次数 (默认: 100)
  --warmup <n>        预热次数 (默认: 10)
  --format <format>   输出格式: json, html (默认: json)
  --suite <name>      指定测试套件 (可多次使用)
  --help              显示帮助信息
                `);
                process.exit(0);
        }
    }
    
    return params;
}

/**
 * 基准测试结果类
 */
class BenchmarkResult {
    /**
     * @param {string} name 测试名称
     */
    constructor(name) {
        this.name = name;
        this.iterations = 0;
        this.totalTime = 0;
        this.minTime = Infinity;
        this.maxTime = 0;
        this.times = [];
        this.errors = [];
    }
    
    /**
     * 添加一次测量结果
     * @param {number} time 耗时(毫秒)
     */
    addMeasurement(time) {
        this.iterations++;
        this.totalTime += time;
        this.minTime = Math.min(this.minTime, time);
        this.maxTime = Math.max(this.maxTime, time);
        this.times.push(time);
    }
    
    /**
     * 添加错误
     * @param {Error} error 错误对象
     */
    addError(error) {
        this.errors.push(error.message);
    }
    
    /**
     * 获取平均耗时
     * @returns {number} 平均耗时(毫秒)
     */
    get avgTime() {
        return this.iterations > 0 ? this.totalTime / this.iterations : 0;
    }
    
    /**
     * 获取标准差
     * @returns {number} 标准差
     */
    get stdDev() {
        if (this.times.length < 2) return 0;
        const avg = this.avgTime;
        const squareDiffs = this.times.map(t => Math.pow(t - avg, 2));
        return Math.sqrt(squareDiffs.reduce((a, b) => a + b, 0) / this.times.length);
    }
    
    /**
     * 获取百分位数
     * @param {number} p 百分位 (0-100)
     * @returns {number} 百分位数值
     */
    getPercentile(p) {
        if (this.times.length === 0) return 0;
        const sorted = [...this.times].sort((a, b) => a - b);
        const index = Math.ceil((p / 100) * sorted.length) - 1;
        return sorted[Math.max(0, index)];
    }
    
    /**
     * 转换为JSON对象
     * @returns {Object} JSON对象
     */
    toJSON() {
        return {
            name: this.name,
            iterations: this.iterations,
            totalTime: this.totalTime,
            avgTime: this.avgTime,
            minTime: this.minTime === Infinity ? 0 : this.minTime,
            maxTime: this.maxTime,
            stdDev: this.stdDev,
            p50: this.getPercentile(50),
            p90: this.getPercentile(90),
            p95: this.getPercentile(95),
            p99: this.getPercentile(99),
            opsPerSecond: this.avgTime > 0 ? 1000 / this.avgTime : 0,
            errors: this.errors
        };
    }
}

/**
 * 基准测试套件类
 */
class BenchmarkSuite {
    /**
     * @param {string} name 套件名称
     */
    constructor(name) {
        this.name = name;
        this.benchmarks = new Map();
        this.beforeAll = null;
        this.afterAll = null;
        this.beforeEach = null;
        this.afterEach = null;
    }
    
    /**
     * 添加基准测试
     * @param {string} name 测试名称
     * @param {Function} fn 测试函数
     */
    add(name, fn) {
        this.benchmarks.set(name, fn);
    }
    
    /**
     * 设置所有测试前的钩子
     * @param {Function} fn 钩子函数
     */
    setBeforeAll(fn) {
        this.beforeAll = fn;
    }
    
    /**
     * 设置所有测试后的钩子
     * @param {Function} fn 钩子函数
     */
    setAfterAll(fn) {
        this.afterAll = fn;
    }
    
    /**
     * 设置每个测试前的钩子
     * @param {Function} fn 钩子函数
     */
    setBeforeEach(fn) {
        this.beforeEach = fn;
    }
    
    /**
     * 设置每个测试后的钩子
     * @param {Function} fn 钩子函数
     */
    setAfterEach(fn) {
        this.afterEach = fn;
    }
    
    /**
     * 运行套件中的所有测试
     * @param {number} iterations 迭代次数
     * @param {number} warmup 预热次数
     * @returns {Array<BenchmarkResult>} 测试结果数组
     */
    async run(iterations, warmup) {
        const results = [];
        
        if (this.beforeAll) {
            await this.beforeAll();
        }
        
        for (const [name, fn] of this.benchmarks) {
            const result = new BenchmarkResult(name);
            
            // 预热
            for (let i = 0; i < warmup; i++) {
                try {
                    if (this.beforeEach) await this.beforeEach();
                    await fn();
                    if (this.afterEach) await this.afterEach();
                } catch (e) {
                    // 预热错误忽略
                }
            }
            
            // 正式测试
            for (let i = 0; i < iterations; i++) {
                try {
                    if (this.beforeEach) await this.beforeEach();
                    
                    const start = performance.now();
                    await fn();
                    const end = performance.now();
                    
                    if (this.afterEach) await this.afterEach();
                    
                    result.addMeasurement(end - start);
                } catch (e) {
                    result.addError(e);
                }
            }
            
            results.push(result);
        }
        
        if (this.afterAll) {
            await this.afterAll();
        }
        
        return results;
    }
}

/**
 * 性能测试运行器
 */
class PerformanceRunner {
    constructor() {
        this.suites = new Map();
    }
    
    /**
     * 创建测试套件
     * @param {string} name 套件名称
     * @param {Function} configure 配置函数
     */
    suite(name, configure) {
        const suite = new BenchmarkSuite(name);
        configure(suite);
        this.suites.set(name, suite);
    }
    
    /**
     * 运行所有测试
     * @param {Object} options 运行选项
     * @returns {Object} 测试报告
     */
    async runAll(options) {
        const report = {
            timestamp: new Date().toISOString(),
            options: {
                iterations: options.iterations,
                warmup: options.warmup
            },
            suites: [],
            summary: {
                totalBenchmarks: 0,
                totalErrors: 0,
                fastestBenchmark: null,
                slowestBenchmark: null
            }
        };
        
        let fastest = { name: '', ops: 0 };
        let slowest = { name: '', ops: Infinity };
        
        for (const [name, suite] of this.suites) {
            if (options.suites.length > 0 && !options.suites.includes(name)) {
                continue;
            }
            
            console.log(`\n运行测试套件: ${name}`);
            const results = await suite.run(options.iterations, options.warmup);
            
            const suiteReport = {
                name: name,
                benchmarks: results.map(r => r.toJSON()),
                summary: {
                    totalBenchmarks: results.length,
                    totalErrors: results.reduce((sum, r) => sum + r.errors.length, 0)
                }
            };
            
            report.suites.push(suiteReport);
            report.summary.totalBenchmarks += results.length;
            report.summary.totalErrors += suiteReport.summary.totalErrors;
            
            // 更新最快/最慢
            for (const r of results) {
                const json = r.toJSON();
                if (json.opsPerSecond > fastest.ops) {
                    fastest = { name: `${name}/${r.name}`, ops: json.opsPerSecond };
                }
                if (json.opsPerSecond < slowest.ops) {
                    slowest = { name: `${name}/${r.name}`, ops: json.opsPerSecond };
                }
            }
        }
        
        report.summary.fastestBenchmark = fastest;
        report.summary.slowestBenchmark = slowest;
        
        return report;
    }
}

/**
 * 生成HTML报告
 * @param {Object} report 测试报告
 * @returns {string} HTML内容
 */
function generateHtmlReport(report) {
    let benchmarkRows = '';
    
    for (const suite of report.suites) {
        for (const bench of suite.benchmarks) {
            const status = bench.errors.length === 0 ? '✅' : '❌';
            benchmarkRows += `
            <tr>
                <td>${status}</td>
                <td>${suite.name}</td>
                <td>${bench.name}</td>
                <td>${bench.avgTime.toFixed(4)}</td>
                <td>${bench.minTime.toFixed(4)}</td>
                <td>${bench.maxTime.toFixed(4)}</td>
                <td>${bench.stdDev.toFixed(4)}</td>
                <td>${bench.opsPerSecond.toFixed(2)}</td>
                <td>${bench.p95.toFixed(4)}</td>
            </tr>
            `;
        }
    }
    
    return `
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>性能基准测试报告</title>
    <style>
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; margin: 40px; background: #f5f5f5; }
        h1 { color: #333; }
        .summary { background: white; padding: 20px; border-radius: 8px; margin-bottom: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .summary-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; }
        .summary-item { text-align: center; padding: 10px; }
        .summary-item .value { font-size: 1.5em; font-weight: bold; color: #007bff; }
        .summary-item .label { color: #666; font-size: 0.9em; }
        table { width: 100%; border-collapse: collapse; background: white; border-radius: 8px; overflow: hidden; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        th { background: #007bff; color: white; padding: 12px; text-align: left; }
        td { padding: 10px 12px; border-bottom: 1px solid #eee; }
        tr:hover { background: #f8f9fa; }
        .footer { margin-top: 20px; text-align: center; color: #666; font-size: 0.9em; }
    </style>
</head>
<body>
    <h1>⚡ 性能基准测试报告</h1>
    
    <div class="summary">
        <div class="summary-grid">
            <div class="summary-item">
                <div class="value">${report.summary.totalBenchmarks}</div>
                <div class="label">测试总数</div>
            </div>
            <div class="summary-item">
                <div class="value">${report.summary.totalErrors}</div>
                <div class="label">错误数</div>
            </div>
            <div class="summary-item">
                <div class="value">${report.summary.fastestBenchmark ? report.summary.fastestBenchmark.ops.toFixed(2) : 'N/A'}</div>
                <div class="label">最快 (ops/s)</div>
            </div>
            <div class="summary-item">
                <div class="value">${report.options.iterations}</div>
                <div class="label">迭代次数</div>
            </div>
        </div>
    </div>
    
    <table>
        <thead>
            <tr>
                <th>状态</th>
                <th>套件</th>
                <th>测试名称</th>
                <th>平均耗时(ms)</th>
                <th>最小耗时(ms)</th>
                <th>最大耗时(ms)</th>
                <th>标准差</th>
                <th>ops/s</th>
                <th>P95(ms)</th>
            </tr>
        </thead>
        <tbody>
            ${benchmarkRows}
        </tbody>
    </table>
    
    <div class="footer">
        生成时间: ${report.timestamp}
    </div>
</body>
</html>
    `;
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
        const jsonFile = path.join(outputPath, `benchmark-${timestamp}.json`);
        fs.writeFileSync(jsonFile, JSON.stringify(report, null, 2), 'utf8');
        console.log(`\nJSON报告已保存: ${jsonFile}`);
    }
    
    if (format === 'html' || format === 'all') {
        const htmlFile = path.join(outputPath, `benchmark-${timestamp}.html`);
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
    console.log('性能基准测试结果');
    console.log('='.repeat(60));
    console.log(`测试总数: ${report.summary.totalBenchmarks}`);
    console.log(`错误数: ${report.summary.totalErrors}`);
    
    if (report.summary.fastestBenchmark) {
        console.log(`最快测试: ${report.summary.fastestBenchmark.name} (${report.summary.fastestBenchmark.ops.toFixed(2)} ops/s)`);
    }
    
    if (report.summary.slowestBenchmark) {
        console.log(`最慢测试: ${report.summary.slowestBenchmark.name} (${report.summary.slowestBenchmark.ops.toFixed(2)} ops/s)`);
    }
    
    console.log('='.repeat(60));
}

// 主函数
async function main() {
    const args = parseArgs();
    
    const runner = new PerformanceRunner();
    
    // 示例测试套件 - 数组操作
    runner.suite('数组操作', (suite) => {
        const arr = Array.from({ length: 10000 }, (_, i) => i);
        
        suite.add('Array.map', () => {
            arr.map(x => x * 2);
        });
        
        suite.add('Array.filter', () => {
            arr.filter(x => x % 2 === 0);
        });
        
        suite.add('Array.reduce', () => {
            arr.reduce((sum, x) => sum + x, 0);
        });
        
        suite.add('Array.forEach', () => {
            arr.forEach(x => x * 2);
        });
        
        suite.add('for循环', () => {
            const result = [];
            for (let i = 0; i < arr.length; i++) {
                result.push(arr[i] * 2);
            }
        });
    });
    
    // 示例测试套件 - 对象操作
    runner.suite('对象操作', (suite) => {
        const obj = { a: 1, b: 2, c: 3, d: 4, e: 5 };
        
        suite.add('Object.keys', () => {
            Object.keys(obj);
        });
        
        suite.add('Object.values', () => {
            Object.values(obj);
        });
        
        suite.add('Object.entries', () => {
            Object.entries(obj);
        });
        
        suite.add('for...in', () => {
            const keys = [];
            for (const key in obj) {
                keys.push(key);
            }
        });
    });
    
    // 示例测试套件 - 字符串操作
    runner.suite('字符串操作', (suite) => {
        const str = 'Hello, World! 这是一个测试字符串。';
        
        suite.add('String.split', () => {
            str.split('');
        });
        
        suite.add('String.replace', () => {
            str.replace(/a/g, 'b');
        });
        
        suite.add('String.includes', () => {
            str.includes('测试');
        });
        
        suite.add('正则表达式test', () => {
            /测试/.test(str);
        });
    });
    
    console.log('开始运行性能基准测试...');
    const report = await runner.runAll(args);
    
    saveReport(args.output, report, args.format);
    printSummary(report);
}

main().catch(console.error);
