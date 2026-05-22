from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime

from ..models.base import get_db
from ..models.project import Project, ProjectStatus, PROJECT_STATUS_TRANSITIONS
from ..models.task import Task, TaskStatus, TASK_STATUS_TRANSITIONS
from ..services.workflow import (
    StatusValidator,
    StateTransitionManager,
    StatusHistoryManager,
    WorkflowExecutor
)

router = APIRouter()


class StatusUpdateRequest(BaseModel):
    status: str
    operator: Optional[str] = None
    comment: Optional[str] = None


class StatusHistoryEntry(BaseModel):
    from_status: str
    to_status: str
    operator: Optional[str]
    comment: Optional[str]
    timestamp: str


class StatusHistoryResponse(BaseModel):
    entity_type: str
    entity_id: int
    history: List[StatusHistoryEntry]


class DependencyCheckRequest(BaseModel):
    task_id: int


class DependencyCheckResponse(BaseModel):
    task_id: int
    all_dependencies_completed: bool
    pending_dependencies: List[int]
    dependency_details: List[dict]


@router.put("/project/{project_id}/status")
def update_project_status(
    project_id: int,
    request: StatusUpdateRequest,
    db: Session = Depends(get_db)
):
    project = _get_project_or_raise(project_id, db)
    new_status = StatusValidator.validate_project_status(request.status)
    current_status = ProjectStatus(project.status)
    
    StatusValidator.validate_transition(
        current_status,
        new_status,
        PROJECT_STATUS_TRANSITIONS
    )
    
    StatusHistoryManager.add_status_history(
        project,
        project.status,
        new_status.value,
        request.operator,
        request.comment
    )
    
    project.status = new_status.value
    project.updated_at = datetime.now()
    
    db.commit()
    db.refresh(project)
    
    return {
        "id": project.id,
        "status": project.status,
        "message": f"Project status updated to {new_status.value}"
    }


@router.put("/task/{task_id}/status")
def update_task_status(
    task_id: int,
    request: StatusUpdateRequest,
    db: Session = Depends(get_db)
):
    task = _get_task_or_raise(task_id, db)
    new_status = StatusValidator.validate_task_status(request.status)
    current_status = TaskStatus(task.status)
    
    StatusValidator.validate_transition(
        current_status,
        new_status,
        TASK_STATUS_TRANSITIONS
    )
    
    StatusHistoryManager.add_status_history(
        task,
        task.status,
        new_status.value,
        request.operator,
        request.comment
    )
    
    task.status = new_status.value
    task.updated_at = datetime.now()
    
    if new_status == TaskStatus.COMPLETED:
        task.completed_at = datetime.now()
    
    db.commit()
    db.refresh(task)
    
    return {
        "id": task.id,
        "status": task.status,
        "message": f"Task status updated to {new_status.value}"
    }


@router.get("/history/{entity_type}/{entity_id}", response_model=StatusHistoryResponse)
def get_status_history(
    entity_type: str,
    entity_id: int,
    db: Session = Depends(get_db)
):
    StatusValidator.validate_entity_type(entity_type)
    
    entity = _get_entity_by_type(entity_type, entity_id, db)
    
    history = StatusHistoryManager.get_status_history(entity)
    
    return StatusHistoryResponse(
        entity_type=entity_type,
        entity_id=entity_id,
        history=[StatusHistoryEntry(**entry) for entry in history]
    )


@router.post("/task/check-dependencies", response_model=DependencyCheckResponse)
def check_task_dependencies(
    request: DependencyCheckRequest,
    db: Session = Depends(get_db)
):
    task = WorkflowExecutor.get_task_or_raise(request.task_id, db)
    
    result = WorkflowExecutor.check_dependencies(task, db)
    
    return DependencyCheckResponse(
        task_id=request.task_id,
        **result
    )


@router.get("/project/{project_id}/allowed-transitions")
def get_project_allowed_transitions(project_id: int, db: Session = Depends(get_db)):
    project = _get_project_or_raise(project_id, db)
    current_status = ProjectStatus(project.status)
    allowed = StateTransitionManager.get_project_transitions(current_status)
    
    return StateTransitionManager.format_transitions_response(
        current_status,
        allowed
    )


@router.get("/task/{task_id}/allowed-transitions")
def get_task_allowed_transitions(task_id: int, db: Session = Depends(get_db)):
    task = _get_task_or_raise(task_id, db)
    current_status = TaskStatus(task.status)
    allowed = StateTransitionManager.get_task_transitions(current_status)
    
    return StateTransitionManager.format_transitions_response(
        current_status,
        allowed
    )


def _get_project_or_raise(project_id: int, db: Session) -> Project:
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


def _get_task_or_raise(task_id: int, db: Session) -> Task:
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


def _get_entity_by_type(entity_type: str, entity_id: int, db: Session):
    if entity_type == "project":
        return _get_project_or_raise(entity_id, db)
    else:
        return _get_task_or_raise(entity_id, db)
