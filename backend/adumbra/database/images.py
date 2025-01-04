import json
import os
import typing as t

import cv2
import imantics as im
import numpy as np
from flask_login import current_user
from mongoengine import fields
from PIL import Image, ImageFile

from adumbra.database.categories import CategoryModel
from adumbra.database.datasets import DatasetModel
from adumbra.database.events import Event, SessionEvent
from adumbra.database.mongo_shim import ShimmedDynamicDocument

ImageFile.LOAD_TRUNCATED_IMAGES = True


class ImageModel(ShimmedDynamicDocument):

    COCO_PROPERTIES = [
        "id",
        "width",
        "height",
        "file_name",
        "path",
        "license",
        "flickr_url",
        "coco_url",
        "date_captured",
        "dataset_id",
    ]

    # -- Contants
    THUMBNAIL_DIRECTORY = ".thumbnail"
    PATTERN = (
        ".gif",
        ".png",
        ".jpg",
        ".jpeg",
        ".bmp",
        ".tif",
        ".tiff",
        ".GIF",
        ".PNG",
        ".JPG",
        ".JPEG",
        ".BMP",
        ".TIF",
        ".TIFF",
    )

    # Set maximum thumbnail size (h x w) to use on dataset page
    MAX_THUMBNAIL_DIM = (1024, 1024)

    # -- Private
    _dataset = None

    # -- Database
    id = fields.SequenceField(primary_key=True)
    dataset_id = fields.IntField(required=True)
    category_ids = fields.ListField(default=[])

    # Absolute path to image file
    path = fields.StringField(required=True, unique=True)
    width = fields.IntField(required=True)
    height = fields.IntField(required=True)
    file_name = fields.StringField()

    # True if the image is annotated
    annotated = fields.BooleanField(default=False)
    # Poeple currently annotation the image
    annotating = fields.ListField(default=[])
    num_annotations = fields.IntField(default=0)

    thumbnail_url = fields.StringField()
    image_url = fields.StringField()
    coco_url = fields.StringField()
    date_captured = fields.DateTimeField()

    metadata = fields.DictField()
    license = fields.IntField()

    deleted = fields.BooleanField(default=False)
    deleted_date = fields.DateTimeField()

    milliseconds = fields.IntField(default=0)
    events = fields.EmbeddedDocumentListField(Event)
    regenerate_thumbnail = fields.BooleanField(default=False)

    @classmethod
    def create_from_path(cls, path, dataset_id=None):

        pil_image = Image.open(path)

        image = cls()
        image.file_name = os.path.basename(path)
        image.path = path
        image.width = pil_image.size[0]
        image.height = pil_image.size[1]
        image.regenerate_thumbnail = True

        if dataset_id is not None:
            image.dataset_id = dataset_id
        else:
            # Get dataset name from path
            folders = path.split("/")
            i = folders.index("datasets")
            dataset_name = folders[i + 1]

            dataset = DatasetModel.objects(name=dataset_name).first()
            if dataset is not None:
                image.dataset_id = dataset.id

        pil_image.close()

        return image

    def delete(self, *args, **kwargs):
        self.thumbnail_delete()
        AnnotationModel.objects(image_id=self.id).delete()
        return super(ImageModel, self).delete(*args, **kwargs)

    def segmented(self):
        """
        Generates segmented image
        """
        pil_image = self.generate_thumbnail()
        pil_image = pil_image.convert("RGB")

        self.update(is_modified=False)
        return pil_image

    def thumbnail(self):
        """
        Generates (if required) thumbnail
        """

        thumbnail_path = self.thumbnail_path()

        if self.regenerate_thumbnail:

            pil_image = self.generate_thumbnail()
            pil_image = pil_image.convert("RGB")

            # Resize image to fit in MAX_THUMBNAIL_DIM envelope as necessary
            pil_image.thumbnail((self.MAX_THUMBNAIL_DIM[1], self.MAX_THUMBNAIL_DIM[0]))

            # Save as a jpeg to improve loading time
            # (note file extension will not match but allows for backwards compatibility)
            pil_image.save(
                thumbnail_path, "JPEG", quality=80, optimize=True, progressive=True
            )

            self.update(is_modified=False)
            return pil_image
        return None

    def open_thumbnail(self):
        """
        Return thumbnail
        """
        thumbnail_path = self.thumbnail_path()
        # check if thumbnail exists
        if not os.path.exists(thumbnail_path):
            return None
        return Image.open(thumbnail_path)

    def thumbnail_path(self):
        folders = self.path.split("/")
        folders.insert(len(folders) - 1, self.THUMBNAIL_DIRECTORY)

        path = "/" + os.path.join(*folders)
        directory = os.path.dirname(path)

        if not os.path.exists(directory):
            os.makedirs(directory)

        return path

    def thumbnail_delete(self):
        path = self.thumbnail_path()
        if os.path.isfile(path):
            os.remove(path)

    def generate_thumbnail(self):
        image = self().draw(color_by_category=True, bbox=False)
        return Image.fromarray(image)

    def flag_thumbnail(self, flag=True):
        """
        Toggles values to regenerate thumbnail on next thumbnail request
        """
        if self.regenerate_thumbnail != flag:
            self.update(regenerate_thumbnail=flag)

    def copy_annotations(self, annotations):
        """
        Creates a copy of the annotations for this image
        :param annotations: QuerySet of annotation models
        :return: number of annotations
        """
        annotations = annotations.filter(width=self.width, height=self.height).exclude(
            "events"
        )

        for annotation in annotations:
            if annotation.area > 0 or len(annotation.keypoints) > 0:
                clone = annotation.clone()

                clone.dataset_id = self.dataset_id
                clone.image_id = self.id

                clone.save(copy=True)

        return annotations.count()

    @property
    def dataset(self):
        if self._dataset is None:
            self._dataset = DatasetModel.objects(id=self.dataset_id).first()
        return self._dataset

    def __call__(self):

        image = im.Image.from_path(self.path)
        for annotation in AnnotationModel.objects(
            image_id=self.id, deleted=False
        ).all():
            if not annotation.is_empty():
                image.add(annotation())

        return image

    def can_delete(self, user):
        return user.can_delete(self.dataset)

    def can_download(self, user):
        return user.can_download(self.dataset)

    # TODO: Fix why using the functions throws an error
    def permissions(self, user):
        del user
        return {"delete": True, "download": True}

    def add_event(self, e):
        u = {
            "push__events": e,
        }
        if isinstance(e, SessionEvent):
            u["inc__milliseconds"] = e.milliseconds

        self.update(**u)


# TODO: determine how to split into own file without circular imports
class AnnotationModel(ShimmedDynamicDocument):

    COCO_PROPERTIES = [
        "id",
        "image_id",
        "category_id",
        "segmentation",
        "iscrowd",
        "color",
        "area",
        "bbox",
        "metadata",
        "keypoints",
        "isbbox",
    ]

    id = fields.SequenceField(primary_key=True)
    image_id = fields.IntField(required=True)
    category_id = fields.IntField(required=True)
    dataset_id = fields.IntField()

    segmentation = fields.ListField(default=[])
    area = fields.IntField(default=0)
    bbox = fields.ListField(default=[0, 0, 0, 0])
    iscrowd = fields.BooleanField(default=False)
    isbbox = fields.BooleanField(default=False)

    creator = fields.StringField(required=True)
    width = fields.IntField()
    height = fields.IntField()

    color = fields.StringField()

    keypoints = fields.ListField(default=[])

    metadata = fields.DictField(default={})
    paper_object = fields.ListField(default=[])

    deleted = fields.BooleanField(default=False)
    deleted_date = fields.DateTimeField()

    milliseconds = fields.IntField(default=0)
    events = fields.EmbeddedDocumentListField(Event)

    def __init__(self, image_id=None, **data):

        if image_id is not None:
            image = ImageModel.objects(id=image_id).first()

            if image is not None:
                data["image_id"] = image_id
                data["width"] = image.width
                data["height"] = image.height
                data["dataset_id"] = image.dataset_id

        super(AnnotationModel, self).__init__(**data)

    def save(self, *args, copy=False, **kwargs):

        if self.dataset_id and not copy:
            dataset = DatasetModel.objects(id=self.dataset_id).first()

            if dataset is not None:
                self.metadata = dataset.default_annotation_metadata.copy()

        if self.color is None:
            self.color = im.Color.random().hex

        if not self.creator:
            self.creator = current_user.username if current_user else "system"

        return super(AnnotationModel, self).save(*args, **kwargs)

    def is_empty(self):
        return len(self.segmentation) == 0 or self.area == 0

    def mask(self):
        """Returns binary mask of annotation"""
        mask = np.zeros((self.height or 0, self.width or 0))
        pts = [
            np.array(anno).reshape(-1, 2).round().astype(int)
            for anno in self.segmentation
        ]
        mask = cv2.fillPoly(mask, pts, t.cast(cv2.typing.Scalar, 1))
        return mask

    def clone(self):
        """Creates a clone"""
        create = json.loads(self.to_json())
        del create["_id"]

        return AnnotationModel(**create)

    def __call__(self):

        category = CategoryModel.objects(id=self.category_id).first()
        if category:
            category = category()

        data = {
            "image": None,
            "category": category,
            "color": self.color,
            "polygons": self.segmentation,
            "width": self.width,
            "height": self.height,
            "metadata": self.metadata,
        }

        return im.Annotation(**data)

    def add_event(self, e):
        self.update(push__events=e)


__all__ = ["ImageModel"]
