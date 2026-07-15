import asyncio
import httpx
import websockets
import json

BASE_URL = "http://localhost:8000"
WS_URL = "ws://localhost:8000"

async def play_game():
    print("starting multiplayer api and websocket validation...")
    
    async with httpx.AsyncClient() as client:
        # 1. register player 1
        print("\n1. registering player1...")
        p1_reg = await client.post(f"{BASE_URL}/register", json={
            "username": "player1",
            "password": "password123"
        })
        if p1_reg.status_code == 201:
            print("player1 registered successfully.")
        else:
            print(f"player1 registration skipped/status: {p1_reg.json().get('detail')}")
            
        # 2. register player 2
        print("\n2. registering player2...")
        p2_reg = await client.post(f"{BASE_URL}/register", json={
            "username": "player2",
            "password": "password123"
        })
        if p2_reg.status_code == 201:
            print("player2 registered successfully.")
        else:
            print(f"player2 registration skipped/status: {p2_reg.json().get('detail')}")
            
        # 3. login player 1
        print("\n3. logging in player1...")
        p1_login = await client.post(f"{BASE_URL}/login", json={
            "username": "player1",
            "password": "password123"
        })
        p1_token = p1_login.json()["access_token"]
        print("player1 token retrieved.")
        
        # 4. login player 2
        print("\n4. logging in player2...")
        p2_login = await client.post(f"{BASE_URL}/login", json={
            "username": "player2",
            "password": "password123"
        })
        p2_token = p2_login.json()["access_token"]
        print("player2 token retrieved.")
        
        # 5. player 1 creates room
        print("\n5. player1 creating a game room...")
        headers = {"Authorization": f"Bearer {p1_token}"}
        room_res = await client.post(f"{BASE_URL}/room", json={"play_as": "X"}, headers=headers)
        room = room_res.json()
        room_id = room["id"]
        print(f"game room created with id: {room_id}")
        
    # 6. establish websocket connections
    print(f"\n6. establishing websocket connections for room {room_id}...")
    p1_ws_uri = f"{WS_URL}/ws/room/{room_id}?token={p1_token}"
    p2_ws_uri = f"{WS_URL}/ws/room/{room_id}?token={p2_token}"
    
    async with websockets.connect(p1_ws_uri) as ws1, websockets.connect(p2_ws_uri) as ws2:
        # player 1 receives connection info
        await ws1.recv()
        p1_msg2 = await ws1.recv()
        print(f"player1 received initial frames: {json.loads(p1_msg2)['type']}")
        
        # player 2 receives connection info
        await ws2.recv()
        await ws2.recv()
        p2_msg3 = await ws2.recv()
        print(f"player2 received initial frames: {json.loads(p2_msg3)['type']}")
        
        # 7. simulate game moves
        # standard tic-tac-toe sequence:
        # X: 0
        # O: 4
        # X: 1
        # O: 5
        # X: 2 (X wins)
        moves = [
            (ws1, 0, "X"),
            (ws2, 4, "O"),
            (ws1, 1, "X"),
            (ws2, 5, "O"),
            (ws1, 2, "X")
        ]
        
        for ws, pos, role in moves:
            print(f"\nplayer {role} playing move in space {pos}...")
            await ws.send(json.dumps({"action": "make_move", "position": pos}))
            
            # read responses for both players
            msg1 = await ws1.recv()
            await ws2.recv()
            data1 = json.loads(msg1)
            print(f"broadcast result: {data1['type']} - board: {data1['payload']['board']}")
            
        print("\nmultiplayer sequence complete. verifying stats...")
        async with httpx.AsyncClient() as client:
            p1_stats = await client.get(f"{BASE_URL}/player/me", headers={"Authorization": f"Bearer {p1_token}"})
            p2_stats = await client.get(f"{BASE_URL}/player/me", headers={"Authorization": f"Bearer {p2_token}"})
            print(f"player1 wins count: {p1_stats.json()['wins']}")
            print(f"player2 losses count: {p2_stats.json()['losses']}")

if __name__ == "__main__":
    asyncio.run(play_game())
