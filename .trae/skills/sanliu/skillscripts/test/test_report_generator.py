#!/usr/bin/env python3
"""
测试报告生成脚本 - Sanliu 技能

功能：
- 收集所有测试结果
- 生成 HTML/Markdown 报告
- 输出到 docs/reports/<version>/
- 支持历史趋势分析
- 支持多种测试框架的结果解析
- 版本控制和历史管理

使用方法：
    python scripts/test_report_generator.py --help
    python scripts/test_report_generator.py --collect
    python scripts/test_report_generator.py --format html --output docs/reports
    python scripts/test_report_generator.py --bump minor
    python scripts/test_report_generator.py --history
"""

import argparse
import json
import logging
import os
import re
import shutil
import sys
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Optional
from path_config_manager import PathConfigManager


# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - [%(name)s] %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('test_report.log', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)


@dataclass
class TestCase:
    """测试用例数据类"""
    name: str
    status: str  # passed, failed, skipped, error
    duration: float = 0.0
    message: str = ""
    stack_trace: str = ""
    suite: str = ""
    file: str = ""
    line: int = 0


@dataclass
class TestSuite:
    """测试套件数据类"""
    name: str
    tests: list[TestCase] = field(default_factory=list)
    total_tests: int = 0
    passed_tests: int = 0
    failed_tests: int = 0
    skipped_tests: int = 0
    error_tests: int = 0
    duration: float = 0.0
    timestamp: Optional[datetime] = None


@dataclass
class TestReport:
    """测试报告数据类"""
    title: str
    version: str
    timestamp: datetime
    suites: list[TestSuite] = field(default_factory=list)
    summary: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class ReportConfig:
    """报告配置数据类"""
    output_dir: Path
    format: str = "html"
    version: str = "1.0.0"
    collect_coverage: bool = True
    include_history: bool = True
    history_days: int = 30
    test_results_dirs: list[Path] = field(default_factory=list)


class VersionPart(Enum):
    """版本号部分枚举"""
    MAJOR = "major"
    MINOR = "minor"
    PATCH = "patch"


@dataclass
class ReportVersionInfo:
    """报告版本信息数据类"""
    version: str
    created_at: datetime
    total_tests: int = 0
    passed_tests: int = 0
    failed_tests: int = 0
    coverage: float = 0.0
    pass_rate: float = 0.0
    is_stable: bool = True


class ReportVersionController:
    """报告版本控制器"""

    def __init__(self, output_dir: Path):
        self.output_dir = output_dir
        self.version_file = output_dir / "report_versions.json"
        self._versions: dict[str, ReportVersionInfo] = {}
        self._load_versions()

    def _load_versions(self):
        """加载版本历史"""
        if self.version_file.exists():
            try:
                with open(self.version_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                for ver, info in data.items():
                    self._versions[ver] = ReportVersionInfo(
                        version=ver,
                        created_at=datetime.fromisoformat(info['created_at']),
                        total_tests=info.get('total_tests', 0),
                        passed_tests=info.get('passed_tests', 0),
                        failed_tests=info.get('failed_tests', 0),
                        coverage=info.get('coverage', 0.0),
                        pass_rate=info.get('pass_rate', 0.0),
                        is_stable=info.get('is_stable', True)
                    )
            except Exception as e:
                logger.warning(f"加载报告版本历史失败: {e}")

    def _save_versions(self):
        """保存版本历史"""
        self.output_dir.mkdir(parents=True, exist_ok=True)
        data = {}
        for ver, info in self._versions.items():
            data[ver] = {
                'version': info.version,
                'created_at': info.created_at.isoformat(),
                'total_tests': info.total_tests,
                'passed_tests': info.passed_tests,
                'failed_tests': info.failed_tests,
                'coverage': info.coverage,
                'pass_rate': info.pass_rate,
                'is_stable': info.is_stable
            }
        with open(self.version_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def get_version_dir(self, version: str) -> Path:
        """获取版本目录"""
        return self.output_dir / f"v{version}"

    def create_version(self, version: str, summary: dict[str, Any]) -> Path:
        """创建新版本"""
        version_dir = self.get_version_dir(version)
        version_dir.mkdir(parents=True, exist_ok=True)

        version_info = ReportVersionInfo(
            version=version,
            created_at=datetime.now(),
            total_tests=summary.get('total_tests', 0),
            passed_tests=summary.get('passed_tests', 0),
            failed_tests=summary.get('failed_tests', 0),
            coverage=summary.get('coverage', 0.0),
            pass_rate=summary.get('pass_rate', 0.0),
            is_stable=summary.get('failed_tests', 0) == 0
        )
        self._versions[version] = version_info
        self._save_versions()

        logger.info(f"创建报告版本: v{version}")
        return version_dir

    def get_latest_version(self) -> Optional[str]:
        """获取最新版本"""
        if not self._versions:
            return None
        return max(self._versions.keys(), key=lambda v: self._parse_version(v))

    def _parse_version(self, version: str) -> tuple:
        """解析版本号为元组"""
        try:
            parts = version.lstrip('v').split('.')
            return tuple(int(p) for p in parts[:3])
        except Exception:
            return (0, 0, 0)

    def bump_version(self, part: VersionPart, current: str = None) -> str:
        """递增版本号"""
        if current is None:
            current = self.get_latest_version() or "0.0.0"

        parts = self._parse_version(current)
        if part == VersionPart.MAJOR:
            return f"{parts[0] + 1}.0.0"
        elif part == VersionPart.MINOR:
            return f"{parts[0]}.{parts[1] + 1}.0"
        else:
            return f"{parts[0]}.{parts[1]}.{parts[2] + 1}"

    def list_versions(self) -> list[dict[str, Any]]:
        """列出所有版本"""
        versions = []
        for ver, info in sorted(self._versions.items(), key=lambda x: self._parse_version(x[0]), reverse=True):
            versions.append({
                'version': info.version,
                'created_at': info.created_at.isoformat(),
                'total_tests': info.total_tests,
                'passed_tests': info.passed_tests,
                'failed_tests': info.failed_tests,
                'coverage': info.coverage,
                'pass_rate': info.pass_rate,
                'is_stable': info.is_stable
            })
        return versions

    def get_trend(self, days: int = 30) -> list[dict[str, Any]]:
        """获取趋势数据"""
        cutoff_date = datetime.now() - timedelta(days=days)
        trend = []
        for ver, info in sorted(self._versions.items(), key=lambda x: x[1].created_at):
            if info.created_at >= cutoff_date:
                trend.append({
                    'date': info.created_at.isoformat(),
                    'version': info.version,
                    'total_tests': info.total_tests,
                    'passed_tests': info.passed_tests,
                    'failed_tests': info.failed_tests,
                    'coverage': info.coverage,
                    'pass_rate': info.pass_rate
                })
        return trend

    def compare_versions(self, version1: str, version2: str) -> dict[str, Any]:
        """比较两个版本"""
        v1_info = self._versions.get(version1)
        v2_info = self._versions.get(version2)

        result = {
            'version1': version1,
            'version2': version2,
            'v1_exists': v1_info is not None,
            'v2_exists': v2_info is not None,
            'difference': None
        }

        if v1_info and v2_info:
            result['difference'] = {
                'total_tests': v2_info.total_tests - v1_info.total_tests,
                'passed_tests': v2_info.passed_tests - v1_info.passed_tests,
                'failed_tests': v2_info.failed_tests - v1_info.failed_tests,
                'coverage': round(v2_info.coverage - v1_info.coverage, 2),
                'pass_rate': round(v2_info.pass_rate - v1_info.pass_rate, 2)
            }

        return result

    def archive_version(self, version: str, archive_dir: Path = None):
        """归档旧版本"""
        version_dir = self.get_version_dir(version)
        if not version_dir.exists():
            logger.warning(f"版本目录不存在: {version_dir}")
            return

        archive_dir = archive_dir or self.output_dir / "archive"
        archive_dir.mkdir(parents=True, exist_ok=True)

        archive_path = archive_dir / f"v{version}"
        if archive_path.exists():
            shutil.rmtree(archive_path)

        shutil.move(str(version_dir), str(archive_path))
        logger.info(f"版本 v{version} 已归档到 {archive_path}")


class TestResultCollector:
    """测试结果收集器"""

    def __init__(self, config: ReportConfig):
        self.config = config

    def collect(self) -> TestReport:
        """收集所有测试结果"""
        logger.info("开始收集测试结果...")

        report = TestReport(
            title="Sanliu 技能测试报告",
            version=self.config.version,
            timestamp=datetime.now()
        )

        # 收集 pytest 结果
        pytest_suites = self._collect_pytest_results()
        report.suites.extend(pytest_suites)

        # 收集 Playwright 结果
        playwright_suites = self._collect_playwright_results()
        report.suites.extend(playwright_suites)

        # 收集覆盖率结果
        if self.config.collect_coverage:
            coverage_data = self._collect_coverage_results()
            report.metadata["coverage"] = coverage_data

        # 收集历史数据
        if self.config.include_history:
            history_data = self._collect_history()
            report.metadata["history"] = history_data

        # 计算摘要
        report.summary = self._calculate_summary(report)

        logger.info(f"收集完成 - 共 {len(report.suites)} 个测试套件")
        return report

    def _collect_pytest_results(self) -> list[TestSuite]:
        """收集 pytest 测试结果"""
        suites = []

        # 查找 pytest 结果文件
        result_files = []
        for results_dir in self.config.test_results_dirs:
            if results_dir.exists():
                result_files.extend(results_dir.rglob("*.xml"))
                result_files.extend(results_dir.rglob("pytest-report.json"))

        # 解析 JUnit XML 格式
        for xml_file in result_files:
            if xml_file.suffix == '.xml':
                try:
                    suite = self._parse_junit_xml(xml_file)
                    if suite:
                        suites.append(suite)
                except Exception as e:
                    logger.error(f"解析 JUnit XML 失败: {xml_file} - {e}")

        return suites

    def _parse_junit_xml(self, xml_file: Path) -> Optional[TestSuite]:
        """解析 JUnit XML 文件"""
        try:
            tree = ET.parse(xml_file)
            root = tree.getroot()

            # 处理 testsuites 或 testsuite 根元素
            if root.tag == 'testsuites':
                test_elements = root.findall('.//testcase')
                suite_name = root.get('name', 'Test Suite')
            else:
                test_elements = root.findall('testcase')
                suite_name = root.get('name', xml_file.stem)

            suite = TestSuite(name=suite_name)

            for testcase in test_elements:
                test_case = TestCase(
                    name=testcase.get('name', 'Unknown'),
                    suite=testcase.get('classname', suite_name),
                    duration=float(testcase.get('time', 0)),
                    file=testcase.get('file', ''),
                    line=int(testcase.get('line', 0))
                )

                # 检查失败、错误、跳过
                failure = testcase.find('failure')
                error = testcase.find('error')
                skipped = testcase.find('skipped')

                if failure is not None:
                    test_case.status = 'failed'
                    test_case.message = failure.get('message', '')
                    test_case.stack_trace = failure.text or ''
                    suite.failed_tests += 1
                elif error is not None:
                    test_case.status = 'error'
                    test_case.message = error.get('message', '')
                    test_case.stack_trace = error.text or ''
                    suite.error_tests += 1
                elif skipped is not None:
                    test_case.status = 'skipped'
                    test_case.message = skipped.get('message', '')
                    suite.skipped_tests += 1
                else:
                    test_case.status = 'passed'
                    suite.passed_tests += 1

                suite.tests.append(test_case)
                suite.total_tests += 1
                suite.duration += test_case.duration

            return suite

        except Exception as e:
            logger.error(f"解析 XML 文件失败: {xml_file} - {e}")
            return None

    def _collect_playwright_results(self) -> list[TestSuite]:
        """收集 Playwright 测试结果"""
        suites = []

        for results_dir in self.config.test_results_dirs:
            # 查找 Playwright JSON 报告
            json_file = results_dir / "playwright-report.json"
            if json_file.exists():
                try:
                    with open(json_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)

                    suite = TestSuite(name="Playwright E2E Tests")

                    for test in data.get('suites', []):
                        for spec in test.get('specs', []):
                            for test_result in spec.get('tests', []):
                                test_case = TestCase(
                                    name=spec.get('title', 'Unknown'),
                                    suite=test.get('title', ''),
                                    duration=test_result.get('results', [{}])[0].get('duration', 0) / 1000
                                )

                                status = test_result.get('results', [{}])[0].get('status', 'unknown')
                                if status == 'passed':
                                    test_case.status = 'passed'
                                    suite.passed_tests += 1
                                elif status == 'failed':
                                    test_case.status = 'failed'
                                    suite.failed_tests += 1
                                elif status == 'skipped':
                                    test_case.status = 'skipped'
                                    suite.skipped_tests += 1

                                suite.tests.append(test_case)
                                suite.total_tests += 1

                    suites.append(suite)

                except Exception as e:
                    logger.error(f"解析 Playwright 报告失败: {e}")

        return suites

    def _collect_coverage_results(self) -> dict[str, Any]:
        """收集覆盖率结果"""
        coverage_data = {}

        for results_dir in self.config.test_results_dirs:
            # 查找 coverage.json
            coverage_file = results_dir / "coverage.json"
            if coverage_file.exists():
                try:
                    with open(coverage_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)

                    totals = data.get('totals', {})
                    coverage_data = {
                        'percent_covered': totals.get('percent_covered', 0),
                        'covered_lines': totals.get('covered_lines', 0),
                        'missing_lines': totals.get('missing_lines', 0),
                        'excluded_lines': totals.get('excluded_lines', 0),
                        'num_statements': totals.get('num_statements', 0)
                    }

                except Exception as e:
                    logger.error(f"解析覆盖率报告失败: {e}")

        return coverage_data

    def _collect_history(self) -> list[dict[str, Any]]:
        """收集历史测试数据"""
        history = []

        # 查找历史报告
        if self.config.output_dir.exists():
            cutoff_date = datetime.now() - timedelta(days=self.config.history_days)

            for report_file in self.config.output_dir.rglob("*.json"):
                try:
                    # 从文件名解析日期
                    date_match = re.search(r'(\d{8})', report_file.stem)
                    if date_match:
                        report_date = datetime.strptime(date_match.group(1), '%Y%m%d')
                        if report_date >= cutoff_date:
                            with open(report_file, 'r', encoding='utf-8') as f:
                                data = json.load(f)

                            history.append({
                                'date': report_date.isoformat(),
                                'total_tests': data.get('summary', {}).get('total_tests', 0),
                                'passed_tests': data.get('summary', {}).get('passed_tests', 0),
                                'failed_tests': data.get('summary', {}).get('failed_tests', 0),
                                'coverage': data.get('metadata', {}).get('coverage', {}).get('percent_covered', 0)
                            })

                except Exception as e:
                    logger.warning(f"解析历史报告失败: {report_file} - {e}")

        # 按日期排序
        history.sort(key=lambda x: x['date'])
        return history

    def _calculate_summary(self, report: TestReport) -> dict[str, Any]:
        """计算报告摘要"""
        total_tests = sum(s.total_tests for s in report.suites)
        passed_tests = sum(s.passed_tests for s in report.suites)
        failed_tests = sum(s.failed_tests for s in report.suites)
        skipped_tests = sum(s.skipped_tests for s in report.suites)
        error_tests = sum(s.error_tests for s in report.suites)
        total_duration = sum(s.duration for s in report.suites)

        return {
            'total_suites': len(report.suites),
            'total_tests': total_tests,
            'passed_tests': passed_tests,
            'failed_tests': failed_tests,
            'skipped_tests': skipped_tests,
            'error_tests': error_tests,
            'pass_rate': (passed_tests / total_tests * 100) if total_tests > 0 else 0,
            'total_duration': total_duration,
            'avg_duration': total_duration / len(report.suites) if report.suites else 0
        }


class ReportGenerator:
    """报告生成器"""

    def __init__(self, config: ReportConfig):
        self.config = config
        self.collector = TestResultCollector(config)
        self.version_controller = ReportVersionController(config.output_dir)

    def generate(self) -> dict[str, Any]:
        """生成测试报告"""
        report = self.collector.collect()

        coverage = report.metadata.get('coverage', {})
        summary_with_coverage = {
            **report.summary,
            'coverage': coverage.get('percent_covered', 0)
        }

        version_dir = self.version_controller.create_version(
            version=self.config.version,
            summary=summary_with_coverage
        )

        if self.config.format == "html":
            result = self._generate_html(report)
        elif self.config.format == "markdown":
            result = self._generate_markdown(report)
        else:
            result = self._generate_json(report)

        self._generate_version_index()

        return result

    def _generate_version_index(self):
        """生成版本索引页面"""
        versions = self.version_controller.list_versions()

        index_file = self.config.output_dir / "README.md"
        with open(index_file, 'w', encoding='utf-8') as f:
            f.write("# Sanliu 技能测试报告版本索引\n\n")
            f.write(f"**更新时间**: {datetime.now().isoformat()}\n\n")
            f.write("## 可用版本\n\n")

            if versions:
                f.write("| 版本 | 创建时间 | 测试数 | 通过率 | 覆盖率 | 状态 |\n")
                f.write("|------|----------|--------|--------|--------|------|\n")
                for ver in versions:
                    status = "✅ 稳定" if ver['is_stable'] else "⚠️ 有失败"
                    f.write(f"| [v{ver['version']}](./v{ver['version']}/) | {ver['created_at'][:10]} | {ver['total_tests']} | {ver['pass_rate']:.1f}% | {ver['coverage']:.1f}% | {status} |\n")
            else:
                f.write("暂无版本记录\n")

            f.write("\n## 使用说明\n\n")
            f.write("```bash\n")
            f.write("# 生成测试报告\n")
            f.write("python scripts/test_report_generator.py --collect --version 1.0.0\n")
            f.write("\n")
            f.write("# 递增版本号\n")
            f.write("python scripts/test_report_generator.py --bump minor\n")
            f.write("```\n")

        logger.info(f"版本索引已生成: {index_file}")

    def _generate_html(self, report: TestReport) -> dict[str, Any]:
        """生成 HTML 报告"""
        output_dir = self.config.output_dir / f"v{self.config.version}"
        output_dir.mkdir(parents=True, exist_ok=True)

        timestamp_str = report.timestamp.strftime("%Y%m%d_%H%M%S")
        output_file = output_dir / f"test_report_{timestamp_str}.html"

        html_content = self._build_html_report(report)

        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html_content)

        logger.info(f"HTML 报告已生成: {output_file}")

        return {
            "format": "html",
            "output_file": str(output_file),
            "version": self.config.version
        }

    def _build_html_report(self, report: TestReport) -> str:
        """构建 HTML 报告内容"""
        summary = report.summary
        coverage = report.metadata.get('coverage', {})
        history = report.metadata.get('history', [])

        # 计算通过率颜色
        pass_rate = summary['pass_rate']
        if pass_rate >= 90:
            pass_color = "#27ae60"
        elif pass_rate >= 70:
            pass_color = "#f39c12"
        else:
            pass_color = "#e74c3c"

        html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{report.title}</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            line-height: 1.6;
            background: #f5f7fa;
            color: #333;
        }}
        .container {{ max-width: 1400px; margin: 0 auto; padding: 20px; }}
        header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            border-radius: 12px;
            margin-bottom: 30px;
        }}
        header h1 {{ font-size: 2.5em; margin-bottom: 10px; }}
        header p {{ opacity: 0.9; }}
        .summary-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}
        .summary-card {{
            background: white;
            padding: 25px;
            border-radius: 12px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            transition: transform 0.2s;
        }}
        .summary-card:hover {{ transform: translateY(-5px); }}
        .summary-card h3 {{
            font-size: 0.9em;
            color: #7f8c8d;
            text-transform: uppercase;
            letter-spacing: 1px;
            margin-bottom: 10px;
        }}
        .summary-card .value {{
            font-size: 2.5em;
            font-weight: bold;
            color: #2c3e50;
        }}
        .summary-card .sub-value {{
            font-size: 0.9em;
            color: #7f8c8d;
            margin-top: 5px;
        }}
        .pass-rate {{ color: {pass_color} !important; }}
        .section {{
            background: white;
            padding: 25px;
            border-radius: 12px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            margin-bottom: 20px;
        }}
        .section h2 {{
            color: #2c3e50;
            margin-bottom: 20px;
            padding-bottom: 10px;
            border-bottom: 2px solid #ecf0f1;
        }}
        .suite {{
            margin-bottom: 20px;
            padding: 15px;
            background: #f8f9fa;
            border-radius: 8px;
        }}
        .suite-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 10px;
        }}
        .suite-name {{ font-weight: bold; color: #2c3e50; }}
        .suite-stats {{ font-size: 0.9em; color: #7f8c8d; }}
        .test-list {{ margin-top: 10px; }}
        .test-item {{
            display: flex;
            align-items: center;
            padding: 8px 12px;
            margin: 5px 0;
            border-radius: 6px;
            font-size: 0.9em;
        }}
        .test-passed {{ background: #d4edda; color: #155724; }}
        .test-failed {{ background: #f8d7da; color: #721c24; }}
        .test-skipped {{ background: #fff3cd; color: #856404; }}
        .test-error {{ background: #f5c6cb; color: #721c24; }}
        .status-icon {{ margin-right: 10px; font-weight: bold; }}
        .coverage-bar {{
            height: 30px;
            background: #ecf0f1;
            border-radius: 15px;
            overflow: hidden;
            margin-top: 10px;
        }}
        .coverage-fill {{
            height: 100%;
            background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-weight: bold;
            transition: width 0.5s ease;
        }}
        .chart-container {{
            height: 300px;
            margin-top: 20px;
        }}
        .trend-table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 15px;
        }}
        .trend-table th, .trend-table td {{
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #ecf0f1;
        }}
        .trend-table th {{
            background: #f8f9fa;
            font-weight: 600;
            color: #2c3e50;
        }}
        .trend-table tr:hover {{ background: #f8f9fa; }}
        .badge {{
            display: inline-block;
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 0.75em;
            font-weight: bold;
        }}
        .badge-success {{ background: #d4edda; color: #155724; }}
        .badge-warning {{ background: #fff3cd; color: #856404; }}
        .badge-danger {{ background: #f8d7da; color: #721c24; }}
        footer {{
            text-align: center;
            padding: 20px;
            color: #7f8c8d;
            font-size: 0.9em;
        }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>{report.title}</h1>
            <p>版本 {report.version} | 生成时间: {report.timestamp.strftime('%Y-%m-%d %H:%M:%S')}</p>
        </header>

        <div class="summary-grid">
            <div class="summary-card">
                <h3>总测试数</h3>
                <div class="value">{summary['total_tests']}</div>
                <div class="sub-value">{summary['total_suites']} 个测试套件</div>
            </div>
            <div class="summary-card">
                <h3>通过率</h3>
                <div class="value pass-rate">{pass_rate:.1f}%</div>
                <div class="sub-value">{summary['passed_tests']} 个通过</div>
            </div>
            <div class="summary-card">
                <h3>失败数</h3>
                <div class="value" style="color: #e74c3c;">{summary['failed_tests']}</div>
                <div class="sub-value">{summary['error_tests']} 个错误</div>
            </div>
            <div class="summary-card">
                <h3>代码覆盖率</h3>
                <div class="value">{coverage.get('percent_covered', 0):.1f}%</div>
                <div class="sub-value">{coverage.get('covered_lines', 0)} / {coverage.get('num_statements', 0)} 行</div>
            </div>
        </div>
"""

        # 覆盖率详情
        if coverage:
            html += f"""
        <div class="section">
            <h2>代码覆盖率</h2>
            <div class="coverage-bar">
                <div class="coverage-fill" style="width: {coverage.get('percent_covered', 0)}%">
                    {coverage.get('percent_covered', 0):.1f}%
                </div>
            </div>
            <div style="margin-top: 15px; display: grid; grid-template-columns: repeat(3, 1fr); gap: 15px; text-align: center;">
                <div>
                    <div style="font-size: 1.5em; font-weight: bold; color: #27ae60;">{coverage.get('covered_lines', 0)}</div>
                    <div style="color: #7f8c8d;">已覆盖行</div>
                </div>
                <div>
                    <div style="font-size: 1.5em; font-weight: bold; color: #e74c3c;">{coverage.get('missing_lines', 0)}</div>
                    <div style="color: #7f8c8d;">未覆盖行</div>
                </div>
                <div>
                    <div style="font-size: 1.5em; font-weight: bold; color: #3498db;">{coverage.get('excluded_lines', 0)}</div>
                    <div style="color: #7f8c8d;">排除行</div>
                </div>
            </div>
        </div>
"""

        # 测试套件详情
        html += """
        <div class="section">
            <h2>测试套件详情</h2>
"""

        for suite in report.suites:
            suite_pass_rate = (suite.passed_tests / suite.total_tests * 100) if suite.total_tests > 0 else 0
            html += f"""
            <div class="suite">
                <div class="suite-header">
                    <span class="suite-name">{suite.name}</span>
                    <span class="suite-stats">
                        {suite.total_tests} 个测试 | 
                        {suite.passed_tests} 通过 | 
                        {suite.failed_tests} 失败 | 
                        {suite.skipped_tests} 跳过 |
                        耗时 {suite.duration:.2f}s
                    </span>
                </div>
                <div class="test-list">
"""

            for test in suite.tests[:10]:  # 只显示前10个
                status_class = f"test-{test.status}"
                icon = "✓" if test.status == "passed" else "✗" if test.status == "failed" else "⊘" if test.status == "skipped" else "⚠"
                html += f"""
                    <div class="test-item {status_class}">
                        <span class="status-icon">{icon}</span>
                        <span>{test.name}</span>
                        <span style="margin-left: auto; color: #7f8c8d;">{test.duration:.3f}s</span>
                    </div>
"""

            if len(suite.tests) > 10:
                html += f'<div style="text-align: center; padding: 10px; color: #7f8c8d;">... 还有 {len(suite.tests) - 10} 个测试 ...</div>'

            html += """
                </div>
            </div>
"""

        html += """
        </div>
"""

        # 历史趋势
        if history:
            html += """
        <div class="section">
            <h2>历史趋势</h2>
            <table class="trend-table">
                <thead>
                    <tr>
                        <th>日期</th>
                        <th>总测试数</th>
                        <th>通过数</th>
                        <th>失败数</th>
                        <th>覆盖率</th>
                        <th>状态</th>
                    </tr>
                </thead>
                <tbody>
"""

            for record in history[-10:]:  # 最近10条
                status_badge = "badge-success" if record['failed_tests'] == 0 else "badge-warning" if record['failed_tests'] < 5 else "badge-danger"
                status_text = "通过" if record['failed_tests'] == 0 else "警告" if record['failed_tests'] < 5 else "失败"

                html += f"""
                    <tr>
                        <td>{record['date'][:10]}</td>
                        <td>{record['total_tests']}</td>
                        <td>{record['passed_tests']}</td>
                        <td>{record['failed_tests']}</td>
                        <td>{record['coverage']:.1f}%</td>
                        <td><span class="badge {status_badge}">{status_text}</span></td>
                    </tr>
"""

            html += """
                </tbody>
            </table>
        </div>
"""

        html += f"""
        <footer>
            <p>Sanliu 技能测试报告 | 生成时间: {report.timestamp.strftime('%Y-%m-%d %H:%M:%S')}</p>
        </footer>
    </div>
</body>
</html>
"""

        return html

    def _generate_markdown(self, report: TestReport) -> dict[str, Any]:
        """生成 Markdown 报告"""
        output_dir = self.config.output_dir / f"v{self.config.version}"
        output_dir.mkdir(parents=True, exist_ok=True)

        timestamp_str = report.timestamp.strftime("%Y%m%d_%H%M%S")
        output_file = output_dir / f"test_report_{timestamp_str}.md"

        summary = report.summary
        coverage = report.metadata.get('coverage', {})

        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(f"# {report.title}\n\n")
            f.write(f"**版本**: {report.version}\n\n")
            f.write(f"**生成时间**: {report.timestamp.isoformat()}\n\n")

            # 摘要
            f.write("## 执行摘要\n\n")
            f.write(f"| 指标 | 数值 |\n")
            f.write(f"|------|------|\n")
            f.write(f"| 测试套件数 | {summary['total_suites']} |\n")
            f.write(f"| 总测试数 | {summary['total_tests']} |\n")
            f.write(f"| 通过 | {summary['passed_tests']} |\n")
            f.write(f"| 失败 | {summary['failed_tests']} |\n")
            f.write(f"| 跳过 | {summary['skipped_tests']} |\n")
            f.write(f"| 错误 | {summary['error_tests']} |\n")
            f.write(f"| 通过率 | {summary['pass_rate']:.2f}% |\n")
            f.write(f"| 总耗时 | {summary['total_duration']:.2f}s |\n")
            f.write(f"| 代码覆盖率 | {coverage.get('percent_covered', 0):.2f}% |\n\n")

            # 覆盖率详情
            if coverage:
                f.write("## 代码覆盖率详情\n\n")
                f.write(f"- **已覆盖行**: {coverage.get('covered_lines', 0)}\n")
                f.write(f"- **未覆盖行**: {coverage.get('missing_lines', 0)}\n")
                f.write(f"- **排除行**: {coverage.get('excluded_lines', 0)}\n")
                f.write(f"- **总行数**: {coverage.get('num_statements', 0)}\n\n")

            # 测试套件详情
            f.write("## 测试套件详情\n\n")
            for suite in report.suites:
                f.write(f"### {suite.name}\n\n")
                f.write(f"- 总测试数: {suite.total_tests}\n")
                f.write(f"- 通过: {suite.passed_tests}\n")
                f.write(f"- 失败: {suite.failed_tests}\n")
                f.write(f"- 跳过: {suite.skipped_tests}\n")
                f.write(f"- 耗时: {suite.duration:.2f}s\n\n")

                if suite.failed_tests > 0:
                    f.write("**失败的测试**:\n\n")
                    for test in suite.tests:
                        if test.status in ['failed', 'error']:
                            f.write(f"- ❌ {test.name}\n")
                            if test.message:
                                f.write(f"  - 错误: {test.message}\n")
                    f.write("\n")

        logger.info(f"Markdown 报告已生成: {output_file}")

        return {
            "format": "markdown",
            "output_file": str(output_file),
            "version": self.config.version
        }

    def _generate_json(self, report: TestReport) -> dict[str, Any]:
        """生成 JSON 报告"""
        output_dir = self.config.output_dir / f"v{self.config.version}"
        output_dir.mkdir(parents=True, exist_ok=True)

        timestamp_str = report.timestamp.strftime("%Y%m%d_%H%M%S")
        output_file = output_dir / f"test_report_{timestamp_str}.json"

        data = {
            "metadata": {
                "title": report.title,
                "version": report.version,
                "timestamp": report.timestamp.isoformat()
            },
            "summary": report.summary,
            "metadata_extended": report.metadata,
            "suites": []
        }

        for suite in report.suites:
            suite_data = {
                "name": suite.name,
                "total_tests": suite.total_tests,
                "passed_tests": suite.passed_tests,
                "failed_tests": suite.failed_tests,
                "skipped_tests": suite.skipped_tests,
                "error_tests": suite.error_tests,
                "duration": suite.duration,
                "tests": []
            }

            for test in suite.tests:
                suite_data["tests"].append({
                    "name": test.name,
                    "status": test.status,
                    "duration": test.duration,
                    "message": test.message,
                    "suite": test.suite
                })

            data["suites"].append(suite_data)

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        logger.info(f"JSON 报告已生成: {output_file}")

        return {
            "format": "json",
            "output_file": str(output_file),
            "version": self.config.version
        }


def parse_args() -> ReportConfig:
    """解析命令行参数"""
    parser = argparse.ArgumentParser(
        description="测试报告生成脚本 - Sanliu 技能",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 收集并生成 HTML 报告
  python scripts/test_report_generator.py --collect --format html

  # 指定输出目录
  python scripts/test_report_generator.py --output docs/reports --version 1.2.0

  # 生成 Markdown 报告
  python scripts/test_report_generator.py --format markdown

  # 包含历史趋势
  python scripts/test_report_generator.py --include-history --history-days 30

  # 递增版本号
  python scripts/test_report_generator.py --bump minor

  # 列出所有版本
  python scripts/test_report_generator.py --list-versions

  # 比较两个版本
  python scripts/test_report_generator.py --compare 1.0.0 1.1.0
        """
    )

    parser.add_argument(
        "--collect",
        action="store_true",
        help="自动收集测试结果"
    )

    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="报告输出目录 (默认: docs/reports)"
    )

    parser.add_argument(
        "--format",
        choices=["html", "markdown", "json"],
        default="html",
        help="报告格式 (默认: html)"
    )

    parser.add_argument(
        "--version",
        default="1.0.0",
        help="报告版本号 (默认: 1.0.0)"
    )

    parser.add_argument(
        "--no-coverage",
        action="store_true",
        help="不包含覆盖率数据"
    )

    parser.add_argument(
        "--include-history",
        action="store_true",
        help="包含历史趋势数据"
    )

    parser.add_argument(
        "--history-days",
        type=int,
        default=30,
        help="历史数据天数 (默认: 30)"
    )

    parser.add_argument(
        "--test-results-dirs",
        nargs="+",
        type=Path,
        default=None,
        help="测试结果目录列表"
    )

    parser.add_argument(
        "--bump",
        choices=["major", "minor", "patch"],
        help="递增版本号 (major/minor/patch)"
    )

    parser.add_argument(
        "--list-versions",
        action="store_true",
        help="列出所有版本"
    )

    parser.add_argument(
        "--compare",
        nargs=2,
        metavar=("VERSION1", "VERSION2"),
        help="比较两个版本"
    )

    parser.add_argument(
        "--trend",
        type=int,
        metavar="DAYS",
        help="显示最近N天的趋势"
    )

    parser.add_argument(
        "--archive",
        metavar="VERSION",
        help="归档指定版本"
    )

    args = parser.parse_args()

    if args.test_results_dirs is None:
        path_manager = PathConfigManager(auto_detect=True)
        args.test_results_dirs = [
            path_manager.get_backend_path(),
            path_manager.get_frontend_path()
        ]

    if args.list_versions or args.compare or args.trend or args.archive:
        return args

    return ReportConfig(
        output_dir=args.output,
        format=args.format,
        version=args.version,
        collect_coverage=not args.no_coverage,
        include_history=args.include_history,
        history_days=args.history_days,
        test_results_dirs=args.test_results_dirs
    )


def main():
    """主入口函数"""
    try:
        args = parse_args()

        if isinstance(args, ReportConfig):
            config = args

            if config.bump:
                version_controller = ReportVersionController(config.output_dir)
                new_version = version_controller.bump_version(VersionPart(config.bump))
                config.version = new_version
                print(f"\n版本号已递增至: {new_version}")

            generator = ReportGenerator(config)
            result = generator.generate()

            print("\n" + "=" * 60)
            print("测试报告生成完成")
            print("=" * 60)
            print(f"格式: {result['format']}")
            print(f"版本: {result['version']}")
            print(f"输出文件: {result['output_file']}")
            print("=" * 60)

        else:
            try:
                from skillscripts.utils.enhanced_path_config_manager import create_path_manager, PathKey
                _manager = create_path_manager()
                output_dir = _manager.resolve_path(PathKey.DOCS_DIR) / "reports"
            except Exception:
                output_dir = Path("docs/reports")
            version_controller = ReportVersionController(output_dir)

            if args.list_versions:
                versions = version_controller.list_versions()
                print("\n" + "=" * 60)
                print("测试报告版本列表")
                print("=" * 60)
                if versions:
                    for ver in versions:
                        status = "✅ 稳定" if ver['is_stable'] else "⚠️ 有失败"
                        print(f"  v{ver['version']} - {ver['created_at'][:10]} - {ver['total_tests']} 测试 - {ver['pass_rate']:.1f}% 通过 - {status}")
                else:
                    print("  暂无版本记录")
                print("=" * 60)

            elif args.compare:
                result = version_controller.compare_versions(args.compare[0], args.compare[1])
                print("\n" + "=" * 60)
                print("版本比较")
                print("=" * 60)
                print(f"版本1: {result['version1']} {'(存在)' if result['v1_exists'] else '(不存在)'}")
                print(f"版本2: {result['version2']} {'(存在)' if result['v2_exists'] else '(不存在)'}")
                if result['difference']:
                    diff = result['difference']
                    print(f"测试数变化: {diff['total_tests']:+d}")
                    print(f"通过数变化: {diff['passed_tests']:+d}")
                    print(f"失败数变化: {diff['failed_tests']:+d}")
                    print(f"覆盖率变化: {diff['coverage']:+.2f}%")
                    print(f"通过率变化: {diff['pass_rate']:+.2f}%")
                print("=" * 60)

            elif args.trend:
                trend = version_controller.get_trend(args.trend)
                print("\n" + "=" * 60)
                print(f"最近 {args.trend} 天趋势")
                print("=" * 60)
                if trend:
                    for record in trend:
                        print(f"  {record['date'][:10]} v{record['version']}: {record['total_tests']} 测试, {record['pass_rate']:.1f}% 通过, {record['coverage']:.1f}% 覆盖")
                else:
                    print("  暂无趋势数据")
                print("=" * 60)

            elif args.archive:
                version_controller.archive_version(args.archive)
                print(f"\n版本 v{args.archive} 已归档")

        sys.exit(0)

    except KeyboardInterrupt:
        logger.info("用户中断执行")
        sys.exit(130)
    except Exception as e:
        logger.error(f"执行失败: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
