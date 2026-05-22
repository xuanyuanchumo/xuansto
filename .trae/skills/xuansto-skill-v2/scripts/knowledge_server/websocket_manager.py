import asyncio
import logging

logger = logging.getLogger("knowledge-server")


class WebSocketManager:
    def __init__(self):
        self._connections: list = []

    async def connect(self, websocket):
        await websocket.accept()
        self._connections.append(websocket)

    def disconnect(self, websocket):
        if websocket in self._connections:
            self._connections.remove(websocket)

    async def broadcast(self, message: dict):
        disconnected = []
        for ws in self._connections:
            try:
                await ws.send_json(message)
            except Exception:
                disconnected.append(ws)
        for ws in disconnected:
            self.disconnect(ws)

    def broadcast_sync(self, message: dict):
        if not self._connections:
            return
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                asyncio.run_coroutine_threadsafe(self.broadcast(message), loop)
            else:
                loop.run_until_complete(self.broadcast(message))
        except RuntimeError:
            pass

    @property
    def connection_count(self) -> int:
        return len(self._connections)
