"""
数据库模型验证测试

测试所有数据库模型的基本 CRUD 操作、属性验证和关系验证
"""

import pytest
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.models.project import Project, ProjectStatus
from app.models.task import Task, TaskStatus, TaskPriority
from app.models.agent import Agent
from app.models.department import Department
from app.models.skill_call import SkillCall
from app.models.assignment import Assignment
from app.models.acceptance_test import AcceptanceTest
from app.models.code_change import CodeChange
from app.models.decision_log import DecisionLog
from app.models.human_approval import HumanApproval
from app.models.input_output_trace import InputOutputTrace
from app.models.intermediate_artifact import IntermediateArtifact
from app.models.milestone import Milestone, MilestoneStatus
from app.models.mutation_test_result import MutationTestResult
from app.models.non_functional_check import NonFunctionalCheck
from app.models.pipeline_stage import PipelineStage
from app.models.requirement_trace import RequirementTrace
from app.models.clarification_question import ClarificationQuestion


@pytest.mark.database
@pytest.mark.models
class TestProjectModel:
    """测试 Project 模型"""

    def test_create_project(self, db_session: Session):
        """测试创建项目"""
        project = Project(
            name="测试项目",
            description="项目描述",
            tech_stack=["Python", "FastAPI"],
            status=ProjectStatus.REQUIREMENT.value
        )
        db_session.add(project)
        db_session.commit()
        db_session.refresh(project)

        assert project.id is not None
        assert project.name == "测试项目"
        assert project.status == ProjectStatus.REQUIREMENT.value
        assert project.created_at is not None

    def test_read_project(self, db_session: Session):
        """测试读取项目"""
        project = Project(name="读取测试项目")
        db_session.add(project)
        db_session.commit()

        found = db_session.query(Project).filter_by(name="读取测试项目").first()
        assert found is not None
        assert found.name == "读取测试项目"

    def test_update_project(self, db_session: Session):
        """测试更新项目"""
        project = Project(name="更新前项目")
        db_session.add(project)
        db_session.commit()

        project.name = "更新后项目"
        project.status = ProjectStatus.DESIGN.value
        db_session.commit()
        db_session.refresh(project)

        assert project.name == "更新后项目"
        assert project.status == ProjectStatus.DESIGN.value

    def test_delete_project(self, db_session: Session):
        """测试删除项目"""
        project = Project(name="待删除项目")
        db_session.add(project)
        db_session.commit()
        project_id = project.id

        db_session.delete(project)
        db_session.commit()

        deleted = db_session.query(Project).filter_by(id=project_id).first()
        assert deleted is None

    def test_project_status_history(self, db_session: Session):
        """测试项目状态历史"""
        project = Project(
            name="状态历史项目",
            status_history=[
                {"status": "DESIGN", "timestamp": datetime.utcnow().isoformat()}
            ]
        )
        db_session.add(project)
        db_session.commit()
        db_session.refresh(project)

        assert len(project.status_history) == 1
        assert project.status_history[0]["status"] == "DESIGN"

    def test_project_milestones(self, db_session: Session):
        """测试项目里程碑"""
        project = Project(
            name="里程碑项目",
            milestones=[
                {"name": "阶段1", "completed": True},
                {"name": "阶段2", "completed": False}
            ]
        )
        db_session.add(project)
        db_session.commit()
        db_session.refresh(project)

        assert len(project.milestones) == 2


@pytest.mark.database
@pytest.mark.models
class TestTaskModel:
    """测试 Task 模型"""

    def test_create_task(self, db_session: Session):
        """测试创建任务"""
        project = Project(name="任务项目")
        db_session.add(project)
        db_session.commit()

        task = Task(
            title="测试任务",
            description="任务描述",
            project_id=project.id,
            status=TaskStatus.PENDING.value,
            priority=TaskPriority.HIGH.value
        )
        db_session.add(task)
        db_session.commit()
        db_session.refresh(task)

        assert task.id is not None
        assert task.title == "测试任务"
        assert task.status == TaskStatus.PENDING.value
        assert task.priority == TaskPriority.HIGH.value

    def test_task_project_relationship(self, db_session: Session):
        """测试任务与项目的关系"""
        project = Project(name="关系测试项目")
        db_session.add(project)
        db_session.commit()

        task = Task(title="关系测试任务", project_id=project.id)
        db_session.add(task)
        db_session.commit()
        db_session.refresh(task)

        assert task.project is not None
        assert task.project.name == "关系测试项目"

    def test_task_dependencies(self, db_session: Session):
        """测试任务依赖"""
        project = Project(name="依赖测试项目")
        db_session.add(project)
        db_session.commit()

        task1 = Task(title="任务1", project_id=project.id)
        task2 = Task(title="任务2", project_id=project.id, dependencies=[1])
        db_session.add_all([task1, task2])
        db_session.commit()
        db_session.refresh(task2)

        assert task2.dependencies == [1]

    def test_task_estimated_hours(self, db_session: Session):
        """测试任务预估工时"""
        project = Project(name="工时测试项目")
        db_session.add(project)
        db_session.commit()

        task = Task(
            title="工时测试任务",
            project_id=project.id,
            estimated_hours=8.5,
            actual_hours=7.0
        )
        db_session.add(task)
        db_session.commit()
        db_session.refresh(task)

        assert task.estimated_hours == 8.5
        assert task.actual_hours == 7.0


@pytest.mark.database
@pytest.mark.models
class TestAgentModel:
    """测试 Agent 模型"""

    def test_create_agent(self, db_session: Session):
        """测试创建代理"""
        agent = Agent(
            name="测试代理",
            role="Developer",
            skills=["Python", "JavaScript"],
            status="idle",
            max_load=10
        )
        db_session.add(agent)
        db_session.commit()
        db_session.refresh(agent)

        assert agent.id is not None
        assert agent.name == "测试代理"
        assert agent.role == "Developer"
        assert agent.skills == ["Python", "JavaScript"]

    def test_agent_unique_name(self, db_session: Session):
        """测试代理名称唯一性"""
        agent1 = Agent(name="唯一代理")
        db_session.add(agent1)
        db_session.commit()

        agent2 = Agent(name="唯一代理")
        db_session.add(agent2)
        with pytest.raises(IntegrityError):
            db_session.commit()

    def test_agent_department_relationship(self, db_session: Session):
        """测试代理与部门的关系"""
        department = Department(name="工程部", pinyin="gongchengbu")
        db_session.add(department)
        db_session.commit()

        agent = Agent(name="部门代理", department_id=department.id)
        db_session.add(agent)
        db_session.commit()
        db_session.refresh(agent)

        assert agent.department is not None
        assert agent.department.name == "工程部"

    def test_agent_load_management(self, db_session: Session):
        """测试代理负载管理"""
        agent = Agent(name="负载代理", current_load=3, max_load=5)
        db_session.add(agent)
        db_session.commit()
        db_session.refresh(agent)

        assert agent.current_load == 3
        assert agent.max_load == 5


@pytest.mark.database
@pytest.mark.models
class TestDepartmentModel:
    """测试 Department 模型"""

    def test_create_department(self, db_session: Session):
        """测试创建部门"""
        department = Department(
            name="研发部",
            pinyin="yanfabu",
            level="L1"
        )
        db_session.add(department)
        db_session.commit()
        db_session.refresh(department)

        assert department.id is not None
        assert department.name == "研发部"
        assert department.pinyin == "yanfabu"

    def test_department_hierarchy(self, db_session: Session):
        """测试部门层级关系"""
        parent = Department(name="总公司", pinyin="zonggongsi")
        db_session.add(parent)
        db_session.commit()

        child = Department(
            name="分公司",
            pinyin="fengongsi",
            parent_id=parent.id
        )
        db_session.add(child)
        db_session.commit()
        db_session.refresh(child)

        assert child.parent is not None
        assert child.parent.name == "总公司"

    def test_department_pinyin_unique(self, db_session: Session):
        """测试部门拼音唯一性"""
        dept1 = Department(name="部门1", pinyin="bumen")
        db_session.add(dept1)
        db_session.commit()

        dept2 = Department(name="部门2", pinyin="bumen")
        db_session.add(dept2)
        with pytest.raises(IntegrityError):
            db_session.commit()


@pytest.mark.database
@pytest.mark.models
class TestSkillCallModel:
    """测试 SkillCall 模型"""

    def test_create_skill_call(self, db_session: Session):
        """测试创建技能调用"""
        call = SkillCall(
            skill_name="code_generation",
            caller="agent_001",
            status="started",
            details={"language": "python"}
        )
        db_session.add(call)
        db_session.commit()
        db_session.refresh(call)

        assert call.id is not None
        assert call.skill_name == "code_generation"
        assert call.caller == "agent_001"

    def test_skill_call_parent_child_relationship(self, db_session: Session):
        """测试技能调用的父子关系"""
        parent = SkillCall(skill_name="parent_skill", caller="agent_001")
        db_session.add(parent)
        db_session.commit()

        child = SkillCall(
            skill_name="child_skill",
            caller="agent_001",
            parent_call_id=parent.id
        )
        db_session.add(child)
        db_session.commit()
        db_session.refresh(child)

        assert child.parent is not None
        assert child.parent.skill_name == "parent_skill"

    def test_skill_call_input_output(self, db_session: Session):
        """测试技能调用的输入输出"""
        call = SkillCall(
            skill_name="test_skill",
            caller="agent_001",
            input_data={"param": "value"},
            output_data={"result": "success"}
        )
        db_session.add(call)
        db_session.commit()
        db_session.refresh(call)

        assert call.input_data == {"param": "value"}
        assert call.output_data == {"result": "success"}


@pytest.mark.database
@pytest.mark.models
class TestAssignmentModel:
    """测试 Assignment 模型"""

    def test_create_assignment(self, db_session: Session):
        """测试创建分配"""
        project = Project(name="分配项目")
        db_session.add(project)
        db_session.commit()

        task = Task(title="分配任务", project_id=project.id)
        db_session.add(task)
        db_session.commit()

        agent = Agent(name="分配代理")
        db_session.add(agent)
        db_session.commit()

        assignment = Assignment(
            agent_id=agent.id,
            task_id=task.id,
            status="assigned"
        )
        db_session.add(assignment)
        db_session.commit()
        db_session.refresh(assignment)

        assert assignment.id is not None
        assert assignment.status == "assigned"

    def test_assignment_relationships(self, db_session: Session):
        """测试分配关系"""
        project = Project(name="关系分配项目")
        db_session.add(project)
        db_session.commit()

        task = Task(title="关系分配任务", project_id=project.id)
        db_session.add(task)
        db_session.commit()

        agent = Agent(name="关系分配代理")
        db_session.add(agent)
        db_session.commit()

        assignment = Assignment(agent_id=agent.id, task_id=task.id)
        db_session.add(assignment)
        db_session.commit()
        db_session.refresh(assignment)

        assert assignment.agent is not None
        assert assignment.task is not None


@pytest.mark.database
@pytest.mark.models
class TestAcceptanceTestModel:
    """测试 AcceptanceTest 模型"""

    def test_create_acceptance_test(self, db_session: Session):
        """测试创建验收测试"""
        project = Project(name="验收测试项目")
        db_session.add(project)
        db_session.commit()

        test = AcceptanceTest(
            project_id=project.id,
            scenario_name="用户登录场景",
            given="用户在登录页面",
            when="输入正确的用户名和密码",
            then="成功登录并跳转到首页"
        )
        db_session.add(test)
        db_session.commit()
        db_session.refresh(test)

        assert test.id is not None
        assert test.scenario_name == "用户登录场景"

    def test_acceptance_test_shadow_test(self, db_session: Session):
        """测试影子测试功能"""
        project = Project(name="影子测试项目")
        db_session.add(project)
        db_session.commit()

        test = AcceptanceTest(
            project_id=project.id,
            scenario_name="影子测试场景",
            is_shadow_test=True,
            shadow_comparison={"diff": "无差异"}
        )
        db_session.add(test)
        db_session.commit()
        db_session.refresh(test)

        assert test.is_shadow_test is True
        assert test.shadow_comparison is not None


@pytest.mark.database
@pytest.mark.models
class TestCodeChangeModel:
    """测试 CodeChange 模型"""

    def test_create_code_change(self, db_session: Session):
        """测试创建代码变更"""
        skill_call = SkillCall(skill_name="code_edit", caller="agent_001")
        db_session.add(skill_call)
        db_session.commit()

        change = CodeChange(
            skill_call_id=skill_call.id,
            file_path="/src/main.py",
            change_type="modify",
            content_before="old code",
            content_after="new code",
            diff="@@ -1 +1 @@\n-old code\n+new code"
        )
        db_session.add(change)
        db_session.commit()
        db_session.refresh(change)

        assert change.id is not None
        assert change.file_path == "/src/main.py"
        assert change.change_type == "modify"


@pytest.mark.database
@pytest.mark.models
class TestDecisionLogModel:
    """测试 DecisionLog 模型"""

    def test_create_decision_log(self, db_session: Session):
        """测试创建决策日志"""
        skill_call = SkillCall(skill_name="decision_skill", caller="agent_001")
        db_session.add(skill_call)
        db_session.commit()

        log = DecisionLog(
            skill_call_id=skill_call.id,
            decision_type="architecture",
            decision_basis={"reason": "性能优化"},
            reasoning_process="分析多种方案后选择...",
            final_decision="使用微服务架构"
        )
        db_session.add(log)
        db_session.commit()
        db_session.refresh(log)

        assert log.id is not None
        assert log.decision_type == "architecture"


@pytest.mark.database
@pytest.mark.models
class TestHumanApprovalModel:
    """测试 HumanApproval 模型"""

    def test_create_human_approval(self, db_session: Session):
        """测试创建人工审批"""
        project = Project(name="审批项目")
        db_session.add(project)
        db_session.commit()

        approval = HumanApproval(
            project_id=project.id,
            approval_type="deployment",
            title="部署审批",
            description="需要审批部署请求",
            risk_level="medium",
            status="pending"
        )
        db_session.add(approval)
        db_session.commit()
        db_session.refresh(approval)

        assert approval.id is not None
        assert approval.approval_type == "deployment"
        assert approval.status == "pending"


@pytest.mark.database
@pytest.mark.models
class TestInputOutputTraceModel:
    """测试 InputOutputTrace 模型"""

    def test_create_io_trace(self, db_session: Session):
        """测试创建输入输出追踪"""
        skill_call = SkillCall(skill_name="trace_skill", caller="agent_001")
        db_session.add(skill_call)
        db_session.commit()

        trace = InputOutputTrace(
            skill_call_id=skill_call.id,
            trace_type="input",
            data={"key": "value"},
            data_type="json",
            source="user",
            target="agent"
        )
        db_session.add(trace)
        db_session.commit()
        db_session.refresh(trace)

        assert trace.id is not None
        assert trace.trace_type == "input"


@pytest.mark.database
@pytest.mark.models
class TestIntermediateArtifactModel:
    """测试 IntermediateArtifact 模型"""

    def test_create_artifact(self, db_session: Session):
        """测试创建中间产物"""
        project = Project(name="产物项目")
        db_session.add(project)
        db_session.commit()

        artifact = IntermediateArtifact(
            project_id=project.id,
            artifact_type="document",
            name="设计文档",
            content="文档内容",
            file_path="/docs/design.md"
        )
        db_session.add(artifact)
        db_session.commit()
        db_session.refresh(artifact)

        assert artifact.id is not None
        assert artifact.artifact_type == "document"


@pytest.mark.database
@pytest.mark.models
class TestMilestoneModel:
    """测试 Milestone 模型"""

    def test_create_milestone(self, db_session: Session):
        """测试创建里程碑"""
        project = Project(name="里程碑项目")
        db_session.add(project)
        db_session.commit()

        milestone = Milestone(
            project_id=project.id,
            name="第一阶段",
            description="需求分析完成",
            status=MilestoneStatus.PENDING.value
        )
        db_session.add(milestone)
        db_session.commit()
        db_session.refresh(milestone)

        assert milestone.id is not None
        assert milestone.name == "第一阶段"

    def test_milestone_completion(self, db_session: Session):
        """测试里程碑完成"""
        project = Project(name="完成里程碑项目")
        db_session.add(project)
        db_session.commit()

        milestone = Milestone(
            project_id=project.id,
            name="已完成里程碑",
            status=MilestoneStatus.COMPLETED.value,
            completed_date=datetime.utcnow()
        )
        db_session.add(milestone)
        db_session.commit()
        db_session.refresh(milestone)

        assert milestone.status == MilestoneStatus.COMPLETED.value
        assert milestone.completed_date is not None


@pytest.mark.database
@pytest.mark.models
class TestMutationTestResultModel:
    """测试 MutationTestResult 模型"""

    def test_create_mutation_result(self, db_session: Session):
        """测试创建变异测试结果"""
        project = Project(name="变异测试项目")
        db_session.add(project)
        db_session.commit()

        result = MutationTestResult(
            project_id=project.id,
            test_run_id="run_001",
            total_mutants=100,
            killed_mutants=85,
            survived_mutants=15,
            mutation_score=0.85
        )
        db_session.add(result)
        db_session.commit()
        db_session.refresh(result)

        assert result.id is not None
        assert result.mutation_score == 0.85


@pytest.mark.database
@pytest.mark.models
class TestNonFunctionalCheckModel:
    """测试 NonFunctionalCheck 模型"""

    def test_create_non_functional_check(self, db_session: Session):
        """测试创建非功能检查"""
        project = Project(name="非功能检查项目")
        db_session.add(project)
        db_session.commit()

        check = NonFunctionalCheck(
            project_id=project.id,
            check_type="performance",
            check_name="响应时间检查",
            baseline_value=100.0,
            actual_value=95.0,
            unit="ms",
            status="passed"
        )
        db_session.add(check)
        db_session.commit()
        db_session.refresh(check)

        assert check.id is not None
        assert check.check_type == "performance"


@pytest.mark.database
@pytest.mark.models
class TestPipelineStageModel:
    """测试 PipelineStage 模型"""

    def test_create_pipeline_stage(self, db_session: Session):
        """测试创建流水线阶段"""
        project = Project(name="流水线项目")
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

    def test_pipeline_stage_timing(self, db_session: Session):
        """测试流水线阶段计时"""
        project = Project(name="计时流水线项目")
        db_session.add(project)
        db_session.commit()

        start = datetime.utcnow()
        stage = PipelineStage(
            project_id=project.id,
            stage_name="构建阶段",
            stage_order=2,
            status="completed",
            start_time=start,
            end_time=datetime.utcnow(),
            duration_seconds=120
        )
        db_session.add(stage)
        db_session.commit()
        db_session.refresh(stage)

        assert stage.duration_seconds == 120


@pytest.mark.database
@pytest.mark.models
class TestRequirementTraceModel:
    """测试 RequirementTrace 模型"""

    def test_create_requirement_trace(self, db_session: Session):
        """测试创建需求追溯"""
        project = Project(name="需求追溯项目")
        db_session.add(project)
        db_session.commit()

        trace = RequirementTrace(
            project_id=project.id,
            requirement_id="REQ-001",
            requirement_title="用户登录功能",
            feature_id="FEAT-001",
            feature_title="登录模块",
            trace_type="implements",
            status="verified"
        )
        db_session.add(trace)
        db_session.commit()
        db_session.refresh(trace)

        assert trace.id is not None
        assert trace.requirement_id == "REQ-001"


@pytest.mark.database
@pytest.mark.models
class TestClarificationQuestionModel:
    """测试 ClarificationQuestion 模型"""

    def test_create_clarification_question(self, db_session: Session):
        """测试创建澄清问题"""
        project = Project(name="澄清问题项目")
        db_session.add(project)
        db_session.commit()

        question = ClarificationQuestion(
            project_id=project.id,
            question="是否需要支持多语言？",
            question_type="requirement",
            status="pending"
        )
        db_session.add(question)
        db_session.commit()
        db_session.refresh(question)

        assert question.id is not None
        assert question.question == "是否需要支持多语言？"

    def test_answer_clarification_question(self, db_session: Session):
        """测试回答澄清问题"""
        project = Project(name="回答问题项目")
        db_session.add(project)
        db_session.commit()

        question = ClarificationQuestion(
            project_id=project.id,
            question="数据库类型？",
            answer="使用 PostgreSQL",
            answered_by="用户A",
            answered_at=datetime.utcnow(),
            status="answered"
        )
        db_session.add(question)
        db_session.commit()
        db_session.refresh(question)

        assert question.answer == "使用 PostgreSQL"
        assert question.status == "answered"


@pytest.mark.database
@pytest.mark.models
class TestModelRelationships:
    """测试模型间的复杂关系"""

    def test_project_full_workflow(self, db_session: Session):
        """测试项目完整工作流"""
        department = Department(name="开发部", pinyin="kaifabu")
        db_session.add(department)
        db_session.commit()

        project = Project(name="完整工作流项目")
        db_session.add(project)
        db_session.commit()

        agent = Agent(
            name="工作流代理",
            department_id=department.id
        )
        db_session.add(agent)
        db_session.commit()

        task = Task(
            title="工作流任务",
            project_id=project.id,
            department_id=department.id
        )
        db_session.add(task)
        db_session.commit()

        assignment = Assignment(
            agent_id=agent.id,
            task_id=task.id
        )
        db_session.add(assignment)
        db_session.commit()

        skill_call = SkillCall(
            skill_name="implement",
            caller=agent.name
        )
        db_session.add(skill_call)
        db_session.commit()

        db_session.refresh(project)
        db_session.refresh(agent)
        db_session.refresh(task)

        assert len(agent.assignments) == 1
        assert len(task.assignments) == 1

    def test_skill_call_with_code_changes(self, db_session: Session):
        """测试技能调用与代码变更的关系"""
        skill_call = SkillCall(skill_name="refactor", caller="agent_001")
        db_session.add(skill_call)
        db_session.commit()

        change1 = CodeChange(
            skill_call_id=skill_call.id,
            file_path="/src/a.py",
            change_type="modify"
        )
        change2 = CodeChange(
            skill_call_id=skill_call.id,
            file_path="/src/b.py",
            change_type="create"
        )
        db_session.add_all([change1, change2])
        db_session.commit()

        db_session.refresh(skill_call)
        assert len(skill_call.code_changes) == 2
