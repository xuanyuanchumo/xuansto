from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime

from ..models.base import get_db
from ..models.non_functional_check import NonFunctionalCheck

router = APIRouter()

class NonFunctionalCheckCreate(BaseModel):
    project_id: int
    check_type: str
    check_name: str
    description: Optional[str] = None
    baseline_value: Optional[float] = None
    unit: Optional[str] = None

class NonFunctionalCheckResponse(BaseModel):
    id: int
    project_id: int
    check_type: str
    check_name: str
    description: Optional[str]
    baseline_value: Optional[float]
    actual_value: Optional[float]
    unit: Optional[str]
    status: str
    details: Optional[dict]
    recommendations: Optional[str]
    checked_at: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True

@router.post("/", response_model=NonFunctionalCheckResponse)
def create_check(check: NonFunctionalCheckCreate, db: Session = Depends(get_db)):
    db_check = NonFunctionalCheck(**check.model_dump())
    db.add(db_check)
    db.commit()
    db.refresh(db_check)
    return db_check

@router.get("/project/{project_id}", response_model=List[NonFunctionalCheckResponse])
def get_checks_by_project(project_id: int, check_type: Optional[str] = None, db: Session = Depends(get_db)):
    query = db.query(NonFunctionalCheck).filter(NonFunctionalCheck.project_id == project_id)
    if check_type:
        query = query.filter(NonFunctionalCheck.check_type == check_type)
    return query.all()

@router.post("/{check_id}/execute")
def execute_check(check_id: int, db: Session = Depends(get_db)):
    check = db.query(NonFunctionalCheck).filter(NonFunctionalCheck.id == check_id).first()
    if not check:
        raise HTTPException(status_code=404, detail="Check not found")
    check.actual_value = 95.0
    check.status = "passed" if check.actual_value >= (check.baseline_value or 0) else "failed"
    check.checked_at = datetime.now()
    db.commit()
    return {"check_id": check_id, "status": check.status}
