from mongoengine import DynamicDocument, QuerySet


class ShimmedDynamicDocument(DynamicDocument):
    """Provides type hinting on `objects`, nothing more."""

    meta = {"abstract": True}
    objects: QuerySet
