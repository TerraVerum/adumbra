from flask import Blueprint
from flask_restx import Api

from adumbra.config import CONFIG
from adumbra.ia.api.models import api as ns_models

# Create /api/ space
blueprint = Blueprint("api", __name__, url_prefix="/api")

api = Api(
    blueprint,
    title=CONFIG.name,
    version=CONFIG.version,
)

# Remove default namespace
api.namespaces.pop(0)

# Setup API namespaces
api.add_namespace(ns_models)
