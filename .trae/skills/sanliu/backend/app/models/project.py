from sqlalchemy import Column, Integer, String, Text, JSON, DateTime, Index
from sqlalchemy.sql import func
from .base import Base
import enum

class ProjectStatus(str, enum.Enum):
    REQUIREMENT = "REQUIREMENT"
    DESIGN = "DESIGN"
    DEVELOPMENT = "DEVELOPMENT"
    TESTING = "TESTING"
    DEPLOYMENT = "DEPLOYMENT"
    COMPLETED = "COMPLETED"

PROJECT_STATUS_TRANSITIONS = {
    ProjectStatus.REQUIREMENT: [ProjectStatus.DESIGN],
    ProjectStatus.DESIGN: [ProjectStatus.DEVELOPMENT],
    ProjectStatus.DEVELOPMENT: [ProjectStatus.TESTING],
    ProjectStatus.TESTING: [ProjectStatus.DEVELOPMENT, ProjectStatus.DEPLOYMENT],
    ProjectStatus.DEPLOYMENT: [ProjectStatus.TESTING, ProjectStatus.COMPLETED],
    ProjectStatus.COMPLETED: [],
}

class Project(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False, index=True)
    description = Column(Text)
    tech_stack = Column(JSON)
    status = Column(String(50), default=ProjectStatus.REQUIREMENT.value, index=True)
    status_history = Column(JSON, default=list)
    milestones = Column(JSON, default=list)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    __table_args__ = (
        Index('ix_projects_status_created', 'status', 'created_at'),
    )
