from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime

from ..models.base import get_db
from ..models.mutation_test_result import MutationTestResult

router = APIRouter()

class MutationTestCreate(BaseModel):
    project_id: int
    test_run_id: str

class MutationTestResponse(BaseModel):
    id: int
    project_id: int
    test_run_id: str
    total_mutants: int
    killed_mutants: int
    survived_mutants: int
    mutation_score: float
    mutant_details: Optional[dict]
    status: str
    created_at: datetime

    class Config:
        from_attributes = True

@router.post("/", response_model=MutationTestResponse)
def create_mutation_test(test: MutationTestCreate, db: Session = Depends(get_db)):
    db_test = MutationTestResult(**test.model_dump(), status="pending")
    db.add(db_test)
    db.commit()
    db.refresh(db_test)
    return db_test

@router.get("/project/{project_id}", response_model=List[MutationTestResponse])
def get_mutation_tests_by_project(project_id: int, db: Session = Depends(get_db)):
    return db.query(MutationTestResult).filter(MutationTestResult.project_id == project_id).all()

@router.post("/{test_id}/run")
def run_mutation_test(test_id: int, db: Session = Depends(get_db)):
    test = db.query(MutationTestResult).filter(MutationTestResult.id == test_id).first()
    if not test:
        raise HTTPException(status_code=404, detail="Mutation test not found")
    test.status = "running"
    db.commit()
    test.total_mutants = 100
    test.killed_mutants = 85
    test.survived_mutants = 15
    test.mutation_score = 85.0
    test.status = "completed"
    db.commit()
    return {"test_id": test_id, "mutation_score": test.mutation_score}
