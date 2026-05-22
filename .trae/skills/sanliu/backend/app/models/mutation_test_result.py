from sqlalchemy import Column, Integer, String, JSON, DateTime, ForeignKey, Float
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .base import Base

class MutationTestResult(Base):
    __tablename__ = "mutation_test_results"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    test_run_id = Column(String(100))
    total_mutants = Column(Integer, default=0)
    killed_mutants = Column(Integer, default=0)
    survived_mutants = Column(Integer, default=0)
    mutation_score = Column(Float, default=0.0)
    mutant_details = Column(JSON)
    coverage_improvement = Column(Float)
    status = Column(String(20), default="pending")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    project = relationship("Project", backref="mutation_test_results")
