#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
模式学习脚本
功能：从代码库中学习成功模式
"""

import argparse
import sys
import json
import re
import os
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Tuple, Set
from collections import defaultdict
from dataclasses import dataclass, field


def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(
        description='模式学习脚本 - 从代码库中学习成功模式'
    )
    parser.add_argument(
        '--source',
        type=str,
        default='src',
        help='源代码目录（默认：src）'
    )
    parser.add_argument(
        '--output',
        type=str,
        default='learned-patterns',
        help='输出目录名称（默认：learned-patterns）'
    )
    parser.add_argument(
        '--language',
        type=str,
        default='auto',
        help='编程语言（默认：auto自动检测）'
    )
    parser.add_argument(
        '--min-frequency',
        type=int,
        default=3,
        help='最小出现频率（默认：3）'
    )
    parser.add_argument(
        '--pattern-types',
        type=str,
        nargs='+',
        default=['all'],
        choices=['all', 'naming', 'structure', 'error-handling', 'testing', 'api'],
        help='要学习的模式类型'
    )
    return parser.parse_args()


@dataclass
class Pattern:
    """模式数据类"""
    name: str
    pattern_type: str
    description: str
    examples: List[str] = field(default_factory=list)
    frequency: int = 0
    confidence: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)


class PatternLearner:
    """模式学习器"""
    
    def __init__(self, source_dir: str, min_frequency: int):
        """
        初始化学习器
        
        参数:
            source_dir: 源代码目录
            min_frequency: 最小出现频率
        """
        self.source_dir = Path(source_dir)
        self.min_frequency = min_frequency
        self.patterns: Dict[str, List[Pattern]] = defaultdict(list)
        self.file_count = 0
        self.total_lines = 0
    
    def learn_all(self) -> Dict[str, Any]:
        """
        学习所有模式
        
        返回:
            学习结果字典
        """
        if not self.source_dir.exists():
            print(f"源代码目录不存在: {self.source_dir}")
            return {}
        
        print(f"\n开始从 {self.source_dir} 学习模式...")
        
        files = self._collect_source_files()
        print(f"发现 {len(files)} 个源文件")
        
        for file_path in files:
            self._analyze_file(file_path)
        
        self._filter_and_rank_patterns()
        
        return self._generate_report()
    
    def _collect_source_files(self) -> List[Path]:
        """
        收集所有源文件
        
        返回:
            源文件路径列表
        """
        extensions = ['.py', '.js', '.ts', '.java', '.go', '.rs', '.rb', '.php']
        files = []
        
        for ext in extensions:
            files.extend(self.source_dir.glob(f'**/*{ext}'))
        
        return files
    
    def _analyze_file(self, file_path: Path):
        """
        分析单个文件
        
        参数:
            file_path: 文件路径
        """
        try:
            content = file_path.read_text(encoding='utf-8')
            lines = content.splitlines()
            
            self.file_count += 1
            self.total_lines += len(lines)
            
            self._learn_naming_patterns(file_path, content)
            self._learn_structure_patterns(file_path, content)
            self._learn_error_handling_patterns(file_path, content)
            self._learn_testing_patterns(file_path, content)
            self._learn_api_patterns(file_path, content)
            
        except Exception as e:
            print(f"分析文件失败 {file_path}: {e}")
    
    def _learn_naming_patterns(self, file_path: Path, content: str):
        """学习命名模式"""
        naming_patterns = []
        
        class_pattern = r'class\s+([A-Z][a-zA-Z0-9]*)'
        classes = re.findall(class_pattern, content)
        for cls in classes:
            if cls:
                naming_patterns.append(('class', cls))
        
        func_pattern = r'def\s+([a-z_][a-z0-9_]*)'
        functions = re.findall(func_pattern, content)
        for func in functions:
            if func:
                naming_patterns.append(('function', func))
        
        const_pattern = r'([A-Z][A-Z0-9_]*)\s*='
        constants = re.findall(const_pattern, content)
        for const in constants:
            if len(const) > 2:
                naming_patterns.append(('constant', const))
        
        pattern_counts = defaultdict(int)
        for ptype, name in naming_patterns:
            pattern_counts[(ptype, name)] += 1
        
        for (ptype, name), count in pattern_counts.items():
            if count >= self.min_frequency:
                pattern = Pattern(
                    name=f"{ptype}_naming_{name}",
                    pattern_type='naming',
                    description=f"{ptype}命名模式: {name}",
                    frequency=count,
                    confidence=min(count / 10, 1.0)
                )
                self.patterns['naming'].append(pattern)
    
    def _learn_structure_patterns(self, file_path: Path, content: str):
        """学习结构模式"""
        lines = content.splitlines()
        
        imports = []
        for line in lines:
            if line.strip().startswith('import ') or line.strip().startswith('from '):
                imports.append(line.strip())
        
        if imports:
            import_pattern = Pattern(
                name='import_organization',
                pattern_type='structure',
                description='导入语句组织模式',
                examples=imports[:5],
                frequency=len(imports),
                confidence=0.8
            )
            self.patterns['structure'].append(import_pattern)
        
        docstring_pattern = r'"""[\s\S]*?"""|\'\'\'[\s\S]*?\'\'\''
        docstrings = re.findall(docstring_pattern, content)
        if len(docstrings) >= 1:
            pattern = Pattern(
                name='docstring_usage',
                pattern_type='structure',
                description='文档字符串使用模式',
                frequency=len(docstrings),
                confidence=min(len(docstrings) / 5, 1.0)
            )
            self.patterns['structure'].append(pattern)
        
        class_defs = len(re.findall(r'class\s+\w+', content))
        if class_defs > 0:
            avg_methods = content.count('def ') / max(class_defs, 1)
            pattern = Pattern(
                name='class_size',
                pattern_type='structure',
                description=f'类平均方法数: {avg_methods:.1f}',
                frequency=class_defs,
                confidence=0.7,
                metadata={'avg_methods_per_class': avg_methods}
            )
            self.patterns['structure'].append(pattern)
    
    def _learn_error_handling_patterns(self, file_path: Path, content: str):
        """学习错误处理模式"""
        try_blocks = re.findall(r'try\s*:', content)
        except_blocks = re.findall(r'except\s+(\w+)', content)
        raise_statements = re.findall(r'raise\s+(\w+)', content)
        
        if try_blocks:
            pattern = Pattern(
                name='try_except_usage',
                pattern_type='error-handling',
                description='try-except错误处理模式',
                frequency=len(try_blocks),
                confidence=0.9
            )
            self.patterns['error-handling'].append(pattern)
        
        exception_types = defaultdict(int)
        for exc in except_blocks:
            exception_types[exc] += 1
        
        for exc_type, count in exception_types.items():
            if count >= self.min_frequency:
                pattern = Pattern(
                    name=f'catch_{exc_type.lower()}',
                    pattern_type='error-handling',
                    description=f'捕获异常类型: {exc_type}',
                    frequency=count,
                    confidence=0.8
                )
                self.patterns['error-handling'].append(pattern)
        
        if raise_statements:
            pattern = Pattern(
                name='raise_usage',
                pattern_type='error-handling',
                description='主动抛出异常模式',
                frequency=len(raise_statements),
                confidence=0.85
            )
            self.patterns['error-handling'].append(pattern)
    
    def _learn_testing_patterns(self, file_path: Path, content: str):
        """学习测试模式"""
        if 'test' not in file_path.name.lower():
            return
        
        test_functions = re.findall(r'def\s+(test_\w+)', content)
        assertions = re.findall(r'assert\s+', content)
        
        if test_functions:
            pattern = Pattern(
                name='test_function_naming',
                pattern_type='testing',
                description='测试函数命名模式 (test_*)',
                examples=test_functions[:5],
                frequency=len(test_functions),
                confidence=0.95
            )
            self.patterns['testing'].append(pattern)
        
        if assertions:
            pattern = Pattern(
                name='assertion_usage',
                pattern_type='testing',
                description='断言使用模式',
                frequency=len(assertions),
                confidence=0.9
            )
            self.patterns['testing'].append(pattern)
        
        fixtures = re.findall(r'@pytest\.fixture', content)
        if fixtures:
            pattern = Pattern(
                name='fixture_usage',
                pattern_type='testing',
                description='pytest fixture使用模式',
                frequency=len(fixtures),
                confidence=0.9
            )
            self.patterns['testing'].append(pattern)
        
        mocks = re.findall(r'@patch|@mock|Mock\(', content, re.IGNORECASE)
        if mocks:
            pattern = Pattern(
                name='mocking_usage',
                pattern_type='testing',
                description='Mock使用模式',
                frequency=len(mocks),
                confidence=0.85
            )
            self.patterns['testing'].append(pattern)
    
    def _learn_api_patterns(self, file_path: Path, content: str):
        """学习API模式"""
        route_decorators = re.findall(r'@(?:app|router)\.(get|post|put|delete|patch)\s*\([\'"]([^\'"]+)[\'"]', content, re.IGNORECASE)
        
        if route_decorators:
            methods = defaultdict(int)
            for method, path in route_decorators:
                methods[method.lower()] += 1
            
            for method, count in methods.items():
                pattern = Pattern(
                    name=f'api_{method}_endpoint',
                    pattern_type='api',
                    description=f'API {method.upper()} 端点模式',
                    frequency=count,
                    confidence=0.9
                )
                self.patterns['api'].append(pattern)
        
        response_patterns = re.findall(r'JSONResponse|jsonify|json\.dumps', content)
        if response_patterns:
            pattern = Pattern(
                name='json_response',
                pattern_type='api',
                description='JSON响应模式',
                frequency=len(response_patterns),
                confidence=0.85
            )
            self.patterns['api'].append(pattern)
        
        auth_decorators = re.findall(r'@(?:login_required|auth|authenticate|jwt_required)', content, re.IGNORECASE)
        if auth_decorators:
            pattern = Pattern(
                name='authentication_decorator',
                pattern_type='api',
                description='认证装饰器模式',
                frequency=len(auth_decorators),
                confidence=0.9
            )
            self.patterns['api'].append(pattern)
    
    def _filter_and_rank_patterns(self):
        """过滤和排序模式"""
        for ptype in self.patterns:
            seen = set()
            unique_patterns = []
            for pattern in self.patterns[ptype]:
                if pattern.name not in seen:
                    seen.add(pattern.name)
                    unique_patterns.append(pattern)
            
            unique_patterns.sort(key=lambda p: p.frequency, reverse=True)
            self.patterns[ptype] = unique_patterns
    
    def _generate_report(self) -> Dict[str, Any]:
        """
        生成学习报告
        
        返回:
            报告字典
        """
        report = {
            'timestamp': datetime.now().isoformat(),
            'source_dir': str(self.source_dir),
            'statistics': {
                'files_analyzed': self.file_count,
                'total_lines': self.total_lines,
                'patterns_found': sum(len(p) for p in self.patterns.values())
            },
            'patterns': {}
        }
        
        for ptype, patterns in self.patterns.items():
            report['patterns'][ptype] = [
                {
                    'name': p.name,
                    'description': p.description,
                    'frequency': p.frequency,
                    'confidence': p.confidence,
                    'examples': p.examples[:3]
                }
                for p in patterns
            ]
        
        return report


def save_patterns(output_dir: str, report: Dict[str, Any]):
    """
    保存学习到的模式
    
    参数:
        output_dir: 输出目录
        report: 学习报告
    """
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    json_file = output_path / f'learned-patterns-{timestamp}.json'
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    print(f"\n模式已保存: {json_file}")
    
    md_file = output_path / f'learned-patterns-{timestamp}.md'
    md_content = generate_markdown_report(report)
    with open(md_file, 'w', encoding='utf-8') as f:
        f.write(md_content)
    print(f"Markdown报告已保存: {md_file}")


def generate_markdown_report(report: Dict[str, Any]) -> str:
    """
    生成Markdown格式报告
    
    参数:
        report: 学习报告
    
    返回:
        Markdown字符串
    """
    md = f"""# 模式学习报告

## 统计信息

- **分析文件数**: {report['statistics']['files_analyzed']}
- **总代码行数**: {report['statistics']['total_lines']}
- **发现模式数**: {report['statistics']['patterns_found']}
- **生成时间**: {report['timestamp']}

## 学习到的模式

"""
    
    for ptype, patterns in report['patterns'].items():
        if patterns:
            md += f"### {ptype.upper()} 模式\n\n"
            md += "| 模式名称 | 描述 | 频率 | 置信度 |\n"
            md += "|----------|------|------|--------|\n"
            
            for p in patterns:
                md += f"| {p['name']} | {p['description']} | {p['frequency']} | {p['confidence']:.2f} |\n"
            
            md += "\n"
    
    return md


def print_summary(report: Dict[str, Any]):
    """打印学习摘要"""
    print(f"\n{'='*60}")
    print("模式学习结果")
    print(f"{'='*60}")
    print(f"分析文件数: {report['statistics']['files_analyzed']}")
    print(f"总代码行数: {report['statistics']['total_lines']}")
    print(f"发现模式数: {report['statistics']['patterns_found']}")
    
    print("\n各类型模式数量:")
    for ptype, patterns in report['patterns'].items():
        if patterns:
            print(f"  {ptype}: {len(patterns)} 个")
    
    print(f"{'='*60}")


def main():
    """主函数"""
    args = parse_args()
    
    learner = PatternLearner(args.source, args.min_frequency)
    report = learner.learn_all()
    
    if report:
        save_patterns(args.output, report)
        print_summary(report)
    
    sys.exit(0)


if __name__ == '__main__':
    main()
