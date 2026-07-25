"""
contains pydantic models representing request/response schemas for api endpoints.
each module in this subpackage corresponds to a separate router.

naming convention:
- models for incoming request payloads must end with 'RequestModel' (e.g. DummyRequestModel).
- models for outgoing response payloads must end with 'ResponseModel' (e.g. RoomCreateResponseModel).

usage requirement:
- all outgoing api response payloads must be validated by instantiating the corresponding
  ResponseModel class first, then converted via `.model_dump()`, passed into `get_api_output_in_standard_format`
  using the `data` parameter, and finally returned to the end user.
"""

