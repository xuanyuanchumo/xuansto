"""
演化洞察 API - /api/evolution/insights

提供趋势预测、改进建议、演化状态查询能力
"""
from fastapi import APIRouter, Depends, Query, BackgroundTasks, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any, AsyncGenerator
from pydantic import BaseModel, Field
from datetime import datetime, timedelta
from enum import Enum
import json
import asyncio
import time
import random

from ..models.base import get_db
from ..services.cache import cache_service, CacheKeys

router = APIRouter()

class InsightMetricType(str, Enum):
    PERFORMANCE = "performance"
    EFFICIENCY = "efficiency"
    SUCCESS_RATE = "success_rate"
    RESPONSE_TIME = "response_time"
    RESOURCE_USAGE = "resource_usage"
    ERROR_RATE = "error_rate"
    COVERAGE = "coverage"
    TECHNICAL_DEBT = "technical_debt"

class TrendDirection(str, Enum):
    UPWARD = "upward"
    DOWNWARD = "downward"
    STABLE = "stable"
    VOLATILE = "volatile"

class EvolutionPhase(str, Enum):
    IDLE = "idle"
    ANALYZING = "analyzing"
    PLANNING = "planning"
    EXECUTING = "executing"
    VALIDATING = "validating"
    DEPLOYING = "deploying"

class RecommendationPriority(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

class TrendDataPoint(BaseModel):
    timestamp: datetime
    value: float
    predicted: bool = Field(False, description="是否为预测值")
    confidence: Optional[float] = Field(None, description="预测置信度")

class TrendPrediction(BaseModel):
    metric_type: InsightMetricType
    period: str
    direction: TrendDirection
    change_percentage: float
    current_value: float
    predicted_value: Optional[float] = None
    confidence_score: float = Field(0.0, ge=0, le=1)
    data_points: List[TrendDataPoint] = Field(default_factory=list)
    prediction_horizon: str = Field("7d", description="预测时间范围")

class ImprovementRecommendation(BaseModel):
    recommendation_id: str
    title: str
    description: str
    priority: RecommendationPriority
    category: str
    impact_area: List[str]
    estimated_improvement: Dict[str, float]
    effort_level: str = Field(..., description="effort level: low, medium, high")
    risk_level: str = Field(..., description="risk level: low, medium, high")
    status: str = Field("pending", description="pending, accepted, rejected, implemented")
    created_at: datetime = Field(default_factory=datetime.now)
    implemented_at: Optional[datetime] = None

class EvolutionStatusInsight(BaseModel):
    current_phase: EvolutionPhase
    progress_percentage: float = Field(0.0, ge=0, le=100)
    active_cycle_id: Optional[str] = None
    last_cycle_result: Optional[Dict[str, Any]] = None
    next_scheduled_cycle: Optional[datetime] = None
    total_cycles_completed: int = 0
    success_rate: float = Field(0.0, ge=0, le=1)
    average_cycle_duration_seconds: float = 0.0
    capabilities_status: Dict[str, Dict[str, Any]] = Field(default_factory=dict)
    system_health_score: float = Field(0.0, ge=0, le=100)

class EvolutionTriggerRequest(BaseModel):
    evolution_type: str = Field("auto", description="演化类型: auto, skill_optimization, workflow_adaptation, performance_tuning")
    force: bool = Field(False, description="是否强制执行")
    dry_run: bool = Field(False, description="模拟运行")
    parameters: Optional[Dict[str, Any]] = Field(default_factory=dict)

class EvolutionTriggerResponse(BaseModel):
    trigger_id: str
    status: str
    message: str
    estimated_duration: Optional[int] = None
    cycle_id: Optional[str] = None

_insights_cache_ttl = {
    "trends": 120,
    "recommendations": 300,
    "status": 30,
}

def _generate_mock_trend_data(metric: InsightMetricType, period: str) -> TrendPrediction:
    now = datetime.now()
    points_count = {"24h": 24, "7d": 7 * 24, "30d": 30}.get(period, 24)
    interval = timedelta(hours=1) if period == "24h" else timedelta(hours=1) if period == "7d" else timedelta(days=1)

    base_values = {
        InsightMetricType.PERFORMANCE: (75.0, 95.0),
        InsightMetricType.EFFICIENCY: (60.0, 85.0),
        InsightMetricType.SUCCESS_RATE: (90.0, 99.5),
        InsightMetricType.RESPONSE_TIME: (0.5, 3.0),
        InsightMetricType.RESOURCE_USAGE: (40.0, 80.0),
        InsightMetricType.ERROR_RATE: (0.1, 5.0),
        InsightMetricType.COVERAGE: (70.0, 95.0),
        InsightMetricType.TECHNICAL_DEBT: (10.0, 60.0),
    }
    base_min, base_max = base_values.get(metric, (50.0, 90.0))

    data_points = []
    current_val = base_min + (base_max - base_min) * random.random()
    for i in range(points_count):
        timestamp = now - interval * (points_count - i - 1)
        change = (random.random() - 0.48) * (base_max - base_min) * 0.03
        current_val = max(base_min, min(base_max, current_val + change))
        data_points.append(TrendDataPoint(
            timestamp=timestamp,
            value=round(current_val, 2),
            predicted=False
        ))

    last_value = data_points[-1].value if data_points else base_min
    trend_direction = TrendDirection.UPWARD if metric in [InsightMetricType.PERFORMANCE, InsightMetricType.EFFICIENCY, InsightMetricType.SUCCESS_RATE, InsightMetricType.COVERAGE] else (
        TrendDirection.DOWNWARD if metric in [InsightMetricType.RESPONSE_TIME, InsightMetricType.ERROR_RATE, InsightMetricType.TECHNICAL_DEBT] else TrendDirection.STABLE
    )
    first_value = data_points[0].value if data_points else base_min
    change_pct = round((last_value - first_value) / max(first_value, 0.01) * 100, 2) if data_points else 0

    predicted_points = []
    predicted_val = last_value
    pred_count = min(10, points_count // 3)
    for i in range(pred_count):
        pred_change = (random.random() - 0.45) * (base_max - base_min) * 0.02
        if trend_direction == TrendDirection.UPWARD:
            pred_change = abs(pred_change)
        elif trend_direction == TrendDirection.DOWNWARD:
            pred_change = -abs(pred_change)
        predicted_val = max(base_min, min(base_max, predicted_val + pred_change))
        predicted_points.append(TrendDataPoint(
            timestamp=now + interval * (i + 1),
            value=round(predicted_val, 2),
            predicted=True,
            confidence=round(0.9 - i * 0.05, 2)
        ))

    return TrendPrediction(
        metric_type=metric,
        period=period,
        direction=trend_direction,
        change_percentage=change_pct,
        current_value=round(last_value, 2),
        predicted_value=round(predicted_val, 2) if predicted_points else None,
        confidence_score=round(0.82 + random.random() * 0.15, 2),
        data_points=data_points + predicted_points,
        prediction_horizon=period
    )

def _generate_mock_recommendations() -> List[ImprovementRecommendation]:
    return [
        ImprovementRecommendation(
            recommendation_id=f"rec_{int(time.time())}_001",
            title="优化代码生成器响应时间",
            description="当前代码生成器平均响应时间为2.1s，建议通过增加缓存层和优化算法将响应时间降低至1.5s以内",
            priority=RecommendationPriority.HIGH,
            category="performance_optimization",
            impact_area=["code_generator", "response_time", "user_experience"],
            estimated_improvement={"response_time_reduction_pct": 28.6, "throughput_increase_pct": 15.2},
            effort_level="medium",
            risk_level="low"
        ),
        ImprovementRecommendation(
            recommendation_id=f"rec_{int(time.time())}_002",
            title="提升测试覆盖率至90%以上",
            description="当前整体测试覆盖率为82.3%，建议补充边界条件和异常路径的测试用例",
            priority=RecommendationPriority.MEDIUM,
            category="quality_improvement",
            impact_area=["test_runner", "coverage", "code_quality"],
            estimated_improvement={"coverage_increase": 7.7, "defect_detection_rate": 12.5},
            effort_level="high",
            risk_level="low"
        ),
        ImprovementRecommendation(
            recommendation_id=f"rec_{int(time.time())}_003",
            title="修复安全扫描器依赖漏洞",
            description="检测到3个关键安全漏洞，建议立即更新依赖库版本",
            priority=RecommendationPriority.CRITICAL,
            category="security",
            impact_area=["security_scanner", "dependency_management", "security_compliance"],
            estimated_improvement={"vulnerability_count": -3, "security_score": 15.0},
            effort_level="medium",
            risk_level="medium"
        ),
        ImprovementRecommendation(
            recommendation_id=f"rec_{int(time.time())}_004",
            title="优化内存使用效率",
            description="测试运行器存在内存泄漏问题，内存增长率为150MB/hour，建议实施对象池和定期GC策略",
            priority=RecommendationPriority.HIGH,
            category="resource_optimization",
            impact_area=["test_runner", "memory_management", "stability"],
            estimated_improvement={"memory_reduction_pct": 40.0, "stability_increase": 25.0},
            effort_level="high",
            risk_level="medium"
        ),
        ImprovementRecommendation(
            recommendation_id=f"rec_{int(time.time())}_005",
            title="增强知识库同步机制",
            description="建议实现增量同步和冲突解决机制，减少全量同步带来的性能开销",
            priority=RecommendationPriority.LOW,
            category="architecture_improvement",
            impact_area=["knowledge_base", "sync_mechanism", "network_efficiency"],
            estimated_improvement={"sync_time_reduction_pct": 60.0, "bandwidth_saving_pct": 45.0},
            effort_level="high",
            risk_level="low"
        ),
    ]

def _generate_mock_evolution_status() -> EvolutionStatusInsight:
    return EvolutionStatusInsight(
        current_phase=EvolutionPhase.IDLE,
        progress_percentage=0.0,
        active_cycle_id=None,
        last_cycle_result={
            "cycle_id": f"cycle_{int(time.time()) - 3600}",
            "type": "skill_optimization",
            "status": "completed",
            "duration_seconds": 5400,
            "improvements_applied": 8,
            "success_rate": 0.96
        },
        next_scheduled_cycle=datetime.now() + timedelta(hours=6),
        total_cycles_completed=156,
        success_rate=0.9487,
        average_cycle_duration_seconds=3420.5,
        capabilities_status={
            "self_iteration": {"enabled": True, "status": "active", "last_run": (datetime.now() - timedelta(hours=2)).isoformat(), "success_count": 142},
            "self_optimization": {"enabled": True, "status": "idle", "last_run": (datetime.now() - timedelta(hours=8)).isoformat(), "success_count": 128},
            "self_repair": {"enabled": True, "status": "monitoring", "last_run": (datetime.now() - timedelta(minutes=30)).isoformat(), "success_count": 89},
            "self_improvement": {"enabled": True, "status": "learning", "last_run": (datetime.now() - timedelta(hours=1)).isoformat(), "success_count": 115}
        },
        system_health_score=87.5
    )

@router.get(
    "/trends",
    response_model=TrendPrediction,
    summary="获取趋势预测数据",
    description="分析指定指标在指定时间范围内的趋势，并提供未来预测"
)
async def get_trends(
    metric: InsightMetricType = Query(InsightMetricType.PERFORMANCE, description="指标类型"),
    period: str = Query("7d", description="时间范围: 24h, 7d, 30d"),
    db: Session = Depends(get_db)
):
    cache_key = f"evolution-insights:trends:{metric.value}:{period}"
    cached = cache_service.get_json(cache_key)
    if cached:
        return TrendPrediction(**cached)

    result = _generate_mock_trend_data(metric, period)
    cache_service.set_json(cache_key, result.model_dump(), ttl=_insights_cache_ttl["trends"])
    return result

@router.get(
    "/trends/all",
    response_model=List[TrendPrediction],
    summary="获取所有指标趋势",
    description="获取所有可用指标的趋势预测数据"
)
async def get_all_trends(
    period: str = Query("7d", description="时间范围"),
    db: Session = Depends(get_db)
):
    cache_key = f"evolution-insights:trends:all:{period}"
    cached = cache_service.get_json(cache_key)
    if cached:
        return [TrendPrediction(**c) for c in cached]

    results = [_generate_mock_trend_data(m, period) for m in InsightMetricType]
    cache_service.set_json(cache_key, [r.model_dump() for r in results], ttl=_insights_cache_ttl["trends"])
    return results

@router.get(
    "/recommendations",
    response_model=List[ImprovementRecommendation],
    summary="获取改进建议",
    description="基于当前系统状态生成的改进建议列表，按优先级排序"
)
async def get_recommendations(
    priority: Optional[RecommendationPriority] = Query(None, description="按优先级筛选"),
    category: Optional[str] = Query(None, description="按类别筛选"),
    status: Optional[str] = Query(None, description="按状态筛选"),
    limit: int = Query(20, ge=1, le=100, description="返回数量"),
    db: Session = Depends(get_db)
):
    cache_key = f"evolution-insights:recommendations:{priority}:{category}:{status}:{limit}"
    cached = cache_service.get_json(cache_key)
    if cached:
        return [ImprovementRecommendation(**r) for r in cached]

    recommendations = _generate_mock_recommendations()

    if priority:
        recommendations = [r for r in recommendations if r.priority == priority]
    if category:
        recommendations = [r for r in recommendations if r.category == category]
    if status:
        recommendations = [r for r in recommendations if r.status == status]

    recommendations = sorted(recommendations, key=lambda x: {
        RecommendationPriority.CRITICAL: 0,
        RecommendationPriority.HIGH: 1,
        RecommendationPriority.MEDIUM: 2,
        RecommendationPriority.LOW: 3
    }.get(x.priority, 4))

    result = recommendations[:limit]
    cache_service.set_json(cache_key, [r.model_dump() for r in result], ttl=_insights_cache_ttl["recommendations"])
    return result

@router.get(
    "/status",
    response_model=EvolutionStatusInsight,
    summary="获取当前演化状态",
    description="获取自演化系统的完整状态信息，包括各能力模块状态"
)
async def get_evolution_insights_status(db: Session = Depends(get_db)):
    cache_key = "evolution-insights:status"
    cached = cache_service.get_json(cache_key)
    if cached:
        return EvolutionStatusInsight(**cached)

    result = _generate_mock_evolution_status()
    cache_service.set_json(cache_key, result.model_dump(), ttl=_insights_cache_ttl["status"])
    return result

@router.post(
    "/trigger",
    response_model=EvolutionTriggerResponse,
    summary="手动触发演化循环",
    description="手动触发一次完整的自演化循环"
)
async def trigger_evolution_cycle(
    request: EvolutionTriggerRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    trigger_id = f"trigger_{int(time.time() * 1000)}"
    cycle_id = f"cycle_{int(time.time() * 1000)}"

    if request.dry_run:
        return EvolutionTriggerResponse(
            trigger_id=trigger_id,
            status="dry_run_completed",
            message="模拟运行完成，未执行实际变更",
            estimated_duration=0,
            cycle_id=cycle_id
        )

    async def _execute_evolution_cycle():
        phases = [
            (EvolutionPhase.ANALYZING, 20),
            (EvolutionPhase.PLANNING, 40),
            (EvolutionPhase.EXECUTING, 70),
            (EvolutionPhase.VALIDATING, 90),
            (EvolutionPhase.DEPLOYING, 100),
        ]
        for phase, progress in phases:
            await asyncio.sleep(1)

    background_tasks.add_task(_execute_evolution_cycle)

    return EvolutionTriggerResponse(
        trigger_id=trigger_id,
        status="triggered",
        message=f"演化循环已触发，类型: {request.evolution_type}",
        estimated_duration=600,
        cycle_id=cycle_id
    )

@router.get(
    "/trends/stream",
    summary="趋势数据实时流",
    description="通过SSE推送实时趋势更新数据"
)
async def trends_stream():
    async def event_generator() -> AsyncGenerator[str, None]:
        while True:
            metric = random.choice(list(InsightMetricType))
            trend = _generate_mock_trend_data(metric, "24h")
            data = {
                "type": "trend_update",
                "data": trend.model_dump(),
                "timestamp": datetime.now().isoformat()
            }
            yield f"data: {json.dumps(data)}\n\n"
            await asyncio.sleep(10)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )

@router.get(
    "/summary",
    summary="获取洞察摘要",
    description="获取演化洞察的总体摘要信息"
)
async def get_insights_summary(db: Session = Depends(get_db)):
    trends = {m.value: _generate_mock_trend_data(m, "7d") for m in [InsightMetricType.PERFORMANCE, InsightMetricType.SUCCESS_RATE, InsightMetricType.COVERAGE]}
    recommendations = _generate_mock_recommendations()
    status = _generate_mock_evolution_status()

    return {
        "timestamp": datetime.now().isoformat(),
        "system_health_score": status.system_health_score,
        "evolution_phase": status.current_phase.value,
        "total_recommendations": len(recommendations),
        "critical_recommendations": len([r for r in recommendations if r.priority == RecommendationPriority.CRITICAL]),
        "high_recommendations": len([r for r in recommendations if r.priority == RecommendationPriority.HIGH]),
        "key_metrics": {
            m.value: {
                "current_value": t.current_value,
                "direction": t.direction.value,
                "change_percentage": t.change_percentage,
                "predicted_value": t.predicted_value,
                "confidence": t.confidence_score
            } for m, t in trends.items()
        },
        "capabilities": status.capabilities_status,
        "next Scheduled_cycle": status.next_scheduled_cycle.isoformat() if status.next_scheduled_cycle else None
    }
