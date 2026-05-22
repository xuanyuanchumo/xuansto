"""
Quality Monitor API 测试

测试质量监控相关的 API 端点
"""

import pytest
from datetime import datetime, timedelta
from tests.conftest import create_test_project, create_test_task, create_test_agent


def create_test_skill_call(db, **kwargs):
    """创建测试 Skill Call 的辅助函数"""
    from app.models.skill_call import SkillCall

    details = kwargs.get("details", {})
    error_message = kwargs.get("error_message", None)
    if error_message:
        details["error_message"] = error_message

    call_data = {
        "skill_name": kwargs.get("skill_name", "test_skill"),
        "caller": kwargs.get("caller", "test_caller"),
        "status": kwargs.get("status", "completed"),
        "details": details
    }

    call = SkillCall(**call_data)
    db.add(call)
    db.commit()
    db.refresh(call)
    return call


@pytest.mark.api
@pytest.mark.integration
class TestPerformanceMetrics:
    """测试性能指标 API"""

    def test_get_performance_metrics_empty(self, client, mock_redis):
        """测试空数据时的性能指标"""
        mock_redis.get_json.return_value = None

        response = client.get("/api/quality/performance")

        assert response.status_code == 200
        data = response.json()
        assert "avg_response_time_ms" in data
        assert "p95_response_time_ms" in data
        assert "p99_response_time_ms" in data
        assert "throughput_per_sec" in data
        assert "error_rate_percent" in data
        assert "slow_request_count" in data
        assert "total_request_count" in data

    def test_get_performance_metrics_with_data(self, client, db_session, mock_redis):
        """测试有数据时的性能指标"""
        create_test_skill_call(db_session, skill_name="skill_1", status="completed")
        create_test_skill_call(db_session, skill_name="skill_2", status="failed")
        create_test_skill_call(db_session, skill_name="skill_3", status="completed")

        mock_redis.get_json.return_value = None

        response = client.get("/api/quality/performance")

        assert response.status_code == 200
        data = response.json()
        assert data["total_request_count"] >= 0
        assert data["error_rate_percent"] >= 0

    def test_get_realtime_performance(self, client, mock_redis):
        """测试实时性能数据"""
        mock_redis.get_json.return_value = None

        response = client.get("/api/quality/realtime/performance")

        assert response.status_code == 200
        data = response.json()
        assert "cpu_usage_percent" in data
        assert "memory_usage_percent" in data
        assert "disk_usage_percent" in data
        assert "avg_response_time_ms" in data
        assert "requests_per_second" in data
        assert "error_rate_percent" in data
        assert "timestamp" in data


@pytest.mark.api
@pytest.mark.integration
class TestErrorStatistics:
    """测试错误统计 API"""

    def test_get_error_statistics_empty(self, client, mock_redis):
        """测试空数据时的错误统计"""
        mock_redis.get_json.return_value = None

        response = client.get("/api/quality/errors")

        assert response.status_code == 200
        data = response.json()
        assert "total_errors" in data
        assert "error_rate" in data
        assert "errors_by_type" in data
        assert "errors_by_endpoint" in data
        assert "recent_errors" in data
        assert "error_trend" in data

    def test_get_error_statistics_with_data(self, client, db_session, mock_redis):
        """测试有数据时的错误统计"""
        create_test_skill_call(db_session, skill_name="skill_1", status="failed", 
                              error_message="ConnectionError: Connection timeout")
        create_test_skill_call(db_session, skill_name="skill_2", status="failed",
                              error_message="TimeoutError: Request timeout")
        create_test_skill_call(db_session, skill_name="skill_3", status="completed")

        mock_redis.get_json.return_value = None

        response = client.get("/api/quality/errors?hours=24")

        assert response.status_code == 200
        data = response.json()
        assert data["total_errors"] == 2
        assert data["error_rate"] > 0
        assert len(data["recent_errors"]) <= 20

    def test_get_detailed_error_stats(self, client, db_session, mock_redis):
        """测试详细错误统计"""
        create_test_skill_call(db_session, skill_name="skill_1", status="failed",
                              error_message="ConnectionError: Connection timeout")
        create_test_skill_call(db_session, skill_name="skill_2", status="failed",
                              error_message="TimeoutError: Request timeout")

        mock_redis.get_json.return_value = None

        response = client.get("/api/quality/errors/detailed?hours=24")

        assert response.status_code == 200
        data = response.json()
        assert "time_range" in data
        assert "total_errors" in data
        assert "error_rate_percent" in data
        assert "errors_by_hour" in data
        assert "errors_by_skill" in data
        assert "errors_by_error_type" in data
        assert "errors_by_severity" in data
        assert "top_error_messages" in data
        assert "error_hotspots" in data


@pytest.mark.api
@pytest.mark.integration
class TestCodeQuality:
    """测试代码质量 API"""

    def test_get_code_quality_score(self, client, mock_redis):
        """测试代码质量评分"""
        mock_redis.get_json.return_value = None

        response = client.get("/api/quality/code-quality")

        assert response.status_code == 200
        data = response.json()
        assert "overall_score" in data
        assert "maintainability_index" in data
        assert "cyclomatic_complexity" in data
        assert "code_duplication_percent" in data
        assert "technical_debt_hours" in data
        assert "code_smell_count" in data
        assert "security_issues" in data
        assert "code_coverage_percent" in data
        assert "documentation_coverage_percent" in data
        assert 0 <= data["overall_score"] <= 100

    def test_get_enhanced_code_quality(self, client, mock_redis):
        """测试增强代码质量评分"""
        mock_redis.get_json.return_value = None

        response = client.get("/api/quality/code-quality/enhanced")

        assert response.status_code == 200
        data = response.json()
        assert "overall_score" in data
        assert "maintainability_index" in data
        assert "cyclomatic_complexity" in data
        assert "cognitive_complexity" in data
        assert "code_duplication_percent" in data
        assert "technical_debt_hours" in data
        assert "code_smells" in data
        assert "security_vulnerabilities" in data
        assert "bug_risk_score" in data
        assert "dependency_health" in data
        assert "quality_trend" in data


@pytest.mark.api
@pytest.mark.integration
class TestTestCoverage:
    """测试测试覆盖率 API"""

    def test_get_test_coverage_metrics(self, client, mock_redis):
        """测试测试覆盖率指标"""
        mock_redis.get_json.return_value = None

        response = client.get("/api/quality/test-coverage")

        assert response.status_code == 200
        data = response.json()
        assert "line_coverage_percent" in data
        assert "branch_coverage_percent" in data
        assert "function_coverage_percent" in data
        assert "statement_coverage_percent" in data
        assert "total_lines" in data
        assert "covered_lines" in data
        assert "total_branches" in data
        assert "covered_branches" in data
        assert "uncovered_files" in data
        assert "coverage_trend" in data
        assert 0 <= data["line_coverage_percent"] <= 100

    def test_get_enhanced_test_coverage(self, client, mock_redis):
        """测试增强测试覆盖率"""
        mock_redis.get_json.return_value = None

        response = client.get("/api/quality/test-coverage/enhanced")

        assert response.status_code == 200
        data = response.json()
        assert "line_coverage_percent" in data
        assert "branch_coverage_percent" in data
        assert "function_coverage_percent" in data
        assert "statement_coverage_percent" in data
        assert "mutation_score_percent" in data
        assert "coverage_by_module" in data
        assert "coverage_trend" in data
        assert "coverage_delta" in data
        assert "risk_areas" in data


@pytest.mark.api
@pytest.mark.integration
class TestQualityDashboard:
    """测试质量监控仪表板 API"""

    def test_get_quality_dashboard(self, client, mock_redis):
        """测试质量监控仪表板"""
        mock_redis.get_json.return_value = None

        response = client.get("/api/quality/dashboard")

        assert response.status_code == 200
        data = response.json()
        assert "overall_score" in data
        assert "performance" in data
        assert "errors" in data
        assert "code_quality" in data
        assert "test_coverage" in data
        assert "active_alerts" in data
        assert "last_updated" in data
        assert 0 <= data["overall_score"] <= 100


@pytest.mark.api
@pytest.mark.integration
class TestAlerts:
    """测试告警 API"""

    def test_get_active_alerts(self, client, mock_redis):
        """测试获取活跃告警"""
        mock_redis.get_json.return_value = None

        response = client.get("/api/quality/alerts")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_get_alert_rules(self, client):
        """测试获取告警规则"""
        response = client.get("/api/quality/alerts/rules")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        if len(data) > 0:
            rule = data[0]
            assert "rule_id" in rule
            assert "name" in rule
            assert "metric_type" in rule
            assert "condition" in rule
            assert "threshold" in rule
            assert "severity" in rule
            assert "enabled" in rule

    def test_create_alert_rule(self, client):
        """测试创建告警规则"""
        new_rule = {
            "rule_id": "test_rule_001",
            "name": "测试告警规则",
            "metric_type": "performance",
            "condition": "avg_response_time_ms > threshold",
            "threshold": 500.0,
            "severity": "warning",
            "enabled": True,
            "cooldown_minutes": 10
        }

        response = client.post("/api/quality/alerts/rules", json=new_rule)

        assert response.status_code == 200
        data = response.json()
        assert data["rule_id"] == new_rule["rule_id"]
        assert data["name"] == new_rule["name"]

    def test_trigger_quality_check(self, client):
        """测试触发质量检查"""
        response = client.post("/api/quality/check")

        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "timestamp" in data


@pytest.mark.api
@pytest.mark.integration
class TestMetricsTrend:
    """测试指标趋势 API"""

    def test_get_metrics_trend_performance(self, client, mock_redis):
        """测试性能指标趋势"""
        mock_redis.get_json.return_value = None

        response = client.get("/api/quality/metrics/trend?metric_type=performance&hours=24")

        assert response.status_code == 200
        data = response.json()
        assert "metric_type" in data
        assert "period_hours" in data
        assert "trend" in data
        assert data["metric_type"] == "performance"
        assert data["period_hours"] == 24

    def test_get_metrics_trend_error_rate(self, client, mock_redis):
        """测试错误率指标趋势"""
        mock_redis.get_json.return_value = None

        response = client.get("/api/quality/metrics/trend?metric_type=error_rate&hours=12")

        assert response.status_code == 200
        data = response.json()
        assert data["metric_type"] == "error_rate"
        assert data["period_hours"] == 12


@pytest.mark.api
@pytest.mark.integration
class TestQualityReport:
    """测试质量报告 API"""

    def test_generate_quality_report_daily(self, client, mock_redis):
        """测试生成日报"""
        mock_redis.get_json.return_value = None

        response = client.post("/api/quality/report/generate?report_type=daily")

        assert response.status_code == 200
        data = response.json()
        assert "report_id" in data
        assert "report_type" in data
        assert "generated_at" in data
        assert "period_start" in data
        assert "period_end" in data
        assert "overall_score" in data
        assert "metrics_summary" in data
        assert "trends" in data
        assert "issues_found" in data
        assert "recommendations" in data
        assert data["report_type"] == "daily"

    def test_generate_quality_report_weekly(self, client, mock_redis):
        """测试生成周报"""
        mock_redis.get_json.return_value = None

        response = client.post("/api/quality/report/generate?report_type=weekly")

        assert response.status_code == 200
        data = response.json()
        assert data["report_type"] == "weekly"


@pytest.mark.api
@pytest.mark.integration
class TestQualityBenchmark:
    """测试质量基准对比 API"""

    def test_get_quality_benchmark(self, client, mock_redis):
        """测试获取质量基准对比"""
        mock_redis.get_json.return_value = None

        response = client.get("/api/quality/benchmark")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        if len(data) > 0:
            benchmark = data[0]
            assert "benchmark_id" in benchmark
            assert "category" in benchmark
            assert "metric_name" in benchmark
            assert "current_value" in benchmark
            assert "benchmark_value" in benchmark
            assert "deviation" in benchmark
            assert "status" in benchmark

    def test_get_quality_benchmark_by_category(self, client, mock_redis):
        """测试按类别获取质量基准对比"""
        mock_redis.get_json.return_value = None

        response = client.get("/api/quality/benchmark?category=performance")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        for benchmark in data:
            assert benchmark["category"] == "performance"


@pytest.mark.api
@pytest.mark.integration
class TestQualityPrediction:
    """测试质量预测 API"""

    def test_predict_quality_performance(self, client, mock_redis):
        """测试性能预测"""
        mock_redis.get_json.return_value = None

        response = client.get("/api/quality/predict?metric_type=performance&prediction_horizon=24h")

        assert response.status_code == 200
        data = response.json()
        assert "prediction_id" in data
        assert "metric_type" in data
        assert "current_value" in data
        assert "predicted_value" in data
        assert "prediction_horizon" in data
        assert "confidence" in data
        assert "trend" in data
        assert "factors" in data
        assert "predicted_at" in data
        assert data["metric_type"] == "performance"
        assert data["prediction_horizon"] == "24h"
        assert 0 <= data["confidence"] <= 1

    def test_predict_quality_error_rate(self, client, mock_redis):
        """测试错误率预测"""
        mock_redis.get_json.return_value = None

        response = client.get("/api/quality/predict?metric_type=error_rate&prediction_horizon=7d")

        assert response.status_code == 200
        data = response.json()
        assert data["metric_type"] == "error_rate"
        assert data["prediction_horizon"] == "7d"


@pytest.mark.api
@pytest.mark.integration
class TestBulkAlertOperations:
    """测试批量告警操作 API"""

    def test_bulk_acknowledge_alerts(self, client):
        """测试批量确认告警"""
        alert_ids = ["alert_001", "alert_002"]

        response = client.post("/api/quality/alerts/bulk-acknowledge?alert_ids=alert_001&alert_ids=alert_002")

        assert response.status_code == 200
        data = response.json()
        assert "success" in data
        assert "acknowledged_count" in data
        assert "failed_ids" in data

    def test_bulk_resolve_alerts(self, client):
        """测试批量解决告警"""
        alert_ids = ["alert_001", "alert_002"]

        response = client.post("/api/quality/alerts/bulk-resolve?alert_ids=alert_001&alert_ids=alert_002")

        assert response.status_code == 200
        data = response.json()
        assert "success" in data
        assert "resolved_count" in data
        assert "failed_ids" in data


@pytest.mark.api
@pytest.mark.integration
class TestQualityMonitorIntegration:
    """测试质量监控集成"""

    def test_full_quality_monitoring_workflow(self, client, db_session, mock_redis):
        """测试完整的质量监控工作流"""
        mock_redis.get_json.return_value = None

        create_test_skill_call(db_session, skill_name="skill_1", status="completed")
        create_test_skill_call(db_session, skill_name="skill_2", status="failed",
                              error_message="TestError: Test error")

        perf_response = client.get("/api/quality/performance")
        assert perf_response.status_code == 200

        error_response = client.get("/api/quality/errors")
        assert error_response.status_code == 200

        quality_response = client.get("/api/quality/code-quality")
        assert quality_response.status_code == 200

        coverage_response = client.get("/api/quality/test-coverage")
        assert coverage_response.status_code == 200

        dashboard_response = client.get("/api/quality/dashboard")
        assert dashboard_response.status_code == 200
        dashboard_data = dashboard_response.json()
        assert "overall_score" in dashboard_data
        assert "performance" in dashboard_data
        assert "errors" in dashboard_data

    def test_quality_monitor_with_cache(self, client, mock_redis):
        """测试质量监控缓存机制"""
        cached_data = {
            "overall_score": 85.5,
            "performance": {
                "avg_response_time_ms": 150.0,
                "p95_response_time_ms": 200.0,
                "p99_response_time_ms": 250.0,
                "throughput_per_sec": 100.0,
                "error_rate_percent": 2.5,
                "slow_request_count": 5,
                "total_request_count": 1000,
                "active_connections": 10,
                "cpu_usage_percent": 45.0,
                "memory_usage_percent": 60.0
            },
            "errors": {
                "total_errors": 25,
                "error_rate": 2.5,
                "errors_by_type": {},
                "errors_by_endpoint": {},
                "recent_errors": [],
                "error_trend": []
            },
            "code_quality": {
                "overall_score": 78.5,
                "maintainability_index": 82.3,
                "cyclomatic_complexity": 12.5,
                "code_duplication_percent": 8.2,
                "technical_debt_hours": 24.5,
                "code_smell_count": 15,
                "security_issues": 3,
                "code_coverage_percent": 85.2,
                "documentation_coverage_percent": 72.5
            },
            "test_coverage": {
                "line_coverage_percent": 85.2,
                "branch_coverage_percent": 75.0,
                "function_coverage_percent": 80.0,
                "statement_coverage_percent": 85.0,
                "total_lines": 10000,
                "covered_lines": 8520,
                "total_branches": 2500,
                "covered_branches": 1875,
                "uncovered_files": [],
                "coverage_trend": []
            },
            "active_alerts": [],
            "last_updated": datetime.now().isoformat()
        }
        mock_redis.get_json.return_value = cached_data

        response = client.get("/api/quality/dashboard")

        assert response.status_code == 200
        data = response.json()
        assert "overall_score" in data
        assert 0 <= data["overall_score"] <= 100
