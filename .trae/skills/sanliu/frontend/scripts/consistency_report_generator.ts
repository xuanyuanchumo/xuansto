import * as fs from 'fs';
import * as path from 'path';

/**
 * 一致性报告生成器
 * 
 * 功能说明：
 * - 分析组件的颜色、字体、间距、样式一致性
 * - 检测无障碍访问性问题
 * - 生成 HTML、Markdown 和 JSON 格式的报告
 * - 跟踪一致性趋势变化
 * 
 * 输出内容：
 * - consistency-reports/consistency-report.json - JSON 格式报告
 * - consistency-reports/consistency-report.html - HTML 格式报告
 * - consistency-reports/consistency-report.md - Markdown 格式报告
 * - consistency-reports/consistency-history.json - 历史趋势数据
 * 
 * 使用方法：
 * ```bash
 * npx ts-node consistency_report_generator.ts
 * ```
 * 
 * @author GUI优化子代理
 * @version 1.0.0
 */

interface ConsistencyReport {
  timestamp: string;
  project: string;
  summary: {
    totalComponents: number;
    totalIssues: number;
    consistencyScore: number;
    categories: Record<string, CategorySummary>;
  };
  details: ComponentDetail[];
  trends: TrendData[];
  recommendations: string[];
}

interface CategorySummary {
  total: number;
  passed: number;
  failed: number;
  score: number;
}

interface ComponentDetail {
  name: string;
  path: string;
  score: number;
  issues: IssueDetail[];
  metrics: ComponentMetrics;
}

interface IssueDetail {
  type: string;
  severity: 'critical' | 'major' | 'minor';
  description: string;
  location: string;
  suggestion: string;
}

interface ComponentMetrics {
  colorConsistency: number;
  fontConsistency: number;
  spacingConsistency: number;
  styleConsistency: number;
  accessibilityScore: number;
}

interface TrendData {
  date: string;
  score: number;
  issues: number;
}

class ConsistencyReportGenerator {
  private projectRoot: string;
  private outputDir: string;
  private report: ConsistencyReport;
  private historicalData: TrendData[] = [];

  constructor(projectRoot: string, outputDir: string) {
    this.projectRoot = projectRoot;
    this.outputDir = outputDir;
    this.report = this.initializeReport();
    this.ensureOutputDir();
    this.loadHistoricalData();
  }

  private ensureOutputDir(): void {
    if (!fs.existsSync(this.outputDir)) {
      fs.mkdirSync(this.outputDir, { recursive: true });
    }
  }

  private initializeReport(): ConsistencyReport {
    return {
      timestamp: new Date().toISOString(),
      project: path.basename(this.projectRoot),
      summary: {
        totalComponents: 0,
        totalIssues: 0,
        consistencyScore: 0,
        categories: {
          colors: { total: 0, passed: 0, failed: 0, score: 0 },
          fonts: { total: 0, passed: 0, failed: 0, score: 0 },
          spacing: { total: 0, passed: 0, failed: 0, score: 0 },
          borders: { total: 0, passed: 0, failed: 0, score: 0 },
          shadows: { total: 0, passed: 0, failed: 0, score: 0 },
          accessibility: { total: 0, passed: 0, failed: 0, score: 0 }
        }
      },
      details: [],
      trends: [],
      recommendations: []
    };
  }

  private loadHistoricalData(): void {
    const historyPath = path.join(this.outputDir, 'consistency-history.json');
    if (fs.existsSync(historyPath)) {
      try {
        this.historicalData = JSON.parse(fs.readFileSync(historyPath, 'utf-8'));
      } catch {
        this.historicalData = [];
      }
    }
  }

  public async generate(): Promise<ConsistencyReport> {
    console.log('开始生成一致性报告...');
    
    await this.analyzeComponents();
    await this.analyzeStyles();
    await this.analyzeAccessibility();
    this.calculateScores();
    this.generateRecommendations();
    this.updateTrends();
    
    this.saveReport();
    this.generateHTMLReport();
    this.generateMarkdownReport();
    
    return this.report;
  }

  private async analyzeComponents(): Promise<void> {
    console.log('\n分析组件一致性...');
    
    const componentsDir = path.join(this.projectRoot, 'src', 'components');
    if (!fs.existsSync(componentsDir)) return;
    
    const componentFiles = this.findVueFiles(componentsDir);
    this.report.summary.totalComponents = componentFiles.length;
    
    for (const file of componentFiles) {
      const detail = await this.analyzeComponent(file);
      this.report.details.push(detail);
    }
  }

  private async analyzeComponent(filePath: string): Promise<ComponentDetail> {
    const content = fs.readFileSync(filePath, 'utf-8');
    const relativePath = path.relative(this.projectRoot, filePath);
    const name = path.basename(filePath, '.vue');
    
    const issues: IssueDetail[] = [];
    const metrics: ComponentMetrics = {
      colorConsistency: 100,
      fontConsistency: 100,
      spacingConsistency: 100,
      styleConsistency: 100,
      accessibilityScore: 100
    };
    
    const colorIssues = this.checkColorConsistency(content);
    issues.push(...colorIssues);
    metrics.colorConsistency = Math.max(0, 100 - colorIssues.length * 5);
    
    const fontIssues = this.checkFontConsistency(content);
    issues.push(...fontIssues);
    metrics.fontConsistency = Math.max(0, 100 - fontIssues.length * 5);
    
    const spacingIssues = this.checkSpacingConsistency(content);
    issues.push(...spacingIssues);
    metrics.spacingConsistency = Math.max(0, 100 - spacingIssues.length * 3);
    
    const styleIssues = this.checkStyleConsistency(content);
    issues.push(...styleIssues);
    metrics.styleConsistency = Math.max(0, 100 - styleIssues.length * 4);
    
    const a11yIssues = this.checkAccessibility(content);
    issues.push(...a11yIssues);
    metrics.accessibilityScore = Math.max(0, 100 - a11yIssues.length * 10);
    
    const score = Math.round(
      (metrics.colorConsistency + metrics.fontConsistency + 
       metrics.spacingConsistency + metrics.styleConsistency + 
       metrics.accessibilityScore) / 5
    );
    
    return {
      name,
      path: relativePath,
      score,
      issues,
      metrics
    };
  }

  private checkColorConsistency(content: string): IssueDetail[] {
    const issues: IssueDetail[] = [];
    
    const hardCodedColors = content.match(/#[0-9A-Fa-f]{3,6}/g) || [];
    if (hardCodedColors.length > 3) {
      issues.push({
        type: 'color',
        severity: 'major',
        description: `发现 ${hardCodedColors.length} 处硬编码颜色`,
        location: 'template/style',
        suggestion: '使用 CSS 变量或设计规范中的颜色'
      });
    }
    
    if (content.includes('color:') && !content.includes('var(--')) {
      issues.push({
        type: 'color',
        severity: 'minor',
        description: '颜色值未使用 CSS 变量',
        location: 'style section',
        suggestion: '将颜色值提取为 CSS 变量'
      });
    }
    
    return issues;
  }

  private checkFontConsistency(content: string): IssueDetail[] {
    const issues: IssueDetail[] = [];
    
    const fontSizes = content.match(/font-size\s*:\s*\d+px/g) || [];
    const uniqueSizes = new Set(fontSizes);
    
    if (uniqueSizes.size > 5) {
      issues.push({
        type: 'font',
        severity: 'minor',
        description: `使用 ${uniqueSizes.size} 种不同字体大小`,
        location: 'style section',
        suggestion: '统一使用设计规范中的字体大小'
      });
    }
    
    if (content.includes('font-family') && !content.includes('sans-serif')) {
      issues.push({
        type: 'font',
        severity: 'minor',
        description: '字体族缺少后备字体',
        location: 'style section',
        suggestion: '添加系统字体作为后备'
      });
    }
    
    return issues;
  }

  private checkSpacingConsistency(content: string): IssueDetail[] {
    const issues: IssueDetail[] = [];
    
    const margins = content.match(/margin\s*:\s*\d+px/g) || [];
    const paddings = content.match(/padding\s*:\s*\d+px/g) || [];
    
    const allSpacing = [...margins, ...paddings];
    const uniqueSpacing = new Set(allSpacing);
    
    if (uniqueSpacing.size > 8) {
      issues.push({
        type: 'spacing',
        severity: 'minor',
        description: `使用 ${uniqueSpacing.size} 种不同间距值`,
        location: 'style section',
        suggestion: '使用统一的间距系统（如 4px 倍数）'
      });
    }
    
    return issues;
  }

  private checkStyleConsistency(content: string): IssueDetail[] {
    const issues: IssueDetail[] = [];
    
    if (content.includes('<style') && !content.includes('scoped')) {
      issues.push({
        type: 'style',
        severity: 'major',
        description: '组件样式未使用 scoped',
        location: 'style tag',
        suggestion: '添加 scoped 属性避免样式污染'
      });
    }
    
    const inlineStyles = (content.match(/style\s*=\s*["'][^"']+["']/g) || []).length;
    if (inlineStyles > 5) {
      issues.push({
        type: 'style',
        severity: 'minor',
        description: `发现 ${inlineStyles} 处内联样式`,
        location: 'template',
        suggestion: '将内联样式提取到 CSS 类中'
      });
    }
    
    return issues;
  }

  private checkAccessibility(content: string): IssueDetail[] {
    const issues: IssueDetail[] = [];
    
    const images = (content.match(/<img/g) || []).length;
    const alts = (content.match(/alt\s*=/g) || []).length;
    if (images > alts) {
      issues.push({
        type: 'accessibility',
        severity: 'critical',
        description: '图片缺少 alt 属性',
        location: 'template',
        suggestion: '为所有图片添加描述性 alt 属性'
      });
    }
    
    if (content.includes('v-for') && !content.includes(':key')) {
      issues.push({
        type: 'accessibility',
        severity: 'major',
        description: 'v-for 缺少 :key 属性',
        location: 'template',
        suggestion: '为 v-for 添加唯一的 :key 属性'
      });
    }
    
    const buttons = (content.match(/<button/g) || []).length;
    const ariaLabels = (content.match(/aria-label/g) || []).length;
    if (buttons > 0 && ariaLabels < buttons) {
      issues.push({
        type: 'accessibility',
        severity: 'minor',
        description: '部分按钮缺少无障碍标签',
        location: 'template',
        suggestion: '为图标按钮添加 aria-label'
      });
    }
    
    return issues;
  }

  private async analyzeStyles(): Promise<void> {
    console.log('\n分析样式文件一致性...');
    
    const styleFiles = this.findStyleFiles(path.join(this.projectRoot, 'src'));
    
    for (const file of styleFiles) {
      const content = fs.readFileSync(file, 'utf-8');
      this.analyzeStyleSheet(content, file);
    }
  }

  private analyzeStyleSheet(content: string, filePath: string): void {
    const relativePath = path.relative(this.projectRoot, filePath);
    
    const colorVars = (content.match(/--[\w-]*color[\w-]*:/gi) || []).length;
    this.report.summary.categories.colors.total += colorVars;
    
    const fontVars = (content.match(/--[\w-]*font[\w-]*:/gi) || []).length;
    this.report.summary.categories.fonts.total += fontVars;
    
    const spacingVars = (content.match(/--[\w-]*(margin|padding|gap|spacing)[\w-]*:/gi) || []).length;
    this.report.summary.categories.spacing.total += spacingVars;
  }

  private async analyzeAccessibility(): Promise<void> {
    console.log('\n分析无障碍访问性...');
    
    let totalChecks = 0;
    let passedChecks = 0;
    
    for (const detail of this.report.details) {
      totalChecks += 5;
      passedChecks += detail.metrics.accessibilityScore / 20;
    }
    
    this.report.summary.categories.accessibility = {
      total: totalChecks,
      passed: passedChecks,
      failed: totalChecks - passedChecks,
      score: totalChecks > 0 ? Math.round((passedChecks / totalChecks) * 100) : 100
    };
  }

  private calculateScores(): void {
    let totalScore = 0;
    let totalIssues = 0;
    
    for (const detail of this.report.details) {
      totalScore += detail.score;
      totalIssues += detail.issues.length;
    }
    
    this.report.summary.totalIssues = totalIssues;
    this.report.summary.consistencyScore = 
      this.report.details.length > 0 
        ? Math.round(totalScore / this.report.details.length) 
        : 100;
    
    for (const detail of this.report.details) {
      this.report.summary.categories.colors.failed += 
        detail.issues.filter(i => i.type === 'color').length;
      this.report.summary.categories.fonts.failed += 
        detail.issues.filter(i => i.type === 'font').length;
      this.report.summary.categories.spacing.failed += 
        detail.issues.filter(i => i.type === 'spacing').length;
    }
    
    for (const key of Object.keys(this.report.summary.categories)) {
      const cat = this.report.summary.categories[key];
      cat.passed = Math.max(0, cat.total - cat.failed);
      cat.score = cat.total > 0 ? Math.round((cat.passed / cat.total) * 100) : 100;
    }
  }

  private generateRecommendations(): void {
    const recommendations: string[] = [];
    
    if (this.report.summary.categories.colors.score < 80) {
      recommendations.push('建立统一的颜色变量系统，避免硬编码颜色值');
    }
    
    if (this.report.summary.categories.fonts.score < 80) {
      recommendations.push('统一字体大小和字重，使用设计规范中的标准值');
    }
    
    if (this.report.summary.categories.spacing.score < 80) {
      recommendations.push('采用一致的间距系统（如 4px 或 8px 倍数）');
    }
    
    if (this.report.summary.categories.accessibility.score < 80) {
      recommendations.push('增强无障碍访问性：添加 alt 属性、aria 标签等');
    }
    
    const criticalIssues = this.report.details
      .flatMap(d => d.issues)
      .filter(i => i.severity === 'critical').length;
    
    if (criticalIssues > 0) {
      recommendations.push(`立即修复 ${criticalIssues} 个严重问题`);
    }
    
    recommendations.push('定期运行一致性检查，保持设计规范');
    recommendations.push('建立组件库，提高复用性');
    
    this.report.recommendations = recommendations;
  }

  private updateTrends(): void {
    const today = new Date().toISOString().split('T')[0];
    
    this.historicalData.push({
      date: today,
      score: this.report.summary.consistencyScore,
      issues: this.report.summary.totalIssues
    });
    
    if (this.historicalData.length > 30) {
      this.historicalData = this.historicalData.slice(-30);
    }
    
    this.report.trends = this.historicalData;
    
    const historyPath = path.join(this.outputDir, 'consistency-history.json');
    fs.writeFileSync(historyPath, JSON.stringify(this.historicalData, null, 2), 'utf-8');
  }

  private saveReport(): void {
    const reportPath = path.join(this.outputDir, 'consistency-report.json');
    fs.writeFileSync(reportPath, JSON.stringify(this.report, null, 2), 'utf-8');
    console.log(`\n一致性报告已生成: ${reportPath}`);
  }

  private generateHTMLReport(): void {
    const htmlPath = path.join(this.outputDir, 'consistency-report.html');
    
    const html = `<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>UI/UX 一致性报告</title>
  <style>
    * { margin: 0; padding: 0; box-sizing: border-box; }
    body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #f5f5f5; color: #333; line-height: 1.6; }
    .container { max-width: 1200px; margin: 0 auto; padding: 20px; }
    .header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 40px 20px; text-align: center; border-radius: 10px; margin-bottom: 30px; }
    .header h1 { font-size: 2.5em; margin-bottom: 10px; }
    .header .subtitle { opacity: 0.9; font-size: 1.1em; }
    .score-card { background: white; border-radius: 10px; padding: 30px; margin-bottom: 20px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
    .score-circle { width: 150px; height: 150px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 3em; font-weight: bold; margin: 0 auto 20px; }
    .score-excellent { background: #e8f5e9; color: #2e7d32; }
    .score-good { background: #fff3e0; color: #f57c00; }
    .score-poor { background: #ffebee; color: #c62828; }
    .stats-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin-top: 20px; }
    .stat-item { background: #f8f9fa; padding: 20px; border-radius: 8px; text-align: center; }
    .stat-value { font-size: 2em; font-weight: bold; color: #667eea; }
    .stat-label { color: #666; margin-top: 5px; }
    .category-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 15px; }
    .category-card { background: white; border-radius: 8px; padding: 20px; text-align: center; box-shadow: 0 2px 5px rgba(0,0,0,0.05); }
    .category-score { font-size: 2em; font-weight: bold; margin-bottom: 10px; }
    .category-name { color: #666; font-size: 0.9em; }
    .issues-list { background: white; border-radius: 10px; padding: 20px; margin-top: 20px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
    .issue-item { padding: 15px; border-left: 4px solid #ddd; margin-bottom: 10px; background: #f8f9fa; }
    .issue-critical { border-left-color: #c62828; }
    .issue-major { border-left-color: #f57c00; }
    .issue-minor { border-left-color: #1976d2; }
    .issue-title { font-weight: bold; margin-bottom: 5px; }
    .issue-location { color: #666; font-size: 0.9em; }
    .recommendations { background: white; border-radius: 10px; padding: 20px; margin-top: 20px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
    .recommendation-item { padding: 10px 0; border-bottom: 1px solid #eee; }
    .recommendation-item:last-child { border-bottom: none; }
    .trend-chart { background: white; border-radius: 10px; padding: 20px; margin-top: 20px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
    .chart-bars { display: flex; align-items: flex-end; height: 200px; gap: 5px; padding: 20px 0; }
    .chart-bar { flex: 1; background: linear-gradient(to top, #667eea, #764ba2); border-radius: 4px 4px 0 0; min-height: 10px; transition: height 0.3s; }
    .chart-bar:hover { opacity: 0.8; }
    .footer { text-align: center; padding: 20px; color: #666; margin-top: 40px; }
  </style>
</head>
<body>
  <div class="container">
    <div class="header">
      <h1>UI/UX 一致性报告</h1>
      <div class="subtitle">生成时间: ${new Date(this.report.timestamp).toLocaleString('zh-CN')}</div>
    </div>
    
    <div class="score-card">
      <div class="score-circle ${this.getScoreClass(this.report.summary.consistencyScore)}">
        ${this.report.summary.consistencyScore}
      </div>
      <h2 style="text-align: center;">总体一致性得分</h2>
      <div class="stats-grid">
        <div class="stat-item">
          <div class="stat-value">${this.report.summary.totalComponents}</div>
          <div class="stat-label">检查组件</div>
        </div>
        <div class="stat-item">
          <div class="stat-value">${this.report.summary.totalIssues}</div>
          <div class="stat-label">发现问题</div>
        </div>
        <div class="stat-item">
          <div class="stat-value">${this.report.details.filter(d => d.issues.length === 0).length}</div>
          <div class="stat-label">完美组件</div>
        </div>
      </div>
    </div>
    
    <div class="score-card">
      <h3>分类得分</h3>
      <div class="category-grid" style="margin-top: 20px;">
        ${Object.entries(this.report.summary.categories).map(([key, cat]) => `
          <div class="category-card">
            <div class="category-score ${this.getScoreClass(cat.score)}">${cat.score}%</div>
            <div class="category-name">${this.getCategoryName(key)}</div>
          </div>
        `).join('')}
      </div>
    </div>
    
    ${this.report.trends.length > 1 ? `
    <div class="trend-chart">
      <h3>趋势分析</h3>
      <div class="chart-bars">
        ${this.report.trends.map(t => {
          const height = Math.max(10, t.score * 2);
          return `<div class="chart-bar" style="height: ${height}px;" title="${t.date}: ${t.score}分"></div>`;
        }).join('')}
      </div>
    </div>
    ` : ''}
    
    <div class="issues-list">
      <h3>主要问题</h3>
      ${this.getTopIssues().map(issue => `
        <div class="issue-item issue-${issue.severity}">
          <div class="issue-title">${issue.description}</div>
          <div class="issue-location">位置: ${issue.location}</div>
          <div style="color: #666; margin-top: 5px;">建议: ${issue.suggestion}</div>
        </div>
      `).join('')}
    </div>
    
    <div class="recommendations">
      <h3>优化建议</h3>
      ${this.report.recommendations.map((rec, idx) => `
        <div class="recommendation-item">
          <strong>${idx + 1}.</strong> ${rec}
        </div>
      `).join('')}
    </div>
    
    <div class="footer">
      <p>此报告由 UI/UX 一致性检查工具自动生成</p>
    </div>
  </div>
</body>
</html>`;

    fs.writeFileSync(htmlPath, html, 'utf-8');
    console.log(`HTML 报告已生成: ${htmlPath}`);
  }

  private getScoreClass(score: number): string {
    if (score >= 80) return 'score-excellent';
    if (score >= 60) return 'score-good';
    return 'score-poor';
  }

  private getCategoryName(key: string): string {
    const names: Record<string, string> = {
      colors: '颜色',
      fonts: '字体',
      spacing: '间距',
      borders: '边框',
      shadows: '阴影',
      accessibility: '无障碍'
    };
    return names[key] || key;
  }

  private getTopIssues(): IssueDetail[] {
    return this.report.details
      .flatMap(d => d.issues)
      .sort((a, b) => {
        const severityOrder = { critical: 0, major: 1, minor: 2 };
        return severityOrder[a.severity] - severityOrder[b.severity];
      })
      .slice(0, 10);
  }

  private generateMarkdownReport(): void {
    const mdPath = path.join(this.outputDir, 'consistency-report.md');
    
    const content = `# UI/UX 一致性报告

## 概览

- **生成时间**: ${new Date(this.report.timestamp).toLocaleString('zh-CN')}
- **总体得分**: ${this.report.summary.consistencyScore}/100
- **检查组件**: ${this.report.summary.totalComponents} 个
- **发现问题**: ${this.report.summary.totalIssues} 个

## 分类得分

| 类别 | 得分 | 通过 | 失败 |
|------|------|------|------|
${Object.entries(this.report.summary.categories).map(([key, cat]) => 
  `| ${this.getCategoryName(key)} | ${cat.score}% | ${cat.passed} | ${cat.failed} |`
).join('\n')}

## 组件详情

${this.report.details
  .filter(d => d.issues.length > 0)
  .slice(0, 10)
  .map(d => `### ${d.name}

- **得分**: ${d.score}/100
- **问题数**: ${d.issues.length}

${d.issues.slice(0, 3).map(i => `- [${i.severity}] ${i.description}`).join('\n')}
`).join('\n')}

## 优化建议

${this.report.recommendations.map((r, i) => `${i + 1}. ${r}`).join('\n')}

---

*此报告由 UI/UX 一致性检查工具自动生成*
`;

    fs.writeFileSync(mdPath, content, 'utf-8');
    console.log(`Markdown 报告已生成: ${mdPath}`);
  }

  private findVueFiles(dir: string): string[] {
    const files: string[] = [];
    if (!fs.existsSync(dir)) return files;
    
    const items = fs.readdirSync(dir);
    for (const item of items) {
      const fullPath = path.join(dir, item);
      const stat = fs.statSync(fullPath);
      
      if (stat.isDirectory()) {
        files.push(...this.findVueFiles(fullPath));
      } else if (item.endsWith('.vue')) {
        files.push(fullPath);
      }
    }
    
    return files;
  }

  private findStyleFiles(dir: string): string[] {
    const files: string[] = [];
    if (!fs.existsSync(dir)) return files;
    
    const items = fs.readdirSync(dir);
    for (const item of items) {
      const fullPath = path.join(dir, item);
      const stat = fs.statSync(fullPath);
      
      if (stat.isDirectory()) {
        files.push(...this.findStyleFiles(fullPath));
      } else if (item.endsWith('.css') || item.endsWith('.scss') || item.endsWith('.less')) {
        files.push(fullPath);
      }
    }
    
    return files;
  }
}

async function main() {
  const projectRoot = path.resolve(__dirname, '..');
  const outputDir = path.join(projectRoot, 'consistency-reports');
  
  const generator = new ConsistencyReportGenerator(projectRoot, outputDir);
  await generator.generate();
  
  console.log('\n一致性报告生成完成！');
}

main().catch(console.error);

export { ConsistencyReportGenerator, ConsistencyReport };
