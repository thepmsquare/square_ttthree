import random
import string
from typing import Dict, Optional

from fastapi import status
from fastapi.responses import JSONResponse
from square_commons.api_utils import get_api_output_in_standard_format

from square_ttthree.configuration import auto_logger
from square_ttthree.messages import messages
from square_ttthree.models.api.rooms import (
    RoomCreateResponseModel,
    RoomGetResponseModel,
)
from square_ttthree.models.internal.rooms import GameRoom, RoomStatus


class RoomManager:
    def __init__(self):
        self._rooms: Dict[str, GameRoom] = {}

    def create_room(self) -> GameRoom:
        """
        generates a unique 4-letter alphanumeric room code in uppercase
        and stores it in-memory.
        """
        while True:
            code = "".join(random.choices(string.ascii_uppercase + string.digits, k=4))
            if code not in self._rooms:
                break

        room = GameRoom(room_code=code)
        self._rooms[code] = room
        return room

    def get_room(self, room_code: str) -> Optional[GameRoom]:
        """
        retrieves a room by its code, case-insensitively.
        """
        return self._rooms.get(room_code.upper())


# singleton instance for in-memory room management
room_manager = RoomManager()


@auto_logger()
def logic_create_room() -> JSONResponse:
    try:
        room = room_manager.create_room()
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
