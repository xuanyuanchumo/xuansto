import pytest
from tests.conftest import create_test_project, create_test_task


@pytest.mark.api
class TestReportsAPI:

    def test_generate_project_report(self, client, db_session):
        project = create_test_project(db_session, name="测试项目", description="测试描述")
        
        response = client.get(f"/api/reports/project/{project.id}")
        assert response.status_code == 200
        data = response.json()
        assert data["project_id"] == project.id
        assert data["project_name"] == "测试项目"
        assert "generated_at" in data
        assert "content" in data

    def test_generate_project_report_not_found(self, client):
        response = client.get("/api/reports/project/99999")
        assert response.status_code == 404

    def test_generate_project_report_with_tasks(self, client, db_session):
        from app.models.task import TaskStatus
        
        project = create_test_project(db_session, name="测试项目")
        create_test_task(db_session, project_id=project.id, title="任务1", status=TaskStatus.COMPLETED.value)
        create_test_task(db_session, project_id=project.id, title="任务2", status=TaskStatus.PENDING.value)
        create_test_task(db_session, project_id=project.id, title="任务3", status=TaskStatus.IN_PROGRESS.value)
        
        response = client.get(f"/api/reports/project/{project.id}")
        assert response.status_code == 200
        data = response.json()
        assert data["project_id"] == project.id
        assert "content" in data

    def test_generate_project_report_empty_project(self, client, db_session):
        project = create_test_project(db_session, name="空项目")
        
        response = client.get(f"/api/reports/project/{project.id}")
        assert response.status_code == 200
        data = response.json()
        assert data["project_id"] == project.id
        assert "content" in data

    def test_report_content_structure(self, client, db_session):
        project = create_test_project(
            db_session, 
            name="测试项目", 
            description="项目描述",
            tech_stack=["Python", "FastAPI"]
        )
        
        response = client.get(f"/api/reports/project/{project.id}")
        assert response.status_code == 200
        data = response.json()
        
        content = data["content"]
        assert isinstance(content, str)
        assert "测试项目" in content

    def test_report_with_milestones(self, client, db_session):
        from app.models.milestone import Milestone
        from datetime import datetime, timedelta
        
        project = create_test_project(db_session, name="测试项目")
        
        milestone = Milestone(
            project_id=project.id,
            name="里程碑1",
            description="测试里程碑",
            planned_date=datetime.utcnow() + timedelta(days=7),
            status="pending"
        )
        db_session.add(milestone)
        db_session.commit()
        
        response = client.get(f"/api/reports/project/{project.id}")
        assert response.status_code == 200
        data = response.json()
        assert "content" in data
