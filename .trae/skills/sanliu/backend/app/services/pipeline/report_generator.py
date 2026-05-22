from typing import List, Dict, Any
from datetime import datetime

from ...models.pipeline_stage import PipelineStage


class PipelineReportGenerator:
    PIPELINE_STAGES = [
        {"name": "requirement_structuring", "order": 1, "requires_human": 1, "description": "需求结构化分析"},
        {"name": "test_first", "order": 2, "requires_human": 1, "description": "测试优先设计"},
        {"name": "implementation_with_decisions", "order": 3, "requires_human": 1, "description": "实现与决策记录"},
        {"name": "static_analysis", "order": 4, "requires_human": 0, "description": "静态代码分析"},
        {"name": "test_execution", "order": 5, "requires_human": 0, "description": "测试执行"},
        {"name": "acceptance_report", "order": 6, "requires_human": 1, "description": "验收报告生成"},
        {"name": "human_gate", "order": 7, "requires_human": 1, "description": "人工审批关卡"},
    ]

    @classmethod
    def generate_initialization_report(
        cls,
        project_id: int,
        stages_count: int
    ) -> Dict[str, Any]:
        return {
            "project_id": project_id,
            "stages_created": stages_count,
            "message": "Pipeline initialized successfully"
        }

    @classmethod
    def generate_reset_report(cls, project_id: int) -> Dict[str, Any]:
        return {
            "project_id": project_id,
            "message": "Pipeline reset successfully"
        }

    @classmethod
    def generate_summary_report(
        cls,
        project_id: int,
        stages: List[PipelineStage]
    ) -> Dict[str, Any]:
        total_stages = len(stages)
        completed_stages = sum(1 for s in stages if s.status == "completed")
        
        current_stage = cls._find_current_stage(stages)
        progress_percentage = cls._calculate_progress(
            completed_stages, 
            total_stages
        )
        
        return {
            "project_id": project_id,
            "total_stages": total_stages,
            "completed_stages": completed_stages,
            "current_stage": current_stage,
            "progress_percentage": progress_percentage,
            "stages": stages
        }

    @classmethod
    def generate_stage_report(
        cls,
        stage_name: str,
        status: str,
        **kwargs
    ) -> Dict[str, Any]:
        report = {
            "stage": stage_name,
            "status": status
        }
        report.update(kwargs)
        return report

    @classmethod
    def get_pipeline_stages_config(cls) -> List[Dict[str, Any]]:
        return cls.PIPELINE_STAGES

    @staticmethod
    def _find_current_stage(stages: List[PipelineStage]) -> str:
        for stage in stages:
            if stage.status in ["pending", "running"]:
                return stage.stage_name
        return None

    @staticmethod
    def _calculate_progress(completed: int, total: int) -> float:
        if total == 0:
            return 0.0
        return round((completed / total) * 100, 2)
