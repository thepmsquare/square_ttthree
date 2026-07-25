"""
all functions bound to endpoints must start with prefix api_ and
perform only routing and error handling without any endpoint logic.
they must call a corresponding logic_ function and return its response.
this file acts solely as an index of all endpoints for the router.
"""

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import JSONResponse
from square_commons.api_utils import StandardResponse, get_api_output_in_standard_format

from square_ttthree.configuration import auto_logger, logger
from square_ttthree.logic.rooms import logic_create_room, logic_get_room
from square_ttthree.messages import messages
from square_ttthree.models.api.rooms import (
    RoomCreateResponseModel,
    RoomGetResponseModel,
)

router = APIRouter(tags=["rooms"], prefix="/api/v1")


@router.post(
    "/room",
    status_code=status.HTTP_201_CREATED,
    response_model=StandardResponse[RoomCreateResponseModel],
)
@auto_logger()
async def api_create_room():
    try:
        return logic_create_room()
    except HTTPException as he:
        logger.error(he, exc_info=True)
        return JSONResponse(status_code=he.status_code, content=he.detail)
    except Exception as e:
        logger.logger.error(e, exc_info=True)
        output_content = get_api_output_in_standard_format(
            message=messages["GENERIC_500"], log=str(e)
        )
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content=output_content
        )


@router.get(
    "/room/{room_code}",
    status_code=status.HTTP_200_OK,
    response_model=StandardResponse[RoomGetResponseModel],
)
@auto_logger()
async def api_get_room(room_code: str):
    try:
        return logic_get_room(room_code)
    except HTTPException as he:
        logger.error(he, exc_info=True)
        return JSONResponse(status_code=he.status_code, content=he.detail)
    except Exception as e:
        logger.logger.error(e, exc_info=True)
        output_content = get_api_output_in_standard_format(
            message=messages["GENERIC_500"], log=str(e)
        )
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content=output_content
        )
