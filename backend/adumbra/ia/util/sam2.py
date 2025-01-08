import logging
import os

import numpy as np
from sam2.build_sam import build_sam2
from sam2.sam2_image_predictor import SAM2ImagePredictor

from adumbra.config import CONFIG
from adumbra.ia.util import update_none_values
from adumbra.types import SAM2Config

logger = logging.getLogger("gunicorn.error")


class SAM2:
    is_loaded = False

    def __init__(self, *, config: SAM2Config | None = None):
        config = update_none_values(config or SAM2Config(), CONFIG.ia.sam2)
        device = CONFIG.ia.get_best_device()
        logger.info(f"SAM2 info: {config}, {device}")
        if not os.path.isfile(config.ckpt_path or ""):
            logger.warning("SAM2 model is disabled.")
            return

        self.sam2_model = build_sam2(
            **config.model_dump(exclude={"assistant_type"}), device=device
        )
        self.config = config
        self.is_loaded = True
        logger.info(f"SAM2 model is loaded on device {device}.")

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
            Forwarded to SAM2ImagePredictor.

        Returns
        -------
        np.ndarray
            Segmented mask of the image in CxHxW format.
        """
        # Avoid a helper function for a single call to sam vs zim predictor duplication.
        # pylint: disable=duplicate-code
        predictor = SAM2ImagePredictor(self.sam2_model, **kwargs)
        predictor.set_image(np.array(image, copy=True))
        masks, *_unused = predictor.predict(
            point_coords=foreground_xy,
            point_labels=np.ones(foreground_xy.shape[0], dtype=np.uint8),
            multimask_output=True,
        )
        del _unused
        return masks
