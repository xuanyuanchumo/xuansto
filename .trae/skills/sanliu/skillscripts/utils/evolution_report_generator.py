#!/usr/bin/env python3
"""
演化报告生成器
生成三省六部技能的演化报告，支持周期性报告、历史报告、对比报告等多种类型

功能:
1. 周期性报告生成 - 每日/每周/每月演化报告
2. 历史报告生成 - 演化历史汇总
3. 对比报告生成 - 演化前后对比分析
4. 多格式输出支持 - JSON、Markdown、HTML

使用示例:
    generator = EvolutionReportGenerator()
    generator.generate_daily_report()
    generator.generate_weekly_report()
    generator.generate_comparison_report(before_data, after_data)
    generator.save_report(report, format="html")
"""

import json
import os
import sys
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any, Optional
from enum import Enum
from collections import defaultdict

from skillscripts.core.path_config_center import get_path_config


class ReportType(Enum):
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    EVOLUTION_CYCLE = "evolution_cycle"
    COMPARISON = "comparison"
    DIAGNOSTIC = "diagnostic"


class IssueSeverity(Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class EvolutionStatus(Enum):
    SUCCESS = "success"
    FAILED = "failed"
    PARTIAL = "partial"
    ROLLED_BACK = "rolled_back"
    PENDING = "pending"


@dataclass
class EvolutionRecord:
    evolution_id: str
    timestamp: str
    evolution_type: str
    status: EvolutionStatus
    duration_ms: float
    issues_found: int
    issues_fixed: int
    issues_remaining: int
    coverage_before: float
    coverage_after: float
    quality_score_before: float
    quality_score_after: float
    patterns_learned: List[str] = field(default_factory=list)
    knowledge_updates: List[str] = field(default_factory=list)
    side_effects: List[str] = field(default_factory=list)
    details: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "evolution_id": self.evolution_id,
            "timestamp": self.timestamp,
            "evolution_type": self.evolution_type,
            "status": self.status.value,
            "duration_ms": self.duration_ms,
            "issues_found": self.issues_found,
            "issues_fixed": self.issues_fixed,
            "issues_remaining": self.issues_remaining,
            "coverage_before": self.coverage_before,
            "coverage_after": self.coverage_after,
            "quality_score_before": self.quality_score_before,
            "quality_score_after": self.quality_score_after,
            "patterns_learned": self.patterns_learned,
            "knowledge_updates": self.knowledge_updates,
            "side_effects": self.side_effects,
            "details": self.details
        }


@dataclass
class IssueDistribution:
    issue_type: str
    count: int
    percentage: float
    severity_distribution: Dict[str, int] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "issue_type": self.issue_type,
            "count": self.count,
            "percentage": self.percentage,
            "severity_distribution": self.severity_distribution
        }


@dataclass
class EvolutionStatistics:
    total_evolutions: int
    successful_evolutions: int
    failed_evolutions: int
    partial_evolutions: int
    rolled_back_evolutions: int
    success_rate: float
    average_duration_ms: float
    total_issues_found: int
    total_issues_fixed: int
    fix_rate: float
    average_coverage_improvement: float
    average_quality_improvement: float

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_evolutions": self.total_evolutions,
            "successful_evolutions": self.successful_evolutions,
            "failed_evolutions": self.failed_evolutions,
            "partial_evolutions": self.partial_evolutions,
            "rolled_back_evolutions": self.rolled_back_evolutions,
            "success_rate": self.success_rate,
            "average_duration_ms": self.average_duration_ms,
            "total_issues_found": self.total_issues_found,
            "total_issues_fixed": self.total_issues_fixed,
            "fix_rate": self.fix_rate,
            "average_coverage_improvement": self.average_coverage_improvement,
            "average_quality_improvement": self.average_quality_improvement
        }


@dataclass
class ProblemAnalysis:
    issue_distributions: List[IssueDistribution]
    severity_summary: Dict[str, int]
    top_issues: List[Dict[str, Any]]
    problem_trends: List[Dict[str, Any]]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "issue_distributions": [d.to_dict() for d in self.issue_distributions],
            "severity_summary": self.severity_summary,
            "top_issues": self.top_issues,
            "problem_trends": self.problem_trends
        }


@dataclass
class FixEffect:
    total_fixes: int
    successful_fixes: int
    failed_fixes: int
    fix_success_rate: float
    side_effects_count: int
    side_effects_types: Dict[str, int]
    rollback_count: int
    fix_time_distribution: Dict[str, int]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_fixes": self.total_fixes,
            "successful_fixes": self.successful_fixes,
            "failed_fixes": self.failed_fixes,
            "fix_success_rate": self.fix_success_rate,
            "side_effects_count": self.side_effects_count,
            "side_effects_types": self.side_effects_types,
            "rollback_count": self.rollback_count,
            "fix_time_distribution": self.fix_time_distribution
        }


@dataclass
class LearningOutcome:
    new_patterns_learned: int
    pattern_list: List[Dict[str, Any]]
    knowledge_base_updates: int
    update_list: List[Dict[str, Any]]
    rule_refinements: int
    refinement_list: List[Dict[str, Any]]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "new_patterns_learned": self.new_patterns_learned,
            "pattern_list": self.pattern_list,
            "knowledge_base_updates": self.knowledge_base_updates,
            "update_list": self.update_list,
            "rule_refinements": self.rule_refinements,
            "refinement_list": self.refinement_list
        }


@dataclass
class TrendAnalysis:
    metric_name: str
    values: List[float]
    timestamps: List[str]
    trend_direction: str
    improvement_rate: float
    prediction: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "metric_name": self.metric_name,
            "values": self.values,
            "timestamps": self.timestamps,
            "trend_direction": self.trend_direction,
            "improvement_rate": self.improvement_rate,
            "prediction": self.prediction
        }


@dataclass
class EvolutionReport:
    report_id: str
    report_type: ReportType
    timestamp: str
    period_start: str
    period_end: str
    statistics: EvolutionStatistics
    problem_analysis: ProblemAnalysis
    fix_effect: FixEffect
    learning_outcome: LearningOutcome
    trend_analyses: List[TrendAnalysis]
    recommendations: List[str]
    summary: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "report_id": self.report_id,
            "report_type": self.report_type.value,
            "timestamp": self.timestamp,
            "period_start": self.period_start,
            "period_end": self.period_end,
            "statistics": self.statistics.to_dict(),
            "problem_analysis": self.problem_analysis.to_dict(),
            "fix_effect": self.fix_effect.to_dict(),
            "learning_outcome": self.learning_outcome.to_dict(),
            "trend_analyses": [t.to_dict() for t in self.trend_analyses],
            "recommendations": self.recommendations,
            "summary": self.summary
        }


@dataclass
class ComparisonReport:
    report_id: str
    timestamp: str
    before_snapshot: Dict[str, Any]
    after_snapshot: Dict[str, Any]
    changes: Dict[str, Any]
    improvements: List[Dict[str, Any]]
    regressions: List[Dict[str, Any]]
    overall_assessment: str
    recommendations: List[str]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "report_id": self.report_id,
            "timestamp": self.timestamp,
            "before_snapshot": self.before_snapshot,
            "after_snapshot": self.after_snapshot,
            "changes": self.changes,
            "improvements": self.improvements,
            "regressions": self.regressions,
            "overall_assessment": self.overall_assessment,
            "recommendations": self.recommendations
        }


class EvolutionReportGenerator:
    def __init__(self, project_root: Optional[Path] = None):
        self.project_root = project_root or get_path_config().SKILL_ROOT
        self.sanliu_root = self.project_root
        self.reports_dir = self.sanliu_root / "evolution_reports"
        self.history_dir = self.sanliu_root / "evolution_history"
        self.reports_dir.mkdir(parents=True, exist_ok=True)
        self.history_dir.mkdir(parents=True, exist_ok=True)
        self.history_file = self.history_dir / "evolution_history.json"
        self.records: List[EvolutionRecord] = []
        self._load_history()

    def _load_history(self):
        if self.history_file.exists():
            try:
                with open(self.history_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    for record_data in data.get("records", []):
                        record_data["status"] = EvolutionStatus(record_data.get("status", "pending"))
                        self.records.append(EvolutionRecord(**record_data))
            except Exception:
                self.records = []

    def _save_history(self):
        data = {
            "records": [r.to_dict() for r in self.records],
            "last_updated": datetime.now().isoformat(),
            "total_evolutions": len(self.records)
        }
        with open(self.history_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def record_evolution(
        self,
        evolution_type: str,
        status: EvolutionStatus,
        duration_ms: float,
        issues_found: int,
        issues_fixed: int,
        issues_remaining: int,
        coverage_before: float,
        coverage_after: float,
        quality_score_before: float,
        quality_score_after: float,
        patterns_learned: Optional[List[str]] = None,
        knowledge_updates: Optional[List[str]] = None,
        side_effects: Optional[List[str]] = None,
        details: str = ""
    ) -> EvolutionRecord:
        evolution_id = f"EVO-{datetime.now().strftime('%Y%m%d%H%M%S')}-{len(self.records):04d}"
        
        record = EvolutionRecord(
            evolution_id=evolution_id,
            timestamp=datetime.now().isoformat(),
            evolution_type=evolution_type,
            status=status,
            duration_ms=duration_ms,
            issues_found=issues_found,
            issues_fixed=issues_fixed,
            issues_remaining=issues_remaining,
            coverage_before=coverage_before,
            coverage_after=coverage_after,
            quality_score_before=quality_score_before,
            quality_score_after=quality_score_after,
            patterns_learned=patterns_learned or [],
            knowledge_updates=knowledge_updates or [],
            side_effects=side_effects or [],
            details=details
        )
        
        self.records.append(record)
        self._save_history()
        
        return record

    def _get_records_in_period(self, start_date: datetime, end_date: datetime) -> List[EvolutionRecord]:
        result = []
        for record in self.records:
            try:
                record_time = datetime.fromisoformat(record.timestamp)
                if start_date <= record_time <= end_date:
                    result.append(record)
            except Exception:
                continue
        return result

    def _calculate_statistics(self, records: List[EvolutionRecord]) -> EvolutionStatistics:
        if not records:
            return EvolutionStatistics(
                total_evolutions=0,
                successful_evolutions=0,
                failed_evolutions=0,
                partial_evolutions=0,
                rolled_back_evolutions=0,
                success_rate=0.0,
                average_duration_ms=0.0,
                total_issues_found=0,
                total_issues_fixed=0,
                fix_rate=0.0,
                average_coverage_improvement=0.0,
                average_quality_improvement=0.0
            )

        successful = sum(1 for r in records if r.status == EvolutionStatus.SUCCESS)
        failed = sum(1 for r in records if r.status == EvolutionStatus.FAILED)
        partial = sum(1 for r in records if r.status == EvolutionStatus.PARTIAL)
        rolled_back = sum(1 for r in records if r.status == EvolutionStatus.ROLLED_BACK)

        total_duration = sum(r.duration_ms for r in records)
        total_issues_found = sum(r.issues_found for r in records)
        total_issues_fixed = sum(r.issues_fixed for r in records)

        coverage_improvements = [r.coverage_after - r.coverage_before for r in records]
        quality_improvements = [r.quality_score_after - r.quality_score_before for r in records]

        return EvolutionStatistics(
            total_evolutions=len(records),
            successful_evolutions=successful,
            failed_evolutions=failed,
            partial_evolutions=partial,
            rolled_back_evolutions=rolled_back,
            success_rate=round((successful / len(records)) * 100, 2) if records else 0,
            average_duration_ms=round(total_duration / len(records), 2) if records else 0,
            total_issues_found=total_issues_found,
            total_issues_fixed=total_issues_fixed,
            fix_rate=round((total_issues_fixed / total_issues_found) * 100, 2) if total_issues_found > 0 else 0,
            average_coverage_improvement=round(sum(coverage_improvements) / len(coverage_improvements), 2) if coverage_improvements else 0,
            average_quality_improvement=round(sum(quality_improvements) / len(quality_improvements), 2) if quality_improvements else 0
        )

    def _analyze_problems(self, records: List[EvolutionRecord]) -> ProblemAnalysis:
        issue_type_counts: Dict[str, int] = defaultdict(int)
        severity_counts: Dict[str, int] = defaultdict(int)
        issue_details: List[Dict[str, Any]] = []

        for record in records:
            for pattern in record.patterns_learned:
                issue_type_counts[pattern] += 1
            for side_effect in record.side_effects:
                severity_counts["medium"] += 1
                issue_details.append({
                    "type": "side_effect",
                    "description": side_effect,
                    "evolution_id": record.evolution_id
                })

        total_issues = sum(issue_type_counts.values()) if issue_type_counts else 1
        issue_distributions = [
            IssueDistribution(
                issue_type=issue_type,
                count=count,
                percentage=round((count / total_issues) * 100, 2),
                severity_distribution={"medium": count}
            )
            for issue_type, count in sorted(issue_type_counts.items(), key=lambda x: -x[1])
        ]

        top_issues = issue_details[:10] if issue_details else [
            {"type": "no_issues", "description": "该周期内无重大问题", "count": 0}
        ]

        problem_trends = self._calculate_problem_trends(records)

        return ProblemAnalysis(
            issue_distributions=issue_distributions[:10],
            severity_summary=dict(severity_counts),
            top_issues=top_issues,
            problem_trends=problem_trends
        )

    def _calculate_problem_trends(self, records: List[EvolutionRecord]) -> List[Dict[str, Any]]:
        if len(records) < 2:
            return []

        trends = []
        sorted_records = sorted(records, key=lambda r: r.timestamp)
        
        mid_point = len(sorted_records) // 2
        first_half = sorted_records[:mid_point]
        second_half = sorted_records[mid_point:]

        first_issues = sum(r.issues_found for r in first_half)
        second_issues = sum(r.issues_found for r in second_half)

        if first_issues > 0:
            change_rate = ((second_issues - first_issues) / first_issues) * 100
            trends.append({
                "metric": "issues_found",
                "direction": "decreasing" if change_rate < 0 else "increasing",
                "change_rate": round(change_rate, 2)
            })

        return trends

    def _analyze_fix_effect(self, records: List[EvolutionRecord]) -> FixEffect:
        if not records:
            return FixEffect(
                total_fixes=0,
                successful_fixes=0,
                failed_fixes=0,
                fix_success_rate=0.0,
                side_effects_count=0,
                side_effects_types={},
                rollback_count=0,
                fix_time_distribution={}
            )

        total_fixes = sum(r.issues_fixed for r in records)
        successful_fixes = sum(r.issues_fixed for r in records if r.status == EvolutionStatus.SUCCESS)
        failed_fixes = sum(r.issues_remaining for r in records if r.status == EvolutionStatus.FAILED)

        side_effects_count = sum(len(r.side_effects) for r in records)
        side_effects_types: Dict[str, int] = defaultdict(int)
        for record in records:
            for side_effect in record.side_effects:
                effect_type = side_effect.split(":")[0] if ":" in side_effect else "unknown"
                side_effects_types[effect_type] += 1

        rollback_count = sum(1 for r in records if r.status == EvolutionStatus.ROLLED_BACK)

        fix_time_distribution = self._calculate_fix_time_distribution(records)

        return FixEffect(
            total_fixes=total_fixes,
            successful_fixes=successful_fixes,
            failed_fixes=failed_fixes,
            fix_success_rate=round((successful_fixes / total_fixes) * 100, 2) if total_fixes > 0 else 0,
            side_effects_count=side_effects_count,
            side_effects_types=dict(side_effects_types),
            rollback_count=rollback_count,
            fix_time_distribution=fix_time_distribution
        )

    def _calculate_fix_time_distribution(self, records: List[EvolutionRecord]) -> Dict[str, int]:
        distribution = {
            "fast (<1s)": 0,
            "normal (1s-10s)": 0,
            "slow (10s-60s)": 0,
            "very_slow (>60s)": 0
        }

        for record in records:
            duration_s = record.duration_ms / 1000
            if duration_s < 1:
                distribution["fast (<1s)"] += 1
            elif duration_s < 10:
                distribution["normal (1s-10s)"] += 1
            elif duration_s < 60:
                distribution["slow (10s-60s)"] += 1
            else:
                distribution["very_slow (>60s)"] += 1

        return distribution

    def _analyze_learning_outcome(self, records: List[EvolutionRecord]) -> LearningOutcome:
        all_patterns: List[Dict[str, Any]] = []
        all_updates: List[Dict[str, Any]] = []
        all_refinements: List[Dict[str, Any]] = []

        for record in records:
            for pattern in record.patterns_learned:
                all_patterns.append({
                    "pattern": pattern,
                    "evolution_id": record.evolution_id,
                    "timestamp": record.timestamp
                })
            for update in record.knowledge_updates:
                all_updates.append({
                    "update": update,
                    "evolution_id": record.evolution_id,
                    "timestamp": record.timestamp
                })

        return LearningOutcome(
            new_patterns_learned=len(all_patterns),
            pattern_list=all_patterns[:20],
            knowledge_base_updates=len(all_updates),
            update_list=all_updates[:20],
            rule_refinements=len(all_refinements),
            refinement_list=all_refinements[:20]
        )

    def _analyze_trends(self, records: List[EvolutionRecord]) -> List[TrendAnalysis]:
        trends = []

        if len(records) < 2:
            return trends

        sorted_records = sorted(records, key=lambda r: r.timestamp)

        coverage_trend = self._calculate_metric_trend(
            "coverage",
            [r.coverage_after for r in sorted_records],
            [r.timestamp for r in sorted_records]
        )
        trends.append(coverage_trend)

        quality_trend = self._calculate_metric_trend(
            "quality_score",
            [r.quality_score_after for r in sorted_records],
            [r.timestamp for r in sorted_records]
        )
        trends.append(quality_trend)

        duration_trend = self._calculate_metric_trend(
            "duration",
            [r.duration_ms for r in sorted_records],
            [r.timestamp for r in sorted_records],
            lower_is_better=True
        )
        trends.append(duration_trend)

        return trends

    def _calculate_metric_trend(
        self,
        metric_name: str,
        values: List[float],
        timestamps: List[str],
        lower_is_better: bool = False
    ) -> TrendAnalysis:
        if len(values) < 2:
            return TrendAnalysis(
                metric_name=metric_name,
                values=values,
                timestamps=timestamps,
                trend_direction="stable",
                improvement_rate=0.0
            )

        mid_point = len(values) // 2
        first_half = values[:mid_point]
        second_half = values[mid_point:]

        first_avg = sum(first_half) / len(first_half) if first_half else 0
        second_avg = sum(second_half) / len(second_half) if second_half else 0

        if first_avg == 0:
            improvement_rate = 0.0
        else:
            improvement_rate = ((second_avg - first_avg) / first_avg) * 100

        if lower_is_better:
            improvement_rate = -improvement_rate

        if improvement_rate > 5:
            direction = "improving"
        elif improvement_rate < -5:
            direction = "declining"
        else:
            direction = "stable"

        prediction = None
        if len(values) >= 3:
            recent_values = values[-3:]
            avg_change = sum(recent_values) / len(recent_values)
            prediction = round(second_avg + avg_change * 0.1, 2)

        return TrendAnalysis(
            metric_name=metric_name,
            values=values,
            timestamps=timestamps,
            trend_direction=direction,
            improvement_rate=round(improvement_rate, 2),
            prediction=prediction
        )

    def _generate_recommendations(
        self,
        statistics: EvolutionStatistics,
        problem_analysis: ProblemAnalysis,
        fix_effect: FixEffect
    ) -> List[str]:
        recommendations = []

        if statistics.success_rate < 80:
            recommendations.append(f"演化成功率较低({statistics.success_rate}%)，建议检查演化策略和测试覆盖率")

        if statistics.average_duration_ms > 10000:
            recommendations.append(f"平均演化耗时较长({statistics.average_duration_ms}ms)，建议优化演化流程")

        if fix_effect.side_effects_count > 0:
            recommendations.append(f"检测到{fix_effect.side_effects_count}个副作用，建议增强副作用检测机制")

        if fix_effect.rollback_count > 0:
            recommendations.append(f"发生{fix_effect.rollback_count}次回滚，建议改进演化验证流程")

        if statistics.fix_rate < 70:
            recommendations.append(f"问题修复率较低({statistics.fix_rate}%)，建议增强自动修复能力")

        if statistics.average_coverage_improvement < 0:
            recommendations.append("覆盖率呈下降趋势，建议补充测试用例")

        for trend in problem_analysis.problem_trends:
            if trend.get("direction") == "increasing":
                recommendations.append(f"问题数量呈上升趋势，建议加强预防措施")

        if not recommendations:
            recommendations.append("演化状态良好，继续保持当前策略")

        return recommendations

    def _generate_summary(self, statistics: EvolutionStatistics, report_type: ReportType) -> str:
        type_names = {
            ReportType.DAILY: "日报",
            ReportType.WEEKLY: "周报",
            ReportType.MONTHLY: "月报",
            ReportType.EVOLUTION_CYCLE: "演化周期报告",
            ReportType.COMPARISON: "对比报告",
            ReportType.DIAGNOSTIC: "诊断报告"
        }

        summary_parts = [
            f"【{type_names.get(report_type, '报告')}摘要】",
            f"共执行{statistics.total_evolutions}次演化，",
            f"成功率{statistics.success_rate}%，",
            f"平均耗时{statistics.average_duration_ms}ms。"
        ]

        if statistics.total_issues_found > 0:
            summary_parts.append(f"发现{statistics.total_issues_found}个问题，")
            summary_parts.append(f"修复{statistics.total_issues_fixed}个，")
            summary_parts.append(f"修复率{statistics.fix_rate}%。")

        if statistics.average_coverage_improvement != 0:
            sign = "+" if statistics.average_coverage_improvement > 0 else ""
            summary_parts.append(f"覆盖率{sign}{statistics.average_coverage_improvement}%。")

        return "".join(summary_parts)

    def generate_report(
        self,
        report_type: ReportType,
        start_date: datetime,
        end_date: datetime
    ) -> EvolutionReport:
        records = self._get_records_in_period(start_date, end_date)
        
        statistics = self._calculate_statistics(records)
        problem_analysis = self._analyze_problems(records)
        fix_effect = self._analyze_fix_effect(records)
        learning_outcome = self._analyze_learning_outcome(records)
        trend_analyses = self._analyze_trends(records)
        recommendations = self._generate_recommendations(statistics, problem_analysis, fix_effect)
        summary = self._generate_summary(statistics, report_type)

        report_id = f"RPT-{report_type.value.upper()}-{datetime.now().strftime('%Y%m%d%H%M%S')}"

        return EvolutionReport(
            report_id=report_id,
            report_type=report_type,
            timestamp=datetime.now().isoformat(),
            period_start=start_date.isoformat(),
            period_end=end_date.isoformat(),
            statistics=statistics,
            problem_analysis=problem_analysis,
            fix_effect=fix_effect,
            learning_outcome=learning_outcome,
            trend_analyses=trend_analyses,
            recommendations=recommendations,
            summary=summary
        )

    def generate_daily_report(self, date: Optional[datetime] = None) -> EvolutionReport:
        target_date = date or datetime.now()
        start_date = target_date.replace(hour=0, minute=0, second=0, microsecond=0)
        end_date = start_date + timedelta(days=1)
        
        return self.generate_report(ReportType.DAILY, start_date, end_date)

    def generate_weekly_report(self, end_date: Optional[datetime] = None) -> EvolutionReport:
        end = end_date or datetime.now()
        start_date = end - timedelta(days=7)
        
        return self.generate_report(ReportType.WEEKLY, start_date, end)

    def generate_monthly_report(self, end_date: Optional[datetime] = None) -> EvolutionReport:
        end = end_date or datetime.now()
        start_date = end - timedelta(days=30)
        
        return self.generate_report(ReportType.MONTHLY, start_date, end)

    def generate_evolution_cycle_report(self, cycle_id: str) -> EvolutionReport:
        cycle_records = [r for r in self.records if cycle_id in r.evolution_id]
        
        if not cycle_records:
            start_date = datetime.now() - timedelta(days=1)
            end_date = datetime.now()
        else:
            timestamps = [datetime.fromisoformat(r.timestamp) for r in cycle_records]
            start_date = min(timestamps)
            end_date = max(timestamps)

        return self.generate_report(ReportType.EVOLUTION_CYCLE, start_date, end_date)

    def generate_diagnostic_report(self) -> EvolutionReport:
        end_date = datetime.now()
        start_date = end_date - timedelta(days=7)
        
        return self.generate_report(ReportType.DIAGNOSTIC, start_date, end_date)

    def generate_comparison_report(
        self,
        before_snapshot: Dict[str, Any],
        after_snapshot: Dict[str, Any]
    ) -> ComparisonReport:
        report_id = f"CMP-{datetime.now().strftime('%Y%m%d%H%M%S')}"

        changes: Dict[str, Any] = {}
        improvements: List[Dict[str, Any]] = []
        regressions: List[Dict[str, Any]] = []

        for key in set(list(before_snapshot.keys()) + list(after_snapshot.keys())):
            before_val = before_snapshot.get(key, 0)
            after_val = after_snapshot.get(key, 0)

            if isinstance(before_val, (int, float)) and isinstance(after_val, (int, float)):
                change = after_val - before_val
                change_percent = (change / before_val * 100) if before_val != 0 else 0

                changes[key] = {
                    "before": before_val,
                    "after": after_val,
                    "change": round(change, 4),
                    "change_percent": round(change_percent, 2)
                }

                if key in ["coverage", "quality_score", "success_rate"]:
                    if change > 0:
                        improvements.append({
                            "metric": key,
                            "improvement": round(change, 4),
                            "percent": round(change_percent, 2)
                        })
                    elif change < 0:
                        regressions.append({
                            "metric": key,
                            "regression": round(abs(change), 4),
                            "percent": round(abs(change_percent), 2)
                        })
                elif key in ["issues_found", "duration_ms", "error_count"]:
                    if change < 0:
                        improvements.append({
                            "metric": key,
                            "improvement": round(abs(change), 4),
                            "percent": round(abs(change_percent), 2)
                        })
                    elif change > 0:
                        regressions.append({
                            "metric": key,
                            "regression": round(change, 4),
                            "percent": round(change_percent, 2)
                        })

        if len(improvements) > len(regressions):
            overall_assessment = "positive"
        elif len(regressions) > len(improvements):
            overall_assessment = "negative"
        else:
            overall_assessment = "neutral"

        recommendations = self._generate_comparison_recommendations(improvements, regressions)

        return ComparisonReport(
            report_id=report_id,
            timestamp=datetime.now().isoformat(),
            before_snapshot=before_snapshot,
            after_snapshot=after_snapshot,
            changes=changes,
            improvements=improvements,
            regressions=regressions,
            overall_assessment=overall_assessment,
            recommendations=recommendations
        )

    def _generate_comparison_recommendations(
        self,
        improvements: List[Dict[str, Any]],
        regressions: List[Dict[str, Any]]
    ) -> List[str]:
        recommendations = []

        for improvement in improvements:
            recommendations.append(f"{improvement['metric']}提升了{improvement['percent']}%，继续保持")

        for regression in regressions:
            recommendations.append(f"{regression['metric']}下降了{regression['percent']}%，需要关注")

        if not recommendations:
            recommendations.append("演化前后无明显变化，建议进一步分析")

        return recommendations

    def generate_history_report(self, days: int = 30) -> EvolutionReport:
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        return self.generate_report(ReportType.MONTHLY, start_date, end_date)

    def save_report(
        self,
        report: Any,
        format: str = "json",
        output_path: Optional[Path] = None
    ) -> Path:
        if format == "json":
            return self._save_json_report(report, output_path)
        elif format == "markdown":
            return self._save_markdown_report(report, output_path)
        elif format == "html":
            return self._save_html_report(report, output_path)
        else:
            return self._save_json_report(report, output_path)

    def _save_json_report(self, report: Any, output_path: Optional[Path] = None) -> Path:
        if output_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            if hasattr(report, 'report_type'):
                filename = f"evolution_report_{report.report_type.value}_{timestamp}.json"
            else:
                filename = f"comparison_report_{timestamp}.json"
            output_path = self.reports_dir / filename

        data = report.to_dict() if hasattr(report, 'to_dict') else report

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        latest_path = output_path.parent / f"latest_{output_path.name.split('_', 1)[1]}"
        with open(latest_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        return output_path

    def _save_markdown_report(self, report: Any, output_path: Optional[Path] = None) -> Path:
        if output_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            if hasattr(report, 'report_type'):
                filename = f"evolution_report_{report.report_type.value}_{timestamp}.md"
            else:
                filename = f"comparison_report_{timestamp}.md"
            output_path = self.reports_dir / filename

        if isinstance(report, EvolutionReport):
            content = self._generate_markdown_content(report)
        elif isinstance(report, ComparisonReport):
            content = self._generate_comparison_markdown_content(report)
        else:
            content = str(report)

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(content)

        return output_path

    def _generate_markdown_content(self, report: EvolutionReport) -> str:
        lines = [
            f"# 演化报告 - {report.report_type.value.upper()}",
            "",
            f"**报告ID**: {report.report_id}",
            f"**生成时间**: {report.timestamp}",
            f"**统计周期**: {report.period_start} ~ {report.period_end}",
            "",
            "## 摘要",
            "",
            report.summary,
            "",
            "## 演化统计",
            "",
            f"- 总演化次数: {report.statistics.total_evolutions}",
            f"- 成功次数: {report.statistics.successful_evolutions}",
            f"- 失败次数: {report.statistics.failed_evolutions}",
            f"- 部分成功: {report.statistics.partial_evolutions}",
            f"- 回滚次数: {report.statistics.rolled_back_evolutions}",
            f"- 成功率: {report.statistics.success_rate}%",
            f"- 平均耗时: {report.statistics.average_duration_ms}ms",
            "",
            "## 问题分析",
            "",
            f"- 发现问题总数: {report.statistics.total_issues_found}",
            f"- 修复问题总数: {report.statistics.total_issues_fixed}",
            f"- 修复率: {report.statistics.fix_rate}%",
            "",
            "### 问题类型分布",
            ""
        ]

        for dist in report.problem_analysis.issue_distributions[:5]:
            lines.append(f"- {dist.issue_type}: {dist.count} ({dist.percentage}%)")

        lines.extend([
            "",
            "## 修复效果",
            "",
            f"- 总修复数: {report.fix_effect.total_fixes}",
            f"- 成功修复: {report.fix_effect.successful_fixes}",
            f"- 修复成功率: {report.fix_effect.fix_success_rate}%",
            f"- 副作用数量: {report.fix_effect.side_effects_count}",
            "",
            "## 学习成果",
            "",
            f"- 学习新模式: {report.learning_outcome.new_patterns_learned}",
            f"- 知识库更新: {report.learning_outcome.knowledge_base_updates}",
            "",
            "## 趋势分析",
            ""
        ])

        for trend in report.trend_analyses:
            direction_emoji = "📈" if trend.trend_direction == "improving" else "📉" if trend.trend_direction == "declining" else "➡️"
            lines.append(f"- **{trend.metric_name}**: {direction_emoji} {trend.trend_direction} ({trend.improvement_rate:+.2f}%)")

        lines.extend([
            "",
            "## 建议",
            ""
        ])

        for i, rec in enumerate(report.recommendations, 1):
            lines.append(f"{i}. {rec}")

        return "\n".join(lines)

    def _generate_comparison_markdown_content(self, report: ComparisonReport) -> str:
        lines = [
            "# 演化对比报告",
            "",
            f"**报告ID**: {report.report_id}",
            f"**生成时间**: {report.timestamp}",
            "",
            "## 总体评估",
            "",
            f"**评估结果**: {report.overall_assessment}",
            "",
            "## 改进项",
            ""
        ]

        for imp in report.improvements:
            lines.append(f"- {imp['metric']}: +{imp['percent']}%")

        lines.extend([
            "",
            "## 回归项",
            ""
        ])

        for reg in report.regressions:
            lines.append(f"- {reg['metric']}: -{reg['percent']}%")

        lines.extend([
            "",
            "## 详细变化",
            ""
        ])

        for key, change in report.changes.items():
            lines.append(f"- **{key}**: {change['before']} → {change['after']} ({change['change_percent']:+.2f}%)")

        lines.extend([
            "",
            "## 建议",
            ""
        ])

        for i, rec in enumerate(report.recommendations, 1):
            lines.append(f"{i}. {rec}")

        return "\n".join(lines)

    def _save_html_report(self, report: Any, output_path: Optional[Path] = None) -> Path:
        if output_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            if hasattr(report, 'report_type'):
                filename = f"evolution_report_{report.report_type.value}_{timestamp}.html"
            else:
                filename = f"comparison_report_{timestamp}.html"
            output_path = self.reports_dir / filename

        if isinstance(report, EvolutionReport):
            content = self._generate_html_content(report)
        elif isinstance(report, ComparisonReport):
            content = self._generate_comparison_html_content(report)
        else:
            content = f"<pre>{report}</pre>"

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(content)

        return output_path

    def _generate_html_content(self, report: EvolutionReport) -> str:
        stats = report.statistics
        fix = report.fix_effect
        learning = report.learning_outcome

        trend_rows = ""
        for trend in report.trend_analyses:
            direction_class = "improving" if trend.trend_direction == "improving" else "declining" if trend.trend_direction == "declining" else "stable"
            direction_icon = "📈" if trend.trend_direction == "improving" else "📉" if trend.trend_direction == "declining" else "➡️"
            trend_rows += f"""
            <tr>
                <td>{trend.metric_name}</td>
                <td class="{direction_class}">{direction_icon} {trend.trend_direction}</td>
                <td>{trend.improvement_rate:+.2f}%</td>
                <td>{trend.prediction if trend.prediction else 'N/A'}</td>
            </tr>"""

        issue_rows = ""
        for dist in report.problem_analysis.issue_distributions[:5]:
            issue_rows += f"""
            <tr>
                <td>{dist.issue_type}</td>
                <td>{dist.count}</td>
                <td>{dist.percentage}%</td>
            </tr>"""

        rec_items = ""
        for rec in report.recommendations:
            rec_items += f"<li>{rec}</li>"

        return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>演化报告 - {report.report_type.value.upper()}</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #f5f5f5; padding: 20px; }}
        .container {{ max-width: 1200px; margin: 0 auto; }}
        .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; border-radius: 10px; margin-bottom: 20px; }}
        .header h1 {{ font-size: 28px; margin-bottom: 10px; }}
        .summary {{ background: white; border-radius: 10px; padding: 20px; margin-bottom: 20px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
        .stats-grid {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 15px; margin-bottom: 20px; }}
        .stat-card {{ background: white; border-radius: 10px; padding: 20px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); text-align: center; }}
        .stat-card h3 {{ color: #666; font-size: 14px; margin-bottom: 10px; }}
        .stat-card .value {{ font-size: 28px; font-weight: bold; color: #333; }}
        .stat-card .value.success {{ color: #10b981; }}
        .stat-card .value.warning {{ color: #f59e0b; }}
        .stat-card .value.danger {{ color: #ef4444; }}
        .card {{ background: white; border-radius: 10px; padding: 20px; margin-bottom: 20px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
        .card h2 {{ color: #333; margin-bottom: 15px; font-size: 18px; border-bottom: 2px solid #667eea; padding-bottom: 10px; }}
        table {{ width: 100%; border-collapse: collapse; margin-top: 15px; }}
        th, td {{ padding: 12px; text-align: left; border-bottom: 1px solid #eee; }}
        th {{ background: #f8f9fa; font-weight: 600; }}
        .improving {{ color: #10b981; }}
        .declining {{ color: #ef4444; }}
        .stable {{ color: #6b7280; }}
        .recommendations {{ background: #f0f9ff; border-left: 4px solid #3b82f6; padding: 15px; margin-top: 15px; }}
        .recommendations h3 {{ color: #1e40af; margin-bottom: 10px; }}
        .recommendations ul {{ list-style: none; }}
        .recommendations li {{ padding: 5px 0; padding-left: 20px; position: relative; }}
        .recommendations li::before {{ content: "→"; position: absolute; left: 0; color: #3b82f6; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📊 演化报告 - {report.report_type.value.upper()}</h1>
            <p>报告ID: {report.report_id} | 生成时间: {report.timestamp}</p>
            <p>统计周期: {report.period_start} ~ {report.period_end}</p>
        </div>

        <div class="summary">
            <h2>摘要</h2>
            <p>{report.summary}</p>
        </div>

        <div class="stats-grid">
            <div class="stat-card">
                <h3>总演化次数</h3>
                <div class="value">{stats.total_evolutions}</div>
            </div>
            <div class="stat-card">
                <h3>成功率</h3>
                <div class="value {'success' if stats.success_rate >= 80 else 'warning' if stats.success_rate >= 60 else 'danger'}">{stats.success_rate}%</div>
            </div>
            <div class="stat-card">
                <h3>平均耗时</h3>
                <div class="value">{stats.average_duration_ms}ms</div>
            </div>
            <div class="stat-card">
                <h3>修复率</h3>
                <div class="value {'success' if stats.fix_rate >= 70 else 'warning' if stats.fix_rate >= 50 else 'danger'}">{stats.fix_rate}%</div>
            </div>
        </div>

        <div class="card">
            <h2>演化统计</h2>
            <table>
                <tr><th>指标</th><th>数值</th></tr>
                <tr><td>成功次数</td><td class="improving">{stats.successful_evolutions}</td></tr>
                <tr><td>失败次数</td><td class="declining">{stats.failed_evolutions}</td></tr>
                <tr><td>部分成功</td><td>{stats.partial_evolutions}</td></tr>
                <tr><td>回滚次数</td><td class="declining">{stats.rolled_back_evolutions}</td></tr>
                <tr><td>覆盖率变化</td><td>{stats.average_coverage_improvement:+.2f}%</td></tr>
                <tr><td>质量分数变化</td><td>{stats.average_quality_improvement:+.2f}</td></tr>
            </table>
        </div>

        <div class="card">
            <h2>问题分析</h2>
            <table>
                <tr><th>问题类型</th><th>数量</th><th>占比</th></tr>
                {issue_rows}
            </table>
        </div>

        <div class="card">
            <h2>修复效果</h2>
            <table>
                <tr><th>指标</th><th>数值</th></tr>
                <tr><td>总修复数</td><td>{fix.total_fixes}</td></tr>
                <tr><td>成功修复</td><td>{fix.successful_fixes}</td></tr>
                <tr><td>修复成功率</td><td>{fix.fix_success_rate}%</td></tr>
                <tr><td>副作用数量</td><td>{fix.side_effects_count}</td></tr>
            </table>
        </div>

        <div class="card">
            <h2>学习成果</h2>
            <table>
                <tr><th>指标</th><th>数值</th></tr>
                <tr><td>学习新模式</td><td>{learning.new_patterns_learned}</td></tr>
                <tr><td>知识库更新</td><td>{learning.knowledge_base_updates}</td></tr>
                <tr><td>规则优化</td><td>{learning.rule_refinements}</td></tr>
            </table>
        </div>

        <div class="card">
            <h2>趋势分析</h2>
            <table>
                <tr><th>指标</th><th>趋势</th><th>变化率</th><th>预测</th></tr>
                {trend_rows}
            </table>
        </div>

        <div class="recommendations">
            <h3>建议</h3>
            <ul>
                {rec_items}
            </ul>
        </div>
    </div>
</body>
</html>"""

    def _generate_comparison_html_content(self, report: ComparisonReport) -> str:
        improvement_rows = ""
        for imp in report.improvements:
            improvement_rows += f"""
            <tr>
                <td>{imp['metric']}</td>
                <td class="improving">+{imp['percent']}%</td>
                <td>{imp['improvement']}</td>
            </tr>"""

        regression_rows = ""
        for reg in report.regressions:
            regression_rows += f"""
            <tr>
                <td>{reg['metric']}</td>
                <td class="declining">-{reg['percent']}%</td>
                <td>{reg['regression']}</td>
            </tr>"""

        change_rows = ""
        for key, change in report.changes.items():
            change_class = "improving" if change['change'] > 0 else "declining" if change['change'] < 0 else ""
            change_rows += f"""
            <tr>
                <td>{key}</td>
                <td>{change['before']}</td>
                <td>{change['after']}</td>
                <td class="{change_class}">{change['change_percent']:+.2f}%</td>
            </tr>"""

        assessment_class = "improving" if report.overall_assessment == "positive" else "declining" if report.overall_assessment == "negative" else "stable"
        assessment_text = "正面" if report.overall_assessment == "positive" else "负面" if report.overall_assessment == "negative" else "中性"

        rec_items = ""
        for rec in report.recommendations:
            rec_items += f"<li>{rec}</li>"

        return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>演化对比报告</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #f5f5f5; padding: 20px; }}
        .container {{ max-width: 1200px; margin: 0 auto; }}
        .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; border-radius: 10px; margin-bottom: 20px; }}
        .header h1 {{ font-size: 28px; margin-bottom: 10px; }}
        .assessment {{ background: white; border-radius: 10px; padding: 20px; margin-bottom: 20px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); text-align: center; }}
        .assessment .result {{ font-size: 36px; font-weight: bold; margin: 10px 0; }}
        .assessment .result.positive {{ color: #10b981; }}
        .assessment .result.negative {{ color: #ef4444; }}
        .assessment .result.neutral {{ color: #6b7280; }}
        .card {{ background: white; border-radius: 10px; padding: 20px; margin-bottom: 20px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
        .card h2 {{ color: #333; margin-bottom: 15px; font-size: 18px; border-bottom: 2px solid #667eea; padding-bottom: 10px; }}
        table {{ width: 100%; border-collapse: collapse; margin-top: 15px; }}
        th, td {{ padding: 12px; text-align: left; border-bottom: 1px solid #eee; }}
        th {{ background: #f8f9fa; font-weight: 600; }}
        .improving {{ color: #10b981; }}
        .declining {{ color: #ef4444; }}
        .stable {{ color: #6b7280; }}
        .recommendations {{ background: #f0f9ff; border-left: 4px solid #3b82f6; padding: 15px; margin-top: 15px; }}
        .recommendations h3 {{ color: #1e40af; margin-bottom: 10px; }}
        .recommendations ul {{ list-style: none; }}
        .recommendations li {{ padding: 5px 0; padding-left: 20px; position: relative; }}
        .recommendations li::before {{ content: "→"; position: absolute; left: 0; color: #3b82f6; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📊 演化对比报告</h1>
            <p>报告ID: {report.report_id} | 生成时间: {report.timestamp}</p>
        </div>

        <div class="assessment">
            <h2>总体评估</h2>
            <div class="result {assessment_class}">{assessment_text}</div>
            <p>改进项: {len(report.improvements)} | 回归项: {len(report.regressions)}</p>
        </div>

        <div class="card">
            <h2>改进项</h2>
            <table>
                <tr><th>指标</th><th>变化</th><th>数值</th></tr>
                {improvement_rows}
            </table>
        </div>

        <div class="card">
            <h2>回归项</h2>
            <table>
                <tr><th>指标</th><th>变化</th><th>数值</th></tr>
                {regression_rows}
            </table>
        </div>

        <div class="card">
            <h2>详细变化</h2>
            <table>
                <tr><th>指标</th><th>演化前</th><th>演化后</th><th>变化率</th></tr>
                {change_rows}
            </table>
        </div>

        <div class="recommendations">
            <h3>建议</h3>
            <ul>
                {rec_items}
            </ul>
        </div>
    </div>
</body>
</html>"""

    def get_statistics(self) -> Dict[str, Any]:
        stats = self._calculate_statistics(self.records)
        return stats.to_dict()

    def export_history(self, format: str = "json", output_path: Optional[Path] = None) -> Path:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        if output_path is None:
            if format == "json":
                output_path = self.history_dir / f"evolution_history_export_{timestamp}.json"
            elif format == "csv":
                output_path = self.history_dir / f"evolution_history_export_{timestamp}.csv"
            else:
                output_path = self.history_dir / f"evolution_history_export_{timestamp}.txt"

        if format == "json":
            data = {
                "records": [r.to_dict() for r in self.records],
                "statistics": self.get_statistics(),
                "exported_at": datetime.now().isoformat()
            }
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        elif format == "csv":
            import csv
            with open(output_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow([
                    "evolution_id", "timestamp", "type", "status", "duration_ms",
                    "issues_found", "issues_fixed", "coverage_before", "coverage_after",
                    "quality_before", "quality_after", "success"
                ])
                for r in self.records:
                    writer.writerow([
                        r.evolution_id, r.timestamp, r.evolution_type, r.status.value,
                        r.duration_ms, r.issues_found, r.issues_fixed,
                        r.coverage_before, r.coverage_after,
                        r.quality_score_before, r.quality_score_after,
                        r.status == EvolutionStatus.SUCCESS
                    ])
        else:
            with open(output_path, "w", encoding="utf-8") as f:
                for r in self.records:
                    f.write(f"{r.timestamp} | {r.evolution_type} | {r.status.value} | {r.details}\n")

        return output_path


def main():
    import argparse

    parser = argparse.ArgumentParser(description="演化报告生成器")
    parser.add_argument("--daily", action="store_true", help="生成日报")
    parser.add_argument("--weekly", action="store_true", help="生成周报")
    parser.add_argument("--monthly", action="store_true", help="生成月报")
    parser.add_argument("--diagnostic", action="store_true", help="生成诊断报告")
    parser.add_argument("--stats", action="store_true", help="显示统计信息")
    parser.add_argument("--export", type=str, choices=["json", "csv", "txt"], help="导出历史数据")
    parser.add_argument("--format", type=str, choices=["json", "markdown", "html"], default="json", help="输出格式")
    parser.add_argument("--days", type=int, default=30, help="统计天数")

    args = parser.parse_args()

    generator = EvolutionReportGenerator()

    if args.daily:
        report = generator.generate_daily_report()
        path = generator.save_report(report, format=args.format)
        print(f"日报已生成: {path}")
    elif args.weekly:
        report = generator.generate_weekly_report()
        path = generator.save_report(report, format=args.format)
        print(f"周报已生成: {path}")
    elif args.monthly:
        report = generator.generate_monthly_report()
        path = generator.save_report(report, format=args.format)
        print(f"月报已生成: {path}")
    elif args.diagnostic:
        report = generator.generate_diagnostic_report()
        path = generator.save_report(report, format=args.format)
        print(f"诊断报告已生成: {path}")
    elif args.stats:
        stats = generator.get_statistics()
        print("\n演化统计:")
        for key, value in stats.items():
            print(f"  {key}: {value}")
    elif args.export:
        path = generator.export_history(args.export)
        print(f"历史数据已导出: {path}")
    else:
        report = generator.generate_history_report(args.days)
        path = generator.save_report(report, format=args.format)
        print(f"历史报告已生成: {path}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
