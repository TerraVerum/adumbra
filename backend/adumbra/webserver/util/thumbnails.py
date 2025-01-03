from adumbra.database import ImageModel
from adumbra.workers.tasks.thumbnails import thumbnail_generate_single_image


def generate_thumbnails():
    PREFIX = "[Thumbnails]"
    print(
        f"{PREFIX} Sending request for regenerating images with non actual thumbnails",
        flush=True,
    )
    _ = [
        generate_thumbnail(image)
        for image in ImageModel.objects(regenerate_thumbnail=True).all()
    ]


def generate_thumbnail(image):
    thumbnail_generate_single_image.delay(image.id)
