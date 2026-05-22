from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime

from ..models.base import get_db
from ..models.code_change import CodeChange

router = APIRouter()

class CodeChangeCreate(BaseModel):
    skill_call_id: int
    file_path: str
    change_type: str
    content_before: Optional[str] = None
    content_after: Optional[str] = None
    diff: Optional[str] = None
    reason: Optional[str] = None
    related_task_id: Optional[int] = None

class CodeChangeResponse(BaseModel):
    id: int
    skill_call_id: int
    file_path: str
    change_type: str
    content_before: Optional[str]
    content_after: Optional[str]
    diff: Optional[str]
    reason: Optional[str]
    related_task_id: Optional[int]
    created_at: datetime

    class Config:
        from_attributes = True

@router.post("/", response_model=CodeChangeResponse)
def create_code_change(change: CodeChangeCreate, db: Session = Depends(get_db)):
    db_change = CodeChange(**change.model_dump())
    db.add(db_change)
    db.commit()
    db.refresh(db_change)
    return db_change

@router.get("/skill_call/{skill_call_id}", response_model=List[CodeChangeResponse])
def get_code_changes_by_skill_call(skill_call_id: int, db: Session = Depends(get_db)):
    return db.query(CodeChange).filter(CodeChange.skill_call_id == skill_call_id).all()

@router.get("/{change_id}", response_model=CodeChangeResponse)
def get_code_change(change_id: int, db: Session = Depends(get_db)):
    change = db.query(CodeChange).filter(CodeChange.id == change_id).first()
    if not change:
        raise HTTPException(status_code=404, detail="Code change not found")
    return change
