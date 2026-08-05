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
        assert msg["payload"]["your_role"] == "X"
        assert msg["payload"]["status"] == "not_started"


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
            assert guest_msg["payload"]["your_role"] == "O"
            assert guest_msg["payload"]["status"] == "active"

            host_msg = host_ws.receive_json()
            assert host_msg["event"] == "STATE_UPDATE"
            assert host_msg["payload"]["your_role"] == "X"
            assert host_msg["payload"]["status"] == "active"


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
