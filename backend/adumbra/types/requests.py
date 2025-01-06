import typing as t

from fastapi import UploadFile
from pydantic import BaseModel, ConfigDict, Json

from adumbra.types.assistants import SAM2Parameters, ZIMParameters

BaseModel_T = t.TypeVar("BaseModel_T", BaseModel, list)
MaybeJson = t.Union[Json[BaseModel_T], BaseModel_T]


class CreateAssistantRequest(BaseModel):
    model_config = ConfigDict(use_attribute_docstrings=True)

    assistant_name: str
    """
    Name of this configuration. So the combination of model type + weights + params can
    be identified as e.g. `zim-x-ray-small`.
    """

    assistant_type: t.Literal["sam2", "zim"]
    """Type of the model"""

    config_parameters: dict = {}
    """
    Additional parameters the model's config should recognize. For ZIM, it's just a
    `checkpoint` parameter pointing to a folder with encoder/decoder onnx weights. For
    SAM2, you must pass `ckpt_path` and `config_file` pointing to the model's weights
    and config file.
    """

    assets: UploadFile | list[UploadFile]
    """
    File or files referenced by name in the parameters. If a zip file is provided, it is
    extracted maintaining directories.
    """


class GetAssistantsRequest(BaseModel):
    model_config = ConfigDict(use_attribute_docstrings=True)

    assistant_name: str | None = None
    """Name of the configuration to retrieve"""

    assistant_type: t.Literal["sam2", "zim"] | None = None
    """Type of the model"""


class BaseSegmentationRequest(BaseModel):
    model_config = ConfigDict(use_attribute_docstrings=True)

    assistant_name: str
    """Name of the model to use"""

    image: UploadFile
    """Image to be segmented"""

    foreground_xy: Json[list]
    """List of (x, y) points to consider as foreground"""


class ZimSegmentationRequest(BaseSegmentationRequest):
    parameters: MaybeJson[ZIMParameters]
    """Relevant additional parameters for this iteration of segmentation"""


class SAM2SegmentationRequest(BaseSegmentationRequest):
    parameters: MaybeJson[SAM2Parameters]
    """Relevant additional parameters for this iteration of segmentation"""
