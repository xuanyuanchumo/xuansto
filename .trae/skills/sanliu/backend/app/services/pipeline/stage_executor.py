from datetime import datetime
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from fastapi import HTTPException

from ...models.pipeline_stage import PipelineStage
from ...models.project import Project


class StageExecutor:
    def __init__(self, db: Session):
        self.db = db

    def start_stage(
        self,
        project_id: int,
        stage_name: str,
        triggered_by: Optional[str] = None
    ) -> Dict[str, Any]:
        stage = self._get_stage(project_id, stage_name)
        self._validate_stage_status(stage, ["pending"], "start")
        self._validate_previous_stages_completed(project_id, stage.stage_order)
        
        stage.status = "running"
        stage.start_time = datetime.utcnow()
        self.db.commit()
        
        return {
            "stage": stage_name,
            "status": "running",
            "started_at": stage.start_time.isoformat()
        }

    def complete_stage(
        self,
        project_id: int,
        stage_name: str,
        output_artifacts: Optional[Dict[str, Any]] = None,
        triggered_by: Optional[str] = None
    ) -> Dict[str, Any]:
        stage = self._get_stage(project_id, stage_name)
        self._validate_stage_status(stage, ["running"], "complete")
        
        stage.status = "completed"
        stage.end_time = datetime.utcnow()
        
        if stage.start_time:
            stage.duration_seconds = int(
                (stage.end_time - stage.start_time).total_seconds()
            )
        
        if output_artifacts:
            stage.output_artifacts = output_artifacts
        
        self.db.commit()
        
        all_completed = self._check_all_stages_completed(project_id)
        
        if all_completed:
            self._update_project_status(project_id, "COMPLETED")
        
        return {
            "stage": stage_name,
            "status": "completed",
            "duration_seconds": stage.duration_seconds,
            "all_stages_completed": all_completed
        }

    def fail_stage(
        self,
        project_id: int,
        stage_name: str,
        error_message: str
    ) -> Dict[str, Any]:
        stage = self._get_stage(project_id, stage_name)
        self._validate_stage_status(stage, ["running"], "fail")
        
        stage.status = "failed"
        stage.end_time = datetime.utcnow()
        
        if stage.start_time:
            stage.duration_seconds = int(
                (stage.end_time - stage.start_time).total_seconds()
            )
        
        stage.output_artifacts = {"error": error_message}
        self.db.commit()
        
        return {
            "stage": stage_name,
            "status": "failed",
            "error_message": error_message
        }

    def skip_stage(
        self,
        project_id: int,
        stage_name: str,
        reason: str
    ) -> Dict[str, Any]:
        stage = self._get_stage(project_id, stage_name)
        self._validate_stage_status(stage, ["pending"], "skip")
        
        stage.status = "skipped"
        stage.output_artifacts = {"skip_reason": reason}
        self.db.commit()
        
        return {
            "stage": stage_name,
            "status": "skipped",
            "reason": reason
        }

    def _get_stage(self, project_id: int, stage_name: str) -> PipelineStage:
        stage = self.db.query(PipelineStage).filter(
            PipelineStage.project_id == project_id,
            PipelineStage.stage_name == stage_name
        ).first()
        
        if not stage:
            raise HTTPException(status_code=404, detail="Stage not found")
        
        return stage

    def _validate_stage_status(
        self,
        stage: PipelineStage,
        allowed_statuses: list,
        action: str
    ) -> None:
        if stage.status not in allowed_statuses:
            raise HTTPException(
                status_code=400,
                detail=f"Cannot {action} stage with status '{stage.status}'. "
                       f"Stage must be in {allowed_statuses} status."
            )

    def _validate_previous_stages_completed(
        self,
        project_id: int,
        current_stage_order: int
    ) -> None:
        prev_stages = self.db.query(PipelineStage).filter(
            PipelineStage.project_id == project_id,
            PipelineStage.stage_order < current_stage_order
        ).all()
        
        incomplete_prev = [
            s.stage_name for s in prev_stages 
            if s.status != "completed"
        ]
        
        if incomplete_prev:
            raise HTTPException(
                status_code=400,
                detail=f"Previous stages must be completed first: {incomplete_prev}"
            )

    def _check_all_stages_completed(self, project_id: int) -> bool:
        all_stages = self.db.query(PipelineStage).filter(
            PipelineStage.project_id == project_id
        ).all()
        
        return all(s.status == "completed" for s in all_stages)

    def _update_project_status(self, project_id: int, status: str) -> None:
        project = self.db.query(Project).filter(
            Project.id == project_id
        ).first()
        
        if project:
            project.status = status
            self.db.commit()
