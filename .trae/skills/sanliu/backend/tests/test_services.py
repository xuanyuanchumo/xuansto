"""
服务层单元测试

测试核心服务类的功能，包括 BaseCRUDService、StatusValidator、PaginationHelper 等
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from sqlalchemy.orm import Session
from fastapi import HTTPException
from pydantic import BaseModel

from app.services.base_crud import BaseCRUDService, StatusValidator, PaginationHelper
from app.models.project import Project, ProjectStatus
from app.models.task import Task, TaskStatus, TaskPriority
from app.models.agent import Agent


class TestProjectCreate(BaseModel):
    name: str
    description: str = ""


class TestProjectUpdate(BaseModel):
    name: str | None = None
    description: str | None = None


@pytest.mark.unit
@pytest.mark.services
class TestBaseCRUDService:
    """测试 BaseCRUDService 基类"""

    def test_get_by_id(self, db_session: Session):
        """测试根据ID获取实体"""
        project = Project(name="测试项目", description="描述")
        db_session.add(project)
        db_session.commit()

        service = BaseCRUDService[Project, TestProjectCreate, TestProjectUpdate](Project)
        result = service.get(db_session, project.id)

        assert result is not None
        assert result.name == "测试项目"

    def test_get_by_id_not_found(self, db_session: Session):
        """测试获取不存在的实体"""
        service = BaseCRUDService[Project, TestProjectCreate, TestProjectUpdate](Project)
        result = service.get(db_session, 99999)

        assert result is None

    def test_get_or_404_success(self, db_session: Session):
        """测试获取实体或抛出404 - 成功"""
        project = Project(name="测试项目")
        db_session.add(project)
        db_session.commit()

        service = BaseCRUDService[Project, TestProjectCreate, TestProjectUpdate](Project)
        result = service.get_or_404(db_session, project.id, "Project")

        assert result.id == project.id

    def test_get_or_404_not_found(self, db_session: Session):
        """测试获取实体或抛出404 - 未找到"""
        service = BaseCRUDService[Project, TestProjectCreate, TestProjectUpdate](Project)

        with pytest.raises(HTTPException) as exc_info:
            service.get_or_404(db_session, 99999, "Project")

        assert exc_info.value.status_code == 404
        assert "Project not found" in exc_info.value.detail

    def test_get_multi_no_filters(self, db_session: Session):
        """测试获取多个实体 - 无筛选"""
        for i in range(5):
            project = Project(name=f"项目{i}")
            db_session.add(project)
        db_session.commit()

        service = BaseCRUDService[Project, TestProjectCreate, TestProjectUpdate](Project)
        results = service.get_multi(db_session, skip=0, limit=10)

        assert len(results) == 5

    def test_get_multi_with_pagination(self, db_session: Session):
        """测试获取多个实体 - 分页"""
        for i in range(15):
            project = Project(name=f"项目{i}")
            db_session.add(project)
        db_session.commit()

        service = BaseCRUDService[Project, TestProjectCreate, TestProjectUpdate](Project)
        results = service.get_multi(db_session, skip=5, limit=5)

        assert len(results) == 5

    def test_get_multi_with_filters(self, db_session: Session):
        """测试获取多个实体 - 带筛选"""
        project1 = Project(name="项目1", status=ProjectStatus.DESIGN.value)
        project2 = Project(name="项目2", status=ProjectStatus.DEVELOPMENT.value)
        project3 = Project(name="项目3", status=ProjectStatus.DESIGN.value)
        db_session.add_all([project1, project2, project3])
        db_session.commit()

        service = BaseCRUDService[Project, TestProjectCreate, TestProjectUpdate](Project)
        results = service.get_multi(
            db_session,
            filters={"status": ProjectStatus.DESIGN.value}
        )

        assert len(results) == 2

    def test_get_all(self, db_session: Session):
        """测试获取所有实体"""
        for i in range(3):
            project = Project(name=f"项目{i}")
            db_session.add(project)
        db_session.commit()

        service = BaseCRUDService[Project, TestProjectCreate, TestProjectUpdate](Project)
        results = service.get_all(db_session)

        assert len(results) == 3

    def test_create(self, db_session: Session):
        """测试创建实体"""
        service = BaseCRUDService[Project, TestProjectCreate, TestProjectUpdate](Project)
        obj_in = TestProjectCreate(name="新项目", description="新项目描述")

        result = service.create(db_session, obj_in)

        assert result.id is not None
        assert result.name == "新项目"
        assert result.description == "新项目描述"

    def test_update(self, db_session: Session):
        """测试更新实体"""
        project = Project(name="原名称", description="原描述")
        db_session.add(project)
        db_session.commit()

        service = BaseCRUDService[Project, TestProjectCreate, TestProjectUpdate](Project)
        obj_in = TestProjectUpdate(name="新名称")

        result = service.update(db_session, project, obj_in)

        assert result.name == "新名称"
        assert result.description == "原描述"

    def test_update_partial(self, db_session: Session):
        """测试部分更新实体"""
        project = Project(name="原名称", description="原描述")
        db_session.add(project)
        db_session.commit()

        service = BaseCRUDService[Project, TestProjectCreate, TestProjectUpdate](Project)
        obj_in = TestProjectUpdate(description="新描述")

        result = service.update(db_session, project, obj_in)

        assert result.name == "原名称"
        assert result.description == "新描述"

    def test_delete_success(self, db_session: Session):
        """测试删除实体 - 成功"""
        project = Project(name="待删除项目")
        db_session.add(project)
        db_session.commit()
        project_id = project.id

        service = BaseCRUDService[Project, TestProjectCreate, TestProjectUpdate](Project)
        result = service.delete(db_session, project_id)

        assert result is True
        assert db_session.query(Project).filter_by(id=project_id).first() is None

    def test_delete_not_found(self, db_session: Session):
        """测试删除实体 - 未找到"""
        service = BaseCRUDService[Project, TestProjectCreate, TestProjectUpdate](Project)
        result = service.delete(db_session, 99999)

        assert result is False

    def test_count_no_filters(self, db_session: Session):
        """测试计数 - 无筛选"""
        for i in range(5):
            project = Project(name=f"项目{i}")
            db_session.add(project)
        db_session.commit()

        service = BaseCRUDService[Project, TestProjectCreate, TestProjectUpdate](Project)
        count = service.count(db_session)

        assert count == 5

    def test_count_with_filters(self, db_session: Session):
        """测试计数 - 带筛选"""
        project1 = Project(name="项目1", status=ProjectStatus.DESIGN.value)
        project2 = Project(name="项目2", status=ProjectStatus.DEVELOPMENT.value)
        db_session.add_all([project1, project2])
        db_session.commit()

        service = BaseCRUDService[Project, TestProjectCreate, TestProjectUpdate](Project)
        count = service.count(db_session, filters={"status": ProjectStatus.DESIGN.value})

        assert count == 1

    def test_exists_by_name_true(self, db_session: Session):
        """测试名称存在检查 - 存在"""
        project = Project(name="唯一名称")
        db_session.add(project)
        db_session.commit()

        service = BaseCRUDService[Project, TestProjectCreate, TestProjectUpdate](Project)
        result = service.exists_by_name(db_session, "唯一名称")

        assert result is True

    def test_exists_by_name_false(self, db_session: Session):
        """测试名称存在检查 - 不存在"""
        service = BaseCRUDService[Project, TestProjectCreate, TestProjectUpdate](Project)
        result = service.exists_by_name(db_session, "不存在的名称")

        assert result is False

    def test_exists_by_name_exclude_self(self, db_session: Session):
        """测试名称存在检查 - 排除自身"""
        project = Project(name="唯一名称")
        db_session.add(project)
        db_session.commit()

        service = BaseCRUDService[Project, TestProjectCreate, TestProjectUpdate](Project)
        result = service.exists_by_name(db_session, "唯一名称", exclude_id=project.id)

        assert result is False

    def test_check_unique_name_conflict(self, db_session: Session):
        """测试唯一名称检查 - 冲突"""
        project = Project(name="已存在名称")
        db_session.add(project)
        db_session.commit()

        service = BaseCRUDService[Project, TestProjectCreate, TestProjectUpdate](Project)

        with pytest.raises(HTTPException) as exc_info:
            service.check_unique_name(db_session, "已存在名称", "Project")

        assert exc_info.value.status_code == 409

    def test_check_unique_name_no_conflict(self, db_session: Session):
        """测试唯一名称检查 - 无冲突"""
        service = BaseCRUDService[Project, TestProjectCreate, TestProjectUpdate](Project)
        service.check_unique_name(db_session, "不存在的名称", "Project")


@pytest.mark.unit
@pytest.mark.services
class TestStatusValidator:
    """测试状态验证器"""

    def test_validate_valid_status(self):
        """测试验证有效状态"""
        validator = StatusValidator(["pending", "running", "completed"])
        validator.validate("pending")

    def test_validate_invalid_status(self):
        """测试验证无效状态"""
        validator = StatusValidator(["pending", "running", "completed"])

        with pytest.raises(HTTPException) as exc_info:
            validator.validate("invalid_status")

        assert exc_info.value.status_code == 400
        assert "Invalid status" in exc_info.value.detail

    def test_validate_custom_field_name(self):
        """测试自定义字段名"""
        validator = StatusValidator(["active", "inactive"])

        with pytest.raises(HTTPException) as exc_info:
            validator.validate("unknown", "agent_status")

        assert "Invalid agent_status" in exc_info.value.detail


@pytest.mark.unit
@pytest.mark.services
class TestPaginationHelper:
    """测试分页辅助类"""

    def test_calculate_offset_first_page(self):
        """测试计算偏移量 - 第一页"""
        offset = PaginationHelper.calculate_offset(page=1, page_size=10)
        assert offset == 0

    def test_calculate_offset_second_page(self):
        """测试计算偏移量 - 第二页"""
        offset = PaginationHelper.calculate_offset(page=2, page_size=10)
        assert offset == 10

    def test_calculate_offset_large_page(self):
        """测试计算偏移量 - 大页码"""
        offset = PaginationHelper.calculate_offset(page=100, page_size=20)
        assert offset == 1980

    def test_calculate_total_pages_exact(self):
        """测试计算总页数 - 整除"""
        total_pages = PaginationHelper.calculate_total_pages(total=100, page_size=10)
        assert total_pages == 10

    def test_calculate_total_pages_with_remainder(self):
        """测试计算总页数 - 有余数"""
        total_pages = PaginationHelper.calculate_total_pages(total=95, page_size=10)
        assert total_pages == 10

    def test_calculate_total_pages_zero(self):
        """测试计算总页数 - 零条目"""
        total_pages = PaginationHelper.calculate_total_pages(total=0, page_size=10)
        assert total_pages == 0

    def test_calculate_total_pages_single_page(self):
        """测试计算总页数 - 单页"""
        total_pages = PaginationHelper.calculate_total_pages(total=5, page_size=10)
        assert total_pages == 1

    def test_get_paginated_result(self):
        """测试获取分页结果"""
        items = [{"id": 1}, {"id": 2}, {"id": 3}]
        result = PaginationHelper.get_paginated_result(
            items=items,
            total=100,
            page=2,
            page_size=10
        )

        assert result["items"] == items
        assert result["total"] == 100
        assert result["page"] == 2
        assert result["page_size"] == 10
        assert result["total_pages"] == 10


@pytest.mark.unit
@pytest.mark.services
class TestCacheService:
    """测试缓存服务"""

    def test_cache_get_hit(self, mock_redis):
        """测试缓存命中"""
        mock_redis.get_json.return_value = {"key": "value"}

        result = mock_redis.get_json("test_key")

        assert result == {"key": "value"}
        mock_redis.get_json.assert_called_once_with("test_key")

    def test_cache_get_miss(self, mock_redis):
        """测试缓存未命中"""
        mock_redis.get_json.return_value = None

        result = mock_redis.get_json("nonexistent_key")

        assert result is None

    def test_cache_set(self, mock_redis):
        """测试缓存设置"""
        mock_redis.set_json.return_value = True

        result = mock_redis.set_json("test_key", {"data": "value"}, ttl=300)

        assert result is True

    def test_cache_delete(self, mock_redis):
        """测试缓存删除"""
        mock_redis.delete.return_value = 1

        result = mock_redis.delete("test_key")

        assert result == 1

    def test_cache_exists_true(self, mock_redis):
        """测试缓存存在检查 - 存在"""
        mock_redis.exists.return_value = 1

        result = mock_redis.exists("test_key")

        assert result == 1

    def test_cache_exists_false(self, mock_redis):
        """测试缓存存在检查 - 不存在"""
        mock_redis.exists.return_value = 0

        result = mock_redis.exists("nonexistent_key")

        assert result == 0

    def test_cache_expire(self, mock_redis):
        """测试缓存过期设置"""
        mock_redis.expire.return_value = True

        result = mock_redis.expire("test_key", 600)

        assert result is True

    def test_cache_ttl(self, mock_redis):
        """测试缓存TTL获取"""
        mock_redis.ttl.return_value = 300

        result = mock_redis.ttl("test_key")

        assert result == 300


@pytest.mark.unit
@pytest.mark.services
class TestPerformanceService:
    """测试性能服务"""

    def test_performance_stats_structure(self, client):
        """测试性能统计结构"""
        response = client.get("/performance/stats")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)

    def test_performance_timing(self, client):
        """测试性能计时"""
        import time

        start_time = time.time()
        response = client.get("/health")
        end_time = time.time()

        assert response.status_code == 200
        assert end_time - start_time < 5.0