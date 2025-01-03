import typing as t

from pydantic import AliasChoices, BaseModel, Field, StringConstraints
from pydantic_settings import BaseSettings, SettingsConfigDict

from adumbra.config.version_util import VersionControl

version_info = VersionControl()


class IAModelSettings(BaseModel):
    default_model_path: str = ""
    default_model_type: str = ""
    default_model_config: str = ""


class GunicornSettings(BaseSettings):
    bind: str = "0.0.0.0:5001"
    backlog: int = 2048

    workers: int = 1
    worker_class: str = "eventlet"
    worker_connections: int = 1000
    timeout: int = 60
    keepalive: int = 2

    reload: bool = False
    preload: bool = False

    errorlog: str = "-"
    loglevel: str = "debug"
    accesslog: str | None = None


class FlaskSettings(BaseSettings):
    # Flask expects uppercase keys

    # Give default value that fails constraint so user is prompted to add their
    # own FLASK_SECRET_KEY if unset
    SECRET_KEY: t.Annotated[str, StringConstraints(min_length=10)] = "CHANGE_ME!"


class CelerySettings(BaseSettings):
    broker_url: str = "amqp://user:password@messageq:5672//"
    result_backend: str = "mongodb://database/flask"


class Config(BaseSettings):
    model_config = SettingsConfigDict(env_nested_delimiter="__")

    version: str = version_info.get_tag()

    name: str = "Adumbra"

    ### File Watcher
    file_watcher: bool = False
    ignore_directories: list[str] = ["_thumbnail", "_settings"]

    # Flask/Gunicorn
    #
    #   LOG_LEVEL - The granularity of log output
    #
    #       A string of "debug", "info", "warning", "error", "critical"
    #
    #   WORKER_CONNECTIONS - limits the maximum number of simultaneous
    #       clients that a single process can handle.
    #
    #       A positive integer generally set to around 1000.
    #
    #   WORKER_TIMEOUT - If a worker does not notify the master process
    #       in this number of seconds it is killed and a new worker is
    #       spawned to replace it.
    #
    gunicorn: GunicornSettings = GunicornSettings()
    flask: FlaskSettings = FlaskSettings()

    max_content_length: int = 1 * 1024 * 1024 * 1024  # 1GB
    mongodb_host: str = "mongodb://database/flask"

    ### Workers
    celery: CelerySettings = CelerySettings()

    ### Dataset Options
    dataset_directory: str = "/datasets/"
    initialize_from_file: str | None = None

    ### User Options
    login_disabled: bool = False
    allow_registration: bool = True

    ### Models
    sam2: IAModelSettings = IAModelSettings(default_model_path="/models/sam2")
    zim: IAModelSettings = IAModelSettings(
        default_model_path="/models/zim", default_model_type="vit_b"
    )

    ia_device: str = Field(
        default="cpu", validation_alias=AliasChoices("device", "ia_device")
    )


CONFIG = Config()
__all__ = ["CONFIG"]
