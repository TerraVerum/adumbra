import os

import imantics
from PIL import Image, ImageFile

ImageFile.LOAD_TRUNCATED_IMAGES = True

THUMBNAIL_DIRECTORY = ".thumbnail"

# Set maximum thumbnail size (h x w) to use on dataset page
MAX_THUMBNAIL_DIM = (1024, 1024)


def get_thumbnail_path(image_path):
    """
    Return thumbnail path based on image path
    """
    folders = image_path.split("/")
    folders.insert(len(folders) - 1, THUMBNAIL_DIRECTORY)

    thumbnail_path = "/" + os.path.join(*folders)
    directory = os.path.dirname(thumbnail_path)

    if not os.path.exists(directory):
        os.makedirs(directory)

    return thumbnail_path


def open_thumbnail(image_path):
    """
    Return thumbnail
    """
    thumbnail_path = get_thumbnail_path(image_path)
    # check if thumbnail exists
    if not os.path.exists(thumbnail_path):
        return None
    return Image.open(thumbnail_path)


def delete_thumbnail(image_path):
    """
    Delete thumbnail
    """
    thumbnail_path = get_thumbnail_path(image_path)
    if os.path.isfile(thumbnail_path):
        os.remove(thumbnail_path)


def create_thumbnail(image_path, annotations):
    image = imantics.Image.from_path(image_path)
    for annotation in annotations:
        if not annotation.is_empty():
            # TODO: pull __call__ from annotation
            image.add(annotation())

    drawn_thumbnail = image.draw(color_by_category=True, bbox=True)
    return Image.fromarray(drawn_thumbnail)


def save_thumbnail(image_path, annotations):
    thumbnail_path = get_thumbnail_path(image_path)
    pil_image = create_thumbnail(image_path, annotations)
    pil_image = pil_image.convert("RGB")

    # Resize image to fit in MAX_THUMBNAIL_DIM envelope as necessary
    pil_image.thumbnail((MAX_THUMBNAIL_DIM[1], MAX_THUMBNAIL_DIM[0]))

    # Save as a jpeg to improve loading time
    # (note file extension will not match but allows for backwards compatibility)
    pil_image.save(thumbnail_path, "JPEG", quality=80, optimize=True, progressive=True)

    return pil_image
