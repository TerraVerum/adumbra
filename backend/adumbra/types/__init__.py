from pydantic import BaseModel


class SAM2Config(BaseModel):
    """All params are named the same as sam2.build_sam2(...) and directly forwarded"""

    ckpt_path: str | None = None
    config_file: str | None = None


class ZIMConfig(BaseModel):
    """Passed directly to zim_anything.build_zim_model(...)"""

    checkpoint: str = ""
