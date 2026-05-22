import * as fs from 'fs';
import * as path from 'path';

/**
 * 适配问题修复器
 * 
 * 功能说明：
 * - 分析视口、布局、字体、触摸目标、媒体查询、图片、间距问题
 * - 生成可自动修复和需手动修复的建议
 * - 生成响应式 CSS 工具类
 * - 提供详细的修复指南
 * 
 * 输出内容：
 * - adaptation-fixes/adaptation-fixes.json - 修复报告
 * - adaptation-fixes/auto-fix-adaptation.ts - 自动修复脚本
 * - adaptation-fixes/adaptation-fix-guide.md - 修复指南
 * - adaptation-fixes/responsive-utilities.css - 响应式工具类
 * 
 * 使用方法：
 * ```bash
 * npx ts-node adaptation_fixer.ts
 * ```
 * 
 * @author GUI优化子代理
 * @version 1.0.0
 */

interface AdaptationFix {
  file: string;
  type: 'viewport' | 'layout' | 'typography' | 'touch' | 'media-query' | 'image' | 'spacing';
  priority: 'high' | 'medium' | 'low';
  issue: string;
  currentCode: string;
  suggestedCode: string;
  explanation: string;
  autoFixable: boolean;
  breakpoint?: string;
}

interface FixResult {
  file: string;
  fixes: AdaptationFix[];
  appliedCount: number;
  skippedCount: number;
}

class AdaptationFixer {
  private projectRoot: string;
  private outputDir: string;
  private fixes: AdaptationFix[] = [];
  private results: FixResult[] = [];

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

  public async fix(): Promise<FixResult[]> {
    console.log('开始分析适配问题并生成修复方案...');
    
    await this.analyzeViewportIssues();
    await this.analyzeLayoutIssues();
    await this.analyzeTypographyIssues();
    await this.analyzeTouchTargetIssues();
    await this.analyzeMediaQueryIssues();
    await this.analyzeImageIssues();
    await this.analyzeSpacingIssues();
    
    this.generateFixReport();
    this.generateAutoFixScript();
    this.generateFixGuide();
    this.generateResponsiveCSS();
    
    return this.results;
  }

  private async analyzeViewportIssues(): Promise<void> {
    console.log('\n分析视口问题...');
    
    const htmlPath = path.join(this.projectRoot, 'index.html');
    if (fs.existsSync(htmlPath)) {
      const content = fs.readFileSync(htmlPath, 'utf-8');
      
      if (!content.includes('viewport')) {
        this.fixes.push({
          file: htmlPath,
          type: 'viewport',
          priority: 'high',
          issue: '缺少 viewport meta 标签',
          currentCode: '<head>',
          suggestedCode: `<head>
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=5.0">`,
          explanation: '添加 viewport meta 标签确保移动端正确渲染',
          autoFixable: true
        });
      } else if (!content.includes('maximum-scale')) {
        this.fixes.push({
          file: htmlPath,
          type: 'viewport',
          priority: 'low',
          issue: 'viewport 缺少 maximum-scale 属性',
          currentCode: content.match(/<meta name="viewport"[^>]*>/)?.[0] || '',
          suggestedCode: '<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=5.0">',
          explanation: '添加 maximum-scale 允许用户缩放，提高可访问性',
          autoFixable: true
        });
      }
    }
  }

  private async analyzeLayoutIssues(): Promise<void> {
    console.log('\n分析布局问题...');
    
    const vueFiles = this.findVueFiles(path.join(this.projectRoot, 'src'));
    
    for (const file of vueFiles) {
      const content = fs.readFileSync(file, 'utf-8');
      const lines = content.split('\n');
      
      lines.forEach((line, index) => {
        const fixedWidthMatch = line.match(/width\s*:\s*(\d+)px/);
        if (fixedWidthMatch) {
          const width = parseInt(fixedWidthMatch[1]);
          if (width > 600) {
            this.fixes.push({
              file,
              type: 'layout',
              priority: 'high',
              issue: `固定宽度 ${width}px 可能导致移动端溢出`,
              currentCode: line.trim(),
              suggestedCode: this.getWidthFix(line, width),
              explanation: '使用 max-width 和相对单位替代固定宽度',
              autoFixable: true,
              breakpoint: 'mobile'
            });
          }
        }
        
        if (line.includes('position: fixed') && !content.includes('@media')) {
          this.fixes.push({
            file,
            type: 'layout',
            priority: 'medium',
            issue: '固定定位元素缺少响应式适配',
            currentCode: line.trim(),
            suggestedCode: this.getFixedPositionFix(line),
            explanation: '为固定定位元素添加移动端媒体查询',
            autoFixable: false,
            breakpoint: 'mobile'
          });
        }
        
        if (line.includes('float:') && !content.includes('@media')) {
          this.fixes.push({
            file,
            type: 'layout',
            priority: 'low',
            issue: '使用 float 布局，建议使用 Flexbox 或 Grid',
            currentCode: line.trim(),
            suggestedCode: this.getFloatFix(line),
            explanation: 'Flexbox 和 Grid 提供更好的响应式支持',
            autoFixable: false
          });
        }
      });
    }
  }

  private getWidthFix(line: string, width: number): string {
    return line.replace(
      /width\s*:\s*\d+px/,
      `width: 100%; max-width: ${width}px`
    );
  }

  private getFixedPositionFix(line: string): string {
    const indent = line.match(/^(\s*)/)?.[1] || '';
    return `${line}

${indent}@media (max-width: 768px) {
${indent}  /* 移动端适配 */
${indent}}`;
  }

  private getFloatFix(line: string): string {
    return `/* 考虑使用 Flexbox 替代 float */
display: flex;
/* ${line.trim()} */`;
  }

  private async analyzeTypographyIssues(): Promise<void> {
    console.log('\n分析字体排版问题...');
    
    const vueFiles = this.findVueFiles(path.join(this.projectRoot, 'src'));
    
    for (const file of vueFiles) {
      const content = fs.readFileSync(file, 'utf-8');
      const lines = content.split('\n');
      
      lines.forEach((line, index) => {
        const fontSizeMatch = line.match(/font-size\s*:\s*(\d+)px/);
        if (fontSizeMatch) {
          const size = parseInt(fontSizeMatch[1]);
          if (size < 12) {
            this.fixes.push({
              file,
              type: 'typography',
              priority: 'high',
              issue: `字体大小 ${size}px 过小，影响可读性`,
              currentCode: line.trim(),
              suggestedCode: line.replace(/font-size\s*:\s*\d+px/, 'font-size: 12px'),
              explanation: '移动端最小字体应为 12px',
              autoFixable: true,
              breakpoint: 'mobile'
            });
          }
        }
        
        if (line.includes('line-height') && line.match(/line-height\s*:\s*1(?!\.)/)) {
          this.fixes.push({
            file,
            type: 'typography',
            priority: 'low',
            issue: '行高过小可能影响可读性',
            currentCode: line.trim(),
            suggestedCode: line.replace(/line-height\s*:\s*1/, 'line-height: 1.5'),
            explanation: '建议行高至少为 1.5 以提高可读性',
            autoFixable: true
          });
        }
      });
    }
  }

  private async analyzeTouchTargetIssues(): Promise<void> {
    console.log('\n分析触摸目标问题...');
    
    const vueFiles = this.findVueFiles(path.join(this.projectRoot, 'src'));
    
    for (const file of vueFiles) {
      const content = fs.readFileSync(file, 'utf-8');
      const lines = content.split('\n');
      
      lines.forEach((line, index) => {
        if (line.includes('<button') || line.includes('<a ') || line.includes('role="button"')) {
          const hasSize = line.includes('width') || line.includes('height') || line.includes('padding');
          
          if (!hasSize && !line.includes('class=')) {
            this.fixes.push({
              file,
              type: 'touch',
              priority: 'high',
              issue: '触摸目标可能过小',
              currentCode: line.trim(),
              suggestedCode: this.addTouchTargetSize(line),
              explanation: '触摸目标最小应为 44x44 像素',
              autoFixable: false,
              breakpoint: 'mobile'
            });
          }
        }
        
        const paddingMatch = line.match(/padding\s*:\s*(\d+)px/);
        if (paddingMatch) {
          const padding = parseInt(paddingMatch[1]);
          if (padding < 8 && (line.includes('button') || line.includes('click'))) {
            this.fixes.push({
              file,
              type: 'touch',
              priority: 'medium',
              issue: `内边距 ${padding}px 可能导致触摸目标过小`,
              currentCode: line.trim(),
              suggestedCode: line.replace(/padding\s*:\s*\d+px/, 'padding: 12px'),
              explanation: '增加内边距确保触摸目标足够大',
              autoFixable: true,
              breakpoint: 'mobile'
            });
          }
        }
      });
    }
  }

  private addTouchTargetSize(line: string): string {
    const indent = line.match(/^(\s*)/)?.[1] || '';
    const className = `touch-target`;
    
    return `${line.replace(/>$/, ` class="${className}">`)}

${indent}<style scoped>
${indent}.${className} {
${indent}  min-width: 44px;
${indent}  min-height: 44px;
${indent}  display: inline-flex;
${indent}  align-items: center;
${indent}  justify-content: center;
${indent}}
${indent}</style>`;
  }

  private async analyzeMediaQueryIssues(): Promise<void> {
    console.log('\n分析媒体查询问题...');
    
    const styleFiles = this.findStyleFiles(path.join(this.projectRoot, 'src'));
    
    for (const file of styleFiles) {
      const content = fs.readFileSync(file, 'utf-8');
      
      const hasMobileQuery = content.includes('max-width: 768px') || 
                            content.includes('max-width: 480px');
      const hasTabletQuery = content.includes('max-width: 1024px') || 
                            content.includes('min-width: 768px');
      
      if (!hasMobileQuery && !hasTabletQuery) {
        this.fixes.push({
          file,
          type: 'media-query',
          priority: 'medium',
          issue: '缺少响应式媒体查询',
          currentCode: '/* 无媒体查询 */',
          suggestedCode: this.generateMediaQueries(),
          explanation: '添加标准断点的媒体查询',
          autoFixable: false
        });
      }
    }
    
    const vueFiles = this.findVueFiles(path.join(this.projectRoot, 'src'));
    
    for (const file of vueFiles) {
      const content = fs.readFileSync(file, 'utf-8');
      
      if (content.includes('<style') && !content.includes('@media')) {
        const hasResponsiveNeed = content.includes('width:') || 
                                   content.includes('padding:') ||
                                   content.includes('margin:');
        
        if (hasResponsiveNeed) {
          this.fixes.push({
            file,
            type: 'media-query',
            priority: 'medium',
            issue: '组件样式缺少媒体查询',
            currentCode: '<style scoped>',
            suggestedCode: this.generateComponentMediaQuery(content),
            explanation: '为组件添加响应式媒体查询',
            autoFixable: false
          });
        }
      }
    }
  }

  private generateMediaQueries(): string {
    return `/* 响应式媒体查询 */

/* 移动设备 */
@media (max-width: 480px) {
  /* 小屏幕手机 */
}

@media (max-width: 768px) {
  /* 平板和手机 */
}

/* 平板 */
@media (min-width: 769px) and (max-width: 1024px) {
  /* 平板设备 */
}

/* 桌面 */
@media (min-width: 1025px) and (max-width: 1280px) {
  /* 小桌面 */
}

@media (min-width: 1281px) {
  /* 大桌面 */
}

/* 打印样式 */
@media print {
  /* 打印优化 */
}`;
  }

  private generateComponentMediaQuery(content: string): string {
    const indent = '  ';
    return `<style scoped>
/* 基础样式 */

/* 移动端适配 */
@media (max-width: 768px) {
${indent}/* 移动端样式 */
}

/* 平板适配 */
@media (min-width: 769px) and (max-width: 1024px) {
${indent}/* 平板样式 */
}`;
  }

  private async analyzeImageIssues(): Promise<void> {
    console.log('\n分析图片问题...');
    
    const vueFiles = this.findVueFiles(path.join(this.projectRoot, 'src'));
    
    for (const file of vueFiles) {
      const content = fs.readFileSync(file, 'utf-8');
      const lines = content.split('\n');
      
      lines.forEach((line, index) => {
        if (line.includes('<img') && !line.includes('srcset')) {
          this.fixes.push({
            file,
            type: 'image',
            priority: 'medium',
            issue: '图片缺少响应式 srcset',
            currentCode: line.trim(),
            suggestedCode: this.addResponsiveImage(line),
            explanation: '添加 srcset 提供不同分辨率的图片',
            autoFixable: false
          });
        }
        
        if (line.includes('<img') && !line.includes('loading=')) {
          this.fixes.push({
            file,
            type: 'image',
            priority: 'low',
            issue: '图片缺少懒加载',
            currentCode: line.trim(),
            suggestedCode: line.replace('<img', '<img loading="lazy"'),
            explanation: '添加懒加载提升页面加载性能',
            autoFixable: true
          });
        }
      });
    }
  }

  private addResponsiveImage(line: string): string {
    const srcMatch = line.match(/src\s*=\s*["']([^"']+)["']/);
    if (srcMatch) {
      const src = srcMatch[1];
      const baseName = src.replace(/\.[^.]+$/, '');
      const ext = src.match(/\.[^.]+$/)?.[0] || '.jpg';
      
      return line.replace(
        /src\s*=\s*["'][^"']+["']/,
        `src="${src}" srcset="${baseName}-320w${ext} 320w, ${baseName}-640w${ext} 640w, ${baseName}-1024w${ext} 1024w" sizes="(max-width: 768px) 100vw, (max-width: 1024px) 50vw, 33vw"`
      );
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
        const marginMatch = line.match(/margin\s*:\s*(\d+)px/);
        if (marginMatch) {
          const margin = parseInt(marginMatch[1]);
          if (margin > 20 && !content.includes('@media')) {
            this.fixes.push({
              file,
              type: 'spacing',
              priority: 'low',
              issue: `大边距 ${margin}px 可能需要移动端调整`,
              currentCode: line.trim(),
              suggestedCode: this.addResponsiveSpacing(line, margin),
              explanation: '为移动端减小边距',
              autoFixable: false,
              breakpoint: 'mobile'
            });
          }
        }
        
        const paddingMatch = line.match(/padding\s*:\s*(\d+)px/);
        if (paddingMatch) {
          const padding = parseInt(paddingMatch[1]);
          if (padding > 16 && !content.includes('@media')) {
            this.fixes.push({
              file,
              type: 'spacing',
              priority: 'low',
              issue: `大内边距 ${padding}px 可能需要移动端调整`,
              currentCode: line.trim(),
              suggestedCode: this.addResponsiveSpacing(line, padding),
              explanation: '为移动端减小内边距',
              autoFixable: false,
              breakpoint: 'mobile'
            });
          }
        }
      });
    }
  }

  private addResponsiveSpacing(line: string, value: number): string {
    const indent = line.match(/^(\s*)/)?.[1] || '';
    const mobileValue = Math.round(value * 0.6);
    
    return `${line}

${indent}@media (max-width: 768px) {
${indent}  ${line.trim().replace(/:\s*\d+px/, `: ${mobileValue}px`)}
${indent}}`;
  }

  private generateFixReport(): void {
    const reportPath = path.join(this.outputDir, 'adaptation-fixes.json');
    
    const report = {
      timestamp: new Date().toISOString(),
      summary: {
        totalIssues: this.fixes.length,
        autoFixable: this.fixes.filter(f => f.autoFixable).length,
        manualFixRequired: this.fixes.filter(f => !f.autoFixable).length,
        byPriority: {
          high: this.fixes.filter(f => f.priority === 'high').length,
          medium: this.fixes.filter(f => f.priority === 'medium').length,
          low: this.fixes.filter(f => f.priority === 'low').length
        },
        byType: this.groupByType()
      },
      fixes: this.fixes
    };
    
    fs.writeFileSync(reportPath, JSON.stringify(report, null, 2), 'utf-8');
    console.log(`\n修复报告已生成: ${reportPath}`);
  }

  private groupByType(): Record<string, number> {
    const counts: Record<string, number> = {};
    
    for (const fix of this.fixes) {
      counts[fix.type] = (counts[fix.type] || 0) + 1;
    }
    
    return counts;
  }

  private generateAutoFixScript(): void {
    const scriptPath = path.join(this.outputDir, 'auto-fix-adaptation.ts');
    
    const autoFixable = this.fixes.filter(f => f.autoFixable);
    
    const script = `import * as fs from 'fs';
import * as path from 'path';

interface Fix {
  file: string;
  search: string;
  replace: string;
  type: string;
}

const fixes: Fix[] = [
${autoFixable.slice(0, 50).map(f => `  {
    file: '${f.file}',
    search: \`${f.currentCode.replace(/`/g, '\\`')}\`,
    replace: \`${f.suggestedCode.replace(/`/g, '\\`')}\`,
    type: '${f.type}'
  }`).join(',\n')}
];

function applyFixes() {
  console.log('开始应用自动修复...');
  
  const fileChanges = new Map<string, { content: string; count: number }>();
  
  for (const fix of fixes) {
    if (!fileChanges.has(fix.file)) {
      try {
        const content = fs.readFileSync(fix.file, 'utf-8');
        fileChanges.set(fix.file, { content, count: 0 });
      } catch (error) {
        console.warn(\`无法读取文件: \${fix.file}\`);
        continue;
      }
    }
    
    const fileData = fileChanges.get(fix.file)!;
    if (fileData.content.includes(fix.search)) {
      fileData.content = fileData.content.replace(fix.search, fix.replace);
      fileData.count++;
      console.log(\`  修复: \${fix.type} - \${fix.file}\`);
    }
  }
  
  for (const [file, data] of fileChanges) {
    if (data.count > 0) {
      fs.writeFileSync(file, data.content, 'utf-8');
      console.log(\`✓ 已修复 \${file} (\${data.count} 处)\`);
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
    const guidePath = path.join(this.outputDir, 'adaptation-fix-guide.md');
    
    const groupedByPriority = {
      high: this.fixes.filter(f => f.priority === 'high'),
      medium: this.fixes.filter(f => f.priority === 'medium'),
      low: this.fixes.filter(f => f.priority === 'low')
    };
    
    const content = `# 响应式适配修复指南

## 概览

- **总问题数**: ${this.fixes.length}
- **可自动修复**: ${this.fixes.filter(f => f.autoFixable).length}
- **需手动修复**: ${this.fixes.filter(f => !f.autoFixable).length}

## 按优先级分类

### 高优先级 (${groupedByPriority.high.length} 个)

${groupedByPriority.high.slice(0, 10).map((f, i) => `
${i + 1}. **${f.issue}**
   - 文件: \`${path.relative(this.projectRoot, f.file)}\`
   - 类型: ${f.type}
   - 当前代码:
     \`\`\`
     ${f.currentCode}
     \`\`\`
   - 建议修改:
     \`\`\`
     ${f.suggestedCode}
     \`\`\`
   - 说明: ${f.explanation}
`).join('\n')}

### 中优先级 (${groupedByPriority.medium.length} 个)

${groupedByPriority.medium.slice(0, 10).map((f, i) => `
${i + 1}. **${f.issue}**
   - 文件: \`${path.relative(this.projectRoot, f.file)}\`
   - 说明: ${f.explanation}
`).join('\n')}

### 低优先级 (${groupedByPriority.low.length} 个)

${groupedByPriority.low.slice(0, 5).map((f, i) => `
${i + 1}. **${f.issue}**
   - 文件: \`${path.relative(this.projectRoot, f.file)}\`
`).join('\n')}

## 修复步骤

### 1. 自动修复

运行以下命令自动修复可修复的问题：

\`\`\`bash
npx ts-node ${path.join(this.outputDir, 'auto-fix-adaptation.ts')}
\`\`\`

### 2. 手动修复

#### 视口问题
- 确保 index.html 包含正确的 viewport meta 标签
- 添加 maximum-scale 属性提高可访问性

#### 布局问题
- 使用 max-width 替代固定 width
- 为固定定位元素添加移动端媒体查询
- 考虑使用 Flexbox 或 Grid 替代 float

#### 字体排版问题
- 移动端字体最小 12px
- 行高建议至少 1.5

#### 触摸目标问题
- 触摸目标最小 44x44 像素
- 按钮之间保持至少 8px 间距

#### 媒体查询问题
- 添加标准断点的媒体查询
- 移动优先设计

#### 图片问题
- 添加 srcset 提供响应式图片
- 使用 loading="lazy" 懒加载

#### 间距问题
- 移动端适当减小边距和内边距

## 测试验证

修复后，请在以下设备上测试：

1. **移动设备**
   - iPhone SE (375x667)
   - iPhone 12 (390x844)
   - Pixel 5 (393x851)

2. **平板设备**
   - iPad Mini (768x1024)
   - iPad Pro (1024x1366)

3. **桌面设备**
   - 1280x720
   - 1920x1080

## 最佳实践

1. **移动优先**: 从小屏幕开始设计，逐步增强到大屏幕
2. **相对单位**: 使用 rem、em、vw、vh 替代固定像素
3. **弹性布局**: 使用 Flexbox 和 Grid 实现弹性布局
4. **图片优化**: 提供多种尺寸的图片，使用懒加载
5. **触摸友好**: 确保触摸目标足够大，间距合理

---

*此指南由响应式适配修复工具自动生成*
`;

    fs.writeFileSync(guidePath, content, 'utf-8');
    console.log(`修复指南已生成: ${guidePath}`);
  }

  private generateResponsiveCSS(): void {
    const cssPath = path.join(this.outputDir, 'responsive-utilities.css');
    
    const css = `/* 响应式工具类 */

/* 隐藏/显示 */
.hide-mobile {
  display: block;
}

.show-mobile {
  display: none;
}

.hide-tablet {
  display: block;
}

.show-tablet {
  display: none;
}

@media (max-width: 768px) {
  .hide-mobile {
    display: none !important;
  }
  
  .show-mobile {
    display: block !important;
  }
}

@media (min-width: 769px) and (max-width: 1024px) {
  .hide-tablet {
    display: none !important;
  }
  
  .show-tablet {
    display: block !important;
  }
}

/* 响应式间距 */
.padding-responsive {
  padding: 24px;
}

.margin-responsive {
  margin: 24px;
}

@media (max-width: 768px) {
  .padding-responsive {
    padding: 16px;
  }
  
  .margin-responsive {
    margin: 16px;
  }
}

@media (max-width: 480px) {
  .padding-responsive {
    padding: 12px;
  }
  
  .margin-responsive {
    margin: 12px;
  }
}

/* 响应式字体 */
.font-responsive {
  font-size: 16px;
  line-height: 1.5;
}

@media (max-width: 768px) {
  .font-responsive {
    font-size: 14px;
  }
}

@media (max-width: 480px) {
  .font-responsive {
    font-size: 12px;
  }
}

/* 响应式容器 */
.container-responsive {
  width: 100%;
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 24px;
}

@media (max-width: 768px) {
  .container-responsive {
    padding: 0 16px;
  }
}

/* 响应式网格 */
.grid-responsive {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 24px;
}

@media (max-width: 768px) {
  .grid-responsive {
    grid-template-columns: 1fr;
    gap: 16px;
  }
}

/* 响应式 Flexbox */
.flex-responsive {
  display: flex;
  gap: 24px;
}

@media (max-width: 768px) {
  .flex-responsive {
    flex-direction: column;
    gap: 16px;
  }
}

/* 触摸目标 */
.touch-target {
  min-width: 44px;
  min-height: 44px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
}

/* 图片响应式 */
.img-responsive {
  max-width: 100%;
  height: auto;
  display: block;
}

/* 文字截断 */
.text-truncate {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.text-truncate-2 {
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.text-truncate-3 {
  display: -webkit-box;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

/* 安全区域 */
.safe-area-inset {
  padding-left: env(safe-area-inset-left);
  padding-right: env(safe-area-inset-right);
  padding-bottom: env(safe-area-inset-bottom);
}

/* 滚动优化 */
.scroll-smooth {
  scroll-behavior: smooth;
  -webkit-overflow-scrolling: touch;
}

/* 防止文字选择 */
.no-select {
  -webkit-user-select: none;
  -moz-user-select: none;
  -ms-user-select: none;
  user-select: none;
}

/* 触摸反馈 */
.tap-highlight {
  -webkit-tap-highlight-color: rgba(0, 0, 0, 0.1);
}

/* 响应式断点变量 */
:root {
  --breakpoint-xs: 480px;
  --breakpoint-sm: 640px;
  --breakpoint-md: 768px;
  --breakpoint-lg: 1024px;
  --breakpoint-xl: 1280px;
  --breakpoint-2xl: 1536px;
  
  --spacing-xs: 4px;
  --spacing-sm: 8px;
  --spacing-md: 16px;
  --spacing-lg: 24px;
  --spacing-xl: 32px;
  --spacing-2xl: 48px;
}
`;

    fs.writeFileSync(cssPath, css, 'utf-8');
    console.log(`响应式 CSS 工具类已生成: ${cssPath}`);
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
  const outputDir = path.join(projectRoot, 'adaptation-fixes');
  
  const fixer = new AdaptationFixer(projectRoot, outputDir);
  await fixer.fix();
  
  console.log('\n适配问题修复分析完成！');
}

main().catch(console.error);

export { AdaptationFixer, AdaptationFix };
