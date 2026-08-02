"""
internal models and enums for room state management.
"""

import time
from enum import Enum
from typing import Optional


class RoomStatus(str, Enum):
    NOT_STARTED = "not_started"
    ACTIVE = "active"
    PAUSED = "paused"
    FINISHED = "finished"


class GameRoom:
    def __init__(self, room_code: str, host_user_id: str):
        self.room_code = room_code
        self.host_user_id = host_user_id
        self.guest_user_id: Optional[str] = None
        self.status = RoomStatus.NOT_STARTED
        self.created_at = time.time()
