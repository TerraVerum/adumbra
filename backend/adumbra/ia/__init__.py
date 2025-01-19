import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.routing import APIRoute

from adumbra.config import CONFIG
from adumbra.database import create_from_json
from adumbra.ia.api import app

fastapi_logger = logging.getLogger("fastapi")
module_logger = logging.getLogger("adumbra.ia")

for logger in [fastapi_logger, module_logger]:
    logger.setLevel(CONFIG.log_level)
    if not logger.handlers:
        logger.addHandler(logging.StreamHandler())


origins = [
    "http://ia:6001",
    "http://webserver:8080",
    "http://localhost:8080",
    "http://localhost:6001",
]


def use_route_names_as_operation_ids(app: FastAPI) -> None:
    """
    Simplify operation IDs so that generated API clients have simpler function
    names.

    Should be called only after all routes have been added.
    """
    for route in app.routes:
        if isinstance(route, APIRoute):
            route.operation_id = route.name


app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
use_route_names_as_operation_ids(app)

if CONFIG.initialize_from_file:
    create_from_json(CONFIG.initialize_from_file)
