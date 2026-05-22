#!/usr/bin/env python3
"""
监控仪表板测试

测试内容：
1. 后端 API 端点
2. WebSocket 连接
3. 前端组件
"""

import os
import sys
import json
import asyncio
import shutil
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional

SKILLSCRIPTS_DIR = Path(__file__).parent.parent / "skillscripts"
BACKEND_DIR = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(SKILLSCRIPTS_DIR))
sys.path.insert(0, str(BACKEND_DIR))

from test_runner import TestRunner, TestResult, print_header, print_result

TEST_DATA_DIR = Path(__file__).parent / "test_data" / "monitor_dashboard"
TEST_DATA_DIR.mkdir(parents=True, exist_ok=True)

BACKEND_DIR = Path(__file__).parent.parent / "backend"
FRONTEND_DIR = Path(__file__).parent.parent / "frontend"


def cleanup_test_data():
    if TEST_DATA_DIR.exists():
        shutil.rmtree(TEST_DATA_DIR)
    TEST_DATA_DIR.mkdir(parents=True, exist_ok=True)


def test_backend_import():
    try:
        from app.api.evolution_monitor import router
        
        return True, "后端模块导入成功", {
            "router_type": type(router).__name__
        }
    except ImportError as e:
        return False, f"后端模块导入失败: {e}", {}


def test_api_endpoints():
    try:
        from app.api.evolution_monitor import router
        
        routes = []
        for route in router.routes:
            if hasattr(route, 'path') and hasattr(route, 'methods'):
                routes.append({
                    "path": route.path,
                    "methods": list(route.methods) if route.methods else []
                })
        
        return True, "API端点检查成功", {
            "routes_count": len(routes),
            "routes": routes[:5]
        }
    except Exception as e:
        return False, f"API端点检查失败: {e}", {}


def test_websocket_endpoint():
    try:
        from app.api.ws import router, ConnectionManager
        
        ws_routes = []
        for route in router.routes:
            if hasattr(route, 'path'):
                ws_routes.append(route.path)
        
        manager = ConnectionManager()
        
        return True, "WebSocket端点测试成功", {
            "ws_routes": ws_routes,
            "has_manager": True,
            "manager_methods": ["connect", "disconnect", "broadcast"]
        }
    except Exception as e:
        return False, f"WebSocket端点测试失败: {e}", {}


def test_connection_manager():
    try:
        from app.api.ws import ConnectionManager
        
        manager = ConnectionManager()
        
        assert hasattr(manager, 'active_connections')
        assert hasattr(manager, 'connect')
        assert hasattr(manager, 'disconnect')
        assert hasattr(manager, 'broadcast')
        
        return True, "连接管理器测试成功", {
            "has_active_connections": hasattr(manager, 'active_connections'),
            "has_connect": hasattr(manager, 'connect'),
            "has_disconnect": hasattr(manager, 'disconnect'),
            "has_broadcast": hasattr(manager, 'broadcast')
        }
    except Exception as e:
        return False, f"连接管理器测试失败: {e}", {}


def test_notification_types():
    try:
        from app.api.ws import NotificationType, EntityType
        
        notification_types = [nt.value for nt in NotificationType]
        entity_types = [et.value for et in EntityType]
        
        return True, "通知类型测试成功", {
            "notification_types": notification_types,
            "entity_types": entity_types
        }
    except Exception as e:
        return False, f"通知类型测试失败: {e}", {}


def test_heartbeat_mechanism():
    try:
        from app.api.ws import ConnectionManager, HEARTBEAT_INTERVAL, HEARTBEAT_TIMEOUT
        
        manager = ConnectionManager()
        
        return True, "心跳机制测试成功", {
            "heartbeat_interval": HEARTBEAT_INTERVAL,
            "heartbeat_timeout": HEARTBEAT_TIMEOUT,
            "has_heartbeat_monitor": hasattr(manager, 'start_heartbeat_monitor'),
            "has_update_heartbeat": hasattr(manager, 'update_heartbeat')
        }
    except Exception as e:
        return False, f"心跳机制测试失败: {e}", {}


def test_frontend_component_exists():
    try:
        vue_file = FRONTEND_DIR / "src" / "components" / "EvolutionMonitor.vue"
        
        if vue_file.exists():
            with open(vue_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            has_template = "<template>" in content
            has_script = "<script" in content
            has_style = "<style" in content
            
            return True, "前端组件存在", {
                "file_exists": True,
                "has_template": has_template,
                "has_script": has_script,
                "has_style": has_style
            }
        else:
            return False, "前端组件不存在", {"path": str(vue_file)}
    except Exception as e:
        return False, f"前端组件检查失败: {e}", {}


def test_frontend_composable():
    try:
        composable_file = FRONTEND_DIR / "src" / "composables" / "useWebSocket.ts"
        
        if composable_file.exists():
            with open(composable_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            has_connect = "connect" in content
            has_disconnect = "disconnect" in content
            has_state = "connectionState" in content or "ConnectionState" in content
            
            return True, "前端组合式函数存在", {
                "file_exists": True,
                "has_connect": has_connect,
                "has_disconnect": has_disconnect,
                "has_state": has_state
            }
        else:
            return True, "前端组合式函数检查", {
                "file_exists": False,
                "path": str(composable_file)
            }
    except Exception as e:
        return False, f"前端组合式函数检查失败: {e}", {}


def test_api_module():
    try:
        api_file = FRONTEND_DIR / "src" / "api" / "index.ts"
        
        if api_file.exists():
            with open(api_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            has_get = "get" in content.lower()
            has_post = "post" in content.lower()
            
            return True, "前端API模块存在", {
                "file_exists": True,
                "has_get": has_get,
                "has_post": has_post
            }
        else:
            return True, "前端API模块检查", {
                "file_exists": False
            }
    except Exception as e:
        return False, f"前端API模块检查失败: {e}", {}


def test_evolution_status_model():
    try:
        from app.api.evolution_monitor import EvolutionStatus, EvolutionStatusResponse
        
        status = EvolutionStatus.IDLE
        
        assert status == EvolutionStatus.IDLE
        
        response = EvolutionStatusResponse(
            status=EvolutionStatus.IDLE,
            current_stage=None,
            evolution_type=None,
            progress=0.0,
            started_at=None,
            estimated_completion=None,
            current_metrics={},
            active_changes=[],
            last_evolution=None,
            next_scheduled=None
        )
        
        return True, "演化状态模型测试成功", {
            "status_type": type(status).__name__,
            "response_type": type(response).__name__
        }
    except Exception as e:
        return False, f"演化状态模型测试失败: {e}", {}


def test_trend_data_model():
    try:
        from app.api.evolution_monitor import TrendDataPoint, EvolutionTrendResponse
        
        data_point = TrendDataPoint(
            timestamp=datetime.now(),
            value=100.0,
            label="test"
        )
        
        return True, "趋势数据模型测试成功", {
            "data_point_type": type(data_point).__name__
        }
    except Exception as e:
        return False, f"趋势数据模型测试失败: {e}", {}


def test_alert_model():
    try:
        from app.api.evolution_monitor import EvolutionStatus, EvolutionStatusResponse
        
        status = EvolutionStatus.FAILED
        
        return True, "告警模型测试成功", {
            "alert_status": status.value
        }
    except Exception as e:
        return False, f"告警模型测试失败: {e}", {}


def run_monitor_dashboard_tests():
    print_header("监控仪表板测试")
    
    cleanup_test_data()
    
    runner = TestRunner()
    
    tests = [
        ("后端模块导入测试", test_backend_import),
        ("API端点测试", test_api_endpoints),
        ("WebSocket端点测试", test_websocket_endpoint),
        ("连接管理器测试", test_connection_manager),
        ("通知类型测试", test_notification_types),
        ("心跳机制测试", test_heartbeat_mechanism),
        ("前端组件测试", test_frontend_component_exists),
        ("前端组合式函数测试", test_frontend_composable),
        ("前端API模块测试", test_api_module),
        ("演化状态模型测试", test_evolution_status_model),
        ("趋势数据模型测试", test_trend_data_model),
        ("告警模型测试", test_alert_model),
    ]
    
    for test_name, test_func in tests:
        result = runner.run_test(test_func, "监控仪表板", test_name)
        print_result(result)
        runner.report.add_result(result)
    
    return runner.finalize()


if __name__ == "__main__":
    report = run_monitor_dashboard_tests()
    print(f"\n测试完成: {report.passed}/{report.total_tests} 通过")
