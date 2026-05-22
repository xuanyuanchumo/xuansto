from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any
from datetime import datetime
import logging

router = APIRouter(prefix="/api/resources", tags=["资源协调"])
logger = logging.getLogger(__name__)

class ResourceRegisterRequest(BaseModel):
    resource_id: str = Field(..., description="资源唯一标识")
    resource_type: str = Field(..., description="资源类型: file/api/compute/terminal/secret")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="资源元数据")

class ResourceRegisterResponse(BaseModel):
    success: bool
    message: str
    resource_id: str

class LockAcquireRequest(BaseModel):
    agent_id: str = Field(..., description="请求锁的Agent ID")
    lock_type: str = Field(..., description="锁类型: shared/exclusive")
    mode: Optional[str] = Field(default="optimistic", description="获取模式: optimistic/pessimistic")
    timeout: Optional[float] = Field(default=30.0, description="超时时间(秒)")

class LockAcquireResponse(BaseModel):
    success: bool
    token_id: Optional[str] = None
    message: str
    acquired_at: Optional[str] = None
    expires_at: Optional[str] = None

class ResourceStatusResponse(BaseModel):
    resource_id: str
    resource_type: str
    is_active: bool
    current_locks: List[Dict[str, Any]]
    lock_holders: List[str]

class DeadlockDetectionResponse(BaseModel):
    has_deadlock_risk: bool
    risks: List[Dict[str, Any]]
    detected_at: str
    recommendations: List[str]

class QueueStatusResponse(BaseModel):
    waiting_count: int
    high_priority: int
    medium_priority: int
    low_priority: int
    queue_items: List[Dict[str, Any]]

class QuotaInfoResponse(BaseModel):
    agent_id: str
    cpu_percent: float
    memory_percent: float
    files_percent: float
    api_percent: float
    is_within_limits: bool
    warnings: List[str]

_resource_registry: Dict[str, Dict[str, Any]] = {}
_locks: Dict[str, List[Dict[str, Any]]] = {}
_queue: List[Dict[str, Any]] = []
_quotas: Dict[str, Dict[str, Any]] = {}

@router.post("/register", response_model=ResourceRegisterResponse, summary="注册新资源")
async def register_resource(request: ResourceRegisterRequest):
    if request.resource_id in _resource_registry:
        raise HTTPException(status_code=400, detail=f"资源 {request.resource_id} 已存在")
    
    valid_types = ["file", "api", "compute", "terminal", "secret"]
    if request.resource_type not in valid_types:
        raise HTTPException(status_code=400, detail=f"无效的资源类型，支持: {valid_types}")
    
    _resource_registry[request.resource_id] = {
        "resource_id": request.resource_id,
        "resource_type": request.resource_type,
        "metadata": request.metadata or {},
        "is_active": True,
        "created_at": datetime.now().isoformat()
    }
    
    logger.info(f"注册资源: {request.resource_id} (类型: {request.resource_type})")
    
    return ResourceRegisterResponse(
        success=True,
        message="资源注册成功",
        resource_id=request.resource_id
    )

@router.post("/{resource_id}/lock", response_model=LockAcquireResponse, summary="获取资源锁")
async def acquire_lock(resource_id: str, request: LockAcquireRequest):
    import uuid
    
    if resource_id not in _resource_registry:
        raise HTTPException(status_code=404, detail=f"资源 {resource_id} 未注册")
    
    if request.lock_type not in ["shared", "exclusive"]:
        raise HTTPException(status_code=400, detail="锁类型必须是 shared 或 exclusive")
    
    resource_info = _resource_registry[resource_id]
    
    if resource_id not in _locks:
        _locks[resource_id] = []
    
    existing_locks = _locks[resource_id]
    
    has_writer = any(l["lock_type"] == "exclusive" for l in existing_locks)
    reader_count = sum(1 for l in existing_locks if l["lock_type"] == "shared")
    
    if request.lock_type == "exclusive":
        if has_writer or reader_count > 0:
            if request.mode == "pessimistic":
                return LockAcquireResponse(
                    success=False,
                    token_id=None,
                    message="资源被占用，无法获取独占锁"
                )
            return LockAcquireResponse(
                success=False,
                token_id=None,
                message="资源被占用，已加入等待队列"
            )
    
    elif request.lock_type == "shared":
        if has_writer:
            if request.mode == "pessimistic":
                return LockAcquireResponse(
                    success=False,
                    token_id=None,
                    message="资源被写锁占用，无法获取读锁"
                )
            return LockAcquireResponse(
                success=False,
                token_id=None,
                message="资源被写锁占用，已加入等待队列"
            )
    
    token_id = str(uuid.uuid4())[:8]
    now = datetime.now()
    expires_at = now.timestamp() + request.timeout
    
    lock_entry = {
        "token_id": token_id,
        "agent_id": request.agent_id,
        "lock_type": request.lock_type,
        "acquired_at": now.isoformat(),
        "expires_at": datetime.fromtimestamp(expires_at).isoformat()
    }
    
    _locks[resource_id].append(lock_entry)
    
    logger.info(f"Agent {request.agent_id} 获取{request.lock_type}锁: {token_id} on {resource_id}")
    
    return LockAcquireResponse(
        success=True,
        token_id=token_id,
        message="锁获取成功",
        acquired_at=now.isoformat(),
        expires_at=datetime.fromtimestamp(expires_at).isoformat()
    )

@router.get("/{resource_id}/status", response_model=ResourceStatusResponse, summary="查询资源状态")
async def get_resource_status(resource_id: str):
    if resource_id not in _resource_registry:
        raise HTTPException(status_code=404, detail=f"资源 {resource_id} 未注册")
    
    resource = _resource_registry[resource_id]
    current_locks = _locks.get(resource_id, [])
    lock_holders = list(set(l["agent_id"] for l in current_locks))
    
    return ResourceStatusResponse(
        resource_id=resource_id,
        resource_type=resource["resource_type"],
        is_active=resource["is_active"],
        current_locks=current_locks,
        lock_holders=lock_holders
    )

@router.get("/deadlock/detect", response_model=DeadlockDetectionResponse, summary="死锁检测")
async def detect_deadlock():
    risks = []
    wait_graph: Dict[str, set] = {}
    
    for resource_id, locks in _locks.items():
        holders = set(l["agent_id"] for l in locks)
        for agent in holders:
            if agent not in wait_graph:
                wait_graph[agent] = set()
            wait_graph[agent].update(holders - {agent})
    
    visited = set()
    rec_stack = set()
    
    def dfs(agent: str, path: List[str]) -> bool:
        visited.add(agent)
        rec_stack.add(agent)
        path.append(agent)
        
        for waiting_for in wait_graph.get(agent, set()):
            if waiting_for not in visited:
                if dfs(waiting_for, path):
                    return True
            elif waiting_for in rec_stack:
                cycle = path[path.index(waiting_for):] + [waiting_for]
                risks.append({
                    "level": "HIGH",
                    "agents": cycle.copy(),
                    "cycle_length": len(cycle)
                })
                return True
        
        path.pop()
        rec_stack.discard(agent)
        return False
    
    for agent in list(wait_graph.keys()):
        if agent not in visited:
            dfs(agent, [])
    
    recommendations = []
    if risks:
        recommendations.append("建议释放部分锁以解除循环等待")
        recommendations.append("考虑使用统一的资源获取顺序")
    
    return DeadlockDetectionResponse(
        has_deadlock_risk=len(risks) > 0,
        risks=risks,
        detected_at=datetime.now().isoformat(),
        recommendations=recommendations
    )

@router.get("/queue", response_model=QueueStatusResponse, summary="队列状态查询")
async def get_queue_status():
    from collections import Counter
    
    priority_counts = Counter(item.get("priority", "medium") for item in _queue)
    
    return QueueStatusResponse(
        waiting_count=len(_queue),
        high_priority=priority_counts.get("high", 0),
        medium_priority=priority_counts.get("medium", 0),
        low_priority=priority_counts.get("low", 0),
        queue_items=_queue[:20]
    )

@router.get("/quota/{agent_id}", response_model=QuotaInfoResponse, summary="配额查询")
async def get_agent_quota(agent_id: str):
    if agent_id not in _quotas:
        _quotas[agent_id] = {
            "cpu_percent": 0.0,
            "memory_percent": 0.0,
            "files_percent": 0.0,
            "api_percent": 0.0,
            "max_files": 10,
            "max_api_calls": 5,
            "current_files": 0,
            "current_api_calls": 0
        }
    
    quota = _quotas[agent_id]
    warnings = []
    
    if quota["files_percent"] > 80:
        warnings.append(f"文件锁使用率过高: {quota['files_percent']:.1f}%")
    if quota["api_percent"] > 80:
        warnings.append(f"API调用使用率过高: {quota['api_percent']:.1f}%")
    if quota["cpu_percent"] > 90:
        warnings.append(f"CPU使用率接近上限: {quota['cpu_percent']:.1f}%")
    
    is_within_limits = (
        quota["files_percent"] < 100 and
        quota["api_percent"] < 100 and
        quota["cpu_percent"] < 100 and
        quota["memory_percent"] < 100
    )
    
    return QuotaInfoResponse(
        agent_id=agent_id,
        cpu_percent=quota["cpu_percent"],
        memory_percent=quota["memory_percent"],
        files_percent=quota["files_percent"],
        api_percent=quota["api_percent"],
        is_within_limits=is_within_limits,
        warnings=warnings
    )
