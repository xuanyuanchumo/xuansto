from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime

from ..models.base import get_db
from ..models.milestone import Milestone, MilestoneStatus
from ..models.project import Project
from ..services import BaseCRUDService, EntityValidator, APIResponseBuilder

router = APIRouter()
milestone_service = BaseCRUDService(Milestone)
validator = EntityValidator()

class MilestoneCreate(BaseModel):
    project_id: int
    name: str
    description: Optional[str] = None
    planned_date: Optional[datetime] = None

class MilestoneUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    planned_date: Optional[datetime] = None
    status: Optional[str] = None

class MilestoneResponse(BaseModel):
    id: int
    project_id: int
    name: str
    description: Optional[str]
    planned_date: Optional[datetime]
    completed_date: Optional[datetime]
    status: str
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True

@router.post("/", response_model=MilestoneResponse)
def create_milestone(milestone: MilestoneCreate, db: Session = Depends(get_db)):
    validator.check_exists(db, Project, milestone.project_id, "Project")
    return milestone_service.create(db, milestone)

@router.get("/", response_model=List[MilestoneResponse])
def list_milestones(db: Session = Depends(get_db)):
    return milestone_service.get_all(db)

@router.get("/{milestone_id}", response_model=MilestoneResponse)
def get_milestone(milestone_id: int, db: Session = Depends(get_db)):
    return milestone_service.get_or_404(db, milestone_id, "Milestone")

@router.put("/{milestone_id}", response_model=MilestoneResponse)
def update_milestone(milestone_id: int, milestone: MilestoneUpdate, db: Session = Depends(get_db)):
    db_milestone = milestone_service.get_or_404(db, milestone_id, "Milestone")
    return milestone_service.update(db, db_milestone, milestone)

@router.delete("/{milestone_id}")
def delete_milestone(milestone_id: int, db: Session = Depends(get_db)):
    milestone_service.delete(db, milestone_id)
    return APIResponseBuilder.deleted("Milestone", milestone_id)

@router.put("/{milestone_id}/complete", response_model=MilestoneResponse)
def complete_milestone(milestone_id: int, db: Session = Depends(get_db)):
    db_milestone = milestone_service.get_or_404(db, milestone_id, "Milestone")
    
    db_milestone.status = MilestoneStatus.COMPLETED.value
    db_milestone.completed_date = datetime.utcnow()
    db.commit()
    db.refresh(db_milestone)
    return db_milestone

@router.get("/project/{project_id}", response_model=List[MilestoneResponse])
def get_project_milestones(project_id: int, db: Session = Depends(get_db)):
    validator.check_exists(db, Project, project_id, "Project")
    return milestone_service.get_multi(db, filters={"project_id": project_id}, limit=1000)
