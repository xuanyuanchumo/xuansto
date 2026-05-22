import * as fs from 'fs';
import * as path from 'path';
import { execSync } from 'child_process';

/**
 * GUI界面优化主入口脚本
 * 
 * 功能说明：
 * - 统一执行所有GUI优化相关任务
 * - Task 39: 前端组件优化
 * - Task 40: UI/UX一致性检查
 * - Task 41: 响应式设计验证
 * 
 * 使用方法：
 * ```bash
 * npx ts-node gui_optimizer.ts [task]
 * ```
 * 
 * 参数说明：
 * - 不带参数：执行所有任务
 * - task39：仅执行前端组件优化
 * - task40：仅执行UI/UX一致性检查
 * - task41：仅执行响应式设计验证
 * 
 * @author GUI优化子代理
 * @version 1.0.0
 */

interface TaskResult {
  task: string;
  success: boolean;
  duration: number;
  outputDir: string;
  error?: string;
}

interface OptimizationReport {
  timestamp: string;
  projectRoot: string;
  results: TaskResult[];
  summary: {
    totalTasks: number;
    successfulTasks: number;
    failedTasks: number;
    totalDuration: number;
  };
}

class GUIOptimizer {
  private projectRoot: string;
  private outputDir: string;
  private results: TaskResult[] = [];

  constructor() {
    this.projectRoot = path.resolve(__dirname, '..');
    this.outputDir = path.join(this.projectRoot, 'gui-optimization-reports');
    this.ensureOutputDir();
  }

  private ensureOutputDir(): void {
    if (!fs.existsSync(this.outputDir)) {
      fs.mkdirSync(this.outputDir, { recursive: true });
    }
  }

  public async run(task?: string): Promise<OptimizationReport> {
    console.log('='.repeat(60));
    console.log('GUI界面优化工具');
    console.log('='.repeat(60));
    console.log(`项目根目录: ${this.projectRoot}`);
    console.log(`输出目录: ${this.outputDir}`);
    console.log(`执行时间: ${new Date().toLocaleString('zh-CN')}`);
    console.log('='.repeat(60));

    const tasks = this.getTasksToRun(task);

    for (const taskName of tasks) {
      await this.runTask(taskName);
    }

    return this.generateFinalReport();
  }

  private getTasksToRun(task?: string): string[] {
    if (!task) {
      return ['task39', 'task40', 'task41'];
    }

    const taskMap: Record<string, string[]> = {
      'task39': ['task39'],
      'task40': ['task40'],
      'task41': ['task41'],
      'all': ['task39', 'task40', 'task41'],
      '组件': ['task39'],
      '一致性': ['task40'],
      '响应式': ['task41']
    };

    return taskMap[task.toLowerCase()] || ['task39', 'task40', 'task41'];
  }

  private async runTask(taskName: string): Promise<void> {
    console.log(`\n${'='.repeat(60)}`);
    console.log(`开始执行: ${this.getTaskDisplayName(taskName)}`);
    console.log('='.repeat(60));

    const startTime = Date.now();
    let success = true;
    let error: string | undefined;
    let outputDir = '';

    try {
      switch (taskName) {
        case 'task39':
          outputDir = await this.runTask39();
          break;
        case 'task40':
          outputDir = await this.runTask40();
          break;
        case 'task41':
          outputDir = await this.runTask41();
          break;
        default:
          throw new Error(`未知任务: ${taskName}`);
      }
    } catch (err) {
      success = false;
      error = err instanceof Error ? err.message : String(err);
      console.error(`任务执行失败: ${error}`);
    }

    const duration = Date.now() - startTime;

    this.results.push({
      task: taskName,
      success,
      duration,
      outputDir,
      error
    });

    console.log(`\n任务完成: ${this.getTaskDisplayName(taskName)}`);
    console.log(`状态: ${success ? '✓ 成功' : '✗ 失败'}`);
    console.log(`耗时: ${(duration / 1000).toFixed(2)}秒`);
    if (outputDir) {
      console.log(`输出目录: ${outputDir}`);
    }
  }

  private getTaskDisplayName(taskName: string): string {
    const names: Record<string, string> = {
      'task39': 'Task 39: 前端组件优化',
      'task40': 'Task 40: UI/UX一致性检查',
      'task41': 'Task 41: 响应式设计验证'
    };
    return names[taskName] || taskName;
  }

  private async runTask39(): Promise<string> {
    console.log('\n--- SubTask 39.1: 审查前端组件性能 ---');
    await this.runScript('component_rendering_optimizer.ts');

    console.log('\n--- SubTask 39.2: 优化组件渲染效率 ---');
    await this.runScript('vue_component_analyzer.ts');

    console.log('\n--- SubTask 39.3: 增强组件测试 ---');
    await this.runScript('component_test_enhancer.ts');

    return path.join(this.projectRoot, 'test-enhancement-reports');
  }

  private async runTask40(): Promise<string> {
    console.log('\n--- SubTask 40.1: 实现设计规范验证 ---');
    await this.runScript('design_spec_validator.ts');

    console.log('\n--- SubTask 40.2: 实现一致性报告生成 ---');
    await this.runScript('consistency_report_generator.ts');

    console.log('\n--- SubTask 40.3: 实现一致性修复建议 ---');
    await this.runScript('consistency_fix_suggester.ts');

    return path.join(this.projectRoot, 'consistency-reports');
  }

  private async runTask41(): Promise<string> {
    console.log('\n--- SubTask 41.1: 实现多设备适配测试 ---');
    console.log('注意: 多设备测试需要运行中的服务器，跳过实际测试');
    console.log('可手动运行: npx ts-node multi_device_tester.ts');

    console.log('\n--- SubTask 41.2: 实现适配报告生成 ---');
    await this.runScript('adaptation_report_generator.ts');

    console.log('\n--- SubTask 41.3: 实现适配问题修复 ---');
    await this.runScript('adaptation_fixer.ts');

    return path.join(this.projectRoot, 'adaptation-reports');
  }

  private async runScript(scriptName: string): Promise<void> {
    const scriptPath = path.join(__dirname, scriptName);
    
    if (!fs.existsSync(scriptPath)) {
      console.log(`脚本不存在: ${scriptName}，跳过`);
      return;
    }

    console.log(`执行脚本: ${scriptName}`);
    
    try {
      execSync(`npx ts-node "${scriptPath}"`, {
        cwd: this.projectRoot,
        stdio: 'inherit',
        timeout: 300000
      });
    } catch (error) {
      console.warn(`脚本执行出错: ${scriptName}`);
      console.warn(error);
    }
  }

  private generateFinalReport(): OptimizationReport {
    const report: OptimizationReport = {
      timestamp: new Date().toISOString(),
      projectRoot: this.projectRoot,
      results: this.results,
      summary: {
        totalTasks: this.results.length,
        successfulTasks: this.results.filter(r => r.success).length,
        failedTasks: this.results.filter(r => !r.success).length,
        totalDuration: this.results.reduce((sum, r) => sum + r.duration, 0)
      }
    };

    this.saveJSONReport(report);
    this.generateSummaryReport(report);
    this.printConsoleSummary(report);

    return report;
  }

  private saveJSONReport(report: OptimizationReport): void {
    const reportPath = path.join(this.outputDir, 'gui-optimization-report.json');
    fs.writeFileSync(reportPath, JSON.stringify(report, null, 2), 'utf-8');
    console.log(`\nJSON 报告已生成: ${reportPath}`);
  }

  private generateSummaryReport(report: OptimizationReport): void {
    const summaryPath = path.join(this.outputDir, 'gui-optimization-summary.txt');
    
    const lines = [
      '='.repeat(60),
      'GUI界面优化报告',
      '='.repeat(60),
      `生成时间: ${new Date(report.timestamp).toLocaleString('zh-CN')}`,
      `项目路径: ${report.projectRoot}`,
      '',
      '-'.repeat(60),
      '执行摘要',
      '-'.repeat(60),
      `总任务数: ${report.summary.totalTasks}`,
      `成功: ${report.summary.successfulTasks}`,
      `失败: ${report.summary.failedTasks}`,
      `总耗时: ${(report.summary.totalDuration / 1000).toFixed(2)}秒`,
      '',
      '-'.repeat(60),
      '任务详情',
      '-'.repeat(60),
    ];

    for (const result of report.results) {
      lines.push('');
      lines.push(`[${result.success ? '✓' : '✗'}] ${this.getTaskDisplayName(result.task)}`);
      lines.push(`    耗时: ${(result.duration / 1000).toFixed(2)}秒`);
      if (result.outputDir) {
        lines.push(`    输出: ${result.outputDir}`);
      }
      if (result.error) {
        lines.push(`    错误: ${result.error}`);
      }
    }

    lines.push('', '='.repeat(60), '优化完成', '='.repeat(60));

    fs.writeFileSync(summaryPath, lines.join('\n'), 'utf-8');
    console.log(`摘要报告已生成: ${summaryPath}`);
  }

  private printConsoleSummary(report: OptimizationReport): void {
    console.log('\n' + '='.repeat(60));
    console.log('执行摘要');
    console.log('='.repeat(60));
    console.log(`总任务数: ${report.summary.totalTasks}`);
    console.log(`成功: ${report.summary.successfulTasks}`);
    console.log(`失败: ${report.summary.failedTasks}`);
    console.log(`总耗时: ${(report.summary.totalDuration / 1000).toFixed(2)}秒`);
    console.log('='.repeat(60));

    if (report.summary.failedTasks > 0) {
      console.log('\n失败的任务:');
      for (const result of report.results.filter(r => !r.success)) {
        console.log(`  - ${this.getTaskDisplayName(result.task)}: ${result.error}`);
      }
    }

    console.log('\n生成的报告目录:');
    for (const result of report.results.filter(r => r.outputDir)) {
      console.log(`  - ${this.getTaskDisplayName(result.task)}: ${result.outputDir}`);
    }
  }
}

async function main() {
  const task = process.argv[2];
  const optimizer = new GUIOptimizer();
  await optimizer.run(task);
  console.log('\nGUI界面优化完成！');
}

main().catch(console.error);

export { GUIOptimizer, OptimizationReport, TaskResult };
