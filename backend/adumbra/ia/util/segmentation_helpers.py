import logging
import typing as t
from collections import OrderedDict

import cv2
import numpy as np
from PIL import Image
from pydantic import BaseModel, TypeAdapter
from typing_extensions import ParamSpec

from adumbra.ia.util.sam2 import SAM2
from adumbra.ia.util.zim import ZIM
from adumbra.types.assistants import SAM2Config, SegmentationResult, ZIMConfig

BaseModel_co = t.TypeVar("BaseModel_co", bound=BaseModel, covariant=True)
logger = logging.getLogger("gunicorn.error")
config_adapter = TypeAdapter[SAM2Config | ZIMConfig](SAM2Config | ZIMConfig)
P = ParamSpec("P")
R = t.TypeVar("R")


class SegmenterProtocol(t.Protocol, t.Generic[BaseModel_co]):
    def __init__(self, *, config: BaseModel_co | None = None) -> None: ...

    is_loaded: bool

    def end_to_end_segmentation(
        self, image: np.ndarray, foreground_xy: np.ndarray, **kwargs
    ) -> np.ndarray: ...


CONFIG_SEGMENTER_MAP: dict[type[BaseModel], type[SegmenterProtocol[BaseModel]]] = {
    SAM2Config: SAM2,
    ZIMConfig: ZIM,
}


class cache_with_key(t.Generic[P, R]):
    _unset = object()

    def __init__(self, key: t.Callable[P, t.Hashable], maxsize: int | None = 128):
        self.maxsize = maxsize
        self.cache = OrderedDict()
        self.key = key
        self.func: t.Callable[P, R] | None = None

    def __call__(self, func: t.Callable[P, R]):
        self.func = func
        return self.wrapper

    def wrapper(self, *args: P.args, **kwargs: P.kwargs) -> R:
        if self.func is None:
            raise ValueError("Function not set")
        func_key = self.key(*args, **kwargs)
        if (result := self.cache.get(func_key, self._unset)) is not self._unset:
            self.cache.move_to_end(func_key)
            return result
        if self.maxsize is not None and len(self.cache) >= self.maxsize:
            self.cache.popitem(last=False)
        result = self.func(*args, **kwargs)
        self.cache[func_key] = result
        return result


# Can't use functools.lru_cache since BaseModel is not hashable
# Keep the explicit lambda since `key=tuple` would be more confusing
# pylint: disable-next=unnecessary-lambda
@cache_with_key[[BaseModel], SegmenterProtocol](key=lambda config: tuple(config))
def config_to_segmenter(config: BaseModel) -> SegmenterProtocol:
    """
    Convenience wrapper around the `CONFIG_SEGMENTER_MAP` to convert a config
    dictionary to a segmenter instance. The main benefit is that same configs will
    avoid re-creating an expensive instance on constrained resources.
    """
    parsed = config_adapter.validate_python(config)
    return CONFIG_SEGMENTER_MAP[type(parsed)](config=parsed)


def run_segmentation(
    config: BaseModel,
    image: t.BinaryIO | str,
    foreground_xy: list[list[float]],
    **kwargs,
) -> SegmentationResult:
    segmenter = config_to_segmenter(config)
    if not segmenter.is_loaded:
        return SegmentationResult(
            disabled=True,
            segmentation=[],
            message=f"{segmenter.__class__.__name__} is disabled",
        )
    img = Image.open(image).convert("RGB")
    img = np.asarray(img)
    masks = segmenter.end_to_end_segmentation(
        img, foreground_xy=np.array(foreground_xy), **kwargs
    )
    if masks is None:
        logger.warning(f"{segmenter} No masks found")
        return SegmentationResult(disabled=False, segmentation=[])
    # Assume only bg/fg channels, so grab mask associated with fg
    mask = masks[1]
    contours, _ = cv2.findContours(
        mask.astype("uint8"), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE
    )
    # Convert the contour to the format required for segmentation in COCO format
    flattened = [contour.flatten().tolist() for contour in contours]

    return SegmentationResult(disabled=False, segmentation=flattened)
