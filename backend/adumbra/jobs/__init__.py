import logging

from fastapi.middleware.cors import CORSMiddleware

from .api import app

fastapi_logger = logging.getLogger("fastapi")
module_logger = logging.getLogger("jobs")

# TODO: Lock down middleware later
app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
