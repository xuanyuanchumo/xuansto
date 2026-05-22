from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .base import Base

class Assignment(Base):
    __tablename__ = "assignments"

    id = Column(Integer, primary_key=True, index=True)
    agent_id = Column(Integer, ForeignKey("agents.id"), index=True)
    task_id = Column(Integer, ForeignKey("tasks.id"), index=True)
    skill_call_id = Column(Integer, ForeignKey("skill_calls.id"), nullable=True, index=True)
    task_description = Column(Text)
    status = Column(String(20), default="assigned", index=True)
    assigned_time = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    completed_time = Column(DateTime(timezone=True), nullable=True)
    
    __table_args__ = (
        Index('ix_assignments_agent_status', 'agent_id', 'status'),
        Index('ix_assignments_status_assigned', 'status', 'assigned_time'),
    )
    
    agent = relationship("Agent", back_populates="assignments")
    task = relationship("Task", back_populates="assignments")
