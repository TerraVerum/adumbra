import os

from flask_login import current_user
from mongoengine import fields

from adumbra.config import CONFIG
from adumbra.database.mongo_shim import ShimmedDynamicDocument
from adumbra.database.tasks import TaskModel


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

    def import_coco(self, coco_json):

        from adumbra.workers.tasks import import_annotations

        task = TaskModel(
            name=f"Import COCO format into {self.name}",
            dataset_id=self.id,
            group="Annotation Import",
        )
        task.save()

        cel_task = import_annotations.delay(task.id, self.id, coco_json)

        return {"celery_id": cel_task.id, "id": task.id, "name": task.name}

    def export_coco(self, categories=None, style="COCO", with_empty_images=False):

        from adumbra.workers.tasks import export_annotations

        if categories is None or len(categories) == 0:
            categories = self.categories

        task = TaskModel(
            name=f"Exporting {self.name} into {style} format",
            dataset_id=self.id,
            group="Annotation Export",
        )
        task.save()

        cel_task = export_annotations.delay(
            task.id, self.id, categories, with_empty_images
        )

        return {"celery_id": cel_task.id, "id": task.id, "name": task.name}

    def scan(self):

        from adumbra.workers.tasks import scan_dataset

        task = TaskModel(
            name=f"Scanning {self.name} for new images",
            dataset_id=self.id,
            group="Directory Image Scan",
        )
        task.save()

        cel_task = scan_dataset.delay(task.id, self.id)

        return {"celery_id": cel_task.id, "id": task.id, "name": task.name}

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
