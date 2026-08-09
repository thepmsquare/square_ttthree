import random
import string
from typing import Dict, Optional

from fastapi import WebSocket, WebSocketDisconnect, status
from fastapi.responses import JSONResponse
from square_commons.api_utils import get_api_output_in_standard_format

from square_ttthree.configuration import auto_logger
from square_ttthree.messages import messages
from square_ttthree.models.api.rooms import (
    RoomCreateRequestModel,
    RoomCreateResponseModel,
    RoomGetAllResponseModel,
    RoomGetResponseModel,
    RoomStateModel,
    WSErrorPayload,
    WSStateUpdatePayload,
)
from square_ttthree.models.internal.rooms import GameRoom, RoomStatus


class RoomManager:
    def __init__(self):
        self._rooms: Dict[str, GameRoom] = {}

    def create_room(self, host_user_id: str) -> GameRoom:
        """
        generates a unique 4-letter alphanumeric room code in uppercase
        and stores it in-memory along with host_user_id.
        """
        while True:
            code = "".join(random.choices(string.ascii_uppercase + string.digits, k=4))
            if code not in self._rooms:
                break

        room = GameRoom(room_code=code, host_user_id=host_user_id)
        self._rooms[code] = room
        return room

    def get_room(self, room_code: str) -> Optional[GameRoom]:
        """
        retrieves a room by its code, case-insensitively.
        """
        return self._rooms.get(room_code.upper())

    def get_all_rooms(self) -> Dict[str, GameRoom]:
        """
        retrieves all active rooms in-memory.
        """
        return self._rooms


# singleton instance for in-memory room management
room_manager = RoomManager()


async def broadcast_state_update(room: GameRoom) -> None:
    """
    broadcasts state_update to all connected active sockets in the room.
    """
    host_connected = bool(room.sockets.get(room.host_user_id))
    guest_connected = bool(room.guest_user_id and room.sockets.get(room.guest_user_id))

    payload = WSStateUpdatePayload(
        room_code=room.room_code,
        status=room.status.value,
        host_user_id=room.host_user_id,
        guest_user_id=room.guest_user_id,
        current_x_player=room.current_x_player.value,
        created_at=room.created_at,
        host_connected=host_connected,
        guest_connected=guest_connected,
    )
    message = {
        "event": "STATE_UPDATE",
        "payload": payload.model_dump(),
    }

    for user_id, socket_list in list(room.sockets.items()):
        disconnected_sockets = []
        for socket in list(socket_list):
            try:
                await socket.send_json(message)
            except Exception:
                disconnected_sockets.append(socket)

        for sock in disconnected_sockets:
            if sock in socket_list:
                socket_list.remove(sock)
        if not socket_list:
            room.sockets.pop(user_id, None)


@auto_logger()
def logic_create_room(param: RoomCreateRequestModel) -> JSONResponse:
    try:
        room = room_manager.create_room(host_user_id=param.user_id)
        response_data = RoomCreateResponseModel(room_code=room.room_code)
        output_content = get_api_output_in_standard_format(
            message=messages["CREATE_SUCCESSFUL"],
            data=response_data.model_dump(),
            as_dict=False,
        )
        return JSONResponse(
            status_code=status.HTTP_201_CREATED,
            content=output_content.model_dump(),
        )
    except Exception:
        raise


@auto_logger()
def logic_get_room(room_code: str) -> JSONResponse:
    try:
        room = room_manager.get_room(room_code)
        if not room:
            output_content = get_api_output_in_standard_format(
                message=messages["GENERIC_404"],
                log=f"{room_code} not found.",
                as_dict=False,
            )
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content=output_content.model_dump(),
            )

        response_data = RoomGetResponseModel(
            room_code=room.room_code,
            is_joinable=(room.status == RoomStatus.NOT_STARTED),
        )
        output_content = get_api_output_in_standard_format(
            message=messages["READ_SUCCESSFUL"],
            data=response_data.model_dump(),
            as_dict=False,
        )
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=output_content.model_dump(),
        )
    except Exception:
        raise


@auto_logger()
def logic_get_all_rooms() -> JSONResponse:
    try:
        all_rooms = room_manager.get_all_rooms()
        room_models = []
        for room in all_rooms.values():
            host_conn = bool(room.sockets.get(room.host_user_id))
            guest_conn = bool(
                room.guest_user_id and room.sockets.get(room.guest_user_id)
            )
            total_socks = sum(len(socks) for socks in room.sockets.values())
            room_models.append(
                RoomStateModel(
                    room_code=room.room_code,
                    status=room.status.value,
                    host_user_id=room.host_user_id,
                    guest_user_id=room.guest_user_id,
                    current_x_player=room.current_x_player.value,
                    created_at=room.created_at,
                    host_connected=host_conn,
                    guest_connected=guest_conn,
                    total_connected_sockets=total_socks,
                )
            )

        response_data = RoomGetAllResponseModel(
            rooms=room_models,
            total_rooms=len(room_models),
        )
        output_content = get_api_output_in_standard_format(
            message=messages["READ_SUCCESSFUL"],
            data=response_data.model_dump(),
            as_dict=False,
        )
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=output_content.model_dump(),
        )
    except Exception:
        raise


def update_room_status(room: GameRoom) -> None:
    """
    updates room status deterministically based on player connectivity and explicit leave state.
    """
    host_connected = bool(room.sockets.get(room.host_user_id))
    guest_connected = bool(room.guest_user_id and room.sockets.get(room.guest_user_id))
    total_connected = (1 if host_connected else 0) + (1 if guest_connected else 0)

    if total_connected == 0:
        room.status = RoomStatus.EMPTY_LOBBY
    elif room.guest_user_id is None:
        if host_connected:
            room.status = RoomStatus.NOT_STARTED
        else:
            room.status = RoomStatus.EMPTY_LOBBY
    else:
        if total_connected == 1:
            if room.explicit_leave:
                room.status = RoomStatus.MISSING_PLAYER
            else:
                room.status = RoomStatus.PAUSED
        elif total_connected == 2:
            if room.status == RoomStatus.MATCH_ONGOING:
                room.status = RoomStatus.MATCH_ONGOING
            else:
                room.status = RoomStatus.READY


@auto_logger()
async def logic_ws_room(websocket: WebSocket, room_code: str) -> None:
    await websocket.accept()
    room = room_manager.get_room(room_code)
    if not room:
        error_msg = {
            "event": "ERROR",
            "payload": WSErrorPayload(
                code="ROOM_NOT_FOUND",
                message="The requested room code does not exist or has expired.",
            ).model_dump(),
        }
        await websocket.send_json(error_msg)
        await websocket.close(code=4004)
        return

    user_id: Optional[str] = None
    try:
        while True:
            data = await websocket.receive_json()
            event = data.get("event")
            payload = data.get("payload", {})

            if event == "JOIN_ROOM":
                incoming_user_id = payload.get("user_id")
                if not incoming_user_id:
                    error_msg = {
                        "event": "ERROR",
                        "payload": WSErrorPayload(
                            code="INVALID_PAYLOAD",
                            message="user_id is required in JOIN_ROOM payload.",
                        ).model_dump(),
                    }
                    await websocket.send_json(error_msg)
                    continue

                if incoming_user_id == room.host_user_id:
                    user_id = incoming_user_id
                elif (
                    room.guest_user_id is None and incoming_user_id != room.host_user_id
                ):
                    user_id = incoming_user_id
                    room.guest_user_id = user_id
                elif incoming_user_id == room.guest_user_id:
                    user_id = incoming_user_id
                else:
                    error_msg = {
                        "event": "ERROR",
                        "payload": WSErrorPayload(
                            code="ROOM_FULL",
                            message="This room already has 2 active players.",
                        ).model_dump(),
                    }
                    await websocket.send_json(error_msg)
                    await websocket.close(code=4003)
                    return

                if user_id not in room.sockets:
                    room.sockets[user_id] = []
                if websocket not in room.sockets[user_id]:
                    room.sockets[user_id].append(websocket)

                update_room_status(room)
                await broadcast_state_update(room)
            elif event == "LEAVE_ROOM":
                if user_id and user_id in room.sockets:
                    if websocket in room.sockets[user_id]:
                        room.sockets[user_id].remove(websocket)
                    if not room.sockets[user_id]:
                        room.sockets.pop(user_id, None)

                room.explicit_leave = True
                update_room_status(room)
                await broadcast_state_update(room)
                await websocket.close()
                return
    except WebSocketDisconnect:
        if user_id and user_id in room.sockets:
            if websocket in room.sockets[user_id]:
                room.sockets[user_id].remove(websocket)
            if not room.sockets[user_id]:
                room.sockets.pop(user_id, None)
        update_room_status(room)
        await broadcast_state_update(room)
    except Exception:
        if user_id and user_id in room.sockets:
            if websocket in room.sockets[user_id]:
                room.sockets[user_id].remove(websocket)
            if not room.sockets[user_id]:
                room.sockets.pop(user_id, None)
        update_room_status(room)
        await broadcast_state_update(room)
