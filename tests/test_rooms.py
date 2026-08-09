import pytest


@pytest.mark.anyio
async def test_create_room(get_patched_configuration, create_client_and_cleanup):
    client = create_client_and_cleanup
    response = await client.post("/api/v1/room", json={"user_id": "usr_test123"})
    assert response.status_code == 201

    json_data = response.json()
    assert "data" in json_data
    assert "message" in json_data
    assert "log" in json_data

    assert json_data["message"] == "the record has been created successfully."

    data = json_data["data"]
    assert "room_code" in data
    assert len(data["room_code"]) == 4


@pytest.mark.anyio
async def test_get_room_success(get_patched_configuration, create_client_and_cleanup):
    client = create_client_and_cleanup

    # 1. create room first
    create_response = await client.post("/api/v1/room", json={"user_id": "usr_test123"})
    assert create_response.status_code == 201
    room_code = create_response.json()["data"]["room_code"]

    # 2. get the created room
    get_response = await client.get(f"/api/v1/room/{room_code}")
    assert get_response.status_code == 200

    json_data = get_response.json()
    assert json_data["message"] == "the record has been retrieved successfully."

    data = json_data["data"]
    assert data["room_code"] == room_code
    assert data["is_joinable"] is True


@pytest.mark.anyio
async def test_get_room_case_insensitive(
    get_patched_configuration, create_client_and_cleanup
):
    client = create_client_and_cleanup

    # 1. create room first
    create_response = await client.post("/api/v1/room", json={"user_id": "usr_test123"})
    assert create_response.status_code == 201
    room_code = create_response.json()["data"]["room_code"]

    # 2. get room using lowercase room code
    get_response = await client.get(f"/api/v1/room/{room_code.lower()}")
    assert get_response.status_code == 200

    data = get_response.json()["data"]
    assert data["room_code"] == room_code
    assert data["is_joinable"] is True


@pytest.mark.anyio
async def test_get_room_not_found(get_patched_configuration, create_client_and_cleanup):
    client = create_client_and_cleanup

    # get a non-existent room
    response = await client.get("/api/v1/room/NONEXISTENTROOMCODE")
    assert response.status_code == 404

    json_data = response.json()
    assert json_data["data"] is None
    assert json_data["message"] == "the record could not be found."
    assert json_data["log"] == "NONEXISTENTROOMCODE not found."


@pytest.mark.anyio
async def test_create_room_http_exception(
    get_patched_configuration, create_client_and_cleanup, mocker
):
    from fastapi import HTTPException

    client = create_client_and_cleanup
    mocker.patch(
        "square_ttthree.routes.rooms.logic_create_room",
        side_effect=HTTPException(status_code=400, detail="bad request"),
    )
    response = await client.post("/api/v1/room", json={"user_id": "usr_test123"})
    assert response.status_code == 400
    assert response.json() == "bad request"


@pytest.mark.anyio
async def test_create_room_generic_exception(
    get_patched_configuration, create_client_and_cleanup, mocker
):
    client = create_client_and_cleanup
    mocker.patch(
        "square_ttthree.logic.rooms.room_manager.create_room",
        side_effect=RuntimeError("create failure"),
    )
    response = await client.post("/api/v1/room", json={"user_id": "usr_test123"})
    assert response.status_code == 500
    json_data = response.json()
    assert (
        json_data["message"]
        == "an internal server error occurred. please try again later."
    )
    assert "create failure" in json_data["log"]


@pytest.mark.anyio
async def test_get_room_http_exception(
    get_patched_configuration, create_client_and_cleanup, mocker
):
    from fastapi import HTTPException

    client = create_client_and_cleanup
    mocker.patch(
        "square_ttthree.routes.rooms.logic_get_room",
        side_effect=HTTPException(status_code=403, detail="forbidden"),
    )
    response = await client.get("/api/v1/room/ABCD")
    assert response.status_code == 403
    assert response.json() == "forbidden"


@pytest.mark.anyio
async def test_get_room_generic_exception(
    get_patched_configuration, create_client_and_cleanup, mocker
):
    client = create_client_and_cleanup
    mocker.patch(
        "square_ttthree.logic.rooms.room_manager.get_room",
        side_effect=RuntimeError("get failure"),
    )
    response = await client.get("/api/v1/room/ABCD")
    assert response.status_code == 500
    json_data = response.json()
    assert (
        json_data["message"]
        == "an internal server error occurred. please try again later."
    )
    assert "get failure" in json_data["log"]


def test_room_manager_collision(mocker):
    from square_ttthree.logic.rooms import RoomManager

    manager = RoomManager()
    manager._rooms["AAAA"] = None  # simulate existing room code

    mocker.patch("random.choices", side_effect=[list("AAAA"), list("BBBB")])
    room = manager.create_room(host_user_id="usr_test123")
    assert room.room_code == "BBBB"
    assert room.host_user_id == "usr_test123"


def test_ws_join_room_host(get_patched_configuration):
    from fastapi.testclient import TestClient

    from square_ttthree.main import app

    client = TestClient(app)
    res = client.post("/api/v1/room", json={"user_id": "usr_host123"})
    room_code = res.json()["data"]["room_code"]

    with client.websocket_connect(f"/ws/room/{room_code}") as ws:
        ws.send_json({"event": "JOIN_ROOM", "payload": {"user_id": "usr_host123"}})
        msg = ws.receive_json()
        assert msg["event"] == "STATE_UPDATE"
        assert msg["payload"]["room_code"] == room_code
        assert msg["payload"]["host_user_id"] == "usr_host123"
        assert msg["payload"]["guest_user_id"] is None
        assert msg["payload"]["current_x_player"] == "host"
        assert msg["payload"]["host_connected"] is True
        assert msg["payload"]["guest_connected"] is False
        assert msg["payload"]["status"] == "not_started"
        assert msg["payload"]["previous_match_results"] == {
            "host_wins": 0,
            "guest_wins": 0,
            "draws": 0,
        }


def test_ws_join_room_guest(get_patched_configuration):
    from fastapi.testclient import TestClient

    from square_ttthree.main import app

    client = TestClient(app)
    res = client.post("/api/v1/room", json={"user_id": "usr_host123"})
    room_code = res.json()["data"]["room_code"]

    with client.websocket_connect(f"/ws/room/{room_code}") as host_ws:
        host_ws.send_json({"event": "JOIN_ROOM", "payload": {"user_id": "usr_host123"}})
        _ = host_ws.receive_json()

        with client.websocket_connect(f"/ws/room/{room_code}") as guest_ws:
            guest_ws.send_json(
                {"event": "JOIN_ROOM", "payload": {"user_id": "usr_guest456"}}
            )

            guest_msg = guest_ws.receive_json()
            assert guest_msg["event"] == "STATE_UPDATE"
            assert guest_msg["payload"]["host_user_id"] == "usr_host123"
            assert guest_msg["payload"]["guest_user_id"] == "usr_guest456"
            assert guest_msg["payload"]["host_connected"] is True
            assert guest_msg["payload"]["guest_connected"] is True
            assert guest_msg["payload"]["status"] == "ready"

            host_msg = host_ws.receive_json()
            assert host_msg["event"] == "STATE_UPDATE"
            assert host_msg["payload"]["host_connected"] is True
            assert host_msg["payload"]["guest_connected"] is True
            assert host_msg["payload"]["status"] == "ready"


def test_ws_leave_room_missing_player(get_patched_configuration):
    from fastapi.testclient import TestClient

    from square_ttthree.main import app

    client = TestClient(app)
    res = client.post("/api/v1/room", json={"user_id": "usr_host123"})
    room_code = res.json()["data"]["room_code"]

    with client.websocket_connect(f"/ws/room/{room_code}") as host_ws:
        host_ws.send_json({"event": "JOIN_ROOM", "payload": {"user_id": "usr_host123"}})
        _ = host_ws.receive_json()

        with client.websocket_connect(f"/ws/room/{room_code}") as guest_ws:
            guest_ws.send_json(
                {"event": "JOIN_ROOM", "payload": {"user_id": "usr_guest456"}}
            )
            _ = guest_ws.receive_json()
            _ = host_ws.receive_json()

            # guest sends LEAVE_ROOM
            guest_ws.send_json({"event": "LEAVE_ROOM"})
            host_msg = host_ws.receive_json()
            assert host_msg["event"] == "STATE_UPDATE"
            assert host_msg["payload"]["status"] == "missing_player"
            assert host_msg["payload"]["guest_connected"] is False


def test_ws_disconnect_empty_lobby(get_patched_configuration):
    from fastapi.testclient import TestClient

    from square_ttthree.main import app

    client = TestClient(app)
    res = client.post("/api/v1/room", json={"user_id": "usr_host123"})
    room_code = res.json()["data"]["room_code"]

    with client.websocket_connect(f"/ws/room/{room_code}") as ws:
        ws.send_json({"event": "JOIN_ROOM", "payload": {"user_id": "usr_host123"}})
        _ = ws.receive_json()

    # after ws block exits (disconnects), check room status via GET /api/v1/rooms
    rooms_res = client.get("/api/v1/rooms")
    room_item = next(
        r for r in rooms_res.json()["data"]["rooms"] if r["room_code"] == room_code
    )
    assert room_item["status"] == "empty_lobby"
    assert room_item["host_connected"] is False


def test_ws_join_room_invalid_room(get_patched_configuration):
    from fastapi.testclient import TestClient

    from square_ttthree.main import app

    client = TestClient(app)
    with client.websocket_connect("/ws/room/INVALID") as ws:
        msg = ws.receive_json()
        assert msg["event"] == "ERROR"
        assert msg["payload"]["code"] == "ROOM_NOT_FOUND"


def test_ws_join_room_missing_user_id(get_patched_configuration):
    from fastapi.testclient import TestClient

    from square_ttthree.main import app

    client = TestClient(app)
    res = client.post("/api/v1/room", json={"user_id": "usr_host123"})
    room_code = res.json()["data"]["room_code"]

    with client.websocket_connect(f"/ws/room/{room_code}") as ws:
        ws.send_json({"event": "JOIN_ROOM", "payload": {}})
        msg = ws.receive_json()
        assert msg["event"] == "ERROR"
        assert msg["payload"]["code"] == "INVALID_PAYLOAD"


def test_ws_join_room_full(get_patched_configuration):
    from fastapi.testclient import TestClient

    from square_ttthree.main import app

    client = TestClient(app)
    res = client.post("/api/v1/room", json={"user_id": "usr_host123"})
    room_code = res.json()["data"]["room_code"]

    with client.websocket_connect(f"/ws/room/{room_code}") as host_ws:
        host_ws.send_json({"event": "JOIN_ROOM", "payload": {"user_id": "usr_host123"}})
        _ = host_ws.receive_json()

        with client.websocket_connect(f"/ws/room/{room_code}") as guest_ws:
            guest_ws.send_json(
                {"event": "JOIN_ROOM", "payload": {"user_id": "usr_guest456"}}
            )
            _ = guest_ws.receive_json()

            with client.websocket_connect(f"/ws/room/{room_code}") as third_ws:
                third_ws.send_json(
                    {"event": "JOIN_ROOM", "payload": {"user_id": "usr_third789"}}
                )
                msg = third_ws.receive_json()
                assert msg["event"] == "ERROR"
                assert msg["payload"]["code"] == "ROOM_FULL"


@pytest.mark.anyio
async def test_get_all_rooms(get_patched_configuration, create_client_and_cleanup):
    client = create_client_and_cleanup

    # 1. create a room
    res1 = await client.post("/api/v1/room", json={"user_id": "usr_admin_host1"})
    assert res1.status_code == 201
    room_code1 = res1.json()["data"]["room_code"]

    # 2. get all rooms
    response = await client.get("/api/v1/rooms")
    assert response.status_code == 200

    json_data = response.json()
    assert json_data["message"] == "the record has been retrieved successfully."
    data = json_data["data"]
    assert "rooms" in data
    assert "total_rooms" in data
    assert data["total_rooms"] >= 1

    room_item = next(r for r in data["rooms"] if r["room_code"] == room_code1)
    assert room_item["host_user_id"] == "usr_admin_host1"
    assert room_item["status"] == "not_started"
    assert room_item["host_connected"] is False
    assert room_item["guest_connected"] is False
    assert room_item["previous_match_results"] == {
        "host_wins": 0,
        "guest_wins": 0,
        "draws": 0,
    }


@pytest.mark.anyio
async def test_get_all_rooms_generic_exception(
    get_patched_configuration, create_client_and_cleanup, mocker
):
    client = create_client_and_cleanup
    mocker.patch(
        "square_ttthree.logic.rooms.room_manager.get_all_rooms",
        side_effect=RuntimeError("get all failure"),
    )
    response = await client.get("/api/v1/rooms")
    assert response.status_code == 500
    json_data = response.json()
    assert (
        json_data["message"]
        == "an internal server error occurred. please try again later."
    )
    assert "get all failure" in json_data["log"]


def test_ws_make_move_full_game_win(get_patched_configuration):
    from fastapi.testclient import TestClient

    from square_ttthree.main import app

    client = TestClient(app)
    res = client.post("/api/v1/room", json={"user_id": "usr_host123"})
    room_code = res.json()["data"]["room_code"]

    with client.websocket_connect(f"/ws/room/{room_code}") as host_ws:
        host_ws.send_json({"event": "JOIN_ROOM", "payload": {"user_id": "usr_host123"}})
        _ = host_ws.receive_json()

        with client.websocket_connect(f"/ws/room/{room_code}") as guest_ws:
            guest_ws.send_json(
                {"event": "JOIN_ROOM", "payload": {"user_id": "usr_guest456"}}
            )
            _ = guest_ws.receive_json()  # guest STATE_UPDATE
            _ = host_ws.receive_json()  # host STATE_UPDATE

            # Move 1: Host ('X') plays cell 0
            host_ws.send_json({"event": "MAKE_MOVE", "payload": {"cell_index": 0}})
            _ = guest_ws.receive_json()
            _ = host_ws.receive_json()

            # Move 2: Guest ('O') plays cell 3
            guest_ws.send_json({"event": "MAKE_MOVE", "payload": {"cell_index": 3}})
            _ = guest_ws.receive_json()
            _ = host_ws.receive_json()

            # Move 3: Host ('X') plays cell 1
            host_ws.send_json({"event": "MAKE_MOVE", "payload": {"cell_index": 1}})
            _ = guest_ws.receive_json()
            _ = host_ws.receive_json()

            # Move 4: Guest ('O') plays cell 4
            guest_ws.send_json({"event": "MAKE_MOVE", "payload": {"cell_index": 4}})
            _ = guest_ws.receive_json()
            _ = host_ws.receive_json()

            # Move 5: Host ('X') plays cell 2 -> Host completes top row [0, 1, 2]
            host_ws.send_json({"event": "MAKE_MOVE", "payload": {"cell_index": 2}})

            # Host receives STATE_UPDATE then GAME_OVER
            host_state_update = host_ws.receive_json()
            assert host_state_update["event"] == "STATE_UPDATE"
            assert host_state_update["payload"]["status"] == "ready"

            host_game_over = host_ws.receive_json()
            assert host_game_over["event"] == "GAME_OVER"
            assert host_game_over["payload"]["winner"] == "X"
            assert host_game_over["payload"]["winning_line"] == [0, 1, 2]
            assert host_game_over["payload"]["previous_match_results"] == {
                "host_wins": 1,
                "guest_wins": 0,
                "draws": 0,
            }


def test_ws_make_move_out_of_turn(get_patched_configuration):
    from fastapi.testclient import TestClient

    from square_ttthree.main import app

    client = TestClient(app)
    res = client.post("/api/v1/room", json={"user_id": "usr_host123"})
    room_code = res.json()["data"]["room_code"]

    with client.websocket_connect(f"/ws/room/{room_code}") as host_ws:
        host_ws.send_json({"event": "JOIN_ROOM", "payload": {"user_id": "usr_host123"}})
        _ = host_ws.receive_json()

        with client.websocket_connect(f"/ws/room/{room_code}") as guest_ws:
            guest_ws.send_json(
                {"event": "JOIN_ROOM", "payload": {"user_id": "usr_guest456"}}
            )
            _ = guest_ws.receive_json()
            _ = host_ws.receive_json()

            # Guest tries to move first when current_turn is 'X' (Host)
            guest_ws.send_json({"event": "MAKE_MOVE", "payload": {"cell_index": 0}})
            err_msg = guest_ws.receive_json()
            assert err_msg["event"] == "ERROR"
            assert err_msg["payload"]["code"] == "NOT_YOUR_TURN"


def test_ws_make_move_occupied_cell(get_patched_configuration):
    from fastapi.testclient import TestClient

    from square_ttthree.main import app

    client = TestClient(app)
    res = client.post("/api/v1/room", json={"user_id": "usr_host123"})
    room_code = res.json()["data"]["room_code"]

    with client.websocket_connect(f"/ws/room/{room_code}") as host_ws:
        host_ws.send_json({"event": "JOIN_ROOM", "payload": {"user_id": "usr_host123"}})
        _ = host_ws.receive_json()

        with client.websocket_connect(f"/ws/room/{room_code}") as guest_ws:
            guest_ws.send_json(
                {"event": "JOIN_ROOM", "payload": {"user_id": "usr_guest456"}}
            )
            _ = guest_ws.receive_json()
            _ = host_ws.receive_json()

            # Host plays cell 0
            host_ws.send_json({"event": "MAKE_MOVE", "payload": {"cell_index": 0}})
            _ = guest_ws.receive_json()
            _ = host_ws.receive_json()

            # Guest tries to play cell 0 as well
            guest_ws.send_json({"event": "MAKE_MOVE", "payload": {"cell_index": 0}})
            err_msg = guest_ws.receive_json()
            assert err_msg["event"] == "ERROR"
            assert err_msg["payload"]["code"] == "INVALID_MOVE"


def test_ws_request_rematch(get_patched_configuration):
    from fastapi.testclient import TestClient

    from square_ttthree.main import app

    client = TestClient(app)
    res = client.post("/api/v1/room", json={"user_id": "usr_host123"})
    room_code = res.json()["data"]["room_code"]

    with client.websocket_connect(f"/ws/room/{room_code}") as host_ws:
        host_ws.send_json({"event": "JOIN_ROOM", "payload": {"user_id": "usr_host123"}})
        _ = host_ws.receive_json()

        with client.websocket_connect(f"/ws/room/{room_code}") as guest_ws:
            guest_ws.send_json(
                {"event": "JOIN_ROOM", "payload": {"user_id": "usr_guest456"}}
            )
            _ = guest_ws.receive_json()
            _ = host_ws.receive_json()

            # Host plays cell 0
            host_ws.send_json({"event": "MAKE_MOVE", "payload": {"cell_index": 0}})
            _ = guest_ws.receive_json()
            _ = host_ws.receive_json()

            # Request rematch
            host_ws.send_json({"event": "REQUEST_REMATCH"})
            guest_rematch_msg = guest_ws.receive_json()
            assert guest_rematch_msg["event"] == "STATE_UPDATE"
            assert guest_rematch_msg["payload"]["board"] == [""] * 9
            assert guest_rematch_msg["payload"]["current_x_player"] == "guest"
            assert guest_rematch_msg["payload"]["current_turn"] == "X"
            assert guest_rematch_msg["payload"]["status"] == "match_ongoing"
