from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
from pydantic import BaseModel, Field
from datetime import datetime

from ..models.base import get_db
from ..models.agent import Agent
from ..models.task import Task
from ..services import BaseCRUDService, StatusValidator, EntityValidator, StatsCalculator

router = APIRouter()
agent_service = BaseCRUDService(Agent)
status_validator = StatusValidator(["idle", "busy", "offline"])
validator = EntityValidator()

class AgentCreate(BaseModel):
    name: str = Field(..., description="代理名称", min_length=1, max_length=100)
    role: Optional[str] = Field(None, description="代理角色", max_length=100)
    skills: Optional[List[str]] = Field(None, description="代理技能列表")
    max_load: int = Field(5, description="最大负载", ge=1, le=20)
    department_id: Optional[int] = Field(None, description="所属部门ID")

class AgentUpdate(BaseModel):
    name: Optional[str] = Field(None, description="代理名称", min_length=1, max_length=100)
    role: Optional[str] = Field(None, description="代理角色", max_length=100)
    skills: Optional[List[str]] = Field(None, description="代理技能列表")
    status: Optional[str] = Field(None, description="代理状态: idle, busy, offline")
    current_load: Optional[int] = Field(None, description="当前负载", ge=0)
    current_task: Optional[str] = Field(None, description="当前任务描述", max_length=500)
    max_load: Optional[int] = Field(None, description="最大负载", ge=1, le=20)
    department_id: Optional[int] = Field(None, description="所属部门ID")

class AgentResponse(BaseModel):
    id: int
    name: str
    role: Optional[str]
    skills: Optional[List[str]]
    status: str
    current_load: int
    max_load: int
    current_task: Optional[str]
    department_id: Optional[int]
    last_heartbeat: datetime
    created_at: datetime

    class Config:
        from_attributes = True

class AgentDetailResponse(AgentResponse):
    assigned_tasks_count: int
    completed_tasks_count: int
    utilization_rate: float

class AgentStatsResponse(BaseModel):
    total: int
    idle: int
    busy: int
    offline: int
    avg_utilization: float

@router.post("/", response_model=AgentResponse, summary="创建代理", description="创建一个新的代理，可指定名称、角色、技能等信息")
def create_agent(agent: AgentCreate, db: Session = Depends(get_db)):
    agent_service.check_unique_name(db, agent.name, "Agent")
    return agent_service.create(db, agent)

@router.get("/", response_model=List[AgentResponse], summary="获取代理列表", description="获取代理列表，支持按状态和部门筛选")
def list_agents(
    status: Optional[str] = Query(None, description="按状态筛选: idle, busy, offline"),
    department_id: Optional[int] = Query(None, description="按部门ID筛选"),
    skill: Optional[str] = Query(None, description="按技能筛选"),
    db: Session = Depends(get_db)
):
    query = db.query(Agent)
    if status:
        status_validator.validate(status)
        query = query.filter(Agent.status == status)
    if department_id:
        query = query.filter(Agent.department_id == department_id)
    if skill:
        query = query.filter(Agent.skills.contains([skill]))
    return query.all()

@router.get("/stats", response_model=AgentStatsResponse, summary="获取代理统计", description="获取代理的整体统计信息")
def get_agent_stats(db: Session = Depends(get_db)):
    total = agent_service.count(db)
    idle = agent_service.count(db, filters={"status": "idle"})
    busy = agent_service.count(db, filters={"status": "busy"})
    offline = agent_service.count(db, filters={"status": "offline"})
    
    agents = agent_service.get_all(db)
    total_utilization = sum(
        (a.current_load / a.max_load * 100) if a.max_load > 0 else 0
        for a in agents
    )
    avg_utilization = StatsCalculator.calculate_percentage(total_utilization, total) if total > 0 else 0.0
    
    return AgentStatsResponse(
        total=total,
        idle=idle,
        busy=busy,
        offline=offline,
        avg_utilization=round(avg_utilization, 2)
    )

@router.get("/{agent_id}", response_model=AgentResponse, summary="获取代理详情", description="根据ID获取代理的详细信息")
def get_agent(agent_id: int, db: Session = Depends(get_db)):
    return agent_service.get_or_404(db, agent_id, "Agent")

@router.get("/{agent_id}/detail", response_model=AgentDetailResponse, summary="获取代理详细信息", description="获取代理的详细信息，包括任务统计")
def get_agent_detail(agent_id: int, db: Session = Depends(get_db)):
    db_agent = agent_service.get_or_404(db, agent_id, "Agent")
    
    assigned_tasks = db.query(func.count(Task.id)).filter(
        Task.agent_id == agent_id,
        Task.status.in_(["PENDING", "IN_PROGRESS", "REVIEW"])
    ).scalar()
    
    completed_tasks = db.query(func.count(Task.id)).filter(
        Task.agent_id == agent_id,
        Task.status == "COMPLETED"
    ).scalar()
    
    utilization_rate = StatsCalculator.calculate_percentage(
        db_agent.current_load, db_agent.max_load
    ) if db_agent.max_load > 0 else 0.0
    
    return AgentDetailResponse(
        id=db_agent.id,
        name=db_agent.name,
        role=db_agent.role,
        skills=db_agent.skills,
        status=db_agent.status,
        current_load=db_agent.current_load,
        max_load=db_agent.max_load,
        current_task=db_agent.current_task,
        department_id=db_agent.department_id,
        last_heartbeat=db_agent.last_heartbeat,
        created_at=db_agent.created_at,
        assigned_tasks_count=assigned_tasks,
        completed_tasks_count=completed_tasks,
        utilization_rate=round(utilization_rate, 2)
    )

@router.put("/{agent_id}", response_model=AgentResponse, summary="更新代理", description="更新代理的角色、技能、状态等信息")
def update_agent(agent_id: int, agent: AgentUpdate, db: Session = Depends(get_db)):
    from fastapi import HTTPException
    
    db_agent = agent_service.get_or_404(db, agent_id, "Agent")
    
    update_data = agent.model_dump(exclude_unset=True)
    
    if "status" in update_data:
        status_validator.validate(update_data["status"])
    
    if "name" in update_data:
        agent_service.check_unique_name(db, update_data["name"], "Agent", exclude_id=agent_id)
    
    if "current_load" in update_data:
        max_load = update_data.get("max_load", db_agent.max_load)
        if update_data["current_load"] > max_load:
            raise HTTPException(status_code=400, detail=f"Current load cannot exceed max load ({max_load})")
    
    return agent_service.update(db, db_agent, agent)

@router.delete("/{agent_id}", summary="删除代理", description="删除指定的代理（需确保无关联任务）")
def delete_agent(agent_id: int, db: Session = Depends(get_db)):
    from fastapi import HTTPException
    
    agent_service.get_or_404(db, agent_id, "Agent")
    
    assigned_tasks = db.query(Task).filter(
        Task.agent_id == agent_id,
        Task.status.in_(["PENDING", "IN_PROGRESS", "REVIEW"])
    ).count()
    
    if assigned_tasks > 0:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot delete agent. {assigned_tasks} active tasks are assigned to this agent"
        )
    
    agent_service.delete(db, agent_id)
    return {"message": "Agent deleted successfully", "agent_id": agent_id}

@router.post("/{agent_id}/heartbeat", summary="更新心跳", description="更新代理的心跳时间，用于存活检测")
def update_heartbeat(agent_id: int, db: Session = Depends(get_db)):
    db_agent = agent_service.get_or_404(db, agent_id, "Agent")
    
    db_agent.last_heartbeat = datetime.utcnow()
    db.commit()
    return {"message": "Heartbeat updated", "agent_id": agent_id, "timestamp": datetime.utcnow().isoformat()}
