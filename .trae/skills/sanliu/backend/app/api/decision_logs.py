from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime

from ..models.base import get_db
from ..models.decision_log import DecisionLog
from ..services import BaseCRUDService

router = APIRouter()
decision_log_service = BaseCRUDService(DecisionLog)

class DecisionLogCreate(BaseModel):
    skill_call_id: int
    decision_type: str
    decision_basis: Optional[dict] = None
    reasoning_process: Optional[str] = None
    alternatives: Optional[dict] = None
    final_decision: Optional[str] = None

class DecisionLogResponse(BaseModel):
    id: int
    skill_call_id: int
    decision_type: str
    decision_basis: Optional[dict]
    reasoning_process: Optional[str]
    alternatives: Optional[dict]
    final_decision: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True

@router.post("/", response_model=DecisionLogResponse)
def create_decision_log(log: DecisionLogCreate, db: Session = Depends(get_db)):
    return decision_log_service.create(db, log)

@router.get("/skill_call/{skill_call_id}", response_model=List[DecisionLogResponse])
def get_decision_logs_by_skill_call(skill_call_id: int, db: Session = Depends(get_db)):
    return decision_log_service.get_multi(db, filters={"skill_call_id": skill_call_id}, limit=1000)

@router.get("/{log_id}", response_model=DecisionLogResponse)
def get_decision_log(log_id: int, db: Session = Depends(get_db)):
    return decision_log_service.get_or_404(db, log_id, "Decision log")
