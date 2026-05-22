#!/usr/bin/env python3
"""
问题优先级评估器
根据问题类型、影响范围、修复难度评估优先级
生成问题清单
"""

import json
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import List, Dict, Any, Optional


class Priority(Enum):
    P0_CRITICAL = "P0"
    P1_HIGH = "P1"
    P2_MEDIUM = "P2"
    P3_LOW = "P3"
    P4_INFO = "P4"


class IssueSource(Enum):
    CODE_SCANNER = "code_scanner"
    COVERAGE_ANALYZER = "coverage_analyzer"
    PERFORMANCE_DETECTOR = "performance_detector"
    MANUAL = "manual"


@dataclass
class Issue:
    id: str
    title: str
    description: str
    source: IssueSource
    category: str
    severity: str
    file_path: str
    line_number: int
    impact_score: float
    effort_score: float
    priority: Priority
    tags: List[str] = field(default_factory=list)
    suggestion: str = ""
    created_at: str = ""
    status: str = "open"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "source": self.source.value,
            "category": self.category,
            "severity": self.severity,
            "file_path": self.file_path,
            "line_number": self.line_number,
            "impact_score": round(self.impact_score, 2),
            "effort_score": round(self.effort_score, 2),
            "priority": self.priority.value,
            "tags": self.tags,
            "suggestion": self.suggestion,
            "created_at": self.created_at,
            "status": self.status
        }


@dataclass
class IssueList:
    name: str
    issues: List[Issue]
    total_count: int
    by_priority: Dict[str, int]
    by_category: Dict[str, int]
    by_source: Dict[str, int]
    generated_at: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "issues": [i.to_dict() for i in self.issues],
            "total_count": self.total_count,
            "by_priority": self.by_priority,
            "by_category": self.by_category,
            "by_source": self.by_source,
            "generated_at": self.generated_at
        }


class PriorityEvaluator:
    SEVERITY_WEIGHTS = {
        "critical": 10.0,
        "high": 7.0,
        "medium": 4.0,
        "low": 2.0,
        "info": 1.0
    }

    CATEGORY_WEIGHTS = {
        "security": 3.0,
        "performance": 2.5,
        "complexity": 2.0,
        "code_smell": 1.5,
        "style": 1.0,
        "coverage": 2.0
    }

    EFFORT_ESTIMATES = {
        "security_hardcoded_password": 2.0,
        "security_sql_injection_risk": 5.0,
        "security_eval_usage": 8.0,
        "complexity_long_function": 4.0,
        "complexity_deep_nesting": 3.0,
        "complexity_too_many_params": 2.0,
        "complexity_large_class": 6.0,
        "smell_console_log": 1.0,
        "smell_any_type": 2.0,
        "smell_bare_except": 2.0,
        "smell_todo_comment": 1.0,
        "coverage_gap": 3.0,
        "performance_slow_api": 5.0,
        "performance_large_bundle": 4.0,
        "performance_slow_load": 6.0
    }

    PRIORITY_THRESHOLDS = {
        Priority.P0_CRITICAL: 15.0,
        Priority.P1_HIGH: 10.0,
        Priority.P2_MEDIUM: 5.0,
        Priority.P3_LOW: 2.0,
        Priority.P4_INFO: 0.0
    }

    def __init__(self):
        self.issues: List[Issue] = []
        self.issue_counter = 0

    def _generate_issue_id(self) -> str:
        self.issue_counter += 1
        return f"ISSUE-{self.issue_counter:04d}"

    def calculate_impact_score(
        self,
        severity: str,
        category: str,
        file_importance: float = 1.0,
        user_impact: float = 1.0
    ) -> float:
        severity_weight = self.SEVERITY_WEIGHTS.get(severity.lower(), 1.0)
        category_weight = self.CATEGORY_WEIGHTS.get(category.lower(), 1.0)

        return severity_weight * category_weight * file_importance * user_impact

    def estimate_effort(self, problem_type: str, complexity: float = 1.0) -> float:
        base_effort = self.EFFORT_ESTIMATES.get(problem_type, 3.0)
        return base_effort * complexity

    def determine_priority(self, impact_score: float, effort_score: float) -> Priority:
        roi = impact_score / max(effort_score, 0.1)

        adjusted_score = impact_score * (1 + roi / 10)

        if adjusted_score >= self.PRIORITY_THRESHOLDS[Priority.P0_CRITICAL]:
            return Priority.P0_CRITICAL
        elif adjusted_score >= self.PRIORITY_THRESHOLDS[Priority.P1_HIGH]:
            return Priority.P1_HIGH
        elif adjusted_score >= self.PRIORITY_THRESHOLDS[Priority.P2_MEDIUM]:
            return Priority.P2_MEDIUM
        elif adjusted_score >= self.PRIORITY_THRESHOLDS[Priority.P3_LOW]:
            return Priority.P3_LOW
        else:
            return Priority.P4_INFO

    def add_code_problem(self, problem: Dict[str, Any]) -> Issue:
        problem_type = problem.get("problem_type", "unknown")
        severity = problem.get("severity", "medium")
        category = problem.get("category", "code_smell")

        impact_score = self.calculate_impact_score(severity, category)
        effort_score = self.estimate_effort(problem_type)
        priority = self.determine_priority(impact_score, effort_score)

        issue = Issue(
            id=self._generate_issue_id(),
            title=f"{problem_type}: {problem.get('message', '')[:50]}",
            description=problem.get("message", ""),
            source=IssueSource.CODE_SCANNER,
            category=category,
            severity=severity,
            file_path=problem.get("file_path", ""),
            line_number=problem.get("line_number", 0),
            impact_score=impact_score,
            effort_score=effort_score,
            priority=priority,
            tags=problem.get("tags", []),
            suggestion=problem.get("suggestion", ""),
            created_at=datetime.now().isoformat()
        )

        self.issues.append(issue)
        return issue

    def add_coverage_gap(self, gap: Dict[str, Any]) -> Issue:
        gap_type = gap.get("gap_type", "missing_line")
        current_coverage = gap.get("current_coverage", 0)
        target_coverage = gap.get("target_coverage", 80)

        coverage_gap = target_coverage - current_coverage
        impact_score = self.calculate_impact_score(
            "medium" if coverage_gap > 30 else "low",
            "coverage",
            file_importance=gap.get("impact_score", 1.0) / 10
        )
        effort_score = self.estimate_effort("coverage_gap", complexity=coverage_gap / 20)
        priority = self.determine_priority(impact_score, effort_score)

        issue = Issue(
            id=self._generate_issue_id(),
            title=f"覆盖率缺口: {gap.get('file_path', '').split('/')[-1]}",
            description=gap.get("description", ""),
            source=IssueSource.COVERAGE_ANALYZER,
            category="coverage",
            severity="medium",
            file_path=gap.get("file_path", ""),
            line_number=gap.get("line_start", 0),
            impact_score=impact_score,
            effort_score=effort_score,
            priority=priority,
            tags=["coverage", gap_type],
            suggestion=gap.get("suggestion", "添加测试用例"),
            created_at=datetime.now().isoformat()
        )

        self.issues.append(issue)
        return issue

    def add_performance_issue(self, perf_issue: Dict[str, Any]) -> Issue:
        issue_type = perf_issue.get("issue_type", "unknown")
        severity = perf_issue.get("severity", "medium")
        metric_value = perf_issue.get("metric_value", 0)
        threshold = perf_issue.get("threshold", 1)

        deviation = abs(metric_value - threshold) / max(threshold, 1)
        impact_score = self.calculate_impact_score(
            severity,
            "performance",
            user_impact=1 + deviation
        )
        effort_score = self.estimate_effort(f"performance_{issue_type}")
        priority = self.determine_priority(impact_score, effort_score)

        issue = Issue(
            id=self._generate_issue_id(),
            title=f"性能问题: {issue_type}",
            description=perf_issue.get("description", ""),
            source=IssueSource.PERFORMANCE_DETECTOR,
            category="performance",
            severity=severity,
            file_path=perf_issue.get("location", ""),
            line_number=0,
            impact_score=impact_score,
            effort_score=effort_score,
            priority=priority,
            tags=["performance", issue_type],
            suggestion=perf_issue.get("suggestion", ""),
            created_at=datetime.now().isoformat()
        )

        self.issues.append(issue)
        return issue

    def load_code_problems(self, report_path: Path) -> int:
        if not report_path.exists():
            return 0

        with open(report_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        problems = data.get("problems", [])
        for problem in problems:
            self.add_code_problem(problem)

        return len(problems)

    def load_coverage_gaps(self, report_path: Path) -> int:
        if not report_path.exists():
            return 0

        with open(report_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        count = 0
        for project_name, project_data in data.items():
            if isinstance(project_data, dict) and "gaps" in project_data:
                for gap in project_data["gaps"]:
                    self.add_coverage_gap(gap)
                    count += 1

        return count

    def load_performance_issues(self, report_path: Path) -> int:
        if not report_path.exists():
            return 0

        with open(report_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        issues = data.get("issues", [])
        for issue in issues:
            self.add_performance_issue(issue)

        return len(issues)

    def sort_by_priority(self) -> List[Issue]:
        priority_order = {
            Priority.P0_CRITICAL: 0,
            Priority.P1_HIGH: 1,
            Priority.P2_MEDIUM: 2,
            Priority.P3_LOW: 3,
            Priority.P4_INFO: 4
        }

        return sorted(
            self.issues,
            key=lambda i: (priority_order.get(i.priority, 5), -i.impact_score)
        )

    def sort_by_roi(self) -> List[Issue]:
        return sorted(
            self.issues,
            key=lambda i: i.impact_score / max(i.effort_score, 0.1),
            reverse=True
        )

    def generate_issue_list(self, name: str = "问题清单") -> IssueList:
        sorted_issues = self.sort_by_priority()

        by_priority: Dict[str, int] = {}
        by_category: Dict[str, int] = {}
        by_source: Dict[str, int] = {}

        for issue in self.issues:
            by_priority[issue.priority.value] = by_priority.get(issue.priority.value, 0) + 1
            by_category[issue.category] = by_category.get(issue.category, 0) + 1
            by_source[issue.source.value] = by_source.get(issue.source.value, 0) + 1

        return IssueList(
            name=name,
            issues=sorted_issues,
            total_count=len(self.issues),
            by_priority=by_priority,
            by_category=by_category,
            by_source=by_source,
            generated_at=datetime.now().isoformat()
        )

    def generate_report(self) -> str:
        report = []
        report.append("=" * 80)
        report.append("问题优先级评估报告")
        report.append(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("=" * 80)

        issue_list = self.generate_issue_list()

        report.append(f"\n## 统计概览")
        report.append("-" * 40)
        report.append(f"问题总数: {issue_list.total_count}")

        report.append(f"\n按优先级分布:")
        for priority in ["P0", "P1", "P2", "P3", "P4"]:
            count = issue_list.by_priority.get(priority, 0)
            if count > 0:
                report.append(f"  {priority}: {count}")

        report.append(f"\n按类别分布:")
        for category, count in sorted(issue_list.by_category.items(), key=lambda x: -x[1]):
            report.append(f"  {category}: {count}")

        report.append(f"\n按来源分布:")
        for source, count in sorted(issue_list.by_source.items(), key=lambda x: -x[1]):
            report.append(f"  {source}: {count}")

        report.append(f"\n## 问题清单")
        report.append("-" * 40)

        current_priority = None
        for issue in issue_list.issues:
            if issue.priority != current_priority:
                current_priority = issue.priority
                report.append(f"\n### {current_priority.value} - {self._get_priority_label(current_priority)}")

            report.append(f"\n[{issue.id}] {issue.title}")
            report.append(f"  文件: {issue.file_path}:{issue.line_number}")
            report.append(f"  类别: {issue.category} | 严重程度: {issue.severity}")
            report.append(f"  影响分数: {issue.impact_score:.1f} | 工作量: {issue.effort_score:.1f}")
            report.append(f"  建议: {issue.suggestion}")

        report.append("\n" + "=" * 80)
        report.append("修复建议")
        report.append("=" * 80)

        p0_issues = [i for i in self.issues if i.priority == Priority.P0_CRITICAL]
        p1_issues = [i for i in self.issues if i.priority == Priority.P1_HIGH]

        if p0_issues:
            report.append(f"\n紧急处理 (P0): {len(p0_issues)}个")
            report.append("这些问题需要立即处理，可能影响系统安全或核心功能")
            for issue in p0_issues[:5]:
                report.append(f"  - {issue.id}: {issue.title}")

        if p1_issues:
            report.append(f"\n高优先级 (P1): {len(p1_issues)}个")
            report.append("这些问题应在本迭代内处理")
            for issue in p1_issues[:5]:
                report.append(f"  - {issue.id}: {issue.title}")

        roi_sorted = self.sort_by_roi()[:10]
        if roi_sorted:
            report.append(f"\n高ROI问题 (建议优先修复):")
            for issue in roi_sorted:
                roi = issue.impact_score / max(issue.effort_score, 0.1)
                report.append(f"  - {issue.id}: ROI={roi:.1f} ({issue.title})")

        return "\n".join(report)

    def _get_priority_label(self, priority: Priority) -> str:
        labels = {
            Priority.P0_CRITICAL: "紧急 - 立即处理",
            Priority.P1_HIGH: "高 - 本迭代处理",
            Priority.P2_MEDIUM: "中 - 近期处理",
            Priority.P3_LOW: "低 - 有空处理",
            Priority.P4_INFO: "信息 - 可选处理"
        }
        return labels.get(priority, "未知")

    def save_issue_list(self, output_path: Path) -> None:
        output_path.parent.mkdir(parents=True, exist_ok=True)

        issue_list = self.generate_issue_list()

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(issue_list.to_dict(), f, indent=2, ensure_ascii=False)

    def get_issues_by_priority(self, priority: Priority) -> List[Issue]:
        return [i for i in self.issues if i.priority == priority]

    def get_issues_by_category(self, category: str) -> List[Issue]:
        return [i for i in self.issues if i.category == category]

    def get_critical_issues(self) -> List[Issue]:
        return self.get_issues_by_priority(Priority.P0_CRITICAL)

    def export_to_markdown(self, output_path: Path) -> None:
        output_path.parent.mkdir(parents=True, exist_ok=True)

        report = self.generate_report()
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(report)


def main():
    base_dir = Path(__file__).parent.parent
    reports_dir = base_dir / "reports"

    print("=" * 80)
    print("问题优先级评估器")
    print("=" * 80)

    evaluator = PriorityEvaluator()

    print("\n加载代码问题...")
    code_report = reports_dir / "code_problem_report.json"
    code_count = evaluator.load_code_problems(code_report)
    print(f"加载了 {code_count} 个代码问题")

    print("\n加载覆盖率缺口...")
    backend_coverage = reports_dir / "backend_coverage_report.json"
    frontend_coverage = reports_dir / "frontend_coverage_report.json"

    coverage_count = 0
    coverage_count += evaluator.load_coverage_gaps(backend_coverage)
    coverage_count += evaluator.load_coverage_gaps(frontend_coverage)
    print(f"加载了 {coverage_count} 个覆盖率缺口")

    print("\n加载性能问题...")
    perf_report = reports_dir / "performance_detection_report.json"
    perf_count = evaluator.load_performance_issues(perf_report)
    print(f"加载了 {perf_count} 个性能问题")

    print("\n生成优先级报告...")
    report = evaluator.generate_report()
    print(report)

    print("\n保存问题清单...")
    issue_list_path = reports_dir / "issue_list.json"
    evaluator.save_issue_list(issue_list_path)
    print(f"问题清单已保存: {issue_list_path}")

    md_path = reports_dir / "issue_priority_report.md"
    evaluator.export_to_markdown(md_path)
    print(f"Markdown报告已保存: {md_path}")

    critical = evaluator.get_critical_issues()
    if critical:
        print(f"\n紧急问题: {len(critical)}")
        for issue in critical:
            print(f"  - {issue.id}: {issue.title}")

    return 0 if not critical else 1


if __name__ == "__main__":
    import sys
    sys.exit(main())
