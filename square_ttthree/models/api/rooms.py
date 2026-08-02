"""
pydantic models for the rooms router endpoints.
"""

from pydantic import BaseModel


class RoomCreateRequestModel(BaseModel):
    user_id: str


class RoomCreateResponseModel(BaseModel):
    room_code: str


class RoomGetResponseModel(BaseModel):
    room_code: str
    is_joinable: bool
