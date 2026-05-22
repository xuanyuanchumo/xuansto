#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
覆盖率验证脚本

读取覆盖率报告，验证覆盖率是否达标，生成覆盖率摘要，输出未覆盖代码列表。
支持后端（Python）和前端（JavaScript/TypeScript）覆盖率分析。

使用示例:
    python validate_test_coverage.py
    python validate_test_coverage.py --backend-threshold 85 --frontend-threshold 75
    python validate_test_coverage.py --output json --output-file result.json
    python validate_test_coverage.py --list-uncovered
"""

import argparse
import json
import os
import sys
import logging
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional
from xml.etree import ElementTree
from enum import Enum

# 添加后端路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False

# 默认阈值
DEFAULT_BACKEND_THRESHOLD = 80
DEFAULT_FRONTEND_THRESHOLD = 70

API_BASE = os.getenv("VISUAL_API_BASE", "http://localhost:8000/api")


class CoverageStatus(Enum):
    """覆盖率状态枚举"""
    PASS = "pass"
    FAIL = "fail"
    WARNING = "warning"


@dataclass
class CoverageFile:
    """覆盖率文件数据类"""
    path: str
    line_rate: float
    branch_rate: float = 0.0
    covered_lines: int = 0
    total_lines: int = 0
    uncovered_lines: List[int] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "path": self.path,
            "line_rate": round(self.line_rate, 2),
            "branch_rate": round(self.branch_rate, 2),
            "covered_lines": self.covered_lines,
            "total_lines": self.total_lines,
            "uncovered_lines": self.uncovered_lines
        }


@dataclass
class CoverageSummary:
    """覆盖率摘要数据类"""
    name: str
    line_rate: float
    branch_rate: float = 0.0
    threshold: float = 0.0
    passed: bool = False
    files: List[CoverageFile] = field(default_factory=list)
    uncovered_files: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "name": self.name,
            "line_rate": round(self.line_rate, 2),
            "branch_rate": round(self.branch_rate, 2),
            "threshold": self.threshold,
            "passed": self.passed,
            "files_count": len(self.files),
            "uncovered_files_count": len(self.uncovered_files),
            "files": [f.to_dict() for f in self.files[:10]],  # 只包含前10个文件
            "uncovered_files": self.uncovered_files[:10]
        }


@dataclass
class CoverageReport:
    """覆盖率报告数据类"""
    timestamp: str
    backend: Optional[CoverageSummary] = None
    frontend: Optional[CoverageSummary] = None
    overall_passed: bool = False
    skill_call_id: Optional[int] = None

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "timestamp": self.timestamp,
            "overall_passed": self.overall_passed,
            "skill_call_id": self.skill_call_id,
            "backend": self.backend.to_dict() if self.backend else None,
            "frontend": self.frontend.to_dict() if self.frontend else None
        }


class CoverageReader:
    """覆盖率读取器"""

    def __init__(self, project_root: Optional[Path] = None, logger: Optional[logging.Logger] = None):
        self.project_root = project_root or get_path_config().SKILL_ROOT
        self.backend_dir = self.project_root / "backend"
        self.frontend_dir = self.project_root / "frontend"
        self.reports_dir = self.project_root / "coverage_reports"
        self.reports_dir.mkdir(exist_ok=True)
        self.logger = logger or logging.getLogger(__name__)

    def read_backend_coverage(self, threshold: float = DEFAULT_BACKEND_THRESHOLD) -> CoverageSummary:
        """读取后端覆盖率报告"""
        self.logger.info("读取后端覆盖率报告...")
        print("\n" + "=" * 60)
        print("读取后端覆盖率报告...")
        print("=" * 60)

        summary = CoverageSummary(
            name="backend",
            line_rate=0.0,
            threshold=threshold
        )

        coverage_json = self.backend_dir / "coverage.json"
        coverage_xml = self.backend_dir / "coverage.xml"

        try:
            if coverage_json.exists():
                summary = self._parse_coverage_json(coverage_json, "backend", threshold)
            elif coverage_xml.exists():
                summary = self._parse_coverage_xml(coverage_xml, "backend", threshold)
            else:
                self.logger.warning("未找到后端覆盖率报告文件")
                print("⚠️ 警告: 未找到后端覆盖率报告文件")
                return summary

            summary.passed = summary.line_rate >= threshold

            status_icon = "✅" if summary.passed else "❌"
            print(f"{status_icon} 后端覆盖率: {summary.line_rate:.2f}%")
            print(f"   阈值要求: >= {threshold}%")
            print(f"   状态: {'达标' if summary.passed else '未达标'}")

        except Exception as e:
            self.logger.error(f"读取后端覆盖率失败: {e}")
            print(f"❌ 读取后端覆盖率失败: {e}")

        return summary

    def read_frontend_coverage(self, threshold: float = DEFAULT_FRONTEND_THRESHOLD) -> CoverageSummary:
        """读取前端覆盖率报告"""
        self.logger.info("读取前端覆盖率报告...")
        print("\n" + "=" * 60)
        print("读取前端覆盖率报告...")
        print("=" * 60)

        summary = CoverageSummary(
            name="frontend",
            line_rate=0.0,
            threshold=threshold
        )

        coverage_summary = self.frontend_dir / "coverage" / "coverage-summary.json"
        coverage_final = self.frontend_dir / "coverage" / "coverage-final.json"

        try:
            if coverage_summary.exists():
                summary = self._parse_frontend_coverage_summary(coverage_summary, threshold)
            elif coverage_final.exists():
                summary = self._parse_frontend_coverage_final(coverage_final, threshold)
            else:
                self.logger.warning("未找到前端覆盖率报告文件")
                print("⚠️ 警告: 未找到前端覆盖率报告文件")
                return summary

            summary.passed = summary.line_rate >= threshold

            status_icon = "✅" if summary.passed else "❌"
            print(f"{status_icon} 前端覆盖率: {summary.line_rate:.2f}%")
            print(f"   阈值要求: >= {threshold}%")
            print(f"   状态: {'达标' if summary.passed else '未达标'}")

        except Exception as e:
            self.logger.error(f"读取前端覆盖率失败: {e}")
            print(f"❌ 读取前端覆盖率失败: {e}")

        return summary

    def _parse_coverage_json(self, json_path: Path, name: str, threshold: float) -> CoverageSummary:
        """解析Python coverage JSON报告"""
        summary = CoverageSummary(name=name, line_rate=0.0, threshold=threshold)

        try:
            with open(json_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            totals = data.get("totals", {})
            summary.line_rate = totals.get("percent_covered", 0)
            summary.branch_rate = totals.get("percent_covered_branches", 0) or totals.get("branch_percent", 0)

            files_data = data.get("files", {})
            for file_path, file_info in files_data.items():
                if file_path.startswith("app/") or file_path.startswith("src/"):
                    summary_meta = file_info.get("summary", {})
                    covered = summary_meta.get("covered_lines", 0)
                    total = summary_meta.get("num_statements", 0)

                    coverage_file = CoverageFile(
                        path=file_path,
                        line_rate=(covered / total * 100) if total > 0 else 0,
                        covered_lines=covered,
                        total_lines=total
                    )

                    executed_lines = set(file_info.get("executed_lines", []))
                    all_lines = set(file_info.get("summary", {}).get("covered_lines", []))

                    if coverage_file.line_rate < 50:
                        summary.uncovered_files.append(file_path)

                    summary.files.append(coverage_file)

        except Exception as e:
            self.logger.error(f"解析覆盖率JSON失败: {e}")

        return summary

    def _parse_coverage_xml(self, xml_path: Path, name: str, threshold: float) -> CoverageSummary:
        """解析Python coverage XML报告"""
        summary = CoverageSummary(name=name, line_rate=0.0, threshold=threshold)

        try:
            tree = ElementTree.parse(xml_path)
            root = tree.getroot()

            line_rate = float(root.attrib.get("line-rate", 0))
            branch_rate = float(root.attrib.get("branch-rate", 0))
            summary.line_rate = line_rate * 100
            summary.branch_rate = branch_rate * 100

            for package in root.findall(".//package"):
                package_name = package.attrib.get("name", "")

                for cls in package.findall("classes/class"):
                    filename = cls.attrib.get("filename", "")
                    file_line_rate = float(cls.attrib.get("line-rate", 0))
                    file_branch_rate = float(cls.attrib.get("branch-rate", 0))

                    lines = cls.findall("lines/line")
                    covered = sum(1 for line in lines if line.attrib.get("hits", "0") != "0")
                    total = len(lines)

                    coverage_file = CoverageFile(
                        path=f"{package_name}/{filename}" if package_name else filename,
                        line_rate=file_line_rate * 100,
                        branch_rate=file_branch_rate * 100,
                        covered_lines=covered,
                        total_lines=total
                    )

                    if coverage_file.line_rate < 50:
                        summary.uncovered_files.append(coverage_file.path)

                    summary.files.append(coverage_file)

        except Exception as e:
            self.logger.error(f"解析覆盖率XML失败: {e}")

        return summary

    def _parse_frontend_coverage_summary(self, json_path: Path, threshold: float) -> CoverageSummary:
        """解析前端覆盖率摘要报告"""
        summary = CoverageSummary(name="frontend", line_rate=0.0, threshold=threshold)

        try:
            with open(json_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            total = data.get("total", {})
            summary.line_rate = total.get("lines", {}).get("pct", 0)
            summary.branch_rate = total.get("branches", {}).get("pct", 0)

            for file_path, file_data in data.items():
                if file_path == "total":
                    continue

                lines = file_data.get("lines", {})
                covered = lines.get("covered", 0)
                total_lines = lines.get("total", 0)

                coverage_file = CoverageFile(
                    path=file_path,
                    line_rate=lines.get("pct", 0),
                    covered_lines=covered,
                    total_lines=total_lines
                )

                if coverage_file.line_rate < 50:
                    summary.uncovered_files.append(file_path)

                summary.files.append(coverage_file)

        except Exception as e:
            self.logger.error(f"解析前端覆盖率摘要失败: {e}")

        return summary

    def _parse_frontend_coverage_final(self, json_path: Path, threshold: float) -> CoverageSummary:
        """解析前端覆盖率最终报告"""
        summary = CoverageSummary(name="frontend", line_rate=0.0, threshold=threshold)

        try:
            with open(json_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            total_lines = 0
            covered_lines = 0

            for file_path, file_data in data.items():
                lines = file_data.get("l", {})
                file_total = len(lines)
                file_covered = sum(1 for hits in lines.values() if hits > 0)

                total_lines += file_total
                covered_lines += file_covered

                coverage_file = CoverageFile(
                    path=file_path,
                    line_rate=(file_covered / file_total * 100) if file_total > 0 else 0,
                    covered_lines=file_covered,
                    total_lines=file_total
                )

                if coverage_file.line_rate < 50:
                    summary.uncovered_files.append(file_path)

                summary.files.append(coverage_file)

            summary.line_rate = (covered_lines / total_lines * 100) if total_lines > 0 else 0

        except Exception as e:
            self.logger.error(f"解析前端覆盖率详情失败: {e}")

        return summary


class CoverageValidator:
    """覆盖率验证器"""

    def __init__(self, reader: CoverageReader, logger: Optional[logging.Logger] = None):
        self.reader = reader
        self.logger = logger or logging.getLogger(__name__)

    def validate(self, backend_threshold: Optional[float] = None,
                 frontend_threshold: Optional[float] = None) -> CoverageReport:
        """验证覆盖率"""
        backend_threshold = backend_threshold or DEFAULT_BACKEND_THRESHOLD
        frontend_threshold = frontend_threshold or DEFAULT_FRONTEND_THRESHOLD

        backend_summary = self.reader.read_backend_coverage(backend_threshold)
        frontend_summary = self.reader.read_frontend_coverage(frontend_threshold)

        backend_summary.threshold = backend_threshold
        frontend_summary.threshold = frontend_threshold

        backend_summary.passed = backend_summary.line_rate >= backend_threshold
        frontend_summary.passed = frontend_summary.line_rate >= frontend_threshold

        report = CoverageReport(
            timestamp=datetime.now().isoformat(),
            backend=backend_summary,
            frontend=frontend_summary,
            overall_passed=backend_summary.passed and frontend_summary.passed
        )

        return report

    def generate_summary(self, report: CoverageReport) -> Dict[str, Any]:
        """生成摘要"""
        summary = {
            "timestamp": report.timestamp,
            "overall_passed": report.overall_passed,
            "backend": None,
            "frontend": None
        }

        if report.backend:
            summary["backend"] = {
                "line_rate": round(report.backend.line_rate, 2),
                "threshold": report.backend.threshold,
                "passed": report.backend.passed,
                "total_files": len(report.backend.files),
                "uncovered_files_count": len(report.backend.uncovered_files)
            }

        if report.frontend:
            summary["frontend"] = {
                "line_rate": round(report.frontend.line_rate, 2),
                "threshold": report.frontend.threshold,
                "passed": report.frontend.passed,
                "total_files": len(report.frontend.files),
                "uncovered_files_count": len(report.frontend.uncovered_files)
            }

        return summary

    def get_uncovered_code_list(self, report: CoverageReport,
                                threshold: float = 50.0) -> Dict[str, List[Dict]]:
        """获取未覆盖代码列表"""
        result = {
            "backend": [],
            "frontend": []
        }

        if report.backend:
            for f in report.backend.files:
                if f.line_rate < threshold:
                    result["backend"].append({
                        "path": f.path,
                        "line_rate": round(f.line_rate, 2),
                        "covered_lines": f.covered_lines,
                        "total_lines": f.total_lines
                    })

        if report.frontend:
            for f in report.frontend.files:
                if f.line_rate < threshold:
                    result["frontend"].append({
                        "path": f.path,
                        "line_rate": round(f.line_rate, 2),
                        "covered_lines": f.covered_lines,
                        "total_lines": f.total_lines
                    })

        return result

    def save_report(self, report: CoverageReport, filename: Optional[str] = None) -> Path:
        """保存报告"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"coverage_validation_{timestamp}.json"

        report_path = self.reader.reports_dir / filename

        data = report.to_dict()

        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        # 同时保存最新报告
        latest_path = self.reader.reports_dir / "coverage_validation_latest.json"
        with open(latest_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        self.logger.info(f"覆盖率验证报告已保存: {report_path}")
        return report_path

    def print_summary(self, report: CoverageReport):
        """打印摘要"""
        print("\n" + "=" * 60)
        print("覆盖率验证摘要")
        print("=" * 60)

        if report.backend:
            status_icon = "✅" if report.backend.passed else "❌"
            print(f"\n后端覆盖率:")
            print(f"  行覆盖率: {report.backend.line_rate:.2f}%")
            print(f"  阈值要求: >= {report.backend.threshold}%")
            print(f"  状态: {status_icon} {'达标' if report.backend.passed else '未达标'}")
            print(f"  文件数: {len(report.backend.files)}")
            print(f"  低覆盖率文件数: {len(report.backend.uncovered_files)}")

        if report.frontend:
            status_icon = "✅" if report.frontend.passed else "❌"
            print(f"\n前端覆盖率:")
            print(f"  行覆盖率: {report.frontend.line_rate:.2f}%")
            print(f"  阈值要求: >= {report.frontend.threshold}%")
            print(f"  状态: {status_icon} {'达标' if report.frontend.passed else '未达标'}")
            print(f"  文件数: {len(report.frontend.files)}")
            print(f"  低覆盖率文件数: {len(report.frontend.uncovered_files)}")

        print("\n" + "-" * 60)
        if report.overall_passed:
            print("🎉 所有覆盖率检查通过!")
        else:
            print("⚠️ 部分覆盖率检查未通过")


class SkillCallIntegration:
    """技能调用集成"""

    def __init__(self, api_base: str = API_BASE):
        self.api_base = api_base

    def record_coverage_validation(self, report: CoverageReport,
                                   parent_skill_id: Optional[int] = None) -> Optional[int]:
        """记录覆盖率验证到技能调用系统"""
        if not HAS_REQUESTS:
            self.logger.warning("requests库未安装，无法记录到技能调用系统")
            return None

        payload = {
            "skill_name": "coverage_validation",
            "status": "completed" if report.overall_passed else "failed",
            "details": {
                "backend_coverage": report.backend.line_rate if report.backend else 0,
                "frontend_coverage": report.frontend.line_rate if report.frontend else 0,
                "backend_passed": report.backend.passed if report.backend else False,
                "frontend_passed": report.frontend.passed if report.frontend else False
            },
            "parent_call_id": parent_skill_id,
            "caller": "validate_test_coverage"
        }

        try:
            resp = requests.post(f"{self.api_base}/skill_calls", json=payload, timeout=10)
            resp.raise_for_status()
            result = resp.json()
            call_id = result.get("id")
            print(f"覆盖率验证已记录到技能调用系统: ID={call_id}")
            return call_id
        except requests.exceptions.RequestException as e:
            print(f"记录覆盖率验证失败: {e}", file=sys.stderr)
            return None


def setup_logger(verbose: bool = False) -> logging.Logger:
    """配置日志记录器"""
    logger = logging.getLogger("CoverageValidator")
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
        description="覆盖率验证脚本",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python validate_test_coverage.py
  python validate_test_coverage.py --backend-threshold 85 --frontend-threshold 75
  python validate_test_coverage.py --output json --output-file result.json
  python validate_test_coverage.py --list-uncovered
        """
    )

    parser.add_argument(
        "--backend-threshold",
        type=float,
        default=DEFAULT_BACKEND_THRESHOLD,
        help=f"后端覆盖率阈值 (默认: {DEFAULT_BACKEND_THRESHOLD})"
    )

    parser.add_argument(
        "--frontend-threshold",
        type=float,
        default=DEFAULT_FRONTEND_THRESHOLD,
        help=f"前端覆盖率阈值 (默认: {DEFAULT_FRONTEND_THRESHOLD})"
    )

    parser.add_argument(
        "--uncovered-threshold",
        type=float,
        default=50.0,
        help="低覆盖率文件阈值 (默认: 50)"
    )

    parser.add_argument(
        "--record-skill",
        action="store_true",
        help="记录到技能调用系统"
    )

    parser.add_argument(
        "--parent-skill-id",
        type=int,
        help="父技能调用ID"
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
        "--list-uncovered",
        action="store_true",
        help="列出所有低覆盖率文件"
    )

    parser.add_argument(
        "--verbose",
        action="store_true",
        help="启用详细日志输出"
    )

    args = parser.parse_args()

    # 配置日志
    logger = setup_logger(args.verbose)

    # 创建组件
    reader = CoverageReader(logger=logger)
    validator = CoverageValidator(reader, logger=logger)

    # 验证覆盖率
    report = validator.validate(args.backend_threshold, args.frontend_threshold)

    # 记录到技能调用系统
    if args.record_skill and HAS_REQUESTS:
        integration = SkillCallIntegration()
        skill_call_id = integration.record_coverage_validation(report, args.parent_skill_id)
        if skill_call_id:
            report.skill_call_id = skill_call_id

    # 保存报告
    report_path = validator.save_report(report)
    print(f"\n覆盖率验证报告已保存: {report_path}")

    # 打印摘要
    validator.print_summary(report)

    # 列出未覆盖文件
    if args.list_uncovered:
        uncovered = validator.get_uncovered_code_list(report, args.uncovered_threshold)

        print("\n" + "=" * 60)
        print("低覆盖率文件完整列表")
        print("=" * 60)

        if uncovered["backend"]:
            print(f"\n后端 ({len(uncovered['backend'])} 个文件):")
            for item in uncovered["backend"]:
                print(f"  {item['path']}: {item['line_rate']:.1f}%")

        if uncovered["frontend"]:
            print(f"\n前端 ({len(uncovered['frontend'])} 个文件):")
            for item in uncovered["frontend"]:
                print(f"  {item['path']}: {item['line_rate']:.1f}%")

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

    return 0 if report.overall_passed else 1


if __name__ == "__main__":
    sys.exit(main())
