from sqlalchemy import Column, Integer, String, Text, JSON, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .base import Base

class AcceptanceTest(Base):
    __tablename__ = "acceptance_tests"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    requirement_id = Column(String(100))
    scenario_name = Column(String(500), nullable=False)
    given = Column(Text)
    when = Column(Text)
    then = Column(Text)
    test_code = Column(Text)
    execution_result = Column(String(20))
    execution_log = Column(Text)
    executed_at = Column(DateTime(timezone=True))
    is_shadow_test = Column(Boolean, default=False)
    shadow_comparison = Column(JSON)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    project = relationship("Project", backref="acceptance_tests")
