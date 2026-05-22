"""
Evolution Status API 测试

测试演化系统状态相关的 API 端点
"""

import pytest
from datetime import datetime, timedelta


@pytest.mark.api
class TestEvolutionStatus:
    """测试演化系统状态 API"""

    def test_get_evolution_system_status(self, client, mock_redis):
        """测试获取演化系统完整状态"""
        mock_redis.get_json.return_value = None

        response = client.get("/api/skill-evolution/evolution/status")

        assert response.status_code == 200
        data = response.json()

        assert "current_cycle" in data
        assert "cycle_history" in data
        assert "capabilities" in data
        assert "quality_trend" in data
        assert "next_scheduled_cycle" in data

    def test_current_cycle_structure(self, client, mock_redis):
        """测试当前周期信息结构"""
        mock_redis.get_json.return_value = None

        response = client.get("/api/skill-evolution/evolution/status")
        data = response.json()

        cycle = data["current_cycle"]
        assert "id" in cycle
        assert "phase" in cycle
        assert cycle["phase"] in ["red", "green", "blue", "regression"]
        assert "progress" in cycle
        assert 0 <= cycle["progress"] <= 100
        assert "started_at" in cycle
        assert "estimated_completion" in cycle

    def test_cycle_history_structure(self, client, mock_redis):
        """测试周期历史结构"""
        mock_redis.get_json.return_value = None

        response = client.get("/api/skill-evolution/evolution/status")
        data = response.json()

        history = data["cycle_history"]
        assert isinstance(history, list)
        assert len(history) > 0

        for item in history:
            assert "id" in item
            assert "status" in item
            assert item["status"] in ["completed", "running", "failed", "pending"]
            assert "duration" in item

    def test_capabilities_structure(self, client, mock_redis):
        """测试能力状态结构"""
        mock_redis.get_json.return_value = None

        response = client.get("/api/skill-evolution/evolution/status")
        data = response.json()

        capabilities = data["capabilities"]
        assert "self_iteration" in capabilities
        assert "self_optimization" in capabilities
        assert "self_repair" in capabilities
        assert "self_improvement" in capabilities

        self_iter = capabilities["self_iteration"]
        assert "enabled" in self_iter
        assert "last_run" in self_iter
        assert "trigger" in self_iter
        assert "total_iterations" in self_iter
        assert "success_rate" in self_iter

    def test_quality_trend_structure(self, client, mock_redis):
        """测试质量趋势数据结构"""
        mock_redis.get_json.return_value = None

        response = client.get("/api/skill-evolution/evolution/status")
        data = response.json()

        trend = data["quality_trend"]
        assert isinstance(trend, list)
        assert len(trend) > 0

        for item in trend:
            assert "date" in item
            assert "score" in item
            assert isinstance(item["score"], (int, float))

    def test_get_capabilities_status(self, client, mock_redis):
        """测试获取系统能力状态"""
        mock_redis.get_json.return_value = None

        response = client.get("/api/skill-evolution/evolution/status/capabilities")

        assert response.status_code == 200
        data = response.json()

        assert "self_iteration" in data
        assert "self_optimization" in data
        assert "self_repair" in data
        assert "self_improvement" in data

    def test_get_cycle_history(self, client, mock_redis):
        """测试获取周期历史列表"""
        mock_redis.get_json.return_value = None

        response = client.get("/api/skill-evolution/evolution/status/cycles?limit=5")

        assert response.status_code == 200
        data = response.json()

        assert "total" in data
        assert "cycles" in data
        assert len(data["cycles"]) <= 5

    def test_evolution_status_cache(self, client, mock_redis):
        """测试演化状态缓存功能"""
        cached_data = {
            "current_cycle": {"id": "test", "phase": "green", "progress": 50,
                             "started_at": "2024-01-01T00:00:00"},
            "cycle_history": [],
            "capabilities": {},
            "quality_trend": [],
            "next_scheduled_cycle": None,
            "system_uptime_seconds": 1000,
            "active_tasks": 1
        }
        mock_redis.get_json.return_value = cached_data

        response = client.get("/api/skill-evolution/evolution/status")

        assert response.status_code == 200
        data = response.json()
        assert data["current_cycle"]["id"] == "test"

    def test_self_iteration_enabled(self, client, mock_redis):
        """测试自迭代能力是否启用"""
        mock_redis.get_json.return_value = None

        response = client.get("/api/skill-evolution/evolution/status/capabilities")
        data = response.json()

        assert data["self_iteration"]["enabled"] is True
        assert data["self_iteration"]["total_iterations"] >= 0

    def test_self_repair_issues_fixed(self, client, mock_redis):
        """测试自修复能力的问题修复数"""
        mock_redis.get_json.return_value = None

        response = client.get("/api/skill-evolution/evolution/status/capabilities")
        data = response.json()

        repair_info = data["self_repair"]
        assert "issues_fixed" in repair_info
        assert repair_info["issues_fixed"] >= 0
        assert "last_repair" in repair_info

    def test_quality_trend_scores_range(self, client, mock_redis):
        """测试质量趋势分数范围"""
        mock_redis.get_json.return_value = None

        response = client.get("/api/skill-evolution/evolution/status")
        data = response.json()

        for item in data["quality_trend"]:
            assert 0 <= item["score"] <= 100
