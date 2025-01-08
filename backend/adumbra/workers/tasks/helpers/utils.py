from adumbra.database.tasks import TaskModel
from adumbra.workers.tasks.data import export_annotations, import_annotations
from adumbra.workers.tasks.scan import scan_dataset


def scan(dataset):
    task = TaskModel(
        name=f"Scanning {dataset.name} for new images",
        dataset_id=dataset.id,
        group="Directory Image Scan",
    )
    task.save()

    cel_task = scan_dataset.delay(task.id, dataset.id)

    return {"celery_id": cel_task.id, "id": task.id, "name": task.name}


def import_coco(dataset, coco_json):
    task = TaskModel(
        name=f"Importing COCO annotations into {dataset.name}",
        dataset_id=dataset.id,
        group="Annotation Import",
    )
    task.save()

    cel_task = import_annotations.delay(task.id, dataset.id, coco_json)

    return {"celery_id": cel_task.id, "id": task.id, "name": task.name}


def export_coco(dataset, categories=None, style="COCO", with_empty_images=False):

    if categories is None or len(categories) == 0:
        categories = dataset.categories

    task = TaskModel(
        name=f"Exporting {dataset.name} into {style} format",
        dataset_id=dataset.id,
        group="Annotation Export",
    )
    task.save()

    cel_task = export_annotations.delay(
        task.id, dataset.id, categories, with_empty_images
    )

    return {"celery_id": cel_task.id, "id": task.id, "name": task.name}
