"""
项目管理功能回归测试套件

验证项目管理的核心功能，包括：
- 项目创建、读取、更新、删除 (CRUD)
- 项目状态管理
- 项目搜索和筛选
- 项目统计信息
- 边界条件和错误处理
"""

import pytest
from datetime import datetime
from typing import Dict, Any

from tests.conftest import create_test_project, create_test_task
from app.models.project import ProjectStatus


@pytest.mark.regression
@pytest.mark.api
class TestProjectManagementRegression:
    """项目管理回归测试套件"""

    def test_project_crud_lifecycle(self, client, db_session):
        """测试项目完整CRUD生命周期"""
        project_data = {
            "name": "回归测试项目",
            "description": "测试项目完整生命周期",
            "tech_stack": ["Python", "FastAPI", "Vue"],
            "status": "REQUIREMENT"
        }
        
        response = client.post("/api/projects/", json=project_data)
        assert response.status_code == 200
        created = response.json()
        project_id = created["id"]
        assert created["name"] == project_data["name"]
        
        response = client.get(f"/api/projects/{project_id}")
        assert response.status_code == 200
        read_data = response.json()
        assert read_data["name"] == project_data["name"]
        
        update_data = {
            "name": "更新后的项目名称",
            "description": "更新后的描述",
            "status": "DESIGN"
        }
        response = client.put(f"/api/projects/{project_id}", json=update_data)
        assert response.status_code == 200
        updated = response.json()
        assert updated["name"] == update_data["name"]
        assert updated["status"] == "DESIGN"
        
        response = client.delete(f"/api/projects/{project_id}")
        assert response.status_code == 200
        
        response = client.get(f"/api/projects/{project_id}")
        assert response.status_code == 404

    def test_project_status_transitions(self, client, db_session):
        """测试项目状态转换"""
        project = create_test_project(db_session, name="状态转换测试", status="REQUIREMENT")
        
        valid_transitions = [
            ("DESIGN", 200),
            ("DEVELOPMENT", 200),
            ("TESTING", 200),
            ("DEPLOYMENT", 200),
            ("COMPLETED", 200),
        ]
        
        for status, expected_code in valid_transitions:
            response = client.put(f"/api/projects/{project.id}", json={"status": status})
            assert response.status_code == expected_code, f"状态转换到 {status} 失败"
            
            updated = response.json()
            assert updated["status"] == status

    def test_project_with_tasks_integration(self, client, db_session, mock_redis):
        """测试项目与任务的集成"""
        project = create_test_project(db_session, name="集成测试项目")
        
        for i in range(5):
            create_test_task(db_session, project_id=project.id, title=f"任务{i+1}")
        
        mock_redis.get_json.return_value = None
        
        response = client.get(f"/api/projects/{project.id}")
        assert response.status_code == 200
        data = response.json()
        assert "task_stats" in data
        assert data["task_stats"]["total"] == 5
        
        response = client.get(f"/api/projects/{project.id}/stats")
        assert response.status_code == 200
        stats = response.json()
        assert stats["total_tasks"] == 5

    def test_project_search_functionality(self, client, db_session):
        """测试项目搜索功能"""
        projects = [
            create_test_project(db_session, name="Python Web开发", description="使用Python开发Web应用"),
            create_test_project(db_session, name="Java后端服务", description="Java微服务架构"),
            create_test_project(db_session, name="Python数据分析", description="数据分析和可视化"),
            create_test_project(db_session, name="React前端", description="React前端开发"),
        ]
        
        response = client.get("/api/projects/search?q=Python")
        assert response.status_code == 200
        results = response.json()
        assert len(results) >= 2
        
        response = client.get("/api/projects/search?q=开发")
        assert response.status_code == 200
        results = response.json()
        assert len(results) >= 2

    def test_project_pagination(self, client, db_session, mock_redis):
        """测试项目分页功能"""
        for i in range(25):
            create_test_project(db_session, name=f"分页测试项目{i+1}")
        
        mock_redis.get_json.return_value = None
        
        response = client.get("/api/projects/?page=1&page_size=10")
        assert response.status_code == 200
        page1 = response.json()
        assert len(page1["items"]) == 10
        assert page1["total"] == 25
        assert page1["total_pages"] == 3
        
        response = client.get("/api/projects/?page=3&page_size=10")
        assert response.status_code == 200
        page3 = response.json()
        assert len(page3["items"]) == 5

    def test_project_filter_by_status(self, client, db_session, mock_redis):
        """测试按状态筛选项目"""
        create_test_project(db_session, name="需求项目", status="REQUIREMENT")
        create_test_project(db_session, name="开发项目", status="DEVELOPMENT")
        create_test_project(db_session, name="测试项目", status="TESTING")
        create_test_project(db_session, name="需求项目2", status="REQUIREMENT")
        
        mock_redis.get_json.return_value = None
        
        response = client.get("/api/projects/?status=REQUIREMENT")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 2
        for item in data["items"]:
            assert item["status"] == "REQUIREMENT"

    def test_project_duplicate_name_handling(self, client, db_session):
        """测试项目名称重复处理"""
        project_data = {"name": "唯一名称项目"}
        
        response1 = client.post("/api/projects/", json=project_data)
        assert response1.status_code == 200
        
        response2 = client.post("/api/projects/", json=project_data)
        assert response2.status_code == 409

    def test_project_validation_rules(self, client):
        """测试项目验证规则"""
        invalid_cases = [
            ({"name": ""}, 422, "空名称"),
            ({"name": "x" * 201}, 422, "名称过长"),
            ({}, 422, "缺少名称"),
            ({"name": "测试", "status": "INVALID"}, 400, "无效状态"),
        ]
        
        for data, expected_code, description in invalid_cases:
            response = client.post("/api/projects/", json=data)
            assert response.status_code == expected_code, f"{description} 验证失败"

    def test_project_unicode_support(self, client):
        """测试项目Unicode支持"""
        unicode_names = [
            "中文项目名称",
            "日本語プロジェクト",
            "한국어 프로젝트",
            "🚀 Emoji Project 🎉",
            "Mixed 混合 名称",
        ]
        
        for name in unicode_names:
            response = client.post("/api/projects/", json={"name": name})
            assert response.status_code == 200
            assert response.json()["name"] == name

    def test_project_stats_accuracy(self, client, db_session, mock_redis):
        """测试项目统计准确性"""
        from app.models.task import TaskStatus
        
        project = create_test_project(db_session, name="统计测试项目")
        
        task_statuses = [
            TaskStatus.COMPLETED.value,
            TaskStatus.COMPLETED.value,
            TaskStatus.IN_PROGRESS.value,
            TaskStatus.PENDING.value,
            TaskStatus.PENDING.value,
            TaskStatus.REVIEW.value,
        ]
        
        for i, status in enumerate(task_statuses):
            create_test_task(db_session, project_id=project.id, title=f"任务{i+1}", status=status)
        
        mock_redis.get_json.return_value = None
        
        response = client.get(f"/api/projects/{project.id}/stats")
        assert response.status_code == 200
        stats = response.json()
        
        assert stats["total_tasks"] == 6
        assert stats["completed_tasks"] == 2
        assert stats["pending_tasks"] == 2
        assert stats["in_progress_tasks"] == 1
        assert "progress" in stats

    def test_project_deletion_cascade(self, client, db_session):
        """测试项目删除级联效果"""
        project = create_test_project(db_session, name="待删除项目")
        for i in range(3):
            create_test_task(db_session, project_id=project.id, title=f"任务{i+1}")
        
        response = client.delete(f"/api/projects/{project.id}")
        assert response.status_code == 200
        data = response.json()
        assert data["deleted_tasks"] == 3
        
        response = client.get(f"/api/projects/{project.id}")
        assert response.status_code == 404

    def test_project_concurrent_updates(self, client, db_session):
        """测试项目并发更新处理"""
        project = create_test_project(db_session, name="并发测试项目")
        
        update1 = {"name": "更新1"}
        update2 = {"description": "更新2描述"}
        
        response1 = client.put(f"/api/projects/{project.id}", json=update1)
        response2 = client.put(f"/api/projects/{project.id}", json=update2)
        
        assert response1.status_code == 200
        assert response2.status_code == 200
        
        final = client.get(f"/api/projects/{project.id}").json()
        assert final["name"] == "更新1"
        assert final["description"] == "更新2描述"


@pytest.mark.regression
@pytest.mark.api
class TestProjectEdgeCases:
    """项目管理边界条件测试"""

    def test_empty_project_list(self, client):
        """测试空项目列表"""
        response = client.get("/api/projects/")
        assert response.status_code == 200
        data = response.json()
        assert data["items"] == []
        assert data["total"] == 0

    def test_project_not_found_scenarios(self, client):
        """测试项目不存在场景"""
        endpoints = [
            "/api/projects/99999",
            "/api/projects/99999/stats",
            "/api/projects/99999/status",
        ]
        
        for endpoint in endpoints:
            response = client.get(endpoint)
            assert response.status_code == 404

    def test_project_with_special_characters(self, client):
        """测试特殊字符处理"""
        special_chars = [
            "项目<>&\"'",
            "项目\n换行",
            "项目\t制表符",
        ]
        
        for name in special_chars:
            response = client.post("/api/projects/", json={"name": name})
            assert response.status_code == 200

    def test_project_large_data_handling(self, client):
        """测试大数据量处理"""
        large_description = "A" * 5000
        large_tech_stack = [f"Tech{i}" for i in range(100)]
        
        response = client.post("/api/projects/", json={
            "name": "大数据项目",
            "description": large_description,
            "tech_stack": large_tech_stack
        })
        assert response.status_code == 200

    def test_project_invalid_id_formats(self, client):
        """测试无效ID格式"""
        invalid_ids = ["abc", "-1", "0", "null", "undefined"]
        
        for invalid_id in invalid_ids:
            response = client.get(f"/api/projects/{invalid_id}")
            assert response.status_code in [400, 404, 422]


@pytest.mark.regression
@pytest.mark.performance
class TestProjectPerformance:
    """项目管理性能测试"""

    def test_list_projects_performance(self, client, db_session, mock_redis):
        """测试项目列表性能"""
        for i in range(100):
            create_test_project(db_session, name=f"性能测试项目{i}")
        
        mock_redis.get_json.return_value = None
        
        import time
        start = time.time()
        response = client.get("/api/projects/")
        duration = time.time() - start
        
        assert response.status_code == 200
        assert duration < 3.0

    def test_search_performance(self, client, db_session):
        """测试搜索性能"""
        for i in range(50):
            create_test_project(db_session, name=f"搜索项目{i}")
        
        import time
        start = time.time()
        response = client.get("/api/projects/search?q=搜索")
        duration = time.time() - start
        
        assert response.status_code == 200
        assert duration < 2.0
