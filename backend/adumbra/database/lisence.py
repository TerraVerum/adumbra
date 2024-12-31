from mongoengine import DynamicDocument, fields


class LicenseModel(DynamicDocument):
    id = fields.SequenceField(primary_key=True)
    name = fields.StringField()
    url = fields.StringField()


__all__ = ["LicenseModel"]
