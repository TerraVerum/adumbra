import datetime

from mongoengine import fields

from adumbra.database.mongo_shim import ShimmedDynamicDocument


class ExportModel(ShimmedDynamicDocument):

    id = fields.SequenceField(primary_key=True)
    dataset_id = fields.IntField(required=True)
    path = fields.StringField(required=True)
    tags = fields.ListField(default=[])
    categories = fields.ListField(default=[])
    created_at = fields.DateTimeField(default=datetime.datetime.utcnow)

    def get_file(self):
        return


__all__ = ["ExportModel"]
