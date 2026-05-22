import pytest
from tests.conftest import create_test_project, create_test_skill_call


@pytest.mark.api
class TestArtifactsAPI:

    def test_create_artifact_success(self, client, db_session):
        project = create_test_project(db_session, name="测试项目")
        
        artifact_data = {
            "project_id": project.id,
            "artifact_type": "document",
            "name": "需求文档",
            "content": "这是需求文档内容",
            "metadata": {"version": "1.0"}
        }
        response = client.post("/api/artifacts/", json=artifact_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "需求文档"
        assert data["artifact_type"] == "document"
        assert data["project_id"] == project.id

    def test_create_artifact_with_skill_call(self, client, db_session):
        project = create_test_project(db_session, name="测试项目")
        skill_call = create_test_skill_call(db_session, skill_name="test_skill")
        
        artifact_data = {
            "project_id": project.id,
            "skill_call_id": skill_call.id,
            "artifact_type": "code",
            "name": "生成的代码"
        }
        response = client.post("/api/artifacts/", json=artifact_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["skill_call_id"] == skill_call.id

    def test_get_artifacts_by_project(self, client, db_session):
        from app.models.intermediate_artifact import IntermediateArtifact
        
        project = create_test_project(db_session, name="测试项目")
        
        a1 = IntermediateArtifact(project_id=project.id, artifact_type="doc", name="文档1")
        a2 = IntermediateArtifact(project_id=project.id, artifact_type="code", name="代码1")
        db_session.add_all([a1, a2])
        db_session.commit()
        
        response = client.get(f"/api/artifacts/project/{project.id}")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2

    def test_get_artifacts_by_project_with_type_filter(self, client, db_session):
        from app.models.intermediate_artifact import IntermediateArtifact
        
        project = create_test_project(db_session, name="测试项目")
        
        a1 = IntermediateArtifact(project_id=project.id, artifact_type="doc", name="文档1")
        a2 = IntermediateArtifact(project_id=project.id, artifact_type="code", name="代码1")
        db_session.add_all([a1, a2])
        db_session.commit()
        
        response = client.get(f"/api/artifacts/project/{project.id}?artifact_type=doc")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["artifact_type"] == "doc"

    def test_get_artifact_by_id(self, client, db_session):
        from app.models.intermediate_artifact import IntermediateArtifact
        
        project = create_test_project(db_session, name="测试项目")
        artifact = IntermediateArtifact(
            project_id=project.id, 
            artifact_type="doc", 
            name="测试文档",
            content="文档内容"
        )
        db_session.add(artifact)
        db_session.commit()
        db_session.refresh(artifact)
        
        response = client.get(f"/api/artifacts/{artifact.id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == artifact.id
        assert data["name"] == "测试文档"
        assert data["content"] == "文档内容"

    def test_get_artifact_not_found(self, client):
        response = client.get("/api/artifacts/99999")
        assert response.status_code == 404

    def test_create_artifact_with_file_path(self, client, db_session):
        project = create_test_project(db_session, name="测试项目")
        
        artifact_data = {
            "project_id": project.id,
            "artifact_type": "file",
            "name": "配置文件",
            "file_path": "/path/to/config.json"
        }
        response = client.post("/api/artifacts/", json=artifact_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["file_path"] == "/path/to/config.json"
