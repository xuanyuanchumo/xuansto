from sqlalchemy import Column, Integer, String, Text, JSON, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .base import Base

class HumanApproval(Base):
    __tablename__ = "human_approvals"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    skill_call_id = Column(Integer, ForeignKey("skill_calls.id"), nullable=True)
    approval_type = Column(String(50), nullable=False)
    title = Column(String(500), nullable=False)
    description = Column(Text)
    change_details = Column(JSON)
    risk_level = Column(String(20))
    status = Column(String(20), default="pending")
    approved_by = Column(String(100))
    approved_at = Column(DateTime(timezone=True))
    rejection_reason = Column(Text)
    modification_suggestions = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    project = relationship("Project", backref="human_approvals")
    skill_call = relationship("SkillCall", backref="approvals")
