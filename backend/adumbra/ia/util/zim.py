import logging
import os

import numpy as np
from zim_anything import ZimPredictor, zim_model_registry

from adumbra.config import CONFIG

logger = logging.getLogger("gunicorn.error")


class ZIM:
    is_loaded = False
    masks: np.ndarray | None = None
    scores: np.ndarray | None = None
    logits: np.ndarray | None = None

    def __init__(self):
        ia_settings = CONFIG.ia
        model_path = ia_settings.zim.default_model_path
        model_type = ia_settings.zim.default_model_type
        device = ia_settings.get_best_device()

        logger.info(f"ZIM info: {model_type}, {model_path}, {device}")
        ZIM_LOADED = os.path.isdir(model_path)
        if ZIM_LOADED:
            zim_model = zim_model_registry[model_type](checkpoint=model_path).to(device)
            self.predictor = ZimPredictor(zim_model)
            self.is_loaded = True
            logger.info(f"ZIM model is loaded on device {device}.")
        else:
            logger.warning("ZIM model is disabled.")

    def setImage(self, image):
        self.predictor.set_image(np.array(image, copy=True))

    def calcMasks(self, input_points, input_label):
        self.masks, self.scores, self.logits = self.predictor.predict(
            point_coords=input_points,
            point_labels=input_label,
            multimask_output=True,
        )
        self.masks = (self.masks * 255).astype(np.uint8)


model = ZIM()
