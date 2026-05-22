from sqlalchemy import Column, Integer, String, JSON, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .base import Base

class Agent(Base):
    __tablename__ = "agents"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False, index=True)
    role = Column(String(100), index=True)
    skills = Column(JSON)
    status = Column(String(50), default="idle", index=True)
    current_load = Column(Integer, default=0)
    max_load = Column(Integer, default=5)
    current_task = Column(String(500))
    department_id = Column(Integer, ForeignKey("departments.id"), index=True)
    last_heartbeat = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    __table_args__ = (
        Index('ix_agents_status_department', 'status', 'department_id'),
    )
    
    department = relationship("Department", back_populates="agents")
    assignments = relationship("Assignment", back_populates="agent")
