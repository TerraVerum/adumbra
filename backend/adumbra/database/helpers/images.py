import os

from PIL import Image, ImageFile

from adumbra.database import ImageModel

ImageFile.LOAD_TRUNCATED_IMAGES = True


def create_from_path(path, dataset_id):
    if not dataset_id:
        raise ValueError("Dataset ID is required")

    pil_image = Image.open(path)

    image = ImageModel()
    image.file_name = os.path.basename(path)
    image.path = path
    image.width = pil_image.size[0]
    image.height = pil_image.size[1]
    image.regenerate_thumbnail = True
    image.dataset_id = dataset_id

    pil_image.close()

    return image
