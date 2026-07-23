import importlib
import os

import pytest
from fastapi.testclient import TestClient


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
def create_client_and_cleanup(get_patched_configuration):

    from square_ttthree.main import (
        app,
    )

    client = TestClient(app)
    yield client
