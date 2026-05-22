"""
Reports Generate API 测试

测试报告生成相关的 API 端点
"""

import pytest
from datetime import datetime
import os
import json


@pytest.mark.api
class TestReportsGenerate:
    """测试报告生成 API"""

    def test_generate_quality_report(self, client):
        """测试生成质量报告"""
        request_data = {
            "report_type": "quality_report",
            "format": "markdown"
        }

        response = client.post("/api/reports/generate", json=request_data)

        assert response.status_code == 200
        data = response.json()

        assert "task_id" in data
        assert data["report_type"] == "quality_report"
        assert data["status"] in ["pending", "generating", "completed", "failed"]
        assert "message" in data
        assert "estimated_time_seconds" in data

    def test_generate_test_report(self, client):
        """测试生成测试报告"""
        request_data = {
            "report_type": "test_report",
            "format": "json"
        }

        response = client.post("/api/reports/generate", json=request_data)

        assert response.status_code == 200
        data = response.json()

        assert data["report_type"] == "test_report"
        assert "task_id" in data

    def test_generate_evolution_report(self, client):
        """测试生成演化报告"""
        request_data = {
            "report_type": "evolution_report",
            "format": "markdown",
            "version": "v1.0"
        }

        response = client.post("/api/reports/generate", json=request_data)

        assert response.status_code == 200
        data = response.json()

        assert data["report_type"] == "evolution_report"

    def test_generate_health_report(self, client):
        """测试生成健康报告"""
        request_data = {
            "report_type": "health_report",
            "format": "html"
        }

        response = client.post("/api/reports/generate", json=request_data)

        assert response.status_code == 200
        data = response.json()

        assert data["report_type"] == "health_report"

    def test_generate_comprehensive_report(self, client):
        """测试生成完整综合报告"""
        request_data = {
            "report_type": "comprehensive_report",
            "format": "markdown",
            "version": "v2.0",
            "include_details": True
        }

        response = client.post("/api/reports/generate", json=request_data)

        assert response.status_code == 200
        data = response.json()

        assert data["report_type"] == "comprehensive_report"
        assert data["estimated_time_seconds"] > 0

    def test_generate_path_validation_report(self, client):
        """测试生成路径验证报告"""
        request_data = {
            "report_type": "path_validation_report",
            "format": "json"
        }

        response = client.post("/api/reports/generate", json=request_data)

        assert response.status_code == 200
        data = response.json()

        assert data["report_type"] == "path_validation_report"

    def test_invalid_report_type(self, client):
        """测试无效的报告类型"""
        request_data = {
            "report_type": "invalid_type",
            "format": "markdown"
        }

        response = client.post("/api/reports/generate", json=request_data)

        assert response.status_code == 422

    def test_get_report_task_status(self, client):
        """测试查询报告任务状态"""
        generate_response = client.post("/api/reports/generate", json={
            "report_type": "quality_report",
            "format": "markdown"
        })
        task_data = generate_response.json()
        task_id = task_data["task_id"]

        status_response = client.get(f"/api/reports/tasks/{task_id}")

        assert status_response.status_code == 200
        status_data = status_response.json()

        assert status_data["task_id"] == task_id
        assert "status" in status_data
        assert "progress" in status_data
        assert 0 <= status_data["progress"] <= 100

    def test_get_nonexistent_task_status(self, client):
        """测试查询不存在的任务"""
        response = client.get("/api/reports/tasks/nonexistent_task_12345")

        assert response.status_code == 404

    def test_get_all_report_tasks(self, client):
        """测试获取所有报告任务列表"""
        client.post("/api/reports/generate", json={
            "report_type": "test_report",
            "format": "json"
        })

        response = client.get("/api/reports/tasks")

        assert response.status_code == 200
        data = response.json()

        assert "total" in data
        assert "tasks" in data
        assert isinstance(data["tasks"], list)
        assert data["total"] >= 1

    def test_filter_tasks_by_status(self, client):
        """测试按状态筛选任务"""
        for _ in range(3):
            client.post("/api/reports/generate", json={
                "report_type": "quality_report",
                "format": "markdown"
            })

        response = client.get("/api/reports/tasks?status=pending&limit=10")

        assert response.status_code == 200
        data = response.json()

        for task in data["tasks"]:
            assert task["status"] == "pending"

    def test_tasks_limit_parameter(self, client):
        """测试返回数量限制参数"""
        for _ in range(5):
            client.post("/api/reports/generate", json={
                "report_type": "test_report",
                "format": "json"
            })

        response = client.get("/api/reports/tasks?limit=3")

        assert response.status_code == 200
        data = response.json()

        assert len(data["tasks"]) <= 3

    def test_report_with_version(self, client):
        """测试带版本号的报告生成"""
        request_data = {
            "report_type": "quality_report",
            "format": "markdown",
            "version": "v1.2.3"
        }

        response = client.post("/api/reports/generate", json=request_data)

        assert response.status_code == 200
        data = response.json()
        assert "task_id" in data

    def test_report_with_date_range(self, client):
        """测试带日期范围的报告生成"""
        request_data = {
            "report_type": "evolution_report",
            "format": "json",
            "start_date": "2024-01-01T00:00:00",
            "end_date": "2024-01-31T23:59:59"
        }

        response = client.post("/api/reports/generate", json=request_data)

        assert response.status_code == 200
        data = response.json()
        assert data["report_type"] == "evolution_report"

    def test_different_formats(self, client):
        """测试不同输出格式"""
        formats = ["markdown", "json", "html"]

        for fmt in formats:
            response = client.post("/api/reports/generate", json={
                "report_type": "health_report",
                "format": fmt
            })
            assert response.status_code == 200

    def test_task_info_structure(self, client):
        """测试任务信息结构完整性"""
        response = client.post("/api/reports/generate", json={
            "report_type": "quality_report",
            "format": "markdown"
        })
        task_data = response.json()

        status_response = client.get(f"/api/reports/tasks/{task_data['task_id']}")
        status_data = status_response.json()

        required_fields = [
            "task_id", "report_type", "status", "created_at",
            "completed_at", "progress", "file_path", "error_message"
        ]

        for field in required_fields:
            assert field in status_data, f"Missing field: {field}"
