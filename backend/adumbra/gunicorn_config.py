from adumbra.config import CONFIG

# Allow setting config values in global scope where gunicorn expects, but keep source of
# truth with pydantic settings
globals().update(CONFIG.gunicorn.model_dump())
