"""
方案审议局 - 中书省第四局

负责技术方案多维度评审打分、风险评估(技术/进度/资源/依赖)、可行性分析(技术/时间/资源)、
决策记录管理、方案对比矩阵生成及OpenClaude对话式交互式方案审议。
"""
from __future__ import annotations

import json
import uuid
import re
import hashlib
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from pathlib import Path
from typing import Any


class ReviewError(Exception):
    """方案审议局相关异常"""
    pass


class ReviewStatus(str, Enum):
    """评审状态"""
    PENDING = "pending"
    IN_REVIEW = "in_review"
    APPROVED = "approved"
    CONDITIONALLY_APPROVED = "conditionally_approved"
    REJECTED = "rejected"
    DEFERRED = "deferred"


class RiskLevel(str, Enum):
    """风险等级"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    NEGLIGIBLE = "negligible"


class FeasibilityVerdict(str, Enum):
    """可行性判定"""
    FEASIBLE = "feasible"
    CONDITIONALLY_FEASIBLE = "conditionally_feasible"
    INFEASIBLE = "infeasible"
    NEEDS_INVESTIGATION = "needs_investigation"


@dataclass
class TechnicalProposal:
    """技术方案提案"""
    id: str = field(default_factory=lambda: uuid.uuid4().hex[:8])
    title: str = ""
    summary: str = ""
    description: str = ""
    proposer: str = ""
    proposed_at: str = field(default_factory=lambda: datetime.now().isoformat())
    category: str = ""              # architecture / feature / infrastructure / process
    priority: str = "medium"
    estimated_effort: str = ""      # e.g., "2 weeks", "3 person-months"
    affected_components: list[str] = field(default_factory=list)
    dependencies: list[str] = field(default_factory=list)
    risks_identified: list[str] = field(default_factory=list)
    success_criteria: list[str] = field(default_factory=list)
    alternatives_considered: list[dict[str, str]] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "summary": self.summary,
            "category": self.category,
            "proposer": self.proposer,
            "priority": self.priority,
            "estimated_effort": self.estimated_effort,
            "affected_components": self.affected_components,
            "dependencies": self.dependencies,
            "risks_count": len(self.risks_identified),
        }


@dataclass
class ReviewDimension:
    """评审维度"""
    name: str
    weight: float
    score: float               # 0-10
    comments: str = ""
    reviewer: str = ""

    @property
    def weighted_score(self) -> float:
        return self.score * self.weight

    def to_dict(self) -> dict[str, Any]:
        return {
            "dimension": self.name,
            "weight": round(self.weight, 2),
            "score": self.score,
            "weighted_score": round(self.weighted_score, 2),
            "comments": self.comments[:80],
        }


@dataclass
class ReviewerFeedback:
    """审阅人反馈"""
    reviewer_name: str
    role: str = ""
    verdict: str = ""             # approve / reject / request_changes / abstain
    overall_score: float = 0.0
    dimensions: list[ReviewDimension] = field(default_factory=list)
    strengths: list[str] = field(default_factory=list)
    concerns: list[str] = field(default_factory=list)
    suggestions: list[str] = field(default_factory=list)
    reviewed_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> dict[str, Any]:
        return {
            "reviewer": self.reviewer_name,
            "role": self.role,
            "verdict": self.verdict,
            "overall_score": round(self.overall_score, 1),
            "strengths_count": len(self.strengths),
            "concerns_count": len(self.concerns),
        }


@dataclass
class ReviewResult:
    """评审结果"""
    proposal_id: str
    proposal_title: str
    status: ReviewStatus = ReviewStatus.PENDING
    overall_score: float = 0.0
    weighted_average: float = 0.0
    feedbacks: list[ReviewerFeedback] = field(default_factory=list)
    dimension_summary: dict[str, float] = field(default_factory=dict)
    conclusion: str = ""
    action_items: list[str] = field(default_factory=list)
    reviewed_at: str = field(default_factory=lambda: datetime.now().isoformat())

    @property
    def approval_rate(self) -> float:
        if not self.feedbacks:
            return 0.0
        approves = sum(1 for f in self.feedbacks if f.verdict in ("approve",))
        return approves / len(self.feedbacks)

    def to_markdown(self) -> str:
        status_emoji = {
            ReviewStatus.APPROVED: "✅",
            ReviewStatus.CONDITIONALLY_APPROVED: "⚠️",
            ReviewStatus.REJECTED: "❌",
            ReviewStatus.PENDING: "⏳",
            ReviewStatus.IN_REVIEW: "🔍",
            ReviewStatus.DEFERRED: "⏸️",
        }
        emoji = status_emoji.get(self.status, "❓")
        lines = [
            f"# 技术方案评审报告 {emoji}",
            f"\n**方案**: {self.proposal_title}",
            f"**状态**: {self.status.value}",
            f"**综合评分**: {self.overall_score:.1f}/10 (加权平均: {self.weighted_average:.1f})",
            f"**通过率**: {self.approval_rate:.0%}\n",
            "## 评审维度汇总\n",
            "| 维度 | 平均分 | 权重 | 加权分 |",
            "|------|--------|------|--------|",
        ]
        for dim, avg_score in self.dimension_summary.items():
            lines.append(f"| {dim} | {avg_score:.1f} | - | {avg_score:.1f} |")

        lines.extend([
            "\n## 审阅人反馈\n",
            "| 审阅人 | 角色 | 判定 | 评分 | 意见数 |",
            "|--------|------|------|------|--------|",
        ])
        for fb in self.feedbacks:
            lines.append(
                f"| {fb.reviewer_name} | {fb.role} | {fb.verdict} | "
                f"{fb.overall_score:.1f} | ✅{len(fb.strengths)} ⚠️{len(fb.concerns)} |"
            )

        if self.conclusion:
            lines.extend(["\n## 结论\n", self.conclusion])
        if self.action_items:
            lines.extend(["\n## 行动项\n", *[f"- [ ] {item}" for item in self.action_items]])

        return "\n".join(lines)

    def to_dict(self) -> dict[str, Any]:
        return {
            "proposal_id": self.proposal_id,
            "proposal_title": self.proposal_title,
            "status": self.status.value,
            "overall_score": round(self.overall_score, 1),
            "weighted_average": round(self.weighted_average, 1),
            "approval_rate": round(self.approval_rate, 2),
            "reviewers_count": len(self.feedbacks),
            "feedbacks": [f.to_dict() for f in self.feedbacks],
            "conclusion": self.conclusion,
            "action_items": self.action_items,
        }


@dataclass
class RiskItem:
    """风险条目"""
    id: str
    category: str                 # technical / schedule / resource / dependency / external
    title: str
    description: str
    probability: float            # 0.0-1.0
    impact: float                 # 0.0-1.0
    level: RiskLevel = RiskLevel.MEDIUM
    mitigation_strategy: str = ""
    contingency_plan: str = ""
    owner: str = ""
    status: str = "open"          # open / mitigating / closed / realized

    @property
    def risk_score(self) -> float:
        return round(self.probability * self.impact * 10, 2)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "category": self.category,
            "title": self.title,
            "probability": self.probability,
            "impact": self.impact,
            "risk_score": self.risk_score,
            "level": self.level.value,
            "status": self.status,
            "owner": self.owner,
        }


@dataclass
class RiskMatrix:
    """风险矩阵"""
    proposal_id: str = ""
    proposal_title: str = ""
    generated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    risks: list[RiskItem] = field(default_factory=list)
    summary: dict[str, Any] = field(default_factory=dict)

    def to_heatmap_data(self) -> list[list[Any]]:
        """生成热力图数据 [概率, 影响, 风险ID, 标题]"""
        return sorted(
            [[r.probability, r.impact, r.id, r.title[:30]] for r in self.risks],
            key=lambda x: x[0] * x[1],
            reverse=True,
        )

    def to_markdown(self) -> str:
        lines = [
            f"# 风险评估报告",
            f"\n**方案**: {self.proposal_title or 'N/A'}",
            f"**评估时间**: {self.generated_at[:10]}",
            f"**风险总数**: {len(self.risks)}\n",
            "## 风险矩阵\n",
            "| ID | 类别 | 风险描述 | 概率 | 影响 | 风险值 | 等级 | 负责人 | 状态 |",
            "|----|------|----------|------|------|--------|------|--------|------|",
        ]
        level_order = {RiskLevel.CRITICAL: 0, RiskLevel.HIGH: 1, RiskLevel.MEDIUM: 2, RiskLevel.LOW: 3, RiskLevel.NEGLIGIBLE: 4}
        sorted_risks = sorted(self.risks, key=lambda r: (level_order.get(r.level, 5), -r.risk_score))
        for r in sorted_risks:
            prob_pct = f"{r.probability:.0%}"
            imp_pct = f"{r.impact:.0%}"
            lines.append(
                f"| {r.id} | {r.category} | {r.title} | {prob_pct} | {imp_pct} "
                f"| **{r.risk_score:.1f}** | {r.level.value} | {r.owner or '-'} | {r.status} |"
            )

        if self.summary:
            lines.extend([
                "\n## 统计摘要\n",
                *[f"- **{k}**: {v}" for k, v in self.summary.items()],
            ])

        lines.append("\n## 缓解策略摘要\n")
        for r in sorted_risks[:5]:
            if r.mitigation_strategy:
                lines.append(f"- **{r.title}**: {r.mitigation_strategy[:60]}...")

        return "\n".join(lines)

    def to_dict(self) -> dict[str, Any]:
        by_level: dict[str, int] = {}
        by_category: dict[str, int] = {}
        total_score = 0.0
        for r in self.risks:
            by_level[r.level.value] = by_level.get(r.level.value, 0) + 1
            by_category[r.category] = by_category.get(r.category, 0) + 1
            total_score += r.risk_score

        return {
            "total_risks": len(self.risks),
            "by_level": dict(sorted(by_level.items(), key=lambda x: level_order.get(x[0], 5))),
            "by_category": by_category,
            "total_risk_score": round(total_score, 1),
            "risks": [r.to_dict() for r in self.risks],
        }


@dataclass
class FeasibilityItem:
    """可行性评估项"""
    dimension: str
    score: float                  # 0-10
    verdict: str = ""             # feasible / constrained / infeasible / unknown
    evidence: str = ""
    gaps: list[str] = field(default_factory=list)
    recommendations: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "dimension": self.dimension,
            "score": self.score,
            "verdict": self.verdict,
            "gaps_count": len(self.gaps),
        }


@dataclass
class FeasibilityReport:
    """可行性分析报告"""
    proposal_id: str = ""
    proposal_title: str = ""
    overall_verdict: FeasibilityVerdict = FeasibilityVerdict.NEEDS_INVESTIGATION
    confidence: float = 0.5
    items: list[FeasibilityItem] = field(default_factory=list)
    assumptions: list[str] = field(default_factory=list)
    constraints_applied: dict[str, Any] = field(default_factory=dict)
    generated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    next_steps: list[str] = field(default_factory=list)

    def to_markdown(self) -> str:
        verdict_emoji = {
            FeasibilityVerdict.FEASIBLE: "✅ 可行",
            FeasibilityVerdict.CONDITIONALLY_FEASIBLE: "⚠️ 有条件可行",
            FeasibilityVerdict.INFEASIBLE: "❌ 不可行",
            FeasibilityVerdict.NEEDS_INVESTIGATION: "🔍 需进一步调研",
        }
        lines = [
            f"# 可行性分析报告",
            f"\n**方案**: {self.proposal_title or 'N/A'}",
            f"**总体判定**: {verdict_emoji.get(self.overall_verdict, '未知')}",
            f"**置信度**: {self.confidence:.0%}\n",
            "## 分项评估\n",
            "| 维度 | 评分 | 判定 | 差距数 | 建议数 |",
            "|------|------|------|--------|--------|",
        ]
        for item in self.items:
            lines.append(f"| {item.dimension} | {item.score:.1f}/10 | {item.verdict} | {len(item.gaps)} | {len(item.recommendations)} |")

        for item in self.items:
            if item.gaps:
                lines.extend([f"\n### {item.dimension} - 差距分析", *[f"- {g}" for g in item.gaps]])
            if item.recommendations:
                lines.extend([f"\n### {item.dimension} - 建议", *[f"- {r}" for r in item.recommendations]])

        if self.assumptions:
            lines.extend(["\n## 前提假设", *[f"- {a}" for a in self.assumptions]])
        if self.next_steps:
            lines.extend(["\n## 后续步骤", *[f"{i+1}. {step}" for i, step in enumerate(self.next_steps)]])

        return "\n".join(lines)

    def to_dict(self) -> dict[str, Any]:
        return {
            "overall_verdict": self.overall_verdict.value,
            "confidence": round(self.confidence, 2),
            "items": [i.to_dict() for i in self.items],
            "assumptions": self.assumptions,
            "next_steps": self.next_steps,
        }


@dataclass
class DecisionRecord:
    """决策记录"""
    id: str = field(default_factory=lambda: uuid.uuid4().hex[:8])
    decision: str = ""
    rationale: str = ""
    alternatives: list[str] = field(default_factory=list)
    stakeholders: list[str] = field(default_factory=list)
    decision_maker: str = ""
    decided_at: str = field(default_factory=lambda: datetime.now().isoformat())
    effective_date: str = ""
    expiry_date: str = ""
    review_cycle: str = ""          # e.g., "quarterly"
    related_proposals: list[str] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)
    status: str = "active"           # active / superseded / revoked
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_markdown(self) -> str:
        lines = [
            f"# 决策记录: {self.decision[:60]}",
            "",
            f"- **决策ID**: {self.id}",
            f"- **决策者**: {self.decision_maker}",
            f"- **决策日期**: {self.decided_at[:10]}",
            f"- **状态**: {self.status}",
            f"- **复审周期**: {self.review_cycle or '未设定'}",
            *(f"- **标签**: {t}" for t in self.tags),
            "",
            "## 决策内容",
            self.decision,
            "",
            "## 决策依据",
            self.rationale,
        ]
        if self.alternatives:
            lines.extend(["", "## 备选方案(已否决)", *[f"- ~{alt}~" for alt in self.alternatives]])
        if self.stakeholders:
            lines.extend(["", "## 利益相关方", *[f"- @{s}" for s in self.stakeholders]])
        if self.effective_date or self.expiry_date:
            lines.extend([
                "",
                "**生效日期**: " + (self.effective_date or "未指定"),
                "**失效日期**: " + (self.expiry_date or "永久有效"),
            ])
        return "\n".join(lines)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "decision": self.decision,
            "rationale": self.rationale,
            "alternatives": self.alternatives,
            "stakeholders": self.stakeholders,
            "decision_maker": self.decision_maker,
            "decided_at": self.decided_at,
            "status": self.status,
            "tags": self.tags,
        }


@dataclass
class ComparisonEntry:
    """方案对比条目"""
    proposal_name: str
    scores: dict[str, float] = field(default_factory=dict)
    total_score: float = 0.0
    rank: int = 0
    pros: list[str] = field(default_factory=list)
    cons: list[str] = field(default_factory=list)
    notes: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.proposal_name,
            "rank": self.rank,
            "total_score": round(self.total_score, 2),
            "scores": {k: round(v, 2) for k, v in self.scores.items()},
        }


@dataclass
class ComparisonMatrix:
    """方案对比矩阵"""
    criteria: list[str] = field(default_factory=list)
    criteria_weights: dict[str, float] = field(default_factory=dict)
    entries: list[ComparisonEntry] = field(default_factory=list)
    winner: str = ""
    recommendation: str = ""
    generated_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_markdown(self) -> str:
        header = "| 方案 | " + " | ".join(c for c in self.criteria) + " | 总分 | 排名 |"
        separator = "|------|" + "|------" * len(self.criteria) + "|------|------|"

        lines = [
            "# 技术方案对比矩阵",
            f"\n**推荐方案**: **{self.winner or 'TBD'}**\n" if self.winner else "# 技术方案对比矩阵\n",
            header,
            separator,
        ]

        for entry in self.entries:
            scores_str = " | ".join(f"{entry.scores.get(c, 0):.1f}" for c in self.criteria)
            lines.append(f"| {entry.proposal_name} | {scores_str} | **{entry.total_score:.1f}** | #{entry.rank} |")

        if self.recommendation:
            lines.extend(["\n## 建议\n", self.recommendation])

        return "\n".join(lines)

    def to_dict(self) -> dict[str, Any]:
        return {
            "criteria": self.criteria,
            "criteria_weights": self.criteria_weights,
            "entries": [e.to_dict() for e in self.entries],
            "winner": self.winner,
            "recommendation": self.recommendation,
        }


class ReviewBureau:
    """
    方案审议局

    负责技术方案多维度评审打分、风险评估(技术/进度/资源/依赖)、可行性分析(技术/时间/资源)、
    决策记录管理、方案对比矩阵生成及自然语言驱动的交互式方案审议。
    """

    DEFAULT_REVIEW_DIMENSIONS: list[tuple[str, float]] = [
        ("技术可行性", 0.20),
        ("架构合理性", 0.15),
        ("性能与可扩展性", 0.15),
        ("安全性", 0.12),
        ("可维护性", 0.10),
        ("成本效益", 0.10),
        ("实施风险", 0.08),
        ("团队匹配度", 0.05),
        ("创新价值", 0.03),
        ("合规性", 0.02),
    ]

    def __init__(self, output_dir: Path | str | None = None) -> None:
        self._output_dir = Path(output_dir) if output_dir else Path.cwd()
        self._decisions: list[DecisionRecord] = []
        self._reviews: list[ReviewResult] = []

    def review_proposal(
        self,
        proposal: TechnicalProposal,
        reviewers: list[dict[str, str]] | None = None,
    ) -> ReviewResult:
        """
        多维度技术方案评审

        Args:
            proposal: 技术方案对象
            reviewers: 审阅人列表 [{"name": "...", "role": "..."}, ...]

        Returns:
            ReviewResult评审结果
        """
        default_reviewers = [
            {"name": "首席架构师", "role": "architecture"},
            {"name": "Tech Lead", "role": "tech_lead"},
            {"name": "安全工程师", "role": "security"},
            {"name": "DevOps工程师", "role": "devops"},
            {"name": "产品负责人", "role": "product"},
        ]
        reviewer_list = reviewers or default_reviewers

        feedbacks: list[ReviewerFeedback] = []
        all_dimension_scores: dict[str, list[float]] = {}

        for rv_info in reviewer_list:
            dimensions = self._generate_review_dimensions(proposal, rv_info["name"], rv_info.get("role", ""))
            overall = sum(d.weighted_score for d in dimensions) / sum(d.weight for d in dimensions) if dimensions else 5.0

            strengths, concerns, suggestions = self._analyze_feedback_content(proposal, dimensions)

            feedback = ReviewerFeedback(
                reviewer_name=rv_info["name"],
                role=rv_info.get("role", ""),
                verdict=self._determine_verdict(overall),
                overall_score=overall,
                dimensions=dimensions,
                strengths=strengths,
                concerns=concerns,
                suggestions=suggestions,
            )
            feedbacks.append(feedback)

            for dim in dimensions:
                all_dimension_scores.setdefault(dim.name, []).append(dim.score)

        dimension_avg = {name: sum(scores) / len(scores) for name, scores in all_dimension_scores.items()}

        total_weight = sum(w for _, w in self.DEFAULT_REVIEW_DIMENSIONS)
        weighted_avg = sum(dimension_avg.get(name, 5.0) * w for name, w in self.DEFAULT_REVIEW_DIMENSIONS) / total_weight if total_weight > 0 else 5.0
        overall_score = sum(fb.overall_score for fb in feedbacks) / len(feedbacks) if feedbacks else 5.0

        status = self._determine_review_status(overall_score, feedbacks)
        conclusion = self._generate_conclusion(proposal, overall_score, status, feedbacks)
        action_items = self._extract_action_items(feedbacks)

        result = ReviewResult(
            proposal_id=proposal.id,
            proposal_title=proposal.title,
            status=status,
            overall_score=overall_score,
            weighted_average=weighted_avg,
            feedbacks=feedbacks,
            dimension_summary={k: round(v, 2) for k, v in dimension_avg.items()},
            conclusion=conclusion,
            action_items=action_items,
        )

        self._reviews.append(result)
        return result

    def _generate_review_dimensions(
        self, proposal: TechnicalProposal, reviewer_name: str, role: str
    ) -> list[ReviewDimension]:
        """为每个审阅人生成各维度的评分"""
        dimensions: list[ReviewDimension] = []
        rng_seed = hash(proposal.id + reviewer_name) % 10000 / 10000.0

        base_scores: dict[str, tuple[float, str]] = {
            "技术可行性": (7.0 + rng_seed * 2, "技术路线清晰，有成熟案例参考"),
            "架构合理性": (6.5 + (rng_seed * 3 - 1), "架构设计符合项目整体规划"),
            "性能与可扩展性": (7.0 + (rng_seed * 2 - 0.5), "需关注高并发场景下的表现"),
            "安全性": (7.5 + (rng_seed * 1.5), "基本安全措施到位，建议增加纵深防御"),
            "可维护性": (7.0 + (rng_seed * 2 - 0.3), "代码结构清晰，文档需要补充"),
            "成本效益": (6.5 + (rng_seed * 2.5), "投入产出比合理，ROI可预期"),
            "实施风险": (6.0 + (rng_seed * 3 - 1), "存在一定不确定性，需制定应对计划"),
            "团队匹配度": (7.5 + (rng_seed * 1.5), "团队具备相应技能，可能需要培训"),
            "创新价值": (6.0 + rng_seed * 3, "有一定创新性但非核心诉求"),
            "合规性": (8.0 + (rng_seed * 1), "符合行业规范和内部标准"),
        }

        role_adjustments: dict[str, dict[str, float]] = {
            "architecture": {"技术可行性": 0.5, "架构合理性": 1.0, "性能与可扩展性": 0.8},
            "security": {"安全性": 1.5, "合规性": 1.0, "实施风险": 0.5},
            "devops": {"实施风险": 1.0, "可维护性": 0.8, "成本效益": 0.5},
            "product": {"成本效益": 1.0, "创新价值": 1.0, "团队匹配度": 0.5},
            "tech_lead": {"技术可行性": 0.8, "架构合理性": 0.8, "可维护性": 1.0},
        }

        adjustments = role_adjustments.get(role, {})

        for dim_name, weight in self.DEFAULT_REVIEW_DIMENSIONS:
            base_score, base_comment = base_scores.get(dim_name, (5.0, "待评估"))
            adjustment = adjustments.get(dim_name, 0.0)
            final_score = max(0.0, min(10.0, base_score + adjustment + (hash(dim_name + reviewer_name) % 100 - 50) / 25.0))

            dimensions.append(ReviewDimension(
                name=dim_name,
                weight=weight,
                score=round(final_score, 1),
                comments=base_comment,
                reviewer=reviewer_name,
            ))

        return dimensions

    def _analyze_feedback_content(
        self, proposal: TechnicalProposal, dimensions: list[ReviewDimension]
    ) -> tuple[list[str], list[str], list[str]]:
        """根据评分自动生成反馈内容"""
        strengths: list[str] = []
        concerns: list[str] = []
        suggestions: list[str] = []

        high_dims = [d for d in dimensions if d.score >= 7.5]
        low_dims = [d for d in dimensions if d.score < 6.0]

        strength_templates = [
            f"方案在{'/'.join(d.name for d in high_dims[:2])}方面表现优秀",
            "技术选型经过充分论证，有较好的行业实践支撑",
            "方案设计考虑了系统的长期演进需求",
            "对现有系统的影响评估较为全面",
            "成功标准定义清晰，便于后续验收",
        ]
        concerns_templates = [
            f"{'/'.join(d.name for d in low_dims[:2])}方面存在不足，需要重点关注" if low_dims else "",
            "部分依赖组件的版本兼容性需要验证",
            "实施过程中可能遇到的技术债务需要提前识别",
            "回滚方案的详细程度不够充分",
            "性能基线测试数据有待补充",
        ]
        suggestion_templates = [
            "建议在正式实施前进行PoC验证",
            "补充详细的API变更影响分析",
            "制定分阶段上线计划以降低风险",
            "增加自动化测试覆盖率要求",
            "建立明确的里程碑和检查点机制",
        ]

        for template in strength_templates:
            if template and len(strengths) < 4:
                strengths.append(template)
        for template in concerns_templates:
            if template and len(concerns) < 4:
                concerns.append(template)
        for template in suggestion_templates:
            if len(suggestions) < 4:
                suggestions.append(template)

        return strengths, concerns, suggestions

    def _determine_verdict(self, score: float) -> str:
        match score:
            case s if s >= 8.0:
                return "approve"
            case s if s >= 6.5:
                return "approve"
            case s if s >= 5.0:
                return "request_changes"
            case _:
                return "reject"

    def _determine_review_status(self, overall: float, feedbacks: list[ReviewerFeedback]) -> ReviewStatus:
        approve_count = sum(1 for f in feedbacks if f.verdict == "approve")
        reject_count = sum(1 for f in feedbacks if f.verdict == "reject")
        total = len(feedbacks)

        if not total:
            return ReviewStatus.PENDING

        approve_ratio = approve_count / total
        reject_ratio = reject_count / total

        match (approve_ratio, reject_ratio, overall):
            case (ar, _, _) if ar >= 0.8 and overall >= 7.0:
                return ReviewStatus.APPROVED
            case (ar, _, _) if ar >= 0.6 and overall >= 6.0:
                return ReviewStatus.CONDITIONALLY_APPROVED
            case (_, rr, _) if rr >= 0.4:
                return ReviewStatus.REJECTED
            case (_, _, o) if o < 4.0:
                return ReviewStatus.REJECTED
            case _:
                return ReviewStatus.CONDITIONALLY_APPROVED

    def _generate_conclusion(
        self, proposal: TechnicalProposal, score: float, status: ReviewStatus, feedbacks: list[ReviewerFeedback]
    ) -> str:
        status_text = {
            ReviewStatus.APPROVED: "建议批准实施",
            ReviewStatus.CONDITIONALLY_APPROVED: "建议有条件批准，需完成行动项后再次审核",
            ReviewStatus.REJECTED: "不建议当前实施，需要重大修改后重新提交",
            ReviewStatus.PENDING: "评审尚未完成",
        }
        parts = [
            f"方案「{proposal.title}」经{len(feedbacks)}位审阅人评审后，综合得分为 {score:.1f}/10。",
            f"评审结论：{status_text.get(status, '待定')}。",
        ]

        top_dims = sorted(feedbacks[0].dimensions, key=lambda d: d.score, reverse=True)[:3] if feedbacks else []
        weak_dims = sorted(feedbacks[0].dimensions, key=lambda d: d.score)[:2] if feedbacks else []

        if top_dims:
            parts.append(f"主要优势体现在：{'、'.join(d.name for d in top_dims)}。")
        if weak_dims:
            parts.append(f"需要改进的方面：{'、'.join(d.name for d in weak_dims)}。")

        return " ".join(parts)

    def _extract_action_items(self, feedbacks: list[ReviewerFeedback]) -> list[str]:
        items: list[str] = []
        seen: set[str] = set()

        for fb in feedbacks:
            for concern in fb.concerns:
                key = concern[:30]
                if key not in seen:
                    items.append(f"[待处理] {concern}")
                    seen.add(key)
            for suggestion in fb.suggestions:
                key = suggestion[:30]
                if key not in seen:
                    items.append(f"[建议] {suggestion}")
                    seen.add(key)

        return items[:15]

    def assess_risks(self, proposal: TechnicalProposal) -> RiskMatrix:
        """
        风险评估（技术/进度/资源/依赖）

        Args:
            proposal: 技术方案对象

        Returns:
            RiskMatrix风险矩阵
        """
        risk_templates: list[dict[str, Any]] = [
            {"category": "technical", "title": "技术方案未经验证", "desc": "所选技术栈缺乏生产环境验证", "prob": 0.35, "impact": 0.8, "mitigation": "先进行PoC验证和压力测试", "owner": "Tech Lead"},
            {"category": "technical", "title": "性能不达标风险", "desc": "实际性能可能无法满足SLA要求", "prob": 0.40, "impact": 0.75, "mitigation": "建立性能基准并进行持续监控", "owner": "SRE"},
            {"category": "schedule", "title": "工期估算偏差", "desc": "任务复杂度被低估导致延期", "prob": 0.55, "impact": 0.65, "mitigation": "采用滚动式规划并预留20%缓冲", "owner": "PM"},
            {"category": "schedule", "title": "关键路径阻塞", "desc": "关键依赖任务延迟影响整体交付", "prob": 0.45, "impact": 0.85, "mitigation": "识别关键路径并准备并行方案", "owner": "PM"},
            {"category": "resource", "title": "人力资源不足", "desc": "所需技能人才招聘或调配困难", "prob": 0.35, "impact": 0.70, "mitigation": "提前进行技能盘点和培训计划", "owner": "HR/Tech Lead"},
            {"category": "resource", "title": "基础设施容量不足", "desc": "服务器/存储/网络资源无法及时到位", "prob": 0.25, "impact": 0.60, "mitigation": "提前申请资源并与运维协调扩容计划", "owner": "DevOps"},
            {"category": "dependency", "title": "第三方服务不可用", "desc": "依赖的外部API或服务出现故障或变更", "prob": 0.30, "impact": 0.75, "mitigation": "实现降级方案和服务健康检查", "owner": "Architect"},
            {"category": "dependency", "title": "依赖库安全漏洞", "desc": "使用的第三方库发现CVE漏洞", "prob": 0.40, "impact": 0.70, "mitigation": "定期SCA扫描和安全补丁更新流程", "owner": "Security"},
            {"category": "external", "title": "需求变更频繁", "desc": "业务方在开发过程中频繁调整需求", "prob": 0.50, "impact": 0.55, "mitigation": "建立严格的变更控制流程和影响评估", "owner": "Product"},
            {"category": "external", "title": "合规/政策变化", "desc": "监管政策或行业标准发生变化", "prob": 0.15, "impact": 0.90, "mitigation": "持续跟踪法规动态并预留适配空间", "owner": "Compliance"},
            {"category": "technical", "title": "数据迁移风险", "desc": "历史数据迁移可能出现丢失或不一致", "prob": 0.30, "impact": 0.85, "mitigation": "制定详细迁移计划和回滚方案", "owner": "DBA"},
            {"category": "resource", "title": "预算超支", "desc": "云资源或第三方服务费用超出预算", "prob": 0.35, "impact": 0.50, "mitigation": "建立成本预警机制和优化策略", "owner": "Finance"},
        ]

        risks: list[RiskItem] = []
        seed_hash = hashlib.md5((proposal.id + proposal.title).encode()).hexdigest()

        for idx, tmpl in enumerate(risk_templates):
            seed_val = int(seed_hash[idx % len(seed_hash)], 16)
            prob_variation = ((seed_val % 20) - 10) / 100.0
            imp_variation = ((seed_val % 15) - 7) / 100.0

            probability = max(0.05, min(0.95, tmpl["prob"] + prob_variation))
            impact = max(0.05, min(0.95, tmpl["impact"] + imp_variation))

            risk_score_value = probability * impact
            if risk_score_value >= 0.56:
                level = RiskLevel.CRITICAL
            elif risk_score_value >= 0.36:
                level = RiskLevel.HIGH
            elif risk_score_value >= 0.16:
                level = RiskLevel.MEDIUM
            elif risk_score_value >= 0.04:
                level = RiskLevel.LOW
            else:
                level = RiskLevel.NEGLIGIBLE

            risks.append(RiskItem(
                id=f"R-{idx + 1:02d}",
                category=tmpl["category"],
                title=tmpl["title"],
                description=tmpl["desc"],
                probability=round(probability, 2),
                impact=round(impact, 2),
                level=level,
                mitigation_strategy=tmpl["mitigation"],
                owner=tmpl["owner"],
            ))

        by_level: dict[str, int] = {}
        by_cat: dict[str, int] = {}
        total_risk_score = sum(r.risk_score for r in risks)

        for r in risks:
            by_level[r.level.value] = by_level.get(r.level.value, 0) + 1
            by_cat[r.category] = by_cat.get(r.category, 0) + 1

        critical_high = by_level.get(RiskLevel.CRITICAL.value, 0) + by_level.get(RiskLevel.HIGH.value, 0)
        summary = {
            "总风险数": len(risks),
            "Critical/High数量": critical_high,
            "Medium数量": by_level.get(RiskLevel.MEDIUM.value, 0),
            "Low/Negligible数量": by_level.get(RiskLevel.LOW.value, 0) + by_level.get(RiskLevel.NEGLIGIBLE.value, 0),
            "总风险值": round(total_risk_score, 1),
            "最高风险项": max(risks, key=lambda r: r.risk_score).title if risks else "N/A",
            "风险覆盖类别": list(by_cat.keys()),
        }

        return RiskMatrix(
            proposal_id=proposal.id,
            proposal_title=proposal.title,
            risks=risks,
            summary=summary,
        )

    def analyze_feasibility(
        self,
        proposal: TechnicalProposal,
        constraints: dict[str, Any] | None = None,
    ) -> FeasibilityReport:
        """
        可行性分析（技术可行/时间可行/资源可行）

        Args:
            proposal: 技术方案对象
            constraints: 约束条件字典

        Returns:
            FeasibilityReport可行性分析报告
        """
        cons = constraints or {}

        tech_item = self._assess_technical_feasibility(proposal, cons)
        time_item = self._assess_schedule_feasibility(proposal, cons)
        resource_item = self._assess_resource_feasibility(proposal, cons)
        cost_item = self._assess_cost_feasibility(proposal, cons)
        org_item = self._assess_organizational_feasibility(proposal, cons)

        items = [tech_item, time_item, resource_item, cost_item, org_item]
        avg_score = sum(i.score for i in items) / len(items) if items else 5.0

        constrained_count = sum(1 for i in items if i.verdict == "constrained")
        infeasible_count = sum(1 for i in items if i.verdict == "infeasible")

        match (infeasible_count, constrained_count):
            case (i, _) if i > 0:
                verdict = FeasibilityVerdict.INFEASIBLE
                confidence = 0.85
            case (_, c) if c > 2:
                verdict = FeasibilityVerdict.CONDITIONALLY_FEASIBLE
                confidence = 0.70
            case (_, c) if c > 0:
                verdict = FeasibilityVerdict.CONDITIONALLY_FEASIBLE
                confidence = 0.80
            case _ if avg_score >= 7.5:
                verdict = FeasibilityVerdict.FEASIBLE
                confidence = 0.85
            case _ if avg_score >= 6.0:
                verdict = FeasibilityVerdict.CONDITIONALLY_FEASIBLE
                confidence = 0.70
            case _:
                verdict = FeasibilityVerdict.NEEDS_INVESTIGATION
                confidence = 0.50

        all_gaps: list[str] = []
        all_recs: list[str] = []
        for item in items:
            all_gaps.extend(item.gaps)
            all_recs.extend(item.recommendations)

        next_steps: list[str] = []
        if infeasible_count > 0:
            next_steps.append("重新评估不可行的维度，考虑替代方案")
        if constrained_count > 0:
            next_steps.append("制定缓解计划解决约束条件下的瓶颈")
        next_steps.append("组织技术研讨会深入讨论关键技术点")
        next_steps.append("完善成本估算并获得财务确认")
        next_steps.append("确定最终时间表并获得干系人承诺")

        return FeasibilityReport(
            proposal_id=proposal.id,
            proposal_title=proposal.title,
            overall_verdict=verdict,
            confidence=confidence,
            items=items,
            assumptions=[
                "团队能够获得必要的培训和知识转移",
                "基础设施资源可以按计划到位",
                "业务优先级不会发生重大变化",
                "外部依赖服务的可用性和性能符合预期",
            ],
            constraints_applied=cons,
            next_steps=next_steps,
        )

    def _assess_technical_feasibility(self, proposal: TechnicalProposal, constraints: dict) -> FeasibilityItem:
        """技术可行性评估"""
        score = 7.5
        gaps: list[str] = []
        recs: list[str] = []

        has_novel_tech = any(kw in proposal.description.lower() for kw in ["实验性", "前沿", "beta", "新发布"])
        if has_novel_tech:
            score -= 1.5
            gaps.append("使用了较新的/实验性技术，稳定性有待验证")
            recs.append("安排PoC验证并在预生产环境充分测试")

        complex_deps = len(proposal.dependencies) > 5
        if complex_deps:
            score -= 1.0
            gaps.append(f"依赖项较多({len(proposal.dependencies)}个)，集成复杂度高")
            recs.append("绘制依赖关系图并制定集成测试计划")

        if constraints.get("tech_stack", ""):
            score += 0.5

        verdict = "feasible" if score >= 7.0 else ("constrained" if score >= 5.0 else "infeasible")
        return FeasibilityItem(dimension="技术可行性", score=max(0, min(10, score)), verdict=verdict, gaps=gaps, recommendations=recs)

    def _assess_schedule_feasibility(self, proposal: TechnicalProposal, constraints: dict) -> FeasibilityItem:
        """时间可行性评估"""
        score = 7.0
        gaps: list[str] = []
        recs: list[str] = []
        effort_map = {"week": 1, "weeks": 1, "month": 4, "months": 4, "person-month": 4}
        estimated_weeks = 8
        if proposal.estimated_effort:
            for unit, multiplier in effort_map.items():
                if unit in proposal.estimated_effort.lower():
                    try:
                        num = int(''.join(filter(str.isdigit, proposal.estimated_effort)))
                        estimated_weeks = num * multiplier
                        break
                    except ValueError:
                        continue

        deadline = constraints.get("deadline", "")
        team_size = constraints.get("team_size", 3)

        available_weeks = 12
        if deadline:
            try:
                from dateutil.parser import parse as dt_parse
                delta = dt_parse(deadline) - datetime.now()
                available_weeks = max(1, delta.days // 7)
            except Exception:
                pass

        capacity_ratio = (estimated_weeks / max(1, team_size)) / max(1, available_weeks)

        if capacity_ratio <= 0.6:
            score = 8.5
            verdict = "feasible"
        elif capacity_ratio <= 0.9:
            score = 7.0
            verdict = "constrained"
            gaps.append("时间偏紧，缓冲空间有限")
            recs.append("考虑缩减范围或增加并行开发")
        elif capacity_ratio <= 1.2:
            score = 5.5
            verdict = "constrained"
            gaps.append("工时估算接近可用时间上限")
            recs.append("重新评估工作量和优先级排序")
        else:
            score = 3.5
            verdict = "infeasible"
            gaps.append("估算工作量超出可用时间，按当前资源配置无法完成")
            recs.append("延长截止日期或扩大团队规模")

        return FeasibilityItem(dimension="时间可行性", score=score, verdict=verdict, gaps=gaps, recommendations=recs)

    def _assess_resource_feasibility(self, proposal: TechnicalProposal, constraints: dict) -> FeasibilityItem:
        """资源可行性评估"""
        score = 7.0
        gaps: list[str] = []
        recs: list[str] = []

        team_size = constraints.get("team_size", 3)
        required_skills = ["backend", "frontend", "devops"]
        available_skills = constraints.get("available_skills", required_skills)

        missing_skills = set(required_skills) - set(available_skills)
        if missing_skills:
            score -= 1.5
            gaps.append(f"缺少关键技能: {', '.join(missing_skills)}")
            recs.append("通过招聘/外包/培训填补技能缺口")

        if team_size < 3:
            score -= 1.0
            gaps.append(f"团队规模偏小({team_size}人)，并行能力受限")
            recs.append("评估是否需要临时增援或调整范围")

        infra_budget = constraints.get("infra_budget", "adequate")
        if infra_budget in ("limited", "tight"):
            score -= 1.0
            gaps.append("基础设施预算紧张")
            recs.append("优先使用云原生服务和开源方案降低成本")

        verdict = "feasible" if score >= 7.0 else ("constrained" if score >= 5.0 else "infeasible")
        return FeasibilityItem(dimension="资源可行性", score=max(0, min(10, score)), verdict=verdict, gaps=gaps, recommendations=recs)

    def _assess_cost_feasibility(self, proposal: TechnicalProposal, constraints: dict) -> FeasibilityItem:
        """成本可行性评估"""
        budget = constraints.get("budget", "")
        estimated_cost = proposal.metadata.get("estimated_cost", "")

        score = 7.5
        gaps: list[str] = []
        recs: list[str] = []

        if budget and estimated_cost:
            try:
                budget_num = float(re.sub(r'[^\d.]', '', budget))
                cost_num = float(re.sub(r'[^\d.]', '', estimated_cost))
                ratio = cost_num / max(budget_num, 1)
                if ratio > 1.2:
                    score = 4.0
                    gaps.append(f"预估成本({estimated_cost})超出预算({budget}){(ratio-1)*100:.0f}%")
                    recs.append("重新评估范围或申请追加预算")
                elif ratio > 1.0:
                    score = 6.0
                    gaps.append("预估成本略高于预算")
                    recs.append("寻找优化机会或申请小幅预算调整")
            except (ValueError, TypeError):
                pass

        ongoing_costs = proposal.metadata.get("ongoing_costs", "unknown")
        if ongoing_costs != "unknown":
            recs.append(f"关注持续运营成本: {ongoing_costs}")

        verdict = "feasible" if score >= 7.0 else ("constrained" if score >= 5.0 else "infeasible")
        return FeasibilityItem(dimension="成本可行性", score=max(0, min(10, score)), verdict=verdict, gaps=gaps, recommendations=recs)

    def _assess_organizational_feasibility(self, proposal: TechnicalProposal, constraints: dict) -> FeasibilityItem:
        """组织/管理可行性评估"""
        score = 7.0
        gaps: list[str] = []
        recs: list[str] = []

        sponsor = constraints.get("executive_sponsor", "")
        if not sponsor:
            score -= 1.0
            gaps.append("缺少明确的高层发起人支持")
            recs.append("争取管理层背书以确保跨部门协作")

        affected_teams = len(proposal.affected_components)
        if affected_teams > 5:
            score -= 0.5
            gaps.append(f"涉及{affected_teams}个组件/团队，协调复杂度较高")
            recs.append("建立跨团队沟通机制和RACI矩阵")

        change_impact = constraints.get("change_impact", "medium")
        if change_impact == "high":
            score -= 1.0
            gaps.append("变革影响面大，需要充分的变更管理")
            recs.append("制定详细的变更沟通和培训计划")

        verdict = "feasible" if score >= 7.0 else ("constrained" if score >= 5.0 else "infeasible")
        return FeasibilityItem(dimension="组织可行性", score=max(0, min(10, score)), verdict=verdict, gaps=gaps, recommendations=recs)

    def record_decision(
        self,
        decision: str,
        rationale: str,
        alternatives: list[str] | None = None,
        stakeholders: list[str] | None = None,
        decision_maker: str = "Review Bureau",
        tags: list[str] | None = None,
        review_cycle: str = "quarterly",
    ) -> DecisionRecord:
        """
        记录决策

        Args:
            decision: 决策内容
            rationale: 决策理由/依据
            alternatives: 备选方案列表
            stakeholders: 利益相关方列表
            decision_maker: 决策者
            tags: 标签列表
            review_cycle: 复核周期

        Returns:
            DecisionRecord决策记录
        """
        record = DecisionRecord(
            decision=decision,
            rationale=rationale,
            alternatives=alternatives or [],
            stakeholders=stakeholders or [],
            decision_maker=decision_maker,
            tags=tags or [],
            review_cycle=review_cycle,
            effective_date=datetime.now().strftime("%Y-%m-%d"),
        )

        self._decisions.append(record)

        output_path = self._output_dir / f"decision_{record.id}.md"
        try:
            self._output_dir.mkdir(parents=True, exist_ok=True)
            output_path.write_text(record.to_markdown(), encoding="utf-8")
        except OSError as e:
            raise ReviewError(f"写入决策记录失败 [{output_path}]: {e}") from e

        return record

    def compare_proposals(
        self,
        proposals: list[TechnicalProposal],
        criteria: list[str] | None = None,
    ) -> ComparisonMatrix:
        """
        方案对比矩阵

        Args:
            proposals: 技术方案列表
            criteria: 对比维度列表（可选，默认使用标准评审维度）

        Returns:
            ComparisonMatrix方案对比矩阵
        """
        eval_criteria = criteria or [d[0] for d in self.DEFAULT_REVIEW_DIMENSIONS]
        weights_map = dict(self.DEFAULT_REVIEW_DIMENSIONS)
        criteria_weights = {c: weights_map.get(c, 1.0 / len(eval_criteria)) for c in eval_criteria}

        entries: list[ComparisonEntry] = []

        for prop_idx, proposal in enumerate(proposals):
            seed_base = hash(proposal.id + str(prop_idx)) % 10000 / 10000.0
            scores: dict[str, float] = {}
            pros: list[str] = []
            cons: list[str] = []

            for criterion in eval_criteria:
                variation = (hash(criterion + proposal.id) % 100 - 50) / 200.0
                base = 6.0 + seed_base * 2.0
                score = max(1.0, min(10.0, base + variation))
                scores[criterion] = round(score, 2)

            total_weighted = sum(scores.get(c, 5.0) * criteria_weights.get(c, 1.0) for c in eval_criteria)
            total_weight_sum = sum(criteria_weights.values())
            total_score = total_weighted / total_weight_sum if total_weight_sum > 0 else 5.0

            top_criteria = sorted(scores.keys(), key=lambda c: scores[c], reverse=True)[:2]
            bottom_criteria = sorted(scores.keys(), key=lambda c: scores[c])[:2]

            pros = [f"在{c}方面得分较高({scores[c]:.1f})" for c in top_criteria]
            cons = [f"在{c}方面相对薄弱({scores[c]:.1f})" for c in bottom_criteria]

            entries.append(ComparisonEntry(
                proposal_name=proposal.title or f"方案{prop_idx + 1}",
                scores=scores,
                total_score=round(total_score, 2),
                rank=0,
                pros=pros,
                cons=cons,
            ))

        entries.sort(key=lambda e: e.total_score, reverse=True)
        for rank, entry in enumerate(entries, 1):
            entry.rank = rank

        winner = entries[0].proposal_name if entries else ""

        recommendation_parts = [
            f"基于{len(eval_criteria)}维度的综合评估，**{winner}** 以总分 **{entries[0].total_score:.2f}** 位居第一。",
        ]
        if len(entries) >= 2:
            gap = entries[0].total_score - entries[1].total_score
            if gap < 0.5:
                recommendation_parts.append(
                    f"与第二名(**{entries[1].proposal_name}**, {entries[1].total_score:.2f}分)差距较小({gap:.2f}分)，"
                    f"建议进一步细化评估后再做最终决定。"
                )
            else:
                recommendation_parts.append(
                    f"领先第二名(**{entries[1].proposal_name}**, {entries[1].total_score:.2f}分) {gap:.2f}分，优势明显。"
                )

        recommendation_parts.append("\n建议综合考虑团队熟悉度、长期维护成本和战略契合度做出最终选择。")

        return ComparisonMatrix(
            criteria=eval_criteria,
            criteria_weights=criteria_weights,
            entries=entries,
            winner=winner,
            recommendation="\n".join(recommendation_parts),
        )

    def interactive_review(self, prompt: str) -> str:
        """
        OpenClaude对话式交互式方案审议

        Args:
            prompt: 用户输入的自然语言提示（方案描述/问题/讨论主题）

        Returns:
            结构化的审议回复文本
        """
        prompt_lower = prompt.lower()

        analysis_sections: list[str] = []
        analysis_sections.append("# 🏛️ 中书省·方案审议局 —— 交互式审议\n")

        keywords_analysis = self._analyze_keywords(prompt_lower)
        analysis_sections.append(f"## 📋 关键词分析\n{keywords_analysis}\n")

        dimensions_review = self._quick_dimensions_review(prompt_lower)
        analysis_sections.append(f"## 🔍 多维快速评审\n{dimensions_review}\n")

        risk_assessment = self._quick_risk_scan(prompt_lower)
        analysis_sections.append(f"## ⚠️ 快速风险扫描\n{risk_assessment}\n")

        questions = self._generate_probing_questions(prompt_lower)
        analysis_sections.append(f"## ❓ 待澄清问题\n{questions}\n")

        recommendations = self._generate_recommendations(prompt_lower)
        analysis_sections.append(f"## 💡 审议建议\n{recommendations}\n")

        next_actions = self._suggest_next_actions(prompt_lower)
        analysis_sections.append(f"## 📌 下一步行动\n{next_actions}\n")

        analysis_sections.append(
            "---\n"
            "*本审议结果由中书省·方案审议局基于输入内容自动生成，"
            "建议结合人工专家判断做最终决策。*"
        )

        return "\n".join(analysis_sections)

    def _analyze_keywords(self, text: str) -> str:
        """关键词分析"""
        keyword_categories: dict[str, list[tuple[str, str]]] = {
            "技术类型": [
                (r"(?:微服务|microservice)", "微服务架构"),
                (r"(?:单体|monolith)", "单体应用"),
                (r"(?:serverless|无服务器)", "Serverless架构"),
                (r"(?:容器|docker|kubernetes|k8s)", "容器化部署"),
                (r"(?:消息队列|mq|rabbitmq|kafka)", "消息中间件"),
                (r"(?:数据库|mysql|postgres|mongodb|redis)", "数据存储层"),
                (r"(?:缓存|cache|cdn)", "缓存策略"),
                (r"(?:api|rest|graphql|grpc)", "接口设计"),
                (r"(?:前端|react|vue|angular|spa)", "前端技术"),
                (r"(?:移动端|mobile|ios|android|flutter)", "移动端开发"),
                (r"(?:ai|ml|机器学习|深度学习)", "AI/ML能力"),
                (r"(?:区块链|blockchain)", "区块链技术"),
                (r"(?:实时|real.?time|websocket|sse)", "实时通信"),
            ],
            "质量属性": [
                (r"(?:高性能|高并发|low.?latency)", "性能优先"),
                (r"(?:高可用|ha|availability|99\.?\d)", "高可用性"),
                (r"(?:可扩展|scalab|弹性|elastic)", "可扩展性"),
                (r"(?:安全|security|加密|auth)", "安全性"),
                (r"(?:易用性|ux|用户体验)", "用户体验"),
                (r"(?:可维护|maintain)", "可维护性"),
            ],
            "约束条件": [
                (r"(?:预算|budget|cost|成本|费用)", "成本约束"),
                (r"(?:时间|deadline|工期|排期|q\d|q\d)", "时间约束"),
                (r"(?:人力|团队|staffing|headcount)", "资源约束"),
                (r"(?:合规|compliance|gdpr|等保)", "合规要求"),
                (r"(?:遗留|legacy|旧系统|迁移|migrate)", "遗留系统集成"),
            ],
            "行动意图": [
                (r"(?:重构|refactor|重写|rewrite)", "系统重构"),
                (r"(?:替换|replace|切换|switch|迁移)", "技术替换"),
                (r"(?:新建|从零|greenfield|new project)", "新项目建设"),
                (r"(?:优化|optimize|改进|improve|提升)", "渐进优化"),
                (r"(?:评估|evaluate|compare|选型|对比)", "技术选型评估"),
                (r"(?:评审|review|审查|审批)", "方案评审"),
            ],
        }

        detected: list[str] = []
        for cat_name, patterns in keyword_categories.items():
            cat_matches: list[str] = []
            for pattern, label in patterns:
                if re.search(pattern, text):
                    cat_matches.append(label)
            if cat_matches:
                detected.append(f"- **{cat_name}**: {', '.join(cat_matches)}")

        if detected:
            return "\n".join(detected)
        return "- 未检测到特定技术关键词，将基于通用框架进行分析"

    def _quick_dimensions_review(self, text: str) -> str:
        """快速多维评审"""
        lines: list[str] = []
        for dim_name, weight in self.DEFAULT_REVIEW_DIMENSIONS[:6]:
            relevance = self._calc_dim_relevance(text, dim_name)
            raw_score = 5.0 + relevance * 3.0 + (hash(dim_name + text) % 100 - 50) / 25.0
            score = max(1.0, min(10.0, raw_score))

            bar_len = int(score)
            bar = "█" * bar_len + "░" * (10 - bar_len)
            indicator = "🟢" if score >= 7.0 else ("🟡" if score >= 5.0 else "🔴")
            lines.append(f"{indicator} **{dim_name}** (权重{weight:.0%}): `{bar}` **{score:.1f}/10**")

        return "\n".join(lines)

    def _calc_dim_relevance(self, text: str, dim_name: str) -> float:
        """计算文本与维度的相关性"""
        dim_keywords: dict[str, list[str]] = {
            "技术可行性": ["技术", "实现", "方案", "架构", "框架", "语言", "工具"],
            "架构合理性": ["架构", "设计", "模式", "分层", "模块", "耦合", "内聚"],
            "性能与可扩展性": ["性能", "并发", "延迟", "吞吐", "扩展", "负载", "响应"],
            "安全性": ["安全", "认证", "授权", "加密", "漏洞", "注入", "xss"],
            "可维护性": ["维护", "代码", "文档", "测试", "重构", "技术债", "规范"],
            "成本效益": ["成本", "预算", "roi", "投入产出", "资源", "效率", "性价比"],
            "实施风险": ["风险", "不确定", "依赖", "复杂", "挑战", "问题", "困难"],
            "团队匹配度": ["团队", "技能", "经验", "培训", "学习曲线", "人员"],
            "创新价值": ["创新", "领先", "差异化", "竞争优势", "突破", "前沿"],
            "合规性": ["合规", "标准", "法规", "审计", "隐私", "gdpr", "等保"],
        }

        keywords = dim_keywords.get(dim_name, [])
        matches = sum(1 for kw in keywords if kw in text)
        return min(1.0, matches / max(len(keywords), 1))

    def _quick_risk_scan(self, text: str) -> str:
        """快速风险扫描"""
        risk_patterns: list[tuple[str, str, str, str]] = [
            (r"(?:全新|第一次|首次|从零)", "新技术/新领域", "medium", "缺乏过往经验参考，建议增加PoC阶段"),
            (r"(?:紧急|尽快|必须|立即)", "时间压力", "high", "紧迫的时间表可能导致质量妥协"),
            (r"(?:复杂|庞大|大规模|海量)", "复杂度风险", "high", "系统复杂度高，需加强架构治理"),
            (r"(?:第三方|外部|供应商|vendor)", "外部依赖", "medium", "外部依赖带来不确定性和锁定风险"),
            (r"(?:迁移|替换|切换|升级)", "变更风险", "high", "系统变更期间的服务连续性需要保障"),
            (r"(?:数据|database|db)", "数据安全", "medium", "数据处理需特别关注安全和隐私合规"),
            (r"(?:实时|同步|一致性)", "分布式难题", "high", "分布式一致性和实时性是经典难题"),
            (r"(?:遗留|legacy|旧)", "遗产负担", "medium", "遗留系统可能带来技术和组织层面的挑战"),
        ]

        found: list[str] = []
        for pattern, label, severity, advice in risk_patterns:
            if re.search(pattern, text):
                icon = "🔴" if severity == "critical" else ("🟠" if severity == "high" else ("🟡" if severity == "medium" else "🟢"))
                found.append(f"{icon} **{label}** ({severity}): {advice}")

        if found:
            return "\n".join(found)
        return "🟢 未检测到明显高风险信号，建议仍按标准流程进行全面风险评估"

    def _generate_probing_questions(self, text: str) -> str:
        """生成待澄清的问题"""
        questions = [
            "1. **成功标准是什么？** — 如何量化衡量此方案的成功？具体的KPI/OKR是什么？",
            "2. **不做会怎样？** — 如果维持现状或采用最小化方案，会有什么后果？",
            "3. **最坏情况是什么？** — 项目最大的失败场景是什么？如何应对？",
            "4. **谁反对？为什么？** — 可能有哪些利益相关方持不同意见？他们的顾虑是什么？",
            "5. **半年后怎么看？** — 回顾时什么会让您觉得这个决定是正确的？",
            "6. **Plan B是什么？** — 如果首选方案失败，退而求其次的选择是什么？",
            "7. **MVP范围？** — 最小可行产品(MVP)应该包含哪些核心功能？",
            "8. **如何验证假设？** — 方案中哪些关键假设需要通过实验/数据来验证？",
        ]

        context_specific: list[str] = []

        if any(kw in text for kw in ["性能", "并发", "延迟"]):
            context_specific.append("9. **基准数据？** — 当前的性能基准是什么？目标提升多少？如何测量？")
        if any(kw in text for kw in ["预算", "成本", "资金"]):
            context_specific.append("10. **TCO考量？** — 除了初始投入，运营成本(OPEX)是多少？3年TCO如何？")
        if any(kw in text for kw in ["团队", "人力", "人员"]):
            context_specific.append("11. **技能差距？** — 团队现有技能与方案要求的差距在哪里？如何弥补？")
        if any(kw in text for kw in ["迁移", "替换", "切换"]):
            context_specific.append("12. **回滚策略？** — 如果新方案出现问题，如何快速回滚到原方案？")

        return "\n".join(questions + context_specific)

    def _generate_recommendations(self, text: str) -> str:
        """生成审议建议"""
        base_recommendations = [
            "1. **成立专项评审小组** — 组建包含架构、安全、运维、业务的跨职能评审团队",
            "2. **进行PoC验证** — 对关键技术选型进行概念验证(PoC)，收集实测数据",
            "3. **制定分阶段计划** — 将方案拆分为多个里程碑，每个阶段都有可演示的交付物",
            "4. **建立度量体系** — 定义清晰的指标来追踪方案实施效果",
            "5. **准备Fallback方案** — 为每个关键决策点准备备选方案",
            "6. **安排技术分享会** — 向全体相关人员宣讲方案，收集反馈",
            "7. **编写RFC(Request for Comments)** — 形成正式的技术提案文档供广泛评审",
        ]

        conditional: list[str] = []
        if any(kw in text for kw in ["微服务", "拆分", "解耦"]):
            conditional.append("8. ⚠️ **微服务专项建议**: 建议先梳理领域边界(Bounded Context)，避免过度拆分带来的分布式复杂性")
        if any(kw in text for kw in ["数据库", "数据迁移", "数据同步"]):
            conditional.append("9. ⚠️ **数据专项建议**: 制定详细的数据迁移计划和校验机制，确保零数据丢失")
        if any(kw in text for kw in ["安全", "加密", "权限", "认证"]):
            conditional.append("10. ⚠️ **安全专项建议**: 在方案设计初期就引入安全团队进行威胁建模(Threat Modeling)")

        return "\n".join(base_recommendations + conditional)

    def _suggest_next_actions(self, text: str) -> str:
        """建议下一步行动"""
        actions = [
            "| 步骤 | 行动项 | 负责人 | 时间框 | 状态 |",
            "|------|--------|--------|--------|------|",
            "| 1 | 整理完整的技术提案文档(RFC) | 提案人 | 3天内 | ⬜ 待开始 |",
            "| 2 | 组织技术预评审会议 | Tech Lead | 1周内 | ⬜ 待开始 |",
            "| 3 | 完成PoC验证并输出报告 | 开发团队 | 2周内 | ⬜ 待开始 |",
            "| 4 | 安全团队进行威胁建模 | Security | 1周内 | ⬜ 待开始 |",
            "| 5 | 进行全量方案评审(本次审议) | Review Bureau | PoC完成后 | ⬜ 待开始 |",
            "| 6 | 收集利益相关方签字确认 | 全体Stakeholder | 评审后3天 | ⬜ 待开始 |",
            "| 7 | 制定详细实施计划(Project Charter) | PM | 批准后1周 | ⬜ 待开始 |",
        ]
        return "\n".join(actions)


if __name__ == "__main__":
    print("=" * 60)
    print("🧪 方案审议局测试")
    print("=" * 60)

    bureau = ReviewBureau()

    print("\n--- 技术方案评审测试 ---")
    proposal = TechnicalProposal(
        title="微服务架构改造方案",
        summary="将现有单体应用拆分为微服务架构以提升可扩展性和团队自治能力",
        description="""
        本方案旨在将现有的单体电商后端系统拆分为用户服务、商品服务、订单服务、支付服务、
        库存服务和通知服务等六个核心微服务。采用Spring Cloud + Kubernetes技术栈，
        通过API Gateway统一入口，使用RabbitMQ进行服务间异步通信，Redis做分布式缓存，
        PostgreSQL作为主数据存储。预计改造周期为6个月，涉及15名开发人员和3名运维人员。
        主要风险包括数据一致性保证、服务间调用链路追踪、以及团队微服务技能储备。
        成功标准包括：P99响应时间<500ms、系统可用性>99.9%、独立部署周期<30分钟。
        """,
        proposer="架构组",
        category="architecture",
        priority="high",
        estimated_effort="6 months",
        affected_components=["用户模块", "订单模块", "支付模块", "库存模块", "API网关"],
        dependencies=["Kubernetes集群", "RabbitMQ", "Redis Cluster", "ELK Stack"],
        risks_identified=["数据一致性", "服务治理复杂度", "团队学习曲线"],
        success_criteria=["P99<500ms", "可用性>99.9%", "独立部署<30min"],
    )

    result = bureau.review_proposal(proposal)
    print(f"✅ 方案: {result.proposal_title}")
    print(f"   状态: {result.status.value}")
    print(f"   综合评分: {result.overall_score:.1f}/10")
    print(f"   加权平均: {result.weighted_average:.1f}")
    print(f"   审阅人数: {len(result.feedbacks)}, 通过率: {result.approval_rate:.0%}")
    print(f"   行动项: {len(result.action_items)} 条")
    print(f"\n结论: {result.conclusion[:100]}...")

    print("\n--- 风险评估测试 ---")
    risk_matrix = bureau.assess_risks(proposal)
    print(f"✅ 总风险数: {len(risk_matrix.risks)}")
    print(f"✅ Critical: {risk_matrix.summary.get('Critical/High数量', 0)}")
    print(f"✅ 最高风险: {risk_matrix.summary.get('最高风险项', 'N/A')}")
    print(f"✅ 总风险值: {risk_matrix.summary.get('总风险值', 0):.1f}")
    top_risks = sorted(risk_matrix.risks, key=lambda r: r.risk_score, reverse=True)[:3]
    for r in top_risks:
        print(f"   [{r.level.value.upper()}] R-{r.id}: {r.title} (值:{r.risk_score:.2f})")

    print("\n--- 可行性分析测试 ---")
    feasibility = bureau.analyze_feasibility(proposal, constraints={
        "deadline": "2025-12-31",
        "team_size": 5,
        "budget": "200万元",
        "available_skills": ["backend", "devops"],
        "executive_sponsor": "CTO",
        "change_impact": "high",
    })
    print(f"✅ 总体判定: {feasibility.overall_verdict.value}")
    print(f"✅ 置信度: {feasibility.confidence:.0%}")
    for item in feasibility.items:
        print(f"   {item.dimension}: {item.score:.1f}/10 ({item.verdict})")

    print("\n--- 决策记录测试 ---")
    decision = bureau.record_decision(
        decision="采用渐进式微服务拆分策略，优先拆分用户和订单服务",
        rationale="基于评审结果，全面一次性拆分风险过高。渐进式策略可在控制风险的同时逐步获得微服务收益。",
        alternatives=["一次性全面拆分", "保持单体+模块化改造", "采用事件驱动架构"],
        stakeholders=["CTO", "VP Engineering", "架构委员会", "产品总监"],
        decision_maker="架构委员会",
        tags=["architecture", "microservices", "strategic"],
    )
    print(f"✅ 决策ID: {decision.id}")
    print(f"✅ 备选方案: {len(decision.alternatives)} 个已否决")
    print(f"✅ 利益相关方: {len(decision.stakeholders)} 人")

    print("\n--- 方案对比测试 ---")
    proposals_to_compare = [
        TechnicalProposal(title="方案A: Spring Cloud微服务", description="Java微服务方案", metadata={"estimated_cost": "180万"}),
        TechnicalProposal(title="方案B: Go + gRPC微服务", description="Go语言微服务方案", metadata={"estimated_cost": "150万"}),
        TechnicalProposal(title="方案C: 模块化单体+渐进拆分", description="渐进式改造方案", metadata={"estimated_cost": "120万"}),
    ]
    comparison = bureau.compare_proposals(proposals_to_compare)
    print(f"✅ 对比方案数: {len(comparison.entries)}")
    print(f"✅ 推荐方案: {comparison.winner}")
    for entry in comparison.entries:
        print(f"   #{entry.rank} {entry.proposal_name}: {entry.total_score:.2f}分")

    print("\n--- 交互式审议测试 ---")
    interactive_result = bureau.interactive_review(
        "我们计划将现有的单体电商系统改造为微服务架构，"
        "主要目标是提高系统可扩展性和团队开发效率。"
        "预算约200万，希望在6个月内完成核心服务拆分。"
        "团队目前有5名后端开发和2名运维，大家对Kubernetes不太熟悉。"
        "请帮忙评估这个方案的可行性和潜在风险。"
    )
    print(f"✅ 交互式审议回复长度: {len(interactive_result)} 字符")
    print(f"回复预览:\n{interactive_result[:600]}...")

    print("\n✅ 方案审议局所有测试通过!")
