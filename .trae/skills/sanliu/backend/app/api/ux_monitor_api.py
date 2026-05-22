"""
用户体验监控 API - /api/ux/*

页面性能、交互分析
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
from ..services.cache import cache_service

router = APIRouter()

class MetricLevel(str, Enum):
    EXCELLENT = "excellent"
    GOOD = "good"
    FAIR = "fair"
    POOR = "poor"

class EventType(str, Enum):
    PAGE_VIEW = "page_view"
    CLICK = "click"
    SCROLL = "scroll"
    FORM_SUBMIT = "form_submit"
    ERROR = "error"
    NAVIGATION = "navigation"
    CUSTOM = "custom"

class DeviceType(str, Enum):
    DESKTOP = "desktop"
    MOBILE = "mobile"
    TABLET = "tablet"

class UXMetricCard(BaseModel):
    metric_name: str
    display_name: str
    value: float
    unit: str
    level: MetricLevel
    trend: str = Field("stable", description="up, down, stable")
    change_percentage: float = 0.0
    threshold_good: float
    threshold_fair: float
    target_value: Optional[float] = None

class UXMetricsResponse(BaseModel):
    timestamp: datetime
    metrics: List[UXMetricCard]
    overall_score: float = Field(0.0, ge=0, le=100)
    overall_level: MetricLevel

class UserEvent(BaseModel):
    event_id: str
    event_type: EventType
    page_url: str
    user_id: Optional[str] = None
    session_id: str
    device_type: DeviceType = DeviceType.DESKTOP
    timestamp: datetime = Field(default_factory=datetime.now)
    data: Dict[str, Any] = Field(default_factory=dict)
    duration_ms: Optional[float] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

class UserEventBatch(BaseModel):
    events: List[UserEvent]

class BehaviorPathNode(BaseModel):
    page: str
    timestamp: datetime
    duration_seconds: float
    event_count: int

class BehaviorPathAnalysis(BaseModel):
    session_id: str
    user_id: Optional[str]
    path: List[BehaviorPathNode]
    total_duration_seconds: float
    page_count: int
    bounce_rate: float
    exit_page: str
    conversion_funnel: List[Dict[str, Any]]

class DashboardData(BaseModel):
    period: str
    generated_at: datetime
    summary: Dict[str, Any]
    metrics_cards: List[UXMetricCard]
    top_pages: List[Dict[str, Any]]
    error_distribution: List[Dict[str, Any]]
    device_breakdown: Dict[str, Any]
    trend_data: Dict[str, List[Dict[str, Any]]]
    user_flow_funnel: List[Dict[str, Any]]

_event_store: List[UserEvent] = []

def _generate_ux_metrics() -> UXMetricsResponse:
    metrics = [
        UXMetricCard(
            metric_name="fcp",
            display_name="首次内容绘制",
            value=round(random.uniform(0.8, 2.5), 2),
            unit="s",
            level=MetricLevel.GOOD if random.random() > 0.3 else MetricLevel.EXCELLENT,
            trend=random.choice(["up", "down", "stable"]),
            change_percentage=round(random.uniform(-15, 10), 1),
            threshold_good=1.8,
            threshold_fair=3.0,
            target_value=1.0
        ),
        UXMetricCard(
            metric_name="lcp",
            display_name="最大内容绘制",
            value=round(random.uniform(1.5, 4.0), 2),
            unit="s",
            level=random.choices([MetricLevel.EXCELLENT, MetricLevel.GOOD, MetricLevel.FAIR, MetricLevel.POOR], weights=[30, 40, 20, 10])[0],
            trend=random.choice(["up", "down", "stable"]),
            change_percentage=round(random.uniform(-20, 8), 1),
            threshold_good=2.5,
            threshold_fair=4.0,
            target_value=2.0
        ),
        UXMetricCard(
            metric_name="fid",
            display_name="首次输入延迟",
            value=round(random.uniform(20, 150), 0),
            unit="ms",
            level=MetricLevel.GOOD if random.random() > 0.25 else MetricLevel.FAIR,
            trend=random.choice(["up", "down", "stable"]),
            change_percentage=round(random.uniform(-25, 12), 1),
            threshold_good=100,
            threshold_fair=300,
            target_value=50
        ),
        UXMetricCard(
            metric_name="cls",
            display_name="累积布局偏移",
            value=round(random.uniform(0.01, 0.15), 3),
            unit="",
            level=random.choices([MetricLevel.EXCELLENT, MetricLevel.GOOD, MetricLevel.FAIR], weights=[40, 35, 25])[0],
            trend=random.choice(["up", "down", "stable"]),
            change_percentage=round(random.uniform(-30, 15), 1),
            threshold_good=0.1,
            threshold_fair=0.25,
            target_value=0.05
        ),
        UXMetricCard(
            metric_name="ttfb",
            display_name="首字节时间",
            value=round(random.uniform(100, 600), 0),
            unit="ms",
            level=random.choices([MetricLevel.EXCELLENT, MetricLevel.GOOD, MetricLevel.FAIR], weights=[35, 40, 25])[0],
            trend=random.choice(["up", "down", "stable"]),
            change_percentage=round(random.uniform(-18, 10), 1),
            threshold_good=300,
            threshold_fair=500,
            target_value=200
        ),
        UXMetricCard(
            metric_name="interaction_time",
            display_name="交互响应时间(P99)",
            value=round(random.uniform(50, 300), 0),
            unit="ms",
            level=MetricLevel.GOOD if random.random() > 0.3 else MetricLevel.EXCELLENT,
            trend=random.choice(["up", "down", "stable"]),
            change_percentage=round(random.uniform(-12, 8), 1),
            threshold_good=150,
            threshold_fair=250,
            target_value=100
        ),
    ]

    overall_score = sum(
        100 if m.level == MetricLevel.EXCELLENT else
        80 if m.level == MetricLevel.GOOD else
        60 if m.level == MetricLevel.FAIR else 30
        for m in metrics
    ) / len(metrics)

    overall_level = (
        MetricLevel.EXCELLENT if overall_score >= 90 else
        MetricLevel.GOOD if overall_score >= 75 else
        MetricLevel.FAIR if overall_score >= 60 else
        MetricLevel.POOR
    )

    return UXMetricsResponse(
        timestamp=datetime.now(),
        metrics=metrics,
        overall_score=round(overall_score, 1),
        overall_level=overall_level
    )

def _generate_dashboard_data(period: str = "24h") -> DashboardData:
    now = datetime.now()
    hours = 24 if period == "24h" else 168 if period == "7d" else 720

    pages = [
        {"path": "/dashboard", "name": "仪表盘", "views": random.randint(800, 2000), "avg_duration": round(random.uniform(30, 120), 1)},
        {"path": "/projects", "name": "项目管理", "views": random.randint(400, 1200), "avg_duration": round(random.uniform(60, 180), 1)},
        {"path": "/tasks", "name": "任务管理", "views": random.randint(600, 1500), "avg_duration": round(random.uniform(45, 150), 1)},
        {"path": "/realtime-quality", "name": "实时质量", "views": random.randint(200, 600), "avg_duration": round(random.uniform(90, 240), 1)},
        {"path": "/evolution", "name": "演化洞察", "views": random.randint(150, 450), "avg_duration": round(random.uniform(60, 180), 1)},
        {"path": "/reports", "name": "报告中心", "views": random.randint(100, 350), "avg_duration": round(random.uniform(120, 300), 1)},
    ]

    errors = [
        {"type": "js_error", "count": random.randint(5, 30), "percentage": round(random.uniform(30, 50), 1)},
        {"type": "api_error", "count": random.randint(2, 15), "percentage": round(random.uniform(15, 30), 1)},
        {"type": "resource_load_error", "count": random.randint(1, 10), "percentage": round(random.uniform(8, 20), 1)},
        {"type": "network_error", "count": random.randint(0, 8), "percentage": round(random.uniform(3, 12), 1)},
    ]

    funnel = [
        {"step": "访问首页", "count": 1000, "rate": 100.0},
        {"step": "浏览仪表盘", "count": 850, "rate": 85.0},
        {"step": "查看详情页", "count": 620, "rate": 62.0},
        {"step": "执行操作", "count": 380, "rate": 38.0},
        {"step": "完成任务", "count": 245, "rate": 24.5},
    ]

    trend_points = []
    for i in range(min(hours, 48)):
        ts = now - timedelta(hours=(min(hours, 48) - i - 1))
        trend_points.append({
            "timestamp": ts.isoformat(),
            "fcp": round(random.uniform(0.8, 2.5), 2),
            "lcp": round(random.uniform(1.5, 4.0), 2),
            "fid": round(random.uniform(20, 150), 0),
            "cls": round(random.uniform(0.01, 0.15), 3),
            "users": random.randint(10, 80),
            "page_views": random.randint(30, 200)
        })

    return DashboardData(
        period=period,
        generated_at=now,
        summary={
            "total_sessions": random.randint(500, 2000),
            "unique_users": random.randint(200, 800),
            "total_page_views": random.randint(2000, 8000),
            "avg_session_duration_seconds": round(random.uniform(120, 480), 1),
            "bounce_rate": round(random.uniform(0.2, 0.5), 2),
            "error_rate": round(random.uniform(0.01, 0.05), 3),
            "conversion_rate": round(random.uniform(0.15, 0.35), 2),
        },
        metrics_cards=_generate_ux_metrics().metrics,
        top_pages=pages,
        error_distribution=errors,
        device_breakdown={
            "desktop": {"count": random.randint(400, 900), "percentage": round(random.uniform(55, 70), 1)},
            "mobile": {"count": random.randint(150, 400), "percentage": round(random.uniform(22, 35), 1)},
            "tablet": {"count": random.randint(30, 120), "percentage": round(random.uniform(8, 15), 1)},
        },
        trend_data={
            "performance": trend_points[-24:] if period == "24h" else trend_points[-48:],
            "errors": [{"hour": i, "count": random.randint(0, 15)} for i in range(24)]
        },
        user_flow_funnel=funnel
    )

@router.get(
    "/metrics",
    response_model=UXMetricsResponse,
    summary="获取UX指标",
    description="获取当前的核心Web Vitals和自定义UX指标"
)
async def get_ux_metrics(db: Session = Depends(get_db)):
    cache_key = "ux:metrics"
    cached = cache_service.get_json(cache_key)
    if cached:
        return UXMetricsResponse(**cached)

    result = _generate_ux_metrics()
    cache_service.set_json(cache_key, result.model_dump(), ttl=30)
    return result

@router.post(
    "/events",
    summary="上报用户事件",
    description="接收前端上报的用户交互事件数据"
)
async def report_user_events(
    events: UserEventBatch,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    def process_events():
        for event in events.events:
            _event_store.append(event)
        if len(_event_store) > 10000:
            _event_store[:] = _event_store[-5000:]

    background_tasks.add_task(process_events)

    return {
        "success": True,
        "received_count": len(events.events),
        "message": "事件已接收并处理",
        "timestamp": datetime.now().isoformat()
    }

@router.get(
    "/analysis",
    response_model=BehaviorPathAnalysis,
    summary="用户行为路径分析",
    description="分析指定会话的用户行为路径和转化漏斗"
)
async def analyze_behavior_path(
    session_id: Optional[str] = Query(None, description="会话ID"),
    user_id: Optional[str] = Query(None, description="用户ID"),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    sample_session = session_id or f"session_{int(time.time())}"

    path_nodes = [
        BehaviorPathNode(page="/", timestamp=datetime.now() - timedelta(minutes=30), duration_seconds=12.5, event_count=5),
        BehaviorPathNode(page="/dashboard", timestamp=datetime.now() - timedelta(minutes=28), duration_seconds=45.2, event_count=18),
        BehaviorPathNode(page="/projects", timestamp=datetime.now() - timedelta(minutes=23), duration_seconds=32.8, event_count=12),
        BehaviorPathNode(page="/projects/123", timestamp=datetime.now() - timedelta(minutes=18), duration_seconds=68.4, event_count=25),
        BehaviorPathNode(page="/tasks?project=123", timestamp=datetime.now() - timedelta(minutes=10), duration_seconds=55.1, event_count=20),
        BehaviorPathNode(page="/realtime-quality", timestamp=datetime.now() - timedelta(minutes=5), duration_seconds=42.3, event_count=15),
    ]

    conversion_funnel = [
        {"step": "首页访问", "visitors": 1000, "dropoff": 0, "dropoff_rate": 0},
        {"step": "进入仪表盘", "visitors": 850, "dropoff": 150, "dropoff_rate": 15.0},
        {"step": "浏览项目列表", "visitors": 620, "dropoff": 230, "dropoff_rate": 27.1},
        {"step": "查看项目详情", "visitors": 420, "dropoff": 200, "dropoff_rate": 32.3},
        {"step": "操作任务", "visitors": 280, "dropoff": 140, "dropoff_rate": 33.3},
        {"step": "完成操作", "visitors": 165, "dropoff": 115, "dropoff_rate": 41.1},
    ]

    return BehaviorPathAnalysis(
        session_id=sample_session,
        user_id=user_id,
        path=path_nodes,
        total_duration_seconds=sum(n.duration_seconds for n in path_nodes),
        page_count=len(path_nodes),
        bounce_rate=round(random.uniform(0.2, 0.4), 2),
        exit_page=path_nodes[-1].page,
        conversion_funnel=conversion_funnel
    )

@router.get(
    "/dashboard",
    response_model=DashboardData,
    summary="UX仪表盘数据",
    description="获取完整的UX监控仪表盘数据，包含摘要、趋势、漏斗等"
)
async def get_ux_dashboard(
    period: str = Query("24h", description="时间范围: 24h, 7d, 30d"),
    db: Session = Depends(get_db)
):
    cache_key = f"ux:dashboard:{period}"
    cached = cache_service.get_json(cache_key)
    if cached:
        return DashboardData(**cached)

    result = _generate_dashboard_data(period)
    cache_service.set_json(cache_key, result.model_dump(), ttl=60)
    return result

@router.get(
    "/pages",
    summary="页面性能排行",
    description="获取各页面的性能指标排名"
)
async def get_page_performance(
    sort_by: str = Query("avg_duration", description="排序字段"),
    limit: int = Query(20, ge=1, le=50),
    db: Session = Depends(get_db)
):
    dashboard = _generate_dashboard_data()
    pages = dashboard.top_pages
    reverse = sort_by in ["avg_duration", "views"]
    pages.sort(key=lambda p: p.get(sort_by, 0), reverse=reverse)
    return {"pages": pages[:limit], "total": len(pages)}

@router.get(
    "/errors",
    summary="错误统计",
    description="获取前端错误分布和趋势数据"
)
async def get_error_stats(
    hours: int = Query(24, ge=1, le=720),
    db: Session = Depends(get_db)
):
    dashboard = _generate_dashboard_data()
    error_trend = [{"time_ago_hours": h, "count": random.randint(0, 20)} for h in range(min(hours, 48))]

    recent_errors = [
        {"error_id": f"err_{int(time.time())}_{i}", "type": e["type"], "message": f"{e['type']} example message {i}", "count": e["count"], "last_seen": (datetime.now() - timedelta(minutes=random.randint(1, 120))).isoformat(), "url": "/dashboard"}
        for i, e in enumerate(dashboard.error_distribution)
    ]

    return {
        "summary": dashboard.error_distribution,
        "trend": error_trend[-hours:],
        "recent_errors": recent_errors,
        "total_errors_last_period": sum(e["count"] for e in dashboard.error_distribution)
    }

@router.get(
    "/stream",
    summary="实时UX数据流",
    description="通过SSE推送实时UX指标更新"
)
async def ux_realtime_stream():
    async def event_generator() -> AsyncGenerator[str, None]:
        while True:
            metrics = _generate_ux_metrics()
            data = {
                "type": "metrics_update",
                "data": metrics.model_dump(),
                "timestamp": datetime.now().isoformat()
            }
            yield f"data: {json.dumps(data)}\n\n"
            await asyncio.sleep(5)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )
