"""
测试配置和 Fixtures

提供测试所需的配置和 fixtures
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from unittest.mock import Mock, MagicMock

# 导入应用
import sys
from pathlib import Path

backend_dir = Path(__file__).parent.parent / 'backend'
sys.path.insert(0, str(backend_dir))

from app.main import app
from app.models.base import Base, get_db
from app.models.project import Project
from app.models.task import Task
from app.models.agent import Agent
from app.models.skill_call import SkillCall
from app.models.assignment import Assignment
from app.models.department import Department


# 测试数据库配置
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db_session():
    """创建测试数据库会话"""
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db_session):
    """创建测试客户端"""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
def mock_redis():
    """创建 Mock Redis 客户端"""
    mock = Mock()
    mock.get_json.return_value = None
    mock.set_json.return_value = True
    mock.delete.return_value = True
    mock.exists.return_value = False
    return mock


# 辅助函数
def create_test_project(db, **kwargs):
    """创建测试项目"""
    project_data = {
        "name": kwargs.get("name", "Test Project"),
        "description": kwargs.get("description", "Test Description"),
        "tech_stack": kwargs.get("tech_stack", ["Python", "FastAPI"]),
        "status": kwargs.get("status", "REQUIREMENT")
    }
    project = Project(**project_data)
    db.add(project)
    db.commit()
    db.refresh(project)
    return project


def create_test_task(db, **kwargs):
    """创建测试任务"""
    from app.models.task import TaskStatus
    task_data = {
        "title": kwargs.get("title", "Test Task"),
        "description": kwargs.get("description", "Test Description"),
        "project_id": kwargs.get("project_id"),
        "agent_id": kwargs.get("agent_id"),
        "status": kwargs.get("status", TaskStatus.PENDING.value),
        "priority": kwargs.get("priority", "medium"),
        "required_skill": kwargs.get("required_skill"),
        "estimated_hours": kwargs.get("estimated_hours"),
        "actual_hours": kwargs.get("actual_hours"),
        "dependencies": kwargs.get("dependencies", [])
    }
    task = Task(**task_data)
    db.add(task)
    db.commit()
    db.refresh(task)
    return task


def create_test_agent(db, **kwargs):
    """创建测试代理"""
    agent_data = {
        "name": kwargs.get("name", "Test Agent"),
        "role": kwargs.get("role", "Developer"),
        "skills": kwargs.get("skills", ["Python", "FastAPI"]),
        "status": kwargs.get("status", "idle"),
        "current_load": kwargs.get("current_load", 0),
        "max_load": kwargs.get("max_load", 5),
        "department_id": kwargs.get("department_id"),
        "current_task": kwargs.get("current_task")
    }
    agent = Agent(**agent_data)
    db.add(agent)
    db.commit()
    db.refresh(agent)
    return agent


def create_test_skill_call(db, **kwargs):
    """创建测试 Skill Call"""
    call_data = {
        "skill_name": kwargs.get("skill_name", "test_skill"),
        "caller": kwargs.get("caller", "test_caller"),
        "status": kwargs.get("status", "started"),
        "details": kwargs.get("details", {}),
        "parent_call_id": kwargs.get("parent_call_id"),
        "error_message": kwargs.get("error_message")
    }
    call = SkillCall(**call_data)
    db.add(call)
    db.commit()
    db.refresh(call)
    return call


def create_test_assignment(db, **kwargs):
    """创建测试 Assignment"""
    assignment_data = {
        "task_id": kwargs.get("task_id"),
        "agent_id": kwargs.get("agent_id"),
        "status": kwargs.get("status", "assigned")
    }
    assignment = Assignment(**assignment_data)
    db.add(assignment)
    db.commit()
    db.refresh(assignment)
    return assignment


def create_test_department(db, **kwargs):
    """创建测试部门"""
    department_data = {
        "name": kwargs.get("name", "Test Department"),
        "description": kwargs.get("description", "Test Description")
    }
    department = Department(**department_data)
    db.add(department)
    db.commit()
    db.refresh(department)
    return department


# Fixtures 提供示例数据
@pytest.fixture
def sample_project_data():
    """提供示例项目数据"""
    return {
        "name": "Sample Project",
        "description": "This is a sample project for testing",
        "tech_stack": ["Python", "FastAPI", "React"],
        "status": "REQUIREMENT"
    }


@pytest.fixture
def sample_task_data():
    """提供示例任务数据"""
    return {
        "title": "Sample Task",
        "description": "This is a sample task for testing",
        "priority": "high",
        "estimated_hours": 8.0
    }


@pytest.fixture
def sample_agent_data():
    """提供示例代理数据"""
    return {
        "name": "Sample Agent",
        "role": "Developer",
        "skills": ["Python", "FastAPI", "SQLAlchemy"],
        "max_load": 10
    }


@pytest.fixture
def sample_skill_call_data():
    """提供示例 Skill Call 数据"""
    return {
        "skill_name": "code_generation",
        "caller": "agent_001",
        "status": "started",
        "details": {"language": "python", "task": "generate_function"}
    }


# 标记 fixtures
@pytest.fixture(autouse=True)
def setup_test_environment(monkeypatch):
    """设置测试环境"""
    # 设置测试环境变量
    monkeypatch.setenv("TESTING", "true")
    monkeypatch.setenv("DATABASE_URL", SQLALCHEMY_DATABASE_URL)
    yield


# 自定义标记
@pytest.fixture
def api_test():
    """标记 API 测试"""
    pass


@pytest.fixture
def model_test():
    """标记模型测试"""
    pass


@pytest.fixture
def service_test():
    """标记服务测试"""
    pass


@pytest.fixture
def integration_test():
    """标记集成测试"""
    pass


@pytest.fixture
def performance_test():
    """标记性能测试"""
    pass


@pytest.fixture
def security_test():
    """标记安全测试"""
    pass
