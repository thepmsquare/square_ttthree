import pytest
from square_commons import get_api_output_in_standard_format


@pytest.mark.anyio
async def test_read_main(get_patched_configuration, create_client_and_cleanup):

    client = create_client_and_cleanup
    response = await client.get("/")
    assert response.status_code == 200
    assert response.json() == get_api_output_in_standard_format(
        log=get_patched_configuration.MODULE_NAME
    )
