from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload, selectinload
from sqlalchemy import func, case
from typing import List, Optional
from pydantic import BaseModel, Field
from datetime import datetime

from ..models.base import get_db
from ..models.task import Task, TaskStatus, TaskPriority
from ..models.agent import Agent
from ..models.project import Project
from ..models.department import Department
from ..services.cache import cache_service, CacheKeys, invalidate_cache

router = APIRouter()

class TaskCreate(BaseModel):
    title: str = Field(..., description="任务标题", min_length=1, max_length=200)
    description: Optional[str] = Field(None, description="任务描述")
    project_id: Optional[int] = Field(None, description="所属项目ID")
    department_id: Optional[int] = Field(None, description="所属部门ID")
    agent_id: Optional[int] = Field(None, description="分配的代理ID")
    required_skill: Optional[str] = Field(None, description="所需技能")
    priority: Optional[str] = Field("medium", description="优先级: high, medium, low")
    dependencies: Optional[List[int]] = Field(default_factory=list, description="依赖任务ID列表")
    estimated_hours: Optional[float] = Field(None, description="预估工时", ge=0)
    details: Optional[dict] = Field(None, description="任务详情")

class TaskUpdate(BaseModel):
    title: Optional[str] = Field(None, description="任务标题", min_length=1, max_length=200)
    description: Optional[str] = Field(None, description="任务描述")
    required_skill: Optional[str] = Field(None, description="所需技能")
    priority: Optional[str] = Field(None, description="优先级: high, medium, low")
    agent_id: Optional[int] = Field(None, description="分配的代理ID")
    dependencies: Optional[List[int]] = Field(None, description="依赖任务ID列表")
    estimated_hours: Optional[float] = Field(None, description="预估工时", ge=0)
    actual_hours: Optional[float] = Field(None, description="实际工时", ge=0)
    details: Optional[dict] = Field(None, description="任务详情")

class TaskResponse(BaseModel):
    id: int
    project_id: Optional[int]
    department_id: Optional[int]
    agent_id: Optional[int]
    title: str
    description: Optional[str]
    required_skill: Optional[str]
    priority: str
    status: str
    status_history: List[dict]
    dependencies: List[int]
    estimated_hours: Optional[float]
    actual_hours: Optional[float]
    details: Optional[dict]
    created_at: datetime
    updated_at: Optional[datetime]
    completed_at: Optional[datetime]

    class Config:
        from_attributes = True

class TaskDetailResponse(TaskResponse):
    agent: Optional[dict]
    dependencies_detail: List[dict]
    status_history_detail: List[dict]

class TaskSearchParams(BaseModel):
    keyword: Optional[str] = None
    status: Optional[str] = None
    priority: Optional[str] = None
    project_id: Optional[int] = None
    agent_id: Optional[int] = None

class TaskStatsResponse(BaseModel):
    total: int
    by_status: dict
    by_priority: dict
    completed_rate: float
    avg_estimated_hours: Optional[float]
    avg_actual_hours: Optional[float]

def _validate_task_relations(task: TaskCreate, db: Session) -> None:
    validations = []
    
    if task.project_id:
        validations.append(('Project', Project.id == task.project_id))
    if task.department_id:
        validations.append(('Department', Department.id == task.department_id))
    if task.agent_id:
        validations.append(('Agent', Agent.id == task.agent_id))
    
    for entity_name, condition in validations:
        model = Project if entity_name == 'Project' else Department if entity_name == 'Department' else Agent
        if not db.query(model).filter(condition).first():
            raise HTTPException(status_code=404, detail=f"{entity_name} not found")
    
    if task.priority and task.priority not in [p.value for p in TaskPriority]:
        raise HTTPException(status_code=400, detail=f"Invalid priority. Must be one of: {[p.value for p in TaskPriority]}")


def _prepare_task_data(task: TaskCreate) -> dict:
    task_data = task.model_dump()
    if task_data.get("priority") is None:
        task_data["priority"] = TaskPriority.MEDIUM.value
    return task_data


@router.post("/", response_model=TaskResponse, summary="创建任务", description="创建一个新的任务，可指定项目、部门、代理等信息")
def create_task(task: TaskCreate, db: Session = Depends(get_db)):
    _validate_task_relations(task, db)
    
    task_data = _prepare_task_data(task)
    db_task = Task(**task_data)
    db.add(db_task)
    db.commit()
    db.refresh(db_task)
    
    invalidate_cache("tasks:*")
    
    return db_task

@router.get("/", response_model=List[TaskResponse], summary="获取任务列表", description="获取所有任务列表")
def list_tasks(db: Session = Depends(get_db)):
    cache_key = CacheKeys.TASK_LIST.format(project_id="all")
    cached = cache_service.get_json(cache_key)
    if cached:
        return [TaskResponse(**t) for t in cached]
    
    tasks = db.query(Task).all()
    result = [TaskResponse.model_validate(t) for t in tasks]
    
    cache_service.set_json(cache_key, [t.model_dump() for t in result], ttl=60)
    
    return result

@router.get("/search", response_model=List[TaskResponse], summary="搜索任务", description="根据条件搜索任务")
def search_tasks(
    keyword: Optional[str] = Query(None, description="搜索关键词"),
    status: Optional[str] = Query(None, description="按状态筛选"),
    priority: Optional[str] = Query(None, description="按优先级筛选"),
    project_id: Optional[int] = Query(None, description="按项目ID筛选"),
    agent_id: Optional[int] = Query(None, description="按代理ID筛选"),
    db: Session = Depends(get_db)
):
    query = db.query(Task)
    
    if keyword:
        query = query.filter(
            (Task.title.ilike(f"%{keyword}%")) |
            (Task.description.ilike(f"%{keyword}%"))
        )
    
    if status:
        query = query.filter(Task.status == status)
    
    if priority:
        query = query.filter(Task.priority == priority)
    
    if project_id:
        query = query.filter(Task.project_id == project_id)
    
    if agent_id:
        query = query.filter(Task.agent_id == agent_id)
    
    return query.all()

def _get_task_status_counts(db: Session, project_id: Optional[int]) -> dict:
    status_counts = db.query(
        Task.status,
        func.count(Task.id)
    )
    if project_id:
        status_counts = status_counts.filter(Task.project_id == project_id)
    status_counts = status_counts.group_by(Task.status).all()
    return {status: count for status, count in status_counts}

def _get_task_priority_counts(db: Session, project_id: Optional[int]) -> dict:
    priority_counts = db.query(
        Task.priority,
        func.count(Task.id)
    )
    if project_id:
        priority_counts = priority_counts.filter(Task.project_id == project_id)
    priority_counts = priority_counts.group_by(Task.priority).all()
    return {priority: count for priority, count in priority_counts}

def _get_task_avg_hours(db: Session, project_id: Optional[int]) -> tuple:
    avg_stats = db.query(
        func.avg(Task.estimated_hours).label('avg_estimated'),
        func.avg(Task.actual_hours).label('avg_actual')
    )
    if project_id:
        avg_stats = avg_stats.filter(Task.project_id == project_id)
    return avg_stats.first()

@router.get("/stats", response_model=TaskStatsResponse, summary="获取任务统计", description="获取任务的统计信息")
def get_task_stats(
    project_id: Optional[int] = Query(None, description="按项目ID筛选"),
    db: Session = Depends(get_db)
):
    cache_key = CacheKeys.generate_key(CacheKeys.TASK_STATS, project_id=project_id or "all")
    cached = cache_service.get_json(cache_key)
    if cached:
        return TaskStatsResponse(**cached)
    
    base_query = db.query(Task)
    if project_id:
        base_query = base_query.filter(Task.project_id == project_id)
    
    total = base_query.count()
    
    by_status = _get_task_status_counts(db, project_id)
    by_priority = _get_task_priority_counts(db, project_id)
    
    completed_count = by_status.get(TaskStatus.COMPLETED.value, 0)
    completed_rate = (completed_count / total * 100) if total > 0 else 0
    
    avg_stats = _get_task_avg_hours(db, project_id)
    
    result = TaskStatsResponse(
        total=total,
        by_status=by_status,
        by_priority=by_priority,
        completed_rate=round(completed_rate, 2),
        avg_estimated_hours=round(avg_stats.avg_estimated, 2) if avg_stats.avg_estimated else None,
        avg_actual_hours=round(avg_stats.avg_actual, 2) if avg_stats.avg_actual else None
    )
    
    cache_service.set_json(cache_key, result.model_dump(), ttl=60)
    
    return result

@router.get("/project/{project_id}", response_model=List[TaskResponse], summary="获取项目任务", description="获取指定项目的所有任务")
def get_project_tasks(project_id: int, db: Session = Depends(get_db)):
    cache_key = CacheKeys.generate_key(CacheKeys.TASK_LIST, project_id=project_id)
    cached = cache_service.get_json(cache_key)
    if cached:
        return [TaskResponse(**t) for t in cached]
    
    tasks = db.query(Task).filter(Task.project_id == project_id).all()
    result = [TaskResponse.model_validate(t) for t in tasks]
    
    cache_service.set_json(cache_key, [t.model_dump() for t in result], ttl=60)
    
    return result

def _get_agent_info(db: Session, agent_id: Optional[int]) -> Optional[dict]:
    if not agent_id:
        return None
    
    agent = db.query(Agent).filter(Agent.id == agent_id).first()
    if agent:
        return {
            "id": agent.id,
            "name": agent.name,
            "role": agent.role,
            "status": agent.status
        }
    return None

def _get_dependencies_detail(db: Session, dependencies: Optional[List[int]]) -> List[dict]:
    if not dependencies:
        return []
    
    dep_tasks = db.query(
        Task.id,
        Task.title,
        Task.status
    ).filter(Task.id.in_(dependencies)).all()
    
    return [
        {
            "id": t.id,
            "title": t.title,
            "status": t.status
        }
        for t in dep_tasks
    ]

@router.get("/{task_id}", response_model=TaskDetailResponse, summary="获取任务详情", description="根据任务ID获取任务的详细信息，包括代理信息、依赖详情等")
def get_task_detail(task_id: int, db: Session = Depends(get_db)):
    cache_key = CacheKeys.generate_key(CacheKeys.TASK_DETAIL, task_id=task_id)
    cached = cache_service.get_json(cache_key)
    if cached:
        return TaskDetailResponse(**cached)
    
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    agent_info = _get_agent_info(db, task.agent_id)
    dependencies_detail = _get_dependencies_detail(db, task.dependencies)
    
    result = TaskDetailResponse(
        id=task.id,
        project_id=task.project_id,
        department_id=task.department_id,
        agent_id=task.agent_id,
        title=task.title,
        description=task.description,
        required_skill=task.required_skill,
        priority=task.priority,
        status=task.status,
        status_history=task.status_history or [],
        dependencies=task.dependencies or [],
        estimated_hours=task.estimated_hours,
        actual_hours=task.actual_hours,
        details=task.details,
        created_at=task.created_at,
        updated_at=task.updated_at,
        completed_at=task.completed_at,
        agent=agent_info,
        dependencies_detail=dependencies_detail,
        status_history_detail=task.status_history or []
    )
    
    cache_service.set_json(cache_key, result.model_dump(), ttl=60)
    
    return result


def _validate_task_update(update_data: dict, task_id: int, db: Session) -> None:
    if "priority" in update_data and update_data["priority"] not in [p.value for p in TaskPriority]:
        raise HTTPException(status_code=400, detail=f"Invalid priority. Must be one of: {[p.value for p in TaskPriority]}")
    
    if "agent_id" in update_data and update_data["agent_id"] is not None:
        agent = db.query(Agent).filter(Agent.id == update_data["agent_id"]).first()
        if not agent:
            raise HTTPException(status_code=404, detail="Agent not found")
    
    if "dependencies" in update_data:
        for dep_id in update_data["dependencies"]:
            dep_task = db.query(Task).filter(Task.id == dep_id).first()
            if not dep_task:
                raise HTTPException(status_code=400, detail=f"Dependency task {dep_id} not found")
            if dep_id == task_id:
                raise HTTPException(status_code=400, detail="Task cannot depend on itself")


@router.put("/{task_id}", response_model=TaskResponse, summary="更新任务", description="更新任务的基本信息，如标题、描述、优先级等")
def update_task(task_id: int, task_update: TaskUpdate, db: Session = Depends(get_db)):
    db_task = db.query(Task).filter(Task.id == task_id).first()
    if not db_task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    update_data = task_update.model_dump(exclude_unset=True)
    _validate_task_update(update_data, task_id, db)
    
    for key, value in update_data.items():
        setattr(db_task, key, value)
    
    db.commit()
    db.refresh(db_task)
    
    invalidate_cache("tasks:*")
    cache_service.delete(CacheKeys.generate_key(CacheKeys.TASK_DETAIL, task_id=task_id))
    
    return db_task


@router.delete("/{task_id}", summary="删除任务", description="删除指定的任务（需确保任务无依赖关系）")
def delete_task(task_id: int, db: Session = Depends(get_db)):
    db_task = db.query(Task).filter(Task.id == task_id).first()
    if not db_task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    dependent_tasks = db.query(Task).filter(Task.dependencies.contains([task_id])).all()
    if dependent_tasks:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot delete task. It is a dependency of tasks: {[t.id for t in dependent_tasks]}"
        )
    
    db.delete(db_task)
    db.commit()
    
    invalidate_cache("tasks:*")
    cache_service.delete(CacheKeys.generate_key(CacheKeys.TASK_DETAIL, task_id=task_id))
    
    return {"message": "Task deleted successfully", "task_id": task_id}
