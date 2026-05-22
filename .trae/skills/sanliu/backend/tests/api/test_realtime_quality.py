"""
Realtime Quality WebSocket API 测试

测试实时质量监控的 WebSocket 端点
"""

import pytest
from datetime import datetime
import json
import asyncio


@pytest.mark.api
@pytest.mark.websocket
class TestRealtimeQualityWebSocket:
    """测试实时质量监控 WebSocket 端点"""

    def test_websocket_connection(self, client):
        """测试 WebSocket 连接建立"""
        with client.websocket_connect("/api/quality/realtime") as websocket:
            data = websocket.receive_json()
            assert data is not None

    def test_websocket_ping_pong(self, client):
        """测试心跳机制"""
        with client.websocket_connect("/api/quality/realtime") as websocket:
            websocket.send_json({"type": "ping"})
            response = websocket.receive_json(timeout=5)
            assert response["type"] == "pong"
            assert "timestamp" in response

    def test_websocket_heartbeat(self, client):
        """测试心跳检测"""
        with client.websocket_connect("/api/quality/realtime") as websocket:
            websocket.send_json({"type": "heartbeat"})
            response = websocket.receive_json(timeout=5)
            assert response["type"] == "heartbeat"
            assert "timestamp" in response

    def test_websocket_subscribe_metrics(self, client):
        """测试订阅特定指标类型"""
        with client.websocket_connect(
                "/api/quality/realtime?metrics=code_coverage,test_pass_rate"
        ) as websocket:
            websocket.send_json({
                "type": "subscribe",
                "metrics": ["code_coverage", "test_pass_rate"]
            })
            response = websocket.receive_json(timeout=5)
            assert response["type"] == "subscription_updated"
            assert "subscribed" in response

    def test_websocket_unsubscribe_metrics(self, client):
        """测试取消订阅指标类型"""
        with client.websocket_connect("/api/quality/realtime") as websocket:
            websocket.send_json({
                "type": "unsubscribe",
                "metrics": ["code_coverage"]
            })
            response = websocket.receive_json(timeout=5)
            assert response["type"] == "subscription_updated"
            assert "unsubscribed" in response

    def test_websocket_receive_metrics_update(self, client):
        """测试接收指标更新数据"""
        with client.websocket_connect(
                "/api/quality/realtime?interval=2"
        ) as websocket:
            data = websocket.receive_json(timeout=10)
            assert data["type"] == "metrics_update"
            assert "timestamp" in data
            assert "metrics" in data
            assert len(data["metrics"]) > 0

            for metric in data["metrics"]:
                assert "metric_type" in metric
                assert "data" in metric
                assert "timestamp" in metric

    def test_websocket_custom_interval(self, client):
        """测试自定义推送间隔"""
        with client.websocket_connect(
                "/api/quality/realtime?interval=3"
        ) as websocket:
            start_time = datetime.now()
            websocket.receive_json(timeout=10)
            first_interval = (datetime.now() - start_time).total_seconds()

            assert 1 <= first_interval <= 6

    def test_websocket_invalid_json(self, client):
        """测试发送无效 JSON 的处理"""
        with client.websocket_connect("/api/quality/realtime") as websocket:
            websocket.send_text("invalid json")
            response = websocket.receive_json(timeout=5)
            assert response["type"] == "error"

    def test_websocket_unknown_message_type(self, client):
        """测试未知消息类型的处理"""
        with client.websocket_connect("/api/quality/realtime") as websocket:
            websocket.send_json({"type": "unknown_type"})
            response = websocket.receive_json(timeout=5)
            assert response["type"] == "error"

    def test_websocket_default_subscriptions(self, client):
        """测试默认订阅所有指标类型"""
        with client.websocket_connect("/api/quality/realtime") as websocket:
            data = websocket.receive_json(timeout=10)
            metric_types = set(m["metric_type"] for m in data["metrics"])

            expected_types = {
                "code_coverage",
                "complexity",
                "technical_debt",
                "test_pass_rate",
                "build_status",
                "security_scan"
            }

            assert expected_types.issubset(metric_types)

    def test_websocket_code_coverage_data_structure(self, client):
        """测试代码覆盖率数据结构"""
        with client.websocket_connect(
                "/api/quality/realtime?metrics=code_coverage&interval=3"
        ) as websocket:
            data = websocket.receive_json(timeout=10)

            coverage_metric = next(
                (m for m in data["metrics"] if m["metric_type"] == "code_coverage"),
                None
            )
            assert coverage_metric is not None

            coverage_data = coverage_metric["data"]
            assert "line_coverage" in coverage_data
            assert "branch_coverage" in coverage_data
            assert "function_coverage" in coverage_data
            assert "total_lines" in coverage_data
            assert "covered_lines" in coverage_data

    def test_websocket_security_scan_data_structure(self, client):
        """测试安全扫描数据结构"""
        with client.websocket_connect(
                "/api/quality/realtime?metrics=security_scan&interval=3"
        ) as websocket:
            data = websocket.receive_json(timeout=10)

            security_metric = next(
                (m for m in data["metrics"] if m["metric_type"] == "security_scan"),
                None
            )
            assert security_metric is not None

            security_data = security_metric["data"]
            assert "critical_count" in security_data
            assert "high_count" in security_data
            assert "medium_count" in security_data
            assert "low_count" in security_data
            assert "score" in security_data
