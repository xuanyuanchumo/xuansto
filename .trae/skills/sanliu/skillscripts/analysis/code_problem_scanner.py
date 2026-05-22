#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
代码问题扫描器

扫描三省六部项目的代码问题，包括：
- 未使用变量
- 未使用导入
- 未使用函数
- 未使用类
- 代码异味检测

使用示例:
    python code_problem_scanner.py
    python code_problem_scanner.py --output json --output-file result.json
    python code_problem_scanner.py --fix
    python code_problem_scanner.py --verbose
"""

import os
import sys
import ast
import re
import argparse
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Set, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class ProblemType(Enum):
    """问题类型枚举"""
    UNUSED_VARIABLE = "unused_variable"
    UNUSED_IMPORT = "unused_import"
    UNUSED_FUNCTION = "unused_function"
    UNUSED_CLASS = "unused_class"
    CODE_SMELL = "code_smell"
    DUPLICATE_CODE = "duplicate_code"


class Severity(Enum):
    """严重程度枚举"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


@dataclass
class CodeProblem:
    """代码问题数据类"""
    file_path: str
    line_number: int
    problem_type: ProblemType
    severity: Severity
    description: str
    code_snippet: str = ""
    suggestion: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "file_path": self.file_path,
            "line_number": self.line_number,
            "problem_type": self.problem_type.value,
            "severity": self.severity.value,
            "description": self.description,
            "code_snippet": self.code_snippet,
            "suggestion": self.suggestion
        }


@dataclass
class ScanResult:
    """扫描结果数据类"""
    file_path: str
    problems: List[CodeProblem] = field(default_factory=list)
    lines_scanned: int = 0
    scan_time_ms: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "file_path": self.file_path,
            "problems": [p.to_dict() for p in self.problems],
            "lines_scanned": self.lines_scanned,
            "scan_time_ms": round(self.scan_time_ms, 2),
            "problem_count": len(self.problems)
        }


@dataclass
class ScanReport:
    """扫描报告数据类"""
    timestamp: str
    project_root: str
    total_files: int
    total_problems: int
    results: List[ScanResult]
    summary: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "timestamp": self.timestamp,
            "project_root": self.project_root,
            "total_files": self.total_files,
            "total_problems": self.total_problems,
            "summary": self.summary,
            "results": [r.to_dict() for r in self.results]
        }


class CodeProblemScanner:
    """代码问题扫描器"""

    # 代码异味模式
    CODE_SMELL_PATTERNS = {
        "too_many_arguments": {
            "pattern": r"def\s+\w+\s*\([^)]{80,}\)",
            "description": "函数参数过多",
            "severity": Severity.MEDIUM,
            "suggestion": "考虑使用对象封装参数"
        },
        "long_line": {
            "pattern": r".{121,}",
            "description": "行长度超过120字符",
            "severity": Severity.LOW,
            "suggestion": "拆分行或简化代码"
        },
        "todo_comment": {
            "pattern": r"#\s*(TODO|FIXME|XXX|HACK)",
            "description": "发现待办事项注释",
            "severity": Severity.INFO,
            "suggestion": "及时处理待办事项"
        },
        "bare_except": {
            "pattern": r"except\s*:",
            "description": "使用裸异常捕获",
            "severity": Severity.HIGH,
            "suggestion": "捕获具体的异常类型"
        },
        "print_statement": {
            "pattern": r"^\s*print\s*\(",
            "description": "使用print语句",
            "severity": Severity.LOW,
            "suggestion": "使用日志记录器替代print"
        },
        "mutable_default": {
            "pattern": r"def\s+\w+\s*\([^)]*=\s*(\[\s*\]|\{\s*\})",
            "description": "使用可变默认参数",
            "severity": Severity.HIGH,
            "suggestion": "使用None作为默认值，在函数内部初始化"
        }
    }

    def __init__(self, project_root: Optional[Path] = None,
                 logger: Optional[logging.Logger] = None):
        self.project_root = project_root or get_path_config().SKILL_ROOT
        self.logger = logger or logging.getLogger(__name__)
        self.results: List[ScanResult] = []

    def scan_project(self, include_tests: bool = False) -> ScanReport:
        """扫描整个项目"""
        self.logger.info("开始扫描项目...")

        python_files = []

        # 扫描后端
        backend_dir = self.project_root / "backend"
        if backend_dir.exists():
            for py_file in backend_dir.rglob("*.py"):
                if not include_tests and "test" in py_file.name.lower():
                    continue
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

        for py_file in python_files:
            result = self.scan_file(py_file)
            if result.problems:
                self.results.append(result)

        # 计算摘要
        total_problems = sum(len(r.problems) for r in self.results)
        problems_by_type: Dict[str, int] = {}
        problems_by_severity: Dict[str, int] = {}

        for result in self.results:
            for problem in result.problems:
                pt = problem.problem_type.value
                problems_by_type[pt] = problems_by_type.get(pt, 0) + 1

                sev = problem.severity.value
                problems_by_severity[sev] = problems_by_severity.get(sev, 0) + 1

        summary = {
            "files_scanned": len(python_files),
            "files_with_problems": len(self.results),
            "total_problems": total_problems,
            "problems_by_type": problems_by_type,
            "problems_by_severity": problems_by_severity
        }

        return ScanReport(
            timestamp=datetime.now().isoformat(),
            project_root=str(self.project_root),
            total_files=len(python_files),
            total_problems=total_problems,
            results=self.results,
            summary=summary
        )

    def scan_file(self, file_path: Path) -> ScanResult:
        """扫描单个文件"""
        import time
        start_time = time.perf_counter()

        result = ScanResult(file_path=str(file_path))

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                lines = content.split('\n')
                result.lines_scanned = len(lines)

            # 解析AST
            try:
                tree = ast.parse(content)
            except SyntaxError as e:
                result.problems.append(CodeProblem(
                    file_path=str(file_path),
                    line_number=e.lineno or 1,
                    problem_type=ProblemType.CODE_SMELL,
                    severity=Severity.CRITICAL,
                    description=f"语法错误: {e.msg}",
                    suggestion="修复语法错误"
                ))
                return result

            # 检查未使用的导入
            result.problems.extend(self._check_unused_imports(file_path, tree, lines))

            # 检查未使用的变量
            result.problems.extend(self._check_unused_variables(file_path, tree, lines))

            # 检查未使用的函数
            result.problems.extend(self._check_unused_functions(file_path, tree, lines))

            # 检查未使用的类
            result.problems.extend(self._check_unused_classes(file_path, tree, lines))

            # 检查代码异味
            result.problems.extend(self._check_code_smells(file_path, content, lines))

        except Exception as e:
            self.logger.error(f"扫描文件失败 {file_path}: {e}")

        end_time = time.perf_counter()
        result.scan_time_ms = (end_time - start_time) * 1000

        return result

    def _check_unused_imports(self, file_path: Path, tree: ast.AST,
                               lines: List[str]) -> List[CodeProblem]:
        """检查未使用的导入"""
        problems = []

        imports: Dict[str, Tuple[int, str]] = {}
        used_names: Set[str] = set()

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    name = alias.asname if alias.asname else alias.name
                    imports[name] = (node.lineno, alias.name)
            elif isinstance(node, ast.ImportFrom):
                for alias in node.names:
                    name = alias.asname if alias.asname else alias.name
                    imports[name] = (node.lineno, alias.name)
            elif isinstance(node, ast.Name):
                used_names.add(node.id)
            elif isinstance(node, ast.Attribute):
                # 处理模块属性访问
                if isinstance(node.value, ast.Name):
                    used_names.add(node.value.id)

        for name, (lineno, original_name) in imports.items():
            if name not in used_names and not name.startswith('_'):
                # 排除一些特殊情况
                if original_name not in ['TYPE_CHECKING', 'annotations']:
                    problems.append(CodeProblem(
                        file_path=str(file_path),
                        line_number=lineno,
                        problem_type=ProblemType.UNUSED_IMPORT,
                        severity=Severity.MEDIUM,
                        description=f"未使用的导入: {original_name}",
                        code_snippet=lines[lineno - 1].strip() if lineno <= len(lines) else "",
                        suggestion=f"删除未使用的导入: {original_name}"
                    ))

        return problems

    def _check_unused_variables(self, file_path: Path, tree: ast.AST,
                                 lines: List[str]) -> List[CodeProblem]:
        """检查未使用的变量"""
        problems = []

        defined_vars: Dict[str, Tuple[int, str]] = {}
        used_vars: Set[str] = set()

        for node in ast.walk(tree):
            if isinstance(node, ast.Name):
                if isinstance(node.ctx, ast.Store):
                    defined_vars[node.id] = (node.lineno, node.id)
                elif isinstance(node.ctx, ast.Load):
                    used_vars.add(node.id)
            elif isinstance(node, ast.FunctionDef):
                # 函数参数不算未使用
                for arg in node.args.args:
                    used_vars.add(arg.arg)
                for arg in node.args.kwonlyargs:
                    used_vars.add(arg.arg)

        # 排除特殊变量
        excluded = {'_', 'e', 'i', 'j', 'k', 'x', 'y', 'z', 'exc'}

        for var, (lineno, name) in defined_vars.items():
            if var not in used_vars and var not in excluded and not var.startswith('_'):
                problems.append(CodeProblem(
                    file_path=str(file_path),
                    line_number=lineno,
                    problem_type=ProblemType.UNUSED_VARIABLE,
                    severity=Severity.LOW,
                    description=f"未使用的变量: {name}",
                    code_snippet=lines[lineno - 1].strip() if lineno <= len(lines) else "",
                    suggestion=f"删除未使用的变量或使用它"
                ))

        return problems

    def _check_unused_functions(self, file_path: Path, tree: ast.AST,
                                 lines: List[str]) -> List[CodeProblem]:
        """检查未使用的函数"""
        problems = []

        defined_funcs: Dict[str, Tuple[int, ast.FunctionDef]] = {}
        used_funcs: Set[str] = set()

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                # 排除特殊方法
                if not node.name.startswith('_') and not node.name.startswith('test_'):
                    defined_funcs[node.name] = (node.lineno, node)
            elif isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name):
                    used_funcs.add(node.func.id)
                elif isinstance(node.func, ast.Attribute):
                    used_funcs.add(node.func.attr)

        # 只检查模块级别的函数
        for func_name, (lineno, func_node) in defined_funcs.items():
            if func_name not in used_funcs:
                # 检查是否是入口函数
                if func_name not in ['main', 'run', 'start']:
                    problems.append(CodeProblem(
                        file_path=str(file_path),
                        line_number=lineno,
                        problem_type=ProblemType.UNUSED_FUNCTION,
                        severity=Severity.MEDIUM,
                        description=f"未使用的函数: {func_name}",
                        code_snippet=lines[lineno - 1].strip() if lineno <= len(lines) else "",
                        suggestion=f"删除未使用的函数或添加调用"
                    ))

        return problems

    def _check_unused_classes(self, file_path: Path, tree: ast.AST,
                               lines: List[str]) -> List[CodeProblem]:
        """检查未使用的类"""
        problems = []

        defined_classes: Dict[str, Tuple[int, ast.ClassDef]] = {}
        used_classes: Set[str] = set()

        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                if not node.name.startswith('_'):
                    defined_classes[node.name] = (node.lineno, node)
            elif isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name):
                    used_classes.add(node.func.id)

        for class_name, (lineno, class_node) in defined_classes.items():
            if class_name not in used_classes:
                problems.append(CodeProblem(
                    file_path=str(file_path),
                    line_number=lineno,
                    problem_type=ProblemType.UNUSED_CLASS,
                    severity=Severity.MEDIUM,
                    description=f"未使用的类: {class_name}",
                    code_snippet=lines[lineno - 1].strip() if lineno <= len(lines) else "",
                    suggestion=f"删除未使用的类或添加实例化"
                ))

        return problems

    def _check_code_smells(self, file_path: Path, content: str,
                           lines: List[str]) -> List[CodeProblem]:
        """检查代码异味"""
        problems = []

        for i, line in enumerate(lines, 1):
            for smell_name, smell_config in self.CODE_SMELL_PATTERNS.items():
                if re.search(smell_config["pattern"], line):
                    # 排除注释行中的匹配
                    if smell_name != "todo_comment" and line.strip().startswith('#'):
                        continue

                    problems.append(CodeProblem(
                        file_path=str(file_path),
                        line_number=i,
                        problem_type=ProblemType.CODE_SMELL,
                        severity=smell_config["severity"],
                        description=smell_config["description"],
                        code_snippet=line.strip(),
                        suggestion=smell_config["suggestion"]
                    ))

        return problems

    def print_report(self, report: ScanReport):
        """打印报告"""
        print("\n" + "=" * 80)
        print("代码问题扫描报告")
        print("=" * 80)
        print(f"项目根目录: {report.project_root}")
        print(f"扫描时间: {report.timestamp}")
        print(f"扫描文件数: {report.total_files}")
        print(f"发现问题数: {report.total_problems}")

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

        # 按严重程度排序
        severity_order = {
            Severity.CRITICAL: 0,
            Severity.HIGH: 1,
            Severity.MEDIUM: 2,
            Severity.LOW: 3,
            Severity.INFO: 4
        }

        all_problems = []
        for result in report.results:
            for problem in result.problems:
                all_problems.append(problem)

        all_problems.sort(key=lambda p: severity_order.get(p.severity, 99))

        if all_problems:
            print("\n" + "-" * 80)
            print("发现的问题")
            print("-" * 80)

            for problem in all_problems[:50]:  # 限制显示数量
                severity_icon = {
                    Severity.CRITICAL: "🔴",
                    Severity.HIGH: "🟠",
                    Severity.MEDIUM: "🟡",
                    Severity.LOW: "🔵",
                    Severity.INFO: "⚪"
                }.get(problem.severity, "⚪")

                print(f"\n{severity_icon} [{problem.severity.value.upper()}] {problem.problem_type.value}")
                print(f"   文件: {problem.file_path}:{problem.line_number}")
                print(f"   描述: {problem.description}")
                if problem.code_snippet:
                    print(f"   代码: {problem.code_snippet[:80]}")
                if problem.suggestion:
                    print(f"   建议: {problem.suggestion}")

            if len(all_problems) > 50:
                print(f"\n... 还有 {len(all_problems) - 50} 个问题未显示")

    def save_report(self, report: ScanReport, output_dir: Optional[Path] = None) -> Path:
        """保存报告"""
        if output_dir is None:
            output_dir = get_path_config().REPORTS_DIR
        output_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_path = output_dir / f"code_problem_scan_{timestamp}.json"

        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report.to_dict(), f, indent=2, ensure_ascii=False)

        # 同时保存最新报告
        latest_path = output_dir / "code_problem_scan_latest.json"
        with open(latest_path, 'w', encoding='utf-8') as f:
            json.dump(report.to_dict(), f, indent=2, ensure_ascii=False)

        self.logger.info(f"报告已保存: {report_path}")
        return report_path

    def fix_problems(self, report: ScanReport, dry_run: bool = True) -> List[str]:
        """自动修复问题"""
        fixed_files = []

        for result in report.results:
            file_path = Path(result.file_path)
            if not file_path.exists():
                continue

            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    lines = f.readlines()

                original_lines = lines.copy()
                lines_to_remove = set()

                for problem in result.problems:
                    if problem.problem_type == ProblemType.UNUSED_IMPORT:
                        if problem.line_number > 0 and problem.line_number <= len(lines):
                            lines_to_remove.add(problem.line_number - 1)

                if lines_to_remove and not dry_run:
                    new_lines = [line for i, line in enumerate(lines) if i not in lines_to_remove]
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.writelines(new_lines)
                    fixed_files.append(str(file_path))
                    self.logger.info(f"已修复: {file_path}")
                elif lines_to_remove:
                    self.logger.info(f"将修复 {file_path}: 删除 {len(lines_to_remove)} 行")

            except Exception as e:
                self.logger.error(f"修复文件失败 {file_path}: {e}")

        return fixed_files


def setup_logger(verbose: bool = False) -> logging.Logger:
    """配置日志记录器"""
    logger = logging.getLogger("CodeProblemScanner")
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
        description="代码问题扫描器",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python code_problem_scanner.py
  python code_problem_scanner.py --output json --output-file result.json
  python code_problem_scanner.py --fix
  python code_problem_scanner.py --verbose
        """
    )

    parser.add_argument(
        "--include-tests",
        action="store_true",
        help="包含测试文件"
    )

    parser.add_argument(
        "--fix",
        action="store_true",
        help="自动修复问题"
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="模拟修复（不实际修改文件）"
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

    # 运行扫描
    scanner = CodeProblemScanner(logger=logger)
    report = scanner.scan_project(include_tests=args.include_tests)

    # 打印报告
    scanner.print_report(report)

    # 保存报告
    report_path = scanner.save_report(report)
    print(f"\n报告已保存到: {report_path}")

    # 自动修复
    if args.fix or args.dry_run:
        print("\n" + "=" * 80)
        print("自动修复")
        print("=" * 80)
        fixed = scanner.fix_problems(report, dry_run=args.dry_run)
        if fixed:
            print(f"已修复 {len(fixed)} 个文件")
            for f in fixed:
                print(f"  - {f}")
        else:
            print("没有可修复的问题")

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

    return 0 if report.total_problems == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
