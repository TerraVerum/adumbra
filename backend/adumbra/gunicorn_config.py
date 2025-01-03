from adumbra.config import CONFIG


def __getattr__(name):
    # Allow setting config values where gunicorn expects, but manage them with
    # pydantic settings
    return getattr(CONFIG.gunicorn, name)
