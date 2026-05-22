from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .base import Base

class CodeChange(Base):
    __tablename__ = "code_changes"

    id = Column(Integer, primary_key=True, index=True)
    skill_call_id = Column(Integer, ForeignKey("skill_calls.id"), nullable=False)
    file_path = Column(String(500), nullable=False)
    change_type = Column(String(20), nullable=False)
    content_before = Column(Text)
    content_after = Column(Text)
    diff = Column(Text)
    reason = Column(Text)
    related_task_id = Column(Integer, ForeignKey("tasks.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    skill_call = relationship("SkillCall", backref="code_changes")
    related_task = relationship("Task", backref="code_changes")
