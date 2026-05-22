from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime

from ..models.base import get_db
from ..models.human_approval import HumanApproval
from ..services import BaseCRUDService

router = APIRouter()
approval_service = BaseCRUDService(HumanApproval)

class HumanApprovalCreate(BaseModel):
    project_id: int
    skill_call_id: Optional[int] = None
    approval_type: str
    title: str
    description: Optional[str] = None
    change_details: Optional[dict] = None
    risk_level: Optional[str] = None

class HumanApprovalDecision(BaseModel):
    decision: str
    approved_by: str
    rejection_reason: Optional[str] = None
    modification_suggestions: Optional[str] = None

class HumanApprovalResponse(BaseModel):
    id: int
    project_id: int
    skill_call_id: Optional[int]
    approval_type: str
    title: str
    description: Optional[str]
    change_details: Optional[dict]
    risk_level: Optional[str]
    status: str
    approved_by: Optional[str]
    approved_at: Optional[datetime]
    rejection_reason: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True

@router.post("/", response_model=HumanApprovalResponse)
def create_approval(approval: HumanApprovalCreate, db: Session = Depends(get_db)):
    return approval_service.create(db, approval)

@router.get("/project/{project_id}", response_model=List[HumanApprovalResponse])
def get_approvals_by_project(project_id: int, status: Optional[str] = None, db: Session = Depends(get_db)):
    filters = {"project_id": project_id}
    if status:
        filters["status"] = status
    return approval_service.get_multi(db, filters=filters, limit=1000)

@router.get("/pending", response_model=List[HumanApprovalResponse])
def get_pending_approvals(db: Session = Depends(get_db)):
    return approval_service.get_multi(db, filters={"status": "pending"}, limit=1000)

@router.put("/{approval_id}/decide", response_model=HumanApprovalResponse)
def decide_approval(approval_id: int, decision_data: HumanApprovalDecision, db: Session = Depends(get_db)):
    from fastapi import HTTPException
    
    approval = approval_service.get_or_404(db, approval_id, "Approval")
    if approval.status != "pending":
        raise HTTPException(status_code=400, detail="Approval already processed")
    
    approval.status = decision_data.decision
    approval.approved_by = decision_data.approved_by
    approval.approved_at = datetime.now()
    if decision_data.decision == "rejected":
        approval.rejection_reason = decision_data.rejection_reason
    else:
        approval.modification_suggestions = decision_data.modification_suggestions
    
    db.commit()
    db.refresh(approval)
    return approval
