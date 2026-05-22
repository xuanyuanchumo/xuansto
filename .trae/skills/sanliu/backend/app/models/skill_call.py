from sqlalchemy import Column, Integer, String, Text, JSON, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .base import Base

class SkillCall(Base):
    __tablename__ = "skill_calls"

    id = Column(Integer, primary_key=True, index=True)
    skill_name = Column(String(100), nullable=False, index=True)
    caller = Column(String(100), index=True)
    status = Column(String(20), default="started", index=True)
    start_time = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    end_time = Column(DateTime(timezone=True), nullable=True)
    details = Column(JSON)
    parent_call_id = Column(Integer, ForeignKey("skill_calls.id"), nullable=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    input_data = Column(JSON)
    output_data = Column(JSON)
    reasoning_log = Column(Text)
    decision_type = Column(String(50), index=True)
    decision_basis = Column(JSON)
    alternatives = Column(JSON)
    
    __table_args__ = (
        Index('ix_skill_calls_skill_status', 'skill_name', 'status'),
        Index('ix_skill_calls_status_created', 'status', 'created_at'),
        Index('ix_skill_calls_caller_status', 'caller', 'status'),
    )
    
    parent = relationship("SkillCall", remote_side=[id], backref="children")
