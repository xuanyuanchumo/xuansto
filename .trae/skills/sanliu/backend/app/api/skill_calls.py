from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, extract
from typing import List, Optional
from pydantic import BaseModel, Field
from datetime import datetime

from ..models.base import get_db
from ..models.skill_call import SkillCall
from ..services import (
    BaseCRUDService, StatusValidator, StatsCalculator, 
    cache_service, CacheKeys, invalidate_cache
)

router = APIRouter()
skill_call_service = BaseCRUDService(SkillCall)
status_validator = StatusValidator(["started", "running", "completed", "failed", "cancelled"])

class SkillCallCreate(BaseModel):
    skill_name: str = Field(..., description="技能名称", min_length=1, max_length=200)
    caller: Optional[str] = Field(None, description="调用者标识", max_length=100)
    status: str = Field("started", description="初始状态")
    details: Optional[dict] = Field(None, description="调用详情")
    parent_call_id: Optional[int] = Field(None, description="父调用ID，用于嵌套调用")

class SkillCallUpdate(BaseModel):
    status: Optional[str] = Field(None, description="调用状态: started, running, completed, failed, cancelled")
    details: Optional[dict] = Field(None, description="调用详情")
    end_time: Optional[datetime] = Field(None, description="结束时间")
    error_message: Optional[str] = Field(None, description="错误信息")

class SkillCallResponse(BaseModel):
    id: int
    skill_name: str
    caller: Optional[str]
    status: str
    start_time: datetime
    end_time: Optional[datetime]
    details: Optional[dict]
    parent_call_id: Optional[int]
    created_at: datetime

    class Config:
        from_attributes = True

class SkillCallDetailResponse(SkillCallResponse):
    duration_seconds: Optional[float]
    children_count: int
    has_error: bool

class SkillCallStatsResponse(BaseModel):
    total: int
    by_status: dict
    by_skill: dict
    avg_duration: Optional[float]
    success_rate: float

VALID_TRANSITIONS = {
    "started": ["running", "completed", "failed", "cancelled"],
    "running": ["completed", "failed", "cancelled"],
    "completed": [],
    "failed": [],
    "cancelled": []
}

@router.post("/", response_model=SkillCallResponse, summary="创建技能调用", description="创建一个新的技能调用记录，记录技能执行的开始")
def create_skill_call(call: SkillCallCreate, db: Session = Depends(get_db)):
    status_validator.validate(call.status)
    
    if call.parent_call_id:
        skill_call_service.get_or_404(db, call.parent_call_id, "Parent skill call")
    
    result = skill_call_service.create(db, call)
    invalidate_cache("skill_calls:*")
    return result

@router.put("/{call_id}", response_model=SkillCallResponse, summary="更新技能调用", description="更新技能调用的状态、详情或结束时间")
def update_skill_call(call_id: int, call: SkillCallUpdate, db: Session = Depends(get_db)):
    db_call = skill_call_service.get_or_404(db, call_id, "Skill call")
    
    update_data = call.model_dump(exclude_unset=True)
    
    if "status" in update_data:
        status_validator.validate(update_data["status"])
        
        if update_data["status"] not in VALID_TRANSITIONS.get(db_call.status, []):
            raise HTTPException(
                status_code=400,
                detail=f"Cannot transition from '{db_call.status}' to '{update_data['status']}'"
            )
    
    result = skill_call_service.update(db, db_call, call)
    invalidate_cache("skill_calls:*")
    cache_service.delete(CacheKeys.generate_key(CacheKeys.SKILL_CALL_DETAIL, call_id=call_id))
    return result

@router.get("/", response_model=List[SkillCallResponse], summary="获取技能调用列表", description="获取技能调用列表，支持按技能名称和状态筛选，支持分页")
def list_skill_calls(
    skip: int = Query(0, ge=0, description="跳过的记录数"),
    limit: int = Query(100, ge=1, le=500, description="返回的记录数"),
    skill_name: Optional[str] = Query(None, description="按技能名称筛选"),
    status: Optional[str] = Query(None, description="按状态筛选"),
    caller: Optional[str] = Query(None, description="按调用者筛选"),
    db: Session = Depends(get_db)
):
    cache_key = CacheKeys.generate_key(
        CacheKeys.SKILL_CALL_LIST,
        skill_name=skill_name or "all",
        status=status or "all",
        skip=skip,
        limit=limit
    )
    cached = cache_service.get_json(cache_key)
    if cached:
        return [SkillCallResponse(**c) for c in cached]
    
    query = db.query(SkillCall)
    if skill_name:
        query = query.filter(SkillCall.skill_name == skill_name)
    if status:
        status_validator.validate(status)
        query = query.filter(SkillCall.status == status)
    if caller:
        query = query.filter(SkillCall.caller == caller)
    
    calls = query.offset(skip).limit(limit).all()
    result = [SkillCallResponse.model_validate(c) for c in calls]
    
    cache_service.set_json(cache_key, [c.model_dump() for c in result], ttl=30)
    return result

@router.get("/stats", response_model=SkillCallStatsResponse, summary="获取技能调用统计", description="获取技能调用的整体统计信息")
def get_skill_call_stats(db: Session = Depends(get_db)):
    cache_key = CacheKeys.SKILL_CALL_STATS
    cached = cache_service.get_json(cache_key)
    if cached:
        return SkillCallStatsResponse(**cached)
    
    total = skill_call_service.count(db)
    by_status = StatsCalculator.get_status_distribution(db, SkillCall)
    by_skill = StatsCalculator.get_status_distribution(db, SkillCall, "skill_name")
    
    avg_duration = None
    completed_calls = by_status.get("completed", 0)
    if completed_calls > 0:
        duration_result = db.query(
            func.avg(
                extract('epoch', SkillCall.end_time) - extract('epoch', SkillCall.start_time)
            ).label('avg_duration')
        ).filter(
            SkillCall.status == "completed",
            SkillCall.start_time.isnot(None),
            SkillCall.end_time.isnot(None)
        ).first()
        
        if duration_result and duration_result.avg_duration:
            avg_duration = round(duration_result.avg_duration, 2)
    
    success_rate = StatsCalculator.calculate_percentage(by_status.get("completed", 0), total)
    
    result = SkillCallStatsResponse(
        total=total,
        by_status=by_status,
        by_skill=by_skill,
        avg_duration=avg_duration,
        success_rate=success_rate
    )
    
    cache_service.set_json(cache_key, result.model_dump(), ttl=60)
    return result

@router.get("/{call_id}", response_model=SkillCallResponse, summary="获取技能调用详情", description="根据ID获取单个技能调用的详细信息")
def get_skill_call(call_id: int, db: Session = Depends(get_db)):
    cache_key = CacheKeys.generate_key(CacheKeys.SKILL_CALL_DETAIL, call_id=call_id)
    cached = cache_service.get_json(cache_key)
    if cached:
        return SkillCallResponse(**cached)
    
    db_call = skill_call_service.get_or_404(db, call_id, "Skill call")
    result = SkillCallResponse.model_validate(db_call)
    cache_service.set_json(cache_key, result.model_dump(), ttl=60)
    return result

@router.get("/{call_id}/detail", response_model=SkillCallDetailResponse, summary="获取技能调用详细信息", description="获取技能调用的详细信息，包括执行时长等")
def get_skill_call_detail(call_id: int, db: Session = Depends(get_db)):
    cache_key = f"skill_calls:detail_full:{call_id}"
    cached = cache_service.get_json(cache_key)
    if cached:
        return SkillCallDetailResponse(**cached)
    
    db_call = skill_call_service.get_or_404(db, call_id, "Skill call")
    
    duration_seconds = None
    if db_call.start_time and db_call.end_time:
        duration_seconds = (db_call.end_time - db_call.start_time).total_seconds()
    
    children_count = db.query(func.count(SkillCall.id)).filter(
        SkillCall.parent_call_id == call_id
    ).scalar()
    
    has_error = bool(db_call.status == "failed" or (db_call.details and db_call.details.get("error")))
    
    result = SkillCallDetailResponse(
        id=db_call.id,
        skill_name=db_call.skill_name,
        caller=db_call.caller,
        status=db_call.status,
        start_time=db_call.start_time,
        end_time=db_call.end_time,
        details=db_call.details,
        parent_call_id=db_call.parent_call_id,
        created_at=db_call.created_at,
        duration_seconds=round(duration_seconds, 2) if duration_seconds else None,
        children_count=children_count,
        has_error=has_error
    )
    
    cache_service.set_json(cache_key, result.model_dump(), ttl=60)
    return result

@router.get("/tree/{root_id}", summary="获取技能调用树", description="获取技能调用的层级树结构，包含所有子调用")
def get_call_tree(root_id: int, db: Session = Depends(get_db)):
    cache_key = CacheKeys.generate_key(CacheKeys.SKILL_CALL_TREE, root_id=root_id)
    cached = cache_service.get_json(cache_key)
    if cached:
        return cached
    
    def build_tree_recursive(call_id: int, visited: set = None):
        call = db.query(SkillCall).filter(SkillCall.id == call_id).first()
        if not call:
            return None
        
        if visited is None:
            visited = set()
        
        if call_id in visited:
            return None
        visited.add(call_id)
        
        children = db.query(SkillCall).filter(SkillCall.parent_call_id == call_id).all()
        return {
            "id": call.id,
            "skill_name": call.skill_name,
            "status": call.status,
            "start_time": call.start_time.isoformat() if call.start_time else None,
            "end_time": call.end_time.isoformat() if call.end_time else None,
            "details": call.details,
            "children": [build_tree_recursive(c.id, visited.copy()) for c in children]
        }
    
    tree = build_tree_recursive(root_id)
    if not tree:
        raise HTTPException(status_code=404, detail="Skill call not found")
    
    cache_service.set_json(cache_key, tree, ttl=60)
    return tree

@router.delete("/{call_id}", summary="删除技能调用", description="删除指定的技能调用记录（仅限无子调用的记录）")
def delete_skill_call(call_id: int, db: Session = Depends(get_db)):
    skill_call_service.get_or_404(db, call_id, "Skill call")
    
    children_count = db.query(func.count(SkillCall.id)).filter(
        SkillCall.parent_call_id == call_id
    ).scalar()
    
    if children_count > 0:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot delete skill call. {children_count} child calls exist"
        )
    
    skill_call_service.delete(db, call_id)
    invalidate_cache("skill_calls:*")
    return {"message": "Skill call deleted successfully", "call_id": call_id}
