"""
Comprehensive Health API 测试

测试综合健康检查相关的 API 端点
"""

import pytest
from datetime import datetime


@pytest.mark.api
class TestHealthComprehensive:
    """测试综合健康检查 API"""

    def test_get_comprehensive_health(self, client, mock_redis):
        """测试获取综合健康报告"""
        mock_redis.get_json.return_value = None

        response = client.get("/api/health/comprehensive")

        assert response.status_code == 200
        data = response.json()

        assert "overall_score" in data
        assert "overall_status" in data
        assert 0 <= data["overall_score"] <= 100
        assert data["overall_status"] in ["healthy", "warning", "critical", "unknown"]

    def test_overall_status_values(self, client, mock_redis):
        """测试总体状态的有效值"""
        mock_redis.get_json.return_value = None

        response = client.get("/api/health/comprehensive")
        data = response.json()

        valid_statuses = ["healthy", "warning", "critical", "unknown"]
        assert data["overall_status"] in valid_statuses

    def test_dimensions_structure(self, client, mock_redis):
        """测试各维度详情结构"""
        mock_redis.get_json.return_value = None

        response = client.get("/api/health/comprehensive")
        data = response.json()

        dimensions = data["dimensions"]
        assert isinstance(dimensions, list)
        assert len(dimensions) >= 4

        for dim in dimensions:
            assert "name" in dim
            assert "status" in dim
            assert "score" in dim
            assert 0 <= dim["score"] <= 100
            assert "details" in dim
            assert "issues" in dim
            assert "warnings" in dim
            assert "last_check" in dim

    def test_path_configuration_dimension(self, client, mock_redis):
        """测试路径配置维度"""
        mock_redis.get_json.return_value = None

        response = client.get("/api/health/comprehensive")
        data = response.json()

        path_dim = next(
            (d for d in data["dimensions"] if d["name"] == "path_configuration"),
            None
        )
        assert path_dim is not None

        paths = path_dim["details"]["paths"]
        assert isinstance(paths, list)
        assert len(paths) > 0

        for path_info in paths:
            assert "path" in path_info
            assert "exists" in path_info
            assert "accessible" in path_info

    def test_database_connection_dimension(self, client, mock_redis):
        """测试数据库连接维度"""
        mock_redis.get_json.return_value = None

        response = client.get("/api/health/comprehensive")
        data = response.json()

        db_dim = next(
            (d for d in data["dimensions"] if d["name"] == "database_connection"),
            None
        )
        assert db_dim is not None

        db_details = db_dim["details"]
        assert "status" in db_details
        assert "connected" in db_details
        assert "response_time_ms" in db_details

    def test_system_resources_dimension(self, client, mock_redis):
        """测试系统资源维度"""
        mock_redis.get_json.return_value = None

        response = client.get("/api/health/comprehensive")
        data = response.json()

        resource_dim = next(
            (d for d in data["dimensions"] if d["name"] == "system_resources"),
            None
        )
        assert resource_dim is not None

        resources = resource_dim["details"]
        assert "disk_usage_percent" in resources
        assert "memory_usage_percent" in resources
        assert "cpu_count" in resources
        assert 0 <= resources["disk_usage_percent"] <= 100
        assert 0 <= resources["memory_usage_percent"] <= 100

    def test_critical_issues_list(self, client, mock_redis):
        """测试严重问题列表"""
        mock_redis.get_json.return_value = None

        response = client.get("/api/health/comprehensive")
        data = response.json()

        assert "critical_issues" in data
        assert isinstance(data["critical_issues"], list)

    def test_warnings_list(self, client, mock_redis):
        """测试警告列表"""
        mock_redis.get_json.return_value = None

        response = client.get("/api/health/comprehensive")
        data = response.json()

        assert "warnings" in data
        assert isinstance(data["warnings"], list)

    def test_recommendations_list(self, client, mock_redis):
        """测试建议列表"""
        mock_redis.get_json.return_value = None

        response = client.get("/api/health/comprehensive")
        data = response.json()

        assert "recommendations" in data
        assert isinstance(data["recommendations"], list)
        assert len(data["recommendations"]) > 0

    def test_last_successful_evolution(self, client, mock_redis):
        """测试上次成功演化时间"""
        mock_redis.get_json.return_value = None

        response = client.get("/api/health/comprehensive")
        data = response.json()

        assert "last_successful_evolution" in data

    def test_checked_at_timestamp(self, client, mock_redis):
        """测试检查时间戳"""
        mock_redis.get_json.return_value = None

        response = client.get("/api/health/comprehensive")
        data = response.json()

        assert "checked_at" in data

    def test_get_health_dimensions(self, client, mock_redis):
        """测试获取各健康维度详情"""
        mock_redis.get_json.return_value = None

        response = client.get("/api/health/comprehensive/dimensions")

        assert response.status_code == 200
        data = response.json()

        assert "dimensions" in data
        assert "total_dimensions" in data
        assert "healthy_count" in data
        assert "warning_count" in data
        assert "critical_count" in data

        assert data["total_dimensions"] == len(data["dimensions"])
        assert data["healthy_count"] + data["warning_count"] + data["critical_count"] == data["total_dimensions"]

    def test_service_dependencies_dimension(self, client, mock_redis):
        """测试服务依赖维度"""
        mock_redis.get_json.return_value = None

        response = client.get("/api/health/comprehensive")
        data = response.json()

        service_dim = next(
            (d for d in data["dimensions"] if d["name"] == "service_dependencies"),
            None
        )
        assert service_dim is not None

        services = service_dim["details"]["services"]
        assert isinstance(services, list)
        assert len(services) > 0

        for service in services:
            assert "service_name" in service
            assert "status" in service
            assert "available" in service

    def test_script_availability_dimension(self, client, mock_redis):
        """测试脚本可用性维度"""
        mock_redis.get_json.return_value = None

        response = client.get("/api/health/comprehensive")
        data = response.json()

        script_dim = next(
            (d for d in data["dimensions"] if d["name"] == "script_availability"),
            None
        )
        assert script_dim is not None

        scripts = script_dim["details"]["scripts"]
        assert isinstance(scripts, list)

        for script in scripts:
            assert "script_name" in script
            assert "exists" in script
            assert "syntax_valid" in script
