import typing as t

from pydantic import BaseModel


class SAM2Config(BaseModel):
    """All params are named the same as sam2.build_sam2(...) and directly forwarded"""

    assistant_type: t.Literal["sam2"] = "sam2"
    ckpt_path: str | None = None
    config_file: str | None = None


class ZIMConfig(BaseModel):
    """Passed directly to zim_anything.build_zim_model(...)"""

    assistant_type: t.Literal["zim"] = "zim"
    checkpoint: str = ""
