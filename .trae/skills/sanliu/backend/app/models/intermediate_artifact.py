from sqlalchemy import Column, Integer, String, Text, JSON, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .base import Base

class IntermediateArtifact(Base):
    __tablename__ = "intermediate_artifacts"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    skill_call_id = Column(Integer, ForeignKey("skill_calls.id"), nullable=True)
    artifact_type = Column(String(50), nullable=False)
    name = Column(String(200), nullable=False)
    content = Column(Text)
    file_path = Column(String(500))
    artifact_metadata = Column("metadata", JSON)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    project = relationship("Project", backref="artifacts")
    skill_call = relationship("SkillCall", backref="artifacts")
