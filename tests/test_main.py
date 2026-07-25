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


@pytest.mark.anyio
async def test_dummy_v0(get_patched_configuration, create_client_and_cleanup):
    client = create_client_and_cleanup
    payload = {"dummy": 42}
    response = await client.post("/dummy/v0", json=payload)
    assert response.status_code == 201
    
    json_data = response.json()
    assert json_data["message"] == "the record has been created successfully."
    assert json_data["data"] == {"dummy": 42}

