from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .base import Base

class RequirementTrace(Base):
    __tablename__ = "requirement_traces"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    requirement_id = Column(String(100), nullable=False)
    requirement_title = Column(String(500))
    feature_id = Column(String(100))
    feature_title = Column(String(500))
    trace_type = Column(String(50))
    status = Column(String(20), default="pending")
    test_case_id = Column(String(100))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    project = relationship("Project", backref="requirement_traces")
