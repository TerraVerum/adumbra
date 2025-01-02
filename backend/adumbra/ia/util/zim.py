import logging
import os

import numpy as np
import torch
from zim_anything import ZimPredictor, zim_model_registry

from adumbra.config import Config as AnnotatorConfig

logger = logging.getLogger("gunicorn.error")

MODEL_DIR = "/workspace/models"
ZIM_MODEL_PATH = AnnotatorConfig.ZIM_MODEL_FILE
ZIM_MODEL_TYPE = AnnotatorConfig.ZIM_MODEL_TYPE


class ZIM:
    is_loaded = False
    masks: np.ndarray | None = None
    scores: np.ndarray | None = None
    logits: np.ndarray | None = None

    def __init__(self):
        device = AnnotatorConfig.DEVICE
        logger.info(f"zz info: {ZIM_MODEL_TYPE}, {ZIM_MODEL_PATH}, {device}")
        ZIM_LOADED = os.path.isdir(ZIM_MODEL_PATH)
        if ZIM_LOADED:
            zim_model = zim_model_registry[ZIM_MODEL_TYPE](checkpoint=ZIM_MODEL_PATH)
            if os.getenv("DEVICE", "cuda") == "cuda" and torch.cuda.is_available():
                zim_model.cuda()
            self.predictor = ZimPredictor(zim_model)
            self.is_loaded = True
            logger.info("ZIM model is loaded.")
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
