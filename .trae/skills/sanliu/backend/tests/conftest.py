"""
Backend 测试配置和 Fixtures

提供后端测试所需的配置和 fixtures
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from unittest.mock import Mock, MagicMock

# 导入应用
from app.main import app
from app.models.base import Base, get_db
from app.models.project import Project
from app.models.task import Task
from app.models.agent import Agent
from app.models.skill_call import SkillCall
from app.models.assignment import Assignment
from app.models.department import Department


# 测试数据库配置 - 使用内存数据库以提高性能和隔离性
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db_engine():
    """创建测试数据库引擎"""
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def db_session(db_engine):
    """创建测试数据库会话"""
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture(scope="function")
def client(db_session):
    """创建测试客户端
    
    确保每个测试都有独立的客户端实例，并正确覆盖数据库依赖
    """
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    
    try:
        with TestClient(app, raise_server_exceptions=False) as test_client:
            yield test_client
    finally:
        app.dependency_overrides.clear()


@pytest.fixture(scope="function")
def mock_redis():
    """创建 Mock Redis 客户端"""
    mock = Mock()
    mock.get_json.return_value = None
    mock.set_json.return_value = True
    mock.delete.return_value = True
    mock.exists.return_value = False
    mock.get.return_value = None
    mock.set.return_value = True
    mock.expire.return_value = True
    mock.ttl.return_value = 300
    return mock


@pytest.fixture(scope="function")
def mock_celery():
    """创建 Mock Celery 应用"""
    mock = Mock()
    mock.send_task.return_value = Mock(id="task_id_123")
    mock.AsyncResult.return_value = Mock(
        state="SUCCESS",
        result={"status": "completed"}
    )
    return mock


@pytest.fixture(scope="function")
def mock_external_services():
    """创建 Mock 外部服务（如LLM、文件系统等）"""
    mock = Mock()
    mock.llm_client = Mock()
    mock.llm_client.generate.return_value = "Mock LLM response"
    mock.llm_client.embed.return_value = [0.1] * 768
    
    mock.file_storage = Mock()
    mock.file_storage.upload.return_value = "mock_file_path"
    mock.file_storage.download.return_value = b"mock file content"
    mock.file_storage.delete.return_value = True
    
    mock.email_service = Mock()
    mock.email_service.send.return_value = True
    
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
        "status": kwargs.get("status", "assigned"),
        "task_description": kwargs.get("task_description", "测试任务描述")
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


@pytest.fixture
def sample_assignment_data():
    """提供示例 Assignment 数据"""
    return {
        "status": "assigned"
    }


@pytest.fixture
def sample_department_data():
    """提供示例部门数据"""
    return {
        "name": "Engineering",
        "description": "Engineering Department"
    }


# 标记 fixtures
@pytest.fixture(autouse=True)
def setup_test_environment(monkeypatch):
    """设置测试环境
    
    自动配置测试所需的环境变量和设置
    """
    monkeypatch.setenv("TESTING", "true")
    monkeypatch.setenv("DATABASE_URL", SQLALCHEMY_DATABASE_URL)
    monkeypatch.setenv("REDIS_URL", "redis://localhost:6379/1")
    monkeypatch.setenv("SECRET_KEY", "test_secret_key_for_testing_only")
    monkeypatch.setenv("ENVIRONMENT", "test")
    monkeypatch.setenv("LOG_LEVEL", "DEBUG")
    monkeypatch.setenv("CORS_ORIGINS", "*")
    
    import logging
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    
    yield
    
    logging.getLogger("sqlalchemy.engine").setLevel(logging.INFO)
    logging.getLogger("uvicorn.access").setLevel(logging.INFO)


@pytest.fixture(scope="function")
def clean_db(db_session):
    """确保数据库会话在测试前后都是干净的
    
    提供更强的隔离保证，确保每个测试都从干净的状态开始
    """
    from sqlalchemy import text
    
    for table in reversed(Base.metadata.sorted_tables):
        db_session.execute(text(f"DELETE FROM {table.name}"))
    db_session.commit()
    
    yield db_session
    
    db_session.rollback()
    
    for table in reversed(Base.metadata.sorted_tables):
        db_session.execute(text(f"DELETE FROM {table.name}"))
    db_session.commit()


@pytest.fixture(scope="function")
def test_data_factory(db_session):
    """测试数据工厂fixture
    
    提供统一的数据创建接口，自动跟踪和清理创建的对象
    """
    created_objects = []
    
    def factory(model_class, **kwargs):
        obj = model_class(**kwargs)
        db_session.add(obj)
        db_session.commit()
        db_session.refresh(obj)
        created_objects.append((model_class, obj.id))
        return obj
    
    yield factory
    
    for model_class, obj_id in reversed(created_objects):
        try:
            obj = db_session.query(model_class).filter_by(id=obj_id).first()
            if obj:
                db_session.delete(obj)
                db_session.commit()
        except Exception:
            db_session.rollback()


@pytest.fixture(scope="function")
def isolated_test_environment(db_session, mock_redis, mock_celery, mock_external_services):
    """隔离的测试环境
    
    提供完全隔离的测试环境，包括数据库、缓存、外部服务等
    """
    from sqlalchemy import text
    
    for table in reversed(Base.metadata.sorted_tables):
        db_session.execute(text(f"DELETE FROM {table.name}"))
    db_session.commit()
    
    mock_redis.reset_mock()
    mock_celery.reset_mock()
    
    environment = {
        "db_session": db_session,
        "redis": mock_redis,
        "celery": mock_celery,
        "external_services": mock_external_services,
        "created_objects": []
    }
    
    yield environment
    
    db_session.rollback()
    
    for table in reversed(Base.metadata.sorted_tables):
        db_session.execute(text(f"DELETE FROM {table.name}"))
    db_session.commit()


@pytest.fixture(scope="function")
def api_client_headers():
    """API客户端默认headers"""
    return {
        "Content-Type": "application/json",
        "Accept": "application/json"
    }


@pytest.fixture(scope="function")
def test_context():
    """测试上下文，用于存储测试过程中的临时数据"""
    context = {}
    yield context
    context.clear()


@pytest.fixture(autouse=True)
def cleanup_test_files():
    """自动清理测试生成的文件
    
    提供文件注册机制，自动清理测试过程中创建的临时文件
    """
    import tempfile
    import os
    
    temp_files = []
    temp_dirs = []
    
    def register_temp_file(filepath):
        """注册临时文件，测试结束后自动删除"""
        temp_files.append(filepath)
        return filepath
    
    def register_temp_dir(dirpath):
        """注册临时目录，测试结束后自动删除"""
        temp_dirs.append(dirpath)
        return dirpath
    
    def create_temp_file(suffix="", content=""):
        """创建临时文件"""
        fd, filepath = tempfile.mkstemp(suffix=suffix)
        if content:
            with os.fdopen(fd, 'w') as f:
                f.write(content)
        else:
            os.close(fd)
        temp_files.append(filepath)
        return filepath
    
    def create_temp_dir(prefix="test_"):
        """创建临时目录"""
        dirpath = tempfile.mkdtemp(prefix=prefix)
        temp_dirs.append(dirpath)
        return dirpath
    
    cleanup_helper = Mock()
    cleanup_helper.register_temp_file = register_temp_file
    cleanup_helper.register_temp_dir = register_temp_dir
    cleanup_helper.create_temp_file = create_temp_file
    cleanup_helper.create_temp_dir = create_temp_dir
    
    yield cleanup_helper
    
    for filepath in temp_files:
        try:
            if os.path.exists(filepath):
                os.remove(filepath)
        except Exception:
            pass
    
    for dirpath in temp_dirs:
        try:
            if os.path.exists(dirpath):
                import shutil
                shutil.rmtree(dirpath)
        except Exception:
            pass


class BaseE2ETest:
    """E2E测试基类，提供统一的测试环境和fixture管理
    
    使用方法：
        class TestMyFeature(BaseE2ETest):
            def test_something(self):
                response = self.client.get("/api/endpoint")
                assert response.status_code == 200
    """
    
    @pytest.fixture(autouse=True)
    def setup_e2e_test(self, client, db_session, mock_redis, mock_celery, mock_external_services):
        """自动设置E2E测试环境"""
        self.client = client
        self.db_session = db_session
        self.mock_redis = mock_redis
        self.mock_celery = mock_celery
        self.mock_external_services = mock_external_services
        self._test_data = []
        self._test_context = {}
        
        self._setup_test_specific_fixtures()
        
        yield
        
        self._cleanup_test_data()
        self._cleanup_test_context()
    
    def _setup_test_specific_fixtures(self):
        """设置测试特定的fixture，子类可以覆盖此方法"""
        pass
    
    def _cleanup_test_data(self):
        """清理测试数据"""
        for obj_type, obj_id in reversed(self._test_data):
            try:
                if obj_type == 'project':
                    obj = self.db_session.query(Project).filter_by(id=obj_id).first()
                elif obj_type == 'task':
                    obj = self.db_session.query(Task).filter_by(id=obj_id).first()
                elif obj_type == 'agent':
                    obj = self.db_session.query(Agent).filter_by(id=obj_id).first()
                elif obj_type == 'skill_call':
                    obj = self.db_session.query(SkillCall).filter_by(id=obj_id).first()
                elif obj_type == 'assignment':
                    obj = self.db_session.query(Assignment).filter_by(id=obj_id).first()
                elif obj_type == 'department':
                    obj = self.db_session.query(Department).filter_by(id=obj_id).first()
                else:
                    continue
                
                if obj:
                    self.db_session.delete(obj)
                    self.db_session.commit()
            except Exception:
                self.db_session.rollback()
        
        self._test_data.clear()
    
    def _cleanup_test_context(self):
        """清理测试上下文"""
        self._test_context.clear()
    
    def create_test_project(self, **kwargs):
        """创建测试项目的便捷方法"""
        project = create_test_project(self.db_session, **kwargs)
        self._test_data.append(('project', project.id))
        return project
    
    def create_test_task(self, **kwargs):
        """创建测试任务的便捷方法"""
        task = create_test_task(self.db_session, **kwargs)
        self._test_data.append(('task', task.id))
        return task
    
    def create_test_agent(self, **kwargs):
        """创建测试代理的便捷方法"""
        agent = create_test_agent(self.db_session, **kwargs)
        self._test_data.append(('agent', agent.id))
        return agent
    
    def create_test_skill_call(self, **kwargs):
        """创建测试技能调用的便捷方法"""
        call = create_test_skill_call(self.db_session, **kwargs)
        self._test_data.append(('skill_call', call.id))
        return call
    
    def create_test_assignment(self, **kwargs):
        """创建测试分配的便捷方法"""
        assignment = create_test_assignment(self.db_session, **kwargs)
        self._test_data.append(('assignment', assignment.id))
        return assignment
    
    def create_test_department(self, **kwargs):
        """创建测试部门的便捷方法"""
        department = create_test_department(self.db_session, **kwargs)
        self._test_data.append(('department', department.id))
        return department
    
    def assert_response_ok(self, response, expected_status=200):
        """断言响应成功的辅助方法"""
        assert response.status_code == expected_status, \
            f"Expected status {expected_status}, got {response.status_code}. Response: {response.text}"
        return response.json()
    
    def assert_response_error(self, response, expected_status=400):
        """断言响应错误的辅助方法"""
        assert response.status_code == expected_status, \
            f"Expected status {expected_status}, got {response.status_code}. Response: {response.text}"
        return response.json()


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


# Pytest Hooks
def pytest_configure(config):
    """配置pytest，注册自定义标记"""
    config.addinivalue_line(
        "markers", "api: mark test as an API test"
    )
    config.addinivalue_line(
        "markers", "integration: mark test as an integration test"
    )
    config.addinivalue_line(
        "markers", "unit: mark test as a unit test"
    )
    config.addinivalue_line(
        "markers", "performance: mark test as a performance test"
    )
    config.addinivalue_line(
        "markers", "benchmark: mark test as a benchmark test"
    )
    config.addinivalue_line(
        "markers", "security: mark test as a security test"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )
    config.addinivalue_line(
        "markers", "e2e: mark test as end-to-end test"
    )
    config.addinivalue_line(
        "markers", "models: mark test as a model test"
    )
    config.addinivalue_line(
        "markers", "database: mark test as a database test"
    )
    config.addinivalue_line(
        "markers", "regression: mark test as a regression test"
    )
    config.addinivalue_line(
        "markers", "services: mark test as a services test"
    )


def pytest_collection_modifyitems(config, items):
    """修改测试集合，自动添加标记"""
    for item in items:
        if "api" in item.nodeid:
            item.add_marker(pytest.mark.api)
        if "integration" in item.nodeid:
            item.add_marker(pytest.mark.integration)
        if "benchmark" in item.nodeid:
            item.add_marker(pytest.mark.benchmark)
            item.add_marker(pytest.mark.slow)


def pytest_runtest_setup(item):
    """测试运行前的设置"""
    if "slow" in item.keywords and not item.config.getoption("--runslow", default=False):
        pytest.skip("need --runslow option to run")


def pytest_report_header(config):
    """在测试报告中添加自定义头部信息"""
    return [
        "Backend Test Configuration",
        f"Database: {SQLALCHEMY_DATABASE_URL}",
        "Test Environment: Isolated",
    ]
