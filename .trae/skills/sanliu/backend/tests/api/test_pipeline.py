import pytest
from tests.conftest import create_test_project


@pytest.mark.api
class TestPipelineAPI:

    def test_initialize_pipeline(self, client, db_session):
        project = create_test_project(db_session, name="测试项目")
        
        response = client.post(f"/api/pipeline/project/{project.id}/initialize")
        assert response.status_code == 200
        data = response.json()
        assert data["project_id"] == project.id
        assert "stages_created" in data

    def test_initialize_pipeline_project_not_found(self, client):
        response = client.post("/api/pipeline/project/99999/initialize")
        assert response.status_code == 404

    def test_initialize_pipeline_already_initialized(self, client, db_session):
        project = create_test_project(db_session, name="测试项目")
        
        client.post(f"/api/pipeline/project/{project.id}/initialize")
        response = client.post(f"/api/pipeline/project/{project.id}/initialize")
        assert response.status_code == 400

    def test_get_pipeline_status(self, client, db_session):
        project = create_test_project(db_session, name="测试项目")
        client.post(f"/api/pipeline/project/{project.id}/initialize")
        
        response = client.get(f"/api/pipeline/project/{project.id}")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_get_pipeline_status_project_not_found(self, client):
        response = client.get("/api/pipeline/project/99999")
        assert response.status_code == 404

    def test_get_pipeline_summary(self, client, db_session):
        project = create_test_project(db_session, name="测试项目")
        client.post(f"/api/pipeline/project/{project.id}/initialize")
        
        response = client.get(f"/api/pipeline/project/{project.id}/summary")
        assert response.status_code == 200
        data = response.json()
        assert data["project_id"] == project.id
        assert "total_stages" in data
        assert "completed_stages" in data
        assert "progress_percentage" in data

    def test_get_pipeline_summary_not_initialized(self, client, db_session):
        project = create_test_project(db_session, name="测试项目")
        
        response = client.get(f"/api/pipeline/project/{project.id}/summary")
        assert response.status_code == 400

    def test_start_stage(self, client, db_session):
        project = create_test_project(db_session, name="测试项目")
        client.post(f"/api/pipeline/project/{project.id}/initialize")
        
        response = client.post(
            f"/api/pipeline/project/{project.id}/stage/requirement/start",
            json={"triggered_by": "test_user"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "running"

    def test_complete_stage(self, client, db_session):
        project = create_test_project(db_session, name="测试项目")
        client.post(f"/api/pipeline/project/{project.id}/initialize")
        client.post(f"/api/pipeline/project/{project.id}/stage/requirement/start")
        
        response = client.post(
            f"/api/pipeline/project/{project.id}/stage/requirement/complete",
            json={"output_artifacts": {"doc": "requirement.md"}, "triggered_by": "test_user"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "completed"

    def test_fail_stage(self, client, db_session):
        project = create_test_project(db_session, name="测试项目")
        client.post(f"/api/pipeline/project/{project.id}/initialize")
        client.post(f"/api/pipeline/project/{project.id}/stage/requirement/start")
        
        response = client.post(
            f"/api/pipeline/project/{project.id}/stage/requirement/fail?error_message=测试失败"
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "failed"

    def test_skip_stage(self, client, db_session):
        project = create_test_project(db_session, name="测试项目")
        client.post(f"/api/pipeline/project/{project.id}/initialize")
        
        response = client.post(
            f"/api/pipeline/project/{project.id}/stage/requirement/skip?reason=测试跳过"
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "skipped"

    def test_reset_pipeline(self, client, db_session):
        project = create_test_project(db_session, name="测试项目")
        client.post(f"/api/pipeline/project/{project.id}/initialize")
        client.post(f"/api/pipeline/project/{project.id}/stage/requirement/start")
        
        response = client.post(f"/api/pipeline/project/{project.id}/reset")
        assert response.status_code == 200
        data = response.json()
        assert "reset_at" in data
