"""
项目 API 测试

测试项目相关的 API 端点
"""

import pytest
from tests.conftest import create_test_project, create_test_task


@pytest.mark.api
@pytest.mark.integration
class TestProjectCreate:
    """测试项目创建 API"""

    def test_create_project_success(self, client, sample_project_data):
        """测试成功创建项目"""
        response = client.post("/api/projects/", json=sample_project_data)

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == sample_project_data["name"]
        assert data["description"] == sample_project_data["description"]
        assert data["tech_stack"] == sample_project_data["tech_stack"]
        assert data["status"] == "REQUIREMENT"
        assert "id" in data
        assert "created_at" in data

    def test_create_project_without_optional_fields(self, client):
        """测试使用最小数据创建项目"""
        minimal_data = {"name": "最小项目"}
        response = client.post("/api/projects/", json=minimal_data)

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "最小项目"
        assert data["description"] is None
        assert data["tech_stack"] is None

    def test_create_project_duplicate_name(self, client, sample_project_data, db_session):
        """测试创建同名项目应该失败"""
        # 先创建一个项目
        response1 = client.post("/api/projects/", json=sample_project_data)
        assert response1.status_code == 200

        # 尝试创建同名项目
        response2 = client.post("/api/projects/", json=sample_project_data)
        assert response2.status_code == 409
        assert "already exists" in response2.json()["detail"]

    def test_create_project_invalid_data(self, client):
        """测试使用无效数据创建项目"""
        # 空名称
        response = client.post("/api/projects/", json={"name": ""})
        assert response.status_code == 422

        # 名称过长
        response = client.post("/api/projects/", json={"name": "x" * 201})
        assert response.status_code == 422

    def test_create_project_missing_name(self, client):
        """测试缺少名称字段"""
        response = client.post("/api/projects/", json={"description": "没有名称"})
        assert response.status_code == 422

    def test_create_project_with_special_characters(self, client):
        """测试使用特殊字符创建项目"""
        project_data = {
            "name": "项目-123_测试",
            "description": "测试描述"
        }
        response = client.post("/api/projects/", json=project_data)
        assert response.status_code == 200

    def test_create_project_with_unicode(self, client):
        """测试使用 Unicode 字符创建项目"""
        project_data = {
            "name": "🚀 项目 日本語 한국어",
            "description": "国际化描述"
        }
        response = client.post("/api/projects/", json=project_data)
        assert response.status_code == 200


@pytest.mark.api
@pytest.mark.integration
class TestProjectList:
    """测试项目列表 API"""

    def test_list_projects_empty(self, client):
        """测试空项目列表"""
        response = client.get("/api/projects/")

        assert response.status_code == 200
        data = response.json()
        assert data["items"] == []
        assert data["total"] == 0
        assert data["page"] == 1
        assert data["page_size"] == 12
        assert data["total_pages"] == 0

    def test_list_projects_with_data(self, client, db_session, mock_redis):
        """测试有数据时的项目列表"""
        # 创建测试项目
        create_test_project(db_session, name="项目1")
        create_test_project(db_session, name="项目2")

        # 确保缓存返回 None，以便从数据库查询
        mock_redis.get_json.return_value = None

        response = client.get("/api/projects/")

        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 2
        assert data["total"] == 2
        assert data["total_pages"] == 1

    def test_list_projects_pagination(self, client, db_session, mock_redis):
        """测试项目列表分页"""
        # 创建多个项目
        for i in range(15):
            create_test_project(db_session, name=f"项目{i+1}")

        # 确保缓存返回 None，以便从数据库查询
        mock_redis.get_json.return_value = None

        # 第一页
        response = client.get("/api/projects/?page=1&page_size=10")
        data = response.json()
        assert len(data["items"]) == 10
        assert data["total"] == 15
        assert data["total_pages"] == 2

        # 第二页
        response = client.get("/api/projects/?page=2&page_size=10")
        data = response.json()
        assert len(data["items"]) == 5

    def test_list_projects_filter_by_status(self, client, db_session, mock_redis):
        """测试按状态筛选项目"""
        from app.models.project import ProjectStatus

        # 创建不同状态的项目
        create_test_project(db_session, name="项目1", status=ProjectStatus.REQUIREMENT.value)
        create_test_project(db_session, name="项目2", status=ProjectStatus.DEVELOPMENT.value)
        create_test_project(db_session, name="项目3", status=ProjectStatus.REQUIREMENT.value)

        # 确保缓存返回 None，以便从数据库查询
        mock_redis.get_json.return_value = None

        # 筛选 REQUIREMENT 状态
        response = client.get("/api/projects/?status=REQUIREMENT")
        data = response.json()
        assert data["total"] == 2
        for item in data["items"]:
            assert item["status"] == "REQUIREMENT"

    def test_list_projects_search(self, client, db_session, mock_redis):
        """测试搜索项目"""
        create_test_project(db_session, name="Python 项目", description="关于 Python")
        create_test_project(db_session, name="Java 项目", description="关于 Java")
        create_test_project(db_session, name="另一个项目")

        # 确保缓存返回 None，以便从数据库查询
        mock_redis.get_json.return_value = None

        # 搜索 Python
        response = client.get("/api/projects/?search=Python")
        data = response.json()
        assert data["total"] >= 1

        # 搜索 Java
        response = client.get("/api/projects/?search=Java")
        data = response.json()
        assert data["total"] >= 1

    def test_list_projects_sorting(self, client, db_session, mock_redis):
        """测试项目列表排序"""
        create_test_project(db_session, name="项目A")
        create_test_project(db_session, name="项目B")

        mock_redis.get_json.return_value = None

        # 按名称升序
        response = client.get("/api/projects/?sort_by=name&sort_order=asc")
        data = response.json()
        assert response.status_code == 200

        # 按名称降序
        response = client.get("/api/projects/?sort_by=name&sort_order=desc")
        data = response.json()
        assert response.status_code == 200


@pytest.mark.api
@pytest.mark.integration
class TestProjectDetail:
    """测试项目详情 API"""

    def test_get_project_success(self, client, db_session):
        """测试成功获取项目详情"""
        project = create_test_project(db_session, name="测试项目")

        response = client.get(f"/api/projects/{project.id}")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == project.id
        assert data["name"] == "测试项目"

    def test_get_project_not_found(self, client):
        """测试获取不存在的项目"""
        response = client.get("/api/projects/99999")

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_get_project_with_tasks(self, client, db_session):
        """测试获取包含任务的项目详情"""
        project = create_test_project(db_session, name="测试项目")
        create_test_task(db_session, project_id=project.id, title="任务1")
        create_test_task(db_session, project_id=project.id, title="任务2")

        response = client.get(f"/api/projects/{project.id}")

        assert response.status_code == 200
        data = response.json()
        assert "task_stats" in data
        assert data["task_stats"]["total"] == 2

    def test_get_project_with_invalid_id(self, client):
        """测试使用无效 ID 获取项目"""
        response = client.get("/api/projects/invalid_id")
        assert response.status_code == 422


@pytest.mark.api
@pytest.mark.integration
class TestProjectUpdate:
    """测试项目更新 API"""

    def test_update_project_success(self, client, db_session):
        """测试成功更新项目"""
        project = create_test_project(db_session, name="旧名称")

        update_data = {
            "name": "新名称",
            "description": "新描述"
        }
        response = client.put(f"/api/projects/{project.id}", json=update_data)

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "新名称"
        assert data["description"] == "新描述"

    def test_update_project_not_found(self, client):
        """测试更新不存在的项目"""
        response = client.put("/api/projects/99999", json={"name": "新名称"})

        assert response.status_code == 404

    def test_update_project_duplicate_name(self, client, db_session):
        """测试更新项目时使用已存在的名称"""
        project1 = create_test_project(db_session, name="项目1")
        project2 = create_test_project(db_session, name="项目2")

        response = client.put(f"/api/projects/{project1.id}", json={"name": "项目2"})

        assert response.status_code == 409

    def test_update_project_status(self, client, db_session):
        """测试更新项目状态"""
        from app.models.project import ProjectStatus

        project = create_test_project(db_session, name="测试项目", status=ProjectStatus.REQUIREMENT.value)

        response = client.put(f"/api/projects/{project.id}", json={"status": "DESIGN"})

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "DESIGN"
        assert "status_history" in data

    def test_update_project_invalid_status(self, client, db_session):
        """测试更新为无效状态"""
        project = create_test_project(db_session, name="测试项目")

        response = client.put(f"/api/projects/{project.id}", json={"status": "INVALID_STATUS"})

        assert response.status_code == 400

    def test_update_project_tech_stack(self, client, db_session):
        """测试更新项目技术栈"""
        project = create_test_project(db_session, name="测试项目", tech_stack=["Python"])

        response = client.put(f"/api/projects/{project.id}", json={"tech_stack": ["Python", "React", "Node.js"]})

        assert response.status_code == 200
        data = response.json()
        assert data["tech_stack"] == ["Python", "React", "Node.js"]

    def test_update_project_partial(self, client, db_session):
        """测试部分更新项目"""
        project = create_test_project(db_session, name="测试项目", description="原描述")

        # 只更新描述
        response = client.put(f"/api/projects/{project.id}", json={"description": "新描述"})

        assert response.status_code == 200
        data = response.json()
        assert data["description"] == "新描述"
        assert data["name"] == "测试项目"  # 未改变


@pytest.mark.api
@pytest.mark.integration
class TestProjectDelete:
    """测试项目删除 API"""

    def test_delete_project_success(self, client, db_session):
        """测试成功删除项目"""
        project = create_test_project(db_session, name="待删除项目")

        response = client.delete(f"/api/projects/{project.id}")

        assert response.status_code == 200
        data = response.json()
        assert "deleted successfully" in data["message"]
        assert data["project_id"] == project.id

        # 验证项目已被删除
        get_response = client.get(f"/api/projects/{project.id}")
        assert get_response.status_code == 404

    def test_delete_project_not_found(self, client):
        """测试删除不存在的项目"""
        response = client.delete("/api/projects/99999")

        assert response.status_code == 404

    def test_delete_project_with_tasks(self, client, db_session):
        """测试删除包含任务的项目"""
        project = create_test_project(db_session, name="待删除项目")
        create_test_task(db_session, project_id=project.id, title="任务1")
        create_test_task(db_session, project_id=project.id, title="任务2")

        response = client.delete(f"/api/projects/{project.id}")

        assert response.status_code == 200
        data = response.json()
        assert data["deleted_tasks"] == 2


@pytest.mark.api
@pytest.mark.integration
class TestProjectStats:
    """测试项目统计 API"""

    def test_get_project_stats(self, client, db_session, mock_redis):
        """测试获取项目统计"""
        from app.models.task import TaskStatus

        project = create_test_project(db_session, name="统计测试项目")
        create_test_task(db_session, project_id=project.id, title="任务1", status=TaskStatus.COMPLETED.value)
        create_test_task(db_session, project_id=project.id, title="任务2", status=TaskStatus.PENDING.value)
        create_test_task(db_session, project_id=project.id, title="任务3", status=TaskStatus.IN_PROGRESS.value)

        # 确保缓存返回 None，以便从数据库查询
        mock_redis.get_json.return_value = None

        response = client.get(f"/api/projects/{project.id}/stats")

        assert response.status_code == 200
        data = response.json()
        assert data["project_id"] == project.id
        assert data["project_name"] == "统计测试项目"
        assert data["total_tasks"] == 3
        assert data["completed_tasks"] == 1
        assert data["pending_tasks"] == 1
        assert data["in_progress_tasks"] == 1
        assert "progress" in data

    def test_get_all_projects_stats(self, client, db_session, mock_redis):
        """测试获取所有项目统计"""
        from app.models.project import ProjectStatus

        create_test_project(db_session, name="项目1", status=ProjectStatus.REQUIREMENT.value)
        create_test_project(db_session, name="项目2", status=ProjectStatus.DEVELOPMENT.value)
        create_test_project(db_session, name="项目3", status=ProjectStatus.REQUIREMENT.value)

        # 确保缓存返回 None，以便从数据库查询
        mock_redis.get_json.return_value = None

        response = client.get("/api/projects/stats")

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 3
        assert "status_distribution" in data
        assert data["status_distribution"]["REQUIREMENT"] == 2
        assert data["status_distribution"]["DEVELOPMENT"] == 1

    def test_get_project_stats_not_found(self, client):
        """测试获取不存在项目的统计"""
        response = client.get("/api/projects/99999/stats")
        assert response.status_code == 404


@pytest.mark.api
@pytest.mark.integration
class TestProjectSearch:
    """测试项目搜索 API"""

    def test_search_projects(self, client, db_session):
        """测试搜索项目"""
        create_test_project(db_session, name="Python Web 开发", description="使用 Python")
        create_test_project(db_session, name="Java 后端", description="使用 Java")
        create_test_project(db_session, name="Python 数据分析", description="数据分析项目")

        response = client.get("/api/projects/search?q=Python")

        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 2
        for item in data:
            assert "Python" in item["name"] or "Python" in (item["description"] or "")

    def test_search_projects_with_limit(self, client, db_session):
        """测试搜索项目并限制结果数量"""
        for i in range(10):
            create_test_project(db_session, name=f"Python 项目{i}")

        response = client.get("/api/projects/search?q=Python&limit=5")

        assert response.status_code == 200
        data = response.json()
        assert len(data) <= 5

    def test_search_projects_empty_query(self, client):
        """测试空查询搜索"""
        response = client.get("/api/projects/search?q=")
        assert response.status_code == 200


@pytest.mark.api
@pytest.mark.integration
class TestProjectStatus:
    """测试项目状态 API"""

    def test_get_project_status(self, client, db_session):
        """测试获取项目状态"""
        from app.models.task import TaskStatus

        project = create_test_project(db_session, name="状态测试项目")
        create_test_task(db_session, project_id=project.id, title="任务1", status=TaskStatus.COMPLETED.value)
        create_test_task(db_session, project_id=project.id, title="任务2", status=TaskStatus.PENDING.value)

        response = client.get(f"/api/projects/{project.id}/status")

        assert response.status_code == 200
        data = response.json()
        assert data["project"]["name"] == "状态测试项目"
        assert data["total_tasks"] == 2
        assert data["completed_tasks"] == 1
        assert data["pending_tasks"] == 1

    def test_get_project_status_not_found(self, client):
        """测试获取不存在项目的状态"""
        response = client.get("/api/projects/99999/status")
        assert response.status_code == 404


@pytest.mark.api
@pytest.mark.integration
class TestProjectEdgeCases:
    """测试项目边界情况"""

    def test_create_project_with_long_description(self, client):
        """测试使用长描述创建项目"""
        project_data = {
            "name": "长描述项目",
            "description": "A" * 1000
        }
        response = client.post("/api/projects/", json=project_data)
        assert response.status_code == 200

    def test_create_project_with_empty_tech_stack(self, client):
        """测试使用空技术栈创建项目"""
        project_data = {
            "name": "空技术栈项目",
            "tech_stack": []
        }
        response = client.post("/api/projects/", json=project_data)
        assert response.status_code == 200
        assert response.json()["tech_stack"] == []

    def test_update_project_with_empty_name(self, client, db_session):
        """测试更新项目为空名称"""
        project = create_test_project(db_session, name="测试项目")

        response = client.put(f"/api/projects/{project.id}", json={"name": ""})
        assert response.status_code == 422

    def test_pagination_with_invalid_page(self, client):
        """测试使用无效页码分页"""
        response = client.get("/api/projects/?page=0")
        assert response.status_code == 422

    def test_pagination_with_large_page_size(self, client, db_session, mock_redis):
        """测试使用大页面大小分页"""
        for i in range(5):
            create_test_project(db_session, name=f"项目{i}")

        mock_redis.get_json.return_value = None

        response = client.get("/api/projects/?page_size=100")
        assert response.status_code == 200


@pytest.mark.api
@pytest.mark.integration
class TestProjectPerformance:
    """测试项目 API 性能"""

    def test_list_projects_performance(self, client, db_session, mock_redis):
        """测试项目列表性能"""
        # 创建大量项目
        for i in range(100):
            create_test_project(db_session, name=f"性能测试项目{i}")

        mock_redis.get_json.return_value = None

        import time
        start_time = time.time()
        response = client.get("/api/projects/")
        end_time = time.time()

        assert response.status_code == 200
        assert end_time - start_time < 3.0  # 应该在 3 秒内完成

    def test_search_projects_performance(self, client, db_session):
        """测试项目搜索性能"""
        # 创建大量项目
        for i in range(50):
            create_test_project(db_session, name=f"搜索测试项目{i}")

        import time
        start_time = time.time()
        response = client.get("/api/projects/search?q=测试")
        end_time = time.time()

        assert response.status_code == 200
        assert end_time - start_time < 2.0  # 应该在 2 秒内完成
