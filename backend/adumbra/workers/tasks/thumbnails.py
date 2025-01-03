from adumbra.database import ImageModel
from adumbra.workers import celery


@celery.task
def thumbnail_generate_single_image(image_id):
    print("will generate thumbnails in worker")
    image = ImageModel.objects(id=image_id).first()
    image.thumbnail()
    image.flag_thumbnail(flag=False)


__all__ = ["thumbnail_generate_single_image"]
