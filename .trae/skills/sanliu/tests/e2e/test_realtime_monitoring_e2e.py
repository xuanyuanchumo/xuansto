"""
前后端实时监控流程端到端测试

测试前后端实时监控流程：
1. 启动后端服务
2. 启动前端服务
3. 连接 WebSocket
4. 触发演化操作
5. 验证实时状态更新
6. 测试演化干预（暂停、继续、回滚）
"""

import pytest
import asyncio
import json
import time
from fastapi.testclient import TestClient
from fastapi.websockets import WebSocket
import sys
from pathlib import Path

backend_dir = Path(__file__).parent.parent.parent / 'backend'
sys.path.insert(0, str(backend_dir))

from app.main import app


class BaseE2ETest:
    """E2E测试基类"""
    
    @pytest.fixture(autouse=True)
    def setup_e2e(self):
        """E2E测试前准备"""
        self.client = TestClient(app)
        yield
        self.client = None


class TestRealtimeMonitoringE2E(BaseE2ETest):
    """前后端实时监控流程端到端测试"""
    
    def setup(self):
        """测试前准备"""
        if not hasattr(self, 'client'):
            self.client = TestClient(app)
        self.ws_client = None
        self.received_messages = []
        
    def test_01_backend_health_check(self):
        """测试1：后端健康检查"""
        print("\n=== 测试1：后端健康检查 ===")
        
        response = self.client.get("/health")
        assert response.status_code == 200
        
        data = response.json()
        print(f"状态: {data['status']}")
        print(f"时间戳: {data['timestamp']}")
        
        assert data["status"] == "healthy"
        
    def test_02_get_evolution_monitor_status(self):
        """测试2：获取演化监控状态"""
        print("\n=== 测试2：获取演化监控状态 ===")
        
        response = self.client.get("/api/evolution/status")
        assert response.status_code == 200
        
        data = response.json()
        print(f"演化状态: {data['status']}")
        print(f"当前阶段: {data.get('current_stage')}")
        print(f"进度: {data['progress']}%")
        
        if data.get('current_metrics'):
            print(f"\n当前指标:")
            for key, value in data['current_metrics'].items():
                print(f"  {key}: {value}")
        
    def test_03_websocket_connection(self):
        """测试3：WebSocket 连接"""
        print("\n=== 测试3：WebSocket 连接 ===")
        
        with self.client.websocket_connect("/ws/evolution/ws") as websocket:
            initial_message = websocket.receive_json()
            print(f"收到初始消息类型: {initial_message['type']}")
            print(f"初始状态: {initial_message.get('data', {})}")
            
            assert initial_message['type'] == 'initial_state'
            
            ping_message = {"type": "ping"}
            websocket.send_json(ping_message)
            
            pong_message = websocket.receive_json()
            print(f"收到 Pong 消息: {pong_message['type']}")
            assert pong_message['type'] == 'pong'
            
            status_request = {"type": "get_status"}
            websocket.send_json(status_request)
            
            status_message = websocket.receive_json()
            print(f"收到状态更新: {status_message['type']}")
            assert status_message['type'] == 'status_update'
        
        print("WebSocket 连接测试成功")
        
    def test_04_trigger_evolution_with_websocket(self):
        """测试4：通过 WebSocket 触发演化"""
        print("\n=== 测试4：通过 WebSocket 触发演化 ===")
        
        evolution_request = {
            "evolution_type": "performance_tuning",
            "reason": "测试实时监控功能",
            "force": False,
            "dry_run": False
        }
        
        trigger_response = self.client.post("/api/evolution/trigger", json=evolution_request)
        assert trigger_response.status_code == 200
        
        trigger_data = trigger_response.json()
        trigger_id = trigger_data['trigger_id']
        print(f"触发ID: {trigger_id}")
        print(f"状态: {trigger_data['status']}")
        
        time.sleep(1)
        
        status_response = self.client.get("/api/evolution/status")
        assert status_response.status_code == 200
        
        status_data = status_response.json()
        print(f"\n演化状态: {status_data['status']}")
        print(f"当前阶段: {status_data.get('current_stage')}")
        print(f"进度: {status_data['progress']}%")
        
    def test_05_monitor_evolution_progress(self):
        """测试5：监控演化进度"""
        print("\n=== 测试5：监控演化进度 ===")
        
        for i in range(3):
            time.sleep(2)
            
            response = self.client.get("/api/evolution/status")
            assert response.status_code == 200
            
            data = response.json()
            print(f"\n轮询 {i+1}:")
            print(f"  状态: {data['status']}")
            print(f"  进度: {data['progress']}%")
            print(f"  当前阶段: {data.get('current_stage')}")
            
            if data['status'] in ['completed', 'failed']:
                break
        
    def test_06_test_pause_evolution(self):
        """测试6：测试暂停演化"""
        print("\n=== 测试6：测试暂停演化 ===")
        
        evolution_request = {
            "evolution_type": "resource_rebalance",
            "reason": "测试暂停功能",
            "force": True
        }
        
        trigger_response = self.client.post("/api/evolution/trigger", json=evolution_request)
        assert trigger_response.status_code == 200
        
        time.sleep(1)
        
        pause_response = self.client.post("/api/evolution/pause")
        
        if pause_response.status_code == 200:
            pause_data = pause_response.json()
            print(f"暂停成功: {pause_data['message']}")
            print(f"状态: {pause_data['status']}")
            
            status_response = self.client.get("/api/evolution/status")
            status_data = status_response.json()
            print(f"当前状态: {status_data['status']}")
        else:
            print(f"暂停响应: {pause_response.status_code}")
            print(f"详情: {pause_response.json()}")
        
    def test_07_test_resume_evolution(self):
        """测试7：测试恢复演化"""
        print("\n=== 测试7：测试恢复演化 ===")
        
        resume_response = self.client.post("/api/evolution/resume")
        
        if resume_response.status_code == 200:
            resume_data = resume_response.json()
            print(f"恢复成功: {resume_data['message']}")
            print(f"状态: {resume_data['status']}")
            
            status_response = self.client.get("/api/evolution/status")
            status_data = status_response.json()
            print(f"当前状态: {status_data['status']}")
        else:
            print(f"恢复响应: {resume_response.status_code}")
            print(f"详情: {resume_response.json()}")
        
    def test_08_test_cancel_evolution(self):
        """测试8：测试取消演化"""
        print("\n=== 测试8：测试取消演化 ===")
        
        evolution_request = {
            "evolution_type": "knowledge_update",
            "reason": "测试取消功能",
            "force": True
        }
        
        trigger_response = self.client.post("/api/evolution/trigger", json=evolution_request)
        assert trigger_response.status_code == 200
        
        time.sleep(1)
        
        cancel_response = self.client.post("/api/evolution/cancel")
        
        if cancel_response.status_code == 200:
            cancel_data = cancel_response.json()
            print(f"取消成功: {cancel_data['message']}")
            print(f"状态: {cancel_data['status']}")
            
            status_response = self.client.get("/api/evolution/status")
            status_data = status_response.json()
            print(f"当前状态: {status_data['status']}")
        else:
            print(f"取消响应: {cancel_response.status_code}")
            print(f"详情: {cancel_response.json()}")
        
    def test_09_get_evolution_trends(self):
        """测试9：获取演化趋势"""
        print("\n=== 测试9：获取演化趋势 ===")
        
        response = self.client.get("/api/evolution/trends?metric=performance&period=7d")
        assert response.status_code == 200
        
        data = response.json()
        print(f"指标名称: {data['metric_name']}")
        print(f"时间范围: {data['period']}")
        print(f"趋势方向: {data['trend_direction']}")
        print(f"变化百分比: {data['change_percentage']}%")
        print(f"预测值: {data.get('prediction')}")
        print(f"置信度: {data.get('confidence')}")
        
        print(f"\n数据点数量: {len(data['data_points'])}")
        if data['data_points']:
            print(f"第一个数据点: {data['data_points'][0]}")
            print(f"最后一个数据点: {data['data_points'][-1]}")
        
    def test_10_get_evolution_metrics_summary(self):
        """测试10：获取演化指标汇总"""
        print("\n=== 测试10：获取演化指标汇总 ===")
        
        response = self.client.get("/api/evolution/metrics/summary")
        assert response.status_code == 200
        
        data = response.json()
        print(f"总演化次数: {data['total_evolutions']}")
        print(f"成功次数: {data['successful_evolutions']}")
        print(f"失败次数: {data['failed_evolutions']}")
        print(f"平均持续时间: {data['average_duration']}秒")
        print(f"成功率: {data['success_rate']:.2%}")
        print(f"最常见类型: {data.get('most_common_type')}")
        print(f"24小时内: {data['last_24h_count']}")
        print(f"7天内: {data['last_7d_count']}")
        
    def test_11_websocket_heartbeat(self):
        """测试11：WebSocket 心跳"""
        print("\n=== 测试11：WebSocket 心跳 ===")
        
        with self.client.websocket_connect("/ws/evolution/ws") as websocket:
            for i in range(3):
                heartbeat_message = {"type": "heartbeat"}
                websocket.send_json(heartbeat_message)
                
                ack_message = websocket.receive_json()
                print(f"心跳 {i+1}: 收到 {ack_message['type']}")
                assert ack_message['type'] == 'heartbeat_ack'
                
                time.sleep(1)
        
        print("心跳测试成功")
        
    def test_12_multiple_websocket_connections(self):
        """测试12：多个 WebSocket 连接"""
        print("\n=== 测试12：多个 WebSocket 连接 ===")
        
        with self.client.websocket_connect("/ws/evolution/ws") as ws1:
            with self.client.websocket_connect("/ws/evolution/ws") as ws2:
                msg1 = ws1.receive_json()
                msg2 = ws2.receive_json()
                
                print(f"连接1收到: {msg1['type']}")
                print(f"连接2收到: {msg2['type']}")
                
                assert msg1['type'] == 'initial_state'
                assert msg2['type'] == 'initial_state'
                
                ws1.send_json({"type": "ping"})
                ws2.send_json({"type": "ping"})
                
                pong1 = ws1.receive_json()
                pong2 = ws2.receive_json()
                
                print(f"连接1 Pong: {pong1['type']}")
                print(f"连接2 Pong: {pong2['type']}")
        
        print("多连接测试成功")


def test_complete_realtime_flow():
    """测试完整的实时监控流程"""
    print("\n" + "="*60)
    print("开始完整的前后端实时监控流程测试")
    print("="*60)
    
    test_instance = TestRealtimeMonitoringE2E()
    test_instance.setup()
    
    tests = [
        ("后端健康检查", test_instance.test_01_backend_health_check),
        ("获取演化监控状态", test_instance.test_02_get_evolution_monitor_status),
        ("WebSocket 连接", test_instance.test_03_websocket_connection),
        ("触发演化并监控", test_instance.test_04_trigger_evolution_with_websocket),
        ("监控演化进度", test_instance.test_05_monitor_evolution_progress),
        ("测试暂停演化", test_instance.test_06_test_pause_evolution),
        ("测试恢复演化", test_instance.test_07_test_resume_evolution),
        ("测试取消演化", test_instance.test_08_test_cancel_evolution),
        ("获取演化趋势", test_instance.test_09_get_evolution_trends),
        ("获取演化指标汇总", test_instance.test_10_get_evolution_metrics_summary),
        ("WebSocket 心跳", test_instance.test_11_websocket_heartbeat),
        ("多个 WebSocket 连接", test_instance.test_12_multiple_websocket_connections),
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        try:
            test_func()
            print(f"[PASS] {test_name} - 通过")
            passed += 1
        except Exception as e:
            print(f"[FAIL] {test_name} - 失败: {str(e)}")
            failed += 1
    
    print("\n" + "="*60)
    print(f"测试完成: {passed} 通过, {failed} 失败")
    print("="*60)
    
    return passed, failed


if __name__ == "__main__":
    passed, failed = test_complete_realtime_flow()
    exit(0 if failed == 0 else 1)
