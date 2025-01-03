import datetime

from mongoengine import fields, DynamicDocument, QuerySet


class ExportModel(DynamicDocument):
    objects: QuerySet

    id = fields.SequenceField(primary_key=True)
    dataset_id = fields.IntField(required=True)
    path = fields.StringField(required=True)
    tags = fields.ListField(default=[])
    categories = fields.ListField(default=[])
    created_at = fields.DateTimeField(default=datetime.datetime.utcnow)

    def get_file(self):
        return


__all__ = ["ExportModel"]
