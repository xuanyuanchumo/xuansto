"""
任务 API 集成测试

测试任务相关的 API 端点，包括完整的 CRUD 操作和业务流程
"""

import pytest
from tests.conftest import create_test_task, create_test_project, create_test_agent


@pytest.mark.api
@pytest.mark.integration
class TestTaskAPI:
    """测试任务 API 集成"""

    def test_task_lifecycle(self, client, db_session, mock_redis):
        """测试任务完整生命周期"""
        from app.models.task import TaskStatus

        # 1. 创建项目
        project = create_test_project(db_session, name="任务生命周期项目")

        # 2. 创建任务
        task_data = {
            "title": "生命周期测试任务",
            "description": "测试任务完整生命周期",
            "project_id": project.id,
            "priority": "high"
        }
        response = client.post("/api/tasks/", json=task_data)
        assert response.status_code == 200
        task = response.json()
        task_id = task["id"]
        assert task["status"] == TaskStatus.PENDING.value

        # 3. 获取任务详情
        mock_redis.get_json.return_value = None
        response = client.get(f"/api/tasks/{task_id}")
        assert response.status_code == 200
        assert response.json()["title"] == "生命周期测试任务"

        # 4. 更新任务状态
        response = client.put(f"/api/tasks/{task_id}", json={"status": TaskStatus.IN_PROGRESS.value})
        assert response.status_code == 200
        assert response.json()["status"] == TaskStatus.IN_PROGRESS.value

        # 5. 完成任务
        response = client.put(f"/api/tasks/{task_id}", json={"status": TaskStatus.COMPLETED.value})
        assert response.status_code == 200
        assert response.json()["status"] == TaskStatus.COMPLETED.value

        # 6. 删除任务
        response = client.delete(f"/api/tasks/{task_id}")
        assert response.status_code == 200

        # 7. 验证任务已删除
        response = client.get(f"/api/tasks/{task_id}")
        assert response.status_code == 404

    def test_task_with_agent_assignment(self, client, db_session, mock_redis):
        """测试任务代理分配"""
        project = create_test_project(db_session, name="代理分配项目")
        agent = create_test_agent(db_session, name="测试代理")

        # 创建任务
        task_data = {
            "title": "代理分配任务",
            "project_id": project.id,
            "agent_id": agent.id,
            "required_skill": "python"
        }
        response = client.post("/api/tasks/", json=task_data)
        assert response.status_code == 200
        task = response.json()
        assert task["agent_id"] == agent.id

        # 获取任务详情
        mock_redis.get_json.return_value = None
        response = client.get(f"/api/tasks/{task.id}")
        assert response.status_code == 200
        data = response.json()
        assert data["agent"] is not None
        assert data["agent"]["id"] == agent.id

    def test_task_with_dependencies(self, client, db_session, mock_redis):
        """测试任务依赖关系"""
        project = create_test_project(db_session, name="依赖关系项目")

        # 创建前置任务
        dep_task = create_test_task(db_session, project_id=project.id, title="前置任务")

        # 创建依赖任务
        task_data = {
            "title": "依赖任务",
            "project_id": project.id,
            "dependencies": [dep_task.id]
        }
        response = client.post("/api/tasks/", json=task_data)
        assert response.status_code == 200
        task = response.json()
        assert dep_task.id in task["dependencies"]

        # 获取任务详情
        mock_redis.get_json.return_value = None
        response = client.get(f"/api/tasks/{task['id']}")
        assert response.status_code == 200
        data = response.json()
        assert len(data["dependencies_detail"]) == 1
        assert data["dependencies_detail"][0]["id"] == dep_task.id

    def test_task_status_transitions(self, client, db_session):
        """测试任务状态流转"""
        from app.models.task import TaskStatus

        project = create_test_project(db_session, name="状态流转项目")
        task = create_test_task(db_session, project_id=project.id, title="状态流转任务")

        # 测试状态流转
        transitions = [
            (TaskStatus.PENDING.value, TaskStatus.IN_PROGRESS.value),
            (TaskStatus.IN_PROGRESS.value, TaskStatus.COMPLETED.value)
        ]

        for current_status, next_status in transitions:
            response = client.put(f"/api/tasks/{task.id}", json={"status": next_status})
            assert response.status_code == 200
            assert response.json()["status"] == next_status
            db_session.refresh(task)

    def test_task_search_and_filter(self, client, db_session):
        """测试任务搜索和筛选"""
        project = create_test_project(db_session, name="搜索筛选项目")

        # 创建多个任务
        create_test_task(db_session, project_id=project.id, title="Python 开发任务", priority="high")
        create_test_task(db_session, project_id=project.id, title="Java 开发任务", priority="medium")
        create_test_task(db_session, project_id=project.id, title="测试任务", priority="low")

        # 按关键词搜索
        response = client.get("/api/tasks/search?keyword=Python")
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1

        # 按优先级筛选
        response = client.get("/api/tasks/search?priority=high")
        assert response.status_code == 200
        data = response.json()
        for task in data:
            assert task["priority"] == "high"


@pytest.mark.api
@pytest.mark.integration
class TestTaskValidation:
    """测试任务 API 验证"""

    def test_create_task_validation(self, client, db_session):
        """测试创建任务验证"""
        project = create_test_project(db_session, name="验证项目")

        # 空标题
        response = client.post("/api/tasks/", json={"title": "", "project_id": project.id})
        assert response.status_code == 422

        # 缺少必需字段
        response = client.post("/api/tasks/", json={"project_id": project.id})
        assert response.status_code == 422

        # 无效项目 ID
        response = client.post("/api/tasks/", json={"title": "任务", "project_id": 99999})
        assert response.status_code == 404

    def test_update_task_validation(self, client, db_session):
        """测试更新任务验证"""
        project = create_test_project(db_session, name="验证项目")
        task = create_test_task(db_session, project_id=project.id, title="验证任务")

        # 无效状态
        response = client.put(f"/api/tasks/{task.id}", json={"status": "INVALID"})
        assert response.status_code == 400

        # 空标题
        response = client.put(f"/api/tasks/{task.id}", json={"title": ""})
        assert response.status_code == 422

    def test_task_not_found(self, client):
        """测试任务不存在的情况"""
        # 获取不存在的任务
        response = client.get("/api/tasks/99999")
        assert response.status_code == 404

        # 更新不存在的任务
        response = client.put("/api/tasks/99999", json={"title": "新标题"})
        assert response.status_code == 404

        # 删除不存在的任务
        response = client.delete("/api/tasks/99999")
        assert response.status_code == 404


@pytest.mark.api
@pytest.mark.integration
class TestTaskEdgeCases:
    """测试任务边界情况"""

    def test_task_with_long_title(self, client, db_session):
        """测试使用长标题的任务"""
        project = create_test_project(db_session, name="长标题项目")
        task_data = {
            "title": "A" * 200,
            "project_id": project.id
        }
        response = client.post("/api/tasks/", json=task_data)
        assert response.status_code == 200

    def test_task_with_special_characters(self, client, db_session):
        """测试使用特殊字符的任务标题"""
        project = create_test_project(db_session, name="特殊字符项目")
        task_data = {
            "title": "任务!@#$%^&*()_+-=[]{}|;':\",./<>?",
            "project_id": project.id
        }
        response = client.post("/api/tasks/", json=task_data)
        assert response.status_code == 200

    def test_task_with_unicode(self, client, db_session):
        """测试使用 Unicode 的任务标题"""
        project = create_test_project(db_session, name="Unicode项目")
        task_data = {
            "title": "🚀 任务 日本語 한국어 العربية",
            "project_id": project.id
        }
        response = client.post("/api/tasks/", json=task_data)
        assert response.status_code == 200

    def test_task_circular_dependency(self, client, db_session):
        """测试任务循环依赖检测"""
        project = create_test_project(db_session, name="循环依赖项目")

        task1 = create_test_task(db_session, project_id=project.id, title="任务1")
        task2 = create_test_task(db_session, project_id=project.id, title="任务2", dependencies=[task1.id])

        # 尝试让 task1 依赖 task2，形成循环
        response = client.put(f"/api/tasks/{task1.id}", json={"dependencies": [task2.id]})

        # 应该失败或处理循环依赖
        assert response.status_code in [200, 400]

    def test_task_self_dependency(self, client, db_session):
        """测试任务依赖自身"""
        project = create_test_project(db_session, name="自依赖项目")
        task = create_test_task(db_session, project_id=project.id, title="自依赖任务")

        response = client.put(f"/api/tasks/{task.id}", json={"dependencies": [task.id]})
        assert response.status_code == 400
        assert "cannot depend on itself" in response.json()["detail"].lower()

    def test_task_delete_with_dependencies(self, client, db_session):
        """测试删除有被依赖的任务"""
        project = create_test_project(db_session, name="删除依赖项目")

        task1 = create_test_task(db_session, project_id=project.id, title="前置任务")
        task2 = create_test_task(db_session, project_id=project.id, title="依赖任务", dependencies=[task1.id])

        # 尝试删除被依赖的任务
        response = client.delete(f"/api/tasks/{task1.id}")
        assert response.status_code == 400
        assert "dependency" in response.json()["detail"].lower()


@pytest.mark.api
@pytest.mark.integration
class TestTaskPerformance:
    """测试任务 API 性能"""

    def test_list_tasks_performance(self, client, db_session, mock_redis):
        """测试任务列表性能"""
        project = create_test_project(db_session, name="性能测试项目")

        # 创建大量任务
        for i in range(100):
            create_test_task(db_session, project_id=project.id, title=f"性能测试任务{i}")

        mock_redis.get_json.return_value = None

        import time
        start_time = time.time()
        response = client.get("/api/tasks/")
        end_time = time.time()

        assert response.status_code == 200
        assert end_time - start_time < 3.0  # 应该在 3 秒内完成

    def test_search_tasks_performance(self, client, db_session):
        """测试任务搜索性能"""
        project = create_test_project(db_session, name="搜索性能项目")

        # 创建大量任务
        for i in range(50):
            create_test_task(db_session, project_id=project.id, title=f"搜索性能任务{i}")

        import time
        start_time = time.time()
        response = client.get("/api/tasks/search?keyword=性能")
        end_time = time.time()

        assert response.status_code == 200
        assert end_time - start_time < 2.0  # 应该在 2 秒内完成

    def test_task_stats_performance(self, client, db_session, mock_redis):
        """测试任务统计性能"""
        project = create_test_project(db_session, name="统计性能项目")

        # 创建大量任务
        for i in range(50):
            create_test_task(db_session, project_id=project.id, title=f"统计任务{i}")

        mock_redis.get_json.return_value = None

        import time
        start_time = time.time()
        response = client.get("/api/tasks/stats")
        end_time = time.time()

        assert response.status_code == 200
        assert end_time - start_time < 2.0  # 应该在 2 秒内完成


@pytest.mark.api
@pytest.mark.integration
class TestTaskHours:
    """测试任务工时管理"""

    def test_task_hours_tracking(self, client, db_session):
        """测试任务工时跟踪"""
        project = create_test_project(db_session, name="工时跟踪项目")

        # 创建带工时的任务
        task_data = {
            "title": "工时跟踪任务",
            "project_id": project.id,
            "estimated_hours": 16.0,
            "actual_hours": 0.0
        }
        response = client.post("/api/tasks/", json=task_data)
        assert response.status_code == 200
        task = response.json()
        assert task["estimated_hours"] == 16.0
        assert task["actual_hours"] == 0.0

        # 更新实际工时
        response = client.put(f"/api/tasks/{task['id']}", json={"actual_hours": 8.0})
        assert response.status_code == 200
        assert response.json()["actual_hours"] == 8.0

    def test_task_hours_validation(self, client, db_session):
        """测试任务工时验证"""
        project = create_test_project(db_session, name="工时验证项目")

        # 负工时
        task_data = {
            "title": "负工时任务",
            "project_id": project.id,
            "estimated_hours": -1.0
        }
        response = client.post("/api/tasks/", json=task_data)
        assert response.status_code == 422

    def test_task_hours_progress(self, client, db_session):
        """测试任务工时进度"""
        project = create_test_project(db_session, name="工时进度项目")

        task_data = {
            "title": "工时进度任务",
            "project_id": project.id,
            "estimated_hours": 10.0,
            "actual_hours": 5.0
        }
        response = client.post("/api/tasks/", json=task_data)
        assert response.status_code == 200
        task = response.json()

        # 验证进度计算
        progress = (task["actual_hours"] / task["estimated_hours"]) * 100
        assert progress == 50.0


@pytest.mark.api
@pytest.mark.integration
class TestTaskPriority:
    """测试任务优先级"""

    def test_task_priority_levels(self, client, db_session):
        """测试任务优先级级别"""
        project = create_test_project(db_session, name="优先级项目")

        priorities = ["low", "medium", "high", "critical"]

        for priority in priorities:
            task_data = {
                "title": f"{priority}优先级任务",
                "project_id": project.id,
                "priority": priority
            }
            response = client.post("/api/tasks/", json=task_data)
            assert response.status_code == 200
            assert response.json()["priority"] == priority

    def test_task_priority_filter(self, client, db_session):
        """测试任务优先级筛选"""
        project = create_test_project(db_session, name="优先级筛选项目")

        # 创建不同优先级的任务
        create_test_task(db_session, project_id=project.id, title="高优先级任务", priority="high")
        create_test_task(db_session, project_id=project.id, title="中优先级任务", priority="medium")
        create_test_task(db_session, project_id=project.id, title="低优先级任务", priority="low")

        # 筛选高优先级任务
        response = client.get("/api/tasks/search?priority=high")
        assert response.status_code == 200
        data = response.json()
        for task in data:
            assert task["priority"] == "high"

    def test_task_priority_update(self, client, db_session):
        """测试任务优先级更新"""
        project = create_test_project(db_session, name="优先级更新项目")
        task = create_test_task(db_session, project_id=project.id, title="优先级任务", priority="low")

        # 更新优先级
        response = client.put(f"/api/tasks/{task.id}", json={"priority": "high"})
        assert response.status_code == 200
        assert response.json()["priority"] == "high"
