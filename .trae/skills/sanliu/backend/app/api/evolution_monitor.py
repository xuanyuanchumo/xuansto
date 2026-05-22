from fastapi import APIRouter, Depends, HTTPException, Query, WebSocket, WebSocketDisconnect, BackgroundTasks
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from typing import List, Optional, Dict, Any, AsyncGenerator
from pydantic import BaseModel, Field
from datetime import datetime, timedelta
from enum import Enum
import json
import asyncio
import time
import queue
import threading

from ..models.base import get_db
from ..services.cache import cache_service, CacheKeys

router = APIRouter()

class EvolutionStatus(str, Enum):
    IDLE = "idle"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    PAUSED = "paused"

class EvolutionType(str, Enum):
    SKILL_OPTIMIZATION = "skill_optimization"
    WORKFLOW_ADAPTATION = "workflow_adaptation"
    RESOURCE_REBALANCE = "resource_rebalance"
    KNOWLEDGE_UPDATE = "knowledge_update"
    PERFORMANCE_TUNING = "performance_tuning"

class EvolutionStage(str, Enum):
    ANALYSIS = "analysis"
    PLANNING = "planning"
    EXECUTION = "execution"
    VALIDATION = "validation"
    DEPLOYMENT = "deployment"

class EvolutionTriggerType(str, Enum):
    AUTOMATIC = "automatic"
    MANUAL = "manual"
    SCHEDULED = "scheduled"
    THRESHOLD_BASED = "threshold_based"

class EvolutionStatusResponse(BaseModel):
    status: EvolutionStatus = Field(..., description="当前演化状态")
    current_stage: Optional[EvolutionStage] = Field(None, description="当前演化阶段")
    evolution_type: Optional[EvolutionType] = Field(None, description="演化类型")
    progress: float = Field(0.0, description="演化进度百分比", ge=0, le=100)
    started_at: Optional[datetime] = Field(None, description="演化开始时间")
    estimated_completion: Optional[datetime] = Field(None, description="预计完成时间")
    current_metrics: Dict[str, Any] = Field(default_factory=dict, description="当前指标")
    active_changes: List[Dict[str, Any]] = Field(default_factory=list, description="正在进行的变更")
    last_evolution: Optional[datetime] = Field(None, description="上次演化时间")
    next_scheduled: Optional[datetime] = Field(None, description="下次计划演化时间")

    class Config:
        from_attributes = True

class EvolutionHistoryItem(BaseModel):
    id: int
    evolution_type: EvolutionType
    trigger_type: EvolutionTriggerType
    status: EvolutionStatus
    started_at: datetime
    completed_at: Optional[datetime]
    duration_seconds: Optional[float]
    changes_count: int
    success_rate: float
    metrics_before: Dict[str, Any]
    metrics_after: Dict[str, Any]
    summary: str

    class Config:
        from_attributes = True

class EvolutionHistoryResponse(BaseModel):
    total: int
    items: List[EvolutionHistoryItem]
    page: int
    page_size: int
    total_pages: int

class TrendDataPoint(BaseModel):
    timestamp: datetime
    value: float
    label: Optional[str] = None

class EvolutionTrendResponse(BaseModel):
    metric_name: str
    period: str
    data_points: List[TrendDataPoint]
    trend_direction: str
    change_percentage: float
    prediction: Optional[float]
    confidence: Optional[float]

class EvolutionTriggerRequest(BaseModel):
    evolution_type: EvolutionType = Field(..., description="演化类型")
    reason: str = Field(..., description="触发原因", min_length=1, max_length=500)
    parameters: Optional[Dict[str, Any]] = Field(default_factory=dict, description="演化参数")
    force: bool = Field(False, description="是否强制执行（忽略当前状态检查）")
    dry_run: bool = Field(False, description="是否为模拟运行（不实际执行变更）")
    priority: str = Field("normal", description="优先级: high, normal, low")
    scheduled_at: Optional[datetime] = Field(None, description="计划执行时间")

class EvolutionTriggerResponse(BaseModel):
    trigger_id: int
    evolution_type: EvolutionType
    status: EvolutionStatus
    message: str
    estimated_duration: Optional[int]
    queued_position: Optional[int]

class EvolutionMetricsSummary(BaseModel):
    total_evolutions: int
    successful_evolutions: int
    failed_evolutions: int
    average_duration: float
    success_rate: float
    most_common_type: Optional[EvolutionType]
    last_24h_count: int
    last_7d_count: int

HEARTBEAT_INTERVAL = 30
HEARTBEAT_TIMEOUT = 60

class EvolutionConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.connection_heartbeats: Dict[WebSocket, float] = {}
        self._heartbeat_task: Optional[asyncio.Task] = None
        self._evolution_state: Dict[str, Any] = {
            "status": EvolutionStatus.IDLE,
            "current_stage": None,
            "evolution_type": None,
            "progress": 0.0,
            "started_at": None,
            "estimated_completion": None,
            "current_metrics": {},
            "active_changes": [],
            "last_evolution": None,
            "next_scheduled": None
        }

    async def start_heartbeat_monitor(self):
        if self._heartbeat_task is None or self._heartbeat_task.done():
            self._heartbeat_task = asyncio.create_task(self._heartbeat_monitor_loop())

    async def _heartbeat_monitor_loop(self):
        while True:
            try:
                await asyncio.sleep(HEARTBEAT_INTERVAL)
                await self._check_heartbeats()
            except asyncio.CancelledError:
                break
            except Exception:
                pass

    async def _check_heartbeats(self):
        current_time = time.time()
        disconnected = []
        
        for websocket in list(self.active_connections):
            last_heartbeat = self.connection_heartbeats.get(websocket, current_time)
            if current_time - last_heartbeat > HEARTBEAT_TIMEOUT:
                disconnected.append(websocket)
        
        for ws in disconnected:
            try:
                await ws.close()
            except Exception:
                pass
            self.disconnect(ws)

    def update_heartbeat(self, websocket: WebSocket):
        self.connection_heartbeats[websocket] = time.time()

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        self.connection_heartbeats[websocket] = time.time()
        await self.start_heartbeat_monitor()

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        if websocket in self.connection_heartbeats:
            del self.connection_heartbeats[websocket]

    async def broadcast(self, message: Dict[str, Any]):
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception:
                pass

    async def broadcast_evolution_update(self, event_type: str, data: Dict[str, Any]):
        await self.broadcast({
            "type": event_type,
            "data": data,
            "timestamp": datetime.now().isoformat()
        })

    def get_state(self) -> Dict[str, Any]:
        return self._evolution_state.copy()

    def update_state(self, **kwargs):
        self._evolution_state.update(kwargs)

evolution_manager = EvolutionConnectionManager()

def _get_mock_evolution_status() -> EvolutionStatusResponse:
    return EvolutionStatusResponse(
        status=EvolutionStatus.IDLE,
        current_stage=None,
        evolution_type=None,
        progress=0.0,
        started_at=None,
        estimated_completion=None,
        current_metrics={
            "skill_success_rate": 94.5,
            "avg_response_time": 1.2,
            "active_agents": 5,
            "pending_tasks": 12
        },
        active_changes=[],
        last_evolution=datetime.now() - timedelta(hours=6),
        next_scheduled=datetime.now() + timedelta(hours=18)
    )

def _get_mock_history(skip: int, limit: int) -> EvolutionHistoryResponse:
    items = []
    for i in range(limit):
        idx = skip + i
        items.append(EvolutionHistoryItem(
            id=idx + 1,
            evolution_type=list(EvolutionType)[idx % len(EvolutionType)],
            trigger_type=list(EvolutionTriggerType)[idx % len(EvolutionTriggerType)],
            status=EvolutionStatus.COMPLETED if idx % 4 != 0 else EvolutionStatus.FAILED,
            started_at=datetime.now() - timedelta(days=idx + 1, hours=idx),
            completed_at=datetime.now() - timedelta(days=idx + 1, hours=idx - 1) if idx % 4 != 0 else None,
            duration_seconds=3600 + idx * 100 if idx % 4 != 0 else None,
            changes_count=5 + idx,
            success_rate=0.95 - idx * 0.01 if idx % 4 != 0 else 0.0,
            metrics_before={"performance": 80 + idx, "efficiency": 75 + idx},
            metrics_after={"performance": 85 + idx, "efficiency": 80 + idx} if idx % 4 != 0 else {},
            summary=f"演化 #{idx + 1} 完成摘要"
        ))
    
    return EvolutionHistoryResponse(
        total=100,
        items=items,
        page=skip // limit + 1,
        page_size=limit,
        total_pages=10
    )

def _get_mock_trends(metric: str, period: str) -> EvolutionTrendResponse:
    data_points = []
    base_value = 80.0
    now = datetime.now()
    
    points_count = 24 if period == "24h" else 7 if period == "7d" else 30
    interval = timedelta(hours=1) if period == "24h" else timedelta(days=1)
    
    for i in range(points_count):
        timestamp = now - interval * (points_count - i - 1)
        value = base_value + (i * 0.5) + (i % 3 * 0.2)
        data_points.append(TrendDataPoint(
            timestamp=timestamp,
            value=round(value, 2),
            label=f"Point {i + 1}"
        ))
    
    return EvolutionTrendResponse(
        metric_name=metric,
        period=period,
        data_points=data_points,
        trend_direction="upward",
        change_percentage=round((data_points[-1].value - data_points[0].value) / data_points[0].value * 100, 2),
        prediction=round(data_points[-1].value * 1.05, 2),
        confidence=0.85
    )

def _get_mock_metrics_summary() -> EvolutionMetricsSummary:
    return EvolutionMetricsSummary(
        total_evolutions=156,
        successful_evolutions=148,
        failed_evolutions=8,
        average_duration=3420.5,
        success_rate=94.87,
        most_common_type=EvolutionType.SKILL_OPTIMIZATION,
        last_24h_count=4,
        last_7d_count=23
    )

@router.get(
    "/status",
    response_model=EvolutionStatusResponse,
    summary="获取演化状态",
    description="获取当前系统的演化状态，包括当前阶段、进度、指标等信息"
)
async def get_evolution_status(db: Session = Depends(get_db)):
    cache_key = "evolution:status"
    cached = cache_service.get_json(cache_key)
    if cached:
        return EvolutionStatusResponse(**cached)
    
    result = _get_mock_evolution_status()
    cache_service.set_json(cache_key, result.model_dump(), ttl=30)
    
    return result

@router.get(
    "/history",
    response_model=EvolutionHistoryResponse,
    summary="获取演化历史",
    description="查询历史演化记录，支持分页和筛选"
)
async def get_evolution_history(
    skip: int = Query(0, description="跳过的记录数", ge=0),
    limit: int = Query(20, description="返回的记录数", ge=1, le=100),
    evolution_type: Optional[EvolutionType] = Query(None, description="按演化类型筛选"),
    status: Optional[EvolutionStatus] = Query(None, description="按状态筛选"),
    start_date: Optional[datetime] = Query(None, description="开始日期"),
    end_date: Optional[datetime] = Query(None, description="结束日期"),
    db: Session = Depends(get_db)
):
    cache_key = f"evolution:history:{skip}:{limit}:{evolution_type}:{status}:{start_date}:{end_date}"
    cached = cache_service.get_json(cache_key)
    if cached:
        return EvolutionHistoryResponse(**cached)
    
    result = _get_mock_history(skip, limit)
    cache_service.set_json(cache_key, result.model_dump(), ttl=60)
    
    return result

@router.get(
    "/trends",
    response_model=EvolutionTrendResponse,
    summary="获取演化趋势",
    description="分析指定指标在指定时间范围内的演化趋势"
)
async def get_evolution_trends(
    metric: str = Query("performance", description="指标名称: performance, efficiency, success_rate, response_time"),
    period: str = Query("7d", description="时间范围: 24h, 7d, 30d"),
    db: Session = Depends(get_db)
):
    cache_key = f"evolution:trends:{metric}:{period}"
    cached = cache_service.get_json(cache_key)
    if cached:
        return EvolutionTrendResponse(**cached)
    
    result = _get_mock_trends(metric, period)
    cache_service.set_json(cache_key, result.model_dump(), ttl=120)
    
    return result

@router.get(
    "/metrics/summary",
    response_model=EvolutionMetricsSummary,
    summary="获取演化指标汇总",
    description="获取演化相关的统计指标汇总"
)
async def get_evolution_metrics_summary(db: Session = Depends(get_db)):
    cache_key = "evolution:metrics:summary"
    cached = cache_service.get_json(cache_key)
    if cached:
        return EvolutionMetricsSummary(**cached)
    
    result = _get_mock_metrics_summary()
    cache_service.set_json(cache_key, result.model_dump(), ttl=300)
    
    return result

async def _execute_evolution(trigger_id: int, request: EvolutionTriggerRequest):
    evolution_manager.update_state(
        status=EvolutionStatus.RUNNING,
        current_stage=EvolutionStage.ANALYSIS,
        evolution_type=request.evolution_type,
        progress=0.0,
        started_at=datetime.now(),
        active_changes=[{"type": request.evolution_type.value, "status": "initializing"}]
    )
    
    await evolution_manager.broadcast_evolution_update("evolution_started", {
        "trigger_id": trigger_id,
        "evolution_type": request.evolution_type.value,
        "reason": request.reason
    })
    
    stages = [
        (EvolutionStage.ANALYSIS, 20),
        (EvolutionStage.PLANNING, 40),
        (EvolutionStage.EXECUTION, 70),
        (EvolutionStage.VALIDATION, 90),
        (EvolutionStage.DEPLOYMENT, 100)
    ]
    
    for stage, progress in stages:
        await asyncio.sleep(2)
        evolution_manager.update_state(
            current_stage=stage,
            progress=progress
        )
        await evolution_manager.broadcast_evolution_update("evolution_progress", {
            "trigger_id": trigger_id,
            "stage": stage.value,
            "progress": progress
        })
    
    evolution_manager.update_state(
        status=EvolutionStatus.COMPLETED,
        current_stage=None,
        progress=100.0,
        last_evolution=datetime.now(),
        active_changes=[]
    )
    
    await evolution_manager.broadcast_evolution_update("evolution_completed", {
        "trigger_id": trigger_id,
        "evolution_type": request.evolution_type.value,
        "duration": 10
    })

@router.post(
    "/trigger",
    response_model=EvolutionTriggerResponse,
    summary="手动触发演化",
    description="手动触发一次演化过程，可选择演化类型和参数"
)
async def trigger_evolution(
    request: EvolutionTriggerRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    current_state = evolution_manager.get_state()
    
    if current_state["status"] == EvolutionStatus.RUNNING and not request.force:
        raise HTTPException(
            status_code=409,
            detail="演化正在进行中，请等待完成或使用 force=true 强制执行"
        )
    
    trigger_id = int(time.time() * 1000)
    
    if request.dry_run:
        return EvolutionTriggerResponse(
            trigger_id=trigger_id,
            evolution_type=request.evolution_type,
            status=EvolutionStatus.IDLE,
            message="模拟运行完成，未执行实际变更",
            estimated_duration=0,
            queued_position=None
        )
    
    background_tasks.add_task(_execute_evolution, trigger_id, request)
    
    return EvolutionTriggerResponse(
        trigger_id=trigger_id,
        evolution_type=request.evolution_type,
        status=EvolutionStatus.RUNNING,
        message="演化已触发，正在后台执行",
        estimated_duration=600,
        queued_position=1
    )

@router.post(
    "/pause",
    summary="暂停演化",
    description="暂停当前正在进行的演化过程"
)
async def pause_evolution(db: Session = Depends(get_db)):
    current_state = evolution_manager.get_state()
    
    if current_state["status"] != EvolutionStatus.RUNNING:
        raise HTTPException(
            status_code=400,
            detail="当前没有正在进行的演化"
        )
    
    evolution_manager.update_state(status=EvolutionStatus.PAUSED)
    
    await evolution_manager.broadcast_evolution_update("evolution_paused", {
        "timestamp": datetime.now().isoformat()
    })
    
    return {"message": "演化已暂停", "status": EvolutionStatus.PAUSED.value}

@router.post(
    "/resume",
    summary="恢复演化",
    description="恢复已暂停的演化过程"
)
async def resume_evolution(db: Session = Depends(get_db)):
    current_state = evolution_manager.get_state()
    
    if current_state["status"] != EvolutionStatus.PAUSED:
        raise HTTPException(
            status_code=400,
            detail="当前没有已暂停的演化"
        )
    
    evolution_manager.update_state(status=EvolutionStatus.RUNNING)
    
    await evolution_manager.broadcast_evolution_update("evolution_resumed", {
        "timestamp": datetime.now().isoformat()
    })
    
    return {"message": "演化已恢复", "status": EvolutionStatus.RUNNING.value}

@router.post(
    "/cancel",
    summary="取消演化",
    description="取消当前正在进行的演化过程"
)
async def cancel_evolution(db: Session = Depends(get_db)):
    current_state = evolution_manager.get_state()
    
    if current_state["status"] not in [EvolutionStatus.RUNNING, EvolutionStatus.PAUSED]:
        raise HTTPException(
            status_code=400,
            detail="当前没有可取消的演化"
        )
    
    evolution_manager.update_state(
        status=EvolutionStatus.IDLE,
        current_stage=None,
        evolution_type=None,
        progress=0.0,
        started_at=None,
        active_changes=[]
    )
    
    await evolution_manager.broadcast_evolution_update("evolution_cancelled", {
        "timestamp": datetime.now().isoformat()
    })
    
    return {"message": "演化已取消", "status": EvolutionStatus.IDLE.value}

@router.websocket("/ws")
async def evolution_websocket_endpoint(websocket: WebSocket):
    await evolution_manager.connect(websocket)
    try:
        current_state = evolution_manager.get_state()
        await websocket.send_json({
            "type": "initial_state",
            "data": current_state,
            "timestamp": datetime.now().isoformat()
        })
        
        while True:
            data = await websocket.receive_text()
            try:
                message = json.loads(data)
                if message.get("type") == "ping":
                    evolution_manager.update_heartbeat(websocket)
                    await websocket.send_json({
                        "type": "pong",
                        "timestamp": time.time()
                    })
                elif message.get("type") == "heartbeat":
                    evolution_manager.update_heartbeat(websocket)
                    await websocket.send_json({
                        "type": "heartbeat_ack",
                        "timestamp": time.time()
                    })
                elif message.get("type") == "get_status":
                    current_state = evolution_manager.get_state()
                    await websocket.send_json({
                        "type": "status_update",
                        "data": current_state,
                        "timestamp": datetime.now().isoformat()
                    })
            except json.JSONDecodeError:
                await websocket.send_json({"error": "Invalid JSON"})
    except WebSocketDisconnect:
        evolution_manager.disconnect(websocket)

def get_evolution_manager() -> EvolutionConnectionManager:
    return evolution_manager

class HealthMonitorStatus(str, Enum):
    ACTIVE = "active"
    PAUSED = "paused"
    ERROR = "error"

class HealthAlertLevel(str, Enum):
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"
    EMERGENCY = "emergency"

class HealthMetricRealtime(BaseModel):
    skill_id: str = Field(..., description="技能ID")
    skill_name: str = Field(..., description="技能名称")
    metric_name: str = Field(..., description="指标名称")
    current_value: float = Field(..., description="当前值")
    threshold_warning: float = Field(..., description="警告阈值")
    threshold_critical: float = Field(..., description="严重阈值")
    unit: str = Field(..., description="单位")
    status: str = Field(..., description="状态: normal, warning, critical")
    trend: str = Field("stable", description="趋势")
    timestamp: datetime = Field(default_factory=datetime.now, description="时间戳")

class HealthAlert(BaseModel):
    alert_id: str = Field(..., description="告警ID")
    skill_id: str = Field(..., description="技能ID")
    skill_name: str = Field(..., description="技能名称")
    level: HealthAlertLevel = Field(..., description="告警级别")
    metric_name: str = Field(..., description="指标名称")
    message: str = Field(..., description="告警消息")
    value: float = Field(..., description="当前值")
    threshold: float = Field(..., description="阈值")
    timestamp: datetime = Field(default_factory=datetime.now, description="时间戳")
    acknowledged: bool = Field(False, description="是否已确认")
    resolved_at: Optional[datetime] = Field(None, description="解决时间")

class HealthMonitorConfig(BaseModel):
    monitor_interval_seconds: int = Field(30, description="监控间隔（秒）")
    alert_cooldown_seconds: int = Field(300, description="告警冷却时间（秒）")
    enable_auto_alert: bool = Field(True, description="启用自动告警")
    monitored_skills: Optional[List[str]] = Field(None, description="监控的技能列表，为空则监控所有")

class HealthMonitorState(BaseModel):
    status: HealthMonitorStatus = Field(HealthMonitorStatus.ACTIVE, description="监控状态")
    last_check: Optional[datetime] = Field(None, description="上次检查时间")
    next_check: Optional[datetime] = Field(None, description="下次检查时间")
    total_checks: int = Field(0, description="总检查次数")
    alerts_count: int = Field(0, description="告警数量")
    active_alerts: int = Field(0, description="活跃告警数")

class HealthMonitorResponse(BaseModel):
    state: HealthMonitorState = Field(..., description="监控状态")
    config: HealthMonitorConfig = Field(..., description="监控配置")
    recent_metrics: List[HealthMetricRealtime] = Field(default_factory=list, description="最近指标")
    active_alerts: List[HealthAlert] = Field(default_factory=list, description="活跃告警")

class HealthMonitorControlRequest(BaseModel):
    action: str = Field(..., description="操作: start, stop, pause, resume")
    config: Optional[HealthMonitorConfig] = Field(None, description="新配置（可选）")

class HealthMonitorControlResponse(BaseModel):
    success: bool = Field(..., description="是否成功")
    message: str = Field(..., description="消息")
    new_status: HealthMonitorStatus = Field(..., description="新状态")

_health_monitor_state: Dict[str, Any] = {
    "status": HealthMonitorStatus.ACTIVE,
    "last_check": None,
    "next_check": None,
    "total_checks": 0,
    "alerts_count": 0,
    "active_alerts": [],
    "config": HealthMonitorConfig()
}

_health_monitor_alerts: List[HealthAlert] = []
_health_monitor_metrics_history: List[HealthMetricRealtime] = []

def _generate_realtime_health_metrics() -> List[HealthMetricRealtime]:
    skills = [
        ("skill_001", "code_generator", "response_time", 1.2, 2.0, 5.0, "seconds"),
        ("skill_001", "code_generator", "success_rate", 98.5, 95.0, 90.0, "%"),
        ("skill_002", "test_runner", "execution_time", 45.0, 60.0, 120.0, "seconds"),
        ("skill_002", "test_runner", "coverage", 85.0, 70.0, 50.0, "%"),
        ("skill_003", "doc_writer", "quality_score", 92.0, 80.0, 60.0, "score"),
        ("skill_004", "api_designer", "validation_rate", 99.2, 95.0, 90.0, "%"),
        ("skill_005", "security_scanner", "scan_time", 3.5, 5.0, 10.0, "seconds"),
    ]
    
    metrics = []
    for skill_id, skill_name, metric_name, value, warning, critical, unit in skills:
        status = "normal"
        if "rate" in metric_name or "coverage" in metric_name or "score" in metric_name:
            if value < critical:
                status = "critical"
            elif value < warning:
                status = "warning"
        else:
            if value > critical:
                status = "critical"
            elif value > warning:
                status = "warning"
        
        metrics.append(HealthMetricRealtime(
            skill_id=skill_id,
            skill_name=skill_name,
            metric_name=metric_name,
            current_value=value + (hash(str(time.time())) % 10) * 0.1,
            threshold_warning=warning,
            threshold_critical=critical,
            unit=unit,
            status=status,
            trend=["improving", "stable", "declining"][hash(metric_name) % 3],
            timestamp=datetime.now()
        ))
    
    return metrics

def _generate_health_alerts() -> List[HealthAlert]:
    alerts = [
        HealthAlert(
            alert_id=f"alert_{int(time.time())}_001",
            skill_id="skill_005",
            skill_name="security_scanner",
            level=HealthAlertLevel.WARNING,
            metric_name="scan_time",
            message="安全扫描时间接近警告阈值",
            value=4.8,
            threshold=5.0,
            timestamp=datetime.now() - timedelta(minutes=15),
            acknowledged=False
        ),
        HealthAlert(
            alert_id=f"alert_{int(time.time())}_002",
            skill_id="skill_002",
            skill_name="test_runner",
            level=HealthAlertLevel.INFO,
            metric_name="coverage",
            message="测试覆盖率有所下降",
            value=82.0,
            threshold=70.0,
            timestamp=datetime.now() - timedelta(hours=1),
            acknowledged=True
        )
    ]
    return alerts

@router.get(
    "/health/realtime",
    response_model=HealthMonitorResponse,
    summary="获取技能健康度实时监控",
    description="获取所有技能的实时健康度监控数据，包括当前指标、活跃告警和监控状态"
)
async def get_health_realtime_monitor(db: Session = Depends(get_db)):
    cache_key = "evolution:health:realtime"
    cached = cache_service.get_json(cache_key)
    if cached:
        return HealthMonitorResponse(**cached)
    
    metrics = _generate_realtime_health_metrics()
    alerts = _generate_health_alerts()
    
    state = HealthMonitorState(
        status=_health_monitor_state["status"],
        last_check=_health_monitor_state.get("last_check"),
        next_check=datetime.now() + timedelta(seconds=30) if _health_monitor_state["status"] == HealthMonitorStatus.ACTIVE else None,
        total_checks=_health_monitor_state["total_checks"],
        alerts_count=len(alerts),
        active_alerts=len([a for a in alerts if not a.acknowledged])
    )
    
    result = HealthMonitorResponse(
        state=state,
        config=_health_monitor_state["config"],
        recent_metrics=metrics,
        active_alerts=alerts
    )
    
    cache_service.set_json(cache_key, result.model_dump(), ttl=10)
    
    return result

@router.get(
    "/health/realtime/stream",
    summary="技能健康度实时数据流",
    description="通过Server-Sent Events推送实时健康度数据"
)
async def health_realtime_stream():
    async def event_generator() -> AsyncGenerator[str, None]:
        while True:
            metrics = _generate_realtime_health_metrics()
            data = {
                "type": "health_metrics",
                "data": [m.model_dump() for m in metrics],
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

@router.post(
    "/health/realtime/control",
    response_model=HealthMonitorControlResponse,
    summary="控制健康度监控",
    description="启动、停止、暂停或恢复健康度监控"
)
async def control_health_monitor(
    request: HealthMonitorControlRequest,
    db: Session = Depends(get_db)
):
    global _health_monitor_state
    
    action = request.action.lower()
    current_status = _health_monitor_state["status"]
    
    if action == "start":
        if current_status == HealthMonitorStatus.ACTIVE:
            return HealthMonitorControlResponse(
                success=False,
                message="监控已在运行中",
                new_status=current_status
            )
        _health_monitor_state["status"] = HealthMonitorStatus.ACTIVE
    elif action == "stop":
        _health_monitor_state["status"] = HealthMonitorStatus.PAUSED
    elif action == "pause":
        if current_status != HealthMonitorStatus.ACTIVE:
            return HealthMonitorControlResponse(
                success=False,
                message="监控未在运行，无法暂停",
                new_status=current_status
            )
        _health_monitor_state["status"] = HealthMonitorStatus.PAUSED
    elif action == "resume":
        if current_status != HealthMonitorStatus.PAUSED:
            return HealthMonitorControlResponse(
                success=False,
                message="监控未暂停，无法恢复",
                new_status=current_status
            )
        _health_monitor_state["status"] = HealthMonitorStatus.ACTIVE
    else:
        raise HTTPException(
            status_code=400,
            detail=f"未知操作: {action}"
        )
    
    if request.config:
        _health_monitor_state["config"] = request.config
    
    return HealthMonitorControlResponse(
        success=True,
        message=f"监控已{action}",
        new_status=_health_monitor_state["status"]
    )

@router.get(
    "/health/alerts",
    response_model=List[HealthAlert],
    summary="获取健康度告警列表",
    description="获取当前所有健康度告警，支持按级别和状态筛选"
)
async def get_health_alerts(
    level: Optional[HealthAlertLevel] = Query(None, description="按告警级别筛选"),
    acknowledged: Optional[bool] = Query(None, description="按确认状态筛选"),
    skill_id: Optional[str] = Query(None, description="按技能ID筛选"),
    limit: int = Query(50, description="返回数量", ge=1, le=200),
    db: Session = Depends(get_db)
):
    cache_key = f"evolution:health:alerts:{level}:{acknowledged}:{skill_id}:{limit}"
    cached = cache_service.get_json(cache_key)
    if cached:
        return [HealthAlert(**a) for a in cached]
    
    alerts = _generate_health_alerts()
    
    if level:
        alerts = [a for a in alerts if a.level == level]
    if acknowledged is not None:
        alerts = [a for a in alerts if a.acknowledged == acknowledged]
    if skill_id:
        alerts = [a for a in alerts if a.skill_id == skill_id]
    
    alerts = alerts[:limit]
    
    cache_service.set_json(cache_key, [a.model_dump() for a in alerts], ttl=30)
    
    return alerts

@router.post(
    "/health/alerts/{alert_id}/acknowledge",
    summary="确认健康度告警",
    description="确认指定的健康度告警"
)
async def acknowledge_health_alert(
    alert_id: str,
    db: Session = Depends(get_db)
):
    global _health_monitor_alerts
    alerts = _generate_health_alerts()
    alert = next((a for a in alerts if a.alert_id == alert_id), None)
    
    if not alert:
        raise HTTPException(
            status_code=404,
            detail=f"未找到告警: {alert_id}"
        )
    
    return {
        "success": True,
        "message": f"告警 {alert_id} 已确认",
        "alert_id": alert_id,
        "acknowledged_at": datetime.now().isoformat()
    }

@router.websocket("/health/realtime/ws")
async def health_realtime_websocket(websocket: WebSocket):
    await websocket.accept()
    try:
        await websocket.send_json({
            "type": "connected",
            "message": "健康度实时监控WebSocket已连接",
            "timestamp": datetime.now().isoformat()
        })
        
        while True:
            try:
                data = await asyncio.wait_for(websocket.receive_text(), timeout=35)
                message = json.loads(data)
                
                if message.get("type") == "ping":
                    await websocket.send_json({
                        "type": "pong",
                        "timestamp": time.time()
                    })
                elif message.get("type") == "get_metrics":
                    metrics = _generate_realtime_health_metrics()
                    await websocket.send_json({
                        "type": "metrics_update",
                        "data": [m.model_dump() for m in metrics],
                        "timestamp": datetime.now().isoformat()
                    })
                elif message.get("type") == "get_alerts":
                    alerts = _generate_health_alerts()
                    await websocket.send_json({
                        "type": "alerts_update",
                        "data": [a.model_dump() for a in alerts],
                        "timestamp": datetime.now().isoformat()
                    })
            except asyncio.TimeoutError:
                metrics = _generate_realtime_health_metrics()
                await websocket.send_json({
                    "type": "metrics_update",
                    "data": [m.model_dump() for m in metrics],
                    "timestamp": datetime.now().isoformat()
                })
    except WebSocketDisconnect:
        pass
    except Exception:
        pass

class AutoFixStatus(str, Enum):
    IDLE = "idle"
    DETECTING = "detecting"
    ANALYZING = "analyzing"
    FIXING = "fixing"
    VERIFYING = "verifying"
    COMPLETED = "completed"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"

class AutoFixTriggerType(str, Enum):
    AUTOMATIC = "automatic"
    MANUAL = "manual"
    SCHEDULED = "scheduled"
    THRESHOLD_BASED = "threshold_based"

class AutoFixSeverity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class AutoFixIssue(BaseModel):
    issue_id: str = Field(..., description="问题ID")
    skill_id: str = Field(..., description="技能ID")
    skill_name: str = Field(..., description="技能名称")
    issue_type: str = Field(..., description="问题类型")
    severity: AutoFixSeverity = Field(..., description="严重程度")
    description: str = Field(..., description="问题描述")
    detected_at: datetime = Field(default_factory=datetime.now, description="检测时间")
    metrics: Dict[str, Any] = Field(default_factory=dict, description="相关指标")
    auto_fixable: bool = Field(True, description="是否可自动修复")

class AutoFixTask(BaseModel):
    task_id: str = Field(..., description="任务ID")
    issue_id: str = Field(..., description="关联问题ID")
    status: AutoFixStatus = Field(..., description="任务状态")
    trigger_type: AutoFixTriggerType = Field(..., description="触发类型")
    started_at: Optional[datetime] = Field(None, description="开始时间")
    completed_at: Optional[datetime] = Field(None, description="完成时间")
    progress: float = Field(0.0, description="进度百分比", ge=0, le=100)
    current_step: Optional[str] = Field(None, description="当前步骤")
    steps_completed: List[str] = Field(default_factory=list, description="已完成步骤")
    steps_remaining: List[str] = Field(default_factory=list, description="剩余步骤")
    fix_strategy: Optional[str] = Field(None, description="修复策略")
    changes_applied: List[Dict[str, Any]] = Field(default_factory=list, description="应用的变更")
    rollback_available: bool = Field(True, description="是否可回滚")
    error_message: Optional[str] = Field(None, description="错误消息")

class AutoFixSummary(BaseModel):
    total_issues_detected: int = Field(0, description="检测到的总问题数")
    total_fixes_applied: int = Field(0, description="已应用的修复数")
    successful_fixes: int = Field(0, description="成功的修复数")
    failed_fixes: int = Field(0, description="失败的修复数")
    rolled_back_fixes: int = Field(0, description="回滚的修复数")
    pending_fixes: int = Field(0, description="待处理的修复数")
    average_fix_duration_seconds: float = Field(0.0, description="平均修复时长（秒）")
    success_rate: float = Field(0.0, description="成功率")

class AutoFixStatusResponse(BaseModel):
    system_status: AutoFixStatus = Field(..., description="系统状态")
    active_tasks: int = Field(0, description="活跃任务数")
    pending_issues: int = Field(0, description="待处理问题数")
    recent_fixes: List[AutoFixTask] = Field(default_factory=list, description="最近的修复任务")
    summary: AutoFixSummary = Field(..., description="修复汇总")

class AutoFixTriggerRequest(BaseModel):
    issue_ids: Optional[List[str]] = Field(None, description="指定问题ID列表，为空则自动检测")
    force: bool = Field(False, description="是否强制执行")
    dry_run: bool = Field(False, description="是否模拟运行")
    strategy: Optional[str] = Field(None, description="指定修复策略")

class AutoFixTriggerResponse(BaseModel):
    task_id: str = Field(..., description="任务ID")
    status: AutoFixStatus = Field(..., description="任务状态")
    issues_to_fix: int = Field(0, description="待修复问题数")
    message: str = Field(..., description="消息")

class AutoFixControlRequest(BaseModel):
    action: str = Field(..., description="操作: pause, resume, cancel, rollback")
    task_id: Optional[str] = Field(None, description="任务ID（可选）")

class AutoFixControlResponse(BaseModel):
    success: bool = Field(..., description="是否成功")
    message: str = Field(..., description="消息")
    new_status: Optional[AutoFixStatus] = Field(None, description="新状态")

_autofix_state: Dict[str, Any] = {
    "system_status": AutoFixStatus.IDLE,
    "active_tasks": [],
    "pending_issues": []
}

_autofix_tasks: Dict[str, AutoFixTask] = {}
_autofix_issues: List[AutoFixIssue] = []

def _generate_autofix_issues() -> List[AutoFixIssue]:
    issues = [
        AutoFixIssue(
            issue_id=f"issue_{int(time.time())}_001",
            skill_id="skill_001",
            skill_name="code_generator",
            issue_type="performance_degradation",
            severity=AutoFixSeverity.MEDIUM,
            description="代码生成器响应时间超过阈值",
            detected_at=datetime.now() - timedelta(minutes=30),
            metrics={
                "response_time": 3.5,
                "threshold": 2.0,
                "deviation": "75%"
            },
            auto_fixable=True
        ),
        AutoFixIssue(
            issue_id=f"issue_{int(time.time())}_002",
            skill_id="skill_002",
            skill_name="test_runner",
            issue_type="resource_leak",
            severity=AutoFixSeverity.HIGH,
            description="测试运行器存在内存泄漏",
            detected_at=datetime.now() - timedelta(hours=1),
            metrics={
                "memory_growth": "150MB/hour",
                "current_memory": "2.5GB",
                "threshold": "2GB"
            },
            auto_fixable=True
        ),
        AutoFixIssue(
            issue_id=f"issue_{int(time.time())}_003",
            skill_id="skill_005",
            skill_name="security_scanner",
            issue_type="dependency_vulnerability",
            severity=AutoFixSeverity.CRITICAL,
            description="发现依赖库存在安全漏洞",
            detected_at=datetime.now() - timedelta(hours=2),
            metrics={
                "vulnerability_count": 3,
                "severity": "critical",
                "affected_packages": ["lodash@4.17.15", "axios@0.19.0"]
            },
            auto_fixable=True
        )
    ]
    return issues

def _generate_autofix_tasks() -> List[AutoFixTask]:
    tasks = [
        AutoFixTask(
            task_id=f"task_{int(time.time())}_001",
            issue_id=f"issue_{int(time.time())}_001",
            status=AutoFixStatus.COMPLETED,
            trigger_type=AutoFixTriggerType.AUTOMATIC,
            started_at=datetime.now() - timedelta(hours=2),
            completed_at=datetime.now() - timedelta(hours=1, minutes=45),
            progress=100.0,
            current_step="完成",
            steps_completed=["检测问题", "分析原因", "应用修复", "验证结果"],
            steps_remaining=[],
            fix_strategy="性能优化策略",
            changes_applied=[
                {"type": "config_change", "key": "max_workers", "old_value": 5, "new_value": 10},
                {"type": "cache_optimization", "action": "enabled_lru_cache"}
            ],
            rollback_available=True
        ),
        AutoFixTask(
            task_id=f"task_{int(time.time())}_002",
            issue_id=f"issue_{int(time.time())}_002",
            status=AutoFixStatus.FIXING,
            trigger_type=AutoFixTriggerType.MANUAL,
            started_at=datetime.now() - timedelta(minutes=15),
            progress=65.0,
            current_step="应用内存优化补丁",
            steps_completed=["检测问题", "分析原因", "定位泄漏源"],
            steps_remaining=["应用修复", "验证结果"],
            fix_strategy="内存泄漏修复策略",
            changes_applied=[],
            rollback_available=True
        ),
        AutoFixTask(
            task_id=f"task_{int(time.time())}_003",
            issue_id=f"issue_{int(time.time())}_003",
            status=AutoFixStatus.ANALYZING,
            trigger_type=AutoFixTriggerType.AUTOMATIC,
            started_at=datetime.now() - timedelta(minutes=5),
            progress=25.0,
            current_step="分析依赖更新影响",
            steps_completed=["检测问题"],
            steps_remaining=["分析原因", "应用修复", "验证结果"],
            fix_strategy="依赖更新策略",
            changes_applied=[],
            rollback_available=True
        )
    ]
    return tasks

@router.get(
    "/autofix/status",
    response_model=AutoFixStatusResponse,
    summary="获取自动修复状态",
    description="获取自动修复系统的整体状态和汇总信息"
)
async def get_autofix_status(db: Session = Depends(get_db)):
    cache_key = "evolution:autofix:status"
    cached = cache_service.get_json(cache_key)
    if cached:
        return AutoFixStatusResponse(**cached)
    
    issues = _generate_autofix_issues()
    tasks = _generate_autofix_tasks()
    
    active_tasks = [t for t in tasks if t.status in [AutoFixStatus.DETECTING, AutoFixStatus.ANALYZING, AutoFixStatus.FIXING, AutoFixStatus.VERIFYING]]
    pending_issues = [i for i in issues if i.auto_fixable]
    
    summary = AutoFixSummary(
        total_issues_detected=len(issues),
        total_fixes_applied=len(tasks),
        successful_fixes=len([t for t in tasks if t.status == AutoFixStatus.COMPLETED]),
        failed_fixes=len([t for t in tasks if t.status == AutoFixStatus.FAILED]),
        rolled_back_fixes=len([t for t in tasks if t.status == AutoFixStatus.ROLLED_BACK]),
        pending_fixes=len([t for t in tasks if t.status in [AutoFixStatus.IDLE, AutoFixStatus.DETECTING, AutoFixStatus.ANALYZING]]),
        average_fix_duration_seconds=900.0,
        success_rate=0.92
    )
    
    result = AutoFixStatusResponse(
        system_status=AutoFixStatus.FIXING if active_tasks else AutoFixStatus.IDLE,
        active_tasks=len(active_tasks),
        pending_issues=len(pending_issues),
        recent_fixes=tasks[:5],
        summary=summary
    )
    
    cache_service.set_json(cache_key, result.model_dump(), ttl=10)
    
    return result

@router.get(
    "/autofix/issues",
    response_model=List[AutoFixIssue],
    summary="获取自动修复问题列表",
    description="获取当前检测到的所有问题，支持按严重程度和状态筛选"
)
async def get_autofix_issues(
    severity: Optional[AutoFixSeverity] = Query(None, description="按严重程度筛选"),
    skill_id: Optional[str] = Query(None, description="按技能ID筛选"),
    auto_fixable: Optional[bool] = Query(None, description="按是否可自动修复筛选"),
    limit: int = Query(50, description="返回数量", ge=1, le=200),
    db: Session = Depends(get_db)
):
    cache_key = f"evolution:autofix:issues:{severity}:{skill_id}:{auto_fixable}:{limit}"
    cached = cache_service.get_json(cache_key)
    if cached:
        return [AutoFixIssue(**i) for i in cached]
    
    issues = _generate_autofix_issues()
    
    if severity:
        issues = [i for i in issues if i.severity == severity]
    if skill_id:
        issues = [i for i in issues if i.skill_id == skill_id]
    if auto_fixable is not None:
        issues = [i for i in issues if i.auto_fixable == auto_fixable]
    
    issues = issues[:limit]
    
    cache_service.set_json(cache_key, [i.model_dump() for i in issues], ttl=30)
    
    return issues

@router.get(
    "/autofix/tasks",
    response_model=List[AutoFixTask],
    summary="获取自动修复任务列表",
    description="获取所有自动修复任务，支持按状态筛选"
)
async def get_autofix_tasks(
    status: Optional[AutoFixStatus] = Query(None, description="按状态筛选"),
    issue_id: Optional[str] = Query(None, description="按问题ID筛选"),
    limit: int = Query(50, description="返回数量", ge=1, le=200),
    db: Session = Depends(get_db)
):
    cache_key = f"evolution:autofix:tasks:{status}:{issue_id}:{limit}"
    cached = cache_service.get_json(cache_key)
    if cached:
        return [AutoFixTask(**t) for t in cached]
    
    tasks = _generate_autofix_tasks()
    
    if status:
        tasks = [t for t in tasks if t.status == status]
    if issue_id:
        tasks = [t for t in tasks if t.issue_id == issue_id]
    
    tasks = tasks[:limit]
    
    cache_service.set_json(cache_key, [t.model_dump() for t in tasks], ttl=30)
    
    return tasks

@router.get(
    "/autofix/tasks/{task_id}",
    response_model=AutoFixTask,
    summary="获取特定自动修复任务",
    description="获取指定自动修复任务的详细信息"
)
async def get_autofix_task(
    task_id: str,
    db: Session = Depends(get_db)
):
    cache_key = f"evolution:autofix:task:{task_id}"
    cached = cache_service.get_json(cache_key)
    if cached:
        return AutoFixTask(**cached)
    
    tasks = _generate_autofix_tasks()
    task = next((t for t in tasks if t.task_id == task_id), None)
    
    if not task:
        raise HTTPException(
            status_code=404,
            detail=f"未找到任务: {task_id}"
        )
    
    cache_service.set_json(cache_key, task.model_dump(), ttl=30)
    
    return task

@router.post(
    "/autofix/trigger",
    response_model=AutoFixTriggerResponse,
    summary="触发自动修复",
    description="手动触发自动修复任务"
)
async def trigger_autofix(
    request: AutoFixTriggerRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    issues = _generate_autofix_issues()
    
    if request.issue_ids:
        issues = [i for i in issues if i.issue_id in request.issue_ids]
    else:
        issues = [i for i in issues if i.auto_fixable]
    
    if not issues:
        return AutoFixTriggerResponse(
            task_id=f"task_{int(time.time() * 1000)}",
            status=AutoFixStatus.IDLE,
            issues_to_fix=0,
            message="没有需要修复的问题"
        )
    
    task_id = f"task_{int(time.time() * 1000)}"
    
    if request.dry_run:
        return AutoFixTriggerResponse(
            task_id=task_id,
            status=AutoFixStatus.IDLE,
            issues_to_fix=len(issues),
            message=f"模拟运行：将修复 {len(issues)} 个问题"
        )
    
    return AutoFixTriggerResponse(
        task_id=task_id,
        status=AutoFixStatus.DETECTING,
        issues_to_fix=len(issues),
        message=f"自动修复已触发，正在处理 {len(issues)} 个问题"
    )

@router.post(
    "/autofix/control",
    response_model=AutoFixControlResponse,
    summary="控制自动修复任务",
    description="暂停、恢复、取消或回滚自动修复任务"
)
async def control_autofix(
    request: AutoFixControlRequest,
    db: Session = Depends(get_db)
):
    action = request.action.lower()
    
    if action == "pause":
        return AutoFixControlResponse(
            success=True,
            message="自动修复任务已暂停",
            new_status=AutoFixStatus.IDLE
        )
    elif action == "resume":
        return AutoFixControlResponse(
            success=True,
            message="自动修复任务已恢复",
            new_status=AutoFixStatus.FIXING
        )
    elif action == "cancel":
        return AutoFixControlResponse(
            success=True,
            message="自动修复任务已取消",
            new_status=AutoFixStatus.IDLE
        )
    elif action == "rollback":
        if not request.task_id:
            raise HTTPException(
                status_code=400,
                detail="回滚操作需要指定任务ID"
            )
        return AutoFixControlResponse(
            success=True,
            message=f"任务 {request.task_id} 已回滚",
            new_status=AutoFixStatus.ROLLED_BACK
        )
    else:
        raise HTTPException(
            status_code=400,
            detail=f"未知操作: {action}"
        )

@router.post(
    "/autofix/tasks/{task_id}/rollback",
    summary="回滚自动修复",
    description="回滚指定的自动修复任务"
)
async def rollback_autofix_task(
    task_id: str,
    db: Session = Depends(get_db)
):
    tasks = _generate_autofix_tasks()
    task = next((t for t in tasks if t.task_id == task_id), None)
    
    if not task:
        raise HTTPException(
            status_code=404,
            detail=f"未找到任务: {task_id}"
        )
    
    if not task.rollback_available:
        raise HTTPException(
            status_code=400,
            detail="该任务不支持回滚"
        )
    
    return {
        "success": True,
        "task_id": task_id,
        "message": f"任务 {task_id} 已回滚",
        "rolled_back_at": datetime.now().isoformat()
    }

@router.get(
    "/autofix/history",
    summary="获取自动修复历史",
    description="获取历史自动修复记录"
)
async def get_autofix_history(
    skip: int = Query(0, description="跳过数量", ge=0),
    limit: int = Query(20, description="返回数量", ge=1, le=100),
    db: Session = Depends(get_db)
):
    cache_key = f"evolution:autofix:history:{skip}:{limit}"
    cached = cache_service.get_json(cache_key)
    if cached:
        return cached
    
    tasks = _generate_autofix_tasks()
    
    history = []
    for i in range(min(limit, len(tasks))):
        task = tasks[i]
        history.append({
            "task_id": task.task_id,
            "issue_id": task.issue_id,
            "status": task.status.value,
            "trigger_type": task.trigger_type.value,
            "started_at": task.started_at.isoformat() if task.started_at else None,
            "completed_at": task.completed_at.isoformat() if task.completed_at else None,
            "progress": task.progress,
            "success": task.status == AutoFixStatus.COMPLETED
        })
    
    result = {
        "total": len(tasks),
        "items": history,
        "page": skip // limit + 1,
        "page_size": limit
    }
    
    cache_service.set_json(cache_key, result, ttl=60)
    
    return result

class EvolutionPrediction(BaseModel):
    prediction_id: str = Field(..., description="预测ID")
    evolution_type: EvolutionType = Field(..., description="演化类型")
    target_components: List[str] = Field(default_factory=list, description="目标组件")
    prediction_horizon: str = Field("short_term", description="预测范围: short_term, medium_term, long_term")
    predicted_metrics: Dict[str, Any] = Field(default_factory=dict, description="预测指标")
    confidence_score: float = Field(0.0, description="置信度分数", ge=0, le=1)
    risk_assessment: Dict[str, Any] = Field(default_factory=dict, description="风险评估")
    recommended_actions: List[str] = Field(default_factory=list, description="推荐操作")
    created_at: datetime = Field(default_factory=datetime.now, description="创建时间")

class EvolutionComparison(BaseModel):
    comparison_id: str = Field(..., description="比较ID")
    baseline_metrics: Dict[str, Any] = Field(..., description="基准指标")
    current_metrics: Dict[str, Any] = Field(..., description="当前指标")
    improvement_percentage: Dict[str, float] = Field(default_factory=dict, description="改进百分比")
    regression_areas: List[str] = Field(default_factory=list, description="回退区域")
    improvement_areas: List[str] = Field(default_factory=list, description="改进区域")
    comparison_time: datetime = Field(default_factory=datetime.now, description="比较时间")

class EvolutionRollback(BaseModel):
    rollback_id: str = Field(..., description="回滚ID")
    evolution_id: str = Field(..., description="演化ID")
    trigger_type: str = Field(..., description="触发类型: manual, automatic, scheduled")
    reason: str = Field(..., description="回滚原因")
    status: str = Field(..., description="状态: pending, running, completed, failed")
    started_at: Optional[datetime] = Field(None, description="开始时间")
    completed_at: Optional[datetime] = Field(None, description="完成时间")
    affected_components: List[str] = Field(default_factory=list, description="影响组件")
    rollback_steps: List[Dict[str, Any]] = Field(default_factory=list, description="回滚步骤")

class EvolutionExport(BaseModel):
    export_id: str = Field(..., description="导出ID")
    export_type: str = Field(..., description="导出类型: json, csv, pdf, html")
    data_scope: str = Field(..., description="数据范围: full, filtered, summary")
    filters: Optional[Dict[str, Any]] = Field(None, description="过滤条件")
    format_config: Optional[Dict[str, Any]] = Field(None, description="格式配置")
    created_at: datetime = Field(default_factory=datetime.now, description="创建时间")
    download_url: Optional[str] = Field(None, description="下载链接")

@router.post(
    "/predict",
    response_model=EvolutionPrediction,
    summary="预测演化效果",
    description="基于历史数据和当前状态预测未来演化效果"
)
async def predict_evolution(
    evolution_type: EvolutionType = Query(..., description="演化类型"),
    target_components: Optional[List[str]] = Query(None, description="目标组件"),
    prediction_horizon: str = Query("short_term", description="预测范围"),
    db: Session = Depends(get_db)
):
    cache_key = f"evolution:predict:{evolution_type}:{target_components}:{prediction_horizon}"
    cached = cache_service.get_json(cache_key)
    if cached:
        return EvolutionPrediction(**cached)
    
    prediction_id = f"pred_{int(time.time() * 1000)}"
    
    predicted_metrics = {
        "performance_improvement": 15.5,
        "error_rate_reduction": 8.2,
        "resource_efficiency": 12.3,
        "stability_score": 0.92
    }
    
    risk_assessment = {
        "overall_risk": "low",
        "rollback_complexity": "medium",
        "data_loss_risk": "none",
        "service_disruption_risk": "low"
    }
    
    recommended_actions = [
        "建议在低峰期执行",
        "建议先在测试环境验证",
        "建议准备回滚方案"
    ]
    
    result = EvolutionPrediction(
        prediction_id=prediction_id,
        evolution_type=evolution_type,
        target_components=target_components or ["all"],
        prediction_horizon=prediction_horizon,
        predicted_metrics=predicted_metrics,
        confidence_score=0.88,
        risk_assessment=risk_assessment,
        recommended_actions=recommended_actions
    )
    
    cache_service.set_json(cache_key, result.model_dump(), ttl=300)
    
    return result

@router.post(
    "/compare",
    response_model=EvolutionComparison,
    summary="比较演化效果",
    description="比较演化前后的指标变化"
)
async def compare_evolution(
    evolution_id: str = Query(..., description="演化ID"),
    db: Session = Depends(get_db)
):
    comparison_id = f"comp_{int(time.time() * 1000)}"
    
    baseline_metrics = {
        "response_time": 250.0,
        "error_rate": 3.5,
        "throughput": 150.0,
        "resource_usage": 75.0
    }
    
    current_metrics = {
        "response_time": 180.0,
        "error_rate": 2.1,
        "throughput": 185.0,
        "resource_usage": 68.0
    }
    
    improvement_percentage = {
        "response_time": 28.0,
        "error_rate": 40.0,
        "throughput": 23.3,
        "resource_usage": 9.3
    }
    
    result = EvolutionComparison(
        comparison_id=comparison_id,
        evolution_id=evolution_id,
        baseline_metrics=baseline_metrics,
        current_metrics=current_metrics,
        improvement_percentage=improvement_percentage,
        regression_areas=[],
        improvement_areas=["response_time", "error_rate", "throughput"],
        comparison_time=datetime.now()
    )
    
    return result

@router.post(
    "/rollback",
    summary="回滚演化",
    description="回滚指定的演化操作"
)
async def rollback_evolution(
    evolution_id: str = Query(..., description="演化ID"),
    reason: str = Query(..., description="回滚原因"),
    trigger_type: str = Query("manual", description="触发类型"),
    db: Session = Depends(get_db)
):
    rollback_id = f"rb_{int(time.time() * 1000)}"
    
    rollback = EvolutionRollback(
        rollback_id=rollback_id,
        evolution_id=evolution_id,
        trigger_type=trigger_type,
        reason=reason,
        status="running",
        started_at=datetime.now(),
        affected_components=["api", "services", "models"],
        rollback_steps=[
            {"step": 1, "action": "停止当前演化", "status": "pending"},
            {"step": 2, "action": "恢复备份数据", "status": "pending"},
            {"step": 3, "action": "重启服务", "status": "pending"},
            {"step": 4, "action": "验证系统状态", "status": "pending"}
        ]
    )
    
    await evolution_manager.broadcast_evolution_update("rollback_started", {
        "rollback_id": rollback_id,
        "evolution_id": evolution_id,
        "reason": reason
    })
    
    return {
        "success": True,
        "rollback_id": rollback_id,
        "message": "回滚已启动",
        "estimated_duration": 300
    }

@router.post(
    "/export",
    response_model=EvolutionExport,
    summary="导出演化数据",
    description="导出演化历史和统计数据"
)
async def export_evolution_data(
    export_type: str = Query("json", description="导出类型"),
    data_scope: str = Query("full", description="数据范围"),
    filters: Optional[Dict[str, Any]] = None,
    db: Session = Depends(get_db)
):
    export_id = f"export_{int(time.time() * 1000)}"
    
    download_url = f"/api/evolution-monitor/downloads/{export_id}.{export_type}"
    
    result = EvolutionExport(
        export_id=export_id,
        export_type=export_type,
        data_scope=data_scope,
        filters=filters,
        format_config={"include_metadata": True, "pretty_print": True},
        created_at=datetime.now(),
        download_url=download_url
    )
    
    return result

@router.websocket("/autofix/ws")
async def autofix_status_websocket(websocket: WebSocket):
    await websocket.accept()
    try:
        await websocket.send_json({
            "type": "connected",
            "message": "自动修复状态WebSocket已连接",
            "timestamp": datetime.now().isoformat()
        })
        
        while True:
            try:
                data = await asyncio.wait_for(websocket.receive_text(), timeout=35)
                message = json.loads(data)
                
                if message.get("type") == "ping":
                    await websocket.send_json({
                        "type": "pong",
                        "timestamp": time.time()
                    })
                elif message.get("type") == "get_status":
                    issues = _generate_autofix_issues()
                    tasks = _generate_autofix_tasks()
                    await websocket.send_json({
                        "type": "status_update",
                        "data": {
                            "system_status": "fixing" if any(t.status in [AutoFixStatus.FIXING, AutoFixStatus.ANALYZING] for t in tasks) else "idle",
                            "active_tasks": len([t for t in tasks if t.status in [AutoFixStatus.DETECTING, AutoFixStatus.ANALYZING, AutoFixStatus.FIXING, AutoFixStatus.VERIFYING]]),
                            "pending_issues": len([i for i in issues if i.auto_fixable])
                        },
                        "timestamp": datetime.now().isoformat()
                    })
                elif message.get("type") == "get_tasks":
                    tasks = _generate_autofix_tasks()
                    await websocket.send_json({
                        "type": "tasks_update",
                        "data": [t.model_dump() for t in tasks[:10]],
                        "timestamp": datetime.now().isoformat()
                    })
                elif message.get("type") == "get_issues":
                    issues = _generate_autofix_issues()
                    await websocket.send_json({
                        "type": "issues_update",
                        "data": [i.model_dump() for i in issues[:10]],
                        "timestamp": datetime.now().isoformat()
                    })
            except asyncio.TimeoutError:
                tasks = _generate_autofix_tasks()
                active_tasks = [t for t in tasks if t.status in [AutoFixStatus.FIXING, AutoFixStatus.ANALYZING]]
                if active_tasks:
                    await websocket.send_json({
                        "type": "progress_update",
                        "data": {
                            "task_id": active_tasks[0].task_id,
                            "progress": active_tasks[0].progress,
                            "current_step": active_tasks[0].current_step
                        },
                        "timestamp": datetime.now().isoformat()
                    })
    except WebSocketDisconnect:
        pass
    except Exception:
        pass

class KnowledgeUpdateType(str, Enum):
    PATTERN_ADDED = "pattern_added"
    PATTERN_UPDATED = "pattern_updated"
    PATTERN_DEPRECATED = "pattern_deprecated"
    RECOMMENDATION_GENERATED = "recommendation_generated"
    KNOWLEDGE_SYNC = "knowledge_sync"
    CACHE_INVALIDATED = "cache_invalidated"
    MODEL_UPDATED = "model_updated"

class KnowledgeUpdatePriority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class KnowledgeUpdateNotification(BaseModel):
    notification_id: str = Field(..., description="通知ID")
    update_type: KnowledgeUpdateType = Field(..., description="更新类型")
    priority: KnowledgeUpdatePriority = Field(..., description="优先级")
    title: str = Field(..., description="标题")
    message: str = Field(..., description="消息内容")
    affected_components: List[str] = Field(default_factory=list, description="影响的组件")
    affected_skills: List[str] = Field(default_factory=list, description="影响的技能")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="元数据")
    timestamp: datetime = Field(default_factory=datetime.now, description="时间戳")
    read: bool = Field(False, description="是否已读")
    acknowledged: bool = Field(False, description="是否已确认")

class KnowledgeUpdateSubscription(BaseModel):
    subscription_id: str = Field(..., description="订阅ID")
    update_types: List[KnowledgeUpdateType] = Field(default_factory=list, description="订阅的更新类型")
    priorities: Optional[List[KnowledgeUpdatePriority]] = Field(None, description="订阅的优先级")
    created_at: datetime = Field(default_factory=datetime.now, description="创建时间")
    active: bool = Field(True, description="是否活跃")

class KnowledgeUpdateSubscriptionRequest(BaseModel):
    update_types: List[KnowledgeUpdateType] = Field(..., description="订阅的更新类型")
    priorities: Optional[List[KnowledgeUpdatePriority]] = Field(None, description="订阅的优先级")
    callback_url: Optional[str] = Field(None, description="回调URL")

class KnowledgeUpdateSubscriptionResponse(BaseModel):
    subscription_id: str = Field(..., description="订阅ID")
    update_types: List[KnowledgeUpdateType] = Field(..., description="订阅的更新类型")
    status: str = Field(..., description="订阅状态")
    message: str = Field(..., description="消息")

class KnowledgeUpdateHistoryResponse(BaseModel):
    total: int = Field(0, description="总数")
    notifications: List[KnowledgeUpdateNotification] = Field(default_factory=list, description="通知列表")
    page: int = Field(1, description="页码")
    page_size: int = Field(20, description="每页大小")

class KnowledgeUpdateBroadcastRequest(BaseModel):
    update_type: KnowledgeUpdateType = Field(..., description="更新类型")
    priority: KnowledgeUpdatePriority = Field(..., description="优先级")
    title: str = Field(..., description="标题")
    message: str = Field(..., description="消息内容")
    affected_components: Optional[List[str]] = Field(None, description="影响的组件")
    affected_skills: Optional[List[str]] = Field(None, description="影响的技能")
    metadata: Optional[Dict[str, Any]] = Field(None, description="元数据")

_knowledge_notifications: List[KnowledgeUpdateNotification] = []
_knowledge_subscriptions: Dict[str, KnowledgeUpdateSubscription] = {}

def _generate_knowledge_notifications() -> List[KnowledgeUpdateNotification]:
    notifications = [
        KnowledgeUpdateNotification(
            notification_id=f"knotif_{int(time.time())}_001",
            update_type=KnowledgeUpdateType.PATTERN_ADDED,
            priority=KnowledgeUpdatePriority.HIGH,
            title="新演化模式已添加",
            message="性能优化模式v2.0已添加到知识库",
            affected_components=["evolution_engine", "skill_optimizer"],
            affected_skills=["skill_001", "skill_002"],
            metadata={
                "pattern_id": "pattern_006",
                "pattern_name": "性能优化模式v2.0",
                "added_by": "system"
            },
            timestamp=datetime.now() - timedelta(hours=1)
        ),
        KnowledgeUpdateNotification(
            notification_id=f"knotif_{int(time.time())}_002",
            update_type=KnowledgeUpdateType.RECOMMENDATION_GENERATED,
            priority=KnowledgeUpdatePriority.MEDIUM,
            title="新演化推荐已生成",
            message="基于当前系统状态，已生成3条新的演化推荐",
            affected_components=["recommendation_engine"],
            affected_skills=["skill_003", "skill_004"],
            metadata={
                "recommendations_count": 3,
                "trigger": "automatic_analysis"
            },
            timestamp=datetime.now() - timedelta(hours=2)
        ),
        KnowledgeUpdateNotification(
            notification_id=f"knotif_{int(time.time())}_003",
            update_type=KnowledgeUpdateType.KNOWLEDGE_SYNC,
            priority=KnowledgeUpdatePriority.LOW,
            title="知识库同步完成",
            message="知识库已与远程存储同步，新增15条记录",
            affected_components=["knowledge_base", "cache_layer"],
            affected_skills=[],
            metadata={
                "sync_duration_ms": 2500,
                "records_added": 15,
                "records_updated": 8
            },
            timestamp=datetime.now() - timedelta(hours=5)
        ),
        KnowledgeUpdateNotification(
            notification_id=f"knotif_{int(time.time())}_004",
            update_type=KnowledgeUpdateType.MODEL_UPDATED,
            priority=KnowledgeUpdatePriority.CRITICAL,
            title="演化模型已更新",
            message="核心演化模型已更新至v3.2，建议重新评估现有演化策略",
            affected_components=["evolution_model", "prediction_engine"],
            affected_skills=["skill_001", "skill_002", "skill_003", "skill_004", "skill_005"],
            metadata={
                "old_version": "3.1",
                "new_version": "3.2",
                "breaking_changes": False
            },
            timestamp=datetime.now() - timedelta(hours=8)
        )
    ]
    return notifications

@router.get(
    "/knowledge/notifications",
    response_model=KnowledgeUpdateHistoryResponse,
    summary="获取知识库更新通知",
    description="获取知识库更新通知列表，支持按类型、优先级和状态筛选"
)
async def get_knowledge_notifications(
    update_type: Optional[KnowledgeUpdateType] = Query(None, description="按更新类型筛选"),
    priority: Optional[KnowledgeUpdatePriority] = Query(None, description="按优先级筛选"),
    read: Optional[bool] = Query(None, description="按已读状态筛选"),
    acknowledged: Optional[bool] = Query(None, description="按确认状态筛选"),
    skip: int = Query(0, description="跳过数量", ge=0),
    limit: int = Query(20, description="返回数量", ge=1, le=100),
    db: Session = Depends(get_db)
):
    cache_key = f"evolution:knowledge:notifications:{update_type}:{priority}:{read}:{acknowledged}:{skip}:{limit}"
    cached = cache_service.get_json(cache_key)
    if cached:
        return KnowledgeUpdateHistoryResponse(**cached)
    
    notifications = _generate_knowledge_notifications()
    
    if update_type:
        notifications = [n for n in notifications if n.update_type == update_type]
    if priority:
        notifications = [n for n in notifications if n.priority == priority]
    if read is not None:
        notifications = [n for n in notifications if n.read == read]
    if acknowledged is not None:
        notifications = [n for n in notifications if n.acknowledged == acknowledged]
    
    total = len(notifications)
    notifications = notifications[skip:skip + limit]
    
    result = KnowledgeUpdateHistoryResponse(
        total=total,
        notifications=notifications,
        page=skip // limit + 1,
        page_size=limit
    )
    
    cache_service.set_json(cache_key, result.model_dump(), ttl=30)
    
    return result

@router.post(
    "/knowledge/notifications/broadcast",
    summary="广播知识库更新通知",
    description="向所有订阅者广播知识库更新通知"
)
async def broadcast_knowledge_notification(
    request: KnowledgeUpdateBroadcastRequest,
    db: Session = Depends(get_db)
):
    notification_id = f"knotif_{int(time.time() * 1000)}"
    
    notification = KnowledgeUpdateNotification(
        notification_id=notification_id,
        update_type=request.update_type,
        priority=request.priority,
        title=request.title,
        message=request.message,
        affected_components=request.affected_components or [],
        affected_skills=request.affected_skills or [],
        metadata=request.metadata or {}
    )
    
    _knowledge_notifications.insert(0, notification)
    
    await evolution_manager.broadcast_evolution_update("knowledge_update", notification.model_dump())
    
    return {
        "success": True,
        "notification_id": notification_id,
        "message": "知识库更新通知已广播",
        "subscribers_notified": len(_knowledge_subscriptions)
    }

@router.post(
    "/knowledge/notifications/{notification_id}/read",
    summary="标记通知为已读",
    description="将指定的知识库更新通知标记为已读"
)
async def mark_notification_read(
    notification_id: str,
    db: Session = Depends(get_db)
):
    notifications = _generate_knowledge_notifications()
    notification = next((n for n in notifications if n.notification_id == notification_id), None)
    
    if not notification:
        raise HTTPException(
            status_code=404,
            detail=f"未找到通知: {notification_id}"
        )
    
    return {
        "success": True,
        "notification_id": notification_id,
        "read_at": datetime.now().isoformat()
    }

@router.post(
    "/knowledge/notifications/{notification_id}/acknowledge",
    summary="确认知识库更新通知",
    description="确认指定的知识库更新通知"
)
async def acknowledge_knowledge_notification(
    notification_id: str,
    db: Session = Depends(get_db)
):
    notifications = _generate_knowledge_notifications()
    notification = next((n for n in notifications if n.notification_id == notification_id), None)
    
    if not notification:
        raise HTTPException(
            status_code=404,
            detail=f"未找到通知: {notification_id}"
        )
    
    return {
        "success": True,
        "notification_id": notification_id,
        "acknowledged_at": datetime.now().isoformat()
    }

@router.post(
    "/knowledge/subscribe",
    response_model=KnowledgeUpdateSubscriptionResponse,
    summary="订阅知识库更新",
    description="订阅指定类型的知识库更新通知"
)
async def subscribe_knowledge_updates(
    request: KnowledgeUpdateSubscriptionRequest,
    db: Session = Depends(get_db)
):
    subscription_id = f"ksub_{int(time.time() * 1000)}"
    
    subscription = KnowledgeUpdateSubscription(
        subscription_id=subscription_id,
        update_types=request.update_types,
        priorities=request.priorities
    )
    
    _knowledge_subscriptions[subscription_id] = subscription
    
    return KnowledgeUpdateSubscriptionResponse(
        subscription_id=subscription_id,
        update_types=request.update_types,
        status="active",
        message="订阅成功，将通过WebSocket接收知识库更新通知"
    )

@router.delete(
    "/knowledge/subscribe/{subscription_id}",
    summary="取消知识库更新订阅",
    description="取消指定的知识库更新订阅"
)
async def unsubscribe_knowledge_updates(
    subscription_id: str,
    db: Session = Depends(get_db)
):
    if subscription_id not in _knowledge_subscriptions:
        raise HTTPException(
            status_code=404,
            detail=f"未找到订阅: {subscription_id}"
        )
    
    del _knowledge_subscriptions[subscription_id]
    
    return {
        "success": True,
        "message": f"订阅 {subscription_id} 已取消"
    }

@router.get(
    "/knowledge/subscriptions",
    response_model=List[KnowledgeUpdateSubscription],
    summary="获取所有知识库更新订阅",
    description="获取当前所有活跃的知识库更新订阅"
)
async def get_knowledge_subscriptions(db: Session = Depends(get_db)):
    return list(_knowledge_subscriptions.values())

@router.websocket("/knowledge/ws")
async def knowledge_updates_websocket(websocket: WebSocket):
    await websocket.accept()
    try:
        await websocket.send_json({
            "type": "connected",
            "message": "知识库更新通知WebSocket已连接",
            "timestamp": datetime.now().isoformat()
        })
        
        while True:
            try:
                data = await asyncio.wait_for(websocket.receive_text(), timeout=35)
                message = json.loads(data)
                
                if message.get("type") == "ping":
                    await websocket.send_json({
                        "type": "pong",
                        "timestamp": time.time()
                    })
                elif message.get("type") == "subscribe":
                    update_types = message.get("update_types", [])
                    subscription_id = f"ws_ksub_{int(time.time() * 1000)}"
                    
                    subscription = KnowledgeUpdateSubscription(
                        subscription_id=subscription_id,
                        update_types=[KnowledgeUpdateType(ut) for ut in update_types]
                    )
                    _knowledge_subscriptions[subscription_id] = subscription
                    
                    await websocket.send_json({
                        "type": "subscription_confirmed",
                        "subscription_id": subscription_id,
                        "update_types": update_types,
                        "timestamp": datetime.now().isoformat()
                    })
                elif message.get("type") == "get_notifications":
                    notifications = _generate_knowledge_notifications()
                    await websocket.send_json({
                        "type": "notifications_update",
                        "data": [n.model_dump() for n in notifications[:10]],
                        "timestamp": datetime.now().isoformat()
                    })
            except asyncio.TimeoutError:
                notifications = _generate_knowledge_notifications()
                if notifications:
                    latest = notifications[0]
                    await websocket.send_json({
                        "type": "notification_push",
                        "data": latest.model_dump(),
                        "timestamp": datetime.now().isoformat()
                    })
    except WebSocketDisconnect:
        pass
    except Exception:
        pass

class EvolutionEventType(str, Enum):
    EVOLUTION_STARTED = "evolution_started"
    EVOLUTION_PROGRESS = "evolution_progress"
    EVOLUTION_STAGE_CHANGE = "evolution_stage_change"
    EVOLUTION_COMPLETED = "evolution_completed"
    EVOLUTION_FAILED = "evolution_failed"
    EVOLUTION_PAUSED = "evolution_paused"
    EVOLUTION_RESUMED = "evolution_resumed"
    EVOLUTION_CANCELLED = "evolution_cancelled"
    METRICS_UPDATE = "metrics_update"
    ERROR_ALERT = "error_alert"

class EvolutionEvent(BaseModel):
    event_id: str = Field(..., description="事件ID")
    event_type: EvolutionEventType = Field(..., description="事件类型")
    evolution_id: Optional[str] = Field(None, description="演化ID")
    timestamp: datetime = Field(default_factory=datetime.now, description="时间戳")
    data: Dict[str, Any] = Field(default_factory=dict, description="事件数据")
    message: Optional[str] = Field(None, description="事件消息")
    severity: str = Field("info", description="严重程度: info, warning, error, critical")

class EvolutionSubscription(BaseModel):
    subscription_id: str = Field(..., description="订阅ID")
    event_types: List[EvolutionEventType] = Field(default_factory=list, description="订阅的事件类型")
    created_at: datetime = Field(default_factory=datetime.now, description="创建时间")
    active: bool = Field(True, description="是否活跃")

class EvolutionSubscriptionRequest(BaseModel):
    event_types: List[EvolutionEventType] = Field(..., description="订阅的事件类型")
    callback_url: Optional[str] = Field(None, description="回调URL（可选）")

class EvolutionSubscriptionResponse(BaseModel):
    subscription_id: str = Field(..., description="订阅ID")
    event_types: List[EvolutionEventType] = Field(..., description="订阅的事件类型")
    status: str = Field(..., description="订阅状态")
    message: str = Field(..., description="消息")
    created_at: datetime = Field(default_factory=datetime.now, description="创建时间")

class EvolutionEventHistory(BaseModel):
    total: int = Field(0, description="总数")
    events: List[EvolutionEvent] = Field(default_factory=list, description="事件列表")
    page: int = Field(1, description="页码")
    page_size: int = Field(20, description="每页大小")

_evolution_event_history: List[EvolutionEvent] = []
_evolution_subscriptions: Dict[str, EvolutionSubscription] = {}

def _generate_evolution_events() -> List[EvolutionEvent]:
    events = [
        EvolutionEvent(
            event_id=f"evt_{int(time.time())}_001",
            event_type=EvolutionEventType.EVOLUTION_STARTED,
            evolution_id="evo_001",
            timestamp=datetime.now() - timedelta(hours=2),
            data={
                "evolution_type": "skill_optimization",
                "trigger": "automatic",
                "target_skills": ["skill_001", "skill_002"]
            },
            message="技能优化演化已启动",
            severity="info"
        ),
        EvolutionEvent(
            event_id=f"evt_{int(time.time())}_002",
            event_type=EvolutionEventType.EVOLUTION_STAGE_CHANGE,
            evolution_id="evo_001",
            timestamp=datetime.now() - timedelta(hours=1, minutes=50),
            data={
                "previous_stage": "analysis",
                "current_stage": "planning",
                "progress": 25
            },
            message="演化阶段从分析切换到规划",
            severity="info"
        ),
        EvolutionEvent(
            event_id=f"evt_{int(time.time())}_003",
            event_type=EvolutionEventType.EVOLUTION_PROGRESS,
            evolution_id="evo_001",
            timestamp=datetime.now() - timedelta(hours=1, minutes=30),
            data={
                "progress": 50,
                "current_stage": "execution",
                "estimated_remaining": "30 minutes"
            },
            message="演化进度达到50%",
            severity="info"
        ),
        EvolutionEvent(
            event_id=f"evt_{int(time.time())}_004",
            event_type=EvolutionEventType.ERROR_ALERT,
            evolution_id="evo_001",
            timestamp=datetime.now() - timedelta(hours=1),
            data={
                "error_code": "E001",
                "error_message": "资源临时不可用",
                "retry_count": 1
            },
            message="演化过程中出现错误，正在重试",
            severity="warning"
        ),
        EvolutionEvent(
            event_id=f"evt_{int(time.time())}_005",
            event_type=EvolutionEventType.EVOLUTION_COMPLETED,
            evolution_id="evo_001",
            timestamp=datetime.now() - timedelta(minutes=30),
            data={
                "duration_seconds": 5400,
                "success_rate": 0.98,
                "changes_applied": 12
            },
            message="演化成功完成",
            severity="info"
        )
    ]
    return events

@router.get(
    "/events",
    response_model=EvolutionEventHistory,
    summary="获取演化事件历史",
    description="获取演化系统的事件历史记录，支持按事件类型和时间筛选"
)
async def get_evolution_events(
    event_type: Optional[EvolutionEventType] = Query(None, description="按事件类型筛选"),
    evolution_id: Optional[str] = Query(None, description="按演化ID筛选"),
    severity: Optional[str] = Query(None, description="按严重程度筛选"),
    start_time: Optional[datetime] = Query(None, description="开始时间"),
    end_time: Optional[datetime] = Query(None, description="结束时间"),
    skip: int = Query(0, description="跳过数量", ge=0),
    limit: int = Query(20, description="返回数量", ge=1, le=100),
    db: Session = Depends(get_db)
):
    cache_key = f"evolution:events:{event_type}:{evolution_id}:{severity}:{skip}:{limit}"
    cached = cache_service.get_json(cache_key)
    if cached:
        return EvolutionEventHistory(**cached)
    
    events = _generate_evolution_events()
    
    if event_type:
        events = [e for e in events if e.event_type == event_type]
    if evolution_id:
        events = [e for e in events if e.evolution_id == evolution_id]
    if severity:
        events = [e for e in events if e.severity == severity]
    if start_time:
        events = [e for e in events if e.timestamp >= start_time]
    if end_time:
        events = [e for e in events if e.timestamp <= end_time]
    
    total = len(events)
    events = events[skip:skip + limit]
    
    result = EvolutionEventHistory(
        total=total,
        events=events,
        page=skip // limit + 1,
        page_size=limit
    )
    
    cache_service.set_json(cache_key, result.model_dump(), ttl=30)
    
    return result

@router.post(
    "/events/subscribe",
    response_model=EvolutionSubscriptionResponse,
    summary="订阅演化事件",
    description="订阅指定类型的演化事件，可通过WebSocket或回调URL接收通知"
)
async def subscribe_evolution_events(
    request: EvolutionSubscriptionRequest,
    db: Session = Depends(get_db)
):
    subscription_id = f"sub_{int(time.time() * 1000)}"
    
    subscription = EvolutionSubscription(
        subscription_id=subscription_id,
        event_types=request.event_types
    )
    
    _evolution_subscriptions[subscription_id] = subscription
    
    return EvolutionSubscriptionResponse(
        subscription_id=subscription_id,
        event_types=request.event_types,
        status="active",
        message="订阅成功，将通过WebSocket接收事件通知"
    )

@router.delete(
    "/events/subscribe/{subscription_id}",
    summary="取消演化事件订阅",
    description="取消指定的演化事件订阅"
)
async def unsubscribe_evolution_events(
    subscription_id: str,
    db: Session = Depends(get_db)
):
    if subscription_id not in _evolution_subscriptions:
        raise HTTPException(
            status_code=404,
            detail=f"未找到订阅: {subscription_id}"
        )
    
    del _evolution_subscriptions[subscription_id]
    
    return {
        "success": True,
        "message": f"订阅 {subscription_id} 已取消"
    }

@router.get(
    "/events/subscriptions",
    response_model=List[EvolutionSubscription],
    summary="获取所有订阅",
    description="获取当前所有活跃的演化事件订阅"
)
async def get_evolution_subscriptions(db: Session = Depends(get_db)):
    return list(_evolution_subscriptions.values())

@router.websocket("/events/ws")
async def evolution_events_websocket(websocket: WebSocket):
    await websocket.accept()
    try:
        await websocket.send_json({
            "type": "connected",
            "message": "演化事件推送WebSocket已连接",
            "timestamp": datetime.now().isoformat()
        })
        
        while True:
            try:
                data = await asyncio.wait_for(websocket.receive_text(), timeout=35)
                message = json.loads(data)
                
                if message.get("type") == "ping":
                    await websocket.send_json({
                        "type": "pong",
                        "timestamp": time.time()
                    })
                elif message.get("type") == "subscribe":
                    event_types = message.get("event_types", [])
                    subscription_id = f"ws_sub_{int(time.time() * 1000)}"
                    
                    subscription = EvolutionSubscription(
                        subscription_id=subscription_id,
                        event_types=[EvolutionEventType(et) for et in event_types]
                    )
                    _evolution_subscriptions[subscription_id] = subscription
                    
                    await websocket.send_json({
                        "type": "subscription_confirmed",
                        "subscription_id": subscription_id,
                        "event_types": event_types,
                        "timestamp": datetime.now().isoformat()
                    })
                elif message.get("type") == "get_events":
                    events = _generate_evolution_events()
                    await websocket.send_json({
                        "type": "events_update",
                        "data": [e.model_dump() for e in events[:10]],
                        "timestamp": datetime.now().isoformat()
                    })
            except asyncio.TimeoutError:
                events = _generate_evolution_events()
                if events:
                    latest_event = events[0]
                    await websocket.send_json({
                        "type": "event_push",
                        "data": latest_event.model_dump(),
                        "timestamp": datetime.now().isoformat()
                    })
    except WebSocketDisconnect:
        pass
    except Exception:
        pass
