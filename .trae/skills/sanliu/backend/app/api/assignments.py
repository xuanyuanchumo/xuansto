from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
from pydantic import BaseModel, Field
from datetime import datetime

from ..models.base import get_db
from ..models.assignment import Assignment
from ..models.agent import Agent
from ..models.task import Task

router = APIRouter()

VALID_ASSIGNMENT_STATUSES = ["assigned", "in_progress", "completed", "cancelled"]

class AssignmentCreate(BaseModel):
    agent_id: int = Field(..., description="代理ID")
    task_id: Optional[int] = Field(None, description="任务ID")
    skill_call_id: Optional[int] = Field(None, description="技能调用ID")
    task_description: str = Field(..., description="任务描述", min_length=1, max_length=500)

class AssignmentUpdate(BaseModel):
    task_description: Optional[str] = Field(None, description="任务描述", min_length=1, max_length=500)
    status: Optional[str] = Field(None, description="状态: assigned, in_progress, completed, cancelled")

class AssignmentResponse(BaseModel):
    id: int
    agent_id: int
    task_id: Optional[int]
    skill_call_id: Optional[int]
    task_description: str
    status: str
    assigned_time: datetime
    completed_time: Optional[datetime]

    class Config:
        from_attributes = True

class AssignmentDetailResponse(AssignmentResponse):
    agent_name: Optional[str]
    task_title: Optional[str]
    duration_seconds: Optional[float]

class AssignmentStatsResponse(BaseModel):
    total: int
    by_status: dict
    active_assignments: int
    completed_today: int

@router.post("/", response_model=AssignmentResponse, summary="创建任务分配", description="将任务分配给代理执行")
def create_assignment(assignment: AssignmentCreate, db: Session = Depends(get_db)):
    agent = db.query(Agent).filter(Agent.id == assignment.agent_id).first()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    if assignment.task_id:
        task = db.query(Task).filter(Task.id == assignment.task_id).first()
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")
        
        existing = db.query(Assignment).filter(
            Assignment.task_id == assignment.task_id,
            Assignment.status.in_(["assigned", "in_progress"])
        ).first()
        if existing:
            raise HTTPException(status_code=400, detail="Task is already assigned")
    
    if agent.current_load >= agent.max_load:
        raise HTTPException(status_code=400, detail=f"Agent has reached maximum load ({agent.max_load})")
    
    db_assignment = Assignment(**assignment.model_dump())
    db.add(db_assignment)
    
    agent.current_load += 1
    agent.status = "busy"
    
    db.commit()
    db.refresh(db_assignment)
    return db_assignment

@router.get("/active", response_model=List[AssignmentResponse], summary="获取活跃分配", description="获取当前状态为assigned的所有任务分配")
def get_active_assignments(db: Session = Depends(get_db)):
    return db.query(Assignment).filter(Assignment.status == "assigned").all()

@router.get("/", response_model=List[AssignmentResponse], summary="获取分配列表", description="获取任务分配列表，支持按代理ID和状态筛选")
def list_assignments(
    agent_id: Optional[int] = Query(None, description="按代理ID筛选"),
    status: Optional[str] = Query(None, description="按状态筛选"),
    task_id: Optional[int] = Query(None, description="按任务ID筛选"),
    db: Session = Depends(get_db)
):
    query = db.query(Assignment)
    if agent_id:
        query = query.filter(Assignment.agent_id == agent_id)
    if status:
        if status not in VALID_ASSIGNMENT_STATUSES:
            raise HTTPException(status_code=400, detail=f"Invalid status. Must be one of: {VALID_ASSIGNMENT_STATUSES}")
        query = query.filter(Assignment.status == status)
    if task_id:
        query = query.filter(Assignment.task_id == task_id)
    return query.all()

@router.get("/stats", response_model=AssignmentStatsResponse, summary="获取分配统计", description="获取任务分配的整体统计信息")
def get_assignment_stats(db: Session = Depends(get_db)):
    total = db.query(func.count(Assignment.id)).scalar()
    
    status_counts = db.query(
        Assignment.status,
        func.count(Assignment.id)
    ).group_by(Assignment.status).all()
    by_status = {status: count for status, count in status_counts}
    
    active_assignments = by_status.get("assigned", 0) + by_status.get("in_progress", 0)
    
    today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    completed_today = db.query(func.count(Assignment.id)).filter(
        Assignment.status == "completed",
        Assignment.completed_time >= today_start
    ).scalar()
    
    return AssignmentStatsResponse(
        total=total,
        by_status=by_status,
        active_assignments=active_assignments,
        completed_today=completed_today
    )

@router.get("/{assignment_id}", response_model=AssignmentResponse, summary="获取分配详情", description="根据ID获取任务分配的详细信息")
def get_assignment(assignment_id: int, db: Session = Depends(get_db)):
    assignment = db.query(Assignment).filter(Assignment.id == assignment_id).first()
    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")
    return assignment

@router.get("/{assignment_id}/detail", response_model=AssignmentDetailResponse, summary="获取分配详细信息", description="获取分配的详细信息，包括代理名称、任务标题等")
def get_assignment_detail(assignment_id: int, db: Session = Depends(get_db)):
    assignment = db.query(Assignment).filter(Assignment.id == assignment_id).first()
    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")
    
    agent_name = None
    if assignment.agent_id:
        agent = db.query(Agent).filter(Agent.id == assignment.agent_id).first()
        if agent:
            agent_name = agent.name
    
    task_title = None
    if assignment.task_id:
        task = db.query(Task).filter(Task.id == assignment.task_id).first()
        if task:
            task_title = task.title
    
    duration_seconds = None
    if assignment.assigned_time and assignment.completed_time:
        duration_seconds = (assignment.completed_time - assignment.assigned_time).total_seconds()
    
    return AssignmentDetailResponse(
        id=assignment.id,
        agent_id=assignment.agent_id,
        task_id=assignment.task_id,
        skill_call_id=assignment.skill_call_id,
        task_description=assignment.task_description,
        status=assignment.status,
        assigned_time=assignment.assigned_time,
        completed_time=assignment.completed_time,
        agent_name=agent_name,
        task_title=task_title,
        duration_seconds=round(duration_seconds, 2) if duration_seconds else None
    )

@router.put("/{assignment_id}", response_model=AssignmentResponse, summary="更新分配", description="更新任务分配的信息")
def update_assignment(assignment_id: int, assignment_update: AssignmentUpdate, db: Session = Depends(get_db)):
    assignment = db.query(Assignment).filter(Assignment.id == assignment_id).first()
    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")
    
    update_data = assignment_update.model_dump(exclude_unset=True)
    
    if "status" in update_data:
        if update_data["status"] not in VALID_ASSIGNMENT_STATUSES:
            raise HTTPException(status_code=400, detail=f"Invalid status. Must be one of: {VALID_ASSIGNMENT_STATUSES}")
    
    for key, value in update_data.items():
        setattr(assignment, key, value)
    
    db.commit()
    db.refresh(assignment)
    return assignment

@router.put("/{assignment_id}/complete", response_model=AssignmentResponse, summary="完成任务分配", description="将指定的任务分配标记为已完成状态")
def complete_assignment(assignment_id: int, db: Session = Depends(get_db)):
    assignment = db.query(Assignment).filter(Assignment.id == assignment_id).first()
    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")
    
    if assignment.status not in ["assigned", "in_progress"]:
        raise HTTPException(status_code=400, detail=f"Cannot complete assignment with status '{assignment.status}'")
    
    assignment.status = "completed"
    assignment.completed_time = datetime.utcnow()
    
    agent = db.query(Agent).filter(Agent.id == assignment.agent_id).first()
    if agent:
        agent.current_load = max(0, agent.current_load - 1)
        if agent.current_load == 0:
            agent.status = "idle"
    
    if assignment.task_id:
        task = db.query(Task).filter(Task.id == assignment.task_id).first()
        if task and task.status != "COMPLETED":
            task.status = "COMPLETED"
            task.completed_at = datetime.utcnow()
    
    db.commit()
    db.refresh(assignment)
    return assignment

@router.put("/{assignment_id}/cancel", response_model=AssignmentResponse, summary="取消任务分配", description="取消指定的任务分配")
def cancel_assignment(assignment_id: int, db: Session = Depends(get_db)):
    assignment = db.query(Assignment).filter(Assignment.id == assignment_id).first()
    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")
    
    if assignment.status not in ["assigned", "in_progress"]:
        raise HTTPException(status_code=400, detail=f"Cannot cancel assignment with status '{assignment.status}'")
    
    assignment.status = "cancelled"
    
    agent = db.query(Agent).filter(Agent.id == assignment.agent_id).first()
    if agent:
        agent.current_load = max(0, agent.current_load - 1)
        if agent.current_load == 0:
            agent.status = "idle"
    
    db.commit()
    db.refresh(assignment)
    return assignment

@router.delete("/{assignment_id}", summary="删除分配", description="删除指定的任务分配记录（仅限已完成或已取消的记录）")
def delete_assignment(assignment_id: int, db: Session = Depends(get_db)):
    assignment = db.query(Assignment).filter(Assignment.id == assignment_id).first()
    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")
    
    if assignment.status in ["assigned", "in_progress"]:
        raise HTTPException(
            status_code=400,
            detail="Cannot delete active assignment. Complete or cancel it first."
        )
    
    db.delete(assignment)
    db.commit()
    return {"message": "Assignment deleted successfully", "assignment_id": assignment_id}
