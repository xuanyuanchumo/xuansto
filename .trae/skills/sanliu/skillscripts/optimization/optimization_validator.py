"""
优化效果验证模块

包含：
- OptimizationComparator: 优化前后对比
- PerformanceBenchmark: 性能基准测试
- QualityMetricsValidator: 质量指标验证
- OptimizationReportGenerator: 优化报告生成
"""

import ast
import re
import json
import time
import statistics
import hashlib
import difflib
from pathlib import Path
from typing import Dict, List, Tuple, Any, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading


class MetricType(Enum):
    PERFORMANCE = "performance"
    QUALITY = "quality"
    COMPLEXITY = "complexity"
    COVERAGE = "coverage"
    MAINTAINABILITY = "maintainability"


@dataclass
class MetricResult:
    name: str
    metric_type: MetricType
    before_value: float
    after_value: float
    improvement: float
    unit: str
    description: str
    passed: bool


@dataclass
class BenchmarkResult:
    name: str
    iterations: int
    avg_time_ms: float
    min_time_ms: float
    max_time_ms: float
    std_dev_ms: float
    memory_usage_mb: float
    cpu_usage_percent: float
    passed: bool
    threshold_ms: float


@dataclass
class ComparisonResult:
    file_path: str
    metric_name: str
    before_value: Any
    after_value: Any
    change_percent: float
    improvement: bool
    details: Dict[str, Any]


class OptimizationComparator:
    """优化前后对比器"""

    def __init__(self):
        self._comparisons: List[ComparisonResult] = []
        self._before_snapshot: Dict[str, Any] = {}
        self._after_snapshot: Dict[str, Any] = {}

    def capture_before(self, project_path: Path) -> Dict[str, Any]:
        self._before_snapshot = self._capture_snapshot(project_path)
        return self._before_snapshot

    def capture_after(self, project_path: Path) -> Dict[str, Any]:
        self._after_snapshot = self._capture_snapshot(project_path)
        return self._after_snapshot

    def _capture_snapshot(self, project_path: Path) -> Dict[str, Any]:
        snapshot = {
            'timestamp': datetime.now().isoformat(),
            'metrics': {},
            'file_stats': {},
            'code_metrics': {}
        }

        backend_dir = project_path / "backend" / "app"
        if backend_dir.exists():
            snapshot['code_metrics']['backend'] = self._analyze_code_metrics(backend_dir)

        frontend_dir = project_path / "frontend" / "src"
        if frontend_dir.exists():
            snapshot['code_metrics']['frontend'] = self._analyze_frontend_metrics(frontend_dir)

        snapshot['metrics'] = {
            'total_files': sum(
                len(m.get('files', []))
                for m in snapshot['code_metrics'].values()
            ),
            'total_lines': sum(
                m.get('total_lines', 0)
                for m in snapshot['code_metrics'].values()
            ),
            'total_functions': sum(
                m.get('function_count', 0)
                for m in snapshot['code_metrics'].values()
            ),
            'total_classes': sum(
                m.get('class_count', 0)
                for m in snapshot['code_metrics'].values()
            ),
        }

        return snapshot

    def _analyze_code_metrics(self, code_dir: Path) -> Dict[str, Any]:
        metrics = {
            'files': [],
            'total_lines': 0,
            'total_code_lines': 0,
            'total_comment_lines': 0,
            'function_count': 0,
            'class_count': 0,
            'average_function_length': 0,
            'average_class_size': 0,
            'complexity_metrics': {}
        }

        function_lengths = []
        class_sizes = []

        for py_file in code_dir.rglob("*.py"):
            if "__pycache__" in str(py_file):
                continue

            file_metrics = self._analyze_python_file(py_file)
            metrics['files'].append({
                'path': str(py_file.relative_to(code_dir)),
                'lines': file_metrics['total_lines'],
                'functions': file_metrics['function_count'],
                'classes': file_metrics['class_count']
            })

            metrics['total_lines'] += file_metrics['total_lines']
            metrics['total_code_lines'] += file_metrics['code_lines']
            metrics['total_comment_lines'] += file_metrics['comment_lines']
            metrics['function_count'] += file_metrics['function_count']
            metrics['class_count'] += file_metrics['class_count']

            function_lengths.extend(file_metrics['function_lengths'])
            class_sizes.extend(file_metrics['class_sizes'])

        if function_lengths:
            metrics['average_function_length'] = statistics.mean(function_lengths)
        if class_sizes:
            metrics['average_class_size'] = statistics.mean(class_sizes)

        return metrics

    def _analyze_python_file(self, file_path: Path) -> Dict[str, Any]:
        metrics = {
            'total_lines': 0,
            'code_lines': 0,
            'comment_lines': 0,
            'blank_lines': 0,
            'function_count': 0,
            'class_count': 0,
            'function_lengths': [],
            'class_sizes': []
        }

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                lines = content.split('\n')

            metrics['total_lines'] = len(lines)

            for line in lines:
                stripped = line.strip()
                if not stripped:
                    metrics['blank_lines'] += 1
                elif stripped.startswith('#'):
                    metrics['comment_lines'] += 1
                else:
                    metrics['code_lines'] += 1

            tree = ast.parse(content)

            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    metrics['function_count'] += 1
                    if hasattr(node, 'end_lineno'):
                        length = node.end_lineno - node.lineno + 1
                        metrics['function_lengths'].append(length)

                elif isinstance(node, ast.ClassDef):
                    metrics['class_count'] += 1
                    if hasattr(node, 'end_lineno'):
                        size = node.end_lineno - node.lineno + 1
                        metrics['class_sizes'].append(size)

        except Exception:
            pass

        return metrics

    def _analyze_frontend_metrics(self, frontend_dir: Path) -> Dict[str, Any]:
        metrics = {
            'files': [],
            'total_lines': 0,
            'total_code_lines': 0,
            'function_count': 0,
            'class_count': 0
        }

        for ts_file in frontend_dir.rglob("*.ts"):
            if "node_modules" in str(ts_file):
                continue

            try:
                with open(ts_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    lines = content.split('\n')

                file_metrics = {
                    'path': str(ts_file.relative_to(frontend_dir)),
                    'lines': len(lines)
                }

                metrics['files'].append(file_metrics)
                metrics['total_lines'] += len(lines)
                metrics['total_code_lines'] += len([l for l in lines if l.strip() and not l.strip().startswith('//')])
                metrics['function_count'] += content.count('function ')
                metrics['class_count'] += content.count('class ')

            except Exception:
                pass

        for vue_file in frontend_dir.rglob("*.vue"):
            if "node_modules" in str(vue_file):
                continue

            try:
                with open(vue_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    lines = content.split('\n')

                metrics['total_lines'] += len(lines)

            except Exception:
                pass

        return metrics

    def compare(self) -> Dict[str, Any]:
        if not self._before_snapshot or not self._after_snapshot:
            return {'error': '需要先捕获优化前后的快照'}

        comparison = {
            'timestamp': datetime.now().isoformat(),
            'metrics_comparison': {},
            'improvements': [],
            'regressions': [],
            'summary': {}
        }

        before_metrics = self._before_snapshot.get('metrics', {})
        after_metrics = self._after_snapshot.get('metrics', {})

        for metric_name in before_metrics:
            if metric_name in after_metrics:
                before_val = before_metrics[metric_name]
                after_val = after_metrics[metric_name]

                if isinstance(before_val, (int, float)) and isinstance(after_val, (int, float)):
                    if before_val != 0:
                        change_percent = ((after_val - before_val) / before_val) * 100
                    else:
                        change_percent = 0 if after_val == 0 else 100

                    comparison['metrics_comparison'][metric_name] = {
                        'before': before_val,
                        'after': after_val,
                        'change': after_val - before_val,
                        'change_percent': round(change_percent, 2)
                    }

                    if metric_name in ['total_lines', 'total_code_lines']:
                        if change_percent < 0:
                            comparison['improvements'].append({
                                'metric': metric_name,
                                'improvement': abs(change_percent),
                                'description': f'代码行数减少 {abs(change_percent):.1f}%'
                            })
                    elif metric_name in ['function_count', 'class_count']:
                        pass

        comparison['summary'] = {
            'total_improvements': len(comparison['improvements']),
            'total_regressions': len(comparison['regressions']),
            'overall_improvement': len(comparison['improvements']) > len(comparison['regressions'])
        }

        return comparison

    def compare_files(self, before_content: str, after_content: str, file_path: str) -> Dict[str, Any]:
        before_lines = before_content.splitlines(keepends=True)
        after_lines = after_content.splitlines(keepends=True)

        diff = list(difflib.unified_diff(
            before_lines,
            after_lines,
            fromfile=f'{file_path} (before)',
            tofile=f'{file_path} (after)',
            lineterm=''
        ))

        additions = sum(1 for line in diff if line.startswith('+') and not line.startswith('+++'))
        deletions = sum(1 for line in diff if line.startswith('-') and not line.startswith('---'))

        return {
            'file_path': file_path,
            'diff': ''.join(diff),
            'additions': additions,
            'deletions': deletions,
            'net_change': additions - deletions,
            'change_summary': f'+{additions} -{deletions}'
        }


class PerformanceBenchmark:
    """性能基准测试"""

    def __init__(self, warmup_iterations: int = 3, test_iterations: int = 10):
        self._warmup_iterations = warmup_iterations
        self._test_iterations = test_iterations
        self._results: List[BenchmarkResult] = []
        self._benchmarks: Dict[str, Callable] = {}

    def register_benchmark(self, name: str, func: Callable, threshold_ms: float = 1000.0):
        self._benchmarks[name] = {'func': func, 'threshold_ms': threshold_ms}

    def run_all_benchmarks(self) -> Dict[str, Any]:
        results = []

        for name, config in self._benchmarks.items():
            result = self._run_benchmark(name, config['func'], config['threshold_ms'])
            results.append(result)

        self._results = results

        return {
            'timestamp': datetime.now().isoformat(),
            'results': [self._result_to_dict(r) for r in results],
            'summary': self._generate_summary(results)
        }

    def _run_benchmark(self, name: str, func: Callable, threshold_ms: float) -> BenchmarkResult:
        for _ in range(self._warmup_iterations):
            try:
                func()
            except Exception:
                pass

        times = []
        memory_usage = []
        cpu_usage = []

        for _ in range(self._test_iterations):
            try:
                import tracemalloc
                import os

                tracemalloc.start()
                start_cpu = time.process_time()
                start_time = time.perf_counter()

                func()

                end_time = time.perf_counter()
                end_cpu = time.process_time()

                current, peak = tracemalloc.get_traced_memory()
                tracemalloc.stop()

                elapsed_ms = (end_time - start_time) * 1000
                times.append(elapsed_ms)
                memory_usage.append(peak / 1024 / 1024)
                cpu_usage.append((end_cpu - start_cpu) * 100)

            except Exception as e:
                times.append(float('inf'))
                memory_usage.append(0)
                cpu_usage.append(0)

        if not times or all(t == float('inf') for t in times):
            return BenchmarkResult(
                name=name,
                iterations=0,
                avg_time_ms=0,
                min_time_ms=0,
                max_time_ms=0,
                std_dev_ms=0,
                memory_usage_mb=0,
                cpu_usage_percent=0,
                passed=False,
                threshold_ms=threshold_ms
            )

        valid_times = [t for t in times if t != float('inf')]

        return BenchmarkResult(
            name=name,
            iterations=len(valid_times),
            avg_time_ms=statistics.mean(valid_times) if valid_times else 0,
            min_time_ms=min(valid_times) if valid_times else 0,
            max_time_ms=max(valid_times) if valid_times else 0,
            std_dev_ms=statistics.stdev(valid_times) if len(valid_times) > 1 else 0,
            memory_usage_mb=statistics.mean(memory_usage) if memory_usage else 0,
            cpu_usage_percent=statistics.mean(cpu_usage) if cpu_usage else 0,
            passed=statistics.mean(valid_times) < threshold_ms if valid_times else False,
            threshold_ms=threshold_ms
        )

    def _result_to_dict(self, result: BenchmarkResult) -> Dict[str, Any]:
        return {
            'name': result.name,
            'iterations': result.iterations,
            'avg_time_ms': round(result.avg_time_ms, 3),
            'min_time_ms': round(result.min_time_ms, 3),
            'max_time_ms': round(result.max_time_ms, 3),
            'std_dev_ms': round(result.std_dev_ms, 3),
            'memory_usage_mb': round(result.memory_usage_mb, 2),
            'cpu_usage_percent': round(result.cpu_usage_percent, 2),
            'passed': result.passed,
            'threshold_ms': result.threshold_ms
        }

    def _generate_summary(self, results: List[BenchmarkResult]) -> Dict[str, Any]:
        passed = sum(1 for r in results if r.passed)
        failed = len(results) - passed

        return {
            'total_benchmarks': len(results),
            'passed': passed,
            'failed': failed,
            'pass_rate': round(passed / len(results) * 100, 2) if results else 0,
            'total_avg_time_ms': round(sum(r.avg_time_ms for r in results), 3),
            'total_memory_mb': round(sum(r.memory_usage_mb for r in results), 2)
        }

    def create_code_benchmark(self, code: str, setup_code: str = '') -> Callable:
        def benchmark_func():
            local_vars = {}
            if setup_code:
                exec(setup_code, {}, local_vars)
            exec(code, {}, local_vars)

        return benchmark_func

    def benchmark_file_parsing(self, file_path: Path) -> BenchmarkResult:
        def parse_func():
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            if file_path.suffix == '.py':
                ast.parse(content)

        return self._run_benchmark(f'parse_{file_path.name}', parse_func, 100.0)


class QualityMetricsValidator:
    """质量指标验证器"""

    def __init__(self):
        self._metrics: List[MetricResult] = []
        self._thresholds: Dict[str, Dict[str, float]] = {
            'cyclomatic_complexity': {'max': 10, 'target': 5},
            'lines_of_code': {'max': 500, 'target': 200},
            'function_length': {'max': 50, 'target': 20},
            'class_length': {'max': 300, 'target': 100},
            'parameter_count': {'max': 7, 'target': 4},
            'nesting_depth': {'max': 5, 'target': 3},
            'code_duplication': {'max': 10, 'target': 3},
            'test_coverage': {'min': 80, 'target': 90},
            'documentation_coverage': {'min': 50, 'target': 80},
        }

    def validate(self, project_path: Path) -> Dict[str, Any]:
        self._metrics.clear()

        backend_dir = project_path / "backend" / "app"
        if backend_dir.exists():
            self._validate_python_code(backend_dir)

        return {
            'timestamp': datetime.now().isoformat(),
            'metrics': [self._metric_to_dict(m) for m in self._metrics],
            'summary': self._generate_summary(),
            'recommendations': self._generate_recommendations()
        }

    def _validate_python_code(self, code_dir: Path):
        for py_file in code_dir.rglob("*.py"):
            if "__pycache__" in str(py_file):
                continue

            self._validate_file_complexity(py_file)
            self._validate_file_length(py_file)
            self._validate_documentation(py_file)

    def _validate_file_complexity(self, file_path: Path):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            tree = ast.parse(content)

            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    complexity = self._calculate_cyclomatic_complexity(node)
                    threshold = self._thresholds['cyclomatic_complexity']

                    self._metrics.append(MetricResult(
                        name=f'complexity:{node.name}',
                        metric_type=MetricType.COMPLEXITY,
                        before_value=complexity,
                        after_value=0,
                        improvement=0,
                        unit='points',
                        description=f'函数 {node.name} 的圈复杂度',
                        passed=complexity <= threshold['max']
                    ))

                elif isinstance(node, ast.ClassDef):
                    if hasattr(node, 'end_lineno'):
                        class_length = node.end_lineno - node.lineno + 1
                        threshold = self._thresholds['class_length']

                        self._metrics.append(MetricResult(
                            name=f'class_length:{node.name}',
                            metric_type=MetricType.COMPLEXITY,
                            before_value=class_length,
                            after_value=0,
                            improvement=0,
                            unit='lines',
                            description=f'类 {node.name} 的长度',
                            passed=class_length <= threshold['max']
                        ))

        except Exception:
            pass

    def _validate_file_length(self, file_path: Path):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()

            line_count = len(lines)
            threshold = self._thresholds['lines_of_code']

            self._metrics.append(MetricResult(
                name=f'file_length:{file_path.name}',
                metric_type=MetricType.COMPLEXITY,
                before_value=line_count,
                after_value=0,
                improvement=0,
                unit='lines',
                description=f'文件 {file_path.name} 的行数',
                passed=line_count <= threshold['max']
            ))

        except Exception:
            pass

    def _validate_documentation(self, file_path: Path):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            tree = ast.parse(content)

            total_functions = 0
            documented_functions = 0

            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    if not node.name.startswith('_'):
                        total_functions += 1
                        if ast.get_docstring(node):
                            documented_functions += 1

            if total_functions > 0:
                coverage = (documented_functions / total_functions) * 100
                threshold = self._thresholds['documentation_coverage']

                self._metrics.append(MetricResult(
                    name=f'doc_coverage:{file_path.name}',
                    metric_type=MetricType.QUALITY,
                    before_value=coverage,
                    after_value=0,
                    improvement=0,
                    unit='%',
                    description=f'文件 {file_path.name} 的文档覆盖率',
                    passed=coverage >= threshold['min']
                ))

        except Exception:
            pass

    def _calculate_cyclomatic_complexity(self, node: ast.FunctionDef) -> int:
        complexity = 1

        for child in ast.walk(node):
            if isinstance(child, (ast.If, ast.While, ast.For, ast.ExceptHandler)):
                complexity += 1
            elif isinstance(child, ast.BoolOp):
                complexity += len(child.values) - 1
            elif isinstance(child, ast.comprehension):
                complexity += 1
                if child.ifs:
                    complexity += len(child.ifs)

        return complexity

    def _metric_to_dict(self, metric: MetricResult) -> Dict[str, Any]:
        return {
            'name': metric.name,
            'type': metric.metric_type.value,
            'value': metric.before_value,
            'unit': metric.unit,
            'description': metric.description,
            'passed': metric.passed
        }

    def _generate_summary(self) -> Dict[str, Any]:
        if not self._metrics:
            return {'total': 0, 'passed': 0, 'failed': 0, 'pass_rate': 0}

        passed = sum(1 for m in self._metrics if m.passed)
        total = len(self._metrics)

        return {
            'total': total,
            'passed': passed,
            'failed': total - passed,
            'pass_rate': round(passed / total * 100, 2)
        }

    def _generate_recommendations(self) -> List[str]:
        recommendations = []

        failed_metrics = [m for m in self._metrics if not m.passed]

        complexity_failures = [m for m in failed_metrics if m.metric_type == MetricType.COMPLEXITY]
        if complexity_failures:
            recommendations.append(f"发现 {len(complexity_failures)} 个复杂度问题，建议重构")

        doc_failures = [m for m in failed_metrics if 'doc_coverage' in m.name]
        if doc_failures:
            recommendations.append(f"发现 {len(doc_failures)} 个文件文档覆盖率不足，建议添加文档")

        return recommendations

    def compare_before_after(self, before_metrics: Dict[str, Any], after_metrics: Dict[str, Any]) -> List[MetricResult]:
        results = []

        for metric_name in before_metrics:
            if metric_name in after_metrics:
                before_val = before_metrics[metric_name]
                after_val = after_metrics[metric_name]

                if isinstance(before_val, (int, float)) and isinstance(after_val, (int, float)):
                    improvement = before_val - after_val

                    threshold = self._thresholds.get(metric_name, {})
                    passed = True
                    if 'max' in threshold:
                        passed = after_val <= threshold['max']
                    elif 'min' in threshold:
                        passed = after_val >= threshold['min']

                    results.append(MetricResult(
                        name=metric_name,
                        metric_type=MetricType.QUALITY,
                        before_value=before_val,
                        after_value=after_val,
                        improvement=improvement,
                        unit='',
                        description=f'{metric_name} 指标变化',
                        passed=passed
                    ))

        return results


class OptimizationReportGenerator:
    """优化报告生成器"""

    def __init__(self):
        self._report_data: Dict[str, Any] = {}

    def generate_report(
        self,
        comparison_result: Dict[str, Any],
        benchmark_result: Dict[str, Any],
        quality_result: Dict[str, Any],
        optimization_details: Dict[str, Any]
    ) -> Dict[str, Any]:
        report = {
            'report_id': f"OPT-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            'generated_at': datetime.now().isoformat(),
            'summary': self._generate_summary(comparison_result, benchmark_result, quality_result),
            'comparison': comparison_result,
            'benchmark': benchmark_result,
            'quality': quality_result,
            'optimizations': optimization_details,
            'recommendations': self._generate_recommendations(comparison_result, benchmark_result, quality_result)
        }

        self._report_data = report
        return report

    def _generate_summary(
        self,
        comparison: Dict[str, Any],
        benchmark: Dict[str, Any],
        quality: Dict[str, Any]
    ) -> Dict[str, Any]:
        comparison_summary = comparison.get('summary', {})
        benchmark_summary = benchmark.get('summary', {})
        quality_summary = quality.get('summary', {})

        return {
            'overall_improvement': comparison_summary.get('overall_improvement', False),
            'improvements_count': comparison_summary.get('total_improvements', 0),
            'regressions_count': comparison_summary.get('total_regressions', 0),
            'benchmark_pass_rate': benchmark_summary.get('pass_rate', 0),
            'quality_pass_rate': quality_summary.get('pass_rate', 0),
            'overall_score': self._calculate_overall_score(
                comparison_summary, benchmark_summary, quality_summary
            )
        }

    def _calculate_overall_score(
        self,
        comparison: Dict[str, Any],
        benchmark: Dict[str, Any],
        quality: Dict[str, Any]
    ) -> float:
        improvement_score = 100 if comparison.get('overall_improvement', False) else 50

        benchmark_score = benchmark.get('pass_rate', 0)

        quality_score = quality.get('pass_rate', 0)

        overall = (
            improvement_score * 0.3 +
            benchmark_score * 0.35 +
            quality_score * 0.35
        )

        return round(overall, 2)

    def _generate_recommendations(
        self,
        comparison: Dict[str, Any],
        benchmark: Dict[str, Any],
        quality: Dict[str, Any]
    ) -> List[str]:
        recommendations = []

        if comparison.get('summary', {}).get('total_regressions', 0) > 0:
            recommendations.append("存在性能回退，建议检查最近的代码变更")

        failed_benchmarks = [
            r for r in benchmark.get('results', [])
            if not r.get('passed', True)
        ]
        if failed_benchmarks:
            recommendations.append(f"{len(failed_benchmarks)} 个基准测试未通过，建议优化相关代码")

        quality_recommendations = quality.get('recommendations', [])
        recommendations.extend(quality_recommendations)

        if not recommendations:
            recommendations.append("优化效果良好，建议继续保持代码质量")

        return recommendations

    def generate_markdown_report(self, report: Dict[str, Any]) -> str:
        lines = [
            "# 优化效果验证报告",
            "",
            f"**报告ID**: {report['report_id']}",
            f"**生成时间**: {report['generated_at']}",
            "",
            "## 总体评估",
            "",
            f"- **综合得分**: {report['summary']['overall_score']}/100",
            f"- **改进项数**: {report['summary']['improvements_count']}",
            f"- **回退项数**: {report['summary']['regressions_count']}",
            f"- **基准测试通过率**: {report['summary']['benchmark_pass_rate']}%",
            f"- **质量指标通过率**: {report['summary']['quality_pass_rate']}%",
            "",
            "## 优化前后对比",
            "",
        ]

        comparison = report.get('comparison', {})
        for metric_name, data in comparison.get('metrics_comparison', {}).items():
            change_symbol = '↓' if data['change_percent'] < 0 else '↑'
            lines.append(f"- **{metric_name}**: {data['before']} → {data['after']} ({change_symbol}{abs(data['change_percent'])}%)")

        lines.extend([
            "",
            "## 性能基准测试",
            "",
        ])

        benchmark = report.get('benchmark', {})
        for result in benchmark.get('results', []):
            status = '✅' if result['passed'] else '❌'
            lines.append(f"- {status} **{result['name']}**: {result['avg_time_ms']:.2f}ms (阈值: {result['threshold_ms']}ms)")

        lines.extend([
            "",
            "## 质量指标验证",
            "",
        ])

        quality = report.get('quality', {})
        quality_summary = quality.get('summary', {})
        lines.append(f"- **总指标数**: {quality_summary.get('total', 0)}")
        lines.append(f"- **通过数**: {quality_summary.get('passed', 0)}")
        lines.append(f"- **失败数**: {quality_summary.get('failed', 0)}")
        lines.append(f"- **通过率**: {quality_summary.get('pass_rate', 0)}%")

        lines.extend([
            "",
            "## 建议",
            "",
        ])

        for rec in report.get('recommendations', []):
            lines.append(f"- {rec}")

        return '\n'.join(lines)

    def generate_html_report(self, report: Dict[str, Any]) -> str:
        html = f"""
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <title>优化效果验证报告 - {report['report_id']}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }}
        .container {{ max-width: 1200px; margin: 0 auto; background: white; padding: 20px; border-radius: 8px; }}
        h1 {{ color: #333; border-bottom: 2px solid #4CAF50; padding-bottom: 10px; }}
        h2 {{ color: #555; margin-top: 30px; }}
        .summary {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 20px; margin: 20px 0; }}
        .summary-card {{ background: #f9f9f9; padding: 15px; border-radius: 8px; text-align: center; }}
        .summary-card h3 {{ margin: 0; color: #666; }}
        .summary-card .value {{ font-size: 2em; color: #4CAF50; margin: 10px 0; }}
        .metric {{ display: flex; justify-content: space-between; padding: 10px; border-bottom: 1px solid #eee; }}
        .improved {{ color: #4CAF50; }}
        .regressed {{ color: #f44336; }}
        .passed {{ color: #4CAF50; }}
        .failed {{ color: #f44336; }}
        table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
        th, td {{ padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }}
        th {{ background: #4CAF50; color: white; }}
        tr:hover {{ background: #f5f5f5; }}
        .recommendation {{ background: #fff3cd; padding: 15px; border-radius: 8px; margin: 10px 0; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>优化效果验证报告</h1>
        <p><strong>报告ID:</strong> {report['report_id']}</p>
        <p><strong>生成时间:</strong> {report['generated_at']}</p>

        <h2>总体评估</h2>
        <div class="summary">
            <div class="summary-card">
                <h3>综合得分</h3>
                <div class="value">{report['summary']['overall_score']}</div>
            </div>
            <div class="summary-card">
                <h3>基准测试通过率</h3>
                <div class="value">{report['summary']['benchmark_pass_rate']}%</div>
            </div>
            <div class="summary-card">
                <h3>质量指标通过率</h3>
                <div class="value">{report['summary']['quality_pass_rate']}%</div>
            </div>
        </div>

        <h2>建议</h2>
        {''.join(f'<div class="recommendation">{rec}</div>' for rec in report.get('recommendations', []))}
    </div>
</body>
</html>
"""
        return html

    def save_report(self, report: Dict[str, Any], output_path: Path, format: str = 'json'):
        output_path.parent.mkdir(parents=True, exist_ok=True)

        if format == 'json':
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(report, f, ensure_ascii=False, indent=2)
        elif format == 'markdown':
            md_content = self.generate_markdown_report(report)
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(md_content)
        elif format == 'html':
            html_content = self.generate_html_report(report)
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
