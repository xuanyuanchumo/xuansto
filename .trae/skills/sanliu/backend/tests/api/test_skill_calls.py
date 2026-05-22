"""
Skill Call API 测试

测试 Skill Call 相关的 API 端点
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
class TestSkillCallCreate:
    """测试 Skill Call 创建 API"""

    def test_create_skill_call_success(self, client):
        """测试成功创建 Skill Call"""
        call_data = {
            "skill_name": "code_generation",
            "caller": "agent_001",
            "status": "started",
            "details": {"language": "python", "task": "generate_function"}
        }

        response = client.post("/api/skill_calls/", json=call_data)

        assert response.status_code == 200
        data = response.json()
        assert data["skill_name"] == "code_generation"
        assert data["caller"] == "agent_001"
        assert data["status"] == "started"
        assert data["details"] == {"language": "python", "task": "generate_function"}
        assert "id" in data
        assert "start_time" in data

    def test_create_skill_call_minimal_data(self, client):
        """测试使用最小数据创建 Skill Call"""
        minimal_data = {
            "skill_name": "simple_skill"
        }

        response = client.post("/api/skill_calls/", json=minimal_data)

        assert response.status_code == 200
        data = response.json()
        assert data["skill_name"] == "simple_skill"
        assert data["status"] == "started"
        assert data["caller"] is None

    def test_create_skill_call_with_parent(self, client, db_session):
        """测试创建带父调用的 Skill Call"""
        parent_call = create_test_skill_call(db_session, skill_name="parent_skill")

        call_data = {
            "skill_name": "child_skill",
            "caller": "agent_001",
            "parent_call_id": parent_call.id
        }

        response = client.post("/api/skill_calls/", json=call_data)

        assert response.status_code == 200
        data = response.json()
        assert data["skill_name"] == "child_skill"
        assert data["parent_call_id"] == parent_call.id

    def test_create_skill_call_invalid_parent(self, client):
        """测试创建时指定不存在的父调用"""
        call_data = {
            "skill_name": "orphan_skill",
            "parent_call_id": 99999
        }

        response = client.post("/api/skill_calls/", json=call_data)

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_create_skill_call_invalid_status(self, client):
        """测试使用无效状态创建 Skill Call"""
        call_data = {
            "skill_name": "test_skill",
            "status": "invalid_status"
        }

        response = client.post("/api/skill_calls/", json=call_data)

        assert response.status_code == 400

    def test_create_skill_call_with_complex_details(self, client):
        """测试创建带复杂详情的 Skill Call"""
        call_data = {
            "skill_name": "complex_skill",
            "details": {
                "nested": {
                    "key1": "value1",
                    "key2": ["item1", "item2"]
                },
                "numbers": [1, 2, 3],
                "boolean": True
            }
        }

        response = client.post("/api/skill_calls/", json=call_data)

        assert response.status_code == 200
        data = response.json()
        assert data["details"]["nested"]["key1"] == "value1"
        assert data["details"]["numbers"] == [1, 2, 3]


@pytest.mark.api
@pytest.mark.integration
class TestSkillCallList:
    """测试 Skill Call 列表 API"""

    def test_list_skill_calls_empty(self, client):
        """测试空 Skill Call 列表"""
        response = client.get("/api/skill_calls/")

        assert response.status_code == 200
        data = response.json()
        assert data == []

    def test_list_skill_calls_with_data(self, client, db_session, mock_redis):
        """测试有数据时的 Skill Call 列表"""
        create_test_skill_call(db_session, skill_name="skill_1")
        create_test_skill_call(db_session, skill_name="skill_2")
        create_test_skill_call(db_session, skill_name="skill_3")

        mock_redis.get_json.return_value = None

        response = client.get("/api/skill_calls/")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3

    def test_list_skill_calls_with_pagination(self, client, db_session, mock_redis):
        """测试 Skill Call 列表分页"""
        for i in range(10):
            create_test_skill_call(db_session, skill_name=f"skill_{i}")

        mock_redis.get_json.return_value = None

        # 测试 skip 和 limit
        response = client.get("/api/skill_calls/?skip=0&limit=5")
        data = response.json()
        assert len(data) == 5

        response = client.get("/api/skill_calls/?skip=5&limit=5")
        data = response.json()
        assert len(data) == 5

    def test_list_skill_calls_filter_by_skill_name(self, client, db_session, mock_redis):
        """测试按技能名称筛选"""
        create_test_skill_call(db_session, skill_name="code_generation")
        create_test_skill_call(db_session, skill_name="code_review")
        create_test_skill_call(db_session, skill_name="code_generation")

        mock_redis.get_json.return_value = None

        response = client.get("/api/skill_calls/?skill_name=code_generation")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        for call in data:
            assert call["skill_name"] == "code_generation"

    def test_list_skill_calls_filter_by_status(self, client, db_session, mock_redis):
        """测试按状态筛选"""
        create_test_skill_call(db_session, skill_name="skill_1", status="started")
        create_test_skill_call(db_session, skill_name="skill_2", status="completed")
        create_test_skill_call(db_session, skill_name="skill_3", status="failed")

        mock_redis.get_json.return_value = None

        response = client.get("/api/skill_calls/?status=completed")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["status"] == "completed"

    def test_list_skill_calls_filter_by_caller(self, client, db_session, mock_redis):
        """测试按调用者筛选"""
        create_test_skill_call(db_session, skill_name="skill_1", caller="agent_001")
        create_test_skill_call(db_session, skill_name="skill_2", caller="agent_002")
        create_test_skill_call(db_session, skill_name="skill_3", caller="agent_001")

        mock_redis.get_json.return_value = None

        response = client.get("/api/skill_calls/?caller=agent_001")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        for call in data:
            assert call["caller"] == "agent_001"

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
class TestSkillCallDetail:
    """测试 Skill Call 详情 API"""

    def test_get_skill_call_success(self, client, db_session, mock_redis):
        """测试成功获取 Skill Call 详情"""
        call = create_test_skill_call(db_session, skill_name="test_skill", caller="test_caller")

        mock_redis.get_json.return_value = None

        response = client.get(f"/api/skill_calls/{call.id}")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == call.id
        assert data["skill_name"] == "test_skill"
        assert data["caller"] == "test_caller"

    def test_get_skill_call_not_found(self, client):
        """测试获取不存在的 Skill Call"""
        response = client.get("/api/skill_calls/99999")

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_get_skill_call_detail_with_stats(self, client, db_session, mock_redis):
        """测试获取包含统计信息的 Skill Call 详情"""
        parent_call = create_test_skill_call(db_session, skill_name="parent_skill")
        child_call1 = create_test_skill_call(db_session, skill_name="child_1", parent_call_id=parent_call.id)
        child_call2 = create_test_skill_call(db_session, skill_name="child_2", parent_call_id=parent_call.id)

        mock_redis.get_json.return_value = None

        response = client.get(f"/api/skill_calls/{parent_call.id}/detail")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == parent_call.id
        assert data["children_count"] == 2
        assert "duration_seconds" in data
        assert "has_error" in data

    def test_get_skill_call_detail_with_duration(self, client, db_session, mock_redis):
        """测试获取包含执行时长的详情"""
        from sqlalchemy import text

        call = create_test_skill_call(db_session, skill_name="timed_skill", status="completed")

        # 手动设置时间以计算时长
        db_session.execute(
            text("UPDATE skill_calls SET start_time = :start, end_time = :end WHERE id = :id"),
            {
                "start": datetime.utcnow() - timedelta(minutes=5),
                "end": datetime.utcnow(),
                "id": call.id
            }
        )
        db_session.commit()

        mock_redis.get_json.return_value = None

        response = client.get(f"/api/skill_calls/{call.id}/detail")

        assert response.status_code == 200
        data = response.json()
        assert data["duration_seconds"] >= 300  # 5 minutes


@pytest.mark.api
@pytest.mark.integration
class TestSkillCallUpdate:
    """测试 Skill Call 更新 API"""

    def test_update_skill_call_success(self, client, db_session):
        """测试成功更新 Skill Call"""
        call = create_test_skill_call(db_session, skill_name="test_skill", status="started")

        update_data = {
            "status": "running",
            "details": {"progress": 50}
        }
        response = client.put(f"/api/skill_calls/{call.id}", json=update_data)

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "running"
        assert data["details"] == {"progress": 50}

    def test_update_skill_call_not_found(self, client):
        """测试更新不存在的 Skill Call"""
        response = client.put("/api/skill_calls/99999", json={"status": "completed"})

        assert response.status_code == 404

    def test_update_skill_call_status_transition_started_to_running(self, client, db_session):
        """测试状态从 started 到 running 的转换"""
        call = create_test_skill_call(db_session, skill_name="test_skill", status="started")

        response = client.put(f"/api/skill_calls/{call.id}", json={"status": "running"})

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "running"

    def test_update_skill_call_status_transition_running_to_completed(self, client, db_session):
        """测试状态从 running 到 completed 的转换"""
        call = create_test_skill_call(db_session, skill_name="test_skill", status="running")

        end_time = (datetime.utcnow() + timedelta(minutes=5)).isoformat()
        response = client.put(f"/api/skill_calls/{call.id}", json={
            "status": "completed",
            "end_time": end_time
        })

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "completed"

    def test_update_skill_call_status_transition_to_failed(self, client, db_session):
        """测试状态转换到 failed"""
        call = create_test_skill_call(db_session, skill_name="test_skill", status="running")

        response = client.put(f"/api/skill_calls/{call.id}", json={
            "status": "failed",
            "error_message": "Execution timeout"
        })

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "failed"

    def test_update_skill_call_invalid_status_transition(self, client, db_session):
        """测试无效的状态转换"""
        call = create_test_skill_call(db_session, skill_name="test_skill", status="completed")

        response = client.put(f"/api/skill_calls/{call.id}", json={"status": "running"})

        assert response.status_code == 400
        assert "cannot transition" in response.json()["detail"].lower()

    def test_update_skill_call_invalid_status(self, client, db_session):
        """测试更新为无效状态"""
        call = create_test_skill_call(db_session, skill_name="test_skill")

        response = client.put(f"/api/skill_calls/{call.id}", json={"status": "invalid_status"})

        assert response.status_code == 400


@pytest.mark.api
@pytest.mark.integration
class TestSkillCallDelete:
    """测试 Skill Call 删除 API"""

    def test_delete_skill_call_success(self, client, db_session):
        """测试成功删除 Skill Call"""
        call = create_test_skill_call(db_session, skill_name="test_skill")

        response = client.delete(f"/api/skill_calls/{call.id}")

        assert response.status_code == 200
        data = response.json()
        assert "deleted successfully" in data["message"]
        assert data["call_id"] == call.id

        # 验证 Skill Call 已被删除
        get_response = client.get(f"/api/skill_calls/{call.id}")
        assert get_response.status_code == 404

    def test_delete_skill_call_not_found(self, client):
        """测试删除不存在的 Skill Call"""
        response = client.delete("/api/skill_calls/99999")

        assert response.status_code == 404

    def test_delete_skill_call_with_children(self, client, db_session):
        """测试删除有子调用的 Skill Call"""
        parent_call = create_test_skill_call(db_session, skill_name="parent_skill")
        child_call = create_test_skill_call(db_session, skill_name="child_skill", parent_call_id=parent_call.id)

        response = client.delete(f"/api/skill_calls/{parent_call.id}")

        assert response.status_code == 400
        assert "child calls" in response.json()["detail"].lower()


@pytest.mark.api
@pytest.mark.integration
class TestSkillCallTree:
    """测试 Skill Call 树形结构 API"""

    def test_get_call_tree_success(self, client, db_session, mock_redis):
        """测试成功获取调用树"""
        root_call = create_test_skill_call(db_session, skill_name="root_skill")
        child1 = create_test_skill_call(db_session, skill_name="child_1", parent_call_id=root_call.id)
        child2 = create_test_skill_call(db_session, skill_name="child_2", parent_call_id=root_call.id)
        grandchild = create_test_skill_call(db_session, skill_name="grandchild", parent_call_id=child1.id)

        mock_redis.get_json.return_value = None

        response = client.get(f"/api/skill_calls/tree/{root_call.id}")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == root_call.id
        assert data["skill_name"] == "root_skill"
        assert len(data["children"]) == 2

        # 找到 child_1 并检查其子节点
        child_1_data = next(c for c in data["children"] if c["skill_name"] == "child_1")
        assert len(child_1_data["children"]) == 1
        assert child_1_data["children"][0]["skill_name"] == "grandchild"

    def test_get_call_tree_not_found(self, client):
        """测试获取不存在的调用树"""
        response = client.get("/api/skill_calls/tree/99999")

        assert response.status_code == 404

    def test_get_call_tree_single_node(self, client, db_session, mock_redis):
        """测试获取单节点调用树"""
        call = create_test_skill_call(db_session, skill_name="single_skill")

        mock_redis.get_json.return_value = None

        response = client.get(f"/api/skill_calls/tree/{call.id}")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == call.id
        assert data["children"] == []


@pytest.mark.api
@pytest.mark.integration
class TestSkillCallStats:
    """测试 Skill Call 统计 API"""

    def test_get_skill_call_stats(self, client, db_session, mock_redis):
        """测试获取 Skill Call 统计"""
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

    def test_get_skill_call_stats_empty(self, client, mock_redis):
        """测试无 Skill Call 时的统计"""
        mock_redis.get_json.return_value = None

        response = client.get("/api/skill_calls/stats")

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0
        assert data["success_rate"] == 0.0

    def test_get_skill_call_stats_with_duration(self, client, db_session, mock_redis):
        """测试包含执行时长的统计"""
        from sqlalchemy import text

        # 创建已完成的调用（带结束时间）
        call1 = create_test_skill_call(db_session, skill_name="quick_skill", status="completed")
        call2 = create_test_skill_call(db_session, skill_name="slow_skill", status="completed")

        # 手动设置时间以计算时长
        db_session.execute(
            text("UPDATE skill_calls SET start_time = :start, end_time = :end WHERE id = :id"),
            {
                "start": datetime.utcnow() - timedelta(minutes=5),
                "end": datetime.utcnow(),
                "id": call1.id
            }
        )
        db_session.execute(
            text("UPDATE skill_calls SET start_time = :start, end_time = :end WHERE id = :id"),
            {
                "start": datetime.utcnow() - timedelta(minutes=10),
                "end": datetime.utcnow(),
                "id": call2.id
            }
        )
        db_session.commit()

        mock_redis.get_json.return_value = None

        response = client.get("/api/skill_calls/stats")

        assert response.status_code == 200
        data = response.json()
        assert "avg_duration" in data

    def test_get_skill_call_stats_success_rate(self, client, db_session, mock_redis):
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
class TestSkillCallQuery:
    """测试 Skill Call 查询 API"""

    def test_query_skill_calls_by_time_range(self, client, db_session, mock_redis):
        """测试按时间范围查询 Skill Call"""
        # 创建一些调用
        create_test_skill_call(db_session, skill_name="recent_skill")
        create_test_skill_call(db_session, skill_name="another_skill")

        mock_redis.get_json.return_value = None

        response = client.get("/api/skill_calls/?limit=10")

        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 2

    def test_query_skill_calls_combined_filters(self, client, db_session, mock_redis):
        """测试组合筛选条件查询"""
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
class TestSkillCallEdgeCases:
    """测试 Skill Call 边界情况"""

    def test_create_skill_call_with_long_skill_name(self, client):
        """测试使用长技能名称创建 Skill Call"""
        call_data = {
            "skill_name": "a" * 100,
            "caller": "test_caller"
        }
        response = client.post("/api/skill_calls/", json=call_data)
        assert response.status_code == 200

    def test_create_skill_call_with_special_characters(self, client):
        """测试使用特殊字符创建 Skill Call"""
        call_data = {
            "skill_name": "skill-name_123.test",
            "caller": "agent-001_test"
        }
        response = client.post("/api/skill_calls/", json=call_data)
        assert response.status_code == 200

    def test_update_skill_call_with_empty_details(self, client, db_session):
        """测试更新 Skill Call 为空详情"""
        call = create_test_skill_call(db_session, skill_name="test_skill", details={"key": "value"})

        response = client.put(f"/api/skill_calls/{call.id}", json={"details": {}})

        assert response.status_code == 200
        data = response.json()
        assert data["details"] == {}

    def test_get_skill_call_with_invalid_id(self, client):
        """测试使用无效 ID 获取 Skill Call"""
        response = client.get("/api/skill_calls/invalid_id")
        assert response.status_code == 422


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
