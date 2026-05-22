from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
from pydantic import BaseModel, Field

from ..models.base import get_db
from ..models.department import Department
from ..models.agent import Agent
from ..models.task import Task
from ..services import BaseCRUDService, EntityValidator, APIResponseBuilder

router = APIRouter()
department_service = BaseCRUDService(Department)
validator = EntityValidator()

class DepartmentCreate(BaseModel):
    name: str = Field(..., description="部门名称", min_length=1, max_length=100)
    pinyin: str = Field(..., description="部门拼音缩写", min_length=1, max_length=50)
    level: Optional[str] = Field(None, description="部门级别")
    parent_id: Optional[int] = Field(None, description="上级部门ID")

class DepartmentUpdate(BaseModel):
    name: Optional[str] = Field(None, description="部门名称", min_length=1, max_length=100)
    pinyin: Optional[str] = Field(None, description="部门拼音缩写", min_length=1, max_length=50)
    level: Optional[str] = Field(None, description="部门级别")
    parent_id: Optional[int] = Field(None, description="上级部门ID")

class DepartmentResponse(BaseModel):
    id: int
    name: str
    pinyin: str
    level: Optional[str]
    parent_id: Optional[int]

    class Config:
        from_attributes = True

class DepartmentDetailResponse(DepartmentResponse):
    agents_count: int
    tasks_count: int
    children: List[dict]

class DepartmentTreeResponse(BaseModel):
    id: int
    name: str
    pinyin: str
    level: Optional[str]
    children: List["DepartmentTreeResponse"]

    class Config:
        from_attributes = True

@router.post("/", response_model=DepartmentResponse, summary="创建部门", description="创建一个新的部门")
def create_department(department: DepartmentCreate, db: Session = Depends(get_db)):
    department_service.check_unique_name(db, department.name, "Department")
    
    if db.query(Department).filter(Department.pinyin == department.pinyin).first():
        from fastapi import HTTPException
        raise HTTPException(status_code=409, detail=f"Department with pinyin '{department.pinyin}' already exists")
    
    if department.parent_id:
        validator.check_exists(db, Department, department.parent_id, "Parent department")
    
    return department_service.create(db, department)

@router.get("/", response_model=List[DepartmentResponse], summary="获取部门列表", description="获取所有部门列表")
def list_departments(
    level: Optional[str] = Query(None, description="按级别筛选"),
    parent_id: Optional[int] = Query(None, description="按上级部门筛选"),
    db: Session = Depends(get_db)
):
    filters = {}
    if level:
        filters["level"] = level
    if parent_id is not None:
        filters["parent_id"] = parent_id
    return department_service.get_multi(db, filters=filters, limit=1000)

@router.get("/tree", response_model=List[DepartmentTreeResponse], summary="获取部门树", description="获取部门的树形结构")
def get_department_tree(db: Session = Depends(get_db)):
    departments = department_service.get_all(db)
    
    def build_tree(parent_id: Optional[int] = None) -> List[DepartmentTreeResponse]:
        children = []
        for dept in departments:
            if dept.parent_id == parent_id:
                children.append(DepartmentTreeResponse(
                    id=dept.id,
                    name=dept.name,
                    pinyin=dept.pinyin,
                    level=dept.level,
                    children=build_tree(dept.id)
                ))
        return children
    
    return build_tree(None)

@router.get("/{department_id}", response_model=DepartmentResponse, summary="获取部门详情", description="根据ID获取部门信息")
def get_department(department_id: int, db: Session = Depends(get_db)):
    return department_service.get_or_404(db, department_id, "Department")

@router.get("/{department_id}/detail", response_model=DepartmentDetailResponse, summary="获取部门详细信息", description="获取部门的详细信息，包括代理和任务统计")
def get_department_detail(department_id: int, db: Session = Depends(get_db)):
    db_department = department_service.get_or_404(db, department_id, "Department")
    
    agents_count = db.query(func.count(Agent.id)).filter(Agent.department_id == department_id).scalar()
    tasks_count = db.query(func.count(Task.id)).filter(Task.department_id == department_id).scalar()
    
    children = db.query(Department).filter(Department.parent_id == department_id).all()
    children_list = [{"id": c.id, "name": c.name, "pinyin": c.pinyin} for c in children]
    
    return DepartmentDetailResponse(
        id=db_department.id,
        name=db_department.name,
        pinyin=db_department.pinyin,
        level=db_department.level,
        parent_id=db_department.parent_id,
        agents_count=agents_count,
        tasks_count=tasks_count,
        children=children_list
    )

@router.put("/{department_id}", response_model=DepartmentResponse, summary="更新部门", description="更新部门的基本信息")
def update_department(department_id: int, department: DepartmentUpdate, db: Session = Depends(get_db)):
    db_department = department_service.get_or_404(db, department_id, "Department")
    
    update_data = department.model_dump(exclude_unset=True)
    
    if "name" in update_data:
        department_service.check_unique_name(db, update_data["name"], "Department", exclude_id=department_id)
    
    if "pinyin" in update_data:
        if db.query(Department).filter(
            Department.pinyin == update_data["pinyin"],
            Department.id != department_id
        ).first():
            from fastapi import HTTPException
            raise HTTPException(status_code=409, detail=f"Department with pinyin '{update_data['pinyin']}' already exists")
    
    if "parent_id" in update_data and update_data["parent_id"] is not None:
        if update_data["parent_id"] == department_id:
            from fastapi import HTTPException
            raise HTTPException(status_code=400, detail="Department cannot be its own parent")
        validator.check_exists(db, Department, update_data["parent_id"], "Parent department")
    
    return department_service.update(db, db_department, department)

@router.delete("/{department_id}", summary="删除部门", description="删除指定的部门（需确保无子部门和关联代理）")
def delete_department(department_id: int, db: Session = Depends(get_db)):
    department_service.get_or_404(db, department_id, "Department")
    
    children = db.query(Department).filter(Department.parent_id == department_id).count()
    if children > 0:
        from fastapi import HTTPException
        raise HTTPException(
            status_code=400,
            detail=f"Cannot delete department. {children} child departments exist"
        )
    
    agents_count = db.query(Agent).filter(Agent.department_id == department_id).count()
    if agents_count > 0:
        from fastapi import HTTPException
        raise HTTPException(
            status_code=400,
            detail=f"Cannot delete department. {agents_count} agents are assigned to this department"
        )
    
    department_service.delete(db, department_id)
    return APIResponseBuilder.deleted("Department", department_id)
