import os
from importlib.metadata import version

from fastapi import FastAPI, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from square_commons import get_api_output_in_standard_format

from square_ttthree.config import (
    ALLOW_ORIGINS,
    HOST_IP,
    HOST_PORT,
    MODULE_NAME,
    SSL_CRT_FILE_PATH,
    SSL_KEY_FILE_PATH,
    auto_logger,
    logger,
)

app = FastAPI(
    title=MODULE_NAME,
    version=version(MODULE_NAME),
)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=ALLOW_ORIGINS,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
@auto_logger()
async def root():
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content=get_api_output_in_standard_format(log=MODULE_NAME),
    )


if __name__ == "__main__":
    try:
        import uvicorn

        if os.path.exists(SSL_CRT_FILE_PATH) and os.path.exists(SSL_KEY_FILE_PATH):
            uvicorn.run(
                app,
                host=HOST_IP,
                port=HOST_PORT,
                ssl_certfile=SSL_CRT_FILE_PATH,
                ssl_keyfile=SSL_KEY_FILE_PATH,
            )
        else:
            uvicorn.run(
                app,
                host=HOST_IP,
                port=HOST_PORT,
            )
    except Exception as exc:
        logger.critical(exc, exc_info=True)
