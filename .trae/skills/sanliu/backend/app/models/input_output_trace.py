from sqlalchemy import Column, Integer, String, JSON, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .base import Base

class InputOutputTrace(Base):
    __tablename__ = "input_output_traces"

    id = Column(Integer, primary_key=True, index=True)
    skill_call_id = Column(Integer, ForeignKey("skill_calls.id"), nullable=False)
    trace_type = Column(String(10), nullable=False)
    data = Column(JSON, nullable=False)
    data_type = Column(String(50))
    source = Column(String(100))
    target = Column(String(100))
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    
    skill_call = relationship("SkillCall", backref="io_traces")
