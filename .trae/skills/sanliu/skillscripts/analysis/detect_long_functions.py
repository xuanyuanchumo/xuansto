#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
长函数检测器

检测三省六部项目中的长函数，分析函数复杂度，提供重构建议。
支持Python代码的长函数检测和复杂度分析。

使用示例:
    python detect_long_functions.py
    python detect_long_functions.py --max-lines 50
    python detect_long_functions.py --output json --output-file result.json
    python detect_long_functions.py --verbose
"""

import os
import sys
import ast
import argparse
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class ComplexityLevel(Enum):
    """复杂度等级枚举"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    VERY_HIGH = "very_high"


class FunctionType(Enum):
    """函数类型枚举"""
    FUNCTION = "function"
    METHOD = "method"
    CLASS_METHOD = "class_method"
    STATIC_METHOD = "static_method"
    PROPERTY = "property"


@dataclass
class FunctionMetrics:
    """函数指标数据类"""
    name: str
    file_path: str
    line_start: int
    line_end: int
    line_count: int
    complexity: int
    parameter_count: int
    return_count: int
    nested_function_count: int
    docstring_lines: int
    function_type: FunctionType
    class_name: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "name": self.name,
            "file_path": self.file_path,
            "line_start": self.line_start,
            "line_end": self.line_end,
            "line_count": self.line_count,
            "complexity": self.complexity,
            "parameter_count": self.parameter_count,
            "return_count": self.return_count,
            "nested_function_count": self.nested_function_count,
            "docstring_lines": self.docstring_lines,
            "function_type": self.function_type.value,
            "class_name": self.class_name
        }


@dataclass
class LongFunction:
    """长函数数据类"""
    metrics: FunctionMetrics
    severity: ComplexityLevel
    issues: List[str] = field(default_factory=list)
    suggestions: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "metrics": self.metrics.to_dict(),
            "severity": self.severity.value,
            "issues": self.issues,
            "suggestions": self.suggestions
        }


@dataclass
class DetectionReport:
    """检测报告数据类"""
    timestamp: str
    project_root: str
    max_lines: int
    max_complexity: int
    total_functions: int
    long_functions: List[LongFunction]
    summary: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "timestamp": self.timestamp,
            "project_root": self.project_root,
            "max_lines": self.max_lines,
            "max_complexity": self.max_complexity,
            "total_functions": self.total_functions,
            "long_functions_count": len(self.long_functions),
            "summary": self.summary,
            "long_functions": [f.to_dict() for f in self.long_functions]
        }


class FunctionAnalyzer(ast.NodeVisitor):
    """函数分析器"""

    def __init__(self, file_path: str, content: str):
        self.file_path = file_path
        self.content = content
        self.lines = content.split('\n')
        self.functions: List[FunctionMetrics] = []
        self.current_class: Optional[str] = None

    def visit_ClassDef(self, node: ast.ClassDef):
        """访问类定义"""
        old_class = self.current_class
        self.current_class = node.name
        self.generic_visit(node)
        self.current_class = old_class

    def visit_FunctionDef(self, node: ast.FunctionDef):
        """访问函数定义"""
        self._analyze_function(node, FunctionType.FUNCTION)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef):
        """访问异步函数定义"""
        self._analyze_function(node, FunctionType.FUNCTION)

    def _analyze_function(self, node: ast.FunctionDef, default_type: FunctionType):
        """分析函数"""
        # 确定函数类型
        func_type = default_type
        if self.current_class:
            func_type = FunctionType.METHOD
            for decorator in node.decorator_list:
                if isinstance(decorator, ast.Name):
                    if decorator.id == 'classmethod':
                        func_type = FunctionType.CLASS_METHOD
                    elif decorator.id == 'staticmethod':
                        func_type = FunctionType.STATIC_METHOD
                    elif decorator.id == 'property':
                        func_type = FunctionType.PROPERTY

        # 计算行数
        line_start = node.lineno
        line_end = node.end_lineno if hasattr(node, 'end_lineno') else line_start
        line_count = line_end - line_start + 1

        # 计算复杂度
        complexity = self._calculate_complexity(node)

        # 计算参数数量
        param_count = len(node.args.args) + len(node.args.kwonlyargs)
        if node.args.vararg:
            param_count += 1
        if node.args.kwarg:
            param_count += 1

        # 计算return语句数量
        return_count = sum(1 for n in ast.walk(node) if isinstance(n, ast.Return) and n.value is not None)

        # 计算嵌套函数数量
        nested_count = sum(1 for n in ast.walk(node) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n != node)

        # 计算文档字符串行数
        docstring_lines = 0
        if (node.body and isinstance(node.body[0], ast.Expr) and
            isinstance(node.body[0].value, ast.Constant) and
            isinstance(node.body[0].value.value, str)):
            docstring = node.body[0].value.value
            docstring_lines = len(docstring.split('\n'))

        metrics = FunctionMetrics(
            name=node.name,
            file_path=self.file_path,
            line_start=line_start,
            line_end=line_end,
            line_count=line_count,
            complexity=complexity,
            parameter_count=param_count,
            return_count=return_count,
            nested_function_count=nested_count,
            docstring_lines=docstring_lines,
            function_type=func_type,
            class_name=self.current_class
        )

        self.functions.append(metrics)
        self.generic_visit(node)

    def _calculate_complexity(self, node: ast.AST) -> int:
        """计算圈复杂度"""
        complexity = 1

        for child in ast.walk(node):
            if isinstance(child, (ast.If, ast.While, ast.For, ast.ExceptHandler)):
                complexity += 1
            elif isinstance(child, ast.BoolOp):
                complexity += len(child.values) - 1
            elif isinstance(child, ast.comprehension):
                complexity += 1

        return complexity


class LongFunctionDetector:
    """长函数检测器"""

    # 默认阈值
    DEFAULT_MAX_LINES = 50
    DEFAULT_MAX_COMPLEXITY = 10

    def __init__(self, project_root: Optional[Path] = None,
                 max_lines: int = DEFAULT_MAX_LINES,
                 max_complexity: int = DEFAULT_MAX_COMPLEXITY,
                 logger: Optional[logging.Logger] = None):
        self.project_root = project_root or get_path_config().SKILL_ROOT
        self.max_lines = max_lines
        self.max_complexity = max_complexity
        self.logger = logger or logging.getLogger(__name__)
        self.long_functions: List[LongFunction] = []

    def detect_project(self) -> DetectionReport:
        """检测整个项目"""
        self.logger.info("开始检测长函数...")

        python_files = []

        # 扫描后端
        backend_dir = self.project_root / "backend"
        if backend_dir.exists():
            for py_file in backend_dir.rglob("*.py"):
                if "__pycache__" in str(py_file):
                    continue
                python_files.append(py_file)

        # 扫描脚本
        scripts_dir = self.project_root / "scripts"
        if scripts_dir.exists():
            for py_file in scripts_dir.rglob("*.py"):
                if "__pycache__" in str(py_file):
                    continue
                python_files.append(py_file)

        self.logger.info(f"找到 {len(python_files)} 个Python文件")

        total_functions = 0

        for py_file in python_files:
            functions = self._analyze_file(py_file)
            total_functions += len(functions)

            for func in functions:
                if self._is_long_function(func):
                    long_func = self._create_long_function(func)
                    self.long_functions.append(long_func)

        # 计算摘要
        summary = self._calculate_summary()

        return DetectionReport(
            timestamp=datetime.now().isoformat(),
            project_root=str(self.project_root),
            max_lines=self.max_lines,
            max_complexity=self.max_complexity,
            total_functions=total_functions,
            long_functions=self.long_functions,
            summary=summary
        )

    def _analyze_file(self, file_path: Path) -> List[FunctionMetrics]:
        """分析单个文件"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            tree = ast.parse(content)
            analyzer = FunctionAnalyzer(str(file_path), content)
            analyzer.visit(tree)

            return analyzer.functions
        except SyntaxError as e:
            self.logger.warning(f"语法错误 {file_path}: {e}")
            return []
        except Exception as e:
            self.logger.error(f"分析文件失败 {file_path}: {e}")
            return []

    def _is_long_function(self, metrics: FunctionMetrics) -> bool:
        """判断是否为长函数"""
        return (metrics.line_count > self.max_lines or
                metrics.complexity > self.max_complexity or
                metrics.parameter_count > 5 or
                metrics.return_count > 3)

    def _create_long_function(self, metrics: FunctionMetrics) -> LongFunction:
        """创建长函数对象"""
        issues = []
        suggestions = []

        # 确定严重程度
        if metrics.line_count > self.max_lines * 2 or metrics.complexity > self.max_complexity * 2:
            severity = ComplexityLevel.VERY_HIGH
        elif metrics.line_count > self.max_lines or metrics.complexity > self.max_complexity:
            severity = ComplexityLevel.HIGH
        elif metrics.line_count > self.max_lines * 0.7 or metrics.complexity > self.max_complexity * 0.7:
            severity = ComplexityLevel.MEDIUM
        else:
            severity = ComplexityLevel.LOW

        # 分析具体问题
        if metrics.line_count > self.max_lines:
            issues.append(f"函数过长: {metrics.line_count} 行 (阈值: {self.max_lines})")
            suggestions.append("考虑将函数拆分为多个小函数")
            suggestions.append("提取重复代码到辅助函数")

        if metrics.complexity > self.max_complexity:
            issues.append(f"复杂度过高: {metrics.complexity} (阈值: {self.max_complexity})")
            suggestions.append("简化条件逻辑")
            suggestions.append("使用策略模式替代多重条件")

        if metrics.parameter_count > 5:
            issues.append(f"参数过多: {metrics.parameter_count} 个")
            suggestions.append("使用对象封装参数")
            suggestions.append("考虑使用建造者模式")

        if metrics.return_count > 3:
            issues.append(f"返回点过多: {metrics.return_count} 个")
            suggestions.append("统一返回逻辑")
            suggestions.append("使用提前返回模式")

        if metrics.nested_function_count > 2:
            issues.append(f"嵌套函数过多: {metrics.nested_function_count} 个")
            suggestions.append("将嵌套函数提取为独立函数")

        return LongFunction(
            metrics=metrics,
            severity=severity,
            issues=issues,
            suggestions=suggestions
        )

    def _calculate_summary(self) -> Dict[str, Any]:
        """计算摘要"""
        if not self.long_functions:
            return {
                "long_function_count": 0,
                "percentage": 0.0,
                "by_severity": {},
                "by_type": {},
                "average_lines": 0,
                "average_complexity": 0
            }

        by_severity: Dict[str, int] = {}
        by_type: Dict[str, int] = {}
        total_lines = 0
        total_complexity = 0

        for func in self.long_functions:
            sev = func.severity.value
            by_severity[sev] = by_severity.get(sev, 0) + 1

            ftype = func.metrics.function_type.value
            by_type[ftype] = by_type.get(ftype, 0) + 1

            total_lines += func.metrics.line_count
            total_complexity += func.metrics.complexity

        return {
            "long_function_count": len(self.long_functions),
            "by_severity": by_severity,
            "by_type": by_type,
            "average_lines": round(total_lines / len(self.long_functions), 1),
            "average_complexity": round(total_complexity / len(self.long_functions), 1)
        }

    def print_report(self, report: DetectionReport):
        """打印报告"""
        print("\n" + "=" * 80)
        print("长函数检测报告")
        print("=" * 80)
        print(f"项目根目录: {report.project_root}")
        print(f"检测时间: {report.timestamp}")
        print(f"行数阈值: {report.max_lines}")
        print(f"复杂度阈值: {report.max_complexity}")
        print(f"总函数数: {report.total_functions}")
        print(f"长函数数: {len(report.long_functions)}")

        print("\n" + "-" * 80)
        print("摘要")
        print("-" * 80)
        for key, value in report.summary.items():
            if isinstance(value, dict):
                print(f"\n{key}:")
                for k, v in value.items():
                    print(f"  {k}: {v}")
            else:
                print(f"  {key}: {value}")

        if report.long_functions:
            print("\n" + "-" * 80)
            print("长函数列表")
            print("-" * 80)

            # 按严重程度排序
            severity_order = {
                ComplexityLevel.VERY_HIGH: 0,
                ComplexityLevel.HIGH: 1,
                ComplexityLevel.MEDIUM: 2,
                ComplexityLevel.LOW: 3
            }

            sorted_functions = sorted(
                report.long_functions,
                key=lambda f: severity_order.get(f.severity, 99)
            )

            for i, func in enumerate(sorted_functions, 1):
                severity_icon = {
                    ComplexityLevel.VERY_HIGH: "🔴",
                    ComplexityLevel.HIGH: "🟠",
                    ComplexityLevel.MEDIUM: "🟡",
                    ComplexityLevel.LOW: "🔵"
                }.get(func.severity, "⚪")

                print(f"\n{i}. {severity_icon} {func.metrics.name}")
                print(f"   文件: {func.metrics.file_path}:{func.metrics.line_start}")
                print(f"   行数: {func.metrics.line_count} (文档: {func.metrics.docstring_lines})")
                print(f"   复杂度: {func.metrics.complexity}")
                print(f"   参数: {func.metrics.parameter_count}, 返回: {func.metrics.return_count}")
                print(f"   类型: {func.metrics.function_type.value}")

                if func.issues:
                    print(f"   问题:")
                    for issue in func.issues:
                        print(f"     - {issue}")

                if func.suggestions:
                    print(f"   建议:")
                    for suggestion in func.suggestions[:3]:
                        print(f"     - {suggestion}")

    def save_report(self, report: DetectionReport, output_dir: Optional[Path] = None) -> Path:
        """保存报告"""
        if output_dir is None:
            output_dir = get_path_config().REPORTS_DIR
        output_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_path = output_dir / f"long_functions_{timestamp}.json"

        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report.to_dict(), f, indent=2, ensure_ascii=False)

        # 同时保存最新报告
        latest_path = output_dir / "long_functions_latest.json"
        with open(latest_path, 'w', encoding='utf-8') as f:
            json.dump(report.to_dict(), f, indent=2, ensure_ascii=False)

        self.logger.info(f"报告已保存: {report_path}")
        return report_path


def setup_logger(verbose: bool = False) -> logging.Logger:
    """配置日志记录器"""
    logger = logging.getLogger("LongFunctionDetector")
    logger.setLevel(logging.DEBUG if verbose else logging.INFO)

    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(logging.DEBUG if verbose else logging.INFO)
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    return logger


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="长函数检测器",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python detect_long_functions.py
  python detect_long_functions.py --max-lines 50
  python detect_long_functions.py --max-complexity 10
  python detect_long_functions.py --output json --output-file result.json
        """
    )

    parser.add_argument(
        "--max-lines",
        type=int,
        default=LongFunctionDetector.DEFAULT_MAX_LINES,
        help=f"最大行数阈值 (默认: {LongFunctionDetector.DEFAULT_MAX_LINES})"
    )

    parser.add_argument(
        "--max-complexity",
        type=int,
        default=LongFunctionDetector.DEFAULT_MAX_COMPLEXITY,
        help=f"最大复杂度阈值 (默认: {LongFunctionDetector.DEFAULT_MAX_COMPLEXITY})"
    )

    parser.add_argument(
        "--output",
        choices=["console", "json"],
        default="console",
        help="输出格式 (默认: console)"
    )

    parser.add_argument(
        "--output-file",
        type=str,
        help="输出文件路径"
    )

    parser.add_argument(
        "--verbose",
        action="store_true",
        help="启用详细日志输出"
    )

    args = parser.parse_args()

    # 配置日志
    logger = setup_logger(args.verbose)

    # 运行检测
    detector = LongFunctionDetector(
        max_lines=args.max_lines,
        max_complexity=args.max_complexity,
        logger=logger
    )
    report = detector.detect_project()

    # 打印报告
    detector.print_report(report)

    # 保存报告
    report_path = detector.save_report(report)
    print(f"\n报告已保存到: {report_path}")

    # 输出JSON结果
    if args.output == "json":
        output_data = json.dumps(report.to_dict(), ensure_ascii=False, indent=2)

        if args.output_file:
            output_path = Path(args.output_file)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(output_data)
            print(f"\nJSON结果已保存到: {output_path}")
        else:
            print("\nJSON结果:")
            print(output_data)

    return 0 if len(report.long_functions) == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
