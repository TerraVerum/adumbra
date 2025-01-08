# pylint: disable=wrong-import-position
# pylint: disable=wrong-import-order
# monkey patching must be done before importing the remaining modules
# https://eventlet.readthedocs.io/en/latest/patching.html#monkeypatching-the-standard-library

import logging

from fastapi.middleware.cors import CORSMiddleware

from adumbra.config import CONFIG
from adumbra.database import create_from_json
from adumbra.ia.api import app

gunicorn_logger = logging.getLogger("gunicorn.error")
fastapi_logger = logging.getLogger("fastapi")
fastapi_logger.handlers = gunicorn_logger.handlers
fastapi_logger.setLevel(gunicorn_logger.level)

origins = [
    "http://ia:6001",
    "http://webserver:8080",
    "http://localhost:8080",
    "http://localhost:6001",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

if CONFIG.initialize_from_file:
    create_from_json(CONFIG.initialize_from_file)
