"""
自主决策层 (Decide Layer)
==========================
基于感知层的报告进行多准则决策分析，输出可执行的决策方案。
包含四个核心能力：
- 多准则决策引擎：加权评分、Pareto最优解筛选
- 风险评估模块：影响范围分析、风险等级判定
- Trade-off分析器：多方案对比矩阵生成
- 策略选择器：根据任务类型和上下文选择最佳策略
"""
from __future__ import annotations

import math
import statistics
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from pathlib import Path
from typing import Any


class DecisionError(Exception):
    """决策层相关异常"""
    pass


class RiskLevel(str, Enum):
    """风险等级"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class TaskCategory(str, Enum):
    """任务类型分类"""
    BUG_FIX = "bug_fix"
    REFACTORING = "refactoring"
    FEATURE_ADD = "feature_add"
    PERFORMANCE_OPT = "performance_optimization"
    SECURITY_FIX = "security_fix"
    TEST_ADDITION = "test_addition"
    DOCUMENTATION = "documentation"
    DEPENDENCY_UPDATE = "dependency_update"
    CODE_REVIEW = "code_review"
    GENERAL = "general"


class StrategyType(str, Enum):
    """策略类型"""
    CONSERVATIVE = "conservative"
    BALANCED = "balanced"
    AGGRESSIVE = "aggressive"
    AUTOMATED = "automated"
    MANUAL = "manual"
    HYBRID = "hybrid"


@dataclass
class Criterion:
    """决策准则"""
    name: str
    weight: float = 1.0
    direction: str = "maximize"
    score: float = 0.0
    normalized_score: float = 0.0


@dataclass
class CandidateAction:
    """候选行动方案"""
    action_id: str
    description: str
    category: str = ""
    scores: dict[str, float] = field(default_factory=dict)
    estimated_effort: float = 1.0
    risk_level: RiskLevel = RiskLevel.LOW
    affected_files: list[str] = field(default_factory=list)
    prerequisites: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def weighted_score(self) -> float:
        return sum(
            s * (self.scores.get(c.name, 0) if c.direction == "maximize" else (100 - self.scores.get(c.name, 100)))
            for c in []
        )


@dataclass
class RiskAssessment:
    """风险评估结果"""
    level: RiskLevel = RiskLevel.LOW
    score: float = 0.0
    impact_scope: str = ""
    affected_components: list[str] = field(default_factory=list)
    affected_users: str = ""
    rollback_difficulty: str = "easy"
    side_effects: list[str] = field(default_factory=list)
    mitigation_suggestions: list[str] = field(default_factory=list)
    details: dict[str, Any] = field(default_factory=dict)


@dataclass
class TradeOffMatrix:
    """Trade-off对比矩阵"""
    candidates: list[CandidateAction] = field(default_factory=list)
    criteria: list[Criterion] = field(default_factory=list)
    pareto_front: list[int] = field(default_factory=list)
    recommendation: int = -1
    comparison_data: dict[str, Any] = field(default_factory=dict)


@dataclass
class ReasoningStep:
    """推理步骤（理由链中的一环）"""
    step_id: int
    phase: str
    conclusion: str
    evidence: dict[str, Any] = field(default_factory=dict)
    confidence: float = 1.0
    timestamp: str = ""


@dataclass
class Decision:
    """
    决策结果 - 决策层的统一输出
    
    包含完整的决策方案和推理链，确保决策过程可追溯。
    """
    decision_id: str = ""
    timestamp: str = ""
    task_category: TaskCategory = TaskCategory.GENERAL
    selected_action: CandidateAction | None = None
    strategy: StrategyType = StrategyType.BALANCED
    risk_assessment: RiskAssessment = field(default_factory=RiskAssessment)
    trade_off: TradeOffMatrix = field(default_factory=TradeOffMatrix)
    reasoning_chain: list[ReasoningStep] = field(default_factory=list)
    confidence: float = 0.0
    alternatives: list[CandidateAction] = field(default_factory=list)
    execution_plan: list[dict[str, Any]] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "decision_id": self.decision_id,
            "timestamp": self.timestamp,
            "task_category": self.task_category.value,
            "strategy": self.strategy.value,
            "selected_action": self.selected_action.action_id if self.selected_action else None,
            "risk_level": self.risk_assessment.level.value,
            "confidence": round(self.confidence, 3),
            "reasoning_steps": len(self.reasoning_chain),
            "alternatives_count": len(self.alternatives),
        }


class MultiCriteriaDecisionEngine:
    """
    多准则决策引擎
    
    基于加权评分模型和Pareto最优理论进行多目标决策。
    支持动态权重调整、敏感性分析和多方案排序。
    """

    DEFAULT_CRITERIA: list[Criterion] = [
        Criterion("effectiveness", weight=0.25, direction="maximize"),
        Criterion("safety", weight=0.20, direction="maximize"),
        Criterion("efficiency", weight=0.15, direction="maximize"),
        Criterion("maintainability", weight=0.15, direction="maximize"),
        Criterion("testability", weight=0.10, direction="maximize"),
        Criterion("effort_cost", weight=0.10, direction="minimize"),
        Criterion("risk", weight=0.05, direction="minimize"),
    ]

    def __init__(self, custom_criteria: list[Criterion] | None = None) -> None:
        self._criteria: list[Criterion] = list(custom_criteria or self.DEFAULT_CRITERIA)
        self._normalize_weights()

    def _normalize_weights(self) -> None:
        total = sum(c.weight for c in self._criteria)
        if total > 0:
            for c in self._criteria:
                c.weight /= total

    def evaluate(self, candidates: list[CandidateAction]) -> tuple[list[CandidateAction], TradeOffMatrix]:
        """
        对所有候选方案进行多准则评估
        
        Args:
            candidates: 候选行动方案列表
            
        Returns:
            (评估后的候选方案列表, TradeOff矩阵)
        """
        for candidate in candidates:
            candidate.scores = self._compute_scores(candidate)
        matrix = self._build_tradeoff_matrix(candidates)
        return candidates, matrix

    def _compute_scores(self, candidate: CandidateAction) -> dict[str, float]:
        scores: dict[str, float] = {}
        for criterion in self._criteria:
            raw = self._score_criterion(candidate, criterion.name)
            scores[criterion.name] = raw
        return scores

    @staticmethod
    def _score_criterion(candidate: CandidateAction, criterion_name: str) -> float:
        base_scores: dict[str, float] = {
            "effectiveness": 70.0,
            "safety": 80.0 - ({"LOW": 0, "MEDIUM": 20, "HIGH": 45, "CRITICAL": 70}.get(candidate.risk_level.value, 0)),
            "efficiency": max(20, 90 - candidate.estimated_effort * 10),
            "maintainability": 65.0 + len(candidate.affected_files) * -1.5,
            "testability": 60.0,
            "effort_cost": min(100, candidate.estimated_effort * 15),
            "risk": {"LOW": 10, "MEDIUM": 35, "HIGH": 65, "CRITICAL": 90}.get(candidate.risk_level.value, 50),
        }
        base = base_scores.get(criterion_name, 50.0)
        meta_mod = candidate.metadata.get(f"{criterion_name}_modifier", 0)
        return max(0, min(100, base + meta_mod))

    def _build_tradeoff_matrix(self, candidates: list[CandidateAction]) -> TradeOffMatrix:
        pareto_indices = self._find_pareto_front(candidates)
        best_idx = self._select_best(candidates, pareto_indices)
        return TradeOffMatrix(
            candidates=candidates,
            criteria=self._criteria,
            pareto_front=pareto_indices,
            recommendation=best_idx,
            comparison_data={
                "total_candidates": len(candidates),
                "pareto_count": len(pareto_indices),
                "criteria_weights": {c.name: round(c.weight, 4) for c in self._criteria},
            },
        )

    def _find_pareto_front(self, candidates: list[CandidateAction]) -> list[int]:
        pareto: list[int] = []
        for i, cand_a in enumerate(candidates):
            dominated = False
            for j, cand_b in enumerate(candidates):
                if i == j:
                    continue
                a_better_or_equal = all(
                    cand_a.scores.get(c.name, 0) >= cand_b.scores.get(c.name, 0)
                    if c.direction == "maximize" else
                    cand_a.scores.get(c.name, 100) <= cand_b.scores.get(c.name, 100)
                    for c in self._criteria
                )
                a_strictly_better = any(
                    cand_a.scores.get(c.name, 0) > cand_b.scores.get(c.name, 0)
                    if c.direction == "maximize" else
                    cand_a.scores.get(c.name, 100) < cand_b.scores.get(c.name, 100)
                    for c in self._criteria
                )
                if a_better_or_equal and a_strictly_better:
                    dominated = True
                    break
            if not dominated:
                pareto.append(i)
        return pareto or list(range(len(candidates)))

    def _select_best(self, candidates: list[CandidateAction], pareto_indices: list[int]) -> int:
        if not candidates:
            return -1
        if len(pareto_indices) == 1:
            return pareto_indices[0]
        best_idx = -1
        best_weighted = -float("inf")
        for idx in pareto_indices:
            cand = candidates[idx]
            weighted = sum(
                cand.scores.get(c.name, 50) * c.weight
                for c in self._criteria
                if c.direction == "maximize"
            ) - sum(
                cand.scores.get(c.name, 50) * c.weight
                for c in self._criteria
                if c.direction == "minimize"
            )
            if weighted > best_weighted:
                best_weighted = weighted
                best_idx = idx
        return best_idx

    def sensitivity_analysis(self, candidates: list[CandidateAction], delta: float = 0.1) -> dict[str, Any]:
        """
        敏感性分析：测试权重变化对决策结果的影响
        
        Args:
            candidates: 候选方案列表
            delta: 权重变化幅度
            
        Returns:
            敏感性分析结果字典
        """
        results: dict[str, Any] = {"stable_rankings": True, "changes": []}
        original_evaluated, original_matrix = self.evaluate(list(candidates))
        original_best = original_matrix.recommendation

        for ci, criterion in enumerate(self._criteria):
            test_criteria = [Criterion(c.name, c.weight, c.direction) for c in self._criteria]
            test_criteria[ci].weight += delta
            total_w = sum(tc.weight for tc in test_criteria)
            for tc in test_criteria:
                tc.weight /= total_w

            test_engine = MultiCriteriaDecisionEngine(test_criteria)
            _, test_matrix = test_engine.evaluate(list(candidates))
            if test_matrix.recommendation != original_best:
                results["stable_rankings"] = False
                results["changes"].append({
                    "criterion": criterion.name,
                    "weight_change": f"+{delta}",
                    "new_best": candidates[test_matrix.recommendation].action_id if test_matrix.recommendation >= 0 else None,
                })
        return results


class RiskAssessor:
    """
    风险评估模块
    
    分析操作的影响范围、判定风险等级、生成缓解建议。
    基于多维度因子综合评估：影响范围、修改复杂度、代码热度、历史回归率等。
    """

    RISK_THRESHOLDS = {
        RiskLevel.LOW: 25,
        RiskLevel.MEDIUM: 50,
        RiskLevel.HIGH: 75,
        RiskLevel.CRITICAL: 100,
    }

    def assess(
        self,
        action: CandidateAction,
        perception_report: Any = None,
    ) -> RiskAssessment:
        """
        执行全面风险评估
        
        Args:
            action: 待评估的候选行动方案
            perception_report: 感知报告（可选，用于增强评估）
            
        Returns:
            RiskAssessment对象
        """
        factors: dict[str, float] = {}
        factors["scope"] = self._assess_scope(action)
        factors["complexity"] = self._assess_complexity(action)
        factors["history"] = self._assess_history(action, perception_report)
        factors["quality"] = self._assess_quality_context(perception_report)
        factors["stability"] = self._assess_stability(perception_report)

        weights = {"scope": 0.30, "complexity": 0.25, "history": 0.20, "quality": 0.15, "stability": 0.10}
        total_score = sum(factors.get(k, 0) * w for k, w in weights.items())
        level = self._determine_level(total_score)

        impact_desc = self._describe_impact(action, level)
        side_effects = self._predict_side_effects(action, level)
        mitigations = self._generate_mitigations(action, level)

        return RiskAssessment(
            level=level,
            score=round(total_score, 2),
            impact_scope=impact_desc,
            affected_components=action.affected_files[:],
            affected_users=self._estimate_affected_users(level),
            rollback_difficulty=self._estimate_rollback_difficulty(action),
            side_effects=side_effects,
            mitigation_suggestions=mitigations,
            details={"factors": factors, "weights": weights},
        )

    def _assess_scope(self, action: CandidateAction) -> float:
        file_count = len(action.affected_files)
        if file_count == 0:
            return 5.0
        elif file_count <= 2:
            return 15.0
        elif file_count <= 5:
            return 30.0
        elif file_count <= 10:
            return 50.0
        elif file_count <= 20:
            return 70.0
        else:
            return 90.0

    def _assess_complexity(self, action: CandidateAction) -> float:
        effort = action.estimated_effort
        if effort <= 1:
            return 10.0
        elif effort <= 3:
            return 25.0
        elif effort <= 5:
            return 45.0
        elif effort <= 8:
            return 65.0
        else:
            return 85.0

    def _assess_history(self, action: CandidateAction, report: Any) -> float:
        if report is None:
            return 30.0
        try:
            pattern = report.historical_pattern
            hotspot_files = [hf["file_path"] for hf in pattern.hotspot_files]
            regression_areas = pattern.regression_prone_areas
            overlap_hotspot = sum(1 for f in action.affected_files if any(hf in f or f in hf for hf in hotspot_files))
            overlap_regression = sum(1 for f in action.affected_files if any(ra in f or f in ra for ra in regression_areas))
            score = overlap_hotspot * 15 + overlap_regression * 20
            score += (1.0 - pattern.fix_success_rate) * 40
            return min(95, max(5, score))
        except Exception:
            return 30.0

    def _assess_quality_context(self, report: Any) -> float:
        if report is None:
            return 30.0
        try:
            quality = report.quality_snapshot
            if quality.overall_score >= 80:
                return 15.0
            elif quality.overall_score >= 60:
                return 30.0
            elif quality.overall_score >= 40:
                return 50.0
            else:
                return 75.0
        except Exception:
            return 30.0

    def _assess_stability(self, report: Any) -> float:
        if report is None:
            return 30.0
        try:
            state = report.project_state
            if not state.git_status_clean:
                return 55.0
            recent_activity = state.commit_count_7d
            if recent_activity > 20:
                return 40.0
            elif recent_activity > 5:
                return 25.0
            else:
                return 15.0
        except Exception:
            return 30.0

    def _determine_level(self, score: float) -> RiskLevel:
        if score >= self.RISK_THRESHOLDS[RiskLevel.CRITICAL]:
            return RiskLevel.CRITICAL
        elif score >= self.RISK_THRESHOLDS[RiskLevel.HIGH]:
            return RiskLevel.HIGH
        elif score >= self.RISK_THRESHOLDS[RiskLevel.MEDIUM]:
            return RiskLevel.MEDIUM
        else:
            return RiskLevel.LOW

    @staticmethod
    def _describe_impact(action: CandidateAction, level: RiskLevel) -> str:
        count = len(action.affected_files)
        desc_map = {
            RiskLevel.LOW: f"局部影响({count}个文件)，仅限当前模块内部",
            RiskLevel.MEDIUM: f"中等影响({count}个文件)，可能波及关联模块",
            RiskLevel.HIGH: f"较大影响({count}个文件)，涉及核心功能区域",
            RiskLevel.CRITICAL: f"全局影响({count}个文件)，可能影响系统整体稳定性",
        }
        return desc_map.get(level, "未知影响范围")

    @staticmethod
    def _predict_side_effects(action: CandidateAction, level: RiskLevel) -> list[str]:
        effects: list[str] = []
        if level in (RiskLevel.HIGH, RiskLevel.CRITICAL):
            effects.extend(["可能触发级联失败", "API兼容性风险", "性能回退可能性"])
        if level in (RiskLevel.MEDIUM, RiskLevel.HIGH, RiskLevel.CRITICAL):
            effects.append("依赖模块需同步更新")
        if action.estimated_effort > 5:
            effects.append("长时间开发窗口增加合并冲突风险")
        if len(action.affected_files) > 5:
            effects.append("多文件协调变更增加遗漏风险")
        return effects[:6]

    @staticmethod
    def _generate_mitigations(action: CandidateAction, level: RiskLevel) -> list[str]:
        mitigations: list[str] = ["编写充分的单元测试覆盖变更"]
        if level in (RiskLevel.MEDIUM, RiskLevel.HIGH, RiskLevel.CRITICAL):
            mitigations.extend([
                "实施灰度发布或特性开关",
                "准备完整的回滚方案",
                "邀请资深开发者进行Code Review",
            ])
        if level in (RiskLevel.HIGH, RiskLevel.CRITICAL):
            mitigations.extend([
                "在独立分支上充分验证后再合入",
                "监控关键指标设置告警阈值",
                "准备紧急修复预案",
            ])
        if len(action.affected_files) > 3:
            mitigations.append("分阶段提交，每阶段独立验证")
        return mitigations[:8]

    @staticmethod
    def _estimate_affected_users(level: RiskLevel) -> str:
        return {
            RiskLevel.LOW: "开发团队内部",
            RiskLevel.MEDIUM: "部分用户/特定场景",
            RiskLevel.HIGH: "大部分用户",
            RiskLevel.CRITICAL: "全部用户/系统级别",
        }.get(level, "未知")

    @staticmethod
    def _estimate_rollback_difficulty(action: CandidateAction) -> str:
        if action.estimated_effort <= 2 and len(action.affected_files) <= 2:
            return "easy"
        elif action.estimated_effort <= 5 and len(action.affected_files) <= 5:
            return "moderate"
        else:
            return "difficult"


class TradeOffAnalyzer:
    """
    Trade-off分析器
    
    生成多方案的详细对比矩阵，帮助理解各方案在不同维度上的优劣权衡。
    输出结构化的对比数据，支持可视化展示。
    """

    def analyze(
        self,
        candidates: list[CandidateAction],
        criteria: list[Criterion],
    ) -> TradeOffMatrix:
        """
        执行完整的Trade-off分析
        
        Args:
            candidates: 候选方案列表
            criteria: 评估准则列表
            
        Returns:
            完整的TradeOffMatrix对象
        """
        scored_candidates = []
        for cand in candidates:
            scores: dict[str, float] = {}
            for crit in criteria:
                val = cand.scores.get(crit.name, 50.0)
                scores[crit.name] = val
            new_cand = CandidateAction(
                action_id=cand.action_id,
                description=cand.description,
                category=cand.category,
                scores=scores,
                estimated_effort=cand.estimated_effort,
                risk_level=cand.risk_level,
                affected_files=list(cand.affected_files),
                prerequisites=list(cand.prerequisites),
                metadata=dict(cand.metadata),
            )
            scored_candidates.append(new_cand)

        pareto = self._compute_pareto(scored_candidates, criteria)
        recommended = self._recommend(scored_candidates, pareto, criteria)

        comp_data = self._generate_comparison_data(scored_candidates, criteria, pareto, recommended)

        return TradeOffMatrix(
            candidates=scored_candidates,
            criteria=criteria,
            pareto_front=pareto,
            recommendation=recommended,
            comparison_data=comp_data,
        )

    @staticmethod
    def _compute_pareto(
        candidates: list[CandidateAction],
        criteria: list[Criterion],
    ) -> list[int]:
        pareto: list[int] = []
        for i, ca in enumerate(candidates):
            dominated = False
            for j, cb in enumerate(candidates):
                if i == j:
                    continue
                all_better_eq = True
                any_strictly_better = False
                for c in criteria:
                    va = ca.scores.get(c.name, 50)
                    vb = cb.scores.get(c.name, 50)
                    if c.direction == "maximize":
                        if va < vb - 0.001:
                            all_better_eq = False
                        if va > vb + 0.001:
                            any_strictly_better = True
                    else:
                        if va > vb + 0.001:
                            all_better_eq = False
                        if va < vb - 0.001:
                            any_strictly_better = True
                if all_better_eq and any_strictly_better:
                    dominated = True
                    break
            if not dominated:
                pareto.append(i)
        return pareto if pareto else list(range(len(candidates)))

    @staticmethod
    def _recommend(
        candidates: list[CandidateAction],
        pareto: list[int],
        criteria: list[Criterion],
    ) -> int:
        if not candidates:
            return -1
        if len(pareto) == 1:
            return pareto[0]

        best_idx = -1
        best_score = -float("inf")
        for idx in pareto:
            cand = candidates[idx]
            total = 0.0
            for c in criteria:
                val = cand.scores.get(c.name, 50.0)
                if c.direction == "maximize":
                    total += val * c.weight
                else:
                    total += (100 - val) * c.weight
            if total > best_score:
                best_score = total
                best_idx = idx
        return best_idx

    def _generate_comparison_data(
        self,
        candidates: list[CandidateAction],
        criteria: list[Criterion],
        pareto: list[int],
        recommended: int,
    ) -> dict[str, Any]:
        rows: list[dict[str, Any]] = []
        for i, cand in enumerate(candidates):
            row: dict[str, Any] = {
                "rank": i + 1,
                "action_id": cand.action_id,
                "description": cand.description,
                "is_pareto": i in pareto,
                "is_recommended": i == recommended,
                "weighted_total": round(
                    sum(
                        cand.scores.get(c.name, 50) * c.weight
                        for c in criteria
                        if c.direction == "maximize"
                    ) - sum(
                        cand.scores.get(c.name, 50) * c.weight
                        for c in criteria
                        if c.direction == "minimize"
                    ), 2
                ),
                "scores": {},
            }
            for c in criteria:
                row["scores"][c.name] = round(cand.scores.get(c.name, 0), 2)
            rows.append(row)

        dimension_analysis: dict[str, Any] = {}
        for c in criteria:
            values = [cand.scores.get(c.name, 0) for cand in candidates]
            dimension_analysis[c.name] = {
                "best": round(max(values), 2) if c.direction == "maximize" else round(min(values), 2),
                "worst": round(min(values), 2) if c.direction == "maximize" else round(max(values), 2),
                "avg": round(statistics.mean(values), 2) if values else 0,
                "range": round(max(values) - min(values), 2) if len(values) > 1 else 0,
                "direction": c.direction,
            }

        return {
            "comparison_rows": rows,
            "dimension_analysis": dimension_analysis,
            "summary": {
                "total_candidates": len(candidates),
                "pareto_front_size": len(pareto),
                "recommended_index": recommended,
                "recommended_action": candidates[recommended].action_id if recommended >= 0 else None,
            },
        }


class StrategySelector:
    """
    策略选择器
    
    根据任务类型、风险评估结果、质量指标和历史模式，
    自动选择最适合的执行策略（保守/平衡/激进/自动化/手动/混合）。
    """

    STRATEGY_MAP: dict[tuple[TaskCategory, RiskLevel], StrategyType] = {
        (TaskCategory.SECURITY_FIX, RiskLevel.CRITICAL): StrategyType.CONSERVATIVE,
        (TaskCategory.SECURITY_FIX, RiskLevel.HIGH): StrategyType.CONSERVATIVE,
        (TaskCategory.BUG_FIX, RiskLevel.CRITICAL): StrategyType.CONSERVATIVE,
        (TaskCategory.PERFORMANCE_OPT, RiskLevel.HIGH): StrategyType.BALANCED,
        (TaskCategory.FEATURE_ADD, RiskLevel.LOW): StrategyType.AGGRESSIVE,
        (TaskCategory.DOCUMENTATION, RiskLevel.LOW): StrategyType.AUTOMATED,
        (TaskCategory.TEST_ADDITION, RiskLevel.LOW): StrategyType.AUTOMATED,
        (TaskCategory.CODE_REVIEW, RiskLevel.LOW): StrategyType.AUTOMATED,
    }

    def select(
        self,
        task_category: TaskCategory,
        risk_assessment: RiskAssessment,
        perception_report: Any = None,
    ) -> StrategyType:
        """
        选择最佳执行策略
        
        Args:
            task_category: 任务类型
            risk_assessment: 风险评估结果
            perception_report: 感知报告（可选）
            
        Returns:
            推荐的策略类型
        """
        cache_key = (task_category, risk_assessment.level)
        if cache_key in self.STRATEGY_MAP:
            return self.STRATEGY_MAP[cache_key]

        context_factors = self._analyze_context(risk_assessment, perception_report)
        strategy = self._resolve_strategy(task_category, risk_assessment.level, context_factors)
        return strategy

    def _analyze_context(self, risk: RiskAssessment, report: Any) -> dict[str, float]:
        factors: dict[str, float] = {
            "quality_health": 0.5,
            "team_confidence": 0.7,
            "time_pressure": 0.5,
            "automation_readiness": 0.6,
        }

        if report is not None:
            try:
                q = report.quality_snapshot
                factors["quality_health"] = q.overall_score / 100.0
            except Exception:
                pass
            try:
                p = report.historical_pattern
                factors["team_confidence"] = p.fix_success_rate
            except Exception:
                pass

        return factors

    def _resolve_strategy(
        self,
        category: TaskCategory,
        risk_level: RiskLevel,
        context: dict[str, float],
    ) -> StrategyType:
        risk_penalty = {
            RiskLevel.LOW: 0,
            RiskLevel.MEDIUM: 1,
            RiskLevel.HIGH: 2,
            RiskLevel.CRITICAL: 3,
        }.get(risk_level, 0)

        category_bonus = {
            TaskCategory.DOCUMENTATION: 2,
            TaskCategory.TEST_ADDITION: 1,
            TaskCategory.CODE_REVIEW: 1,
            TaskCategory.DEPENDENCY_UPDATE: 0,
            TaskCategory.GENERAL: 0,
            TaskCategory.REFACTORING: -1,
            TaskCategory.BUG_FIX: -1,
            TaskCategory.FEATURE_ADD: -1,
            TaskCategory.PERFORMANCE_OPT: -2,
            TaskCategory.SECURITY_FIX: -3,
        }.get(category, 0)

        score = context.get("quality_health", 0.5) * 20 + \
                context.get("team_confidence", 0.7) * 15 + \
                category_bonus * 5 - \
                risk_penalty * 8

        if score >= 30:
            return StrategyType.AGGRESSIVE
        elif score >= 15:
            return StrategyType.BALANCED
        elif score >= 0:
            return StrategyType.CONSERVATIVE
        else:
            if category in (TaskCategory.DOCUMENTATION, TaskCategory.TEST_ADDITION):
                return StrategyType.AUTOMATED
            else:
                return StrategyType.HYBRID


class DecideLayer:
    """
    自主决策层 - 统一入口
    
    协调四个子模块完成完整的决策流程：
    MultiCriteriaDecisionEngine → RiskAssessor → TradeOffAnalyzer → StrategySelector
    最终输出包含完整推理链的Decision对象。
    """

    def __init__(
        self,
        custom_criteria: list[Criterion] | None = None,
    ) -> None:
        self._engine = MultiCriteriaDecisionEngine(custom_criteria)
        self._risk_assessor = RiskAssessor()
        self._tradeoff_analyzer = TradeOffAnalyzer()
        self._strategy_selector = StrategySelector()
        self._decision_counter: int = 0

    def decide(
        self,
        perception_report: Any,
        candidates: list[CandidateAction] | None = None,
    ) -> Decision:
        """
        执行完整决策流程
        
        Args:
            perception_report: 感知层的输出报告
            candidates: 候选行动方案列表（如不提供则自动生成）
            
        Returns:
            完整的Decision对象，含推理链
        """
        self._decision_counter += 1
        now = datetime.now().isoformat()
        reasoning: list[ReasoningStep] = []

        task_cat = self._classify_task(perception_report.task_description)
        reasoning.append(ReasoningStep(
            step_id=1, phase="task_classification",
            conclusion=f"任务分类为: {task_cat.value}",
            evidence={"task_description": perception_report.task_description[:200]},
            confidence=0.85,
            timestamp=now,
        ))

        if candidates is None:
            candidates = self._generate_candidates(perception_report, task_cat)
        reasoning.append(ReasoningStep(
            step_id=2, phase="candidate_generation",
            conclusion=f"生成了{len(candidates)}个候选方案",
            evidence={"candidate_ids": [c.action_id for c in candidates]},
            confidence=0.75,
            timestamp=datetime.now().isoformat(),
        ))

        evaluated_candidates, tradeoff = self._engine.evaluate(candidates)
        reasoning.append(ReasoningStep(
            step_id=3, phase="multi_criteria_evaluation",
            conclusion=f"多准则评估完成，Pareto前沿包含{len(tradeoff.pareto_front)}个方案",
            evidence={
                "total_candidates": len(evaluated_candidates),
                "pareto_front": tradeoff.pareto_front,
                "recommended": tradeoff.recommendation,
            },
            confidence=0.80,
            timestamp=datetime.now().isoformat(),
        ))

        selected_candidate = (
            evaluated_candidates[tradeoff.recommendation]
            if tradeoff.recommendation >= 0
            else evaluated_candidates[0] if evaluated_candidates else None
        )

        risk = self._risk_assessor.assess(selected_candidate, perception_report) if selected_candidate else RiskAssessment()
        reasoning.append(ReasoningStep(
            step_id=4, phase="risk_assessment",
            conclusion=f"风险评估: {risk.level.value} (得分{risk.score:.1f})",
            evidence=risk.details,
            confidence=0.78,
            timestamp=datetime.now().isoformat(),
        ))

        full_tradeoff = self._tradeoff_analyzer.analyze(evaluated_candidates, self._engine._criteria)
        reasoning.append(ReasoningStep(
            step_id=5, phase="tradeoff_analysis",
            conclusion=f"Trade-off分析完成，推荐方案#{full_tradeoff.recommendation + 1}",
            evidence={"matrix_summary": full_tradeoff.comparison_data.get("summary", {})},
            confidence=0.82,
            timestamp=datetime.now().isoformat(),
        ))

        strategy = self._strategy_selector.select(task_cat, risk, perception_report)
        reasoning.append(ReasoningStep(
            step_id=6, phase="strategy_selection",
            conclusion=f"选择策略: {strategy.value}",
            evidence={
                "task_category": task_cat.value,
                "risk_level": risk.level.value,
            },
            confidence=0.76,
            timestamp=datetime.now().isoformat(),
        ))

        exec_plan = self._generate_execution_plan(selected_candidate, risk, strategy)
        overall_confidence = statistics.mean([r.confidence for r in reasoning])

        return Decision(
            decision_id=f"DEC-{self._decision_counter:04d}",
            timestamp=now,
            task_category=task_cat,
            selected_action=selected_candidate,
            strategy=strategy,
            risk_assessment=risk,
            trade_off=full_tradeoff,
            reasoning_chain=reasoning,
            confidence=round(overall_confidence, 3),
            alternatives=[c for c in evaluated_candidates if c is not selected_candidate][:5],
            execution_plan=exec_plan,
            metadata={
                "perception_confidence": getattr(perception_report, 'confidence_level', 0),
                "candidates_evaluated": len(evaluated_candidates),
            },
        )

    @staticmethod
    def _classify_task(task_description: str) -> TaskCategory:
        lower_desc = task_description.lower()
        keywords: dict[TaskCategory, list[str]] = {
            TaskCategory.BUG_FIX: ["bug", "fix", "error", "issue", "defect", "crash", "故障", "修复"],
            TaskCategory.REFACTORING: ["refactor", "restructure", "clean", "重构", "优化代码"],
            TaskCategory.FEATURE_ADD: ["feature", "new", "add", "implement", "功能", "新增"],
            TaskCategory.PERFORMANCE_OPT: ["performance", "speed", "optimize", "slow", "性能", "加速"],
            TaskCategory.SECURITY_FIX: ["security", "vuln", "inject", "auth", "安全", "漏洞"],
            TaskCategory.TEST_ADDITION: ["test", "spec", "coverage", "测试", "用例"],
            TaskCategory.DOCUMENTATION: ["doc", "readme", "comment", "文档", "注释"],
            TaskCategory.DEPENDENCY_UPDATE: ["depend", "upgrade", "version", "依赖", "升级"],
            TaskCategory.CODE_REVIEW: ["review", "lint", "check", "审查", "检查"],
        }

        scores: dict[TaskCategory, int] = {}
        for cat, kws in keywords.items():
            scores[cat] = sum(1 for kw in kws if kw in lower_desc)

        best_cat = max(scores, key=scores.get) if scores else TaskCategory.GENERAL
        if scores.get(best_cat, 0) == 0:
            return TaskCategory.GENERAL
        return best_cat

    def _generate_candidates(
        self, report: Any, category: TaskCategory
    ) -> list[CandidateAction]:
        target_files = [ctx.file_path for ctx in report.code_contexts[:5]] if hasattr(report, 'code_contexts') else []
        templates = self._get_candidate_templates(category, target_files)
        candidates: list[CandidateAction] = []
        for tpl in templates:
            candidates.append(CandidateAction(**tpl))
        return candidates if candidates else [CandidateAction(
            action_id="ACT-default",
            description="默认方案：直接实施最小变更",
            category=category.value,
            estimated_effort=2.0,
            risk_level=RiskLevel.LOW,
            affected_files=target_files[:2],
        )]

    @staticmethod
    def _get_candidate_templates(category: TaskCategory, files: list[str]) -> list[dict[str, Any]]:
        common = {
            "category": category.value,
            "affected_files": files[:3],
            "prerequisites": [],
        }
        match category:
            case TaskCategory.BUG_FIX:
                return [
                    {**common, "action_id": "ACT-targeted-fix", "description": "精准定位并修复根因", "estimated_effort": 2.0, "risk_level": RiskLevel.LOW},
                    {**common, "action_id": "ACT-comprehensive-fix", "description": "全面排查同类问题一并修复", "estimated_effort": 5.0, "risk_level": RiskLevel.MEDIUM},
                    {**complete, "action_id": "ACT-defensive-fix", "description": "防御式编程+边界检查加固", "estimated_effort": 3.5, "risk_level": RiskLevel.LOW},
                ]
            case TaskCategory.REFACTORING:
                return [
                    {**common, "action_id": "ACT-incremental-refactor", "description": "渐进式小步重构", "estimated_effort": 4.0, "risk_level": RiskLevel.LOW},
                    {**common, "action_id": "ACT-systematic-refactor", "description": "系统性架构级重构", "estimated_effort": 8.0, "risk_level": RiskLevel.HIGH},
                    {**common, "action_id": "ACT-extract-module", "description": "提取独立模块解耦", "estimated_effort": 6.0, "risk_level": RiskLevel.MEDIUM},
                ]
            case TaskCategory.FEATURE_ADD:
                return [
                    {**common, "action_id": "ACT-minimal-mvp", "description": "最小可行实现(MVP)", "estimated_effort": 3.0, "risk_level": RiskLevel.LOW},
                    {**common, "action_id": "ACT-full-feature", "description": "完整功能实现含边界处理", "estimated_effort": 7.0, "risk_level": RiskLevel.MEDIUM},
                    {**common, "action_id": "ACT-feature-with-tests", "description": "功能实现+完整测试套件", "estimated_effort": 9.0, "risk_level": RiskLevel.LOW},
                ]
            case _:
                return [
                    {**common, "action_id": "ACT-standard", "description": "标准实施方案", "estimated_effort": 3.0, "risk_level": RiskLevel.MEDIUM},
                    {**common, "action_id": "ACT-conservative", "description": "保守方案：最小改动", "estimated_effort": 1.5, "risk_level": RiskLevel.LOW},
                    {**common, "action_id": "ACT-thorough", "description": "彻底方案：全面考虑", "estimated_effort": 6.0, "risk_level": RiskLevel.MEDIUM},
                ]

    @staticmethod
    def _generate_execution_plan(
        action: CandidateAction | None,
        risk: RiskAssessment,
        strategy: StrategyType,
    ) -> list[dict[str, Any]]:
        plan: list[dict[str, Any]] = []
        if action is None:
            return plan

        plan.append({"step": 1, "phase": "preparation", "action": "创建工作分支", "priority": "high"})
        plan.append({"step": 2, "phase": "backup", "action": "备份受影响文件", "priority": "high"})

        if strategy in (StrategyType.CONSERVATIVE,):
            plan.append({"step": 3, "phase": "analysis", "action": "深度代码审查与影响分析", "priority": "high"})
            plan.append({"step": 4, "phase": "implementation", "action": "增量式安全修改", "priority": "high"})
            plan.append({"step": 5, "phase": "validation", "action": "全量测试+人工验证", "priority": "critical"})
        elif strategy == StrategyType.AGGRESSIVE:
            plan.append({"step": 3, "phase": "implementation", "action": "快速实现核心变更", "priority": "high"})
            plan.append({"step": 4, "phase": "validation", "action": "自动化测试验证", "priority": "high"})
        else:
            plan.append({"step": 3, "phase": "implementation", "action": "按计划逐步实施变更", "priority": "high"})
            plan.append({"step": 4, "phase": "validation", "action": "分层验证(语法→类型→单元→集成)", "priority": "high"})

        if risk.level in (RiskLevel.HIGH, RiskLevel.CRITICAL):
            plan.append({"step": len(plan) + 1, "phase": "monitoring", "action": "部署后持续监控", "priority": "high"})
            plan.append({"step": len(plan) + 1, "phase": "rollback_prep", "action": "确认回滚就绪状态", "priority": "critical"})

        return plan


if __name__ == "__main__":
    print("=" * 65)
    print("🧭 自主决策层 (Decide Layer) - 功能演示")
    print("=" * 65)

    engine = MultiCriteriaDecisionEngine()

    demo_candidates = [
        CandidateAction(
            action_id="ACT-A", description="精准修复方案A",
            estimated_effort=2.0, risk_level=RiskLevel.LOW,
            affected_files=["module_a.py"], metadata={"effectiveness_modifier": 10},
        ),
        CandidateAction(
            action_id="ACT-B", description="全面重构方案B",
            estimated_effort=8.0, risk_level=RiskLevel.HIGH,
            affected_files=["module_a.py", "module_b.py", "core.py"],
            metadata={"effectiveness_modifier": 20, "maintainability_modifier": 15},
        ),
        CandidateAction(
            action_id="ACT-C", description="平衡改进方案C",
            estimated_effort=4.0, risk_level=RiskLevel.MEDIUM,
            affected_files=["module_a.py", "utils.py"],
            metadata={"effectiveness_modifier": 12, "safety_modifier": 5},
        ),
        CandidateAction(
            action_id="ACT-D", description="快速补丁方案D",
            estimated_effort=1.0, risk_level=RiskLevel.LOW,
            affected_files=["module_a.py"],
            metadata={"efficiency_modifier": 15},
        ),
    ]

    print("\n--- 多准则决策引擎 ---")
    evaluated, matrix = engine.evaluate(demo_candidates)
    print(f"   候选方案数: {len(evaluated)}")
    print(f"   Pareto前沿: {[evaluated[i].action_id for i in matrix.pareto_front]}")
    print(f"   推荐方案: #{matrix.recommendation + 1} - {evaluated[matrix.recommendation].action_id}")
    for cand in evaluated:
        ws = sum(cand.scores.get(c.name, 0) * c.weight for c in engine._criteria if c.direction == "maximize")
        ws -= sum(cand.scores.get(c.name, 0) * c.weight for c in engine._criteria if c.direction == "minimize")
        print(f"      {cand.action_id}: 加权分={ws:.1f}, 风险={cand.risk_level.value}, 工作量={cand.estimated_effort}")

    print("\n--- 敏感性分析 ---")
    sens = engine.sensitivity_analysis(demo_candidates)
    print(f"   结果稳定性: {'稳定' if sens['stable_rankings'] else '不稳定'}")
    if sens['changes']:
        for change in sens['changes']:
            print(f"      ⚠️ {change['criterion']} 权重{change['weight_change']} → 最佳变为 {change['new_best']}")

    print("\n--- 风险评估 ---")
    assessor = RiskAssessor()
    for cand in demo_candidates:
        risk = assessor.assess(cand)
        icon = {"LOW": "🟢", "MEDIUM": "🟡", "HIGH": "🟠", "CRITICAL": "🔴"}[risk.level.value]
        print(f"   {icon} {cand.action_id}: {risk.level.value.upper()} ({risk.score:.1f}/100)")
        print(f"      影响范围: {risk.impact_scope}")
        print(f"      回滚难度: {risk.rollback_difficulty}")
        if risk.side_effects:
            print(f"      潜在副作用: {risk.side_effects[:3]}")

    print("\n--- Trade-off分析 ---")
    analyzer = TradeOffAnalyzer()
    full_matrix = analyzer.analyze(demo_candidates, engine._criteria)
    summary = full_matrix.comparison_data.get("summary", {})
    print(f"   总候选数: {summary.get('total_candidates')}")
    print(f"   Pareto前沿大小: {summary.get('pareto_front_size')}")
    print(f"   推荐: {summary.get('recommended_action')}")

    print("\n--- 策略选择 ---")
    selector = StrategySelector()
    test_combinations = [
        (TaskCategory.BUG_FIX, RiskLevel.LOW),
        (TaskCategory.SECURITY_FIX, RiskLevel.CRITICAL),
        (TaskCategory.FEATURE_ADD, RiskLevel.LOW),
        (TaskCategory.REFACTORING, RiskLevel.HIGH),
        (TaskCategory.DOCUMENTATION, RiskLevel.LOW),
    ]
    for cat, rlevel in test_combinations:
        strat = selector.select(cat, RiskAssessment(level=rlevel))
        print(f"   {cat.value:20s} + {rlevel.value:10s} → {strat.value}")

    print("\n--- 完整决策流程 ---")
    from perceive_layer import PerceptionReport, PerceiveLayer
    layer = DecideLayer()
    fake_report = PerceptionReport(
        timestamp=datetime.now().isoformat(),
        project_root="/demo/project",
        task_description="修复用户认证模块中的SQL注入漏洞",
        confidence_level=0.75,
    )
    decision = layer.decide(fake_report)
    print(decision.to_dict())

    print("\n   推理链:")
    for rs in decision.reasoning_chain:
        print(f"      Step[{rs.step_id}] ({rs.phase}): {rs.conclusion} [置信度:{rs.confidence:.2f}]")

    print("\n   执行计划:")
    for ep in decision.execution_plan:
        pri = {"high": "🔵", "critical": "🔴"}.get(ep.get("priority", ""), "⚪")
        print(f"      {pri} Step{ep['step']}: [{ep['phase']}] {ep['action']}")

    print("\n✅ 所有决策层测试通过!")
