#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试覆盖率分析器

分析pytest和vitest覆盖率报告，识别覆盖率缺口，生成详细的覆盖率分析报告。
支持Python和JavaScript/TypeScript项目的覆盖率分析。

使用示例:
    python coverage_analyzer.py
    python coverage_analyzer.py --backend-threshold 85 --frontend-threshold 75
    python coverage_analyzer.py --run-tests
    python coverage_analyzer.py --output json --output-file result.json
"""

import json
import os
import subprocess
import sys
import argparse
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime
from xml.etree import ElementTree
from enum import Enum


class CoverageGapType(Enum):
    """覆盖率缺口类型枚举"""
    MISSING_BRANCH = "missing_branch"
    MISSING_LINE = "missing_line"
    MISSING_FUNCTION = "missing_function"
    MISSING_CLASS = "missing_class"
    MISSING_FILE = "missing_file"


@dataclass
class CoverageGap:
    """覆盖率缺口数据类"""
    file_path: str
    gap_type: CoverageGapType
    line_start: int
    line_end: int
    description: str
    current_coverage: float
    target_coverage: float
    impact_score: float = 0.0
    suggestion: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "file_path": self.file_path,
            "gap_type": self.gap_type.value,
            "line_start": self.line_start,
            "line_end": self.line_end,
            "description": self.description,
            "current_coverage": round(self.current_coverage, 2),
            "target_coverage": self.target_coverage,
            "impact_score": round(self.impact_score, 2),
            "suggestion": self.suggestion
        }


@dataclass
class FileCoverage:
    """文件覆盖率数据类"""
    file_path: str
    line_rate: float
    branch_rate: float
    function_rate: float
    covered_lines: int
    total_lines: int
    covered_branches: int
    total_branches: int
    missing_lines: List[int] = field(default_factory=list)
    missing_branches: List[tuple] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "file_path": self.file_path,
            "line_rate": round(self.line_rate, 2),
            "branch_rate": round(self.branch_rate, 2),
            "function_rate": round(self.function_rate, 2),
            "covered_lines": self.covered_lines,
            "total_lines": self.total_lines,
            "covered_branches": self.covered_branches,
            "total_branches": self.total_branches,
            "missing_lines": self.missing_lines[:20],  # 限制数量
            "missing_branches": self.missing_branches[:10]
        }


@dataclass
class ProjectCoverageReport:
    """项目覆盖率报告数据类"""
    timestamp: str
    project: str
    total_line_rate: float
    total_branch_rate: float
    files: List[FileCoverage]
    gaps: List[CoverageGap]
    threshold_met: bool
    threshold: float

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "timestamp": self.timestamp,
            "project": self.project,
            "total_line_rate": round(self.total_line_rate, 2),
            "total_branch_rate": round(self.total_branch_rate, 2),
            "files": [f.to_dict() for f in self.files],
            "gaps": [g.to_dict() for g in self.gaps],
            "threshold_met": self.threshold_met,
            "threshold": self.threshold
        }


class PythonCoverageAnalyzer:
    """Python覆盖率分析器"""

    def __init__(self, threshold: float = 80.0, logger: Optional[logging.Logger] = None):
        self.threshold = threshold
        self.logger = logger or logging.getLogger(__name__)
        self.coverage_data: Dict[str, FileCoverage] = {}
        self.gaps: List[CoverageGap] = []

    def run_pytest_coverage(self, backend_dir: Path, timeout: int = 300) -> bool:
        """运行pytest覆盖率测试"""
        if not backend_dir.exists():
            self.logger.warning(f"后端目录不存在: {backend_dir}")
            return False

        os.chdir(backend_dir)

        cmd = [
            sys.executable, "-m", "pytest",
            "--cov=app",
            "--cov-report=xml:coverage.xml",
            "--cov-report=json:coverage.json",
            "-q", "--tb=no"
        ]

        try:
            self.logger.info("运行pytest覆盖率测试...")
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
            self.logger.info("pytest覆盖率测试完成")
            return True
        except subprocess.TimeoutExpired:
            self.logger.warning("pytest覆盖率运行超时")
            return False
        except Exception as e:
            self.logger.warning(f"pytest覆盖率运行失败: {e}")
            return False

    def parse_coverage_xml(self, xml_path: Path) -> Dict[str, FileCoverage]:
        """解析coverage XML报告"""
        if not xml_path.exists():
            self.logger.warning(f"XML报告不存在: {xml_path}")
            return {}

        try:
            tree = ElementTree.parse(xml_path)
            root = tree.getroot()

            for package in root.findall(".//package"):
                package_name = package.get("name", "")

                for cls in package.findall("classes/class"):
                    file_name = cls.get("filename", "")
                    if not file_name:
                        continue

                    file_path = f"{package_name}/{file_name}" if package_name else file_name

                    line_rate = float(cls.get("line-rate", 0)) * 100
                    branch_rate = float(cls.get("branch-rate", 0)) * 100

                    lines = cls.findall("lines/line")
                    covered_lines = sum(1 for l in lines if l.get("hits", "0") != "0")
                    total_lines = len(lines)
                    missing_lines = [int(l.get("number", 0)) for l in lines if l.get("hits", "0") == "0"]

                    branches = [l for l in lines if l.get("branch") == "true"]
                    covered_branches = sum(1 for b in branches if b.get("condition-coverage", "").startswith("100%"))
                    total_branches = len(branches)

                    self.coverage_data[file_path] = FileCoverage(
                        file_path=file_path,
                        line_rate=line_rate,
                        branch_rate=branch_rate,
                        function_rate=line_rate,
                        covered_lines=covered_lines,
                        total_lines=total_lines,
                        covered_branches=covered_branches,
                        total_branches=total_branches,
                        missing_lines=missing_lines
                    )
        except Exception as e:
            self.logger.error(f"解析覆盖率XML失败: {e}")

        return self.coverage_data

    def parse_coverage_json(self, json_path: Path) -> Dict[str, FileCoverage]:
        """解析coverage JSON报告"""
        if not json_path.exists():
            self.logger.warning(f"JSON报告不存在: {json_path}")
            return {}

        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            files_data = data.get("files", {})

            for file_path, file_info in files_data.items():
                summary = file_info.get("summary", {})
                executed_lines = file_info.get("executed_lines", [])
                missing_lines = file_info.get("missing_lines", [])

                covered_lines = len(executed_lines)
                total_lines = covered_lines + len(missing_lines)
                line_rate = (covered_lines / total_lines * 100) if total_lines > 0 else 0

                self.coverage_data[file_path] = FileCoverage(
                    file_path=file_path,
                    line_rate=line_rate,
                    branch_rate=summary.get("covered_branches", 0) / max(summary.get("num_branches", 1), 1) * 100,
                    function_rate=line_rate,
                    covered_lines=covered_lines,
                    total_lines=total_lines,
                    covered_branches=summary.get("covered_branches", 0),
                    total_branches=summary.get("num_branches", 0),
                    missing_lines=missing_lines
                )
        except Exception as e:
            self.logger.error(f"解析覆盖率JSON失败: {e}")

        return self.coverage_data

    def identify_gaps(self) -> List[CoverageGap]:
        """识别覆盖率缺口"""
        self.gaps = []

        for file_path, coverage in self.coverage_data.items():
            if coverage.line_rate < self.threshold:
                gap = CoverageGap(
                    file_path=file_path,
                    gap_type=CoverageGapType.MISSING_LINE,
                    line_start=min(coverage.missing_lines) if coverage.missing_lines else 0,
                    line_end=max(coverage.missing_lines) if coverage.missing_lines else 0,
                    description=f"文件覆盖率 {coverage.line_rate:.1f}% 低于阈值 {self.threshold}%",
                    current_coverage=coverage.line_rate,
                    target_coverage=self.threshold,
                    impact_score=self._calculate_impact_score(coverage),
                    suggestion=self._generate_suggestion(coverage)
                )
                self.gaps.append(gap)

            # 添加具体未覆盖行的缺口
            for line in coverage.missing_lines[:20]:  # 限制数量
                gap = CoverageGap(
                    file_path=file_path,
                    gap_type=CoverageGapType.MISSING_LINE,
                    line_start=line,
                    line_end=line,
                    description=f"第 {line} 行未被测试覆盖",
                    current_coverage=coverage.line_rate,
                    target_coverage=self.threshold,
                    impact_score=5.0,
                    suggestion="添加测试用例覆盖此行代码"
                )
                self.gaps.append(gap)

        return self.gaps

    def _calculate_impact_score(self, coverage: FileCoverage) -> float:
        """计算影响分数"""
        gap = self.threshold - coverage.line_rate
        size_factor = min(coverage.total_lines / 100, 2.0)
        return gap * size_factor

    def _generate_suggestion(self, coverage: FileCoverage) -> str:
        """生成优化建议"""
        suggestions = []
        if coverage.line_rate < 50:
            suggestions.append("该文件覆盖率严重不足，建议优先编写基础测试")
        elif coverage.line_rate < self.threshold:
            suggestions.append(f"需要增加测试用例以达到 {self.threshold}% 覆盖率")

        if coverage.total_lines > 200:
            suggestions.append("文件较大，考虑拆分以提高可测试性")

        return "; ".join(suggestions) if suggestions else "继续完善测试用例"


class VitestCoverageAnalyzer:
    """Vitest覆盖率分析器"""

    def __init__(self, threshold: float = 70.0, logger: Optional[logging.Logger] = None):
        self.threshold = threshold
        self.logger = logger or logging.getLogger(__name__)
        self.coverage_data: Dict[str, FileCoverage] = {}
        self.gaps: List[CoverageGap] = []

    def run_vitest_coverage(self, frontend_dir: Path, timeout: int = 300) -> bool:
        """运行vitest覆盖率测试"""
        if not (frontend_dir / "package.json").exists():
            self.logger.warning(f"前端目录不存在package.json: {frontend_dir}")
            return False

        os.chdir(frontend_dir)

        try:
            self.logger.info("运行vitest覆盖率测试...")
            result = subprocess.run(
                ["npm", "run", "test:coverage"],
                capture_output=True,
                text=True,
                shell=True,
                timeout=timeout
            )
            self.logger.info("vitest覆盖率测试完成")
            return True
        except subprocess.TimeoutExpired:
            self.logger.warning("vitest覆盖率运行超时")
            return False
        except Exception as e:
            self.logger.warning(f"vitest覆盖率运行失败: {e}")
            return False

    def parse_coverage_json(self, json_path: Path) -> Dict[str, FileCoverage]:
        """解析覆盖率JSON报告"""
        if not json_path.exists():
            self.logger.warning(f"覆盖率JSON不存在: {json_path}")
            return {}

        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            if "total" in data:
                return self._parse_coverage_summary_json(data)

            return self._parse_coverage_final_json(data)
        except Exception as e:
            self.logger.error(f"解析覆盖率JSON失败: {e}")
            return {}

    def _parse_coverage_summary_json(self, data: Dict) -> Dict[str, FileCoverage]:
        """解析覆盖率摘要JSON"""
        for file_path, file_info in data.items():
            if file_path == "total":
                continue

            lines = file_info.get("lines", {})
            branches = file_info.get("branches", {})
            functions = file_info.get("functions", {})

            self.coverage_data[file_path] = FileCoverage(
                file_path=file_path,
                line_rate=lines.get("pct", 0),
                branch_rate=branches.get("pct", 0),
                function_rate=functions.get("pct", 0),
                covered_lines=lines.get("covered", 0),
                total_lines=lines.get("total", 0),
                covered_branches=branches.get("covered", 0),
                total_branches=branches.get("total", 0)
            )

        return self.coverage_data

    def _parse_coverage_final_json(self, data: Dict) -> Dict[str, FileCoverage]:
        """解析覆盖率最终JSON"""
        for file_path, file_info in data.items():
            if not isinstance(file_info, dict):
                continue

            line_map = file_info.get("l", {})
            branch_map = file_info.get("b", {})
            func_map = file_info.get("f", {})

            total_lines = len(line_map)
            covered_lines = sum(1 for hits in line_map.values() if hits > 0)
            line_rate = (covered_lines / total_lines * 100) if total_lines > 0 else 0

            total_branches = sum(len(branches) for branches in branch_map.values())
            covered_branches = sum(sum(1 for h in branches if h > 0) for branches in branch_map.values())
            branch_rate = (covered_branches / total_branches * 100) if total_branches > 0 else 0

            total_funcs = len(func_map)
            covered_funcs = sum(1 for hits in func_map.values() if hits > 0)
            func_rate = (covered_funcs / total_funcs * 100) if total_funcs > 0 else 0

            missing_lines = [int(k) for k, v in line_map.items() if v == 0]

            self.coverage_data[file_path] = FileCoverage(
                file_path=file_path,
                line_rate=line_rate,
                branch_rate=branch_rate,
                function_rate=func_rate,
                covered_lines=covered_lines,
                total_lines=total_lines,
                covered_branches=covered_branches,
                total_branches=total_branches,
                missing_lines=missing_lines
            )

        return self.coverage_data

    def identify_gaps(self) -> List[CoverageGap]:
        """识别覆盖率缺口"""
        self.gaps = []

        for file_path, coverage in self.coverage_data.items():
            if coverage.line_rate < self.threshold:
                gap = CoverageGap(
                    file_path=file_path,
                    gap_type=CoverageGapType.MISSING_LINE,
                    line_start=min(coverage.missing_lines) if coverage.missing_lines else 0,
                    line_end=max(coverage.missing_lines) if coverage.missing_lines else 0,
                    description=f"文件覆盖率 {coverage.line_rate:.1f}% 低于阈值 {self.threshold}%",
                    current_coverage=coverage.line_rate,
                    target_coverage=self.threshold,
                    impact_score=self._calculate_impact_score(coverage),
                    suggestion=self._generate_suggestion(coverage)
                )
                self.gaps.append(gap)

        return self.gaps

    def _calculate_impact_score(self, coverage: FileCoverage) -> float:
        """计算影响分数"""
        gap = self.threshold - coverage.line_rate
        size_factor = min(coverage.total_lines / 100, 2.0)
        return gap * size_factor

    def _generate_suggestion(self, coverage: FileCoverage) -> str:
        """生成优化建议"""
        suggestions = []
        if coverage.line_rate < 50:
            suggestions.append("该文件覆盖率严重不足，建议优先编写基础测试")
        elif coverage.line_rate < self.threshold:
            suggestions.append(f"需要增加测试用例以达到 {self.threshold}% 覆盖率")

        if coverage.function_rate < coverage.line_rate:
            suggestions.append("部分函数未被测试，建议为每个函数编写测试")

        return "; ".join(suggestions) if suggestions else "继续完善测试用例"


class CoverageAnalyzer:
    """覆盖率分析器主类"""

    def __init__(self, backend_threshold: float = 80.0, frontend_threshold: float = 70.0,
                 logger: Optional[logging.Logger] = None):
        self.backend_threshold = backend_threshold
        self.frontend_threshold = frontend_threshold
        self.logger = logger or logging.getLogger(__name__)
        self.python_analyzer = PythonCoverageAnalyzer(backend_threshold, logger)
        self.vitest_analyzer = VitestCoverageAnalyzer(frontend_threshold, logger)
        self.reports: Dict[str, ProjectCoverageReport] = {}

    def analyze_backend(self, backend_dir: Path, run_tests: bool = False) -> ProjectCoverageReport:
        """分析后端覆盖率"""
        if run_tests:
            self.python_analyzer.run_pytest_coverage(backend_dir)

        xml_path = backend_dir / "coverage.xml"
        json_path = backend_dir / "coverage.json"

        if json_path.exists():
            self.python_analyzer.parse_coverage_json(json_path)
        elif xml_path.exists():
            self.python_analyzer.parse_coverage_xml(xml_path)

        gaps = self.python_analyzer.identify_gaps()

        files = list(self.python_analyzer.coverage_data.values())
        total_line_rate = sum(f.line_rate for f in files) / len(files) if files else 0
        total_branch_rate = sum(f.branch_rate for f in files) / len(files) if files else 0

        report = ProjectCoverageReport(
            timestamp=datetime.now().isoformat(),
            project="backend",
            total_line_rate=total_line_rate,
            total_branch_rate=total_branch_rate,
            files=files,
            gaps=gaps,
            threshold_met=total_line_rate >= self.backend_threshold,
            threshold=self.backend_threshold
        )

        self.reports["backend"] = report
        return report

    def analyze_frontend(self, frontend_dir: Path, run_tests: bool = False) -> ProjectCoverageReport:
        """分析前端覆盖率"""
        if run_tests:
            self.vitest_analyzer.run_vitest_coverage(frontend_dir)

        summary_path = frontend_dir / "coverage" / "coverage-summary.json"
        final_path = frontend_dir / "coverage" / "coverage-final.json"

        if summary_path.exists():
            self.vitest_analyzer.parse_coverage_json(summary_path)
        elif final_path.exists():
            self.vitest_analyzer.parse_coverage_json(final_path)

        gaps = self.vitest_analyzer.identify_gaps()

        files = list(self.vitest_analyzer.coverage_data.values())
        total_line_rate = sum(f.line_rate for f in files) / len(files) if files else 0
        total_branch_rate = sum(f.branch_rate for f in files) / len(files) if files else 0

        report = ProjectCoverageReport(
            timestamp=datetime.now().isoformat(),
            project="frontend",
            total_line_rate=total_line_rate,
            total_branch_rate=total_branch_rate,
            files=files,
            gaps=gaps,
            threshold_met=total_line_rate >= self.frontend_threshold,
            threshold=self.frontend_threshold
        )

        self.reports["frontend"] = report
        return report

    def analyze_existing_reports(self, base_dir: Path) -> Dict[str, ProjectCoverageReport]:
        """分析现有报告"""
        backend_dir = base_dir / "backend"
        frontend_dir = base_dir / "frontend"

        if backend_dir.exists():
            self.analyze_backend(backend_dir, run_tests=False)

        if frontend_dir.exists():
            self.analyze_frontend(frontend_dir, run_tests=False)

        return self.reports

    def generate_combined_report(self) -> str:
        """生成合并报告"""
        report = []
        report.append("=" * 80)
        report.append("测试覆盖率分析报告")
        report.append(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("=" * 80)

        for project_name, project_report in self.reports.items():
            report.append(f"\n## {project_name.upper()} 覆盖率报告")
            report.append("-" * 40)
            report.append(f"总行覆盖率: {project_report.total_line_rate:.2f}%")
            report.append(f"总分支覆盖率: {project_report.total_branch_rate:.2f}%")
            report.append(f"阈值: {project_report.threshold}%")
            status_icon = "✅" if project_report.threshold_met else "❌"
            report.append(f"达标: {status_icon} {'是' if project_report.threshold_met else '否'}")
            report.append(f"文件数: {len(project_report.files)}")
            report.append(f"覆盖率缺口: {len(project_report.gaps)}")

            if project_report.gaps:
                report.append(f"\n### 主要覆盖率缺口 (前10个)")
                sorted_gaps = sorted(project_report.gaps, key=lambda g: g.impact_score, reverse=True)[:10]
                for i, gap in enumerate(sorted_gaps, 1):
                    report.append(f"\n{i}. {gap.file_path}")
                    report.append(f"   类型: {gap.gap_type.value}")
                    report.append(f"   位置: 行 {gap.line_start}-{gap.line_end}")
                    report.append(f"   当前覆盖率: {gap.current_coverage:.1f}%")
                    report.append(f"   影响分数: {gap.impact_score:.1f}")
                    report.append(f"   建议: {gap.suggestion}")

        report.append("\n" + "=" * 80)
        report.append("覆盖率优化建议")
        report.append("=" * 80)
        report.append("\n1. 优先处理影响分数高的文件")
        report.append("2. 为核心业务逻辑添加单元测试")
        report.append("3. 为边界条件添加测试用例")
        report.append("4. 使用突变测试验证测试质量")
        report.append("5. 定期运行覆盖率检查，防止覆盖率下降")

        return "\n".join(report)

    def save_reports(self, output_dir: Path) -> None:
        """保存报告"""
        output_dir.mkdir(parents=True, exist_ok=True)

        for project_name, project_report in self.reports.items():
            json_path = output_dir / f"{project_name}_coverage_report.json"
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(project_report.to_dict(), f, indent=2, ensure_ascii=False)

        combined_path = output_dir / "combined_coverage_report.txt"
        with open(combined_path, 'w', encoding='utf-8') as f:
            f.write(self.generate_combined_report())

    def get_low_coverage_files(self, threshold: Optional[float] = None) -> List[FileCoverage]:
        """获取低覆盖率文件"""
        low_coverage = []
        for report in self.reports.values():
            file_threshold = threshold or report.threshold
            for file_cov in report.files:
                if file_cov.line_rate < file_threshold:
                    low_coverage.append(file_cov)
        return sorted(low_coverage, key=lambda f: f.line_rate)

    def get_total_gap_count(self) -> int:
        """获取总缺口数"""
        return sum(len(r.gaps) for r in self.reports.values())

    def all_thresholds_met(self) -> bool:
        """检查所有阈值是否达标"""
        return all(r.threshold_met for r in self.reports.values())


def setup_logger(verbose: bool = False) -> logging.Logger:
    """配置日志记录器"""
    logger = logging.getLogger("CoverageAnalyzer")
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
        description="测试覆盖率分析器",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python coverage_analyzer.py
  python coverage_analyzer.py --backend-threshold 85 --frontend-threshold 75
  python coverage_analyzer.py --run-tests
  python coverage_analyzer.py --output json --output-file result.json
        """
    )

    parser.add_argument(
        "--backend-threshold",
        type=float,
        default=80.0,
        help="后端覆盖率阈值 (默认: 80)"
    )

    parser.add_argument(
        "--frontend-threshold",
        type=float,
        default=70.0,
        help="前端覆盖率阈值 (默认: 70)"
    )

    parser.add_argument(
        "--run-tests",
        action="store_true",
        help="运行测试生成覆盖率报告"
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

    base_dir = Path(__file__).parent.parent

    print("=" * 80)
    print("测试覆盖率分析器")
    print("=" * 80)

    analyzer = CoverageAnalyzer(
        backend_threshold=args.backend_threshold,
        frontend_threshold=args.frontend_threshold,
        logger=logger
    )

    print("\n分析后端覆盖率...")
    backend_dir = base_dir / "backend"
    if backend_dir.exists():
        backend_report = analyzer.analyze_backend(backend_dir, run_tests=args.run_tests)
        print(f"后端行覆盖率: {backend_report.total_line_rate:.2f}%")
        print(f"后端达标: {'是' if backend_report.threshold_met else '否'}")

    print("\n分析前端覆盖率...")
    frontend_dir = base_dir / "frontend"
    if frontend_dir.exists():
        frontend_report = analyzer.analyze_frontend(frontend_dir, run_tests=args.run_tests)
        print(f"前端行覆盖率: {frontend_report.total_line_rate:.2f}%")
        print(f"前端达标: {'是' if frontend_report.threshold_met else '否'}")

    print("\n生成报告...")
    report = analyzer.generate_combined_report()
    print(report)

    reports_dir = base_dir / "reports"
    analyzer.save_reports(reports_dir)
    print(f"\n报告已保存到: {reports_dir}")

    low_coverage = analyzer.get_low_coverage_files()
    if low_coverage:
        print(f"\n覆盖率低于阈值的文件数: {len(low_coverage)}")
        print("最低覆盖率文件:")
        for f in low_coverage[:5]:
            print(f"  - {f.file_path}: {f.line_rate:.1f}%")

    # 输出JSON结果
    if args.output == "json":
        output_data = {
            "timestamp": datetime.now().isoformat(),
            "reports": {k: v.to_dict() for k, v in analyzer.reports.items()},
            "all_thresholds_met": analyzer.all_thresholds_met(),
            "total_gaps": analyzer.get_total_gap_count()
        }
        output_json = json.dumps(output_data, ensure_ascii=False, indent=2)

        if args.output_file:
            output_path = Path(args.output_file)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(output_json)
            print(f"\nJSON结果已保存到: {output_path}")
        else:
            print("\nJSON结果:")
            print(output_json)

    return 0 if analyzer.all_thresholds_met() else 1


if __name__ == "__main__":
    sys.exit(main())
