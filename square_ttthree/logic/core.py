from fastapi import status
from fastapi.responses import JSONResponse
from square_commons import get_api_output_in_standard_format

from square_ttthree.configuration import auto_logger
from square_ttthree.messages import messages
from square_ttthree.models.api.core import DummyRequestModelV0, DummyResponseModelV0


@auto_logger()
def logic_dummy_v0(dummy_model: DummyRequestModelV0):
    try:
        response_data = DummyResponseModelV0(dummy=dummy_model.dummy)
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
