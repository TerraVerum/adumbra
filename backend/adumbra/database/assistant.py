from mongoengine import fields

from adumbra.database.mongo_shim import ShimmedDynamicDocument


class AssistantModel(ShimmedDynamicDocument):

    id = fields.SequenceField(primary_key=True)
    name = fields.StringField(required=True, unique=True)
    assistant_type = fields.StringField(required=True)
    parameters = fields.DictField(required=True)


__all__ = ["AssistantModel"]
