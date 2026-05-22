#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
推荐引擎模块

实现智能推荐功能，支持：
1. 最佳实践推荐 - 基于历史成功案例
2. 优化建议推荐 - 基于代码分析和性能数据
3. 个性化推荐 - 基于用户偏好和历史行为
4. 推荐效果追踪 - 追踪推荐采纳率和效果

推荐维度：
- 代码质量优化建议
- 性能优化建议
- 安全加固建议
- 架构改进建议

使用示例:
    python recommendation_engine.py --project myproject
    python recommendation_engine.py --type code_quality --output json
    python recommendation_engine.py --personalized --user dev_user
"""

import json
import logging
import sys
import argparse
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple
import hashlib
import math
import statistics


class RecommendationCategory(Enum):
    """推荐类别枚举"""
    CODE_QUALITY = "code_quality"
    PERFORMANCE = "performance"
    SECURITY = "security"
    ARCHITECTURE = "architecture"
    TESTING = "testing"
    DOCUMENTATION = "documentation"
    DEPENDENCY = "dependency"
    DEVOPS = "devops"


class RecommendationPriority(Enum):
    """推荐优先级枚举"""
    CRITICAL = 1
    HIGH = 2
    MEDIUM = 3
    LOW = 4
    INFO = 5


class RecommendationStatus(Enum):
    """推荐状态枚举"""
    PENDING = "pending"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    IMPLEMENTED = "implemented"
    DEPRECATED = "deprecated"


class ConfidenceLevel(Enum):
    """置信度等级枚举"""
    VERY_HIGH = "very_high"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    VERY_LOW = "very_low"


class EvolutionRiskLevel(Enum):
    """演化风险等级枚举"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class EvolutionTiming(Enum):
    """演化时机枚举"""
    IMMEDIATE = "immediate"
    SOON = "soon"
    SCHEDULED = "scheduled"
    DEFERRED = "deferred"


class EvolutionResourceLevel(Enum):
    """演化资源消耗等级枚举"""
    MINIMAL = "minimal"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    EXTENSIVE = "extensive"


@dataclass
class EvolutionRecommendation:
    """演化推荐数据类"""
    recommendation_id: str
    evolution_type: str
    title: str
    description: str
    trigger_reason: str
    execution_steps: List[str]
    expected_effects: Dict[str, float]
    risk_level: EvolutionRiskLevel
    timing: EvolutionTiming
    resource_level: EvolutionResourceLevel
    priority_score: float = 0.0
    confidence: float = 0.0
    success_rate: float = 0.0
    related_patterns: List[str] = field(default_factory=list)
    prerequisites: List[str] = field(default_factory=list)
    rollback_available: bool = True
    estimated_duration: str = ""
    affected_components: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "recommendation_id": self.recommendation_id,
            "evolution_type": self.evolution_type,
            "title": self.title,
            "description": self.description,
            "trigger_reason": self.trigger_reason,
            "execution_steps": self.execution_steps,
            "expected_effects": self.expected_effects,
            "risk_level": self.risk_level.value,
            "timing": self.timing.value,
            "resource_level": self.resource_level.value,
            "priority_score": round(self.priority_score, 4),
            "confidence": round(self.confidence, 4),
            "success_rate": round(self.success_rate, 4),
            "related_patterns": self.related_patterns,
            "prerequisites": self.prerequisites,
            "rollback_available": self.rollback_available,
            "estimated_duration": self.estimated_duration,
            "affected_components": self.affected_components,
            "tags": self.tags,
            "created_at": self.created_at,
            "metadata": self.metadata
        }


@dataclass
class EvolutionPrediction:
    """演化效果预测数据类"""
    prediction_id: str
    evolution_type: str
    performance_improvement: float
    quality_improvement: float
    maintainability_change: float
    risk_score: float
    confidence: float
    predicted_duration: float
    resource_consumption: float
    success_probability: float
    potential_issues: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    metrics_before: Dict[str, float] = field(default_factory=dict)
    metrics_after: Dict[str, float] = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "prediction_id": self.prediction_id,
            "evolution_type": self.evolution_type,
            "performance_improvement": round(self.performance_improvement, 4),
            "quality_improvement": round(self.quality_improvement, 4),
            "maintainability_change": round(self.maintainability_change, 4),
            "risk_score": round(self.risk_score, 4),
            "confidence": round(self.confidence, 4),
            "predicted_duration": round(self.predicted_duration, 4),
            "resource_consumption": round(self.resource_consumption, 4),
            "success_probability": round(self.success_probability, 4),
            "potential_issues": self.potential_issues,
            "recommendations": self.recommendations,
            "metrics_before": self.metrics_before,
            "metrics_after": self.metrics_after,
            "created_at": self.created_at
        }


@dataclass
class EvolutionPriorityScore:
    """演化优先级评分数据类"""
    score_id: str
    effect_score: float
    risk_score: float
    resource_score: float
    urgency_score: float
    historical_score: float
    final_score: float
    ranking_factors: Dict[str, float] = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "score_id": self.score_id,
            "effect_score": round(self.effect_score, 4),
            "risk_score": round(self.risk_score, 4),
            "resource_score": round(self.resource_score, 4),
            "urgency_score": round(self.urgency_score, 4),
            "historical_score": round(self.historical_score, 4),
            "final_score": round(self.final_score, 4),
            "ranking_factors": self.ranking_factors,
            "created_at": self.created_at
        }


@dataclass
class PersonalizedEvolutionSuggestion:
    """个性化演化建议数据类"""
    suggestion_id: str
    skill_id: str
    recommendations: List[EvolutionRecommendation]
    user_preferences: Dict[str, Any]
    project_characteristics: Dict[str, Any]
    historical_context: Dict[str, Any]
    confidence: float
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "suggestion_id": self.suggestion_id,
            "skill_id": self.skill_id,
            "recommendations": [r.to_dict() for r in self.recommendations],
            "user_preferences": self.user_preferences,
            "project_characteristics": self.project_characteristics,
            "historical_context": self.historical_context,
            "confidence": round(self.confidence, 4),
            "created_at": self.created_at
        }


@dataclass
class Recommendation:
    """推荐项数据类"""
    recommendation_id: str
    category: RecommendationCategory
    priority: RecommendationPriority
    title: str
    description: str
    rationale: str
    actions: List[str]
    impact_score: float
    confidence: float
    effort_estimate: str
    related_files: List[str] = field(default_factory=list)
    related_metrics: Dict[str, float] = field(default_factory=dict)
    tags: List[str] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    status: RecommendationStatus = RecommendationStatus.PENDING
    source: str = "system"
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "recommendation_id": self.recommendation_id,
            "category": self.category.value,
            "priority": self.priority.value,
            "title": self.title,
            "description": self.description,
            "rationale": self.rationale,
            "actions": self.actions,
            "impact_score": round(self.impact_score, 4),
            "confidence": round(self.confidence, 4),
            "effort_estimate": self.effort_estimate,
            "related_files": self.related_files,
            "related_metrics": self.related_metrics,
            "tags": self.tags,
            "created_at": self.created_at,
            "status": self.status.value,
            "source": self.source,
            "metadata": self.metadata
        }


@dataclass
class BestPractice:
    """最佳实践数据类"""
    practice_id: str
    category: RecommendationCategory
    name: str
    description: str
    conditions: List[str]
    implementation_steps: List[str]
    success_rate: float
    adoption_count: int
    avg_impact: float
    tags: List[str] = field(default_factory=list)
    examples: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "practice_id": self.practice_id,
            "category": self.category.value,
            "name": self.name,
            "description": self.description,
            "conditions": self.conditions,
            "implementation_steps": self.implementation_steps,
            "success_rate": round(self.success_rate, 4),
            "adoption_count": self.adoption_count,
            "avg_impact": round(self.avg_impact, 4),
            "tags": self.tags,
            "examples": self.examples
        }


@dataclass
class UserPreference:
    """用户偏好数据类"""
    user_id: str
    preferred_categories: List[RecommendationCategory]
    priority_weights: Dict[str, float]
    excluded_tags: List[str]
    preferred_effort_levels: List[str]
    historical_acceptance: Dict[str, float]
    feedback_scores: Dict[str, float]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "user_id": self.user_id,
            "preferred_categories": [c.value for c in self.preferred_categories],
            "priority_weights": self.priority_weights,
            "excluded_tags": self.excluded_tags,
            "preferred_effort_levels": self.preferred_effort_levels,
            "historical_acceptance": self.historical_acceptance,
            "feedback_scores": self.feedback_scores
        }


@dataclass
class RecommendationFeedback:
    """推荐反馈数据类"""
    recommendation_id: str
    user_id: str
    action: str
    rating: Optional[int] = None
    comment: Optional[str] = None
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    implementation_time: Optional[float] = None
    actual_impact: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "recommendation_id": self.recommendation_id,
            "user_id": self.user_id,
            "action": self.action,
            "rating": self.rating,
            "comment": self.comment,
            "timestamp": self.timestamp,
            "implementation_time": self.implementation_time,
            "actual_impact": self.actual_impact
        }


@dataclass
class RecommendationEffect:
    """推荐效果数据类"""
    recommendation_id: str
    total_views: int
    acceptance_rate: float
    avg_rating: float
    avg_implementation_time: float
    avg_impact_improvement: float
    user_satisfaction: float
    category: RecommendationCategory
    period_days: int

    def to_dict(self) -> Dict[str, Any]:
        return {
            "recommendation_id": self.recommendation_id,
            "total_views": self.total_views,
            "acceptance_rate": round(self.acceptance_rate, 4),
            "avg_rating": round(self.avg_rating, 4),
            "avg_implementation_time": round(self.avg_implementation_time, 4),
            "avg_impact_improvement": round(self.avg_impact_improvement, 4),
            "user_satisfaction": round(self.user_satisfaction, 4),
            "category": self.category.value,
            "period_days": self.period_days
        }


@dataclass
class RecommendationReport:
    """推荐报告数据类"""
    timestamp: str
    project: str
    recommendations: List[Recommendation]
    effects: List[RecommendationEffect]
    summary: Dict[str, Any]
    top_categories: List[Dict[str, Any]]
    improvement_potential: float

    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp,
            "project": self.project,
            "recommendations": [r.to_dict() for r in self.recommendations],
            "effects": [e.to_dict() for e in self.effects],
            "summary": self.summary,
            "top_categories": self.top_categories,
            "improvement_potential": round(self.improvement_potential, 4)
        }


class IRecommendationSource(ABC):
    """推荐源接口"""

    @abstractmethod
    def generate_recommendations(
        self,
        context: Dict[str, Any],
        category: Optional[RecommendationCategory] = None
    ) -> List[Recommendation]:
        pass

    @abstractmethod
    def get_confidence(self, recommendation: Recommendation) -> float:
        pass


class BestPracticeRecommender(IRecommendationSource):
    """最佳实践推荐器"""

    def __init__(self, logger: Optional[logging.Logger] = None):
        self.logger = logger or logging.getLogger(__name__)
        self._practice_library: Dict[str, BestPractice] = {}
        self._success_cases: List[Dict[str, Any]] = []
        self._initialize_practices()

    def _initialize_practices(self) -> None:
        practices = [
            BestPractice(
                practice_id="BP-CODE-001",
                category=RecommendationCategory.CODE_QUALITY,
                name="函数复杂度控制",
                description="保持函数圈复杂度在10以下，提高代码可读性和可维护性",
                conditions=["圈复杂度 > 10", "函数行数 > 50"],
                implementation_steps=[
                    "识别高复杂度函数",
                    "拆分复杂逻辑为多个小函数",
                    "应用单一职责原则",
                    "添加必要的注释和文档"
                ],
                success_rate=0.92,
                adoption_count=156,
                avg_impact=0.75,
                tags=["complexity", "refactoring", "maintainability"],
                examples=["extract_method", "replace_conditional_with_polymorphism"]
            ),
            BestPractice(
                practice_id="BP-CODE-002",
                category=RecommendationCategory.CODE_QUALITY,
                name="代码重复消除",
                description="识别并消除代码重复，提高代码复用性和维护效率",
                conditions=["重复代码块 > 3", "相似度 > 80%"],
                implementation_steps=[
                    "使用代码重复检测工具",
                    "提取公共方法或类",
                    "应用模板方法模式",
                    "建立共享工具库"
                ],
                success_rate=0.88,
                adoption_count=134,
                avg_impact=0.68,
                tags=["duplication", "dry", "refactoring"],
                examples=["extract_class", "form_template_method"]
            ),
            BestPractice(
                practice_id="BP-PERF-001",
                category=RecommendationCategory.PERFORMANCE,
                name="数据库查询优化",
                description="优化慢查询，添加适当的索引，提高数据库访问性能",
                conditions=["查询时间 > 100ms", "全表扫描", "缺少索引"],
                implementation_steps=[
                    "分析慢查询日志",
                    "使用EXPLAIN分析执行计划",
                    "添加必要的索引",
                    "优化查询语句结构"
                ],
                success_rate=0.85,
                adoption_count=98,
                avg_impact=0.82,
                tags=["database", "query", "index"],
                examples=["add_index", "optimize_join", "use_covering_index"]
            ),
            BestPractice(
                practice_id="BP-PERF-002",
                category=RecommendationCategory.PERFORMANCE,
                name="缓存策略实施",
                description="实施合理的缓存策略，减少重复计算和数据库访问",
                conditions=["重复计算", "频繁数据库访问", "响应时间波动大"],
                implementation_steps=[
                    "识别热点数据",
                    "选择合适的缓存策略",
                    "实施缓存失效机制",
                    "监控缓存命中率"
                ],
                success_rate=0.87,
                adoption_count=112,
                avg_impact=0.78,
                tags=["cache", "performance", "optimization"],
                examples=["redis_cache", "local_cache", "cdn_cache"]
            ),
            BestPractice(
                practice_id="BP-SEC-001",
                category=RecommendationCategory.SECURITY,
                name="输入验证强化",
                description="对所有外部输入进行严格验证，防止注入攻击",
                conditions=["用户输入处理", "API参数", "文件上传"],
                implementation_steps=[
                    "识别所有输入点",
                    "实施白名单验证",
                    "使用参数化查询",
                    "添加输入长度限制"
                ],
                success_rate=0.95,
                adoption_count=178,
                avg_impact=0.90,
                tags=["security", "validation", "injection"],
                examples=["sql_injection_prevention", "xss_prevention"]
            ),
            BestPractice(
                practice_id="BP-SEC-002",
                category=RecommendationCategory.SECURITY,
                name="敏感数据保护",
                description="对敏感数据进行加密存储和传输，防止数据泄露",
                conditions=["密码存储", "个人信息", "支付数据"],
                implementation_steps=[
                    "识别敏感数据类型",
                    "选择合适的加密算法",
                    "实施密钥管理",
                    "启用传输加密"
                ],
                success_rate=0.93,
                adoption_count=145,
                avg_impact=0.88,
                tags=["security", "encryption", "privacy"],
                examples=["password_hashing", "data_encryption", "tls"]
            ),
            BestPractice(
                practice_id="BP-ARCH-001",
                category=RecommendationCategory.ARCHITECTURE,
                name="模块化设计",
                description="采用模块化设计，降低组件耦合度，提高系统可扩展性",
                conditions=["高耦合度", "循环依赖", "职责不清"],
                implementation_steps=[
                    "分析现有依赖关系",
                    "定义模块边界",
                    "重构依赖关系",
                    "建立模块接口"
                ],
                success_rate=0.82,
                adoption_count=89,
                avg_impact=0.72,
                tags=["architecture", "modularity", "coupling"],
                examples=["dependency_injection", "module_boundary"]
            ),
            BestPractice(
                practice_id="BP-ARCH-002",
                category=RecommendationCategory.ARCHITECTURE,
                name="API设计规范",
                description="遵循RESTful API设计规范，提高API一致性和可用性",
                conditions=["API不一致", "版本管理混乱", "文档缺失"],
                implementation_steps=[
                    "制定API设计规范",
                    "统一响应格式",
                    "实施版本控制",
                    "生成API文档"
                ],
                success_rate=0.86,
                adoption_count=102,
                avg_impact=0.70,
                tags=["api", "rest", "design"],
                examples=["restful_design", "api_versioning"]
            ),
            BestPractice(
                practice_id="BP-TEST-001",
                category=RecommendationCategory.TESTING,
                name="测试覆盖率提升",
                description="提高单元测试覆盖率，确保代码质量和稳定性",
                conditions=["覆盖率 < 80%", "关键路径无测试"],
                implementation_steps=[
                    "分析覆盖率报告",
                    "识别未覆盖代码",
                    "编写单元测试",
                    "集成到CI流程"
                ],
                success_rate=0.90,
                adoption_count=167,
                avg_impact=0.76,
                tags=["testing", "coverage", "quality"],
                examples=["unit_test", "integration_test"]
            ),
            BestPractice(
                practice_id="BP-DOC-001",
                category=RecommendationCategory.DOCUMENTATION,
                name="代码文档完善",
                description="为关键代码添加文档注释，提高代码可读性和维护性",
                conditions=["文档覆盖率 < 50%", "关键函数无注释"],
                implementation_steps=[
                    "识别需要文档的代码",
                    "编写docstring",
                    "生成API文档",
                    "维护文档更新"
                ],
                success_rate=0.78,
                adoption_count=78,
                avg_impact=0.55,
                tags=["documentation", "readability", "maintenance"],
                examples=["docstring", "readme", "api_docs"]
            )
        ]

        for practice in practices:
            self._practice_library[practice.practice_id] = practice

    def generate_recommendations(
        self,
        context: Dict[str, Any],
        category: Optional[RecommendationCategory] = None
    ) -> List[Recommendation]:
        recommendations: List[Recommendation] = []

        for practice_id, practice in self._practice_library.items():
            if category and practice.category != category:
                continue

            if self._matches_conditions(practice, context):
                recommendation = self._create_recommendation(practice, context)
                recommendations.append(recommendation)

        return sorted(recommendations, key=lambda r: r.impact_score, reverse=True)

    def _matches_conditions(self, practice: BestPractice, context: Dict[str, Any]) -> bool:
        metrics = context.get("metrics", {})
        issues = context.get("issues", [])

        for condition in practice.conditions:
            if any(keyword in condition.lower() for keyword in ["复杂度", "complexity"]):
                if metrics.get("code_complexity", 0) > 10:
                    return True
            elif any(keyword in condition.lower() for keyword in ["重复", "duplication"]):
                if metrics.get("duplication_rate", 0) > 3:
                    return True
            elif any(keyword in condition.lower() for keyword in ["查询", "query"]):
                if metrics.get("slow_queries", 0) > 0:
                    return True
            elif any(keyword in condition.lower() for keyword in ["缓存", "cache"]):
                if metrics.get("cache_hit_rate", 100) < 80:
                    return True
            elif any(keyword in condition.lower() for keyword in ["安全", "security", "输入"]):
                if metrics.get("security_issues", 0) > 0:
                    return True
            elif any(keyword in condition.lower() for keyword in ["覆盖", "coverage"]):
                if metrics.get("code_coverage", 100) < 80:
                    return True
            elif any(keyword in condition.lower() for keyword in ["文档", "documentation"]):
                if metrics.get("doc_coverage", 100) < 50:
                    return True

        for issue in issues:
            issue_lower = issue.lower()
            if practice.category == RecommendationCategory.CODE_QUALITY:
                if any(kw in issue_lower for kw in ["complex", "duplicate", "smell"]):
                    return True
            elif practice.category == RecommendationCategory.PERFORMANCE:
                if any(kw in issue_lower for kw in ["slow", "performance", "timeout"]):
                    return True
            elif practice.category == RecommendationCategory.SECURITY:
                if any(kw in issue_lower for kw in ["security", "vulnerability", "injection"]):
                    return True
            elif practice.category == RecommendationCategory.ARCHITECTURE:
                if any(kw in issue_lower for kw in ["architecture", "coupling", "dependency"]):
                    return True

        return False

    def _create_recommendation(self, practice: BestPractice, context: Dict[str, Any]) -> Recommendation:
        recommendation_id = f"REC-{practice.practice_id}-{datetime.now().strftime('%Y%m%d%H%M%S')}"

        confidence = self._calculate_confidence(practice, context)
        priority = self._determine_priority(practice, context)

        return Recommendation(
            recommendation_id=recommendation_id,
            category=practice.category,
            priority=priority,
            title=practice.name,
            description=practice.description,
            rationale=f"基于 {practice.adoption_count} 次成功应用，成功率 {practice.success_rate:.1%}",
            actions=practice.implementation_steps,
            impact_score=practice.avg_impact,
            confidence=confidence,
            effort_estimate=self._estimate_effort(practice),
            tags=practice.tags,
            source="best_practice",
            metadata={
                "practice_id": practice.practice_id,
                "success_rate": practice.success_rate,
                "adoption_count": practice.adoption_count
            }
        )

    def _calculate_confidence(self, practice: BestPractice, context: Dict[str, Any]) -> float:
        base_confidence = practice.success_rate
        adoption_factor = min(practice.adoption_count / 100, 1.0)
        impact_factor = practice.avg_impact

        context_match_score = 0.7
        metrics = context.get("metrics", {})
        if metrics:
            context_match_score = 0.8

        confidence = (
            base_confidence * 0.4 +
            adoption_factor * 0.2 +
            impact_factor * 0.2 +
            context_match_score * 0.2
        )

        return min(confidence, 1.0)

    def _determine_priority(self, practice: BestPractice, context: Dict[str, Any]) -> RecommendationPriority:
        if practice.category == RecommendationCategory.SECURITY:
            return RecommendationPriority.CRITICAL
        elif practice.avg_impact > 0.8:
            return RecommendationPriority.HIGH
        elif practice.avg_impact > 0.6:
            return RecommendationPriority.MEDIUM
        elif practice.avg_impact > 0.4:
            return RecommendationPriority.LOW
        else:
            return RecommendationPriority.INFO

    def _estimate_effort(self, practice: BestPractice) -> str:
        steps_count = len(practice.implementation_steps)
        complexity_tags = {"architecture", "refactoring", "migration"}

        if practice.tags and set(practice.tags) & complexity_tags:
            if steps_count > 4:
                return "高 (1-2周)"
            else:
                return "中 (3-5天)"
        else:
            if steps_count > 4:
                return "中 (3-5天)"
            else:
                return "低 (1-2天)"

    def get_confidence(self, recommendation: Recommendation) -> float:
        return recommendation.confidence

    def add_success_case(self, case: Dict[str, Any]) -> None:
        self._success_cases.append({
            **case,
            "timestamp": datetime.now().isoformat()
        })

    def get_practices_by_category(self, category: RecommendationCategory) -> List[BestPractice]:
        return [p for p in self._practice_library.values() if p.category == category]


class OptimizationRecommender(IRecommendationSource):
    """优化建议推荐器"""

    def __init__(self, logger: Optional[logging.Logger] = None):
        self.logger = logger or logging.getLogger(__name__)
        self._optimization_rules: Dict[str, Dict[str, Any]] = {}
        self._initialize_rules()

    def _initialize_rules(self) -> None:
        self._optimization_rules = {
            "code_quality": {
                "high_complexity": {
                    "threshold": 15,
                    "message": "函数圈复杂度过高",
                    "suggestion": "考虑拆分函数或简化条件逻辑",
                    "impact": 0.75,
                    "category": RecommendationCategory.CODE_QUALITY
                },
                "low_coverage": {
                    "threshold": 70,
                    "message": "测试覆盖率低于推荐值",
                    "suggestion": "增加单元测试以提高覆盖率",
                    "impact": 0.70,
                    "category": RecommendationCategory.TESTING
                },
                "high_duplication": {
                    "threshold": 5,
                    "message": "代码重复率较高",
                    "suggestion": "提取公共代码，消除重复",
                    "impact": 0.65,
                    "category": RecommendationCategory.CODE_QUALITY
                }
            },
            "performance": {
                "slow_query": {
                    "threshold": 100,
                    "message": "存在慢查询",
                    "suggestion": "优化查询语句或添加索引",
                    "impact": 0.85,
                    "category": RecommendationCategory.PERFORMANCE
                },
                "low_cache_hit": {
                    "threshold": 80,
                    "message": "缓存命中率较低",
                    "suggestion": "优化缓存策略或增加缓存容量",
                    "impact": 0.78,
                    "category": RecommendationCategory.PERFORMANCE
                },
                "high_memory": {
                    "threshold": 80,
                    "message": "内存使用率较高",
                    "suggestion": "检查内存泄漏或优化数据结构",
                    "impact": 0.72,
                    "category": RecommendationCategory.PERFORMANCE
                }
            },
            "security": {
                "vulnerability_count": {
                    "threshold": 0,
                    "message": "存在安全漏洞",
                    "suggestion": "立即修复安全问题",
                    "impact": 0.95,
                    "category": RecommendationCategory.SECURITY
                },
                "outdated_deps": {
                    "threshold": 0,
                    "message": "存在过时的依赖包",
                    "suggestion": "更新依赖包到最新安全版本",
                    "impact": 0.80,
                    "category": RecommendationCategory.SECURITY
                }
            },
            "architecture": {
                "high_coupling": {
                    "threshold": 0.7,
                    "message": "模块耦合度较高",
                    "suggestion": "重构以降低耦合度",
                    "impact": 0.70,
                    "category": RecommendationCategory.ARCHITECTURE
                },
                "circular_deps": {
                    "threshold": 0,
                    "message": "存在循环依赖",
                    "suggestion": "重构以消除循环依赖",
                    "impact": 0.75,
                    "category": RecommendationCategory.ARCHITECTURE
                }
            }
        }

    def generate_recommendations(
        self,
        context: Dict[str, Any],
        category: Optional[RecommendationCategory] = None
    ) -> List[Recommendation]:
        recommendations: List[Recommendation] = []
        metrics = context.get("metrics", {})
        analysis_results = context.get("analysis_results", {})

        for rule_category, rules in self._optimization_rules.items():
            for rule_name, rule in rules.items():
                if category and rule["category"] != category:
                    continue

                recommendation = self._check_rule(rule_name, rule, metrics, analysis_results)
                if recommendation:
                    recommendations.append(recommendation)

        return sorted(recommendations, key=lambda r: r.impact_score, reverse=True)

    def _check_rule(
        self,
        rule_name: str,
        rule: Dict[str, Any],
        metrics: Dict[str, float],
        analysis_results: Dict[str, Any]
    ) -> Optional[Recommendation]:
        metric_value = self._get_metric_value(rule_name, metrics, analysis_results)

        if metric_value is None:
            return None

        is_violation = self._check_violation(rule_name, metric_value, rule["threshold"])

        if not is_violation:
            return None

        recommendation_id = f"REC-OPT-{rule_name.upper()}-{datetime.now().strftime('%Y%m%d%H%M%S')}"

        return Recommendation(
            recommendation_id=recommendation_id,
            category=rule["category"],
            priority=self._determine_priority(rule),
            title=rule["message"],
            description=f"当前值: {metric_value:.2f}, 阈值: {rule['threshold']}",
            rationale="基于代码分析和性能数据检测到优化机会",
            actions=[
                rule["suggestion"],
                "分析具体原因",
                "制定优化方案",
                "实施并验证效果"
            ],
            impact_score=rule["impact"],
            confidence=0.85,
            effort_estimate=self._estimate_effort(rule),
            tags=[rule_name, "optimization"],
            source="optimization_analysis",
            metadata={
                "rule_name": rule_name,
                "current_value": metric_value,
                "threshold": rule["threshold"]
            }
        )

    def _get_metric_value(
        self,
        rule_name: str,
        metrics: Dict[str, float],
        analysis_results: Dict[str, Any]
    ) -> Optional[float]:
        metric_mapping = {
            "high_complexity": "code_complexity",
            "low_coverage": "code_coverage",
            "high_duplication": "duplication_rate",
            "slow_query": "avg_query_time",
            "low_cache_hit": "cache_hit_rate",
            "high_memory": "memory_usage",
            "vulnerability_count": "security_issues",
            "outdated_deps": "outdated_dependencies",
            "high_coupling": "coupling_score",
            "circular_deps": "circular_dependencies"
        }

        metric_key = metric_mapping.get(rule_name)
        if metric_key and metric_key in metrics:
            return metrics[metric_key]

        if rule_name in analysis_results:
            return analysis_results[rule_name].get("value")

        return None

    def _check_violation(self, rule_name: str, value: float, threshold: float) -> bool:
        inverse_rules = {"low_coverage", "low_cache_hit"}

        if rule_name in inverse_rules:
            return value < threshold
        else:
            return value > threshold

    def _determine_priority(self, rule: Dict[str, Any]) -> RecommendationPriority:
        if rule["category"] == RecommendationCategory.SECURITY:
            return RecommendationPriority.CRITICAL
        elif rule["impact"] > 0.8:
            return RecommendationPriority.HIGH
        elif rule["impact"] > 0.6:
            return RecommendationPriority.MEDIUM
        else:
            return RecommendationPriority.LOW

    def _estimate_effort(self, rule: Dict[str, Any]) -> str:
        if rule["impact"] > 0.8:
            return "中 (3-5天)"
        elif rule["impact"] > 0.6:
            return "低 (1-3天)"
        else:
            return "低 (1天内)"

    def get_confidence(self, recommendation: Recommendation) -> float:
        return recommendation.confidence


class PersonalizedRecommender(IRecommendationSource):
    """个性化推荐器"""

    def __init__(self, logger: Optional[logging.Logger] = None):
        self.logger = logger or logging.getLogger(__name__)
        self._user_preferences: Dict[str, UserPreference] = {}
        self._recommendation_history: Dict[str, List[str]] = {}
        self._feedback_history: List[RecommendationFeedback] = []

    def set_user_preference(self, preference: UserPreference) -> None:
        self._user_preferences[preference.user_id] = preference

    def get_user_preference(self, user_id: str) -> Optional[UserPreference]:
        return self._user_preferences.get(user_id)

    def record_feedback(self, feedback: RecommendationFeedback) -> None:
        self._feedback_history.append(feedback)

        if feedback.user_id not in self._recommendation_history:
            self._recommendation_history[feedback.user_id] = []
        self._recommendation_history[feedback.user_id].append(feedback.recommendation_id)

        self._update_user_preference_from_feedback(feedback)

    def _update_user_preference_from_feedback(self, feedback: RecommendationFeedback) -> None:
        preference = self._user_preferences.get(feedback.user_id)
        if not preference:
            return

        if feedback.rating:
            current_score = preference.feedback_scores.get(feedback.recommendation_id, 0.5)
            new_score = (current_score + feedback.rating / 5.0) / 2
            preference.feedback_scores[feedback.recommendation_id] = new_score

        if feedback.action == "accepted":
            acceptance = preference.historical_acceptance.get(feedback.recommendation_id, 0.5)
            preference.historical_acceptance[feedback.recommendation_id] = min(acceptance + 0.1, 1.0)
        elif feedback.action == "rejected":
            acceptance = preference.historical_acceptance.get(feedback.recommendation_id, 0.5)
            preference.historical_acceptance[feedback.recommendation_id] = max(acceptance - 0.1, 0.0)

    def generate_recommendations(
        self,
        context: Dict[str, Any],
        category: Optional[RecommendationCategory] = None,
        user_id: Optional[str] = None
    ) -> List[Recommendation]:
        base_recommendations = context.get("base_recommendations", [])

        if not user_id:
            return base_recommendations

        preference = self._user_preferences.get(user_id)
        if not preference:
            self._create_default_preference(user_id)
            preference = self._user_preferences.get(user_id)

        personalized = []
        for rec in base_recommendations:
            if self._should_recommend(rec, preference):
                personalized_rec = self._personalize_recommendation(rec, preference)
                personalized.append(personalized_rec)

        return sorted(personalized, key=lambda r: r.impact_score, reverse=True)

    def _create_default_preference(self, user_id: str) -> None:
        self._user_preferences[user_id] = UserPreference(
            user_id=user_id,
            preferred_categories=list(RecommendationCategory),
            priority_weights={
                "critical": 1.0,
                "high": 0.8,
                "medium": 0.6,
                "low": 0.4,
                "info": 0.2
            },
            excluded_tags=[],
            preferred_effort_levels=["low", "medium", "high"],
            historical_acceptance={},
            feedback_scores={}
        )

    def _should_recommend(self, recommendation: Recommendation, preference: UserPreference) -> bool:
        if recommendation.category not in preference.preferred_categories:
            return False

        if set(recommendation.tags) & set(preference.excluded_tags):
            return False

        if recommendation.effort_estimate.split()[0].lower() not in [e.lower() for e in preference.preferred_effort_levels]:
            return False

        return True

    def _personalize_recommendation(
        self,
        recommendation: Recommendation,
        preference: UserPreference
    ) -> Recommendation:
        priority_weight = preference.priority_weights.get(
            recommendation.priority.name.lower(), 0.5
        )

        historical_factor = preference.historical_acceptance.get(
            recommendation.recommendation_id, 0.5
        )

        feedback_factor = preference.feedback_scores.get(
            recommendation.recommendation_id, 0.5
        )

        personalized_impact = recommendation.impact_score * (
            0.5 + priority_weight * 0.3 + historical_factor * 0.1 + feedback_factor * 0.1
        )

        personalized_confidence = recommendation.confidence * (
            0.6 + historical_factor * 0.2 + feedback_factor * 0.2
        )

        return Recommendation(
            recommendation_id=recommendation.recommendation_id,
            category=recommendation.category,
            priority=recommendation.priority,
            title=recommendation.title,
            description=recommendation.description,
            rationale=recommendation.rationale,
            actions=recommendation.actions,
            impact_score=min(personalized_impact, 1.0),
            confidence=min(personalized_confidence, 1.0),
            effort_estimate=recommendation.effort_estimate,
            related_files=recommendation.related_files,
            related_metrics=recommendation.related_metrics,
            tags=recommendation.tags + ["personalized"],
            created_at=recommendation.created_at,
            status=recommendation.status,
            source="personalized",
            metadata={
                **recommendation.metadata,
                "personalization_factors": {
                    "priority_weight": priority_weight,
                    "historical_factor": historical_factor,
                    "feedback_factor": feedback_factor
                }
            }
        )

    def get_confidence(self, recommendation: Recommendation) -> float:
        return recommendation.confidence

    def get_user_recommendation_history(self, user_id: str) -> List[str]:
        return self._recommendation_history.get(user_id, [])


class RecommendationEffectTracker:
    """推荐效果追踪器"""

    def __init__(self, logger: Optional[logging.Logger] = None):
        self.logger = logger or logging.getLogger(__name__)
        self._feedback_records: List[RecommendationFeedback] = []
        self._recommendation_views: Dict[str, int] = {}
        self._effect_cache: Dict[str, RecommendationEffect] = {}

    def record_view(self, recommendation_id: str) -> None:
        self._recommendation_views[recommendation_id] = \
            self._recommendation_views.get(recommendation_id, 0) + 1

    def record_feedback(self, feedback: RecommendationFeedback) -> None:
        self._feedback_records.append(feedback)
        self._invalidate_cache(feedback.recommendation_id)

    def calculate_effect(
        self,
        recommendation_id: str,
        category: RecommendationCategory,
        period_days: int = 30
    ) -> RecommendationEffect:
        cache_key = f"{recommendation_id}:{period_days}"
        if cache_key in self._effect_cache:
            return self._effect_cache[cache_key]

        views = self._recommendation_views.get(recommendation_id, 0)

        feedbacks = [f for f in self._feedback_records
                     if f.recommendation_id == recommendation_id]

        acceptance_rate = self._calculate_acceptance_rate(feedbacks)
        avg_rating = self._calculate_avg_rating(feedbacks)
        avg_implementation_time = self._calculate_avg_implementation_time(feedbacks)
        avg_impact_improvement = self._calculate_avg_impact_improvement(feedbacks)
        user_satisfaction = self._calculate_user_satisfaction(feedbacks)

        effect = RecommendationEffect(
            recommendation_id=recommendation_id,
            total_views=views,
            acceptance_rate=acceptance_rate,
            avg_rating=avg_rating,
            avg_implementation_time=avg_implementation_time,
            avg_impact_improvement=avg_impact_improvement,
            user_satisfaction=user_satisfaction,
            category=category,
            period_days=period_days
        )

        self._effect_cache[cache_key] = effect
        return effect

    def _calculate_acceptance_rate(self, feedbacks: List[RecommendationFeedback]) -> float:
        if not feedbacks:
            return 0.0

        accepted = sum(1 for f in feedbacks if f.action in ["accepted", "implemented"])
        return accepted / len(feedbacks)

    def _calculate_avg_rating(self, feedbacks: List[RecommendationFeedback]) -> float:
        ratings = [f.rating for f in feedbacks if f.rating is not None]
        if not ratings:
            return 0.0
        return statistics.mean(ratings) / 5.0

    def _calculate_avg_implementation_time(self, feedbacks: List[RecommendationFeedback]) -> float:
        times = [f.implementation_time for f in feedbacks if f.implementation_time is not None]
        if not times:
            return 0.0
        return statistics.mean(times)

    def _calculate_avg_impact_improvement(self, feedbacks: List[RecommendationFeedback]) -> float:
        impacts = [f.actual_impact for f in feedbacks if f.actual_impact is not None]
        if not impacts:
            return 0.0
        return statistics.mean(impacts)

    def _calculate_user_satisfaction(self, feedbacks: List[RecommendationFeedback]) -> float:
        if not feedbacks:
            return 0.0

        satisfaction_scores = []
        for feedback in feedbacks:
            score = 0.5
            if feedback.action == "accepted":
                score += 0.2
            elif feedback.action == "implemented":
                score += 0.3
            elif feedback.action == "rejected":
                score -= 0.2

            if feedback.rating:
                score += (feedback.rating - 3) * 0.1

            satisfaction_scores.append(max(0, min(1, score)))

        return statistics.mean(satisfaction_scores)

    def _invalidate_cache(self, recommendation_id: str) -> None:
        keys_to_remove = [k for k in self._effect_cache if k.startswith(recommendation_id)]
        for key in keys_to_remove:
            del self._effect_cache[key]

    def get_category_statistics(
        self,
        category: RecommendationCategory,
        period_days: int = 30
    ) -> Dict[str, Any]:
        category_feedbacks = [
            f for f in self._feedback_records
            if self._get_category_for_recommendation(f.recommendation_id) == category
        ]

        return {
            "category": category.value,
            "total_feedbacks": len(category_feedbacks),
            "acceptance_rate": self._calculate_acceptance_rate(category_feedbacks),
            "avg_rating": self._calculate_avg_rating(category_feedbacks),
            "user_satisfaction": self._calculate_user_satisfaction(category_feedbacks)
        }

    def _get_category_for_recommendation(self, recommendation_id: str) -> Optional[RecommendationCategory]:
        for feedback in self._feedback_records:
            if feedback.recommendation_id == recommendation_id:
                return RecommendationCategory.CODE_QUALITY
        return None

    def get_top_performing_recommendations(
        self,
        limit: int = 10,
        period_days: int = 30
    ) -> List[RecommendationEffect]:
        effects = list(self._effect_cache.values())
        sorted_effects = sorted(
            effects,
            key=lambda e: (e.acceptance_rate, e.user_satisfaction),
            reverse=True
        )
        return sorted_effects[:limit]


class EvolutionRecommender:
    """演化推荐器
    
    基于演化知识库推荐演化策略、时机和步骤。
    支持优先级排序、效果预测和个性化建议。
    """
    
    EVOLUTION_TYPE_MAPPING = {
        "optimization": {
            "name": "性能优化",
            "default_timing": EvolutionTiming.SOON,
            "default_risk": EvolutionRiskLevel.LOW,
            "resource_level": EvolutionResourceLevel.MEDIUM
        },
        "refactoring": {
            "name": "代码重构",
            "default_timing": EvolutionTiming.SCHEDULED,
            "default_risk": EvolutionRiskLevel.MEDIUM,
            "resource_level": EvolutionResourceLevel.HIGH
        },
        "enhancement": {
            "name": "功能增强",
            "default_timing": EvolutionTiming.SCHEDULED,
            "default_risk": EvolutionRiskLevel.MEDIUM,
            "resource_level": EvolutionResourceLevel.HIGH
        },
        "bug_fix": {
            "name": "缺陷修复",
            "default_timing": EvolutionTiming.IMMEDIATE,
            "default_risk": EvolutionRiskLevel.LOW,
            "resource_level": EvolutionResourceLevel.LOW
        },
        "adaptation": {
            "name": "环境适配",
            "default_timing": EvolutionTiming.SOON,
            "default_risk": EvolutionRiskLevel.MEDIUM,
            "resource_level": EvolutionResourceLevel.MEDIUM
        },
        "extension": {
            "name": "功能扩展",
            "default_timing": EvolutionTiming.SCHEDULED,
            "default_risk": EvolutionRiskLevel.MEDIUM,
            "resource_level": EvolutionResourceLevel.HIGH
        },
        "deprecation": {
            "name": "功能废弃",
            "default_timing": EvolutionTiming.DEFERRED,
            "default_risk": EvolutionRiskLevel.LOW,
            "resource_level": EvolutionResourceLevel.LOW
        },
        "merge": {
            "name": "模块合并",
            "default_timing": EvolutionTiming.SCHEDULED,
            "default_risk": EvolutionRiskLevel.HIGH,
            "resource_level": EvolutionResourceLevel.HIGH
        },
        "split": {
            "name": "模块拆分",
            "default_timing": EvolutionTiming.SCHEDULED,
            "default_risk": EvolutionRiskLevel.HIGH,
            "resource_level": EvolutionResourceLevel.HIGH
        },
        "replacement": {
            "name": "模块替换",
            "default_timing": EvolutionTiming.SCHEDULED,
            "default_risk": EvolutionRiskLevel.HIGH,
            "resource_level": EvolutionResourceLevel.EXTENSIVE
        }
    }
    
    TRIGGER_PRIORITY_WEIGHTS = {
        "performance_issue": 0.9,
        "bug_report": 0.85,
        "security_issue": 0.95,
        "requirement_change": 0.75,
        "dependency_update": 0.65,
        "user_feedback": 0.7,
        "automated_detection": 0.6,
        "manual_review": 0.55,
        "scheduled_maintenance": 0.5,
        "code_smell": 0.45
    }
    
    def __init__(
        self,
        knowledge_base_path: Optional[Path] = None,
        logger: Optional[logging.Logger] = None
    ):
        self.logger = logger or logging.getLogger(__name__)
        self.knowledge_base_path = knowledge_base_path
        
        self._evolution_patterns: Dict[str, Dict[str, Any]] = {}
        self._evolution_history: List[Dict[str, Any]] = []
        self._effect_predictions: Dict[str, EvolutionPrediction] = {}
        self._team_preferences: Dict[str, Dict[str, Any]] = {}
        
        self._initialize_default_patterns()
    
    def _initialize_default_patterns(self) -> None:
        self._evolution_patterns = {
            "perf_optimize": {
                "pattern_id": "perf_optimize",
                "evolution_type": "optimization",
                "name": "性能优化模式",
                "description": "针对性能问题的优化演化模式",
                "trigger_conditions": ["performance_issue", "slow_query", "high_memory"],
                "execution_steps": [
                    "分析性能瓶颈",
                    "制定优化方案",
                    "实施优化措施",
                    "验证优化效果",
                    "更新监控指标"
                ],
                "expected_effects": {
                    "performance_gain": 0.3,
                    "resource_efficiency": 0.25
                },
                "success_rate": 0.85,
                "avg_duration": 2.5,
                "risk_factors": ["可能影响稳定性", "需要充分测试"]
            },
            "code_refactor": {
                "pattern_id": "code_refactor",
                "evolution_type": "refactoring",
                "name": "代码重构模式",
                "description": "改善代码结构和可维护性的重构模式",
                "trigger_conditions": ["code_smell", "high_complexity", "duplication"],
                "execution_steps": [
                    "识别重构目标",
                    "设计重构方案",
                    "编写测试用例",
                    "逐步重构代码",
                    "验证功能正确性"
                ],
                "expected_effects": {
                    "code_quality": 0.35,
                    "maintainability": 0.4,
                    "complexity_reduction": 0.3
                },
                "success_rate": 0.78,
                "avg_duration": 5.0,
                "risk_factors": ["可能引入新缺陷", "需要回归测试"]
            },
            "feature_enhance": {
                "pattern_id": "feature_enhance",
                "evolution_type": "enhancement",
                "name": "功能增强模式",
                "description": "基于需求变更的功能增强模式",
                "trigger_conditions": ["requirement_change", "user_feedback"],
                "execution_steps": [
                    "分析需求变更",
                    "设计功能方案",
                    "实现新功能",
                    "更新文档",
                    "集成测试"
                ],
                "expected_effects": {
                    "functionality": 0.4,
                    "user_satisfaction": 0.35
                },
                "success_rate": 0.82,
                "avg_duration": 8.0,
                "risk_factors": ["可能影响现有功能", "需要用户验收"]
            },
            "bug_fix_pattern": {
                "pattern_id": "bug_fix_pattern",
                "evolution_type": "bug_fix",
                "name": "缺陷修复模式",
                "description": "快速响应和修复缺陷的模式",
                "trigger_conditions": ["bug_report", "security_issue"],
                "execution_steps": [
                    "复现问题",
                    "定位根因",
                    "实施修复",
                    "编写回归测试",
                    "验证修复效果"
                ],
                "expected_effects": {
                    "bug_fix_rate": 0.9,
                    "stability": 0.3
                },
                "success_rate": 0.92,
                "avg_duration": 1.5,
                "risk_factors": ["可能引入回归问题"]
            },
            "dependency_update": {
                "pattern_id": "dependency_update",
                "evolution_type": "adaptation",
                "name": "依赖更新模式",
                "description": "更新外部依赖以适应环境变化",
                "trigger_conditions": ["dependency_update", "security_issue"],
                "execution_steps": [
                    "检查依赖版本",
                    "评估兼容性",
                    "更新依赖配置",
                    "运行测试套件",
                    "部署验证"
                ],
                "expected_effects": {
                    "security": 0.4,
                    "compatibility": 0.35
                },
                "success_rate": 0.75,
                "avg_duration": 2.0,
                "risk_factors": ["可能存在兼容性问题", "需要全面测试"]
            },
            "module_split": {
                "pattern_id": "module_split",
                "evolution_type": "split",
                "name": "模块拆分模式",
                "description": "将大型模块拆分为更小的独立模块",
                "trigger_conditions": ["high_coupling", "large_module", "scalability_issue"],
                "execution_steps": [
                    "分析模块边界",
                    "设计拆分方案",
                    "创建新模块",
                    "迁移功能代码",
                    "更新依赖关系",
                    "验证功能完整性"
                ],
                "expected_effects": {
                    "modularity": 0.45,
                    "maintainability": 0.35,
                    "scalability": 0.3
                },
                "success_rate": 0.68,
                "avg_duration": 12.0,
                "risk_factors": ["复杂度高", "需要重构依赖", "可能影响性能"]
            },
            "module_merge": {
                "pattern_id": "module_merge",
                "evolution_type": "merge",
                "name": "模块合并模式",
                "description": "合并相关模块以减少冗余",
                "trigger_conditions": ["duplication", "tight_coupling", "maintenance_burden"],
                "execution_steps": [
                    "识别合并目标",
                    "分析功能重叠",
                    "设计合并方案",
                    "整合代码",
                    "消除冗余",
                    "验证功能"
                ],
                "expected_effects": {
                    "code_reduction": 0.25,
                    "maintainability": 0.3,
                    "consistency": 0.35
                },
                "success_rate": 0.72,
                "avg_duration": 10.0,
                "risk_factors": ["可能引入冲突", "需要大量测试"]
            }
        }
    
    def get_evolution_recommendations(
        self,
        skill_id: str,
        context: Dict[str, Any],
        limit: int = 10
    ) -> List[EvolutionRecommendation]:
        recommendations = []
        
        health_data = context.get("health_assessment", {})
        metrics = context.get("metrics", {})
        issues = context.get("issues", [])
        triggers = context.get("triggers", [])
        
        for pattern_id, pattern in self._evolution_patterns.items():
            if self._matches_context(pattern, context):
                recommendation = self._create_recommendation(
                    pattern, skill_id, context
                )
                recommendations.append(recommendation)
        
        for issue in issues:
            issue_recommendations = self._recommend_for_issue(
                issue, skill_id, context
            )
            recommendations.extend(issue_recommendations)
        
        for trigger in triggers:
            trigger_recommendations = self._recommend_for_trigger(
                trigger, skill_id, context
            )
            recommendations.extend(trigger_recommendations)
        
        seen_ids = set()
        unique_recommendations = []
        for rec in recommendations:
            if rec.recommendation_id not in seen_ids:
                seen_ids.add(rec.recommendation_id)
                unique_recommendations.append(rec)
        
        sorted_recommendations = self.prioritize_evolutions(unique_recommendations)
        
        return sorted_recommendations[:limit]
    
    def _matches_context(self, pattern: Dict[str, Any], context: Dict[str, Any]) -> bool:
        triggers = context.get("triggers", [])
        issues = context.get("issues", [])
        metrics = context.get("metrics", {})
        
        pattern_triggers = pattern.get("trigger_conditions", [])
        
        for trigger in triggers:
            if trigger in pattern_triggers:
                return True
        
        for issue in issues:
            issue_lower = issue.lower()
            for pt in pattern_triggers:
                if pt.replace("_", " ") in issue_lower:
                    return True
        
        evolution_type = pattern.get("evolution_type", "")
        if evolution_type == "optimization":
            if metrics.get("performance_score", 100) < 70:
                return True
            if metrics.get("response_time", 0) > 1000:
                return True
        elif evolution_type == "refactoring":
            if metrics.get("code_complexity", 0) > 15:
                return True
            if metrics.get("duplication_rate", 0) > 5:
                return True
        elif evolution_type == "bug_fix":
            if metrics.get("bug_count", 0) > 0:
                return True
            if metrics.get("security_issues", 0) > 0:
                return True
        
        return False
    
    def _create_recommendation(
        self,
        pattern: Dict[str, Any],
        skill_id: str,
        context: Dict[str, Any]
    ) -> EvolutionRecommendation:
        recommendation_id = f"EVO-REC-{pattern['pattern_id']}-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        evolution_type = pattern.get("evolution_type", "optimization")
        type_config = self.EVOLUTION_TYPE_MAPPING.get(evolution_type, {})
        
        risk_level = self._assess_risk(pattern, context)
        timing = self._determine_timing(pattern, context)
        resource_level = type_config.get("resource_level", EvolutionResourceLevel.MEDIUM)
        
        expected_effects = pattern.get("expected_effects", {})
        adjusted_effects = self._adjust_expected_effects(expected_effects, context)
        
        confidence = self._calculate_confidence(pattern, context)
        success_rate = pattern.get("success_rate", 0.5)
        
        return EvolutionRecommendation(
            recommendation_id=recommendation_id,
            evolution_type=evolution_type,
            title=pattern.get("name", "演化推荐"),
            description=pattern.get("description", ""),
            trigger_reason=self._generate_trigger_reason(pattern, context),
            execution_steps=pattern.get("execution_steps", []),
            expected_effects=adjusted_effects,
            risk_level=risk_level,
            timing=timing,
            resource_level=resource_level,
            confidence=confidence,
            success_rate=success_rate,
            related_patterns=[pattern.get("pattern_id", "")],
            prerequisites=self._get_prerequisites(pattern, context),
            estimated_duration=f"{pattern.get('avg_duration', 3.0):.1f} 天",
            affected_components=self._get_affected_components(context),
            tags=[evolution_type, pattern.get("pattern_id", "")],
            metadata={
                "pattern_id": pattern.get("pattern_id"),
                "skill_id": skill_id
            }
        )
    
    def _recommend_for_issue(
        self,
        issue: str,
        skill_id: str,
        context: Dict[str, Any]
    ) -> List[EvolutionRecommendation]:
        recommendations = []
        issue_lower = issue.lower()
        
        if any(kw in issue_lower for kw in ["performance", "slow", "timeout", "latency"]):
            recommendations.append(self._create_recommendation(
                self._evolution_patterns["perf_optimize"],
                skill_id,
                {**context, "triggers": ["performance_issue"]}
            ))
        
        if any(kw in issue_lower for kw in ["bug", "error", "crash", "fail"]):
            recommendations.append(self._create_recommendation(
                self._evolution_patterns["bug_fix_pattern"],
                skill_id,
                {**context, "triggers": ["bug_report"]}
            ))
        
        if any(kw in issue_lower for kw in ["security", "vulnerability", "injection"]):
            recommendations.append(self._create_recommendation(
                self._evolution_patterns["bug_fix_pattern"],
                skill_id,
                {**context, "triggers": ["security_issue"]}
            ))
        
        if any(kw in issue_lower for kw in ["complex", "duplicate", "smell", "refactor"]):
            recommendations.append(self._create_recommendation(
                self._evolution_patterns["code_refactor"],
                skill_id,
                {**context, "triggers": ["code_smell"]}
            ))
        
        return recommendations
    
    def _recommend_for_trigger(
        self,
        trigger: str,
        skill_id: str,
        context: Dict[str, Any]
    ) -> List[EvolutionRecommendation]:
        recommendations = []
        
        trigger_pattern_mapping = {
            "performance_issue": "perf_optimize",
            "bug_report": "bug_fix_pattern",
            "security_issue": "bug_fix_pattern",
            "code_smell": "code_refactor",
            "requirement_change": "feature_enhance",
            "dependency_update": "dependency_update",
            "user_feedback": "feature_enhance",
            "high_coupling": "module_split",
            "duplication": "module_merge"
        }
        
        pattern_id = trigger_pattern_mapping.get(trigger)
        if pattern_id and pattern_id in self._evolution_patterns:
            recommendations.append(self._create_recommendation(
                self._evolution_patterns[pattern_id],
                skill_id,
                {**context, "triggers": [trigger]}
            ))
        
        return recommendations
    
    def prioritize_evolutions(
        self,
        recommendations: List[EvolutionRecommendation],
        strategy: str = "balanced"
    ) -> List[EvolutionRecommendation]:
        if not recommendations:
            return []
        
        scored_recommendations = []
        for rec in recommendations:
            priority_score = self._calculate_priority_score(rec, strategy)
            rec.priority_score = priority_score.final_score
            rec.metadata["priority_details"] = priority_score.to_dict()
            scored_recommendations.append((rec, priority_score.final_score))
        
        scored_recommendations.sort(key=lambda x: x[1], reverse=True)
        
        return [rec for rec, _ in scored_recommendations]
    
    def _calculate_priority_score(
        self,
        recommendation: EvolutionRecommendation,
        strategy: str
    ) -> EvolutionPriorityScore:
        effect_score = self._calculate_effect_score(recommendation)
        risk_score = self._calculate_risk_score(recommendation)
        resource_score = self._calculate_resource_score(recommendation)
        urgency_score = self._calculate_urgency_score(recommendation)
        historical_score = self._calculate_historical_score(recommendation)
        
        weights = self._get_strategy_weights(strategy)
        
        final_score = (
            effect_score * weights["effect"] +
            (1 - risk_score) * weights["risk"] +
            (1 - resource_score) * weights["resource"] +
            urgency_score * weights["urgency"] +
            historical_score * weights["historical"]
        )
        
        return EvolutionPriorityScore(
            score_id=f"PRI-{recommendation.recommendation_id[:12]}",
            effect_score=effect_score,
            risk_score=risk_score,
            resource_score=resource_score,
            urgency_score=urgency_score,
            historical_score=historical_score,
            final_score=final_score,
            ranking_factors={
                "strategy": strategy,
                "weights": weights
            }
        )
    
    def _get_strategy_weights(self, strategy: str) -> Dict[str, float]:
        strategies = {
            "balanced": {
                "effect": 0.25,
                "risk": 0.25,
                "resource": 0.15,
                "urgency": 0.20,
                "historical": 0.15
            },
            "aggressive": {
                "effect": 0.35,
                "risk": 0.15,
                "resource": 0.10,
                "urgency": 0.30,
                "historical": 0.10
            },
            "conservative": {
                "effect": 0.15,
                "risk": 0.35,
                "resource": 0.20,
                "urgency": 0.15,
                "historical": 0.15
            },
            "efficiency": {
                "effect": 0.20,
                "risk": 0.20,
                "resource": 0.35,
                "urgency": 0.15,
                "historical": 0.10
            }
        }
        return strategies.get(strategy, strategies["balanced"])
    
    def _calculate_effect_score(self, recommendation: EvolutionRecommendation) -> float:
        effects = recommendation.expected_effects
        if not effects:
            return 0.5
        
        effect_values = list(effects.values())
        avg_effect = statistics.mean(effect_values) if effect_values else 0.5
        
        confidence_factor = recommendation.confidence
        success_factor = recommendation.success_rate
        
        return avg_effect * 0.5 + confidence_factor * 0.3 + success_factor * 0.2
    
    def _calculate_risk_score(self, recommendation: EvolutionRecommendation) -> float:
        risk_scores = {
            EvolutionRiskLevel.LOW: 0.2,
            EvolutionRiskLevel.MEDIUM: 0.5,
            EvolutionRiskLevel.HIGH: 0.75,
            EvolutionRiskLevel.CRITICAL: 0.95
        }
        
        base_risk = risk_scores.get(recommendation.risk_level, 0.5)
        
        complexity_factor = len(recommendation.execution_steps) / 10.0
        component_factor = len(recommendation.affected_components) / 20.0
        
        adjusted_risk = base_risk + complexity_factor * 0.1 + component_factor * 0.1
        
        return min(adjusted_risk, 1.0)
    
    def _calculate_resource_score(self, recommendation: EvolutionRecommendation) -> float:
        resource_scores = {
            EvolutionResourceLevel.MINIMAL: 0.1,
            EvolutionResourceLevel.LOW: 0.25,
            EvolutionResourceLevel.MEDIUM: 0.5,
            EvolutionResourceLevel.HIGH: 0.75,
            EvolutionResourceLevel.EXTENSIVE: 0.95
        }
        
        return resource_scores.get(recommendation.resource_level, 0.5)
    
    def _calculate_urgency_score(self, recommendation: EvolutionRecommendation) -> float:
        timing_scores = {
            EvolutionTiming.IMMEDIATE: 1.0,
            EvolutionTiming.SOON: 0.75,
            EvolutionTiming.SCHEDULED: 0.5,
            EvolutionTiming.DEFERRED: 0.25
        }
        
        base_urgency = timing_scores.get(recommendation.timing, 0.5)
        
        trigger_weights = self.TRIGGER_PRIORITY_WEIGHTS
        trigger_reason = recommendation.trigger_reason.lower()
        
        for trigger, weight in trigger_weights.items():
            if trigger.replace("_", " ") in trigger_reason:
                base_urgency = max(base_urgency, weight)
                break
        
        return base_urgency
    
    def _calculate_historical_score(self, recommendation: EvolutionRecommendation) -> float:
        if not self._evolution_history:
            return 0.5
        
        similar_evolutions = [
            h for h in self._evolution_history
            if h.get("evolution_type") == recommendation.evolution_type
        ]
        
        if not similar_evolutions:
            return 0.5
        
        success_count = sum(1 for h in similar_evolutions if h.get("success", False))
        success_rate = success_count / len(similar_evolutions)
        
        recency_bonus = 0.0
        if similar_evolutions:
            recent = sorted(similar_evolutions, key=lambda x: x.get("timestamp", ""), reverse=True)
            if recent:
                recency_bonus = 0.1
        
        return min(success_rate + recency_bonus, 1.0)
    
    def predict_evolution_effect(
        self,
        evolution_pattern: Dict[str, Any],
        context: Dict[str, Any]
    ) -> EvolutionPrediction:
        prediction_id = f"PRED-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        evolution_type = evolution_pattern.get("evolution_type", "optimization")
        
        performance_improvement = self._predict_performance_improvement(evolution_pattern, context)
        quality_improvement = self._predict_quality_improvement(evolution_pattern, context)
        maintainability_change = self._predict_maintainability_change(evolution_pattern, context)
        
        risk_score = self._predict_risk_score(evolution_pattern, context)
        success_probability = self._predict_success_probability(evolution_pattern, context)
        
        predicted_duration = evolution_pattern.get("avg_duration", 3.0)
        resource_consumption = self._estimate_resource_consumption(evolution_pattern, context)
        
        potential_issues = self._identify_potential_issues(evolution_pattern, context)
        recommendations = self._generate_prediction_recommendations(evolution_pattern, context)
        
        metrics_before = context.get("metrics", {})
        metrics_after = self._predict_metrics_after(metrics_before, evolution_pattern)
        
        confidence = self._calculate_prediction_confidence(evolution_pattern, context)
        
        return EvolutionPrediction(
            prediction_id=prediction_id,
            evolution_type=evolution_type,
            performance_improvement=performance_improvement,
            quality_improvement=quality_improvement,
            maintainability_change=maintainability_change,
            risk_score=risk_score,
            confidence=confidence,
            predicted_duration=predicted_duration,
            resource_consumption=resource_consumption,
            success_probability=success_probability,
            potential_issues=potential_issues,
            recommendations=recommendations,
            metrics_before=metrics_before,
            metrics_after=metrics_after
        )
    
    def _predict_performance_improvement(
        self,
        pattern: Dict[str, Any],
        context: Dict[str, Any]
    ) -> float:
        base_improvement = pattern.get("expected_effects", {}).get("performance_gain", 0.1)
        
        metrics = context.get("metrics", {})
        current_performance = metrics.get("performance_score", 80)
        
        if current_performance < 50:
            improvement_factor = 1.5
        elif current_performance < 70:
            improvement_factor = 1.2
        else:
            improvement_factor = 0.8
        
        success_rate = pattern.get("success_rate", 0.5)
        
        return min(base_improvement * improvement_factor * success_rate, 0.5)
    
    def _predict_quality_improvement(
        self,
        pattern: Dict[str, Any],
        context: Dict[str, Any]
    ) -> float:
        base_improvement = pattern.get("expected_effects", {}).get("code_quality", 0.1)
        
        metrics = context.get("metrics", {})
        current_quality = metrics.get("code_quality_score", 80)
        
        if current_quality < 60:
            improvement_factor = 1.4
        elif current_quality < 80:
            improvement_factor = 1.1
        else:
            improvement_factor = 0.7
        
        success_rate = pattern.get("success_rate", 0.5)
        
        return min(base_improvement * improvement_factor * success_rate, 0.4)
    
    def _predict_maintainability_change(
        self,
        pattern: Dict[str, Any],
        context: Dict[str, Any]
    ) -> float:
        base_change = pattern.get("expected_effects", {}).get("maintainability", 0.1)
        
        metrics = context.get("metrics", {})
        complexity = metrics.get("code_complexity", 10)
        duplication = metrics.get("duplication_rate", 0)
        
        complexity_factor = min(complexity / 15.0, 1.5)
        duplication_factor = min(duplication / 5.0, 1.3)
        
        return min(base_change * (1 + complexity_factor * 0.2 + duplication_factor * 0.1), 0.35)
    
    def _predict_risk_score(
        self,
        pattern: Dict[str, Any],
        context: Dict[str, Any]
    ) -> float:
        evolution_type = pattern.get("evolution_type", "optimization")
        
        type_risk = {
            "optimization": 0.3,
            "refactoring": 0.5,
            "enhancement": 0.45,
            "bug_fix": 0.25,
            "adaptation": 0.4,
            "extension": 0.5,
            "deprecation": 0.35,
            "merge": 0.65,
            "split": 0.7,
            "replacement": 0.75
        }
        
        base_risk = type_risk.get(evolution_type, 0.5)
        
        steps_count = len(pattern.get("execution_steps", []))
        steps_factor = min(steps_count / 8.0, 0.2)
        
        success_rate = pattern.get("success_rate", 0.5)
        success_factor = (1 - success_rate) * 0.3
        
        return min(base_risk + steps_factor + success_factor, 1.0)
    
    def _predict_success_probability(
        self,
        pattern: Dict[str, Any],
        context: Dict[str, Any]
    ) -> float:
        base_probability = pattern.get("success_rate", 0.5)
        
        health_data = context.get("health_assessment", {})
        health_score = health_data.get("overall_score", 70)
        
        if health_score >= 80:
            health_factor = 1.1
        elif health_score >= 60:
            health_factor = 1.0
        else:
            health_factor = 0.85
        
        similar_count = sum(
            1 for h in self._evolution_history
            if h.get("evolution_type") == pattern.get("evolution_type")
        )
        history_factor = min(1 + similar_count * 0.02, 1.15)
        
        return min(base_probability * health_factor * history_factor, 0.98)
    
    def _estimate_resource_consumption(
        self,
        pattern: Dict[str, Any],
        context: Dict[str, Any]
    ) -> float:
        base_duration = pattern.get("avg_duration", 3.0)
        
        steps_count = len(pattern.get("execution_steps", []))
        steps_factor = steps_count / 5.0
        
        complexity = context.get("metrics", {}).get("code_complexity", 10)
        complexity_factor = complexity / 10.0
        
        return min(base_duration * (1 + steps_factor * 0.1 + complexity_factor * 0.1), 20.0)
    
    def _identify_potential_issues(
        self,
        pattern: Dict[str, Any],
        context: Dict[str, Any]
    ) -> List[str]:
        issues = []
        
        risk_factors = pattern.get("risk_factors", [])
        issues.extend(risk_factors)
        
        metrics = context.get("metrics", {})
        
        if metrics.get("test_coverage", 100) < 50:
            issues.append("测试覆盖率较低，演化可能引入未发现的问题")
        
        if metrics.get("code_complexity", 0) > 20:
            issues.append("代码复杂度高，演化难度增加")
        
        if len(context.get("dependencies", [])) > 20:
            issues.append("依赖项较多，演化可能影响其他组件")
        
        if metrics.get("security_issues", 0) > 0:
            issues.append("存在安全问题，建议优先处理")
        
        return issues[:5]
    
    def _generate_prediction_recommendations(
        self,
        pattern: Dict[str, Any],
        context: Dict[str, Any]
    ) -> List[str]:
        recommendations = []
        
        steps = pattern.get("execution_steps", [])
        if len(steps) > 5:
            recommendations.append("演化步骤较多，建议分阶段执行并验证中间结果")
        
        metrics = context.get("metrics", {})
        
        if metrics.get("test_coverage", 100) < 70:
            recommendations.append("建议先提高测试覆盖率再进行演化")
        
        if metrics.get("code_complexity", 0) > 15:
            recommendations.append("建议先简化复杂逻辑再进行演化")
        
        evolution_type = pattern.get("evolution_type", "")
        if evolution_type in ["merge", "split", "replacement"]:
            recommendations.append("此演化类型风险较高，建议在非生产环境充分测试")
        
        if not recommendations:
            recommendations.append("建议按照执行步骤逐步实施，并在每个阶段进行验证")
        
        return recommendations
    
    def _predict_metrics_after(
        self,
        metrics_before: Dict[str, float],
        pattern: Dict[str, Any]
    ) -> Dict[str, float]:
        metrics_after = metrics_before.copy()
        
        expected_effects = pattern.get("expected_effects", {})
        
        if "performance_gain" in expected_effects:
            current = metrics_before.get("performance_score", 80)
            improvement = expected_effects["performance_gain"] * 100
            metrics_after["performance_score"] = min(current + improvement, 100)
        
        if "code_quality" in expected_effects:
            current = metrics_before.get("code_quality_score", 80)
            improvement = expected_effects["code_quality"] * 100
            metrics_after["code_quality_score"] = min(current + improvement, 100)
        
        if "complexity_reduction" in expected_effects:
            current = metrics_before.get("code_complexity", 10)
            reduction = expected_effects["complexity_reduction"]
            metrics_after["code_complexity"] = max(current * (1 - reduction), 1)
        
        return metrics_after
    
    def _calculate_prediction_confidence(
        self,
        pattern: Dict[str, Any],
        context: Dict[str, Any]
    ) -> float:
        base_confidence = pattern.get("success_rate", 0.5)
        
        usage_count = pattern.get("usage_count", 0)
        usage_factor = min(1 + usage_count * 0.01, 1.2)
        
        similar_evolutions = sum(
            1 for h in self._evolution_history
            if h.get("evolution_type") == pattern.get("evolution_type")
        )
        history_factor = min(1 + similar_evolutions * 0.02, 1.15)
        
        metrics_completeness = len(context.get("metrics", {})) / 10.0
        context_factor = min(0.8 + metrics_completeness * 0.2, 1.0)
        
        return min(base_confidence * usage_factor * history_factor * context_factor, 0.95)
    
    def get_personalized_recommendations(
        self,
        skill_id: str,
        user_preferences: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> PersonalizedEvolutionSuggestion:
        context = context or {}
        
        base_recommendations = self.get_evolution_recommendations(skill_id, context, limit=20)
        
        personalized_recommendations = self._apply_personalization(
            base_recommendations, user_preferences, context
        )
        
        project_characteristics = self._extract_project_characteristics(context)
        historical_context = self._build_historical_context(skill_id)
        
        confidence = self._calculate_personalization_confidence(
            user_preferences, context, historical_context
        )
        
        return PersonalizedEvolutionSuggestion(
            suggestion_id=f"PERS-{skill_id[:8]}-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            skill_id=skill_id,
            recommendations=personalized_recommendations[:10],
            user_preferences=user_preferences,
            project_characteristics=project_characteristics,
            historical_context=historical_context,
            confidence=confidence
        )
    
    def _apply_personalization(
        self,
        recommendations: List[EvolutionRecommendation],
        user_preferences: Dict[str, Any],
        context: Dict[str, Any]
    ) -> List[EvolutionRecommendation]:
        preferred_types = user_preferences.get("preferred_evolution_types", [])
        risk_tolerance = user_preferences.get("risk_tolerance", "medium")
        resource_availability = user_preferences.get("resource_availability", "medium")
        priority_focus = user_preferences.get("priority_focus", "balanced")
        
        risk_tolerance_scores = {
            "low": 0.3,
            "medium": 0.5,
            "high": 0.7
        }
        max_risk = risk_tolerance_scores.get(risk_tolerance, 0.5)
        
        resource_scores = {
            "low": EvolutionResourceLevel.LOW,
            "medium": EvolutionResourceLevel.MEDIUM,
            "high": EvolutionResourceLevel.HIGH
        }
        max_resource = resource_scores.get(resource_availability, EvolutionResourceLevel.MEDIUM)
        
        resource_order = [
            EvolutionResourceLevel.MINIMAL,
            EvolutionResourceLevel.LOW,
            EvolutionResourceLevel.MEDIUM,
            EvolutionResourceLevel.HIGH,
            EvolutionResourceLevel.EXTENSIVE
        ]
        max_resource_idx = resource_order.index(max_resource)
        
        filtered_recommendations = []
        for rec in recommendations:
            risk_scores = {
                EvolutionRiskLevel.LOW: 0.2,
                EvolutionRiskLevel.MEDIUM: 0.5,
                EvolutionRiskLevel.HIGH: 0.75,
                EvolutionRiskLevel.CRITICAL: 0.95
            }
            rec_risk = risk_scores.get(rec.risk_level, 0.5)
            
            if rec_risk > max_risk + 0.2:
                continue
            
            rec_resource_idx = resource_order.index(rec.resource_level)
            if rec_resource_idx > max_resource_idx + 1:
                continue
            
            if preferred_types and rec.evolution_type not in preferred_types:
                rec.priority_score *= 0.7
            
            filtered_recommendations.append(rec)
        
        return self.prioritize_evolutions(filtered_recommendations, priority_focus)
    
    def _extract_project_characteristics(self, context: Dict[str, Any]) -> Dict[str, Any]:
        metrics = context.get("metrics", {})
        health = context.get("health_assessment", {})
        
        return {
            "size": self._categorize_size(metrics),
            "complexity": self._categorize_complexity(metrics),
            "quality_level": self._categorize_quality(metrics),
            "health_status": health.get("health_level", "unknown"),
            "primary_concerns": self._identify_primary_concerns(metrics),
            "improvement_potential": self._calculate_improvement_potential(metrics)
        }
    
    def _categorize_size(self, metrics: Dict[str, float]) -> str:
        loc = metrics.get("lines_of_code", 0)
        if loc < 1000:
            return "small"
        elif loc < 10000:
            return "medium"
        else:
            return "large"
    
    def _categorize_complexity(self, metrics: Dict[str, float]) -> str:
        complexity = metrics.get("code_complexity", 0)
        if complexity < 10:
            return "low"
        elif complexity < 20:
            return "medium"
        else:
            return "high"
    
    def _categorize_quality(self, metrics: Dict[str, float]) -> str:
        quality_score = metrics.get("code_quality_score", 80)
        if quality_score >= 80:
            return "high"
        elif quality_score >= 60:
            return "medium"
        else:
            return "low"
    
    def _identify_primary_concerns(self, metrics: Dict[str, float]) -> List[str]:
        concerns = []
        
        if metrics.get("performance_score", 100) < 70:
            concerns.append("performance")
        if metrics.get("code_complexity", 0) > 15:
            concerns.append("complexity")
        if metrics.get("test_coverage", 100) < 70:
            concerns.append("testing")
        if metrics.get("security_issues", 0) > 0:
            concerns.append("security")
        if metrics.get("duplication_rate", 0) > 5:
            concerns.append("duplication")
        
        return concerns[:3]
    
    def _calculate_improvement_potential(self, metrics: Dict[str, float]) -> float:
        potential = 0.0
        
        performance = metrics.get("performance_score", 100)
        potential += max(0, (100 - performance) / 100) * 0.3
        
        quality = metrics.get("code_quality_score", 100)
        potential += max(0, (100 - quality) / 100) * 0.3
        
        coverage = metrics.get("test_coverage", 100)
        potential += max(0, (100 - coverage) / 100) * 0.2
        
        complexity = metrics.get("code_complexity", 0)
        potential += min(complexity / 30, 1.0) * 0.2
        
        return min(potential, 1.0)
    
    def _build_historical_context(self, skill_id: str) -> Dict[str, Any]:
        skill_history = [
            h for h in self._evolution_history
            if h.get("skill_id") == skill_id
        ]
        
        if not skill_history:
            return {
                "total_evolutions": 0,
                "success_rate": 0.0,
                "common_types": [],
                "avg_duration": 0.0
            }
        
        success_count = sum(1 for h in skill_history if h.get("success", False))
        success_rate = success_count / len(skill_history)
        
        type_counts: Dict[str, int] = {}
        total_duration = 0.0
        
        for h in skill_history:
            evo_type = h.get("evolution_type", "unknown")
            type_counts[evo_type] = type_counts.get(evo_type, 0) + 1
            total_duration += h.get("duration", 0)
        
        common_types = sorted(type_counts.keys(), key=lambda x: type_counts[x], reverse=True)[:3]
        avg_duration = total_duration / len(skill_history)
        
        return {
            "total_evolutions": len(skill_history),
            "success_rate": success_rate,
            "common_types": common_types,
            "avg_duration": avg_duration
        }
    
    def _calculate_personalization_confidence(
        self,
        user_preferences: Dict[str, Any],
        context: Dict[str, Any],
        historical_context: Dict[str, Any]
    ) -> float:
        preference_completeness = len(user_preferences) / 5.0
        preference_factor = min(preference_completeness, 1.0)
        
        metrics_completeness = len(context.get("metrics", {})) / 10.0
        context_factor = min(metrics_completeness, 1.0)
        
        history_count = historical_context.get("total_evolutions", 0)
        history_factor = min(0.5 + history_count * 0.05, 1.0)
        
        return (preference_factor * 0.4 + context_factor * 0.3 + history_factor * 0.3)
    
    def _assess_risk(self, pattern: Dict[str, Any], context: Dict[str, Any]) -> EvolutionRiskLevel:
        evolution_type = pattern.get("evolution_type", "optimization")
        
        type_risk = {
            "optimization": EvolutionRiskLevel.LOW,
            "refactoring": EvolutionRiskLevel.MEDIUM,
            "enhancement": EvolutionRiskLevel.MEDIUM,
            "bug_fix": EvolutionRiskLevel.LOW,
            "adaptation": EvolutionRiskLevel.MEDIUM,
            "extension": EvolutionRiskLevel.MEDIUM,
            "deprecation": EvolutionRiskLevel.LOW,
            "merge": EvolutionRiskLevel.HIGH,
            "split": EvolutionRiskLevel.HIGH,
            "replacement": EvolutionRiskLevel.HIGH
        }
        
        base_risk = type_risk.get(evolution_type, EvolutionRiskLevel.MEDIUM)
        
        metrics = context.get("metrics", {})
        
        if metrics.get("test_coverage", 100) < 50:
            if base_risk == EvolutionRiskLevel.LOW:
                return EvolutionRiskLevel.MEDIUM
            elif base_risk == EvolutionRiskLevel.MEDIUM:
                return EvolutionRiskLevel.HIGH
        
        if metrics.get("code_complexity", 0) > 20:
            if base_risk != EvolutionRiskLevel.CRITICAL:
                risks = list(EvolutionRiskLevel)
                current_idx = risks.index(base_risk)
                return risks[min(current_idx + 1, len(risks) - 1)]
        
        return base_risk
    
    def _determine_timing(self, pattern: Dict[str, Any], context: Dict[str, Any]) -> EvolutionTiming:
        evolution_type = pattern.get("evolution_type", "optimization")
        type_config = self.EVOLUTION_TYPE_MAPPING.get(evolution_type, {})
        base_timing = type_config.get("default_timing", EvolutionTiming.SCHEDULED)
        
        metrics = context.get("metrics", {})
        
        if evolution_type == "bug_fix":
            if metrics.get("security_issues", 0) > 0:
                return EvolutionTiming.IMMEDIATE
            return EvolutionTiming.SOON
        
        if evolution_type == "optimization":
            if metrics.get("performance_score", 100) < 50:
                return EvolutionTiming.IMMEDIATE
            elif metrics.get("performance_score", 100) < 70:
                return EvolutionTiming.SOON
        
        return base_timing
    
    def _adjust_expected_effects(
        self,
        effects: Dict[str, float],
        context: Dict[str, Any]
    ) -> Dict[str, float]:
        adjusted = effects.copy()
        
        metrics = context.get("metrics", {})
        
        for key in adjusted:
            if key == "performance_gain":
                current_perf = metrics.get("performance_score", 80)
                if current_perf < 50:
                    adjusted[key] *= 1.5
                elif current_perf > 90:
                    adjusted[key] *= 0.5
            
            elif key == "code_quality":
                current_quality = metrics.get("code_quality_score", 80)
                if current_quality < 60:
                    adjusted[key] *= 1.3
                elif current_quality > 90:
                    adjusted[key] *= 0.6
        
        return adjusted
    
    def _calculate_confidence(self, pattern: Dict[str, Any], context: Dict[str, Any]) -> float:
        base_confidence = pattern.get("success_rate", 0.5)
        
        usage_count = pattern.get("usage_count", 0)
        usage_factor = min(1 + usage_count * 0.01, 1.2)
        
        metrics = context.get("metrics", {})
        metrics_factor = min(len(metrics) / 10.0, 1.0) * 0.2 + 0.8
        
        return min(base_confidence * usage_factor * metrics_factor, 0.95)
    
    def _generate_trigger_reason(self, pattern: Dict[str, Any], context: Dict[str, Any]) -> str:
        triggers = context.get("triggers", [])
        issues = context.get("issues", [])
        
        if triggers:
            trigger_names = [t.replace("_", " ").title() for t in triggers[:2]]
            return f"检测到触发条件: {', '.join(trigger_names)}"
        
        if issues:
            return f"基于问题分析: {issues[0][:50]}..."
        
        return f"基于演化模式: {pattern.get('name', '未知模式')}"
    
    def _get_prerequisites(self, pattern: Dict[str, Any], context: Dict[str, Any]) -> List[str]:
        prerequisites = []
        
        metrics = context.get("metrics", {})
        
        if metrics.get("test_coverage", 100) < 50:
            prerequisites.append("提高测试覆盖率至50%以上")
        
        if metrics.get("code_complexity", 0) > 20:
            prerequisites.append("降低代码复杂度")
        
        evolution_type = pattern.get("evolution_type", "")
        if evolution_type in ["merge", "split", "replacement"]:
            prerequisites.append("创建完整备份")
            prerequisites.append("准备回滚方案")
        
        return prerequisites[:5]
    
    def _get_affected_components(self, context: Dict[str, Any]) -> List[str]:
        components = []
        
        files = context.get("affected_files", [])
        for f in files[:5]:
            components.append(Path(f).stem)
        
        return list(set(components))[:10]
    
    def add_evolution_history(self, record: Dict[str, Any]) -> None:
        self._evolution_history.append({
            **record,
            "timestamp": datetime.now().isoformat()
        })
        
        if len(self._evolution_history) > 1000:
            self._evolution_history = self._evolution_history[-1000:]
    
    def set_team_preferences(self, team_id: str, preferences: Dict[str, Any]) -> None:
        self._team_preferences[team_id] = preferences
    
    def get_evolution_statistics(self) -> Dict[str, Any]:
        if not self._evolution_history:
            return {
                "total_evolutions": 0,
                "success_rate": 0.0,
                "type_distribution": {},
                "avg_duration": 0.0
            }
        
        success_count = sum(1 for h in self._evolution_history if h.get("success", False))
        success_rate = success_count / len(self._evolution_history)
        
        type_counts: Dict[str, int] = {}
        total_duration = 0.0
        
        for h in self._evolution_history:
            evo_type = h.get("evolution_type", "unknown")
            type_counts[evo_type] = type_counts.get(evo_type, 0) + 1
            total_duration += h.get("duration", 0)
        
        return {
            "total_evolutions": len(self._evolution_history),
            "success_rate": round(success_rate, 4),
            "type_distribution": type_counts,
            "avg_duration": round(total_duration / len(self._evolution_history), 2)
        }


class RecommendationEngine:
    """推荐引擎主类
    
    整合最佳实践推荐、优化建议推荐、个性化推荐和演化推荐功能。
    """

    def __init__(
        self,
        storage_path: Optional[Path] = None,
        knowledge_base_path: Optional[Path] = None,
        logger: Optional[logging.Logger] = None
    ):
        self.logger = logger or logging.getLogger(__name__)
        self.storage_path = storage_path or Path("recommendation_data")
        self.knowledge_base_path = knowledge_base_path

        self.best_practice_recommender = BestPracticeRecommender(logger)
        self.optimization_recommender = OptimizationRecommender(logger)
        self.personalized_recommender = PersonalizedRecommender(logger)
        self.effect_tracker = RecommendationEffectTracker(logger)
        self.evolution_recommender = EvolutionRecommender(knowledge_base_path, logger)

        self._recommendations: List[Recommendation] = []
        self._evolution_recommendations: List[EvolutionRecommendation] = []
        self._context: Dict[str, Any] = {}

    def set_context(self, context: Dict[str, Any]) -> None:
        self._context = context

    def generate_recommendations(
        self,
        category: Optional[RecommendationCategory] = None,
        user_id: Optional[str] = None,
        include_personalized: bool = True
    ) -> List[Recommendation]:
        self.logger.info("开始生成推荐...")

        all_recommendations: List[Recommendation] = []

        bp_recommendations = self.best_practice_recommender.generate_recommendations(
            self._context, category
        )
        all_recommendations.extend(bp_recommendations)

        opt_recommendations = self.optimization_recommender.generate_recommendations(
            self._context, category
        )
        all_recommendations.extend(opt_recommendations)

        if include_personalized and user_id:
            self._context["base_recommendations"] = all_recommendations
            all_recommendations = self.personalized_recommender.generate_recommendations(
                self._context, category, user_id
            )

        seen_ids: Set[str] = set()
        unique_recommendations: List[Recommendation] = []
        for rec in all_recommendations:
            if rec.recommendation_id not in seen_ids:
                seen_ids.add(rec.recommendation_id)
                unique_recommendations.append(rec)

        self._recommendations = sorted(
            unique_recommendations,
            key=lambda r: (r.priority.value, -r.impact_score)
        )

        return self._recommendations

    def get_recommendations_by_category(
        self,
        category: RecommendationCategory
    ) -> List[Recommendation]:
        return [r for r in self._recommendations if r.category == category]

    def get_recommendations_by_priority(
        self,
        priority: RecommendationPriority
    ) -> List[Recommendation]:
        return [r for r in self._recommendations if r.priority == priority]

    def accept_recommendation(self, recommendation_id: str, user_id: str) -> bool:
        recommendation = self._find_recommendation(recommendation_id)
        if not recommendation:
            return False

        recommendation.status = RecommendationStatus.ACCEPTED

        feedback = RecommendationFeedback(
            recommendation_id=recommendation_id,
            user_id=user_id,
            action="accepted"
        )
        self.personalized_recommender.record_feedback(feedback)
        self.effect_tracker.record_feedback(feedback)

        return True

    def reject_recommendation(
        self,
        recommendation_id: str,
        user_id: str,
        reason: Optional[str] = None
    ) -> bool:
        recommendation = self._find_recommendation(recommendation_id)
        if not recommendation:
            return False

        recommendation.status = RecommendationStatus.REJECTED

        feedback = RecommendationFeedback(
            recommendation_id=recommendation_id,
            user_id=user_id,
            action="rejected",
            comment=reason
        )
        self.personalized_recommender.record_feedback(feedback)
        self.effect_tracker.record_feedback(feedback)

        return True

    def implement_recommendation(
        self,
        recommendation_id: str,
        user_id: str,
        implementation_time: float,
        actual_impact: Optional[float] = None,
        rating: Optional[int] = None
    ) -> bool:
        recommendation = self._find_recommendation(recommendation_id)
        if not recommendation:
            return False

        recommendation.status = RecommendationStatus.IMPLEMENTED

        feedback = RecommendationFeedback(
            recommendation_id=recommendation_id,
            user_id=user_id,
            action="implemented",
            rating=rating,
            implementation_time=implementation_time,
            actual_impact=actual_impact
        )
        self.personalized_recommender.record_feedback(feedback)
        self.effect_tracker.record_feedback(feedback)

        return True

    def _find_recommendation(self, recommendation_id: str) -> Optional[Recommendation]:
        for rec in self._recommendations:
            if rec.recommendation_id == recommendation_id:
                return rec
        return None

    def track_view(self, recommendation_id: str) -> None:
        self.effect_tracker.record_view(recommendation_id)

    def get_recommendation_effect(
        self,
        recommendation_id: str,
        period_days: int = 30
    ) -> Optional[RecommendationEffect]:
        recommendation = self._find_recommendation(recommendation_id)
        if not recommendation:
            return None

        return self.effect_tracker.calculate_effect(
            recommendation_id,
            recommendation.category,
            period_days
        )

    def generate_report(
        self,
        project: str,
        category: Optional[RecommendationCategory] = None,
        user_id: Optional[str] = None
    ) -> RecommendationReport:
        self.logger.info(f"生成推荐报告: {project}")

        recommendations = self.generate_recommendations(
            category=category,
            user_id=user_id
        )

        effects: List[RecommendationEffect] = []
        for rec in recommendations[:20]:
            effect = self.get_recommendation_effect(rec.recommendation_id)
            if effect:
                effects.append(effect)

        summary = self._generate_summary(recommendations, effects)
        top_categories = self._get_top_categories(recommendations)
        improvement_potential = self._calculate_improvement_potential(recommendations)

        return RecommendationReport(
            timestamp=datetime.now().isoformat(),
            project=project,
            recommendations=recommendations,
            effects=effects,
            summary=summary,
            top_categories=top_categories,
            improvement_potential=improvement_potential
        )

    def _generate_summary(
        self,
        recommendations: List[Recommendation],
        effects: List[RecommendationEffect]
    ) -> Dict[str, Any]:
        category_counts: Dict[RecommendationCategory, int] = {}
        for rec in recommendations:
            category_counts[rec.category] = category_counts.get(rec.category, 0) + 1

        priority_counts: Dict[RecommendationPriority, int] = {}
        for rec in recommendations:
            priority_counts[rec.priority] = priority_counts.get(rec.priority, 0) + 1

        avg_impact = 0.0
        if recommendations:
            avg_impact = sum(r.impact_score for r in recommendations) / len(recommendations)

        avg_confidence = 0.0
        if recommendations:
            avg_confidence = sum(r.confidence for r in recommendations) / len(recommendations)

        avg_acceptance = 0.0
        if effects:
            avg_acceptance = sum(e.acceptance_rate for e in effects) / len(effects)

        return {
            "total_recommendations": len(recommendations),
            "category_distribution": {c.value: v for c, v in category_counts.items()},
            "priority_distribution": {p.name: v for p, v in priority_counts.items()},
            "average_impact_score": round(avg_impact, 4),
            "average_confidence": round(avg_confidence, 4),
            "average_acceptance_rate": round(avg_acceptance, 4)
        }

    def _get_top_categories(
        self,
        recommendations: List[Recommendation]
    ) -> List[Dict[str, Any]]:
        category_impact: Dict[RecommendationCategory, List[float]] = {}
        for rec in recommendations:
            if rec.category not in category_impact:
                category_impact[rec.category] = []
            category_impact[rec.category].append(rec.impact_score)

        category_stats = []
        for category, impacts in category_impact.items():
            category_stats.append({
                "category": category.value,
                "count": len(impacts),
                "avg_impact": round(statistics.mean(impacts), 4),
                "max_impact": round(max(impacts), 4)
            })

        return sorted(category_stats, key=lambda x: x["avg_impact"], reverse=True)

    def _calculate_improvement_potential(
        self,
        recommendations: List[Recommendation]
    ) -> float:
        if not recommendations:
            return 0.0

        potential = 0.0
        for rec in recommendations:
            if rec.status == RecommendationStatus.PENDING:
                weight = {
                    RecommendationPriority.CRITICAL: 1.0,
                    RecommendationPriority.HIGH: 0.8,
                    RecommendationPriority.MEDIUM: 0.6,
                    RecommendationPriority.LOW: 0.4,
                    RecommendationPriority.INFO: 0.2
                }.get(rec.priority, 0.5)

                potential += rec.impact_score * weight * rec.confidence

        return min(potential / len(recommendations), 1.0)

    def save_recommendations(self, output_path: Path) -> bool:
        try:
            output_path.parent.mkdir(parents=True, exist_ok=True)

            data = {
                "timestamp": datetime.now().isoformat(),
                "recommendations": [r.to_dict() for r in self._recommendations]
            }

            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            self.logger.info(f"推荐已保存到 {output_path}")
            return True
        except Exception as e:
            self.logger.error(f"保存推荐失败: {e}")
            return False

    def load_recommendations(self, input_path: Path) -> bool:
        try:
            if not input_path.exists():
                return False

            with open(input_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            self._recommendations = []
            for item in data.get("recommendations", []):
                recommendation = Recommendation(
                    recommendation_id=item["recommendation_id"],
                    category=RecommendationCategory(item["category"]),
                    priority=RecommendationPriority(item["priority"]),
                    title=item["title"],
                    description=item["description"],
                    rationale=item["rationale"],
                    actions=item["actions"],
                    impact_score=item["impact_score"],
                    confidence=item["confidence"],
                    effort_estimate=item["effort_estimate"],
                    related_files=item.get("related_files", []),
                    related_metrics=item.get("related_metrics", {}),
                    tags=item.get("tags", []),
                    created_at=item.get("created_at", datetime.now().isoformat()),
                    status=RecommendationStatus(item.get("status", "pending")),
                    source=item.get("source", "system"),
                    metadata=item.get("metadata", {})
                )
                self._recommendations.append(recommendation)

            self.logger.info(f"从 {input_path} 加载了 {len(self._recommendations)} 条推荐")
            return True
        except Exception as e:
            self.logger.error(f"加载推荐失败: {e}")
            return False

    def set_user_preference(self, preference: UserPreference) -> None:
        self.personalized_recommender.set_user_preference(preference)

    def get_evolution_recommendations(
        self,
        skill_id: str,
        context: Optional[Dict[str, Any]] = None,
        limit: int = 10
    ) -> List[EvolutionRecommendation]:
        context = context or self._context
        
        self.logger.info(f"获取演化推荐: skill_id={skill_id}")
        
        recommendations = self.evolution_recommender.get_evolution_recommendations(
            skill_id, context, limit
        )
        
        self._evolution_recommendations = recommendations
        
        return recommendations

    def prioritize_evolutions(
        self,
        recommendations: Optional[List[EvolutionRecommendation]] = None,
        strategy: str = "balanced"
    ) -> List[EvolutionRecommendation]:
        recommendations = recommendations or self._evolution_recommendations
        
        self.logger.info(f"演化优先级排序: strategy={strategy}, count={len(recommendations)}")
        
        return self.evolution_recommender.prioritize_evolutions(recommendations, strategy)

    def predict_evolution_effect(
        self,
        evolution_pattern_id: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Optional[EvolutionPrediction]:
        context = context or self._context
        
        patterns = self.evolution_recommender._evolution_patterns
        pattern = patterns.get(evolution_pattern_id)
        
        if not pattern:
            self.logger.warning(f"演化模式不存在: {evolution_pattern_id}")
            return None
        
        self.logger.info(f"预测演化效果: pattern={evolution_pattern_id}")
        
        return self.evolution_recommender.predict_evolution_effect(pattern, context)

    def get_personalized_evolution_recommendations(
        self,
        skill_id: str,
        user_preferences: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> PersonalizedEvolutionSuggestion:
        context = context or self._context
        
        self.logger.info(f"获取个性化演化建议: skill_id={skill_id}")
        
        return self.evolution_recommender.get_personalized_recommendations(
            skill_id, user_preferences, context
        )

    def integrate_health_assessment(
        self,
        health_report: Dict[str, Any]
    ) -> Dict[str, Any]:
        self._context["health_assessment"] = health_report
        
        recommendations = []
        
        overall_score = health_report.get("overall_score", 0)
        health_level = health_report.get("health_level", "unknown")
        category_results = health_report.get("category_results", [])
        
        for category_result in category_results:
            category = category_result.get("category", "")
            score = category_result.get("score", 0)
            max_score = category_result.get("max_score", 100)
            percentage = category_result.get("percentage", 0)
            
            if percentage < 60:
                items = category_result.get("items", [])
                for item in items:
                    if item.get("percentage", 100) < 50:
                        suggestions = item.get("suggestions", [])
                        for suggestion in suggestions:
                            recommendations.append({
                                "category": category,
                                "priority": "high" if item.get("percentage", 100) < 30 else "medium",
                                "suggestion": suggestion,
                                "source": "health_assessment"
                            })
        
        return {
            "integrated": True,
            "health_level": health_level,
            "overall_score": overall_score,
            "recommendations": recommendations
        }

    def integrate_evolution_knowledge(
        self,
        evolution_patterns: List[Dict[str, Any]]
    ) -> int:
        added_count = 0
        
        for pattern in evolution_patterns:
            pattern_id = pattern.get("pattern_id", "")
            if pattern_id:
                self.evolution_recommender._evolution_patterns[pattern_id] = pattern
                added_count += 1
        
        self.logger.info(f"集成演化知识: {added_count} 个模式")
        
        return added_count

    def record_evolution_result(
        self,
        skill_id: str,
        evolution_type: str,
        success: bool,
        duration: float,
        effects: Optional[Dict[str, float]] = None
    ) -> None:
        record = {
            "skill_id": skill_id,
            "evolution_type": evolution_type,
            "success": success,
            "duration": duration,
            "effects": effects or {}
        }
        
        self.evolution_recommender.add_evolution_history(record)
        
        self.logger.info(f"记录演化结果: skill={skill_id}, type={evolution_type}, success={success}")

    def get_evolution_statistics(self) -> Dict[str, Any]:
        return self.evolution_recommender.get_evolution_statistics()

    def generate_evolution_report(
        self,
        skill_id: str,
        context: Optional[Dict[str, Any]] = None,
        user_preferences: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        context = context or self._context
        
        recommendations = self.get_evolution_recommendations(skill_id, context)
        
        predictions = []
        for rec in recommendations[:5]:
            pattern_id = rec.related_patterns[0] if rec.related_patterns else None
            if pattern_id:
                prediction = self.predict_evolution_effect(pattern_id, context)
                if prediction:
                    predictions.append(prediction.to_dict())
        
        personalized = None
        if user_preferences:
            personalized = self.get_personalized_evolution_recommendations(
                skill_id, user_preferences, context
            )
        
        statistics = self.get_evolution_statistics()
        
        return {
            "timestamp": datetime.now().isoformat(),
            "skill_id": skill_id,
            "recommendations": [r.to_dict() for r in recommendations],
            "predictions": predictions,
            "personalized": personalized.to_dict() if personalized else None,
            "statistics": statistics,
            "summary": {
                "total_recommendations": len(recommendations),
                "high_priority_count": sum(1 for r in recommendations if r.timing == EvolutionTiming.IMMEDIATE),
                "avg_confidence": statistics.get("success_rate", 0),
                "improvement_potential": self._calculate_evolution_potential(recommendations)
            }
        }

    def _calculate_evolution_potential(
        self,
        recommendations: List[EvolutionRecommendation]
    ) -> float:
        if not recommendations:
            return 0.0
        
        potential = 0.0
        for rec in recommendations:
            effects = rec.expected_effects
            if effects:
                avg_effect = sum(effects.values()) / len(effects)
                potential += avg_effect * rec.confidence * rec.success_rate
        
        return min(potential / len(recommendations), 1.0)


def setup_logger(verbose: bool = False) -> logging.Logger:
    logger = logging.getLogger("RecommendationEngine")
    logger.setLevel(logging.DEBUG if verbose else logging.INFO)

    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(logging.DEBUG if verbose else logging.INFO)
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    return logger


def main():
    parser = argparse.ArgumentParser(
        description="推荐引擎",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python recommendation_engine.py --project myproject
  python recommendation_engine.py --type code_quality --output json
  python recommendation_engine.py --personalized --user dev_user
        """
    )

    parser.add_argument(
        "--project",
        type=str,
        default="default",
        help="项目名称 (默认: default)"
    )

    parser.add_argument(
        "--type",
        type=str,
        choices=[c.value for c in RecommendationCategory],
        help="推荐类别"
    )

    parser.add_argument(
        "--user",
        type=str,
        help="用户ID (用于个性化推荐)"
    )

    parser.add_argument(
        "--personalized",
        action="store_true",
        help="启用个性化推荐"
    )

    parser.add_argument(
        "--output",
        choices=["console", "json"],
        default="console",
        help="输出格式 (默认: console)"
    )

    parser.add_argument(
        "--output-file",
        type=str,
        help="输出文件路径"
    )

    parser.add_argument(
        "--verbose",
        action="store_true",
        help="启用详细日志输出"
    )

    args = parser.parse_args()

    logger = setup_logger(args.verbose)

    print("=" * 80)
    print("推荐引擎")
    print("=" * 80)

    engine = RecommendationEngine(logger=logger)

    context = {
        "metrics": {
            "code_complexity": 12,
            "code_coverage": 72,
            "duplication_rate": 4.5,
            "security_issues": 2,
            "slow_queries": 3
        },
        "issues": [
            "High complexity in function process_data",
            "Security vulnerability in input validation",
            "Slow database query detected"
        ]
    }

    engine.set_context(context)

    category = RecommendationCategory(args.type) if args.type else None

    report = engine.generate_report(
        project=args.project,
        category=category,
        user_id=args.user if args.personalized else None
    )

    if args.output == "console":
        print(f"\n生成时间: {report.timestamp}")
        print(f"项目: {report.project}")
        print(f"改进潜力: {report.improvement_potential:.2%}")

        print(f"\n摘要:")
        print(f"  总推荐数: {report.summary['total_recommendations']}")
        print(f"  平均影响分数: {report.summary['average_impact_score']:.2f}")
        print(f"  平均置信度: {report.summary['average_confidence']:.2%}")

        print(f"\n类别分布:")
        for cat, count in report.summary['category_distribution'].items():
            print(f"  {cat}: {count}")

        print(f"\n推荐列表 (前10个):")
        for i, rec in enumerate(report.recommendations[:10], 1):
            priority_icon = {
                RecommendationPriority.CRITICAL: "🔴",
                RecommendationPriority.HIGH: "🟠",
                RecommendationPriority.MEDIUM: "🟡",
                RecommendationPriority.LOW: "🟢",
                RecommendationPriority.INFO: "🔵"
            }.get(rec.priority, "⚪")

            print(f"\n  {i}. {priority_icon} [{rec.category.value}] {rec.title}")
            print(f"     描述: {rec.description}")
            print(f"     影响: {rec.impact_score:.2f}, 置信度: {rec.confidence:.2%}")
            print(f"     工作量: {rec.effort_estimate}")
            print(f"     行动: {', '.join(rec.actions[:2])}")

        if report.effects:
            print(f"\n效果统计 (前5个):")
            for effect in report.effects[:5]:
                print(f"  {effect.recommendation_id}:")
                print(f"    接受率: {effect.acceptance_rate:.2%}")
                print(f"    用户满意度: {effect.user_satisfaction:.2%}")

    if args.output == "json" or args.output_file:
        output_data = report.to_dict()
        output_json = json.dumps(output_data, ensure_ascii=False, indent=2)

        if args.output_file:
            output_path = Path(args.output_file)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(output_json)
            print(f"\n报告已保存到: {output_path}")
        else:
            print("\nJSON 输出:")
            print(output_json)

    return 0


if __name__ == "__main__":
    sys.exit(main())
