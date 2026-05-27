#!/usr/bin/env node
/**
 * 设计令牌同步脚本
 * 功能：同步设计令牌到CSS变量
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
        input: 'design-tokens.json',
        output: 'tokens.css',
        format: 'css',
        prefix: '--',
        selector: ':root'
    };
    
    for (let i = 0; i < args.length; i++) {
        switch (args[i]) {
            case '--input':
                params.input = args[++i];
                break;
            case '--output':
                params.output = args[++i];
                break;
            case '--format':
                params.format = args[++i];
                break;
            case '--prefix':
                params.prefix = args[++i];
                break;
            case '--selector':
                params.selector = args[++i];
                break;
            case '--help':
                console.log(`
设计令牌同步脚本

用法: node design-tokens-sync.js [选项]

选项:
  --input <file>      输入文件路径 (默认: design-tokens.json)
  --output <file>     输出文件路径 (默认: tokens.css)
  --format <format>   输出格式: css, scss, less (默认: css)
  --prefix <prefix>   变量前缀 (默认: --)
  --selector <sel>    CSS选择器 (默认: :root)
  --help              显示帮助信息
                `);
                process.exit(0);
        }
    }
    
    return params;
}

/**
 * 设计令牌同步器
 */
class DesignTokensSync {
    /**
     * @param {Object} options 配置选项
     */
    constructor(options) {
        this.options = options;
        this.tokens = null;
        this.variables = [];
        this.warnings = [];
    }
    
    /**
     * 加载设计令牌
     * @returns {boolean} 是否成功
     */
    loadTokens() {
        const inputPath = path.resolve(this.options.input);
        
        if (!fs.existsSync(inputPath)) {
            console.error(`输入文件不存在: ${inputPath}`);
            return false;
        }
        
        try {
            const content = fs.readFileSync(inputPath, 'utf8');
            this.tokens = JSON.parse(content);
            console.log(`成功加载设计令牌: ${inputPath}`);
            return true;
        } catch (e) {
            console.error(`解析设计令牌失败: ${e.message}`);
            return false;
        }
    }
    
    /**
     * 处理令牌
     */
    processTokens() {
        this.variables = [];
        this.warnings = [];
        
        if (!this.tokens) {
            console.error('没有可处理的令牌');
            return;
        }
        
        this._processTokenObject(this.tokens, '');
        
        console.log(`处理完成，生成 ${this.variables.length} 个变量`);
        
        if (this.warnings.length > 0) {
            console.log(`警告: ${this.warnings.length} 个`);
            this.warnings.forEach(w => console.log(`  ⚠️ ${w}`));
        }
    }
    
    /**
     * 递归处理令牌对象
     * @param {Object} obj 令牌对象
     * @param {string} prefix 当前前缀
     */
    _processTokenObject(obj, prefix) {
        for (const [key, value] of Object.entries(obj)) {
            const varName = prefix ? `${prefix}-${this._toKebabCase(key)}` : this._toKebabCase(key);
            
            if (value === null || value === undefined) {
                this.warnings.push(`令牌值为空: ${varName}`);
                continue;
            }
            
            if (typeof value === 'object' && !Array.isArray(value)) {
                // 检查是否是标准令牌格式
                if (value.hasOwnProperty('value')) {
                    this.variables.push({
                        name: varName,
                        value: this._processValue(value.value),
                        type: value.type || 'unknown',
                        description: value.description || ''
                    });
                } else {
                    // 递归处理嵌套对象
                    this._processTokenObject(value, varName);
                }
            } else {
                // 简单值
                this.variables.push({
                    name: varName,
                    value: this._processValue(value),
                    type: this._inferType(value),
                    description: ''
                });
            }
        }
    }
    
    /**
     * 转换为kebab-case
     * @param {string} str 输入字符串
     * @returns {string} kebab-case字符串
     */
    _toKebabCase(str) {
        return str
            .replace(/([a-z])([A-Z])/g, '$1-$2')
            .replace(/[\s_]+/g, '-')
            .toLowerCase();
    }
    
    /**
     * 处理令牌值
     * @param {*} value 原始值
     * @returns {string} 处理后的值
     */
    _processValue(value) {
        if (typeof value === 'string') {
            // 处理引用 {colors.primary}
            if (value.startsWith('{') && value.endsWith('}')) {
                const ref = value.slice(1, -1);
                return `var(${this.options.prefix}${this._toKebabCase(ref.replace(/\./g, '-'))})`;
            }
            return value;
        }
        
        if (typeof value === 'number') {
            return String(value);
        }
        
        if (Array.isArray(value)) {
            return value.join(', ');
        }
        
        return String(value);
    }
    
    /**
     * 推断类型
     * @param {*} value 值
     * @returns {string} 类型
     */
    _inferType(value) {
        if (typeof value === 'number') return 'number';
        if (typeof value === 'string') {
            if (value.startsWith('#') || value.startsWith('rgb') || value.startsWith('hsl')) {
                return 'color';
            }
            if (value.endsWith('px') || value.endsWith('em') || value.endsWith('rem') || value.endsWith('%')) {
                return 'dimension';
            }
            return 'string';
        }
        return 'unknown';
    }
    
    /**
     * 生成CSS输出
     * @returns {string} CSS内容
     */
    generateCss() {
        const lines = [];
        lines.push('/**');
        lines.push(' * 设计令牌 - 自动生成');
        lines.push(` * 生成时间: ${new Date().toISOString()}`);
        lines.push(` * 变量数量: ${this.variables.length}`);
        lines.push(' */');
        lines.push('');
        lines.push(`${this.options.selector} {`);
        
        // 按类型分组
        const grouped = this._groupByType();
        
        for (const [type, vars] of Object.entries(grouped)) {
            lines.push(`  /* ${this._getTypeLabel(type)} */`);
            for (const v of vars) {
                const comment = v.description ? ` /* ${v.description} */` : '';
                lines.push(`  ${this.options.prefix}${v.name}: ${v.value};${comment}`);
            }
            lines.push('');
        }
        
        lines.push('}');
        
        return lines.join('\n');
    }
    
    /**
     * 生成SCSS输出
     * @returns {string} SCSS内容
     */
    generateScss() {
        const lines = [];
        lines.push('// 设计令牌 - 自动生成');
        lines.push(`// 生成时间: ${new Date().toISOString()}`);
        lines.push(`// 变量数量: ${this.variables.length}`);
        lines.push('');
        
        const grouped = this._groupByType();
        
        for (const [type, vars] of Object.entries(grouped)) {
            lines.push(`// ${this._getTypeLabel(type)}`);
            for (const v of vars) {
                const comment = v.description ? ` // ${v.description}` : '';
                lines.push(`$${v.name}: ${v.value};${comment}`);
            }
            lines.push('');
        }
        
        // 生成CSS变量映射
        lines.push('// CSS变量映射');
        lines.push(':root {');
        for (const v of this.variables) {
            lines.push(`  ${this.options.prefix}${v.name}: $#${v.name};`);
        }
        lines.push('}');
        
        return lines.join('\n');
    }
    
    /**
     * 生成Less输出
     * @returns {string} Less内容
     */
    generateLess() {
        const lines = [];
        lines.push('// 设计令牌 - 自动生成');
        lines.push(`// 生成时间: ${new Date().toISOString()}`);
        lines.push(`// 变量数量: ${this.variables.length}`);
        lines.push('');
        
        const grouped = this._groupByType();
        
        for (const [type, vars] of Object.entries(grouped)) {
            lines.push(`// ${this._getTypeLabel(type)}`);
            for (const v of vars) {
                const comment = v.description ? ` // ${v.description}` : '';
                lines.push(`@${v.name}: ${v.value};${comment}`);
            }
            lines.push('');
        }
        
        return lines.join('\n');
    }
    
    /**
     * 按类型分组
     * @returns {Object} 分组后的变量
     */
    _groupByType() {
        const grouped = {};
        
        for (const v of this.variables) {
            if (!grouped[v.type]) {
                grouped[v.type] = [];
            }
            grouped[v.type].push(v);
        }
        
        return grouped;
    }
    
    /**
     * 获取类型标签
     * @param {string} type 类型
     * @returns {string} 标签
     */
    _getTypeLabel(type) {
        const labels = {
            'color': '颜色',
            'dimension': '尺寸',
            'number': '数值',
            'string': '字符串',
            'fontFamily': '字体',
            'fontWeight': '字重',
            'lineHeight': '行高',
            'borderRadius': '圆角',
            'shadow': '阴影',
            'spacing': '间距',
            'unknown': '其他'
        };
        return labels[type] || type;
    }
    
    /**
     * 保存输出
     */
    saveOutput() {
        let content;
        
        switch (this.options.format) {
            case 'scss':
                content = this.generateScss();
                break;
            case 'less':
                content = this.generateLess();
                break;
            default:
                content = this.generateCss();
        }
        
        const outputPath = path.resolve(this.options.output);
        const outputDir = path.dirname(outputPath);
        
        if (!fs.existsSync(outputDir)) {
            fs.mkdirSync(outputDir, { recursive: true });
        }
        
        fs.writeFileSync(outputPath, content, 'utf8');
        console.log(`\n输出已保存: ${outputPath}`);
    }
}

/**
 * 创建示例设计令牌文件
 * @param {string} filePath 文件路径
 */
function createExampleTokens(filePath) {
    const exampleTokens = {
        colors: {
            primary: {
                value: '#007bff',
                type: 'color',
                description: '主色调'
            },
            secondary: {
                value: '#6c757d',
                type: 'color',
                description: '次要色调'
            },
            success: {
                value: '#28a745',
                type: 'color'
            },
            warning: {
                value: '#ffc107',
                type: 'color'
            },
            danger: {
                value: '#dc3545',
                type: 'color'
            },
            text: {
                primary: {
                    value: '#212529',
                    type: 'color'
                },
                secondary: {
                    value: '#6c757d',
                    type: 'color'
                }
            },
            background: {
                value: '#ffffff',
                type: 'color'
            }
        },
        spacing: {
            xs: { value: '4px', type: 'dimension' },
            sm: { value: '8px', type: 'dimension' },
            md: { value: '16px', type: 'dimension' },
            lg: { value: '24px', type: 'dimension' },
            xl: { value: '32px', type: 'dimension' }
        },
        borderRadius: {
            sm: { value: '4px', type: 'dimension' },
            md: { value: '8px', type: 'dimension' },
            lg: { value: '16px', type: 'dimension' },
            full: { value: '9999px', type: 'dimension' }
        },
        fontSize: {
            xs: { value: '12px', type: 'dimension' },
            sm: { value: '14px', type: 'dimension' },
            base: { value: '16px', type: 'dimension' },
            lg: { value: '18px', type: 'dimension' },
            xl: { value: '20px', type: 'dimension' },
            '2xl': { value: '24px', type: 'dimension' }
        },
        fontWeight: {
            normal: { value: '400', type: 'fontWeight' },
            medium: { value: '500', type: 'fontWeight' },
            bold: { value: '700', type: 'fontWeight' }
        },
        lineHeight: {
            tight: { value: '1.25', type: 'lineHeight' },
            normal: { value: '1.5', type: 'lineHeight' },
            relaxed: { value: '1.75', type: 'lineHeight' }
        },
        shadows: {
            sm: { value: '0 1px 2px rgba(0, 0, 0, 0.05)', type: 'shadow' },
            md: { value: '0 4px 6px rgba(0, 0, 0, 0.1)', type: 'shadow' },
            lg: { value: '0 10px 15px rgba(0, 0, 0, 0.1)', type: 'shadow' }
        },
        transitions: {
            fast: { value: '150ms', type: 'duration' },
            normal: { value: '300ms', type: 'duration' },
            slow: { value: '500ms', type: 'duration' }
        }
    };
    
    fs.writeFileSync(filePath, JSON.stringify(exampleTokens, null, 2), 'utf8');
    console.log(`示例令牌文件已创建: ${filePath}`);
}

/**
 * 主函数
 */
function main() {
    const args = parseArgs();
    
    // 如果输入文件不存在，创建示例
    if (!fs.existsSync(args.input)) {
        console.log(`输入文件不存在，创建示例文件...`);
        createExampleTokens(args.input);
    }
    
    const sync = new DesignTokensSync(args);
    
    if (!sync.loadTokens()) {
        process.exit(1);
    }
    
    sync.processTokens();
    sync.saveOutput();
    
    console.log('\n设计令牌同步完成！');
}

main();
