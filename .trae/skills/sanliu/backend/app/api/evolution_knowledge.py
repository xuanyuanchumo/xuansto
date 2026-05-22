from fastapi import APIRouter, Depends, HTTPException, Query, WebSocket, WebSocketDisconnect, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime, timedelta
from enum import Enum
import json
import time
import asyncio

from ..models.base import get_db
from ..services.cache import cache_service

router = APIRouter()

class PatternType(str, Enum):
    OPTIMIZATION = "optimization"
    REFACTORING = "refactoring"
    MIGRATION = "migration"
    SCALING = "scaling"
    DEPRECATION = "deprecation"
    ENHANCEMENT = "enhancement"

class PatternStatus(str, Enum):
    ACTIVE = "active"
    DEPRECATED = "deprecated"
    EXPERIMENTAL = "experimental"
    RECOMMENDED = "recommended"

class RecommendationPriority(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

class EvolutionPredictionStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"

class EvolutionTriggerStatus(str, Enum):
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"

class EvolutionPattern(BaseModel):
    pattern_id: str = Field(..., description="模式ID")
    name: str = Field(..., description="模式名称")
    type: PatternType = Field(..., description="模式类型")
    status: PatternStatus = Field(..., description="模式状态")
    description: str = Field(..., description="描述")
    applicability: List[str] = Field(default_factory=list, description="适用场景")
    prerequisites: List[str] = Field(default_factory=list, description="前置条件")
    steps: List[Dict[str, Any]] = Field(default_factory=list, description="执行步骤")
    expected_outcomes: List[str] = Field(default_factory=list, description="预期结果")
    risks: List[str] = Field(default_factory=list, description="风险")
    success_rate: float = Field(0.0, description="成功率")
    usage_count: int = Field(0, description="使用次数")
    last_used: Optional[datetime] = Field(None, description="上次使用时间")
    created_at: datetime = Field(default_factory=datetime.now, description="创建时间")
    tags: List[str] = Field(default_factory=list, description="标签")

    class Config:
        from_attributes = True

class PatternListResponse(BaseModel):
    total: int = Field(0, description="总数")
    items: List[EvolutionPattern] = Field(default_factory=list, description="模式列表")
    page: int = Field(1, description="当前页")
    page_size: int = Field(20, description="每页大小")

class EvolutionRecommendation(BaseModel):
    recommendation_id: str = Field(..., description="推荐ID")
    pattern_id: str = Field(..., description="关联模式ID")
    pattern_name: str = Field(..., description="模式名称")
    priority: RecommendationPriority = Field(..., description="优先级")
    confidence: float = Field(..., description="置信度", ge=0, le=1)
    reason: str = Field(..., description="推荐原因")
    expected_benefit: str = Field(..., description="预期收益")
    estimated_effort: str = Field(..., description="预估工作量")
    affected_components: List[str] = Field(default_factory=list, description="影响组件")
    prerequisites_met: bool = Field(True, description="前置条件是否满足")
    missing_prerequisites: List[str] = Field(default_factory=list, description="缺失的前置条件")
    created_at: datetime = Field(default_factory=datetime.now, description="创建时间")

    class Config:
        from_attributes = True

class RecommendationListResponse(BaseModel):
    total: int = Field(0, description="总数")
    items: List[EvolutionRecommendation] = Field(default_factory=list, description="推荐列表")

class PredictionRequest(BaseModel):
    pattern_id: str = Field(..., description="模式ID")
    target_components: Optional[List[str]] = Field(None, description="目标组件")
    parameters: Optional[Dict[str, Any]] = Field(default_factory=dict, description="参数")
    simulation_depth: str = Field("standard", description="模拟深度: quick, standard, deep")

class PredictionResult(BaseModel):
    prediction_id: str = Field(..., description="预测ID")
    pattern_id: str = Field(..., description="模式ID")
    status: EvolutionPredictionStatus = Field(..., description="状态")
    predicted_outcomes: Dict[str, Any] = Field(default_factory=dict, description="预测结果")
    performance_impact: Dict[str, float] = Field(default_factory=dict, description="性能影响")
    risk_assessment: Dict[str, Any] = Field(default_factory=dict, description="风险评估")
    confidence_score: float = Field(0.0, description="置信度分数")
    simulation_duration_ms: int = Field(0, description="模拟耗时")
    recommendations: List[str] = Field(default_factory=list, description="建议")
    warnings: List[str] = Field(default_factory=list, description="警告")
    created_at: datetime = Field(default_factory=datetime.now, description="创建时间")

    class Config:
        from_attributes = True

class EvolutionState(str, Enum):
    IDLE = "idle"
    ANALYZING = "analyzing"
    PLANNING = "planning"
    EXECUTING = "executing"
    VALIDATING = "validating"
    COMPLETED = "completed"
    FAILED = "failed"

class EvolutionStateResponse(BaseModel):
    state: EvolutionState = Field(..., description="当前状态")
    current_operation: Optional[str] = Field(None, description="当前操作")
    progress: float = Field(0.0, description="进度", ge=0, le=100)
    started_at: Optional[datetime] = Field(None, description="开始时间")
    estimated_completion: Optional[datetime] = Field(None, description="预计完成时间")
    current_pattern: Optional[str] = Field(None, description="当前模式")
    completed_steps: List[str] = Field(default_factory=list, description="已完成步骤")
    pending_steps: List[str] = Field(default_factory=list, description="待完成步骤")
    errors: List[str] = Field(default_factory=list, description="错误列表")
    metrics: Dict[str, Any] = Field(default_factory=dict, description="当前指标")

    class Config:
        from_attributes = True

class TriggerRequest(BaseModel):
    pattern_id: str = Field(..., description="模式ID")
    reason: str = Field(..., description="触发原因", min_length=1, max_length=500)
    components: Optional[List[str]] = Field(None, description="目标组件")
    parameters: Optional[Dict[str, Any]] = Field(default_factory=dict, description="参数")
    dry_run: bool = Field(False, description="是否模拟运行")
    force: bool = Field(False, description="是否强制执行")

class TriggerResponse(BaseModel):
    trigger_id: str = Field(..., description="触发ID")
    pattern_id: str = Field(..., description="模式ID")
    status: EvolutionTriggerStatus = Field(..., description="状态")
    message: str = Field(..., description="消息")
    estimated_duration_ms: Optional[int] = Field(None, description="预计耗时")

HEARTBEAT_INTERVAL = 30
HEARTBEAT_TIMEOUT = 60

class EvolutionKnowledgeManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.connection_heartbeats: Dict[WebSocket, float] = {}
        self._heartbeat_task: Optional[asyncio.Task] = None
        self._evolution_state: Dict[str, Any] = {
            "state": EvolutionState.IDLE,
            "current_operation": None,
            "progress": 0.0,
            "started_at": None,
            "current_pattern": None,
            "completed_steps": [],
            "pending_steps": [],
            "errors": [],
            "metrics": {}
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
    
    async def broadcast_state_update(self, event_type: str, data: Dict[str, Any]):
        await self.broadcast({
            "type": event_type,
            "data": data,
            "timestamp": datetime.now().isoformat()
        })
    
    def get_state(self) -> Dict[str, Any]:
        return self._evolution_state.copy()
    
    def update_state(self, **kwargs):
        self._evolution_state.update(kwargs)

evolution_knowledge_manager = EvolutionKnowledgeManager()

def _generate_mock_patterns() -> List[EvolutionPattern]:
    patterns = [
        EvolutionPattern(
            pattern_id="pattern_001",
            name="性能优化模式",
            type=PatternType.OPTIMIZATION,
            status=PatternStatus.RECOMMENDED,
            description="通过分析性能瓶颈并应用优化策略提升系统性能",
            applicability=["高延迟场景", "资源密集型任务", "并发瓶颈"],
            prerequisites=["性能监控已启用", "基准测试数据可用"],
            steps=[
                {"step": 1, "action": "性能分析", "description": "收集性能指标"},
                {"step": 2, "action": "瓶颈识别", "description": "识别性能瓶颈"},
                {"step": 3, "action": "优化实施", "description": "应用优化策略"},
                {"step": 4, "action": "效果验证", "description": "验证优化效果"},
            ],
            expected_outcomes=["响应时间降低20-50%", "资源利用率提升"],
            risks=["可能引入新问题", "需要回滚机制"],
            success_rate=0.92,
            usage_count=156,
            last_used=datetime.now() - timedelta(days=2),
            tags=["performance", "optimization", "latency"]
        ),
        EvolutionPattern(
            pattern_id="pattern_002",
            name="代码重构模式",
            type=PatternType.REFACTORING,
            status=PatternStatus.ACTIVE,
            description="通过重构提升代码质量和可维护性",
            applicability=["代码异味检测", "技术债务清理", "架构优化"],
            prerequisites=["测试覆盖率>80%", "代码审查流程"],
            steps=[
                {"step": 1, "action": "代码分析", "description": "识别重构目标"},
                {"step": 2, "action": "重构计划", "description": "制定重构计划"},
                {"step": 3, "action": "增量重构", "description": "逐步实施重构"},
                {"step": 4, "action": "测试验证", "description": "运行测试验证"},
            ],
            expected_outcomes=["代码复杂度降低", "可维护性提升"],
            risks=["可能破坏现有功能", "需要充分测试"],
            success_rate=0.88,
            usage_count=89,
            last_used=datetime.now() - timedelta(days=5),
            tags=["refactoring", "code-quality", "maintainability"]
        ),
        EvolutionPattern(
            pattern_id="pattern_003",
            name="服务迁移模式",
            type=PatternType.MIGRATION,
            status=PatternStatus.ACTIVE,
            description="安全地将服务迁移到新架构或平台",
            applicability=["平台升级", "架构迁移", "云迁移"],
            prerequisites=["迁移计划已审批", "回滚方案已准备"],
            steps=[
                {"step": 1, "action": "迁移评估", "description": "评估迁移影响"},
                {"step": 2, "action": "环境准备", "description": "准备目标环境"},
                {"step": 3, "action": "数据迁移", "description": "迁移数据"},
                {"step": 4, "action": "服务切换", "description": "切换服务"},
                {"step": 5, "action": "验证确认", "description": "验证迁移结果"},
            ],
            expected_outcomes=["迁移成功", "服务正常运行"],
            risks=["数据丢失风险", "服务中断"],
            success_rate=0.95,
            usage_count=45,
            last_used=datetime.now() - timedelta(days=10),
            tags=["migration", "platform", "cloud"]
        ),
        EvolutionPattern(
            pattern_id="pattern_004",
            name="水平扩展模式",
            type=PatternType.SCALING,
            status=PatternStatus.RECOMMENDED,
            description="通过增加实例数量提升系统处理能力",
            applicability=["负载增长", "高峰期应对", "容量规划"],
            prerequisites=["无状态设计", "负载均衡配置"],
            steps=[
                {"step": 1, "action": "容量评估", "description": "评估扩展需求"},
                {"step": 2, "action": "资源配置", "description": "配置新实例"},
                {"step": 3, "action": "负载均衡", "description": "更新负载均衡"},
                {"step": 4, "action": "监控验证", "description": "验证扩展效果"},
            ],
            expected_outcomes=["处理能力提升", "响应时间稳定"],
            risks=["资源成本增加", "管理复杂度提升"],
            success_rate=0.97,
            usage_count=78,
            last_used=datetime.now() - timedelta(days=1),
            tags=["scaling", "horizontal", "capacity"]
        ),
        EvolutionPattern(
            pattern_id="pattern_005",
            name="功能增强模式",
            type=PatternType.ENHANCEMENT,
            status=PatternStatus.ACTIVE,
            description="安全地添加新功能或改进现有功能",
            applicability=["功能迭代", "用户需求", "竞品对标"],
            prerequisites=["需求已确认", "设计已评审"],
            steps=[
                {"step": 1, "action": "需求分析", "description": "分析功能需求"},
                {"step": 2, "action": "设计实现", "description": "设计和实现"},
                {"step": 3, "action": "测试验证", "description": "测试新功能"},
                {"step": 4, "action": "灰度发布", "description": "逐步发布"},
            ],
            expected_outcomes=["功能上线", "用户满意度提升"],
            risks=["需求变更", "技术复杂度"],
            success_rate=0.85,
            usage_count=234,
            last_used=datetime.now() - timedelta(hours=12),
            tags=["enhancement", "feature", "iteration"]
        ),
    ]
    return patterns

def _generate_mock_recommendations() -> List[EvolutionRecommendation]:
    return [
        EvolutionRecommendation(
            recommendation_id="rec_001",
            pattern_id="pattern_001",
            pattern_name="性能优化模式",
            priority=RecommendationPriority.HIGH,
            confidence=0.92,
            reason="检测到响应时间持续增长，建议进行性能优化",
            expected_benefit="预计响应时间降低30%，用户满意度提升",
            estimated_effort="中等 (2-3天)",
            affected_components=["api_gateway", "skill_executor"],
            prerequisites_met=True,
            missing_prerequisites=[],
            created_at=datetime.now()
        ),
        EvolutionRecommendation(
            recommendation_id="rec_002",
            pattern_id="pattern_004",
            pattern_name="水平扩展模式",
            priority=RecommendationPriority.MEDIUM,
            confidence=0.85,
            reason="当前实例负载接近80%，建议扩展以应对增长",
            expected_benefit="处理能力提升50%，避免性能瓶颈",
            estimated_effort="低 (半天)",
            affected_components=["worker_pool", "load_balancer"],
            prerequisites_met=True,
            missing_prerequisites=[],
            created_at=datetime.now()
        ),
        EvolutionRecommendation(
            recommendation_id="rec_003",
            pattern_id="pattern_002",
            pattern_name="代码重构模式",
            priority=RecommendationPriority.LOW,
            confidence=0.78,
            reason="检测到代码复杂度较高，建议进行重构",
            expected_benefit="代码可维护性提升，技术债务减少",
            estimated_effort="高 (1-2周)",
            affected_components=["core_engine", "utils"],
            prerequisites_met=False,
            missing_prerequisites=["测试覆盖率需提升至80%以上"],
            created_at=datetime.now()
        ),
    ]

def _generate_mock_prediction(pattern_id: str) -> PredictionResult:
    return PredictionResult(
        prediction_id=f"pred_{int(time.time())}",
        pattern_id=pattern_id,
        status=EvolutionPredictionStatus.COMPLETED,
        predicted_outcomes={
            "performance_improvement": "+25%",
            "resource_efficiency": "+15%",
            "error_rate_change": "-10%",
            "user_satisfaction": "+8%",
        },
        performance_impact={
            "response_time": -0.25,
            "throughput": 0.30,
            "cpu_usage": -0.10,
            "memory_usage": -0.05,
        },
        risk_assessment={
            "overall_risk": "low",
            "rollback_complexity": "medium",
            "data_loss_risk": "none",
            "service_disruption_risk": "low",
        },
        confidence_score=0.88,
        simulation_duration_ms=2500,
        recommendations=[
            "建议在低峰期执行",
            "建议先在测试环境验证",
            "建议准备回滚方案",
        ],
        warnings=[
            "可能需要短暂服务中断",
        ],
        created_at=datetime.now()
    )

def _get_mock_evolution_state() -> EvolutionStateResponse:
    return EvolutionStateResponse(
        state=EvolutionState.IDLE,
        current_operation=None,
        progress=0.0,
        started_at=None,
        estimated_completion=None,
        current_pattern=None,
        completed_steps=[],
        pending_steps=[],
        errors=[],
        metrics={
            "last_evolution": (datetime.now() - timedelta(hours=6)).isoformat(),
            "total_evolutions": 156,
            "success_rate": 0.94,
        }
    )

async def _execute_evolution(trigger_id: str, request: TriggerRequest):
    evolution_knowledge_manager.update_state(
        state=EvolutionState.ANALYZING,
        current_operation="分析演化需求",
        progress=0.0,
        started_at=datetime.now(),
        current_pattern=request.pattern_id,
        completed_steps=[],
        pending_steps=["分析", "规划", "执行", "验证"],
        errors=[]
    )
    
    await evolution_knowledge_manager.broadcast_state_update("evolution_started", {
        "trigger_id": trigger_id,
        "pattern_id": request.pattern_id,
        "reason": request.reason
    })
    
    steps = [
        (EvolutionState.ANALYZING, "分析演化需求", 20),
        (EvolutionState.PLANNING, "制定演化计划", 40),
        (EvolutionState.EXECUTING, "执行演化操作", 70),
        (EvolutionState.VALIDATING, "验证演化结果", 90),
        (EvolutionState.COMPLETED, "演化完成", 100),
    ]
    
    for state, operation, progress in steps:
        await asyncio.sleep(2)
        current_state = evolution_knowledge_manager.get_state()
        completed = current_state.get("completed_steps", [])
        completed.append(operation)
        
        evolution_knowledge_manager.update_state(
            state=state,
            current_operation=operation,
            progress=progress,
            completed_steps=completed
        )
        
        await evolution_knowledge_manager.broadcast_state_update("evolution_progress", {
            "trigger_id": trigger_id,
            "state": state.value,
            "operation": operation,
            "progress": progress
        })
    
    evolution_knowledge_manager.update_state(
        state=EvolutionState.IDLE,
        current_operation=None,
        progress=0.0,
        current_pattern=None,
        started_at=None
    )
    
    await evolution_knowledge_manager.broadcast_state_update("evolution_completed", {
        "trigger_id": trigger_id,
        "pattern_id": request.pattern_id,
        "duration_ms": 10000
    })

@router.get(
    "/patterns",
    response_model=PatternListResponse,
    summary="获取演化模式列表",
    description="获取所有可用的演化模式，支持按类型和状态筛选"
)
async def get_evolution_patterns(
    type: Optional[PatternType] = Query(None, description="按类型筛选"),
    status: Optional[PatternStatus] = Query(None, description="按状态筛选"),
    tag: Optional[str] = Query(None, description="按标签筛选"),
    skip: int = Query(0, description="跳过数量", ge=0),
    limit: int = Query(20, description="返回数量", ge=1, le=100),
    db: Session = Depends(get_db)
):
    cache_key = f"evolution_knowledge:patterns:{type}:{status}:{tag}:{skip}:{limit}"
    cached = cache_service.get_json(cache_key)
    if cached:
        return PatternListResponse(**cached)
    
    patterns = _generate_mock_patterns()
    
    if type:
        patterns = [p for p in patterns if p.type == type]
    if status:
        patterns = [p for p in patterns if p.status == status]
    if tag:
        patterns = [p for p in patterns if tag in p.tags]
    
    total = len(patterns)
    items = patterns[skip:skip + limit]
    
    result = PatternListResponse(
        total=total,
        items=items,
        page=skip // limit + 1,
        page_size=limit
    )
    
    cache_service.set_json(cache_key, result.model_dump(), ttl=300)
    
    return result

@router.get(
    "/patterns/{pattern_id}",
    response_model=EvolutionPattern,
    summary="获取特定演化模式",
    description="获取指定演化模式的详细信息"
)
async def get_evolution_pattern(
    pattern_id: str,
    db: Session = Depends(get_db)
):
    cache_key = f"evolution_knowledge:pattern:{pattern_id}"
    cached = cache_service.get_json(cache_key)
    if cached:
        return EvolutionPattern(**cached)
    
    patterns = _generate_mock_patterns()
    pattern = next((p for p in patterns if p.pattern_id == pattern_id), None)
    
    if not pattern:
        raise HTTPException(
            status_code=404,
            detail=f"未找到模式: {pattern_id}"
        )
    
    cache_service.set_json(cache_key, pattern.model_dump(), ttl=300)
    
    return pattern

@router.get(
    "/recommendations",
    response_model=RecommendationListResponse,
    summary="获取演化推荐",
    description="获取基于当前系统状态的演化推荐"
)
async def get_evolution_recommendations(
    priority: Optional[RecommendationPriority] = Query(None, description="按优先级筛选"),
    limit: int = Query(10, description="返回数量", ge=1, le=50),
    db: Session = Depends(get_db)
):
    cache_key = f"evolution_knowledge:recommendations:{priority}:{limit}"
    cached = cache_service.get_json(cache_key)
    if cached:
        return RecommendationListResponse(**cached)
    
    recommendations = _generate_mock_recommendations()
    
    if priority:
        recommendations = [r for r in recommendations if r.priority == priority]
    
    recommendations = recommendations[:limit]
    
    result = RecommendationListResponse(
        total=len(recommendations),
        items=recommendations
    )
    
    cache_service.set_json(cache_key, result.model_dump(), ttl=60)
    
    return result

@router.post(
    "/predict",
    response_model=PredictionResult,
    summary="预测演化效果",
    description="模拟指定演化模式的效果预测"
)
async def predict_evolution(
    request: PredictionRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    patterns = _generate_mock_patterns()
    pattern = next((p for p in patterns if p.pattern_id == request.pattern_id), None)
    
    if not pattern:
        raise HTTPException(
            status_code=404,
            detail=f"未找到模式: {request.pattern_id}"
        )
    
    result = _generate_mock_prediction(request.pattern_id)
    
    if request.target_components:
        result.predicted_outcomes["target_components"] = request.target_components
    
    return result

@router.get(
    "/status",
    response_model=EvolutionStateResponse,
    summary="获取当前演化状态",
    description="获取当前演化操作的状态信息"
)
async def get_evolution_status(db: Session = Depends(get_db)):
    state = evolution_knowledge_manager.get_state()
    return EvolutionStateResponse(
        state=state.get("state", EvolutionState.IDLE),
        current_operation=state.get("current_operation"),
        progress=state.get("progress", 0.0),
        started_at=state.get("started_at"),
        estimated_completion=datetime.now() + timedelta(minutes=5) if state.get("started_at") else None,
        current_pattern=state.get("current_pattern"),
        completed_steps=state.get("completed_steps", []),
        pending_steps=state.get("pending_steps", []),
        errors=state.get("errors", []),
        metrics=state.get("metrics", {})
    )

@router.post(
    "/trigger",
    response_model=TriggerResponse,
    summary="触发演化操作",
    description="手动触发一次演化操作"
)
async def trigger_evolution(
    request: TriggerRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    current_state = evolution_knowledge_manager.get_state()
    
    if current_state.get("state") not in [EvolutionState.IDLE, EvolutionState.COMPLETED, EvolutionState.FAILED]:
        if not request.force:
            raise HTTPException(
                status_code=409,
                detail="演化操作正在进行中，请等待完成或使用 force=true 强制执行"
            )
    
    patterns = _generate_mock_patterns()
    pattern = next((p for p in patterns if p.pattern_id == request.pattern_id), None)
    
    if not pattern:
        raise HTTPException(
            status_code=404,
            detail=f"未找到模式: {request.pattern_id}"
        )
    
    trigger_id = f"trigger_{int(time.time() * 1000)}"
    
    if request.dry_run:
        return TriggerResponse(
            trigger_id=trigger_id,
            pattern_id=request.pattern_id,
            status=EvolutionTriggerStatus.COMPLETED,
            message="模拟运行完成，未执行实际演化",
            estimated_duration_ms=0
        )
    
    background_tasks.add_task(_execute_evolution, trigger_id, request)
    
    return TriggerResponse(
        trigger_id=trigger_id,
        pattern_id=request.pattern_id,
        status=EvolutionTriggerStatus.RUNNING,
        message="演化已触发，正在后台执行",
        estimated_duration_ms=10000
    )

@router.websocket("/ws")
async def evolution_websocket_endpoint(websocket: WebSocket):
    await evolution_knowledge_manager.connect(websocket)
    try:
        current_state = evolution_knowledge_manager.get_state()
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
                    evolution_knowledge_manager.update_heartbeat(websocket)
                    await websocket.send_json({
                        "type": "pong",
                        "timestamp": time.time()
                    })
                elif message.get("type") == "heartbeat":
                    evolution_knowledge_manager.update_heartbeat(websocket)
                    await websocket.send_json({
                        "type": "heartbeat_ack",
                        "timestamp": time.time()
                    })
                elif message.get("type") == "get_status":
                    current_state = evolution_knowledge_manager.get_state()
                    await websocket.send_json({
                        "type": "status_update",
                        "data": current_state,
                        "timestamp": datetime.now().isoformat()
                    })
            except json.JSONDecodeError:
                await websocket.send_json({"error": "Invalid JSON"})
    except WebSocketDisconnect:
        evolution_knowledge_manager.disconnect(websocket)

@router.get(
    "/history",
    summary="获取演化历史",
    description="获取历史演化操作记录"
)
async def get_evolution_history(
    skip: int = Query(0, description="跳过数量", ge=0),
    limit: int = Query(20, description="返回数量", ge=1, le=100),
    pattern_type: Optional[PatternType] = Query(None, description="按模式类型筛选"),
    db: Session = Depends(get_db)
):
    cache_key = f"evolution_knowledge:history:{skip}:{limit}:{pattern_type}"
    cached = cache_service.get_json(cache_key)
    if cached:
        return cached
    
    history = []
    for i in range(limit):
        idx = skip + i
        history.append({
            "id": f"hist_{idx}",
            "pattern_id": f"pattern_{idx % 5 + 1:03d}",
            "pattern_name": ["性能优化", "代码重构", "服务迁移", "水平扩展", "功能增强"][idx % 5],
            "triggered_at": (datetime.now() - timedelta(days=idx, hours=idx)).isoformat(),
            "completed_at": (datetime.now() - timedelta(days=idx, hours=idx - 1)).isoformat(),
            "status": "completed" if idx % 5 != 0 else "failed",
            "duration_ms": 3600000 + idx * 10000,
            "success": idx % 5 != 0,
        })
    
    result = {
        "total": 156,
        "items": history,
        "page": skip // limit + 1,
        "page_size": limit,
    }
    
    cache_service.set_json(cache_key, result, ttl=60)
    
    return result

@router.get(
    "/statistics",
    summary="获取演化统计",
    description="获取演化操作的统计数据"
)
async def get_evolution_statistics(db: Session = Depends(get_db)):
    cache_key = "evolution_knowledge:statistics"
    cached = cache_service.get_json(cache_key)
    if cached:
        return cached
    
    result = {
        "total_evolutions": 156,
        "successful_evolutions": 148,
        "failed_evolutions": 8,
        "success_rate": 0.9487,
        "by_pattern_type": {
            "optimization": 45,
            "refactoring": 32,
            "migration": 18,
            "scaling": 28,
            "enhancement": 33,
        },
        "average_duration_ms": 3420500,
        "last_24h": 4,
        "last_7d": 23,
        "most_used_pattern": "功能增强模式",
    }
    
    cache_service.set_json(cache_key, result, ttl=300)
    
    return result

class KnowledgeCategory(str, Enum):
    BEST_PRACTICE = "best_practice"
    LESSON_LEARNED = "lesson_learned"
    TECHNICAL_SOLUTION = "technical_solution"
    ARCHITECTURE_PATTERN = "architecture_pattern"
    PERFORMANCE_TIP = "performance_tip"
    SECURITY_GUIDELINE = "security_guideline"

class KnowledgeStatus(str, Enum):
    DRAFT = "draft"
    PUBLISHED = "published"
    ARCHIVED = "archived"
    DEPRECATED = "deprecated"

class KnowledgeItem(BaseModel):
    knowledge_id: str = Field(..., description="知识ID")
    title: str = Field(..., description="知识标题")
    category: KnowledgeCategory = Field(..., description="知识类别")
    status: KnowledgeStatus = Field(..., description="知识状态")
    content: str = Field(..., description="知识内容")
    tags: List[str] = Field(default_factory=list, description="标签")
    author: str = Field(..., description="作者")
    department: Optional[str] = Field(None, description="所属部门")
    related_skills: List[str] = Field(default_factory=list, description="相关技能")
    related_patterns: List[str] = Field(default_factory=list, description="相关演化模式")
    usage_count: int = Field(0, description="使用次数")
    effectiveness_score: float = Field(0.0, description="有效性评分", ge=0, le=100)
    created_at: datetime = Field(default_factory=datetime.now, description="创建时间")
    updated_at: datetime = Field(default_factory=datetime.now, description="更新时间")
    published_at: Optional[datetime] = Field(None, description="发布时间")
    
    class Config:
        from_attributes = True

class KnowledgeListResponse(BaseModel):
    total: int = Field(0, description="总数")
    items: List[KnowledgeItem] = Field(default_factory=list, description="知识列表")
    page: int = Field(1, description="当前页")
    page_size: int = Field(20, description="每页大小")

class KnowledgeCreateRequest(BaseModel):
    title: str = Field(..., description="知识标题", min_length=1, max_length=200)
    category: KnowledgeCategory = Field(..., description="知识类别")
    content: str = Field(..., description="知识内容", min_length=1)
    tags: List[str] = Field(default_factory=list, description="标签")
    author: str = Field(..., description="作者")
    department: Optional[str] = Field(None, description="所属部门")
    related_skills: List[str] = Field(default_factory=list, description="相关技能")
    related_patterns: List[str] = Field(default_factory=list, description="相关演化模式")

def _generate_mock_knowledge_items() -> List[KnowledgeItem]:
    knowledge_items = [
        KnowledgeItem(
            knowledge_id="knowledge_001",
            title="API性能优化最佳实践",
            category=KnowledgeCategory.BEST_PRACTICE,
            status=KnowledgeStatus.PUBLISHED,
            content="通过缓存策略、数据库优化和异步处理提升API性能。建议使用Redis缓存热点数据，优化SQL查询，使用消息队列处理耗时操作。",
            tags=["performance", "api", "optimization", "caching"],
            author="张三",
            department="技术部",
            related_skills=["skill_001", "skill_002"],
            related_patterns=["pattern_001"],
            usage_count=45,
            effectiveness_score=92.5,
            created_at=datetime.now() - timedelta(days=30),
            updated_at=datetime.now() - timedelta(days=5),
            published_at=datetime.now() - timedelta(days=28)
        ),
        KnowledgeItem(
            knowledge_id="knowledge_002",
            title="微服务架构迁移经验",
            category=KnowledgeCategory.LESSON_LEARNED,
            status=KnowledgeStatus.PUBLISHED,
            content="从单体应用迁移到微服务架构的经验总结。关键点：1. 服务边界划分要清晰；2. 数据一致性处理要谨慎；3. 监控和日志要完善；4. 渐进式迁移降低风险。",
            tags=["microservices", "migration", "architecture"],
            author="李四",
            department="架构组",
            related_skills=["skill_003"],
            related_patterns=["pattern_003"],
            usage_count=38,
            effectiveness_score=88.0,
            created_at=datetime.now() - timedelta(days=20),
            updated_at=datetime.now() - timedelta(days=3),
            published_at=datetime.now() - timedelta(days=18)
        ),
        KnowledgeItem(
            knowledge_id="knowledge_003",
            title="高并发场景下的数据库连接池配置",
            category=KnowledgeCategory.TECHNICAL_SOLUTION,
            status=KnowledgeStatus.PUBLISHED,
            content="针对高并发场景的数据库连接池配置方案。推荐配置：最大连接数=CPU核心数*2+有效磁盘数，最小空闲连接数=最大连接数/4，连接超时时间=30秒，空闲超时时间=600秒。",
            tags=["database", "connection-pool", "concurrency"],
            author="王五",
            department="数据库组",
            related_skills=["skill_004"],
            related_patterns=["pattern_004"],
            usage_count=56,
            effectiveness_score=95.0,
            created_at=datetime.now() - timedelta(days=15),
            updated_at=datetime.now() - timedelta(days=2),
            published_at=datetime.now() - timedelta(days=13)
        ),
        KnowledgeItem(
            knowledge_id="knowledge_004",
            title="事件驱动架构设计模式",
            category=KnowledgeCategory.ARCHITECTURE_PATTERN,
            status=KnowledgeStatus.PUBLISHED,
            content="事件驱动架构的核心设计模式：事件溯源、CQRS、Saga模式。适用于高扩展性、松耦合的系统设计。需要注意事件顺序性和幂等性处理。",
            tags=["event-driven", "architecture", "cqrs", "saga"],
            author="赵六",
            department="架构组",
            related_skills=["skill_005"],
            related_patterns=["pattern_002"],
            usage_count=32,
            effectiveness_score=90.0,
            created_at=datetime.now() - timedelta(days=10),
            updated_at=datetime.now() - timedelta(days=1),
            published_at=datetime.now() - timedelta(days=8)
        ),
        KnowledgeItem(
            knowledge_id="knowledge_005",
            title="前端性能优化技巧",
            category=KnowledgeCategory.PERFORMANCE_TIP,
            status=KnowledgeStatus.PUBLISHED,
            content="前端性能优化的关键技巧：1. 代码分割和懒加载；2. 图片优化和CDN加速；3. 浏览器缓存策略；4. 虚拟滚动处理大数据列表；5. 防抖和节流优化事件处理。",
            tags=["frontend", "performance", "optimization"],
            author="孙七",
            department="前端组",
            related_skills=["skill_006"],
            related_patterns=["pattern_001"],
            usage_count=67,
            effectiveness_score=93.5,
            created_at=datetime.now() - timedelta(days=8),
            updated_at=datetime.now() - timedelta(hours=12),
            published_at=datetime.now() - timedelta(days=6)
        ),
    ]
    return knowledge_items

@router.get(
    "/knowledge",
    response_model=KnowledgeListResponse,
    summary="获取知识列表",
    description="获取知识库中的知识列表，支持按类别、状态、标签筛选"
)
async def get_knowledge_list(
    category: Optional[KnowledgeCategory] = Query(None, description="按类别筛选"),
    status: Optional[KnowledgeStatus] = Query(None, description="按状态筛选"),
    tag: Optional[str] = Query(None, description="按标签筛选"),
    author: Optional[str] = Query(None, description="按作者筛选"),
    skip: int = Query(0, description="跳过数量", ge=0),
    limit: int = Query(20, description="返回数量", ge=1, le=100),
    db: Session = Depends(get_db)
):
    cache_key = f"evolution_knowledge:knowledge_list:{category}:{status}:{tag}:{author}:{skip}:{limit}"
    cached = cache_service.get_json(cache_key)
    if cached:
        return KnowledgeListResponse(**cached)
    
    knowledge_items = _generate_mock_knowledge_items()
    
    if category:
        knowledge_items = [k for k in knowledge_items if k.category == category]
    if status:
        knowledge_items = [k for k in knowledge_items if k.status == status]
    if tag:
        knowledge_items = [k for k in knowledge_items if tag in k.tags]
    if author:
        knowledge_items = [k for k in knowledge_items if author in k.author]
    
    total = len(knowledge_items)
    items = knowledge_items[skip:skip + limit]
    
    result = KnowledgeListResponse(
        total=total,
        items=items,
        page=skip // limit + 1,
        page_size=limit
    )
    
    cache_service.set_json(cache_key, result.model_dump(), ttl=300)
    
    return result

@router.post(
    "/knowledge",
    response_model=KnowledgeItem,
    summary="创建知识",
    description="创建新的知识条目"
)
async def create_knowledge(
    request: KnowledgeCreateRequest,
    db: Session = Depends(get_db)
):
    knowledge_id = f"knowledge_{int(time.time() * 1000)}"
    
    new_knowledge = KnowledgeItem(
        knowledge_id=knowledge_id,
        title=request.title,
        category=request.category,
        status=KnowledgeStatus.DRAFT,
        content=request.content,
        tags=request.tags,
        author=request.author,
        department=request.department,
        related_skills=request.related_skills,
        related_patterns=request.related_patterns,
        usage_count=0,
        effectiveness_score=0.0,
        created_at=datetime.now(),
        updated_at=datetime.now(),
        published_at=None
    )
    
    return new_knowledge

@router.get(
    "/knowledge/{knowledge_id}",
    response_model=KnowledgeItem,
    summary="获取特定知识",
    description="获取指定知识的详细信息"
)
async def get_knowledge_item(
    knowledge_id: str,
    db: Session = Depends(get_db)
):
    cache_key = f"evolution_knowledge:knowledge_item:{knowledge_id}"
    cached = cache_service.get_json(cache_key)
    if cached:
        return KnowledgeItem(**cached)
    
    knowledge_items = _generate_mock_knowledge_items()
    knowledge = next((k for k in knowledge_items if k.knowledge_id == knowledge_id), None)
    
    if not knowledge:
        raise HTTPException(
            status_code=404,
            detail=f"未找到知识: {knowledge_id}"
        )
    
    cache_service.set_json(cache_key, knowledge.model_dump(), ttl=300)
    
    return knowledge

class SharingStatus(str, Enum):
    PUBLIC = "public"
    PRIVATE = "private"
    SHARED = "shared"
    RESTRICTED = "restricted"

class SharingPermission(str, Enum):
    READ = "read"
    WRITE = "write"
    ADMIN = "admin"

class KnowledgeSharing(BaseModel):
    sharing_id: str = Field(..., description="共享ID")
    knowledge_id: str = Field(..., description="知识ID")
    source_project_id: str = Field(..., description="源项目ID")
    target_project_ids: List[str] = Field(default_factory=list, description="目标项目ID列表")
    status: SharingStatus = Field(..., description="共享状态")
    permission: SharingPermission = Field(..., description="共享权限")
    shared_by: str = Field(..., description="共享者")
    shared_at: datetime = Field(default_factory=datetime.now, description="共享时间")
    expires_at: Optional[datetime] = Field(None, description="过期时间")
    access_count: int = Field(0, description="访问次数")
    tags: List[str] = Field(default_factory=list, description="标签")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="元数据")
    
    class Config:
        from_attributes = True

class KnowledgeSharingListResponse(BaseModel):
    total: int = Field(0, description="总数")
    items: List[KnowledgeSharing] = Field(default_factory=list, description="共享列表")
    page: int = Field(1, description="当前页")
    page_size: int = Field(20, description="每页大小")

class KnowledgeSharingCreateRequest(BaseModel):
    knowledge_id: str = Field(..., description="知识ID")
    source_project_id: str = Field(..., description="源项目ID")
    target_project_ids: List[str] = Field(..., description="目标项目ID列表")
    permission: SharingPermission = Field(SharingPermission.READ, description="共享权限")
    shared_by: str = Field(..., description="共享者")
    expires_at: Optional[datetime] = Field(None, description="过期时间")
    tags: List[str] = Field(default_factory=list, description="标签")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="元数据")

def _generate_mock_knowledge_sharings() -> List[KnowledgeSharing]:
    sharing_items = [
        KnowledgeSharing(
            sharing_id="sharing_001",
            knowledge_id="knowledge_001",
            source_project_id="project_001",
            target_project_ids=["project_002", "project_003"],
            status=SharingStatus.SHARED,
            permission=SharingPermission.READ,
            shared_by="张三",
            shared_at=datetime.now() - timedelta(days=10),
            expires_at=datetime.now() + timedelta(days=90),
            access_count=45,
            tags=["performance", "api"],
            metadata={"department": "技术部", "importance": "high"}
        ),
        KnowledgeSharing(
            sharing_id="sharing_002",
            knowledge_id="knowledge_002",
            source_project_id="project_002",
            target_project_ids=["project_001"],
            status=SharingStatus.PUBLIC,
            permission=SharingPermission.WRITE,
            shared_by="李四",
            shared_at=datetime.now() - timedelta(days=5),
            expires_at=None,
            access_count=32,
            tags=["microservices", "architecture"],
            metadata={"department": "架构组", "importance": "medium"}
        ),
        KnowledgeSharing(
            sharing_id="sharing_003",
            knowledge_id="knowledge_003",
            source_project_id="project_001",
            target_project_ids=["project_003", "project_004"],
            status=SharingStatus.RESTRICTED,
            permission=SharingPermission.ADMIN,
            shared_by="王五",
            shared_at=datetime.now() - timedelta(days=3),
            expires_at=datetime.now() + timedelta(days=30),
            access_count=18,
            tags=["database", "security"],
            metadata={"department": "数据库组", "importance": "critical"}
        ),
    ]
    return sharing_items

@router.get(
    "/sharing",
    response_model=KnowledgeSharingListResponse,
    summary="获取知识共享列表",
    description="获取所有知识共享记录，支持按状态、权限、项目筛选"
)
async def get_knowledge_sharing_list(
    status: Optional[SharingStatus] = Query(None, description="按状态筛选"),
    permission: Optional[SharingPermission] = Query(None, description="按权限筛选"),
    source_project_id: Optional[str] = Query(None, description="按源项目筛选"),
    target_project_id: Optional[str] = Query(None, description="按目标项目筛选"),
    skip: int = Query(0, description="跳过数量", ge=0),
    limit: int = Query(20, description="返回数量", ge=1, le=100),
    db: Session = Depends(get_db)
):
    cache_key = f"evolution_knowledge:sharing_list:{status}:{permission}:{source_project_id}:{target_project_id}:{skip}:{limit}"
    cached = cache_service.get_json(cache_key)
    if cached:
        return KnowledgeSharingListResponse(**cached)
    
    sharing_items = _generate_mock_knowledge_sharings()
    
    if status:
        sharing_items = [s for s in sharing_items if s.status == status]
    if permission:
        sharing_items = [s for s in sharing_items if s.permission == permission]
    if source_project_id:
        sharing_items = [s for s in sharing_items if s.source_project_id == source_project_id]
    if target_project_id:
        sharing_items = [s for s in sharing_items if target_project_id in s.target_project_ids]
    
    total = len(sharing_items)
    items = sharing_items[skip:skip + limit]
    
    result = KnowledgeSharingListResponse(
        total=total,
        items=items,
        page=skip // limit + 1,
        page_size=limit
    )
    
    cache_service.set_json(cache_key, result.model_dump(), ttl=300)
    
    return result

@router.post(
    "/sharing",
    response_model=KnowledgeSharing,
    summary="创建知识共享",
    description="创建新的知识共享记录"
)
async def create_knowledge_sharing(
    request: KnowledgeSharingCreateRequest,
    db: Session = Depends(get_db)
):
    sharing_id = f"sharing_{int(time.time() * 1000)}"
    
    new_sharing = KnowledgeSharing(
        sharing_id=sharing_id,
        knowledge_id=request.knowledge_id,
        source_project_id=request.source_project_id,
        target_project_ids=request.target_project_ids,
        status=SharingStatus.SHARED,
        permission=request.permission,
        shared_by=request.shared_by,
        shared_at=datetime.now(),
        expires_at=request.expires_at,
        access_count=0,
        tags=request.tags,
        metadata=request.metadata
    )
    
    return new_sharing

@router.get(
    "/sharing/{sharing_id}",
    response_model=KnowledgeSharing,
    summary="获取特定知识共享",
    description="获取指定知识共享的详细信息"
)
async def get_knowledge_sharing_item(
    sharing_id: str,
    db: Session = Depends(get_db)
):
    cache_key = f"evolution_knowledge:sharing_item:{sharing_id}"
    cached = cache_service.get_json(cache_key)
    if cached:
        return KnowledgeSharing(**cached)
    
    sharing_items = _generate_mock_knowledge_sharings()
    sharing = next((s for s in sharing_items if s.sharing_id == sharing_id), None)
    
    if not sharing:
        raise HTTPException(
            status_code=404,
            detail=f"未找到知识共享: {sharing_id}"
        )
    
    cache_service.set_json(cache_key, sharing.model_dump(), ttl=300)
    
    return sharing

@router.get(
    "/sharing/status/summary",
    summary="获取知识共享状态汇总",
    description="获取知识共享的状态统计信息"
)
async def get_knowledge_sharing_summary(db: Session = Depends(get_db)):
    cache_key = "evolution_knowledge:sharing_summary"
    cached = cache_service.get_json(cache_key)
    if cached:
        return cached
    
    sharing_items = _generate_mock_knowledge_sharings()
    
    status_counts = {}
    for status in SharingStatus:
        status_counts[status.value] = len([s for s in sharing_items if s.status == status])
    
    permission_counts = {}
    for permission in SharingPermission:
        permission_counts[permission.value] = len([s for s in sharing_items if s.permission == permission])
    
    total_access_count = sum(s.access_count for s in sharing_items)
    
    result = {
        "total_sharings": len(sharing_items),
        "status_distribution": status_counts,
        "permission_distribution": permission_counts,
        "total_access_count": total_access_count,
        "average_access_count": total_access_count / len(sharing_items) if sharing_items else 0,
        "active_sharings": len([s for s in sharing_items if s.status in [SharingStatus.PUBLIC, SharingStatus.SHARED]]),
        "expired_sharings": len([s for s in sharing_items if s.expires_at and s.expires_at < datetime.now()])
    }
    
    cache_service.set_json(cache_key, result, ttl=300)
    
    return result

class KnowledgeSearchResult(BaseModel):
    query: str = Field(..., description="查询关键词")
    total_results: int = Field(0, description="总结果数")
    results: List[KnowledgeItem] = Field(default_factory=list, description="搜索结果")
    search_time_ms: int = Field(0, description="搜索耗时（毫秒）")
    filters_applied: List[str] = Field(default_factory=list, description="应用的过滤器")
    suggestions: List[str] = Field(default_factory=list, description="搜索建议")

class KnowledgeAnalytics(BaseModel):
    period: str = Field(..., description="统计周期")
    total_knowledge: int = Field(0, description="知识总数")
    new_knowledge: int = Field(0, description="新增知识数")
    updated_knowledge: int = Field(0, description="更新知识数")
    top_categories: List[Dict[str, Any]] = Field(default_factory=list, description="热门分类")
    top_tags: List[Dict[str, Any]] = Field(default_factory=list, description="热门标签")
    usage_trend: List[Dict[str, Any]] = Field(default_factory=list, description="使用趋势")
    effectiveness_avg: float = Field(0.0, description="平均有效性评分")

class KnowledgeImportRequest(BaseModel):
    source_type: str = Field(..., description="来源类型: file, url, api")
    source_data: str = Field(..., description="来源数据")
    category: Optional[KnowledgeCategory] = Field(None, description="目标分类")
    tags: List[str] = Field(default_factory=list, description="标签")
    auto_categorize: bool = Field(True, description="自动分类")

class KnowledgeImportResult(BaseModel):
    import_id: str = Field(..., description="导入ID")
    status: str = Field(..., description="状态: processing, completed, failed")
    total_items: int = Field(0, description="总条目数")
    imported_items: int = Field(0, description="已导入条目数")
    failed_items: int = Field(0, description="失败条目数")
    errors: List[str] = Field(default_factory=list, description="错误列表")
    started_at: datetime = Field(default_factory=datetime.now, description="开始时间")
    completed_at: Optional[datetime] = Field(None, description="完成时间")

class KnowledgeExportRequest(BaseModel):
    export_type: str = Field("json", description="导出类型: json, csv, markdown")
    category: Optional[KnowledgeCategory] = Field(None, description="分类筛选")
    tags: Optional[List[str]] = Field(None, description="标签筛选")
    include_metadata: bool = Field(True, description="包含元数据")

class KnowledgeExportResult(BaseModel):
    export_id: str = Field(..., description="导出ID")
    export_type: str = Field(..., description="导出类型")
    total_items: int = Field(0, description="总条目数")
    file_size_kb: float = Field(0.0, description="文件大小（KB）")
    download_url: str = Field(..., description="下载链接")
    created_at: datetime = Field(default_factory=datetime.now, description="创建时间")

@router.post(
    "/search",
    response_model=KnowledgeSearchResult,
    summary="搜索知识",
    description="全文搜索知识库内容，支持多种过滤条件"
)
async def search_knowledge(
    query: str = Query(..., description="搜索关键词", min_length=1),
    category: Optional[KnowledgeCategory] = Query(None, description="按分类筛选"),
    tags: Optional[List[str]] = Query(None, description="按标签筛选"),
    author: Optional[str] = Query(None, description="按作者筛选"),
    min_effectiveness: Optional[float] = Query(None, description="最低有效性评分", ge=0, le=100),
    skip: int = Query(0, description="跳过数量", ge=0),
    limit: int = Query(20, description="返回数量", ge=1, le=100),
    db: Session = Depends(get_db)
):
    import time as time_module
    start_time = time_module.time()
    
    knowledge_items = _generate_mock_knowledge_items()
    
    filters_applied = []
    if category:
        knowledge_items = [k for k in knowledge_items if k.category == category]
        filters_applied.append(f"category={category}")
    if tags:
        knowledge_items = [k for k in knowledge_items if any(tag in k.tags for tag in tags)]
        filters_applied.append(f"tags={tags}")
    if author:
        knowledge_items = [k for k in knowledge_items if author in k.author]
        filters_applied.append(f"author={author}")
    if min_effectiveness is not None:
        knowledge_items = [k for k in knowledge_items if k.effectiveness_score >= min_effectiveness]
        filters_applied.append(f"min_effectiveness={min_effectiveness}")
    
    query_lower = query.lower()
    results = [
        k for k in knowledge_items
        if query_lower in k.title.lower() or query_lower in k.content.lower() or
           any(query_lower in tag.lower() for tag in k.tags)
    ]
    
    search_time = int((time_module.time() - start_time) * 1000)
    
    suggestions = []
    if len(results) == 0:
        suggestions = [
            "尝试使用更通用的关键词",
            "检查拼写是否正确",
            "移除部分过滤条件"
        ]
    
    return KnowledgeSearchResult(
        query=query,
        total_results=len(results),
        results=results[skip:skip + limit],
        search_time_ms=search_time,
        filters_applied=filters_applied,
        suggestions=suggestions
    )

@router.get(
    "/analytics",
    response_model=KnowledgeAnalytics,
    summary="获取知识库分析",
    description="获取知识库的使用统计和分析数据"
)
async def get_knowledge_analytics(
    period: str = Query("7d", description="统计周期: 24h, 7d, 30d, 90d"),
    db: Session = Depends(get_db)
):
    cache_key = f"evolution_knowledge:analytics:{period}"
    cached = cache_service.get_json(cache_key)
    if cached:
        return KnowledgeAnalytics(**cached)
    
    knowledge_items = _generate_mock_knowledge_items()
    
    top_categories = [
        {"category": "best_practice", "count": 45, "avg_effectiveness": 88.5},
        {"category": "technical_solution", "count": 38, "avg_effectiveness": 92.3},
        {"category": "lesson_learned", "count": 32, "avg_effectiveness": 85.0},
        {"category": "architecture_pattern", "count": 28, "avg_effectiveness": 90.2},
        {"category": "performance_tip", "count": 25, "avg_effectiveness": 87.8}
    ]
    
    top_tags = [
        {"tag": "performance", "count": 56, "trend": "up"},
        {"tag": "optimization", "count": 48, "trend": "stable"},
        {"tag": "api", "count": 42, "trend": "up"},
        {"tag": "architecture", "count": 38, "trend": "stable"},
        {"tag": "security", "count": 35, "trend": "up"}
    ]
    
    usage_trend = []
    days = 7 if period == "7d" else 30 if period == "30d" else 90 if period == "90d" else 1
    for i in range(days):
        date = datetime.now() - timedelta(days=i)
        usage_trend.append({
            "date": date.strftime("%Y-%m-%d"),
            "views": 150 + (hash(str(i)) % 50),
            "searches": 45 + (hash(str(i)) % 20),
            "new_knowledge": 3 + (hash(str(i)) % 5)
        })
    usage_trend.reverse()
    
    avg_effectiveness = sum(k.effectiveness_score for k in knowledge_items) / len(knowledge_items) if knowledge_items else 0
    
    result = KnowledgeAnalytics(
        period=period,
        total_knowledge=len(knowledge_items),
        new_knowledge=12,
        updated_knowledge=8,
        top_categories=top_categories,
        top_tags=top_tags,
        usage_trend=usage_trend,
        effectiveness_avg=round(avg_effectiveness, 2)
    )
    
    cache_service.set_json(cache_key, result.model_dump(), ttl=300)
    
    return result

@router.post(
    "/import",
    response_model=KnowledgeImportResult,
    summary="导入知识",
    description="从外部来源导入知识到知识库"
)
async def import_knowledge(
    request: KnowledgeImportRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    import_id = f"import_{int(time.time() * 1000)}"
    
    result = KnowledgeImportResult(
        import_id=import_id,
        status="processing",
        total_items=0,
        imported_items=0,
        failed_items=0,
        errors=[],
        started_at=datetime.now()
    )
    
    return result

@router.post(
    "/export",
    response_model=KnowledgeExportResult,
    summary="导出知识",
    description="导出知识库数据到文件"
)
async def export_knowledge(
    request: KnowledgeExportRequest,
    db: Session = Depends(get_db)
):
    export_id = f"export_{int(time.time() * 1000)}"
    
    knowledge_items = _generate_mock_knowledge_items()
    
    if request.category:
        knowledge_items = [k for k in knowledge_items if k.category == request.category]
    if request.tags:
        knowledge_items = [k for k in knowledge_items if any(tag in k.tags for tag in request.tags)]
    
    total_items = len(knowledge_items)
    file_size = total_items * 2.5
    
    download_url = f"/api/evolution-knowledge/downloads/{export_id}.{request.export_type}"
    
    result = KnowledgeExportResult(
        export_id=export_id,
        export_type=request.export_type,
        total_items=total_items,
        file_size_kb=round(file_size, 2),
        download_url=download_url,
        created_at=datetime.now()
    )
    
    return result

@router.post(
    "/knowledge/{knowledge_id}/rate",
    summary="评价知识",
    description="对知识条目进行有效性评分"
)
async def rate_knowledge(
    knowledge_id: str,
    rating: float = Query(..., description="评分", ge=0, le=100),
    feedback: Optional[str] = Query(None, description="反馈意见"),
    db: Session = Depends(get_db)
):
    knowledge_items = _generate_mock_knowledge_items()
    knowledge = next((k for k in knowledge_items if k.knowledge_id == knowledge_id), None)
    
    if not knowledge:
        raise HTTPException(
            status_code=404,
            detail=f"未找到知识: {knowledge_id}"
        )
    
    return {
        "success": True,
        "knowledge_id": knowledge_id,
        "new_rating": rating,
        "message": "评分已提交",
        "rated_at": datetime.now().isoformat()
    }

@router.post(
    "/knowledge/{knowledge_id}/relate",
    summary="关联知识",
    description="建立知识条目之间的关联关系"
)
async def relate_knowledge(
    knowledge_id: str,
    related_ids: List[str] = Query(..., description="关联知识ID列表"),
    relation_type: str = Query("related", description="关系类型: related, prerequisite, extension"),
    db: Session = Depends(get_db)
):
    knowledge_items = _generate_mock_knowledge_items()
    knowledge = next((k for k in knowledge_items if k.knowledge_id == knowledge_id), None)
    
    if not knowledge:
        raise HTTPException(
            status_code=404,
            detail=f"未找到知识: {knowledge_id}"
        )
    
    return {
        "success": True,
        "knowledge_id": knowledge_id,
        "related_ids": related_ids,
        "relation_type": relation_type,
        "message": f"已建立 {len(related_ids)} 个关联关系",
        "related_at": datetime.now().isoformat()
    }
