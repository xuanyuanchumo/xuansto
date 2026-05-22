from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from typing import List, Dict, Any, Optional, Set
from enum import Enum
from datetime import datetime
import json
import asyncio
import time
import random

router = APIRouter()

DEFAULT_PUSH_INTERVAL = 5
HEARTBEAT_INTERVAL = 30
HEARTBEAT_TIMEOUT = 60


class QualityMetricType(str, Enum):
    CODE_COVERAGE = "code_coverage"
    COMPLEXITY = "complexity"
    TECHNICAL_DEBT = "technical_debt"
    TEST_PASS_RATE = "test_pass_rate"
    BUILD_STATUS = "build_status"
    SECURITY_SCAN = "security_scan"


class MessageType(str, Enum):
    PING = "ping"
    PONG = "pong"
    SUBSCRIBE = "subscribe"
    UNSUBSCRIBE = "unsubscribe"
    METRICS_UPDATE = "metrics_update"
    HEARTBEAT = "heartbeat"
    ERROR = "error"


class RealtimeQualityManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.connection_subscriptions: Dict[WebSocket, Set[str]] = {}
        self.connection_heartbeats: Dict[WebSocket, float] = {}
        self._heartbeat_task: Optional[asyncio.Task] = None
        self._push_tasks: Dict[WebSocket, asyncio.Task] = {}

    async def start_heartbeat_monitor(self):
        if self._heartbeat_task is None or self._heartbeat_task.done():
            self._heartbeat_task = asyncio.create_task(self._heartbeat_monitor_loop())

    async def _heartbeat_monitor_loop(self):
        while True:
            try:
                await asyncio.sleep(HEARTBEAT_INTERVAL)
                await self._check_heartbeats()
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"Heartbeat monitor error: {e}")

    async def _check_heartbeats(self):
        current_time = time.time()
        disconnected = []

        for websocket in list(self.active_connections):
            last_heartbeat = self.connection_heartbeats.get(websocket, current_time)
            if current_time - last_heartbeat > HEARTBEAT_TIMEOUT:
                disconnected.append(websocket)

        for ws in disconnected:
            try:
                await ws.close()
            except Exception:
                pass
            self.disconnect(ws)

    def update_heartbeat(self, websocket: WebSocket):
        self.connection_heartbeats[websocket] = time.time()

    async def connect(self, websocket: WebSocket, subscriptions: Optional[List[str]] = None):
        await websocket.accept()
        self.active_connections.append(websocket)
        self.connection_heartbeats[websocket] = time.time()
        self.connection_subscriptions[websocket] = set(subscriptions) if subscriptions else set(
            mt.value for mt in QualityMetricType)
        await self.start_heartbeat_monitor()

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        if websocket in self.connection_heartbeats:
            del self.connection_heartbeats[websocket]
        if websocket in self.connection_subscriptions:
            del self.connection_subscriptions[websocket]
        if websocket in self._push_tasks:
            self._push_tasks[websocket].cancel()
            del self._push_tasks[websocket]

    async def subscribe(self, websocket: WebSocket, metric_types: List[str]):
        if websocket in self.connection_subscriptions:
            self.connection_subscriptions[websocket].update(metric_types)

    async def unsubscribe(self, websocket: WebSocket, metric_types: List[str]):
        if websocket in self.connection_subscriptions:
            self.connection_subscriptions[websocket].difference_update(metric_types)

    def _generate_coverage_data(self) -> Dict[str, Any]:
        return {
            "metric_type": QualityMetricType.CODE_COVERAGE.value,
            "timestamp": datetime.now().isoformat(),
            "data": {
                "line_coverage": round(85.2 + random.uniform(-2, 2), 2),
                "branch_coverage": round(75.0 + random.uniform(-3, 3), 2),
                "function_coverage": round(81.0 + random.uniform(-2.5, 2.5), 2),
                "total_lines": 10000,
                "covered_lines": 8520
            }
        }

    def _generate_complexity_data(self) -> Dict[str, Any]:
        return {
            "metric_type": QualityMetricType.COMPLEXITY.value,
            "timestamp": datetime.now().isoformat(),
            "data": {
                "cyclomatic_complexity": round(12.5 + random.uniform(-1, 1), 2),
                "cognitive_complexity": round(15.8 + random.uniform(-2, 2), 2),
                "trend": ["stable", "improving", "declining"][random.randint(0, 2)],
                "avg_per_function": round(8.3 + random.uniform(-0.5, 0.5), 2)
            }
        }

    def _generate_technical_debt_data(self) -> Dict[str, Any]:
        return {
            "metric_type": QualityMetricType.TECHNICAL_DEBT.value,
            "timestamp": datetime.now().isoformat(),
            "data": {
                "score": round(24.5 + random.uniform(-2, 2), 2),
                "hours": round(145 + random.uniform(-10, 10), 0),
                "trend": "stable",
                "categories": {
                    "code_duplication": round(8.2 + random.uniform(-1, 1), 1),
                    "complexity": round(6.5 + random.uniform(-0.5, 0.5), 1),
                    "documentation": round(5.8 + random.uniform(-0.8, 0.8), 1)
                }
            }
        }

    def _generate_test_pass_rate_data(self) -> Dict[str, Any]:
        pass_rate = round(94.5 + random.uniform(-3, 3), 2)
        return {
            "metric_type": QualityMetricType.TEST_PASS_RATE.value,
            "timestamp": datetime.now().isoformat(),
            "data": {
                "pass_rate": pass_rate,
                "total_tests": 1250,
                "passed_tests": int(1250 * pass_rate / 100),
                "failed_tests": int(1250 * (100 - pass_rate) / 100),
                "skipped_tests": random.randint(5, 15)
            }
        }

    def _generate_build_status_data(self) -> Dict[str, Any]:
        statuses = ["success", "failed", "running", "pending"]
        weights = [0.85, 0.05, 0.07, 0.03]
        status = random.choices(statuses, weights=weights)[0]
        return {
            "metric_type": QualityMetricType.BUILD_STATUS.value,
            "timestamp": datetime.now().isoformat(),
            "data": {
                "status": status,
                "build_number": f"build_{int(time.time())}",
                "duration_seconds": round(random.uniform(120, 300), 0) if status == "success" else None,
                "trigger": "automatic"
            }
        }

    def _generate_security_scan_data(self) -> Dict[str, Any]:
        return {
            "metric_type": QualityMetricType.SECURITY_SCAN.value,
            "timestamp": datetime.now().isoformat(),
            "data": {
                "critical_count": random.randint(0, 2),
                "high_count": random.randint(1, 4),
                "medium_count": random.randint(3, 8),
                "low_count": random.randint(5, 12),
                "score": round(88.0 + random.uniform(-5, 5), 1),
                "last_scan": (datetime.now() - timedelta(hours=random.randint(1, 24))).isoformat() if 'timedelta' in dir() else (
                            datetime.now() - __import__('datetime').timedelta(
                        hours=random.randint(1, 24))).isoformat()
            }
        }

    def _get_metric_generator(self, metric_type: str):
        generators = {
            QualityMetricType.CODE_COVERAGE.value: self._generate_coverage_data,
            QualityMetricType.COMPLEXITY.value: self._generate_complexity_data,
            QualityMetricType.TECHNICAL_DEBT.value: self._generate_technical_debt_data,
            QualityMetricType.TEST_PASS_RATE.value: self._generate_test_pass_rate_data,
            QualityMetricType.BUILD_STATUS.value: self._generate_build_status_data,
            QualityMetricType.SECURITY_SCAN.value: self._generate_security_scan_data,
        }
        return generators.get(metric_type)

    async def _push_metrics_loop(self, websocket: WebSocket, interval: int = DEFAULT_PUSH_INTERVAL):
        try:
            while True:
                await asyncio.sleep(interval)

                if websocket not in self.active_connections:
                    break

                subscriptions = self.connection_subscriptions.get(websocket, set())
                metrics_data = []

                for metric_type in subscriptions:
                    generator = self._get_metric_generator(metric_type)
                    if generator:
                        metrics_data.append(generator())

                if metrics_data:
                    message = {
                        "type": MessageType.METRICS_UPDATE.value,
                        "timestamp": datetime.now().isoformat(),
                        "metrics": metrics_data
                    }
                    try:
                        await websocket.send_json(message)
                    except Exception:
                        break
        except asyncio.CancelledError:
            pass
        except Exception as e:
            print(f"Push metrics loop error: {e}")

    async def start_pushing(self, websocket: WebSocket, interval: int = DEFAULT_PUSH_INTERVAL):
        if websocket in self._push_tasks:
            self._push_tasks[websocket].cancel()

        self._push_tasks[websocket] = asyncio.create_task(
            self._push_metrics_loop(websocket, interval)
        )


manager = RealtimeQualityManager()


@router.websocket("/quality/realtime")
async def realtime_quality_websocket(
        websocket: WebSocket,
        metrics: Optional[str] = Query(None, description="订阅的指标类型，逗号分隔"),
        interval: int = Query(DEFAULT_PUSH_INTERVAL, description="推送间隔（秒）", ge=1, le=60)):
    subscription_list = None
    if metrics:
        subscription_list = [m.strip() for m in metrics.split(",")]
        valid_types = {mt.value for mt in QualityMetricType}
        subscription_list = [m for m in subscription_list if m in valid_types]

    await manager.connect(websocket, subscription_list)
    await manager.start_pushing(websocket, interval)

    try:
        while True:
            data = await websocket.receive_text()
            try:
                message = json.loads(data)

                if message.get("type") == MessageType.PING.value:
                    manager.update_heartbeat(websocket)
                    await websocket.send_json({
                        "type": MessageType.PONG.value,
                        "timestamp": time.time()
                    })

                elif message.get("type") == MessageType.HEARTBEAT.value:
                    manager.update_heartbeat(websocket)
                    await websocket.send_json({
                        "type": MessageType.HEARTBEAT.value,
                        "timestamp": time.time()
                    })

                elif message.get("type") == MessageType.SUBSCRIBE.value:
                    metric_types = message.get("metrics", [])
                    if isinstance(metric_types, list):
                        await manager.subscribe(websocket, metric_types)
                    await websocket.send_json({
                        "type": "subscription_updated",
                        "subscribed": metric_types,
                        "timestamp": datetime.now().isoformat()
                    })

                elif message.get("type") == MessageType.UNSUBSCRIBE.value:
                    metric_types = message.get("metrics", [])
                    if isinstance(metric_types, list):
                        await manager.unsubscribe(websocket, metric_types)
                    await websocket.send_json({
                        "type": "subscription_updated",
                        "unsubscribed": metric_types,
                        "timestamp": datetime.now().isoformat()
                    })

                else:
                    await websocket.send_json({
                        "type": MessageType.ERROR.value,
                        "message": f"Unknown message type: {message.get('type')}"
                    })

            except json.JSONDecodeError:
                await websocket.send_json({
                    "type": MessageType.ERROR.value,
                    "message": "Invalid JSON format"
                })

    except WebSocketDisconnect:
        manager.disconnect(websocket)


def get_realtime_quality_manager() -> RealtimeQualityManager:
    return manager
