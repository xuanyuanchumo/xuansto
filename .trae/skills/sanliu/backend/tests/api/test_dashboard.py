"""
Dashboard API 测试

测试 Dashboard 相关的 API 端点
"""

import pytest
from datetime import datetime, timedelta
from tests.conftest import create_test_project, create_test_task, create_test_agent


def create_test_skill_call(db, **kwargs):
    """创建测试 Skill Call 的辅助函数"""
    from app.models.skill_call import SkillCall

    call_data = {
        "skill_name": kwargs.get("skill_name", "test_skill"),
        "caller": kwargs.get("caller", "test_caller"),
        "status": kwargs.get("status", "completed"),
        "details": kwargs.get("details", {})
    }

    call = SkillCall(**call_data)
    db.add(call)
    db.commit()
    db.refresh(call)
    return call


def create_test_assignment(db, **kwargs):
    """创建测试 Assignment 的辅助函数"""
    from app.models.assignment import Assignment

    assignment_data = {
        "task_id": kwargs.get("task_id"),
        "agent_id": kwargs.get("agent_id"),
        "status": kwargs.get("status", "assigned")
    }

    assignment = Assignment(**assignment_data)
    db.add(assignment)
    db.commit()
    db.refresh(assignment)
    return assignment


@pytest.mark.api
@pytest.mark.integration
class TestDashboardStats:
    """测试 Dashboard 统计 API"""

    def test_get_dashboard_stats_empty(self, client, mock_redis):
        """测试空数据时的仪表盘统计"""
        mock_redis.get_json.return_value = None

        response = client.get("/api/dashboard/stats")

        assert response.status_code == 200
        data = response.json()
        assert data["total_skill_calls"] == 0
        assert data["active_agents"] == 0
        assert data["total_agents"] == 0
        assert data["pending_tasks"] == 0
        assert data["active_assignments"] == 0
        assert data["recent_calls"] == []
        assert data["status_distribution"] == {}

    def test_get_dashboard_stats_with_data(self, client, db_session, mock_redis):
        """测试有数据时的仪表盘统计"""
        from app.models.task import TaskStatus

        # 创建测试数据
        project = create_test_project(db_session, name="测试项目")
        agent1 = create_test_agent(db_session, name="忙碌代理", status="busy")
        agent2 = create_test_agent(db_session, name="空闲代理", status="idle")

        # 创建任务
        create_test_task(db_session, project_id=project.id, title="待处理任务",
                        status=TaskStatus.PENDING.value)
        create_test_task(db_session, project_id=project.id, title="进行中任务",
                        status=TaskStatus.IN_PROGRESS.value)
        create_test_task(db_session, project_id=project.id, title="已完成任务",
                        status=TaskStatus.COMPLETED.value)

        # 创建 Skill Call
        create_test_skill_call(db_session, skill_name="code_generation", status="completed")
        create_test_skill_call(db_session, skill_name="code_review", status="running")
        create_test_skill_call(db_session, skill_name="test_execution", status="failed")

        # 创建 Assignment
        create_test_assignment(db_session, task_id=1, agent_id=agent1.id, status="assigned")

        mock_redis.get_json.return_value = None

        response = client.get("/api/dashboard/stats")

        assert response.status_code == 200
        data = response.json()

        # 验证统计数据
        assert data["total_skill_calls"] == 3
        assert data["active_agents"] == 1  # busy agents
        assert data["total_agents"] == 2
        assert data["pending_tasks"] == 1
        assert data["active_assignments"] == 1
        assert len(data["recent_calls"]) <= 10
        assert "status_distribution" in data

    def test_get_dashboard_stats_skill_calls_count(self, client, db_session, mock_redis):
        """测试仪表盘 Skill Call 计数"""
        # 创建多个 Skill Call
        for i in range(5):
            create_test_skill_call(db_session, skill_name=f"skill_{i}", status="completed")

        mock_redis.get_json.return_value = None

        response = client.get("/api/dashboard/stats")

        assert response.status_code == 200
        data = response.json()
        assert data["total_skill_calls"] == 5

    def test_get_dashboard_stats_agent_count(self, client, db_session, mock_redis):
        """测试仪表盘 Agent 计数"""
        create_test_agent(db_session, name="代理1", status="busy")
        create_test_agent(db_session, name="代理2", status="busy")
        create_test_agent(db_session, name="代理3", status="idle")
        create_test_agent(db_session, name="代理4", status="offline")

        mock_redis.get_json.return_value = None

        response = client.get("/api/dashboard/stats")

        assert response.status_code == 200
        data = response.json()
        assert data["total_agents"] == 4
        assert data["active_agents"] == 2  # busy agents

    def test_get_dashboard_stats_task_count(self, client, db_session, mock_redis):
        """测试仪表盘 Task 计数"""
        from app.models.task import TaskStatus

        project = create_test_project(db_session, name="测试项目")

        # 创建不同状态的任务
        create_test_task(db_session, project_id=project.id, title="任务1",
                        status=TaskStatus.PENDING.value)
        create_test_task(db_session, project_id=project.id, title="任务2",
                        status=TaskStatus.PENDING.value)
        create_test_task(db_session, project_id=project.id, title="任务3",
                        status=TaskStatus.IN_PROGRESS.value)
        create_test_task(db_session, project_id=project.id, title="任务4",
                        status=TaskStatus.COMPLETED.value)

        mock_redis.get_json.return_value = None

        response = client.get("/api/dashboard/stats")

        assert response.status_code == 200
        data = response.json()
        assert data["pending_tasks"] == 2

    def test_get_dashboard_stats_assignment_count(self, client, db_session, mock_redis):
        """测试仪表盘 Assignment 计数"""
        from app.models.task import TaskStatus

        project = create_test_project(db_session, name="测试项目")
        agent = create_test_agent(db_session, name="测试代理")

        task1 = create_test_task(db_session, project_id=project.id, title="任务1")
        task2 = create_test_task(db_session, project_id=project.id, title="任务2")

        create_test_assignment(db_session, task_id=task1.id, agent_id=agent.id, status="assigned")
        create_test_assignment(db_session, task_id=task2.id, agent_id=agent.id, status="completed")

        mock_redis.get_json.return_value = None

        response = client.get("/api/dashboard/stats")

        assert response.status_code == 200
        data = response.json()
        assert data["active_assignments"] == 1

    def test_get_dashboard_stats_recent_calls(self, client, db_session, mock_redis):
        """测试仪表盘最近调用记录"""
        # 创建多个 Skill Call
        for i in range(15):
            create_test_skill_call(db_session, skill_name=f"skill_{i}", status="completed")

        mock_redis.get_json.return_value = None

        response = client.get("/api/dashboard/stats")

        assert response.status_code == 200
        data = response.json()
        assert len(data["recent_calls"]) <= 10

        # 验证最近调用的数据结构
        if data["recent_calls"]:
            recent_call = data["recent_calls"][0]
            assert "id" in recent_call
            assert "skill_name" in recent_call
            assert "status" in recent_call
            assert "start_time" in recent_call

    def test_get_dashboard_stats_status_distribution(self, client, db_session, mock_redis):
        """测试仪表盘状态分布"""
        # 创建不同状态的 Skill Call
        create_test_skill_call(db_session, skill_name="skill_1", status="completed")
        create_test_skill_call(db_session, skill_name="skill_2", status="completed")
        create_test_skill_call(db_session, skill_name="skill_3", status="running")
        create_test_skill_call(db_session, skill_name="skill_4", status="failed")
        create_test_skill_call(db_session, skill_name="skill_5", status="started")

        mock_redis.get_json.return_value = None

        response = client.get("/api/dashboard/stats")

        assert response.status_code == 200
        data = response.json()
        status_dist = data["status_distribution"]
        assert status_dist["completed"] == 2
        assert status_dist["running"] == 1
        assert status_dist["failed"] == 1
        assert status_dist["started"] == 1


@pytest.mark.api
@pytest.mark.integration
class TestDashboardCache:
    """测试 Dashboard 缓存机制"""

    def test_dashboard_stats_uses_cache(self, client, db_session, mock_redis):
        """测试仪表盘统计使用缓存"""
        cached_data = {
            "total_skill_calls": 100,
            "active_agents": 5,
            "total_agents": 10,
            "pending_tasks": 3,
            "active_assignments": 2,
            "recent_calls": [],
            "status_distribution": {"completed": 100}
        }
        mock_redis.get_json.return_value = cached_data

        response = client.get("/api/dashboard/stats")

        assert response.status_code == 200
        data = response.json()
        assert data["total_skill_calls"] == 100
        assert data["active_agents"] == 5

    def test_dashboard_stats_cache_miss(self, client, db_session, mock_redis):
        """测试仪表盘统计缓存未命中"""
        create_test_skill_call(db_session, skill_name="test_skill")
        mock_redis.get_json.return_value = None

        response = client.get("/api/dashboard/stats")

        assert response.status_code == 200
        data = response.json()
        assert data["total_skill_calls"] == 1
        # 验证缓存被设置
        mock_redis.set_json.assert_called_once()

    def test_dashboard_stats_cache_invalidation(self, client, db_session, mock_redis):
        """测试仪表盘缓存失效"""
        mock_redis.get_json.return_value = None

        # 第一次请求
        response1 = client.get("/api/dashboard/stats")
        assert response1.status_code == 200

        # 添加新数据
        create_test_skill_call(db_session, skill_name="new_skill")

        # 第二次请求应该重新计算
        mock_redis.get_json.return_value = None
        response2 = client.get("/api/dashboard/stats")
        assert response2.status_code == 200


@pytest.mark.api
@pytest.mark.integration
class TestDashboardIntegration:
    """测试 Dashboard 集成数据"""

    def test_dashboard_comprehensive_stats(self, client, db_session, mock_redis):
        """测试仪表盘综合统计数据"""
        from app.models.task import TaskStatus

        # 创建完整的测试数据集
        project = create_test_project(db_session, name="综合测试项目")

        # 创建 Agents
        agent1 = create_test_agent(db_session, name="开发代理1", status="busy",
                                   skills=["python", "javascript"])
        agent2 = create_test_agent(db_session, name="开发代理2", status="idle",
                                   skills=["java", "kotlin"])
        agent3 = create_test_agent(db_session, name="测试代理", status="busy",
                                   skills=["testing", "automation"])

        # 创建 Tasks
        task1 = create_test_task(db_session, project_id=project.id, title="功能开发",
                                status=TaskStatus.IN_PROGRESS.value, priority="high",
                                agent_id=agent1.id)
        task2 = create_test_task(db_session, project_id=project.id, title="代码审查",
                                status=TaskStatus.PENDING.value, priority="medium")
        task3 = create_test_task(db_session, project_id=project.id, title="单元测试",
                                status=TaskStatus.COMPLETED.value, priority="high",
                                agent_id=agent3.id)

        # 创建 Skill Calls
        create_test_skill_call(db_session, skill_name="code_generation",
                              status="completed", caller="agent_001")
        create_test_skill_call(db_session, skill_name="code_review",
                              status="completed", caller="agent_002")
        create_test_skill_call(db_session, skill_name="test_execution",
                              status="running", caller="agent_003")
        create_test_skill_call(db_session, skill_name="bug_fixing",
                              status="failed", caller="agent_001")

        # 创建 Assignments
        create_test_assignment(db_session, task_id=task1.id, agent_id=agent1.id, status="assigned")
        create_test_assignment(db_session, task_id=task2.id, agent_id=agent2.id, status="pending")

        mock_redis.get_json.return_value = None

        response = client.get("/api/dashboard/stats")

        assert response.status_code == 200
        data = response.json()

        # 验证所有统计数据
        assert data["total_skill_calls"] == 4
        assert data["active_agents"] == 2  # busy agents
        assert data["total_agents"] == 3
        assert data["pending_tasks"] == 1  # PENDING status
        assert data["active_assignments"] == 1  # assigned status
        assert len(data["recent_calls"]) == 4

        # 验证状态分布
        status_dist = data["status_distribution"]
        assert status_dist["completed"] == 2
        assert status_dist["running"] == 1
        assert status_dist["failed"] == 1

    def test_dashboard_data_consistency(self, client, db_session, mock_redis):
        """测试仪表盘数据一致性"""
        from app.models.task import TaskStatus

        # 创建关联数据
        project = create_test_project(db_session, name="一致性测试项目")
        agent = create_test_agent(db_session, name="一致性测试代理", status="busy")
        task = create_test_task(db_session, project_id=project.id, title="一致性测试任务",
                               status=TaskStatus.IN_PROGRESS.value, agent_id=agent.id)

        create_test_skill_call(db_session, skill_name="consistency_test", status="completed")
        create_test_assignment(db_session, task_id=task.id, agent_id=agent.id, status="assigned")

        mock_redis.get_json.return_value = None

        response = client.get("/api/dashboard/stats")

        assert response.status_code == 200
        data = response.json()

        # 验证数据一致性
        assert data["total_agents"] >= data["active_agents"]
        assert data["total_skill_calls"] == sum(data["status_distribution"].values())
        assert len(data["recent_calls"]) <= data["total_skill_calls"]


@pytest.mark.api
@pytest.mark.integration
class TestDashboardEdgeCases:
    """测试 Dashboard 边界情况"""

    def test_dashboard_with_large_dataset(self, client, db_session, mock_redis):
        """测试大数据集下的仪表盘"""
        from app.models.task import TaskStatus

        project = create_test_project(db_session, name="大数据测试项目")

        # 创建大量数据
        for i in range(50):
            create_test_skill_call(db_session, skill_name=f"skill_{i}",
                                  status="completed" if i % 2 == 0 else "running")

        for i in range(20):
            create_test_agent(db_session, name=f"代理{i}",
                             status="busy" if i % 3 == 0 else "idle")

        for i in range(30):
            create_test_task(db_session, project_id=project.id, title=f"任务{i}",
                            status=TaskStatus.PENDING.value if i % 2 == 0 else TaskStatus.COMPLETED.value)

        mock_redis.get_json.return_value = None

        response = client.get("/api/dashboard/stats")

        assert response.status_code == 200
        data = response.json()
        assert data["total_skill_calls"] == 50
        assert data["total_agents"] == 20
        assert data["pending_tasks"] == 15
        assert len(data["recent_calls"]) <= 10  # 限制返回数量

    def test_dashboard_with_no_active_agents(self, client, db_session, mock_redis):
        """测试无活跃 Agent 时的仪表盘"""
        create_test_agent(db_session, name="离线代理1", status="offline")
        create_test_agent(db_session, name="离线代理2", status="offline")

        mock_redis.get_json.return_value = None

        response = client.get("/api/dashboard/stats")

        assert response.status_code == 200
        data = response.json()
        assert data["active_agents"] == 0
        assert data["total_agents"] == 2

    def test_dashboard_with_all_failed_calls(self, client, db_session, mock_redis):
        """测试所有 Skill Call 都失败时的仪表盘"""
        for i in range(5):
            create_test_skill_call(db_session, skill_name=f"failed_skill_{i}",
                                  status="failed")

        mock_redis.get_json.return_value = None

        response = client.get("/api/dashboard/stats")

        assert response.status_code == 200
        data = response.json()
        assert data["total_skill_calls"] == 5
        assert data["status_distribution"]["failed"] == 5
        assert "completed" not in data["status_distribution"] or data["status_distribution"]["completed"] == 0


@pytest.mark.api
@pytest.mark.integration
class TestDashboardRealTime:
    """测试 Dashboard 实时数据"""

    def test_dashboard_reflects_new_data(self, client, db_session, mock_redis):
        """测试仪表盘反映新数据"""
        mock_redis.get_json.return_value = None

        # 初始状态
        response1 = client.get("/api/dashboard/stats")
        assert response1.status_code == 200
        initial_count = response1.json()["total_skill_calls"]

        # 添加新数据
        create_test_skill_call(db_session, skill_name="new_skill")

        # 再次查询
        mock_redis.get_json.return_value = None
        response2 = client.get("/api/dashboard/stats")
        assert response2.status_code == 200
        new_count = response2.json()["total_skill_calls"]

        assert new_count == initial_count + 1

    def test_dashboard_with_mixed_status_agents(self, client, db_session, mock_redis):
        """测试混合状态 Agent 的仪表盘"""
        create_test_agent(db_session, name="代理1", status="idle")
        create_test_agent(db_session, name="代理2", status="busy")
        create_test_agent(db_session, name="代理3", status="offline")
        create_test_agent(db_session, name="代理4", status="idle")

        mock_redis.get_json.return_value = None

        response = client.get("/api/dashboard/stats")

        assert response.status_code == 200
        data = response.json()
        assert data["total_agents"] == 4
        assert data["active_agents"] == 1  # only busy


@pytest.mark.api
@pytest.mark.integration
class TestDashboardPerformance:
    """测试 Dashboard 性能"""

    def test_dashboard_stats_performance(self, client, db_session, mock_redis):
        """测试仪表盘统计性能"""
        # 创建大量数据
        for i in range(100):
            create_test_skill_call(db_session, skill_name=f"skill_{i}")

        mock_redis.get_json.return_value = None

        import time
        start_time = time.time()
        response = client.get("/api/dashboard/stats")
        end_time = time.time()

        assert response.status_code == 200
        assert end_time - start_time < 3.0  # 应该在 3 秒内完成

    def test_dashboard_with_cache_performance(self, client, db_session, mock_redis):
        """测试带缓存的仪表盘性能"""
        cached_data = {
            "total_skill_calls": 1000,
            "active_agents": 50,
            "total_agents": 100,
            "pending_tasks": 25,
            "active_assignments": 30,
            "recent_calls": [],
            "status_distribution": {"completed": 800, "running": 200}
        }
        mock_redis.get_json.return_value = cached_data

        import time
        start_time = time.time()
        response = client.get("/api/dashboard/stats")
        end_time = time.time()

        assert response.status_code == 200
        assert end_time - start_time < 0.5  # 缓存应该在 0.5 秒内返回
