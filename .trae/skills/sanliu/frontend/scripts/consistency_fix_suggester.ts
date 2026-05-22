import * as fs from 'fs';
import * as path from 'path';

/**
 * 一致性修复建议器
 * 
 * 功能说明：
 * - 分析颜色、字体、间距、样式、无障碍问题
 * - 生成可自动修复和需手动修复的建议
 * - 生成自动修复脚本和修复指南
 * - 按优先级和类型分类问题
 * 
 * 输出内容：
 * - fix-suggestions/fix-suggestions.json - 修复建议报告
 * - fix-suggestions/auto-fix-script.ts - 自动修复脚本
 * - fix-suggestions/fix-guide.md - 修复指南
 * 
 * 使用方法：
 * ```bash
 * npx ts-node consistency_fix_suggester.ts
 * ```
 * 
 * @author GUI优化子代理
 * @version 1.0.0
 */

interface FixSuggestion {
  file: string;
  type: 'color' | 'font' | 'spacing' | 'style' | 'accessibility' | 'component';
  priority: 'high' | 'medium' | 'low';
  issue: string;
  currentCode: string;
  suggestedCode: string;
  explanation: string;
  autoFixable: boolean;
}

interface FixReport {
  timestamp: string;
  totalIssues: number;
  autoFixable: number;
  manualFixRequired: number;
  suggestions: FixSuggestion[];
}

class ConsistencyFixSuggester {
  private projectRoot: string;
  private outputDir: string;
  private suggestions: FixSuggestion[] = [];

  constructor(projectRoot: string, outputDir: string) {
    this.projectRoot = projectRoot;
    this.outputDir = outputDir;
    this.ensureOutputDir();
  }

  private ensureOutputDir(): void {
    if (!fs.existsSync(this.outputDir)) {
      fs.mkdirSync(this.outputDir, { recursive: true });
    }
  }

  public async suggest(): Promise<FixReport> {
    console.log('开始生成一致性修复建议...');
    
    await this.analyzeColorIssues();
    await this.analyzeFontIssues();
    await this.analyzeSpacingIssues();
    await this.analyzeStyleIssues();
    await this.analyzeAccessibilityIssues();
    
    this.generateFixReport();
    this.generateAutoFixScript();
    this.generateFixGuide();
    
    return this.createReport();
  }

  private async analyzeColorIssues(): Promise<void> {
    console.log('\n分析颜色问题...');
    
    const vueFiles = this.findVueFiles(path.join(this.projectRoot, 'src'));
    
    for (const file of vueFiles) {
      const content = fs.readFileSync(file, 'utf-8');
      const lines = content.split('\n');
      
      lines.forEach((line, index) => {
        const colorMatches = line.matchAll(/(color|background-color|border-color)\s*:\s*(#[0-9A-Fa-f]{3,6}|rgb\([^)]+\)|rgba\([^)]+\))/g);
        
        for (const match of colorMatches) {
          const property = match[1];
          const color = match[2];
          
          this.suggestions.push({
            file,
            type: 'color',
            priority: 'medium',
            issue: `硬编码颜色值: ${color}`,
            currentCode: line.trim(),
            suggestedCode: this.getColorFix(property, color, line),
            explanation: `使用 CSS 变量替代硬编码颜色，便于主题管理和维护`,
            autoFixable: true
          });
        }
      });
    }
  }

  private getColorFix(property: string, color: string, line: string): string {
    const varName = this.getColorVariableName(color);
    return line.replace(
      new RegExp(`${property}\\s*:\\s*${color.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')}`),
      `${property}: var(--${varName})`
    );
  }

  private getColorVariableName(color: string): string {
    const colorMap: Record<string, string> = {
      '#409EFF': 'color-primary',
      '#67C23A': 'color-success',
      '#E6A23C': 'color-warning',
      '#F56C6C': 'color-danger',
      '#909399': 'color-info',
      '#303133': 'color-text-primary',
      '#606266': 'color-text-regular',
      '#909399': 'color-text-secondary',
      '#C0C4CC': 'color-text-placeholder'
    };
    
    return colorMap[color.toUpperCase()] || 'color-custom';
  }

  private async analyzeFontIssues(): Promise<void> {
    console.log('\n分析字体问题...');
    
    const vueFiles = this.findVueFiles(path.join(this.projectRoot, 'src'));
    
    for (const file of vueFiles) {
      const content = fs.readFileSync(file, 'utf-8');
      const lines = content.split('\n');
      
      lines.forEach((line, index) => {
        const fontSizeMatches = line.matchAll(/font-size\s*:\s*(\d+px)/g);
        
        for (const match of fontSizeMatches) {
          const size = match[1];
          const standardSize = this.getStandardFontSize(size);
          
          if (standardSize && standardSize !== size) {
            this.suggestions.push({
              file,
              type: 'font',
              priority: 'low',
              issue: `非标准字体大小: ${size}`,
              currentCode: line.trim(),
              suggestedCode: line.replace(`font-size: ${size}`, `font-size: var(--font-size-${standardSize})`),
              explanation: `使用设计规范中的标准字体大小，保持一致性`,
              autoFixable: true
            });
          }
        }
        
        if (line.includes('font-family') && !line.includes('sans-serif')) {
          this.suggestions.push({
            file,
            type: 'font',
            priority: 'low',
            issue: '字体族缺少后备字体',
            currentCode: line.trim(),
            suggestedCode: this.getFontFamilyFix(line),
            explanation: '添加系统字体作为后备，提高兼容性',
            autoFixable: true
          });
        }
      });
    }
  }

  private getStandardFontSize(size: string): string | null {
    const sizeMap: Record<string, string> = {
      '12px': 'xs',
      '13px': 'sm',
      '14px': 'base',
      '16px': 'md',
      '18px': 'lg',
      '20px': 'xl',
      '22px': '2xl',
      '24px': '3xl'
    };
    
    return sizeMap[size] || null;
  }

  private getFontFamilyFix(line: string): string {
    const match = line.match(/font-family\s*:\s*([^;]+)/);
    if (match) {
      const current = match[1].trim();
      if (!current.includes('sans-serif')) {
        return line.replace(
          /font-family\s*:\s*[^;]+/,
          `font-family: ${current}, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif`
        );
      }
    }
    return line;
  }

  private async analyzeSpacingIssues(): Promise<void> {
    console.log('\n分析间距问题...');
    
    const vueFiles = this.findVueFiles(path.join(this.projectRoot, 'src'));
    
    for (const file of vueFiles) {
      const content = fs.readFileSync(file, 'utf-8');
      const lines = content.split('\n');
      
      lines.forEach((line, index) => {
        const spacingMatches = line.matchAll(/(margin|padding|gap)\s*:\s*(\d+px)/g);
        
        for (const match of spacingMatches) {
          const property = match[1];
          const value = match[2];
          const numValue = parseInt(value);
          
          if (numValue % 4 !== 0) {
            const nearestStandard = Math.round(numValue / 4) * 4;
            this.suggestions.push({
              file,
              type: 'spacing',
              priority: 'low',
              issue: `非标准间距值: ${value}`,
              currentCode: line.trim(),
              suggestedCode: line.replace(`${property}: ${value}`, `${property}: ${nearestStandard}px`),
              explanation: `使用 4px 倍数的标准间距，保持设计一致性`,
              autoFixable: true
            });
          }
        }
      });
    }
  }

  private async analyzeStyleIssues(): Promise<void> {
    console.log('\n分析样式问题...');
    
    const vueFiles = this.findVueFiles(path.join(this.projectRoot, 'src'));
    
    for (const file of vueFiles) {
      const content = fs.readFileSync(file, 'utf-8');
      
      if (content.includes('<style') && !content.includes('scoped')) {
        this.suggestions.push({
          file,
          type: 'style',
          priority: 'high',
          issue: '组件样式未使用 scoped',
          currentCode: '<style>',
          suggestedCode: '<style scoped>',
          explanation: '添加 scoped 属性避免样式污染其他组件',
          autoFixable: true
        });
      }
      
      const inlineStyles = (content.match(/style\s*=\s*["'][^"']+["']/g) || []).length;
      if (inlineStyles > 3) {
        this.suggestions.push({
          file,
          type: 'style',
          priority: 'medium',
          issue: `过多内联样式 (${inlineStyles} 处)`,
          currentCode: '内联样式分散在模板中',
          suggestedCode: this.generateStyleClassSuggestion(content),
          explanation: '将内联样式提取到 CSS 类中，提高可维护性',
          autoFixable: false
        });
      }
    }
  }

  private generateStyleClassSuggestion(content: string): string {
    const inlineStyles = content.matchAll(/style\s*=\s*["']([^"']+)["']/g);
    const styles: string[] = [];
    let classIndex = 1;
    
    for (const match of inlineStyles) {
      styles.push(`.inline-style-${classIndex} { ${match[1]} }`);
      classIndex++;
    }
    
    return `/* 在 <style> 中添加 */
${styles.join('\n')}

/* 在模板中使用 class 替代 style */`;
  }

  private async analyzeAccessibilityIssues(): Promise<void> {
    console.log('\n分析无障碍问题...');
    
    const vueFiles = this.findVueFiles(path.join(this.projectRoot, 'src'));
    
    for (const file of vueFiles) {
      const content = fs.readFileSync(file, 'utf-8');
      const lines = content.split('\n');
      
      lines.forEach((line, index) => {
        if (line.includes('<img') && !line.includes('alt=')) {
          this.suggestions.push({
            file,
            type: 'accessibility',
            priority: 'high',
            issue: '图片缺少 alt 属性',
            currentCode: line.trim(),
            suggestedCode: line.replace('<img', '<img alt="图片描述"'),
            explanation: '添加 alt 属性提高无障碍访问性',
            autoFixable: false
          });
        }
        
        if (line.includes('v-for') && !content.includes(':key')) {
          this.suggestions.push({
            file,
            type: 'accessibility',
            priority: 'high',
            issue: 'v-for 缺少 :key 属性',
            currentCode: line.trim(),
            suggestedCode: this.addKeyAttribute(line),
            explanation: '添加 :key 属性提高渲染性能和可访问性',
            autoFixable: false
          });
        }
        
        if (line.includes('<button') && line.includes('icon') && !line.includes('aria-label')) {
          this.suggestions.push({
            file,
            type: 'accessibility',
            priority: 'medium',
            issue: '图标按钮缺少 aria-label',
            currentCode: line.trim(),
            suggestedCode: line.replace('<button', '<button aria-label="按钮描述"'),
            explanation: '添加 aria-label 提高屏幕阅读器兼容性',
            autoFixable: false
          });
        }
      });
    }
  }

  private addKeyAttribute(line: string): string {
    const forMatch = line.match(/v-for="[^"]*in\s+(\w+)/);
    if (forMatch) {
      const listName = forMatch[1];
      return line.replace(/(<\w+)/, `$1 :key="${listName}Item.id || index"`);
    }
    return line;
  }

  private generateFixReport(): void {
    const reportPath = path.join(this.outputDir, 'fix-suggestions.json');
    
    const report = this.createReport();
    
    fs.writeFileSync(reportPath, JSON.stringify(report, null, 2), 'utf-8');
    console.log(`\n修复建议报告已生成: ${reportPath}`);
  }

  private createReport(): FixReport {
    return {
      timestamp: new Date().toISOString(),
      totalIssues: this.suggestions.length,
      autoFixable: this.suggestions.filter(s => s.autoFixable).length,
      manualFixRequired: this.suggestions.filter(s => !s.autoFixable).length,
      suggestions: this.suggestions
    };
  }

  private generateAutoFixScript(): void {
    const scriptPath = path.join(this.outputDir, 'auto-fix-script.ts');
    
    const autoFixable = this.suggestions.filter(s => s.autoFixable);
    
    const script = `import * as fs from 'fs';
import * as path from 'path';

interface Fix {
  file: string;
  search: string;
  replace: string;
}

const fixes: Fix[] = [
${autoFixable.map(s => `  {
    file: '${s.file}',
    search: \`${s.currentCode.replace(/`/g, '\\`')}\`,
    replace: \`${s.suggestedCode.replace(/`/g, '\\`')}\`
  }`).join(',\n')}
];

function applyFixes() {
  const fileChanges = new Map<string, { content: string; changes: number }>();
  
  for (const fix of fixes) {
    if (!fileChanges.has(fix.file)) {
      const content = fs.readFileSync(fix.file, 'utf-8');
      fileChanges.set(fix.file, { content, changes: 0 });
    }
    
    const fileData = fileChanges.get(fix.file)!;
    if (fileData.content.includes(fix.search)) {
      fileData.content = fileData.content.replace(fix.search, fix.replace);
      fileData.changes++;
    }
  }
  
  for (const [file, data] of fileChanges) {
    if (data.changes > 0) {
      fs.writeFileSync(file, data.content, 'utf-8');
      console.log(\`已修复: \${file} (\${data.changes} 处)\`);
    }
  }
  
  console.log('\\n自动修复完成！');
}

applyFixes();
`;

    fs.writeFileSync(scriptPath, script, 'utf-8');
    console.log(`自动修复脚本已生成: ${scriptPath}`);
  }

  private generateFixGuide(): void {
    const guidePath = path.join(this.outputDir, 'fix-guide.md');
    
    const groupedByType = this.groupByType();
    const groupedByPriority = this.groupByPriority();
    
    const content = `# 一致性修复指南

## 概览

- **总问题数**: ${this.suggestions.length}
- **可自动修复**: ${this.suggestions.filter(s => s.autoFixable).length}
- **需手动修复**: ${this.suggestions.filter(s => !s.autoFixable).length}

## 按优先级分类

### 高优先级 (${groupedByPriority.high.length} 个)

${groupedByPriority.high.map((s, i) => `
${i + 1}. **${s.issue}**
   - 文件: \`${path.relative(this.projectRoot, s.file)}\`
   - 类型: ${s.type}
   - 当前代码:
     \`\`\`
     ${s.currentCode}
     \`\`\`
   - 建议修改:
     \`\`\`
     ${s.suggestedCode}
     \`\`\`
   - 说明: ${s.explanation}
`).join('\n')}

### 中优先级 (${groupedByPriority.medium.length} 个)

${groupedByPriority.medium.slice(0, 10).map((s, i) => `
${i + 1}. **${s.issue}**
   - 文件: \`${path.relative(this.projectRoot, s.file)}\`
   - 说明: ${s.explanation}
`).join('\n')}

${groupedByPriority.medium.length > 10 ? `\n... 还有 ${groupedByPriority.medium.length - 10} 个中优先级问题` : ''}

### 低优先级 (${groupedByPriority.low.length} 个)

${groupedByPriority.low.slice(0, 5).map((s, i) => `
${i + 1}. **${s.issue}**
   - 文件: \`${path.relative(this.projectRoot, s.file)}\`
   - 说明: ${s.explanation}
`).join('\n')}

${groupedByPriority.low.length > 5 ? `\n... 还有 ${groupedByPriority.low.length - 5} 个低优先级问题` : ''}

## 按类型分类

${Object.entries(groupedByType).map(([type, items]) => `
### ${this.getTypeName(type)} (${items.length} 个)

${items.slice(0, 5).map((s, i) => `${i + 1}. ${s.issue} - \`${path.basename(s.file)}\``).join('\n')}
${items.length > 5 ? `\n... 还有 ${items.length - 5} 个问题` : ''}
`).join('\n')}

## 自动修复

运行以下命令自动修复可修复的问题：

\`\`\`bash
npx ts-node ${path.join(this.outputDir, 'auto-fix-script.ts')}
\`\`\`

## 手动修复步骤

1. **颜色问题**
   - 创建 CSS 变量文件
   - 替换硬编码颜色为变量引用
   - 测试主题切换功能

2. **字体问题**
   - 定义标准字体大小变量
   - 更新组件使用标准字体
   - 检查字体渲染效果

3. **间距问题**
   - 采用 4px 或 8px 倍数系统
   - 更新间距值
   - 检查布局一致性

4. **样式问题**
   - 为组件样式添加 scoped
   - 提取内联样式到 CSS 类
   - 检查样式隔离效果

5. **无障碍问题**
   - 添加 alt 属性
   - 添加 aria 标签
   - 测试屏幕阅读器兼容性

## 最佳实践

1. **定期检查**: 每次提交前运行一致性检查
2. **代码审查**: 在 PR 中关注一致性问题
3. **文档更新**: 保持设计规范文档最新
4. **团队培训**: 确保团队了解设计规范

---

*此指南由一致性修复建议工具自动生成*
`;

    fs.writeFileSync(guidePath, content, 'utf-8');
    console.log(`修复指南已生成: ${guidePath}`);
  }

  private groupByType(): Record<string, FixSuggestion[]> {
    const grouped: Record<string, FixSuggestion[]> = {};
    
    for (const suggestion of this.suggestions) {
      if (!grouped[suggestion.type]) {
        grouped[suggestion.type] = [];
      }
      grouped[suggestion.type].push(suggestion);
    }
    
    return grouped;
  }

  private groupByPriority(): Record<string, FixSuggestion[]> {
    return {
      high: this.suggestions.filter(s => s.priority === 'high'),
      medium: this.suggestions.filter(s => s.priority === 'medium'),
      low: this.suggestions.filter(s => s.priority === 'low')
    };
  }

  private getTypeName(type: string): string {
    const names: Record<string, string> = {
      color: '颜色问题',
      font: '字体问题',
      spacing: '间距问题',
      style: '样式问题',
      accessibility: '无障碍问题',
      component: '组件问题'
    };
    return names[type] || type;
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
}

async function main() {
  const projectRoot = path.resolve(__dirname, '..');
  const outputDir = path.join(projectRoot, 'fix-suggestions');
  
  const suggester = new ConsistencyFixSuggester(projectRoot, outputDir);
  await suggester.suggest();
  
  console.log('\n一致性修复建议生成完成！');
}

main().catch(console.error);

export { ConsistencyFixSuggester, FixSuggestion };
