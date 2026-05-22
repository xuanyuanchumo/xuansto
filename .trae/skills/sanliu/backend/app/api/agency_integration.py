from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any
from datetime import datetime
import uuid
import logging

router = APIRouter(prefix="/api/agency", tags=["Agency集成"])
logger = logging.getLogger(__name__)

class AgentInfo(BaseModel):
    agent_id: str
    name: str
    type: str
    status: str = Field(..., description="idle/busy/offline/error")
    capabilities: List[str]
    current_task: Optional[str] = None
    performance_score: float
    last_active: str

class AgentsListResponse(BaseModel):
    total_agents: int
    active_agents: int
    busy_agents: int
    agents: List[AgentInfo]

class RecommendRequest(BaseModel):
    task_description: str = Field(..., description="任务描述")
    required_capabilities: Optional[List[str]] = Field(default=None, description="所需能力列表")
    priority: Optional[str] = Field(default="medium", description="优先级: high/medium/low")
    exclude_agents: Optional[List[str]] = Field(default=None, description="排除的Agent列表")

class RecommendationItem(BaseModel):
    agent_id: str
    name: str
    match_score: float
    reasons: List[str]
    estimated_duration: Optional[str] = None
    current_workload: str

class RecommendResponse(BaseModel):
    task_id: str
    recommendations: List[RecommendationItem]
    total_evaluated: int
    generated_at: str

class InvokeRequest(BaseModel):
    agent_id: str = Field(..., description="目标Agent ID")
    task_type: str = Field(..., description="任务类型")
    payload: Dict[str, Any] = Field(..., description="任务载荷数据")
    priority: Optional[str] = Field(default="medium", description="优先级")
    timeout: Optional[int] = Field(default=300, description="超时时间(秒)")
    callback_url: Optional[str] = Field(default=None, description="回调地址")

class InvokeResponse(BaseModel):
    task_id: str
    agent_id: str
    status: str
    accepted: bool
    message: str
    estimated_completion: Optional[str] = None
    created_at: str

class TaskResultResponse(BaseModel):
    task_id: str
    agent_id: str
    status: str = Field(..., description="pending/running/completed/failed/cancelled")
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    started_at: str
    completed_at: Optional[str] = None
    duration_ms: Optional[float] = None
    logs: List[Dict[str, Any]]

_agents_registry: List[Dict[str, Any]] = [
    {
        "agent_id": "agent_code_gen_01",
        "name": "代码生成专家",
        "type": "code_generator",
        "status": "idle",
        "capabilities": ["code_generation", "refactoring", "documentation"],
        "current_task": None,
        "performance_score": 4.5,
        "last_active": datetime.now().isoformat()
    },
    {
        "agent_id": "agent_tester_01",
        "name": "测试工程师",
        "type": "tester",
        "status": "busy",
        "capabilities": ["unit_testing", "integration_testing", "mutation_testing"],
        "current_task": "task_003",
        "performance_score": 4.2,
        "last_active": datetime.now().isoformat()
    },
    {
        "agent_id": "agent_reviewer_01",
        "name": "代码审查员",
        "type": "reviewer",
        "status": "idle",
        "capabilities": ["code_review", "security_audit", "quality_check"],
        "current_task": None,
        "performance_score": 4.7,
        "last_active": (datetime.now().__sub__(__import__('datetime').timedelta(minutes=10))).isoformat()
    },
    {
        "agent_id": "agent_deployer_01",
        "name": "部署专家",
        "type": "deployer",
        "status": "idle",
        "capabilities": ["deployment", "ci_cd", "docker", "kubernetes"],
        "current_task": None,
        "performance_score": 4.0,
        "last_active": (datetime.now().__sub__(__import__('datetime').timedelta(hours=1))).isoformat()
    }
]

_tasks_store: Dict[str, Dict[str, Any]] = {}

@router.get("/agents", response_model=AgentsListResponse, summary="获取Agent列表")
async def get_agents(status: Optional[str] = None, capability: Optional[str] = None):
    filtered_agents = list(_agents_registry)
    
    if status:
        filtered_agents = [a for a in filtered_agents if a.get("status") == status]
    
    if capability:
        filtered_agents = [
            a for a in filtered_agents 
            if capability in a.get("capabilities", [])
        ]
    
    agents = [AgentInfo(**agent) for agent in filtered_agents]
    
    active_count = sum(1 for a in _agents_registry if a.get("status") != "offline")
    busy_count = sum(1 for a in _agents_registry if a.get("status") == "busy")
    
    return AgentsListResponse(
        total_agents=len(_agents_registry),
        active_agents=active_count,
        busy_agents=busy_count,
        agents=agents
    )

@router.post("/recommend", response_model=RecommendResponse, summary="获取Agent推荐")
async def recommend_agent(request: RecommendRequest):
    task_id = f"rec_{uuid.uuid4().hex[:8]}"
    
    exclude_set = set(request.exclude_agents or [])
    candidates = [
        a for a in _agents_registry 
        if a["agent_id"] not in exclude_set and a["status"] != "offline"
    ]
    
    recommendations = []
    
    for agent in candidates:
        match_score = 0.0
        reasons = []
        
        if request.required_capabilities:
            matched_caps = set(request.required_capabilities) & set(agent.get("capabilities", []))
            cap_score = len(matched_caps) / len(request.required_capabilities) if request.required_capabilities else 0
            match_score += cap_score * 0.5
            
            if matched_caps:
                reasons.append(f"能力匹配: {', '.join(matched_caps)}")
        
        perf_weight = agent.get("performance_score", 3.0) / 5.0
        match_score += perf_weight * 0.3
        reasons.append(f"性能评分: {agent.get('performance_score', 0):.1f}/5.0")
        
        if agent.get("status") == "idle":
            match_score += 0.2
            reasons.append("当前空闲，可立即执行")
        elif agent.get("status") == "busy":
            reasons.append("当前繁忙，可能需要等待")
        
        task_lower = request.task_description.lower()
        capabilities_str = ' '.join(agent.get("capabilities", [])).lower()
        keywords = ['code', 'test', 'deploy', 'review', 'security']
        for kw in keywords:
            if kw in task_lower and kw in capabilities_str:
                match_score += 0.05
                break
        
        workload = "空闲" if agent.get("status") == "idle" else f"正在处理 {agent.get('current_task', '未知任务')}"
        
        est_durations = {
            "code_generator": "5-15分钟",
            "tester": "10-30分钟",
            "reviewer": "5-20分钟",
            "deployer": "10-60分钟"
        }
        
        recommendations.append(RecommendationItem(
            agent_id=agent["agent_id"],
            name=agent["name"],
            match_score=round(min(1.0, match_score), 2),
            reasons=reasons,
            estimated_duration=est_durations.get(agent.get("type"), "待评估"),
            current_workload=workload
        ))
    
    recommendations.sort(key=lambda x: x.match_score, reverse=True)
    
    logger.info(f"生成推荐: {task_id}, 候选数: {len(candidates)}")
    
    return RecommendResponse(
        task_id=task_id,
        recommendations=recommendations[:5],
        total_evaluated=len(candidates),
        generated_at=datetime.now().isoformat()
    )

@router.post("/invoke", response_model=InvokeResponse, summary="调用Agent执行任务")
async def invoke_agent(request: InvokeRequest):
    task_id = f"task_{uuid.uuid4().hex[:8]}"
    
    target_agent = None
    for agent in _agents_registry:
        if agent["agent_id"] == request.agent_id:
            target_agent = agent
            break
    
    if not target_agent:
        raise HTTPException(status_code=404, detail=f"Agent {request.agent_id} 不存在")
    
    if target_agent.get("status") == "offline":
        raise HTTPException(status_code=400, detail=f"Agent {request.agent_id} 离线，无法接受任务")
    
    valid_types = ["code_generation", "testing", "review", "deployment", "analysis"]
    if request.task_type not in valid_types:
        raise HTTPException(status_code=400, detail=f"无效的任务类型，支持: {valid_types}")
    
    now = datetime.now()
    
    estimated_seconds = {
        "code_generation": 600,
        "testing": 1200,
        "review": 900,
        "deployment": 1800,
        "analysis": 300
    }.get(request.task_type, 600)
    
    from datetime import timedelta
    estimated_completion = now + timedelta(seconds=estimated_seconds)
    
    _tasks_store[task_id] = {
        "task_id": task_id,
        "agent_id": request.agent_id,
        "task_type": request.task_type,
        "payload": request.payload,
        "priority": request.priority or "medium",
        "status": "pending",
        "result": None,
        "error": None,
        "started_at": now.isoformat(),
        "completed_at": None,
        "logs": [
            {"timestamp": now.isoformat(), "level": "INFO", "message": f"任务已创建，等待Agent接受"}
        ],
        "callback_url": request.callback_url
    }
    
    if target_agent.get("status") == "idle":
        target_agent["status"] = "busy"
        target_agent["current_task"] = task_id
        target_agent["last_active"] = now.isoformat()
        
        _tasks_store[task_id]["status"] = "running"
        _tasks_store[task_id]["logs"].append({
            "timestamp": now.isoformat(),
            "level": "INFO",
            "message": f"Agent {target_agent['name']} 已接受任务"
        })
        
        accepted = True
        message = "任务已被Agent接受并开始执行"
    else:
        accepted = True
        message = "任务已加入队列，等待Agent完成当前任务后执行"
    
    logger.info(f"调用Agent: {request.agent_id}, 任务: {task_id}, 类型: {request.task_type}")
    
    return InvokeResponse(
        task_id=task_id,
        agent_id=request.agent_id,
        status=_tasks_store[task_id]["status"],
        accepted=accepted,
        message=message,
        estimated_completion=estimated_completion.isoformat(),
        created_at=now.isoformat()
    )

@router.get("/results/{task_id}", response_model=TaskResultResponse, summary="查询任务结果")
async def get_task_result(task_id: str):
    if task_id not in _tasks_store:
        raise HTTPException(status_code=404, detail=f"任务 {task_id} 不存在")
    
    task = _tasks_store[task_id]
    
    started_at = task.get("started_at", "")
    completed_at = task.get("completed_at")
    
    duration_ms = None
    if completed_at and started_at:
        start_dt = datetime.fromisoformat(started_at)
        end_dt = datetime.fromisoformat(completed_at)
        duration_ms = (end_dt - start_dt).total_seconds() * 1000
    
    result_data = task.get("result")
    if result_data and isinstance(result_data, dict):
        for key in ['api_key', 'password', 'secret', 'token']:
            if key in result_data and isinstance(result_data[key], str):
                value = result_data[key]
                if len(value) > 6:
                    result_data[key] = value[:3] + "*" * (len(value) - 6) + value[-3:]
    
    return TaskResultResponse(
        task_id=task_id,
        agent_id=task.get("agent_id", ""),
        status=task.get("status", "unknown"),
        result=result_data,
        error=task.get("error"),
        started_at=started_at,
        completed_at=completed_at,
        duration_ms=round(duration_ms, 1) if duration_ms else None,
        logs=task.get("logs", [])
    )
