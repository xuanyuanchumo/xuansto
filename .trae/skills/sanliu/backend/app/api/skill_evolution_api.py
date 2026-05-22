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
import io
import csv
import random

from ..models.base import get_db
from ..services.cache import cache_service, CacheKeys

router = APIRouter()

class EvolutionStatus(str, Enum):
    IDLE = "idle"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    PAUSED = "paused"
    ROLLING_BACK = "rolling_back"

class EvolutionType(str, Enum):
    SKILL_OPTIMIZATION = "skill_optimization"
    WORKFLOW_ADAPTATION = "workflow_adaptation"
    RESOURCE_REBALANCE = "resource_rebalance"
    KNOWLEDGE_UPDATE = "knowledge_update"
    PERFORMANCE_TUNING = "performance_tuning"
    MODEL_UPGRADE = "model_upgrade"
    CONFIG_UPDATE = "config_update"

class EvolutionPhase(str, Enum):
    INITIALIZATION = "initialization"
    ANALYSIS = "analysis"
    PLANNING = "planning"
    EXECUTION = "execution"
    VALIDATION = "validation"
    DEPLOYMENT = "deployment"
    CLEANUP = "cleanup"

class TriggerType(str, Enum):
    AUTOMATIC = "automatic"
    MANUAL = "manual"
    SCHEDULED = "scheduled"
    THRESHOLD_BASED = "threshold_based"
    API_TRIGGERED = "api_triggered"

class HealthStatus(str, Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    CRITICAL = "critical"

class ContentMonitorStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    ERROR = "error"
    PAUSED = "paused"

class SkillEvolutionStatus(BaseModel):
    is_running: bool = Field(..., description="是否正在演化")
    current_phase: str = Field(..., description="当前演化阶段")
    last_evolution: Optional[datetime] = Field(None, description="上次演化时间")
    total_evolutions: int = Field(0, description="总演化次数")
    success_rate: float = Field(0.0, description="成功率")
    active_monitors: List[str] = Field(default_factory=list, description="活跃监控器列表")
    evolution_type: Optional[EvolutionType] = Field(None, description="当前演化类型")
    progress: float = Field(0.0, description="演化进度", ge=0, le=100)
    started_at: Optional[datetime] = Field(None, description="开始时间")
    estimated_completion: Optional[datetime] = Field(None, description="预计完成时间")

    class Config:
        from_attributes = True

class ContentStatusResponse(BaseModel):
    monitor_id: str = Field(..., description="监控器ID")
    status: ContentMonitorStatus = Field(..., description="监控状态")
    last_check: datetime = Field(..., description="上次检查时间")
    items_monitored: int = Field(0, description="监控项目数")
    alerts_count: int = Field(0, description="告警数量")
    health_score: float = Field(0.0, description="健康分数", ge=0, le=100)
    details: Dict[str, Any] = Field(default_factory=dict, description="详细信息")

    class Config:
        from_attributes = True

class ContentStatusListResponse(BaseModel):
    total_monitors: int = Field(..., description="监控器总数")
    active_monitors: int = Field(..., description="活跃监控器数")
    monitors: List[ContentStatusResponse] = Field(default_factory=list, description="监控器列表")
    overall_health: float = Field(0.0, description="整体健康分数")

class HealthCheckResult(BaseModel):
    component: str = Field(..., description="组件名称")
    status: HealthStatus = Field(..., description="健康状态")
    message: str = Field(..., description="状态消息")
    details: Dict[str, Any] = Field(default_factory=dict, description="详细信息")
    last_check: datetime = Field(..., description="上次检查时间")

class SkillHealthStatus(BaseModel):
    overall_status: HealthStatus = Field(..., description="整体健康状态")
    components: List[HealthCheckResult] = Field(default_factory=list, description="组件健康检查结果")
    uptime_seconds: int = Field(0, description="运行时间（秒）")
    last_evolution: Optional[datetime] = Field(None, description="上次演化时间")
    pending_operations: int = Field(0, description="待处理操作数")
    error_count_24h: int = Field(0, description="24小时内错误数")

    class Config:
        from_attributes = True

class EvolutionHistoryItem(BaseModel):
    event_id: str = Field(..., description="事件ID")
    timestamp: datetime = Field(..., description="时间戳")
    evolution_type: EvolutionType = Field(..., description="演化类型")
    trigger_type: TriggerType = Field(..., description="触发类型")
    status: EvolutionStatus = Field(..., description="状态")
    duration_ms: int = Field(0, description="持续时间（毫秒）")
    changes: List[str] = Field(default_factory=list, description="变更列表")
    summary: Optional[str] = Field(None, description="摘要")
    metrics_before: Dict[str, Any] = Field(default_factory=dict, description="演化前指标")
    metrics_after: Dict[str, Any] = Field(default_factory=dict, description="演化后指标")
    rollback_available: bool = Field(False, description="是否可回滚")

    class Config:
        from_attributes = True

class EvolutionHistoryListResponse(BaseModel):
    total: int = Field(..., description="总数")
    items: List[EvolutionHistoryItem] = Field(default_factory=list, description="历史记录列表")
    page: int = Field(1, description="当前页")
    page_size: int = Field(20, description="每页大小")
    total_pages: int = Field(1, description="总页数")

class EvolutionEventDetail(BaseModel):
    event_id: str = Field(..., description="事件ID")
    timestamp: datetime = Field(..., description="时间戳")
    evolution_type: EvolutionType = Field(..., description="演化类型")
    trigger_type: TriggerType = Field(..., description="触发类型")
    status: EvolutionStatus = Field(..., description="状态")
    duration_ms: int = Field(0, description="持续时间（毫秒）")
    phases: List[Dict[str, Any]] = Field(default_factory=list, description="阶段详情")
    changes: List[Dict[str, Any]] = Field(default_factory=list, description="变更详情")
    metrics_before: Dict[str, Any] = Field(default_factory=dict, description="演化前指标")
    metrics_after: Dict[str, Any] = Field(default_factory=dict, description="演化后指标")
    errors: List[Dict[str, Any]] = Field(default_factory=list, description="错误信息")
    rollback_info: Optional[Dict[str, Any]] = Field(None, description="回滚信息")
    related_events: List[str] = Field(default_factory=list, description="相关事件ID")

    class Config:
        from_attributes = True

class EvolutionStatistics(BaseModel):
    total_evolutions: int = Field(0, description="总演化次数")
    successful_evolutions: int = Field(0, description="成功次数")
    failed_evolutions: int = Field(0, description="失败次数")
    rolled_back_evolutions: int = Field(0, description="回滚次数")
    average_duration_ms: float = Field(0.0, description="平均持续时间（毫秒）")
    success_rate: float = Field(0.0, description="成功率")
    evolution_by_type: Dict[str, int] = Field(default_factory=dict, description="按类型统计")
    evolution_by_trigger: Dict[str, int] = Field(default_factory=dict, description="按触发类型统计")
    last_24h_count: int = Field(0, description="24小时内演化次数")
    last_7d_count: int = Field(0, description="7天内演化次数")
    last_30d_count: int = Field(0, description="30天内演化次数")
    most_active_period: Optional[str] = Field(None, description="最活跃时段")
    average_changes_per_evolution: float = Field(0.0, description="每次演化平均变更数")

    class Config:
        from_attributes = True

class TriggerEvolutionRequest(BaseModel):
    evolution_type: EvolutionType = Field(..., description="演化类型")
    reason: str = Field(..., description="触发原因", min_length=1, max_length=500)
    parameters: Optional[Dict[str, Any]] = Field(default_factory=dict, description="演化参数")
    force: bool = Field(False, description="是否强制执行")
    dry_run: bool = Field(False, description="是否模拟运行")
    priority: str = Field("normal", description="优先级: high, normal, low")
    scheduled_at: Optional[datetime] = Field(None, description="计划执行时间")
    timeout_seconds: int = Field(3600, description="超时时间（秒）", ge=60, le=86400)

class TriggerEvolutionResponse(BaseModel):
    trigger_id: str = Field(..., description="触发ID")
    evolution_type: EvolutionType = Field(..., description="演化类型")
    status: EvolutionStatus = Field(..., description="状态")
    message: str = Field(..., description="消息")
    estimated_duration_ms: Optional[int] = Field(None, description="预计持续时间（毫秒）")
    queued_position: Optional[int] = Field(None, description="队列位置")

class PauseEvolutionRequest(BaseModel):
    reason: Optional[str] = Field(None, description="暂停原因", max_length=500)
    save_state: bool = Field(True, description="是否保存当前状态")

class PauseEvolutionResponse(BaseModel):
    success: bool = Field(..., description="是否成功")
    message: str = Field(..., description="消息")
    saved_state_id: Optional[str] = Field(None, description="保存的状态ID")
    paused_at: datetime = Field(..., description="暂停时间")

class ResumeEvolutionRequest(BaseModel):
    state_id: Optional[str] = Field(None, description="要恢复的状态ID")
    continue_from_checkpoint: bool = Field(True, description="是否从检查点继续")

class ResumeEvolutionResponse(BaseModel):
    success: bool = Field(..., description="是否成功")
    message: str = Field(..., description="消息")
    resumed_at: datetime = Field(..., description="恢复时间")
    current_phase: str = Field(..., description="当前阶段")

class RollbackRequest(BaseModel):
    event_id: str = Field(..., description="要回滚的事件ID")
    reason: str = Field(..., description="回滚原因", min_length=1, max_length=500)
    force: bool = Field(False, description="是否强制回滚")
    create_backup: bool = Field(True, description="是否创建备份")

class RollbackResponse(BaseModel):
    rollback_id: str = Field(..., description="回滚ID")
    target_event_id: str = Field(..., description="目标事件ID")
    status: EvolutionStatus = Field(..., description="状态")
    message: str = Field(..., description="消息")
    estimated_duration_ms: Optional[int] = Field(None, description="预计持续时间（毫秒）")
    backup_id: Optional[str] = Field(None, description="备份ID")

class EvolutionReport(BaseModel):
    report_id: str = Field(..., description="报告ID")
    generated_at: datetime = Field(..., description="生成时间")
    period_start: datetime = Field(..., description="报告周期开始")
    period_end: datetime = Field(..., description="报告周期结束")
    summary: Dict[str, Any] = Field(default_factory=dict, description="摘要")
    evolution_statistics: EvolutionStatistics = Field(..., description="演化统计")
    health_trends: List[Dict[str, Any]] = Field(default_factory=list, description="健康趋势")
    recommendations: List[str] = Field(default_factory=list, description="建议")
    detailed_events: List[EvolutionHistoryItem] = Field(default_factory=list, description="详细事件")

    class Config:
        from_attributes = True

class ExportFormat(str, Enum):
    JSON = "json"
    CSV = "csv"
    EXCEL = "excel"

class ExportRequest(BaseModel):
    format: ExportFormat = Field(ExportFormat.JSON, description="导出格式")
    start_date: Optional[datetime] = Field(None, description="开始日期")
    end_date: Optional[datetime] = Field(None, description="结束日期")
    include_metrics: bool = Field(True, description="是否包含指标")
    include_changes: bool = Field(True, description="是否包含变更详情")

class CallChainNode(BaseModel):
    node_id: str = Field(..., description="节点ID")
    node_type: str = Field(..., description="节点类型")
    name: str = Field(..., description="名称")
    status: str = Field(..., description="状态")
    duration_ms: int = Field(0, description="持续时间（毫秒）")
    children: List["CallChainNode"] = Field(default_factory=list, description="子节点")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="元数据")

class CallChainResponse(BaseModel):
    event_id: str = Field(..., description="事件ID")
    root_node: CallChainNode = Field(..., description="根节点")
    total_nodes: int = Field(0, description="总节点数")
    max_depth: int = Field(0, description="最大深度")
    total_duration_ms: int = Field(0, description="总持续时间（毫秒）")

HEARTBEAT_INTERVAL = 30
HEARTBEAT_TIMEOUT = 60

class SkillEvolutionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.connection_heartbeats: Dict[WebSocket, float] = {}
        self._heartbeat_task: Optional[asyncio.Task] = None
        self._evolution_state: Dict[str, Any] = {
            "is_running": False,
            "current_phase": EvolutionPhase.INITIALIZATION.value,
            "last_evolution": None,
            "total_evolutions": 0,
            "success_rate": 0.0,
            "active_monitors": [],
            "evolution_type": None,
            "progress": 0.0,
            "started_at": None,
            "estimated_completion": None
        }
        self._evolution_history: List[Dict[str, Any]] = []
        self._paused_state: Optional[Dict[str, Any]] = None
        self._rollback_history: List[Dict[str, Any]] = []

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

    def add_history_item(self, item: Dict[str, Any]):
        self._evolution_history.append(item)
        if len(self._evolution_history) > 1000:
            self._evolution_history = self._evolution_history[-1000:]

    def get_history(self, skip: int = 0, limit: int = 20) -> List[Dict[str, Any]]:
        return self._evolution_history[skip:skip + limit]

    def save_paused_state(self, state: Dict[str, Any]) -> str:
        state_id = f"pause_{int(time.time() * 1000)}"
        self._paused_state = {"id": state_id, "state": state, "saved_at": datetime.now()}
        return state_id

    def get_paused_state(self) -> Optional[Dict[str, Any]]:
        return self._paused_state

    def clear_paused_state(self):
        self._paused_state = None

skill_evolution_manager = SkillEvolutionManager()

def _generate_mock_status() -> SkillEvolutionStatus:
    return SkillEvolutionStatus(
        is_running=False,
        current_phase=EvolutionPhase.INITIALIZATION.value,
        last_evolution=datetime.now() - timedelta(hours=6),
        total_evolutions=156,
        success_rate=94.87,
        active_monitors=["skill_health", "performance", "resource_usage", "error_rate"],
        evolution_type=None,
        progress=0.0,
        started_at=None,
        estimated_completion=None
    )

def _generate_mock_content_status() -> ContentStatusListResponse:
    monitors = [
        ContentStatusResponse(
            monitor_id="skill_health_001",
            status=ContentMonitorStatus.ACTIVE,
            last_check=datetime.now() - timedelta(minutes=5),
            items_monitored=45,
            alerts_count=2,
            health_score=92.5,
            details={"avg_response_time": 1.2, "error_rate": 0.02}
        ),
        ContentStatusResponse(
            monitor_id="performance_001",
            status=ContentMonitorStatus.ACTIVE,
            last_check=datetime.now() - timedelta(minutes=3),
            items_monitored=128,
            alerts_count=0,
            health_score=98.2,
            details={"cpu_usage": 45.5, "memory_usage": 62.3}
        ),
        ContentStatusResponse(
            monitor_id="resource_usage_001",
            status=ContentMonitorStatus.ACTIVE,
            last_check=datetime.now() - timedelta(minutes=1),
            items_monitored=32,
            alerts_count=1,
            health_score=88.0,
            details={"disk_usage": 75.2, "network_io": 1024}
        ),
        ContentStatusResponse(
            monitor_id="error_rate_001",
            status=ContentMonitorStatus.ACTIVE,
            last_check=datetime.now() - timedelta(minutes=2),
            items_monitored=256,
            alerts_count=3,
            health_score=85.5,
            details={"error_count_1h": 12, "warning_count_1h": 45}
        )
    ]
    
    return ContentStatusListResponse(
        total_monitors=4,
        active_monitors=4,
        monitors=monitors,
        overall_health=91.05
    )

def _generate_mock_health_status() -> SkillHealthStatus:
    components = [
        HealthCheckResult(
            component="evolution_engine",
            status=HealthStatus.HEALTHY,
            message="演化引擎运行正常",
            details={"uptime_hours": 168, "last_evolution": "6 hours ago"},
            last_check=datetime.now()
        ),
        HealthCheckResult(
            component="monitoring_system",
            status=HealthStatus.HEALTHY,
            message="监控系统运行正常",
            details={"active_monitors": 4, "alerts_pending": 6},
            last_check=datetime.now()
        ),
        HealthCheckResult(
            component="rollback_manager",
            status=HealthStatus.HEALTHY,
            message="回滚管理器就绪",
            details={"available_rollbacks": 12, "last_rollback": "2 days ago"},
            last_check=datetime.now()
        ),
        HealthCheckResult(
            component="database",
            status=HealthStatus.DEGRADED,
            message="数据库响应稍慢",
            details={"avg_query_time_ms": 150, "connection_pool": "80%"},
            last_check=datetime.now()
        ),
        HealthCheckResult(
            component="cache",
            status=HealthStatus.HEALTHY,
            message="缓存系统运行正常",
            details={"hit_rate": "95.5%", "memory_usage": "45%"},
            last_check=datetime.now()
        )
    ]
    
    return SkillHealthStatus(
        overall_status=HealthStatus.HEALTHY,
        components=components,
        uptime_seconds=604800,
        last_evolution=datetime.now() - timedelta(hours=6),
        pending_operations=3,
        error_count_24h=8
    )

def _generate_mock_history(skip: int, limit: int) -> EvolutionHistoryListResponse:
    items = []
    for i in range(limit):
        idx = skip + i
        event_id = f"evt_{int(time.time())}_{idx}"
        evolution_type = list(EvolutionType)[idx % len(EvolutionType)]
        trigger_type = list(TriggerType)[idx % len(TriggerType)]
        status = EvolutionStatus.COMPLETED if idx % 5 != 0 else EvolutionStatus.FAILED
        
        items.append(EvolutionHistoryItem(
            event_id=event_id,
            timestamp=datetime.now() - timedelta(days=idx + 1, hours=idx),
            evolution_type=evolution_type,
            trigger_type=trigger_type,
            status=status,
            duration_ms=3600000 + idx * 10000,
            changes=[
                f"优化技能参数 #{idx + 1}",
                f"更新工作流配置 #{idx + 1}",
                f"调整资源分配 #{idx + 1}"
            ],
            summary=f"演化事件 #{idx + 1} - {evolution_type.value}",
            metrics_before={"performance": 80 + idx, "efficiency": 75 + idx},
            metrics_after={"performance": 85 + idx, "efficiency": 80 + idx} if status == EvolutionStatus.COMPLETED else {},
            rollback_available=status == EvolutionStatus.COMPLETED
        ))
    
    total = 156
    return EvolutionHistoryListResponse(
        total=total,
        items=items,
        page=skip // limit + 1,
        page_size=limit,
        total_pages=(total + limit - 1) // limit
    )

def _generate_mock_event_detail(event_id: str) -> EvolutionEventDetail:
    return EvolutionEventDetail(
        event_id=event_id,
        timestamp=datetime.now() - timedelta(hours=6),
        evolution_type=EvolutionType.SKILL_OPTIMIZATION,
        trigger_type=TriggerType.AUTOMATIC,
        status=EvolutionStatus.COMPLETED,
        duration_ms=3600000,
        phases=[
            {"name": "initialization", "duration_ms": 5000, "status": "completed"},
            {"name": "analysis", "duration_ms": 600000, "status": "completed"},
            {"name": "planning", "duration_ms": 300000, "status": "completed"},
            {"name": "execution", "duration_ms": 2400000, "status": "completed"},
            {"name": "validation", "duration_ms": 180000, "status": "completed"},
            {"name": "deployment", "duration_ms": 115000, "status": "completed"}
        ],
        changes=[
            {"type": "parameter_update", "target": "skill_A", "before": {"threshold": 0.8}, "after": {"threshold": 0.85}},
            {"type": "workflow_update", "target": "workflow_B", "before": {"parallelism": 4}, "after": {"parallelism": 6}},
            {"type": "resource_update", "target": "agent_pool", "before": {"max_agents": 10}, "after": {"max_agents": 15}}
        ],
        metrics_before={"performance": 80, "efficiency": 75, "error_rate": 0.05},
        metrics_after={"performance": 85, "efficiency": 80, "error_rate": 0.03},
        errors=[],
        rollback_info={"available": True, "snapshot_id": "snap_001", "created_at": datetime.now().isoformat()},
        related_events=["evt_prev_001", "evt_prev_002"]
    )

def _generate_mock_statistics() -> EvolutionStatistics:
    return EvolutionStatistics(
        total_evolutions=156,
        successful_evolutions=148,
        failed_evolutions=8,
        rolled_back_evolutions=3,
        average_duration_ms=3420500,
        success_rate=94.87,
        evolution_by_type={
            "skill_optimization": 45,
            "workflow_adaptation": 32,
            "resource_rebalance": 28,
            "knowledge_update": 25,
            "performance_tuning": 18,
            "model_upgrade": 5,
            "config_update": 3
        },
        evolution_by_trigger={
            "automatic": 98,
            "manual": 32,
            "scheduled": 18,
            "threshold_based": 8
        },
        last_24h_count=4,
        last_7d_count=23,
        last_30d_count=89,
        most_active_period="02:00-04:00",
        average_changes_per_evolution=3.5
    )

def _generate_mock_report() -> EvolutionReport:
    return EvolutionReport(
        report_id=f"report_{int(time.time())}",
        generated_at=datetime.now(),
        period_start=datetime.now() - timedelta(days=7),
        period_end=datetime.now(),
        summary={
            "total_evolutions": 23,
            "success_rate": 95.6,
            "average_duration_minutes": 57,
            "most_common_type": "skill_optimization"
        },
        evolution_statistics=_generate_mock_statistics(),
        health_trends=[
            {"date": (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d"), "health_score": 90 + i * 0.5}
            for i in range(7, 0, -1)
        ],
        recommendations=[
            "建议增加自动化演化频率以提高系统适应性",
            "考虑在低峰期执行资源重平衡操作",
            "建议更新知识库以提升决策准确性"
        ],
        detailed_events=_generate_mock_history(0, 10).items
    )

def _generate_mock_call_chain(event_id: str) -> CallChainResponse:
    root = CallChainNode(
        node_id="root_001",
        node_type="evolution_trigger",
        name="Skill Evolution Trigger",
        status="completed",
        duration_ms=3600000,
        children=[
            CallChainNode(
                node_id="node_001",
                node_type="phase",
                name="Analysis Phase",
                status="completed",
                duration_ms=600000,
                children=[
                    CallChainNode(
                        node_id="node_001_001",
                        node_type="skill_call",
                        name="analyze_performance",
                        status="completed",
                        duration_ms=120000,
                        metadata={"skill": "performance_analyzer", "input_size": 1024}
                    ),
                    CallChainNode(
                        node_id="node_001_002",
                        node_type="skill_call",
                        name="identify_bottlenecks",
                        status="completed",
                        duration_ms=180000,
                        metadata={"skill": "bottleneck_detector", "issues_found": 5}
                    )
                ]
            ),
            CallChainNode(
                node_id="node_002",
                node_type="phase",
                name="Planning Phase",
                status="completed",
                duration_ms=300000,
                children=[
                    CallChainNode(
                        node_id="node_002_001",
                        node_type="skill_call",
                        name="generate_plan",
                        status="completed",
                        duration_ms=150000,
                        metadata={"skill": "planner", "plan_steps": 8}
                    )
                ]
            ),
            CallChainNode(
                node_id="node_003",
                node_type="phase",
                name="Execution Phase",
                status="completed",
                duration_ms=2400000,
                children=[
                    CallChainNode(
                        node_id="node_003_001",
                        node_type="skill_call",
                        name="apply_changes",
                        status="completed",
                        duration_ms=1200000,
                        metadata={"skill": "executor", "changes_applied": 12}
                    ),
                    CallChainNode(
                        node_id="node_003_002",
                        node_type="skill_call",
                        name="validate_changes",
                        status="completed",
                        duration_ms=600000,
                        metadata={"skill": "validator", "validation_passed": True}
                    )
                ]
            )
        ]
    )
    
    return CallChainResponse(
        event_id=event_id,
        root_node=root,
        total_nodes=8,
        max_depth=3,
        total_duration_ms=3600000
    )

async def _execute_evolution_task(trigger_id: str, request: TriggerEvolutionRequest):
    skill_evolution_manager.update_state(
        is_running=True,
        current_phase=EvolutionPhase.ANALYSIS.value,
        evolution_type=request.evolution_type,
        progress=0.0,
        started_at=datetime.now()
    )
    
    await skill_evolution_manager.broadcast_evolution_update("evolution_started", {
        "trigger_id": trigger_id,
        "evolution_type": request.evolution_type.value,
        "reason": request.reason
    })
    
    phases = [
        (EvolutionPhase.ANALYSIS, 15),
        (EvolutionPhase.PLANNING, 30),
        (EvolutionPhase.EXECUTION, 60),
        (EvolutionPhase.VALIDATION, 80),
        (EvolutionPhase.DEPLOYMENT, 95),
        (EvolutionPhase.CLEANUP, 100)
    ]
    
    for phase, progress in phases:
        await asyncio.sleep(2)
        skill_evolution_manager.update_state(
            current_phase=phase.value,
            progress=progress
        )
        await skill_evolution_manager.broadcast_evolution_update("evolution_progress", {
            "trigger_id": trigger_id,
            "phase": phase.value,
            "progress": progress
        })
    
    current_state = skill_evolution_manager.get_state()
    total = current_state.get("total_evolutions", 0) + 1
    success_rate = (current_state.get("success_rate", 0) * (total - 1) + 100) / total
    
    skill_evolution_manager.update_state(
        is_running=False,
        current_phase=EvolutionPhase.INITIALIZATION.value,
        progress=0.0,
        last_evolution=datetime.now(),
        total_evolutions=total,
        success_rate=success_rate,
        evolution_type=None,
        started_at=None
    )
    
    skill_evolution_manager.add_history_item({
        "event_id": trigger_id,
        "timestamp": datetime.now(),
        "evolution_type": request.evolution_type.value,
        "trigger_type": TriggerType.API_TRIGGERED.value,
        "status": EvolutionStatus.COMPLETED.value,
        "duration_ms": 12000,
        "changes": ["参数优化", "配置更新", "资源调整"]
    })
    
    await skill_evolution_manager.broadcast_evolution_update("evolution_completed", {
        "trigger_id": trigger_id,
        "evolution_type": request.evolution_type.value,
        "duration_ms": 12000
    })

async def _execute_rollback(rollback_id: str, request: RollbackRequest):
    skill_evolution_manager.update_state(
        is_running=True,
        current_phase=EvolutionPhase.EXECUTION.value,
        evolution_type=EvolutionType.CONFIG_UPDATE,
        progress=0.0,
        started_at=datetime.now()
    )
    
    await skill_evolution_manager.broadcast_evolution_update("rollback_started", {
        "rollback_id": rollback_id,
        "target_event_id": request.event_id,
        "reason": request.reason
    })
    
    progress_stages = [25, 50, 75, 100]
    for progress in progress_stages:
        await asyncio.sleep(1)
        skill_evolution_manager.update_state(progress=progress)
        await skill_evolution_manager.broadcast_evolution_update("rollback_progress", {
            "rollback_id": rollback_id,
            "progress": progress
        })
    
    skill_evolution_manager.update_state(
        is_running=False,
        current_phase=EvolutionPhase.INITIALIZATION.value,
        progress=0.0,
        evolution_type=None,
        started_at=None
    )
    
    await skill_evolution_manager.broadcast_evolution_update("rollback_completed", {
        "rollback_id": rollback_id,
        "target_event_id": request.event_id,
        "status": "success"
    })

@router.get(
    "/status",
    response_model=SkillEvolutionStatus,
    summary="获取技能演化状态",
    description="获取当前技能演化系统的运行状态，包括演化进度、成功率等关键指标"
)
async def get_skill_evolution_status(db: Session = Depends(get_db)):
    cache_key = "skill_evolution:status"
    cached = cache_service.get_json(cache_key)
    if cached:
        return SkillEvolutionStatus(**cached)
    
    result = _generate_mock_status()
    cache_service.set_json(cache_key, result.model_dump(), ttl=30)
    
    return result

@router.get(
    "/content-status",
    response_model=ContentStatusListResponse,
    summary="获取内容监控状态",
    description="获取所有内容监控器的状态信息，包括健康分数、告警数量等"
)
async def get_content_status(db: Session = Depends(get_db)):
    cache_key = "skill_evolution:content_status"
    cached = cache_service.get_json(cache_key)
    if cached:
        return ContentStatusListResponse(**cached)
    
    result = _generate_mock_content_status()
    cache_service.set_json(cache_key, result.model_dump(), ttl=60)
    
    return result

@router.get(
    "/health",
    response_model=SkillHealthStatus,
    summary="获取技能健康状态",
    description="获取技能演化系统各组件的健康检查结果"
)
async def get_skill_health_status(db: Session = Depends(get_db)):
    cache_key = "skill_evolution:health"
    cached = cache_service.get_json(cache_key)
    if cached:
        return SkillHealthStatus(**cached)
    
    result = _generate_mock_health_status()
    cache_service.set_json(cache_key, result.model_dump(), ttl=30)
    
    return result

@router.get(
    "/history",
    response_model=EvolutionHistoryListResponse,
    summary="获取演化历史列表",
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
    cache_key = f"skill_evolution:history:{skip}:{limit}:{evolution_type}:{status}:{start_date}:{end_date}"
    cached = cache_service.get_json(cache_key)
    if cached:
        return EvolutionHistoryListResponse(**cached)
    
    result = _generate_mock_history(skip, limit)
    cache_service.set_json(cache_key, result.model_dump(), ttl=60)
    
    return result

@router.get(
    "/history/{event_id}",
    response_model=EvolutionEventDetail,
    summary="获取单个演化事件详情",
    description="获取指定演化事件的详细信息，包括各阶段详情、变更内容等"
)
async def get_evolution_event_detail(
    event_id: str,
    db: Session = Depends(get_db)
):
    cache_key = f"skill_evolution:event:{event_id}"
    cached = cache_service.get_json(cache_key)
    if cached:
        return EvolutionEventDetail(**cached)
    
    result = _generate_mock_event_detail(event_id)
    cache_service.set_json(cache_key, result.model_dump(), ttl=300)
    
    return result

@router.get(
    "/statistics",
    response_model=EvolutionStatistics,
    summary="获取演化统计数据",
    description="获取演化系统的统计数据，包括成功率、按类型统计等"
)
async def get_evolution_statistics(db: Session = Depends(get_db)):
    cache_key = "skill_evolution:statistics"
    cached = cache_service.get_json(cache_key)
    if cached:
        return EvolutionStatistics(**cached)
    
    result = _generate_mock_statistics()
    cache_service.set_json(cache_key, result.model_dump(), ttl=300)
    
    return result

@router.post(
    "/trigger",
    response_model=TriggerEvolutionResponse,
    summary="手动触发演化",
    description="手动触发一次技能演化过程"
)
async def trigger_evolution(
    request: TriggerEvolutionRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    current_state = skill_evolution_manager.get_state()
    
    if current_state.get("is_running") and not request.force:
        raise HTTPException(
            status_code=409,
            detail="演化正在进行中，请等待完成或使用 force=true 强制执行"
        )
    
    trigger_id = f"trigger_{int(time.time() * 1000)}"
    
    if request.dry_run:
        return TriggerEvolutionResponse(
            trigger_id=trigger_id,
            evolution_type=request.evolution_type,
            status=EvolutionStatus.IDLE,
            message="模拟运行完成，未执行实际变更",
            estimated_duration_ms=0,
            queued_position=None
        )
    
    background_tasks.add_task(_execute_evolution_task, trigger_id, request)
    
    return TriggerEvolutionResponse(
        trigger_id=trigger_id,
        evolution_type=request.evolution_type,
        status=EvolutionStatus.RUNNING,
        message="演化已触发，正在后台执行",
        estimated_duration_ms=600000,
        queued_position=1
    )

@router.post(
    "/pause",
    response_model=PauseEvolutionResponse,
    summary="暂停演化",
    description="暂停当前正在进行的演化过程"
)
async def pause_evolution(
    request: PauseEvolutionRequest,
    db: Session = Depends(get_db)
):
    current_state = skill_evolution_manager.get_state()
    
    if not current_state.get("is_running"):
        raise HTTPException(
            status_code=400,
            detail="当前没有正在进行的演化"
        )
    
    saved_state_id = None
    if request.save_state:
        saved_state_id = skill_evolution_manager.save_paused_state(current_state)
    
    skill_evolution_manager.update_state(is_running=False)
    
    await skill_evolution_manager.broadcast_evolution_update("evolution_paused", {
        "reason": request.reason,
        "saved_state_id": saved_state_id
    })
    
    return PauseEvolutionResponse(
        success=True,
        message="演化已暂停",
        saved_state_id=saved_state_id,
        paused_at=datetime.now()
    )

@router.post(
    "/resume",
    response_model=ResumeEvolutionResponse,
    summary="恢复演化",
    description="恢复已暂停的演化过程"
)
async def resume_evolution(
    request: ResumeEvolutionRequest,
    db: Session = Depends(get_db)
):
    paused_state = skill_evolution_manager.get_paused_state()
    
    if not paused_state and request.continue_from_checkpoint:
        raise HTTPException(
            status_code=400,
            detail="没有找到可恢复的演化状态"
        )
    
    if paused_state:
        skill_evolution_manager.update_state(
            is_running=True,
            **{k: v for k, v in paused_state["state"].items() if k != "is_running"}
        )
        skill_evolution_manager.clear_paused_state()
    else:
        skill_evolution_manager.update_state(is_running=True)
    
    current_state = skill_evolution_manager.get_state()
    
    await skill_evolution_manager.broadcast_evolution_update("evolution_resumed", {
        "state_id": request.state_id,
        "continue_from_checkpoint": request.continue_from_checkpoint
    })
    
    return ResumeEvolutionResponse(
        success=True,
        message="演化已恢复",
        resumed_at=datetime.now(),
        current_phase=current_state.get("current_phase", EvolutionPhase.INITIALIZATION.value)
    )

@router.post(
    "/rollback",
    response_model=RollbackResponse,
    summary="执行回滚",
    description="将系统回滚到指定演化事件之前的状态"
)
async def execute_rollback(
    request: RollbackRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    current_state = skill_evolution_manager.get_state()
    
    if current_state.get("is_running") and not request.force:
        raise HTTPException(
            status_code=409,
            detail="演化正在进行中，请等待完成或使用 force=true 强制回滚"
        )
    
    rollback_id = f"rollback_{int(time.time() * 1000)}"
    backup_id = f"backup_{int(time.time() * 1000)}" if request.create_backup else None
    
    background_tasks.add_task(_execute_rollback, rollback_id, request)
    
    return RollbackResponse(
        rollback_id=rollback_id,
        target_event_id=request.event_id,
        status=EvolutionStatus.RUNNING,
        message="回滚已触发，正在后台执行",
        estimated_duration_ms=300000,
        backup_id=backup_id
    )

@router.get(
    "/report",
    response_model=EvolutionReport,
    summary="生成演化报告",
    description="生成指定时间范围内的演化报告"
)
async def generate_evolution_report(
    start_date: Optional[datetime] = Query(None, description="报告开始日期"),
    end_date: Optional[datetime] = Query(None, description="报告结束日期"),
    db: Session = Depends(get_db)
):
    if not start_date:
        start_date = datetime.now() - timedelta(days=7)
    if not end_date:
        end_date = datetime.now()
    
    cache_key = f"skill_evolution:report:{start_date}:{end_date}"
    cached = cache_service.get_json(cache_key)
    if cached:
        return EvolutionReport(**cached)
    
    result = _generate_mock_report()
    cache_service.set_json(cache_key, result.model_dump(), ttl=600)
    
    return result

@router.get(
    "/export",
    summary="导出演化数据",
    description="导出演化历史数据，支持JSON和CSV格式"
)
async def export_evolution_data(
    format: ExportFormat = Query(ExportFormat.JSON, description="导出格式"),
    start_date: Optional[datetime] = Query(None, description="开始日期"),
    end_date: Optional[datetime] = Query(None, description="结束日期"),
    include_metrics: bool = Query(True, description="是否包含指标"),
    include_changes: bool = Query(True, description="是否包含变更详情"),
    db: Session = Depends(get_db)
):
    history = _generate_mock_history(0, 100)
    
    if format == ExportFormat.JSON:
        content = json.dumps(history.model_dump(), ensure_ascii=False, indent=2, default=str)
        return StreamingResponse(
            iter([content]),
            media_type="application/json",
            headers={
                "Content-Disposition": f"attachment; filename=evolution_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            }
        )
    elif format == ExportFormat.CSV:
        output = io.StringIO()
        writer = csv.writer(output)
        
        headers = ["event_id", "timestamp", "evolution_type", "trigger_type", "status", "duration_ms"]
        if include_changes:
            headers.append("changes")
        if include_metrics:
            headers.extend(["metrics_before", "metrics_after"])
        
        writer.writerow(headers)
        
        for item in history.items:
            row = [
                item.event_id,
                item.timestamp.isoformat(),
                item.evolution_type.value,
                item.trigger_type.value,
                item.status.value,
                item.duration_ms
            ]
            if include_changes:
                row.append("; ".join(item.changes))
            if include_metrics:
                row.append(json.dumps(item.metrics_before))
                row.append(json.dumps(item.metrics_after))
            writer.writerow(row)
        
        output.seek(0)
        return StreamingResponse(
            iter([output.getvalue()]),
            media_type="text/csv",
            headers={
                "Content-Disposition": f"attachment; filename=evolution_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            }
        )
    else:
        raise HTTPException(
            status_code=400,
            detail=f"不支持的导出格式: {format}"
        )

@router.get(
    "/call-chain/{event_id}",
    response_model=CallChainResponse,
    summary="获取调用链",
    description="获取指定演化事件的调用链信息"
)
async def get_evolution_call_chain(
    event_id: str,
    db: Session = Depends(get_db)
):
    cache_key = f"skill_evolution:call_chain:{event_id}"
    cached = cache_service.get_json(cache_key)
    if cached:
        return CallChainResponse(**cached)
    
    result = _generate_mock_call_chain(event_id)
    cache_service.set_json(cache_key, result.model_dump(), ttl=300)
    
    return result

@router.websocket("/ws")
async def skill_evolution_websocket_endpoint(websocket: WebSocket):
    await skill_evolution_manager.connect(websocket)
    try:
        current_state = skill_evolution_manager.get_state()
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
                    skill_evolution_manager.update_heartbeat(websocket)
                    await websocket.send_json({
                        "type": "pong",
                        "timestamp": time.time()
                    })
                elif message.get("type") == "heartbeat":
                    skill_evolution_manager.update_heartbeat(websocket)
                    await websocket.send_json({
                        "type": "heartbeat_ack",
                        "timestamp": time.time()
                    })
                elif message.get("type") == "get_status":
                    current_state = skill_evolution_manager.get_state()
                    await websocket.send_json({
                        "type": "status_update",
                        "data": current_state,
                        "timestamp": datetime.now().isoformat()
                    })
                elif message.get("type") == "get_history":
                    history = skill_evolution_manager.get_history(
                        message.get("skip", 0),
                        message.get("limit", 20)
                    )
                    await websocket.send_json({
                        "type": "history_update",
                        "data": history,
                        "timestamp": datetime.now().isoformat()
                    })
            except json.JSONDecodeError:
                await websocket.send_json({"error": "Invalid JSON"})
    except WebSocketDisconnect:
        skill_evolution_manager.disconnect(websocket)

class CyclePhase(str, Enum):
    RED = "red"
    GREEN = "green"
    BLUE = "blue"
    REGRESSION = "regression"


class CycleStatus(str, Enum):
    COMPLETED = "completed"
    RUNNING = "running"
    FAILED = "failed"
    PENDING = "pending"


class CurrentCycleInfo(BaseModel):
    id: str = Field(..., description="周期ID")
    phase: CyclePhase = Field(..., description="当前阶段")
    progress: float = Field(..., description="进度 (0-100)", ge=0, le=100)
    started_at: datetime = Field(..., description="开始时间")
    estimated_completion: Optional[datetime] = Field(None, description="预计完成时间")

    class Config:
        from_attributes = True


class CycleHistoryItem(BaseModel):
    id: str = Field(..., description="周期ID")
    status: CycleStatus = Field(..., description="状态")
    duration: Optional[str] = Field(None, description="持续时间")
    completed_at: Optional[datetime] = Field(None, description="完成时间")

    class Config:
        from_attributes = True


class SelfIterationInfo(BaseModel):
    enabled: bool = Field(..., description="是否启用")
    last_run: Optional[datetime] = Field(None, description="上次运行时间")
    trigger: str = Field(..., description="触发方式")
    total_iterations: int = Field(0, description="总迭代次数")
    success_rate: float = Field(0.0, description="成功率")

    class Config:
        from_attributes = True


class SelfOptimizationInfo(BaseModel):
    enabled: bool = Field(..., description="是否启用")
    last_optimization: Optional[datetime] = Field(None, description="上次优化时间")
    strategies_applied: int = Field(0, description="已应用策略数")
    improvement_percent: float = Field(0.0, description="改进百分比")

    class Config:
        from_attributes = True


class SelfRepairInfo(BaseModel):
    enabled: bool = Field(..., description="是否启用")
    issues_fixed: int = Field(0, description="修复问题数")
    last_repair: Optional[datetime] = Field(None, description="上次修复时间")
    avg_repair_time_minutes: float = Field(0.0, description="平均修复时间（分钟）")

    class Config:
        from_attributes = True


class SelfImprovementInfo(BaseModel):
    enabled: bool = Field(..., description="是否启用")
    knowledge_items: int = Field(0, description="知识条目数")
    last_learning: Optional[datetime] = Field(None, description="上次学习时间")
    improvement_areas: List[str] = Field(default_factory=list, description="改进领域")

    class Config:
        from_attributes = True


class CapabilitiesInfo(BaseModel):
    self_iteration: SelfIterationInfo = Field(..., description="自迭代能力")
    self_optimization: SelfOptimizationInfo = Field(..., description="自优化能力")
    self_repair: SelfRepairInfo = Field(..., description="自修复能力")
    self_improvement: SelfImprovementInfo = Field(..., description="自改进能力")

    class Config:
        from_attributes = True


class QualityTrendItem(BaseModel):
    date: str = Field(..., description="日期")
    score: float = Field(..., description="质量分数")


class EvolutionSystemStatus(BaseModel):
    current_cycle: CurrentCycleInfo = Field(..., description="当前周期信息")
    cycle_history: List[CycleHistoryItem] = Field(default_factory=list, description="历史周期")
    capabilities: CapabilitiesInfo = Field(..., description="能力状态")
    quality_trend: List[QualityTrendItem] = Field(default_factory=list, description="质量趋势")
    next_scheduled_cycle: Optional[datetime] = Field(None, description="下次计划周期")
    system_uptime_seconds: int = Field(0, description="系统运行时间（秒）")
    active_tasks: int = Field(0, description="活跃任务数")

    class Config:
        from_attributes = True


def _generate_evolution_system_status() -> EvolutionSystemStatus:
    now = datetime.now()

    return EvolutionSystemStatus(
        current_cycle=CurrentCycleInfo(
            id=f"cycle_{int(time.time())}",
            phase=CyclePhase.GREEN,
            progress=65.5,
            started_at=now - timedelta(hours=2),
            estimated_completion=now + timedelta(hours=1)
        ),
        cycle_history=[
            CycleHistoryItem(
                id=f"cycle_{int(time.time()) - 86400 * i}",
                status=CycleStatus.COMPLETED if i % 4 != 0 else (CycleStatus.FAILED if i % 7 == 0 else CycleStatus.RUNNING),
                duration=f"{random.randint(3, 8)}h {random.randint(0, 59)}m",
                completed_at=now - timedelta(days=i) if i > 0 else None
            )
            for i in range(10)
        ],
        capabilities=CapabilitiesInfo(
            self_iteration=SelfIterationInfo(
                enabled=True,
                last_run=now - timedelta(hours=6),
                trigger="quality_based",
                total_iterations=156,
                success_rate=94.87
            ),
            self_optimization=SelfOptimizationInfo(
                enabled=True,
                last_optimization=now - timedelta(hours=12),
                strategies_applied=3,
                improvement_percent=12.5
            ),
            self_repair=SelfRepairInfo(
                enabled=True,
                issues_fixed=5,
                last_repair=now - timedelta(days=1),
                avg_repair_time_minutes=15.3
            ),
            self_improvement=SelfImprovementInfo(
                enabled=True,
                knowledge_items=42,
                last_learning=now - timedelta(hours=3),
                improvement_areas=["代码质量", "性能优化", "错误处理"]
            )
        ),
        quality_trend=[
            QualityTrendItem(
                date=(now - timedelta(days=i)).strftime("%Y-%m-%d"),
                score=round(87 - i * 0.5 + random.uniform(-2, 2), 1)
            )
            for i in range(30, 0, -1)
        ],
        next_scheduled_cycle=now + timedelta(hours=4),
        system_uptime_seconds=604800,
        active_tasks=3
    )


@router.get(
    "/evolution/status",
    response_model=EvolutionSystemStatus,
    summary="获取演化系统完整状态",
    description="返回演化系统的当前状态总览，包括当前周期、历史记录、能力状态、质量趋势等完整信息"
)
async def get_evolution_system_status(db: Session = Depends(get_db)):
    cache_key = "evolution:system_status"
    cached = cache_service.get_json(cache_key)
    if cached:
        return EvolutionSystemStatus(**cached)

    result = _generate_evolution_system_status()
    cache_service.set_json(cache_key, result.model_dump(), ttl=30)

    return result


@router.get(
    "/evolution/status/capabilities",
    response_model=CapabilitiesInfo,
    summary="获取系统能力状态",
    description="获取系统四大能力的详细状态：自迭代、自优化、自修复、自改进"
)
async def get_capabilities_status(db: Session = Depends(get_db)):
    cache_key = "evolution:capabilities"
    cached = cache_service.get_json(cache_key)
    if cached:
        return CapabilitiesInfo(**cached)

    result = _generate_evolution_system_status().capabilities
    cache_service.set_json(cache_key, result.model_dump(), ttl=60)

    return result


@router.get(
    "/evolution/status/cycles",
    summary="获取周期历史",
    description="获取演化周期的历史记录列表"
)
async def get_cycle_history(
    limit: int = Query(20, description="返回数量限制", ge=1, le=100),
    db: Session = Depends(get_db)
):
    status = _generate_evolution_system_status()
    return {
        "total": len(status.cycle_history),
        "cycles": status.cycle_history[:limit]
    }


def get_skill_evolution_manager() -> SkillEvolutionManager:
    return skill_evolution_manager
