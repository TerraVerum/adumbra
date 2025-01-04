import logging
import os

import numpy as np
from zim_anything import ZimPredictor, build_zim_model

from adumbra.config import CONFIG, ZIMConfig

logger = logging.getLogger("gunicorn.error")


class ZIM:
    is_loaded = False
    masks: np.ndarray | None = None
    scores: np.ndarray | None = None
    logits: np.ndarray | None = None

    def __init__(self, config: ZIMConfig | None = None):
        ia_settings = CONFIG.ia
        config = config or ia_settings.zim
        device = ia_settings.get_best_device()

        logger.info(f"ZIM info: {config}, {device}")
        if not os.path.isdir(ia_settings.zim.checkpoint):
            logger.warning(f"Disabling ZIM; checkpoint directory not found")
            return

        zim_model = build_zim_model(**config.model_dump()).to(device)
        self.predictor = ZimPredictor(zim_model)
        self.is_loaded = True
        logger.info(f"ZIM model is loaded on device {device}.")

    def setImage(self, image):
        self.predictor.set_image(np.array(image, copy=True))

    def calcMasks(self, input_points, input_label):
        self.masks, self.scores, self.logits = self.predictor.predict(
            point_coords=input_points,
            point_labels=input_label,
            multimask_output=True,
        )
        self.masks = (self.masks * 255).astype(np.uint8)
