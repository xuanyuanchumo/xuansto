"""
任务 API 测试

测试任务相关的 API 端点
"""

import pytest
from tests.conftest import create_test_project, create_test_task, create_test_agent


@pytest.mark.api
@pytest.mark.integration
class TestTaskCreate:
    """测试任务创建 API"""

    def test_create_task_success(self, client, db_session):
        """测试成功创建任务"""
        project = create_test_project(db_session, name="测试项目")
        
        task_data = {
            "title": "新任务",
            "description": "任务描述",
            "project_id": project.id,
            "priority": "high"
        }
        response = client.post("/api/tasks/", json=task_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "新任务"
        assert data["description"] == "任务描述"
        assert data["project_id"] == project.id
        assert data["priority"] == "high"
        assert data["status"] == "PENDING"

    def test_create_task_with_agent(self, client, db_session):
        """测试创建任务并分配代理"""
        project = create_test_project(db_session, name="测试项目")
        agent = create_test_agent(db_session, name="测试代理")
        
        task_data = {
            "title": "分配代理的任务",
            "project_id": project.id,
            "agent_id": agent.id
        }
        response = client.post("/api/tasks/", json=task_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["agent_id"] == agent.id

    def test_create_task_with_dependencies(self, client, db_session):
        """测试创建带依赖的任务"""
        project = create_test_project(db_session, name="测试项目")
        task1 = create_test_task(db_session, project_id=project.id, title="前置任务")
        
        task_data = {
            "title": "依赖任务",
            "project_id": project.id,
            "dependencies": [task1.id]
        }
        response = client.post("/api/tasks/", json=task_data)
        
        assert response.status_code == 200
        data = response.json()
        assert task1.id in data["dependencies"]

    def test_create_task_invalid_project(self, client):
        """测试使用无效项目ID创建任务"""
        task_data = {
            "title": "任务",
            "project_id": 99999
        }
        response = client.post("/api/tasks/", json=task_data)
        
        assert response.status_code == 404

    def test_create_task_invalid_agent(self, client, db_session):
        """测试使用无效代理ID创建任务"""
        project = create_test_project(db_session, name="测试项目")
        
        task_data = {
            "title": "任务",
            "project_id": project.id,
            "agent_id": 99999
        }
        response = client.post("/api/tasks/", json=task_data)
        
        assert response.status_code == 404

    def test_create_task_invalid_priority(self, client, db_session):
        """测试使用无效优先级创建任务"""
        project = create_test_project(db_session, name="测试项目")
        
        task_data = {
            "title": "任务",
            "project_id": project.id,
            "priority": "invalid_priority"
        }
        response = client.post("/api/tasks/", json=task_data)
        
        assert response.status_code == 400

    def test_create_task_empty_title(self, client):
        """测试创建空标题任务"""
        task_data = {
            "title": ""
        }
        response = client.post("/api/tasks/", json=task_data)
        
        assert response.status_code == 422


@pytest.mark.api
@pytest.mark.integration
class TestTaskList:
    """测试任务列表 API"""

    def test_list_tasks_empty(self, client):
        """测试空任务列表"""
        response = client.get("/api/tasks/")
        
        assert response.status_code == 200
        data = response.json()
        assert data == []

    def test_list_tasks_with_data(self, client, db_session, mock_redis):
        """测试有数据时的任务列表"""
        project = create_test_project(db_session, name="测试项目")
        create_test_task(db_session, project_id=project.id, title="任务1")
        create_test_task(db_session, project_id=project.id, title="任务2")
        
        mock_redis.get_json.return_value = None
        
        response = client.get("/api/tasks/")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2

    def test_list_tasks_caching(self, client, db_session, mock_redis):
        """测试任务列表缓存"""
        mock_redis.get_json.return_value = None
        
        project = create_test_project(db_session, name="测试项目")
        create_test_task(db_session, project_id=project.id, title="任务1")
        
        response = client.get("/api/tasks/")
        
        assert response.status_code == 200
        assert mock_redis.get_json.called


@pytest.mark.api
@pytest.mark.integration
class TestTaskSearch:
    """测试任务搜索 API"""

    def test_search_tasks_by_keyword(self, client, db_session):
        """测试按关键词搜索任务"""
        project = create_test_project(db_session, name="测试项目")
        create_test_task(db_session, project_id=project.id, title="Python开发")
        create_test_task(db_session, project_id=project.id, title="Java开发")
        create_test_task(db_session, project_id=project.id, title="测试任务")
        
        response = client.get("/api/tasks/search?keyword=Python")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1
        assert "Python" in data[0]["title"]

    def test_search_tasks_by_status(self, client, db_session):
        """测试按状态搜索任务"""
        from app.models.task import TaskStatus
        
        project = create_test_project(db_session, name="测试项目")
        create_test_task(db_session, project_id=project.id, title="任务1", status=TaskStatus.PENDING.value)
        create_test_task(db_session, project_id=project.id, title="任务2", status=TaskStatus.COMPLETED.value)
        
        response = client.get(f"/api/tasks/search?status={TaskStatus.PENDING.value}")
        
        assert response.status_code == 200
        data = response.json()
        for task in data:
            assert task["status"] == TaskStatus.PENDING.value

    def test_search_tasks_by_priority(self, client, db_session):
        """测试按优先级搜索任务"""
        project = create_test_project(db_session, name="测试项目")
        create_test_task(db_session, project_id=project.id, title="任务1", priority="high")
        create_test_task(db_session, project_id=project.id, title="任务2", priority="low")
        
        response = client.get("/api/tasks/search?priority=high")
        
        assert response.status_code == 200
        data = response.json()
        for task in data:
            assert task["priority"] == "high"

    def test_search_tasks_by_project(self, client, db_session):
        """测试按项目搜索任务"""
        project1 = create_test_project(db_session, name="项目1")
        project2 = create_test_project(db_session, name="项目2")
        create_test_task(db_session, project_id=project1.id, title="任务1")
        create_test_task(db_session, project_id=project2.id, title="任务2")
        
        response = client.get(f"/api/tasks/search?project_id={project1.id}")
        
        assert response.status_code == 200
        data = response.json()
        for task in data:
            assert task["project_id"] == project1.id

    def test_search_tasks_combined_filters(self, client, db_session):
        """测试组合条件搜索任务"""
        from app.models.task import TaskStatus
        
        project = create_test_project(db_session, name="测试项目")
        create_test_task(
            db_session, 
            project_id=project.id, 
            title="Python任务", 
            status=TaskStatus.PENDING.value,
            priority="high"
        )
        create_test_task(
            db_session, 
            project_id=project.id, 
            title="Java任务", 
            status=TaskStatus.PENDING.value,
            priority="low"
        )
        
        response = client.get(f"/api/tasks/search?keyword=Python&status={TaskStatus.PENDING.value}&priority=high")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1


@pytest.mark.api
@pytest.mark.integration
class TestTaskDetail:
    """测试任务详情 API"""

    def test_get_task_detail_success(self, client, db_session, mock_redis):
        """测试成功获取任务详情"""
        project = create_test_project(db_session, name="测试项目")
        task = create_test_task(db_session, project_id=project.id, title="测试任务")
        
        mock_redis.get_json.return_value = None
        
        response = client.get(f"/api/tasks/{task.id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == task.id
        assert data["title"] == "测试任务"
        assert "agent" in data
        assert "dependencies_detail" in data

    def test_get_task_detail_not_found(self, client):
        """测试获取不存在的任务"""
        response = client.get("/api/tasks/99999")
        
        assert response.status_code == 404

    def test_get_task_detail_with_agent(self, client, db_session, mock_redis):
        """测试获取带代理的任务详情"""
        project = create_test_project(db_session, name="测试项目")
        agent = create_test_agent(db_session, name="测试代理")
        task = create_test_task(db_session, project_id=project.id, title="测试任务", agent_id=agent.id)
        
        mock_redis.get_json.return_value = None
        
        response = client.get(f"/api/tasks/{task.id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["agent"] is not None
        assert data["agent"]["name"] == "测试代理"


@pytest.mark.api
@pytest.mark.integration
class TestTaskUpdate:
    """测试任务更新 API"""

    def test_update_task_success(self, client, db_session):
        """测试成功更新任务"""
        project = create_test_project(db_session, name="测试项目")
        task = create_test_task(db_session, project_id=project.id, title="旧标题")
        
        update_data = {
            "title": "新标题",
            "description": "新描述"
        }
        response = client.put(f"/api/tasks/{task.id}", json=update_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "新标题"
        assert data["description"] == "新描述"

    def test_update_task_not_found(self, client):
        """测试更新不存在的任务"""
        response = client.put("/api/tasks/99999", json={"title": "新标题"})
        
        assert response.status_code == 404

    def test_update_task_priority(self, client, db_session):
        """测试更新任务优先级"""
        project = create_test_project(db_session, name="测试项目")
        task = create_test_task(db_session, project_id=project.id, title="任务", priority="low")
        
        response = client.put(f"/api/tasks/{task.id}", json={"priority": "high"})
        
        assert response.status_code == 200
        data = response.json()
        assert data["priority"] == "high"

    def test_update_task_invalid_priority(self, client, db_session):
        """测试更新为无效优先级"""
        project = create_test_project(db_session, name="测试项目")
        task = create_test_task(db_session, project_id=project.id, title="任务")
        
        response = client.put(f"/api/tasks/{task.id}", json={"priority": "invalid"})
        
        assert response.status_code == 400

    def test_update_task_dependencies(self, client, db_session):
        """测试更新任务依赖"""
        project = create_test_project(db_session, name="测试项目")
        task1 = create_test_task(db_session, project_id=project.id, title="任务1")
        task2 = create_test_task(db_session, project_id=project.id, title="任务2")
        
        response = client.put(f"/api/tasks/{task2.id}", json={"dependencies": [task1.id]})
        
        assert response.status_code == 200
        data = response.json()
        assert task1.id in data["dependencies"]

    def test_update_task_self_dependency(self, client, db_session):
        """测试任务不能依赖自己"""
        project = create_test_project(db_session, name="测试项目")
        task = create_test_task(db_session, project_id=project.id, title="任务")
        
        response = client.put(f"/api/tasks/{task.id}", json={"dependencies": [task.id]})
        
        assert response.status_code == 400


@pytest.mark.api
@pytest.mark.integration
class TestTaskDelete:
    """测试任务删除 API"""

    def test_delete_task_success(self, client, db_session):
        """测试成功删除任务"""
        project = create_test_project(db_session, name="测试项目")
        task = create_test_task(db_session, project_id=project.id, title="待删除任务")
        
        response = client.delete(f"/api/tasks/{task.id}")
        
        assert response.status_code == 200
        data = response.json()
        assert "deleted successfully" in data["message"]
        
        get_response = client.get(f"/api/tasks/{task.id}")
        assert get_response.status_code == 404

    def test_delete_task_not_found(self, client):
        """测试删除不存在的任务"""
        response = client.delete("/api/tasks/99999")
        
        assert response.status_code == 404

    def test_delete_task_with_dependents(self, client, db_session):
        """测试删除被依赖的任务"""
        project = create_test_project(db_session, name="测试项目")
        task1 = create_test_task(db_session, project_id=project.id, title="任务1")
        task2 = create_test_task(db_session, project_id=project.id, title="任务2")
        
        client.put(f"/api/tasks/{task2.id}", json={"dependencies": [task1.id]})
        
        response = client.delete(f"/api/tasks/{task1.id}")
        
        assert response.status_code == 400


@pytest.mark.api
@pytest.mark.integration
class TestTaskStats:
    """测试任务统计 API"""

    def test_get_task_stats(self, client, db_session, mock_redis):
        """测试获取任务统计"""
        from app.models.task import TaskStatus
        
        project = create_test_project(db_session, name="测试项目")
        create_test_task(db_session, project_id=project.id, title="任务1", status=TaskStatus.COMPLETED.value)
        create_test_task(db_session, project_id=project.id, title="任务2", status=TaskStatus.PENDING.value)
        create_test_task(db_session, project_id=project.id, title="任务3", status=TaskStatus.IN_PROGRESS.value)
        
        mock_redis.get_json.return_value = None
        
        response = client.get("/api/tasks/stats")
        
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 3
        assert "by_status" in data
        assert "by_priority" in data
        assert "completed_rate" in data

    def test_get_task_stats_by_project(self, client, db_session, mock_redis):
        """测试按项目获取任务统计"""
        project1 = create_test_project(db_session, name="项目1")
        project2 = create_test_project(db_session, name="项目2")
        create_test_task(db_session, project_id=project1.id, title="任务1")
        create_test_task(db_session, project_id=project2.id, title="任务2")
        
        mock_redis.get_json.return_value = None
        
        response = client.get(f"/api/tasks/stats?project_id={project1.id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1


@pytest.mark.api
@pytest.mark.integration
class TestProjectTasks:
    """测试项目任务 API"""

    def test_get_project_tasks(self, client, db_session, mock_redis):
        """测试获取项目任务"""
        project = create_test_project(db_session, name="测试项目")
        create_test_task(db_session, project_id=project.id, title="任务1")
        create_test_task(db_session, project_id=project.id, title="任务2")
        
        mock_redis.get_json.return_value = None
        
        response = client.get(f"/api/tasks/project/{project.id}")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2

    def test_get_project_tasks_empty(self, client, db_session, mock_redis):
        """测试获取空项目任务"""
        project = create_test_project(db_session, name="空项目")
        
        mock_redis.get_json.return_value = None
        
        response = client.get(f"/api/tasks/project/{project.id}")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 0


@pytest.mark.api
@pytest.mark.integration
class TestTaskPerformance:
    """测试任务 API 性能"""

    def test_list_tasks_performance(self, client, db_session, mock_redis):
        """测试任务列表性能"""
        project = create_test_project(db_session, name="测试项目")
        for i in range(100):
            create_test_task(db_session, project_id=project.id, title=f"任务{i}")
        
        mock_redis.get_json.return_value = None
        
        import time
        start_time = time.time()
        response = client.get("/api/tasks/")
        end_time = time.time()
        
        assert response.status_code == 200
        assert end_time - start_time < 3.0

    def test_search_tasks_performance(self, client, db_session):
        """测试任务搜索性能"""
        project = create_test_project(db_session, name="测试项目")
        for i in range(50):
            create_test_task(db_session, project_id=project.id, title=f"搜索任务{i}")
        
        import time
        start_time = time.time()
        response = client.get("/api/tasks/search?keyword=搜索")
        end_time = time.time()
        
        assert response.status_code == 200
        assert end_time - start_time < 2.0
