from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime

from ..models.base import get_db
from ..models.clarification_question import ClarificationQuestion

router = APIRouter()

class ClarificationQuestionCreate(BaseModel):
    project_id: int
    question: str
    question_type: Optional[str] = None
    context: Optional[str] = None

class ClarificationQuestionAnswer(BaseModel):
    answer: str
    answered_by: str

class ClarificationQuestionResponse(BaseModel):
    id: int
    project_id: int
    question: str
    question_type: Optional[str]
    context: Optional[str]
    answer: Optional[str]
    answered_by: Optional[str]
    answered_at: Optional[datetime]
    status: str
    created_at: datetime

    class Config:
        from_attributes = True

@router.post("/", response_model=ClarificationQuestionResponse)
def create_question(question: ClarificationQuestionCreate, db: Session = Depends(get_db)):
    db_question = ClarificationQuestion(**question.model_dump())
    db.add(db_question)
    db.commit()
    db.refresh(db_question)
    return db_question

@router.get("/project/{project_id}", response_model=List[ClarificationQuestionResponse])
def get_questions_by_project(project_id: int, status: Optional[str] = None, db: Session = Depends(get_db)):
    query = db.query(ClarificationQuestion).filter(ClarificationQuestion.project_id == project_id)
    if status:
        query = query.filter(ClarificationQuestion.status == status)
    return query.all()

@router.put("/{question_id}/answer", response_model=ClarificationQuestionResponse)
def answer_question(question_id: int, answer_data: ClarificationQuestionAnswer, db: Session = Depends(get_db)):
    question = db.query(ClarificationQuestion).filter(ClarificationQuestion.id == question_id).first()
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")
    question.answer = answer_data.answer
    question.answered_by = answer_data.answered_by
    question.answered_at = datetime.now()
    question.status = "answered"
    db.commit()
    db.refresh(question)
    return question

@router.put("/{question_id}/confirm", response_model=ClarificationQuestionResponse)
def confirm_question(question_id: int, confirmed_by: str, db: Session = Depends(get_db)):
    question = db.query(ClarificationQuestion).filter(ClarificationQuestion.id == question_id).first()
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")
    if question.status != "answered":
        raise HTTPException(status_code=400, detail="Question must be answered first")
    question.confirmed_by = confirmed_by
    question.confirmed_at = datetime.now()
    question.status = "confirmed"
    db.commit()
    db.refresh(question)
    return question
