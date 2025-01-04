import logging
import os

import numpy as np
from sam2.build_sam import build_sam2
from sam2.sam2_image_predictor import SAM2ImagePredictor

from adumbra.config import CONFIG
from adumbra.types import SAM2Config

logger = logging.getLogger("gunicorn.error")


class SAM2:
    is_loaded = False
    masks: np.ndarray | None = None
    scores: np.ndarray | None = None
    logits: np.ndarray | None = None
    predictor: SAM2ImagePredictor | None = None

    def __init__(self, *, config: SAM2Config | None = None):
        config = config or CONFIG.ia.sam2
        device = CONFIG.ia.get_best_device()
        logger.info(f"SAM2 info: {config}, {device}")
        if not os.path.isfile(config.ckpt_path or ""):
            logger.warning("SAM2 model is disabled.")
            return

        self.sam2_model = build_sam2(**config.model_dump(), device=device)
        self.is_loaded = True
        logger.info(f"SAM2 model is loaded on device {device}.")

    def setPredictor(self, threshold=0.0, max_hole_area=0.0, max_sprinkle_area=0.0):
        self.predictor = SAM2ImagePredictor(
            self.sam2_model, threshold, max_hole_area, max_sprinkle_area
        )

    def setImage(self, image):
        if self.predictor is None:
            logger.warning("Sam2:setImage predictor not set")
            return
        self.predictor.set_image(np.array(image, copy=True))

    def calcMasks(self, input_points, input_label):
        if self.predictor is None:
            logger.warning("Sam2:calcMasks predictor not set")
            return
        self.masks, self.scores, self.logits = self.predictor.predict(
            point_coords=input_points,
            point_labels=input_label,
            multimask_output=True,
        )
