import type { Reporter, TestCase, TestResult, Suite } from '@playwright/test/reporter';
import * as fs from 'fs';
import * as path from 'path';

interface TestCoverage {
  total: number;
  passed: number;
  failed: number;
  skipped: number;
  duration: number;
  files: {
    [key: string]: {
      total: number;
      passed: number;
      failed: number;
      skipped: number;
      tests: {
        name: string;
        status: string;
        duration: number;
      }[];
    };
  };
  browsers: {
    [key: string]: {
      total: number;
      passed: number;
      failed: number;
    };
  };
}

class E2ECoverageReporter implements Reporter {
  private coverage: TestCoverage = {
    total: 0,
    passed: 0,
    failed: 0,
    skipped: 0,
    duration: 0,
    files: {},
    browsers: {}
  };

  onTestEnd(test: TestCase, result: TestResult) {
    const fileName = test.location.file.split('/').pop() || 'unknown';
    const browserName = test.parent.project()?.name || 'unknown';
    const testName = test.titlePath().join(' > ');
    
    this.coverage.total++;
    this.coverage.duration += result.duration;
    
    if (result.status === 'passed') {
      this.coverage.passed++;
    } else if (result.status === 'failed') {
      this.coverage.failed++;
    } else {
      this.coverage.skipped++;
    }
    
    if (!this.coverage.files[fileName]) {
      this.coverage.files[fileName] = {
        total: 0,
        passed: 0,
        failed: 0,
        skipped: 0,
        tests: []
      };
    }
    
    this.coverage.files[fileName].total++;
    this.coverage.files[fileName].tests.push({
      name: testName,
      status: result.status,
      duration: result.duration
    });
    
    if (result.status === 'passed') {
      this.coverage.files[fileName].passed++;
    } else if (result.status === 'failed') {
      this.coverage.files[fileName].failed++;
    } else {
      this.coverage.files[fileName].skipped++;
    }
    
    if (!this.coverage.browsers[browserName]) {
      this.coverage.browsers[browserName] = {
        total: 0,
        passed: 0,
        failed: 0
      };
    }
    
    this.coverage.browsers[browserName].total++;
    if (result.status === 'passed') {
      this.coverage.browsers[browserName].passed++;
    } else if (result.status === 'failed') {
      this.coverage.browsers[browserName].failed++;
    }
  }

  onEnd() {
    const reportDir = path.join(process.cwd(), 'e2e-report');
    if (!fs.existsSync(reportDir)) {
      fs.mkdirSync(reportDir, { recursive: true });
    }
    
    fs.writeFileSync(
      path.join(reportDir, 'coverage-summary.json'),
      JSON.stringify(this.coverage, null, 2)
    );
    
    console.log('\n========================================');
    console.log('E2E测试覆盖率概要');
    console.log('========================================\n');
    
    console.log(`总测试数: ${this.coverage.total}`);
    console.log(`通过: ${this.coverage.passed}`);
    console.log(`失败: ${this.coverage.failed}`);
    console.log(`跳过: ${this.coverage.skipped}`);
    console.log(`总耗时: ${(this.coverage.duration / 1000).toFixed(2)}秒`);
    
    console.log('\n按文件统计:');
    console.log('----------------------------------------');
    for (const [file, stats] of Object.entries(this.coverage.files)) {
      const passRate = ((stats.passed / stats.total) * 100).toFixed(1);
      console.log(`${file}: ${stats.passed}/${stats.total} (${passRate}%)`);
    }
    
    console.log('\n按浏览器统计:');
    console.log('----------------------------------------');
    for (const [browser, stats] of Object.entries(this.coverage.browsers)) {
      const passRate = ((stats.passed / stats.total) * 100).toFixed(1);
      console.log(`${browser}: ${stats.passed}/${stats.total} (${passRate}%)`);
    }
    
    console.log('\n========================================\n');
  }
}

export default E2ECoverageReporter;
