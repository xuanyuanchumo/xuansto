import pytest
from tests.conftest import create_test_project, create_test_task, create_test_agent, create_test_skill_call


@pytest.mark.api
class TestStatisticsAPI:

    def test_get_project_statistics_empty(self, client, mock_redis):
        mock_redis.get_json.return_value = None
        response = client.get("/api/statistics/projects")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0
        assert data["status_distribution"] == {}

    def test_get_project_statistics_with_data(self, client, db_session, mock_redis):
        from app.models.project import ProjectStatus
        mock_redis.get_json.return_value = None
        
        create_test_project(db_session, name="项目1", status=ProjectStatus.REQUIREMENT.value)
        create_test_project(db_session, name="项目2", status=ProjectStatus.DEVELOPMENT.value)
        create_test_project(db_session, name="项目3", status=ProjectStatus.REQUIREMENT.value)
        
        response = client.get("/api/statistics/projects")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 3
        assert "REQUIREMENT" in data["status_distribution"]
        assert "DEVELOPMENT" in data["status_distribution"]

    def test_get_project_statistics_cached(self, client, mock_redis):
        cached_data = {"total": 5, "status_distribution": {"REQUIREMENT": 5}}
        mock_redis.get_json.return_value = cached_data
        
        response = client.get("/api/statistics/projects")
        assert response.status_code == 200
        data = response.json()
        assert data == cached_data

    def test_get_task_statistics_empty(self, client, mock_redis):
        mock_redis.get_json.return_value = None
        response = client.get("/api/statistics/tasks")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0
        assert data["completed"] == 0
        assert data["completion_rate"] == 0

    def test_get_task_statistics_with_data(self, client, db_session, mock_redis):
        from app.models.task import TaskStatus
        mock_redis.get_json.return_value = None
        
        project = create_test_project(db_session, name="测试项目")
        create_test_task(db_session, project_id=project.id, title="任务1", status=TaskStatus.COMPLETED.value)
        create_test_task(db_session, project_id=project.id, title="任务2", status=TaskStatus.PENDING.value)
        create_test_task(db_session, project_id=project.id, title="任务3", status=TaskStatus.COMPLETED.value)
        
        response = client.get("/api/statistics/tasks")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 3
        assert data["completed"] == 2
        assert data["completion_rate"] == 66.67

    def test_get_skill_call_statistics_empty(self, client, mock_redis):
        mock_redis.get_json.return_value = None
        response = client.get("/api/statistics/skill-calls")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0
        assert data["successful"] == 0
        assert data["success_rate"] == 0

    def test_get_skill_call_statistics_with_data(self, client, db_session, mock_redis):
        mock_redis.get_json.return_value = None
        
        create_test_skill_call(db_session, skill_name="skill_a", status="completed")
        create_test_skill_call(db_session, skill_name="skill_b", status="completed")
        create_test_skill_call(db_session, skill_name="skill_a", status="failed")
        
        response = client.get("/api/statistics/skill-calls")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 3
        assert data["successful"] == 2
        assert data["success_rate"] == 66.67
        assert "skill_a" in data["skill_distribution"]
        assert "skill_b" in data["skill_distribution"]

    def test_get_agent_statistics_empty(self, client, mock_redis):
        mock_redis.get_json.return_value = None
        response = client.get("/api/statistics/agents")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0
        assert data["active"] == 0

    def test_get_agent_statistics_with_data(self, client, db_session, mock_redis):
        mock_redis.get_json.return_value = None
        
        create_test_agent(db_session, name="代理1", status="idle", current_load=0, max_load=5)
        create_test_agent(db_session, name="代理2", status="busy", current_load=3, max_load=5)
        create_test_agent(db_session, name="代理3", status="busy", current_load=2, max_load=10)
        
        response = client.get("/api/statistics/agents")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 3
        assert data["active"] == 2
        assert len(data["workload"]) == 3

    def test_get_agent_statistics_workload_calculation(self, client, db_session, mock_redis):
        mock_redis.get_json.return_value = None
        
        create_test_agent(db_session, name="代理1", current_load=2, max_load=10)
        
        response = client.get("/api/statistics/agents")
        assert response.status_code == 200
        data = response.json()
        assert len(data["workload"]) == 1
        assert data["workload"][0]["utilization"] == 20.0

    def test_get_agent_statistics_zero_max_load(self, client, db_session, mock_redis):
        mock_redis.get_json.return_value = None
        
        create_test_agent(db_session, name="代理1", current_load=0, max_load=0)
        
        response = client.get("/api/statistics/agents")
        assert response.status_code == 200
        data = response.json()
        assert data["workload"][0]["utilization"] == 0
