from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, attributes, joinedload
from sqlalchemy import or_, desc, asc, func, case
from typing import List, Optional
from pydantic import BaseModel, Field
from datetime import datetime

from ..models.base import get_db
from ..models.project import Project, ProjectStatus
from ..models.task import Task, TaskStatus
from ..services.cache import cache_service, CacheKeys, invalidate_cache

router = APIRouter()

VALID_PROJECT_STATUSES = [s.value for s in ProjectStatus]

class ProjectCreate(BaseModel):
    name: str = Field(..., description="项目名称", min_length=1, max_length=200)
    description: Optional[str] = Field(None, description="项目描述")
    tech_stack: Optional[List[str]] = Field(None, description="技术栈列表")

class ProjectUpdate(BaseModel):
    name: Optional[str] = Field(None, description="项目名称", min_length=1, max_length=200)
    description: Optional[str] = Field(None, description="项目描述")
    tech_stack: Optional[List[str]] = Field(None, description="技术栈列表")
    status: Optional[str] = Field(None, description="项目状态")

class ProjectResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    tech_stack: Optional[List[str]]
    status: str
    status_history: Optional[List[dict]]
    milestones: Optional[List[dict]]
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True

class ProjectListResponse(BaseModel):
    items: List[ProjectResponse]
    total: int
    page: int
    page_size: int
    total_pages: int

class ProjectStatsResponse(BaseModel):
    project_id: int
    project_name: str
    status: str
    total_tasks: int
    completed_tasks: int
    pending_tasks: int
    in_progress_tasks: int
    review_tasks: int
    progress: float
    tasks_by_status: dict
    tasks: List[dict]

class TaskSummary(BaseModel):
    id: int
    title: str
    status: str
    priority: str
    estimated_hours: Optional[float]
    actual_hours: Optional[float]

class ProjectDetailResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    tech_stack: Optional[List[str]]
    status: str
    status_history: Optional[List[dict]]
    milestones: Optional[List[dict]]
    created_at: datetime
    updated_at: Optional[datetime]
    task_stats: Optional[dict]

    class Config:
        from_attributes = True

@router.post(
    "/",
    response_model=ProjectResponse,
    summary="创建项目",
    description="创建一个新的项目，可指定名称、描述、技术栈等信息",
    responses={
        201: {"description": "项目创建成功"},
        400: {"description": "请求参数无效"},
        409: {"description": "项目名称已存在"}
    }
)
def create_project(project: ProjectCreate, db: Session = Depends(get_db)):
    existing = db.query(Project).filter(Project.name == project.name).first()
    if existing:
        raise HTTPException(status_code=409, detail=f"Project with name '{project.name}' already exists")
    
    db_project = Project(**project.model_dump())
    db.add(db_project)
    db.commit()
    db.refresh(db_project)
    invalidate_cache("projects:*")
    return db_project

def _apply_project_filters(query, status: Optional[str], search: Optional[str]) -> any:
    if status:
        if status not in VALID_PROJECT_STATUSES:
            raise HTTPException(status_code=400, detail=f"Invalid status. Must be one of: {VALID_PROJECT_STATUSES}")
        query = query.filter(Project.status == status)
    
    if search:
        search_pattern = f"%{search}%"
        query = query.filter(
            or_(
                Project.name.ilike(search_pattern),
                Project.description.ilike(search_pattern)
            )
        )
    return query

def _get_task_counts_for_projects(db: Session, project_ids: List[int]) -> dict:
    if not project_ids:
        return {}
    
    task_counts = db.query(
        Task.project_id,
        func.count(Task.id).label('total'),
        func.sum(case((Task.status == TaskStatus.COMPLETED.value, 1), else_=0)).label('completed')
    ).filter(Task.project_id.in_(project_ids)).group_by(Task.project_id).all()
    
    return {t.project_id: {"total": t.total, "completed": t.completed or 0} for t in task_counts}

def _build_project_responses(projects: List, task_stats_map: dict) -> List[ProjectResponse]:
    project_responses = []
    for p in projects:
        stats = task_stats_map.get(p.id, {"total": 0, "completed": 0})
        project_dict = {
            "id": p.id,
            "name": p.name,
            "description": p.description,
            "tech_stack": p.tech_stack,
            "status": p.status,
            "status_history": p.status_history,
            "milestones": p.milestones,
            "created_at": p.created_at,
            "updated_at": p.updated_at,
            "task_stats": stats
        }
        project_responses.append(ProjectResponse(**project_dict))
    return project_responses

@router.get(
    "/",
    response_model=ProjectListResponse,
    summary="获取项目列表",
    description="获取项目列表，支持分页、状态筛选、搜索和排序",
    responses={
        200: {"description": "成功获取项目列表"}
    }
)
def list_projects(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(12, ge=1, le=100, description="每页数量"),
    status: Optional[str] = Query(None, description="状态筛选"),
    search: Optional[str] = Query(None, description="搜索关键词"),
    sort_by: str = Query("created_at", description="排序字段"),
    sort_order: str = Query("desc", description="排序方向 asc/desc"),
    db: Session = Depends(get_db)
):
    cache_key = CacheKeys.generate_key(
        CacheKeys.PROJECT_LIST,
        status=status or "all",
        page=page,
        page_size=page_size
    )
    cached = cache_service.get_json(cache_key)
    if cached:
        return ProjectListResponse(**cached)
    
    query = _apply_project_filters(db.query(Project), status, search)
    
    total = query.count()
    
    sort_column = getattr(Project, sort_by, Project.created_at)
    if sort_order == "desc":
        query = query.order_by(desc(sort_column))
    else:
        query = query.order_by(asc(sort_column))
    
    offset = (page - 1) * page_size
    projects = query.offset(offset).limit(page_size).all()
    
    task_stats_map = _get_task_counts_for_projects(db, [p.id for p in projects])
    project_responses = _build_project_responses(projects, task_stats_map)
    
    total_pages = (total + page_size - 1) // page_size
    
    result = ProjectListResponse(
        items=project_responses,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages
    )
    
    cache_service.set_json(cache_key, result.model_dump(), ttl=60)
    
    return result

@router.get(
    "/search",
    response_model=List[ProjectResponse],
    summary="搜索项目",
    description="根据关键词搜索项目名称和描述",
    responses={
        200: {"description": "成功搜索到项目"}
    }
)
def search_projects(
    q: str = Query(..., min_length=1, description="搜索关键词"),
    limit: int = Query(10, ge=1, le=50, description="返回数量限制"),
    db: Session = Depends(get_db)
):
    search_pattern = f"%{q}%"
    projects = db.query(Project).filter(
        or_(
            Project.name.ilike(search_pattern),
            Project.description.ilike(search_pattern)
        )
    ).limit(limit).all()
    
    return [ProjectResponse.model_validate(p) for p in projects]

@router.get(
    "/stats",
    summary="获取项目统计",
    description="获取所有项目的整体统计信息",
    responses={
        200: {"description": "成功获取统计信息"}
    }
)
def get_all_projects_stats(db: Session = Depends(get_db)):
    cache_key = CacheKeys.PROJECT_ALL_STATS
    cached = cache_service.get_json(cache_key)
    if cached:
        return cached
    
    total = db.query(func.count(Project.id)).scalar()
    
    status_counts = db.query(
        Project.status,
        func.count(Project.id)
    ).group_by(Project.status).all()
    
    status_distribution = {status: count for status, count in status_counts}
    
    result = {
        "total": total,
        "status_distribution": status_distribution
    }
    
    cache_service.set_json(cache_key, result, ttl=120)
    
    return result

@router.get(
    "/{project_id}",
    response_model=ProjectDetailResponse,
    summary="获取项目详情",
    description="根据项目ID获取项目的详细信息，包括任务统计",
    responses={
        200: {"description": "成功获取项目详情"},
        404: {"description": "项目不存在"}
    }
)
def get_project(project_id: int, db: Session = Depends(get_db)):
    cache_key = CacheKeys.generate_key(CacheKeys.PROJECT_DETAIL, project_id=project_id)
    cached = cache_service.get_json(cache_key)
    if cached:
        return ProjectDetailResponse(**cached)
    
    db_project = db.query(Project).filter(Project.id == project_id).first()
    if not db_project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    task_stats = db.query(
        func.count(Task.id).label('total'),
        func.sum(case((Task.status == TaskStatus.COMPLETED.value, 1), else_=0)).label('completed')
    ).filter(Task.project_id == project_id).first()
    
    result = ProjectDetailResponse(
        id=db_project.id,
        name=db_project.name,
        description=db_project.description,
        tech_stack=db_project.tech_stack,
        status=db_project.status,
        status_history=db_project.status_history,
        milestones=db_project.milestones,
        created_at=db_project.created_at,
        updated_at=db_project.updated_at,
        task_stats={
            "total": task_stats.total or 0,
            "completed": task_stats.completed or 0
        }
    )
    
    cache_service.set_json(cache_key, result.model_dump(), ttl=60)
    
    return result

def _get_tasks_by_status(db: Session, project_id: int) -> dict:
    status_counts = db.query(
        Task.status,
        func.count(Task.id)
    ).filter(Task.project_id == project_id).group_by(Task.status).all()
    
    return dict(status_counts)

def _build_task_list(db: Session, project_id: int) -> List[dict]:
    tasks = db.query(
        Task.id,
        Task.title,
        Task.status,
        Task.priority,
        Task.estimated_hours,
        Task.actual_hours
    ).filter(Task.project_id == project_id).all()
    
    return [
        {
            "id": t.id,
            "title": t.title,
            "status": t.status,
            "priority": t.priority,
            "estimated_hours": t.estimated_hours,
            "actual_hours": t.actual_hours
        }
        for t in tasks
    ]

@router.get(
    "/{project_id}/stats",
    response_model=ProjectStatsResponse,
    summary="获取项目统计",
    description="获取指定项目的详细统计信息，包括任务分布和进度",
    responses={
        200: {"description": "成功获取项目统计"},
        404: {"description": "项目不存在"}
    }
)
def get_project_stats(project_id: int, db: Session = Depends(get_db)):
    cache_key = CacheKeys.generate_key(CacheKeys.PROJECT_STATS, project_id=project_id)
    cached = cache_service.get_json(cache_key)
    if cached:
        return ProjectStatsResponse(**cached)
    
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    tasks_by_status = _get_tasks_by_status(db, project_id)
    total_tasks = sum(tasks_by_status.values())
    completed_tasks = tasks_by_status.get(TaskStatus.COMPLETED.value, 0)
    pending_tasks = tasks_by_status.get(TaskStatus.PENDING.value, 0)
    in_progress_tasks = tasks_by_status.get(TaskStatus.IN_PROGRESS.value, 0)
    review_tasks = tasks_by_status.get(TaskStatus.REVIEW.value, 0)
    
    progress = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
    
    task_list = _build_task_list(db, project_id)
    
    result = ProjectStatsResponse(
        project_id=project.id,
        project_name=project.name,
        status=project.status,
        total_tasks=total_tasks,
        completed_tasks=completed_tasks,
        pending_tasks=pending_tasks,
        in_progress_tasks=in_progress_tasks,
        review_tasks=review_tasks,
        progress=round(progress, 2),
        tasks_by_status={
            "PENDING": pending_tasks,
            "IN_PROGRESS": in_progress_tasks,
            "REVIEW": review_tasks,
            "COMPLETED": completed_tasks
        },
        tasks=task_list
    )
    
    cache_service.set_json(cache_key, result.model_dump(), ttl=60)
    
    return result

def _validate_project_update(db: Session, project_id: int, update_data: dict) -> None:
    if "name" in update_data:
        existing = db.query(Project).filter(
            Project.name == update_data["name"],
            Project.id != project_id
        ).first()
        if existing:
            raise HTTPException(status_code=409, detail=f"Project with name '{update_data['name']}' already exists")
    
    if "status" in update_data:
        if update_data["status"] not in VALID_PROJECT_STATUSES:
            raise HTTPException(status_code=400, detail=f"Invalid status. Must be one of: {VALID_PROJECT_STATUSES}")


def _update_status_history(db_project: Project, new_status: str) -> None:
    status_history = list(db_project.status_history or [])
    status_history.append({
        "status": new_status,
        "previous_status": db_project.status,
        "timestamp": datetime.utcnow().isoformat(),
        "comment": None
    })
    db_project.status_history = status_history
    attributes.flag_modified(db_project, "status_history")


@router.put(
    "/{project_id}",
    response_model=ProjectResponse,
    summary="更新项目",
    description="更新项目的基本信息，如名称、描述、技术栈等",
    responses={
        200: {"description": "项目更新成功"},
        404: {"description": "项目不存在"},
        409: {"description": "项目名称已存在"}
    }
)
def update_project(
    project_id: int,
    project_update: ProjectUpdate,
    db: Session = Depends(get_db)
):
    db_project = db.query(Project).filter(Project.id == project_id).first()
    if not db_project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    update_data = project_update.model_dump(exclude_unset=True)
    _validate_project_update(db, project_id, update_data)
    
    if "status" in update_data and update_data["status"] != db_project.status:
        _update_status_history(db_project, update_data["status"])
    
    for key, value in update_data.items():
        if key != "status_history":
            setattr(db_project, key, value)
    
    db.commit()
    db.refresh(db_project)
    
    invalidate_cache(f"projects:*")
    cache_service.delete(CacheKeys.generate_key(CacheKeys.PROJECT_DETAIL, project_id=project_id))
    cache_service.delete(CacheKeys.generate_key(CacheKeys.PROJECT_STATS, project_id=project_id))
    
    return db_project

@router.delete(
    "/{project_id}",
    summary="删除项目",
    description="删除指定的项目及其所有关联任务",
    responses={
        200: {"description": "项目删除成功"},
        404: {"description": "项目不存在"}
    }
)
def delete_project(project_id: int, db: Session = Depends(get_db)):
    db_project = db.query(Project).filter(Project.id == project_id).first()
    if not db_project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    task_count = db.query(func.count(Task.id)).filter(Task.project_id == project_id).scalar()
    
    db.query(Task).filter(Task.project_id == project_id).delete()
    
    db.delete(db_project)
    db.commit()
    
    invalidate_cache("projects:*")
    
    return {
        "message": "Project deleted successfully",
        "project_id": project_id,
        "deleted_tasks": task_count
    }

@router.get(
    "/{project_id}/status",
    summary="获取项目状态",
    description="获取项目的当前状态和任务完成情况",
    responses={
        200: {"description": "成功获取项目状态"},
        404: {"description": "项目不存在"}
    }
)
def get_project_status(project_id: int, db: Session = Depends(get_db)):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    status_counts = db.query(
        Task.status,
        func.count(Task.id)
    ).filter(Task.project_id == project_id).group_by(Task.status).all()
    
    tasks_by_status = dict(status_counts)
    
    return {
        "project": {
            "id": project.id,
            "name": project.name,
            "status": project.status,
            "status_history": project.status_history
        },
        "total_tasks": sum(tasks_by_status.values()),
        "completed_tasks": tasks_by_status.get(TaskStatus.COMPLETED.value, 0),
        "pending_tasks": tasks_by_status.get(TaskStatus.PENDING.value, 0),
        "in_progress_tasks": tasks_by_status.get(TaskStatus.IN_PROGRESS.value, 0),
    }
