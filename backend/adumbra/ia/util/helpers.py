import logging

import cv2
import numpy as np

logger = logging.getLogger("gunicorn.error")


def getSegmentation(model_name: str, masks: np.ndarray | None) -> list:
    if masks is None:
        logger.warning(f"{model_name} No masks found")
        return []

    for mask in masks:
        contours, _ = cv2.findContours(
            mask.astype("uint8"), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE
        )
        # Convert the contour to the format required for segmentation in COCO format
        segmentation = []
        for contour in contours:
            contour = contour.flatten().tolist()
            contour_pairs = [
                (contour[i], contour[i + 1]) for i in range(0, len(contour), 2)
            ]
            segmentation.append(
                [int(coord) for pair in contour_pairs for coord in pair]
            )
    return segmentation
