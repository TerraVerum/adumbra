import datetime

from flask_login import UserMixin
from mongoengine import DynamicDocument, Q, fields

from adumbra.database.annotations import AnnotationModel
from adumbra.database.categories import CategoryModel
from adumbra.database.datasets import DatasetModel
from adumbra.database.images import ImageModel


class UserModel(DynamicDocument, UserMixin):

    password = fields.StringField(required=True)
    username = fields.StringField(max_length=25, required=True, unique=True)
    email = fields.StringField(max_length=30)

    name = fields.StringField()
    online = fields.BooleanField(default=False)
    last_seen = fields.DateTimeField()

    is_admin = fields.BooleanField(default=False)

    preferences = fields.DictField(default={})
    permissions = fields.ListField(default=[])

    # meta = {'allow_inheritance': True}

    @property
    def datasets(self):
        self._update_last_seen()

        if self.is_admin:
            return DatasetModel.objects

        return DatasetModel.objects(
            Q(owner=self.username) | Q(users__contains=self.username)
        )

    @property
    def categories(self):
        self._update_last_seen()

        if self.is_admin:
            return CategoryModel.objects

        dataset_ids = self.datasets.distinct("categories")
        return CategoryModel.objects(Q(id__in=dataset_ids) | Q(creator=self.username))

    @property
    def images(self):
        self._update_last_seen()

        if self.is_admin:
            return ImageModel.objects

        dataset_ids = self.datasets.distinct("id")
        return ImageModel.objects(dataset_id__in=dataset_ids)

    @property
    def annotations(self):
        self._update_last_seen()

        if self.is_admin:
            return AnnotationModel.objects

        image_ids = self.images.distinct("id")
        return AnnotationModel.objects(image_id__in=image_ids)

    def can_view(self, model):
        if model is None:
            return False

        return model.can_view(self)

    def can_download(self, model):
        if model is None:
            return False

        return model.can_download(self)

    def can_delete(self, model):
        if model is None:
            return False
        return model.can_delete(self)

    def can_edit(self, model):
        if model is None:
            return False

        return model.can_edit(self)

    def _update_last_seen(self):
        self.update(last_seen=datetime.datetime.utcnow())


__all__ = ["UserModel"]
