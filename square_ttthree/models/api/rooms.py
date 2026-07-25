"""
pydantic models for the rooms router endpoints.
"""

from pydantic import BaseModel


class RoomCreateResponseModel(BaseModel):
    room_code: str


class RoomGetResponseModel(BaseModel):
    room_code: str
    is_joinable: bool
