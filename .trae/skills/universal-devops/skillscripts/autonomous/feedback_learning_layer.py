"""
反馈学习层 (Feedback & Learning Layer)
=======================================
从执行结果中学习，持续优化自主决策和执行能力。
包含四个核心能力：
- 结果验证：对比预期vs实际结果
- 模式积累：成功/失败模式记录到知识库
- 策略调优：根据成功率调整策略权重
- 知识提炼：从操作序列中提炼可复用经验
"""
from __future__ import annotations

import json
import math
import statistics
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum, auto
from pathlib import Path
from typing import Any


class LearningError(Exception):
    """反馈学习层相关异常"""
    pass


class OutcomeType(str, Enum):
    """操作结果类型"""
    SUCCESS = "success"
    PARTIAL_SUCCESS = "partial_success"
    FAILURE = "failure"
    ROLLED_BACK = "rolled_back"


class PatternCategory(str, Enum):
    """模式类别"""
    SUCCESS_PATTERN = "success_pattern"
    FAILURE_PATTERN = "failure_pattern"
    ANTI_PATTERN = "anti_pattern"
    BEST_PRACTICE = "best_practice"


@dataclass
class VerificationResult:
    """验证对比结果"""
    expected_outcome: str = ""
    actual_outcome: str = ""
    outcome_match: bool = True
    match_score: float = 1.0
    discrepancies: list[dict[str, Any]] = field(default_factory=list)
    improvements: list[str] = field(default_factory=list)
    regressions: list[str] = field(default_factory=list)
    quality_delta: dict[str, float] = field(default_factory=dict)


@dataclass
class KnowledgeEntry:
    """知识库条目"""
    entry_id: str = ""
    category: PatternCategory = PatternCategory.SUCCESS_PATTERN
    title: str = ""
    description: str = ""
    context_tags: list[str] = field(default_factory=list)
    task_type: str = ""
    strategy_used: str = ""
    risk_level: str = ""
    effectiveness_score: float = 0.0
    confidence: float = 0.5
    source_execution_id: str = ""
    created_at: str = ""
    updated_at: str = ""
    application_count: int = 0
    success_count: int = 0
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "entry_id": self.entry_id,
            "category": self.category.value,
            "title": self.title,
            "task_type": self.task_type,
            "strategy": self.strategy_used,
            "effectiveness": round(self.effectiveness_score, 3),
            "confidence": round(self.confidence, 3),
            "applications": self.application_count,
            "success_rate": round(self.success_count / max(self.application_count, 1), 3),
        }


@dataclass
class StrategyProfile:
    """策略画像"""
    strategy_name: str = ""
    total_uses: int = 0
    success_count: int = 0
    failure_count: int = 0
    avg_confidence: float = 0.0
    avg_effort: float = 0.0
    avg_risk_score: float = 0.0
    success_rate: float = 0.0
    weight_adjustment: float = 0.0
    trend: str = "stable"
    recent_results: list[bool] = field(default_factory=list)

    @property
    def is_reliable(self) -> bool:
        return self.total_uses >= 5 and self.success_rate >= 0.6

    def recalculate(self) -> None:
        self.success_rate = self.success_count / max(self.total_uses, 1)
        if len(self.recent_results) >= 5:
            recent_sr = sum(self.recent_results[-5:]) / 5
            if recent_sr > self.success_rate + 0.15:
                self.trend = "improving"
            elif recent_sr < self.success_rate - 0.15:
                self.trend = "declining"
            else:
                self.trend = "stable"


@dataclass
class DistilledExperience:
    """
    提炼的经验
    
    从完整的操作序列中抽象出的可复用经验模板。
    """
    experience_id: str = ""
    name: str = ""
    scenario: str = ""
    preconditions: list[str] = field(default_factory=list)
    action_sequence: list[dict[str, str]] = field(default_factory=list)
    expected_outcome: str = ""
    anti_patterns: list[str] = field(default_factory=list)
    lessons_learned: list[str] = field(default_factory=list)
    applicability_scope: list[str] = field(default_factory=list)
    effectiveness_estimate: float = 0.0
    source_executions: list[str] = field(default_factory=list)
    created_at: str = ""
    usage_count: int = 0


@dataclass
class LearningInsight:
    """
    学习洞察 - 反馈学习层的统一输出
    
    汇总验证结果、模式更新、策略调整、经验提炼等所有学习产出。
    """
    insight_id: str = ""
    timestamp: str = ""
    execution_id: str = ""
    verification: VerificationResult = field(default_factory=VerificationResult)
    new_patterns: list[KnowledgeEntry] = field(default_factory=list)
    updated_strategies: list[StrategyProfile] = field(default_factory=list)
    distilled_experiences: list[DistilledExperience] = field(default_factory=list)
    recommendations: list[str] = field(default_factory=list)
    metrics: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "insight_id": self.insight_id,
            "timestamp": self.timestamp,
            "execution_id": self.execution_id,
            "outcome_match": self.verification.outcome_match,
            "match_score": round(self.verification.match_score, 3),
            "new_patterns": len(self.new_patterns),
            "updated_strategies": len(self.updated_strategies),
            "distilled_experiences": len(self.distilled_experiences),
            "recommendations": len(self.recommendations),
        }


class ResultVerifier:
    """
    结果验证器
    
    对比执行的实际结果与决策的预期目标，
    识别偏差、发现改进机会、检测潜在回归。
    """

    def verify(
        self,
        execution_result: Any,
        perception_report: Any,
        decision: Any,
    ) -> VerificationResult:
        """
        执行完整的结果验证
        
        Args:
            execution_result: 执行层的ExecutionResult
            perception_report: 感知层的PerceptionReport
            decision: 决策层的Decision
            
        Returns:
            VerificationResult对象
        """
        result = VerificationResult()
        exec_status = getattr(execution_result, 'status', None)
        selected_action = getattr(decision, 'selected_action', None)

        expected = self._build_expected_outcome(decision, perception_report)
        actual = self._build_actual_outcome(execution_result)
        result.expected_outcome = expected
        result.actual_outcome = actual

        result.discrepancies = self._find_discrepancies(expected, actual, decision)
        result.quality_delta = self._compute_quality_delta(perception_report, execution_result)
        result.improvements = self._detect_improvements(result.quality_delta)
        result.regressions = self._detect_regressions(result.quality_delta)

        base_score = 1.0
        for disc in result.discrepancies:
            severity = disc.get("severity", "low")
            penalty = {"low": 0.05, "medium": 0.15, "high": 0.30, "critical": 0.50}.get(severity, 0.10)
            base_score -= penalty

        for reg in result.regressions:
            base_score -= 0.10

        result.match_score = max(0.0, min(1.0, base_score))
        result.outcome_match = result.match_score >= 0.7

        return result

    @staticmethod
    def _build_expected_outcome(decision: Any, report: Any) -> str:
        parts: list[str] = []
        action = getattr(decision, 'selected_action', None)
        if action:
            parts.append(f"方案:{action.action_id}")
            parts.append(f"描述:{action.description[:60]}")
        risk = getattr(decision, 'risk_assessment', None)
        if risk:
            parts.append(f"预期风险:{risk.level.value}")
        strategy = getattr(decision, 'strategy', None)
        if strategy:
            parts.append(f"策略:{strategy.value}")
        plan = getattr(decision, 'execution_plan', None)
        if plan:
            parts.append(f"计划步骤:{len(plan)}")
        return " | ".join(parts) if parts else "无明确预期"

    @staticmethod
    def _build_actual_outcome(exec_result: Any) -> str:
        parts: list[str] = []
        status = getattr(exec_result, 'status', None)
        if status:
            parts.append(f"状态:{status.value}")
        ops = getattr(exec_result, 'operations', None)
        if ops:
            parts.append(f"操作数:{len(ops)}")
        validation = getattr(exec_result, 'validation', None)
        if validation and hasattr(validation, 'overall_pass'):
            parts.append(f"验证:{'通过' if validation.overall_pass else '未通过'}")
        error = getattr(exec_result, 'error_message', '')
        if error:
            parts.append(f"错误:{error[:50]}")
        metrics = getattr(exec_result, 'metrics', None)
        if metrics:
            impact = metrics.get('impact_score', 0)
            parts.append(f"影响分:{impact:.1f}")
        return " | ".join(parts) if parts else "未知实际结果"

    @staticmethod
    def _find_discrepancies(expected: str, actual: str, decision: Any) -> list[dict[str, Any]]:
        discrepancies: list[dict[str, Any]] = []
        risk = getattr(decision, 'risk_assessment', None)
        expected_risk = risk.level.value if risk else "unknown"

        if "failed" in actual.lower() or "FAILED" in actual:
            discrepancies.append({
                "type": "execution_failure",
                "severity": "high",
                "message": "执行过程中出现失败",
                "expected": "成功完成",
                "actual": actual,
            })

        if "CRITICAL" in expected_risk and ("completed" in actual.lower() or "COMPLETED" in actual):
            discrepancies.append({
                "type": "risk_mismatch",
                "severity": "info",
                "message": "高风险任务意外顺利执行",
                "expected": f"风险{expected_risk}，可能遇到困难",
                "actual": "顺利完成",
            })

        validation_phrase = "验证:通过"
        if validation_phrase not in actual and "completed" in actual.lower():
            discrepancies.append({
                "type": "validation_skipped",
                "severity": "medium",
                "message": "完成但可能跳过了验证",
                "expected": "通过完整验证",
                "actual": actual,
            })

        return discrepancies

    @staticmethod
    def _compute_quality_delta(report: Any, exec_result: Any) -> dict[str, float]:
        delta: dict[str, float] = {}
        try:
            q_before = report.quality_snapshot.overall_score if hasattr(report, 'quality_snapshot') else 50.0
            impact = exec_result.impact_report.overall_risk_score if hasattr(exec_result, 'impact_report') else 0
            delta["overall"] = round(-impact * 0.1 + (1 if exec_result.status.value == "completed" else -5), 2)
            delta["code_quality"] = round(delta.get("overall", 0) * 0.8, 2)
            delta["testability"] = round(len(getattr(exec_result, 'operations', [])) * 0.5, 2)
        except Exception:
            delta["overall"] = 0.0
        return delta

    @staticmethod
    def _detect_improvements(delta: dict[str, float]) -> list[str]:
        improvements: list[str] = []
        for key, value in delta.items():
            if value > 2:
                label = {"overall": "综合质量", "code_quality": "代码质量", "testability": "可测试性"}.get(key, key)
                improvements.append(f"{label}提升+{value:.1f}")
        return improvements

    @staticmethod
    def _detect_regressions(delta: dict[str, float]) -> list[str]:
        regressions: list[str] = []
        for key, value in delta.items():
            if value < -3:
                label = {"overall": "综合质量", "code_quality": "代码质量", "testability": "可测试性"}.get(key, key)
                regressions.append(f"{label}回退{value:.1f}")
        return regressions


class PatternAccumulator:
    """
    模式积累器
    
    将每次操作的成败经验记录到知识库中，
    支持按类别、任务类型、策略等维度检索和应用。
    """

    def __init__(self, knowledge_base_path: Path | str | None = None) -> None:
        if knowledge_base_path is None:
            self._kb_path = Path(".aof_knowledge_base.json")
        else:
            self._kb_path = Path(knowledge_base_path)
        self._entries: list[KnowledgeEntry] = []
        self._entry_counter: int = 0
        self._load_knowledge_base()

    def accumulate(
        self,
        execution_result: Any,
        verification: VerificationResult,
        decision: Any,
    ) -> list[KnowledgeEntry]:
        """
        从执行结果中提取并记录模式
        
        Args:
            execution_result: 执行结果
            verification: 验证结果
            decision: 决策对象
            
        Returns:
            新创建的知识条目列表
        """
        new_entries: list[KnowledgeEntry] = []

        outcome_type = self._determine_outcome_type(execution_result, verification)
        entry = self._create_entry(outcome_type, execution_result, verification, decision)
        if entry:
            new_entries.append(entry)
            self._entries.append(entry)

        if verification.match_score < 0.5:
            anti_entry = self._create_anti_pattern(execution_result, verification, decision)
            if anti_entry:
                new_entries.append(anti_entry)
                self._entries.append(anti_entry)

        if verification.match_score > 0.9:
            bp_entry = self._create_best_practice(execution_result, verification, decision)
            if bp_entry:
                new_entries.append(bp_entry)
                self._entries.append(bp_entry)

        self._save_knowledge_base()
        return new_entries

    def query(
        self,
        task_type: str = "",
        strategy: str = "",
        category: PatternCategory | None = None,
        min_confidence: float = 0.0,
        limit: int = 20,
    ) -> list[KnowledgeEntry]:
        """
        查询知识库
        
        Args:
            task_type: 任务类型过滤
            strategy: 策略过滤
            category: 类别过滤
            min_confidence: 最小置信度
            limit: 返回条数上限
            
        Returns:
            匹配的知识条目列表
        """
        results: list[KnowledgeEntry] = []
        for entry in self._entries:
            if task_type and entry.task_type != task_type:
                continue
            if strategy and entry.strategy_used != strategy:
                continue
            if category and entry.category != category:
                continue
            if entry.confidence < min_confidence:
                continue
            results.append(entry)
        return sorted(results, key=lambda e: (-e.effectiveness_score, -e.confidence))[:limit]

    def get_statistics(self) -> dict[str, Any]:
        """获取知识库统计信息"""
        total = len(self._entries)
        by_category: dict[str, int] = {}
        by_task: dict[str, int] = {}
        by_strategy: dict[str, int] = {}
        avg_effectiveness: list[float] = []

        for entry in self._entries:
            by_category[entry.category.value] = by_category.get(entry.category.value, 0) + 1
            by_task[entry.task_type] = by_task.get(entry.task_type, 0) + 1
            by_strategy[entry.strategy_used] = by_strategy.get(entry.strategy_used, 0) + 1
            avg_effectiveness.append(entry.effectiveness_score)

        return {
            "total_entries": total,
            "by_category": by_category,
            "by_task_type": by_task,
            "by_strategy": by_strategy,
            "avg_effectiveness": round(statistics.mean(avg_effectiveness), 3) if avg_effectiveness else 0,
            "high_confidence_count": sum(1 for e in self._entries if e.confidence >= 0.8),
        }

    def _determine_outcome_type(self, exec_result: Any, verification: VerificationResult) -> OutcomeType:
        status = getattr(exec_result, 'status', None)
        status_val = status.value if status else "unknown"
        if status_val in ("completed",):
            return OutcomeType.SUCCESS if verification.outcome_match else OutcomeType.PARTIAL_SUCCESS
        elif status_val == "partial":
            return OutcomeType.PARTIAL_SUCCESS
        elif status_val == "rolled_back":
            return OutcomeType.ROLLED_BACK
        else:
            return OutcomeType.FAILURE

    def _create_entry(
        self,
        outcome: OutcomeType,
        exec_result: Any,
        verification: VerificationResult,
        decision: Any,
    ) -> KnowledgeEntry | None:
        self._entry_counter += 1
        now = datetime.now().isoformat()

        cat_map = {
            OutcomeType.SUCCESS: PatternCategory.SUCCESS_PATTERN,
            OutcomeType.PARTIAL_SUCCESS: PatternCategory.SUCCESS_PATTERN,
            OutcomeType.FAILURE: PatternCategory.FAILURE_PATTERN,
            OutcomeType.ROLLED_BACK: PatternCategory.FAILURE_PATTERN,
        }

        action = getattr(decision, 'selected_action', None)
        risk = getattr(decision, 'risk_assessment', None)

        tags = [
            getattr(decision, 'task_category', None).value if hasattr(decision, 'task_category') and getattr(decision, 'task_category') else "general",
            outcome.value,
            risk.level.value if risk else "unknown",
        ]

        return KnowledgeEntry(
            entry_id=f"KB-{self._entry_counter:04d}",
            category=cat_map.get(outcome, PatternCategory.SUCCESS_PATTERN),
            title=f"{outcome.value.replace('_', ' ').title()}: {action.action_id if action else 'unknown'}",
            description=verification.actual_outcome[:200],
            context_tags=tags,
            task_type=getattr(decision, 'task_category', type('', (), {'value': 'general'})).value if hasattr(decision, 'task_category') else "general",
            strategy_used=getattr(decision, 'strategy', type('', (), {'value': 'unknown'})).value if hasattr(decision, 'strategy') else "unknown",
            risk_level=risk.level.value if risk else "unknown",
            effectiveness_score=round(verification.match_score, 4),
            confidence=min(1.0, 0.3 + verification.match_score * 0.5 + (1.0 if outcome == OutcomeType.SUCCESS else 0)),
            source_execution_id=getattr(exec_result, 'execution_id', ''),
            created_at=now,
            updated_at=now,
            application_count=1,
            success_count=1 if outcome in (OutcomeType.SUCCESS,) else 0,
            metadata={
                "outcome": outcome.value,
                "match_score": verification.match_score,
                "discrepancy_count": len(verification.discrepancies),
                "operations_count": len(getattr(exec_result, 'operations', [])),
            },
        )

    def _create_anti_pattern(
        self, exec_result: Any, verification: VerificationResult, decision: Any
    ) -> KnowledgeEntry | None:
        if not verification.discrepancies:
            return None
        self._entry_counter += 1
        now = datetime.now().isoformat()
        action = getattr(decision, 'selected_action', None)
        return KnowledgeEntry(
            entry_id=f"KB-{self._entry_counter:04d}",
            category=PatternCategory.ANTI_PATTERN,
            title=f"反模式: {action.description[:50] if action else 'unknown'}",
            description="; ".join(d["message"] for d in verification.discrepancies[:3]),
            context_tags=["anti_pattern", "warning"],
            task_type=getattr(decision, 'task_category', type('', (), {'value': 'general'})).value if hasattr(decision, 'task_category') else "general",
            strategy_used=getattr(decision, 'strategy', type('', (), {'value': 'unknown'})).value if hasattr(decision, 'strategy') else "unknown",
            effectiveness_score=round(verification.match_score, 4),
            confidence=0.6,
            source_execution_id=getattr(exec_result, 'execution_id', ''),
            created_at=now,
            updated_at=now,
            metadata={"source": "auto_detected_from_discrepancies"},
        )

    def _create_best_practice(
        self, exec_result: Any, verification: VerificationResult, decision: Any
    ) -> KnowledgeEntry | None:
        self._entry_counter += 1
        now = datetime.now().isoformat()
        action = getattr(decision, 'selected_action', None)
        return KnowledgeEntry(
            entry_id=f"KB-{self._entry_counter:04d}",
            category=PatternCategory.BEST_PRACTICE,
            title=f"最佳实践: {action.action_id if action else 'excellent_execution'}",
            description=f"高匹配度执行 ({verification.match_score:.1%})，建议复用此方案模式",
            context_tags=["best_practice", "recommended"],
            task_type=getattr(decision, 'task_category', type('', (), {'value': 'general'})).value if hasattr(decision, 'task_category') else "general",
            strategy_used=getattr(decision, 'strategy', type('', (), {'value': 'unknown'})).value if hasattr(decision, 'strategy') else "unknown",
            effectiveness_score=round(verification.match_score, 4),
            confidence=0.9,
            source_execution_id=getattr(exec_result, 'execution_id', ''),
            created_at=now,
            updated_at=now,
            metadata={"source": "auto_detected_high_match"},
        )

    def _load_knowledge_base(self) -> None:
        if not self._kb_path.exists():
            return
        try:
            data = json.loads(self._kb_path.read_text(encoding="utf-8"))
            entries_data = data.get("entries", [])
            for ed in entries_data:
                try:
                    entry = KnowledgeEntry(**{
                        k: v for k, v in ed.items()
                        if k in KnowledgeEntry.__dataclass_fields__
                    })
                    self._entries.append(entry)
                except Exception:
                    continue
            max_id = 0
            for e in self._entries:
                try:
                    num = int(e.entry_id.split("-")[1])
                    max_id = max(max_id, num)
                except (ValueError, IndexError):
                    pass
            self._entry_counter = max_id
        except (json.JSONDecodeError, Exception):
            pass

    def _save_knowledge_base(self) -> None:
        try:
            data = {
                "version": "1.0",
                "updated_at": datetime.now().isoformat(),
                "total_entries": len(self._entries),
                "entries": [e.to_dict() for e in self._entries],
            }
            self._kb_path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
        except Exception:
            pass


class StrategyTuner:
    """
    策略调优器
    
    根据历史执行的成功率动态调整各策略的权重和推荐优先级，
    实现持续的自我优化。
    """

    def __init__(self) -> None:
        self._profiles: dict[str, StrategyProfile] = {}
        self._history: list[dict[str, Any]] = []
        self._initialize_default_profiles()

    def _initialize_default_profiles(self) -> None:
        default_strategies = [
            "conservative", "balanced", "aggressive",
            "automated", "manual", "hybrid",
        ]
        for s in default_strategies:
            self._profiles[s] = StrategyProfile(strategy_name=s)

    def tune(
        self,
        execution_result: Any,
        verification: VerificationResult,
        decision: Any,
    ) -> list[StrategyProfile]:
        """
        根据执行结果调优策略
        
        Args:
            execution_result: 执行结果
            verification: 验证结果
            decision: 决策对象
            
        Returns:
            更新后的策略画像列表
        """
        strategy_name = getattr(decision, 'strategy', type('', (), {'value': 'balanced'})).value if hasattr(decision, 'strategy') else "balanced"
        is_success = verification.outcome_match and getattr(execution_result, 'status', type('', (), {'value': ''})).value in ("completed",)

        profile = self._get_or_create_profile(strategy_name)
        profile.total_uses += 1
        profile.success_count += 1 if is_success else 0
        profile.failure_count += 0 if is_success else 1
        profile.recent_results.append(is_success)
        if len(profile.recent_results) > 20:
            profile.recent_results.pop(0)

        profile.avg_confidence = (
            profile.avg_confidence * (profile.total_uses - 1) + getattr(decision, 'confidence', 0.5)
        ) / profile.total_uses

        effort = getattr(getattr(decision, 'selected_action', None), 'estimated_effort', 3.0) or 3.0
        profile.avg_effort = (
            profile.avg_effort * (profile.total_uses - 1) + effort
        ) / profile.total_uses

        risk_score = getattr(getattr(decision, 'risk_assessment', None), 'score', 30.0) or 30.0
        profile.avg_risk_score = (
            profile.avg_risk_score * (profile.total_uses - 1) + risk_score
        ) / profile.total_uses

        profile.recalculate()
        profile.weight_adjustment = self._compute_weight_adjustment(profile)
        profile.updated_at = datetime.now().isoformat()

        self._history.append({
            "timestamp": datetime.now().isoformat(),
            "strategy": strategy_name,
            "success": is_success,
            "match_score": verification.match_score,
            "execution_id": getattr(execution_result, 'execution_id', ''),
        })

        return self.get_all_profiles()

    def get_all_profiles(self) -> list[StrategyProfile]:
        """获取所有策略画像"""
        return sorted(self._profiles.values(), key=lambda p: (-p.success_rate, -p.total_uses))

    def get_recommendation(self, task_type: str = "") -> StrategyProfile | None:
        """
        获取当前最优策略推荐
        
        Args:
            task_type: 任务类型（可选，用于更精准推荐）
            
        Returns:
            推荐的策略画像
        """
        reliable = [p for p in self._profiles.values() if p.is_reliable]
        if reliable:
            return max(reliable, key=lambda p: p.success_rate)
        active = [p for p in self._profiles.values() if p.total_uses > 0]
        if active:
            return max(active, key=lambda p: p.success_rate)
        return self._profiles.get("balanced")

    def _get_or_create_profile(self, name: str) -> StrategyProfile:
        if name not in self._profiles:
            self._profiles[name] = StrategyProfile(strategy_name=name)
        return self._profiles[name]

    @staticmethod
    def _compute_weight_adjustment(profile: StrategyProfile) -> float:
        base = 0.0
        sr_bonus = (profile.success_rate - 0.5) * 20
        trend_bonus = {"improving": 5, "stable": 0, "declining": -5}.get(profile.trend, 0)
        volume_bonus = min(5, profile.total_uses * 0.1)
        confidence_bonus = (profile.avg_confidence - 0.5) * 10
        base += sr_bonus + trend_bonus + volume_bonus + confidence_bonus
        return round(max(-25, min(25, base)), 2)


class KnowledgeDistiller:
    """
    知识提炼器
    
    从多个相似的操作序列中提炼出通用的、可复用的经验模板。
    支持场景匹配、经验组合、效果评估等高级功能。
    """

    def __init__(self) -> None:
        self._experiences: list[DistilledExperience] = []
        self._experience_counter: int = 0

    def distill(
        self,
        recent_executions: list[tuple[Any, Any, Any]],
        pattern_accumulator: PatternAccumulator,
    ) -> list[DistilledExperience]:
        """
        从最近的执行序列中提炼经验
        
        Args:
            recent_executions: (exec_result, verification, decision) 元组列表
            pattern_accumulator: 模式积累器（用于关联已有知识）
            
        Returns:
            新提炼的经验列表
        """
        new_experiences: list[DistilledExperience] = []

        grouped = self._group_by_scenario(recent_executions)
        for scenario, group in grouped.items():
            if len(group) < 2:
                continue
            experience = self._distill_from_group(scenario, group, pattern_accumulator)
            if experience:
                new_experiences.append(experience)
                self._experiences.append(experience)

        return new_experiences

    def query_experiences(
        self,
        scenario_keyword: str = "",
        min_effectiveness: float = 0.0,
        limit: int = 10,
    ) -> list[DistilledExperience]:
        """
        查询已提炼的经验
        
        Args:
            scenario_keyword: 场景关键词
            min_effectiveness: 最小有效性估计
            limit: 返回数量上限
            
        Returns:
            匹配的经验列表
        """
        results: list[DistilledExperience] = []
        for exp in self._experiences:
            if scenario_keyword and scenario_keyword.lower() not in exp.scenario.lower():
                continue
            if exp.effectiveness_estimate < min_effectiveness:
                continue
            results.append(exp)
        return sorted(results, key=lambda e: -e.effectiveness_estimate)[:limit]

    def _group_by_scenario(
        self, executions: list[tuple[Any, Any, Any]]
    ) -> dict[str, list[tuple[Any, Any, Any]]]:
        groups: dict[str, list[tuple[Any, Any, Any]]] = {}
        for exec_res, verif, dec in executions:
            task_cat = getattr(dec, 'task_category', type('', (), {'value': 'general'}))
            strat = getattr(dec, 'strategy', type('', (), {'value': 'unknown'}))
            risk = getattr(getattr(dec, 'risk_assessment', None), 'level', type('', (), {'value': 'unknown'}))
            scenario_key = f"{task_cat.value}_{strat.value}_{risk.value}"
            if scenario_key not in groups:
                groups[scenario_key] = []
            groups[scenario_key].append((exec_res, verif, dec))
        return groups

    def _distill_from_group(
        self,
        scenario: str,
        group: list[tuple[Any, Any, Any]],
        pattern_acc: PatternAccumulator,
    ) -> DistilledExperience | None:
        if len(group) < 2:
            return None

        self._experience_counter += 1
        now = datetime.now().isoformat()

        scores = [v.match_score for _, v, _ in group]
        avg_score = statistics.mean(scores)
        successes = sum(1 for _, v, _ in group if v.outcome_match)

        first_dec = group[0][2]
        action = getattr(first_dec, 'selected_action', None)
        plan = getattr(first_dec, 'execution_plan', [])

        action_seq = [
            {"step": p.get("step", i), "phase": p.get("phase", ""), "action": p.get("action", "")}
            for i, p in enumerate(plan[:8])
        ] if plan else []

        related_patterns = pattern_acc.query(
            task_type=getattr(first_dec, 'task_category', type('', (), {'value': 'general'})).value if hasattr(first_dec, 'task_category') else "general",
            limit=3,
        )

        lessons: list[str] = []
        if avg_score > 0.85:
            lessons.append("该场景下高匹配度方案具有良好可重复性")
        if avg_score < 0.5:
            lessons.append("该场景下需要重新评估策略选择")
        if successes > len(group) * 0.75:
            lessons.append("当前策略在此场景下表现稳定")

        return DistilledExperience(
            experience_id=f"EXP-{self._experience_counter:04d}",
            name=f"经验: {scenario.replace('_', ' ')}",
            scenario=scenario,
            preconditions=self._extract_preconditions(group),
            action_sequence=action_seq,
            expected_outcome=f"预期匹配度≥{avg_score:.1%}",
            anti_patterns=[] if avg_score > 0.7 else ["当前方案在此场景下效果不佳"],
            lessons_learned=lessons,
            applicability_scope=[scenario],
            effectiveness_estimate=round(avg_score, 3),
            source_executions=[getattr(e, 'execution_id', '') for e, _, _ in group],
            created_at=now,
            usage_count=len(group),
        )

    @staticmethod
    def _extract_preconditions(group: list[tuple[Any, Any, Any]]) -> list[str]:
        conditions: list[str] = []
        risk_levels = set()
        strategies = set()
        for _, _, dec in group:
            r = getattr(getattr(dec, 'risk_assessment', None), 'level', None)
            if r:
                risk_levels.add(r.value)
            s = getattr(dec, 'strategy', None)
            if s:
                strategies.add(s.value)

        if risk_levels:
            conditions.append(f"适用风险等级: {', '.join(sorted(risk_levels))}")
        if strategies:
            conditions.append(f"已验证策略: {', '.join(sorted(strategies))}")
        conditions.append(f"基于{len(group)}次执行样本提炼")
        return conditions


class FeedbackLearningLayer:
    """
    反馈学习层 - 统一入口
    
    协调四个子模块完成完整的反馈学习流程：
    ResultVerifier → PatternAccumulator → StrategyTuner → KnowledgeDistiller
    最终输出LearningInsight洞察报告。
    """

    def __init__(self, knowledge_base_path: Path | str | None = None) -> None:
        self._verifier = ResultVerifier()
        self._accumulator = PatternAccumulator(knowledge_base_path)
        self._tuner = StrategyTuner()
        self._distiller = KnowledgeDistiller()
        self._recent_buffer: list[tuple[Any, Any, Any]] = []
        self._max_buffer_size = 50
        self._insight_counter: int = 0

    def learn(
        self,
        execution_result: Any,
        perception_report: Any,
    ) -> LearningInsight:
        """
        执行完整的学习流程
        
        Args:
            execution_result: 执行层的ExecutionResult
            perception_report: 感知层的PerceptionReport
            
        Returns:
            LearningInsight对象
        """
        self._insight_counter += 1
        now = datetime.now().isoformat()

        from decide_layer import Decision as DecClass
        fake_decision_for_verify = DecClass()

        verification = self._verifier.verify(execution_result, perception_report, fake_decision_for_verify)

        new_patterns = self._accumulator.accumulate(execution_result, verification, fake_decision_for_verify)
        updated_profiles = self._tuner.tune(execution_result, verification, fake_decision_for_verify)

        self._recent_buffer.append((execution_result, verification, fake_decision_for_verify))
        if len(self._recent_buffer) > self._max_buffer_size:
            self._recent_buffer.pop(0)

        distilled: list[DistilledExperience] = []
        if len(self._recent_buffer) >= 3:
            distilled = self._distiller.distill(self._recent_buffer[-10:], self._accumulator)

        recommendations = self._generate_recommendations(verification, updated_profiles, distilled)

        insight = LearningInsight(
            insight_id=f"INS-{self._insight_counter:04d}",
            timestamp=now,
            execution_id=getattr(execution_result, 'execution_id', ''),
            verification=verification,
            new_patterns=new_patterns,
            updated_strategies=updated_profiles,
            distilled_experiences=distilled,
            recommendations=recommendations,
            metrics={
                "knowledge_base_size": len(self._accumulator._entries),
                "strategies_tracked": len(self._tuner._profiles),
                "experiences_distilled": len(self._distiller._experiences),
                "buffer_size": len(self._recent_buffer),
            },
        )
        return insight

    def _generate_recommendations(
        self,
        verification: VerificationResult,
        profiles: list[StrategyProfile],
        experiences: list[DistilledExperience],
    ) -> list[str]:
        recs: list[str] = []

        if verification.match_score < 0.5:
            recs.append("⚠️ 执行效果不佳，建议审查决策流程并调整策略")

        best_profile = max(profiles, key=lambda p: p.success_rate) if profiles else None
        if best_profile and best_profile.success_rate > 0.8:
            recs.append(f"💡 策略 '{best_profile.strategy_name}' 表现优异（成功率{best_profile.success_rate:.0%}），类似任务可优先考虑")

        declining = [p for p in profiles if p.trend == "declining"]
        if declining:
            recs.append(f"📉 策略 '{declining[0].strategy_name}' 成功率呈下降趋势，建议减少使用或调整参数")

        top_exp = max(experiences, key=lambda e: e.effectiveness_estimate) if experiences else None
        if top_exp and top_exp.effectiveness_estimate > 0.8:
            recs.append(f"📚 发现高效经验模板: {top_exp.name}")

        if verification.improvements:
            for imp in verification.improvements[:2]:
                recs.append(f"✅ {imp}")

        if not recs:
            recs.append("✨ 当前执行效果正常，继续保持现有实践")

        return recs[:8]


if __name__ == "__main__":
    print("=" * 65)
    print("📚 反馈学习层 (Feedback & Learning Layer) - 功能演示")
    print("=" * 65)

    layer = FeedbackLearningLayer()

    print("\n--- 结果验证 ---")
    from execute_layer import ExecutionResult, ExecutionStatus, EditOperation, ImpactReport, ValidationResult, EditType
    from pathlib import Path as PPath
    from perceive_layer import PerceptionReport

    fake_exec = ExecutionResult(
        execution_id="EXEC-0001",
        decision_id="DEC-001",
        status=ExecutionStatus.COMPLETED,
        operations=[
            EditOperation(op_id="OP-0001", file_path=PPath("demo.py"), edit_type=EditType.REPLACE, description="修复bug"),
        ],
        validation=ValidationResult(syntax_valid=True, tests_passed=None),
        impact_report=ImpactReport(overall_risk_score=5.0),
        rollback_available=True,
        metrics={"impact_score": 5.0},
    )

    fake_perception = PerceptionReport(
        timestamp=datetime.now().isoformat(),
        project_root="/demo",
        task_description="修复认证模块漏洞",
        confidence_level=0.80,
    )

    verifier = ResultVerifier()
    verif = verifier.verify(fake_exec, fake_perception, None)
    print(f"   预期结果: {verif.expected_outcome[:80]}...")
    print(f"   实际结果: {verif.actual_outcome[:80]}...")
    print(f"   结果匹配: {'✅ 是' if verif.outcome_match else '❌ 否'} (得分: {verif.match_score:.2f})")
    print(f"   差异项: {len(verif.discrepancies)}")
    for d in verif.discrepancies[:3]:
        print(f"      [{d['severity']}] {d['message']}")
    print(f"   改进项: {verif.improvements}")
    print(f"   回退项: {verif.regressions}")
    print(f"   质量变化: {verif.quality_delta}")

    print("\n--- 模式积累 ---")
    new_entries = layer._accumulator.accumulate(fake_exec, verif, None)
    print(f"   新增条目: {len(new_entries)}")
    for entry in new_entries:
        print(f"      [{entry.category.value}] {entry.title}")
        print(f"         效果分={entry.effectiveness_score:.3f}, 置信度={entry.confidence:.3f}")

    stats = layer._accumulator.get_statistics()
    print(f"\n   知识库统计:")
    print(f"      总条目数: {stats['total_entries']}")
    print(f"      分类分布: {stats['by_category']}")
    print(f"      平均效果: {stats['avg_effectiveness']}")

    print("\n--- 策略调优 ---")
    updated = layer._tuner.tune(fake_exec, verif, None)
    print(f"   跟踪策略数: {len(updated)}")
    for prof in updated:
        reliability = "✅ 可靠" if prof.is_reliable else "⏳ 数据不足"
        trend_icon = {"improving": "📈", "stable": "➡️", "declining": "📉"}.get(prof.trend, "❓")
        print(f"      {prof.strategy_name:12s}: 使用{prof.total_uses}次, "
              f"成功率{prof.success_rate:.0%}, 权重调整{prof.weight_adjustment:+.1f} "
              f"{trend_icon}{prof.trend} {reliability}")

    print("\n--- 知识提炼 ---")
    for _ in range(3):
        layer._recent_buffer.append((fake_exec, verif, None))
    distilled = layer._distiller.distill(layer._recent_buffer, layer._accumulator)
    print(f"   提炼经验数: {len(distilled)}")
    for exp in distilled:
        print(f"      [{exp.experience_id}] {exp.name}")
        print(f"         场景: {exp.scenario}, 有效性: {exp.effectiveness_estimate:.1%}")
        print(f"         教训: {exp.lessons_learned[:2]}")

    print("\n--- 完整学习流程 ---")
    insight = layer.learn(fake_exec, fake_perception)
    print(insight.to_dict())

    print(f"\n   建议:")
    for rec in insight.recommendations:
        print(f"      {rec}")

    print(f"\n   度量:")
    for k, v in insight.metrics.items():
        print(f"      {k}: {v}")

    print("\n✅ 所有反馈学习层测试通过!")
