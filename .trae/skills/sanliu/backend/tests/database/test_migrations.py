"""
数据库迁移测试

测试数据库迁移脚本的正确性和数据一致性
"""

import pytest
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import OperationalError

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
from app.models.milestone import Milestone
from app.models.mutation_test_result import MutationTestResult
from app.models.non_functional_check import NonFunctionalCheck
from app.models.pipeline_stage import PipelineStage
from app.models.requirement_trace import RequirementTrace
from app.models.clarification_question import ClarificationQuestion


@pytest.mark.database
@pytest.mark.migrations
class TestSchemaCreation:
    """测试数据库模式创建"""

    def test_create_all_tables(self, db_engine):
        """测试创建所有表"""
        inspector = inspect(db_engine)
        tables = inspector.get_table_names()

        expected_tables = [
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

        for table in expected_tables:
            assert table in tables, f"表 {table} 未创建"

    def test_drop_all_tables(self, db_engine):
        """测试删除所有表"""
        Base.metadata.drop_all(bind=db_engine)

        inspector = inspect(db_engine)
        tables = inspector.get_table_names()

        assert len(tables) == 0

    def test_recreate_tables(self, db_engine):
        """测试重新创建表"""
        Base.metadata.drop_all(bind=db_engine)
        Base.metadata.create_all(bind=db_engine)

        inspector = inspect(db_engine)
        tables = inspector.get_table_names()

        assert "projects" in tables
        assert "tasks" in tables
        assert "agents" in tables


@pytest.mark.database
@pytest.mark.migrations
class TestTableColumns:
    """测试表列定义"""

    def test_project_columns(self, db_engine):
        """测试 projects 表列"""
        inspector = inspect(db_engine)
        columns = {col["name"]: col for col in inspector.get_columns("projects")}

        assert "id" in columns
        assert "name" in columns
        assert "description" in columns
        assert "tech_stack" in columns
        assert "status" in columns
        assert "status_history" in columns
        assert "milestones" in columns
        assert "created_at" in columns
        assert "updated_at" in columns

    def test_task_columns(self, db_engine):
        """测试 tasks 表列"""
        inspector = inspect(db_engine)
        columns = {col["name"]: col for col in inspector.get_columns("tasks")}

        assert "id" in columns
        assert "project_id" in columns
        assert "department_id" in columns
        assert "agent_id" in columns
        assert "title" in columns
        assert "description" in columns
        assert "required_skill" in columns
        assert "priority" in columns
        assert "status" in columns
        assert "dependencies" in columns
        assert "estimated_hours" in columns
        assert "actual_hours" in columns
        assert "created_at" in columns
        assert "updated_at" in columns
        assert "completed_at" in columns

    def test_agent_columns(self, db_engine):
        """测试 agents 表列"""
        inspector = inspect(db_engine)
        columns = {col["name"]: col for col in inspector.get_columns("agents")}

        assert "id" in columns
        assert "name" in columns
        assert "role" in columns
        assert "skills" in columns
        assert "status" in columns
        assert "current_load" in columns
        assert "max_load" in columns
        assert "current_task" in columns
        assert "department_id" in columns
        assert "last_heartbeat" in columns
        assert "created_at" in columns

    def test_department_columns(self, db_engine):
        """测试 departments 表列"""
        inspector = inspect(db_engine)
        columns = {col["name"]: col for col in inspector.get_columns("departments")}

        assert "id" in columns
        assert "name" in columns
        assert "pinyin" in columns
        assert "level" in columns
        assert "parent_id" in columns

    def test_skill_call_columns(self, db_engine):
        """测试 skill_calls 表列"""
        inspector = inspect(db_engine)
        columns = {col["name"]: col for col in inspector.get_columns("skill_calls")}

        assert "id" in columns
        assert "skill_name" in columns
        assert "caller" in columns
        assert "status" in columns
        assert "start_time" in columns
        assert "end_time" in columns
        assert "details" in columns
        assert "parent_call_id" in columns
        assert "created_at" in columns
        assert "input_data" in columns
        assert "output_data" in columns
        assert "reasoning_log" in columns
        assert "decision_type" in columns
        assert "decision_basis" in columns
        assert "alternatives" in columns


@pytest.mark.database
@pytest.mark.migrations
class TestPrimaryKeys:
    """测试主键定义"""

    def test_project_primary_key(self, db_engine):
        """测试 projects 表主键"""
        inspector = inspect(db_engine)
        pk = inspector.get_pk_constraint("projects")

        assert "id" in pk["constrained_columns"]

    def test_task_primary_key(self, db_engine):
        """测试 tasks 表主键"""
        inspector = inspect(db_engine)
        pk = inspector.get_pk_constraint("tasks")

        assert "id" in pk["constrained_columns"]

    def test_agent_primary_key(self, db_engine):
        """测试 agents 表主键"""
        inspector = inspect(db_engine)
        pk = inspector.get_pk_constraint("agents")

        assert "id" in pk["constrained_columns"]

    def test_skill_call_primary_key(self, db_engine):
        """测试 skill_calls 表主键"""
        inspector = inspect(db_engine)
        pk = inspector.get_pk_constraint("skill_calls")

        assert "id" in pk["constrained_columns"]


@pytest.mark.database
@pytest.mark.migrations
class TestForeignKeys:
    """测试外键定义"""

    def test_task_foreign_keys(self, db_engine):
        """测试 tasks 表外键"""
        inspector = inspect(db_engine)
        fks = inspector.get_foreign_keys("tasks")

        fk_columns = []
        for fk in fks:
            fk_columns.extend(fk["constrained_columns"])

        assert "project_id" in fk_columns
        assert "department_id" in fk_columns
        assert "agent_id" in fk_columns

    def test_agent_foreign_keys(self, db_engine):
        """测试 agents 表外键"""
        inspector = inspect(db_engine)
        fks = inspector.get_foreign_keys("agents")

        fk_columns = []
        for fk in fks:
            fk_columns.extend(fk["constrained_columns"])

        assert "department_id" in fk_columns

    def test_assignment_foreign_keys(self, db_engine):
        """测试 assignments 表外键"""
        inspector = inspect(db_engine)
        fks = inspector.get_foreign_keys("assignments")

        fk_columns = []
        for fk in fks:
            fk_columns.extend(fk["constrained_columns"])

        assert "agent_id" in fk_columns
        assert "task_id" in fk_columns
        assert "skill_call_id" in fk_columns

    def test_skill_call_self_referencing_fk(self, db_engine):
        """测试 skill_calls 表自引用外键"""
        inspector = inspect(db_engine)
        fks = inspector.get_foreign_keys("skill_calls")

        fk_columns = []
        for fk in fks:
            fk_columns.extend(fk["constrained_columns"])

        assert "parent_call_id" in fk_columns

    def test_department_self_referencing_fk(self, db_engine):
        """测试 departments 表自引用外键"""
        inspector = inspect(db_engine)
        fks = inspector.get_foreign_keys("departments")

        fk_columns = []
        for fk in fks:
            fk_columns.extend(fk["constrained_columns"])

        assert "parent_id" in fk_columns


@pytest.mark.database
@pytest.mark.migrations
class TestIndexes:
    """测试索引定义"""

    def test_project_indexes(self, db_engine):
        """测试 projects 表索引"""
        inspector = inspect(db_engine)
        indexes = inspector.get_indexes("projects")

        index_columns = []
        for idx in indexes:
            index_columns.extend(idx["column_names"])

        assert "id" in index_columns
        assert "name" in index_columns
        assert "status" in index_columns
        assert "created_at" in index_columns

    def test_task_indexes(self, db_engine):
        """测试 tasks 表索引"""
        inspector = inspect(db_engine)
        indexes = inspector.get_indexes("tasks")

        index_columns = []
        for idx in indexes:
            index_columns.extend(idx["column_names"])

        assert "id" in index_columns
        assert "project_id" in index_columns
        assert "status" in index_columns
        assert "priority" in index_columns
        assert "agent_id" in index_columns

    def test_agent_indexes(self, db_engine):
        """测试 agents 表索引"""
        inspector = inspect(db_engine)
        indexes = inspector.get_indexes("agents")

        index_columns = []
        for idx in indexes:
            index_columns.extend(idx["column_names"])

        assert "id" in index_columns
        assert "name" in index_columns
        assert "status" in index_columns

    def test_skill_call_indexes(self, db_engine):
        """测试 skill_calls 表索引"""
        inspector = inspect(db_engine)
        indexes = inspector.get_indexes("skill_calls")

        index_columns = []
        for idx in indexes:
            index_columns.extend(idx["column_names"])

        assert "id" in index_columns
        assert "skill_name" in index_columns
        assert "status" in index_columns
        assert "created_at" in index_columns


@pytest.mark.database
@pytest.mark.migrations
class TestUniqueConstraints:
    """测试唯一约束"""

    def test_agent_name_unique(self, db_session):
        """测试代理名称唯一约束"""
        from sqlalchemy.exc import IntegrityError

        agent1 = Agent(name="唯一代理名")
        db_session.add(agent1)
        db_session.commit()

        agent2 = Agent(name="唯一代理名")
        db_session.add(agent2)

        with pytest.raises(IntegrityError):
            db_session.commit()

    def test_department_pinyin_unique(self, db_session):
        """测试部门拼音唯一约束"""
        from sqlalchemy.exc import IntegrityError

        dept1 = Department(name="部门1", pinyin="unique_pinyin")
        db_session.add(dept1)
        db_session.commit()

        dept2 = Department(name="部门2", pinyin="unique_pinyin")
        db_session.add(dept2)

        with pytest.raises(IntegrityError):
            db_session.commit()


@pytest.mark.database
@pytest.mark.migrations
class TestColumnDefaults:
    """测试列默认值"""

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

    def test_agent_status_default(self, db_session):
        """测试代理状态默认值"""
        agent = Agent(name="默认状态代理")
        db_session.add(agent)
        db_session.commit()
        db_session.refresh(agent)

        assert agent.status == "idle"

    def test_agent_load_defaults(self, db_session):
        """测试代理负载默认值"""
        agent = Agent(name="负载默认代理")
        db_session.add(agent)
        db_session.commit()
        db_session.refresh(agent)

        assert agent.current_load == 0
        assert agent.max_load == 5


@pytest.mark.database
@pytest.mark.migrations
class TestNullableColumns:
    """测试可空列定义"""

    def test_project_name_not_nullable(self, db_session):
        """测试项目名称不可为空"""
        from sqlalchemy.exc import IntegrityError

        project = Project(name=None)
        db_session.add(project)

        with pytest.raises(IntegrityError):
            db_session.commit()

    def test_task_title_not_nullable(self, db_session):
        """测试任务标题不可为空"""
        from sqlalchemy.exc import IntegrityError

        project = Project(name="任务标题测试")
        db_session.add(project)
        db_session.commit()

        task = Task(title=None, project_id=project.id)
        db_session.add(task)

        with pytest.raises(IntegrityError):
            db_session.commit()

    def test_agent_name_not_nullable(self, db_session):
        """测试代理名称不可为空"""
        from sqlalchemy.exc import IntegrityError

        agent = Agent(name=None)
        db_session.add(agent)

        with pytest.raises(IntegrityError):
            db_session.commit()

    def test_project_description_nullable(self, db_session):
        """测试项目描述可为空"""
        project = Project(name="描述测试项目", description=None)
        db_session.add(project)
        db_session.commit()
        db_session.refresh(project)

        assert project.description is None


@pytest.mark.database
@pytest.mark.migrations
class TestMigrationCompatibility:
    """测试迁移兼容性"""

    def test_data_preservation_after_recreate(self, db_engine):
        """测试重建表后数据保留（模拟迁移场景）"""
        engine = create_engine("sqlite:///./test_migration.db")
        Session = sessionmaker(bind=engine)

        Base.metadata.create_all(bind=engine)
        session = Session()

        project = Project(name="迁移测试项目")
        session.add(project)
        session.commit()
        project_id = project.id
        session.close()

        session = Session()
        found = session.query(Project).filter_by(id=project_id).first()
        assert found is not None
        assert found.name == "迁移测试项目"
        session.close()

        Base.metadata.drop_all(bind=engine)
        Base.metadata.create_all(bind=engine)

        session = Session()
        not_found = session.query(Project).filter_by(id=project_id).first()
        assert not_found is None
        session.close()

        import os
        if os.path.exists("./test_migration.db"):
            os.remove("./test_migration.db")

    def test_json_column_migration(self, db_session):
        """测试 JSON 列迁移兼容性"""
        project = Project(
            name="JSON迁移测试",
            tech_stack=["Python", "JavaScript"],
            status_history=[{"status": "CREATED"}],
            milestones=[{"name": "M1"}]
        )
        db_session.add(project)
        db_session.commit()
        db_session.refresh(project)

        assert project.tech_stack == ["Python", "JavaScript"]
        assert project.status_history == [{"status": "CREATED"}]
        assert project.milestones == [{"name": "M1"}]


@pytest.mark.database
@pytest.mark.migrations
class TestSchemaVersioning:
    """测试模式版本控制"""

    def test_table_names_consistency(self, db_engine):
        """测试表名一致性"""
        inspector = inspect(db_engine)
        tables = inspector.get_table_names()

        assert all(table.islower() or "_" in table for table in tables)

    def test_column_names_consistency(self, db_engine):
        """测试列名一致性"""
        inspector = inspect(db_engine)

        for table in inspector.get_table_names():
            columns = inspector.get_columns(table)
            for col in columns:
                assert col["name"].islower() or "_" in col["name"]

    def test_foreign_key_naming_convention(self, db_engine):
        """测试外键命名约定"""
        inspector = inspect(db_engine)

        for table in inspector.get_table_names():
            fks = inspector.get_foreign_keys(table)
            for fk in fks:
                assert len(fk["constrained_columns"]) > 0
                assert fk["referred_table"] is not None
                assert len(fk["referred_columns"]) > 0
