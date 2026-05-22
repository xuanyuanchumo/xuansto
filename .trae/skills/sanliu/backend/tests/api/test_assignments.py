import pytest
from tests.conftest import create_test_project, create_test_task, create_test_agent, create_test_assignment


@pytest.mark.api
class TestAssignmentsAPI:

    def test_create_assignment_success(self, client, db_session):
        agent = create_test_agent(db_session, name="测试代理", max_load=5)
        project = create_test_project(db_session, name="测试项目")
        task = create_test_task(db_session, project_id=project.id, title="测试任务")
        
        assignment_data = {
            "agent_id": agent.id,
            "task_id": task.id,
            "task_description": "完成测试任务"
        }
        response = client.post("/api/assignments/", json=assignment_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["agent_id"] == agent.id
        assert data["task_id"] == task.id
        assert data["status"] == "assigned"

    def test_create_assignment_agent_not_found(self, client, db_session):
        assignment_data = {
            "agent_id": 99999,
            "task_description": "测试任务"
        }
        response = client.post("/api/assignments/", json=assignment_data)
        assert response.status_code == 404

    def test_create_assignment_task_not_found(self, client, db_session):
        agent = create_test_agent(db_session, name="测试代理")
        
        assignment_data = {
            "agent_id": agent.id,
            "task_id": 99999,
            "task_description": "测试任务"
        }
        response = client.post("/api/assignments/", json=assignment_data)
        assert response.status_code == 404

    def test_create_assignment_task_already_assigned(self, client, db_session):
        agent1 = create_test_agent(db_session, name="代理1", max_load=5)
        agent2 = create_test_agent(db_session, name="代理2", max_load=5)
        project = create_test_project(db_session, name="测试项目")
        task = create_test_task(db_session, project_id=project.id, title="测试任务")
        
        create_test_assignment(db_session, task_id=task.id, agent_id=agent1.id, status="assigned")
        
        assignment_data = {
            "agent_id": agent2.id,
            "task_id": task.id,
            "task_description": "测试任务"
        }
        response = client.post("/api/assignments/", json=assignment_data)
        assert response.status_code == 400

    def test_create_assignment_agent_max_load_reached(self, client, db_session):
        agent = create_test_agent(db_session, name="测试代理", current_load=5, max_load=5)
        
        assignment_data = {
            "agent_id": agent.id,
            "task_description": "测试任务"
        }
        response = client.post("/api/assignments/", json=assignment_data)
        assert response.status_code == 400

    def test_list_assignments_empty(self, client):
        response = client.get("/api/assignments/")
        assert response.status_code == 200
        data = response.json()
        assert data == []

    def test_list_assignments_with_data(self, client, db_session):
        agent = create_test_agent(db_session, name="测试代理", max_load=5)
        project = create_test_project(db_session, name="测试项目")
        task = create_test_task(db_session, project_id=project.id, title="测试任务")
        
        create_test_assignment(db_session, task_id=task.id, agent_id=agent.id)
        
        response = client.get("/api/assignments/")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1

    def test_list_assignments_filter_by_agent(self, client, db_session):
        agent1 = create_test_agent(db_session, name="代理1", max_load=5)
        agent2 = create_test_agent(db_session, name="代理2", max_load=5)
        
        create_test_assignment(db_session, agent_id=agent1.id, task_description="任务1")
        create_test_assignment(db_session, agent_id=agent2.id, task_description="任务2")
        
        response = client.get(f"/api/assignments/?agent_id={agent1.id}")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["agent_id"] == agent1.id

    def test_list_assignments_filter_by_status(self, client, db_session):
        agent = create_test_agent(db_session, name="测试代理", max_load=10)
        
        create_test_assignment(db_session, agent_id=agent.id, task_description="任务1", status="assigned")
        create_test_assignment(db_session, agent_id=agent.id, task_description="任务2", status="completed")
        
        response = client.get("/api/assignments/?status=assigned")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["status"] == "assigned"

    def test_list_assignments_invalid_status(self, client):
        response = client.get("/api/assignments/?status=invalid_status")
        assert response.status_code == 400

    def test_get_active_assignments(self, client, db_session):
        agent = create_test_agent(db_session, name="测试代理", max_load=10)
        
        create_test_assignment(db_session, agent_id=agent.id, task_description="任务1", status="assigned")
        create_test_assignment(db_session, agent_id=agent.id, task_description="任务2", status="completed")
        create_test_assignment(db_session, agent_id=agent.id, task_description="任务3", status="assigned")
        
        response = client.get("/api/assignments/active")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2

    def test_get_assignment_by_id(self, client, db_session):
        agent = create_test_agent(db_session, name="测试代理", max_load=5)
        assignment = create_test_assignment(db_session, agent_id=agent.id, task_description="测试任务")
        
        response = client.get(f"/api/assignments/{assignment.id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == assignment.id

    def test_get_assignment_not_found(self, client):
        response = client.get("/api/assignments/99999")
        assert response.status_code == 404

    def test_get_assignment_detail(self, client, db_session):
        agent = create_test_agent(db_session, name="测试代理名称")
        project = create_test_project(db_session, name="测试项目")
        task = create_test_task(db_session, project_id=project.id, title="测试任务标题")
        
        assignment = create_test_assignment(
            db_session, 
            task_id=task.id, 
            agent_id=agent.id, 
            task_description="测试任务描述"
        )
        
        response = client.get(f"/api/assignments/{assignment.id}/detail")
        assert response.status_code == 200
        data = response.json()
        assert data["agent_name"] == "测试代理名称"
        assert data["task_title"] == "测试任务标题"

    def test_get_assignment_stats(self, client, db_session):
        agent = create_test_agent(db_session, name="测试代理", max_load=10)
        
        create_test_assignment(db_session, agent_id=agent.id, task_description="任务1", status="assigned")
        create_test_assignment(db_session, agent_id=agent.id, task_description="任务2", status="completed")
        create_test_assignment(db_session, agent_id=agent.id, task_description="任务3", status="in_progress")
        
        response = client.get("/api/assignments/stats")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 3
        assert data["active_assignments"] == 2

    def test_update_assignment(self, client, db_session):
        agent = create_test_agent(db_session, name="测试代理", max_load=5)
        assignment = create_test_assignment(db_session, agent_id=agent.id, task_description="原任务描述")
        
        update_data = {"task_description": "新任务描述"}
        response = client.put(f"/api/assignments/{assignment.id}", json=update_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["task_description"] == "新任务描述"

    def test_update_assignment_status(self, client, db_session):
        agent = create_test_agent(db_session, name="测试代理", max_load=5)
        assignment = create_test_assignment(db_session, agent_id=agent.id, task_description="测试任务")
        
        update_data = {"status": "in_progress"}
        response = client.put(f"/api/assignments/{assignment.id}", json=update_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "in_progress"

    def test_update_assignment_invalid_status(self, client, db_session):
        agent = create_test_agent(db_session, name="测试代理", max_load=5)
        assignment = create_test_assignment(db_session, agent_id=agent.id, task_description="测试任务")
        
        update_data = {"status": "invalid_status"}
        response = client.put(f"/api/assignments/{assignment.id}", json=update_data)
        assert response.status_code == 400

    def test_complete_assignment(self, client, db_session):
        agent = create_test_agent(db_session, name="测试代理", current_load=1, max_load=5)
        project = create_test_project(db_session, name="测试项目")
        task = create_test_task(db_session, project_id=project.id, title="测试任务")
        assignment = create_test_assignment(
            db_session, 
            task_id=task.id, 
            agent_id=agent.id, 
            task_description="测试任务",
            status="assigned"
        )
        
        response = client.put(f"/api/assignments/{assignment.id}/complete")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "completed"

    def test_complete_assignment_already_completed(self, client, db_session):
        agent = create_test_agent(db_session, name="测试代理", max_load=5)
        assignment = create_test_assignment(
            db_session, 
            agent_id=agent.id, 
            task_description="测试任务",
            status="completed"
        )
        
        response = client.put(f"/api/assignments/{assignment.id}/complete")
        assert response.status_code == 400

    def test_cancel_assignment(self, client, db_session):
        agent = create_test_agent(db_session, name="测试代理", current_load=1, max_load=5)
        assignment = create_test_assignment(
            db_session, 
            agent_id=agent.id, 
            task_description="测试任务",
            status="assigned"
        )
        
        response = client.put(f"/api/assignments/{assignment.id}/cancel")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "cancelled"

    def test_cancel_assignment_already_completed(self, client, db_session):
        agent = create_test_agent(db_session, name="测试代理", max_load=5)
        assignment = create_test_assignment(
            db_session, 
            agent_id=agent.id, 
            task_description="测试任务",
            status="completed"
        )
        
        response = client.put(f"/api/assignments/{assignment.id}/cancel")
        assert response.status_code == 400

    def test_delete_assignment_completed(self, client, db_session):
        agent = create_test_agent(db_session, name="测试代理", max_load=5)
        assignment = create_test_assignment(
            db_session, 
            agent_id=agent.id, 
            task_description="测试任务",
            status="completed"
        )
        
        response = client.delete(f"/api/assignments/{assignment.id}")
        assert response.status_code == 200

    def test_delete_assignment_active(self, client, db_session):
        agent = create_test_agent(db_session, name="测试代理", max_load=5)
        assignment = create_test_assignment(
            db_session, 
            agent_id=agent.id, 
            task_description="测试任务",
            status="assigned"
        )
        
        response = client.delete(f"/api/assignments/{assignment.id}")
        assert response.status_code == 400
