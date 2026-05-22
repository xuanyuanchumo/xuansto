#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
自动报告生成器 - Auto Report Generator

功能：
- 自动收集测试结果数据
- 生成Markdown格式报告
- 归档到 docs/迭代版本/v{version}/ 目录
- 支持版本号自动递增
"""

import os
import sys
import json
import yaml
import re
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any


class AutoReportGenerator:
    """自动报告生成器"""

    def __init__(self, base_dir: str = None):
        self.base_dir = Path(base_dir) if base_dir else Path(__file__).parent.parent.parent
        self.docs_dir = self.base_dir / "docs" / "迭代版本"
        self.reports_dir = self.base_dir / "reports"
        self.quality_config = self._load_quality_config()

    def _load_quality_config(self) -> Dict:
        """加载质量门禁配置"""
        config_path = self.base_dir / "skillscripts" / "core" / "quality_gate_config.yaml"
        if config_path.exists():
            with open(config_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        return {}

    def get_current_version(self) -> str:
        """获取当前版本号（从CHANGELOG或配置文件中读取）"""
        version_dirs = sorted([d for d in self.docs_dir.iterdir() if d.is_dir() and d.name.startswith('v')])
        if not version_dirs:
            return "3.3.0"
        
        latest_version = version_dirs[-1].name.replace('v', '')
        parts = latest_version.split('.')
        major, minor, patch = int(parts[0]), int(parts[1]), int(parts[2])
        return f"{major}.{minor}.{patch + 1}"

    def increment_version(self, current_version: str, increment_type: str = 'patch') -> str:
        """
        递增版本号
        
        Args:
            current_version: 当前版本号 (如 "3.3.0")
            increment_type: 递增类型 ('major', 'minor', 'patch')
        
        Returns:
            新版本号字符串
        """
        parts = current_version.split('.')
        major, minor, patch = int(parts[0]), int(parts[1]), int(parts[2])

        if increment_type == 'major':
            major += 1
            minor = 0
            patch = 0
        elif increment_type == 'minor':
            minor += 1
            patch = 0
        else:
            patch += 1

        return f"{major}.{minor}.{patch}"

    def collect_test_results(self) -> Dict[str, Any]:
        """收集所有测试结果数据"""
        results = {
            'timestamp': datetime.now().isoformat(),
            'skillscripts': {},
            'backend': {},
            'frontend': {},
            'security': {}
        }

        # 收集 skillscripts 测试结果
        skillscripts_cov_path = self.base_dir / "skillscripts" / "htmlcov"
        if skillscripts_cov_path.exists():
            results['skillscripts']['coverage'] = self._parse_coverage_data(skillscripts_cov_path)

        # 收集 backend 测试结果
        backend_cov_path = self.base_dir / "backend" / "htmlcov"
        if backend_cov_path.exists():
            results['backend']['coverage'] = self._parse_coverage_data(backend_cov_path)

        backend_test_results = self.base_dir / "backend" / "test-results.xml"
        if backend_test_results.exists():
            results['backend']['junit'] = self._parse_junit_xml(backend_test_results)

        # 收集安全扫描结果
        security_dir = self.base_dir / "security-reports"
        if security_dir.exists():
            bandit_report = security_dir / "bandit-report.json"
            safety_report = security_dir / "safety-report.json"

            if bandit_report.exists():
                with open(bandit_report, 'r', encoding='utf-8') as f:
                    results['security']['bandit'] = json.load(f)
            
            if safety_report.exists():
                with open(safety_report, 'r', encoding='utf-8') as f:
                    results['security']['safety'] = json.load(f)

        return results

    def _parse_coverage_data(self, cov_dir: Path) -> Dict[str, float]:
        """解析覆盖率数据"""
        coverage_json = cov_dir / "coverage.json"
        if coverage_json.exists():
            with open(coverage_json, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return {
                    'line_coverage': data.get('totals', {}).get('percent_covered', 0),
                    'branch_coverage': data.get('totals', {}).get('percent_covered_branches', 0),
                    'function_coverage': data.get('totals', {}).get('percent_covered_functions', 0)
                }
        return {'line_coverage': 0, 'branch_coverage': 0, 'function_coverage': 0}

    def _parse_junit_xml(self, xml_path: Path) -> Dict[str, Any]:
        """解析JUnit XML格式的测试结果"""
        try:
            import xml.etree.ElementTree as ET
            tree = ET.parse(xml_path)
            root = tree.getroot()
            
            tests = int(root.attrib.get('tests', 0))
            failures = int(root.attrib.get('failures', 0))
            errors = int(root.attrib.get('errors', 0))
            skipped = int(root.attrib.get('skipped', 0))

            return {
                'total': tests,
                'passed': tests - failures - errors - skipped,
                'failures': failures,
                'errors': errors,
                'skipped': skipped,
                'pass_rate': ((tests - failures - errors) / tests * 100) if tests > 0 else 0
            }
        except Exception as e:
            print(f"Warning: Failed to parse JUnit XML: {e}")
            return {'total': 0, 'passed': 0, 'failures': 0, 'errors': 0, 'skipped': 0, 'pass_rate': 0}

    def generate_markdown_report(self, test_results: Dict, version: str) -> str:
        """生成Markdown格式的测试报告"""
        
        report_lines = [
            f"# 三省六部技能 v{version} 测试报告",
            "",
            f"> **生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"> **版本**: v{version}",
            "",
            "---",
            "",
            "## 📊 测试执行摘要",
            ""
        ]

        # 后端测试摘要
        if test_results.get('backend', {}).get('junit'):
            junit = test_results['backend']['junit']
            report_lines.extend([
                "### 后端单元测试",
                "",
                "| 指标 | 数值 |",
                "|------|------|",
                f"| 总用例数 | {junit['total']} |",
                f"| 通过数 | {junit['passed']} ✅ |",
                f"| 失败数 | {junit['failures']} ❌ |",
                f"| 错误数 | {junit['errors']} ⚠️ |",
                f"| 跳过数 | {junit['skipped']} ⏭️ |",
                f"| 通过率 | {junit['pass_rate']:.1f}% |",
                ""
            ])

        # 覆盖率摘要
        report_lines.append("### 代码覆盖率")
        report_lines.append("")
        report_lines.append("| 模块 | 行覆盖率 | 分支覆盖率 | 函数覆盖率 | 状态 |")
        report_lines.append("|------|----------|------------|------------|------|")

        for module_name, coverage in [('Skillscripts', test_results.get('skillscripts', {}).get('coverage', {})),
                                       ('Backend', test_results.get('backend', {}).get('coverage', {}))]:
            line_cov = coverage.get('line_coverage', 0)
            branch_cov = coverage.get('branch_coverage', 0)
            func_cov = coverage.get('function_coverage', 0)
            
            status = "✅" if line_cov >= self.quality_config.get('quality_gate', {}).get('coverage', {}).get('line_coverage_min', 95) else "❌"
            
            report_lines.append(
                f"| {module_name} | {line_cov:.1f}% | {branch_cov:.1f}% | {func_cov:.1f}% | {status} |"
            )
        
        report_lines.append("")

        # 安全扫描结果
        if test_results.get('security'):
            report_lines.extend([
                "## 🔒 安全扫描结果",
                ""
            ])

            bandit = test_results['security'].get('bandit')
            if bandit:
                report_lines.extend([
                    "### Bandit 安全扫描",
                    "",
                    f"- 扫描文件数: {len(bandit.get('results', []))}",
                    f"- 发现问题数: {len([r for r in bandit.get('results', []) if r.get('issue_severity') in ['HIGH', 'MEDIUM']])}",
                    ""
                ])

            safety = test_results['security'].get('safety')
            if safety:
                report_lines.extend([
                    "### Safety 依赖检查",
                    "",
                    "- 已检查依赖包安全性",
                    ""
                ])

        # 质量门禁检查结果
        report_lines.extend([
            "## ✅ 质量门禁检查",
            "",
            "| 检查项 | 阈值 | 实际值 | 结果 |",
            "|--------|------|--------|------|"
        ])

        gate_config = self.quality_config.get('quality_gate', {})
        
        for check_name, config in gate_config.items():
            if isinstance(config, dict):
                for metric, threshold in config.items():
                    actual_value = self._get_actual_value(test_results, check_name, metric)
                    threshold_val = list(threshold.values())[0] if isinstance(threshold, dict) else threshold
                    
                    if isinstance(actual_value, (int, float)):
                        passed = actual_value >= threshold_val if 'min' in metric or 'rate' in metric or 'correctness' in metric else actual_value <= threshold_val
                        status = "✅ 通过" if passed else "❌ 未通过"
                        
                        report_lines.append(
                            f"| {check_name}/{metric} | {threshold_val} | {actual_value} | {status} |"
                        )

        report_lines.extend([
            "",
            "---",
            "",
            "*此报告由 AutoReportGenerator 自动生成*",
            f"*生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*"
        ])

        return '\n'.join(report_lines)

    def _get_actual_value(self, test_results: Dict, category: str, metric: str) -> float:
        """获取实际测量值"""
        try:
            if category == 'coverage':
                backend_cov = test_results.get('backend', {}).get('coverage', {})
                if 'line' in metric:
                    return backend_cov.get('line_coverage', 0)
                elif 'branch' in metric:
                    return backend_cov.get('branch_coverage', 0)
                elif 'function' in metric:
                    return backend_cov.get('function_coverage', 0)
            
            elif category == 'testing':
                junit = test_results.get('backend', {}).get('junit', {})
                if 'pass_rate' in metric:
                    return junit.get('pass_rate', 0)
            
            return 0.0
        except Exception:
            return 0.0

    def save_report(self, content: str, version: str, report_type: str = "test") -> Path:
        """保存报告到指定目录"""
        version_dir = self.docs_dir / f"v{version}"
        version_dir.mkdir(parents=True, exist_ok=True)

        if report_type == "test":
            filename = "test_report.md"
        elif report_type == "changelog":
            filename = "CHANGELOG.md"
        elif report_type == "quality":
            filename = "quality_report.md"
        else:
            filename = f"{report_type}_report.md"

        report_path = version_dir / filename
        
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(content)

        print(f"✅ 报告已保存至: {report_path}")
        return report_path

    def generate_changelog(self, version: str, changes: List[str]) -> str:
        """生成变更日志"""
        
        changelog_lines = [
            f"# 三省六部技能 v{version} 变更日志",
            "",
            f"## 发布日期: {datetime.now().strftime('%Y-%m-%d')}",
            "",
            "---",
            "",
            "## 主要新功能",
            ""
        ]

        for change in changes:
            changelog_lines.append(f"- {change}")

        changelog_lines.extend([
            "",
            "---",
            "",
            "**维护者**: 三省六部开发团队",
            f"**最后更新**: {datetime.now().strftime('%Y-%m-%d')}"
        ])

        return '\n'.join(changelog_lines)


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='三省六部技能自动报告生成器')
    parser.add_argument('--version', type=str, default=None, help='指定版本号（如 3.3.0）')
    parser.add_argument('--increment', type=str, choices=['major', 'minor', 'patch'], 
                       default='patch', help='版本递增类型')
    parser.add_argument('--output-dir', type=str, default=None, help='输出目录')
    parser.add_argument('--generate-changelog', action='store_true', help='同时生成变更日志')
    parser.add_argument('--changes', type=str, nargs='+', help='变更内容列表')

    args = parser.parse_args()

    generator = AutoReportGenerator()

    # 确定版本号
    if args.version:
        version = args.version
    else:
        current_version = generator.get_current_version()
        version = generator.increment_version(current_version, args.increment)

    print(f"📝 正在为版本 v{version} 生成报告...")

    # 收集测试结果
    print("🔍 收集测试结果...")
    test_results = generator.collect_test_results()

    # 生成Markdown报告
    print("📊 生成测试报告...")
    report_content = generator.generate_markdown_report(test_results, version)
    
    # 保存报告
    report_path = generator.save_report(report_content, version, "test")

    # 可选：生成变更日志
    if args.generate_changelog and args.changes:
        print("📝 生成变更日志...")
        changelog_content = generator.generate_changelog(version, args.changes)
        generator.save_report(changelog_content, version, "changelog")

    print(f"\n✅ 报告生成完成！")
    print(f"   版本: v{version}")
    print(f"   报告路径: {report_path}")
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
