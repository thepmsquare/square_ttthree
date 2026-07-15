from sqlalchemy import ForeignKey, JSON
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from typing import Optional

class Base(DeclarativeBase):
    pass

class Player(Base):
    __tablename__ = "player"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(unique=True, index=True)
    password_hash: Mapped[str]

    wins: Mapped[int] = mapped_column(default=0)
    losses: Mapped[int] = mapped_column(default=0)
    draws: Mapped[int] = mapped_column(default=0)

class GameRoom(Base):
    __tablename__ = "game_room"

    id: Mapped[str] = mapped_column(primary_key=True)  # unique room code
    player_x_id: Mapped[Optional[int]] = mapped_column(ForeignKey("player.id"), nullable=True)
    player_o_id: Mapped[Optional[int]] = mapped_column(ForeignKey("player.id"), nullable=True)
    
    # board state: flat list of 9 elements. 0 = empty, 1 = X, -1 = O
    board: Mapped[list] = mapped_column(JSON, default=lambda: [0]*9)
    status: Mapped[str] = mapped_column(default="waiting")  # "waiting", "active", "finished"
    current_turn: Mapped[str] = mapped_column(default="X")  # "X" or "O"
    winner_id: Mapped[Optional[int]] = mapped_column(ForeignKey("player.id"), nullable=True)

    player_x: Mapped[Optional[Player]] = relationship(foreign_keys=[player_x_id])
    player_o: Mapped[Optional[Player]] = relationship(foreign_keys=[player_o_id])
    winner: Mapped[Optional[Player]] = relationship(foreign_keys=[winner_id])
