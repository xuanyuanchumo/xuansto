from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .base import Base

class ClarificationQuestion(Base):
    __tablename__ = "clarification_questions"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    question = Column(Text, nullable=False)
    question_type = Column(String(50))
    context = Column(Text)
    answer = Column(Text)
    answered_by = Column(String(100))
    answered_at = Column(DateTime(timezone=True))
    status = Column(String(20), default="pending")
    confirmed_by = Column(String(100))
    confirmed_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    project = relationship("Project", backref="clarification_questions")
