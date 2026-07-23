import importlib
import os

import pytest
from httpx2 import ASGITransport, AsyncClient


@pytest.fixture(scope="session")
def anyio_backend():
    return "asyncio"


@pytest.fixture(scope="session")
def get_patched_configuration():
    def patched_join(*args):
        *rest, last = args
        if last == "config.ini":
            last = "config.testing.ini"
        elif last == "config.sample.ini":
            last = "config.testing.sample.ini"

        return original_join(*rest, last)

    original_join = os.path.join
    os.path.join = patched_join

    import square_ttthree.configuration

    importlib.reload(square_ttthree.configuration)
    config = square_ttthree.configuration

    yield config

    # cleanup
    os.path.join = original_join


@pytest.fixture(scope="session")
async def create_client_and_cleanup(get_patched_configuration):

    from square_ttthree.main import (
        app,
    )

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        yield client
