#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
嵌套层级分析器

分析三省六部项目代码的嵌套层级，识别过深的嵌套结构，提供重构建议。
支持Python代码的if/for/while/try等语句的嵌套深度分析。

使用示例:
    python nesting_analyzer.py
    python nesting_analyzer.py --max-depth 4
    python nesting_analyzer.py --output json --output-file result.json
    python nesting_analyzer.py --verbose
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


class NestingType(Enum):
    """嵌套类型枚举"""
    IF = "if"
    FOR = "for"
    WHILE = "while"
    TRY = "try"
    WITH = "with"
    FUNCTION = "function"
    CLASS = "class"
    COMPREHENSION = "comprehension"


class Severity(Enum):
    """严重程度枚举"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass
class NestingLocation:
    """嵌套位置数据类"""
    file_path: str
    line_start: int
    line_end: int
    nesting_type: NestingType
    depth: int
    context: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "file_path": self.file_path,
            "line_start": self.line_start,
            "line_end": self.line_end,
            "nesting_type": self.nesting_type.value,
            "depth": self.depth,
            "context": self.context[:100]  # 限制长度
        }


@dataclass
class DeepNesting:
    """深度嵌套数据类"""
    location: NestingLocation
    severity: Severity
    issues: List[str] = field(default_factory=list)
    suggestions: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "location": self.location.to_dict(),
            "severity": self.severity.value,
            "issues": self.issues,
            "suggestions": self.suggestions
        }


@dataclass
class FileNestingReport:
    """文件嵌套报告数据类"""
    file_path: str
    max_depth: int
    deep_nestings: List[DeepNesting]
    nesting_stats: Dict[str, int] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "file_path": self.file_path,
            "max_depth": self.max_depth,
            "deep_nesting_count": len(self.deep_nestings),
            "nesting_stats": self.nesting_stats,
            "deep_nestings": [n.to_dict() for n in self.deep_nestings]
        }


@dataclass
class AnalysisReport:
    """分析报告数据类"""
    timestamp: str
    project_root: str
    max_allowed_depth: int
    total_files: int
    files_with_deep_nesting: int
    file_reports: List[FileNestingReport]
    summary: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "timestamp": self.timestamp,
            "project_root": self.project_root,
            "max_allowed_depth": self.max_allowed_depth,
            "total_files": self.total_files,
            "files_with_deep_nesting": self.files_with_deep_nesting,
            "summary": self.summary,
            "file_reports": [r.to_dict() for r in self.file_reports]
        }


class NestingAnalyzer(ast.NodeVisitor):
    """嵌套分析器"""

    def __init__(self, file_path: str, content: str, max_depth: int = 4):
        self.file_path = file_path
        self.content = content
        self.lines = content.split('\n')
        self.max_depth = max_depth
        self.current_depth = 0
        self.max_depth_found = 0
        self.deep_nestings: List[DeepNesting] = []
        self.nesting_stats: Dict[str, int] = {}
        self.nesting_stack: List[Tuple[ast.AST, int]] = []

    def analyze(self) -> FileNestingReport:
        """分析文件"""
        try:
            tree = ast.parse(self.content)
            self.visit(tree)
        except SyntaxError as e:
            logging.warning(f"语法错误 {self.file_path}: {e}")

        return FileNestingReport(
            file_path=self.file_path,
            max_depth=self.max_depth_found,
            deep_nestings=self.deep_nestings,
            nesting_stats=self.nesting_stats
        )

    def _get_context(self, node: ast.AST) -> str:
        """获取代码上下文"""
        if hasattr(node, 'lineno') and node.lineno > 0:
            line_idx = node.lineno - 1
            if line_idx < len(self.lines):
                return self.lines[line_idx].strip()
        return ""

    def _get_nesting_type(self, node: ast.AST) -> Optional[NestingType]:
        """获取嵌套类型"""
        if isinstance(node, ast.If):
            return NestingType.IF
        elif isinstance(node, ast.For):
            return NestingType.FOR
        elif isinstance(node, ast.While):
            return NestingType.WHILE
        elif isinstance(node, ast.Try):
            return NestingType.TRY
        elif isinstance(node, ast.With):
            return NestingType.WITH
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            return NestingType.FUNCTION
        elif isinstance(node, ast.ClassDef):
            return NestingType.CLASS
        elif isinstance(node, (ast.ListComp, ast.SetComp, ast.GeneratorExp)):
            return NestingType.COMPREHENSION
        elif isinstance(node, ast.DictComp):
            return NestingType.COMPREHENSION
        return None

    def _check_deep_nesting(self, node: ast.AST):
        """检查深度嵌套"""
        nesting_type = self._get_nesting_type(node)
        if not nesting_type:
            return

        # 更新统计
        type_key = nesting_type.value
        self.nesting_stats[type_key] = self.nesting_stats.get(type_key, 0) + 1

        # 检查是否超过阈值
        if self.current_depth > self.max_depth:
            self.max_depth_found = max(self.max_depth_found, self.current_depth)

            # 确定严重程度
            if self.current_depth > self.max_depth + 2:
                severity = Severity.CRITICAL
            elif self.current_depth > self.max_depth + 1:
                severity = Severity.HIGH
            else:
                severity = Severity.MEDIUM

            # 获取行号
            line_start = getattr(node, 'lineno', 1)
            line_end = getattr(node, 'end_lineno', line_start)

            location = NestingLocation(
                file_path=self.file_path,
                line_start=line_start,
                line_end=line_end,
                nesting_type=nesting_type,
                depth=self.current_depth,
                context=self._get_context(node)
            )

            issues = [f"嵌套深度 {self.current_depth} 超过阈值 {self.max_depth}"]
            suggestions = self._generate_suggestions(node, nesting_type)

            deep_nesting = DeepNesting(
                location=location,
                severity=severity,
                issues=issues,
                suggestions=suggestions
            )

            self.deep_nestings.append(deep_nesting)

    def _generate_suggestions(self, node: ast.AST, nesting_type: NestingType) -> List[str]:
        """生成重构建议"""
        suggestions = []

        if nesting_type == NestingType.IF:
            suggestions.append("使用卫语句提前返回")
            suggestions.append("将条件逻辑提取为函数")
        elif nesting_type in (NestingType.FOR, NestingType.WHILE):
            suggestions.append("将循环逻辑提取为函数")
            suggestions.append("考虑使用列表推导式或生成器表达式")
        elif nesting_type == NestingType.TRY:
            suggestions.append("将异常处理提取为独立函数")
        elif nesting_type == NestingType.FUNCTION:
            suggestions.append("拆分函数为更小的函数")
            suggestions.append("使用策略模式替代条件逻辑")
        elif nesting_type == NestingType.CLASS:
            suggestions.append("考虑使用组合替代继承")

        suggestions.append("使用提取方法重构")
        return suggestions

    def _visit_nested(self, node: ast.AST):
        """访问嵌套节点"""
        nesting_type = self._get_nesting_type(node)

        if nesting_type:
            self.current_depth += 1
            self._check_deep_nesting(node)

        self.generic_visit(node)

        if nesting_type:
            self.current_depth -= 1

    def visit_If(self, node: ast.If):
        self._visit_nested(node)

    def visit_For(self, node: ast.For):
        self._visit_nested(node)

    def visit_While(self, node: ast.While):
        self._visit_nested(node)

    def visit_Try(self, node: ast.Try):
        self._visit_nested(node)

    def visit_With(self, node: ast.With):
        self._visit_nested(node)

    def visit_FunctionDef(self, node: ast.FunctionDef):
        self._visit_nested(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef):
        self._visit_nested(node)

    def visit_ClassDef(self, node: ast.ClassDef):
        self._visit_nested(node)

    def visit_ListComp(self, node: ast.ListComp):
        self._visit_nested(node)

    def visit_SetComp(self, node: ast.SetComp):
        self._visit_nested(node)

    def visit_DictComp(self, node: ast.DictComp):
        self._visit_nested(node)

    def visit_GeneratorExp(self, node: ast.GeneratorExp):
        self._visit_nested(node)


class NestingDepthAnalyzer:
    """嵌套深度分析器"""

    DEFAULT_MAX_DEPTH = 4

    def __init__(self, project_root: Optional[Path] = None,
                 max_depth: int = DEFAULT_MAX_DEPTH,
                 logger: Optional[logging.Logger] = None):
        self.project_root = project_root or get_path_config().SKILL_ROOT
        self.max_depth = max_depth
        self.logger = logger or logging.getLogger(__name__)
        self.file_reports: List[FileNestingReport] = []

    def analyze_project(self) -> AnalysisReport:
        """分析整个项目"""
        self.logger.info("开始分析嵌套层级...")

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

        for py_file in python_files:
            report = self._analyze_file(py_file)
            if report.deep_nestings or report.max_depth > 0:
                self.file_reports.append(report)

        # 计算摘要
        summary = self._calculate_summary()

        return AnalysisReport(
            timestamp=datetime.now().isoformat(),
            project_root=str(self.project_root),
            max_allowed_depth=self.max_depth,
            total_files=len(python_files),
            files_with_deep_nesting=len(self.file_reports),
            file_reports=self.file_reports,
            summary=summary
        )

    def _analyze_file(self, file_path: Path) -> FileNestingReport:
        """分析单个文件"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            analyzer = NestingAnalyzer(str(file_path), content, self.max_depth)
            return analyzer.analyze()
        except Exception as e:
            self.logger.error(f"分析文件失败 {file_path}: {e}")
            return FileNestingReport(
                file_path=str(file_path),
                max_depth=0,
                deep_nestings=[],
                nesting_stats={}
            )

    def _calculate_summary(self) -> Dict[str, Any]:
        """计算摘要"""
        if not self.file_reports:
            return {
                "total_deep_nestings": 0,
                "max_depth_found": 0,
                "by_severity": {},
                "by_type": {},
                "files_needing_attention": 0
            }

        total_deep_nestings = sum(len(r.deep_nestings) for r in self.file_reports)
        max_depth_found = max(r.max_depth for r in self.file_reports)

        by_severity: Dict[str, int] = {}
        by_type: Dict[str, int] = {}

        for report in self.file_reports:
            for nesting in report.deep_nestings:
                sev = nesting.severity.value
                by_severity[sev] = by_severity.get(sev, 0) + 1

                ntype = nesting.location.nesting_type.value
                by_type[ntype] = by_type.get(ntype, 0) + 1

        files_needing_attention = sum(
            1 for r in self.file_reports
            if any(n.severity in (Severity.CRITICAL, Severity.HIGH) for n in r.deep_nestings)
        )

        return {
            "total_deep_nestings": total_deep_nestings,
            "max_depth_found": max_depth_found,
            "by_severity": by_severity,
            "by_type": by_type,
            "files_needing_attention": files_needing_attention
        }

    def print_report(self, report: AnalysisReport):
        """打印报告"""
        print("\n" + "=" * 80)
        print("嵌套层级分析报告")
        print("=" * 80)
        print(f"项目根目录: {report.project_root}")
        print(f"分析时间: {report.timestamp}")
        print(f"最大允许深度: {report.max_allowed_depth}")
        print(f"总文件数: {report.total_files}")
        print(f"存在深度嵌套的文件数: {report.files_with_deep_nesting}")

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

        if report.file_reports:
            print("\n" + "-" * 80)
            print("深度嵌套详情")
            print("-" * 80)

            # 按严重程度排序
            severity_order = {
                Severity.CRITICAL: 0,
                Severity.HIGH: 1,
                Severity.MEDIUM: 2,
                Severity.LOW: 3
            }

            all_nestings = []
            for file_report in report.file_reports:
                for nesting in file_report.deep_nestings:
                    all_nestings.append((file_report, nesting))

            all_nestings.sort(
                key=lambda x: severity_order.get(x[1].severity, 99)
            )

            for i, (file_report, nesting) in enumerate(all_nestings[:30], 1):
                severity_icon = {
                    Severity.CRITICAL: "🔴",
                    Severity.HIGH: "🟠",
                    Severity.MEDIUM: "🟡",
                    Severity.LOW: "🔵"
                }.get(nesting.severity, "⚪")

                print(f"\n{i}. {severity_icon} [{nesting.severity.value.upper()}]")
                print(f"   文件: {nesting.location.file_path}:{nesting.location.line_start}")
                print(f"   类型: {nesting.location.nesting_type.value}")
                print(f"   深度: {nesting.location.depth}")
                if nesting.location.context:
                    print(f"   上下文: {nesting.location.context[:60]}")

                if nesting.issues:
                    print(f"   问题:")
                    for issue in nesting.issues:
                        print(f"     - {issue}")

                if nesting.suggestions:
                    print(f"   建议:")
                    for suggestion in nesting.suggestions[:2]:
                        print(f"     - {suggestion}")

            if len(all_nestings) > 30:
                print(f"\n... 还有 {len(all_nestings) - 30} 个深度嵌套未显示")

    def save_report(self, report: AnalysisReport, output_dir: Optional[Path] = None) -> Path:
        """保存报告"""
        if output_dir is None:
            output_dir = get_path_config().REPORTS_DIR
        output_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_path = output_dir / f"nesting_analysis_{timestamp}.json"

        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report.to_dict(), f, indent=2, ensure_ascii=False)

        # 同时保存最新报告
        latest_path = output_dir / "nesting_analysis_latest.json"
        with open(latest_path, 'w', encoding='utf-8') as f:
            json.dump(report.to_dict(), f, indent=2, ensure_ascii=False)

        self.logger.info(f"报告已保存: {report_path}")
        return report_path


def setup_logger(verbose: bool = False) -> logging.Logger:
    """配置日志记录器"""
    logger = logging.getLogger("NestingAnalyzer")
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
        description="嵌套层级分析器",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python nesting_analyzer.py
  python nesting_analyzer.py --max-depth 4
  python nesting_analyzer.py --output json --output-file result.json
  python nesting_analyzer.py --verbose
        """
    )

    parser.add_argument(
        "--max-depth",
        type=int,
        default=NestingDepthAnalyzer.DEFAULT_MAX_DEPTH,
        help=f"最大允许嵌套深度 (默认: {NestingDepthAnalyzer.DEFAULT_MAX_DEPTH})"
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

    # 运行分析
    analyzer = NestingDepthAnalyzer(
        max_depth=args.max_depth,
        logger=logger
    )
    report = analyzer.analyze_project()

    # 打印报告
    analyzer.print_report(report)

    # 保存报告
    report_path = analyzer.save_report(report)
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

    return 0 if report.summary.get("total_deep_nestings", 0) == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
