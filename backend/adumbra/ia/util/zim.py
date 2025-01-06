import logging
import os

import numpy as np
from zim_anything import ZimPredictor, build_zim_model

from adumbra.config import CONFIG
from adumbra.ia.util import update_none_values
from adumbra.types import ZIMConfig

logger = logging.getLogger("gunicorn.error")


class ZIM:
    is_loaded = False
    masks: np.ndarray | None = None
    scores: np.ndarray | None = None
    logits: np.ndarray | None = None

    def __init__(self, *, config: ZIMConfig | None = None):
        ia_settings = CONFIG.ia
        config = update_none_values(config or ZIMConfig(), ia_settings.zim)
        device = ia_settings.get_best_device()

        logger.info(f"ZIM info: {config}, {device}")
        if config.checkpoint is None or not os.path.isdir(config.checkpoint):
            logger.warning("Disabling ZIM; checkpoint directory not found")
            return

        self.zim_model = build_zim_model(
            **config.model_dump(exclude={"assistant_type"})
        ).to(device)
        self.config = config
        self.is_loaded = True
        logger.info(f"ZIM model is loaded on device {device}.")

    def end_to_end_segmentation(
        self, image: np.ndarray, foreground_xy: np.ndarray, **kwargs
    ) -> np.ndarray:
        """
        Perform end-to-end segmentation with SAM2 model.

        Parameters
        ----------
        image
            HxWx3 Image to be segmented, expected in RGB format.
        foreground_xy
            Points known to be in object foreground.
        kwargs
            Unused.

        Returns
        -------
        np.ndarray
            Segmented mask of the image in CxHxW format.
        """
        del kwargs
        predictor = ZimPredictor(self.zim_model)
        predictor.set_image(image)

        masks, *_unused = predictor.predict(
            point_coords=foreground_xy,
            point_labels=np.ones(foreground_xy.shape[0], dtype=np.uint8),
            multimask_output=True,
        )
        del _unused
        return (masks * 255).astype(np.uint8)
