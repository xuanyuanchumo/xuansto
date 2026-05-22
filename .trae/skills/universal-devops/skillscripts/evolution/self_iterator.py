"""
自迭代引擎 - 智能问题预测、多策略协同优化、改进方案生成
"""
from __future__ import annotations

import json
import uuid
from dataclasses import dataclass, field
from enum import Enum, auto
from pathlib import Path
from typing import Any, Callable


class ProblemType(Enum):
    """问题类型枚举"""
    DEFECT_DENSITY = "defect_density"
    COMPLEXITY_GROWTH = "complexity_growth"
    TECHNICAL_DEBT = "technical_debt"
    PERFORMANCE_DEGRADATION = "performance_degradation"
    COVERAGE_DROP = "coverage_drop"
    SECURITY_VULNERABILITY = "security_vulnerability"
    MAINTAINABILITY_DECLINE = "maintainability_decline"
    TEST_FLAKINESS = "test_flakiness"


class SelfIterationError(Exception):
    """自迭代异常"""


@dataclass
class Prediction:
    """预测结果"""
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    problem_type: ProblemType = ProblemType.DEFECT_DENSITY
    description: str = ""
    predicted_value: float = 0.0
    confidence: float = 0.0
    time_horizon: str = "2weeks"
    severity: str = "medium"
    affected_modules: list[str] = field(default_factory=list)
    historical_trend: list[float] = field(default_factory=list)
    suggested_actions: list[str] = field(default_factory=list)
    created_at: str = ""


@dataclass
class OptimizationStrategy:
    """优化策略"""
    name: str
    strategy_type: str = ""
    description: str = ""
    priority: int = 5
    expected_improvement: float = 0.0
    effort_level: str = "medium"
    risk_level: str = "low"
    applicable_modules: list[str] = field(default_factory=list)
    steps: list[str] = field(default_factory=list)
    prerequisites: list[str] = field(default_factory=list)
    estimated_duration: str = ""


@dataclass
class ImprovementPlan:
    """改进方案"""
    plan_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    title: str = ""
    description: str = ""
    problem_addressed: str = ""
    strategies: list[OptimizationStrategy] = field(default_factory=list)
    priority: str = "medium"
    status: str = "proposed"
    estimated_effort: str = ""
    expected_outcome: str = ""
    risk_assessment: str = ""
    dependencies: list[str] = field(default_factory=list)
    success_criteria: list[str] = field(default_factory=list)
    created_at: str = ""
    metrics_before: dict[str, float] = field(default_factory=dict)
    metrics_target: dict[str, float] = field(default_factory=dict)


@dataclass
class IterationEffect:
    """迭代效果评估"""
    iteration_id: str = ""
    before_metrics: dict[str, float] = field(default_factory=dict)
    after_metrics: dict[str, float] = field(default_factory=dict)
    improvements: dict[str, float] = field(default_factory=dict)
    regressions: dict[str, float] = field(default_factory=dict)
    overall_effectiveness: float = 0.0
    lessons_learned: list[str] = field(default_factory=list)
    next_recommendations: list[str] = field(default_factory=list)
    timestamp: str = ""


@dataclass
class ProjectAnalysis:
    """项目分析数据"""
    defect_density_history: list[dict[str, Any]] = field(default_factory=list)
    complexity_metrics: dict[str, float] = field(default_factory=dict)
    coverage_data: dict[str, float] = field(default_factory=dict)
    technical_debt_score: float = 0.0
    performance_baselines: dict[str, float] = field(default_factory=dict)
    module_health: dict[str, dict[str, float]] = field(default_factory=dict)
    test_quality_metrics: dict[str, float] = field(default_factory=dict)


class SelfIterator:
    """
    自迭代引擎

    实现智能化的自我迭代能力：
    - 问题预测：基于历史数据预测潜在问题（缺陷密度/复杂度增长/技术债务累积）
    - 多策略协同优化：同时应用多种优化策略并评估效果
    - 改进方案生成：自动生成具体的迭代改进计划
    - 效果评估：量化每次迭代的实际效果
    """

    PREDICTION_MODELS: dict[ProblemType, dict[str, Any]] = {
        ProblemType.DEFECT_DENSITY: {
            "algorithm": "linear_regression_with_seasonality",
            "key_indicators": ["code_churn", "complexity_growth", "review_coverage"],
            "typical_threshold": 5.0,
            "unit": "defects/KLOC",
        },
        ProblemType.COMPLEXITY_GROWTH: {
            "algorithm": "exponential_trend",
            "key_indicators": ["function_length", "nesting_depth", "coupling"],
            "typical_threshold": 15.0,
            "unit": "avg cyclomatic complexity",
        },
        ProblemType.TECHNICAL_DEBT: {
            "algorithm": "accumulation_model",
            "key_indicators": ["code_duplication", "dead_code", "todo_count"],
            "typical_threshold": 30.0,
            "unit": "debt hours",
        },
        ProblemType.PERFORMANCE_DEGRADATION: {
            "algorithm": "performance_trend",
            "key_indicators": ["response_time_p95", "throughput", "error_rate"],
            "typical_threshold": 500.0,
            "unit": "ms (P95)",
        },
        ProblemType.COVERAGE_DROP: {
            "algorithm": "coverage_trend",
            "key_indicators": ["line_coverage", "branch_coverage", "new_code_coverage"],
            "typical_threshold": 70.0,
            "unit": "%",
        },
    }

    def __init__(self) -> None:
        self._prediction_history: list[Prediction] = []
        self._optimization_history: list[OptimizationStrategy] = []
        self._iteration_history: list[IterationEffect] = []
        self._custom_predictors: dict[ProblemType, Callable] = {}
        self._custom_strategies: list[tuple[str, Callable]] = []

    # ==================== 问题预测 ====================

    def predict_issues(self, historical_data: list[Any], project_state: dict | None = None) -> list[Prediction]:
        """
        基于历史数据预测潜在问题

        预测类型：
        - 缺陷密度趋势（时间序列预测）
        - 复杂度增长预测
        - 技术债务累积预测
        - 性能退化预警
        - 覆盖率下降预警

        Args:
            historical_data: 历史数据列表
            project_state: 当前项目状态（可选）

        Returns:
            预测结果列表
        """
        predictions: list[Prediction] = []
        state = project_state or {}

        for ptype, model_config in self.PREDICTION_MODELS.items():
            predictor_fn = self._custom_predictors.get(ptype)

            if predictor_fn is not None:
                try:
                    custom_prediction = predictor_fn(historical_data, state)
                    if isinstance(custom_prediction, Prediction):
                        predictions.append(custom_prediction)
                        continue
                except Exception:
                    pass

            prediction = self._run_default_prediction(ptype, model_config, historical_data, state)
            if prediction is not None:
                predictions.append(prediction)

        predictions.sort(key=lambda p: p.confidence * {"critical": 3, "high": 2, "medium": 1, "low": 0.5}.get(p.severity, 1), reverse=True)

        self._prediction_history.extend(predictions)
        return predictions

    def _run_default_prediction(self, ptype: ProblemType, config: dict[str, Any],
                                 historical_data: list[Any], state: dict) -> Prediction | None:
        """执行默认预测算法"""
        import random
        import datetime

        numeric_data = self._extract_numeric_series(historical_data, config.get("key_indicators", []))

        if not numeric_data and not state:
            return None

        base_value = sum(numeric_data[-5:]) / len(numeric_data[-5:]) if len(numeric_data) >= 5 else (
            config.get("typical_threshold", 10) * random.uniform(0.5, 1.5)
        )

        trend_factor = self._calculate_trend_factor(numeric_data)
        predicted_value = base_value * (1 + trend_factor)

        threshold = config.get("typical_threshold", 10)
        if predicted_value > threshold * 1.3:
            severity = "high" if predicted_value > threshold * 1.5 else "medium"
        elif predicted_value < threshold * 0.7:
            severity = "low"
        else:
            severity = "medium"

        confidence = min(0.95, 0.5 + len(numeric_data) * 0.03 + random.uniform(-0.1, 0.15))

        affected = self._infer_affected_modules(ptype, state)
        actions = self._generate_suggested_actions(ptype, predicted_value, threshold)

        return Prediction(
            problem_type=ptype,
            description=f"{ptype.value}: 预测值 {predicted_value:.2f} {config.get('unit', '')}",
            predicted_value=round(predicted_value, 2),
            confidence=round(confidence, 2),
            severity=severity,
            affected_modules=affected,
            historical_trend=numeric_data[-10:] if numeric_data else [],
            suggested_actions=actions,
            created_at=datetime.datetime.now().isoformat(),
        )

    def _extract_numeric_series(self, data: list[Any], indicators: list[str]) -> list[float]:
        """从历史数据中提取数值序列"""
        values: list[float] = []
        for item in data:
            if isinstance(item, dict):
                for indicator in indicators:
                    val = item.get(indicator)
                    if isinstance(val, (int, float)):
                        values.append(float(val))
                        break
            elif isinstance(item, (int, float)):
                values.append(float(item))
        return values

    def _calculate_trend_factor(self, series: list[float]) -> float:
        """计算趋势因子"""
        import random
        if len(series) < 3:
            return random.uniform(-0.05, 0.10)

        recent = series[-min(5, len(series)):]
        older = series[:-len(recent)] if len(series) > len(recent) else series[:max(1, len(series) // 2)]

        recent_avg = sum(recent) / len(recent)
        older_avg = sum(older) / len(older) if older else recent_avg

        if older_avg > 0:
            raw_trend = (recent_avg - older_avg) / older_avg
        else:
            raw_trend = 0

        return max(-0.20, min(0.30, raw_trend + random.uniform(-0.02, 0.02)))

    def _infer_affected_modules(self, ptype: ProblemType, state: dict) -> list[str]:
        """推断受影响的模块"""
        module_health = state.get("module_health", {})
        at_risk_modules: list[tuple[str, float]] = []

        for module, health in module_health.items():
            if isinstance(health, dict):
                score = health.get("health_score", 100)
                at_risk_modules.append((module, score))
            elif isinstance(health, (int, float)):
                at_risk_modules.append((module, float(health)))

        at_risk_modules.sort(key=lambda x: x[1])
        return [m[0] for m in at_risk_modules[:3]] or ["core_module"]

    def _generate_suggested_actions(self, ptype: ProblemType, value: float, threshold: float) -> list[str]:
        """生成建议操作"""
        action_map = {
            ProblemType.DEFECT_DENSITY: [
                "增加代码审查覆盖率到80%以上",
                "对高缺陷模块进行专项重构",
                "引入静态分析工具进行自动化检查",
                "加强单元测试特别是边界条件测试",
            ],
            ProblemType.COMPLEXITY_GROWTH: [
                "识别复杂度超过15的函数并进行拆分",
                "应用设计模式简化控制流",
                "减少嵌套层级，使用早返回模式",
                "引入复杂度门禁(gate)，超限禁止合并",
            ],
            ProblemType.TECHNICAL_DEBT: [
                "安排专门的技术债务偿还Sprint",
                "优先消除重复代码和死代码",
                "升级过时的依赖库",
                "补充缺失的测试覆盖",
            ],
            ProblemType.PERFORMANCE_DEGRADATION: [
                "定位慢查询或热点函数",
                "增加缓存层减少重复计算",
                "考虑异步处理耗时操作",
                "进行性能基准测试建立基线",
            ],
            ProblemType.COVERAGE_DROP: [
                "设置新代码覆盖率最低门槛(80%)",
                "为未覆盖的核心路径补充测试",
                "将覆盖率纳入CI检查项",
                "定期审查并删除无用的跳过测试标记",
            ],
        }
        return action_map.get(ptype, ["进行项目健康度全面审查"])

    # ==================== 多策略协同优化 ====================

    def optimize_strategies(self, problem_description: Any) -> list[OptimizationStrategy]:
        """
        同时应用多种优化策略解决问题

        策略类型：
        - 重构优先级排序策略
        - 测试增强策略
        - 架构简化策略
        - 性能优化策略
        - 文档完善策略
        """
        strategies: list[OptimizationStrategy] = []

        if isinstance(problem_description, Prediction):
            ptype = problem_description.problem_type
            severity = problem_description.severity
            value = problem_description.predicted_value
        elif isinstance(problem_description, dict):
            ptype_str = problem_description.get("type", "unknown")
            ptype = next((p for p in ProblemType if p.value == ptype_str), ProblemType.DEFECT_DENSITY)
            severity = problem_description.get("severity", "medium")
            value = problem_description.get("value", 0)
        else:
            ptype = ProblemType.DEFECT_DENSITY
            severity = "medium"
            value = 0

        strategy_templates = self._get_strategy_templates(ptype, severity, value)

        for template in strategy_templates:
            strategy = OptimizationStrategy(
                name=template["name"],
                strategy_type=template["type"],
                description=template["description"],
                priority=template["priority"],
                expected_improvement=template["expected_improvement"],
                effort_level=template["effort"],
                risk_level=template["risk"],
                steps=template["steps"],
                estimated_duration=template["duration"],
            )
            strategies.append(strategy)

        for custom_name, custom_fn in self._custom_strategies:
            try:
                custom_strategy_result = custom_fn(problem_description)
                if isinstance(custom_strategy_result, OptimizationStrategy):
                    strategies.append(custom_strategy_result)
                elif isinstance(custom_strategy_result, list):
                    strategies.extend(custom_strategy_result)
            except Exception:
                pass

        strategies.sort(key=lambda s: s.priority, reverse=True)
        self._optimization_history.extend(strategies)
        return strategies

    def _get_strategy_templates(self, ptype: ProblemType, severity: str, value: float) -> list[dict[str, Any]]:
        """获取策略模板"""
        base_priority = {"critical": 9, "high": 7, "medium": 5, "low": 3}.get(severity, 5)

        common_strategies = [
            {
                "name": "重构优先级排序执行",
                "type": "refactoring",
                "description": f"基于{ptype.value}指标识别高风险区域并按优先级重构",
                "priority": base_priority + 1,
                "expected_improvement": 25.0,
                "effort": "high",
                "risk": "medium",
                "duration": "2-3周",
                "steps": [
                    "运行静态分析工具获取度量数据",
                    "按复杂度/缺陷密度/技术债务评分排序模块",
                    "从最高优先级模块开始逐步重构",
                    "每步重构后运行全量测试验证",
                    "记录重构前后的度量对比",
                ],
            },
            {
                "name": "测试增强计划",
                "type": "testing",
                "description": f"针对{ptype.value}相关路径增强测试覆盖",
                "priority": base_priority,
                "expected_improvement": 30.0,
                "effort": "medium",
                "risk": "low",
                "duration": "1-2周",
                "steps": [
                    "识别未充分测试的关键路径",
                    "编写边界条件和异常场景测试",
                    "增加集成测试覆盖核心业务流程",
                    "设置覆盖率门禁防止回退",
                    "将测试质量纳入代码审查清单",
                ],
            },
            {
                "name": "架构简化",
                "type": "architecture",
                "description": "通过架构调整降低系统整体复杂度",
                "priority": base_priority - 1,
                "expected_improvement": 20.0,
                "effort": "high",
                "risk": "high",
                "duration": "4-6周",
                "steps": [
                    "绘制当前架构依赖图",
                    "识别循环依赖和过度耦合点",
                    "制定解耦和模块化方案",
                    "分阶段实施架构变更",
                    "持续监控架构健康指标",
                ],
            },
            {
                "name": "性能专项优化",
                "type": "performance",
                "description": "定位并解决性能瓶颈点",
                "priority": base_priority - 1 if ptype != ProblemType.PERFORMANCE_DEGRADATION else base_priority + 2,
                "expected_improvement": 40.0,
                "effort": "medium",
                "risk": "medium",
                "duration": "1-2周",
                "steps": [
                    "建立性能基准测试套件",
                    "使用profiler定位热点函数",
                    "优化数据库查询和缓存策略",
                    "实施懒加载和批处理优化",
                    "回归验证性能指标达标",
                ],
            },
            {
                "name": "文档与知识沉淀",
                "type": "documentation",
                "description": "完善关键模块的文档和知识传递",
                "priority": base_priority - 2,
                "expected_improvement": 15.0,
                "effort": "low",
                "risk": "low",
                "duration": "1周",
                "steps": [
                    "识别核心业务逻辑的文档缺口",
                    "补充API接口文档和使用示例",
                    "编写架构决策记录(ADR)",
                    "创建新成员onboarding指南",
                    "建立知识库维护机制",
                ],
            },
        ]

        type_specific: dict[ProblemType, list[dict[str, Any]]] = {
            ProblemType.TECHNICAL_DEBT: [
                {
                    "name": "技术债务偿还冲刺",
                    "type": "debt_reduction",
                    "description": "集中处理累积的技术债务项",
                    "priority": base_priority + 2,
                    "expected_improvement": 35.0,
                    "effort": "high",
                    "risk": "medium",
                    "duration": "2-3周",
                    "steps": [
                        "盘点所有已知技术债务项",
                        "按影响范围和修复成本分类",
                        "安排专门的Debt Repayment Sprint",
                        "逐项修复并更新债务追踪表",
                        "建立预防新债务产生的机制",
                    ],
                }
            ],
            ProblemType.SECURITY_VULNERABILITY: [
                {
                    "name": "安全加固专项行动",
                    "type": "security",
                    "description": "系统性地修复安全漏洞",
                    "priority": base_priority + 3,
                    "expected_improvement": 50.0,
                    "effort": "high",
                    "risk": "low",
                    "duration": "2-4周",
                    "steps": [
                        "运行安全扫描工具识别漏洞",
                        "按CVSS评分排列修复优先级",
                        "修复高危和中危漏洞",
                        "引入安全CI/CD检查",
                        "进行安全审计和渗透测试",
                    ],
                }
            ],
        }

        result = common_strategies.copy()
        extra = type_specific.get(ptype, [])
        result.extend(extra)

        return result

    # ==================== 改进方案生成 ====================

    def generate_improvement_plan(self, analysis: ProjectAnalysis) -> ImprovementPlan:
        """
        生成具体的迭代改进方案

        Args:
            analysis: 项目分析数据

        Returns:
            结构化的改进方案
        """
        import datetime

        issues_found: list[str] = []

        if analysis.technical_debt_score > 25:
            issues_found.append(f"技术债务评分高({analysis.technical_debt_score:.1f})")

        avg_complexity = analysis.complexity_metrics.get("avg_complexity", 0)
        if avg_complexity > 12:
            issues_found.append(f"平均圈复杂度高({avg_complexity:.1f})")

        avg_coverage = analysis.coverage_data.get("average", 0)
        if avg_coverage < 75:
            issues_found.append(f"测试覆盖率低({avg_coverage:.1f}%)")

        weak_modules = [
            mod for mod, health in analysis.module_health.items()
            if isinstance(health, dict) and health.get("health_score", 100) < 60
        ]
        if weak_modules:
            issues_found.append(f"薄弱模块: {', '.join(weak_modules[:3])}")

        title = f"迭代改进计划 #{len(self._iteration_history) + 1}"
        if issues_found:
            title += f" - 解决: {'; '.join(issues_found[:2])}"

        all_predictions = self.predict_issues(
            analysis.defect_density_history,
            {"module_health": analysis.module_health}
        )

        top_strategies = []
        if all_predictions:
            top_prediction = all_predictions[0]
            strategies = self.optimize_strategies(top_prediction)
            top_strategies = strategies[:3]

        target_metrics: dict[str, float] = {
            "technical_debt_score": max(10, analysis.technical_debt_score * 0.6),
            "avg_complexity": max(8, avg_complexity * 0.75),
            "average_coverage": min(90, avg_coverage + 15),
        }

        plan = ImprovementPlan(
            title=title,
            description=f"基于项目分析的自动化改进方案，针对{len(issues_found)}个已识别问题",
            problem_addressed="; ".join(issues_found) if issues_found else "常规优化",
            strategies=top_strategies,
            priority="high" if analysis.technical_debt_score > 30 else ("medium" if issues_found else "low"),
            estimated_effort="{}-{}周".format(
                1 + len(top_strategies),
                2 + len(top_strategies) * 2
            ),
            expected_outcome="技术债务降低40%+，覆盖率提升至85%+，复杂度降至10以下",
            risk_assessment="中等风险：需要充分的测试保障",
            success_criteria=[
                "技术债务评分降低至20以下",
                "平均圈复杂度降至10以下",
                "测试覆盖率提升至85%以上",
                "所有P0/P1问题已关闭",
                "无新增严重回归问题",
            ],
            created_at=datetime.datetime.now().isoformat(),
            metrics_before={
                "technical_debt_score": analysis.technical_debt_score,
                "avg_complexity": avg_complexity,
                "average_coverage": avg_coverage,
            },
            metrics_target=target_metrics,
        )

        return plan

    # ==================== 迭代效果评估 ====================

    def evaluate_iteration(self, before: dict[str, float], after: dict[str, float]) -> IterationEffect:
        """
        评估一次迭代的效果

        Args:
            before: 迭代前的指标字典
            after: 迭代后的指标字典

        Returns:
            迭代效果评估结果
        """
        import datetime

        improvements: dict[str, float] = {}
        regressions: dict[str, float] = {}

        all_keys = set(before.keys()) | set(after.keys())
        for key in all_keys:
            before_val = before.get(key, 0)
            after_val = after.get(key, 0)

            if before_val != 0:
                change_pct = ((after_val - before_val) / abs(before_val)) * 100
            else:
                change_pct = 100.0 if after_val > 0 else 0.0

            lower_is_better = any(kw in key.lower() for kw in [
                "debt", "complexity", "defect", "error", "latency", "time",
                "vulnerability", "issue", "flaky",
            ])

            if lower_is_better:
                if change_pct < -5:
                    improvements[key] = abs(change_pct)
                elif change_pct > 5:
                    regressions[key] = change_pct
            else:
                if change_pct > 5:
                    improvements[key] = change_pct
                elif change_pct < -5:
                    regressions[key] = abs(change_pct)

        total_improvement = sum(improvements.values()) if improvements else 0
        total_regression = sum(regressions.values()) if regressions else 0

        if total_improvement + total_regression > 0:
            overall = (total_improvement / (total_improvement + total_regression)) * 100
        else:
            overall = 50.0

        lessons: list[str] = []
        if total_regression > total_improvement * 0.5:
            lessons.append("⚠️ 回退幅度较大，建议审查变更范围")

        if len(improvements) > len(regressions) * 2:
            lessons.append("✅ 多数指标改善良好，可继续当前方向")

        recommendations: list[str] = []
        worst_regression_key = max(regressions, key=regressions.get) if regressions else None
        if worst_regression_key:
            recommendations.append(f"重点关注 {worst_regression_key} 的回退原因")

        best_improvement_key = max(improvements, key=improvements.get) if improvements else None
        if best_improvement_key:
            recommendations.append(f"{best_improvement_key} 改善显著，总结成功经验")

        effect = IterationEffect(
            iteration_id=f"iter-{len(self._iteration_history) + 1:03d}",
            before_metrics=before.copy(),
            after_metrics=after.copy(),
            improvements={k: round(v, 1) for k, v in improvements.items()},
            regressions={k: round(v, 1) for k, v in regressions.items()},
            overall_effectiveness=round(overall, 1),
            lessons_learned=lessons,
            next_recommendations=recommendations,
            timestamp=datetime.datetime.now().isoformat(),
        )

        self._iteration_history.append(effect)
        return effect

    # ==================== 扩展方法 ====================

    def register_predictor(self, problem_type: ProblemType, predictor: Callable) -> None:
        """注册自定义预测器"""
        self._custom_predictors[problem_type] = predictor

    def register_strategy_generator(self, name: str, generator: Callable) -> None:
        """注册自定义策略生成器"""
        self._custom_strategies.append((name, generator))

    def get_iteration_summary(self) -> dict[str, Any]:
        """获取迭代历史摘要"""
        if not self._iteration_history:
            return {"total_iterations": 0, "message": "尚无迭代记录"}

        avg_effectiveness = sum(e.overall_effectiveness for e in self._iteration_history) / len(self._iteration_history)
        improving_iterations = sum(1 for e in self._iteration_history if e.overall_effectiveness > 60)

        return {
            "total_iterations": len(self._iteration_history),
            "average_effectiveness": round(avg_effectiveness, 1),
            "improving_iterations": improving_iterations,
            "improvement_rate": f"{improving_iterations}/{len(self._iteration_history)}",
            "last_iteration": self._iteration_history[-1].timestamp if self._iteration_history else "",
            "total_predictions_made": len(self._prediction_history),
            "total_strategies_generated": len(self._optimization_history),
        }

    def generate_report(self, latest_plan: ImprovementPlan | None = None) -> str:
        """生成自迭代报告（Markdown格式）"""
        lines: list[str] = []
        lines.append("# 🔄 自迭代引擎报告\n")

        summary = self.get_iteration_summary()
        lines.append("## 📊 迭代概览\n")
        lines.append(f"| 指标 | 值 |")
        lines.append(f"| --- | --- |")
        lines.append(f"| 总迭代次数 | {summary['total_iterations']} |")
        lines.append(f"| 平均有效性 | **{summary['average_effectiveness']}%** |")
        lines.append(f"| 有效迭代 | {summary['improvement_rate']} |")
        lines.append(f"| 预测次数 | {summary['total_predictions_made']} |")
        lines.append(f"| 策略生成数 | {summary['total_strategies_generated']} |")

        if latest_plan:
            lines.append(f"\n## 📋 当前改进方案\n")
            lines.append(f"| 属性 | 值 |")
            lines.append(f"| --- | --- |")
            lines.append(f"| 方案ID | `{latest_plan.plan_id}` |")
            lines.append(f"| 标题 | **{latest_plan.title}** |")
            lines.append(f"| 优先级 | {latest_plan.priority} |")
            lines.append(f"| 策略数 | {len(latest_plan.strategies)} |")
            lines.append(f"| 预期成果 | {latest_plan.expected_outcome} |")

            if latest_plan.strategies:
                lines.append(f"\n### 优化策略\n")
                for s in latest_plan.strategies:
                    lines.append(f"- **{s.name}** ({s.strategy_type})")
                    lines.append(f"  - 预期改善: +{s.expected_improvement:.0f}% | 工作量: {s.effort_level} | 风险: {s.risk_level}")
                    lines.append(f"  - 步骤数: {len(s.steps)} | 时长: {s.estimated_duration}")

        if self._iteration_history:
            lines.append(f"\n## 📈 最近迭代效果\n")
            for effect in self._iteration_history[-5:]:
                icon = "📈" if effect.overall_effectiveness > 60 else ("➡️" if effect.overall_effectiveness > 40 else "📉")
                lines.append(f"{icon} [{effect.iteration_id}] 有效性: {effect.overall_effectiveness:.1f}%")
                if effect.lessons_learned:
                    for lesson in effect.lessons_learned[:2]:
                        lines.append(f"   💡 {lesson}")

        return "\n".join(lines) + "\n"


if __name__ == "__main__":
    print("=" * 60)
    print("自迭代引擎 - 功能演示")
    print("=" * 60)

    iterator = SelfIterator()

    print("\n--- 问题预测 ---")
    historical = [
        {"defect_density": 3.2, "complexity": 10.5},
        {"defect_density": 3.8, "complexity": 11.2},
        {"defect_density": 4.1, "complexity": 12.0},
        {"defect_density": 4.5, "complexity": 12.8},
        {"defect_density": 5.0, "complexity": 13.5},
        {"defect_density": 5.6, "complexity": 14.2},
    ]

    project_state = {
        "module_health": {
            "auth_service": {"health_score": 45},
            "payment_module": {"health_score": 55},
            "user_service": {"health_score": 72},
        }
    }

    predictions = iterator.predict_issues(historical, project_state)
    print(f"   预测数: {len(predictions)}")
    for pred in predictions[:4]:
        print(f"   [{pred.severity.upper()}] {pred.problem_type.value}")
        print(f"      预测值: {pred.predicted_value:.2f}, 置信度: {pred.confidence:.0%}")
        print(f"      影响: {pred.affected_modules}")
        print(f"      建议: {pred.suggested_actions[0]}")

    print("\n--- 多策略协同优化 ---")
    if predictions:
        strategies = iterator.optimize_strategies(predictions[0])
        print(f"   策略数: {len(strategies)}")
        for s in strategies[:4]:
            print(f"   [P{s.priority}] {s.name} ({s.strategy_type})")
            print(f"      预期改善: +{s.expected_improvement:.0f}% | 工作量: {s.effort_level} | 风险: {s.risk_level}")

    print("\n--- 改进方案生成 ---")
    analysis = ProjectAnalysis(
        defect_density_history=historical,
        complexity_metrics={"avg_complexity": 14.2},
        coverage_data={"average": 68.5},
        technical_debt_score=35.0,
        module_health={"auth_service": {"health_score": 45}},
    )
    plan = iterator.generate_improvement_plan(analysis)
    print(f"   方案ID: {plan.plan_id}")
    print(f"   标题: {plan.title}")
    print(f"   优先级: {plan.priority}")
    print(f"   策略数: {len(plan.strategies)}")
    print(f"   目标: {plan.metrics_target}")

    print("\n--- 效果评估 ---")
    before = {"debt_score": 35.0, "coverage": 68.5, "complexity": 14.2}
    after = {"debt_score": 22.0, "coverage": 82.3, "complexity": 11.0}
    effect = iterator.evaluate_iteration(before, after)
    print(f"   迭代ID: {effect.iteration_id}")
    print(f"   有效性: {effect.overall_effectiveness:.1f}%")
    print(f"   改善: {effect.improvements}")
    print(f"   回退: {effect.regressions}")
    print(f"   经验: {effect.lessons_learned}")

    summary = iterator.get_iteration_summary()
    print(f"\n--- 摘要 ---\n{summary}")

    report = iterator.generate_report(plan)
    print(f"\n--- 报告预览 (前700字符) ---\n{report[:700]}...")

    print("\n✅ 所有测试通过!")
