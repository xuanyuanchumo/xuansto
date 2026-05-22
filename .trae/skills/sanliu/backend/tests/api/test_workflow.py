import pytest
from tests.conftest import create_test_project, create_test_task


@pytest.mark.api
class TestWorkflowAPI:

    def test_update_project_status(self, client, db_session):
        project = create_test_project(db_session, name="测试项目", status="REQUIREMENT")
        
        update_data = {
            "status": "DESIGN",
            "operator": "test_user",
            "comment": "状态更新测试"
        }
        response = client.put(f"/api/workflow/project/{project.id}/status", json=update_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "DESIGN"

    def test_update_project_status_not_found(self, client):
        update_data = {"status": "DESIGN"}
        response = client.put("/api/workflow/project/99999/status", json=update_data)
        assert response.status_code == 404

    def test_update_project_status_invalid_transition(self, client, db_session):
        project = create_test_project(db_session, name="测试项目", status="REQUIREMENT")
        
        update_data = {"status": "COMPLETED"}
        response = client.put(f"/api/workflow/project/{project.id}/status", json=update_data)
        assert response.status_code == 400

    def test_update_task_status(self, client, db_session):
        project = create_test_project(db_session, name="测试项目")
        task = create_test_task(db_session, project_id=project.id, title="测试任务", status="PENDING")
        
        update_data = {
            "status": "IN_PROGRESS",
            "operator": "test_user"
        }
        response = client.put(f"/api/workflow/task/{task.id}/status", json=update_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "IN_PROGRESS"

    def test_update_task_status_not_found(self, client):
        update_data = {"status": "IN_PROGRESS"}
        response = client.put("/api/workflow/task/99999/status", json=update_data)
        assert response.status_code == 404

    def test_update_task_status_to_completed(self, client, db_session):
        project = create_test_project(db_session, name="测试项目")
        task = create_test_task(db_session, project_id=project.id, title="测试任务", status="IN_PROGRESS")
        
        update_data = {"status": "COMPLETED"}
        response = client.put(f"/api/workflow/task/{task.id}/status", json=update_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "COMPLETED"

    def test_get_status_history_project(self, client, db_session):
        project = create_test_project(db_session, name="测试项目")
        
        response = client.get(f"/api/workflow/history/project/{project.id}")
        assert response.status_code == 200
        data = response.json()
        assert data["entity_type"] == "project"
        assert data["entity_id"] == project.id
        assert "history" in data

    def test_get_status_history_task(self, client, db_session):
        project = create_test_project(db_session, name="测试项目")
        task = create_test_task(db_session, project_id=project.id, title="测试任务")
        
        response = client.get(f"/api/workflow/history/task/{task.id}")
        assert response.status_code == 200
        data = response.json()
        assert data["entity_type"] == "task"
        assert data["entity_id"] == task.id

    def test_get_status_history_invalid_entity_type(self, client, db_session):
        project = create_test_project(db_session, name="测试项目")
        
        response = client.get(f"/api/workflow/history/invalid/{project.id}")
        assert response.status_code == 400

    def test_check_task_dependencies_no_dependencies(self, client, db_session):
        project = create_test_project(db_session, name="测试项目")
        task = create_test_task(db_session, project_id=project.id, title="测试任务", dependencies=[])
        
        response = client.post("/api/workflow/task/check-dependencies", json={"task_id": task.id})
        
        assert response.status_code == 200
        data = response.json()
        assert data["task_id"] == task.id
        assert data["all_dependencies_completed"] == True

    def test_check_task_dependencies_not_found(self, client):
        response = client.post("/api/workflow/task/check-dependencies", json={"task_id": 99999})
        assert response.status_code == 404

    def test_get_project_allowed_transitions(self, client, db_session):
        project = create_test_project(db_session, name="测试项目", status="REQUIREMENT")
        
        response = client.get(f"/api/workflow/project/{project.id}/allowed-transitions")
        assert response.status_code == 200
        data = response.json()
        assert "current_status" in data
        assert "allowed_transitions" in data

    def test_get_project_allowed_transitions_not_found(self, client):
        response = client.get("/api/workflow/project/99999/allowed-transitions")
        assert response.status_code == 404

    def test_get_task_allowed_transitions(self, client, db_session):
        project = create_test_project(db_session, name="测试项目")
        task = create_test_task(db_session, project_id=project.id, title="测试任务", status="PENDING")
        
        response = client.get(f"/api/workflow/task/{task.id}/allowed-transitions")
        assert response.status_code == 200
        data = response.json()
        assert "current_status" in data
        assert "allowed_transitions" in data

    def test_get_task_allowed_transitions_not_found(self, client):
        response = client.get("/api/workflow/task/99999/allowed-transitions")
        assert response.status_code == 404
