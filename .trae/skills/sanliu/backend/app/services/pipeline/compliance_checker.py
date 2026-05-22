from typing import List, Dict, Any
from sqlalchemy.orm import Session
from fastapi import HTTPException

from ...models.pipeline_stage import PipelineStage
from ...models.project import Project


class ComplianceChecker:
    def __init__(self, db: Session):
        self.db = db

    def validate_project_exists(self, project_id: int) -> Project:
        project = self.db.query(Project).filter(
            Project.id == project_id
        ).first()
        
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        
        return project

    def validate_pipeline_not_initialized(self, project_id: int) -> None:
        existing = self.db.query(PipelineStage).filter(
            PipelineStage.project_id == project_id
        ).first()
        
        if existing:
            raise HTTPException(
                status_code=400,
                detail="Pipeline already initialized for this project"
            )

    def validate_pipeline_initialized(self, project_id: int) -> List[PipelineStage]:
        stages = self.db.query(PipelineStage).filter(
            PipelineStage.project_id == project_id
        ).order_by(PipelineStage.stage_order).all()
        
        if not stages:
            raise HTTPException(
                status_code=404,
                detail="Pipeline not initialized for this project"
            )
        
        return stages

    def get_incomplete_previous_stages(
        self,
        project_id: int,
        current_stage_order: int
    ) -> List[str]:
        prev_stages = self.db.query(PipelineStage).filter(
            PipelineStage.project_id == project_id,
            PipelineStage.stage_order < current_stage_order
        ).all()
        
        return [s.stage_name for s in prev_stages if s.status != "completed"]

    def check_stage_status(
        self,
        stage: PipelineStage,
        allowed_statuses: List[str],
        action: str
    ) -> None:
        if stage.status not in allowed_statuses:
            raise HTTPException(
                status_code=400,
                detail=f"Cannot {action} stage with status '{stage.status}'. "
                       f"Stage must be in {allowed_statuses} status."
            )

    def get_pipeline_progress(
        self,
        stages: List[PipelineStage]
    ) -> Dict[str, Any]:
        total_stages = len(stages)
        completed_stages = sum(1 for s in stages if s.status == "completed")
        
        current_stage = None
        for stage in stages:
            if stage.status in ["pending", "running"]:
                current_stage = stage.stage_name
                break
        
        progress_percentage = (
            (completed_stages / total_stages * 100) 
            if total_stages > 0 else 0
        )
        
        return {
            "total_stages": total_stages,
            "completed_stages": completed_stages,
            "current_stage": current_stage,
            "progress_percentage": round(progress_percentage, 2)
        }
