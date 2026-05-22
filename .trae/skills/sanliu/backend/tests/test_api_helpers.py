"""
API辅助服务单元测试

测试 APIResponseBuilder、StatsCalculator、EntityValidator、SearchHelper、CacheHelper 等类
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from sqlalchemy.orm import Session
from fastapi import HTTPException

from app.services.api_helpers import (
    APIResponseBuilder,
    StatsCalculator,
    EntityValidator,
    SearchHelper,
    CacheHelper,
    ListResponse
)
from app.models.project import Project, ProjectStatus
from app.models.task import Task, TaskStatus


@pytest.mark.unit
@pytest.mark.services
class TestAPIResponseBuilder:
    """测试 APIResponseBuilder 类"""

    def test_success_with_data(self):
        """测试成功响应 - 带数据"""
        data = {"id": 1, "name": "测试"}
        result = APIResponseBuilder.success(data, "操作成功")

        assert result["success"] is True
        assert result["message"] == "操作成功"
        assert result["data"] == data

    def test_success_without_data(self):
        """测试成功响应 - 无数据"""
        result = APIResponseBuilder.success()

        assert result["success"] is True
        assert result["message"] == "Success"
        assert result["data"] is None

    def test_success_with_custom_message(self):
        """测试成功响应 - 自定义消息"""
        result = APIResponseBuilder.success(message="创建成功")

        assert result["success"] is True
        assert result["message"] == "创建成功"

    def test_error_default_code(self):
        """测试错误响应 - 默认错误码"""
        result = APIResponseBuilder.error("操作失败")

        assert result["success"] is False
        assert result["message"] == "操作失败"
        assert result["error_code"] == 400

    def test_error_custom_code(self):
        """测试错误响应 - 自定义错误码"""
        result = APIResponseBuilder.error("资源未找到", code=404)

        assert result["success"] is False
        assert result["message"] == "资源未找到"
        assert result["error_code"] == 404

    def test_deleted(self):
        """测试删除响应"""
        result = APIResponseBuilder.deleted("Project", 123)

        assert result["message"] == "Project deleted successfully"
        assert result["id"] == 123


@pytest.mark.unit
@pytest.mark.services
class TestStatsCalculator:
    """测试 StatsCalculator 类"""

    def test_get_status_distribution_no_filters(self, db_session: Session):
        """测试状态分布计算 - 无筛选"""
        project1 = Project(name="项目1", status=ProjectStatus.REQUIREMENT.value)
        project2 = Project(name="项目2", status=ProjectStatus.DEVELOPMENT.value)
        project3 = Project(name="项目3", status=ProjectStatus.REQUIREMENT.value)
        db_session.add_all([project1, project2, project3])
        db_session.commit()

        result = StatsCalculator.get_status_distribution(
            db_session, Project, "status"
        )

        assert result[ProjectStatus.REQUIREMENT.value] == 2
        assert result[ProjectStatus.DEVELOPMENT.value] == 1

    def test_get_status_distribution_with_filters(self, db_session: Session):
        """测试状态分布计算 - 带筛选"""
        from app.models.task import TaskPriority

        project = Project(name="测试项目")
        db_session.add(project)
        db_session.commit()

        task1 = Task(title="任务1", project_id=project.id, status=TaskStatus.COMPLETED.value, priority=TaskPriority.HIGH.value)
        task2 = Task(title="任务2", project_id=project.id, status=TaskStatus.PENDING.value, priority=TaskPriority.HIGH.value)
        task3 = Task(title="任务3", project_id=project.id, status=TaskStatus.COMPLETED.value, priority=TaskPriority.LOW.value)
        db_session.add_all([task1, task2, task3])
        db_session.commit()

        result = StatsCalculator.get_status_distribution(
            db_session, Task, "status", filters={"priority": TaskPriority.HIGH.value}
        )

        assert TaskStatus.COMPLETED.value in result
        assert TaskStatus.PENDING.value in result

    def test_calculate_percentage_normal(self):
        """测试百分比计算 - 正常"""
        result = StatsCalculator.calculate_percentage(25, 100)
        assert result == 25.0

    def test_calculate_percentage_zero_total(self):
        """测试百分比计算 - 总数为零"""
        result = StatsCalculator.calculate_percentage(25, 0)
        assert result == 0.0

    def test_calculate_percentage_decimal(self):
        """测试百分比计算 - 小数结果"""
        result = StatsCalculator.calculate_percentage(1, 3)
        assert result == pytest.approx(33.33, rel=0.01)

    def test_get_average_no_filters(self, db_session: Session):
        """测试平均值计算 - 无筛选"""
        project = Project(name="测试项目")
        db_session.add(project)
        db_session.commit()

        task1 = Task(title="任务1", project_id=project.id, estimated_hours=5.0)
        task2 = Task(title="任务2", project_id=project.id, estimated_hours=10.0)
        task3 = Task(title="任务3", project_id=project.id, estimated_hours=15.0)
        db_session.add_all([task1, task2, task3])
        db_session.commit()

        result = StatsCalculator.get_average(db_session, Task, "estimated_hours")

        assert result == 10.0

    def test_get_average_with_filters(self, db_session: Session):
        """测试平均值计算 - 带筛选"""
        from app.models.task import TaskPriority

        project = Project(name="测试项目")
        db_session.add(project)
        db_session.commit()

        task1 = Task(title="任务1", project_id=project.id, estimated_hours=5.0, priority=TaskPriority.HIGH.value)
        task2 = Task(title="任务2", project_id=project.id, estimated_hours=10.0, priority=TaskPriority.LOW.value)
        db_session.add_all([task1, task2])
        db_session.commit()

        result = StatsCalculator.get_average(
            db_session, Task, "estimated_hours",
            filters={"priority": TaskPriority.HIGH.value}
        )

        assert result == 5.0

    def test_get_average_empty_table(self, db_session: Session):
        """测试平均值计算 - 空表"""
        result = StatsCalculator.get_average(db_session, Task, "estimated_hours")
        assert result is None


@pytest.mark.unit
@pytest.mark.services
class TestEntityValidator:
    """测试 EntityValidator 类"""

    def test_check_exists_found(self, db_session: Session):
        """测试实体存在检查 - 存在"""
        project = Project(name="测试项目")
        db_session.add(project)
        db_session.commit()

        result = EntityValidator.check_exists(db_session, Project, project.id, "Project")

        assert result.id == project.id
        assert result.name == "测试项目"

    def test_check_exists_not_found(self, db_session: Session):
        """测试实体存在检查 - 不存在"""
        with pytest.raises(HTTPException) as exc_info:
            EntityValidator.check_exists(db_session, Project, 99999, "Project")

        assert exc_info.value.status_code == 404
        assert "Project not found" in exc_info.value.detail

    def test_check_not_exists_available(self, db_session: Session):
        """测试实体不存在检查 - 可用"""
        EntityValidator.check_not_exists(db_session, Project, "name", "不存在的名称", "Project")

    def test_check_not_exists_conflict(self, db_session: Session):
        """测试实体不存在检查 - 冲突"""
        project = Project(name="已存在名称")
        db_session.add(project)
        db_session.commit()

        with pytest.raises(HTTPException) as exc_info:
            EntityValidator.check_not_exists(db_session, Project, "name", "已存在名称", "Project")

        assert exc_info.value.status_code == 409
        assert "already exists" in exc_info.value.detail


@pytest.mark.unit
@pytest.mark.services
class TestSearchHelper:
    """测试 SearchHelper 类"""

    def test_build_search_query_single_field(self, db_session: Session):
        """测试搜索查询构建 - 单字段"""
        project1 = Project(name="Python项目", description="描述1")
        project2 = Project(name="Java项目", description="描述2")
        db_session.add_all([project1, project2])
        db_session.commit()

        query = SearchHelper.build_search_query(
            db_session, Project, ["name"], "Python"
        )
        results = query.all()

        assert len(results) == 1
        assert results[0].name == "Python项目"

    def test_build_search_query_multiple_fields(self, db_session: Session):
        """测试搜索查询构建 - 多字段"""
        project1 = Project(name="项目1", description="Python开发")
        project2 = Project(name="Python项目", description="描述2")
        project3 = Project(name="项目3", description="Java开发")
        db_session.add_all([project1, project2, project3])
        db_session.commit()

        query = SearchHelper.build_search_query(
            db_session, Project, ["name", "description"], "Python"
        )
        results = query.all()

        assert len(results) == 2

    def test_build_search_query_no_match(self, db_session: Session):
        """测试搜索查询构建 - 无匹配"""
        project = Project(name="项目1", description="描述1")
        db_session.add(project)
        db_session.commit()

        query = SearchHelper.build_search_query(
            db_session, Project, ["name", "description"], "不存在的关键词"
        )
        results = query.all()

        assert len(results) == 0

    def test_build_search_query_case_insensitive(self, db_session: Session):
        """测试搜索查询构建 - 不区分大小写"""
        project = Project(name="PYTHON项目", description="描述")
        db_session.add(project)
        db_session.commit()

        query = SearchHelper.build_search_query(
            db_session, Project, ["name"], "python"
        )
        results = query.all()

        assert len(results) == 1

    def test_build_search_query_partial_match(self, db_session: Session):
        """测试搜索查询构建 - 部分匹配"""
        project = Project(name="我的Python项目", description="描述")
        db_session.add(project)
        db_session.commit()

        query = SearchHelper.build_search_query(
            db_session, Project, ["name"], "Python"
        )
        results = query.all()

        assert len(results) == 1


@pytest.mark.unit
@pytest.mark.services
class TestCacheHelper:
    """测试 CacheHelper 类"""

    def test_get_or_set_cache_hit(self):
        """测试缓存辅助 - 缓存命中"""
        mock_cache = Mock()
        mock_cache.get_json.return_value = {"cached": "data"}

        fetch_func = Mock(return_value={"fresh": "data"})
        result = CacheHelper.get_or_set(mock_cache, "test_key", fetch_func)

        assert result == {"cached": "data"}
        fetch_func.assert_not_called()

    def test_get_or_set_cache_miss(self):
        """测试缓存辅助 - 缓存未命中"""
        mock_cache = Mock()
        mock_cache.get_json.return_value = None
        mock_cache.set_json.return_value = True

        fetch_func = Mock(return_value={"fresh": "data"})
        result = CacheHelper.get_or_set(mock_cache, "test_key", fetch_func, ttl=120)

        assert result == {"fresh": "data"}
        fetch_func.assert_called_once()
        mock_cache.set_json.assert_called_once_with("test_key", {"fresh": "data"}, ttl=120)

    def test_get_or_set_empty_result(self):
        """测试缓存辅助 - 空结果"""
        mock_cache = Mock()
        mock_cache.get_json.return_value = None

        fetch_func = Mock(return_value=None)
        result = CacheHelper.get_or_set(mock_cache, "test_key", fetch_func)

        assert result is None


@pytest.mark.unit
@pytest.mark.services
class TestListResponse:
    """测试 ListResponse 模型"""

    def test_list_response_creation(self):
        """测试列表响应创建"""
        response = ListResponse(
            items=[{"id": 1}, {"id": 2}],
            total=100,
            page=2,
            page_size=10,
            total_pages=10
        )

        assert len(response.items) == 2
        assert response.total == 100
        assert response.page == 2
        assert response.page_size == 10
        assert response.total_pages == 10

    def test_list_response_model_config(self):
        """测试列表响应模型配置"""
        response = ListResponse(
            items=[],
            total=0,
            page=1,
            page_size=10,
            total_pages=0
        )

        assert hasattr(response, 'model_dump')
