import * as fs from 'fs';
import * as path from 'path';

/**
 * 设计规范验证器
 * 
 * 功能说明：
 * - 验证项目中的颜色、字体、间距、边框、阴影是否符合设计规范
 * - 检测硬编码的颜色值、非标准字体大小、非标准间距等
 * - 生成设计规范文档和验证报告
 * - 提供一致性评分和改进建议
 * 
 * 输出内容：
 * - design-spec-reports/design-spec-validation-report.json - 详细验证报告
 * - design-spec-reports/design-spec-validation-summary.txt - 摘要报告
 * - design-spec-reports/design-spec.md - 设计规范文档
 * 
 * 使用方法：
 * ```bash
 * npx ts-node design_spec_validator.ts
 * ```
 * 
 * @author GUI优化子代理
 * @version 1.0.0
 */

interface DesignSpec {
  colors: {
    primary: string[];
    secondary: string[];
    success: string[];
    warning: string[];
    danger: string[];
    info: string[];
    text: string[];
    background: string[];
  };
  fonts: {
    families: string[];
    sizes: { name: string; value: string }[];
    weights: number[];
  };
  spacing: {
    values: string[];
    scale: string;
  };
  borderRadius: string[];
  shadows: string[];
}

interface ConsistencyIssue {
  type: 'color' | 'font' | 'spacing' | 'border' | 'shadow' | 'component';
  severity: 'error' | 'warning' | 'info';
  file: string;
  line?: number;
  actual: string;
  expected: string;
  message: string;
}

interface ValidationResult {
  file: string;
  issues: ConsistencyIssue[];
  score: number;
}

class DesignSpecValidator {
  private projectRoot: string;
  private outputDir: string;
  private spec: DesignSpec;
  private validationResults: ValidationResult[] = [];

  constructor(projectRoot: string, outputDir: string) {
    this.projectRoot = projectRoot;
    this.outputDir = outputDir;
    this.spec = this.getDefaultSpec();
    this.ensureOutputDir();
  }

  private ensureOutputDir(): void {
    if (!fs.existsSync(this.outputDir)) {
      fs.mkdirSync(this.outputDir, { recursive: true });
    }
  }

  private getDefaultSpec(): DesignSpec {
    return {
      colors: {
        primary: ['#409EFF', '#66b1ff', '#79bbff', '#8cc5ff', '#a0cfff', '#c6e2ff'],
        secondary: ['#909399', '#a6a9ad', '#b4b7bb', '#c8cbcf', '#d3d5d8', '#e9e9eb'],
        success: ['#67C23A', '#85ce61', '#95d475', '#a4da89', '#b3e19d', '#c2e7b0'],
        warning: ['#E6A23C', '#ebb563', '#f0c78a', '#f5dab1', '#faecd8', '#fdf6ec'],
        danger: ['#F56C6C', '#f78989', '#faa8a8', '#fbc4c4', '#fde2e2', '#fef0f0'],
        info: ['#909399', '#a6a9ad', '#b4b7bb', '#c8cbcf', '#d3d5d8', '#e9e9eb'],
        text: ['#303133', '#606266', '#909399', '#C0C4CC'],
        background: ['#FFFFFF', '#F5F7FA', '#FAFAFA', '#F2F6FC']
      },
      fonts: {
        families: [
          'Helvetica Neue',
          'Helvetica',
          'PingFang SC',
          'Hiragino Sans GB',
          'Microsoft YaHei',
          'Arial',
          'sans-serif'
        ],
        sizes: [
          { name: 'xs', value: '12px' },
          { name: 'sm', value: '13px' },
          { name: 'base', value: '14px' },
          { name: 'md', value: '16px' },
          { name: 'lg', value: '18px' },
          { name: 'xl', value: '20px' },
          { name: '2xl', value: '22px' },
          { name: '3xl', value: '24px' }
        ],
        weights: [100, 200, 300, 400, 500, 600, 700, 800, 900]
      },
      spacing: {
        values: ['0', '4px', '8px', '12px', '16px', '20px', '24px', '32px', '40px', '48px'],
        scale: '4px'
      },
      borderRadius: ['0', '2px', '4px', '8px', '12px', '16px', '50%'],
      shadows: [
        'none',
        '0 2px 4px rgba(0, 0, 0, 0.12), 0 0 6px rgba(0, 0, 0, 0.04)',
        '0 2px 8px rgba(0, 0, 0, 0.12), 0 0 6px rgba(0, 0, 0, 0.04)',
        '0 4px 12px rgba(0, 0, 0, 0.15), 0 0 6px rgba(0, 0, 0, 0.05)',
        '0 6px 16px rgba(0, 0, 0, 0.15), 0 0 6px rgba(0, 0, 0, 0.05)'
      ]
    };
  }

  public async validate(): Promise<ValidationResult[]> {
    console.log('开始设计规范验证...');
    
    await this.validateColors();
    await this.validateFonts();
    await this.validateSpacing();
    await this.validateBorders();
    await this.validateShadows();
    await this.validateComponents();
    
    this.generateValidationReport();
    return this.validationResults;
  }

  private async validateColors(): Promise<void> {
    console.log('\n验证颜色规范...');
    
    const vueFiles = this.findVueFiles(path.join(this.projectRoot, 'src'));
    const cssFiles = this.findCSSFiles(path.join(this.projectRoot, 'src'));
    
    for (const file of [...vueFiles, ...cssFiles]) {
      const content = fs.readFileSync(file, 'utf-8');
      const issues = this.checkColorConsistency(content, file);
      
      if (issues.length > 0) {
        this.addValidationResult(file, issues);
      }
    }
  }

  private checkColorConsistency(content: string, file: string): ConsistencyIssue[] {
    const issues: ConsistencyIssue[] = [];
    const lines = content.split('\n');
    
    const colorPatterns = [
      /#[0-9A-Fa-f]{3,6}/g,
      /rgb\(\s*\d+\s*,\s*\d+\s*,\s*\d+\s*\)/g,
      /rgba\(\s*\d+\s*,\s*\d+\s*,\s*\d+\s*,\s*[\d.]+\s*\)/g,
      /hsl\(\s*\d+\s*,\s*\d+%\s*,\s*\d+%\s*\)/g
    ];
    
    lines.forEach((line, lineIndex) => {
      colorPatterns.forEach(pattern => {
        const matches = line.matchAll(pattern);
        
        for (const match of matches) {
          const color = match[0].toLowerCase();
          
          if (!this.isColorInSpec(color)) {
            issues.push({
              type: 'color',
              severity: 'warning',
              file,
              line: lineIndex + 1,
              actual: color,
              expected: '使用设计规范中的颜色变量',
              message: `发现非标准颜色值: ${color}`
            });
          }
        }
      });
    });
    
    return issues;
  }

  private isColorInSpec(color: string): boolean {
    const normalizedColor = color.toLowerCase();
    
    for (const category of Object.values(this.spec.colors)) {
      if (category.some(c => c.toLowerCase() === normalizedColor)) {
        return true;
      }
    }
    
    return false;
  }

  private async validateFonts(): Promise<void> {
    console.log('\n验证字体规范...');
    
    const vueFiles = this.findVueFiles(path.join(this.projectRoot, 'src'));
    const cssFiles = this.findCSSFiles(path.join(this.projectRoot, 'src'));
    
    for (const file of [...vueFiles, ...cssFiles]) {
      const content = fs.readFileSync(file, 'utf-8');
      const issues = this.checkFontConsistency(content, file);
      
      if (issues.length > 0) {
        this.addValidationResult(file, issues);
      }
    }
  }

  private checkFontConsistency(content: string, file: string): ConsistencyIssue[] {
    const issues: ConsistencyIssue[] = [];
    const lines = content.split('\n');
    
    const fontSizePattern = /font-size\s*:\s*(\d+px|\d+rem|\d+em)/g;
    const fontFamilyPattern = /font-family\s*:\s*([^;]+)/g;
    const fontWeightPattern = /font-weight\s*:\s*(\d+)/g;
    
    lines.forEach((line, lineIndex) => {
      const fontSizeMatches = line.matchAll(fontSizePattern);
      for (const match of fontSizeMatches) {
        const size = match[1];
        if (!this.isFontSizeInSpec(size)) {
          issues.push({
            type: 'font',
            severity: 'info',
            file,
            line: lineIndex + 1,
            actual: size,
            expected: '使用设计规范中的字体大小',
            message: `非标准字体大小: ${size}`
          });
        }
      }
      
      const fontFamilyMatches = line.matchAll(fontFamilyPattern);
      for (const match of fontFamilyMatches) {
        const family = match[1].trim();
        if (!this.isFontFamilyInSpec(family)) {
          issues.push({
            type: 'font',
            severity: 'warning',
            file,
            line: lineIndex + 1,
            actual: family,
            expected: `使用设计规范中的字体: ${this.spec.fonts.families[0]}`,
            message: `非标准字体族: ${family}`
          });
        }
      }
      
      const fontWeightMatches = line.matchAll(fontWeightPattern);
      for (const match of fontWeightMatches) {
        const weight = parseInt(match[1]);
        if (!this.spec.fonts.weights.includes(weight)) {
          issues.push({
            type: 'font',
            severity: 'info',
            file,
            line: lineIndex + 1,
            actual: match[1],
            expected: `使用标准字重: ${this.spec.fonts.weights.join(', ')}`,
            message: `非标准字重: ${weight}`
          });
        }
      }
    });
    
    return issues;
  }

  private isFontSizeInSpec(size: string): boolean {
    return this.spec.fonts.sizes.some(s => s.value === size);
  }

  private isFontFamilyInSpec(family: string): boolean {
    const normalizedFamily = family.toLowerCase().replace(/['"]/g, '');
    return this.spec.fonts.families.some(f => 
      normalizedFamily.includes(f.toLowerCase())
    );
  }

  private async validateSpacing(): Promise<void> {
    console.log('\n验证间距规范...');
    
    const vueFiles = this.findVueFiles(path.join(this.projectRoot, 'src'));
    const cssFiles = this.findCSSFiles(path.join(this.projectRoot, 'src'));
    
    for (const file of [...vueFiles, ...cssFiles]) {
      const content = fs.readFileSync(file, 'utf-8');
      const issues = this.checkSpacingConsistency(content, file);
      
      if (issues.length > 0) {
        this.addValidationResult(file, issues);
      }
    }
  }

  private checkSpacingConsistency(content: string, file: string): ConsistencyIssue[] {
    const issues: ConsistencyIssue[] = [];
    const lines = content.split('\n');
    
    const spacingPattern = /(margin|padding|gap)\s*:\s*(\d+px)/g;
    
    lines.forEach((line, lineIndex) => {
      const matches = line.matchAll(spacingPattern);
      
      for (const match of matches) {
        const property = match[1];
        const value = match[2];
        
        if (!this.isSpacingInSpec(value)) {
          issues.push({
            type: 'spacing',
            severity: 'info',
            file,
            line: lineIndex + 1,
            actual: value,
            expected: `使用标准间距: ${this.spec.spacing.values.join(', ')}`,
            message: `${property} 使用非标准间距: ${value}`
          });
        }
      }
    });
    
    return issues;
  }

  private isSpacingInSpec(value: string): boolean {
    return this.spec.spacing.values.includes(value);
  }

  private async validateBorders(): Promise<void> {
    console.log('\n验证边框规范...');
    
    const vueFiles = this.findVueFiles(path.join(this.projectRoot, 'src'));
    const cssFiles = this.findCSSFiles(path.join(this.projectRoot, 'src'));
    
    for (const file of [...vueFiles, ...cssFiles]) {
      const content = fs.readFileSync(file, 'utf-8');
      const issues = this.checkBorderConsistency(content, file);
      
      if (issues.length > 0) {
        this.addValidationResult(file, issues);
      }
    }
  }

  private checkBorderConsistency(content: string, file: string): ConsistencyIssue[] {
    const issues: ConsistencyIssue[] = [];
    const lines = content.split('\n');
    
    const borderRadiusPattern = /border-radius\s*:\s*(\d+px|\d+%)/g;
    
    lines.forEach((line, lineIndex) => {
      const matches = line.matchAll(borderRadiusPattern);
      
      for (const match of matches) {
        const radius = match[1];
        
        if (!this.isBorderRadiusInSpec(radius)) {
          issues.push({
            type: 'border',
            severity: 'info',
            file,
            line: lineIndex + 1,
            actual: radius,
            expected: `使用标准圆角: ${this.spec.borderRadius.join(', ')}`,
            message: `非标准圆角值: ${radius}`
          });
        }
      }
    });
    
    return issues;
  }

  private isBorderRadiusInSpec(radius: string): boolean {
    return this.spec.borderRadius.includes(radius);
  }

  private async validateShadows(): Promise<void> {
    console.log('\n验证阴影规范...');
    
    const vueFiles = this.findVueFiles(path.join(this.projectRoot, 'src'));
    const cssFiles = this.findCSSFiles(path.join(this.projectRoot, 'src'));
    
    for (const file of [...vueFiles, ...cssFiles]) {
      const content = fs.readFileSync(file, 'utf-8');
      const issues = this.checkShadowConsistency(content, file);
      
      if (issues.length > 0) {
        this.addValidationResult(file, issues);
      }
    }
  }

  private checkShadowConsistency(content: string, file: string): ConsistencyIssue[] {
    const issues: ConsistencyIssue[] = [];
    const lines = content.split('\n');
    
    const shadowPattern = /box-shadow\s*:\s*([^;]+)/g;
    
    lines.forEach((line, lineIndex) => {
      const matches = line.matchAll(shadowPattern);
      
      for (const match of matches) {
        const shadow = match[1].trim();
        
        if (!this.isShadowInSpec(shadow)) {
          issues.push({
            type: 'shadow',
            severity: 'info',
            file,
            line: lineIndex + 1,
            actual: shadow,
            expected: '使用设计规范中的阴影',
            message: `非标准阴影值`
          });
        }
      }
    });
    
    return issues;
  }

  private isShadowInSpec(shadow: string): boolean {
    const normalizedShadow = shadow.replace(/\s+/g, ' ').trim();
    return this.spec.shadows.some(s => 
      s.replace(/\s+/g, ' ').trim() === normalizedShadow
    );
  }

  private async validateComponents(): Promise<void> {
    console.log('\n验证组件样式一致性...');
    
    const componentsDir = path.join(this.projectRoot, 'src', 'components');
    if (!fs.existsSync(componentsDir)) return;
    
    const componentFiles = this.findVueFiles(componentsDir);
    
    for (const file of componentFiles) {
      const content = fs.readFileSync(file, 'utf-8');
      const issues = this.checkComponentStyleConsistency(content, file);
      
      if (issues.length > 0) {
        this.addValidationResult(file, issues);
      }
    }
  }

  private checkComponentStyleConsistency(content: string, file: string): ConsistencyIssue[] {
    const issues: ConsistencyIssue[] = [];
    
    if (content.includes('style') && !content.includes('scoped')) {
      issues.push({
        type: 'component',
        severity: 'warning',
        file,
        actual: '全局样式',
        expected: '使用 scoped 样式',
        message: '组件样式未使用 scoped，可能影响其他组件'
      });
    }
    
    const inlineStylePattern = /style\s*=\s*["']([^"']+)["']/g;
    const inlineStyles = content.match(inlineStylePattern);
    
    if (inlineStyles && inlineStyles.length > 3) {
      issues.push({
        type: 'component',
        severity: 'info',
        file,
        actual: `${inlineStyles.length} 个内联样式`,
        expected: '使用 CSS 类代替内联样式',
        message: '过多内联样式，建议提取到 CSS 类中'
      });
    }
    
    return issues;
  }

  private addValidationResult(file: string, issues: ConsistencyIssue[]): void {
    const existing = this.validationResults.find(r => r.file === file);
    
    if (existing) {
      existing.issues.push(...issues);
      existing.score = this.calculateScore(existing.issues);
    } else {
      this.validationResults.push({
        file,
        issues,
        score: this.calculateScore(issues)
      });
    }
  }

  private calculateScore(issues: ConsistencyIssue[]): number {
    let score = 100;
    
    issues.forEach(issue => {
      if (issue.severity === 'error') score -= 10;
      else if (issue.severity === 'warning') score -= 5;
      else score -= 2;
    });
    
    return Math.max(0, score);
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

  private findCSSFiles(dir: string): string[] {
    const files: string[] = [];
    if (!fs.existsSync(dir)) return files;
    
    const items = fs.readdirSync(dir);
    for (const item of items) {
      const fullPath = path.join(dir, item);
      const stat = fs.statSync(fullPath);
      
      if (stat.isDirectory()) {
        files.push(...this.findCSSFiles(fullPath));
      } else if (item.endsWith('.css') || item.endsWith('.scss') || item.endsWith('.less')) {
        files.push(fullPath);
      }
    }
    
    return files;
  }

  private generateValidationReport(): void {
    const reportPath = path.join(this.outputDir, 'design-spec-validation-report.json');
    
    const report = {
      timestamp: new Date().toISOString(),
      summary: {
        totalFiles: this.validationResults.length,
        averageScore: this.calculateAverageScore(),
        issuesByType: this.getIssuesByType(),
        issuesBySeverity: this.getIssuesBySeverity()
      },
      spec: this.spec,
      results: this.validationResults
    };
    
    fs.writeFileSync(reportPath, JSON.stringify(report, null, 2), 'utf-8');
    console.log(`\n验证报告已生成: ${reportPath}`);
    
    this.generateSummaryReport();
    this.generateDesignSpecDocument();
  }

  private calculateAverageScore(): number {
    if (this.validationResults.length === 0) return 100;
    const total = this.validationResults.reduce((sum, r) => sum + r.score, 0);
    return Math.round(total / this.validationResults.length);
  }

  private getIssuesByType(): Record<string, number> {
    const counts: Record<string, number> = {};
    
    this.validationResults.forEach(result => {
      result.issues.forEach(issue => {
        counts[issue.type] = (counts[issue.type] || 0) + 1;
      });
    });
    
    return counts;
  }

  private getIssuesBySeverity(): Record<string, number> {
    const counts: Record<string, number> = { error: 0, warning: 0, info: 0 };
    
    this.validationResults.forEach(result => {
      result.issues.forEach(issue => {
        counts[issue.severity]++;
      });
    });
    
    return counts;
  }

  private generateSummaryReport(): void {
    const summaryPath = path.join(this.outputDir, 'design-spec-validation-summary.txt');
    
    const lines = [
      '='.repeat(60),
      '设计规范验证报告',
      '='.repeat(60),
      `生成时间: ${new Date().toLocaleString('zh-CN')}`,
      '',
      '-'.repeat(60),
      '总体统计',
      '-'.repeat(60),
      `验证文件数: ${this.validationResults.length}`,
      `平均得分: ${this.calculateAverageScore()}/100`,
      '',
      '-'.repeat(60),
      '问题统计',
      '-'.repeat(60),
    ];
    
    const severity = this.getIssuesBySeverity();
    lines.push(`错误: ${severity.error}`);
    lines.push(`警告: ${severity.warning}`);
    lines.push(`提示: ${severity.info}`);
    
    lines.push('', '-'.repeat(60), '按类型统计', '-'.repeat(60));
    const byType = this.getIssuesByType();
    Object.entries(byType).forEach(([type, count]) => {
      lines.push(`${type}: ${count} 个问题`);
    });
    
    lines.push('', '-'.repeat(60), '需要改进的文件', '-'.repeat(60));
    
    const lowScoreFiles = this.validationResults
      .filter(r => r.score < 80)
      .sort((a, b) => a.score - b.score);
    
    lowScoreFiles.slice(0, 10).forEach((result, idx) => {
      const relativePath = path.relative(this.projectRoot, result.file);
      lines.push(`\n${idx + 1}. ${relativePath}`);
      lines.push(`   得分: ${result.score}/100`);
      lines.push(`   问题数: ${result.issues.length}`);
    });
    
    lines.push('', '='.repeat(60), '验证完成', '='.repeat(60));
    
    fs.writeFileSync(summaryPath, lines.join('\n'), 'utf-8');
    console.log(`摘要报告已生成: ${summaryPath}`);
  }

  private generateDesignSpecDocument(): void {
    const specPath = path.join(this.outputDir, 'design-spec.md');
    
    const content = `# 设计规范文档

## 颜色规范

### 主色
${this.spec.colors.primary.map(c => `- ${c}`).join('\n')}

### 辅助色
${this.spec.colors.secondary.map(c => `- ${c}`).join('\n')}

### 成功色
${this.spec.colors.success.map(c => `- ${c}`).join('\n')}

### 警告色
${this.spec.colors.warning.map(c => `- ${c}`).join('\n')}

### 危险色
${this.spec.colors.danger.map(c => `- ${c}`).join('\n')}

### 信息色
${this.spec.colors.info.map(c => `- ${c}`).join('\n')}

### 文字颜色
${this.spec.colors.text.map(c => `- ${c}`).join('\n')}

### 背景颜色
${this.spec.colors.background.map(c => `- ${c}`).join('\n')}

## 字体规范

### 字体族
\`\`\`css
font-family: ${this.spec.fonts.families.join(', ')};
\`\`\`

### 字体大小
| 名称 | 值 |
|------|-----|
${this.spec.fonts.sizes.map(s => `| ${s.name} | ${s.value} |`).join('\n')}

### 字重
${this.spec.fonts.weights.join(', ')}

## 间距规范

### 标准间距值
${this.spec.spacing.values.join(', ')}

### 间距比例
基础单位: ${this.spec.spacing.scale}

## 圆角规范
${this.spec.borderRadius.join(', ')}

## 阴影规范
${this.spec.shadows.map((s, i) => `${i + 1}. \`${s}\``).join('\n')}

---

*此文档由设计规范验证工具自动生成*
`;

    fs.writeFileSync(specPath, content, 'utf-8');
    console.log(`设计规范文档已生成: ${specPath}`);
  }
}

async function main() {
  const projectRoot = path.resolve(__dirname, '..');
  const outputDir = path.join(projectRoot, 'design-spec-reports');
  
  const validator = new DesignSpecValidator(projectRoot, outputDir);
  await validator.validate();
  
  console.log('\n设计规范验证完成！');
}

main().catch(console.error);

export { DesignSpecValidator, ConsistencyIssue, ValidationResult };
