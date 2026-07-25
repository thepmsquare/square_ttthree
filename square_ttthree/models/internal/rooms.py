"""
internal models and enums for room state management.
"""

from enum import Enum
import time


class RoomStatus(str, Enum):
    NOT_STARTED = "not_started"
    ACTIVE = "active"
    PAUSED = "paused"
    FINISHED = "finished"


class GameRoom:
    def __init__(self, room_code: str):
        self.room_code = room_code
        self.status = RoomStatus.NOT_STARTED
        self.created_at = time.time()
