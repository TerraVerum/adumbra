import restx_monkey as monkey
from flask import Blueprint
from flask_restx import Api

from adumbra.config import Config
from adumbra.ia.api.models import api as ns_models

monkey.patch_restx()

# Create /api/ space
blueprint = Blueprint("api", __name__, url_prefix="/api")

api = Api(
    blueprint,
    title=Config.NAME,
    version=Config.VERSION,
)

# Remove default namespace
api.namespaces.pop(0)

# Setup API namespaces
api.add_namespace(ns_models)
