from fastapi import APIRouter, HTTPException, status
from fastapi.responses import JSONResponse
from square_commons.api_utils import StandardResponse, get_api_output_in_standard_format

from square_ttthree.configuration import auto_logger, logger
from square_ttthree.logic.core import logic_dummy_v0
from square_ttthree.messages import messages
from square_ttthree.models.core import DummyModelV0

router = APIRouter(
    tags=["core"],
)


@router.post(
    "/dummy/v0",
    status_code=status.HTTP_201_CREATED,
    response_model=StandardResponse[DummyModelV0],
)
@auto_logger()
async def api_dummy_v0(dummy_model: DummyModelV0):
    try:
        return logic_dummy_v0(dummy_model)
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
