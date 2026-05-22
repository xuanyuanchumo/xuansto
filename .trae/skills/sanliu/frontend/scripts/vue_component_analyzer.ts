import * as fs from 'fs';
import * as path from 'path';

interface ComponentAnalysis {
  name: string;
  path: string;
  size: number;
  props: string[];
  emits: string[];
  computedProperties: string[];
  methods: string[];
  watchers: string[];
  lifecycleHooks: string[];
  templateComplexity: number;
  dependencies: string[];
  issues: string[];
  recommendations: string[];
}

interface PerformanceIssue {
  type: 'warning' | 'error' | 'info';
  message: string;
  line?: number;
  suggestion: string;
}

class VueComponentAnalyzer {
  private componentsDir: string;
  private outputDir: string;
  private analysisResults: ComponentAnalysis[] = [];

  constructor(componentsDir: string, outputDir: string) {
    this.componentsDir = componentsDir;
    this.outputDir = outputDir;
    this.ensureOutputDir();
  }

  private ensureOutputDir(): void {
    if (!fs.existsSync(this.outputDir)) {
      fs.mkdirSync(this.outputDir, { recursive: true });
    }
  }

  public async analyze(): Promise<ComponentAnalysis[]> {
    console.log('开始分析Vue组件性能...');
    
    const componentFiles = this.findVueFiles(this.componentsDir);
    console.log(`找到 ${componentFiles.length} 个Vue组件文件`);

    for (const file of componentFiles) {
      try {
        const analysis = await this.analyzeComponent(file);
        this.analysisResults.push(analysis);
      } catch (error) {
        console.error(`分析组件 ${file} 时出错:`, error);
      }
    }

    this.generateReport();
    return this.analysisResults;
  }

  private findVueFiles(dir: string): string[] {
    const files: string[] = [];
    
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

  private async analyzeComponent(filePath: string): Promise<ComponentAnalysis> {
    const content = fs.readFileSync(filePath, 'utf-8');
    const relativePath = path.relative(this.componentsDir, filePath);
    const componentName = path.basename(filePath, '.vue');

    const analysis: ComponentAnalysis = {
      name: componentName,
      path: relativePath,
      size: content.length,
      props: this.extractProps(content),
      emits: this.extractEmits(content),
      computedProperties: this.extractComputed(content),
      methods: this.extractMethods(content),
      watchers: this.extractWatchers(content),
      lifecycleHooks: this.extractLifecycleHooks(content),
      templateComplexity: this.calculateTemplateComplexity(content),
      dependencies: this.extractDependencies(content),
      issues: [],
      recommendations: []
    };

    this.detectPerformanceIssues(content, analysis);
    this.generateRecommendations(analysis);

    return analysis;
  }

  private extractProps(content: string): string[] {
    const props: string[] = [];
    const propsMatch = content.match(/defineProps<[^>]*>/);
    if (propsMatch) {
      const propsContent = propsMatch[0];
      const propNames = propsContent.match(/\w+\s*:/g);
      if (propNames) {
        props.push(...propNames.map(p => p.replace(':', '').trim()));
      }
    }
    
    const propsArrayMatch = content.match(/props\s*:\s*\{([^}]*)\}/);
    if (propsArrayMatch) {
      const propNames = propsArrayMatch[1].match(/\w+\s*:/g);
      if (propNames) {
        props.push(...propNames.map(p => p.replace(':', '').trim()));
      }
    }
    
    return [...new Set(props)];
  }

  private extractEmits(content: string): string[] {
    const emits: string[] = [];
    const emitsMatch = content.match(/defineEmits<[^>]*>/);
    if (emitsMatch) {
      const emitsContent = emitsMatch[0];
      const emitNames = emitsContent.match(/"\w+"/g);
      if (emitNames) {
        emits.push(...emitNames.map(e => e.replace(/"/g, '')));
      }
    }
    
    const emitsArrayMatch = content.match(/emits\s*:\s*\[([^\]]*)\]/);
    if (emitsArrayMatch) {
      const emitNames = emitsArrayMatch[1].match(/'[^']+'/g);
      if (emitNames) {
        emits.push(...emitNames.map(e => e.replace(/'/g, '')));
      }
    }
    
    return [...new Set(emits)];
  }

  private extractComputed(content: string): string[] {
    const computed: string[] = [];
    const computedMatch = content.match(/computed\s*:\s*\{([^}]*?)\n\s*\}/s);
    if (computedMatch) {
      const computedNames = computedMatch[1].match(/^\s*(\w+)\s*\(/gm);
      if (computedNames) {
        computed.push(...computedNames.map(c => c.trim().replace('(', '')));
      }
    }
    
    const computedRefMatch = content.matchAll(/const\s+(\w+)\s*=\s*computed\(/g);
    for (const match of computedRefMatch) {
      computed.push(match[1]);
    }
    
    return [...new Set(computed)];
  }

  private extractMethods(content: string): string[] {
    const methods: string[] = [];
    
    const methodsMatch = content.match(/methods\s*:\s*\{([^}]*?)\n\s*\}/s);
    if (methodsMatch) {
      const methodNames = methodsMatch[1].match(/^\s*(\w+)\s*\(/gm);
      if (methodNames) {
        methods.push(...methodNames.map(m => m.trim().replace('(', '')));
      }
    }
    
    const functionMatch = content.matchAll(/(?:const|function)\s+(\w+)\s*[=\(]/g);
    for (const match of functionMatch) {
      if (!['computed', 'ref', 'reactive', 'watch', 'watchEffect'].includes(match[1])) {
        methods.push(match[1]);
      }
    }
    
    return [...new Set(methods)];
  }

  private extractWatchers(content: string): string[] {
    const watchers: string[] = [];
    
    const watchMatch = content.match(/watch\s*:\s*\{([^}]*?)\n\s*\}/s);
    if (watchMatch) {
      const watchNames = watchMatch[1].match(/^\s*(\w+)\s*:/gm);
      if (watchNames) {
        watchers.push(...watchNames.map(w => w.trim().replace(':', '')));
      }
    }
    
    const watchFunctionMatch = content.matchAll(/watch\(\s*['"`]?(\w+)['"`]?/g);
    for (const match of watchFunctionMatch) {
      watchers.push(match[1]);
    }
    
    const watchEffectMatch = content.matchAll(/watchEffect\(/g);
    let count = 1;
    for (const _ of watchEffectMatch) {
      watchers.push(`watchEffect_${count++}`);
    }
    
    return [...new Set(watchers)];
  }

  private extractLifecycleHooks(content: string): string[] {
    const hooks: string[] = [];
    const hookPatterns = [
      'onMounted', 'onUpdated', 'onUnmounted', 'onBeforeMount', 
      'onBeforeUpdate', 'onBeforeUnmount', 'onActivated', 
      'onDeactivated', 'onErrorCaptured'
    ];
    
    for (const hook of hookPatterns) {
      const regex = new RegExp(`${hook}\\s*\\(`, 'g');
      if (regex.test(content)) {
        hooks.push(hook);
      }
    }
    
    const optionsApiHooks = [
      'mounted', 'updated', 'unmounted', 'beforeMount', 
      'beforeUpdate', 'beforeUnmount', 'activated', 
      'deactivated', 'errorCaptured'
    ];
    
    for (const hook of optionsApiHooks) {
      const regex = new RegExp(`${hook}\\s*:\\s*(?:async\\s*)?function|${hook}\\s*\\(`, 'g');
      if (regex.test(content)) {
        hooks.push(hook);
      }
    }
    
    return [...new Set(hooks)];
  }

  private calculateTemplateComplexity(content: string): number {
    const templateMatch = content.match(/<template>([\s\S]*?)<\/template>/);
    if (!templateMatch) return 0;
    
    const template = templateMatch[1];
    let complexity = 0;
    
    complexity += (template.match(/v-for/g) || []).length * 3;
    complexity += (template.match(/v-if/g) || []).length * 2;
    complexity += (template.match(/v-else-if/g) || []).length * 2;
    complexity += (template.match(/v-show/g) || []).length * 1;
    complexity += (template.match(/@click|@input|@change/g) || []).length * 1;
    complexity += (template.match(/:/g) || []).length * 0.5;
    
    return Math.round(complexity);
  }

  private extractDependencies(content: string): string[] {
    const dependencies: string[] = [];
    
    const importMatch = content.matchAll(/import\s+.*?from\s+['"`]([^'"`]+)['"`]/g);
    for (const match of importMatch) {
      dependencies.push(match[1]);
    }
    
    return [...new Set(dependencies)];
  }

  private detectPerformanceIssues(content: string, analysis: ComponentAnalysis): void {
    if (analysis.templateComplexity > 50) {
      analysis.issues.push(`模板复杂度过高 (${analysis.templateComplexity})，建议拆分组件`);
    }
    
    if (analysis.computedProperties.length > 10) {
      analysis.issues.push(`计算属性过多 (${analysis.computedProperties.length})，考虑优化数据结构`);
    }
    
    if (analysis.watchers.length > 5) {
      analysis.issues.push(`侦听器过多 (${analysis.watchers.length})，可能导致性能问题`);
    }
    
    if (analysis.methods.length > 20) {
      analysis.issues.push(`方法过多 (${analysis.methods.length})，考虑拆分组件或使用组合式函数`);
    }
    
    if (content.includes('v-for') && !content.includes(':key')) {
      analysis.issues.push('v-for 缺少 :key 属性，可能影响渲染性能');
    }
    
    if (content.includes('v-for') && content.includes('v-if') && 
        content.indexOf('v-for') < content.indexOf('v-if')) {
      analysis.issues.push('v-for 和 v-if 不应同时使用在同一元素上');
    }
    
    if (content.length > 50000) {
      analysis.issues.push(`组件文件过大 (${Math.round(content.length / 1024)}KB)，建议拆分`);
    }
    
    const deepWatchMatch = content.match(/deep\s*:\s*true/g);
    if (deepWatchMatch && deepWatchMatch.length > 3) {
      analysis.issues.push('过多深度侦听器 (deep: true)，可能影响性能');
    }
    
    if (content.includes('this.$forceUpdate()')) {
      analysis.issues.push('使用了 $forceUpdate()，建议优化数据响应式设计');
    }
    
    if (content.includes('v-html') && !content.includes('DOMPurify')) {
      analysis.issues.push('使用 v-html 存在XSS风险，建议使用 DOMPurify 进行清理');
    }
  }

  private generateRecommendations(analysis: ComponentAnalysis): void {
    if (analysis.templateComplexity > 30) {
      analysis.recommendations.push('考虑将复杂模板拆分为多个子组件');
    }
    
    if (analysis.watchers.length > 3) {
      analysis.recommendations.push('使用 computed 替代部分 watcher，或考虑使用 watchEffect');
    }
    
    if (analysis.methods.length > 15) {
      analysis.recommendations.push('将相关方法提取到 composables 中');
    }
    
    if (analysis.dependencies.length > 10) {
      analysis.recommendations.push('考虑减少外部依赖，优化导入策略');
    }
    
    if (analysis.lifecycleHooks.length > 4) {
      analysis.recommendations.push('简化生命周期逻辑，考虑使用组合式 API');
    }
    
    if (analysis.props.length > 10) {
      analysis.recommendations.push('Props 过多，考虑使用对象形式或拆分组件');
    }
    
    if (analysis.size > 30000) {
      analysis.recommendations.push('组件体积较大，考虑异步加载或代码分割');
    }
    
    analysis.recommendations.push('为组件添加性能监控点');
    analysis.recommendations.push('确保使用生产模式构建以获得更好的性能');
  }

  private generateReport(): void {
    const report = {
      timestamp: new Date().toISOString(),
      totalComponents: this.analysisResults.length,
      averageComplexity: this.calculateAverageComplexity(),
      highComplexityComponents: this.getHighComplexityComponents(),
      commonIssues: this.getCommonIssues(),
      recommendations: this.getOverallRecommendations(),
      components: this.analysisResults
    };

    const reportPath = path.join(this.outputDir, 'component-analysis-report.json');
    fs.writeFileSync(reportPath, JSON.stringify(report, null, 2), 'utf-8');
    console.log(`分析报告已生成: ${reportPath}`);

    const summaryPath = path.join(this.outputDir, 'component-analysis-summary.txt');
    this.generateSummaryReport(summaryPath);
  }

  private calculateAverageComplexity(): number {
    if (this.analysisResults.length === 0) return 0;
    const total = this.analysisResults.reduce((sum, c) => sum + c.templateComplexity, 0);
    return Math.round(total / this.analysisResults.length);
  }

  private getHighComplexityComponents(): ComponentAnalysis[] {
    return this.analysisResults
      .filter(c => c.templateComplexity > 30 || c.issues.length > 3)
      .sort((a, b) => b.templateComplexity - a.templateComplexity);
  }

  private getCommonIssues(): { issue: string; count: number }[] {
    const issueMap = new Map<string, number>();
    
    for (const component of this.analysisResults) {
      for (const issue of component.issues) {
        const normalizedIssue = issue.replace(/\d+/g, 'N');
        issueMap.set(normalizedIssue, (issueMap.get(normalizedIssue) || 0) + 1);
      }
    }
    
    return Array.from(issueMap.entries())
      .map(([issue, count]) => ({ issue, count }))
      .sort((a, b) => b.count - a.count)
      .slice(0, 10);
  }

  private getOverallRecommendations(): string[] {
    const recommendations = new Set<string>();
    
    for (const component of this.analysisResults) {
      component.recommendations.forEach(r => recommendations.add(r));
    }
    
    return Array.from(recommendations);
  }

  private generateSummaryReport(outputPath: string): void {
    const lines: string[] = [
      '='.repeat(60),
      'Vue 组件性能分析报告',
      '='.repeat(60),
      `生成时间: ${new Date().toLocaleString('zh-CN')}`,
      `分析组件总数: ${this.analysisResults.length}`,
      `平均模板复杂度: ${this.calculateAverageComplexity()}`,
      '',
      '-'.repeat(60),
      '高复杂度组件 (需要重点关注)',
      '-'.repeat(60),
    ];

    const highComplexity = this.getHighComplexityComponents();
    for (const comp of highComplexity.slice(0, 10)) {
      lines.push(`\n组件: ${comp.name}`);
      lines.push(`  路径: ${comp.path}`);
      lines.push(`  模板复杂度: ${comp.templateComplexity}`);
      lines.push(`  问题数量: ${comp.issues.length}`);
      if (comp.issues.length > 0) {
        lines.push(`  主要问题:`);
        comp.issues.slice(0, 3).forEach(issue => {
          lines.push(`    - ${issue}`);
        });
      }
    }

    lines.push('', '-'.repeat(60), '常见问题统计', '-'.repeat(60));
    const commonIssues = this.getCommonIssues();
    for (const { issue, count } of commonIssues) {
      lines.push(`  [${count}次] ${issue}`);
    }

    lines.push('', '-'.repeat(60), '优化建议', '-'.repeat(60));
    const recommendations = this.getOverallRecommendations();
    recommendations.slice(0, 10).forEach((rec, idx) => {
      lines.push(`${idx + 1}. ${rec}`);
    });

    lines.push('', '='.repeat(60), '分析完成', '='.repeat(60));

    fs.writeFileSync(outputPath, lines.join('\n'), 'utf-8');
    console.log(`摘要报告已生成: ${outputPath}`);
  }
}

async function main() {
  const projectRoot = path.resolve(__dirname, '..');
  const componentsDir = path.join(projectRoot, 'src', 'components');
  const outputDir = path.join(projectRoot, 'analysis-reports');

  const analyzer = new VueComponentAnalyzer(componentsDir, outputDir);
  await analyzer.analyze();
  
  console.log('\n组件分析完成！');
}

main().catch(console.error);

export { VueComponentAnalyzer, ComponentAnalysis };
