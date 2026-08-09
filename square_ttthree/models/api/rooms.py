"""
pydantic models for the rooms router endpoints.
"""

from typing import Any, Dict, Optional

from pydantic import BaseModel


class RoomCreateRequestModel(BaseModel):
    user_id: str


class RoomCreateResponseModel(BaseModel):
    room_code: str


class RoomGetResponseModel(BaseModel):
    room_code: str
    is_joinable: bool


class WSInboundMessage(BaseModel):
    event: str
    payload: Dict[str, Any] = {}


class WSJoinRoomPayload(BaseModel):
    user_id: str


class WSStateUpdatePayload(BaseModel):
    room_code: str
    status: str
    host_user_id: str
    guest_user_id: Optional[str] = None
    current_x_player: str
    created_at: float
    host_connected: bool
    guest_connected: bool
    board: list[str]
    current_turn: str
    previous_match_results: Dict[str, int]


class WSMakeMovePayload(BaseModel):
    cell_index: int


class WSGameOverPayload(BaseModel):
    winner: str
    winning_line: Optional[list[int]] = None
    previous_match_results: Dict[str, int]


class WSErrorPayload(BaseModel):
    code: str
    message: str


class RoomStateModel(BaseModel):
    room_code: str
    status: str
    host_user_id: str
    guest_user_id: Optional[str] = None
    current_x_player: str
    created_at: float
    host_connected: bool
    guest_connected: bool
    total_connected_sockets: int
    board: list[str]
    current_turn: str
    previous_match_results: Dict[str, int]


class RoomGetAllResponseModel(BaseModel):
    rooms: list[RoomStateModel]
    total_rooms: int
