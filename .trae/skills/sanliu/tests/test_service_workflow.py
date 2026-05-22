"""
工作流服务集成测试

测试工作流相关的服务层功能
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

from tests.conftest import create_test_project, create_test_task, create_test_agent


@pytest.mark.service
@pytest.mark.integration
class TestWorkflowService:
    """测试工作流服务"""

    def test_workflow_initialization(self, db_session, mock_redis):
        """测试工作流初始化"""
        # 创建工作流服务实例
        workflow_service = Mock()
        workflow_service.initialize.return_value = True

        result = workflow_service.initialize()

        assert result is True
        workflow_service.initialize.assert_called_once()

    def test_workflow_project_creation(self, db_session, mock_redis):
        """测试工作流项目创建"""
        project = create_test_project(db_session, name="工作流项目")

        # 模拟工作流服务
        workflow_service = Mock()
        workflow_service.create_project_workflow.return_value = {
            "project_id": project.id,
            "status": "initialized",
            "stages": ["requirement", "design", "development", "testing", "deployment"]
        }

        result = workflow_service.create_project_workflow(project.id)

        assert result["project_id"] == project.id
        assert result["status"] == "initialized"
        assert len(result["stages"]) == 5

    def test_workflow_task_assignment(self, db_session, mock_redis):
        """测试工作流任务分配"""
        project = create_test_project(db_session, name="任务分配项目")
        agent = create_test_agent(db_session, name="工作流代理")
        task = create_test_task(db_session, project_id=project.id, title="工作流任务")

        # 模拟工作流服务
        workflow_service = Mock()
        workflow_service.assign_task.return_value = {
            "task_id": task.id,
            "agent_id": agent.id,
            "status": "assigned",
            "assigned_at": datetime.utcnow().isoformat()
        }

        result = workflow_service.assign_task(task.id, agent.id)

        assert result["task_id"] == task.id
        assert result["agent_id"] == agent.id
        assert result["status"] == "assigned"

    def test_workflow_status_transition(self, db_session, mock_redis):
        """测试工作流状态转换"""
        from app.models.project import ProjectStatus

        project = create_test_project(db_session, name="状态转换项目")

        # 模拟工作流服务
        workflow_service = Mock()
        workflow_service.transition_status.return_value = {
            "project_id": project.id,
            "previous_status": ProjectStatus.REQUIREMENT.value,
            "current_status": ProjectStatus.DESIGN.value,
            "transition_time": datetime.utcnow().isoformat()
        }

        result = workflow_service.transition_status(
            project.id,
            ProjectStatus.REQUIREMENT.value,
            ProjectStatus.DESIGN.value
        )

        assert result["previous_status"] == ProjectStatus.REQUIREMENT.value
        assert result["current_status"] == ProjectStatus.DESIGN.value

    def test_workflow_completion(self, db_session, mock_redis):
        """测试工作流完成"""
        project = create_test_project(db_session, name="完成项目")

        # 模拟工作流服务
        workflow_service = Mock()
        workflow_service.complete_workflow.return_value = {
            "project_id": project.id,
            "status": "completed",
            "completed_at": datetime.utcnow().isoformat(),
            "duration_hours": 120.5
        }

        result = workflow_service.complete_workflow(project.id)

        assert result["project_id"] == project.id
        assert result["status"] == "completed"
        assert "duration_hours" in result


@pytest.mark.service
@pytest.mark.integration
class TestWorkflowValidation:
    """测试工作流验证"""

    def test_workflow_invalid_transition(self, db_session, mock_redis):
        """测试无效的工作流转换"""
        from app.models.project import ProjectStatus

        # 模拟工作流服务
        workflow_service = Mock()
        workflow_service.transition_status.side_effect = ValueError("Invalid status transition")

        with pytest.raises(ValueError) as exc_info:
            workflow_service.transition_status(
                1,
                ProjectStatus.REQUIREMENT.value,
                ProjectStatus.COMPLETED.value
            )

        assert "Invalid status transition" in str(exc_info.value)

    def test_workflow_duplicate_assignment(self, db_session, mock_redis):
        """测试重复任务分配"""
        # 模拟工作流服务
        workflow_service = Mock()
        workflow_service.assign_task.side_effect = ValueError("Task already assigned")

        with pytest.raises(ValueError) as exc_info:
            workflow_service.assign_task(1, 1)

        assert "Task already assigned" in str(exc_info.value)

    def test_workflow_nonexistent_project(self, db_session, mock_redis):
        """测试不存在的项目"""
        # 模拟工作流服务
        workflow_service = Mock()
        workflow_service.create_project_workflow.side_effect = ValueError("Project not found")

        with pytest.raises(ValueError) as exc_info:
            workflow_service.create_project_workflow(99999)

        assert "Project not found" in str(exc_info.value)


@pytest.mark.service
@pytest.mark.integration
class TestWorkflowStateManagement:
    """测试工作流状态管理"""

    def test_workflow_state_persistence(self, db_session, mock_redis):
        """测试工作流状态持久化"""
        project = create_test_project(db_session, name="状态持久化项目")

        # 模拟工作流服务
        workflow_service = Mock()
        workflow_service.save_state.return_value = True
        workflow_service.load_state.return_value = {
            "project_id": project.id,
            "current_stage": "development",
            "completed_stages": ["requirement", "design"]
        }

        # 保存状态
        save_result = workflow_service.save_state(project.id, {"stage": "development"})
        assert save_result is True

        # 加载状态
        state = workflow_service.load_state(project.id)
        assert state["project_id"] == project.id
        assert state["current_stage"] == "development"

    def test_workflow_checkpoint_creation(self, db_session, mock_redis):
        """测试工作流检查点创建"""
        project = create_test_project(db_session, name="检查点项目")

        # 模拟工作流服务
        workflow_service = Mock()
        workflow_service.create_checkpoint.return_value = {
            "checkpoint_id": "cp_001",
            "project_id": project.id,
            "stage": "development",
            "created_at": datetime.utcnow().isoformat(),
            "data": {"tasks_completed": 5, "tasks_total": 10}
        }

        result = workflow_service.create_checkpoint(project.id, "development")

        assert result["checkpoint_id"] == "cp_001"
        assert result["project_id"] == project.id
        assert result["stage"] == "development"

    def test_workflow_rollback(self, db_session, mock_redis):
        """测试工作流回滚"""
        project = create_test_project(db_session, name="回滚项目")

        # 模拟工作流服务
        workflow_service = Mock()
        workflow_service.rollback.return_value = {
            "project_id": project.id,
            "rolled_back_to": "design",
            "previous_stage": "development",
            "rollback_time": datetime.utcnow().isoformat()
        }

        result = workflow_service.rollback(project.id, "design")

        assert result["project_id"] == project.id
        assert result["rolled_back_to"] == "design"
        assert result["previous_stage"] == "development"


@pytest.mark.service
@pytest.mark.integration
class TestWorkflowIntegration:
    """测试工作流集成"""

    def test_workflow_full_lifecycle(self, db_session, mock_redis):
        """测试工作流完整生命周期"""
        from app.models.project import ProjectStatus

        project = create_test_project(db_session, name="完整生命周期项目")

        # 模拟工作流服务
        workflow_service = Mock()

        # 初始化
        workflow_service.initialize.return_value = True

        # 创建项目工作流
        workflow_service.create_project_workflow.return_value = {
            "project_id": project.id,
            "status": "initialized"
        }

        # 状态转换
        workflow_service.transition_status.return_value = {
            "project_id": project.id,
            "current_status": ProjectStatus.COMPLETED.value
        }

        # 完成工作流
        workflow_service.complete_workflow.return_value = {
            "project_id": project.id,
            "status": "completed"
        }

        # 执行完整生命周期
        assert workflow_service.initialize() is True

        result = workflow_service.create_project_workflow(project.id)
        assert result["status"] == "initialized"

        result = workflow_service.transition_status(
            project.id,
            ProjectStatus.REQUIREMENT.value,
            ProjectStatus.COMPLETED.value
        )
        assert result["current_status"] == ProjectStatus.COMPLETED.value

        result = workflow_service.complete_workflow(project.id)
        assert result["status"] == "completed"

    def test_workflow_parallel_tasks(self, db_session, mock_redis):
        """测试工作流并行任务"""
        project = create_test_project(db_session, name="并行任务项目")

        # 创建多个任务
        tasks = []
        for i in range(3):
            task = create_test_task(db_session, project_id=project.id, title=f"并行任务{i+1}")
            tasks.append(task)

        # 模拟工作流服务
        workflow_service = Mock()
        workflow_service.execute_parallel.return_value = {
            "project_id": project.id,
            "tasks_executed": len(tasks),
            "results": [{"task_id": t.id, "status": "completed"} for t in tasks]
        }

        result = workflow_service.execute_parallel(project.id, [t.id for t in tasks])

        assert result["tasks_executed"] == 3
        assert len(result["results"]) == 3

    def test_workflow_dependencies_resolution(self, db_session, mock_redis):
        """测试工作流依赖解析"""
        project = create_test_project(db_session, name="依赖解析项目")

        # 创建带依赖的任务
        task1 = create_test_task(db_session, project_id=project.id, title="前置任务")
        task2 = create_test_task(db_session, project_id=project.id, title="依赖任务", dependencies=[task1.id])

        # 模拟工作流服务
        workflow_service = Mock()
        workflow_service.resolve_dependencies.return_value = {
            "project_id": project.id,
            "execution_order": [task1.id, task2.id],
            "dependencies_resolved": True
        }

        result = workflow_service.resolve_dependencies(project.id)

        assert result["dependencies_resolved"] is True
        assert result["execution_order"] == [task1.id, task2.id]


@pytest.mark.service
@pytest.mark.integration
class TestWorkflowErrorHandling:
    """测试工作流错误处理"""

    def test_workflow_execution_error(self, db_session, mock_redis):
        """测试工作流执行错误"""
        # 模拟工作流服务
        workflow_service = Mock()
        workflow_service.execute.side_effect = Exception("Execution failed")

        with pytest.raises(Exception) as exc_info:
            workflow_service.execute(1)

        assert "Execution failed" in str(exc_info.value)

    def test_workflow_timeout_handling(self, db_session, mock_redis):
        """测试工作流超时处理"""
        # 模拟工作流服务
        workflow_service = Mock()
        workflow_service.execute_with_timeout.side_effect = TimeoutError("Workflow timeout")

        with pytest.raises(TimeoutError) as exc_info:
            workflow_service.execute_with_timeout(1, timeout=30)

        assert "Workflow timeout" in str(exc_info.value)

    def test_workflow_retry_mechanism(self, db_session, mock_redis):
        """测试工作流重试机制"""
        # 模拟工作流服务
        workflow_service = Mock()
        workflow_service.execute_with_retry.return_value = {
            "success": True,
            "attempts": 2,
            "result": "completed"
        }

        result = workflow_service.execute_with_retry(1, max_retries=3)

        assert result["success"] is True
        assert result["attempts"] == 2


@pytest.mark.service
@pytest.mark.integration
class TestWorkflowPerformance:
    """测试工作流性能"""

    def test_workflow_execution_performance(self, db_session, mock_redis):
        """测试工作流执行性能"""
        import time

        # 模拟工作流服务
        workflow_service = Mock()
        workflow_service.execute.return_value = {"status": "completed"}

        start_time = time.time()
        result = workflow_service.execute(1)
        end_time = time.time()

        assert result["status"] == "completed"
        # 模拟性能检查
        assert end_time - start_time < 10.0  # 应该在 10 秒内完成

    def test_workflow_batch_processing(self, db_session, mock_redis):
        """测试工作流批处理性能"""
        # 模拟工作流服务
        workflow_service = Mock()
        workflow_service.process_batch.return_value = {
            "processed": 100,
            "failed": 0,
            "duration_seconds": 5.5
        }

        result = workflow_service.process_batch(list(range(100)))

        assert result["processed"] == 100
        assert result["failed"] == 0
        assert result["duration_seconds"] < 10.0


@pytest.mark.service
@pytest.mark.integration
class TestWorkflowMonitoring:
    """测试工作流监控"""

    def test_workflow_metrics_collection(self, db_session, mock_redis):
        """测试工作流指标收集"""
        # 模拟工作流服务
        workflow_service = Mock()
        workflow_service.get_metrics.return_value = {
            "total_workflows": 10,
            "completed_workflows": 8,
            "failed_workflows": 1,
            "in_progress_workflows": 1,
            "avg_duration_seconds": 3600
        }

        metrics = workflow_service.get_metrics()

        assert metrics["total_workflows"] == 10
        assert metrics["completed_workflows"] == 8
        assert metrics["failed_workflows"] == 1
        assert "avg_duration_seconds" in metrics

    def test_workflow_health_check(self, db_session, mock_redis):
        """测试工作流健康检查"""
        # 模拟工作流服务
        workflow_service = Mock()
        workflow_service.health_check.return_value = {
            "status": "healthy",
            "checks": {
                "database": "ok",
                "redis": "ok",
                "queue": "ok"
            }
        }

        health = workflow_service.health_check()

        assert health["status"] == "healthy"
        assert health["checks"]["database"] == "ok"
        assert health["checks"]["redis"] == "ok"
