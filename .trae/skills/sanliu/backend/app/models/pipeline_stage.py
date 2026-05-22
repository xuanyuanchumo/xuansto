from sqlalchemy import Column, Integer, String, Text, JSON, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .base import Base

class PipelineStage(Base):
    __tablename__ = "pipeline_stages"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False, index=True)
    stage_name = Column(String(100), nullable=False, index=True)
    stage_order = Column(Integer, default=0)
    status = Column(String(20), default="pending", index=True)
    requires_human = Column(Integer, default=0)
    human_approval_id = Column(Integer, ForeignKey("human_approvals.id"))
    start_time = Column(DateTime(timezone=True))
    end_time = Column(DateTime(timezone=True))
    duration_seconds = Column(Integer)
    output_artifacts = Column(JSON)
    error_message = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    __table_args__ = (
        Index('ix_pipeline_stages_project_status', 'project_id', 'status'),
        Index('ix_pipeline_stages_project_order', 'project_id', 'stage_order'),
    )
    
    project = relationship("Project", backref="pipeline_stages")
    human_approval = relationship("HumanApproval", backref="pipeline_stages")
