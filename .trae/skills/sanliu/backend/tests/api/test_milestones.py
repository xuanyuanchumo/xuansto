import pytest
from datetime import datetime, timedelta
from tests.conftest import create_test_project


@pytest.mark.api
class TestMilestonesAPI:

    def test_create_milestone_success(self, client, db_session):
        project = create_test_project(db_session, name="测试项目")
        
        milestone_data = {
            "project_id": project.id,
            "name": "里程碑1",
            "description": "测试里程碑",
            "planned_date": (datetime.utcnow() + timedelta(days=7)).isoformat()
        }
        response = client.post("/api/milestones/", json=milestone_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "里程碑1"
        assert data["project_id"] == project.id
        assert data["status"] == "pending"

    def test_create_milestone_project_not_found(self, client):
        milestone_data = {
            "project_id": 99999,
            "name": "里程碑"
        }
        response = client.post("/api/milestones/", json=milestone_data)
        assert response.status_code == 404

    def test_list_milestones_empty(self, client):
        response = client.get("/api/milestones/")
        assert response.status_code == 200
        data = response.json()
        assert data == []

    def test_list_milestones_with_data(self, client, db_session):
        from app.models.milestone import Milestone
        
        project = create_test_project(db_session, name="测试项目")
        
        m1 = Milestone(project_id=project.id, name="里程碑1")
        m2 = Milestone(project_id=project.id, name="里程碑2")
        db_session.add_all([m1, m2])
        db_session.commit()
        
        response = client.get("/api/milestones/")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2

    def test_get_milestone_by_id(self, client, db_session):
        from app.models.milestone import Milestone
        
        project = create_test_project(db_session, name="测试项目")
        milestone = Milestone(project_id=project.id, name="测试里程碑")
        db_session.add(milestone)
        db_session.commit()
        db_session.refresh(milestone)
        
        response = client.get(f"/api/milestones/{milestone.id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == milestone.id
        assert data["name"] == "测试里程碑"

    def test_get_milestone_not_found(self, client):
        response = client.get("/api/milestones/99999")
        assert response.status_code == 404

    def test_update_milestone(self, client, db_session):
        from app.models.milestone import Milestone
        
        project = create_test_project(db_session, name="测试项目")
        milestone = Milestone(project_id=project.id, name="原名称")
        db_session.add(milestone)
        db_session.commit()
        db_session.refresh(milestone)
        
        update_data = {"name": "新名称"}
        response = client.put(f"/api/milestones/{milestone.id}", json=update_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "新名称"

    def test_update_milestone_status(self, client, db_session):
        from app.models.milestone import Milestone
        
        project = create_test_project(db_session, name="测试项目")
        milestone = Milestone(project_id=project.id, name="里程碑")
        db_session.add(milestone)
        db_session.commit()
        db_session.refresh(milestone)
        
        update_data = {"status": "in_progress"}
        response = client.put(f"/api/milestones/{milestone.id}", json=update_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "in_progress"

    def test_delete_milestone(self, client, db_session):
        from app.models.milestone import Milestone
        
        project = create_test_project(db_session, name="测试项目")
        milestone = Milestone(project_id=project.id, name="待删除里程碑")
        db_session.add(milestone)
        db_session.commit()
        db_session.refresh(milestone)
        
        response = client.delete(f"/api/milestones/{milestone.id}")
        assert response.status_code == 200

    def test_complete_milestone(self, client, db_session):
        from app.models.milestone import Milestone
        
        project = create_test_project(db_session, name="测试项目")
        milestone = Milestone(project_id=project.id, name="里程碑", status="pending")
        db_session.add(milestone)
        db_session.commit()
        db_session.refresh(milestone)
        
        response = client.put(f"/api/milestones/{milestone.id}/complete")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "completed"
        assert data["completed_date"] is not None

    def test_get_project_milestones(self, client, db_session):
        from app.models.milestone import Milestone
        
        project = create_test_project(db_session, name="测试项目")
        
        m1 = Milestone(project_id=project.id, name="里程碑1")
        m2 = Milestone(project_id=project.id, name="里程碑2")
        db_session.add_all([m1, m2])
        db_session.commit()
        
        response = client.get(f"/api/milestones/project/{project.id}")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2

    def test_get_project_milestones_project_not_found(self, client):
        response = client.get("/api/milestones/project/99999")
        assert response.status_code == 404
