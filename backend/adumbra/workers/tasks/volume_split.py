from pathlib import Path

import cv2
import numpy as np
from xrayrecon.layerseg import layerInfoForWindow  # pylint: disable=import-error

from adumbra.database import DatasetModel, ImageModel, TaskModel
from adumbra.workers import celery
from adumbra.workers.socket import create_socket
from adumbra.workers.tasks.thumbnails import thumbnail_generate_single_image


def forceDepthToLastAx(cube: np.ndarray):
    minAx = np.argmin(cube.shape)
    if minAx != 2:
        neworder = np.setdiff1d([0, 1, 2], minAx).tolist() + [minAx]
        cube = cube.transpose(neworder)
    return cube


def _maybeBgrToRgb(image: np.ndarray):
    """Treats 3/4-channel images as BGR/BGRA for opencv saving/reading"""
    if image.ndim > 2:
        # if image.shape[0] == 1:
        #   image = image[...,0]
        if image.shape[2] >= 3:
            lastAx = np.arange(image.shape[2], dtype="int")
            # Swap B & R
            lastAx[[0, 2]] = [2, 0]
            image = image[..., lastAx]
    return image


def generate_layer_images(volumeFile: str, outputDir: str):
    dataCube = np.load(volumeFile)
    dataCube = forceDepthToLastAx(dataCube)
    layerInfo = layerInfoForWindow(dataCube, dataCube.shape[:2], 50, returnMetric=True)
    images = []
    for i, s in enumerate(layerInfo["Slices"]):
        layerImage = dataCube[..., s].mean(2).astype("uint8")
        layerName = layerInfo["Layer Name"][i]
        rgbImage = _maybeBgrToRgb(layerImage)
        imagePath = Path(outputDir) / f"{layerName}.png"
        cv2.imwrite(str(imagePath), rgbImage)
        images.append(str(imagePath))
    return images


@celery.task
def split_volume_into_layers(task_id, dataset_id, volume_path):
    task = TaskModel.objects.get(id=task_id)
    dataset = DatasetModel.objects.get(id=dataset_id)

    task.update(status="PROGRESS")
    socket = create_socket()

    volume_model = ImageModel(dataset_id=-1, path=volume_path, width=0, height=0).save()
    volume_model = volume_model.save()

    image_paths = generate_layer_images(volume_path, f"/datasets/{dataset.name}")
    for image_path in image_paths:
        ImageModel.create_from_path(image_path, dataset_id).save()

    for image in ImageModel.objects(regenerate_thumbnail=True).all():
        thumbnail_generate_single_image.delay(image.id)

    task.set_progress(100, socket=socket)


__all__ = ["split_volume_into_layers"]
