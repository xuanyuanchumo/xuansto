from sqlalchemy import Column, Integer, String, Text, JSON, DateTime, ForeignKey, Float, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .base import Base
import enum

class TaskStatus(str, enum.Enum):
    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    REVIEW = "REVIEW"
    COMPLETED = "COMPLETED"

class TaskPriority(str, enum.Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

TASK_STATUS_TRANSITIONS = {
    TaskStatus.PENDING: [TaskStatus.IN_PROGRESS],
    TaskStatus.IN_PROGRESS: [TaskStatus.REVIEW],
    TaskStatus.REVIEW: [TaskStatus.IN_PROGRESS, TaskStatus.COMPLETED],
    TaskStatus.COMPLETED: [],
}

class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), index=True)
    department_id = Column(Integer, ForeignKey("departments.id"), index=True)
    agent_id = Column(Integer, ForeignKey("agents.id"), nullable=True, index=True)
    title = Column(String(200), nullable=False)
    description = Column(Text)
    required_skill = Column(String(100), index=True)
    priority = Column(String(20), default=TaskPriority.MEDIUM.value, index=True)
    status = Column(String(50), default=TaskStatus.PENDING.value, index=True)
    status_history = Column(JSON, default=list)
    dependencies = Column(JSON, default=list)
    estimated_hours = Column(Float, nullable=True)
    actual_hours = Column(Float, nullable=True)
    details = Column(JSON)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)
    
    __table_args__ = (
        Index('ix_tasks_project_status', 'project_id', 'status'),
        Index('ix_tasks_status_priority', 'status', 'priority'),
        Index('ix_tasks_agent_status', 'agent_id', 'status'),
    )
    
    project = relationship("Project")
    department = relationship("Department", back_populates="tasks")
    agent = relationship("Agent")
    assignments = relationship("Assignment", back_populates="task")
