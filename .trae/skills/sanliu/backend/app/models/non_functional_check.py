from sqlalchemy import Column, Integer, String, Text, JSON, DateTime, ForeignKey, Float
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .base import Base

class NonFunctionalCheck(Base):
    __tablename__ = "non_functional_checks"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    check_type = Column(String(50), nullable=False)
    check_name = Column(String(200), nullable=False)
    description = Column(Text)
    baseline_value = Column(Float)
    actual_value = Column(Float)
    unit = Column(String(50))
    status = Column(String(20), default="pending")
    details = Column(JSON)
    recommendations = Column(Text)
    checked_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    project = relationship("Project", backref="non_functional_checks")
