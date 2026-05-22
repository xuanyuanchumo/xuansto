import pytest
from tests.conftest import create_test_project, create_test_skill_call


@pytest.mark.api
class TestTransparencyAPI:

    def test_get_transparency_report_empty(self, client, db_session):
        project = create_test_project(db_session, name="测试项目")
        
        response = client.get(f"/api/transparency/report/project/{project.id}")
        assert response.status_code == 200
        data = response.json()
        assert data["project_id"] == project.id
        assert data["statistics"]["total_skill_calls"] == 0
        assert data["transparency_score"] == 0

    def test_get_transparency_report_with_skill_calls(self, client, db_session):
        project = create_test_project(db_session, name="测试项目")
        
        create_test_skill_call(
            db_session, 
            skill_name="skill_a", 
            status="completed",
            details={"project_id": project.id}
        )
        create_test_skill_call(
            db_session, 
            skill_name="skill_b", 
            status="completed",
            details={"project_id": project.id}
        )
        
        response = client.get(f"/api/transparency/report/project/{project.id}")
        assert response.status_code == 200
        data = response.json()
        assert data["project_id"] == project.id
        assert data["statistics"]["total_skill_calls"] == 2
        assert "generated_at" in data
        assert "transparency_score" in data

    def test_transparency_score_calculation(self, client, db_session):
        project = create_test_project(db_session, name="测试项目")
        
        create_test_skill_call(
            db_session, 
            skill_name="skill_a", 
            status="completed",
            details={"project_id": project.id}
        )
        
        response = client.get(f"/api/transparency/report/project/{project.id}")
        assert response.status_code == 200
        data = response.json()
        assert data["transparency_score"] >= 0
        assert data["transparency_score"] <= 100

    def test_transparency_report_statistics_structure(self, client, db_session):
        project = create_test_project(db_session, name="测试项目")
        
        create_test_skill_call(
            db_session, 
            skill_name="skill_a", 
            status="completed",
            details={"project_id": project.id}
        )
        
        response = client.get(f"/api/transparency/report/project/{project.id}")
        assert response.status_code == 200
        data = response.json()
        
        assert "statistics" in data
        stats = data["statistics"]
        assert "total_skill_calls" in stats
        assert "total_decisions" in stats
        assert "total_io_traces" in stats
        assert "total_code_changes" in stats
        assert "total_artifacts" in stats
        assert "decision_types" in stats
