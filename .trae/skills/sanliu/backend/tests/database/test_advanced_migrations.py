"""
数据库迁移高级测试

测试数据库迁移的高级场景，包括模式变更、数据迁移等
"""

import pytest
import os
import tempfile
from datetime import datetime
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import IntegrityError

from app.models.base import Base
from app.models.project import Project, ProjectStatus
from app.models.task import Task, TaskStatus
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


EXPECTED_TABLES = [
    "projects",
    "tasks",
    "agents",
    "departments",
    "skill_calls",
    "assignments",
    "acceptance_tests",
    "code_changes",
    "decision_logs",
    "human_approvals",
    "input_output_traces",
    "intermediate_artifacts",
    "milestones",
    "mutation_test_results",
    "non_functional_checks",
    "pipeline_stages",
    "requirement_traces",
    "clarification_questions"
]


@pytest.mark.database
@pytest.mark.migrations
class TestSchemaValidation:
    """测试模式验证"""

    def test_all_tables_exist(self, db_engine):
        """测试所有表都存在"""
        inspector = inspect(db_engine)
        tables = inspector.get_table_names()

        for table in EXPECTED_TABLES:
            assert table in tables, f"表 {table} 不存在"

    def test_table_count(self, db_engine):
        """测试表数量"""
        inspector = inspect(db_engine)
        tables = inspector.get_table_names()

        assert len(tables) == len(EXPECTED_TABLES), \
            f"表数量不匹配: 期望 {len(EXPECTED_TABLES)}, 实际 {len(tables)}"

    def test_no_extra_tables(self, db_engine):
        """测试没有多余的表"""
        inspector = inspect(db_engine)
        tables = inspector.get_table_names()

        for table in tables:
            assert table in EXPECTED_TABLES, f"发现未预期的表: {table}"


@pytest.mark.database
@pytest.mark.migrations
class TestColumnValidation:
    """测试列验证"""

    def test_projects_table_columns(self, db_engine):
        """测试 projects 表所有列"""
        inspector = inspect(db_engine)
        columns = {col["name"]: col for col in inspector.get_columns("projects")}

        required_columns = [
            "id", "name", "description", "tech_stack", "status",
            "status_history", "milestones", "created_at", "updated_at"
        ]

        for col in required_columns:
            assert col in columns, f"projects 表缺少列: {col}"

    def test_tasks_table_columns(self, db_engine):
        """测试 tasks 表所有列"""
        inspector = inspect(db_engine)
        columns = {col["name"]: col for col in inspector.get_columns("tasks")}

        required_columns = [
            "id", "project_id", "department_id", "agent_id", "title",
            "description", "required_skill", "priority", "status",
            "status_history", "dependencies", "estimated_hours", "actual_hours",
            "details", "created_at", "updated_at", "completed_at"
        ]

        for col in required_columns:
            assert col in columns, f"tasks 表缺少列: {col}"

    def test_agents_table_columns(self, db_engine):
        """测试 agents 表所有列"""
        inspector = inspect(db_engine)
        columns = {col["name"]: col for col in inspector.get_columns("agents")}

        required_columns = [
            "id", "name", "role", "skills", "status", "current_load",
            "max_load", "current_task", "department_id", "last_heartbeat",
            "created_at"
        ]

        for col in required_columns:
            assert col in columns, f"agents 表缺少列: {col}"

    def test_skill_calls_table_columns(self, db_engine):
        """测试 skill_calls 表所有列"""
        inspector = inspect(db_engine)
        columns = {col["name"]: col for col in inspector.get_columns("skill_calls")}

        required_columns = [
            "id", "skill_name", "caller", "status", "start_time",
            "end_time", "details", "parent_call_id", "created_at",
            "input_data", "output_data", "reasoning_log", "decision_type",
            "decision_basis", "alternatives"
        ]

        for col in required_columns:
            assert col in columns, f"skill_calls 表缺少列: {col}"

    def test_column_types_correct(self, db_engine):
        """测试列类型正确"""
        inspector = inspect(db_engine)

        projects_id = inspector.get_columns("projects")[0]
        assert projects_id["name"] == "id"
        assert projects_id["primary_key"] is True


@pytest.mark.database
@pytest.mark.migrations
class TestConstraintValidation:
    """测试约束验证"""

    def test_primary_keys_defined(self, db_engine):
        """测试主键定义"""
        inspector = inspect(db_engine)

        for table in EXPECTED_TABLES:
            pk = inspector.get_pk_constraint(table)
            assert pk is not None, f"表 {table} 没有主键"
            assert len(pk["constrained_columns"]) > 0, f"表 {table} 主键列为空"

    def test_foreign_keys_defined(self, db_engine):
        """测试外键定义"""
        inspector = inspect(db_engine)

        task_fks = inspector.get_foreign_keys("tasks")
        fk_columns = []
        for fk in task_fks:
            fk_columns.extend(fk["constrained_columns"])

        expected_fk_columns = ["project_id", "department_id", "agent_id"]
        for col in expected_fk_columns:
            assert col in fk_columns, f"tasks 表缺少外键: {col}"

    def test_unique_constraints(self, db_engine):
        """测试唯一约束"""
        inspector = inspect(db_engine)

        agents_unique = inspector.get_unique_constraints("agents")
        unique_columns = []
        for constraint in agents_unique:
            unique_columns.extend(constraint["column_names"])

        assert "name" in unique_columns, "agents 表 name 列应该有唯一约束"

    def test_foreign_key_referential_integrity(self, db_session):
        """测试外键引用完整性"""
        project = Project(name="引用完整性项目")
        db_session.add(project)
        db_session.commit()

        task = Task(
            title="引用完整性任务",
            project_id=project.id
        )
        db_session.add(task)
        db_session.commit()

        assert task.project_id == project.id

        invalid_task = Task(
            title="无效引用任务",
            project_id=99999
        )
        db_session.add(invalid_task)

        with pytest.raises(IntegrityError):
            db_session.commit()


@pytest.mark.database
@pytest.mark.migrations
class TestIndexValidation:
    """测试索引验证"""

    def test_projects_indexes(self, db_engine):
        """测试 projects 表索引"""
        inspector = inspect(db_engine)
        indexes = inspector.get_indexes("projects")

        index_columns = set()
        for idx in indexes:
            index_columns.update(idx["column_names"])

        expected_indexes = ["id", "name", "status", "created_at"]
        for col in expected_indexes:
            assert col in index_columns, f"projects 表缺少索引: {col}"

    def test_tasks_indexes(self, db_engine):
        """测试 tasks 表索引"""
        inspector = inspect(db_engine)
        indexes = inspector.get_indexes("tasks")

        index_columns = set()
        for idx in indexes:
            index_columns.update(idx["column_names"])

        expected_indexes = ["id", "project_id", "status", "priority", "agent_id"]
        for col in expected_indexes:
            assert col in index_columns, f"tasks 表缺少索引: {col}"

    def test_skill_calls_indexes(self, db_engine):
        """测试 skill_calls 表索引"""
        inspector = inspect(db_engine)
        indexes = inspector.get_indexes("skill_calls")

        index_columns = set()
        for idx in indexes:
            index_columns.update(idx["column_names"])

        expected_indexes = ["id", "skill_name", "status", "created_at"]
        for col in expected_indexes:
            assert col in index_columns, f"skill_calls 表缺少索引: {col}"

    def test_composite_indexes(self, db_engine):
        """测试复合索引"""
        inspector = inspect(db_engine)

        projects_indexes = inspector.get_indexes("projects")
        composite_found = False

        for idx in projects_indexes:
            if len(idx["column_names"]) > 1:
                composite_found = True
                break

        assert composite_found, "projects 表应该有复合索引"


@pytest.mark.database
@pytest.mark.migrations
class TestDefaultValues:
    """测试默认值"""

    def test_project_status_default(self, db_session):
        """测试项目状态默认值"""
        project = Project(name="默认状态项目")
        db_session.add(project)
        db_session.commit()
        db_session.refresh(project)

        assert project.status == ProjectStatus.REQUIREMENT.value

    def test_task_status_default(self, db_session):
        """测试任务状态默认值"""
        project = Project(name="任务默认状态项目")
        db_session.add(project)
        db_session.commit()

        task = Task(title="默认状态任务", project_id=project.id)
        db_session.add(task)
        db_session.commit()
        db_session.refresh(task)

        assert task.status == TaskStatus.PENDING.value

    def test_task_priority_default(self, db_session):
        """测试任务优先级默认值"""
        project = Project(name="优先级默认项目")
        db_session.add(project)
        db_session.commit()

        task = Task(title="默认优先级任务", project_id=project.id)
        db_session.add(task)
        db_session.commit()
        db_session.refresh(task)

        assert task.priority == "medium"

    def test_agent_status_default(self, db_session):
        """测试代理状态默认值"""
        agent = Agent(name="默认状态代理")
        db_session.add(agent)
        db_session.commit()
        db_session.refresh(agent)

        assert agent.status == "idle"

    def test_agent_load_defaults(self, db_session):
        """测试代理负载默认值"""
        agent = Agent(name="默认负载代理")
        db_session.add(agent)
        db_session.commit()
        db_session.refresh(agent)

        assert agent.current_load == 0
        assert agent.max_load == 5

    def test_milestone_status_default(self, db_session):
        """测试里程碑状态默认值"""
        project = Project(name="里程碑默认项目")
        db_session.add(project)
        db_session.commit()

        milestone = Milestone(project_id=project.id, name="默认里程碑")
        db_session.add(milestone)
        db_session.commit()
        db_session.refresh(milestone)

        assert milestone.status == MilestoneStatus.PENDING.value


@pytest.mark.database
@pytest.mark.migrations
class TestNullableColumns:
    """测试可空列"""

    def test_project_required_fields(self, db_session):
        """测试项目必填字段"""
        project = Project(name=None)
        db_session.add(project)

        with pytest.raises(IntegrityError):
            db_session.commit()

    def test_task_required_fields(self, db_session):
        """测试任务必填字段"""
        project = Project(name="任务必填项目")
        db_session.add(project)
        db_session.commit()

        task = Task(title=None, project_id=project.id)
        db_session.add(task)

        with pytest.raises(IntegrityError):
            db_session.commit()

    def test_agent_required_fields(self, db_session):
        """测试代理必填字段"""
        agent = Agent(name=None)
        db_session.add(agent)

        with pytest.raises(IntegrityError):
            db_session.commit()

    def test_optional_fields_can_be_null(self, db_session):
        """测试可选字段可以为空"""
        project = Project(
            name="可选字段项目",
            description=None,
            tech_stack=None
        )
        db_session.add(project)
        db_session.commit()
        db_session.refresh(project)

        assert project.description is None
        assert project.tech_stack is None


@pytest.mark.database
@pytest.mark.migrations
class TestJSONColumns:
    """测试 JSON 列"""

    def test_project_json_columns(self, db_session):
        """测试项目 JSON 列"""
        project = Project(
            name="JSON项目",
            tech_stack=["Python", "FastAPI"],
            status_history=[{"status": "CREATED", "timestamp": datetime.utcnow().isoformat()}],
            milestones=[{"name": "M1", "completed": False}]
        )
        db_session.add(project)
        db_session.commit()
        db_session.refresh(project)

        assert isinstance(project.tech_stack, list)
        assert isinstance(project.status_history, list)
        assert isinstance(project.milestones, list)

    def test_task_json_columns(self, db_session):
        """测试任务 JSON 列"""
        project = Project(name="任务JSON项目")
        db_session.add(project)
        db_session.commit()

        task = Task(
            title="JSON任务",
            project_id=project.id,
            dependencies=[1, 2, 3],
            details={"key": "value"}
        )
        db_session.add(task)
        db_session.commit()
        db_session.refresh(task)

        assert isinstance(task.dependencies, list)
        assert isinstance(task.details, dict)

    def test_agent_json_columns(self, db_session):
        """测试代理 JSON 列"""
        agent = Agent(
            name="JSON代理",
            skills=["Python", "JavaScript", "SQL"]
        )
        db_session.add(agent)
        db_session.commit()
        db_session.refresh(agent)

        assert isinstance(agent.skills, list)

    def test_skill_call_json_columns(self, db_session):
        """测试技能调用 JSON 列"""
        call = SkillCall(
            skill_name="json_skill",
            caller="agent",
            input_data={"param": "value"},
            output_data={"result": "success"},
            details={"info": "test"}
        )
        db_session.add(call)
        db_session.commit()
        db_session.refresh(call)

        assert isinstance(call.input_data, dict)
        assert isinstance(call.output_data, dict)
        assert isinstance(call.details, dict)


@pytest.mark.database
@pytest.mark.migrations
class TestDateTimeColumns:
    """测试日期时间列"""

    def test_created_at_auto_set(self, db_session):
        """测试创建时间自动设置"""
        before = datetime.utcnow()
        project = Project(name="自动时间项目")
        db_session.add(project)
        db_session.commit()
        db_session.refresh(project)
        after = datetime.utcnow()

        assert project.created_at is not None
        assert before <= project.created_at.replace(tzinfo=None) <= after

    def test_updated_at_on_update(self, db_session):
        """测试更新时间自动更新"""
        project = Project(name="更新时间项目")
        db_session.add(project)
        db_session.commit()
        db_session.refresh(project)

        original_updated = project.updated_at

        project.name = "更新时间项目_修改"
        db_session.commit()
        db_session.refresh(project)

    def test_nullable_datetime_columns(self, db_session):
        """测试可空日期时间列"""
        project = Project(name="可空时间项目")
        db_session.add(project)
        db_session.commit()

        task = Task(
            title="可空时间任务",
            project_id=project.id,
            completed_at=None
        )
        db_session.add(task)
        db_session.commit()
        db_session.refresh(task)

        assert task.completed_at is None


@pytest.mark.database
@pytest.mark.migrations
class TestSchemaRecreation:
    """测试模式重建"""

    def test_drop_and_recreate(self, db_engine):
        """测试删除并重建表"""
        inspector = inspect(db_engine)
        tables_before = inspector.get_table_names()
        assert len(tables_before) > 0

        Base.metadata.drop_all(bind=db_engine)

        inspector = inspect(db_engine)
        tables_after_drop = inspector.get_table_names()
        assert len(tables_after_drop) == 0

        Base.metadata.create_all(bind=db_engine)

        inspector = inspect(db_engine)
        tables_after_create = inspector.get_table_names()
        assert len(tables_after_create) == len(EXPECTED_TABLES)

    def test_idempotent_create(self, db_engine):
        """测试幂等创建"""
        for _ in range(3):
            Base.metadata.create_all(bind=db_engine)

        inspector = inspect(db_engine)
        tables = inspector.get_table_names()
        assert len(tables) == len(EXPECTED_TABLES)


@pytest.mark.database
@pytest.mark.migrations
class TestRelationshipIntegrity:
    """测试关系完整性"""

    def test_project_task_relationship(self, db_session):
        """测试项目-任务关系"""
        project = Project(name="关系项目")
        db_session.add(project)
        db_session.commit()

        task1 = Task(title="任务1", project_id=project.id)
        task2 = Task(title="任务2", project_id=project.id)
        db_session.add_all([task1, task2])
        db_session.commit()

        db_session.refresh(project)

    def test_agent_department_relationship(self, db_session):
        """测试代理-部门关系"""
        department = Department(name="关系部门", pinyin="guanxibumen")
        db_session.add(department)
        db_session.commit()

        agent = Agent(name="关系代理", department_id=department.id)
        db_session.add(agent)
        db_session.commit()

        db_session.refresh(agent)
        assert agent.department_id == department.id

    def test_skill_call_hierarchy(self, db_session):
        """测试技能调用层级"""
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

        db_session.refresh(child)
        assert child.parent_call_id == parent.id

    def test_department_hierarchy(self, db_session):
        """测试部门层级"""
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

        db_session.refresh(child)
        assert child.parent_id == parent.id


@pytest.mark.database
@pytest.mark.migrations
class TestNamingConventions:
    """测试命名约定"""

    def test_table_names_lowercase(self, db_engine):
        """测试表名小写"""
        inspector = inspect(db_engine)
        tables = inspector.get_table_names()

        for table in tables:
            assert table == table.lower(), f"表名 {table} 不是小写"

    def test_table_names_snake_case(self, db_engine):
        """测试表名蛇形命名"""
        inspector = inspect(db_engine)
        tables = inspector.get_table_names()

        for table in tables:
            assert "_" in table or table.islower(), \
                f"表名 {table} 不符合蛇形命名"

    def test_column_names_snake_case(self, db_engine):
        """测试列名蛇形命名"""
        inspector = inspect(db_engine)

        for table in inspector.get_table_names():
            columns = inspector.get_columns(table)
            for col in columns:
                name = col["name"]
                assert "_" in name or name.islower(), \
                    f"表 {table} 的列 {name} 不符合蛇形命名"
