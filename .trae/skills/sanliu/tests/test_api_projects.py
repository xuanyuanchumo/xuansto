"""
项目 API 集成测试

测试项目相关的 API 端点，包括完整的 CRUD 操作和业务流程
"""

import pytest
from tests.conftest import create_test_project, create_test_task


@pytest.mark.api
@pytest.mark.integration
class TestProjectAPI:
    """测试项目 API 集成"""

    def test_project_lifecycle(self, client, db_session, mock_redis):
        """测试项目完整生命周期"""
        from app.models.project import ProjectStatus

        # 1. 创建项目
        project_data = {
            "name": "生命周期测试项目",
            "description": "测试项目完整生命周期",
            "tech_stack": ["Python", "FastAPI", "React"]
        }
        response = client.post("/api/projects/", json=project_data)
        assert response.status_code == 200
        project = response.json()
        project_id = project["id"]
        assert project["status"] == ProjectStatus.REQUIREMENT.value

        # 2. 获取项目详情
        response = client.get(f"/api/projects/{project_id}")
        assert response.status_code == 200
        assert response.json()["name"] == "生命周期测试项目"

        # 3. 更新项目
        update_data = {
            "description": "更新后的描述",
            "status": ProjectStatus.DESIGN.value
        }
        response = client.put(f"/api/projects/{project_id}", json=update_data)
        assert response.status_code == 200
        assert response.json()["description"] == "更新后的描述"
        assert response.json()["status"] == ProjectStatus.DESIGN.value

        # 4. 创建任务
        task_data = {
            "title": "项目任务",
            "project_id": project_id,
            "priority": "high"
        }
        response = client.post("/api/tasks/", json=task_data)
        assert response.status_code == 200

        # 5. 获取项目统计
        mock_redis.get_json.return_value = None
        response = client.get(f"/api/projects/{project_id}/stats")
        assert response.status_code == 200
        stats = response.json()
        assert stats["total_tasks"] == 1

        # 6. 删除项目
        response = client.delete(f"/api/projects/{project_id}")
        assert response.status_code == 200

        # 7. 验证项目已删除
        response = client.get(f"/api/projects/{project_id}")
        assert response.status_code == 404

    def test_project_with_multiple_tasks(self, client, db_session, mock_redis):
        """测试包含多个任务的项目"""
        from app.models.task import TaskStatus

        # 创建项目
        project = create_test_project(db_session, name="多任务项目")

        # 创建多个任务
        for i in range(5):
            create_test_task(db_session, project_id=project.id, title=f"任务{i+1}")

        # 更新任务状态
        mock_redis.get_json.return_value = None
        response = client.get(f"/api/projects/{project_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["task_stats"]["total"] == 5

    def test_project_status_transitions(self, client, db_session):
        """测试项目状态流转"""
        from app.models.project import ProjectStatus

        # 创建项目
        project = create_test_project(db_session, name="状态流转项目")

        # 定义状态流转路径
        transitions = [
            (ProjectStatus.REQUIREMENT.value, ProjectStatus.DESIGN.value),
            (ProjectStatus.DESIGN.value, ProjectStatus.DEVELOPMENT.value),
            (ProjectStatus.DEVELOPMENT.value, ProjectStatus.TESTING.value),
            (ProjectStatus.TESTING.value, ProjectStatus.DEPLOYMENT.value),
            (ProjectStatus.DEPLOYMENT.value, ProjectStatus.COMPLETED.value)
        ]

        for current_status, next_status in transitions:
            # 确保当前状态正确
            db_session.refresh(project)
            assert project.status == current_status

            # 更新到下一个状态
            response = client.put(f"/api/projects/{project.id}", json={"status": next_status})
            assert response.status_code == 200
            assert response.json()["status"] == next_status

            # 刷新项目状态
            db_session.refresh(project)

    def test_project_search_and_filter(self, client, db_session, mock_redis):
        """测试项目搜索和筛选"""
        # 创建多个项目
        create_test_project(db_session, name="Python Web 项目")
        create_test_project(db_session, name="Python Data 项目")
        create_test_project(db_session, name="Java 项目")

        mock_redis.get_json.return_value = None

        # 搜索 Python 项目
        response = client.get("/api/projects/search?q=Python")
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 2

        # 按状态筛选
        response = client.get("/api/projects/?status=REQUIREMENT")
        assert response.status_code == 200

    def test_project_pagination(self, client, db_session, mock_redis):
        """测试项目分页"""
        # 创建多个项目
        for i in range(25):
            create_test_project(db_session, name=f"分页项目{i+1}")

        mock_redis.get_json.return_value = None

        # 第一页
        response = client.get("/api/projects/?page=1&page_size=10")
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 10
        assert data["total"] == 25
        assert data["total_pages"] == 3

        # 最后一页
        response = client.get("/api/projects/?page=3&page_size=10")
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 5


@pytest.mark.api
@pytest.mark.integration
class TestProjectValidation:
    """测试项目 API 验证"""

    def test_create_project_validation(self, client):
        """测试创建项目验证"""
        # 空名称
        response = client.post("/api/projects/", json={"name": ""})
        assert response.status_code == 422

        # 缺少必需字段
        response = client.post("/api/projects/", json={})
        assert response.status_code == 422

        # 名称过长
        response = client.post("/api/projects/", json={"name": "x" * 201})
        assert response.status_code == 422

    def test_update_project_validation(self, client, db_session):
        """测试更新项目验证"""
        project = create_test_project(db_session, name="验证项目")

        # 无效状态
        response = client.put(f"/api/projects/{project.id}", json={"status": "INVALID"})
        assert response.status_code == 400

        # 空名称
        response = client.put(f"/api/projects/{project.id}", json={"name": ""})
        assert response.status_code == 422

    def test_project_not_found(self, client):
        """测试项目不存在的情况"""
        # 获取不存在的项目
        response = client.get("/api/projects/99999")
        assert response.status_code == 404

        # 更新不存在的项目
        response = client.put("/api/projects/99999", json={"name": "新名称"})
        assert response.status_code == 404

        # 删除不存在的项目
        response = client.delete("/api/projects/99999")
        assert response.status_code == 404


@pytest.mark.api
@pytest.mark.integration
class TestProjectEdgeCases:
    """测试项目边界情况"""

    def test_duplicate_project_name(self, client, db_session):
        """测试重复项目名称"""
        project_data = {"name": "重复名称项目"}

        # 第一次创建
        response = client.post("/api/projects/", json=project_data)
        assert response.status_code == 200

        # 第二次创建同名项目
        response = client.post("/api/projects/", json=project_data)
        assert response.status_code == 409
        assert "already exists" in response.json()["detail"]

    def test_project_with_special_characters(self, client):
        """测试使用特殊字符的项目名称"""
        project_data = {
            "name": "特殊字符!@#$%^&*()_+-=[]{}|;':\",./<>?",
            "description": "包含特殊字符"
        }
        response = client.post("/api/projects/", json=project_data)
        assert response.status_code == 200

    def test_project_with_unicode(self, client):
        """测试使用 Unicode 的项目名称"""
        project_data = {
            "name": "🚀 项目 日本語 한국어 العربية",
            "description": "国际化项目"
        }
        response = client.post("/api/projects/", json=project_data)
        assert response.status_code == 200

    def test_project_with_long_description(self, client):
        """测试使用长描述的项目"""
        project_data = {
            "name": "长描述项目",
            "description": "A" * 5000
        }
        response = client.post("/api/projects/", json=project_data)
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
            create_test_project(db_session, name=f"搜索性能项目{i}")

        import time
        start_time = time.time()
        response = client.get("/api/projects/search?q=性能")
        end_time = time.time()

        assert response.status_code == 200
        assert end_time - start_time < 2.0  # 应该在 2 秒内完成

    def test_project_stats_performance(self, client, db_session, mock_redis):
        """测试项目统计性能"""
        # 创建大量项目
        for i in range(50):
            create_test_project(db_session, name=f"统计项目{i}")

        mock_redis.get_json.return_value = None

        import time
        start_time = time.time()
        response = client.get("/api/projects/stats")
        end_time = time.time()

        assert response.status_code == 200
        assert end_time - start_time < 2.0  # 应该在 2 秒内完成


@pytest.mark.api
@pytest.mark.integration
class TestProjectRelationships:
    """测试项目关系"""

    def test_project_with_tasks_relationship(self, client, db_session, mock_redis):
        """测试项目与任务的关系"""
        project = create_test_project(db_session, name="关系测试项目")

        # 创建任务
        for i in range(3):
            create_test_task(db_session, project_id=project.id, title=f"任务{i+1}")

        mock_redis.get_json.return_value = None

        # 获取项目详情
        response = client.get(f"/api/projects/{project.id}")
        assert response.status_code == 200
        data = response.json()
        assert data["task_stats"]["total"] == 3

    def test_project_deletion_with_tasks(self, client, db_session):
        """测试删除带任务的项目"""
        project = create_test_project(db_session, name="待删除项目")

        # 创建任务
        for i in range(3):
            create_test_task(db_session, project_id=project.id, title=f"任务{i+1}")

        # 删除项目
        response = client.delete(f"/api/projects/{project.id}")
        assert response.status_code == 200
        data = response.json()
        assert data["deleted_tasks"] == 3

    def test_project_task_stats_accuracy(self, client, db_session, mock_redis):
        """测试项目任务统计准确性"""
        from app.models.task import TaskStatus

        project = create_test_project(db_session, name="统计准确性项目")

        # 创建不同状态的任务
        create_test_task(db_session, project_id=project.id, title="已完成任务",
                        status=TaskStatus.COMPLETED.value)
        create_test_task(db_session, project_id=project.id, title="待处理任务",
                        status=TaskStatus.PENDING.value)
        create_test_task(db_session, project_id=project.id, title="进行中任务",
                        status=TaskStatus.IN_PROGRESS.value)

        mock_redis.get_json.return_value = None

        response = client.get(f"/api/projects/{project.id}/stats")
        assert response.status_code == 200
        data = response.json()
        assert data["total_tasks"] == 3
        assert data["completed_tasks"] == 1
        assert data["pending_tasks"] == 1
        assert data["in_progress_tasks"] == 1
