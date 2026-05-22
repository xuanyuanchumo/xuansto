"""
安全测试报告生成器

生成详细的安全测试报告，包括OWASP Top 10覆盖情况
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Any, Optional
from pathlib import Path
from dataclasses import dataclass, field, asdict
from enum import Enum


class Severity(Enum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    INFO = "INFO"


@dataclass
class SecurityFinding:
    test_name: str
    category: str
    severity: str
    description: str
    payload: Optional[str] = None
    response_code: Optional[int] = None
    endpoint: Optional[str] = None
    recommendation: Optional[str] = None
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class TestSummary:
    total_tests: int = 0
    passed: int = 0
    failed: int = 0
    warnings: int = 0
    skipped: int = 0
    duration_seconds: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class SecurityReportGenerator:
    def __init__(self, project_name: str = "三省六部技能项目"):
        self.project_name = project_name
        self.start_time = datetime.utcnow()
        self.end_time: Optional[datetime] = None
        self.findings: List[SecurityFinding] = []
        self.summary = TestSummary()
        self.owasp_coverage: Dict[str, Dict[str, Any]] = self._init_owasp_coverage()

    def _init_owasp_coverage(self) -> Dict[str, Dict[str, Any]]:
        return {
            "A01:2021-访问控制失效": {
                "tests": [],
                "covered": False,
                "description": "Broken Access Control"
            },
            "A02:2021-加密失效": {
                "tests": [],
                "covered": False,
                "description": "Cryptographic Failures"
            },
            "A03:2021-注入": {
                "tests": [],
                "covered": False,
                "description": "Injection"
            },
            "A04:2021-不安全设计": {
                "tests": [],
                "covered": False,
                "description": "Insecure Design"
            },
            "A05:2021-安全配置错误": {
                "tests": [],
                "covered": False,
                "description": "Security Misconfiguration"
            },
            "A06:2021-脆弱和过时的组件": {
                "tests": [],
                "covered": False,
                "description": "Vulnerable and Outdated Components"
            },
            "A07:2021-识别和身份验证失效": {
                "tests": [],
                "covered": False,
                "description": "Identification and Authentication Failures"
            },
            "A08:2021-软件和数据完整性失效": {
                "tests": [],
                "covered": False,
                "description": "Software and Data Integrity Failures"
            },
            "A09:2021-安全日志和监控失效": {
                "tests": [],
                "covered": False,
                "description": "Security Logging and Monitoring Failures"
            },
            "A10:2021-服务端请求伪造": {
                "tests": [],
                "covered": False,
                "description": "Server-Side Request Forgery"
            }
        }

    def add_finding(self, finding: SecurityFinding):
        self.findings.append(finding)
        self._update_owasp_coverage(finding)

    def _update_owasp_coverage(self, finding: SecurityFinding):
        category_mapping = {
            "A01:2021-访问控制": "A01:2021-访问控制失效",
            "A01:2021-访问控制失效": "A01:2021-访问控制失效",
            "A02:2021-加密失效": "A02:2021-加密失效",
            "A03:2021-注入": "A03:2021-注入",
            "A05:2021-安全配置错误": "A05:2021-安全配置错误",
            "A07:2021-身份验证": "A07:2021-识别和身份验证失效",
            "A07:2021-识别和身份验证失效": "A07:2021-识别和身份验证失效",
            "A10:2021-服务端请求伪造": "A10:2021-服务端请求伪造",
            "安全配置": "A05:2021-安全配置错误",
        }

        owasp_category = category_mapping.get(finding.category)
        if owasp_category and owasp_category in self.owasp_coverage:
            self.owasp_coverage[owasp_category]["tests"].append(finding.test_name)
            self.owasp_coverage[owasp_category]["covered"] = True

    def update_summary(self, total: int, passed: int, failed: int, warnings: int = 0, skipped: int = 0):
        self.summary.total_tests = total
        self.summary.passed = passed
        self.summary.failed = failed
        self.summary.warnings = warnings
        self.summary.skipped = skipped

    def finalize(self):
        self.end_time = datetime.utcnow()
        if self.start_time and self.end_time:
            self.summary.duration_seconds = (self.end_time - self.start_time).total_seconds()

    def generate_json_report(self) -> Dict[str, Any]:
        self.finalize()

        severity_counts = {
            "CRITICAL": 0,
            "HIGH": 0,
            "MEDIUM": 0,
            "LOW": 0,
            "INFO": 0
        }

        for finding in self.findings:
            severity = finding.severity.upper()
            if severity in severity_counts:
                severity_counts[severity] += 1

        return {
            "report_metadata": {
                "project_name": self.project_name,
                "generated_at": datetime.utcnow().isoformat(),
                "report_version": "1.0.0",
                "tool": "三省六部安全测试框架"
            },
            "executive_summary": {
                "overall_status": self._get_overall_status(),
                "total_tests": self.summary.total_tests,
                "passed": self.summary.passed,
                "failed": self.summary.failed,
                "warnings": self.summary.warnings,
                "severity_distribution": severity_counts,
                "duration_seconds": self.summary.duration_seconds
            },
            "owasp_top10_coverage": {
                category: {
                    "covered": data["covered"],
                    "test_count": len(data["tests"]),
                    "tests": data["tests"],
                    "description": data["description"]
                }
                for category, data in self.owasp_coverage.items()
            },
            "findings": [f.to_dict() for f in self.findings],
            "recommendations": self._generate_recommendations()
        }

    def _get_overall_status(self) -> str:
        critical_count = sum(1 for f in self.findings if f.severity == "CRITICAL")
        high_count = sum(1 for f in self.findings if f.severity == "HIGH")

        if critical_count > 0:
            return "CRITICAL"
        elif high_count > 0:
            return "HIGH_RISK"
        elif self.summary.failed > 0:
            return "NEEDS_ATTENTION"
        elif self.summary.warnings > 0:
            return "MODERATE"
        else:
            return "SECURE"

    def _generate_recommendations(self) -> List[Dict[str, str]]:
        recommendations = []

        category_recommendations = {
            "A01:2021-访问控制失效": "实施严格的访问控制检查，验证用户对每个资源的访问权限",
            "A02:2021-加密失效": "使用强加密算法保护敏感数据，实施TLS加密传输",
            "A03:2021-注入": "使用参数化查询，实施输入验证和输出编码",
            "A05:2021-安全配置错误": "审查并加固安全配置，移除不必要的功能和服务",
            "A07:2021-识别和身份验证失效": "实施多因素认证，使用强密码策略",
            "A10:2021-服务端请求伪造": "验证和清理所有用户提供的URL，实施网络分段"
        }

        for category, data in self.owasp_coverage.items():
            if data["covered"]:
                failed_tests = [f for f in self.findings if f.category in category]
                if failed_tests:
                    recommendations.append({
                        "category": category,
                        "recommendation": category_recommendations.get(category, "请进行安全审查"),
                        "priority": "HIGH" if any(f.severity in ["CRITICAL", "HIGH"] for f in failed_tests) else "MEDIUM"
                    })

        return recommendations

    def generate_markdown_report(self) -> str:
        self.finalize()
        report = self.generate_json_report()

        md_lines = [
            f"# 安全测试报告",
            f"",
            f"**项目名称**: {self.project_name}",
            f"**生成时间**: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}",
            f"**报告版本**: 1.0.0",
            f"",
            f"---",
            f"",
            f"## 执行摘要",
            f"",
            f"### 总体状态",
            f"",
        ]

        status_emoji = {
            "SECURE": "✅ 安全",
            "MODERATE": "⚠️ 中等风险",
            "NEEDS_ATTENTION": "⚠️ 需要关注",
            "HIGH_RISK": "🔴 高风险",
            "CRITICAL": "🚨 严重"
        }

        md_lines.append(f"**状态**: {status_emoji.get(report['executive_summary']['overall_status'], '未知')}")
        md_lines.append(f"")

        md_lines.extend([
            f"| 指标 | 数值 |",
            f"|------|------|",
            f"| 总测试数 | {report['executive_summary']['total_tests']} |",
            f"| 通过 | {report['executive_summary']['passed']} |",
            f"| 失败 | {report['executive_summary']['failed']} |",
            f"| 警告 | {report['executive_summary']['warnings']} |",
            f"| 执行时间 | {report['executive_summary']['duration_seconds']:.2f}秒 |",
            f"",
            f"### 严重性分布",
            f"",
            f"| 严重性 | 数量 |",
            f"|--------|------|",
        ])

        for severity, count in report['executive_summary']['severity_distribution'].items():
            md_lines.append(f"| {severity} | {count} |")

        md_lines.extend([
            f"",
            f"---",
            f"",
            f"## OWASP Top 10 覆盖情况",
            f"",
        ])

        for category, data in report['owasp_top10_coverage'].items():
            status = "✅ 已覆盖" if data['covered'] else "❌ 未覆盖"
            md_lines.extend([
                f"### {category}",
                f"",
                f"- **状态**: {status}",
                f"- **描述**: {data['description']}",
                f"- **测试数量**: {data['test_count']}",
            ])
            if data['tests']:
                md_lines.append(f"- **测试列表**: {', '.join(data['tests'][:5])}")
            md_lines.append(f"")

        if self.findings:
            md_lines.extend([
                f"---",
                f"",
                f"## 发现的安全问题",
                f"",
            ])

            severity_order = ["CRITICAL", "HIGH", "MEDIUM", "LOW", "INFO"]
            sorted_findings = sorted(self.findings, key=lambda x: severity_order.index(x.severity) if x.severity in severity_order else 5)

            for i, finding in enumerate(sorted_findings, 1):
                severity_emoji = {
                    "CRITICAL": "🚨",
                    "HIGH": "🔴",
                    "MEDIUM": "🟠",
                    "LOW": "🟡",
                    "INFO": "ℹ️"
                }
                emoji = severity_emoji.get(finding.severity, "⚪")

                md_lines.extend([
                    f"### {i}. {finding.test_name}",
                    f"",
                    f"- **严重性**: {emoji} {finding.severity}",
                    f"- **类别**: {finding.category}",
                    f"- **描述**: {finding.description}",
                ])

                if finding.payload:
                    md_lines.append(f"- **Payload**: `{finding.payload[:100]}{'...' if len(finding.payload) > 100 else ''}`")
                if finding.endpoint:
                    md_lines.append(f"- **端点**: `{finding.endpoint}`")
                if finding.response_code:
                    md_lines.append(f"- **响应码**: {finding.response_code}")
                if finding.recommendation:
                    md_lines.append(f"- **建议**: {finding.recommendation}")

                md_lines.append(f"")

        if report['recommendations']:
            md_lines.extend([
                f"---",
                f"",
                f"## 安全建议",
                f"",
            ])

            for rec in report['recommendations']:
                priority_emoji = "🔴" if rec['priority'] == "HIGH" else "🟠"
                md_lines.extend([
                    f"### {rec['category']}",
                    f"",
                    f"- **优先级**: {priority_emoji} {rec['priority']}",
                    f"- **建议**: {rec['recommendation']}",
                    f"",
                ])

        md_lines.extend([
            f"---",
            f"",
            f"## 附录",
            f"",
            f"### 测试环境",
            f"",
            f"- Python版本: {self._get_python_version()}",
            f"- 测试框架: pytest",
            f"",
            f"### 参考标准",
            f"",
            f"- OWASP Top 10 2021",
            f"- CWE (Common Weakness Enumeration)",
            f"- ASVS (Application Security Verification Standard)",
            f"",
            f"---",
            f"",
            f"*本报告由三省六部安全测试框架自动生成*",
        ])

        return "\n".join(md_lines)

    def _get_python_version(self) -> str:
        import sys
        return f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"

    def save_report(self, output_dir: str, format: str = "all"):
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")

        if format in ["json", "all"]:
            json_report = self.generate_json_report()
            json_file = output_path / f"security_report_{timestamp}.json"
            with open(json_file, 'w', encoding='utf-8') as f:
                json.dump(json_report, f, ensure_ascii=False, indent=2)
            print(f"JSON报告已保存: {json_file}")

        if format in ["markdown", "md", "all"]:
            md_report = self.generate_markdown_report()
            md_file = output_path / f"security_report_{timestamp}.md"
            with open(md_file, 'w', encoding='utf-8') as f:
                f.write(md_report)
            print(f"Markdown报告已保存: {md_file}")

    def print_summary(self):
        self.finalize()
        report = self.generate_json_report()

        print("\n" + "=" * 60)
        print("安全测试报告摘要")
        print("=" * 60)
        print(f"项目: {self.project_name}")
        print(f"状态: {report['executive_summary']['overall_status']}")
        print(f"总测试: {report['executive_summary']['total_tests']}")
        print(f"通过: {report['executive_summary']['passed']}")
        print(f"失败: {report['executive_summary']['failed']}")
        print(f"警告: {report['executive_summary']['warnings']}")
        print(f"执行时间: {report['executive_summary']['duration_seconds']:.2f}秒")
        print("=" * 60)

        severity_dist = report['executive_summary']['severity_distribution']
        print("\n严重性分布:")
        for severity, count in severity_dist.items():
            if count > 0:
                print(f"  {severity}: {count}")

        print("\nOWASP Top 10 覆盖:")
        covered_count = sum(1 for data in self.owasp_coverage.values() if data['covered'])
        print(f"  已覆盖: {covered_count}/10")

        print("=" * 60 + "\n")


def run_security_tests_and_generate_report():
    import subprocess
    import sys

    generator = SecurityReportGenerator()

    print("正在运行安全测试...")

    result = subprocess.run(
        [sys.executable, "-m", "pytest", "tests/", "-v", "-m", "security", 
         "--tb=short", "-q"],
        capture_output=True,
        text=True,
        cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    )

    output = result.stdout + result.stderr

    passed = output.count(" PASSED")
    failed = output.count(" FAILED")
    warnings = output.count(" WARNING")
    skipped = output.count(" SKIPPED")

    total = passed + failed + skipped

    generator.update_summary(total, passed, failed, warnings, skipped)

    if "SQL注入" in output:
        generator.add_finding(SecurityFinding(
            test_name="SQL注入测试",
            category="A03:2021-注入",
            severity="HIGH" if "FAILED" in output else "INFO",
            description="SQL注入防护测试已完成"
        ))

    if "XSS" in output:
        generator.add_finding(SecurityFinding(
            test_name="XSS攻击测试",
            category="A03:2021-注入",
            severity="HIGH" if "FAILED" in output else "INFO",
            description="XSS攻击防护测试已完成"
        ))

    if "CSRF" in output:
        generator.add_finding(SecurityFinding(
            test_name="CSRF防护测试",
            category="A01:2021-访问控制失效",
            severity="MEDIUM" if "FAILED" in output else "INFO",
            description="CSRF防护测试已完成"
        ))

    if "认证" in output or "身份验证" in output:
        generator.add_finding(SecurityFinding(
            test_name="认证授权测试",
            category="A07:2021-识别和身份验证失效",
            severity="HIGH" if "FAILED" in output else "INFO",
            description="认证授权测试已完成"
        ))

    if "敏感数据" in output:
        generator.add_finding(SecurityFinding(
            test_name="敏感数据暴露检测",
            category="A02:2021-加密失效",
            severity="HIGH" if "FAILED" in output else "INFO",
            description="敏感数据暴露检测已完成"
        ))

    output_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "security_reports")
    generator.save_report(output_dir)

    generator.print_summary()

    return generator


if __name__ == "__main__":
    run_security_tests_and_generate_report()
