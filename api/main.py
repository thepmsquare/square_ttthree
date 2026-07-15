import secrets
from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, HTTPException, status, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List

from api.config import HOST, PORT, auto_logger
from api.database import engine, get_db
from api.models import Base, Player, GameRoom
from api.schemas import PlayerRegister, PlayerLogin, PlayerResponse, Token, RoomCreate, RoomResponse
from api.auth import get_password_hash, verify_password, create_access_token, get_current_player, verify_access_token
from api.websocket_manager import manager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # create database tables if they do not exist
    print("startup: creating database tables...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("startup: database tables created.")
    yield
    # dispose engine on shutdown
    await engine.dispose()

app = FastAPI(lifespan=lifespan)

# configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def check_winner(board: List[int]) -> str | None:
    """checks if X (1) or O (-1) won, or if it is a draw, or None if ongoing."""
    winning_lines = [
        (0, 1, 2), (3, 4, 5), (6, 7, 8),  # rows
        (0, 3, 6), (1, 4, 7), (2, 5, 8),  # columns
        (0, 4, 8), (2, 4, 6)              # diagonals
    ]
    for line in winning_lines:
        line_sum = sum(board[i] for i in line)
        if line_sum == 3:
            return "X"
        if line_sum == -3:
            return "O"
            
    if 0 not in board:
        return "draw"
        
    return None

@app.post("/register", response_model=PlayerResponse, status_code=status.HTTP_201_CREATED)
@auto_logger()
async def register(player_data: PlayerRegister, db: AsyncSession = Depends(get_db)):
    # check if username exists
    result = await db.execute(select(Player).where(Player.username == player_data.username))
    if result.scalars().first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="username already exists"
        )
        
    hashed_pwd = get_password_hash(player_data.password)
    new_player = Player(
        username=player_data.username,
        password_hash=hashed_pwd
    )
    db.add(new_player)
    await db.commit()
    await db.refresh(new_player)
    return new_player

@app.post("/login", response_model=Token)
@auto_logger()
async def login(login_data: PlayerLogin, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Player).where(Player.username == login_data.username))
    player = result.scalars().first()
    if not player or not verify_password(login_data.password, player.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="invalid username or password"
        )
        
    token = create_access_token(data={"sub": player.username})
    return {"access_token": token, "token_type": "bearer"}

@app.get("/player/me", response_model=PlayerResponse)
@auto_logger()
async def get_me(current_player: Player = Depends(get_current_player)):
    return current_player

@app.post("/room", response_model=RoomResponse, status_code=status.HTTP_201_CREATED)
@auto_logger()
async def create_room(room_data: RoomCreate, current_player: Player = Depends(get_current_player), db: AsyncSession = Depends(get_db)):
    # generate a unique 6-character room ID
    room_id = secrets.token_hex(3)
    
    # ensure uniqueness
    while True:
        res = await db.execute(select(GameRoom).where(GameRoom.id == room_id))
        if not res.scalars().first():
            break
        room_id = secrets.token_hex(3)
        
    if room_data.play_as == "O":
        new_room = GameRoom(
            id=room_id,
            player_o_id=current_player.id,
            player_x_id=None,
            current_turn="X"  # X always starts
        )
    else:
        new_room = GameRoom(
            id=room_id,
            player_x_id=current_player.id,
            player_o_id=None,
            current_turn="X"
        )
        
    db.add(new_room)
    await db.commit()
    await db.refresh(new_room)
    return new_room

@app.get("/rooms", response_model=List[RoomResponse])
@auto_logger()
async def list_rooms(db: AsyncSession = Depends(get_db)):
    # return active or waiting rooms
    result = await db.execute(select(GameRoom).where(GameRoom.status != "finished"))
    return list(result.scalars().all())

@app.websocket("/ws/room/{room_id}")
async def websocket_endpoint(websocket: WebSocket, room_id: str, token: str = None, db: AsyncSession = Depends(get_db)):
    if not token:
        await websocket.close(code=4000, reason="token is required")
        return
        
    payload = verify_access_token(token)
    if not payload or "sub" not in payload:
        await websocket.close(code=4001, reason="invalid token")
        return
        
    # get player from DB
    result = await db.execute(select(Player).where(Player.username == payload["sub"]))
    player = result.scalars().first()
    if not player:
        await websocket.close(code=4002, reason="player not found")
        return
        
    # get game room
    result = await db.execute(select(GameRoom).where(GameRoom.id == room_id))
    room = result.scalars().first()
    if not room:
        await websocket.close(code=4003, reason="room not found")
        return
        
    # determine role
    role = None
    if room.player_x_id == player.id:
        role = "X"
    elif room.player_o_id == player.id:
        role = "O"
    else:
        # join room as second player
        if room.player_x_id is None:
            room.player_x_id = player.id
            role = "X"
        elif room.player_o_id is None:
            room.player_o_id = player.id
            role = "O"
        else:
            await websocket.close(code=4004, reason="room is full")
            return
            
        # if both players are present, start game
        if room.player_x_id is not None and room.player_o_id is not None:
            room.status = "active"
        await db.commit()
        await db.refresh(room)
        
    # connect to websocket manager
    await manager.connect(websocket, room_id, role)
    
    # notify room
    await manager.broadcast_to_room({
        "type": "player_joined",
        "payload": {
            "player_id": player.id,
            "username": player.username,
            "role": role,
            "status": room.status
        }
    }, room_id)
    
    # sync initial game state
    await manager.send_to_player({
        "type": "game_state",
        "payload": {
            "board": room.board,
            "status": room.status,
            "current_turn": room.current_turn,
            "player_x_id": room.player_x_id,
            "player_o_id": room.player_o_id
        }
    }, room_id, role)
    
    try:
        while True:
            # receive message from client
            data = await websocket.receive_json()
            
            # verify turn
            if room.status != "active":
                await manager.send_to_player({
                    "type": "error",
                    "payload": {"message": "game is not active"}
                }, room_id, role)
                continue
                
            if room.current_turn != role:
                await manager.send_to_player({
                    "type": "error",
                    "payload": {"message": "not your turn"}
                }, room_id, role)
                continue
                
            action_type = data.get("action")
            if action_type == "make_move":
                position = data.get("position")
                if position is None or not (0 <= position <= 8) or room.board[position] != 0:
                    await manager.send_to_player({
                        "type": "error",
                        "payload": {"message": "invalid position"}
                    }, room_id, role)
                    continue
                    
                # execute move: 1 for X, -1 for O
                room.board[position] = 1 if role == "X" else -1
                
                # check game state
                winner_token = check_winner(room.board)
                
                if winner_token is not None:
                    # game finished
                    room.status = "finished"
                    
                    if winner_token == "draw":
                        # draw: update stats
                        # we must query players inside this session or retrieve them
                        x_player = await db.get(Player, room.player_x_id)
                        o_player = await db.get(Player, room.player_o_id)
                        x_player.draws += 1
                        o_player.draws += 1
                    else:
                        winner_id = room.player_x_id if winner_token == "X" else room.player_o_id
                        loser_id = room.player_o_id if winner_token == "X" else room.player_x_id
                        
                        room.winner_id = winner_id
                        
                        winner_player = await db.get(Player, winner_id)
                        loser_player = await db.get(Player, loser_id)
                        winner_player.wins += 1
                        loser_player.losses += 1
                        
                    await db.commit()
                    await db.refresh(room)
                    
                    await manager.broadcast_to_room({
                        "type": "game_over",
                        "payload": {
                            "board": room.board,
                            "status": room.status,
                            "winner": winner_token,
                            "winner_id": room.winner_id
                        }
                    }, room_id)
                else:
                    # switch turn
                    room.current_turn = "O" if role == "X" else "X"
                    await db.commit()
                    await db.refresh(room)
                    
                    await manager.broadcast_to_room({
                        "type": "move_made",
                        "payload": {
                            "board": room.board,
                            "current_turn": room.current_turn,
                            "last_move_by": role
                        }
                    }, room_id)
                    
    except WebSocketDisconnect:
        manager.disconnect(room_id, role)
        print(f"websocket disconnected: room={room_id}, role={role}")
        await manager.broadcast_to_room({
            "type": "player_left",
            "payload": {
                "role": role,
                "player_id": player.id,
                "username": player.username
            }
        }, room_id)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api.main:app", host=HOST, port=PORT, reload=True)
