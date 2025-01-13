import json
import typing as t

from fastapi import UploadFile
from pydantic import BaseModel, ConfigDict, Json, field_validator

from adumbra.types.assistants import SAM2Parameters, ZIMParameters

BaseModel_T = t.TypeVar("BaseModel_T", BaseModel, list)
MaybeJson = t.Union[Json[BaseModel_T], BaseModel_T]


class BaseRequest(BaseModel):
    model_config = ConfigDict(use_attribute_docstrings=True)


class CreateAssistantRequest(BaseRequest):
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


class PaginationParams(BaseRequest):
    page_size: int | None = 20
    """Number of items per page. If None, all items are returned"""

    page: int = 1
    """Page number to retrieve"""


class GetAssistantsRequest(BaseRequest):
    assistant_name: str | None = None
    """Name of the configuration to retrieve"""

    assistant_type: t.Literal["sam2", "zim"] | None = None
    """Type of the model"""


class BaseSegmentationRequest(BaseRequest):
    assistant_name: str
    """Name of the model to use"""

    image: UploadFile
    """Image to be segmented"""

    foreground_xy: list[list[int | float]]
    """List of (x, y) points to consider as foreground"""

    @field_validator("foreground_xy", mode="before")
    @classmethod
    def validate_foreground_xy(cls, v):
        """
        Some weird issues occur when parsing FormData with Pydantic, with no clear
        answer on why. Possibly related to
        https://github.com/fastapi/fastapi/discussions/8480. If a type is declared as a
        list, "scalar" values are arbitrarily wrapped to become a list of one element.
        But since FormData can only send scalars, it becomes [the_value], which pydantic
        fails to parse. This validator "undoes" invalid Pydantic default behavior by
        extracting the scalar value from the list, also allowing parsing of str-format
        objects from the frontend.
        """
        if not isinstance(v, list) or len(v) == 0:
            return v  # Let Pydantic handle this
        if isinstance(v[0], list):
            return v  # Already in the correct format
        # Expect to only handle one nested element
        if len(v) > 1:
            raise ValueError("Only one nested element is expected")
        val = v[0]
        if isinstance(val, str):
            return json.loads(val)
        raise ValueError(f"No special handling for {val} of type {type(val)}")


class ZimSegmentationRequest(BaseSegmentationRequest):
    parameters: MaybeJson[ZIMParameters]
    """Relevant additional parameters for this iteration of segmentation"""


class SAM2SegmentationRequest(BaseSegmentationRequest):
    parameters: MaybeJson[SAM2Parameters]
    """Relevant additional parameters for this iteration of segmentation"""
