#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
智能自迭代系统 - Intelligent Auto Iteration System

增强功能：
1. IntelligentProblemPredictor - 基于历史数据的智能问题预测器
   - 时序分析和模式识别
   - 频率统计和趋势预测
   - 关联规则挖掘

2. MultiStrategyOptimizer - 多策略协同优化方案生成器
   - 同时应用多种优化策略
   - 最优组合选择算法
   - 风险评估和效果预测

3. PrioritySorter - 四维优先级排序器
   - 价值/成本/风险/依赖四维评估
   - 动态权重调整
   - 排序结果可视化

使用示例：
    from intelligent_auto_iteration import (
        IntelligentProblemPredictor,
        MultiStrategyOptimizer,
        PrioritySorter
    )

    predictor = IntelligentProblemPredictor()
    issues = predictor.predict_issues(historical_data)

    optimizer = MultiStrategyOptimizer()
    plans = optimizer.generate_optimization_plan(problem)

    sorter = PrioritySorter()
    sorted_tasks = sorter.sort_tasks(tasks)
"""

import json
import logging
import math
import random
from collections import Counter, defaultdict
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple, Set
from enum import Enum, auto

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(name)s - %(message)s'
)
logger = logging.getLogger(__name__)


class IssueSeverity(Enum):
    """问题严重程度"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class PredictionConfidence(Enum):
    """预测置信度"""
    VERY_HIGH = "very_high"      # > 0.8
    HIGH = "high"                # 0.6 - 0.8
    MEDIUM = "medium"            # 0.4 - 0.6
    LOW = "low"                  # < 0.4


@dataclass
class PredictedIssue:
    """预测的问题"""
    issue_id: str
    issue_type: str
    description: str
    probability: float           # 发生概率 (0-1)
    confidence: float            # 置信度 (0-1)
    severity: IssueSeverity
    predicted_time: datetime     # 预测发生时间
    related_patterns: List[str] = field(default_factory=list)
    historical_evidence: List[str] = field(default_factory=list)
    suggested_prevention: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            'issue_id': self.issue_id,
            'issue_type': self.issue_type,
            'description': self.description,
            'probability': round(self.probability, 3),
            'confidence': round(self.confidence, 3),
            'severity': self.severity.value,
            'predicted_time': self.predicted_time.isoformat(),
            'related_patterns': self.related_patterns,
            'historical_evidence': self.historical_evidence,
            'suggested_prevention': self.suggested_prevention,
            'metadata': self.metadata
        }


@dataclass
class OptimizationPlan:
    """优化方案"""
    plan_id: str
    strategy: str
    description: str
    expected_improvement: Dict[str, float]  # {metric: improvement_value}
    risk_level: str                          # low/medium/high/critical
    implementation_cost: int                 # 1-10
    time_estimate_hours: float
    prerequisites: List[str] = field(default_factory=list)
    side_effects: List[str] = field(default_factory=list)
    success_probability: float = 0.7
    priority_score: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            'plan_id': self.plan_id,
            'strategy': self.strategy,
            'description': self.description,
            'expected_improvement': self.expected_improvement,
            'risk_level': self.risk_level,
            'implementation_cost': self.implementation_cost,
            'time_estimate_hours': self.time_estimate_hours,
            'prerequisites': self.prerequisites,
            'side_effects': self.side_effects,
            'success_probability': round(self.success_probability, 3),
            'priority_score': round(self.priority_score, 3)
        }


@dataclass
class TaskWithPriority:
    """带优先级的任务"""
    task_id: str
    title: str
    description: str
    value_score: float          # 业务价值分 (0-100)
    cost_score: float           # 实施成本分 (0-100, 越低越好)
    risk_score: float           # 技术风险分 (0-100, 越低越好)
    dependency_score: float     # 依赖复杂度分 (0-100, 越低越好)
    final_priority: float       # 最终优先级分 (0-100)
    rank: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            'task_id': self.task_id,
            'title': self.title,
            'description': self.description,
            'value_score': round(self.value_score, 2),
            'cost_score': round(self.cost_score, 2),
            'risk_score': round(self.risk_score, 2),
            'dependency_score': round(self.dependency_score, 2),
            'final_priority': round(self.final_priority, 2),
            'rank': self.rank,
            'metadata': self.metadata
        }


class IntelligentProblemPredictor:
    """
    基于历史数据的智能问题预测器

    使用时序分析、模式识别、频率统计等技术预测潜在问题。

    核心能力:
    1. 频率模式识别 - 分析历史问题的出现频率
    2. 时间序列趋势分析 - 识别问题的时间趋势
    3. 关联规则挖掘 - 发现问题之间的关联关系
    4. 周期性检测 - 识别周期性问题模式
    """

    def __init__(self):
        self.logger = logging.getLogger('IntelligentProblemPredictor')
        self.pattern_cache: Dict[str, Any] = {}
        self.historical_data: List[Dict[str, Any]] = []

    def predict_issues(
        self,
        historical_data: List[Dict[str, Any]],
        time_window_days: int = 30,
        min_confidence: float = 0.3
    ) -> List[PredictedIssue]:
        """
        预测未来可能出现的问题

        Args:
            historical_data: 历史问题数据列表
                每个元素应包含: {
                    'issue_type': str,
                    'description': str,
                    'timestamp': str (ISO格式),
                    'severity': str,
                    'resolved': bool,
                    'resolution_time_hours': float,
                    'affected_modules': list,
                    'root_cause': str
                }
            time_window_days: 分析的时间窗口（天）
            min_confidence: 最低置信度阈值

        Returns:
            预测的问题列表，包含概率和置信度
        """
        if not historical_data:
            self.logger.warning("历史数据为空，无法进行预测")
            return []

        self.historical_data = historical_data
        predictions = []

        cutoff_date = datetime.now() - timedelta(days=time_window_days)

        frequency_analysis = self._analyze_frequency(historical_data, cutoff_date)
        trend_analysis = self._analyze_trends(historical_data, time_window_days)
        pattern_analysis = self.analyze_patterns(historical_data)
        cyclical_analysis = self._detect_cyclical_patterns(historical_data)

        issue_types = set(item.get('issue_type', '') for item in historical_data if item.get('issue_type'))

        for issue_type in issue_types:
            type_predictions = self._predict_for_issue_type(
                issue_type=issue_type,
                frequency_data=frequency_analysis.get(issue_type, {}),
                trend_data=trend_analysis.get(issue_type, {}),
                pattern_data=pattern_analysis.get(issue_type, {}),
                cyclical_data=cyclical_analysis.get(issue_type, {}),
                total_issues=len(historical_data),
                time_window=time_window_days
            )

            for pred in type_predictions:
                if pred.confidence >= min_confidence:
                    predictions.append(pred)

        predictions.sort(key=lambda x: (-x.probability, -x.confidence))

        self.logger.info(f"完成问题预测，共生成 {len(predictions)} 个预测")
        return predictions

    def _analyze_frequency(
        self,
        data: List[Dict[str, Any]],
        cutoff_date: datetime
    ) -> Dict[str, Dict[str, Any]]:
        """分析问题频率"""
        recent_issues = []
        older_issues = []

        for item in data:
            try:
                ts = datetime.fromisoformat(item.get('timestamp', datetime.now().isoformat()))
                if ts >= cutoff_date:
                    recent_issues.append(item)
                else:
                    older_issues.append(item)
            except (ValueError, TypeError):
                recent_issues.append(item)

        freq_result = {}
        all_issues = recent_issues + older_issues

        type_counts = Counter(item.get('issue_type', 'unknown') for item in all_issues)
        recent_counts = Counter(item.get('issue_type', 'unknown') for item in recent_issues)

        for issue_type in type_counts.keys():
            total_count = type_counts[issue_type]
            recent_count = recent_counts.get(issue_type, 0)
            older_count = total_count - recent_count

            growth_rate = 0.0
            if older_count > 0:
                growth_rate = (recent_count - older_count) / older_count

            avg_interval = 0.0
            if total_count > 0:
                avg_interval = 30.0 / total_count  # 平均每30天出现的次数

            freq_result[issue_type] = {
                'total_count': total_count,
                'recent_count': recent_count,
                'growth_rate': growth_rate,
                'avg_frequency': avg_interval,
                'is_increasing': growth_rate > 0.1
            }

        return freq_result

    def _analyze_trends(
        self,
        data: List[Dict[str, Any]],
        window_days: int
    ) -> Dict[str, Dict[str, Any]]:
        """分析时间序列趋势"""
        trends = {}

        sorted_data = sorted(
            [item for item in data if item.get('timestamp')],
            key=lambda x: x.get('timestamp', '')
        )

        buckets = defaultdict(list)
        bucket_size = max(1, window_days // 6)  # 分成6个时间段

        for item in sorted_data:
            try:
                ts = datetime.fromisoformat(item['timestamp'])
                days_ago = (datetime.now() - ts).days
                bucket_idx = days_ago // bucket_size
                buckets[bucket_idx].append(item)
            except (ValueError, TypeError):
                continue

        for issue_type in set(item.get('issue_type', '') for item in data):
            counts_per_bucket = []
            for idx in range(6):
                bucket_items = buckets[idx]
                count = sum(1 for item in bucket_items if item.get('issue_type') == issue_type)
                counts_per_bucket.append(count)

            if len(counts_per_bucket) >= 2:
                slope = self._calculate_slope(counts_per_bucket)
                variance = self._calculate_variance(counts_per_bucket)
                acceleration = self._calculate_acceleration(counts_per_bucket)
            else:
                slope = 0.0
                variance = 0.0
                acceleration = 0.0

            trends[issue_type] = {
                'slope': slope,
                'variance': variance,
                'acceleration': acceleration,
                'trend_direction': 'increasing' if slope > 0.5 else ('decreasing' if slope < -0.5 else 'stable'),
                'counts_history': counts_per_bucket
            }

        return trends

    def _detect_cyclical_patterns(
        self,
        data: List[Dict[str, Any]]
    ) -> Dict[str, Dict[str, Any]]:
        """检测周期性模式"""
        cyclical = {}

        day_of_week_counts = defaultdict(lambda: defaultdict(int))
        hour_counts = defaultdict(lambda: defaultdict(int))

        for item in data:
            try:
                ts = datetime.fromisoformat(item.get('timestamp', ''))
                issue_type = item.get('issue_type', '')
                day_of_week_counts[issue_type][ts.weekday()] += 1
                hour_counts[issue_type][ts.hour] += 1
            except (ValueError, TypeError):
                continue

        for issue_type in day_of_week_counts.keys():
            dow_data = day_of_week_counts[issue_type]
            hour_data = hour_counts[issue_type]

            dow_variance = self._calculate_variance(list(dow_data.values()))
            hour_variance = self._calculate_variance(list(hour_data.values()))

            peak_day = max(dow_data.items(), key=lambda x: x[1])[0] if dow_data else 0
            peak_hour = max(hour_data.items(), key=lambda x: x[1])[0] if hour_data else 0

            is_cyclical_dow = dow_variance > 2.0 and max(dow_data.values()) > 2 * (sum(dow_data.values()) / 7)
            is_cyclical_hour = hour_variance > 2.0 and max(hour_data.values()) > 2 * (sum(hour_data.values()) / 24)

            cyclical[issue_type] = {
                'has_daily_pattern': is_cyclical_hour,
                'has_weekly_pattern': is_cyclical_dow,
                'peak_day': peak_day,
                'peak_hour': peak_hour,
                'day_variance': dow_variance,
                'hour_variance': hour_variance
            }

        return cyclical

    def _predict_for_issue_type(
        self,
        issue_type: str,
        frequency_data: Dict[str, Any],
        trend_data: Dict[str, Any],
        pattern_data: Dict[str, Any],
        cyclical_data: Dict[str, Any],
        total_issues: int,
        time_window: int
    ) -> List[PredictedIssue]:
        """为特定问题类型生成预测"""
        predictions = []

        base_prob = frequency_data.get('avg_frequency', 0) / max(1, time_window)

        growth_factor = 1.0 + max(0, frequency_data.get('growth_rate', 0))
        trend_factor = 1.0 + max(0, trend_data.get('slope', 0)) * 0.1

        probability = min(0.95, base_prob * growth_factor * trend_factor)

        confidence_components = []
        confidence_components.append(min(1.0, frequency_data.get('total_count', 0) / 10))
        if abs(trend_data.get('slope', 0)) > 0.5:
            confidence_components.append(0.8)
        if pattern_data.get('strong_associations'):
            confidence_components.append(0.7)
        if cyclical_data.get('has_daily_pattern') or cyclical_data.get('has_weekly_pattern'):
            confidence_components.append(0.6)

        confidence = sum(confidence_components) / len(confidence_components) if confidence_components else 0.3

        severity = self._infer_severity(issue_type, frequency_data, pattern_data)

        predicted_time = datetime.now() + timedelta(days=int(1 / max(probability, 0.01)))

        prevention_suggestions = self._generate_prevention_suggestions(
            issue_type,
            frequency_data,
            pattern_data
        )

        evidence = []
        if frequency_data.get('total_count', 0) > 0:
            evidence.append(f"历史出现{frequency_data['total_count']}次")
        if frequency_data.get('is_increasing'):
            evidence.append(f"呈增长趋势（增长率{frequency_data['growth_rate']:.1%}）")
        if trend_data.get('trend_direction') == 'increasing':
            evidence.append("时间序列显示上升趋势")

        prediction = PredictedIssue(
            issue_id=f"PRED-{issue_type.upper()}-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            issue_type=issue_type,
            description=f"预测可能出现{issue_type}类型问题",
            probability=probability,
            confidence=confidence,
            severity=severity,
            predicted_time=predicted_time,
            related_patterns=list(pattern_data.get('associated_patterns', [])),
            historical_evidence=evidence,
            suggested_prevention=prevention_suggestions
        )
        predictions.append(prediction)

        return predictions

    def analyze_patterns(self, issues: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
        """
        分析问题模式和关联规则

        Args:
            issues: 问题列表

        Returns:
            模式分析结果字典
        """
        patterns = {}

        co_occurrence = defaultdict(int)
        type_module_map = defaultdict(set)
        severity_by_type = defaultdict(list)

        for i, issue1 in enumerate(issues):
            type1 = issue1.get('issue_type', '')
            modules1 = set(issue1.get('affected_modules', []))
            severity_by_type[type1].append(issue1.get('severity', 'medium'))

            for module in modules1:
                type_module_map[type1].add(module)

            for j, issue2 in enumerate(issues[i+1:], i+1):
                type2 = issue2.get('issue_type', '')

                try:
                    ts1 = datetime.fromisoformat(issue1.get('timestamp', ''))
                    ts2 = datetime.fromisoformat(issue2.get('timestamp', ''))

                    if abs((ts1 - ts2).days) <= 7:
                        pair = tuple(sorted([type1, type2]))
                        co_occurrence[pair] += 1
                except (ValueError, TypeError):
                    continue

        strong_associations = [
            {'types': list(pair), 'co_occurrence_count': count}
            for pair, count in co_occurrence.most_common(10)
            if count >= 2
        ]

        for issue_type in set(i.get('issue_type', '') for i in issues):
            severities = severity_by_type.get(issue_type, [])
            most_common_severity = Counter(severities).most_common(1)[0][0] if severities else 'medium'
            associated_modules = list(type_module_map.get(issue_type, []))[:5]
            associated_patterns = [
                item['types'][1] if item['types'][0] == issue_type else item['types'][0]
                for item in strong_associations
                if issue_type in item['types']
            ]

            patterns[issue_type] = {
                'most_common_severity': most_common_severity,
                'associated_modules': associated_modules,
                'strong_associations': [a for a in strong_associations if issue_type in a['types']],
                'associated_patterns': associated_patterns,
                'total_occurrences': len(severities)
            }

        return patterns

    def _calculate_slope(self, values: List[float]) -> float:
        """计算线性回归斜率"""
        n = len(values)
        if n < 2:
            return 0.0

        x_mean = (n - 1) / 2.0
        y_mean = sum(values) / n

        numerator = sum((i - x_mean) * (values[i] - y_mean) for i in range(n))
        denominator = sum((i - x_mean) ** 2 for i in range(n))

        return numerator / denominator if denominator != 0 else 0.0

    def _calculate_variance(self, values: List[float]) -> float:
        """计算方差"""
        if not values:
            return 0.0
        mean = sum(values) / len(values)
        return sum((x - mean) ** 2 for x in values) / len(values)

    def _calculate_acceleration(self, values: List[float]) -> float:
        """计算加速度（二阶导数近似）"""
        if len(values) < 3:
            return 0.0

        first_derivatives = [values[i+1] - values[i] for i in range(len(values)-1)]
        second_derivatives = [first_derivatives[i+1] - first_derivatives[i] for i in range(len(first_derivatives)-1)]

        return sum(second_derivatives) / len(second_derivatives) if second_derivatives else 0.0

    def _infer_severity(
        self,
        issue_type: str,
        frequency_data: Dict[str, Any],
        pattern_data: Dict[str, Any]
    ) -> IssueSeverity:
        """推断问题严重程度"""
        severity_keywords = {
            'crritical': ['security', 'memory_leak', 'data_loss', 'corruption'],
            'high': ['performance', 'crash', 'timeout', 'error'],
            'medium': ['warning', 'deprecation', 'compatibility'],
            'low': ['style', 'cosmetic', 'documentation']
        }

        issue_lower = issue_type.lower()

        for severity, keywords in severity_keywords.items():
            if any(kw in issue_lower for kw in keywords):
                return IssueSeverity(severity)

        if frequency_data.get('total_count', 0) > 10:
            return IssueSeverity.HIGH
        elif frequency_data.get('total_count', 0) > 5:
            return IssueSeverity.MEDIUM

        return IssueSeverity.LOW

    def _generate_prevention_suggestions(
        self,
        issue_type: str,
        frequency_data: Dict[str, Any],
        pattern_data: Dict[str, Any]
    ) -> str:
        """生成预防建议"""

        suggestions = []

        if frequency_data.get('is_increasing'):
            suggestions.append("建议增加监控频率并设置预警阈值")

        if pattern_data.get('associated_modules'):
            modules = ', '.join(pattern_data['associated_modules'][:3])
            suggestions.append(f"重点关注模块: {modules}")

        if pattern_data.get('strong_associations'):
            assoc = pattern_data['strong_associations'][0]['types']
            suggestions.append(f"注意与{assoc[1] if len(assoc) > 1 else assoc[0]}类问题的关联")

        prevention_templates = {
            'error': "建议加强错误处理和日志记录",
            'performance': "建议进行性能测试和优化",
            'security': "建议进行安全审计和漏洞扫描",
            'memory': "建议检查内存泄漏和资源管理",
            'default': "建议定期检查相关代码和配置"
        }

        template_key = next(
            (k for k in prevention_templates if k in issue_type.lower()),
            'default'
        )
        suggestions.append(prevention_templates[template_key])

        return '; '.join(suggestions) if suggestions else "建议持续监控"

    def generate_prediction_report(
        self,
        predictions: List[PredictedIssue],
        output_path: Optional[str] = None
    ) -> str:
        """生成预测报告"""
        lines = [
            "# 智能问题预测报告",
            "",
            f"**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"**预测数量**: {len(predictions)}",
            "",
            "## 预测摘要",
            "",
        ]

        high_risk = [p for p in predictions if p.severity in [IssueSeverity.CRITICAL, IssueSeverity.HIGH]]
        medium_risk = [p for p in predictions if p.severity == IssueSeverity.MEDIUM]
        low_risk = [p for p in predictions if p.severity == IssueSeverity.LOW]

        lines.extend([
            f"- 🔴 高风险预测: {len(high_risk)} 个",
            f"- 🟡 中等风险预测: {len(medium_risk)} 个",
            f"- 🟢 低风险预测: {len(low_risk)} 个",
            "",
            "## 详细预测列表",
            "",
        ])

        for i, pred in enumerate(predictions[:20], 1):
            severity_icon = {
                IssueSeverity.CRITICAL: "🔴🔴",
                IssueSeverity.HIGH: "🔴",
                IssueSeverity.MEDIUM: "🟡",
                IssueSeverity.LOW: "🟢"
            }.get(pred.severity, "⚪")

            lines.extend([
                f"### {i}. {pred.issue_type} [{severity_icon}]",
                f"- **描述**: {pred.description}",
                f"- **概率**: {pred.probability:.1%}",
                f"- **置信度**: {pred.confidence:.1%}",
                f"- **预计时间**: {pred.predicted_time.strftime('%Y-%m-%d %H:%M')}",
                f"- **预防建议**: {pred.suggested_prevention}",
                "",
            ])

        report = '\n'.join(lines)

        if output_path:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(report)

        return report


class MultiStrategyOptimizer:
    """
    多策略协同优化方案生成器

    同时应用多种优化策略，选择最优组合。
    支持策略协同效应评估和风险评估。
    """

    STRATEGIES = ['refactor', 'optimize', 'restructure', 'consolidate']

    STRATEGY_DETAILS = {
        'refactor': {
            'desc': '代码重构',
            'applicable_to': ['code_quality', 'complexity', 'maintainability'],
            'cost_range': (3, 7),
            'risk_range': (2, 5),
            'improvement_potential': {'code_quality': 0.3, 'maintainability': 0.4}
        },
        'optimize': {
            'desc': '性能优化',
            'applicable_to': ['performance', 'speed', 'resource_usage'],
            'cost_range': (4, 8),
            'risk_range': (3, 6),
            'improvement_potential': {'performance': 0.5, 'speed': 0.4}
        },
        'restructure': {
            'desc': '架构重组',
            'applicable_to': ['architecture', 'scalability', 'flexibility'],
            'cost_range': (6, 9),
            'risk_range': (5, 8),
            'improvement_potential': {'architecture': 0.5, 'scalability': 0.4}
        },
        'consolidate': {
            'desc': '合并整合',
            'applicable_to': ['duplication', 'code_size', 'complexity'],
            'cost_range': (2, 5),
            'risk_range': (1, 4),
            'improvement_potential': {'code_size': 0.4, 'complexity': 0.3}
        }
    }

    SYNERGY_MATRIX = {
        ('refactor', 'optimize'): 1.2,
        ('refactor', 'restructure'): 1.3,
        ('refactor', 'consolidate'): 1.15,
        ('optimize', 'restructure'): 1.25,
        ('optimize', 'consolidate'): 1.1,
        ('restructure', 'consolidate'): 1.2,
    }

    def __init__(self):
        self.logger = logging.getLogger('MultiStrategyOptimizer')
        self.strategy_history: List[Dict[str, Any]] = []

    def generate_optimization_plan(
        self,
        problem: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None,
        max_plans: int = 4
    ) -> List[OptimizationPlan]:
        """
        为给定问题生成多种优化方案

        Args:
            problem: 问题描述字典
                应包含: {
                    'problem_type': str,
                    'description': str,
                    'severity': str,
                    'affected_metrics': list,
                    'current_state': dict,
                    'target_state': dict
                }
            context: 上下文信息（可选）
            max_plans: 最大生成方案数

        Returns:
            优化方案列表，每个方案包含策略、预期效果、风险评估
        """
        plans = []
        context = context or {}
        problem_type = problem.get('problem_type', 'general')

        applicable_strategies = self._select_applicable_strategies(problem, context)

        for strategy in applicable_strategies[:max_plans]:
            plan = self._apply_strategy(strategy, problem, context)
            if plan:
                plans.append(plan)

        if len(plans) > 1:
            plans = self._evaluate_synergy(plans)

        plans.sort(key=lambda p: p.priority_score, reverse=True)

        for rank, plan in enumerate(plans, 1):
            plan.rank = rank

        self.logger.info(f"为问题 '{problem_type}' 生成了 {len(plans)} 个优化方案")
        return plans

    def _select_applicable_strategies(
        self,
        problem: Dict[str, Any],
        context: Dict[str, Any]
    ) -> List[str]:
        """选择适用的策略"""
        applicable = []
        problem_type = problem.get('problem_type', '').lower()
        affected_metrics = problem.get('affected_metrics', [])
        severity = problem.get('severity', 'medium').lower()

        for strategy, details in self.STRATEGY_DETAILS.items():
            is_applicable = any(
                metric in details['applicable_to']
                for metric in affected_metrics + [problem_type]
            )

            if is_applicable or problem_type == 'general':
                cost_ok = True
                risk_ok = True

                if context.get('budget_limit'):
                    cost_ok = details['cost_range'][0] <= context['budget_limit']
                if context.get('max_risk_allowed'):
                    risk_ok = details['risk_range'][1] <= context['max_risk_allowed'] * 10

                if cost_ok and risk_ok:
                    applicable.append(strategy)

        if not applicable:
            applicable = ['refactor', 'optimize']

        return applicable

    def _apply_strategy(
        self,
        strategy: str,
        problem: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Optional[OptimizationPlan]:
        """应用特定策略生成优化方案"""
        details = self.STRATEGY_DETAILS.get(strategy)
        if not details:
            return None

        problem_type = problem.get('problem_type', 'unknown')
        base_cost = random.randint(*details['cost_range'])
        base_risk = random.randint(*details['risk_range'])

        if context.get('team_experience') == 'senior':
            base_cost = max(1, base_cost - 2)
            base_risk = max(1, base_risk - 1)

        expected_improvement = {}
        for metric, potential in details['improvement_potential'].items():
            if metric in problem.get('affected_metrics', []) or problem_type == 'general':
                variance = random.uniform(-0.1, 0.1)
                expected_improvement[metric] = round(max(0.1, potential + variance), 2)

        time_hours = base_cost * 2 + len(expected_improvement) * 0.5

        risk_level = self._classify_risk(base_risk)

        success_prob = self._estimate_success_probability(
            strategy=strategy,
            cost=base_cost,
            risk=base_risk,
            context=context
        )

        prerequisites = self._determine_prerequisites(strategy, problem)
        side_effects = self._identify_side_effects(strategy, problem)

        plan = OptimizationPlan(
            plan_id=f"PLAN-{strategy.upper()}-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            strategy=strategy,
            description=f"{details['desc']}: {problem.get('description', '')[:50]}",
            expected_improvement=expected_improvement,
            risk_level=risk_level,
            implementation_cost=base_cost,
            time_estimate_hours=time_hours,
            prerequisites=prerequisites,
            side_effects=side_effects,
            success_probability=success_prob
        )

        plan.priority_score = self._calculate_plan_priority(plan, context)

        return plan

    def _evaluate_synergy(self, plans: List[OptimizationPlan]) -> List[OptimizationPlan]:
        """评估策略间的协同效应"""
        for i, plan1 in enumerate(plans):
            synergy_bonus = 0.0
            for j, plan2 in enumerate(plans):
                if i != j:
                    key = tuple(sorted([plan1.strategy, plan2.strategy]))
                    synergy = self.SYNERGY_MATRIX.get(key, 1.0)
                    synergy_bonus += (synergy - 1.0) * 0.1

            plan1.priority_score *= (1 + synergy_bonus)

        return plans

    def _classify_risk(self, risk_score: int) -> str:
        """分类风险等级"""
        if risk_score <= 2:
            return 'low'
        elif risk_score <= 4:
            return 'medium'
        elif risk_score <= 6:
            return 'high'
        else:
            return 'critical'

    def _estimate_success_probability(
        self,
        strategy: str,
        cost: int,
        risk: int,
        context: Dict[str, Any]
    ) -> float:
        """估算成功概率"""
        base_prob = 0.7

        cost_factor = 1.0 - (cost / 100.0)
        risk_factor = 1.0 - (risk / 100.0)

        experience_bonus = 0.0
        if context.get('team_experience') == 'senior':
            experience_bonus = 0.1
        elif context.get('team_experience') == 'junior':
            experience_bonus = -0.1

        tooling_bonus = 0.05 if context.get('has_testing_framework') else 0.0
        tooling_bonus += 0.05 if context.get('has_ci_cd') else 0.0

        success_prob = base_prob * cost_factor * risk_factor + experience_bonus + tooling_bonus

        return max(0.3, min(0.95, success_prob))

    def _determine_prerequisites(self, strategy: str, problem: Dict[str, Any]) -> List[str]:
        """确定前置条件"""
        prereqs = {
            'refactor': ['现有测试覆盖', '代码理解文档'],
            'optimize': ['性能基线数据', '监控工具就绪'],
            'restructure': ['架构文档', '影响范围分析完成'],
            'consolidate': ['重复代码清单', '依赖关系图']
        }
        return prereqs.get(strategy, [])

    def _identify_side_effects(self, strategy: str, problem: Dict[str, Any]) -> List[str]:
        """识别潜在副作用"""
        effects = {
            'refactor': ['可能引入新bug', 'API可能变化'],
            'optimize': ['可读性可能降低', '调试难度增加'],
            'restructure': ['学习成本增加', '迁移期间不稳定'],
            'consolidate': ['耦合度可能增加', '单一职责可能受损']
        }
        return effects.get(strategy, [])

    def _calculate_plan_priority(
        self,
        plan: OptimizationPlan,
        context: Dict[str, Any]
    ) -> float:
        """计算方案优先级得分"""
        improvement_score = sum(plan.expected_improvement.values()) * 25
        cost_penalty = plan.implementation_cost * 2
        risk_penalty = {'low': 0, 'medium': 5, 'high': 10, 'critical': 20}.get(plan.risk_level, 5)
        success_bonus = plan.success_probability * 20

        urgency_multiplier = 1.0
        if context.get('urgency') == 'high':
            urgency_multiplier = 1.2
        elif context.get('urgency') == 'critical':
            urgency_multiplier = 1.4

        priority = (improvement_score - cost_penalty - risk_penalty + success_bonus) * urgency_multiplier

        return max(0, min(100, priority))

    def generate_optimization_report(
        self,
        plans: List[OptimizationPlan],
        output_path: Optional[str] = None
    ) -> str:
        """生成优化方案报告"""
        lines = [
            "# 多策略优化方案报告",
            "",
            f"**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"**方案数量**: {len(plans)}",
            "",
            "## 方案对比",
            "",
            "| 排名 | 策略 | 描述 | 优先级 | 成功率 | 风险 | 成本 |",
            "|------|------|------|--------|--------|------|------|",
        ]

        for plan in plans:
            lines.append(
                f"| {plan.rank} | {plan.strategy} | {plan.description[:30]}... "
                f"| {plan.priority_score:.1f} | {plan.success_probability:.0%} "
                f"| {plan.risk_level} | {plan.implementation_cost}/10 |"
            )

        lines.extend(["", "## 详细方案", ""])

        for i, plan in enumerate(plans, 1):
            improvements_str = ', '.join([
                f"{k}: +{v:.0%}" for k, v in plan.expected_improvement.items()
            ])

            lines.extend([
                f"### 方案{i}: {plan.strategy} ({self.STRATEGY_DETAILS[plan.strategy]['desc']})",
                f"- **描述**: {plan.description}",
                f"- **预期改进**: {improvements_str}",
                f"- **成功概率**: {plan.success_probability:.0%}",
                f"- **实施成本**: {plan.implementation_cost}/10",
                f"- **预估工时**: {plan.time_estimate_hours:.1f}小时",
                f"- **风险等级**: {plan.risk_level}",
                "- **前置条件**:",
            ])

            for prereq in plan.prerequisites:
                lines.append(f"  - {prereq}")

            if plan.side_effects:
                lines.append("- **潜在副作用**:")
                for effect in plan.side_effects:
                    lines.append(f"  - ⚠️ {effect}")

            lines.append("")

        report = '\n'.join(lines)

        if output_path:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(report)

        return report


class PrioritySorter:
    """
    四维优先级排序器

    基于 价值/成本/风险/依赖 四维度进行综合排序，
    支持动态权重调整和多目标优化。
    """

    DEFAULT_WEIGHTS = {
        'value_weight': 0.40,         # 业务价值权重
        'cost_weight': 0.25,          # 实施成本权重（越低越好）
        'risk_weight': 0.20,          # 技术风险权重（越低越好）
        'dependency_weight': 0.15     # 依赖复杂度权重（越低越好）
    }

    def __init__(
        self,
        custom_weights: Optional[Dict[str, float]] = None,
        normalize: bool = True
    ):
        self.weights = {**self.DEFAULT_WEIGHTS, **(custom_weights or {})}
        self.normalize = normalize
        self.logger = logging.getLogger('PrioritySorter')

        weight_sum = sum(self.weights.values())
        if abs(weight_sum - 1.0) > 0.01:
            self.logger.warning(f"权重总和不等于1.0 ({weight_sum})，自动归一化")
            for k in self.weights:
                self.weights[k] /= weight_sum

    def calculate_priority(self, task: Dict[str, Any]) -> float:
        """
        计算单个任务的优先级分数

        四维评分模型:
        - value_score: 业务价值 (0-100)，越高越好
        - cost_score: 实施成本 (0-100)，越低越好
        - risk_score: 技术风险 (0-100)，越低越好
        - dependency_score: 依赖复杂度 (0-100)，越低越好

        Args:
            task: 任务字典，应包含上述四个维度字段

        Returns:
            优先级分数 (0-100)
        """
        value = task.get('value', task.get('value_score', 50))
        cost = task.get('cost', task.get('cost_score', 50))
        risk = task.get('risk', task.get('risk_score', 50))
        dependency = task.get('dependency_complexity', task.get('dependency_score', 50))

        value_score = value * self.weights['value_weight']
        cost_score = (100 - cost) * self.weights['cost_weight']
        risk_score = (100 - risk) * self.weights['risk_weight']
        dep_score = (100 - dependency) * self.weights['dependency_weight']

        raw_score = value_score + cost_score + risk_score + dep_score

        if self.normalize:
            normalized_score = max(0, min(100, raw_score))
            return round(normalized_score, 2)

        return round(raw_score, 2)

    def sort_tasks(
        self,
        tasks: List[Dict[str, Any]],
        descending: bool = True
    ) -> List[TaskWithPriority]:
        """
        对任务列表进行优先级排序

        Args:
            tasks: 任务列表
            descending: 是否降序排列（高优先级在前）

        Returns:
            排序后的带优先级信息任务列表
        """
        scored_tasks = []

        for task in tasks:
            task_id = task.get('task_id', task.get('id', f"TASK-{len(scored_tasks)+1}"))
            priority = self.calculate_priority(task)

            scored_task = TaskWithPriority(
                task_id=task_id,
                title=task.get('title', task.get('name', '')),
                description=task.get('description', ''),
                value_score=task.get('value', task.get('value_score', 50)),
                cost_score=task.get('cost', task.get('cost_score', 50)),
                risk_score=task.get('risk', task.get('risk_score', 50)),
                dependency_score=task.get('dependency_complexity', task.get('dependency_score', 50)),
                final_priority=priority,
                metadata={k: v for k, v in task.items() if k not in [
                    'task_id', 'id', 'title', 'name', 'description',
                    'value', 'value_score', 'cost', 'cost_score',
                    'risk', 'risk_score', 'dependency_complexity', 'dependency_score'
                ]}
            )
            scored_tasks.append(scored_task)

        scored_tasks.sort(key=lambda t: t.final_priority, reverse=descending)

        for rank, task in enumerate(scored_tasks, 1):
            task.rank = rank

        self.logger.info(f"已完成 {len(tasks)} 个任务的优先级排序")
        return scored_tasks

    def batch_calculate_priorities(
        self,
        tasks: List[Dict[str, Any]]
    ) -> Dict[str, float]:
        """批量计算任务优先级"""
        return {task.get('task_id', task.get('id', f"TASK-{i}")): self.calculate_priority(task)
                for i, task in enumerate(tasks)}

    def adjust_weights_for_context(
        self,
        context: str,
        intensity: float = 0.2
    ) -> Dict[str, float]:
        """
        根据上下文动态调整权重

        Args:
            context: 上下文字符串 ('urgent', 'stable', 'experimental', etc.)
            intensity: 调整强度 (0-1)

        Returns:
            调整后的权重字典
        """
        new_weights = self.weights.copy()

        adjustments = {
            'urgent': {'value_weight': intensity, 'cost_weight': -intensity * 0.5},
            'stable': {'risk_weight': intensity, 'dependency_weight': intensity * 0.5},
            'experimental': {'risk_weight': -intensity * 0.5, 'value_weight': intensity * 0.5},
            'cost_sensitive': {'cost_weight': intensity, 'value_weight': -intensity * 0.3},
            'quality_focus': {'risk_weight': intensity, 'cost_weight': intensity * 0.3}
        }

        adj = adjustments.get(context, {})
        for key, delta in adj.items():
            new_weights[key] = max(0.05, min(0.6, new_weights[key] + delta))

        total = sum(new_weights.values())
        for key in new_weights:
            new_weights[key] /= total

        self.weights = new_weights
        return new_weights

    def generate_sorting_report(
        self,
        sorted_tasks: List[TaskWithPriority],
        output_path: Optional[str] = None
    ) -> str:
        """生成排序报告"""
        lines = [
            "# 任务优先级排序报告",
            "",
            f"**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"**任务总数**: {len(sorted_tasks)}",
            "",
            "## 权重配置",
            "",
            "| 维度 | 权重 | 说明 |",
            "|------|------|------|",
            f"| 业务价值 | {self.weights['value_weight']:.0%} | 越高越好 |",
            f"| 实施成本 | {self.weights['cost_weight']:.0%} | 越低越好 |",
            f"| 技术风险 | {self.weights['risk_weight']:.0%} | 越低越好 |",
            f"| 依赖复杂度 | {self.weights['dependency_weight']:.0%} | 越低越好 |",
            "",
            "## 排序结果",
            "",
            "| 排名 | 任务ID | 标题 | 价值 | 成本 | 风险 | 依赖 | 总分 |",
            "|------|--------|------|------|------|------|------|------|",
        ]

        for task in sorted_tasks[:20]:
            lines.append(
                f"| {task.rank} | {task.task_id} | {task.title[:25]} "
                f"| {task.value_score:.0f} | {task.cost_score:.0f} "
                f"| {task.risk_score:.0f} | {task.dependency_score:.0f} "
                f"| {task.final_priority:.1f} |"
            )

        if len(sorted_tasks) > 20:
            lines.append(f"\n*... 还有 {len(sorted_tasks) - 20} 个任务 ...*")

        top_tasks = sorted_tasks[:5]
        if top_tasks:
            avg_priority = sum(t.final_priority for t in top_tasks) / len(top_tasks)
            lines.extend([
                "",
                "## 统计摘要",
                "",
                f"- **Top 5 平均分**: {avg_priority:.1f}",
                f"- **最高分**: {sorted_tasks[0].final_priority:.1f} ({sorted_tasks[0].title})",
                f"- **最低分**: {sorted_tasks[-1].final_priority:.1f} ({sorted_tasks[-1].title})",
            ])

        report = '\n'.join(lines)

        if output_path:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(report)

        return report


if __name__ == '__main__':
    print("智能自迭代系统模块已加载")
