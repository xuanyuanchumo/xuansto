"""
Agent API 测试

测试 Agent 相关的 API 端点
"""

import pytest
from datetime import datetime, timedelta
from tests.conftest import create_test_agent, create_test_project, create_test_task, create_test_department


@pytest.mark.api
@pytest.mark.integration
class TestAgentCreate:
    """测试 Agent 创建 API"""

    def test_create_agent_success(self, client, sample_agent_data):
        """测试成功创建 Agent"""
        response = client.post("/api/agents/", json=sample_agent_data)

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == sample_agent_data["name"]
        assert data["role"] == sample_agent_data["role"]
        assert data["skills"] == sample_agent_data["skills"]
        assert data["status"] == "idle"
        assert data["current_load"] == 0
        assert data["max_load"] == 5
        assert "id" in data
        assert "created_at" in data

    def test_create_agent_minimal_data(self, client):
        """测试使用最小数据创建 Agent"""
        minimal_data = {"name": "最小代理"}
        response = client.post("/api/agents/", json=minimal_data)

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "最小代理"
        assert data["status"] == "idle"
        assert data["max_load"] == 5

    def test_create_agent_duplicate_name(self, client, sample_agent_data, db_session):
        """测试创建同名 Agent 应该失败"""
        # 先创建一个 Agent
        response1 = client.post("/api/agents/", json=sample_agent_data)
        assert response1.status_code == 200

        # 尝试创建同名 Agent
        response2 = client.post("/api/agents/", json=sample_agent_data)
        assert response2.status_code == 409
        assert "already exists" in response2.json()["detail"]

    def test_create_agent_invalid_name(self, client):
        """测试使用无效名称创建 Agent"""
        # 空名称
        response = client.post("/api/agents/", json={"name": ""})
        assert response.status_code == 422

        # 名称过长
        response = client.post("/api/agents/", json={"name": "x" * 101})
        assert response.status_code == 422

    def test_create_agent_with_department(self, client, db_session):
        """测试创建带部门的 Agent"""
        department = create_test_department(db_session, name="开发部")
        agent_data = {
            "name": "部门代理",
            "department_id": department.id
        }

        response = client.post("/api/agents/", json=agent_data)

        assert response.status_code == 200
        data = response.json()
        assert data["department_id"] == department.id

    def test_create_agent_with_max_load(self, client):
        """测试创建带最大负载的 Agent"""
        agent_data = {
            "name": "高负载代理",
            "max_load": 15
        }

        response = client.post("/api/agents/", json=agent_data)

        assert response.status_code == 200
        data = response.json()
        assert data["max_load"] == 15

    def test_create_agent_invalid_max_load(self, client):
        """测试使用无效的最大负载创建 Agent"""
        # 超过最大值
        response = client.post("/api/agents/", json={"name": "测试代理", "max_load": 25})
        assert response.status_code == 422

        # 小于最小值
        response = client.post("/api/agents/", json={"name": "测试代理", "max_load": 0})
        assert response.status_code == 422


@pytest.mark.api
@pytest.mark.integration
class TestAgentList:
    """测试 Agent 列表 API"""

    def test_list_agents_empty(self, client):
        """测试空 Agent 列表"""
        response = client.get("/api/agents/")

        assert response.status_code == 200
        data = response.json()
        assert data == []

    def test_list_agents_with_data(self, client, db_session):
        """测试有数据时的 Agent 列表"""
        create_test_agent(db_session, name="代理1")
        create_test_agent(db_session, name="代理2")

        response = client.get("/api/agents/")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2

    def test_list_agents_filter_by_status(self, client, db_session):
        """测试按状态筛选 Agent"""
        create_test_agent(db_session, name="空闲代理", status="idle")
        create_test_agent(db_session, name="忙碌代理", status="busy")
        create_test_agent(db_session, name="离线代理", status="offline")

        # 筛选 idle 状态
        response = client.get("/api/agents/?status=idle")
        data = response.json()
        assert len(data) == 1
        assert data[0]["status"] == "idle"

        # 筛选 busy 状态
        response = client.get("/api/agents/?status=busy")
        data = response.json()
        assert len(data) == 1
        assert data[0]["status"] == "busy"

    def test_list_agents_filter_by_skill(self, client, db_session):
        """测试按技能筛选 Agent"""
        create_test_agent(db_session, name="Python代理", skills=["python", "fastapi"])
        create_test_agent(db_session, name="Java代理", skills=["java", "spring"])

        response = client.get("/api/agents/?skill=python")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert "python" in data[0]["skills"]

    def test_list_agents_filter_by_department(self, client, db_session):
        """测试按部门筛选 Agent"""
        dept1 = create_test_department(db_session, name="部门1")
        dept2 = create_test_department(db_session, name="部门2")

        create_test_agent(db_session, name="代理1", department_id=dept1.id)
        create_test_agent(db_session, name="代理2", department_id=dept2.id)

        response = client.get(f"/api/agents/?department_id={dept1.id}")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["department_id"] == dept1.id

    def test_list_agents_invalid_status(self, client):
        """测试使用无效状态筛选 Agent"""
        response = client.get("/api/agents/?status=invalid_status")
        assert response.status_code == 400


@pytest.mark.api
@pytest.mark.integration
class TestAgentDetail:
    """测试 Agent 详情 API"""

    def test_get_agent_success(self, client, db_session):
        """测试成功获取 Agent 详情"""
        agent = create_test_agent(db_session, name="测试代理")

        response = client.get(f"/api/agents/{agent.id}")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == agent.id
        assert data["name"] == "测试代理"

    def test_get_agent_not_found(self, client):
        """测试获取不存在的 Agent"""
        response = client.get("/api/agents/99999")

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_get_agent_detail_with_stats(self, client, db_session):
        """测试获取包含统计信息的 Agent 详情"""
        from app.models.task import TaskStatus

        agent = create_test_agent(db_session, name="统计测试代理")
        project = create_test_project(db_session, name="测试项目")

        # 创建分配的任务
        create_test_task(db_session, project_id=project.id, agent_id=agent.id,
                        title="进行中任务", status=TaskStatus.IN_PROGRESS.value)
        create_test_task(db_session, project_id=project.id, agent_id=agent.id,
                        title="已完成任务", status=TaskStatus.COMPLETED.value)

        response = client.get(f"/api/agents/{agent.id}/detail")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == agent.id
        assert data["assigned_tasks_count"] == 1
        assert data["completed_tasks_count"] == 1
        assert "utilization_rate" in data

    def test_get_agent_detail_not_found(self, client):
        """测试获取不存在的 Agent 详情"""
        response = client.get("/api/agents/99999/detail")
        assert response.status_code == 404


@pytest.mark.api
@pytest.mark.integration
class TestAgentUpdate:
    """测试 Agent 更新 API"""

    def test_update_agent_success(self, client, db_session):
        """测试成功更新 Agent"""
        agent = create_test_agent(db_session, name="旧名称")

        update_data = {
            "name": "新名称",
            "role": "新角色",
            "skills": ["python", "javascript"]
        }
        response = client.put(f"/api/agents/{agent.id}", json=update_data)

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "新名称"
        assert data["role"] == "新角色"
        assert data["skills"] == ["python", "javascript"]

    def test_update_agent_not_found(self, client):
        """测试更新不存在的 Agent"""
        response = client.put("/api/agents/99999", json={"name": "新名称"})

        assert response.status_code == 404

    def test_update_agent_status(self, client, db_session):
        """测试更新 Agent 状态"""
        agent = create_test_agent(db_session, name="状态测试代理", status="idle")

        response = client.put(f"/api/agents/{agent.id}", json={"status": "busy"})

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "busy"

    def test_update_agent_invalid_status(self, client, db_session):
        """测试更新为无效状态"""
        agent = create_test_agent(db_session, name="测试代理")

        response = client.put(f"/api/agents/{agent.id}", json={"status": "invalid_status"})

        assert response.status_code == 400

    def test_update_agent_load(self, client, db_session):
        """测试更新 Agent 负载"""
        agent = create_test_agent(db_session, name="负载测试代理", max_load=10)

        response = client.put(f"/api/agents/{agent.id}", json={"current_load": 5})

        assert response.status_code == 200
        data = response.json()
        assert data["current_load"] == 5

    def test_update_agent_load_exceeds_max(self, client, db_session):
        """测试更新负载超过最大值"""
        agent = create_test_agent(db_session, name="测试代理", max_load=5)

        response = client.put(f"/api/agents/{agent.id}", json={"current_load": 10})

        assert response.status_code == 400
        assert "cannot exceed" in response.json()["detail"].lower()

    def test_update_agent_duplicate_name(self, client, db_session):
        """测试更新 Agent 时使用已存在的名称"""
        agent1 = create_test_agent(db_session, name="代理1")
        agent2 = create_test_agent(db_session, name="代理2")

        response = client.put(f"/api/agents/{agent1.id}", json={"name": "代理2"})

        assert response.status_code == 409

    def test_update_agent_partial(self, client, db_session):
        """测试部分更新 Agent"""
        agent = create_test_agent(db_session, name="测试代理", role="开发者", skills=["python"])

        # 只更新角色
        response = client.put(f"/api/agents/{agent.id}", json={"role": "架构师"})

        assert response.status_code == 200
        data = response.json()
        assert data["role"] == "架构师"
        assert data["name"] == "测试代理"  # 未改变
        assert data["skills"] == ["python"]  # 未改变

    def test_update_agent_current_task(self, client, db_session):
        """测试更新 Agent 当前任务"""
        agent = create_test_agent(db_session, name="测试代理")

        response = client.put(f"/api/agents/{agent.id}", json={"current_task": "处理用户请求"})

        assert response.status_code == 200
        data = response.json()
        assert data["current_task"] == "处理用户请求"


@pytest.mark.api
@pytest.mark.integration
class TestAgentDelete:
    """测试 Agent 删除 API"""

    def test_delete_agent_success(self, client, db_session):
        """测试成功删除 Agent"""
        agent = create_test_agent(db_session, name="待删除代理")

        response = client.delete(f"/api/agents/{agent.id}")

        assert response.status_code == 200
        data = response.json()
        assert "deleted successfully" in data["message"]
        assert data["agent_id"] == agent.id

        # 验证 Agent 已被删除
        get_response = client.get(f"/api/agents/{agent.id}")
        assert get_response.status_code == 404

    def test_delete_agent_not_found(self, client):
        """测试删除不存在的 Agent"""
        response = client.delete("/api/agents/99999")

        assert response.status_code == 404

    def test_delete_agent_with_active_tasks(self, client, db_session):
        """测试删除有活跃任务的 Agent"""
        from app.models.task import TaskStatus

        agent = create_test_agent(db_session, name="有任务代理")
        project = create_test_project(db_session, name="测试项目")

        # 创建活跃任务
        create_test_task(db_session, project_id=project.id, agent_id=agent.id,
                        title="活跃任务", status=TaskStatus.IN_PROGRESS.value)

        response = client.delete(f"/api/agents/{agent.id}")

        assert response.status_code == 400
        assert "active tasks" in response.json()["detail"].lower()

    def test_delete_agent_with_completed_tasks(self, client, db_session):
        """测试删除只有已完成任务的 Agent"""
        from app.models.task import TaskStatus

        agent = create_test_agent(db_session, name="已完成任务代理")
        project = create_test_project(db_session, name="测试项目")

        # 创建已完成任务
        create_test_task(db_session, project_id=project.id, agent_id=agent.id,
                        title="已完成任务", status=TaskStatus.COMPLETED.value)

        response = client.delete(f"/api/agents/{agent.id}")

        assert response.status_code == 200


@pytest.mark.api
@pytest.mark.integration
class TestAgentStats:
    """测试 Agent 统计 API"""

    def test_get_agent_stats(self, client, db_session):
        """测试获取 Agent 统计"""
        create_test_agent(db_session, name="空闲代理1", status="idle", current_load=0, max_load=10)
        create_test_agent(db_session, name="空闲代理2", status="idle", current_load=2, max_load=10)
        create_test_agent(db_session, name="忙碌代理", status="busy", current_load=8, max_load=10)
        create_test_agent(db_session, name="离线代理", status="offline", current_load=0, max_load=10)

        response = client.get("/api/agents/stats")

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 4
        assert data["idle"] == 2
        assert data["busy"] == 1
        assert data["offline"] == 1
        assert "avg_utilization" in data

    def test_get_agent_stats_empty(self, client):
        """测试无 Agent 时的统计"""
        response = client.get("/api/agents/stats")

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0
        assert data["avg_utilization"] == 0.0

    def test_get_agent_stats_utilization_calculation(self, client, db_session):
        """测试 Agent 利用率计算"""
        # 50% 利用率
        create_test_agent(db_session, name="代理1", status="busy", current_load=5, max_load=10)
        # 100% 利用率
        create_test_agent(db_session, name="代理2", status="busy", current_load=10, max_load=10)

        response = client.get("/api/agents/stats")

        assert response.status_code == 200
        data = response.json()
        assert data["avg_utilization"] == 75.0  # (50 + 100) / 2


@pytest.mark.api
@pytest.mark.integration
class TestAgentHeartbeat:
    """测试 Agent 心跳 API"""

    def test_update_heartbeat_success(self, client, db_session):
        """测试成功更新心跳"""
        agent = create_test_agent(db_session, name="心跳测试代理")

        response = client.post(f"/api/agents/{agent.id}/heartbeat")

        assert response.status_code == 200
        data = response.json()
        assert "Heartbeat updated" in data["message"]
        assert data["agent_id"] == agent.id
        assert "timestamp" in data

    def test_update_heartbeat_not_found(self, client):
        """测试更新不存在 Agent 的心跳"""
        response = client.post("/api/agents/99999/heartbeat")

        assert response.status_code == 404

    def test_heartbeat_updates_timestamp(self, client, db_session):
        """测试心跳更新时间戳"""
        # 创建带有旧心跳时间的 Agent
        agent = create_test_agent(db_session, name="心跳测试代理")
        old_heartbeat = agent.last_heartbeat

        # 等待一小段时间
        import time
        time.sleep(0.1)

        # 更新心跳
        response = client.post(f"/api/agents/{agent.id}/heartbeat")

        assert response.status_code == 200

        # 验证心跳时间已更新
        db_session.refresh(agent)
        assert agent.last_heartbeat > old_heartbeat


@pytest.mark.api
@pytest.mark.integration
class TestAgentAssignment:
    """测试 Agent 分配相关 API"""

    def test_assign_task_to_agent(self, client, db_session):
        """测试分配任务给 Agent"""
        agent = create_test_agent(db_session, name="任务代理")
        project = create_test_project(db_session, name="测试项目")

        # 创建任务并分配给 Agent
        task_data = {
            "title": "分配任务",
            "project_id": project.id,
            "agent_id": agent.id,
            "priority": "high"
        }

        response = client.post("/api/tasks/", json=task_data)

        assert response.status_code == 200
        data = response.json()
        assert data["agent_id"] == agent.id

        # 验证 Agent 详情中包含该任务
        detail_response = client.get(f"/api/agents/{agent.id}/detail")
        detail_data = detail_response.json()
        assert detail_data["assigned_tasks_count"] >= 1


@pytest.mark.api
@pytest.mark.integration
class TestAgentEdgeCases:
    """测试 Agent 边界情况"""

    def test_create_agent_with_special_characters(self, client):
        """测试使用特殊字符创建 Agent"""
        agent_data = {"name": "代理-123_测试"}
        response = client.post("/api/agents/", json=agent_data)
        assert response.status_code == 200

    def test_create_agent_with_unicode(self, client):
        """测试使用 Unicode 字符创建 Agent"""
        agent_data = {"name": "🤖 AI代理 日本語 한국어"}
        response = client.post("/api/agents/", json=agent_data)
        assert response.status_code == 200

    def test_update_agent_with_empty_skills(self, client, db_session):
        """测试更新 Agent 为空技能列表"""
        agent = create_test_agent(db_session, name="测试代理", skills=["python"])

        response = client.put(f"/api/agents/{agent.id}", json={"skills": []})

        assert response.status_code == 200
        data = response.json()
        assert data["skills"] == []

    def test_get_agent_with_invalid_id_format(self, client):
        """测试使用无效 ID 格式获取 Agent"""
        response = client.get("/api/agents/invalid_id")
        assert response.status_code == 422

    def test_concurrent_agent_updates(self, client, db_session):
        """测试并发更新 Agent"""
        agent = create_test_agent(db_session, name="并发测试代理", current_load=0, max_load=10)

        # 模拟并发更新
        response1 = client.put(f"/api/agents/{agent.id}", json={"current_load": 3})
        response2 = client.put(f"/api/agents/{agent.id}", json={"current_load": 5})

        # 两个请求都应该成功
        assert response1.status_code == 200
        assert response2.status_code == 200

        # 最终结果应该是最后一次更新的值
        final_response = client.get(f"/api/agents/{agent.id}")
        assert final_response.status_code == 200


@pytest.mark.api
@pytest.mark.integration
class TestAgentPerformance:
    """测试 Agent API 性能"""

    def test_list_agents_performance(self, client, db_session):
        """测试 Agent 列表性能"""
        # 创建大量 Agent
        for i in range(100):
            create_test_agent(db_session, name=f"性能测试代理{i}")

        import time
        start_time = time.time()
        response = client.get("/api/agents/")
        end_time = time.time()

        assert response.status_code == 200
        assert end_time - start_time < 2.0  # 应该在 2 秒内完成

    def test_agent_stats_performance(self, client, db_session):
        """测试 Agent 统计性能"""
        # 创建大量 Agent
        for i in range(50):
            create_test_agent(db_session, name=f"统计测试代理{i}", status="busy" if i % 2 == 0 else "idle")

        import time
        start_time = time.time()
        response = client.get("/api/agents/stats")
        end_time = time.time()

        assert response.status_code == 200
        assert end_time - start_time < 1.0  # 应该在 1 秒内完成
