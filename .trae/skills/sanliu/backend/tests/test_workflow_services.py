"""
工作流服务单元测试

测试 StateTransitionManager、StatusValidator、WorkflowExecutor、WorkflowHistory 等类
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from fastapi import HTTPException

from app.services.workflow.state_transitions import StateTransitionManager
from app.services.workflow.validators import StatusValidator as WorkflowStatusValidator
from app.models.project import ProjectStatus, PROJECT_STATUS_TRANSITIONS
from app.models.task import TaskStatus, TASK_STATUS_TRANSITIONS


@pytest.mark.unit
@pytest.mark.services
class TestStateTransitionManager:
    """测试 StateTransitionManager 类"""

    def test_get_allowed_transitions_existing_status(self):
        """测试获取允许的状态转换 - 存在的状态"""
        transitions = StateTransitionManager.get_allowed_transitions(
            ProjectStatus.REQUIREMENT,
            PROJECT_STATUS_TRANSITIONS
        )

        assert len(transitions) > 0
        assert ProjectStatus.DESIGN in transitions

    def test_get_allowed_transitions_empty_transitions(self):
        """测试获取允许的状态转换 - 空转换列表"""
        transitions = StateTransitionManager.get_allowed_transitions(
            "UNKNOWN_STATUS",
            {}
        )

        assert transitions == []

    def test_get_project_transitions_requirement(self):
        """测试项目状态转换 - 需求阶段"""
        transitions = StateTransitionManager.get_project_transitions(ProjectStatus.REQUIREMENT)

        assert ProjectStatus.DESIGN in transitions

    def test_get_project_transitions_design(self):
        """测试项目状态转换 - 设计阶段"""
        transitions = StateTransitionManager.get_project_transitions(ProjectStatus.DESIGN)

        assert ProjectStatus.DEVELOPMENT in transitions

    def test_get_project_transitions_completed(self):
        """测试项目状态转换 - 已完成"""
        transitions = StateTransitionManager.get_project_transitions(ProjectStatus.COMPLETED)

        assert transitions == []

    def test_get_task_transitions_pending(self):
        """测试任务状态转换 - 待处理"""
        transitions = StateTransitionManager.get_task_transitions(TaskStatus.PENDING)

        assert TaskStatus.IN_PROGRESS in transitions

    def test_get_task_transitions_in_progress(self):
        """测试任务状态转换 - 进行中"""
        transitions = StateTransitionManager.get_task_transitions(TaskStatus.IN_PROGRESS)

        assert TaskStatus.COMPLETED in transitions or TaskStatus.REVIEW in transitions

    def test_format_transitions_response(self):
        """测试格式化状态转换响应"""
        response = StateTransitionManager.format_transitions_response(
            ProjectStatus.REQUIREMENT,
            [ProjectStatus.DESIGN, ProjectStatus.CANCELLED]
        )

        assert response["current_status"] == "REQUIREMENT"
        assert "DESIGN" in response["allowed_transitions"]
        assert "CANCELLED" in response["allowed_transitions"]

    def test_format_transitions_response_empty(self):
        """测试格式化状态转换响应 - 空转换"""
        response = StateTransitionManager.format_transitions_response(
            ProjectStatus.COMPLETED,
            []
        )

        assert response["current_status"] == "COMPLETED"
        assert response["allowed_transitions"] == []


@pytest.mark.unit
@pytest.mark.services
class TestWorkflowStatusValidator:
    """测试工作流状态验证器"""

    def test_validate_status_valid(self):
        """测试验证状态 - 有效"""
        result = WorkflowStatusValidator.validate_status("REQUIREMENT", ProjectStatus)

        assert result == ProjectStatus.REQUIREMENT

    def test_validate_status_invalid(self):
        """测试验证状态 - 无效"""
        with pytest.raises(HTTPException) as exc_info:
            WorkflowStatusValidator.validate_status("INVALID_STATUS", ProjectStatus)

        assert exc_info.value.status_code == 400
        assert "Invalid status" in exc_info.value.detail

    def test_validate_transition_valid(self):
        """测试验证状态转换 - 有效"""
        WorkflowStatusValidator.validate_transition(
            ProjectStatus.REQUIREMENT,
            ProjectStatus.DESIGN,
            PROJECT_STATUS_TRANSITIONS
        )

    def test_validate_transition_invalid(self):
        """测试验证状态转换 - 无效"""
        with pytest.raises(HTTPException) as exc_info:
            WorkflowStatusValidator.validate_transition(
                ProjectStatus.REQUIREMENT,
                ProjectStatus.COMPLETED,
                PROJECT_STATUS_TRANSITIONS
            )

        assert exc_info.value.status_code == 400
        assert "Cannot transition" in exc_info.value.detail

    def test_validate_entity_type_project(self):
        """测试验证实体类型 - 项目"""
        WorkflowStatusValidator.validate_entity_type("project")

    def test_validate_entity_type_task(self):
        """测试验证实体类型 - 任务"""
        WorkflowStatusValidator.validate_entity_type("task")

    def test_validate_entity_type_invalid(self):
        """测试验证实体类型 - 无效"""
        with pytest.raises(HTTPException) as exc_info:
            WorkflowStatusValidator.validate_entity_type("invalid")

        assert exc_info.value.status_code == 400
        assert "Invalid entity type" in exc_info.value.detail

    def test_validate_project_status_valid(self):
        """测试验证项目状态 - 有效"""
        result = WorkflowStatusValidator.validate_project_status("DESIGN")

        assert result == ProjectStatus.DESIGN

    def test_validate_project_status_invalid(self):
        """测试验证项目状态 - 无效"""
        with pytest.raises(HTTPException) as exc_info:
            WorkflowStatusValidator.validate_project_status("INVALID")

        assert exc_info.value.status_code == 400

    def test_validate_task_status_valid(self):
        """测试验证任务状态 - 有效"""
        result = WorkflowStatusValidator.validate_task_status("IN_PROGRESS")

        assert result == TaskStatus.IN_PROGRESS

    def test_validate_task_status_invalid(self):
        """测试验证任务状态 - 无效"""
        with pytest.raises(HTTPException) as exc_info:
            WorkflowStatusValidator.validate_task_status("INVALID")

        assert exc_info.value.status_code == 400


@pytest.mark.unit
@pytest.mark.services
class TestProjectStatusTransitions:
    """测试项目状态转换规则"""

    def test_requirement_can_transition_to_design(self):
        """测试需求阶段可转换到设计阶段"""
        assert ProjectStatus.DESIGN in PROJECT_STATUS_TRANSITIONS.get(ProjectStatus.REQUIREMENT, [])

    def test_design_can_transition_to_development(self):
        """测试设计阶段可转换到开发阶段"""
        assert ProjectStatus.DEVELOPMENT in PROJECT_STATUS_TRANSITIONS.get(ProjectStatus.DESIGN, [])

    def test_development_can_transition_to_testing(self):
        """测试开发阶段可转换到测试阶段"""
        assert ProjectStatus.TESTING in PROJECT_STATUS_TRANSITIONS.get(ProjectStatus.DEVELOPMENT, [])

    def test_testing_can_transition_to_completed(self):
        """测试测试阶段可转换到完成阶段"""
        assert ProjectStatus.COMPLETED in PROJECT_STATUS_TRANSITIONS.get(ProjectStatus.TESTING, [])

    def test_any_status_can_transition_to_cancelled(self):
        """测试任何状态可转换到取消状态"""
        for status in [ProjectStatus.REQUIREMENT, ProjectStatus.DESIGN, 
                       ProjectStatus.DEVELOPMENT, ProjectStatus.TESTING]:
            assert ProjectStatus.CANCELLED in PROJECT_STATUS_TRANSITIONS.get(status, [])

    def test_completed_has_no_transitions(self):
        """测试完成状态无转换"""
        assert PROJECT_STATUS_TRANSITIONS.get(ProjectStatus.COMPLETED, []) == []

    def test_cancelled_has_no_transitions(self):
        """测试取消状态无转换"""
        assert PROJECT_STATUS_TRANSITIONS.get(ProjectStatus.CANCELLED, []) == []


@pytest.mark.unit
@pytest.mark.services
class TestTaskStatusTransitions:
    """测试任务状态转换规则"""

    def test_pending_can_transition_to_in_progress(self):
        """测试待处理可转换到进行中"""
        assert TaskStatus.IN_PROGRESS in TASK_STATUS_TRANSITIONS.get(TaskStatus.PENDING, [])

    def test_in_progress_can_transition_to_review(self):
        """测试进行中可转换到审核中"""
        assert TaskStatus.REVIEW in TASK_STATUS_TRANSITIONS.get(TaskStatus.IN_PROGRESS, [])

    def test_review_can_transition_to_completed(self):
        """测试审核中可转换到已完成"""
        assert TaskStatus.COMPLETED in TASK_STATUS_TRANSITIONS.get(TaskStatus.REVIEW, [])

    def test_review_can_transition_to_in_progress(self):
        """测试审核中可转换回进行中"""
        assert TaskStatus.IN_PROGRESS in TASK_STATUS_TRANSITIONS.get(TaskStatus.REVIEW, [])

    def test_completed_has_no_transitions(self):
        """测试已完成状态无转换"""
        assert TASK_STATUS_TRANSITIONS.get(TaskStatus.COMPLETED, []) == []

    def test_cancelled_has_no_transitions(self):
        """测试已取消状态无转换"""
        assert TASK_STATUS_TRANSITIONS.get(TaskStatus.CANCELLED, []) == []
