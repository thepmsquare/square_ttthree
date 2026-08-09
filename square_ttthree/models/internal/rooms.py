"""
internal models and enums for room state management.
"""

import time
from enum import Enum
from typing import Any, Dict, List, Optional


class RoomStatus(str, Enum):
    NOT_STARTED = "not_started"
    READY = "ready"
    MATCH_ONGOING = "match_ongoing"
    PAUSED = "paused"
    MISSING_PLAYER = "missing_player"
    EMPTY_LOBBY = "empty_lobby"


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
        self.explicit_leave: bool = False
        self.created_at = time.time()
        self.sockets: Dict[str, List[Any]] = {}
        self.board: List[str] = [""] * 9
        self.current_turn: str = "X"
        self.previous_match_results: Dict[str, int] = {
            "host_wins": 0,
            "guest_wins": 0,
            "draws": 0,
        }

    def get_role(self, user_id: str) -> Optional[str]:
        if user_id == self.host_user_id:
            return "X" if self.current_x_player == PlayerRole.HOST else "O"
        elif user_id == self.guest_user_id:
            return "X" if self.current_x_player == PlayerRole.GUEST else "O"
        return None
