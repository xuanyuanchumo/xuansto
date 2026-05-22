"""
任务管理功能回归测试套件

验证任务管理的核心功能，包括：
- 任务创建、读取、更新、删除 (CRUD)
- 任务状态管理
- 任务依赖关系
- 任务分配
- 任务搜索和筛选
- 任务统计信息
"""

import pytest
from typing import List

from tests.conftest import create_test_project, create_test_task, create_test_agent
from app.models.task import TaskStatus


@pytest.mark.regression
@pytest.mark.api
class TestTaskManagementRegression:
    """任务管理回归测试套件"""

    def test_task_crud_lifecycle(self, client, db_session):
        """测试任务完整CRUD生命周期"""
        project = create_test_project(db_session, name="任务测试项目")
        
        task_data = {
            "title": "回归测试任务",
            "description": "测试任务完整生命周期",
            "project_id": project.id,
            "priority": "high",
            "estimated_hours": 8.0
        }
        
        response = client.post("/api/tasks/", json=task_data)
        assert response.status_code == 200
        created = response.json()
        task_id = created["id"]
        assert created["title"] == task_data["title"]
        assert created["status"] == "PENDING"
        
        response = client.get(f"/api/tasks/{task_id}")
        assert response.status_code == 200
        read_data = response.json()
        assert read_data["title"] == task_data["title"]
        
        update_data = {
            "title": "更新后的任务",
            "status": "IN_PROGRESS",
            "actual_hours": 4.0
        }
        response = client.put(f"/api/tasks/{task_id}", json=update_data)
        assert response.status_code == 200
        updated = response.json()
        assert updated["title"] == update_data["title"]
        assert updated["status"] == "IN_PROGRESS"
        
        response = client.delete(f"/api/tasks/{task_id}")
        assert response.status_code == 200
        
        response = client.get(f"/api/tasks/{task_id}")
        assert response.status_code == 404

    def test_task_status_transitions(self, client, db_session):
        """测试任务状态转换"""
        project = create_test_project(db_session, name="状态测试项目")
        task = create_test_task(db_session, project_id=project.id, title="状态转换任务")
        
        valid_transitions = [
            (TaskStatus.IN_PROGRESS.value, 200),
            (TaskStatus.REVIEW.value, 200),
            (TaskStatus.COMPLETED.value, 200),
        ]
        
        for status, expected_code in valid_transitions:
            response = client.put(f"/api/tasks/{task.id}", json={"status": status})
            assert response.status_code == expected_code
            
            updated = response.json()
            assert updated["status"] == status

    def test_task_dependencies_management(self, client, db_session):
        """测试任务依赖关系管理"""
        project = create_test_project(db_session, name="依赖测试项目")
        
        task1 = create_test_task(db_session, project_id=project.id, title="前置任务")
        task2 = create_test_task(db_session, project_id=project.id, title="后置任务")
        task3 = create_test_task(db_session, project_id=project.id, title="独立任务")
        
        response = client.put(f"/api/tasks/{task2.id}", json={"dependencies": [task1.id]})
        assert response.status_code == 200
        assert task1.id in response.json()["dependencies"]
        
        response = client.put(f"/api/tasks/{task3.id}", json={"dependencies": [task1.id, task2.id]})
        assert response.status_code == 200
        dependencies = response.json()["dependencies"]
        assert task1.id in dependencies
        assert task2.id in dependencies
        
        response = client.put(f"/api/tasks/{task2.id}", json={"dependencies": []})
        assert response.status_code == 200
        assert response.json()["dependencies"] == []

    def test_task_dependency_validation(self, client, db_session):
        """测试任务依赖验证"""
        project = create_test_project(db_session, name="依赖验证项目")
        task = create_test_task(db_session, project_id=project.id, title="自依赖测试")
        
        response = client.put(f"/api/tasks/{task.id}", json={"dependencies": [task.id]})
        assert response.status_code == 400
        
        non_existent_id = 99999
        response = client.put(f"/api/tasks/{task.id}", json={"dependencies": [non_existent_id]})
        assert response.status_code in [400, 404]

    def test_task_assignment_flow(self, client, db_session, mock_redis):
        """测试任务分配流程"""
        project = create_test_project(db_session, name="分配测试项目")
        agent = create_test_agent(db_session, name="测试代理", skills=["Python"])
        
        mock_redis.get_json.return_value = None
        
        task_data = {
            "title": "待分配任务",
            "project_id": project.id,
            "required_skill": "Python"
        }
        response = client.post("/api/tasks/", json=task_data)
        assert response.status_code == 200
        task_id = response.json()["id"]
        
        response = client.put(f"/api/tasks/{task_id}", json={"agent_id": agent.id})
        assert response.status_code == 200
        updated = response.json()
        assert updated["agent_id"] == agent.id
        
        mock_redis.get_json.return_value = None
        response = client.get(f"/api/tasks/{task_id}")
        assert response.status_code == 200
        detail = response.json()
        assert detail["agent"] is not None
        assert detail["agent"]["name"] == "测试代理"

    def test_task_search_functionality(self, client, db_session):
        """测试任务搜索功能"""
        project = create_test_project(db_session, name="搜索测试项目")
        
        tasks = [
            create_test_task(db_session, project_id=project.id, title="Python开发任务", priority="high"),
            create_test_task(db_session, project_id=project.id, title="Java开发任务", priority="medium"),
            create_test_task(db_session, project_id=project.id, title="测试任务", priority="low"),
            create_test_task(db_session, project_id=project.id, title="Python测试任务", priority="high"),
        ]
        
        response = client.get("/api/tasks/search?keyword=Python")
        assert response.status_code == 200
        results = response.json()
        assert len(results) >= 2
        
        response = client.get("/api/tasks/search?priority=high")
        assert response.status_code == 200
        results = response.json()
        for task in results:
            assert task["priority"] == "high"

    def test_task_filter_by_status(self, client, db_session):
        """测试按状态筛选任务"""
        project = create_test_project(db_session, name="状态筛选项目")
        
        create_test_task(db_session, project_id=project.id, title="待处理任务", status=TaskStatus.PENDING.value)
        create_test_task(db_session, project_id=project.id, title="进行中任务", status=TaskStatus.IN_PROGRESS.value)
        create_test_task(db_session, project_id=project.id, title="已完成任务", status=TaskStatus.COMPLETED.value)
        
        response = client.get(f"/api/tasks/search?status={TaskStatus.PENDING.value}")
        assert response.status_code == 200
        results = response.json()
        for task in results:
            assert task["status"] == TaskStatus.PENDING.value

    def test_task_filter_by_project(self, client, db_session):
        """测试按项目筛选任务"""
        project1 = create_test_project(db_session, name="项目1")
        project2 = create_test_project(db_session, name="项目2")
        
        create_test_task(db_session, project_id=project1.id, title="项目1任务")
        create_test_task(db_session, project_id=project1.id, title="项目1任务2")
        create_test_task(db_session, project_id=project2.id, title="项目2任务")
        
        response = client.get(f"/api/tasks/search?project_id={project1.id}")
        assert response.status_code == 200
        results = response.json()
        assert len(results) == 2
        for task in results:
            assert task["project_id"] == project1.id

    def test_task_priority_management(self, client, db_session):
        """测试任务优先级管理"""
        project = create_test_project(db_session, name="优先级测试项目")
        
        valid_priorities = ["low", "medium", "high", "critical"]
        
        for priority in valid_priorities:
            task = create_test_task(
                db_session, 
                project_id=project.id, 
                title=f"{priority}优先级任务",
                priority=priority
            )
            assert task.priority == priority
        
        task = create_test_task(db_session, project_id=project.id, title="优先级更新任务")
        response = client.put(f"/api/tasks/{task.id}", json={"priority": "critical"})
        assert response.status_code == 200
        assert response.json()["priority"] == "critical"

    def test_task_statistics(self, client, db_session, mock_redis):
        """测试任务统计功能"""
        project = create_test_project(db_session, name="统计测试项目")
        
        statuses = [
            TaskStatus.COMPLETED.value,
            TaskStatus.COMPLETED.value,
            TaskStatus.IN_PROGRESS.value,
            TaskStatus.PENDING.value,
            TaskStatus.PENDING.value,
            TaskStatus.REVIEW.value,
        ]
        
        for i, status in enumerate(statuses):
            create_test_task(
                db_session,
                project_id=project.id,
                title=f"统计任务{i+1}",
                status=status,
                priority="high" if i < 2 else "medium"
            )
        
        mock_redis.get_json.return_value = None
        
        response = client.get("/api/tasks/stats")
        assert response.status_code == 200
        stats = response.json()
        
        assert stats["total"] == 6
        assert "by_status" in stats
        assert "by_priority" in stats
        assert "completed_rate" in stats

    def test_task_time_tracking(self, client, db_session):
        """测试任务时间跟踪"""
        project = create_test_project(db_session, name="时间跟踪项目")
        
        task_data = {
            "title": "时间跟踪任务",
            "project_id": project.id,
            "estimated_hours": 10.0
        }
        response = client.post("/api/tasks/", json=task_data)
        assert response.status_code == 200
        task_id = response.json()["id"]
        
        response = client.put(f"/api/tasks/{task_id}", json={"actual_hours": 8.5})
        assert response.status_code == 200
        updated = response.json()
        assert updated["actual_hours"] == 8.5
        assert updated["estimated_hours"] == 10.0

    def test_task_deletion_with_dependencies(self, client, db_session):
        """测试删除有依赖关系的任务"""
        project = create_test_project(db_session, name="删除测试项目")
        
        task1 = create_test_task(db_session, project_id=project.id, title="被依赖任务")
        task2 = create_test_task(db_session, project_id=project.id, title="依赖任务")
        
        client.put(f"/api/tasks/{task2.id}", json={"dependencies": [task1.id]})
        
        response = client.delete(f"/api/tasks/{task1.id}")
        assert response.status_code == 400

    def test_task_bulk_operations(self, client, db_session, mock_redis):
        """测试任务批量操作"""
        project = create_test_project(db_session, name="批量操作项目")
        
        task_ids = []
        for i in range(5):
            task = create_test_task(db_session, project_id=project.id, title=f"批量任务{i+1}")
            task_ids.append(task.id)
        
        mock_redis.get_json.return_value = None
        
        response = client.get(f"/api/tasks/project/{project.id}")
        assert response.status_code == 200
        tasks = response.json()
        assert len(tasks) == 5


@pytest.mark.regression
@pytest.mark.api
class TestTaskEdgeCases:
    """任务管理边界条件测试"""

    def test_empty_task_list(self, client):
        """测试空任务列表"""
        response = client.get("/api/tasks/")
        assert response.status_code == 200
        assert response.json() == []

    def test_task_not_found_scenarios(self, client):
        """测试任务不存在场景"""
        response = client.get("/api/tasks/99999")
        assert response.status_code == 404
        
        response = client.put("/api/tasks/99999", json={"title": "更新"})
        assert response.status_code == 404
        
        response = client.delete("/api/tasks/99999")
        assert response.status_code == 404

    def test_task_with_invalid_project(self, client):
        """测试使用无效项目创建任务"""
        task_data = {
            "title": "无效项目任务",
            "project_id": 99999
        }
        response = client.post("/api/tasks/", json=task_data)
        assert response.status_code == 404

    def test_task_with_invalid_agent(self, client, db_session):
        """测试使用无效代理创建任务"""
        project = create_test_project(db_session, name="无效代理项目")
        
        task_data = {
            "title": "无效代理任务",
            "project_id": project.id,
            "agent_id": 99999
        }
        response = client.post("/api/tasks/", json=task_data)
        assert response.status_code == 404

    def test_task_validation_rules(self, client):
        """测试任务验证规则"""
        invalid_cases = [
            ({"title": ""}, 422, "空标题"),
            ({}, 422, "缺少标题"),
            ({"title": "测试", "priority": "invalid"}, 400, "无效优先级"),
        ]
        
        for data, expected_code, description in invalid_cases:
            response = client.post("/api/tasks/", json=data)
            assert response.status_code == expected_code, f"{description} 验证失败"

    def test_task_unicode_support(self, client, db_session):
        """测试任务Unicode支持"""
        project = create_test_project(db_session, name="Unicode项目")
        
        unicode_titles = [
            "中文任务标题",
            "日本語タスク",
            "한국어 작업",
            "🚀 Emoji Task 🎉",
        ]
        
        for title in unicode_titles:
            response = client.post("/api/tasks/", json={
                "title": title,
                "project_id": project.id
            })
            assert response.status_code == 200
            assert response.json()["title"] == title

    def test_task_large_description(self, client, db_session):
        """测试大描述文本"""
        project = create_test_project(db_session, name="大描述项目")
        
        large_description = "A" * 10000
        response = client.post("/api/tasks/", json={
            "title": "大描述任务",
            "description": large_description,
            "project_id": project.id
        })
        assert response.status_code == 200


@pytest.mark.regression
@pytest.mark.performance
class TestTaskPerformance:
    """任务管理性能测试"""

    def test_list_tasks_performance(self, client, db_session, mock_redis):
        """测试任务列表性能"""
        project = create_test_project(db_session, name="性能测试项目")
        for i in range(100):
            create_test_task(db_session, project_id=project.id, title=f"性能任务{i}")
        
        mock_redis.get_json.return_value = None
        
        import time
        start = time.time()
        response = client.get("/api/tasks/")
        duration = time.time() - start
        
        assert response.status_code == 200
        assert duration < 3.0

    def test_search_tasks_performance(self, client, db_session):
        """测试任务搜索性能"""
        project = create_test_project(db_session, name="搜索性能项目")
        for i in range(50):
            create_test_task(db_session, project_id=project.id, title=f"搜索任务{i}")
        
        import time
        start = time.time()
        response = client.get("/api/tasks/search?keyword=搜索")
        duration = time.time() - start
        
        assert response.status_code == 200
        assert duration < 2.0

    def test_task_stats_performance(self, client, db_session, mock_redis):
        """测试任务统计性能"""
        project = create_test_project(db_session, name="统计性能项目")
        for i in range(50):
            create_test_task(db_session, project_id=project.id, title=f"统计任务{i}")
        
        mock_redis.get_json.return_value = None
        
        import time
        start = time.time()
        response = client.get("/api/tasks/stats")
        duration = time.time() - start
        
        assert response.status_code == 200
        assert duration < 2.0
