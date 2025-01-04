import os

from flask_login import current_user
from mongoengine import fields

from adumbra.config import CONFIG
from adumbra.database.mongo_shim import ShimmedDynamicDocument


class DatasetModel(ShimmedDynamicDocument):

    id = fields.SequenceField(primary_key=True)
    name = fields.StringField(required=True, unique=True)
    directory = fields.StringField()
    thumbnails = fields.StringField()
    categories = fields.ListField(default=[])

    owner = fields.StringField(required=True)
    users = fields.ListField(default=[])

    annotate_url = fields.StringField(default="")

    default_annotation_metadata = fields.DictField(default={})

    deleted = fields.BooleanField(default=False)
    deleted_date = fields.DateTimeField()

    def save(self, *args, **kwargs):

        directory = os.path.join(CONFIG.dataset_directory, str(self.name) + "/")
        os.makedirs(directory, mode=0o777, exist_ok=True)

        self.directory = directory
        self.owner = current_user.username if current_user else "system"

        return super(DatasetModel, self).save(*args, **kwargs)

    def get_users(self):
        from adumbra.database.users import UserModel

        members = self.users
        members.append(self.owner)

        return UserModel.objects(username__in=members).exclude(
            "password", "id", "preferences"
        )

    def is_owner(self, user):

        if user.is_admin:
            return True

        return user.username.lower() == self.owner.lower()

    def can_download(self, user):
        return self.is_owner(user)

    def can_delete(self, user):
        return self.is_owner(user)

    def can_share(self, user):
        return self.is_owner(user)

    def can_generate(self, user):
        return self.is_owner(user)

    def can_edit(self, user):
        return user.username in self.users or self.is_owner(user)

    def permissions(self, user):
        return {
            "owner": self.is_owner(user),
            "edit": self.can_edit(user),
            "share": self.can_share(user),
            "generate": self.can_generate(user),
            "delete": self.can_delete(user),
            "download": self.can_download(user),
        }


__all__ = ["DatasetModel"]
