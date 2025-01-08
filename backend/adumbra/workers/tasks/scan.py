import os

from adumbra.constants import SUPPORTED_IMAGE_EXTENTIONS
from adumbra.database import DatasetModel, ImageModel, TaskModel
from adumbra.database.helpers.images import create_from_path
from adumbra.workers import celery
from adumbra.workers.socket import create_socket
from adumbra.workers.tasks.thumbnails import thumbnail_generate_single_image


@celery.task
def scan_dataset(task_id, dataset_id):

    task = TaskModel.objects.get(id=task_id)
    dataset = DatasetModel.objects.get(id=dataset_id)

    task.update(status="PROGRESS")
    socket = create_socket()

    directory = dataset.directory
    toplevel = list(os.listdir(directory))
    task.info(f"Scanning {directory}")

    count = 0
    for root, _, files in os.walk(directory):

        try:
            youarehere = toplevel.index(root.split("/")[-1])
            progress = int(((youarehere) / len(toplevel)) * 100)
            task.set_progress(progress, socket=socket)
        # TODO: This is a broad exception, should be narrowed down as we see more errors
        except Exception as e:  # pylint: disable=broad-except
            print(e)

        if root.split("/")[-1].startswith("."):
            continue

        for file in files:
            path = os.path.join(root, file)

            if path.endswith(SUPPORTED_IMAGE_EXTENTIONS):
                db_image = ImageModel.objects(path=path).first()

                if db_image is not None:
                    continue

                try:
                    create_from_path(path, dataset.id).save()
                    count += 1
                    task.info(f"New file found: {path}")
                # TODO: This is a broad exception, should be narrowed down as we see more errors
                except Exception as e:  # pylint: disable=broad-except
                    print(e)
                    task.warning(f"Could not read {path}")

    for image in ImageModel.objects(regenerate_thumbnail=True).all():
        thumbnail_generate_single_image.delay(image.id)

    task.info(f"Created {count} new image(s)")
    task.set_progress(100, socket=socket)


__all__ = ["scan_dataset"]
