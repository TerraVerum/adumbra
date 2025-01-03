from adumbra.database import ImageModel
from adumbra.workers.tasks.thumbnails import thumbnail_generate_single_image


def generate_thumbnails():
    PREFIX = "[Thumbnails]"
    print(
        f"{PREFIX} Sending request for regenerating images with non actual thumbnails",
        flush=True,
    )

    for image in ImageModel.objects(regenerate_thumbnail=True).all():
        generate_thumbnail(image)


def generate_thumbnail(image):
    thumbnail_generate_single_image.delay(image.id)
