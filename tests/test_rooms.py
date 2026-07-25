import pytest


@pytest.mark.anyio
async def test_create_room(get_patched_configuration, create_client_and_cleanup):
    client = create_client_and_cleanup
    response = await client.post("/api/v1/room")
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
    create_response = await client.post("/api/v1/room")
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
    create_response = await client.post("/api/v1/room")
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
