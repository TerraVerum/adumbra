from mongoengine import fields

from adumbra.config import CONFIG
from adumbra.database.mongo_shim import ShimmedDynamicDocument


class AssistantDBModel(ShimmedDynamicDocument):

    id = fields.SequenceField(primary_key=True)
    name = fields.StringField(required=True, unique=True)
    assistant_type = fields.StringField(required=True)
    parameters = fields.DictField(default=dict)

    @classmethod
    def ensure_defaults_available(cls):
        if not CONFIG.connect_to_mongo:
            return
        if not cls.objects(name="zim").first():
            cls(name="zim", assistant_type="zim", parameters={}).save()
        if not cls.objects(name="sam2").first():
            cls(name="sam2", assistant_type="sam2", parameters={}).save()


__all__ = ["AssistantDBModel"]
