from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from .base import Base

class Department(Base):
    __tablename__ = "departments"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    pinyin = Column(String(100), unique=True, nullable=False)
    level = Column(String(50))
    parent_id = Column(Integer, ForeignKey("departments.id"), nullable=True)
    
    parent = relationship("Department", remote_side=[id], backref="children")
    agents = relationship("Agent", back_populates="department")
    tasks = relationship("Task", back_populates="department")
