"""
pydantic models for the rooms router endpoints.
"""

from typing import Any, Dict

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
    your_role: str
    status: str


class WSErrorPayload(BaseModel):
    code: str
    message: str
