"""
数据完整性约束测试

测试数据库的数据完整性约束，包括唯一性、非空、外键等约束
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
@pytest.mark.integrity
class TestNotNullConstraints:
    """测试非空约束"""

    def test_project_name_not_null(self, db_session: Session):
        """测试项目名称不能为空"""
        project = Project(name=None)
        db_session.add(project)

        with pytest.raises(IntegrityError):
            db_session.commit()

    def test_task_title_not_null(self, db_session: Session):
        """测试任务标题不能为空"""
        project = Project(name="任务非空测试")
        db_session.add(project)
        db_session.commit()

        task = Task(title=None, project_id=project.id)
        db_session.add(task)

        with pytest.raises(IntegrityError):
            db_session.commit()

    def test_agent_name_not_null(self, db_session: Session):
        """测试代理名称不能为空"""
        agent = Agent(name=None)
        db_session.add(agent)

        with pytest.raises(IntegrityError):
            db_session.commit()

    def test_department_name_not_null(self, db_session: Session):
        """测试部门名称不能为空"""
        department = Department(name=None, pinyin="test")
        db_session.add(department)

        with pytest.raises(IntegrityError):
            db_session.commit()

    def test_department_pinyin_not_null(self, db_session: Session):
        """测试部门拼音不能为空"""
        department = Department(name="测试部门", pinyin=None)
        db_session.add(department)

        with pytest.raises(IntegrityError):
            db_session.commit()

    def test_skill_call_name_not_null(self, db_session: Session):
        """测试技能调用名称不能为空"""
        call = SkillCall(skill_name=None, caller="agent")
        db_session.add(call)

        with pytest.raises(IntegrityError):
            db_session.commit()

    def test_acceptance_test_scenario_not_null(self, db_session: Session):
        """测试验收测试场景名称不能为空"""
        project = Project(name="验收测试非空")
        db_session.add(project)
        db_session.commit()

        test = AcceptanceTest(project_id=project.id, scenario_name=None)
        db_session.add(test)

        with pytest.raises(IntegrityError):
            db_session.commit()

    def test_code_change_file_path_not_null(self, db_session: Session):
        """测试代码变更文件路径不能为空"""
        skill_call = SkillCall(skill_name="test", caller="agent")
        db_session.add(skill_call)
        db_session.commit()

        change = CodeChange(skill_call_id=skill_call.id, file_path=None, change_type="modify")
        db_session.add(change)

        with pytest.raises(IntegrityError):
            db_session.commit()

    def test_code_change_type_not_null(self, db_session: Session):
        """测试代码变更类型不能为空"""
        skill_call = SkillCall(skill_name="test", caller="agent")
        db_session.add(skill_call)
        db_session.commit()

        change = CodeChange(skill_call_id=skill_call.id, file_path="/test.py", change_type=None)
        db_session.add(change)

        with pytest.raises(IntegrityError):
            db_session.commit()

    def test_human_approval_title_not_null(self, db_session: Session):
        """测试人工审批标题不能为空"""
        project = Project(name="审批非空测试")
        db_session.add(project)
        db_session.commit()

        approval = HumanApproval(
            project_id=project.id,
            approval_type="test",
            title=None
        )
        db_session.add(approval)

        with pytest.raises(IntegrityError):
            db_session.commit()

    def test_milestone_name_not_null(self, db_session: Session):
        """测试里程碑名称不能为空"""
        project = Project(name="里程碑非空测试")
        db_session.add(project)
        db_session.commit()

        milestone = Milestone(project_id=project.id, name=None)
        db_session.add(milestone)

        with pytest.raises(IntegrityError):
            db_session.commit()

    def test_clarification_question_not_null(self, db_session: Session):
        """测试澄清问题不能为空"""
        project = Project(name="问题非空测试")
        db_session.add(project)
        db_session.commit()

        question = ClarificationQuestion(project_id=project.id, question=None)
        db_session.add(question)

        with pytest.raises(IntegrityError):
            db_session.commit()


@pytest.mark.database
@pytest.mark.integrity
class TestUniqueConstraints:
    """测试唯一约束"""

    def test_agent_name_unique(self, db_session: Session):
        """测试代理名称唯一性"""
        agent1 = Agent(name="unique_agent_name")
        db_session.add(agent1)
        db_session.commit()

        agent2 = Agent(name="unique_agent_name")
        db_session.add(agent2)

        with pytest.raises(IntegrityError):
            db_session.commit()

    def test_department_pinyin_unique(self, db_session: Session):
        """测试部门拼音唯一性"""
        dept1 = Department(name="部门1", pinyin="unique_pinyin")
        db_session.add(dept1)
        db_session.commit()

        dept2 = Department(name="部门2", pinyin="unique_pinyin")
        db_session.add(dept2)

        with pytest.raises(IntegrityError):
            db_session.commit()

    def test_multiple_agents_different_names(self, db_session: Session):
        """测试不同名称的代理可以创建"""
        agent1 = Agent(name="agent_one")
        agent2 = Agent(name="agent_two")
        db_session.add_all([agent1, agent2])
        db_session.commit()

        assert agent1.id != agent2.id
        assert agent1.name != agent2.name

    def test_multiple_departments_different_pinyin(self, db_session: Session):
        """测试不同拼音的部门可以创建"""
        dept1 = Department(name="部门1", pinyin="pinyin_one")
        dept2 = Department(name="部门2", pinyin="pinyin_two")
        db_session.add_all([dept1, dept2])
        db_session.commit()

        assert dept1.id != dept2.id


@pytest.mark.database
@pytest.mark.integrity
class TestForeignKeyConstraints:
    """测试外键约束"""

    def test_task_project_fk_valid(self, db_session: Session):
        """测试任务的有效项目外键"""
        project = Project(name="有效项目")
        db_session.add(project)
        db_session.commit()

        task = Task(title="有效任务", project_id=project.id)
        db_session.add(task)
        db_session.commit()

        assert task.project_id == project.id

    def test_task_project_fk_invalid(self, db_session: Session):
        """测试任务的无效项目外键"""
        task = Task(title="无效任务", project_id=99999)
        db_session.add(task)

        with pytest.raises(IntegrityError):
            db_session.commit()

    def test_task_agent_fk_valid(self, db_session: Session):
        """测试任务的有效代理外键"""
        project = Project(name="代理任务项目")
        agent = Agent(name="任务代理")
        db_session.add_all([project, agent])
        db_session.commit()

        task = Task(
            title="代理任务",
            project_id=project.id,
            agent_id=agent.id
        )
        db_session.add(task)
        db_session.commit()

        assert task.agent_id == agent.id

    def test_agent_department_fk_valid(self, db_session: Session):
        """测试代理的有效部门外键"""
        department = Department(name="技术部", pinyin="jishubu")
        db_session.add(department)
        db_session.commit()

        agent = Agent(name="部门代理", department_id=department.id)
        db_session.add(agent)
        db_session.commit()

        assert agent.department_id == department.id

    def test_agent_department_fk_invalid(self, db_session: Session):
        """测试代理的无效部门外键"""
        agent = Agent(name="无效部门代理", department_id=99999)
        db_session.add(agent)

        with pytest.raises(IntegrityError):
            db_session.commit()

    def test_assignment_task_fk_valid(self, db_session: Session):
        """测试分配的有效任务外键"""
        project = Project(name="分配项目")
        db_session.add(project)
        db_session.commit()

        task = Task(title="分配任务", project_id=project.id)
        agent = Agent(name="分配代理")
        db_session.add_all([task, agent])
        db_session.commit()

        assignment = Assignment(task_id=task.id, agent_id=agent.id)
        db_session.add(assignment)
        db_session.commit()

        assert assignment.task_id == task.id

    def test_assignment_agent_fk_valid(self, db_session: Session):
        """测试分配的有效代理外键"""
        project = Project(name="代理分配项目")
        db_session.add(project)
        db_session.commit()

        task = Task(title="代理分配任务", project_id=project.id)
        agent = Agent(name="被分配代理")
        db_session.add_all([task, agent])
        db_session.commit()

        assignment = Assignment(task_id=task.id, agent_id=agent.id)
        db_session.add(assignment)
        db_session.commit()

        assert assignment.agent_id == agent.id

    def test_skill_call_parent_fk_valid(self, db_session: Session):
        """测试技能调用的有效父调用外键"""
        parent = SkillCall(skill_name="parent", caller="agent")
        db_session.add(parent)
        db_session.commit()

        child = SkillCall(
            skill_name="child",
            caller="agent",
            parent_call_id=parent.id
        )
        db_session.add(child)
        db_session.commit()

        assert child.parent_call_id == parent.id

    def test_department_parent_fk_valid(self, db_session: Session):
        """测试部门的有效父部门外键"""
        parent = Department(name="父部门", pinyin="fubumen")
        db_session.add(parent)
        db_session.commit()

        child = Department(
            name="子部门",
            pinyin="zibumen",
            parent_id=parent.id
        )
        db_session.add(child)
        db_session.commit()

        assert child.parent_id == parent.id

    def test_code_change_skill_call_fk_valid(self, db_session: Session):
        """测试代码变更的有效技能调用外键"""
        skill_call = SkillCall(skill_name="edit", caller="agent")
        db_session.add(skill_call)
        db_session.commit()

        change = CodeChange(
            skill_call_id=skill_call.id,
            file_path="/test.py",
            change_type="modify"
        )
        db_session.add(change)
        db_session.commit()

        assert change.skill_call_id == skill_call.id

    def test_code_change_skill_call_fk_invalid(self, db_session: Session):
        """测试代码变更的无效技能调用外键"""
        change = CodeChange(
            skill_call_id=99999,
            file_path="/test.py",
            change_type="modify"
        )
        db_session.add(change)

        with pytest.raises(IntegrityError):
            db_session.commit()

    def test_acceptance_test_project_fk_valid(self, db_session: Session):
        """测试验收测试的有效项目外键"""
        project = Project(name="验收项目")
        db_session.add(project)
        db_session.commit()

        test = AcceptanceTest(
            project_id=project.id,
            scenario_name="测试场景"
        )
        db_session.add(test)
        db_session.commit()

        assert test.project_id == project.id

    def test_acceptance_test_project_fk_invalid(self, db_session: Session):
        """测试验收测试的无效项目外键"""
        test = AcceptanceTest(
            project_id=99999,
            scenario_name="测试场景"
        )
        db_session.add(test)

        with pytest.raises(IntegrityError):
            db_session.commit()

    def test_milestone_project_fk_valid(self, db_session: Session):
        """测试里程碑的有效项目外键"""
        project = Project(name="里程碑项目")
        db_session.add(project)
        db_session.commit()

        milestone = Milestone(
            project_id=project.id,
            name="里程碑1"
        )
        db_session.add(milestone)
        db_session.commit()

        assert milestone.project_id == project.id

    def test_pipeline_stage_project_fk_valid(self, db_session: Session):
        """测试流水线阶段的有效项目外键"""
        project = Project(name="流水线项目")
        db_session.add(project)
        db_session.commit()

        stage = PipelineStage(
            project_id=project.id,
            stage_name="构建"
        )
        db_session.add(stage)
        db_session.commit()

        assert stage.project_id == project.id

    def test_human_approval_project_fk_valid(self, db_session: Session):
        """测试人工审批的有效项目外键"""
        project = Project(name="审批项目")
        db_session.add(project)
        db_session.commit()

        approval = HumanApproval(
            project_id=project.id,
            approval_type="deploy",
            title="部署审批"
        )
        db_session.add(approval)
        db_session.commit()

        assert approval.project_id == project.id


@pytest.mark.database
@pytest.mark.integrity
class TestNullableForeignKeys:
    """测试可空外键约束"""

    def test_task_agent_nullable(self, db_session: Session):
        """测试任务的代理外键可为空"""
        project = Project(name="可空代理项目")
        db_session.add(project)
        db_session.commit()

        task = Task(
            title="无代理任务",
            project_id=project.id,
            agent_id=None
        )
        db_session.add(task)
        db_session.commit()

        assert task.agent_id is None

    def test_task_department_nullable(self, db_session: Session):
        """测试任务的部门外键可为空"""
        project = Project(name="可空部门项目")
        db_session.add(project)
        db_session.commit()

        task = Task(
            title="无部门任务",
            project_id=project.id,
            department_id=None
        )
        db_session.add(task)
        db_session.commit()

        assert task.department_id is None

    def test_agent_department_nullable(self, db_session: Session):
        """测试代理的部门外键可为空"""
        agent = Agent(name="无部门代理", department_id=None)
        db_session.add(agent)
        db_session.commit()

        assert agent.department_id is None

    def test_skill_call_parent_nullable(self, db_session: Session):
        """测试技能调用的父调用外键可为空"""
        call = SkillCall(
            skill_name="root",
            caller="agent",
            parent_call_id=None
        )
        db_session.add(call)
        db_session.commit()

        assert call.parent_call_id is None

    def test_department_parent_nullable(self, db_session: Session):
        """测试部门的父部门外键可为空"""
        department = Department(
            name="根部门",
            pinyin="genbumen",
            parent_id=None
        )
        db_session.add(department)
        db_session.commit()

        assert department.parent_id is None

    def test_assignment_skill_call_nullable(self, db_session: Session):
        """测试分配的技能调用外键可为空"""
        project = Project(name="可空技能调用项目")
        db_session.add(project)
        db_session.commit()

        task = Task(title="任务", project_id=project.id)
        agent = Agent(name="代理")
        db_session.add_all([task, agent])
        db_session.commit()

        assignment = Assignment(
            task_id=task.id,
            agent_id=agent.id,
            skill_call_id=None
        )
        db_session.add(assignment)
        db_session.commit()

        assert assignment.skill_call_id is None


@pytest.mark.database
@pytest.mark.integrity
class TestDataValidation:
    """测试数据验证"""

    def test_project_status_valid(self, db_session: Session):
        """测试项目状态有效值"""
        valid_statuses = [
            ProjectStatus.REQUIREMENT.value,
            ProjectStatus.DESIGN.value,
            ProjectStatus.DEVELOPMENT.value,
            ProjectStatus.TESTING.value,
            ProjectStatus.DEPLOYMENT.value,
            ProjectStatus.COMPLETED.value
        ]

        for status in valid_statuses:
            project = Project(name=f"状态测试_{status}", status=status)
            db_session.add(project)
            db_session.commit()
            db_session.refresh(project)
            assert project.status == status
            db_session.rollback()

    def test_task_status_valid(self, db_session: Session):
        """测试任务状态有效值"""
        project = Project(name="任务状态测试")
        db_session.add(project)
        db_session.commit()

        valid_statuses = [
            TaskStatus.PENDING.value,
            TaskStatus.IN_PROGRESS.value,
            TaskStatus.REVIEW.value,
            TaskStatus.COMPLETED.value
        ]

        for status in valid_statuses:
            task = Task(
                title=f"任务_{status}",
                project_id=project.id,
                status=status
            )
            db_session.add(task)
            db_session.commit()
            db_session.refresh(task)
            assert task.status == status
            db_session.rollback()

    def test_task_priority_valid(self, db_session: Session):
        """测试任务优先级有效值"""
        project = Project(name="优先级测试")
        db_session.add(project)
        db_session.commit()

        valid_priorities = [
            TaskPriority.HIGH.value,
            TaskPriority.MEDIUM.value,
            TaskPriority.LOW.value
        ]

        for priority in valid_priorities:
            task = Task(
                title=f"任务_{priority}",
                project_id=project.id,
                priority=priority
            )
            db_session.add(task)
            db_session.commit()
            db_session.refresh(task)
            assert task.priority == priority
            db_session.rollback()

    def test_milestone_status_valid(self, db_session: Session):
        """测试里程碑状态有效值"""
        project = Project(name="里程碑状态测试")
        db_session.add(project)
        db_session.commit()

        valid_statuses = [
            MilestoneStatus.PENDING.value,
            MilestoneStatus.IN_PROGRESS.value,
            MilestoneStatus.COMPLETED.value
        ]

        for status in valid_statuses:
            milestone = Milestone(
                project_id=project.id,
                name=f"里程碑_{status}",
                status=status
            )
            db_session.add(milestone)
            db_session.commit()
            db_session.refresh(milestone)
            assert milestone.status == status
            db_session.rollback()


@pytest.mark.database
@pytest.mark.integrity
class TestJSONFieldIntegrity:
    """测试 JSON 字段完整性"""

    def test_project_tech_stack_json(self, db_session: Session):
        """测试项目技术栈 JSON 存储"""
        tech_stack = ["Python", "FastAPI", "PostgreSQL", "Redis"]
        project = Project(
            name="技术栈测试",
            tech_stack=tech_stack
        )
        db_session.add(project)
        db_session.commit()
        db_session.refresh(project)

        assert project.tech_stack == tech_stack
        assert isinstance(project.tech_stack, list)

    def test_project_status_history_json(self, db_session: Session):
        """测试项目状态历史 JSON 存储"""
        status_history = [
            {
                "status": "DESIGN",
                "timestamp": datetime.utcnow().isoformat(),
                "comment": "开始设计"
            },
            {
                "status": "DEVELOPMENT",
                "timestamp": datetime.utcnow().isoformat(),
                "comment": "开始开发"
            }
        ]
        project = Project(
            name="状态历史测试",
            status_history=status_history
        )
        db_session.add(project)
        db_session.commit()
        db_session.refresh(project)

        assert project.status_history == status_history

    def test_task_dependencies_json(self, db_session: Session):
        """测试任务依赖 JSON 存储"""
        project = Project(name="依赖测试项目")
        db_session.add(project)
        db_session.commit()

        task = Task(
            title="依赖任务",
            project_id=project.id,
            dependencies=[1, 2, 3]
        )
        db_session.add(task)
        db_session.commit()
        db_session.refresh(task)

        assert task.dependencies == [1, 2, 3]

    def test_agent_skills_json(self, db_session: Session):
        """测试代理技能 JSON 存储"""
        skills = ["Python", "JavaScript", "SQL", "Docker"]
        agent = Agent(name="技能代理", skills=skills)
        db_session.add(agent)
        db_session.commit()
        db_session.refresh(agent)

        assert agent.skills == skills

    def test_skill_call_details_json(self, db_session: Session):
        """测试技能调用详情 JSON 存储"""
        details = {
            "language": "python",
            "framework": "fastapi",
            "version": "3.11"
        }
        call = SkillCall(
            skill_name="generate",
            caller="agent",
            details=details
        )
        db_session.add(call)
        db_session.commit()
        db_session.refresh(call)

        assert call.details == details

    def test_empty_json_fields(self, db_session: Session):
        """测试空 JSON 字段"""
        project = Project(
            name="空JSON测试",
            tech_stack=[],
            status_history=[],
            milestones=[]
        )
        db_session.add(project)
        db_session.commit()
        db_session.refresh(project)

        assert project.tech_stack == []
        assert project.status_history == []
        assert project.milestones == []


@pytest.mark.database
@pytest.mark.integrity
class TestNumericConstraints:
    """测试数值约束"""

    def test_agent_load_values(self, db_session: Session):
        """测试代理负载值"""
        agent = Agent(
            name="负载代理",
            current_load=3,
            max_load=10
        )
        db_session.add(agent)
        db_session.commit()
        db_session.refresh(agent)

        assert agent.current_load == 3
        assert agent.max_load == 10

    def test_task_hours_values(self, db_session: Session):
        """测试任务工时值"""
        project = Project(name="工时测试")
        db_session.add(project)
        db_session.commit()

        task = Task(
            title="工时任务",
            project_id=project.id,
            estimated_hours=8.5,
            actual_hours=7.25
        )
        db_session.add(task)
        db_session.commit()
        db_session.refresh(task)

        assert task.estimated_hours == 8.5
        assert task.actual_hours == 7.25

    def test_mutation_test_scores(self, db_session: Session):
        """测试变异测试分数"""
        project = Project(name="变异测试")
        db_session.add(project)
        db_session.commit()

        result = MutationTestResult(
            project_id=project.id,
            total_mutants=100,
            killed_mutants=85,
            survived_mutants=15,
            mutation_score=0.85
        )
        db_session.add(result)
        db_session.commit()
        db_session.refresh(result)

        assert result.mutation_score == 0.85
        assert result.total_mutants == result.killed_mutants + result.survived_mutants

    def test_non_functional_check_values(self, db_session: Session):
        """测试非功能检查值"""
        project = Project(name="非功能测试")
        db_session.add(project)
        db_session.commit()

        check = NonFunctionalCheck(
            project_id=project.id,
            check_type="performance",
            check_name="响应时间",
            baseline_value=100.0,
            actual_value=95.5,
            unit="ms"
        )
        db_session.add(check)
        db_session.commit()
        db_session.refresh(check)

        assert check.baseline_value == 100.0
        assert check.actual_value == 95.5


@pytest.mark.database
@pytest.mark.integrity
class TestDateTimeConstraints:
    """测试日期时间约束"""

    def test_project_created_at_auto(self, db_session: Session):
        """测试项目创建时间自动设置"""
        before = datetime.utcnow()
        project = Project(name="时间测试")
        db_session.add(project)
        db_session.commit()
        db_session.refresh(project)
        after = datetime.utcnow()

        assert project.created_at is not None
        assert before <= project.created_at.replace(tzinfo=None) <= after

    def test_task_completed_at_nullable(self, db_session: Session):
        """测试任务完成时间可为空"""
        project = Project(name="完成时间测试")
        db_session.add(project)
        db_session.commit()

        task = Task(
            title="未完成任务",
            project_id=project.id,
            completed_at=None
        )
        db_session.add(task)
        db_session.commit()
        db_session.refresh(task)

        assert task.completed_at is None

    def test_task_completed_at_set(self, db_session: Session):
        """测试任务完成时间设置"""
        project = Project(name="完成时间设置测试")
        db_session.add(project)
        db_session.commit()

        completed_time = datetime.utcnow()
        task = Task(
            title="已完成任务",
            project_id=project.id,
            completed_at=completed_time
        )
        db_session.add(task)
        db_session.commit()
        db_session.refresh(task)

        assert task.completed_at is not None

    def test_milestone_dates(self, db_session: Session):
        """测试里程碑日期"""
        project = Project(name="里程碑日期测试")
        db_session.add(project)
        db_session.commit()

        planned = datetime.utcnow()
        milestone = Milestone(
            project_id=project.id,
            name="里程碑",
            planned_date=planned,
            completed_date=None
        )
        db_session.add(milestone)
        db_session.commit()
        db_session.refresh(milestone)

        assert milestone.planned_date is not None
        assert milestone.completed_date is None

    def test_pipeline_stage_timing(self, db_session: Session):
        """测试流水线阶段时间"""
        project = Project(name="流水线时间测试")
        db_session.add(project)
        db_session.commit()

        start = datetime.utcnow()
        stage = PipelineStage(
            project_id=project.id,
            stage_name="构建",
            start_time=start,
            duration_seconds=120
        )
        db_session.add(stage)
        db_session.commit()
        db_session.refresh(stage)

        assert stage.start_time is not None
        assert stage.duration_seconds == 120


@pytest.mark.database
@pytest.mark.integrity
class TestCascadeBehavior:
    """测试级联行为"""

    def test_delete_project_with_tasks(self, db_session: Session):
        """测试删除项目时任务的处理"""
        project = Project(name="级联删除项目")
        db_session.add(project)
        db_session.commit()

        task = Task(title="级联任务", project_id=project.id)
        db_session.add(task)
        db_session.commit()

        task_id = task.id
        project_id = project.id

        db_session.delete(project)
        db_session.commit()

        deleted_project = db_session.query(Project).filter_by(id=project_id).first()
        assert deleted_project is None

    def test_delete_agent_with_assignments(self, db_session: Session):
        """测试删除代理时分配的处理"""
        project = Project(name="代理级联项目")
        db_session.add(project)
        db_session.commit()

        task = Task(title="代理级联任务", project_id=project.id)
        agent = Agent(name="级联代理")
        db_session.add_all([task, agent])
        db_session.commit()

        assignment = Assignment(task_id=task.id, agent_id=agent.id)
        db_session.add(assignment)
        db_session.commit()

        assignment_id = assignment.id

        db_session.delete(agent)
        db_session.commit()

    def test_delete_skill_call_with_children(self, db_session: Session):
        """测试删除父技能调用时子调用的处理"""
        parent = SkillCall(skill_name="parent", caller="agent")
        db_session.add(parent)
        db_session.commit()

        child = SkillCall(
            skill_name="child",
            caller="agent",
            parent_call_id=parent.id
        )
        db_session.add(child)
        db_session.commit()

        child_id = child.id
        parent_id = parent.id

        db_session.delete(parent)
        db_session.commit()
