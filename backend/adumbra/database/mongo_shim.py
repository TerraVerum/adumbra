from mongoengine import DynamicDocument, QuerySet


class ShimmedDynamicDocument(DynamicDocument):
    objects: QuerySet
