"""
internal models and enums for room state management.
"""

import time
from enum import Enum
from typing import Any, Dict, List, Optional


class RoomStatus(str, Enum):
    NOT_STARTED = "not_started"
    ACTIVE = "active"
    PAUSED = "paused"
    FINISHED = "finished"


class PlayerRole(str, Enum):
    HOST = "host"
    GUEST = "guest"


class GameRoom:
    def __init__(self, room_code: str, host_user_id: str):
        self.room_code = room_code
        self.host_user_id = host_user_id
        self.guest_user_id: Optional[str] = None
        self.current_x_player = PlayerRole.HOST
        self.status = RoomStatus.NOT_STARTED
        self.created_at = time.time()
        self.sockets: Dict[str, List[Any]] = {}

    def get_role(self, user_id: str) -> Optional[str]:
        if user_id == self.host_user_id:
            return "X" if self.current_x_player == PlayerRole.HOST else "O"
        elif user_id == self.guest_user_id:
            return "X" if self.current_x_player == PlayerRole.GUEST else "O"
        return None
