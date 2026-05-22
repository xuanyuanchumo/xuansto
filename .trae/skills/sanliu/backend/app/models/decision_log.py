from sqlalchemy import Column, Integer, String, Text, JSON, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .base import Base

class DecisionLog(Base):
    __tablename__ = "decision_logs"

    id = Column(Integer, primary_key=True, index=True)
    skill_call_id = Column(Integer, ForeignKey("skill_calls.id"), nullable=False, index=True)
    decision_type = Column(String(50), nullable=False, index=True)
    decision_basis = Column(JSON)
    reasoning_process = Column(Text)
    alternatives = Column(JSON)
    final_decision = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    
    __table_args__ = (
        Index('ix_decision_logs_skill_type', 'skill_call_id', 'decision_type'),
    )
    
    skill_call = relationship("SkillCall", backref="decision_logs")
