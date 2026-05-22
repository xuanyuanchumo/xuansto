"""
Skill Call API 集成测试

测试 Skill Call 相关的 API 端点，包括完整的调用流程和树形结构
"""

import pytest
from datetime import datetime, timedelta
from tests.conftest import create_test_project


def create_test_skill_call(db, **kwargs):
    """创建测试 Skill Call 的辅助函数"""
    from app.models.skill_call import SkillCall

    call_data = {
        "skill_name": kwargs.get("skill_name", "test_skill"),
        "caller": kwargs.get("caller", "test_caller"),
        "status": kwargs.get("status", "started"),
        "details": kwargs.get("details", {}),
        "parent_call_id": kwargs.get("parent_call_id", None)
    }

    call = SkillCall(**call_data)
    db.add(call)
    db.commit()
    db.refresh(call)
    return call


@pytest.mark.api
@pytest.mark.integration
class TestSkillCallAPI:
    """测试 Skill Call API 集成"""

    def test_skill_call_lifecycle(self, client, db_session, mock_redis):
        """测试 Skill Call 完整生命周期"""
        # 1. 创建 Skill Call
        call_data = {
            "skill_name": "code_generation",
            "caller": "agent_001",
            "status": "started",
            "details": {"language": "python", "task": "generate_function"}
        }
        response = client.post("/api/skill_calls/", json=call_data)
        assert response.status_code == 200
        call = response.json()
        call_id = call["id"]
        assert call["status"] == "started"

        # 2. 获取 Skill Call
        mock_redis.get_json.return_value = None
        response = client.get(f"/api/skill_calls/{call_id}")
        assert response.status_code == 200
        assert response.json()["skill_name"] == "code_generation"

        # 3. 更新状态为 running
        response = client.put(f"/api/skill_calls/{call_id}", json={"status": "running"})
        assert response.status_code == 200
        assert response.json()["status"] == "running"

        # 4. 完成 Skill Call
        response = client.put(f"/api/skill_calls/{call_id}", json={"status": "completed"})
        assert response.status_code == 200
        assert response.json()["status"] == "completed"

        # 5. 删除 Skill Call
        response = client.delete(f"/api/skill_calls/{call_id}")
        assert response.status_code == 200

        # 6. 验证已删除
        response = client.get(f"/api/skill_calls/{call_id}")
        assert response.status_code == 404

    def test_skill_call_with_parent(self, client, db_session, mock_redis):
        """测试带父调用的 Skill Call"""
        # 创建父调用
        parent_call = create_test_skill_call(db_session, skill_name="parent_skill", caller="agent_001")

        # 创建子调用
        call_data = {
            "skill_name": "child_skill",
            "caller": "agent_001",
            "parent_call_id": parent_call.id
        }
        response = client.post("/api/skill_calls/", json=call_data)
        assert response.status_code == 200
        call = response.json()
        assert call["parent_call_id"] == parent_call.id

        # 获取父调用的详情
        mock_redis.get_json.return_value = None
        response = client.get(f"/api/skill_calls/{parent_call.id}/detail")
        assert response.status_code == 200
        data = response.json()
        assert data["children_count"] == 1

    def test_skill_call_tree_structure(self, client, db_session, mock_redis):
        """测试 Skill Call 树形结构"""
        # 创建树形结构
        root = create_test_skill_call(db_session, skill_name="root_skill")
        child1 = create_test_skill_call(db_session, skill_name="child_1", parent_call_id=root.id)
        child2 = create_test_skill_call(db_session, skill_name="child_2", parent_call_id=root.id)
        grandchild = create_test_skill_call(db_session, skill_name="grandchild", parent_call_id=child1.id)

        mock_redis.get_json.return_value = None

        # 获取调用树
        response = client.get(f"/api/skill_calls/tree/{root.id}")
        assert response.status_code == 200
        tree = response.json()

        assert tree["id"] == root.id
        assert len(tree["children"]) == 2

        # 找到 child_1 并验证其子节点
        child_1_data = next(c for c in tree["children"] if c["skill_name"] == "child_1")
        assert len(child_1_data["children"]) == 1
        assert child_1_data["children"][0]["skill_name"] == "grandchild"

    def test_skill_call_status_transitions(self, client, db_session):
        """测试 Skill Call 状态流转"""
        call = create_test_skill_call(db_session, skill_name="transition_skill", status="started")

        # started -> running
        response = client.put(f"/api/skill_calls/{call.id}", json={"status": "running"})
        assert response.status_code == 200
        assert response.json()["status"] == "running"

        # running -> completed
        response = client.put(f"/api/skill_calls/{call.id}", json={"status": "completed"})
        assert response.status_code == 200
        assert response.json()["status"] == "completed"

    def test_skill_call_failed_status(self, client, db_session):
        """测试 Skill Call 失败状态"""
        call = create_test_skill_call(db_session, skill_name="failing_skill", status="running")

        response = client.put(f"/api/skill_calls/{call.id}", json={
            "status": "failed",
            "error_message": "Execution timeout"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "failed"


@pytest.mark.api
@pytest.mark.integration
class TestSkillCallListAndFilter:
    """测试 Skill Call 列表和筛选"""

    def test_list_skill_calls_with_filters(self, client, db_session, mock_redis):
        """测试带筛选的 Skill Call 列表"""
        # 创建多个 Skill Call
        create_test_skill_call(db_session, skill_name="code_generation", status="completed", caller="agent_001")
        create_test_skill_call(db_session, skill_name="code_review", status="failed", caller="agent_001")
        create_test_skill_call(db_session, skill_name="code_generation", status="running", caller="agent_002")

        mock_redis.get_json.return_value = None

        # 按技能名称筛选
        response = client.get("/api/skill_calls/?skill_name=code_generation")
        assert response.status_code == 200
        data = response.json()
        assert all(c["skill_name"] == "code_generation" for c in data)

        # 按状态筛选
        response = client.get("/api/skill_calls/?status=completed")
        assert response.status_code == 200
        data = response.json()
        assert all(c["status"] == "completed" for c in data)

        # 按调用者筛选
        response = client.get("/api/skill_calls/?caller=agent_001")
        assert response.status_code == 200
        data = response.json()
        assert all(c["caller"] == "agent_001" for c in data)

    def test_list_skill_calls_pagination(self, client, db_session, mock_redis):
        """测试 Skill Call 列表分页"""
        # 创建多个 Skill Call
        for i in range(15):
            create_test_skill_call(db_session, skill_name=f"skill_{i}")

        mock_redis.get_json.return_value = None

        # 第一页
        response = client.get("/api/skill_calls/?skip=0&limit=10")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 10

        # 第二页
        response = client.get("/api/skill_calls/?skip=10&limit=10")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 5

    def test_list_skill_calls_combined_filters(self, client, db_session, mock_redis):
        """测试组合筛选条件"""
        create_test_skill_call(db_session, skill_name="code_generation", status="completed", caller="agent_001")
        create_test_skill_call(db_session, skill_name="code_generation", status="failed", caller="agent_001")
        create_test_skill_call(db_session, skill_name="code_review", status="completed", caller="agent_002")

        mock_redis.get_json.return_value = None

        response = client.get("/api/skill_calls/?skill_name=code_generation&status=completed&caller=agent_001")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["skill_name"] == "code_generation"
        assert data[0]["status"] == "completed"
        assert data[0]["caller"] == "agent_001"


@pytest.mark.api
@pytest.mark.integration
class TestSkillCallStats:
    """测试 Skill Call 统计"""

    def test_skill_call_stats(self, client, db_session, mock_redis):
        """测试 Skill Call 统计"""
        # 创建不同状态的调用
        create_test_skill_call(db_session, skill_name="code_generation", status="completed")
        create_test_skill_call(db_session, skill_name="code_generation", status="completed")
        create_test_skill_call(db_session, skill_name="code_review", status="failed")
        create_test_skill_call(db_session, skill_name="test_execution", status="running")
        create_test_skill_call(db_session, skill_name="code_generation", status="started")

        mock_redis.get_json.return_value = None

        response = client.get("/api/skill_calls/stats")
        assert response.status_code == 200
        data = response.json()

        assert data["total"] == 5
        assert "by_status" in data
        assert "by_skill" in data
        assert "success_rate" in data
        assert data["by_status"]["completed"] == 2
        assert data["by_status"]["failed"] == 1
        assert data["by_skill"]["code_generation"] == 3

    def test_skill_call_stats_empty(self, client, mock_redis):
        """测试无 Skill Call 时的统计"""
        mock_redis.get_json.return_value = None

        response = client.get("/api/skill_calls/stats")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0
        assert data["success_rate"] == 0.0

    def test_skill_call_stats_success_rate(self, client, db_session, mock_redis):
        """测试成功率计算"""
        # 创建不同状态的调用
        create_test_skill_call(db_session, skill_name="skill_1", status="completed")
        create_test_skill_call(db_session, skill_name="skill_2", status="completed")
        create_test_skill_call(db_session, skill_name="skill_3", status="completed")
        create_test_skill_call(db_session, skill_name="skill_4", status="failed")

        mock_redis.get_json.return_value = None

        response = client.get("/api/skill_calls/stats")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 4
        assert data["success_rate"] == 75.0  # 3 completed out of 4


@pytest.mark.api
@pytest.mark.integration
class TestSkillCallValidation:
    """测试 Skill Call API 验证"""

    def test_create_skill_call_validation(self, client):
        """测试创建 Skill Call 验证"""
        # 缺少必需字段
        response = client.post("/api/skill_calls/", json={})
        assert response.status_code == 422

        # 无效状态
        response = client.post("/api/skill_calls/", json={
            "skill_name": "test",
            "status": "invalid_status"
        })
        assert response.status_code == 400

    def test_update_skill_call_validation(self, client, db_session):
        """测试更新 Skill Call 验证"""
        call = create_test_skill_call(db_session, skill_name="test_skill", status="started")

        # 无效状态
        response = client.put(f"/api/skill_calls/{call.id}", json={"status": "INVALID"})
        assert response.status_code == 400

        # 无效的状态转换（completed -> running）
        call_completed = create_test_skill_call(db_session, skill_name="completed_skill", status="completed")
        response = client.put(f"/api/skill_calls/{call_completed.id}", json={"status": "running"})
        assert response.status_code == 400

    def test_skill_call_not_found(self, client):
        """测试 Skill Call 不存在的情况"""
        # 获取不存在的调用
        response = client.get("/api/skill_calls/99999")
        assert response.status_code == 404

        # 更新不存在的调用
        response = client.put("/api/skill_calls/99999", json={"status": "completed"})
        assert response.status_code == 404

        # 删除不存在的调用
        response = client.delete("/api/skill_calls/99999")
        assert response.status_code == 404

        # 获取不存在的调用树
        response = client.get("/api/skill_calls/tree/99999")
        assert response.status_code == 404


@pytest.mark.api
@pytest.mark.integration
class TestSkillCallEdgeCases:
    """测试 Skill Call 边界情况"""

    def test_skill_call_with_long_skill_name(self, client):
        """测试使用长技能名称"""
        call_data = {
            "skill_name": "a" * 100,
            "caller": "test_caller"
        }
        response = client.post("/api/skill_calls/", json=call_data)
        assert response.status_code == 200

    def test_skill_call_with_special_characters(self, client):
        """测试使用特殊字符"""
        call_data = {
            "skill_name": "skill-name_123.test",
            "caller": "agent-001_test"
        }
        response = client.post("/api/skill_calls/", json=call_data)
        assert response.status_code == 200

    def test_skill_call_with_complex_details(self, client):
        """测试使用复杂详情"""
        call_data = {
            "skill_name": "complex_skill",
            "details": {
                "nested": {
                    "key1": "value1",
                    "key2": ["item1", "item2"]
                },
                "numbers": [1, 2, 3],
                "boolean": True,
                "null_value": None
            }
        }
        response = client.post("/api/skill_calls/", json=call_data)
        assert response.status_code == 200
        data = response.json()
        assert data["details"]["nested"]["key1"] == "value1"
        assert data["details"]["numbers"] == [1, 2, 3]

    def test_skill_call_delete_with_children(self, client, db_session):
        """测试删除有子调用的 Skill Call"""
        parent_call = create_test_skill_call(db_session, skill_name="parent_skill")
        child_call = create_test_skill_call(db_session, skill_name="child_skill", parent_call_id=parent_call.id)

        # 尝试删除父调用
        response = client.delete(f"/api/skill_calls/{parent_call.id}")
        assert response.status_code == 400
        assert "child calls" in response.json()["detail"].lower()

    def test_skill_call_invalid_parent(self, client):
        """测试创建时指定不存在的父调用"""
        call_data = {
            "skill_name": "orphan_skill",
            "parent_call_id": 99999
        }
        response = client.post("/api/skill_calls/", json=call_data)
        assert response.status_code == 404


@pytest.mark.api
@pytest.mark.integration
class TestSkillCallPerformance:
    """测试 Skill Call API 性能"""

    def test_list_skill_calls_performance(self, client, db_session, mock_redis):
        """测试 Skill Call 列表性能"""
        # 创建大量 Skill Call
        for i in range(100):
            create_test_skill_call(db_session, skill_name=f"skill_{i}")

        mock_redis.get_json.return_value = None

        import time
        start_time = time.time()
        response = client.get("/api/skill_calls/")
        end_time = time.time()

        assert response.status_code == 200
        assert end_time - start_time < 3.0  # 应该在 3 秒内完成

    def test_skill_call_stats_performance(self, client, db_session, mock_redis):
        """测试 Skill Call 统计性能"""
        # 创建大量 Skill Call
        for i in range(50):
            create_test_skill_call(db_session, skill_name=f"skill_{i}", status="completed")

        mock_redis.get_json.return_value = None

        import time
        start_time = time.time()
        response = client.get("/api/skill_calls/stats")
        end_time = time.time()

        assert response.status_code == 200
        assert end_time - start_time < 2.0  # 应该在 2 秒内完成

    def test_call_tree_performance(self, client, db_session, mock_redis):
        """测试调用树性能"""
        # 创建深层调用树
        root = create_test_skill_call(db_session, skill_name="root")
        current = root
        for i in range(20):
            child = create_test_skill_call(db_session, skill_name=f"child_{i}", parent_call_id=current.id)
            current = child

        mock_redis.get_json.return_value = None

        import time
        start_time = time.time()
        response = client.get(f"/api/skill_calls/tree/{root.id}")
        end_time = time.time()

        assert response.status_code == 200
        assert end_time - start_time < 2.0  # 应该在 2 秒内完成


@pytest.mark.api
@pytest.mark.integration
class TestSkillCallConcurrent:
    """测试 Skill Call 并发场景"""

    def test_concurrent_skill_calls(self, client, db_session):
        """测试并发创建 Skill Call"""
        # 模拟并发创建
        responses = []
        for i in range(10):
            call_data = {
                "skill_name": f"concurrent_skill_{i}",
                "caller": f"agent_{i}"
            }
            response = client.post("/api/skill_calls/", json=call_data)
            responses.append(response)

        # 验证所有请求都成功
        assert all(r.status_code == 200 for r in responses)

    def test_concurrent_updates(self, client, db_session):
        """测试并发更新 Skill Call"""
        call = create_test_skill_call(db_session, skill_name="concurrent_update", status="started")

        # 模拟并发更新
        responses = []
        for i in range(5):
            response = client.put(f"/api/skill_calls/{call.id}", json={"details": {"update": i}})
            responses.append(response)

        # 验证所有请求都成功
        assert all(r.status_code == 200 for r in responses)
