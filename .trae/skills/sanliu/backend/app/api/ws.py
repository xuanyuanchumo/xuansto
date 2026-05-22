from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import List, Dict, Any, Optional
from enum import Enum
from datetime import datetime
import json
import asyncio
import time

router = APIRouter()

HEARTBEAT_INTERVAL = 30
HEARTBEAT_TIMEOUT = 60

class NotificationType(str, Enum):
    STATUS_CHANGE = "status_change"
    TASK_ASSIGNED = "task_assigned"
    MILESTONE_COMPLETED = "milestone_completed"

class EntityType(str, Enum):
    PROJECT = "project"
    TASK = "task"
    MILESTONE = "milestone"

class MessageType(str, Enum):
    PING = "ping"
    PONG = "pong"
    NOTIFICATION = "notification"
    HEARTBEAT = "heartbeat"

class NotificationMessage:
    def __init__(
        self,
        type: NotificationType,
        entity_type: EntityType,
        entity_id: int,
        message: str,
        data: Optional[Dict[str, Any]] = None
    ):
        self.type = type
        self.entity_type = entity_type
        self.entity_id = entity_id
        self.message = message
        self.timestamp = datetime.now().isoformat()
        self.data = data or {}

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": self.type.value,
            "entity_type": self.entity_type.value,
            "entity_id": self.entity_id,
            "message": self.message,
            "timestamp": self.timestamp,
            "data": self.data
        }

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.user_connections: Dict[int, List[WebSocket]] = {}
        self.connection_heartbeats: Dict[WebSocket, float] = {}
        self._heartbeat_task: Optional[asyncio.Task] = None

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

    async def connect(self, websocket: WebSocket, user_id: Optional[int] = None):
        await websocket.accept()
        self.active_connections.append(websocket)
        self.connection_heartbeats[websocket] = time.time()
        if user_id:
            if user_id not in self.user_connections:
                self.user_connections[user_id] = []
            self.user_connections[user_id].append(websocket)
        await self.start_heartbeat_monitor()

    def disconnect(self, websocket: WebSocket, user_id: Optional[int] = None):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        if websocket in self.connection_heartbeats:
            del self.connection_heartbeats[websocket]
        if user_id and user_id in self.user_connections:
            if websocket in self.user_connections[user_id]:
                self.user_connections[user_id].remove(websocket)
            if not self.user_connections[user_id]:
                del self.user_connections[user_id]

    async def broadcast(self, message: Dict[str, Any]):
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception:
                pass

    async def send_to_user(self, user_id: int, message: Dict[str, Any]):
        if user_id in self.user_connections:
            for connection in self.user_connections[user_id]:
                try:
                    await connection.send_json(message)
                except Exception:
                    pass

    async def broadcast_notification(self, notification: NotificationMessage):
        await self.broadcast(notification.to_dict())

    async def send_notification_to_user(self, user_id: int, notification: NotificationMessage):
        await self.send_to_user(user_id, notification.to_dict())

manager = ConnectionManager()

@router.websocket("/status")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            try:
                message = json.loads(data)
                if message.get("type") == MessageType.PING.value:
                    manager.update_heartbeat(websocket)
                    await websocket.send_json({"type": MessageType.PONG.value, "timestamp": time.time()})
                elif message.get("type") == MessageType.HEARTBEAT.value:
                    manager.update_heartbeat(websocket)
                    await websocket.send_json({"type": MessageType.HEARTBEAT.value, "timestamp": time.time()})
                else:
                    await manager.broadcast(message)
            except json.JSONDecodeError:
                await websocket.send_json({"error": "Invalid JSON"})
    except WebSocketDisconnect:
        manager.disconnect(websocket)

@router.websocket("/notifications/{user_id}")
async def notifications_endpoint(websocket: WebSocket, user_id: int):
    await manager.connect(websocket, user_id)
    try:
        while True:
            data = await websocket.receive_text()
            try:
                message = json.loads(data)
                if message.get("type") == MessageType.PING.value:
                    manager.update_heartbeat(websocket)
                    await websocket.send_json({"type": MessageType.PONG.value, "timestamp": time.time()})
                elif message.get("type") == MessageType.HEARTBEAT.value:
                    manager.update_heartbeat(websocket)
                    await websocket.send_json({"type": MessageType.HEARTBEAT.value, "timestamp": time.time()})
            except json.JSONDecodeError:
                await websocket.send_json({"error": "Invalid JSON"})
    except WebSocketDisconnect:
        manager.disconnect(websocket, user_id)

async def broadcast_status_update(event_type: str, data: dict):
    await manager.broadcast({
        "type": event_type,
        "data": data,
        "timestamp": datetime.now().isoformat()
    })

async def notify_status_change(
    entity_type: EntityType,
    entity_id: int,
    old_status: str,
    new_status: str,
    entity_name: str,
    additional_data: Optional[Dict[str, Any]] = None
):
    notification = NotificationMessage(
        type=NotificationType.STATUS_CHANGE,
        entity_type=entity_type,
        entity_id=entity_id,
        message=f"{entity_type.value} '{entity_name}' 状态已从 '{old_status}' 变更为 '{new_status}'",
        data={
            "old_status": old_status,
            "new_status": new_status,
            "entity_name": entity_name,
            **(additional_data or {})
        }
    )
    await manager.broadcast_notification(notification)

async def notify_task_assigned(
    task_id: int,
    task_name: str,
    agent_id: int,
    agent_name: str,
    assigned_by: Optional[str] = None,
    additional_data: Optional[Dict[str, Any]] = None
):
    notification = NotificationMessage(
        type=NotificationType.TASK_ASSIGNED,
        entity_type=EntityType.TASK,
        entity_id=task_id,
        message=f"任务 '{task_name}' 已分配给 {agent_name}",
        data={
            "task_id": task_id,
            "task_name": task_name,
            "agent_id": agent_id,
            "agent_name": agent_name,
            "assigned_by": assigned_by,
            **(additional_data or {})
        }
    )
    await manager.broadcast_notification(notification)
    await manager.send_notification_to_user(agent_id, notification)

async def notify_milestone_completed(
    milestone_id: int,
    milestone_name: str,
    project_id: int,
    project_name: str,
    completed_by: Optional[str] = None,
    additional_data: Optional[Dict[str, Any]] = None
):
    notification = NotificationMessage(
        type=NotificationType.MILESTONE_COMPLETED,
        entity_type=EntityType.MILESTONE,
        entity_id=milestone_id,
        message=f"里程碑 '{milestone_name}' 已完成（项目：{project_name}）",
        data={
            "milestone_id": milestone_id,
            "milestone_name": milestone_name,
            "project_id": project_id,
            "project_name": project_name,
            "completed_by": completed_by,
            **(additional_data or {})
        }
    )
    await manager.broadcast_notification(notification)

def get_notification_manager() -> ConnectionManager:
    return manager
