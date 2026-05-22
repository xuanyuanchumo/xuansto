import pytest
from tests.conftest import create_test_department, create_test_agent, create_test_project, create_test_task


@pytest.mark.api
class TestDepartmentsAPI:

    def test_create_department_success(self, client, db_session):
        department_data = {
            "name": "工程部",
            "pinyin": "GCB",
            "level": "一级"
        }
        response = client.post("/api/departments/", json=department_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "工程部"
        assert data["pinyin"] == "GCB"
        assert data["level"] == "一级"

    def test_create_department_with_parent(self, client, db_session):
        parent = create_test_department(db_session, name="总部门", pinyin="ZBM")
        
        department_data = {
            "name": "子部门",
            "pinyin": "ZBM",
            "parent_id": parent.id
        }
        response = client.post("/api/departments/", json=department_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["parent_id"] == parent.id

    def test_create_department_duplicate_name(self, client, db_session):
        create_test_department(db_session, name="工程部", pinyin="GCB1")
        
        department_data = {
            "name": "工程部",
            "pinyin": "GCB2"
        }
        response = client.post("/api/departments/", json=department_data)
        assert response.status_code == 409

    def test_create_department_duplicate_pinyin(self, client, db_session):
        create_test_department(db_session, name="部门1", pinyin="GCB")
        
        department_data = {
            "name": "部门2",
            "pinyin": "GCB"
        }
        response = client.post("/api/departments/", json=department_data)
        assert response.status_code == 409

    def test_create_department_parent_not_found(self, client, db_session):
        department_data = {
            "name": "子部门",
            "pinyin": "ZBM",
            "parent_id": 99999
        }
        response = client.post("/api/departments/", json=department_data)
        assert response.status_code == 404

    def test_list_departments_empty(self, client):
        response = client.get("/api/departments/")
        assert response.status_code == 200
        data = response.json()
        assert data == []

    def test_list_departments_with_data(self, client, db_session):
        create_test_department(db_session, name="部门1", pinyin="BM1")
        create_test_department(db_session, name="部门2", pinyin="BM2")
        
        response = client.get("/api/departments/")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2

    def test_list_departments_filter_by_level(self, client, db_session):
        create_test_department(db_session, name="部门1", pinyin="BM1", level="一级")
        create_test_department(db_session, name="部门2", pinyin="BM2", level="二级")
        
        response = client.get("/api/departments/?level=一级")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["level"] == "一级"

    def test_get_department_tree(self, client, db_session):
        parent = create_test_department(db_session, name="父部门", pinyin="FBM")
        create_test_department(db_session, name="子部门1", pinyin="ZBM1", parent_id=parent.id)
        create_test_department(db_session, name="子部门2", pinyin="ZBM2", parent_id=parent.id)
        
        response = client.get("/api/departments/tree")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert len(data[0]["children"]) == 2

    def test_get_department_by_id(self, client, db_session):
        department = create_test_department(db_session, name="测试部门", pinyin="CSBM")
        
        response = client.get(f"/api/departments/{department.id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == department.id
        assert data["name"] == "测试部门"

    def test_get_department_not_found(self, client):
        response = client.get("/api/departments/99999")
        assert response.status_code == 404

    def test_get_department_detail(self, client, db_session):
        department = create_test_department(db_session, name="测试部门", pinyin="CSBM")
        create_test_agent(db_session, name="代理1", department_id=department.id)
        create_test_agent(db_session, name="代理2", department_id=department.id)
        
        response = client.get(f"/api/departments/{department.id}/detail")
        assert response.status_code == 200
        data = response.json()
        assert data["agents_count"] == 2

    def test_get_department_detail_with_children(self, client, db_session):
        parent = create_test_department(db_session, name="父部门", pinyin="FBM")
        create_test_department(db_session, name="子部门1", pinyin="ZBM1", parent_id=parent.id)
        create_test_department(db_session, name="子部门2", pinyin="ZBM2", parent_id=parent.id)
        
        response = client.get(f"/api/departments/{parent.id}/detail")
        assert response.status_code == 200
        data = response.json()
        assert len(data["children"]) == 2

    def test_update_department(self, client, db_session):
        department = create_test_department(db_session, name="原名称", pinyin="YMC")
        
        update_data = {"name": "新名称"}
        response = client.put(f"/api/departments/{department.id}", json=update_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "新名称"

    def test_update_department_pinyin(self, client, db_session):
        department = create_test_department(db_session, name="部门", pinyin="YMC")
        
        update_data = {"pinyin": "XMC"}
        response = client.put(f"/api/departments/{department.id}", json=update_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["pinyin"] == "XMC"

    def test_update_department_duplicate_pinyin(self, client, db_session):
        dept1 = create_test_department(db_session, name="部门1", pinyin="BM1")
        create_test_department(db_session, name="部门2", pinyin="BM2")
        
        update_data = {"pinyin": "BM2"}
        response = client.put(f"/api/departments/{dept1.id}", json=update_data)
        assert response.status_code == 409

    def test_update_department_self_parent(self, client, db_session):
        department = create_test_department(db_session, name="部门", pinyin="BM")
        
        update_data = {"parent_id": department.id}
        response = client.put(f"/api/departments/{department.id}", json=update_data)
        assert response.status_code == 400

    def test_delete_department_success(self, client, db_session):
        department = create_test_department(db_session, name="待删除部门", pinyin="DSCBM")
        
        response = client.delete(f"/api/departments/{department.id}")
        assert response.status_code == 200

    def test_delete_department_not_found(self, client):
        response = client.delete("/api/departments/99999")
        assert response.status_code == 404

    def test_delete_department_with_children(self, client, db_session):
        parent = create_test_department(db_session, name="父部门", pinyin="FBM")
        create_test_department(db_session, name="子部门", pinyin="ZBM", parent_id=parent.id)
        
        response = client.delete(f"/api/departments/{parent.id}")
        assert response.status_code == 400

    def test_delete_department_with_agents(self, client, db_session):
        department = create_test_department(db_session, name="部门", pinyin="BM")
        create_test_agent(db_session, name="代理", department_id=department.id)
        
        response = client.delete(f"/api/departments/{department.id}")
        assert response.status_code == 400
