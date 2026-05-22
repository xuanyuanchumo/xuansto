"""
数据库模型操作测试

测试所有数据库模型的CRUD操作、状态转换、边界条件等
"""

import pytest
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from sqlalchemy import func

from app.models.project import Project, ProjectStatus, PROJECT_STATUS_TRANSITIONS
from app.models.task import Task, TaskStatus, TaskPriority, TASK_STATUS_TRANSITIONS
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
class TestProjectOperations:
    """测试 Project 模型操作"""

    def test_create_project_with_all_fields(self, db_session: Session):
        """测试创建包含所有字段的项目"""
        project = Project(
            name="完整项目",
            description="完整描述",
            tech_stack=["Python", "FastAPI", "PostgreSQL"],
            status=ProjectStatus.DESIGN.value,
            status_history=[{"status": "REQUIREMENT", "timestamp": datetime.utcnow().isoformat()}],
            milestones=[{"name": "M1", "completed": False}]
        )
        db_session.add(project)
        db_session.commit()
        db_session.refresh(project)

        assert project.id is not None
        assert project.name == "完整项目"
        assert project.description == "完整描述"
        assert len(project.tech_stack) == 3
        assert project.status == ProjectStatus.DESIGN.value

    def test_project_status_transitions_valid(self, db_session: Session):
        """测试项目状态转换有效性"""
        valid_transitions = PROJECT_STATUS_TRANSITIONS[ProjectStatus.REQUIREMENT]
        assert ProjectStatus.DESIGN in valid_transitions

        valid_transitions = PROJECT_STATUS_TRANSITIONS[ProjectStatus.TESTING]
        assert ProjectStatus.DEVELOPMENT in valid_transitions
        assert ProjectStatus.DEPLOYMENT in valid_transitions

    def test_project_filter_by_status(self, db_session: Session):
        """测试按状态过滤项目"""
        for i in range(5):
            project = Project(
                name=f"状态项目{i}",
                status=ProjectStatus.DEVELOPMENT.value if i < 3 else ProjectStatus.COMPLETED.value
            )
            db_session.add(project)
        db_session.commit()

        dev_projects = db_session.query(Project).filter(
            Project.status == ProjectStatus.DEVELOPMENT.value
        ).all()

        assert len(dev_projects) == 3

    def test_project_search_by_name(self, db_session: Session):
        """测试按名称搜索项目"""
        project1 = Project(name="前端开发项目")
        project2 = Project(name="后端开发项目")
        project3 = Project(name="测试项目")
        db_session.add_all([project1, project2, project3])
        db_session.commit()

        results = db_session.query(Project).filter(
            Project.name.like("%开发%")
        ).all()

        assert len(results) == 2

    def test_project_order_by_created_at(self, db_session: Session):
        """测试按创建时间排序项目"""
        project1 = Project(name="项目1")
        db_session.add(project1)
        db_session.commit()

        project2 = Project(name="项目2")
        db_session.add(project2)
        db_session.commit()

        projects = db_session.query(Project).order_by(Project.created_at.desc()).all()
        assert projects[0].name == "项目2"

    def test_project_update_tech_stack(self, db_session: Session):
        """测试更新项目技术栈"""
        project = Project(name="技术栈项目", tech_stack=["Python"])
        db_session.add(project)
        db_session.commit()

        project.tech_stack = ["Python", "TypeScript", "React"]
        db_session.commit()
        db_session.refresh(project)

        assert len(project.tech_stack) == 3

    def test_project_bulk_create(self, db_session: Session):
        """测试批量创建项目"""
        projects = [Project(name=f"批量项目{i}") for i in range(10)]
        db_session.add_all(projects)
        db_session.commit()

        count = db_session.query(Project).count()
        assert count >= 10


@pytest.mark.database
@pytest.mark.models
class TestTaskOperations:
    """测试 Task 模型操作"""

    def test_create_task_with_dependencies(self, db_session: Session):
        """测试创建带依赖的任务"""
        project = Project(name="依赖项目")
        db_session.add(project)
        db_session.commit()

        task1 = Task(title="任务1", project_id=project.id)
        db_session.add(task1)
        db_session.commit()

        task2 = Task(
            title="任务2",
            project_id=project.id,
            dependencies=[task1.id]
        )
        db_session.add(task2)
        db_session.commit()
        db_session.refresh(task2)

        assert task2.dependencies == [task1.id]

    def test_task_status_transitions_valid(self, db_session: Session):
        """测试任务状态转换有效性"""
        valid_transitions = TASK_STATUS_TRANSITIONS[TaskStatus.PENDING]
        assert TaskStatus.IN_PROGRESS in valid_transitions

        valid_transitions = TASK_STATUS_TRANSITIONS[TaskStatus.REVIEW]
        assert TaskStatus.IN_PROGRESS in valid_transitions
        assert TaskStatus.COMPLETED in valid_transitions

    def test_task_priority_filtering(self, db_session: Session):
        """测试任务优先级过滤"""
        project = Project(name="优先级项目")
        db_session.add(project)
        db_session.commit()

        for i, priority in enumerate([TaskPriority.HIGH.value, TaskPriority.MEDIUM.value, TaskPriority.LOW.value]):
            for j in range(3):
                task = Task(
                    title=f"任务_{priority}_{j}",
                    project_id=project.id,
                    priority=priority
                )
                db_session.add(task)
        db_session.commit()

        high_tasks = db_session.query(Task).filter(
            Task.project_id == project.id,
            Task.priority == TaskPriority.HIGH.value
        ).all()

        assert len(high_tasks) == 3

    def test_task_hours_tracking(self, db_session: Session):
        """测试任务工时跟踪"""
        project = Project(name="工时项目")
        db_session.add(project)
        db_session.commit()

        task = Task(
            title="工时任务",
            project_id=project.id,
            estimated_hours=10.0
        )
        db_session.add(task)
        db_session.commit()

        task.actual_hours = 8.5
        task.status = TaskStatus.COMPLETED.value
        task.completed_at = datetime.utcnow()
        db_session.commit()
        db_session.refresh(task)

        assert task.actual_hours == 8.5
        assert task.completed_at is not None

    def test_task_assign_to_agent(self, db_session: Session):
        """测试任务分配给代理"""
        project = Project(name="分配项目")
        agent = Agent(name="分配代理")
        db_session.add_all([project, agent])
        db_session.commit()

        task = Task(
            title="待分配任务",
            project_id=project.id,
            agent_id=agent.id
        )
        db_session.add(task)
        db_session.commit()
        db_session.refresh(task)

        assert task.agent_id == agent.id

    def test_task_complex_query(self, db_session: Session):
        """测试复杂任务查询"""
        project = Project(name="复杂查询项目")
        agent = Agent(name="查询代理")
        db_session.add_all([project, agent])
        db_session.commit()

        for i in range(10):
            task = Task(
                title=f"查询任务{i}",
                project_id=project.id,
                agent_id=agent.id if i < 5 else None,
                status=TaskStatus.COMPLETED.value if i < 7 else TaskStatus.PENDING.value
            )
            db_session.add(task)
        db_session.commit()

        completed_with_agent = db_session.query(Task).filter(
            Task.project_id == project.id,
            Task.status == TaskStatus.COMPLETED.value,
            Task.agent_id.isnot(None)
        ).count()

        assert completed_with_agent == 5


@pytest.mark.database
@pytest.mark.models
class TestAgentOperations:
    """测试 Agent 模型操作"""

    def test_agent_skill_management(self, db_session: Session):
        """测试代理技能管理"""
        agent = Agent(
            name="技能代理",
            skills=["Python", "JavaScript", "SQL"]
        )
        db_session.add(agent)
        db_session.commit()
        db_session.refresh(agent)

        assert len(agent.skills) == 3
        assert "Python" in agent.skills

    def test_agent_load_tracking(self, db_session: Session):
        """测试代理负载跟踪"""
        agent = Agent(
            name="负载代理",
            current_load=2,
            max_load=5
        )
        db_session.add(agent)
        db_session.commit()

        agent.current_load += 1
        db_session.commit()
        db_session.refresh(agent)

        assert agent.current_load == 3

    def test_agent_status_change(self, db_session: Session):
        """测试代理状态变更"""
        agent = Agent(name="状态代理", status="idle")
        db_session.add(agent)
        db_session.commit()

        agent.status = "busy"
        agent.current_task = "处理任务A"
        db_session.commit()
        db_session.refresh(agent)

        assert agent.status == "busy"
        assert agent.current_task == "处理任务A"

    def test_agent_department_assignment(self, db_session: Session):
        """测试代理部门分配"""
        department = Department(name="技术部", pinyin="jishubu")
        db_session.add(department)
        db_session.commit()

        agent = Agent(
            name="部门代理",
            department_id=department.id
        )
        db_session.add(agent)
        db_session.commit()
        db_session.refresh(agent)

        assert agent.department_id == department.id

    def test_agent_find_by_skill(self, db_session: Session):
        """测试按技能查找代理"""
        agent1 = Agent(name="Python代理", skills=["Python", "Django"])
        agent2 = Agent(name="JS代理", skills=["JavaScript", "React"])
        agent3 = Agent(name="全栈代理", skills=["Python", "JavaScript"])
        db_session.add_all([agent1, agent2, agent3])
        db_session.commit()

        python_agents = db_session.query(Agent).filter(
            Agent.skills.contains(["Python"])
        ).all()

        assert len(python_agents) == 2


@pytest.mark.database
@pytest.mark.models
class TestDepartmentOperations:
    """测试 Department 模型操作"""

    def test_department_hierarchy_create(self, db_session: Session):
        """测试创建部门层级"""
        root = Department(name="总公司", pinyin="zonggongsi", level="L0")
        db_session.add(root)
        db_session.commit()

        dept1 = Department(
            name="研发部",
            pinyin="yanfabu",
            level="L1",
            parent_id=root.id
        )
        dept2 = Department(
            name="产品部",
            pinyin="chanpinbu",
            level="L1",
            parent_id=root.id
        )
        db_session.add_all([dept1, dept2])
        db_session.commit()

        db_session.refresh(root)
        assert len(root.children) == 2

    def test_department_find_root(self, db_session: Session):
        """测试查找根部门"""
        root = Department(name="根部门", pinyin="genbumen", parent_id=None)
        child = Department(name="子部门", pinyin="zibumen", parent_id=1)
        db_session.add_all([root, child])
        db_session.commit()

        roots = db_session.query(Department).filter(
            Department.parent_id.is_(None)
        ).all()

        assert len(roots) == 1

    def test_department_level_query(self, db_session: Session):
        """测试按层级查询部门"""
        dept1 = Department(name="L1部门A", pinyin="l1a", level="L1")
        dept2 = Department(name="L1部门B", pinyin="l1b", level="L1")
        dept3 = Department(name="L2部门", pinyin="l2", level="L2")
        db_session.add_all([dept1, dept2, dept3])
        db_session.commit()

        l1_depts = db_session.query(Department).filter(
            Department.level == "L1"
        ).all()

        assert len(l1_depts) == 2


@pytest.mark.database
@pytest.mark.models
class TestSkillCallOperations:
    """测试 SkillCall 模型操作"""

    def test_skill_call_lifecycle(self, db_session: Session):
        """测试技能调用生命周期"""
        call = SkillCall(
            skill_name="code_generation",
            caller="agent_001",
            status="started",
            input_data={"prompt": "生成用户登录功能"}
        )
        db_session.add(call)
        db_session.commit()

        call.status = "completed"
        call.output_data = {"code": "def login(): pass"}
        call.end_time = datetime.utcnow()
        db_session.commit()
        db_session.refresh(call)

        assert call.status == "completed"
        assert call.output_data is not None

    def test_skill_call_tree_structure(self, db_session: Session):
        """测试技能调用树结构"""
        parent = SkillCall(skill_name="parent_skill", caller="agent_001")
        db_session.add(parent)
        db_session.commit()

        child1 = SkillCall(
            skill_name="child_skill_1",
            caller="agent_001",
            parent_call_id=parent.id
        )
        child2 = SkillCall(
            skill_name="child_skill_2",
            caller="agent_001",
            parent_call_id=parent.id
        )
        db_session.add_all([child1, child2])
        db_session.commit()

        db_session.refresh(parent)
        assert len(parent.children) == 2

    def test_skill_call_reasoning_log(self, db_session: Session):
        """测试技能调用推理日志"""
        call = SkillCall(
            skill_name="decision_skill",
            caller="agent_001",
            reasoning_log="分析问题...\n考虑方案A...\n选择方案B...",
            decision_type="architecture",
            decision_basis={"reason": "性能优先"}
        )
        db_session.add(call)
        db_session.commit()
        db_session.refresh(call)

        assert call.reasoning_log is not None
        assert call.decision_type == "architecture"

    def test_skill_call_filter_by_status(self, db_session: Session):
        """测试按状态过滤技能调用"""
        for i in range(5):
            call = SkillCall(
                skill_name=f"skill_{i}",
                caller="agent_001",
                status="completed" if i < 3 else "failed"
            )
            db_session.add(call)
        db_session.commit()

        completed = db_session.query(SkillCall).filter(
            SkillCall.status == "completed"
        ).count()

        assert completed == 3


@pytest.mark.database
@pytest.mark.models
class TestAssignmentOperations:
    """测试 Assignment 模型操作"""

    def test_assignment_create_and_complete(self, db_session: Session):
        """测试分配创建和完成"""
        project = Project(name="分配测试项目")
        agent = Agent(name="分配测试代理")
        db_session.add_all([project, agent])
        db_session.commit()

        task = Task(title="分配测试任务", project_id=project.id)
        db_session.add(task)
        db_session.commit()

        assignment = Assignment(
            agent_id=agent.id,
            task_id=task.id,
            status="assigned",
            task_description="完成功能开发"
        )
        db_session.add(assignment)
        db_session.commit()

        assignment.status = "completed"
        assignment.completed_time = datetime.utcnow()
        db_session.commit()
        db_session.refresh(assignment)

        assert assignment.status == "completed"
        assert assignment.completed_time is not None

    def test_assignment_with_skill_call(self, db_session: Session):
        """测试带技能调用的分配"""
        project = Project(name="技能分配项目")
        agent = Agent(name="技能分配代理")
        db_session.add_all([project, agent])
        db_session.commit()

        task = Task(title="技能分配任务", project_id=project.id)
        db_session.add(task)
        db_session.commit()

        skill_call = SkillCall(skill_name="implement", caller=agent.name)
        db_session.add(skill_call)
        db_session.commit()

        assignment = Assignment(
            agent_id=agent.id,
            task_id=task.id,
            skill_call_id=skill_call.id
        )
        db_session.add(assignment)
        db_session.commit()
        db_session.refresh(assignment)

        assert assignment.skill_call_id == skill_call.id


@pytest.mark.database
@pytest.mark.models
class TestMilestoneOperations:
    """测试 Milestone 模型操作"""

    def test_milestone_progress_tracking(self, db_session: Session):
        """测试里程碑进度跟踪"""
        project = Project(name="里程碑项目")
        db_session.add(project)
        db_session.commit()

        milestones = []
        for i, status in enumerate([MilestoneStatus.PENDING.value, MilestoneStatus.IN_PROGRESS.value, MilestoneStatus.COMPLETED.value]):
            milestone = Milestone(
                project_id=project.id,
                name=f"里程碑{i+1}",
                status=status,
                planned_date=datetime.utcnow() + timedelta(days=i*7)
            )
            milestones.append(milestone)
            db_session.add(milestone)
        db_session.commit()

        completed_count = db_session.query(Milestone).filter(
            Milestone.project_id == project.id,
            Milestone.status == MilestoneStatus.COMPLETED.value
        ).count()

        assert completed_count == 1

    def test_milestone_completion_date(self, db_session: Session):
        """测试里程碑完成日期"""
        project = Project(name="完成日期项目")
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

        assert milestone.completed_date is not None


@pytest.mark.database
@pytest.mark.models
class TestAcceptanceTestOperations:
    """测试 AcceptanceTest 模型操作"""

    def test_acceptance_test_bdd_format(self, db_session: Session):
        """测试BDD格式验收测试"""
        project = Project(name="BDD项目")
        db_session.add(project)
        db_session.commit()

        test = AcceptanceTest(
            project_id=project.id,
            scenario_name="用户登录成功",
            given="用户在登录页面",
            when="输入正确的用户名和密码并点击登录",
            then="成功登录并跳转到首页"
        )
        db_session.add(test)
        db_session.commit()
        db_session.refresh(test)

        assert test.given == "用户在登录页面"
        assert test.when is not None
        assert test.then is not None

    def test_acceptance_test_execution(self, db_session: Session):
        """测试验收测试执行"""
        project = Project(name="执行测试项目")
        db_session.add(project)
        db_session.commit()

        test = AcceptanceTest(
            project_id=project.id,
            scenario_name="执行测试",
            execution_result="passed",
            execution_log="测试通过",
            executed_at=datetime.utcnow()
        )
        db_session.add(test)
        db_session.commit()
        db_session.refresh(test)

        assert test.execution_result == "passed"

    def test_shadow_test_comparison(self, db_session: Session):
        """测试影子测试比较"""
        project = Project(name="影子测试项目")
        db_session.add(project)
        db_session.commit()

        test = AcceptanceTest(
            project_id=project.id,
            scenario_name="影子测试",
            is_shadow_test=True,
            shadow_comparison={
                "original_result": "pass",
                "new_result": "pass",
                "diff": None
            }
        )
        db_session.add(test)
        db_session.commit()
        db_session.refresh(test)

        assert test.is_shadow_test is True


@pytest.mark.database
@pytest.mark.models
class TestCodeChangeOperations:
    """测试 CodeChange 模型操作"""

    def test_code_change_create(self, db_session: Session):
        """测试创建代码变更"""
        skill_call = SkillCall(skill_name="edit", caller="agent_001")
        db_session.add(skill_call)
        db_session.commit()

        change = CodeChange(
            skill_call_id=skill_call.id,
            file_path="/src/main.py",
            change_type="modify",
            content_before="def old(): pass",
            content_after="def new(): return True",
            diff="@@ -1 +1 @@\n-def old(): pass\n+def new(): return True"
        )
        db_session.add(change)
        db_session.commit()
        db_session.refresh(change)

        assert change.change_type == "modify"
        assert change.diff is not None

    def test_code_change_types(self, db_session: Session):
        """测试不同代码变更类型"""
        skill_call = SkillCall(skill_name="multi_edit", caller="agent_001")
        db_session.add(skill_call)
        db_session.commit()

        changes = [
            CodeChange(skill_call_id=skill_call.id, file_path="/new.py", change_type="create"),
            CodeChange(skill_call_id=skill_call.id, file_path="/old.py", change_type="delete"),
            CodeChange(skill_call_id=skill_call.id, file_path="/mod.py", change_type="modify"),
        ]
        db_session.add_all(changes)
        db_session.commit()

        create_count = db_session.query(CodeChange).filter(
            CodeChange.skill_call_id == skill_call.id,
            CodeChange.change_type == "create"
        ).count()

        assert create_count == 1


@pytest.mark.database
@pytest.mark.models
class TestDecisionLogOperations:
    """测试 DecisionLog 模型操作"""

    def test_decision_log_create(self, db_session: Session):
        """测试创建决策日志"""
        skill_call = SkillCall(skill_name="decide", caller="agent_001")
        db_session.add(skill_call)
        db_session.commit()

        log = DecisionLog(
            skill_call_id=skill_call.id,
            decision_type="architecture",
            decision_basis={"requirement": "高性能", "constraint": "预算限制"},
            reasoning_process="分析了三种方案...",
            alternatives=[
                {"name": "方案A", "pros": ["简单"], "cons": ["性能差"]},
                {"name": "方案B", "pros": ["高性能"], "cons": ["复杂"]}
            ],
            final_decision="选择方案B"
        )
        db_session.add(log)
        db_session.commit()
        db_session.refresh(log)

        assert log.decision_type == "architecture"
        assert len(log.alternatives) == 2


@pytest.mark.database
@pytest.mark.models
class TestHumanApprovalOperations:
    """测试 HumanApproval 模型操作"""

    def test_human_approval_workflow(self, db_session: Session):
        """测试人工审批工作流"""
        project = Project(name="审批项目")
        db_session.add(project)
        db_session.commit()

        approval = HumanApproval(
            project_id=project.id,
            approval_type="deployment",
            title="生产环境部署审批",
            description="需要部署新版本到生产环境",
            risk_level="high",
            status="pending"
        )
        db_session.add(approval)
        db_session.commit()

        approval.status = "approved"
        approval.approved_by = "admin"
        approval.approved_at = datetime.utcnow()
        db_session.commit()
        db_session.refresh(approval)

        assert approval.status == "approved"
        assert approval.approved_by == "admin"

    def test_human_approval_rejection(self, db_session: Session):
        """测试人工审批拒绝"""
        project = Project(name="拒绝审批项目")
        db_session.add(project)
        db_session.commit()

        approval = HumanApproval(
            project_id=project.id,
            approval_type="code_merge",
            title="代码合并审批",
            status="rejected",
            rejection_reason="代码质量不达标",
            modification_suggestions="请增加单元测试覆盖率"
        )
        db_session.add(approval)
        db_session.commit()
        db_session.refresh(approval)

        assert approval.status == "rejected"
        assert approval.rejection_reason is not None


@pytest.mark.database
@pytest.mark.models
class TestInputOutputTraceOperations:
    """测试 InputOutputTrace 模型操作"""

    def test_io_trace_create(self, db_session: Session):
        """测试创建输入输出追踪"""
        skill_call = SkillCall(skill_name="process", caller="agent_001")
        db_session.add(skill_call)
        db_session.commit()

        input_trace = InputOutputTrace(
            skill_call_id=skill_call.id,
            trace_type="input",
            data={"request": "生成用户API"},
            data_type="json",
            source="user",
            target="agent"
        )
        output_trace = InputOutputTrace(
            skill_call_id=skill_call.id,
            trace_type="output",
            data={"response": "API已生成"},
            data_type="json",
            source="agent",
            target="user"
        )
        db_session.add_all([input_trace, output_trace])
        db_session.commit()

        traces = db_session.query(InputOutputTrace).filter(
            InputOutputTrace.skill_call_id == skill_call.id
        ).all()

        assert len(traces) == 2


@pytest.mark.database
@pytest.mark.models
class TestIntermediateArtifactOperations:
    """测试 IntermediateArtifact 模型操作"""

    def test_artifact_create(self, db_session: Session):
        """测试创建中间产物"""
        project = Project(name="产物项目")
        db_session.add(project)
        db_session.commit()

        artifact = IntermediateArtifact(
            project_id=project.id,
            artifact_type="document",
            name="系统设计文档",
            content="# 系统设计\n\n## 架构\n...",
            file_path="/docs/design.md",
            artifact_metadata={"version": "1.0", "author": "agent"}
        )
        db_session.add(artifact)
        db_session.commit()
        db_session.refresh(artifact)

        assert artifact.artifact_type == "document"
        assert artifact.artifact_metadata["version"] == "1.0"


@pytest.mark.database
@pytest.mark.models
class TestMutationTestResultOperations:
    """测试 MutationTestResult 模型操作"""

    def test_mutation_result_create(self, db_session: Session):
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
            mutation_score=0.85,
            mutant_details={
                "survived": ["mutant_1", "mutant_2"],
                "killed": ["mutant_3", "mutant_4"]
            },
            status="completed"
        )
        db_session.add(result)
        db_session.commit()
        db_session.refresh(result)

        assert result.mutation_score == 0.85
        assert result.total_mutants == result.killed_mutants + result.survived_mutants


@pytest.mark.database
@pytest.mark.models
class TestNonFunctionalCheckOperations:
    """测试 NonFunctionalCheck 模型操作"""

    def test_performance_check(self, db_session: Session):
        """测试性能检查"""
        project = Project(name="性能检查项目")
        db_session.add(project)
        db_session.commit()

        check = NonFunctionalCheck(
            project_id=project.id,
            check_type="performance",
            check_name="API响应时间",
            description="检查API响应时间是否在阈值内",
            baseline_value=100.0,
            actual_value=85.5,
            unit="ms",
            status="passed",
            recommendations="响应时间良好"
        )
        db_session.add(check)
        db_session.commit()
        db_session.refresh(check)

        assert check.actual_value < check.baseline_value
        assert check.status == "passed"

    def test_security_check(self, db_session: Session):
        """测试安全检查"""
        project = Project(name="安全检查项目")
        db_session.add(project)
        db_session.commit()

        check = NonFunctionalCheck(
            project_id=project.id,
            check_type="security",
            check_name="SQL注入检测",
            status="passed",
            details={"vulnerabilities_found": 0}
        )
        db_session.add(check)
        db_session.commit()
        db_session.refresh(check)

        assert check.check_type == "security"


@pytest.mark.database
@pytest.mark.models
class TestPipelineStageOperations:
    """测试 PipelineStage 模型操作"""

    def test_pipeline_stage_sequence(self, db_session: Session):
        """测试流水线阶段顺序"""
        project = Project(name="流水线项目")
        db_session.add(project)
        db_session.commit()

        stages = [
            PipelineStage(project_id=project.id, stage_name="需求分析", stage_order=1),
            PipelineStage(project_id=project.id, stage_name="设计", stage_order=2),
            PipelineStage(project_id=project.id, stage_name="开发", stage_order=3),
            PipelineStage(project_id=project.id, stage_name="测试", stage_order=4),
        ]
        db_session.add_all(stages)
        db_session.commit()

        ordered_stages = db_session.query(PipelineStage).filter(
            PipelineStage.project_id == project.id
        ).order_by(PipelineStage.stage_order).all()

        assert ordered_stages[0].stage_name == "需求分析"
        assert ordered_stages[-1].stage_name == "测试"

    def test_pipeline_stage_with_approval(self, db_session: Session):
        """测试带审批的流水线阶段"""
        project = Project(name="审批流水线项目")
        db_session.add(project)
        db_session.commit()

        approval = HumanApproval(
            project_id=project.id,
            approval_type="stage_gate",
            title="设计阶段审批",
            status="pending"
        )
        db_session.add(approval)
        db_session.commit()

        stage = PipelineStage(
            project_id=project.id,
            stage_name="设计",
            stage_order=2,
            requires_human=1,
            human_approval_id=approval.id,
            status="waiting_approval"
        )
        db_session.add(stage)
        db_session.commit()
        db_session.refresh(stage)

        assert stage.requires_human == 1


@pytest.mark.database
@pytest.mark.models
class TestRequirementTraceOperations:
    """测试 RequirementTrace 模型操作"""

    def test_requirement_trace_create(self, db_session: Session):
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
            test_case_id="TC-001",
            status="verified"
        )
        db_session.add(trace)
        db_session.commit()
        db_session.refresh(trace)

        assert trace.requirement_id == "REQ-001"
        assert trace.trace_type == "implements"

    def test_requirement_coverage(self, db_session: Session):
        """测试需求覆盖"""
        project = Project(name="需求覆盖项目")
        db_session.add(project)
        db_session.commit()

        traces = [
            RequirementTrace(
                project_id=project.id,
                requirement_id="REQ-001",
                requirement_title="功能1",
                status="verified"
            ),
            RequirementTrace(
                project_id=project.id,
                requirement_id="REQ-002",
                requirement_title="功能2",
                status="pending"
            ),
        ]
        db_session.add_all(traces)
        db_session.commit()

        verified_count = db_session.query(RequirementTrace).filter(
            RequirementTrace.project_id == project.id,
            RequirementTrace.status == "verified"
        ).count()

        assert verified_count == 1


@pytest.mark.database
@pytest.mark.models
class TestClarificationQuestionOperations:
    """测试 ClarificationQuestion 模型操作"""

    def test_question_create_and_answer(self, db_session: Session):
        """测试问题创建和回答"""
        project = Project(name="问题项目")
        db_session.add(project)
        db_session.commit()

        question = ClarificationQuestion(
            project_id=project.id,
            question="是否需要支持多语言？",
            question_type="requirement",
            context="国际化需求",
            status="pending"
        )
        db_session.add(question)
        db_session.commit()

        question.answer = "需要支持中英文"
        question.answered_by = "产品经理"
        question.answered_at = datetime.utcnow()
        question.status = "answered"
        db_session.commit()
        db_session.refresh(question)

        assert question.status == "answered"
        assert question.answer is not None

    def test_question_confirmation(self, db_session: Session):
        """测试问题确认"""
        project = Project(name="确认问题项目")
        db_session.add(project)
        db_session.commit()

        question = ClarificationQuestion(
            project_id=project.id,
            question="数据库类型？",
            answer="PostgreSQL",
            answered_by="架构师",
            status="answered"
        )
        db_session.add(question)
        db_session.commit()

        question.confirmed_by = "技术总监"
        question.confirmed_at = datetime.utcnow()
        question.status = "confirmed"
        db_session.commit()
        db_session.refresh(question)

        assert question.status == "confirmed"


@pytest.mark.database
@pytest.mark.models
class TestComplexRelationships:
    """测试复杂模型关系"""

    def test_full_project_workflow(self, db_session: Session):
        """测试完整项目工作流"""
        department = Department(name="开发部", pinyin="kaifabu")
        db_session.add(department)
        db_session.commit()

        project = Project(
            name="完整工作流项目",
            status=ProjectStatus.DEVELOPMENT.value
        )
        db_session.add(project)
        db_session.commit()

        agent = Agent(
            name="工作流代理",
            department_id=department.id,
            status="busy"
        )
        db_session.add(agent)
        db_session.commit()

        task = Task(
            title="工作流任务",
            project_id=project.id,
            department_id=department.id,
            agent_id=agent.id,
            status=TaskStatus.IN_PROGRESS.value
        )
        db_session.add(task)
        db_session.commit()

        skill_call = SkillCall(
            skill_name="implement",
            caller=agent.name,
            status="started"
        )
        db_session.add(skill_call)
        db_session.commit()

        assignment = Assignment(
            agent_id=agent.id,
            task_id=task.id,
            skill_call_id=skill_call.id,
            status="assigned"
        )
        db_session.add(assignment)
        db_session.commit()

        db_session.refresh(project)
        db_session.refresh(agent)
        db_session.refresh(task)

        assert task.agent_id == agent.id
        assert task.project_id == project.id

    def test_cascading_skill_calls(self, db_session: Session):
        """测试级联技能调用"""
        parent = SkillCall(skill_name="main_task", caller="agent_001")
        db_session.add(parent)
        db_session.commit()

        child1 = SkillCall(
            skill_name="sub_task_1",
            caller="agent_001",
            parent_call_id=parent.id
        )
        db_session.add(child1)
        db_session.commit()

        grandchild = SkillCall(
            skill_name="sub_sub_task",
            caller="agent_001",
            parent_call_id=child1.id
        )
        db_session.add(grandchild)
        db_session.commit()

        db_session.refresh(parent)
        db_session.refresh(child1)

        assert len(parent.children) == 1
        assert len(child1.children) == 1

    def test_project_with_all_artifacts(self, db_session: Session):
        """测试项目包含所有产物"""
        project = Project(name="全产物项目")
        db_session.add(project)
        db_session.commit()

        milestone = Milestone(project_id=project.id, name="M1")
        acceptance_test = AcceptanceTest(
            project_id=project.id,
            scenario_name="测试场景"
        )
        artifact = IntermediateArtifact(
            project_id=project.id,
            artifact_type="code",
            name="main.py"
        )
        requirement_trace = RequirementTrace(
            project_id=project.id,
            requirement_id="REQ-001"
        )
        pipeline_stage = PipelineStage(
            project_id=project.id,
            stage_name="开发"
        )

        db_session.add_all([milestone, acceptance_test, artifact, requirement_trace, pipeline_stage])
        db_session.commit()

        db_session.refresh(project)

        assert len(project.milestones) >= 1
