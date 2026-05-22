"""
优化效果评估体系模块

包含：
- OptimizationMetrics: 优化效果指标定义
- OptimizationComparator: 优化前后对比器
- OptimizationScorer: 优化效果评分器
- OptimizationHistoryTracker: 优化历史追踪器
- UnifiedOptimizationEvaluator: 统一优化效果评估器
"""

import json
import statistics
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class MetricCategory(Enum):
    PERFORMANCE = "performance"
    QUALITY = "quality"
    ARCHITECTURE = "architecture"
    MAINTAINABILITY = "maintainability"
    TESTABILITY = "testability"


class ImprovementLevel(Enum):
    EXCELLENT = "excellent"
    GOOD = "good"
    ACCEPTABLE = "acceptable"
    POOR = "poor"
    REGRESSION = "regression"


@dataclass
class OptimizationMetric:
    name: str
    category: MetricCategory
    description: str
    unit: str
    target_value: Optional[float]
    weight: float
    higher_is_better: bool


@dataclass
class MetricMeasurement:
    metric_name: str
    before_value: float
    after_value: float
    improvement_percent: float
    improvement_level: ImprovementLevel
    passed: bool


@dataclass
class OptimizationScore:
    overall_score: float
    category_scores: Dict[str, float]
    improvement_level: ImprovementLevel
    summary: str


@dataclass
class OptimizationHistory:
    optimization_id: str
    timestamp: str
    optimization_type: str
    metrics: List[MetricMeasurement]
    score: OptimizationScore
    details: Dict[str, Any]


class OptimizationMetrics:
    """优化效果指标定义"""

    def __init__(self):
        self._metrics: Dict[str, OptimizationMetric] = {}
        self._initialize_default_metrics()

    def _initialize_default_metrics(self):
        default_metrics = [
            OptimizationMetric(
                name="execution_time",
                category=MetricCategory.PERFORMANCE,
                description="代码执行时间",
                unit="ms",
                target_value=100.0,
                weight=0.15,
                higher_is_better=False
            ),
            OptimizationMetric(
                name="memory_usage",
                category=MetricCategory.PERFORMANCE,
                description="内存使用量",
                unit="MB",
                target_value=50.0,
                weight=0.10,
                higher_is_better=False
            ),
            OptimizationMetric(
                name="cpu_usage",
                category=MetricCategory.PERFORMANCE,
                description="CPU使用率",
                unit="%",
                target_value=30.0,
                weight=0.10,
                higher_is_better=False
            ),
            OptimizationMetric(
                name="cyclomatic_complexity",
                category=MetricCategory.QUALITY,
                description="圈复杂度",
                unit="points",
                target_value=10.0,
                weight=0.12,
                higher_is_better=False
            ),
            OptimizationMetric(
                name="code_duplication",
                category=MetricCategory.QUALITY,
                description="代码重复率",
                unit="%",
                target_value=5.0,
                weight=0.10,
                higher_is_better=False
            ),
            OptimizationMetric(
                name="function_length",
                category=MetricCategory.QUALITY,
                description="平均函数长度",
                unit="lines",
                target_value=30.0,
                weight=0.08,
                higher_is_better=False
            ),
            OptimizationMetric(
                name="coupling_score",
                category=MetricCategory.ARCHITECTURE,
                description="模块耦合度",
                unit="score",
                target_value=0.3,
                weight=0.10,
                higher_is_better=False
            ),
            OptimizationMetric(
                name="cohesion_score",
                category=MetricCategory.ARCHITECTURE,
                description="模块内聚度",
                unit="score",
                target_value=0.7,
                weight=0.08,
                higher_is_better=True
            ),
            OptimizationMetric(
                name="dependency_cycles",
                category=MetricCategory.ARCHITECTURE,
                description="依赖循环数",
                unit="count",
                target_value=0.0,
                weight=0.07,
                higher_is_better=False
            ),
            OptimizationMetric(
                name="test_coverage",
                category=MetricCategory.TESTABILITY,
                description="测试覆盖率",
                unit="%",
                target_value=80.0,
                weight=0.10,
                higher_is_better=True
            ),
        ]

        for metric in default_metrics:
            self._metrics[metric.name] = metric

    def get_metric(self, name: str) -> Optional[OptimizationMetric]:
        return self._metrics.get(name)

    def get_all_metrics(self) -> Dict[str, OptimizationMetric]:
        return self._metrics.copy()

    def get_metrics_by_category(self, category: MetricCategory) -> List[OptimizationMetric]:
        return [m for m in self._metrics.values() if m.category == category]


class OptimizationComparator:
    """优化前后对比器"""

    def __init__(self):
        self.metrics_definition = OptimizationMetrics()
        self._measurements: List[MetricMeasurement] = []

    def compare(
        self,
        before_metrics: Dict[str, float],
        after_metrics: Dict[str, float]
    ) -> List[MetricMeasurement]:
        self._measurements.clear()

        for metric_name, before_value in before_metrics.items():
            if metric_name in after_metrics:
                after_value = after_metrics[metric_name]
                metric_def = self.metrics_definition.get_metric(metric_name)

                if metric_def:
                    measurement = self._create_measurement(
                        metric_name,
                        before_value,
                        after_value,
                        metric_def
                    )
                    self._measurements.append(measurement)

        return self._measurements

    def _create_measurement(
        self,
        metric_name: str,
        before_value: float,
        after_value: float,
        metric_def: OptimizationMetric
    ) -> MetricMeasurement:
        if before_value != 0:
            if metric_def.higher_is_better:
                improvement_percent = ((after_value - before_value) / before_value) * 100
            else:
                improvement_percent = ((before_value - after_value) / before_value) * 100
        else:
            improvement_percent = 0.0 if after_value == 0 else 100.0

        improvement_level = self._determine_improvement_level(
            improvement_percent,
            metric_def.higher_is_better
        )

        passed = self._check_if_passed(after_value, metric_def)

        return MetricMeasurement(
            metric_name=metric_name,
            before_value=before_value,
            after_value=after_value,
            improvement_percent=improvement_percent,
            improvement_level=improvement_level,
            passed=passed
        )

    def _determine_improvement_level(self, improvement_percent: float, higher_is_better: bool) -> ImprovementLevel:
        if improvement_percent >= 50:
            return ImprovementLevel.EXCELLENT
        elif improvement_percent >= 20:
            return ImprovementLevel.GOOD
        elif improvement_percent >= 5:
            return ImprovementLevel.ACCEPTABLE
        elif improvement_percent >= 0:
            return ImprovementLevel.POOR
        else:
            return ImprovementLevel.REGRESSION

    def _check_if_passed(self, value: float, metric_def: OptimizationMetric) -> bool:
        if metric_def.target_value is None:
            return True

        if metric_def.higher_is_better:
            return value >= metric_def.target_value
        else:
            return value <= metric_def.target_value

    def get_measurements_by_category(self, category: MetricCategory) -> List[MetricMeasurement]:
        return [
            m for m in self._measurements
            if self.metrics_definition.get_metric(m.metric_name)?.category == category
        ]


class OptimizationScorer:
    """优化效果评分器"""

    def __init__(self):
        self.metrics_definition = OptimizationMetrics()

    def calculate_score(self, measurements: List[MetricMeasurement]) -> OptimizationScore:
        category_scores = self._calculate_category_scores(measurements)

        overall_score = self._calculate_overall_score(category_scores)

        improvement_level = self._determine_overall_improvement_level(overall_score)

        summary = self._generate_summary(measurements, overall_score, improvement_level)

        return OptimizationScore(
            overall_score=overall_score,
            category_scores=category_scores,
            improvement_level=improvement_level,
            summary=summary
        )

    def _calculate_category_scores(self, measurements: List[MetricMeasurement]) -> Dict[str, float]:
        category_scores = {}

        for category in MetricCategory:
            category_measurements = [
                m for m in measurements
                if self.metrics_definition.get_metric(m.metric_name)?.category == category
            ]

            if category_measurements:
                weighted_sum = 0.0
                total_weight = 0.0

                for measurement in category_measurements:
                    metric_def = self.metrics_definition.get_metric(measurement.metric_name)
                    if metric_def:
                        score = self._normalize_score(measurement.improvement_percent)
                        weighted_sum += score * metric_def.weight
                        total_weight += metric_def.weight

                if total_weight > 0:
                    category_scores[category.value] = (weighted_sum / total_weight) * 100

        return category_scores

    def _normalize_score(self, improvement_percent: float) -> float:
        if improvement_percent >= 50:
            return 1.0
        elif improvement_percent >= 20:
            return 0.8
        elif improvement_percent >= 5:
            return 0.6
        elif improvement_percent >= 0:
            return 0.4
        else:
            return max(0.0, 0.4 + improvement_percent / 100)

    def _calculate_overall_score(self, category_scores: Dict[str, float]) -> float:
        if not category_scores:
            return 0.0

        return statistics.mean(category_scores.values())

    def _determine_overall_improvement_level(self, overall_score: float) -> ImprovementLevel:
        if overall_score >= 80:
            return ImprovementLevel.EXCELLENT
        elif overall_score >= 60:
            return ImprovementLevel.GOOD
        elif overall_score >= 40:
            return ImprovementLevel.ACCEPTABLE
        elif overall_score >= 20:
            return ImprovementLevel.POOR
        else:
            return ImprovementLevel.REGRESSION

    def _generate_summary(
        self,
        measurements: List[MetricMeasurement],
        overall_score: float,
        improvement_level: ImprovementLevel
    ) -> str:
        excellent_count = sum(1 for m in measurements if m.improvement_level == ImprovementLevel.EXCELLENT)
        good_count = sum(1 for m in measurements if m.improvement_level == ImprovementLevel.GOOD)
        regression_count = sum(1 for m in measurements if m.improvement_level == ImprovementLevel.REGRESSION)

        summary_parts = [
            f"总体得分: {overall_score:.1f}/100",
            f"改进等级: {improvement_level.value}",
            f"优秀改进: {excellent_count} 项",
            f"良好改进: {good_count} 项",
        ]

        if regression_count > 0:
            summary_parts.append(f"性能回退: {regression_count} 项")

        return " | ".join(summary_parts)


class OptimizationHistoryTracker:
    """优化历史追踪器"""

    def __init__(self, history_file: Optional[Path] = None):
        self._history: List[OptimizationHistory] = []
        self._history_file = history_file or Path("optimization_history.json")

        if self._history_file.exists():
            self._load_history()

    def record_optimization(
        self,
        optimization_id: str,
        optimization_type: str,
        measurements: List[MetricMeasurement],
        score: OptimizationScore,
        details: Dict[str, Any]
    ):
        history_entry = OptimizationHistory(
            optimization_id=optimization_id,
            timestamp=datetime.now().isoformat(),
            optimization_type=optimization_type,
            metrics=measurements,
            score=score,
            details=details
        )

        self._history.append(history_entry)
        self._save_history()

    def get_history(self, limit: Optional[int] = None) -> List[OptimizationHistory]:
        if limit:
            return self._history[-limit:]
        return self._history.copy()

    def get_optimization_by_id(self, optimization_id: str) -> Optional[OptimizationHistory]:
        for entry in self._history:
            if entry.optimization_id == optimization_id:
                return entry
        return None

    def get_optimizations_by_type(self, optimization_type: str) -> List[OptimizationHistory]:
        return [
            entry for entry in self._history
            if entry.optimization_type == optimization_type
        ]

    def get_trend_analysis(self) -> Dict[str, Any]:
        if len(self._history) < 2:
            return {'error': '历史记录不足，无法进行趋势分析'}

        recent_scores = [entry.score.overall_score for entry in self._history[-10:]]
        average_score = statistics.mean(recent_scores)
        trend = 'improving' if recent_scores[-1] > recent_scores[0] else 'declining'

        return {
            'total_optimizations': len(self._history),
            'average_score': average_score,
            'trend': trend,
            'recent_scores': recent_scores,
            'best_score': max(recent_scores),
            'worst_score': min(recent_scores)
        }

    def _load_history(self):
        try:
            with open(self._history_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            for entry_data in data:
                measurements = [
                    MetricMeasurement(
                        metric_name=m['metric_name'],
                        before_value=m['before_value'],
                        after_value=m['after_value'],
                        improvement_percent=m['improvement_percent'],
                        improvement_level=ImprovementLevel(m['improvement_level']),
                        passed=m['passed']
                    )
                    for m in entry_data.get('metrics', [])
                ]

                score = OptimizationScore(
                    overall_score=entry_data['score']['overall_score'],
                    category_scores=entry_data['score']['category_scores'],
                    improvement_level=ImprovementLevel(entry_data['score']['improvement_level']),
                    summary=entry_data['score']['summary']
                )

                self._history.append(OptimizationHistory(
                    optimization_id=entry_data['optimization_id'],
                    timestamp=entry_data['timestamp'],
                    optimization_type=entry_data['optimization_type'],
                    metrics=measurements,
                    score=score,
                    details=entry_data.get('details', {})
                ))

        except Exception:
            pass

    def _save_history(self):
        try:
            data = []
            for entry in self._history:
                entry_data = {
                    'optimization_id': entry.optimization_id,
                    'timestamp': entry.timestamp,
                    'optimization_type': entry.optimization_type,
                    'metrics': [
                        {
                            'metric_name': m.metric_name,
                            'before_value': m.before_value,
                            'after_value': m.after_value,
                            'improvement_percent': m.improvement_percent,
                            'improvement_level': m.improvement_level.value,
                            'passed': m.passed
                        }
                        for m in entry.metrics
                    ],
                    'score': {
                        'overall_score': entry.score.overall_score,
                        'category_scores': entry.score.category_scores,
                        'improvement_level': entry.score.improvement_level.value,
                        'summary': entry.score.summary
                    },
                    'details': entry.details
                }
                data.append(entry_data)

            with open(self._history_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

        except Exception:
            pass


class UnifiedOptimizationEvaluator:
    """统一优化效果评估器"""

    def __init__(self, history_file: Optional[Path] = None):
        self.metrics_definition = OptimizationMetrics()
        self.comparator = OptimizationComparator()
        self.scorer = OptimizationScorer()
        self.history_tracker = OptimizationHistoryTracker(history_file)

    def evaluate_optimization(
        self,
        optimization_id: str,
        optimization_type: str,
        before_metrics: Dict[str, float],
        after_metrics: Dict[str, float],
        details: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        measurements = self.comparator.compare(before_metrics, after_metrics)

        score = self.scorer.calculate_score(measurements)

        self.history_tracker.record_optimization(
            optimization_id,
            optimization_type,
            measurements,
            score,
            details or {}
        )

        return {
            'optimization_id': optimization_id,
            'timestamp': datetime.now().isoformat(),
            'optimization_type': optimization_type,
            'measurements': [
                {
                    'metric': m.metric_name,
                    'before': m.before_value,
                    'after': m.after_value,
                    'improvement': f"{m.improvement_percent:.1f}%",
                    'level': m.improvement_level.value,
                    'passed': m.passed
                }
                for m in measurements
            ],
            'score': {
                'overall': score.overall_score,
                'categories': score.category_scores,
                'level': score.improvement_level.value,
                'summary': score.summary
            },
            'recommendations': self._generate_recommendations(measurements, score)
        }

    def _generate_recommendations(
        self,
        measurements: List[MetricMeasurement],
        score: OptimizationScore
    ) -> List[str]:
        recommendations = []

        regressions = [m for m in measurements if m.improvement_level == ImprovementLevel.REGRESSION]
        if regressions:
            recommendations.append(
                f"发现 {len(regressions)} 项性能回退，建议检查: {', '.join(m.metric_name for m in regressions)}"
            )

        poor_improvements = [m for m in measurements if m.improvement_level == ImprovementLevel.POOR]
        if poor_improvements:
            recommendations.append(
                f"{len(poor_improvements)} 项指标改进不明显，建议进一步优化"
            )

        if score.overall_score >= 80:
            recommendations.append("优化效果优秀，建议继续保持")
        elif score.overall_score >= 60:
            recommendations.append("优化效果良好，可以考虑进一步改进")
        elif score.overall_score >= 40:
            recommendations.append("优化效果一般，建议加强优化力度")
        else:
            recommendations.append("优化效果不理想，建议重新评估优化策略")

        return recommendations

    def get_evaluation_history(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        history = self.history_tracker.get_history(limit)

        return [
            {
                'optimization_id': entry.optimization_id,
                'timestamp': entry.timestamp,
                'type': entry.optimization_type,
                'score': entry.score.overall_score,
                'level': entry.score.improvement_level.value
            }
            for entry in history
        ]

    def get_trend_report(self) -> Dict[str, Any]:
        return self.history_tracker.get_trend_analysis()

    def export_evaluation_report(
        self,
        evaluation: Dict[str, Any],
        output_path: Path
    ):
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(evaluation, f, ensure_ascii=False, indent=2)
