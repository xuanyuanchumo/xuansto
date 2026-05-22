from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime

from ..models.base import get_db
from ..models.input_output_trace import InputOutputTrace

router = APIRouter()

class IOTraceCreate(BaseModel):
    skill_call_id: int
    trace_type: str
    data: dict
    data_type: Optional[str] = None
    source: Optional[str] = None
    target: Optional[str] = None

class IOTraceResponse(BaseModel):
    id: int
    skill_call_id: int
    trace_type: str
    data: dict
    data_type: Optional[str]
    source: Optional[str]
    target: Optional[str]
    timestamp: datetime

    class Config:
        from_attributes = True

@router.post("/", response_model=IOTraceResponse)
def create_io_trace(trace: IOTraceCreate, db: Session = Depends(get_db)):
    db_trace = InputOutputTrace(**trace.model_dump())
    db.add(db_trace)
    db.commit()
    db.refresh(db_trace)
    return db_trace

@router.get("/skill_call/{skill_call_id}", response_model=List[IOTraceResponse])
def get_io_traces_by_skill_call(skill_call_id: int, trace_type: Optional[str] = None, db: Session = Depends(get_db)):
    query = db.query(InputOutputTrace).filter(InputOutputTrace.skill_call_id == skill_call_id)
    if trace_type:
        query = query.filter(InputOutputTrace.trace_type == trace_type)
    return query.all()

@router.get("/{trace_id}", response_model=IOTraceResponse)
def get_io_trace(trace_id: int, db: Session = Depends(get_db)):
    trace = db.query(InputOutputTrace).filter(InputOutputTrace.id == trace_id).first()
    if not trace:
        raise HTTPException(status_code=404, detail="IO trace not found")
    return trace
