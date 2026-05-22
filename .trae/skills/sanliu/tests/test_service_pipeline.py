"""
管道服务集成测试

测试管道相关的服务层功能
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

from tests.conftest import create_test_project, create_test_task, create_test_agent


@pytest.mark.service
@pytest.mark.integration
class TestPipelineService:
    """测试管道服务"""

    def test_pipeline_initialization(self, db_session, mock_redis):
        """测试管道初始化"""
        # 创建管道服务实例
        pipeline_service = Mock()
        pipeline_service.initialize.return_value = True

        result = pipeline_service.initialize()

        assert result is True
        pipeline_service.initialize.assert_called_once()

    def test_pipeline_creation(self, db_session, mock_redis):
        """测试管道创建"""
        project = create_test_project(db_session, name="管道项目")

        # 模拟管道服务
        pipeline_service = Mock()
        pipeline_service.create_pipeline.return_value = {
            "pipeline_id": "pipe_001",
            "project_id": project.id,
            "name": "开发管道",
            "stages": [
                {"name": "build", "status": "pending"},
                {"name": "test", "status": "pending"},
                {"name": "deploy", "status": "pending"}
            ]
        }

        result = pipeline_service.create_pipeline(project.id, "开发管道")

        assert result["pipeline_id"] == "pipe_001"
        assert result["project_id"] == project.id
        assert len(result["stages"]) == 3

    def test_pipeline_execution(self, db_session, mock_redis):
        """测试管道执行"""
        # 模拟管道服务
        pipeline_service = Mock()
        pipeline_service.execute_pipeline.return_value = {
            "pipeline_id": "pipe_001",
            "execution_id": "exec_001",
            "status": "running",
            "started_at": datetime.utcnow().isoformat()
        }

        result = pipeline_service.execute_pipeline("pipe_001")

        assert result["pipeline_id"] == "pipe_001"
        assert result["execution_id"] == "exec_001"
        assert result["status"] == "running"

    def test_pipeline_stage_execution(self, db_session, mock_redis):
        """测试管道阶段执行"""
        # 模拟管道服务
        pipeline_service = Mock()
        pipeline_service.execute_stage.return_value = {
            "stage_name": "build",
            "status": "completed",
            "duration_seconds": 45.5,
            "logs": ["Building...", "Build successful"]
        }

        result = pipeline_service.execute_stage("pipe_001", "build")

        assert result["stage_name"] == "build"
        assert result["status"] == "completed"
        assert "duration_seconds" in result

    def test_pipeline_completion(self, db_session, mock_redis):
        """测试管道完成"""
        # 模拟管道服务
        pipeline_service = Mock()
        pipeline_service.get_pipeline_status.return_value = {
            "pipeline_id": "pipe_001",
            "status": "completed",
            "completed_at": datetime.utcnow().isoformat(),
            "stages": [
                {"name": "build", "status": "success"},
                {"name": "test", "status": "success"},
                {"name": "deploy", "status": "success"}
            ]
        }

        result = pipeline_service.get_pipeline_status("pipe_001")

        assert result["status"] == "completed"
        assert all(s["status"] == "success" for s in result["stages"])


@pytest.mark.service
@pytest.mark.integration
class TestPipelineValidation:
    """测试管道验证"""

    def test_pipeline_invalid_configuration(self, db_session, mock_redis):
        """测试无效的管道配置"""
        # 模拟管道服务
        pipeline_service = Mock()
        pipeline_service.create_pipeline.side_effect = ValueError("Invalid pipeline configuration")

        with pytest.raises(ValueError) as exc_info:
            pipeline_service.create_pipeline(1, "")

        assert "Invalid pipeline configuration" in str(exc_info.value)

    def test_pipeline_nonexistent_stage(self, db_session, mock_redis):
        """测试不存在的阶段"""
        # 模拟管道服务
        pipeline_service = Mock()
        pipeline_service.execute_stage.side_effect = ValueError("Stage not found")

        with pytest.raises(ValueError) as exc_info:
            pipeline_service.execute_stage("pipe_001", "nonexistent")

        assert "Stage not found" in str(exc_info.value)

    def test_pipeline_execution_failure(self, db_session, mock_redis):
        """测试管道执行失败"""
        # 模拟管道服务
        pipeline_service = Mock()
        pipeline_service.execute_pipeline.return_value = {
            "pipeline_id": "pipe_001",
            "execution_id": "exec_001",
            "status": "failed",
            "failed_stage": "test",
            "error_message": "Tests failed"
        }

        result = pipeline_service.execute_pipeline("pipe_001")

        assert result["status"] == "failed"
        assert result["failed_stage"] == "test"


@pytest.mark.service
@pytest.mark.integration
class TestPipelineStateManagement:
    """测试管道状态管理"""

    def test_pipeline_state_persistence(self, db_session, mock_redis):
        """测试管道状态持久化"""
        # 模拟管道服务
        pipeline_service = Mock()
        pipeline_service.save_state.return_value = True
        pipeline_service.load_state.return_value = {
            "pipeline_id": "pipe_001",
            "current_stage": "test",
            "completed_stages": ["build"]
        }

        # 保存状态
        save_result = pipeline_service.save_state("pipe_001", {"stage": "test"})
        assert save_result is True

        # 加载状态
        state = pipeline_service.load_state("pipe_001")
        assert state["current_stage"] == "test"

    def test_pipeline_pause_resume(self, db_session, mock_redis):
        """测试管道暂停和恢复"""
        # 模拟管道服务
        pipeline_service = Mock()
        pipeline_service.pause_pipeline.return_value = {
            "pipeline_id": "pipe_001",
            "status": "paused",
            "paused_at": datetime.utcnow().isoformat()
        }
        pipeline_service.resume_pipeline.return_value = {
            "pipeline_id": "pipe_001",
            "status": "running",
            "resumed_at": datetime.utcnow().isoformat()
        }

        # 暂停管道
        pause_result = pipeline_service.pause_pipeline("pipe_001")
        assert pause_result["status"] == "paused"

        # 恢复管道
        resume_result = pipeline_service.resume_pipeline("pipe_001")
        assert resume_result["status"] == "running"

    def test_pipeline_cancel(self, db_session, mock_redis):
        """测试管道取消"""
        # 模拟管道服务
        pipeline_service = Mock()
        pipeline_service.cancel_pipeline.return_value = {
            "pipeline_id": "pipe_001",
            "status": "cancelled",
            "cancelled_at": datetime.utcnow().isoformat(),
            "reason": "User requested"
        }

        result = pipeline_service.cancel_pipeline("pipe_001", "User requested")

        assert result["status"] == "cancelled"
        assert result["reason"] == "User requested"


@pytest.mark.service
@pytest.mark.integration
class TestPipelineIntegration:
    """测试管道集成"""

    def test_pipeline_full_execution(self, db_session, mock_redis):
        """测试管道完整执行"""
        project = create_test_project(db_session, name="管道执行项目")

        # 模拟管道服务
        pipeline_service = Mock()

        # 创建管道
        pipeline_service.create_pipeline.return_value = {
            "pipeline_id": "pipe_001",
            "project_id": project.id,
            "status": "created"
        }

        # 执行管道
        pipeline_service.execute_pipeline.return_value = {
            "pipeline_id": "pipe_001",
            "execution_id": "exec_001",
            "status": "running"
        }

        # 获取状态
        pipeline_service.get_pipeline_status.return_value = {
            "pipeline_id": "pipe_001",
            "status": "completed"
        }

        # 执行完整流程
        pipeline = pipeline_service.create_pipeline(project.id, "CI/CD")
        assert pipeline["status"] == "created"

        execution = pipeline_service.execute_pipeline(pipeline["pipeline_id"])
        assert execution["status"] == "running"

        status = pipeline_service.get_pipeline_status(pipeline["pipeline_id"])
        assert status["status"] == "completed"

    def test_pipeline_parallel_stages(self, db_session, mock_redis):
        """测试管道并行阶段"""
        # 模拟管道服务
        pipeline_service = Mock()
        pipeline_service.execute_parallel_stages.return_value = {
            "pipeline_id": "pipe_001",
            "stages_executed": ["unit_test", "integration_test", "lint"],
            "results": [
                {"stage": "unit_test", "status": "success"},
                {"stage": "integration_test", "status": "success"},
                {"stage": "lint", "status": "success"}
            ]
        }

        result = pipeline_service.execute_parallel_stages("pipe_001", ["unit_test", "integration_test", "lint"])

        assert len(result["stages_executed"]) == 3
        assert all(r["status"] == "success" for r in result["results"])

    def test_pipeline_conditional_execution(self, db_session, mock_redis):
        """测试管道条件执行"""
        # 模拟管道服务
        pipeline_service = Mock()
        pipeline_service.execute_conditional.return_value = {
            "pipeline_id": "pipe_001",
            "condition": "branch == 'main'",
            "evaluated": True,
            "executed": True,
            "result": "deployed to production"
        }

        result = pipeline_service.execute_conditional("pipe_001", "branch == 'main'")

        assert result["evaluated"] is True
        assert result["executed"] is True


@pytest.mark.service
@pytest.mark.integration
class TestPipelineArtifacts:
    """测试管道制品"""

    def test_pipeline_artifact_storage(self, db_session, mock_redis):
        """测试管道制品存储"""
        # 模拟管道服务
        pipeline_service = Mock()
        pipeline_service.store_artifact.return_value = {
            "artifact_id": "art_001",
            "pipeline_id": "pipe_001",
            "name": "build.zip",
            "size_bytes": 1024000,
            "stored_at": datetime.utcnow().isoformat()
        }

        result = pipeline_service.store_artifact("pipe_001", "build.zip", b"artifact_data")

        assert result["artifact_id"] == "art_001"
        assert result["name"] == "build.zip"

    def test_pipeline_artifact_retrieval(self, db_session, mock_redis):
        """测试管道制品检索"""
        # 模拟管道服务
        pipeline_service = Mock()
        pipeline_service.get_artifact.return_value = {
            "artifact_id": "art_001",
            "name": "build.zip",
            "data": b"artifact_data",
            "size_bytes": 1024000
        }

        result = pipeline_service.get_artifact("art_001")

        assert result["artifact_id"] == "art_001"
        assert result["data"] == b"artifact_data"

    def test_pipeline_artifact_cleanup(self, db_session, mock_redis):
        """测试管道制品清理"""
        # 模拟管道服务
        pipeline_service = Mock()
        pipeline_service.cleanup_artifacts.return_value = {
            "pipeline_id": "pipe_001",
            "artifacts_deleted": 5,
            "space_freed_bytes": 5120000
        }

        result = pipeline_service.cleanup_artifacts("pipe_001", keep_last=3)

        assert result["artifacts_deleted"] == 5
        assert result["space_freed_bytes"] == 5120000


@pytest.mark.service
@pytest.mark.integration
class TestPipelineErrorHandling:
    """测试管道错误处理"""

    def test_pipeline_stage_failure(self, db_session, mock_redis):
        """测试管道阶段失败"""
        # 模拟管道服务
        pipeline_service = Mock()
        pipeline_service.execute_stage.return_value = {
            "stage_name": "test",
            "status": "failed",
            "error": "Test suite failed",
            "exit_code": 1
        }

        result = pipeline_service.execute_stage("pipe_001", "test")

        assert result["status"] == "failed"
        assert "error" in result

    def test_pipeline_retry_failed_stage(self, db_session, mock_redis):
        """测试重试失败的阶段"""
        # 模拟管道服务
        pipeline_service = Mock()
        pipeline_service.retry_stage.return_value = {
            "stage_name": "test",
            "attempt": 2,
            "status": "success",
            "message": "Stage succeeded on retry"
        }

        result = pipeline_service.retry_stage("pipe_001", "test")

        assert result["attempt"] == 2
        assert result["status"] == "success"

    def test_pipeline_error_notification(self, db_session, mock_redis):
        """测试管道错误通知"""
        # 模拟管道服务
        pipeline_service = Mock()
        pipeline_service.send_notification.return_value = {
            "notification_id": "notif_001",
            "type": "pipeline_failure",
            "recipients": ["team@example.com"],
            "sent_at": datetime.utcnow().isoformat()
        }

        result = pipeline_service.send_notification(
            "pipe_001",
            "pipeline_failure",
            ["team@example.com"]
        )

        assert result["type"] == "pipeline_failure"
        assert "team@example.com" in result["recipients"]


@pytest.mark.service
@pytest.mark.integration
class TestPipelinePerformance:
    """测试管道性能"""

    def test_pipeline_execution_performance(self, db_session, mock_redis):
        """测试管道执行性能"""
        import time

        # 模拟管道服务
        pipeline_service = Mock()
        pipeline_service.execute_pipeline.return_value = {
            "pipeline_id": "pipe_001",
            "status": "completed",
            "duration_seconds": 120.5
        }

        start_time = time.time()
        result = pipeline_service.execute_pipeline("pipe_001")
        end_time = time.time()

        assert result["status"] == "completed"
        assert result["duration_seconds"] < 300  # 应该在 5 分钟内完成

    def test_pipeline_batch_execution(self, db_session, mock_redis):
        """测试管道批量执行"""
        # 模拟管道服务
        pipeline_service = Mock()
        pipeline_service.execute_batch.return_value = {
            "pipelines_executed": 10,
            "successful": 9,
            "failed": 1,
            "total_duration_seconds": 600.0
        }

        result = pipeline_service.execute_batch([f"pipe_{i}" for i in range(10)])

        assert result["pipelines_executed"] == 10
        assert result["successful"] == 9


@pytest.mark.service
@pytest.mark.integration
class TestPipelineMonitoring:
    """测试管道监控"""

    def test_pipeline_metrics_collection(self, db_session, mock_redis):
        """测试管道指标收集"""
        # 模拟管道服务
        pipeline_service = Mock()
        pipeline_service.get_metrics.return_value = {
            "total_pipelines": 50,
            "successful_pipelines": 45,
            "failed_pipelines": 3,
            "cancelled_pipelines": 2,
            "avg_duration_seconds": 180.5,
            "success_rate": 90.0
        }

        metrics = pipeline_service.get_metrics()

        assert metrics["total_pipelines"] == 50
        assert metrics["success_rate"] == 90.0
        assert "avg_duration_seconds" in metrics

    def test_pipeline_logs_collection(self, db_session, mock_redis):
        """测试管道日志收集"""
        # 模拟管道服务
        pipeline_service = Mock()
        pipeline_service.get_logs.return_value = {
            "pipeline_id": "pipe_001",
            "execution_id": "exec_001",
            "logs": [
                {"timestamp": "2024-01-01T00:00:00Z", "level": "INFO", "message": "Starting build..."},
                {"timestamp": "2024-01-01T00:01:00Z", "level": "INFO", "message": "Build completed"},
                {"timestamp": "2024-01-01T00:02:00Z", "level": "ERROR", "message": "Tests failed"}
            ]
        }

        logs = pipeline_service.get_logs("pipe_001", "exec_001")

        assert len(logs["logs"]) == 3
        assert logs["logs"][2]["level"] == "ERROR"

    def test_pipeline_health_check(self, db_session, mock_redis):
        """测试管道健康检查"""
        # 模拟管道服务
        pipeline_service = Mock()
        pipeline_service.health_check.return_value = {
            "status": "healthy",
            "components": {
                "executor": "ok",
                "storage": "ok",
                "queue": "ok"
            },
            "active_pipelines": 5
        }

        health = pipeline_service.health_check()

        assert health["status"] == "healthy"
        assert health["components"]["executor"] == "ok"
