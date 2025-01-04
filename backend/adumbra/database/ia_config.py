import os

from flask_login import current_user
from mongoengine import fields

from adumbra.config import CONFIG
from adumbra.database.mongo_shim import ShimmedDynamicDocument


class IAConfigModel(ShimmedDynamicDocument):

    id = fields.SequenceField(primary_key=True)
    name = fields.StringField(required=True, unique=True)
    model_type = fields.StringField(required=True)
    parameters = fields.DictField(required=True)


__all__ = ["IAConfigModel"]
