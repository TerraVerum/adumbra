from adumbra.database import ImageModel
from adumbra.database.images import AnnotationModel
from adumbra.services.thumbnail_service import save_thumbnail
from adumbra.workers import celery


@celery.task
def thumbnail_generate_single_image(image_id):
    print("will generate thumbnails in worker")
    image = ImageModel.objects(id=image_id).first()
    if image.regenerate_thumbnail:
        print(f"regenerating thumbnail for {image_id}")
        annotations = AnnotationModel.objects(image_id=image_id, deleted=False).all()
        save_thumbnail(image.path, annotations)
        image.update(regenerate_thumbnail=False)
    print(f"skip thumbnail generation for {image_id}")


__all__ = ["thumbnail_generate_single_image"]
