"""
管道服务单元测试

测试 StageExecutor, ComplianceChecker 等管道相关服务类
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, MagicMock, patch
from sqlalchemy.orm import Session
from fastapi import HTTPException

from app.services.pipeline.stage_executor import StageExecutor
from app.services.pipeline.compliance_checker import ComplianceChecker
from app.models.pipeline_stage import PipelineStage
from app.models.project import Project, ProjectStatus


@pytest.mark.unit
@pytest.mark.services
class TestStageExecutor:
    """测试 StageExecutor 类"""

    def test_start_stage_success(self, db_session: Session):
        """测试成功启动阶段"""
        project = Project(name="管道测试项目", status=ProjectStatus.DEVELOPMENT.value)
        db_session.add(project)
        db_session.commit()

        stage = PipelineStage(
            project_id=project.id,
            stage_name="代码审查",
            stage_order=1,
            status="pending"
        )
        db_session.add(stage)
        db_session.commit()

        executor = StageExecutor(db_session)
        result = executor.start_stage(project.id, "代码审查")

        assert result["status"] == "running"
        assert result["stage"] == "代码审查"
        assert "started_at" in result

    def test_start_stage_not_found(self, db_session: Session):
        """测试启动不存在的阶段"""
        executor = StageExecutor(db_session)

        with pytest.raises(HTTPException) as exc_info:
            executor.start_stage(99999, "不存在的阶段")

        assert exc_info.value.status_code == 404

    def test_start_stage_wrong_status(self, db_session: Session):
        """测试启动非待处理状态的阶段"""
        project = Project(name="状态测试项目")
        db_session.add(project)
        db_session.commit()

        stage = PipelineStage(
            project_id=project.id,
            stage_name="已完成阶段",
            stage_order=1,
            status="completed"
        )
        db_session.add(stage)
        db_session.commit()

        executor = StageExecutor(db_session)

        with pytest.raises(HTTPException) as exc_info:
            executor.start_stage(project.id, "已完成阶段")

        assert exc_info.value.status_code == 400
        assert "Cannot start" in exc_info.value.detail

    def test_start_stage_previous_not_completed(self, db_session: Session):
        """测试前一阶段未完成时启动"""
        project = Project(name="顺序测试项目")
        db_session.add(project)
        db_session.commit()

        stage1 = PipelineStage(
            project_id=project.id,
            stage_name="阶段1",
            stage_order=1,
            status="pending"
        )
        stage2 = PipelineStage(
            project_id=project.id,
            stage_name="阶段2",
            stage_order=2,
            status="pending"
        )
        db_session.add_all([stage1, stage2])
        db_session.commit()

        executor = StageExecutor(db_session)

        with pytest.raises(HTTPException) as exc_info:
            executor.start_stage(project.id, "阶段2")

        assert exc_info.value.status_code == 400
        assert "Previous stages must be completed" in exc_info.value.detail

    def test_complete_stage_success(self, db_session: Session):
        """测试成功完成阶段"""
        project = Project(name="完成测试项目")
        db_session.add(project)
        db_session.commit()

        stage = PipelineStage(
            project_id=project.id,
            stage_name="运行中阶段",
            stage_order=1,
            status="running",
            start_time=datetime.utcnow()
        )
        db_session.add(stage)
        db_session.commit()

        executor = StageExecutor(db_session)
        result = executor.complete_stage(
            project.id,
            "运行中阶段",
            output_artifacts={"result": "success"}
        )

        assert result["status"] == "completed"
        assert result["duration_seconds"] >= 0
        assert result["all_stages_completed"] == True

    def test_complete_stage_not_running(self, db_session: Session):
        """测试完成非运行中的阶段"""
        project = Project(name="非运行测试项目")
        db_session.add(project)
        db_session.commit()

        stage = PipelineStage(
            project_id=project.id,
            stage_name="待处理阶段",
            stage_order=1,
            status="pending"
        )
        db_session.add(stage)
        db_session.commit()

        executor = StageExecutor(db_session)

        with pytest.raises(HTTPException) as exc_info:
            executor.complete_stage(project.id, "待处理阶段")

        assert exc_info.value.status_code == 400

    def test_fail_stage_success(self, db_session: Session):
        """测试成功标记阶段失败"""
        project = Project(name="失败测试项目")
        db_session.add(project)
        db_session.commit()

        stage = PipelineStage(
            project_id=project.id,
            stage_name="失败阶段",
            stage_order=1,
            status="running",
            start_time=datetime.utcnow()
        )
        db_session.add(stage)
        db_session.commit()

        executor = StageExecutor(db_session)
        result = executor.fail_stage(project.id, "失败阶段", "测试错误")

        assert result["status"] == "failed"
        assert result["error_message"] == "测试错误"

    def test_skip_stage_success(self, db_session: Session):
        """测试成功跳过阶段"""
        project = Project(name="跳过测试项目")
        db_session.add(project)
        db_session.commit()

        stage = PipelineStage(
            project_id=project.id,
            stage_name="跳过阶段",
            stage_order=1,
            status="pending"
        )
        db_session.add(stage)
        db_session.commit()

        executor = StageExecutor(db_session)
        result = executor.skip_stage(project.id, "跳过阶段", "不需要执行")

        assert result["status"] == "skipped"
        assert result["reason"] == "不需要执行"

    def test_complete_all_stages_updates_project(self, db_session: Session):
        """测试所有阶段完成后更新项目状态"""
        project = Project(name="全部完成项目", status=ProjectStatus.DEVELOPMENT.value)
        db_session.add(project)
        db_session.commit()

        stage = PipelineStage(
            project_id=project.id,
            stage_name="最后阶段",
            stage_order=1,
            status="running",
            start_time=datetime.utcnow()
        )
        db_session.add(stage)
        db_session.commit()

        executor = StageExecutor(db_session)
        executor.complete_stage(project.id, "最后阶段")

        db_session.refresh(project)
        assert project.status == "COMPLETED"


@pytest.mark.unit
@pytest.mark.services
class TestComplianceChecker:
    """测试 ComplianceChecker 类"""

    def test_validate_project_exists_success(self, db_session: Session):
        """测试验证项目存在 - 成功"""
        project = Project(name="验证测试项目")
        db_session.add(project)
        db_session.commit()

        checker = ComplianceChecker(db_session)
        result = checker.validate_project_exists(project.id)

        assert result.id == project.id

    def test_validate_project_exists_not_found(self, db_session: Session):
        """测试验证项目存在 - 未找到"""
        checker = ComplianceChecker(db_session)

        with pytest.raises(HTTPException) as exc_info:
            checker.validate_project_exists(99999)

        assert exc_info.value.status_code == 404
        assert "not found" in exc_info.value.detail.lower()

    def test_validate_pipeline_not_initialized_success(self, db_session: Session):
        """测试验证管道未初始化 - 成功"""
        project = Project(name="未初始化项目")
        db_session.add(project)
        db_session.commit()

        checker = ComplianceChecker(db_session)
        checker.validate_pipeline_not_initialized(project.id)

    def test_validate_pipeline_not_initialized_already_exists(self, db_session: Session):
        """测试验证管道未初始化 - 已存在"""
        project = Project(name="已初始化项目")
        db_session.add(project)
        db_session.commit()

        stage = PipelineStage(
            project_id=project.id,
            stage_name="测试阶段",
            stage_order=1
        )
        db_session.add(stage)
        db_session.commit()

        checker = ComplianceChecker(db_session)

        with pytest.raises(HTTPException) as exc_info:
            checker.validate_pipeline_not_initialized(project.id)

        assert exc_info.value.status_code == 400
        assert "already initialized" in exc_info.value.detail.lower()

    def test_validate_pipeline_initialized_success(self, db_session: Session):
        """测试验证管道已初始化 - 成功"""
        project = Project(name="已初始化验证项目")
        db_session.add(project)
        db_session.commit()

        stage = PipelineStage(
            project_id=project.id,
            stage_name="阶段1",
            stage_order=1
        )
        db_session.add(stage)
        db_session.commit()

        checker = ComplianceChecker(db_session)
        result = checker.validate_pipeline_initialized(project.id)

        assert len(result) == 1

    def test_validate_pipeline_initialized_not_found(self, db_session: Session):
        """测试验证管道已初始化 - 未找到"""
        project = Project(name="未初始化验证项目")
        db_session.add(project)
        db_session.commit()

        checker = ComplianceChecker(db_session)

        with pytest.raises(HTTPException) as exc_info:
            checker.validate_pipeline_initialized(project.id)

        assert exc_info.value.status_code == 404
        assert "not initialized" in exc_info.value.detail.lower()

    def test_get_incomplete_previous_stages(self, db_session: Session):
        """测试获取未完成的前置阶段"""
        project = Project(name="前置阶段项目")
        db_session.add(project)
        db_session.commit()

        stages = [
            PipelineStage(project_id=project.id, stage_name="阶段1", stage_order=1, status="completed"),
            PipelineStage(project_id=project.id, stage_name="阶段2", stage_order=2, status="pending"),
            PipelineStage(project_id=project.id, stage_name="阶段3", stage_order=3, status="pending"),
        ]
        db_session.add_all(stages)
        db_session.commit()

        checker = ComplianceChecker(db_session)
        incomplete = checker.get_incomplete_previous_stages(project.id, 3)

        assert len(incomplete) == 1
        assert "阶段2" in incomplete

    def test_check_stage_status_valid(self, db_session: Session):
        """测试检查阶段状态 - 有效"""
        project = Project(name="状态检查项目")
        db_session.add(project)
        db_session.commit()

        stage = PipelineStage(
            project_id=project.id,
            stage_name="测试阶段",
            stage_order=1,
            status="pending"
        )
        db_session.add(stage)
        db_session.commit()

        checker = ComplianceChecker(db_session)
        checker.check_stage_status(stage, ["pending"], "start")

    def test_check_stage_status_invalid(self, db_session: Session):
        """测试检查阶段状态 - 无效"""
        project = Project(name="无效状态项目")
        db_session.add(project)
        db_session.commit()

        stage = PipelineStage(
            project_id=project.id,
            stage_name="测试阶段",
            stage_order=1,
            status="completed"
        )
        db_session.add(stage)
        db_session.commit()

        checker = ComplianceChecker(db_session)

        with pytest.raises(HTTPException) as exc_info:
            checker.check_stage_status(stage, ["pending"], "start")

        assert exc_info.value.status_code == 400

    def test_get_pipeline_progress(self, db_session: Session):
        """测试获取管道进度"""
        project = Project(name="进度测试项目")
        db_session.add(project)
        db_session.commit()

        stages = [
            PipelineStage(project_id=project.id, stage_name="阶段1", stage_order=1, status="completed"),
            PipelineStage(project_id=project.id, stage_name="阶段2", stage_order=2, status="running"),
            PipelineStage(project_id=project.id, stage_name="阶段3", stage_order=3, status="pending"),
        ]
        db_session.add_all(stages)
        db_session.commit()

        checker = ComplianceChecker(db_session)
        progress = checker.get_pipeline_progress(stages)

        assert progress["total_stages"] == 3
        assert progress["completed_stages"] == 1
        assert progress["current_stage"] == "阶段2"
        assert progress["progress_percentage"] == pytest.approx(33.33, rel=0.1)

    def test_get_pipeline_progress_all_completed(self, db_session: Session):
        """测试获取全部完成的管道进度"""
        project = Project(name="全部完成进度项目")
        db_session.add(project)
        db_session.commit()

        stages = [
            PipelineStage(project_id=project.id, stage_name="阶段1", stage_order=1, status="completed"),
            PipelineStage(project_id=project.id, stage_name="阶段2", stage_order=2, status="completed"),
        ]
        db_session.add_all(stages)
        db_session.commit()

        checker = ComplianceChecker(db_session)
        progress = checker.get_pipeline_progress(stages)

        assert progress["completed_stages"] == 2
        assert progress["progress_percentage"] == 100.0
        assert progress["current_stage"] is None

    def test_get_pipeline_progress_empty(self, db_session: Session):
        """测试获取空管道进度"""
        checker = ComplianceChecker(db_session)
        progress = checker.get_pipeline_progress([])

        assert progress["total_stages"] == 0
        assert progress["completed_stages"] == 0
        assert progress["progress_percentage"] == 0


@pytest.mark.unit
@pytest.mark.services
class TestPipelineStageModel:
    """测试 PipelineStage 模型"""

    def test_create_pipeline_stage(self, db_session: Session):
        """测试创建管道阶段"""
        project = Project(name="阶段模型项目")
        db_session.add(project)
        db_session.commit()

        stage = PipelineStage(
            project_id=project.id,
            stage_name="代码审查",
            stage_order=1,
            status="pending",
            requires_human=1
        )
        db_session.add(stage)
        db_session.commit()
        db_session.refresh(stage)

        assert stage.id is not None
        assert stage.stage_name == "代码审查"
        assert stage.status == "pending"
        assert stage.requires_human == 1

    def test_pipeline_stage_timing(self, db_session: Session):
        """测试管道阶段计时"""
        project = Project(name="计时项目")
        db_session.add(project)
        db_session.commit()

        start = datetime.utcnow()
        stage = PipelineStage(
            project_id=project.id,
            stage_name="计时阶段",
            stage_order=1,
            status="completed",
            start_time=start,
            end_time=datetime.utcnow(),
            duration_seconds=120
        )
        db_session.add(stage)
        db_session.commit()
        db_session.refresh(stage)

        assert stage.duration_seconds == 120
        assert stage.start_time is not None
        assert stage.end_time is not None

    def test_pipeline_stage_output_artifacts(self, db_session: Session):
        """测试管道阶段输出产物"""
        project = Project(name="产物项目")
        db_session.add(project)
        db_session.commit()

        stage = PipelineStage(
            project_id=project.id,
            stage_name="构建阶段",
            stage_order=1,
            output_artifacts={
                "build_log": "/logs/build.log",
                "artifact_path": "/artifacts/build.zip"
            }
        )
        db_session.add(stage)
        db_session.commit()
        db_session.refresh(stage)

        assert stage.output_artifacts is not None
        assert "build_log" in stage.output_artifacts
