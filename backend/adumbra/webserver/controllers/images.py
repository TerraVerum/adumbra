from adumbra.database.images import AnnotationModel
from adumbra.services.thumbnail_service import create_thumbnail


def generate_segmented_image(image):
    """
    Generates segmented image
    """
    annotations = AnnotationModel.objects(image_id=image.id, deleted=False).all()
    pil_image = create_thumbnail(image.path, annotations)
    pil_image = pil_image.convert("RGB")

    return pil_image


def copy_image_annotations(image, annotations):
    """
    Creates a copy of the annotations for this image
    :param annotations: QuerySet of annotation models
    :return: number of annotations
    """
    annotations = annotations.filter(width=image.width, height=image.height).exclude(
        "events"
    )

    for annotation in annotations:
        if annotation.area > 0 or len(annotation.keypoints) > 0:
            clone = annotation.clone()

            clone.dataset_id = image.dataset_id
            clone.image_id = image.id

            clone.save(copy=True)

    return annotations.count()
