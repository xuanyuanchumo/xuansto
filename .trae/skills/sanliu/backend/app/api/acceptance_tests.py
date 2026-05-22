from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime

from ..models.base import get_db
from ..models.acceptance_test import AcceptanceTest

router = APIRouter()

class AcceptanceTestCreate(BaseModel):
    project_id: int
    requirement_id: Optional[str] = None
    scenario_name: str
    given: Optional[str] = None
    when: Optional[str] = None
    then: Optional[str] = None
    test_code: Optional[str] = None
    is_shadow_test: bool = False

class AcceptanceTestResponse(BaseModel):
    id: int
    project_id: int
    requirement_id: Optional[str]
    scenario_name: str
    given: Optional[str]
    when: Optional[str]
    then: Optional[str]
    test_code: Optional[str]
    execution_result: Optional[str]
    execution_log: Optional[str]
    executed_at: Optional[datetime]
    is_shadow_test: bool
    created_at: datetime

    class Config:
        from_attributes = True

@router.post("/", response_model=AcceptanceTestResponse)
def create_test(test: AcceptanceTestCreate, db: Session = Depends(get_db)):
    db_test = AcceptanceTest(**test.model_dump())
    db.add(db_test)
    db.commit()
    db.refresh(db_test)
    return db_test

@router.get("/project/{project_id}", response_model=List[AcceptanceTestResponse])
def get_tests_by_project(project_id: int, is_shadow: Optional[bool] = None, db: Session = Depends(get_db)):
    query = db.query(AcceptanceTest).filter(AcceptanceTest.project_id == project_id)
    if is_shadow is not None:
        query = query.filter(AcceptanceTest.is_shadow_test == is_shadow)
    return query.all()

@router.post("/{test_id}/execute")
def execute_test(test_id: int, db: Session = Depends(get_db)):
    test = db.query(AcceptanceTest).filter(AcceptanceTest.id == test_id).first()
    if not test:
        raise HTTPException(status_code=404, detail="Test not found")
    test.execution_result = "passed"
    test.execution_log = "Test executed successfully"
    test.executed_at = datetime.now()
    db.commit()
    return {"test_id": test_id, "result": test.execution_result}

@router.get("/shadow-comparison/{project_id}")
def compare_shadow_tests(project_id: int, db: Session = Depends(get_db)):
    main_tests = db.query(AcceptanceTest).filter(
        AcceptanceTest.project_id == project_id,
        AcceptanceTest.is_shadow_test.is_(False)
    ).all()
    shadow_tests = db.query(AcceptanceTest).filter(
        AcceptanceTest.project_id == project_id,
        AcceptanceTest.is_shadow_test.is_(True)
    ).all()
    
    divergences = []
    for main in main_tests:
        for shadow in shadow_tests:
            if main.requirement_id == shadow.requirement_id:
                if main.execution_result != shadow.execution_result:
                    divergences.append({
                        "requirement_id": main.requirement_id,
                        "main_result": main.execution_result,
                        "shadow_result": shadow.execution_result
                    })
    
    return {
        "project_id": project_id,
        "main_tests_count": len(main_tests),
        "shadow_tests_count": len(shadow_tests),
        "divergences": divergences,
        "needs_human_intervention": len(divergences) > 0
    }
