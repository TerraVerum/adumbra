import json
import typing as t

from mongoengine import DynamicDocument, QuerySet, connect, fields
from mongoengine.base import BaseField
from mongoengine.queryset.manager import queryset_manager

from adumbra.config import Config
from adumbra.database.annotations import *
from adumbra.database.categories import *
from adumbra.database.datasets import *
from adumbra.database.events import *
from adumbra.database.exports import *
from adumbra.database.images import *
from adumbra.database.lisence import *
from adumbra.database.tasks import *
from adumbra.database.users import *

FieldBase_T = t.TypeVar("FieldBase_T", bound=type[BaseField])


def connect_mongo(name, host=None):
    if host is None:
        host = Config.MONGODB_HOST
    connect(name, host=host)


# https://github.com/MongoEngine/mongoengine/issues/1171
# Use this methods until a solution is found
def upsert(model, query=None, update=None) -> t.Optional[DynamicDocument]:

    if not update:
        update = query

    if not query:
        return None

    found = model.objects(**query)

    if found.first():
        return found.modify(new=True, **update)

    new_model = model(**update)
    new_model.save()

    return new_model


def fix_ids(q):
    json_obj = json.loads(q.to_json().replace('"_id"', '"id"'))
    return json_obj


def create_from_json(json_file):

    with open(json_file) as file:

        data_json = json.load(file)
        for category in data_json.get("categories", []):
            name = category.get("name")
            if name is not None:
                upsert(CategoryModel, query={"name": name}, update=category)

        for dataset_json in data_json.get("datasets", []):
            name = dataset_json.get("name")
            if name:
                # map category names to ids; create as needed
                category_ids = []
                for category in dataset_json.get("categories", []):
                    category_obj = {"name": category}

                    category_model = t.cast(
                        CategoryModel, upsert(CategoryModel, query=category_obj)
                    )
                    category_ids.append(category_model.id)

                dataset_json["categories"] = category_ids
                upsert(DatasetModel, query={"name": name}, update=dataset_json)
