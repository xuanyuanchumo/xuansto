#!/usr/bin/env python3
"""
模式学习脚本
功能：从代码库中学习成功模式
"""

import argparse
import sys
import json
import re
import os
import ast
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
        choices=['all', 'naming', 'structure', 'error-handling', 'testing', 'api', 'react-component', 'api-route', 'test-pattern'],
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

    def __init__(self, source_dir: str, min_frequency: int, pattern_types: List[str] = None):
        self.source_dir = Path(source_dir)
        self.min_frequency = min_frequency
        self.pattern_types = pattern_types or ['all']
        self.patterns: Dict[str, List[Pattern]] = defaultdict(list)
        self._naming_accumulator: Dict[Tuple[str, str], Set[str]] = defaultdict(set)
        self._ts_js_naming_accumulator: Dict[Tuple[str, str], Set[str]] = defaultdict(set)
        self.file_count = 0
        self.total_lines = 0
        self.ts_js_extensions = {'.ts', '.tsx', '.js', '.jsx'}
        self.ts_js_patterns = {
            'function_decl': re.compile(r'function\s+(\w+)'),
            'const_func': re.compile(r'const\s+(\w+)\s*=\s*\('),
            'const_async_func': re.compile(r'const\s+(\w+)\s*=\s*(?:async\s+)?\('),
            'arrow_func': re.compile(r'const\s+(\w+)\s*=\s*(?:async\s+)?(?:\([^)]*\)|[\w]+)\s*=>'),
            'interface_decl': re.compile(r'interface\s+(\w+)'),
            'type_decl': re.compile(r'type\s+(\w+)\s*='),
            'class_decl': re.compile(r'class\s+(\w+)'),
            'export_pattern': re.compile(r'export\s+(?:default\s+)?(?:class|function|const|interface|type)\s+(\w+)'),
            'try_catch': re.compile(r'try\s*\{'),
            'async_function': re.compile(r'async\s+function\s+(\w+)'),
            'await_usage': re.compile(r'await\s+'),
            'react_component': re.compile(r'(?:function|const)\s+(\w+)\s*[=(].*?(?:React\.FC|JSX\.Element|ReactNode)'),
            'express_route': re.compile(r'app\.(get|post|put|delete|patch)\s*\(\s*[\'"]([^\'"]+)[\'"]'),
            'jest_test': re.compile(r'(?:describe|it|test|beforeEach|afterEach)\s*\(\s*[\'"]([^\'"]+)[\'"]'),
        }

    def learn_all(self) -> Dict[str, Any]:
        if not self.source_dir.exists():
            print(f"源代码目录不存在: {self.source_dir}")
            return {}

        print(f"\n开始从 {self.source_dir} 学习模式...")

        files = self._collect_source_files()
        print(f"发现 {len(files)} 个源文件")

        for file_path in files:
            self._analyze_file(file_path)

        self._finalize_naming_patterns()
        self._filter_and_rank_patterns()

        return self._generate_report()

    def _should_learn(self, pattern_type: str) -> bool:
        if 'all' in self.pattern_types:
            return True
        return pattern_type in self.pattern_types

    def _collect_source_files(self) -> List[Path]:
        """
        收集所有源文件

        返回:
            源文件路径列表
        """
        extensions = ['.py', '.js', '.jsx', '.ts', '.tsx', '.java', '.go', '.rs', '.rb', '.php']
        files = []

        for ext in extensions:
            files.extend(self.source_dir.glob(f'**/*{ext}'))

        return files

    def _analyze_file(self, file_path: Path):
        try:
            content = file_path.read_text(encoding='utf-8')
            lines = content.splitlines()

            self.file_count += 1
            self.total_lines += len(lines)

            if file_path.suffix in self.ts_js_extensions:
                self._extract_ts_js_patterns(file_path, content)
            else:
                if self._should_learn('naming'):
                    self._learn_naming_patterns(file_path, content)
                if self._should_learn('structure'):
                    self._learn_structure_patterns(file_path, content)
                if self._should_learn('error-handling'):
                    self._learn_error_handling_patterns(file_path, content)
                if self._should_learn('testing'):
                    self._learn_testing_patterns(file_path, content)
                if self._should_learn('api'):
                    self._learn_api_patterns(file_path, content)

        except Exception as e:
            print(f"分析文件失败 {file_path}: {e}")

    def _learn_naming_patterns(self, file_path: Path, content: str):
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

        file_key = str(file_path)
        for ptype, name in naming_patterns:
            self._naming_accumulator[(ptype, name)].add(file_key)

    def _learn_structure_patterns(self, file_path: Path, content: str):
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
            try:
                tree = ast.parse(content)
                class_method_counts = []
                for node in ast.walk(tree):
                    if isinstance(node, ast.ClassDef):
                        method_count = sum(
                            1 for item in node.body
                            if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef))
                        )
                        class_method_counts.append(method_count)
                if class_method_counts:
                    avg_methods = sum(class_method_counts) / len(class_method_counts)
                else:
                    avg_methods = 0.0
            except SyntaxError:
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

    def _extract_ts_js_patterns(self, file_path: Path, content: str):
        if self._should_learn('naming'):
            self._learn_ts_js_naming_patterns(file_path, content)
        if self._should_learn('structure'):
            self._learn_ts_js_structure_patterns(content)
        if self._should_learn('error-handling'):
            self._learn_ts_js_error_handling_patterns(content)
        if self._should_learn('testing'):
            self._learn_ts_js_testing_patterns(file_path, content)
        if self._should_learn('api'):
            self._learn_ts_js_api_patterns(content)
        if self._should_learn('react-component'):
            self._learn_react_component_patterns(content)
        if self._should_learn('api-route'):
            self._learn_api_route_patterns(content)
        if self._should_learn('test-pattern'):
            self._learn_test_patterns(file_path, content)

    def _learn_ts_js_naming_patterns(self, file_path: Path, content: str):
        naming_patterns = []

        classes = self.ts_js_patterns['class_decl'].findall(content)
        for cls in classes:
            if cls:
                naming_patterns.append(('class', cls))

        functions = self.ts_js_patterns['function_decl'].findall(content)
        for func in functions:
            if func:
                naming_patterns.append(('function', func))

        arrow_funcs = self.ts_js_patterns['arrow_func'].findall(content)
        for func in arrow_funcs:
            if func:
                naming_patterns.append(('arrow-function', func))

        const_funcs = self.ts_js_patterns['const_func'].findall(content)
        for func in const_funcs:
            if func:
                naming_patterns.append(('const-function', func))

        interfaces = self.ts_js_patterns['interface_decl'].findall(content)
        for iface in interfaces:
            if iface:
                naming_patterns.append(('interface', iface))

        type_decls = self.ts_js_patterns['type_decl'].findall(content)
        for t in type_decls:
            if t:
                naming_patterns.append(('type', t))

        exports = self.ts_js_patterns['export_pattern'].findall(content)
        for exp in exports:
            if exp:
                naming_patterns.append(('export', exp))

        file_key = str(file_path)
        for ptype, name in naming_patterns:
            self._ts_js_naming_accumulator[(ptype, name)].add(file_key)

    def _learn_ts_js_structure_patterns(self, content: str):
        lines = content.splitlines()

        imports = []
        for line in lines:
            stripped = line.strip()
            if stripped.startswith('import ') or stripped.startswith('import{') or stripped.startswith('import {'):
                imports.append(stripped)
            elif stripped.startswith('require('):
                imports.append(stripped)

        if imports:
            import_pattern = Pattern(
                name='tsjs_import_organization',
                pattern_type='structure',
                description='TS/JS导入语句组织模式',
                examples=imports[:5],
                frequency=len(imports),
                confidence=0.8
            )
            self.patterns['structure'].append(import_pattern)

        interfaces = self.ts_js_patterns['interface_decl'].findall(content)
        if interfaces:
            pattern = Pattern(
                name='tsjs_interface_usage',
                pattern_type='structure',
                description='TypeScript接口使用模式',
                frequency=len(interfaces),
                confidence=min(len(interfaces) / 5, 1.0)
            )
            self.patterns['structure'].append(pattern)

        type_decls = self.ts_js_patterns['type_decl'].findall(content)
        if type_decls:
            pattern = Pattern(
                name='tsjs_type_declaration',
                pattern_type='structure',
                description='TypeScript类型声明模式',
                frequency=len(type_decls),
                confidence=min(len(type_decls) / 5, 1.0)
            )
            self.patterns['structure'].append(pattern)

        class_defs = self.ts_js_patterns['class_decl'].findall(content)
        if class_defs:
            class_bodies = self._extract_ts_js_class_bodies(content)
            total_methods = 0
            for body in class_bodies:
                methods = re.findall(
                    r'(?:public|private|protected)\s+(?:static\s+)?(?:async\s+)?(?:get\s+|set\s+)?\w+\s*\(|'
                    r'(?:static\s+)(?:async\s+)?\w+\s*\(|'
                    r'(?:async\s+)\w+\s*\(',
                    body
                )
                total_methods += len(methods)
            avg_methods = total_methods / max(len(class_defs), 1)
            pattern = Pattern(
                name='tsjs_class_size',
                pattern_type='structure',
                description=f'TS/JS类平均方法数: {avg_methods:.1f}',
                frequency=len(class_defs),
                confidence=0.7,
                metadata={'avg_methods_per_class': avg_methods}
            )
            self.patterns['structure'].append(pattern)

        exports = self.ts_js_patterns['export_pattern'].findall(content)
        if exports:
            pattern = Pattern(
                name='tsjs_export_usage',
                pattern_type='structure',
                description='TS/JS导出模式',
                frequency=len(exports),
                confidence=0.8
            )
            self.patterns['structure'].append(pattern)

    def _learn_ts_js_error_handling_patterns(self, content: str):
        try_blocks = self.ts_js_patterns['try_catch'].findall(content)

        if try_blocks:
            pattern = Pattern(
                name='tsjs_try_catch_usage',
                pattern_type='error-handling',
                description='TS/JS try-catch错误处理模式',
                frequency=len(try_blocks),
                confidence=0.9
            )
            self.patterns['error-handling'].append(pattern)

        catch_blocks = re.findall(r'catch\s*\(\s*(\w+)\s*\)', content)
        if catch_blocks:
            pattern = Pattern(
                name='tsjs_catch_binding',
                pattern_type='error-handling',
                description='TS/JS catch绑定模式',
                frequency=len(catch_blocks),
                confidence=0.85
            )
            self.patterns['error-handling'].append(pattern)

        throw_statements = re.findall(r'throw\s+(?:new\s+)?(\w+)', content)
        if throw_statements:
            error_types = defaultdict(int)
            for err in throw_statements:
                error_types[err] += 1
            for err_type, count in error_types.items():
                if count >= self.min_frequency:
                    pattern = Pattern(
                        name=f'tsjs_throw_{err_type.lower()}',
                        pattern_type='error-handling',
                        description=f'TS/JS抛出错误类型: {err_type}',
                        frequency=count,
                        confidence=0.8
                    )
                    self.patterns['error-handling'].append(pattern)

        async_funcs = self.ts_js_patterns['async_function'].findall(content)
        await_usages = self.ts_js_patterns['await_usage'].findall(content)
        if async_funcs or await_usages:
            pattern = Pattern(
                name='tsjs_async_await',
                pattern_type='error-handling',
                description='TS/JS async/await模式',
                frequency=len(async_funcs) + len(await_usages),
                confidence=0.85
            )
            self.patterns['error-handling'].append(pattern)

    def _learn_ts_js_testing_patterns(self, file_path: Path, content: str):
        if 'test' not in file_path.name.lower() and 'spec' not in file_path.name.lower():
            return

        test_blocks = self.ts_js_patterns['jest_test'].findall(content)
        if test_blocks:
            pattern = Pattern(
                name='tsjs_jest_test',
                pattern_type='testing',
                description='Jest测试模式',
                examples=test_blocks[:5],
                frequency=len(test_blocks),
                confidence=0.95
            )
            self.patterns['testing'].append(pattern)

        expects = re.findall(r'expect\(', content)
        if expects:
            pattern = Pattern(
                name='tsjs_expect_usage',
                pattern_type='testing',
                description='Jest expect断言模式',
                frequency=len(expects),
                confidence=0.9
            )
            self.patterns['testing'].append(pattern)

    def _learn_ts_js_api_patterns(self, content: str):
        response_patterns = re.findall(r'res\.(?:json|send|status|end)\(', content)
        if response_patterns:
            pattern = Pattern(
                name='tsjs_express_response',
                pattern_type='api',
                description='Express响应模式',
                frequency=len(response_patterns),
                confidence=0.85
            )
            self.patterns['api'].append(pattern)

        middleware_patterns = re.findall(r'app\.use\(', content)
        if middleware_patterns:
            pattern = Pattern(
                name='tsjs_middleware_usage',
                pattern_type='api',
                description='Express中间件模式',
                frequency=len(middleware_patterns),
                confidence=0.8
            )
            self.patterns['api'].append(pattern)

    def _learn_react_component_patterns(self, content: str):
        react_components = self.ts_js_patterns['react_component'].findall(content)
        if react_components:
            pattern = Pattern(
                name='react_typed_component',
                pattern_type='react-component',
                description='React类型化组件模式',
                examples=react_components[:5],
                frequency=len(react_components),
                confidence=0.9
            )
            self.patterns['react-component'].append(pattern)

        jsx_returns = re.findall(r'return\s*\([^\n]{0,500}?<', content)
        if jsx_returns:
            pattern = Pattern(
                name='react_jsx_return',
                pattern_type='react-component',
                description='React JSX返回模式',
                frequency=len(jsx_returns),
                confidence=0.85
            )
            self.patterns['react-component'].append(pattern)

        hooks = re.findall(r'use(?:State|Effect|Callback|Memo|Ref|Context|Reducer)\(', content)
        if hooks:
            hook_counts = defaultdict(int)
            for hook in hooks:
                hook_counts[hook] += 1
            for hook_name, count in hook_counts.items():
                if count >= self.min_frequency:
                    pattern = Pattern(
                        name=f'react_hook_{hook_name.lower()}',
                        pattern_type='react-component',
                        description=f'React Hook使用模式: {hook_name}',
                        frequency=count,
                        confidence=0.9
                    )
                    self.patterns['react-component'].append(pattern)

        props_interfaces = re.findall(r'interface\s+(\w+Props)\s*\{', content)
        if props_interfaces:
            pattern = Pattern(
                name='react_props_interface',
                pattern_type='react-component',
                description='React Props接口定义模式',
                examples=props_interfaces[:5],
                frequency=len(props_interfaces),
                confidence=0.9
            )
            self.patterns['react-component'].append(pattern)

    def _learn_api_route_patterns(self, content: str):
        routes = self.ts_js_patterns['express_route'].findall(content)
        if routes:
            methods = defaultdict(int)
            for method, path in routes:
                methods[method.lower()] += 1

            for method, count in methods.items():
                pattern = Pattern(
                    name=f'tsjs_api_{method}_endpoint',
                    pattern_type='api-route',
                    description=f'TS/JS API {method.upper()} 端点模式',
                    frequency=count,
                    confidence=0.9
                )
                self.patterns['api-route'].append(pattern)

            route_paths = [path for _, path in routes]
            pattern = Pattern(
                name='tsjs_express_routes',
                pattern_type='api-route',
                description='Express路由定义模式',
                examples=route_paths[:5],
                frequency=len(routes),
                confidence=0.9
            )
            self.patterns['api-route'].append(pattern)

        fastify_routes = re.findall(r'fastify\.(get|post|put|delete|patch)\s*\(\s*[\'"]([^\'"]+)[\'"]', content)
        if fastify_routes:
            pattern = Pattern(
                name='tsjs_fastify_routes',
                pattern_type='api-route',
                description='Fastify路由定义模式',
                frequency=len(fastify_routes),
                confidence=0.85
            )
            self.patterns['api-route'].append(pattern)

    def _learn_test_patterns(self, file_path: Path, content: str):
        if 'test' not in file_path.name.lower() and 'spec' not in file_path.name.lower():
            return

        describe_blocks = re.findall(r'describe\s*\(\s*[\'"]([^\'"]+)[\'"]', content)
        if describe_blocks:
            pattern = Pattern(
                name='tsjs_describe_block',
                pattern_type='test-pattern',
                description='Jest/Vitest describe块模式',
                examples=describe_blocks[:5],
                frequency=len(describe_blocks),
                confidence=0.9
            )
            self.patterns['test-pattern'].append(pattern)

        it_blocks = re.findall(r'(?:it|test)\s*\(\s*[\'"]([^\'"]+)[\'"]', content)
        if it_blocks:
            pattern = Pattern(
                name='tsjs_it_block',
                pattern_type='test-pattern',
                description='Jest/Vitest it/test块模式',
                examples=it_blocks[:5],
                frequency=len(it_blocks),
                confidence=0.9
            )
            self.patterns['test-pattern'].append(pattern)

        before_after = re.findall(r'(?:beforeEach|afterEach|beforeAll|afterAll)\s*\(', content)
        if before_after:
            pattern = Pattern(
                name='tsjs_lifecycle_hooks',
                pattern_type='test-pattern',
                description='Jest/Vitest生命周期钩子模式',
                frequency=len(before_after),
                confidence=0.85
            )
            self.patterns['test-pattern'].append(pattern)

        vitest_specific = re.findall(r'vi\.(?:fn|spyOn|mock|importMock)', content)
        if vitest_specific:
            pattern = Pattern(
                name='tsjs_vitest_mocking',
                pattern_type='test-pattern',
                description='Vitest mock模式',
                frequency=len(vitest_specific),
                confidence=0.85
            )
            self.patterns['test-pattern'].append(pattern)

    def _filter_and_rank_patterns(self):
        for ptype in self.patterns:
            seen = set()
            unique_patterns = []
            for pattern in self.patterns[ptype]:
                if pattern.name not in seen:
                    seen.add(pattern.name)
                    unique_patterns.append(pattern)

            unique_patterns.sort(key=lambda p: p.frequency, reverse=True)
            self.patterns[ptype] = unique_patterns

    def _finalize_naming_patterns(self):
        for (ptype, name), files in self._naming_accumulator.items():
            count = len(files)
            if count >= self.min_frequency:
                pattern = Pattern(
                    name=f"{ptype}_naming_{name}",
                    pattern_type='naming',
                    description=f"{ptype}命名模式: {name}",
                    frequency=count,
                    confidence=min(count / 10, 1.0)
                )
                self.patterns['naming'].append(pattern)

        for (ptype, name), files in self._ts_js_naming_accumulator.items():
            count = len(files)
            if count >= self.min_frequency:
                pattern = Pattern(
                    name=f"tsjs_{ptype}_naming_{name}",
                    pattern_type='naming',
                    description=f"TS/JS {ptype}命名模式: {name}",
                    frequency=count,
                    confidence=min(count / 10, 1.0)
                )
                self.patterns['naming'].append(pattern)

    def _extract_ts_js_class_bodies(self, content: str) -> List[str]:
        class_bodies = []
        i = 0
        while i < len(content):
            match = re.search(r'class\s+\w+', content[i:])
            if not match:
                break
            brace_start = content.find('{', i + match.start())
            if brace_start == -1:
                break
            depth = 1
            j = brace_start + 1
            while j < len(content) and depth > 0:
                if content[j] == '{':
                    depth += 1
                elif content[j] == '}':
                    depth -= 1
                j += 1
            class_bodies.append(content[brace_start + 1:j - 1])
            i = j
        return class_bodies

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

    learner = PatternLearner(args.source, args.min_frequency, args.pattern_types)
    report = learner.learn_all()

    if report:
        save_patterns(args.output, report)
        print_summary(report)

    sys.exit(0)


if __name__ == '__main__':
    main()
