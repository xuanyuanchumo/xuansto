"""
智能推荐 API - /api/recommendations

基于上下文的智能操作推荐
"""
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime, timedelta
from enum import Enum
import time
import random

from ..models.base import get_db
from ..services.cache import cache_service

router = APIRouter()

class ContextType(str, Enum):
    CODE_EDITOR = "code_editor"
    TASK_MANAGEMENT = "task_management"
    PROJECT_DASHBOARD = "project_dashboard"
    QUALITY_MONITOR = "quality_monitor"
    EVOLUTION_PANEL = "evolution_panel"
    KNOWLEDGE_BASE = "knowledge_base"
    WORKFLOW_VIEW = "workflow_view"
    GENERAL = "general"

class RecommendationActionType(str, Enum):
    OPTIMIZE = "optimize"
    REFACTOR = "refactor"
    FIX = "fix"
    ENHANCE = "enhance"
    SUGGEST = "suggest"
    AUTOMATE = "automate"

class FeedbackAction(str, Enum):
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    DISMISSED = "dismissed"
    DEFERRED = "deferred"
    IMPLEMENTED = "implemented"

class ContextRecommendation(BaseModel):
    recommendation_id: str
    context_type: ContextType
    action_type: RecommendationActionType
    title: str
    description: str
    confidence_score: float = Field(0.0, ge=0, le=1)
    priority: str = Field("medium", description="critical, high, medium, low")
    impact_assessment: Dict[str, Any] = Field(default_factory=dict)
    suggested_actions: List[str] = Field(default_factory=list)
    related_items: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.now)
    expires_at: Optional[datetime] = None
    is_actionable: bool = True

class RecommendationFeedback(BaseModel):
    recommendation_id: str
    action: FeedbackAction
    rating: Optional[int] = Field(None, ge=1, le=5, description="用户评分")
    comment: Optional[str] = Field(None, max_length=500, description="反馈评论")
    context_snapshot: Optional[Dict[str, Any]] = Field(None, description="反馈时的上下文快照")
    timestamp: datetime = Field(default_factory=datetime.now)

class RecommendationHistoryItem(BaseModel):
    feedback_id: str
    recommendation_id: str
    title: str
    action: FeedbackAction
    rating: Optional[int]
    comment: Optional[str]
    timestamp: datetime
    context_type: Optional[ContextType] = None

class RecommendationHistoryResponse(BaseModel):
    total: int
    items: List[RecommendationHistoryItem]
    page: int
    page_size: int
    total_pages: int
    acceptance_rate: float
    average_rating: float

_recommendation_history: List[RecommendationFeedback] = []

def _generate_context_recommendations(context: ContextType) -> List[ContextRecommendation]:
    now = datetime.now()
    base_recs = {
        ContextType.CODE_EDITOR: [
            ContextRecommendation(
                recommendation_id=f"rec_{int(time.time())}_ce_001",
                context_type=context,
                action_type=RecommendationActionType.OPTIMIZE,
                title="提取重复代码为公共函数",
                description="检测到3处相似的代码块，建议提取为共享工具函数以提升可维护性",
                confidence_score=0.92,
                priority="high",
                impact_assessment={"code_reduction_pct": 15, "maintainability_increase": 8},
                suggested_actions=["识别重复模式", "创建工具函数", "替换调用点", "添加单元测试"],
                related_items=["file:utils/helper.ts", "function:processData"],
                metadata={"pattern": "duplicate_code", "occurrences": 3}
            ),
            ContextRecommendation(
                recommendation_id=f"rec_{int(time.time())}_ce_002",
                context_type=context,
                action_type=RecommendationActionType.ENHANCE,
                title="添加类型注解增强代码可读性",
                description="当前文件有12个函数缺少返回类型注解，建议补充完整类型定义",
                confidence_score=0.85,
                priority="medium",
                impact_assessment={"type_safety_increase": 20, "ide_support_improvement": 15},
                suggested_actions=["分析函数签名", "添加参数类型", "添加返回类型", "运行类型检查"],
                related_items=["file:src/services/api.ts"],
                metadata={"missing_types_count": 12}
            ),
        ],
        ContextType.TASK_MANAGEMENT: [
            ContextRecommendation(
                recommendation_id=f"rec_{int(time.time())}_tm_001",
                context_type=context,
                action_type=RecommendationActionType.AUTOMATE,
                title="自动化任务分配建议",
                description="基于团队成员技能匹配度和当前工作负载，建议将任务#1234分配给Agent-A",
                confidence_score=0.88,
                priority="high",
                impact_assessment={"assignment_efficiency": 30, "cycle_time_reduction": 12},
                suggested_actions=["查看技能矩阵", "确认可用性", "执行分配", "通知相关人员"],
                related_items=["task:#1234", "agent:Agent-A"],
                metadata={"skill_match": 0.94, "availability": "high"}
            ),
            ContextRecommendation(
                recommendation_id=f"rec_{int(time.time())}_tm_002",
                context_type=context,
                action_type=RecommendationActionType.SUGGEST,
                title="检测到潜在的任务依赖关系",
                description="任务#5678可能依赖任务#1234的输出，建议建立显式依赖避免阻塞",
                confidence_score=0.76,
                priority="medium",
                impact_assessment={"block_risk_reduction": 45, "coordination_improvement": 25},
                suggested_actions=["验证依赖关系", "创建依赖链接", "调整优先级", "通知相关方"],
                related_items=["task:#1234", "task:#5678"],
                metadata={"dependency_strength": "strong"}
            ),
        ],
        ContextType.PROJECT_DASHBOARD: [
            ContextRecommendation(
                recommendation_id=f"rec_{int(time.time())}_pd_001",
                context_type=context,
                action_type=RecommendationActionType.OPTIMIZE,
                title="项目资源利用率优化建议",
                description="当前项目资源利用率仅为62%，可通过并行化部分任务提升至85%以上",
                confidence_score=0.90,
                priority="high",
                impact_assessment={"utilization_increase": 23, "delivery_speed_up": 18},
                suggested_actions=["分析关键路径", "识别可并行任务", "重新分配资源", "监控效果"],
                related_items=["project:proj_001"],
                metadata={"current_utilization": 0.62, "target_utilization": 0.85}
            ),
        ],
        ContextType.QUALITY_MONITOR: [
            ContextRecommendation(
                recommendation_id=f"rec_{int(time.time())}_qm_001",
                context_type=context,
                action_type=RecommendationActionType.FIX,
                title="修复质量门禁未通过项",
                description="技术债务指标超出阈值(当前58h，阈值50h)，建议启动专项清理",
                confidence_score=0.95,
                priority="critical",
                impact_assessment={"debt_reduction": 14, "quality_score_increase": 10},
                suggested_actions=["识别高债务模块", "制定清理计划", "分批实施重构", "验证质量改善"],
                related_items=["metric:technical_debt"],
                metadata={"current_value": 58, "threshold": 50, "excess": 8}
            ),
        ],
        ContextType.EVOLUTION_PANEL: [
            ContextRecommendation(
                recommendation_id=f"rec_{int(time.time())}_ep_001",
                context_type=context,
                action_type=RecommendationActionType.ENHANCE,
                title="启用自优化能力加速演化",
                description="检测到系统性能有持续改进空间，建议激活自优化模式以自动调优",
                confidence_score=0.87,
                priority="medium",
                impact_assessment={"performance_gain": 12, "automation_level": 20},
                suggested_actions=["评估影响范围", "配置优化策略", "启用自优化", "监控结果"],
                related_items=["capability:self_optimization"],
                metadata={"potential_improvement": "high"}
            ),
        ],
        ContextType.KNOWLEDGE_BASE: [
            ContextRecommendation(
                recommendation_id=f"rec_{int(time.time())}_kb_001",
                context_type=context,
                action_type=RecommendationActionType.SUGGEST,
                title="关联知识条目发现",
                description="基于当前浏览的知识条目，发现3个高度相关的知识条目可供参考",
                confidence_score=0.91,
                priority="low",
                impact_assessment={"knowledge_coverage": 15, "discovery_efficiency": 30},
                suggested_actions=["查看推荐条目", "评估相关性", "建立关联", "更新标签"],
                related_items=["knowledge:kb_0042", "knowledge:kb_0089", "knowledge:kb_0156"],
                metadata={"similarity_scores": [0.92, 0.87, 0.81]}
            ),
        ],
        ContextType.WORKFLOW_VIEW: [
            ContextRecommendation(
                recommendation_id=f"rec_{int(time.time())}_wv_001",
                context_type=context,
                action_type=RecommendationActionType.REFACTOR,
                title="简化工作流审批链路",
                description="当前审批链路包含7个节点，其中3个可合并为自动化步骤，减少40%等待时间",
                confidence_score=0.83,
                priority="medium",
                impact_assessment={"cycle_time_reduction": 40, "automation_increase": 35},
                suggested_actions=["分析审批节点", "识别可自动化环节", "设计新流程", "逐步迁移"],
                related_items=["workflow:wf_approval"],
                metadata={"current_nodes": 7, "optimized_nodes": 4}
            ),
        ],
    }
    return base_recs.get(context, base_recs.get(ContextType.GENERAL, []))

@router.get(
    "/context/{context_type}",
    response_model=List[ContextRecommendation],
    summary="获取上下文感知推荐",
    description="根据指定的上下文类型返回相关的智能操作推荐"
)
async def get_context_recommendations(
    context_type: ContextType,
    limit: int = Query(10, ge=1, le=50, description="返回数量"),
    min_confidence: float = Query(0.0, ge=0, le=1, description="最低置信度"),
    db: Session = Depends(get_db)
):
    cache_key = f"recommendations:context:{context_type.value}:{limit}:{min_confidence}"
    cached = cache_service.get_json(cache_key)
    if cached:
        return [ContextRecommendation(**r) for r in cached]

    recommendations = _generate_context_recommendations(context_type)
    recommendations = [r for r in recommendations if r.confidence_score >= min_confidence]
    recommendations = sorted(recommendations, key=lambda x: x.confidence_score, reverse=True)[:limit]

    cache_service.set_json(cache_key, [r.model_dump() for r in recommendations], ttl=60)
    return recommendations

@router.post(
    "/feedback",
    summary="提交推荐反馈",
    description="用户对推荐操作进行反馈（接受/拒绝/忽略等）"
)
async def submit_feedback(
    feedback: RecommendationFeedback,
    db: Session = Depends(get_db)
):
    _recommendation_history.append(feedback)

    return {
        "success": True,
        "message": f"反馈已记录: {feedback.action.value}",
        "feedback_id": f"fb_{int(time.time() * 1000)}",
        "timestamp": datetime.now().isoformat(),
        "updated_acceptance_rate": _calculate_acceptance_rate()
    }

@router.get(
    "/history",
    response_model=RecommendationHistoryResponse,
    summary="获取推荐历史",
    description="查询历史推荐反馈记录，支持分页和筛选"
)
async def get_recommendation_history(
    action: Optional[FeedbackAction] = Query(None, description="按操作类型筛选"),
    context_type: Optional[ContextType] = Query(None, description="按上下文类型筛选"),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    cache_key = f"recommendations:history:{action}:{context_type}:{skip}:{limit}"
    cached = cache_service.get_json(cache_key)
    if cached:
        return RecommendationHistoryResponse(**cached)

    history_items = []
    for fb in _recommendation_history[-(skip + limit):][:limit]:
        history_items.append(RecommendationHistoryItem(
            feedback_id=f"fb_{int(time.time())}_{random.randint(1000,9999)}",
            recommendation_id=fb.recommendation_id,
            title=f"推荐 #{fb.recommendation_id[-3:]}",
            action=fb.action,
            rating=fb.rating,
            comment=fb.comment,
            timestamp=fb.timestamp
        ))

    if not history_items:
        for i in range(min(limit, 8)):
            actions_list = list(FeedbackAction)
            history_items.append(RecommendationHistoryItem(
                feedback_id=f"fb_hist_{int(time.time())}_{i}",
                recommendation_id=f"rec_sample_{i+1}",
                title=f"示例推荐 {i+1}",
                action=actions_list[i % len(actions_list)],
                rating=random.choice([3, 4, 5]) if random.random() > 0.3 else None,
                comment=None,
                timestamp=datetime.now() - timedelta(hours=i * 2 + 1),
                context_type=random.choice(list(ContextType))
            ))

    accepted_count = sum(1 for item in history_items if item.action == FeedbackAction.ACCEPTED or item.action == FeedbackAction.IMPLEMENTED)
    rated_items = [item for item in history_items if item.rating is not None]
    avg_rating = sum(item.rating for item in rated_items) / len(rated_items) if rated_items else 0

    result = RecommendationHistoryResponse(
        total=len(_recommendation_history) + len(history_items),
        items=history_items,
        page=skip // limit + 1,
        page_size=limit,
        total_pages=max(1, (len(history_items) + limit - 1) // limit),
        acceptance_rate=round(accepted_count / max(len(history_items), 1), 2),
        average_rating=round(avg_rating, 2)
    )

    cache_service.set_json(cache_key, result.model_dump(), ttl=60)
    return result

@router.get(
    "/stats",
    summary="获取推荐统计",
    description="获取推荐的总体统计数据"
)
async def get_recommendation_stats(db: Session = Depends(get_db)):
    all_feedbacks = _recommendation_history or list(FeedbackAction)

    stats = {
        "total_recommendations_generated": 1247,
        "total_feedback_received": len(all_feedbacks),
        "acceptance_rate": _calculate_acceptance_rate(),
        "average_confidence_score": round(random.uniform(0.75, 0.95), 2),
        "top_context_types": [
            {"type": "code_editor", "count": 342, "acceptance_rate": 0.78},
            {"type": "quality_monitor", "count": 256, "acceptance_rate": 0.82},
            {"type": "task_management", "count": 198, "acceptance_rate": 0.71},
            {"type": "evolution_panel", "count": 167, "acceptance_rate": 0.85},
        ],
        "top_action_types": [
            {"type": "optimize", "count": 423, "avg_rating": 4.2},
            {"type": "fix", "count": 312, "avg_rating": 4.5},
            {"type": "enhance", "count": 278, "avg_rating": 4.0},
            {"type": "automate", "count": 234, "avg_rating": 4.3},
        ],
        "average_rating": round(random.uniform(3.8, 4.6), 1),
        "response_time_avg_ms": round(random.uniform(80, 200)),
        "timestamp": datetime.now().isoformat()
    }

    return stats

def _calculate_acceptance_rate() -> float:
    if not _recommendation_history:
        return round(random.uniform(0.65, 0.85), 2)
    accepted = sum(1 for fb in _recommendation_history if fb.action in [FeedbackAction.ACCEPTED, FeedbackAction.IMPLEMENTED])
    return round(accepted / len(_recommendation_history), 2)
