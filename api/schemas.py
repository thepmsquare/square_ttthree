from pydantic import BaseModel
from typing import Optional, List

class PlayerBase(BaseModel):
    username: str

class PlayerRegister(PlayerBase):
    password: str

class PlayerLogin(PlayerBase):
    password: str

class PlayerResponse(PlayerBase):
    id: int
    wins: int
    losses: int
    draws: int

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str

class RoomCreate(BaseModel):
    play_as: Optional[str] = "X"  # "X" or "O"

class RoomResponse(BaseModel):
    id: str
    player_x_id: Optional[int] = None
    player_o_id: Optional[int] = None
    board: List[int]
    status: str
    current_turn: str
    winner_id: Optional[int] = None

    class Config:
        from_attributes = True
