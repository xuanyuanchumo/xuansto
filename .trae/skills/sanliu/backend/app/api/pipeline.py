from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel, Field
from datetime import datetime

from ..models.base import get_db
from ..models.pipeline_stage import PipelineStage
from ..models.project import Project
from ..services.pipeline import StageExecutor, ComplianceChecker, PipelineReportGenerator

router = APIRouter()

VALID_STAGE_STATUSES = ["pending", "running", "completed", "failed", "skipped"]


class PipelineStageResponse(BaseModel):
    id: int
    project_id: int
    stage_name: str
    stage_order: int
    status: str
    requires_human: int
    start_time: Optional[datetime]
    end_time: Optional[datetime]
    duration_seconds: Optional[int]
    output_artifacts: Optional[dict]
    created_at: datetime

    class Config:
        from_attributes = True


class PipelineStatusResponse(BaseModel):
    project_id: int
    total_stages: int
    completed_stages: int
    current_stage: Optional[str]
    progress_percentage: float
    stages: List[PipelineStageResponse]


class StageStartRequest(BaseModel):
    triggered_by: Optional[str] = Field(None, description="触发者")


class StageCompleteRequest(BaseModel):
    output_artifacts: Optional[dict] = Field(None, description="输出产物")
    triggered_by: Optional[str] = Field(None, description="完成者")


@router.post("/project/{project_id}/initialize", summary="初始化流水线", description="为项目初始化开发流水线阶段")
def initialize_pipeline(project_id: int, db: Session = Depends(get_db)):
    checker = ComplianceChecker(db)
    checker.validate_project_exists(project_id)
    checker.validate_pipeline_not_initialized(project_id)
    
    pipeline_stages = PipelineReportGenerator.get_pipeline_stages_config()
    
    for stage in pipeline_stages:
        db_stage = PipelineStage(
            project_id=project_id,
            stage_name=stage["name"],
            stage_order=stage["order"],
            requires_human=stage["requires_human"],
            status="pending"
        )
        db.add(db_stage)
    db.commit()
    
    return PipelineReportGenerator.generate_initialization_report(
        project_id, 
        len(pipeline_stages)
    )


@router.get("/project/{project_id}", response_model=List[PipelineStageResponse], summary="获取流水线状态", description="获取项目的流水线各阶段状态")
def get_pipeline_status(project_id: int, db: Session = Depends(get_db)):
    checker = ComplianceChecker(db)
    checker.validate_project_exists(project_id)
    
    return db.query(PipelineStage).filter(
        PipelineStage.project_id == project_id
    ).order_by(PipelineStage.stage_order).all()


@router.get("/project/{project_id}/summary", response_model=PipelineStatusResponse, summary="获取流水线摘要", description="获取项目流水线的整体状态摘要")
def get_pipeline_summary(project_id: int, db: Session = Depends(get_db)):
    checker = ComplianceChecker(db)
    checker.validate_project_exists(project_id)
    stages = checker.validate_pipeline_initialized(project_id)
    
    return PipelineReportGenerator.generate_summary_report(project_id, stages)


@router.post("/project/{project_id}/stage/{stage_name}/start", summary="开始阶段", description="开始执行指定的流水线阶段")
def start_stage(
    project_id: int,
    stage_name: str,
    request: Optional[StageStartRequest] = None,
    db: Session = Depends(get_db)
):
    executor = StageExecutor(db)
    triggered_by = request.triggered_by if request else None
    
    return executor.start_stage(project_id, stage_name, triggered_by)


@router.post("/project/{project_id}/stage/{stage_name}/complete", summary="完成阶段", description="标记指定的流水线阶段为已完成")
def complete_stage(
    project_id: int,
    stage_name: str,
    request: StageCompleteRequest = None,
    db: Session = Depends(get_db)
):
    executor = StageExecutor(db)
    artifacts = None
    if request:
        artifacts = {"output_artifacts": request.output_artifacts} if request.output_artifacts else None
    triggered_by = request.triggered_by if request else None
    
    return executor.complete_stage(
        project_id, 
        stage_name, 
        artifacts, 
        triggered_by
    )


@router.post("/project/{project_id}/stage/{stage_name}/fail", summary="标记阶段失败", description="标记指定的流水线阶段为失败状态")
def fail_stage(
    project_id: int,
    stage_name: str,
    error_message: str = Query(..., description="错误信息"),
    db: Session = Depends(get_db)
):
    executor = StageExecutor(db)
    return executor.fail_stage(project_id, stage_name, error_message)


@router.post("/project/{project_id}/stage/{stage_name}/skip", summary="跳过阶段", description="跳过指定的流水线阶段")
def skip_stage(
    project_id: int,
    stage_name: str,
    reason: str = Query(..., description="跳过原因"),
    db: Session = Depends(get_db)
):
    executor = StageExecutor(db)
    return executor.skip_stage(project_id, stage_name, reason)


@router.post("/project/{project_id}/reset", summary="重置流水线", description="重置项目的流水线状态")
def reset_pipeline(project_id: int, db: Session = Depends(get_db)):
    checker = ComplianceChecker(db)
    checker.validate_project_exists(project_id)
    
    db.query(PipelineStage).filter(
        PipelineStage.project_id == project_id
    ).delete()
    
    pipeline_stages = PipelineReportGenerator.get_pipeline_stages_config()
    
    for stage in pipeline_stages:
        db_stage = PipelineStage(
            project_id=project_id,
            stage_name=stage["name"],
            stage_order=stage["order"],
            requires_human=stage["requires_human"],
            status="pending"
        )
        db.add(db_stage)
    db.commit()
    
    return PipelineReportGenerator.generate_reset_report(project_id)
