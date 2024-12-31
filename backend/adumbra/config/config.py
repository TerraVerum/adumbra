import os

from adumbra.config.version_util import VersionControl


def _get_bool(key, default_value):
    if key in os.environ:
        value = os.environ[key]
        if value == "True" or value == "true" or value == "1":
            return True
        return False
    return default_value


version_info = VersionControl()


class Config:

    VERSION = version_info.get_tag()

    NAME = os.getenv("NAME", "Adumbra")

    ### File Watcher
    FILE_WATCHER = os.getenv("FILE_WATCHER", False)
    IGNORE_DIRECTORIES = ["_thumbnail", "_settings"]

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
    SWAGGER_UI_JSONEDITOR = True
    DEBUG = os.getenv("DEBUG", "false").lower() == "true"
    PRELOAD = False

    MAX_CONTENT_LENGTH = os.getenv("MAX_CONTENT_LENGTH", 1 * 1024 * 1024 * 1024)  # 1GB
    MONGODB_HOST = os.getenv("MONGODB_HOST", "mongodb://database/flask")
    SECRET_KEY = os.getenv("SECRET_KEY", "<--- CHANGE THIS KEY --->")

    LOG_LEVEL = "debug"
    WORKER_CONNECTIONS = 1000

    TESTING = os.getenv("TESTING", False)

    ### Workers
    CELERY_BROKER_URL = os.getenv(
        "CELERY_BROKER_URL", "amqp://user:password@messageq:5672//"
    )
    CELERY_RESULT_BACKEND = os.getenv(
        "CELERY_RESULT_BACKEND", "mongodb://database/flask"
    )

    ### Dataset Options
    DATASET_DIRECTORY = os.getenv("DATASET_DIRECTORY", "/datasets/")
    INITIALIZE_FROM_FILE = os.getenv("INITIALIZE_FROM_FILE")

    ### User Options
    LOGIN_DISABLED = _get_bool("LOGIN_DISABLED", False)
    ALLOW_REGISTRATION = _get_bool("ALLOW_REGISTRATION", True)

    ### Models
    SAM2_MODEL_FILE = os.getenv("SAM2_MODEL_FILE", "")
    SAM2_MODEL_CONFIG = os.getenv("SAM2_MODEL_CONFIG", "")
    ZIM_MODEL_FILE = os.getenv("ZIM_MODEL_FILE", "")
    ZIM_MODEL_TYPE = os.getenv("ZIM_MODEL_TYPE", "")

    DEVICE = os.getenv("DEVICE", "cuda")


__all__ = ["Config"]
