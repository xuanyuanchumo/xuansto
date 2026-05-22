import pytest
from datetime import datetime
from unittest.mock import Mock, patch


class TestStageExecutor:
    
    def test_start_stage_success(self, db_session):
        from app.services.pipeline.stage_executor import StageExecutor
        from app.models.pipeline_stage import PipelineStage
        from tests.conftest import create_test_project
        
        project = create_test_project(db_session, name="测试项目")
        
        stage1 = PipelineStage(
            project_id=project.id,
            stage_name="requirement",
            stage_order=1,
            status="completed",
            requires_human=0
        )
        stage2 = PipelineStage(
            project_id=project.id,
            stage_name="design",
            stage_order=2,
            status="pending",
            requires_human=0
        )
        db_session.add_all([stage1, stage2])
        db_session.commit()
        
        executor = StageExecutor(db_session)
        result = executor.start_stage(project.id, "design")
        
        assert result["status"] == "running"
        assert "started_at" in result

    def test_start_stage_not_found(self, db_session):
        from app.services.pipeline.stage_executor import StageExecutor
        from fastapi import HTTPException
        
        executor = StageExecutor(db_session)
        
        with pytest.raises(HTTPException) as exc_info:
            executor.start_stage(99999, "nonexistent")
        
        assert exc_info.value.status_code == 404

    def test_start_stage_wrong_status(self, db_session):
        from app.services.pipeline.stage_executor import StageExecutor
        from app.models.pipeline_stage import PipelineStage
        from tests.conftest import create_test_project
        from fastapi import HTTPException
        
        project = create_test_project(db_session, name="测试项目")
        
        stage = PipelineStage(
            project_id=project.id,
            stage_name="requirement",
            stage_order=1,
            status="running",
            requires_human=0
        )
        db_session.add(stage)
        db_session.commit()
        
        executor = StageExecutor(db_session)
        
        with pytest.raises(HTTPException) as exc_info:
            executor.start_stage(project.id, "requirement")
        
        assert exc_info.value.status_code == 400

    def test_start_stage_previous_not_completed(self, db_session):
        from app.services.pipeline.stage_executor import StageExecutor
        from app.models.pipeline_stage import PipelineStage
        from tests.conftest import create_test_project
        from fastapi import HTTPException
        
        project = create_test_project(db_session, name="测试项目")
        
        stage1 = PipelineStage(
            project_id=project.id,
            stage_name="requirement",
            stage_order=1,
            status="pending",
            requires_human=0
        )
        stage2 = PipelineStage(
            project_id=project.id,
            stage_name="design",
            stage_order=2,
            status="pending",
            requires_human=0
        )
        db_session.add_all([stage1, stage2])
        db_session.commit()
        
        executor = StageExecutor(db_session)
        
        with pytest.raises(HTTPException) as exc_info:
            executor.start_stage(project.id, "design")
        
        assert exc_info.value.status_code == 400

    def test_complete_stage_success(self, db_session):
        from app.services.pipeline.stage_executor import StageExecutor
        from app.models.pipeline_stage import PipelineStage
        from tests.conftest import create_test_project
        
        project = create_test_project(db_session, name="测试项目")
        
        stage = PipelineStage(
            project_id=project.id,
            stage_name="requirement",
            stage_order=1,
            status="running",
            requires_human=0,
            start_time=datetime.utcnow()
        )
        db_session.add(stage)
        db_session.commit()
        
        executor = StageExecutor(db_session)
        result = executor.complete_stage(
            project.id, 
            "requirement",
            output_artifacts={"doc": "requirement.md"}
        )
        
        assert result["status"] == "completed"
        assert "duration_seconds" in result

    def test_complete_stage_not_running(self, db_session):
        from app.services.pipeline.stage_executor import StageExecutor
        from app.models.pipeline_stage import PipelineStage
        from tests.conftest import create_test_project
        from fastapi import HTTPException
        
        project = create_test_project(db_session, name="测试项目")
        
        stage = PipelineStage(
            project_id=project.id,
            stage_name="requirement",
            stage_order=1,
            status="pending",
            requires_human=0
        )
        db_session.add(stage)
        db_session.commit()
        
        executor = StageExecutor(db_session)
        
        with pytest.raises(HTTPException) as exc_info:
            executor.complete_stage(project.id, "requirement")
        
        assert exc_info.value.status_code == 400

    def test_fail_stage_success(self, db_session):
        from app.services.pipeline.stage_executor import StageExecutor
        from app.models.pipeline_stage import PipelineStage
        from tests.conftest import create_test_project
        
        project = create_test_project(db_session, name="测试项目")
        
        stage = PipelineStage(
            project_id=project.id,
            stage_name="requirement",
            stage_order=1,
            status="running",
            requires_human=0,
            start_time=datetime.utcnow()
        )
        db_session.add(stage)
        db_session.commit()
        
        executor = StageExecutor(db_session)
        result = executor.fail_stage(project.id, "requirement", "测试失败")
        
        assert result["status"] == "failed"
        assert result["error_message"] == "测试失败"

    def test_skip_stage_success(self, db_session):
        from app.services.pipeline.stage_executor import StageExecutor
        from app.models.pipeline_stage import PipelineStage
        from tests.conftest import create_test_project
        
        project = create_test_project(db_session, name="测试项目")
        
        stage = PipelineStage(
            project_id=project.id,
            stage_name="requirement",
            stage_order=1,
            status="pending",
            requires_human=0
        )
        db_session.add(stage)
        db_session.commit()
        
        executor = StageExecutor(db_session)
        result = executor.skip_stage(project.id, "requirement", "测试跳过")
        
        assert result["status"] == "skipped"
        assert result["reason"] == "测试跳过"


class TestPerformanceMiddleware:
    
    def test_middleware_initialization(self):
        from app.services.performance import PerformanceMiddleware
        from unittest.mock import MagicMock
        
        app = MagicMock()
        middleware = PerformanceMiddleware(app, slow_threshold_ms=100.0)
        
        assert middleware.slow_threshold_ms == 100.0
        assert middleware.request_stats["total_requests"] == 0

    def test_get_stats_empty(self):
        from app.services.performance import PerformanceMiddleware, get_performance_stats
        from unittest.mock import MagicMock
        
        app = MagicMock()
        middleware = PerformanceMiddleware(app)
        
        stats = middleware.get_stats()
        
        assert stats["total_requests"] == 0
        assert stats["slow_requests"] == 0
        assert stats["avg_response_time_ms"] == 0
        assert stats["endpoints"] == []

    def test_get_stats_with_data(self):
        from app.services.performance import PerformanceMiddleware
        from unittest.mock import MagicMock
        
        app = MagicMock()
        middleware = PerformanceMiddleware(app)
        
        middleware.request_stats["total_requests"] = 10
        middleware.request_stats["slow_requests"] = 2
        middleware.request_stats["total_time_ms"] = 500.0
        middleware.request_stats["endpoint_stats"]["GET /api/test"] = {
            "count": 10,
            "total_ms": 500.0,
            "min_ms": 10.0,
            "max_ms": 100.0,
            "slow_count": 2
        }
        
        stats = middleware.get_stats()
        
        assert stats["total_requests"] == 10
        assert stats["slow_requests"] == 2
        assert stats["slow_rate"] == 20.0
        assert stats["avg_response_time_ms"] == 50.0
        assert len(stats["endpoints"]) == 1

    def test_get_performance_stats_no_instance(self):
        from app.services import performance
        
        performance.performance_middleware_instance = None
        
        stats = performance.get_performance_stats()
        
        assert "error" in stats
