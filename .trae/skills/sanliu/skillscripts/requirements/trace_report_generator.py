#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
追溯报告生成器
生成详细的追溯分析报告
"""

import json
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime
from enum import Enum


class ReportType(Enum):
    SUMMARY = "summary"
    DETAILED = "detailed"
    GAP_ANALYSIS = "gap_analysis"
    COMPLIANCE = "compliance"


@dataclass
class TraceGap:
    requirement_id: str
    requirement_name: str
    requirement_type: str
    gap_type: str
    description: str
    severity: str
    suggestion: str
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "requirement_id": self.requirement_id,
            "requirement_name": self.requirement_name,
            "requirement_type": self.requirement_type,
            "gap_type": self.gap_type,
            "description": self.description,
            "severity": self.severity,
            "suggestion": self.suggestion
        }


@dataclass
class TraceStatistics:
    total_requirements: int
    total_test_cases: int
    total_trace_links: int
    covered_requirements: int
    verified_requirements: int
    uncovered_requirements: int
    coverage_rate: float
    verification_rate: float
    avg_tests_per_requirement: float
    requirements_without_tests: int
    orphan_tests: int
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_requirements": self.total_requirements,
            "total_test_cases": self.total_test_cases,
            "total_trace_links": self.total_trace_links,
            "covered_requirements": self.covered_requirements,
            "verified_requirements": self.verified_requirements,
            "uncovered_requirements": self.uncovered_requirements,
            "coverage_rate": self.coverage_rate,
            "verification_rate": self.verification_rate,
            "avg_tests_per_requirement": self.avg_tests_per_requirement,
            "requirements_without_tests": self.requirements_without_tests,
            "orphan_tests": self.orphan_tests
        }


@dataclass
class TraceReport:
    report_id: str
    report_type: ReportType
    project_name: str
    generated_at: str
    statistics: TraceStatistics
    gaps: List[TraceGap]
    coverage_by_type: Dict[str, Any]
    coverage_by_priority: Dict[str, Any]
    recommendations: List[str]
    details: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "report_id": self.report_id,
            "report_type": self.report_type.value,
            "project_name": self.project_name,
            "generated_at": self.generated_at,
            "statistics": self.statistics.to_dict(),
            "gaps": [g.to_dict() for g in self.gaps],
            "coverage_by_type": self.coverage_by_type,
            "coverage_by_priority": self.coverage_by_priority,
            "recommendations": self.recommendations,
            "details": self.details
        }


class TraceReportGenerator:
    def __init__(self):
        self.report_counter = 0
    
    def _generate_report_id(self) -> str:
        self.report_counter += 1
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        return f"TR-REPORT-{timestamp}-{self.report_counter:03d}"
    
    def _calculate_statistics(self, matrix_data: Dict[str, Any]) -> TraceStatistics:
        requirements = matrix_data.get("requirements", [])
        test_cases = matrix_data.get("test_cases", [])
        trace_links = matrix_data.get("trace_links", [])
        
        total_requirements = len(requirements)
        total_test_cases = len(test_cases)
        total_trace_links = len(trace_links)
        
        covered_req_ids = set()
        verified_req_ids = set()
        
        for link in trace_links:
            if link.get("trace_type") == "requirement_to_test":
                covered_req_ids.add(link.get("source_id"))
                if link.get("status") == "verified":
                    verified_req_ids.add(link.get("source_id"))
        
        covered_requirements = len(covered_req_ids)
        verified_requirements = len(verified_req_ids)
        uncovered_requirements = total_requirements - covered_requirements
        
        coverage_rate = (covered_requirements / total_requirements * 100) if total_requirements > 0 else 0
        verification_rate = (verified_requirements / total_requirements * 100) if total_requirements > 0 else 0
        
        avg_tests = total_trace_links / covered_requirements if covered_requirements > 0 else 0
        
        linked_test_ids = {link.get("target_id") for link in trace_links}
        orphan_tests = total_test_cases - len(linked_test_ids)
        
        return TraceStatistics(
            total_requirements=total_requirements,
            total_test_cases=total_test_cases,
            total_trace_links=total_trace_links,
            covered_requirements=covered_requirements,
            verified_requirements=verified_requirements,
            uncovered_requirements=uncovered_requirements,
            coverage_rate=round(coverage_rate, 2),
            verification_rate=round(verification_rate, 2),
            avg_tests_per_requirement=round(avg_tests, 2),
            requirements_without_tests=uncovered_requirements,
            orphan_tests=orphan_tests
        )
    
    def _identify_gaps(self, matrix_data: Dict[str, Any]) -> List[TraceGap]:
        gaps = []
        requirements = matrix_data.get("requirements", [])
        trace_links = matrix_data.get("trace_links", [])
        
        covered_req_ids = set()
        for link in trace_links:
            if link.get("trace_type") == "requirement_to_test":
                covered_req_ids.add(link.get("source_id"))
        
        for req in requirements:
            req_id = req.get("id")
            if req_id not in covered_req_ids:
                gap = TraceGap(
                    requirement_id=req_id,
                    requirement_name=req.get("name", ""),
                    requirement_type=req.get("requirement_type", "unknown"),
                    gap_type="missing_test",
                    description=f"需求 '{req.get('name')}' 没有关联的测试用例",
                    severity="high" if req.get("priority") == "high" else "medium",
                    suggestion="为此需求创建验收测试用例"
                )
                gaps.append(gap)
        
        req_test_count: Dict[str, int] = {}
        for link in trace_links:
            if link.get("trace_type") == "requirement_to_test":
                req_id = link.get("source_id")
                req_test_count[req_id] = req_test_count.get(req_id, 0) + 1
        
        for req_id, count in req_test_count.items():
            if count < 2:
                req_name = next((r.get("name") for r in requirements if r.get("id") == req_id), "")
                gap = TraceGap(
                    requirement_id=req_id,
                    requirement_name=req_name,
                    requirement_type="",
                    gap_type="insufficient_coverage",
                    description=f"需求 '{req_name}' 仅有 {count} 个测试用例，建议增加测试覆盖",
                    severity="low",
                    suggestion="增加边界条件测试和异常场景测试"
                )
                gaps.append(gap)
        
        return gaps
    
    def _calculate_coverage_by_type(self, matrix_data: Dict[str, Any]) -> Dict[str, Any]:
        requirements = matrix_data.get("requirements", [])
        trace_links = matrix_data.get("trace_links", [])
        
        type_stats: Dict[str, Dict[str, int]] = {}
        
        for req in requirements:
            req_type = req.get("requirement_type", "unknown")
            if req_type not in type_stats:
                type_stats[req_type] = {"total": 0, "covered": 0}
            type_stats[req_type]["total"] += 1
        
        covered_req_ids = set()
        for link in trace_links:
            if link.get("trace_type") == "requirement_to_test":
                covered_req_ids.add(link.get("source_id"))
        
        for req in requirements:
            req_type = req.get("requirement_type", "unknown")
            if req.get("id") in covered_req_ids:
                type_stats[req_type]["covered"] += 1
        
        result = {}
        for req_type, stats in type_stats.items():
            rate = (stats["covered"] / stats["total"] * 100) if stats["total"] > 0 else 0
            result[req_type] = {
                "total": stats["total"],
                "covered": stats["covered"],
                "coverage_rate": round(rate, 2)
            }
        
        return result
    
    def _calculate_coverage_by_priority(self, matrix_data: Dict[str, Any]) -> Dict[str, Any]:
        requirements = matrix_data.get("requirements", [])
        trace_links = matrix_data.get("trace_links", [])
        
        priority_stats: Dict[str, Dict[str, int]] = {}
        
        for req in requirements:
            priority = req.get("priority", "medium")
            if priority not in priority_stats:
                priority_stats[priority] = {"total": 0, "covered": 0}
            priority_stats[priority]["total"] += 1
        
        covered_req_ids = set()
        for link in trace_links:
            if link.get("trace_type") == "requirement_to_test":
                covered_req_ids.add(link.get("source_id"))
        
        for req in requirements:
            priority = req.get("priority", "medium")
            if req.get("id") in covered_req_ids:
                priority_stats[priority]["covered"] += 1
        
        result = {}
        for priority, stats in priority_stats.items():
            rate = (stats["covered"] / stats["total"] * 100) if stats["total"] > 0 else 0
            result[priority] = {
                "total": stats["total"],
                "covered": stats["covered"],
                "coverage_rate": round(rate, 2)
            }
        
        return result
    
    def _generate_recommendations(self, statistics: TraceStatistics, gaps: List[TraceGap]) -> List[str]:
        recommendations = []
        
        if statistics.coverage_rate < 80:
            recommendations.append(f"当前覆盖率 {statistics.coverage_rate}% 低于目标值 80%，建议优先补充测试用例")
        
        if statistics.requirements_without_tests > 0:
            recommendations.append(f"有 {statistics.requirements_without_tests} 个需求缺少测试用例，建议按优先级补充")
        
        if statistics.orphan_tests > 0:
            recommendations.append(f"发现 {statistics.orphan_tests} 个孤立测试用例，建议检查是否需要关联需求")
        
        if statistics.avg_tests_per_requirement < 2:
            recommendations.append("平均每个需求测试用例数不足2个，建议增加测试场景覆盖")
        
        high_severity_gaps = [g for g in gaps if g.severity == "high"]
        if high_severity_gaps:
            recommendations.append(f"发现 {len(high_severity_gaps)} 个高优先级覆盖缺口，建议立即处理")
        
        if statistics.verification_rate < statistics.coverage_rate * 0.8:
            recommendations.append("验证率明显低于覆盖率，建议执行更多测试验证")
        
        if not recommendations:
            recommendations.append("追溯矩阵状态良好，建议持续维护")
        
        return recommendations
    
    def generate_summary_report(self, 
                                matrix_data: Dict[str, Any],
                                project_name: str = "未命名项目") -> TraceReport:
        
        statistics = self._calculate_statistics(matrix_data)
        gaps = self._identify_gaps(matrix_data)
        coverage_by_type = self._calculate_coverage_by_type(matrix_data)
        coverage_by_priority = self._calculate_coverage_by_priority(matrix_data)
        recommendations = self._generate_recommendations(statistics, gaps)
        
        return TraceReport(
            report_id=self._generate_report_id(),
            report_type=ReportType.SUMMARY,
            project_name=project_name,
            generated_at=datetime.now().isoformat(),
            statistics=statistics,
            gaps=gaps,
            coverage_by_type=coverage_by_type,
            coverage_by_priority=coverage_by_priority,
            recommendations=recommendations
        )
    
    def generate_detailed_report(self,
                                  matrix_data: Dict[str, Any],
                                  project_name: str = "未命名项目") -> TraceReport:
        
        report = self.generate_summary_report(matrix_data, project_name)
        report.report_type = ReportType.DETAILED
        
        requirements = matrix_data.get("requirements", [])
        test_cases = matrix_data.get("test_cases", [])
        trace_links = matrix_data.get("trace_links", [])
        
        req_details = {}
        for req in requirements:
            req_id = req.get("id")
            linked_tests = [
                {
                    "id": link.get("target_id"),
                    "status": link.get("status"),
                    "confidence": link.get("confidence", 1.0)
                }
                for link in trace_links
                if link.get("source_id") == req_id and link.get("trace_type") == "requirement_to_test"
            ]
            req_details[req_id] = {
                "name": req.get("name"),
                "type": req.get("requirement_type"),
                "priority": req.get("priority"),
                "status": req.get("status"),
                "linked_tests": linked_tests,
                "test_count": len(linked_tests)
            }
        
        test_details = {}
        for test in test_cases:
            test_id = test.get("id")
            linked_reqs = [
                {
                    "id": link.get("source_id"),
                    "name": link.get("source_name")
                }
                for link in trace_links
                if link.get("target_id") == test_id
            ]
            test_details[test_id] = {
                "name": test.get("name"),
                "type": test.get("test_type"),
                "status": test.get("status"),
                "execution_result": test.get("execution_result"),
                "linked_requirements": linked_reqs
            }
        
        report.details = {
            "requirements": req_details,
            "test_cases": test_details
        }
        
        return report
    
    def generate_gap_analysis_report(self,
                                      matrix_data: Dict[str, Any],
                                      project_name: str = "未命名项目") -> TraceReport:
        
        report = self.generate_summary_report(matrix_data, project_name)
        report.report_type = ReportType.GAP_ANALYSIS
        
        gaps = report.gaps
        
        gap_summary = {
            "total_gaps": len(gaps),
            "by_severity": {},
            "by_type": {},
            "by_requirement_type": {}
        }
        
        for gap in gaps:
            gap_summary["by_severity"][gap.severity] = gap_summary["by_severity"].get(gap.severity, 0) + 1
            gap_summary["by_type"][gap.gap_type] = gap_summary["by_type"].get(gap.gap_type, 0) + 1
            gap_summary["by_requirement_type"][gap.requirement_type] = gap_summary["by_requirement_type"].get(gap.requirement_type, 0) + 1
        
        report.details = {
            "gap_summary": gap_summary,
            "priority_gaps": sorted(gaps, key=lambda g: {"high": 0, "medium": 1, "low": 2}.get(g.severity, 3))
        }
        
        return report
    
    def to_markdown(self, report: TraceReport) -> str:
        lines = [
            f"# 需求追溯报告",
            "",
            f"**报告ID**: {report.report_id}",
            f"**项目名称**: {report.project_name}",
            f"**报告类型**: {report.report_type.value}",
            f"**生成时间**: {report.generated_at}",
            "",
            "---",
            ""
        ]
        
        stats = report.statistics
        lines.extend([
            "## 统计概览",
            "",
            "| 指标 | 数值 |",
            "|------|------|",
            f"| 需求总数 | {stats.total_requirements} |",
            f"| 测试用例总数 | {stats.total_test_cases} |",
            f"| 追溯链接数 | {stats.total_trace_links} |",
            f"| 已覆盖需求 | {stats.covered_requirements} |",
            f"| 已验证需求 | {stats.verified_requirements} |",
            f"| 未覆盖需求 | {stats.uncovered_requirements} |",
            f"| 覆盖率 | {stats.coverage_rate}% |",
            f"| 验证率 | {stats.verification_rate}% |",
            f"| 平均测试数/需求 | {stats.avg_tests_per_requirement} |",
            ""
        ])
        
        lines.extend([
            "## 按类型覆盖",
            "",
            "| 类型 | 总数 | 已覆盖 | 覆盖率 |",
            "|------|------|--------|--------|"
        ])
        for req_type, data in report.coverage_by_type.items():
            lines.append(f"| {req_type} | {data['total']} | {data['covered']} | {data['coverage_rate']}% |")
        lines.append("")
        
        lines.extend([
            "## 按优先级覆盖",
            "",
            "| 优先级 | 总数 | 已覆盖 | 覆盖率 |",
            "|--------|------|--------|--------|"
        ])
        for priority, data in report.coverage_by_priority.items():
            lines.append(f"| {priority} | {data['total']} | {data['covered']} | {data['coverage_rate']}% |")
        lines.append("")
        
        if report.gaps:
            lines.extend([
                "## 覆盖缺口分析",
                "",
                f"共发现 {len(report.gaps)} 个覆盖缺口：",
                ""
            ])
            
            for gap in report.gaps:
                severity_icon = {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(gap.severity, "⚪")
                lines.extend([
                    f"### {severity_icon} {gap.requirement_name}",
                    "",
                    f"- **需求ID**: {gap.requirement_id}",
                    f"- **缺口类型**: {gap.gap_type}",
                    f"- **严重程度**: {gap.severity}",
                    f"- **描述**: {gap.description}",
                    f"- **建议**: {gap.suggestion}",
                    ""
                ])
        
        lines.extend([
            "## 改进建议",
            ""
        ])
        for i, rec in enumerate(report.recommendations, 1):
            lines.append(f"{i}. {rec}")
        lines.append("")
        
        if report.details and report.report_type == ReportType.DETAILED:
            lines.extend([
                "## 详细追溯信息",
                "",
                "### 需求追溯详情",
                ""
            ])
            for req_id, req_data in report.details.get("requirements", {}).items():
                lines.append(f"- **{req_id}**: {req_data['name']}")
                lines.append(f"  - 类型: {req_data['type']}, 优先级: {req_data['priority']}")
                lines.append(f"  - 关联测试: {req_data['test_count']} 个")
                lines.append("")
        
        lines.extend([
            "---",
            "",
            "*报告由需求追溯系统自动生成*"
        ])
        
        return '\n'.join(lines)
    
    def to_json(self, report: TraceReport) -> str:
        return json.dumps(report.to_dict(), ensure_ascii=False, indent=2)
    
    def save_report(self, report: TraceReport, output_path: str, format: str = "markdown") -> str:
        if format == "markdown":
            content = self.to_markdown(report)
            file_path = f"{output_path}.md"
        elif format == "json":
            content = self.to_json(report)
            file_path = f"{output_path}.json"
        else:
            raise ValueError(f"不支持的格式: {format}")
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        return file_path


def main():
    generator = TraceReportGenerator()
    
    test_matrix_data = {
        "requirements": [
            {"id": "REQ-001", "name": "用户登录功能", "requirement_type": "functional", "priority": "high", "status": "active"},
            {"id": "REQ-002", "name": "密码重置功能", "requirement_type": "functional", "priority": "high", "status": "active"},
            {"id": "REQ-003", "name": "用户注册功能", "requirement_type": "functional", "priority": "medium", "status": "active"},
            {"id": "REQ-004", "name": "性能要求", "requirement_type": "non_functional", "priority": "medium", "status": "active"},
            {"id": "REQ-005", "name": "安全要求", "requirement_type": "non_functional", "priority": "high", "status": "active"}
        ],
        "test_cases": [
            {"id": "TC-001", "name": "登录成功测试", "test_type": "acceptance", "status": "passed", "execution_result": "passed"},
            {"id": "TC-002", "name": "登录失败测试", "test_type": "acceptance", "status": "passed", "execution_result": "passed"},
            {"id": "TC-003", "name": "密码重置测试", "test_type": "acceptance", "status": "pending", "execution_result": None},
            {"id": "TC-004", "name": "性能测试", "test_type": "performance", "status": "passed", "execution_result": "passed"}
        ],
        "trace_links": [
            {"source_id": "REQ-001", "target_id": "TC-001", "trace_type": "requirement_to_test", "status": "verified", "source_name": "用户登录功能", "target_name": "登录成功测试"},
            {"source_id": "REQ-001", "target_id": "TC-002", "trace_type": "requirement_to_test", "status": "verified", "source_name": "用户登录功能", "target_name": "登录失败测试"},
            {"source_id": "REQ-002", "target_id": "TC-003", "trace_type": "requirement_to_test", "status": "pending", "source_name": "密码重置功能", "target_name": "密码重置测试"},
            {"source_id": "REQ-004", "target_id": "TC-004", "trace_type": "requirement_to_test", "status": "verified", "source_name": "性能要求", "target_name": "性能测试"}
        ]
    }
    
    print("="*60)
    print("追溯报告生成器测试")
    print("="*60)
    
    print("\n--- 摘要报告 ---")
    summary_report = generator.generate_summary_report(test_matrix_data, "用户管理系统")
    print(generator.to_markdown(summary_report))
    
    print("\n" + "="*60)
    print("--- 缺口分析报告 ---")
    gap_report = generator.generate_gap_analysis_report(test_matrix_data, "用户管理系统")
    print(f"发现缺口: {len(gap_report.gaps)}")
    for gap in gap_report.gaps[:3]:
        print(f"  - {gap.requirement_name}: {gap.description}")


if __name__ == "__main__":
    main()
