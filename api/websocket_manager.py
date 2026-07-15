from fastapi import WebSocket
from typing import Dict
from api.config import auto_logger

class ConnectionManager:
    def __init__(self):
        # maps room_id -> { "X": websocket, "O": websocket }
        self.active_connections: Dict[str, Dict[str, WebSocket]] = {}

    @auto_logger()
    async def connect(self, websocket: WebSocket, room_id: str, role: str):
        await websocket.accept()
        if room_id not in self.active_connections:
            self.active_connections[room_id] = {}
        self.active_connections[room_id][role] = websocket

    @auto_logger()
    def disconnect(self, room_id: str, role: str):
        if room_id in self.active_connections:
            if role in self.active_connections[room_id]:
                del self.active_connections[room_id][role]
            if not self.active_connections[room_id]:
                del self.active_connections[room_id]

    @auto_logger()
    async def send_to_player(self, message: dict, room_id: str, role: str):
        if room_id in self.active_connections and role in self.active_connections[room_id]:
            websocket = self.active_connections[room_id][role]
            # fastapi websockets support send_json
            await websocket.send_json(message)

    @auto_logger()
    async def broadcast_to_room(self, message: dict, room_id: str):
        if room_id in self.active_connections:
            for role, websocket in self.active_connections[room_id].items():
                try:
                    await websocket.send_json(message)
                except Exception:
                    # connection might be closed already
                    pass

# instantiate a global connection manager
manager = ConnectionManager()
